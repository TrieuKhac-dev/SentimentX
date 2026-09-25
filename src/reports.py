# -*- coding: utf-8 -*-
"""Sinh BỐN NHÓM bảng tổng hợp từ bản ghi lần chạy và bảng chỉ số đã có trên đĩa.

VÌ SAO ĐỌC LẠI FILE, KHÔNG TÍNH LẠI
Mọi con số vào bảng đều lấy từ file mà chính lượt chạy đã ghi (`run_meta.json`, `metrics.json`,
`metrics.csv`, `model_input.csv`). Tính lại từ dữ liệu gốc là có hai đường tính cho cùng một con số,
và khi hai đường lệch nhau thì không ai biết đường nào đúng. Bảng tổng hợp chỉ TRÌNH BÀY.

BỐN NHÓM (tên lấy từ `configs/paths.yaml`, xem docs/05_config/01_paths.md)
    dataset_registry      mỗi PHIÊN BẢN DỮ LIỆU một dòng: có gì, sinh từ đâu, đang dùng ở đâu
    experiment_registry   mỗi LƯỢT CHẠY một dòng: code, cấu hình, dữ liệu, trạng thái, chi phí
    model_input           số đo đầu vào của model (do run_token_stats.py ghi; ở đây trình bày lại)
    metrics_matrix        ma trận chỉ số: dòng là khía cạnh (hoặc khía cạnh × sắc thái), cột là
                          TỪNG LƯỢT CHẠY, kèm cột `reference` chứa số của công bố khi có

MỖI NHÓM GHI BA THỨ
    <tên>.csv    bảng nguồn: mở được bằng Excel/pandas, và là thứ người khác đọc lại để kiểm
    <tên>.html   bảng trình bày: tự chứa, không cần mạng, không cần thư viện vẽ
    <tên>.md      CHỈ sơ đồ Mermaid: quan hệ giữa các dòng. Số liệu không chép lại vào đây - chép
                  là có bản sao thứ hai của cùng một con số, rồi hai bản lệch nhau.

Nhóm nào chưa có dữ liệu thì vẫn ghi bảng RỖNG kèm một dòng giải thích, chứ không im lặng bỏ qua:
người đọc cần phân biệt "chưa chạy" với "chạy rồi mà không ra gì".
"""

import html
import json
from pathlib import Path

from src import config, dataset as dataset_module, paths, utils, versioning

NO_DATA = "chưa có dữ liệu"

# Tên file CSV nguồn của mỗi nhóm. Nhóm có nhiều bảng thì tên ở đây là bảng CHÍNH; các bảng phụ
# khai trong `TABLE_NAMES` (metrics_matrix có hai bảng, đúng như docs/04_experiments/metrics.md).
CSV_NAME = {
    "dataset_registry": "dataset_registry.csv",
    "experiment_registry": "experiment_registry.csv",
    "model_input": "model_input.csv",
    "metrics_matrix": "accuracy_by_aspect.csv",
}

TABLE_NAMES = {
    "metrics_matrix": ("accuracy_by_aspect.csv", "prf_by_aspect_sentiment.csv"),
}

# Nhãn cột của bảng CHƯA có số đo: báo cáo vẫn sinh ra, kèm dấu hiệu RỖNG để người đọc phân biệt
# "chưa đo" với "đo rồi mà không ra gì".
EMPTY_TABLE_COLUMN = "model_input"

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
            ma = versioning.compute_id(cfg)
            directory = versioning.processed_dir(ma)
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
                "ma": ma,
                "on_disk": "yes" if directory.is_dir() else "no",
                "splits": ", ".join("{}={}".format(key, splits[key]) for key in sorted(splits)),
                "rows": sum(splits.values()),
                "eval_locked": ", ".join(locked) or NO_DATA,
                "aspects": ", ".join(cfg.get("aspects") or []),
                "raw_dir": str(cfg.get("raw_dir") or ""),
                "config": utils.rel(dataset_module.config_path(name, version)),
            })
    return rows


def _row_count(path):
    """Số DÒNG DỮ LIỆU của một file CSV (không đọc cả file vào bộ nhớ)."""
    with open(path, "r", encoding="utf-8-sig", errors="replace") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


# ---
# Nhóm 2: experiment_registry
# ---

REGISTRY_COLUMNS = ("run", "status", "started", "seconds", "model", "method", "exp_id", "split",
                    "prompt", "prompt_sha", "examples_sha", "n_samples", "subset", "decoding",
                    "quant", "max_length", "max_new_tokens", "dataset", "version_id",
                    "config_sha256", "repo_sha", "mode", "read_percent", "tokens_per_second",
                    "accuracy_micro", "f1_macro", "exact_match_percent", "out_dir")


