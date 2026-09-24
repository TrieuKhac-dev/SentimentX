# -*- coding: utf-8 -*-
"""`none`: KHÔNG ghi nhận đi đâu cả.

Dùng khi chạy thử trên máy cá nhân, hoặc khi máy chủ không dùng được mà vẫn muốn chạy tiếp. Đây
là lựa chọn hợp lệ chứ không phải lỗi: kết quả vẫn nằm trong thư mục kết quả với `metrics.json`
và `run_meta.json`.
"""

from src.tracking import base

NAME = "none"
DESCRIPTION = "Không ghi nhận đi đâu cả; kết quả chỉ nằm trong thư mục kết quả."


def begin(config, dagshub, out_dir, info=None, log=None):
    """Phiên TẮT. Không có gì để kiểm vì không kết nối đi đâu."""
    return base.Session(active=False, reason="tracking.tracker = none")
