# -*- coding: utf-8 -*-
"""Đọc file CSV.

Đây chỉ là một trong các loader. Xem src/loaders/__init__.py để biết cách
thêm định dạng mới.
"""

import pandas as pd


def read(path):
    """Đọc CSV luôn ở dạng chuỗi (string).

    Hai lựa chọn quan trọng:
    - encoding 'utf-8-sig': đọc được CẢ file có BOM và file không có BOM.
    - keep_default_na=False: ô trống giữ nguyên là chuỗi rỗng "".
      Điều này rất quan trọng vì ô trống ở cột aspect nghĩa là
      "aspect này không được nhắc tới" — không được biến thành NaN.
    """
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
