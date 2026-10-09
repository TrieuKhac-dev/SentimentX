# -*- coding: utf-8 -*-
"""`mlflow`: ghi nhận lên máy chủ MLflow của DagsHub (địa chỉ ở `configs/dagshub.yaml`).

KHÔNG CẦN GÓI `dagshub`
`docs/05_config/07_env.md` chốt cách thủ công: đặt `MLFLOW_TRACKING_URI`,
`MLFLOW_TRACKING_USERNAME`, `MLFLOW_TRACKING_PASSWORD` rồi để thư viện `mlflow` tự gửi. Cách này
chỉ cần `mlflow`, không thêm gói nào khác và không tự ý vá thư viện.

VÌ SAO MỌI THỨ ĐỀU NẰM TRONG try/except
Ghi nhận là việc PHỤ. Đứt mạng hay token hết hạn không được làm mất một lần chạy 40 phút đã xong
việc: file kết quả đã được ghi xuống đĩa TRƯỚC khi gọi máy chủ (xem `src/tracking/base.py`).
"""

import importlib.util
import os
from pathlib import Path

from src.core import utils
from src.tracking import base, run_meta

NAME = "mlflow"
DESCRIPTION = "Ghi nhận lên máy chủ MLflow của DagsHub (configs/dagshub.yaml)."


def check(config, dagshub):
    """Kiểm tracker này dùng được không. Lỗi kèm đúng việc cần làm, gom hết rồi báo một lần.

    Dùng cho preflight trong notebook (P5): kiểm TRƯỚC khi chạy, chứ không phải đợi tới lúc ghi
    nhận mới biết là thiếu token.
    """
    dagshub = dagshub or {}
    problems = []
    if not dagshub.get("owner") or not dagshub.get("mlflow_uri"):
        problems.append("{} thiếu `owner` hoặc `mlflow_uri`".format(
            utils.rel(base.dagshub_path())))
    token_env = dagshub.get("token_env") or "DAGSHUB_TOKEN"
    if not base.token(dagshub):
        problems.append("chưa có biến môi trường {} (token DagsHub)".format(token_env))
    if importlib.util.find_spec("mlflow") is None:
        problems.append("chưa cài thư viện `mlflow`: pip install mlflow")
    if not str((config or {}).get("experiment") or "").strip():
        problems.append("`tracking.experiment` trống: chưa biết tên experiment trên máy chủ")
    if problems:
        raise base.TrackingError("; ".join(problems) + ".")
    return True


def connect(config, dagshub):
    """Đặt cách kết nối rồi trả về module `mlflow` đã trỏ đúng máy chủ và experiment.

    Dùng cho `begin()` và cho việc tra cứu/xoá run (script dọn run smoke). Gộp một chỗ để hai
    đường không thể cấu hình lệch nhau.
    """
    import mlflow

    uri = str(dagshub["mlflow_uri"])
    # Đặt ở os.environ để chính thư viện mlflow dùng, giống cách cấu hình thủ công trong
    # 07_env.md; setdefault để không đè lên biến người dùng đã đặt.
    os.environ.setdefault("MLFLOW_TRACKING_URI", uri)
    os.environ.setdefault("MLFLOW_TRACKING_USERNAME", str(dagshub.get("owner") or ""))
    os.environ.setdefault("MLFLOW_TRACKING_PASSWORD", base.token(dagshub))
    mlflow.set_tracking_uri(uri)
    mlflow.set_experiment(str(config["experiment"]))
    return mlflow


def runs_with_tag(config, dagshub, key="smoke", value="true"):
    """Các run mang một nhãn nhất định. Dùng để tìm run kiểm tra trước khi xoá.

    Trả về danh sách run; máy chủ hỏng thì trả về danh sách rỗng kèm một dòng giải thích, để chỗ
    gọi in ra được chứ không phải bắt ngoại lệ.
    """
    try:
        mlflow = connect(config, dagshub)
        experiment = mlflow.get_experiment_by_name(str(config["experiment"]))
        if experiment is None:
            return [], "chưa có experiment '{}' trên máy chủ".format(config["experiment"])
        found = mlflow.search_runs(
            experiment_ids=[experiment.experiment_id],
            filter_string="tags.`{}` = '{}'".format(key, value))
        return list(found.iterrows()), ""
    except Exception as exc:  # noqa: BLE001 - công cụ dọn dẹp, không làm chết việc khác
        return [], "{}: {}".format(type(exc).__name__, exc)


