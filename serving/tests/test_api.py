# -*- coding: utf-8 -*-
"""Integration-style API tests using FastAPI TestClient (fake runtime)."""

import unittest

from fastapi.testclient import TestClient

from serving.app import create_app
from serving.config import load_settings
from serving.registry import ModelRegistry

ASPECTS = ["stayingpower", "texture", "smell", "price", "colour", "shipping", "packing"]


class ApiTests(unittest.TestCase):
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

    def test_health(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["ready"])
        self.assertEqual(set(data["models"]), {"cafebert_exp027", "qwen3_4b_exp009"})

    def test_models(self):
        resp = self.client.get("/models")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()["models"]), 2)

    def test_index_html(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/html", resp.headers.get("content-type", ""))

    def test_predict_specific_model(self):
        resp = self.client.post("/predict", json={"model": "cafebert_exp027", "text": "son đẹp"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["model"], "cafebert_exp027")
        self.assertEqual(set(data["results"][0]["aspects"]), set(ASPECTS))
        self.assertEqual(data["results"][0]["aspects"]["colour"]["label"], "positive")
        for key in ("results", "model", "latency_ms", "batch_size"):
            self.assertIn(key, data)

    def test_predict_default(self):
        resp = self.client.post("/predict", json={"text": "tệ"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["model"], "cafebert_exp027")

    def test_predict_path(self):
        resp = self.client.post("/predict/cafebert_exp027", json={"text": "son đẹp"})
        self.assertEqual(resp.status_code, 200)

    def test_predict_hybrid_not_implemented(self):
        resp = self.client.post("/predict/hybrid")
        self.assertEqual(resp.status_code, 501)
        self.assertEqual(resp.json()["error"]["code"], "hybrid_not_implemented")

    def test_predict_unknown_model(self):
        resp = self.client.post("/predict", json={"model": "nope", "text": "x"})
        self.assertEqual(resp.status_code, 404)

    def test_predict_llm_fake(self):
        resp = self.client.post("/predict", json={"model": "qwen3_4b_exp009", "text": "tệ"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["model"], "qwen3_4b_exp009")

    def test_predict_empty_body(self):
        resp = self.client.post("/predict", json={})
        self.assertEqual(resp.status_code, 422)


class DisabledModelApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.settings = load_settings(models_override="cafebert_exp027", fake=True)
        cls.registry = ModelRegistry(cls.settings)
        cls.app = create_app(cls.settings, cls.registry)
        cls.client = TestClient(cls.app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)
        cls.registry.close()

    def test_predict_disabled_model(self):
        resp = self.client.post("/predict/qwen3_4b_exp009", json={"text": "x"})
        self.assertEqual(resp.status_code, 503)
        self.assertEqual(resp.json()["error"]["code"], "model_disabled")


if __name__ == "__main__":
    unittest.main()