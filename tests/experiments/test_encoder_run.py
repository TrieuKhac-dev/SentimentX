# -*- coding: utf-8 -*-
"""Test phần TÍNH của đường encoder: bảng xác suất từng ô (`probabilities.csv`).

Vì sao khoá ở đây: bước kết hợp (dò ngưỡng theo khía cạnh, ensemble nhiều encoder, luật lai encoder +
LLM) đọc tệp xác suất rồi ghép với `predictions.csv` theo (chỉ số, khía cạnh). Sai một trong ba thứ -
tên cột mang mã nhãn, số dòng, hay thứ tự khía cạnh - thì bước kết hợp ghép nhầm ô mà KHÔNG báo lỗi.

Chạy: python -m unittest discover -s tests
"""

import shutil
import tempfile
import unittest
from pathlib import Path

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


class WriteProbabilitiesTest(unittest.TestCase):
    """Lỗi A: `utils.write_csv` nhận `(rows, columns, path)`, KHÔNG phải `(path, columns, rows)`.

    Gọi sai thứ tự thì `TypeError` nổ ở DÒNG CUỐI của lượt chạy - sau khi đã huấn luyện và suy luận
    xong cả lượt - nên lượt chạy mất trắng kết quả. Đã gặp thật: giết 5 lượt encoder (4 model mới +
    lượt chạy tiếp của xlm-roberta). Test này gọi thẳng hàm THUẦN (không GPU), nên lỗi không quay lại.
    """

    def write(self, plan, probabilities, codes):
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder, ignore_errors=True)
        path = encoder_run.write_probabilities(Path(folder), plan, probabilities, codes)
        return Path(path).read_text(encoding="utf-8-sig")

    def test_header_comes_from_the_columns(self):
        plan = {"aspects": ["price"], "split": "val", "row_index": [3]}
        text = self.write(plan, [[[0.25, 0.75]]], [1, 2])
        self.assertEqual(text.splitlines()[0], "chỉ số,split,khía cạnh,p(mã 1),p(mã 2)")

    def test_one_line_per_cell_review_times_aspect(self):
        plan = {"aspects": ["colour", "price"], "split": "val", "row_index": [3, 4]}
        text = self.write(plan, [[[0.1, 0.9], [0.2, 0.8]], [[0.3, 0.7], [0.4, 0.6]]], [1, 2])
        lines = text.strip().splitlines()
        self.assertEqual(len(lines), 5)                                  # 1 header + 4 ô
        self.assertEqual(lines[1].split(",")[:3], ["3", "val", "colour"])
        self.assertEqual(lines[4].split(",")[:3], ["4", "val", "price"])

    def test_written_under_the_declared_file_name(self):
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder, ignore_errors=True)
        plan = {"aspects": ["price"], "split": "val", "row_index": [3]}
        path = encoder_run.write_probabilities(Path(folder), plan, [[[0.5, 0.5]]], [1, 2])
        self.assertEqual(Path(path).name, paths.pattern("probabilities"))


if __name__ == "__main__":
    unittest.main()
