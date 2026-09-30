# -*- coding: utf-8 -*-
"""Test việc chuẩn bị môi trường chạy notebook (src/bootstrap.py).

CÁC PHÉP KIỂM NÀY Ở ĐÂU RA: trước Batch 5b chúng soi CHUỖI trong Ô BOOTSTRAP
(`tests/test_templates.py::TestBootstrap`). Ô đó nay mỏng, logic nằm ở thư viện, nên phép kiểm
chuyển về đây - cùng câu chữ, cùng nhánh, nhưng kiểm HÀNH VI (gọi hàm với điểm tiêm) thay vì đọc
chuỗi trong notebook. Kiểm hành vi bắt được lỗi mà đọc chuỗi không bắt được: một dòng in ra ở nhánh
sai, một bước bị bỏ qua, một lệnh không được gọi.

VÌ SAO PHẢI TIÊM ĐƯỢC: máy cá nhân không có Colab, không có `/content/drive`, không có `apt-get`.
Không tiêm thì đúng những nhánh chỉ-chạy-trên-Colab - nhánh hay hỏng nhất - không bao giờ được kiểm.
Ranh giới với MÁY THẬT (`runtime.drive_dir`, `runtime.drive_listing`) thì vá bằng `mock.patch.object`
vì ở đây không thể tạo ra Drive thật.

Chạy: python -m unittest discover -s tests
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src import bootstrap


class Recorder:
    """Thay cho `print`: ghi lại từng câu để so câu chữ (thứ người đọc dựa vào để dò lỗi)."""

    def __init__(self):
        self.lines = []

    def __call__(self, message):
        self.lines.append(str(message))

    def text(self):
        return "\n".join(self.lines)


class Done:
    """Kết quả giả của `subprocess.run`."""

    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def fake_run(recorder, returncode=0, stdout="", stderr=""):
    """Thay cho `subprocess.run`: ghi lại lệnh đã chạy, trả mã thoát theo ý test."""

    def run(command, **kwargs):
        recorder.lines.append(" ".join(str(part) for part in command))
        return Done(returncode, stdout, stderr)

    return run


def fake_spec(missing=()):
    """Thay cho `importlib.util.find_spec`: nói gói nào CHƯA có."""
    absent = set(missing)

    def spec(name):
        return None if name in absent else object()

    return spec


def fake_download(tiny=False):
    """Thay cho `urllib.request.urlretrieve`: ghi file đủ lớn, hoặc quá nhỏ khi `tiny=True`."""
    calls = []

    def download(url, target):
        name = url.split("/VnCoreNLP/master/")[-1]
        minimum = dict(bootstrap.VNCORENLP_FILES)[name]
        path = Path(target)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"x" * (100 if tiny else minimum + 1))
        calls.append((url, str(path)))

    download.calls = calls
    return download


class EnvCase(unittest.TestCase):
    """Bỏ ghi đè gốc đường dẫn của MÁY đang chạy, trả lại nguyên trạng sau khi test."""

    def setUp(self):
        patcher = mock.patch.dict(os.environ)
        patcher.start()
        self.addCleanup(patcher.stop)
        for name in ("SENTIMENTX_DATA_ROOT", "SENTIMENTX_RESULTS_ROOT"):
            os.environ.pop(name, None)


class PrepareTest(EnvCase):
    """`prepare`: mount Drive, dò thư mục nhóm, nạp env, đặt hai gốc - và khi nào thì DỪNG."""

    def test_o_may_ca_nhan_thi_khong_mount_va_khong_dung(self):
        log = Recorder()
        mount = mock.Mock()
        result = bootstrap.prepare(colab=False, mount=mount, log=log)
        mount.assert_not_called()
        self.assertIsNone(result["drive"])
        self.assertIsNone(result["stop"], "máy cá nhân không có gì để dừng")
        self.assertIn("Nơi chạy    :", log.text())
        self.assertIn("Gốc dữ liệu :", log.text())

    def test_o_colab_thi_tu_mount_drive(self):
        log = Recorder()
        mount = mock.Mock()
        with mock.patch.object(bootstrap.runtime, "drive_dir", return_value=None), \
                mock.patch.object(bootstrap.runtime, "drive_listing", return_value=[]):
            bootstrap.prepare(colab=True, mount=mount, log=log)
        mount.assert_called_once_with("/content/drive")
        self.assertIn("Chưa mount Drive - đang mount (Colab hỏi quyền, bấm Allow)...", log.text())

    def test_khong_mount_duoc_thi_bao_chu_khong_lam_chet_notebook(self):
        log = Recorder()

        def broken(path):
            raise RuntimeError("hết quyền")

        with mock.patch.object(bootstrap.runtime, "drive_dir", return_value=None), \
                mock.patch.object(bootstrap.runtime, "drive_listing", return_value=[]):
            bootstrap.prepare(colab=True, mount=broken, log=log)
        self.assertIn("  không mount được Drive (hết quyền).", log.text())

    def test_dat_hai_goc_duong_dan_tu_thu_muc_nhom(self):
        log = Recorder()
        with tempfile.TemporaryDirectory() as tmp:
            drive = Path(tmp)
            with mock.patch.object(bootstrap.runtime, "drive_dir", return_value=drive), \
                    mock.patch.object(bootstrap.runtime, "drive_env_file", return_value=None):
                result = bootstrap.prepare(colab=True, mount=mock.Mock(), log=log)
            self.assertEqual(os.environ.get("SENTIMENTX_DATA_ROOT"), str(drive / "data"))
            self.assertEqual(os.environ.get("SENTIMENTX_RESULTS_ROOT"),
                             str(drive / "experiments"))
            self.assertEqual(result["drive"], drive)
        self.assertIn("Drive       : {} (nhận ra bằng file đánh dấu)".format(drive), log.text())
        self.assertIsNone(result["stop"])

    def test_khong_co_file_danh_dau_thi_noi_ro_cach_nhan_ra(self):
        """Nhận ra bằng CẤU TRÚC GÓI vẫn chạy được - phải nói ra, đừng để người đọc tưởng lỗi."""
        log = Recorder()
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(bootstrap.runtime, "drive_dir", return_value=Path(tmp)), \
                    mock.patch.object(bootstrap.runtime, "drive_env_file", return_value=None):
                bootstrap.prepare(colab=True, mount=mock.Mock(), log=log)
        self.assertIn("CẤU TRÚC GÓI", log.text())
        self.assertIn(".sentimentx_root", log.text())

    def test_thieu_thu_muc_nhom_thi_TRA_stop_va_in_cach_sua(self):
        """Không thấy thư mục nhóm: trả `stop` (thư viện KHÔNG tự `SystemExit`), in 3 nguyên nhân."""
        log = Recorder()
        listing = [{"gone": True, "root": "/content/drive/MyDrive", "names": [], "shortcuts": []}]
        with mock.patch.object(bootstrap.runtime, "drive_dir", return_value=None), \
                mock.patch.object(bootstrap.runtime, "drive_listing", return_value=listing):
            result = bootstrap.prepare(colab=True, mount=mock.Mock(), log=log)
        self.assertIsNotNone(result["stop"])
        self.assertIn("DỪNG: chưa thấy thư mục nhóm", result["stop"])
        text = log.text()
        for needle in ("CHƯA thấy gốc Drive: /content/drive/MyDrive",
                       "Ba nguyên nhân hay gặp", "MỘT TÀI KHOẢN GOOGLE KHÁC",
                       "Add shortcut to My Drive", "SHARED DRIVE", "SENTIMENTX_DATA_ROOT"):
            self.assertIn(needle, text)

    def test_thay_thu_muc_nhom_roi_thi_khong_cho_them_30_giay(self):
        """Lần dò ĐẦU tiên thấy rồi thì không chờ - chờ vô ích làm người chạy tưởng notebook treo."""
        log = Recorder()
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(bootstrap.runtime, "drive_dir",
                                   return_value=Path(tmp)) as found, \
                    mock.patch.object(bootstrap.runtime, "drive_env_file", return_value=None):
                bootstrap.prepare(colab=True, mount=mock.Mock(), log=log)
        self.assertEqual(found.call_count, 1)
        self.assertNotIn("chờ Drive liệt kê xong", log.text())

    def test_in_tung_goc_drive_va_loi_tat(self):
        log = Recorder()
        listing = [{"gone": False, "root": "/content/drive/MyDrive", "names": ["ABSA"],
                    "shortcuts": ["nhom-cua-A"]}]
        with mock.patch.object(bootstrap.runtime, "drive_dir", return_value=None), \
                mock.patch.object(bootstrap.runtime, "drive_listing", return_value=listing):
            bootstrap.prepare(colab=True, mount=mock.Mock(), log=log)
        text = log.text()
        self.assertIn("  /content/drive/MyDrive: ABSA", text)
        self.assertIn("lối tắt (shortcut) đang trỏ tới: nhom-cua-A", text)


class InstallPackagesTest(EnvCase):
    """`install_packages`: cài gói máy ảo còn thiếu, và gỡ `torchao` cũ khi nó chặn `peft`."""

    EXPERIMENT = "qwen3-0.6b/prompt-cot/exp001"

    def test_o_may_ca_nhan_thi_khong_cai_gi(self):
        log = Recorder()
        commands = Recorder()
        result = bootstrap.install_packages(self.EXPERIMENT, colab=False,
                                            run=fake_run(commands), log=log)
        self.assertEqual(commands.lines, [])
        self.assertEqual(log.lines, [])
        self.assertFalse(result["colab"])

    def test_cai_goi_con_thieu_va_in_ma_thoat(self):
        log = Recorder()
        commands = Recorder()
        result = bootstrap.install_packages(
            self.EXPERIMENT, colab=True, run=fake_run(commands, returncode=0),
            spec=fake_spec(missing=("bitsandbytes",)), load=lambda *parts: {"config": {}}, log=log)
        self.assertIn("Thiếu gói bitsandbytes - đang cài...", log.text())
        self.assertIn("  pip install -> 0", log.text())
        self.assertEqual(result["missing"], ["bitsandbytes"])
        self.assertEqual(result["installed"], ["bitsandbytes"])
        self.assertIn("-m pip install -q bitsandbytes", commands.lines[0])

    def test_cai_hong_thi_in_phan_cuoi_cua_log(self):
        """pip hỏng: mã thoát khác 0 kèm đoạn cuối của log - đó là thứ duy nhất để dò lỗi."""
        log = Recorder()
        result = bootstrap.install_packages(
            self.EXPERIMENT, colab=True,
            run=fake_run(Recorder(), returncode=1, stderr="ERROR: không tải được gói mlflow"),
            spec=fake_spec(missing=("mlflow",)), load=lambda *parts: {"config": {}}, log=log)
        self.assertIn("  pip install -> 1", log.text())
        self.assertIn("ERROR: không tải được gói mlflow", log.text())
        self.assertEqual(result["installed"], [], "cài hỏng thì KHÔNG được ghi là đã cài")

    def test_chi_cai_peft_cho_duong_huan_luyen(self):
        """Đường prompt không được cài `peft` - gói đó chỉ phục vụ LoRA."""
        commands = Recorder()
        training = bootstrap.install_packages(
            "visobert/lora/exp001", colab=True, run=fake_run(commands),
            spec=fake_spec(missing=("peft",)),
            load=lambda *parts: {"config": {"enabled": True}}, log=Recorder())
        self.assertTrue(training["needs_training"])
        self.assertIn("peft", training["missing"])
        prompt = bootstrap.install_packages(
            self.EXPERIMENT, colab=True, run=fake_run(commands),
            spec=fake_spec(missing=("peft",)), load=lambda *parts: {"config": {}}, log=Recorder())
        self.assertFalse(prompt["needs_training"])
        self.assertNotIn("peft", prompt["missing"])

    def test_doc_config_hong_thi_coi_nhu_duong_prompt(self):
        """Đọc config hỏng KHÔNG được làm chết ô này: còn phải cài `mlflow` cho phần ghi nhận."""
        log = Recorder()

        def broken(*parts):
            raise RuntimeError("config lạ")

        result = bootstrap.install_packages(self.EXPERIMENT, colab=True, run=fake_run(Recorder()),
                                            spec=fake_spec(missing=("mlflow",)), load=broken, log=log)
        self.assertIn("(chưa biết thí nghiệm này có huấn luyện không: config lạ)", log.text())
        self.assertFalse(result["needs_training"])
        self.assertIn("mlflow", result["missing"])

    def test_go_torchao_khi_peft_khong_dung_duoc_no(self):
        """Ca thật: Colab có torchao 0.10.0, peft đòi >= 0.16.0 -> phải gỡ torchao."""
        log = Recorder()
        commands = Recorder()

        def bad_torchao():
            raise ImportError("Found an incompatible version of torchao 0.10.0; peft needs 0.16.0")

        result = bootstrap.install_packages(
            "visobert/lora/exp001", colab=True, run=fake_run(commands), spec=fake_spec(),
            load=lambda *parts: {"config": {"enabled": True}}, torchao=bad_torchao, log=log)
        self.assertTrue(result["torchao_removed"])
        text = log.text()
        self.assertIn("peft không dùng được torchao của máy ảo:", text)
        self.assertIn("  đang gỡ torchao (LoRA của dự án không dùng gói này)...", text)
        self.assertIn("  pip uninstall -> 0", text)
        self.assertIn("-m pip uninstall -y -q torchao", commands.lines[0])

    def test_loi_torchao_vi_ly_do_khac_thi_khong_go(self):
        """Chỉ gỡ khi lỗi NÓI VỀ torchao; lỗi khác của peft thì để nguyên cho người đọc thấy."""
        log = Recorder()

        def other_error():
            raise ImportError("No module named 'peft'")

        result = bootstrap.install_packages(
            "visobert/lora/exp001", colab=True, run=fake_run(Recorder()), spec=fake_spec(),
            load=lambda *parts: {"config": {"enabled": True}}, torchao=other_error, log=log)
        self.assertFalse(result["torchao_removed"])
        self.assertNotIn("đang gỡ torchao", log.text())


class VerifyCheckoutTest(EnvCase):
    """`verify_checkout`: lệch sha là DỪNG, và câu in phải nói rõ đang chạy bản code nào.

    `repo.prepare` được vá ở đây vì nó gọi git thật (đã có test riêng ở `tests/test_repo.py`);
    phần được kiểm ở đây là CÂU IN và cách xử lý cảnh báo.
    """

    SHA = "a" * 40

    @staticmethod
    def result(action="checkout tách rời", warnings=()):
        return {"action": action, "dir": "/content/SentimentX", "warnings": list(warnings)}

    def test_in_ban_code_dang_chay_va_canh_bao(self):
        log = Recorder()
        with mock.patch.object(bootstrap.repo, "prepare",
                               return_value=self.result(warnings=["commit chưa nằm trên nhánh"])):
            bootstrap.verify_checkout("https://ví-dụ", self.SHA, "experiment",
                                      "/content/SentimentX", colab=False, log=log)
        text = log.text()
        self.assertIn("Code        : checkout tách rời | /content/SentimentX | aaaaaaaa", text)
        self.assertIn("cảnh báo: commit chưa nằm trên nhánh", text)
        self.assertIn("checkout tách rời)", text)

    def test_dung_ban_code_dang_co_thi_khong_them_loi_canh_bao(self):
        """Máy cá nhân đang đúng commit: chỉ in ra, không thêm lời cảnh báo nào."""
        log = Recorder()
        with mock.patch.object(bootstrap.repo, "prepare",
                               return_value=self.result(action="dùng bản code đang có")):
            bootstrap.verify_checkout("https://ví-dụ", self.SHA, "experiment",
                                      "/content/SentimentX", colab=False, log=log)
        self.assertEqual(log.text(),
                         "Code        : dùng bản code đang có | /content/SentimentX | aaaaaaaa")


class ModelAssetsTest(EnvCase):
    """`model_assets`: chỉ tải model VnCoreNLP khi thí nghiệm THẬT SỰ cần bộ tách từ đó."""

    EXPERIMENT = "phobert-base-v2/lora/exp001"

    def preprocess(self, segmenter):
        return mock.patch.object(bootstrap.model_config, "preprocess",
                                 return_value={"segmenter": segmenter})

    def with_data_root(self):
        holder = tempfile.TemporaryDirectory()
        patcher = mock.patch.dict(os.environ, {bootstrap.paths.ENV_DATA_ROOT: holder.name})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(holder.cleanup)
        return Path(holder.name)

    def test_o_may_ca_nhan_thi_khong_tai_gi(self):
        log = Recorder()
        download = fake_download()
        result = bootstrap.model_assets(self.EXPERIMENT, colab=False, download=download, log=log)
        self.assertEqual(download.calls, [])
        self.assertEqual(log.lines, [])
        self.assertEqual(result["downloaded"], [])

    def test_bo_tach_tu_khac_vncorenlp_thi_khong_tai_gi(self):
        """Qwen3 và ViSoBERT đọc văn bản nguyên bản: tải 27 MB về là vô ích."""
        log = Recorder()
        download = fake_download()
        with self.preprocess("none"):
            result = bootstrap.model_assets(self.EXPERIMENT, colab=True, download=download, log=log)
        self.assertEqual(result["segmenter"], "none")
        self.assertEqual(download.calls, [])
        self.assertEqual(log.lines, [])

    def test_tai_model_khi_thieu_java_goi_va_file(self):
        log = Recorder()
        commands = Recorder()
        download = fake_download()
        self.with_data_root()
        with self.preprocess("vncorenlp"):
            result = bootstrap.model_assets(self.EXPERIMENT, colab=True, which=lambda name: None,
                                            run=fake_run(commands),
                                            spec=fake_spec(missing=("py_vncorenlp",)),
                                            download=download, log=log)
        text = log.text()
        self.assertIn("Thiếu Java cho bộ tách từ vncorenlp - đang cài default-jdk...", text)
        self.assertIn("  apt-get -> 0", text)
        self.assertIn("Thiếu gói py-vncorenlp - đang cài...", text)
        self.assertIn("Thiếu model VnCoreNLP trong", text)
        self.assertIn("(~27 MB)", text)
        self.assertIn("(có)", text)
        self.assertEqual(len(result["downloaded"]), 3)
        self.assertEqual(len(result["present"]), 3)

    def test_java_co_san_thi_dat_java_home_tu_duong_dan_cua_no(self):
        """pyjnius tìm JVM qua JAVA_HOME/JDK_HOME, không qua lệnh `java`."""
        log = Recorder()
        self.with_data_root()
        with self.preprocess("vncorenlp"):
            bootstrap.model_assets(self.EXPERIMENT, colab=True,
                                   which=lambda name: "/usr/lib/jvm/java-17/bin/javac",
                                   run=fake_run(Recorder()), spec=fake_spec(),
                                   download=fake_download(), log=log)
        line = [item for item in log.lines if "JAVA_HOME" in item][0]
        self.assertTrue(line.endswith("java-17"), line)
        self.assertNotIn("Thiếu Java", log.text())

    def test_file_tai_ve_qua_nho_thi_xoa_va_bao_thieu(self):
        """Mạng trả về một trang HTML vài KB: phải xoá và nói THIẾU, đừng tưởng là xong."""
        log = Recorder()
        self.with_data_root()
        with self.preprocess("vncorenlp"):
            result = bootstrap.model_assets(self.EXPERIMENT, colab=True,
                                            which=lambda name: "/usr/bin/javac",
                                            run=fake_run(Recorder()), spec=fake_spec(),
                                            download=fake_download(tiny=True), log=log)
        self.assertIn("quá nhỏ (đã xoá); thử lại sau", log.text())
        self.assertIn("THIẾU - chép data/models/vncorenlp", log.text())
        self.assertEqual(result["present"], [])
        self.assertEqual(result["downloaded"], [])

    def test_da_co_du_file_thi_khong_tai_lai(self):
        log = Recorder()
        download = fake_download()
        root = self.with_data_root()
        assets = root / "models" / "vncorenlp"
        for name, minimum in bootstrap.VNCORENLP_FILES:
            path = assets / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"x" * (minimum + 1))
        with self.preprocess("vncorenlp"):
            result = bootstrap.model_assets(self.EXPERIMENT, colab=True,
                                            which=lambda name: "/usr/bin/javac",
                                            run=fake_run(Recorder()), spec=fake_spec(),
                                            download=download, log=log)
        self.assertEqual(download.calls, [])
        self.assertIn("(có)", log.text())
        self.assertEqual(len(result["present"]), 3)


if __name__ == "__main__":
    unittest.main()



