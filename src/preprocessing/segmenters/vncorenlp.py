# -*- coding: utf-8 -*-
"""Tách từ bằng RDRSegmenter trong VnCoreNLP - bộ CHÍNH CHỦ của PhoBERT.

Vì sao đây là bộ mặc định: PhoBERT được tiền huấn luyện trên văn bản đã tách từ bằng
chính RDRSegmenter của VnCoreNLP (VinAI ghi rõ trong README của PhoBERT), nên dùng
đúng bộ đó là cách duy nhất không tạo thêm khác biệt so với thiết kế gốc của model.

CẦN JAVA - VÀ CÁCH DÒ JAVA
---
Gói `py-vncorenlp` gọi model Java qua **pyjnius (JNI)**, không phải qua lệnh `java`.
Trên Windows, pyjnius chỉ tìm JVM ở hai biến môi trường `JDK_HOME` rồi `JAVA_HOME`,
không thấy thì ném `Exception("Unable to find JAVA_HOME")` - một lỗi chung chung, dễ
làm sập cả tiến trình đo. Vì vậy module này kiểm tra Java TRƯỚC và báo lỗi kèm đúng
lệnh cần chạy (xem `_java_home()`), nhờ đó model thiếu Java chỉ bị BỎ QUA kèm lí do
rõ ràng chứ không làm hỏng phép đo của các model khác.

`py_vncorenlp.download_model()` KHÔNG dùng được trên Windows: nó gọi `wget` qua
`os.system`. Trên Windows phải tải jar + model bằng PowerShell - xem
`scripts/setup_vncorenlp.ps1`.
"""

import os
import re
import subprocess
from pathlib import Path

from src import config

NAME = "vncorenlp"
OFFICIAL = True
DESCRIPTION = (
    "RDRSegmenter trong VnCoreNLP - bộ tách từ CHÍNH CHỦ của PhoBERT "
    "(VinAI dùng chính nó khi tiền huấn luyện). Cần Java 1.8+"
)

# py-vncorenlp 0.1.4 cứng tên jar này (xem mã nguồn gói): đổi tên file là nó báo
# "Please download the VnCoreNLP model!".
JAR_NAME = "VnCoreNLP-1.2.jar"
# Chỉ cần model của phần tách từ; pos/ner/parse không tải (nặng mà không dùng).
MODEL_FILES = (
    "models/wordsegmenter/vi-vocab",
    "models/wordsegmenter/wordsegmenter.rdr",
)
# Bộ nhớ cấp cho JVM. RDRSegmenter rất nhẹ nên 1g là thừa sức (gói mặc định 2g).
MAX_HEAP_SIZE = "-Xmx1g"

# ---
# Dấu '_' ở ĐẦU câu: dấu hiệu "nối tiếp từ trước" khi không có từ nào trước
# ---
# Quy ước output của VnCoreNLP (hàm segmentTokenizedString trong WordSegmenter.java):
#     âm tiết MỞ ĐẦU một từ  -> in ra sau MỘT KHOẢNG TRẮNG   (" " + form)
#     âm tiết NỐI TIẾP      -> in ra sau dấu "_"            ("_" + form)
# Vì vậy "Đại_học" nghĩa là "học" nối tiếp "Đại".
#
# Nhưng khi chạy trên MỘT CÂU riêng lẻ, từ đầu tiên đôi khi bị gán nhãn "nối tiếp"
# dù không có từ nào trước nó, sinh ra output như "_Son" (đo trên 3.000 review
# cosmetics: 711 review có hiện tượng này - 23.7%). Dấu "_" đó không mang thông tin
# gì: nó không nối với từ nào cả, chỉ khiến tokenizer nhìn thấy một ký tự mà văn bản
# gốc không có.
#
# Vì vậy mặc định BỎ dấu "_" vô nghĩa ở đầu câu. Đặt False nếu muốn giữ nguyên output
# thô của công cụ (số liệu khi đó KHÔNG so sánh ngang được với bản mặc định).
STRIP_LEADING_BOUNDARY = True

# Chỉ bỏ khi dấu "_" đứng đầu chuỗi / sau khoảng trắng VÀ dính liền với một chữ.
# Nhờ điều kiện thứ hai, dấu "_" do NGƯỜI VIẾT tự gõ được giữ nguyên: họ luôn gõ nó
# đứng riêng ("^ _ ^", "đẹp _ rẻ _ xịn", "?__?_"), và đó là dữ liệu không được sửa.
# Kiểm chứng trên 3.000 review cosmetics: 0 review có dấu "_" dính liền chữ do người
# viết gõ, nên quy tắc này không đụng tới dữ liệu người dùng.
_BOUNDARY_RE = re.compile(r"(^|\s)_(?=\w)")

