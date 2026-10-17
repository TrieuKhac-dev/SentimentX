# -*- coding: utf-8 -*-
"""Kiểm tra artifact serving của từng model mà KHÔNG nạp trọng số.

Đọc cấu hình bằng ``serving.config.load_settings``, dựng ``serving.registry.ModelRegistry``
rồi gọi ``check(all_models=...)`` - mỗi runtime tự kiểm file/head_config/base mà không tải
model. In ra kết quả theo từng model; không có vấn đề nào thì mã thoát 0, có thì 2.

CÁCH DÙNG
    python scripts/check_serving_artifacts.py
    python scripts/check_serving_artifacts.py --model cafebert_exp027
    python scripts/check_serving_artifacts.py --all
"""

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from serving.config import load_settings  # noqa: E402

try:
    from serving.registry import ModelRegistry  # noqa: E402
except ImportError:  # registry do agent khác tạo; chưa có thì báo rõ
    ModelRegistry = None


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Kiểm artifact serving của model.")
    parser.add_argument("--model", action="append", default=[], metavar="ID",
                        help="Chỉ kiểm model này (dùng nhiều lần được).")
    parser.add_argument("--all", action="store_true",
                        help="Kiểm MỌI model, kể cả model đang tắt.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if ModelRegistry is None:
        print("serving.registry chưa có (đang được agent khác tạo). Chưa kiểm được.")
        return 2

    settings = load_settings(models_override=args.model or None)
    registry = ModelRegistry(settings)
    problems = registry.check(all_models=args.all)

    checked = sorted(settings.models) if args.all else sorted(settings.enabled_models)
    total = 0
    for model_id in checked:
        model_problems = (problems or {}).get(model_id) or []
        if not model_problems:
            print("{}: OK".format(model_id))
            continue
        print("{}: {} vấn đề".format(model_id, len(model_problems)))
        for problem in model_problems:
            print("  - {}".format(problem))
            total += 1

    if total == 0:
        print("KẾT LUẬN: ĐẠT")
        return 0
    print("KẾT LUẬN: CHƯA ({} vấn đề)".format(total))
    return 2


if __name__ == "__main__":
    sys.exit(main())