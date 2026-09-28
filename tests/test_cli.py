# -*- coding: utf-8 -*-
"""Test tham số dòng lệnh của các tool và `versioning.find_version`.

VÌ SAO CẦN
Cú pháp dòng lệnh là hợp đồng với người chạy (và với ghi chú mà notebook in ra trên Colab). Hai lỗi
ở đây đều im lặng: nhầm mã phiên bản dữ liệu với nhãn raw_version, hoặc để tool tự chọn "bản mới
nhất" - cả hai dẫn tới đo/kiểm một phiên bản khác với điều người chạy tưởng. Test này khoá lại câu
lỗi và mã thoát cho từng dạng sai.

Chạy: python -m unittest discover -s tests
"""

import io
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
from src import paths, versioning

HASH8 = "e0ccc484"
FULL_ID = "cosmetics-ds0.1.0-pl0.1.0-srccosmetics@0.1.0-" + HASH8


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


if __name__ == "__main__":
    unittest.main()
