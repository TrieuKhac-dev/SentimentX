# -*- coding: utf-8 -*-
"""Chạy notebook của một thí nghiệm trên máy cá nhân, KHÔNG cần tiện ích Jupyter.

CÁCH DÙNG
    python scripts/run_notebook.py qwen3-4b-instruct-2507/prompt-cot/exp002
    python scripts/run_notebook.py <...> --limit 8          # chạy thử nhanh, KHÔNG sửa file nào
    python scripts/run_notebook.py <...> --preflight-only    # chỉ tới ô kiểm trước khi chạy
    python scripts/run_notebook.py <...> --keep              # giữ bản clone tạm để soi lại

VÌ SAO CHẠY TRONG BẢN CLONE TẠM, KHÔNG CHECKOUT NGAY TẠI REPO
Notebook chỉ đáng tin khi nó chạy ĐÚNG commit đã ghim (docs/00_workflow/01_flow.md), mà commit đã
ghim thì thường KHÔNG phải bản đang làm dở. Bấm Run all trong Jupyter/VS Code sẽ để bootstrap
`git checkout` commit ghim NGAY TRONG repo: cây làm việc bị đưa về bản cũ, và file notebook trong
cây đó trỏ về commit ghim của ĐỜI TRƯỚC (mỗi lần ghim lại là một commit mới), nên lần bấm sau lùi
thêm một đời code - đã gặp thật ngày 25/09/2026.

Script này kéo commit đã ghim vào một thư mục TẠM rồi chạy ở đó, nên repo của bạn KHÔNG bị đụng:
file chưa commit, file chưa `git add`, thư mục chưa theo dõi đều còn nguyên - không có gì phải
"quay lại" cả, và cuối lượt chạy script tự so lại trạng thái repo để bạn thấy đúng như vậy.

Kết quả vẫn về thẳng repo: `SENTIMENTX_RESULTS_ROOT` trỏ vào `<repo>/experiments`, nên thư mục kết
quả nằm ngay trong repo như mọi lần chạy khác, kèm `run.log` và `run_meta.json`.

LUẬT KÉO CODE VẪN CHỈ CÓ MỘT BẢN: script gọi `src.repo.prepare()` - đúng hàm mà ô bootstrap của
notebook gọi - nên không có bản luật thứ hai để lệch nhau.
"""

import argparse
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Trên Windows, console mặc định có thể không phải UTF-8 (ví dụ cp1252),
# khiến việc in tiếng Việt bị lỗi. Ép stdout/stderr sang UTF-8.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from src import notebooks, paths, repo

NOTEBOOK_NAME = "notebook.ipynb"
CONFIG_NAME = "config.yaml"
CELL_TIMEOUT = 8 * 3600          # giây; một lượt `test` đầy đủ trên GPU 6 GB có thể vài giờ
PIN_KEYS = ("REPO_URL", "REPO_BRANCH", "REPO_SHA", "EXP_DIR")
# Hai gốc đường dẫn và `SENTIMENTX_ENV` do script tự đặt; lấy từ `.env` thì notebook sẽ trỏ sai chỗ.
ROOT_KEYS = ("SENTIMENTX_DATA_ROOT", "SENTIMENTX_RESULTS_ROOT", "SENTIMENTX_ENV")

LIMIT_PRELUDE = '''\
# --- CHẠY THỬ do scripts/run_notebook.py chèn (không có trong file notebook) ---
import src.experiments as _sx_experiments

_sx_original_load = _sx_experiments.load


def _sx_load(model_id, method, exp_id):
    """Nạp cấu hình như thật, rồi ép `n` - chỉ trong RAM, không ghi file nào."""
    result = _sx_original_load(model_id, method, exp_id)
    result["config"]["n"] = {limit}
    return result


_sx_experiments.load = _sx_load
print("[CHẠY THỬ] đã ép n = {limit} (chỉ trong RAM; tên thư mục kết quả có 'n{limit}' nên "
      "không lẫn với lượt chạy đủ)")
'''


