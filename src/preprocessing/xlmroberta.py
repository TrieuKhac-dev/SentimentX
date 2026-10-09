# -*- coding: utf-8 -*-
"""Model preprocessing cho XLM-R base (FacebookAI/xlm-roberta-base) - **ĐỐI CHỨNG NGUỒN TIỀN HUẤN LUYỆN**.

VÌ SAO CÓ (nói cho đúng, tránh hiểu sai):
XLM-R đọc được tiếng Việt - câu hỏi ở đây KHÔNG phải "model có đọc được tiếng Việt không". Câu hỏi là
**"tiền huấn luyện CHUYÊN tiếng Việt có lợi thế rõ không?"**: bốn encoder kia (PhoBERT, ViBERT, CafeBERT,
ViSoBERT) đều học từ kho văn bản TIẾNG VIỆT, còn XLM-R học 100 ngôn ngữ nên phần tiếng Việt rất nhỏ.

⚠️ **CẢNH BÁO ĐỌC KẾT QUẢ**: XLM-R cũng KHÁC về BỘ TÁCH TỪ (SentencePiece, `segmenter: none`) so với
PhoBERT/ViBERT (`vncorenlp`). Vì vậy so XLM-R với PhoBERT là so HAI biến cùng lúc (kho tiền huấn luyện +
bộ tách từ) - không được kết luận gọn thành "cần tiếng Việt". Muốn tách biến thì xem thêm cặp
CafeBERT (đa ngữ + tiền huấn luyện tiếp tiếng Việt) và so với XLM-R: hai model CÙNG họ tokenizer.

Kiến trúc: xlm-roberta, vocab 250.002 (giống CafeBERT), trần 514 vị trí.
"""

from src.preprocessing import bert_like

MODEL_NAME = "FacebookAI/xlm-roberta-base"

# Tên file cấu hình trong configs/models/ (không cần đuôi .yaml); phải trùng `model_id` khai trong file.
CONFIG_NAME = "xlm-roberta-base"

# SentencePiece trên văn bản nguyên bản: KHÔNG tách từ tiếng Việt (đây cũng là một phần của đối chứng).
SEGMENTER = "none"


def limit():
    """Ngưỡng cắt đang dùng: (giá trị, nguồn) - từ `configs/models/xlm-roberta-base.yaml`."""
    return bert_like.limit(CONFIG_NAME)


def tokenizer():
    """Nạp tokenizer của XLM-R một lần duy nhất."""
    return bert_like.tokenizer(CONFIG_NAME, MODEL_NAME)


def encode(texts):
    """Chuỗi id token (CHƯA cắt) - dùng cho việc ĐO độ dài input thật."""
    return bert_like.encode(CONFIG_NAME, MODEL_NAME, texts, SEGMENTER)


def build_inputs(texts, max_length=None, segmenter=None):
    """Input cho model: dict của tokenizer (đã pad + cắt theo `max_length`).

    `segmenter` là bộ tách từ ĐANG DÙNG của lượt chạy (`preprocess.segmenter` trong cấu hình đã
    hợp nhất, xem `src/training/lora.py::_segmenter`). Để `None` nghĩa là giữ đúng bộ đã khai ở
    đầu file này - đó là hành vi của mọi lượt đã chạy.
    """
    return bert_like.build_inputs(CONFIG_NAME, MODEL_NAME, texts, SEGMENTER, max_length,
                                  segmenter)


def info():
    """Thông tin truy vết: tokenizer, từ vựng, ngưỡng cắt, `segmenter = none` (chủ ý)."""
    return bert_like.info(CONFIG_NAME, MODEL_NAME, SEGMENTER)
