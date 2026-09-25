# -*- coding: utf-8 -*-
"""Test phần THUẦN của runner (không cần GPU, không cần model).

Điều được khoá: kiểu số dùng để nạp model phải chọn theo MÁY đang chạy. bf16 chỉ có từ Ampere trở
lên; T4 của Colab là Turing nên không có, và ép bf16 ở đó là hoặc lỗi, hoặc chậm bất thường. Đây là
lỗi thật đã gặp khi chuẩn bị chạy trên T4.

Chạy: python -m unittest discover -s tests
"""

import importlib.util
import unittest
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


if __name__ == "__main__":
    unittest.main()
