# -*- coding: utf-8 -*-
"""EDA 05 - Quan hệ giữa các split và rò rỉ dữ liệu (leakage).

Đo lường: review xuất hiện ở nhiều split, và các trường hợp cùng một review
nhưng nhãn khác nhau giữa các split.

Hai phép đo trùng lặp KHÁC NHAU, đừng so trực tiếp:
    - theo cặp split: số VĂN BẢN xuất hiện ở cả hai split của cặp;
    - "dòng val/test trùng train": số DÒNG - đúng phép mà bước Clean dùng để
      chống rò rỉ dữ liệu.

Khoá so trùng đọc từ `clean.deduplicate.ignore_diacritics` của config pipeline,
nên EDA và pipeline luôn dùng cùng một quy tắc.

Danh sách xung đột nhãn được ghi ĐẦY ĐỦ (không cắt bớt, không chỉ là ví dụ):
mỗi dòng là một ô nhãn xung đột, kèm nhãn thật của từng split.

Báo cáo chỉ có số liệu: mỗi số liệu xuất hiện một lần (bảng HOẶC biểu đồ), phần
đầy đủ nằm ở CSV.
"""

from collections import Counter, defaultdict

from src import config, utils

# Nhãn hiển thị cho ô trống (review không nhắc tới aspect đó)
NULL_TEXT = "(không nhắc tới)"

SPLIT_ORDER = ("train", "val", "test")


def run(context):
    splits = context["splits"]
    out_dir = context["out_dir"]
    aspects = context["dataset"]["aspects"]
    files = []

    # Quy tắc của KHOÁ so trùng: đọc từ config pipeline để EDA và bước Clean dùng
    # đúng một quy tắc (khi tắt `ignore_diacritics`, khoá giữ dấu tiếng Việt).
    dedup_cfg = utils.load_pipeline_config()["clean"]["deduplicate"]
    ignore_diacritics = bool(dedup_cfg.get("ignore_diacritics", False))

    def _key(text):
        return utils.dedup_key(text, ignore_diacritics=ignore_diacritics)

# ---
    # 1. Đếm trùng lặp giữa các split
# ---
    exact_map = defaultdict(set)   # văn bản gốc   -> tập split
    norm_map = defaultdict(set)    # khoá so trùng -> tập split

    for name, df in splits.items():
        for text in df[config.TEXT_COLUMN].astype(str):
            exact_map[text].add(name)
            norm_map[_key(text)].add(name)

    cross_exact = sum(1 for names in exact_map.values() if len(names) > 1)
    cross_norm = sum(1 for names in norm_map.values() if len(names) > 1)

    pair_rows = []
    for first, second in [("train", "val"), ("train", "test"), ("val", "test")]:
        n_exact = sum(1 for names in exact_map.values()
                      if first in names and second in names)
        n_norm = sum(1 for names in norm_map.values()
                     if first in names and second in names)
        pair_rows.append(["{} <-> {}".format(first, second), n_exact, n_norm])

    files.append(utils.rel(utils.write_csv(
        pair_rows,
        ["cặp split", "số văn bản trùng chính xác",
         "số văn bản trùng theo khoá so trùng"],
        out_dir / "05_split_duplicates.csv",
    )))

    # Số DÒNG của val/test trùng với train - đây mới là con số quyết định policy
    # `clean.leakage.remove_eval_overlap` (loại khỏi val/test những dòng đã có
    # trong train). Cách đếm: lấy khoá chuẩn hoá của mọi dòng train, rồi xem mỗi
    # dòng val/test có khoá nằm trong tập đó hay không.
    # Khác với bảng "cặp split" ở trên: bảng đó đếm VĂN BẢN chung giữa hai split
    # bất kỳ (kể cả val ↔ test), còn hai con số dưới đây đếm DÒNG của val/test
    # trùng với train - đúng phép mà pipeline thực hiện.
    train_keys = {_key(text)
                  for text in splits["train"][config.TEXT_COLUMN].astype(str)}
    train_texts = set(splits["train"][config.TEXT_COLUMN].astype(str))
    leakage_exact = 0
    leakage_normalized = 0
    for name in ("val", "test"):
        if name not in splits:
            continue
        texts = splits[name][config.TEXT_COLUMN].astype(str)
        leakage_exact += int(texts.isin(train_texts).sum())
        leakage_normalized += int(texts.map(_key).isin(train_keys).sum())

    duplicate_chart = {
        "title": ("Số văn bản xuất hiện ở CẢ HAI split của cặp "
                  "(một văn bản có thể bị đếm ở nhiều cặp)"),
        "kind": "grouped_bar",
        "x": [row[0] for row in pair_rows],
        "series": {
            "trùng chính xác": [row[1] for row in pair_rows],
            "trùng theo khoá so trùng": [row[2] for row in pair_rows],
        },
        "x_label": "cặp split",
        "y_label": "số văn bản",
    }

# ---
    # 2. Xung đột nhãn: cùng một review nhưng nhãn khác nhau - ghi ĐẦY ĐỦ
