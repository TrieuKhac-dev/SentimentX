# -*- coding: utf-8 -*-
"""Sinh NĂM NHÓM bảng tổng hợp từ bản ghi lần chạy và bảng chỉ số đã có trên đĩa.

VÌ SAO ĐỌC LẠI FILE, KHÔNG TÍNH LẠI
Mọi con số vào bảng đều lấy từ file mà chính lượt chạy đã ghi (`run_meta.json`, `metrics.json`,
`metrics.csv`, `model_input.csv`). Tính lại từ dữ liệu gốc là có hai đường tính cho cùng một con số,
và khi hai đường lệch nhau thì không ai biết đường nào đúng. Bảng tổng hợp chỉ TRÌNH BÀY.

NĂM NHÓM (tên lấy từ `configs/paths.yaml`, xem docs/05_config/01_paths.md)
    dataset_registry      mỗi PHIÊN BẢN DỮ LIỆU một dòng: có gì, sinh từ đâu, đang dùng ở đâu
    experiment_registry   mỗi LƯỢT CHẠY một dòng: code, cấu hình, dữ liệu, trạng thái, chi phí
    attempt_registry      MỌI lần thử, kể cả lượt HỎNG: trạng thái, thời lượng, lý do dừng. Đây là
                          "bản tổng hợp toàn bộ"; bốn nhóm kia mặc định chỉ liệt kê lượt THÀNH CÔNG
    model_input           số đo đầu vào của model (do run_token_stats.py ghi; ở đây trình bày lại)
    metrics_matrix        ma trận chỉ số: dòng là khía cạnh (hoặc khía cạnh × sắc thái), cột là
                          TỪNG LƯỢT CHẠY, kèm cột `reference` chứa số của công bố khi có

HAI BỘ BẢNG, TÁCH RÕ
Lượt hỏng không có `metrics.json`, nên mọi bảng SỐ đều vô nghĩa với nó: mặc định các nhóm bảng số chỉ
liệt kê lượt `FINISHED` (`build(..., only="finished")`). Muốn xem cả lượt hỏng thì dùng nhóm
`attempt_registry` (luôn liệt kê đủ) hoặc `--only all` (xem `scripts/collect_reports.py`).

MỖI NHÓM GHI BA THỨ
    <tên>.csv    bảng nguồn: mở được bằng Excel/pandas, và là thứ người khác đọc lại để kiểm
    <tên>.html   bảng trình bày: tự chứa, không cần mạng, không cần thư viện vẽ
    <tên>.md      CHỈ sơ đồ Mermaid: quan hệ giữa các dòng. Số liệu không chép lại vào đây - chép
                  là có bản sao thứ hai của cùng một con số, rồi hai bản lệch nhau.

Nhóm nào chưa có dữ liệu thì vẫn ghi bảng RỖNG kèm một dòng giải thích, chứ không im lặng bỏ qua:
người đọc cần phân biệt "chưa chạy" với "chạy rồi mà không ra gì".
"""

import csv
import html
import json
from pathlib import Path

from src.core import config, dataset as dataset_module, paths, utils, versioning
from src.workflow import repo as repo_module

NO_DATA = "chưa có dữ liệu"

# Tên file CSV nguồn của mỗi nhóm. Nhóm có nhiều bảng thì tên ở đây là bảng CHÍNH; các bảng phụ
# khai trong `TABLE_NAMES` (metrics_matrix có hai bảng, đúng như docs/04_experiments/metrics.md).
CSV_NAME = {
    "dataset_registry": "dataset_registry.csv",
    "experiment_registry": "experiment_registry.csv",
    "attempt_registry": "attempt_registry.csv",
    "model_input": "model_input.csv",
    "metrics_matrix": "accuracy_by_aspect.csv",
}

TABLE_NAMES = {
    "metrics_matrix": ("accuracy_by_aspect.csv", "prf_by_aspect_sentiment.csv"),
}

# Nhãn cột của bảng CHƯA có số đo: báo cáo vẫn sinh ra, kèm dấu hiệu RỖNG để người đọc phân biệt
# "chưa đo" với "đo rồi mà không ra gì".
EMPTY_TABLE_COLUMN = "model_input"

# Phiên bản dataset không khai `parent`: nó sinh trực tiếp từ dữ liệu gốc, không kế thừa phiên bản nào.
FROM_RAW = "sinh từ dữ liệu gốc"

MERMAID_HEADER = "```mermaid"


class ReportError(Exception):
    """Không sinh được báo cáo: thiếu file nguồn, hoặc tên nhóm không có trong config."""


# ---
# Quét lượt chạy
# ---


def default_roots():
    """Gốc quét lượt chạy: gốc kết quả của các thí nghiệm (`experiments/**/results/<hash8>/`).

    Chỉ còn MỘT gốc: mọi kết quả đều thuộc một thí nghiệm, nên không có chỗ nào khác để quét và
    cũng không có lượt chạy nào "không thuộc thí nghiệm nào".
    """
    roots = [paths.results_root()]
    seen, unique = set(), []
    for path in roots:
        key = str(Path(path).resolve()) if Path(path).exists() else str(path)
        if key in seen:
            continue
        seen.add(key)
        unique.append(Path(path))
    return unique


def scan_runs(roots=None):
    """Tìm mọi thư mục lượt chạy (có `run_meta.json`) dưới các gốc cho trước.

    Trả về danh sách dict đã đọc sẵn `run_meta.json` và `metrics.json`, sắp theo thời điểm bắt đầu
    để bảng tổng hợp đọc theo thứ tự thời gian.
    """
    found = []
    for root in (roots or default_roots()):
        root = Path(root)
        if not root.is_dir():
            continue
        for path in sorted(root.rglob(paths.pattern("run_meta"))):
            meta = _read_json(path)
            if not meta:
                continue
            run_dir = path.parent
            found.append({
                "dir": run_dir,
                "meta": meta,
                "metrics": _read_json(run_dir / paths.pattern("metrics_json")),
            })
    found.sort(key=lambda item: ((item["meta"].get("run") or {}).get("started") or "",
                                 str(item["dir"])))
    return found


def _read_json(path):
    """Đọc JSON, trả về {} nếu file thiếu hoặc hỏng (báo cáo không được chết vì một file hỏng)."""
    path = Path(path)
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return {}


