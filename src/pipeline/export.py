# -*- coding: utf-8 -*-
"""Pipeline bước 7 — EXPORT.

Ghi ra đĩa (thư mục kết quả của phiên bản hiện tại):
- <data/processed>/versions/<mã phiên bản>/processed_train.csv, _val, _test
  (dạng multi_head: cột văn bản + một cột cho mỗi aspect, chứa mã nhãn)
- <data/processed>/versions/<mã phiên bản>/label_map.json  (aspect + mã nhãn)
- <data/processed>/versions/<mã phiên bản>/processing_log.json
  (config + số liệu để truy vết: nằm CÙNG thư mục với dataset mà nó mô tả,
  nên chép riêng thư mục phiên bản đi đâu vẫn giữ đủ dấu vết)

Pipeline chỉ xuất MỘT dạng dữ liệu (bảng multi_head). Dạng JSONL cho model
sinh được tạo khi cần, xem src/preprocessing/loader.py.

Báo cáo HTML do build_report.py sinh ra từ file kết quả,
vì chỉ ở đó mới có đầy đủ số liệu của tất cả các bước.
"""

from src import config, utils


def run(context):
    cfg = context["config"]
    transformed = context["transformed"]
    out_dir = context["out_dir"]
    processed_dir = context["processed_dir"]
    dataset_cfg = context["dataset"]
    aspects = dataset_cfg["aspects"]
    label_to_id = dataset_cfg["_label_to_id"]

    written = []
    row_chart_data = []

    # -----------------------------------------------------------------
    # 1. Bảng multi_head cho từng split
    # -----------------------------------------------------------------
    columns = [config.TEXT_COLUMN] + aspects
    for name, rows in transformed["rows_per_split"].items():
        path = utils.write_csv(
            rows, columns, processed_dir / "processed_{}.csv".format(name)
        )
        written.append([path.name, len(rows), "multi_head (văn bản + mã nhãn)"])
        row_chart_data.append([name, len(rows)])

    # -----------------------------------------------------------------
    # 2. Bảng mã nhãn
    # -----------------------------------------------------------------
    utils.write_json(
        {
            "dataset": dataset_cfg["name"],
            "version_id": context.get("version_id", ""),
            "aspects": aspects,
            "labels": dataset_cfg["labels"],
            "label_to_id": label_to_id,
            "id_to_label": {
                str(value): key for key, value in label_to_id.items()
            },
        },
        processed_dir / "label_map.json",
    )
    written.append(["label_map.json", len(aspects) + len(dataset_cfg["labels"]),
                    "bảng mã nhãn, danh sách aspect"])

    # -----------------------------------------------------------------
    # 3. Mẫu ABSA dạng JSONL
    #
    # KHÔNG ghi ở đây nữa. Dạng JSONL chỉ là một cách TRÌNH BÀY khác của cùng
    # một dữ liệu, nên nó được sinh khi cần cho model sinh (Qwen3 / ViTASA)
    # từ chính file processed_*.csv:
    #     from src.preprocessing import loader
    #     loader.to_absa_records("train")
    # Nhờ vậy pipeline chỉ xuất MỘT dạng dữ liệu duy nhất.
    # -----------------------------------------------------------------

    # -----------------------------------------------------------------
    # 4. Log truy vết
    # -----------------------------------------------------------------
    original = context.get("original_counts", {})
    final = {name: len(df) for name, df in context["splits"].items()}

    config_path = cfg.get("_path")
    try:
        config_path_display = config_path.relative_to(config.ROOT_DIR).as_posix()
    except (AttributeError, ValueError):
        config_path_display = str(config_path)

    log_path = utils.write_json(
        {
            "pipeline_version": cfg.get("version", "unknown"),
            "config_file": config_path_display,
            "config": {k: v for k, v in cfg.items() if not k.startswith("_")},
            "record_counts": {
                "before": original,
                "after": final,
                "removed_total": sum(original.values()) - sum(final.values()),
            },
            "number_of_validation_issues": len(context.get("validation_issues", [])),
            "number_of_json_records": len(transformed["json_records"]),
            "outputs": [item[0] for item in written],
        },
        processed_dir / "processing_log.json",
    )

    config_rows = utils.config_to_rows(cfg)

    return {
        "id": "pipeline_export",
        "title": "Step 7 — Export (ghi kết quả)",
        "cards": [
            {"label": "Số file đã ghi", "value": len(written)},
            {"label": "Số dòng đầu ra", "value": "{}".format(sum(final.values()))},
            {"label": "Phiên bản pipeline", "value": cfg.get("version", "unknown")},
        ],
        "charts": [
            {
                "title": "Số dòng ghi ra theo split",
                "kind": "bar",
                "x": [row[0] for row in row_chart_data],
                "y": [row[1] for row in row_chart_data],
                "y_label": "số dòng",
            },
        ],
        "tables": [
            {
                "title": "Các file đã ghi",
                "columns": ["file", "số dòng / mục", "định dạng"],
                "rows": written,
                "num_columns": [1],
            },
            {
                "title": "Cấu hình đã dùng cho lần chạy này",
                "columns": ["thiết lập", "giá trị"],
                "rows": config_rows,
            },
        ],
        "files": [utils.rel(log_path)],
    }
