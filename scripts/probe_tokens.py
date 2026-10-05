# -*- coding: utf-8 -*-
"""Đo PHÂN VỊ số token SINH RA của một lượt chạy để CHỐT TRẦN token. KHÔNG chạy model.

CÁCH DÙNG
    # lượt DÒ (bật suy nghĩ, trần rộng) -> xem phân vị rồi chốt trần cho lượt thật
    python scripts/probe_tokens.py --run experiments/<model>/<method>/<expNNN>/results/<hash8>
    # kèm kiểm hai luật: cắt vì chạm trần, và trần không được vượt cửa sổ ngữ cảnh của model
    python scripts/probe_tokens.py --run <thư mục> --ceiling 8192 --context-window 32768

VÌ SAO CẦN: luật 23 của `docs/00_workflow/02_rules.md` - một lượt bật suy nghĩ phải chạy một lượt DÒ
trước rồi chốt `max_new_tokens = làm tròn lên (p99 × 1,5)`. Số đó phải ĐO từ kết quả đã có, không đoán,
và phân vị phải tính bằng đúng hàm của dự án (`utils.length_stats`) để không có định nghĩa thứ hai.

HAI ĐIỀU KIỆN ĐƯỢC KIỂM Ở ĐÂY (luật 3 của `docs/04_experiments/metrics.md` và luật 23a)
1. `--ceiling`: nếu số token sinh TRUNG BÌNH ≥ 95% trần thì lượt đó là lượt **BỊ CẮT**;
2. `--context-window`: trần đề xuất vượt cửa sổ ngữ cảnh của model là LỖI (không tự hạ xuống rồi im
   lặng chạy - lượt chạy khi đó sẽ cắt mất phần đuôi mà không ai biết).

Mã thoát: `0` xong, `1` đọc không được / trần vượt cửa sổ ngữ cảnh, `2` câu lệnh chưa rõ.
"""

import argparse
import datetime
import json
import math
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
from src.evaluation import rescore  # noqa: E402

# Tên cột do đường chạy ghi (`src/evaluation/records.py`); cố định vì đây là hợp đồng của tệp.
COLUMN = "token sinh"

# Luật 23a: trần = làm tròn LÊN (p99 × 1,5).
FACTOR = 1.5

# Luật 3 của `metrics.md`: trung bình ≥ 95% trần thì lượt chạy bị coi là BỊ CẮT.
CUT_SHARE = 0.95


class ProbeError(Exception):
    """Không đo được: thiếu `predictions.csv`, cột token không phải số, hoặc trần vượt cửa sổ."""


def read_tokens(out_dir):
    """Số token sinh của TỪNG mẫu, đọc lại `predictions.csv` (không chạy model, không chấm lại)."""
    try:
        context = rescore.settings(out_dir)
    except rescore.RescoreError as exc:
        # Giữ MỘT loại lỗi cho cả script: người chạy chỉ cần đọc một câu, không phải phân biệt hai tầng.
        raise ProbeError(str(exc)) from exc
    rows = rescore._read_predictions(context["predictions"])
    if not rows:
        raise ProbeError("{} rỗng, không có mẫu nào để đo.".format(
            utils.rel(context["predictions"])))
    tokens = []
    for position, row in enumerate(rows):
        try:
            tokens.append(int(float(row.get(COLUMN))))
        except (TypeError, ValueError):
            raise ProbeError(
                "Dòng {} của {} có cột '{}' = {!r}, không phải số. Cột này do đường chạy ghi; thiếu "
                "hoặc hỏng nghĩa là tệp không phải `predictions.csv` của dự án.".format(
                    position + 1, utils.rel(context["predictions"]), COLUMN, row.get(COLUMN)))
    return tokens, context


def ceiling_for(p99, factor=FACTOR, context_window=None):
    """Trần đề xuất = làm tròn LÊN (p99 × `factor`); vượt cửa sổ ngữ cảnh là LỖI kèm hai số."""
    value = int(math.ceil(int(p99) * float(factor)))
    if context_window and value > int(context_window):
        raise ProbeError(
            "Trần đề xuất {} token VƯỢT cửa sổ ngữ cảnh {} token của model (p99={} × {}). Hạ "
            "`--factor`, hoặc chọn model có cửa sổ lớn hơn - KHÔNG hạ trần rồi chạy im lặng: lượt đó "
            "sẽ cắt mất phần đuôi.".format(value, int(context_window), int(p99), factor))
    return value


