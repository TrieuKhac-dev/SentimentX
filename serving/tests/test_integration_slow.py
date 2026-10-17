# -*- coding: utf-8 -*-
"""Slow integration tests that exercise the real runtimes (GPU/model weights).

Skipped unless RUN_SLOW=1 is set in the environment.
"""

import os
import unittest

from serving.config import load_settings
from serving.registry import ModelRegistry


@unittest.skipUnless(os.environ.get("RUN_SLOW") == "1", "requires GPU/model weights")
class SlowIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.settings = load_settings()
        cls.registry = ModelRegistry(cls.settings)

    @classmethod
    def tearDownClass(cls):
        cls.registry.close()

    def test_encoder_real_predict(self):
        out = self.registry.predict("cafebert_exp027", ["son đẹp thơm"])
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0])

    def test_llm_real_predict(self):
        out = self.registry.predict("qwen3_4b_exp009", ["tệ chậm"])
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0])


if __name__ == "__main__":
    unittest.main()