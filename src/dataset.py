# -*- coding: utf-8 -*-
"""Cấu hình và nạp MỘT dataset.

Mọi thứ thuộc về SCHEMA của dữ liệu (tên cột văn bản, danh sách aspect, nhãn
hợp lệ, đường dẫn file) đều nằm trong configs/datasets/<tên>.yaml.
Nhờ vậy: thêm dataset mới = thêm một file YAML, không sửa code EDA/pipeline.

DẠNG CHUẨN NỘI BỘ
------------------
Sau khi nạp, mọi DataFrame trong dự án đều có dạng:
    cột "text"  +  một cột cho mỗi aspect (nhãn để ở dạng CHUỖI)
Ô trống ở cột aspect nghĩa là "aspect này không được nhắc tới" (null).
"""

import difflib
from pathlib import Path

import yaml

from src import config, loaders

DATASET_ERROR_HINT = (
    "Xem configs/datasets/cosmetics.yaml để biết các khoá cần có."
)


class DatasetError(Exception):
    """Lỗi cấu hình dataset (thiếu khoá, sai đường dẫn, định dạng chưa hỗ trợ)."""


# ---------------------------------------------------------------------
# Danh sách và nội dung cấu hình
# ---------------------------------------------------------------------


def available():
    """Tên các dataset đã có file cấu hình trong configs/datasets/."""
    directory = config.DATASET_CONFIG_DIR
    if not directory.is_dir():
        return []
    return sorted(path.stem for path in directory.glob("*.yaml"))


def default_name():
    """Dataset mặc định: dataset đầu tiên theo thứ tự chữ cái."""
    names = available()
    if not names:
        raise DatasetError(
            "Chưa có file cấu hình dataset nào trong {}. Tạo một file "
            "configs/datasets/<tên>.yaml trước. {}".format(
                config.DATASET_CONFIG_DIR, DATASET_ERROR_HINT
            )
        )
    return names[0]


def config_path(name):
    """Đường dẫn file cấu hình của một dataset."""
    return config.DATASET_CONFIG_DIR / "{}.yaml".format(name)


def suggest(name):
    """Câu gợi ý tên dataset gần đúng khi người dùng gõ sai tên.

    Gõ sai một ký tự là chuyện thường (`consmetics` thay vì `cosmetics`), và
    thông báo lỗi nên chỉ luôn tên đúng thay vì chỉ nói "không tìm thấy".
    """
    similar = difflib.get_close_matches(name, available(), n=3, cutoff=0.6)
    if not similar:
        return ""
    return "Có phải bạn muốn: {}?".format(" hoặc ".join(similar))


def load_config(name=None):
    """Đọc và chuẩn hoá cấu hình dataset.

    Ngoài các khoá trong file YAML, hàm còn bổ sung:
        _path        : đường dẫn file cấu hình
        _raw_dir     : thư mục dữ liệu gốc (đã tính thành đường dẫn tuyệt đối)
        _label_to_id : bảng mã nhãn (nhãn chữ -> mã số)
    """
    name = name or default_name()
    path = config_path(name)
    if not path.exists():
        hint = suggest(name)
        raise DatasetError(
            "Không tìm thấy cấu hình dataset '{}' tại {}. Các dataset hiện có: {}. {}{}".format(
                name, config_path(name), ", ".join(available()) or "(trống)",
                hint + " " if hint else "", DATASET_ERROR_HINT)
        )

    with open(path, "r", encoding="utf-8") as handle:
        cfg = yaml.safe_load(handle) or {}

    cfg.setdefault("name", name)
    cfg.setdefault("version", "0.0.0")
    cfg.setdefault("format", "csv")
    cfg.setdefault("text_column", config.TEXT_COLUMN)
    cfg["aspects"] = list(cfg.get("aspects") or [])
    cfg["labels"] = list(cfg.get("labels") or [])
    cfg["drop_columns"] = list(cfg.get("drop_columns") or [])
    cfg["splits"] = dict(cfg.get("splits") or {})
    cfg["raw_dir"] = str(cfg.get("raw_dir") or "data/raw/{}".format(cfg["name"]))

    cfg["_path"] = path
    cfg["_raw_dir"] = _resolve(cfg["raw_dir"])
    cfg["_label_to_id"] = label_encoding(cfg)

    _check(cfg)
    return cfg


def _resolve(relative_path):
    """Đổi đường dẫn (tương đối so với gốc dự án hoặc tuyệt đối) thành Path."""
    path = Path(relative_path)
    return path if path.is_absolute() else (config.ROOT_DIR / path)


