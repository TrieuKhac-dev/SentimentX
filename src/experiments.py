# -*- coding: utf-8 -*-
"""Hợp nhất cấu hình của MỘT thí nghiệm từ 7 lớp.

THỨ TỰ HỢP NHẤT - lớp sau đè lên lớp trước
    1. configs/models/<model_id>.yaml
    2. configs/experiments/repo.yaml
    3. configs/experiments/task.yaml
    4. configs/experiments/evaluation.yaml
    5. configs/experiments/training.yaml
    6. configs/experiments/tracking.yaml
    7. experiments/<model_id>/<method>/<expNNN>/config.yaml

VÌ SAO PHẢI GHI LẠI NGUỒN CỦA TỪNG KHOÁ
Bảy lớp là quá nhiều để đoán. Đọc một giá trị mà không biết nó đến từ file nào thì không sửa
được, và cũng không biết phải sửa file nào. Vì vậy mỗi khoá đều giữ lại lớp đã đặt ra giá trị
đang dùng, và những khoá bị lớp sau đè lên được liệt kê riêng để in thành bảng.

KHÔNG HỢP NHẤT, VÀ CŨNG KHÔNG SỬA
`configs/paths.yaml`, `configs/dagshub.yaml`, `configs/pipeline/<v>.yaml`,
`configs/datasets/<name>/<v>.yaml` và các file prompt là ĐẦU VÀO của lần chạy, không phải cấu
hình của thí nghiệm. Chúng được ghi vào `run_meta.files[]` kèm `role` (xem P4).
"""

import hashlib
import json
from pathlib import Path

import yaml

from src import model_config, paths, utils

# Năm file cấu hình dùng chung, theo đúng thứ tự hợp nhất.
SHARED = ("repo", "task", "evaluation", "training", "tracking")

# Nhãn lớp dùng trong `sources` và trong bảng ghi đè.
MODEL_LAYER = "model"
EXPERIMENT_LAYER = "experiment"
# Khối `task` của model được áp SAU tất cả các lớp, nên có nhãn riêng.
MODEL_TASK_LAYER = "model.task"


class ExperimentError(Exception):
    """Lỗi cấu hình thí nghiệm: thiếu file, thiếu khoá, khoá không hợp lệ."""


def experiment_dir(model_id, method, exp_id):
    """Thư mục định nghĩa một thí nghiệm: `experiments/<model_id>/<method>/<exp_id>/`."""
    return paths.experiment_dir(model_id, method, exp_id)


def config_path(model_id, method, exp_id):
    """Đường dẫn file config riêng của thí nghiệm."""
    return experiment_dir(model_id, method, exp_id) / paths.pattern("experiment_config")


def shared_path(name):
    """Đường dẫn MỘT lớp cấu hình dùng chung: `repo`, `task`, `evaluation`, `training`, `tracking`."""
    if name not in SHARED:
        raise ExperimentError(
            "Không có lớp cấu hình dùng chung '{}'. Các lớp hiện có: {}.".format(
                name, ", ".join(SHARED)))
    return paths.config_path("experiments", "{}.yaml".format(name))


def shared(name):
    """Nội dung MỘT lớp cấu hình dùng chung, chưa hợp nhất với lớp nào.

    Dùng cho công cụ chỉ cần lớp dùng chung: ví dụ phần chấm điểm đọc `task` (cách nhìn bài toán)
    và `evaluation` (chỉ số nào cần tính) mà chưa cần cấu hình riêng của một thí nghiệm. Nhờ vậy
    công cụ không phải chép lại giá trị mặc định - `configs/experiments/*.yaml` vẫn là nguồn duy
    nhất, và đổi ở đó là đổi cho mọi chỗ dùng.
    """
    return _read(name, shared_path(name), None)


def layer_files(model_id, method, exp_id):
    """Danh sách (nhãn lớp, đường dẫn) theo ĐÚNG thứ tự hợp nhất."""
    files = [(MODEL_LAYER, model_config.config_path(model_id))]
    for name in SHARED:
        files.append((name, shared_path(name)))
    files.append((EXPERIMENT_LAYER, config_path(model_id, method, exp_id)))
    return files


