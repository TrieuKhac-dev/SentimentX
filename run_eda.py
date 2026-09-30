# -*- coding: utf-8 -*-
"""Chạy toàn bộ EDA và GHI FILE KẾT QUẢ (không vẽ báo cáo).

Cách dùng - BẮT BUỘC chọn đúng MỘT nơi đo:

    # Đo dữ liệu GỐC: cần tên dataset + nhãn raw_version
    python run_eda.py --on raw --name cosmetics --version v0.1.0

    # Đo dataset ĐÃ XỬ LÝ: cần phiên bản dữ liệu (hash8 hoặc mã đầy đủ)
    python run_eda.py --on dataset --hash e0ccc484
    python run_eda.py --on dataset --hash cosmetics-ds0.1.0-pl0.1.0-srccosmetics@0.1.0-e0ccc484

Kết quả ghi NGAY CẠNH thứ được đo:
data/raw/<tên>/<raw_version>/eda/    khi --on raw
data/processed/<mã>/eda/             khi --on dataset
gồm: eda_result.json (đủ mọi phần - file build_report.py đọc lại), 0X_<mục>.json (riêng từng phần), 0X_<mục>_*.csv (bảng số liệu chi tiết).

Vì sao không có mặc định: để tool tự chọn "bản mới nhất" là ĐOÁN - khi có phiên bản thứ hai thì số
liệu rơi vào thư mục của một bản khác mà nhìn vào vẫn hợp lý. Xem docs/00_workflow/09_cli.md.

Bước này KHÔNG sinh HTML. Muốn xem báo cáo, chạy tiếp:
    python build_report.py --phase eda --on raw --name <tên> --version <nhãn raw>
    python build_report.py --phase eda --on dataset --hash <hash8|mã>
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
from src.preprocessing import loader
from src.reporting import result as result_io

# Thư mục cấu hình dataset, dựng từ `configs/paths.yaml` (không viết cứng trong chuỗi help:
# `tests/test_paths.py` chặn đường dẫn viết cứng trong source).
DATASET_CONFIG_DIR = utils.rel(paths.config_path("datasets"))


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Khảo sát dữ liệu (EDA) và ghi file kết quả.",
        epilog="Cú pháp đầy đủ: docs/00_workflow/09_cli.md",
    )
    parser.add_argument(
        "--on", dest="where", choices=("raw", "dataset"), default=None,
        help="Nơi đo: raw = dữ liệu gốc (data/raw/<tên>/<nhãn>/) hoặc "
             "dataset = dataset đã xử lý (data/processed/<mã>/). Bắt buộc.",
    )
    parser.add_argument(
        "--name", default=None,
        help="Tên dataset = thư mục {}/<tên>/. Bắt buộc khi --on raw "
             "(khi --on dataset thì suy ra từ mã, ghi thêm chỉ để đối chiếu).".format(
                 DATASET_CONFIG_DIR),
    )
    parser.add_argument(
        "--version", default=None,
        help="Nhãn phiên bản của dữ liệu GỐC: data/raw/<tên>/<nhãn>/. Bắt buộc khi --on raw. "
             "KHÔNG phải mã phiên bản dữ liệu đã xử lý.",
    )
    parser.add_argument(
        "--hash", default=None,
        help="Phiên bản dữ liệu ĐÃ XỬ LÝ: 8 ký tự hex cuối mã (ví dụ e0ccc484) hoặc mã đầy đủ "
             "(ví dụ cosmetics-ds0.1.0-pl0.1.0-srccosmetics@0.1.0-e0ccc484). Bắt buộc khi "
             "--on dataset.",
    )
    return parser.parse_args(argv)


def check_args(args):
    """Kiểm tham số trước khi chạy; trả về câu lỗi, hoặc None nếu hợp lệ.

    Tách riêng để test được mà không phải chạy EDA. Mọi dạng thiếu/thừa/nhầm đều có gợi ý cụ thể:
    nhầm mã phiên bản dữ liệu với nhãn raw_version là lỗi hay gặp nhất.
    """
    if not args.where:
        return ("thiếu `--on`: chọn đúng một nơi đo.\n"
                "      Đo dữ liệu GỐC : python run_eda.py --on raw --name <tên> --version <nhãn raw>\n"
                "      Đo dataset     : python run_eda.py --on dataset --hash <hash8|mã đầy đủ>")
    if args.where == "raw":
        if args.hash:
            return ("`--hash` là của dataset đã xử lý; đo dữ liệu gốc dùng `--name` + `--version`.")
        if not args.name or not args.version:
            return ("`--on raw` cần đủ `--name` và `--version` (nhãn raw_version).\n"
                    "      Ví dụ: python run_eda.py --on raw --name cosmetics --version v0.1.0")
        if "-ds" in str(args.version):
            return ("{!r} là MÃ PHIÊN BẢN của dữ liệu đã xử lý, không phải nhãn raw_version.\n"
                    "      Muốn đo dataset: python run_eda.py --on dataset --hash {}".format(
                        args.version, args.version))
        return None
    if args.version:
        return ("`--on dataset` không dùng `--version` (đó là nhãn raw_version của dữ liệu gốc).\n"
                "      Dùng: python run_eda.py --on dataset --hash <hash8|mã đầy đủ>")
    if not args.hash:
        return ("`--on dataset` cần `--hash` để chỉ đích danh phiên bản dữ liệu.\n"
                "      Ví dụ: python run_eda.py --on dataset --hash e0ccc484")
    return None


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

    # Gõ sai tham số là lỗi hay gặp nhất khi mới dùng: in một dòng lỗi gọn kèm cách sửa,
    # thay vì để traceback che mất thông báo.
    mistake = check_args(args)
    if mistake:
        print("LỖI: {}".format(mistake))
        return 2

    try:
        if args.where == "dataset":
            version_id = versioning.find_version(args.hash)
            name, _ = versioning.version_parts(version_id)
            if args.name and args.name != name:
                print("LỖI: `--name {}` không khớp mã {} (tên dataset trong mã là {}).".format(
                    args.name, version_id, name))
                return 2
            ds, splits, full, missing = load_processed(name, version_id)
            out_dir = versioning.processed_dir(version_id) / paths.pattern("eda_dir")
            where = "dataset đã xử lý"
        else:
            ds, splits, full, missing = load_raw(args.name, args.version)
            pipeline_cfg = utils.load_pipeline_config(ds.get("pipeline_version"))
            versioning.guard_versions(ds, pipeline_cfg)
            version_id = versioning.compute_id(ds, pipeline_cfg)
            out_dir = ds["_raw_dir"] / paths.pattern("eda_dir")
            where = "dữ liệu gốc"
    except (dataset.DatasetError, versioning.VersionError) as exc:
        print("LỖI: {}".format(exc))
        return 2

    # In ĐÍCH đã chốt trước khi đo: nhầm phiên bản là lỗi im lặng đắt nhất của EDA.
    _, hash8 = versioning.version_parts(version_id)
    print("Dataset: {} (cấu hình: {})".format(ds["name"], utils.rel(ds["_path"])))
    print("Đang đọc {} từ: {}".format(where, utils.rel(ds["_raw_dir"])))
    print("Phiên bản dữ liệu: {} (hash8 {})".format(version_id, hash8))
    print("Thư mục kết quả: {}".format(utils.rel(out_dir)))

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
    if args.where == "dataset":
        print("  python build_report.py --phase eda --on dataset --hash {}".format(hash8))
    else:
        print("  python build_report.py --phase eda --on raw --name {} --version {}".format(
            ds["name"], args.version))


if __name__ == "__main__":
    raise SystemExit(main())
