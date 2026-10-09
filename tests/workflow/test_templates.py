# -*- coding: utf-8 -*-
"""Test bản mẫu (thư mục templates/).

Vì sao cần: notebook không được biên dịch ở đâu cả, nên một lỗi cú pháp trong đó chỉ lộ ra khi
người nhận bấm Run all - đúng lúc không sửa được nữa (sau khi ghim thì không đụng vào thí nghiệm).
Test ở đây BIÊN DỊCH TỪNG Ô CODE của notebook, và kiểm những thứ mà `scripts/pin.py` dựa vào.

Chạy: python -m unittest discover -s tests
"""

import importlib.util
import json
import unittest

import yaml

from src.workflow import notebooks
from src.core import paths

SPEC = importlib.util.spec_from_file_location("pin", paths.root() / "scripts" / "pin.py")
pin = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pin)

TEMPLATES = paths.root() / "templates"


def notebook():
    with open(TEMPLATES / "experiment" / "notebook.ipynb", encoding="utf-8") as handle:
        return json.load(handle)


class TestFiles(unittest.TestCase):
    def test_every_template_file_exists(self):
        for name in ("templates/README.md", "templates/experiment/README.md",
                     "templates/experiment/config.yaml", "templates/experiment/notebook.ipynb",
                     "templates/prompt/prompt.txt", "templates/prompt/examples.txt",
                     "templates/prompt/system.txt"):
            self.assertTrue((paths.root() / name).is_file(), name)

    def test_config_template_has_the_required_keys(self):
        data = yaml.safe_load((TEMPLATES / "experiment" / "config.yaml").read_text(
            encoding="utf-8"))
        for key in ("exp_id", "model", "method", "data", "prompt"):
            self.assertIn(key, data)
        self.assertIn("dataset", data["data"])
        self.assertIn("version", data["data"])
        self.assertIn("roles", data["data"])
        self.assertIn("eval", data["data"]["roles"])

    def test_prompt_template_has_the_placeholders_the_builder_fills(self):
        text = (TEMPLATES / "prompt" / "prompt.txt").read_text(encoding="utf-8")
        for placeholder in ("{text}", "{aspects}", "{label_guide}"):
            self.assertIn(placeholder, text)
        self.assertIn("[SYSTEM]", text)
        self.assertIn("[USER]", text)

    def test_examples_template_has_a_block_and_the_source_note(self):
        text = (TEMPLATES / "prompt" / "examples.txt").read_text(encoding="utf-8")
        self.assertIn("--- Ví dụ 1 ---", text)
        self.assertIn("KHÔNG lấy từ dữ liệu", text)

    def test_system_template_goes_to_the_model_so_it_has_no_placeholder(self):
        text = (TEMPLATES / "prompt" / "system.txt").read_text(encoding="utf-8").strip()
        self.assertTrue(text)
        self.assertNotIn("{", text)
        self.assertNotIn("]", text.splitlines()[0])


