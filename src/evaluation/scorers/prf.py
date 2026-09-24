# -*- coding: utf-8 -*-
"""`prf`: precision, recall, F1 cho TỪNG CẶP (khía cạnh, sắc thái).

Cách đếm là một-chọi-phần-còn-lại: với cặp (price, negative), lớp dương là "ô này đúng là
negative ở khía cạnh price", mọi ô khác của cùng khía cạnh là lớp âm. Nhờ vậy so được với bảng
P/R/F1 của công bố tham chiếu (docs/04_experiments/reference_publication.md).

Ô không đọc được tính là "không thuộc lớp này", tức là SAI. Sắc thái được chấm là các mã trong
không gian nhãn của thí nghiệm; mã "không nhắc tới" chỉ được chấm như một sắc thái khi nó là một
LỚP (`not_mentioned: as_class`), còn khi nó là quyết định riêng thì đã có `aspect_detection`.
"""

from src.evaluation.scorers import base

NAME = "prf"
DESCRIPTION = "Precision/recall/F1 cho từng cặp khía cạnh và sắc thái (một-chọi-phần-còn-lại)."

# Tên chỉ số in ra `metrics.csv` theo thứ tự đọc.
METRICS = ("precision", "recall", "f1", "support")


def run(samples):
    """Trả về số theo cặp (khía cạnh, sắc thái) + macro/micro trên ô."""
    per_sentiment = samples.per_sentiment()

    rows = []
    for aspect in samples.aspects:
        for code, item in per_sentiment["by_aspect"][aspect].items():
            sentiment = samples.code_for(code)
            for metric in METRICS:
                rows.append(base.row(aspect, sentiment, metric, item[metric]))

    by_aspect = {}
    for aspect in samples.aspects:
        by_aspect[aspect] = {
            samples.code_for(code): {
                "precision": item["precision"], "recall": item["recall"],
                "f1": item["f1"], "support": item["support"]}
            for code, item in per_sentiment["by_aspect"][aspect].items()}

    values = {
        "macro": per_sentiment["macro"],
        "micro": per_sentiment["micro"],
        "sentiments": [samples.code_for(code) for code in samples.sentiments()],
        "by_aspect": by_aspect,
    }
    return {"values": values, "rows": rows, "tables": {}}
