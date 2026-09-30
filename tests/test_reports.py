# -*- coding: utf-8 -*-
"""Test sinh bảng tổng hợp (src/reporting/reports.py, scripts/collect_reports.py).

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

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.core import paths, utils
from src.reporting import reports

METRICS_COLUMNS = ["aspect", "sentiment", "metric", "value"]
METRICS_ROWS = [
    ["colour", "all", "accuracy", "75.0"],
    ["price", "all", "accuracy", "50.0"],
    ["colour", "positive", "precision", "0.5"],
    ["colour", "positive", "recall", "1.0"],
    ["colour", "positive", "f1", "0.667"],
]


def write_run(root, tag, experiment=None, status="FINISHED", prompt="absa_cot_v1", examples=None):
    """Dựng một thư mục lượt chạy tối thiểu: đủ file mà báo cáo đọc.

    `examples`: số ví dụ few-shot đã dùng. Có giá trị thì báo cáo chọn cột công bố THEO MỨC VÍ DỤ của
    lượt đó (`reports.shot_of`), nên fixture phải ghi được nó để khoá hành vi này lại.
    """
    directory = Path(root) / tag
    directory.mkdir(parents=True, exist_ok=True)
    utils.write_csv(METRICS_ROWS, METRICS_COLUMNS, directory / "metrics.csv")
    prompt_examples = {"sha": "c513f5a6"}
    if examples is not None:
        prompt_examples["examples"] = examples
    utils.write_json({
        "version": 1,
        "run": {"hash": "1a2b3c4d", "status": status, "started": "2026-09-24 20:51:05"},
        "experiment": experiment or {"model": "model-x", "method": None, "exp_id": None},
        "data": {"dataset": "cosmetics", "version": "v0.1.0", "build": "cosmetics-ma"},
        "repo": {"url": "https://example", "branch": "experiment", "sha": "a" * 40},
        "config": {"sha256": "b" * 64},
    }, directory / "run_meta.json")
    utils.write_json({
        "dataset": "cosmetics", "version_id": "cosmetics-ma", "split": "val",
        "prompt": prompt, "prompt_sha": "3abf6934",
        "model": "data/models/Qwen3-4B-Instruct-2507", "quant": "4bit", "max_length": 1280,
        "generation": {"max_new_tokens": 400, "do_sample": False},
        "subset": {"limit": 4, "seed": 42}, "n_samples": 4,
        "prompt_examples": prompt_examples,
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
        # Nhãn = <model>/<method>/<expNNN>:<hash8>: tên thư mục chỉ là mã băm nên nhãn phải nói
        # được lượt chạy thuộc thí nghiệm nào VÀ là lượt nào trong thí nghiệm đó.
        self.assertEqual(reports.canonical_label(runs[0]), "model-x/prompt-cot/exp001:1a2b3c4d")
        self.assertEqual(reports.column_label(runs[0]), "exp001")

    def test_moi_luot_chay_deu_thuoc_mot_thi_nghiem(self):
        """Không còn lượt chạy "ngoài thí nghiệm": nhãn lấy mã băm trong `run_meta.json`."""
        write_run(self.root, "1a2b3c4d", experiment={})
        runs = reports.scan_runs([self.root])
        self.assertEqual(reports.canonical_label(runs[0]), "1a2b3c4d")

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


class ColumnLabelTest(unittest.TestCase):
    """Nhãn cột phải KHÔNG TRÙNG NHAU.

    Đây là lỗi thật đã gặp: hai thí nghiệm khác model nhưng cùng số `expNNN` (chuyện bình thường khi
    so Qwen với PhoBERT) cho ra hai cột cùng tên, và vì bảng dựng theo từ điển nhãn -> cột, lượt
    chạy thứ hai GHI ĐÈ lượt thứ nhất, không báo gì.
    """

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="sentimentx-columns-"))
        self.addCleanup(shutil.rmtree, str(self.root), ignore_errors=True)

    def _labels(self, runs):
        return reports.column_labels(runs)

    def test_hai_model_cung_so_thi_them_ten_model(self):
        write_run(self.root, "run-a",
                  experiment={"model": "qwen3-4b-instruct-2507", "method": "prompt-cot",
                              "exp_id": "exp001"})
        write_run(self.root, "run-b",
                  experiment={"model": "phobert-base", "method": "prompt-cot",
                              "exp_id": "exp001"})
        runs = reports.scan_runs([self.root])
        self.assertEqual(self._labels(runs),
                         ["qwen3-4b-instruct-2507 exp001", "phobert-base exp001"])

    def test_cung_ten_thi_them_so_thu_tu(self):
        write_run(self.root, "run-a")
        write_run(self.root, "run-b")
        runs = reports.scan_runs([self.root])
        self.assertEqual(self._labels(runs), ["absa_cot_v1 n4", "absa_cot_v1 n4 #2"])

    def test_khong_trung_khi_chi_co_mot_luot_chay(self):
        write_run(self.root, "run-a")
        runs = reports.scan_runs([self.root])
        self.assertEqual(self._labels(runs), ["absa_cot_v1 n4"])

    def test_cot_trong_bang_accuracy_khong_trung_va_khong_mat_du_lieu(self):
        write_run(self.root, "run-a",
                  experiment={"model": "qwen3-4b-instruct-2507", "method": "prompt-cot",
                              "exp_id": "exp001"})
        write_run(self.root, "run-b",
                  experiment={"model": "phobert-base", "method": "prompt-cot",
                              "exp_id": "exp001"})
        runs = reports.scan_runs([self.root])
        columns, rows = reports.accuracy_table(runs)
        self.assertEqual(len(columns), len(set(columns)), columns)
        colour = [row for row in rows if row["aspect"] == "colour"][0]
        # Hai cột, hai giá trị riêng: không cột nào bị nuốt.
        self.assertEqual(colour["qwen3-4b-instruct-2507 exp001"], 75.0)
        self.assertEqual(colour["phobert-base exp001"], 75.0)
        self.assertEqual(len([key for key in colour if key != "aspect"]), 2)


class ModelInputTest(unittest.TestCase):
    """Số đo input của model phải vào được bảng tổng hợp.

    Khoá cả TÊN FILE: `run_token_stats.py` ghi file theo mẫu tên trong `configs/paths.yaml`, còn
    bảng tổng hợp đi tìm theo đúng mẫu đó. Hai bên lệch tên thì báo cáo vẫn sinh ra bình thường,
    chỉ là rỗng mãi - không có gì báo lỗi.
    """

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="sentimentx-model-input-"))
        self.addCleanup(shutil.rmtree, str(self.root), ignore_errors=True)
        patcher = mock.patch.object(reports.paths, "report", return_value=self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_doc_duoc_file_so_do_cua_run_token_stats(self):
        from src.preprocessing import token_stats

        version = "cosmetics-ds0.1.0"
        (self.root / version).mkdir(parents=True)
        row = [str(index) for index, _name in enumerate(token_stats.COLUMNS)]
        utils.write_csv([row], list(token_stats.COLUMNS),
                        self.root / version / token_stats.file_name("prompt-absa_cot_v1"))
        rows, columns = reports.model_input_rows()
        self.assertEqual(len(rows), 1)
        self.assertIn("file", columns)
        self.assertIn(version, rows[0]["file"])

    def test_chua_do_thi_bang_rong_va_noi_ro(self):
        rows, columns = reports.model_input_rows()
        self.assertEqual(rows, [])
        self.assertEqual(columns, [reports.EMPTY_TABLE_COLUMN])

    def test_bang_gom_cua_chinh_nhom_khong_duoc_doc_lai(self):
        """Bảng gom là ĐẦU RA: đọc lại nó thì mỗi lần sinh báo cáo lại thêm một bộ cột trùng tên."""
        aggregate = self.root / Path(reports.paths.pattern("model_input")).name
        utils.write_csv([["1", "x"]], ["model", "file"], aggregate)
        rows, columns = reports.model_input_rows()
        self.assertEqual(rows, [])
        self.assertEqual(columns, [reports.EMPTY_TABLE_COLUMN])


class WriteTest(unittest.TestCase):

    def setUp(self):
        self.out = Path(tempfile.mkdtemp(prefix="sentimentx-reports-out-"))
        self.addCleanup(shutil.rmtree, str(self.out), ignore_errors=True)
        self.source = Path(tempfile.mkdtemp(prefix="sentimentx-reports-in-"))
        self.addCleanup(shutil.rmtree, str(self.source), ignore_errors=True)
        # Nhóm `model_input` đọc CHÍNH thư mục report của dự án (nó là bảng tổng hợp của cả dự án,
        # không theo `roots` như các nhóm theo lượt chạy), nên phải trỏ nó vào thư mục tạm. Không
        # thì kết quả test phụ thuộc dữ liệu đang có trên máy: đo token một lần là bảng hết rỗng và
        # test đỏ dù code không đổi.
        patcher = mock.patch.object(reports.paths, "report", return_value=self.source / "reports")
        patcher.start()
        self.addCleanup(patcher.stop)

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
        self.assertIn(reports.NO_DATA.upper(),
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


class TestTwoReportSets(unittest.TestCase):
    """HAI BỘ BẢNG: `attempt_registry` liệt kê MỌI lần thử, bảng số chỉ lượt THÀNH CÔNG.

    Vì sao cần tách: lượt hỏng không có `metrics.json`, nên mọi ô số của nó đều trống - đưa vào bảng để
    so là làm nhiễu đúng bảng dùng để đọc kết quả (đã gặp thật: bảng hiện 4 dòng PhoBERT, 3 dòng rỗng).
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.out = self.root / "out"
        write_run(self.root, "a1", experiment={"model": "model-x", "method": "lora", "exp_id": "exp001"},
                  status="FINISHED")
        write_run(self.root, "b2", experiment={"model": "model-x", "method": "lora", "exp_id": "exp002"},
                  status="FAILED")
        utils.write_json({"errors": [{"message": "ImportError: Found an incompatible version of torchao"}]},
                         self.root / "b2" / "errors.json")
        self.runs = reports.scan_runs([self.root])

    def test_the_attempt_registry_lists_every_attempt_with_the_reason(self):
        """Nhóm `attempt_registry` là bản tổng hợp TOÀN BỘ: hai lượt, kèm trạng thái và LÝ DO DỪNG."""
        rows = reports.attempt_rows(self.runs)
        self.assertEqual(len(rows), 2)
        self.assertEqual(sorted(row["status"] for row in rows), ["FAILED", "FINISHED"])
        failed = [row for row in rows if row["status"] == "FAILED"][0]
        self.assertIn("torchao", failed["reason"])

    def test_number_tables_hold_only_finished_runs(self):
        """Mặc định bảng SỐ chỉ có lượt `FINISHED`; `--only all` mới liệt kê cả lượt hỏng."""
        built = reports.build(roots=[self.root], groups=["metrics_matrix", "attempt_registry"],
                              out_root=self.out)
        matrix = (self.out / "metrics_matrix" / "accuracy_by_aspect.csv").read_text(encoding="utf-8")
        self.assertIn("exp001", matrix)
        self.assertNotIn("exp002", matrix)

        every = reports.build(roots=[self.root], groups=["metrics_matrix"], out_root=self.out,
                              only="all")
        self.assertTrue(every)
        matrix_all = (self.out / "metrics_matrix" / "accuracy_by_aspect.csv").read_text(encoding="utf-8")
        self.assertIn("exp002", matrix_all)
        self.assertTrue(built)

    def test_the_new_group_is_declared_and_writable(self):
        """Nhóm mới phải có trong `GROUPS` và có thư mục report trong `configs/paths.yaml`."""
        self.assertIn("attempt_registry", reports.GROUPS)
        self.assertEqual(reports.CSV_NAME["attempt_registry"], "attempt_registry.csv")
        self.assertEqual(paths.report("attempt_registry").name, "attempt_registry")


