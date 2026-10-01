# -*- coding: utf-8 -*-
"""Dựng GÓI BÀN GIAO TĂNG DẦN, kèm sổ biết đã gửi file nào.

VÌ SAO CẦN CÔNG CỤ NÀY
Gói bàn giao chứa đúng những thứ git KHÔNG chở được: dữ liệu (`data/`), `env/.env.colab`, bản
notebook đã ghim, README của từng thí nghiệm, và file đánh dấu thư mục nhóm. Gửi lại TOÀN BỘ mỗi
lần là bắt người nhận tải lại vài chục MB họ đã có, mà cũng không ai biết chính xác file nào đã đổi.
Công cụ này gửi TĂNG DẦN: gói `NNN` chỉ chứa file MỚI hoặc ĐÃ ĐỔI so với gói trước, kèm một sổ ghi
băm của từng file đã gửi. Sổ nằm trong git nên biết được gói nào đã gửi file nào, và băm nào.

BỐN LỚP CỦA MỘT FILE
    new      chưa từng gửi            -> có trong gói
    changed  đã gửi, nội dung nay khác -> có trong gói
    kept     đã gửi, nội dung y nguyên -> KHÔNG có trong gói (người nhận đã có rồi)
    deleted  đã gửi, nay không còn     -> không có trong gói, nhưng CÓ trong manifest để người nhận
                                          biết mà xoá đi

CẢNH BÁO ĐỎ: ĐỔI NỘI DUNG TRONG MỘT PHIÊN BẢN DỮ LIỆU ĐÃ GỬI
Mã phiên bản dữ liệu được tính từ NỘI DUNG các file gốc. Nếu một file trong `data/processed/<mã>/`
hay `data/raw/<tên>/<phiên bản>/` đã gửi rồi mà nay khác đi, thì người nhận đang giữ một bộ dữ liệu
mang ĐÚNG mã cũ nhưng nội dung khác - kết quả họ đã báo cáo không còn so được với lần chạy mới.
Đó là lỗi im lặng, nên mặc định công cụ DỪNG (mã thoát 3). Cách sửa đúng là tạo phiên bản dữ liệu
MỚI (dữ liệu gốc mới, hoặc pipeline mới) rồi gửi gói mới - không sửa tại chỗ. Ai đã hiểu rõ và vẫn
muốn gửi thì thêm `--allow-red`; cảnh báo khi đó được ghi vào manifest.

ỨNG VIÊN SUY TỪ CẤU HÌNH THÍ NGHIỆM, KHÔNG CHÉP TAY
Danh sách file không được viết cứng ở đây. Với từng thí nghiệm trong `experiments/`, công cụ hỏi
chính cấu hình của nó:
    - `experiments.list_experiments()`  -> có thí nghiệm nào (để lấy notebook + README)
    - `experiments.load(...)` + `experiments.requires(...)`  -> lần chạy đó CẦN những đường dẫn nào
      (file dữ liệu theo vai, bảng mã nhãn, prompt, `requires_extra`)
    - file phiên bản dataset + `versioning.declared_files(...)`  -> dữ liệu gốc nào đã đi vào dataset
Chỉ những đường dẫn nằm TRONG GỐC DỮ LIỆU mới vào gói: prompt và file cấu hình đã nằm trong git,
notebook kéo chúng về theo đúng commit đã ghim.

CÒN KHAI PHIÊN BẢN TRONG REPO THÌ CÒN GIỮ DỮ LIỆU CỦA NÓ
Ứng viên suy từ thí nghiệm nghĩa là khi `experiments/` chuyển sang một phiên bản dữ liệu mới, bộ dữ
liệu cũ rời khỏi danh sách và bị xếp vào lớp `deleted` - tức bảo người nhận XOÁ nó khỏi Drive. Với dữ
liệu thì đó là cảnh báo ĐỎ: kết quả người nhận đã chạy trên bộ cũ thành không tái lập được. Nên công
cụ còn hỏi thêm `configs/datasets/<tên>/<phiên bản>.yaml`: PHIÊN BẢN NÀO CÒN CẤU HÌNH TRONG REPO thì
dữ liệu đã xử lý của nó vẫn là ứng viên, và vì nội dung không đổi nên nó thành `kept` - người nhận
giữ nguyên, không phải xoá, cũng không phải tải lại. Bỏ hẳn file cấu hình khỏi repo thì phiên bản đó
mới rời gói, và cảnh báo đỏ nổi lên như cũ để người dựng gói quyết định.
(`declared_dataset_versions`)

CÂY GÓI TRÙNG CÂY CŨ (người nhận không phải đổi thói quen)
    README.md, MANIFEST.csv, .sentimentx_root, env/, data/
    notebooks/<model>/<method>/<expNNN>.ipynb      (nguồn: experiments/<...>/notebook.ipynb)
    experiments/<model>/<method>/<expNNN>/README.md
Đường dẫn của notebook KHÁC đường dẫn trong repo, nên `files.csv` ghi cả hai: `package_path` (trong
gói) và `source` (trong repo).

CÁCH DÙNG
    python scripts/build_package.py                     # gói kế tiếp, theo sổ đang có
    python scripts/build_package.py --dry-run           # chỉ in ra, không ghi gì
    python scripts/build_package.py --number 002        # đặt số gói
    python scripts/build_package.py --allow-red         # vẫn gửi dù có cảnh báo đỏ

Gói zip nằm ở `handover/out/` - thư mục này KHÔNG vào git (vài chục MB nhị phân). Sổ thì vào git:
`handover/files.csv`, `handover/ledger.csv`, `handover/packages/<NNN>/manifest.csv`. Mỗi gói một
lần commit.
"""

