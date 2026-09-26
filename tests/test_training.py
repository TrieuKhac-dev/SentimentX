# -*- coding: utf-8 -*-
"""Test đường chạy encoder: cấu hình model, lượt huấn luyện, và phần dùng chung với đường prompt.

Chạy: python -m unittest discover -s tests

Vì sao cần: đường này được thêm sau, và nó chạm vào những chỗ mà lỗi im lặng rất đắt - thiếu khoá
cấu hình thì phải biết TRƯỚC khi tải dữ liệu, checkpoint của lượt chạy khác thì không được dùng để
chạy tiếp, và ô neutral bị loại thì không được vào loss.
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src import model_config, paths
from src import encoder_run
from src import dataset as dataset_module
from src import versioning
from src.evaluation import records
from src.training import lora
from src.training import encoders, TRAINERS

try:
    import torch
    HAS_TORCH = True
except ImportError:                                   # CI không cài torch
    HAS_TORCH = False

needs_torch = unittest.skipUnless(HAS_TORCH, "cần torch")

MODEL_YAML = (
    "model_id: x\n"
    "checkpoint: test/x\n"
    "config_version: 1\n"
    "approach: {}\n"
    "preprocess:\n  max_length: 64\n"
)

BASE_CONFIG = {
    "approach": "encoder",
    "trainer": "lora",
    "lora": {"r": 8, "alpha": 16, "dropout": 0.05, "target_modules": ["query", "value"]},
    "lr": 0.0002, "batch": 4, "epochs": 1, "grad_accum": 2, "weight_decay": 0.01,
    "checkpoints": {"every_n_steps": 2, "keep_last_k": 1, "save_last": True, "save_best": True,
                    "delete_intermediate": True},
    "preprocess": {"max_length": 64},
    "inference": {"dtype": "auto", "batch_size": 4},
    "url": "https://example.invalid/repo",
    "branch": "experiment",
}


class ModelApproachTest(unittest.TestCase):
    """`approach` là khoá quyết định ĐƯỜNG CHẠY, nên sai hoặc thiếu phải là lỗi rõ."""

    def write(self, text):
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder, ignore_errors=True)
        path = Path(folder) / "x.yaml"
        path.write_text(text, encoding="utf-8")
        return path

    def test_missing_approach_is_an_error(self):
        path = self.write(MODEL_YAML.format("prompt").replace("approach: prompt\n", ""))
        with mock.patch.object(model_config, "config_path", return_value=path):
            with self.assertRaises(model_config.ModelConfigError) as caught:
                model_config.load("x")
        self.assertIn("approach", str(caught.exception))

    def test_unknown_approach_is_an_error(self):
        path = self.write(MODEL_YAML.format("khong-co"))
        with mock.patch.object(model_config, "config_path", return_value=path):
            with self.assertRaises(model_config.ModelConfigError) as caught:
                model_config.load("x")
        self.assertIn("prompt", str(caught.exception))

    def test_approach_of_prefers_the_merged_config(self):
        self.assertEqual(model_config.approach_of({"approach": "encoder"}), "encoder")

    def test_approach_of_falls_back_to_prompt_without_a_model_file(self):
        """Chạy tay với cấu hình không có file model: chỉ đường prompt chạy được."""
        self.assertEqual(model_config.approach_of({}, "khong-co-model-nay"), "prompt")

    def test_lora_targets_come_from_the_model_file(self):
        path = self.write(MODEL_YAML.format("encoder"))
        with mock.patch.object(model_config, "config_path", return_value=path):
            self.assertEqual(model_config.approach("x"), "encoder")


class SettingsTest(unittest.TestCase):
    """Thiếu khoá thì báo ĐÚNG khoá đó và chỉ nơi khai, không đoán hộ."""

    def test_missing_key_names_the_key(self):
        with self.assertRaises(lora.TrainingError) as caught:
            lora.settings({}, "visobert")
        self.assertIn("trainer", str(caught.exception))

    def test_missing_model_key_points_at_the_model_file(self):
        config = dict(BASE_CONFIG)
        config["lora"] = {"r": 8, "alpha": 16, "dropout": 0.05}
        with self.assertRaises(lora.TrainingError) as caught:
            lora.settings(config, "visobert")
        self.assertIn("lora.target_modules", str(caught.exception))
        self.assertIn("model", str(caught.exception))

    def test_unknown_dtype_is_an_error(self):
        config = dict(BASE_CONFIG, inference={"dtype": "float8", "batch_size": 4})
        with self.assertRaises(lora.TrainingError) as caught:
            lora.settings(config, "visobert")
        self.assertIn("float8", str(caught.exception))

    def test_settings_read_every_knob(self):
        found = lora.settings(BASE_CONFIG, "visobert")
        self.assertEqual(found["target_modules"], ["query", "value"])
        self.assertEqual(found["epochs"], 1)
        self.assertEqual(found["quantization"], "none")
        self.assertEqual(found["max_length"], 64)

    def test_check_without_enabled_says_so(self):
        self.assertTrue(lora.check({"enabled": False}, "visobert"))

    def test_check_reports_a_missing_model(self):
        found = lora.check(dict(BASE_CONFIG, enabled=True), "khong-co-encoder")
        self.assertTrue(any("encoder" in item for item in found), found)

    def test_registry_contents(self):
        self.assertIn("lora", TRAINERS)
        self.assertEqual(encoders.available(), ["phobert-base-v2", "visobert"])
        self.assertEqual(encoders.check(), [])


class CheckpointTest(unittest.TestCase):
    """`model/last` và `model/best` là hợp đồng của một lượt huấn luyện; sai đường dẫn là mất khả
    năng chạy tiếp, mà không có thông báo nào."""

    def setUp(self):
        self.out_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(self.out_dir), ignore_errors=True)

    def test_paths_come_from_the_paths_config(self):
        self.assertEqual(lora.checkpoint_dir(self.out_dir, "ckpt_last"),
                         self.out_dir / "model" / "last")
        self.assertEqual(lora.checkpoint_dir(self.out_dir, "ckpt_best"),
                         self.out_dir / "model" / "best")

    def test_snapshots_are_sorted_and_pruned(self):
        for step in (30, 10, 20):
            (self.out_dir / "model" / "checkpoint-{}".format(step)).mkdir(parents=True)
        self.assertEqual([item.name for item in lora.snapshots(self.out_dir)],
                         ["checkpoint-10", "checkpoint-20", "checkpoint-30"])
        self.assertEqual(lora.prune_snapshots(self.out_dir, 1),
                         ["checkpoint-10", "checkpoint-20"])
        self.assertEqual([item.name for item in lora.snapshots(self.out_dir)], ["checkpoint-30"])

    def test_resume_state_needs_the_same_fingerprint(self):
        folder = lora.checkpoint_dir(self.out_dir, "ckpt_last")
        folder.mkdir(parents=True)
        wanted = {"config_sha256": "a", "data": "d", "sha": "s"}
        lora.write_state(folder, {"fingerprint": dict(wanted)})
        self.assertEqual(lora.resume_state(self.out_dir, wanted)["fingerprint"], wanted)
        with self.assertRaises(lora.TrainingError):
            lora.resume_state(self.out_dir, {"config_sha256": "b", "data": "d", "sha": "s"})
        self.assertIsNone(
            lora.resume_state(self.out_dir, {"config_sha256": "b"}, require=False))

    def test_broken_state_file_counts_as_absent(self):
        folder = lora.checkpoint_dir(self.out_dir, "ckpt_last")
        folder.mkdir(parents=True)
        (folder / lora.STATE_FILE).write_text("{ khong-phai-json", encoding="utf-8")
        self.assertIsNone(lora.resume_state(self.out_dir, {"config_sha256": "a"}))


@needs_torch
class TorchModelTest(unittest.TestCase):
    """Ba tính chất phải đúng, vì sai chúng thì điểm số vẫn ra nhưng sai nghĩa."""

    def test_dropped_cells_become_class_zero(self):
        # Ô mã 3 là neutral bị loại (mask 0): chỉ số phải hợp lệ để tensor không lỗi.
        targets = lora.targets_from([[0, 1, 3], [2, 0, 3]], [0, 1, 2])
        self.assertEqual(targets.tolist(), [[0, 1, 0], [2, 0, 0]])

    def test_masked_loss_ignores_dropped_cells(self):
        logits = torch.zeros(1, 2, 2, dtype=torch.float32)
        logits[0, 0, 1] = 10.0     # ô 1: đoán đúng lớp đích
        logits[0, 1, 0] = 10.0     # ô 2: đoán sai hẳn
        targets = torch.tensor([[1, 1]])
        good = lora.masked_loss(logits, targets, torch.tensor([[1.0, 0.0]]), 2)
        bad = lora.masked_loss(logits, targets, torch.tensor([[0.0, 1.0]]), 2)
        self.assertLess(float(good), 0.01)
        self.assertGreater(float(bad), 5.0)

    def test_head_shape_follows_aspects_and_codes(self):
        class FakeEncoder(torch.nn.Module):
            """Encoder giả: chỉ cần `config.hidden_size` và `last_hidden_state`."""

            def __init__(self):
                super().__init__()
                self.config = type("C", (), {"hidden_size": 8})()
                self.linear = torch.nn.Linear(8, 8)

            def forward(self, input_ids, attention_mask):
                hidden = self.linear(torch.ones(input_ids.shape[0], 8))
                return type("O", (), {"last_hidden_state": hidden.unsqueeze(1)})()

        classifier_class, rows_class = lora.build_classes()
        model = classifier_class(FakeEncoder(), 7, 3)
        logits = model(torch.zeros(2, 3, dtype=torch.long), torch.ones(2, 3, dtype=torch.long))
        self.assertEqual(tuple(logits.shape), (2, 7, 3))
        self.assertEqual(len(rows_class(torch.zeros(2, 3), torch.ones(2, 3),
                                        torch.zeros(2, 7), torch.ones(2, 7))), 2)


def _has_dataset():
    """Dataset đã xử lý có trên đĩa không. CI không có dữ liệu (luật 20), nên phần này tự bỏ qua."""
    try:
        version_id = versioning.latest_dataset("cosmetics")
    except Exception:                                     # noqa: BLE001 - chỉ để bỏ qua test
        return False
    return bool(version_id) and paths.processed(version_id).is_dir()


HAS_DATASET = _has_dataset()
needs_dataset = unittest.skipUnless(HAS_DATASET, "cần dataset đã xử lý trên đĩa")


class IdentityTest(unittest.TestCase):
    """Dấu vân tay của lượt chạy encoder: tên thư mục, và đổi cấu hình là đổi dấu."""

    def test_hash_and_fingerprint_shape(self):
        found = encoder_run.identity(BASE_CONFIG, "ma-ds0.1.0", "visobert", "lora", "exp001")
        self.assertEqual(len(found["hash"]), 8)
        self.assertEqual(found["out_dir"].name, found["hash"])
        self.assertEqual(found["out_dir"].parent.name, "results")
        self.assertEqual(sorted(found["fingerprint"]),
                         ["config_sha256", "data", "sha"])

    def test_changing_a_training_knob_changes_the_hash(self):
        first = encoder_run.identity(BASE_CONFIG, "ma-ds0.1.0", "visobert", "lora", "exp001")
        other = dict(BASE_CONFIG, lr=0.0005)
        second = encoder_run.identity(other, "ma-ds0.1.0", "visobert", "lora", "exp001")
        self.assertNotEqual(first["config_sha256"], second["config_sha256"])
        self.assertNotEqual(first["hash"], second["hash"])

    def test_max_length_is_part_of_the_identity(self):
        """Ngưỡng cắt truyền từ dòng lệnh đổi phép đo, nên phải đổi dấu vân tay."""
        first = encoder_run.identity(BASE_CONFIG, "ma-ds0.1.0", "visobert", "lora", "exp001")
        second = encoder_run.identity(BASE_CONFIG, "ma-ds0.1.0", "visobert", "lora", "exp001",
                                      max_length=512)
        self.assertNotEqual(first["config_sha256"], second["config_sha256"])


class RolesTest(unittest.TestCase):
    def test_encoder_needs_three_roles(self):
        with self.assertRaises(encoder_run.EncoderRunError) as caught:
            encoder_run.roles_of({"data": {"roles": {"eval": "test"}}})
        self.assertIn("val", str(caught.exception))
        self.assertIn("train", str(caught.exception))

    def test_roles_are_returned_untouched(self):
        roles = {"train": "train", "val": "val", "eval": "test"}
        self.assertEqual(encoder_run.roles_of({"data": {"roles": roles}}), roles)


class PredictionRowsTest(unittest.TestCase):
    """Bảng dự đoán của encoder phải khớp cột với đường prompt, chỉ thiếu cột prompt."""

    def plan(self):
        return {"columns": records.columns(with_prompt=False), "aspects": ["smell", "price"],
                "row_index": [7], "split": "test", "texts": ["son thơm"], "golds": [{"smell": 1, "price": 0}]}

    def test_row_shape_and_values(self):
        rows = encoder_run.prediction_rows(self.plan(), [[1, 2]], seconds_per_sample=0.5)
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(rows[0]), len(self.plan()["columns"]))
        row = dict(zip(self.plan()["columns"], rows[0]))
        self.assertEqual(row["chỉ số"], "7")
        self.assertEqual(row["đọc được"], records.MENTIONED)
        self.assertEqual(row[records.REASON_COLUMN], "ok")
        self.assertEqual(json.loads(row["nhãn đoán"]), {"smell": 1, "price": 2})
        self.assertEqual(json.loads(row["nhãn đúng"]), {"smell": 1, "price": 0})
        self.assertNotIn(records.PROMPT_COLUMN, row)

    def test_rows_are_readable_by_the_scorer(self):
        plan = self.plan()
        rows = encoder_run.prediction_rows(plan, [[1, 2]])
        golds, preds, infos = records.to_arrays(rows, plan["aspects"])
        self.assertEqual(golds, [{"smell": 1, "price": 0}])
        self.assertEqual(preds, [{"smell": 1, "price": 2}])
        self.assertTrue(infos[0]["valid"])


@needs_dataset
class FitDataTest(unittest.TestCase):
    def test_labels_are_projected_and_masked(self):
        ds = dataset_module.load_config("cosmetics")
        version_id = versioning.compute_id(ds)
        config = dict(BASE_CONFIG, label_space="binary", neutral_policy="drop",
                      not_mentioned="separate", aspects="all")
        data, codes, _projection, aspects, _label_map = encoder_run.fit_data(
            config, version_id, ds, {"train": "train", "val": "val", "eval": "test"})

        self.assertEqual(codes, [0, 1, 2])
        self.assertEqual(aspects, ["stayingpower", "texture", "smell", "price", "colour",
                                   "shipping", "packing"])
        for role in encoder_run.REQUIRED_ROLES:
            self.assertEqual(len(data[role]["labels"]), len(data[role]["texts"]))
            self.assertEqual(len(data[role]["mask"]), len(data[role]["labels"]))
            self.assertEqual(len(data[role]["labels"][0]), len(aspects))
        # Ô neutral bị loại thì mask 0 - đó là cách "loại" mà KHÔNG mất các khía cạnh khác.
        dropped = sum(1 for row in data["train"]["mask"] for value in row if not value)
        self.assertGreater(dropped, 0)
        self.assertEqual(sum(1 for row in data["train"]["mask"] for value in row if value),
                         len(data["train"]["texts"]) * len(aspects) - dropped)

    def test_as_negative_keeps_neutral_cells(self):
        ds = dataset_module.load_config("cosmetics")
        version_id = versioning.compute_id(ds)
        config = dict(BASE_CONFIG, label_space="binary", neutral_policy="as_negative",
                      not_mentioned="separate", aspects="all")
        data, codes, _projection, _aspects, _label_map = encoder_run.fit_data(
            config, version_id, ds, {"train": "train", "val": "val", "eval": "test"})
        self.assertEqual(codes, [0, 1, 2])
        self.assertTrue(all(value for row in data["train"]["mask"] for value in row))
        self.assertTrue(any(code == 2 for row in data["train"]["labels"] for code in row))


@unittest.skipUnless(HAS_TORCH, "CI không cài torch")
class EncodeTest(unittest.TestCase):
    """`encode` phải nối được các lô có ĐỘ RỘNG khác nhau.

    Lỗi thật trên Colab: `build_inputs` pad theo văn bản dài nhất TRONG LÔ, nên lô đầu rộng 107 còn lô
    sau rộng 164, và `torch.cat` ném `RuntimeError: Sizes of tensors must match except in dimension 0`
    - chết ngay ở bước mã hoá tập train (~4.000 review). Phép chạy thử ở máy chỉ có 40 review nên chỉ
    một lô, không lộ ra; test này dựng NHIỀU lô với độ dài khác nhau.
    """

    class FakeModule:
        """Bắt chước `build_inputs` của module model: pad theo văn bản dài nhất trong lô."""

        def build_inputs(self, texts, max_length=None):
            import torch

            widths = [min(len(text), max_length or len(text)) for text in texts]
            width = max(widths)
            rows = [list(range(1, size + 1)) + [0] * (width - size) for size in widths]
            ids = torch.tensor(rows, dtype=torch.long)
            return {"input_ids": ids, "attention_mask": (ids != 0).long()}

    def test_chunks_of_different_width_are_padded_to_one_width(self):
        texts = ["a" * 3, "b" * 5, "c" * 40, "d" * 2, "e" * 17]
        ids, masks = lora.encode(self.FakeModule(), texts, max_length=64, batch=2)
        self.assertEqual(ids.shape, masks.shape)
        self.assertEqual(ids.shape[0], len(texts))
        self.assertEqual(ids.shape[1], 40)
        # Ô thêm vào là token pad: mask 0, nên model không nhìn thấy gì khác so với không pad.
        self.assertEqual(int(masks[0].sum()), 3)
        self.assertEqual(int(masks[2].sum()), 40)
        self.assertEqual(int(masks[4].sum()), 17)

    def test_a_single_chunk_keeps_its_own_width(self):
        """Một lô thì không pad thêm gì: số token tính vào attention không đổi so với trước."""
        ids, masks = lora.encode(self.FakeModule(), ["a" * 3, "b" * 9], max_length=64, batch=8)
        self.assertEqual(ids.shape[1], 9)
        self.assertEqual(int(masks[0].sum()), 3)

    def test_empty_input_gives_empty_tensors(self):
        ids, masks = lora.encode(self.FakeModule(), [], max_length=64)
        self.assertEqual(ids.shape, masks.shape)
        self.assertEqual(ids.shape[0], 0)


class PeftFailureTest(unittest.TestCase):
    """`peft` ném ImportError vì `torchao` cũ: thông báo phải có CÁCH SỬA.

    Lỗi thật trên Colab: `Found an incompatible version of torchao. Found version 0.10.0, but only
    versions above 0.16.0 are supported` làm chết lượt chạy LoRA sau khi đã tải và nạp xong model.
    Thông báo gốc chỉ nói về một gói mà dự án không dùng, nên người đọc không biết phải làm gì.
    """

    TORCHAO_TEXT = ("Found an incompatible version of torchao. Found version 0.10.0, but only "
                    "versions above 0.16.0 are supported")

    def test_torchao_failure_gets_the_uninstall_hint(self):
        message = str(lora._peft_error(ImportError(self.TORCHAO_TEXT)))
        self.assertIn("torchao", message)
        self.assertIn("pip uninstall -y torchao", message)
        self.assertIn("bootstrap", message)

    def test_other_peft_failures_keep_the_first_line_only(self):
        message = str(lora._peft_error(ImportError("cannot import name 'LoraConfig'\n  chi tiết")))
        self.assertIn("cannot import name 'LoraConfig'", message)
        self.assertNotIn("torchao", message)
        self.assertNotIn("chi tiết", message)


