# -*- coding: utf-8 -*-
"""Test mục lục các lần chạy (src/versioning.py).

Chạy: python -m unittest discover -s tests

Vì sao cần: mục lục là DẤU VẾT của mọi con số trong báo cáo. Một dòng bị mất hay một dòng
trỏ tới file không còn tồn tại đều làm người đọc tin vào thứ không kiểm chứng được - và cả
hai lỗi đó đều không gây ra exception nào. Bộ test dùng manifest ở thư mục tạm, không đụng
vào mục lục thật của dự án.
"""

import tempfile
import unittest
from pathlib import Path

from src import versioning


class TestManifest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "manifest.json"
        self.original = versioning.manifest_path
        versioning.manifest_path = lambda: self.path

    def tearDown(self):
        versioning.manifest_path = self.original
        self.tmp.cleanup()

    def test_record_keeps_all_entries(self):
        """Ghi nhiều lần chạy khác nhóm thì KHÔNG được làm mất dòng nào."""
        versioning.record({"version_id": "v1", "phase": "eda"})
        versioning.record({"version_id": "v1", "phase": "model_input",
                           "report": "README.md"})
        versioning.record({"version_id": "v1", "phase": "qwen_eval",
                           "report": "README.md"})
        self.assertEqual(len(versioning.read_manifest()["entries"]), 3)

    def test_record_drops_entry_whose_report_is_gone(self):
        """Dòng trỏ tới file báo cáo không tồn tại phải bị dọn, dòng còn lại thì giữ."""
        versioning.record({"version_id": "v1", "phase": "qwen_eval",
                           "report": "README.md"})
        versioning.record({"version_id": "v1", "phase": "qwen_eval",
                           "report": "data/reports/khong_ton_tai.csv"})
        reports = [entry.get("report")
                   for entry in versioning.read_manifest()["entries"]]
        self.assertIn("README.md", reports)
        self.assertNotIn("data/reports/khong_ton_tai.csv", reports)

    def test_same_run_replaces_instead_of_duplicating(self):
        """Cùng (phiên bản, nhóm, file báo cáo) là cùng một lần chạy -> thay thế, không thêm."""
        versioning.record({"version_id": "v1", "phase": "qwen_eval",
                           "report": "README.md", "lần": 1})
        versioning.record({"version_id": "v1", "phase": "qwen_eval",
                           "report": "README.md", "lần": 2})
        entries = versioning.read_manifest()["entries"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["lần"], 2)

    def test_prune_missing_only_writes_when_something_dropped(self):
        versioning.record({"version_id": "v1", "phase": "eda"})
        before = self.path.stat().st_mtime
        dropped = versioning.prune_missing()
        self.assertEqual(dropped, [])
        self.assertEqual(self.path.stat().st_mtime, before)


if __name__ == "__main__":
    unittest.main()
