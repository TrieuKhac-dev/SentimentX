# -*- coding: utf-8 -*-
"""Test bước Export của pipeline (`src/pipeline/export.py`).

VÌ SAO CẦN FILE NÀY
Trước đây KHÔNG test nào chạy qua `export.run()`, nên hai lỗi thật sống sót qua CI: biến `written`
vừa là danh sách file đã ghi vừa là cờ boolean (`len(written)` -> TypeError), và biến `lock_matches`
đã được đổi tên nhưng card của báo cáo vẫn dùng (NameError). Cùng lúc, hợp đồng BYTE của
`{split}.csv` không được khoá ở đâu: đổi cách ghi CSV là đổi `eval_lock` của tập test đã công bố
(25/09/2026: 1.518 bản ghi y nguyên mà `sha256` đổi từ `e2558137…` thành `9ac701de…`).

ĐIỀU ĐƯỢC KHOÁ
    1. `{split}.csv` của dataset giữ xuống dòng THẬT trong ô (không escape mất mát);
    2. `eval_lock.json` có đủ hai dấu vân tay + `schema` + số bản ghi;
    3. `export.run` trả về section hợp lệ (không TypeError/NameError) và chạy lại không lỗi;
    4. đổi một bản ghi thì khoá CHẶN (`VersionError`).

Chạy: python -m unittest discover -s tests
"""

import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src import paths, utils, versioning
from src.pipeline import export

VERSION_ID = "cosmetics-ds0.1.0-pl0.1.0-srccosmetics@0.1.0-abcdef12"
ASPECTS = ["stayingpower", "texture", "smell"]
ROWS = {
    "train": [["Son đẹp\nShip nhanh", 1, 0, 0]],
    "val": [["Son thường", 0, 2, 0]],
    "test": [["Sạch sẽ, thơm\nmùi dễ chịu", 0, 1, 1], ["Giá hơi cao", 0, 0, 2]],
}


class ExportCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        patcher = mock.patch.dict(os.environ, {paths.ENV_DATA_ROOT: self._tmp.name})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.processed = paths.processed(VERSION_ID)
        self.config_file = Path(self._tmp.name) / "v0.1.0.yaml"
        self.config_file.write_text("version: v0.1.0\n", encoding="utf-8")
        self.pipeline_config = Path(self._tmp.name) / "pipeline-v0.1.0.yaml"
        self.pipeline_config.write_text("version: v0.1.0\n", encoding="utf-8")

    def context(self, rows=None):
        rows = rows or ROWS
        return {
            "config": {"version": "v0.1.0", "steps": {"clean": {"remove_empty": True}},
                       "_path": self.pipeline_config},
            "transformed": {"rows_per_split": {name: list(split) for name, split in rows.items()},
                            "json_records": [{"split": "train"}, {"split": "val"},
                                             {"split": "test"}]},
            "out_dir": Path(self._tmp.name) / "pipeline",
            "processed_dir": self.processed,
            "dataset": {"name": "cosmetics", "version": "v0.1.0", "aspects": ASPECTS,
                        "labels": ["positive", "negative", "neutral"],
                        "_label_to_id": {"": 0, "positive": 1, "negative": 2, "neutral": 3},
                        "_path": self.config_file,
                        "eval_lock": {"enforce": True, "test": {"file": "test.csv"}}},
            "version_id": VERSION_ID,
            "splits": {name: list(split) for name, split in rows.items()},
            "original_counts": {name: len(split) for name, split in rows.items()},
        }

    def run_export(self, rows=None):
        """Gọi `export.run` với stdout là bộ đệm.

        Không in ra console thật: `export` in tiếng Việt, còn console Windows mặc định là cp1252, nên
        việc in sẽ lỗi ở chỗ KHÔNG liên quan tới điều đang kiểm. Lúc chạy thật, `run_pipeline.py` đã
        ép stdout sang UTF-8 trước khi gọi bước này.
        """
        with mock.patch("sys.stdout", new_callable=io.StringIO):
            return export.run(self.context(rows))

    def test_dataset_csv_giu_duong_dong_that(self):
        """Dataset KHÔNG escape xuống dòng: đây là thứ `eval_lock` và văn bản cho model dựa vào."""
        self.run_export()
        text = (self.processed / "test.csv").read_text(encoding="utf-8-sig")
        self.assertIn("Sạch sẽ, thơm\nmùi dễ chịu", text)
        self.assertNotIn("Sạch sẽ, thơm\\nmùi dễ chịu", text)
        # 1 header + 2 bản ghi, trong đó một bản ghi nằm trên 2 dòng vật lý.
        self.assertEqual(len(text.splitlines()), 4)

    def test_eval_lock_co_hai_dau_van_tay(self):
        self.run_export()
        lock = versioning.split_lock(VERSION_ID)
        test_csv = self.processed / "test.csv"
        self.assertEqual(lock["schema"], versioning.RECORDS_LOCK_SCHEMA)
        self.assertEqual(lock["sha256"], versioning.file_sha256(test_csv))
        self.assertEqual(lock["records_sha256"], versioning.records_sha256(test_csv, ASPECTS))
        self.assertEqual(lock["rows"], 2)

    def test_section_hop_le_va_dem_du_file(self):
        """Lỗi thật đã gặp: `len(written)` với `written` là boolean, và `lock_matches` không tồn tại."""
        section = self.run_export()
        cards = {card["label"]: card["value"] for card in section["cards"]}
        self.assertEqual(cards["Số file đã ghi"], 4)                 # 3 split + label_map.json
        self.assertEqual(cards["test.csv khớp eval_lock"], "Đạt")
        self.assertEqual(section["id"], "pipeline_export")

    def test_chay_lai_cung_du_lieu_khong_loi(self):
        self.run_export()
        self.run_export()
        self.assertEqual(versioning.split_lock(VERSION_ID)["rows"], 2)

    def test_doi_mot_ban_ghi_thi_khoa_chan(self):
        self.run_export()
        changed = dict(ROWS)
        changed["test"] = [["Sạch sẽ, thơm\nmùi dễ chịu", 0, 1, 1], ["Giá rất cao", 0, 0, 2]]
        with self.assertRaises(versioning.VersionError):
            self.run_export(changed)


if __name__ == "__main__":
    unittest.main()
