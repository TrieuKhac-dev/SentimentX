# -*- coding: utf-8 -*-
"""Việc chuẩn bị môi trường chạy notebook, gom từ ô bootstrap vào thư viện.

VÌ SAO Ở ĐÂY MÀ KHÔNG Ở TRONG Ô NOTEBOOK
Ô bootstrap từng dài 317 dòng. Mọi thứ SAU khi đã có mã nguồn - mount Drive, dò thư mục nhóm, nạp
biến môi trường, đặt hai gốc đường dẫn, cài gói còn thiếu, kiểm lại commit đã ghim, tải tài nguyên
model - đều là LOGIC. Logic nằm trong ô notebook thì mỗi lần sửa phải sửa ở MỌI notebook, mà
notebook đã ghim thì không được sửa nữa. Nay logic ở đây; ô notebook chỉ còn phần BẮT BUỘC phải ở
đó: kéo mã nguồn (trên máy mới `src/` chưa tồn tại, nên không thể gọi thư viện để kéo chính nó) rồi
gọi bốn hàm dưới đây theo đúng thứ tự cũ.

CÂU IN GIỮ NGUYÊN TỪNG CHỮ so với bản cũ: `run.log` của những lượt đã chạy, bảng "Notebook tự làm
gì" trong `docs/00_workflow/07_colab.md`, và cách người đọc dò lỗi đều dựa vào chúng.

MỌI HÀM NHẬN `log` (mặc định `print`) VÀ CÁC ĐIỂM TIÊM (`mount`, `run`, `which`, `download`):
máy cá nhân không có Colab, nên nhánh chỉ-làm-trên-Colab mà không tiêm được thì không bao giờ được
kiểm. Test nằm ở `tests/workflow/test_bootstrap.py`.

CHÍNH SÁCH DỪNG Ở LẠI NƠI GỌI: `prepare()` không ném `SystemExit` khi thiếu thư mục nhóm - nó TRẢ
`stop` (câu thông báo) để ô notebook quyết định dừng. Thư viện không được tự giết kernel.
"""

import importlib.util
import os
import pathlib
import shutil
import subprocess
import sys
import urllib.request

from src.experiments import experiments, model_config
from src.core import paths
from src.workflow import repo, runtime

# Gói mà một lượt chạy cần. `peft` chỉ cho đường HUẤN LUYỆN (LoRA); `mlflow` thì luôn cần: thiếu nó,
# phần ghi nhận tự hạ cấp và lượt chạy KHÔNG lên DagsHub (đã gặp thật ở cả ba lượt chạy đầu).
# `plotly` + `jinja2` để vẽ BIỂU ĐỒ train/val (`plots/training.html`) - thiếu thì chỉ mất biểu đồ
# (hàm vẽ là best-effort), nhưng cài sẵn để lượt chạy có đủ thứ người đọc cần.
WANTED_PACKAGES = ("transformers", "accelerate", "bitsandbytes", "mlflow", "plotly", "jinja2")
TRAINING_PACKAGES = ("peft",)

# Ba file của model VnCoreNLP, kèm kích thước TỐI THIỂU để phát hiện trường hợp mạng trả về một trang
# HTML vài KB rồi tưởng là xong. Đúng bằng `scripts/setup/setup_vncorenlp.ps1` tải trên Windows.
VNCORENLP_FILES = (("VnCoreNLP-1.2.jar", 10 * 1024 * 1024),
                   ("models/wordsegmenter/vi-vocab", 100 * 1024),
                   ("models/wordsegmenter/wordsegmenter.rdr", 50 * 1024))
VNCORENLP_BASE = "https://raw.githubusercontent.com/vncorenlp/VnCoreNLP/master"


