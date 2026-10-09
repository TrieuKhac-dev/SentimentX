# -*- coding: utf-8 -*-
"""Test đường chạy encoder: cấu hình model, lượt huấn luyện, và phần dùng chung với đường prompt.

Chạy: python -m unittest discover -s tests

Vì sao cần: đường này được thêm sau, và nó chạm vào những chỗ mà lỗi im lặng rất đắt - thiếu khoá
cấu hình thì phải biết TRƯỚC khi tải dữ liệu, checkpoint của lượt chạy khác thì không được dùng để
chạy tiếp, và ô neutral bị loại thì không được vào loss.
"""

import contextlib
import inspect
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.experiments import experiments, model_config
from src.core import paths
from src.experiments import encoder_run
from src.core import dataset as dataset_module
from src.core import versioning
from src.evaluation import records
from src.training import lora
from src.training import checkpoints, encoders
from src.training import TRAINERS

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
    # Đầu phân loại: `trainable` = đóng băng (mặc định, hành vi của các lượt đã chạy);
    # `aspect_marker` = KHÍA CẠNH có đi vào đầu vào của đầu phân loại hay không (mục 14.7).
    "head": {"trainable": False, "aspect_marker": False},
    "lr": 0.0002, "batch": 4, "epochs": 1, "grad_accum": 2, "weight_decay": 0.01,
    "checkpoints": {"every_n_steps": 2, "keep_last_k": 1, "save_last": True, "save_best": True,
                    "delete_intermediate": True, "best_metric": "sentiment_f1"},
    "early_stop": {"enabled": False, "patience": 2, "min_delta": 0.0},
    "loss": {"type": "ce", "class_weight": "none"},
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
        self.assertIs(found["head_trainable"], False)

    def test_segmenter_di_toi_build_inputs(self):
        """`preprocess.segmenter` phải đi TỚI CHỖ chia văn bản, không chỉ để BÁO rồi bỏ qua.

        Lỗi thật đã sửa: `encode()` gọi `build_inputs()` mà không truyền bộ tách từ, nên một lượt
        khai `preprocess.segmenter: pyvi` vẫn chạy bằng bộ mặc định của module model - không có gì
        báo, và phép ĐO ảnh hưởng của việc tách từ biến thành kết luận RỖNG (mọi bộ ra cùng điểm).
        """
        self.assertIsNone(lora._segmenter({}))
        self.assertIsNone(lora._segmenter({"preprocess": {"segmenter": None}}))
        self.assertIsNone(lora._segmenter({"preprocess": {"segmenter": "   "}}))
        self.assertEqual(lora._segmenter({"preprocess": {"segmenter": " pyvi "}}), "pyvi")
        config = dict(BASE_CONFIG, preprocess={"max_length": 64, "segmenter": "underthesea"})
        self.assertEqual(lora.settings(config, "visobert")["segmenter"], "underthesea")

    def test_encode_chuyen_tiep_segmenter(self):
        """`encode()` phải CHUYỂN tiếp bộ tách từ xuống `build_inputs()` của module model."""
        seen = {}

        class FakeModule:
            @staticmethod
            def build_inputs(texts, max_length=None, segmenter=None):
                seen["segmenter"] = segmenter
                # Dừng ngay tại đây: điều đang kiểm là THAM SỐ đã tới, không phải phép mã hoá.
                raise RuntimeError("dừng")

        with self.assertRaises(RuntimeError):
            lora.encode(FakeModule, ["a", "b"], 64, segmenter="pyvi")
        self.assertEqual(seen["segmenter"], "pyvi")

    def test_check_without_enabled_says_so(self):
        self.assertTrue(lora.check({"enabled": False}, "visobert"))

    def test_check_reports_a_missing_model(self):
        found = lora.check(dict(BASE_CONFIG, enabled=True), "khong-co-encoder")
        self.assertTrue(any("encoder" in item for item in found), found)

    def test_registry_contents(self):
        self.assertIn("lora", TRAINERS)
        self.assertEqual(encoders.available(),
                         ["cafebert", "phobert-base-v2", "phobert-large", "vibert-base-cased",
                          "visobert", "xlm-roberta-base"])
        self.assertEqual(encoders.check(), [])