def canonical_label(run):
    """Nhãn của một lượt chạy: `<model>/<method>/<expNNN>:<hash8>`.

    Thí nghiệm là đơn vị so sánh, nên nhãn phải nói được nó thuộc thí nghiệm nào; thêm mã băm danh
    tính vì một thí nghiệm có thể có nhiều lượt chạy (khác commit hoặc khác cấu hình), và tên thư
    mục chỉ là mã băm nên không tự nói được gì.
    """
    meta = run.get("meta") or {}
    experiment = dict(meta.get("experiment") or {})
    run_block = dict(meta.get("run") or {})
    hash8 = str(run_block.get("hash") or (run.get("dir") or "").name)
    model, method, exp_id = experiment.get("model"), experiment.get("method"), experiment.get("exp_id")
    if model and method and exp_id:
        return "{}/{}/{}:{}".format(model, method, exp_id, hash8)
    return hash8


# ---
# Nhóm 1: dataset_registry
# ---


def dataset_rows():
    """Mỗi phiên bản dữ liệu ĐÃ XỬ LÝ một dòng, ghép với khai báo dataset của nó.

    Bảng này trả lời: dữ liệu đang dùng sinh từ đâu, gồm split nào với bao nhiêu dòng, và tập đánh
    giá đã CHỐT mã chưa. Chưa chốt thì con số không neo được vào một bản dữ liệu cụ thể - người đọc
    sau có thể chấm trên bản khác mà không biết.
    """
    rows = []
    for name in dataset_module.available():
        for version in dataset_module.versions(name):
            cfg = dataset_module.load_config(name, version)
            build = versioning.compute_id(cfg)
            directory = versioning.processed_dir(build)
            splits = {}
            if directory.is_dir():
                for path in sorted(directory.glob("*.csv")):
                    splits[path.stem] = _row_count(path)
            lock = _read_json(directory / "eval_lock.json")
            locked = sorted(key for key, value in lock.items()
                            if isinstance(value, dict) and value.get("sha256"))
            rows.append({
                "dataset": name,
                "version": version,
                "build": build,
                # Dòng dõi: phiên bản NÀY sinh từ phiên bản dataset nào. Không khai `parent` nghĩa là
                # sinh trực tiếp từ dữ liệu gốc - nói ra thay vì để ô trống, vì ô trống đọc thành
                # "chưa biết". Người đọc tra tiếp ở `docs/01_dataset/changelog.md`.
                "parent": str(cfg.get("parent") or FROM_RAW),
                "on_disk": "yes" if directory.is_dir() else "no",
                "splits": ", ".join("{}={}".format(key, splits[key]) for key in sorted(splits)),
                "rows": sum(splits.values()),
                "eval_locked": ", ".join(locked) or NO_DATA,
                "aspects": ", ".join(cfg.get("aspects") or []),
                # Khoá khai `raw_dir` đã bị bỏ ở P1 T5; thư mục dữ liệu gốc nay do `src/core/dataset.py`
                # SUY RA thành `_raw_dir` (chỉ khi có đúng một nguồn `raw`). Đọc khoá cũ thì cột này
                # luôn rỗng - lỗi im lặng đã vào tận bảng đã commit.
                "raw_dir": utils.rel(cfg["_raw_dir"]) if cfg.get("_raw_dir") else "",
                "config": utils.rel(dataset_module.config_path(name, version)),
            })
    return rows


def _row_count(path):
    """Số BẢN GHI của một file CSV (không đọc cả file vào bộ nhớ).

    Đếm bằng `csv.reader` chứ KHÔNG đếm dòng: ô văn bản của review có thể chứa xuống dòng, nên đếm dòng
    cho ra 2.271 trong khi tập `test` chỉ có 1.518 bản ghi - đúng loại lỗi đã gặp ở preflight
    (`fix(preflight): eval_lock counts records, not lines`). Bảng tổng hợp ghi sai số bản ghi là chuyện
    về sau không ai phát hiện được, vì con số trông vẫn hợp lý.
    """
    with open(path, "r", encoding="utf-8-sig", newline="", errors="replace") as handle:
        records = csv.reader(handle)
        next(records, None)          # dòng đầu là tên cột
        return sum(1 for _ in records)


# ---
# Nhóm 2: experiment_registry
# ---

# Ba giá trị của hai cột `valid` và `comparable`. Có cả "chưa rõ" vì thiếu git hoặc thiếu thông tin
# không được coi là hợp lệ (nói dối kiểu khác) mà cũng không được coi là sai.
VALID_YES = "yes"
VALID_NO = "no"
VALID_UNKNOWN = "chưa rõ"


def commit_status(sha, branch, cache=None):
    """Commit của lượt chạy có nằm trên nhánh `branch` của `origin` không: trả `(valid, lý do)`.

    Vì sao cần: một lượt chạy có thể được chấm bằng commit CHƯA merge vào nhánh đã ghim (chạy trước khi
    merge, hoặc máy khác còn nhánh riêng). Đọc thì vẫn ra số, nhưng không ai tái lập được từ bản code đã
    công bố - nên bảng phải NÓI RA, thay vì để người đọc tự phát hiện.

    Gọi git qua `src/workflow/repo.py` (một chỗ duy nhất biết gọi git). Máy không có git, thiếu ref, hoặc thiếu
    thông tin trong `run_meta.json` thì trả "chưa rõ" kèm lý do - báo cáo không được chết vì việc phụ.
    """
    if not sha:
        return VALID_UNKNOWN, "run_meta.json không ghi commit"
    if not branch:
        return VALID_UNKNOWN, "run_meta.json không ghi nhánh"
    cache = {} if cache is None else cache
    if (sha, branch) in cache:
        return cache[(sha, branch)]
    try:
        ref = "origin/{}".format(branch)
        if not repo_module.ref_exists(ref):
            # Máy chỉ có nhánh nội bộ (chưa có `origin`): đối chiếu bằng chính ref đó.
            ref = branch
            if not repo_module.ref_exists(ref):
                result = (VALID_UNKNOWN,
                          "máy này không có ref {!r} để đối chiếu".format(branch))
                cache[(sha, branch)] = result
                return result
        if repo_module.is_ancestor(sha, ref):
            result = (VALID_YES, "")
        else:
            result = (VALID_NO,
                      "commit {} không nằm trên {} (chạy trước khi merge?)".format(sha[:7], ref))
    except repo_module.RepoError as exc:
        result = (VALID_UNKNOWN, str(exc))
    cache[(sha, branch)] = result
    return result


