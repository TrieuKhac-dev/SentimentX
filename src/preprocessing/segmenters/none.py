# -*- coding: utf-8 -*-
"""Không tách từ — BASELINE để đo đúng tác động của việc tách từ.

Đây là bộ "tắt tách từ". Nó KHÔNG phải một thư viện: không cần cài gì, không lỗi,
luôn dùng được. Mục đích duy nhất là làm mốc đối chứng:

    --segmenter none  vs  --segmenter vncorenlp

Chênh lệch giữa hai lần đo chính là câu trả lời cho "tách từ có giúp không", thay
vì chỉ trích dẫn khuyến nghị của tác giả PhoBERT. Lưu ý đọc số liệu cho đúng: bỏ
tách từ thường làm SỐ TOKEN tăng lên (một từ bị chẻ thành nhiều mảnh), nên đừng
so `token/review TB` giữa hai bộ rồi kết luận bộ nào "tốt hơn" — khác biệt thật sự
chỉ hiện ra ở bước huấn luyện.
"""

NAME = "none"
OFFICIAL = False
DESCRIPTION = "Không tách từ (baseline đối chứng; luôn dùng được, không cần cài gì)"


def available():
    """Luôn dùng được — đây là lựa chọn duy nhất không phụ thuộc thư viện nào."""
    return True, ""


def info():
    """Thông tin bộ tách từ. Xem hợp đồng ở base.py."""
    return {
        "segmenter": NAME,
        "package": None,
        "version": None,
        "official": OFFICIAL,
    }


def segment(text):
    """Trả về NGUYÊN VĂN văn bản (không tách từ)."""
    return text