def experiment_rows(runs):
    """Mỗi LƯỢT CHẠY một dòng: code đã chạy, cấu hình, dữ liệu, trạng thái và chi phí.

    Con số lấy từ `run_meta.json` (code, dữ liệu, trạng thái) và `metrics.json` (cấu hình, kết quả,
    chi phí) - hai file mà chính lượt chạy đã ghi; không tính lại gì từ dữ liệu gốc.
    """
    rows = []
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
            "n_samples": metrics.get("n_samples"),
            "subset": "limit={} seed={}".format(subset.get("limit") or "cả split",
                                                subset.get("seed", "-")),
            "decoding": "sample" if generation.get("do_sample") else "greedy",
            "quant": metrics.get("quant"),
            "dtype": dict(meta.get("env") or {}).get("dtype") or "-",
            "max_length": metrics.get("max_length"),
            "max_new_tokens": generation.get("max_new_tokens"),
            "dataset": data.get("dataset"),
            "version_id": data.get("ma"),
            "config_sha256": (config.get("sha256") or "")[:12],
            "repo_sha": (repo.get("sha") or "")[:12],
            "mode": dict(metrics.get("resume") or {}).get("mode") or "-",
            "read_percent": dict(metrics.get("read_rate") or {}).get("% đọc được"),
            "tokens_per_second": cost.get("token sinh/giây"),
            "accuracy_micro": _dig(metrics, "scores", "aggregate", "accuracy_micro"),
            "f1_macro": _dig(metrics, "scores", "prf", "macro", "f1"),
            "exact_match_percent": _dig(metrics, "scores", "aggregate", "exact_match", "percent"),
            "out_dir": utils.rel(run["dir"]),
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

    Nhận CẢ HAI tên file: số đo (`token_stats*.csv`, mỗi phiên bản một thư mục con) và bảng gom của
    chính nhóm này (`model_input*.csv`). Chỉ quét một tên thì số đo không bao giờ vào được báo cáo,
    mà báo cáo vẫn sinh ra bình thường nên không ai thấy thiếu.
    """
    rows, columns = [], []
    root = paths.report("model_input")
    if not root.is_dir():
        return [], [EMPTY_TABLE_COLUMN]
    stems = {Path(paths.pattern("model_input")).stem,
             Path(paths.pattern("token_stats")).stem}
    found = sorted({path for stem in stems for path in root.rglob("{}*.csv".format(stem))})
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


def metric_map(run):
    """Bảng `(aspect, sentiment, metric) -> giá trị` của một lượt chạy, đọc từ `metrics.csv`.

    Đọc lại file mà lượt chạy đã ghi, không tính lại: `metrics.csv` là bảng dài nên nó là nguồn
    duy nhất cho mọi cách nhìn khác nhau (theo khía cạnh, theo sắc thái, tổng hợp).
    """
    path = run["dir"] / paths.pattern("metrics_csv")
    if not path.is_file():
        return {}
    frame = utils.read_csv(path)
    result = {}
    for record in frame.to_dict("records"):
        key = (str(record.get("aspect")), str(record.get("sentiment")), str(record.get("metric")))
        result[key] = _number(record.get("value"))
    return result


def _number(value):
    """Giá trị trong CSV thành số; không đổi được thì giữ nguyên văn (không đoán, không nuốt lỗi)."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def accuracy_table(runs, reference=None, suffix=None):
    """Dòng là KHÍA CẠNH, cột là từng lượt chạy, kèm cột của công bố khi có.

    Giá trị lấy từ dòng `(khía cạnh, all, accuracy)` của `metrics.csv` - độ chính xác trên mọi ô
    của khía cạnh đó, đúng cách bảng của công bố đếm. Khía cạnh CHỈ CÓ trong bảng công bố vẫn được
    giữ thành một dòng (ô của các lượt chạy để trống), để thấy ngay còn thiếu gì.
    """
    labels = column_labels(runs)
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
    if reference and "aspect_detection" in reference:
        # Dòng `Aspect` của công bố là PHÁT HIỆN khía cạnh (review có nhắc khía cạnh đó hay không),
        # không phải độ chính xác của một khía cạnh. Để ở CUỐI bảng, không xen vào danh sách khía cạnh.
        row = {"aspect": "aspect_detection"}
        for label, run in zip(labels, runs):
            row[label] = _blank(_dig(run.get("metrics") or {}, "scores", "aspect_detection",
                                     "micro", "accuracy"))
        row[reference_column] = _blank(reference["aspect_detection"])
        rows.append(row)
    return columns, rows


def prf_table(runs, reference=None, suffix=None):
    """Dòng là (khía cạnh, sắc thái), cột là precision/recall/f1 của từng lượt chạy.

    Cùng định dạng với bảng P R F1 của công bố: mỗi khía cạnh một dòng cho mỗi sắc thái CÓ NHÃN
    (không gộp `all`, không lấy dòng `mentioned` - đó là cách đếm khác, xem metrics.md). Ô nào của
    công bố mà lượt chạy chưa có thì vẫn thành một dòng, với ô của lượt chạy để trống.
    """
    labels = column_labels(runs)
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


