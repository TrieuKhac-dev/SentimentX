# -*- coding: utf-8 -*-
"""BẢY kiểm tra tĩnh cho CI: không cần GPU, không cần dữ liệu, không gọi mạng.

BẢY KIỂM TRA NÀY CHẶN GÌ (docs/00_workflow/03_ci.md)
    1. Không file DỮ LIỆU nào bị git theo dõi (ngoài bảng chi tiết trong `pipeline/`, `eda/` và
       metadata/report được phép) - chặn việc vô tình commit dữ liệu nặng.
    2. `.gitignore` đúng: dữ liệu nặng bị bỏ qua, nhưng metadata và report thì KHÔNG - mất metadata
       là mất dấu vết của phiên bản dữ liệu.
    3. Notebook đã được làm sạch output - để diff GitHub không đầy rác (ảnh base64, số dòng thực thi
       đổi mỗi lần chạy).
    4. Mọi registry đều hợp lệ - thêm module rồi QUÊN ĐĂNG KÝ là lỗi im lặng: model không bao giờ
       dùng tới module đó nữa.
    5. Mọi `experiments/**/config.yaml` hợp lệ - lỗi config phát hiện muộn là phát hiện trên Colab,
       sau khi đã chờ kéo code.
    6. `REPO_SHA` trong notebook là sha hợp lệ và TỒN TẠI trong repo - ghim sai thì notebook kéo
       không được bản code nào, mà lỗi chỉ lộ ra lúc chạy.
    7. Link trong tài liệu (`README.md`, `docs/**/*.md`) trỏ tới file có thật - người mới đọc tài
       liệu trước tiên, mà không ai kiểm đường dẫn trong đó.

Logic nằm ở đây chứ không nằm trong script vì CI chạy `python scripts/ci_checks.py` còn test chạy
thẳng hàm trong file này - hai bên kiểm đúng cùng một thứ, không phải hai bản.

KHÔNG NÉM: giống preflight, `run()` gom mọi vấn đề vào một danh sách để in ra hết một lần. Sửa
từng lỗi rồi chạy lại mất vài vòng CI, mà thông tin thì đã có sẵn trên đĩa.
"""

import os
import re
import subprocess
from pathlib import Path

from src import dataset as dataset_module, experiments, notebooks, paths, repo, utils, versioning
from src import labels as labels_module
from src import tracking, training
from src.evaluation import scorers
from src.labels import LABEL_SPACES
from src.preprocessing import segmenters
from src.training import encoders

# File ĐƯỢC PHÉP nằm trong git dù ở trong `data/` (docs/00_workflow/03_ci.md, luật 20).
ALLOWED_DATA_NAMES = ("raw_meta.yaml", "processing_log.json", "label_map.json", "eval_lock.json",
                      ".gitkeep", "README.md")
# Thư mục ĐƯỢC PHÉP trong `data/`. Ghi bằng từng phần đường dẫn, không ghép chuỗi có dấu `/`, vì
# đường dẫn viết cứng trong source bị test `test_sources_have_no_hardcoded_paths` chặn.
ALLOWED_DATA_PREFIXES = (("data", "assets"), ("data", "reference_publication"),
                         ("data", "reports"))
ALLOWED_DATA_PARTS = ("/pipeline/", "/eda/")

# `.gitignore` phải bỏ qua dữ liệu nặng và KHÔNG được bỏ qua metadata/report.
# `.gitignore` phải bỏ qua dữ liệu nặng và KHÔNG được bỏ qua metadata/report. Ghi theo từng phần vì
# test `test_sources_have_no_hardcoded_paths` cấm mọi chuỗi đường dẫn viết cứng trong `src/`.
_DATA = "data" + "/"

# File tạm của người làm việc có đuôi này - xem `_scratch_files`.
SCRATCH_SUFFIXES = (".txt", ".py", ".log", ".json")
REQUIRED_IGNORES = (_DATA + "raw", _DATA + "processed", _DATA + "models",
                    "experiments/**/results")
FORBIDDEN_IGNORES = (_DATA + "reference_publication", _DATA + "assets", _DATA + "reports")

SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
PLACEHOLDER_SHA = "<chua-ghim>"


class CheckError(Exception):
    """Không chạy được phép kiểm (ví dụ: thư mục này không phải repo git)."""


