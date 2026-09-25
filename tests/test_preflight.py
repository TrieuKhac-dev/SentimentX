# -*- coding: utf-8 -*-
"""Test kiểm trước khi chạy (src/preflight.py).

Điều quan trọng nhất được khoá ở đây: **kiểm trước phải chỉ ra đúng việc còn thiếu, và không bao
giờ ném ra ngoài**. Một lượt val tốn hàng chục phút, nên phát hiện thiếu `test.csv` hay Drive chỉ
đọc muộn hơn là mất cả buổi; còn ném ra ngoài thì notebook dừng ở giữa và không ai biết còn việc gì.

Test dùng dataset THẬT đang có trên đĩa (mã phiên bản tính từ config, không viết cứng), nên nếu
phiên bản dữ liệu đổi thì test vẫn đúng. Test cũng ghi một thí nghiệm và một model config TẠM vào
cây thật (định nghĩa thí nghiệm theo thiết kế nằm trong repo) và xoá sạch trong `cleanup`.

Chạy: python -m unittest discover -s tests
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src import dataset as dataset_module
from src import experiments, model_config, paths, preflight, utils, versioning

TEST_MODEL = "zz-test-model"
TEST_METHOD = "test-method"
TEST_EXP = "exp001"

# Nhóm test cần DỮ LIỆU THẬT (dataset đã xử lý trên đĩa). CI chạy trên bản clone sạch, mà dữ liệu
# không nằm trong git (luật 20 của docs/00_workflow/02_rules.md), nên ở đó chúng tự bỏ qua thay vì
# báo đỏ vì thiếu dữ liệu. Trên máy cá nhân - nơi có dữ liệu - chúng vẫn chạy đủ, vì bỏ qua im lặng
# ở máy có dữ liệu là mất luôn phần kiểm quan trọng nhất của preflight.
HAS_DATASET = versioning.processed_dir(
    versioning.compute_id(dataset_module.load_config("cosmetics"))).is_dir()
requires_dataset = unittest.skipUnless(
    HAS_DATASET,
    "cần dataset đã xử lý trên đĩa (CI không có dữ liệu, xem docs/00_workflow/03_ci.md)")

MODEL_CONFIG = (
    "model_id: {}\n"
    "checkpoint: test/checkpoint\n"
    "config_version: 1\n"
    "approach: prompt\n"
    "preprocess:\n"
    "  max_length: 128\n"
    "inference:\n"
    "  quantization: 4bit\n"
).format(TEST_MODEL)

BASE_CONFIG = (
    "exp_id: exp001\n"
    "parent: null\n"
    "model: {}\n"
    "method: {}\n"
    "data:\n"
    "  dataset: cosmetics\n"
    "  version: v0.1.0\n"
    "  roles: {{train: train, val: val, eval: test}}\n"
    "prompt: prompt.txt\n"
).format(TEST_MODEL, TEST_METHOD)

PROMPT_TEXT = "Phan tich review sau va tra ve JSON.\n{aspets} {text}\n"


class PreflightCase(unittest.TestCase):
    """Lớp cha: một thí nghiệm tạm, và mã phiên bản dữ liệu THẬT đang có trên đĩa."""

    def setUp(self):
        self.model_path = model_config.config_path(TEST_MODEL)
        self.exp_dir = experiments.experiment_dir(TEST_MODEL, TEST_METHOD, TEST_EXP)
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        self.model_path.write_text(MODEL_CONFIG, encoding="utf-8")
        self.exp_dir.mkdir(parents=True, exist_ok=True)
        (self.exp_dir / "config.yaml").write_text(BASE_CONFIG, encoding="utf-8")
        (self.exp_dir / "prompt.txt").write_text(PROMPT_TEXT, encoding="utf-8")
        self.addCleanup(self.cleanup)

        self.dataset = dataset_module.load_config("cosmetics")
        self.version_id = versioning.compute_id(self.dataset)

    def cleanup(self):
        self.model_path.unlink(missing_ok=True)
        shutil.rmtree(paths.experiments_dir() / TEST_MODEL, ignore_errors=True)
        root = paths.experiments_dir()
        if root.is_dir() and not any(root.iterdir()):
            root.rmdir()

    def report(self, **kwargs):
        result = experiments.load(TEST_MODEL, TEST_METHOD, TEST_EXP)
        options = {"ds": self.dataset, "version_id": self.version_id, "model_id": TEST_MODEL}
        options.update(kwargs)
        return preflight.run(result, **options)


class TestWritable(unittest.TestCase):
    def test_ok_on_a_normal_folder(self):
        problems, notes = [], []
        with tempfile.TemporaryDirectory() as folder:
            self.assertTrue(preflight.writable(Path(folder) / "con", "gốc", problems, notes))
        self.assertEqual(problems, [])
        self.assertEqual(len(notes), 1)

    def test_reports_when_the_path_is_not_a_folder(self):
        problems, notes = [], []
        with tempfile.TemporaryDirectory() as folder:
            blocker = Path(folder) / "tep"
            blocker.write_text("x", encoding="utf-8")
            self.assertFalse(preflight.writable(blocker / "con", "gốc", problems, notes))
        self.assertEqual(len(problems), 1)
        self.assertIn("gốc", problems[0])


@requires_dataset
class TestEvalLock(PreflightCase):
    def test_mismatch_is_a_problem(self):
        problems, notes, info = [], [], {}
        fake = {"eval_lock": {"enforce": True,
                              "test": {"file": "test.csv", "sha256": "0" * 64}}}
        preflight.eval_lock_report(fake, self.version_id, problems, notes, info)
        self.assertEqual(len(problems), 1)
        self.assertIn("KHÔNG khớp", problems[0])

    def test_matching_lock_is_reported_as_ok(self):
        problems, notes, info = [], [], {}
        measured = preflight.eval_lock_report(self.dataset, self.version_id, problems, notes, info)
        locked = {"eval_lock": {"enforce": True,
                                "test": {"file": measured["file"],
                                         "sha256": measured["sha256"]}}}
        problems, notes = [], []
        preflight.eval_lock_report(locked, self.version_id, problems, notes, info)
        self.assertEqual(problems, [])
        self.assertTrue(any("khớp" in note for note in notes))

    def test_missing_test_file_is_a_problem(self):
        problems, notes, info = [], [], {}
        preflight.eval_lock_report(self.dataset, "khong-co-phien-ban-nay", problems, notes, info)
        self.assertEqual(len(problems), 1)
        self.assertIn("Thiếu tập đánh giá", problems[0])


class TestEvalLockFromData(unittest.TestCase):
    """Khoá tập đánh giá ghi CÙNG DỮ LIỆU (`data/processed/<mã>/eval_lock.json`).

    Đây là nguồn chính thức, và nó có từ bản dữ liệu ĐẦU TIÊN: nếu chỉ dựa vào giá trị khai trong
    file phiên bản dataset thì bản đầu tiên (sha256 null) không có khoá nào cả, còn các bản sau lại
    thừa hưởng khoá của bản trước - một chuỗi hở ở gốc. Test chạy trên gốc dữ liệu TẠM nên không cần
    dataset thật, và không đụng vào dữ liệu của dự án.
    """

    VERSION_ID = "cosmetics-ds0.1.0-pl0.1.0-srccosmetics@0.1.0-abcdef12"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        patcher = mock.patch.dict(os.environ, {paths.ENV_DATA_ROOT: self._tmp.name})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.directory = paths.processed(self.VERSION_ID)
        self.directory.mkdir(parents=True)
        self.test_csv = self.directory / "test.csv"
        utils.write_csv([["review a"], ["review b"]], ["text"], self.test_csv)

    def dataset(self, sha256=None, enforce=True):
        return {"eval_lock": {"enforce": enforce,
                              "test": {"file": "test.csv", "sha256": sha256}}}

    def lock(self, sha256):
        versioning.write_eval_lock(self.VERSION_ID, {"file": "test.csv", "sha256": sha256,
                                                     "rows": 2})

    def test_khoa_ghi_cung_du_lieu_khop_thi_chi_ghi_chu(self):
        self.lock(versioning.file_sha256(self.test_csv))
        problems, notes, info = [], [], {}
        measured = preflight.eval_lock_report(self.dataset(), self.VERSION_ID, problems, notes, info)
        self.assertEqual(problems, [])
        self.assertEqual(measured["rows"], 2)
        self.assertTrue(any("khớp khoá" in note for note in notes))
        self.assertIn("eval_lock.json", info["eval_lock"]["source"])

    def test_khoa_ghi_cung_du_lieu_lech_thi_la_loi(self):
        self.lock("0" * 64)
        problems, notes, info = [], [], {}
        preflight.eval_lock_report(self.dataset(), self.VERSION_ID, problems, notes, info)
        self.assertEqual(len(problems), 1)
        self.assertIn("KHÔNG khớp", problems[0])
        self.assertIn("eval_lock.json", problems[0])

    def test_chua_co_khoa_thi_ghi_chu_kem_lenh_tao(self):
        problems, notes, info = [], [], {}
        preflight.eval_lock_report(self.dataset(), self.VERSION_ID, problems, notes, info)
        self.assertEqual(problems, [])
        self.assertTrue(any("Chưa có khoá" in note for note in notes))
        self.assertTrue(any("run_pipeline.py" in note for note in notes))

    def test_gia_tri_khai_trong_config_thang_khoa_ghi_cung_du_lieu(self):
        self.lock(versioning.file_sha256(self.test_csv))
        problems, notes, info = [], [], {}
        preflight.eval_lock_report(self.dataset(sha256="0" * 64), self.VERSION_ID,
                                   problems, notes, info)
        self.assertEqual(len(problems), 1)
        self.assertIn("file phiên bản dataset", problems[0])

    def test_enforce_tat_thi_khong_kiem(self):
        problems, notes, info = [], [], {}
        preflight.eval_lock_report(self.dataset(enforce=False), self.VERSION_ID,
                                   problems, notes, info)
        self.assertEqual(problems, [])
        self.assertTrue(any("đang TẮT" in note for note in notes))


class TestDeviceAndSegmenter(PreflightCase):
    def test_device_report_shape(self):
        problems, notes, info = [], [], {}
        preflight.device_report(TEST_MODEL, problems, notes, info)

        self.assertEqual(info["quantization"], "4bit")
        self.assertIn("torch", info)
        if not info["torch"]:
            # Máy chưa có torch, hoặc torch cài hỏng (thiếu DLL, hết bộ nhớ trang).
            self.assertTrue(any("torch" in item for item in problems))
        elif info.get("cuda"):
            self.assertTrue(info.get("gpu"))
            self.assertGreater(info.get("vram_gb") or 0, 0)
        else:
            self.assertTrue(any("GPU" in item for item in problems))

    def test_quantization_needs_bitsandbytes_or_says_so(self):
        """Máy thiếu `torch` vẫn phải được kể là thiếu `bitsandbytes` khi config khai 4-bit.

        Hai việc độc lập: bản đầu của `device_report` thoát sớm khi không nạp được torch, nên trên
        máy chưa cài torch (CI) vấn đề về bitsandbytes biến mất - người chạy sửa xong torch mới biết
        còn thiếu thứ nữa.
        """
        import importlib.util
        problems, notes, info = [], [], {}
        preflight.device_report(TEST_MODEL, problems, notes, info)
        has_bnb = importlib.util.find_spec("bitsandbytes") is not None
        mentions = any("bitsandbytes" in item for item in problems)
        self.assertEqual(mentions, not has_bnb)

    def test_segmenter_of_a_real_model_config(self):
        problems, notes, info = [], [], {}
        name = preflight.segmenter_report("phobert-base-v2", problems, notes, info)
        self.assertEqual(name, "vncorenlp")
        # Chạy được thì có ghi chú; không chạy được (thiếu Java/gói/model) thì phải có VẤN ĐỀ.
        self.assertEqual(bool(problems), not any("bộ tách từ" in note for note in notes))

    def test_model_without_segmenter_is_fine(self):
        problems, notes, info = [], [], {}
        self.assertIsNone(preflight.segmenter_report(TEST_MODEL, problems, notes, info))
        self.assertEqual(problems, [])

    def test_unknown_segmenter_is_a_problem(self):
        problems, notes, info = [], [], {}
        with tempfile.TemporaryDirectory() as folder:
            config = Path(folder) / "x.yaml"   # tên file phải trùng `model_id`
            config.write_text("model_id: x\ncheckpoint: test/x\nconfig_version: 1\n"
                              "approach: prompt\n"
                              "preprocess:\n  max_length: 64\n  segmenter: khong-co\n",
                              encoding="utf-8")
            with mock.patch.object(model_config, "config_path", return_value=config):
                preflight.segmenter_report("x", problems, notes, info)
        self.assertEqual(len(problems), 1)
        self.assertIn("khong-co", problems[0])


class TestStateAndRun(PreflightCase):
    def test_state_without_out_dir_is_a_note(self):
        problems, notes, info = [], [], {}
        self.assertIsNone(preflight.state_report(None, {}, problems, notes, info))
        self.assertEqual(problems, [])
        self.assertTrue(any("out_dir" in note for note in notes))

    def test_state_of_a_fresh_folder_is_new(self):
        problems, notes, info = [], [], {}
        with tempfile.TemporaryDirectory() as folder:
            mode = preflight.state_report(Path(folder) / "run", {}, problems, notes, info)
        self.assertEqual(mode, "NEW")
        self.assertEqual(problems, [])

    @requires_dataset
    def test_full_run_returns_a_report(self):
        with tempfile.TemporaryDirectory() as folder:
            report = self.report(out_dir=Path(folder) / "run")

        self.assertEqual(sorted(report),
                         ["info", "missing", "notes", "problems", "version_id"])
        self.assertEqual(report["version_id"], self.version_id)
        self.assertTrue(any("dataset:" in note for note in report["notes"]))
        self.assertTrue(any("trạng thái: NEW" in note for note in report["notes"]))
        self.assertEqual(sorted(report["info"]["fingerprint"]),
                         ["config_sha256", "data", "sha"])

    def test_full_run_reports_a_broken_config_instead_of_raising(self):
        (self.exp_dir / "config.yaml").write_text(
            BASE_CONFIG + "khong_co_khoa_nay: 1\n", encoding="utf-8")
        report = self.report()
        self.assertTrue(any("khoá lạ" in item for item in report["problems"]))

    def test_check_raises_if_and_only_if_there_are_problems(self):
        """`check()` là bản "dừng ngay" của `run()`: có vấn đề thì ném, không thì trả báo cáo."""
        with tempfile.TemporaryDirectory() as folder:
            result = experiments.load(TEST_MODEL, TEST_METHOD, TEST_EXP)
            out_dir = Path(folder) / "run"
            report = self.report(out_dir=out_dir)
            if report["problems"]:
                with self.assertRaises(preflight.PreflightError):
                    preflight.check(result, ds=self.dataset, version_id=self.version_id,
                                    model_id=TEST_MODEL, out_dir=out_dir)
            else:
                checked = preflight.check(result, ds=self.dataset, version_id=self.version_id,
                                          model_id=TEST_MODEL, out_dir=out_dir)
                self.assertEqual(checked["problems"], [])


class TestRawSource(unittest.TestCase):
    """Dữ liệu GỐC.

    Điều được khoá ở đây: thiếu dữ liệu gốc phải được kể ra ĐẦU TIÊN và kèm lệnh CHẠY ĐƯỢC. Đây là
    việc hay gặp nhất khi chạy notebook trên Colab, vì dữ liệu gốc không nằm trong git (luật 20):
    preflight từng in "chạy `python run_pipeline.py` trước" mà lệnh đó thiếu `--version` nên dán vào
    là lỗi ngay, còn nguyên nhân thật (không có dữ liệu gốc) thì không được nói ra.
    """

    NAMES = ("data_train.csv", "data_val.csv", "data_test.csv", "full_data.csv")

    def make(self, folder):
        return {
            "name": "cosmetics",
            "version": "v0.1.0",
            "splits": {"train": "data_train.csv", "val": "data_val.csv",
                       "test": "data_test.csv"},
            "full": "full_data.csv",
            "_sources": [{"kind": "raw", "name": "cosmetics", "version": "v0.1.0",
                          "dir": Path(folder)}],
        }

    def test_missing_raw_data_is_reported_first_with_a_runnable_command(self):
        problems, notes, info = ["việc khác"], [], {}
        preflight.raw_source_report(self.make("khong/co/thu-muc-nay"), problems, notes, info)
        self.assertEqual(len(problems), 2)
        self.assertIn("dữ liệu GỐC", problems[0])
        self.assertIn("--dataset cosmetics --version v0.1.0", problems[0])
        self.assertEqual(len(info["raw_missing"]), 4)
        self.assertEqual(notes, [])

    def test_present_raw_data_is_a_note_not_a_problem(self):
        problems, notes, info = [], [], {}
        with tempfile.TemporaryDirectory() as folder:
            for name in self.NAMES:
                (Path(folder) / name).write_text("text,a\n", encoding="utf-8")
            preflight.raw_source_report(self.make(folder), problems, notes, info)
        self.assertEqual(problems, [])
        self.assertEqual(info["raw_missing"], [])
        self.assertTrue(any("dữ liệu gốc: đủ (4 file)" in note for note in notes))

    def test_a_dataset_source_is_not_checked_as_raw(self):
        """Nguồn `dataset` nằm trong `data/processed`, việc tồn tại của nó do phép kiểm khác lo."""
        problems, notes, info = [], [], {}
        preflight.raw_source_report(
            {"_sources": [{"kind": "dataset", "dir": Path("khong/co")}]}, problems, notes, info)
        self.assertEqual((problems, info["raw_missing"]), ([], []))

    def test_row_count_ignores_newlines_inside_quoted_fields(self):
        """`eval_lock.rows` là số BẢN GHI, không phải số dòng.

        Review trong bộ dữ liệu này có xuống dòng bên trong ô được trích dẫn: đếm dòng thì tập test
        1518 bản ghi bị ghi thành 2271, và con số sai đó nằm lại trong file phiên bản dataset.
        """
        path = Path(tempfile.mkdtemp()) / "test.csv"
        path.write_text('text,a\n"dong 1\ndong 2",positive\n"x",negative\n', encoding="utf-8")
        self.assertEqual(preflight.count_rows(path), 2)

    def test_pipeline_command_has_both_required_arguments(self):
        self.assertEqual(preflight.pipeline_command({"name": "cosmetics", "version": "v0.1.0"}),
                         "`python run_pipeline.py --dataset cosmetics --version v0.1.0`")
        self.assertIn("<tên dataset>", preflight.pipeline_command(None))


class TestRawFingerprint(unittest.TestCase):
    """Nội dung file gốc phải khớp dấu vân tay đã ghi khi dựng dataset.

    Nội dung file gốc đi vào mã phiên bản dữ liệu, nên một file bị sửa (Excel, Notepad, công cụ tải)
    làm mã đổi và thông báo "chưa có dataset đã xử lý" trở thành ngõ cụt nếu không nói ra file nào.
    Phép kiểm phải CHỊU ĐƯỢC khác biệt kiểu xuống dòng, vì `digest_bytes` chuẩn hoá trước khi băm:
    cùng một bộ dữ liệu trên Windows (CRLF) và trên Colab (LF) KHÔNG được coi là đã đổi.
    """

    NAMES = ("data_train.csv", "full_data.csv")

    def make(self, folder):
        return {"_sources": [{"kind": "raw", "name": "cosmetics", "version": "v0.1.0",
                              "dir": Path(folder)}]}

    def payload(self, folder, names):
        return {"dataset": {"sources": [{"kind": "raw", "dir": str(folder), "files": [
            {"name": name, "sha256": versioning.file_sha256(Path(folder) / name)}
            for name in names]}]}}

    def run_it(self, folder, payload):
        problems, notes, info = [], [], {}
        with mock.patch.object(versioning, "read_processing_log", return_value=payload):
            preflight.raw_fingerprint_report(self.make(folder), "ma", problems, notes, info)
        return problems, notes, info

    def test_matching_data_is_a_note(self):
        with tempfile.TemporaryDirectory() as folder:
            for name in self.NAMES:
                (Path(folder) / name).write_text("text,a\n", encoding="utf-8")
            problems, notes, info = self.run_it(folder, self.payload(folder, self.NAMES))
        self.assertEqual(problems, [])
        self.assertEqual(info["raw_checked"], 2)
        self.assertTrue(any("khớp 2 file" in note for note in notes), notes)

    def test_changed_content_is_an_error_naming_the_file(self):
        with tempfile.TemporaryDirectory() as folder:
            for name in self.NAMES:
                (Path(folder) / name).write_text("text,a\n", encoding="utf-8")
            payload = self.payload(folder, self.NAMES)
            (Path(folder) / "data_train.csv").write_text("text,a\nsua roi\n", encoding="utf-8")
            problems, _notes, _info = self.run_it(folder, payload)
        self.assertEqual(len(problems), 1)
        self.assertIn("data_train.csv", problems[0])
        self.assertIn("ĐỔI", problems[0])
        self.assertNotIn("full_data.csv", problems[0])

    def test_line_endings_do_not_count_as_a_change(self):
        with tempfile.TemporaryDirectory() as folder:
            for name in self.NAMES:
                (Path(folder) / name).write_text("text,a\n", encoding="utf-8")
            payload = self.payload(folder, self.NAMES)
            # Cùng nội dung, khác kiểu xuống dòng: Windows ghi CRLF, Colab ghi LF.
            (Path(folder) / "data_train.csv").write_bytes("text,a\n".replace("\n", "\r\n").encode())
            problems, notes, _info = self.run_it(folder, payload)
        self.assertEqual(problems, [])
        self.assertTrue(any("khớp 2 file" in note for note in notes), notes)

    def test_missing_file_is_an_error(self):
        with tempfile.TemporaryDirectory() as folder:
            for name in self.NAMES:
                (Path(folder) / name).write_text("text,a\n", encoding="utf-8")
            payload = self.payload(folder, self.NAMES)
            (Path(folder) / "full_data.csv").unlink()
            problems, _notes, _info = self.run_it(folder, payload)
        self.assertEqual(len(problems), 1)
        self.assertIn("thiếu file", problems[0])
        self.assertIn("full_data.csv", problems[0])

    def test_without_a_recorded_log_it_stays_quiet(self):
        problems, notes, info = self.run_it("khong/co/thu-muc-nay", {})
        self.assertEqual((problems, notes), ([], []))
        self.assertNotIn("raw_checked", info)


if __name__ == "__main__":
    unittest.main()

