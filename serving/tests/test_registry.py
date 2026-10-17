# -*- coding: utf-8 -*-
"""Unit tests for serving.registry.ModelRegistry (fake runtime)."""

import unittest

from serving.config import load_settings
from serving.errors import ModelDisabledError, ModelNotFoundError
from serving.registry import DISABLED, UNLOADED, ModelRegistry

ASPECTS = ["stayingpower", "texture", "smell", "price", "colour", "shipping", "packing"]
SENTIMENT_LABELS = {"positive", "negative", "not_mentioned"}


class ModelRegistryTests(unittest.TestCase):
    def setUp(self):
        self.settings = load_settings(fake=True)
        self.registry = ModelRegistry(self.settings)

    def tearDown(self):
        self.registry.close()

    def test_list_models(self):
        models = self.registry.list_models()
        self.assertEqual(len(models), 2)
        ids = {m["id"] for m in models}
        self.assertEqual(ids, {"cafebert_exp027", "qwen3_4b_exp009"})
        for m in models:
            self.assertIn(m["state"], {DISABLED, UNLOADED})
            self.assertIn("hash", m)

    def test_check_returns_empty(self):
        self.assertEqual(self.registry.check(), {})

    def test_predict_positive(self):
        out = self.registry.predict(None, ["son đẹp thơm"])
        self.assertEqual(len(out), 1)
        aspects = out[0]
        self.assertEqual(set(aspects.keys()), set(ASPECTS))
        for result in aspects.values():
            self.assertIn(result.label, SENTIMENT_LABELS)
            self.assertEqual(result.code, 1)

    def test_predict_negative(self):
        out = self.registry.predict("cafebert_exp027", ["tệ chậm"])
        self.assertEqual(len(out), 1)
        for result in out[0].values():
            self.assertEqual(result.code, 2)

    def test_predict_unknown_model(self):
        with self.assertRaises(ModelNotFoundError):
            self.registry.predict("nope", ["x"])

    def test_predict_disabled_model(self):
        settings = load_settings(models_override="cafebert_exp027", fake=True)
        reg = ModelRegistry(settings)
        try:
            with self.assertRaises(ModelDisabledError):
                reg.predict("qwen3_4b_exp009", ["x"])
        finally:
            reg.close()

    def test_close_leaves_unloaded(self):
        self.registry.predict(None, ["son đẹp thơm"])
        self.registry.close()
        for m in self.registry.list_models():
            self.assertEqual(m["state"], UNLOADED)


if __name__ == "__main__":
    unittest.main()