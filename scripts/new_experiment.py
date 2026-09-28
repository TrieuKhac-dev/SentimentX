# -*- coding: utf-8 -*-
"""Tạo một thí nghiệm mới từ `templates/experiment/`.

CÁCH DÙNG
    python scripts/new_experiment.py --model qwen3-4b-instruct-2507 --method prompt-cot
    python scripts/new_experiment.py --model ... --method ... --exp-id exp005 --parent qwen3-4b-instruct-2507/prompt-cot/exp004
    python scripts/new_experiment.py --model ... --method ... --dry-run      # chỉ in ra

VÌ SAO PHẢI CÓ CÔNG CỤ NÀY, KHÔNG CHÉP TAY
Ba file phải nói cùng một chuyện: `config.yaml` ghi `exp_id` nào thì ô GHIM trong notebook phải
trỏ đúng `EXP_DIR` đó, và số `expNNN` không được trùng thí nghiệm đang có. Chép tay là ba chỗ lệch
nhau lúc nào không biết - mà notebook sai `EXP_DIR` thì kết quả ghi vào thư mục của thí nghiệm
KHÁC, vẫn ra số bình thường.

BA VIỆC KIỂM TRƯỚC KHI TẠO
    1. Cây làm việc phải SẠCH: còn thay đổi chưa commit thì dừng - commit tạo thí nghiệm chỉ được chứa
       thí nghiệm mới, không được mang theo việc đang làm dở. Ở `--dry-run` thì MIỄN điều kiện này,
       vì chế độ đó không ghi gì; cờ `--allow-dirty` là đường thoát khi tạo thật (khi đó có cảnh báo).
    2. `git fetch origin <nhánh>` (nhánh ở `configs/experiments/repo.yaml`). Fetch hỏng (mất mạng)
       thì chỉ CẢNH BÁO rồi đi tiếp.
    3. Nhánh hiện tại phải CHỨA `origin/<nhánh>`, và số `expNNN` kế tiếp tính trên cả thí nghiệm đã
       nằm trên nhánh đó - hai người làm song song trên hai máy không thể cùng nhận một số
       (docs/00_workflow/01_flow.md).

NÓ KHÔNG TỰ GHIM COMMIT
Tạo xong, xem lại config (dataset, roles, n, prompt, examples) rồi chạy
`python scripts/pin.py <model>/<method>/<expNNN>`. Tách hai việc vì config phải được con người
xem trước khi commit được ghim vào notebook.
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

from src import experiments, model_config, notebooks, paths, repo, utils

TEMPLATE_DIR = ("experiment",)
FILES = ("config.yaml", "README.md", "notebook.ipynb")
CONFIG = "config.yaml"
NOTEBOOK = "notebook.ipynb"


class NewExperimentError(Exception):
    """Không tạo được: thiếu bản mẫu/config model, thí nghiệm đã có, hoặc nhánh chưa lên remote."""


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Tạo thư mục thí nghiệm mới từ templates/experiment/ và chọn số expNNN kế tiếp.")
    parser.add_argument("--model", required=True,
                        help="Tên model, phải trùng configs/models/<model_id>.yaml.")
    parser.add_argument("--method", required=True, help="Tên phương pháp, ví dụ prompt-cot.")
    parser.add_argument("--exp-id", dest="exp_id", default=None,
                        help="Số thí nghiệm (mặc định: số kế tiếp của --model/--method).")
    parser.add_argument("--parent", default=None,
                        help="Thí nghiệm làm lại từ đâu, dạng <model>/<method>/<expNNN>; "
                             "'none' nếu là bản gốc (mặc định: none).")
    parser.add_argument("--notes", dest="notes", default=None,
                        help="Mô tả ngắn, ghi vào `notes` của config.yaml. Sửa sau cũng được. "
                             "Tên cờ trùng tên khoá trong config; tên cũ `--title` đã bỏ.")
    parser.add_argument("--branch", default=None,
                        help="Nhánh đã ghim cần kiểm (mặc định: repo.yaml).")
    parser.add_argument("--dry-run", action="store_true", help="Chỉ in ra, không ghi file.")
    parser.add_argument("--allow-dirty", action="store_true",
                        help="Cho phép cây làm việc có file khác đang sửa. Mặc định là TỪ CHỐI: commit "
                             "tạo thí nghiệm chỉ được chứa thí nghiệm mới. Cờ này để soi công cụ giữa "
                             "lúc đang làm dở (giống `pin.py --allow-dirty`).")
    return parser.parse_args(argv)


def clean_parent(text):
    """Giá trị `parent`: None khi để trống, ngược lại phải đủ `<model>/<method>/<expNNN>`."""
    if not text or str(text).strip().lower() in ("none", "null", "-"):
        return None
    parts = [part for part in str(text).replace("\\", "/").split("/") if part]
    if len(parts) != 3:
        raise NewExperimentError(
            "--parent phải ghi dạng <model>/<method>/<expNNN>, hoặc 'none' nếu là bản gốc.")
    return "/".join(parts)


def config_text(template, model_id, method, exp_id, parent, notes=None):
    """Config của thí nghiệm: sửa ĐÚNG năm dòng định danh, giữ nguyên phần còn lại của bản mẫu.

    Sửa theo dòng và kiểm dòng đó CÓ THẬT, thay vì ghép lại cả file: bản mẫu còn nhiều ghi chú giải
    thích, ghép lại là mất hết và tạo nguồn sự thật thứ hai cho các khoá khác.

    `notes` là mô tả ngắn (một dòng, không xuống dòng) và được ghi bằng JSON để tiêu đề có dấu hai
    chấm hay dấu ngoặc kép vẫn là YAML hợp lệ.
    """
    wanted = {"exp_id": exp_id, "model": model_id, "method": method,
              "parent": "null" if parent is None else parent,
              "notes": "null" if not notes else json.dumps(str(notes).strip(),
                                                           ensure_ascii=False)}
    lines, seen = [], set()
    for line in template.splitlines():
        key = line.split(":", 1)[0].strip() if ":" in line else ""
        if key in wanted and not line.startswith((" ", "\t")):
            lines.append("{}: {}".format(key, wanted[key]))
            seen.add(key)
        else:
            lines.append(line)
    missing = sorted(set(wanted) - seen)
    if missing:
        raise NewExperimentError(
            "Bản mẫu {} thiếu dòng {}. Sửa templates/experiment/config.yaml trước.".format(
                CONFIG, ", ".join(missing)))
    return "\n".join(lines) + "\n"


def load_templates():
    """Nội dung ba file bản mẫu, đọc một lần."""
    directory = paths.templates_dir().joinpath(*TEMPLATE_DIR)
    if not directory.is_dir():
        raise NewExperimentError("Thiếu thư mục bản mẫu {}.".format(utils.rel(directory)))
    files = {}
    for name in FILES:
        source = directory / name
        if not source.is_file():
            raise NewExperimentError("Thiếu bản mẫu {}.".format(utils.rel(source)))
        files[name] = source.read_text(encoding="utf-8")
    return directory, files


def main(argv=None):
    args = parse_args(argv)
    try:
        model_id = str(args.model or "").strip()
        method = str(args.method or "").strip()
        if not model_id or not method:
            raise NewExperimentError("Thiếu --model hoặc --method.")
        if not model_config.config_path(model_id).is_file():
            raise NewExperimentError(
                "Chưa có {}: tạo config của model trước, vì thí nghiệm kế thừa lớp model.".format(
                    utils.rel(model_config.config_path(model_id))))

        # BA VIỆC KIỂM TRƯỚC KHI TẠO (docs/00_workflow/01_flow.md):
        #   1. cây làm việc phải SẠCH - commit tạo thí nghiệm chỉ được chứa thí nghiệm mới;
        #   2. cập nhật ref `origin/<nhánh>` rồi tính `expNNN` trên CẢ nhánh đó, để hai người làm song
        #      song không chọn trùng số;
        #   3. nhánh hiện tại phải CHỨA `origin/<nhánh>`, nếu không thì commit ghim không nằm trên nhánh
        #      đã ghim và kết quả chạy ra không dùng được.
        # `--dry-run` KHÔNG ghi gì, nên điều kiện "commit chỉ chứa thí nghiệm mới" không áp dụng: ở chế
        # độ soi công cụ thì cây bẩn là chuyện bình thường, không cần cảnh báo.
        dirty = [] if args.dry_run else repo.worktree_dirty()
        if dirty and not args.allow_dirty:
            raise NewExperimentError(
                "Cây làm việc còn {} file đang thay đổi: {}. Commit hoặc cất chúng trước, vì commit tạo "
                "thí nghiệm phải chỉ chứa thí nghiệm mới (muốn soi công cụ giữa lúc đang làm dở thì "
                "thêm --allow-dirty).".format(len(dirty), ", ".join(dirty[:3])))
        if dirty:
            print("CẢNH BÁO: cây làm việc còn {} file đang thay đổi - commit tạo thí nghiệm sẽ mang "
                  "theo chúng.".format(len(dirty)))
        settings = experiments.shared("repo")
        branch = args.branch or settings.get("branch")
        ref = "origin/{}".format(branch)
        code, output = repo.run_git(["fetch", "origin", branch])
        if code != 0:
            # Mất mạng không phải lỗi của người tạo thí nghiệm: nói ra rồi đi tiếp - nhưng khi đó số
            # `expNNN` chỉ tính trên cây làm việc và nhánh hiện tại chưa được kiểm.
            print("CẢNH BÁO: không fetch được `{}` ({}). Số expNNN chỉ tính trên cây làm việc, và chưa "
                  "kiểm được nhánh hiện tại có chứa `{}`.".format(
                      branch, output.splitlines()[0] if output else "không rõ lỗi", ref))
        if not repo.ref_exists(ref):
            raise NewExperimentError(
                "Chưa có {} trong repo: nhánh đã ghim phải có trên remote, nếu không thì commit "
                "ghim không nằm trên nhánh và kết quả chạy ra không dùng được "
                "(docs/00_workflow/01_flow.md). Đẩy nhánh lên rồi chạy lại lệnh này.".format(ref))
        if code == 0 and not repo.is_ancestor(repo.current_sha(), ref):
            raise NewExperimentError(
                "Nhánh hiện tại CHƯA chứa {}: merge nhánh đó vào trước rồi chạy lại, vì commit ghim "
                "phải nằm trên nhánh đã ghim (docs/00_workflow/01_flow.md).".format(ref))

        exp_id = str(args.exp_id or experiments.next_exp_id(model_id, method, ref=ref)).strip()
        if not (exp_id.startswith("exp") and exp_id[3:].isdigit()):
            raise NewExperimentError("--exp-id phải có dạng expNNN, ví dụ exp002.")
        parent = clean_parent(args.parent)
        experiment = "{}/{}/{}".format(model_id, method, exp_id)
        target = experiments.experiment_dir(model_id, method, exp_id)
        if target.exists():
            raise NewExperimentError("Đã có {} - không ghi đè. Chọn --exp-id khác.".format(
                utils.rel(target)))

        directory, files = load_templates()
        config = config_text(files[CONFIG], model_id, method, exp_id, parent, args.notes)
        notebook = notebooks.read(directory / NOTEBOOK)
        notebooks.set_exp_dir(notebook, experiment)
    except (NewExperimentError, experiments.ExperimentError, notebooks.NotebookError,
            model_config.ModelConfigError, ValueError) as exc:
        print("LỖI: {}".format(exc))
        return 2

    print("Thí nghiệm : {}".format(experiment))
    print("Thư mục    : {}".format(utils.rel(target)))
    print("Bản mẫu    : {}".format(utils.rel(directory)))
    print("Nhánh ghim : {} (đã có trên remote)".format(ref))
    print("Nối tiếp   : {}".format(parent or "không (bản gốc)"))

    if args.dry_run:
        print("\n--dry-run nên chưa ghi gì. config.yaml sẽ là:")
        for line in config.splitlines():
            print("    " + line)
        return 0

    target.mkdir(parents=True, exist_ok=True)
    (target / CONFIG).write_text(config, encoding="utf-8")
    (target / "README.md").write_text(files["README.md"], encoding="utf-8")
    notebooks.write(target / NOTEBOOK, notebook)
    print("\nĐã tạo {} gồm {}.".format(utils.rel(target), ", ".join(FILES)))
    print("Bước tiếp: 1) mở {} xem lại dataset, roles, n, prompt, examples;".format(CONFIG))
    print("           2) python scripts/pin.py {}".format(experiment))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

