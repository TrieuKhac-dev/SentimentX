# -*- coding: utf-8 -*-
"""Test hợp đồng file prompt (src/prompts.py, src/preprocessing/qwen.py).

Ba điều được khoá ở đây, đều là lỗi im lặng nếu sai:

1. Prompt khai bằng ĐƯỜNG DẪN phải dựng được ở bước sau, khi nơi gọi chỉ còn biết TÊN prompt
   (`build_inputs(prompt_name=...)`). Đường dẫn trong config tính từ thư mục thí nghiệm, mà thư mục
   đó không đi theo cái tên - nên nó phải được giải MỘT LẦN lúc nạp.
2. Ô nhớ `{system_prompt}` là một ô nhớ hợp lệ, và khối hệ thống đọc được ở cả hai cách viết:
   file chỉ có câu hệ thống, hoặc file có mục `[SYSTEM]`.
3. Thiếu khai niệm thì lỗi phải nói rõ thiếu khoá nào, chứ không dựng ra prompt thiếu nội dung.

Chạy: python -m unittest discover -s tests
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from src import prompts
from src.preprocessing import qwen

PROMPT_WITH_EXAMPLES = "[USER]\nXet review:\n{text}\n{examples}\n"
PROMPT_WITH_SYSTEM = "[SYSTEM]\n{system_prompt}\n\n[USER]\nXet review:\n{text}\n"

# Bảng mã nhãn tối thiểu để gọi `qwen.values` mà không cần đọc dữ liệu đã xử lý.
LABEL_MAP = {"aspects": ["smell"], "label_to_id": {"": 0, "positive": 1, "negative": 2},
             "id_to_label": {"0": "", "1": "positive", "2": "negative"}}


class PathPromptTest(unittest.TestCase):
    """Prompt và file đi kèm khai bằng đường dẫn tính từ thư mục thí nghiệm."""

    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix="sentimentx-prompts-"))
        self.addCleanup(shutil.rmtree, str(self.base), ignore_errors=True)

    def write(self, name, text):
        path = self.base / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_vi_du_theo_duong_dan_dung_duoc_khi_chi_con_biet_ten(self):
        """Lỗi thật đã gặp: `values()` gọi `prompts.examples(value)` không có `base_dir`."""
        self.write("prompt.txt", PROMPT_WITH_EXAMPLES)
        self.write("examples.txt", "--- Ví dụ 1 ---\nReview: \"a\"\nKẾT QUẢ: {\"smell\": 1}\n")
        prompt = qwen.load_prompt("prompt.txt", base_dir=self.base, examples="examples.txt")
        values = qwen.values("review thử", aspects=["smell"], label_map=LABEL_MAP, prompt=prompt)
        self.assertIn("Ví dụ 1", values["examples"])

    def test_khoi_he_thong_theo_duong_dan(self):
        self.write("prompt.txt", PROMPT_WITH_SYSTEM)
        self.write("system.txt", "Bạn là chuyên gia ABSA.\n")
        prompt = qwen.load_prompt("prompt.txt", base_dir=self.base, examples=None,
                                  system="system.txt")
        values = qwen.values("review thử", prompt=prompt)
        self.assertEqual(values["system_prompt"], "Bạn là chuyên gia ABSA.")

    def test_khoi_he_thong_co_muc_SYSTEM_cung_doc_duoc(self):
        self.write("prompt.txt", PROMPT_WITH_SYSTEM)
        self.write("system.txt", "[SYSTEM]\nChỉ trả JSON.\n\n[USER]\n(bỏ qua)\n")
        prompt = qwen.load_prompt("prompt.txt", base_dir=self.base, system="system.txt")
        values = qwen.values("review thử", prompt=prompt)
        self.assertEqual(values["system_prompt"], "Chỉ trả JSON.")

    def test_thieu_khoa_system_prompt_thi_bao_loi_ro(self):
        self.write("prompt.txt", PROMPT_WITH_SYSTEM)
        prompt = qwen.load_prompt("prompt.txt", base_dir=self.base)
        with self.assertRaises(prompts.PromptError) as caught:
            qwen.values("review thử", prompt=prompt)
        self.assertIn("system_prompt", str(caught.exception))

    def test_prompt_dung_system_prompt_nam_trong_o_nho_hop_le(self):
        self.write("prompt.txt", PROMPT_WITH_SYSTEM)
        prompt = qwen.load_prompt("prompt.txt", base_dir=self.base)
        self.assertIn("system_prompt", prompt.placeholders)


class SharedSystemTest(unittest.TestCase):
    """Tên trần của khối hệ thống trỏ vào configs/prompts/system/<tên>.txt."""

    def test_ten_tran_di_vao_thu_muc_system(self):
        _name, path = prompts.resolve("absa_cot", system=True)
        self.assertEqual(path, prompts.system_path("absa_cot"))
        self.assertTrue(path.is_file(), "thiếu configs/prompts/system/absa_cot.txt")

    def test_khoi_he_thong_dung_chung_doc_duoc(self):
        text = prompts.system("absa_cot")
        self.assertIn("ABSA", text)


class CacheKeyTest(unittest.TestCase):
    """Hai thí nghiệm khác file ví dụ thì KHÔNG được dùng chung một prompt đã nhớ."""

    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix="sentimentx-cache-"))
        self.addCleanup(shutil.rmtree, str(self.base), ignore_errors=True)

    def test_cung_ten_prompt_khac_file_vi_du_la_hai_prompt(self):
        for name, body in (("mot.txt", "--- Ví dụ 1 ---\nA\n"), ("hai.txt", "--- Ví dụ 1 ---\nB\n")):
            (self.base / name).write_text(body, encoding="utf-8")
        (self.base / "prompt.txt").write_text(PROMPT_WITH_EXAMPLES, encoding="utf-8")
        first = qwen.load_prompt("prompt.txt", base_dir=self.base, examples="mot.txt")
        second = qwen.load_prompt("prompt.txt", base_dir=self.base, examples="hai.txt")
        self.assertIsNot(first, second)


LABEL_MAP = {"aspects": ["smell"], "label_to_id": {"": 0, "positive": 1, "negative": 2},
             "id_to_label": {"0": "", "1": "positive", "2": "negative"}}

if __name__ == "__main__":
    unittest.main()