class TestRunValidity(unittest.TestCase):
    """Hai cột `valid` và `comparable`: lượt chạy này có dùng được trong bảng so hay không.

    Vì sao cần: một lượt có thể được chấm bằng commit CHƯA merge vào nhánh đã ghim, hoặc bằng một cơ sở
    đo khác (dữ liệu, không gian nhãn, split, bộ chấm). Đọc thì vẫn ra số, nhưng con số đó không tái lập
    được từ bản code đã công bố - bảng phải nói ra chứ không để người đọc tự phát hiện.
    """

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="sentimentx-validity-"))
        self.addCleanup(shutil.rmtree, str(self.root), ignore_errors=True)

    def make_run(self, tag="a1", task=None, experiment=None):
        directory = write_run(self.root, tag, experiment=experiment or {
            "model": "model-x", "method": "lora", "exp_id": "exp001"})
        if task is not None:
            meta = json.loads((directory / "run_meta.json").read_text(encoding="utf-8"))
            meta["task"] = task
            utils.write_json(meta, directory / "run_meta.json")
        return reports.scan_runs([self.root])[-1]

    def test_commit_on_the_pinned_branch_is_valid(self):
        with mock.patch.object(reports.repo_module, "ref_exists", return_value=True), \
                mock.patch.object(reports.repo_module, "is_ancestor", return_value=True):
            row = reports.experiment_rows([self.make_run()])[0]
        self.assertEqual(row["valid"], reports.VALID_YES)
        self.assertEqual(row["invalid_reason"], "")

    def test_commit_outside_the_branch_is_flagged_with_the_reason(self):
        with mock.patch.object(reports.repo_module, "ref_exists", return_value=True), \
                mock.patch.object(reports.repo_module, "is_ancestor", return_value=False):
            row = reports.experiment_rows([self.make_run()])[0]
        self.assertEqual(row["valid"], reports.VALID_NO)
        self.assertIn("không nằm trên", row["invalid_reason"])

    def test_a_machine_without_git_is_unknown_not_invalid(self):
        """"Chưa kiểm được" không được ghi thành "không hợp lệ" - đó là nói dối kiểu khác."""
        with mock.patch.object(reports.repo_module, "ref_exists",
                               side_effect=reports.repo_module.RepoError("Máy này không có `git`.")):
            row = reports.experiment_rows([self.make_run()])[0]
        self.assertEqual(row["valid"], reports.VALID_UNKNOWN)
        self.assertIn("git", row["invalid_reason"])

    def test_missing_remote_ref_falls_back_to_the_local_branch(self):
        """Máy chỉ có nhánh nội bộ (chưa fetch) vẫn kiểm được, thay vì báo "chưa rõ"."""
        with mock.patch.object(reports.repo_module, "ref_exists",
                               side_effect=lambda ref: ref == "experiment"), \
                mock.patch.object(reports.repo_module, "is_ancestor", return_value=True):
            row = reports.experiment_rows([self.make_run()])[0]
        self.assertEqual(row["valid"], reports.VALID_YES)

    def test_git_is_asked_once_for_the_same_commit(self):
        """Nhiều lượt cùng một commit: hỏi git một lần, không gọi lại cho từng dòng."""
        asked = []
        with mock.patch.object(reports.repo_module, "ref_exists", return_value=True), \
                mock.patch.object(reports.repo_module, "is_ancestor",
                                  side_effect=lambda sha, ref: asked.append(sha) or True):
            reports.experiment_rows([self.make_run("a1"), self.make_run("b2")])
        self.assertEqual(len(asked), 1)

    def test_a_different_measurement_basis_is_not_comparable(self):
        """Hai lượt khác không gian nhãn thì không so được: lệch vì ĐO KHÁC, không phải vì model khác."""
        first = self.make_run("a1", task={"label_space": "binary", "neutral_policy": "drop"})
        second = self.make_run("b2", task={"label_space": "full", "neutral_policy": "drop"})
        with mock.patch.object(reports.repo_module, "ref_exists", return_value=True), \
                mock.patch.object(reports.repo_module, "is_ancestor", return_value=True):
            rows = reports.experiment_rows([first, second])
        self.assertEqual(rows[0]["comparable"], reports.VALID_YES)
        self.assertEqual(rows[1]["comparable"], reports.VALID_NO)
        self.assertIn("khác cơ sở đo", rows[1]["invalid_reason"])
        self.assertIn("full so với binary", rows[1]["invalid_reason"])

    def test_the_three_columns_are_in_the_registry_table(self):
        for column in ("valid", "comparable", "invalid_reason"):
            self.assertIn(column, reports.REGISTRY_COLUMNS)


