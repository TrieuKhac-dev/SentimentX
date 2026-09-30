# -*- coding: utf-8 -*-
"""Test `scripts/clean.py`: chỉ xoá RÁC, và không bao giờ xoá thứ đang được git theo dõi.

VÌ SAO KHOÁ NHỮNG CA NÀY: công cụ xoá file thì phải chứng minh được là nó KHÔNG xoá nhầm. Ba nhóm
dưới đây là toàn bộ hợp đồng: xoá đúng thứ là rác, giữ nguyên mọi thứ khác (kể cả file tên giống rác
mà đang được git theo dõi), và `--dry-run` không đụng vào đĩa.

Chạy: python -m unittest discover -s tests
"""

import contextlib
import importlib.util
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from src.core import paths

SPEC = importlib.util.spec_from_file_location("clean", paths.root() / "scripts" / "clean.py")
clean = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(clean)


class CleanCase(unittest.TestCase):
    """Dựng một cây giả có git để kiểm cả luật 'file theo dõi thì không xoá'."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, relative, text="x"):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def track(self, relative):
        self.write(relative)
        subprocess.run(["git", "-C", str(self.root), "add", "-f", relative], check=True)

    def lines(self):
        collected = []
        clean.clean(self.root, log=collected.append)
        return "\n".join(collected)


class MustDeleteTest(CleanCase):
    def test_xoa_thu_muc_rac_va_file_rac(self):
        self.write("pkg/__pycache__/mod.cpython-313.pyc")
        self.write("pkg/sub/__pycache__/other.pyc")
        self.write("loose.pyc")
        self.write(".ipynb_checkpoints/note.ipynb")
        removed = clean.clean(self.root, log=lambda line: None)
        self.assertEqual(sorted(removed),
                         [".ipynb_checkpoints", "loose.pyc", "pkg/__pycache__",
                          "pkg/sub/__pycache__"])
        self.assertFalse((self.root / "pkg" / "__pycache__").exists())
        self.assertFalse((self.root / "loose.pyc").exists())
        self.assertTrue((self.root / "pkg" / "sub").is_dir(), "thư mục thật phải còn")

    def test_chay_lan_hai_thi_khong_con_gi(self):
        self.write("a/__pycache__/x.pyc")
        clean.clean(self.root, log=lambda line: None)
        self.assertEqual(clean.clean(self.root, log=lambda line: None), [])


class MustKeepTest(CleanCase):
    def test_giu_file_that_va_du_lieu(self):
        self.write("run_eda.py")
        self.write("data/models/.gitkeep")
        self.write("experiments/qwen3-0.6b/prompt-cot/exp001/results/abc/metrics.json")
        self.write(".env", "DAGSHUB_TOKEN=that\n")
        self.write("data/raw/cosmetics/v0.1.0/data_test.csv")
        clean.clean(self.root, log=lambda line: None)
        for relative in ("run_eda.py", "data/models/.gitkeep",
                         "experiments/qwen3-0.6b/prompt-cot/exp001/results/abc/metrics.json",
                         ".env", "data/raw/cosmetics/v0.1.0/data_test.csv"):
            self.assertTrue((self.root / relative).is_file(), "{} bị xoá nhầm".format(relative))

    def test_khong_xoa_file_dang_duoc_git_theo_doi_du_ten_giong_rac(self):
        """Tên khớp mẫu rác nhưng ĐANG được git theo dõi: giữ lại, và nói ra vì sao."""
        self.track("data/bang.pyc")
        self.write("rac.pyc")
        text = self.lines()
        self.assertTrue((self.root / "data" / "bang.pyc").is_file())
        self.assertFalse((self.root / "rac.pyc").exists())
        self.assertIn("GIỮ LẠI  data/bang.pyc", text)


class ModeTest(CleanCase):
    def test_chay_thanh_tien_trinh_hai_lan_thi_lan_hai_rong(self):
        """Chạy y như người dùng chạy (`python scripts/clean.py`): lần hai phải KHÔNG có gì để xoá.

        Ca thật: bản đầu của tool import `src.core.paths` để lấy gốc repo, nên CHÍNH NÓ ghi ra
        `src/core/__pycache__` - dọn rác mà tự sinh rác, và lần chạy sau lại thấy mục mới. Test này
        chạy tiến trình riêng nên bắt được đúng cái đó.
        """
        self.write("a/__pycache__/x.pyc")
        script = paths.root() / "scripts" / "clean.py"
        first = subprocess.run([sys.executable, str(script), "--root", str(self.root)],
                               capture_output=True, text=True, encoding="utf-8")
        second = subprocess.run([sys.executable, str(script), "--root", str(self.root)],
                                capture_output=True, text=True, encoding="utf-8")
        self.assertIn("Đã xoá 1 mục.", first.stdout)
        self.assertIn("Không có gì để xoá.", second.stdout)
        self.assertEqual(second.returncode, 0)

    def test_dry_run_khong_dung_vao_dia(self):
        target = self.write("pkg/__pycache__/x.pyc")
        self.write("rac.pyc")
        removed = clean.clean(self.root, dry_run=True, log=lambda line: None)
        self.assertEqual(len(removed), 2, "vẫn phải ĐẾM đúng số mục sẽ xoá")
        self.assertTrue(target.is_file())
        self.assertTrue((self.root / "rac.pyc").is_file())

    def test_main_tra_ve_0_va_in_ra_so_muc(self):
        self.write("rac.pyc")
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = clean.main(["--root", str(self.root)])
        self.assertEqual(code, 0)
        self.assertIn("Đã xoá 1 mục.", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
