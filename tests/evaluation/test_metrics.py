# -*- coding: utf-8 -*-
"""Test phần ĐỌC KẾT QUẢ của model (src/evaluation/metrics.py).

Chỉ số đánh giá đã chuyển sang registry `src/evaluation/scorers/` - test ở `tests/evaluation/test_scorers.py`.

Chạy: python -m unittest discover -s tests
"""

import unittest

from src.evaluation import metrics


class TestReadRate(unittest.TestCase):
    def test_counts_reasons(self):
        infos = [
            {"valid": True},
            {"valid": False, "reason": "JSON không hợp lệ"},
            {"valid": False, "reason": "JSON không hợp lệ"},
        ]
        report = metrics.read_rate(infos)
        self.assertEqual(report["% đọc được"], 33.33)
        self.assertEqual(report["lí do lỗi"], {"JSON không hợp lệ": 2})

    def test_empty(self):
        report = metrics.read_rate([])
        self.assertEqual(report["tổng"], 0)
        self.assertEqual(report["% đọc được"], 0.0)


class TestReadRateGate(unittest.TestCase):
    """Cửa chất lượng `% đọc được` (luật 2 của `docs/04_experiments/metrics.md`).

    Lý do có cửa: ba lượt `Qwen/Qwen3-0.6B` ngày 02/10/2026 chỉ đọc được 3,33 / 1,36 / 1,73% mà
    `metrics.json` vẫn ra "hợp lệ" - rất dễ bị đem đi so. Cửa gắn cờ, KHÔNG xoá dữ liệu.
    """

    def test_khong_truyen_nguong_thi_khong_co_co(self):
        report = metrics.read_rate([{"valid": True}])
        self.assertNotIn("valid", report)
        self.assertNotIn("ngưỡng", report)
        self.assertNotIn("reason", report)

    def test_duoi_nguong_thi_valid_false_kem_li_do(self):
        infos = [{"valid": True}] + [{"valid": False, "reason": "không thấy JSON nào"}] * 9
        report = metrics.read_rate(infos, min_rate=95)
        self.assertEqual(report["% đọc được"], 10.0)
        self.assertIs(report["valid"], False)
        self.assertEqual(report["ngưỡng"], 95.0)
        self.assertIn("10.0%", report["reason"])
        self.assertIn("95", report["reason"])

    def test_dung_bang_nguong_thi_dat(self):
        infos = [{"valid": True}] * 95 + [{"valid": False}] * 5
        report = metrics.read_rate(infos, min_rate=95)
        self.assertEqual(report["% đọc được"], 95.0)
        self.assertIs(report["valid"], True)
        self.assertIsNone(report["reason"])

    def test_tren_nguong_thi_dat(self):
        report = metrics.read_rate([{"valid": True}] * 100, min_rate=95)
        self.assertIs(report["valid"], True)


if __name__ == "__main__":
    unittest.main()
