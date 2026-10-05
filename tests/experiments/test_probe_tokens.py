# -*- coding: utf-8 -*-
"""Test `scripts/probe_tokens.py`: đo phân vị token SINH RA để chốt trần `max_new_tokens`.

VÌ SAO CẦN
Con số quyết định trần token là con số quyết định CẢ lượt chạy: trần quá nhỏ thì lượt bị cắt mà cửa
`% đọc được` vẫn có thể qua, trần quá lớn thì vô ích. Ba chỗ dễ sai và đều im lặng: làm tròn XUỐNG thay
vì lên (hụt một token là mẫu dài nhất bị cắt), tự hạ trần khi vượt cửa sổ ngữ cảnh, và đọc nhầm cột
token (ra số vô nghĩa mà không báo). Test khoá lại đúng ba chỗ đó.

Chạy: python -m unittest discover -s tests
"""

import csv
import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from src.core import paths, utils

# `scripts/` không phải package nên nạp bằng đường dẫn (như tests/workflow/test_cli.py).
SPEC = importlib.util.spec_from_file_location(
    "probe_tokens", paths.root() / "scripts" / "probe_tokens.py")
probe_tokens = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe_tokens)


def write_run(directory, tokens, column=None, meta=True):
    """Lượt chạy tổng hợp đủ để `rescore.settings` đọc được: `predictions.csv` + `run_meta.json`."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    name = column or probe_tokens.COLUMN
    path = directory / paths.pattern("predictions")
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["chỉ số", name, "giây", "split", "nhãn đúng", "nhãn đoán"])
        for index, value in enumerate(tokens):
            writer.writerow([index, value, "0.1", "test", "{}", "{}"])
    if meta:
        (directory / paths.pattern("run_meta")).write_text(
            json.dumps({"split": "test", "experiment": {"model": "model-x"}}), encoding="utf-8")
    return directory


class CeilingTest(unittest.TestCase):
    """Trần = làm tròn LÊN (p99 × hệ số); vượt cửa sổ ngữ cảnh là LỖI."""

    def test_lam_tron_len_chu_khong_lam_tron_xuong(self):
        # 1323 × 1,5 = 1984,5 -> 1985 (làm tròn xuống là 1984, hụt một token).
        self.assertEqual(probe_tokens.ceiling_for(1323), 1985)

    def test_he_so_1_giu_nguyen_p99(self):
        self.assertEqual(probe_tokens.ceiling_for(1323, factor=1.0), 1323)

    def test_vuot_cua_so_ngu_canh_thi_bao_loi_kem_hai_so(self):
        with self.assertRaises(probe_tokens.ProbeError) as found:
            probe_tokens.ceiling_for(1323, context_window=1000)
        self.assertIn("1985", str(found.exception))
        self.assertIn("1000", str(found.exception))


class SummariseTest(unittest.TestCase):
    """Phân vị lấy từ `utils.length_stats` (một định nghĩa duy nhất), và luật "bị cắt" của metrics.md."""

    def test_phan_vi_lay_tu_dung_ham_cua_du_an(self):
        tokens = [10, 20, 30, 40, 50, 600]
        found = probe_tokens.summarise(tokens)
        stats = utils.length_stats(tokens, "token sinh")
        self.assertEqual(found["token sinh"]["p50"], stats["p50"])
        self.assertEqual(found["token sinh"]["p99"], stats["p99"])
        self.assertEqual(found["token sinh"]["lớn nhất"], stats["lớn nhất"])

    def test_dem_mau_cham_tran(self):
        found = probe_tokens.summarise([10, 400, 400, 399], ceiling=400)
        self.assertEqual(found["chạm_trần"]["số mẫu"], 2)
        self.assertEqual(found["chạm_trần"]["% mẫu"], 50.0)
        # Trung bình 302,25 / 400 = 0,76 < 0,95 -> KHÔNG bị cắt.
        self.assertFalse(found["chạm_trần"]["bị_cắt"])

    def test_trung_binh_cham_nguong_95_phan_tram_thi_la_bi_cat(self):
        found = probe_tokens.summarise([400, 400, 400], ceiling=400)
        self.assertTrue(found["chạm_trần"]["bị_cắt"])

    def test_khong_truyen_tran_thi_khong_kiem_dieu_kien_cat(self):
        self.assertNotIn("chạm_trần", probe_tokens.summarise([400, 400]))


class ReadTokensTest(unittest.TestCase):
    """Đọc `predictions.csv` thật: thiếu tệp / thiếu `run_meta.json` / sai cột đều phải báo LỖI."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="probe-"))

    def test_doc_dung_cot_token_sinh(self):
        run = write_run(self.root / "run", [12, 34, 56])
        tokens, context = probe_tokens.read_tokens(run)
        self.assertEqual(tokens, [12, 34, 56])
        self.assertEqual(context["meta"]["split"], "test")

    def test_sai_ten_cot_thi_bao_loi_chu_khong_ra_so_vo_nghia(self):
        run = write_run(self.root / "run", [12], column="token")
        with self.assertRaises(probe_tokens.ProbeError) as found:
            probe_tokens.read_tokens(run)
        self.assertIn(probe_tokens.COLUMN, str(found.exception))

    def test_thieu_run_meta_thi_bao_loi(self):
        run = write_run(self.root / "run", [12], meta=False)
        with self.assertRaises(probe_tokens.ProbeError):
            probe_tokens.read_tokens(run)


class CliTest(unittest.TestCase):
    """Cờ dòng lệnh và đường đi đầy đủ (đọc lượt -> in số -> ghi JSON)."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="probe-"))

    def mistake(self, argv):
        return probe_tokens.check_args(probe_tokens.parse_args(argv))

    def test_he_so_phai_lon_hon_0(self):
        self.assertIn("--factor", self.mistake(["--run", "x", "--factor", "0"]))

    def test_cua_so_ngu_canh_phai_lon_hon_0(self):
        self.assertIn("--context-window", self.mistake(["--run", "x", "--context-window", "0"]))

    def test_thieu_thu_muc_thi_ma_thoai_2(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(probe_tokens.main(["--run", str(self.root / "khong-co")]), 2)

    def test_chay_duoc_va_ghi_json(self):
        run = write_run(self.root / "run", [100, 200, 300, 400, 500])
        out = self.root / "out" / "tokens.json"
        with redirect_stdout(io.StringIO()) as screen:
            self.assertEqual(probe_tokens.main(["--run", str(run), "--ceiling", "500",
                                                "--out", str(out)]), 0)
        report = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(report["số mẫu"], 5)
        self.assertEqual(report["trần_đang_dùng"], 500)
        self.assertEqual(report["chạm_trần"]["số mẫu"], 1)
        self.assertIn("Trần đề xuất", screen.getvalue())


if __name__ == "__main__":
    unittest.main()
