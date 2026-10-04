# -*- coding: utf-8 -*-
"""Model preprocessing cho CafeBERT (uitnlp/CafeBERT).

VÌ SAO CÓ: CafeBERT là encoder tiếng Việt dựng trên XLM-R (vocab 250.002, trần 514 vị trí), tức là
**model ĐA NGỮ được tiền huấn luyện TIẾP trên văn bản tiếng Việt**, khác hẳn PhoBERT (tiếng Việt từ đầu).
Nó là bậc thang giữa "tiếng Việt chuyên biệt" và "đa ngữ thuần" (XLM-R), nên bộ ba này tách được câu
"lợi thế đến từ KHO TIẾNG VIỆT hay từ KIẾN TRÚC".

KHÔNG tách từ: CafeBERT dùng SentencePiece trên văn bản NGUYÊN BẢN (giống ViSoBERT), nên `segmenter` là
`none` - chủ ý, và số liệu ghi rõ.
"""

from src.preprocessing import bert_like

MODEL_NAME = "uitnlp/CafeBERT"

# Tên file cấu hình trong configs/models/ (không cần đuôi .yaml); phải trùng `model_id` khai trong file.
CONFIG_NAME = "cafebert"

# XLM-R dùng SentencePiece: KHÔNG tách từ tiếng Việt.
SEGMENTER = "none"


def limit():
    """Ngưỡng cắt đang dùng: (giá trị, nguồn) - từ `configs/models/cafebert.yaml`."""
    return bert_like.limit(CONFIG_NAME)


def tokenizer():
    """Nạp tokenizer của CafeBERT một lần duy nhất."""
    return bert_like.tokenizer(CONFIG_NAME, MODEL_NAME)


def encode(texts):
    """Chuỗi id token (CHƯA cắt) - dùng cho việc ĐO độ dài input thật."""
    return bert_like.encode(CONFIG_NAME, MODEL_NAME, texts, SEGMENTER)


def build_inputs(texts, max_length=None):
    """Input cho model: dict của tokenizer (đã pad + cắt theo `max_length`)."""
    return bert_like.build_inputs(CONFIG_NAME, MODEL_NAME, texts, SEGMENTER, max_length)


def info():
    """Thông tin truy vết: tokenizer, từ vựng, ngưỡng cắt, `segmenter = none` (chủ ý)."""
    return bert_like.info(CONFIG_NAME, MODEL_NAME, SEGMENTER)
