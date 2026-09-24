# -*- coding: utf-8 -*-
"""Test lớp CHẠY THÍ NGHIỆM (src/experiment_run.py) và việc nhận prompt theo tên/đường dẫn.

Ba điều được khoá ở đây:

1. Kết quả chạy TRONG thí nghiệm phải nằm dưới `experiments/<model>/<method>/<expNNN>/results/`,
   không được lẫn vào thư mục đánh giá dùng chung - lẫn là sau này không biết con số thuộc thí
   nghiệm nào, mà đó chính là nội dung của bản refactor này.
2. Prompt nhận CẢ HAI dạng: tên trong thư viện dùng chung, và đường dẫn tới file nằm cạnh
   notebook của thí nghiệm. Sau khi nạp, `qwen.load_prompt(<tên>)` phải trả lại ĐÚNG prompt đó -
   không đi tìm trong thư viện (prompt của thí nghiệm không nằm ở đó).
3. Bước LẬP KẾ HOẠCH không được đụng tới model/GPU: đây là bước hay hỏng nhất (thiếu file, sai tên
   split, lệch mã phiên bản) và phải kiểm được trong vài giây.

Chạy: python -m unittest discover -s tests
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from src import config, dataset, experiment_run, experiments, paths, prompts
from src.preprocessing import qwen

ROOT = Path(__file__).resolve().parents[1]


class HelpersTest(unittest.TestCase):
    """Các hàm thuần: đọc config, dựng tên thư mục, chọn chỗ ghi kết quả."""

    def test_split_lay_tu_vai_eval(self):
        self.assertEqual(experiment_run.split_of({"data": {"roles": {"eval": "val"}}}), "val")
        with self.assertRaises(experiment_run.RunError):
            experiment_run.split_of({"data": {"roles": {}}})

    def test_limit_rong_nghia_la_ca_split(self):
        self.assertEqual(experiment_run.limit_of({"n": None}), 0)
        self.assertEqual(experiment_run.limit_of({}), 0)
        self.assertEqual(experiment_run.limit_of({"n": 200}), 200)

    def test_greedy_la_mac_dinh_lay_mau_moi_them_nhiet_do(self):
        settings, sampled = experiment_run.settings_of({})
        self.assertFalse(sampled)
        self.assertEqual(settings, {})
        settings, sampled = experiment_run.settings_of({"decoding": {"mode": "sample"}})
        self.assertTrue(sampled)
        self.assertEqual(settings["temperature"], experiment_run.CARD_SETTINGS["temperature"])
        settings, _ = experiment_run.settings_of({"decoding": {"mode": "greedy",
                                                              "temperature": 0.2}})
        self.assertEqual(settings["temperature"], 0.2)

    def test_tag_ghi_ro_cau_hinh(self):
        greedy = experiment_run.build_tag("absa_cot_v1", "val", 200, False, None)
        self.assertEqual(greedy, "prompt-absa_cot_v1__val__n200__greedy")
        full = experiment_run.build_tag("absa_cot_v1", "test", 0, True, "4bit")
        self.assertEqual(full, "prompt-absa_cot_v1__test__sample__4bit")

    def test_ket_qua_trong_thi_nghiem_di_vao_thu_muc_thi_nghiem(self):
        inside, flag = experiment_run.out_dir_of("v1", "tag", "model", "method", "exp001")
        self.assertTrue(flag)
        self.assertTrue(inside.as_posix().startswith(
            paths.experiment_dir("model", "method", "exp001").as_posix()))
        outside, flag = experiment_run.out_dir_of("v1", "tag")
        self.assertFalse(flag)
        self.assertEqual(outside, config.MODEL_EVAL_REPORT_DIR / "v1" / "tag")

    def test_doi_ten_nhan_theo_ma_so(self):
        names = experiment_run.label_names({"id_to_label": {0: "không", 1: "có"}})
        self.assertEqual(names, {0: "không", 1: "có"})


class ResolveTest(unittest.TestCase):
    """Nhận prompt theo TÊN hoặc theo ĐƯỜNG DẪN (prompt riêng của thí nghiệm)."""

    def test_ten_tran_la_ten_trong_thu_vien(self):
        name, path = prompts.resolve("absa_cot_v1")
        self.assertEqual(name, "absa_cot_v1")
        self.assertEqual(path, prompts.prompt_path("absa_cot_v1"))

    def test_ten_tran_cua_file_vi_du_di_vao_thu_muc_examples(self):
        _name, path = prompts.resolve("absa_cot_v1", examples=True)
        self.assertEqual(path, prompts.examples_path("absa_cot_v1"))

    def test_duong_dan_tinh_tu_thu_muc_thi_nghiem_truoc(self):
        tmp = Path(tempfile.mkdtemp(prefix="sentimentx-resolve-"))
        try:
            (tmp / "prompt.txt").write_text("{text}", encoding="utf-8")
            name, path = prompts.resolve("prompt.txt", base_dir=tmp)
            self.assertEqual(name, "prompt")
            self.assertEqual(path, tmp / "prompt.txt")
            # Đường dẫn không có trong thư mục thí nghiệm thì tính từ gốc repo.
            _name, missing = prompts.resolve("khong/co/that.txt", base_dir=tmp)
            self.assertEqual(missing, ROOT / "khong" / "co" / "that.txt")
        finally:
            shutil.rmtree(str(tmp), ignore_errors=True)

    def test_thieu_gia_tri_thi_bao_loi(self):
        with self.assertRaises(prompts.PromptError):
            prompts.resolve("   ")


class PlanTest(unittest.TestCase):
    """Lập kế hoạch cho một lần chạy thật (không cần GPU)."""

    @classmethod
    def setUpClass(cls):
        cls.merged = experiments.load_shared(qwen.CONFIG_NAME)
        names = prompts.available()
        if not names:
            raise unittest.SkipTest("chưa có prompt nào trong configs/prompts/")
        cls.prompt_name = names[0]

    def _plan(self, **kwargs):
        try:
            return experiment_run.plan(self.merged, split="val", limit=3,
                                       prompt=self.prompt_name, **kwargs)
        except (FileNotFoundError, dataset.DatasetError) as exc:
            self.skipTest("chưa có dữ liệu đã xử lý trên máy này: {}".format(exc))

    def test_plan_khong_can_model_va_dang_ky_prompt(self):
        plan = self._plan()
        self.assertEqual(plan["split"], "val")
        self.assertEqual(len(plan["texts"]), 3)
        self.assertTrue(all(0 <= index < plan["total"] for index in plan["row_index"]))
        self.assertEqual(sorted(plan["row_index"]), plan["row_index"])
        self.assertTrue(plan["names"])
        self.assertTrue(plan["files"])
        self.assertEqual(plan["mode"], "NEW")
        # Prompt phải nằm trong "sổ" của qwen: các bước sau chỉ truyền được một cái TÊN.
        self.assertIs(qwen.load_prompt(plan["prompt"].name), plan["prompt"])
        self.assertFalse(plan["sampled"])
        self.assertIsNone(plan["generation"]["temperature"])

    def test_plan_trong_thi_nghiem_ghi_vao_thu_muc_thi_nghiem(self):
        plan = self._plan(model_id="model", method="method", exp_id="exp001")
        self.assertTrue(plan["inside"])
        self.assertTrue(plan["out_dir"].as_posix().startswith(
            paths.experiment_dir("model", "method", "exp001").as_posix()))
        self.assertEqual(plan["info"]["experiment"],
                         {"model": "model", "method": "method", "exp_id": "exp001"})

    def test_plan_prompt_nam_canh_thi_nghiem(self):
        source = prompts.prompt_path(self.prompt_name)
        if not source.is_file():
            self.skipTest("prompt {} không có file".format(self.prompt_name))
        tmp = Path(tempfile.mkdtemp(prefix="sentimentx-exp-"))
        try:
            shutil.copyfile(str(source), str(tmp / "prompt.txt"))
            plan = experiment_run.plan(dict(self.merged, dir=str(tmp)), split="val", limit=2,
                                       prompt="prompt.txt")
            self.assertEqual(plan["prompt"].name, "prompt")
            self.assertEqual(plan["prompt"].path, tmp / "prompt.txt")
            self.assertEqual(len(plan["texts"]), 2)
            self.assertIs(qwen.load_prompt("prompt"), plan["prompt"])
        except (FileNotFoundError, dataset.DatasetError) as exc:
            self.skipTest("chưa có dữ liệu đã xử lý trên máy này: {}".format(exc))
        finally:
            shutil.rmtree(str(tmp), ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

