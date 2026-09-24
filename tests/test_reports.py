# -*- coding: utf-8 -*-
"""Test sinh bảng tổng hợp (src/reports.py, scripts/collect_reports.py).

Điều quan trọng nhất được khoá ở đây:

1. Bảng tổng hợp ĐỌC LẠI file mà lượt chạy đã ghi (`run_meta.json`, `metrics.json`, `metrics.csv`),
   không tính lại từ dữ liệu gốc - nên con số trong bảng phải bằng đúng con số trong `metrics.csv`.
2. Cột đối chiếu công bố (`COT+0-shot`) phải cùng THANG ĐO với dự án: độ chính xác theo phần trăm,
   P/R/F1 theo tỉ lệ 0..1. Để nguyên thì hai cột cạnh nhau trong cùng một bảng là hai thang đo khác
   nhau, và người đọc sẽ đem 0.667 so với 97.06.
3. Nhóm chưa có dữ liệu vẫn phải sinh ra file, kèm dấu hiệu RỖNG: người đọc cần phân biệt "chưa
   chạy" với "chạy rồi mà không ra gì".

Chạy: python -m unittest discover -s tests
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from src import reports, utils

METRICS_COLUMNS = ["aspect", "sentiment", "metric", "value"]
METRICS_ROWS = [
    ["colour", "all", "accuracy", "75.0"],
    ["price", "all", "accuracy", "50.0"],
    ["colour", "positive", "precision", "0.5"],
    ["colour", "positive", "recall", "1.0"],
    ["colour", "positive", "f1", "0.667"],
]


def write_run(root, tag, experiment=None, status="FINISHED"):
    """Dựng một thư mục lượt chạy tối thiểu: đủ file mà báo cáo đọc."""
    directory = Path(root) / tag
    directory.mkdir(parents=True, exist_ok=True)
    utils.write_csv(METRICS_ROWS, METRICS_COLUMNS, directory / "metrics.csv")
    utils.write_json({
        "version": 1,
        "run": {"tag": tag, "status": status, "started": "2026-09-24 20:51:05"},
        "experiment": experiment or {"model": "model-x", "method": None, "exp_id": None},
        "data": {"dataset": "cosmetics", "version": "v0.1.0", "ma": "cosmetics-ma"},
        "repo": {"url": "https://example", "branch": "experiment", "sha": "a" * 40},
        "config": {"sha256": "b" * 64},
    }, directory / "run_meta.json")
    utils.write_json({
        "dataset": "cosmetics", "version_id": "cosmetics-ma", "split": "val",
        "prompt": "absa_cot_v1", "prompt_sha": "3abf6934",
        "model": "data/models/Qwen3-4B-Instruct-2507", "quant": "4bit", "max_length": 1280,
        "generation": {"max_new_tokens": 400, "do_sample": False},
        "subset": {"limit": 4, "seed": 42}, "n_samples": 4,
        "prompt_examples": {"sha": "c513f5a6"},
        "cost": {"giây": 12.5, "token sinh/giây": 17.7},
        "read_rate": {"% đọc được": 100.0},
        "resume": {"mode": "RESUME", "reused": 1, "new": 3},
        "scores": {"aggregate": {"accuracy_micro": 71.43,
                                 "exact_match": {"percent": 0.0}},
                   "prf": {"macro": {"f1": 0.667}},
                   "aspect_detection": {"micro": {"accuracy": 89.29}}},
    }, directory / "metrics.json")
    return directory


class ScanTest(unittest.TestCase):

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="sentimentx-reports-"))
        self.addCleanup(shutil.rmtree, str(self.root), ignore_errors=True)

    def test_tim_duoc_luot_chay_va_dat_nhan(self):
        write_run(self.root, "prompt-absa_cot_v1__val__n4__greedy",
                  experiment={"model": "model-x", "method": "prompt-cot", "exp_id": "exp001"})
        runs = reports.scan_runs([self.root])
        self.assertEqual(len(runs), 1)
        self.assertEqual(reports.canonical_label(runs[0]), "model-x/prompt-cot/exp001")
        self.assertEqual(reports.column_label(runs[0]), "exp001")

    def test_chay_ngoai_thi_nghiem_thi_nhan_la_ten_thu_muc(self):
        write_run(self.root, "prompt-absa_cot_v1__val__n4__greedy")
        runs = reports.scan_runs([self.root])
        self.assertEqual(reports.canonical_label(runs[0]), "prompt-absa_cot_v1__val__n4__greedy")
        self.assertEqual(reports.column_label(runs[0]), "absa_cot_v1 n4")

    def test_thu_muc_khong_co_run_meta_thi_bo_qua(self):
        (self.root / "khong-phai-luot-chay").mkdir()
        self.assertEqual(reports.scan_runs([self.root]), [])


class TableTest(unittest.TestCase):

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="sentimentx-reports-"))
        self.addCleanup(shutil.rmtree, str(self.root), ignore_errors=True)
        write_run(self.root, "exp001",
                  experiment={"model": "model-x", "method": "prompt-cot", "exp_id": "exp001"})
        self.runs = reports.scan_runs([self.root])

    def test_so_trong_bang_bang_so_trong_metrics_csv(self):
        mapping = reports.metric_map(self.runs[0])
        self.assertEqual(mapping[("colour", "all", "accuracy")], 75.0)
        self.assertEqual(mapping[("colour", "positive", "f1")], 0.667)
        columns, rows = reports.accuracy_table(self.runs)
        self.assertEqual(columns, ["aspect", "exp001"])
        self.assertEqual(rows, [{"aspect": "colour", "exp001": 75.0},
                                {"aspect": "price", "exp001": 50.0}])

    def test_cot_cong_bo_duoc_them_va_dung_thang_do(self):
        reference = {"colour": 94.12, "aspect_detection": 100.0}
        columns, rows = reports.accuracy_table(self.runs, reference, "COT+0-shot")
        self.assertEqual(columns, ["aspect", "exp001", "COT+0-shot"])
        self.assertEqual(rows[0], {"aspect": "colour", "exp001": 75.0, "COT+0-shot": 94.12})
        # Dòng `Aspect` của công bố điền bằng bộ chấm `aspect_detection` của lượt chạy, ở CUỐI bảng.
        self.assertEqual(rows[-1]["aspect"], "aspect_detection")
        self.assertEqual(rows[-1]["exp001"], 89.29)

    def test_bang_prf_co_ba_cot_moi_luot_chay(self):
        columns, rows = reports.prf_table(self.runs)
        self.assertEqual(columns, ["aspect", "sentiment", "exp001 P", "exp001 R", "exp001 F1"])
        self.assertEqual(rows[0]["sentiment"], "positive")
        self.assertEqual(rows[0]["exp001 F1"], 0.667)

    def test_khia_canh_chi_co_trong_bang_cong_bo_van_thanh_mot_dong(self):
        columns, rows = reports.accuracy_table(self.runs, {"smell": 90.0}, "COT+0-shot")
        self.assertEqual(columns, ["aspect", "exp001", "COT+0-shot"])
        smell = [row for row in rows if row["aspect"] == "smell"]
        self.assertEqual(len(smell), 1)
        self.assertEqual(smell[0]["COT+0-shot"], 90.0)
        self.assertEqual(smell[0]["exp001"], "")


class ReferenceTest(unittest.TestCase):
    """Đọc bảng công bố: chọn đúng cột theo số ví dụ, và đổi về cùng thang đo."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="sentimentx-reference-"))
        self.addCleanup(shutil.rmtree, str(self.root), ignore_errors=True)
        (self.root / "accuracy_by_aspect.csv").write_text(
            "Aspect,COT+0-shot,COT+1-shot\nPrice,94.59,96.15\nTexture,97.22,100\n"
            "Aspect,100,98.89\n", encoding="utf-8")
        (self.root / "prf_by_aspect_sentiment_0shot.csv").write_text(
            "Aspect,Sentiment,Precision,Recall,F1\nSMELL,positive,97.06,97.06,97.06\n",
            encoding="utf-8")

    def test_chon_cot_theo_so_vi_du(self):
        accuracy, _prf, suffix = reports.load_reference(self.root, shot=0)
        self.assertEqual(accuracy["price"], 94.59)
        self.assertEqual(accuracy["aspect_detection"], 100.0)
        self.assertEqual(suffix, "COT+0-shot")
        accuracy, _prf, suffix = reports.load_reference(self.root, shot=1)
        self.assertEqual(accuracy["price"], 96.15)
        self.assertEqual(suffix, "COT+1-shot")

    def test_ten_khia_canh_duoc_dua_ve_chu_thuong(self):
        _accuracy, prf, _suffix = reports.load_reference(self.root, shot=0)
        self.assertIn(("smell", "positive"), prf)

    def test_p_r_f1_cua_cong_bo_dua_ve_ti_le(self):
        _accuracy, prf, _suffix = reports.load_reference(self.root, shot=0)
        cell = prf[("smell", "positive")]
        self.assertEqual(cell["precision"], 0.9706)
        self.assertEqual(cell["f1"], 0.9706)

    def test_thieu_file_thi_khong_co_cot_doi_chieu(self):
        empty = Path(tempfile.mkdtemp(prefix="sentimentx-reference-empty-"))
        self.addCleanup(shutil.rmtree, str(empty), ignore_errors=True)
        self.assertEqual(reports.load_reference(empty), (None, None, None))


