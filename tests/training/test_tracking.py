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
from unittest import mock

from src.experiments import experiments
from src.core import runlog
from src import tracking
from src.tracking import base, mlflow_tracker, run_meta


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


class SessionRunIdTest(unittest.TestCase):
    """MỌI phiên ghi nhận đều có `run_id()` (rỗng khi không có run trên máy chủ).

    Vì sao khoá: `experiment_run.run()`/`encoder_run.run()` gọi `session.run_id()` NGAY sau khi mở
    phiên để ghi `tracking.run_id` vào `run_meta.json`. Phiên TẮT (tracker `none`/`local_json`, hoặc
    MLflow thiếu token/không dùng được) trả về base `Session`; thiếu phương thức này là AttributeError
    GIỮA lúc chạy -> chết run, đúng thứ luật "ghi nhận không làm chết lần chạy" cấm. Lớp test cần
    dataset không chạy được trên CI nên phải có ca này ở đây.
    """

    def test_base_session_run_id_is_empty(self):
        self.assertEqual(base.Session().run_id(), "")
        self.assertEqual(base.Session(active=False, reason="thử").run_id(), "")

    def test_none_tracker_session_has_run_id(self):
        session = tracking.begin({"tracker": "none"}, "/tmp/khong-dung")
        self.assertEqual(session.run_id(), "")

    def test_local_json_session_has_run_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            session = tracking.begin({"tracker": "local_json"}, tmp,
                                     info={"model": "m", "method": "x", "exp_id": "e"})
            self.assertEqual(session.run_id(), "")


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

    def test_auto_tags_are_looked_up_inside_the_experiment_block(self):
        """`method` và `exp_id` nằm trong khối `experiment` của `info`, không ở mức ngoài.

        Lỗi thật: chỉ tra khoá mức ngoài thì hai nhãn đó bị BỎ ÂM THẦM - nhãn khai trong
        `configs/experiments/tracking.yaml` mà chưa bao giờ xuất hiện trên run, và không có cảnh báo
        nào vì "thiếu khoá thì bỏ nhãn" là hành vi đúng cho trường hợp khác.
        """
        info = {"experiment": {"model": "visobert", "method": "lora", "exp_id": "exp001"}}
        resolved = base.resolve_tags({"model": "auto", "method": "auto", "exp_id": "auto"}, info)
        self.assertEqual(resolved, {"model": "visobert", "method": "lora", "exp_id": "exp001"})

    def test_the_eight_declared_tags_all_resolve_from_a_real_run(self):
        """Config khai 8 nhãn; một `info` đầy đủ phải làm cả 8 thành giá trị thật, không còn `auto`.

        Đọc qua `experiments.load` - đúng đường mà lượt chạy đi - nên phép kiểm này cũng xác nhận thí
        nghiệm THẬT SỰ thừa hưởng danh sách nhãn, chứ không chỉ là file config có khai.
        """
        merged = experiments.load("visobert", "lora", "exp001")
        tags = dict(merged["config"].get("mlflow_tags") or {})
        self.assertEqual(sorted(tags), ["config_sha256", "dataset", "exp_id", "method", "model",
                                        "repo_sha", "split", "version_id"])
        info = {"dataset": "cosmetics", "version_id": "cosmetics-...", "split": "test",
                "repo_sha": "a" * 40, "config_sha256": "b" * 64,
                "experiment": {"model": "visobert", "method": "lora", "exp_id": "exp001"}}
        resolved = base.resolve_tags(tags, info)
        self.assertEqual(sorted(resolved), sorted(tags))
        self.assertNotIn("auto", resolved.values())

    def test_the_artifact_list_carries_the_run_files_and_the_plot(self):
        merged = experiments.load("visobert", "lora", "exp001")
        names = list(merged["config"].get("artifacts") or [])
        for name in ("run_meta.json", "metrics.json", "metrics.csv", "plots/accuracy.html"):
            self.assertIn(name, names)
        # File nằm trong thư mục con cũng phải lấy được, và file thiếu thì bỏ qua chứ không lỗi.
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            (folder / "plots").mkdir()
            (folder / "plots" / "accuracy.html").write_text("<html></html>", encoding="utf-8")
            found = base.artifact_paths(folder, ["plots/accuracy.html", "khong-co.json"])
            self.assertEqual([path.name for path in found], ["accuracy.html"])

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


class LogPointTest(unittest.TestCase):
    """D-6: `log_point` gom chuỗi theo bước (để trình ghi vẽ được curve train/val)."""

    def test_inactive_session_keeps_nothing(self):
        session = base.Session(active=False)
        session.log_point({"sentiment_f1": 0.5}, 1)
        self.assertEqual(session.series, {})

    def test_points_are_collected_with_their_step(self):
        session = base.Session(active=True)
        session.log_point({"sentiment_f1": 0.5, "val_loss": 1.2}, 100)
        session.log_point({"sentiment_f1": 0.6}, 200)
        self.assertEqual(session.series["sentiment_f1"], [(100, 0.5), (200, 0.6)])
        self.assertEqual(session.series["val_loss"], [(100, 1.2)])

    def test_non_numeric_values_are_dropped(self):
        session = base.Session(active=True)
        session.log_point({"ghi_chu": "ok", "sentiment_f1": 0.5}, 1)
        self.assertEqual(list(session.series), ["sentiment_f1"])


