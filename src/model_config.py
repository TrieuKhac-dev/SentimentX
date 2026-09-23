# -*- coding: utf-8 -*-
"""Cấu hình riêng của từng model: configs/models/<tên>.yaml.

VÌ SAO TÁCH KHỎI configs/pipeline.yaml
--------------------------------------
`pipeline.yaml` mô tả "ta xử lý DỮ LIỆU thế nào", và nội dung file đó được đưa vào
hash để sinh MÃ PHIÊN BẢN DỮ LIỆU (src/versioning.py). Còn file ở đây mô tả "MODEL
đọc dữ liệu thế nào" (dùng prompt nào, có chèn lượt assistant hay không) — đổi
prompt không làm đổi một dòng dữ liệu nào, nên không được nằm trong hash đó. Để
chung một file sẽ sinh ra những mã phiên bản mới vô nghĩa cho cùng một dataset.

MỘT FILE GỒM NHỮNG GÌ
---------------------
    prompt                : tên file trong configs/prompts/ (bắt buộc)
    add_generation_prompt : chèn lượt "assistant" rỗng ở cuối hội thoại (mặc định true)

Model nào không có file ở đây (PhoBERT, ViSoBERT) nghĩa là cấu hình của nó chỉ gồm
hằng số trong module tương ứng (tên model, `max_length`, bộ tách từ).

Gõ sai TÊN KHOÁ là lỗi hay gặp (`promt:` thay vì `prompt:`), nên file này báo lỗi
kèm gợi ý thay vì âm thầm bỏ qua — bỏ qua sẽ khiến prompt nằm lại ở mặc định mà
người dùng không biết.
"""

import difflib
from functools import lru_cache

import yaml

from src import config

# Khoá được phép dùng trong configs/models/<tên>.yaml
KNOWN_KEYS = ("prompt", "add_generation_prompt", "max_length")

CONFIG_HINT = "Xem configs/models/qwen.yaml để biết các khoá cần có."

# Khoá `max_length` là ngưỡng cắt input (số token) — xem ghi chú ở đầu file này và ở
# hàm max_length() phía dưới. Đây là chỗ để THỬ NGHIỆM mà không phải sửa code.


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


@lru_cache(maxsize=None)
def load(name):
    """Đọc + kiểm tra cấu hình của một model (BẮT BUỘC có file). Báo lỗi rõ nếu thiếu.

    File THIẾU là lỗi (không phải "dùng mặc định"): model gọi hàm này là model có
    cấu hình riêng, và thiếu file nghĩa là ta không biết nó đang chạy với prompt
    nào — đo ra số liệu mà không biết prompt nào thì số liệu không dùng được.
    """
    path = config_path(name)
    if not path.exists():
        hint = suggest(name)
        raise ModelConfigError(
            "Không tìm thấy cấu hình model '{}' tại {}. Các model có cấu hình: "
            "{}. {}{}".format(
                name, _display(path), ", ".join(available()) or "(trống)",
                hint + " " if hint else "", CONFIG_HINT)
        )

    cfg = dict(optional(name))
    if not str(cfg.get("prompt") or "").strip():
        raise ModelConfigError(
            "{}: thiếu khoá 'prompt' (tên file prompt trong configs/prompts/). "
            "Ví dụ:\n    prompt: {}".format(
                _display(path), _first_prompt_name())
        )

    cfg["add_generation_prompt"] = bool(cfg.get("add_generation_prompt", True))
    cfg["_path"] = path
    return cfg


@lru_cache(maxsize=None)
def optional(name):
    """Đọc cấu hình NẾU CÓ file; không có file thì trả về {} (khác `load` là không bắt buộc).

    Nhờ vậy một model chỉ muốn ghi đè một khoá (ví dụ `max_length`) không phải tạo file
    cấu hình đầy đủ — và PhoBERT / ViSoBERT (không có khoá `prompt`) vẫn dùng được cơ chế
    này y như Qwen.
    """
    path = config_path(name)
    if not path.exists():
        return {}

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

    value = cfg.get("max_length")
    if value is not None and (isinstance(value, bool)
                              or not isinstance(value, int) or value <= 0):
        raise ModelConfigError(
            "{}: 'max_length' phải là số nguyên dương (đang là {!r}). Đơn vị là TOKEN, "
            "tính cả token đặc biệt và cả prompt.".format(_display(path), value)
        )
    return cfg


def max_length(name, default):
    """Ngưỡng cắt đang dùng cho một model: (giá trị, nguồn hiển thị được).

    Thứ tự áp dụng: khoá `max_length` trong configs/models/<tên>.yaml > hằng số `default`
    của module model. (`--max-length` trên dòng lệnh đứng TRÊN cả hai, xử lý ở
    src/preprocessing/token_stats.py.)

    VÌ SAO cho thử ở YAML: `max_length` là một BIẾN THỰC NGHIỆM (đổi ngưỡng cắt là đổi
    input), mà hằng số trong code thì mỗi lần thử lại phải sửa code. Vì sao KHÔNG để ở
    configs/pipeline.yaml: file đó bị đưa vào hash sinh MÃ PHIÊN BẢN DỮ LIỆU, nên đổi
    ngưỡng cắt sẽ đẻ ra mã phiên bản dữ liệu mới cho cùng một dataset — dữ liệu không đổi.

    Trả về cả NGUỒN vì một con số không rõ từ đâu ra là con số không kiểm tra được: nó
    được in khi chạy, ghi vào cột `max_length` của CSV và vào mục lục.
    """
    value = optional(name).get("max_length")
    if value:
        return int(value), _display(config_path(name))
    return int(default), "hằng số MAX_LENGTH trong module model"


def prompt_name(name):
    """Tiện dụng: tên prompt mà một model đang dùng."""
    return load(name)["prompt"]


def _first_prompt_name():
    """Tên prompt đầu tiên đang có, để điền vào thông báo lỗi cho dễ hình dung."""
    from src import prompts
    names = prompts.available()
    return names[0] if names else "qwen_absa_v1"


def _display(path):
    """Đường dẫn tương đối so với gốc dự án, cho dễ đọc trong thông báo lỗi."""
    try:
        return path.relative_to(config.ROOT_DIR).as_posix()
    except ValueError:
        return str(path)
