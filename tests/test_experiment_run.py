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

import io
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from src import (config, dataset, experiment_run, experiments, paths, preflight, prompts, resume,
                 runlog, versioning)
from src.preprocessing import qwen

ROOT = Path(__file__).resolve().parents[1]


class NoRootOverrideMixin:
    """Bỏ ghi đè gốc đường dẫn của MÁY đang chạy trong lúc test.

    `plan()` và `out_dir_of()` đọc gốc kết quả, nên máy nào đặt sẵn `SENTIMENTX_RESULTS_ROOT`
    (biến dùng khi chạy trên Colab) thì các phép so với đường dẫn dựng từ repo sẽ sai dù code
    không sai. Bỏ hai biến đó trong lúc chạy test và trả lại nguyên trạng sau khi xong.
    """

    def setUp(self):
        patcher = mock.patch.dict(os.environ)
        patcher.start()
        self.addCleanup(patcher.stop)
        for name in (paths.ENV_DATA_ROOT, paths.ENV_RESULTS_ROOT):
            os.environ.pop(name, None)


class HelpersTest(NoRootOverrideMixin, unittest.TestCase):
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

    def test_config_de_trong_thi_lay_khuyen_nghi_cua_model_card(self):
        # `configs/experiments/evaluation.yaml` để null cho temperature/top_p (chưa khai). Chạy ở
        # chế độ sample thì phải dùng ĐÚNG khuyến nghị model card: 1.0 không phải một lựa chọn của
        # dự án, nó là giá trị "không đè gì" và làm mất luôn khuyến nghị.
        settings, sampled = experiment_run.settings_of(
            {"decoding": {"mode": "sample", "temperature": None, "top_p": None}})
        self.assertTrue(sampled)
        self.assertEqual(settings["temperature"], experiment_run.CARD_SETTINGS["temperature"])
        self.assertEqual(settings["top_p"], experiment_run.CARD_SETTINGS["top_p"])
        # Còn khi config khai số cụ thể thì config thắng - đó là chỗ để ghi lý do đè.
        settings, _ = experiment_run.settings_of(
            {"decoding": {"mode": "sample", "temperature": 0.2, "top_p": 0.9}})
        self.assertEqual(settings["temperature"], 0.2)
        self.assertEqual(settings["top_p"], 0.9)

    def test_run_hash_lay_tam_ky_tu_dau_cua_ma_bam(self):
        self.assertEqual(experiment_run.run_hash("1a2b3c4d5e6f"), "1a2b3c4d")
        self.assertEqual(experiment_run.run_hash("abc"), "abc")

    def test_ket_qua_di_vao_thu_muc_thi_nghiem_theo_ma_bam(self):
        folder = experiment_run.out_dir_of("1a2b3c4d", "model", "method", "exp001")
        self.assertTrue(folder.as_posix().startswith(
            paths.experiment_dir("model", "method", "exp001").as_posix()))
        self.assertEqual(folder.name, "1a2b3c4d")

    def test_thieu_dinh_danh_thi_nghiem_la_loi(self):
        """Không còn chỗ ghi ngoài thí nghiệm, nên thiếu bộ ba định danh là LỖI có hướng dẫn."""
        with self.assertRaises(experiment_run.RunError) as caught:
            experiment_run.out_dir_of("1a2b3c4d", "model", None, "exp001")
        self.assertIn("method", str(caught.exception))
        self.assertIn("new_experiment.py", str(caught.exception))

    def test_batch_size_lay_tu_config_cua_model(self):
        """Đúng lỗi đã xảy ra: notebook gọi `plan()` không truyền batch, mà plan cũng không lấy từ
        config, nên `batch_size` là None và lượt sinh chết ở `range(0, n, None)`."""
        self.assertEqual(
            experiment_run.batch_size_of("qwen3-4b-instruct-2507",
                                         {"inference": {"batch_size": 8}}), 8)

    def test_thieu_batch_size_thi_bao_loi_kem_duong_dan_file(self):
        with self.assertRaises(experiment_run.RunError) as caught:
            experiment_run.batch_size_of("qwen3-4b-instruct-2507", {"inference": {}})
        self.assertIn("batch_size", str(caught.exception))
        self.assertIn("qwen3-4b-instruct-2507.yaml", str(caught.exception))

    def test_log_config_ghi_bang_de_va_gia_tri_hieu_luc(self):
        """Bảng ghi đè phải vào FILE: notebook gửi cho giảng viên đã bị làm sạch output."""
        plan = {"config": {"label_space": "binary", "neutral_policy": "drop",
                           "not_mentioned": "separate"},
                "merged": {"overrides": [["n", 100, 200, "experiment"]]},
                "model_id": "qwen3-4b-instruct-2507", "method": "prompt-cot", "exp_id": "exp001",
                "version_id": "cosmetics-ds0.1.0", "split": "val", "limit": 200,
                "max_length": 2304, "batch_size": 8,
                "generation": {"max_new_tokens": 400, "do_sample": False, "temperature": None,
                               "top_p": None, "top_k": None, "seed": None},
                "prompt": prompts.load("absa_cot_v1"), "examples": None, "sampled": False}
        with tempfile.TemporaryDirectory() as tmp:
            with runlog.start(Path(tmp) / "tag") as log:
                experiment_run.log_config(plan, log)
            text = (Path(tmp) / "tag" / "run.log").read_text(encoding="utf-8")
        self.assertIn("[CONFIG] đè n: 100 <- 200", text)
        self.assertIn("label_space=binary", text)
        self.assertIn("prompt: absa_cot_v1", text)
        # Ngưỡng cắt và cách sinh phải nằm trong FILE: màn hình thì notebook không giữ lại.
        self.assertIn("max_length=2304", text)
        self.assertIn("max_new_tokens=400", text)
        self.assertIn("batch=8", text)

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


