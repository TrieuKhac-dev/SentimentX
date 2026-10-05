# -*- coding: utf-8 -*-
"""Gộp NHIỀU lượt encoder bằng trung bình xác suất (ensemble). KHÔNG chạy model.

CÁCH DÙNG
    # 1) CHỐT TRỌNG SỐ trên val: ghi số của bản gộp trên val VÀ tệp trọng số để lát nữa áp lên test
    python scripts/ensemble.py --run <val A> --run <val B> --weights val \
        --out data/reports/fusion/ensemble_val.json \
        --write-weights data/reports/fusion/weights_val.json

    # 2) ÁP lên test: đọc tệp trọng số đã chốt (KHÔNG tính lại trên test)
    python scripts/ensemble.py --run <test A> --run <test B> \
        --weights-file data/reports/fusion/weights_val.json

`--weights val` tính trọng số theo macro-F1 lớp âm của CHÍNH các lượt đang xét, nên chỉ dùng được khi
các lượt đó là `val` - đưa lượt `test` vào là lỗi và công cụ sẽ chặn. Muốn chốt trên `val` rồi áp lên
`test`: bước 1 ghi `--write-weights`, bước 2 đọc `--weights-file`; tệp trọng số khoá theo TÊN MODEL nên
ráp được `.../exp003` (val) với `.../exp004` (test) của cùng một encoder.

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
                        help="Trọng số: bằng nhau (mặc định) hay theo macro-F1 lớp âm chốt trên `val`.")
    parser.add_argument("--val", action="append", default=None,
                        help="Lượt `val` để CHỐT trọng số (lặp lại). Dùng khi áp lên `test` mà muốn "
                             "trọng số lấy từ `val`: truyền cả `--weights val` và `--val ...`.")
    parser.add_argument("--weights-file", default=None,
                        help="Tệp trọng số đã chốt (do `--write-weights` ghi) để ÁP lên các lượt `--run`.")
    parser.add_argument("--write-weights", default=None,
                        help="Ghi bảng trọng số vừa chốt (khoá theo TÊN MODEL) để lát nữa áp lên tập khác.")
    parser.add_argument("--out", default=DEFAULT_OUT, help="Tệp JSON để ghi số của bản gộp.")
    parser.add_argument("--inputs-dir", default=DEFAULT_INPUTS,
                        help="Thư mục ghi đầu vào rút gọn từng lượt (chuỗi rỗng = không ghi).")
    return parser.parse_args(argv)


def check_args(args):
    """Tổ hợp cờ chưa rõ -> câu giải thích; hợp lệ -> None (test gọi thẳng được)."""
    if args.weights_file and args.weights == "val":
        return ("chọn ĐÚNG MỘT cách: `--weights val` để CHỐT trọng số theo các lượt đang xét, hoặc "
                "`--weights-file <tệp>` để ÁP bảng trọng số đã chốt trên `val`. Truyền cả hai là hai "
                "nguồn trọng số khác nhau cho cùng một lần gộp.")
    if args.weights_file and args.write_weights:
        return ("`--write-weights` chỉ dùng khi CHỐT trọng số (`--weights val`): đọc một tệp rồi ghi "
                "lại đúng nội dung đó là việc không có gì để làm.")
    if args.write_weights and args.weights != "val":
        return "`--write-weights` cần `--weights val`: nếu không chốt trọng số thì không có gì để ghi."
    if args.val and args.weights != "val":
        return "`--val` chỉ dùng cùng `--weights val` (đó là các lượt để chốt trọng số)."
    return None


def weights_of(args, runs):
    """Bảng trọng số khoá theo đường dẫn cho các lượt đang gộp, kèm bảng khoá theo model (để ghi tệp)."""
    if args.weights_file:
        table = fusion.load_weights(args.weights_file)
        return fusion.weights_for(runs, table, source=args.weights_file), None
    if args.weights == "val":
        source = args.val or [str(run["dir"]) for run in runs]
        valleys = [fusion.load_run(path, need_probabilities=True) for path in source]
        wrong = [run for run in valleys if str(run["split"]) != "val"]
        if wrong:
            raise fusion.FusionError(
                "`--weights val` chỉ chốt được trên `val`, nhưng có lượt không phải `val`: {}. Muốn áp "
                "lên tập khác thì chốt trên `val` rồi truyền `--weights-file` (xem đầu tệp).".format(
                    ", ".join("{} (split={})".format(utils.rel(run["dir"]), run["split"] or "?")
                              for run in wrong)))
        table = fusion.fit_weights_by_model(valleys)
        return fusion.weights_for(runs, table, source="chốt trên " + ", ".join(source)), table
    return {str(run["dir"]): round(1.0 / len(runs), 6) for run in runs}, None


def write_report(path, report):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main(argv=None):
    args = parse_args(argv)
    mistake = check_args(args)
    if mistake:
        print("LỖI: {}".format(mistake))
        return 2
    missing = [path for path in args.run if not Path(path).is_dir()]
    if missing:
        print("LỖI: không thấy thư mục {}.".format(", ".join(missing)))
        return 2
    try:
        runs = [fusion.load_run(path, need_probabilities=True) for path in args.run]
        weights, table = weights_of(args, runs)
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
    write_report(path, report)
    print("Đã ghi {}".format(utils.rel(path)))
    if table is not None and args.write_weights:
        document = fusion.weights_document(
            [fusion.load_run(item, need_probabilities=True) for item in (args.val or args.run)], table)
        document["at"] = datetime.datetime.now().isoformat(timespec="seconds")
        target = Path(args.write_weights)
        write_report(target, document)
        print("Đã ghi trọng số chốt trên `val`: {} (khoá theo tên model: {})".format(
            utils.rel(target), ", ".join("{}={}".format(key, value)
                                         for key, value in sorted(document["trọng_số"].items()))))
    if args.inputs_dir:
        for run in runs:
            written = fusion.dump_inputs(run, Path(args.inputs_dir) / "{}.csv".format(tag_of(run)))
            print("  đầu vào: {}".format(utils.rel(written)))
    print("  F1 âm macro (paper): {}".format(report["f1_âm_macro"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