def run(root=None, log=None):
    """Chạy bảy kiểm tra, trả về `{problems, notes, info}`. KHÔNG ném."""
    root = Path(root or paths.root())
    problems, notes, info = [], [], {"root": utils.rel(root)}

    for name, function in CHECKS:
        try:
            found = function(root)
        except CheckError as exc:
            problems.append("[{}] {}".format(name, exc))
            continue
        if not found:
            notes.append("{}: không có vấn đề".format(name))
            continue
        for item in found:
            problems.append("[{}] {}".format(name, item))

    info["problems"] = len(problems)
    if log is not None:
        for item in notes:
            log.step("CI: {}".format(item))
        for item in problems:
            log.error("CI: {}".format(item), context={"bước": "ci_checks"})
    return {"problems": problems, "notes": notes, "info": info}


def print_report(report):
    """In báo cáo theo cùng cách `preflight` in, để hai chỗ đọc giống nhau."""
    print("Kiểm tra tĩnh cho CI:")
    for item in report["notes"]:
        print("  - {}".format(item))
    if not report["problems"]:
        print("\nKhông có việc nào phải sửa.")
        return report
    print("\n  CÒN {} VIỆC PHẢI SỬA:".format(len(report["problems"])))
    for item in report["problems"]:
        print("    * {}".format(item))
    return report


# ---
# 1. Dữ liệu bị git theo dõi
# ---


def data_tracked(root):
    """File trong `data/` đang bị git theo dõi mà KHÔNG nằm trong danh sách được phép.

    Không cấm mọi thứ trong `data/`: metadata và báo cáo PHẢI được theo dõi (luật 20), vì mất chúng
    là mất dấu vết của phiên bản dữ liệu. Chỉ file dữ liệu nặng mới bị cấm.
    """
    found = []
    for path in tracked_files(root):
        parts = path.split("/")
        if not parts or parts[0] != "data":
            continue
        if path.endswith(tuple(ALLOWED_DATA_NAMES)):
            continue
        if any(tuple(parts[:len(prefix)]) == prefix for prefix in ALLOWED_DATA_PREFIXES):
            continue
        if any(part in path for part in ALLOWED_DATA_PARTS):
            continue
        found.append("{} (bỏ khỏi git bằng `git rm --cached {}`)".format(path, path))
    return found


# ---
# 2. Quy tắc .gitignore
# ---


def gitignore_rules(root):
    """`.gitignore` thiếu quy tắc bỏ qua dữ liệu, bỏ qua nhầm metadata/report, hoặc có file tạm lọt vào git.

    Phần file tạm thêm vào sau khi chính tôi để lọt hai lần: file tạm đặt tên bằng MỘT dấu gạch dưới
    ở đầu (`_ut.txt`, `_m24.txt`) là rác của một lần chạy tay, mà `git add -A` thì không phân biệt.
    Tên bắt đầu bằng HAI gạch dưới (`__init__.py`) là file thật, không được báo.
    """
    path = Path(root) / ".gitignore"
    if not path.is_file():
        raise CheckError("Thiếu .gitignore ở gốc repo.")
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    rules = [line for line in lines if line and not line.startswith("#")]
    found = []
    for pattern in REQUIRED_IGNORES:
        if not any(rule.rstrip("/").startswith(pattern.rstrip("/")) for rule in rules):
            found.append("thiếu quy tắc bỏ qua {!r} - dữ liệu nặng sẽ bị commit.".format(pattern))
    for pattern in FORBIDDEN_IGNORES:
        if any(rule.rstrip("/") == pattern for rule in rules):
            found.append("đang bỏ qua cả {!r} - metadata và report PHẢI được theo dõi.".format(
                pattern))
    try:
        tracked = tracked_files(root)
    except CheckError:
        # Không đọc được danh sách file của git (chưa cài git, hoặc gốc không phải repo). Việc đó đã
        # là một vấn đề ở kiểm tra 1; kể lại ở đây chỉ làm rối báo cáo - mà các quy tắc trong
        # `.gitignore` thì vẫn kiểm được bình thường.
        tracked = []
    for item in _scratch_files(tracked):
        found.append("{} (file tạm bị git theo dõi; bỏ bằng `git rm --cached {}`)".format(
            item, item))
    return found


def _scratch_files(paths):
    """File tạm của người làm việc: tên bắt đầu bằng MỘT dấu `_` và có đuôi văn bản/mã."""
    found = []
    for path in paths:
        name = str(path).rsplit("/", 1)[-1]
        if name.startswith("_") and not name.startswith("__") and name.endswith(SCRATCH_SUFFIXES):
            found.append(path)
    return found