# ---
    labels_by_key = defaultdict(lambda: defaultdict(set))
    splits_by_key = defaultdict(set)
    text_by_key = {}
    for name, df in splits.items():
        texts = df[config.TEXT_COLUMN].astype(str).tolist()
        stripped = df[aspects].astype(str).apply(lambda col: col.str.strip())
        aspect_values = {aspect: stripped[aspect].tolist() for aspect in aspects}
        for index, text in enumerate(texts):
            key = _key(text)
            splits_by_key[key].add(name)
            # Giữ NGUYÊN văn bản (kể cả xuống dòng) để báo cáo hiện đúng như
            # trong CSV - nếu gộp xuống dòng thành khoảng trắng thì người đọc
            # copy ô đó đi tìm trong CSV sẽ không thấy (bảng dùng `pre_wrap`).
            text_by_key.setdefault(key, text)
            for aspect in aspects:
                value = aspect_values[aspect][index]
                labels_by_key[(key, aspect)][name].add(value or NULL_TEXT)

    def _cell(per_split, split_name):
        """Nhãn của một split (nhiều nhãn thì nối lại), '-' nếu split không có."""
        values = per_split.get(split_name)
        return " / ".join(sorted(values)) if values else "-"

    conflict_rows = []      # bảng đầy đủ đưa lên báo cáo
    conflict_file_rows = []  # bản ghi ra CSV, kèm khoá chuẩn hoá
    conflict_reviews = 0
    for key, text in text_by_key.items():
        names = splits_by_key[key]
        if len(names) < 2:
            continue
        rows_here = []
        for aspect in aspects:
            per_split = labels_by_key[(key, aspect)]
            all_values = set()
            for values in per_split.values():
                all_values |= values
            if len(all_values) < 2:
                continue
            row = [text, aspect] + [_cell(per_split, name)
                                    for name in SPLIT_ORDER]
            rows_here.append(row)
            conflict_file_rows.append([text, key, aspect]
                                      + [_cell(per_split, name)
                                         for name in SPLIT_ORDER])
        if rows_here:
            conflict_reviews += 1
            conflict_rows.extend(rows_here)

    files.append(utils.rel(utils.write_csv(
        conflict_file_rows or [["-", "-", "-", "-", "-", "-"]],
        ["văn bản", "khoá chuẩn hoá", "khía cạnh"] + list(SPLIT_ORDER),
        out_dir / "05_split_label_conflict.csv",
    )))

    # Hai cách đếm trùng lặp khác nhau, ghi ra một file để tra cứu:
    #   - "văn bản ở từ 2 split trở lên": một VĂN BẢN bị đếm một lần, dù nó nằm
    #     ở 2 hay 3 split;
    #   - "dòng val/test trùng train": đếm theo DÒNG và chỉ so với train - đúng
    #     phép mà Clean dùng để chống rò rỉ dữ liệu (leakage.remove_eval_overlap).
    totals_path = utils.write_csv(
        [
            ["văn bản xuất hiện ở từ 2 split trở lên", cross_exact, cross_norm],
            ["dòng val/test trùng train", leakage_exact, leakage_normalized],
        ],
        ["phép đếm", "trùng chính xác", "trùng theo khoá so trùng"],
        out_dir / "05_split_duplicate_totals.csv",
    )

    conflict_table = {
        "title": ("Xung đột nhãn giữa các split - toàn bộ {} ô nhãn "
                  "(review × khía cạnh) bị xung đột").format(len(conflict_rows)),
        "columns": ["văn bản", "khía cạnh"] + list(SPLIT_ORDER),
        "rows": conflict_rows,
        # Cột "khía cạnh" và 3 cột split chỉ chứa chữ ngắn: cho co hết mức để cột
        # văn bản (rất dài) được rộng.
        "narrow_columns": [1, 2, 3, 4],
        # Văn bản là nguyên văn trong CSV (có thể có xuống dòng, thậm chí có gạch
        # đầu dòng "•" do người viết tự gõ): giữ đúng xuống dòng để tra lại được.
        "pre_wrap_columns": [0],
    }

# ---
    # 3. So sánh phân bố nhãn giữa các split - chỉ ghi ra CSV để tra cứu
    #    (báo cáo đã trình bày phần này ở EDA 02, không lặp lại)
# ---
    dist_rows = []
    for name, df in splits.items():
        stripped = df[aspects].astype(str).apply(lambda col: col.str.strip())
        total = len(df)
        for aspect in aspects:
            column = stripped[aspect]
            counts = Counter(column.tolist())
            dist_rows.append([
                name,
                aspect,
                round(100 * counts.get("positive", 0) / total, 2),
                round(100 * counts.get("negative", 0) / total, 2),
                round(100 * counts.get("neutral", 0) / total, 2),
                round(100 * counts.get("", 0) / total, 2),
            ])

    files.append(utils.rel(utils.write_csv(
        dist_rows,
        ["split", "khía cạnh", "positive %", "negative %", "neutral %",
         "không nhắc tới %"],
        out_dir / "05_split_label_distribution.csv",
    )))

    return {
        "id": "split_leakage",
        "title": "EDA 05 - Quan hệ giữa các split và rò rỉ dữ liệu",
        "cards": [
            {"label": "Số dòng val/test trùng train - chính xác",
             "value": "{}".format(leakage_exact)},
            {"label": "Số dòng val/test trùng train - theo khoá so trùng",
             "value": "{}".format(leakage_normalized)},
            {"label": "Số review bị xung đột nhãn giữa các split",
             "value": "{}".format(conflict_reviews)},
            {"label": "Số ô nhãn (review × khía cạnh) bị xung đột",
             "value": "{}".format(len(conflict_rows))},
        ],
        "charts": [duplicate_chart],
        "tables": [conflict_table],
        "files": files + [utils.rel(totals_path)],
    }