class RunNotebookError(Exception):
    """Không chạy được: thiếu notebook/config, không kéo được commit ghim, hoặc kernel không lên."""


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Chạy notebook của một thí nghiệm bằng Jupyter kernel, trong bản clone tạm.")
    parser.add_argument("target", help="`<model_id>/<method>/<expNNN>` hoặc đường dẫn tới notebook.")
    parser.add_argument("--limit", type=int, default=None, metavar="N",
                        help="Ép `n = N` cho lượt chạy thử (chỉ trong RAM, không sửa config).")
    parser.add_argument("--preflight-only", dest="preflight_only", action="store_true",
                        help="Chạy tới ô kiểm trước khi chạy rồi dừng (không nạp model).")
    parser.add_argument("--model", default=None,
                        help="Đặt `SENTIMENTX_MODEL` cho kernel (dùng trọng số có sẵn trên đĩa).")
    parser.add_argument("--keep", action="store_true",
                        help="Giữ thư mục code tạm để soi lại (mặc định: xoá sau khi xong).")
    parser.add_argument("--log", default=None, metavar="PATH",
                        help="Ghi thêm toàn bộ đầu ra của kernel vào file này.")
    return parser.parse_args(argv)


def notebook_path(target):
    """Đường dẫn notebook từ `<model_id>/<method>/<expNNN>` hoặc từ đường dẫn trực tiếp."""
    path = Path(target)
    if path.suffix == ".ipynb":
        if not path.is_file():
            raise RunNotebookError("Không thấy notebook: {}".format(path))
        return path
    parts = [part for part in str(target).replace("\\", "/").split("/") if part]
    if len(parts) != 3:
        raise RunNotebookError(
            "Cần `<model_id>/<method>/<expNNN>` (ví dụ `qwen3-4b-instruct-2507/prompt-cot/exp002`) "
            "hoặc đường dẫn tới file .ipynb; nhận được: {}".format(target))
    path = paths.experiment_dir(*parts) / NOTEBOOK_NAME
    if not path.is_file():
        raise RunNotebookError("Không thấy notebook của thí nghiệm: {}".format(path))
    return path


def constants(notebook, experiment="<model>/<method>/<expNNN>"):
    """Hằng số trong ô GHIM của notebook: `REPO_URL`, `REPO_BRANCH`, `REPO_SHA`, `EXP_DIR`.

    Đọc từ CHÍNH file notebook, không lấy từ config hay từ git: đây là thứ mà lượt Run all của
    người nhận sẽ dùng, nên script phải chạy đúng thứ đó. `experiment` chỉ dùng để câu báo lỗi nói
    đúng tên thí nghiệm cần ghim lại.
    """
    try:
        cell = notebooks.pinned_cell(notebook, required=True)
    except notebooks.NotebookError as error:
        raise RunNotebookError(
            "{} - chạy `python scripts/pin.py {}` để ghim commit đang muốn chạy.".format(
                error, experiment)) from error
    source = notebooks.source_of(cell)
    found = {}
    for key in PIN_KEYS:
        matched = re.search(r"^{}\s*=\s*(.+)$".format(key), source, re.MULTILINE)
        if matched:
            found[key] = matched.group(1).strip().strip("'\"")
    missing = [key for key in ("REPO_URL", "REPO_SHA") if not found.get(key)]
    if missing:
        raise RunNotebookError("Ô GHIM thiếu {} - chạy `python scripts/pin.py` trước.".format(
            ", ".join(missing)))
    return found


def code_cells(notebook):
    """Các ô code theo đúng thứ tự, dạng chuỗi."""
    return [notebooks.source_of(cell) for cell in notebook["cells"]
            if cell.get("cell_type") == "code"]


