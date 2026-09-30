# -*- coding: utf-8 -*-
"""Test phần THUẦN của runner (không cần GPU, không cần model).

Bốn điều được khoá ở đây, đều là chỗ đã hoặc sẽ im lặng làm sai kết quả:

1. Kiểu số dùng để nạp model phải chọn theo MÁY đang chạy. bf16 chỉ có từ Ampere trở lên; T4 của
   Colab là Turing nên không có, và ép bf16 ở đó là hoặc lỗi, hoặc chậm bất thường.
2. `chat_template` rỗng thì `apply_chat_template` trả về chuỗi RỖNG mà KHÔNG báo lỗi - model sinh ra
   rác ở giữa, kèm thông báo chẳng liên quan. Lỗi thật: file `chat_template.jinja` 0 byte che mất
   template hợp lệ nằm trong `tokenizer_config.json`.
3. Cột `prompt` của bảng dự đoán phải là ĐÚNG thứ model nhận: đã cắt ở `max_length` và đã bỏ phần đệm
   BÊN TRÁI (`padding_side="left"`), nếu không thì prompt in ra bắt đầu bằng một loạt token đệm và
   người đọc tưởng model bị cho ăn rác.

Phần "cắt đúng đoạn model SINH RA" của `generate()` vẫn phải kiểm bằng lượt chạy thật: nó nằm sau
`model.generate`, mà một model giả ở đây chỉ chứng minh được chính cái phép cắt, không chứng minh được
phép cắt đó đúng với đầu ra của model.

Chạy: python -m unittest discover -s tests
"""

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.evaluation import runner

HAS_TORCH = importlib.util.find_spec("torch") is not None


class ComputeDtypeTest(unittest.TestCase):
    def test_may_ho_tro_bf16_thi_dung_bf16(self):
        self.assertEqual(runner.compute_dtype_name(True), "bfloat16")

    def test_t4_khong_co_bf16_thi_dung_fp16(self):
        self.assertEqual(runner.compute_dtype_name(False), "float16")

    @unittest.skipUnless(HAS_TORCH, "cần torch để đối chiếu tên với thuộc tính thật")
    def test_ten_kieu_so_khop_thuoc_tinh_cua_torch(self):
        import torch

        for flag in (True, False):
            name = runner.compute_dtype_name(flag)
            self.assertTrue(hasattr(torch, name))

    @unittest.skipUnless(HAS_TORCH, "cần torch")
    def test_hoi_torch_ho_tro_THAT_chu_khong_phai_gia_lap(self):
        """T4 là Turing: torch đời mới trả `is_bf16_supported()` = True vì có giả lập phần mềm.

        Hỏi bằng `including_emulation=False` thì mới biết máy có bf16 THẬT hay không. Nếu torch bị
        mock thành bản chỉ hỗ trợ giả lập, kết quả phải là fp16.
        """
        import torch

        with mock.patch.object(torch.cuda, "is_bf16_supported",
                               side_effect=lambda including_emulation=True: including_emulation):
            _dtype, name = runner._model_dtype(torch)
        self.assertEqual(name, "float16")


class FakeMask(list):
    """Mặt nạ boolean của MỘT hàng: `.bool()` trả về chính nó, giống `tensor.bool()`."""

    def bool(self):
        return self


class FakeIds(list):
    """Hàng id giống tensor: `hàng[mặt_nạ]` lọc theo mặt nạ boolean, và `.tolist()` như tensor."""

    def __getitem__(self, item):
        if isinstance(item, FakeMask):
            return FakeIds(value for value, keep in zip(self, item) if keep)
        return list.__getitem__(self, item)

    def tolist(self):
        return list(self)


class FakeTokenizer:
    """Tokenizer giả: đủ để `sent_prompts` và `_ensure_chat_template` chạy."""

    pad_token_id = 0

    def __init__(self, template=None):
        self.chat_template = template
        self.decoded = []

    def decode(self, ids, skip_special_tokens=True):
        self.decoded.append(list(ids))
        return "|".join(str(int(value)) for value in ids)