class ExamplesDefaultTest(unittest.TestCase):
    """File ví dụ few-shot: suy ra được theo TÊN, KHÔNG suy ra theo đường dẫn."""

    def test_prompt_goi_bang_ten_thi_vi_du_cung_ten(self):
        self.assertEqual(prompts.load("absa_cot_v1").examples_value, "absa_cot_v1")

    def test_prompt_goi_bang_duong_dan_thi_vi_du_chua_khai(self):
        source = prompts.prompt_path("absa_cot_v1")
        if not source.is_file():
            self.skipTest("chưa có prompt absa_cot_v1 trong thư viện")
        tmp = Path(tempfile.mkdtemp(prefix="sentimentx-examples-"))
        try:
            shutil.copyfile(str(source), str(tmp / "prompt.txt"))
            prompt = prompts.load("prompt.txt", base_dir=tmp)
            # None chứ KHÔNG phải đường dẫn tới file prompt: lấy file prompt làm file ví dụ là lỗi
            # im lặng - model nhận cả file prompt ở chỗ đáng lẽ là vài ví dụ mẫu, số liệu vẫn ra.
            self.assertIsNone(prompt.examples_value)
            with self.assertRaises(prompts.PromptError):
                prompts.examples_info(prompt.examples_value, base_dir=tmp)
        finally:
            shutil.rmtree(str(tmp), ignore_errors=True)


