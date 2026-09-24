# -*- coding: utf-8 -*-
"""Pipeline bước 6 - FINAL VALIDATE (cổng chất lượng).

Đây KHÔNG phải EDA lần hai. Đây là bước kiểm tra cuối, trả lời câu hỏi:

    "Dữ liệu sau khi xử lý có còn hợp lệ để đưa cho model không?"

Kiểm tra:
1. Schema   - đủ cột, đúng tên cột, không thừa cột.
2. Văn bản  - không có review rỗng.
3. Nhãn     - không có giá trị lạ; nhãn không bị thay đổi so với lúc đầu.
4. Văn bản chỉ đổi hình thức - mỗi dòng phải khớp ĐÚNG dòng gốc sau khi áp quy
   tắc chuẩn hoá, chứng minh việc xoá trùng lặp / khoá so trùng (có bỏ dấu khi
   SO) không làm mất dấu tiếng Việt trong văn bản.
5. Toàn vẹn - số dòng khớp giữa các bước.
"""

from src import config, dataset, utils
from src.pipeline.normalize import labels_signature, normalize_steps


def run(context):
    splits = context["splits"]
    transformed = context["transformed"]
    out_dir = context["out_dir"]
    dataset_cfg = context["dataset"]
    aspects = dataset_cfg["aspects"]
    labels = dataset_cfg["labels"]
    expected = dataset.expected_columns(dataset_cfg)

    checks = []          # [tên kiểm tra, kết quả, chi tiết]
    problems = []

# ---
    # 1. Schema
# ---
    bad_schema = []
    for name, df in splits.items():
        missing = [c for c in expected if c not in df.columns]
        extra = [c for c in df.columns if c not in expected]
        if missing or extra:
            bad_schema.append("{} (thiếu: {}, thừa: {})".format(
                name, ", ".join(missing) or "-", ", ".join(extra) or "-"))
    if bad_schema:
        problems.append("schema")
        checks.append(["Schema", "LỖI", "; ".join(bad_schema)])
    else:
        checks.append(["Schema", "ĐẠT", "cả {} split đều đủ cột".format(len(splits))])

# ---
    # 2. Văn bản rỗng
# ---
    empty_total = 0
    for df in splits.values():
        empty_total += int((df[config.TEXT_COLUMN].astype(str).str.strip() == "").sum())
    if empty_total > 0:
        problems.append("văn bản rỗng")
        checks.append(["Văn bản", "LỖI", "{} review rỗng".format(empty_total)])
    else:
        checks.append(["Văn bản", "ĐẠT", "không có review rỗng"])

# ---
    # 3. Nhãn hợp lệ và nhãn không bị thay đổi
# ---
    invalid_total = 0
    for df in splits.values():
        stripped = df[aspects].astype(str).apply(lambda col: col.str.strip())
        for aspect in aspects:
            column = stripped[aspect]
            invalid_total += int(
                ((column != "") & (~column.isin(labels))).sum()
            )

    if invalid_total > 0:
        problems.append("nhãn không hợp lệ")
        checks.append(["Nhãn hợp lệ", "LỖI", "{} ô nhãn sai".format(invalid_total)])
    else:
        checks.append(["Nhãn hợp lệ", "ĐẠT", "mọi nhãn thuộc 3 giá trị hợp lệ"])

    signature_now = labels_signature(splits, aspects)
    signature_then = context.get("labels_signature_before_normalize")
    if signature_then is None:
        checks.append(["Nhãn không bị thay đổi", "BỎ QUA",
                       "không có dấu vân tay để so sánh"])
    elif signature_now == signature_then:
        checks.append(["Nhãn không bị thay đổi", "ĐẠT",
                       "dấu vân tay nhãn trùng khớp với lúc đầu"])
    else:
        problems.append("nhãn bị thay đổi")
        checks.append(["Nhãn không bị thay đổi", "LỖI",
                       "dấu vân tay nhãn KHÁC với lúc đầu"])

