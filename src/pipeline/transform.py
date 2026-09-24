# -*- coding: utf-8 -*-
"""Pipeline bước 5 - TRANSFORM.

Chuyển dữ liệu đã sạch sang dạng mà model có thể dùng:

1. Dạng "multi_head": một bảng gồm cột văn bản + 7 cột aspect,
   mỗi ô là MÃ SỐ nhãn:
       0 = aspect không được nhắc tới
       1 = positive
       2 = negative
       3 = neutral

2. Dạng JSON: mỗi dòng là một object
   {"split": ..., "text": ..., "labels": {"colour": "positive", ...}}
   Chỉ chứa các aspect THỰC SỰ được nhắc tới.

Bước này KHÔNG đọc/ghi file - việc ghi do bước Export đảm nhiệm.
"""

from collections import Counter

from src import config


def _label_id(value, label_to_id):
    """Đổi nhãn chữ thành mã số. Giá trị lạ trả về -1 để dễ phát hiện."""
    if value == "":
        return label_to_id[config.NULL_LABEL]
    return label_to_id.get(value, -1)


def run(context):
    tcfg = context["config"]["transform"]
    splits = context["splits"]
    dataset_cfg = context["dataset"]
    aspects = dataset_cfg["aspects"]
    label_to_id = dataset_cfg["_label_to_id"]

    rows_per_split = {}
    json_records = []
    no_aspect_rows = []
    code_counter = Counter()

    for name, df in splits.items():
        texts = df[config.TEXT_COLUMN].astype(str).tolist()
        stripped = df[aspects].astype(str).apply(lambda col: col.str.strip())
        aspect_values = {aspect: stripped[aspect].tolist() for aspect in aspects}

        rows = []
        for index, text in enumerate(texts):
            values = {aspect: aspect_values[aspect][index] for aspect in aspects}
            codes = [_label_id(values[aspect], label_to_id) for aspect in aspects]
            code_counter.update(codes)
            rows.append([text] + codes)

            mentioned = {aspect: value for aspect, value in values.items() if value != ""}
            if mentioned:
                json_records.append({"split": name, "text": text, "labels": mentioned})
            else:
                no_aspect_rows.append([name, index, text[:100]])

        rows_per_split[name] = rows

    context["transformed"] = {
        "rows_per_split": rows_per_split,
        "json_records": json_records,
        "no_aspect_rows": no_aspect_rows,
    }

# ---
    # Bảng và biểu đồ
# ---
    map_rows = [[config.NULL_LABEL or "(ô trống)", label_to_id[config.NULL_LABEL]]]
    for label in dataset_cfg["labels"]:
        map_rows.append([label, label_to_id.get(label, -1)])

    count_rows = []
    for name in splits:
        n_rows = len(rows_per_split[name])
        n_with = n_rows - sum(1 for row in no_aspect_rows if row[0] == name)
        count_rows.append([name, n_rows, n_with, n_rows - n_with])

    # Vài dòng đầu dạng multi_head KHÔNG in lên báo cáo: dữ liệu đã xử lý nằm
    # nguyên trong data/processed/*.csv, in lại chỉ làm bảng dài mà không thêm
    # thông tin nào. Bước này cũng không ghi file (việc ghi do Export đảm nhiệm).

    count_chart = {
        "title": "Số dòng có / không có nhãn khía cạnh, theo split",
        "kind": "grouped_bar",
        "x": [row[0] for row in count_rows],
        "series": {
            "có ít nhất 1 nhãn khía cạnh": [row[2] for row in count_rows],
            "không có nhãn khía cạnh nào": [row[3] for row in count_rows],
        },
        "y_label": "số dòng",
    }

    code_rows = [
        [row[0], row[1], code_counter.get(row[1], 0)] for row in map_rows
    ]
    code_chart = {
        "title": "Số ô nhãn theo mã (toàn bộ dữ liệu)",
        "kind": "bar",
        "x": [row[0] for row in code_rows],
        "y": [row[2] for row in code_rows],
        "x_label": "mã nhãn",
        "y_label": "số ô",
    }

    return {
        "id": "pipeline_transform",
        "title": "Step 5 - Transform (chuyển sang dạng ABSA)",
        "cards": [
            {"label": "Định dạng xuất", "value": tcfg["format"]},
            {"label": "Số bản ghi ABSA (mỗi dòng có nhãn khía cạnh)",
             "value": "{}".format(len(json_records))},
            {"label": "Số dòng không có nhãn khía cạnh nào (không sinh bản ghi)",
             "value": len(no_aspect_rows)},
            {"label": "Số ô nhãn có giá trị lạ", "value": code_counter.get(-1, 0)},
        ],
        "charts": [count_chart, code_chart],
        "tables": [
            {
                "title": "Bảng mã nhãn (dạng multi_head: mỗi khía cạnh một cột, ô là mã nhãn)",
                "columns": ["nhãn", "mã số"],
                "rows": map_rows,
                "num_columns": [1],
            },
            {
                # Bảng này là bảng DUY NHẤT của bước Transform: "Số ô nhãn theo mã" đã có
                # biểu đồ, bảng mã nhãn ở trên đã cho phần ánh xạ nhãn -> mã, còn bảng
                # "Ví dụ vài dòng đầu" đã bỏ vì chỉ lặp lại data/processed/*.csv.
                "title": "Số dòng theo split",
                "columns": ["split", "số dòng", "có ít nhất 1 nhãn khía cạnh",
                            "không có nhãn khía cạnh nào"],
                "rows": count_rows,
                "num_columns": [1, 2, 3],
            },
        ],
        "files": [],
    }