class CheckpointTest(unittest.TestCase):
    """Chính sách + chỗ lưu checkpoint dùng chung cho mọi cách huấn luyện
    (`src/training/checkpoints.py`); CÁCH GHI trọng số do writer quyết định (`src/training/savers/`).
    Sai đường dẫn là mất khả năng chạy tiếp mà không có thông báo nào."""

    def setUp(self):
        self.out_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(self.out_dir), ignore_errors=True)
        self.store = checkpoints.Store(self.out_dir, {
            "every_n_steps": 2, "keep_last_k": 1, "save_last": True, "save_best": True,
            "delete_intermediate": True})

    def test_paths_come_from_the_paths_config(self):
        self.assertEqual(self.store.last_dir(), self.out_dir / "model" / "last")
        self.assertEqual(self.store.best_dir(), self.out_dir / "model" / "best")
        self.assertEqual(self.store.snapshot_dir(30), self.out_dir / "model" / "checkpoint-30")

    def test_snapshots_are_sorted_and_pruned(self):
        for step in (30, 10, 20):
            self.store.snapshot_dir(step).mkdir(parents=True)
        self.assertEqual([item.name for item in self.store.snapshots()],
                         ["checkpoint-10", "checkpoint-20", "checkpoint-30"])
        self.assertEqual(self.store.prune(), ["checkpoint-10", "checkpoint-20"])
        self.assertEqual([item.name for item in self.store.snapshots()], ["checkpoint-30"])

    def test_resume_state_needs_the_same_fingerprint(self):
        folder = self.store.last_dir()
        folder.mkdir(parents=True)
        wanted = {"config_sha256": "a", "build": "d", "sha": "s"}
        self.store.write_state(folder, {"fingerprint": dict(wanted)})
        self.assertEqual(self.store.resume_state(wanted)["fingerprint"], wanted)
        with self.assertRaises(checkpoints.CheckpointError):
            self.store.resume_state({"config_sha256": "b", "build": "d", "sha": "s"})
        self.assertIsNone(self.store.resume_state({"config_sha256": "b"}, require=False))

    def test_broken_state_file_counts_as_absent(self):
        folder = self.store.last_dir()
        folder.mkdir(parents=True)
        (folder / checkpoints.STATE_FILE).write_text("{ khong-phai-json", encoding="utf-8")
        self.assertIsNone(self.store.resume_state({"config_sha256": "a"}))

    def test_store_saves_with_any_writer(self):
        """`Store` chỉ lo thư mục + state; CÁCH GHI trọng số do writer quyết định."""
        calls = []

        class FakeWriter:
            def save(self, directory, weights_only=False, **payload):
                calls.append((directory.name, weights_only, sorted(payload)))
                (directory / "weights.bin").write_text("x", encoding="utf-8")
                return directory

        self.store.save(self.store.last_dir(), FakeWriter(), {"fingerprint": {}}, {"model": "m"})
        self.assertTrue((self.store.last_dir() / "weights.bin").is_file())
        self.assertEqual(calls, [("last", False, ["model"])])

    def test_policy_must_be_declared(self):
        with self.assertRaises(checkpoints.CheckpointError) as caught:
            checkpoints.settings({})
        self.assertIn("checkpoints.every_n_steps", str(caught.exception))

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

    def test_aspect_marker_head_keeps_the_output_shape(self):
        """`head.aspect_marker` đổi KIẾN TRÚC nhưng KHÔNG đổi hình đầu ra `(B, 7, 3)`.

        Vì sao chốt bằng test: hai kiến trúc KHÔNG nạp `head.pt` lẫn nhau, nên nếu đầu ra khác hình
        thì lỗi chỉ hiện ở lúc chấm điểm (hoặc ở `load_state_dict`) - đúng loại lỗi muốn chặn sớm.
        """
        class FakeEncoder(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.config = type("C", (), {"hidden_size": 8})()
                self.linear = torch.nn.Linear(8, 8)

            def forward(self, input_ids, attention_mask):
                hidden = self.linear(torch.ones(input_ids.shape[0], 8))
                return type("O", (), {"last_hidden_state": hidden.unsqueeze(1)})()

        classifier_class, _rows = lora.build_classes()
        model = classifier_class(FakeEncoder(), 7, 3, aspect_marker=True)
        logits = model(torch.zeros(2, 3, dtype=torch.long), torch.ones(2, 3, dtype=torch.long))
        self.assertEqual(tuple(logits.shape), (2, 7, 3))
        # Đầu vào của đầu phân loại rộng thêm ĐÚNG số khía cạnh (one-hot ghép vào vector review).
        self.assertEqual(model.head.in_features, 8 + 7)

    def test_head_aspect_marker_phai_khai_va_phai_la_bool(self):
        """Thiếu khoá `head.aspect_marker`, hoặc giá trị không phải bool, đều là LỖI - không đoán.

        Vì sao: `bool("flase")` là `True`, nên một lỗi gõ ở đây BẬT một kiến trúc đầu phân loại khác
        mà không ai biết; còn thiếu khoá thì phải dừng kèm NƠI KHAI chứ không lặng lẽ dùng mặc định.
        """
        config = dict(BASE_CONFIG, head={"trainable": False})
        with self.assertRaises(lora.TrainingError) as caught:
            lora.settings(config, "visobert")
        self.assertIn("head.aspect_marker", str(caught.exception))
        config = dict(BASE_CONFIG, head={"trainable": False, "aspect_marker": "true"})
        with self.assertRaises(lora.TrainingError) as caught:
            lora.settings(config, "visobert")
        self.assertIn("phải là `true` hoặc `false`", str(caught.exception))


def _has_dataset():
    """Có ĐỦ dữ liệu để tính mã phiên bản không - tức cần CẢ dữ liệu gốc, không chỉ thư mục dataset.

    Vì sao không chỉ hỏi `latest_dataset`: bản clone CI VẪN có `data/processed/<mã>/` (các file
    JSON/`eda/`/`pipeline/` nằm trong git) nhưng KHÔNG có dữ liệu GỐC (luật 20). Hỏi theo processed
    thì thấy "có dataset" rồi chạy `compute_id`, mà hàm đó NÉM lỗi khi thiếu gốc - nên phải thử tính
    chính nó: ném thì coi như không có dữ liệu và bỏ qua test."""
    try:
        version_id = versioning.compute_id(dataset_module.load_config("cosmetics"))
    except Exception:                                     # noqa: BLE001 - chỉ để bỏ qua test
        return False
    return paths.processed(version_id).is_dir()


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
                         ["build", "config_sha256", "sha"])

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


