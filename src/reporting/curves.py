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


def available():
    """Thư viện vẽ (`plotly` + `jinja2`) đã sẵn sàng chưa.

    CI KHÔNG cài hai gói này (`requirements-ci.txt`), nên mọi thứ ở đây phải chịu được việc thiếu
    chúng: `render`/`charts` chỉ được import TRONG HÀM, và `write_html` trả `None` thay vì ném.
    """
    import importlib.util

    return (importlib.util.find_spec("plotly") is not None
            and importlib.util.find_spec("jinja2") is not None)


def write_html(history_path, out_dir, plotlyjs="local", log=None):
    """Ghi `plots/training.html` từ file lịch sử. Trả về đường dẫn, hoặc `None` nếu không vẽ được.

    BEST-EFFORT: thiếu `plotly`/`jinja2` (CI, hoặc máy chạy chưa cài) thì BỎ QUA biểu đồ - số liệu vẫn
    nằm nguyên trong `training_history.csv`, và lượt chạy KHÔNG được chết vì một việc phụ.
    """
    path = Path(history_path)
    if not path.is_file():
        return None
    frame = utils.read_csv(path)
    rows = frame.to_dict("records")
    if not rows:
        return None
    if not available():
        if log is not None:
            log("chưa cài plotly/jinja2 nên không vẽ biểu đồ train/val (số liệu vẫn ở {})".format(
                path.name))
        return None
    from src.reporting import render  # import TRONG hàm: chỉ khi thật sự vẽ (xem `available`)

    try:
        return render.write_training_html(payload(rows, list(frame.columns)), out_dir,
                                          plotlyjs=plotlyjs)
    except Exception as exc:  # noqa: BLE001 - vẽ hỏng là việc phụ, không được làm chết lượt chạy
        if log is not None:
            log("không vẽ được biểu đồ train/val ({}: {})".format(type(exc).__name__, exc))
        return None
