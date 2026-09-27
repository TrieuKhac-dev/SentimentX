# -*- coding: utf-8 -*-
"""Registry CÁCH GHI TRỌNG SỐ của checkpoint. Hợp đồng ở ``base.py``.

    adapter   LoRA (peft): adapter + đầu phân loại cho mỗi khía cạnh

Thêm cách ghi mới (ví dụ full fine-tune ghi ``state_dict``): viết một module trong thư mục này rồi thêm
MỘT dòng vào ``SAVERS``. Trainer chọn writer bằng tên (``training.checkpoint_writer``); mặc định
``adapter`` để cấu hình cũ chạy nguyên như trước.
"""

from src.training.savers import adapter

SAVERS = {
    adapter.NAME: adapter,
}

DEFAULT = adapter.NAME


def available():
    """Tên các cách ghi trọng số đang có."""
    return list(SAVERS)


def get(name=None):
    """Module writer theo tên. Tên sai thì báo lỗi kèm danh sách."""
    name = str(name or DEFAULT).strip() or DEFAULT
    if name not in SAVERS:
        raise KeyError(
            "Không có cách ghi checkpoint {!r}. Các cách hiện có: {}.".format(
                name, ", ".join(available())))
    return SAVERS[name]


def check():
    """Việc phải sửa để dùng được các writer (rỗng là chạy được)."""
    problems = []
    for name in available():
        module = SAVERS[name]
        for function in ("save", "read_metadata", "check"):
            if not callable(getattr(module, function, None)):
                problems.append("savers: {!r} thiếu hàm {}()".format(name, function))
    return problems
