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

from src import paths

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
        # Notebook gọi THƯ VIỆN (`src/experiment_run.py`), KHÔNG gọi script dòng lệnh: hợp đồng
        # giữa notebook đã ghim và thí nghiệm không được là tên cờ dòng lệnh.
        self.assertIn("experiment_run.plan", text)
        self.assertIn("experiment_run.run", text)
        self.assertNotIn("run_qwen_eval", text)
        self.assertIn("preflight.run", text)
        self.assertIn("repo.prepare", text)
        self.assertIn("runtime.load_env", text)

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
        imported = first("from src import")
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
        self.assertIn("repo.prepare", source)

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

    def test_bootstrap_does_the_whole_colab_setup_itself(self):
        """Ô bootstrap tự mount Drive, tự đặt gốc, tự cài gói thiếu - người chạy chỉ bấm Run all.

        Đây là yêu cầu của thiết kế bàn giao: "copy thư mục vào Drive rồi bấm Run all". Mỗi bước bị
        chuyển ra thành thao tác tay là một bước sẽ bị bỏ qua hoặc làm sai thứ tự, nên chúng bị khoá ở đây.
        """
        source = self.bootstrap_source(TEMPLATES / "experiment" / "notebook.ipynb")
        self.assertIn("drive.mount", source)
        self.assertIn("SENTIMENTX_DATA_ROOT", source)
        self.assertIn("SENTIMENTX_RESULTS_ROOT", source)
        self.assertIn("find_spec", source)
        lines = [line for line in source.splitlines() if not line.lstrip().startswith("#")]
        mount = next(index for index, line in enumerate(lines) if "drive.mount" in line)
        lookup = next(index for index, line in enumerate(lines)
                      if "runtime.drive_dir()" in line)
        self.assertLess(mount, lookup, "mount Drive phải chạy TRƯỚC khi tìm thư mục nhóm")
        # Cài đặt chỉ trên Colab, và phải là `pip install`, không phải lệnh nào khác.
        self.assertIn("IN_COLAB", source)
        self.assertIn('"-m", "pip", "install"', source)

    def test_bootstrap_downloads_the_tokenizer_assets_when_missing(self):
        """Ô bootstrap phải TỰ có model VnCoreNLP, không bắt người chạy chép tay.

        Lỗi thật trên Colab: preflight dừng vì thiếu `data/models/vncorenlp`, trong khi gói bàn giao
        đã có thư mục đó - người chạy chép thiếu một thư mục là cả lượt chạy không bắt đầu được.
        Nay ô bootstrap tự tải ba file cần thiết vào GỐC DỮ LIỆU khi thiếu, cùng nguồn và cùng mức
        kích thước tối thiểu như `scripts/setup_vncorenlp.ps1`.
        """
        source = self.bootstrap_source(TEMPLATES / "experiment" / "notebook.ipynb")
        self.assertIn("urlretrieve", source)
        self.assertIn("VnCoreNLP-1.2.jar", source)
        self.assertIn("models/wordsegmenter/vi-vocab", source)
        self.assertIn("models/wordsegmenter/wordsegmenter.rdr", source)
        # Tải về chỗ mà preflight và bộ tách từ cùng đọc: gốc dữ liệu, không phải thư mục khác.
        self.assertIn('paths.data("models")', source)

    def test_bootstrap_stops_when_the_group_folder_is_missing(self):
        """Colab không thấy thư mục nhóm là DỪNG, không chạy tiếp rồi chết ở ô cấu hình.

        Máy ảo Colab không chứa dữ liệu gốc, nên chạy tiếp chỉ tạo ra thêm hai thông báo khó hiểu
        (thiếu dữ liệu, kết quả ghi vào chỗ mất khi hết phiên). Lượt chạy thật đã rơi vào đúng cảnh
        đó. Việc dừng phải nằm SAU bước tìm thư mục nhóm, và phải nhường chỗ cho trường hợp người
        chạy cố ý khai `SENTIMENTX_DATA_ROOT`.
        """
        source = self.bootstrap_source(TEMPLATES / "experiment" / "notebook.ipynb")
        self.assertIn("chưa thấy thư mục nhóm trên Drive", source)
        self.assertIn('os.environ.get("SENTIMENTX_DATA_ROOT"', source)
        lines = [line for line in source.splitlines() if not line.lstrip().startswith("#")]
        lookup = next(index for index, line in enumerate(lines) if "runtime.drive_dir()" in line)
        stop = next(index for index, line in enumerate(lines)
                    if "chưa thấy thư mục nhóm trên Drive" in line)
        self.assertLess(lookup, stop, "phải tìm thư mục nhóm TRƯỚC khi kết luận là không có")

    def test_bootstrap_waits_before_giving_up_on_drive(self):
        """Drive vừa mount thì danh sách thư mục có thể chưa đủ: phải chờ rồi thử lại.

        Lỗi thật: cùng một phiên Colab, notebook này thấy thư mục nhóm còn notebook kia thì không -
        lượt chạy sau đó rơi vào máy ảo và báo thiếu dữ liệu gốc.
        """
        source = self.bootstrap_source(TEMPLATES / "experiment" / "notebook.ipynb")
        self.assertIn("attempts=10, delay=3", source)

    def test_bootstrap_removes_a_torchao_that_breaks_peft(self):
        """`peft` ném ImportError khi máy có torchao cũ, nên ô bootstrap phải gỡ nó.

        Lỗi thật trên Colab: torchao 0.10.0 so với ngưỡng 0.16.0 của peft, và lượt chạy LoRA chết sau
        khi đã nạp xong model. Hỏi thẳng `peft.import_utils` thay vì tự so phiên bản trong notebook.
        """
        source = self.bootstrap_source(TEMPLATES / "experiment" / "notebook.ipynb")
        self.assertIn("from peft.import_utils import is_torchao_available", source)
        self.assertIn('"uninstall", "-y", "-q", "torchao"', source)
        self.assertIn('sys.modules.pop("torchao", None)', source)

    def test_bootstrap_shows_what_it_sees_when_the_drive_lookup_fails(self):
        """Không thấy thư mục nhóm thì phải in DANH SÁCH thư mục đang thấy, và vẫn nhận ra thư mục gói.

        Hai việc này đi cùng nhau: dòng danh sách là bằng chứng để người đọc biết máy đang nhìn vào đâu,
        còn `looks_like_group_dir` cứu trường hợp file đánh dấu bị MẤT khi chép thư mục - file bắt đầu
        bằng dấu chấm nên `Compress-Archive` (và đôi khi cả Explorer) bỏ qua nó.
        """
        source = self.bootstrap_source(TEMPLATES / "experiment" / "notebook.ipynb")
        self.assertIn("runtime.drive_children()", source)
        self.assertIn("runtime.looks_like_group_dir", source)
        self.assertIn("THIẾU file đánh dấu .sentimentx_root", source)

    def test_bootstrap_lists_each_drive_root_separately(self):
        """MyDrive và Shareddrives là hai gốc khác nhau: phải in từng gốc khi không thấy thư mục nhóm.

        Thư mục nhóm của nhóm/giảng viên có thể nằm trong SHARED DRIVE, nên câu hỏi "gốc nào có gì"
        phải trả lời được ngay từ dòng notebook in ra - nếu gộp chung thì không biết `Shareddrives`
        rỗng hay tài khoản chưa được chia sẻ.
        """
        source = self.bootstrap_source(TEMPLATES / "experiment" / "notebook.ipynb")
        self.assertIn("runtime.drive_listing()", source)
        self.assertIn("SHARED DRIVE", source)
        self.assertIn("Shareddrives", source)

    def test_bootstrap_says_which_account_to_pick_when_the_drive_has_nothing(self):
        """Thấy toàn thư mục lạ thì phải nói tới chuyện chọn nhầm TÀI KHOẢN Google.

        Lỗi thật: một phiên Colab mount Drive của tài khoản khác, nên chỉ thấy `Colab Notebooks`,
        `artifacts_backup3`... và notebook kết luận "chưa thấy thư mục nhóm". Nguyên nhân nằm ở lần
        Colab hỏi chọn tài khoản khi mount, mà điều đó chỉ người chạy sửa được.
        """
        source = self.bootstrap_source(TEMPLATES / "experiment" / "notebook.ipynb")
        self.assertIn("MỘT TÀI KHOẢN GOOGLE KHÁC", source)
        self.assertIn("Disconnect and delete runtime", source)

    def test_bootstrap_explains_the_shared_folder_case(self):
        """A chia sẻ thư mục cho b/c/d: notebook phải nói bước "Add shortcut to My Drive".

        Được chia sẻ thôi thì Drive của người nhận vẫn KHÔNG chứa thư mục đó ("Shared with me" không
        nằm trong `MyDrive`), nên nếu notebook không nói bước này thì lượt chạy dừng mà không ai biết
        phải làm gì. Kèm theo là lối tắt được in ra và hai khoá env để chỉ định thẳng đường dẫn.
        """
        source = self.bootstrap_source(TEMPLATES / "experiment" / "notebook.ipynb")
        self.assertIn("Add shortcut to My Drive", source)
        self.assertIn("lối tắt (shortcut) đang trỏ tới", source)
        self.assertIn("SENTIMENTX_RESULTS_ROOT", source)

    def test_bootstrap_is_the_same_in_every_notebook(self):
        """Ô bootstrap của notebook thí nghiệm phải GIỐNG HỆT bản mẫu, từng ký tự.

        Sửa cách kéo code ở bản mẫu mà quên notebook đã giao là notebook đó mãi mãi chạy phiên bản
        cũ - mà nó đã được ghim, người nhận không tự sửa được. So từng ký tự để việc quên đó lộ ra
        ngay tại đây, kèm đúng đường dẫn cần chép lại.
        """
        template = self.bootstrap_source(TEMPLATES / "experiment" / "notebook.ipynb")
        found = sorted((paths.root() / "experiments").rglob("notebook.ipynb"))
        self.assertTrue(found, "chưa có notebook thí nghiệm nào để so")
        for path in found:
            with self.subTest(notebook=str(path)):
                self.assertEqual(
                    self.bootstrap_source(path), template,
                    "{}: ô bootstrap khác bản mẫu - chép lại từ {}".format(
                        path, TEMPLATES / "experiment" / "notebook.ipynb"))


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

    def test_it_compiles_and_matches_the_template(self):
        template = self.config_cell(TEMPLATES / "experiment" / "notebook.ipynb")
        compile(template, "<cell-config>", "exec")
        for path in self.every_notebook():
            with self.subTest(notebook=str(path)):
                self.assertEqual(
                    self.config_cell(path), template,
                    "{}: ô cấu hình khác bản mẫu - chép lại từ {}".format(
                        path, TEMPLATES / "experiment" / "notebook.ipynb"))


if __name__ == "__main__":
    unittest.main()