def load(model_id, method, exp_id):
    """Nạp và hợp nhất 7 lớp của một thí nghiệm.

    Trả về dict gồm:
        config    : cấu hình đã hợp nhất (dict lồng nhau)
        sources   : {khoá dạng 'a.b': nhãn lớp đã đặt giá trị đang dùng}
        overrides : [[khoá, giá trị trước, giá trị sau, lớp đè]] - chỉ khoá bị đè
        layers    : [[nhãn lớp, đường dẫn]] theo thứ tự đã đọc
        history   : {khoá: [(nhãn lớp, giá trị), ...]} - toàn bộ lịch sử, để tra khi cần
        dir       : thư mục thí nghiệm
    """
    return _merge_layers(layer_files(model_id, method, exp_id), model_id,
                         method=method, exp_id=exp_id)


def load_shared(model_id=None):
    """Hợp nhất các lớp ĐANG CÓ khi chưa có thư mục thí nghiệm.

    Dùng cho công cụ chạy tay (`run_qwen_eval.py`): nó chạy MỘT model với MỘT prompt, chưa gắn
    với `expNNN` nào. Có thư mục thí nghiệm rồi thì dùng `load()`.

    Không thay thế được `load()`: thiếu lớp thí nghiệm nghĩa là thiếu `data.roles` và thiếu prompt
    của thí nghiệm, nên bản ghi lần chạy phải nói rõ đang chạy bằng cấu hình dùng chung.
    """
    layers = []
    if model_id:
        layers.append((MODEL_LAYER, model_config.config_path(model_id)))
    layers.extend((name, shared_path(name)) for name in SHARED)
    return _merge_layers(layers, model_id)


def _merge_layers(layers, model_id, method=None, exp_id=None):
    """Hợp nhất một danh sách lớp. Dùng chung cho `load` và `load_shared`."""
    config, history, sources = {}, {}, {}
    for label, path in layers:
        _merge_into(config, history, sources, _read(label, path, model_id), label)

    # Khối `task` của model là RÀNG BUỘC của model ("model này chỉ làm 2 nhãn"), nên áp SAU cùng
    # chứ không theo thứ tự lớp: `configs/experiments/task.yaml` không ghi đè được nó.
    task_override = model_config.task_override(model_id) if model_id else None
    if task_override:
        _merge_into(config, history, sources, task_override, MODEL_TASK_LAYER)

    return {
        "model_id": model_id,
        "method": method,
        "exp_id": exp_id,
        "dir": (experiment_dir(model_id, method, exp_id)
                if model_id and method and exp_id else None),
        "config": config,
        "sources": sources,
        "overrides": _overrides(history),
        "layers": [[label, utils.rel(path)] for label, path in layers],
        "history": history,
    }


def _read(label, path, model_id):
    """Nội dung một lớp. Riêng lớp model đi qua `model_config` để được kiểm tra đầy đủ.

    Khối `task` của lớp model KHÔNG được trả về ở đây: nó là ràng buộc của model nên phải áp
    SAU tất cả các lớp (xem `load` và docs/05_config/04_models.md).
    """
    if label == MODEL_LAYER:
        data = dict(model_config.load(model_id))
        data.pop("task", None)
        return data
    if not path.exists():
        raise ExperimentError(
            "Thiếu file cấu hình của lớp '{}': {}.".format(label, utils.rel(path)))
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ExperimentError(
            "{}: nội dung phải là các dòng 'khoá: giá trị'.".format(utils.rel(path)))
    return data