class TestNotebookTemplate(unittest.TestCase):
    def test_it_is_a_valid_nbformat_4_notebook(self):
        data = notebook()
        self.assertEqual(data["nbformat"], 4)
        self.assertTrue(data["cells"])

    def test_code_cells_compile(self):
        """Ô code không được biên dịch ở đâu khác, nên lỗi cú pháp chỉ lộ khi bấm Run all."""
        for index, cell in enumerate(notebook()["cells"]):
            if cell.get("cell_type") != "code":
                continue
            source = cell.get("source") or ""
            if isinstance(source, list):
                source = "".join(source)
            with self.subTest(cell=index):
                compile(source, "<cell {}>".format(index), "exec")

    def test_first_code_cell_is_the_pinned_one(self):
        code_cells = [cell for cell in notebook()["cells"] if cell.get("cell_type") == "code"]
        source = "".join(code_cells[0].get("source") or [])
        self.assertIn(pin.MARKER, source)
        for name in ("REPO_URL", "REPO_BRANCH", "REPO_SHA", "EXP_DIR"):
            self.assertIn("{} = ".format(name), source)

    def test_notebook_calls_the_library_and_the_preflight(self):
        text = json.dumps(notebook(), ensure_ascii=False)
        # Notebook gọi THƯ VIỆN (`src/experiments/experiment_run.py`), KHÔNG gọi script dòng lệnh: hợp đồng
        # giữa notebook đã ghim và thí nghiệm không được là tên cờ dòng lệnh.
        self.assertIn("experiment_run.plan", text)
        self.assertIn("experiment_run.run", text)
        self.assertNotIn("run_qwen_eval", text)
        self.assertIn("preflight.run", text)
        # Việc chuẩn bị môi trường cũng gọi thư viện, không còn nằm trong ô (Batch 5b).
        self.assertIn("from src.api import bootstrap", text)
        self.assertIn("bootstrap.verify_checkout", text)

    def test_the_config_cell_reads_the_dataset_version_the_experiment_declares(self):
        """`data.version` là bản ĐỂ ĐỌC, và ô cấu hình phải hỏi CÙNG một chỗ với preflight/`plan()`.

        Khoá lỗi 09/10/2026: ô cấu hình tự gọi `dataset.load_config(tên)` - hàm đó khi thiếu version
        lấy bản MỚI NHẤT theo tên file - nên một thí nghiệm khai v0.2.0 vừa in sai phiên bản, vừa làm
        preflight DỪNG (nó nhận `ds` của bản mới nhất, lệch với `data.version`).
        """
        text = json.dumps(notebook(), ensure_ascii=False)
        self.assertIn("experiments.dataset_of(config)", text)
        self.assertNotIn("dataset.load_config(dataset_name)", text)

    def test_it_stops_when_the_preflight_finds_problems(self):
        text = json.dumps(notebook(), ensure_ascii=False)
        self.assertIn("SystemExit", text)


