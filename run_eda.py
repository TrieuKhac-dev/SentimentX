# -*- coding: utf-8 -*-
"""Chạy toàn bộ EDA và GHI FILE KẾT QUẢ (không vẽ báo cáo).

Cách dùng:
    python run_eda.py
    python run_eda.py --dataset cosmetics

Kết quả (trong thư mục theo phiên bản: data/reports/eda/versions/<mã>/):
    <mã>/eda_result.json   (đủ mọi phần - file build_report.py đọc lại)
    <mã>/01_*.json ...       (file kết quả riêng của từng phần)
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

from src import config, dataset, paths, registry, utils, versioning
from src.preprocessing import loader
from src.reporting import result as result_io


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Khảo sát dữ liệu (EDA) và ghi file kết quả."
    )
    parser.add_argument(
        "--dataset", default=None,
        help="Tên dataset (mặc định: dataset đầu tiên trong configs/datasets/).",
    )
    parser.add_argument(
        "--raw-version", default=None,
        help="Đo trên dữ liệu gốc: data/raw/<tên>/<phiên bản>/. Bắt buộc ghi rõ một trong "
             "hai nơi đo, vì kết quả nằm cạnh thứ được đo.",
    )
    parser.add_argument(
        "--version", default=None,
        help="Đo trên dataset đã xử lý: data/processed/<mã>/.",
    )
    return parser.parse_args(argv)


def load_raw(name, raw_version):
    """Đọc dữ liệu gốc của một phiên bản raw cụ thể.

    Phiên bản khai trong file dataset là bản MẶC ĐỊNH; hàm này cho đo một phiên bản gốc khác
    mà không phải sửa file cấu hình, để so được hai bản dữ liệu gốc.
    """
    directory = paths.raw_dir(name, raw_version)
    if not directory.is_dir():
        siblings = sorted(path.name for path in directory.parent.iterdir()) \
            if directory.parent.is_dir() else []
        raise dataset.DatasetError(
            "Không có dữ liệu gốc ở {}. Các phiên bản hiện có: {}.".format(
                utils.rel(directory), ", ".join(siblings) or "(chưa có)"))
    cfg = dataset.load_config(name)
    cfg["raw_version"] = raw_version
    cfg["_raw_dir"] = directory
    cfg["_sources"] = [{"kind": "raw", "name": cfg["name"], "version": raw_version,
                        "dir": directory}]
    splits, missing = dataset.load_splits(cfg)
    full, _ = dataset.load_full(cfg)
    return cfg, splits, full, missing


def load_processed(name, version_id):
    """Đọc dataset đã xử lý, đổi mã nhãn về nhãn chữ để EDA đọc được như dữ liệu gốc."""
    directory = versioning.processed_dir(version_id)
    if not directory.is_dir():
        raise dataset.DatasetError(
            "Chưa có dataset ở {}. Hãy chạy run_pipeline.py trước.".format(
                utils.rel(directory)))
    label_map = loader.load_label_map(version_id)
    id_to_label = {int(code): label for code, label in label_map["id_to_label"].items()}
    aspects = list(label_map["aspects"])
    splits = {}
    for split in ("train", "val", "test"):
        frame = loader.load_processed(split, version_id=version_id)
        for aspect in aspects:
            frame[aspect] = frame[aspect].map(lambda code: id_to_label.get(int(code), ""))
        splits[split] = frame[[config.TEXT_COLUMN] + aspects]

    # Dùng cấu hình dataset thật để có đủ schema cho các module EDA, chỉ đổi chỗ đọc file: ba
    # split nằm trong thư mục dataset chứ không nằm trong thư mục dữ liệu gốc.
    log = versioning.read_processing_log(version_id)
    config_version = (log.get("dataset") or {}).get("version")
    cfg = dataset.load_config(name, config_version)
    cfg["pipeline_version"] = ((log.get("pipeline") or {}).get("version")
                               or cfg.get("pipeline_version"))
    cfg["_path"] = versioning.processing_log_path(version_id)
    cfg["_raw_dir"] = directory
    cfg["_sources"] = []
    cfg["splits"] = {split: "{}.csv".format(split) for split in ("train", "val", "test")}
    cfg["full"] = None
    return cfg, splits, None, {}


def main(argv=None):
    args = parse_args(argv)

    print("EDA - Khảo sát dữ liệu (chỉ đo lường, KHÔNG sửa dữ liệu)")

    # Gõ sai tên dataset là lỗi hay gặp nhất khi mới dùng: in một dòng lỗi gọn
    # (kèm gợi ý tên đúng) thay vì để traceback che mất thông báo.
    if bool(args.raw_version) == bool(args.version):
        print("LỖI: chọn đúng MỘT nơi đo: --raw-version <phiên bản> (đo dữ liệu gốc) "
              "hoặc --version <mã> (đo dataset đã xử lý).")
        return 2

    try:
        if args.version:
            ds, splits, full, missing = load_processed(args.dataset, args.version)
            version_id = args.version
            out_dir = versioning.processed_dir(version_id) / paths.pattern("eda_dir")
            where = "dataset đã xử lý"
        else:
            name = args.dataset or dataset.default_name()
            ds, splits, full, missing = load_raw(name, args.raw_version)
            pipeline_cfg = utils.load_pipeline_config(ds.get("pipeline_version"))
            versioning.guard_versions(ds, pipeline_cfg)
            version_id = versioning.compute_id(ds, pipeline_cfg)
            out_dir = ds["_raw_dir"] / paths.pattern("eda_dir")
            where = "dữ liệu gốc"
    except (dataset.DatasetError, versioning.VersionError) as exc:
        print("LỖI: {}".format(exc))
        return 2

    print("Dataset: {} (cấu hình: {})".format(ds["name"], utils.rel(ds["_path"])))
    print("Đang đọc {} từ: {}".format(where, utils.rel(ds["_raw_dir"])))
    print("Mã phiên bản: {}".format(version_id))

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
        title="Báo cáo EDA - ABSA tiếng Việt",
        subtitle="Khảo sát dữ liệu của dataset '{}'".format(ds["name"]),
    )

    # Mỗi mục được ghi thêm một file JSON riêng (0X_<mục>.json) trong cùng thư
    # mục phiên bản. Báo cáo KHÔNG liệt kê từng file nữa: mục nào cũng có nhiều
    # file nên danh sách rất dài mà không giúp gì - thay vào đó phần đầu báo cáo
    # ghi MỘT dòng "Thư mục số liệu chi tiết" để người đọc tự mở thư mục đó.
    section_paths = result_io.write_sections(payload, out_dir)
    path = result_io.write_result(payload, result_io.result_path(out_dir, "eda"))

    print("\nHoàn tất. Đã ghi file kết quả:")
    print("  - {}".format(utils.rel(path)))
    print("  - {} file JSON riêng cho từng phần: {}".format(
        len(section_paths),
        ", ".join(result_io.section_filename(index, section["id"])
                  for index, section in enumerate(payload["sections"], start=1))))
    print("  - Thư mục : {}".format(utils.rel(out_dir)))
    print("\nBước tiếp theo - vẽ báo cáo:")
    print("  python build_report.py --phase eda")


if __name__ == "__main__":
    raise SystemExit(main())
