# -*- coding: utf-8 -*-
"""Test `build_report.py`: chọn đích, mã thoát, mục CẦN CHẠY, link và `--open`.

VÌ SAO CẦN
Luật của công cụ này là "không đoán": thiếu tham số thì PHẢI lỗi (mã 2), không được lặng lẽ vẽ một
đích khác. Trước 28/09/2026 nó tự lấy thư mục kết quả ĐẦU TIÊN, nên `--phase eda` bỏ qua báo cáo EDA
của dataset mà không ai biết. Test dựng gốc dữ liệu TẠM và chặn phần vẽ (mock), nên chỉ kiểm logic.

Chạy: python -m unittest discover -s tests
"""

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import build_report as br
from src import paths

RAW = "v0.1.0"
RAW_PENDING = "v0.2.0"
NAME = "cosmetics"
BUILD = "cosmetics-ds0.1.0-pl0.1.0-srccosmetics@0.1.0-e0ccc484"
BUILD_PENDING = "cosmetics-ds0.2.0-pl0.1.0-srccosmetics@0.1.0-9c0d1e2f"
HASH8 = "e0ccc484"


def payload(phase, version_id, dataset=NAME):
    """Payload tối thiểu: test này không kiểm nội dung báo cáo, chỉ kiểm luật chọn đích."""
    return {"schema": 1, "phase": phase, "dataset": dataset, "version_id": version_id,
            "generated_at": "01/01/2026 00:00", "meta": [], "sections": []}