class PlanTest(NoRootOverrideMixin, unittest.TestCase):
    """Lập kế hoạch cho một lần chạy thật (không cần GPU)."""

    @classmethod
    def setUpClass(cls):
        cls.merged = experiments.load_shared(qwen.CONFIG_NAME)
        names = prompts.available()
        if not names:
            raise unittest.SkipTest("chưa có prompt nào trong configs/prompts/")
        cls.prompt_name = names[0]

    def _plan(self, **kwargs):
        # Mọi lượt chạy đều thuộc MỘT thí nghiệm (không còn đường ghi ngoài thí nghiệm), nên bộ ba
        # định danh là bắt buộc - test truyền sẵn, test nào muốn kiểm thiếu thì đè lại.
        options = {"model_id": "model", "method": "method", "exp_id": "exp001"}
        options.update(kwargs)
        try:
            return experiment_run.plan(self.merged, split="val", limit=3,
                                       prompt=self.prompt_name, **options)
        except (FileNotFoundError, dataset.DatasetError) as exc:
            self.skipTest("chưa có dữ liệu đã xử lý trên máy này: {}".format(exc))

    def test_plan_lay_batch_size_tu_config_model(self):
        """Notebook không truyền `batch_size`, nên plan phải lấy từ `inference.batch_size`."""
        plan = self._plan()
        self.assertEqual(plan["batch_size"], 8)

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
        plan = self._plan()
        self.assertTrue(plan["out_dir"].as_posix().startswith(
            paths.experiment_dir("model", "method", "exp001").as_posix()))
        # Tên thư mục CHÍNH LÀ mã băm danh tính (8 ký tự), không phải câu mô tả cấu hình.
        self.assertEqual(plan["out_dir"].name, plan["hash"])
        self.assertEqual(len(plan["hash"]), 8)
        self.assertEqual(plan["info"]["experiment"],
                         {"model": "model", "method": "method", "exp_id": "exp001"})

    def test_thieu_thi_nghiem_la_loi(self):
        """Không còn chỗ ghi nào NGOÀI thí nghiệm: thiếu định danh thì DỪNG, không tự chọn chỗ khác."""
        with self.assertRaises(experiment_run.RunError) as caught:
            self._plan(model_id=None, method=None, exp_id=None)
        self.assertIn("thí nghiệm", str(caught.exception))
        self.assertIn("new_experiment.py", str(caught.exception))

    def test_doi_commit_thi_doi_ma_bam(self):
        """Mã băm danh tính có commit: cùng cấu hình nhưng khác bản code là THƯ MỤC KHÁC."""
        plan = self._plan()
        other = dict(plan["repo"])
        other["sha"] = "f" * 40
        with mock.patch.object(experiment_run.run_meta, "repo_info", return_value=other):
            changed = self._plan()
        self.assertNotEqual(plan["hash"], changed["hash"])
        self.assertTrue(changed["out_dir"].name.startswith(changed["hash"]))

    def test_plan_khong_dong_vao_dia(self):
        """`plan()` chỉ lập kế hoạch: không tạo thư mục kết quả, không chuyển/xoá kết quả cũ.

        Không còn `_bo-qua-*` để chuyển: thư mục kết quả là duy nhất theo mã băm danh tính, nên
        không có chuyện hai phép đo chen vào một thư mục.
        """
        plan = self._plan()
        self.assertFalse(plan["out_dir"].exists())
        self.assertFalse(hasattr(experiment_run.resume.Parts, "stash"))

    def test_plan_prompt_nam_canh_thi_nghiem(self):
        source = prompts.prompt_path(self.prompt_name)
        if not source.is_file():
            self.skipTest("prompt {} không có file".format(self.prompt_name))
        tmp = Path(tempfile.mkdtemp(prefix="sentimentx-exp-"))
        try:
            shutil.copyfile(str(source), str(tmp / "prompt.txt"))
            # File ví dụ phải khai TƯỜNG MINH khi prompt đi bằng đường dẫn (xem ExamplesTest).
            examples = prompts.examples_path(self.prompt_name)
            extra = {}
            if examples.is_file():
                shutil.copyfile(str(examples), str(tmp / "examples.txt"))
                extra["examples"] = "examples.txt"
            plan = experiment_run.plan(dict(self.merged, dir=str(tmp)), split="val", limit=2,
                                       prompt="prompt.txt", model_id="model", method="method",
                                       exp_id="exp001", **extra)
            self.assertEqual(plan["prompt"].name, "prompt")
            self.assertEqual(plan["prompt"].path, tmp / "prompt.txt")
            self.assertEqual(len(plan["texts"]), 2)
            self.assertIs(qwen.load_prompt("prompt"), plan["prompt"])
        except (FileNotFoundError, dataset.DatasetError) as exc:
            self.skipTest("chưa có dữ liệu đã xử lý trên máy này: {}".format(exc))
        finally:
            shutil.rmtree(str(tmp), ignore_errors=True)

    def test_plan_bao_loi_khi_prompt_can_vi_du_ma_chua_khai(self):
        source = prompts.prompt_path(self.prompt_name)
        if not source.is_file():
            self.skipTest("prompt {} không có file".format(self.prompt_name))
        if "examples" not in prompts.load(self.prompt_name).placeholders:
            self.skipTest("prompt {} không dùng ô nhớ {{examples}}".format(self.prompt_name))
        tmp = Path(tempfile.mkdtemp(prefix="sentimentx-exp-"))
        try:
            shutil.copyfile(str(source), str(tmp / "prompt.txt"))
            # Prompt cần ví dụ mà config không khai `examples`: phải lỗi NGAY ở bước lập kế hoạch
            # (chưa nạp model) - và tuyệt đối không được lấy file prompt làm file ví dụ.
            with self.assertRaises(prompts.PromptError):
                experiment_run.plan(dict(self.merged, dir=str(tmp)), split="val", limit=2,
                                    prompt="prompt.txt", model_id="model", method="method",
                                    exp_id="exp001")
        finally:
            shutil.rmtree(str(tmp), ignore_errors=True)



