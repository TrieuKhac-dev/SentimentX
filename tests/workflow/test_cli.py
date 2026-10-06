# -*- coding: utf-8 -*-
"""Test tham số dòng lệnh của các tool và `versioning.find_version`.

VÌ SAO CẦN
Cú pháp dòng lệnh là hợp đồng với người chạy (và với ghi chú mà notebook in ra trên Colab). Hai lỗi
ở đây đều im lặng: nhầm mã phiên bản dữ liệu với nhãn raw_version, hoặc để tool tự chọn "bản mới
nhất" - cả hai dẫn tới đo/kiểm một phiên bản khác với điều người chạy tưởng. Test này khoá lại câu
lỗi và mã thoát cho từng dạng sai.

Chạy: python -m unittest discover -s tests
"""

import importlib.util
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

import run_check_examples
import run_eda
import run_pipeline
import run_token_stats
from src.core import paths, versioning

HASH8 = "e0ccc484"
FULL_ID = "cosmetics-ds0.1.0-pl0.1.0-srccosmetics@0.1.0-" + HASH8

# `scripts/` không phải package, nên tool trong đó phải nạp bằng đường dẫn (như tests/workflow/test_pin.py).
SPEC = importlib.util.spec_from_file_location(
    "reset_experiment", paths.root() / "scripts" / "reset_experiment.py")
reset_experiment = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reset_experiment)

# Cùng cách đó cho `scripts/collect_reports.py` (kiểm cờ `--exclude`).
COLLECT_SPEC = importlib.util.spec_from_file_location(
    "collect_reports", paths.root() / "scripts" / "collect_reports.py")
collect_reports = importlib.util.module_from_spec(COLLECT_SPEC)
COLLECT_SPEC.loader.exec_module(collect_reports)

# Cùng cách đó cho `scripts/fit_thresholds.py` (hai chế độ: DÒ trên `val` và ÁP bảng đã chốt).
FIT_SPEC = importlib.util.spec_from_file_location(
    "fit_thresholds", paths.root() / "scripts" / "fit_thresholds.py")
fit_thresholds = importlib.util.module_from_spec(FIT_SPEC)
FIT_SPEC.loader.exec_module(fit_thresholds)


class RunEdaArgsTest(unittest.TestCase):
    """`run_eda.py`: bắt buộc chọn đúng MỘT nơi đo, và không nhận lẫn nhãn."""

    def mistake(self, argv):
        return run_eda.check_args(run_eda.parse_args(argv))

    def test_raw_needs_name_and_version(self):
        self.assertIsNone(self.mistake(["--on", "raw", "--name", "cosmetics",
                                        "--version", "v0.1.0"]))

    def test_dataset_needs_hash(self):
        self.assertIsNone(self.mistake(["--on", "dataset", "--hash", HASH8]))

    def test_missing_on_is_refused(self):
        self.assertIn("--on", self.mistake([]))
        self.assertIn("--on", self.mistake(["--name", "cosmetics", "--version", "v0.1.0"]))

    def test_raw_without_name_or_version_is_refused(self):
        message = self.mistake(["--on", "raw", "--name", "cosmetics"])
        self.assertIn("--name", message)
        self.assertIn("--version", message)

    def test_edition_id_passed_as_raw_version_is_diagnosed(self):
        message = self.mistake(["--on", "raw", "--name", "cosmetics", "--version", FULL_ID])
        self.assertIn("MÃ PHIÊN BẢN", message)
        self.assertIn("--on dataset --hash", message)

    def test_hash_with_raw_is_refused(self):
        self.assertIn("--hash", self.mistake(["--on", "raw", "--hash", HASH8]))

    def test_version_with_dataset_is_refused(self):
        message = self.mistake(["--on", "dataset", "--version", "v0.1.0"])
        self.assertIn("không dùng `--version`", message)

    def test_dataset_without_hash_is_refused(self):
        self.assertIn("--hash", self.mistake(["--on", "dataset"]))

    def test_removed_flag_dataset_is_rejected_by_argparse(self):
        with self.assertRaises(SystemExit), redirect_stdout(io.StringIO()), \
                redirect_stderr(io.StringIO()):
            run_eda.parse_args(["--dataset", "cosmetics", "--raw-version", "v0.1.0"])