MODEL_DIR = config.MODEL_ASSETS_DIR / "vncorenlp"

# Nơi scripts/setup_java.ps1 cài JDK (cài trong thư mục người dùng, không cần admin)
USER_JDK_DIR = Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".jdks"

# Vài nơi JDK hay được cài trên Windows (winget / choco / bản tải tay)
JDK_SEARCH_DIRS = (
    USER_JDK_DIR,
    Path("C:/Program Files/Eclipse Adoptium"),
    Path("C:/Program Files/Java"),
    Path("C:/Program Files/Microsoft"),
    Path("C:/Program Files/Amazon Corretto"),
    Path("C:/Program Files/Zulu"),
    Path(os.environ.get("LOCALAPPDATA", "C:/")) / "Programs" / "Eclipse Adoptium",
)

INSTALL_HINT = (
    "Bộ tách từ chính chủ của PhoBERT cần 2 thứ: JAVA (JDK/JRE 1.8+) và model VnCoreNLP.\n"
    "Cài trên Windows (không cần quyền admin, cài trong thư mục người dùng):\n"
    "    powershell -ExecutionPolicy Bypass -File scripts\\setup_java.ps1\n"
    "    powershell -ExecutionPolicy Bypass -File scripts\\setup_vncorenlp.ps1\n"
    "Hoặc cài tay:\n"
    "    winget install EclipseAdoptium.Temurin.17.JDK   (nhớ đặt JAVA_HOME)\n"
    "    pip install py-vncorenlp\n"
    "    (tải VnCoreNLP-1.2.jar + models/wordsegmenter vào {})\n"
    "Trong lúc chưa có Java, có thể tạm chạy bằng: --segmenter pyvi".format(
        MODEL_DIR.as_posix())
)

_RDR = None


# ---
# Dò Java
# ---


def _jdk_candidates():
    """Các thư mục có thể chứa JDK/JRE, theo thứ tự ưu tiên."""
    for variable in ("JDK_HOME", "JAVA_HOME"):
        value = os.environ.get(variable)
        if value:
            yield Path(value)
    for base in JDK_SEARCH_DIRS:
        if not base.is_dir():
            continue
        if (base / "bin").is_dir():
            yield base
        for child in sorted(base.iterdir()):
            if child.is_dir() and (child / "bin").is_dir():
                yield child


def _java_home():
    """Thư mục JDK/JRE dùng được, hoặc None nếu máy chưa cài Java.

    Điều kiện "dùng được" là có `bin/server/jvm.dll` (Windows) hoặc `bin/java`
    (Linux/macOS) - pyjnius cần đúng thư viện này, không chỉ cần lệnh `java`.
    """
    for candidate in _jdk_candidates():
        if (candidate / "bin" / "server" / "jvm.dll").exists():
            return candidate
        if (candidate / "bin" / "java").exists():
            return candidate
    return None


def _ensure_java():
    """Đặt JAVA_HOME/JDK_HOME cho tiến trình hiện tại. Trả về thư mục JDK.

    Việc đặt biến Ở ĐÂY (không chỉ trong shell) là có chủ ý: script cài đặt đặt
    JAVA_HOME ở mức người dùng, nhưng terminal đang mở chưa thấy biến đó. Tự đặt
    trong tiến trình giúp chạy được ngay, không phải mở lại terminal.
    """
    home = _java_home()
    if home is None:
        raise FileNotFoundError(
            "Không tìm thấy Java (JDK/JRE 1.8+) trên máy này.\n" + INSTALL_HINT
        )
    for variable in ("JDK_HOME", "JAVA_HOME"):
        os.environ.setdefault(variable, str(home))
    return home


def _java_version(home):
    """Chuỗi phiên bản Java, ví dụ 'openjdk version "17.0.12"'. None nếu không gọi được."""
    for name in ("java.exe", "java"):
        binary = home / "bin" / name
        if not binary.exists():
            continue
        try:
            result = subprocess.run(
                [str(binary), "-version"], capture_output=True, text=True,
                timeout=60, check=False,
            )
        except (OSError, subprocess.SubprocessError):  # pragma: no cover
            return None
        text = (result.stderr or result.stdout or "").strip()
        return text.splitlines()[0].strip() if text else None
    return None


