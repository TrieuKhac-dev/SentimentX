# -*- coding: utf-8 -*-
"""Ghim bản code vào cell đầu của notebook thí nghiệm.

CÁCH DÙNG
    python scripts/pin.py qwen3-4b-instruct-2507/prompt-cot/exp001
    python scripts/pin.py <model>/<method>/<expNNN> --sha <commit>      # mặc định: HEAD
    python scripts/pin.py <model>/<method>/<expNNN> --dry-run           # chỉ in ra, không ghi

VÌ SAO CELL ĐẦU CHỈ CÓ HẰNG SỐ
Cell đầu chứa `REPO_URL`, `REPO_BRANCH`, `REPO_SHA`, `EXP_DIR`. Phần kéo code nằm ở cell
bootstrap do `templates/` sinh ra và gọi `src/repo.prepare()`. Tách như vậy để đổi CÁCH kéo code
thì không phải ghim lại mọi notebook đã giao, còn thứ phải đổi theo từng thí nghiệm (bản code nào,
thí nghiệm nào) thì nằm đúng một chỗ.

HAI VIỆC KIỂM TRƯỚC KHI GHI
    1. Commit đã ghim phải nằm trên nhánh cho phép (`configs/experiments/repo.yaml`). Chưa thì
       CẢNH BÁO: kết quả chạy ra không dùng được cho tới khi commit đó lên nhánh (01_flow.md).
    2. Cây làm việc phải sạch NGOÀI file notebook: commit ghim chỉ được đổi đúng một file, nếu
       không thì không ai biết commit đó còn chứa gì.

VÌ SAO KHÔNG BẮT BUỘC `nbformat`
Việc ở đây là thay nguồn của ĐÚNG một ô, nên `json` của thư viện chuẩn là đủ và lệnh ghim chạy
được trên mọi máy. Nếu máy có `nbformat` thì script còn KIỂM cấu trúc notebook trước khi ghi -
thiếu nó thì vẫn ghi, kèm một dòng nhắc.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Trên Windows, console mặc định có thể không phải UTF-8 (ví dụ cp1252),
# khiến việc in tiếng Việt bị lỗi. Ép stdout/stderr sang UTF-8.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from src import experiments, paths, repo, utils

NOTEBOOK = "notebook.ipynb"
MARKER = "# --- BẢN CODE ĐÃ GHIM (do scripts/pin.py ghi; sửa tay sẽ bị ghi đè) ---"


class PinError(Exception):
    """Không ghim được: thiếu notebook, sha sai, hoặc notebook hỏng."""


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Ghi REPO_URL/REPO_BRANCH/REPO_SHA/EXP_DIR vào cell đầu của notebook.")
    parser.add_argument("experiment", metavar="<model>/<method>/<expNNN>",
                        help="Thư mục thí nghiệm, tính từ gốc repo.")
    parser.add_argument("--sha", default=None, help="Commit cần ghim (mặc định: HEAD).")
    parser.add_argument("--url", default=None, help="Ghi đè địa chỉ repo (mặc định: repo.yaml).")
    parser.add_argument("--branch", default=None, help="Ghi đè nhánh (mặc định: repo.yaml).")
    parser.add_argument("--allow-dirty", action="store_true",
                        help="Cho phép cây làm việc có file khác đang sửa.")
    parser.add_argument("--dry-run", action="store_true", help="Chỉ in ra, không ghi file.")
    return parser.parse_args(argv)


def experiment_parts(text):
    """Tách `<model>/<method>/<expNNN>` thành ba phần. Sai định dạng thì báo lỗi rõ."""
    parts = [part for part in str(text).replace("\\", "/").split("/") if part]
    if len(parts) != 3:
        raise PinError("Thí nghiệm phải ghi dạng <model>/<method>/<expNNN>, đang là {!r}.".format(
            text))
    return parts[0], parts[1], parts[2]


def notebook_path(experiment):
    """Đường dẫn notebook của một thí nghiệm."""
    model, method, exp_id = experiment_parts(experiment)
    return experiments.experiment_dir(model, method, exp_id) / NOTEBOOK


def pinned_lines(url, branch, sha, experiment):
    """Nguồn của cell đầu: bốn hằng số, không có việc gì khác."""
    return [
        MARKER + "\n",
        "REPO_URL = {!r}\n".format(url),
        "REPO_BRANCH = {!r}\n".format(branch),
        "REPO_SHA = {!r}\n".format(sha),
        "EXP_DIR = {!r}\n".format(experiment),
    ]


def read_notebook(path):
    """Đọc notebook. File thiếu hoặc JSON hỏng thì báo lỗi kèm việc cần làm."""
    if not path.is_file():
        raise PinError("Chưa có {}. Tạo thí nghiệm trước (xem templates/ trong repo).".format(
            utils.rel(path)))
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise PinError("{} không phải notebook hợp lệ: {}.".format(
            utils.rel(path), exc)) from exc


def validate(nb, path):
    """Kiểm cấu trúc notebook bằng `nbformat` nếu máy có. Trả về danh sách cảnh báo."""
    try:
        import nbformat
    except ImportError:
        return ["Máy chưa có `nbformat` nên không kiểm cấu trúc notebook (vẫn ghi bình thường)."]
    try:
        nbformat.validate(nb)
    except Exception as exc:  # noqa: BLE001 - nbformat ném nhiều kiểu lỗi khác nhau
        raise PinError("Notebook {} không hợp lệ: {}. Sửa hoặc tạo lại từ templates.".format(
            utils.rel(path), exc)) from exc
    return []


def update(nb, lines):
    """Ghi nguồn đã ghim vào notebook. Trả về (notebook, có thay ô cũ hay không).

    Ô cũ được TÌM THEO DẤU, không theo vị trí: người dùng có thể đã di chuyển ô, và ghim lại phải
    cập nhật đúng ô đó chứ không thêm một ô thứ hai.
    """
    cells = nb.setdefault("cells", [])
    source = list(lines)
    for cell in cells:
        if cell.get("cell_type") == "code" and MARKER in "".join(cell.get("source") or []):
            cell["source"] = source
            cell["execution_count"] = None
            cell["outputs"] = []
            return nb, True
    cells.insert(0, {"cell_type": "code", "execution_count": None, "metadata": {},
                     "outputs": [], "source": source})
    return nb, False


def write_notebook(path, nb):
    """Ghi notebook theo đúng dạng Jupyter: JSON thụt lề, kết thúc bằng một dòng trống."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(nb, ensure_ascii=False, indent=1) + "\n")
    return path


