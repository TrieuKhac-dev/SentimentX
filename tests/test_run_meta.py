# -*- coding: utf-8 -*-
"""Test bản ghi lần chạy (src/tracking/run_meta.py).

Ba điều được khoá ở đây, vì đều là thứ chỉ phát hiện được khi đã hỏng thật:
    - KHÔNG có đường dẫn tuyệt đối trong file: thư mục kết quả bị đem từ máy này sang máy khác.
    - `attempts[]` giữ được lịch sử khi chạy lại vào cùng thư mục, và mỗi attempt mang `sha`,
      `config_sha256`, `data` của CHÍNH lần đó - đây là dữ liệu để quyết định resume.
    - attempt được chốt cả khi lần chạy HỎNG.

Chạy: python -m unittest discover -s tests
"""

import json
import re
import tempfile
import unittest
from pathlib import Path

from src import paths
from src.tracking import run_meta


class TestRecords(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.out_dir = Path(self._tmp.name) / "prompt-absa_cot_v1__val__greedy"
        self.out_dir.mkdir(parents=True)

    def tearDown(self):
        self._tmp.cleanup()

    def build(self, **kwargs):
        payload = dict(
            tag="prompt-absa_cot_v1__val__greedy",
            experiment={"model": "qwen3-4b-instruct-2507", "method": "prompt-cot",
                        "exp_id": "exp001"},
            data={"dataset": "cosmetics", "version": "v0.1.0",
                  "ma": "cosmetics-ds0.1.0-pl0.1.0-srccosmetics@0.1.0-1a2b3c4d"},
            repo={"url": "https://github.com/example/repo", "branch": "experiment",
                  "sha": "a" * 40},
            config={"sha256": "b" * 64},
            files=[], env=dict(run_meta.env_info("local")))
        payload.update(kwargs)
        return run_meta.build(self.out_dir, **payload)

    def test_task_and_overrides_are_recorded(self):
        """Bài toán đang giải và khoá bị đè: máy khác đọc file là biết, không phải mở log."""
        payload = self.build(task={"label_space": "binary", "neutral_policy": "drop",
                                   "not_mentioned": "separate"},
                             overrides=[["n", 100, 200, "experiment"]])
        self.assertEqual(payload["task"]["label_space"], "binary")
        self.assertEqual(payload["overrides"], [["n", 100, 200, "experiment"]])

    def test_mac_dinh_cua_hai_khoa_moi_la_rong(self):
        payload = self.build()
        self.assertEqual(payload["task"], {})
        self.assertEqual(payload["overrides"], [])

    def test_device_info_prefers_the_resolved_quantization(self):
        """Bản ghi phải nói phép đo đã chạy bằng gì, không phải tham số khai trong config.

        `quant` truyền vào thường là "auto" (tham số của người chạy), còn giá trị THẬT nằm ở
        `model_info` do bước nạp model trả về ("4-bit nf4 (tính bằng float16)").
        """
        info = run_meta.device_info({"thiết bị": "cuda:0", "quant": "4-bit nf4 (tính bằng float16)",
                                     "torch": "2.14.0"}, quant="auto")
        self.assertEqual(info["device"], "cuda:0")
        self.assertEqual(info["quantization"], "4-bit nf4 (tính bằng float16)")
        self.assertEqual(info["libs"], {"torch": "2.14.0"})
        self.assertIsNone(info["vram_gb"])

    def test_device_info_falls_back_to_the_declared_quantization(self):
        info = run_meta.device_info({}, quant="4bit")
        self.assertEqual(info["quantization"], "4bit")

    def test_device_info_without_anything_readable(self):
        info = run_meta.device_info()
        self.assertIsNone(info["quantization"])
        self.assertEqual(info["libs"], {})

    def test_new_record_starts_one_attempt(self):
        payload = self.build()
        attempts = payload["attempts"]
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0]["n"], 1)
        self.assertEqual(attempts[0]["status"], run_meta.STATUS_RUNNING)
        self.assertEqual(attempts[0]["sha"], "a" * 40)
        self.assertEqual(attempts[0]["config_sha256"], "b" * 64)
        self.assertEqual(payload["run"]["status"], run_meta.STATUS_RUNNING)

    def test_running_again_keeps_history(self):
        """Chạy lại vào cùng thư mục: attempt cũ giữ nguyên, thêm attempt mới."""
        first = self.build()
        run_meta.finish_attempt(run_meta.attempt_of(first), run_meta.STATUS_FINISHED)
        run_meta.write(self.out_dir, first)

        second = self.build(previous=run_meta.read(self.out_dir))
        self.assertEqual([item["n"] for item in second["attempts"]], [1, 2])
        self.assertEqual(second["attempts"][1]["status"], run_meta.STATUS_RUNNING)

    def test_closer_marks_failed_run(self):
        payload = self.build()
        run_meta.closer(payload, self.out_dir)(ok=False)
        stored = run_meta.read(self.out_dir)
        self.assertEqual(stored["run"]["status"], run_meta.STATUS_FAILED)
        self.assertEqual(stored["attempts"][-1]["status"], run_meta.STATUS_FAILED)
        self.assertIsNotNone(stored["run"]["finished"])

    def test_closer_records_seconds(self):
        payload = self.build()
        run_meta.closer(payload, self.out_dir)(ok=True)
        self.assertIsInstance(run_meta.read(self.out_dir)["attempts"][-1]["seconds"], float)

    def test_no_absolute_paths_in_the_file(self):
        """Đường dẫn tuyệt đối của máy này không được lọt vào file."""
        (self.out_dir / "metrics.json").write_text("{}", encoding="utf-8")
        payload = self.build(files=run_meta.input_files(
            [(self.out_dir / "metrics.json", "metrics")]))
        run_meta.write(self.out_dir, payload)
        text = (self.out_dir / "run_meta.json").read_text(encoding="utf-8")

        self.assertNotIn(self._tmp.name, text)
        self.assertNotIn(paths.root().as_posix(), text)
        for entry in payload["files"]:
            self.assertFalse(Path(entry["path"]).is_absolute(), entry["path"])
        self.assertEqual(payload["files"][0]["path"], "metrics.json")

    def test_input_files_skips_missing_and_keeps_sha(self):
        present = self.out_dir / "config.yaml"
        present.write_text("a: 1\n", encoding="utf-8")
        found = run_meta.input_files([(present, run_meta.ROLE_CONFIG),
                                      (self.out_dir / "khong-co.yaml", run_meta.ROLE_PROMPT)])
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["role"], run_meta.ROLE_CONFIG)
        self.assertEqual(len(found[0]["sha256"]), 64)
        self.assertEqual(found[0]["bytes"], present.stat().st_size)

    def test_repo_info_reads_git_sha(self):
        info = run_meta.repo_info(url="u", branch="b")
        self.assertEqual((info["url"], info["branch"]), ("u", "b"))
        self.assertTrue(info["sha"] == "" or re.fullmatch(r"[0-9a-f]{40}", info["sha"]))

    def test_relative_outside_repo_keeps_name_only(self):
        with tempfile.TemporaryDirectory() as folder:
            outside = Path(folder) / "ngoai.txt"
            outside.write_text("x", encoding="utf-8")
            self.assertEqual(run_meta.relative(outside), "ngoai.txt")

    def test_seconds_between_handles_bad_input(self):
        self.assertEqual(run_meta.seconds_between(None, "2026-01-01 00:00:00"), None)
        self.assertEqual(run_meta.seconds_between("2026-01-01 00:00:00",
                                                  "2026-01-01 00:01:00"), 60.0)


if __name__ == "__main__":
    unittest.main()
