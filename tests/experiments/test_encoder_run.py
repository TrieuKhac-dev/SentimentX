# -*- coding: utf-8 -*-
"""Test phần TÍNH của đường encoder: bảng xác suất từng ô (`probabilities.csv`).

Vì sao khoá ở đây: bước kết hợp (dò ngưỡng theo khía cạnh, ensemble nhiều encoder, luật lai encoder +
LLM) đọc tệp xác suất rồi ghép với `predictions.csv` theo (chỉ số, khía cạnh). Sai một trong ba thứ -
tên cột mang mã nhãn, số dòng, hay thứ tự khía cạnh - thì bước kết hợp ghép nhầm ô mà KHÔNG báo lỗi.

Chạy: python -m unittest discover -s tests
"""

import unittest

from src.core import paths
from src.experiments import encoder_run


class ProbabilityTableTest(unittest.TestCase):
    def test_ten_cot_mang_ma_nhan_chu_khong_phai_so_thu_tu(self):
        columns = encoder_run.probability_columns([1, 2])
        self.assertEqual(columns, ["chỉ số", "split", "khía cạnh", "p(mã 1)", "p(mã 2)"])

    def test_ten_cot_theo_dung_bo_ma_bon_trang_thai(self):
        self.assertEqual(encoder_run.probability_columns([0, 1, 2, 3])[-1], "p(mã 3)")

    def test_mot_dong_cho_moi_o_review_nhan_khia_canh(self):
        plan = {"aspects": ["colour", "price"], "split": "test", "row_index": [7, 9]}
        probs = [
            [[0.1, 0.9], [0.4, 0.6]],
            [[0.2, 0.8], [0.3, 0.7]],
        ]
        rows = encoder_run.probability_rows(plan, probs, [1, 2])
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0], ["7", "test", "colour", 0.1, 0.9])
        self.assertEqual(rows[1], ["7", "test", "price", 0.4, 0.6])
        self.assertEqual(rows[2], ["9", "test", "colour", 0.2, 0.8])
        self.assertEqual(rows[3], ["9", "test", "price", 0.3, 0.7])

    def test_so_o_cua_mot_dong_bang_so_cot(self):
        columns = encoder_run.probability_columns([0, 1, 2, 3])
        plan = {"aspects": ["price"], "split": "test", "row_index": [3]}
        rows = encoder_run.probability_rows(plan, [[[0.25, 0.25, 0.25, 0.25]]], [0, 1, 2, 3])
        self.assertEqual(len(rows[0]), len(columns))

    def test_cat_theo_so_ma_neu_hang_dai_hon(self):
        """Hàng xác suất dài hơn bộ mã thì CẮT, không ghi thừa cột (bảng phải khớp header)."""
        plan = {"aspects": ["price"], "split": "test", "row_index": [3]}
        rows = encoder_run.probability_rows(plan, [[[0.1, 0.2, 0.3, 0.4, 0.5]]], [1, 2])
        self.assertEqual(rows[0], ["3", "test", "price", 0.1, 0.2])


class ProbabilityPathTest(unittest.TestCase):
    def test_da_khai_mau_ten_tep_xac_suat(self):
        self.assertEqual(paths.pattern("probabilities"), "probabilities.csv")


if __name__ == "__main__":
    unittest.main()
