# -*- coding: utf-8 -*-
"""Pipeline bước 4 - NORMALIZE.

Chuẩn hoá văn bản theo config (mỗi phép đều có thể BẬT/TẮT):
- Chữ thường (tuỳ chọn; mặc định TẮT)
- Unicode (NFC)
- Khoảng trắng / xuống dòng
- Rút gọn ký tự lặp (tuỳ chọn)

Bước này KHÔNG bỏ dấu tiếng Việt và KHÔNG thay teencode: nó chỉ chuẩn hoá hình
thức văn bản, không đoán nghĩa. Việc bỏ dấu tiếng Việt chỉ xảy ra bên trong KHOÁ
so trùng của bước Clean (`utils.dedup_key`) - khoá đó không bao giờ thay văn bản.

RÀNG BUỘC QUAN TRỌNG (invariant):
Bước này chỉ được sửa CỘT VĂN BẢN. Nhãn phải giữ nguyên tuyệt đối.
Cuối bước có kiểm tra "dấu vân tay nhãn" trước và sau để chứng minh điều đó.
"""

import hashlib

from src import config, utils


def labels_signature(splits, aspects):
    """Tạo 'dấu vân tay' cho toàn bộ nhãn.

    Nếu chuỗi dấu vân tay trước và sau khi chuẩn hoá giống nhau,
    ta chứng minh được rằng quá trình chuẩn hoá KHÔNG làm đổi nhãn.
    Hàm này được cả bước Normalize và Final Validate dùng chung.
    """
    digest = hashlib.sha256()
    for name in sorted(splits):
        stripped = splits[name][aspects].astype(str).apply(lambda col: col.str.strip())
        for aspect in aspects:
            digest.update("|".join(stripped[aspect].tolist()).encode("utf-8"))
    return digest.hexdigest()


def normalize_steps(text, ncfg):
    """Áp dụng lần lượt các phép chuẩn hoá đang BẬT.

    Trả về (văn bản mới, danh sách tên phép ĐÃ THỰC SỰ làm thay đổi văn bản).

    Hàm này là NGUỒN DUY NHẤT định nghĩa "chuẩn hoá là gì": bước Normalize dùng
    nó để sửa dữ liệu, và bước Final Validate dùng lại chính nó để chứng minh
    văn bản sau pipeline đúng bằng văn bản gốc sau chuẩn hoá (không mất dấu
    tiếng Việt, không bị bỏ dấu câu...).
    """
    changed = []
    result = text
    if ncfg["lowercase"]:
        step = result.lower()
        if step != result:
            changed.append("chữ thường")
        result = step
    if ncfg["unicode"]:
        step = utils.normalize_unicode(result)
        if step != result:
            changed.append("unicode (NFC)")
        result = step
    if ncfg["whitespace"]:
        step = utils.normalize_whitespace(result)
        if step != result:
            changed.append("khoảng trắng")
        result = step
    if ncfg["repeated_chars"]:
        step = utils.collapse_repeated_chars(result, int(ncfg["repeated_chars_max"]))
        if step != result:
            changed.append("ký tự lặp")
        result = step
    return result, changed

def run(context):
    cfg = context["config"]
    ncfg = cfg["normalize"]
    splits = context["splits"]
    out_dir = context["out_dir"]
    aspects = context["dataset"]["aspects"]

    # Dấu vân tay nhãn TRƯỚC khi chuẩn hoá
    signature_before = labels_signature(splits, aspects)
    context["labels_signature_before_normalize"] = signature_before

    # Các phép đang BẬT, theo đúng thứ tự áp dụng
    method_labels = []
    if ncfg["lowercase"]:
        method_labels.append("chữ thường")
    if ncfg["unicode"]:
        method_labels.append("unicode (NFC)")
    if ncfg["whitespace"]:
        method_labels.append("khoảng trắng")
    if ncfg["repeated_chars"]:
        method_labels.append("ký tự lặp")

    total = 0
    changed = 0
    samples = []
    empty_after = []
    changed_per_split = {}
    changed_by_method = {label: {} for label in method_labels}

    for name, df in splits.items():
        texts = df[config.TEXT_COLUMN].astype(str).tolist()
        new_texts = []
        changed_here = 0
        for label in method_labels:
            changed_by_method[label][name] = 0
        for index, text in enumerate(texts):
            total += 1
            new_text, methods = normalize_steps(text, ncfg)
            for label in methods:
                changed_by_method[label][name] += 1
            if new_text != text:
                changed += 1
                changed_here += 1
                if len(samples) < 12:
                    before, after = utils.diff_window(text, new_text)
                    samples.append([
                        name,
                        " + ".join(methods) if methods else "-",
                        before,
                        after,
                    ])
            if new_text.strip() == "":
                empty_after.append([name, index])
            new_texts.append(new_text)
        changed_per_split[name] = changed_here
        df.loc[:, config.TEXT_COLUMN] = new_texts

    # Dấu vân tay nhãn SAU khi chuẩn hoá
    labels_unchanged = signature_before == labels_signature(splits, aspects)

    samples_path = utils.write_csv(
        samples or [["-", "-", "không có thay đổi", ""]],
        ["split", "phép đã thay đổi", "trước (đoạn khác nhau)",
         "sau (đoạn khác nhau)"],
        out_dir / "normalize_samples.csv",
    )

    config_rows = [
        ["lowercase (chuyển về chữ thường)", utils.on_off(ncfg["lowercase"])],
        ["unicode (chuẩn hoá Unicode NFC)", utils.on_off(ncfg["unicode"])],
        ["whitespace (chuẩn hoá khoảng trắng)", utils.on_off(ncfg["whitespace"])],
        ["repeated_chars (rút gọn ký tự lặp)", utils.on_off(ncfg["repeated_chars"])],
        ["repeated_chars_max (số lần ký tự được giữ lại)",
         ncfg["repeated_chars_max"]],
    ]

    # Biểu đồ chỉ vẽ các phép ĐANG BẬT, nên đổi config là biểu đồ đổi theo.
    change_chart = {
        "title": "Số review bị thay đổi bởi từng phép chuẩn hoá",
        "kind": "grouped_bar",
        "x": list(changed_per_split),
        "series": {
            label: [changed_by_method[label].get(name, 0)
                    for name in changed_per_split]
            for label in method_labels
        },
        "y_label": "số review",
    }

    return {
        "id": "pipeline_normalize",
        "title": "Step 4 - Normalize (chuẩn hoá văn bản)",
        "cards": [
            {"label": "Số review đã xét", "value": "{}".format(total)},
            {"label": "Số review bị thay đổi", "value": "{}".format(changed)},
            {"label": "Nhãn có bị bước này thay đổi?",
             "value": "Không" if labels_unchanged else "CÓ"},
            {"label": "Số review thành rỗng sau chuẩn hoá", "value": len(empty_after)},
        ],
        "charts": [change_chart],
        "tables": [
            {
                "title": "Cấu hình chuẩn hoá đang áp dụng",
                "columns": ["thiết lập", "giá trị"],
                "rows": config_rows,
            },
            {
                "title": "Số review có thay đổi, theo split",
                "columns": ["split", "số review", "bị thay đổi",
                            "tỉ lệ bị thay đổi %"],
                "rows": [
                    [
                        name,
                        len(splits[name]),
                        changed_per_split[name],
                        round(100 * changed_per_split[name] / (len(splits[name]) or 1), 2),
                    ]
                    for name in changed_per_split
                ],
                "num_columns": [1, 2, 3],
            },
        ],
        "files": [utils.rel(samples_path)],
    }