# ---
    # 4. Văn bản chỉ được đổi HÌNH THỨC, không được mất dấu tiếng Việt
    #
    # Mỗi dòng được giữ lại phải khớp CHÍNH XÁC với dòng gốc của nó sau khi áp
    # quy tắc chuẩn hoá (`normalize_steps` - đúng hàm mà bước Normalize dùng).
    #
    # Nhờ phép kiểm này, câu hỏi "khoá so trùng có bỏ dấu tiếng Việt thì văn bản
    # có bị mất dấu không?" được trả lời bằng số liệu: khoá so trùng chỉ dùng để
    # SO, còn văn bản xuất ra vẫn đúng từng ký tự như bản gốc sau chuẩn hoá.
# ---
    raw_texts = context.get("raw_texts") or {}
    kept_positions = context.get("kept_positions") or {}
    ncfg = context["config"]["steps"]["normalize"]
    max_repeat = int(context["config"]["thresholds"]["repeated_chars_max"])
    compared = 0
    text_mismatches = []
    for name, df in splits.items():
        texts_now = df[config.TEXT_COLUMN].astype(str).tolist()
        originals = raw_texts.get(name) or []
        positions = kept_positions.get(name) or []
        if not originals or len(positions) != len(texts_now):
            text_mismatches.append(
                "{}: thiếu dữ liệu gốc để đối chiếu".format(name))
            continue
        for index, position in enumerate(positions):
            expected, _ = normalize_steps(originals[position], ncfg, max_repeat)
            compared += 1
            if expected != texts_now[index] and len(text_mismatches) < 5:
                text_mismatches.append(
                    "{} dòng {}: {!r} != {!r}".format(
                        name, position, expected[:60], texts_now[index][:60]))

    if text_mismatches:
        problems.append("văn bản bị biến đổi ngoài quy tắc chuẩn hoá")
        checks.append(["Văn bản chỉ đổi hình thức", "LỖI",
                       "; ".join(text_mismatches)])
    else:
        checks.append([
            "Văn bản chỉ đổi hình thức", "ĐẠT",
            "{} dòng khớp đúng dòng gốc sau chuẩn hoá (không mất dấu tiếng Việt)"
            .format(compared),
        ])

# ---
    # 5. Toàn vẹn số dòng
# ---
    integrity_rows = []
    integrity_ok = True
    for name, df in splits.items():
        n_split = len(df)
        n_transform = len(transformed["rows_per_split"].get(name, []))
        ok = n_split == n_transform
        integrity_ok = integrity_ok and ok
        integrity_rows.append([name, n_split, n_transform, "ĐẠT" if ok else "LỖI"])
    if not integrity_ok:
        problems.append("số dòng không khớp")

# ---
    # 5. Báo cáo
# ---
    total_rows = sum(len(df) for df in splits.values())
    files = [
        utils.rel(utils.write_json(
            {
                "checks": [{"kiểm tra": row[0], "kết quả": row[1], "chi tiết": row[2]}
                           for row in checks],
                "problems": problems,
                "total_rows": total_rows,
                "passed": len(problems) == 0,
            },
            out_dir / "final_validation.json",
        ))
    ]

    return {
        "id": "pipeline_final_validate",
        "title": "Step 6 - Final Validate (kiểm tra dữ liệu đầu ra)",
        "cards": [
            {"label": "Số hạng mục kiểm tra", "value": len(checks)},
            {"label": "Kết quả", "value": "ĐẠT" if not problems else "CÓ LỖI"},
            {"label": "Số dòng đầu ra", "value": "{}".format(total_rows)},
            {"label": "Số vấn đề", "value": len(problems)},
        ],
        "charts": [
            {
                "title": "Toàn vẹn số dòng giữa split và dữ liệu chuyển đổi",
                "kind": "grouped_bar",
                "x": [row[0] for row in integrity_rows],
                "series": {
                    "số dòng trong split": [row[1] for row in integrity_rows],
                    "số dòng sau transform": [row[2] for row in integrity_rows],
                },
                "y_label": "số dòng",
            },
        ],
        "tables": [
            {
                "title": "Kết quả kiểm tra cuối",
                "columns": ["kiểm tra", "kết quả", "chi tiết"],
                "rows": checks,
            },
            {
                "title": "Toàn vẹn số dòng",
                "columns": ["split", "số dòng trong split", "số dòng sau transform",
                            "kết quả"],
                "rows": integrity_rows,
                "num_columns": [1, 2],
            },
        ],
        "files": files,
    }
