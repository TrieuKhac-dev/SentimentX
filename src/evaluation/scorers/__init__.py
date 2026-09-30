# -*- coding: utf-8 -*-
"""Registry các BỘ CHẤM ĐIỂM, và chỗ DUY NHẤT ghi file chỉ số của một lần chạy.

    metrics.json        toàn bộ chỉ số, kèm `label_space`, `neutral_policy`, số ô neutral bị loại
    metrics.csv         bảng dài (aspect, sentiment, metric, value) để so giữa các thí nghiệm
    mispredictions.csv  chỉ các ô đoán sai, kèm khía cạnh, nhãn đúng, nhãn đoán
    plots/accuracy.html biểu đồ của lượt chạy (HTML tự chứa, bật/tắt bằng `save.plots`)

Bộ chấm nào chạy là do `evaluation.scores` trong `configs/experiments/evaluation.yaml` quyết
định; tên lạ thì `check()` báo lỗi kèm danh sách chứ KHÔNG im lặng bỏ qua - bỏ qua thì bảng kết
quả thiếu một chỉ số mà người đọc không biết là thiếu.

THÊM MỘT BỘ CHẤM MỚI
    Viết một module trong thư mục này theo hợp đồng ở `base.py`, rồi thêm một dòng vào `SCORERS`.
    Không phải sửa bộ chấm nào đang có. Xem docs/04_experiments/metrics.md.
"""

import html
from pathlib import Path

from src.core import paths, utils
from src.evaluation.scorers import (
    accuracy,
    aggregate,
    aspect_detection,
    base,
    confusion,
    prf,
)

# Các bộ chấm đang có. Thứ tự ở đây là thứ tự đọc bảng kết quả.
SCORERS = {
    accuracy.NAME: accuracy,
    aspect_detection.NAME: aspect_detection,
    prf.NAME: prf,
    aggregate.NAME: aggregate,
    confusion.NAME: confusion,
}

# Cột của file kết quả. Bảng dài để nối kết quả nhiều thí nghiệm vào cùng một bảng.
CSV_COLUMNS = ["aspect", "sentiment", "metric", "value"]
MISPREDICTION_COLUMNS = ["review", "aspect", "gold", "pred"]

# Xuất lại những gì chỗ gọi cần, để không phải với vào `base`.
Samples = base.Samples
ScorerError = base.ScorerError
UNREADABLE = base.UNREADABLE


def available():
    """Tên các bộ chấm đang có."""
    return list(SCORERS)


def get(name):
    """Module của một bộ chấm. Tên sai thì báo lỗi kèm danh sách."""
    if name not in SCORERS:
        raise base.ScorerError(
            "Không có chỉ số '{}'. Các chỉ số hiện có: {}.".format(
                name, ", ".join(available())))
    return SCORERS[name]


def check(names):
    """Kiểm danh sách tên chỉ số đọc từ `evaluation.scores`."""
    if names is None:
        return available()
    names = list(names)
    if not names:
        raise base.ScorerError("`evaluation.scores` rỗng: không có chỉ số nào để tính.")
    unknown = [name for name in names if name not in SCORERS]
    if unknown:
        raise base.ScorerError(
            "Không có chỉ số {} trong registry SCORERS. Các chỉ số hiện có: {}.".format(
                ", ".join(repr(name) for name in unknown), ", ".join(available())))
    return names


def describe():
    """Vài dòng mô tả các bộ chấm, để in bằng `--list-scorers`."""
    return ["{:<16} {}".format(name, SCORERS[name].DESCRIPTION) for name in available()]


def run_all(samples, names=None):
    """Chạy các bộ chấm điểm trên dữ liệu đã chiếu.

    Trả về dict:
        scores      {tên chỉ số: con số tổng hợp}  -> `metrics.json`
        rows        dòng của `metrics.csv` (bảng dài)
        tables      bảng nhiều chiều (ma trận nhầm) -> `metrics.json`
        aspects     khía cạnh đã chấm
        n_reviews   số review đã chấm
    """
    names = check(names)
    scores, rows, tables = {}, [], {}
    for name in names:
        result = SCORERS[name].run(samples)
        scores[name] = result.get("values") or {}
        rows.extend(result.get("rows") or [])
        if result.get("tables"):
            tables[name] = result["tables"]
    return {"scores": scores, "rows": rows, "tables": tables,
            "aspects": list(samples.aspects), "n_reviews": samples.n_reviews,
            "names": names}


