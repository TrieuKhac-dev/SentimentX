# -*- coding: utf-8 -*-
"""Bộ đọc kết quả của model sinh (pha 4).

VÌ SAO PHẢI CÓ MỘT MODULE RIÊNG, VÀ VÌ SAO NÓ PHẢI ĐƯỢC KIỂM BẰNG TEST
-------------------------------------------------------------------
Model sinh trả về VĂN BẢN, không trả về nhãn. Mọi chỉ số (F1, độ chính xác) đều đi qua
hàm đọc này, nên một lỗi ở đây làm SAI TOÀN BỘ BẢNG ĐIỂM mà không có gì báo động: JSON
đọc hụt một khía cạnh thì khía cạnh đó bị tính là "không nhắc tới", và điểm số trông vẫn
hợp lí. Vì vậy:

    - hàm đọc là hàm THUẦN (không I/O, không model) nên kiểm được bằng test;
    - mọi trường hợp KHÔNG đọc được đều trả về lí do CỤ THỂ, không âm thầm trả nhãn 0;
    - có test ở tests/test_parse.py (`python -m unittest discover -s tests`).

HAI ĐỊNH DẠNG ĐẦU RA CẦN ĐỌC
----------------------------
    prompt một lượt : {"khoá": mã, ...}                     — đọc cả câu trả lời
    prompt CoT      : ... SUY LUẬN: ... KẾT QUẢ: {"khoá": mã, ...}
                      — phải lấy khối SAU dấu "KẾT QUẢ:", nếu không sẽ đọc phải JSON nằm
                        trong phần suy luận (nếu model có trích JSON ở giữa).

Dấu "KẾT QUẢ:" là QUY ƯỚC CỦA DỰ ÁN (đặt trong configs/prompts/*.txt), không phải chuẩn
của Qwen — nên bộ đọc nhận cả vài biến thể gõ thiếu dấu, và luôn có đường lui: không thấy
dấu thì tìm object JSON CUỐI CÙNG trong câu trả lời, và GHI RÕ đã dùng đường lui nào.
"""

import json
import re

# Các cách viết dấu mở khối kết quả (kể cả gõ thiếu dấu, model hay mắc khi trả lời nhanh)
RESULT_MARKERS = ("KẾT QUẢ:", "KẾT QUA:", "KET QUA:", "KẾT QUẢ :", "KETQUA:")

# Khối suy luận: chỉ dùng để ĐẾM (model có suy luận hay không), không dùng để chấm điểm
REASONING_MARKERS = ("SUY LUẬN:", "SUY LUAN:", "SUY LUẬN :")

# Model 2507 là bản non-thinking (không sinh <think></think>), nhưng tokenizer vẫn có sẵn
# token tương ứng nên phải KIỂM TRA chứ không giả định: nếu có thì cắt trước khi đọc JSON.
_THINK_RE = re.compile(r"<think(?:ing)?>.*?</think(?:ing)?>", re.S | re.I)

OK = "ok"
NO_RESULT = "không thấy khối kết quả"
BAD_JSON = "JSON không hợp lệ"
NOT_OBJECT = "kết quả không phải object JSON"
BAD_KEYS = "khoá không khớp bộ khía cạnh"
BAD_CODES = "mã nhãn không hợp lệ"


def strip_thinking(text):
    """Bỏ khối <think>...</think> nếu có. Trả về (văn bản sạch, có gặp khối không)."""
    found = bool(_THINK_RE.search(text))
    return _THINK_RE.sub(" ", text), found


def tail_after_marker(text, markers=RESULT_MARKERS):
    """Phần văn bản SAU dấu mở khối kết quả (lấy dấu xuất hiện CUỐI CÙNG), hoặc None."""
    lowered = text.upper()
    position = -1
    for marker in markers:
        index = lowered.rfind(marker.upper())
        position = max(position, index)
    if position < 0:
        return None
    return text[position + len("KẾT QUẢ:"):]


