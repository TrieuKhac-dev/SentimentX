# -*- coding: utf-8 -*-
"""Test bảng đo input thật (src/preprocessing/token_stats.py).

Một điều được khoá ở đây, vì nó là loại số liệu dùng để biện luận trong báo cáo:

    Cột đếm token `<unk>` phải là SỐ ĐẾM, không phải tỉ lệ làm tròn. Bảng cũ chỉ có `% token <unk>`,
    nên câu "tách từ giảm bao nhiêu token `<unk>`" (21.886 -> 14.302 trên train) phải đo bằng script
    riêng và không lưu lại được. Test này giữ cột đó khỏi bị bỏ quên khi thêm model mới.

Test chạy KHÔNG cần GPU, không cần tokenizer thật: `measure()` chỉ cần một dict "spec" có bốn hàm
(`tokenizer`, `encode`, `words`, `info`), nên ở đây dùng tokenizer giả có số token biết trước.

Chạy: python -m unittest discover -s tests
"""

import importlib.util
import unittest
from pathlib import Path
from unittest import mock

from src.experiments import model_config
from src.preprocessing import token_stats

ROOT = Path(__file__).resolve().parents[2]


def load_script(name):
    """Nạp một script ở gốc repo như module, để gọi thẳng hàm cần kiểm."""
    spec = importlib.util.spec_from_file_location(name, ROOT / "{}.py".format(name))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeTokenizer:
    """Tokenizer giả: đủ để `measure()` chạy, với `model_max_length` bé hơn ngưỡng cắt của spec."""

    model_max_length = 256
    unk_token_id = 0


class NoUnkTokenizer:
    """Tokenizer không khai báo token `<unk>` (như Qwen) - hai cột phải là `-`, KHÔNG phải `0`."""

    model_max_length = 256
    unk_token_id = None


def spec_for(tokenizer, encode, words=("vài", "từ")):
    """Spec tối thiểu mà `token_stats.measure` cần."""
    return {
        "model_id": "fake-model",
        "model_name": "fake-model",
        "max_length": 128,
        "tokenizer": lambda: tokenizer,
        "encode": lambda texts: encode,
        "words": lambda texts: len(words),
        "info": lambda: {"tokenizer": "tokenizer-giả", "segmenter": "không",
                        "vocab": 100, "unk_id": tokenizer.unk_token_id},
    }


class CountUnkTest(unittest.TestCase):
    def measure(self, spec):
        # `position_limits()` đọc config của các model THẬT (cache hoặc mạng) - không liên quan tới
        # phép đo này, nên khoá lại để test chạy được cả khi máy không có mạng.
        with mock.patch.object(token_stats, "position_limits", return_value={}):
            return token_stats.measure(spec, ["một review", "review hai"])

    def test_the_count_column_counts_the_unknown_tokens(self):
        # 7 token, trong đó 2 token là <unk>.
        metrics, _meta = self.measure(spec_for(FakeTokenizer(), [[1, 0, 1, 0, 2], [1, 1]]))
        self.assertEqual(metrics["số token <unk>"], 2)
        self.assertEqual(metrics["% token <unk>"], round(100 * 2 / 7, 2))

    def test_a_tokenizer_without_unk_reports_not_applicable_in_both_columns(self):
        metrics, _meta = self.measure(spec_for(NoUnkTokenizer(), [[1, 2], [3]]))
        self.assertEqual(metrics["số token <unk>"], token_stats.NOT_APPLICABLE)
        self.assertEqual(metrics["% token <unk>"], token_stats.NOT_APPLICABLE)

    def test_both_columns_are_in_the_table(self):
        self.assertIn("số token <unk>", token_stats.COLUMNS)
        self.assertIn("% token <unk>", token_stats.COLUMNS)
        # Cột đếm đứng ngay trước cột tỉ lệ: hai con số của cùng một thứ, đọc cạnh nhau.
        self.assertEqual(token_stats.COLUMNS.index("% token <unk>")
                         - token_stats.COLUMNS.index("số token <unk>"), 1)
        # Cả hai đều là cột SỐ ĐO (không phải cột truy vết), nên phải nằm trong phần số đo.
        self.assertIn("số token <unk>", token_stats.METRIC_COLUMNS)


class SpecsTest(unittest.TestCase):
    """Mỗi mục đo phải trỏ tới MỘT file cấu hình model có thật, và tên file là danh tính của mục đó.

    Vì sao khoá: cột `model` của bảng số liệu CHÍNH LÀ `model_id`, nên một mục ghi sai tên (hoặc trỏ
    tới model không còn file cấu hình) thì bảng số liệu mang một cái tên không tra được ra cấu hình nào,
    mà không có gì báo lỗi.
    """

    def test_moi_muc_tro_toi_mot_config_model_co_that(self):
        for spec in token_stats.MODELS:
            name = spec["model_id"]
            path = model_config.config_path(name)
            self.assertTrue(path.is_file(), "thiếu config {}".format(path))
            self.assertEqual(model_config.load(name)["model_id"], name)

    def test_dong_duoc_ghi_voi_model_id(self):
        spec = {"model_id": "qwen3-0.6b", "max_length": 2304}
        metrics = {column: 0 for column in token_stats.METRIC_COLUMNS}
        meta = {column: "-" for column in token_stats.TRACE_COLUMNS}
        self.assertEqual(token_stats._row(spec, "test", metrics, meta)[0], "qwen3-0.6b")


class MaxLengthNameTest(unittest.TestCase):
    """`--max-length` nhận TÊN FILE CẤU HÌNH; tên ngắn cũ (`qwen`) đã bỏ và phải lỗi kèm gợi ý."""

    def setUp(self):
        self.script = load_script("run_token_stats")

    def test_ten_ngan_cu_bi_tu_choi_kem_goi_y(self):
        with self.assertRaises(ValueError) as caught:
            self.script.parse_max_length(["qwen=1280"], ["qwen3-4b-instruct-2507"])
        self.assertIn("qwen3-4b-instruct-2507", str(caught.exception))

    def test_ten_model_id_duoc_nhan(self):
        with mock.patch.object(token_stats, "position_limits", return_value={}):
            self.assertEqual(
                self.script.parse_max_length(["qwen3-0.6b=1024"], ["qwen3-0.6b"]),
                {"qwen3-0.6b": 1024})


if __name__ == "__main__":
    unittest.main()
