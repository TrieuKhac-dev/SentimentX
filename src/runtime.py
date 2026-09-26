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
    """Thư mục Drive của nhóm trên Colab.

    Nhận ra thư mục theo hai dấu hiệu, KHÔNG đoán theo tên (MyDrive và Shared drives trông giống nhau,
    đoán theo tên thì notebook có thể ghi kết quả vào thư mục cùng tên của người khác):

      1. FILE ĐÁNH DẤU `.sentimentx_root` - chắc chắn nhất;
      2. CẤU TRÚC CỦA GÓI: `env/.env.colab`, hoặc `data/` đi kèm `experiments/`.

    Vì sao phải có dấu hiệu thứ hai: không phải ai cũng tạo được `.sentimentx_root`. Tên file bắt đầu
    bằng dấu chấm nên **web Drive không tạo được**, và khi A chia sẻ thư mục cho b/c/d thì A có thể chỉ
    share rồi thôi. Không có dấu hiệu thứ hai thì mọi người được chia sẻ đều bị chặn vô cớ.

    KHÔNG tự mount Drive: việc mount là của người chạy notebook (docs/00_workflow/01_flow.md).

    Không khớp theo tên thì xét (`drive_candidates`, theo thứ tự ưu tiên): một cấp trong các gốc đã khai
    (`MyDrive`, `Shareddrives`), rồi trong thư mục con của gốc (shared drive lồng), rồi QUA LỐI TẮT
    (`MyDrive/.shortcut-targets-by-id/...`) - lối tắt là cách b/c/d nhìn thấy thư mục A chia sẻ.

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
    """Một lượt tìm: khớp theo TÊN (nếu có khai) trước, rồi tới thư mục đáng xét nhất."""
    roots = drive_roots(places)
    for place in places:
        try:
            candidate = Path(str(place).format(folder=folder or ""))
        except (KeyError, IndexError, ValueError):
            continue
        # Bỏ qua chính các GỐC Drive: nhận `MyDrive/` làm thư mục nhóm thì kết quả sẽ ghi vào
        # `MyDrive/experiments` - sai chỗ mà lại im lặng.
        if candidate in roots or not candidate.is_dir():
            continue
        if marker and not (candidate / marker).exists() and not looks_like_group_dir(candidate):
            continue
        return candidate
    found = drive_candidates(places)
    return found[0]["path"] if found else None


def drive_candidates(places=None, limit=40):
    """Mọi thư mục ĐÁNG XÉT trong các gốc Drive, kèm cách nhận ra chúng.

    Trả về `[{"path": Path, "how": "marker" | "structure", "where": str, "prepared": bool}, ...]`, đã
    sắp theo thứ tự ưu tiên: file đánh dấu trước cấu trúc, cấp nông trước cấp sâu, trong cùng nhóm thì
    thư mục có `data/` lên trước (dấu hiệu đã được chuẩn bị để chạy), cuối cùng theo đường dẫn - để kết
    quả không phụ thuộc thứ tự đọc đĩa.

    Đây là MỘT nguồn duy nhất cho cả việc chọn thư mục (`drive_dir`) và việc in ra khi không chọn được
    (ô bootstrap), nên hai chỗ không thể lệch nhau.

    Các lượt xét dừng ngay khi lượt trước đã có kết quả, vì mỗi lượt là một loạt lệnh đọc đĩa trên
    Drive (chậm): (1) một cấp, (2) QUA LỐI TẮT, (3) trong thư mục con của gốc - shared drive lồng. Lối
    tắt xét trước lượt thứ ba vì nó chỉ đọc một thư mục ẩn nhỏ, còn lượt thứ ba phải đi hết cây một cấp
    của MyDrive - đúng chỗ tốn thời gian nhất.
    """
    from src import paths

    settings = paths.cfg().get("colab") or {}
    marker = str(settings.get("folder_marker") or "")
    shortcut = str(settings.get("shortcut_dir") or "")
    places = list(places if places is not None else settings.get("drive_candidates") or [])

    found = []

    def consider(path, where):
        if any(item["path"] == path for item in found):
            return False
        if marker and (path / marker).exists():
            how = "marker"
        elif looks_like_group_dir(path):
            how = "structure"
        else:
            return False
        found.append({"path": path, "how": how, "where": where,
                      "prepared": (path / "data").is_dir()})
        return True

    for root in drive_roots(places):
        if not root.is_dir():
            continue
        # Mỗi lượt phải xét HẾT các thư mục của lượt đó rồi mới quyết định có đi tiếp hay không: xét
        # kiểu "dừng ngay khi thấy một cái" thì phép xếp hạng bên dưới không có gì để chọn - đúng lỗi mà
        # test "thư mục có file đánh dấu phải thắng thư mục chỉ có cấu trúc" bắt được.
        before = len(found)
        children = sorted(child for child in root.iterdir() if child.is_dir())
        for child in children:
            consider(child, "một cấp")
        if len(found) > before:
            continue
        if shortcut and (root / shortcut).is_dir():
            targets = [target for folder_id in sorted(item for item in (root / shortcut).iterdir()
                                                      if item.is_dir())
                       for target in sorted(item for item in folder_id.iterdir() if item.is_dir())]
            for item in targets:
                consider(item, "qua lối tắt (shortcut)")
            if len(found) > before:
                continue
        nested = [grand for child in children
                  for grand in sorted(item for item in child.iterdir() if item.is_dir())]
        for item in nested:
            consider(item, "trong thư mục con")

    def rank(item):
        return (0 if item["how"] == "marker" else 1,
                {"một cấp": 0, "qua lối tắt (shortcut)": 1}.get(item["where"], 2),
                0 if item["prepared"] else 1,
                item["path"].as_posix())

    return sorted(found, key=rank)[:limit]


def folder_marker():
    """Tên file đánh dấu thư mục nhóm, đọc từ `configs/paths.yaml`.

    Notebook cần tên này chỉ để NÓI RA khi thư mục được nhận bằng cấu trúc gói chứ không bằng dấu
    (`drive_dir` đã đọc cấu hình cho việc tìm). Không viết cứng tên file ở hai chỗ.
    """
    from src import paths

    return str((paths.cfg().get("colab") or {}).get("folder_marker") or "")


def drive_roots(places=None):
    """Các GỐC Drive đã khai (`/content/drive/MyDrive`, `/content/drive/Shareddrives`, ...).

    Lấy từ mẫu đường dẫn trong `configs/paths.yaml`: phần trước `{folder}` là gốc. Shared drive nằm
    ở gốc riêng, nên khi không thấy thư mục nhóm thì phải in TỪNG gốc - người đọc cần biết gốc nào
    rỗng, gốc nào có thư mục lạ.
    """
    from src import paths

    settings = paths.cfg().get("colab") or {}
    places = list(places if places is not None else settings.get("drive_candidates") or [])
    roots = []
    for place in places:
        pattern = Path(str(place))
        if "{" not in pattern.name:
            continue
        if pattern.parent not in roots:
            roots.append(pattern.parent)
    return roots


def drive_listing(places=None, limit=12):
    """Mỗi gốc Drive kèm tên các thư mục con đang thấy: để IN RA khi không tìm được thư mục nhóm.

    Trả về `[{"root": Path, "names": [tên...], "shortcuts": [tên...], "gone": bool}, ...]`. Không phải
    để chọn thư mục - chọn thì theo `drive_candidates` (dấu hiệu file đánh dấu hoặc cấu trúc gói) - mà
    để người đọc biết máy đang nhìn vào đâu: gốc MyDrive có gì, gốc Shareddrives có gì, LỐI TẮT
    (shortcut) đang trỏ tới đâu, hay cả hai gốc đều rỗng.

    `shortcuts` là chỗ trả lời câu hỏi hay gặp nhất của người được chia sẻ thư mục nhóm: "tôi đã được
    chia sẻ rồi mà notebook bảo chưa thấy" - khi đó hoặc chưa bấm "Add shortcut to My Drive", hoặc lối
    tắt đã có mà thư mục đích không có dấu hiệu nào của gói.
    """
    from src import paths

    settings = paths.cfg().get("colab") or {}
    shortcut = str(settings.get("shortcut_dir") or "")
    listing = []
    for root in drive_roots(places):
        exists = root.is_dir()
        names = sorted(child.name for child in root.iterdir()) if exists else []
        shortcuts = []
        if shortcut and (root / shortcut).is_dir():
            for folder_id in sorted((root / shortcut).iterdir()):
                if folder_id.is_dir():
                    shortcuts.extend(sorted(target.name for target in folder_id.iterdir()))
        listing.append({"root": root, "names": names[:limit], "gone": not exists,
                        "shortcuts": shortcuts[:limit]})
    return listing


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
