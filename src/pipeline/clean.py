# -*- coding: utf-8 -*-
"""Pipeline bước 3 - CLEAN.

Thực hiện POLICY đã chốt trong configs/pipeline.yaml:
- Loại bản ghi không hợp lệ / nhiễu (rỗng, gibberish, quảng cáo...)
- Xử lý trùng lặp (chính xác và sau chuẩn hoá)
- Xử lý xung đột nhãn (cùng review nhưng nhãn khác nhau)

Nguyên tắc:
- Khoá so trùng chỉ dùng để PHÁT HIỆN, không thay thế văn bản.
- Xung đột nhãn KHÔNG tự động chọn -> đưa vào "quarantine" để xem xét tay.
- Mọi bản ghi bị loại đều được GHI LẠI, không biến mất im lặng.
"""

from collections import Counter

from src import config, utils


def _build_records(splits, aspects):
    """Chuyển các DataFrame thành danh sách bản ghi để xử lý thống nhất."""
    records = []
    for name, df in splits.items():
        texts = df[config.TEXT_COLUMN].astype(str).tolist()
        stripped = df[aspects].astype(str).apply(lambda col: col.str.strip())
        aspect_values = {aspect: stripped[aspect].tolist() for aspect in aspects}
        for index in range(len(df)):
            records.append({
                "split": name,
                "pos": index,
                "text": texts[index],
                "labels": tuple(aspect_values[aspect][index] for aspect in aspects),
            })
    return records


def _noise_reason(text, ccfg):
    """Trả về lý do nếu bản ghi cần loại, hoặc None nếu giữ lại.

    Thứ tự kiểm tra quan trọng: rỗng trước, rồi mới tới các nhóm khác.
    """
    if ccfg["remove_empty"] and text.strip() == "":
        return "review rỗng"
    if ccfg["remove_gibberish"] and utils.is_gibberish(text):
        return "chuỗi ký tự vô nghĩa (gibberish)"
    if ccfg["remove_ads"] and utils.is_advertisement(text):
        return "quảng cáo / tin nhắn nhà mạng"
    if ccfg.get("remove_code") and utils.is_code_like(text):
        return "chứa mã HTML / SQL / code"
    return None


def _remove_eval_overlap(records, ignore_diacritics=False):
    """Loại khỏi val/test những bản ghi đã xuất hiện trong train.

    Đây là cách xử lý RÒ RỈ DỮ LIỆU (leakage): nếu một review vừa nằm trong train
    vừa nằm trong test, điểm đánh giá model sẽ cao giả tạo vì model đã "học" nó.

    Cách xử lý: GIỮ trong train, LOẠI khỏi val/test.
    Lý do: tập train cần dữ liệu để học; tập eval phải sạch mới đo đúng.

    So trùng bằng KHOÁ so trùng (`utils.dedup_key`) - cùng khoá mà bước xử lý
    trùng lặp dùng, nên hai chỗ luôn nhất quán. Khoá này bỏ dấu câu; dấu tiếng
    Việt CHỈ bị bỏ khi `ignore_diacritics=True` (mặc định false, nên "Son đẹp!"
    và "son dep" là hai review khác nhau).

    Trả về (kept, removed).
    """
    def key(text):
        return utils.dedup_key(text, ignore_diacritics=ignore_diacritics)

    train_keys = {
        key(rec["text"]) for rec in records if rec["split"] == "train"
    }

    kept, removed = [], []
    for rec in records:
        if rec["split"] != "train" and key(rec["text"]) in train_keys:
            removed.append([
                rec["split"], rec["pos"],
                "rò rỉ dữ liệu (review đã có trong train)",
                rec["text"][:200],
            ])
            continue
        kept.append(rec)
    return kept, removed


def _dedup_pass(records, key_of, policy, reason_label):
    """Một lượt xử lý trùng lặp.

    - Gom các bản ghi theo `key_of`.
    - Nhóm chỉ có 1 bản ghi: giữ.
    - Nhóm có nhiều bản ghi VÀ nhãn giống nhau: giữ bản ghi đầu, loại phần còn lại.
    - Nhóm có nhiều bản ghi VÀ nhãn KHÁC nhau:
        + policy = "quarantine": đưa TẤT CẢ ra khỏi tập (chờ xem xét tay)
        + policy = "keep_first": vẫn giữ bản ghi đầu

    Trả về (kept, removed, quarantine).
    """
    groups = {}
    order = []
    for rec in records:
        key = key_of(rec)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(rec)

    kept, removed, quarantine = [], [], []
    for key in order:
        group = groups[key]
        if len(group) == 1:
            kept.append(group[0])
            continue

        has_conflict = len({rec["labels"] for rec in group}) > 1
        if has_conflict and policy == "quarantine":
            for rec in group:
                quarantine.append([
                    rec["split"], rec["pos"],
                    reason_label + " + xung đột nhãn",
                    rec["text"][:200],
                ])
        else:
            kept.append(group[0])
            for rec in group[1:]:
                removed.append([
                    rec["split"], rec["pos"], reason_label, rec["text"][:200],
                ])
    return kept, removed, quarantine

