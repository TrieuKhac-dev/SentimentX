# -*- coding: utf-8 -*-
"""Bỏ phiếu TỪNG Ô trên nhiều lượt lấy mẫu (self-consistency). KHÔNG chạy model.

CÁCH DÙNG
    python scripts/vote.py --run <seed1> --run <seed2> --run <seed3> \
        --out data/reports/fusion/vote.json

Luật đã chốt (`present_plan.md` mục 4.9, `docs/04_experiments/metrics.md` luật 6):
- **ba mẫu** cho đợt này (ba `seed`);
- ô chỉ được bỏ phiếu nếu ĐỌC ĐƯỢC ở ít nhất một lượt; ô không lượt nào đọc được thì không có phiếu;
- **hoà thì lấy nhãn của lượt ĐẦU TIÊN**, nên phải truyền các lượt theo thứ tự `seed` TĂNG DẦN.

Số của từng lượt lẻ cũng được ghi vào JSON (để đo dao động giữa các seed), và bản bỏ phiếu được ghi
kèm nhãn từng ô vào thư mục đầu vào rút gọn.

Mã thoát: `0` xong, `1` không bỏ phiếu được, `2` câu lệnh chưa rõ.
"""

import argparse
import csv
import datetime
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from src.core import paths, utils  # noqa: E402
from src.evaluation import fusion  # noqa: E402

# Thư mục bảng KẾT HỢP đọc từ `configs/paths.yaml` (nhóm report `fusion`) - KHÔNG viết cứng đường dẫn.
FUSION_DIR = paths.report("fusion")
DEFAULT_OUT = str(FUSION_DIR / "vote.json")
DEFAULT_INPUTS = str(FUSION_DIR / "inputs")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Bỏ phiếu từng ô trên các lượt lấy mẫu.")
    parser.add_argument("--run", action="append", required=True,
                        help="Thư mục kết quả của một mẫu; truyền theo thứ tự seed TĂNG DẦN.")
    parser.add_argument("--out", default=DEFAULT_OUT, help="Tệp JSON để ghi.")
    parser.add_argument("--inputs-dir", default=DEFAULT_INPUTS,
                        help="Thư mục ghi nhãn từng ô của bản bỏ phiếu (chuỗi rỗng = không ghi).")
    parser.add_argument("--tag", default="vote", help="Tiền tố tên tệp trong thư mục đầu vào.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    missing = [path for path in args.run if not Path(path).is_dir()]
    if missing:
        print("LỖI: không thấy thư mục {}.".format(", ".join(missing)))
        return 2
    try:
        runs = [fusion.load_run(path) for path in args.run]
        preds, counts = fusion.vote(runs)
    except fusion.FusionError as exc:
        print("LỖI: {}".format(exc))
        return 1
    report = fusion.report_of(runs[0], preds, {
        "at": datetime.datetime.now().isoformat(timespec="seconds"),
        "cách": "bỏ phiếu từng ô; hoà -> nhãn của lượt đầu tiên (seed nhỏ nhất)",
        "thống kê phiếu": counts,
        "nguồn": [utils.rel(run["dir"]) for run in runs],
        "số của từng mẫu": [fusion.report_of(run, None) for run in runs],
        "ghi_chú": ("ba mẫu cho đợt này; so từng mẫu với bản bỏ phiếu để biết bỏ phiếu có ích không, "
                    "và đọc kèm số ô + số ô hoà"),
    })
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("Đã ghi {}".format(utils.rel(path)))
    if args.inputs_dir:
        out = Path(args.inputs_dir) / "{}__nhan_tung_o.csv".format(args.tag)
        columns = ["chỉ số", "split", "khía cạnh", "nhãn đúng", "nhãn đoán bỏ phiếu"]
        rows = []
        for position, sample_id in enumerate(runs[0]["sample_ids"]):
            for aspect in runs[0]["aspects"]:
                rows.append([sample_id, runs[0]["split"], aspect,
                             (runs[0]["golds"][position] or {}).get(aspect),
                             (preds[position] or {}).get(aspect)])
        utils.write_csv(rows, columns, out)
        print("  nhãn từng ô: {}".format(utils.rel(out)))
    print("  F1 âm macro (paper): {}".format(report["f1_âm_macro"]))
    print("  thống kê phiếu: {}".format(counts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