def prepare(colab=None, mount=None, log=print):
    """Mount Drive (nếu ở Colab), tìm thư mục nhóm, nạp env, đặt hai gốc đường dẫn.

    Trả về `{"colab", "drive", "env", "stop"}`. `stop` khác None nghĩa là nơi gọi PHẢI dừng (kèm lý
    do in ra) - thư viện không tự `SystemExit`.
    """
    colab = runtime.is_colab() if colab is None else bool(colab)
    if colab and not pathlib.Path("/content/drive").is_mount():
        try:
            if mount is None:
                from google.colab import drive as colab_drive  # type: ignore
                mount = colab_drive.mount
            log("Chưa mount Drive - đang mount (Colab hỏi quyền, bấm Allow)...")
            mount("/content/drive")
        except Exception as exc:  # noqa: BLE001 - thiếu quyền/mạng thì báo, không làm chết notebook
            log("  không mount được Drive ({}).".format(exc))

    drive = runtime.drive_dir() if colab else None
    if colab and drive is None:
        # `drive.mount()` trả về NGAY khi Drive được gắn, nhưng danh sách thư mục của Drive (FUSE) có
        # thể chưa đủ ngay lập tức: một phiên chạy thật đã có cảnh notebook này thấy thư mục nhóm còn
        # notebook kia thì không. Kết luận sớm là lượt chạy rơi vào máy ảo, nên chờ rồi thử lại.
        log("Chưa thấy thư mục nhóm - chờ Drive liệt kê xong rồi thử lại (tối đa 30 giây)...")
        drive = runtime.drive_dir(attempts=10, delay=3)
        log("  " + ("đã thấy: {}".format(drive) if drive else "vẫn chưa thấy."))
    if colab and drive is not None and not (drive / runtime.folder_marker()).exists():
        # Nhận ra thư mục nhóm bằng CẤU TRÚC GÓI thay vì file đánh dấu. Không phải lỗi: tên file bắt
        # đầu bằng dấu chấm nên web Drive không tạo được, và người chia sẻ thư mục có thể chỉ share.
        log("  (nhận ra thư mục nhóm bằng CẤU TRÚC GÓI: không có file đánh dấu {} - không sao, "
            "nhưng".format(runtime.folder_marker()))
        log("   nếu tạo được file đó (mục 3 của docs/00_workflow/07_colab.md) thì lần sau chắc chắn "
            "hơn.)")

    if colab and drive is None:
        # Không nhận ra thư mục nhóm: in ra những gì ĐANG THẤY - từng gốc một, kèm lối tắt - rồi mới
        # nói cách sửa. Dòng danh sách là bằng chứng để người đọc biết máy đang nhìn vào đâu.
        for item in runtime.drive_listing():
            if item["gone"]:
                log("  CHƯA thấy gốc Drive: {}".format(item["root"]))
            else:
                log("  {}: {}".format(item["root"],
                                      ", ".join(item["names"]) or "không có thư mục nào"))
            if item["shortcuts"]:
                log("    lối tắt (shortcut) đang trỏ tới: {}".format(", ".join(item["shortcuts"])))
        log("  Không thấy thư mục nào có dấu hiệu của thư mục nhóm. Ba nguyên nhân hay gặp:")
        log("   a) Phiên này dùng Drive của MỘT TÀI KHOẢN GOOGLE KHÁC (thư mục nhóm nằm ở tài khoản")
        log("      đã chạy được lượt trước): Runtime > Disconnect and delete runtime, rồi Run all và")
        log("      chọn đúng tài khoản khi Colab hỏi.")
        log("   b) Thư mục nhóm do NGƯỜI KHÁC chia sẻ (A chia sẻ cho b/c/d): mỗi người phải bấm")
        log("      'Add shortcut to My Drive' MỘT lần (chuột phải thư mục > Organize > Add shortcut),")
        log("      rồi chạy lại ô này. Được chia sẻ thôi thì Drive của mình vẫn KHÔNG chứa thư mục đó.")
        log("   c) Thư mục nhóm nằm trong SHARED DRIVE (Google Workspace) mà tài khoản này chưa được")
        log("      chia sẻ - gốc 'Shareddrives' ở trên rỗng. Cần được chia sẻ quyền, và quyền phải ĐỦ")
        log("      GHI vì kết quả chạy ghi vào chính thư mục đó.")
        log("  Hoặc chỉ định thẳng đường dẫn: bỏ chú thích SENTIMENTX_DATA_ROOT và")
        log("  SENTIMENTX_RESULTS_ROOT trong env/.env.colab (mục 2 của docs/00_workflow/07_colab.md).")



    # Thứ tự: `env/.env.colab` (nếu có) nạp trước, rồi hai gốc suy từ thư mục Drive tìm được - nên một
    # lượt chạy bình thường KHÔNG cần tạo file env nào.
    env = runtime.load_env(colab_env_file=(runtime.drive_env_file() if drive else None))
    if drive:
        os.environ.setdefault("SENTIMENTX_DATA_ROOT", str(drive / "data"))
        os.environ.setdefault("SENTIMENTX_RESULTS_ROOT", str(drive / "experiments"))

    log("Nơi chạy    : {}".format(runtime.env_name()))
    stop = None
    if colab:
        if drive:
            log("Drive       : {} (nhận ra bằng file đánh dấu)".format(drive))
        else:
            log("Drive       : CHƯA thấy - dữ liệu và kết quả sẽ nằm trong máy ảo và MẤT khi hết "
                "phiên.")
            log("              Cách sửa: đưa thư mục của nhóm (có file .sentimentx_root) lên Drive "
                "rồi chạy lại ô này.")
            if not os.environ.get("SENTIMENTX_DATA_ROOT", "").strip():
                # Không có thư mục nhóm thì máy ảo KHÔNG có dữ liệu gốc, và kết quả cũng ghi vào chỗ
                # mất khi hết phiên. Dừng ở đây rẻ hơn nhiều so với chạy tiếp rồi chết ở ô cấu hình
                # (hoặc sau khi đã tải model). Đã gặp thật: nhiều lượt chạy rơi vào máy ảo.
                log("")
                log("DỪNG: chưa thấy thư mục nhóm trên Drive, nên không có dữ liệu gốc để chạy.")
                log("  1. Thư mục nhóm phải có file đánh dấu .sentimentx_root - xem")
                log("     docs/00_workflow/07_colab.md mục 3 (tạo file đó bằng code, web Drive không "
                    "tạo được).")
                log("  2. Runtime > Restart session, rồi Run all lại TỪ ĐẦU và bấm Allow khi Colab hỏi")
                log("     quyền truy cập Drive.")
                log("  3. Nếu bạn cố ý để dữ liệu trong máy ảo: khai SENTIMENTX_DATA_ROOT trong")
                log("     env/.env.colab thì ô này sẽ không dừng nữa.")
                stop = "DỪNG: chưa thấy thư mục nhóm trên Drive (xem 3 việc ở trên)."
    log("Gốc dữ liệu : {}".format(paths.data_root()))
    log("Gốc kết quả : {}".format(paths.results_root()))
    log("Biến bắt buộc: có {} | thiếu {}".format(
        ", ".join(env["found"]) or "không có", ", ".join(env["missing"]) or "không thiếu"))
    return {"colab": colab, "drive": drive, "env": env, "stop": stop}