import argparse
import csv
import datetime
import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Trên Windows, console mặc định có thể không phải UTF-8 (ví dụ cp1252),
# khiến việc in tiếng Việt bị lỗi. Ép stdout/stderr sang UTF-8.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from src.experiments import experiments
from src.core import dataset as dataset_module
from src.core import paths, utils, versioning
from src.workflow import repo, runtime

HANDOVER_DIRNAME = "handover"
OUT_DIRNAME = "out"
PACKAGES_DIRNAME = "packages"

FILES_CSV = "files.csv"
LEDGER_CSV = "ledger.csv"
MANIFEST_CSV = "manifest.csv"

# Tên file gói dùng cho bản README của người nhận và bản manifest đi kèm trong zip.
PACKAGE_README = "README.md"
PACKAGE_MANIFEST = "MANIFEST.csv"

# File đánh dấu thư mục nhóm. Lấy từ `runtime` chứ không viết lại: notebook dò thư mục nhóm bằng
# chính hàm đó, lệch tên là gói không được nhận ra.
MARKER_NAME = runtime.folder_marker()

# Hai tệp env. Đường dẫn TRONG GÓI khác đường dẫn trong repo: trên Drive, notebook dò thư mục nhóm
# bằng `env/.env.colab` (xem `runtime.looks_like_group_dir`), còn trong repo hai file này nằm ở gốc.
ENV_FILES = (("env/.env.colab", ".env.colab"),
             ("env/.env.colab.example", ".env.colab.example"))

# Nhóm KHÔNG bắt buộc: thiếu thì cảnh báo chứ không dừng. `.env.colab` là secret nên không có trong
# git - máy nào chưa từng chạy Colab sẽ không có nó, mà gói vẫn phải dựng được (người nhận tự điền,
# hoặc lấy từ gói trước).
OPTIONAL_GROUPS = ("env",)

# Bốn lớp. `kept` không vào gói; `deleted` vào manifest nhưng không vào gói.
CLASS_NEW, CLASS_CHANGED, CLASS_KEPT, CLASS_DELETED = "new", "changed", "kept", "deleted"
CLASSES = (CLASS_NEW, CLASS_CHANGED, CLASS_KEPT, CLASS_DELETED)
IN_ZIP = (CLASS_NEW, CLASS_CHANGED)

# Thư mục dữ liệu mà việc đổi nội dung SAU KHI GỬI là chuyện phải cảnh báo đỏ.
DATA_ROOTS = ("data/processed/", "data/raw/")

FILES_FIELDS = ("package_path", "source", "group", "sha256", "size")
LEDGER_FIELDS = ("package_path", "sha256", "size", "group", "source", "first_package",
                 "last_package", "mtime", "sent_at")
MANIFEST_FIELDS = ("package_path", "class", "group", "sha256", "size", "source",
                   "sent_package", "note", "depends_on")

# File đánh dấu là file RỖNG (đúng như gói cũ), nên băm của nó cố định và nó không bị coi là "đổi"
# ở mọi gói sau.
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()


class PackageError(Exception):
    """Không dựng được gói: thiếu file bắt buộc, sổ hỏng, hoặc số gói không hợp lệ."""


# ---
# Ứng viên: hỏi cấu hình thí nghiệm, không chép tay danh sách
# ---


def under(path, base):
    """`path` có nằm trong `base` không (so theo đường dẫn đã giải)."""
    try:
        Path(path).resolve().relative_to(Path(base).resolve())
        return True
    except ValueError:
        return False


