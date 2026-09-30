# -*- coding: utf-8 -*-
"""Test MẶT TIỀN `src/api/` và luật "ô notebook chỉ đi qua mặt tiền".

VÌ SAO CÓ MẶT TIỀN (và vì sao phải canh nó bằng test)
Notebook ghim MỘT commit rồi chạy rất lâu sau đó, còn `src/` thì đổi chỗ liên tục. Một ô trỏ thẳng
`from src.workflow import repo` sẽ chết lặng lẽ khi file đó chuyển nhà - mà notebook đã ghim thì
không sửa được nữa. Năm phép kiểm dưới đây là toàn bộ luật:

    (a) ô notebook chỉ import từ `src.api`
    (b) tên import từ `src.api` phải có trong `__all__` VÀ tồn tại thật
    (c) hợp `__all__` của các vùng phải BẰNG `__all__` của hub, mỗi tên thuộc ĐÚNG MỘT vùng
    (d) file trong `src/api/` chỉ chứa docstring + import + `__all__` (không logic)
    (e) mã trong `src/` KHÔNG được import `src.api` (chặn vòng import)

Ở chặng này (a) mới áp cho notebook MẪU: 12 notebook đã ghim là bản cũ, được dựng lại ở chặng sau và
khi đó (a) mở rộng cho tất cả.

Chạy: python -m unittest discover -s tests
"""

import ast
import importlib
import json
import re
import unittest

from src import api
from src.workflow import notebooks
from src.core import paths

API_DIR = paths.root() / "src" / "api"
TEMPLATE = paths.root() / "templates" / "experiment" / "notebook.ipynb"
IMPORT_LINE = re.compile(r"^\s*(from|import)\s+src(?:$|\s|\.)")
ALLOWED = re.compile(r"^\s*(?:from\s+src\.api\s+import\s+[\w, ]+|import\s+src\.api\s*)$")


def code_cells(path):
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    return [notebooks.source_of(cell) for cell in data["cells"]
            if cell.get("cell_type") == "code"]


def api_files():
    return sorted(API_DIR.glob("*.py"))


class ImportRuleTest(unittest.TestCase):
    """(a) + (b): ô notebook chỉ đi qua mặt tiền, và tên gọi phải có thật."""

    def imports_of(self, source):
        return [line.strip() for line in source.splitlines()
                if IMPORT_LINE.match(line) and not line.lstrip().startswith("#")]

    def test_o_notebook_chi_import_tu_mat_tien(self):
        wrong = []
        for source in code_cells(TEMPLATE):
            for line in self.imports_of(source):
                if not ALLOWED.match(line):
                    wrong.append(line)
        self.assertEqual(wrong, [], "ô notebook phải import qua `src.api`: {}".format(wrong))

    def test_moi_ten_import_tu_mat_tien_deu_that(self):
        missing = []
        for source in code_cells(TEMPLATE):
            for line in self.imports_of(source):
                if not line.startswith("from src.api import"):
                    continue
                for name in [item.strip() for item in line.split("import", 1)[1].split(",")]:
                    if not name or "." in name or " as " in name:
                        continue
                    if not hasattr(api, name):
                        missing.append(name)
                    elif name not in api.__all__:
                        missing.append(name + " (thiếu trong __all__)")
        self.assertEqual(missing, [], "tên không có trên mặt tiền: {}".format(missing))


class SurfaceTest(unittest.TestCase):
    """(c) + (d): các vùng hợp lại đúng bằng hub, và không vùng nào chứa logic."""

    def zones(self):
        found = {}
        for path in api_files():
            if path.name == "__init__.py":
                continue
            found[path.stem] = importlib.import_module("src.api." + path.stem)
        return found

    def test_cac_vung_hop_lai_dung_bang_hub(self):
        zones = self.zones()
        self.assertTrue(zones, "chưa có vùng nào trong src/api/")
        union = {}
        for name, module in zones.items():
            self.assertTrue(hasattr(module, "__all__"), "vùng {} thiếu __all__".format(name))
            for item in module.__all__:
                self.assertNotIn(item, union, "{} nằm ở HAI vùng ({} và {})".format(
                    item, union.get(item), name))
                union[item] = name
        self.assertEqual(sorted(union), sorted(api.__all__),
                         "hợp các vùng phải đúng bằng __all__ của hub")

    def test_ten_tren_mat_tien_deu_that(self):
        for name in api.__all__:
            with self.subTest(name=name):
                self.assertTrue(hasattr(api, name), "thiếu {} trên src.api".format(name))

    def test_file_trong_api_chi_re_export(self):
        """(d) Mỗi file chỉ được có: docstring, import, và `__all__`."""
        for path in api_files():
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in tree.body:
                with self.subTest(file=path.name, line=getattr(node, "lineno", 0)):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        continue
                    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                        continue                                    # docstring
                    if isinstance(node, ast.Assign) and all(
                            isinstance(target, ast.Name) and target.id == "__all__"
                            for target in node.targets):
                        continue
                    self.fail("{} dòng {}: file mặt tiền chỉ được re-export, không viết logic".format(
                        path.name, getattr(node, "lineno", "?")))


    def test_ten_tren_mat_tien_khong_tro_vao_chinh_src_api(self):
        """Không tên nào trên mặt tiền được là MỘT FILE TRONG `src/api/`.

        Lỗi thật đã suýt lọt: file vùng viết `from src.api import experiments` (import chính nó), nên
        tên `experiments` trên mặt tiền trỏ vào FILE VÙNG thay vì gói `src/experiments` - notebook gọi
        `experiments.load(...)` sẽ chết trên Colab, mà test cũ vẫn xanh vì tên thì "có tồn tại".
        """
        for name in api.__all__:
            value = getattr(api, name)
            if hasattr(value, "__name__") and getattr(value, "__file__", None):
                with self.subTest(name=name):
                    self.assertNotIn(str(API_DIR), value.__file__,
                                     "{} đang trỏ vào file mặt tiền, không phải module thật".format(name))

    def test_vung_khong_import_tu_chinh_src_api(self):
        """File vùng chỉ được import từ GÓI THẬT của nó, không được `from src.api import ...`."""
        for path in api_files():
            if path.name == "__init__.py":
                continue        # hub là chỗ DUY NHẤT được phép nói tới `src.api`
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if line.strip().startswith("from src.api"):
                    self.fail("{} dòng {}: vùng không được import từ src.api ({})".format(
                        path.name, number, line.strip()))


class NoCycleTest(unittest.TestCase):
    """(e): mã trong `src/` không được import mặt tiền, nếu không sẽ thành vòng import."""

    def test_ma_trong_src_khong_import_mat_tien(self):
        wrong = []
        for path in sorted((paths.root() / "src").rglob("*.py")):
            if API_DIR == path.parent or API_DIR in path.parents:
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                if IMPORT_LINE.match(line) and ".api" in line:
                    wrong.append("{}: {}".format(path.relative_to(paths.root()), line.strip()))
        self.assertEqual(wrong, [], "src/ không được import src.api: {}".format(wrong))


if __name__ == "__main__":
    unittest.main()
