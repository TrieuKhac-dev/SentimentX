# -*- coding: utf-8 -*-
"""Vẽ lại báo cáo từ FILE KẾT QUẢ (không chạy lại EDA / pipeline).

Cách dùng - phải chỉ ĐÍCH DANH đích cần vẽ, hoặc dùng `--all`:

    python build_report.py --phase eda --on raw --name cosmetics --version v0.1.0
    python build_report.py --phase eda --on dataset --hash e0ccc484
    python build_report.py --phase pipeline --on dataset --hash e0ccc484
    python build_report.py --all                  # mọi nhóm × mọi đích đang có
    python build_report.py --phase eda --all      # mọi đích EDA (raw + dataset)
    python build_report.py --all --open           # vẽ hết rồi MỞ hết
    python build_report.py --list                 # đang có gì + lệnh copy được
    python build_report.py --version <mã> --plotlyjs cdn   # thiếu --phase/--on nên sẽ báo lỗi

Kết quả: `report.html` nằm ngay trong thư mục chứa file kết quả, nên mở được khi không có mạng:
    <gốc dữ liệu>/raw/<tên>/<nhãn raw>/eda/report.html      (EDA đo trên dữ liệu gốc)
    <gốc dữ liệu>/processed/<mã>/eda/report.html            (EDA đo trên dataset)
    <gốc dữ liệu>/processed/<mã>/pipeline/report.html

Mặc định KHÔNG tự mở trình duyệt: cuối lượt chạy, công cụ in danh sách link `file://` để bấm
(Ctrl+Click trong VS Code). Muốn mở hết thì thêm `--open`.

Mã thoát: 0 = có vẽ báo cáo · 1 = đích hợp lệ nhưng CHƯA có kết quả (in lệnh cần chạy trước) ·
2 = câu lệnh chưa rõ (thiếu `--phase`/`--on`/`--hash`), cú pháp đã bỏ (`--dataset`, `--phase all`),
hoặc bộ lọc không khớp đích nào.

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

from src.core import config, paths, versioning
from src.core import dataset as dataset_config

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
    """Kiểm tra `--name` có thật không, TRƯỚC khi đi tìm file kết quả.

    VÌ SAO PHẢI KIỂM SỚM: lệnh này không tự chạy EDA / pipeline, nên tên gõ sai thì hệ thống chỉ lọc
    thư mục theo tên đó, không thấy gì rồi kết luận "chưa có file kết quả" - dễ tưởng là lỗi ở khâu
    chạy. Kiểm sớm để chỉ đúng chỗ gõ sai và gợi ý tên gần đúng.

    KHÔNG dùng `dataset.config_path(name)` ở đây: hàm đó NÉM lỗi khi tên không tồn tại - đúng tình
    huống đang kiểm - nên báo lỗi sẽ thành traceback. Tự ghép đường dẫn từ `configs/paths.yaml`.
    """
    names = dataset_config.available()
    if not names:
        print("Chưa có cấu hình dataset nào trong {}.".format(
            _rel(paths.config_path("datasets"))))
        print("Tạo thư mục <tên>/<phiên bản>.yaml ở đó trước, rồi chạy lại.")
        return False
    if name in names:
        return True

    print("Không có dataset tên '{}' trong {}.".format(
        name, _rel(paths.config_path("datasets"))))
    print("Các dataset hiện có: {}".format(", ".join(names)))
    similar = difflib.get_close_matches(name, names, n=3, cutoff=0.6)
    if similar:
        print("Có phải bạn muốn: {}?".format(" hoặc ".join(similar)))
    return False


def target_label(target):
    """Nhãn ngắn của một đích, để in ra: `raw cosmetics@v0.1.0`, `dataset cosmetics@e0ccc484`."""
    if target["source"] == "raw":
        return "raw {}@{}".format(target["name"], target["version"])
    return "dataset {}@{}".format(
        target["name"], versioning.version_parts(target["version"])[1])


def target_command(target):
    """Lệnh `build_report.py` chỉ đích danh MỘT đích (copy dán là chạy)."""
    if target["source"] == "raw":
        return "python build_report.py --phase eda --on raw --name {} --version {}".format(
            target["name"], target["version"])
    _, hash8 = versioning.version_parts(target["version"])
    return "python build_report.py --phase {} --on dataset --hash {}".format(
        target["phase"], hash8)


def raw_targets(dataset=None):
    """Các đích EDA của dữ liệu GỐC: mỗi phiên bản raw một đích.

    Gồm cả nơi CHƯA có thư mục kết quả EDA: "thiếu" là thông tin phải nói ra, kèm lệnh tạo.
    """
    found = []
    raw_root = paths.data("raw")
    if not raw_root.is_dir():
        return found
    for name_dir in sorted(raw_root.iterdir()):
        if not name_dir.is_dir() or (dataset and name_dir.name != dataset):
            continue
        for version_dir in sorted(path for path in name_dir.iterdir() if path.is_dir()):
            found.append({
                "phase": "eda",
                "source": "raw",
                "name": name_dir.name,
                "version": version_dir.name,
                "directory": version_dir / paths.pattern("eda_dir"),
                "producer": "python run_eda.py --on raw --name {} --version {}".format(
                    name_dir.name, version_dir.name),
            })
    return found


def processed_targets(dataset=None):
    """Các đích của dataset ĐÃ XỬ LÝ: EDA và pipeline, mỗi nhóm một đích cho mỗi phiên bản."""
    found = []
    for processed in versioning.dataset_dirs():
        name, hash8 = versioning.version_parts(processed.name)
        if dataset and name != dataset:
            continue
        found.append({
            "phase": "eda",
            "source": "dataset",
            "name": name,
            "version": processed.name,
            "directory": processed / paths.pattern("eda_dir"),
            "producer": "python run_eda.py --on dataset --hash {}".format(hash8),
        })
        log = versioning.read_processing_log(processed.name)
        config_version = (log.get("dataset") or {}).get("version") or "<phiên bản cấu hình>"
        found.append({
            "phase": "pipeline",
            "source": "dataset",
            "name": name,
            "version": processed.name,
            "directory": versioning.pipeline_report_dir(processed.name),
            "producer": "python run_pipeline.py --name {} --version {}".format(
                name, config_version),
        })
    return found


def targets(phase=None, source=None, dataset=None):
    """Mọi đích khớp bộ lọc, theo thứ tự: EDA dữ liệu gốc, EDA dataset, pipeline."""
    want_raw_eda = phase in (None, "eda") and source in (None, "raw")
    want_dataset_eda = phase in (None, "eda") and source in (None, "dataset")
    want_pipeline = phase in (None, "pipeline") and source in (None, "dataset")
    found = raw_targets(dataset) if want_raw_eda else []
    if want_dataset_eda or want_pipeline:
        processed = processed_targets(dataset)
        found += [item for item in processed
                  if (item["phase"] == "eda" and want_dataset_eda)
                  or (item["phase"] == "pipeline" and want_pipeline)]
    return found


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Sinh báo cáo HTML/Markdown từ file kết quả.",
        epilog="Cú pháp đầy đủ: docs/00_workflow/09_cli.md",
    )
    parser.add_argument(
        "--phase", choices=("eda", "pipeline"), default=None,
        help="Nhóm cần vẽ. Bắt buộc, trừ khi dùng --all.",
    )
    parser.add_argument(
        "--on", dest="where", choices=("raw", "dataset"), default=None,
        help="Nơi đo: raw = dữ liệu gốc (cần --name + --version), dataset = dataset đã xử lý "
             "(cần --hash). Bắt buộc, trừ khi dùng --all.",
    )
    parser.add_argument(
        "--name", default=None,
        help="Tên dataset: bắt buộc với --on raw; với --on dataset thì ghi thêm chỉ để đối chiếu.",
    )
    parser.add_argument(
        "--version", default=None,
        help="Nhãn phiên bản dữ liệu GỐC, chỉ dùng với --on raw. KHÔNG phải mã phiên bản dữ liệu "
             "đã xử lý.",
    )
    parser.add_argument(
        "--hash", default=None,
        help="Phiên bản dữ liệu ĐÃ XỬ LÝ: mã đầy đủ hoặc 8 ký tự hex cuối (ví dụ e0ccc484). "
             "Bắt buộc khi --on dataset.",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Vẽ HẾT mọi đích khớp các bộ lọc còn lại; không kèm bộ lọc nào = mọi nhóm × mọi đích.",
    )
    parser.add_argument(
        "--plotlyjs", choices=("local", "cdn"), default="local",
        help="Nguồn thư viện vẽ: local = mở offline, cdn = cần Internet.",
    )
    parser.add_argument(
        "--open", dest="open_browser", action="store_true",
        help="Mở TẤT CẢ báo cáo vừa vẽ bằng trình duyệt (mặc định: chỉ in link file:// để bấm).",
    )
    parser.add_argument(
        "--no-open", action="store_true",
        help="Không tự mở trình duyệt (nay là mặc định; giữ cờ cho tương thích câu lệnh cũ).",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="Liệt kê đích đang có trên đĩa kèm lệnh copy được, rồi thoát.",
    )
    return parser.parse_args(argv)


def removed_flag_message(argv):
    """Câu lỗi khi người dùng gõ cú pháp ĐÃ BỎ, thay vì để argparse nói 'unrecognized arguments'."""
    items = [str(item) for item in argv]
    for flag in ("--dataset", "--raw-version"):
        if any(item == flag or item.startswith(flag + "=") for item in items):
            return ("`{}` đã bỏ: tên dataset nay là `--name`; nhãn dữ liệu gốc nay là "
                    "`--on raw --name <tên> --version <nhãn>`.".format(flag))
    if "--phase" in items:
        index = items.index("--phase")
        if index + 1 < len(items) and items[index + 1] == "all":
            return "`--phase all` đã bỏ: dùng `--all`."
    return None


def plan_targets(args):
    """Chọn danh sách đích sẽ vẽ theo tham số. Trả về `(danh sách, câu lỗi)`.

    Luật cố ý khắt khe: không có `--all` thì phải chỉ ĐÍCH DANH một đích - "tự chọn đại một cái"
    là đoán, mà báo cáo vẽ cho một phiên bản khác thì nhìn vào vẫn hợp lý.
    """
    if not args.all and not args.where:
        return [], ("thiếu `--on`: ghi rõ nơi đo (`--on raw` hoặc `--on dataset`), hoặc `--all`.")
    if args.where == "raw":
        if args.hash:
            return [], "`--hash` là của dataset đã xử lý; dữ liệu gốc dùng `--name` + `--version`."
        if "-ds" in str(args.version or ""):
            return [], ("`--version {}` là MÃ PHIÊN BẢN của dataset đã xử lý, không phải nhãn "
                        "raw_version.\n      Muốn vẽ dataset: python build_report.py --phase {} "
                        "--on dataset --hash {}".format(
                            args.version, args.phase or "eda", args.version))
        if args.phase == "pipeline":
            return [], "pipeline chỉ có nguồn là dataset đã xử lý; dùng `--on dataset --hash …`."
        if not args.all and (not args.name or not args.version):
            return [], ("`--phase eda --on raw` cần đủ `--name` và `--version` (nhãn raw_version).\n"
                        "      Ví dụ: python build_report.py --phase eda --on raw "
                        "--name cosmetics --version v0.1.0")
    if args.where == "dataset":
        if args.version:
            return [], ("`--on dataset` không dùng `--version` (đó là nhãn dữ liệu gốc); dùng "
                        "`--hash`.")
        if not args.all and not args.hash:
            return [], ("`--on dataset` cần `--hash` để chỉ đích danh phiên bản dữ liệu.\n"
                        "      Ví dụ: python build_report.py --phase {} --on dataset "
                        "--hash e0ccc484".format(args.phase or "eda"))
    if not args.all and not args.phase:
        return [], ("thiếu `--phase`: ghi rõ `--phase eda` hoặc `--phase pipeline`, hoặc `--all`.")

    found = targets(phase=args.phase, source=args.where, dataset=args.name)

    if args.where == "dataset" and args.hash:
        try:
            version_id = versioning.find_version(args.hash)
        except versioning.VersionError as exc:
            return [], str(exc)
        name, _ = versioning.version_parts(version_id)
        if args.name and args.name != name:
            return [], "`--name {}` không khớp mã {} (tên dataset trong mã là {}).".format(
                args.name, version_id, name)
        found = [item for item in found if item["version"] == version_id]

    if args.where == "raw" and args.name and args.version:
        found = [item for item in found
                 if item["name"] == args.name and item["version"] == args.version]
        if not found:
            available = ["{}@{}".format(item["name"], item["version"]) for item in raw_targets()]
            return [], "Không có dữ liệu gốc `{}` phiên bản `{}`. Đang có:\n  - {}".format(
                args.name, args.version, "\n  - ".join(available) or "(không có)")

    if not found:
        return [], "Bộ lọc không khớp đích nào. Xem đang có gì: python build_report.py --list"
    return found, None


def draw(target, plotlyjs):
    """Vẽ báo cáo của MỘT đích. Trả về đường dẫn file HTML, hoặc None nếu thiếu file kết quả."""
    directory = target["directory"]
    path = result_io.result_path(directory, target["phase"])
    if not path.is_file():
        return None
    payload = result_io.read_result(path)
    html_path = render.write_reports(payload, directory, plotlyjs=plotlyjs)
    print("  - [{}] {} -> {}".format(
        target_label(target), PHASE_LABELS[target["phase"]], _rel(html_path)))
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
    """In đang có gì trên đĩa, kèm LỆNH COPY ĐƯỢC cho từng đích.

    Đây là cách khỏi phải nhớ hash8: mở bảng này rồi dán đúng lệnh của đích cần vẽ.
    """
    print("Dataset đã xử lý trong {}:".format(_rel(paths.data("processed"))))
    datasets = versioning.dataset_dirs()
    if not datasets:
        print("  (chưa có)")
    for path in datasets:
        log = versioning.read_processing_log(path.name)
        after = (log.get("record_counts") or {}).get("after") or {}
        total = sum(after.values()) if after else ""
        print("  - {:<46} {}".format(path.name, "{} dòng".format(total) if total else ""))

    for phase, title in (("eda", "Đích EDA"), ("pipeline", "Đích pipeline")):
        found = targets(phase=phase)
        print("\n{} ({}):".format(title, len(found)))
        for item in found:
            ready = result_io.result_path(item["directory"], item["phase"]).is_file()
            print("  [{}] {}".format(
                target_label(item), "có kết quả" if ready else "CHƯA có kết quả"))
            print("      {}".format(_rel(item["directory"])))
            print("      -> {}".format(target_command(item)))
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)

    print("BUILD REPORT - vẽ báo cáo từ file kết quả")

    # Cú pháp ĐÃ BỎ thì báo rõ cách thay thế, thay vì để argparse nói "unrecognized arguments".
    removed = removed_flag_message(argv)
    if removed:
        print("LỖI: {}".format(removed))
        return 2

    args = parse_args(argv)

    if args.list:
        return list_versions()

    print("Thư viện vẽ: {}".format(args.plotlyjs))

    # Gõ sai tên dataset: dừng ngay kèm gợi ý tên đúng, thay vì báo "chưa có file kết quả".
    if args.name and not check_dataset(args.name):
        return 2

    plan, mistake = plan_targets(args)
    if mistake:
        print("LỖI: {}".format(mistake))
        return 2

    print("\nĐích sẽ vẽ ({}):".format(len(plan)))
    for item in plan:
        ready = result_io.result_path(item["directory"], item["phase"]).is_file()
        print("  [{}] {}{}".format(
            target_label(item), _rel(item["directory"]),
            "" if ready else "   (CHƯA có kết quả)"))

    written, skipped = [], []
    for item in plan:
        html_path = draw(item, args.plotlyjs)
        if html_path:
            written.append(html_path)
        else:
            skipped.append(item)

    if skipped:
        print("\nCHƯA CÓ KẾT QUẢ ({} đích) - chạy trước rồi vẽ lại:".format(len(skipped)))
        for item in skipped:
            print("  [{}] {}".format(target_label(item), _rel(item["directory"])))
            print("      chạy trước: {}".format(item["producer"]))

    if not written:
        print("\nKhông vẽ được báo cáo nào.")
        return 1

    print("\nĐã vẽ {} báo cáo (Ctrl+Click để mở, hoặc chạy lại với --open):".format(
        len(written)))
    for path in written:
        print("  {}".format(Path(path).resolve().as_uri()))
        print("    {}".format(_rel(path)))
    if args.open_browser:
        open_reports(written)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
