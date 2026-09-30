# -*- coding: utf-8 -*-
"""Khoá cấu trúc FILE THẬT của công bố (`data/reference_publication/`).

Vì sao có file test này: bản `accuracy_by_aspect.csv` nhận ngày 24/09/2026 bị LỆCH MỘT HÀNG so với
Table 3 của bài - hàng `Smell` bị thiếu và hàng cuối bị ghi tên `Aspect`, nên MỌI khía cạnh bị đem
so với số của khía cạnh khác (ví dụ `colour` bị so với 94,12 vốn là của `Smell`) mà bảng vẫn trông
hợp lý. Bộ đọc không thể tự biết một cái tên là sai, nên phải khoá bằng SỐ CỦA CHÍNH BÀI BÁO:
Table 3 cho accuracy theo khía cạnh, Tables 4-6 cho P/R/F1 theo khía cạnh và sắc thái.
"""

import unittest

from src.core import paths, utils

# Table 3 của bài: (khía cạnh, COT+0-shot, COT+1-shot, COT+5-shot).
ACCURACY = (
    ("smell", 94.59, 96.15, 92.86),
    ("price", 97.22, 100, 100),
    ("texture", 94.12, 100, 100),
    ("colour", 97.37, 96.61, 94.74),
    ("stayingpower", 100, 94.12, 92.86),
    ("packing", 98.25, 98.11, 100),
    ("shipping", 100, 98.89, 96.70),
)
SHOTS = (0, 1, 5)


class ReferenceFileTest(unittest.TestCase):
    """Số của công bố phải khớp Table 3 và Tables 4-6, và không được có hàng nhãn lạ."""

    def setUp(self):
        self.directory = paths.reference_publication_dir()

    def rows(self, name):
        path = self.directory / name
        self.assertTrue(path.is_file(), "thiếu file tham chiếu: {}".format(path))
        return utils.read_csv(path).to_dict("records")

    def test_accuracy_by_aspect_khop_table3(self):
        rows = self.rows("accuracy_by_aspect.csv")
        self.assertEqual(len(rows), len(ACCURACY), "bảng công bố phải có đúng 7 khía cạnh")
        self.assertEqual([str(row["Aspect"]).strip().lower() for row in rows],
                         [item[0] for item in ACCURACY])
        for row, (aspect, shot0, shot1, shot5) in zip(rows, ACCURACY):
            for column, expected in (("COT+0-shot", shot0), ("COT+1-shot", shot1),
                                     ("COT+5-shot", shot5)):
                self.assertEqual(float(row[column]), float(expected),
                                 "{} - {}".format(aspect, column))

    def test_khong_con_hang_ten_aspect(self):
        """Chữ `Aspect` là chữ TIÊU ĐỀ, không phải tên khía cạnh - có hàng đó nghĩa là cột nhãn lệch."""
        names = [str(row["Aspect"]).strip().lower() for row in self.rows("accuracy_by_aspect.csv")]
        self.assertNotIn("aspect", names)

    def test_prf_du_khia_canh_va_sac_thai(self):
        """Ba file P/R/F1 phải đủ 7 khía cạnh × 2 sắc thái, cùng bộ khía cạnh với Table 3."""
        expected = {(aspect, sentiment) for aspect in [item[0] for item in ACCURACY]
                    for sentiment in ("positive", "negative")}
        for shot in SHOTS:
            name = "prf_by_aspect_sentiment_{}shot.csv".format(shot)
            rows = self.rows(name)
            keys = {(str(row["Aspect"]).strip().lower(),
                     str(row["Sentiment"]).strip().lower()) for row in rows}
            self.assertEqual(keys, expected, name)
            for row in rows:
                for column in ("Precision", "Recall", "F1"):
                    value = float(row[column])
                    self.assertGreaterEqual(value, 0.0, "{} - {}".format(name, column))
                    self.assertLessEqual(value, 100.0, "{} - {}".format(name, column))

    def test_phan_bo_nhan_du_bay_khia_canh(self):
        rows = self.rows("sentiment_distribution.csv")
        names = {str(row.get("Aspect") or row.get("aspect") or "").strip().lower()
                 for row in rows}
        self.assertEqual(names, {item[0] for item in ACCURACY})


if __name__ == "__main__":
    unittest.main()
