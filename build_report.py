# -*- coding: utf-8 -*-
"""Vẽ lại báo cáo từ FILE KẾT QUẢ (không chạy lại EDA / pipeline).

Cách dùng:
    python build_report.py                     # cả 2 báo cáo, kết quả mới nhất
    python build_report.py --dataset cosmetics # 2 báo cáo + TỰ MỞ trình duyệt
    python build_report.py --phase eda         # chỉ báo cáo EDA
    python build_report.py --list              # xem kết quả đang có trên đĩa
    python build_report.py --version <mã> --plotlyjs cdn

Kết quả: `report.html` nằm ngay trong thư mục chứa file kết quả, nên mở được khi
không có mạng:
    data/raw/<name>/<raw_version>/eda/report.html      (EDA đo trên raw)
    data/processed/<mã>/eda/report.html                (EDA đo trên dataset)
    data/processed/<mã>/pipeline/report.html

Chỉ định --dataset nghĩa là bạn đang xem một dataset cụ thể, nên công cụ mở luôn file
HTML của các nhóm vừa vẽ bằng trình duyệt mặc định. Muốn tắt: --no-open.
Gõ sai tên dataset sẽ báo ngay kèm gợi ý tên gần đúng.

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

from src import config, paths, versioning
from src import dataset as dataset_config

from src.reporting import render
from src.reporting import result as result_io

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
    rồi kết luận "chưa có file kết quả" - dễ tưởng là lỗi ở khâu chạy. Kiểm tra
    sớm để chỉ đúng chỗ gõ sai và gợi ý tên gần đúng.
    """
    names = dataset_config.available()
    if not names:
        print("Chưa có cấu hình dataset nào trong {}.".format(
            _rel(config.DATASET_CONFIG_DIR)))
        print("Tạo thư mục <tên>/<version>.yaml ở đó trước, rồi chạy lại.")
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


def eda_dirs(dataset=None):
    """Thư mục chứa kết quả EDA, mới nhất trước.

    EDA ghi kết quả ngay cạnh thứ nó đo: `data/raw/<name>/<raw_version>/eda/` khi đo trên
    raw, hoặc `data/processed/<mã>/eda/` khi đo trên dataset.
    """
    found = []
    raw_root = paths.data("raw")
    if raw_root.is_dir():
        for name_dir in sorted(raw_root.iterdir()):
            if not name_dir.is_dir() or (dataset and name_dir.name != dataset):
                continue
            for version_dir in sorted(name_dir.iterdir()):
                candidate = version_dir / paths.pattern("eda_dir")
                if candidate.is_dir():
                    found.append(candidate)
    for processed in versioning.dataset_dirs():
        if dataset and not processed.name.startswith(str(dataset) + "-ds"):
            continue
        candidate = processed / paths.pattern("eda_dir")
        if candidate.is_dir():
            found.append(candidate)
    return found


def pipeline_dirs(dataset=None):
    """Thư mục chứa kết quả pipeline, mới nhất trước."""
    found = []
    for processed in versioning.dataset_dirs():
        if dataset and not processed.name.startswith(str(dataset) + "-ds"):
            continue
        found.append(versioning.pipeline_report_dir(processed.name))
    return found


def result_dirs(phase, dataset=None):
    """Các thư mục đang có kết quả của một nhóm báo cáo."""
    return eda_dirs(dataset) if phase == "eda" else pipeline_dirs(dataset)


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
        help="Nhóm cần vẽ báo cáo (mặc định: all).",
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


def resolve_dir(phase, version=None, dataset=None):
    """Thư mục chứa file kết quả của một nhóm.

    Ưu tiên mã chỉ định bằng --version, rồi tới kết quả mới nhất trên đĩa.
    Với EDA, `version` có thể là mã phiên bản dataset hoặc nhãn `raw_version`.
    """
    if version:
        if phase == "pipeline":
            return versioning.pipeline_report_dir(version)
        candidate = paths.processed(version) / paths.pattern("eda_dir")
        if candidate.is_dir():
            return candidate
        raw_root = paths.data("raw")
        if raw_root.is_dir():
            for name_dir in sorted(raw_root.iterdir()):
                candidate = name_dir / version / paths.pattern("eda_dir")
                if candidate.is_dir():
                    return candidate
        return paths.processed(version) / paths.pattern("eda_dir")

    found = result_dirs(phase, dataset)
    return found[0] if found else None


def build_one(phase, version, plotlyjs, dataset):
    """Vẽ báo cáo của một nhóm. Trả về đường dẫn file HTML, hoặc None."""
    directory = resolve_dir(phase, version, dataset)

    if directory is None:
        print("  - {}: chưa có kết quả{} - nhóm này chưa chạy lần nào.".format(
            phase, " cho dataset '{}'".format(dataset) if dataset else ""))
        print("    Hãy chạy: python run_{}.py".format(phase))
        return None

    path = result_io.result_path(directory, phase)

    if not path.exists():
        print("  - {}: thư mục này thiếu file kết quả ({})".format(
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
    """In ra những gì đang có trên đĩa: dataset đã xử lý, kết quả EDA, kết quả pipeline."""
    datasets = versioning.dataset_dirs()
    if not datasets:
        print("Chưa có dataset nào trong {}.".format(_rel(paths.data("processed"))))
    else:
        print("Dataset đã xử lý trong {}:".format(_rel(paths.data("processed"))))
        for path in datasets:
            log = versioning.read_processing_log(path.name)
            after = (log.get("record_counts") or {}).get("after") or {}
            total = sum(after.values()) if after else ""
            print("  - {:<46} {}".format(path.name, "{} dòng".format(total) if total else ""))

    eda = eda_dirs()
    print("\nKết quả EDA ({}):".format(len(eda)))
    for path in eda or []:
        print("  - {}".format(_rel(path)))

    pipeline = pipeline_dirs()
    print("\nKết quả pipeline ({}):".format(len(pipeline)))
    for path in pipeline or []:
        print("  - {}".format(_rel(path)))
    return 0


def main(argv=None):
    args = parse_args(argv)

    print("=" * 70)
    print("BUILD REPORT - vẽ báo cáo từ file kết quả")
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
        print("\nNhóm: {}".format(phase))
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