class SilentLog:
    """Ghi nhận rỗng: `log_config` chỉ cần đối tượng có `.config()`."""

    def config(self, *args, **kwargs):
        pass


class EarlyStopSettingsTest(unittest.TestCase):
    """D-1: thiếu khoá `early_stop.*` là LỖI kèm nơi khai (không đặt mặc định trong code)."""

    def test_missing_key_is_a_clear_error(self):
        with self.assertRaises(lora.TrainingError) as caught:
            lora.early_settings({})
        self.assertIn("early_stop.enabled", str(caught.exception))

    def test_patience_must_be_at_least_one(self):
        config = {"early_stop": {"enabled": True, "patience": 0, "min_delta": 0.0}}
        with self.assertRaises(lora.TrainingError) as caught:
            lora.early_settings(config)
        self.assertIn("patience", str(caught.exception))

    def test_reads_the_policy(self):
        config = {"early_stop": {"enabled": True, "patience": 3, "min_delta": 0.01}}
        self.assertEqual(lora.early_settings(config),
                         {"enabled": True, "patience": 3, "min_delta": 0.01})


class BestMetricTest(unittest.TestCase):
    """D-2: `checkpoints.best_metric` là chuỗi, và phải nằm trong bộ chỉ số `measure()` tính."""

    def test_policy_keeps_the_metric_name(self):
        self.assertEqual(checkpoints.settings(BASE_CONFIG)["best_metric"], "sentiment_f1")

    def test_default_metric_is_in_the_measured_set(self):
        self.assertIn(checkpoints.settings(BASE_CONFIG)["best_metric"], lora.MEASURED_METRICS)


class LossSettingsTest(unittest.TestCase):
    """E-1: hàm mất mát khai trong config; `weighted_ce` phải đi kèm `class_weight: inverse`."""

    def test_missing_key_is_a_clear_error(self):
        with self.assertRaises(lora.TrainingError) as caught:
            lora.loss_settings({})
        self.assertIn("loss.type", str(caught.exception))

    def test_weighted_ce_requires_inverse(self):
        with self.assertRaises(lora.TrainingError) as caught:
            lora.loss_settings({"loss": {"type": "weighted_ce", "class_weight": "none"}})
        self.assertIn("inverse", str(caught.exception))

    def test_reads_the_policy(self):
        self.assertEqual(
            lora.loss_settings({"loss": {"type": "weighted_ce", "class_weight": "inverse"}}),
            {"type": "weighted_ce", "class_weight": "inverse"})