class RunIdentityTest(unittest.TestCase):
    """`run_identity` là chỗ DUY NHẤT quyết định thư mục kết quả và dấu vân tay.

    Vì sao khoá: `plan()` (lượt chạy thật) và `preflight` (kiểm trước) từng tính hai kiểu khác nhau.
    preflight báo `NEW - chưa có lần chạy nào trong thư mục này` trong khi lượt chạy cùng lúc báo
    `RESUME - chạy tiếp từ 16 mẫu đã xong`, vì preflight nhìn thư mục PHIÊN BẢN còn lượt chạy nhìn
    thư mục LƯỢT CHẠY. Test này so hai đường với nhau trên đúng cấu hình của exp001.
    """

    MODEL = "qwen3-4b-instruct-2507"
    METHOD = "prompt-cot"
    EXP = "exp001"

    def setUp(self):
        # Cần dữ liệu ĐÃ XỬ LÝ trên máy (bước dựng prompt/dấu vân tay đọc khoá tập đánh giá).
        self.version_id = versioning.compute_id(dataset.load_config("cosmetics"))
        processed = paths.processed(self.version_id) / "test.csv"
        if not processed.is_file():
            raise unittest.SkipTest(
                "chưa có dữ liệu đã xử lý trên máy này: {}".format(processed))

    def pieces(self):
        result = experiments.load(self.MODEL, self.METHOD, self.EXP)
        config = dict(result["config"])
        prompt_obj = experiment_run.run_prompt(config, self.MODEL, self.METHOD, self.EXP)
        ds = dataset.load_config(config["data"]["dataset"])
        return result, config, prompt_obj, versioning.compute_id(ds)

    def identity(self, **overrides):
        result, config, prompt_obj, version_id = self.pieces()
        options = dict(
            model_id=self.MODEL, method=self.METHOD, exp_id=self.EXP,
            generation=experiment_run.run_generation(
                config, experiment_run.effective_quant("auto", config),
                experiment_run.settings_of(config)[1]),
            max_length=experiment_run.effective_max_length(config))
        options.update(overrides)
        found = experiment_run.run_identity(config, version_id, prompt_obj, **options)
        return result, config, prompt_obj, version_id, found

    def test_plan_and_preflight_agree_on_the_folder_and_the_fingerprint(self):
        """Khoá lỗi đã xảy ra: `plan()` và `preflight` phải ra CÙNG thư mục và CÙNG bộ ba."""
        merged = experiments.load(self.MODEL, self.METHOD, self.EXP)
        with mock.patch.dict(os.environ, {"SENTIMENTX_MODEL": ""}):
            # Bắt stdout: `plan()` in cảnh báo "đang chạy trên TEST", và console của Windows không
            # mã hoá được tiếng Việt trong lúc chạy test - lỗi mã hoá đó không phải lỗi của code.
            with redirect_stdout(io.StringIO()):
                plan_data = experiment_run.plan(merged, quiet=True)
            pre_dir, pre_fingerprint = preflight._fingerprint(
                merged, plan_data["version_id"], self.MODEL, self.METHOD, self.EXP)
        self.assertEqual(pre_dir, plan_data["out_dir"])
        self.assertEqual(pre_fingerprint["config_sha256"], plan_data["config_sha256"])
        self.assertEqual(pre_fingerprint["sha"], plan_data["repo"]["sha"])

    def test_folder_name_is_the_identity_hash(self):
        _result, _config, _prompt, _version, found = self.identity()
        self.assertEqual(found["out_dir"].name, found["hash"])
        self.assertEqual(found["hash"], found["config_sha256"][:8])

    def test_another_model_source_keeps_the_same_folder(self):
        """Nguồn trọng số KHÔNG vào mã băm: Colab (id HF) và local (thư mục trên đĩa) phải ra CÙNG tên.

        Đây là điều kiện để copy kết quả từ Drive về repo, và để hai bên không sinh ra hai thư mục
        "trông khác nhau mà thật ra là một".
        """
        _result, _config, _prompt, _version, found = self.identity()
        self.assertNotIn("Qwen3-4B", found["out_dir"].name)
        self.assertEqual(len(found["out_dir"].name), 8)

    def test_quantization_changes_the_hash(self):
        """4-bit và không lượng hoá là hai phép đo khác nhau, nên phải ra hai thư mục khác.

        Lượng hoá nằm trong cấu hình (`inference.quantization`) nên đã vào mã băm; đổi nó là đổi
        cấu hình, đúng như luật "khác cấu hình thì khác thư mục".
        """
        _result, config, _prompt, _version, four = self.identity()
        plain_config = dict(config)
        plain_config["inference"] = dict(config.get("inference") or {})
        plain_config["inference"]["quantization"] = None
        _result2, _config2, _prompt2, _version2, plain = self.identity()
        changed = experiment_run.run_identity(
            plain_config, _version, _prompt2, model_id=self.MODEL, method=self.METHOD,
            exp_id=self.EXP)
        self.assertNotEqual(four["hash"], changed["hash"])
        self.assertNotEqual(four["out_dir"], changed["out_dir"])
        self.assertNotEqual(plain["hash"], changed["hash"])

    def test_changing_the_examples_file_changes_the_fingerprint(self):
        """Đổi bộ ví dụ mà dấu vân tay không đổi thì lượt chạy bị ngắt sẽ RESUME trên bộ ví dụ CŨ."""
        _result, config, prompt_obj, version_id, found = self.identity()
        with mock.patch.object(experiment_run, "side_shas",
                               return_value={"examples": ("x.txt", "khac-sha")}):
            changed = experiment_run.run_identity(
                config, version_id, prompt_obj, model_id=self.MODEL, method=self.METHOD,
                exp_id=self.EXP)
        self.assertNotEqual(changed["config_sha256"], found["config_sha256"])
        self.assertNotEqual(changed["out_dir"], found["out_dir"])


