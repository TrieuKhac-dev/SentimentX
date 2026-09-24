# -*- coding: utf-8 -*-
"""Hợp đồng của một TRÌNH GHI NHẬN (tracker) và những thứ dùng chung.

MỘT MODULE CẦN CÓ
    NAME         tên dùng trong config (khoá `tracking.tracker`)
    DESCRIPTION  một dòng mô tả
    begin(config, dagshub, out_dir, info, log) -> Session

`Session` là một phiên ghi nhận:
    active        False nghĩa là không ghi đi đâu cả (tracker tắt, hoặc không dùng được)
    log_params    tham số của lần chạy (đều thành chuỗi)
    log_metrics   các con số
    log_artifacts file nhỏ cần tải lên
    close(ok)     kết thúc phiên; `ok=False` là lần chạy hỏng

QUY TẮC QUAN TRỌNG NHẤT
Ghi nhận KHÔNG BAO GIỜ được làm chết một lần chạy. Máy chủ hỏng, token hết hạn, mạng đứt - tất
cả phải trở thành dòng `[WARN]`/`[TRACK]` trong `run.log`, còn `metrics.json` và `run_meta.json`
vẫn nằm nguyên trong thư mục kết quả. Vì vậy:
    - `begin` bắt mọi lỗi và trả về phiên KHÔNG hoạt động, không ném.
    - `close` cũng vậy, và luôn được gọi qua `runlog.on_close` nên phiên nào cũng kết thúc.
    - File được ghi xuống đĩa TRƯỚC khi tải lên máy chủ.
"""

import os
from pathlib import Path

import yaml

from src import paths, utils

# Giá trị dài hơn mức này bị cắt khi gửi lên MLflow: MLflow giới hạn độ dài tham số, vượt là lỗi
# cả lần ghi nhận - mà tham số dài thường chỉ là đường dẫn hoặc văn bản, không cần nguyên vẹn.
MAX_PARAM = 500

# Giá trị `auto` trong `tracking.mlflow_tags`: lấy từ thông tin của lần chạy.
AUTO = "auto"


class TrackingError(Exception):
    """Lỗi khai báo hoặc kết nối phần ghi nhận."""


def dagshub_path():
    """Đường dẫn file cấu hình DagsHub. Tên file lấy từ `configs/paths.yaml`, không viết lại."""
    return paths.config_path(paths.cfg()["configs"]["dagshub"])


def dagshub_config():
    """Nội dung khối `dagshub` trong file cấu hình DagsHub, đã thay `{owner}`/`{repo}`."""
    path = dagshub_path()
    if not path.exists():
        raise TrackingError("Thiếu {}. Xem docs/05_config/07_env.md.".format(utils.rel(path)))
    with open(path, "r", encoding="utf-8") as handle:
        data = (yaml.safe_load(handle) or {}).get("dagshub") or {}
    if not isinstance(data, dict):
        raise TrackingError("{}: khối `dagshub` phải là các dòng 'khoá: giá trị'.".format(
            utils.rel(path)))
    data = dict(data)
    for key, value in list(data.items()):
        if isinstance(value, str):
            data[key] = value.format(owner=data.get("owner", ""), repo=data.get("repo", ""))
    return data


def token(dagshub):
    """Token đọc từ biến môi trường mà `token_env` chỉ ra. Không có thì trả về chuỗi rỗng.

    Token KHÔNG BAO GIỜ được ghi vào log hay file kết quả: nó là secret, mà file kết quả thì bị
    đem từ máy này sang máy khác.
    """
    name = (dagshub or {}).get("token_env") or "DAGSHUB_TOKEN"
    return os.environ.get(name, "").strip()


def artifact_paths(out_dir, names):
    """Đường dẫn các file cần tải lên, theo danh sách `tracking.artifacts`.

    Chỉ lấy file ĐANG CÓ: lần chạy hỏng có thể chưa kịp sinh file nào, mà tải một file không tồn
    tại thì máy chủ báo lỗi và cả lần ghi nhận coi như mất.
    """
    out_dir = Path(out_dir)
    found = []
    for name in names or []:
        path = out_dir / str(name)
        if path.is_file():
            found.append(path)
    return found


def numeric(data, prefix=""):
    """Rút các con số ra khỏi dict lồng nhau, tên theo đường dẫn khoá.

    Trả về {'accuracy.macro': 91.4, ...}. Giá trị không phải số bị bỏ qua: máy chủ chỉ nhận số,
    gửi chuỗi vào đó là lỗi và mất cả lần ghi nhận.
    """
    found = {}
    for key, value in (data or {}).items():
        name = "{}.{}".format(prefix, key) if prefix else str(key)
        if isinstance(value, bool):
            found[name] = float(value)
        elif isinstance(value, (int, float)):
            found[name] = float(value)
        elif isinstance(value, dict):
            found.update(numeric(value, name))
    return found


def as_param(value):
    """Đổi một giá trị thành tham số gửi lên máy chủ: chuỗi, ngắn, không xuống dòng."""
    if isinstance(value, bool):
        text = "true" if value else "false"
    elif isinstance(value, (list, tuple)):
        text = ", ".join(str(item) for item in value)
    elif isinstance(value, dict):
        text = ", ".join("{}={}".format(key, item) for key, item in value.items())
    else:
        text = str(value)
    text = text.replace("\n", " ").strip()
    return text if len(text) <= MAX_PARAM else text[:MAX_PARAM - 3] + "..."


def resolve_tags(tags, info):
    """Đổi `auto` trong `tracking.mlflow_tags` thành giá trị thật lấy từ `info`.

    Thiếu khoá thì BỎ nhãn đó: gắn nhãn "auto" lên máy chủ là gắn một thông tin vô nghĩa, và
    người xem sẽ tưởng đó là giá trị thật.
    """
    resolved = {}
    for key, value in (tags or {}).items():
        if value == AUTO:
            if (info or {}).get(key):
                resolved[str(key)] = as_param(info[key])
            continue
        resolved[str(key)] = as_param(value)
    return resolved


class Session:
    """Một phiên ghi nhận. Lớp cơ sở = phiên TẮT (không ghi đi đâu cả)."""

    NAME = "none"

    def __init__(self, active=False, reason=""):
        self.active = bool(active)
        self.reason = reason
        self.params = {}
        self.metrics = {}
        self.artifacts = []
        self.notes = []

    def note(self, message):
        """Ghi lại một việc đã xảy ra trong lúc ghi nhận (để `runlog` in ra)."""
        self.notes.append(str(message))
        return self.notes[-1]

    def log_params(self, values):
        if self.active:
            self.params.update({str(key): as_param(value)
                                for key, value in (values or {}).items()})
        return self.params

    def log_metrics(self, values):
        if self.active:
            self.metrics.update(numeric(values))
        return self.metrics

    def log_artifacts(self, paths_):
        if self.active:
            self.artifacts.extend(Path(path) for path in paths_ or [])
        return self.artifacts

    def close(self, ok=True):
        """Kết thúc phiên. Lớp cơ sở không làm gì; lớp con KHÔNG được ném ra ngoài."""
        return None

