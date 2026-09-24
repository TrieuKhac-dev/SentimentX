# -*- coding: utf-8 -*-
"""Cấu hình và nạp MỘT dataset.

Mọi thứ thuộc về SCHEMA của dữ liệu (tên cột văn bản, danh sách aspect, nhãn
hợp lệ, nguồn dữ liệu) đều nằm trong file phiên bản
configs/datasets/<tên>/<version>.yaml.
Nhờ vậy: thêm dataset mới, hoặc thêm phiên bản mới, không phải sửa code EDA/pipeline.

DẠNG CHUẨN NỘI BỘ
---
Sau khi nạp, mọi DataFrame trong dự án đều có dạng:
    cột "text"  +  một cột cho mỗi aspect (nhãn để ở dạng CHUỖI)
Ô trống ở cột aspect nghĩa là "aspect này không được nhắc tới" (null).
"""

import difflib
from pathlib import Path

import yaml

from src import config, loaders, paths

DATASET_ERROR_HINT = (
    "Xem một file configs/datasets/<tên>/<version>.yaml để biết các khoá cần có."
)


CONFIG_SUFFIX = ".yaml"


class DatasetError(Exception):
    """Lỗi cấu hình dataset (thiếu khoá, sai đường dẫn, định dạng chưa hỗ trợ)."""


# ---
# Danh sách và nội dung cấu hình
# ---


def available():
    """Tên các dataset đã có thư mục cấu hình trong configs/datasets/."""
    directory = config.DATASET_CONFIG_DIR
    if not directory.is_dir():
        return []
    return sorted(path.name for path in directory.iterdir() if path.is_dir())


def versions(name):
    """Các phiên bản đã khai của một dataset, theo thứ tự tên file."""
    directory = config.DATASET_CONFIG_DIR / str(name)
    if not directory.is_dir():
        return []
    return sorted(path.stem for path in directory.glob("*" + CONFIG_SUFFIX))


def default_name():
    """Dataset mặc định: dataset đầu tiên theo thứ tự chữ cái."""
    names = available()
    if not names:
        raise DatasetError(
            "Chưa có thư mục cấu hình dataset nào trong {}. Tạo "
            "<tên>/<version>.yaml ở đó trước. {}".format(
                config.DATASET_CONFIG_DIR, DATASET_ERROR_HINT
            )
        )
    return names[0]


def config_path(name, version=None):
    """Đường dẫn file cấu hình của một phiên bản dataset.

    Không truyền `version` thì lấy phiên bản mới nhất theo tên file.
    """
    directory = config.DATASET_CONFIG_DIR / str(name)
    if version:
        return directory / "{}{}".format(version, CONFIG_SUFFIX)
    found = versions(name)
    if not found:
        raise DatasetError(
            "Dataset '{}' chưa có phiên bản nào trong {}. {}".format(
                name, _display(directory), DATASET_ERROR_HINT)
        )
    return directory / "{}{}".format(found[-1], CONFIG_SUFFIX)


def suggest(name):
    """Câu gợi ý tên dataset gần đúng khi người dùng gõ sai tên.

    Gõ sai một ký tự là chuyện thường (`consmetics` thay vì `cosmetics`), và
    thông báo lỗi nên chỉ luôn tên đúng thay vì chỉ nói "không tìm thấy".
    """
    similar = difflib.get_close_matches(name, available(), n=3, cutoff=0.6)
    if not similar:
        return ""
    return "Có phải bạn muốn: {}?".format(" hoặc ".join(similar))


