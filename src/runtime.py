# -*- coding: utf-8 -*-
"""Máy đang chạy là Colab hay máy cá nhân, và nạp biến môi trường.

VÌ SAO CẦN BIẾT ĐANG Ở ĐÂU
Một số việc chỉ làm trên Colab: mount Drive, đổi gốc đường dẫn sang Drive, cài
thư viện. Trên máy cá nhân thì không làm những việc đó.

THỨ TỰ NẠP BIẾN MÔI TRƯỜNG
    1. Colab Secrets, nếu giảng viên tự đặt
    2. file `<Drive>/env/.env.colab`
    3. biến môi trường đang có
    4. file `.env` ở máy cá nhân

Giá trị nào gặp trước thì được dùng trước. Hàm trả về danh sách tên biến đã có và
còn thiếu, để notebook in ra. Không bao giờ in giá trị, vì đó là secret.
"""

import os
import sys
import time
from pathlib import Path

ENV_NAME = "SENTIMENTX_ENV"

# Biến notebook cần, dùng để kiểm và in ra khi thiếu.
REQUIRED_ON_COLAB = ("DAGSHUB_TOKEN",)
REQUIRED_ON_LOCAL = ()


def is_colab():
    """True nếu đang chạy trong Google Colab."""
    if "google.colab" in sys.modules:
        return True
    return bool(os.environ.get("COLAB_RELEASE_TAG") or os.environ.get("COLAB_GPU"))


def env_name():
    """`colab` hoặc `local`, để ghi vào log và `run_meta.json`."""
    value = os.environ.get(ENV_NAME, "").strip().lower()
    if value in ("colab", "local"):
        return value
    return "colab" if is_colab() else "local"


def load_env(colab_env_file=None):
    """Nạp biến môi trường theo thứ tự ở trên.

    `colab_env_file` là đường dẫn file env trên Drive, ví dụ
    `<Drive>/env/.env.colab`. Bỏ qua nếu không truyền.
    Trả về dict: `{"found": [...], "missing": [...], "files": [...]}`.
    """
    files = []
    if is_colab():
        for name, value in _from_colab_secrets().items():
            os.environ.setdefault(name, value)
    if colab_env_file:
        path = str(colab_env_file)
        if os.path.isfile(path):
            _apply_file(path)
            files.append(path)
    if os.path.isfile(_local_env_path()):
        _apply_file(_local_env_path())
        files.append(_local_env_path())

    required = REQUIRED_ON_COLAB if env_name() == "colab" else REQUIRED_ON_LOCAL
    found = [name for name in required if os.environ.get(name)]
    missing = [name for name in required if not os.environ.get(name)]
    return {"found": found, "missing": missing, "files": files, "env": env_name()}


def _local_env_path():
    """File `.env` ở gốc repo, không phụ thuộc thư mục đang đứng."""
    from src import paths
    return str(paths.root() / ".env")


def drive_dir(folder=None, candidates=None, attempts=1, delay=0.0):
    """Thư mục Drive của nhóm trên Colab, nhận ra bằng FILE ĐÁNH DẤU.

    Vì sao phải có file đánh dấu: MyDrive và Shared drives trông giống nhau, mà chỉ một trong hai
    là thư mục giảng viên cấp. Đoán theo tên thư mục thì notebook có thể đọc nhầm một thư mục
    cùng tên của người khác - và lúc đó nó ghi kết quả vào chỗ không ai tìm thấy.

    KHÔNG tự mount Drive: việc mount là của người chạy notebook (docs/00_workflow/01_flow.md).

    Không khớp theo tên thì TÌM một cấp trong các gốc của những đường dẫn đã khai (`MyDrive`,
    `Shareddrives`): người nhận notebook chỉ việc copy thư mục của nhóm vào Drive của mình, tên có
    thể là "SentimentX (1)" hoặc do giảng viên đặt - bắt họ khai đúng tên là bắt làm việc máy làm được.
    Vẫn nhận ra bằng `.sentimentx_root` chứ không bằng tên, nên không thể nhầm sang thư mục người khác.

    `attempts` và `delay` (giây): số lần thử và thời gian chờ giữa hai lần. Cần thiết vì
    `drive.mount()` trả về NGAY khi Drive được gắn, nhưng danh sách thư mục của Drive (FUSE) có thể
    chưa đủ ngay lập tức - đã gặp thật: cùng một phiên, notebook này thấy thư mục nhóm còn notebook
    kia thì không. Kết luận "chưa có thư mục" quá sớm là lượt chạy rơi vào máy ảo và mất kết quả.

    Trả về `Path` hoặc None (chưa mount, hoặc chưa có thư mục nào khớp).
    """
    from src import paths

    folder = folder if folder is not None else os.environ.get("SENTIMENTX_DRIVE_FOLDER", "")
    settings = paths.cfg().get("colab") or {}
    marker = str(settings.get("folder_marker") or "")
    places = list(candidates if candidates is not None
                  else settings.get("drive_candidates") or [])
    total = max(1, int(attempts))
    for attempt in range(total):
        found = _find_drive(folder, places, marker)
        if found is not None:
            return found
        if delay and attempt + 2 <= total:
            time.sleep(delay)
    return None


def _find_drive(folder, places, marker):
    """Một lượt tìm thư mục nhóm: khớp theo tên trước, rồi tìm thư mục có file đánh dấu."""
    for place in places:
        try:
            candidate = Path(str(place).format(folder=folder or ""))
        except (KeyError, IndexError, ValueError):
            continue
        if not candidate.is_dir():
            continue
        if marker and not (candidate / marker).exists():
            continue
        return candidate
    return _search_for_marker(places, marker)


