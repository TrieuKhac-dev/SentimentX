# -*- coding: utf-8 -*-
"""Test các bộ chấm điểm (src/evaluation/scorers/).

Các ca ở đây khoá ĐÚNG quy ước trong docs/04_experiments/metrics.md:
    - ô không đọc được tính là SAI, không bỏ khỏi mẫu số
    - lớp dương của "có nhắc tới" là CÓ nhắc tới, nên phải có ca BẤT ĐỐI XỨNG (chỉ dương tính
      giả, và chỉ âm tính giả) - nếu hoán vị FP/FN thì F1 không đổi nhưng Precision/Recall đổi
      chỗ, và đó là lỗi đã từng xảy ra thật
    - ô neutral bị loại theo `neutral_policy` được ĐẾM và ghi lại
    - điểm macro chỉ lấy trung bình trên đơn vị có dữ liệu để chấm

Chạy: python -m unittest discover -s tests
"""

import json
import tempfile
import unittest
from pathlib import Path

from src.evaluation import scorers

TASK = {"label_space": "binary", "neutral_policy": "drop", "not_mentioned": "separate"}
LABELS = {0: "không nhắc", 1: "positive", 2: "negative", 3: "neutral"}


def build(gold, pred, aspects=("texture", "price"), task=None, **kwargs):
    """Đóng gói dữ liệu đã chiếu để chấm, dùng đúng lớp `scorers.Samples.build`."""
    return scorers.Samples.build(list(aspects), gold, pred,
                                 task=dict(task or TASK), labels=LABELS, **kwargs)


def score(name, gold, pred, aspects=("texture", "price"), task=None, **kwargs):
    """Chạy MỘT bộ chấm, trả về `values` của nó."""
    samples = build(gold, pred, aspects=aspects, task=task, **kwargs)
    return scorers.run_all(samples, names=[name])["scores"][name]


class TestAccuracy(unittest.TestCase):
    def test_perfect_answers(self):
        rows = [{"texture": 1, "price": 0}, {"texture": 2, "price": 3}]
        values = score("accuracy", rows, rows)
        self.assertEqual(values["macro"], 100.0)
        self.assertEqual(values["micro"], 100.0)
        self.assertEqual(values["when_mentioned_macro"], 100.0)

    def test_unreadable_prediction_counts_as_wrong(self):
        """Không đọc được thì KHÔNG biết model đã đoán gì, nên cả hai ô đều tính là sai.

        Bỏ mẫu ra khỏi mẫu số sẽ vô tình nâng điểm cho model trả lời hỏng định dạng.
        """
        gold = [{"texture": 1, "price": 0}]
        values = score("accuracy", gold, [None])
        self.assertEqual(values["macro"], 0.0)
        self.assertEqual(values["micro"], 0.0)

    def test_missing_aspect_in_prediction_is_wrong(self):
        gold = [{"texture": 1, "price": 0}]
        values = score("accuracy", gold, [{"price": 0}])
        self.assertEqual(values["macro"], 50.0)

    def test_mention_metrics_split_the_two_questions(self):
        """Model nhận ra khía cạnh nhưng chọn SAI sắc thái: recall nhắc = 1, accuracy = 0."""
        gold = [{"texture": 1, "price": 0}]
        pred = [{"texture": 2, "price": 0}]
        detection = score("aspect_detection", gold, pred)
        self.assertEqual(detection["by_aspect"]["texture"]["recall"], 1.0)
        values = score("accuracy", gold, pred)
        self.assertEqual(values["by_aspect"]["texture"], 0.0)
        self.assertEqual(values["when_mentioned_by_aspect"]["texture"], 0.0)
        self.assertEqual(values["macro"], 50.0)

    def test_macro_skips_aspect_without_mentioned_cells(self):
        """Khía cạnh không được nhắc trong tập đang chấm không bị tính là 0."""
        gold = [{"texture": 1, "price": 0}]
        values = score("accuracy", gold, gold)
        self.assertEqual(values["by_aspect"]["price"], 100.0)
        self.assertEqual(values["when_mentioned_by_aspect"]["price"], 0.0)
        # Điểm macro khi đã nhắc tới chỉ tính khía cạnh thật sự có ô để chấm.
        self.assertEqual(values["when_mentioned_macro"], 100.0)


