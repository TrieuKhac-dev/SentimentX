# -*- coding: utf-8 -*-
"""Gộp NHIỀU lượt encoder bằng trung bình xác suất (ensemble). KHÔNG chạy model.

CÁCH DÙNG
    python scripts/ensemble.py --run <val A> --run <val B> [--weights val]
    python scripts/ensemble.py --run <test A> --run <test B> --out data/reports/fusion/ensemble_test.json

`--weights val`: trọng số theo macro-F1 lớp âm trên `val` của từng lượt, chuẩn hoá tổng = 1; không có cờ
này thì trọng số bằng nhau. Mọi lượt phải chấm CÙNG split (lượt đầu là lượt giữ khung ô).

Ghi hai thứ: (a) JSON số của bản gộp (hai cơ sở, số ô, F1 âm từng khía cạnh); (b) **đầu vào rút gọn** của
từng lượt vào `data/reports/fusion/inputs/` để con số gộp tái lập được TỪ REPO (lượt chạy thật nằm trên
Drive). Xem `docs/04_experiments/09_fusion.md`.

Mã thoát: `0` xong, `1` không gộp được (thiếu xác suất), `2` câu lệnh chưa rõ.
"""

import argparse
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

from src.core import utils  # noqa: E402
from src.evaluation import fusion  # noqa: E402

DEFAULT_OUT = "data/reports/fusion/ensemble.json"
DEFAULT_INPUTS = "data/reports/fusion/inputs"


def tag_of(run):
    """Tên ngắn của một lượt để đặt tên tệp đầu vào: `<model>_<method>_<expNNN>_<hash8>`."""
    parts = list(run["dir"].parts)
    try:
        index = parts.index("experiments")
        model, method, exp_id = parts[index + 1], parts[index + 2], parts[index + 3]
        return "{}_{}_{}_{}".format(model, method, exp_id, run["dir"].name)
    except (ValueError, IndexError):
        return "{}__{}".format(run["split"] or "run", run["dir"].name)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Gộp nhiều lượt encoder bằng trung bình xác suất.")
    parser.add_argument("--run", action="append", required=True,
                        help="Thư mục kết quả (lặp lại cho từng lượt); lượt ĐẦU giữ khung ô.")
    parser.add_argument("--weights", choices=("equal", "val"), default="equal",
                        help="Trọng số: bằng nhau (mặc định) hay theo macro-F1 lớp âm trên val.")
    parser.add_argument("--out", default=DEFAULT_OUT, help="Tệp JSON để ghi số của bản gộp.")
    parser.add_argument("--inputs-dir", default=DEFAULT_INPUTS,
                        help="Thư mục ghi đầu vào rút gọn từng lượt (chuỗi rỗng = không ghi).")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    missing = [path for path in args.run if not Path(path).is_dir()]
    if missing:
        print("LỖI: không thấy thư mục {}.".format(", ".join(missing)))
        return 2
    try:
        runs = [fusion.load_run(path, need_probabilities=True) for path in args.run]
        weights = fusion.fit_ensemble_weights(runs) if args.weights == "val" else \
            {str(run["dir"]): round(1.0 / len(runs), 6) for run in runs}
        preds = fusion.ensemble_predictions(runs[0], runs, weights=weights)
    except fusion.FusionError as exc:
        print("LỖI: {}".format(exc))
        return 1
    report = fusion.report_of(runs[0], preds, {
        "at": datetime.datetime.now().isoformat(timespec="seconds"),
        "cách": "trung bình xác suất rồi argmax theo từng khía cạnh",
        "trọng số": weights,
        "nguồn": [utils.rel(run["dir"]) for run in runs],
        "ghi_chú": "mọi lượt phải chấm CÙNG split; số ô đọc kèm theo luật 1 của metrics.md",
    })
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("Đã ghi {}".format(utils.rel(path)))
    if args.inputs_dir:
        for run in runs:
            written = fusion.dump_inputs(run, Path(args.inputs_dir) / "{}.csv".format(tag_of(run)))
            print("  đầu vào: {}".format(utils.rel(written)))
    print("  F1 âm macro (paper): {}".format(report["f1_âm_macro"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