class WriteTest(unittest.TestCase):

    def setUp(self):
        self.out = Path(tempfile.mkdtemp(prefix="sentimentx-reports-out-"))
        self.addCleanup(shutil.rmtree, str(self.out), ignore_errors=True)
        self.source = Path(tempfile.mkdtemp(prefix="sentimentx-reports-in-"))
        self.addCleanup(shutil.rmtree, str(self.source), ignore_errors=True)

    def test_moi_nhom_ghi_ba_dinh_dang(self):
        write_run(self.source, "exp001",
                  experiment={"model": "model-x", "method": "prompt-cot", "exp_id": "exp001"})
        result = reports.build(roots=[self.source], out_root=self.out)
        self.assertEqual(sorted(result), sorted(reports.GROUPS))
        for name, item in result.items():
            with self.subTest(group=name):
                self.assertTrue(item["html"].is_file())
                self.assertTrue(item["md"].is_file())
                for path in item["csv"].values():
                    self.assertTrue(Path(path).is_file())
                self.assertIn("```mermaid", item["md"].read_text(encoding="utf-8"))

    def test_nhom_rong_van_ghi_va_bao_rong(self):
        result = reports.build(roots=[self.source], out_root=self.out, groups=["model_input"])
        self.assertEqual(result["model_input"]["rows"], 0)
        self.assertIn(reports.GREETING.upper(),
                      result["model_input"]["html"].read_text(encoding="utf-8"))

    def test_khong_ghi_de_lan_nhau_giua_cac_nhom(self):
        write_run(self.source, "exp001",
                  experiment={"model": "model-x", "method": "prompt-cot", "exp_id": "exp001"})
        result = reports.build(roots=[self.source], out_root=self.out)
        folders = {path.parent.name for item in result.values() for path in item["csv"].values()}
        self.assertEqual(folders, set(reports.GROUPS))

    def test_nhom_khong_ton_tai_thi_bao_loi(self):
        with self.assertRaises(reports.ReportError):
            reports.group_tables("khong-co-nhom-nay", [])

    def test_so_do_mermaid_thay_dau_nhay_kep(self):
        text = reports.mermaid_graph([('a"b', "", "c")])
        self.assertIn("[\"a'b\"]", text)
        self.assertIn("-->", text)

    def test_html_escape_noi_dung(self):
        page = reports.html_page("nhom", {"x.csv": (["a"], [{"a": "<script>"}])})
        self.assertIn("&lt;script&gt;", page)
        self.assertNotIn("<script>", page)


if __name__ == "__main__":
    unittest.main()


