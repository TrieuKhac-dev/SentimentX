# -*- coding: utf-8 -*-
"""Đọc file JSONL — mỗi dòng là một object JSON.

Ví dụ một dòng hợp lệ:
    {"data": "son này đẹp", "colour": "positive", "price": ""}

Dùng khi dữ liệu nguồn ở dạng JSONL (thường gặp khi dữ liệu được crawl
hoặc export từ công cụ gán nhãn).
"""

import json

import pandas as pd

from src.loaders import base


def read(path):
    """Đọc JSONL thành DataFrame, mọi cột ở dạng chuỗi."""
    records = []
    with open(path, "r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(
                    "{}: dòng {} không phải JSON hợp lệ ({}).".format(
                        path, line_number, exc
                    )
                )
    if not records:
        raise ValueError("File JSONL rỗng: {}".format(path))

    frame = pd.DataFrame(records)
    # Ép mọi cột về chuỗi để giữ đúng quy ước "ô trống = chuỗi rỗng": trong
    # JSONL, cùng một cột có thể chứa cả chữ ("positive") và số (1).
    return base.as_string_frame(frame)
