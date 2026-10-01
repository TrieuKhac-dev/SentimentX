# -*- coding: utf-8 -*-
"""C-3: ca BẤT ĐỐI XỨNG (P != R) để bắt lỗi hoán vị FP/FN trong hàm chấm điểm.

Vì sao cần: F1 ĐỐI XỨNG, nên một ca "dễ" (precision == recall) vẫn xanh dù FP/FN bị đổi chỗ - sự cố
thật đã xảy ra (xem docs/04_experiments/03_training_eval.md mục 2.1). Ca dưới đây khoá đúng QUAN HỆ
giữa P và R, nên hoán vị là đỏ ngay.

Chạy: python -m unittest discover -s tests
"""

import unittest

from src.evaluation import scorers


def _samples():
    """4 ô khía cạnh `smell`: 3 ô đúng là positive, 1 ô đúng là không nhắc tới.

    Model đoán: 1 ô positive, 3 ô negative -> lớp positive có precision > recall (đúng chiều, KHÔNG
    phải chiều ngược), nên P và R phải KHÁC nhau.
    """
    gold = [{"smell": 1}, {"smell": 1}, {"smell": 1}, {"smell": 0}]
    pred = [{"smell": 1}, {"smell": 2}, {"smell": 2}, {"smell": 2}]
    return scorers.Samples.build(
        ["smell"], gold, pred,
        task={"label_space": "binary", "neutral_policy": "drop", "not_mentioned": "separate"},
        labels={0: "", 1: "positive", 2: "negative"})


class AsymmetricMetricTest(unittest.TestCase):
    def test_precision_is_higher_than_recall(self):
        item = _samples().per_sentiment()["by_aspect"]["smell"][1]
        self.assertGreater(item["precision"], item["recall"],
                           "hoán vị FP/FN sẽ đảo hai con số này -> phải đỏ")
        self.assertLess(item["f1"], item["precision"])
        self.assertGreater(item["f1"], item["recall"])

    def test_macro_average_differs_from_the_two_classes(self):
        macro = _samples().per_sentiment()["macro"]
        self.assertLess(macro["f1"], 0.5,
                        "lớp negative không có ô đúng nào nên macro-F1 phải bị kéo xuống")


if __name__ == "__main__":
    unittest.main()
