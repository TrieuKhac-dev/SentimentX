# -*- coding: utf-8 -*-
"""Kéo ĐÚNG bản code đã ghim, và kiểm lại trước khi tin.

VÌ SAO PHẢI GHIM ĐÚNG COMMIT
Notebook của giảng viên chạy trên máy khác, sau khi ta đã sửa code thêm vài lần. Nếu notebook kéo
"bản mới nhất" thì kết quả không còn ứng với bản code đã đọc, và không ai biết vì sao số liệu
khác. Vì vậy notebook giữ một commit cụ thể (`REPO_SHA`), và mọi kết quả chỉ được dùng khi commit
đó nằm trên nhánh `experiment` (docs/00_workflow/01_flow.md).

BA CÁCH, THEO THỨ TỰ RẺ TỚI ĐẮT
    1. Thư mục đang có đúng commit rồi  -> không làm gì (máy cá nhân thường ở trường hợp này)
    2. `git fetch --depth 1 origin <sha>`  -> nhẹ nhất, nhưng GitHub không phải lúc nào cũng cho
       fetch theo sha
    3. `git clone --filter=blob:none --no-checkout` rồi `git checkout <sha>` -> nặng hơn nhưng
       chắc chắn được, vì bản clone có đủ lịch sử để checkout bất kỳ commit nào

Sau khi kéo, `git rev-parse HEAD` PHẢI bằng đúng sha đã ghim. Không thì báo lỗi kèm hai lệnh đã
thử - thà dừng ngay còn hơn chạy trên bản code không rõ là bản nào.
"""

import os
import subprocess
from pathlib import Path

from src import paths


class RepoError(Exception):
    """Không kéo được đúng commit đã ghim, hoặc commit không nằm trên nhánh cho phép."""