def measurement_basis(run):
    """Cơ sở đo của một lượt chạy: khác một trong những thứ này thì hai lượt KHÔNG so được với nhau.

    Không có nó thì bảng đặt hai cột cạnh nhau và người đọc so số của hai phép đo khác nhau - lệch vì
    ĐO KHÁC chứ không phải vì model khác.

    Hai khoá cuối nói về CƠ SỞ ĐO THỨ HAI (`paper`, xem docs/04_experiments/metrics.md): một lượt
    chạy ghi trước 01/10/2026 chưa có cơ sở đó (`chưa có`), nên nó không so được với lượt có - số
    `paper` của lượt cũ đơn giản là không tồn tại, không phải bằng 0.
    """
    meta = dict(run["meta"] or {})
    metrics = dict(run["metrics"] or {})
    task = dict(meta.get("task") or {})
    paper = dict(metrics.get("paper") or {})
    return {
        "dữ liệu": (meta.get("data") or {}).get("build") or NO_DATA,
        "không gian nhãn": task.get("label_space") or NO_DATA,
        "cách xử lý neutral": task.get("neutral_policy") or NO_DATA,
        "khía cạnh không nhắc tới": task.get("not_mentioned") or NO_DATA,
        "split": metrics.get("split") or NO_DATA,
        "bộ chấm": ", ".join(metrics.get("scores_order") or []) or NO_DATA,
        "bộ chấm paper": ", ".join(metrics.get("scores_order_paper") or []) or NO_DATA,
        "nhãn lọc paper": ", ".join(paper.get("label_filter") or []) or NO_DATA,
    }


def comparable_with(basis, run):
    """Lượt này so được với lượt CHUẨN không: trả `(comparable, lý do)`.

    Lượt chuẩn là lượt `FINISHED` sớm nhất trong bảng (`build` đã lọc), tức lượt mà các cột khác được
    đặt cạnh để so.
    """
    mine = measurement_basis(run)
    differ = ["{}: {} so với {}".format(key, mine[key], basis[key])
              for key in basis if mine[key] != basis[key]]
    if differ:
        return VALID_NO, "khác cơ sở đo với lượt chuẩn - " + "; ".join(differ)
    return VALID_YES, ""


REGISTRY_COLUMNS = ("run", "status", "started", "seconds", "model", "method", "exp_id", "split",
                    "prompt", "prompt_sha", "examples_sha", "shot", "n_samples", "subset", "decoding",
                    "quant", "max_length", "max_new_tokens", "dataset", "version_id",
                    "config_sha256", "repo_sha", "valid", "comparable", "invalid_reason", "mode",
                    "read_percent", "tokens_per_second",
                    "accuracy_micro", "f1_macro", "exact_match_percent", "out_dir")


def experiment_rows(runs):
    """Mỗi LƯỢT CHẠY một dòng: code đã chạy, cấu hình, dữ liệu, trạng thái và chi phí.

    Con số lấy từ `run_meta.json` (code, dữ liệu, trạng thái) và `metrics.json` (cấu hình, kết quả,
    chi phí) - hai file mà chính lượt chạy đã ghi; không tính lại gì từ dữ liệu gốc.

    Hai cột nói lượt chạy này có DÙNG ĐƯỢC TRONG BẢNG SO hay không: `valid` (commit có nằm trên nhánh đã
    ghim) và `comparable` (cơ sở đo có khớp lượt chuẩn). `invalid_reason` gộp lý do của cả hai - không
    có cột này thì người đọc tự phát hiện bằng cách tin vào một con số không tái lập được.
    """
    rows = []
    # Lượt CHUẨN để đối chiếu: lượt sớm nhất trong bảng (danh sách đã sắp theo thời gian).
    basis = measurement_basis(runs[0]) if runs else {}
    git_cache = {}
    for run in runs:
        meta = run["meta"]
        metrics = run["metrics"]
        run_info = dict(meta.get("run") or {})
        experiment = dict(meta.get("experiment") or {})
        data = dict(meta.get("data") or {})
        repo = dict(meta.get("repo") or {})
        config = dict(meta.get("config") or {})
        generation = dict(metrics.get("generation") or {})
        subset = dict(metrics.get("subset") or {})
        examples = dict(metrics.get("prompt_examples") or {})
        cost = dict(metrics.get("cost") or {})
        # Mức ví dụ few-shot của lượt này: dùng để so với ĐÚNG cột của công bố (`shot_of`).
        shot = shot_of(run)
        # Hai câu hỏi khác nhau, cùng quyết định "con số này có nằm chung bảng so được không": commit
        # có trên nhánh đã ghim không, và cơ sở đo có khớp lượt chuẩn không.
        valid, git_reason = commit_status(repo.get("sha"), repo.get("branch"), cache=git_cache)
        comparable, basis_reason = (comparable_with(basis, run) if basis else (VALID_UNKNOWN, ""))
        invalid_reason = git_reason or basis_reason
        rows.append({
            "run": canonical_label(run),
            "hash": run_info.get("hash") or run["dir"].name,
            "status": run_info.get("status"),
            "started": run_info.get("started"),
            "seconds": cost.get("giây"),
            "model": experiment.get("model") or metrics.get("model"),
            "method": experiment.get("method") or "-",
            "exp_id": experiment.get("exp_id") or "-",
            "split": metrics.get("split"),
            "prompt": metrics.get("prompt"),
            "prompt_sha": metrics.get("prompt_sha"),
            "examples_sha": examples.get("sha") or "-",
            "shot": "-" if shot is None else shot,
            "n_samples": metrics.get("n_samples"),
            "subset": "limit={} seed={}".format(subset.get("limit") or "cả split",
                                                subset.get("seed", "-")),
            "decoding": "sample" if generation.get("do_sample") else "greedy",
            "quant": metrics.get("quant"),
            "dtype": dict(meta.get("env") or {}).get("dtype") or "-",
            "max_length": metrics.get("max_length"),
            "max_new_tokens": generation.get("max_new_tokens"),
            "dataset": data.get("dataset"),
            "version_id": data.get("build"),
            "config_sha256": (config.get("sha256") or "")[:12],
            "repo_sha": (repo.get("sha") or "")[:12],
            "valid": valid,
            "comparable": comparable,
            "invalid_reason": invalid_reason,
            "mode": dict(metrics.get("resume") or {}).get("mode") or "-",
            "read_percent": dict(metrics.get("read_rate") or {}).get("% đọc được"),
            "tokens_per_second": cost.get("token sinh/giây"),
            "accuracy_micro": _dig(metrics, "scores", "aggregate", "accuracy_micro"),
            "f1_macro": _dig(metrics, "scores", "prf", "macro", "f1"),
            "exact_match_percent": _dig(metrics, "scores", "aggregate", "exact_match", "percent"),
            "out_dir": utils.rel(run["dir"]),
        })
    return rows


ATTEMPT_COLUMNS = ("run", "status", "mode", "started", "seconds", "model", "method", "exp_id", "split",
                   "version_id", "config_sha256", "repo_sha", "reason")