class BuildReportCase(unittest.TestCase):
    """Gốc dữ liệu tạm có đủ 4 tình trạng: có kết quả, đang thiếu, và 2 phiên bản."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        patcher = mock.patch.dict(os.environ, {paths.ENV_DATA_ROOT: self._tmp.name})
        patcher.start()
        self.addCleanup(patcher.stop)
        root = Path(self._tmp.name)
        self.ready_raw = root / "raw" / NAME / RAW / "eda"
        self.pending_raw = root / "raw" / NAME / RAW_PENDING
        self.ready_eda = root / "processed" / BUILD / "eda"
        self.ready_pipeline = root / "processed" / BUILD / "pipeline"
        self.pending_build = root / "processed" / BUILD_PENDING
        for directory in (self.ready_raw, self.pending_raw, self.ready_eda,
                          self.ready_pipeline, self.pending_build):
            directory.mkdir(parents=True)
        self._write(self.ready_raw, "eda_result.json", payload("eda", BUILD))
        self._write(self.ready_eda, "eda_result.json", payload("eda", BUILD))
        self._write(self.ready_pipeline, "pipeline_result.json", payload("pipeline", BUILD))

    @staticmethod
    def _write(directory, name, data):
        (directory / name).write_text(json.dumps(data), encoding="utf-8")

    def run_cli(self, argv, drawn=None, opened=None):
        """Chạy `main` với phần vẽ và trình duyệt bị chặn. Trả về `(mã thoát, stdout)`."""
        buffer = io.StringIO()
        writer = mock.Mock(return_value=Path(self._tmp.name) / "report.html")
        with mock.patch.object(br.render, "write_reports", writer), \
                mock.patch.object(br.webbrowser, "open") as opener, \
                redirect_stdout(buffer):
            code = br.main(list(argv))
        if drawn is not None:
            self.assertEqual(writer.call_count, drawn)
        if opened is not None:
            self.assertEqual(opener.call_count, opened)
        return code, buffer.getvalue()

    # --- phải chỉ rõ đích, nếu không thì LỖI (mã 2) ---

    def test_bare_command_is_refused(self):
        code, text = self.run_cli([], drawn=0)
        self.assertEqual(code, 2)
        self.assertIn("thiếu `--on`", text)

    def test_phase_alone_is_refused(self):
        code, text = self.run_cli(["--phase", "eda"], drawn=0)
        self.assertEqual(code, 2)
        self.assertIn("thiếu `--on`", text)

    def test_pipeline_alone_is_refused(self):
        code, _ = self.run_cli(["--phase", "pipeline"], drawn=0)
        self.assertEqual(code, 2)

    def test_raw_needs_name_and_version(self):
        code, text = self.run_cli(["--phase", "eda", "--on", "raw"], drawn=0)
        self.assertEqual(code, 2)
        self.assertIn("--name", text)

    def test_dataset_needs_hash(self):
        code, text = self.run_cli(["--phase", "eda", "--on", "dataset"], drawn=0)
        self.assertEqual(code, 2)
        self.assertIn("--hash", text)

    def test_pipeline_with_raw_source_is_refused(self):
        code, text = self.run_cli(["--phase", "pipeline", "--on", "raw",
                                   "--name", NAME, "--version", RAW], drawn=0)
        self.assertEqual(code, 2)
        self.assertIn("pipeline chỉ có nguồn", text)

    def test_removed_syntax_is_diagnosed(self):
        code, text = self.run_cli(["--dataset", NAME], drawn=0)
        self.assertEqual(code, 2)
        self.assertIn("`--dataset` đã bỏ", text)
        code, text = self.run_cli(["--phase", "all"], drawn=0)
        self.assertEqual(code, 2)
        self.assertIn("dùng `--all`", text)

    def test_unknown_hash_lists_what_exists(self):
        code, text = self.run_cli(["--phase", "eda", "--on", "dataset",
                                   "--hash", "deadbeef"], drawn=0)
        self.assertEqual(code, 2)
        self.assertIn(HASH8, text)

    def test_name_conflicting_with_hash_is_refused(self):
        """Tên dataset trong `--name` phải khớp mã trong `--hash`."""
        with mock.patch.object(br, "check_dataset", return_value=True):
            code, text = self.run_cli(["--phase", "eda", "--on", "dataset",
                                       "--hash", HASH8, "--name", "khac"], drawn=0)
        self.assertEqual(code, 2)
        self.assertIn("không khớp", text)

    def test_unknown_dataset_name_is_reported_without_traceback(self):
        """Gõ sai tên dataset: báo gọn kèm danh sách (bug cũ: `config_path` ném DatasetError)."""
        code, text = self.run_cli(["--phase", "eda", "--on", "raw", "--name", "khong-co",
                                   "--version", RAW], drawn=0)
        self.assertEqual(code, 2)
        self.assertIn("Không có dataset tên 'khong-co'", text)
        self.assertIn(NAME, text)

    # --- đích rõ ràng thì vẽ đúng một báo cáo, và MẶC ĐỊNH không mở trình duyệt ---

    def test_exact_raw_target_draws_one(self):
        code, _ = self.run_cli(["--phase", "eda", "--on", "raw", "--name", NAME,
                                "--version", RAW], drawn=1, opened=0)
        self.assertEqual(code, 0)

    def test_exact_dataset_target_draws_one(self):
        code, _ = self.run_cli(["--phase", "eda", "--on", "dataset", "--hash", HASH8],
                               drawn=1, opened=0)
        self.assertEqual(code, 0)

    def test_full_edition_id_is_accepted_too(self):
        code, _ = self.run_cli(["--phase", "pipeline", "--on", "dataset", "--hash", BUILD],
                               drawn=1)
        self.assertEqual(code, 0)

    def test_all_draws_every_target_with_results(self):
        code, text = self.run_cli(["--all"], drawn=3, opened=0)
        self.assertEqual(code, 0)
        self.assertIn("CHƯA CÓ KẾT QUẢ (3 đích)", text)
        self.assertIn("run_eda.py --on raw --name cosmetics --version v0.2.0", text)

    def test_pending_target_exits_one_with_the_command_to_run(self):
        code, text = self.run_cli(["--phase", "eda", "--on", "raw", "--name", NAME,
                                   "--version", RAW_PENDING], drawn=0)
        self.assertEqual(code, 1)
        self.assertIn("chạy trước: python run_eda.py --on raw", text)

    def test_open_flag_opens_every_report(self):
        code, _ = self.run_cli(["--all", "--open"], drawn=3, opened=3)
        self.assertEqual(code, 0)

    def test_no_open_flag_is_honoured(self):
        code, _ = self.run_cli(["--all", "--no-open"], drawn=3, opened=0)
        self.assertEqual(code, 0)

    def test_links_are_printed_for_clicking(self):
        code, text = self.run_cli(["--phase", "eda", "--on", "dataset", "--hash", HASH8])
        self.assertEqual(code, 0)
        self.assertIn("file:///", text)

    def test_list_prints_copyable_commands(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = br.main(["--list"])
        self.assertEqual(code, 0)
        text = buffer.getvalue()
        self.assertIn("--on dataset --hash " + HASH8, text)
        self.assertIn("--on raw --name cosmetics --version v0.1.0", text)


if __name__ == "__main__":
    unittest.main()