def run_git(args, cwd=None, timeout=600):
    """Chạy một lệnh git. Trả về (mã thoát, đầu ra gộp cả stdout và stderr).

    `GIT_TERMINAL_PROMPT=0`: trên Colab, git có thể dừng lại hỏi tài khoản mà không ai trả lời,
    và notebook treo tới lúc hết thời gian. Tắt hỏi thì nó báo lỗi ngay.

    Thư mục chạy chưa tồn tại (lần đầu kéo code trên Colab) coi như lệnh THẤT BẠI chứ không ném
    lỗi hệ điều hành: chỗ gọi chỉ cần biết "ở đây chưa có repo" để đi bước tiếp theo.
    """
    if cwd is not None and not Path(cwd).is_dir():
        return 128, "thư mục chưa tồn tại: {}".format(cwd)
    env = dict(os.environ)
    env.setdefault("GIT_TERMINAL_PROMPT", "0")
    env.setdefault("GIT_ASKPASS", "echo")
    try:
        done = subprocess.run(["git"] + [str(item) for item in args],
                              cwd=str(cwd) if cwd else None, env=env,
                              capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError as exc:
        raise RepoError("Máy này không có `git`. Cài git rồi chạy lại.") from exc
    except subprocess.TimeoutExpired as exc:
        raise RepoError("Lệnh git quá lâu ({} giây): git {}".format(
            timeout, " ".join(str(item) for item in args))) from exc
    output = (done.stdout or "") + (done.stderr or "")
    return done.returncode, output.strip()


def is_repo(root=None):
    """Thư mục này có phải git repo không."""
    code, output = run_git(["rev-parse", "--is-inside-work-tree"], cwd=root or paths.root())
    return code == 0 and output.strip().startswith("true")


def current_sha(root=None):
    """Commit đang có trong thư mục (chuỗi rỗng nếu không phải repo)."""
    code, output = run_git(["rev-parse", "HEAD"], cwd=root or paths.root())
    return output.strip() if code == 0 else ""


def is_ancestor(sha, ref, root=None):
    """Commit `sha` có nằm trong lịch sử của `ref` không.

    Dùng để trả lời câu quan trọng nhất: bản code đã ghim đã nằm trên nhánh cho phép chưa. Chưa
    thì kết quả chạy ra không dùng được, vì không ai khác tải lại được đúng bản code đó.
    """
    if not sha or not ref:
        return False
    code, _output = run_git(["merge-base", "--is-ancestor", sha, ref],
                            cwd=root or paths.root())
    return code == 0


def ref_exists(ref, root=None):
    """Nhánh (hoặc ref) này có trong repo không."""
    if not ref:
        return False
    code, _output = run_git(["rev-parse", "--verify", "--quiet", ref + "^{commit}"],
                            cwd=root or paths.root())
    return code == 0


def plans(url, sha):
    """Các cách kéo code, theo thứ tự rẻ tới đắt.

    Mỗi bước là `(tham số git, bắt buộc thành công không)`. Bước không bắt buộc là bước có thể
    đã đúng sẵn (ví dụ `remote add` khi `origin` đã có), nên hỏng thì đi tiếp chứ không bỏ cả cách.
    """
    return [
        ("fetch theo sha", [
            (["init", "-q"], True),
            (["remote", "remove", "origin"], False),
            (["remote", "add", "origin", url], True),
            (["fetch", "--depth", "1", "origin", sha], True),
            (["checkout", "--detach", "FETCH_HEAD"], True),
        ]),
        ("clone rút gọn rồi checkout", [
            # `--filter=blob:none`: lấy lịch sử mà không lấy nội dung file cho tới lúc cần, nên
            # checkout được BẤT KỲ commit nào (khác `--depth 1`, chỉ có commit mới nhất).
            (["clone", "--filter=blob:none", "--no-checkout", url, "."], True),
            (["fetch", "--depth", "1", "origin", sha], True),
            (["checkout", "--detach", sha], True),
        ]),
    ]


def _try(steps, dest, info):
    """Chạy các bước của một cách kéo code. Trả về True nếu tới được bước cuối."""
    dest.mkdir(parents=True, exist_ok=True)
    for args, required in steps:
        code, output = run_git(args, cwd=dest)
        info["output"].append("$ git {}  ->  mã thoát {}".format(" ".join(args), code))
        if code != 0:
            info["output"].append(output[-400:])
            if required:
                return False
    return True


def _check_branch(sha, branch, dest, info, require_branch, log):
    """Kiểm commit đã ghim có nằm trên nhánh cho phép.

    Nhánh không có trong repo thì bỏ qua kèm cảnh báo: máy cá nhân có thể chưa fetch nhánh đó, mà
    báo lỗi vì thiếu thông tin thì không giúp gì. Có thông tin mà commit KHÔNG nằm trên nhánh thì
    mới là việc phải xử lý.
    """
    ref = "origin/" + branch
    if not ref_exists(ref, dest):
        info["warnings"].append(
            "Chưa có {} trong repo nên không kiểm được commit đã ghim có nằm trên nhánh {}.".format(
                ref, branch))
        return
    if is_ancestor(sha, ref, dest):
        info["on_branch"] = True
        return
    info["on_branch"] = False
    message = ("Commit đã ghim ({}) KHÔNG nằm trên nhánh {}. Kết quả chạy ra không dùng được cho "
               "tới khi commit đó được đẩy lên nhánh này.".format(sha[:12], branch))
    if require_branch:
        raise RepoError(message)
    info["warnings"].append(message)


def prepare(url, sha, branch=None, dest=None, require_branch=False, log=None):
    """Bảo đảm thư mục code đang Ở ĐÚNG commit đã ghim. Trả về thông tin của lần chuẩn bị.

    url, sha        hai giá trị notebook ghi ở cell đầu (do `scripts/pin.py` ghi vào)
    branch          nhánh được phép, để kiểm commit đã ghim có nằm trên đó
    dest            thư mục code; để trống là gốc repo hiện tại (máy cá nhân)
    require_branch  True thì commit không nằm trên nhánh là LỖI (preflight dùng giá trị này)
    """
    if not url or not sha:
        raise RepoError(
            "Thiếu `url` hoặc `sha` của bản code đã ghim. Chạy `python scripts/pin.py` để ghi vào "
            "cell đầu của notebook.")
    dest = Path(dest or paths.root())
    info = {"dir": str(dest), "url": url, "sha": sha, "branch": branch, "action": "",
            "warnings": [], "output": []}

    if is_repo(dest) and current_sha(dest) == sha:
        info["action"] = "dùng bản code đang có"
    else:
        for action, steps in plans(url, sha):
            info["output"].append("--- {}".format(action))
            if _try(steps, dest, info):
                info["action"] = action
                break
        else:
            raise RepoError("Không kéo được commit đã ghim ({}). Đã thử:\n{}".format(
                sha[:12], "\n".join(info["output"][-12:])))

    found = current_sha(dest)
    if found != sha:
        raise RepoError(
            "Sau khi kéo, thư mục {} đang ở commit {} chứ không phải {}. Dừng lại thay vì chạy "
            "trên bản code không rõ là bản nào.".format(dest, found[:12] or "(không rõ)", sha[:12]))

    if branch:
        _check_branch(sha, branch, dest, info, require_branch, log)

    if log is not None:
        log.step("code: {} | {} | {}".format(info["action"], info["dir"], sha[:12]))
        for warning in info["warnings"]:
            log.warn(warning)
    return info