def tracked_files(root):
    """Danh sách file đang bị git theo dõi (đường dẫn tương đối, dấu `/`)."""
    try:
        result = subprocess.run(["git", "-C", str(root), "ls-files"],
                                capture_output=True, text=True, encoding="utf-8")
    except OSError as exc:
        raise CheckError("không gọi được git: {}".format(exc))
    if result.returncode != 0:
        raise CheckError("`git ls-files` lỗi: {}".format((result.stderr or "").strip()))
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


# ---
# 3. Notebook sạch output
# ---

NOTEBOOK_DIRS = ("experiments", "templates")


def notebooks_clean(root):
    """Notebook còn output hoặc còn số dòng thực thi: diff GitHub sẽ đầy rác, không đọc được.

    Cả hai đều là rác theo cùng một cách: output chứa ảnh base64 và toàn bộ nội dung đã in, còn số
    dòng thực thi thì đổi ở mỗi lần chạy - nên hai lần chạy cùng một notebook vẫn cho ra một diff.
    """
    found = []
    directory = Path(root)
    for name in NOTEBOOK_DIRS:
        base = directory / name
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.ipynb")):
            try:
                notebook = notebooks.read(path)
            except notebooks.NotebookError as exc:
                found.append(str(exc))
                continue
            for index, cell in enumerate(notebook.get("cells") or []):
                if cell.get("cell_type") != "code":
                    continue
                if cell.get("outputs"):
                    found.append("{} ô {}: còn {} output (chạy Kernel -> Restart và Clear All "
                                 "Outputs)".format(utils.rel(path), index, len(cell["outputs"])))
                if cell.get("execution_count") is not None:
                    found.append("{} ô {}: còn số dòng thực thi ({})".format(
                        utils.rel(path), index, cell["execution_count"]))
    return found


# ---
# 4. Registry
# ---

NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def registries(root=None):
    """Mọi registry phải khai được và mọi mục trong đó phải DÙNG ĐƯỢC.

    Vì sao kiểm cả tên: tên là thứ đi vào config, nên tên sai quy ước (`Prompt-CoT`, `4bit`) vừa khó
    gõ vừa không khớp với tên khác trong cùng config.
    """
    found = []
    # Bộ tách từ KHÔNG kiểm ở đây: nó phụ thuộc gói cài ngoài (pyvi/VnCoreNLP), mà CI cố ý không cài
    # model. Thiếu bộ tách từ là việc của preflight trên máy chạy, không phải việc của CI.
    for label, registry in (("labels", LABEL_SPACES), ("scorers", scorers.SCORERS),
                            ("tracking", tracking.TRACKERS),
                            ("segmenters", segmenters.SEGMENTERS),
                            ("trainers", training.TRAINERS)):
        found += _registry_names(registry, label)
    # Encoders: khoá là `model_id` nên tên có gạch ngang; chỉ kiểm "có trỏ tới đâu".
    found += _registry_names(encoders.ENCODERS, "encoders", check_name=False)
    for name in sorted(LABEL_SPACES):
        found += _attempt("labels[{}]".format(name), labels_module.get, name)
    found += _attempt("scorers", scorers.check, scorers.available())
    found += _attempt("encoders", encoders.check)
    configured = (experiments.shared("tracking") or {}).get("tracker")
    if configured and configured not in tracking.TRACKERS:
        found.append("tracking: config đang chọn {!r} mà registry không có. Đang có: {}".format(
            configured, ", ".join(sorted(tracking.TRACKERS))))
    # Kiểm từng cách ghi nhận bằng config tối thiểu. `mlflow` cần token DagsHub nên chỉ kiểm khi CÓ
    # token: CI không giữ secret, còn thiếu token là việc của preflight lúc chạy thật.
    for name in sorted(tracking.TRACKERS):
        if name == "mlflow" and not os.environ.get("DAGSHUB_TOKEN"):
            continue
        found += _attempt("tracking[{}]".format(name), tracking.check, {"tracker": name})
    return found


