# -*- coding: utf-8 -*-
"""Registry các TRÌNH GHI NHẬN (tracker), và chỗ nối vào nhật ký lần chạy.

    mlflow      ghi lên máy chủ MLflow của DagsHub (địa chỉ ở `configs/dagshub.yaml`)
    local_json  ghi bản ghi JSON trong nhóm report `experiment_registry`
    none        không ghi đi đâu cả

CÁCH DÙNG (`src/experiment_run.py` gọi, notebook không gọi trực tiếp)

    session = tracking.begin(tracking_config, out_dir, info=info, log=log)
    log.on_close(tracking.closer(session, log=log))     # phiên nào cũng được kết thúc
    ...
    session.log_params(extra)
    session.log_metrics(result["scores"])
    session.log_artifacts(tracking.base.artifact_paths(out_dir, artifacts))

Thứ tự quan trọng: ghi FILE xuống đĩa trước, rồi mới `begin`/`close` phần ghi nhận. Nhờ vậy máy
chủ hỏng cũng không làm mất `metrics.json` - đó là điều kiện hoàn thành của P4.

`begin` và phần đóng phiên KHÔNG BAO GIỜ ném. Ghi nhận hỏng thì `run.log` có dòng `[WARN]` hoặc
`[TRACK]`, còn kết quả vẫn nguyên trong thư mục kết quả.
"""

from functools import partial

from src.tracking import base, local_json, mlflow_tracker, none, run_meta

# Các tracker đang có, theo thứ tự đọc.
TRACKERS = {
    mlflow_tracker.NAME: mlflow_tracker,
    local_json.NAME: local_json,
    none.NAME: none,
}


def available():
    """Tên các tracker đang có."""
    return list(TRACKERS)


def get(name):
    """Module của một tracker. Tên sai thì báo lỗi kèm danh sách."""
    if name not in TRACKERS:
        raise base.TrackingError("Không có tracker '{}'. Các tracker hiện có: {}.".format(
            name, ", ".join(available())))
    return TRACKERS[name]


def check(config, dagshub=None):
    """Kiểm tracker đã khai trong `tracking.tracker` có dùng được không.

    Dùng cho preflight: biết TRƯỚC khi chạy là thiếu token hay thiếu thư viện, thay vì đợi tới
    lúc ghi nhận mới phát hiện.
    """
    name = str((config or {}).get("tracker") or "none").strip()
    module = get(name)
    if name == none.NAME:
        return True
    if not hasattr(module, "check"):
        return True
    return module.check(config, dagshub if dagshub is not None else base.dagshub_config())


def describe():
    """Vài dòng mô tả các tracker, để in bằng `--list-trackers`."""
    return ["{:<12} {}".format(name, TRACKERS[name].DESCRIPTION) for name in available()]


def begin(config, out_dir, info=None, log=None, dagshub=None):
    """Mở phiên ghi nhận theo `tracking.tracker`. KHÔNG ném trong mọi trường hợp."""
    name = str((config or {}).get("tracker") or "none").strip()
    try:
        module = get(name)
    except base.TrackingError as exc:
        if log is not None:
            log.warn("tracker không dùng được: {}".format(exc))
        return base.Session(active=False, reason=str(exc))

    if dagshub is None:
        try:
            dagshub = base.dagshub_config()
        except base.TrackingError as exc:
            if log is not None:
                log.warn("không đọc được configs/dagshub.yaml: {}".format(exc))
            dagshub = {}

    try:
        session = module.begin(config, dagshub, out_dir, info=info, log=log)
    except Exception as exc:  # noqa: BLE001 - ghi nhận không được làm chết lần chạy
        if log is not None:
            log.warn("không mở được phiên ghi nhận: {}: {}".format(type(exc).__name__, exc))
        return base.Session(active=False, reason=str(exc))

    if log is not None and not session.active:
        log.track("không ghi nhận: {}".format(session.reason or "tracker tắt"))
    return session


def close(session, log=None, ok=True):
    """Kết thúc phiên và ghi lại kết quả vào `run.log`. Không ném, nên dùng được làm callback."""
    try:
        session.close(ok=ok)
    except Exception as exc:  # noqa: BLE001 - đang đóng, không được ném
        session.note("đóng phiên ghi nhận hỏng: {}: {}".format(type(exc).__name__, exc))
    if log is not None:
        for note in session.notes:
            log.track(note)
        if not session.notes:
            log.track("không ghi nhận gì (tracker tắt)")
    return session.notes


def closer(session, log=None):
    """Hàm đóng phiên để đưa cho `runlog.on_close`, bảo đảm phiên nào cũng kết thúc.

    Lần chạy hỏng giữa chừng vẫn phải kết thúc run trên máy chủ; bỏ qua việc này thì trên DagsHub
    còn lại những run mãi ở trạng thái đang chạy, và người xem không biết run nào thật sự xong.
    """
    return partial(close, session, log=log)
