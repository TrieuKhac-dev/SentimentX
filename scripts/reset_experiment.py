# -*- coding: utf-8 -*-
"""Dọn nơi GHI NHẬN trên MLflow của DagsHub: xoá run, hoặc xoá cả experiment, để lượt chạy sau
đếm lại từ đầu.

VÌ SAO CÓ SCRIPT NÀY
Mục Experiments là nơi ghi nhận, KHÔNG phải nơi lưu bằng chứng: kết quả thật nằm trong
`experiments/**/results/<hash8>/` và trong git. Vì vậy dọn sạch nơi ghi nhận không làm mất kết quả.
Hai đường sẵn có không đủ: `smoke_tracking.py --clean` chỉ xoá run mang nhãn `smoke=true`, còn
`--delete` chỉ nhận `run_id` - trong khi cột người dùng NHÌN THẤY trên giao diện DagsHub là runName.

CÁCH DÙNG
    python scripts/reset_experiment.py --dry-run                    # liệt kê run, KHÔNG xoá gì
    python scripts/reset_experiment.py                              # xoá HẾT run -> xoá experiment
    python scripts/reset_experiment.py --keep-experiment            # chỉ xoá HẾT run, giữ experiment
    python scripts/reset_experiment.py --run 07637bcf --yes         # xoá chọn lọc theo RUN NAME
    python scripts/reset_experiment.py --run <mã run đầy đủ> --yes  # hoặc theo run_id
    python scripts/reset_experiment.py --experiment <tên> --dry-run # đổi đích

Có `--run` thì script CHỈ đụng tới những run đó và KHÔNG xoá experiment - dọn vài run không được
phép kéo theo việc mất cả experiment.

runName khác run_id: runName của dự án là tên thư mục kết quả (`<hash8>`, 8 ký tự hex, ví dụ
`07637bcf`), đặt trong `mlflow_tracker.begin`; run_id là mã dài của máy chủ. Cột `--run` nhận cả hai
vì người chạy đọc được runName trên giao diện, còn `run.log` thì ghi run_id.

runName KHÔNG duy nhất: chạy lại (hoặc chạy tiếp) cùng một thư mục kết quả sinh NHIỀU run cùng tên.
Vì vậy `--run <tên>` có thể khớp nhiều run - script in số run khớp cho từng tên trước khi xoá, và muốn
chắc chắn đúng MỘT run thì dùng `run_id`.

CẢNH BÁO
1. ĐỪNG đổi tên experiment nếu còn muốn so sánh số cũ: khoá `tracking.experiment` nằm trong phần băm
   `config_sha256` (`IDENTITY_SKIP_KEYS` chỉ có `notes`), nên đổi tên là đổi thư mục kết quả. Cứ xoá
   rồi để lượt chạy sau tự tạo lại CÙNG TÊN.
2. Không xoá được gì trên đĩa: script chỉ gọi máy chủ, không chạm `data/` hay `experiments/`.
3. MLflow >= 3 xoá MỀM (run vào thùng rác, `restore_run` phục hồi được); mlflow 2.x xoá thẳng khỏi
   danh sách. Script in phiên bản mlflow đang dùng để không phải đoán.
4. Nếu tên experiment chưa có, thư viện `mlflow` TỰ TẠO một experiment cùng tên khi mở kết nối; khi đó
   số run bằng 0 và script dừng (mã thoát 1) để bạn kịp nhận ra tên bị gõ sai.

MÃ THOÁT
    0 xong (kể cả khi xoá chọn lọc bằng `--run`) · 1 người dùng trả lời KHÔNG, hoặc chưa có run nào ·
    2 câu lệnh chưa rõ (tổ hợp cờ), hoặc không tra được máy chủ (thiếu token/mlflow/mạng), hoặc tên
    run không khớp run nào, hoặc có run xoá lỗi.

CHẠY Ở MÁY KHÁC
Không viết cứng đường dẫn nào (mọi thứ theo `src/core/paths.py`), không cần GPU/model/dữ liệu, và
`runtime.load_env()` nạp token theo đúng thứ tự của dự án (Colab Secrets -> `env/.env.colab` ->
`os.environ` -> `.env` gốc repo). Cần: bản clone đầy đủ của repo, thư viện `mlflow`, mạng tới DagsHub,
và token có QUYỀN XOÁ.
"""