def run(context):
    cfg = context["config"]
    ccfg = cfg["steps"]["clean"]
    dedup_cfg = ccfg["deduplicate"]
    # Quy tắc của KHOÁ so trùng (dùng cho cả xử lý trùng lặp và xử lý rò rỉ).
    ignore_diacritics = bool(dedup_cfg.get("ignore_diacritics", False))
    splits = context["splits"]
    out_dir = context["out_dir"]

    before_counts = {name: len(df) for name, df in splits.items()}
    records = _build_records(splits, context["dataset"]["aspects"])

# ---
    # 1. Loại bản ghi không hợp lệ / nhiễu
# ---
    removed = []
    kept = []
    for rec in records:
        reason = _noise_reason(rec["text"], ccfg)
        if reason:
            removed.append([rec["split"], rec["pos"], reason, rec["text"][:200]])
        else:
            kept.append(rec)

    noise_removed = len(removed)

# ---
    # 2. Xử lý rò rỉ dữ liệu giữa các split (nếu được bật)
# ---
    leakage_removed = 0
    if ccfg.get("leakage", {}).get("remove_eval_overlap", False):
        kept, part_removed = _remove_eval_overlap(
            kept, ignore_diacritics=ignore_diacritics)
        leakage_removed = len(part_removed)
        removed.extend(part_removed)

# ---
    # 3. Xử lý trùng lặp (hai lượt: chính xác -> theo khoá so trùng)
    #
    # Tên gọi: lượt 2 KHÔNG phải bước Normalize. Nó so bằng `utils.dedup_key`
    # (bỏ hoa/thường, gộp khoảng trắng, bỏ dấu câu, và tuỳ config mà bỏ cả dấu
    # tiếng Việt) - đây là quy tắc của KHOÁ, văn bản gốc không bị sửa.
# ---
    scope = dedup_cfg["scope"]
    policy = dedup_cfg["conflict_policy"]
    quarantine = []
    exact_removed = 0
    normalized_removed = 0

    if dedup_cfg["exact"]:
        if scope == "global":
            key_of = lambda rec: rec["text"]                              # noqa: E731
        else:
            key_of = lambda rec: (rec["split"], rec["text"])              # noqa: E731
        kept, part_removed, part_quarantine = _dedup_pass(
            kept, key_of, policy, "trùng lặp chính xác"
        )
        exact_removed = len(part_removed)
        removed.extend(part_removed)
        quarantine.extend(part_quarantine)

    if dedup_cfg["normalized"]:
        def dedup_key_of(rec):
            return utils.dedup_key(rec["text"], ignore_diacritics=ignore_diacritics)

        if scope == "global":
            key_of = dedup_key_of
        else:
            key_of = lambda rec: (rec["split"], dedup_key_of(rec))        # noqa: E731
        kept, part_removed, part_quarantine = _dedup_pass(
            kept, key_of, policy, "trùng lặp theo khoá so trùng"
        )
        normalized_removed = len(part_removed)
        removed.extend(part_removed)
        quarantine.extend(part_quarantine)

# ---
    # 4. Dựng lại các DataFrame đã làm sạch
# ---
    kept_positions = {}
    for rec in kept:
        kept_positions.setdefault(rec["split"], []).append(rec["pos"])

    new_splits = {}
    for name, df in splits.items():
        positions = kept_positions.get(name, [])
        new_splits[name] = df.iloc[positions].reset_index(drop=True)
    context["splits"] = new_splits
    # Vị trí gốc của từng dòng được giữ lại: bước Final Validate dùng để đối
    # chiếu văn bản sau pipeline với ĐÚNG dòng gốc của nó.
    context["kept_positions"] = kept_positions

# ---
    # 5. Ghi lại các bản ghi bị loại và bị cách ly
# ---
    removed_path = utils.write_csv(
        removed or [["-", "-", "không có", ""]],
        ["split", "dòng gốc", "lý do loại", "văn bản (rút gọn)"],
        out_dir / "removed_records.csv",
    )
    quarantine_path = utils.write_csv(
        quarantine or [["-", "-", "không có", ""]],
        ["split", "dòng gốc", "lý do", "văn bản (rút gọn)"],
        out_dir / "quarantine_records.csv",
    )

# ---
    # 6. Bảng và biểu đồ tổng hợp
    #
    # Mỗi dòng vào Clean kết thúc ở đúng MỘT trong ba nhóm: giữ lại, bị loại,
    # hoặc bị cách ly. Ba nhóm này cộng lại bằng số dòng vào, nên biểu đồ xếp
    # chồng dưới đây khớp với các thẻ số liệu (trước đây cột "đã bỏ" gộp cả
    # phần cách ly nên không cộng lại được).
