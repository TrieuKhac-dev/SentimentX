# -*- coding: utf-8 -*-
"""Test HỢP ĐỒNG của các encoder kiểu BERT: registry, tham số cắt, và bộ tách từ theo từng model.

Vì sao khoá ở đây: bốn encoder thêm ở đợt 7 dùng CHUNG mã (`bert_like.py`) và chỉ khác BA tham số
(checkpoint, tên cấu hình, có/không tách từ). Sai một trong ba thì lượt chạy vẫn ra số, chỉ là số của
model KHÁC - đúng loại lỗi im lặng mà test này chốt lại.

Chạy: python -m unittest discover -s tests
"""

import unittest

from src.experiments import model_config
from src.preprocessing import bert_like, cafebert, phobert_large, token_stats, vibert, xlmroberta
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
        for name in NEW_ENCODERS + ("qwen2.5-0.5b-instruct",):
            self.assertIn(name, ids)
        self.assertEqual(len(ids), 9)          # 4 encoder cũ + 4 encoder mới + 3 model sinh

    def test_moi_muc_co_du_ham_va_ten_model_khop_config(self):
        for spec in token_stats.MODELS:
            for key in ("limit", "encode", "words", "tokenizer", "info", "model_name", "model_id"):
                self.assertIn(key, spec, "{} thiếu khoá {}".format(spec.get("model_id"), key))
            self.assertEqual(spec["model_name"], model_config.checkpoint(spec["model_id"]))


if __name__ == "__main__":
    unittest.main()