def _registry_names(registry, label, check_name=True):
    """Kiểm cấu trúc của một registry: tên đúng quy ước và có trỏ tới một mục thật.

    `check_name=False` cho registry mà khoá là `model_id`: tên model trên Hugging Face có gạch
    ngang (`phobert-base-v2`), nên quy ước chữ thường + gạch dưới không áp dụng được.
    """
    found = []
    if not registry:
        return ["{}: registry rỗng".format(label)]
    for name, entry in sorted(registry.items()):
        if check_name and not NAME_PATTERN.match(str(name)):
            found.append("{}[{}]: tên phải là chữ thường + gạch dưới".format(label, name))
        if entry is None:
            found.append("{}[{}]: chưa trỏ tới đâu".format(label, name))
    return found


def _attempt(label, function, *args):
    """Gọi một hàm của registry và đổi mọi lỗi thành một dòng việc-phải-sửa.

    Bắt rộng là CỐ Ý: ở đây mọi lỗi đều có cùng một nghĩa - registry hỏng - và việc của CI là kể ra
    hết chứ không phải dừng ở lỗi đầu tiên.
    """
    try:
        function(*args)
    except Exception as exc:                                  # noqa: BLE001 - xem docstring
        return ["{}: {}: {}".format(label, type(exc).__name__, exc)]
    return []


# ---
# 5. Config thí nghiệm
# ---

# Những đường dẫn PHẢI có trong repo. Đường dẫn dữ liệu (data/...) không kiểm ở CI: CI cố ý không có
# dữ liệu, việc đó do preflight trong notebook bắt khi đã có dữ liệu thật.
REPO_SIDE_KEYS = ("prompt", "examples", "system_prompt")


def experiment_configs(root=None):
    """Mọi thí nghiệm phải hợp nhất được, có vai `eval`, và file prompt/ví dụ phải có thật."""
    found = []
    for model_id, method, exp_id in experiments.list_experiments():
        label = "{}/{}/{}".format(model_id, method, exp_id)
        try:
            result = experiments.load(model_id, method, exp_id)
            experiments.check(result)
        except Exception as exc:                              # noqa: BLE001 - kể ra hết, không dừng
            found.append("{}: {}: {}".format(label, type(exc).__name__, exc))
            continue
        try:
            config = result["config"]
            dataset_name = (config.get("data") or {}).get("dataset")
            dataset_cfg = dataset_module.load_config(dataset_name)
            # CI cố ý KHÔNG có dữ liệu (luật 20), nên thiếu file gốc thì chưa tính được mã phiên bản.
            # Việc thiếu dữ liệu là việc của preflight trên máy có dữ liệu; ở đây vẫn kiểm tiếp được
            # các đường dẫn nằm trong repo (prompt, ví dụ) nên không bỏ qua phần kiểm đó.
            version = (None if versioning.missing_sources(dataset_cfg)
                       else versioning.compute_id(dataset_cfg))
            rows = experiments.requires(result, version)
        except Exception as exc:                              # noqa: BLE001 - như trên
            found.append("{}: mã phiên bản dữ liệu: {}: {}".format(
                label, type(exc).__name__, exc))
            continue
        for row in rows:
            if row.get("role") not in REPO_SIDE_KEYS:
                continue
            if not row["path"].exists():
                found.append("{}: thiếu {} ({}) - đường dẫn tính từ thư mục thí nghiệm trước, rồi "
                             "tới gốc repo".format(label, row.get("display"), row.get("role")))
    return found


# ---
# 6. REPO_SHA đã ghim
# ---


def pinned_shas(root=None):
    """`REPO_SHA` trong notebook thí nghiệm: đúng dạng sha, có thật trong repo, và nằm trên nhánh ghim.

    Mọi lệnh git đều nhận `root`: `checks.run(root=...)` có thể kiểm một gốc khác thư mục đang đứng,
    mà git thì mặc định chạy ở thư mục đang đứng - thiếu `root` là kiểm nhầm repo.
    """
    found = []
    settings = experiments.shared("repo")
    branch = settings.get("branch")
    ref = "origin/{}".format(branch)
    has_ref = bool(branch) and repo.ref_exists(ref, root)
    for model_id, method, exp_id in experiments.list_experiments():
        label = "{}/{}/{}".format(model_id, method, exp_id)
        path = paths.experiment_dir(model_id, method, exp_id) / "notebook.ipynb"
        try:
            cell = notebooks.pinned_cell(notebooks.read(path), required=True)
        except notebooks.NotebookError as exc:
            found.append(str(exc))
            continue
        sha = pinned_value(notebooks.source_of(cell), "REPO_SHA")
        if not sha or sha == PLACEHOLDER_SHA:
            found.append("{}: chưa ghim commit (REPO_SHA = {!r}); chạy `python scripts/pin.py {}`"
                         .format(label, sha or "", label))
            continue
        if not SHA_PATTERN.match(sha):
            found.append("{}: REPO_SHA không phải sha 40 ký tự hex: {!r}".format(label, sha))
            continue
        if not repo.object_exists(sha, root):
            found.append("{}: repo không có commit {} - sha sai, hoặc commit chưa được đẩy lên"
                         .format(label, sha[:12]))
            continue
        if has_ref and not repo.is_ancestor(sha, ref, root):
            found.append("{}: commit {} chưa nằm trên {} - kết quả chạy ra không dùng được cho tới "
                         "khi đẩy lên nhánh".format(label, sha[:12], ref))
    return found