def _merge_into(target, history, sources, data, label, prefix=""):
    """Đè `data` lên `target`, ghi lại lịch sử giá trị của từng khoá lá.

    Khoá bắt đầu bằng `_` bị bỏ qua: đó là khoá nội bộ của module đọc file (ví dụ `_path`).

    Đổi KIỂU ở cùng một khoá (giá trị vô hướng thành nhóm khoá, hoặc ngược lại) là LỖI, không
    phải ghi đè: hầu như luôn là hai lớp vô tình dùng trùng tên, và lớp sau sẽ xoá mất dữ liệu
    của lớp trước mà không ai biết. Đã gặp thật: `checkpoint` (tên model trên Hugging Face ở
    lớp model) trùng với nhóm `checkpoint` của chính sách lưu.
    """
    for key, value in data.items():
        if str(key).startswith("_"):
            continue
        name = _key(prefix, key)
        node = target.get(key)
        if isinstance(value, dict):
            if node is not None and not isinstance(node, dict):
                raise ExperimentError(
                    "Lớp '{}' khai nhóm khoá '{}' nhưng lớp trước đã đặt nó là giá trị {!r}. "
                    "Đây là hai lớp trùng tên khoá, không phải ghi đè.".format(
                        label, name, node))
            if node is None:
                node = {}
                target[key] = node
            _merge_into(node, history, sources, value, label, name)
        else:
            if isinstance(node, dict):
                raise ExperimentError(
                    "Lớp '{}' đặt giá trị {!r} cho khoá '{}' nhưng lớp trước đã khai nó là một "
                    "nhóm khoá. Đây là hai lớp trùng tên khoá, không phải ghi đè.".format(
                        label, value, name))
            target[key] = value
            history.setdefault(name, []).append((label, value))
            sources[name] = label


def _overrides(history):
    """Các khoá bị lớp sau ĐÈ lên một giá trị KHÁC, dạng bảng để in ra.

    Chỉ tính khi giá trị thật sự đổi: cùng một khoá khai ở hai lớp với cùng giá trị là chuyện
    bình thường (ví dụ chép lại giá trị mặc định), không phải ghi đè, và in ra sẽ gây nhiễu.
    """
    rows = []
    for name in sorted(history):
        entries = history[name]
        for (before_label, before), (after_label, after) in zip(entries, entries[1:]):
            if before != after:
                rows.append([name, before, after, after_label])
    return rows


def flatten(config, prefix=""):
    """Đổi dict lồng nhau thành {khoá dạng 'a.b': giá trị lá}."""
    flat = {}
    for key, value in config.items():
        name = "{}.{}".format(prefix, key) if prefix else str(key)
        if isinstance(value, dict):
            flat.update(flatten(value, name))
        else:
            flat[name] = value
    return flat


def table(result):
    """Bảng giá trị hiệu lực: [khoá, giá trị, lớp đặt giá trị]."""
    flat = flatten(result["config"])
    return [
        [name, _value(flat[name]), result["sources"].get(name, "?")]
        for name in sorted(flat)
    ]


def override_table(result):
    """Bảng ghi đè: [khoá, giá trị trước, giá trị sau, lớp đè]."""
    return [[name, _value(before), _value(after), label]
            for name, before, after, label in result["overrides"]]


def describe(result):
    """Vài dòng mô tả thí nghiệm và các lớp đã hợp nhất, để in ra hoặc đưa vào báo cáo."""
    lines = [
        "Thí nghiệm: {}/{}/{}".format(
            result["model_id"], result["method"], result["exp_id"]),
        "Định nghĩa: {}".format(utils.rel(result["dir"])),
        "Các lớp đã hợp nhất, theo thứ tự (lớp sau đè lên lớp trước):",
    ]
    for label, path in result["layers"]:
        lines.append("    {} <- {}".format(label, path))
    lines.append("Số khoá bị lớp sau đè: {}".format(len(result["overrides"])))
    return lines


