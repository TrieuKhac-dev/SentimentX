# -*- coding: utf-8 -*-
"""Test bước Normalize của pipeline (`src/pipeline/normalize.py`).

VÌ SAO CẦN FILE NÀY
`normalize_steps()` là NGUỒN DUY NHẤT định nghĩa "chuẩn hoá là gì": bước Normalize dùng nó để sửa dữ
liệu, và bước Final Validate dùng LẠI chính nó để chứng minh văn bản đầu ra đúng bằng văn bản gốc
sau chuẩn hoá. Vì vậy phép chuẩn hoá mới phải được khoá ở mức HÀM này, không phải ở mức một lần chạy.

ĐIỀU ĐƯỢC KHOÁ
    1. `remove_emoji` (pipeline v0.3.0) bỏ emoji, và GỘP khoảng trắng dư do việc bỏ để lại;
    2. review CHỈ có emoji thì GIỮ NGUYÊN - bỏ hết sẽ tạo dòng rỗng mà không bước nào loại nữa;
    3. cấu hình CŨ (không khai `remove_emoji`) chạy y như trước: thiếu khoá KHÔNG phải lỗi;
    4. định nghĩa emoji dùng chung với EDA (`utils.EMOJI_PATTERN`), kể cả chuỗi ZWJ và tông màu da.

Chạy: python -m unittest discover -s tests
"""

import unittest

from src.pipeline import normalize

# Cấu hình Normalize của v0.2.0: CHƯA có khoá `remove_emoji`.
BASE = {"lowercase": False, "unicode": True, "whitespace": True, "repeated_chars": False}


def steps(text, **extra):
    """Áp `normalize_steps` với cấu hình v0.2.0, thêm khoá tuỳ ý của lượt đang kiểm."""
    return normalize.normalize_steps(text, dict(BASE, **extra), 2)


class RemoveEmojiTest(unittest.TestCase):
    """Khoá `steps.normalize.remove_emoji` - chỉ có từ phiên bản pipeline v0.3.0."""

    def test_bo_emoji_va_gop_khoang_trang(self):
        got, changed = steps("đẹp ❤️ quá", remove_emoji=True)
        self.assertEqual(got, "đẹp quá")
        self.assertEqual(changed, ["emoji"])

    def test_khong_co_emoji_thi_khong_doi_gi(self):
        got, changed = steps("son đẹp thật", remove_emoji=True)
        self.assertEqual(got, "son đẹp thật")
        self.assertEqual(changed, [])

    def test_review_chi_co_emoji_thi_giu_nguyen(self):
        # Bỏ hết sẽ ra chuỗi RỖNG, mà bước Clean (bước duy nhất loại review rỗng) đã chạy TRƯỚC
        # bước này - nên giữ nguyên là lựa chọn có chủ ý, không phải bỏ sót.
        got, changed = steps("🥰🥰", remove_emoji=True)
        self.assertEqual(got, "🥰🥰")
        self.assertEqual(changed, [])

    def test_khong_khai_thi_khong_dung_toi_emoji(self):
        # Bản v0.1.0/v0.2.0 không có khoá này; thiếu khoá phải là "tắt", KHÔNG được là KeyError.
        got, changed = steps("đẹp ❤️ quá")
        self.assertEqual(got, "đẹp ❤️ quá")
        self.assertEqual(changed, [])

    def test_khai_tat_thi_cung_khong_dung_toi_emoji(self):
        got, changed = steps("đẹp ❤️ quá", remove_emoji=False)
        self.assertEqual(got, "đẹp ❤️ quá")
        self.assertEqual(changed, [])

    def test_giu_dau_cau_dung_canh_emoji(self):
        self.assertEqual(steps("ok 😊!!", remove_emoji=True)[0], "ok !!")

    def test_emoji_gia_dinh_va_tong_mau_da(self):
        self.assertEqual(steps("nhà 👨‍👩‍👧 vui 👍🏻", remove_emoji=True)[0], "nhà vui")

    def test_chay_cung_cac_phep_khac(self):
        # Emoji bỏ SAU khi gộp khoảng trắng, nên phép này phải tự gộp lại phần nó để lại.
        got, changed = steps("Son   đẹp   ❤️   lắm", remove_emoji=True)
        self.assertEqual(got, "Son đẹp lắm")
        self.assertEqual(changed, ["khoảng trắng", "emoji"])

    def test_giu_ky_tu_xuong_dong(self):
        """Review nhiều dòng phải GIỮ xuống dòng: 4.158 dòng `train` có xuống dòng mà chỉ 1.877 dòng
        có emoji, nên một phép `\\s+ -> " "` sẽ sửa cả những review KHÔNG hề có emoji."""
        got, changed = steps("Công dụng: tốt\nKết cấu: mịn ❤️", remove_emoji=True)
        self.assertEqual(got, "Công dụng: tốt\nKết cấu: mịn")
        self.assertEqual(changed, ["emoji"])

    def test_review_khong_co_emoji_di_qua_khong_doi(self):
        """Bất biến quan trọng nhất: văn bản KHÔNG có emoji phải đi qua y nguyên từng ký tự."""
        for text in ("Công dụng: tốt\nKết cấu: mịn", "son đẹp thật", "ok!!", "1 2 3"):
            with self.subTest(text=text):
                self.assertEqual(steps(text, remove_emoji=True), (text, []))


if __name__ == "__main__":
    unittest.main()