import argparse
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

from src import tracking
from src.experiments import experiments
from src.tracking import base as tracking_base
from src.workflow import runtime


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Xoá run hoặc experiment trên MLflow của DagsHub.")
    parser.add_argument("--experiment", dest="experiment_name", default=None,
                        help="Ghi đè tên experiment trên máy chủ.")
    parser.add_argument("--run", nargs="+", metavar="RUN_NAME|RUN_ID", default=None,
                        help="Chỉ xoá các run này (theo runName hoặc run_id); không xoá experiment.")
    parser.add_argument("--keep-experiment", action="store_true",
                        help="Chỉ xoá run, giữ lại experiment.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Chỉ liệt kê run sẽ xoá, không xoá gì.")
    parser.add_argument("--yes", action="store_true",
                        help="Không hỏi xác nhận.")
    return parser.parse_args(argv)


def check_args(args):
    """Tổ hợp cờ chưa rõ -> câu giải thích; hợp lệ -> None.

    Trả về CHUỖI (không tự in, không tự thoát) để `tests/workflow/test_cli.py` kiểm được mà không
    phải chạy mạng.
    """
    if args.dry_run and args.yes:
        return ("chưa rõ: `--dry-run` chỉ xem trước nên không đi với `--yes`; "
                "bỏ `--yes` để xem trước, hoặc bỏ `--dry-run` để xoá thật.")
    if args.run and args.keep_experiment:
        return ("chưa rõ: `--run` chỉ xoá run nên không đụng tới experiment, "
                "nên `--keep-experiment` là thừa; bỏ một trong hai cờ.")
    return None


def text_of(row, key):
    """Một ô của dòng `search_runs` thành chuỗi; ô thiếu hoặc không phải chuỗi thì trả về rỗng."""
    value = row.get(key)
    return value if isinstance(value, str) else ""


def run_id_of(row):
    value = row.get("run_id")
    return "" if value is None else str(value)


def run_name_of(row):
    """runName của run - tên thư mục kết quả (`<hash8>`), cũng là cột hiện trên giao diện DagsHub."""
    return text_of(row, "tags.mlflow.runName")


def started_at(row):
    """Thời điểm bắt đầu, đủ để phân biệt các lượt chạy cùng tên."""
    value = row.get("start_time")
    write = getattr(value, "strftime", None)
    if callable(write):
        return write("%Y-%m-%d %H:%M")
    return str(value or "")[:16]


def describe(rows):
    """Bảng run để in TRƯỚC khi xoá: đúng những gì người chạy thấy trên DagsHub."""
    lines = []
    for index, (_position, row) in enumerate(rows):
        lines.append("  {:>3}. runName {:<10}  run_id {}  {:<10}  {}".format(
            index + 1, run_name_of(row) or "-", run_id_of(row),
            text_of(row, "status") or "-", started_at(row)))
    return lines


def select(rows, wanted):
    """Lọc run theo runName HOẶC run_id. Trả về (các dòng khớp, các giá trị không khớp)."""
    matched, missing = [], []
    for value in wanted:
        needle = str(value).strip()
        found = [(index, row) for index, row in rows
                 if needle and needle in (run_name_of(row), run_id_of(row))]
        if found:
            matched.extend(found)
        else:
            missing.append(needle)
    # Cùng một run có thể khớp hai lần (vừa đúng runName vừa đúng run_id): giữ theo run_id.
    unique, seen = [], set()
    for index, row in matched:
        key = run_id_of(row) or str(index)
        if key not in seen:
            seen.add(key)
            unique.append((index, row))
    return unique, missing


