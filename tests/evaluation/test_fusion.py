# -*- coding: utf-8 -*-
"""Test năm bước KẾT HỢP (src/evaluation/fusion.py): ngưỡng, ensemble, lai, biểu quyết, router.

Vì sao khoá ở đây: năm bước này ăn điểm bằng cách CHỌN LẠI nhãn từ thứ đã đo, nên lỗi của chúng là lỗi
im lặng (ghép nhầm ô, hoà chọn sai lượt, ngưỡng học trên tập sẽ báo cáo). Dữ liệu ở đây là TỔNG HỢP
(không cần GPU, không cần dữ liệu thật) nhưng đi qua ĐÚNG engine chấm điểm của dự án.

Chạy: python -m unittest discover -s tests
"""

import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from src.core import paths, utils
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


class AppliedReportTest(unittest.TestCase):
    """Bước THỨ HAI của đường ngưỡng: lấy tệp luật đã chốt trên `val` rồi áp lên một lượt khác.

    Vì sao khoá ở đây: đây là chỗ sinh ra SỐ BÁO CÁO (áp lên `test`), mà luật 1 của `metrics.md` cấm
    gộp hai bước. Lỗi im lặng của bước này là áp nhầm không gian nhãn, hoặc làm `price` đổi theo.
    """

    def setUp(self):
        self.run = make_run(GOLDS, PREDS_BASE, PROBS, split="test")
        self.rules = fusion.fit_thresholds(make_run(GOLDS, PREDS_BASE, PROBS))

    def test_de_nguyen_price_va_giu_nguyen_so_o(self):
        report = fusion.applied_report(self.run, self.rules)
        self.assertEqual(report["ngưỡng_dùng"], {"colour": 0.8})
        self.assertEqual(report["khía_cạnh_để_nguyên"], ["smell", "price"])
        self.assertEqual(report["số_ô_trước"], report["số_ô_sau"])
        # `price` không có ô âm nên không có ngưỡng: F1 âm giữ nguyên `None` ở CẢ hai bên.
        self.assertIsNone(report["f1_âm_từng_khía_cạnh_trước"]["price"])
        self.assertIsNone(report["f1_âm_từng_khía_cạnh_sau"]["price"])
        self.assertIsNone(report["chênh_f1_âm_từng_khía_cạnh"]["price"])
        self.assertEqual(report["chênh_f1_âm_từng_khía_cạnh"]["colour"], 1.0)
        self.assertIn("price", report["ghi_chú_đọc_số"])

    def test_macro_ghi_ca_hai_cach_va_chenh_lenh(self):
        report = fusion.applied_report(self.run, self.rules)
        self.assertEqual(report["chênh_f1_âm_macro"]["macro_trên_khía_cạnh_có_ô_âm"], 1.0)
        # Không khía cạnh nào có F1 âm > 0 ở trạng thái gốc -> chênh là `None`, KHÔNG phải 0,0.
        self.assertIsNone(report["chênh_f1_âm_macro"]["macro_trên_khía_cạnh_đang_dương"])
        self.assertEqual(report["f1_âm_macro_sau"]["macro_trên_khía_cạnh_đang_dương"], 1.0)
        # Cách thứ hai (mọi khía cạnh, `price` tính 0,0): 0,0 -> 1/3.
        self.assertEqual(report["macro_trên_mọi_khía_cạnh"]["trước"], 0.0)
        self.assertEqual(report["macro_trên_mọi_khía_cạnh"]["sau"], round(1.0 / 3, 6))

    def test_lech_khong_gian_nhan_thi_bao_loi(self):
        rules = dict(self.rules, **{"mã_âm": 1})
        with self.assertRaises(fusion.FusionError):
            fusion.applied_report(self.run, rules)

    def test_khia_canh_co_nguong_khong_co_o_luot_nay_thi_ghi_lai(self):
        run = make_run([{"smell": 1}, {"smell": 2}], [{"smell": 1}, {"smell": 1}],
                       probabilities({0: {"smell": {1: 0.2, 2: 0.8}},
                                      1: {"smell": {1: 0.9, 2: 0.1}}}), split="test")
        run["aspects"] = ["smell"]
        report = fusion.applied_report(run, self.rules)
        self.assertEqual(report["khía_cạnh_có_ngưỡng_không_có_ở_lượt_này"], ["colour"])
        self.assertEqual(report["khía_cạnh_để_nguyên"], ["smell"])


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


