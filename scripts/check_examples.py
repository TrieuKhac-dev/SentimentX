# -*- coding: utf-8 -*-
"""Kiểm ví dụ few-shot KHÔNG RÒ RỈ từ `val`/`test`. KHÔNG chạy model.

CÁCH DÙNG
    python scripts/check_examples.py --examples configs/prompts/examples/absa_cot_1shot_v1.txt
    python scripts/check_examples.py --examples <file> --require-train   # ví dụ PHẢI lấy từ `train`
    python scripts/check_examples.py --examples <file> --version <mã phiên bản dữ liệu>

VÌ SAO PHẢI CÓ CỬA NÀY
Ví dụ few-shot nằm trong ĐẦU VÀO của model: một ví dụ lấy từ `test` nghĩa là model đã nhìn thấy đáp án
của chính ô nó sắp được chấm - điểm lên mà không ai kiểm được, và `metrics.json` không ghi lại dấu vết
nào. `ci_checks.py` chỉ kiểm file ví dụ CÓ TỒN TẠI (không kiểm nội dung), nên cửa này là chỗ duy nhất
bắt được lỗi đó trước khi giao notebook cho người chạy.

`--require-train` dùng cho ví dụ LẤY TỪ DỮ LIỆU (quy ước: chỉ lấy từ split `train`, ghi rõ `train, dòng N`).
File ví dụ do người viết tay (như `absa_cot_1shot_v1.txt`) thì KHÔNG bật cờ này - chúng vốn không có
trong dữ liệu, nhưng vẫn phải qua điều kiện "không trùng `val`/`test`".

Mã thoát: `0` sạch, `1` có rò rỉ (hoặc thiếu trong `train` khi bật `--require-train`), `2` câu lệnh chưa rõ.
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

from src.workflow import examples_leak  # noqa: E402


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Kiểm ví dụ few-shot không rò rỉ từ val/test (không chạy model).")
    parser.add_argument("--examples", required=True,
                        help="File ví dụ few-shot (configs/prompts/examples/<tên>.txt).")
    parser.add_argument("--require-train", action="store_true",
                        help="Mọi ví dụ PHẢI có trong split `train` (dùng cho ví dụ lấy từ dữ liệu).")
    parser.add_argument("--dataset", default=None, help="Tên dataset (mặc định lấy theo cấu hình).")
    parser.add_argument("--version", default=None,
                        help="Mã phiên bản dữ liệu đã xử lý (mặc định: bản mới nhất trên đĩa).")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        report = examples_leak.check(args.examples, version_id=args.version, dataset=args.dataset,
                                     require_train=args.require_train)
    except examples_leak.ExamplesLeakError as exc:
        print("LỖI: {}".format(exc))
        return 1
    except FileNotFoundError as exc:
        print("LỖI: {} - không kiểm được ví dụ mà chưa có dữ liệu đã xử lý.".format(exc))
        return 1
    print("File ví dụ : {}".format(report["file"]))
    print("Phiên bản  : {} (nguồn: {})".format(report["version_id"], report["version_source"]))
    print("Số ví dụ   : {} (có trong `train`: {})".format(report["examples"], report["in_train"]))
    for item in report["rò rỉ"]:
        print("  RÒ RỈ: dòng {} trùng một review của split `{}`".format(item["dòng"], item["split"]))
    for item in report["thiếu trong train"]:
        print("  THIẾU TRONG `train`: dòng {} (đã bật --require-train)".format(item["dòng"]))
    if report["sạch"]:
        print("KẾT LUẬN: KHÔNG RÒ RỈ.")
        return 0
    print("KẾT LUẬN: KHÔNG DÙNG ĐƯỢC - đổi ví dụ (lấy dòng khác trong `train`), KHÔNG sửa ngưỡng.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
