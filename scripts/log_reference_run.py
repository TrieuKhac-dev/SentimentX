# -*- coding: utf-8 -*-
"""Ghi MỘT run "tham chiếu công bố" lên MLflow, để so cạnh các lượt chạy của dự án.

VÌ SAO CẦN
Số để SO CÔNG BỐ là cơ sở đo `paper` (`docs/04_experiments/reference_publication.md`). Mỗi lượt chạy
giờ gửi số đó lên MLflow với tiền tố `paper.`; muốn thấy CẠNH NHAU trên cùng biểu đồ thì công bố phải
là một run nữa - run này.

Số đọc từ `data/reference_publication/*.csv` qua `src/reporting/reports.py::load_reference`, nên KHÔNG
chép lại số lần thứ hai (một nguồn, một cách đọc).

CHẠY TAY KHI CÓ MẠNG
Cần mạng + token DagsHub (như việc dọn run rỗng). Không có mạng thì lệnh chỉ in ra và dừng.

    python scripts/log_reference_run.py                 # ghi run tham chiếu
    python scripts/log_reference_run.py --dry-run       # chỉ in số, không gửi
    python scripts/log_reference_run.py --shot 1 5      # ghi thêm các mức ví dụ khác (mặc định 0/1/5)
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

from src.core import paths  # noqa: E402
from src.reporting import reports  # noqa: E402
from src.tracking import base as tracking_base, mlflow_tracker  # noqa: E402

RUN_NAME = "cong-bo-tham-chieu"
PRF_KEYS = ("precision", "recall", "f1")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Ghi run tham chiếu công bố lên MLflow.")
    parser.add_argument("--shot", type=int, action="append", default=None,
                        help="Mức ví dụ cần ghi (lặp lại được). Mặc định: 0, 1, 5.")
    parser.add_argument("--dry-run", action="store_true", help="Chỉ in ra, không gửi lên máy chủ.")
    return parser.parse_args(argv)


def reference_metrics(shots):
    """Số của công bố -> metric đặt tên `paper.<shot>shot.<khía cạnh>.<...>`."""
    found = {}
    for shot in shots:
        accuracy, prf, suffix = reports.load_reference(shot=shot)
        for aspect, value in (accuracy or {}).items():
            found["paper.{}shot.{}.accuracy".format(shot, aspect)] = float(value)
        for (aspect, sentiment), item in (prf or {}).items():
            for key in PRF_KEYS:
                if item.get(key) is not None:
                    found["paper.{}shot.{}.{}.{}".format(shot, aspect, sentiment, key)] = \
                        float(item[key])
    return found


def main(argv=None):
    args = parse_args(argv)
    shots = args.shot or [0, 1, 5]
    metrics = reference_metrics(shots)
    print("Số của công bố ({} mức ví dụ, {} chỉ số):".format(shots, len(metrics)))
    for key in sorted(metrics)[:10]:
        print("  {} = {}".format(key, metrics[key]))
    if args.dry_run:
        print("\n--dry-run: không gửi lên máy chủ.")
        return 0

    try:
        config = {"experiment": "sentimentx-absa"}
        dagshub = tracking_base.dagshub_config()
        mlflow_tracker.check(config, dagshub)
        mlflow = mlflow_tracker.connect(config, dagshub)
    except BaseException as exc:  # noqa: BLE001 - thiếu mạng/token là việc phải báo, không traceback
        print("LỖI: không kết nối được máy chủ MLflow ({}: {}).".format(type(exc).__name__, exc))
        return 1

    run = mlflow.start_run(run_name=RUN_NAME, tags={"reference": "true",
                                                    "source": "reference_publication"})
    try:
        mlflow.log_params({"model": "GPT-4o-mini", "shots": ", ".join(str(s) for s in shots),
                           "note": "so cong bo - docs/04_experiments/reference_publication.md"})
        mlflow.log_metrics(metrics)
        folder = paths.reference_publication_dir()
        for name in ("accuracy_by_aspect.csv", "sentiment_distribution.csv"):
            path = folder / name
            if path.is_file():
                mlflow.log_artifact(str(path))
        print("Đã ghi run tham chiếu: {}".format(getattr(run.info, "run_id", "")))
    finally:
        mlflow.end_run(status="FINISHED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
