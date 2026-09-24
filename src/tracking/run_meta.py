# -*- coding: utf-8 -*-
"""`run_meta.json` - bản ghi của MỘT lần chạy, để tra cứu và để máy khác đọc.

VÌ SAO CẦN
`metrics.json` cho biết kết quả là BAO NHIÊU; file này cho biết con số đó là CỦA CÁI GÌ: code
nào, config nào, dữ liệu nào, đã chạy mấy lần. Không có nó thì hai thư mục kết quả khác nhau
trông giống hệt nhau, và không ai dám xoá cái nào.

KHÔNG GHI ĐƯỜNG DẪN TUYỆT ĐỐI
Thư mục kết quả chạy trên Colab nằm trên Drive rồi được copy về máy khác. Đường dẫn tuyệt đối
của máy cũ chỉ gây nhiễu, nên mọi đường dẫn ở đây đều tính TỪ GỐC REPO (ngoài repo thì chỉ ghi
tên file).

CÁC KHỐI
    version     phiên bản của chính cấu trúc file này
    run         tên thư mục kết quả, tag cấu hình, trạng thái, lúc bắt đầu/kết thúc
    experiment  model, method, exp_id, parent
    data        dataset, version (bản trong configs/datasets), ma (mã phiên bản dữ liệu), roles
    repo        url, branch, sha - `sha` là commit ĐÃ GHIM, một trong ba điều kiện resume
    config      sha256 (điều kiện resume thứ hai), sources (khoá nào do lớp cấu hình nào đặt)
    env         colab hay local, python, hệ điều hành
    attempts    các lần chạy vào cùng thư mục này; mỗi lần có `sha` và `config_sha256` RIÊNG,
                nên nhìn là biết hai lần chạy có so được với nhau hay không
    files       file ĐẦU VÀO của lần chạy, kèm `role` (paths, config, prompt, dataset...)

Quy tắc resume ở docs/00_workflow/02_rules.md mục 13-14: chỉ resume khi `config_sha256`,
`data.ma` và `repo.sha` đều KHÔNG đổi; code đổi thì chạy lại từ đầu và ghi thành attempt mới.
"""

import hashlib
import json
import platform
import subprocess
from datetime import datetime
from pathlib import Path

from src import paths, runlog, utils

# Phiên bản cấu trúc của file này. Đổi cấu trúc thì tăng số, để chỗ đọc biết cách đọc.
SCHEMA_VERSION = 1

# Vai của file đầu vào. Chuỗi cố định để báo cáo và CI tra được, không dùng câu mô tả tự do.
ROLE_PATHS = "paths"
ROLE_CONFIG = "config"
ROLE_MODEL = "model"
ROLE_DATASET = "dataset"
ROLE_PIPELINE = "pipeline"
ROLE_PROMPT = "prompt"
ROLE_EXAMPLES = "examples"
ROLE_SYSTEM = "system"
ROLE_TRACKING = "tracking"

STATUS_RUNNING = "RUNNING"
STATUS_FINISHED = "FINISHED"
STATUS_FAILED = "FAILED"


def relative(path):
    """Đường dẫn so với gốc repo, dạng posix. Ngoài repo thì chỉ giữ tên file."""
    if not path:
        return ""
    path = Path(path)
    try:
        return path.resolve().relative_to(paths.root().resolve()).as_posix()
    except ValueError:
        return path.name


def describe(path, role):
    """Mô tả MỘT file đầu vào: đường dẫn tương đối, vai, số byte, sha256.

    Trả về None nếu file không tồn tại: thiếu file đầu vào là việc của preflight, không phải việc
    của bản ghi lần chạy.
    """
    if not path:
        return None
    path = Path(path)
    if not path.is_file():
        return None
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"path": relative(path), "role": str(role), "bytes": path.stat().st_size,
            "sha256": digest}


def input_files(entries):
    """Mô tả danh sách (đường dẫn, vai). Bỏ qua file không tồn tại."""
    found = []
    for path, role in entries or []:
        described = describe(path, role)
        if described:
            found.append(described)
    return found


def repo_info(url=None, branch=None):
    """Thông tin repo: địa chỉ, nhánh, và commit (`git rev-parse HEAD`).

    Không phải repo git (ví dụ đang chạy trong thư mục đã copy) thì `sha` để trống - ghi một giá
    trị đoán mò vào đây còn tệ hơn để trống, vì điều kiện resume dựa vào chính giá trị này.
    """
    sha = ""
    try:
        done = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(paths.root()),
                              capture_output=True, text=True, timeout=15)
        if done.returncode == 0:
            sha = done.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        sha = ""
    return {"url": url or "", "branch": branch or "", "sha": sha}


def env_info(kind=None, extra=None):
    """Máy đã chạy: colab hay local, phiên bản Python, hệ điều hành."""
    info = {"kind": kind or "", "python": platform.python_version(),
            "system": platform.platform()}
    info.update(extra or {})
    return info


