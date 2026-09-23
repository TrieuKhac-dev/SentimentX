# -*- coding: utf-8 -*-
"""Model preprocessing cho PhoBERT (vinai/phobert-base-v2).

Chuỗi bước:

    văn bản đã làm sạch
        -> TÁCH TỪ tiếng Việt   (bước riêng của PhoBERT, KHÔNG thuộc pipeline)
        -> tokenizer của PhoBERT
        -> input_ids / attention_mask

Lưu ý quan trọng: PhoBERT được huấn luyện trên văn bản đã tách từ, nên nếu bỏ bước
tách từ thì chất lượng sẽ giảm rõ rệt. Vì vậy bước này nằm ở ĐÂY, không nằm trong
Data Pipeline chung.

HAI VIỆC KHÁC NHAU, ĐỪNG LẪN
----------------------------
    TÁCH TỪ  (word segmentation): "Đại học Quốc gia" -> "Đại_học Quốc_gia"
    TOKENIZER (subword)         : cắt chuỗi đã tách từ thành các mảnh nhỏ

Tokenizer của PhoBERT KHÔNG đổi trong mọi thí nghiệm; chỉ bộ tách từ là thay được
(xem src/preprocessing/segmenters/). Bộ tách từ CHÍNH CHỦ là RDRSegmenter/VnCoreNLP
— đúng bộ VinAI đã dùng để tiền huấn luyện PhoBERT — nên đó là mặc định ("auto").
"""

from functools import lru_cache

from src import model_config
from src.preprocessing import segmenters

MODEL_NAME = "vinai/phobert-base-v2"

# Tên file cấu hình trong configs/models/ (không cần đuôi .yaml)
CONFIG_NAME = "phobert"

# Ngưỡng cắt input, tính bằng TOKEN (kể cả 2 token đặc biệt). ĐÂY LÀ GIÁ TRỊ MẶC ĐỊNH —
# có thể ghi đè bằng `max_length` trong configs/models/phobert.yaml (để thử nghiệm) hoặc
# bằng `--max-length` khi chạy; nơi đo (token_stats) và nơi dùng (build_inputs) đều đọc
# qua `limit()` nên hai chỗ không thể lệch nhau.
# 256 là "Max length" trong bảng chính chủ của PhoBERT (README của VinAI); trần kiến trúc
# là `max_position_embeddings: 258` trong config.json (258 = 256 + 2 token đặc biệt).
MAX_LENGTH = 256

# Bộ tách từ dùng cho model này:
#     "auto"        -> vncorenlp (chính chủ), nếu chưa cài được Java thì pyvi
#     "vncorenlp"   -> bắt buộc dùng bộ chính chủ (báo lỗi nếu thiếu)
#     "pyvi" / "underthesea" / "none" -> chỉ định đích danh (dùng cho đối chứng)
# Đổi giá trị này KHÔNG làm đổi dữ liệu hay tokenizer — chỉ đổi bước tách từ, nên số
# liệu đo được phải ghi rõ đã dùng bộ nào (cột `segmenter` trong token_stats.csv).
SEGMENTER = "auto"

_TOKENIZER = None


def limit():
    """Ngưỡng cắt đang dùng: (giá trị, nguồn) — YAML của model > hằng số MAX_LENGTH."""
    return model_config.max_length(CONFIG_NAME, MAX_LENGTH)


def segmenter(segmenter=None):
    """Bộ tách từ thật sự đang dùng: trả về (tên, module)."""
    return segmenters.resolve(SEGMENTER if segmenter is None else segmenter)


def segmenter_name(segmenter=None):
    """Tên bộ tách từ đang dùng, ví dụ "vncorenlp"."""
    return segmenters.resolve(SEGMENTER if segmenter is None else segmenter)[0]



def tokenizer():
    """Nạp tokenizer của PhoBERT một lần duy nhất."""
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


