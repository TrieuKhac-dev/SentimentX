# -*- coding: utf-8 -*-
"""Mã phiên bản cho mỗi lần chạy — để kết quả cũ KHÔNG bị ghi đè.

MÃ PHIÊN BẢN (version_id) ĐƯỢC TÍNH TỪ
-------------------------------------
    nội dung file cấu hình dataset  (configs/datasets/<tên>.yaml)
  + nội dung file cấu hình pipeline (configs/pipeline.yaml)
  + nội dung TẤT CẢ file dữ liệu gốc (data/raw/<tên>/**)

Kết quả là một chuỗi dạng:  cosmetics-v0.1.0-1a2b3c4d

Ý nghĩa:
    - Cùng dữ liệu + cùng config  -> cùng mã -> chạy lại cho ra đúng kết quả cũ.
    - Đổi config (ví dụ bật repeated_chars) -> mã KHÁC -> phiên bản mới,
      kết quả cũ vẫn còn nguyên để so sánh.
    - Đổi dữ liệu gốc -> mã KHÁC (vì nội dung file gốc cũng được đưa vào hash).

CÂY THƯ MỤC KẾT QUẢ
-------------------
    data/processed/versions/<mã>/processed_train.csv, label_map.json, processing_log.json, ...
    data/reports/eda/versions/<mã>/eda_result.json, report.html, ...
    data/reports/pipeline/versions/<mã>/pipeline_result.json, report.html, ...
    data/processed/manifest.json      <- mục lục của mọi phiên bản đã chạy
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path

from src import config, utils

MANIFEST_SCHEMA = 1

# Số ký tự hash dùng trong mã phiên bản (đủ để không trùng trên thực tế)
HASH_LENGTH = 8


# ---------------------------------------------------------------------
# Tính mã phiên bản
# ---------------------------------------------------------------------


def compute_id(dataset_cfg, pipeline_cfg=None):
    """Tính mã phiên bản từ config + nội dung dữ liệu gốc.

    `pipeline_cfg` có thể là dict cấu hình pipeline hoặc đường dẫn file.
    """
    digest = hashlib.sha1()

    digest.update(b"dataset:")
    digest.update(_file_bytes(dataset_cfg.get("_path")))

    digest.update(b"pipeline:")
    digest.update(_file_bytes(_config_path(pipeline_cfg)))

    digest.update(b"raw:")
    for path in sorted(Path(dataset_cfg["_raw_dir"]).rglob("*")):
        if path.is_file():
            name = path.relative_to(dataset_cfg["_raw_dir"]).as_posix()
            digest.update(name.encode("utf-8"))
            digest.update(path.read_bytes())

    name = str(dataset_cfg.get("name", "dataset"))
    data_version = str(dataset_cfg.get("version", "0.0.0"))
    return "{}-v{}-{}".format(name, data_version, digest.hexdigest()[:HASH_LENGTH])


def _config_path(value):
    """Chấp nhận cả dict cấu hình (có khoá _path) và đường dẫn trực tiếp."""
    if value is None:
        return None
    if isinstance(value, (str, Path)):
        return Path(value)
    return value.get("_path")


def _file_bytes(path):
    """Nội dung file cấu hình; file thiếu được coi là rỗng."""
    if not path:
        return b""
    path = Path(path)
    return path.read_bytes() if path.exists() else b""


# ---------------------------------------------------------------------
# Đường dẫn theo phiên bản
# ---------------------------------------------------------------------


def versions_dir(base):
    """Thư mục chứa tất cả phiên bản của một loại kết quả."""
    return Path(base) / "versions"


def version_dir(base, version_id):
    """Thư mục kết quả của MỘT phiên bản (tự tạo khi cần)."""
    return versions_dir(base) / version_id


def latest_version(base, dataset=None):
    """Mã phiên bản mới nhất có thư mục trong `base` (lọc theo dataset nếu có)."""
    directory = versions_dir(base)
    if not directory.is_dir():
        return None
    candidates = [
        path for path in directory.iterdir()
        if path.is_dir() and (dataset is None or path.name.startswith(dataset + "-"))
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime).name


# ---------------------------------------------------------------------
# Mục lục các lần chạy (manifest)
# ---------------------------------------------------------------------


def manifest_path():
    return config.PROCESSED_DIR / "manifest.json"


def read_manifest():
    """Đọc mục lục. Trả về dict rỗng nếu chưa có lần chạy nào."""
    path = manifest_path()
    if not path.exists():
        return {"schema": MANIFEST_SCHEMA, "entries": []}
    with open(path, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    manifest.setdefault("entries", [])
    return manifest


def prune_missing(manifest=None):
    """Bỏ khỏi mục lục những dòng trỏ tới file báo cáo KHÔNG CÒN TỒN TẠI.

    Vì sao cần: `record()` ghi dòng mới mà không kiểm file có thật hay không, nên xoá tay
    một file báo cáo (ví dụ dọn các lần chạy thử vài mẫu) để lại dòng mục lục trỏ vào khoảng
    không. Người đọc mục lục sẽ tưởng số liệu đó vẫn tra được — đúng loại dấu vết sai cần
    tránh. Chạy lại hàm này cũng là cách dọn định kỳ.
    """
    manifest = manifest or read_manifest()
    kept, dropped = [], []
    for entry in manifest["entries"]:
        report = entry.get("report")
        # Các pha cũ (EDA, pipeline) không truyền `report` → giữ nguyên, không suy diễn.
        if report and not (config.ROOT_DIR / report).exists():
            dropped.append(report)
        else:
            kept.append(entry)
    manifest["entries"] = kept
    if dropped:
        utils.write_json(manifest, manifest_path())
    return dropped


def record(entry):
    """Ghi một lần chạy vào mục lục.

    Khoá là bộ (mã phiên bản, pha, FILE BÁO CÁO): chạy lại cùng config và cùng dữ
    liệu sẽ THAY THẾ dòng cũ thay vì sinh thêm dòng trùng.

    Vì sao khoá có cả file báo cáo: cùng một phiên bản dữ liệu có thể có NHIỀU lần đo
    (ví dụ `--prompt X` và `--segmenter Y` ghi ra file riêng để không ghi đè nhau).
    Nếu khoá chỉ có (mã phiên bản, pha) thì lần đo sau sẽ xoá dấu vết của lần trước —
    mục lục nói một đằng, thư mục phiên bản có nhiều file một nẻo. Các pha cũ (EDA,
    pipeline) không truyền `report` nên khoá của chúng vẫn như trước.
    """

    def _same_run(existing):
        return (existing.get("version_id") == entry.get("version_id")
                and existing.get("phase") == entry.get("phase")
                and existing.get("report") == entry.get("report"))

    manifest = read_manifest()
    entry = dict(entry)
    entry.setdefault("created_at", datetime.now().strftime("%d/%m/%Y %H:%M"))

    entries = [existing for existing in manifest["entries"] if not _same_run(existing)]
    entries.append(entry)
    manifest["entries"] = entries
    manifest["updated_at"] = entry["created_at"]

    # Dọn luôn các dòng trỏ tới file đã bị xoá (xem `prune_missing`) — nhờ vậy mục lục không
    # tích tụ dấu vết trỏ vào khoảng không qua các lần dọn thư mục báo cáo.
    # LƯU Ý: hàm này sửa `manifest` TẠI CHỖ và trả về danh sách dòng đã bỏ; đừng gán lại giá
    # trị trả về (đã từng viết `... and manifest["entries"]`, và khi không có gì bị dọn thì
    # biểu thức đó trả về [] — xoá sạch mục lục).
    prune_missing(manifest)

    utils.write_json(manifest, manifest_path())
    return manifest_path()


def entries(dataset=None, phase=None):
    """Các lần chạy trong mục lục, lọc theo dataset và/hoặc pha báo cáo."""
    return [
        entry for entry in read_manifest()["entries"]
        if (dataset is None or entry.get("dataset") == dataset)
        and (phase is None or entry.get("phase") == phase)
    ]


def latest_entry(dataset=None, phase=None):
    """Lần chạy mới nhất trong mục lục."""
    matches = entries(dataset=dataset, phase=phase)
    return matches[-1] if matches else None


def processed_dir(version_id=None, dataset=None):
    """Thư mục chứa dữ liệu đã xử lý của một phiên bản.

    Không truyền gì -> lấy phiên bản mới nhất của dataset trong mục lục.
    Báo lỗi rõ ràng nếu chưa có lần chạy nào.
    """
    if not version_id:
        entry = latest_entry(dataset=dataset, phase="pipeline")
        version_id = entry["version_id"] if entry else latest_version(
            config.PROCESSED_DIR, dataset=dataset)

    if not version_id:
        raise FileNotFoundError(
            "Chưa có phiên bản dữ liệu nào trong {}. Hãy chạy "
            "'python run_pipeline.py' trước.".format(
                utils.rel(config.PROCESSED_DIR))
        )
    return version_dir(config.PROCESSED_DIR, version_id)


def summary_rows(limit=20):
    """Vài dòng mô tả các phiên bản gần nhất, để in ra console."""
    return [
        [
            entry.get("version_id", "?"),
            entry.get("phase", "?"),
            entry.get("created_at", "?"),
            entry.get("records", ""),
        ]
        for entry in read_manifest()["entries"][-limit:]
    ]