class TestAspectDetection(unittest.TestCase):
    def test_over_prediction_lowers_precision_not_recall(self):
        """Chỉ có DƯƠNG TÍNH GIẢ: model nêu thừa khía cạnh không được nhắc.

        3 khía cạnh thật sự được nhắc đều tìm đúng, thêm 1 lần nêu thừa:
            P = 3/4 = 0.75   R = 3/3 = 1.0
        Ca này BẤT ĐỐI XỨNG nên bắt được lỗi hoán vị FP/FN.
        """
        gold = [{"texture": 1}, {"texture": 1}, {"texture": 1}, {"texture": 0}]
        pred = [{"texture": 1}, {"texture": 1}, {"texture": 1}, {"texture": 2}]
        item = score("aspect_detection", gold, pred, aspects=["texture"])["by_aspect"]["texture"]
        self.assertEqual(item["precision"], 0.75)
        self.assertEqual(item["recall"], 1.0)

    def test_under_prediction_lowers_recall_not_precision(self):
        """Chỉ có ÂM TÍNH GIẢ: model bỏ sót khía cạnh được nhắc.

        1/2 khía cạnh được nhắc tìm đúng, không nêu thừa lần nào:
            P = 1/1 = 1.0    R = 1/2 = 0.5
        """
        gold = [{"texture": 1}, {"texture": 1}, {"texture": 0}]
        pred = [{"texture": 1}, {"texture": 0}, {"texture": 0}]
        item = score("aspect_detection", gold, pred, aspects=["texture"])["by_aspect"]["texture"]
        self.assertEqual(item["precision"], 1.0)
        self.assertEqual(item["recall"], 0.5)

    def test_false_positive_mention_lowers_precision(self):
        gold = [{"texture": 0, "price": 0}]
        pred = [{"texture": 2, "price": 0}]
        item = score("aspect_detection", gold, pred)["by_aspect"]["texture"]
        self.assertEqual(item["precision"], 0.0)
        self.assertEqual(item["f1"], 0.0)

    def test_unreadable_answer_loses_recall_only(self):
        """Ô không đọc được coi như model KHÔNG nêu khía cạnh: mất recall, không sinh ra FP."""
        gold = [{"texture": 1, "price": 0}]
        item = score("aspect_detection", gold, [None])["by_aspect"]["texture"]
        self.assertEqual(item["recall"], 0.0)
        self.assertEqual(item["fp"], 0)

    def test_micro_f1_drops_when_over_predicting(self):
        gold = [{"texture": 1}, {"texture": 0}]
        noisy = [{"texture": 1}, {"texture": 2}]
        clean = score("aspect_detection", gold, gold, aspects=["texture"])["micro"]["f1"]
        dirty = score("aspect_detection", gold, noisy, aspects=["texture"])["micro"]["f1"]
        self.assertEqual(clean, 1.0)
        self.assertEqual(dirty, 0.667)


class TestLabelProjection(unittest.TestCase):
    def test_neutral_cells_are_dropped_and_counted(self):
        """`neutral_policy: drop` loại ô neutral và số ô bị loại phải ĐẾM được."""
        gold = [{"texture": 1, "price": 3}, {"texture": 2, "price": 1}]
        samples = build(gold, gold)
        self.assertEqual(samples.meta["dropped_neutral"], 1)
        self.assertEqual(samples.meta["dropped_neutral_by_aspect"]["price"], 1)
        self.assertEqual(samples.accuracy()["by_aspect"]["price"]["cells"], 1)
        self.assertEqual(score("aggregate", gold, gold)["exact_match"]["percent"], 100.0)

    def test_as_negative_keeps_every_cell(self):
        """Gộp neutral vào negative thì không loại ô nào, và nhãn đoán cũng đổi theo."""
        gold = [{"texture": 3, "price": 1}]
        pred = [{"texture": 2, "price": 1}]
        task = dict(TASK, neutral_policy="as_negative")
        samples = build(gold, pred, task=task)
        self.assertEqual(samples.meta["dropped_neutral"], 0)
        self.assertEqual(samples.accuracy()["macro"], 100.0)

    def test_exact_match_ignores_dropped_cells(self):
        gold = [{"texture": 1, "price": 3}, {"texture": 1, "price": 1}]
        pred = [{"texture": 1, "price": 2}, {"texture": 2, "price": 1}]
        # Ô price của review 0 bị loại, nên chỉ còn texture của review 0 đúng và review 1 sai.
        self.assertEqual(score("aggregate", gold, pred)["exact_match"]["percent"], 50.0)


