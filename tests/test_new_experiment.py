# -*- coding: utf-8 -*-
"""Test công cụ tạo thí nghiệm (`scripts/new_experiment.py`, `src/notebooks.py`).

Ba điều được khoá ở đây:

1. `config.yaml` và ô GHIM của notebook phải nói cùng MỘT thí nghiệm. Lệch nhau thì notebook ghi
   kết quả vào thư mục thí nghiệm khác mà vẫn ra số bình thường.
2. Số `expNNN` không được trùng thí nghiệm đang có.
3. Công cụ phải TỪ CHỐI tạo khi nhánh đã ghim chưa có trên remote: commit ghim không nằm trên nhánh
   thì kết quả chạy ra không dùng được (docs/00_workflow/01_flow.md).

Chạy: python -m unittest discover -s tests
"""

import importlib.util
import unittest
from pathlib import Path

from src import experiments, notebooks, paths

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    """Nạp một script trong `scripts/` như module, để gọi thẳng `main()`."""
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / "{}.py".format(name))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


new_experiment = load_script("new_experiment")


class ConfigTextTest(unittest.TestCase):
    """Sinh config của thí nghiệm từ bản mẫu: sửa bốn dòng định danh, giữ ghi chú."""

    def setUp(self):
        self.template = (paths.templates_dir() / "experiment" / "config.yaml").read_text(
            encoding="utf-8")

    def test_bon_dong_dinh_danh_duoc_dat_dung(self):
        text = new_experiment.config_text(self.template, "model-x", "method-y", "exp007",
                                          "model-x/method-y/exp003")
        self.assertIn("exp_id: exp007\n", text)
        self.assertIn("model: model-x\n", text)
        self.assertIn("method: method-y\n", text)
        self.assertIn("parent: model-x/method-y/exp003\n", text)

    def test_parent_rong_thanh_null(self):
        text = new_experiment.config_text(self.template, "model-x", "method-y", "exp007", None)
        self.assertIn("parent: null\n", text)

    def test_ghi_chu_cua_ban_mau_con_nguyen(self):
        text = new_experiment.config_text(self.template, "model-x", "method-y", "exp007", None)
        self.assertIn("# Config RIÊNG của một thí nghiệm", text)
        self.assertIn("roles: {eval: test}", text)
        self.assertIn("prompt: prompt.txt", text)

    def test_ban_mau_thieu_dong_thi_bao_loi(self):
        with self.assertRaises(new_experiment.NewExperimentError):
            new_experiment.config_text("model: x\n", "model-x", "method-y", "exp007", None)


class CleanParentTest(unittest.TestCase):

    def test_de_trong_hoac_none_la_ban_goc(self):
        self.assertIsNone(new_experiment.clean_parent(None))
        self.assertIsNone(new_experiment.clean_parent(""))
        self.assertIsNone(new_experiment.clean_parent("none"))

    def test_du_ba_phan_thi_nhan(self):
        self.assertEqual(new_experiment.clean_parent("a\\b\\c"), "a/b/c")
        self.assertEqual(new_experiment.clean_parent("a/b/c"), "a/b/c")

    def test_thieu_phan_thi_bao_loi(self):
        with self.assertRaises(new_experiment.NewExperimentError):
            new_experiment.clean_parent("a/b")


class NotebookExpDirTest(unittest.TestCase):
    """Ô GHIM: đổi `EXP_DIR`, không đụng các dòng khác."""

    def _notebook(self):
        source = ("{}\nREPO_URL = 'https://example'\nREPO_BRANCH = 'experiment'\n"
                  "REPO_SHA = '<chua-ghim>'\nEXP_DIR = '<model>/<method>/<expNNN>'\n".format(
                      notebooks.MARKER))
        return {"cells": [{"cell_type": "markdown", "source": "tiêu đề"},
                          {"cell_type": "code", "source": source}]}

    def test_dat_lai_exp_dir(self):
        notebook = notebooks.set_exp_dir(self._notebook(), "m/me/exp001")
        source = notebooks.source_of(notebooks.pinned_cell(notebook, required=True))
        self.assertIn("EXP_DIR = 'm/me/exp001'", source)
        self.assertIn("REPO_SHA = '<chua-ghim>'", source)
        self.assertNotIn("<model>/<method>/<expNNN>", source)

    def test_notebook_thieu_o_ghim_thi_bao_loi(self):
        with self.assertRaises(notebooks.NotebookError):
            notebooks.set_exp_dir({"cells": [{"cell_type": "code", "source": "x = 1"}]},
                                  "m/me/exp001")

    def test_o_ghim_thieu_dong_exp_dir_thi_bao_loi(self):
        notebook = {"cells": [{"cell_type": "code",
                               "source": "{}\nREPO_URL = 'x'\n".format(notebooks.MARKER)}]}
        with self.assertRaises(notebooks.NotebookError):
            notebooks.set_exp_dir(notebook, "m/me/exp001")


class NextExpIdTest(unittest.TestCase):

    def test_so_ke_tiep_khong_trung_so_dang_co(self):
        model_id, method = "qwen3-4b-instruct-2507", "prompt-cot"
        existing = [exp_id for _m, _me, exp_id in experiments.list_experiments(model_id, method)]
        nxt = experiments.next_exp_id(model_id, method)
        self.assertRegex(nxt, r"^exp\d{3}$")
        self.assertNotIn(nxt, existing)
        numbers = [int(exp_id[3:]) for exp_id in existing if exp_id[3:].isdigit()]
        if numbers:
            self.assertEqual(int(nxt[3:]), max(numbers) + 1)

    def test_model_khong_ton_tai_thi_bat_dau_tu_exp001(self):
        self.assertEqual(experiments.next_exp_id("khong-co-model-nay", "khong-co-method-nay"),
                         "exp001")


class MainTest(unittest.TestCase):
    """Chạy công cụ: các trường hợp phải TỪ CHỐI, và chế độ chỉ in ra."""

    MODEL = "qwen3-4b-instruct-2507"
    METHOD = "prompt-cot"

    def test_dry_run_khong_tao_gi(self):
        code = new_experiment.main(["--model", self.MODEL, "--method", self.METHOD,
                                    "--exp-id", "exp900", "--dry-run"])
        self.assertEqual(code, 0)
        self.assertFalse(experiments.experiment_dir(self.MODEL, self.METHOD, "exp900").exists())

    def test_tu_choi_khi_nhanh_chua_co_tren_remote(self):
        code = new_experiment.main(["--model", self.MODEL, "--method", self.METHOD,
                                    "--exp-id", "exp901", "--branch", "khong-co-nhanh-nay"])
        self.assertEqual(code, 2)
        self.assertFalse(experiments.experiment_dir(self.MODEL, self.METHOD, "exp901").exists())

    def test_tu_choi_khi_model_chua_co_config(self):
        code = new_experiment.main(["--model", "khong-co-model-nay", "--method", self.METHOD])
        self.assertEqual(code, 2)

    def test_tu_choi_khi_thi_nghiem_da_co(self):
        existing = experiments.list_experiments()
        if not existing:
            self.skipTest("chưa có thí nghiệm nào để thử")
        model_id, method, exp_id = existing[0]
        code = new_experiment.main(["--model", model_id, "--method", method, "--exp-id", exp_id])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()

