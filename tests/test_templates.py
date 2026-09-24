# -*- coding: utf-8 -*-
"""Test bản mẫu (thư mục templates/).

Vì sao cần: notebook không được biên dịch ở đâu cả, nên một lỗi cú pháp trong đó chỉ lộ ra khi
người nhận bấm Run all - đúng lúc không sửa được nữa (sau khi ghim thì không đụng vào thí nghiệm).
Test ở đây BIÊN DỊCH TỪNG Ô CODE của notebook, và kiểm những thứ mà `scripts/pin.py` dựa vào.

Chạy: python -m unittest discover -s tests
"""

import importlib.util
import json
import unittest

import yaml

from src import paths

SPEC = importlib.util.spec_from_file_location("pin", paths.root() / "scripts" / "pin.py")
pin = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pin)

TEMPLATES = paths.root() / "templates"


def notebook():
    with open(TEMPLATES / "experiment" / "notebook.ipynb", encoding="utf-8") as handle:
        return json.load(handle)


class TestFiles(unittest.TestCase):
    def test_every_template_file_exists(self):
        for name in ("templates/README.md", "templates/experiment/README.md",
                     "templates/experiment/config.yaml", "templates/experiment/notebook.ipynb",
                     "templates/prompt/prompt.txt", "templates/prompt/examples.txt",
                     "templates/prompt/system.txt"):
            self.assertTrue((paths.root() / name).is_file(), name)

    def test_config_template_has_the_required_keys(self):
        data = yaml.safe_load((TEMPLATES / "experiment" / "config.yaml").read_text(
            encoding="utf-8"))
        for key in ("exp_id", "model", "method", "data", "prompt"):
            self.assertIn(key, data)
        self.assertIn("dataset", data["data"])
        self.assertIn("version", data["data"])
        self.assertIn("roles", data["data"])
        self.assertIn("eval", data["data"]["roles"])

    def test_prompt_template_has_the_placeholders_the_builder_fills(self):
        text = (TEMPLATES / "prompt" / "prompt.txt").read_text(encoding="utf-8")
        for placeholder in ("{text}", "{aspects}", "{label_guide}"):
            self.assertIn(placeholder, text)
        self.assertIn("[SYSTEM]", text)
        self.assertIn("[USER]", text)

    def test_examples_template_has_a_block_and_the_source_note(self):
        text = (TEMPLATES / "prompt" / "examples.txt").read_text(encoding="utf-8")
        self.assertIn("--- Ví dụ 1 ---", text)
        self.assertIn("KHÔNG lấy từ dữ liệu", text)

    def test_system_template_goes_to_the_model_so_it_has_no_placeholder(self):
        text = (TEMPLATES / "prompt" / "system.txt").read_text(encoding="utf-8").strip()
        self.assertTrue(text)
        self.assertNotIn("{", text)
        self.assertNotIn("]", text.splitlines()[0])


class TestNotebookTemplate(unittest.TestCase):
    def test_it_is_a_valid_nbformat_4_notebook(self):
        data = notebook()
        self.assertEqual(data["nbformat"], 4)
        self.assertTrue(data["cells"])

    def test_code_cells_compile(self):
        """Ô code không được biên dịch ở đâu khác, nên lỗi cú pháp chỉ lộ khi bấm Run all."""
        for index, cell in enumerate(notebook()["cells"]):
            if cell.get("cell_type") != "code":
                continue
            source = cell.get("source") or ""
            if isinstance(source, list):
                source = "".join(source)
            with self.subTest(cell=index):
                compile(source, "<cell {}>".format(index), "exec")

    def test_first_code_cell_is_the_pinned_one(self):
        code_cells = [cell for cell in notebook()["cells"] if cell.get("cell_type") == "code"]
        source = "".join(code_cells[0].get("source") or [])
        self.assertIn(pin.MARKER, source)
        for name in ("REPO_URL", "REPO_BRANCH", "REPO_SHA", "EXP_DIR"):
            self.assertIn("{} = ".format(name), source)

    def test_notebook_calls_the_real_cli_and_the_preflight(self):
        text = json.dumps(notebook(), ensure_ascii=False)
        self.assertIn("run_qwen_eval", text)
        self.assertIn("preflight.run", text)
        self.assertIn("repo.prepare", text)
        self.assertIn("runtime.load_env", text)

    def test_it_stops_when_the_preflight_finds_problems(self):
        text = json.dumps(notebook(), ensure_ascii=False)
        self.assertIn("SystemExit", text)


if __name__ == "__main__":
    unittest.main()
