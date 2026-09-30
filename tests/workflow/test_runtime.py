# -*- coding: utf-8 -*-
"""Test nhận biết nơi đang chạy và nạp biến môi trường (src/workflow/runtime.py).

Điều quan trọng nhất được khoá ở đây: **thư mục Drive phải nhận ra bằng FILE ĐÁNH DẤU**, không
phải bằng tên. MyDrive và Shared drives trông giống nhau, mà chỉ một trong hai là thư mục giảng
viên cấp; đoán theo tên thì notebook ghi kết quả vào chỗ không ai tìm thấy.

Phần cuối khoá `end_session`: ngắt phiên Colab khi lượt chạy xong. Hàm này chạy ở CUỐI một lượt
chạy đã tốn hàng chục phút, nên nó không được phép ném lỗi ra ngoài - và chỉ được ngắt khi CHẮC
CHẮN đang ở Colab và cấu hình cho phép.

Chạy: python -m unittest discover -s tests
"""

import contextlib
import io
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from src.workflow import runtime
from src.core import paths

MARKER = ".sentimentx_root"


class TestEnvironment(unittest.TestCase):
    def test_env_name_from_variable(self):
        with mock.patch.dict(os.environ, {"SENTIMENTX_ENV": "colab"}):
            self.assertEqual(runtime.env_name(), "colab")
        with mock.patch.dict(os.environ, {"SENTIMENTX_ENV": "LOCAL"}):
            self.assertEqual(runtime.env_name(), "local")

    def test_env_name_ignores_unknown_value(self):
        with mock.patch.dict(os.environ, {"SENTIMENTX_ENV": "lung-tung"}):
            self.assertIn(runtime.env_name(), ("colab", "local"))

    def test_load_env_reads_a_file_and_reports_names_only(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / ".env.colab"
            path.write_text("SENTIMENTX_TEST_BIEN=gi-tri-that\n# chu thich\n\n",
                            encoding="utf-8")
            os.environ.pop("SENTIMENTX_TEST_BIEN", None)
            try:
                lines = runtime.load_env(colab_env_file=str(path))
                self.assertIn(str(path), lines["files"])
                self.assertEqual(os.environ.get("SENTIMENTX_TEST_BIEN"), "gi-tri-that")
                # Chỉ tên biến được báo lại, không bao giờ giá trị.
                self.assertNotIn("gi-tri-that", str(lines))
            finally:
                os.environ.pop("SENTIMENTX_TEST_BIEN", None)


    def test_load_env_ignores_empty_values(self):
        """Khoá để trống nghĩa là "không đặt".

        Ca thật: `.env` có `HF_HOME=` để trống, biến bị đặt thành chuỗi rỗng, và `huggingface_hub`
        ghép `os.path.join("", "hub")` thành thư mục `hub` NGAY TRONG REPO rồi tải 6,3 GB model vào
        cây làm việc. Đặt chuỗi rỗng không phải là "không cấu hình" đối với thư viện bên dưới.
        """
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / ".env.colab"
            path.write_text("SENTIMENTX_TEST_RONG=\nSENTIMENTX_TEST_CO=that\n", encoding="utf-8")
            for name in ("SENTIMENTX_TEST_RONG", "SENTIMENTX_TEST_CO"):
                os.environ.pop(name, None)
            try:
                runtime.load_env(colab_env_file=str(path))
                self.assertIsNone(os.environ.get("SENTIMENTX_TEST_RONG"))
                self.assertEqual(os.environ.get("SENTIMENTX_TEST_CO"), "that")
            finally:
                for name in ("SENTIMENTX_TEST_RONG", "SENTIMENTX_TEST_CO"):
                    os.environ.pop(name, None)


    def test_load_env_reads_a_file_with_a_byte_order_mark(self):
        """Tệp env gửi cho người chạy có BOM (để Windows hiện đúng chữ tiếng Việt).

        `utf-8-sig` bỏ BOM. Không bỏ thì BOM lọt vào TÊN khoá đầu tiên và khoá đó biến mất trong im
        lặng - token có trong tệp mà chương trình vẫn báo thiếu token.
        """
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / ".env.colab"
            path.write_bytes(b"\xef\xbb\xbfDAGSHUB_TOKEN=gia-tri-that\n")
            os.environ.pop("DAGSHUB_TOKEN", None)
            try:
                runtime.load_env(colab_env_file=str(path))
                self.assertEqual(os.environ.get("DAGSHUB_TOKEN"), "gia-tri-that")
            finally:
                os.environ.pop("DAGSHUB_TOKEN", None)


class TestDriveDir(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.shared = self.root / "Shareddrives" / "nhom"
        self.mine = self.root / "MyDrive" / "nhom"

    def tearDown(self):
        self._tmp.cleanup()

    def candidates(self):
        return [str(self.root / "MyDrive" / "{folder}"),
                str(self.root / "Shareddrives" / "{folder}")]

    def test_finds_the_folder_that_has_the_marker(self):
        self.mine.mkdir(parents=True)
        (self.mine / MARKER).write_text("", encoding="utf-8")
        found = runtime.drive_dir(folder="nhom", candidates=self.candidates())
        self.assertEqual(found, self.mine)

    def test_ignores_a_folder_without_the_marker(self):
        self.mine.mkdir(parents=True)
        self.assertIsNone(runtime.drive_dir(folder="nhom", candidates=self.candidates()))

    def test_falls_back_to_the_shared_drive(self):
        self.shared.mkdir(parents=True)
        (self.shared / MARKER).write_text("", encoding="utf-8")
        found = runtime.drive_dir(folder="nhom", candidates=self.candidates())
        self.assertEqual(found, self.shared)

    def test_none_when_drive_is_not_mounted(self):
        self.assertIsNone(runtime.drive_dir(folder="nhom", candidates=self.candidates()))

    def test_finds_the_folder_when_its_name_is_unknown(self):
        """Người nhận notebook chỉ copy thư mục của nhóm vào Drive - tên có thể khác.

        Đây là đường đi chính của bản giao: bắt người chạy khai đúng tên thư mục là bắt họ làm một
        việc mà máy làm được, và tên thật thường là "SentimentX (1)" sau khi copy.
        """
        other = self.root / "MyDrive" / "SentimentX (1)"
        other.mkdir(parents=True)
        (other / MARKER).write_text("", encoding="utf-8")
        found = runtime.drive_dir(folder="", candidates=self.candidates())
        self.assertEqual(found, other)

    def test_the_search_never_picks_a_folder_without_the_marker(self):
        (self.root / "MyDrive" / "TaiLieu").mkdir(parents=True)
        (self.root / "MyDrive" / "TaiLieu" / "data").mkdir()
        self.assertIsNone(runtime.drive_dir(folder="", candidates=self.candidates()))

    def test_the_search_prefers_the_folder_that_looks_prepared(self):
        for name in ("b", "a"):
            folder = self.root / "MyDrive" / name
            folder.mkdir(parents=True)
            (folder / MARKER).write_text("", encoding="utf-8")
        (self.root / "MyDrive" / "b" / "data").mkdir()
        self.assertEqual(runtime.drive_dir(folder="", candidates=self.candidates()),
                         self.root / "MyDrive" / "b")

    def test_the_search_also_looks_inside_a_shared_drive(self):
        other = self.root / "Shareddrives" / "Khoa CNTT"
        other.mkdir(parents=True)
        (other / MARKER).write_text("", encoding="utf-8")
        self.assertEqual(runtime.drive_dir(folder="", candidates=self.candidates()), other)

    def test_retries_until_the_marker_shows_up(self):
        """`drive.mount()` trả về TRƯỚC khi Drive liệt kê xong danh sách thư mục.

        Lỗi thật trên Colab: cùng một phiên, notebook này thấy thư mục nhóm còn notebook kia thì không
        - lượt chạy sau đó rơi vào máy ảo, nơi không có dữ liệu gốc. Phải thử lại rồi mới kết luận.
        """
        with mock.patch.object(runtime, "_find_drive",
                               side_effect=[None, None, self.mine]) as finder:
            with mock.patch.object(runtime.time, "sleep") as sleeper:
                found = runtime.drive_dir(folder="nhom", candidates=self.candidates(),
                                          attempts=3, delay=2)
        self.assertEqual(found, self.mine)
        self.assertEqual(finder.call_count, 3)
        self.assertEqual(sleeper.call_count, 2)

    def test_gives_up_after_the_last_attempt(self):
        with mock.patch.object(runtime, "_find_drive", return_value=None) as finder:
            with mock.patch.object(runtime.time, "sleep") as sleeper:
                found = runtime.drive_dir(folder="nhom", candidates=self.candidates(),
                                          attempts=2, delay=1)
        self.assertIsNone(found)
        self.assertEqual(finder.call_count, 2)
        self.assertEqual(sleeper.call_count, 1)

    def test_one_attempt_does_not_sleep(self):
        """Mặc định (một lượt) vẫn như cũ: không chờ, không đổi hành vi của nơi gọi khác."""
        with mock.patch.object(runtime, "_find_drive", return_value=None):
            with mock.patch.object(runtime.time, "sleep") as sleeper:
                self.assertIsNone(runtime.drive_dir(folder="nhom",
                                                    candidates=self.candidates()))
        self.assertEqual(sleeper.call_count, 0)

    def test_a_folder_with_the_package_structure_counts_as_the_group_folder(self):
        """Gói bàn giao có `env/.env.colab` (và `data/` + `experiments/`) - đó là dấu hiệu nhận ra.

        Vì sao cần dấu hiệu này: tên file đánh dấu bắt đầu bằng dấu chấm nên **web Drive không tạo
        được**, và người chia sẻ thư mục (A) có thể chỉ share rồi thôi - không nên bắt ai phải tạo nó.
        """
        folder = self.root / "MyDrive" / "ABSA_2026_2027"
        (folder / "env").mkdir(parents=True)
        (folder / "env" / ".env.colab").write_text("", encoding="utf-8")
        (folder / "data").mkdir()
        (folder / "experiments").mkdir()
        self.assertTrue(runtime.looks_like_group_dir(folder))
        found = runtime.drive_candidates(self.candidates())
        self.assertEqual([item["path"] for item in found], [folder])
        self.assertEqual(found[0]["how"], "structure")
        self.assertTrue(found[0]["prepared"])

    def test_a_shared_folder_reached_by_shortcut_needs_no_marker(self):
        """ĐÚNG MÔ HÌNH CỦA NHÓM: A chia sẻ, b/c/d bấm lối tắt, KHÔNG ai tạo `.sentimentx_root`.

        Thư mục đích của lối tắt nằm ở `MyDrive/.shortcut-targets-by-id/<id>/<tên>` và chỉ có cấu trúc
        của gói. Trước đây chỗ nhận theo cấu trúc chỉ xét một cấp nên không thấy nó, và b/c/d bị chặn
        dù đã làm đúng phần việc của mình.
        """
        target = self.root / "MyDrive" / ".shortcut-targets-by-id" / "1AbC" / "ABSA_2026_2027"
        (target / "env").mkdir(parents=True)
        (target / "env" / ".env.colab").write_text("", encoding="utf-8")
        (target / "data").mkdir()
        (target / "experiments").mkdir()
        self.assertEqual(runtime.drive_dir(folder="", candidates=self.candidates()), target)
        found = runtime.drive_candidates(self.candidates())
        self.assertEqual(found[0]["path"], target)
        self.assertEqual(found[0]["where"], "qua lối tắt (shortcut)")

    def test_the_marker_wins_over_plain_structure(self):
        """Có cả hai loại thư mục thì chọn thư mục CÓ FILE ĐÁNH DẤU - dấu hiệu chắc chắn hơn."""
        marked = self.root / "MyDrive" / "co-dau"
        marked.mkdir(parents=True)
        (marked / MARKER).write_text("", encoding="utf-8")
        plain = self.root / "MyDrive" / "chi-co-cau-truc"
        (plain / "data").mkdir(parents=True)
        (plain / "experiments").mkdir()
        found = runtime.drive_candidates(self.candidates())
        self.assertEqual(found[0]["path"], marked)
        self.assertEqual(found[0]["how"], "marker")

    def test_a_plain_folder_is_not_mistaken_for_the_group_folder(self):
        folder = self.root / "MyDrive" / "TaiLieu"
        (folder / "data").mkdir(parents=True)
        self.assertFalse(runtime.looks_like_group_dir(folder))
        self.assertEqual(runtime.drive_candidates(self.candidates()), [])

    def test_listing_names_each_root_separately(self):
        """In TỪNG gốc: thư mục nhóm có thể nằm trong Shared drive, không phải MyDrive.

        Gộp hai gốc vào một dòng thì người đọc không biết `Shareddrives` rỗng (tài khoản chưa được
        chia sẻ) hay có thư mục khác - mà đó chính là câu hỏi cần trả lời.
        """
        (self.root / "MyDrive" / "TaiLieu").mkdir(parents=True)
        self.mine.mkdir(parents=True)
        (self.root / "Shareddrives" / "Khoa CNTT").mkdir(parents=True)
        listing = runtime.drive_listing(self.candidates())
        by_root = {item["root"].name: item["names"] for item in listing}
        self.assertEqual(by_root["MyDrive"], ["TaiLieu", "nhom"])
        self.assertEqual(by_root["Shareddrives"], ["Khoa CNTT"])
        self.assertFalse(any(item["gone"] for item in listing))

    def test_listing_marks_a_root_that_is_not_there(self):
        """Gốc chưa mount thì phải NÓI RA, thay vì im lặng coi như không có thư mục nào."""
        self.mine.mkdir(parents=True)
        listing = runtime.drive_listing(self.candidates())
        self.assertEqual([item["root"].name for item in listing if item["gone"]], ["Shareddrives"])
        self.assertEqual(runtime.drive_roots(self.candidates()),
                         [self.root / "MyDrive", self.root / "Shareddrives"])

    def test_the_search_also_looks_inside_a_shared_drive(self):
        """Thư mục nhóm có thể nằm TRONG một thư mục con của shared drive.

        Cấu trúc hay gặp: `Shareddrives/Khoa CNTT/ABSA_2026_2027/` - nhóm để dự án trong shared drive
        của khoa. Quét một cấp thì không thấy, và lượt chạy dừng dù dữ liệu nằm ngay đó.
        """
        nested = self.root / "Shareddrives" / "Khoa CNTT" / "ABSA_2026_2027"
        nested.mkdir(parents=True)
        (nested / MARKER).write_text("", encoding="utf-8")
        self.assertEqual(runtime.drive_dir(folder="", candidates=self.candidates()), nested)

    def test_the_search_follows_a_drive_shortcut(self):
        """A chia sẻ thư mục cho b/c/d: mỗi người bấm "Add shortcut to My Drive" một lần.

        Drive để lối tắt trong thư mục ẩn `.shortcut-targets-by-id/<id>/<tên>`. Không xét chỗ này thì
        b/c/d thấy "chưa có thư mục nhóm" dù thư mục đã được chia sẻ và lối tắt đã có - đúng cảnh đã
        gặp, vì `MyDrive` của họ chỉ có thư mục riêng.
        """
        target = self.root / "MyDrive" / ".shortcut-targets-by-id" / "1AbC" / "ABSA_2026_2027"
        target.mkdir(parents=True)
        (target / MARKER).write_text("", encoding="utf-8")
        self.assertEqual(runtime.drive_dir(folder="", candidates=self.candidates()), target)

    def test_listing_reports_the_shortcut_targets(self):
        """Lối tắt phải được IN RA: đó là câu trả lời cho "tôi được chia sẻ rồi mà sao không thấy"."""
        (self.root / "MyDrive" / ".shortcut-targets-by-id" / "1AbC" / "ABSA_2026_2027").mkdir(
            parents=True)
        listing = {item["root"].name: item["shortcuts"]
                   for item in runtime.drive_listing(self.candidates())}
        self.assertEqual(listing["MyDrive"], ["ABSA_2026_2027"])

    def test_the_closest_folder_with_the_marker_wins(self):
        """Có dấu ở cả hai cấp thì lấy cấp MỘT: gần gốc hơn, và tránh chọn thư mục con của nó."""
        outer = self.root / "Shareddrives" / "Khoa CNTT"
        outer.mkdir(parents=True)
        (outer / MARKER).write_text("", encoding="utf-8")
        inner = outer / "ABSA_2026_2027"
        inner.mkdir()
        (inner / MARKER).write_text("", encoding="utf-8")
        self.assertEqual(runtime.drive_dir(folder="", candidates=self.candidates()), outer)

    def test_env_file_path_inside_the_drive(self):
        self.mine.mkdir(parents=True)
        (self.mine / MARKER).write_text("", encoding="utf-8")
        path = runtime.drive_env_file(folder="nhom", candidates=self.candidates())
        self.assertEqual(path.name, ".env.colab")
        self.assertEqual(path.parent.name, "env")

    def test_env_file_is_none_without_drive(self):
        self.assertIsNone(runtime.drive_env_file(folder="nhom", candidates=self.candidates()))


class TestEndSession(unittest.TestCase):
    """`runtime.end_session`: ngắt phiên Colab khi lượt chạy xong.

    VÌ SAO KHOÁ NHỮNG CA NÀY: hàm chạy ở CUỐI một lượt chạy đã tốn hàng chục phút, nên nó KHÔNG
    được phép ném lỗi ra ngoài (hỏng bước ngắt phiên mà làm chết lượt chạy thì mất cả lượt), và nó
    chỉ được ngắt khi CHẮC CHẮN đang ở Colab và cấu hình cho phép - ngắt máy cá nhân là vô nghĩa,
    còn ngắt khi người dùng đã đặt `0` là làm sai ý họ.
    """

    def setUp(self):
        # `is_colab()` còn nhìn hai biến môi trường này, nên ca "máy cá nhân" phải xoá chúng.
        patcher = mock.patch.dict(os.environ, {}, clear=False)
        patcher.start()
        self.addCleanup(patcher.stop)
        self._clear()

    def _clear(self):
        for name in ("COLAB_RELEASE_TAG", "COLAB_GPU", runtime.ENV_END_SESSION):
            os.environ.pop(name, None)

    def install_fake_colab(self, error=None):
        """Nhét một `google.colab` GIẢ vào `sys.modules`; trả về danh sách các lần gọi `unassign`.

        Bắt chước đúng cách Colab thật xuất hiện với Python: một gói `google.colab` có module con
        `runtime`. Không có gói này thì `is_colab()` trả False - và đó là ca máy cá nhân.
        """
        calls = []

        def unassign():
            calls.append("unassign")
            if error is not None:
                raise error

        runtime_module = types.ModuleType("google.colab.runtime")
        runtime_module.unassign = unassign
        package = types.ModuleType("google.colab")
        package.runtime = runtime_module
        patcher = mock.patch.dict(sys.modules, {
            "google.colab": package, "google.colab.runtime": runtime_module})
        patcher.start()
        self.addCleanup(patcher.stop)
        return calls

    @staticmethod
    def fake_log():
        """Ghi lại những gì hàm báo vào một đối tượng cùng hình dạng với `runlog.RunLog`."""

        class _Log:
            def __init__(self):
                self.steps = []
                self.warnings = []

            def step(self, message, seconds=None):
                self.steps.append(message)

            def warn(self, message, context=None):
                self.warnings.append(message)

        return _Log()

    def test_o_may_ca_nhan_thi_khong_ngat(self):
        """Không ở Colab: không làm gì, và nói rõ vì sao - để `run.log` không im lặng."""
        message = runtime.end_session()
        self.assertIn("máy cá nhân", message)

    def test_o_colab_thi_ngat_dung_mot_lan(self):
        calls = self.install_fake_colab()
        message = runtime.end_session()
        self.assertEqual(calls, ["unassign"])
        self.assertIn("Đã ngắt", message)

    def test_dat_bien_thanh_0_thi_khong_ngat(self):
        """`SENTIMENTX_END_SESSION=0` là ý người dùng: giữ phiên lại."""
        calls = self.install_fake_colab()
        os.environ[runtime.ENV_END_SESSION] = "0"
        message = runtime.end_session()
        self.assertEqual(calls, [])
        self.assertIn(runtime.ENV_END_SESSION, message)

    def test_dat_bien_thanh_1_thi_ngat(self):
        calls = self.install_fake_colab()
        os.environ[runtime.ENV_END_SESSION] = "1"
        message = runtime.end_session()
        self.assertEqual(calls, ["unassign"])
        self.assertIn("Đã ngắt", message)

    def test_gia_tri_bien_la_thi_bao_ro_va_khong_ngat(self):
        """Giá trị lạ thì KHÔNG đoán ý người dùng: báo rõ và giữ phiên lại."""
        calls = self.install_fake_colab()
        os.environ[runtime.ENV_END_SESSION] = "yes"
        message = runtime.end_session()
        self.assertEqual(calls, [])
        self.assertIn("không hợp lệ", message)
        self.assertIn("0 hoặc 1", message)

    def test_loi_ngat_phien_khong_lam_chet_luot_chay(self):
        """Colab không ngắt được (mạng, phiên đã hết) thì báo, KHÔNG ném ra ngoài."""
        self.install_fake_colab(error=RuntimeError("Boom"))
        log = self.fake_log()
        message = runtime.end_session(log=log)
        self.assertIn("Boom", message)
        self.assertEqual(log.warnings, [message])
        self.assertEqual(log.steps, [])

    def test_thong_bao_duoc_ghi_vao_log(self):
        self.install_fake_colab()
        log = self.fake_log()
        message = runtime.end_session(log=log)
        self.assertEqual(log.steps, [message])
        self.assertEqual(log.warnings, [])

    def test_hai_tep_env_mau_deu_khai_co_ngat_phien(self):
        """Cờ `SENTIMENTX_END_SESSION` phải có trong HAI tệp mẫu (`.env`, `.env.colab`).

        Vì sao khoá: đây là cách duy nhất người chạy biết có khoá này mà tắt/bật. Hai tệp THẬT
        (`.env`, `.env.colab`) không test được - chúng không vào git và mỗi máy một khác - nên tệp
        mẫu là chỗ duy nhất giữ được lời hứa "cờ này tồn tại".

        Tệp `.env.colab.example` phải là UTF-8 KÈM BOM: nó được gửi kèm gói bàn giao, mở bằng Notepad
        hoặc trình xem trong WinRAR phải hiện đúng chữ tiếng Việt (06_conventions.md).
        """
        for name, expect_bom in ((".env.example", False), (".env.colab.example", True)):
            path = paths.root() / name
            text = path.read_text(encoding="utf-8-sig")
            with self.subTest(file=name):
                self.assertIn("{}={}".format(runtime.ENV_END_SESSION, 1), text,
                              "thiếu dòng khai cờ trong {}".format(name))
                comments = [line for line in text.splitlines()
                            if line.strip().startswith("#") and runtime.ENV_END_SESSION in line]
                self.assertTrue(comments, "thiếu dòng chú thích giải thích cờ trong {}".format(name))
                self.assertEqual(path.read_bytes()[:3] == b"\xef\xbb\xbf", expect_bom,
                                 "BOM của {} không đúng quy ước".format(name))


class EndSessionOnErrorTest(unittest.TestCase):
    """Khối `runtime.end_session_on_error` - dùng ở mọi ô notebook để "ô nào lỗi cũng ngắt phiên".

    VÌ SAO KHOÁ NHỮNG CA NÀY: khối này là thứ duy nhất khiến một ô notebook lỗi giữa chừng không bỏ
    lại phiên Colab đang giữ GPU. Ba mặt của nó: lỗi thường (ngắt + còn dấu vết), ô TỰ dừng bằng
    `SystemExit` (ngắt, nhưng không in thêm khi không có lời nhắn), và người dùng bấm Stop
    (`KeyboardInterrupt` - KHÔNG ngắt, vì họ ngồi trước máy và cần phiên để sửa).
    """

    def setUp(self):
        patcher = mock.patch.dict(os.environ, {}, clear=False)
        patcher.start()
        self.addCleanup(patcher.stop)
        for name in ("COLAB_RELEASE_TAG", "COLAB_GPU", runtime.ENV_END_SESSION):
            os.environ.pop(name, None)

    def install_fake_colab(self):
        """`google.colab` GIẢ; trả về danh sách các lần gọi `unassign`."""
        calls = []

        def unassign():
            calls.append("unassign")

        colab_runtime = types.ModuleType("google.colab.runtime")
        colab_runtime.unassign = unassign
        package = types.ModuleType("google.colab")
        package.runtime = colab_runtime
        patcher = mock.patch.dict(sys.modules, {"google.colab": package,
                                                "google.colab.runtime": colab_runtime})
        patcher.start()
        self.addCleanup(patcher.stop)
        return calls

    def test_than_khoi_thanh_cong_thi_khong_ngat(self):
        calls = self.install_fake_colab()
        with contextlib.redirect_stdout(io.StringIO()):
            with runtime.end_session_on_error():
                pass
        self.assertEqual(calls, [])

    def test_loi_thuong_thi_in_dau_vet_Roi_moi_ngat(self):
        calls = self.install_fake_colab()
        buffer = io.StringIO()
        with self.assertRaises(RuntimeError):
            with contextlib.redirect_stderr(buffer):
                with runtime.end_session_on_error():
                    raise RuntimeError("hỏng giữa chừng")
        self.assertEqual(calls, ["unassign"])
        self.assertIn("hỏng giữa chừng", buffer.getvalue(), "dấu vết phải còn nguyên")

    def test_o_tu_dung_thi_in_ly_do_roi_moi_ngat(self):
        calls = self.install_fake_colab()
        buffer = io.StringIO()
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stdout(buffer):
                with runtime.end_session_on_error():
                    raise SystemExit("DỪNG: còn 2 việc phải sửa")
        self.assertEqual(calls, ["unassign"])
        self.assertIn("DỪNG: còn 2 việc phải sửa", buffer.getvalue())

    def test_systemexit_khong_loi_nhan_thi_khong_in_them(self):
        """`SystemExit(1)` chỉ là mã thoát: ô đã in lý do rồi, in thêm số 1 là vô nghĩa."""
        calls = self.install_fake_colab()
        buffer = io.StringIO()
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stdout(buffer):
                with runtime.end_session_on_error():
                    raise SystemExit(1)
        self.assertEqual(calls, ["unassign"])
        self.assertNotIn("1", [line.strip() for line in buffer.getvalue().splitlines()])

    def test_nguoi_dung_bam_stop_thi_khong_ngat(self):
        calls = self.install_fake_colab()
        with self.assertRaises(KeyboardInterrupt):
            with contextlib.redirect_stdout(io.StringIO()):
                with runtime.end_session_on_error():
                    raise KeyboardInterrupt()
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
