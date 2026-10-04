# -*- coding: utf-8 -*-
"""Test bốn bước KẾT HỢP (src/evaluation/fusion.py): ngưỡng, ensemble, lai, biểu quyết.

Vì sao khoá ở đây: bốn bước này ăn điểm bằng cách CHỌN LẠI nhãn từ thứ đã đo, nên lỗi của chúng là lỗi
im lặng (ghép nhầm ô, hoà chọn sai lượt, ngưỡng học trên tập sẽ báo cáo). Dữ liệu ở đây là TỔNG HỢP
(không cần GPU, không cần dữ liệu thật) nhưng đi qua ĐÚNG engine chấm điểm của dự án.

Chạy: python -m unittest discover -s tests
"""

import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from src.core import paths
from src.evaluation import fusion

TASK = {"label_space": "binary", "neutral_policy": "drop", "not_mentioned": "separate"}
LABELS = {1: "positive", 2: "negative"}


def make_run(golds, preds, probs, split="val", name="run"):
    """Lượt chạy tổng hợp: 3 khía cạnh, ô nào cũng được nhắc tới (đơn giản hoá để test dễ đọc)."""
    aspects = ["colour", "smell", "price"]
    sample_ids = [str(index) for index in range(len(golds))]
    return {
        "dir": Path("experiments/zz/lora/exp001/results/{}".format(name)),
        "rows": [], "aspects": aspects, "golds": golds, "preds": preds, "infos": [],
        "probabilities": probs, "codes": [1, 2], "labels": LABELS, "task": TASK,
        "meta": {}, "metrics": {}, "split": split, "sample_ids": sample_ids,
    }


def probabilities(rows):
    """`{(chỉ số, khía cạnh): {mã: xác suất}}` từ dict lồng nhau cho dễ viết test."""
    table = {}
    for sample_id, per_aspect in rows.items():
        for aspect, values in per_aspect.items():
            table[(str(sample_id), aspect)] = dict(values)
    return table


# colour: hai ô âm thật (mẫu 1 và 3); price: KHÔNG có ô âm nào (đúng ca `price` của dự án).
GOLDS = [{"colour": 1, "smell": 1, "price": 1},
         {"colour": 2, "smell": 1, "price": 1},
         {"colour": 1, "smell": 1, "price": 1},
         {"colour": 2, "smell": 1, "price": 1}]
PREDS_BASE = [{"colour": 1, "smell": 1, "price": 1}] * 4
PROBS = probabilities({
    0: {"colour": {1: 0.8, 2: 0.2}, "smell": {1: 0.9, 2: 0.1}, "price": {1: 0.7, 2: 0.3}},
    1: {"colour": {1: 0.1, 2: 0.9}, "smell": {1: 0.9, 2: 0.1}, "price": {1: 0.7, 2: 0.3}},
    2: {"colour": {1: 0.9, 2: 0.1}, "smell": {1: 0.9, 2: 0.1}, "price": {1: 0.7, 2: 0.3}},
    3: {"colour": {1: 0.2, 2: 0.8}, "smell": {1: 0.9, 2: 0.1}, "price": {1: 0.7, 2: 0.3}},
})


class ThresholdTest(unittest.TestCase):
    def setUp(self):
        self.run = make_run(GOLDS, PREDS_BASE, PROBS)

    def test_chi_day_ve_lop_am_va_giu_o_khong_dat_nguong(self):
        preds = fusion.apply_thresholds(self.run, {"colour": 0.5})
        self.assertEqual([pred["colour"] for pred in preds], [1, 2, 1, 2])
        # `price` không có ngưỡng -> giữ nguyên; `smell` không được khai -> giữ nguyên.
        self.assertEqual([pred["price"] for pred in preds], [1, 1, 1, 1])
        self.assertEqual([pred["smell"] for pred in preds], [1, 1, 1, 1])

    def test_khong_sua_ban_goc(self):
        fusion.apply_thresholds(self.run, {"colour": 0.5})
        self.assertEqual([pred["colour"] for pred in self.run["preds"]], [1, 1, 1, 1])

    def test_do_nguong_chon_nguong_LON_nhat_khi_hoa(self):
        rules = fusion.fit_thresholds(self.run)
        # F1 âm colour đạt 1,0 với mọi ngưỡng trong (0,2; 0,8] -> chọn 0,8 (đổi ít ô nhất).
        self.assertEqual(rules["ngưỡng_chốt"], {"colour": 0.8})
        self.assertEqual(rules["khía_cạnh"]["colour"]["f1_âm_gốc"], 0.0)
        self.assertEqual(rules["khía_cạnh"]["colour"]["f1_âm_sau"], 1.0)

    def test_khia_canh_khong_co_o_am_thi_khong_co_nguong(self):
        rules = fusion.fit_thresholds(self.run)
        price = rules["khía_cạnh"]["price"]
        self.assertIsNone(price["ngưỡng"])
        self.assertIn("không có ô âm", price["lí do"])
        self.assertTrue(price["sweep"], "vẫn phải giữ bảng quét làm bằng chứng")

    def test_so_o_khong_doi_va_macro_ghi_ca_hai_cach(self):
        rules = fusion.fit_thresholds(self.run)
        self.assertEqual(rules["cells_gốc"], rules["cells_sau"])
        self.assertEqual(rules["f1_âm_macro_gốc"]["số_khía_cạnh_có_ô_âm"], 1)