def delete_runs(rows):
    """Xoá các run (dạng dòng của `search_runs`). Trả về (số xoá được, danh sách lỗi)."""
    import mlflow

    deleted, problems = 0, []
    for _index, row in rows:
        run_id = row.get("run_id")
        try:
            mlflow.delete_run(str(run_id))
            deleted += 1
        except Exception as exc:  # noqa: BLE001
            problems.append("{}: {}: {}".format(run_id, type(exc).__name__, exc))
    return deleted, problems


DELETED_MARK = "deleted experiment"


def is_deleted_experiment(error):
    """Lỗi này có phải "experiment đã bị XOÁ trên máy chủ" không.

    Thông báo thật của MLflow: `Cannot set a deleted experiment 'sentimentx-absa' as the active
    experiment. You can restore the experiment, or permanently delete the experiment to create a new
    one.` Đã gặp thật ở MỌI lượt chạy trong đợt 10-11: file kết quả vẫn đủ, nhưng phần ghi nhận mất
    sạch mà `run.log` chỉ có một dòng `[WARN]` dễ bị đọc lướt qua.
    """
    return DELETED_MARK in str(error)


def restore_deleted_experiment(config, dagshub):
    """Khôi phục (hoặc tạo lại) experiment đã bị xoá. Trả về `(đã_xong, ghi_chú)`.

    Vì sao cần: `mlflow.set_experiment` coi experiment đã xoá là LỖI, nên mọi lượt chạy mất phần ghi
    nhận - trong khi đây là ca DUY NHẤT tự sửa được tại chỗ. `get_experiment_by_name` trả `None` khi
    experiment đã bị xoá VĨNH VIỄN (đúng việc mà chính thông báo lỗi của MLflow gợi ý: tạo lại), còn
    trả bản ghi đã đánh dấu xoá thì `restore_experiment` đưa nó về.

    KHÔNG ném: đây là việc phụ, và tài khoản có thể không có quyền khôi phục.
    """
    try:
        import mlflow

        uri = str(dagshub["mlflow_uri"])
        mlflow.set_tracking_uri(uri)
        token = base.token(dagshub)
        if token:
            # Ghi THẲNG (không `setdefault`): biến môi trường có thể đang giữ token cũ/hỏng, và
            # `setdefault` sẽ giữ nguyên giá trị sai đó.
            os.environ["MLFLOW_TRACKING_PASSWORD"] = token
            os.environ.setdefault("MLFLOW_TRACKING_USERNAME", str(dagshub.get("owner") or ""))
        name = str(config["experiment"])
        client = mlflow.MlflowClient(tracking_uri=uri)
        found = client.get_experiment_by_name(name)
        if found is None:
            return True, "experiment {!r} không còn nữa nên đã TẠO MỚI: {}".format(
                name, client.create_experiment(name))
        client.restore_experiment(found.experiment_id)
        return True, "đã KHÔI PHỤC experiment đã bị xoá: {!r} ({})".format(
            name, found.experiment_id)
    except Exception as exc:  # noqa: BLE001 - ghi nhận không được làm chết lần chạy
        return False, "{}: {}".format(type(exc).__name__, exc)