def attempt_rows(runs):
    """MỌI lần thử một dòng, kể cả lượt HỎNG: trạng thái, thời lượng và LÝ DO DỪNG.

    Vì sao cần bảng riêng: bảng số (`metrics_matrix`) chỉ có nghĩa với lượt đã chấm xong, nhưng người
    đọc còn cần biết "đã thử những gì, hỏng vì sao" - nếu không thì mỗi lần hỏng lại phải mở từng
    `run.log`/`errors.json` để dò. Lý do lấy từ `errors.json` khi có, không thì lấy `note` của lượt
    chạy (ví dụ "chạy tiếp").
    """
    rows = []
    for run in runs:
        meta = dict(run["meta"] or {})
        metrics = dict(run["metrics"] or {})
        run_info = dict(meta.get("run") or {})
        experiment = dict(meta.get("experiment") or {})
        data = dict(meta.get("data") or {})
        repo = dict(meta.get("repo") or {})
        config = dict(meta.get("config") or {})
        errors = _read_json(run["dir"] / paths.pattern("errors"))
        reasons = [str(item.get("message") or "") for item in (errors.get("errors") or [])]
        rows.append({
            "run": canonical_label(run),
            "status": run_info.get("status"),
            "mode": run_info.get("mode") or dict(metrics.get("resume") or {}).get("mode") or "-",
            "started": run_info.get("started"),
            "seconds": run_info.get("seconds") or dict(metrics.get("cost") or {}).get("giây"),
            "model": experiment.get("model") or metrics.get("model"),
            "method": experiment.get("method") or "-",
            "exp_id": experiment.get("exp_id") or "-",
            "split": metrics.get("split"),
            "version_id": data.get("build"),
            "config_sha256": (config.get("sha256") or "")[:12],
            "repo_sha": (repo.get("sha") or "")[:12],
            "reason": (reasons[0] if reasons else run_info.get("note")) or "",
        })
    return rows


def _dig(data, *keys):
    """Lấy giá trị lồng nhiều lớp; thiếu ở đâu trả None ở đó (báo cáo không chết vì thiếu một khoá)."""
    value = data
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


# ---
# Nhóm 3: model_input
# ---


def model_input_rows():
    """Bảng số đo đầu vào của model, gom mọi file đã có trong nhóm report `model_input`.

    Bảng này do `run_token_stats.py` sinh (nó mới là nơi ĐO số token); ở đây chỉ gom lại và ghi thêm
    cột `file` để biết dòng nào của phiên bản dữ liệu nào. Chưa đo thì bảng RỖNG - và báo cáo nói rõ
    là rỗng, để người đọc phân biệt "chưa đo" với "đo rồi mà không ra gì".

    Chỉ đọc bảng SỐ ĐO (`token_stats*.csv`, mỗi phiên bản dữ liệu một thư mục con). Bảng gom của
    chính nhóm này (`model_input.csv`) là ĐẦU RA của hàm, không phải đầu vào.
    """
    rows, columns = [], []
    root = paths.report("model_input")
    if not root.is_dir():
        return [], [EMPTY_TABLE_COLUMN]
    # CHỈ đọc bảng số đo (`token_stats*.csv`), KHÔNG đọc bảng gom của chính nhóm này: bảng gom là ĐẦU
    # RA, đọc lại nó thì mỗi lần sinh báo cáo lại nạp thêm một bộ cột trùng tên (`file`, `file.1`,
    # ...) và bảng mất nghĩa. Lỗi này đã vào tận file đã commit trước khi bị phát hiện.
    aggregate = (root / Path(paths.pattern("model_input")).name).resolve()
    stems = {Path(paths.pattern("token_stats")).stem}
    found = sorted({path for stem in stems for path in root.rglob("{}*.csv".format(stem))})
    found = [path for path in found if path.resolve() != aggregate]
    for path in found:
        frame = utils.read_csv(path)
        for name in frame.columns:
            if name not in columns:
                columns.append(name)
        for record in frame.to_dict("records"):
            record = dict(record)
            record["file"] = utils.rel(path)
            rows.append(record)
    return rows, (["file"] + columns if rows else [EMPTY_TABLE_COLUMN])


# ---
# Nhóm 4: metrics_matrix
# ---


def column_label(run):
    """Tên CỘT trong ma trận chỉ số: ngắn nhưng đủ để biết cột nào là gì.

    Bảng này có thể có vài cột, mỗi cột là một lượt chạy, nên nhãn phải ngắn: tên thư mục kết quả
    (như trong bảng `experiment_registry`) dài hàng trăm ký tự là không đọc được. Thí nghiệm thì
    dùng `expNNN`; lượt chạy tay thì dùng `<prompt> n<limit>` - hai thứ đã đủ phân biệt, và nhãn
    đầy đủ vẫn nằm trong bảng `experiment_registry`.
    """
    meta = run.get("meta") or {}
    experiment = dict(meta.get("experiment") or {})
    if experiment.get("exp_id"):
        return str(experiment["exp_id"])
    metrics = run.get("metrics") or {}
    limit = (metrics.get("subset") or {}).get("limit")
    return "{} n{}".format(metrics.get("prompt") or canonical_label(run), limit or "all")


def column_labels(runs):
    """Nhãn cột cho CẢ BỘ lượt chạy, bảo đảm KHÔNG TRÙNG NHAU.

    Vì sao phải làm việc này: hai cột cùng tên không báo lỗi mà ghi đè lẫn nhau (từ điển theo nhãn),
    nên số liệu của một lượt chạy biến mất trong im lặng. Chuyện đó xảy ra thật khi so nhiều model:
    mỗi model có thư mục `exp001` riêng, còn nhãn cột chỉ là `exp001`.

    Cách chữa, theo thứ tự: nếu nhãn trùng vì KHÁC MODEL (so Qwen với PhoBERT) thì thêm tên model
    vào trước, vì đó mới là thứ phân biệt được; nếu vẫn trùng (ví dụ hai lần chạy cùng thí nghiệm với
    `n` khác nhau) thì thêm `#2`, `#3`... KHÔNG đánh số thứ tự ngay từ đầu, vì như vậy tên cột phụ
    thuộc thứ tự quét chứ không phụ thuộc nội dung.
    """
    base = [column_label(run) for run in runs]
    groups = {}
    for run, label in zip(runs, base):
        groups.setdefault(label, []).append(short_model(run))
    labels, used = [], {}
    for run, label in zip(runs, base):
        models = {name for name in groups[label] if name}
        if len(groups[label]) > 1 and len(models) > 1:
            label = "{} {}".format(short_model(run), label).strip()
        if label in used:
            used[label] += 1
            label = "{} #{}".format(label, used[label])
        else:
            used[label] = 1
        labels.append(label)
    return labels