def _value(value):
    """Giá trị để in ra: None thành 'null', danh sách gộp thành một dòng."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return "[{}]".format(", ".join(str(_value(item)) for item in value))
    return value


# ---
# Dấu vân tay của cấu hình
# ---


def config_sha256(result, prompt_text=None):
    """Dấu vân tay của CẤU HÌNH ĐÃ HỢP NHẤT và VĂN BẢN PROMPT ĐÃ HỢP NHẤT.

    Vì sao băm cả văn bản prompt: prompt là một phần của thí nghiệm, mà nội dung nó nằm ở file
    riêng chứ không nằm trong config hợp nhất. Không băm thì hai thí nghiệm khác prompt sẽ mang
    cùng một dấu vân tay.

    `prompt_text`: dùng khi văn bản prompt KHÔNG lấy được từ thư mục thí nghiệm - công cụ chạy tay
    dùng prompt ở thư viện dùng chung (`configs/prompts/`).

    Ba giá trị quyết định resume (xem docs/00_workflow/02_rules.md): `config_sha256`, mã phiên
    bản dữ liệu, và commit đã ghim. Hàm này tính giá trị thứ nhất.
    """
    digest = hashlib.sha256()
    digest.update(b"config:")
    digest.update(canonical_bytes(result["config"]))
    digest.update(b"prompt:")
    text = prompt_text if prompt_text is not None else prompt_merged(result)
    digest.update(text.encode("utf-8"))
    return digest.hexdigest()


def canonical_bytes(config):
    """Config đã chuẩn hoá, ở dạng bytes để băm. Chuẩn hoá như `canonical`."""
    text = json.dumps(canonical(config), sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), default=str)
    return text.encode("utf-8")


def canonical(config):
    """Chuẩn hoá cấu hình để băm: khoá sắp xếp, danh sách coi là TẬP HỢP.

    Vì sao phải chuẩn hoá: `config_sha256` dùng để biết hai lần chạy có cùng cấu hình hay
    không. Nếu thứ tự khoá trong file hay thứ tự phần tử của `target_modules` cũng làm đổi dấu
    vân tay thì mỗi lần format lại YAML sẽ phá resume, dù cấu hình không đổi.

    Danh sách nào có thứ tự CÓ NGHĨA thì khai vào `canonical.ordered_lists` trong
    `configs/paths.yaml`; các danh sách khác được sắp xếp trước khi băm.
    """
    return _canonical(config, "", set(paths.ordered_lists()))


def _canonical(value, prefix, ordered):
    if isinstance(value, dict):
        pairs = sorted(value.items(), key=lambda pair: str(pair[0]))
        return {str(key): _canonical(item, _key(prefix, key), ordered)
                for key, item in pairs}
    if isinstance(value, list):
        items = [_canonical(item, prefix, ordered) for item in value]
        if prefix in ordered:
            return items
        return sorted(items, key=_sort_key)
    return value


def _sort_key(value):
    """Khoá sắp xếp cho một phần tử danh sách, ổn định với mọi kiểu dữ liệu."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)


def _key(prefix, key):
    return "{}.{}".format(prefix, key) if prefix else str(key)


def prompt_merged(result):
    """Văn bản prompt ĐÃ HỢP NHẤT của một thí nghiệm.

    Gồm cả ba phần mà model thật sự nhìn thấy: khối hệ thống (nếu có), file prompt, và file ví
    dụ few-shot (nếu prompt dùng `{examples}`). Vì sao phải gộp: `prompt_sha` chỉ tính nội dung
    file prompt, nên đổi số ví dụ hay đổi khối hệ thống không làm đổi nó - trong khi đó là đổi
    thí nghiệm.

    Đường dẫn `prompt`/`examples`/`system_prompt` tính từ thư mục thí nghiệm trước, rồi mới tới
    gốc repo, nên `prompt.txt` (file của chính thí nghiệm) và
    `configs/prompts/system/absa_cot.txt` (file dùng chung) đều dùng được.
    """
    parts = []
    for key, label in (("system_prompt", "khối hệ thống"),
                       ("prompt", "file prompt"),
                       ("examples", "file ví dụ few-shot")):
        value = (result["config"] or {}).get(key)
        if not value:
            continue
        path = resolve_file(result, value)
        parts.append("# {}\n{}".format(utils.rel(path), _read_prompt_file(path, label)))
    if not parts:
        raise ExperimentError(
            "Thí nghiệm chưa khai 'prompt' nên không có gì để hợp nhất.")
    return "\n\n".join(parts)


def resolve_file(result, value):
    """Đường dẫn file của một khoá thí nghiệm: thử thư mục thí nghiệm trước, rồi tới gốc repo."""
    path = Path(str(value))
    if path.is_absolute():
        return path
    candidate = Path(result["dir"]) / path
    return candidate if candidate.exists() else paths.root() / path


def _read_prompt_file(path, label):
    """Đọc một file văn bản của prompt; thiếu file hoặc thiếu `{text}` là lỗi."""
    if not path.exists():
        raise ExperimentError("Thiếu {}: {}".format(label, utils.rel(path)))
    text = path.read_text(encoding="utf-8")
    if label == "file prompt" and "{text}" not in text:
        raise ExperimentError(
            "{} thiếu ô nhớ {{text}}, nên prompt không dùng được cho review nào.".format(
                utils.rel(path)))
    return text


