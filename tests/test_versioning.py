# -*- coding: utf-8 -*-
"""Test mã phiên bản dữ liệu và đường dẫn kết quả (src/versioning.py).

Chạy: python -m unittest discover -s tests

Vì sao cần: mã phiên bản là thứ nối mọi con số về đúng bộ dữ liệu sinh ra nó. Hai lỗi không
gây exception nào mà vẫn làm mất dấu vết:
    - mã không đổi khi nội dung dữ liệu đổi -> kết quả mới nằm đè lên kết quả cũ;
    - mã băm cả file không phải dữ liệu (kết quả EDA, metadata) -> đổi báo cáo cũng sinh mã mới.
Test dùng thư mục tạm, không đụng vào dữ liệu thật của dự án.
"""

import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src import versioning

ID_PATTERN = re.compile(
    r"^cosmetics-ds0\.1\.0-pl0\.1\.0-srccosmetics@0\.1\.0-[0-9a-f]{8}$")


class TestComputeId(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.raw = self.root / "raw" / "cosmetics" / "v0.1.0"
        self.raw.mkdir(parents=True)
        (self.raw / "train.csv").write_text("text,a\nhay,positive\n", encoding="utf-8")
        (self.raw / "full.csv").write_text("text,a\nhay,positive\n", encoding="utf-8")
        # File KHÔNG được khai là dữ liệu: đổi nó không được làm đổi mã.
        (self.raw / "raw_meta.yaml").write_text("name: cosmetics\n", encoding="utf-8")

        self.dataset_config = self.root / "v0.1.0.yaml"
        self.dataset_config.write_text("name: cosmetics\nversion: v0.1.0\n", encoding="utf-8")
        self.pipeline_config = self.root / "pipeline.yaml"
        self.pipeline_config.write_text("version: v0.1.0\n", encoding="utf-8")
        self.cfg = self.make_cfg()

    def tearDown(self):
        self.tmp.cleanup()

    def make_cfg(self):
        return {
            "name": "cosmetics",
            "version": "v0.1.0",
            "pipeline_version": "v0.1.0",
            "splits": {"train": "train.csv"},
            "full": "full.csv",
            "_path": self.dataset_config,
            "_sources": [{"kind": "raw", "name": "cosmetics", "version": "v0.1.0",
                          "dir": self.raw}],
        }

    def compute(self):
        return versioning.compute_id(self.cfg, {"_path": self.pipeline_config})

    def test_id_has_name_dataset_pipeline_and_source(self):
        self.assertRegex(self.compute(), ID_PATTERN)

    def test_id_changes_when_source_content_changes(self):
        before = self.compute()
        (self.raw / "train.csv").write_text("text,a\nhay,negative\n", encoding="utf-8")
        self.assertNotEqual(before, self.compute())

    def test_id_changes_when_dataset_config_changes(self):
        before = self.compute()
        self.dataset_config.write_text("name: cosmetics\nversion: v0.1.0\nnotes: x\n",
                                       encoding="utf-8")
        self.assertNotEqual(before, self.compute())

    def test_id_changes_when_pipeline_config_changes(self):
        before = self.compute()
        self.pipeline_config.write_text("version: v0.1.0\nnotes: x\n", encoding="utf-8")
        self.assertNotEqual(before, self.compute())

    def test_id_ignores_files_not_declared_as_data(self):
        before = self.compute()
        (self.raw / "raw_meta.yaml").write_text("name: cosmetics\nnotes: khác\n", encoding="utf-8")
        (self.raw / "eda").mkdir()
        (self.raw / "eda" / "eda_result.json").write_text("{}", encoding="utf-8")
        self.assertEqual(before, self.compute())

    def test_source_files_returns_declared_files_in_order(self):
        names = [path.name for path in versioning.source_files(self.cfg, self.cfg["_sources"][0])]
        self.assertEqual(names, ["train.csv", "full.csv"])


class TestPathsOnDisk(unittest.TestCase):
    """Đường dẫn kết quả và việc dò phiên bản mới nhất, dùng gốc dữ liệu tạm."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        patcher = mock.patch.dict(os.environ, {"SENTIMENTX_DATA_ROOT": self.tmp.name})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmp.cleanup)
        self.name = "cosmetics-ds0.1.0-pl0.1.0-srccosmetics@0.1.0-ab12cd34"

    def test_processed_dir_layout(self):
        self.assertEqual(versioning.processed_dir(self.name),
                         Path(self.tmp.name) / "processed" / self.name)
        self.assertEqual(versioning.pipeline_report_dir(self.name),
                         Path(self.tmp.name) / "processed" / self.name / "pipeline")
        self.assertEqual(versioning.processing_log_path(self.name),
                         Path(self.tmp.name) / "processed" / self.name / "processing_log.json")

    def test_processed_dir_requires_version(self):
        with self.assertRaises(ValueError):
            versioning.processed_dir("")

    def test_processing_log_missing_returns_empty(self):
        self.assertEqual(versioning.read_processing_log(self.name), {})

    def test_processing_log_roundtrip(self):
        path = versioning.processing_log_path(self.name)
        path.parent.mkdir(parents=True)
        path.write_text('{"version_id": "%s", "record_counts": {"after": {"train": 10}}}'
                        % self.name, encoding="utf-8")
        log = versioning.read_processing_log(self.name)
        self.assertEqual(log["record_counts"]["after"]["train"], 10)

    def test_latest_dataset_filters_by_name(self):
        self.assertIsNone(versioning.latest_dataset("cosmetics"))
        (Path(self.tmp.name) / "processed" / self.name).mkdir(parents=True)
        other = "khac-ds0.1.0-pl0.1.0-srckhac@0.1.0-ffffffff"
        (Path(self.tmp.name) / "processed" / other).mkdir(parents=True)
        self.assertEqual(versioning.latest_dataset("cosmetics"), self.name)
        self.assertTrue(versioning.latest_dataset())
        self.assertEqual(len(versioning.dataset_dirs()), 2)

    def test_file_sha256_matches_known_value(self):
        path = Path(self.tmp.name) / "a.txt"
        path.write_text("abc", encoding="utf-8")
        self.assertEqual(
            versioning.file_sha256(path),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")


if __name__ == "__main__":
    unittest.main()