def summarise(tokens, factor=FACTOR, ceiling=None, context_window=None):
    """Số liệu chốt trần của một lượt: phân vị, trần đề xuất, và hai điều kiện bị chặn."""
    stats = utils.length_stats(tokens, "token sinh")
    found = {
        "số mẫu": stats["số lượng"],
        "token sinh": {key: stats[key] for key in ("nhỏ nhất", "p50", "p95", "p99", "lớn nhất",
                                                   "trung bình")},
        "hệ số": float(factor),
        "trần_đề_xuất": ceiling_for(stats["p99"], factor, context_window),
        "ghi_chú": ("trần = làm tròn lên (p99 × hệ số) theo luật 23a của "
                    "docs/00_workflow/02_rules.md"),
    }
    if ceiling is not None:
        ceiling = int(ceiling)
        touched = [value for value in tokens if value >= ceiling]
        mean = float(stats["trung bình"])
        found["trần_đang_dùng"] = ceiling
        found["chạm_trần"] = {
            "số mẫu": len(touched),
            "% mẫu": round(100.0 * len(touched) / len(tokens), 2),
            "trung bình / trần": round(mean / ceiling, 4),
            "bị_cắt": mean >= CUT_SHARE * ceiling,
            "ngưỡng_bị_cắt": CUT_SHARE,
        }
    return found


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Đo phân vị số token SINH RA của một lượt chạy để chốt trần `max_new_tokens`.")
    parser.add_argument("--run", required=True,
                        help="Thư mục kết quả của lượt cần đo (phải có `predictions.csv`).")
    parser.add_argument("--ceiling", type=int, default=None,
                        help="Trần ĐANG DÙNG của lượt đó: đo xem có chạm trần không (luật 3 của "
                             "metrics.md). Bỏ trống thì không kiểm điều kiện này.")
    parser.add_argument("--context-window", type=int, default=None,
                        help="Cửa sổ ngữ cảnh của model: trần đề xuất vượt mức này là LỖI (luật 23a).")
    parser.add_argument("--factor", type=float, default=FACTOR,
                        help="Hệ số nhân vào p99 (mặc định {} - luật 23a).".format(FACTOR))
    parser.add_argument("--out", default=None,
                        help="Tệp JSON để ghi số liệu (bỏ trống = chỉ in ra màn hình).")
    return parser.parse_args(argv)


def check_args(args):
    """Tổ hợp cờ chưa rõ -> câu giải thích; hợp lệ -> None (test gọi thẳng được)."""
    if args.factor <= 0:
        return "`--factor` phải lớn hơn 0 (hệ số nhân vào p99 để ra trần)."
    if args.ceiling is not None and args.ceiling <= 0:
        return "`--ceiling` phải lớn hơn 0."
    if args.context_window is not None and args.context_window <= 0:
        return "`--context-window` phải lớn hơn 0."
    return None


def write_report(path, report):
    path = Path(path)
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
    if not Path(args.run).is_dir():
        print("LỖI: không thấy thư mục '{}'.".format(args.run))
        return 2
    try:
        tokens, context = read_tokens(args.run)
        report = summarise(tokens, factor=args.factor, ceiling=args.ceiling,
                           context_window=args.context_window)
    except ProbeError as exc:
        print("LỖI: {}".format(exc))
        return 1
    metrics = context.get("metrics") or {}
    report["lượt"] = utils.rel(Path(args.run))
    report["split"] = str(metrics.get("split") or "")
    read_rate = metrics.get("read_rate") or {}
    report["% đọc được"] = read_rate.get("% đọc được")
    report["at"] = datetime.datetime.now().isoformat(timespec="seconds")

    print("Lượt        : {}".format(report["lượt"]))
    print("Split       : {}".format(report["split"] or "?"))
    if report["% đọc được"] is not None:
        print("% đọc được  : {}".format(report["% đọc được"]))
    print("Số mẫu      : {}".format(report["số mẫu"]))
    print("Token sinh  : p50={p50} p95={p95} p99={p99} max={lớn nhất} TB={trung bình}".format(
        **report["token sinh"]))
    print("Trần đề xuất: {} token = làm tròn lên (p99 × {})".format(
        report["trần_đề_xuất"], report["hệ số"]))
    if "chạm_trần" in report:
        touched = report["chạm_trần"]
        print("Trần đang dùng {}: {} mẫu chạm trần ({}%); trung bình/trần = {}{}".format(
            report["trần_đang_dùng"], touched["số mẫu"], touched["% mẫu"],
            touched["trung bình / trần"],
            " -> BỊ CẮT (luật 3 của metrics.md)" if touched["bị_cắt"] else " -> không bị cắt"))
    if args.out:
        write_report(args.out, report)
        print("Đã ghi {}".format(utils.rel(Path(args.out))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