def confirm(question):
    """Hỏi trước khi xoá. Không hỏi được (phiên không tương tác) thì coi như KHÔNG."""
    try:
        answer = input("{} [y/N] ".format(question))
    except EOFError:
        return False
    return answer.strip().lower() in ("y", "yes", "c", "co", "có")


def match_counts(rows, wanted):
    """Số run khớp với TỪNG giá trị của `--run`.

    Cần in ra vì runName KHÔNG duy nhất: cùng một tên có thể ứng với nhiều run (chạy lại, chạy tiếp
    cùng một thư mục kết quả), nên `--run <tên>` có thể xoá nhiều hơn một run. Im lặng ở đây là chỗ
    dễ xoá nhầm nhất.
    """
    counts = []
    for value in wanted:
        needle = str(value).strip()
        counts.append((needle, sum(
            1 for _index, row in rows
            if needle and needle in (run_name_of(row), run_id_of(row)))))
    return counts


def experiments_on_server(mlflow):
    """Tên các experiment đang có - để nhận ra tên bị gõ sai. Lỗi thì trả về danh sách rỗng."""
    try:
        search = getattr(mlflow, "search_experiments", None)
        found = search() if callable(search) else mlflow.list_experiments()
    except Exception:  # noqa: BLE001 - đây chỉ là thông tin thêm, không được làm hỏng việc chính
        return []
    return sorted(str(getattr(item, "name", "") or "") for item in found)


def runs_of(mlflow, experiment):
    """Các run của experiment, mới nhất trước. Trả về danh sách dòng của `search_runs`."""
    frame = mlflow.search_runs(experiment_ids=[experiment.experiment_id])
    try:
        frame = frame.sort_values(by="start_time", ascending=False)
    except Exception:  # noqa: BLE001 - thiếu cột thì giữ nguyên thứ tự máy chủ trả về
        pass
    return list(frame.iterrows())


def check_ready(config, dagshub):
    """Tra kết nối. Trả về (module mlflow, câu lỗi); một trong hai là None."""
    try:
        tracking.check(config, dagshub)
    except tracking_base.TrackingError as exc:
        return None, str(exc)
    from src.tracking import mlflow_tracker
    try:
        return mlflow_tracker.connect(config, dagshub), None
    except Exception as exc:  # noqa: BLE001 - chưa mở được thì báo, không để traceback
        return None, "không mở được kết nối tới {} ({}: {})".format(
            dagshub.get("mlflow_uri"), type(exc).__name__, exc)


