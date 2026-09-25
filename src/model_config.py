# -*- coding: utf-8 -*-
"""Cấu hình riêng của từng model: configs/models/<tên>.yaml.

VÌ SAO TÁCH KHỎI configs/pipeline.yaml
---
`pipeline.yaml` mô tả "ta xử lý DỮ LIỆU thế nào", và nội dung file đó được đưa vào
hash để sinh MÃ PHIÊN BẢN DỮ LIỆU (src/versioning.py). Còn file ở đây mô tả "MODEL
đọc dữ liệu thế nào" (dùng prompt nào, có chèn lượt assistant hay không) - đổi
prompt không làm đổi một dòng dữ liệu nào, nên không được nằm trong hash đó. Để
chung một file sẽ sinh ra những mã phiên bản mới vô nghĩa cho cùng một dataset.

MỘT FILE GỒM NHỮNG GÌ
    model_id      : tên dùng cho mọi đường dẫn và nhãn MLflow; phải trùng tên file
    checkpoint    : tên model trên Hugging Face, để đối chiếu tránh nhầm model
    config_version: tăng mỗi khi sửa file
    approach      : `prompt` (model sinh, nhận câu chỉ dẫn) hoặc `encoder` (model phân loại,
                    học từ dữ liệu gán nhãn). Quyết định ĐƯỜNG CHẠY, nên phải khai rõ.
    task.*        : ghi đè `configs/experiments/task.yaml` khi model này cần khác
    preprocess.*  : ngưỡng cắt input, chèn lượt trợ lý, bộ tách từ
    lora.*        : thứ RIÊNG của model cho huấn luyện, ví dụ `target_modules` (tên module
                    khác nhau theo kiến trúc, nên không nằm ở file dùng chung)
    inference.*   : kiểu số, lượng hoá, kích thước lô

KHÔNG CÓ GÌ THUỘC RIÊNG MỘT THÍ NGHIỆM
`prompt`, `examples`, `roles`, `dataset` nằm trong config của thí nghiệm. File này cũng KHÔNG
nằm trong hash sinh MÃ PHIÊN BẢN DỮ LIỆU: đổi prompt hay kiểu số không làm đổi một dòng dữ
liệu nào, nên để chung sẽ đẻ ra những mã phiên bản vô nghĩa cho cùng một dataset.

Gõ sai TÊN KHOÁ là lỗi hay gặp (`promt:` thay vì `prompt:`), nên file này báo lỗi kèm gợi ý
thay vì âm thầm bỏ qua - bỏ qua sẽ khiến cấu hình nằm lại ở giá trị cũ mà người dùng không biết.

GIỚI HẠN ĐÃ BIẾT
Chưa kiểm `checkpoint` có khớp với model thật trên Hugging Face; việc đó cần mạng nên để
notebook làm khi nạp model (xem docs/06_plan/P5_notebook_pin.md).
"""

import difflib

import yaml

from src import config

# Khoá được phép dùng trong configs/models/<tên>.yaml
KNOWN_KEYS = ("model_id", "checkpoint", "config_version", "approach", "task", "preprocess",
              "lora", "inference")

# Khoá bắt buộc phải có.
REQUIRED_KEYS = ("model_id", "checkpoint", "config_version", "approach", "preprocess")

# Cách một model được DÙNG trong thí nghiệm. Thêm một cách mới thì thêm module chạy tương ứng
# (`prompt` -> src/evaluation/runner.py, `encoder` -> src/encoder_run.py) rồi thêm tên vào đây.
APPROACHES = ("prompt", "encoder")

CONFIG_HINT = "Xem configs/models/qwen3-4b-instruct-2507.yaml để biết các khoá cần có."


class ModelConfigError(Exception):
    """Lỗi cấu hình model: thiếu file, sai tên khoá, sai kiểu giá trị."""


def available():
    """Tên các model đã có file cấu hình trong configs/models/."""
    directory = config.MODEL_CONFIG_DIR
    if not directory.is_dir():
        return []
    return sorted(path.stem for path in directory.glob("*.yaml"))


def suggest(name):
    """Câu gợi ý tên file gần đúng khi người dùng gõ sai tên model."""
    similar = difflib.get_close_matches(str(name), available(), n=3, cutoff=0.6)
    if not similar:
        return ""
    return "Có phải bạn muốn: {}?".format(" hoặc ".join(similar))


def config_path(name):
    """Đường dẫn file cấu hình của một model."""
    return config.MODEL_CONFIG_DIR / "{}.yaml".format(name)


