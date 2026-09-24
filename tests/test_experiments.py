# -*- coding: utf-8 -*-
"""Test tầng config thí nghiệm (src/experiments.py).

Chạy: python -m unittest discover -s tests

Vì sao cần: bảy lớp config chồng lên nhau, nên một khoá có thể bị lớp sau ghi đè mà không ai
biết, hoặc một khoá gõ sai tên có thể tồn tại mà không chỗ nào đọc. Cả hai loại lỗi đó đều
KHÔNG gây exception - chỉ làm cho kết quả chạy không đúng như người viết config tưởng.

Test ghi vào cây thật (`configs/models/`, `experiments/`) vì định nghĩa thí nghiệm theo thiết kế
nằm trong repo; mọi thứ được tạo ra đều được xoá trong tearDown.
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src import experiments, model_config, paths

TEST_MODEL = "zz-test-model"
TEST_METHOD = "test-method"
TEST_EXP = "exp001"

MODEL_CONFIG = (
    "model_id: {}\n"
    "checkpoint: test/checkpoint\n"
    "config_version: 1\n"
    "task:\n"
    "  label_space: full\n"
    "preprocess:\n"
    "  max_length: 128\n"
).format(TEST_MODEL)

BASE_CONFIG = (
    "exp_id: exp001\n"
    "parent: null\n"
    "model: {}\n"
    "method: {}\n"
    "data:\n"
    "  dataset: cosmetics\n"
    "  version: v0.1.0\n"
    "  roles: {{train: train, val: val, eval: test}}\n"
    "prompt: prompt.txt\n"
).format(TEST_MODEL, TEST_METHOD)

PROMPT_TEXT = "Phan tich review sau va tra ve JSON.\n{aspest} {text}\n"


class ExperimentCase(unittest.TestCase):
    """Lớp cha: dựng một thí nghiệm tạm rồi xoá trong tearDown."""

    def setUp(self):
        self.model_path = model_config.config_path(TEST_MODEL)
        self.exp_dir = experiments.experiment_dir(TEST_MODEL, TEST_METHOD, TEST_EXP)
        self.write_experiment()
        self.addCleanup(self.cleanup)

    def write_experiment(self, extra="", prompt=PROMPT_TEXT):
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        self.model_path.write_text(MODEL_CONFIG, encoding="utf-8")
        self.exp_dir.mkdir(parents=True, exist_ok=True)
        (self.exp_dir / "config.yaml").write_text(BASE_CONFIG + extra, encoding="utf-8")
        (self.exp_dir / "prompt.txt").write_text(prompt, encoding="utf-8")

    def cleanup(self):
        self.model_path.unlink(missing_ok=True)
        shutil.rmtree(paths.experiments_dir() / TEST_MODEL, ignore_errors=True)
        root = paths.experiments_dir()
        if root.is_dir() and not any(root.iterdir()):
            root.rmdir()

    def load(self, extra="", prompt=PROMPT_TEXT):
        self.write_experiment(extra, prompt)
        return experiments.load(TEST_MODEL, TEST_METHOD, TEST_EXP)


class TestMerge(ExperimentCase):
    def test_layers_are_merged_in_documented_order(self):
        result = self.load()
        labels = [label for label, _path in result["layers"]]
        self.assertEqual(labels, ["model", "repo", "task", "evaluation",
                                  "training", "tracking", "experiment"])

    def test_each_key_remembers_which_layer_set_it(self):
        result = self.load()
        sources = result["sources"]
        self.assertEqual(sources["preprocess.max_length"], "model")
        self.assertEqual(sources["label_space"], "model.task")
        self.assertEqual(sources["neutral_policy"], "task")
        self.assertEqual(sources["decoding.mode"], "evaluation")
        self.assertEqual(sources["batch"], "training")
        self.assertEqual(sources["tracker"], "tracking")
        self.assertEqual(sources["data.dataset"], "experiment")

    def test_model_task_block_beats_shared_task_file(self):
        """Khối `task` của model là ràng buộc của model nên phải thắng task.yaml."""
        result = self.load()
        self.assertEqual(result["config"]["label_space"], "full")
        self.assertEqual(result["sources"]["label_space"], experiments.MODEL_TASK_LAYER)

    def test_experiment_layer_overrides_shared_value(self):
        result = self.load(extra="n: 200\n")
        self.assertEqual(result["config"]["n"], 200)
        self.assertEqual(result["sources"]["n"], "experiment")
        self.assertIn(["n", None, 200, "experiment"], result["overrides"])

    def test_same_value_in_two_layers_is_not_reported_as_override(self):
        result = self.load(extra="decoding:\n  mode: greedy\n")
        self.assertEqual([row for row in result["overrides"] if row[0] == "decoding.mode"], [])

    def test_group_key_collision_is_an_error(self):
        """`checkpoint` là giá trị ở lớp model; khai lại thành nhóm ở lớp sau là lỗi."""
        with self.assertRaises(experiments.ExperimentError) as caught:
            self.load(extra="checkpoint:\n  every_n_steps: 1\n")
        self.assertIn("trùng tên khoá", str(caught.exception))

    def test_table_lists_every_leaf_with_its_source(self):
        rows = experiments.table(self.load())
        names = [row[0] for row in rows]
        self.assertIn("preprocess.max_length", names)
        self.assertIn("data.roles.eval", names)
        self.assertEqual(len(names), len(set(names)))


class TestFingerprint(ExperimentCase):
    def test_sha_is_64_hex_and_stable(self):
        first = experiments.config_sha256(self.load())
        second = experiments.config_sha256(self.load())
        self.assertEqual(len(first), 64)
        self.assertEqual(first, second)

    def test_changing_a_shared_value_changes_sha(self):
        before = experiments.config_sha256(self.load())
        result = self.load()
        result["config"]["n"] = 123
        self.assertNotEqual(before, experiments.config_sha256(result))

    def test_changing_prompt_text_changes_sha(self):
        before = experiments.config_sha256(self.load())
        after = experiments.config_sha256(self.load(prompt="Phan tich {text} (khac)\n"))
        self.assertNotEqual(before, after)

    def test_changing_examples_file_changes_sha(self):
        """`prompt_sha` không đổi khi đổi số ví dụ, nên vân tay phải bắt được thay đổi đó."""
        result = self.load(extra="examples: examples.txt\n")
        (self.exp_dir / "examples.txt").write_text("--- Vi du 1 ---\n{aspest}\n", encoding="utf-8")
        before = experiments.config_sha256(result)
        (self.exp_dir / "examples.txt").write_text(
            "--- Vi du 1 ---\n{aspest}\n--- Vi du 2 ---\n{aspest}\n", encoding="utf-8")
        self.assertNotEqual(before, experiments.config_sha256(result))

    def test_reordering_a_list_does_not_change_sha(self):
        result = self.load()
        first = experiments.config_sha256(result)
        reversed_modules = list(reversed(result["config"]["lora"]["target_modules"]))
        result["config"]["lora"]["target_modules"] = reversed_modules
        self.assertEqual(first, experiments.config_sha256(result))

    def test_line_endings_do_not_change_sha(self):
        """Văn bản prompt trên Windows là CRLF, trên Colab là LF: cùng cấu hình phải cùng dấu vân tay.

        Không chuẩn hoá thì báo cáo của hai máy mang hai `config_sha256` khác nhau, và người đọc
        tưởng đó là hai thí nghiệm.
        """
        result = self.load()
        text = experiments.prompt_merged(result)
        self.assertEqual(
            experiments.config_sha256(result, prompt_text=text.replace("\n", "\r\n")),
            experiments.config_sha256(result, prompt_text=text))

    def test_prompt_merged_has_all_three_parts(self):
        result = self.load(extra="examples: examples.txt\n")
        (self.exp_dir / "examples.txt").write_text("--- Vi du 1 ---\n{aspest}\n", encoding="utf-8")
        text = experiments.prompt_merged(result)
        self.assertIn("prompt.txt", text)
        self.assertIn("examples.txt", text)

    def test_prompt_without_text_placeholder_is_an_error(self):
        with self.assertRaises(experiments.ExperimentError):
            experiments.prompt_merged(self.load(prompt="Khong co o nho nao\n"))


class TestCheck(ExperimentCase):
    def test_valid_config_passes(self):
        experiments.check(self.load())

    def test_eval_at_train(self):
        result = self.load()
        result["config"]["data"]["roles"]["eval"] = "train"
        with self.assertRaises(experiments.ExperimentError) as caught:
            experiments.check(result)
        self.assertIn("rò rỉ dữ liệu", str(caught.exception))

    def test_missing_roles(self):
        result = self.load()
        result["config"]["data"].pop("roles")
        with self.assertRaises(experiments.ExperimentError) as caught:
            experiments.check(result)
        self.assertIn("data.roles", str(caught.exception))

    def test_unknown_key(self):
        result = self.load(extra="evaluation:\n  n: 200\n")
        with self.assertRaises(experiments.ExperimentError) as caught:
            experiments.check(result)
        self.assertIn("khoá lạ 'evaluation.n'", str(caught.exception))

    def test_role_name_typo(self):
        result = self.load()
        result["config"]["data"]["roles"]["trian"] = "train"
        with self.assertRaises(experiments.ExperimentError) as caught:
            experiments.check(result)
        self.assertIn("khoá lạ 'data.roles.trian'", str(caught.exception))

    def test_dataset_as_list(self):
        result = self.load()
        result["config"]["data"]["dataset"] = ["cosmetics", "khac"]
        with self.assertRaises(experiments.ExperimentError) as caught:
            experiments.check(result)
        self.assertIn("MỘT tên dataset", str(caught.exception))

    def test_role_with_unknown_split(self):
        result = self.load()
        result["config"]["data"]["roles"]["eval"] = "khong_co_split"
        with self.assertRaises(experiments.ExperimentError) as caught:
            experiments.check(result)
        self.assertIn("không có split đó", str(caught.exception))

    def test_training_needs_train_and_val(self):
        result = self.load()
        result["config"]["enabled"] = True
        result["config"]["data"]["roles"].pop("val")
        with self.assertRaises(experiments.ExperimentError) as caught:
            experiments.check(result)
        self.assertIn("vai 'val'", str(caught.exception))

    def test_all_problems_are_reported_at_once(self):
        result = self.load()
        result["config"]["data"]["roles"]["eval"] = "train"
        result["config"]["data"].pop("dataset")
        with self.assertRaises(experiments.ExperimentError) as caught:
            experiments.check(result)
        message = str(caught.exception)
        self.assertIn("thiếu 'data.dataset'", message)
        self.assertIn("rò rỉ dữ liệu", message)


class TestRequires(ExperimentCase):
    """`requires` và `check_requires`: dùng gốc dữ liệu tạm nên không phụ thuộc máy."""

    def setUp(self):
        super().setUp()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        patcher = mock.patch.dict(paths.os.environ, {paths.ENV_DATA_ROOT: self.tmp.name})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.version_id = "cosmetics-ds0.1.0-pl0.1.0-srccosmetics@0.1.0-deadbeef"
        self.processed = paths.processed(self.version_id)

    def touch_dataset(self):
        self.processed.mkdir(parents=True, exist_ok=True)
        for name in ("train.csv", "val.csv", "test.csv", "label_map.json"):
            (self.processed / name).write_text("x", encoding="utf-8")

    def test_requires_lists_roles_label_map_and_prompt(self):
        rows = experiments.requires(self.load(), self.version_id)
        roles = {row["role"]: row["display"] for row in rows}
        self.assertIn("data.roles.train", roles)
        self.assertIn("data.roles.eval", roles)
        self.assertIn("label_map", roles)
        self.assertIn("prompt", roles)
        self.assertTrue(roles["data.roles.eval"].endswith("test.csv"))

    def test_requires_extra_is_appended(self):
        rows = experiments.requires(
            self.load(extra="requires_extra: [data/models/qwen, khac.txt]\n"), self.version_id)
        self.assertEqual([row["role"] for row in rows][-2:],
                         ["requires_extra[1]", "requires_extra[2]"])

    def test_check_requires_reports_every_missing_path(self):
        with self.assertRaises(experiments.ExperimentError) as caught:
            experiments.check_requires(self.load(), self.version_id)
        message = str(caught.exception)
        self.assertIn("train.csv", message)
        self.assertIn("label_map.json", message)

    def test_check_requires_passes_when_files_exist(self):
        self.touch_dataset()
        self.assertEqual(experiments.check_requires(self.load(), self.version_id), [])


class TestDuplicateGuard(ExperimentCase):
    def setUp(self):
        super().setUp()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.version_id = "cosmetics-ds0.1.0-pl0.1.0-srccosmetics@0.1.0-deadbeef"

    def write_run_meta(self, folder, config_sha256=None, exp_id=None, ma=None):
        prints = experiments.fingerprint(self.load(), self.version_id)
        data = {
            "config_sha256": config_sha256 or prints["config_sha256"],
            "exp_id": exp_id or prints["exp_id"],
            "data": {"ma": ma or prints["ma"]},
        }
        path = self.root / folder / "run_meta.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_fingerprint_has_three_values(self):
        prints = experiments.fingerprint(self.load(), self.version_id)
        self.assertEqual(sorted(prints), ["config_sha256", "exp_id", "ma"])
        self.assertEqual(prints["exp_id"], TEST_EXP)

    def test_matching_run_is_found(self):
        written = self.write_run_meta("a")
        found = experiments.existing_runs(self.load(), self.version_id, root=self.root)
        self.assertEqual(found, [written])

    def test_different_config_or_exp_is_not_found(self):
        self.write_run_meta("a", config_sha256="0" * 64)
        self.write_run_meta("b", exp_id="exp999")
        self.write_run_meta("c", ma="khac")
        self.assertEqual(experiments.existing_runs(self.load(), self.version_id,
                                                   root=self.root), [])

    def test_broken_run_meta_does_not_break_the_scan(self):
        broken = self.root / "broken" / "run_meta.json"
        broken.parent.mkdir(parents=True, exist_ok=True)
        broken.write_text("{ khong phai json", encoding="utf-8")
        written = self.write_run_meta("a")
        found = experiments.existing_runs(self.load(), self.version_id, root=self.root)
        self.assertEqual(found, [written])

    def test_describe_runs_handles_empty_list(self):
        self.assertIn("Chưa có", experiments.describe_runs([])[0])


if __name__ == "__main__":
    unittest.main()
