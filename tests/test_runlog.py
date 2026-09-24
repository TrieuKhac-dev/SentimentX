# -*- coding: utf-8 -*-
"""Test nhật ký lần chạy (src/runlog.py).

Ba điều được khoá ở đây, vì đều là thứ chỉ phát hiện được khi đã hỏng thật:
    - `run.log` phải LUÔN có, và phải có dòng `[RUN] mode=...` ở đầu dòng (DoD của P4 T8).
    - `errors.json` KHÔNG được tạo khi không có lỗi, và PHẢI có khi lỗi thoát ra khỏi khối `with`.
    - mỗi dòng phải xuống đĩa NGAY: tiến trình bị dừng đột ngột vẫn còn log tới dòng cuối.

Chạy: python -m unittest discover -s tests
"""

import platform
import tempfile
import unittest
from pathlib import Path

from src import runlog


class TestRunLog(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.out_dir = Path(self._tmp.name) / "prompt-absa_cot_v1__val__greedy"

    def tearDown(self):
        self._tmp.cleanup()

    def log_text(self):
        return (self.out_dir / "run.log").read_text(encoding="utf-8")

    def test_run_log_always_exists(self):
        with runlog.start(self.out_dir, mode="NEW") as log:
            log.step("bắt đầu")
        self.assertTrue(runlog.log_path(self.out_dir).exists())
        self.assertIn("[RUN] mode=NEW", self.log_text())

    def test_resume_mode_line_is_at_start_of_line(self):
        """Dòng này là mốc kiểm tra của P4 T8, nên nó phải ở ĐẦU dòng để grep là ra."""
        with runlog.start(self.out_dir, mode="RESUME"):
            pass
        self.assertTrue(any(line.startswith("[RUN] mode=RESUME")
                            for line in self.log_text().splitlines()))

    def test_config_lines_are_tagged(self):
        """Bảng ghi đè phải nằm trong FILE: notebook gửi đi đã bị làm sạch output."""
        self.assertIn("CONFIG", runlog.TAGS)
        with runlog.start(self.out_dir) as log:
            log.config("đè eval.n: 100 <- 200")
        self.assertTrue(any(line.startswith("[CONFIG] ")
                            for line in self.log_text().splitlines()))

    def test_no_errors_file_without_error(self):
        with runlog.start(self.out_dir) as log:
            log.step("chạy bình thường")
            log.warn("chưa log được lên MLflow: thiếu DAGSHUB_TOKEN")
        self.assertFalse(runlog.errors_path(self.out_dir).exists())
        self.assertIsNone(runlog.read_errors(self.out_dir))

    def test_error_escaping_the_block_is_recorded(self):
        with self.assertRaises(ValueError):
            with runlog.start(self.out_dir, info={"prompt": "absa_cot_v1"}):
                raise ValueError("hỏng định dạng JSON")

        payload = runlog.read_errors(self.out_dir)
        entry = payload["errors"][0]
        self.assertEqual(entry["type"], "ValueError")
        self.assertIn("hỏng định dạng JSON", entry["message"])
        self.assertIn("ValueError", entry["traceback"])
        self.assertEqual(payload["run"]["info"], {"prompt": "absa_cot_v1"})
        self.assertEqual(payload["run"]["mode"], "NEW")

    def test_keyboard_interrupt_is_recorded_and_propagated(self):
        """Người dùng dừng notebook giữa chừng cũng phải để lại dấu vết."""
        with self.assertRaises(KeyboardInterrupt):
            with runlog.start(self.out_dir):
                raise KeyboardInterrupt()
        entry = runlog.read_errors(self.out_dir)["errors"][0]
        self.assertEqual(entry["type"], "KeyboardInterrupt")
        self.assertEqual(entry["context"]["kind"], "KeyboardInterrupt")


class TestRunLogDetails(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.out_dir = Path(self._tmp.name) / "run"

    def tearDown(self):
        self._tmp.cleanup()

    def log_text(self):
        return (self.out_dir / "run.log").read_text(encoding="utf-8")

    def test_exception_helper_keeps_context_and_requires(self):
        with runlog.start(self.out_dir) as log:
            try:
                import thuvien_khong_ton_tai  # noqa: F401
            except ImportError as exc:
                log.exception(exc, context={"bước": "nạp model"},
                              requires=["bitsandbytes"])

        entry = runlog.read_errors(self.out_dir)["errors"][0]
        # Log ghi TÊN LỚP THẬT của lỗi, nên ở đây là ModuleNotFoundError (lớp con của ImportError).
        self.assertIn(entry["type"], ("ImportError", "ModuleNotFoundError"))
        self.assertEqual(entry["context"], {"bước": "nạp model"})
        self.assertEqual(entry["requires"], ["bitsandbytes"])

    def test_lines_are_flushed_immediately(self):
        """Đọc file trong lúc log còn MỞ: tiến trình chết đột ngột thì log vẫn còn tới đó."""
        log = runlog.start(self.out_dir)
        log.step("dòng thứ nhất")
        with open(log.path, encoding="utf-8") as handle:
            self.assertIn("[STEP] dòng thứ nhất", handle.read())
        log.close()

    def test_step_prints_seconds(self):
        with runlog.start(self.out_dir) as log:
            log.step("sinh xong 100 mẫu", seconds=123.45)
        self.assertIn("[STEP] sinh xong 100 mẫu | 123.5 giây", self.log_text())

    def test_second_run_appends_and_keeps_history(self):
        """Chạy lại vào cùng thư mục không được xoá log của lần trước."""
        with runlog.start(self.out_dir, mode="NEW") as log:
            log.step("lần một")
        with runlog.start(self.out_dir, mode="RESUME") as log:
            log.step("lần hai")

        text = self.log_text()
        self.assertIn("lần một", text)
        self.assertIn("lần hai", text)
        self.assertEqual(text.count("=== lần chạy"), 2)

    def test_unknown_tag_is_rejected(self):
        with runlog.start(self.out_dir) as log:
            with self.assertRaises(ValueError):
                log.line("KHONGCO", "x")

    def test_nested_info_is_flattened(self):
        with runlog.start(self.out_dir, info={"generation": {"do_sample": False}}):
            pass
        self.assertIn("[RUN] generation.do_sample=False", self.log_text())

    def test_payload_records_machine(self):
        log = runlog.start(self.out_dir)
        payload = log.payload()
        self.assertIn("machine", payload["run"])
        self.assertNotIn("\\", payload["run"]["out_dir"])
        self.assertEqual(payload["errors"], [])
        log.close()


if __name__ == "__main__":
    unittest.main()