class TestBootstrap(unittest.TestCase):
    """Ô bootstrap phải KÉO mã nguồn trước khi `import src`.

    Đây là lỗi thật gặp khi chạy notebook trên Colab lần đầu: `from src import ...` chạy trong khi
    `src/` chưa tồn tại (máy mới chưa có mã nguồn) -> `ModuleNotFoundError: No module named 'src'`.
    Người nhận không tự sửa được vì notebook đã ghim, nên thứ tự này phải bị test chặn.
    """

    def bootstrap_source(self, path):
        """Nguồn ô bootstrap (ô có `def repo_root`) của một notebook."""
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        for cell in data["cells"]:
            if cell.get("cell_type") != "code":
                continue
            source = cell.get("source") or []
            source = source if isinstance(source, str) else "".join(source)
            if "def repo_root" in source:
                return source
        self.fail("{}: không có ô bootstrap".format(path))

    def assert_fetch_first(self, source, label):
        """Trong ô bootstrap: kéo mã nguồn phải chạy TRƯỚC `from src import`, và đúng thứ tự git.

        Bỏ dòng chú thích trước khi tìm, vì lời giải thích có nhắc tới chính những thứ này.
        """
        lines = [line for line in source.splitlines() if not line.lstrip().startswith("#")]

        def first(needle):
            for index, line in enumerate(lines):
                if needle in line:
                    return index
            return None

        clone = first('git("clone"')
        fetch = first('"fetch"')
        checkout = first('"checkout"')
        # Ô bootstrap có thể import qua MẶT TIỀN (`from src.api import ...`) hoặc thẳng vào gói:
        # cả hai đều là "đã import src", nên nhận cả hai dạng.
        imported = next((index for index, line in enumerate(lines)
                         if "from src" in line and "import" in line), None)
        for name, index in (("clone", clone), ("fetch", fetch), ("checkout", checkout),
                            ("import src", imported)):
            self.assertIsNotNone(index, "{}: thiếu bước {}".format(label, name))
        self.assertLess(clone, fetch, "{}: clone trước fetch".format(label))
        self.assertLess(fetch, checkout, "{}: fetch trước checkout".format(label))
        for name, index in (("clone", clone), ("fetch", fetch), ("checkout", checkout)):
            self.assertLess(index, imported,
                            "{}: kéo mã nguồn ({}) phải chạy TRƯỚC `import src`".format(label, name))

    def test_template_fetches_before_importing_src(self):
        source = self.bootstrap_source(TEMPLATES / "experiment" / "notebook.ipynb")
        self.assert_fetch_first(source, "notebook mẫu")
        self.assertIn("--filter=blob:none", source)
        # Phải kéo ĐÚNG COMMIT ĐÃ GHIM, không phải nhánh mặc định: mã nguồn nằm trên nhánh
        # `experiment`, nên `git clone` trần có thể không có `src/` nào cả.
        self.assertIn("--no-checkout", source)
        self.assertIn('"checkout", "--detach", REPO_SHA', source)
        # Sau khi có mã nguồn, việc chuẩn bị (mount Drive, đặt gốc, cài gói, kiểm sha, tài nguyên
        # model) do THƯ VIỆN làm - `repo.prepare` nằm trong `bootstrap.verify_checkout`.
        self.assertIn("from src.api import bootstrap", source)
        self.assertIn("bootstrap.verify_checkout(", source)

    def test_every_experiment_notebook_fetches_before_importing_src(self):
        found = sorted((paths.root() / "experiments").rglob("notebook.ipynb"))
        self.assertTrue(found, "chưa có notebook thí nghiệm nào để kiểm")
        for path in found:
            with self.subTest(notebook=str(path)):
                self.assert_fetch_first(self.bootstrap_source(path), path.name)

    def test_bootstrap_survives_a_second_run(self):
        """Chạy lại notebook trên Colab không được lỗi khi thư mục code đã có sẵn.

        Lỗi thật: `/content/SentimentX` còn lại từ lần chạy trước, nên `git clone` báo
        `destination path ... already exists and is not an empty directory` (mã thoát 128) - một dòng
        lỗi đỏ làm người đọc tưởng notebook hỏng, trong khi chỉ cần bỏ qua bước kéo.
        """
        source = self.bootstrap_source(TEMPLATES / "experiment" / "notebook.ipynb")
        self.assertIn("is_repo_here", source)
        lines = [line for line in source.splitlines() if not line.lstrip().startswith("#")]
        clone = next(index for index, line in enumerate(lines) if 'git("clone"' in line)
        guard = next(index for index, line in enumerate(lines) if "if is_repo_here():" in line)
        self.assertLess(guard, clone,
                        "phải kiểm thư mục đã là repo chưa TRƯỚC khi kéo code mới")
        # Thư mục có sẵn mà KHÔNG phải repo thì phải DỪNG kèm cách sửa, không kéo đè lên dữ liệu lạ.
        self.assertIn("rm -rf", source)

    def test_end_cell_prints_dagshub_only_when_the_run_was_recorded(self):
        """Địa chỉ DagsHub chỉ được in khi `run.log` có dòng `[TRACK]` báo ghi THÀNH CÔNG.

        Ba lượt chạy đầu in địa chỉ DagsHub trong khi `[TRACK]` nói "không ghi nhận gì" - người đọc
        tưởng kết quả đã lên máy chủ.
        """
        text = "\n".join("".join(cell.get("source") or []) for cell in notebook()["cells"]
                         if cell.get("cell_type") == "code")
        self.assertIn("CHƯA ghi nhận lượt này", text)
        self.assertIn('"[TRACK]" in line', text)

    def test_config_cell_does_not_say_ca_split_mau(self):
        """Câu in ra phải đọc được: "cả split mẫu" là lỗi chữ ở bản cũ."""
        for cell in notebook()["cells"]:
            source = ("".join(cell.get("source") or [])
                      if cell.get("cell_type") == "code" else "")
            if "ĐANG DÙNG" in source:
                self.assertNotIn('or "cả split"', source)
                self.assertIn("cả split (n: null)", source)
                return
        self.fail("không thấy ô cấu hình trong notebook mẫu")


    def cell_with(self, needle):
        """Ô CODE chứa `needle` trong notebook MẪU (để kiểm quan hệ thứ tự giữa các dòng)."""
        for cell in notebook()["cells"]:
            if cell.get("cell_type") == "code" and needle in notebooks.source_of(cell):
                return notebooks.source_of(cell)
        self.fail("không thấy ô code nào chứa {!r}".format(needle))

    def test_o_bootstrap_mong_va_goi_thu_vien_theo_dung_thu_tu(self):
        """Ô bootstrap chỉ còn việc KÉO mã nguồn; phần chuẩn bị gọi 4 hàm thư viện, đúng thứ tự cũ.

        Đây là điều khiến việc sửa logic KHÔNG phải sửa 12 notebook: logic ở `src/workflow/bootstrap.py`.
        Thứ tự cũng là hợp đồng: mount Drive/đặt gốc trước, rồi cài gói, rồi kiểm sha (trước khi tải
        27 MB tài nguyên model), và DỪNG ngay sau `prepare` khi thiếu thư mục nhóm.
        """
        source = self.bootstrap_source(TEMPLATES / "experiment" / "notebook.ipynb")
        order = ["bootstrap.prepare()", "bootstrap.install_packages(", "bootstrap.verify_checkout(",
                 "bootstrap.model_assets("]
        positions = [source.index(needle) for needle in order]
        self.assertEqual(positions, sorted(positions), "gọi thư viện SAI thứ tự: {}".format(order))
        stop = source.index('if info["stop"]:')
        self.assertLess(stop, source.index("bootstrap.install_packages("),
                        "phải DỪNG ngay sau `prepare` khi thiếu thư mục nhóm, không chạy tiếp")
        # Ô này KHÔNG được mọc lại logic đã chuyển vào thư viện.
        for moved in ("drive.mount", "find_spec", "urlretrieve", "apt-get", '"pip", "install"'):
            self.assertNotIn(moved, source, "'{}' phải nằm ở src/workflow/bootstrap.py".format(moved))

    def test_o_chay_mang_dau_va_chi_mot_o(self):
        """Ô CHẠY mang DẤU để `run_notebook.py --preflight-only` tìm ra (không dò theo câu chữ)."""
        found = [cell for cell in notebook()["cells"] if cell.get("cell_type") == "code"
                 and notebooks.RUN_MARKER in notebooks.source_of(cell)]
        self.assertEqual(len(found), 1, "phải có ĐÚNG MỘT ô mang dấu ô chạy")
        self.assertIn("experiment_run.run(", notebooks.source_of(found[0]))

    def test_o_kiem_truoc_in_xong_roi_moi_ngat_phien(self):
        """Ô kiểm trước: IN danh sách việc phải sửa -> (khối bảo vệ) NGẮT PHIÊN -> dừng.

        Thứ tự là chịu lực: ngắt phiên làm kernel mất kết nối, nên ngắt trước khi in là giấu mất thứ
        người đọc cần nhất (sửa gì để chạy được). Việc ngắt do `end_session_on_error` làm, và nó chạy
        SAU khi thân ô đã in xong - nên trong ô, `print_report` phải đứng trước lệnh dừng.
        """
        source = self.cell_with("preflight.print_report")
        printed = source.index("preflight.print_report(")
        raised = source.index("raise SystemExit(")
        self.assertLess(printed, raised, "phải IN danh sách việc phải sửa TRƯỚC khi dừng")
        self.assertIn("with end_session_on_error():", source,
                      "ô này phải nằm trong khối bảo vệ để lỗi bất ngờ cũng ngắt được phiên")
        self.assertIn("from src.api import end_session_on_error", source)

    def test_moi_o_co_the_loi_deu_co_khoi_bao_ve(self):
        """LUẬT CỦA BẢN MẪU: ô nào lỗi cũng phải IN XONG rồi mới NGẮT PHIÊN Colab.

        Ô không bọc mà lỗi thì Jupyter dừng ngay tại đó, các ô sau - kể cả ô kết thúc - không chạy, và
        phiên vẫn giữ GPU cho tới khi Colab tự thu hồi. Nên mọi ô CODE có thể lỗi đều phải bọc.

        NGOẠI LỆ CÓ LÝ DO: lời gọi `experiment_run.run(plan)`. Đường lỗi của LƯỢT CHẠY đã do chính thư
        viện ngắt (nhật ký đóng TRƯỚC rồi mới ngắt), nên bọc thêm là ngắt hai lần cho cùng một lượt.
        """
        data = notebook()
        guarded = [index for index, cell in enumerate(data["cells"])
                   if cell.get("cell_type") == "code"
                   and "with end_session_on_error():" in notebooks.source_of(cell)]
        self.assertEqual(guarded, [2, 3, 4, 5, 7],
                         "các ô phải có khối bảo vệ (bootstrap, cấu hình, kiểm trước, chạy, kết thúc): "
                         "{}".format(guarded))

        run_cell = self.cell_with("experiment_run.run(")
        self.assertIn("run_result = experiment_run.run(plan)", run_cell,
                      "lời gọi chạy thật phải ở mức ngoài cùng, KHÔNG nằm trong khối bảo vệ")

    def test_o_ket_thuc_ngat_phien_o_cuoi_cung(self):
        """Ô kết thúc: ngắt phiên là việc CUỐI (sau khi in kết quả và địa chỉ DagsHub)."""
        source = self.cell_with("KẾT THÚC")
        lines = [line.strip() for line in source.splitlines() if line.strip()]
        self.assertEqual(lines[-1], "print(end_session())")
        self.assertIn("from src.api import end_session", source)

    def test_o_ket_thuc_chiu_duoc_khi_chua_co_ket_qua(self):
        """Ô SAU ô CHẠY phải chịu được việc `run_result` CHƯA có (luật đã ghi ở 10_template_notebook).

        Vì sao là lỗi thật: lượt chạy có thể LỖI (hoặc tự dừng ở chế độ STOP) trước khi kịp có
        `run_result`, và khi đó ô cuối đọc `run_result["out_dir"]` ném `NameError: run_result` - một
        lỗi vô nghĩa làm người đọc tưởng notebook hỏng, trong khi lỗi THẬT nằm ở ô trên. Đã gặp thật
        khi chạy smoke đợt 11 (lượt PhoBERT chết vì `SENTIMENTX_MODEL` trỏ nhầm sang Qwen3-4B).
        """
        source = self.cell_with("KẾT THÚC")
        check = 'if "run_result" not in globals():'
        self.assertIn(check, source, "ô kết thúc phải KIỂM `run_result` có hay chưa trước khi đọc")
        self.assertLess(source.index(check), source.index('run_result["out_dir"]'),
                        "phép kiểm phải đứng TRƯỚC chỗ đọc kết quả")
        self.assertIn("else:", source)
        # Nhánh "chưa có kết quả" phải NÓI VIỆC CẦN LÀM, không chỉ im lặng bỏ qua.
        self.assertIn("errors.json", source)


