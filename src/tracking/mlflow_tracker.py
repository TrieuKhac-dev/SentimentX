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

from src import utils
from src.tracking import base

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


class _Session(base.Session):
    NAME = NAME

    def __init__(self, module, uri, run):
        super().__init__(active=True)
        self.module = module
        self.uri = uri
        self.run = run

    def run_id(self):
        """Mã run trên máy chủ, hoặc chuỗi rỗng nếu thư viện không cho biết."""
        info = getattr(self.run, "info", None)
        return str(getattr(info, "run_id", "") or "")

    def close(self, ok=True):
        """Gửi tham số, chỉ số, file rồi kết thúc run. Gửi hỏng thì ghi lại vào `notes`."""
        mlflow = self.module
        try:
            if self.params:
                mlflow.log_params(self.params)
            if self.metrics:
                mlflow.log_metrics(self.metrics)
            for path in self.artifacts:
                mlflow.log_artifact(str(path))
            mlflow.end_run(status="FINISHED" if ok else "FAILED")
            # Mã run nằm trong DÒNG LOG, không nằm trong `run_meta.json`: bản ghi đó được chốt
            # TRƯỚC khi run mở ra (để bản tải lên máy chủ là bản đã chốt), nên nó không thể chứa
            # mã của chính run. Muốn mở lại run thì tra dòng này.
            self.note("đã ghi lên {}: run {} ({} tham số, {} chỉ số, {} file)".format(
                self.uri, self.run_id(), len(self.params), len(self.metrics), len(self.artifacts)))
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

    try:
        mlflow = connect(config, dagshub)
        run = mlflow.start_run(
            run_name=Path(out_dir).name,
            tags=base.resolve_tags(config.get("mlflow_tags"), info))
    except Exception as exc:  # noqa: BLE001 - mở phiên hỏng thì chạy tiếp, không dừng
        if log is not None:
            log.warn("không mở được phiên MLflow: {}: {}".format(type(exc).__name__, exc))
        return base.Session(active=False, reason=str(exc))

    if log is not None:
        log.step("đã mở run trên MLflow: {}".format(dagshub["mlflow_uri"]))
    return _Session(mlflow, str(dagshub["mlflow_uri"]), run)
