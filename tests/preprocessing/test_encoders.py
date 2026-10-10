# -*- coding: utf-8 -*-
"""Test HỢP ĐỒNG của các encoder kiểu BERT: registry, tham số cắt, và bộ tách từ theo từng model.

Vì sao khoá ở đây: bốn encoder thêm ở đợt 7 dùng CHUNG mã (`bert_like.py`) và chỉ khác BA tham số
(checkpoint, tên cấu hình, có/không tách từ). Sai một trong ba thì lượt chạy vẫn ra số, chỉ là số của
model KHÁC - đúng loại lỗi im lặng mà test này chốt lại.

Chạy: python -m unittest discover -s tests
"""

import ast
import unittest

from src.core import paths
from src.experiments import model_config
from src.preprocessing import (bert_like, cafebert, phobert_large, token_stats, vibert, visobert,
                               xlmroberta)
from src.training import encoders

NEW_ENCODERS = ("phobert-large", "vibert-base-cased", "cafebert", "xlm-roberta-base")


class RegistryTest(unittest.TestCase):
    def test_moi_encoder_dang_ky_deu_co_du_hop_dong(self):
        problems = encoders.check()
        self.assertEqual(problems, [], "encoders.check() phải sạch: {}".format(problems))

    def test_bon_encoder_moi_da_co_mat(self):
        self.assertEqual(encoders.available(),
                         ["cafebert", "phobert-base-v2", "phobert-large", "vibert-base-cased",
                          "visobert", "xlm-roberta-base"])

    def test_moi_encoder_co_du_ham_ma_huan_luyen_can(self):
        for name in encoders.available():
            module = encoders.get(name)
            for function in ("limit", "tokenizer", "encode", "build_inputs", "info"):
                self.assertTrue(callable(getattr(module, function, None)),
                                "{}.{} phải là hàm".format(name, function))


class ModelChoiceTest(unittest.TestCase):
    """Ba tham số khác nhau của bốn encoder mới - sai một cái là số của model khác."""

    def test_checkpoint_khop_voi_tai_lieu(self):
        for module, expected in ((phobert_large, "vinai/phobert-large"),
                                 (vibert, "FPTAI/vibert-base-cased"),
                                 (cafebert, "uitnlp/CafeBERT"),
                                 (xlmroberta, "FacebookAI/xlm-roberta-base")):
            self.assertEqual(module.MODEL_NAME, expected)
            self.assertEqual(model_config.checkpoint(module.CONFIG_NAME), expected)

    def test_model_tach_tu_va_khong_tach_tu(self):
        # PhoBERT-large và ViBERT học trên văn bản ĐÃ tách từ; CafeBERT và XLM-R dùng SentencePiece.
        self.assertEqual(phobert_large.SEGMENTER, "auto")
        self.assertEqual(vibert.SEGMENTER, "auto")
        self.assertEqual(cafebert.SEGMENTER, "none")
        self.assertEqual(xlmroberta.SEGMENTER, "none")

    def test_nguong_cat_doc_tu_config_va_duoi_tran_kien_truc(self):
        # Trần kiến trúc ĐÃ ĐO: PhoBERT (cả hai bản) 258, ViBERT 512, CafeBERT và XLM-R 514.
        for module, ceiling in ((phobert_large, 258), (vibert, 512), (cafebert, 514),
                                (xlmroberta, 514)):
            value, source = module.limit()
            self.assertEqual(value, 256)
            self.assertLess(value, ceiling,
                            "{}: ngưỡng 256 phải dưới trần {}".format(module.CONFIG_NAME, ceiling))
            self.assertIn(module.CONFIG_NAME, source)

    def test_bert_like_chi_tach_tu_khi_duoc_yeu_cau(self):
        texts = ["Đại học Quốc gia"]
        self.assertEqual(bert_like.prepared(texts, "none"), texts)   # giữ nguyên bản
        self.assertEqual(bert_like.segmenter_name("none"), "none")


