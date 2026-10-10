# -*- coding: utf-8 -*-
"""Test đường ĐO và đường DÙNG đi cùng một cách cho Qwen3: `add_generation_prompt` và `enable_thinking`.

Vì sao khoá ở đây: `enable_thinking` chỉ được truyền cho `apply_chat_template` khi model (hoặc thí
nghiệm) KHAI nó. Truyền bừa cho model không có biến đó là sai, còn để trống khi model mặc định BẬT suy
nghĩ là lỗi tốn cả lượt chạy: `Qwen/Qwen3-0.6B` viết hết trần `max_new_tokens` trong khối ` thinking`
rồi không còn chỗ in JSON (03 lượt ngày 02/10/2026 chỉ đọc được 3,33 / 1,36 / 1,73%).

Không cần `transformers`: tokenizer được thay bằng vật giả ghi lại tham số nhận được.

Chạy: python -m unittest discover -s tests
"""

import sys
import types
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


class FakePadlessTokenizer:
    """Tokenizer giả GIỐNG MISTRAL: có `eos_token` nhưng KHÔNG có `pad_token`.

    Đây đúng là hình dạng tokenizer của `mistralai/Mistral-7B-Instruct-v0.3` - thứ làm lượt
    `mistral-7b-instruct-v0.3/prompt-cot/exp001` (10/10/2026) đổ ngay ở lô đầu tiên.
    """

    def __init__(self, pad=None, pad_id=None, eos="</s>", side="right"):
        self.pad_token = pad
        self.pad_token_id = pad_id
        self.eos_token = eos
        self.padding_side = side
        self.name_or_path = "zz/zz"


class EnsurePaddingTest(unittest.TestCase):
    """Chuẩn hoá tokenizer cho việc sinh theo LÔ: thiếu `pad_token` là lô đầu tiên đổ.

    `apply_chat_template(..., padding=True)` ném `ValueError: Asking to pad but the tokenizer does
    not have a padding token.`; còn đệm bên PHẢI thì không đổ mà làm SAI kết quả (câu ngắn nhất
    sinh tiếp từ token đệm), nên đây là cặp phải khoá cùng nhau.
    """

    def test_thieu_pad_thi_lay_eos_va_dem_ben_trai(self):
        found = FakePadlessTokenizer()
        done = qwen.ensure_padding(found)
        self.assertEqual(found.pad_token, "</s>")
        self.assertEqual(found.padding_side, "left")
        self.assertEqual(len(done), 2)

    def test_da_du_thi_khong_sua_gi(self):
        found = FakePadlessTokenizer(pad="<pad>", pad_id=0, side="left")
        self.assertEqual(qwen.ensure_padding(found), [])
        self.assertEqual(found.pad_token, "<pad>")
        self.assertEqual(found.padding_side, "left")

    def test_chi_sua_dung_phan_ben_phai(self):
        found = FakePadlessTokenizer(pad="<pad>", pad_id=0, side="right")
        self.assertEqual(qwen.ensure_padding(found), ["padding_side = left"])

    def test_co_pad_ma_thieu_id_cung_phai_lay_eos(self):
        """`pad_token_id` là thứ thư viện thật sự dùng để đệm; có chuỗi mà thiếu id vẫn hỏng."""
        found = FakePadlessTokenizer(pad="<pad>", pad_id=None, side="left")
        self.assertEqual(qwen.ensure_padding(found), ["pad_token = eos_token ('</s>')"])
        self.assertEqual(found.pad_token, "</s>")

    def test_khong_co_ca_eos_thi_dung_kem_ly_do(self):
        """Tự thêm token đệm là phải sửa `resize_token_embeddings` - không làm hộ, nhưng phải nói rõ."""
        with self.assertRaises(ValueError) as caught:
            qwen.ensure_padding(FakePadlessTokenizer(eos=None))
        self.assertIn("pad_token", str(caught.exception))

    def test_use_tokenizer_cung_chuan_hoa(self):
        """Tokenizer đưa từ BÊN NGOÀI (đường nạp model) cũng phải đi qua phép chuẩn hoá này."""
        found = FakePadlessTokenizer()
        with mock.patch.object(qwen, "_TOKENIZERS", {}):
            qwen.use_tokenizer(found, "zz-model")
            # Tra lại NGAY TRONG khối này: `_TOKENIZERS` là sổ nhớ của module, ra ngoài khối là
            # quay về sổ thật và phép tra sẽ đi nạp tokenizer từ Hugging Face.
            self.assertIs(qwen.tokenizer("zz-model"), found)
        self.assertEqual(found.pad_token, "</s>")
        self.assertEqual(found.padding_side, "left")

    def test_tokenizer_nap_xong_thi_chuan_hoa_ngay(self):
        """Cửa DUY NHẤT nạp tokenizer: đo (`token_stats`) và dùng (`build_inputs`) chung một bản."""
        found = FakePadlessTokenizer()
        fake_module = types.ModuleType("transformers")
        fake_module.AutoTokenizer = mock.Mock()
        fake_module.AutoTokenizer.from_pretrained = mock.Mock(return_value=found)
        with mock.patch.dict(sys.modules, {"transformers": fake_module}), \
                mock.patch.object(qwen, "_TOKENIZERS", {}), \
                mock.patch.object(qwen, "checkpoint", return_value="zz/zz"):
            loaded = qwen.tokenizer("zz-model")
        self.assertIs(loaded, found)
        self.assertEqual(found.pad_token, "</s>")
        self.assertEqual(found.padding_side, "left")


if __name__ == "__main__":
    unittest.main()