class TestPrfPerSentiment(unittest.TestCase):
    def test_counts_once_per_class(self):
        """Mỗi cặp (khía cạnh, sắc thái) đếm theo kiểu một-chọi-phần-còn-lại."""
        gold = [{"texture": 1}, {"texture": 2}, {"texture": 1}]
        pred = [{"texture": 1}, {"texture": 2}, {"texture": 2}]
        values = score("prf", gold, pred, aspects=["texture"])
        positive = values["by_aspect"]["texture"]["positive"]
        negative = values["by_aspect"]["texture"]["negative"]
        self.assertEqual(positive, {"precision": 1.0, "recall": 0.5, "f1": 0.667,
                                    "support": 2})
        self.assertEqual(negative, {"precision": 0.5, "recall": 1.0, "f1": 0.667,
                                    "support": 1})
        self.assertEqual(values["micro"]["f1"], 0.667)
        # Macro là trung bình của P/R/F1 TỪNG CẶP đã tính riêng, không trộn ba chỉ số vào nhau.
        self.assertEqual(values["macro"], {"precision": 0.75, "recall": 0.75, "f1": 0.667})

    def test_sentiment_list_excludes_not_mentioned(self):
        values = score("prf", [{"texture": 1}], [{"texture": 1}], aspects=["texture"])
        self.assertEqual(values["sentiments"], ["positive", "negative"])


class TestConfusionAndMispredictions(unittest.TestCase):
    def test_confusion_counts_every_cell(self):
        """Ma trận nhầm phải đếm ĐỦ mọi ô, kể cả ô model trả lời hỏng định dạng."""
        gold = [{"texture": 1}, {"texture": 0}]
        samples = build(gold, [{"texture": 1}, None], aspects=["texture"])
        table = samples.confusion("texture")
        self.assertEqual(table["positive"], {"positive": 1})
        self.assertEqual(table["không nhắc"], {"không đọc được": 1})

    def test_mispredictions_keep_the_review_index(self):
        gold = [{"texture": 1}, {"texture": 0}]
        samples = build(gold, [{"texture": 1}, None], aspects=["texture"],
                        sample_ids=["r1", "r2"])
        self.assertEqual(samples.mispredictions(), [{
            "review": "r2", "aspect": "texture", "gold": "không nhắc",
            "pred": "không đọc được"}])


class TestRegistry(unittest.TestCase):
    def test_available_lists_the_five_scorers(self):
        self.assertEqual(scorers.available(),
                         ["accuracy", "aspect_detection", "prf", "aggregate", "confusion"])

    def test_check_rejects_unknown_name(self):
        """Tên chỉ số lạ phải báo lỗi kèm danh sách, không im lặng bỏ qua."""
        with self.assertRaises(scorers.base.ScorerError) as caught:
            scorers.check(["accuracy", "khong_co"])
        self.assertIn("khong_co", str(caught.exception))
        self.assertIn("aspect_detection", str(caught.exception))

    def test_check_rejects_empty_list(self):
        with self.assertRaises(scorers.base.ScorerError):
            scorers.check([])

    def test_run_all_only_runs_selected_scores(self):
        gold = [{"texture": 1, "price": 0}]
        samples = build(gold, gold)
        result = scorers.run_all(samples, names=["aggregate"])
        self.assertEqual(list(result["scores"]), ["aggregate"])
        self.assertEqual(result["tables"], {})

    def test_build_requires_task_config(self):
        with self.assertRaises(scorers.base.ScorerError) as caught:
            build([{"texture": 1}], [{"texture": 1}], task={"label_space": "binary"})
        self.assertIn("neutral_policy", str(caught.exception))


class TestWrite(unittest.TestCase):
    def test_writes_three_files(self):
        gold = [{"texture": 1, "price": 3}, {"texture": 2, "price": 1}]
        samples = build(gold, [{"texture": 2, "price": 3}, {"texture": 2, "price": 1}],
                        sample_ids=["r1", "r2"])
        with tempfile.TemporaryDirectory() as folder:
            written = scorers.write(folder, samples, extra={"split": "val"})
            self.assertEqual(sorted(written), ["metrics.csv", "metrics.json",
                                               "mispredictions.csv"])
            payload = json.loads((Path(folder) / "metrics.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["split"], "val")
            self.assertEqual(payload["label_space"], "binary")
            self.assertEqual(payload["dropped_neutral"], 1)
            self.assertEqual(sorted(payload["scores"]), sorted(scorers.available()))
            self.assertIn("confusion", payload["tables"])
            self.assertEqual((Path(folder) / "metrics.csv").exists(), True)

    def test_extra_cannot_override_projection_facts(self):
        """`extra` là thông tin của lần chạy, không được đè lên phép chiếu nhãn."""
        gold = [{"texture": 1}]
        samples = build(gold, gold, aspects=["texture"])
        with tempfile.TemporaryDirectory() as folder:
            scorers.write(folder, samples, extra={"label_space": "full"})
            payload = json.loads((Path(folder) / "metrics.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["label_space"], "binary")

    def test_save_confusion_false_drops_tables(self):
        gold = [{"texture": 1}]
        samples = build(gold, gold, aspects=["texture"])
        with tempfile.TemporaryDirectory() as folder:
            scorers.write(folder, samples, save_confusion=False)
            payload = json.loads((Path(folder) / "metrics.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["tables"], {})


if __name__ == "__main__":
    unittest.main()