def _torchao_check():
    """Hỏi thẳng `peft` xem nó có dùng được `torchao` của máy ảo không.

    Hỏi thay vì tự so phiên bản: ngưỡng của peft là việc của peft.
    """
    from peft.import_utils import is_torchao_available
    is_torchao_available()


# Gói cài thêm khi lượt chạy khai bộ tách từ KHÁC mặc định của model (`preprocess.segmenter`).
# Bộ chính chủ (`vncorenlp`) không nằm ở đây vì nó còn cần JDK + model Java ~27 MB - có đường
# riêng ở `model_assets()`. Thiếu hai gói này thì lượt chạy dừng ngay ở bước chia văn bản.
SEGMENTER_PACKAGES = {"pyvi": "pyvi", "underthesea": "underthesea"}


def install_packages(experiment, colab=None, run=None, spec=None, load=None, torchao=None,
                     log=print):
    """Cài gói mà lượt chạy cần nhưng máy ảo CHƯA có. Chỉ làm trên Colab.

    `peft` chỉ cài cho đường HUẤN LUYỆN. Việc gỡ `torchao` cũng chỉ để cứu `peft`: nó gọi
    `is_torchao_available()` khi bọc LoRA, mà hàm đó NÉM ImportError khi máy có `torchao` cũ hơn mức
    nó cần (Colab hay có sẵn 0.10.0, peft đòi >= 0.16.0) - đúng lỗi đã làm chết lượt chạy LoRA đầu
    tiên. LoRA của dự án KHÔNG dùng torchao, nên gỡ nó nhẹ hơn nâng cấp và không đụng bản torch của
    máy ảo. Hỏi thẳng `peft` thay vì tự so phiên bản, để khỏi chép lại ngưỡng của nó.
    """
    colab = runtime.is_colab() if colab is None else bool(colab)
    run = subprocess.run if run is None else run
    spec = importlib.util.find_spec if spec is None else spec
    load = experiments.load if load is None else load
    torchao = _torchao_check if torchao is None else torchao
    result = {"colab": colab, "needs_training": False, "missing": [], "installed": [],
              "torchao_removed": False, "segmenter": ""}
    if not colab:
        return result
    try:
        merged = load(*[part for part in experiment.replace("\\", "/").split("/") if part])
        config = merged.get("config") or {}
        result["needs_training"] = bool(config.get("enabled")) or \
            config.get("approach") == "encoder"
        # Bộ tách từ ĐANG DÙNG của lượt chạy. Đọc từ cấu hình ĐÃ HỢP NHẤT, nên lượt nào đè
        # `preprocess.segmenter` thì ở đây đọc đúng giá trị đè - xem docs/05_config/04_models.md.
        result["segmenter"] = str(((config.get("preprocess") or {}).get("segmenter")) or "").strip()
    except Exception as exc:  # noqa: BLE001 - đọc config hỏng thì coi như đường prompt
        log("  (chưa biết thí nghiệm này có huấn luyện không: {})".format(exc))
    wanted = list(WANTED_PACKAGES) + (list(TRAINING_PACKAGES) if result["needs_training"] else [])
    extra = SEGMENTER_PACKAGES.get(result["segmenter"])
    if extra:
        wanted.append(extra)
    result["missing"] = [name for name in wanted if spec(name) is None]
    if result["missing"]:
        log("Thiếu gói {} - đang cài...".format(", ".join(result["missing"])))
        done = run([sys.executable, "-m", "pip", "install", "-q"] + result["missing"],
                   capture_output=True, text=True)
        log("  pip install -> {}".format(done.returncode))
        if done.returncode != 0:
            log("  " + ((done.stdout or "") + (done.stderr or "")).strip()[-400:])
        else:
            result["installed"] = list(result["missing"])
    if result["needs_training"] and spec("peft") is not None:
        try:
            torchao()
        except ImportError as exc:
            if "torchao" in str(exc):
                log("peft không dùng được torchao của máy ảo: {}".format(str(exc).splitlines()[0]))
                log("  đang gỡ torchao (LoRA của dự án không dùng gói này)...")
                removed = run([sys.executable, "-m", "pip", "uninstall", "-y", "-q", "torchao"],
                              capture_output=True, text=True)
                # Gói đã nạp vào bộ nhớ kernel thì `find_spec` vẫn thấy nó -> phải quên đi.
                sys.modules.pop("torchao", None)
                log("  pip uninstall -> {}".format(removed.returncode))
                result["torchao_removed"] = True
    return result


