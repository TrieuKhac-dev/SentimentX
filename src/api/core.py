# -*- coding: utf-8 -*-
"""Vùng CORE của mặt tiền: cấu hình, đường dẫn, tiện ích, mã phiên bản, danh mục dataset.

CHỈ re-export - không viết logic ở đây (test `tests/api/test_api.py` chặn). Chuyển nhà TRONG nhóm này
thì sửa file này; chuyển nhà KHÁC nhóm thì sửa file này + `src/api/__init__.py`.
"""

from src.core import config, dataset, paths, registry, runlog, utils, versioning  # noqa: F401

__all__ = ["config", "dataset", "paths", "registry", "runlog", "utils", "versioning"]