class _Session(base.Session):
    NAME = NAME

    def __init__(self, module, uri, run):
        super().__init__(active=True)
        self.module = module
        self.uri = uri
        self.run = run
        # Tham số đã GỬI lên máy chủ (MLflow không cho ghi đè tham số): gửi ngay khi biết, và chỉ gửi
        # phần CHƯA gửi ở lần sau - nhờ vậy phiên bị ngắt vẫn để lại tham số, mà không bị lỗi trùng khoá.
        self.sent_params = {}

    def log_params(self, values):
        """Nhận tham số rồi GỬI NGAY phần chưa gửi; lỗi gửi không làm chết lượt chạy."""
        stored = super().log_params(values)
        if self.active:
            try:
                self._send_params()
            except Exception as exc:  # noqa: BLE001 - ghi nhận là việc phụ
                self.note("ghi tham số lên MLflow hỏng ({}: {}) - kết quả vẫn nằm trong thư mục kết quả"
                          .format(type(exc).__name__, exc))
        return stored

    def _send_params(self):
        """Gửi các tham số CHƯA gửi. Trả về danh sách khoá vừa gửi."""
        new = {key: value for key, value in self.params.items() if key not in self.sent_params}
        if new:
            self.module.log_params(new)
            self.sent_params.update(new)
        return list(new)

    def run_id(self):
        """Mã run trên máy chủ, hoặc chuỗi rỗng nếu thư viện không cho biết."""
        info = getattr(self.run, "info", None)
        return str(getattr(info, "run_id", "") or "")

    def close(self, ok=True):
        """Gửi tham số, chỉ số, file rồi kết thúc run. Gửi hỏng thì ghi lại vào `notes`."""
        mlflow = self.module
        try:
            self._send_params()
            if self.metrics:
                mlflow.log_metrics(self.metrics)
            # Chuỗi theo bước/epoch: MLflow vẽ thành CURVE khi mỗi điểm có `step`.
            points = sum(len(items) for items in self.series.values())
            for key, items in self.series.items():
                for step, value in items:
                    mlflow.log_metric(key, value, step=step)
            for path in self.artifacts:
                mlflow.log_artifact(str(path))
            mlflow.end_run(status="FINISHED" if ok else "FAILED")
            # Mã run ghi vào CẢ HAI chỗ: dòng log này, và khoá `tracking.run_id` của `run_meta.json`
            # (ghi ngay sau `tracking.begin` trong experiment_run/encoder_run, nên `begin` lần sau
            # đọc lại được để NỐI đúng run). Dòng log là để người đọc tra nhanh.
            self.note("đã ghi lên {}: run {} ({} tham số, {} chỉ số, {} điểm chuỗi, {} file)".format(
                self.uri, self.run_id(), len(self.params), len(self.metrics), points,
                len(self.artifacts)))
        except Exception as exc:  # noqa: BLE001 - ghi nhận không được làm chết lần chạy
            self.note("ghi lên MLflow hỏng ({}: {}) - kết quả vẫn nằm trong thư mục kết quả".format(
                type(exc).__name__, exc))
            try:
                mlflow.end_run(status="FAILED")
            except Exception:  # noqa: BLE001 - máy chủ có thể đã mất kết nối hẳn
                pass
        return self.notes


def begin(config, dagshub, out_dir, info=None, log=None):
    """Mở phiên MLflow. KHÔNG ném: không mở được thì trả về phiên TẮT kèm lí do."""
    try:
        check(config, dagshub)
    except base.TrackingError as exc:
        if log is not None:
            log.warn("không dùng được MLflow: {}".format(exc))
        return base.Session(active=False, reason=str(exc))

    mlflow = None
    try:
        mlflow = connect(config, dagshub)
    except Exception as first:  # noqa: BLE001 - mở phiên hỏng thì chạy tiếp, không dừng
        exc = first
        # Experiment đã bị XOÁ trên máy chủ là ca DUY NHẤT tự sửa được tại chỗ (xem
        # `restore_deleted_experiment`): thử sửa rồi nối tiếp, không xong mới hạ cấp như lỗi khác.
        if is_deleted_experiment(exc):
            restored, note = restore_deleted_experiment(config, dagshub)
            if log is not None:
                log.warn("MLflow: {} {}".format(
                    "ĐÃ sửa được - " if restored else "KHÔNG sửa được - ", note or str(exc)))
            if restored:
                try:
                    mlflow = connect(config, dagshub)
                except Exception as again:  # noqa: BLE001
                    exc, mlflow = again, None
        if mlflow is None:
            if log is not None:
                log.warn("không mở được phiên MLflow: {}: {}".format(type(exc).__name__, exc))
            return base.Session(active=False, reason=str(exc))

    try:
        # MỘT PHÉP ĐO = MỘT RUN: nếu thư mục này đã có `tracking.run_id` thì NỐI vào đúng run đó
        # (phiên chạy tiếp của cùng phép đo), thay vì mở run mới mỗi phiên.
        stored = str((run_meta.read(out_dir).get("tracking") or {}).get("run_id") or "")
        if stored:
            run = mlflow.start_run(run_id=stored)
        else:
            run = mlflow.start_run(
                run_name=Path(out_dir).name,
                tags=base.resolve_tags(config.get("mlflow_tags"), info))
    except Exception as exc:  # noqa: BLE001 - mở phiên hỏng thì chạy tiếp, không dừng
        if log is not None:
            log.warn("không mở được phiên MLflow: {}: {}".format(type(exc).__name__, exc))
        return base.Session(active=False, reason=str(exc))

    session = _Session(mlflow, str(dagshub["mlflow_uri"]), run)
    # Gửi THAM SỐ ngay khi mở: run có nội dung từ đầu, nên phiên bị ngắt vẫn còn dấu vết.
    if info:
        session.log_params(info)
    if log is not None:
        log.step("đã mở run trên MLflow: {}{}".format(
            dagshub["mlflow_uri"], " (nối run cũ {})".format(stored) if stored else ""))
    return session
