# -*- coding: utf-8 -*-
"""Test hai hàm nhãn dùng cho biến thể đo theo công bố (`src/labels/base.py`).

VÌ SAO CÓ FILE NÀY
`named_codes` và `keep_two_sided` là phần DUY NHẤT của dự án lọc ô theo cả nhãn ĐOÁN, và chúng mới chỉ
được kiểm GIÁN TIẾP qua bộ chấm (`tests/evaluation/test_scorers.py`). Hai lỗi ở đây sẽ im lặng: lọc
nhầm mã nhãn (viết theo mã số thay vì theo tên, nên đổi cách đánh số là lọc sai) và không đếm ô bị
loại (mẫu số nhỏ đi mà không ai biết). Khoá trực tiếp thì lỗi hiện ra ngay tại hàm.

ĐIỀU ĐƯỢC KHOÁ
    1. `named_codes` tra mã theo TÊN nhãn, chịu được bảng tên có khoá là chuỗi hoặc số, và BÁO LỖI
       khi thiếu tên;
    2. `keep_two_sided` giữ ô chỉ khi CẢ hai nhãn thuộc tập mã, và đếm RIÊNG ô bị loại với ô không
       đọc được.

Chạy: python -m unittest discover -s tests
"""

import unittest

from src.labels import base

# Bảng tên đúng dạng `id_to_label` của `label_map.json`: khoá là CHUỖI, mã 0 có tên rỗng.
LABELS = {"0": "", "1": "positive", "2": "negative", "3": "neutral"}


class NamedCodesTest(unittest.TestCase):
    def test_tra_ma_theo_ten_nhan(self):
        self.assertEqual(base.named_codes(LABELS, ("positive", "negative")), {1, 2})

    def test_bo_qua_khoang_trang_va_chu_hoa(self):
        self.assertEqual(base.named_codes({"1": " Positive "}, ["POSITIVE"]), {1})

    def test_bang_ten_dung_khoa_so_nguyen_van_dung(self):
        self.assertEqual(base.named_codes({1: "positive", 2: "negative"}, ["negative"]), {2})

    def test_thieu_ten_thi_bao_loi(self):
        with self.assertRaises(base.LabelError):
            base.named_codes(LABELS, ("positive", "tích cực"))

    def test_bang_ten_rong_thi_bao_loi(self):
        with self.assertRaises(base.LabelError):
            base.named_codes({}, ["positive"])


class KeepTwoSidedTest(unittest.TestCase):
    def test_giu_o_hai_cuc_va_dem_o_bi_loai(self):
        gold, pred, dropped, unreadable = base.keep_two_sided([1, 2, 0, 3], [1, 1, 1, 2], {1, 2})
        self.assertEqual(gold, [1, 2])
        self.assertEqual(pred, [1, 1])
        self.assertEqual((dropped, unreadable), (2, 0))

    def test_o_khong_doc_duoc_dem_rieng(self):
        gold, pred, dropped, unreadable = base.keep_two_sided([1, 1, 0], [1, None, None], {1, 2})
        self.assertEqual((gold, pred), ([1], [1]))
        self.assertEqual((dropped, unreadable), (0, 2))

    def test_o_doan_neutral_bi_loai(self):
        _gold, _pred, dropped, unreadable = base.keep_two_sided([1, 1], [1, 3], {1, 2})
        self.assertEqual((dropped, unreadable), (1, 0))


if __name__ == "__main__":
    unittest.main()