@needs_torch
class ClassWeightsTest(unittest.TestCase):
    """E-1: trọng số lớp là NGHỊCH ĐẢO tần suất, nên lớp hiếm được đẩy trọng số lên."""

    def test_rare_class_gets_a_larger_weight(self):
        weights = lora.class_weights([[0], [0], [0], [1]], [[1], [1], [1], [1]], [0, 1], "cpu")
        self.assertEqual(len(weights.tolist()), 2)
        self.assertGreater(weights.tolist()[1], weights.tolist()[0])

    def test_masked_cells_are_not_counted(self):
        weights = lora.class_weights([[0], [1]], [[1], [0]], [0, 1], "cpu")
        self.assertEqual(weights.tolist()[1], 0.0)


class EncoderRunGuardTest(unittest.TestCase):
    """A-4: lượt chạy encoder lỗi phải NGẮT PHIÊN Colab (không thì tốn quota GPU).

    `experiment_run.run` bọc thân trong `runtime.end_session_on_error()`, nhưng với model encoder nó
    `return encoder_run.run(...)` TRƯỚC khối đó - nên phần bọc phải nằm trong chính `encoder_run.run`.
    """

    def test_run_wraps_the_body_in_end_session(self):
        self.assertIn("end_session_on_error", inspect.getsource(encoder_run.run))


class LogConfigTest(unittest.TestCase):
    """A-1 (nửa thứ hai): `log_config` đọc được bộ khoá đã GỘP (lora + checkpoint)."""

    def test_reads_the_merged_training(self):
        training = {**lora.settings(BASE_CONFIG, "visobert"), **checkpoints.settings(BASE_CONFIG)}
        plan = {"config": dict(BASE_CONFIG, label_space="binary", neutral_policy="drop",
                               not_mentioned="separate"),
                "merged": {"overrides": []}, "model_id": "visobert", "method": "lora",
                "exp_id": "exp001", "version_id": "ma-ds0.1.0", "split": "test", "limit": None,
                "max_length": 64, "batch_size": 4, "device": "cpu", "seed": 42, "codes": [0, 1, 2],
                "training": training}
        encoder_run.log_config(plan, SilentLog())


@needs_dataset
class PlanTrainingKeysTest(unittest.TestCase):
    """A-1 (nửa thứ nhất): `plan()["training"]` phải có ĐỦ khoá chính sách checkpoint.

    `plan()` từng trả `lora.settings(...)` (KHÔNG có khoá checkpoint) còn `log_config` đọc
    `plan_data["training"]["every_n_steps"]` -> `KeyError` ngay sau khi mở MLflow (đã gặp thật với
    ViSoBERT).
    """

    def test_plan_training_carries_the_checkpoint_policy(self):
        merged = experiments.load("visobert", "lora", "exp001")
        ds = dataset_module.load_config("cosmetics")
        version_id = versioning.compute_id(ds)
        plan = encoder_run.plan(merged["config"], merged, ds, version_id)
        for key in checkpoints.POLICY_KEYS:
            self.assertIn(key, plan["training"], "thiếu khoá checkpoint '{}'".format(key))


