# -*- coding: utf-8 -*-
"""Registry các CÁCH HUẤN LUYỆN, và hai hợp đồng phải giữ.

    lora    LoRA (peft) trên model encoder, thêm một đầu phân loại cho mỗi khía cạnh

CÁCH DÙNG (`src/experiments/encoder_run.py` gọi; notebook không gọi trực tiếp)

    trainer = training.get(config["trainer"])
    report = trainer.fit(config, model_id=..., out_dir=..., train=..., val=..., ...)

HỢP ĐỒNG CỦA MỘT TRAINER
    NAME, DESCRIPTION
    check(config, model_id)                  thứ cần có TRƯỚC khi chạy (gọi từ preflight/CI)
    fit(...)  -> dict                        huấn luyện, trả số liệu của lượt huấn luyện
    predict(...) -> list[list[int]]          suy luận ra MÃ NHÃN, để phần chấm điểm dùng chung
    head_state_of(found) -> str    (tuỳ chọn) câu mô tả "cái gì đang học"; thiếu thì dùng
                                              câu của đường LoRA (xem `head_state`)

`fit` phải ghi checkpoint, nhưng KHÔNG tự quyết định chính sách và chỗ lưu: chính sách + `Store` nằm ở
`src/training/checkpoints.py`, còn CÁCH GHI trọng số ở một writer trong `src/training/savers/`
(bây giờ: `adapter` cho LoRA). `fit` chỉ trả `last_dir`/`best_dir` trong kết quả của nó.

Thêm cách huấn luyện mới: viết một module trong thư mục này rồi thêm MỘT dòng vào `TRAINERS`, và
khai `training.trainer: <tên>` trong config của thí nghiệm.
"""

from src.training import encoders, full, lora, none

# Các cách huấn luyện đang có, theo thứ tự đọc.
TRAINERS = {
    lora.NAME: lora,
    none.NAME: none,
    full.NAME: full,
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


def head_state(found):
    """Nhãn nói CHÍNH XÁC cái gì đang học ở lượt này, theo CÁCH HUẤN LUYỆN đã khai.

    MỘT CHỖ DUY NHẤT cho câu in ra màn hình và ghi vào `run.log`. Trước đây
    `src/experiments/encoder_run.py` tự chọn câu theo mỗi `head.trainable`, nên hai lượt KHÔNG có
    adapter nào (`trainer: none`) bị in bằng câu của đường LoRA: lượt SÀN hiện ra là "ĐÓNG BĂNG -
    chỉ adapter học", còn lượt linear probe hiện ra là "HỌC cùng adapter". Người đọc `run.log`
    tưởng có một adapter đang học, và mất luôn ý nghĩa của phép đối chứng âm - đã gặp thật khi chạy
    smoke đợt 11.

    Cách huấn luyện nào tự khai `head_state_of` thì dùng câu của nó (`none`, `full`); còn lại (kể cả
    tên trainer lạ) dùng câu của đường LoRA.
    """
    found = found or {}
    module = TRAINERS.get(str(found.get("trainer") or ""))
    if module is not None and hasattr(module, "head_state_of"):
        return module.head_state_of(found)
    return "HỌC cùng adapter" if found.get("head_trainable") else "ĐÓNG BĂNG - chỉ adapter học"


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
