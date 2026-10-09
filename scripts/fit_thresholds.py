# -*- coding: utf-8 -*-
"""Dò ngưỡng theo khía cạnh trên `val`, VÀ áp bảng ngưỡng đã chốt lên một lượt khác (KHÔNG chạy model).

CÁCH DÙNG
    # 1) DÒ: chốt ngưỡng trên một lượt VAL (đường encoder), ghi tệp luật đóng băng
    python scripts/fit_thresholds.py --run experiments/<model>/<method>/<expNNN>/results/<hash8>
    python scripts/fit_thresholds.py --run <thư mục val> --out data/reports/fusion/thresholds.json

    # 2) ÁP: đọc tệp luật ĐÃ CHỐT rồi áp lên một lượt khác - thường là TEST - để ra số báo cáo
    python scripts/fit_thresholds.py --apply-to experiments/<model>/<method>/<expNNN>/results/<hash8>

HAI CHẾ ĐỘ, VÌ SAO KHÔNG GỘP
Luật 1 của `docs/04_experiments/metrics.md`: ngưỡng chốt trên `val` rồi mới áp lên `test`. Chế độ 1 chỉ
so được trên CHÍNH lượt nó đọc, nên phải có chế độ 2 để ráp: đọc tệp luật đã ghi -> áp -> chấm. Số báo
cáo là số của chế độ 2. Trộn hai việc vào một lệnh là mở đường cho việc "xem `test` rồi mới chọn ngưỡng".

Chế độ 1 đọc `predictions.csv` + `probabilities.csv` của một lượt `val` (đường encoder), dò ngưỡng cho
TỪNG khía cạnh, rồi ghi **bảng luật JSON** (mặc định `data/reports/fusion/thresholds.json`). Chế độ 2 ghi
số trước/sau khi áp (mặc định `data/reports/fusion/thresholds_applied.json`): hai cơ sở, số ô, F1 âm
từng khía cạnh, macro hai cách.

`price` KHÔNG có ngưỡng: `val` có 0 ô `price` âm nên không có gì để dò - tệp ghi `null` kèm lí do, giữ
lại bảng quét để làm bằng chứng, và các ô `price` giữ nguyên quyết định của model (đã chốt với người
dùng 04/10/2026). Chế độ 2 in rõ khía cạnh nào để nguyên vì lí do đó.

Mã thoát: `0` xong, `1` không làm được (thiếu tệp/xác suất/luật), `2` câu lệnh chưa rõ.
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

from src.core import paths, utils  # noqa: E402
from src.evaluation import fusion  # noqa: E402

# Thư mục bảng KẾT HỢP đọc từ `configs/paths.yaml` (nhóm report `fusion`) - KHÔNG viết cứng đường dẫn.
FUSION_DIR = paths.report("fusion")
DEFAULT_OUT = str(FUSION_DIR / "thresholds.json")
DEFAULT_APPLIED = str(FUSION_DIR / "thresholds_applied.json")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Dò ngưỡng theo khía cạnh trên val, hoặc áp bảng ngưỡng đã chốt lên một lượt khác.")
    parser.add_argument("--run", help="CHẾ ĐỘ DÒ: thư mục kết quả của lượt VAL (đường encoder, đã có "
                                      "probabilities.csv).")
    parser.add_argument("--apply-to", help="CHẾ ĐỘ ÁP: thư mục kết quả của lượt cần áp bảng ngưỡng đã "
                                           "chốt (thường là TEST).")
    parser.add_argument("--thresholds", default=DEFAULT_OUT,
                        help="Tệp luật đã chốt để áp (mặc định {}).".format(DEFAULT_OUT))
    parser.add_argument("--out", default=None,
                        help="Tệp JSON để ghi (mặc định: {} khi DÒ, {} khi ÁP).".format(
                            DEFAULT_OUT, DEFAULT_APPLIED))
    parser.add_argument("--grid", default=None,
                        help="Khi DÒ: lưới ngưỡng, cách nhau bởi dấu phẩy (mặc định {}).".format(
                            ",".join(str(value) for value in fusion.GRID)))
    parser.add_argument("--max-cells-drop", type=float, default=None,
                        help="Khi DÒ: cho phép số ô giảm tối đa bao nhiêu phần (mặc định {}).".format(
                            fusion.MAX_CELLS_DROP))
    return parser.parse_args(argv)


def check_args(args):
    """Tổ hợp cờ chưa rõ -> câu giải thích; hợp lệ -> None.

    Trả về CHUỖI (không tự in, không tự thoát) để `tests/workflow/test_cli.py` kiểm được mà không phải
    dựng lượt chạy thật.
    """
    if bool(args.run) == bool(args.apply_to):
        return ("chọn ĐÚNG MỘT trong hai chế độ: `--run <thư mục val>` để DÒ ngưỡng, hoặc "
                "`--apply-to <thư mục cần áp>` để ÁP bảng ngưỡng đã chốt.")
    if args.apply_to and (args.grid is not None or args.max_cells_drop is not None):
        return ("`--grid` và `--max-cells-drop` chỉ dùng ở chế độ DÒ (`--run`): chúng quyết định bảng "
                "ngưỡng sinh ra, còn `--apply-to` chỉ đọc bảng đã đóng băng.")
    return None


def grid_of(value):
    """Lưới ngưỡng từ chuỗi `0.1,0.2`; `None` khi không truyền (dùng lưới mặc định của `fusion`)."""
    if not value:
        return None
    return [float(item) for item in value.split(",") if item.strip()]


def decide(args):
    """CHẾ ĐỘ DÒ: chốt ngưỡng trên một lượt `val`, ghi tệp luật đóng băng. Trả mã thoát."""
    if not Path(args.run).is_dir():
        print("LỖI: không thấy thư mục '{}'.".format(args.run))
        return 2
    try:
        grid = grid_of(args.grid)
    except ValueError:
        print("LỖI: --grid phải là danh sách số, cách nhau bởi dấu phẩy.")
        return 2
    try:
        run = fusion.load_run(args.run, need_probabilities=True)
        rules = fusion.fit_thresholds(
            run, grid=grid,
            max_cells_drop=(fusion.MAX_CELLS_DROP if args.max_cells_drop is None
                            else args.max_cells_drop),
            log=lambda text: print("  " + text))
    except fusion.FusionError as exc:
        print("LỖI: {}".format(exc))
        return 1
    rules["at"] = datetime.datetime.now().isoformat(timespec="seconds")
    rules["số_trên_val_gốc"] = fusion.report_of(run)
    rules["số_trên_val_sau_khi_áp_ngưỡng"] = fusion.report_of(
        run, fusion.apply_thresholds(run, rules["ngưỡng_chốt"]))
    rules["ghi_chú_đọc_số"] = ("ngưỡng dò trên {}; số báo cáo là số khi áp lên TEST "
                               "(`fit_thresholds.py --apply-to <thư mục test>`), và luôn đọc kèm số ô."
                               .format(run["split"] or "val"))
    path = Path(args.out or DEFAULT_OUT)
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


def apply_frozen(args):
    """CHẾ ĐỘ ÁP: áp tệp luật đã chốt lên lượt `--apply-to`, ghi số trước/sau. Trả mã thoát."""
    if not Path(args.apply_to).is_dir():
        print("LỖI: không thấy thư mục '{}'.".format(args.apply_to))
        return 2
    path = Path(args.thresholds)
    if not path.is_file():
        print("LỖI: chưa có bảng ngưỡng '{}' - chạy chế độ DÒ trước (`--run <thư mục val>`).".format(
            utils.rel(path)))
        return 1
    try:
        with open(path, "r", encoding="utf-8") as handle:
            rules = json.load(handle) or {}
    except (OSError, ValueError) as exc:
        print("LỖI: không đọc được '{}': {}".format(utils.rel(path), exc))
        return 1
    if not rules.get("ngưỡng_chốt"):
        print("LỖI: '{}' không có khoá `ngưỡng_chốt` - đây không phải tệp ngưỡng.".format(
            utils.rel(path)))
        return 1
    try:
        run = fusion.load_run(args.apply_to, need_probabilities=True)
        report = fusion.applied_report(run, rules)
    except fusion.FusionError as exc:
        print("LỖI: {}".format(exc))
        return 1
    report["at"] = datetime.datetime.now().isoformat(timespec="seconds")
    report["tệp_ngưỡng"] = utils.rel(path)
    out = Path(args.out or DEFAULT_APPLIED)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("Đã ghi {} (lượt '{}': {} khía cạnh có ngưỡng, {} để nguyên).".format(
        utils.rel(out), report["split"] or "?", len(report["ngưỡng_dùng"]),
        len(report["khía_cạnh_để_nguyên"])))
    for aspect, item in sorted(report["ngưỡng_dùng"].items()):
        print("  {:<14} ngưỡng={} F1 âm {} -> {} (chênh {})".format(
            aspect, item, report["f1_âm_từng_khía_cạnh_trước"].get(aspect),
            report["f1_âm_từng_khía_cạnh_sau"].get(aspect),
            report["chênh_f1_âm_từng_khía_cạnh"].get(aspect)))
    for aspect in report["khía_cạnh_để_nguyên"]:
        print("  {:<14} ĐỂ NGUYÊN: F1 âm {} (không đổi - xem lí do trong tệp luật)".format(
            aspect, report["f1_âm_từng_khía_cạnh_trước"].get(aspect)))
    macro_before = report["f1_âm_macro_trước"]
    macro_after = report["f1_âm_macro_sau"]
    print("  số ô {} -> {}; macro (khía cạnh có ô âm) {} -> {}; macro (khía cạnh đang dương) "
          "{} -> {}; macro (MỌI khía cạnh) {} -> {}".format(
              report["số_ô_trước"], report["số_ô_sau"],
              macro_before.get("macro_trên_khía_cạnh_có_ô_âm"),
              macro_after.get("macro_trên_khía_cạnh_có_ô_âm"),
              macro_before.get("macro_trên_khía_cạnh_đang_dương"),
              macro_after.get("macro_trên_khía_cạnh_đang_dương"),
              report["macro_trên_mọi_khía_cạnh"]["trước"],
              report["macro_trên_mọi_khía_cạnh"]["sau"]))
    if report["khía_cạnh_có_ngưỡng_không_có_ở_lượt_này"]:
        print("  LƯU Ý: bảng ngưỡng có khía cạnh không thấy ở lượt này: {}".format(
            ", ".join(report["khía_cạnh_có_ngưỡng_không_có_ở_lượt_này"])))
    return 0


def main(argv=None):
    args = parse_args(argv)
    mistake = check_args(args)
    if mistake:
        print("LỖI: {}".format(mistake))
        return 2
    if args.apply_to:
        return apply_frozen(args)
    return decide(args)


if __name__ == "__main__":
    raise SystemExit(main())
