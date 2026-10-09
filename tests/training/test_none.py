# -*- coding: utf-8 -*-
"""Test cách huấn luyện `none` (không gói adapter) và writer `head_only` của nó.

VÌ SAO CẦN
Cách huấn luyện này là ĐỐI CHỨNG ÂM của câu hỏi "tại sao phải huấn luyện", nên hai chỗ hỏng im lặng
phải bị chặn: (1) hợp đồng trainer (thiếu hàm, đăng ký sai tên) - hỏng thì preflight không thấy và lượt
chạy chết muộn; (2) writer nhận payload dùng chung có khoá `model` mà nó KHÔNG dùng - nếu nó không
nhận, lượt chạy chết ở bước ghi checkpoint, tức là sau khi đã chạy xong.

Chạy: python -m unittest discover -s tests
"""

import inspect
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from src.training import TRAINERS, lora, none, savers

try:
    import torch
    HAS_TORCH = True
except ImportError:                                   # CI không cài torch
    HAS_TORCH = False

needs_torch = unittest.skipUnless(HAS_TORCH, "cần torch")

# Cấu hình tối thiểu mà `settings()` (dùng chung với đường LoRA) đọc được. `model_id` là `visobert`
# vì máy nào cũng có file `configs/models/visobert.yaml`.
CONFIG = {
    "trainer": "none",
    "lora": {"r": 8, "alpha": 16, "dropout": 0.05, "target_modules": ["query", "value"]},
    "head": {"trainable": False, "aspect_marker": False},
    "lr": 0.0002, "batch": 4, "epochs": 1, "grad_accum": 2, "weight_decay": 0.01,
    "loss": {"type": "ce", "class_weight": "none"},
    "preprocess": {"max_length": 64},
    "inference": {"dtype": "auto", "batch_size": 4},
    "enabled": True,
}

# Thông báo "chưa cài thư viện" là chuyện của MÁY, không phải của cấu hình: CI cố ý KHÔNG cài
# `torch`/`transformers` (`requirements-ci.txt`). Hai bài kiểm dưới đây lọc đúng nhóm thông báo đó ra,
# để chúng vừa chạy được ở CI vừa vẫn kiểm được phần CẤU HÌNH và phần hợp đồng registry.
MISSING_LIB = "chưa cài thư viện"


class NoneContractTest(unittest.TestCase):
    """Hợp đồng trainer: registry, các hàm bắt buộc, và `check()` nói đúng việc phải sửa."""

    def test_registered_under_its_own_name(self):
        self.assertIn(none.NAME, TRAINERS)
        self.assertIs(TRAINERS[none.NAME], none)

    def test_has_every_function_the_contract_requires(self):
        for function in ("check", "fit", "predict", "build_model", "describe", "settings"):
            self.assertTrue(callable(getattr(none, function, None)),
                            "none thiếu hàm {}()".format(function))

    def test_settings_is_the_shared_one_of_the_lora_path(self):
        """Cùng một `settings()`: bản ghi lượt chạy (`encoder_run.log_config`) đọc các khoá `lora_*`,
        nên hai đường phải trả về CÙNG hình dạng dict."""
        self.assertIs(none.settings, lora.settings)

    def test_ready_config_has_no_config_problem(self):
        """Cấu hình hợp lệ thì `check()` KHÔNG được kêu lỗi cấu hình (thư viện thiếu là chuyện của máy)."""
        found = [item for item in none.check(dict(CONFIG), "visobert") if MISSING_LIB not in item]
        self.assertEqual(found, [])

    def test_disabled_training_is_reported(self):
        found = none.check(dict(CONFIG, enabled=False), "visobert")
        self.assertEqual(len(found), 1)
        self.assertIn("enabled", found[0])

    def test_wrong_trainer_name_is_reported(self):
        found = none.check(dict(CONFIG, trainer="lora"), "visobert")
        self.assertTrue(any("none" in item and "lora" in item for item in found), found)

    def test_unknown_model_is_reported(self):
        found = none.check(dict(CONFIG), "khong-co-model-nay")
        self.assertTrue(any("khong-co-model-nay" in item for item in found), found)

    def test_describe_says_it_has_no_adapter(self):
        self.assertIn("adapter", none.describe())

    def test_the_loop_is_not_copied(self):
        """`fit()` phải đi qua vòng lặp dùng chung, KHÔNG tự viết một vòng lặp thứ hai."""
        source = inspect.getsource(none.fit)
        self.assertIn("fit_generic", source)
        self.assertIn("writer_name=WRITER", source)
        self.assertIn("build=build_model", source)

    def test_predict_reuses_the_shared_inference_loop(self):
        self.assertIn("predict_generic", inspect.getsource(none.predict))