class WeightsByModelTest(unittest.TestCase):
    """Trọng số ensemble CHỐT TRÊN `val` rồi ÁP LÊN `test`: khoá theo tên model, thiếu là LỖI.

    Vì sao khoá theo model mà không theo đường dẫn: lượt `val` và lượt `test` của cùng một encoder là
    hai thư mục khác nhau (`.../exp003` và `.../exp004`). Nếu không có đường này thì cách duy nhất để
    "áp trọng số val lên test" là tính lại trọng số TRÊN test - đúng thứ luật 1 của `metrics.md` cấm.
    """

    def setUp(self):
        self.good = make_run(GOLDS, [{"colour": 2, "smell": 1, "price": 1} if index in (1, 3)
                                     else {"colour": 1, "smell": 1, "price": 1} for index in range(4)],
                             PROBS, name="good")
        self.weak = make_run(GOLDS, PREDS_BASE, probabilities(
            {index: {"colour": {1: 0.6, 2: 0.4}, "smell": {1: 0.9, 2: 0.1},
                     "price": {1: 0.7, 2: 0.3}} for index in range(4)}), name="weak")
        self.good["meta"] = {"experiment": {"model": "phobert-base-v2"}}
        self.weak["meta"] = {"experiment": {"model": "visobert"}}

    def test_chot_trong_so_theo_model_va_chuan_hoa(self):
        weights = fusion.fit_weights_by_model([self.good, self.weak])
        self.assertEqual(sorted(weights), ["phobert-base-v2", "visobert"])
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=6)
        self.assertGreater(weights["phobert-base-v2"], weights["visobert"])

    def test_hai_luot_cung_model_la_loi(self):
        twin = make_run(GOLDS, PREDS_BASE, PROBS, name="twin")
        twin["meta"] = {"experiment": {"model": "phobert-base-v2"}}
        with self.assertRaises(fusion.FusionError) as found:
            fusion.fit_weights_by_model([self.good, twin])
        self.assertIn("phobert-base-v2", str(found.exception))

    def test_thieu_khoa_model_la_loi_khong_doan(self):
        nameless = make_run(GOLDS, PREDS_BASE, PROBS, name="nameless")
        with self.assertRaises(fusion.FusionError):
            fusion.model_of(nameless)

    def test_rap_bang_trong_so_vao_luot_khac_ten_thu_muc(self):
        """Ca thật: trọng số chốt trên `val` (`.../exp003`) đem áp cho lượt `test` (`.../exp004`)."""
        table = fusion.fit_weights_by_model([self.good, self.weak])
        test_good = make_run(GOLDS, PREDS_BASE, PROBS, split="test", name="other-dir")
        test_good["meta"] = {"experiment": {"model": "phobert-base-v2"}}
        weights = fusion.weights_for([test_good], table)
        self.assertEqual(weights[str(test_good["dir"])], table["phobert-base-v2"])

    def test_bang_trong_so_thieu_model_thi_bao_loi_kem_ten(self):
        test_run = make_run(GOLDS, PREDS_BASE, PROBS, split="test", name="other")
        test_run["meta"] = {"experiment": {"model": "cafebert"}}
        with self.assertRaises(fusion.FusionError) as found:
            fusion.weights_for([test_run], {"phobert-base-v2": 1.0})
        self.assertIn("cafebert", str(found.exception))

    def test_tep_trong_so_do_ghi_ro_nguon_chot(self):
        document = fusion.weights_document([self.good, self.weak],
                                           fusion.fit_weights_by_model([self.good, self.weak]))
        self.assertEqual(document["khoá"], "model")
        self.assertEqual([item["model"] for item in document["chốt_trên"]],
                         ["phobert-base-v2", "visobert"])

    def test_doc_tep_trong_so_sai_dinh_dang_thi_bao_loi(self):
        root = Path(tempfile.mkdtemp(prefix="sentimentx-fusion-"))
        self.addCleanup(shutil.rmtree, str(root), ignore_errors=True)
        path = root / "weights.json"
        path.write_text(json.dumps({"khác": 1}), encoding="utf-8")
        with self.assertRaises(fusion.FusionError):
            fusion.load_weights(path)
        good = root / "ok.json"
        good.write_text(json.dumps({"trọng_số": {"phobert-base-v2": 0.6, "visobert": 0.4}}),
                        encoding="utf-8")
        self.assertEqual(fusion.load_weights(good), {"phobert-base-v2": 0.6, "visobert": 0.4})