def load(name):
    """Đọc và kiểm tra cấu hình của một model. Báo lỗi rõ nếu thiếu file hoặc thiếu khoá.

    File THIẾU là lỗi (không phải "dùng mặc định"): model nào có file ở đây là model đã chốt
    cấu hình, nên thiếu file nghĩa là ta không biết nó đang chạy với ngưỡng cắt nào.
    """
    path = config_path(name)
    if not path.exists():
        raise ModelConfigError(
            "Không tìm thấy cấu hình model '{}' tại {}. Các model có cấu hình: {}. {}{}".format(
                name, _display(path), ", ".join(available()) or "(trống)",
                suggest(name) + " " if suggest(name) else "", CONFIG_HINT)
        )

    with open(path, "r", encoding="utf-8") as handle:
        cfg = yaml.safe_load(handle) or {}
    if not isinstance(cfg, dict):
        raise ModelConfigError(
            "{}: nội dung phải là các dòng 'khoá: giá trị'. {}".format(
                _display(path), CONFIG_HINT)
        )

    unknown = [key for key in cfg if key not in KNOWN_KEYS and not str(key).startswith("_")]
    if unknown:
        hint = difflib.get_close_matches(unknown[0], KNOWN_KEYS, n=1, cutoff=0.5)
        raise ModelConfigError(
            "{}: khoá '{}' không hợp lệ.{} Khoá được phép dùng: {}.".format(
                _display(path), unknown[0],
                " Có phải bạn muốn '{}'?".format(hint[0]) if hint else "",
                ", ".join(KNOWN_KEYS))
        )

    missing = [key for key in REQUIRED_KEYS if cfg.get(key) in (None, {}, "")]
    if missing:
        raise ModelConfigError(
            "{}: thiếu khoá bắt buộc: {}. {}".format(
                _display(path), ", ".join(missing), CONFIG_HINT)
        )
    if str(cfg["model_id"]) != path.stem:
        raise ModelConfigError(
            "{}: 'model_id' là {!r} nhưng tên file là {!r}, hai giá trị này phải trùng nhau.".format(
                _display(path), cfg["model_id"], path.stem)
        )
    if not isinstance(cfg["preprocess"], dict):
        raise ModelConfigError(
            "{}: 'preprocess' phải là một nhóm khoá, ví dụ 'preprocess: {{max_length: 1280}}'.".format(
                _display(path))
        )

    approach = str(cfg["approach"]).strip()
    if approach not in APPROACHES:
        raise ModelConfigError(
            "{}: 'approach' là {!r} nhưng chỉ nhận {}. Đây là khoá quyết định ĐƯỜNG CHẠY của "
            "model, nên không đoán hộ.".format(
                _display(path), cfg["approach"], " hoặc ".join(APPROACHES)))

    value = cfg["preprocess"].get("max_length")
    if value is None:
        raise ModelConfigError(
            "{}: thiếu 'preprocess.max_length' (ngưỡng cắt input, đơn vị TOKEN).".format(
                _display(path))
        )
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ModelConfigError(
            "{}: 'preprocess.max_length' phải là số nguyên dương (đang là {!r}).".format(
                _display(path), value)
        )

    cfg = dict(cfg)
    cfg["_path"] = path
    return cfg


def preprocess(name):
    """Nhóm `preprocess` của một model (đã kiểm ở `load`)."""
    return dict(load(name)["preprocess"])


def inference(name):
    """Nhóm `inference` của một model; rỗng nếu model không khai."""
    return dict(load(name).get("inference") or {})


def task_override(name):
    """Nhóm `task` của một model: phần ghi đè lên `configs/experiments/task.yaml`."""
    return dict(load(name).get("task") or {})


def approach(name):
    """Cách dùng model trong thí nghiệm: `prompt` hoặc `encoder` (đã kiểm ở `load`)."""
    return str(load(name)["approach"]).strip()


def approach_of(config_data, model_id=None):
    """Cách chạy của MỘT LƯỢT CHẠY: đọc `approach` trong config ĐÃ HỢP NHẤT trước, rồi tới file cấu
    hình model.

    Vì sao ưu tiên config đã hợp nhất: nó đã gồm lớp model, mà lại dùng được cả khi chạy tay với
    cấu hình không có file model (khi đó chỉ đường prompt chạy được - đường encoder bắt buộc có
    `lora.target_modules` của model). Nhờ vậy chỗ rẽ nhánh không phụ thuộc việc đọc file.
    """
    value = str((config_data or {}).get("approach") or "").strip()
    if value:
        return value
    if model_id:
        try:
            return approach(model_id)
        except ModelConfigError:
            return "prompt"
    return "prompt"


def lora(name):
    """Nhóm `lora` của một model: thứ riêng của model cho huấn luyện; rỗng nếu model không khai."""
    return dict(load(name).get("lora") or {})


def max_length(name):
    """Ngưỡng cắt đang dùng cho một model: (giá trị, nguồn hiển thị được).

    Chỉ có MỘT nguồn là `preprocess.max_length` của file cấu hình; không có giá trị mặc định
    trong code, vì mặc định trong code là thứ âm thầm khác với thứ đang chạy. Nơi ĐO
    (`token_stats`) và nơi DÙNG (`build_inputs`) đều đọc qua đây nên không thể lệch nhau -
    lệch là mọi kết luận "input có bị cắt hay không" sai hết.

    Trả về cả NGUỒN vì một con số không rõ từ đâu ra là con số không kiểm tra được: nó được
    in khi chạy và ghi vào cột `max_length` của file số liệu.
    """
    value = preprocess(name)["max_length"]
    return int(value), _display(config_path(name))


def checkpoint(name):
    """Tên model trên Hugging Face, để đối chiếu tránh nhầm model."""
    return load(name)["checkpoint"]


def _display(path):
    """Đường dẫn tương đối so với gốc dự án, cho dễ đọc trong thông báo lỗi."""
    try:
        return path.relative_to(config.ROOT_DIR).as_posix()
    except ValueError:
        return str(path)
