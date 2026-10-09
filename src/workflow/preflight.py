# -*- coding: utf-8 -*-
"""Kiểm TRƯỚC khi chạy: mọi thứ phải đúng thì mới tiêu hàng chục phút GPU.

VÌ SAO PHẢI CÓ
Một lượt val tốn hàng chục phút. Phát hiện thiếu Java, thiếu `test.csv` hay Drive chỉ đọc ở mẫu
thứ 800 thì đã muộn, mà Colab thì hết thời gian trước khi chạy xong. Mọi thứ ở đây kiểm được
trong vài giây và kiểm TRƯỚC khi nạp model.

KIỂM NHỮNG GÌ
    1. Cấu hình thí nghiệm hợp lệ (`experiments.check`): khoá lạ, `data.roles` thiếu, nhiều dataset
    2. Đường dẫn thí nghiệm cần có thật (`experiments.check_requires`): dữ liệu, bảng mã nhãn, prompt
    3. Dataset đã xử lý tồn tại, và mã phiên bản tính từ config khớp mã đang dùng
    4. `test.csv` khớp khoá tập đánh giá (rules.md mục 11): lệch TẬP BẢN GHI
       (`records_sha256`) thì kết quả không so được với công bố; lệch cách ghi file (`sha256`)
       chỉ là ghi chú - xem `eval_lock_report`
    5. Thiết bị: có GPU không, `inference.quantization` khai trong model config có dùng được không
    6. Bộ tách từ mà model cần (ví dụ `vncorenlp` cần Java) chạy được trên máy này không
    7. Ghi được vào gốc kết quả (trên Colab: Drive chưa mount thì chỉ đọc)
    8. Trạng thái NEW, RESUME hay STOP, và lí do - dùng chung `src/workflow/resume.py` với lúc chạy thật

CÁCH BÁO
`run()` KHÔNG ném: nó gom hết vấn đề vào `problems` để notebook in ra một lần, kèm cả những việc
KHÔNG chặn chạy (`notes`). Muốn dừng ngay thì gọi `check()`, nó ném `PreflightError` với đủ danh
sách. Lỗi thiếu đường dẫn còn được ghi vào `errors.json` mục `requires` nếu có truyền `log`.
"""

import csv
import importlib.util
from pathlib import Path

from src.core import dataset as dataset_module
from src.experiments import experiments, model_config
from src.core import paths, utils, versioning
from src.workflow import resume, runtime
from src import training
from src.training import checkpoints
from src.preprocessing import segmenters
from src.tracking import run_meta


class PreflightError(Exception):
    """Có vấn đề phải sửa trước khi chạy."""


def _collect(problems, notes, label, function, *args, **kwargs):
    """Gọi một phép kiểm và gom lỗi của nó lại, để báo MỘT LẦN đủ mọi vấn đề."""
    try:
        result = function(*args, **kwargs)
        return result
    except Exception as exc:  # noqa: BLE001 - mỗi phép kiểm ném kiểu lỗi riêng
        problems.append("[{}] {}".format(label, exc))
        return None


