# -*- coding: utf-8 -*-
"""EDA 02 — Nhãn và khía cạnh.

Đo lường theo cả 3 split (train / val / test): tỉ lệ review nhắc tới từng khía
cạnh, phân bố nhãn trong số review có nhắc khía cạnh, số khía cạnh được nhắc
trong một review, mức xuất hiện cùng nhau (toàn bộ dữ liệu) và nhãn không hợp lệ.

Quy ước: ô trống ở cột khía cạnh là null (không nhắc tới), không phải neutral.
Cột khía cạnh trong file gốc tên tiếng Anh (stayingpower, colour...) nên báo cáo
dùng chữ "khía cạnh" khi viết tiếng Việt, không gọi là "aspect" nữa.

Điểm dễ hiểu nhầm đã được xử lý riêng: một phần dữ liệu KHÔNG có nhãn khía cạnh
nào (mọi cột khía cạnh đều trống). Nhóm này được nêu bằng một thẻ số liệu riêng
và bị LOẠI khỏi biểu đồ "số khía cạnh trong một review", vì đứng lẫn trong dải
phân bố thì người đọc dễ hiểu thành "17% dữ liệu không có khía cạnh nào" ngay
giữa một biểu đồ nói về review CÓ nhãn.

Báo cáo chỉ có số liệu: mỗi số liệu xuất hiện một lần (bảng HOẶC biểu đồ).
"""

from collections import Counter

from src import utils

# Thứ tự nhãn hiển thị trong biểu đồ và bảng
LABEL_ORDER = ("positive", "negative", "neutral")


def _stripped(df, aspects):
    """Lấy các cột aspect và bỏ khoảng trắng thừa (không sửa dữ liệu gốc)."""
    return df[aspects].astype(str).apply(lambda col: col.str.strip())


