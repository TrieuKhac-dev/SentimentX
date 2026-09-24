# -*- coding: utf-8 -*-
"""Kiểm CỔNG ghi nhận: ghi một run GIẢ (tham số, chỉ số, 1 file nhỏ) rồi xác nhận nơi nhận.

VÌ SAO CÓ SCRIPT NÀY
Cổng ở P4 là "run smoke xuất hiện trên DagsHub". Kiểm bằng một run giả có hai cái lợi: chạy trong
vài giây (không cần GPU, không cần model, không cần dữ liệu), và nếu hỏng thì biết ngay hỏng ở
KHÂU GHI NHẬN chứ không phải ở model. Script cũng in ra đúng thứ còn thiếu (token, thư viện,
địa chỉ máy chủ) để sửa.

CÁCH DÙNG
    python scripts/smoke_tracking.py                  # theo configs/experiments/tracking.yaml
    python scripts/smoke_tracking.py --tracker none   # thử không ghi đi đâu (kiểm script)
    python scripts/smoke_tracking.py --keep           # giữ thư mục kết quả để xem file

ĐỌC KẾT QUẢ
    KẾT LUẬN: ĐẠT   -> phiên ghi nhận hoạt động, không có ghi chú hỏng (mã thoát 0)
    KẾT LUẬN: CHƯA  -> in ra lí do và việc cần làm (mã thoát 2)

Run giả nằm trong `experiments/_smoke/<lúc chạy>/` (gốc kết quả, đổi được bằng
`SENTIMENTX_RESULTS_ROOT`). Trên DagsHub, run nằm ở địa chỉ có đuôi `.mlflow`:
`https://dagshub.com/<owner>/<repo>.mlflow` - KHÁC trang repo (`.../<owner>/<repo>`), vì trang
repo chỉ hiện dữ liệu/đối tượng của DagsHub, còn run MLflow nằm trong mục Experiments.
"""

import argparse
import shutil
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Trên Windows, console mặc định có thể không phải UTF-8 (ví dụ cp1252),
# khiến việc in tiếng Việt bị lỗi. Ép stdout/stderr sang UTF-8.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from src import experiments, paths, runlog, runtime, tracking, utils
from src.tracking import base as tracking_base
from src.tracking import run_meta

# Giá trị giả để nhìn ra ngay trên giao diện đây là run kiểm tra, không phải kết quả thật.
PARAMS = {"smoke": "true", "prompt": "smoke", "max_length": 1280}
METRICS = {"accuracy": {"macro": 50.0, "micro": 49.5}, "cells": 700}
ARTIFACT = "smoke.json"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Ghi một run giả để kiểm cổng ghi nhận.")
    parser.add_argument("--tracker", default=None,
                        help="Ghi đè `tracking.tracker` (mlflow | local_json | none).")
    parser.add_argument("--experiment", dest="experiment_name", default=None,
                        help="Ghi đè tên experiment trên máy chủ.")
    parser.add_argument("--keep", action="store_true",
                        help="Giữ thư mục kết quả của run giả để xem file bên trong.")
    return parser.parse_args(argv)


def out_dir_for(moment):
    """Thư mục kết quả của run giả: `<gốc kết quả>/_smoke/<lúc chạy>/`."""
    return paths.results_root() / "_smoke" / moment


def status_of(notes, active):
    """Đọc ghi chú của phiên ghi nhận: đạt khi phiên HOẠT ĐỘNG và không có ghi chú hỏng."""
    broken = [note for note in notes if "hỏng" in note.lower() or "không ghi được" in note]
    if not active:
        return False, "phiên ghi nhận KHÔNG hoạt động (xem lí do ở trên)"
    if broken:
        return False, "; ".join(broken)
    return True, "; ".join(notes) or "không có ghi chú"


def main(argv=None):
    args = parse_args(argv)
    env = runtime.load_env()
    print("=" * 70)
    print("SMOKE - kiểm cổng ghi nhận (run giả, không cần GPU/model/dữ liệu)")
    print("=" * 70)
    print("Máy đang chạy : {}".format(env["env"]))
    print("Biến môi trường: có {} | thiếu {}".format(
        ", ".join(env["found"]) or "không có", ", ".join(env["missing"]) or "không thiếu"))
    for path in env["files"]:
        print("  đọc từ      : {}".format(path))

    try:
        config = dict(experiments.shared("tracking"))
        dagshub = tracking_base.dagshub_config()
    except experiments.ExperimentError as exc:
        print("\nKẾT LUẬN: CHƯA - {}".format(exc))
        return 2
    except tracking_base.TrackingError as exc:
        print("\nKẾT LUẬN: CHƯA - {}".format(exc))
        return 2

    if args.tracker:
        config["tracker"] = args.tracker
    if args.experiment_name:
        config["experiment"] = args.experiment_name
    print("Tracker       : {} (experiment '{}')".format(
        config.get("tracker"), config.get("experiment")))
    print("Máy chủ MLflow: {}".format(dagshub.get("mlflow_uri")))

    # Kiểm TRƯỚC khi chạy: thiếu gì thì nói rõ thiếu gì và cần làm gì, thay vì để lỗi hiện ra
    # dưới dạng một ngoại lệ khó hiểu.
    try:
        tracking.check(config, dagshub)
        print("Kiểm trước    : đủ điều kiện để ghi nhận")
    except tracking_base.TrackingError as exc:
        print("Kiểm trước    : CHƯA đủ - {}".format(exc))

    out_dir = out_dir_for(runlog.now().replace(":", "").replace(" ", "-"))
    print("Thư mục run   : {}".format(utils.rel(out_dir)))

    with runlog.start(out_dir, mode="NEW", info={"smoke": "true", "tracker": config.get("tracker")}) as log:
        record = run_meta.build(
            out_dir, tag="smoke",
            experiment={"model": "smoke", "method": "smoke", "exp_id": "smoke"},
            data={"dataset": "smoke", "ma": "smoke"},
            repo=run_meta.repo_info(), files=[], env=run_meta.env_info(env["env"]))
        run_meta.write(out_dir, record)
        log.on_close(run_meta.closer(record, out_dir, log=log))

        session = tracking.begin(config, out_dir, info={"smoke": "true"}, log=log,
                                 dagshub=dagshub)
        log.on_close(tracking.closer(session, log=log))

        utils.write_json({"note": "file nhỏ để kiểm tải lên", "metrics": METRICS},
                         out_dir / ARTIFACT)
        session.log_params(PARAMS)
        session.log_metrics(METRICS)
        session.log_artifacts(tracking_base.artifact_paths(out_dir, [ARTIFACT]))
        log.step("đã chuẩn bị run giả: 1 file, {} tham số, {} chỉ số".format(
            len(session.params), len(session.metrics)))

    passed, reason = status_of(session.notes, session.active)
    print("\nGhi chú ghi nhận: {}".format(reason))
    if getattr(getattr(session, "run", None), "info", None):
        print("Mã run         : {}".format(session.run.info.run_id))
    if passed and config.get("tracker") == "mlflow":
        print("Mở mục Experiments: {}".format(dagshub.get("mlflow_uri")))
        print("(địa chỉ này có đuôi `.mlflow`, khác trang repo của DagsHub)")
    print("File của run giả: {}".format(utils.rel(out_dir)))
    if args.keep:
        print("  (giữ lại thư mục này vì có --keep)")
    else:
        shutil.rmtree(out_dir, ignore_errors=True)
        print("  (đã xoá sau khi kiểm; thêm --keep để giữ lại)")
    print("\nKẾT LUẬN: {} - {}".format("ĐẠT" if passed else "CHƯA", reason))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())

