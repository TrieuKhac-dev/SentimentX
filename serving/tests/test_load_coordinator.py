# -*- coding: utf-8 -*-
"""Unit tests for the latest-wins model load coordinator and registry preload."""

import threading
import time
import unittest

from serving.config import load_settings
from serving.load_coordinator import ModelLoadCoordinator
from serving.registry import ModelRegistry


def _wait_until(predicate, timeout=3.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return predicate()


class FakeRegistry:
    def __init__(self, states=None):
        self._lock = threading.Lock()
        self._states = dict(states or {})
        self.calls = []
        self.block = {}
        self.started = {}
        self.fail = set()

    def list_models(self):
        with self._lock:
            return [
                {"id": model_id, "enabled": True, "state": state}
                for model_id, state in self._states.items()
            ]

    def status(self):
        with self._lock:
            return {
                model_id: {"id": model_id, "enabled": True, "state": state}
                for model_id, state in self._states.items()
            }

    def state(self, model_id):
        with self._lock:
            return self._states.get(model_id)

    def preload(self, model_id):
        with self._lock:
            self.calls.append(model_id)
            self._states[model_id] = (
                "FAILED" if model_id in self.fail else "LOADING"
            )
            started = self.started.get(model_id)
            blocker = self.block.get(model_id)

        if started is not None:
            started.set()
        if blocker is not None:
            blocker.wait(timeout=5.0)

        with self._lock:
            if model_id in self.fail:
                raise RuntimeError("boom")
            self._states[model_id] = "READY"
        return {"id": model_id, "state": "READY"}


class ModelLoadCoordinatorTests(unittest.TestCase):
    def test_ready_model_is_not_preloaded(self):
        registry = FakeRegistry({"a": "READY"})
        coordinator = ModelLoadCoordinator(registry)
        coordinator.start()
        try:
            payload = coordinator.request("a")
            self.assertEqual(payload["state"], "READY")
            time.sleep(0.1)
            self.assertEqual(registry.calls, [])
            self.assertEqual(coordinator.status()["state"], "READY")
        finally:
            coordinator.stop()

    def test_latest_request_wins_without_getting_stuck(self):
        registry = FakeRegistry({"a": "UNLOADED", "b": "UNLOADED"})
        registry.block["a"] = threading.Event()
        registry.started["a"] = threading.Event()
        coordinator = ModelLoadCoordinator(registry)
        coordinator.start()
        try:
            first = coordinator.request("a")
            self.assertEqual(first["state"], "QUEUED")
            self.assertTrue(registry.started["a"].wait(timeout=2.0))

            second = coordinator.request("b")
            self.assertEqual(second["state"], "QUEUED")
            self.assertGreater(second["generation"], first["generation"])

            registry.block["a"].set()
            self.assertTrue(_wait_until(lambda: registry.state("b") == "READY"))
            self.assertEqual(registry.calls, ["a", "b"])
            self.assertTrue(
                _wait_until(
                    lambda: coordinator.status()["model_id"] == "b"
                    and coordinator.status()["state"] == "READY"
                )
            )
        finally:
            coordinator.stop()

    def test_load_error_is_recorded_and_does_not_loop(self):
        registry = FakeRegistry({"a": "UNLOADED"})
        registry.fail.add("a")
        coordinator = ModelLoadCoordinator(registry)
        coordinator.start()
        try:
            coordinator.request("a")
            self.assertTrue(
                _wait_until(lambda: coordinator.status()["state"] == "FAILED")
            )
            self.assertIn("boom", coordinator.status()["error"])
            time.sleep(0.1)
            self.assertEqual(registry.calls, ["a"])
        finally:
            coordinator.stop()

    def test_new_request_retries_after_failure(self):
        registry = FakeRegistry({"a": "UNLOADED"})
        registry.fail.add("a")
        coordinator = ModelLoadCoordinator(registry)
        coordinator.start()
        try:
            coordinator.request("a")
            self.assertTrue(
                _wait_until(lambda: coordinator.status()["state"] == "FAILED")
            )

            registry.fail.discard("a")
            retry = coordinator.request("a")
            self.assertGreater(retry["generation"], 1)
            self.assertTrue(_wait_until(lambda: registry.state("a") == "READY"))
            self.assertEqual(registry.calls, ["a", "a"])
        finally:
            coordinator.stop()

    def test_start_and_stop_are_idempotent(self):
        registry = FakeRegistry({"a": "UNLOADED"})
        coordinator = ModelLoadCoordinator(registry)
        coordinator.start()
        coordinator.start()
        coordinator.stop()
        coordinator.stop()


class RegistryPreloadTests(unittest.TestCase):
    def test_preload_loads_and_warms_without_prediction(self):
        settings = load_settings(fake=True)
        registry = ModelRegistry(settings)
        try:
            info = registry.preload("qwen3_4b_exp009")
            self.assertEqual(info["id"], "qwen3_4b_exp009")
            self.assertEqual(info["state"], "READY")
            self.assertTrue(info["loaded"])

            again = registry.preload("qwen3_4b_exp009")
            self.assertEqual(again["state"], "READY")
        finally:
            registry.close()


if __name__ == "__main__":
    unittest.main()