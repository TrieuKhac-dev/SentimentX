# -*- coding: utf-8 -*-
"""Test that gpu_concurrency actually serializes predict/preload."""

import threading
import time
import unittest
from unittest.mock import patch

from serving.config import load_settings
from serving.registry import ModelRegistry


class _FakeRuntime:
    def __init__(self):
        self.metadata = {"device": "cpu", "max_length": 16}
        self._lock = threading.Lock()
        self._active = 0
        self.max_active = 0
        self.predict_calls = 0

    def load(self, spec, settings):
        pass

    def warmup(self):
        pass

    def predict(self, texts, include_probs=True):
        with self._lock:
            self._active += 1
            self.max_active = max(self.max_active, self._active)
            self.predict_calls += 1
        time.sleep(0.05)
        with self._lock:
            self._active -= 1
        return [{} for _ in texts]

    def unload(self):
        pass


class GpuConcurrencyTests(unittest.TestCase):
    def test_predict_never_overlaps_with_concurrency_one(self):
        settings = load_settings(fake=True)
        self.assertEqual(int(settings.server.get("gpu_concurrency", 1)), 1)
        runtime = _FakeRuntime()
        with patch("serving.registry.create_runtime", return_value=runtime):
            registry = ModelRegistry(settings)
            try:
                threads = [
                    threading.Thread(
                        target=registry.predict,
                        args=("cafebert_exp027", ["son đẹp"]),
                    )
                    for _ in range(2)
                ]
                for thread in threads:
                    thread.start()
                for thread in threads:
                    thread.join(timeout=10)
                    self.assertFalse(thread.is_alive())
                self.assertEqual(runtime.predict_calls, 2)
                self.assertEqual(runtime.max_active, 1)
            finally:
                registry.close()


if __name__ == "__main__":
    unittest.main()