class TestDatasetRegistry(unittest.TestCase):
    """Dòng dõi dataset: phiên bản này sinh từ phiên bản dataset nào.

    `docs/05_config/03_datasets.md` khai `parent` là "phiên bản trước đó, dùng để dựng lại changelog", và
    `docs/01_dataset/changelog.md` là chỗ người đọc tra. Bảng thiếu cột này thì không biết bản đang dùng
    kế thừa từ đâu - hoặc tệ hơn, để ô trống và người đọc hiểu là "chưa biết".
    """

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="sentimentx-dataset-"))
        self.addCleanup(shutil.rmtree, str(self.root), ignore_errors=True)

    def rows(self, config):
        with mock.patch.object(reports.dataset_module, "available", return_value=["cosmetics"]), \
                mock.patch.object(reports.dataset_module, "versions", return_value=["v0.2.0"]), \
                mock.patch.object(reports.dataset_module, "load_config", return_value=config), \
                mock.patch.object(reports.dataset_module, "config_path",
                                  return_value=Path("configs/datasets/cosmetics/v0.2.0.yaml")), \
                mock.patch.object(reports.versioning, "compute_id", return_value="ma-gia"), \
                mock.patch.object(reports.versioning, "processed_dir",
                                  return_value=Path(self.root) / "khong-co"):
            return reports.dataset_rows()

    def test_a_version_without_a_parent_says_it_comes_from_the_raw_data(self):
        row = self.rows({"name": "cosmetics", "sources": []})[0]
        self.assertEqual(row["parent"], reports.FROM_RAW)
        self.assertIn("gốc", row["parent"])

    def test_a_version_with_a_parent_shows_the_parent_id(self):
        config = {"name": "cosmetics", "parent": "cosmetics-ds0.1.0-abc12345", "sources": []}
        self.assertEqual(self.rows(config)[0]["parent"], "cosmetics-ds0.1.0-abc12345")

    def test_the_column_exists_even_when_no_version_is_on_disk(self):
        """Bảng rỗng vẫn phải khai cột `parent`, nếu không người đọc không biết bảng có cột đó."""
        with mock.patch.object(reports.dataset_module, "available", return_value=[]):
            tables, _mermaid = reports.group_tables("dataset_registry", [])
        self.assertIn("parent", tables["dataset_registry.csv"][0])


