# -*- coding: utf-8 -*-
"""Model preprocessing cho PhoBERT-large (vinai/phobert-large).

VÌ SAO CÓ THÊM BẢN LỚN: đợt 7 hỏi "encoder LỚN hơn có vượt 96,62 của PhoBERT-base không" - cùng kho
tiền huấn luyện, cùng bộ tách từ, chỉ khác số tham số, nên đó là một biến sạch.

Khác bản `phobert-base-v2` ĐÚNG MỘT thứ: `checkpoint` (và tên file cấu hình). Cùng họ tokenizer
(roberta, vocab 64.000, trần 258 vị trí) và cùng bộ tách từ chính chủ - nên mã dùng chung ở
`bert_like.py`, còn file này chỉ khai ba hằng số.
"""

from src.preprocessing import bert_like

MODEL_NAME = "vinai/phobert-large"

# Tên file cấu hình trong configs/models/ (không cần đuôi .yaml); phải trùng `model_id` khai trong file.
CONFIG_NAME = "phobert-large"

# "auto" = vncorenlp (chính chủ, giống bản base), thiếu Java thì pyvi; tên bộ tách từ được GHI vào số liệu.
SEGMENTER = "auto"


def limit():
    """Ngưỡng cắt đang dùng: (giá trị, nguồn) - từ `configs/models/phobert-large.yaml`."""
    return bert_like.limit(CONFIG_NAME)


def tokenizer():
    """Nạp tokenizer của PhoBERT-large một lần duy nhất."""
    return bert_like.tokenizer(CONFIG_NAME, MODEL_NAME)


def segmenter_name(segmenter=None):
    """Tên bộ tách từ đang dùng, ví dụ "vncorenlp"."""
    return bert_like.segmenter_name(SEGMENTER if segmenter is None else segmenter)


def segment_all(texts, segmenter=None):
    """Tách từ cho cả dãy văn bản."""
    return bert_like.segment_all(texts, SEGMENTER if segmenter is None else segmenter)


def words(texts, segmenter=None):
    """Số ĐƠN VỊ sau tách từ - mẫu số của chỉ số "subword / từ"."""
    return bert_like.words(texts, SEGMENTER if segmenter is None else segmenter)


def encode(texts, segmenter=None):
    """Chuỗi id token (đã tách từ, CHƯA cắt) - dùng cho việc ĐO độ dài input thật."""
    return bert_like.encode(CONFIG_NAME, MODEL_NAME, texts, SEGMENTER, segmenter)


def build_inputs(texts, max_length=None, segmenter=None):
    """Input cho model: dict của tokenizer (đã pad + cắt theo `max_length`)."""
    return bert_like.build_inputs(CONFIG_NAME, MODEL_NAME, texts, SEGMENTER, max_length, segmenter)


def info(segmenter=None):
    """Thông tin truy vết: tokenizer, từ vựng, ngưỡng cắt, bộ tách từ."""
    return bert_like.info(CONFIG_NAME, MODEL_NAME, SEGMENTER, segmenter)
