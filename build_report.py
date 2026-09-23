# -*- coding: utf-8 -*-
"""Vẽ lại báo cáo từ FILE KẾT QUẢ (không chạy lại EDA / pipeline).

Cách dùng:
    python build_report.py                     # cả 2 báo cáo, phiên bản mới nhất
    python build_report.py --dataset cosmetics # 2 báo cáo + TỰ MỞ trình duyệt
    python build_report.py --phase eda         # chỉ báo cáo EDA
    python build_report.py --list              # xem các phiên bản đã chạy
    python build_report.py --version cosmetics-v0.1.0-1a2b3c4d --plotlyjs cdn

Kết quả (trong thư mục của phiên bản tương ứng):
    report.html   — báo cáo duy nhất cho người đọc, mở được khi không có mạng

Chỉ định --dataset nghĩa là bạn đang xem một dataset cụ thể, nên công cụ mở
luôn file HTML của các pha vừa vẽ bằng trình duyệt mặc định. Muốn tắt: --no-open.
Tên dataset phải trùng tên file configs/datasets/<tên>.yaml; gõ sai sẽ báo ngay
kèm gợi ý tên gần đúng (thay vì báo "chưa có file kết quả" gây hiểu nhầm).

Lệnh này KHÔNG tính toán lại số liệu. Mọi con số đều đọc từ file
eda_result.json / pipeline_result.json do run_eda.py / run_pipeline.py ghi ra.
"""

import argparse
import difflib
import sys
import webbrowser
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Trên Windows, console mặc định có thể không phải UTF-8 (ví dụ cp1252),
# khiến việc in tiếng Việt bị lỗi. Ép stdout/stderr sang UTF-8.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from src import config, versioning
from src import dataset as dataset_config

from src.reporting import render
from src.reporting import result as result_io

# Pha báo cáo -> thư mục gốc chứa báo cáo của pha đó
PHASE_DIRS = {
    "eda": config.EDA_REPORT_DIR,
    "pipeline": config.PIPELINE_REPORT_DIR,
}
PHASE_LABELS = {
    "eda": "Báo cáo EDA (khảo sát dữ liệu)",
    "pipeline": "Báo cáo Data Pipeline (xử lý dữ liệu)",
}


def _rel(path):
    """Đường dẫn tương đối so với gốc dự án, cho dễ đọc trên console."""
    try:
        return Path(path).relative_to(config.ROOT_DIR).as_posix()
    except ValueError:
        return str(path)


def check_dataset(name):
    """Kiểm tra --dataset có thật không, TRƯỚC khi đi tìm file kết quả.

    Lệnh này không tự chạy EDA / pipeline, nên nếu tên dataset gõ sai thì không
    có gì báo lỗi: hệ thống chỉ lọc thư mục phiên bản theo tên đó, không thấy gì
    rồi kết luận "chưa có file kết quả" — dễ tưởng là lỗi ở khâu chạy. Kiểm tra
    sớm để chỉ đúng chỗ gõ sai và gợi ý tên gần đúng.
    """
    names = dataset_config.available()
    if not names:
        print("Chưa có file cấu hình dataset nào trong {}.".format(
            _rel(config.DATASET_CONFIG_DIR)))
        print("Tạo configs/datasets/<tên>.yaml trước, rồi chạy lại.")
        return False
    if name in names:
        return True

    print("Không có dataset tên '{}': thiếu file {}.".format(
        name, _rel(dataset_config.config_path(name))))
    print("Các dataset hiện có: {}".format(", ".join(names)))
    similar = difflib.get_close_matches(name, names, n=3, cutoff=0.6)
    if similar:
        print("Có phải bạn muốn: {}?".format(" hoặc ".join(similar)))
    return False


def has_runs(phase, dataset=None):
    """Đã có phiên bản nào của pha này trên đĩa chưa (lọc theo dataset nếu có)."""
    if versioning.latest_version(PHASE_DIRS[phase], dataset=dataset):
        return True
    return versioning.latest_entry(dataset=dataset, phase=phase) is not None


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Sinh báo cáo HTML/Markdown từ file kết quả."
    )
    parser.add_argument(
        "--dataset", default=None,
        help="Tên dataset (mặc định: mọi dataset).",
    )
    parser.add_argument(
        "--phase", choices=["eda", "pipeline", "all"], default="all",
        help="Pha cần vẽ báo cáo (mặc định: all).",
    )
    parser.add_argument(
        "--version", default=None,
        help="Mã phiên bản cần vẽ (mặc định: bản mới nhất).",
    )
    parser.add_argument(
        "--plotlyjs", choices=["local", "cdn"], default="local",
        help="Nguồn thư viện vẽ: local = mở offline, cdn = cần Internet.",
    )
    parser.add_argument(
        "--no-open", action="store_true",
        help="Không tự mở trình duyệt (mặc định: mở khi có --dataset).",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="Chỉ liệt kê các phiên bản đã chạy trong mục lục rồi thoát.",
    )
    return parser.parse_args(argv)