def data_package_path(path, data_root):
    """Đường dẫn TRONG GÓI của một file dữ liệu: tính từ gốc dữ liệu, thêm tiền tố `data/`.

    Gốc dữ liệu trên Colab là thư mục Drive chứ không phải gốc repo, nên phải nhận nó làm tham số
    thay vì ghép chuỗi từ gốc repo.
    """
    relative = Path(path).resolve().relative_to(Path(data_root).resolve()).as_posix()
    return "data/" + relative


def entry(package_path, source, group):
    """Một dòng ứng viên, kèm băm nội dung (băm là thứ khiến gói gửi được TĂNG DẦN)."""
    path = Path(source)
    return {"package_path": package_path,
            "source": utils.rel(path) if under(path, paths.root()) else str(path),
            "group": group,
            "sha256": versioning.file_sha256(path),
            "size": path.stat().st_size,
            "mtime": datetime.datetime.fromtimestamp(path.stat().st_mtime).isoformat(
                timespec="seconds")}


def marker_entry():
    """Dòng cho file đánh dấu thư mục nhóm - file RỖNG, sinh ra lúc đóng gói."""
    return {"package_path": MARKER_NAME, "source": "", "group": "marker",
            "sha256": EMPTY_SHA256, "size": 0, "mtime": ""}


def declared_dataset_versions(root=None, data_root=None, load_dataset=None):
    """Các phiên bản dữ liệu ĐÃ XỬ LÝ mà repo CÒN KHAI cấu hình: `[(mã phiên bản, cấu hình)]`.

    Quét `<gốc dữ liệu>/processed/`, đọc `processing_log.json` của mỗi phiên bản để biết nó là
    `(tên dataset, phiên bản)`, rồi chỉ giữ những phiên bản còn file cấu hình
    `configs/datasets/<tên>/<phiên bản>.yaml` trong repo.

    Vì sao cần: đổi `data.version` trong `experiments/` làm bộ dữ liệu cũ rời khỏi "ứng viên suy từ
    thí nghiệm", và công cụ sẽ hiểu là `deleted` - tức bảo người nhận XOÁ dữ liệu cũ khỏi Drive. Với
    dữ liệu thì đó là cảnh báo ĐỎ, vì kết quả người nhận đã chạy trên bộ đó thành không tái lập được.
    Quy tắc ở đây: **còn khai thì còn giữ**.

    Phiên bản không đọc được `processing_log.json` hoặc không còn cấu hình thì bỏ qua: lúc đó `deleted`
    là đúng, và cảnh báo đỏ vẫn nổi lên để người dựng gói quyết định.
    """
    root = Path(root or paths.root())
    data_root = Path(data_root or paths.data_root())
    load_dataset = load_dataset or dataset_module.load_config
    directory = root / paths.cfg()["roots"]["configs"] / paths.cfg()["configs"]["datasets"]
    processed_root = data_root / paths.cfg()["data"]["processed"]
    if not processed_root.is_dir():
        return []
    found = []
    for processed in sorted(processed_root.iterdir()):
        if not processed.is_dir() or processed.name.startswith("."):
            continue
        log_path = processed / paths.pattern("processing_log")
        try:
            info = dict((json.loads(log_path.read_text(encoding="utf-8")) or {}).get("dataset") or {})
        except (OSError, ValueError):
            continue
        name, version = info.get("name"), info.get("version")
        if not name or not version:
            continue
        if not (directory / str(name) / "{}.yaml".format(version)).is_file():
            continue
        try:
            found.append((processed.name, load_dataset(name, version)))
        except Exception:  # noqa: BLE001
            continue
    return found


