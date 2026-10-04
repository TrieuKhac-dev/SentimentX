# -*- coding: utf-8 -*-
"""Dò ngưỡng theo khía cạnh trên tập `val` (KHÔNG chạy model).

CÁCH DÙNG
    python scripts/fit_thresholds.py --run experiments/<model>/<method>/<expNNN>/results/<hash8>
    python scripts/fit_thresholds.py --run <thư mục val> --out data/reports/fusion/thresholds.json

Đọc `predictions.csv` + `probabilities.csv` của một lượt `val` (đường encoder), dò ngưỡng cho TỪNG khía
cạnh, rồi ghi **bảng luật JSON** cho `scripts/fuse.py` và cho báo cáo. Ngưỡng chốt trên `val`; áp lên
`test` mới là số báo cáo (luật 1 của `docs/04_experiments/metrics.md`).

`price` KHÔNG có ngưỡng: `val` có 0 ô `price` âm nên không có gì để dò - tệp ghi `null` kèm lí do và
giữ lại bảng quét để làm bằng chứng (đã chốt với người dùng 04/10/2026).

Mã thoát: `0` xong, `1` không dò được (thiếu tệp/xác suất), `2` câu lệnh chưa rõ.
"""

import argparse
import datetime
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Trên Windows, console mặc định có thể không phải UTF-8 nên in tiếng Việt bị lỗi.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from src.core import utils  # noqa: E402
from src.evaluation import fusion  # noqa: E402

DEFAULT_OUT = "data/reports/fusion/thresholds.json"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Dò ngưỡng theo khía cạnh trên val (đọc predictions.csv + probabilities.csv).")
    parser.add_argument("--run", required=True,
                        help="Thư mục kết quả của lượt VAL (đường encoder, đã có probabilities.csv).")
    parser.add_argument("--out", default=DEFAULT_OUT, help="Tệp JSON để ghi bảng luật.")
    parser.add_argument("--grid", default=None,
                        help="Lưới ngưỡng, cách nhau bởi dấu phẩy (mặc định {}).".format(
                            ",".join(str(value) for value in fusion.GRID)))
    parser.add_argument("--max-cells-drop", type=float, default=fusion.MAX_CELLS_DROP,
                        help="Cho phép số ô giảm tối đa bao nhiêu phần (mặc định {}).".format(
                            fusion.MAX_CELLS_DROP))
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if not Path(args.run).is_dir():
        print("LỖI: không thấy thư mục '{}'.".format(args.run))
        return 2
    grid = None
    if args.grid:
        try:
            grid = [float(value) for value in args.grid.split(",") if value.strip()]
        except ValueError:
            print("LỖI: --grid phải là danh sách số, cách nhau bởi dấu phẩy.")
            return 2
    try:
        run = fusion.load_run(args.run, need_probabilities=True)
        rules = fusion.fit_thresholds(run, grid=grid,
                                     max_cells_drop=args.max_cells_drop,
                                     log=lambda text: print("  " + text))
    except fusion.FusionError as exc:
        print("LỖI: {}".format(exc))
        return 1
    rules["at"] = datetime.datetime.now().isoformat(timespec="seconds")
    rules["số_trên_val_gốc"] = fusion.report_of(run)
    rules["số_trên_val_sau_khi_áp_ngưỡng"] = fusion.report_of(
        run, fusion.apply_thresholds(run, rules["ngưỡng_chốt"]))
    rules["ghi_chú_đọc_số"] = ("ngưỡng dò trên {}; số báo cáo là số khi áp lên TEST, và luôn đọc kèm "
                               "số ô".format(run["split"] or "val"))
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(rules, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("Đã ghi {} ({} khía cạnh có ngưỡng).".format(
        utils.rel(path), len(rules["ngưỡng_chốt"])))
    for aspect, item in sorted(rules["khía_cạnh"].items()):
        print("  {:<14} ngưỡng={} F1 âm {} -> {}{}".format(
            aspect, item["ngưỡng"], item["f1_âm_gốc"], item["f1_âm_sau"],
            " ({})".format(item["lí do"]) if item.get("lí do") else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
