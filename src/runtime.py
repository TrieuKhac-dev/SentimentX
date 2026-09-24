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


def drive_dir(folder=None, candidates=None):
    """Thư mục Drive của nhóm trên Colab, nhận ra bằng FILE ĐÁNH DẤU.

    Vì sao phải có file đánh dấu: MyDrive và Shared drives trông giống nhau, mà chỉ một trong hai
    là thư mục giảng viên cấp. Đoán theo tên thư mục thì notebook có thể đọc nhầm một thư mục
    cùng tên của người khác - và lúc đó nó ghi kết quả vào chỗ không ai tìm thấy.

    KHÔNG tự mount Drive: việc mount là của người chạy notebook (docs/00_workflow/01_flow.md).

    Trả về `Path` hoặc None (chưa mount, hoặc chưa có thư mục nào khớp).
    """
    from src import paths

    folder = folder if folder is not None else os.environ.get("SENTIMENTX_DRIVE_FOLDER", "")
    settings = paths.cfg().get("colab") or {}
    marker = str(settings.get("folder_marker") or "")
    places = list(candidates if candidates is not None
                  else settings.get("drive_candidates") or [])
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
    return None


def drive_env_file(folder=None, candidates=None):
    """File env trên Drive (`<Drive>/env/.env.colab`), hoặc None nếu chưa thấy Drive."""
    from src import paths

    root = drive_dir(folder=folder, candidates=candidates)
    if root is None:
        return None
    name = str((paths.cfg().get("colab") or {}).get("env_file") or "")
    return (root / name) if name else None


def _apply_file(path):
    """Đọc file dạng KEY=VALUE. Bỏ qua dòng trống và dòng bắt đầu bằng `#`."""
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


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