class HeadTrainableTest(unittest.TestCase):
    """`head.trainable`: ĐÓNG BĂNG (mặc định) hay HỌC đầu phân loại.

    Vì sao khoá ở đây: `peft` đóng băng MỌI tham số không phải adapter, nên ở chế độ mặc định đầu phân
    loại không học - `head.pt` của bốn lượt LoRA đầu tiên giống nhau TỪNG BYTE giữa các checkpoint đã
    chứng minh điều đó. Sai khoá này là đổi CƠ CHẾ HỌC của lượt chạy, mà bảng điểm không hề nói ra.
    """

    def test_default_is_frozen_and_reads_as_false(self):
        self.assertIs(lora.settings(BASE_CONFIG, "visobert")["head_trainable"], False)

    def test_true_is_read_as_true(self):
        config = dict(BASE_CONFIG, head={"trainable": True, "aspect_marker": False})
        self.assertIs(lora.settings(config, "visobert")["head_trainable"], True)

    def test_missing_key_names_the_key(self):
        config = {key: value for key, value in BASE_CONFIG.items() if key != "head"}
        with self.assertRaises(lora.TrainingError) as caught:
            lora.settings(config, "visobert")
        self.assertIn("head.trainable", str(caught.exception))
        self.assertIn("05_experiments_shared", str(caught.exception))

    def test_a_string_value_is_an_error_not_a_truthy_guess(self):
        """`bool("flase")` là `True`: đoán hộ ở đây là BẬT một cơ chế học khác mà không ai biết."""
        config = dict(BASE_CONFIG, head={"trainable": "flase"})
        with self.assertRaises(lora.TrainingError) as caught:
            lora.settings(config, "visobert")
        self.assertIn("head.trainable", str(caught.exception))
        self.assertIn("flase", str(caught.exception))

    @needs_torch
    def test_set_head_trainable_unlocks_and_freezes_the_head(self):
        head = torch.nn.Linear(4, 3)
        self.assertEqual(lora.set_head_trainable(head, False), 0)
        self.assertFalse(any(item.requires_grad for item in head.parameters()))
        self.assertEqual(lora.set_head_trainable(head, True), 15)      # 4*3 + 3
        self.assertTrue(all(item.requires_grad for item in head.parameters()))

    @needs_torch
    def test_build_model_takes_the_flag(self):
        """`build_model` phải NHẬN cờ này: mặc định `False` là đường SUY LUẬN, quên truyền ở vòng lặp
        huấn luyện thì lượt CHẠY TIẾP chết ở `optimizer got an empty parameter list`.

        Vòng lặp huấn luyện DÙNG CHUNG nằm ở `fit_generic` (đợt 11 tách ra để cách huấn luyện `none`
        dùng lại), nên phép kiểm soi ĐÚNG chỗ đó, cộng một dòng chốt rằng `fit()` của LoRA đi qua
        chính nó: ai đó nối tắt thì cờ `trainable=True` lại biến mất khỏi đường chạy thật.
        """
        self.assertIn("trainable=True", inspect.getsource(lora.fit_generic))
        self.assertIn("fit_generic", inspect.getsource(lora.fit))
        self.assertIn("is_trainable=bool(trainable)", inspect.getsource(lora.build_model))
        self.assertIn("set_head_trainable", inspect.getsource(lora.build_model))


class HeadTrainableVisibleTest(unittest.TestCase):
    """Cơ chế đầu phân loại phải ĐỌC ĐƯỢC từ bản ghi: hai lượt cùng mọi con số khác chỉ khác khoá này,
    nên bản ghi không nói ra thì không ai biết lượt nào là lượt nào."""

    def plan(self, trainable):
        config = dict(BASE_CONFIG, head={"trainable": trainable, "aspect_marker": False})
        training = {**lora.settings(config, "visobert"), **checkpoints.settings(config)}
        return {"config": dict(config, label_space="binary", neutral_policy="drop",
                               not_mentioned="separate"),
                "merged": {"overrides": []}, "model_id": "visobert", "method": "lora",
                "exp_id": "exp001", "version_id": "ma-ds0.1.0", "split": "test", "limit": None,
                "max_length": 64, "batch_size": 4, "device": "cpu", "seed": 42, "codes": [0, 1, 2],
                "dataset": {"name": "cosmetics", "version": "v0.2.0"}, "roles": {"train": "train"},
                "names": ["accuracy"], "model": "test/x", "info": {"n_samples": 10},
                "training": training}

    def test_log_config_writes_the_head_state(self):
        entries = []

        class Recorder(object):
            def config(self, text):
                entries.append(text)

        encoder_run.log_config(self.plan(True), Recorder())
        self.assertTrue(any("đầu phân loại" in text and "HỌC" in text for text in entries), entries)

    def test_log_config_says_frozen_when_frozen(self):
        entries = []

        class Recorder(object):
            def config(self, text):
                entries.append(text)

        encoder_run.log_config(self.plan(False), Recorder())
        self.assertTrue(any("ĐÓNG BĂNG" in text for text in entries), entries)

    def test_run_record_carries_the_flag(self):
        self.assertIs(encoder_run.run_record(self.plan(False))["training"]["head_trainable"], False)
        self.assertIs(encoder_run.run_record(self.plan(True))["training"]["head_trainable"], True)

    def test_print_config_says_it_out_loud(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            encoder_run.print_config(self.plan(True))
        self.assertIn("head.trainable: true", buffer.getvalue())
        self.assertIn("HỌC cùng adapter", buffer.getvalue())

    def test_plan_info_carries_the_flag(self):
        """`info["training"]` là bộ thẻ đẩy lên MLflow: thiếu khoá này thì lượt đầu HỌC và lượt đầu
        ĐÓNG BĂNG mang cùng một bộ thẻ, lọc trên MLflow không tách được hai cơ chế."""
        self.assertIn('"head_trainable"', inspect.getsource(encoder_run.plan))