class TestRowCount(unittest.TestCase):
    """Số BẢN GHI, không phải số dòng: ô văn bản của review có thể chứa xuống dòng.

    Lỗi thật, bắt được khi chạy `collect_reports.py`: `dataset_registry` báo `test=2271` trong khi
    `eval_lock.json` ghi 1.518 bản ghi, vì bảng đếm dòng vật lý. Con số trông vẫn hợp lý (không ai ngờ
    một file CSV lại có ô nhiều dòng) nên nó sống rất lâu - đúng loại lỗi test này khoá lại.
    """

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="sentimentx-rowcount-"))
        self.addCleanup(shutil.rmtree, str(self.root), ignore_errors=True)

    def test_a_record_with_a_newline_inside_counts_once(self):
        path = self.root / "co-xuong-dong.csv"
        path.write_text('text,label\n"hai\ndong",positive\nmot,negative\n', encoding="utf-8")
        self.assertEqual(reports._row_count(path), 2)
        # Con số mà cách đếm dòng cho ra, ghi lại để thấy vì sao phải dùng `csv.reader`.
        self.assertEqual(len(path.read_text(encoding="utf-8").splitlines()), 4)

    def test_the_count_matches_eval_lock_where_the_data_is_on_disk(self):
        """Đối chiếu với khoá tập đánh giá: đây chính là phép so bắt được lỗi đếm dòng."""
        checked = 0
        for directory in sorted(Path(paths.data_root(), "processed").glob("*")):
            lock = directory / "eval_lock.json"
            if not lock.is_file():
                continue
            for name, item in json.loads(lock.read_text(encoding="utf-8")).items():
                path = directory / item.get("file", "")
                if path.is_file() and item.get("rows"):
                    self.assertEqual(reports._row_count(path), item["rows"], name)
                    checked += 1
        if not checked:
            self.skipTest("máy này chưa có dữ liệu đã xử lý (dữ liệu không nằm trong git)")


