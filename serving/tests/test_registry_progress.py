# -*- coding: utf-8 -*-
"""Tests for real model-load progress in serving.registry."""

import unittest

from serving.config import load_settings
from serving.registry import (
    LOADING,
    READY,
    UNLOADED,
    WARMING,
    ModelRegistry,
    _ModelEntry,
    _ProgressTqdm,
    _install_progress_hook,
)


class DescribeProgressTests(unittest.TestCase):
    def setUp(self):
        self.settings = load_settings(fake=True)
        self.registry = ModelRegistry(self.settings)
        self.spec = self.settings.models["cafebert_exp027"]

    def tearDown(self):
        self.registry.close()

    def test_default_unloaded_is_zero(self):
        entry = _ModelEntry(spec=self.spec)
        self.assertEqual(entry.state, UNLOADED)
        self.assertEqual(self.registry._describe(entry)["load_progress"], 0)

    def test_ready_is_100(self):
        entry = _ModelEntry(spec=self.spec, state=READY, load_progress=90)
        self.assertEqual(self.registry._describe(entry)["load_progress"], 100)

    def test_warming_is_at_least_95(self):
        entry = _ModelEntry(spec=self.spec, state=WARMING, load_progress=42)
        self.assertEqual(self.registry._describe(entry)["load_progress"], 95)

    def test_loading_reports_stored_value(self):
        entry = _ModelEntry(spec=self.spec, state=LOADING, load_progress=42)
        self.assertEqual(self.registry._describe(entry)["load_progress"], 42)


class ProgressTqdmTests(unittest.TestCase):
    def test_iteration_is_monotonic_5_to_90(self):
        seen = []
        wrapper = _ProgressTqdm(iter(range(10)), seen.append, total=10)
        self.assertEqual(list(wrapper), list(range(10)))
        self.assertEqual(len(seen), 10)
        self.assertEqual(seen, sorted(seen))
        self.assertEqual(seen[-1], 90)
        for pct in seen:
            self.assertGreaterEqual(pct, 5)
            self.assertLessEqual(pct, 90)

    def test_unknown_total_uses_10(self):
        seen = []
        wrapper = _ProgressTqdm(iter(range(3)), seen.append, total=None)
        list(wrapper)
        self.assertEqual(seen, [10, 10, 10])

    def test_update_counts_steps(self):
        seen = []

        class _Inner:
            def update(self, n=1):
                self.n = n
                return True

        wrapper = _ProgressTqdm(_Inner(), seen.append, total=10)
        self.assertTrue(wrapper.update(5))
        self.assertTrue(wrapper.update(5))
        self.assertEqual(seen[-1], 90)


class ProgressHookTests(unittest.TestCase):
    def setUp(self):
        self.settings = load_settings(fake=True)
        self.registry = ModelRegistry(self.settings)
        self.spec = self.settings.models["cafebert_exp027"]

    def tearDown(self):
        self.registry.close()

    def _transformers_logging(self):
        try:
            from transformers.utils import logging as transformers_logging
        except Exception:
            self.skipTest("transformers is not installed")
        return transformers_logging

    def test_install_and_restore(self):
        logging_mod = self._transformers_logging()
        marker = object()
        calls = []
        original = logging_mod.set_tqdm_hook

        def fake_set(hook):
            calls.append(hook)
            return marker

        logging_mod.set_tqdm_hook = fake_set
        try:
            entry = _ModelEntry(spec=self.spec)
            state = _install_progress_hook(self.registry, entry)
            self.assertIsNotNone(state)
            setter, previous = state
            self.assertIs(setter, fake_set)
            self.assertIs(previous, marker)
            self.assertEqual(len(calls), 1)
            self.assertTrue(callable(calls[0]))
            setter(previous)
            self.assertIs(calls[1], marker)
        finally:
            logging_mod.set_tqdm_hook = original

    def test_hook_filters_desc_and_reports_progress(self):
        logging_mod = self._transformers_logging()
        calls = []
        original = logging_mod.set_tqdm_hook

        def fake_set(hook):
            calls.append(hook)
            return None

        logging_mod.set_tqdm_hook = fake_set
        try:
            entry = _ModelEntry(spec=self.spec, state=LOADING)
            state = _install_progress_hook(self.registry, entry)
            self.assertIsNotNone(state)
            hook = calls[0]

            class _Factory:
                def __init__(self):
                    self.calls = []

                def __call__(self, *args, **kwargs):
                    self.calls.append((args, kwargs))
                    return args[0]

            factory = _Factory()
            untouched = hook(factory, (list(range(10)),), {"desc": "Fetching"})
            self.assertEqual(untouched, list(range(10)))
            self.assertNotIsInstance(untouched, _ProgressTqdm)

            wrapped = hook(factory, (list(range(10)),), {"desc": "Loading weights"})
            self.assertIsInstance(wrapped, _ProgressTqdm)
            list(wrapped)
            self.assertEqual(entry.load_progress, 90)
        finally:
            logging_mod.set_tqdm_hook = original

    def test_missing_hook_api_returns_none(self):
        logging_mod = self._transformers_logging()
        original = logging_mod.set_tqdm_hook
        removed = False
        try:
            del logging_mod.set_tqdm_hook
            removed = True
            entry = _ModelEntry(spec=self.spec)
            self.assertIsNone(_install_progress_hook(self.registry, entry))
        finally:
            if removed:
                logging_mod.set_tqdm_hook = original


if __name__ == "__main__":
    unittest.main()
