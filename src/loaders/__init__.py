# -*- coding: utf-8 -*-
"""Đăng ký các định dạng dữ liệu nguồn.

Đây là NƠI DUY NHẤT quyết định "file có đuôi/định dạng này thì đọc thế nào".

THÊM MỘT ĐỊNH DẠNG MỚI
---
1. Tạo file mới trong src/loaders/, ví dụ `excel_loader.py`.
2. Trong file đó viết hàm `read(path) -> pandas.DataFrame`, theo đúng HỢP ĐỒNG
   ghi trong src/loaders/base.py (giữ nguyên tên cột, ô trống = chuỗi rỗng).
3. Import module đó ở đây và thêm vào dict `LOADERS` với khoá là giá trị
   `format` sẽ dùng trong configs/datasets/*.yaml.

Phần còn lại của dự án (EDA, pipeline, báo cáo) không cần biết gì thêm.
"""

from src.loaders import base, csv_loader, jsonl_loader, parquet_loader

LOADERS = {
    "csv": csv_loader,
    "jsonl": jsonl_loader,
    "parquet": parquet_loader,
}


def formats():
    """Danh sách định dạng được hỗ trợ."""
    return sorted(LOADERS)


def get(fmt):
    """Trả về module loader của một định dạng. Báo lỗi rõ nếu chưa hỗ trợ."""
    key = str(fmt or "").lower().strip()
    if key not in LOADERS:
        raise ValueError(
            "Chưa hỗ trợ định dạng '{}'. Các định dạng hiện có: {}. "
            "Muốn thêm: viết hàm read(path) trong src/loaders/ rồi đăng ký "
            "trong LOADERS.".format(fmt, ", ".join(formats()))
        )
    return base.check(LOADERS[key], key)


def read(path, fmt):
    """Đọc một file theo định dạng đã khai báo."""
    return get(fmt).read(path)
