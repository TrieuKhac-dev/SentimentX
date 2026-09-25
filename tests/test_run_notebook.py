# -*- coding: utf-8 -*-
"""Test script chạy notebook ở máy cá nhân (scripts/run_notebook.py).

Ba điều được khoá ở đây, vì đều là thứ hỏng im lặng nếu sai:
    1. Hằng số ghim được đọc từ CHÍNH file notebook, không lấy từ config hay git - script phải chạy
       đúng thứ mà lượt Run all của người nhận sẽ dùng.
    2. `--preflight-only` phải CẮT từ ô chạy thí nghiệm trở đi. Chạy nốt ô kết thúc (nó đọc
       `run_result`) sẽ báo `NameError` - một lỗi vô nghĩa làm người đọc tưởng notebook hỏng.
    3. `.env` của máy không được mang hai khoá gốc đường dẫn vào kernel: chúng phải trỏ vào repo
       THẬT, không phải thư mục code tạm.

Test đọc `scripts/run_notebook.py` bằng đường dẫn (thư mục `scripts/` không phải package) và KHÔNG
mở kernel: phần chạy thật được kiểm bằng chính lệnh `python scripts/run_notebook.py`.

Chạy: python -m unittest discover -s tests
"""

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src import notebooks, paths

SPEC = importlib.util.spec_from_file_location(
    "run_notebook", paths.root() / "scripts" / "run_notebook.py")
run_notebook = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(run_notebook)

EXPERIMENT = "qwen3-4b-instruct-2507/prompt-cot/exp001"


def pinned_notebook(source=None):
    """Notebook tối thiểu có ô GHIM (tìm theo DẤU, như `scripts/pin.py` ghi)."""
    body = source if source is not None else (
        "# --- BẢN CODE ĐÃ GHIM (do scripts/pin.py ghi; sửa tay sẽ bị ghi đè) ---\n"
        "REPO_URL = 'https://example.invalid/repo.git'\n"
        "REPO_BRANCH = 'experiment'\n"
        "REPO_SHA = '{}'\n"
        "EXP_DIR = '{}'\n".format("a" * 40, EXPERIMENT))
    return {"cells": [{"cell_type": "code", "source": [body], "metadata": {},
                       "outputs": [], "execution_count": None}],
            "metadata": {}, "nbformat": 4, "nbformat_minor": 5}


class TestPathsAndConstants(unittest.TestCase):
    def test_experiment_name_becomes_the_notebook_path(self):
        found = run_notebook.notebook_path(EXPERIMENT)
        self.assertTrue(found.is_file())
        self.assertEqual(found.name, run_notebook.NOTEBOOK_NAME)
        self.assertEqual(found, paths.experiment_dir(*EXPERIMENT.split("/")) / "notebook.ipynb")

    def test_bad_targets_are_an_error(self):
        for target in ("", "chi-co-mot", "a/b", "khong/co/exp999"):
            with self.subTest(target=target):
                with self.assertRaises(run_notebook.RunNotebookError):
                    run_notebook.notebook_path(target)

    def test_constants_come_from_the_pinned_cell(self):
        found = run_notebook.constants(pinned_notebook())
        self.assertEqual(found["REPO_SHA"], "a" * 40)
        self.assertEqual(found["REPO_BRANCH"], "experiment")
        self.assertEqual(found["EXP_DIR"], EXPERIMENT)

    def test_a_missing_pin_is_an_error(self):
        with self.assertRaises(run_notebook.RunNotebookError):
            run_notebook.constants(pinned_notebook(source="# không có hằng số nào\n"))


class TestCellSelection(unittest.TestCase):
    CELLS = ["a", "experiment_run.run(plan, ...)", "print(run_result)", "b"]

    def test_preflight_only_stops_before_the_run_cell(self):
        self.assertEqual(run_notebook.keep_cells(self.CELLS, True),
                         ["a"])

    def test_without_the_flag_all_cells_run(self):
        self.assertEqual(run_notebook.keep_cells(self.CELLS, False), self.CELLS)

    def test_no_run_cell_is_an_error(self):
        with self.assertRaises(run_notebook.RunNotebookError):
            run_notebook.keep_cells(["a", "b"], True)

    def test_run_cell_first_is_an_error(self):
        with self.assertRaises(run_notebook.RunNotebookError):
            run_notebook.keep_cells(["experiment_run.run(x)", "b"], True)


class TestEnvironmentAndState(unittest.TestCase):
    def test_env_file_drops_empty_values_and_the_root_keys(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / ".env").write_text(
                "DAGSHUB_TOKEN=abc\nHF_HOME=\nSENTIMENTX_DATA_ROOT=/noi-khac\n"
                "SENTIMENTX_RESULTS_ROOT=/noi-khac\nSENTIMENTX_ENV=colab\n# chú thích\n",
                encoding="utf-8")
            with mock.patch.object(run_notebook.paths, "root", return_value=Path(folder)):
                found = run_notebook.forward_env()
        self.assertEqual(found, {"DAGSHUB_TOKEN": "abc"})

    def test_state_sees_the_real_repo(self):
        found = run_notebook.state()
        self.assertRegex(found["head"], r"^[0-9a-f]{40}$")
        self.assertEqual(found["branch"], "experiment")
        self.assertIsInstance(found["changes"], list)

    def test_newest_result_dir_is_empty_when_nothing_ran(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertIsNone(run_notebook.newest_result_dir(Path(folder)))


class TestStateDiff(unittest.TestCase):
    """Lượt chạy SINH kết quả trong repo là chuyện bình thường, không phải "repo bị đổi".

    Bản đầu so cả hai chiều nên mỗi lần chạy xong đều in cảnh báo sai - và cảnh báo sai thì người
    đọc học cách bỏ qua cảnh báo thật.
    """

    BEFORE = {"head": "a" * 40, "branch": "experiment", "changes": [" M file.py"]}

    def test_new_result_files_are_not_a_warning(self):
        after = {"head": "a" * 40, "branch": "experiment",
                 "changes": [" M file.py", "?? results/exp001/"]}
        lost, added, moved = run_notebook.state_diff(self.BEFORE, after)
        self.assertEqual(lost, [])
        self.assertEqual(added, ["?? results/exp001/"])
        self.assertFalse(moved)

    def test_a_lost_change_is_reported(self):
        after = {"head": "a" * 40, "branch": "experiment", "changes": []}
        lost, _added, moved = run_notebook.state_diff(self.BEFORE, after)
        self.assertEqual(lost, [" M file.py"])
        self.assertFalse(moved)

    def test_moving_the_head_is_reported(self):
        after = {"head": "b" * 40, "branch": "", "changes": []}
        _lost, _added, moved = run_notebook.state_diff(self.BEFORE, after)
        self.assertTrue(moved)


if __name__ == "__main__":
    unittest.main()