def keep_cells(sources, preflight_only):
    """Cắt bỏ từ ô CHẠY thí nghiệm trở đi khi chỉ muốn kiểm trước.

    Ô đó được nhận ra bằng chính lời gọi thư viện (`experiment_run.run(`), không theo số thứ tự:
    notebook có thể thêm/bớt ô, mà ô nào nạp model thì phải là ô đó. Các ô SAU nó cũng bỏ, vì chúng
    đọc kết quả của nó (`run_result`) - chạy nốt sẽ báo lỗi vô nghĩa và làm người đọc tưởng hỏng.
    """
    if not preflight_only:
        return sources
    for index, source in enumerate(sources):
        if "experiment_run.run(" in source:
            if index == 0:
                raise RunNotebookError(
                    "Ô chạy thí nghiệm nằm ở NGAY ô đầu tiên - notebook này lạ, kiểm lại trước khi "
                    "dùng `--preflight-only`.")
            return sources[:index]
    raise RunNotebookError(
        "Không tìm thấy ô chạy thí nghiệm (không có lời gọi `experiment_run.run(`) nên "
        "`--preflight-only` sẽ chạy cả lượt thật. Kiểm lại notebook.")


def forward_env(basename=".env"):
    """Biến môi trường lấy từ `.env` của repo: bỏ khoá rỗng và bỏ hai khoá gốc đường dẫn.

    `.env` là chỗ giữ token DagsHub và `HF_HOME` của máy này; hai khoá gốc do script tự đặt vì
    chúng phải trỏ vào repo THẬT, không phải thư mục code tạm.
    """
    path = paths.root() / basename
    values = {}
    if not path.is_file():
        return values
    with open(path, "r", encoding="utf-8-sig") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip('"').strip("'")
            if not value or key in ROOT_KEYS:
                continue
            values[key] = value
    return values


def state(root=None):
    """Trạng thái repo: commit, nhánh, và danh sách file đang khác bản đã commit."""
    root = Path(root or paths.root())
    head = repo.current_sha(root)
    code, branch = repo.run_git(["symbolic-ref", "-q", "--short", "HEAD"], cwd=root)
    _code, porcelain = repo.run_git(["status", "--porcelain"], cwd=root)
    changes = [line for line in porcelain.splitlines() if line.strip()]
    return {"head": head, "branch": branch.strip() if code == 0 else "", "changes": changes}


def describe_state(label, current):
    """In trạng thái repo thành một dòng để so trước/sau."""
    print("{}: {} nhánh {} | {} file đang khác bản đã commit".format(
        label, current["head"][:8] or "(không rõ)", current["branch"] or "(tách rời)",
        len(current["changes"])))


def state_diff(before, after):
    """So trạng thái repo trước/sau, trả về (mục bị MẤT, mục MỚI, commit/nhánh đổi).

    Chỉ mục bị MẤT mới là đáng báo động: đó là việc đang làm dở của người dùng bị thay đổi. Mục
    MỚI là chuyện bình thường và là điều mong đợi - lượt chạy vừa sinh thư mục kết quả trong repo.
    Bản trước của hàm này so cả hai chiều nên báo động sai mỗi lần chạy xong.
    """
    lost = [line for line in before["changes"] if line not in after["changes"]]
    added = [line for line in after["changes"] if line not in before["changes"]]
    moved = (before["head"] != after["head"]) or (before["branch"] != after["branch"])
    return lost, added, moved


def newest_result_dir(experiment_dir, since=None):
    """Thư mục kết quả mới nhất của thí nghiệm (None nếu chưa có).

    `since` (mốc thời gian): chỉ xét thư mục được ghi SAU mốc đó. Cần vì một thí nghiệm có thể có
    nhiều thư mục kết quả (mỗi cấu hình một thư mục), và bản "mới nhất theo đồng hồ" có thể là thư mục
    của lượt chạy khác - lúc đó phần tổng kết sẽ chỉ vào một thư mục không liên quan tới lượt vừa rồi.
    """
    found = [path for path in (experiment_dir / "results").glob("*/*") if path.is_dir()]
    if since is not None:
        found = [path for path in found if path.stat().st_mtime >= since]
    if not found:
        return None
    return max(found, key=lambda path: path.stat().st_mtime)
def start_kernel(cwd):
    """Mở một kernel `python3` đúng môi trường đang chạy script này."""
    try:
        from jupyter_client.manager import start_new_kernel
    except ImportError as exc:
        raise RunNotebookError(
            "Máy này thiếu `ipykernel`/`jupyter_client` nên không mở được kernel. Cài bằng:\n"
            "    pip install ipykernel") from exc
    try:
        return start_new_kernel(kernel_name="python3", cwd=str(cwd))
    except Exception as exc:                                     # lỗi môi trường, không phải lỗi code
        raise RunNotebookError(
            "Không mở được kernel `python3`. Kiểm `python -c \"import ipykernel\"`, và nếu cần thì\n"
            "chạy `python -m ipykernel install --user`. Lỗi gốc: {}".format(exc)) from exc


