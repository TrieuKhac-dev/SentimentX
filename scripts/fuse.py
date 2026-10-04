# -*- coding: utf-8 -*-
"""Chốt LUẬT LAI encoder + LLM trên `val`, rồi ÁP lên tập khác. KHÔNG chạy model.

CÁCH DÙNG
    # 1) chốt luật trên val: mỗi khía cạnh lấy nguồn nào (F1 âm cao hơn)
    python scripts/fuse.py --fit --llm <val LLM> --encoder <val encoder> \
        --out data/reports/fusion/rules.json
    # 2) áp luật đã chốt lên test (KHÔNG xem test để sửa luật)
    python scripts/fuse.py --apply --rules data/reports/fusion/rules.json \
        --llm <test LLM> --encoder <test encoder> --out data/reports/fusion/fuse_test.json

Vì sao hai bước tách rời: luật phải chốt trên `val` rồi đóng băng (tệp JSON ghi vào repo), sau đó mới áp
lên `test` - đây là điều kiện (ii) đã ghi ở `04_backlog.md` mục 10.5. Áp luật chỉ tốn vài giây vì không
chạy model.

Mã thoát: `0` xong, `1` không làm được (thiếu tệp/luật), `2` câu lệnh chưa rõ.
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

DEFAULT_RULES = "data/reports/fusion/rules.json"
DEFAULT_OUT = "data/reports/fusion/fuse.json"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Luật lai encoder + LLM: chốt trên val, áp lên test.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--fit", action="store_true", help="Chốt luật trên val.")
    mode.add_argument("--apply", action="store_true", help="Áp luật đã chốt lên tập đang có.")
    parser.add_argument("--llm", required=True, help="Thư mục kết quả của lượt LLM (đường prompt).")
    parser.add_argument("--encoder", required=True, help="Thư mục kết quả của lượt encoder.")
    parser.add_argument("--rules", default=DEFAULT_RULES, help="Tệp luật (khi --apply).")
    parser.add_argument("--out", default=None, help="Tệp JSON để ghi (mặc định theo chế độ).")
    return parser.parse_args(argv)


def _write_report(path, report, log=print):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    log("Đã ghi {}".format(utils.rel(path)))


def main(argv=None):
    args = parse_args(argv)
    for path in (args.llm, args.encoder):
        if not Path(path).is_dir():
            print("LỖI: không thấy thư mục '{}'.".format(path))
            return 2
    try:
        llm_run = fusion.load_run(args.llm)
        encoder_run = fusion.load_run(args.encoder)
        if args.fit:
            rules = fusion.fit_rules(llm_run, encoder_run)
            rules["at"] = datetime.datetime.now().isoformat(timespec="seconds")
            rules["nguồn"] = {"llm": utils.rel(llm_run["dir"]),
                              "encoder": utils.rel(encoder_run["dir"])}
            rules["ghi_chú"] = ("luật chốt trên '{}'; ĐÓNG BĂNG rồi mới áp lên test"
                                .format(llm_run["split"] or "val"))
            out = args.out or DEFAULT_RULES
            _write_report(out, rules)
            for aspect, item in sorted(rules.items()):
                if isinstance(item, dict) and "nguồn" in item:
                    print("  {:<14} -> {:<8} ({})".format(aspect, item["nguồn"], item["lí do"]))
            return 0
        rules_path = Path(args.rules)
        if not rules_path.is_file():
            print("LỖI: không thấy tệp luật '{}' - chạy --fit trước.".format(args.rules))
            return 1
        rules = json.loads(rules_path.read_text(encoding="utf-8"))
        preds, counts = fusion.apply_rules(llm_run, encoder_run, rules)
    except fusion.FusionError as exc:
        print("LỖI: {}".format(exc))
        return 1
    report = fusion.report_of(llm_run, preds, {
        "at": datetime.datetime.now().isoformat(timespec="seconds"),
        "cách": "lai theo khía cạnh: mỗi khía cạnh lấy nhãn của nguồn đã chốt trên val",
        "luật": {aspect: item.get("nguồn") for aspect, item in rules.items()
                 if isinstance(item, dict) and "nguồn" in item},
        "đếm ô theo nguồn": counts,
        "nguồn": {"llm": utils.rel(llm_run["dir"]), "encoder": utils.rel(encoder_run["dir"])},
        "ghi_chú": ("phải so với TỪNG nguồn một mình trên CÙNG tập; số ô đọc kèm theo luật 1 của "
                    "metrics.md"),
    })
    _write_report(args.out or DEFAULT_OUT, report)
    print("  F1 âm macro (paper): {}".format(report["f1_âm_macro"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
