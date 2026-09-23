# -*- coding: utf-8 -*-
"""Tách từ bằng underthesea — bộ của BÊN THỨ BA, không chính chủ.

Có mặt ở đây để kiến trúc "thay được bộ tách từ" được kiểm chứng thật: cùng một
pipeline, cùng một tokenizer, chỉ đổi bước tách từ rồi đo lại. Đây là lựa chọn dùng
khi muốn so thêm một công cụ phổ biến khác, KHÔNG phải mặc định.

Vì sao không mặc định: PhoBERT được tiền huấn luyện bằng RDRSegmenter (VnCoreNLP), và
VinAI khuyến nghị dùng đúng bộ đó cho mọi ứng dụng dùng PhoBERT. Một bộ tách từ khác
nghĩa là có thêm một khác biệt so với thiết kế gốc, nên khi dùng phải GHI RÕ tên bộ
trong báo cáo (`--segmenter underthesea`); số liệu của nó không so sánh ngang hàng
với số liệu của bộ chính chủ.
"""

NAME = "underthesea"
OFFICIAL = False
DESCRIPTION = (
    "underthesea.word_tokenize — bộ tách từ bên thứ ba, dùng để đối chứng "
    "(KHÔNG phải bộ VinAI khuyến nghị cho PhoBERT)"
)
INSTALL_HINT = (
    "Thiếu thư viện tách từ 'underthesea'. Cài bằng:\n"
    "    pip install underthesea\n"
    "Bộ tách từ CHÍNH CHỦ của PhoBERT là RDRSegmenter (VnCoreNLP) và cần Java:\n"
    "    powershell -ExecutionPolicy Bypass -File scripts\\setup_vncorenlp.ps1"
)

_MODEL = None


def _tokenizer():
    """Nạp underthesea một lần duy nhất."""
    global _MODEL
    if _MODEL is None:
        try:
            from underthesea import word_tokenize
        except ImportError as exc:  # pragma: no cover - phụ thuộc môi trường
            raise ImportError(INSTALL_HINT) from exc
        _MODEL = word_tokenize
    return _MODEL


def available():
    """underthesea có cài trên máy này không (chỉ thử import)."""
    try:
        _tokenizer()
    except ImportError:
        return False, "thiếu thư viện underthesea; cài bằng 'pip install underthesea'"
    return True, ""


def info():
    """Thông tin bộ tách từ. Xem hợp đồng ở base.py."""
    return {
        "segmenter": NAME,
        "package": "underthesea",
        "version": _version(),
        "official": OFFICIAL,
    }


def segment(text):
    """Tách từ; underthesea trả về danh sách token nên nối lại thành chuỗi."""
    return " ".join(_tokenizer()(text))


def _version():
    """Phiên bản gói đang cài, để ghi vào số liệu truy vết."""
    try:
        from importlib.metadata import PackageNotFoundError, version
    except ImportError:  # pragma: no cover - Python cũ
        return None
    try:
        return version("underthesea")
    except PackageNotFoundError:
        return None