def verify_checkout(url, sha, branch, dest, colab=None, log=print):
    """Kiểm lại bằng thư viện: lệch sha là DỪNG, chứ không chạy trên bản code không rõ là bản nào."""
    colab = runtime.is_colab() if colab is None else bool(colab)
    code = repo.prepare(url, sha, branch=branch, dest=dest, require_branch=True)
    log("Code        : {} | {} | {}".format(code["action"], code["dir"], sha[:8]))
    if not colab and code["action"] != "dùng bản code đang có":
        log("  cảnh báo: thư mục code vừa được đưa về commit đã ghim (checkout tách rời). Máy cá "
            "nhân nên chạy notebook khi không có việc đang làm dở trong repo này.")
    for warning in code["warnings"]:
        log("  cảnh báo: {}".format(warning))
    return code


def model_assets(experiment, colab=None, which=None, run=None, spec=None, download=None,
                 load=None, log=print):
    """Tài nguyên của model mà git KHÔNG chứa (model VnCoreNLP ~27 MB), chỉ khi thí nghiệm cần.

    Bộ tách từ chính chủ của PhoBERT (`vncorenlp`) gọi model Java qua JNI, nên cần JDK + gói
    `py-vncorenlp`. Chỉ làm cho thí nghiệm THẬT SỰ dùng nó: Qwen3 và ViSoBERT đọc văn bản nguyên bản.

    Bộ tách từ được đọc từ cấu hình ĐÃ HỢP NHẤT chứ không phải từ file model: lớp thí nghiệm ĐÈ được
    khoá `preprocess.segmenter`, nên lượt khai `pyvi` mà vẫn tải 27 MB model Java là vô ích, còn lượt
    khai `vncorenlp` cho một model không khai gì thì lại THIẾU đúng thứ nó cần - mà lỗi đó chỉ hiện ra
    muộn, sau khi đã tải trọng số. Đọc config hỏng thì quay về giá trị của file model (hành vi cũ).

    `shutil.which` chứ không gọi thẳng `java -version`: máy chưa có Java thì lệnh đó ném
    FileNotFoundError, và ô này chết TRƯỚC khi kịp cài.
    """
    colab = runtime.is_colab() if colab is None else bool(colab)
    which = shutil.which if which is None else which
    run = subprocess.run if run is None else run
    spec = importlib.util.find_spec if spec is None else spec
    download = urllib.request.urlretrieve if download is None else download
    load = experiments.load if load is None else load
    result = {"colab": colab, "segmenter": "", "present": [], "downloaded": []}
    if not colab:
        return result
    model_id = experiment.replace("\\", "/").split("/")[0]
    result["segmenter"] = str((model_config.preprocess(model_id) or {}).get("segmenter") or "")
    try:
        merged = load(*[part for part in experiment.replace("\\", "/").split("/") if part])
        found = ((merged.get("config") or {}).get("preprocess") or {}).get("segmenter")
        if found:
            result["segmenter"] = str(found).strip()
    except Exception as exc:  # noqa: BLE001 - đọc config hỏng thì dùng giá trị của file model
        log("  (chưa đọc được bộ tách từ của lượt chạy: {})".format(exc))
    if result["segmenter"] != "vncorenlp":
        return result
    if which("javac") is None and which("java") is None:
        log("Thiếu Java cho bộ tách từ vncorenlp - đang cài default-jdk...")
        jdk = run(["apt-get", "install", "-y", "-q", "default-jdk"], capture_output=True, text=True)
        log("  apt-get -> {}".format(jdk.returncode))
    binary = which("javac") or which("java")
    if binary:
        # pyjnius tìm JVM qua JAVA_HOME/JDK_HOME, không qua lệnh `java`.
        home = pathlib.Path(binary).resolve().parent.parent
        os.environ.setdefault("JAVA_HOME", str(home))
        os.environ.setdefault("JDK_HOME", str(home))
        log("  JAVA_HOME -> {}".format(home))
    if spec("py_vncorenlp") is None:
        log("Thiếu gói py-vncorenlp - đang cài...")
        package = run([sys.executable, "-m", "pip", "install", "-q", "py-vncorenlp"],
                      capture_output=True, text=True)
        log("  pip install -> {}".format(package.returncode))
    assets = paths.data("models") / "vncorenlp"
    missing = [name for name, _minimum in VNCORENLP_FILES if not (assets / name).is_file()]
    if missing:
        log("Thiếu model VnCoreNLP trong {} - đang tải {} file (~27 MB)...".format(
            assets, len(missing)))
        for name, minimum in VNCORENLP_FILES:
            target = assets / name
            if target.is_file():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                download("{}/{}".format(VNCORENLP_BASE, name), target)
            except Exception as exc:  # noqa: BLE001 - mạng là việc của máy ảo
                log("  {} -> LỖI: {}".format(name, exc))
                continue
            size = target.stat().st_size
            if size < minimum:
                # Kích thước là để phát hiện mạng trả về một trang HTML vài KB rồi tưởng là xong.
                target.unlink()
                log("  {} -> chỉ {} byte, quá nhỏ (đã xoá); thử lại sau".format(name, size))
            else:
                log("  {} -> {:.1f} MB".format(name, size / 1024 / 1024))
                result["downloaded"].append(name)
    result["present"] = [name for name, _minimum in VNCORENLP_FILES if (assets / name).is_file()]
    enough = len(result["present"]) == len(VNCORENLP_FILES)
    log("  model VnCoreNLP: {} ({})".format(
        assets, "có" if enough else
        "THIẾU - chép data/models/vncorenlp từ gói bàn giao vào gốc dữ liệu rồi chạy lại"))
    return result
