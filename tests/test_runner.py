# -*- coding: utf-8 -*-
"""Test phần THUẦN của runner (không cần GPU, không cần model).

Điều được khoá: kiểu số dùng để nạp model phải chọn theo MÁY đang chạy. bf16 chỉ có từ Ampere trở
lên; T4 của Colab là Turing nên không có, và ép bf16 ở đó là hoặc lỗi, hoặc chậm bất thường. Đây là
lỗi thật đã gặp khi chuẩn bị chạy trên T4.

Chạy: python -m unittest discover -s tests
"""

import importlib.util
import unittest

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


if __name__ == "__main__":
    unittest.main()