def resolve_dir(base, phase, version=None, dataset=None):
    """Thư mục chứa file kết quả của một pha.

    Thứ tự ưu tiên:
        1. Phiên bản chỉ định bằng --version.
        2. Phiên bản mới nhất ghi trong data/processed/manifest.json.
        3. Thư mục phiên bản mới nhất tìm được trên đĩa (khi chưa có mục lục).
    """
    if version:
        return versioning.version_dir(base, version)

    entry = versioning.latest_entry(dataset=dataset, phase=phase)
    if entry:
        directory = versioning.version_dir(base, entry["version_id"])
        if directory.is_dir():
            return directory

    latest = versioning.latest_version(base, dataset=dataset)
    if latest:
        return versioning.version_dir(base, latest)
    return Path(base)


def build_one(phase, version, plotlyjs, dataset):
    """Vẽ báo cáo của một pha. Trả về đường dẫn file HTML, hoặc None."""
    directory = resolve_dir(PHASE_DIRS[phase], phase, version, dataset)
    path = result_io.result_path(directory, phase)

    if not path.exists():
        if not has_runs(phase, dataset):
            print("  - {}: chưa có kết quả{} — pha này chưa chạy lần nào.".format(
                phase, " cho dataset '{}'".format(dataset) if dataset else ""))
        else:
            print("  - {}: phiên bản này thiếu file kết quả ({})".format(
                phase, _rel(path)))
        print("    Hãy chạy: python run_{}.py{}".format(
            phase, " --dataset {}".format(dataset) if dataset else ""))
        return None

    payload = result_io.read_result(path)
    if dataset and payload.get("dataset") and payload["dataset"] != dataset:
        print("  - {}: file kết quả thuộc dataset '{}', bỏ qua.".format(
            phase, payload["dataset"]))
        return None

    html_path = render.write_reports(payload, directory, plotlyjs=plotlyjs)
    print("  - {}: {}".format(phase, PHASE_LABELS[phase]))
    print("      Phiên bản: {}".format(payload.get("version_id") or "(chưa đặt)"))
    print("      HTML     : {}".format(_rel(html_path)))
    return html_path


def open_reports(paths):
    """Mở các file HTML vừa vẽ bằng trình duyệt mặc định của hệ điều hành."""
    print("\nĐang mở trình duyệt:")
    for path in paths:
        print("  - {}".format(_rel(path)))
        try:
            webbrowser.open(Path(path).resolve().as_uri())
        except Exception as exc:      # pragma: no cover - phụ thuộc hệ điều hành
            print("    Không mở được ({}). Mở tay file trên.".format(exc))


def list_versions():
    """In mục lục các phiên bản đã chạy (data/processed/manifest.json)."""
    print("Mục lục: {}".format(_rel(versioning.manifest_path())))
    rows = versioning.summary_rows()
    if not rows:
        print("  (chưa có lần chạy nào)")
        return 0

    header = ["phiên bản", "pha", "thời gian", "số dòng"]
    widths = [
        max(len(str(row[index])) for row in (rows + [header])) for index in range(4)
    ]
    print("  " + "  ".join(
        "{:<{}}".format(header[index], widths[index]) for index in range(4)))
    for row in rows:
        print("  " + "  ".join(
            "{:<{}}".format(str(row[index]), widths[index]) for index in range(4)))
    return 0


def main(argv=None):
    args = parse_args(argv)

    print("=" * 70)
    print("BUILD REPORT — vẽ báo cáo từ file kết quả")
    print("=" * 70)

    if args.list:
        return list_versions()

    print("Thư viện vẽ: {}".format(args.plotlyjs))
    print("Dataset: {}".format(args.dataset or "(mọi dataset)"))

    # Kiểm tra tên dataset trước khi tìm file kết quả: gõ sai tên thì dừng ngay
    # và chỉ rõ tên đúng, thay vì báo "chưa có file kết quả" (hiểu nhầm là do
    # chưa chạy run_eda.py / run_pipeline.py).
    if args.dataset and not check_dataset(args.dataset):
        return 2

    phases = ["eda", "pipeline"] if args.phase == "all" else [args.phase]

    written = []
    for phase in phases:
        print("\nPha: {}".format(phase))
        html_path = build_one(phase, args.version, args.plotlyjs, args.dataset)
        if html_path:
            written.append(html_path)

    if not written:
        print("\nKhông có báo cáo nào được sinh. Hãy chạy run_eda.py hoặc "
              "run_pipeline.py trước.")
        return 1

    print("\nHoàn tất: {} báo cáo.".format(len(written)))

    # Chỉ định --dataset nghĩa là đang xem một dataset cụ thể -> mở luôn báo cáo.
    if args.dataset and not args.no_open:
        open_reports(written)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