def run_cell(kc, source, sink=None):
    """Chạy một ô, in đầu ra NGAY khi nó tới (lượt chạy dài nên phải thấy tiến độ).

    Trả về (danh sách lỗi, toàn bộ đầu ra dạng chuỗi) - đầu ra để chỗ gọi nhận ra những kết cục
    KHÔNG phải lỗi, ví dụ `Chế độ chạy: STOP` (cấu hình này đã chạy xong rồi).
    """
    message_id = kc.execute(source)
    errors, chunks = [], []
    while True:
        message = kc.get_iopub_msg(timeout=CELL_TIMEOUT)
        if message["parent_header"].get("msg_id") != message_id:
            continue
        kind = message["msg_type"]
        text = ""
        if kind == "stream":
            text = message["content"]["text"]
        elif kind in ("execute_result", "display_data"):
            text = str(message["content"].get("data", {}).get("text/plain", ""))
        elif kind == "error":
            text = "LỖI: " + "\n".join(message["content"].get("traceback", []))
            errors.append(text)
        elif kind == "status" and message["content"]["execution_state"] == "idle":
            break
        if text:
            chunks.append(text)
            print(text if text.endswith("\n") else text + "\n", end="")
            if sink is not None:
                sink.write(text if text.endswith("\n") else text + "\n")
                sink.flush()
    return errors, "".join(chunks)


def already_finished(text):
    """Ô chạy có nói `Chế độ chạy: STOP` - cấu hình này đã xong, không có gì để chạy lại.

    Đây KHÔNG phải lỗi: `src/experiment_run.py` cố ý dừng để không chạy lại một phép đo đã có. Nhưng
    nó thoát bằng `SystemExit`, và ô kết thúc phía sau sẽ lỗi `NameError: run_result` vì chưa có kết
    quả - nên script phải nhận ra và dừng luôn ở đó thay vì kể hai lỗi giả.
    """
    return "Trạng thái     : STOP" in text or "Chế độ chạy: STOP" in text


