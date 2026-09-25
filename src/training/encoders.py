# -*- coding: utf-8 -*-
"""Registry các model ENCODER huấn luyện được.

Vì sao có registry riêng: `src/preprocessing/` biết cách ĐO và CẮT input của từng model, còn ở đây
cần đúng hai thứ để huấn luyện - `CONFIG_NAME` (khớp file `configs/models/<model_id>.yaml`) và
`build_inputs()` (chuỗi đã tách từ nếu cần, đã cắt theo `max_length`, đã pad).

Thêm một encoder mới: viết module trong `src/preprocessing/` theo hợp đồng ở đó, rồi thêm MỘT dòng
vào `ENCODERS`. Không phải sửa `lora.py`.
"""

from src import model_config
from src.preprocessing import phobert, visobert

# Tên khoá là `model_id`, trùng tên file config của model.
ENCODERS = {
    phobert.CONFIG_NAME: phobert,
    visobert.CONFIG_NAME: visobert,
}


class EncoderError(Exception):
    """Không có encoder cho model này, hoặc module thiếu hàm mà bước huấn luyện cần."""


def available():
    """Tên các encoder huấn luyện được."""
    return sorted(ENCODERS)


def get(model_id):
    """Module preprocessing của một encoder. Tên sai thì báo lỗi kèm danh sách."""
    if model_id not in ENCODERS:
        raise EncoderError(
            "Chưa có encoder '{}' cho huấn luyện. Đang có: {}. Thêm một dòng vào "
            "src/training/encoders.py sau khi viết module trong src/preprocessing/.".format(
                model_id, ", ".join(available())))
    return ENCODERS[model_id]


def check():
    """Hợp đồng của registry: đúng tên, có `build_inputs`, và có file config tương ứng."""
    problems = []
    configured = set(model_config.available())
    for name, module in sorted(ENCODERS.items()):
        if getattr(module, "CONFIG_NAME", None) != name:
            problems.append("encoders[{}]: CONFIG_NAME là {!r}, phải bằng chính tên khoá".format(
                name, getattr(module, "CONFIG_NAME", None)))
        if not callable(getattr(module, "build_inputs", None)):
            problems.append("encoders[{}]: thiếu build_inputs()".format(name))
        if name not in configured:
            problems.append("encoders[{}]: chưa có configs/models/{}.yaml".format(name, name))
    return problems


def describe():
    """Vài dòng mô tả các encoder, để in ra khi cần."""
    return ["{:<16} {}".format(name, ENCODERS[name].MODEL_NAME) for name in available()]