# ---
# Kiểm tra cấu hình đã hợp nhất
# ---

# Khoá hợp lệ trong cấu hình đã hợp nhất (đường dẫn dạng dấu chấm). Danh sách này là HỢP ĐỒNG:
# khoá không có ở đây nghĩa là gõ sai tên khoá, hoặc ghi sai đường dẫn (ví dụ `evaluation: {n: 200}`
# tạo khoá `evaluation.n` mà không chỗ nào đọc, trong khi `n` vẫn giữ giá trị cũ).
KNOWN_KEYS = (
    # lớp model
    "model_id", "checkpoint", "config_version",
    "preprocess.max_length", "preprocess.add_generation_prompt", "preprocess.segmenter",
    "inference.dtype", "inference.quantization", "inference.batch_size",
    # lớp repo
    "url", "branch", "allowed_branches",
    # lớp task (task.yaml, và cùng tên đó khi model ghi đè)
    "label_space", "neutral_policy", "not_mentioned", "aspects",
    # lớp evaluation
    "n", "decoding.mode", "decoding.temperature", "decoding.top_p",
    "scores", "group_by",
    "save.predictions", "save.plots", "save.confusion",
    # lớp training
    "enabled",
    "lora.r", "lora.alpha", "lora.dropout", "lora.target_modules",
    "lr", "batch", "epochs", "grad_accum", "weight_decay",
    "checkpoints.every_n_steps", "checkpoints.keep_last_k", "checkpoints.save_last",
    "checkpoints.save_best", "checkpoints.delete_intermediate",
    # lớp tracking
    "tracker", "experiment", "artifacts",
    # lớp config thí nghiệm
    "exp_id", "parent", "model", "method",
    "data.dataset", "data.version",
    "prompt", "examples", "system_prompt", "requires_extra",
)

# Nhóm khoá mà tên con do người dùng đặt, không kiểm được.
FREE_GROUPS = ("mlflow_tags",)

# Vai bắt buộc của một thí nghiệm, và vai bắt buộc khi có huấn luyện.
ALWAYS_ROLES = ("eval",)
TRAINING_ROLES = ("train", "val")
ALL_ROLES = ("train", "val", "eval")


def check(result, dataset_cfg=None):
    """Kiểm tra cấu hình đã hợp nhất. Báo lỗi MỘT LẦN với đầy đủ các vấn đề tìm được.

    Bốn lỗi im lặng cần chặn:
        1. Khoá lạ: gõ sai tên, hoặc ghi sai đường dẫn nên giá trị không có tác dụng.
        2. Thiếu `data.roles`: vai nào dùng split nào phải khai rõ, không kế thừa.
        3. `data.dataset` không phải một dataset duy nhất.
        4. Vai trỏ vào split không có trong file phiên bản dataset, hoặc `eval` trỏ vào `train`
           (rò rỉ dữ liệu).
    """
    config = result["config"] or {}
    data = config.get("data") or {}
    problems = []

    for name in sorted(flatten(config)):
        if name in KNOWN_KEYS or name.split(".")[0] in FREE_GROUPS:
            continue
        # Vai dùng split nào: tên vai cố định, nên `data.roles.trian` vẫn bị bắt là khoá lạ.
        if name.startswith("data.roles.") and name[len("data.roles."):] in ALL_ROLES:
            continue
        problems.append("khoá lạ '{}' (không nhóm nào đọc khoá này)".format(name))

    dataset = data.get("dataset")
    if not dataset:
        problems.append("thiếu 'data.dataset'")
    elif not isinstance(dataset, str):
        problems.append(
            "'data.dataset' phải là MỘT tên dataset, đang là {!r}".format(dataset))

    roles = data.get("roles")
    if not isinstance(roles, dict) or not roles:
        problems.append(
            "thiếu 'data.roles' (mỗi vai phải khai rõ dùng split nào, không kế thừa)")
        roles = {}
    else:
        for role in ALWAYS_ROLES:
            if role not in roles:
                problems.append("'data.roles' phải có vai '{}'".format(role))
        if roles.get("eval") == "train":
            problems.append("'data.roles.eval' trỏ vào 'train' - đó là rò rỉ dữ liệu")
        if config.get("enabled"):
            for role in TRAINING_ROLES:
                if role not in roles:
                    problems.append(
                        "training.enabled: true nên 'data.roles' phải có vai '{}'".format(role))

    splits = _splits_of(data, dataset, dataset_cfg)
    if isinstance(splits, dict):
        for role in sorted(roles):
            if roles[role] not in splits:
                problems.append(
                    "'data.roles.{}' là {!r} nhưng file phiên bản dataset không có split đó "
                    "(đang có: {})".format(
                        role, roles[role], ", ".join(sorted(splits)) or "không có"))

    if problems:
        raise ExperimentError(
            "Cấu hình thí nghiệm {}/{}/{} có {} vấn đề:\n  - {}".format(
                result["model_id"], result["method"], result["exp_id"],
                len(problems), "\n  - ".join(problems)))
    return result