class TestConfigCell(unittest.TestCase):
    """Ô CẤU HÌNH ĐANG DÙNG phải in được cấu hình cho CẢ HAI đường chạy.

    Lỗi thật đã gặp trên Colab: ô này đọc thẳng `config["prompt"]`, nên thí nghiệm model encoder
    (không có prompt) chết ngay ở ô thứ tư - trước cả khi preflight kịp chạy, và trước cả khi in ra
    bản code cùng gốc dữ liệu đang dùng. Ô này chỉ để IN cấu hình, nên nó không được có quyền làm
    chết lượt chạy: mọi khoá phải đọc qua `.get`.
    """

    MARKER = "ĐANG DÙNG"

    def config_cell(self, path):
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        for cell in data["cells"]:
            if cell.get("cell_type") != "code":
                continue
            source = cell.get("source") or []
            source = source if isinstance(source, str) else "".join(source)
            if self.MARKER in source:
                return source
        self.fail("{}: không có ô cấu hình".format(path))

    def every_notebook(self):
        return [TEMPLATES / "experiment" / "notebook.ipynb"] + sorted(
            (paths.root() / "experiments").rglob("notebook.ipynb"))

    def test_every_key_is_read_with_get(self):
        for path in self.every_notebook():
            with self.subTest(notebook=str(path)):
                source = self.config_cell(path)
                self.assertNotIn(
                    'config["', source,
                    "đọc khoá trực tiếp: thiếu khoá là ô này chết. Dùng config.get()")

    def test_it_branches_on_the_run_approach(self):
        for path in self.every_notebook():
            with self.subTest(notebook=str(path)):
                source = self.config_cell(path)
                self.assertIn('approach == "encoder"', source)
                self.assertIn('.get("prompt")', source)
                self.assertIn('config.get("trainer")', source)

    def test_it_compiles_in_every_notebook(self):
        """Ô cấu hình phải BIÊN DỊCH được ở mọi notebook.

        Trước đây test này còn so ô cấu hình với bản mẫu. Bỏ phần so đó ở Batch 5b: bản mẫu là mẫu,
        không phải chuẩn (xem `TestExperimentNotebooks`). Cái còn lại mới là thứ làm hỏng lượt chạy:
        một ô không biên dịch được chỉ lộ ra khi bấm Run all.
        """
        for path in self.every_notebook():
            with self.subTest(notebook=str(path)):
                compile(self.config_cell(path), "<cell-config>", "exec")


