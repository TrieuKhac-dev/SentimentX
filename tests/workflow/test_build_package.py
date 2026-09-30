# -*- coding: utf-8 -*-
"""Test `scripts/build_package.py`: gói bàn giao tăng dần và SỔ biết đã gửi file nào.

VÌ SAO KHOÁ NHỮNG CA NÀY
Gói bàn giao là thứ người khác chạy. Hai lỗi đắt nhất không phải là zip hỏng, mà là:
    - gửi THIẾU một file (người nhận chết ở giữa lượt chạy, sau khi đã tải model), và
    - đổi nội dung một phiên bản dữ liệu ĐÃ GỬI (kết quả họ báo cáo không còn so được, mà không ai
      biết vì sao).
Nên các test dưới đây kiểm: ứng viên có được suy ĐỦ từ cấu hình thí nghiệm không, bốn lớp có đúng
không, người nhận có được bảo phải xoá gì không, và cảnh báo đỏ có thật sự CHẶN việc dựng gói không.

HAI CÁCH KIỂM
`collect` (dò ứng viên) kiểm bằng cây thư mục giả + điểm tiêm, vì nó hỏi cấu hình thí nghiệm và gốc
dữ liệu. Còn luồng gói (bốn lớp, sổ, zip, mã thoát) kiểm qua `main` với một bộ ứng viên dựng sẵn -
nhờ vậy không phải dựng cả một repo giả để kiểm một cái zip.

Chạy: python -m unittest discover -s tests
"""

import csv
import importlib.util
import io
import os
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from src.core import paths

SPEC = importlib.util.spec_from_file_location(
    "build_package", paths.root() / "scripts" / "build_package.py")
build_package = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_package)

VERSION = "cosmetics-ds0.1.0-pl0.1.0-srccosmetics@0.1.0-e0ccc484"
EXP = ("m1", "meth", "exp001")


