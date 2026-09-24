# -*- coding: utf-8 -*-
"""Test sáu kiểm tra tĩnh của CI (src/checks.py, scripts/ci_checks.py).

Mỗi kiểm tra được thử theo HAI chiều: cây sạch thì không báo gì, và cây CỐ TÌNH vi phạm thì báo
đúng chỗ. Chiều thứ hai mới là chiều đáng test - một kiểm tra không bao giờ báo lỗi thì cũng không
chặn được gì, mà lại làm người đọc tin là đã được kiểm.

Chạy: python -m unittest discover -s tests
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src import checks, paths


def notebook(cell_sources, outputs=None, execution_counts=None):
    """Notebook tối thiểu để thử kiểm tra ô sạch."""
    cells = []
    for index, source in enumerate(cell_sources):
        cells.append({"cell_type": "code", "source": source,
                      "outputs": (outputs or [])[index] if outputs else [],
                      "execution_count": (execution_counts or [None] * len(cell_sources))[index]})
    return {"cells": cells, "nbformat": 4, "nbformat_minor": 5}


class DataTrackedTest(unittest.TestCase):
    """Kiểm 1: chỉ file DỮ LIỆU mới bị cấm; metadata và report thì phải được theo dõi."""

    def _found(self, files):
        with mock.patch.object(checks, "tracked_files", return_value=files):
            return checks.data_tracked(paths.root())

    def test_file_du_lieu_thi_bao(self):
        found = self._found(["data/processed/abc/val.csv",
                             "data/models/Qwen3-4B/model.safetensors"])
        self.assertEqual(len(found), 2)

    def test_metadata_va_bao_cao_thi_khong_bao(self):
        self.assertEqual(self._found([
            "data/raw/cosmetics/v0.1.0/raw_meta.yaml",
            "data/raw/cosmetics/v0.1.0/eda/01_x.csv",
            "data/processed/abc/pipeline/steps.json",
            "data/processed/abc/label_map.json",
            "data/models/README.md",
            "data/reports/metrics_matrix/accuracy_by_aspect.csv",
            "data/assets/plotly.min.js",
            "data/reference_publication/accuracy_by_aspect.csv",
        ]), [])

    def test_file_ngoai_data_thi_khong_lien_quan(self):
        self.assertEqual(self._found(["src/checks.py", "docs/README.md"]), [])


class GitignoreTest(unittest.TestCase):

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="sentimentx-gitignore-"))
        self.addCleanup(shutil.rmtree, str(self.root), ignore_errors=True)

    def _write(self, text):
        (self.root / ".gitignore").write_text(text, encoding="utf-8")

    def test_thieu_quy_tac_bo_qua_du_lieu_thi_bao(self):
        self._write("data/reports/x/**\n")
        found = checks.gitignore_rules(self.root)
        self.assertEqual(len(found), len(checks.REQUIRED_IGNORES))

    def test_bo_qua_nham_report_thi_bao(self):
        self._write("\n".join(list(checks.REQUIRED_IGNORES) + ["data/reports"]))
        found = checks.gitignore_rules(self.root)
        self.assertEqual(len(found), 1, found)
        self.assertIn("data/reports", found[0])

    def test_gitignore_dung_thi_khong_bao(self):
        self._write("\n".join(list(checks.REQUIRED_IGNORES) + ["data/reports/x/**"]))
        self.assertEqual(checks.gitignore_rules(self.root), [])

    def test_thieu_file_gitignore_thi_bao_loi_ro(self):
        with self.assertRaises(checks.CheckError):
            checks.gitignore_rules(self.root)


class NotebooksTest(unittest.TestCase):

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="sentimentx-notebooks-"))
        self.addCleanup(shutil.rmtree, str(self.root), ignore_errors=True)
        (self.root / "templates" / "experiment").mkdir(parents=True)

    def _write_notebook(self, name, payload):
        (self.root / "templates" / "experiment" / name).write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def test_notebook_sach_thi_khong_bao(self):
        self._write_notebook("sach.ipynb", notebook(["x = 1"]))
        self.assertEqual(checks.notebooks_clean(self.root), [])

    def test_notebook_con_output_va_con_so_dong_thi_bao_hai_lan(self):
        self._write_notebook("ban.ipynb", notebook(["x = 1"], outputs=[["rác"]],
                                                   execution_counts=[7]))
        found = checks.notebooks_clean(self.root)
        self.assertEqual(len(found), 2, found)
        self.assertTrue(any("output" in item for item in found))
        self.assertTrue(any("số dòng thực thi" in item for item in found))

    def test_notebook_hong_thi_bao(self):
        (self.root / "templates" / "experiment" / "hong.ipynb").write_text("{", encoding="utf-8")
        found = checks.notebooks_clean(self.root)
        self.assertEqual(len(found), 1, found)
        self.assertIn("không đọc được notebook", found[0])


class PinnedTest(unittest.TestCase):

    def test_doc_gia_tri_trong_o_ghim(self):
        sha = "0123456789abcdef0123456789abcdef01234567"
        source = "REPO_SHA = '{}'\n".format(sha)
        self.assertEqual(checks.pinned_value(source, "REPO_SHA"), sha)
        self.assertIsNone(checks.pinned_value(source, "KHONG_CO"))

    def test_chua_ghim_hoac_sha_sai_dang_thi_bao(self):
        root = Path(tempfile.mkdtemp(prefix="sentimentx-pinned-"))
        self.addCleanup(shutil.rmtree, str(root), ignore_errors=True)
        directory = root / "model-x" / "prompt-cot" / "exp001"
        directory.mkdir(parents=True)
        for sha, expected in ((checks.PLACEHOLDER_SHA, "chưa ghim"), ("khong-phai-sha", "40 ký tự")):
            source = "{}\nREPO_SHA = '{}'\n".format(checks.notebooks.MARKER, sha)
            (directory / "notebook.ipynb").write_text(json.dumps({
                "cells": [{"cell_type": "code", "source": source}],
                "nbformat": 4, "nbformat_minor": 5}, ensure_ascii=False), encoding="utf-8")
            with mock.patch.object(checks.experiments, "list_experiments",
                                   return_value=[("model-x", "prompt-cot", "exp001")]), \
                    mock.patch.object(checks.paths, "experiment_dir", return_value=directory), \
                    mock.patch.object(checks.experiments, "shared",
                                      return_value={"branch": "experiment"}):
                found = checks.pinned_shas(root)
            self.assertEqual(len(found), 1, found)
            self.assertIn(expected, found[0])


class RealTreeTest(unittest.TestCase):
    """Chạy trên chính repo này: cây phải SẠCH, nếu không thì commit này chưa được phép đẩy lên."""

    def test_sau_kiem_tra_deu_sach(self):
        report = checks.run()
        self.assertEqual(report["problems"], [])
        self.assertEqual(len(report["notes"]), 6)


if __name__ == "__main__":
    unittest.main()