def collect(root=None, data_root=None, readme=None, list_experiments=None, load=None,
            load_dataset=None, log=print):
    """Danh sách ứng viên của gói, sắp theo đường dẫn trong gói.

    Ba điểm tiêm (`list_experiments`, `load`, `load_dataset`) để test dựng được cây giả mà không cần
    dữ liệu thật, và để nhánh "thí nghiệm khai dataset chưa chạy pipeline" kiểm được.
    """
    root = Path(root or paths.root())
    data_root = Path(data_root or paths.data_root())
    readme = Path(readme) if readme else root / HANDOVER_DIRNAME / PACKAGE_README
    list_experiments = list_experiments or experiments.list_experiments
    load = load or experiments.load
    load_dataset = load_dataset or dataset_module.load_config

    experiments_dir = root / paths.cfg()["roots"]["experiments"]
    found = {}
    missing = []
    warned = []
    notes = []

    def add(package_path, source, group, optional=None):
        optional = group in OPTIONAL_GROUPS if optional is None else optional
        source = Path(source)
        if source.is_dir():
            # `requires_extra` có thể khai một THƯ MỤC (ví dụ `data/models/vncorenlp`): gửi cả cây
            # con, giữ nguyên cấu trúc bên trong.
            for child in sorted(path for path in source.rglob("*") if path.is_file()):
                add(package_path + "/" + child.relative_to(source).as_posix(), child, group,
                    optional=optional)
            return
        if not source.is_file():
            line = "{} ({})".format(utils.rel(source), group)
            (warned if optional else missing).append(line)
            return
        found[package_path] = entry(package_path, source, group)

    for model_id, method, exp_id in list_experiments():
        folder = experiments_dir / model_id / method / exp_id
        # Notebook vào gói dưới tên `notebooks/<model>/<method>/<expNNN>.ipynb`: người nhận mở MỘT
        # file phẳng như vậy, không phải đi vào cây `experiments/` của repo.
        add("notebooks/{}/{}/{}.ipynb".format(model_id, method, exp_id),
            folder / "notebook.ipynb", "notebook")
        add("experiments/{}/{}/{}/README.md".format(model_id, method, exp_id),
            folder / "README.md", "experiment_readme")

        try:
            result = load(model_id, method, exp_id)
        except Exception as exc:  # noqa: BLE001 - config hỏng thì báo, không làm chết cả công cụ
            notes.append("{}/{}/{}: không nạp được config ({})".format(
                model_id, method, exp_id, exc))
            continue
        data = (result.get("config") or {}).get("data") or {}
        dataset_name, dataset_version = data.get("dataset"), data.get("version")
        if not dataset_name:
            notes.append("{}/{}/{}: config không khai `data.dataset`".format(
                model_id, method, exp_id))
            continue
        version_id = versioning.latest_dataset(dataset_name)
        if not version_id:
            notes.append("{}/{}/{}: chưa có dataset đã xử lý của {} (chạy pipeline trước)".format(
                model_id, method, exp_id, dataset_name))
            continue

        for row in experiments.requires(result, version_id):
            path = Path(row["path"])
            # Prompt và file cấu hình nằm trong git: notebook kéo chúng về theo commit đã ghim.
            if under(path, data_root):
                add(data_package_path(path, data_root), path, "data")

        # Hai file SỔ của phiên bản dữ liệu. `experiments.requires` không kể chúng - lúc chạy chúng
        # chỉ để ĐỐI CHIẾU - nhưng thiếu thì máy người nhận không kiểm được gì: `processing_log.json`
        # là bằng chứng bộ dữ liệu do đúng hai file cấu hình nào tạo ra, `eval_lock.json` là khoá tập
        # đánh giá. Gói cũ có cả hai, và preflight đọc cả hai.
        for path in (versioning.processing_log_path(version_id),
                     versioning.eval_lock_path(version_id)):
            if under(path, data_root):
                add(data_package_path(path, data_root), path, "data")

        try:
            dataset_cfg = load_dataset(dataset_name, dataset_version)
        except Exception as exc:  # noqa: BLE001
            notes.append("{}: không đọc được file phiên bản dataset ({})".format(
                dataset_name, exc))
            continue
        for source in dataset_module.sources_of(dataset_cfg):
            for path in versioning.declared_files(dataset_cfg, source):
                if under(path, data_root):
                    add(data_package_path(path, data_root), path, "data_raw")
        # `raw_meta.yaml` nằm cạnh dữ liệu gốc, ghi nguồn gốc của bộ dữ liệu: người nhận cần nó để
        # biết mình đang chạy trên bản nào.
        raw_dir = dataset_cfg.get("_raw_dir")
        if raw_dir:
            candidate = Path(raw_dir) / "raw_meta.yaml"
            if candidate.is_file() and under(candidate, data_root):
                add(data_package_path(candidate, data_root), candidate, "data_raw")

    # Phiên bản dữ liệu CÒN ĐƯỢC KHAI trong repo thì dữ liệu của nó vẫn thuộc gói (thành `kept` vì nội
    # dung không đổi), thay vì bị coi là `deleted` và bảo người nhận xoá - xem
    # `declared_dataset_versions`. `optional=True`: một phiên bản còn khai mà thư mục dữ liệu đã bị dọn
    # thì gói vẫn dựng được, chỉ báo thiếu file đó.
    for version_id, dataset_cfg in declared_dataset_versions(
            root=root, data_root=data_root, load_dataset=load_dataset):
        processed = data_root / paths.cfg()["data"]["processed"] / version_id
        for name in sorted(dataset_cfg.get("splits") or {}):
            candidate = processed / "{}.csv".format(name)
            if under(candidate, data_root):
                add(data_package_path(candidate, data_root), candidate, "data", optional=True)
        for pattern_name in ("label_map", "processing_log", "eval_lock"):
            candidate = processed / paths.pattern(pattern_name)
            if under(candidate, data_root):
                add(data_package_path(candidate, data_root), candidate, "data", optional=True)
        for source in dataset_module.sources_of(dataset_cfg):
            for path in versioning.declared_files(dataset_cfg, source):
                if under(path, data_root):
                    add(data_package_path(path, data_root), path, "data_raw", optional=True)

    for package_path, source in ENV_FILES:
        add(package_path, root / source, "env")
    add(PACKAGE_README, readme, "package_readme")
    found[MARKER_NAME] = marker_entry()
    for note in notes:
        log("  bỏ qua: " + note)
    for warning in warned:
        log("  CẢNH BÁO: không có {}. File env là secret nên không nằm trong git: lấy từ gói trước, "
            "hoặc điền theo bản mẫu env/.env.colab.example, rồi dựng lại gói.".format(warning))
    if missing:
        raise PackageError(
            "Thiếu {} file bắt buộc của gói:\n  - {}\n"
            "Ô nào thiếu thì bổ sung trước: notebook thiếu là thí nghiệm chưa tạo xong, "
            "dữ liệu thiếu là pipeline chưa chạy.".format(len(missing), "\n  - ".join(missing)))
    return sorted(found.values(), key=lambda item: item["package_path"])
