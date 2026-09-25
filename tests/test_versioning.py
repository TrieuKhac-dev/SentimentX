# -*- coding: utf-8 -*-
"""Test mã phiên bản dữ liệu và đường dẫn kết quả (src/versioning.py).

Chạy: python -m unittest discover -s tests

Vì sao cần: mã phiên bản là thứ nối mọi con số về đúng bộ dữ liệu sinh ra nó. Hai lỗi không
gây exception nào mà vẫn làm mất dấu vết:
    - mã không đổi khi nội dung dữ liệu đổi -> kết quả mới nằm đè lên kết quả cũ;
    - mã băm cả file không phải dữ liệu (kết quả EDA, metadata) -> đổi báo cáo cũng sinh mã mới.
Test dùng thư mục tạm, không đụng vào dữ liệu thật của dự án.
"""

import hashlib
import json
import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src import paths, utils, versioning

ID_PATTERN = re.compile(
    r"^cosmetics-ds0\.1\.0-pl0\.1\.0-srccosmetics@0\.1\.0-[0-9a-f]{8}$")


class TestEvalLockFile(unittest.TestCase):
    """Khoá tập đánh giá: ghi MỘT LẦN cho mỗi phiên bản, nằm cạnh dữ liệu.

    Vì sao khoá nằm ở đây chứ không ở file phiên bản dataset: giá trị `sha256` của `test.csv` chỉ
    biết được SAU khi pipeline chạy lần đầu, mà file phiên bản thì bất biến. Ghi khoá cùng dữ liệu
    nghĩa là bản dữ liệu ĐẦU TIÊN đã có khoá, và mọi lượt chạy sau đều kiểm được tập test còn nguyên.
    """

    VERSION_ID = "cosmetics-ds0.1.0-pl0.1.0-srccosmetics@0.1.0-abcdef12"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        patcher = mock.patch.dict(os.environ, {paths.ENV_DATA_ROOT: self.tmp.name})
        patcher.start()
        self.addCleanup(patcher.stop)

    def measured(self, sha256="a" * 64, rows=1518):
        return {"file": "test.csv", "sha256": sha256, "rows": rows}

    def test_ghi_roi_doc_lai(self):
        path = versioning.write_eval_lock(self.VERSION_ID, self.measured())
        self.assertEqual(path, paths.processed(self.VERSION_ID) / "eval_lock.json")
        self.assertEqual(versioning.read_eval_lock(self.VERSION_ID)["test"]["rows"], 1518)
        self.assertEqual(versioning.split_lock(self.VERSION_ID)["sha256"], "a" * 64)

    def test_chua_ghi_thi_doc_ra_rong(self):
        self.assertEqual(versioning.read_eval_lock(self.VERSION_ID), {})
        self.assertEqual(versioning.split_lock(self.VERSION_ID), {})

    def test_ghi_lai_cung_noi_dung_thi_khong_loi(self):
        versioning.write_eval_lock(self.VERSION_ID, self.measured())
        versioning.write_eval_lock(self.VERSION_ID, self.measured())
        self.assertEqual(versioning.split_lock(self.VERSION_ID)["sha256"], "a" * 64)

    def test_doi_tap_danh_gia_thi_bao_loi_kem_cach_sua(self):
        versioning.write_eval_lock(self.VERSION_ID, self.measured())
        with self.assertRaises(versioning.VersionError) as caught:
            versioning.write_eval_lock(self.VERSION_ID, self.measured(sha256="b" * 64))
        self.assertIn("KHÁC", str(caught.exception))
        self.assertIn("phiên bản dataset mới", str(caught.exception))


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

    def test_id_unchanged_when_line_endings_change(self):
        """CRLF (Windows) và LF (Linux/Colab) là CÙNG một dữ liệu, phải ra cùng một mã.

        Lỗi thật: notebook ghim chạy trên Colab xin `...-2d9fc48b` còn máy cá nhân đã tạo
        `...-bf68b1c5` - chỉ vì kiểu xuống dòng khác nhau, nên hai máy không đời nào khớp kết quả.
        """
        before = self.compute()
        (self.raw / "train.csv").write_bytes(b"text,a\r\nhay,positive\r\n")
        (self.raw / "full.csv").write_bytes(b"text,a\r\nhay,positive\r\n")
        self.dataset_config.write_bytes(b"name: cosmetics\r\nversion: v0.1.0\r\n")
        self.assertEqual(before, self.compute())

    def test_id_unchanged_when_a_bom_is_added(self):
        before = self.compute()
        (self.raw / "train.csv").write_bytes(b"\xef\xbb\xbftext,a\nhay,positive\n")
        self.assertEqual(before, self.compute())

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

    def test_file_sha256_ignores_line_endings(self):
        """`eval_lock.test.sha256` ghi ở máy Windows rồi đem so trên Colab Linux."""
        path = Path(self.tmp.name) / "b.txt"
        path.write_bytes(b"mot\nhai\n")
        one = versioning.file_sha256(path)
        path.write_bytes(b"mot\r\nhai\r\n")
        self.assertEqual(one, versioning.file_sha256(path))

    def test_file_sha256_of_a_binary_file_keeps_every_byte(self):
        """File nhị phân KHÔNG được chuẩn hoá: trong nó `\\r` là dữ liệu, không phải xuống dòng."""
        path = Path(self.tmp.name) / "b.bin"
        path.write_bytes(b"\x00\x01mot\r\ntmp")
        self.assertEqual(versioning.file_sha256(path),
                         hashlib.sha256(b"\x00\x01mot\r\ntmp").hexdigest())

    def test_file_sha256_matches_known_value(self):
        path = Path(self.tmp.name) / "a.txt"
        path.write_text("abc", encoding="utf-8")
        self.assertEqual(
            versioning.file_sha256(path),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")


class TestGuard(unittest.TestCase):
    """File phiên bản đã dùng thì không được sửa (guard bất biến)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        patcher = mock.patch.dict(os.environ, {"SENTIMENTX_DATA_ROOT": self.tmp.name})
        patcher.start()
        self.addCleanup(patcher.stop)

        self.config = Path(self.tmp.name) / "v0.1.0.yaml"
        self.config.write_text("version: v0.1.0\n", encoding="utf-8")
        self.name = "cosmetics-ds0.1.0-pl0.1.0-srccosmetics@0.1.0-ab12cd34"
        directory = Path(self.tmp.name) / "processed" / self.name
        directory.mkdir(parents=True)
        (directory / "processing_log.json").write_text(json.dumps({
            "dataset": {"config": utils.rel(self.config),
                        "config_sha256": versioning.file_sha256(self.config)},
        }), encoding="utf-8")

    def test_unchanged_config_passes(self):
        self.assertEqual(versioning.guard_versions({"_path": self.config}), [])

    def test_changed_config_raises_with_instruction(self):
        self.config.write_text("version: v0.1.0\nnotes: sua sau khi dung\n", encoding="utf-8")
        with self.assertRaises(versioning.VersionError) as caught:
            versioning.guard_versions({"_path": self.config})
        self.assertIn(self.name, str(caught.exception))
        self.assertIn("phiên bản mới", str(caught.exception))

    def test_config_never_used_is_not_guarded(self):
        other = Path(self.tmp.name) / "khac.yaml"
        other.write_text("x: 1\n", encoding="utf-8")
        self.assertEqual(versioning.guard_versions({"_path": other}), [])


if __name__ == "__main__":
    unittest.main()
