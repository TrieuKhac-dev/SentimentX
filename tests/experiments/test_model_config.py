# -*- coding: utf-8 -*-
"""Test lớp config model (src/experiments/model_config.py): giải kiểu số và kiểm giá trị.

Ba điều được khoá ở đây, đều là chỗ đã hoặc sẽ IM LẶNG làm sai kết quả:

1. `inference.dtype` phải có TÁC DỤNG thật ở cả hai đường chạy: trước đây đường prompt tự chọn lấy
   (bỏ qua config) còn đường encoder có bản riêng, và bản đó hỏi sai về bf16 trên T4.
2. Khai tường minh mà máy không đáp ứng được là LỖI, KHÔNG hạ cấp - "config gán một đằng, chạy một
   nẻo" là lỗi im lặng mà `run_meta.json` cũng không gỡ được.
3. Gõ sai giá trị trong `inference.*` phải lộ ra ngay lúc nạp config.

Chạy: python -m unittest discover -s tests
"""

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.experiments import model_config

# `resolve_dtype` nạp `torch` khi kiểu số cần nó; CI KHÔNG cài torch (`requirements-ci.txt` rất ngắn),
# nên nhóm test này tự bỏ qua ở đó thay vì báo đỏ vì thiếu thư viện.
try:
    import torch  # noqa: F401
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


class FakeCuda:
    """`torch.cuda` giả: đủ để `bf16_supported` trả lời như máy thật."""

    def __init__(self, available=True, bf16=False, name="Tesla T4", emulate=True):
        self.available = available
        self.bf16 = bf16
        self.name = name
        self.emulate = emulate

    def is_available(self):
        return self.available

    def is_bf16_supported(self, including_emulation=True):
        # Mặc định của torch là True: GPU KHÔNG có bf16 vẫn trả "có" (chạy bằng giả lập phần mềm).
        if including_emulation:
            return self.bf16 or self.emulate
        return self.bf16

    def get_device_name(self, index=0):
        return self.name


class FakeTorch:
    """`torch` giả: `dtype` để dạng chuỗi, `dtype_name()` cắt tiền tố `torch.` như thật."""

    float32 = "torch.float32"
    float16 = "torch.float16"
    bfloat16 = "torch.bfloat16"

    def __init__(self, **kwargs):
        self.cuda = FakeCuda(**kwargs)


@unittest.skipUnless(HAS_TORCH, "cần torch (CI không cài torch)")
class ResolveDtypeTest(unittest.TestCase):
    def test_auto_tren_gpu_co_bf16_that_thi_dung_bf16(self):
        value = model_config.resolve_dtype("auto", "cuda", torch=FakeTorch(bf16=True))
        self.assertEqual(model_config.dtype_name(value), "bfloat16")

    def test_auto_tren_t4_khong_co_bf16_that_thi_dung_fp16(self):
        self.assertEqual(
            model_config.dtype_name(
                model_config.resolve_dtype("auto", "cuda", torch=FakeTorch(bf16=False))),
            "float16")

    def test_auto_tren_cpu_thi_dung_fp32(self):
        self.assertEqual(
            model_config.dtype_name(
                model_config.resolve_dtype("auto", "cpu", torch=FakeTorch(available=False))),
            "float32")

    def test_khai_bfloat16_ma_may_khong_co_bf16_that_la_loi(self):
        with self.assertRaises(ValueError) as caught:
            model_config.resolve_dtype("bfloat16", "cuda", torch=FakeTorch(bf16=False))
        message = str(caught.exception)
        self.assertIn("Tesla T4", message)          # nói đúng máy nào
        self.assertIn("inference.dtype", message)   # và đúng khoá cần sửa

    def test_khai_float16_tren_cpu_la_loi(self):
        with self.assertRaises(ValueError) as caught:
            model_config.resolve_dtype("float16", "cpu", torch=FakeTorch(available=False))
        self.assertIn("float16", str(caught.exception))

    def test_gia_tri_la_thi_bao_loi_kem_danh_sach_gia_tri_hop_le(self):
        with self.assertRaises(ValueError) as caught:
            model_config.resolve_dtype("bf16", "cuda", torch=FakeTorch())
        self.assertIn("float16", str(caught.exception))


