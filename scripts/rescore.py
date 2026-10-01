# -*- coding: utf-8 -*-
"""Chấm THÊM một lượt chạy từ `predictions.csv` (KHÔNG chạy model).

CÁCH DÙNG
    python scripts/rescore.py --dir experiments/<model>/<method>/<expNNN>/results/<hash8>
    python scripts/rescore.py --dir <thư mục kết quả> --reason "thêm một chỉ số mới"

Ghi `metrics_rescored.json` + `metrics_rescored.csv` vào CHÍNH thư mục đó và KHÔNG ghi đè
`metrics.json`/`metrics.csv` (số gốc vẫn là bằng chứng). Mã thoát: `0` xong, `2` câu lệnh chưa rõ,
`1` không chấm được (thiếu `predictions.csv`, ...).
"""

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Trên Windows, console mặc định có thể không phải UTF-8 nên in tiếng Việt bị lỗi.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from src.evaluation import rescore  # noqa: E402


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Chấm thêm một lượt chạy từ predictions.csv (không chạy model).")
    parser.add_argument("--dir", required=True,
                        help="Thư mục kết quả (results/<hash8>/) đang có predictions.csv.")
    parser.add_argument("--reason", default=None,
                        help="Lý do chấm lại; ghi vào khối `rescored` của file kết quả.")
    parser.add_argument("--no-confusion", action="store_true",
                        help="Không lưu ma trận nhầm trong metrics_rescored.json.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if not Path(args.dir).is_dir():
        print("LỖI: không thấy thư mục '{}'.".format(args.dir))
        return 2
    try:
        written = rescore.run(args.dir, save_confusion=not args.no_confusion, reason=args.reason)
    except rescore.RescoreError as exc:
        print("LỖI: {}".format(exc))
        return 1
    print("Đã ghi {} file (KHÔNG chạm metrics.json/metrics.csv).".format(len(written)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
