# -*- coding: utf-8 -*-
"""Registry các CÁCH HUẤN LUYỆN, và hai hợp đồng phải giữ.

    lora    LoRA (peft) trên model encoder, thêm một đầu phân loại cho mỗi khía cạnh

CÁCH DÙNG (`src/encoder_run.py` gọi; notebook không gọi trực tiếp)

    trainer = training.get(config["trainer"])
    report = trainer.fit(config, model_id=..., out_dir=..., train=..., val=..., ...)

HỢP ĐỒNG CỦA MỘT TRAINER
    NAME, DESCRIPTION
    check(config, model_id)                  thứ cần có TRƯỚC khi chạy (gọi từ preflight/CI)
    fit(...)  -> dict                        huấn luyện, trả số liệu của lượt huấn luyện
    predict(...) -> list[list[int]]          suy luận ra MÃ NHÃN, để phần chấm điểm dùng chung

`fit` phải ghi checkpoint theo `configs/experiments/training.yaml`: `model/last` (đủ để chạy tiếp)
và `model/best` (chỉ adapter, để suy luận). Đường dẫn hai thư mục đó lấy từ `configs/paths.yaml`.

Thêm cách huấn luyện mới: viết một module trong thư mục này rồi thêm MỘT dòng vào `TRAINERS`, và
khai `training.trainer: <tên>` trong config của thí nghiệm.
"""

from src.training import encoders, lora

# Các cách huấn luyện đang có, theo thứ tự đọc.
TRAINERS = {
    lora.NAME: lora,
}


def available():
    """Tên các cách huấn luyện đang có."""
    return list(TRAINERS)


def get(name):
    """Module của một cách huấn luyện. Tên sai thì báo lỗi kèm danh sách."""
    if name not in TRAINERS:
        raise lora.TrainingError(
            "Không có cách huấn luyện '{}'. Các cách hiện có: {}. Khai ở "
            "`configs/experiments/training.yaml` (khoá `trainer`).".format(
                name, ", ".join(available())))
    return TRAINERS[name]


def check(config, model_id=None):
    """Kiểm cách huấn luyện đã khai có chạy được không. Gom hết vấn đề rồi báo một lần."""
    name = str((config or {}).get("trainer") or "").strip()
    if not name:
        raise lora.TrainingError(
            "Thiếu `trainer` trong config huấn luyện: chưa biết dùng cách nào. Các cách hiện có: "
            "{}.".format(", ".join(available())))
    module = get(name)
    return module.check(config, model_id) if hasattr(module, "check") else []


def describe():
    """Vài dòng mô tả các cách huấn luyện, để in ra khi cần."""
    return ["{:<12} {}".format(name, TRAINERS[name].DESCRIPTION) for name in available()]
