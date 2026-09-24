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

import yaml

from src import model_config, paths, utils

# Năm file cấu hình dùng chung, theo đúng thứ tự hợp nhất.
SHARED = ("repo", "task", "evaluation", "training", "tracking")

# Nhãn lớp dùng trong `sources` và trong bảng ghi đè.
MODEL_LAYER = "model"
EXPERIMENT_LAYER = "experiment"


class ExperimentError(Exception):
    """Lỗi cấu hình thí nghiệm: thiếu file, thiếu khoá, khoá không hợp lệ."""


def experiment_dir(model_id, method, exp_id):
    """Thư mục định nghĩa một thí nghiệm: `experiments/<model_id>/<method>/<exp_id>/`."""
    return paths.experiment_dir(model_id, method, exp_id)


def config_path(model_id, method, exp_id):
    """Đường dẫn file config riêng của thí nghiệm."""
    return experiment_dir(model_id, method, exp_id) / paths.pattern("experiment_config")


def layer_files(model_id, method, exp_id):
    """Danh sách (nhãn lớp, đường dẫn) theo ĐÚNG thứ tự hợp nhất."""
    files = [(MODEL_LAYER, model_config.config_path(model_id))]
    for name in SHARED:
        files.append((name, paths.config_path("experiments", "{}.yaml".format(name))))
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
    layers = layer_files(model_id, method, exp_id)
    config, history, sources = {}, {}, {}
    for label, path in layers:
        data = _read(label, path, model_id)
        _merge_into(config, history, sources, data, label)

    return {
        "model_id": model_id,
        "method": method,
        "exp_id": exp_id,
        "dir": experiment_dir(model_id, method, exp_id),
        "config": config,
        "sources": sources,
        "overrides": _overrides(history),
        "layers": [[label, utils.rel(path)] for label, path in layers],
        "history": history,
    }


def _read(label, path, model_id):
    """Nội dung một lớp. Riêng lớp model đi qua `model_config` để được kiểm tra đầy đủ."""
    if label == MODEL_LAYER:
        return model_config.load(model_id)
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
    """
    for key, value in data.items():
        if str(key).startswith("_"):
            continue
        name = "{}.{}".format(prefix, key) if prefix else str(key)
        if isinstance(value, dict):
            node = target.get(key)
            # Lớp trước có thể đã đặt giá trị vô hướng ở đúng khoá này: thay bằng nhóm khoá mới
            # thay vì báo lỗi, vì hợp nhất chỉ có nghĩa "lớp sau thắng".
            if not isinstance(node, dict):
                node = {}
                target[key] = node
            _merge_into(node, history, sources, value, label, name)
        else:
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