# ---
    quarantine_per_split = Counter(row[0] for row in quarantine)
    flow_rows = []
    for name in splits:
        quarantined = quarantine_per_split.get(name, 0)
        kept_here = len(new_splits[name])
        flow_rows.append([
            name,
            before_counts[name],
            kept_here,
            before_counts[name] - kept_here - quarantined,
            quarantined,
        ])

    total_before = sum(row[1] for row in flow_rows)
    total_after = sum(row[2] for row in flow_rows)
    total_removed = sum(row[3] for row in flow_rows)
    total_quarantine = sum(row[4] for row in flow_rows)
    flow_rows.append(["Tổng", total_before, total_after, total_removed,
                      total_quarantine])

    reason_counter = Counter(row[2] for row in removed)
    reason_rows = [[key, value] for key, value in reason_counter.most_common()]

    # Số liệu chi tiết ra CSV: báo cáo chỉ vẽ biểu đồ cho hai bảng số này, không
    # hiện thêm bảng có đúng bấy nhiêu con số (quy ước: mỗi số liệu một lần).
    flow_path = utils.write_csv(
        flow_rows,
        ["split", "số dòng trước Clean", "sau Clean", "bị loại", "cách ly"],
        out_dir / "clean_flow.csv",
    )
    reason_path = utils.write_csv(
        reason_rows or [["không có", 0]],
        ["lý do", "số dòng"],
        out_dir / "clean_reasons.csv",
    )

    flow_chart = {
        "title": "Số dòng trước và sau Clean, tách theo kết quả xử lý",
        "kind": "stacked_bar",
        "x": [row[0] for row in flow_rows],
        "series": {
            "sau Clean (giữ lại)": [row[2] for row in flow_rows],
            "bị loại": [row[3] for row in flow_rows],
            "cách ly (xung đột nhãn)": [row[4] for row in flow_rows],
        },
        "y_label": "số dòng",
    }

    reason_chart = {
        "title": "Số dòng bị loại theo lý do (không tính phần cách ly)",
        "kind": "bar",
        "x": [row[0] for row in reason_rows],
        "y": [row[1] for row in reason_rows],
        "x_label": "lý do",
        "y_label": "số dòng",
        "orientation": "h",
    }

    return {
        "id": "pipeline_clean",
        "title": "Step 3 - Clean (loại nhiễu, trùng lặp, cách ly xung đột)",
        "cards": [
            {"label": "Số dòng trước Clean", "value": "{}".format(total_before)},
            {"label": "Số dòng sau Clean", "value": "{}".format(total_after)},
            {"label": "Số dòng bị loại", "value": "{}".format(total_removed)},
            {"label": "Số dòng bị cách ly (xung đột nhãn)",
             "value": "{}".format(total_quarantine)},
            {"label": "Loại do nhiễu (rỗng / vô nghĩa / quảng cáo / code)",
             "value": noise_removed},
            {"label": "Loại do rò rỉ dữ liệu (val, test trùng train)",
             "value": leakage_removed},
            {"label": "Loại do trùng chính xác", "value": exact_removed},
            {"label": "Loại do trùng theo khoá so trùng",
             "value": normalized_removed},
        ],
        "charts": [flow_chart] + ([reason_chart] if reason_rows else []),
        "tables": [
            {
                # "Số dòng vào / giữ lại / bị loại / cách ly" đã có biểu đồ ở
                # trên; số chi tiết nằm trong clean_flow.csv và clean_reasons.csv.
                "title": "Thiết lập Clean đang áp dụng",
                "columns": ["thiết lập", "giá trị"],
                "rows": [
                    ["phạm vi so trùng", scope],
                    ["cách xử lý xung đột nhãn", policy],
                    ["remove_empty (loại review rỗng)", utils.on_off(ccfg["remove_empty"])],
                    ["remove_gibberish (loại chuỗi vô nghĩa)",
                     utils.on_off(ccfg["remove_gibberish"])],
                    ["remove_ads (loại quảng cáo)", utils.on_off(ccfg["remove_ads"])],
                    ["remove_code (loại mã HTML / SQL / code)",
                     utils.on_off(ccfg.get("remove_code"))],
                    ["deduplicate.exact (loại trùng chính xác)",
                     utils.on_off(dedup_cfg["exact"])],
                    ["deduplicate.normalized (loại trùng theo khoá so trùng)",
                     utils.on_off(dedup_cfg["normalized"])],
                    ["deduplicate.ignore_diacritics (khoá bỏ dấu tiếng Việt)",
                     utils.on_off(ignore_diacritics)],
                    ["leakage.remove_eval_overlap (loại val/test trùng train)",
                     utils.on_off(ccfg["leakage"]["remove_eval_overlap"])],
                ],
            },
        ],
        "files": [utils.rel(removed_path), utils.rel(quarantine_path),
                  utils.rel(flow_path), utils.rel(reason_path)],
    }
