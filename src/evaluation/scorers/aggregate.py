# -*- coding: utf-8 -*-
"""`aggregate`: các con số TỔNG HỢP để so giữa các thí nghiệm.

Gồm hai nhóm:
    - trung bình macro / micro của độ chính xác, của bài toán nhắc tới, và của P/R/F1 sắc thái
    - khớp hoàn toàn: tỉ lệ review đoán đúng CẢ bộ khía cạnh (chỉ số khắt khe nhất)

Vì sao cần cả macro và micro: macro cho mỗi khía cạnh một phiếu (khía cạnh ít được nhắc không bị
át), micro cân theo số ô (khía cạnh được nhắc nhiều có trọng lượng lớn hơn). Hai con số lệch nhau
nhiều là dấu hiệu model làm tốt ở một nhóm khía cạnh và bỏ hẳn một nhóm khác.
"""

from src.evaluation.scorers import base

NAME = "aggregate"
DESCRIPTION = "Trung bình macro/micro và tỉ lệ khớp hoàn toàn (đúng cả bộ khía cạnh)."


def run(samples):
    """Trả về các con số tổng hợp trong `values`, và một dòng `all` trong `metrics.csv`."""
    accuracy = samples.accuracy()
    detection = samples.detection()
    per_sentiment = samples.per_sentiment()
    exact = samples.exact()

    rows = [
        base.row("all", "all", "accuracy_macro", accuracy["macro"]),
        base.row("all", "all", "accuracy_micro", accuracy["micro"]),
        base.row("all", "all", "when_mentioned_macro", samples.when_mentioned()["macro"]),
        base.row("all", "all", "detection_f1_macro", detection["macro"]["f1"]),
        base.row("all", "all", "detection_f1_micro", detection["micro"]["f1"]),
        base.row("all", "all", "sentiment_f1_macro", per_sentiment["macro"]["f1"]),
        base.row("all", "all", "sentiment_f1_micro", per_sentiment["micro"]["f1"]),
        base.row("all", "all", "exact_match", exact["percent"]),
    ]

    values = {
        "accuracy_macro": accuracy["macro"],
        "accuracy_micro": accuracy["micro"],
        "when_mentioned_macro": samples.when_mentioned()["macro"],
        "detection": {"macro": detection["macro"], "micro": detection["micro"]},
        "sentiment": {"macro": per_sentiment["macro"], "micro": per_sentiment["micro"]},
        "exact_match": exact,
        "reviews": exact["reviews"],
        "aspects": len(samples.aspects),
        "cells": accuracy["cells"],
    }
    return {"values": values, "rows": rows, "tables": {}}
