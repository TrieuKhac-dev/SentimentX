# -*- coding: utf-8 -*-
"""Test đường ĐO và đường DÙNG đi cùng một cách cho Qwen3: `add_generation_prompt` và `enable_thinking`.

Vì sao khoá ở đây: `enable_thinking` chỉ được truyền cho `apply_chat_template` khi model (hoặc thí
nghiệm) KHAI nó. Truyền bừa cho model không có biến đó là sai, còn để trống khi model mặc định BẬT suy
nghĩ là lỗi tốn cả lượt chạy: `Qwen/Qwen3-0.6B` viết hết trần `max_new_tokens` trong khối ` thinking`
rồi không còn chỗ in JSON (03 lượt ngày 02/10/2026 chỉ đọc được 3,33 / 1,36 / 1,73%).

Không cần `transformers`: tokenizer được thay bằng vật giả ghi lại tham số nhận được.

Chạy: python -m unittest discover -s tests
"""

import unittest
from unittest import mock

from src.preprocessing import qwen


class FakeTokenizer:
    """Tokenizer giả: ghi lại mọi tham số được truyền cho `apply_chat_template`."""

    def __init__(self, rows=3):
        self.calls = []
        self.rows = rows

    def apply_chat_template(self, conversations, **kwargs):
        self.calls.append(kwargs)
        return [[1, 2, 3] for _ in range(len(conversations) or self.rows)]


class ChatKwargsTest(unittest.TestCase):
    def test_khong_khai_thi_khong_truyen_khoa(self):
        with mock.patch.object(qwen, "default_enable_thinking", return_value=None):
            kwargs = qwen._chat_kwargs(True, None, "zz-model")
        self.assertNotIn("enable_thinking", kwargs)
        self.assertTrue(kwargs["add_generation_prompt"])
        self.assertTrue(kwargs["tokenize"])

    def test_khai_false_thi_truyen_false(self):
        with mock.patch.object(qwen, "default_enable_thinking", return_value=False):
            kwargs = qwen._chat_kwargs(True, None, "zz-model")
        self.assertIs(kwargs["enable_thinking"], False)

    def test_tham_so_truyen_thang_thang_thang_gia_tri_cua_config(self):
        with mock.patch.object(qwen, "default_enable_thinking", return_value=False):
            kwargs = qwen._chat_kwargs(True, True, "zz-model")
        self.assertIs(kwargs["enable_thinking"], True)


class EncodePathTest(unittest.TestCase):
    """`encode()` phải đi qua CÙNG một đường với `build_inputs()` (đo và dùng không được lệch)."""

    def _encode(self, enable_thinking=None):
        fake = FakeTokenizer()
        with mock.patch.object(qwen, "tokenizer", return_value=fake), \
                mock.patch.object(qwen, "conversations",
                                  return_value=[{"role": "user", "content": "x"}]), \
                mock.patch.object(qwen, "default_enable_thinking", return_value=False), \
                mock.patch.object(qwen, "default_add_generation_prompt", return_value=True):
            rows = qwen.encode(["một review"], prompt_name="zz-prompt", model_id="zz-model",
                               enable_thinking=enable_thinking)
        return fake, rows

    def test_encode_truyen_enable_thinking_va_khong_tra_ve_dict(self):
        fake, rows = self._encode()
        self.assertEqual(rows, [[1, 2, 3]])
        self.assertIs(fake.calls[0]["enable_thinking"], False)
        self.assertIs(fake.calls[0]["return_dict"], False)

    def test_encode_nhan_tham_so_ghi_de_config(self):
        fake, _rows = self._encode(enable_thinking=True)
        self.assertIs(fake.calls[0]["enable_thinking"], True)


if __name__ == "__main__":
    unittest.main()
