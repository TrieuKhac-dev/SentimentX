# -*- coding: utf-8 -*-
"""Pipeline bước 2 — VALIDATE.

Kiểm tra dữ liệu có thoả điều kiện để đi tiếp hay không:
- Schema: đủ cột, đúng tên, không thừa cột.
- Nội dung: review rỗng, nhãn nằm ngoài danh sách hợp lệ.

QUAN TRỌNG: bước này CHỈ GHI NHẬN lỗi, KHÔNG sửa dữ liệu.
Mọi lỗi được ghi ra validation_report.csv để xem lại.
"""

from collections import Counter

from src import config, dataset, utils


def run(context):
    cfg = context["config"]
    vcfg = cfg["validate"]
    splits = context["splits"]
    out_dir = context["out_dir"]
    dataset_cfg = context["dataset"]
    aspects = dataset_cfg["aspects"]
    labels = dataset_cfg["labels"]
    expected = dataset.expected_columns(dataset_cfg)

    issues = []          # mỗi dòng: [split, dòng, loại lỗi, chi tiết]
    schema_rows = []

    # Cột aspect thiếu trong file gốc (loader đã tự thêm cột rỗng để chạy tiếp)
    for name, columns in (context.get("missing_columns") or {}).items():
        for column in columns:
            issues.append([name, "-", "thiếu cột aspect trong file gốc", column])

    # -----------------------------------------------------------------
    # 1. Kiểm tra schema
    # -----------------------------------------------------------------
    for name, df in splits.items():
        missing = [c for c in expected if c not in df.columns]
        extra = [c for c in df.columns if c not in expected]
        status = "OK" if not missing and not extra else "CÓ LỖI"
        schema_rows.append([
            name,
            len(df.columns),
            ", ".join(missing) if missing else "-",
            ", ".join(extra) if extra else "-",
            status,
        ])
        if vcfg["check_schema"]:
            for column in missing:
                issues.append([name, "-", "thiếu cột", column])
            for column in extra:
                issues.append([name, "-", "thừa cột", column])

    # -----------------------------------------------------------------
    # 2. Kiểm tra nội dung
    # -----------------------------------------------------------------
    if vcfg["check_content"]:
        for name, df in splits.items():
            texts = df[config.TEXT_COLUMN].astype(str).tolist()
            for index, text in enumerate(texts):
                if text.strip() == "":
                    issues.append([name, index, "review rỗng", ""])

            stripped = df[aspects].astype(str).apply(lambda col: col.str.strip())
            for aspect in aspects:
                column = stripped[aspect]
                bad_mask = (column != "") & (~column.isin(labels))
                for index in column.index[bad_mask]:
                    issues.append([
                        name, int(index), "nhãn không hợp lệ",
                        "{} = {}".format(aspect, column.loc[index]),
                    ])

    context["validation_issues"] = issues

    # -----------------------------------------------------------------
    # 3. Ghi file chi tiết và tổng hợp
    # -----------------------------------------------------------------
    report_path = utils.write_csv(
        issues or [["-", "-", "không có lỗi", ""]],
        ["split", "dòng", "loại lỗi", "chi tiết"],
        out_dir / "validation_report.csv",
    )

    counts = Counter(row[2] for row in issues)
    count_rows = [[key, value] for key, value in counts.most_common()]
    schema_ok = not any(row[4] != "OK" for row in schema_rows)

    return {
        "id": "pipeline_validate",
        "title": "Step 2 — Validate (kiểm tra, không sửa)",
        "cards": [
            {"label": "Kết quả schema", "value": "OK" if schema_ok else "CÓ LỖI"},
            {"label": "Số lỗi nội dung", "value": len(issues)},
            {"label": "Bật kiểm tra schema", "value": utils.on_off(vcfg["check_schema"])},
            {"label": "Bật kiểm tra nội dung", "value": utils.on_off(vcfg["check_content"])},
        ],
        "charts": [],
        "tables": [
            {
                # "Thiếu" / "thừa" ở đây là so với khai báo của dataset trong
                # configs/datasets/<tên>.yaml (cột văn bản + các cột khía cạnh),
                # không phải so với file gốc.
                "title": "Kiểm tra schema: so dữ liệu đã nạp với khai báo trong config dataset",
                "columns": ["split", "số cột", "cột thiếu so với config",
                            "cột thừa so với config", "kết quả"],
                "rows": schema_rows,
                "num_columns": [1],
            },
            {
                "title": "Số lỗi theo loại",
                "columns": ["loại lỗi", "số lượng"],
                "rows": count_rows,
                "num_columns": [1],
            },
        ],
        "files": [utils.rel(report_path)],
    }
