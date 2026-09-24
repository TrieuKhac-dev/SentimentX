# -*- coding: utf-8 -*-
"""Tách từ bằng pyvi (ViTokenizer) - bộ tách từ LEGACY, KHÔNG chính chủ.

Vị trí của bộ này trong kiến trúc: đây là lựa chọn THAY THẾ được (kiến trúc cho
phép thay bộ tách từ mà không sửa pipeline hay tokenizer), dùng khi máy chưa cài
được Java - bộ chính chủ của PhoBERT là VnCoreNLP/RDRSegmenter (cần Java).

Vì sao KHÔNG dùng pyvi làm mặc định:
    - VinAI (tác giả PhoBERT) khuyến nghị đúng RDRSegmenter của VnCoreNLP, vì
      chính nó đã tách từ cho dữ liệu tiền huấn luyện. Dùng một công cụ khác nghĩa
      là có thêm một khác biệt so với thiết kế gốc của model.
    - pyvi (2018) không còn được bảo trì.
Nên pyvi chỉ là phương án dự phòng: kết quả đo vẫn đúng nhưng phải GHI RÕ đã dùng
`--segmenter pyvi`, vì số liệu của hai bộ không so sánh ngang nhau được.
"""

NAME = "pyvi"
OFFICIAL = False
DESCRIPTION = (
    "ViTokenizer của pyvi - bộ tách từ legacy, dùng khi chưa cài được Java "
    "(KHÔNG phải bộ VinAI khuyến nghị cho PhoBERT)"
)
INSTALL_HINT = (
    "Thiếu thư viện tách từ 'pyvi'. Cài bằng:\n"
    "    pip install pyvi\n"
    "Bộ tách từ CHÍNH CHỦ của PhoBERT là RDRSegmenter (VnCoreNLP) và cần Java:\n"
    "    powershell -ExecutionPolicy Bypass -File scripts\\setup_vncorenlp.ps1"
)

_MODEL = None


def _tokenizer():
    """Nạp ViTokenizer một lần duy nhất."""
    global _MODEL
    if _MODEL is None:
        try:
            from pyvi import ViTokenizer
        except ImportError as exc:  # pragma: no cover - phụ thuộc môi trường
            raise ImportError(INSTALL_HINT) from exc
        _MODEL = ViTokenizer
    return _MODEL


def available():
    """pyvi có cài trên máy này không (KHÔNG nạp model, chỉ thử import)."""
    try:
        _tokenizer()
    except ImportError:
        return False, "thiếu thư viện pyvi; cài bằng 'pip install pyvi'"
    return True, ""


def info():
    """Thông tin bộ tách từ. Xem hợp đồng ở base.py."""
    return {
        "segmenter": NAME,
        "package": "pyvi",
        "version": _version("pyvi"),
        "official": OFFICIAL,
    }


def segment(text):
    """Tách từ; pyvi đã trả về chuỗi (nối từ bằng dấu _)."""
    return _tokenizer().tokenize(text)


def _version(package):
    """Phiên bản gói đang cài, để ghi vào số liệu truy vết."""
    try:
        from importlib.metadata import PackageNotFoundError, version
    except ImportError:  # pragma: no cover - Python cũ
        return None
    try:
        return version(package)
    except PackageNotFoundError:
        return None