class RunPipelineArgsTest(unittest.TestCase):
    """`run_pipeline.py`: `--name` và `--version` (file cấu hình dataset) đều bắt buộc."""

    def test_both_flags_are_required(self):
        for argv in ([], ["--name", "cosmetics"], ["--version", "v0.1.0"]):
            with self.assertRaises(SystemExit), redirect_stdout(io.StringIO()), \
                    redirect_stderr(io.StringIO()):
                run_pipeline.parse_args(argv)

    def test_reads_name_and_version(self):
        args = run_pipeline.parse_args(["--name", "cosmetics", "--version", "v0.1.0"])
        self.assertEqual(args.name, "cosmetics")
        self.assertEqual(args.version, "v0.1.0")
        self.assertFalse(hasattr(args, "dataset"))

    def test_docstring_explains_both_paths(self):
        """Chú ý: đường dẫn dựng từ configs/paths.yaml, không viết cứng trong code."""
        self.assertIn("--name", run_pipeline.__doc__)
        self.assertIn("--version", run_pipeline.__doc__)
        self.assertTrue(run_pipeline.DATASET_CONFIG_DIR.endswith("datasets"))


class HashOnlyToolsTest(unittest.TestCase):
    """`run_token_stats.py` và `run_check_examples.py`: chỉ còn `--hash` để chỉ định bản."""

    def test_token_stats_takes_hash_only(self):
        args = run_token_stats.parse_args(["--hash", HASH8, "--prompt", "absa_cot_v1"])
        self.assertEqual(args.hash, HASH8)
        self.assertFalse(hasattr(args, "version"))
        self.assertFalse(hasattr(args, "dataset"))

    def test_check_examples_takes_hash_only(self):
        args = run_check_examples.parse_args(["--hash", HASH8])
        self.assertEqual(args.hash, HASH8)
        self.assertFalse(hasattr(args, "version"))
        self.assertFalse(hasattr(args, "dataset"))

    def test_check_examples_without_hash_exits_two(self):
        with redirect_stdout(io.StringIO()) as buffer:
            code = run_check_examples.main([])
        self.assertEqual(code, 2)
        self.assertIn("--hash", buffer.getvalue())

    def test_list_prompts_works_without_a_system_key(self):
        """Liệt kê prompt KHÔNG được đòi khoá `system_prompt` của thí nghiệm.

        Prompt có ô nhớ `{system_prompt}` mà chưa gắn thí nghiệm nào (chưa khai khoá) vẫn là prompt
        đang có, nên phải hiện ra; trước 28/09/2026 lệnh này ném PromptError và thoát 1 kèm traceback.
        """
        with redirect_stdout(io.StringIO()) as buffer:
            code = run_token_stats.main(["--list-prompts"])
        self.assertEqual(code, 0)
        self.assertIn("absa_cot_1shot_v1", buffer.getvalue())


