# -*- coding: utf-8 -*-
"""Đăng ký các BỘ TÁCH TỪ tiếng Việt thay thế được cho nhau.

Đây là NƠI DUY NHẤT quyết định "dự án có những bộ tách từ nào". Kiến trúc cố ý để bộ
tách từ THAY ĐƯỢC: cùng pipeline, cùng tokenizer, chỉ đổi bước tách từ rồi đo lại.
Nhờ vậy câu hỏi "tách từ có giúp không, giúp bao nhiêu" trả lời được bằng số đo thay
vì bằng niềm tin — và cũng không phải viết lại code khi một bộ mới xuất hiện.

THỨ TỰ MẶC ĐỊNH (khi chọn "auto")
--------------------------------
    1. vncorenlp   CHÍNH CHỦ — RDRSegmenter, đúng bộ VinAI dùng tiền huấn luyện PhoBERT
    2. pyvi        dự phòng khi chưa cài được Java, KHÔNG chính chủ

`underthesea` và `none` chỉ chạy khi chỉ định rõ `--segmenter <tên>`.

Nguyên tắc quan trọng: "auto" KHÔNG bao giờ tự chọn một bộ không chính chủ. Máy chưa
cài được bộ chính chủ thì báo lỗi kèm cách cài, chứ không lặng lẽ dùng bộ khác — số
liệu đo bằng bộ khác là số liệu của một thí nghiệm khác, trộn vào là sai.

THÊM MỘT BỘ MỚI
---------------
1. Tạo file trong thư mục này, ví dụ `bami.py`, theo HỢP ĐỒNG ghi ở base.py
   (NAME, OFFICIAL, DESCRIPTION, available(), info(), segment()).
2. Import ở đây và thêm vào dict `SEGMENTERS`.
3. Muốn nó được "auto" chọn thì thêm vào AUTO_ORDER — chỉ làm điều này khi bộ đó thật
   sự là bộ chính chủ mà model mong đợi.
"""

import difflib

from src.preprocessing.segmenters import base, none, pyvi, underthesea, vncorenlp

# Thứ tự thử khi chọn "auto" (chỉ các bộ dùng được làm MẶC ĐỊNH của dự án)
AUTO_ORDER = ("vncorenlp", "pyvi")

SEGMENTERS = {
    vncorenlp.NAME: vncorenlp,
    pyvi.NAME: pyvi,
    underthesea.NAME: underthesea,
    none.NAME: none,
}

INSTALL_HINT = (
    "Cách cài bộ chính chủ (Windows, không cần quyền admin):\n"
    "    powershell -ExecutionPolicy Bypass -File scripts\\setup_java.ps1\n"
    "    powershell -ExecutionPolicy Bypass -File scripts\\setup_vncorenlp.ps1"
)


class SegmenterError(Exception):
    """Không có bộ tách từ nào dùng được, hoặc tên bộ tách từ không hợp lệ.

    Cố ý là lớp riêng để nơi gọi phân biệt được "môi trường chưa sẵn sàng" (bỏ qua
    model kèm lí do) với "lỗi lập trình" (phải sửa ngay).
    """


def names():
    """Tên mọi bộ tách từ đã đăng ký."""
    return sorted(SEGMENTERS)


def official_names():
    """Tên các bộ CHÍNH CHỦ của model (chỉ những bộ này mới đáng làm mặc định)."""
    return [name for name in names() if SEGMENTERS[name].OFFICIAL]


def get(name):
    """Module của một bộ tách từ. Báo lỗi kèm gợi ý nếu tên sai."""
    key = str(name or "").strip().lower()
    if key not in SEGMENTERS:
        hint = difflib.get_close_matches(key, names(), n=3, cutoff=0.6)
        raise SegmenterError(
            "Chưa có bộ tách từ '{}'. Đang có: {}.{}{}".format(
                name, ", ".join(names()),
                " Có phải bạn muốn: {}?".format(" hoặc ".join(hint)) if hint else "",
                " Thêm bộ mới: xem hướng dẫn ở đầu src/preprocessing/segmenters/"
                "__init__.py.")
        )
    return base.check(SEGMENTERS[key], key)


def resolve(spec="auto"):
    """Chọn bộ tách từ thật sự sẽ dùng. Trả về (tên, module).

    `spec="auto"` (mặc định) thử theo AUTO_ORDER và KHÔNG tự chọn bộ không chính chủ.
    Chỉ định đích danh thì bộ đó phải dùng được — nếu không, báo lỗi ngay thay vì
    lặng lẽ quay về mặc định, vì như vậy số liệu sẽ thuộc về một thí nghiệm khác với
    điều người dùng yêu cầu.
    """
    key = str(spec or "auto").strip().lower()
    if key in ("auto", ""):
        reasons = []
        for name in AUTO_ORDER:
            ok, reason = SEGMENTERS[name].available()
            if ok:
                return name, SEGMENTERS[name]
            reasons.append("{}: {}".format(name, reason))
        raise SegmenterError(
            "Không có bộ tách từ nào dùng được ở chế độ 'auto':\n  - {}\n{}".format(
                "\n  - ".join(reasons), INSTALL_HINT)
        )

    module = get(key)
    ok, reason = module.available()
    if not ok:
        raise SegmenterError(
            "Bộ tách từ '{}' chưa dùng được: {}. Xem `python run_token_stats.py "
            "--list-segmenters`.".format(key, reason)
        )
    return key, module


def status():
    """Tình trạng mọi bộ tách từ, để in ra ở --list-segmenters."""
    rows = []
    for name in names():
        module = SEGMENTERS[name]
        ok, reason = module.available()
        meta = module.info() if ok else {}
        rows.append({
            "tên": name,
            "chính chủ": "có" if module.OFFICIAL else "không",
            "dùng được": "có" if ok else "không",
            "gói": meta.get("package") or "—",
            "phiên bản": meta.get("version") or "—",
            "ghi chú": module.DESCRIPTION if ok else reason,
        })
    return rows