# ---
# Sổ: đọc, ghi, và so với ứng viên hiện tại
# ---


def read_csv(path, fields):
    """Đọc một file sổ. Không có file nghĩa là sổ trống (lần gửi đầu tiên)."""
    path = Path(path)
    if not path.is_file():
        return []
    with open(path, "r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        header = tuple(reader.fieldnames or ())
        if header != tuple(fields):
            raise PackageError(
                "{} có cột {} nhưng phải là {}. Sổ bị sửa tay thì phải sửa lại đúng cột, "
                "nếu không công cụ sẽ so sai và gửi thiếu file.".format(
                    utils.rel(path), header, tuple(fields)))
        return [dict(row) for row in reader]


def write_csv(path, fields, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fields})
    return path


def read_ledger(path):
    """Sổ luỹ kế, tra theo đường dẫn trong gói."""
    return {row["package_path"]: row for row in read_csv(path, LEDGER_FIELDS)}


def classify(entries, ledger):
    """Lớp của từng ứng viên so với sổ, cộng những file ĐÃ GỬI mà nay không còn.

    File đã gửi mà nay không còn được ghi lại chứ không lặng lẽ bỏ qua: người nhận còn giữ nó, và
    một file dữ liệu còn nằm trong thư mục dữ liệu của họ là thứ làm hỏng lần chạy sau.
    """
    rows = []
    seen = set()
    for item in entries:
        row = dict(item)
        sent = ledger.get(item["package_path"])
        row["sent_package"] = sent["last_package"] if sent else ""
        if sent is None:
            row["class"] = CLASS_NEW
        elif sent["sha256"] != item["sha256"]:
            row["class"] = CLASS_CHANGED
        else:
            row["class"] = CLASS_KEPT
        rows.append(row)
        seen.add(item["package_path"])
    for package_path, sent in sorted(ledger.items()):
        if package_path in seen:
            continue
        rows.append({"package_path": package_path, "source": sent.get("source", ""),
                     "group": sent.get("group", ""), "sha256": sent.get("sha256", ""),
                     "size": sent.get("size", ""), "sent_package": sent.get("last_package", ""),
                     "class": CLASS_DELETED})
    return sorted(rows, key=lambda row: row["package_path"])


def data_unit(package_path):
    """Thư mục 'phiên bản dữ liệu' chứa một đường dẫn, hoặc None nếu không phải file dữ liệu.

    Đơn vị là thư mục chứ không phải từng file: cả bộ dữ liệu cùng mang một mã phiên bản, nên đổi
    một file trong đó là đổi bộ dữ liệu mà mã thì vẫn thế.
    """
    text = str(package_path).replace("\\", "/")
    for prefix, depth in (("data/processed/", 3), ("data/raw/", 4)):
        if text.startswith(prefix):
            parts = text.split("/")
            if len(parts) >= depth:
                return "/".join(parts[:depth])
    return None