def main(argv=None):
    args = parse_args(argv)
    path = notebook_path(args.target)
    experiment_dir = path.parent
    if not (experiment_dir / CONFIG_NAME).is_file():
        raise RunNotebookError("Thiếu {} trong {}".format(CONFIG_NAME, experiment_dir))

    notebook = notebooks.read(path)
    pinned = constants(notebook, args.target)
    print("Notebook   : {}".format(path))
    print("Ghim       : {} | nhánh {} | {}".format(
        pinned["REPO_SHA"][:8], pinned.get("REPO_BRANCH", "(không khai)"), pinned["REPO_URL"]))
    print("Chạy trên  : máy này, trong BẢN CLONE TẠM (repo không bị đụng)")

    before = state()
    describe_state("Repo trước ", before)

    work = Path(tempfile.mkdtemp(prefix="sentimentx-run-"))
    started_at = time.time()
    sink = open(args.log, "w", encoding="utf-8") if args.log else None
    try:
        print("\n=== Kéo commit đã ghim vào {} ===".format(work))
        info = repo.prepare(pinned["REPO_URL"], pinned["REPO_SHA"],
                            branch=pinned.get("REPO_BRANCH") or None, dest=work, require_branch=True)
        print("  {} | {} | {}".format(info["action"], info["dir"], pinned["REPO_SHA"][:8]))
        for warning in info["warnings"]:
            print("  cảnh báo: {}".format(warning))

        env = {"SENTIMENTX_ENV": "local",
               "SENTIMENTX_DATA_ROOT": str(paths.data()),
               "SENTIMENTX_RESULTS_ROOT": str(paths.root() / "experiments")}
        env.update(forward_env())
        if args.model:
            env["SENTIMENTX_MODEL"] = args.model
        os.environ.update({key: value for key, value in env.items() if value})

        kernels = keep_cells(code_cells(notebook), args.preflight_only)
        print("Số ô sẽ chạy: {}{}".format(
            len(kernels),
            " (bỏ ô chạy thí nghiệm vì --preflight-only)" if args.preflight_only else ""))

        km, kc = start_kernel(work)
        failures = 0
        interrupted = False
        finished_already = False
        try:
            if args.limit:
                print("\n=== Ô chèn thêm: chạy thử n = {} ===".format(args.limit))
                try:
                    prelude_errors, _text = run_cell(
                        kc, LIMIT_PRELUDE.format(limit=args.limit), sink)
                    failures += len(prelude_errors)
                except KeyboardInterrupt:
                    interrupted = True
            for index, source in enumerate(kernels):
                if interrupted:
                    break
                started = time.time()
                print("\n=== Ô {} bắt đầu {} ===".format(index, time.strftime("%H:%M:%S")))
                try:
                    errors, text = run_cell(kc, source, sink)
                except KeyboardInterrupt:
                    # Ctrl+C ở terminal tới CẢ script này và kernel (cùng nhóm tiến trình). Không in
                    # traceback: người chạy chủ động dừng, việc cần biết là dừng có mất gì không.
                    interrupted = True
                    print("\n=== DỪNG theo yêu cầu (Ctrl+C) ở ô {} lúc {} ===".format(
                        index, time.strftime("%H:%M:%S")))
                    print("Các lô đã xong vẫn nằm trong predictions/part_*.jsonl của thư mục kết quả,")
                    print("và lần chạy sau sẽ tự RESUME từ đúng chỗ đó - không phải làm lại từ đầu.")
                    break
                if already_finished(text):
                    # Cấu hình này đã chạy xong ở lượt trước (cùng code, config, dữ liệu): không có
                    # gì để làm, và các ô sau cố ý không chạy được vì chưa có kết quả mới.
                    finished_already = True
                    failures += len(errors)
                    print("\n(Ô chạy báo STOP: cấu hình này đã chạy xong ở lượt trước nên không chạy "
                          "lại. Muốn chạy lại từ đầu thì XOÁ thư mục kết quả rồi chạy lại.)")
                    break
                failures += len(errors)
                print("=== Ô {} xong sau {:.0f} giây{} ===".format(
                    index, time.time() - started, " (CÓ LỖI)" if errors else ""))
        finally:
            kc.stop_channels()
            km.shutdown_kernel(now=True)

        result = newest_result_dir(experiment_dir, since=started_at)
        print("\n=== Kết quả ===")
        if result is None:
            print("Chưa thấy thư mục kết quả nào trong {}".format(experiment_dir / "results"))
        else:
            print("Thư mục kết quả: {}".format(result))
            for name in ("metrics.json", "metrics.csv", "run_meta.json", "run.log", "errors.json"):
                print("  {:<15} {}".format(name, "có" if (result / name).is_file() else "-"))

        after = state()
        print()
        describe_state("Repo sau   ", after)
        lost, added, moved = state_diff(before, after)
        if lost or moved:
            print("CẢNH BÁO: repo đã đổi trong lúc chạy - kiểm lại bằng `git status`.")
            for line in lost:
                print("  mất: {}".format(line))
        else:
            print("Repo KHÔNG đổi: file chưa commit, file chưa `git add` và thư mục chưa theo dõi "
                  "đều còn nguyên.")
        if added:
            print("(Lượt chạy sinh thêm {} mục mới trong repo - đó là kết quả, không phải thay đổi "
                  "của bạn.)".format(len(added)))
        if interrupted:
            return 130
        if finished_already and not failures:
            print("Kết luận: cấu hình này ĐÃ CÓ kết quả của đúng code + config + dữ liệu này; "
                  "không chạy lại.")
            return 0
        return 1 if failures else 0
    finally:
        if sink is not None:
            sink.close()
        if args.keep:
            print("Giữ thư mục code tạm: {}".format(work))
        else:
            shutil.rmtree(str(work), ignore_errors=True)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RunNotebookError as error:
        print("\nDỪNG: {}".format(error))
        raise SystemExit(2)