def short_model(run):
    """Tên model ngắn (đoạn cuối đường dẫn) - chỉ dùng khi cần phân biệt hai cột cùng nhãn."""
    meta = run.get("meta") or {}
    value = ((meta.get("experiment") or {}).get("model")
             or (run.get("metrics") or {}).get("model") or "")
    text = str(value).replace("\\", "/").strip("/")
    return text.split("/")[-1] if text else ""


def shot_of(run):
    """Số VÍ DỤ few-shot của một lượt chạy (để so với ĐÚNG cột của công bố), hoặc None.

    Nguồn tin cậy là `metrics.json -> prompt_examples.examples`: con số mà chính lượt chạy đã dùng
    (`prompts.examples_info()`), nên không phải suy đoán. Không có (lượt của model encoder, hoặc
    lượt chạy tay) thì trả None - khi đó bảng dùng cột công bố do `--reference-shot` chọn.

    Vì sao phải theo TỪNG LƯỢT: ba mức 0/1/5 ví dụ có chi phí input rất khác nhau (372,50 / 721,50 /
    1.877,50 token/review), nên đem cả ba so với cột `COT+0-shot` là so sai - đúng lỗi đã nằm trong
    bảng `metrics_matrix` trước 27/09/2026.
    """
    metrics = run.get("metrics") or {}
    value = dict(metrics.get("prompt_examples") or {}).get("examples")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        value = None
    if value is not None:
        return int(value)
    name = str(metrics.get("prompt") or "").lower()
    if "zeroshot" in name or "zero_shot" in name or "zero-shot" in name:
        return 0
    for shot in (1, 5):
        if "{}shot".format(shot) in name or "{}_shot".format(shot) in name:
            return shot
    return None


# Cơ sở đo dùng cho bảng ĐEM SO VỚI CÔNG BỐ. `metrics.csv` có cột `basis` (xem metrics.md); bảng
# `metrics_matrix` lấy số ở cơ sở `paper` vì cột công bố cũng đo theo cách đó.
PAPER_BASIS = "paper"


def metric_map(run, basis=None):
    """Bảng `(aspect, sentiment, metric) -> giá trị` của một lượt chạy, đọc từ `metrics.csv`.

    Đọc lại file mà lượt chạy đã ghi, không tính lại: `metrics.csv` là bảng dài nên nó là nguồn
    duy nhất cho mọi cách nhìn khác nhau (theo khía cạnh, theo sắc thái, tổng hợp).

    `basis` chọn CƠ SỞ ĐO (xem docs/04_experiments/metrics.md). Mặc định là `paper` - cách công bố
    đếm - vì bảng `metrics_matrix` là bảng ĐEM SO VỚI CÔNG BỐ, nên số của lượt chạy trong đó phải
    cùng cơ sở. Lượt chạy ghi trước 01/10/2026 chưa có cột `basis` (chỉ có một cơ sở đo), khi đó
    đọc hết như cũ.
    """
    path = run["dir"] / paths.pattern("metrics_csv")
    if not path.is_file():
        return {}
    frame = utils.read_csv(path)
    columns = list(frame.columns)
    wanted = PAPER_BASIS if basis is None else basis
    result = {}
    for record in frame.to_dict("records"):
        if "basis" in columns and str(record.get("basis")) != wanted:
            continue
        key = (str(record.get("aspect")), str(record.get("sentiment")), str(record.get("metric")))
        result[key] = _number(record.get("value"))
    return result