class NoneBuildModelTest(unittest.TestCase):
    """Hai cổng chặn của `build_model`.

    KHÔNG cần `torch`: `none.build_model` cố ý import thư viện nặng SAU hai phép kiểm này, nên cấu hình
    sai bị báo trước khi nạp model - và hai phép kiểm chạy được cả trên CI (nơi không cài `transformers`).
    """

    def test_missing_aspect_counts_is_an_error(self):
        with self.assertRaises(lora.TrainingError) as caught:
            none.build_model(dict(CONFIG), "cpu")
        self.assertIn("n_aspects", str(caught.exception))

    def test_loading_a_checkpoint_of_another_head_architecture_is_an_error(self):
        """`head.pt` của hai kiến trúc không nạp lẫn nhau: lệch phải là LỖI, không tự hạ cấp."""
        folder = tempfile.mkdtemp(prefix="sentimentx-none-")
        self.addCleanup(shutil.rmtree, folder, ignore_errors=True)
        Path(folder, "head_config.json").write_text(
            json.dumps({"n_aspects": 7, "n_codes": 3, "aspect_marker": True}), encoding="utf-8")
        with self.assertRaises(lora.TrainingError) as caught:
            none.build_model(dict(CONFIG), "cpu", adapter_dir=folder)
        self.assertIn("KIẾN TRÚC", str(caught.exception))


class HeadOnlyWriterTest(unittest.TestCase):
    """Writer của đường `none`: nhận payload DÙNG CHUNG (có khoá `model`) và đọc lại được."""

    @needs_torch
    def test_saves_and_reads_back_the_head(self):
        folder = tempfile.mkdtemp(prefix="sentimentx-headonly-")
        self.addCleanup(shutil.rmtree, folder, ignore_errors=True)
        head = torch.nn.Linear(4, 3)
        head_config = {"n_aspects": 1, "n_codes": 3, "codes": [0, 1, 2],
                       "aspects": ["price"], "aspect_marker": False}
        optimizer = torch.optim.SGD(head.parameters(), lr=0.1)
        # `model=` có mặt vì vòng lặp huấn luyện dùng chung chuyển tiếp NGUYÊN payload cho mọi writer;
        # writer này nhận rồi bỏ qua. Thiếu tham số đó là TypeError ở bước ghi checkpoint.
        savers.get(none.WRITER).save(folder, model=object(), head=head, head_config=head_config,
                                     optimizer=optimizer, scheduler=None)
        self.assertTrue(Path(folder, "head.pt").is_file())
        self.assertEqual(savers.get(none.WRITER).read_metadata(folder), head_config)
        # `read_head_config` của đường LoRA đọc được checkpoint của `none`: cùng ĐỊNH DẠNG đầu phân loại.
        self.assertEqual(lora.read_head_config(folder), head_config)

    @needs_torch
    def test_weights_only_skips_the_optimizer(self):
        folder = tempfile.mkdtemp(prefix="sentimentx-headonly-")
        self.addCleanup(shutil.rmtree, folder, ignore_errors=True)
        head = torch.nn.Linear(4, 3)
        optimizer = torch.optim.SGD(head.parameters(), lr=0.1)
        savers.get(none.WRITER).save(folder, weights_only=True, head=head, head_config={},
                                     optimizer=optimizer, scheduler=None)
        self.assertFalse(Path(folder, "optimizer.pt").is_file())

    def test_writer_is_registered_and_has_the_contract(self):
        module = savers.get(none.WRITER)
        self.assertEqual(none.WRITER, module.NAME)
        for function in ("save", "read_metadata", "check"):
            self.assertTrue(callable(getattr(module, function, None)))
        self.assertEqual([item for item in module.check() if MISSING_LIB not in item], [])


if __name__ == "__main__":
    unittest.main()