VALID_CONFIG = (
    "model_id: zz-model\n"
    "checkpoint: test/checkpoint\n"
    "config_version: 1\n"
    "approach: prompt\n"
    "preprocess:\n"
    "  max_length: 128\n"
    "inference:\n"
    "  dtype: auto\n"
    "  quantization: 4bit\n"
    "  batch_size: 4\n"
)


class InferenceKeysTest(unittest.TestCase):
    """`inference.*` phải được kiểm NGAY lúc nạp config (trước đây không kiểm gì)."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="sentimentx-modelcfg-"))
        self.addCleanup(shutil.rmtree, str(self.root), ignore_errors=True)
        self.path = self.root / "zz-model.yaml"
        patcher = mock.patch.object(model_config, "config_path", return_value=self.path)
        patcher.start()
        self.addCleanup(patcher.stop)

    def write(self, text):
        self.path.write_text(text, encoding="utf-8")
        return model_config.load("zz-model")

    def test_config_hop_le_nap_duoc(self):
        config = self.write(VALID_CONFIG)
        self.assertEqual(config["inference"]["quantization"], "4bit")

    def test_dtype_go_sai_la_loi_kem_goi_y(self):
        with self.assertRaises(model_config.ModelConfigError) as caught:
            self.write(VALID_CONFIG.replace("dtype: auto", "dtype: bf16"))
        message = str(caught.exception)
        self.assertIn("inference.dtype", message)
        self.assertIn("bfloat16", message)

    def test_quantization_la_la_loi(self):
        with self.assertRaises(model_config.ModelConfigError) as caught:
            self.write(VALID_CONFIG.replace("quantization: 4bit", "quantization: 8bit"))
        self.assertIn("4bit", str(caught.exception))

    def test_quantization_null_nghia_la_khong_luong_hoa(self):
        config = self.write(VALID_CONFIG.replace("quantization: 4bit", "quantization: null"))
        self.assertIsNone(config["inference"]["quantization"])

    def test_inference_khong_phai_nhom_khoa_la_loi(self):
        text = ("model_id: zz-model\ncheckpoint: test/checkpoint\nconfig_version: 1\n"
                "approach: prompt\npreprocess:\n  max_length: 128\ninference: 4bit\n")
        with self.assertRaises(model_config.ModelConfigError) as caught:
            self.write(text)
        self.assertIn("inference", str(caught.exception))


class EnableThinkingTest(unittest.TestCase):
    """`preprocess.enable_thinking`: để TRỐNG khác `false`, và giá trị không phải bool là LỖI.

    Chỗ này đã gây hỏng thật: `Qwen/Qwen3-0.6B` mặc định BẬT suy nghĩ, nên ba lượt 02/10/2026 chỉ đọc
    được 3,33 / 1,36 / 1,73% vì model viết hết trần `max_new_tokens` trong khối ` thinking` rồi không
    in ra JSON. Vì thế "không khai" phải khác "khai false": không khai = giữ mặc định của model.
    """

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="sentimentx-thinking-"))
        self.addCleanup(shutil.rmtree, str(self.root), ignore_errors=True)
        self.path = self.root / "zz-model.yaml"
        patcher = mock.patch.object(model_config, "config_path", return_value=self.path)
        patcher.start()
        self.addCleanup(patcher.stop)

    def write(self, text):
        self.path.write_text(text, encoding="utf-8")
        return model_config.load("zz-model")

    def test_de_trong_nghia_la_none_khong_phai_false(self):
        self.write(VALID_CONFIG)
        self.assertIsNone(model_config.enable_thinking("zz-model"))

    def test_khai_false_thi_tra_false(self):
        self.write(VALID_CONFIG.replace("  max_length: 128\n",
                                        "  max_length: 128\n  enable_thinking: false\n"))
        self.assertIs(model_config.enable_thinking("zz-model"), False)

    def test_khai_true_thi_tra_true(self):
        self.write(VALID_CONFIG.replace("  max_length: 128\n",
                                        "  max_length: 128\n  enable_thinking: true\n"))
        self.assertIs(model_config.enable_thinking("zz-model"), True)

    def test_gia_tri_khong_phai_bool_la_loi(self):
        with self.assertRaises(model_config.ModelConfigError) as caught:
            self.write(VALID_CONFIG.replace("  max_length: 128\n",
                                            "  max_length: 128\n  enable_thinking: 1\n"))
        self.assertIn("preprocess.enable_thinking", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
