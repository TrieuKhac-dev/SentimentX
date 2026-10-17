# -*- coding: utf-8 -*-
"""Privacy-focused tests: serving responses must not leak training data."""

import json
import unittest

from fastapi.testclient import TestClient

from serving.app import create_app
from serving.config import load_settings
from serving.registry import ModelRegistry


class PrivacyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.settings = load_settings(fake=True)
        cls.registry = ModelRegistry(cls.settings)
        cls.app = create_app(cls.settings, cls.registry)
        cls.client = TestClient(cls.app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)
        cls.registry.close()

    def test_no_gold_or_dataset_paths_in_response(self):
        resp = self.client.post("/predict", json={"model": "cafebert_exp027", "text": "son đẹp"})
        self.assertEqual(resp.status_code, 200)
        body = json.dumps(resp.json(), ensure_ascii=False)
        self.assertNotIn("test.csv", body)
        self.assertNotIn("gold", body)


if __name__ == "__main__":
    unittest.main()