class SentPromptsTest(unittest.TestCase):
    """Cột `prompt` ghi lại ĐÚNG thứ model nhận, không phải bản prompt trên lý thuyết.

    Đây là chỗ duy nhất dựng lại prompt từ token id. Sai ở đây thì bảng dự đoán vẫn có prompt, chỉ là
    prompt không phải thứ model nhận - và người đọc tin nó.
    """

    def setUp(self):
        from src.evaluation import records
        self.column = records.PROMPT_COLUMN

    def inputs(self):
        return {
            "input_ids": [FakeIds([0, 0, 7, 8]), FakeIds([0, 9, 10, 11])],
            "attention_mask": [FakeMask([False, False, True, True]),
                               FakeMask([False, True, True, True])],
        }

    def test_without_the_prompt_column_nothing_is_decoded(self):
        """Bảng của model encoder không có cột `prompt`: không dịch gì, và trả ô rỗng."""
        tokenizer = FakeTokenizer()
        texts = runner.sent_prompts(tokenizer, self.inputs(), ["khác"])
        self.assertEqual(texts, ["", ""])
        self.assertEqual(tokenizer.decoded, [])

    def test_left_padding_is_stripped_before_decoding(self):
        """Đệm nằm BÊN TRÁI: không bỏ thì prompt in ra bắt đầu bằng token đệm (id 0)."""
        tokenizer = FakeTokenizer()
        texts = runner.sent_prompts(tokenizer, self.inputs(), [self.column])
        self.assertEqual(texts, ["7|8", "9|10|11"])

    def test_without_a_mask_the_whole_row_is_decoded(self):
        inputs = {"input_ids": [FakeIds([7, 8])]}
        tokenizer = FakeTokenizer()
        texts = runner.sent_prompts(tokenizer, inputs, [self.column])
        self.assertEqual(texts, ["7|8"])


class ChatTemplateTest(unittest.TestCase):
    """`chat_template` rỗng làm prompt RỖNG mà không báo lỗi - phải chặn trước khi nạp model."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="sentimentx-chat-template-"))
        self.addCleanup(shutil.rmtree, str(self.root), ignore_errors=True)

    def test_an_empty_jinja_file_does_not_mask_the_template_in_the_config(self):
        """Lỗi thật: file `chat_template.jinja` 0 byte che mất template hợp lệ trong config."""
        (self.root / "chat_template.jinja").write_text("", encoding="utf-8")
        (self.root / "tokenizer_config.json").write_text(
            json.dumps({"chat_template": "TỪ-CONFIG"}), encoding="utf-8")
        tokenizer = runner._ensure_chat_template(FakeTokenizer(), str(self.root))
        self.assertEqual(tokenizer.chat_template, "TỪ-CONFIG")

    def test_a_jinja_file_with_content_wins(self):
        (self.root / "chat_template.jinja").write_text("TỪ-JINJA", encoding="utf-8")
        (self.root / "tokenizer_config.json").write_text(
            json.dumps({"chat_template": "TỪ-CONFIG"}), encoding="utf-8")
        tokenizer = runner._ensure_chat_template(FakeTokenizer(), str(self.root))
        self.assertEqual(tokenizer.chat_template, "TỪ-JINJA")

    def test_a_list_of_templates_uses_the_first(self):
        """`tokenizer_config.json` có thể khai danh sách template (mỗi mục một điều kiện)."""
        (self.root / "tokenizer_config.json").write_text(
            json.dumps({"chat_template": [{"template": "ĐẦU"}, {"template": "SAU"}]}),
            encoding="utf-8")
        tokenizer = runner._ensure_chat_template(FakeTokenizer(), str(self.root))
        self.assertEqual(tokenizer.chat_template, "ĐẦU")

    def test_no_template_anywhere_stops_with_the_fix(self):
        with self.assertRaises(RuntimeError) as caught:
            runner._ensure_chat_template(FakeTokenizer(), str(self.root))
        self.assertIn("setup_qwen_model.ps1", str(caught.exception))

    def test_a_tokenizer_that_already_has_a_template_is_left_alone(self):
        tokenizer = runner._ensure_chat_template(FakeTokenizer("CÓ-SẴN"), "không-có-thư-mục")
        self.assertEqual(tokenizer.chat_template, "CÓ-SẴN")


class LoadAttemptsTest(unittest.TestCase):
    """Danh sách cách nạp model KHÔNG được vượt qua mức lượng hoá/kiểu số.

    Lỗi cũ (đã sửa 27/09/2026): danh sách trộn cả `4-bit` lẫn `bf16/fp16`, nên khi 4-bit nạp hỏng vì lý
    do runtime thì lượt chạy **âm thầm** dùng 16-bit - thư mục kết quả mang nhãn `4bit` mà số đo là của
    fp16/bf16. Test này khoá lại: mọi cách thử phải CÙNG một mức.
    """

    def test_cac_cach_thu_co_luong_hoa_deu_mang_quantization_config(self):
        attempts = runner._load_attempts("config-4bit", "dtype-fp16", "float16")
        self.assertTrue(attempts)
        for _label, kwargs in attempts:
            self.assertIn("quantization_config", kwargs)

    def test_cac_cach_thu_khong_luong_hoa_thi_khong_bao_gio_mang_quantization_config(self):
        attempts = runner._load_attempts(None, "dtype-fp16", "float16")
        self.assertTrue(attempts)
        for _label, kwargs in attempts:
            self.assertNotIn("quantization_config", kwargs)
        # Vẫn phải giữ nhiều biến thể: đó là khác biệt MÔI TRƯỜNG (accelerate có/không, transformers
        # bản mới dùng `dtype` còn bản cũ `torch_dtype`), không phải khác biệt phép đo.
        self.assertGreaterEqual(len(attempts), 2)


if __name__ == "__main__":
    unittest.main()
