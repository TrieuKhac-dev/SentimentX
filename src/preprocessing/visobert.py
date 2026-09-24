# -*- coding: utf-8 -*-
"""Model preprocessing cho ViSoBERT (uitnlp/visobert).

Chuỗi bước:

    văn bản đã làm sạch
        -> tokenizer của ViSoBERT
        -> input_ids / attention_mask

Khác PhoBERT ở một điểm quan trọng: ViSoBERT được huấn luyện trên văn bản mạng xã
hội ở dạng NGUYÊN BẢN, nên **KHÔNG cần tách từ tiếng Việt**.

Đây chính là lý do phải tách "model preprocessing" khỏi pipeline chung: cùng một
dataset sạch, nhưng PhoBERT cần tách từ còn ViSoBERT thì không. Vì vậy dòng số liệu
của ViSoBERT luôn ghi `segmenter = none` - không phải "quên tách từ" mà là chủ ý, và
cột đó giúp phân biệt hai trường hợp khi đọc lại số liệu.
"""

from src import model_config

MODEL_NAME = "uitnlp/visobert"

# Tên file cấu hình trong configs/models/ (không cần đuôi .yaml); phải trùng `model_id`
# khai trong file đó.
CONFIG_NAME = "visobert"

# Ngưỡng cắt input KHÔNG có hằng số ở đây nữa: nó là `preprocess.max_length` trong
# configs/models/visobert.yaml = 256, và đó là LỰA CHỌN CỦA DỰ ÁN chứ không phải "khớp
# model" (trần kiến trúc thật của ViSoBERT là 514 vị trí, còn rất nhiều dư địa). Lý do chọn
# 256: review dài nhất trong dữ liệu cosmetics chỉ 229 token, và bằng PhoBERT (256) nên hai
# encoder có cùng ngân sách input, so sánh mới công bằng.

# ViSoBERT đọc văn bản nguyên bản; ghi hằng số ở đây để cột truy vết của số liệu nói
# rõ "không tách từ" là CHỦ Ý, chứ không phải thiếu cấu hình.
SEGMENTER = "none"

_TOKENIZER = None


def limit():
    """Ngưỡng cắt đang dùng: (giá trị, nguồn) - đọc từ configs/models/visobert.yaml."""
    return model_config.max_length(CONFIG_NAME)



def tokenizer():
    """Nạp tokenizer của ViSoBERT một lần duy nhất."""
    global _TOKENIZER
    if _TOKENIZER is None:
        try:
            from transformers import AutoTokenizer
        except ImportError as exc:  # pragma: no cover - phụ thuộc môi trường
            raise ImportError(
                "Thiếu thư viện transformers. Cài bằng:\n"
                "    pip install transformers torch"
            ) from exc
        _TOKENIZER = AutoTokenizer.from_pretrained(MODEL_NAME)
    return _TOKENIZER


def encode(texts):
    """Chuỗi id token của từng văn bản (CHƯA cắt theo max_length).

    Không cần torch, nên dùng được cho việc ĐO độ dài input thật trước khi huấn
    luyện (xem src/preprocessing/token_stats.py).
    """
    return tokenizer()(list(texts), add_special_tokens=True)["input_ids"]


def build_inputs(texts, max_length=None):
    """Chuyển danh sách văn bản thành input cho ViSoBERT.

    Trả về dict của tokenizer: {"input_ids": ..., "attention_mask": ...}

    `max_length` để None nghĩa là dùng ngưỡng ĐANG CÓ HIỆU LỰC (`limit()`: YAML của model
    > hằng số MAX_LENGTH) - cũng đúng giá trị mà token_stats dùng để đo.
    """
    if max_length is None:
        max_length = limit()[0]
    return tokenizer()(
        list(texts),
        padding=True,
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )


def info():
    """Thông tin để TRUY VẾT số liệu đo được: tokenizer, từ vựng, ngưỡng cắt.

    `segmenter` luôn là "none" ở đây, và đó là thông tin có ích chứ không phải chỗ
    trống: nó nói rằng model này KHÔNG dùng tách từ, khác hẳn PhoBERT.
    """
    found = tokenizer()
    value, source = limit()
    return {
        "tokenizer": type(found).__name__,
        "segmenter": SEGMENTER,
        "vocab": found.vocab_size,
        "unk_id": found.unk_token_id,
        "max_length": value,
        "max_length_source": source,
    }

