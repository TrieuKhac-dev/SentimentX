# -*- coding: utf-8 -*-
"""Test registry tracker (src/tracking/).

Điều quan trọng nhất được khoá ở đây: **ghi nhận KHÔNG BAO GIỜ làm chết một lần chạy**. Thiếu
thư viện `mlflow`, thiếu token, máy chủ hỏng - tất cả phải dẫn tới một phiên KHÔNG hoạt động kèm
dòng `[WARN]`/`[TRACK]` trong `run.log`, chứ không phải một ngoại lệ.

Chạy: python -m unittest discover -s tests
"""

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

from src import runlog, tracking
from src.tracking import base


class TestRegistry(unittest.TestCase):
    def test_available_lists_three_trackers(self):
        self.assertEqual(tracking.available(), ["mlflow", "local_json", "none"])

    def test_get_rejects_unknown_name(self):
        with self.assertRaises(base.TrackingError) as caught:
            tracking.get("khong_co")
        self.assertIn("khong_co", str(caught.exception))
        self.assertIn("local_json", str(caught.exception))

    def test_check_none_needs_nothing(self):
        """`none` là lựa chọn hợp lệ, không cần token hay thư viện nào."""
        self.assertTrue(tracking.check({"tracker": "none"}))

    def test_check_mlflow_reports_every_problem(self):
        """Kiểm trước khi chạy: thiếu gì báo hết một lần, kèm việc cần làm."""
        dagshub = {"owner": "ai-do", "mlflow_uri": "https://example.invalid",
                   "token_env": "SENTIMENTX_TEST_TOKEN_KHONG_CO"}
        config = {"tracker": "mlflow", "experiment": "sentimentx-absa"}
        with self.assertRaises(base.TrackingError) as caught:
            tracking.check(config, dagshub)
        message = str(caught.exception)
        self.assertIn("SENTIMENTX_TEST_TOKEN_KHONG_CO", message)
        # Thư viện `mlflow` có thể đã được cài (khi đó không còn việc này để báo).
        if importlib.util.find_spec("mlflow") is None:
            self.assertIn("pip install mlflow", message)
        else:
            self.assertNotIn("pip install mlflow", message)

    def test_describe_mentions_every_tracker(self):
        lines = "\n".join(tracking.describe())
        for name in tracking.available():
            self.assertIn(name, lines)


class TestHelpers(unittest.TestCase):
    def test_numeric_keeps_only_numbers(self):
        values = base.numeric({"accuracy": {"macro": 91.43, "by_aspect": {"colour": 90.0}},
                               "label_space": "binary", "cells": 700})
        self.assertEqual(values, {"accuracy.macro": 91.43,
                                  "accuracy.by_aspect.colour": 90.0, "cells": 700.0})

    def test_numeric_turns_bool_into_number(self):
        self.assertEqual(base.numeric({"x": True}), {"x": 1.0})

    def test_as_param_flattens_and_truncates(self):
        self.assertEqual(base.as_param({"a": 1, "b": None}), "a=1, b=None")
        self.assertEqual(base.as_param(["a", "b"]), "a, b")
        self.assertTrue(len(base.as_param("x" * 900)) <= base.MAX_PARAM)

    def test_resolve_tags_uses_info_and_drops_empty_auto(self):
        tags = {"model": "auto", "method": "auto", "owner": "TrieuKhac-dev"}
        info = {"model": "qwen3-4b-instruct-2507"}
        self.assertEqual(base.resolve_tags(tags, info),
                         {"model": "qwen3-4b-instruct-2507", "owner": "TrieuKhac-dev"})

    def test_artifact_paths_skips_missing_files(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            (folder / "metrics.json").write_text("{}", encoding="utf-8")
            found = base.artifact_paths(folder, ["metrics.json", "run_meta.json"])
            self.assertEqual([path.name for path in found], ["metrics.json"])


class TestSessions(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.out_dir = self.root / "results" / "prompt-absa_cot_v1__val__greedy"
        self._saved = os.environ.get("SENTIMENTX_DATA_ROOT")
        os.environ["SENTIMENTX_DATA_ROOT"] = str(self.root / "data")

    def tearDown(self):
        if self._saved is None:
            os.environ.pop("SENTIMENTX_DATA_ROOT", None)
        else:
            os.environ["SENTIMENTX_DATA_ROOT"] = self._saved
        self._tmp.cleanup()

    def test_none_session_writes_nothing(self):
        session = tracking.begin({"tracker": "none"}, self.out_dir)
        self.assertFalse(session.active)
        session.log_params({"a": 1})
        session.log_metrics({"b": 1})
        self.assertIsNone(session.close(ok=True))
        self.assertEqual(list((self.root / "data").rglob("*")), [])

    def test_local_json_writes_a_record(self):
        self.out_dir.mkdir(parents=True)
        (self.out_dir / "metrics.json").write_text("{}", encoding="utf-8")
        session = tracking.begin({"tracker": "local_json"}, self.out_dir,
                                 info={"model": "qwen3-4b-instruct-2507"})
        self.assertTrue(session.active)
        session.log_params({"prompt": "absa_cot_v1", "max_length": 1280})
        session.log_metrics({"accuracy": {"macro": 91.43}})
        session.log_artifacts(base.artifact_paths(self.out_dir, ["metrics.json"]))
        notes = tracking.close(session, ok=True)

        self.assertTrue(any("qwen3-4b-instruct-2507" in note for note in notes))
        payload = json.loads(session.path.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "FINISHED")
        self.assertEqual(payload["params"]["max_length"], "1280")
        self.assertEqual(payload["metrics"], {"accuracy.macro": 91.43})
        self.assertEqual(payload["artifacts"], ["metrics.json"])

    def test_local_json_records_failed_status(self):
        session = tracking.begin({"tracker": "local_json"}, self.out_dir)
        tracking.close(session, ok=False)
        payload = json.loads(session.path.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "FAILED")

    def test_close_never_raises(self):
        """Máy chủ chết lúc đóng phiên: lần chạy vẫn phải xong, chỉ thêm một dòng ghi chú."""

        class Broken(base.Session):
            def close(self, ok=True):
                raise RuntimeError("máy chủ không trả lời")

        notes = tracking.close(Broken(active=True), log=None)
        self.assertTrue(any("máy chủ không trả lời" in note for note in notes))


class TestMlflowDegradesGracefully(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.out_dir = Path(self._tmp.name) / "run"

    def tearDown(self):
        self._tmp.cleanup()

    def test_missing_token_does_not_raise(self):
        """Thiếu token (và có thể thiếu cả `mlflow`): đi tiếp, ghi lại lí do, không lỗi."""
        dagshub = {"owner": "ai-do", "mlflow_uri": "https://example.invalid",
                   "token_env": "SENTIMENTX_TEST_TOKEN_KHONG_CO"}
        with runlog.start(self.out_dir, info={"model": "qwen3-4b"}) as log:
            session = tracking.begin({"tracker": "mlflow", "experiment": "sentimentx-absa"},
                                     self.out_dir, dagshub=dagshub, log=log)
            self.assertFalse(session.active)
            log.on_close(tracking.closer(session, log=log))

        text = (self.out_dir / "run.log").read_text(encoding="utf-8")
        self.assertIn("[WARN] không dùng được MLflow", text)
        self.assertIn("[TRACK] không ghi nhận:", text)
        self.assertFalse(runlog.errors_path(self.out_dir).exists())


if __name__ == "__main__":
    unittest.main()