class EnsembleTest(unittest.TestCase):
    def setUp(self):
        weak = probabilities({index: {"colour": {1: 0.6, 2: 0.4}, "smell": {1: 0.9, 2: 0.1},
                                      "price": {1: 0.7, 2: 0.3}} for index in range(4)})
        good_preds = [{"colour": 2, "smell": 1, "price": 1} if index in (1, 3)
                      else {"colour": 1, "smell": 1, "price": 1} for index in range(4)]
        self.good = make_run(GOLDS, good_preds, PROBS, name="good")
        self.weak = make_run(GOLDS, PREDS_BASE, weak, name="weak")

    def test_trong_so_theo_val_va_chuan_hoa(self):
        weights = fusion.fit_ensemble_weights([self.good, self.weak])
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=6)
        self.assertGreater(weights[str(self.good["dir"])], weights[str(self.weak["dir"])])

    def test_trung_binh_xac_suat_roi_argmax(self):
        preds = fusion.ensemble_predictions(self.good, [self.good, self.weak])
        # mẫu 1 colour: (0,9 + 0,4)/2 = 0,65 > 0,35 -> mã âm
        self.assertEqual(preds[1]["colour"], 2)
        self.assertEqual(preds[0]["colour"], 1)

    def test_o_khong_co_xac_suat_thi_giu_nhan_cua_khung(self):
        empty = make_run(GOLDS, PREDS_BASE, {}, name="empty")
        preds = fusion.ensemble_predictions(self.good, [self.good, empty])
        self.assertEqual(preds[1]["colour"], 2)


class RulesTest(unittest.TestCase):
    def setUp(self):
        # LLM bắt được ô âm `colour`; encoder bắt được ô âm `smell`; `price` không nguồn nào có.
        self.golds = [dict(row) for row in GOLDS]
        self.golds[0]["smell"] = 2
        llm_preds = [{"colour": 2, "smell": 1, "price": 1} if index in (1, 3)
                     else {"colour": 1, "smell": 1, "price": 1} for index in range(4)]
        encoder_preds = [{"colour": 1, "smell": 2, "price": 1} if index == 0
                         else {"colour": 1, "smell": 1, "price": 1} for index in range(4)]
        self.llm = make_run(self.golds, llm_preds, PROBS, name="llm")
        self.encoder = make_run(self.golds, encoder_preds, PROBS, name="encoder")

    def test_chon_nguon_theo_f1_am_tren_val(self):
        rules = fusion.fit_rules(self.llm, self.encoder)
        self.assertEqual(rules["colour"]["nguồn"], "llm")     # LLM bắt được ô âm colour
        self.assertEqual(rules["smell"]["nguồn"], "encoder")  # encoder bắt được ô âm smell
        self.assertEqual(rules["price"]["nguồn"], "llm")      # không nguồn nào có ô âm
        self.assertIn("không có ô âm", rules["price"]["lí do"])

    def test_ap_luat_lay_nhan_theo_nguon_va_dem_o(self):
        rules = fusion.fit_rules(self.llm, self.encoder)
        preds, counts = fusion.apply_rules(self.llm, self.encoder, rules)
        self.assertEqual(preds[1]["colour"], 2)      # theo LLM
        self.assertEqual(preds[0]["smell"], 2)       # theo encoder
        self.assertEqual(counts["llm"] + counts["encoder"] + counts["thiếu"], 12)


class VoteTest(unittest.TestCase):
    def _run(self, preds, name):
        return make_run(GOLDS, preds, PROBS, split="test", name=name)

    def test_da_so_va_hoa_lay_luot_dau_tien(self):
        first = self._run([{"colour": 1, "smell": 1, "price": 1}] * 4, "seed1")
        second = self._run([{"colour": 2, "smell": 1, "price": 1}] * 4, "seed2")
        third = self._run([{"colour": 1, "smell": 1, "price": 1}] * 4, "seed3")
        preds, counts = fusion.vote([first, second, third])
        self.assertEqual([pred["colour"] for pred in preds], [1, 1, 1, 1])  # 2 phiếu mã 1
        self.assertEqual(counts["ô hoà"], 0)
        # hai lượt đối nhau -> hoà -> lấy lượt ĐẦU TIÊN (seed nhỏ nhất)
        preds, counts = fusion.vote([first, second])
        self.assertEqual([pred["colour"] for pred in preds], [1, 1, 1, 1])
        self.assertEqual(counts["ô hoà"], 4)

    def test_o_khong_luot_nao_doc_duoc_thi_khong_co_phieu(self):
        blank = self._run([{"colour": None, "smell": None, "price": None}] * 4, "seed1")
        preds, counts = fusion.vote([blank])
        self.assertEqual(counts["ô không lượt nào đọc được"], 12)
        self.assertIsNone(preds[0]["colour"])


class InputsTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="sentimentx-fusion-"))
        self.addCleanup(shutil.rmtree, str(self.root), ignore_errors=True)

    def test_dau_vao_rut_gon_du_cot_va_du_dong(self):
        run = make_run(GOLDS, PREDS_BASE, PROBS)
        path = fusion.dump_inputs(run, self.root / paths.pattern("probabilities"))
        with open(path, "r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 12)                      # 4 mẫu × 3 khía cạnh
        self.assertEqual(list(rows[0]), ["chỉ số", "split", "khía cạnh", "nhãn đúng", "nhãn đoán",
                                         "p(mã âm)", "p(mã dương)"])
        self.assertEqual(rows[3]["p(mã âm)"], "0.9")          # mẫu 1, colour (dòng 3 = 1 mẫu × 3 khía cạnh)

    def test_bao_cao_kem_so_o_va_f1_am(self):
        run = make_run(GOLDS, PREDS_BASE, PROBS)
        report = fusion.report_of(run)
        self.assertEqual(report["cells_paper"], 12)
        self.assertIsNone(report["f1_âm_từng_khía_cạnh"]["price"])
        self.assertIn("macro_trên_khía_cạnh_có_ô_âm", report["f1_âm_macro"])


if __name__ == "__main__":
    unittest.main()
