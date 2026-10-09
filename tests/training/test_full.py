# -*- coding: utf-8 -*-
"""Test cách huấn luyện `full` (full fine-tune) và writer `state_dict` của nó.

VÌ SAO CẦN
Đây là mốc ĐỐI CHỨNG của cả nhóm LoRA ("cho model học TẤT CẢ thì hơn bao nhiêu?"), nên ba chỗ hỏng im
lặng phải bị chặn: (1) hợp đồng trainer; (2) có tham số nào đó KHÔNG được mở cho học - khi đó lượt chạy
mang tên "full fine-tune" mà thật ra chỉ học một phần; (3) checkpoint thiếu trọng số encoder - khi đó
bước suy luận chạy trên model GỐC và cho ra điểm của một lượt khác.

Chạy: python -m unittest discover -s tests
"""

import inspect
import json
import shutil
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from src.training import TRAINERS, full, lora, savers

try:
    import torch
    HAS_TORCH = True
except ImportError:                                   # CI không cài torch
    HAS_TORCH = False

needs_torch = unittest.skipUnless(HAS_TORCH, "cần torch")

# Cấu hình tối thiểu mà `settings()` (dùng chung với đường LoRA) đọc được. `model_id` là `visobert` vì
# máy nào cũng có file `configs/models/visobert.yaml`. `head.trainable: true` là cấu hình của một lượt
# full fine-tune thật (đầu phân loại cũng học).
CONFIG = {
    "trainer": "full",
    "lora": {"r": 8, "alpha": 16, "dropout": 0.05, "target_modules": ["query", "value"]},
    "head": {"trainable": True, "aspect_marker": False},
    "lr": 0.0002, "batch": 4, "epochs": 1, "grad_accum": 2, "weight_decay": 0.01,
    "loss": {"type": "ce", "class_weight": "none"},
    "preprocess": {"max_length": 64},
    "inference": {"dtype": "auto", "batch_size": 4},
    "enabled": True,
}

# Thông báo "chưa cài thư viện" là chuyện của MÁY, không phải của cấu hình: CI cố ý KHÔNG cài
# `torch`/`transformers` (xem requirements-ci.txt), nên các bài kiểm cấu hình lọc đúng nhóm đó ra.
MISSING_LIB = "chưa cài thư viện"


class FullContractTest(unittest.TestCase):
    """Hợp đồng trainer: registry, các hàm bắt buộc, và `check()` nói đúng việc phải sửa."""

    def test_registered_under_its_own_name(self):
        self.assertIn(full.NAME, TRAINERS)
        self.assertIs(TRAINERS[full.NAME], full)

    def test_has_every_function_the_contract_requires(self):
        for function in ("check", "fit", "predict", "build_model", "describe", "settings"):
            self.assertTrue(callable(getattr(full, function, None)),
                            "full thiếu hàm {}()".format(function))

    def test_settings_is_the_shared_one_of_the_lora_path(self):
        self.assertIs(full.settings, lora.settings)

    def test_ready_config_has_no_config_problem(self):
        found = [item for item in full.check(dict(CONFIG), "visobert") if MISSING_LIB not in item]
        self.assertEqual(found, [])

    def test_disabled_training_is_reported(self):
        found = full.check(dict(CONFIG, enabled=False), "visobert")
        self.assertEqual(len(found), 1)
        self.assertIn("enabled", found[0])

    def test_wrong_trainer_name_is_reported(self):
        found = full.check(dict(CONFIG, trainer="lora"), "visobert")
        self.assertTrue(any("full" in item and "lora" in item for item in found), found)

    def test_unknown_model_is_reported(self):
        found = full.check(dict(CONFIG), "khong-co-model-nay")
        self.assertTrue(any("khong-co-model-nay" in item for item in found), found)

    def test_quantization_4bit_is_rejected(self):
        """4 bit ĐÓNG BĂNG trọng số gốc ⇒ đó là QLoRA, KHÔNG phải full fine-tune: phải bị từ chối."""
        config = dict(CONFIG, inference={"dtype": "auto", "batch_size": 4, "quantization": "4bit"})
        found = [item for item in full.check(config, "visobert") if MISSING_LIB not in item]
        self.assertTrue(any("QLoRA" in item for item in found), found)
        # Và `build_model` phải chặn TRƯỚC khi nạp model (nên phép kiểm này chạy được cả khi thiếu torch).
        with self.assertRaises(lora.TrainingError) as caught:
            full.build_model(dict(CONFIG, quantization="4bit", source="x"), "cuda",
                             n_aspects=7, n_codes=3)
        self.assertIn("QLoRA", str(caught.exception))

    def test_writer_is_the_state_dict_one(self):
        self.assertEqual(full.WRITER, "state_dict")

    def test_head_state_label_says_what_actually_learns(self):
        """Nhãn in ra phải khớp cấu hình: `head.trainable: false` là chuyện chạy được, KHÔNG được nói dối."""
        self.assertIn("TOÀN BỘ", full.head_state_of({"head_trainable": True}))
        self.assertIn("CHỈ encoder", full.head_state_of({"head_trainable": False}))

    def test_the_loop_is_not_copied(self):
        """`fit()` phải đi qua vòng lặp dùng chung, KHÔNG tự viết một vòng lặp thứ hai."""
        source = inspect.getsource(full.fit)
        self.assertIn("fit_generic", source)
        self.assertIn("writer_name=WRITER", source)
        self.assertIn("build=build_model", source)

    def test_predict_reuses_the_shared_inference_loop(self):
        self.assertIn("predict_generic", inspect.getsource(full.predict))