class SystemLabelTest(unittest.TestCase):
    """Nhãn `hệ thống` phải nói ĐÚNG nguồn của khối chỉ dẫn.

    Bản cũ in `không dùng` cả khi model vẫn nhận một khối `[SYSTEM]` nằm trong chính file prompt -
    người đọc log tưởng model không có chỉ dẫn nào, trong khi nó có.
    """

    BODY = "Danh sách khía cạnh: {aspects}\n{label_guide}\nReview:\n{text}"

    def prompt(self, text):
        """Prompt thật sự (không phải dict): nhãn hệ thống đọc từ chính đối tượng đã nạp."""
        return prompts.Prompt("x", paths.root() / "configs/prompts/absa_cot_v1.txt", text)

    def test_a_system_section_inside_the_prompt_file_is_named(self):
        obj = self.prompt("[SYSTEM]\nBạn là trợ lí.\n\n[USER]\n" + self.BODY)
        self.assertEqual(experiment_run.system_label(obj, None),
                         "trong chính file prompt (mục [SYSTEM])")

    def test_a_separate_system_file_is_named_with_its_sha(self):
        obj = self.prompt(self.BODY)
        found = experiment_run.system_label(
            obj, {"file": "configs/prompts/system/absa_v1.txt", "sha": "abc12345"})
        self.assertIn("absa_v1.txt", found)
        self.assertIn("sha abc12345", found)

    def test_no_system_block_says_none(self):
        self.assertEqual(experiment_run.system_label(self.prompt(self.BODY), None), "không dùng")


class MaxLengthTest(unittest.TestCase):
    """Ngưỡng cắt đọc từ đâu: tham số dòng lệnh > config ĐÃ HỢP NHẤT > file cấu hình model.

    Vì sao khoá: bản trước đọc thẳng file cấu hình model, nên khai `preprocess.max_length` trong
    config của thí nghiệm bị BỎ QUA trong im lặng - người viết tưởng đã đổi ngưỡng, còn model vẫn
    nhận input dài như cũ (hoặc bị cắt) mà không có gì báo.
    """

    def test_experiment_layer_can_override_the_model_layer(self):
        self.assertEqual(experiment_run.effective_max_length(
            {"preprocess": {"max_length": 1024}}), 1024)

    def test_the_command_line_wins(self):
        self.assertEqual(experiment_run.effective_max_length(
            {"preprocess": {"max_length": 1024}}, passed=512), 512)

    def test_without_any_override_the_model_config_is_used(self):
        self.assertEqual(experiment_run.effective_max_length({}), qwen.limit()[0])
        self.assertEqual(experiment_run.effective_max_length({"preprocess": {}}), qwen.limit()[0])


if __name__ == "__main__":
    unittest.main()

