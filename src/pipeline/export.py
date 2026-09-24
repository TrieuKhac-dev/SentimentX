# -*- coding: utf-8 -*-
"""Pipeline bước 7 - EXPORT.

Ghi ra đĩa:
- data/processed/<mã>/train.csv, val.csv, test.csv
  (dạng multi_head: cột văn bản + một cột cho mỗi aspect, chứa mã nhãn)
- data/processed/<mã>/label_map.json     (aspect + mã nhãn)
- data/processed/<mã>/processing_log.json
  (dấu vết đầy đủ: mã phiên bản, sha256 của hai file cấu hình và của mọi file dữ liệu nguồn,
  số dòng từng bước. Nằm CÙNG thư mục với dataset mà nó mô tả, nên chép riêng thư mục đó đi
  đâu vẫn giữ đủ dấu vết. Đây cũng là căn cứ cho guard bất biến.)

Pipeline chỉ xuất MỘT dạng dữ liệu (bảng multi_head). Dạng JSONL cho model sinh được tạo khi
cần, xem src/preprocessing/loader.py.

Báo cáo HTML do build_report.py sinh ra từ file kết quả, vì chỉ ở đó mới có đầy đủ số liệu của
tất cả các bước.
"""

from src import config, utils, versioning


def _source_log(dataset_cfg, source):
    """Một nguồn kèm sha256 từng file dữ liệu. Guard bất biến đọc lại các giá trị này."""
    return {
        "kind": source["kind"],
        "name": source["name"],
        "version": source["version"],
        "dir": utils.rel(source["dir"]),
        "files": [
            {"name": path.name, "sha256": versioning.file_sha256(path)}
            for path in versioning.source_files(dataset_cfg, source)
        ],
    }


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

# ---
    # 1. Bảng multi_head cho từng split
# ---
    columns = [config.TEXT_COLUMN] + aspects
    for name, rows in transformed["rows_per_split"].items():
        path = utils.write_csv(
            rows, columns, processed_dir / "{}.csv".format(name)
        )
        written.append([path.name, len(rows), "multi_head (văn bản + mã nhãn)"])
        row_chart_data.append([name, len(rows)])

# ---
    # 2. Bảng mã nhãn
# ---
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

# ---
    # 3. Mẫu ABSA dạng JSONL
    #
    # KHÔNG ghi ở đây nữa. Dạng JSONL chỉ là một cách TRÌNH BÀY khác của cùng
    # một dữ liệu, nên nó được sinh khi cần cho model sinh (Qwen3 / ViTASA)
    # từ chính file processed_*.csv:
    #     from src.preprocessing import loader
    #     loader.to_absa_records("train")
    # Nhờ vậy pipeline chỉ xuất MỘT dạng dữ liệu duy nhất.
# ---

# ---
    # 4. Log truy vết
# ---
    original = context.get("original_counts", {})
    final = {name: len(df) for name, df in context["splits"].items()}

    log_path = utils.write_json(
        {
            "schema": 1,
            "version_id": context.get("version_id", ""),
            "dataset": {
                "name": dataset_cfg["name"],
                "version": dataset_cfg.get("version"),
                "config": utils.rel(dataset_cfg["_path"]),
                "config_sha256": versioning.file_sha256(dataset_cfg["_path"]),
                "sources": [_source_log(dataset_cfg, source)
                            for source in dataset_cfg.get("_sources") or []],
            },
            "pipeline": {
                "version": cfg.get("version"),
                "config": utils.rel(cfg["_path"]),
                "config_sha256": versioning.file_sha256(cfg["_path"]),
                "settings": {key: value for key, value in cfg.items()
                             if not key.startswith("_")},
            },
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
        "title": "Step 7 - Export (ghi kết quả)",
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
