# -*- coding: utf-8 -*-
"""Registry các KHÔNG GIAN NHÃN.

Không gian nhãn là cách một thí nghiệm nhìn bài toán: `full` giữ đủ bốn trạng thái, `binary` chỉ
giữ positive/negative và chấm "có nhắc tới hay không" như một quyết định riêng.

Thêm một không gian mới: viết một module trong thư mục này theo hợp đồng ở `base.py`, rồi thêm
một dòng vào `LABEL_SPACES`. Metric không phải sửa.

CẢNH BÁO VỀ SO SÁNH
Kết quả chỉ so được với công bố tham chiếu khi dùng `label_space`/`neutral_policy` giống công bố.
Đổi hai giá trị đó là đổi bài toán, không phải đổi cách trình bày.
"""

from src.labels import base, binary, full

# Bốn mã nhãn của dataset, xuất lại cho nơi gọi dùng mà không phải với vào `base`.
NOT_MENTIONED = base.NOT_MENTIONED
POSITIVE = base.POSITIVE
NEGATIVE = base.NEGATIVE
NEUTRAL = base.NEUTRAL

LABEL_SPACES = {
    binary.NAME: binary,
    full.NAME: full,
}


def available():
    """Tên các không gian nhãn đang có."""
    return sorted(LABEL_SPACES)


def get(name):
    """Module của một không gian nhãn. Tên sai thì báo lỗi kèm danh sách."""
    if name not in LABEL_SPACES:
        raise base.LabelError(
            "Không có không gian nhãn '{}'. Các không gian hiện có: {}.".format(
                name, ", ".join(available())))
    return LABEL_SPACES[name]


def check(label_space, neutral_policy, not_mentioned):
    """Kiểm bộ ba khai trong `configs/experiments/task.yaml` có dùng được không."""
    get(label_space).check(neutral_policy, not_mentioned)


def project(gold, pred, label_space, neutral_policy, not_mentioned):
    """Chiếu (nhãn đúng, nhãn đoán) sang không gian nhãn của thí nghiệm.

    Trả về dict gồm `gold`, `pred` đã chiếu, `dropped_neutral` (số ô bị loại) và các trường khai
    báo để ghi vào `metrics.json`.
    """
    return get(label_space).project(gold, pred, neutral_policy, not_mentioned)


def describe():
    """Vài dòng mô tả các không gian nhãn, để in ra khi cần."""
    lines = []
    for name in available():
        module = LABEL_SPACES[name]
        lines.append("{}: {} (mã hợp lệ: {})".format(
            name, module.DESCRIPTION, ", ".join(str(code) for code in module.CODES)))
    return lines


def allowed_codes(name, neutral_policy):
    """Các mã nhãn mà model ĐƯỢC PHÉP trả lời trong không gian này.

    Dùng để dựng bảng mã nhãn cho prompt: đưa cho model một nhãn mà không gian nhãn không có
    nghĩa là mọi câu trả lời đó đều bị tính sai.
    """
    module = get(name)
    codes = [code for code in module.CODES if code != base.NEUTRAL]
    if neutral_policy == "keep":
        codes.append(base.NEUTRAL)
    return codes


def task_aspects(task, available):
    """Khía cạnh đem chấm theo `task.aspects`: `all` hoặc danh sách, giữ thứ tự của dataset.

    Tên khía cạnh không có trong dataset là LỖI chứ không bỏ qua: bỏ qua thì thí nghiệm chạy trên
    tập khía cạnh khác với khai báo, và người đọc số liệu không có cách nào biết.
    """
    wanted = (task or {}).get("aspects") or "all"
    available = list(available)
    if wanted == "all":
        return available
    unknown = [name for name in wanted if name not in available]
    if unknown:
        raise base.LabelError(
            "task.aspects có khía cạnh không có trong dataset: {}. Dataset đang có: {}.".format(
                ", ".join(unknown), ", ".join(available)))
    return [name for name in available if name in wanted]


def filter_label_map(label_map, name, neutral_policy):
    """Lọc `label_map.json` của dataset để chỉ còn các nhãn dùng được cho thí nghiệm.

    Trả về bản sao của `label_map` với `aspects` giữ nguyên và `labels`/`id_to_label` đã lọc.
    Nhờ vậy bảng mã nhãn đưa cho model (và bảng in trong báo cáo) khớp đúng không gian nhãn.
    """
    keep = set(allowed_codes(name, neutral_policy))
    filtered = dict(label_map)
    filtered["labels"] = [label for label in label_map.get("labels") or []]
    filtered["id_to_label"] = {
        str(code): label for code, label in (label_map.get("id_to_label") or {}).items()
        if int(code) in keep
    }
    filtered["label_space"] = name
    filtered["neutral_policy"] = neutral_policy
    return filtered
