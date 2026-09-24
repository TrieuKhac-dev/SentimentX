# -*- coding: utf-8 -*-
"""Kiểm tra `src/paths.py`: đường dẫn mặc định, ghi đè bằng biến môi trường, mẫu tên.

Test cuối cùng kiểm luật của P1: trong `src/` và các `run_*.py` không còn đường dẫn
dạng `data/...` viết cứng.
"""

import os
import re
import unittest
from pathlib import Path
from unittest import mock

from src import paths


class TestDefaultPaths(unittest.TestCase):
    """Đường dẫn khi không có gì ghi đè.

    Máy đang chạy có thể đặt sẵn hai biến ghi đè gốc đường dẫn (`SENTIMENTX_DATA_ROOT`,
    `SENTIMENTX_RESULTS_ROOT` - dùng khi chạy trên Colab). Có chúng thì các phép so với đường dẫn
    MẶC ĐỊNH ở đây sẽ sai dù code không sai, nên nhóm test này bỏ chúng trong lúc chạy và trả lại
    nguyên trạng sau khi xong.
    """

    def setUp(self):
        patcher = mock.patch.dict(os.environ)
        patcher.start()
        self.addCleanup(patcher.stop)
        for name in (paths.ENV_DATA_ROOT, paths.ENV_RESULTS_ROOT):
            os.environ.pop(name, None)

    def test_root_contains_paths_config(self):
        self.assertTrue((paths.root() / "configs" / "paths.yaml").is_file())

    def test_data_group(self):
        root = paths.root()
        self.assertEqual(paths.data_root(), root / "data")
        self.assertEqual(paths.data("raw"), root / "data" / "raw")
        self.assertEqual(paths.assets_dir(), root / "data" / "assets")
        self.assertEqual(paths.reference_publication_dir(),
                         root / "data" / "reference_publication")

    def test_report_group(self):
        root = paths.root()
        self.assertEqual(paths.report(), root / "data" / "reports")
        self.assertEqual(paths.report("model_input"),
                         root / "data" / "reports" / "model_input")
        self.assertEqual(paths.report("metrics_matrix"),
                         root / "data" / "reports" / "metrics_matrix")

    def test_report_unknown_group_raises(self):
        with self.assertRaises(KeyError):
            paths.report("khong_co_nhom_nay")

    def test_raw_and_processed(self):
        root = paths.root()
        self.assertEqual(paths.raw_dir("cosmetics", "v0.1.0"),
                         root / "data" / "raw" / "cosmetics" / "v0.1.0")
        self.assertEqual(paths.processed("cosmetics-ds0.1.0-pl0.1.0-abcdef12"),
                         root / "data" / "processed" / "cosmetics-ds0.1.0-pl0.1.0-abcdef12")

    def test_config_paths(self):
        root = paths.root()
        self.assertEqual(paths.configs_dir(), root / "configs")
        self.assertEqual(paths.config_path("datasets"), root / "configs" / "datasets")
        self.assertEqual(paths.config_path("pipeline.yaml"), root / "configs" / "pipeline.yaml")

    def test_experiment_and_results_dir(self):
        root = paths.root()
        self.assertEqual(paths.experiment_dir("qwen3-4b-instruct-2507", "prompt-cot", "exp001"),
                         root / "experiments" / "qwen3-4b-instruct-2507" / "prompt-cot" / "exp001")
        self.assertEqual(
            paths.results_dir("qwen3-4b-instruct-2507", "prompt-cot", "exp001", "cosmetics-ds0.1.0"),
            root / "experiments" / "qwen3-4b-instruct-2507" / "prompt-cot" / "exp001"
            / "results" / "cosmetics-ds0.1.0")

    def test_patterns(self):
        self.assertEqual(paths.pattern("run_log"), "run.log")
        self.assertEqual(paths.pattern("run_meta"), "run_meta.json")
        self.assertEqual(paths.pattern("pred_parts", n=3), "predictions/part_0003.jsonl")

    def test_pattern_unknown_key_raises(self):
        with self.assertRaises(KeyError):
            paths.pattern("khong_co_mau_nay")

    def test_describe_has_roots(self):
        info = paths.describe()
        self.assertEqual(info["data_root"], str(paths.data_root()))
        self.assertEqual(info["results_root"], str(paths.results_root()))


class TestEnvOverrides(unittest.TestCase):
    """Ghi đè gốc đường dẫn, dùng khi chạy trên Colab."""

    def test_data_root_override(self):
        target = str(Path(os.sep) / "tmp" / "sx-data")
        with mock.patch.dict(os.environ, {paths.ENV_DATA_ROOT: target}):
            self.assertEqual(paths.data_root(), Path(target))
            self.assertEqual(paths.data("raw"), Path(target) / "raw")
            # Nhóm report cũng phải đi theo gốc mới, không quay về repo.
            self.assertEqual(paths.report("model_input"),
                             Path(target) / "reports" / "model_input")
            self.assertEqual(paths.raw_dir("cosmetics", "v0.1.0"),
                             Path(target) / "raw" / "cosmetics" / "v0.1.0")

    def test_results_root_override(self):
        target = str(Path(os.sep) / "content" / "drive" / "experiments")
        with mock.patch.dict(os.environ, {paths.ENV_RESULTS_ROOT: target}):
            self.assertEqual(paths.results_root(), Path(target))
            self.assertEqual(
                paths.results_dir("m", "method", "exp001", "ma"),
                Path(target) / "m" / "method" / "exp001" / "results" / "ma")
            # Thư mục định nghĩa thí nghiệm vẫn nằm trong repo.
            self.assertEqual(paths.experiment_dir("m", "method", "exp001"),
                             paths.root() / "experiments" / "m" / "method" / "exp001")

    def test_empty_override_is_ignored(self):
        with mock.patch.dict(os.environ, {paths.ENV_DATA_ROOT: "  "}):
            self.assertEqual(paths.data_root(), paths.root() / "data")


class TestNoHardcodedPaths(unittest.TestCase):
    """Không còn đường dẫn `data/...` viết cứng trong code."""

    # Dựng dấu gạch chéo ngược bằng chr(92) để chính file test này không chứa đường dẫn mẫu.
    NEEDLES = tuple(
        quote + root + separator
        for quote in ('"', "'")
        for root in ("data", "configs")
        for separator in ("/", chr(92))
    )

    def test_sources_have_no_hardcoded_paths(self):
        repo = paths.root()
        targets = list((repo / "src").rglob("*.py"))
        targets += [repo / name for name in (
            "run_eda.py", "run_pipeline.py", "run_token_stats.py", "run_qwen_eval.py",
            "run_rescore_eval.py", "build_report.py", "run_check_examples.py")]
        offenders = []
        for path in targets:
            if "__pycache__" in str(path) or not path.exists():
                continue
            lines = path.read_text(encoding="utf-8").splitlines()
            for number, line in enumerate(lines, start=1):
                if any(needle in line for needle in self.NEEDLES):
                    offenders.append("{}:{}: {}".format(
                        path.relative_to(repo).as_posix(), number, line.strip()))
        self.assertEqual(offenders, [], "Còn đường dẫn viết cứng:\n" + "\n".join(offenders))


if __name__ == "__main__":
    unittest.main()