def _splits_of(data, dataset, dataset_cfg):
    """`splits` của file phiên bản dataset mà thí nghiệm trỏ tới; None nếu không đọc được."""
    if not dataset or not isinstance(dataset, str):
        return None
    if dataset_cfg is not None:
        return dataset_cfg.get("splits") or {}
    from src import dataset as dataset_module
    try:
        return dataset_module.load_config(
            dataset, data.get("version")).get("splits") or {}
    except dataset_module.DatasetError as exc:
        raise ExperimentError("Không đọc được file phiên bản dataset: {}".format(exc))


# ---
# Đầu vào mà lần chạy PHẢI có
# ---


def requires(result, version_id):
    """Danh sách đường dẫn mà lần chạy cần: [{"path": Path, "display": str, "role": str}, ...].

    Sinh từ: file dữ liệu của từng vai trong `data.roles`, bảng mã nhãn của phiên bản dữ liệu,
    các file prompt, rồi cộng `requires_extra` của thí nghiệm.

    Vì sao cần danh sách này: chạy trên Colab thì dữ liệu nằm trên Drive, mà thiếu một file thì
    lỗi hiện ra rất muộn - sau khi đã tải model. Notebook kiểm danh sách này TRƯỚC khi nạp model;
    thiếu gì thì ghi vào `errors.json` mục `requires` (xem docs/00_workflow/01_flow.md).

    `display` là đường dẫn để ghi vào file kết quả: tương đối so với gốc repo khi file nằm trong
    repo, vì ghi đường dẫn tuyệt đối của máy cá nhân vào kết quả là thứ không tra cứu được.
    """
    config = result["config"] or {}
    data = config.get("data") or {}
    processed = paths.processed(version_id)
    rows = []

    for role in sorted(data.get("roles") or {}):
        name = "{}".format(data["roles"][role])
        rows.append(_requirement(processed / "{}.csv".format(name),
                                 "data.roles.{}".format(role)))
    rows.append(_requirement(processed / paths.pattern("label_map"), "label_map"))

    for key in ("prompt", "examples", "system_prompt"):
        if config.get(key):
            rows.append(_requirement(resolve_file(result, config[key]), key))

    for index, extra in enumerate(config.get("requires_extra") or [], start=1):
        rows.append(_requirement(paths.root() / str(extra) if not Path(str(extra)).is_absolute()
                                 else Path(str(extra)), "requires_extra[{}]".format(index)))
    return rows


def _requirement(path, role):
    return {"path": path, "display": utils.rel(path), "role": role}


def check_requires(result, version_id):
    """Kiểm các đường dẫn trong `requires` có thật. Trả về danh sách còn thiếu (rỗng là đủ)."""
    missing = [row for row in requires(result, version_id) if not row["path"].exists()]
    if missing:
        raise ExperimentError(
            "Thiếu {} đường dẫn mà thí nghiệm cần:\n  - {}".format(
                len(missing), "\n  - ".join(
                    "{} ({})".format(row["display"], row["role"]) for row in missing)))
    return []


# ---
# Chống chạy trùng
# ---


