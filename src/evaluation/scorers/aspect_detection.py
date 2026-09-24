# -*- coding: utf-8 -*-
"""`aspect_detection`: bài toán nhị phân "khía cạnh này có được nhắc tới hay không".

Đây là câu hỏi thứ nhất, tách khỏi câu hỏi chọn sắc thái (xem `prf`). Lớp DƯƠNG là "có nhắc
tới" (mã khác 0), nên:
    Precision thấp -> model "thấy" khía cạnh không có (nêu thừa)
    Recall thấp    -> model bỏ sót khía cạnh có (nêu thiếu)

Ô không đọc được coi như model không nêu khía cạnh nào, nên làm GIẢM Recall chứ không sinh ra
dương tính giả. Xem docs/04_experiments/metrics.md.
"""

from src.evaluation.scorers import base

NAME = "aspect_detection"
DESCRIPTION = "Nhị phân \"có nhắc tới hay không\": accuracy, precision, recall, F1."

# Tên chỉ số in ra `metrics.csv` theo thứ tự đọc.
METRICS = ("accuracy", "precision", "recall", "f1")


def run(samples):
    """Trả về số theo khía cạnh + macro/micro + số ô của mỗi lớp."""
    detection = samples.detection()

    rows = []
    for aspect in samples.aspects:
        item = detection["by_aspect"][aspect]
        for metric in METRICS:
            rows.append(base.row(aspect, "mentioned", metric, item[metric]))

    by_aspect = {}
    for aspect in samples.aspects:
        item = detection["by_aspect"][aspect]
        by_aspect[aspect] = {metric: item[metric] for metric in METRICS}
        by_aspect[aspect].update({"tp": item["tp"], "fp": item["fp"],
                                  "fn": item["fn"], "tn": item["tn"]})

    values = {
        "macro": {metric: detection["macro"][metric] for metric in METRICS},
        "micro": {metric: detection["micro"][metric] for metric in METRICS},
        "support": detection["support"],
        "by_aspect": by_aspect,
    }
    return {"values": values, "rows": rows, "tables": {}}