def device_info(model=None, quant=None):
    """Thiết bị, mức lượng hoá và thư viện đã chạy: đọc từ `model_info` của bước nạp model.

    Chỉ ghi thứ ĐỌC ĐƯỢC: thiếu khoá thì để trống chứ không đoán, vì đây là phần truy vết của một
    phép đo (cùng cấu hình chạy bf16 và 4-bit là hai phép đo khác nhau).
    """
    model = dict(model or {})
    return {
        "device": model.get("thiết bị"),
        "gpu": model.get("gpu"),
        "vram_gb": model.get("vram_gb"),
        # Ưu tiên giá trị ĐÃ GIẢI từ bước nạp model ("4-bit nf4 (tính bằng float16)") hơn tham số
        # khai trong config ("auto"), vì bản ghi phải nói phép đo đã chạy bằng gì.
        "quantization": model.get("quant") or quant,
        "libs": {name: version for name, version in (("torch", model.get("torch")),
                                                     ("transformers", model.get("transformers")))
                 if version},
    }


def build(out_dir, tag=None, experiment=None, data=None, repo=None, config=None,
          files=None, env=None, note=None, previous=None, task=None, overrides=None):
    """Dựng nội dung `run_meta.json` cho một lần chạy, kèm attempt đầu tiên.

    `previous` là bản ghi cũ (kết quả của `read`). Chạy lại vào cùng thư mục thì các attempt cũ
    được GIỮ LẠI và thêm attempt mới - đó là cách phân biệt "lần thứ ba" với "lần đầu", và là
    thông tin mà quyết định resume cần.

    `task` và `overrides` là phần TRUY VẾT của cấu hình: bài toán đang giải (không gian nhãn, cách
    xử lý neutral) và những khoá bị lớp sau đè. Bảng ghi đè cũng nằm trong `run.log` (nhãn
    `[CONFIG]`); để ở đây nữa thì máy khác đọc file là biết ngay, không phải mở log.
    """
    payload = {
        "version": SCHEMA_VERSION,
        "run": {"out_dir": Path(out_dir).name, "tag": tag or Path(out_dir).name,
                "log": paths.pattern("run_log"), "errors": paths.pattern("errors"),
                "status": STATUS_RUNNING, "started": runlog.now(), "finished": None,
                "note": note},
        "experiment": dict(experiment or {}),
        "data": dict(data or {}),
        "repo": dict(repo or {}),
        "config": dict(config or {}),
        "task": dict(task or {}),
        "overrides": [list(item) for item in (overrides or [])],
        "env": dict(env or {}),
        "attempts": list((previous or {}).get("attempts") or []),
        "files": list(files or []),
    }
    start_attempt(payload, note=note)
    return payload


def start_attempt(payload, note=None):
    """Thêm một attempt đang chạy. Trả về attempt vừa thêm.

    Mỗi attempt mang `sha`, `config_sha256` và `data.ma` của CHÍNH lần đó: hai lần chạy vào cùng
    thư mục có thể khác code hoặc khác config, khi đó kết quả không so được với nhau, và bản ghi
    phải nói ra điều đó thay vì để người đọc tự đoán.
    """
    attempts = payload.setdefault("attempts", [])
    attempt = {
        "n": len(attempts) + 1,
        "started": runlog.now(),
        "finished": None,
        "seconds": None,
        "status": STATUS_RUNNING,
        "sha": (payload.get("repo") or {}).get("sha", ""),
        "config_sha256": (payload.get("config") or {}).get("sha256", ""),
        "data": (payload.get("data") or {}).get("ma", ""),
        "note": note,
    }
    attempts.append(attempt)
    return attempt


def finish_attempt(attempt, status, note=None):
    """Chốt một attempt: trạng thái, lúc kết thúc, số giây đã chạy."""
    attempt["status"] = status
    attempt["finished"] = runlog.now()
    attempt["seconds"] = seconds_between(attempt.get("started"), attempt["finished"])
    if note:
        attempt["note"] = note
    return attempt


def seconds_between(start, finish):
    """Số giây giữa hai mốc thời gian dạng chuỗi. Không đọc được thì trả None."""
    try:
        begin = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
        end = datetime.strptime(finish, "%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError):
        return None
    return round((end - begin).total_seconds(), 1)


def attempt_of(payload):
    """Attempt đang chạy (attempt cuối cùng)."""
    attempts = (payload or {}).get("attempts") or []
    return attempts[-1] if attempts else None


def write(out_dir, payload):
    """Ghi `run_meta.json`. Trả về đường dẫn file."""
    return utils.write_json(payload, Path(out_dir) / paths.pattern("run_meta"))


def read(out_dir):
    """Đọc `run_meta.json` của một thư mục kết quả. Chưa có file thì trả None."""
    path = Path(out_dir) / paths.pattern("run_meta")
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def closer(payload, out_dir, log=None):
    """Hàm chốt bản ghi lúc đóng log, để đưa cho `runlog.on_close`.

    Chạy cả khi lần chạy HỎNG: một lần hỏng vẫn là một lần đã xảy ra, và lần sau cần biết nó dừng
    ở attempt nào, với code và config nào. Chạy TRƯỚC phần ghi nhận (xem `src/tracking/__init__.py`)
    nên `run_meta.json` đã chốt trước khi được tải lên máy chủ.
    """
    def finish(ok=True, note=None):
        attempt = attempt_of(payload)
        if attempt is not None:
            finish_attempt(attempt, STATUS_FINISHED if ok else STATUS_FAILED, note=note)
        payload["run"]["status"] = STATUS_FINISHED if ok else STATUS_FAILED
        payload["run"]["finished"] = runlog.now()
        write(out_dir, payload)
        if log is not None:
            log.step("run_meta.json: lần chạy thứ {}, trạng thái {}".format(
                len(payload.get("attempts") or []), payload["run"]["status"]))
        return payload
    return finish