class AspectRouterTest(unittest.TestCase):
    """Router theo khía cạnh: chọn nguồn theo LUẬT đã chốt, hoà phải tất định, thiếu model là LỖI.

    Vì sao khoá ở đây: router ăn điểm bằng cách CHỌN LẠI nhãn, nên lỗi của nó là lỗi im lặng - chọn sai
    lượt cho một khía cạnh vẫn ra một con số trông hợp lệ. Luật (`fusion.ROUTER_LAW`) phải kiểm được
    từng nhánh: F1 lớp âm, chuyển sang accuracy khi không có ô âm, và thứ tự khi hoà.
    """

    def setUp(self):
        # `good`: đoán ĐÚNG hai ô âm của `colour` -> F1 âm `colour` = 1,0.
        good_preds = [{"colour": 2 if index in (1, 3) else 1, "smell": 1, "price": 1}
                      for index in range(4)]
        self.good = make_run(GOLDS, good_preds, PROBS, name="good")
        self.good["meta"] = {"experiment": {"model": "phobert-base-v2"}}
        # `weak`: đoán "dương" mọi ô -> F1 âm mọi khía cạnh = 0,0.
        self.weak = make_run(GOLDS, PREDS_BASE, PROBS, name="weak")
        self.weak["meta"] = {"experiment": {"model": "visobert"}}

    def test_chon_theo_f1_am_tung_khia_canh(self):
        router = fusion.fit_aspect_router([self.good, self.weak])
        self.assertEqual(router["colour"]["model"], "phobert-base-v2")
        self.assertIn("F1 lớp âm", router["colour"]["lí_do"])
        # `price`: val không có ô âm nào ở CẢ hai lượt -> chuyển sang accuracy, và GHI RÕ lí do.
        self.assertIn("không có ô âm", router["price"]["lí_do"])

    def test_bang_diem_giu_so_cua_MOI_ung_vien(self):
        router = fusion.fit_aspect_router([self.good, self.weak])
        self.assertEqual(sorted(router["colour"]["điểm"]), ["phobert-base-v2", "visobert"])
        self.assertEqual(router["colour"]["điểm"]["phobert-base-v2"]["f1_âm"], 1.0)
        self.assertEqual(router["colour"]["điểm"]["visobert"]["f1_âm"], 0.0)

    def test_khong_co_o_am_thi_accuracy_quyet_dinh(self):
        first = make_run(GOLDS, [{"colour": 1, "smell": 1, "price": 2} for _ in range(4)], PROBS,
                         name="first")
        first["meta"] = {"experiment": {"model": "a-model"}}
        second = make_run(GOLDS, [{"colour": 1, "smell": 1, "price": 1} for _ in range(4)], PROBS,
                          name="second")
        second["meta"] = {"experiment": {"model": "b-model"}}
        router = fusion.fit_aspect_router([first, second])
        # `price` không có ô âm nào -> xét accuracy: `second` đoán đúng -> thắng dù đứng SAU.
        self.assertEqual(router["price"]["model"], "b-model")
        self.assertIn("chuyển sang accuracy", router["price"]["lí_do"])

    def test_hoa_tuyet_doi_thi_chon_luot_dau_va_ghi_thu_tu(self):
        same_a = make_run(GOLDS, PREDS_BASE, PROBS, name="same-a")
        same_a["meta"] = {"experiment": {"model": "a-model"}}
        same_b = make_run(GOLDS, PREDS_BASE, PROBS, name="same-b")
        same_b["meta"] = {"experiment": {"model": "b-model"}}
        router = fusion.fit_aspect_router([same_a, same_b])
        self.assertEqual(router["colour"]["model"], "a-model")
        document = fusion.router_document([same_a, same_b], router)
        self.assertEqual(document["khoá"], "model")
        self.assertEqual(document["tiêu_chí"], "f1_âm")
        self.assertEqual(document["thứ_tự_hoà"], ["a-model", "b-model"])
        self.assertIn("khoá_luật", document["luật"])
        self.assertEqual(document["router"]["colour"]["model"], "a-model")

    def test_tieu_chi_accuracy_cho_router_khac_va_di_vao_tep_luat(self):
        """Đổi tiêu chí là đổi LỰA CHỌN, nên tiêu chí phải nằm trong tệp luật (chốt trước khi áp)."""
        first = make_run(GOLDS, [{"colour": 1, "smell": 1, "price": 2} for _ in range(4)], PROBS,
                         name="first-acc")
        first["meta"] = {"experiment": {"model": "a-model"}}
        second = make_run(GOLDS, [{"colour": 1, "smell": 1, "price": 1} for _ in range(4)], PROBS,
                          name="second-acc")
        second["meta"] = {"experiment": {"model": "b-model"}}
        router = fusion.fit_aspect_router([first, second], criterion="accuracy")
        # `price` không có ô âm nào -> cả hai tiêu chí đều xét accuracy -> `b-model` đoán đúng.
        self.assertEqual(router["price"]["model"], "b-model")
        self.assertIn("accuracy ô của khía cạnh", router["price"]["lí_do"])
        document = fusion.router_document([first, second], router, criterion="accuracy")
        self.assertEqual(document["tiêu_chí"], "accuracy")
        self.assertEqual(sorted(document["router"]["price"]["điểm"]), ["a-model", "b-model"])

    def test_tieu_chi_la_thi_bao_loi(self):
        with self.assertRaises(fusion.FusionError) as found:
            fusion.fit_aspect_router([self.good], criterion="macro_f1")
        self.assertIn("không có", str(found.exception))

    def test_chot_tren_test_thi_bao_loi(self):
        wrong = make_run(GOLDS, PREDS_BASE, PROBS, split="test", name="t")
        wrong["meta"] = {"experiment": {"model": "zz"}}
        with self.assertRaises(fusion.FusionError) as found:
            fusion.fit_aspect_router([wrong])
        self.assertIn("chỉ chốt được trên `val`", str(found.exception))

    def test_hai_luot_cung_model_la_loi(self):
        twin = make_run(GOLDS, PREDS_BASE, PROBS, name="twin")
        twin["meta"] = {"experiment": {"model": "phobert-base-v2"}}
        with self.assertRaises(fusion.FusionError) as found:
            fusion.fit_aspect_router([self.good, twin])
        self.assertIn("phobert-base-v2", str(found.exception))

    def test_ap_luat_thieu_model_thi_bao_loi_kem_ten_va_khia_canh(self):
        test_run = make_run(GOLDS, PREDS_BASE, PROBS, split="test", name="other")
        test_run["meta"] = {"experiment": {"model": "cafebert"}}
        with self.assertRaises(fusion.FusionError) as found:
            fusion.router_for([test_run], {"colour": "phobert-base-v2"})
        message = str(found.exception)
        self.assertIn("cafebert", message)
        self.assertIn("colour", message)

    def test_router_lay_nhan_theo_tung_khia_canh_va_giu_khung_o(self):
        base = make_run(GOLDS, PREDS_BASE, PROBS, split="test", name="base")
        base["meta"] = {"experiment": {"model": "a-model"}}
        other = make_run(GOLDS, [{"colour": 2 if index in (1, 3) else 1, "smell": 1, "price": 1}
                                 for index in range(4)], PROBS, split="test", name="other")
        other["meta"] = {"experiment": {"model": "b-model"}}
        choices = {aspect: str(other["dir"]) for aspect in other["aspects"]}
        preds, counts = fusion.router_predictions(base, [base, other], choices)
        self.assertEqual([pred["colour"] for pred in preds], [1, 2, 1, 2])
        self.assertEqual(counts["theo_khía_cạnh"]["colour"], 4)
        self.assertEqual(counts["thiếu_ô"], 0)
        self.assertEqual(counts["không_có_trong_luật"], [])
        # Khía cạnh không có trong luật thì GIỮ nhãn của lượt đầu và ĐẾM RIÊNG, không im lặng.
        _preds, counts2 = fusion.router_predictions(base, [base, other],
                                                    {"colour": str(other["dir"])})
        self.assertEqual(counts2["không_có_trong_luật"], ["price", "smell"])

    def test_members_report_giu_so_tung_luot(self):
        found = fusion.members_report([self.good, self.weak])
        self.assertEqual([item["lượt"] for item in found],
                         [utils.rel(self.good["dir"]), utils.rel(self.weak["dir"])])
        self.assertGreater(found[0]["f1_âm_macro"]["macro_trên_khía_cạnh_có_ô_âm"],
                           found[1]["f1_âm_macro"]["macro_trên_khía_cạnh_có_ô_âm"])

    def test_doc_tep_router_sai_dinh_dang_thi_bao_loi(self):
        root = Path(tempfile.mkdtemp(prefix="sentimentx-router-"))
        self.addCleanup(shutil.rmtree, str(root), ignore_errors=True)
        bad = root / "bad.json"
        bad.write_text(json.dumps({"khác": 1}), encoding="utf-8")
        with self.assertRaises(fusion.FusionError):
            fusion.load_router(bad)
        nameless = root / "nameless.json"
        nameless.write_text(json.dumps({"router": {"colour": {"lí_do": "x"}}}), encoding="utf-8")
        with self.assertRaises(fusion.FusionError) as found:
            fusion.load_router(nameless)
        self.assertIn("colour", str(found.exception))
        good = root / "ok.json"
        good.write_text(json.dumps({"router": {"colour": {"model": "visobert"}}}), encoding="utf-8")
        self.assertEqual(fusion.load_router(good), {"colour": "visobert"})