def main(argv=None):
    args = parse_args(argv)
    problem = check_args(args)
    if problem:
        print(problem)
        return 2

    # Nạp token TRƯỚC khi đọc cấu hình: `DAGSHUB_TOKEN` nằm ở Colab Secrets hoặc file env, không
    # nằm trong repo (xem docs/05_config/07_env.md).
    env = runtime.load_env()
    print("RESET - dọn nơi ghi nhận trên MLflow (KHÔNG chạm dữ liệu và thư mục kết quả)")
    print("Máy đang chạy : {}".format(env["env"]))
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
    if args.experiment_name:
        config["experiment"] = args.experiment_name
    experiment_name = str(config.get("experiment") or "").strip()

    mlflow, failure = check_ready(config, dagshub)
    if failure:
        print("\nKẾT LUẬN: CHƯA - {}".format(failure))
        return 2

    print("Máy chủ MLflow: {}".format(dagshub.get("mlflow_uri")))
    print("Thư viện      : mlflow {}".format(getattr(mlflow, "__version__", "?")))
    print("Experiment    : '{}'".format(experiment_name))
    print("Xoá của mlflow: {} (>= 3 là xoá MỀM - run còn trong thùng rác, phục hồi được)".format(
        "mềm" if str(getattr(mlflow, "__version__", "0")).split(".")[0] >= "3" else "thẳng"))

    experiment = mlflow.get_experiment_by_name(experiment_name)
    if experiment is None:
        print("\nKẾT LUẬN: CHƯA - chưa có experiment '{}' trên máy chủ".format(experiment_name))
        return 2
    rows = runs_of(mlflow, experiment)
    if not rows:
        print("\nExperiment '{}' đang có 0 run.".format(experiment_name))
        others = [name for name in experiments_on_server(mlflow) if name != experiment_name]
        if others:
            print("Các experiment khác đang có: {}".format(", ".join(others)))
        print("Không xoá gì. Nếu tên vừa gõ bị sai thì thư viện mlflow đã tự tạo một experiment")
        print("rỗng cùng tên đó khi mở kết nối - xoá nó trên giao diện DagsHub.")
        print("\nKẾT LUẬN: CHƯA - chưa có run nào để xoá")
        return 1

    targets, missing = rows, []
    if args.run:
        targets, missing = select(rows, args.run)
        if missing:
            print("\nKhông khớp run nào: {}".format(", ".join(missing)))
            print("Các runName đang có:")
            for line in describe(rows):
                print(line)
            print("\nKẾT LUẬN: CHƯA - tên run không khớp run nào trên máy chủ")
            return 2
        repeated = [(needle, count) for needle, count in match_counts(rows, args.run) if count > 1]
        if repeated:
            print("\nLưu ý: runName KHÔNG duy nhất trên máy chủ:")
            for needle, count in repeated:
                print("  '{}' khớp {} run (muốn đúng MỘT run thì dùng run_id)".format(needle, count))

    print("\nSẽ xoá {} run:".format(len(targets)))
    for line in describe(targets):
        print(line)
    if not args.run:
        print("  (đây là TOÀN BỘ run của experiment)")
        if args.keep_experiment:
            print("Experiment '{}' được GIỮ LẠI (--keep-experiment).".format(experiment_name))
        else:
            print("Xoá hết run xong sẽ xoá LUÔN experiment '{}'.".format(experiment_name))

    if args.dry_run:
        print("\nKẾT LUẬN: ĐẠT - chỉ xem trước (--dry-run), chưa xoá gì")
        return 0

    if not args.yes and not confirm("Xoá {} run?".format(len(targets))):
        print("\nKẾT LUẬN: CHƯA - bạn trả lời KHÔNG, không xoá gì")
        return 1

    from src.tracking import mlflow_tracker
    deleted, problems = mlflow_tracker.delete_runs(targets)
    print("\nĐã xoá {} / {} run.".format(deleted, len(targets)))
    for item in problems:
        print("  lỗi: {}".format(item))

    if problems:
        print("\nKẾT LUẬN: CHƯA - còn {} run xoá lỗi nên KHÔNG xoá experiment; chạy lại sau".format(
            len(problems)))
        return 2

    if args.run or args.keep_experiment:
        print("\nExperiment '{}' vẫn còn ({}).".format(
            experiment_name, "--run chỉ xoá run" if args.run else "--keep-experiment"))
        print("Lượt chạy sau sẽ NỐI vào experiment này, không phải tạo mới.")
        print("\nKẾT LUẬN: ĐẠT - đã xoá {} run".format(deleted))
        return 0

    try:
        mlflow.delete_experiment(experiment.experiment_id)
    except Exception as exc:  # noqa: BLE001 - báo rõ, không để traceback
        print("  lỗi xoá experiment: {}: {}".format(type(exc).__name__, exc))
        print("\nKẾT LUẬN: CHƯA - đã xoá run nhưng chưa xoá được experiment")
        return 2
    print("Đã xoá experiment '{}'.".format(experiment_name))
    print("Lượt chạy sau tự tạo lại CÙNG TÊN - đừng đổi `tracking.experiment` trong")
    print("configs/experiments/tracking.yaml, vì tên nằm trong config_sha256 (đổi là đổi thư mục kết quả).")
    print("\nKẾT LUẬN: ĐẠT - nơi ghi nhận đã sạch")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