class FullBuildModelTest(unittest.TestCase):
    """Hai cổng chặn của `build_model` (không cần torch) + lượt dựng model thật (cần torch)."""

    def test_missing_aspect_counts_is_an_error(self):
        with self.assertRaises(lora.TrainingError) as caught:
            full.build_model(dict(CONFIG), "cpu")
        self.assertIn("n_aspects", str(caught.exception))

    def test_loading_a_checkpoint_of_another_head_architecture_is_an_error(self):
        """`head.pt` của hai kiến trúc không nạp lẫn nhau: lệch phải là LỖI, không tự hạ cấp."""
        folder = tempfile.mkdtemp(prefix="sentimentx-full-")
        self.addCleanup(shutil.rmtree, folder, ignore_errors=True)
        Path(folder, "head_config.json").write_text(
            json.dumps({"n_aspects": 7, "n_codes": 3, "aspect_marker": True}), encoding="utf-8")
        with self.assertRaises(lora.TrainingError) as caught:
            full.build_model(dict(CONFIG), "cpu", adapter_dir=folder)
        self.assertIn("KIẾN TRÚC", str(caught.exception))

    @needs_torch
    def test_every_parameter_is_trainable(self):
        """ĐỊNH NGHĨA của lượt này: KHÔNG được sót tham số nào bị đóng băng.

        Nếu ai đó "tái dùng" `lora.set_head_trainable` ở đây thì encoder bị đóng băng và lượt chạy mang
        tên full fine-tune trong khi thật ra chỉ học đầu phân loại - đúng loại lỗi test này phải bắt.
        """

        class Encoder(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.proj = torch.nn.Linear(4, 4)
                self.config = types.SimpleNamespace(hidden_size=4)

        with mock.patch("transformers.AutoModel") as auto:
            auto.from_pretrained = mock.Mock(return_value=Encoder())
            model, head = full.build_model(dict(CONFIG), "cpu", n_aspects=2, n_codes=3,
                                           trainable=True, source="test/dummy")
        frozen = [name for name, item in model.named_parameters() if not item.requires_grad]
        self.assertEqual(frozen, [])
        self.assertIs(head, model.head)
        self.assertTrue(all(item.requires_grad for item in model.head.parameters()))


class StateDictWriterTest(unittest.TestCase):
    """Writer của đường `full`: checkpoint phải chứa TRỌNG SỐ ENCODER, không chỉ đầu phân loại."""

    def writer(self):
        return savers.get(full.WRITER)

    def test_registered_with_the_contract_functions(self):
        self.assertIn(full.WRITER, savers.SAVERS)
        for function in ("save", "read_metadata", "check"):
            self.assertTrue(callable(getattr(self.writer(), function, None)),
                            "state_dict thiếu hàm {}()".format(function))

    def test_file_names_of_the_head_are_shared_with_the_other_writers(self):
        """`head.pt` + `head_config.json` là ĐỊNH DẠNG của đầu phân loại, không của một cách huấn luyện."""
        other = savers.get("head_only")
        self.assertEqual(self.writer().HEAD_CONFIG, other.HEAD_CONFIG)
        self.assertEqual(self.writer().HEAD_WEIGHTS, other.HEAD_WEIGHTS)
        self.assertEqual(self.writer().OPTIMIZER_FILE, other.OPTIMIZER_FILE)
        self.assertNotEqual(self.writer().MODEL_WEIGHTS, other.HEAD_WEIGHTS)

    def test_check_does_not_require_peft(self):
        """Full fine-tune KHÔNG có adapter, nên thiếu `peft` không phải vấn đề của writer này."""
        self.assertFalse(any("peft" in item for item in self.writer().check()))

    @needs_torch
    def test_saves_and_reads_back_the_whole_model(self):
        folder = tempfile.mkdtemp(prefix="sentimentx-state-")
        self.addCleanup(shutil.rmtree, folder, ignore_errors=True)
        model = torch.nn.Linear(4, 3)          # đóng vai "CẢ model"
        head_config = {"n_aspects": 1, "n_codes": 3, "codes": [0, 1, 2],
                       "aspects": ["price"], "aspect_marker": False}
        self.writer().save(folder, model=model, head=model, head_config=head_config,
                           optimizer=None, scheduler=None)
        self.assertTrue(Path(folder, self.writer().MODEL_WEIGHTS).is_file())
        self.assertEqual(self.writer().read_metadata(folder), head_config)
        # Đọc lại được vào một model MỚI: đó là điều bước suy luận cần, vì full fine-tune không còn trọng
        # số gốc nào trên Hugging Face để nạp thay.
        fresh = torch.nn.Linear(4, 3)
        fresh.load_state_dict(torch.load(str(Path(folder, self.writer().MODEL_WEIGHTS)),
                                         map_location="cpu"))
        self.assertTrue(torch.equal(fresh.weight, model.weight))
        # Đường đọc đầu phân loại DÙNG CHUNG của dự án cũng đọc được checkpoint này.
        self.assertEqual(lora.read_head_config(folder), head_config)

    @needs_torch
    def test_weights_only_skips_the_optimizer(self):
        folder = tempfile.mkdtemp(prefix="sentimentx-state-")
        self.addCleanup(shutil.rmtree, folder, ignore_errors=True)
        model = torch.nn.Linear(4, 3)
        optimizer = torch.optim.SGD(model.parameters(), lr=0.1)
        self.writer().save(folder, weights_only=True, model=model, head=model, head_config={},
                           optimizer=optimizer, scheduler=None)
        self.assertTrue(Path(folder, self.writer().MODEL_WEIGHTS).is_file())
        self.assertTrue(Path(folder, self.writer().HEAD_WEIGHTS).is_file())
        self.assertFalse(Path(folder, self.writer().OPTIMIZER_FILE).is_file())


if __name__ == "__main__":
    unittest.main()

