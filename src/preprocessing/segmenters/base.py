# -*- coding: utf-8 -*-
"""Hợp đồng chung của mọi BỘ TÁCH TỪ tiếng Việt (word segmenter).

PHÂN BIỆT RÕ: TÁCH TỪ KHÁC TOKENIZER
---
    - Bộ tách từ (thư mục này): gộp các âm tiết của một TỪ tiếng Việt lại bằng
      dấu gạch dưới: "Đại học Quốc gia" -> "Đại_học Quốc_gia". Chạy TRƯỚC.
    - Tokenizer (PhobertTokenizer, XLMRobertaTokenizer...): chẻ văn bản thành
      SUBWORD. Chạy SAU, và KHÔNG đổi dù chọn bộ tách từ nào.

Vì sao phải tách riêng hai việc: PhoBERT được huấn luyện trên văn bản ĐÃ tách từ,
nên tách từ là bước bắt buộc; nhưng tokenizer của nó vẫn là tokenizer của nó. Đổi
bộ tách từ không được kéo theo việc đổi tokenizer.

MỘT BỘ TÁCH TỪ CHUẨN GỒM
---
    NAME        tên ngắn, dùng ở dòng lệnh: `--segmenter <tên>`
    OFFICIAL    True nếu là bộ CHÍNH CHỦ của model (VinAI khuyến nghị cho PhoBERT)
    DESCRIPTION một dòng giải thích, in ra ở `--list-segmenters`
    available() -> (bool, lí do)   máy này chạy được không, chưa cần nạp model
    info()      -> dict            tên, gói, phiên bản, official
    segment(text) -> str           văn bản ĐÃ tách từ

BỐN QUY ƯỚC BẮT BUỘC
---
1. `segment()` trả về CHUỖI, không phải list. Các thư viện không thống nhất chuyện
   này (VnCoreNLP trả về list câu, pyvi trả về chuỗi), nên việc quy về chuỗi làm ở
   đây để phobert.py không phải biết đang dùng bộ nào.
2. Không sửa gì ngoài việc nối từ: không bỏ dấu, không thêm/xoá ký tự. Nhờ vậy bật
   tắt tách từ không làm sai lệch phép đo "văn bản không mất dấu" của pipeline.
3. Thiếu thư viện / thiếu Java / thiếu model => LỖI rõ ràng kèm cách cài
   (ImportError hoặc OSError). TUYỆT ĐỐI không lặng lẽ trả về văn bản nguyên bản:
   như vậy kết quả đo sẽ đúng nhưng lại là của bộ "none" mà không ai biết.
4. `available()` chỉ KIỂM TRA (thư viện, Java, file model có mặt), KHÔNG nạp model -
   để `--list-segmenters` chạy nhanh.

Thêm bộ tách từ mới: tạo file trong thư mục này theo hợp đồng trên, rồi thêm vào
SEGMENTERS ở __init__.py. Không phải sửa phobert.py, token_stats.py hay dòng lệnh.
"""


def check(module, name=""):
    """Kiểm tra một module có đúng hợp đồng bộ tách từ. Báo lỗi rõ nếu sai."""
    label = name or getattr(module, "__name__", "?")
    for attr in ("NAME", "DESCRIPTION"):
        if not str(getattr(module, attr, "") or "").strip():
            raise TypeError(
                "Bộ tách từ '{}' thiếu hằng số {}. Xem hợp đồng trong "
                "src/preprocessing/segmenters/base.py.".format(label, attr)
            )
    if not isinstance(getattr(module, "OFFICIAL", None), bool):
        raise TypeError(
            "Bộ tách từ '{}' thiếu hằng số OFFICIAL (True/False). Xem hợp đồng "
            "trong src/preprocessing/segmenters/base.py.".format(label)
        )
    for func in ("available", "info", "segment"):
        if not callable(getattr(module, func, None)):
            raise TypeError(
                "Bộ tách từ '{}' thiếu hàm {}(). Xem hợp đồng trong "
                "src/preprocessing/segmenters/base.py.".format(label, func)
            )
    return module
