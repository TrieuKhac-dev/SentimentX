# -*- coding: utf-8 -*-
"""Dựng lại ô của MỌI notebook thí nghiệm theo bản mẫu hiện tại. Dùng MỘT LẦN rồi xoá.

    python scripts/migrate_notebooks_5b.py                 # xem trước rồi hỏi y/n
    python scripts/migrate_notebooks_5b.py --dry-run        # chỉ in ra (mã thoát 0)
    python scripts/migrate_notebooks_5b.py --yes            # ghi luôn, không hỏi
    python scripts/migrate_notebooks_5b.py --exp qwen3-0.6b/prompt-cot/exp001

MÃ THOÁT: 0 xong · 1 người dùng trả lời KHÔNG · 2 thiếu/sai cờ, hoặc không terminal mà không `--yes`.

Giữ nguyên: ô GHIM, `EXP_DIR` theo thư mục thí nghiệm, và ô riêng của thí nghiệm thì bị IN RA chứ không
xoá im lặng. Chi tiết + cách lấy lại script: `docs/00_workflow/10_template_notebook.md`.
"""

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from src.experiments import experiments
from src.workflow import notebooks
from src.core import paths, utils

TEMPLATE = ("experiment", "notebook.ipynb")
NOTEBOOK = "notebook.ipynb"


class MigrateError(Exception):
    """Không dựng lại được: thiếu bản mẫu, notebook hỏng, hoặc thí nghiệm không tồn tại."""


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Dựng lại ô của notebook thí nghiệm theo bản mẫu (giữ ô GHIM + EXP_DIR).")
    parser.add_argument("--exp", default=None, metavar="<model>/<method>/<expNNN>",
                        help="Chỉ dựng lại MỘT thí nghiệm (mặc định: tất cả).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Chỉ in ra sẽ đổi gì, không ghi file nào.")
    parser.add_argument("--yes", action="store_true",
                        help="Không hỏi lại (bắt buộc khi chạy không có terminal).")
    return parser.parse_args(argv)


def template_notebook():
    """Notebook bản mẫu, và nó PHẢI có ô GHIM (thiếu thì mọi notebook sẽ mất ô ghim)."""
    path = paths.templates_dir().joinpath(*TEMPLATE)
    if not path.is_file():
        raise MigrateError("Thiếu bản mẫu {}.".format(utils.rel(path)))
    notebook = notebooks.read(path)
    if notebooks.pinned_cell(notebook) is None:
        raise MigrateError("Bản mẫu {} không có ô GHIM.".format(utils.rel(path)))
    return notebook


def targets(only=None):
    """Các thí nghiệm cần dựng lại, sắp theo (model, method, exp)."""
    if only:
        parts = [part for part in str(only).replace("\\", "/").split("/") if part]
        if len(parts) != 3:
            raise MigrateError(
                "`--exp` phải ghi dạng <model>/<method>/<expNNN>, đang là {!r}.".format(only))
        if tuple(parts) not in experiments.list_experiments(parts[0], parts[1]):
            raise MigrateError("Không có thí nghiệm {!r} (thiếu config.yaml?).".format(only))
        return [tuple(parts)]
    return experiments.list_experiments()


def rebuild(notebook, template, experiment):
    """Notebook mới: ô GHIM giữ nguyên, các ô còn lại lấy từ bản mẫu; `EXP_DIR` đặt lại."""
    pinned = notebooks.pinned_cell(notebook, required=True)
    cells = [pinned]
    cells.extend(cell for cell in template["cells"]
                 if notebooks.MARKER not in notebooks.source_of(cell))
    result = dict(notebook)
    result["cells"] = cells
    return notebooks.set_exp_dir(result, experiment)


def extra_cells(notebook, template):
    """Ô riêng của thí nghiệm: có trong notebook mà không có trong bản mẫu (không tính ô GHIM)."""
    known = {notebooks.source_of(cell).strip() for cell in template["cells"]}
    return [source for source in (notebooks.source_of(cell).strip() for cell in notebook["cells"])
            if source and source not in known]


def main(argv=None):
    args = parse_args(argv)
    try:
        template = template_notebook()
        items = targets(args.exp)
    except (MigrateError, experiments.ExperimentError, notebooks.NotebookError) as exc:
        print("LỖI: {}".format(exc))
        return 2
    if not items:
        print("Không có thí nghiệm nào để dựng lại.")
        return 0

    plans = []
    for model_id, method, exp_id in items:
        experiment = "{}/{}/{}".format(model_id, method, exp_id)
        path = paths.experiment_dir(model_id, method, exp_id) / NOTEBOOK
        if not path.is_file():
            print("LỖI: thiếu {}".format(utils.rel(path)))
            return 2
        try:
            notebook = notebooks.read(path)
            updated = rebuild(notebook, template, experiment)
        except notebooks.NotebookError as exc:
            print("LỖI: {}".format(exc))
            return 2
        plans.append((experiment, path, notebook, updated))

    print("Bản mẫu: {} · {} notebook".format(
        utils.rel(paths.templates_dir().joinpath(*TEMPLATE)), len(plans)))
    for experiment, _, notebook, updated in plans:
        print("  {:<44} ô: {} -> {}".format(experiment, len(notebook["cells"]),
                                            len(updated["cells"])))
        for source in extra_cells(notebook, template):
            print("     Ô KHÔNG CÓ TRONG BẢN MẪU (sẽ bị thay): {!r}".format(source[:80]))

    if args.dry_run:
        print("\n--dry-run nên chưa ghi gì.")
        return 0
    if not args.yes:
        if not sys.stdin.isatty():
            print("\nLỖI: không có terminal để hỏi, nên cần truyền --yes (hoặc --dry-run).")
            return 2
        if input("\nGhi {} notebook? [y/N] ".format(len(plans))).strip().lower() not in ("y", "yes"):
            print("Không ghi gì.")
            return 1

    for _, path, _, updated in plans:
        notebooks.write(path, updated)
        print("đã ghi {}".format(utils.rel(path)))
    print("\nBước tiếp: ghim lại CẢ BỘ bằng `pin.py ... --allow-dirty` rồi commit CÙNG LƯỢT.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