def html_page(name, tables, empty=False):
    """Trang HTML tự chứa: chỉ bảng, không Plotly, không mạng, không thư viện ngoài."""
    parts = ["<!DOCTYPE html>", '<html lang="vi">', "<head>", '<meta charset="utf-8">',
             "<title>{}</title>".format(html.escape(name)), "<style>",
             "body{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:24px;color:#222}",
             "table{border-collapse:collapse;margin:0 0 28px;font-size:13px}",
             "th,td{border:1px solid #ccc;padding:4px 8px;text-align:left;vertical-align:top}",
             "th{background:#f2f2f2}", "caption{text-align:left;font-weight:600;padding:6px 0}",
             ".scroll{overflow:auto;max-height:70vh}", ".empty{color:#a00}",
             "</style>", "</head>", "<body>", "<h1>{}</h1>".format(html.escape(name)),
             "<p>Sinh tự động bằng <code>python scripts/collect_reports.py</code>. Số liệu đọc lại "
             "từ file của từng lượt chạy; sơ đồ quan hệ nằm ở <code>{}.md</code>.</p>".format(
                 html.escape(name))]
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
# Ghép lại: bảng của từng nhóm, và sinh cả bốn nhóm
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
                    # Dòng `Aspect` của công bố là PHÁT HIỆN khía cạnh (có nhắc tới hay không),
                    # không phải độ chính xác của một khía cạnh - đổi tên cho khỏi lẫn.
                    accuracy["aspect_detection" if name == "aspect" else name] = _number(
                        row.get(column))
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


def group_tables(name, runs, reference=None):
    """Bảng và sơ đồ của MỘT nhóm, để `build()` chỉ còn việc ghi và báo."""
    accuracy_ref, prf_ref, suffix = reference or (None, None, None)
    if name == "dataset_registry":
        rows = dataset_rows()
        used = {}
        for run in runs:
            ma = (run["meta"].get("data") or {}).get("ma")
            used.setdefault(ma, []).append(canonical_label(run))
        edges = []
        for row in rows:
            edges.append(("<nguồn {}>".format(row["version"]), "{} dòng".format(row["rows"]),
                          row["ma"]))
            for label in used.get(row["ma"], []):
                edges.append((row["ma"], "", label))
        columns = list(rows[0]) if rows else ["dataset", "version", "ma", "on_disk", "splits",
                                             "rows", "eval_locked", "aspects", "raw_dir", "config"]
        return {CSV_NAME[name]: (columns, rows)}, mermaid_graph(edges)
    if name == "experiment_registry":
        rows = experiment_rows(runs)
        edges = [(row["run"], row["mode"], row["version_id"] or "chưa rõ dữ liệu")
                 for row in rows]
        return {CSV_NAME[name]: (list(REGISTRY_COLUMNS), rows)}, mermaid_graph(edges)
    if name == "model_input":
        rows, columns = model_input_rows()
        edges = []
        for row in rows:
            file_name = Path(str(row.get("file") or "")).parent.name or "model_input"
            edges.append((file_name, "", row.get("model_id") or row.get("model") or "model"))
        return {CSV_NAME[name]: (columns, rows)}, mermaid_graph(edges, isolated=["model_input"])
    if name == "metrics_matrix":
        edges = [(label, "chấm trên",
                  (run["meta"].get("data") or {}).get("ma") or "chưa rõ dữ liệu")
                 for run, label in zip(runs, column_labels(runs))]
        if accuracy_ref or prf_ref:
            edges = [("<công bố>", "so với", source) for source, _label, _target in edges] + edges
        tables = {TABLE_NAMES[name][0]: accuracy_table(runs, accuracy_ref, suffix),
                  TABLE_NAMES[name][1]: prf_table(runs, prf_ref, suffix)}
        return tables, mermaid_graph(edges)
    raise ReportError("Không có nhóm report {!r}. Nhóm đang có: {}.".format(
        name, ", ".join(GROUPS)))


def build(roots=None, out_root=None, groups=None, reference=None):
    """Sinh các nhóm report, trả về `{tên nhóm: {csv, html, md, rows}}`.

    `roots` là các gốc chứa lượt chạy (mặc định: gốc kết quả của thí nghiệm và thư mục đánh giá chạy
    tay). `out_root` để trống thì ghi vào đúng nhóm report khai trong `configs/paths.yaml`; truyền
    vào khi cần ghi ra chỗ khác (Colab ghi vào Drive - xem docs/06_plan/P6_reports_ci.md mục 5).
    """
    runs = scan_runs(roots)
    result = {}
    for name in (groups or GROUPS):
        tables, mermaid = group_tables(name, runs, reference)
        out_dir = (Path(out_root) / name) if out_root else paths.report(name)
        result[name] = write_group(name, tables, mermaid, out_dir)
    return result





