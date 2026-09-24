# -*- coding: utf-8 -*-
"""Mã phiên bản dữ liệu và đường dẫn kết quả của một phiên bản.

MÃ PHIÊN BẢN
    <name>-ds<version>-pl<pipeline_version>-src<nguồn>@<phiên bản>-<hash8>

Ví dụ: cosmetics-ds0.1.0-pl0.1.0-srccosmetics@0.1.0-3f9a1c2d

    ds<version>             phiên bản dataset, lấy từ file cấu hình dataset
    pl<pipeline_version>    phiên bản pipeline dùng để tạo dataset
    src<nguồn>@<phiên bản>  từng nguồn; nhiều nguồn thì nối bằng dấu +
    <hash8>                 8 ký tự đầu của băm: nội dung hai file cấu hình và nội dung mọi
                            file dữ liệu của các nguồn

VÌ SAO BĂM CẢ NỘI DUNG FILE
Cùng đường dẫn nhưng khác nội dung là hai bộ dữ liệu khác nhau, nên phải ra hai mã khác nhau.
Nhờ vậy chạy lại cùng cấu hình và cùng dữ liệu cho ra đúng kết quả cũ, còn đổi cấu hình hoặc đổi
dữ liệu thì kết quả cũ vẫn còn nguyên để so sánh.

CÂY KẾT QUẢ CỦA MỘT PHIÊN BẢN
    data/processed/<mã>/train.csv, val.csv, test.csv, label_map.json, processing_log.json
    data/processed/<mã>/pipeline/   báo cáo của lần chạy pipeline
    data/raw/<name>/<raw_version>/eda/ hoặc data/processed/<mã>/eda/   kết quả EDA
"""

import hashlib
import json
from pathlib import Path

from src import paths, utils

# Số ký tự hash dùng trong mã phiên bản (đủ để không trùng trên thực tế)
HASH_LENGTH = 8

# Tên ba file dữ liệu của một dataset đã xử lý. Dùng khi một nguồn là dataset khác.
DATASET_FILES = ("train.csv", "val.csv", "test.csv")


# ---
# Tính mã phiên bản
# ---


class VersionError(Exception):
    """Lỗi liên quan tới phiên bản dữ liệu (file phiên bản bị sửa, thiếu phiên bản...)."""


def compute_id(dataset_cfg, pipeline_cfg=None):
    """Tính mã phiên bản từ cấu hình và nội dung dữ liệu của các nguồn.

    Không truyền `pipeline_cfg` thì nạp file pipeline ghi ở `pipeline_version` của dataset.
    """
    if pipeline_cfg is None:
        pipeline_cfg = utils.load_pipeline_config(dataset_cfg.get("pipeline_version"))

    digest = hashlib.sha1()
    digest.update(b"dataset:")
    digest.update(_file_bytes(dataset_cfg.get("_path")))
    digest.update(b"pipeline:")
    digest.update(_file_bytes(_config_path(pipeline_cfg)))
    digest.update(b"sources:")
    for source in dataset_cfg.get("_sources") or []:
        for path in source_files(dataset_cfg, source):
            name = path.relative_to(source["dir"]).as_posix()
            digest.update(name.encode("utf-8"))
            digest.update(utils.digest_bytes(path))

    sources = "+".join(
        "{}@{}".format(source.get("name"), _label(source.get("version")))
        for source in dataset_cfg.get("_sources") or []
    )
    return "{}-ds{}-pl{}-src{}-{}".format(
        dataset_cfg.get("name", "dataset"),
        _label(dataset_cfg.get("version")),
        _label(dataset_cfg.get("pipeline_version")),
        sources or "khong_nguon",
        digest.hexdigest()[:HASH_LENGTH],
    )


def _label(value):
    """Bỏ chữ 'v' ở đầu nhãn phiên bản cho gọn trong mã."""
    text = str(value or "")
    return text[1:] if text.startswith("v") else text


def source_files(dataset_cfg, source):
    """Các file dữ liệu của một nguồn, theo thứ tự tên.

    Nguồn `raw` chỉ lấy đúng file khai trong `splits` và `full`, không lấy cả thư mục: trong
    thư mục còn `raw_meta.yaml` và kết quả EDA, không phải dữ liệu.
    """
    if source.get("kind") == "dataset":
        names = list(DATASET_FILES)
    else:
        names = list((dataset_cfg.get("splits") or {}).values())
        if dataset_cfg.get("full"):
            names.append(dataset_cfg["full"])
    files = []
    for name in names:
        path = Path(source["dir"]) / str(name)
        if path.exists():
            files.append(path)
    return files