class HandoverCase(unittest.TestCase):
    """Cây giả có đúng những thứ `collect` hỏi tới."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.data_root = self.root / "data"
        self.handover = self.root / "handover"
        # `collect` dò dữ liệu qua `paths.data_root()`, mà hàm đó đọc biến môi trường. Đặt biến vào
        # cây giả thay vì để nó trỏ vào dữ liệu thật của repo.
        patcher = mock.patch.dict(os.environ, {"SENTIMENTX_DATA_ROOT": str(self.data_root)})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self._tmp.cleanup)
        self.counter = 0
        self.write("handover/README.md", "# hướng dẫn cho người nhận")
        self.write(".env.colab.example", "DAGSHUB_TOKEN=\n")

    def write(self, relative, text=None):
        """Ghi một file. Không truyền `text` thì mỗi lần gọi ra một nội dung KHÁC (để kiểm 'đã đổi')."""
        self.counter += 1
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text if text is not None else "noi dung {}\n".format(self.counter),
                        encoding="utf-8")
        return path

    def remove(self, relative):
        (self.root / relative).unlink()

    def experiment_files(self, exp=EXP):
        model, method, exp_id = exp
        self.write("experiments/{}/{}/{}/notebook.ipynb".format(model, method, exp_id), "{}")
        self.write("experiments/{}/{}/{}/README.md".format(model, method, exp_id), "thí nghiệm")

    def data_files(self):
        """Dữ liệu của một phiên bản, cộng dữ liệu gốc: đúng những gì gói phải mang."""
        base = "data/processed/" + VERSION
        for name in ("test.csv", "label_map.json", "processing_log.json", "eval_lock.json"):
            self.write("{}/{}".format(base, name), "du lieu {}\n".format(name))
        for name in ("data_train.csv", "data_val.csv", "data_test.csv", "full_data.csv"):
            self.write("data/raw/cosmetics/v0.1.0/{}".format(name), "goc {}\n".format(name))
        self.write("data/raw/cosmetics/v0.1.0/raw_meta.yaml", "nguon goc\n")

    # --- điểm tiêm cho `collect` ---

    def list_experiments(self, items=(EXP,)):
        return lambda model_id=None, method=None: list(items)

    def fake_load(self, extra=None):
        def load(model_id, method, exp_id):
            config = {"data": {"dataset": "cosmetics", "version": "v0.1.0",
                               "roles": {"eval": "test"}}}
            if extra:
                config["requires_extra"] = list(extra)
            return {"config": config}
        return load

    def fake_dataset(self):
        raw = str(self.data_root / "raw" / "cosmetics" / "v0.1.0")
        return lambda name=None, version=None: {
            "splits": {"train": "data_train.csv", "val": "data_val.csv", "test": "data_test.csv"},
            "full": "full_data.csv",
            "sources": [{"kind": "raw", "name": "cosmetics", "raw_version": "v0.1.0"}],
            "_raw_dir": raw}

    def collect(self, **options):
        prepared = {"root": self.root, "data_root": self.data_root,
                    "readme": self.handover / "README.md",
                    "list_experiments": self.list_experiments(), "load": self.fake_load(),
                    "load_dataset": self.fake_dataset(), "log": lambda line: None}
        prepared.update(options)
        return build_package.collect(**prepared)

    def paths_of(self, entries):
        return {item["package_path"] for item in entries}

class CandidateTest(HandoverCase):
    """Ứng viên suy từ cấu hình thí nghiệm: phải ĐỦ, và đúng đường dẫn trong gói."""

    def test_moi_thu_nguoi_nhan_can_deu_vao_goi(self):
        self.experiment_files()
        self.data_files()
        found = self.paths_of(self.collect())
        for expected in ("notebooks/m1/meth/exp001.ipynb",
                         "experiments/m1/meth/exp001/README.md",
                         "data/processed/{}/test.csv".format(VERSION),
                         "data/processed/{}/label_map.json".format(VERSION),
                         # Hai file SỔ của phiên bản: `requires` không kể, nhưng máy người nhận
                         # đọc chúng để kiểm dữ liệu - gói cũ có cả hai.
                         "data/processed/{}/processing_log.json".format(VERSION),
                         "data/processed/{}/eval_lock.json".format(VERSION),
                         "data/raw/cosmetics/v0.1.0/data_train.csv",
                         "data/raw/cosmetics/v0.1.0/raw_meta.yaml",
                         "env/.env.colab.example",
                         build_package.MARKER_NAME):
            with self.subTest(package_path=expected):
                self.assertIn(expected, found)

    def test_notebook_doi_ten_trong_goi_va_van_ghi_nguon(self):
        """Trong gói là `notebooks/<model>/<method>/<exp>.ipynb`; nguồn ở `experiments/...`."""
        self.experiment_files()
        self.data_files()
        item = [row for row in self.collect()
                if row["package_path"] == "notebooks/m1/meth/exp001.ipynb"][0]
        # Cây giả nằm ngoài repo, mà `source` chỉ rút gọn được khi file nằm TRONG repo: ở đây nó là
        # đường dẫn tuyệt đối. Phần khoá lại là quan hệ giữa hai đường dẫn.
        self.assertTrue(item["source"].endswith(
            os.path.join("experiments", "m1", "meth", "exp001", "notebook.ipynb")), item["source"])
        self.assertTrue(Path(item["source"]).is_file())

    def test_thu_muc_khai_trong_requires_extra_duoc_gui_ca_cay(self):
        """`data/models/vncorenlp` là THƯ MỤC: gửi cả cây con, giữ nguyên cấu trúc."""
        self.experiment_files()
        self.data_files()
        self.write("data/models/vncorenlp/VnCoreNLP-1.2.jar", "jar")
        self.write("data/models/vncorenlp/models/wordsegmenter/vi-vocab", "vocab")
        found = self.paths_of(self.collect(
            load=self.fake_load(extra=["data/models/vncorenlp"])))
        self.assertIn("data/models/vncorenlp/VnCoreNLP-1.2.jar", found)
        self.assertIn("data/models/vncorenlp/models/wordsegmenter/vi-vocab", found)

    def test_file_trong_git_khong_vao_goi(self):
        """Prompt và cấu hình nằm trong git (notebook kéo về theo commit đã ghim), nên không gửi."""
        self.experiment_files()
        self.data_files()
        found = self.paths_of(self.collect(
            load=self.fake_load(extra=["configs/prompts/absa_cot_v1.txt"])))
        self.assertEqual([path for path in found if "configs/" in path], [])

    def test_thieu_notebook_thi_bao_loi_chu_khong_dung_goi_thieu(self):
        """Gói thiếu file mà người nhận cần là gói hỏng: phải dừng lúc DỰNG, không phải lúc họ chạy."""
        self.experiment_files()
        self.data_files()
        self.remove("experiments/m1/meth/exp001/notebook.ipynb")
        with self.assertRaises(build_package.PackageError) as caught:
            self.collect()
        self.assertIn("notebook.ipynb", str(caught.exception))

    def test_ung_vien_chi_gom_thu_git_khong_cho_duoc(self):
        """Không file nào của `src/`, `configs/`, `docs/` vào gói - và do đó cũng không được BĂM.

        Gói chỉ chở thứ git không chở được; mã nguồn và cấu hình đến từ commit đã ghim. Đây cũng là
        điều kiện để công cụ chạy nhanh: nó băm vài chục ứng viên, không băm cả repo.
        """
        self.experiment_files()
        self.data_files()
        entries = self.collect(load=self.fake_load(extra=["configs/prompts/absa_cot_v1.txt"]))
        sources = [item["source"].replace("\\", "/") for item in entries]
        self.assertEqual([s for s in sources
                          if "/src/" in s or "/configs/" in s or "/docs/" in s], [],
                         "chỉ gửi thứ git không chở được")
        groups = sorted({item["group"] for item in entries})
        self.assertEqual(groups, ["data", "data_raw", "env", "experiment_readme", "marker",
                                  "notebook", "package_readme"])

    def test_thi_nghiem_chua_co_dataset_thi_bo_qua_kem_ly_do(self):
        """Chưa chạy pipeline thì không có dữ liệu để gửi: bỏ qua kèm lý do, không nổ."""
        self.experiment_files()
        lines = []
        entries = self.collect(log=lines.append)
        self.assertIn("notebooks/m1/meth/exp001.ipynb", self.paths_of(entries))
        self.assertEqual([path for path in self.paths_of(entries) if path.startswith("data/")], [])
        self.assertTrue(any("chưa có dataset đã xử lý" in line for line in lines),
                        "phải nói rõ vì sao không có dữ liệu nào: {}".format(lines))


class Recorder:
    """Thay cho `print`: ghi lại từng câu để so câu chữ mà người gửi đọc."""

    def __init__(self):
        self.lines = []

    def __call__(self, message):
        self.lines.append(str(message))

    def text(self):
        return "\n".join(self.lines)


class FlowCase(HandoverCase):
    """Luồng gói: bốn lớp, sổ, zip, mã thoát - chạy qua `main` với ứng viên dựng sẵn."""

    def candidates(self, package_paths):
        entries = [build_package.entry(path, self.root / path, "test") for path in package_paths]
        entries.append(build_package.marker_entry())
        return entries

    def build(self, entries, argv=()):
        """Chạy `main` như người dùng chạy, trả (mã thoát, câu in ra)."""
        recorder = Recorder()
        argv = list(argv) + ["--root", str(self.root), "--data-root", str(self.data_root),
                             "--handover", str(self.handover), "--out", str(self.handover / "out")]
        code = build_package.main(argv, log=recorder, collector=lambda **kwargs: entries)
        return code, recorder

    def manifest(self, number=1):
        path = self.handover / "packages" / "{:03d}".format(number) / "manifest.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            return {row["package_path"]: row for row in csv.DictReader(handle)}

    def ledger(self):
        with (self.handover / "ledger.csv").open(encoding="utf-8", newline="") as handle:
            return {row["package_path"]: row for row in csv.DictReader(handle)}

    def zip_names(self, number=1):
        found = sorted((self.handover / "out").glob("*{:03d}*.zip".format(number)))
        self.assertEqual(len(found), 1, "phải có đúng một gói zip mang số {}".format(number))
        with zipfile.ZipFile(str(found[0])) as archive:
            return sorted(archive.namelist())


class FirstPackageTest(FlowCase):
    """Gói đầu tiên: chưa có sổ, nên mọi thứ là `new` và gói phải đầy đủ."""

    def test_lan_dau_moi_file_deu_la_new_va_co_trong_zip(self):
        self.write("env/.env.colab", "TOKEN=x")
        self.write("data/processed/x/test.csv", "du lieu")
        entries = self.candidates(["env/.env.colab", "data/processed/x/test.csv"])
        code, out = self.build(entries)
        self.assertEqual(code, 0)
        rows = self.manifest()
        self.assertEqual({row["class"] for row in rows.values()}, {"new"})
        self.assertEqual(rows["env/.env.colab"]["sent_package"], "")
        self.assertEqual(self.zip_names(),
                         [".sentimentx_root", "MANIFEST.csv", "data/processed/x/test.csv",
                          "env/.env.colab"])
        self.assertIn("gói 001", out.text())

    def test_zip_khong_vao_git_con_so_thi_vao(self):
        """Gói zip nằm ở `handover/out/` (.gitignore chặn); sổ thì phải theo dõi."""
        self.write("a.txt")
        self.build(self.candidates(["a.txt"]))
        gitignore = (paths.root() / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("handover/out/", gitignore)
        self.assertTrue((self.handover / "ledger.csv").is_file())
        self.assertTrue((self.handover / "files.csv").is_file())

    def test_manifest_di_kem_trong_zip_cho_nguoi_nhan(self):
        self.write("a.txt")
        self.build(self.candidates(["a.txt"]))
        with zipfile.ZipFile(str(sorted((self.handover / "out").glob("*.zip"))[0])) as archive:
            text = archive.read("MANIFEST.csv").decode("utf-8")
        self.assertIn("package_path", text)
        self.assertIn("a.txt", text)

    def test_dry_run_khong_ghi_gi(self):
        self.write("a.txt")
        code, out = self.build(self.candidates(["a.txt"]), argv=["--dry-run"])
        self.assertEqual(code, 0)
        self.assertFalse((self.handover / "ledger.csv").exists())
        self.assertFalse((self.handover / "packages").exists())
        self.assertEqual(list((self.handover / "out").glob("*.zip")), [])
        self.assertIn("--dry-run", out.text())


class DeltaTest(FlowCase):
    """Từ gói thứ hai: chỉ gửi cái mới hoặc đã đổi, và nói rõ cái gì phải xoá."""

    def first_package(self):
        self.write("a.txt", "noi dung goc")
        self.write("b.txt", "noi dung goc")
        self.write("data/processed/x/test.csv", "du lieu goc")
        entries = self.candidates(["a.txt", "b.txt", "data/processed/x/test.csv"])
        self.assertEqual(self.build(entries)[0], 0)
        return entries

    def test_file_khong_doi_thi_khong_gui_lai(self):
        self.first_package()
        code, out = self.build(self.candidates(["a.txt", "b.txt", "data/processed/x/test.csv"]))
        self.assertEqual(code, 0)
        self.assertIn("Không có gì mới để gửi", out.text())
        self.assertFalse((self.handover / "packages" / "002").exists())

    def test_file_doi_thi_thanh_changed_va_chi_file_do_vao_zip(self):
        self.first_package()
        self.write("b.txt", "noi dung KHAC")
        code, _ = self.build(self.candidates(["a.txt", "b.txt", "data/processed/x/test.csv"]))
        self.assertEqual(code, 0)
        rows = self.manifest(number=2)
        self.assertEqual(rows["b.txt"]["class"], "changed")
        self.assertEqual(rows["b.txt"]["sent_package"], "001")
        self.assertEqual(rows["a.txt"]["class"], "kept")
        self.assertEqual(rows["data/processed/x/test.csv"]["class"], "kept")
        self.assertEqual(self.zip_names(2), ["MANIFEST.csv", "b.txt"])
        self.assertEqual(self.ledger()["b.txt"]["last_package"], "002")
        self.assertEqual(self.ledger()["b.txt"]["first_package"], "001")

    def test_file_bien_mat_thi_vao_manifest_de_nguoi_nhan_xoa(self):
        self.first_package()
        self.remove("b.txt")
        code, out = self.build(self.candidates(["a.txt", "data/processed/x/test.csv"]))
        self.assertEqual(code, 0)
        rows = self.manifest(number=2)
        self.assertEqual(rows["b.txt"]["class"], "deleted")
        self.assertEqual(rows["b.txt"]["sent_package"], "001")
        self.assertNotIn("b.txt", self.zip_names(2))
        self.assertIn("NGƯỜI NHẬN CẦN XOÁ 1 mục", out.text())
        # File đã xoá được BỎ khỏi sổ: nếu nó quay lại thì phải gửi như file MỚI (người nhận đã xoá).
        self.assertNotIn("b.txt", self.ledger())


class RedFlagTest(FlowCase):
    """Cảnh báo đỏ: đổi nội dung trong một phiên bản dữ liệu ĐÃ GỬI."""

    def first_package(self):
        self.write("data/processed/x/test.csv", "du lieu goc")
        self.write("env/.env.colab.example", "mau goc")
        entries = self.candidates(["data/processed/x/test.csv", "env/.env.colab.example"])
        self.assertEqual(self.build(entries)[0], 0)
        return entries

    def test_doi_du_lieu_da_gui_thi_dung_lai_va_tra_ve_3(self):
        self.first_package()
        self.write("data/processed/x/test.csv", "du lieu KHAC")
        code, out = self.build(self.candidates(
            ["data/processed/x/test.csv", "env/.env.colab.example"]))
        self.assertEqual(code, 3)
        self.assertIn("CẢNH BÁO ĐỎ", out.text())
        self.assertIn("tạo phiên bản dữ liệu MỚI", out.text())
        self.assertFalse((self.handover / "packages" / "002").exists())
        self.assertNotEqual("002", self.ledger()["data/processed/x/test.csv"]["last_package"])

    def test_xoa_du_lieu_da_gui_cung_la_canh_bao_do(self):
        self.first_package()
        self.remove("data/processed/x/test.csv")
        code, out = self.build(self.candidates(["env/.env.colab.example"]))
        self.assertEqual(code, 3)
        self.assertIn("KHÔNG CÒN trong cây", out.text())

    def test_doi_file_ngoai_du_lieu_thi_khong_canh_bao_do(self):
        """Tệp env đổi là chuyện bình thường: người nhận giải nén đè, không đụng tới dữ liệu."""
        self.first_package()
        self.write("env/.env.colab.example", "mau MOI")
        code, out = self.build(self.candidates(
            ["data/processed/x/test.csv", "env/.env.colab.example"]))
        self.assertEqual(code, 0)
        self.assertNotIn("CẢNH BÁO ĐỎ", out.text())

    def test_allow_red_thi_van_dung_va_ghi_chu_vao_manifest(self):
        self.first_package()
        self.write("data/processed/x/test.csv", "du lieu KHAC")
        code, out = self.build(self.candidates(
            ["data/processed/x/test.csv", "env/.env.colab.example"]), argv=["--allow-red"])
        self.assertEqual(code, 0)
        self.assertIn("CẢNH BÁO ĐỎ", out.text())
        self.assertIn("CẢNH BÁO ĐỎ", self.manifest(number=2)["data/processed/x/test.csv"]["note"])


class NumberTest(FlowCase):
    """Số gói: tự tăng, và số đã dùng thì không ghi đè."""

    def test_goi_dau_khong_phu_thuoc_goi_nao_va_goi_sau_phu_thuoc_goi_truoc(self):
        """`depends_on` là điều kiện để gói tăng dần áp đúng thứ tự: gói sau giả định đã có gói trước."""
        self.write("a.txt", "goc")
        self.build(self.candidates(["a.txt"]))
        self.assertEqual(self.manifest(number=1)["a.txt"]["depends_on"], "")
        self.write("a.txt", "moi")
        self.build(self.candidates(["a.txt"]))
        rows = self.manifest(number=2)
        self.assertEqual(rows["a.txt"]["depends_on"], "001")
        self.assertEqual(rows["a.txt"]["sent_package"], "001",
                         "manifest ghi gói ĐÃ GỬI bản trước, để tra ngược")
        entry = self.ledger()["a.txt"]
        self.assertEqual((entry["first_package"], entry["last_package"]), ("001", "002"),
                         "vào tay người nhận từ gói 001, bản mới nhất ở gói 002")
        self.assertTrue(entry["mtime"], "mtime là dấu hiệu phụ để tra khi băm không đổi")

    def test_so_ke_tiep_va_tu_choi_so_da_dung(self):
        self.write("a.txt")
        self.assertEqual(self.build(self.candidates(["a.txt"]))[0], 0)
        self.write("b.txt")
        self.assertEqual(self.build(self.candidates(["a.txt", "b.txt"]))[0], 0)
        self.assertTrue((self.handover / "packages" / "002").is_dir())
        code, out = self.build(self.candidates(["a.txt", "b.txt"]), argv=["--number", "001"])
        self.assertEqual(code, 2)
        self.assertIn("đã có", out.text())

    def test_so_gui_thi_phai_la_so(self):
        code, out = self.build(self.candidates([]), argv=["--number", "abc"])
        self.assertEqual(code, 2)
        self.assertIn("Số gói phải là số", out.text())

    def test_so_hong_thi_bao_loi_chu_khong_doan(self):
        self.write("a.txt")
        self.write("handover/ledger.csv", "package_path,sha256\n")
        code, out = self.build(self.candidates(["a.txt"]))
        self.assertEqual(code, 2)
        self.assertIn("phải là", out.text())