def run(context):
    splits = context["splits"]
    out_dir = context["out_dir"]
    aspects = context["dataset"]["aspects"]
    labels = context["dataset"]["labels"]
    files = []

    # -----------------------------------------------------------------
    # 1. Phân bố nhãn của từng aspect theo từng split
    # -----------------------------------------------------------------
    label_rows = []
    invalid_rows = []
    zero_aspect = {}
    mention_series = {name: [] for name in splits}
    per_split_stacked = {}

    for name, df in splits.items():
        values_df = _stripped(df, aspects)
        total = len(df)
        per_aspect_counts = {label: [] for label in LABEL_ORDER}
        for aspect in aspects:
            column = values_df[aspect]
            counts = {value: int((column == value).sum()) for value in labels}
            n_null = int((column == "").sum())
            n_invalid = total - n_null - sum(counts.values())
            label_rows.append([
                name,
                aspect,
                counts["positive"],
                counts["negative"],
                counts["neutral"],
                n_null,
                round(100 * (total - n_null) / total, 2) if total else 0.0,
            ])
            if n_invalid > 0:
                bad = sorted(set(column[(column != "") & (~column.isin(labels))]))
                invalid_rows.append([name, aspect, n_invalid, ", ".join(bad[:10])])
            mention_series[name].append(
                round(100 * (total - n_null) / total, 2) if total else 0.0
            )
            for label in LABEL_ORDER:
                per_aspect_counts[label].append(counts[label])
        per_split_stacked[name] = per_aspect_counts

    files.append(utils.rel(utils.write_csv(
        label_rows,
        ["split", "khía cạnh", "positive", "negative", "neutral", "không nhắc tới",
         "tỉ lệ được nhắc tới %"],
        out_dir / "02_label_aspect_distribution.csv",
    )))

    # Mỗi split một khung riêng (xem charts._stacked_grid): trong một khung thì
    # đọc được phân bố nhãn giữa các khía cạnh, nhìn ngang thì so được cùng một
    # khía cạnh giữa 3 split. Một biểu đồ duy nhất với nhãn "khía cạnh · split"
    # bắt người đọc tự tách lại nên khó xem.
    label_chart = {
        "title": "Phân bố nhãn trong số review có nhắc khía cạnh — mỗi split một khung (%)",
        "kind": "stacked_grid",
        "barnorm": "percent",
        "x": list(aspects),
        "series_order": list(LABEL_ORDER),
        "facets": [
            {"title": name, "series": per_split_stacked[name]}
            for name in per_split_stacked
        ],
        "y_label": "tỉ lệ % số review nhắc khía cạnh đó",
        "height": 470,
    }

    mention_chart = {
        "title": "Tỉ lệ review nhắc tới từng khía cạnh theo split (%)",
        "kind": "grouped_bar",
        "x": list(aspects),
        "series": mention_series,
        "y_label": "tỉ lệ % số review của split",
    }

    # -----------------------------------------------------------------
    # 2. Số khía cạnh được nhắc tới trong một review — cả 3 split
    # -----------------------------------------------------------------
    per_review_rows = []
    per_review_share = {}     # % trên số review CÓ nhãn khía cạnh
    max_mentioned = 0
    for name, df in splits.items():
        values_df = _stripped(df, aspects)
        n_mentioned = (values_df != "").sum(axis=1)
        counter = Counter(n_mentioned.tolist())
        zero_aspect[name] = counter.get(0, 0)
        n_labelled = len(df) - zero_aspect[name]
        max_mentioned = max(max_mentioned, max(counter) if counter else 0)
        for k in sorted(counter):
            rate = round(100 * counter[k] / len(df), 2) if len(df) else 0.0
            # Nhóm "0 khía cạnh" nằm NGOÀI mẫu số của cột tỉ lệ thứ hai (mẫu số
            # chỉ tính review có nhãn), nên ghi "-" thay vì một con số vô nghĩa.
            share = (
                round(100 * counter[k] / n_labelled, 2) if n_labelled and k else 0.0
            )
            per_review_rows.append([name, k, counter[k], rate,
                                    share if k else "-"])
            if k:
                per_review_share[(name, k)] = share

    files.append(utils.rel(utils.write_csv(
        per_review_rows,
        ["split", "số khía cạnh được nhắc", "số review",
         "tỉ lệ % trên toàn split", "tỉ lệ % trên số review có nhãn"],
        out_dir / "02_label_aspect_per_review.csv",
    )))

    # Nhóm "0 khía cạnh" KHÔNG được vẽ trong biểu đồ này:
    # - nó là một nhóm riêng về mặt ý nghĩa (không có nhãn khía cạnh nào), đã có
    #   thẻ số liệu riêng ở đầu mục;
    # - nếu đứng lẫn trong dải phân bố, người đọc dễ đọc thành "17% dữ liệu không
    #   có khía cạnh nào" ngay giữa biểu đồ đang nói về review CÓ nhãn.
    # Vì vậy trục hoành bắt đầu từ 1 và mẫu số là số review có nhãn khía cạnh.
    per_review_chart = {
        "title": ("Số khía cạnh được nhắc trong một review — chỉ tính review có "
                  "nhắc ít nhất 1 khía cạnh (%)"),
        "kind": "grouped_bar",
        "x": [str(k) for k in range(1, max_mentioned + 1)],
        "series": {
            name: [per_review_share.get((name, k), 0.0)
                   for k in range(1, max_mentioned + 1)]
            for name in splits
        },
        "x_label": "số khía cạnh được nhắc",
        "y_label": "tỉ lệ % số review có nhãn khía cạnh",
    }

    # -----------------------------------------------------------------
    # 3. Ma trận xuất hiện cùng nhau (co-occurrence) trên toàn bộ dữ liệu
    # -----------------------------------------------------------------
    co_counts = {(first, second): 0 for first in aspects for second in aspects}
    for name, df in splits.items():
        mentioned = _stripped(df, aspects) != ""
        for first in aspects:
            for second in aspects:
                co_counts[(first, second)] += int(
                    (mentioned[first] & mentioned[second]).sum())

    co_rows = [[first] + [co_counts[(first, second)] for second in aspects]
               for first in aspects]

    files.append(utils.rel(utils.write_csv(
        co_rows,
        ["aspect"] + aspects,
        out_dir / "02_label_aspect_cooccurrence.csv",
    )))

    co_chart = {
        "title": "Số review nhắc tới cả hai khía cạnh (3 split)",
        "kind": "heatmap",
        "x": list(aspects),
        "y": list(aspects),
        "z": [row[1:] for row in co_rows],
        "height": 460,
    }

    # -----------------------------------------------------------------
    # 4. Nhãn không hợp lệ
    # -----------------------------------------------------------------
    files.append(utils.rel(utils.write_csv(
        invalid_rows or [["-", "-", 0, "không có"]],
        ["split", "khía cạnh", "số nhãn sai", "giá trị sai gặp phải"],
        out_dir / "02_label_aspect_invalid.csv",
    )))

    return {
        "id": "label_aspect",
        "title": "EDA 02 — Nhãn và khía cạnh",
        "cards": [
            {"label": "Số khía cạnh", "value": len(aspects)},
            {"label": "Số dòng không có nhãn khía cạnh nào (3 split)",
             "value": "{}".format(sum(zero_aspect.values()))},
            {"label": "Số nhãn không hợp lệ (3 split)",
             "value": sum(row[2] for row in invalid_rows)},
        ],
        "charts": [label_chart, mention_chart, per_review_chart, co_chart],
        "tables": (
            [
                {
                    "title": "Nhãn không hợp lệ",
                    "columns": ["split", "khía cạnh", "số nhãn sai",
                                "giá trị sai gặp phải"],
                    "rows": invalid_rows,
                    "num_columns": [2],
                },
            ] if invalid_rows else []
        ),
        "files": files,
    }
