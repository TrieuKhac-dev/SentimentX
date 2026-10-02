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


if __name__ == "__main__":
    unittest.main()
