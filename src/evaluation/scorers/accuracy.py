# -*- coding: utf-8 -*-
"""`accuracy`: độ chính xác theo khía cạnh, và độ chính xác chỉ trên ô CÓ nhắc tới.

Hai con số phải đứng cạnh nhau. Model có thể chọn sắc thái đúng cho mọi khía cạnh nó NHẬN RA
(`accuracy_when_mentioned` cao) nhưng vẫn thấp điểm chung vì bỏ sót nhiều khía cạnh - hoặc ngược
lại. Gộp hai câu hỏi làm một sẽ che mất đúng kiểu lỗi cần sửa. Xem docs/04_experiments/metrics.md.
"""

from src.evaluation.scorers import base

NAME = "accuracy"
DESCRIPTION = "Độ chính xác theo khía cạnh, và độ chính xác chỉ trên các ô có nhắc tới."


def run(samples):
    """Trả về số theo khía cạnh + macro/micro. Ô không đọc được tính là sai."""
    accuracy = samples.accuracy()
    mentioned = samples.when_mentioned()

    rows = []
    for aspect in samples.aspects:
        rows.append(base.row(aspect, "all", "accuracy",
                             accuracy["by_aspect"][aspect]["accuracy"]))
        rows.append(base.row(aspect, "mentioned", "accuracy_when_mentioned",
                             mentioned["by_aspect"][aspect]["accuracy"]))

    values = {
        "macro": accuracy["macro"],
        "micro": accuracy["micro"],
        "when_mentioned_macro": mentioned["macro"],
        "when_mentioned_micro": mentioned["micro"],
        "correct": accuracy["correct"],
        "cells": accuracy["cells"],
        "by_aspect": {aspect: accuracy["by_aspect"][aspect]["accuracy"]
                      for aspect in samples.aspects},
        "when_mentioned_by_aspect": {aspect: mentioned["by_aspect"][aspect]["accuracy"]
                                     for aspect in samples.aspects},
    }
    return {"values": values, "rows": rows, "tables": {}}