def _check(cfg):
    """Kiểm tra cấu hình có đủ thông tin để chạy hay không."""
    if not cfg["aspects"]:
        raise DatasetError(
            "Dataset '{}' chưa khai báo 'aspects'. {}".format(
                cfg["name"], DATASET_ERROR_HINT)
        )
    if not cfg["labels"]:
        raise DatasetError(
            "Dataset '{}' chưa khai báo 'labels'. {}".format(
                cfg["name"], DATASET_ERROR_HINT)
        )
    if not cfg["splits"]:
        raise DatasetError(
            "Dataset '{}' chưa khai báo các file trong 'splits'. {}".format(
                cfg["name"], DATASET_ERROR_HINT)
        )
    loaders.get(cfg["format"])  # báo lỗi ngay nếu định dạng chưa được hỗ trợ


def label_encoding(cfg):
    """Bảng mã nhãn: 0 = không nhắc tới, rồi tới nhãn theo thứ tự khai báo.

    Giữ nguyên mã quen thuộc của dự án khi nhãn trùng tên
    (positive = 1, negative = 2, neutral = 3) để model không phải đổi.
    """
    encoding = {config.NULL_LABEL: 0}
    for index, label in enumerate(cfg.get("labels") or [], start=1):
        encoding[label] = config.LABEL_TO_ID.get(label, index)
    return encoding


def expected_columns(cfg):
    """Danh sách cột mong đợi sau khi nạp (cột văn bản + các aspect)."""
    return [config.TEXT_COLUMN] + list(cfg["aspects"])


def describe(cfg):
    """Vài dòng thông tin về dataset, dùng cho phần đầu báo cáo."""
    return [
        "Dataset: {}".format(cfg["name"]),
        "Phiên bản dữ liệu gốc: v{}".format(cfg.get("version", "?")),
        "Định dạng nguồn: {}".format(cfg["format"]),
        "Nguồn dữ liệu: {}".format(_display(cfg["_raw_dir"])),
        "Số khía cạnh khai báo trong config: {}".format(len(cfg["aspects"])),
        "Cột văn bản trong file gốc: {}".format(cfg["text_column"]),
    ]


def _display(path):
    try:
        return Path(path).relative_to(config.ROOT_DIR).as_posix()
    except ValueError:
        return str(path)

# ---------------------------------------------------------------------
# Nạp dữ liệu
# ---------------------------------------------------------------------


def standardize(frame, cfg):
    """Đưa DataFrame về DẠNG CHUẨN NỘI BỘ.

    Việc làm:
    - Đổi tên cột văn bản của dataset thành "text".
    - Bỏ các cột khai báo trong `drop_columns`.
    - Bỏ mọi cột khác không thuộc schema.
    - Cột aspect thiếu trong file gốc được thêm vào với giá trị rỗng.

    Trả về (frame_mới, danh sách cột aspect bị thiếu).
    Nội dung ô KHÔNG bị sửa (không strip, không đổi chữ) — việc đó thuộc pipeline.
    """
    text_column = cfg["text_column"]
    if text_column not in frame.columns:
        raise DatasetError(
            "Dataset '{}': file gốc không có cột văn bản '{}'. Các cột đang có: {}. "
            "Sửa khoá 'text_column' trong {}.".format(
                cfg["name"], text_column, ", ".join(map(str, frame.columns)),
                _display(cfg["_path"])
            )
        )

    missing = [aspect for aspect in cfg["aspects"] if aspect not in frame.columns]
    frame = frame.copy()
    frame = frame.rename(columns={text_column: config.TEXT_COLUMN})

    drop = [column for column in cfg["drop_columns"] if column in frame.columns]
    if drop:
        frame = frame.drop(columns=drop)

    for aspect in missing:
        frame[aspect] = ""

    keep = expected_columns(cfg)
    frame = frame[[column for column in keep if column in frame.columns]]
    for column in frame.columns:
        frame[column] = frame[column].fillna("").astype(str)
    return frame, missing


def read_file(cfg, filename):
    """Đọc một file trong thư mục dữ liệu gốc của dataset."""
    path = Path(cfg["_raw_dir"]) / filename
    if not path.exists():
        raise FileNotFoundError(
            "Không tìm thấy file dữ liệu gốc: {}. Kiểm tra thư mục '{}' và các "
            "file khai báo trong {}.".format(
                path, cfg["raw_dir"], _display(cfg["_path"])
            )
        )
    return loaders.read(path, cfg["format"])


def load_splits(cfg):
    """Nạp toàn bộ file split.

    Trả về (splits, missing) trong đó:
        splits  : {"train": DataFrame, "val": DataFrame, ...}
        missing : {"train": [các cột aspect bị thiếu], ...}
    """
    splits = {}
    missing = {}
    for name, filename in cfg["splits"].items():
        frame, absent = standardize(read_file(cfg, filename), cfg)
        splits[name] = frame
        if absent:
            missing[name] = absent
    return splits, missing


def load_full(cfg):
    """Nạp file gộp (nếu dataset có khai báo). Trả về (DataFrame hoặc None, missing)."""
    filename = cfg.get("full")
    if not filename:
        return None, []
    path = Path(cfg["_raw_dir"]) / filename
    if not path.exists():
        return None, []
    return standardize(read_file(cfg, filename), cfg)
