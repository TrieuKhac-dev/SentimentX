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
from unittest import mock

import yaml

from src import experiments, notebooks, paths, repo

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    """Nạp một script trong `scripts/` như module, để gọi thẳng `main()`."""
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / "{}.py".format(name))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


new_experiment = load_script("new_experiment")


class ConfigTextTest(unittest.TestCase):
    """Sinh config của thí nghiệm từ bản mẫu: sửa năm dòng định danh, giữ ghi chú."""

    def setUp(self):
        self.template = (paths.templates_dir() / "experiment" / "config.yaml").read_text(
            encoding="utf-8")

    def test_nam_dong_dinh_danh_duoc_dat_dung(self):
        text = new_experiment.config_text(self.template, "model-x", "method-y", "exp007",
                                          "model-x/method-y/exp003")
        self.assertIn("exp_id: exp007\n", text)
        self.assertIn("model: model-x\n", text)
        self.assertIn("method: method-y\n", text)
        self.assertIn("parent: model-x/method-y/exp003\n", text)
        self.assertIn("notes: null\n", text)

    def test_tieu_de_di_vao_notes_va_van_la_yaml_hop_le(self):
        """`--title` là tham số tài liệu đã hướng dẫn; tiêu đề có dấu hai chấm vẫn phải hợp lệ."""
        text = new_experiment.config_text(self.template, "model-x", "method-y", "exp007", None,
                                          "CoT 1 shot: bản thử")
        self.assertIn('notes: "CoT 1 shot: bản thử"\n', text)
        self.assertEqual(yaml.safe_load(text)["notes"], "CoT 1 shot: bản thử")

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

    def setUp(self):
        # Cây làm việc của MÁY ĐANG CHẠY test có thể đang bẩn (người dùng đang làm dở). Guard "cây sạch"
        # được kiểm riêng ở `GuardsTest`; ở đây khoá lại trạng thái sạch để mỗi test chỉ kiểm đúng điều
        # nó nói, không phụ thuộc trạng thái repo của người chạy.
        patcher = mock.patch.object(repo, "worktree_dirty", return_value=[])
        patcher.start()
        self.addCleanup(patcher.stop)

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


class NotesFlagTest(unittest.TestCase):
    """Cờ mô tả thí nghiệm tên là `--notes`, TRÙNG tên khoá trong config; `--title` (tên cũ) đã bỏ.

    Vì sao khoá lại: tài liệu cũ, bản mẫu cũ và commit cũ đều nhắc `--title`, nên người đọc tài liệu cũ
    có thể gõ lại nó. Phải LỖI rõ ràng, không được im lặng bỏ qua - và cũng không được thêm alias ngầm.
    """

    def test_notes_flag_fills_the_config(self):
        args = new_experiment.parse_args(["--model", "m", "--method", "mm", "--notes", "mô tả"])
        self.assertEqual(args.notes, "mô tả")

    def test_the_old_title_flag_is_rejected(self):
        import contextlib
        import io

        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                new_experiment.parse_args(["--model", "m", "--method", "mm", "--title", "x"])


class RemoteIdsTest(unittest.TestCase):
    """Số `expNNN` phải tính CẢ thí nghiệm đã nằm trên nhánh, không chỉ cây làm việc.

    Vì sao khoá: hai người tạo thí nghiệm song song trên hai máy - nếu chỉ nhìn cây làm việc thì cả hai
    cùng nhận `exp002`, và chỉ lúc merge mới biết (docs/00_workflow/01_flow.md).
    """

    def test_doc_ten_tu_ls_tree(self):
        with mock.patch.object(repo, "run_git", return_value=(0, "exp001\nexp004\n")):
            self.assertEqual(experiments.remote_exp_ids("m", "mm", "origin/experiment"),
                             ["exp001", "exp004"])

    def test_khong_doc_duoc_thi_tra_danh_sach_rong(self):
        with mock.patch.object(repo, "run_git", return_value=(128, "lỗi")):
            self.assertEqual(experiments.remote_exp_ids("m", "mm", "origin/experiment"), [])

    def test_next_exp_id_tinh_ca_so_tren_remote(self):
        with mock.patch.object(experiments, "list_experiments", return_value=[]), \
                mock.patch.object(experiments, "remote_exp_ids", return_value=["exp001", "exp004"]):
            self.assertEqual(experiments.next_exp_id("m", "mm", ref="origin/experiment"), "exp005")


class GuardsTest(unittest.TestCase):
    """Ba việc kiểm trước khi tạo: cây sạch, nhánh hiện tại chứa `origin/<nhánh>`, thư mục chưa có.

    Mọi test ở đây dùng `--dry-run`, nên KHÔNG ghi gì vào repo.
    """

    ARGS = ["--model", "qwen3-4b-instruct-2507", "--method", "prompt-cot", "--dry-run"]

    def test_cay_ban_thi_tu_choi(self):
        with mock.patch.object(repo, "worktree_dirty", return_value=["a.txt", "b.txt"]):
            self.assertEqual(new_experiment.main(list(self.ARGS)), 2)

    def test_nhanh_chua_chua_origin_thi_tu_choi(self):
        with mock.patch.object(repo, "worktree_dirty", return_value=[]), \
                mock.patch.object(repo, "run_git", return_value=(0, "")), \
                mock.patch.object(repo, "ref_exists", return_value=True), \
                mock.patch.object(repo, "is_ancestor", return_value=False):
            self.assertEqual(new_experiment.main(list(self.ARGS)), 2)

    def test_allow_dirty_van_di_tiep_duoc(self):
        """Cờ thoát cho lúc đang làm dở: công cụ chạy tiếp, nhưng phải NÓI RA là commit sẽ mang theo."""
        with mock.patch.object(repo, "worktree_dirty", return_value=["a.txt"]), \
                mock.patch.object(repo, "run_git", return_value=(0, "")), \
                mock.patch.object(repo, "ref_exists", return_value=True), \
                mock.patch.object(repo, "is_ancestor", return_value=True), \
                mock.patch.object(experiments, "remote_exp_ids", return_value=[]):
            self.assertEqual(new_experiment.main(list(self.ARGS) + ["--allow-dirty"]), 0)

    def test_moi_thu_sach_thi_dry_run_khong_ghi_gi(self):
        with mock.patch.object(repo, "worktree_dirty", return_value=[]), \
                mock.patch.object(repo, "run_git", return_value=(0, "")), \
                mock.patch.object(repo, "ref_exists", return_value=True), \
                mock.patch.object(repo, "is_ancestor", return_value=True), \
                mock.patch.object(experiments, "remote_exp_ids", return_value=[]):
            self.assertEqual(new_experiment.main(list(self.ARGS)), 0)


if __name__ == "__main__":
    unittest.main()