def red_flags(rows, ledger):
    """File dữ liệu ĐÃ GỬI mà nay đổi nội dung hoặc biến mất - xem docstring đầu file."""
    sent_units = set()
    for package_path in ledger:
        unit = data_unit(package_path)
        if unit:
            sent_units.add(unit)
    flags = []
    for row in rows:
        if row["class"] not in (CLASS_CHANGED, CLASS_DELETED):
            continue
        unit = data_unit(row["package_path"])
        if unit and unit in sent_units:
            flags.append(
                "{} ({}{}): đã gửi ở gói {} mà nay {}".format(
                    row["package_path"], unit,
                    ", dữ liệu CÒN thiếu hẳn" if row["class"] == CLASS_DELETED else "",
                    row["sent_package"] or "?",
                    "KHÔNG CÒN trong cây" if row["class"] == CLASS_DELETED
                    else "nội dung KHÁC đi"))
    return flags


RED_ACTION = (
    "Đây là cảnh báo đỏ: người nhận đang giữ bộ dữ liệu mang ĐÚNG mã phiên bản cũ nhưng nội dung "
    "khác, nên kết quả họ đã chạy không còn so được với lần chạy mới.\n"
    "Cách sửa đúng: tạo phiên bản dữ liệu MỚI (dữ liệu gốc mới, hoặc phiên bản pipeline mới) rồi "
    "gửi gói mới - đừng sửa nội dung tại chỗ.\n"
    "Nếu đã hiểu rõ và vẫn muốn gửi, thêm --allow-red; khi đó cảnh báo được ghi vào manifest."
)


def update_ledger(ledger, rows, number, sent_at):
    """Sổ sau khi gửi gói `number`: file gửi thì ghi lại băm MỚI, file mất thì bỏ khỏi sổ.

    Bỏ file đã xoá khỏi sổ là có chủ ý: nếu sau này file đó quay lại với nội dung cũ, nó phải được
    gửi như file MỚI - người nhận đã xoá nó theo manifest nên không còn bản nào để dùng.

    `first_package` giữ nguyên qua các gói (biết file đó vào tay người nhận từ gói nào), `last_package`
    là gói gần nhất chứa nó, `mtime` là thời điểm file được sửa ở máy - dấu hiệu phụ để tra khi hai lần
    băm cho cùng kết quả mà người đọc vẫn muốn biết file đã bị chạm hay chưa.
    """
    updated = dict(ledger)
    for row in rows:
        if row["class"] in IN_ZIP:
            previous = ledger.get(row["package_path"]) or {}
            updated[row["package_path"]] = {
                "package_path": row["package_path"], "sha256": row["sha256"],
                "size": row["size"], "group": row["group"], "source": row.get("source", ""),
                "first_package": previous.get("first_package") or "{:03d}".format(number),
                "last_package": "{:03d}".format(number),
                "mtime": row.get("mtime", ""), "sent_at": sent_at}
        elif row["class"] == CLASS_DELETED:
            updated.pop(row["package_path"], None)
    return updated


def depends_on(number):
    """Gói này phải áp SAU gói nào: `NNN-1`, hoặc rỗng với gói đầu.

    Gói gửi tăng dần chỉ có nghĩa khi áp đúng thứ tự (gói sau giả định người nhận đã có gói trước), nên
    manifest ghi rõ nó phụ thuộc gói nào thay vì để người nhận tự đoán.
    """
    return "" if number <= 1 else "{:03d}".format(number - 1)


def next_number(packages_dir):
    """Số gói kế tiếp, tính từ các thư mục đánh số đang có."""
    numbers = [int(path.name) for path in Path(packages_dir).glob("*")
               if path.is_dir() and path.name.isdigit()] if Path(packages_dir).is_dir() else []
    return (max(numbers) + 1) if numbers else 1


def package_number(raw, packages_dir):
    """Số gói của lần gửi này: số người dùng truyền, hoặc số kế tiếp.

    Số truyền vào phải là số: `--number 001b` mà cứ đoán thì gói sẽ mang một cái tên không ai tra
    được, và `int()` ném ra một lỗi khó đọc.
    """
    if raw is None:
        return next_number(packages_dir)
    try:
        return int(str(raw).strip())
    except ValueError:
        raise PackageError("Số gói phải là số, đang là {!r} (ví dụ --number 002).".format(raw))


def source_path(row, root):
    """Đường dẫn nguồn của một dòng sổ: dạng tương đối so với gốc repo, hoặc tuyệt đối."""
    text = str(row.get("source") or "")
    path = Path(text)
    return path if path.is_absolute() else Path(root) / path