@lru_cache(maxsize=100000)
def _segment_cached(name, text):
    """Tách từ có nhớ kết quả.

    Cùng một review thường bị tách hai lần (một lần để đo token, một lần để đếm từ),
    mà mỗi lần gọi bộ chính chủ là một lời gọi qua JNI nên không rẻ. Nhớ kết quả giúp
    phép đo chạy nhanh gần gấp đôi mà không đổi một con số nào.
    """
    return segmenters.get(name).segment(text)


def segment(text, segmenter=None):
    """Tách từ tiếng Việt cho MỘT văn bản.

    Ví dụ với bộ chính chủ: "Đại học Quốc gia" -> "Đại_học Quốc_gia". Quy ước nối từ
    bằng dấu _ là của RDRSegmenter; bộ tách từ nào cũng phải trả về MỘT CHUỖI như vậy
    (xem hợp đồng ở src/preprocessing/segmenters/base.py).
    """
    name = segmenters.resolve(SEGMENTER if segmenter is None else segmenter)[0]
    return _segment_cached(name, text)


def segment_all(texts, segmenter=None):
    """Tách từ cho cả một dãy văn bản (chỉ dò bộ tách từ MỘT lần)."""
    name = segmenters.resolve(SEGMENTER if segmenter is None else segmenter)[0]
    return [_segment_cached(name, text) for text in texts]


def words(texts, segmenter=None):
    """Tổng số ĐƠN VỊ sau khi tách từ — mẫu số của chỉ số "subword / từ".

    Đếm trên văn bản ĐÃ tách từ (không dùng utils.tokenize), vì mục đích của chỉ số
    này là "tokenizer chẻ mỗi từ thành bao nhiêu mảnh": mẫu số phải là đúng chuỗi đưa
    vào tokenizer. Với bộ "vncorenlp", một từ ghép như "Đại_học" được tính là 1.
    """
    return sum(len(item.split()) for item in segment_all(texts, segmenter))



def encode(texts, segmenter=None):
    """Chuỗi id token của từng văn bản (ĐÃ tách từ, CHƯA cắt theo max_length).

    Không cần torch, nên dùng được cho việc ĐO độ dài input thật trước khi huấn
    luyện (xem src/preprocessing/token_stats.py).
    """
    return tokenizer()(segment_all(texts, segmenter),
                       add_special_tokens=True)["input_ids"]


def build_inputs(texts, max_length=None, segmenter=None):
    """Chuyển danh sách văn bản thành input cho PhoBERT.

    Trả về dict của tokenizer: {"input_ids": ..., "attention_mask": ...}
    (dạng tensor của PyTorch).

    `max_length` để None nghĩa là dùng ngưỡng ĐANG CÓ HIỆU LỰC (`limit()`: YAML của model
    > hằng số MAX_LENGTH) — cũng đúng giá trị mà token_stats dùng để đo, nên hai bước
    không thể lệch nhau. Truyền số cụ thể khi muốn ép cho một lần gọi.
    """
    if max_length is None:
        max_length = limit()[0]
    return tokenizer()(
        segment_all(texts, segmenter),
        padding=True,
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )


def info(segmenter=None):
    """Thông tin để TRUY VẾT số liệu đo được: tokenizer, từ vựng, ngưỡng cắt, bộ tách từ.

    Bộ tách từ trả về tên + gói + phiên bản, vì cùng một review tách bằng VnCoreNLP và
    bằng pyvi cho ra số token khác nhau — không ghi lại thì sau này không biết dòng số
    liệu nào thuộc thí nghiệm nào.
    """
    name = segmenters.resolve(SEGMENTER if segmenter is None else segmenter)[0]
    found = tokenizer()
    value, source = limit()
    result = {
        "tokenizer": type(found).__name__,
        "unk_id": found.unk_token_id,
        "vocab": found.vocab_size,
        "max_length": value,
        "max_length_source": source,
    }
    result.update(segmenters.get(name).info())
    return result