def table(rows, metrics=None):
    """Bảng để IN RA màn hình: dòng là (khía cạnh, sắc thái), cột là chỉ số.

    Trả về (các dòng, tên cột) - cùng dạng với `experiments.table()` để chỗ in dùng chung một hàm.
    """
    metrics = list(metrics) if metrics else sorted({item["metric"] for item in rows})
    index, order = {}, []
    for item in rows:
        key = (item["aspect"], item["sentiment"])
        if key not in index:
            index[key] = {}
            order.append(key)
        index[key][item["metric"]] = item["value"]
    columns = ["aspect", "sentiment"] + metrics
    return [[key[0], key[1]] + [index[key].get(metric, "") for metric in metrics]
            for key in order], columns


def write(out_dir, samples, names=None, save_confusion=True, save_plots=True, extra=None):
    """Ghi các file chỉ số vào một thư mục kết quả. Trả về {tên file: đường dẫn}.

    `extra` là thông tin của lần chạy (prompt, split, cách sinh...). Số liệu về phép chiếu nhãn
    (`label_space`, `neutral_policy`, số ô bị loại) do `samples` quyết định và KHÔNG bị `extra`
    đè lên - đó là sự thật của tập đánh giá, không phải lựa chọn của người gọi hàm.

    `save_confusion` và `save_plots` là hai khoá trong `configs/experiments/evaluation.yaml`
    (`save.confusion`, `save.plots`); nơi gọi đọc config và truyền vào, hàm này không tự đọc.
    """
    out_dir = Path(out_dir)
    result = run_all(samples, names=names)

    payload = dict(extra or {})
    payload.update(samples.meta)
    payload["n_reviews"] = samples.n_reviews
    payload["aspects"] = result["aspects"]
    payload["scores"] = result["scores"]
    payload["tables"] = result["tables"] if save_confusion else {}

    written = {}
    json_name = paths.pattern("metrics_json")
    written[json_name] = utils.write_json(payload, out_dir / json_name)

    csv_name = paths.pattern("metrics_csv")
    written[csv_name] = utils.write_csv(
        [[item["aspect"], item["sentiment"], item["metric"], item["value"]]
         for item in result["rows"]],
        CSV_COLUMNS, out_dir / csv_name)

    mis_name = paths.pattern("mispredictions")
    written[mis_name] = utils.write_csv(
        [[item["review"], item["aspect"], item["gold"], item["pred"]]
         for item in samples.mispredictions()],
        MISPREDICTION_COLUMNS, out_dir / mis_name)

    if save_plots:
        written.update(write_plots(out_dir, payload))
    return written


PLOT_NAME = "accuracy.html"


def write_plots(out_dir, payload):
    """Ghi biểu đồ của lượt chạy vào `<out_dir>/plots/`: một file HTML tự chứa.

    Vì sao không dùng thư viện vẽ: `configs/experiments/evaluation.yaml` khai `save.plots: true` ngay từ
    đầu, nhưng KHÔNG chỗ nào đọc khoá đó - nên người chạy tưởng đã có biểu đồ trong thư mục kết quả, mở
    ra thì không thấy gì. Bản này vẽ bằng HTML/CSS thuần: không thêm phụ thuộc (Colab không cài `plotly`
    và `jinja2`), mở trực tiếp không cần mạng. Con số vẫn là con số `metrics.json` đã ghi - không tính
    lại, vì hai đường tính cho cùng một con số thì sớm muộn cũng lệch nhau.

    Hình dạng đọc từ `metrics.json`: `scores.accuracy` có các con số tóm tắt (`macro`, `micro`, ...) và
    `by_aspect` (khía cạnh -> %); `tables.confusion.by_aspect` (khía cạnh -> nhãn đúng -> nhãn đoán ->
    số ô). Không có số nào để vẽ thì trả `{}` và KHÔNG tạo thư mục rỗng.
    """
    summary, aspects = _accuracy_numbers(payload)
    confusion = _confusion_tables(payload)
    if not summary and not aspects and not confusion:
        return {}

    folder = Path(out_dir) / paths.pattern("plots")
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / PLOT_NAME
    path.write_text(_plot_page(payload, summary, aspects, confusion), encoding="utf-8")
    return {"{}/{}".format(paths.pattern("plots"), PLOT_NAME): path}


