# -*- coding: utf-8 -*-
"""Chạy toàn bộ EDA và GHI FILE KẾT QUẢ (không vẽ báo cáo).

Cách dùng:
    python run_eda.py
    python run_eda.py --dataset cosmetics

Kết quả (trong thư mục theo phiên bản: data/reports/eda/versions/<mã>/):
    <mã>/eda_result.json   (đủ mọi phần — file build_report.py đọc lại)
    <mã>/01_*.json …       (file kết quả riêng của từng phần)
    <mã>/*.csv             (bảng số liệu chi tiết của từng phần)

Bước này KHÔNG sinh HTML. Muốn xem báo cáo, chạy tiếp:
    python build_report.py --phase eda
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

from src import config, dataset, registry, utils, versioning
from src.reporting import result as result_io


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Khảo sát dữ liệu (EDA) và ghi file kết quả."
    )
    parser.add_argument(
        "--dataset", default=None,
        help="Tên dataset (mặc định: dataset đầu tiên trong configs/datasets/).",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    print("=" * 70)
    print("EDA — Khảo sát dữ liệu (chỉ đo lường, KHÔNG sửa dữ liệu)")
    print("=" * 70)

    # Gõ sai tên dataset là lỗi hay gặp nhất khi mới dùng: in một dòng lỗi gọn
    # (kèm gợi ý tên đúng) thay vì để traceback che mất thông báo.
    try:
        ds = dataset.load_config(args.dataset)
    except dataset.DatasetError as exc:
        print("LỖI: {}".format(exc))
        return 2
    version_id = versioning.compute_id(ds, config.PIPELINE_CONFIG_PATH)
    out_dir = versioning.version_dir(config.EDA_REPORT_DIR, version_id)

    print("Dataset: {} (cấu hình: {})".format(ds["name"], utils.rel(ds["_path"])))
    print("Đang đọc dữ liệu gốc từ: {}".format(utils.rel(ds["_raw_dir"])))
    print("Mã phiên bản: {}".format(version_id))

    splits, missing = dataset.load_splits(ds)
    full, _ = dataset.load_full(ds)
    for name, df in splits.items():
        print("  - {:5s}: {:>6,} dòng x {} cột".format(name, len(df), len(df.columns)))
    if full is not None:
        print("  - full : {:>6,} dòng x {} cột".format(len(full), len(full.columns)))
    for name, columns in missing.items():
        print("  ! {} thiếu cột aspect: {}".format(name, ", ".join(columns)))

    context = {
        "splits": splits,
        "full": full,
        "out_dir": out_dir,
        "dataset": ds,
        "version_id": version_id,
        # Cột aspect thiếu trong file gốc: EDA 01 dùng để ghi rõ file nào thiếu gì
        "missing_columns": missing,
    }

    print("\nĐang chạy các module EDA:")
    sections = []
    for module in registry.EDA_MODULES:
        name = module.__name__.replace("src.eda.", "")
        print("  - {}".format(name))
        sections.append(module.run(context))

    # Phần đầu báo cáo chỉ chứa THÔNG TIN (file, số lượng), không nhận xét.
    # Câu "cột aspect thiếu" phải ghi rõ FILE NÀO thiếu cột nào, vì "file gốc"
    # nói chung là thông tin không tra cứu được.
    if missing:
        missing_detail = "; ".join(
            "{} ({}): {}".format(name, ds["splits"].get(name, "?"),
                                 ", ".join(columns))
            for name, columns in missing.items()
        )
    else:
        missing_detail = "không file nào thiếu"
    meta = dataset.describe(ds) + [
        "Mã phiên bản: {}".format(version_id),
        "File gốc đã đọc: {}".format(", ".join(ds["splits"].values())),
        "Cột khía cạnh khai báo trong config nhưng thiếu ở file gốc: {} ({})".format(
            sum(len(columns) for columns in missing.values()), missing_detail),
        "Thư mục số liệu chi tiết: {}".format(utils.rel(out_dir)),
    ]

    payload = result_io.make_payload(
        phase="eda",
        dataset=ds["name"],
        version_id=version_id,
        meta=meta,
        sections=sections,
        title="Báo cáo EDA — ABSA tiếng Việt",
        subtitle="Khảo sát dữ liệu của dataset '{}'".format(ds["name"]),
    )

    # Mỗi mục được ghi thêm một file JSON riêng (0X_<mục>.json) trong cùng thư
    # mục phiên bản. Báo cáo KHÔNG liệt kê từng file nữa: mục nào cũng có nhiều
    # file nên danh sách rất dài mà không giúp gì — thay vào đó phần đầu báo cáo
    # ghi MỘT dòng "Thư mục số liệu chi tiết" để người đọc tự mở thư mục đó.
    section_paths = result_io.write_sections(payload, out_dir)
    path = result_io.write_result(payload, result_io.result_path(out_dir, "eda"))

    versioning.record({
        "version_id": version_id,
        "dataset": ds["name"],
        "phase": "eda",
        "data_version": ds.get("version"),
        "dataset_config": utils.rel(ds["_path"]),
        "report_dir": utils.rel(out_dir),
        "records": "{} dòng (train+val+test)".format(
            sum(len(df) for df in splits.values())),
    })

    print("\nHoàn tất. Đã ghi file kết quả:")
    print("  - {}".format(utils.rel(path)))
    print("  - {} file JSON riêng cho từng phần: {}".format(
        len(section_paths),
        ", ".join(result_io.section_filename(index, section["id"])
                  for index, section in enumerate(payload["sections"], start=1))))
    print("  - Mục lục  : {}".format(utils.rel(versioning.manifest_path())))
    print("\nBước tiếp theo — vẽ báo cáo:")
    print("  python build_report.py --phase eda")


if __name__ == "__main__":
    raise SystemExit(main())
