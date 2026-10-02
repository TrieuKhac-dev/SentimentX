# -*- coding: utf-8 -*-
"""D-5: curve train/val (`plots/training.html`) đọc từ `training_history.csv`.

Chạy: python -m unittest discover -s tests
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from src.core import paths, utils
from src.reporting import charts, curves, render

ROWS = [
    ["step", "epoch", "train_loss", "val_loss", "sentiment_precision", "sentiment_recall",
     "sentiment_f1"],
    [100, 1, "1.20", "1.10", "0.80", "0.60", "0.68"],
    [200, 1, "0.90", "0.95", "0.82", "0.70", "0.75"],
]


class CurvesTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(self.dir), ignore_errors=True)
        self.history = utils.write_csv(ROWS[1:], ROWS[0],
                                       self.dir / paths.pattern("training_history"))

    def test_line_kind_is_registered(self):
        self.assertIn("line", charts.CHART_KINDS)
        fig = charts.build({"kind": "line", "x": ["1", "2"],
                           "series": {"a": [1, 2], "b": [2, 1]}})
        self.assertEqual(len(fig.data), 2)

    def test_payload_has_a_curve_for_loss_and_for_f1(self):
        frame = utils.read_csv(self.history)
        data = curves.payload(frame.to_dict("records"), list(frame.columns))
        titles = [spec["title"] for spec in data["specs"]]
        self.assertEqual(len(titles), 2)
        self.assertTrue(any("Loss" in title for title in titles))
        self.assertTrue(any("F1" in title for title in titles))
        self.assertIn("sentiment_f1", data["specs"][1]["series"])

    def test_write_html_creates_the_plot_under_the_result_dir(self):
        path = curves.write_html(self.history, self.dir)
        self.assertIsNotNone(path)
        self.assertEqual(path.parent.name, paths.pattern("plots"))
        text = path.read_text(encoding="utf-8")
        self.assertIn("Loss", text)
        self.assertIn("sentiment_f1", text)

    def test_missing_history_is_no_chart(self):
        self.assertIsNone(curves.write_html(self.dir / "khong-co.csv", self.dir))

    def test_render_uses_the_project_template(self):
        frame = utils.read_csv(self.history)
        html = render.build_training_html(
            curves.payload(frame.to_dict("records"), list(frame.columns)), self.dir)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("plotly", html.lower())


if __name__ == "__main__":
    unittest.main()
