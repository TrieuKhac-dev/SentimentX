# -*- coding: utf-8 -*-
"""Router THEO KHÍA CẠNH: chốt trên `val` một lượt làm nguồn cho MỖI khía cạnh, rồi áp lên tập khác.

CÁCH DÙNG
    # 1) CHỐT router trên val: ghi LUẬT (đóng băng) + số của bản router trên val
    python scripts/ensemble_aspect.py --fit --run <val A> --run <val B> \
        --write-router data/reports/fusion/aspect_router.json \
        --out data/reports/fusion/router_val.json

    # 2) ÁP lên test: đọc ĐÚNG tệp luật đã chốt (KHÔNG chốt lại trên test)
    python scripts/ensemble_aspect.py --apply --run <test A> --run <test B> \
        --router-file data/reports/fusion/aspect_router.json \
        --out data/reports/fusion/router_test.json

KHÁC `scripts/ensemble.py` Ở ĐÂU: ensemble TRỘN XÁC SUẤT bằng một bộ trọng số cho MỌI khía cạnh; router
này KHÔNG trộn - mỗi khía cạnh lấy nhãn của MỘT lượt đã chốt, theo luật ghi ở `fusion.ROUTER_LAW`. Lượt
ĐẦU trong `--run` giữ KHUNG Ô, và THỨ TỰ truyền vào là một phần của luật (dùng khi hoà - xem `--help`).

TIÊU CHÍ CHỐT LÀ BẮT BUỘC (`--criterion`), và chỉ truyền được ở `--fit`:
    `--criterion f1_âm`    F1 lớp ÂM của khía cạnh trên `val` - sát luật của dự án (lớp âm là chỗ yếu)
    `--criterion accuracy` accuracy ô của khía cạnh trên `val` - sát chỉ số BÁO CÁO (bảng theo khía cạnh)
Hai tiêu chí cho hai router KHÁC NHAU (một bên có thể thắng cả 7 khía cạnh theo F1 âm nhưng thua accuracy
ở vài khía cạnh), nên tiêu chí phải chốt TRƯỚC khi áp lên `test`; `--apply` đọc tiêu chí từ chính tệp
luật, và tệp luật ghi kèm `điểm` của MỌI ứng viên (cả hai tiêu chí) để lựa chọn kiểm lại được.

`--fit` chỉ nhận lượt `val` (công cụ CHẶN nếu có lượt khác split): chốt trên tập sẽ báo cáo là tự lừa
mình. Luật đã chốt ghi ra tệp JSON trong repo TRƯỚC khi áp lên `test` - đó là điều kiện của luật 1 (xem
`docs/04_experiments/09_fusion.md` mục 2).

Ghi hai thứ: (a) JSON số của bản router (hai cơ sở đo, số ô, F1 âm từng khía cạnh) kèm **số của TỪNG lượt
thành viên trên cùng tập** (mục 4 của `09_fusion.md`: không có phép so đó thì con số không nói lên gì);
(b) **đầu vào rút gọn** của từng lượt vào `data/reports/fusion/inputs/` để con số tái lập được TỪ REPO
(lượt chạy thật nằm trên Drive).

Mã thoát: `0` xong, `1` không chốt/áp được (thiếu tệp luật, thiếu xác suất, lượt không phải `val`),
`2` câu lệnh chưa rõ.
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

DEFAULT_OUT = "data/reports/fusion/router_aspect.json"
DEFAULT_ROUTER = "data/reports/fusion/aspect_router.json"
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
        description="Router theo khía cạnh: chốt trên val, rồi áp lên tập khác.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--fit", action="store_true", help="CHỐT router trên `val`.")
    mode.add_argument("--apply", action="store_true", help="ÁP router đã chốt lên các lượt đang có.")
    parser.add_argument("--run", action="append", required=True,
                        help="Thư mục kết quả (lặp lại cho từng lượt). Lượt ĐẦU giữ khung ô; THỨ TỰ "
                             "này là một phần của luật (dùng khi hoà).")
    parser.add_argument("--criterion", choices=tuple(sorted(fusion.ROUTER_CRITERIA)), default=None,
                        help="Tiêu chí CHỐT router, BẮT BUỘC khi `--fit` (khi `--apply` thì đọc từ tệp "
                             "luật): {}. Hai tiêu chí cho hai router KHÁC NHAU.".format(
                                 " / ".join("`{}` = {}".format(name, note)
                                            for name, note in sorted(fusion.ROUTER_CRITERIA.items()))))
    parser.add_argument("--router-file", default=DEFAULT_ROUTER,
                        help="Tệp luật router đã chốt (khi `--apply`).")
    parser.add_argument("--write-router", default=None,
                        help="Ghi tệp luật router vừa chốt (khi `--fit`).")
    parser.add_argument("--out", default=DEFAULT_OUT, help="Tệp JSON để ghi số của bản router.")
    parser.add_argument("--inputs-dir", default=DEFAULT_INPUTS,
                        help="Thư mục ghi đầu vào rút gọn từng lượt (chuỗi rỗng = không ghi).")
    return parser.parse_args(argv)


def check_args(args):
    """Tổ hợp cờ chưa rõ -> câu giải thích; hợp lệ -> None (test gọi thẳng được)."""
    if args.fit and not args.write_router:
        return ("`--fit` cần `--write-router <tệp>`: luật phải ĐÓNG BĂNG thành tệp trước khi áp lên "
                "`test`, nếu không thì bước áp không có gì để đọc và lần sau sẽ chốt lại bằng chính "
                "tập đang báo cáo.")
    if args.apply and args.write_router:
        return "`--write-router` chỉ dùng khi CHỐT (`--fit`): `--apply` đọc luật đã chốt."
    if args.fit and not args.criterion:
        return ("`--fit` cần `--criterion`: luật phải nói rõ chốt theo SỐ NÀO, vì `f1_âm` và `accuracy` "
                "cho hai router khác nhau và tối ưu hai thứ khác nhau.")
    if args.apply and args.criterion:
        return ("`--criterion` chỉ dùng khi CHỐT (`--fit`): `--apply` đọc tiêu chí từ CHÍNH tệp luật, nên "
                "không đổi được tiêu chí sau khi đã thấy `test`.")
    return None


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
        if args.fit:
            router = fusion.fit_aspect_router(runs, criterion=args.criterion)
            choices = fusion.router_for(runs, {aspect: item["model"]
                                               for aspect, item in router.items()})
            document = fusion.router_document(runs, router, criterion=args.criterion)
            document["at"] = datetime.datetime.now().isoformat(timespec="seconds")
            path = Path(args.write_router)
            write_report(path, document)
            print("Đã ghi luật router (khoá theo tên model, tiêu chí `{}`): {}".format(
                args.criterion, utils.rel(path)))
            for aspect, item in sorted(router.items()):
                print("  {:<14} -> {:<20} ({})".format(aspect, item["model"], item["lí_do"]))
        else:
            path = Path(args.router_file)
            if not path.is_file():
                print("LỖI: không thấy tệp luật router '{}' - chạy `--fit` trước.".format(
                    args.router_file))
                return 1
            choices = fusion.router_for(runs, fusion.load_router(path), source=str(path))
        preds, counts = fusion.router_predictions(runs[0], runs, choices)
    except fusion.FusionError as exc:
        print("LỖI: {}".format(exc))
        return 1
    model_of_dir = {str(run["dir"]): fusion.model_of(run) for run in runs}
    report = fusion.report_of(runs[0], preds, {
        "at": datetime.datetime.now().isoformat(timespec="seconds"),
        "cách": "router theo khía cạnh: mỗi khía cạnh lấy nhãn của MỘT lượt đã chốt trên val",
        "luật": dict(fusion.ROUTER_LAW),
        "nguồn_theo_khía_cạnh": {aspect: model_of_dir.get(source, source)
                                 for aspect, source in sorted(choices.items())},
        "đếm_ô": counts,
        "nguồn": [utils.rel(run["dir"]) for run in runs],
        "thành_viên": fusion.members_report(runs),
        "ghi_chú": ("mọi lượt phải chấm CÙNG split; số ô đọc kèm theo luật 1 của metrics.md; số của bản "
                    "router chỉ có nghĩa khi đứng cạnh `thành_viên`"),
    })
    path = Path(args.out)
    write_report(path, report)
    print("Đã ghi {}".format(utils.rel(path)))
    if args.inputs_dir:
        for run in runs:
            written = fusion.dump_inputs(run, Path(args.inputs_dir) / "{}.csv".format(tag_of(run)))
            print("  đầu vào: {}".format(utils.rel(written)))
    print("  F1 âm macro (paper): {}".format(report["f1_âm_macro"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