def _accuracy_numbers(payload):
    """`(con số tóm tắt, số theo khía cạnh)` của bộ chấm `accuracy`, đúng như `metrics.json` đã ghi."""
    accuracy = dict((payload.get("scores") or {}).get("accuracy") or {})
    aspects = dict(accuracy.get("by_aspect") or {})
    summary = [(name, value) for name, value in accuracy.items()
               if isinstance(value, (int, float)) and not isinstance(value, bool)]
    return summary, aspects


def _confusion_tables(payload):
    """Ma trận nhầm theo khía cạnh: `tables.confusion.by_aspect` -> {khía cạnh: {đúng: {đoán: số}}}."""
    tables = dict((payload.get("tables") or {}).get("confusion") or {})
    return dict(tables.get("by_aspect") or {})


def _plot_page(payload, summary, aspects, confusion):
    """Trang HTML tự chứa: độ chính xác từng khía cạnh vẽ bằng thanh, và ma trận nhầm từng khía cạnh."""
    title = "Lượt chạy {} ({})".format(payload.get("model") or "", payload.get("split") or "")
    lines = [
        "<!DOCTYPE html>",
        '<html lang="vi"><head><meta charset="utf-8">',
        "<title>{}</title>".format(html.escape(title)),
        "<style>",
        "body{font-family:system-ui,'Segoe UI',Arial,sans-serif;margin:24px;color:#222}",
        "table{border-collapse:collapse;margin:12px 0}",
        "th,td{border:1px solid #bbb;padding:4px 8px;text-align:left}",
        ".num{text-align:right}",
        ".bar{display:inline-block;height:12px;background:#3b6ea5;vertical-align:middle}",
        ".wrap{display:inline-block;width:240px;background:#eee}",
        "</style></head><body>",
        "<h1>{}</h1>".format(html.escape(title)),
        "<p>Sinh từ <code>metrics.json</code> của lượt chạy, không tính lại. "
        "Số liệu gốc nằm ở <code>metrics.csv</code>.</p>",
    ]
    if summary or aspects:
        lines.append("<h2>Độ chính xác (%)</h2><table>")
        lines.append('<tr><th>Khía cạnh</th><th class="num">Giá trị</th><th>Thanh</th></tr>')
        for name, value in summary:
            lines.append('<tr><td>{}</td><td class="num">{}</td><td></td></tr>'.format(
                html.escape(str(name)), html.escape(str(_round(value)))))
        for name, value in aspects.items():
            number = _number(value)
            width = max(0.0, min(100.0, number)) if number is not None else 0.0
            lines.append(
                '<tr><td>{}</td><td class="num">{}</td>'
                '<td><span class="wrap"><span class="bar" style="width:{:.1f}%"></span></span></td></tr>'
                .format(html.escape(str(name)), html.escape(str(_round(value))), width))
        lines.append("</table>")

    for aspect in sorted(confusion):
        table = dict(confusion[aspect] or {})
        labels = sorted({label for row in table.values() for label in row} | set(table))
        lines.append("<h2>Ma trận nhầm - {}</h2><table>".format(html.escape(str(aspect))))
        lines.append("<tr><th>nhãn đúng \\ nhãn đoán</th>{}</tr>".format(
            "".join("<th>{}</th>".format(html.escape(str(label))) for label in labels)))
        for gold in sorted(table):
            cells = "".join('<td class="num">{}</td>'.format(
                html.escape(str((table[gold] or {}).get(label, 0)))) for label in labels)
            lines.append("<tr><th>{}</th>{}</tr>".format(html.escape(str(gold)), cells))
        lines.append("</table>")
    lines.append("</body></html>")
    return "\n".join(lines)


def _number(value):
    """Số trong ô, hoặc None nếu ô không phải số (bảng vẫn ghi giá trị thô)."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _round(value):
    """Làm tròn số cho dễ đọc; giá trị không phải số thì giữ nguyên."""
    number = _number(value)
    return value if number is None else round(number, 2)