def parse_porcelain(output, keep=()):
    """Đọc `git status --porcelain` thành danh sách đường dẫn đang thay đổi.

    `keep` là các đường dẫn được phép thay đổi (chính file notebook đang ghim).
    """
    keep = set(keep)
    dirty = []
    for line in (output or "").splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip().strip('"')
        if " -> " in path:
            path = path.split(" -> ")[-1].strip()
        if path and path not in keep:
            dirty.append(path)
    return dirty


def working_tree(root, keep=()):
    """Các file đang thay đổi trong cây làm việc, trừ đường dẫn được phép."""
    code, output = repo.run_git(["status", "--porcelain"], cwd=root)
    return parse_porcelain(output, keep) if code == 0 else []


def has_pinned_cell(nb):
    """Notebook đã có ô ghim nào chưa."""
    return any(cell.get("cell_type") == "code" and MARKER in "".join(cell.get("source") or [])
               for cell in nb.get("cells") or [])


def main(argv=None):
    args = parse_args(argv)
    try:
        path = notebook_path(args.experiment)
        settings = experiments.shared("repo")
        url = args.url or settings.get("url")
        branch = args.branch or settings.get("branch")
        allowed = list(settings.get("allowed_branches") or [])
        if not url:
            raise PinError("Thiếu địa chỉ repo: điền `url` trong configs/experiments/repo.yaml.")
        if allowed and branch not in allowed:
            raise PinError(
                "Nhánh {!r} không có trong `allowed_branches` ({}). Sửa "
                "configs/experiments/repo.yaml hoặc truyền --branch.".format(
                    branch, ", ".join(allowed)))
        sha = args.sha or repo.current_sha()
        if not sha:
            raise PinError(
                "Không đọc được commit hiện tại. Thư mục này có phải repo git không?")
        lines = pinned_lines(url, branch, sha, args.experiment)
        notebook = read_notebook(path)
        warnings = validate(notebook, path)
    except (PinError, experiments.ExperimentError) as exc:
        print("LỖI: {}".format(exc))
        return 2

    # Commit phải nằm trên nhánh cho phép; chưa thì cảnh báo, vì kết quả chạy ra không dùng được.
    ref = "origin/" + str(branch)
    if repo.ref_exists(ref):
        on_branch = repo.is_ancestor(sha, ref)
    else:
        on_branch = None
        warnings.append("Chưa có {} trong repo nên chưa kiểm được commit có nằm trên nhánh.".format(
            ref))
    if on_branch is False:
        warnings.append("Commit {} chưa nằm trên {}. Đẩy lên nhánh rồi ghim lại.".format(
            sha[:12], ref))

    dirty = working_tree(paths.root(), keep=[utils.rel(path)])
    if dirty:
        message = "Cây làm việc còn {} file đang thay đổi: {}".format(
            len(dirty), ", ".join(dirty[:5]))
        if args.allow_dirty:
            warnings.append(message)
        else:
            print("LỖI: {}".format(message))
            print("      Commit ghim chỉ được đổi đúng file notebook. Dọn trước, hoặc thêm "
                  "--allow-dirty.")
            return 2

    print("Thí nghiệm : {}".format(args.experiment))
    print("Notebook   : {}".format(utils.rel(path)))
    print("Repo       : {} (nhánh {})".format(url, branch))
    print("Commit     : {}".format(sha))
    print("Trên nhánh : {}".format({True: "có", False: "KHÔNG", None: "chưa kiểm được"}[on_branch]))
    print("Ô ghim      : {}".format("đã có, sẽ cập nhật" if has_pinned_cell(notebook)
                                    else "chưa có, sẽ thêm vào đầu notebook"))
    for item in warnings:
        print("  cảnh báo: {}".format(item))

    if args.dry_run:
        print("\n--dry-run nên chưa ghi gì. Nội dung ô đầu sẽ là:")
        for line in lines:
            print("    " + line.rstrip())
        return 0

    notebook, replaced = update(notebook, lines)
    write_notebook(path, notebook)
    print("\nĐã {} ô ghim trong {}.".format("cập nhật" if replaced else "thêm",
                                        utils.rel(path)))
    print("Bước tiếp: ghi lại file notebook vào git (chỉ một file) rồi đẩy lên nhánh {}.".format(
        branch))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


