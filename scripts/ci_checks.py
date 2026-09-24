# -*- coding: utf-8 -*-
"""Sáu kiểm tra tĩnh cho CI: chạy ở máy trước khi push, và tự động trên nhánh `experiment`.

CÁCH DÙNG
    python scripts/ci_checks.py            # mã thoát 0 nếu sạch, 1 nếu còn việc phải sửa
    python scripts/ci_checks.py --quiet    # chỉ in khi có việc phải sửa

SÁU KIỂM TRA (chi tiết ở src/checks.py và docs/00_workflow/03_ci.md)
    dữ liệu bị git theo dõi, quy tắc .gitignore, notebook sạch output, registry hợp lệ,
    config thí nghiệm hợp lệ, REPO_SHA đã ghim.

KHÔNG CHẠY MODEL, KHÔNG ĐỌC DỮ LIỆU, KHÔNG GỌI MẠNG
CI không có GPU và không có dữ liệu; những thứ phụ thuộc dữ liệu (thiếu file, thiếu GPU) do
preflight trong notebook bắt lúc chạy thật. Ở đây chỉ kiểm những gì đọc được từ chính repo.
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

from src import checks, paths, utils


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Sáu kiểm tra tĩnh cho CI (không cần GPU/dữ liệu).")
    parser.add_argument("--root", default=None, help="Gốc repo cần kiểm (mặc định: gốc dự án).")
    parser.add_argument("--quiet", action="store_true", help="Chỉ in khi có việc phải sửa.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    report = checks.run(root=args.root)
    if args.quiet and not report["problems"]:
        return 0
    checks.print_report(report)
    print("\nGốc kiểm tra: {}".format(utils.rel(paths.root() if not args.root else args.root)))
    if report["problems"]:
        print("Bước tiếp: sửa từng việc ở trên rồi chạy lại lệnh này, và `pytest -q tests/`.")
        return 1
    print("Sạch. Tiếp theo: chạy `python -m unittest discover -s tests`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
