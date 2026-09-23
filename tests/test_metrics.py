# -*- coding: utf-8 -*-
"""Test chỉ số đánh giá (src/evaluation/metrics.py).

Chạy: python -m unittest discover -s tests
"""

import unittest

from src.evaluation import metrics


class TestScore(unittest.TestCase):
    def setUp(self):
        self.aspects = ["texture", "price"]

    def test_perfect_answers(self):
        gold = [{"texture": 1, "price": 0}, {"texture": 2, "price": 3}]
        pred = [{"texture": 1, "price": 0}, {"texture": 2, "price": 3}]
        rows, summary = metrics.score(gold, pred, self.aspects)
        self.assertEqual(summary["acc macro"], 100.0)
        self.assertEqual(summary["khớp hoàn toàn"], 100.0)
        self.assertEqual(summary["F1 nhắc macro"], 1.0)

    def test_unreadable_prediction_counts_as_wrong(self):
        gold = [{"texture": 1, "price": 0}]
        pred = [None]
        rows, summary = metrics.score(gold, pred, self.aspects)
        # Không đọc được kết quả thì KHÔNG biết model đã đoán gì, nên cả 2 ô đều tính là
        # sai (đây là lựa chọn bảo thủ có chủ ý: bỏ mẫu ra khỏi mẫu số sẽ vô tình nâng điểm
        # cho model trả lời hỏng định dạng).
        self.assertEqual(summary["acc macro"], 0.0)
        self.assertEqual(summary["khớp hoàn toàn"], 0.0)
        # Nhưng chỉ số "nhắc tới" không bị phạt hai lần: gold=1 thì mất recall,
        # gold=0 thì không sinh ra lỗi dương tính giả.
        self.assertEqual(rows[0]["R nhắc"], 0.0)
        self.assertEqual(rows[1]["P nhắc"], 0.0)

    def test_missing_aspect_in_prediction_is_wrong(self):
        gold = [{"texture": 1, "price": 0}]
        pred = [{"price": 0}]
        _rows, summary = metrics.score(gold, pred, self.aspects)
        self.assertEqual(summary["acc macro"], 50.0)

    def test_mention_metrics_split_the_two_questions(self):
        # Model nhận ra khía cạnh nhưng chọn SAI sắc thái: R nhắc = 1, acc < 100.
        gold = [{"texture": 1, "price": 0}]
        pred = [{"texture": 2, "price": 0}]
        rows, summary = metrics.score(gold, pred, self.aspects)
        self.assertEqual(rows[0]["R nhắc"], 1.0)
        self.assertEqual(rows[0]["acc"], 0.0)
        self.assertEqual(rows[0]["acc khi có nhắc"], 0.0)
        self.assertEqual(summary["acc macro"], 50.0)

    def test_false_positive_mention_lowers_precision(self):
        gold = [{"texture": 0, "price": 0}]
        pred = [{"texture": 2, "price": 0}]
        rows, _summary = metrics.score(gold, pred, self.aspects)
        self.assertEqual(rows[0]["P nhắc"], 0.0)
        self.assertEqual(rows[0]["F1 nhắc"], 0.0)

    def test_over_prediction_lowers_precision_not_recall(self):
        """Chỉ có DƯƠNG TÍNH GIẢ: model nêu thừa khía cạnh không được nhắc.

        3 khía cạnh thật sự được nhắc đều tìm đúng, và thêm 1 lần nêu thừa:
            P = 3/4 = 0.75   R = 3/3 = 1.0
        Ca này BẤT ĐỐI XỨNG nên bắt được lỗi hoán vị FP/FN (nếu hoán vị thì P và R đổi chỗ).
        """
        gold = [{"texture": 1}, {"texture": 1}, {"texture": 1}, {"texture": 0}]
        pred = [{"texture": 1}, {"texture": 1}, {"texture": 1}, {"texture": 2}]
        rows, _summary = metrics.score(gold, pred, ["texture"])
        self.assertEqual(rows[0]["P nhắc"], 0.75)
        self.assertEqual(rows[0]["R nhắc"], 1.0)

    def test_under_prediction_lowers_recall_not_precision(self):
        """Chỉ có ÂM TÍNH GIẢ: model bỏ sót khía cạnh được nhắc.

        1/2 khía cạnh được nhắc tìm đúng, không nêu thừa lần nào:
            P = 1/1 = 1.0    R = 1/2 = 0.5
        """
        gold = [{"texture": 1}, {"texture": 1}, {"texture": 0}]
        pred = [{"texture": 1}, {"texture": 0}, {"texture": 0}]
        rows, _summary = metrics.score(gold, pred, ["texture"])
        self.assertEqual(rows[0]["P nhắc"], 1.0)
        self.assertEqual(rows[0]["R nhắc"], 0.5)

    def test_macro_counts_over_prediction_as_lower_f1(self):
        """F1 phải giảm khi model nêu thừa — kiểm bằng số, không kiểm bằng cảm giác.

        Lưu ý: đoán ĐÚNG mã nhưng khác sắc thái (2 thay vì 1) KHÔNG làm giảm F1 "nhắc tới",
        vì phép đo này chỉ hỏi "có nhắc hay không". Muốn F1 giảm thì phải nêu thừa một khía
        cạnh mà nhãn đúng là 0.
        """
        gold = [{"texture": 1}, {"texture": 0}]
        noisy = [{"texture": 1}, {"texture": 2}]
        _rows, summary_clean = metrics.score(gold, gold, ["texture"])
        _rows2, summary_noisy = metrics.score(gold, noisy, ["texture"])
        self.assertEqual(summary_clean["F1 nhắc micro"], 1.0)
        self.assertAlmostEqual(summary_noisy["F1 nhắc micro"], 0.667, places=3)


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