def list_experiments(model_id=None, method=None):
    """Các thí nghiệm đang có, sắp theo (model, method, exp_id).

    Một thư mục là một thí nghiệm khi có file `config.yaml`; thư mục rỗng hoặc mới tạo một nửa thì
    không tính. Hàm này chỉ ĐỌC TÊN thư mục (không nạp config của từng thí nghiệm), vì việc dùng
    của nó là chọn số `expNNN` kế tiếp và in danh sách cho người dùng xem.
    """
    found = []
    root = paths.experiments_dir()
    if not root.is_dir():
        return found
    for path in sorted(root.glob("*/*/*")):
        if not path.is_dir():
            continue
        parts = (path.parent.parent.name, path.parent.name, path.name)
        try:
            has_config = config_path(*parts).is_file()
        except ExperimentError:
            has_config = False
        if not has_config:
            continue
        if model_id and parts[0] != model_id:
            continue
        if method and parts[1] != method:
            continue
        found.append(parts)
    return found


def next_exp_id(model_id, method):
    """Số `expNNN` kế tiếp của một (model, method): tiếp nối số LỚN NHẤT đã có.

    Đọc số lớn nhất chứ không đếm số lượng: xoá một thí nghiệm ở giữa rồi tạo mới sẽ không đụng
    vào số của thí nghiệm khác. Tên không theo dạng `expNNN` bị bỏ qua - không đoán số từ tên lạ.
    """
    highest = 0
    for _model, _method, exp_id in list_experiments(model_id, method):
        text = str(exp_id)
        if text.startswith("exp") and text[3:].isdigit():
            highest = max(highest, int(text[3:]))
    return "exp{:03d}".format(highest + 1)


def fingerprint(result, version_id):
    """Bộ ba quyết định một lần chạy có TRÙNG với lần đã chạy hay không.

    `config_sha256` (cấu hình đã hợp nhất + văn bản prompt), mã phiên bản dữ liệu, và `exp_id`.
    Đây cũng đúng là ba giá trị đầu vào của phép kiểm resume (xem docs/00_workflow/02_rules.md).
    """
    return {
        "config_sha256": config_sha256(result),
        "ma": version_id,
        "exp_id": result["exp_id"],
    }


def existing_runs(result, version_id, root=None):
    """Các `run_meta.json` đã có CÙNG bộ ba của lần chạy này, sắp theo đường dẫn.

    Vì sao cần: cùng cấu hình trên cùng dữ liệu nghĩa là CÙNG một thí nghiệm. Không kiểm thì chạy
    lại sẽ đẻ ra hai thư mục kết quả gần giống nhau, và người đọc báo cáo không biết cái nào là
    kết quả dùng để so. Notebook dùng danh sách này để quyết định: lần chạy cũ ĐÃ XONG thì dừng và
    báo; CHƯA XONG thì resume (xem docs/06_plan/P4_logging_mlflow.md).

    `root` để trống thì quét gốc kết quả (`SENTIMENTX_RESULTS_ROOT`, mặc định là `experiments/`).
    """
    want = fingerprint(result, version_id)
    found = []
    for path in sorted((root or paths.results_root()).rglob(paths.pattern("run_meta"))):
        data = _read_json(path)
        if not data:
            continue
        if (data.get("config_sha256") == want["config_sha256"]
                and (data.get("data") or {}).get("ma") == want["ma"]
                and data.get("exp_id") == want["exp_id"]):
            found.append(path)
    return found


def describe_runs(paths_list):
    """Vài dòng mô tả các lần chạy đã có, để in ra trước khi quyết định resume."""
    if not paths_list:
        return ["Chưa có lần chạy nào cùng cấu hình và cùng dữ liệu."]
    lines = ["Đã có {} lần chạy cùng cấu hình và cùng dữ liệu:".format(len(paths_list))]
    for path in paths_list:
        data = _read_json(path)
        lines.append("    {} (trạng thái: {}, lúc: {})".format(
            utils.rel(path), data.get("status") or "không rõ",
            ((data.get("time") or {}).get("started") or "không rõ")))
    return lines


def _read_json(path):
    """Đọc JSON; file hỏng hoặc thiếu trả về {}.

    Quét cả cây kết quả nên không được chết vì một file lỗi: một `run_meta.json` viết dở (do lần
    chạy trước bị ngắt) không phải lí do để lần chạy mới không chạy được.
    """
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle) or {}
    except (OSError, ValueError):
        return {}