def stage(rows, staging, root=None):
    """Chép file của gói vào thư mục tạm, giữ đúng đường dẫn trong gói.

    Thư mục tạm được tạo ở ĐÂY chứ không phải ở nơi gọi: gói chỉ có mục cần xoá thì không có file
    nào để chép, mà `main` vẫn phải đặt được manifest vào thư mục đó (đã gặp thật: WinError 3).
    """
    root = Path(root or ROOT_DIR)
    staging = Path(staging)
    staging.mkdir(parents=True, exist_ok=True)
    staged = []
    for row in rows:
        if row["class"] not in IN_ZIP:
            continue
        target = staging / row["package_path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        if row["package_path"] == MARKER_NAME:
            target.write_bytes(b"")         # file đánh dấu là file RỖNG, đúng như gói cũ
        else:
            shutil.copy2(str(source_path(row, root)), str(target))
        staged.append(row["package_path"])
    return staged


def zip_package(staging, zip_path):
    """Nén thư mục tạm thành gói để gửi. File trong gói sắp theo tên để dễ so giữa hai gói."""
    staging, zip_path = Path(staging), Path(zip_path)
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    files = sorted(path for path in staging.rglob("*") if path.is_file())
    with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(str(path), path.relative_to(staging).as_posix())
    return zip_path


def zip_name(number, sha=None, today=None):
    """Tên file gói: số gói, commit lúc đóng gói (7 ký tự) và NGÀY gửi.

    Notebook trong gói đã ghim commit riêng, nhưng dữ liệu và README thì không, nên tên gói ghi commit
    lúc đóng gói là cách tra lại về sau. Ngày gửi để hai gói cùng nội dung nhưng gửi cách xa nhau không
    bị nhìn nhầm là một.
    """
    short = (sha or "")[:7] or "nogit"
    stamp = (today or datetime.date.today()).strftime("%y%m%d")
    return "SentimentX-goi-{:03d}-{}-{}.zip".format(number, short, stamp)


def report(rows, number, flags, log=print):
    """In ra gói sẽ gửi gì, và cảnh báo đỏ nếu có. Trả số lượng từng lớp.

    Đây là thứ người gửi đọc để duyệt trước khi gửi: từng file mới/đổi, những gì người nhận phải
    xoá, và những file không gửi lại vì y nguyên.
    """
    counts = {name: 0 for name in CLASSES}
    for row in rows:
        counts[row["class"]] += 1
    log("Gói số     : {:03d}".format(number))
    log("Ứng viên   : {} file ({} new, {} changed, {} kept, {} deleted)".format(
        len(rows), counts[CLASS_NEW], counts[CLASS_CHANGED], counts[CLASS_KEPT],
        counts[CLASS_DELETED]))
    for name, title in ((CLASS_NEW, "MỚI"), (CLASS_CHANGED, "ĐỔI")):
        for row in [item for item in rows if item["class"] == name]:
            log("  {:<7} {} ({:.1f} KB)".format(title, row["package_path"],
                                                int(row["size"] or 0) / 1024.0))
    deleted = [row for row in rows if row["class"] == CLASS_DELETED]
    if deleted:
        log("  NGƯỜI NHẬN CẦN XOÁ {} mục:".format(len(deleted)))
        for row in deleted:
            log("    {} (đã gửi ở gói {})".format(row["package_path"], row["sent_package"]))
    if counts[CLASS_KEPT]:
        log("  ({} file y nguyên: không gửi lại)".format(counts[CLASS_KEPT]))
    if flags:
        log("")
        log("!!! CẢNH BÁO ĐỎ ({} mục):".format(len(flags)))
        for line in flags:
            log("  - " + line)
        log("")
        log(RED_ACTION)
    return counts


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Dựng gói bàn giao tăng dần: chỉ chứa file mới hoặc đã đổi.",
        epilog="Gói zip nằm ở handover/out/ (không vào git); sổ nằm trong handover/ (vào git).")
    parser.add_argument("--number", default=None,
                        help="Số gói, ví dụ 002 (mặc định: số kế tiếp sau các gói đang có).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Chỉ in ra nội dung gói, không ghi sổ và không nén.")
    parser.add_argument("--allow-red", action="store_true",
                        help="Vẫn gửi dù có file dữ liệu đã gửi bị đổi nội dung (có ghi chú).")
    parser.add_argument("--no-zip", action="store_true", help="Chỉ ghi sổ, không nén gói.")
    parser.add_argument("--root", default=None, help="Gốc repo (mặc định: gốc thật).")
    parser.add_argument("--data-root", default=None, help="Gốc dữ liệu (mặc định: <repo>/data).")
    parser.add_argument("--handover", default=None, help="Thư mục sổ (mặc định: <repo>/handover).")
    parser.add_argument("--out", default=None, help="Nơi để gói zip (mặc định: <handover>/out).")
    return parser.parse_args(argv)