def _config_path(value):
    """Chấp nhận cả dict cấu hình (có khoá _path) và đường dẫn trực tiếp."""
    if value is None:
        return None
    if isinstance(value, (str, Path)):
        return Path(value)
    return value.get("_path")


def _file_bytes(path):
    """Nội dung file cấu hình để băm; file thiếu được coi là rỗng.

    Đi qua `utils.digest_bytes` để hai máy khác hệ điều hành ra cùng một mã (xem hàm đó).
    """
    if not path:
        return b""
    path = Path(path)
    return utils.digest_bytes(path) if path.exists() else b""


# ---
# Đường dẫn theo phiên bản
# ---


def processed_dir(version_id):
    """Thư mục dataset của một phiên bản: `data/processed/<mã>/`."""
    if not version_id:
        raise ValueError("Thiếu mã phiên bản dữ liệu.")
    return paths.processed(version_id)


def pipeline_report_dir(version_id):
    """Thư mục báo cáo pipeline, nằm trong thư mục dataset."""
    return processed_dir(version_id) / paths.pattern("pipeline_dir")


def processing_log_path(version_id):
    return processed_dir(version_id) / paths.pattern("processing_log")


def read_processing_log(version_id):
    """Đọc `processing_log.json` của một phiên bản; trả về dict rỗng nếu chưa có."""
    path = processing_log_path(version_id)
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle) or {}


def dataset_dirs():
    """Các phiên bản dataset đang có trên đĩa, mới nhất trước theo thời gian sửa."""
    root = paths.data("processed")
    if not root.is_dir():
        return []
    found = [
        path for path in root.iterdir()
        if path.is_dir() and not path.name.startswith(".")
    ]
    return sorted(found, key=lambda path: path.stat().st_mtime, reverse=True)


def latest_dataset(dataset=None):
    """Mã phiên bản dataset mới nhất trên đĩa; lọc theo tên dataset nếu có."""
    for path in dataset_dirs():
        if dataset is None or path.name.startswith(str(dataset) + "-ds"):
            return path.name
    return None


def file_sha256(path):
    """sha256 của một file, dùng cho guard bất biến và cho `eval_lock`.

    Băm qua `utils.digest_bytes`, tức file văn bản được chuẩn hoá kiểu xuống dòng trước khi băm. Cần
    như vậy vì `eval_lock.test.sha256` được ghi vào file config dataset ở một máy rồi ĐEM SO ở máy
    khác (máy cá nhân Windows ghi, Colab Linux đối chiếu): băm thẳng byte thì hai máy luôn lệch nhau
    và tập test bị coi là đã bị đổi.
    """
    digest = hashlib.sha256()
    digest.update(utils.digest_bytes(path))
    return digest.hexdigest()


def guard_versions(dataset_cfg=None, pipeline_cfg=None):
    """Chặn việc sửa file phiên bản đã dùng.

    Mọi `processing_log.json` đã ghi đều giữ sha256 của hai file cấu hình tại thời điểm chạy.
    Nếu file trên đĩa hiện khác giá trị đó thì file đã bị sửa SAU khi dùng, và kết quả cũ
    không còn dựng lại được từ chính file đó nữa. Đây là lỗi im lặng nguy hiểm nhất của cách
    đánh phiên bản theo nội dung, nên phải chặn chứ không chỉ cảnh báo.
    """
    watched = []
    for kind, cfg in (("dataset", dataset_cfg), ("pipeline", pipeline_cfg)):
        path = (cfg or {}).get("_path")
        if path:
            watched.append((kind, Path(path)))
    if not watched:
        return []

    problems = []
    for directory in dataset_dirs():
        log = read_processing_log(directory.name)
        if not log:
            continue
        for kind, path in watched:
            stored_block = log.get(kind) or {}
            stored = stored_block.get("config_sha256")
            # Chỉ so với log của ĐÚNG file đó, không so với file khác cùng loại.
            if not stored or stored_block.get("config") != utils.rel(path):
                continue
            current = file_sha256(path)
            if current != stored:
                problems.append(
                    "{}: {} đã bị sửa sau khi dùng (sha256 hiện tại {}, lúc chạy {}).".format(
                        directory.name, utils.rel(path), current[:8], stored[:8]))

    if problems:
        raise VersionError(
            "File phiên bản đã dùng thì không được sửa:\n  - {}\n"
            "Hãy tạo file phiên bản mới (copy rồi sửa, và đổi cả tên file), rồi chạy lại: "
            "kết quả cũ phải tra được từ đúng file đã tạo ra nó. Nếu lần chạy trước chỉ là chạy "
            "thử thì xoá thư mục kết quả cũ của mã đó rồi chạy lại.".format(
                "\n  - ".join(problems))
        )
    return problems



