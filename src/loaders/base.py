# -*- coding: utf-8 -*-
"""Hợp đồng chung của mọi loader - đọc MỘT file nguồn thành DataFrame.

MỘT LOADER CHUẨN GỒM ĐÚNG MỘT HÀM
---
    def read(path) -> pandas.DataFrame

BỐN QUY ƯỚC BẮT BUỘC (phần còn lại của dự án dựa vào những điều này):

1. Giữ NGUYÊN tên cột như trong file gốc. Việc đổi tên cột văn bản thành
   "text" là do src/dataset.py làm, KHÔNG phải loader - vì mỗi dataset khai
   báo tên cột khác nhau ở khoá `text_column` trong configs/datasets/*.yaml.

2. Ô trống giữ nguyên là chuỗi rỗng "", KHÔNG được biến thành NaN.
   Ở cột aspect, ô trống nghĩa là "aspect này không được nhắc tới" (null),
   khác hoàn toàn với nhãn "neutral".

3. Không sửa nội dung văn bản. Loader chỉ ĐỌC: không strip, không đổi
   teencode, không xoá dòng trùng - những việc đó thuộc pipeline.

4. Trả về DataFrame với mọi dòng đọc được; dòng lỗi thì báo lỗi rõ ràng kèm
   số dòng, không tự bỏ qua.

Thêm định dạng mới: tạo một file trong thư mục này, viết `read()` theo đúng
hợp đồng trên, rồi đăng ký tên định dạng trong LOADERS ở __init__.py.
"""


import pandas as pd


def _to_text(value):
    """Đưa MỘT ô về chuỗi; ô thiếu (None / NaN) thành chuỗi rỗng."""
    if value is None or value is pd.NA:
        return ""
    if isinstance(value, float):
        if value != value:              # NaN -> ô trống
            return ""
        if value.is_integer():          # JSON number 7.0 -> "7", không phải "7.0"
            return str(int(value))
    return str(value)


def _is_text_dtype(dtype):
    """Cột chứa chữ?

    pandas 3 dùng dtype `str`/`string` cho cột chữ, còn pandas 1.x/2.x dùng
    `object` - hàm này nhận cả hai, và nhận cả object chứa dữ liệu hỗn hợp.
    Cột số (int64, float64, bool...) được coi là KHÔNG phải cột chữ.
    """
    return pd.api.types.is_string_dtype(dtype)


def as_text_frame(frame):
    """Ép các cột CHỮ về dạng chuỗi, ô thiếu thành "" (xem quy ước 2).

    Cột số được giữ nguyên - loader không quyết định kiểu dữ liệu của dữ liệu
    gốc; src/dataset.py mới là nơi ép mọi thứ về dạng chuẩn nội bộ.
    """
    for column in frame.columns:
        if _is_text_dtype(frame[column].dtype):
            frame[column] = frame[column].map(_to_text)
    return frame


def as_string_frame(frame):
    """Ép MỌI cột về chuỗi, kể cả cột số.

    Dùng cho định dạng không khai báo kiểu dữ liệu (JSONL) - ở đó một cột có
    thể vừa chứa "positive" vừa chứa 1, nên phải đọc tất cả như chữ để giữ
    đúng quy ước ô trống = chuỗi rỗng, và để nhãn số 1 không thành "1.0".
    """
    for column in frame.columns:
        frame[column] = frame[column].map(_to_text)
    return frame


def check(module, name=""):
    """Kiểm tra một module có đúng hợp đồng loader. Báo lỗi rõ nếu sai."""
    if not callable(getattr(module, "read", None)):
        raise TypeError(
            "Loader '{}' thiếu hàm read(path). Xem hợp đồng trong "
            "src/loaders/base.py.".format(
                name or getattr(module, "__name__", "?")
            )
        )
    return module
