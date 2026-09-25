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
    4. `test.csv` khớp `eval_lock` (rules.md mục 11) - lệch thì kết quả không so được với công bố
    5. Thiết bị: có GPU không, `inference.quantization` khai trong model config có dùng được không
    6. Bộ tách từ mà model cần (ví dụ `vncorenlp` cần Java) chạy được trên máy này không
    7. Ghi được vào gốc kết quả (trên Colab: Drive chưa mount thì chỉ đọc)
    8. Trạng thái FRESH hay RESUME, và lí do - dùng chung `src/resume.py` với lúc chạy thật

CÁCH BÁO
`run()` KHÔNG ném: nó gom hết vấn đề vào `problems` để notebook in ra một lần, kèm cả những việc
KHÔNG chặn chạy (`notes`). Muốn dừng ngay thì gọi `check()`, nó ném `PreflightError` với đủ danh
sách. Lỗi thiếu đường dẫn còn được ghi vào `errors.json` mục `requires` nếu có truyền `log`.
"""

import csv
import importlib.util
import os
from pathlib import Path

from src import dataset as dataset_module
from src import experiments, model_config, paths, resume, runtime, utils, versioning
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


def version_report(ds, version_id, want_version, problems, notes, info):
    """Kiểm mã phiên bản dữ liệu: khớp config, và dataset đã được pipeline tạo chưa."""
    computed = _collect(problems, notes, "mã phiên bản",
                        versioning.compute_id, ds)
    info["version_id"] = version_id or computed
    if computed and version_id and computed != version_id:
        problems.append(
            "Mã phiên bản đang dùng ({}) khác mã tính từ config ({}) - đang chấm trên bộ dữ liệu "
            "không phải bộ config nói.".format(version_id, computed))
    if want_version and ds and str(ds.get("version") or "") != str(want_version):
        problems.append(
            "Thí nghiệm khai `data.version` {} nhưng file config dataset khai {}. Hai giá trị này "
            "phải trùng: thí nghiệm đang đọc một phiên bản khác với bản đã khai.".format(
                want_version, ds.get("version")))
    folder = paths.processed(info["version_id"] or "")
    if info["version_id"] and folder.is_dir():
        notes.append("dataset: {}".format(utils.rel(folder)))
    else:
        problems.append(
            "Chưa có dataset đã xử lý ở {}. Tạo bằng: {}".format(
                utils.rel(folder), pipeline_command(ds)))
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
    return "`python run_pipeline.py --dataset {} --version {}`".format(name, version)


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

    Khoá đọc theo thứ tự: giá trị MONG ĐỢI khai trong file phiên bản dataset (nếu có, dùng khi muốn
    đối chiếu với một tập test bên ngoài), rồi tới khoá ĐÃ GHI cùng dữ liệu
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
    info["test"] = measured

    if not lock.get("enforce", True):
        notes.append("`eval_lock.enforce` đang TẮT: tập test có thể bị đổi mà không ai chặn.")
        info["eval_lock"] = {"enforce": False, "source": ""}
        return measured

    stored = versioning.split_lock(version_id, Path(str(declared.get("file") or "test.csv")).stem)
    source = "khai trong file phiên bản dataset"
    want = declared.get("sha256")
    if not want:
        want = stored.get("sha256")
        source = "ghi cùng dữ liệu lúc tạo ({})".format(
            utils.rel(versioning.eval_lock_path(version_id or "")))
    info["eval_lock"] = {"enforce": True, "source": source, "sha256": want,
                         "rows": stored.get("rows")}
    if not want:
        notes.append(
            "Chưa có khoá tập đánh giá cho phiên bản này. Chạy pipeline để tạo khoá (nó ghi "
            "{} trong cùng lần chạy sinh ra test.csv): `python run_pipeline.py --dataset <tên> "
            "--version <phiên bản>`.".format(utils.rel(versioning.eval_lock_path(version_id or ""))))
        return measured
    if str(want) != measured["sha256"]:
        problems.append(
            "{} KHÔNG khớp khoá tập đánh giá ({}): đã ghi {}, đo được {}. Tập đánh giá đã thay đổi "
            "nên kết quả không so được với công bố tham chiếu.".format(
                measured["file"], source, want, measured["sha256"]))
    else:
        notes.append("{} khớp khoá tập đánh giá ({} dòng; {}).".format(
            measured["file"], measured["rows"], source))
    return measured


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
    return info


def segmenter_report(model_id, problems, notes, info):
    """Bộ tách từ mà model cần: thiếu Java hay thiếu gói thì báo ngay, kèm lí do."""
    preprocess = model_config.preprocess(model_id) if model_id else {}
    name = str(preprocess.get("segmenter") or "").strip()
    info["segmenter"] = name or None
    if not name or name == "none":
        return None
    module = segmenters.SEGMENTERS.get(name)
    if module is None:
        problems.append(
            "Model config khai `preprocess.segmenter: {}` nhưng không có bộ tách từ này. Các bộ "
            "hiện có: {}.".format(name, ", ".join(sorted(segmenters.SEGMENTERS))))
        return None
    available, reason = module.available()
    if not available:
        problems.append("Bộ tách từ '{}' không chạy được trên máy này: {}".format(name, reason))
    else:
        notes.append("bộ tách từ: {} - {}".format(name, module.DESCRIPTION))
    return name


def state_report(out_dir, want, problems, notes, info, force_new=False):
    """FRESH hay RESUME, dùng CHUNG quyết định với lúc chạy thật (`src/resume.py`)."""
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
    from src import repo

    problems, notes, info = [], [], {}
    config = result.get("config") or {}
    data = dict(config.get("data") or {})
    model_id = model_id or result.get("model_id")

    # 1. Cấu hình thí nghiệm: khoá lạ, thiếu `data.roles`, nhiều dataset, vai trỏ vào train...
    _collect(problems, notes, "cấu hình", experiments.check, result, ds)

    # 2. Config dataset: kiểm luôn ở đây vì mọi phép kiểm sau đều dựa vào nó.
    if ds is None and data.get("dataset"):
        ds = _collect(problems, notes, "config dataset",
                      dataset_module.load_config, data["dataset"])

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

    # 5. Thiết bị và cách nạp model; 6. bộ tách từ nếu model cần.
    device_report(model_id, problems, notes, info)
    segmenter_report(model_id, problems, notes, info)

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
    from src import experiment_run

    config = dict(result.get("config") or {})
    model = experiment_run.run_model(config, os.environ.get("SENTIMENTX_MODEL") or None)
    prompt_obj = experiment_run.run_prompt(config, model_id, method, exp_id)
    roles = (config.get("data") or {}).get("roles") or {}
    split = roles.get("eval") or "val"
    sampled = experiment_run.settings_of(config)[1]
    identity = experiment_run.run_identity(
        config, version_id, prompt_obj, split,
        limit=experiment_run.limit_of(config), sampled=sampled,
        quant=experiment_run.effective_quant("auto", config), model=model,
        model_id=model_id, method=method, exp_id=exp_id)
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