# ---
# Dò model VnCoreNLP
# ---


def missing_files():
    """Danh sách file jar/model còn thiếu trong data/models/vncorenlp/."""
    required = [MODEL_DIR / JAR_NAME]
    required += [MODEL_DIR / item for item in MODEL_FILES]
    return [path for path in required if not path.exists()]


def _require_model():
    """Báo lỗi rõ ràng nếu chưa tải model VnCoreNLP."""
    missing = missing_files()
    if missing:
        raise FileNotFoundError(
            "Chưa có model VnCoreNLP trong {} (thiếu {}).\n{}".format(
                MODEL_DIR.as_posix(),
                ", ".join(path.name for path in missing), INSTALL_HINT)
        )


# ---
# Nạp và dùng
# ---


def _rdr():
    """Nạp RDRSegmenter một lần duy nhất cho cả tiến trình."""
    global _RDR
    if _RDR is not None:
        return _RDR

    _ensure_java()
    _require_model()

    try:
        import py_vncorenlp
    except ImportError as exc:  # pragma: no cover - phụ thuộc môi trường
        raise ImportError(
            "Thiếu thư viện py-vncorenlp. Cài bằng:\n"
            "    pip install py-vncorenlp\n" + INSTALL_HINT
        ) from exc

    # py_vncorenlp tự `os.chdir` vào thư mục model (tác dụng phụ ngoài mong muốn),
    # nên đưa về thư mục cũ ngay sau khi nạp xong.
    previous = os.getcwd()
    try:
        _RDR = py_vncorenlp.VnCoreNLP(
            annotators=["wseg"],
            max_heap_size=MAX_HEAP_SIZE,
            save_dir=MODEL_DIR.as_posix(),
        )
    except Exception as exc:  # noqa: BLE001 - pyjnius ném Exception trần
        # Lỗi ở bước này hầu như luôn là môi trường (JVM không khởi động được, jar
        # hỏng, Java sai kiến trúc). Đổi thành OSError để nơi gọi BỎ QUA model này
        # kèm lí do, thay vì làm sập cả phép đo.
        raise OSError(
            "Không khởi động được RDRSegmenter/VnCoreNLP ({}: {}).\n{}".format(
                type(exc).__name__, str(exc).splitlines()[0] if str(exc) else "",
                INSTALL_HINT)
        ) from exc
    finally:
        os.chdir(previous)
    return _RDR


def available():
    """Java + model + thư viện đã sẵn sàng chưa (KHÔNG khởi động JVM)."""
    if _java_home() is None:
        return False, "chưa cài Java (JDK/JRE 1.8+); chạy scripts/setup_java.ps1"
    try:
        import py_vncorenlp  # noqa: F401
    except ImportError:
        return False, "thiếu thư viện py-vncorenlp; cài bằng 'pip install py-vncorenlp'"
    missing = missing_files()
    if missing:
        return False, "thiếu model VnCoreNLP ({}); chạy scripts/setup_vncorenlp.ps1".format(
            ", ".join(path.name for path in missing))
    return True, ""


def info():
    """Thông tin bộ tách từ, kèm bản Java đang dùng (để truy vết khi số liệu lệch)."""
    home = _java_home()
    return {
        "segmenter": NAME,
        "package": "py-vncorenlp",
        "version": _version("py-vncorenlp"),
        "official": OFFICIAL,
        "java_home": str(home) if home else None,
        "java_version": _java_version(home) if home else None,
        "model_dir": MODEL_DIR.as_posix(),
        # Có bỏ dấu '_' vô nghĩa ở đầu câu hay không - đây là một bước XỬ LÝ của dự án
        # (không phải của VnCoreNLP), nên phải ghi lại cùng số liệu.
        "strip_leading_boundary": STRIP_LEADING_BOUNDARY,
    }


def segment(text):
    """Tách từ; py_vncorenlp trả về danh sách CÂU nên phải nối lại thành chuỗi."""
    result = " ".join(_rdr().word_segment(text))
    if STRIP_LEADING_BOUNDARY:
        # Xem giải thích ở _BOUNDARY_RE: bỏ dấu "_" không nối với từ nào.
        result = _BOUNDARY_RE.sub(r"\1", result)
    return result


def _version(package):
    """Phiên bản gói đang cài, để ghi vào số liệu truy vết."""
    try:
        from importlib.metadata import PackageNotFoundError, version
    except ImportError:  # pragma: no cover - Python cũ
        return None
    try:
        return version(package)
    except PackageNotFoundError:
        return None