class TwoTierTest(unittest.TestCase):
    """Gộp HAI TẦNG: khung ô từ ENCODER, sắc thái từng khía cạnh từ lượt MỘT khía cạnh.

    Vì sao khoá ở đây: luật gộp phải chốt TRƯỚC khi chạy bảy lượt (mục 14.10), nên nhánh khó nhất -
    hai nguồn LỆCH nhau về "không nhắc tới" - phải kiểm được bằng test, không phải bằng trí nhớ.
    """

    LABELS = {0: "", 1: "positive", 2: "negative"}

    def single(self, aspect, codes, name="one", labels=None, sample_ids=None):
        run = make_run(GOLDS, [{} for _ in GOLDS], PROBS, split="test", name=name)
        run["aspects"] = [aspect]
        run["preds"] = [{aspect: code} for code in codes]
        run["labels"] = dict(self.LABELS if labels is None else labels)
        run["meta"] = {"experiment": {"model": name}}
        if sample_ids is not None:
            run["sample_ids"] = list(sample_ids)
            run["preds"] = run["preds"][:len(sample_ids)]
        return run

    def frame(self, per_aspect):
        """Lượt ENCODER giữ khung ô: `{khía cạnh: [mã cho từng review]}`."""
        run = make_run(GOLDS, PREDS_BASE, PROBS, split="test", name="encoder")
        run["aspects"] = sorted(per_aspect)
        run["preds"] = [{aspect: codes[index] for aspect, codes in per_aspect.items()}
                        for index in range(len(GOLDS))]
        run["labels"] = dict(self.LABELS)
        run["meta"] = {"experiment": {"model": "phobert-base-v2"}}
        return run

    def test_sac_thai_lay_tu_luot_mot_khia_canh(self):
        encoder = self.frame({"colour": [1, 1, 1, 1], "smell": [1, 1, 1, 1],
                              "price": [1, 1, 1, 1]})
        runs = [self.single("colour", [2, 2, 2, 2], name="colour-run"),
                self.single("smell", [1, 1, 1, 1], name="smell-run"),
                self.single("price", [1, 1, 1, 1], name="price-run")]
        preds, counts = fusion.merge_two_tier(encoder, runs)
        self.assertEqual([pred["colour"] for pred in preds], [2, 2, 2, 2])
        self.assertEqual(counts["từ_một_khía_cạnh"]["colour"], 4)
        self.assertEqual(counts["tổng_lệch"], 0)
        self.assertEqual(counts["thiếu_ô"], 0)

    def test_lech_ve_khong_nhac_toi_thi_giu_encoder(self):
        """Hai chiều lệch: encoder nói "có nhắc" mà lượt riêng nói "không" (và ngược lại)."""
        encoder = self.frame({"colour": [1, 0, 2, 1], "smell": [1, 1, 1, 1],
                              "price": [1, 1, 1, 1]})
        runs = [self.single("colour", [1, 2, 0, 1], name="colour-run"),
                self.single("smell", [1, 1, 1, 1], name="smell-run"),
                self.single("price", [1, 1, 1, 1], name="price-run")]
        preds, counts = fusion.merge_two_tier(encoder, runs)
        # Ô 1: encoder 0 / lượt riêng 2 -> giữ 0. Ô 2: encoder 2 / lượt riêng 0 -> giữ 2.
        self.assertEqual([pred["colour"] for pred in preds], [1, 0, 2, 1])
        self.assertEqual(counts["lệch_giữ_encoder"], {"colour": 2})
        self.assertEqual(counts["tổng_lệch"], 2)
        self.assertEqual(counts["từ_một_khía_cạnh"]["colour"], 2)

    def test_thieu_luot_cho_mot_khia_canh_thi_bao_loi(self):
        encoder = self.frame({"colour": [1, 1, 1, 1], "smell": [1, 1, 1, 1],
                              "price": [1, 1, 1, 1]})
        runs = [self.single("colour", [1, 1, 1, 1], name="colour-run")]
        with self.assertRaises(fusion.FusionError) as found:
            fusion.merge_two_tier(encoder, runs)
        message = str(found.exception)
        self.assertIn("price", message)
        self.assertIn("smell", message)

    def test_luot_nhieu_khia_canh_hoac_trung_khia_canh_la_loi(self):
        encoder = self.frame({"colour": [1, 1, 1, 1]})
        wide = make_run(GOLDS, PREDS_BASE, PROBS, split="test", name="wide")
        wide["labels"] = dict(self.LABELS)
        with self.assertRaises(fusion.FusionError) as found:
            fusion.merge_two_tier(encoder, [wide])
        self.assertIn("ĐÚNG MỘT khía cạnh", str(found.exception))
        twin_a = self.single("colour", [1, 1, 1, 1], name="a")
        twin_b = self.single("colour", [2, 2, 2, 2], name="b")
        with self.assertRaises(fusion.FusionError) as found:
            fusion.merge_two_tier(encoder, [twin_a, twin_b])
        self.assertIn("Hai lượt cùng khía cạnh", str(found.exception))

    def test_khac_khong_gian_nhan_la_loi(self):
        encoder = self.frame({"colour": [1, 1, 1, 1]})
        odd = self.single("colour", [1, 1, 1, 1], name="odd", labels={1: "positive", 2: "negative"})
        with self.assertRaises(fusion.FusionError) as found:
            fusion.merge_two_tier(encoder, [odd])
        self.assertIn("không nhắc tới", str(found.exception))

    def test_o_thieu_thi_giu_encoder_va_dem_rieng(self):
        encoder = self.frame({"colour": [1, 1, 1, 1]})
        partial = self.single("colour", [2, 2], name="partial", sample_ids=["0", "1"])
        preds, counts = fusion.merge_two_tier(encoder, [partial])
        self.assertEqual([pred["colour"] for pred in preds], [2, 2, 1, 1])
        self.assertEqual(counts["thiếu_ô"], 2)
        self.assertEqual(counts["từ_một_khía_cạnh"]["colour"], 2)


if __name__ == "__main__":
    unittest.main()

