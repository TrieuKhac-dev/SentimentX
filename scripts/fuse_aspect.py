# -*- coding: utf-8 -*-
"""Gộp HAI TẦNG: KHUNG Ô từ lượt ENCODER, SẮC THÁI từng khía cạnh từ lượt MỘT khía cạnh. KHÔNG chạy model.

CÁCH DÙNG
    python scripts/fuse_aspect.py --encoder <lượt encoder> \
        --aspect <lượt một-khía-cạnh của colour> --aspect <... của packing> \
        --aspect <... của price> --aspect <... của shipping> --aspect <... của smell> \
        --aspect <... của stayingpower> --aspect <... của texture> \
        --out data/reports/fusion/fuse_aspect_test.json

Luật đã CHỐT TRƯỚC khi chạy bảy lượt (`fusion.TWO_TIER_LAW`, mục 14.10 của `present_plan.md`):
    - KHUNG Ô lấy từ lượt ENCODER (mọi dòng/khía cạnh đã chấm của lượt đó);
    - SẮC THÁI của mỗi khía cạnh lấy từ lượt MỘT-khía-cạnh của CHÍNH khía cạnh đó;
    - LỆCH về "không nhắc tới" thì GIỮ quyết định của ENCODER (phát hiện khía cạnh là điểm mạnh đã đo
      của encoder), và ĐẾM riêng số ô lệch - luật này ĐỔI kết quả nên nó phải nhìn thấy được;
    - THIẾU ô ở lượt một-khía-cạnh thì giữ nhãn của encoder và đếm riêng.
Thiếu lượt cho một khía cạnh nào của encoder, lượt chấm nhiều khía cạnh, lượt trùng khía cạnh, hoặc
khác mã "không nhắc tới" đều là LỖI - không im lặng bỏ qua.

Ghi: JSON số của bản hai tầng (hai cơ sở đo, số ô, F1 âm từng khía cạnh) + số của TỪNG nguồn trên cùng
tập (`thành_viên`), + `đếm_ô` (số ô lấy từ mỗi lượt, số ô lệch giữ encoder, số ô thiếu). Đầu vào rút gọn
của mọi lượt tham gia được ghi vào `data/reports/fusion/inputs/` để con số tái lập được TỪ REPO.

Mã thoát: `0` xong, `1` không gộp được (thiếu lượt/khác nhãn), `2` câu lệnh chưa rõ.
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

DEFAULT_OUT = "data/reports/fusion/fuse_aspect.json"
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
    parser = argparse.ArgumentParser(
        description="Gộp hai tầng: khung ô từ encoder, sắc thái từng khía cạnh từ lượt một-khía-cạnh.")
    parser.add_argument("--encoder", required=True,
                        help="Thư mục kết quả của lượt ENCODER (lượt giữ KHUNG Ô).")
    parser.add_argument("--aspect", action="append", required=True,
                        help="Thư mục kết quả của một lượt MỘT-khía-cạnh (lặp lại cho mỗi khía cạnh).")
    parser.add_argument("--out", default=DEFAULT_OUT, help="Tệp JSON để ghi số của bản gộp.")
    parser.add_argument("--inputs-dir", default=DEFAULT_INPUTS,
                        help="Thư mục ghi đầu vào rút gọn từng lượt (chuỗi rỗng = không ghi).")
    return parser.parse_args(argv)


def write_report(path, report):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main(argv=None):
    args = parse_args(argv)
    missing = [path for path in [args.encoder] + list(args.aspect) if not Path(path).is_dir()]
    if missing:
        print("LỖI: không thấy thư mục {}.".format(", ".join(missing)))
        return 2
    try:
        encoder_run = fusion.load_run(args.encoder)
        aspect_runs = [fusion.load_run(path, need_probabilities=True) for path in args.aspect]
        preds, counts = fusion.merge_two_tier(encoder_run, aspect_runs)
    except fusion.FusionError as exc:
        print("LỖI: {}".format(exc))
        return 1
    report = fusion.report_of(encoder_run, preds, {
        "at": datetime.datetime.now().isoformat(timespec="seconds"),
        "cách": "hai tầng: khung ô từ encoder, sắc thái từng khía cạnh từ lượt một-khía-cạnh",
        "luật": dict(fusion.TWO_TIER_LAW),
        "nguồn": {"encoder": utils.rel(encoder_run["dir"]),
                  "một_khía_cạnh": {run["aspects"][0]: utils.rel(run["dir"]) for run in aspect_runs}},
        "đếm_ô": counts,
        "thành_viên": fusion.members_report([encoder_run] + aspect_runs),
        "ghi_chú": ("mọi lượt phải chấm CÙNG split; số ô đọc kèm theo luật 1 của metrics.md; số của bản "
                    "gộp chỉ có nghĩa khi đứng cạnh `thành_viên`, và `đếm_ô.lệch_giữ_encoder` nói luật "
                    "lệch-về-không-nhắc-tới đã giữ lại bao nhiêu ô của encoder"),
    })
    path = Path(args.out)
    write_report(path, report)
    print("Đã ghi {}".format(utils.rel(path)))
    print("  ô lấy từ lượt một-khía-cạnh: {}".format(counts["từ_một_khía_cạnh"]))
    print("  ô LỆCH về 'không nhắc tới' (giữ encoder): {} (tổng {})".format(
        counts["lệch_giữ_encoder"], counts["tổng_lệch"]))
    if counts["thiếu_ô"]:
        print("  ô THIẾU ở lượt một-khía-cạnh (giữ encoder): {}".format(counts["thiếu_ô"]))
    if args.inputs_dir:
        for run in [encoder_run] + list(aspect_runs):
            written = fusion.dump_inputs(run, Path(args.inputs_dir) / "{}.csv".format(tag_of(run)))
            print("  đầu vào: {}".format(utils.rel(written)))
    print("  F1 âm macro (paper): {}".format(report["f1_âm_macro"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
