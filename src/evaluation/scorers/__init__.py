# -*- coding: utf-8 -*-
"""Registry các BỘ CHẤM ĐIỂM, và chỗ DUY NHẤT ghi file chỉ số của một lần chạy.

    metrics.json        toàn bộ chỉ số, kèm `label_space`, `neutral_policy`, số ô neutral bị loại
    metrics.csv         bảng dài (aspect, sentiment, metric, value) để so giữa các thí nghiệm
    mispredictions.csv  chỉ các ô đoán sai, kèm khía cạnh, nhãn đúng, nhãn đoán

Bộ chấm nào chạy là do `evaluation.scores` trong `configs/experiments/evaluation.yaml` quyết
định; tên lạ thì `check()` báo lỗi kèm danh sách chứ KHÔNG im lặng bỏ qua - bỏ qua thì bảng kết
quả thiếu một chỉ số mà người đọc không biết là thiếu.

THÊM MỘT BỘ CHẤM MỚI
    Viết một module trong thư mục này theo hợp đồng ở `base.py`, rồi thêm một dòng vào `SCORERS`.
    Không phải sửa bộ chấm nào đang có. Xem docs/04_experiments/metrics.md.
"""

from pathlib import Path

from src import paths, utils
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


def write(out_dir, samples, names=None, save_confusion=True, extra=None):
    """Ghi ba file chỉ số vào một thư mục kết quả. Trả về {tên file: đường dẫn}.

    `extra` là thông tin của lần chạy (prompt, split, cách sinh...). Số liệu về phép chiếu nhãn
    (`label_space`, `neutral_policy`, số ô bị loại) do `samples` quyết định và KHÔNG bị `extra`
    đè lên - đó là sự thật của tập đánh giá, không phải lựa chọn của người gọi hàm.
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
    return written
