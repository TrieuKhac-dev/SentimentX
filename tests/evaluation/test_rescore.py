# -*- coding: utf-8 -*-
"""Test chấm lại (rescore): CHỈ THÊM, KHÔNG ghi đè số gốc.

Chạy: python -m unittest discover -s tests
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.core import paths, utils
from src.evaluation import rescore

BUILD = "ma-ds0.1.0"


class RescoreAdditiveTest(unittest.TestCase):
    """`rescore` ghi file MỚI và để nguyên `metrics.json`/`metrics.csv` của lượt chạy."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(self.root), ignore_errors=True)
        patcher = mock.patch.dict(os.environ, {paths.ENV_DATA_ROOT: str(self.root / "data")})
        patcher.start()
        self.addCleanup(patcher.stop)
        label_map = self.root / "data" / "processed" / BUILD / "label_map.json"
        label_map.parent.mkdir(parents=True)
        label_map.write_text(
            json.dumps({"id_to_label": {"0": "", "1": "positive", "2": "negative"}}),
            encoding="utf-8")

        self.dir = self.root / "run"
        self.dir.mkdir()
        self.meta = {
            "task": {"label_space": "binary", "neutral_policy": "drop", "not_mentioned": "separate"},
            "data": {"build": BUILD, "dataset": "cosmetics"},
        }
        self.metrics = {"scores_order": ["accuracy", "prf"], "aspects": ["smell", "price"]}
        self.original_csv = "aspect,sentiment,metric,value,basis\nsmell,all,accuracy,0.5,all\n"
        (self.dir / paths.pattern("run_meta")).write_text(
            json.dumps(self.meta, ensure_ascii=False), encoding="utf-8")
        (self.dir / paths.pattern("metrics_json")).write_text(
            json.dumps(self.metrics, ensure_ascii=False), encoding="utf-8")
        (self.dir / paths.pattern("metrics_csv")).write_text(self.original_csv, encoding="utf-8")
        self.rows = [
            ["0", "test", "", "khối KẾT QUẢ", "có", "ok", "son đẹp",
             json.dumps({"smell": 1, "price": 0}), json.dumps({"smell": 1, "price": 0}),
             "0", "0", "không", "không", ""],
            ["1", "test", "", "khối KẾT QUẢ", "có", "ok", "son lâu trôi",
             json.dumps({"smell": 2, "price": 1}), json.dumps({"smell": 1, "price": 1}),
             "0", "0", "không", "không", ""],
        ]
        utils.write_csv(self.rows, ["chỉ số", "split", "prompt", "kiểu đọc", "đọc được",
                                    "tình trạng đọc", "text", "nhãn đúng", "nhãn đoán", "token sinh",
                                    "giây", "có suy luận", "có <think>", "câu trả lời"],
                        self.dir / paths.pattern("predictions"))

    def test_writes_new_files_and_keeps_the_originals(self):
        before_json = (self.dir / paths.pattern("metrics_json")).read_text(encoding="utf-8")
        before_csv = (self.dir / paths.pattern("metrics_csv")).read_text(encoding="utf-8")

        written = rescore.run(self.dir, log=None)

        self.assertIn(paths.pattern("metrics_rescored_json"), written)
        self.assertIn(paths.pattern("metrics_rescored_csv"), written)
        payload = json.loads((self.dir / paths.pattern("metrics_rescored_json")).read_text(
            encoding="utf-8"))
        self.assertIn("scores", payload)
        self.assertIn("scores_paper", payload)
        self.assertIn("rescored", payload)
        self.assertEqual(payload["rescored"]["source"], paths.pattern("predictions"))
        # KHÔNG ghi đè: hai file gốc y nguyên từng byte.
        self.assertEqual((self.dir / paths.pattern("metrics_json")).read_text(encoding="utf-8"),
                         before_json)
        self.assertEqual((self.dir / paths.pattern("metrics_csv")).read_text(encoding="utf-8"),
                         before_csv)

    def test_missing_predictions_is_a_clear_error(self):
        (self.dir / paths.pattern("predictions")).unlink()
        with self.assertRaises(rescore.RescoreError) as caught:
            rescore.run(self.dir, log=None)
        self.assertIn(paths.pattern("predictions"), str(caught.exception))

    def test_missing_label_map_is_a_clear_error(self):
        shutil.rmtree(str(self.root / "data"))
        with self.assertRaises(rescore.RescoreError) as caught:
            rescore.run(self.dir, log=None)
        self.assertIn("label_map", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
