# -*- coding: utf-8 -*-
"""Chạy toàn bộ Data Pipeline và GHI FILE KẾT QUẢ (không vẽ báo cáo).

Cách dùng:
    python run_pipeline.py --name cosmetics --version v0.1.0

`--name` là THƯ MỤC cấu hình dataset: `configs/datasets/<tên>/`.
`--version` là TÊN FILE cấu hình trong thư mục đó: `configs/datasets/<tên>/<phiên bản>.yaml`.
Cả hai đều bắt buộc: mỗi tổ hợp cho ra một bộ dữ liệu khác nhau. Lưu ý `--version` ở đây KHÔNG phải
mã phiên bản dữ liệu đã xử lý (mã đó do pipeline in ra, dạng ...-e0ccc484).

Kết quả:
    data/processed/<mã>/{train,val,test}.csv   (dữ liệu đã xử lý)
    data/processed/<mã>/label_map.json, processing_log.json, eval_lock.json
    data/processed/<mã>/pipeline/              (pipeline_result.json, removed_records.csv, ...)
(data/reports/ chỉ có 5 nhóm bảng tổng hợp, do scripts/collect_reports.py sinh)

Pipeline gồm 7 bước, chạy tuần tự:
    load -> validate -> clean -> normalize -> transform -> final_validate -> export

Bước này KHÔNG sinh HTML. Muốn xem báo cáo, chạy tiếp:
    python build_report.py --phase pipeline --on dataset --hash <hash8|mã>
"""

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Trên Windows, console mặc định có thể không phải UTF-8 (ví dụ cp1252),
# khiến việc in tiếng Việt bị lỗi. Ép stdout/stderr sang UTF-8.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from src.core import config, dataset, paths, registry, utils, versioning
from src.reporting import result as result_io

# Thư mục cấu hình dataset, dựng từ `configs/paths.yaml` (không viết cứng trong chuỗi help:
# `tests/test_paths.py` chặn đường dẫn viết cứng trong source).
DATASET_CONFIG_DIR = utils.rel(paths.config_path("datasets"))


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Xử lý dữ liệu theo config và ghi file kết quả.",
        epilog="Cú pháp đầy đủ: docs/00_workflow/09_cli.md",
    )
    parser.add_argument(
        "--name", required=True,
        help="Tên dataset = THƯ MỤC cấu hình: {}/<tên>/ "
             "(ví dụ --name cosmetics -> {}/cosmetics/).".format(
                 DATASET_CONFIG_DIR, DATASET_CONFIG_DIR),
    )
    parser.add_argument(
        "--version", required=True,
        help="Tên FILE cấu hình dataset trong thư mục đó: {}/<tên>/<phiên bản>.yaml "
             "(ví dụ --version v0.1.0 -> {}/cosmetics/v0.1.0.yaml). Bắt buộc: mỗi phiên bản cho ra "
             "một bộ dữ liệu khác nhau. KHÔNG phải mã phiên bản dữ liệu đã xử lý.".format(
                 DATASET_CONFIG_DIR, DATASET_CONFIG_DIR),
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    print("DATA PIPELINE - xử lý dữ liệu theo config")

    # Gõ sai tên dataset là lỗi hay gặp nhất khi mới dùng: in một dòng lỗi gọn
    # (kèm gợi ý tên đúng) thay vì để traceback che mất thông báo.
    try:
        ds = dataset.load_config(args.name, args.version)
    except dataset.DatasetError as exc:
        print("LỖI: {}".format(exc))
        return 2
    cfg = utils.load_pipeline_config(ds.get("pipeline_version"))
    try:
        versioning.guard_versions(ds, cfg)
    except versioning.VersionError as exc:
        print("LỖI: {}".format(exc))
        return 2
    version_id = versioning.compute_id(ds, cfg)
    processed_dir = versioning.processed_dir(version_id)
    out_dir = versioning.pipeline_report_dir(version_id)

    # In ĐÍCH đã chốt: `--version` ở đây là file cấu hình dataset, KHÔNG phải mã phiên bản,
    # nên in thẳng đường dẫn config ra để người chạy đối chiếu bằng mắt.
    _, hash8 = versioning.version_parts(version_id)
    print("Dataset: {} (dữ liệu gốc: {})".format(
        ds["name"], utils.rel(ds["_raw_dir"])))
    print("Config dataset: {}   (--name {} --version {})".format(
        utils.rel(ds["_path"]), args.name, args.version))
    print("Config pipeline: {} - phiên bản {}".format(
        utils.rel(cfg["_path"]), cfg.get("version", "unknown")))
    print("Mã phiên bản: {} (hash8 {})".format(version_id, hash8))

    context = {
        "config": cfg,
        "out_dir": out_dir,
        "processed_dir": processed_dir,
        "dataset": ds,
        "version_id": version_id,
    }

    steps = registry.pipeline_steps()
    print("\nĐang chạy {} bước:".format(len(steps)))
    sections = []
    for step in steps:
        name = step.__name__.replace("src.pipeline.", "")
        print("  - {}".format(name))
        sections.append(step.run(context))

    original = context.get("original_counts", {})
    final = {name: len(df) for name, df in context["splits"].items()}

    # Phần đầu báo cáo chỉ chứa THÔNG TIN (file, số lượng), không nhận xét.
    meta = dataset.describe(ds) + [
        "Mã phiên bản: {}".format(version_id),
        "Config: {}".format(utils.rel(cfg["_path"])),
        "Phiên bản pipeline: {}".format(cfg.get("version", "unknown")),
        "Số dòng vào: {} - Số dòng ra: {}".format(
            sum(original.values()) if original else 0, sum(final.values())),
        "Thư mục số liệu chi tiết: {}".format(utils.rel(out_dir)),
    ]

    payload = result_io.make_payload(
        phase="pipeline",
        dataset=ds["name"],
        version_id=version_id,
        meta=meta,
        sections=sections,
        title="Báo cáo Data Pipeline - ABSA tiếng Việt",
        subtitle="Từ dữ liệu gốc đến dữ liệu sẵn sàng cho model",
    )

    path = result_io.write_result(
        payload, result_io.result_path(out_dir, "pipeline"))

    print("\nHoàn tất. Đã ghi:")
    print("  - Dataset     : {}".format(utils.rel(processed_dir)))
    print("  - File kết quả: {}".format(utils.rel(path)))
    print("  - Báo cáo     : {}".format(utils.rel(out_dir)))
    print("\nBước tiếp theo - vẽ báo cáo:")
    print("  python build_report.py --phase pipeline --on dataset --hash {}".format(hash8))


if __name__ == "__main__":
    raise SystemExit(main())
