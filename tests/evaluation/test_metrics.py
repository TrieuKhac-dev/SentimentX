# -*- coding: utf-8 -*-
"""Test phần ĐỌC KẾT QUẢ của model (src/evaluation/metrics.py).

Chỉ số đánh giá đã chuyển sang registry `src/evaluation/scorers/` - test ở `tests/test_scorers.py`.

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


if __name__ == "__main__":
    unittest.main()