class TestExperimentNotebooks(unittest.TestCase):
    """Mỗi notebook thí nghiệm phải nhất quán VỚI CHÍNH NÓ - không so với bản mẫu.

    BẢN MẪU LÀ MẪU, KHÔNG PHẢI CHUẨN (`docs/00_workflow/10_template_notebook.md`): notebook sinh ra
    thuộc về chính thí nghiệm đó, và sửa bản mẫu để phục vụ thí nghiệm mới KHÔNG bắt notebook của
    thí nghiệm đã chạy xong phải cập nhật theo - làm vậy là đổi công thức đứng sau con số đã công bố.

    Ba thứ dưới đây vẫn kiểm, vì chúng làm HỎNG lượt chạy thật: `EXP_DIR` trỏ sai thí nghiệm (kết quả
    ghi vào thư mục của thí nghiệm khác), thiếu ô GHIM (không biết đang chạy bản code nào), và ô code
    không biên dịch được (chỉ lộ ra khi bấm Run all).
    """

    def every_experiment_notebook(self):
        found = sorted((paths.root() / "experiments").rglob("notebook.ipynb"))
        self.assertTrue(found, "chưa có notebook thí nghiệm nào để kiểm")
        return found

    def read(self, path):
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)

    def test_moi_notebook_co_dung_mot_o_chay_mang_dau(self):
        """ĐÚNG MỘT ô mang `RUN_MARKER`, và nó là ô gọi thí nghiệm.

        `scripts/run_notebook.py --preflight-only` tìm ô cần dừng bằng dấu này: hai ô mang dấu thì nó
        dừng quá sớm (chạy thiếu), không ô nào mang dấu là nó dừng NGAY (không chạy gì) - và cả hai
        đều là lỗi im lặng nếu không có phép kiểm này.
        """
        for path in self.every_experiment_notebook():
            with self.subTest(notebook=path.parent.name):
                data = self.read(path)
                found = [cell for cell in data["cells"]
                         if cell.get("cell_type") == "code"
                         and notebooks.RUN_MARKER in notebooks.source_of(cell)]
                self.assertEqual(len(found), 1,
                                 "phải có ĐÚNG MỘT ô mang dấu ô chạy trong {}".format(path))
                self.assertIn("experiment_run.run(", notebooks.source_of(found[0]))

    def test_moi_notebook_ghim_dung_thi_nghiem_cua_no(self):
        for path in self.every_experiment_notebook():
            experiment = path.parent.relative_to(paths.root() / "experiments").as_posix()
            with self.subTest(notebook=experiment):
                source = notebooks.source_of(notebooks.pinned_cell(self.read(path), required=True))
                self.assertIn(notebooks.EXP_DIR_PREFIX + "'{}'".format(experiment), source)

    def test_o_ghim_la_o_code_dau_tien(self):
        for path in self.every_experiment_notebook():
            with self.subTest(notebook=str(path)):
                cells = [cell for cell in self.read(path)["cells"]
                         if cell.get("cell_type") == "code"]
                self.assertTrue(cells, "{}: không có ô code nào".format(path))
                self.assertIn(notebooks.MARKER, notebooks.source_of(cells[0]))

    def test_moi_o_code_bien_dich_duoc(self):
        for path in self.every_experiment_notebook():
            for index, cell in enumerate(self.read(path)["cells"]):
                if cell.get("cell_type") != "code":
                    continue
                with self.subTest(notebook=str(path), cell=index):
                    compile(notebooks.source_of(cell), "<cell {}>".format(index), "exec")


if __name__ == "__main__":
    unittest.main()