def writable(path, label, problems, notes):
    """Kiểm ghi được vào một thư mục. Trên Colab, Drive chưa mount thì thư mục chỉ đọc."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".sentimentx-write-test"
        probe.write_text("x", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        problems.append("Không ghi được vào {} ({}): {}".format(label, utils.rel(path), exc))
        return False
    notes.append("{}: ghi được ({})".format(label, utils.rel(path)))
    return True


def _newest_version(ds):
    """Tên bản MỚI NHẤT của dataset mà `ds` thuộc về; None nếu không đọc được.

    Dùng để NÓI THÊM khi thí nghiệm khai một bản không phải bản mới nhất (xem `version_report`).
    """
    name = (ds or {}).get("name")
    if not name:
        return None
    try:
        found = dataset_module.versions(name)
    except Exception:                                     # noqa: BLE001 - chỉ để nói thêm
        return None
    return found[-1] if found else None


def version_report(ds, version_id, want_version, problems, notes, info):
    """Kiểm mã phiên bản dữ liệu: khớp config, và dataset đã được pipeline tạo chưa.

    `want_version` là `data.version` mà THÍ NGHIỆM khai - và đó là bản ĐỂ ĐỌC, không phải "bản mới
    nhất". Giữ một bản cũ là chuyện hợp lệ: mọi phép ablation đều phải so với kết quả cũ, mà kết quả
    cũ chấm trên đúng bản dữ liệu cũ; và phép đo ảnh hưởng của một thay đổi trong khâu xử lý (bỏ
    emoji chẳng hạn) cần HAI phiên bản sống cạnh nhau - nếu chỉ bản mới nhất được phép thì phép đo
    đó không viết ra được. Nên ở đây KHÔNG chặn bản cũ; chỗ phải chặn - khai một bản KHÔNG TỒN TẠI -
    đã bị `dataset.load_config` chặn, với thông báo kèm danh sách bản đang có. Việc của hàm này là
    nói ra đang đọc bản nào, để không ai lặng lẽ chấm trên bộ dữ liệu cũ.
    """
    computed = _collect(problems, notes, "mã phiên bản",
                        versioning.compute_id, ds)
    info["version_id"] = version_id or computed
    if computed and version_id and computed != version_id:
        problems.append(
            "Mã phiên bản đang dùng ({}) khác mã tính từ config ({}) - đang chấm trên bộ dữ liệu "
            "không phải bộ config nói.".format(version_id, computed))
    if want_version and ds and str(ds.get("version") or "") != str(want_version):
        # `run()` nạp `ds` THEO `data.version`, nên tới đây hai giá trị chỉ lệch khi nơi gọi TỰ
        # truyền vào một `ds` của bản khác - hai nguồn sự thật cho cùng một lượt chạy, phải dừng.
        problems.append(
            "Thí nghiệm khai `data.version` {} nhưng `ds` truyền vào là bản {}. Hai giá trị này "
            "phải trùng: lượt chạy đang đọc một phiên bản khác với bản đã khai.".format(
                want_version, ds.get("version")))
    elif want_version:
        newest = _newest_version(ds)
        if newest and str(newest) != str(want_version):
            notes.append(
                "dữ liệu: đọc bản thí nghiệm khai (`data.version` {}), KHÔNG phải bản mới nhất "
                "({}) - đúng khi so với kết quả cũ đã chạy trên bản đó; nếu không cố ý thì sửa "
                "`data.version`.".format(want_version, newest))
    folder = paths.processed(info["version_id"] or "")
    if info["version_id"] and folder.is_dir():
        notes.append("dataset: {}".format(utils.rel(folder)))
    else:
        # Kể luôn những mã đang có trong `data/processed/`: mã phiên bản tính từ nội dung file gốc,
        # nên một bộ dữ liệu cũ (trên Drive chẳng hạn) cho ra mã khác, và thông báo "chưa có dataset"
        # mà không nói mình đang có mã nào là ngõ cụt - người đọc không biết lệch ở đâu.
        parent = paths.data("processed")
        others = sorted(path.name for path in parent.iterdir() if path.is_dir()) \
            if parent.is_dir() else []
        problems.append(
            "Chưa có dataset đã xử lý ở {}.{} Tạo bằng: {}".format(
                utils.rel(folder),
                " Thư mục đang có: {}.".format(", ".join(others)) if others else "",
                pipeline_command(ds)))
    return info["version_id"]


def pipeline_command(ds):
    """Lệnh tạo dữ liệu đã xử lý, in đủ tham số để COPY DÁN LÀ CHẠY ĐƯỢC.

    `run_pipeline.py` bắt buộc có `--version` (mỗi phiên bản cho ra một bộ dữ liệu khác nhau), nên
    lời khuyên thiếu tham số là lời khuyên chạy ra lỗi ngay. Đã gặp trên Colab: preflight in
    "chạy `python run_pipeline.py` trước", người chạy dán vào và nhận `error: the following
    arguments are required: --version`.
    """
    name = (ds or {}).get("name") or "<tên dataset>"
    version = (ds or {}).get("version") or "<phiên bản>"
    return "`python run_pipeline.py --name {} --version {}`".format(name, version)


def _raw_paths(ds):
    """Các file dữ liệu gốc mà config dataset khai, KỂ CẢ file chưa có trên đĩa."""
    names = [str(name) for name in ((ds or {}).get("splits") or {}).values()]
    if (ds or {}).get("full"):
        names.append(str(ds["full"]))
    found = []
    for source in (ds or {}).get("_sources") or []:
        if source.get("kind") == "raw":
            found.extend(Path(source["dir"]) / name for name in names)
    return found


def raw_source_report(ds, problems, notes, info):
    """Dữ liệu GỐC của nguồn `raw` phải có đủ trước khi chạy pipeline.

    Vì sao kể riêng chứ không gộp vào việc "chạy pipeline trước": thiếu dữ liệu gốc thì lời khuyên
    đó vô dụng, pipeline có chạy cũng hỏng. Đây cũng là việc hay gặp nhất trên Colab, vì dữ liệu gốc
    KHÔNG nằm trong git (luật 20): người chạy phải đưa nó lên (mount Drive, hoặc tải tay), không có
    lệnh nào tự tải hộ.

    Việc này được chèn lên ĐẦU danh sách: nó là nguyên nhân gốc, còn "chưa có dataset đã xử lý" và
    "thiếu tập đánh giá" chỉ là hệ quả - đọc theo thứ tự ngược thì người sửa đi sai đường.
    """
    declared = _raw_paths(ds)
    info["raw_missing"] = []
    if not declared:
        return None
    missing = [path for path in declared if not path.exists()]
    info["raw_missing"] = [utils.rel(path) for path in missing]
    if not missing:
        notes.append("dữ liệu gốc: đủ ({} file)".format(len(declared)))
        return None
    if runtime.is_colab():
        remedy = ("Trên Colab dữ liệu gốc KHÔNG nằm trong git: mount Drive hoặc tải thư mục dữ liệu "
                  "lên, rồi chạy {}.".format(pipeline_command(ds)))
    else:
        remedy = "Có dữ liệu gốc rồi thì chạy {}.".format(pipeline_command(ds))
    problems.insert(0, "Thiếu {} file dữ liệu GỐC của dataset {}:\n      {}\n      {}".format(
        len(missing), (ds or {}).get("name") or "?",
        "\n      ".join(info["raw_missing"]), remedy))
    return info["raw_missing"]


def raw_fingerprint_report(ds, version_id, problems, notes, info):
    """Nội dung file GỐC phải khớp dấu vân tay đã ghi khi dựng dataset.

    Vì sao cần: mã phiên bản dữ liệu được tính từ NỘI DUNG các file gốc, nên một bộ dữ liệu bị sửa
    (mở bằng Excel, lưu lại bằng công cụ khác, tải lên qua đường có sửa file) sinh ra mã khác, và
    thông báo "chưa có dataset đã xử lý" không nói được file nào đã đổi.

    Băm qua `versioning.file_sha256` (tức `utils.digest_bytes`, có chuẩn hoá kiểu xuống dòng), nên
    CRLF so với LF KHÔNG bị coi là lệch - đúng bằng phép băm mà mã phiên bản dùng. Nhờ vậy thông báo
    chỉ kể ra file thật sự bị SỬA.
    """
    log = versioning.read_processing_log(version_id) if version_id else {}
    recorded = {}
    for source in ((log.get("dataset") or {}).get("sources") or []):
        for item in source.get("files") or []:
            if item.get("name") and item.get("sha256"):
                recorded[str(item["name"])] = str(item["sha256"])
    if not recorded:
        return None

    wrong, missing, checked = [], [], 0
    for source in (ds or {}).get("_sources") or []:
        if source.get("kind") != "raw":
            continue
        folder = Path(source["dir"])
        for name, expected in sorted(recorded.items()):
            path = folder / name
            if not path.is_file():
                missing.append(name)
                continue
            checked += 1
            measured = versioning.file_sha256(path)
            if measured != expected:
                wrong.append("{}: lúc dựng dataset {}, hiện tại {} ({})".format(
                    name, expected[:12], measured[:12], utils.rel(path)))
    info["raw_checked"] = checked
    if missing:
        problems.append("Dữ liệu gốc thiếu file so với lúc dựng dataset: {}.".format(
            ", ".join(missing)))
    if wrong:
        problems.append(
            "Nội dung dữ liệu gốc đã ĐỔI so với bản dùng để dựng dataset ({} file):\n      {}\n"
            "      Nội dung file gốc đi vào mã phiên bản dữ liệu, nên dữ liệu đã sửa là mã khác và kết "
            "quả không so được với công bố. Đưa lại đúng bộ dữ liệu gốc.".format(
                len(wrong), "\n      ".join(wrong)))
    elif checked:
        notes.append("dữ liệu gốc: khớp {} file với dấu vân tay lúc dựng dataset".format(checked))
    return wrong


def count_rows(path):
    """Số BẢN GHI của một file CSV, không phải số dòng.

    Vì sao không đếm dòng: review trong bộ dữ liệu này có xuống dòng BÊN TRONG ô được trích dẫn, nên
    đếm dòng cho ra 2271 trong khi tập test chỉ có 1518 bản ghi - và con số sai đó được ghi vào
    `eval_lock` của file phiên bản dataset, tức là lưu lại lâu dài rồi không ai dò lại được.
    Đọc bằng `csv.reader` với `newline=""` xử lý đúng ô nhiều dòng, trên mọi hệ điều hành.
    """
    with open(path, "r", encoding="utf-8", newline="") as handle:
        return max(0, sum(1 for _ in csv.reader(handle)) - 1)


def eval_lock_report(ds, version_id, problems, notes, info):
    """Kiểm tập đánh giá khớp khoá: đổi tập test là mất quyền so với công bố tham chiếu.

    HAI DẤU VÂN TAY, HAI MỨC
    - `records_sha256` (khoá, xem `versioning.records_sha256`): vân tay của TẬP BẢN GHI. Lệch là LỖI,
      vì nội dung đánh giá đã khác - hết quyền so với công bố.
    - `sha256` (dấu vân tay BYTE của file): lệch chỉ là GHI CHÚ - dữ liệu y nguyên, chỉ cách ghi file
      đổi (đã xảy ra thật 25/09/2026). Giữ cả hai để vẫn truy vết được bản đã công bố, và để bản code
      cũ (đã ghim trong notebook, chỉ biết `sha256`) không bị mất guard.

    Một ngoại lệ của mức "ghi chú": giá trị **KHAI trong file phiên bản dataset** (dùng khi đối chiếu
    với một tập test bên ngoài) là giao kèo cứng - khai `sha256` mà byte lệch thì vẫn là LỖI, kể cả khi
    tập bản ghi khớp; muốn chỉ ràng buộc dữ liệu thì khai `records_sha256`.

    Khoá đọc theo thứ tự: giá trị khai trong file phiên bản dataset (nếu có - dùng khi muốn đối chiếu
    với một tập test bên ngoài), rồi tới khoá ĐÃ GHI cùng dữ liệu
    (`data/processed/<mã>/eval_lock.json`) - khoá này có từ bản dữ liệu ĐẦU TIÊN, nên bản v0 cũng
    được kiểm, không phải chờ phiên bản sau.
    """
    lock = dict((ds or {}).get("eval_lock") or {})
    declared = dict(lock.get("test") or {})
    path = paths.processed(version_id or "") / str(declared.get("file") or "test.csv")
    if not path.is_file():
        problems.append("Thiếu tập đánh giá {} (dataset chưa được pipeline tạo?).".format(
            utils.rel(path)))
        return None
    measured = {"file": path.name, "sha256": versioning.file_sha256(path),
                "rows": count_rows(path)}
    aspects = _locked_split_aspects(version_id, notes)
    if aspects:
        try:
            measured["records_sha256"] = versioning.records_sha256(path, aspects)
        except versioning.VersionError as exc:
            problems.append(str(exc))
            return measured
    info["test"] = measured

    if not lock.get("enforce", True):
        notes.append("`eval_lock.enforce` đang TẮT: tập test có thể bị đổi mà không ai chặn.")
        info["eval_lock"] = {"enforce": False, "source": ""}
        return measured

    stored = versioning.split_lock(version_id, Path(str(declared.get("file") or "test.csv")).stem)
    want_records = declared.get("records_sha256") or stored.get("records_sha256")
    want_bytes = declared.get("sha256") or stored.get("sha256")
    source = "khai trong file phiên bản dataset"
    if not (declared.get("sha256") or declared.get("records_sha256")):
        source = "ghi cùng dữ liệu lúc tạo ({})".format(
            utils.rel(versioning.eval_lock_path(version_id or "")))
    info["eval_lock"] = {"enforce": True, "source": source, "sha256": want_bytes,
                         "records_sha256": want_records, "rows": stored.get("rows")}

    if not want_records and not want_bytes:
        notes.append(
            "Chưa có khoá tập đánh giá cho phiên bản này. Chạy pipeline để tạo khoá (nó ghi "
            "{} trong cùng lần chạy sinh ra test.csv): `python run_pipeline.py --name <tên> "
            "--version <phiên bản>`.".format(utils.rel(versioning.eval_lock_path(version_id or ""))))
        return measured

    records_match = None
    if want_records and measured.get("records_sha256"):
        records_match = str(want_records) == measured["records_sha256"]
    bytes_match = str(want_bytes) == measured["sha256"] if want_bytes else None

    if records_match is False:
        problems.append(
            "{} KHÔNG khớp khoá tập đánh giá ({}): tập bản ghi đã ghi {}, đo được {}. Nội dung đánh "
            "giá đã thay đổi nên kết quả không so được với công bố tham chiếu.".format(
                measured["file"], source, want_records, measured["records_sha256"]))
        return measured
    if records_match is None and bytes_match is False:
        # Khoá cũ chưa có vân tay dữ liệu (hoặc không đọc được bảng mã nhãn): giữ mức so cũ.
        problems.append(
            "{} KHÔNG khớp khoá tập đánh giá ({}): đã ghi {}, đo được {}. Tập đánh giá đã thay đổi "
            "nên kết quả không so được với công bố tham chiếu.".format(
                measured["file"], source, want_bytes, measured["sha256"]))
        return measured

    if bytes_match is False and declared.get("sha256"):
        # Giá trị KHAI trong file phiên bản là giao kèo với một file bên ngoài (ví dụ tập test của
        # công bố): phải khớp từng byte. Khác với `sha256` ĐÃ GHI cùng dữ liệu - đó chỉ là dấu vết của
        # lần chạy trước, nên lệch byte ở đó chỉ là ghi chú.
        problems.append(
            "{} KHÔNG khớp giá trị khai trong file phiên bản dataset: `sha256` khai {}, đo được {}{}. "
            "Nếu chỉ cần khớp DỮ LIỆU thì khai `records_sha256` (đo được {}) thay cho `sha256`.".format(
                measured["file"], declared.get("sha256"), measured["sha256"],
                " (tập bản ghi thì khớp)" if records_match else "",
                measured.get("records_sha256", "")))
        return measured

    if bytes_match is False:
        notes.append(
            "{}: định dạng ghi của file đã đổi (`sha256` đã ghi {}, đo được {}) nhưng TẬP BẢN GHI "
            "không đổi ({} bản ghi) - vẫn so được với công bố.".format(
                measured["file"], str(want_bytes)[:8], measured["sha256"][:8], measured["rows"]))
        return measured

    if want_records and not measured.get("records_sha256"):
        # Không được báo "khớp" khi thứ quyết định lại chưa đối chiếu được: nói rõ chỉ kiểm được byte.
        notes.append(
            "{}: khoá có vân tay tập bản ghi nhưng CHƯA tính được vân tay hiện tại (thiếu "
            "`label_map.json`?) nên chỉ đối chiếu được byte `sha256`.".format(measured["file"]))
        return measured
    notes.append("{} khớp khoá tập đánh giá ({} dòng; {} bản ghi; {}).".format(
        measured["file"], measured["rows"], measured.get("records_sha256", "")[:8], source))
    return measured


def _locked_split_aspects(version_id, notes):
    """Danh sách aspect của phiên bản, để tính dấu vân tay tập bản ghi.

    Không đọc được `label_map.json` thì VẪN kiểm được bằng dấu vân tay byte (như trước): thiếu file
    này là chuyện của "chưa chạy pipeline", và preflight không nên nổ vì nó.
    """
    from src.preprocessing import loader
    try:
        return list(loader.load_label_map(version_id)["aspects"])
    except Exception as exc:  # noqa: BLE001 - thiếu/hỏng label_map đều cùng một cách xử lý
        notes.append("Chưa đọc được bảng mã nhãn của {} nên chỉ kiểm dấu vân tay byte: {}".format(
            version_id, exc))
        return []


def device_report(model_id, problems, notes, info):
    """Thiết bị và cách nạp model: có GPU không, lượng hoá khai trong config có dùng được không.

    Hai việc này ĐỘC LẬP với nhau, nên kiểm riêng rồi kể chung: máy thiếu `torch` là một vấn đề,
    thiếu `bitsandbytes` (khi config khai 4-bit) là vấn đề thứ hai - người sửa cần thấy cả hai
    trong cùng một lần chạy preflight, không phải sửa xong cái thứ nhất mới biết có cái thứ hai.
    """
    inference = model_config.inference(model_id) if model_id else {}
    quantization = str(inference.get("quantization") or "").strip().lower() or None
    info["inference"] = dict(inference)
    info["quantization"] = quantization

    # Kiểm lượng hoá TRƯỚC, rồi mới tới torch: nó không phụ thuộc torch, và như vậy một máy thiếu
    # cả hai vẫn được kể đủ hai việc.
    quantization_problem = None
    if quantization == "4bit" and importlib.util.find_spec("bitsandbytes") is None:
        quantization_problem = (
            "Model config khai `inference.quantization: 4bit` nhưng máy chưa có "
            "`bitsandbytes`: pip install bitsandbytes")

    try:
        import torch
    except (ImportError, OSError) as exc:
        # `OSError` là trường hợp CÀI HỎNG (thiếu DLL, hết bộ nhớ trang): báo như một vấn đề kèm
        # lí do, thay vì để ngoại lệ hệ điều hành làm notebook dừng ở giữa.
        problems.append("Không nạp được `torch`: {}: {}. Cài lại bằng:\n"
                        "      pip install torch --index-url "
                        "https://download.pytorch.org/whl/cu126".format(type(exc).__name__, exc))
        if quantization_problem:
            problems.append(quantization_problem)
        info["torch"] = ""
        return info
    info["torch"] = getattr(torch, "__version__", "")
    cuda = bool(torch.cuda.is_available())
    info["cuda"] = cuda
    if cuda:
        info["gpu"] = torch.cuda.get_device_name(0)
        info["vram_gb"] = round(torch.cuda.get_device_properties(0).total_memory / 1024 ** 3, 1)
        notes.append("GPU: {} ({:.1f} GB), torch {}".format(
            info["gpu"], info["vram_gb"], info["torch"]))
    else:
        # Nói luôn TORCH đang là bản gì: trên Colab, "không thấy GPU" gần như luôn là một trong hai
        # chuyện - phiên đang ở chế độ CPU, hoặc torch đã bị cài đè bằng bản CPU. Hai chuyện đó cần
        # hai cách sửa khác nhau, nên thông báo phải phân biệt được.
        build = ("bản CPU" if not getattr(torch.version, "cuda", None)
                 else "bản CUDA {}".format(torch.version.cuda))
        problems.append(
            "Máy KHÔNG thấy GPU (`torch.cuda.is_available()` = False). torch {} ({}), nên model 4B "
            "chạy trên CPU tính bằng ngày. Trên Colab: Runtime > Change runtime type > T4 GPU rồi "
            "Restart session; nếu `!nvidia-smi` CÓ GPU mà torch vẫn không thấy thì torch đã bị cài "
            "đè bằng bản CPU - mở phiên mới thay vì cài lại torch.".format(
                info["torch"], build))

    if quantization == "4bit":
        if quantization_problem:
            problems.append(quantization_problem)
        else:
            notes.append("lượng hoá: 4-bit (đã có bitsandbytes)")
    elif quantization and info.get("vram_gb") and info["vram_gb"] < 8:
        notes.append(
            "Model config khai `quantization: {}` nhưng VRAM chỉ {:.1f} GB: model 4B ở bf16 cần "
            "khoảng 8 GB. Kiểm lại config hoặc dùng máy khoẻ hơn.".format(
                quantization, info["vram_gb"]))

    # 5c. Kiểu số: cùng MỘT hàm giải với lúc chạy (`model_config.resolve_dtype`), nên khai tường minh
    # mà máy không đáp ứng được thì bị chặn NGAY Ở ĐÂY - trước khi tải dữ liệu và nạp model.
    dtype_value = str(inference.get("dtype") or "auto").strip().lower()
    try:
        resolved = model_config.resolve_dtype(dtype_value, "cuda" if cuda else "cpu", torch=torch)
    except ValueError as exc:
        problems.append(str(exc))
    else:
        resolved_name = model_config.dtype_name(resolved)
        notes.append("kiểu số: {} (từ `inference.dtype: {}`)".format(resolved_name, dtype_value))
        if resolved_name == "bfloat16" and not cuda:
            notes.append("bf16 trên CPU chạy được nhưng rất chậm; dùng GPU nếu có.")
    return info


def segmenter_report(model_id, problems, notes, info, segmenter=None):
    """Bộ tách từ mà LƯỢT CHẠY cần: thiếu Java hay thiếu gói thì báo ngay, kèm lí do.

    `segmenter`: giá trị ĐANG DÙNG của lượt chạy (`preprocess.segmenter` trong cấu hình ĐÃ HỢP NHẤT).
    Phải truyền vào vì lớp thí nghiệm ĐÈ được khoá này: đọc thẳng file model thì dòng in ra nói một bộ
    tách từ, còn dữ liệu đưa vào model lại được chia bằng bộ KHÁC - một thông báo sai như vậy làm người
    đọc kết luận nhầm về cả lượt chạy (đã gặp thật ở đợt 11: các lượt khai `preprocess.segmenter` khác
    bộ mặc định của model). Để `None` thì lấy giá trị khai trong file model - hành vi của mọi lượt trước.
    """
    if segmenter is None:
        preprocess = model_config.preprocess(model_id) if model_id else {}
        segmenter = preprocess.get("segmenter")
    name = str(segmenter or "").strip()
    info["segmenter"] = name or None
    if not name or name == "none":
        return None
    module = segmenters.SEGMENTERS.get(name)
    if module is None:
        problems.append(
            "Cấu hình đã hợp nhất khai `preprocess.segmenter: {}` nhưng không có bộ tách từ này. Các "
            "bộ hiện có: {}.".format(name, ", ".join(sorted(segmenters.SEGMENTERS))))
        return None
    available, reason = module.available()
    if not available:
        problems.append("Bộ tách từ '{}' không chạy được trên máy này: {}".format(name, reason))
    else:
        notes.append("bộ tách từ: {} - {}".format(name, module.DESCRIPTION))
    return name


def state_report(out_dir, want, problems, notes, info, force_new=False):
    """NEW, RESUME hay STOP - dùng CHUNG quyết định với lúc chạy thật (`src/workflow/resume.py`)."""
    if not out_dir:
        notes.append("Không truyền `out_dir` nên chưa biết lần này là chạy mới hay chạy tiếp.")
        return None
    parts = resume.Parts(out_dir)
    mode, reason = resume.decide(run_meta.read(out_dir), want, parts.count(),
                                force_new=force_new)
    info["mode"] = mode
    info["mode_reason"] = reason
    info["done_samples"] = parts.count()
    notes.append("trạng thái: {} - {}".format(mode, reason))
    return mode


def run(result, ds=None, version_id=None, out_dir=None, model_id=None, method=None, exp_id=None,
        force_new=False, log=None):
    """Kiểm hết rồi trả về báo cáo. KHÔNG ném: notebook in ra rồi tự quyết định.

    `method`/`exp_id`: khai khi kiểm cho một thí nghiệm - nhờ chúng mà việc kiểm "chạy mới hay chạy
    tiếp" nhìn ĐÚNG thư mục của lượt chạy (`results/<mã>/<hậu tố>/`), không phải thư mục phiên bản.
    """
    from src.workflow import repo

    problems, notes, info = [], [], {}
    config = result.get("config") or {}
    data = dict(config.get("data") or {})
    model_id = model_id or result.get("model_id")

    # 1. Cấu hình thí nghiệm: khoá lạ, thiếu `data.roles`, nhiều dataset, vai trỏ vào train...
    _collect(problems, notes, "cấu hình", experiments.check, result, ds)

    # 2. Config dataset: kiểm luôn ở đây vì mọi phép kiểm sau đều dựa vào nó.
    if ds is None and data.get("dataset"):
        # Nạp THEO `data.version` mà thí nghiệm khai. Không truyền version thì `load_config` lấy
        # bản mới nhất theo tên file, và một thí nghiệm khai v0.2.0 sẽ đọc (rồi chấm trên) bộ dữ
        # liệu v0.3.0 - đúng lỗi im lặng mà `version_report` sinh ra để bắt.
        ds = _collect(problems, notes, "config dataset",
                      dataset_module.load_config, data["dataset"], data.get("version"))

    # 2b. Dữ liệu GỐC của nguồn `raw`. Kể TRƯỚC mọi việc khác: thiếu nó là nguyên nhân gốc, còn
    # "chưa có dataset đã xử lý" và "thiếu tập đánh giá" chỉ là hệ quả của cùng một thiếu sót.
    if ds is not None:
        raw_source_report(ds, problems, notes, info)

    # 3. Đường dẫn thí nghiệm cần: dữ liệu từng vai, bảng mã nhãn, prompt, `requires_extra`.
    missing = []
    if version_id:
        rows = _collect(problems, notes, "đường dẫn",
                        experiments.requires, result, version_id) or []
        missing = [row["display"] for row in rows if not row["path"].exists()]
        # File dữ liệu gốc còn thiếu cũng được ghi vào `errors.json` mục `requires`: người đọc log
        # cần thấy đủ danh sách những gì phải có, không chỉ những gì thí nghiệm trỏ tới.
        missing += info.get("raw_missing") or []
        if missing:
            problems.append("Thiếu {} đường dẫn mà thí nghiệm cần:\n      {}".format(
                len(missing), "\n      ".join(missing)))

    # 4. Mã phiên bản dữ liệu và tập đánh giá.
    version_id = version_report(ds, version_id, data.get("version"), problems, notes, info)
    if version_id:
        eval_lock_report(ds, version_id, problems, notes, info)
        # Nội dung file gốc phải khớp bản đã dùng để dựng dataset: lệch thì mã phiên bản cũng lệch,
        # và người chạy cần biết CHÍNH XÁC file nào đã đổi thay vì đoán.
        raw_fingerprint_report(ds, version_id, problems, notes, info)

    # 5. Thiết bị và cách nạp model; 6. bộ tách từ nếu model cần.
    device_report(model_id, problems, notes, info)
    # Truyền bộ tách từ ĐANG DÙNG (cấu hình đã hợp nhất): lớp thí nghiệm ĐÈ được khoá này, nên đọc
    # thẳng file model có thể in ra một bộ khác với bộ thật sự chia văn bản của lượt chạy.
    segmenter_report(model_id, problems, notes, info,
                     (config.get("preprocess") or {}).get("segmenter"))

    # 5b. Cách huấn luyện (model encoder): thiếu thư viện, thiếu `trainer`, thiếu `lora.target_modules`
    # đều biết được ngay ở đây - không phải sau khi đã tải dữ liệu và nạp model.
    if config.get("enabled"):
        _collect(problems, notes, "huấn luyện", _training_problems, config, model_id)
        notes.append("huấn luyện: trainer={}, {} epoch, batch {} (tích luỹ {})".format(
            config.get("trainer"), config.get("epochs"), config.get("batch"),
            config.get("grad_accum")))

    # 7. Ghi được vào gốc dữ liệu và gốc kết quả (trên Colab: Drive phải mount).
    writable(paths.results_root(), "gốc kết quả", problems, notes)
    writable(paths.data_root(), "gốc dữ liệu", problems, notes)

    # 8. Chạy mới hay chạy tiếp, dùng chung quyết định với lúc chạy thật.
    if version_id:
        if method and exp_id:
            # Có đủ thông tin để tính ĐÚNG thư mục của lượt chạy: dùng nó cho cả dấu vân tay lẫn
            # báo cáo trạng thái, nên "kiểm trước" và lượt chạy không thể nói hai chuyện khác nhau.
            found = _collect(
                problems, notes, "dấu vân tay cấu hình (config + prompt + ví dụ + dữ liệu)",
                _fingerprint, result, version_id, model_id, method, exp_id)
            if found:
                out_dir, want = found
                info["run_dir"] = out_dir
                state_report(out_dir, want, problems, notes, info, force_new=force_new)
                info["fingerprint"] = want
        else:
            notes.append(
                "Không khai `method`/`exp_id` nên chưa tính được thư mục của LƯỢT CHẠY; trạng thái "
                "dưới đây là của thư mục phiên bản, có thể khác lượt chạy thật.")
            sha = _collect(problems, notes, "dấu vân tay cấu hình (config + prompt)",
                           experiments.config_sha256, result)
            if sha:
                want = resume.fingerprint(sha, version_id, repo.current_sha())
                state_report(out_dir, want, problems, notes, info, force_new=force_new)
                info["fingerprint"] = want

    if log is not None:
        for item in notes:
            log.step("kiểm trước: {}".format(item))
        for item in problems:
            log.error("kiểm trước: {}".format(item), context={"bước": "preflight"},
                      requires=missing or None)

    return {"problems": problems, "notes": notes, "info": info, "missing": missing,
            "version_id": version_id}


def _training_problems(config, model_id):
    """Đổi danh sách vấn đề của cách huấn luyện thành một ngoại lệ, để `_collect` gom cùng một chỗ."""
    # Kiểm CẢ chính sách checkpoint: nó không thuộc trainer (`src/training/checkpoints.py`), nên thiếu
    # khoá ở đó phải lộ ra TRƯỚC khi nạp model, không phải sau khi đã tải xong dữ liệu.
    found = checkpoints.check(config) + training.check(config, model_id)
    if found:
        raise PreflightError("; ".join(found))
    return True


def _fingerprint(result, version_id, model_id=None, method=None, exp_id=None, out_dir=None):
    """Bộ ba quyết định chạy mới hay chạy tiếp, tách ra để `run()` thu LỖI thành VẤN ĐỀ.

    Tính bằng CHÍNH `experiment_run.run_identity` - hàm mà lượt chạy thật dùng - nên hai bên luôn
    nói cùng một chuyện. Trước 25/09/2026 chỗ này băm thiếu file ví dụ/khối hệ thống và nhìn thư mục
    PHIÊN BẢN, nên preflight báo "NEW - chưa có lần chạy nào" trong khi lượt chạy báo "RESUME - chạy
    tiếp từ 16 mẫu đã xong" trên cùng một thư mục.

    `config_sha256` phải đọc cả văn bản prompt, nên thiếu file prompt là lỗi ngay ở đây. Đó đúng là
    việc kiểm trước phải kể ra thành danh sách việc-phải-sửa: ném ra giữa chừng thì notebook dừng
    bằng vết gọi, người đọc không biết phải sửa chỗ nào.

    Trả về (thư mục kết quả, bộ ba) - thư mục là thư mục của LƯỢT CHẠY, không phải thư mục phiên bản.
    """
    from src.experiments import experiment_run

    config = dict(result.get("config") or {})
    # Model encoder không có prompt, nên phần "cấu hình + prompt" phải tính bằng hàm của đường đó:
    # băm thiếu một phần là preflight và lượt chạy thật nhìn vào hai thư mục khác nhau.
    if model_id and model_config.approach_of(config, model_id) == "encoder":
        from src.experiments import encoder_run

        found = encoder_run.identity(config, version_id, model_id, method, exp_id)
        return found["out_dir"], found["fingerprint"]

    prompt_obj = experiment_run.run_prompt(config, model_id, method, exp_id)
    quant = experiment_run.effective_quant("auto", config)
    sampled = experiment_run.settings_of(config)[1]
    identity = experiment_run.run_identity(
        config, version_id, prompt_obj, model_id=model_id, method=method, exp_id=exp_id,
        generation=experiment_run.run_generation(config, quant, sampled),
        max_length=experiment_run.effective_max_length(config))
    return identity["out_dir"], identity["fingerprint"]


def check(*args, **kwargs):
    """Như `run()` nhưng NÉM nếu có vấn đề, để notebook dừng trước khi nạp model."""
    report = run(*args, **kwargs)
    if report["problems"]:
        raise PreflightError("Chưa chạy được, còn {} việc phải sửa:\n  - {}".format(
            len(report["problems"]), "\n  - ".join(report["problems"])))
    return report


def print_report(report):
    """In báo cáo cho người đọc (notebook gọi hàm này)."""
    print("Kiểm trước khi chạy:")
    for item in report["notes"]:
        print("  - {}".format(item))
    if report["problems"]:
        print("\n  CÒN {} VIỆC PHẢI SỬA:".format(len(report["problems"])))
        for item in report["problems"]:
            print("    * {}".format(item))
    else:
        print("\n  Không có việc nào phải sửa.")
    return report