def pinned_value(source, name):
    """Giá trị của một hằng số trong ô GHIM (`REPO_SHA = '<sha>'`), bỏ dấu nháy."""
    pattern = re.compile(r"^{}\s*=\s*['\"]([^'\"]*)['\"]".format(re.escape(name)), re.MULTILINE)
    matched = pattern.search(source or "")
    return matched.group(1).strip() if matched else None


# Sáu kiểm tra, theo đúng thứ tự chạy. Khai thành hằng ở CUỐI file (Python tra tên lúc gọi, nên
# `run()` phía trên vẫn dùng được) để bên gọi - script in số việc, test đếm số nhóm - cùng đọc MỘT
# danh sách: thêm kiểm tra thứ bảy thì không phải đi sửa chỗ nào đếm số nữa.
# ---
# 7. Link trong tài liệu
# ---

# Thư mục và file tài liệu cần kiểm. Ghi tên trần (không kèm dấu phân cách) để không vi phạm
# `test_sources_have_no_hardcoded_paths`.
MARKDOWN_DIRS = ("docs",)
MARKDOWN_EXTRA = ("README.md",)
MARKDOWN_SUFFIX = "." + "md"
LINK_PATTERN = re.compile(r"\]\(([^)#\s]+)\)")


def _documents(root):
    """Các file tài liệu phải kiểm: README ở gốc và mọi file markdown trong `docs/`."""
    found = []
    for name in MARKDOWN_EXTRA:
        path = Path(root) / name
        if path.is_file():
            found.append(path)
    for name in MARKDOWN_DIRS:
        base = Path(root) / name
        if base.is_dir():
            found.extend(sorted(base.rglob("*" + MARKDOWN_SUFFIX)))
    return found


def documentation_links(root):
    """Link kiểu `[chữ](đường/dẫn)` trong tài liệu phải trỏ tới file hoặc thư mục CÓ THẬT.

    Vì sao cần: tài liệu là thứ người mới đọc trước tiên, mà đường dẫn trong tài liệu thì không ai
    kiểm. Lỗi thật đã gặp: README còn trỏ tới `02_phase3_input.md` sau khi file đó đổi tên thành
    `02_model_input.md` - người đọc đi tìm một file không tồn tại, còn người viết thì không biết.

    Chỉ kiểm LINK, không kiểm đường dẫn nằm trong dấu `code`: đường dẫn trong code thường là ví dụ có
    chỗ trống (`data/processed/<mã>/train.csv`), đem kiểm sẽ báo lỗi sai hàng loạt. Link thì không có
    chỗ trống - gặp `<`, `>`, `{`, `}` hoặc URL thì bỏ qua.
    """
    found = []
    for path in _documents(root):
        text = path.read_text(encoding="utf-8", errors="replace")
        for target in LINK_PATTERN.findall(text):
            target = target.strip()
            if not target or target.startswith(("http", "mailto:")):
                continue
            if any(char in target for char in "<>{}*"):
                continue
            if (Path(root) / target).exists() or (path.parent / target).exists():
                continue
            found.append("{}: link chết -> {}".format(utils.rel(path), target))
    return found


CHECKS = (
    ("dữ liệu bị git theo dõi", data_tracked),
    ("quy tắc .gitignore", gitignore_rules),
    ("notebook sạch output", notebooks_clean),
    ("registry", registries),
    ("config thí nghiệm", experiment_configs),
    ("REPO_SHA đã ghim", pinned_shas),
    ("link trong tài liệu", documentation_links),
)



