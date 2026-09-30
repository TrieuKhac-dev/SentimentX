# -*- coding: utf-8 -*-
"""Test bước Clean của pipeline (`src/pipeline/clean.py`): luật rò rỉ và PHẠM VI được sửa.

VÌ SAO CẦN FILE NÀY
Từ v0.2.0, `test` KHÔNG được sửa (đó là điều kiện để so với công bố tham chiếu), nên rò rỉ dữ liệu
được xử lý ở phía tập HỌC: trùng lặp giữa các tập bị loại ở tập ưu tiên THẤP hơn (`test` > `val` >
`train`). Luật này NGƯỢC với v0.1.0 (`remove_eval_overlap` loại ở val/test), và cả hai luật vẫn
nằm trong code vì bản dữ liệu cũ phải tái lập được.

ĐIỀU ĐƯỢC KHOÁ
    1. `apply_to` quyết định split nào được SỬA; không khai thì sửa mọi split (hành vi v0.1.0);
    2. luật mới loại ở tập ưu tiên thấp hơn và KHÔNG BAO GIỜ loại khỏi test;
    3. split ngoài `apply_to` giữ nguyên mọi dòng, kể cả dòng trùng và dòng trùng lặp;
    4. khai cả hai luật rò rỉ, hoặc tên split lạ, là LỖI - không đoán ý;
    5. luật cũ vẫn loại khỏi test như trước (bản dữ liệu v0.1.0 tái lập được).

Chạy: python -m unittest discover -s tests
"""

import copy
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.core import config, utils
from src.pipeline import PipelineConfigError, clean, editable_splits

ASPECTS = ["texture"]

# Cấu hình Clean của v0.2.0, trừ khoá `leakage` và `apply_to` mà từng test tự khai.
BASE = {
    "remove_empty": True,
    "remove_gibberish": True,
    "remove_ads": True,
    "remove_code": True,
    "deduplicate": {"exact": True, "normalized": True, "ignore_diacritics": False,
                    "scope": "within_split", "conflict_policy": "quarantine"},
}


def split_frame(items):
    """`[(văn bản, nhãn)]` -> DataFrame đúng dạng bước Load để lại."""
    return pd.DataFrame({config.TEXT_COLUMN: [item[0] for item in items],
                         "texture": [item[1] for item in items]})


class EditableSplitsTest(unittest.TestCase):
    """`apply_to`: bước được sửa split nào."""

    def test_khong_khai_thi_sua_moi_split(self):
        self.assertEqual(editable_splits("clean", {}, {"train": 1, "val": 1, "test": 1}),
                         ["train", "val", "test"])

    def test_chi_sua_cac_split_duoc_khai_va_giu_thu_tu_cua_splits(self):
        got = editable_splits("clean", {"apply_to": ["test", "train"]},
                              {"train": 1, "val": 1, "test": 1})
        self.assertEqual(got, ["train", "test"])

    def test_ten_split_la_la_loi(self):
        with self.assertRaises(PipelineConfigError):
            editable_splits("clean", {"apply_to": ["trian"]}, {"train": 1, "val": 1, "test": 1})

    def test_danh_sach_rong_la_loi(self):
        with self.assertRaises(PipelineConfigError):
            editable_splits("clean", {"apply_to": []}, {"train": 1, "val": 1, "test": 1})


class OverlapRuleTest(unittest.TestCase):
    """Luật mới: loại ở tập ưu tiên thấp hơn, `test` không bao giờ bị loại."""

    def records(self):
        shared = "Son này đẹp"
        return [
            {"split": "train", "pos": 0, "text": shared, "labels": ("positive",)},
            {"split": "train", "pos": 1, "text": "Chỉ có ở train", "labels": ("positive",)},
            {"split": "val", "pos": 0, "text": shared, "labels": ("positive",)},
            {"split": "val", "pos": 1, "text": "Chỉ có ở val", "labels": ("positive",)},
            {"split": "test", "pos": 0, "text": shared, "labels": ("positive",)},
            {"split": "test", "pos": 1, "text": "Chỉ có ở test", "labels": ("negative",)},
        ]

    def test_giu_o_test_roi_moi_toi_val_roi_train(self):
        kept, removed = clean._remove_overlap(
            self.records(), ["test", "val", "train"], {"train", "val"})
        self.assertEqual({(rec["split"], rec["pos"]) for rec in kept},
                         {("train", 1), ("val", 1), ("test", 0), ("test", 1)})
        self.assertEqual([row[0] for row in removed], ["train", "val"])
        self.assertIn("test", removed[0][2])

    def test_quy_tac_doi_loai_khoi_split_khong_duoc_sua_la_loi(self):
        with self.assertRaises(PipelineConfigError):
            clean._remove_overlap(self.records(), ["train", "val", "test"], {"train", "val"})



class CleanStepTest(unittest.TestCase):
    """Chạy cả bước: split ngoài `apply_to` giữ nguyên mọi dòng của nó."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.out_dir = Path(self._tmp.name)

    def context(self, **clean_cfg):
        rows = {
            # "Son đẹp" có ở cả train và test; test còn có hai dòng giống nhau.
            "train": [("Son đẹp", "positive"), ("Chỉ có ở train", "positive")],
            "val": [("Chỉ ở val", "negative")],
            "test": [("Son đẹp", "positive"), ("Lặp trong test", "positive"),
                     ("Lặp trong test", "positive")],
        }
        steps = copy.deepcopy(BASE)
        steps.update(clean_cfg)
        return {"config": {"version": "v0.2.0", "steps": {"clean": steps}},
                "out_dir": self.out_dir,
                "dataset": {"aspects": ASPECTS},
                "splits": {name: split_frame(items) for name, items in rows.items()}}

    def test_test_giu_nguyen_ca_dong_trung_va_dong_lap(self):
        context = self.context(apply_to=["train", "val"],
                               leakage={"keep_priority": ["test", "val", "train"]})
        clean.run(context)
        self.assertEqual(len(context["splits"]["test"]), 3)
        self.assertEqual(len(context["splits"]["train"]), 1)
        flow = utils.read_csv(self.out_dir / "clean_flow.csv").to_dict("records")
        test_row = [row for row in flow if row["split"] == "test"][0]
        self.assertEqual(int(test_row["bị loại"]), 0)
        reasons = utils.read_csv(self.out_dir / "clean_reasons.csv").to_dict("records")
        self.assertTrue(any("rò rỉ" in row["lý do"] for row in reasons))

    def test_luat_cu_van_loai_khoi_test(self):
        context = self.context(leakage={"remove_eval_overlap": True})
        clean.run(context)
        self.assertLess(len(context["splits"]["test"]), 3)

    def test_khai_ca_hai_luat_la_loi(self):
        context = self.context(leakage={"remove_eval_overlap": True,
                                        "keep_priority": ["test", "val", "train"]})
        with self.assertRaises(PipelineConfigError):
            clean.run(context)

    def test_keep_priority_thieu_ten_split_la_loi(self):
        context = self.context(leakage={"keep_priority": ["test", "train"]})
        with self.assertRaises(PipelineConfigError):
            clean.run(context)


if __name__ == "__main__":
    unittest.main()
