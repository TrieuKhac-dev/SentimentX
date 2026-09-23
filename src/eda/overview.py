# -*- coding: utf-8 -*-
"""EDA 01 — Tổng quan dữ liệu.

Đo lường theo cả 3 split (train / val / test): cấu trúc từng file gốc, ô trống
theo từng cột, độ dài review theo số ký tự và số từ (p50 / p95 / p99).

Module này CHỈ đo lường, KHÔNG sửa bất kỳ dòng dữ liệu nào.

Ghi chú thiết kế: mỗi số liệu chỉ được trình bày MỘT lần trong báo cáo HTML
(bảng HOẶC biểu đồ) và báo cáo không chứa câu giải thích. Bản số liệu đầy đủ
luôn nằm ở file CSV.
"""

from src import config, utils

# Các khoảng độ dài (số ký tự) dùng để vẽ phân bố.
LENGTH_BINS = [
    (0, 50, "0-50"),
    (51, 100, "51-100"),
    (101, 200, "101-200"),
    (201, 400, "201-400"),
    (401, 800, "401-800"),
    (801, None, "trên 800"),
]


def _bucket_counts(lengths):
    """Đếm số review rơi vào từng khoảng độ dài."""
    counts = {label: 0 for _, _, label in LENGTH_BINS}
    for value in lengths:
        for low, high, label in LENGTH_BINS:
            if value >= low and (high is None or value <= high):
                counts[label] += 1
                break
    return counts


def _source_filename(cfg, split_name):
    """Tên file gốc của một split, đọc từ configs/datasets/<tên>.yaml."""
    return (cfg.get("splits") or {}).get(split_name, "-")



def run(context):
    splits = context["splits"]
    full = context.get("full")
    cfg = context["dataset"]
    out_dir = context["out_dir"]
    aspects = cfg["aspects"]
    missing = context.get("missing_columns") or {}
    files = []

    # -----------------------------------------------------------------
    # 1. Cấu trúc các file gốc
    # -----------------------------------------------------------------
    struct_rows = []
    for name, df in splits.items():
        absent = missing.get(name) or []
        struct_rows.append([
            name,
            _source_filename(cfg, name),
            len(df),
            len(df.columns),
            cfg["text_column"],
            len(aspects),
            ", ".join(absent) if absent else "-",
        ])
    if full is not None:
        struct_rows.append([
            "(file gộp)",
            cfg.get("full", "full_data.csv"),
            len(full),
            len(full.columns),
            cfg["text_column"],
            len(aspects),
            "-",
        ])

    struct_columns = ["split", "tệp gốc", "số dòng", "số cột", "cột văn bản",
                      "số cột khía cạnh", "cột khía cạnh bị thiếu"]
    files.append(utils.rel(utils.write_csv(
        struct_rows, struct_columns, out_dir / "01_overview_structure.csv")))

    total = sum(len(df) for df in splits.values())

    # -----------------------------------------------------------------
    # 2. Ô trống theo từng cột — cả 3 split
    # -----------------------------------------------------------------
    empty_rows = []
    for name, df in splits.items():
        for column in df.columns:
            n_empty = int((df[column].astype(str).str.strip() == "").sum())
            empty_rows.append([
                name,
                column,
                n_empty,
                round(100 * n_empty / len(df), 2) if len(df) else 0.0,
            ])

    files.append(utils.rel(utils.write_csv(
        empty_rows,
        ["split", "cột", "số ô trống", "tỉ lệ %"],
        out_dir / "01_overview_empty.csv",
    )))

    # Ô trống theo cột chỉ ghi ra CSV: số ô trống gộp cả 3 split không dẫn tới
    # quyết định nào, còn phần đã có ý nghĩa (review không nhắc aspect nào, tỉ lệ
    # nhắc từng aspect) nằm ở EDA 02 nên không lặp lại ở đây.

    # -----------------------------------------------------------------
    # 3. Thống kê độ dài review — cả 3 split, theo ký tự và theo từ
    # -----------------------------------------------------------------
    length_rows = []
    for name, df in splits.items():
        texts = df[config.TEXT_COLUMN].astype(str)
        char_stats = utils.length_stats(texts.str.len(), "số ký tự")
        word_stats = utils.length_stats(texts.str.split().str.len().fillna(0), "số từ")
        for stats in (char_stats, word_stats):
            length_rows.append([
                name, stats["chỉ số"], stats["nhỏ nhất"], stats["p50"], stats["p95"],
                stats["p99"], stats["lớn nhất"], stats["trung bình"],
            ])

    # Độ dài review chỉ ghi ra CSV: p50/p95/p99 không dẫn tới quyết định nào, và
    # biểu đồ phân bố ngay dưới đã cho thấy hình dạng độ dài theo từng split.
    files.append(utils.rel(utils.write_csv(
        length_rows,
        ["split", "chỉ số", "nhỏ nhất", "p50", "p95", "p99", "lớn nhất", "trung bình"],
        out_dir / "01_overview_length.csv",
    )))

    distribution_series = {}
    for name, df in splits.items():
        lengths = df[config.TEXT_COLUMN].astype(str).str.len().tolist()
        counts = _bucket_counts(lengths)
        n_rows = len(lengths) or 1
        distribution_series[name] = [
            round(100 * counts[label] / n_rows, 2) for _, _, label in LENGTH_BINS
        ]

    distribution_chart = {
        "title": "Phân bố độ dài review theo khoảng (%)",
        "kind": "grouped_bar",
        "x": [label for _, _, label in LENGTH_BINS],
        "series": distribution_series,
        "x_label": "số ký tự",
        "y_label": "tỉ lệ %",
    }

    return {
        "id": "overview",
        "title": "EDA 01 — Tổng quan dữ liệu",
        "cards": [
            {"label": "Số dòng (3 split)", "value": "{}".format(total)},
            {"label": "Số khía cạnh", "value": len(aspects)},
            {"label": "Train / Val / Test", "value": "{}/{}/{}".format(
                len(splits["train"]), len(splits["val"]), len(splits["test"]))},
        ],
        "charts": [distribution_chart],
        "tables": [
            {
                # Bảng cấu trúc được đặt NGAY DƯỚI phần thẻ số liệu, trước biểu
                # đồ: đây là thông tin người đọc cần biết trước tiên, và cũng để
                # số dòng mỗi file không bị lặp lại ở cả bảng lẫn biểu đồ.
                "title": "Cấu trúc các file dữ liệu",
                "columns": struct_columns,
                "rows": struct_rows,
                "num_columns": [2, 3, 4, 5],
                "first": True,
            },
        ],
        "files": files,
    }
