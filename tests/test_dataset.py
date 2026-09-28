# -*- coding: utf-8 -*-
"""Test lớp config dataset (src/dataset.py).

Điều được khoá ở đây: file YAML khai khoá mà KHÔNG code nào đọc thì phải BÁO LỖI, không được bỏ qua.

Vì sao cần: `_normalize` làm `cfg = dict(raw)` rồi ghi đè các khoá phẳng nó tự sinh, nên một khoá viết
sai tên - hoặc khoá cũ còn sót lại như `raw_dir`, `text_column` - nằm lại trong config mà không có tác
dụng gì. Đã gặp thật: bảng `dataset_registry` có cột `raw_dir` rỗng suốt vì khoá đó không còn ai đọc,
và tài liệu thì vẫn dạy người mới điền nó.

Chạy: python -m unittest discover -s tests
"""

import unittest

from src import dataset


class CheckKeysTest(unittest.TestCase):
    """`check_keys` chỉ ĐỌC dict, nên test được không cần file."""

    PATH = "configs/datasets/cosmetics/v0.1.0.yaml"

    def test_mot_khoa_cu_nhu_raw_dir_la_loi(self):
        with self.assertRaises(dataset.DatasetError) as caught:
            dataset.check_keys({"name": "cosmetics", "raw_dir": "data/raw/cosmetics"}, self.PATH)
        message = str(caught.exception)
        self.assertIn("raw_dir", message)
        self.assertIn("không hợp lệ", message)
        self.assertIn("sources", message)          # gợi ý khoá gần đúng

    def test_khoa_la_trong_schema_la_loi(self):
        with self.assertRaises(dataset.DatasetError) as caught:
            dataset.check_keys({"schema": {"text_column": "data", "aspects": ["colour"]}}, self.PATH)
        self.assertIn("schema.text_column", str(caught.exception))

    def test_khoa_la_trong_sources_la_loi(self):
        raw = {"sources": [{"kind": "raw", "name": "cosmetics", "raw_versionn": "v0.1.0"}]}
        with self.assertRaises(dataset.DatasetError) as caught:
            dataset.check_keys(raw, self.PATH)
        self.assertIn("raw_versionn", str(caught.exception))

    def test_khoa_noi_bo_bat_dau_bang_gach_duoi_thi_bo_qua(self):
        """Khoá `_path`/`_sources`... là do `_normalize` sinh ra, không phải người viết."""
        dataset.check_keys({"name": "x", "_raw_dir": "đâu đó", "_sources": []}, self.PATH)

    def test_config_that_su_khong_bi_chan(self):
        dataset.check_keys({
            "schema_version": 1, "name": "cosmetics", "version": "v0.1.0",
            "sources": [{"kind": "raw", "name": "cosmetics", "raw_version": "v0.1.0"}],
            "pipeline_version": "v0.1.0", "format": "csv",
            "splits": {"train": "a.csv", "val": "b.csv", "test": "c.csv"},
            "full": "d.csv",
            "schema": {"text": {"column": "data"}, "id": {"column": None},
                       "aspects": ["colour"], "labels": ["positive"], "drop": [], "keep": []},
            "aspect_policy": "union", "parent": None, "notes": "x",
            "eval_lock": {"enforce": True, "test": {"file": "test.csv"}},
        }, self.PATH)

    def test_config_dataset_that_tren_dia_van_nap_duoc(self):
        """Chốt lại: file phiên bản đang dùng trong repo phải qua được phép kiểm này."""
        config = dataset.load_config("cosmetics")
        self.assertEqual(config["name"], "cosmetics")
        self.assertTrue(config["_raw_dir"])


if __name__ == "__main__":
    unittest.main()