class FindVersionTest(unittest.TestCase):
    """`versioning.find_version`: nhận hash8 hoặc mã đầy đủ; không khớp thì báo lỗi rõ."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        patcher = mock.patch.dict(os.environ, {paths.ENV_DATA_ROOT: self._tmp.name})
        patcher.start()
        self.addCleanup(patcher.stop)
        (Path(self._tmp.name) / "processed" / FULL_ID).mkdir(parents=True)
        self.version = FULL_ID

    def test_accepts_hash8_and_full_id(self):
        self.assertEqual(versioning.find_version(HASH8), self.version)
        self.assertEqual(versioning.find_version(FULL_ID), self.version)

    def test_is_case_insensitive_for_hash8(self):
        self.assertEqual(versioning.find_version(HASH8.upper()), self.version)

    def test_unknown_hash8_lists_what_exists(self):
        with self.assertRaises(versioning.VersionError) as caught:
            versioning.find_version("deadbeef")
        self.assertIn(self.version, str(caught.exception))

    def test_wrong_shape_is_refused(self):
        with self.assertRaises(versioning.VersionError) as caught:
            versioning.find_version("khong-phai-hash")
        self.assertIn("8 ký tự hex", str(caught.exception))

    def test_missing_value_is_refused(self):
        with self.assertRaises(versioning.VersionError) as caught:
            versioning.find_version("")
        self.assertIn("Thiếu `--hash`", str(caught.exception))

    def test_two_versions_sharing_a_suffix_are_refused(self):
        other = "khac-ds0.1.0-pl0.1.0-srckhac@0.1.0-" + HASH8
        (Path(self._tmp.name) / "processed" / other).mkdir(parents=True)
        with self.assertRaises(versioning.VersionError) as caught:
            versioning.find_version(HASH8)
        self.assertIn("NHIỀU phiên bản", str(caught.exception))

    def test_version_parts_splits_name_and_hash(self):
        self.assertEqual(versioning.version_parts(self.version), ("cosmetics", HASH8))


class ResetExperimentArgsTest(unittest.TestCase):
    """`scripts/reset_experiment.py`: tổ hợp cờ bị từ chối TRƯỚC khi gọi máy chủ MLflow."""

    def mistake(self, argv):
        return reset_experiment.check_args(reset_experiment.parse_args(argv))

    def test_no_flags_is_allowed(self):
        self.assertIsNone(self.mistake([]))

    def test_dry_run_alone_is_allowed(self):
        self.assertIsNone(self.mistake(["--dry-run"]))

    def test_keep_experiment_with_yes_is_allowed(self):
        self.assertIsNone(self.mistake(["--keep-experiment", "--yes"]))

    def test_run_by_name_is_allowed(self):
        self.assertIsNone(self.mistake(["--run", "07637bcf", "--yes"]))

    def test_run_takes_several_names(self):
        args = reset_experiment.parse_args(["--run", "07637bcf", "e616c1e3"])
        self.assertEqual(args.run, ["07637bcf", "e616c1e3"])

    def test_experiment_flag_overrides_the_config_name(self):
        self.assertEqual(reset_experiment.parse_args(["--experiment", "khac"]).experiment_name,
                         "khac")

    def test_dry_run_with_yes_is_refused(self):
        message = self.mistake(["--dry-run", "--yes"])
        self.assertIn("--dry-run", message)
        self.assertIn("--yes", message)

    def test_run_with_keep_experiment_is_refused(self):
        message = self.mistake(["--run", "07637bcf", "--keep-experiment"])
        self.assertIn("--keep-experiment", message)

    def test_impossible_combination_exits_two_before_touching_the_server(self):
        """Câu lệnh chưa rõ phải dừng NGAY: không đọc env, không mở kết nối."""
        with redirect_stdout(io.StringIO()) as buffer:
            code = reset_experiment.main(["--dry-run", "--yes"])
        self.assertEqual(code, 2)
        self.assertIn("--dry-run", buffer.getvalue())


class ResetExperimentSelectTest(unittest.TestCase):
    """Chọn run để xoá: nhận CẢ runName (cột hiện trên DagsHub) lẫn run_id, và báo tên không khớp.

    Dùng dict thay cho dòng của `search_runs` vì mọi chỗ đọc đều qua `row.get(...)`.
    """

    NAME_A, NAME_B = "07637bcf", "e616c1e3"
    ID_A, ID_B = "1f0a" * 8, "2b3c" * 8
    ROWS = [
        (0, {"run_id": ID_A, "tags.mlflow.runName": NAME_A,
             "status": "FINISHED", "start_time": "2026-10-02 09:30"}),
        (1, {"run_id": ID_B, "tags.mlflow.runName": NAME_B,
             "status": "FAILED", "start_time": "2026-10-02 09:00"}),
    ]

    def test_matches_run_name(self):
        found, missing = reset_experiment.select(self.ROWS, [self.NAME_A])
        self.assertEqual([reset_experiment.run_name_of(row) for _i, row in found], [self.NAME_A])
        self.assertEqual(missing, [])

    def test_matches_run_id(self):
        found, _missing = reset_experiment.select(self.ROWS, [self.ID_B])
        self.assertEqual([reset_experiment.run_name_of(row) for _i, row in found], [self.NAME_B])

    def test_unknown_name_is_reported_as_missing(self):
        found, missing = reset_experiment.select(self.ROWS, ["khong-co"])
        self.assertEqual(found, [])
        self.assertEqual(missing, ["khong-co"])

    def test_same_run_matched_twice_is_deleted_once(self):
        found, missing = reset_experiment.select(self.ROWS, [self.NAME_A, self.ID_A])
        self.assertEqual(len(found), 1)
        self.assertEqual(missing, [])

    def test_runs_without_a_run_name_are_still_listed(self):
        rows = [(0, {"run_id": self.ID_A})]
        self.assertEqual(reset_experiment.run_name_of(rows[0][1]), "")
        self.assertIn(self.ID_A, "\n".join(reset_experiment.describe(rows)))

    def test_describe_prints_both_run_names_and_ids(self):
        text = "\n".join(reset_experiment.describe(self.ROWS))
        self.assertIn(self.NAME_A, text)
        self.assertIn(self.ID_B, text)

    def test_repeated_run_name_is_counted(self):
        """runName KHÔNG duy nhất (chạy lại cùng thư mục kết quả) - phải đếm được để cảnh báo."""
        rows = self.ROWS + [(2, {"run_id": "3c4d" * 8, "tags.mlflow.runName": self.NAME_A})]
        self.assertEqual(reset_experiment.match_counts(rows, [self.NAME_A]), [(self.NAME_A, 2)])
        self.assertEqual(reset_experiment.match_counts(rows, [self.ID_B]), [(self.ID_B, 1)])

    def test_unknown_name_counts_zero(self):
        self.assertEqual(reset_experiment.match_counts(self.ROWS, ["khong-co"]), [("khong-co", 0)])

    def test_silent_console_counts_as_no(self):
        """Phiên không tương tác (hết input) KHÔNG được coi là đồng ý."""
        with mock.patch("builtins.input", side_effect=EOFError):
            self.assertFalse(reset_experiment.confirm("Xoá?"))

    def test_answer_yes_counts_as_yes(self):
        with mock.patch("builtins.input", return_value="y"):
            self.assertTrue(reset_experiment.confirm("Xoá?"))

    def test_answer_no_counts_as_no(self):
        with mock.patch("builtins.input", return_value=""):
            self.assertFalse(reset_experiment.confirm("Xoá?"))


class CollectReportsExcludeTest(unittest.TestCase):
    """`collect_reports.py --exclude`: loại lượt khỏi BẢNG SỐ, giữ nguyên trong `attempt_registry`.

    Dựng REPO TẠM với hai lượt giả (quy ước của dự án: dựng môi trường thật, không giả lập), vì quy
    tắc được khoá ở đây là quy tắc CHỌN LƯỢT - chỉ lộ ra khi đi qua đường ghi file thật.
    """

    def fake_run(self, root, exp_id, hash8):
        """Một lượt chạy tối thiểu: đủ trường để bảng gọi tên lượt và xếp dòng."""
        folder = Path(root) / "m1" / "prompt-cot" / exp_id / "results" / hash8
        folder.mkdir(parents=True)
        (folder / "run_meta.json").write_text(json.dumps({
            "run": {"hash": hash8, "status": "FINISHED", "started": "2026-01-01 00:00:00",
                    "split": "test", "n_samples": 1,
                    "generation": {"do_sample": False, "max_new_tokens": 400}},
            "experiment": {"model": "m1", "method": "prompt-cot", "exp_id": exp_id},
            "data": {"dataset": "cosmetics", "version": "v0.2.0", "build": "fake"},
            "repo": {"sha": "deadbeef"}, "attempts": [],
        }), encoding="utf-8")
        (folder / "metrics.json").write_text(json.dumps({
            "model": "fake", "split": "test", "version_id": "fake", "n_samples": 1,
            "scores": {}, "scores_paper": {}, "read_rate": {}, "aspects": [],
        }), encoding="utf-8")
        (folder / "metrics.csv").write_text("aspect,sentiment,metric,value,basis\n", encoding="utf-8")
        return folder

    def test_exclude_flag_is_repeatable(self):
        args = collect_reports.parse_args(["--exclude", "a", "--exclude", "b"])
        self.assertEqual(args.exclude, ["a", "b"])

    def test_excluded_run_leaves_the_number_table_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, out = Path(tmp) / "experiments", Path(tmp) / "reports"
            self.fake_run(root, "exp001", "aaaa1111")
            self.fake_run(root, "exp002", "bbbb2222")
            with redirect_stdout(io.StringIO()) as captured:
                code = collect_reports.main([
                    "--root", str(root), "--out-root", str(out),
                    "--group", "experiment_registry", "--group", "attempt_registry",
                    "--exclude", "aaaa1111"])
            self.assertEqual(code, 0)
            self.assertIn("Loại khỏi bảng số", captured.getvalue())
            numbers = (out / "experiment_registry" / "experiment_registry.csv").read_text(
                encoding="utf-8-sig").strip().splitlines()
            attempts = (out / "attempt_registry" / "attempt_registry.csv").read_text(
                encoding="utf-8-sig").strip().splitlines()
        # Dòng đầu là tiêu đề, nên số dòng dữ liệu = len - 1.
        self.assertEqual(len(numbers) - 1, 1)
        self.assertIn("bbbb2222", "".join(numbers))
        self.assertNotIn("aaaa1111", "".join(numbers))
        self.assertEqual(len(attempts) - 1, 2)
        self.assertIn("aaaa1111", "".join(attempts))

    def test_unknown_pattern_exits_two_with_the_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, out = Path(tmp) / "experiments", Path(tmp) / "reports"
            self.fake_run(root, "exp001", "aaaa1111")
            with redirect_stdout(io.StringIO()) as captured:
                code = collect_reports.main(["--root", str(root), "--out-root", str(out),
                                             "--dry-run", "--exclude", "khong-co"])
        self.assertEqual(code, 2)
        self.assertIn("không khớp lượt chạy nào", captured.getvalue())


class FitThresholdsArgsTest(unittest.TestCase):
    """`scripts/fit_thresholds.py`: hai chế độ (DÒ trên `val` / ÁP bảng đã chốt lên `test`) không lẫn nhau.

    Vì sao khoá ở đây: gộp hai chế độ là mở đường cho việc "xem `test` rồi mới chọn ngưỡng" - đúng thứ
    luật 1 của `docs/04_experiments/metrics.md` cấm. Câu lỗi phải chỉ ra chế độ nào bị sai.
    """

    def mistake(self, argv):
        return fit_thresholds.check_args(fit_thresholds.parse_args(argv))

    def test_moi_che_do_nhan_dung_mot_thu_muc(self):
        self.assertIsNone(self.mistake(["--run", "experiments/x/lora/exp003/results/abcd1234"]))
        self.assertIsNone(self.mistake(["--apply-to", "experiments/x/lora/exp004/results/abcd1234"]))

    def test_thieu_ca_hai_thi_bi_tu_choi(self):
        self.assertIn("chọn ĐÚNG MỘT", self.mistake([]))

    def test_co_ca_hai_thi_bi_tu_choi(self):
        self.assertIn("chọn ĐÚNG MỘT", self.mistake(["--run", "a", "--apply-to", "b"]))

    def test_luoi_nguong_chi_di_kem_che_do_do(self):
        message = self.mistake(["--apply-to", "b", "--grid", "0.1,0.2"])
        self.assertIn("--grid", message)
        self.assertIn("chế độ DÒ", message)
        self.assertIn("--max-cells-drop",
                      self.mistake(["--apply-to", "b", "--max-cells-drop", "0.02"]))
        self.assertIsNone(self.mistake(["--run", "a", "--grid", "0.1,0.2",
                                        "--max-cells-drop", "0.02"]))

    def test_che_do_ap_doc_tep_luat_mac_dinh(self):
        args = fit_thresholds.parse_args(["--apply-to", "a"])
        self.assertEqual(args.thresholds, fit_thresholds.DEFAULT_OUT)
        self.assertNotEqual(fit_thresholds.DEFAULT_APPLIED, fit_thresholds.DEFAULT_OUT)


# Cùng cách đó cho `scripts/ensemble.py` (trọng số chốt trên `val` rồi áp lên `test`).
ENSEMBLE_SPEC = importlib.util.spec_from_file_location(
    "ensemble", paths.root() / "scripts" / "ensemble.py")
ensemble = importlib.util.module_from_spec(ENSEMBLE_SPEC)
ENSEMBLE_SPEC.loader.exec_module(ensemble)


class EnsembleWeightsArgsTest(unittest.TestCase):
    """`ensemble.py`: trọng số phải CHỐT TRÊN `val` rồi ÁP lên `test` - các tổ hợp cờ mờ bị chặn.

    Lỗi im lặng cần chặn: gọi `--weights val` trên các lượt `test`, tức là chọn trọng số bằng chính tập
    sẽ báo cáo. Luật 1 của `docs/04_experiments/metrics.md` cấm điều đó, nên `weights_of` phải chặn.
    """

    def mistake(self, argv):
        return ensemble.check_args(ensemble.parse_args(argv))

    def test_hai_nguon_trong_so_cung_luc_bi_chan(self):
        message = self.mistake(["--run", "x", "--weights", "val", "--weights-file", "w.json"])
        self.assertIn("--weights-file", message)

    def test_ghi_trong_so_tu_mot_tep_da_co_bi_chan(self):
        message = self.mistake(["--run", "x", "--weights-file", "w.json",
                                "--write-weights", "khac.json"])
        self.assertIn("--write-weights", message)

    def test_ghi_trong_so_can_che_do_chot(self):
        self.assertIn("--write-weights", self.mistake(["--run", "x", "--write-weights", "w.json"]))

    def test_val_chi_dung_cung_che_do_chot(self):
        self.assertIn("--val", self.mistake(["--run", "x", "--val", "val-a"]))

    def test_hai_buoc_chot_va_ap_deu_hop_le(self):
        self.assertIsNone(self.mistake(["--run", "val-a", "--run", "val-b", "--weights", "val",
                                        "--write-weights", "w.json"]))
        self.assertIsNone(self.mistake(["--run", "test-a", "--weights-file", "w.json"]))

    def test_chot_tren_test_thi_bao_loi_kem_ten_luot(self):
        """`--weights val` trên lượt `test` = chọn trọng số bằng tập sẽ báo cáo -> phải chặn."""
        run = {"dir": Path("experiments/zz/lora/exp004/results/aaaaaaaa"), "split": "test",
               "aspects": [], "meta": {"experiment": {"model": "zz"}}}
        args = ensemble.parse_args(["--run", "x", "--weights", "val"])
        with mock.patch.object(ensemble.fusion, "load_run", return_value=run):
            with self.assertRaises(ensemble.fusion.FusionError) as found:
                ensemble.weights_of(args, [run])
        self.assertIn("chỉ chốt được trên `val`", str(found.exception))

    def test_ap_tep_trong_so_rap_theo_ten_model(self):
        run = {"dir": Path("experiments/zz/lora/exp004/results/aaaaaaaa"), "split": "test",
               "aspects": [], "meta": {"experiment": {"model": "zz"}}}
        args = ensemble.parse_args(["--run", "x", "--weights-file", "w.json"])
        with mock.patch.object(ensemble.fusion, "load_weights", return_value={"zz": 1.0}):
            weights, table = ensemble.weights_of(args, [run])
        self.assertIsNone(table)
        self.assertEqual(weights[str(run["dir"])], 1.0)


class EnsembleDocTest(unittest.TestCase):
    """Cách dùng HAI BƯỚC phải có trong chú thích đầu tệp - người chạy đọc nó để biết phải làm gì."""

    def test_docstring_co_hai_buoc_va_ten_co(self):
        text = ensemble.__doc__
        self.assertIn("--write-weights", text)
        self.assertIn("--weights-file", text)
        self.assertIn("chỉ dùng được khi", text)


# Cùng cách đó cho `scripts/ensemble_aspect.py` (luật ROUTER chốt trên `val` rồi áp lên `test`).
ROUTER_SPEC = importlib.util.spec_from_file_location(
    "ensemble_aspect", paths.root() / "scripts" / "ensemble_aspect.py")
router_aspect = importlib.util.module_from_spec(ROUTER_SPEC)
ROUTER_SPEC.loader.exec_module(router_aspect)


class AspectRouterArgsTest(unittest.TestCase):
    """`ensemble_aspect.py`: luật phải CHỐT TRÊN `val` rồi ÁP lên `test` - tổ hợp cờ mờ bị chặn.

    Lỗi im lặng cần chặn: chốt router rồi KHÔNG ghi luật (lần sau sẽ chốt lại, và rất dễ chốt bằng
    chính tập đang báo cáo), và đọc một tệp luật không tồn tại mà vẫn chạy tiếp.
    """

    def mistake(self, argv):
        return router_aspect.check_args(router_aspect.parse_args(argv))

    def test_fit_phai_ghi_luat_ra_tep(self):
        message = self.mistake(["--fit", "--run", "x"])
        self.assertIn("--write-router", message)

    def test_apply_khong_ghi_luat(self):
        message = self.mistake(["--apply", "--run", "x", "--write-router", "w.json"])
        self.assertIn("--write-router", message)

    def test_hai_buoc_chot_va_ap_deu_hop_le(self):
        self.assertIsNone(self.mistake(["--fit", "--run", "val-a", "--write-router", "w.json",
                                        "--criterion", "f1_âm"]))
        self.assertIsNone(self.mistake(["--apply", "--run", "test-a", "--router-file", "w.json"]))

    def test_fit_phai_khai_tieu_chi(self):
        """Hai tiêu chí cho hai router khác nhau, nên chốt mà không nói chốt theo số nào là lỗi."""
        message = self.mistake(["--fit", "--run", "x", "--write-router", "w.json"])
        self.assertIn("--criterion", message)

    def test_apply_khong_doi_duoc_tieu_chi(self):
        """Đổi tiêu chí lúc áp = đổi luật sau khi đã thấy `test` -> chặn."""
        message = self.mistake(["--apply", "--run", "x", "--criterion", "accuracy"])
        self.assertIn("--criterion", message)

    def test_ap_tep_luat_khong_co_thi_bao_loi(self):
        """Thiếu tệp luật là lỗi khi CHẠY (mã 1), không phải lỗi câu lệnh - giống `fuse.py`."""
        run = {"dir": Path("experiments/zz/lora/exp004/results/aaaaaaaa"), "split": "test",
               "aspects": ["colour"], "sample_ids": [], "preds": [], "golds": [],
               "meta": {"experiment": {"model": "zz"}}}
        with mock.patch.object(router_aspect.fusion, "load_run", return_value=run):
            code = router_aspect.main(["--apply", "--run", str(paths.root()),
                                       "--router-file", "khong-co.json", "--inputs-dir", ""])
        self.assertEqual(code, 1)

    def test_che_do_ap_doc_tep_luat_mac_dinh(self):
        args = router_aspect.parse_args(["--apply", "--run", "a"])
        self.assertEqual(args.router_file, router_aspect.DEFAULT_ROUTER)

    def test_chot_tren_test_thi_bao_loi_kem_ten_luot(self):
        """`fit_aspect_router` trên lượt `test` = chọn nguồn bằng tập sẽ báo cáo -> phải chặn."""
        run = {"dir": Path("experiments/zz/lora/exp004/results/aaaaaaaa"), "split": "test",
               "aspects": [], "meta": {"experiment": {"model": "zz"}}}
        with self.assertRaises(router_aspect.fusion.FusionError) as found:
            router_aspect.fusion.fit_aspect_router([run])
        self.assertIn("chỉ chốt được trên `val`", str(found.exception))


class AspectRouterDocTest(unittest.TestCase):
    """Cách dùng HAI BƯỚC phải có trong chú thích đầu tệp - người chạy đọc nó để biết phải làm gì."""

    def test_docstring_co_hai_buoc_va_noi_ro_khac_ensemble(self):
        text = router_aspect.__doc__
        self.assertIn("--write-router", text)
        self.assertIn("--router-file", text)
        self.assertIn("KHÔNG trộn", text)


# ... và `scripts/fuse_aspect.py` (gộp HAI TẦNG: khung ô từ encoder, sắc thái từ lượt một-khía-cạnh).
FUSE_ASPECT_SPEC = importlib.util.spec_from_file_location(
    "fuse_aspect", paths.root() / "scripts" / "fuse_aspect.py")
fuse_aspect = importlib.util.module_from_spec(FUSE_ASPECT_SPEC)
FUSE_ASPECT_SPEC.loader.exec_module(fuse_aspect)


class TwoTierCliTest(unittest.TestCase):
    """`fuse_aspect.py`: luật gộp đã chốt trước khi chạy, nên các ca lệch phải DỪNG chứ không đoán."""

    def test_docstring_noi_ro_hai_nguon_va_luat(self):
        text = fuse_aspect.__doc__
        self.assertIn("--encoder", text)
        self.assertIn("--aspect", text)
        self.assertIn("KHUNG Ô", text)

    def test_thieu_thu_muc_thi_ma_2(self):
        self.assertEqual(fuse_aspect.main(["--encoder", "khong-co-thu-muc",
                                           "--aspect", "cung-khong-co", "--inputs-dir", ""]), 2)

    def test_luot_cham_nhieu_khia_canh_thi_ma_1(self):
        wide = {"dir": Path("experiments/zz/lora/exp002/results/bbbbbbbb"), "split": "test",
                "aspects": ["colour", "smell"], "sample_ids": ["0"], "preds": [{}],
                "labels": {0: "", 1: "positive"}, "golds": [], "meta": {"experiment": {"model": "zz"}}}
        with mock.patch.object(fuse_aspect.fusion, "load_run", return_value=wide):
            code = fuse_aspect.main(["--encoder", str(paths.root()), "--aspect", str(paths.root()),
                                     "--inputs-dir", ""])
        self.assertEqual(code, 1)


class ProbeTokensArgsTest(unittest.TestCase):
    """`probe_tokens.py`: hệ số và cửa sổ ngữ cảnh phải là số dương (trần sai là cả lượt sai)."""

    def setUp(self):
        PROBE_SPEC = importlib.util.spec_from_file_location(
            "probe_tokens_cli", paths.root() / "scripts" / "probe_tokens.py")
        self.probe = importlib.util.module_from_spec(PROBE_SPEC)
        PROBE_SPEC.loader.exec_module(self.probe)

    def mistake(self, argv):
        return self.probe.check_args(self.probe.parse_args(argv))

    def test_he_so_phai_duong(self):
        self.assertIn("--factor", self.mistake(["--run", "x", "--factor", "-1"]))

    def test_mac_dinh_hop_le(self):
        self.assertIsNone(self.mistake(["--run", "x"]))


if __name__ == "__main__":
    unittest.main()
