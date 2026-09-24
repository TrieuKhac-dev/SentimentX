# -*- coding: utf-8 -*-
"""Test nhận biết nơi đang chạy và nạp biến môi trường (src/runtime.py).

Điều quan trọng nhất được khoá ở đây: **thư mục Drive phải nhận ra bằng FILE ĐÁNH DẤU**, không
phải bằng tên. MyDrive và Shared drives trông giống nhau, mà chỉ một trong hai là thư mục giảng
viên cấp; đoán theo tên thì notebook ghi kết quả vào chỗ không ai tìm thấy.

Chạy: python -m unittest discover -s tests
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src import runtime

MARKER = ".sentimentx_root"


class TestEnvironment(unittest.TestCase):
    def test_env_name_from_variable(self):
        with mock.patch.dict(os.environ, {"SENTIMENTX_ENV": "colab"}):
            self.assertEqual(runtime.env_name(), "colab")
        with mock.patch.dict(os.environ, {"SENTIMENTX_ENV": "LOCAL"}):
            self.assertEqual(runtime.env_name(), "local")

    def test_env_name_ignores_unknown_value(self):
        with mock.patch.dict(os.environ, {"SENTIMENTX_ENV": "lung-tung"}):
            self.assertIn(runtime.env_name(), ("colab", "local"))

    def test_load_env_reads_a_file_and_reports_names_only(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / ".env.colab"
            path.write_text("SENTIMENTX_TEST_BIEN=gi-tri-that\n# chu thich\n\n",
                            encoding="utf-8")
            os.environ.pop("SENTIMENTX_TEST_BIEN", None)
            try:
                lines = runtime.load_env(colab_env_file=str(path))
                self.assertIn(str(path), lines["files"])
                self.assertEqual(os.environ.get("SENTIMENTX_TEST_BIEN"), "gi-tri-that")
                # Chỉ tên biến được báo lại, không bao giờ giá trị.
                self.assertNotIn("gi-tri-that", str(lines))
            finally:
                os.environ.pop("SENTIMENTX_TEST_BIEN", None)


    def test_load_env_ignores_empty_values(self):
        """Khoá để trống nghĩa là "không đặt".

        Ca thật: `.env` có `HF_HOME=` để trống, biến bị đặt thành chuỗi rỗng, và `huggingface_hub`
        ghép `os.path.join("", "hub")` thành thư mục `hub` NGAY TRONG REPO rồi tải 6,3 GB model vào
        cây làm việc. Đặt chuỗi rỗng không phải là "không cấu hình" đối với thư viện bên dưới.
        """
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / ".env.colab"
            path.write_text("SENTIMENTX_TEST_RONG=\nSENTIMENTX_TEST_CO=that\n", encoding="utf-8")
            for name in ("SENTIMENTX_TEST_RONG", "SENTIMENTX_TEST_CO"):
                os.environ.pop(name, None)
            try:
                runtime.load_env(colab_env_file=str(path))
                self.assertIsNone(os.environ.get("SENTIMENTX_TEST_RONG"))
                self.assertEqual(os.environ.get("SENTIMENTX_TEST_CO"), "that")
            finally:
                for name in ("SENTIMENTX_TEST_RONG", "SENTIMENTX_TEST_CO"):
                    os.environ.pop(name, None)


class TestDriveDir(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.shared = self.root / "Shareddrives" / "nhom"
        self.mine = self.root / "MyDrive" / "nhom"

    def tearDown(self):
        self._tmp.cleanup()

    def candidates(self):
        return [str(self.root / "MyDrive" / "{folder}"),
                str(self.root / "Shareddrives" / "{folder}")]

    def test_finds_the_folder_that_has_the_marker(self):
        self.mine.mkdir(parents=True)
        (self.mine / MARKER).write_text("", encoding="utf-8")
        found = runtime.drive_dir(folder="nhom", candidates=self.candidates())
        self.assertEqual(found, self.mine)

    def test_ignores_a_folder_without_the_marker(self):
        self.mine.mkdir(parents=True)
        self.assertIsNone(runtime.drive_dir(folder="nhom", candidates=self.candidates()))

    def test_falls_back_to_the_shared_drive(self):
        self.shared.mkdir(parents=True)
        (self.shared / MARKER).write_text("", encoding="utf-8")
        found = runtime.drive_dir(folder="nhom", candidates=self.candidates())
        self.assertEqual(found, self.shared)

    def test_none_when_drive_is_not_mounted(self):
        self.assertIsNone(runtime.drive_dir(folder="nhom", candidates=self.candidates()))

    def test_finds_the_folder_when_its_name_is_unknown(self):
        """Người nhận notebook chỉ copy thư mục của nhóm vào Drive - tên có thể khác.

        Đây là đường đi chính của bản giao: bắt người chạy khai đúng tên thư mục là bắt họ làm một
        việc mà máy làm được, và tên thật thường là "SentimentX (1)" sau khi copy.
        """
        other = self.root / "MyDrive" / "SentimentX (1)"
        other.mkdir(parents=True)
        (other / MARKER).write_text("", encoding="utf-8")
        found = runtime.drive_dir(folder="", candidates=self.candidates())
        self.assertEqual(found, other)

    def test_the_search_never_picks_a_folder_without_the_marker(self):
        (self.root / "MyDrive" / "TaiLieu").mkdir(parents=True)
        (self.root / "MyDrive" / "TaiLieu" / "data").mkdir()
        self.assertIsNone(runtime.drive_dir(folder="", candidates=self.candidates()))

    def test_the_search_prefers_the_folder_that_looks_prepared(self):
        for name in ("b", "a"):
            folder = self.root / "MyDrive" / name
            folder.mkdir(parents=True)
            (folder / MARKER).write_text("", encoding="utf-8")
        (self.root / "MyDrive" / "b" / "data").mkdir()
        self.assertEqual(runtime.drive_dir(folder="", candidates=self.candidates()),
                         self.root / "MyDrive" / "b")

    def test_the_search_also_looks_inside_a_shared_drive(self):
        other = self.root / "Shareddrives" / "Khoa CNTT"
        other.mkdir(parents=True)
        (other / MARKER).write_text("", encoding="utf-8")
        self.assertEqual(runtime.drive_dir(folder="", candidates=self.candidates()), other)

    def test_env_file_path_inside_the_drive(self):
        self.mine.mkdir(parents=True)
        (self.mine / MARKER).write_text("", encoding="utf-8")
        path = runtime.drive_env_file(folder="nhom", candidates=self.candidates())
        self.assertEqual(path.name, ".env.colab")
        self.assertEqual(path.parent.name, "env")

    def test_env_file_is_none_without_drive(self):
        self.assertIsNone(runtime.drive_env_file(folder="nhom", candidates=self.candidates()))


if __name__ == "__main__":
    unittest.main()