class MetricsMatrixShotTest(unittest.TestCase):
    """Bảng `metrics_matrix` phải so mỗi lượt với ĐÚNG cột công bố của mức ví dụ của nó.

    Lỗi đã có trước 27/09/2026: `--reference-shot` mặc định 0 nên lượt 0 ví dụ, 1 ví dụ và 5 ví dụ đều
    bị đem so với cột `COT+0-shot` - so sai mà bảng vẫn trông hợp lý.
    """

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="sentimentx-shot-"))
        self.addCleanup(shutil.rmtree, str(self.root), ignore_errors=True)
        write_run(self.root, "exp002", examples=0,
                  experiment={"model": "model-x", "method": "prompt-cot", "exp_id": "exp002"})
        write_run(self.root, "exp004", examples=5,
                  experiment={"model": "model-x", "method": "prompt-cot", "exp_id": "exp004"})
        self.runs = reports.scan_runs([self.root])

    def test_shot_of_reads_the_example_count(self):
        self.assertEqual([reports.shot_of(run) for run in self.runs], [0, 5])

    def test_shot_of_falls_back_to_the_prompt_name(self):
        self.assertEqual(reports.shot_of({"metrics": {"prompt": "absa_cot_1shot_v1"}}), 1)
        self.assertEqual(reports.shot_of({"metrics": {"prompt": "absa_cot_zeroshot_v1"}}), 0)
        # Prompt 2 ví dụ không phải một mức của công bố, và lượt của model encoder không có ví dụ nào.
        self.assertIsNone(reports.shot_of({"metrics": {"prompt": "absa_cot_v1"}}))
        self.assertIsNone(reports.shot_of({"metrics": {}}))

    def test_each_shot_level_gets_its_own_reference_column(self):
        tables, _mermaid = reports.group_tables("metrics_matrix", self.runs,
                                               reports.load_reference(shot=0))
        columns, rows = tables["accuracy_by_aspect.csv"]
        for name in ("exp002", "exp004", "COT+0-shot", "COT+5-shot"):
            self.assertIn(name, columns)
        colour = [row for row in rows if row["aspect"] == "colour"][0]
        self.assertEqual(colour["COT+0-shot"], reports.load_reference(shot=0)[0]["colour"])
        self.assertEqual(colour["COT+5-shot"], reports.load_reference(shot=5)[0]["colour"])
        self.assertEqual(colour["exp002"], 75.0)
        self.assertEqual(colour["exp004"], 75.0)
        # Dòng `aspect_detection` của công bố vẫn ở CUỐI bảng sau khi ghép hai nhóm mức ví dụ.
        self.assertEqual(rows[-1]["aspect"], "aspect_detection")

    def test_no_run_still_shows_the_reference_rows(self):
        """Bảng rỗng vẫn hiện mốc công bố, để người đọc thấy đích cần vượt."""
        tables, _mermaid = reports.group_tables("metrics_matrix", [],
                                               reports.load_reference(shot=0))
        columns, rows = tables["accuracy_by_aspect.csv"]
        self.assertEqual(columns, ["aspect", "COT+0-shot"])
        self.assertTrue(rows)


if __name__ == "__main__":
    unittest.main()


