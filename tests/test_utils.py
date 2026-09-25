# -*- coding: utf-8 -*-
"""Test các hàm dùng chung (src/utils.py).

Điều được khoá ở đây: **file CSV phải có MỘT bản ghi trên MỘT dòng vật lý**. Ô để nguyên ký tự xuống
dòng vẫn hợp lệ theo chuẩn CSV, nhưng mọi trình xem thông thường (Notepad, VSCode, công cụ tự viết)
coi "một dòng = một bản ghi" - bảng dự đoán có ô dài hàng nghìn ký tự nên một review chiếm hàng chục
dòng, và người đọc tưởng các cột phía sau biến mất (đã gặp thật 25/09/2026).

Chạy: python -m unittest discover -s tests
"""

import csv
import io
import shutil
import tempfile
import unittest
from pathlib import Path

from src import utils

COLUMNS = ["chỉ số", "text", "câu trả lời"]


class WriteCsvTest(unittest.TestCase):
    def write(self, rows):
        folder = Path(tempfile.mkdtemp(prefix="sentimentx-utils-"))
        self.addCleanup(shutil.rmtree, str(folder), ignore_errors=True)
        return utils.write_csv(rows, COLUMNS, folder / "out.csv")

    @staticmethod
    def read(path):
        """Đọc lại bằng bộ đọc CSV chuẩn: kiểm nội dung ĐÃ PARSE, không kiểm chuỗi thô.

        Ô chứa dấu `"` được trích dẫn và nhân đôi dấu, nên so chuỗi thô là kiểm cả cách trích dẫn
        của thư viện - thứ không phải điều đang muốn khoá.
        """
        with io.open(path, encoding="utf-8-sig", newline="") as handle:
            return list(csv.reader(handle))

    def test_newlines_inside_a_cell_become_backslash_n(self):
        path = self.write([[1, "hai\ndòng", 'SUY LUẬN:\n- a | b | mã 1\nKẾT QUẢ:\n{"a": 1}']])
        rows = self.read(path)
        self.assertEqual(len(rows), 2, "phải là 1 dòng header + 1 dòng dữ liệu")
        self.assertEqual(rows[1][1], "hai\\ndòng")
        self.assertEqual(rows[1][2], 'SUY LUẬN:\\n- a | b | mã 1\\nKẾT QUẢ:\\n{"a": 1}')

    def test_crlf_and_lone_cr_are_handled_too(self):
        path = self.write([[2, "một\r\nhai\rba", "x"]])
        rows = self.read(path)
        self.assertEqual(rows[1][1], "một\\nhai\\nba")
        self.assertEqual(len(rows), 2)

    def test_numbers_and_empty_values_are_untouched(self):
        path = self.write([[3, "", 1.5]])
        rows = self.read(path)
        self.assertEqual(rows[1], ["3", "", "1.5"])
        self.assertEqual(len(rows), 2)


if __name__ == "__main__":
    unittest.main()