def _search_for_marker(places, marker):
    """Tìm thư mục có FILE ĐÁNH DẤU trong các gốc của `places`, không cần biết tên trước.

    Quét ĐÚNG MỘT cấp: `/content/drive/MyDrive/<tên bất kỳ>/.sentimentx_root`. Nhiều thư mục cùng
    có dấu thì chọn thư mục CÓ `data/` (dấu hiệu thư mục đã được chuẩn bị để chạy), còn lại lấy theo
    thứ tự tên - để kết quả không phụ thuộc thứ tự đọc đĩa.
    """
    if not marker:
        return None
    roots = []
    for place in places:
        # Dùng `Path` chứ không cắt chuỗi theo "/": trên Windows đường dẫn dùng "\", cắt theo "/" thì
        # không ra gốc nào và phép tìm im lặng không chạy - đúng lỗi mà ba test dưới đây bắt được.
        pattern = Path(str(place))
        if "{" not in pattern.name:
            continue
        root = pattern.parent
        if root not in roots:
            roots.append(root)
    found = []
    for root in roots:
        if not root.is_dir():
            continue
        for child in sorted(root.iterdir()):
            if child.is_dir() and (child / marker).exists() and child not in found:
                found.append(child)
    if not found:
        return None
    for child in found:
        if (child / "data").is_dir():
            return child
    return found[0]



def drive_children(places=None, limit=20):
    """Các thư mục con của những gốc Drive đã khai, để IN RA khi không tìm thấy thư mục nhóm.

    Không phải để chọn thư mục - chọn thì vẫn theo FILE ĐÁNH DẤU. Đây là dữ kiện để người đọc biết máy
    đang thấy gì: thiếu file đánh dấu, hay đang thấy một thư mục khác hẳn.
    """
    from src import paths

    settings = paths.cfg().get("colab") or {}
    places = list(places if places is not None else settings.get("drive_candidates") or [])
    found = []
    for place in places:
        pattern = Path(str(place))
        if "{" not in pattern.name:
            continue
        root = pattern.parent
        if not root.is_dir():
            continue
        for child in sorted(root.iterdir()):
            if child.is_dir() and child not in found:
                found.append(child)
    return found[:limit]


def looks_like_group_dir(path):
    """Thư mục có CẤU TRÚC của gói bàn giao, dù thiếu file đánh dấu.

    Vì sao cần: công cụ chép thư mục trên Windows có thể BỎ QUA file bắt đầu bằng dấu chấm
    (`Compress-Archive` bỏ qua thật, và Explorer cũng có thể), nên thư mục đúng vẫn có thể thiếu
    `.sentimentx_root`. Điều kiện đòi hai dấu hiệu rất đặc trưng của gói - `env/.env.colab`, hoặc
    `data/` đi kèm `experiments/` - chứ không đoán theo tên thư mục.
    """
    path = Path(path)
    if (path / "env" / ".env.colab").is_file():
        return True
    return (path / "data").is_dir() and (path / "experiments").is_dir()


def drive_env_file(folder=None, candidates=None):
    """File env trên Drive (`<Drive>/env/.env.colab`), hoặc None nếu chưa thấy Drive."""
    from src import paths

    root = drive_dir(folder=folder, candidates=candidates)
    if root is None:
        return None
    name = str((paths.cfg().get("colab") or {}).get("env_file") or "")
    return (root / name) if name else None


def _apply_file(path):
    """Đọc file dạng KEY=VALUE. Bỏ qua dòng trống, dòng chú thích, và khoá để TRỐNG giá trị.

    VÌ SAO KHOA ĐỂ TRỐNG PHẢI BỊ BỎ QUA: file mẫu của dự án có những dòng như `HF_HOME=` để trống.
    Đặt biến thành chuỗi rỗng thì thư viện bên dưới không hiểu là "chưa cấu hình": `huggingface_hub`
    ghép `os.path.join("", "hub")` thành thư mục `hub` TƯƠNG ĐỐI, và tải model vào ngay trong repo
    (đã gặp thật: 6,3 GB cache nằm trong cây làm việc). Khoá để trống nghĩa là "không đặt", đúng quy
    ước của `src/paths.py` với hai gốc đường dẫn.

    VÌ SAO ĐỌC BẰNG `utf-8-sig`: tệp env gửi cho người chạy được ghi kèm BOM để công cụ Windows
    (Notepad, trình xem trong WinRAR) hiện đúng chữ tiếng Việt. `utf-8-sig` bỏ BOM nếu có và hành xử
    y hệt `utf-8` nếu không, nên BOM không thể lọt vào TÊN của khoá đầu tiên - đúng lỗi im lặng cần
    tránh: token có trong tệp mà chương trình vẫn báo thiếu.
    """
    with open(path, "r", encoding="utf-8-sig") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            value = value.strip().strip('"').strip("'")
            if not value:
                continue
            os.environ.setdefault(key.strip(), value)


def _from_colab_secrets():
    """Đọc Colab Secrets. Trả về dict rỗng nếu không ở Colab hoặc không có gì."""
    try:
        from google.colab import userdata  # type: ignore
    except Exception:
        return {}
    secrets = {}
    for name in ("DAGSHUB_TOKEN", "HF_TOKEN"):
        try:
            value = userdata.get(name)
        except Exception:
            value = None
        if value:
            secrets[name] = str(value)
    return secrets
