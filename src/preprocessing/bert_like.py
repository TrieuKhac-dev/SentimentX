# -*- coding: utf-8 -*-
"""Phần DÙNG CHUNG của các encoder kiểu BERT (PhoBERT, ViBERT, CafeBERT, XLM-R).

VÌ SAO CÓ FILE NÀY
`phobert.py` và `visobert.py` mỗi file gần 150 dòng, mà phần lớn là cùng một việc: nạp tokenizer, mã
hoá văn bản (có/không tách từ), cắt theo `max_length`, và ghi thông tin truy vết. Bốn encoder thêm ở
đợt 7 chỉ khác nhau ở BA thứ: `checkpoint`, tên file cấu hình, và **có hay không tách từ tiếng Việt**.
Ba thứ đó là THAM SỐ, không phải mã - nên chúng nằm ở tham số, còn mã nằm ở đây.

Hợp đồng của một encoder (xem `src/training/encoders.py` và `src/preprocessing/token_stats.py`):
    MODEL_NAME, CONFIG_NAME, limit(), tokenizer(), encode(), build_inputs(), info()
    (+ `words()` khi model dùng tách từ - mẫu số của chỉ số "subword / từ")

Mỗi module encoder vì thế chỉ còn khai ba hằng số và gọi sang đây. Kiểm bằng test: mọi module trong
`src/training/encoders.py` phải có đủ các hàm này.
"""

from functools import lru_cache

from src.experiments import model_config
from src.preprocessing import segmenters

# Tokenizer nhớ theo TÊN FILE CẤU HÌNH (không theo checkpoint): `phobert-base-v2` và `phobert-large`
# dùng cùng họ tokenizer nhưng là HAI model, nên nhớ chung một chỗ thì lần đo thứ hai nhận nhầm
# tokenizer của model kia mà không có gì báo lỗi.
_TOKENIZERS = {}


def limit(config_name):
    """Ngưỡng cắt đang dùng: (giá trị, nguồn) - đọc từ `configs/models/<config_name>.yaml`."""
    return model_config.max_length(config_name)


def tokenizer(config_name, model_name):
    """Nạp tokenizer của model một lần duy nhất (nhớ theo tên cấu hình)."""
    found = _TOKENIZERS.get(config_name)
    if found is None:
        try:
            from transformers import AutoTokenizer
        except ImportError as exc:  # pragma: no cover - phụ thuộc môi trường
            raise ImportError(
                "Thiếu thư viện transformers. Cài bằng:\n"
                "    pip install transformers torch"
            ) from exc
        found = AutoTokenizer.from_pretrained(model_name)
        _TOKENIZERS[config_name] = found
    return found


def segmenter_name(segmenter):
    """Tên bộ tách từ thật sự dùng (đã giải `auto` -> `vncorenlp`/`pyvi`)."""
    return segmenters.resolve(segmenter)[0]


@lru_cache(maxsize=100000)
def _segment_cached(name, text):
    """Tách từ có nhớ kết quả (bộ chính chủ gọi qua JNI nên không rẻ, mỗi review bị tách hai lần)."""
    return segmenters.get(name).segment(text)


def segment_all(texts, segmenter):
    """Tách từ cho cả dãy văn bản (chỉ dò bộ tách từ MỘT lần)."""
    name = segmenter_name(segmenter)
    return [_segment_cached(name, text) for text in texts]


def prepared(texts, segmenter):
    """Văn bản đưa vào tokenizer: đã tách từ nếu model cần, NGUYÊN BẢN nếu `segmenter` là `none`.

    Đây là chỗ duy nhất phân biệt hai họ encoder: PhoBERT/ViBERT được tiền huấn luyện trên văn bản đã
    tách từ, còn XLM-R/CafeBERT dùng SentencePiece trên văn bản nguyên bản.
    """
    if segmenter_name(segmenter) == "none":
        return list(texts)
    return segment_all(texts, segmenter)


def words(texts, segmenter):
    """Tổng số ĐƠN VỊ sau tách từ - mẫu số của chỉ số "subword / từ".

    Đếm trên văn bản ĐÃ tách từ, vì mục đích của chỉ số là "tokenizer chẻ mỗi từ thành bao nhiêu mảnh".
    """
    return sum(len(item.split()) for item in segment_all(texts, segmenter))


def encode(config_name, model_name, texts, default_segmenter, segmenter=None):
    """Chuỗi id token của từng văn bản (ĐÃ tách từ nếu cần, CHƯA cắt theo `max_length`).

    Không cần torch, nên dùng được cho việc ĐO độ dài input thật trước khi huấn luyện.
    """
    return tokenizer(config_name, model_name)(
        prepared(texts, default_segmenter if segmenter is None else segmenter),
        add_special_tokens=True)["input_ids"]


def build_inputs(config_name, model_name, texts, default_segmenter, max_length=None, segmenter=None):
    """Input cho model: dict của tokenizer (đã pad, đã cắt theo `max_length`).

    `max_length` để None nghĩa là dùng ngưỡng ĐANG CÓ HIỆU LỰC (`limit()`), đúng giá trị mà nơi ĐO
    dùng - nên hai bước không thể lệch nhau.
    """
    if max_length is None:
        max_length = limit(config_name)[0]
    return tokenizer(config_name, model_name)(
        prepared(texts, default_segmenter if segmenter is None else segmenter),
        padding=True,
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )


def info(config_name, model_name, default_segmenter, segmenter=None):
    """Thông tin để TRUY VẾT số liệu đo được: tokenizer, từ vựng, ngưỡng cắt, bộ tách từ."""
    name = segmenter_name(default_segmenter if segmenter is None else segmenter)
    found = tokenizer(config_name, model_name)
    value, source = limit(config_name)
    result = {
        "tokenizer": type(found).__name__,
        "unk_id": found.unk_token_id,
        "vocab": found.vocab_size,
        "max_length": value,
        "max_length_source": source,
    }
    if name == "none":
        # Ghi rõ "không tách từ" là CHỦ Ý, không phải thiếu cấu hình - cùng lối với ViSoBERT.
        result["segmenter"] = "none"
    else:
        result.update(segmenters.get(name).info())
    return result

