# -*- coding: utf-8 -*-
"""Sinh BỐN NHÓM bảng tổng hợp từ các lượt chạy đã có trên đĩa.

CÁCH DÙNG
    python scripts/collect_reports.py                        # quét gốc mặc định, ghi vào nhóm report
    python scripts/collect_reports.py --root <thư mục>       # thêm gốc khác (lặp lại được)
    python scripts/collect_reports.py --group metrics_matrix  # chỉ một nhóm
    python scripts/collect_reports.py --out-root <thư mục>    # ghi ra chỗ khác (Colab: Drive)
    python scripts/collect_reports.py --dry-run              # chỉ in ra, không ghi

CÔNG CỤ NÀY KHÔNG CHẠY MODEL VÀ KHÔNG ĐỌC DỮ LIỆU GỐC
Nó chỉ đọc lại file mà từng lượt chạy đã ghi (`run_meta.json`, `metrics.json`, `metrics.csv`,
`model_input.csv`). Nhờ vậy bảng tổng hợp luôn nói đúng con số đã đo - không có đường tính thứ hai -
và sinh lại được ở bất cứ máy nào đang có kết quả, kể cả máy không có GPU.

MỘT NHÓM GỒM BA ĐỊNH DẠNG: `<tên>.csv` (nguồn), `<tên>.html` (trình bày), `<tên>.md` (chỉ sơ đồ
Mermaid). Chi tiết ở `src/reports.py`; bốn nhóm khai trong `configs/paths.yaml`.
"""

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Trên Windows, console mặc định có thể không phải UTF-8 (ví dụ cp1252),
# khiến việc in tiếng Việt bị lỗi. Ép stdout/stderr sang UTF-8.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from src import reports, utils


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Sinh bảng tổng hợp (dataset_registry, experiment_registry, model_input, "
                    "metrics_matrix) từ kết quả đã có.")
    parser.add_argument("--root", action="append", default=None,
                        help="Gốc chứa lượt chạy; lặp lại để quét nhiều gốc "
                             "(mặc định: gốc kết quả + thư mục đánh giá chạy tay).")
    parser.add_argument("--group", action="append", default=None, choices=list(reports.GROUPS),
                        help="Chỉ sinh nhóm này; lặp lại để chọn nhiều nhóm.")
    parser.add_argument("--out-root", dest="out_root", default=None,
                        help="Ghi vào <thư mục>/<tên nhóm> thay vì nhóm report trong paths.yaml.")
    parser.add_argument("--reference-shot", dest="reference_shot", type=int, default=0,
                        choices=[0, 1, 5],
                        help="Cột nào của bảng công bố dùng làm cột đối chiếu (mặc định 0).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Chỉ in ra sẽ sinh gì, không ghi file.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    roots = [Path(item) for item in (args.root or [])] or None
    runs = reports.scan_runs(roots)

    if args.dry_run:
        used = roots or reports.default_roots()
        print("Gốc quét  : {}".format(", ".join(utils.rel(path) for path in used)))
        print("Lượt chạy : {}".format(len(runs)))
        for run in runs:
            print("  - {:<70} {}".format(
                reports.canonical_label(run),
                (run["meta"].get("run") or {}).get("status")))
        reference = reports.load_reference(shot=args.reference_shot)
        print("Bảng công bố: {}".format(
            "có, cột `{}`".format(reference[2]) if any(reference)
            else "chưa có, không có cột đối chiếu"))
        for name in (args.group or reports.GROUPS):
            tables, mermaid = reports.group_tables(name, runs, reference)
            counts = ", ".join("{}={}".format(file_name, len(rows))
                               for file_name, (_columns, rows) in tables.items())
            print("  {:<20} {:<44} sơ đồ {} dòng".format(name, counts,
                                                         len(mermaid.splitlines())))
        print("\n--dry-run nên chưa ghi gì.")
        return 0

    result = reports.build(roots=roots, out_root=args.out_root, groups=args.group,
                           reference=reports.load_reference(shot=args.reference_shot))
    for name, item in result.items():
        print("{:<20} {} dòng".format(name, item["rows"]))
        for file_name, path in item["csv"].items():
            print("    csv : {}".format(utils.rel(path)))
        print("    html: {}".format(utils.rel(item["html"])))
        print("    md  : {}".format(utils.rel(item["md"])))
    if not result:
        print("Không sinh nhóm nào (xem --group).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
