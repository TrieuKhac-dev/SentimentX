# -*- coding: utf-8 -*-
"""Chấm THÊM (rescore) từ `predictions.csv`: tính lại chỉ số mà KHÔNG chạy lại model.

VÌ SAO CÓ
`predictions.csv` tự chứa đủ (`nhãn đúng` + `nhãn đoán` là JSON trong một ô), nên đổi cách chấm thì
không phải chạy lại thí nghiệm - chỉ đọc lại file là ra số mới. Xem
`docs/04_experiments/05_predictions.md`.

CHỈ THÊM, KHÔNG GHI ĐÈ
Kết quả ghi vào `metrics_rescored.json` / `metrics_rescored.csv`; `metrics.json`/`metrics.csv` của
lượt chạy KHÔNG bị chạm tới - số gốc vẫn là bằng chứng. Khối `rescored` ghi lại lúc nào / vì sao.

CÙNG ENGINE
Dùng đúng `Samples` + các `SCORERS` như lượt chạy thật (`src/evaluation/scorers/`), nên số gốc và
số rescored so được với nhau và với công bố.
"""

import datetime
import json
from pathlib import Path

from src.core import paths, utils
from src.evaluation import metrics, records, scorers
from src.evaluation.scorers import base as scorers_base


class RescoreError(Exception):
    """Không chấm lại được: thiếu `predictions.csv` hoặc thiếu `run_meta.json`."""


def _read_json(path):
    """Đọc JSON từ đĩa; file thiếu/hỏng trả `{}` (rescore không chết vì một file lỗi)."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle) or {}
    except (OSError, ValueError):
        return {}


def _read_predictions(path):
    """Đọc `predictions.csv` thành danh sách dict (DictReader nên không phụ thuộc THỨ TỰ cột)."""
    import csv

    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def aspects_of(rows):
    """Khía cạnh của phép chấm: hợp các khoá trong `nhãn đúng` của mọi dòng."""
    found = set()
    for row in rows:
        found |= set(records._labels(row.get("nhãn đúng")).keys())
    return sorted(found)


def settings(out_dir):
    """Thông tin cần để chấm lại. Ném `RescoreError` khi thiếu file bắt buộc."""
    out_dir = Path(out_dir)
    path = out_dir / paths.pattern("predictions")
    if not path.is_file():
        raise RescoreError("Thiếu {} - không có gì để chấm lại.".format(utils.rel(path)))
    meta = _read_json(out_dir / paths.pattern("run_meta"))
    if not meta:
        raise RescoreError("Thiếu/không đọc được {}.".format(paths.pattern("run_meta")))
    return {"dir": out_dir, "predictions": path, "meta": meta,
            "metrics": _read_json(out_dir / paths.pattern("metrics_json"))}


def task_of(meta, original):
    """Bài toán (label_space/neutral_policy/not_mentioned): `run_meta.json` trước, `metrics.json` sau."""
    task = dict(meta.get("task") or {})
    for key in scorers_base.TASK_KEYS:
        if not task.get(key):
            task[key] = original.get(key)
    missing = [key for key in scorers_base.TASK_KEYS if not task.get(key)]
    if missing:
        raise RescoreError(
            "Thiếu {} trong `run_meta.json`/`metrics.json`: không biết chấm theo bài toán nào."
            .format(", ".join(missing)))
    return task


def labels_of(meta):
    """Bảng mã -> tên nhãn, đọc từ `label_map.json` của ĐÚNG phiên bản dữ liệu.

    BẮT BUỘC: `Samples` cần TÊN nhãn để tra `positive`/`negative` (bộ lọc hai chiều dùng tên), nên
    máy chấm lại phải có `data/processed/<mã>/label_map.json`. Thiếu thì báo lỗi RÕ thay vì chấm sai.
    """
    from src.experiments import experiment_run
    from src.preprocessing import loader

    data = dict(meta.get("data") or {})
    version_id, dataset = data.get("build"), data.get("dataset")
    if not version_id:
        raise RescoreError(
            "Thiếu `data.build` trong run_meta.json: không biết đọc label_map.json ở đâu.")
    try:
        label_map = loader.load_label_map(version_id, dataset=dataset)
    except Exception as exc:  # noqa: BLE001 - thiếu dữ liệu là việc phải báo, không nuốt
        raise RescoreError(
            "Không đọc được label_map.json của phiên bản dữ liệu '{}' ({}: {}). Cần bộ dữ liệu đã "
            "xử lý trên đĩa: data/processed/<mã>/label_map.json.".format(
                version_id, type(exc).__name__, exc))
    labels = experiment_run.label_names(label_map)
    if not labels:
        raise RescoreError("label_map.json của '{}' không có bảng tên nhãn.".format(version_id))
    return labels


def _extra(original, infos, names):
    """Thông tin mô tả của lượt chạy (không phải số điểm), kèm `read_rate` tính lại."""
    extra = {key: value for key, value in original.items() if key not in scorers._SCORE_KEYS}
    extra["read_rate"] = metrics.read_rate(infos)
    extra["scores_order"] = list(names or [])
    return extra


def run(out_dir, names=None, paper=None, save_confusion=True, reason=None, log=print):
    """Chấm lại từ `predictions.csv` rồi ghi `metrics_rescored.*`. KHÔNG chạy model.

    Trả về `{tên file: đường dẫn}`.
    """
    context = settings(out_dir)
    meta, original = context["meta"], context["metrics"]
    rows = _read_predictions(context["predictions"])
    if not rows:
        raise RescoreError("{} rỗng - không có dòng nào để chấm.".format(
            utils.rel(context["predictions"])))
    aspects = aspects_of(rows) or list(original.get("aspects") or [])
    golds, preds, infos = records.to_arrays(rows, aspects)
    task = task_of(meta, original)
    samples = scorers.Samples.build(aspects, golds, preds, task=task, labels=labels_of(meta),
                                    sample_ids=[str(row.get("chỉ số", "")) for row in rows])
    chosen = scorers.check(names) if names else scorers.check(original.get("scores_order") or None)
    paper_names = list(paper or original.get("scores_order_paper") or []) or None
    extra = _extra(original, infos, chosen)
    rescored = {
        "at": datetime.datetime.now().isoformat(timespec="seconds"),
        "reason": reason or "chấm lại từ predictions.csv",
        "source": paths.pattern("predictions"),
        "scorers": list(chosen or []),
        "bases": list(scorers.BASES),
        "note": "số đo THÊM; KHÔNG thay thế metrics.json/metrics.csv của lượt chạy",
    }
    written = scorers.write_rescored(context["dir"], samples, names=chosen, paper=paper_names,
                                     save_confusion=save_confusion, extra=extra, rescored=rescored)
    if log is not None:
        for name, path in sorted(written.items()):
            log("  - {:<26} {}".format(name, utils.rel(path)))
    return written
