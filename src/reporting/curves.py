# -*- coding: utf-8 -*-
"""Vẽ curve train/val (`plots/training.html`) từ `training_history.csv`.

VÌ SAO ĐỌC CSV CHỨ KHÔNG NHẬN LIST TRONG BỘ NHỚ
Báo cáo của dự án chỉ TRÌNH BÀY số liệu đã ghi (`src/reporting/render.py`), không tính lại. Nhờ vậy
vẽ lại được SAU khi lượt chạy xong, trên máy không có GPU, mà không phải chạy lại model.

CÙNG CÔNG NGHỆ VỚI BÁO CÁO KHÁC
Plotly (`src/reporting/charts.py`, kind `line`) + Jinja2 (`templates/training.html`) - đúng đường đi
của báo cáo EDA/pipeline, nên biểu đồ mở được không cần mạng (plotly.min.js nằm trong `data/assets/`).
"""

from pathlib import Path

from src.core import utils
from src.reporting import render

# Các cột vẽ thành đường (đọc từ `training_history.csv`).
LOSS_SERIES = ("train_loss", "val_loss")
PRF_SERIES = ("sentiment_precision", "sentiment_recall", "sentiment_f1")
TITLE = "Curve train/val của lượt huấn luyện (encoder)"


def _numbers(rows, key):
    """Giá trị số của một cột; ô trống/không phải số -> None (Plotly bỏ qua điểm đó)."""
    values = []
    for row in rows:
        try:
            values.append(float(row.get(key)))
        except (TypeError, ValueError):
            values.append(None)
    return values


def _has_data(rows, keys):
    """Có ít nhất một điểm số trong nhóm cột này không (không có thì thôi, không vẽ biểu đồ rỗng)."""
    return any(value is not None for key in keys for value in _numbers(rows, key))


def payload(rows, columns):
    """Payload cho template: biểu đồ đường (loss, P/R/F1) + bảng dữ liệu đầy đủ."""
    steps = [str(row.get("step") or "") for row in rows]
    specs = []
    if _has_data(rows, LOSS_SERIES):
        specs.append({"title": "Loss (train so với val)", "kind": "line", "x": steps,
                      "series": {key: _numbers(rows, key) for key in LOSS_SERIES},
                      "x_label": "bước", "y_label": "loss"})
    if _has_data(rows, PRF_SERIES):
        specs.append({"title": "Precision / Recall / F1 trên val", "kind": "line", "x": steps,
                      "series": {key: _numbers(rows, key) for key in PRF_SERIES},
                      "x_label": "bước", "y_label": "điểm"})
    return {"title": TITLE,
            "subtitle": "Số liệu đọc từ training_history.csv, không tính lại.",
            "meta": ["Hai đường loss tách xa nhau = dấu hiệu overfit; "
                     "chỉ số quyết định là sentiment_f1 (macro-F1 sắc thái)."],
            "specs": specs, "columns": list(columns),
            "rows": [[row.get(column, "") for column in columns] for row in rows]}


def write_html(history_path, out_dir, plotlyjs="local"):
    """Ghi `plots/training.html` từ file lịch sử. Trả về đường dẫn, hoặc None nếu không có dữ liệu."""
    path = Path(history_path)
    if not path.is_file():
        return None
    frame = utils.read_csv(path)
    rows = frame.to_dict("records")
    if not rows:
        return None
    return render.write_training_html(payload(rows, list(frame.columns)), out_dir, plotlyjs=plotlyjs)
