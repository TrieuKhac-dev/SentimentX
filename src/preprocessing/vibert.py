# -*- coding: utf-8 -*-
"""Model preprocessing cho ViBERT (FPTAI/vibert-base-cased).

VÌ SAO CÓ: ViBERT là encoder tiếng Việt KHÁC kho tiền huấn luyện với PhoBERT (dữ liệu wiki + tin tức
tiếng Việt của FPT), nên nó trả lời câu "kết quả của PhoBERT đến từ KIẾN TRÚC hay từ KHO VĂN BẢN?".

Khác PhoBERT ở một điểm phải khai rõ: kiến trúc `bert` (vocab 38.168, trần 512 vị trí) và tokenizer
theo ÂM TIẾT, nhưng vẫn là model ĐƯỢC TIỀN HUẤN LUYỆN TRÊN VĂN BẢN ĐÃ TÁCH TỪ, nên vẫn dùng bộ tách từ
chính chủ ("auto" -> vncorenlp, thiếu Java thì pyvi). Tên bộ tách từ được GHI vào số liệu đo được -
"cùng một review tách bằng VnCoreNLP và bằng pyvi cho ra số token khác nhau".
"""

from src.preprocessing import bert_like

MODEL_NAME = "FPTAI/vibert-base-cased"

# Tên file cấu hình trong configs/models/ (không cần đuôi .yaml); phải trùng `model_id` khai trong file.
CONFIG_NAME = "vibert-base-cased"

# ViBERT học trên văn bản đã tách từ, nên vẫn cần tách từ - dùng chung cơ chế với PhoBERT.
SEGMENTER = "auto"


def limit():
    """Ngưỡng cắt đang dùng: (giá trị, nguồn) - từ `configs/models/vibert-base-cased.yaml`."""
    return bert_like.limit(CONFIG_NAME)


def tokenizer():
    """Nạp tokenizer của ViBERT một lần duy nhất."""
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