class MlflowSeriesTest(unittest.TestCase):
    """D-6: `close()` gửi TỪNG điểm kèm `step`, nên MLflow vẽ được curve."""

    def test_every_point_reaches_the_server_with_its_step(self):
        calls = []
        fake = mock.Mock()
        fake.log_metric.side_effect = lambda key, value, step=None: calls.append((key, value, step))
        run = mock.Mock(info=mock.Mock(run_id="abc123"))
        session = mlflow_tracker._Session(fake, "http://server", run)
        session.log_point({"sentiment_f1": 0.5}, 100)
        session.log_point({"sentiment_f1": 0.6}, 200)
        session.close(ok=True)
        self.assertEqual([item for item in calls if item[0] == "sentiment_f1"],
                         [("sentiment_f1", 0.5, 100), ("sentiment_f1", 0.6, 200)])
        fake.end_run.assert_called_once()


class MlflowRunIdTest(unittest.TestCase):
    """F-4 (A8): một phép đo = MỘT run - nối run cũ, và gửi tham số NGAY khi mở."""

    def session(self, fake):
        run = mock.Mock(info=mock.Mock(run_id="run-1"))
        return mlflow_tracker._Session(fake, "http://server", run)

    def test_params_are_sent_once_and_only_the_new_ones(self):
        fake = mock.Mock()
        session = self.session(fake)
        session.log_params({"a": 1})
        session.log_params({"a": 1, "b": 2})
        session.close(ok=True)
        sent = [call.args[0] for call in fake.log_params.call_args_list]
        self.assertEqual(sent, [{"a": "1"}, {"b": "2"}])

    def test_close_does_not_send_params_twice(self):
        fake = mock.Mock()
        session = self.session(fake)
        session.log_params({"a": 1})
        session.close(ok=True)
        self.assertEqual(fake.log_params.call_count, 1)

    def test_begin_reuses_the_stored_run_id(self):
        fake = mock.Mock()
        fake.get_experiment_by_name.return_value = None
        with mock.patch.object(mlflow_tracker, "connect", return_value=fake), \
                mock.patch.object(mlflow_tracker, "check", return_value=True), \
                mock.patch.object(base, "token", return_value="t"), \
                mock.patch.object(mlflow_tracker.run_meta, "read",
                                  return_value={"tracking": {"run_id": "run-cu"}}):
            session = mlflow_tracker.begin({"experiment": "x"}, {"mlflow_uri": "u"}, "/tmp/out")
        fake.start_run.assert_called_once_with(run_id="run-cu")
        self.assertTrue(session.active)

    def test_begin_opens_a_new_run_without_a_stored_id(self):
        fake = mock.Mock()
        with mock.patch.object(mlflow_tracker, "connect", return_value=fake), \
                mock.patch.object(mlflow_tracker, "check", return_value=True), \
                mock.patch.object(base, "token", return_value="t"), \
                mock.patch.object(mlflow_tracker.run_meta, "read", return_value={}):
            mlflow_tracker.begin({"experiment": "x"}, {"mlflow_uri": "u"}, "/tmp/out")
        self.assertFalse(fake.start_run.call_args.kwargs.get("run_id"))

class TrackingCarryTest(unittest.TestCase):
    """F-4 (A8): `run_meta.build` MANG `tracking` của lần chạy trước sang, để lần sau nối đúng run."""

    def test_tracking_is_carried_from_previous(self):
        payload = run_meta.build("/tmp/out", previous={"attempts": [], "tracking": {"run_id": "cu"}})
        self.assertEqual(payload["tracking"], {"run_id": "cu"})

    def test_no_previous_record_means_empty_tracking(self):
        self.assertEqual(run_meta.build("/tmp/out", previous={})["tracking"], {})

    def test_attempts_are_still_carried(self):
        payload = run_meta.build("/tmp/out", previous={"attempts": [{"status": "FINISHED"}]})
        self.assertEqual(len(payload["attempts"]), 2)


class ParamAndPrefixTest(unittest.TestCase):
    """F-2/F-3: param chỉ nhận giá trị PHẲNG; số của cấu trúc lớn đi qua metric; `paper.` có tiền tố."""

    def test_flat_params_drops_structures(self):
        found = base.flat_params({"a": 1, "b": "x", "c": {"nested": 1}, "d": [1, 2]})
        self.assertEqual(found, {"a": 1, "b": "x"})

    def test_prefixed_tags_every_key(self):
        self.assertEqual(base.prefixed({"accuracy": 0.9}, "paper."), {"paper.accuracy": 0.9})

    def test_numeric_flattens_the_structures_into_metrics(self):
        values = base.numeric({"read_rate": {"% doc duoc": 97.5}, "cost": {"giay": 12.0}})
        self.assertEqual(values["read_rate.% doc duoc"], 97.5)
        self.assertEqual(values["cost.giay"], 12.0)





if __name__ == "__main__":
    unittest.main()


