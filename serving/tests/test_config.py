# -*- coding: utf-8 -*-
"""Unit tests for serving.config / load_settings."""

import unittest

from serving.config import load_settings

ASPECTS = ["stayingpower", "texture", "smell", "price", "colour", "shipping", "packing"]


class LoadSettingsTests(unittest.TestCase):
    def test_default_config_has_two_enabled_models(self):
        settings = load_settings()
        self.assertEqual(len(settings.models), 2)
        self.assertEqual(settings.enabled_models, ["cafebert_exp027", "qwen3_4b_exp009"])
        self.assertEqual(settings.default_model, "cafebert_exp027")

    def test_model_kinds(self):
        settings = load_settings()
        self.assertEqual(settings.models["cafebert_exp027"].kind, "encoder")
        self.assertEqual(settings.models["qwen3_4b_exp009"].kind, "llm")

    def test_labels(self):
        settings = load_settings()
        self.assertEqual(settings.labels["aspects"], ASPECTS)
        codes = settings.labels["codes"]
        self.assertEqual(codes[0]["name"], "not_mentioned")
        self.assertEqual(codes[1]["name"], "positive")
        self.assertEqual(codes[2]["name"], "negative")
        self.assertEqual(codes[0]["vi"], "Không nhắc tới")

    def test_models_override_enables_only_llm(self):
        settings = load_settings(models_override="qwen3_4b_exp009")
        self.assertEqual(settings.enabled_models, ["qwen3_4b_exp009"])
        self.assertFalse(settings.models["cafebert_exp027"].enabled)
        self.assertTrue(settings.models["qwen3_4b_exp009"].enabled)
        self.assertEqual(settings.default_model, "qwen3_4b_exp009")

    def test_default_override_unknown_raises(self):
        with self.assertRaises(ValueError):
            load_settings(default_override="does_not_exist")

    def test_fake_still_loads(self):
        settings = load_settings(fake=True)
        self.assertEqual(settings.enabled_models, ["cafebert_exp027", "qwen3_4b_exp009"])
        self.assertEqual(settings.default_model, "cafebert_exp027")


if __name__ == "__main__":
    unittest.main()