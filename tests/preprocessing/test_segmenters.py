# -*- coding: utf-8 -*-
"""Test bộ tách từ: hướng dẫn cài phải ĐÚNG MÔI TRƯỜNG, và đường dẫn tính LÚC GỌI.

Chạy: python -m unittest discover -s tests
"""

import os
import unittest
from unittest import mock

from src.core import paths
from src.preprocessing.segmenters import vncorenlp


class VnCoreNLPHintTest(unittest.TestCase):
    """A-3: câu hướng dẫn khác nhau giữa Colab và Windows."""

    def test_windows_hint_uses_the_setup_scripts(self):
        with mock.patch.object(vncorenlp, "_in_colab", return_value=False):
            hint = vncorenlp.install_hint()
        self.assertIn("setup_vncorenlp.ps1", hint)

    def test_colab_hint_never_points_at_a_powershell_script(self):
        with mock.patch.object(vncorenlp, "_in_colab", return_value=True):
            hint = vncorenlp.install_hint()
            missing = vncorenlp._missing_model_hint([vncorenlp.model_dir() / "VnCoreNLP-1.2.jar"])
            java = vncorenlp._missing_java_hint()
        for text in (hint, missing, java):
            self.assertNotIn(".ps1", text)
        self.assertIn("Restart session", missing)


class VnCoreNLPModelDirTest(unittest.TestCase):
    """A-2: `model_dir()` tính theo GỐC DỮ LIỆU hiện tại, không dùng giá trị đóng băng lúc import."""

    def test_model_dir_follows_the_env_root(self):
        with mock.patch.dict(os.environ, {paths.ENV_DATA_ROOT: os.path.join("C:", "khong-co-that")}):
            self.assertEqual(vncorenlp.model_dir(), paths.data("models") / "vncorenlp")
            self.assertTrue(str(vncorenlp.model_dir()).endswith("vncorenlp"))


if __name__ == "__main__":
    unittest.main()