def _number(value):
    """Giá trị trong CSV thành số; không đổi được thì giữ nguyên văn (không đoán, không nuốt lỗi)."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def accuracy_table(runs, reference=None, suffix=None, labels=None):
    """Dòng là KHÍA CẠNH, cột là từng lượt chạy, kèm cột của công bố khi có.

    Giá trị lấy từ dòng `(khía cạnh, all, accuracy)` của `metrics.csv` - độ chính xác trên mọi ô
    của khía cạnh đó, đúng cách bảng của công bố đếm. Khía cạnh CHỈ CÓ trong bảng công bố vẫn được
    giữ thành một dòng (ô của các lượt chạy để trống), để thấy ngay còn thiếu gì.

    Khi bảng CÓ cột công bố, cuối bảng thêm MỘT dòng `aspect_detection` - chỉ số RIÊNG của dự án
    (bài nêu task phát hiện khía cạnh nhưng không có bảng số cho nó), nên số lấy từ lượt chạy và ô
    công bố của dòng đó để TRỐNG.

    `labels`: nhãn cột đã tính sẵn cho CẢ BỘ lượt chạy (xem `column_labels`). Phải truyền vào khi
    ghép bảng của nhiều mức ví dụ: tính lại trong từng nhóm thì hai nhóm có thể ra cùng một nhãn và
    bảng ghép sẽ có hai cột trùng tên - đúng loại lỗi `column_labels` sinh ra để chặn.
    """
    labels = list(labels) if labels is not None else column_labels(runs)
    maps = [metric_map(run) for run in runs]
    aspects = sorted({key[0].lower() for item in maps for key in item
                      if key[1:] == ("all", "accuracy")})
    if reference:
        aspects = sorted(set(aspects) | {name for name in reference
                                         if name != "aspect_detection"})
    reference_column = (suffix or "reference") if reference else None
    columns = ["aspect"] + labels + ([reference_column] if reference_column else [])
    rows = []
    for aspect in aspects:
        row = {"aspect": aspect}
        for label, item in zip(labels, maps):
            row[label] = _blank(item.get((aspect, "all", "accuracy")))
        if reference_column:
            row[reference_column] = _blank((reference or {}).get(aspect))
        rows.append(row)
    detected = [_dig(run.get("metrics") or {}, "scores", "aspect_detection", "micro", "accuracy")
                for run in runs]
    reference_detection = (reference or {}).get("aspect_detection")
    if reference_column and (reference_detection is not None
                             or any(value is not None for value in detected)):
        # `aspect_detection` là chỉ số RIÊNG của dự án: bài nêu task phát hiện khía cạnh nhưng KHÔNG
        # có bảng số cho nó, nên số lấy từ LƯỢT CHẠY và ô công bố để trống - hiện một con số vào ô
        # đó là hứa một phép so không tồn tại. Vẫn để ở CUỐI bảng, không xen vào danh sách khía cạnh.
        row = {"aspect": "aspect_detection"}
        for label, value in zip(labels, detected):
            row[label] = _blank(value)
        row[reference_column] = _blank(reference_detection)
        rows.append(row)
    return columns, rows


def prf_table(runs, reference=None, suffix=None, labels=None):
    """Dòng là (khía cạnh, sắc thái), cột là precision/recall/f1 của từng lượt chạy.

    Cùng định dạng với bảng P R F1 của công bố: mỗi khía cạnh một dòng cho mỗi sắc thái CÓ NHÃN
    (không gộp `all`, không lấy dòng `mentioned` - đó là cách đếm khác, xem metrics.md). Ô nào của
    công bố mà lượt chạy chưa có thì vẫn thành một dòng, với ô của lượt chạy để trống.

    `labels`: như ở `accuracy_table` - nhãn cột đã tính sẵn cho cả bộ lượt chạy.
    """
    labels = list(labels) if labels is not None else column_labels(runs)
    maps = [metric_map(run) for run in runs]
    cells = {(key[0].lower(), key[1].lower()) for item in maps for key in item
             if key[2] in ("precision", "recall", "f1")
             and key[1] not in ("all", "mentioned")}
    if reference:
        cells |= {key for key in reference if isinstance(key, tuple) and len(key) == 2}
    cells = sorted(cells)
    reference_column = (suffix or "reference") if reference else None
    metrics = (("precision", "P"), ("recall", "R"), ("f1", "F1"))
    columns = ["aspect", "sentiment"]
    for label in labels:
        columns += ["{} {}".format(label, short) for _metric, short in metrics]
    if reference_column:
        columns += ["{} {}".format(reference_column, short) for _metric, short in metrics]
    rows = []
    for aspect, sentiment in cells:
        row = {"aspect": aspect, "sentiment": sentiment}
        for label, item in zip(labels, maps):
            for metric, short in metrics:
                row["{} {}".format(label, short)] = _blank(item.get((aspect, sentiment, metric)))
        if reference_column:
            reference_cell = (reference or {}).get((aspect, sentiment)) or {}
            for metric, short in metrics:
                row["{} {}".format(reference_column, short)] = _blank(
                    reference_cell.get(metric))
        rows.append(row)
    return columns, rows


def _blank(value):
    """Ô trống khi thiếu số, để bảng không hiện `None` - người đọc hiểu ngay là chưa có."""
    return "" if value is None else value


# ---
# Ghi ba định dạng
# ---


def write_group(name, tables, mermaid, out_dir=None):
    """Ghi một nhóm report: CSV nguồn, một HTML trình bày, và một MD CHỈ có sơ đồ Mermaid.

    `tables` là `{tên file csv: (cột, dòng)}`. Trả về dict đường dẫn để nơi gọi in ra và để test kiểm.
    """
    directory = Path(out_dir) if out_dir else paths.report(name)
    directory.mkdir(parents=True, exist_ok=True)
    written, total = {}, 0
    for file_name, (columns, rows) in tables.items():
        written[file_name] = utils.write_csv(
            [[row.get(column, "") for column in columns] for row in rows], columns,
            directory / file_name)
        total += len(rows)
    html_path = directory / "{}.html".format(name)
    html_path.write_text(html_page(name, tables, empty=(total == 0)), encoding="utf-8")
    md_path = directory / "{}.md".format(name)
    md_path.write_text(markdown_diagram(name, mermaid), encoding="utf-8")
    return {"csv": written, "html": html_path, "md": md_path, "rows": total}


# Ghi chú in đầu trang HTML của nhóm bảng ĐEM SO VỚI CÔNG BỐ. Cùng một ô được đo trên hai cơ sở,
# nên trang phải nói rõ đang đọc cơ sở nào - nếu không thì người đọc so số `all` với số công bố.
COMPARISON_NOTE = {
    "metrics_matrix": (
        "Cột công bố là cột của ĐÚNG mức ví dụ của từng lượt (lượt không có mức ví dụ dùng cột do "
        "<code>--reference-shot</code> chọn). Số của lượt chạy ở đây là <b>cơ sở đo "
        "<code>paper</code></b> - cách công bố đếm: chỉ giữ ô mà CẢ nhãn đúng VÀ nhãn đoán là "
        "positive/negative. Mẫu số vì thế nhỏ hơn cơ sở <code>all</code>; số ô bị loại nằm ở khoá "
        "<code>paper</code> trong <code>metrics.json</code> của từng lượt, và cơ sở "
        "<code>all</code> nằm ở khoá <code>scores</code>."),
}


def html_page(name, tables, empty=False):
    """Trang HTML tự chứa: chỉ bảng, không Plotly, không mạng, không thư viện ngoài.

    Nhóm bảng đem so với công bố (`metrics_matrix`) có thêm một ghi chú in ở đầu trang: người đọc
    số phải biết số của lượt chạy đang ở CƠ SỞ ĐO nào, vì cùng một ô được đo hai lần (xem
    `docs/04_experiments/metrics.md`).
    """
    parts = ["<!DOCTYPE html>", '<html lang="vi">', "<head>", '<meta charset="utf-8">',
             "<title>{}</title>".format(html.escape(name)), "<style>",
             "body{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:24px;color:#222}",
             "table{border-collapse:collapse;margin:0 0 28px;font-size:13px}",
             "th,td{border:1px solid #ccc;padding:4px 8px;text-align:left;vertical-align:top}",
             "th{background:#f2f2f2}", "caption{text-align:left;font-weight:600;padding:6px 0}",
             ".scroll{overflow:auto;max-height:70vh}", ".empty{color:#a00}",
             ".note{background:#fffbe6;border:1px solid #e6d9a2;padding:8px 10px;max-width:900px}",
             "</style>", "</head>", "<body>", "<h1>{}</h1>".format(html.escape(name)),
             "<p>Sinh tự động bằng <code>python scripts/collect_reports.py</code>. Số liệu đọc lại "
             "từ file của từng lượt chạy; sơ đồ quan hệ nằm ở <code>{}.md</code>.</p>".format(
                 html.escape(name))]
    note = COMPARISON_NOTE.get(name)
    if note:
        parts.append('<p class="note">{}</p>'.format(note))
    if empty:
        parts.append('<p class="empty">{}</p>'.format(html.escape(NO_DATA.upper())))
    for file_name, (columns, rows) in tables.items():
        parts.append('<div class="scroll"><table>')
        parts.append("<caption>{}</caption>".format(html.escape(file_name)))
        parts.append("<tr>" + "".join("<th>{}</th>".format(html.escape(str(column)))
                                      for column in columns) + "</tr>")
        for row in rows:
            parts.append("<tr>" + "".join(
                "<td>{}</td>".format(html.escape(str(_blank(row.get(column)))))
                for column in columns) + "</tr>")
        parts.append("</table></div>")
    parts += ["</body>", "</html>", ""]
    return "\n".join(parts)


def markdown_diagram(name, mermaid):
    """File .md CHỈ có sơ đồ Mermaid, thêm một dòng tiêu đề để GitHub hiện đúng tên nhóm."""
    return "# {}\n\n```mermaid\n{}\n```\n".format(name, mermaid.strip())


def mermaid_graph(edges, isolated=()):
    """Sơ đồ Mermaid từ danh sách `(nguồn, nhãn cung, đích)`.

    Tên nút được đánh mã `n1`, `n2`, ... vì Mermaid không nhận mọi ký tự có trong tên thật (`/`,
    `@`, `.`, khoảng trắng). Nhãn hiển thị để riêng trong ngoặc vuông, đã thay dấu ngoặc kép - để
    một cái tên có dấu nháy không làm hỏng cả sơ đồ.
    """
    ids, lines = {}, []

    def node(name):
        if name not in ids:
            ids[name] = "n{}".format(len(ids) + 1)
            lines.append('  {}["{}"]'.format(ids[name], str(name).replace('"', "'")))
        return ids[name]

    for source, _label, target in edges:
        node(source)
        node(target)
    for name in isolated:
        node(name)
    for source, label, target in edges:
        arrow = "-->|{}|".format(str(label).replace("|", "/")) if label else "-->"
        lines.append("  {} {} {}".format(ids[source], arrow, ids[target]))
    if not lines:
        return 'graph LR\n  n1["{}"]'.format(NO_DATA)
    return "\n".join(["graph LR"] + lines)


# ---
# Ghép lại: bảng của từng nhóm, và sinh cả năm nhóm
# ---

GROUPS = tuple(CSV_NAME)


def load_reference(directory=None, shot=0):
    """Đọc bảng số của CÔNG BỐ, trả về `(accuracy, prf, nhãn_cột)`.

    Bảng công bố nằm trong `paths.reference_publication_dir()` (`data/reference_publication/`); tên
    file và tên cột là CỐ ĐỊNH, lấy đúng như bản đã nhận:
        accuracy_by_aspect.csv                cột `Aspect`, `COT+0-shot`, `COT+1-shot`, `COT+5-shot`
        prf_by_aspect_sentiment_<n>shot.csv   cột `Aspect`, `Sentiment`, `Precision`, `Recall`, `F1`
    Bản công bố ghi P/R/F1 theo PHẦN TRĂM (97.06), còn `metrics.csv` của dự án ghi theo tỉ lệ 0..1,
    nên P/R/F1 của công bố được chia 100 khi đọc vào - để hai bên cùng thang đo rồi mới so. Độ chính
    xác thì cả hai bên đều theo phần trăm, không đổi gì.

    Cột nhãn của file này từng bị LỆCH MỘT HÀNG so với Table 3 của bài (bản nhận 24/09/2026): hàng
    cuối ghi `Aspect` trong khi đó là số của `Shipping`, còn hàng `Smell` bị thiếu - đã chữa ngày
    01/10/2026 sau khi đối chiếu từng số với Table 3. Bộ đọc KHÔNG đổi tên hàng nào, nên một file
    lệch sẽ hiện thành một dòng sai tên (nhìn thấy được) thay vì thành một chỉ số mang tên khác
    (không nhìn thấy được); `tests/reporting/test_reference_file.py` khoá cấu trúc file thật lại.

    `shot` chọn cột 0/1/5-shot của công bố. Chưa có file thì trả về `(None, None, None)` và cột công
    bố KHÔNG xuất hiện - thà thiếu cột còn hơn hiện một cột toàn ô trống.
    """
    directory = Path(directory) if directory else paths.reference_publication_dir()
    accuracy, prf, suffix = None, None, None

    path = directory / "accuracy_by_aspect.csv"
    if path.is_file():
        frame = utils.read_csv(path)
        column = _shot_column(list(frame.columns), shot)
        if column:
            accuracy = {}
            for row in frame.to_dict("records"):
                name = str(row.get("Aspect") or row.get("aspect") or "").strip().lower()
                if name:
                    # Tên hàng KHÔNG được đổi thành chỉ số nào: chữ `Aspect` là chữ tiêu đề, không
                    # phải tên một khía cạnh. Hàng `Aspect` của bản nhận 24/09/2026 là hàng `Shipping`
                    # bị ghi nhầm nhãn (xem docstring); đổi tên nó thành `aspect_detection` chính là
                    # cách một con số lệch nhãn lọt vào bảng so công bố mà bảng vẫn trông hợp lý.
                    accuracy[name] = _number(row.get(column))
            suffix = str(column)

    path = directory / "prf_by_aspect_sentiment_{}shot.csv".format(shot)
    if path.is_file():
        prf = {}
        for row in utils.read_csv(path).to_dict("records"):
            key = (str(row.get("Aspect") or row.get("aspect") or "").strip().lower(),
                   str(row.get("Sentiment") or row.get("sentiment") or "").strip().lower())
            prf[key] = {metric: _scale(_number(row.get(metric.capitalize())
                                               if row.get(metric.capitalize()) is not None
                                               else row.get(metric)))
                        for metric in ("precision", "recall", "f1")}
        suffix = suffix or "COT+{}shot".format(shot)
    return accuracy, prf, suffix


def _shot_column(columns, shot):
    """Tên cột của công bố ứng với số ví dụ đang xét (`COT+0-shot`, ...)."""
    wanted = "{}-shot".format(shot)
    for name in columns:
        if wanted in str(name):
            return name
    return None


def _scale(value):
    """Đưa P/R/F1 của công bố về cùng thang 0..1 với `metrics.csv` của dự án.

    Bảng công bố ghi 97.06 cho F1 (phần trăm), dự án ghi 0.97 (tỉ lệ) - để nguyên thì hai cột cạnh
    nhau trong cùng một bảng là hai thang đo khác nhau, và người đọc sẽ so 0.667 với 97.06.
    """
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value > 1:
        return round(value / 100.0, 6)
    return value


def merge_tables(tables, keys):
    """Ghép nhiều bảng cùng khoá dòng thành MỘT bảng, giữ thứ tự cột.

    Dùng cho `metrics_matrix`: mỗi mức ví dụ có cột công bố riêng (0/1/5-shot), nên bảng của từng
    nhóm được ghép lại thành một bảng - cột của nhóm nào đối chiếu cột công bố của chính nhóm đó, mà
    không phải tách thành ba bảng cho khó đọc hơn.

    Dòng `aspect_detection` (nếu có) luôn xuống CUỐI, đúng như `accuracy_table` đặt nó.
    """
    columns, seen, merged = list(keys), set(keys), {}
    for table_columns, rows in tables:
        for item in table_columns:
            if item not in seen:
                seen.add(item)
                columns.append(item)
        for row in rows:
            key = tuple(str(row.get(part, "")) for part in keys)
            target = merged.setdefault(key, {part: "" for part in keys})
            target.update(row)
    order = sorted(merged, key=lambda key: (key[-1] == "aspect_detection", key))
    return columns, [merged[key] for key in order]


def group_tables(name, runs, reference=None):
    """Bảng và sơ đồ của MỘT nhóm, để `build()` chỉ còn việc ghi và báo."""
    accuracy_ref, prf_ref, suffix = reference or (None, None, None)
    if name == "dataset_registry":
        rows = dataset_rows()
        used = {}
        for run in runs:
            build = (run["meta"].get("data") or {}).get("build")
            used.setdefault(build, []).append(canonical_label(run))
        edges = []
        for row in rows:
            edges.append(("<nguồn {}>".format(row["version"]), "{} dòng".format(row["rows"]),
                          row["build"]))
            for label in used.get(row["build"], []):
                edges.append((row["build"], "", label))
        columns = list(rows[0]) if rows else ["dataset", "version", "build", "parent", "on_disk",
                                             "splits", "rows", "eval_locked", "aspects", "raw_dir",
                                             "config"]
        return {CSV_NAME[name]: (columns, rows)}, mermaid_graph(edges)
    if name == "experiment_registry":
        rows = experiment_rows(runs)
        edges = [(row["run"], row["mode"], row["version_id"] or "chưa rõ dữ liệu")
                 for row in rows]
        return {CSV_NAME[name]: (list(REGISTRY_COLUMNS), rows)}, mermaid_graph(edges)
    if name == "model_input":
        rows, columns = model_input_rows()
        # Mỗi DÒNG số đo là một dòng của bảng, KHÔNG phải một cung: khử trùng cặp (thư mục phiên
        # bản, model) trước khi vẽ. Không khử thì sơ đồ lặp cùng một cung hàng chục lần (đã vào tận
        # file .md đã commit) và node `model_input` đứng cô lập.
        pairs = sorted({(Path(str(row.get("file") or "")).parent.name or "model_input",
                         row.get("model_id") or row.get("model") or "model") for row in rows})
        edges = [(source, "", target) for source, target in pairs]
        return {CSV_NAME[name]: (columns, rows)}, mermaid_graph(edges, isolated=["model_input"])
    if name == "metrics_matrix":
        # Cột đối chiếu công bố chọn THEO TỪNG LƯỢT, theo đúng mức ví dụ của lượt đó (0/1/5-shot).
        # Lượt không suy ra được mức (model encoder, lượt chạy tay) dùng cột do `--reference-shot`
        # chọn - nhờ vậy không mức nào bị so nhầm cột, và lượt cũ vẫn giữ cách đối chiếu như trước.
        labels = column_labels(runs)
        groups = {}
        for run, label in zip(runs, labels):
            groups.setdefault(shot_of(run), []).append((run, label))
        accuracy_parts, prf_parts, edges = [], [], []
        for shot in sorted(groups, key=lambda item: (item is None, item if item is not None else 0)):
            items = groups[shot]
            group_runs = [run for run, _label in items]
            group_labels = [label for _run, label in items]
            chosen = load_reference(shot=shot) if shot is not None else (
                accuracy_ref, prf_ref, suffix)
            if not any(chosen):
                # Mức ví dụ này không có cột trong bảng công bố (ví dụ prompt 2 ví dụ của dự án):
                # không có cột đối chiếu còn hơn gán một cột không tồn tại.
                chosen = (None, None, None)
            accuracy_parts.append(accuracy_table(group_runs, chosen[0], chosen[2],
                                                 labels=group_labels))
            prf_parts.append(prf_table(group_runs, chosen[1], chosen[2],
                                       labels=group_labels))
            if chosen[2]:
                edges += [("<công bố {}>".format(chosen[2]), "so với", label)
                          for label in group_labels]
        if not groups and any((accuracy_ref, prf_ref, suffix)):
            # Chưa có lượt chạy nào (hoặc bảng đang rỗng): vẫn hiện cột công bố để người đọc thấy
            # mốc cần vượt thay vì một bảng trắng - giữ đúng hành vi của bảng đã commit.
            accuracy_parts.append(accuracy_table([], accuracy_ref, suffix))
            prf_parts.append(prf_table([], prf_ref, suffix))
        edges += [(label, "chấm trên",
                   (run["meta"].get("data") or {}).get("build") or "chưa rõ dữ liệu")
                  for run, label in zip(runs, labels)]
        tables = {TABLE_NAMES[name][0]: merge_tables(accuracy_parts, ("aspect",)),
                  TABLE_NAMES[name][1]: merge_tables(prf_parts, ("aspect", "sentiment"))}
        return tables, mermaid_graph(edges)
    if name == "attempt_registry":
        rows = attempt_rows(runs)
        edges = [(row["run"], row["status"] or "không rõ",
                  "commit {}".format(row["repo_sha"] or "?")) for row in rows]
        return {CSV_NAME[name]: (list(ATTEMPT_COLUMNS), rows)}, mermaid_graph(edges)
    raise ReportError("Không có nhóm report {!r}. Nhóm đang có: {}.".format(
        name, ", ".join(GROUPS)))


def finished(runs):
    """Chỉ những lượt đã chạy XONG: bảng số chỉ có nghĩa với lượt này (lượt hỏng không có `metrics.json`)."""
    return [run for run in runs
            if dict(run["meta"].get("run") or {}).get("status") == "FINISHED"]


def build(roots=None, out_root=None, groups=None, reference=None, only="finished"):
    """Sinh các nhóm report, trả về `{tên nhóm: {csv, html, md, rows}}`.

    `roots` là các gốc chứa lượt chạy (mặc định: gốc kết quả của thí nghiệm và thư mục đánh giá chạy
    tay). `out_root` để trống thì ghi vào đúng nhóm report khai trong `configs/paths.yaml`; truyền
    vào khi cần ghi ra chỗ khác (Colab ghi vào Drive - xem docs/06_plan/P6_reports_ci.md mục 5).

    `only` quyết định lượt NÀO vào bảng: `"finished"` (mặc định) chỉ lượt chạy xong, `"all"` liệt kê cả
    lượt hỏng. Nhóm `attempt_registry` LUÔN nhận đủ mọi lượt, vì việc của nó là kể lại đã thử những gì.
    """
    runs = scan_runs(roots)
    result = {}
    for name in (groups or GROUPS):
        # `attempt_registry` là "bản tổng hợp toàn bộ"; các nhóm còn lại là bảng để đọc số.
        subset = runs if (name == "attempt_registry" or only == "all") else finished(runs)
        tables, mermaid = group_tables(name, subset, reference)
        out_dir = (Path(out_root) / name) if out_root else paths.report(name)
        result[name] = write_group(name, tables, mermaid, out_dir)
    return result