class TokenStatsRegistryTest(unittest.TestCase):
    """Bảng đo token phải phủ MỌI model của dự án - thiếu một model là bảng gộp thiếu dòng."""

    def test_nam_model_moi_co_mat(self):
        ids = [spec["model_id"] for spec in token_stats.MODELS]
        for name in NEW_ENCODERS + ("qwen2.5-0.5b-instruct", "qwen3-8b",
                                    "qwen3-4b-thinking-2507", "mistral-7b-instruct-v0.3"):
            self.assertIn(name, ids)
        # 6 encoder + 6 model sinh. Đợt 11 thêm BA model sinh (hai bản Qwen3 và một họ KHÁC - Mistral).
        # HAI model của đợt 11 (`llama-3.1-8b-instruct`, `vistral-7b-chat`) là repo GATED nên CHƯA đăng ký
        # được: đăng ký một model không tải nổi tokenizer là làm hỏng phép đo của MỌI model khác trong
        # cùng lần chạy - xem present_plan_batch11.md mục 7.
        self.assertEqual(len(ids), 12)

    def test_moi_muc_co_du_ham_va_ten_model_khop_config(self):
        for spec in token_stats.MODELS:
            for key in ("limit", "encode", "words", "tokenizer", "info", "model_name", "model_id"):
                self.assertIn(key, spec, "{} thiếu khoá {}".format(spec.get("model_id"), key))
            self.assertEqual(spec["model_name"], model_config.checkpoint(spec["model_id"]))


class EncoderModuleImportTest(unittest.TestCase):
    """Module dùng `X.` thì phải import `X` - thiếu là NameError lúc HUẤN LUYỆN, không lộ khi ĐO.

    Ca thật (batch 11, 10/10/2026): `visobert.build_inputs` gọi `bert_like.prepared` mà KHÔNG import
    `bert_like`, nên bốn lượt `visobert/lora/exp006-009` đổ ngay ở bước dựng input với
    `NameError: name 'bert_like' is not defined` - trong khi `encode()` (đường ĐO) vẫn chạy được, nên
    lỗi chỉ hiện ở đường huấn luyện. Dùng AST để soi đúng phép truy cập thuộc tính, tránh nhầm với
    chữ `bert_like.py` trong docstring.
    """

    SIBLINGS = ("bert_like", "segmenters", "model_config")

    @staticmethod
    def imported_names(tree):
        """Tên được import ở cấp module (kể cả dạng có ngoặc) - dò bằng AST, không so chuỗi."""
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    names.add(alias.asname or alias.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    names.add(alias.asname or alias.name.split(".")[0])
        return names

    def test_moi_module_dung_module_anh_em_deu_import(self):
        directory = paths.root() / "src" / "preprocessing"
        missing = []
        for path in sorted(directory.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            used = {node.value.id for node in ast.walk(tree)
                    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)}
            imported = self.imported_names(tree)
            for name in self.SIBLINGS:
                if name in used and name not in imported:
                    missing.append("{}: dùng {}. nhưng không import {}".format(path.name, name, name))
        self.assertEqual(missing, [], "thiếu import sẽ thành NameError lúc chạy: {}".format(missing))


class VisobertBuildInputsTest(unittest.TestCase):
    """ViSoBERT phải DỰNG ĐƯỢC input khi huấn luyện - lỗi batch 11 là thiếu import `bert_like`."""

    def test_build_inputs_chay_voi_tokenizer_gia(self):
        class FakeTokenizer:
            def __call__(self, texts, **kwargs):
                return {"input_ids": [[1, 2]], "attention_mask": [[1, 1]]}

        previous = visobert._TOKENIZER
        visobert._TOKENIZER = FakeTokenizer()
        try:
            found = visobert.build_inputs(["son đẹp"], max_length=8, segmenter="none")
        finally:
            visobert._TOKENIZER = previous
        self.assertIn("input_ids", found)


if __name__ == "__main__":
    unittest.main()
