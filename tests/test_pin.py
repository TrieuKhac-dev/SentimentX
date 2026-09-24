# -*- coding: utf-8 -*-
"""Test ghim bản code vào notebook (scripts/pin.py).

Điều quan trọng nhất được khoá ở đây: **ghim lại không được đẻ ra ô thứ hai**. Ô đã ghim được tìm
theo DẤU, nên người dùng di chuyển ô đi đâu thì lần ghim sau vẫn cập nhật đúng ô đó.

Test đọc `scripts/pin.py` bằng đường dẫn (thư mục `scripts/` không phải package), và KHÔNG bắt
buộc `nbformat`: máy có thì còn kiểm cấu trúc notebook, máy thiếu thì vẫn ghim được.

Chạy: python -m unittest discover -s tests
"""

import importlib.util
import tempfile
import unittest
from pathlib import Path

from src import paths

SPEC = importlib.util.spec_from_file_location("pin", paths.root() / "scripts" / "pin.py")
pin = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pin)


def empty_notebook():
    return {"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}


class TestPathsAndLines(unittest.TestCase):
    def test_experiment_parts(self):
        self.assertEqual(pin.experiment_parts("m/method/exp001"),
                         ("m", "method", "exp001"))
        self.assertEqual(pin.experiment_parts("m\\method\\exp001"),
                         ("m", "method", "exp001"))

    def test_bad_experiment_is_an_error(self):
        for text in ("", "chi-co-mot", "a/b", "a/b/c/d"):
            with self.assertRaises(pin.PinError):
                pin.experiment_parts(text)

    def test_notebook_path(self):
        path = pin.notebook_path("qwen3-4b-instruct-2507/prompt-cot/exp001")
        self.assertEqual(path.name, pin.NOTEBOOK)
        self.assertEqual(path.parent.name, "exp001")
        self.assertEqual(path.parent.parent.name, "prompt-cot")

    def test_pinned_lines_hold_the_four_constants(self):
        text = "".join(pin.pinned_lines("https://example.invalid/r.git", "experiment",
                                        "a" * 40, "m/method/exp001"))
        self.assertIn(pin.MARKER, text)
        self.assertIn("REPO_URL = 'https://example.invalid/r.git'", text)
        self.assertIn("REPO_BRANCH = 'experiment'", text)
        self.assertIn("REPO_SHA = '{}'".format("a" * 40), text)
        self.assertIn("EXP_DIR = 'm/method/exp001'", text)


class TestNotebookEditing(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / pin.NOTEBOOK

    def tearDown(self):
        self._tmp.cleanup()

    def test_inserts_the_cell_at_the_top(self):
        notebook = empty_notebook()
        notebook["cells"].append({"cell_type": "markdown", "metadata": {},
                                  "source": ["# Thí nghiệm"]})
        lines = pin.pinned_lines("u", "experiment", "sha", "m/method/exp001")

        notebook, replaced = pin.update(notebook, lines)
        self.assertFalse(replaced)
        self.assertEqual(len(notebook["cells"]), 2)
        self.assertIn(pin.MARKER, "".join(notebook["cells"][0]["source"]))
        self.assertEqual(notebook["cells"][0]["source"], lines)

    def test_second_pin_updates_in_place(self):
        notebook = empty_notebook()
        notebook["cells"].append({"cell_type": "markdown", "metadata": {}, "source": ["# Đầu"]})
        notebook, _replaced = pin.update(
            notebook, pin.pinned_lines("u", "experiment", "sha1", "m/method/exp001"))
        notebook, replaced = pin.update(
            notebook, pin.pinned_lines("u", "experiment", "sha2", "m/method/exp001"))

        self.assertTrue(replaced)
        self.assertEqual(len(notebook["cells"]), 2)
        self.assertIn("sha2", "".join(notebook["cells"][0]["source"]))
        self.assertEqual(notebook["cells"][1]["source"], ["# Đầu"])

    def test_pinned_cell_moved_away_is_still_updated(self):
        """Người dùng có thể kéo ô ghim xuống dưới: ghim lại phải tìm theo DẤU."""
        notebook = empty_notebook()
        notebook, _ = pin.update(notebook, pin.pinned_lines("u", "b", "sha1", "m/method/exp001"))
        moved = notebook["cells"].pop(0)
        notebook["cells"].append({"cell_type": "code", "metadata": {}, "outputs": [],
                                  "execution_count": None, "source": ["x = 1"]})
        notebook["cells"].append(moved)

        notebook, replaced = pin.update(
            notebook, pin.pinned_lines("u", "b", "sha2", "m/method/exp001"))
        self.assertTrue(replaced)
        # Ô ghim vẫn nằm ở chỗ người dùng đặt (cuối), không bị nhân đôi, và vẫn là ô DUY NHẤT có dấu.
        self.assertEqual(len(notebook["cells"]), 2)
        self.assertIn("sha2", "".join(notebook["cells"][1]["source"]))
        self.assertEqual(sum(pin.MARKER in "".join(cell.get("source") or [])
                             for cell in notebook["cells"]), 1)

    def test_round_trip_through_disk(self):
        notebook, _ = pin.update(empty_notebook(),
                                 pin.pinned_lines("u", "b", "sha", "m/method/exp001"))
        pin.write_notebook(self.path, notebook)

        stored = pin.read_notebook(self.path)
        self.assertEqual(stored, notebook)
        self.assertTrue(self.path.read_text(encoding="utf-8").endswith("\n"))

    def test_missing_or_broken_notebook_is_an_error(self):
        with self.assertRaises(pin.PinError):
            pin.read_notebook(self.path)

        self.path.write_text("{ khong-phai-json", encoding="utf-8")
        with self.assertRaises(pin.PinError):
            pin.read_notebook(self.path)

    def test_validate_only_warns_when_nbformat_is_missing(self):
        warnings = pin.validate(empty_notebook(), self.path)
        try:
            import nbformat  # noqa: F401
            has_nbformat = True
        except ImportError:
            has_nbformat = False
        self.assertEqual(bool(warnings), not has_nbformat)


class TestStatusParsing(unittest.TestCase):
    def test_reads_paths_and_skips_allowed_ones(self):
        output = "\n".join([
            " M scripts/pin.py",
            "?? experiments/m/method/exp001/notebook.ipynb",
            ' M "docs/co dau cach.md"',
            "R  cu.txt -> moi.txt",
            "",
        ])
        dirty = pin.parse_porcelain(output, keep=["scripts/pin.py"])
        self.assertEqual(dirty, ["experiments/m/method/exp001/notebook.ipynb",
                                 "docs/co dau cach.md", "moi.txt"])

    def test_empty_output(self):
        self.assertEqual(pin.parse_porcelain(""), [])


if __name__ == "__main__":
    unittest.main()

