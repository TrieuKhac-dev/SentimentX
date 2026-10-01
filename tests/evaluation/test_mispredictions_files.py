# -*- coding: utf-8 -*-
"""Kiểm HAI tệp ô đoán sai: hợp đồng khi ghi, và tính nhất quán của kết quả ĐÃ có trên đĩa.

Vì sao cần: `mispredictions_paper.csv` phải là TẬP CON của `mispredictions.csv` theo từng dòng, và
số dòng của nó (theo khía cạnh) phải khớp `metrics.json` - `paper.cells` trừ số ô ĐÚNG trong
`scores_paper.accuracy`. Hai điều đó nói lên rằng tệp mới và bộ chấm điểm cùng đọc MỘT bộ ô; lệch
nghĩa là hai con số đang nói về hai tập dữ liệu khác nhau, phải dừng lại tra.

`MispredictionsWriteTest` chạy được ở mọi máy. `MispredictionsFilesTest` chỉ kiểm thứ đã có trên đĩa:
máy chưa có lượt chạy nào (`experiments/` rỗng) thì BỎ QUA - nó không tự chạy model.

Chạy: python -m unittest discover -s tests
"""

import json
import tempfile
import unittest
from pathlib import Path

from src.core import paths, utils
from src.evaluation import scorers

OUTSIDE = ("không nhắc", "không đọc được")
TASK = {"label_space": "binary", "neutral_policy": "drop", "not_mentioned": "separate"}
LABELS = {0: "không nhắc", 1: "positive", 2: "negative", 3: "neutral"}


def build(gold, pred, aspects=("texture",), **kwargs):
    """Đóng gói dữ liệu để chấm, dùng đúng lớp `scorers.Samples.build`."""
    return scorers.Samples.build(list(aspects), gold, pred,
                                 task=dict(TASK), labels=LABELS, **kwargs)


def run_dirs():
    """Mọi thư mục lượt chạy đang có tệp `mispredictions.csv` (bỏ qua khi chưa chạy gì)."""
    root = paths.experiments_dir()
    if not root.is_dir():
        return []
    return sorted(path.parent for path in root.glob("**/results/*/mispredictions.csv"))


class MispredictionsFilesTest(unittest.TestCase):
    def setUp(self):
        self.dirs = run_dirs()
        if not self.dirs:
            self.skipTest("chưa có lượt chạy nào trên đĩa")

    def rows(self, directory, name):
        return utils.read_csv(directory / name).to_dict("records")

    def test_paper_file_is_a_subset_of_the_all_file(self):
        """Mọi dòng của tệp `paper` đều có trong tệp `all`, và không dòng nào ngoài hai cực."""
        for directory in self.dirs:
            with self.subTest(run=str(directory)):
                all_rows = self.rows(directory, "mispredictions.csv")
                paper_rows = self.rows(directory, "mispredictions_paper.csv")
                found = {(row["review"], row["aspect"], row["gold"], row["pred"])
                         for row in all_rows}
                for row in paper_rows:
                    self.assertIn((row["review"], row["aspect"], row["gold"], row["pred"]),
                                  found)
                    self.assertNotIn(row["gold"], OUTSIDE)
                    self.assertNotIn(row["pred"], OUTSIDE)

    def test_paper_rows_match_the_paper_scores(self):
        """Số dòng theo khía cạnh = số ô SAI của `scores_paper` (`cells` trừ `correct`)."""
        for directory in self.dirs:
            with self.subTest(run=str(directory)):
                payload = json.loads((directory / "metrics.json").read_text(encoding="utf-8"))
                accuracy = (payload.get("scores_paper") or {}).get("accuracy") or {}
                by_aspect = accuracy.get("by_aspect") or {}
                if not by_aspect:
                    continue          # lượt chạy trước 01/10/2026: chỉ có cơ sở `all`
                wrong = {}
                for row in self.rows(directory, "mispredictions_paper.csv"):
                    wrong[row["aspect"]] = wrong.get(row["aspect"], 0) + 1
                for aspect, item in by_aspect.items():
                    self.assertEqual(
                        wrong.get(aspect, 0), item["cells"] - item["correct"],
                        "khía cạnh {} lệch giữa tệp và `scores_paper`".format(aspect))


class MispredictionsWriteTest(unittest.TestCase):
    """Hợp đồng của HAI tệp ô đoán sai do `scorers.write` ghi ra (không cần lượt chạy thật)."""

    def test_writes_the_paper_file_next_to_the_all_file(self):
        """Cùng cột với tệp `all`, nhưng chỉ ô của tập công bố."""
        gold = [{"texture": 1}, {"texture": 0}, {"texture": 2}]
        pred = [{"texture": 1}, {"texture": 1}, {"texture": 1}]
        samples = build(gold, pred, sample_ids=["r0", "r1", "r2"])
        with tempfile.TemporaryDirectory() as folder:
            written = scorers.write(folder, samples, save_plots=False)
            all_rows = utils.read_csv(Path(folder) / "mispredictions.csv")
            paper_rows = utils.read_csv(Path(folder) / "mispredictions_paper.csv")
        self.assertIn("mispredictions_paper.csv", written)
        self.assertEqual(list(all_rows.columns), scorers.MISPREDICTION_COLUMNS)
        self.assertEqual(list(paper_rows.columns), scorers.MISPREDICTION_COLUMNS)
        # `all`: dương tính giả trên khía cạnh không nhắc (r1) và đoán sai giữa hai cực (r2).
        self.assertEqual(list(all_rows["review"]), ["r1", "r2"])
        # `paper`: r1 bị loại (nhãn đúng không nhắc) nên chỉ còn r2 - TẬP CON của tệp `all`.
        self.assertEqual(list(paper_rows["review"]), ["r2"])

    def test_both_files_exist_even_without_wrong_cells(self):
        """Không có ô sai nào thì hai tệp vẫn phải tồn tại (chỉ có dòng tiêu đề).

        Thiếu tệp thì người đọc không phân biệt được "không có ô sai" với "lượt chạy cũ không ghi".
        """
        gold = [{"texture": 1}]
        samples = build(gold, gold)
        with tempfile.TemporaryDirectory() as folder:
            written = scorers.write(folder, samples, save_plots=False)
            paper_rows = utils.read_csv(Path(folder) / "mispredictions_paper.csv")
        self.assertIn("mispredictions.csv", written)
        self.assertIn("mispredictions_paper.csv", written)
        self.assertEqual(list(paper_rows.columns), scorers.MISPREDICTION_COLUMNS)
        self.assertEqual(len(paper_rows), 0)


if __name__ == "__main__":
    unittest.main()