def json_objects(text):
    """Mọi object JSON CÂN BẰNG trong văn bản, theo thứ tự xuất hiện.

    Tự đếm ngoặc (không dùng regex) để chịu được ngoặc nhọn và dấu ngoặc kép nằm TRONG
    chuỗi — ví dụ review có chứa dấu "{" hoặc "}". Đây là chỗ dễ sai nhất khi viết bằng
    regex, nên phải làm bằng tay và có test.
    """
    objects = []
    depth = 0
    start = None
    in_string = False
    escaped = False

    for index, char in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}":
            if depth:
                depth -= 1
                if depth == 0 and start is not None:
                    objects.append(text[start:index + 1])
                    start = None
    return objects


def has_reasoning(text):
    """Câu trả lời có khối suy luận hay không (để báo cáo, không để chấm điểm)."""
    upper = text.upper()
    return any(marker in upper for marker in REASONING_MARKERS)


def parse_labels(answer, aspects, codes, require_all=None):
    """Đọc nhãn từ câu trả lời của model. Trả về (labels, info).

    labels: dict {khía cạnh: mã}. Chỉ chứa khía cạnh ĐỌC ĐƯỢC — thiếu khía cạnh nào thì
            `info["thiếu"]` ghi rõ, và nơi chấm điểm phải coi đó là SAI (không được điền 0
            hộ, vì điền 0 là biến lỗi định dạng thành một dự đoán "không nhắc tới").
    info  : {"valid", "reason", "kiểu đọc", "had_thinking", "has_reasoning", "thiếu", "lạ",
             "mã sai"}

    `require_all=True` thì thiếu khía cạnh bị coi là KHÔNG hợp lệ (dùng khi muốn đo chặt).
    """
    aspects = list(aspects)
    allowed = {int(code) for code in codes}
    info = {
        "valid": False,
        "reason": NO_RESULT,
        "kiểu đọc": "không đọc được",
        "had_thinking": False,
        "has_reasoning": has_reasoning(answer),
        "thiếu": [],
        "lạ": [],
        "mã sai": {},
    }

    text, info["had_thinking"] = strip_thinking(answer)
    if not text.strip():
        info["reason"] = "câu trả lời rỗng"
        return {}, info

    tail = tail_after_marker(text)
    if tail is None:
        candidates, method = json_objects(text), "đường lui: object JSON cuối cùng"
    else:
        candidates, method = json_objects(tail), "khối KẾT QUẢ"
    if not candidates:
        info["reason"] = NO_RESULT if tail is not None else "không thấy JSON nào"
        return {}, info

    # Lấy object CUỐI CÙNG: với CoT, đáp án nằm ở cuối; nếu model có trích JSON trong phần
    # suy luận thì object cuối vẫn là đáp án.
    try:
        parsed = json.loads(candidates[-1])
    except ValueError as exc:
        info["reason"] = "{} ({})".format(BAD_JSON, exc)
        info["kiểu đọc"] = method
        return {}, info

    if not isinstance(parsed, dict):
        info["reason"] = NOT_OBJECT
        info["kiểu đọc"] = method
        return {}, info

    labels, bad_codes = {}, {}
    for key, value in parsed.items():
        name = str(key).strip()
        if name not in aspects:
            info["lạ"].append(name)
            continue
        try:
            code = int(value)
        except (TypeError, ValueError):
            bad_codes[name] = value
            continue
        if code not in allowed:
            bad_codes[name] = value
            continue
        labels[name] = code

    info["thiếu"] = [name for name in aspects if name not in labels]
    info["lạ"] = sorted(set(info["lạ"]))
    info["mã sai"] = bad_codes
    info["kiểu đọc"] = method
    info["valid"] = bool(labels) and not bad_codes
    if info["thiếu"] and require_all:
        info["valid"] = False
    if not labels:
        info["reason"] = BAD_KEYS if info["lạ"] else BAD_CODES
    elif bad_codes:
        info["reason"] = BAD_CODES
    elif info["thiếu"]:
        info["reason"] = "{} (thiếu {})".format(OK, ", ".join(info["thiếu"]))
    else:
        info["reason"] = OK
    return labels, info
