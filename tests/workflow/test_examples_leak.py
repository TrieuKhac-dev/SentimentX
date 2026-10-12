# -*- coding: utf-8 -*-
"""Test cửa kiểm rò rỉ ví dụ few-shot (src/workflow/examples_leak.py, scripts/check_examples.py).

Điều quan trọng nhất được khoá ở đây:

1. Dòng chú thích (`#`) KHÔNG được tính là ví dụ - chúng là chú thích của dự án, không gửi cho model.
2. Rò rỉ phải bắt được ở CẢ `val` và `test`, và phải so sau khi CHUẨN HOÁ khoảng trắng/chữ hoa-thường
   (nếu không thì chỉ cần thêm một dấu cách là qua cửa).
3. "Không kiểm được" phải là LỖI, không phải "sạch": thiếu file ví dụ hoặc thiếu dữ liệu đã xử lý.

Chạy: python -m unittest discover -s tests
"""

import tempfile
import unittest
from pathlib import Path

from src.workflow import examples_leak


EXAMPLE_FILE = """\
# --- NGUỒN VÍ DỤ (chú thích của dự án - KHÔNG được gửi cho model) ---
# Nguồn: lấy từ split train, ghi rõ "train, dòng 12".
# --- HẾT CHÚ THÍCH ---
--- Ví dụ 1 ---
Review: "Son lên màu đẹp, giữ được lâu."
SUY LUẬN:
- colour: "lên màu đẹp" | khen màu | mã 1
KẾT QUẢ:
{"colour": 1}
"""


class ExampleReviewsTest(unittest.TestCase):

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="sentimentx-examples-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(str(self.root), ignore_errors=True))

    def write(self, text, name="examples.txt"):
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_bo_qua_dong_chu_thich_va_lay_dung_van_ban_trong_hai_dau_nhay(self):
        found = examples_leak.example_reviews(self.write(EXAMPLE_FILE))
        self.assertEqual(found, [(5, "Son lên màu đẹp, giữ được lâu.")])

    def test_nhieu_vi_du_thi_lay_het(self):
        text = EXAMPLE_FILE + '--- Ví dụ 2 ---\nReview: "Vỏ hộp chắc chắn."\n'
        found = examples_leak.example_reviews(self.write(text))
        self.assertEqual([item[1] for item in found],
                         ["Son lên màu đẹp, giữ được lâu.", "Vỏ hộp chắc chắn."])

    def test_dong_review_thieu_van_ban_trong_hai_dau_nhay_la_loi(self):
        with self.assertRaises(examples_leak.ExamplesLeakError):
            examples_leak.example_reviews(self.write("Review: không có dấu nháy\n"))

    def test_file_khong_co_vi_du_nao_la_loi(self):
        """Có file nhưng không có ví dụ: báo lỗi, vì "0 ví dụ" nghĩa là cửa không kiểm gì cả."""
        with self.assertRaises(examples_leak.ExamplesLeakError):
            examples_leak.example_reviews(self.write("# chỉ có chú thích\n"))

    def test_thieu_file_la_loi(self):
        with self.assertRaises(examples_leak.ExamplesLeakError):
            examples_leak.example_reviews(self.root / "khong-co.txt")

    def test_chuan_hoa_gop_khoang_trang_va_ha_chu_thuong(self):
        self.assertEqual(examples_leak.normalize("  Son   LÊN\nmàu  "), "son lên màu")


class CheckTest(unittest.TestCase):
    """`check()` chạy trên dữ liệu GIẢ, để không phụ thuộc dataset có trên đĩa hay không."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="sentimentx-examples-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(str(self.root), ignore_errors=True))
        self.path = self.root / "examples.txt"
        self.path.write_text(EXAMPLE_FILE, encoding="utf-8")
        self.splits = {"train": {"son lên màu đẹp, giữ được lâu."},
                       "val": {"vỏ hộp chắc chắn."},
                       "test": {"mùi thơm dễ chịu."}}

    def run_check(self, splits=None, require_train=False):
        original = examples_leak.split_texts
        table = self.splits if splits is None else splits
        # Mock phải theo ĐÚNG hợp đồng của `split_texts` thật: trả văn bản ĐÃ CHUẨN HOÁ. Nhờ vậy test
        # dưới đây kiểm được việc `check()` tự chuẩn hoá ví dụ trước khi so.
        examples_leak.split_texts = lambda split, version_id=None, dataset=None: {
            examples_leak.normalize(value) for value in table[split]}
        try:
            return examples_leak.check(self.path, require_train=require_train)
        finally:
            examples_leak.split_texts = original

    def test_vi_du_lay_tu_train_thi_sach(self):
        report = self.run_check(require_train=True)
        self.assertTrue(report["sạch"])
        self.assertEqual(report["examples"], 1)
        self.assertEqual(report["in_train"], 1)

    def test_vi_du_trung_val_bi_bat(self):
        splits = dict(self.splits, val={"son lên màu đẹp, giữ được lâu."})
        report = self.run_check(splits)
        self.assertFalse(report["sạch"])
        self.assertEqual(report["rò rỉ"], [{"dòng": 5, "split": "val"}])

    def test_vi_du_trung_test_bi_bat_du_khac_khoang_trang_va_chu_hoa(self):
        splits = dict(self.splits, test={"  Son Lên   Màu Đẹp,  Giữ Được Lâu. "})
        report = self.run_check(splits)
        self.assertFalse(report["sạch"])
        self.assertEqual(report["rò rỉ"], [{"dòng": 5, "split": "test"}])

    def test_require_train_bat_vi_du_khong_co_trong_train(self):
        splits = dict(self.splits, train={"một review khác."})
        report = self.run_check(splits, require_train=True)
        self.assertFalse(report["sạch"])
        self.assertEqual(report["thiếu trong train"], [{"dòng": 5}])
        # Không bật cờ thì ví dụ tay (không có trong dữ liệu) vẫn dùng được, miễn là không trùng val/test.
        self.assertTrue(self.run_check(splits)["sạch"])
