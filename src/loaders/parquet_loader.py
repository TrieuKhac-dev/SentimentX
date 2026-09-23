# -*- coding: utf-8 -*-
"""Đọc file Parquet.

Parquet cần thư viện `pyarrow`. Dự án không bắt buộc cài pyarrow: chỉ những
dataset khai báo `format: parquet` mới cần. Nếu chưa cài, loader báo lỗi
kèm đúng câu lệnh cần chạy.
"""

import pandas as pd

from src.loaders import base

INSTALL_HINT = "Đọc Parquet cần thư viện pyarrow. Cài bằng: pip install pyarrow"


def read(path):
    """Đọc Parquet; cột văn bản/nhãn được đưa về dạng chuỗi."""
    try:
        frame = pd.read_parquet(path)
    except ImportError as exc:  # chưa cài pyarrow
        raise ImportError("{} (chi tiết: {})".format(INSTALL_HINT, exc))

    # Quy ước: ô trống = chuỗi rỗng (xem src/loaders/base.py).
    return base.as_text_frame(frame)