def load_config(name=None, version=None):
    """Đọc và chuẩn hoá cấu hình một phiên bản dataset.

    Ngoài các khoá trong file YAML, hàm còn bổ sung:
        _path        : đường dẫn file cấu hình
        _sources     : từng nguồn kèm thư mục đã giải
        _raw_dir     : thư mục dữ liệu gốc, chỉ khi có đúng một nguồn `raw`
        _label_to_id : bảng mã nhãn (nhãn chữ -> mã số)
    """
    name = name or default_name()
    path = config_path(name, version)
    if not path.exists():
        hint = suggest(name)
        raise DatasetError(
            "Không tìm thấy cấu hình dataset '{}' phiên bản '{}' tại {}. Các dataset hiện "
            "có: {}; các phiên bản của '{}': {}. {}{}".format(
                name, version or "(mới nhất)", _display(path),
                ", ".join(available()) or "(trống)", name,
                ", ".join(versions(name)) or "(trống)",
                hint + " " if hint else "", DATASET_ERROR_HINT)
        )

    with open(path, "r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    cfg = _normalize(raw, name, path)
    _check(cfg)
    return cfg


def _normalize(raw, name, path):
    """Đổi file phiên bản thành dạng phẳng mà phần còn lại của dự án đang dùng.

    File khai schema lồng trong khoá `schema`; ở đây đổi thành khoá phẳng (`text_column`,
    `aspects`, `labels`, `drop_columns`, `keep_columns`) để EDA và pipeline không phải biết
    cấu trúc file. Các khoá khai báo như `sources`, `eval_lock` được giữ nguyên để báo cáo
    và phần kiểm tra dùng lại.
    """
    schema = dict(raw.get("schema") or {})
    text = dict(schema.get("text") or {})
    identifier = dict(schema.get("id") or {})
    cfg = dict(raw)
    cfg.update({
        "name": raw.get("name") or name,
        "version": str(raw.get("version") or ""),
        "format": raw.get("format") or "csv",
        "splits": dict(raw.get("splits") or {}),
        "aspect_policy": raw.get("aspect_policy"),
        "eval_lock": dict(raw.get("eval_lock") or {}),
        "text_column": text.get("column"),
        "id_column": identifier.get("column"),
        "aspects": list(schema.get("aspects") or []),
        "labels": list(schema.get("labels") or []),
        "drop_columns": list(schema.get("drop") or []),
        "keep_columns": list(schema.get("keep") or []),
        "sources": [dict(item) for item in (raw.get("sources") or [])],
    })
    cfg["_path"] = path
    cfg["_sources"] = sources_of(cfg)
    raw_dirs = [source["dir"] for source in cfg["_sources"] if source["kind"] == "raw"]
    cfg["_raw_dir"] = raw_dirs[0] if len(raw_dirs) == 1 else None
    cfg["_label_to_id"] = label_encoding(cfg)
    return cfg


def sources_of(cfg):
    """Từng nguồn của dataset, kèm thư mục đã giải thành đường dẫn tuyệt đối.

    Nguồn `raw` trỏ vào `data/raw/<name>/<raw_version>/`; nguồn `dataset` trỏ vào
    `data/processed/<mã>/`.
    """
    result = []
    for item in cfg.get("sources") or []:
        kind = item.get("kind")
        if kind == "raw":
            directory = paths.raw_dir(item.get("name"), item.get("raw_version"))
        elif kind == "dataset":
            directory = paths.processed(item.get("version"))
        else:
            raise DatasetError(
                "Nguồn '{}' có 'kind' không hợp lệ: {!r}, chỉ nhận 'raw' hoặc 'dataset'. "
                "{}".format(item.get("name"), kind, DATASET_ERROR_HINT)
            )
        result.append({
            "kind": kind,
            "name": item.get("name"),
            "version": item.get("raw_version") if kind == "raw" else item.get("version"),
            "dir": directory,
        })
    return result


def _check(cfg):
    """Kiểm tra cấu hình có đủ thông tin để chạy hay không.

    Thiếu gì thì nói rõ thiếu gì và đọc từ file nào, không tự điền giá trị mặc định.
    """

    def _fail(message):
        raise DatasetError("{} (đọc từ {}).".format(message, _display(cfg["_path"])))

    stem = Path(cfg["_path"]).stem
    if not cfg["version"]:
        _fail("Dataset '{}' chưa khai báo 'version'".format(cfg["name"]))
    if cfg["version"] != stem:
        _fail("Dataset '{}': 'version' là {!r} nhưng tên file là {!r}, hai giá trị này phải "
              "trùng nhau".format(cfg["name"], cfg["version"], stem))
    if cfg["name"] != Path(cfg["_path"]).parent.name:
        _fail("Dataset '{}': 'name' phải trùng tên thư mục '{}'".format(
            cfg["name"], Path(cfg["_path"]).parent.name))
    if not cfg["sources"]:
        _fail("Dataset '{}' chưa khai báo 'sources'".format(cfg["name"]))
    if not cfg.get("pipeline_version"):
        _fail("Dataset '{}' chưa khai báo 'pipeline_version'".format(cfg["name"]))
    if not cfg["text_column"]:
        _fail("Dataset '{}' chưa khai báo 'schema.text.column'".format(cfg["name"]))
    if not cfg["aspects"]:
        _fail("Dataset '{}' chưa khai báo 'schema.aspects'".format(cfg["name"]))
    if not cfg["labels"]:
        _fail("Dataset '{}' chưa khai báo 'schema.labels'".format(cfg["name"]))
    if not cfg["splits"]:
        _fail("Dataset '{}' chưa khai báo 'splits'".format(cfg["name"]))
    missing = [name for name in ("train", "val", "test") if name not in cfg["splits"]]
    if missing:
        _fail("Dataset '{}' thiếu split trong 'splits': {}".format(
            cfg["name"], ", ".join(missing)))
    if cfg["aspect_policy"] not in ("union", "strict"):
        _fail("Dataset '{}': 'aspect_policy' phải là 'union' hoặc 'strict', đang là {!r}".format(
            cfg["name"], cfg["aspect_policy"]))
    lock = cfg["eval_lock"]
    if lock and lock.get("enforce", True) and not (lock.get("test") or {}).get("file"):
        _fail("Dataset '{}': 'eval_lock.test.file' là bắt buộc khi 'eval_lock.enforce' bật".format(
            cfg["name"]))
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
    """Danh sách cột mong đợi sau khi nạp: cột văn bản, các aspect, rồi cột giữ thêm."""
    return [config.TEXT_COLUMN] + list(cfg["aspects"]) + list(cfg.get("keep_columns") or [])


def describe(cfg):
    """Vài dòng thông tin về dataset, dùng cho phần đầu báo cáo."""
    lines = [
        "Dataset: {} (phiên bản {})".format(cfg["name"], cfg["version"]),
        "Pipeline dùng để tạo dataset: {}".format(cfg.get("pipeline_version", "?")),
        "Định dạng nguồn: {}".format(cfg["format"]),
        "Cột văn bản trong file gốc: {}".format(cfg["text_column"]),
        "Số khía cạnh khai báo trong config: {}".format(len(cfg["aspects"])),
    ]
    for source in cfg["_sources"]:
        lines.append("Nguồn {}: {} ({})".format(
            source["kind"], _display(source["dir"]), source["version"]))
    return lines


def _display(path):
    try:
        return Path(path).relative_to(config.ROOT_DIR).as_posix()
    except ValueError:
        return str(path)

# ---
# Nạp dữ liệu
# ---


def standardize(frame, cfg):
    """Đưa DataFrame về DẠNG CHUẨN NỘI BỘ.

    Việc làm:
    - Đổi tên cột văn bản của dataset thành "text".
    - Bỏ các cột khai báo trong `drop_columns`.
    - Bỏ mọi cột khác không thuộc schema.
    - Cột aspect thiếu trong file gốc được thêm vào với giá trị rỗng.

    Trả về (frame_mới, danh sách cột aspect bị thiếu).
    Nội dung ô KHÔNG bị sửa (không strip, không đổi chữ) - việc đó thuộc pipeline.
    """
    text_column = cfg["text_column"]
    if text_column not in frame.columns:
        raise DatasetError(
            "Dataset '{}': file gốc không có cột văn bản '{}'. Các cột đang có: {}. "
            "Sửa khoá 'schema.text.column' trong {}.".format(
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
                path, _display(cfg["_raw_dir"]), _display(cfg["_path"])
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
