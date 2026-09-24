# -*- coding: utf-8 -*-
"""`confusion`: ma trận nhầm theo từng khía cạnh, để VẼ và để đọc lỗi.

Bảng đếm nhãn đúng (dòng) so với nhãn đoán (cột). Ô không đọc được gom vào một cột riêng, nên
bảng đếm đủ mọi ô và nhìn vào là biết bao nhiêu phần của sai số đến từ việc model trả lời hỏng
định dạng - con số mà bảng `accuracy` không tách ra được.

Bộ chấm này không sinh dòng nào cho `metrics.csv` (bảng dài không biểu diễn được chiều thứ ba);
kết quả nằm trong `metrics.json` ở khoá `tables`, và chỉ ghi khi `evaluation.save.confusion` bật.
"""

from src.evaluation.scorers import base

NAME = "confusion"
DESCRIPTION = "Ma trận nhầm theo khía cạnh: đếm nhãn đúng so với nhãn đoán (để vẽ)."


def run(samples):
    """Trả về bảng đếm của từng khía cạnh, và thứ tự nhãn để vẽ cho khớp nhau."""
    labels = [samples.code_for(code) for code in samples.sentiments()]
    if not samples.meta.get("separate_not_mentioned"):
        labels = [samples.code_for(code) for code in samples.meta.get("codes") or []]
    labels = labels + [base.UNREADABLE]

    return {
        "values": {
            "aspects": list(samples.aspects),
            "labels": labels,
            "cells": samples.accuracy()["cells"],
            "dropped_neutral": samples.meta.get("dropped_neutral", 0),
        },
        "rows": [],
        "tables": {"by_aspect": {aspect: samples.confusion(aspect)
                                 for aspect in samples.aspects}},
    }