def main(argv=None, log=print, collector=None):
    """Dựng một gói. Trả mã thoát: 0 xong, 2 lỗi cây/sổ/tham số, 3 cảnh báo đỏ.

    `collector` là điểm tiêm cho test: thay hàm dò ứng viên bằng một danh sách dựng sẵn thì kiểm
    được luồng gói (bốn lớp, cảnh báo đỏ, sổ, zip) mà không cần dữ liệu thật.
    """
    args = parse_args(argv)
    root = Path(args.root) if args.root else paths.root()
    data_root = Path(args.data_root) if args.data_root else paths.data_root()
    handover = Path(args.handover) if args.handover else root / HANDOVER_DIRNAME
    out_dir = Path(args.out) if args.out else handover / OUT_DIRNAME
    ledger_path = handover / LEDGER_CSV
    readme = handover / PACKAGE_README

    try:
        ledger = read_ledger(ledger_path)
        entries = (collector or collect)(root=root, data_root=data_root, readme=readme, log=log)
        rows = classify(entries, ledger)
        flags = red_flags(rows, ledger)
        number = package_number(args.number, handover / PACKAGES_DIRNAME)
        folder = handover / PACKAGES_DIRNAME / "{:03d}".format(number)
        if folder.exists():
            raise PackageError(
                "Gói {0:03d} đã có ({1}). Số gói là bản ghi của một lần gửi nên không ghi lại được: "
                "sửa gì thì gửi gói MỚI (bỏ --number để lấy số kế tiếp).".format(
                    number, utils.rel(folder)))
    except PackageError as exc:
        log("LỖI: {}".format(exc))
        return 2

    report(rows, number, flags, log=log)
    counts = {name: sum(1 for row in rows if row["class"] == name) for name in CLASSES}

    if flags and not args.allow_red:
        log("")
        log("KHÔNG dựng gói nào. Sửa theo hướng dẫn trên, rồi chạy lại.")
        return 3

    if not counts[CLASS_NEW] and not counts[CLASS_CHANGED] and not counts[CLASS_DELETED]:
        # Gói rỗng thì không có gì để gửi: người nhận đã có đủ mọi thứ. Ghi một gói như vậy chỉ làm
        # sổ dài ra và làm người gửi tưởng đã gửi được cái gì.
        log("")
        log("Không có gì mới để gửi: mọi file trong gói đã gửi rồi và nội dung y nguyên.")
        return 0

    if args.dry_run:
        log("")
        log("--dry-run nên chưa ghi sổ và chưa nén gói.")
        return 0

    # Ghi sổ TRƯỚC khi nén: manifest là thứ đi kèm trong zip cho người nhận biết cần xoá gì.
    write_csv(handover / FILES_CSV, FILES_FIELDS, entries)
    notes = {}
    if flags:
        notes = {line.split(" (")[0]: "CẢNH BÁO ĐỎ: " + line for line in flags}
    manifest_path = write_csv(
        folder / MANIFEST_CSV, MANIFEST_FIELDS,
        [dict(row, note=notes.get(row["package_path"], ""),
              depends_on=depends_on(number)) for row in rows])

    zip_path = None
    if not args.no_zip:
        staging = out_dir / "goi-{:03d}".format(number)
        staged = stage(rows, staging, root=root)
        shutil.copy2(str(manifest_path), str(staging / PACKAGE_MANIFEST))
        zip_path = zip_package(staging, out_dir / zip_name(number, repo.current_sha()))
        shutil.rmtree(str(staging))
        log("")
        log("Trong gói  : {} file (kèm {} của người nhận)".format(
            len(staged), PACKAGE_MANIFEST))
        log("Gói        : {}".format(utils.rel(zip_path)))

    write_csv(ledger_path, LEDGER_FIELDS,
              sorted(update_ledger(ledger, rows, number, sent_at()).values(),
                     key=lambda row: row["package_path"]))
    log("Sổ         : {} · {}".format(utils.rel(handover / FILES_CSV),
                                     utils.rel(ledger_path)))
    log("Manifest   : {}".format(utils.rel(manifest_path)))
    log("")
    log("Bước tiếp  : git add handover && git commit -m \"chore(handover): gói {:03d}\"".format(
        number))
    log("             Gửi {} cho người nhận; nếu họ đã có gói trước thì giải nén đè lên.".format(
        zip_path.name if zip_path else "sổ (chưa nén gói)"))
    return 0


def sent_at():
    """Thời điểm gửi, ghi vào sổ: biết gói nào cũ hơn gói nào khi phải tra lại."""
    return datetime.datetime.now().isoformat(timespec="seconds")


if __name__ == "__main__":
    raise SystemExit(main())
