# -*- coding: utf-8 -*-
"""Bộ đọc kết quả của model sinh (đánh giá model).

VÌ SAO PHẢI CÓ MỘT MODULE RIÊNG, VÀ VÌ SAO NÓ PHẢI ĐƯỢC KIỂM BẰNG TEST
---
Model sinh trả về VĂN BẢN, không trả về nhãn. Mọi chỉ số (F1, độ chính xác) đều đi qua
hàm đọc này, nên một lỗi ở đây làm SAI TOÀN BỘ BẢNG ĐIỂM mà không có gì báo động: JSON
đọc hụt một khía cạnh thì khía cạnh đó bị tính là "không nhắc tới", và điểm số trông vẫn
hợp lí. Vì vậy:

    - hàm đọc là hàm THUẦN (không I/O, không model) nên kiểm được bằng test;
    - mọi trường hợp KHÔNG đọc được đều trả về lí do CỤ THỂ, không âm thầm trả nhãn 0;
    - có test ở tests/evaluation/test_parse.py (`python -m unittest discover -s tests`).

HAI ĐỊNH DẠNG ĐẦU RA CẦN ĐỌC
---
    prompt một lượt : {"khoá": mã, ...}                     - đọc cả câu trả lời
    prompt CoT      : ... SUY LUẬN: ... KẾT QUẢ: {"khoá": mã, ...}
                      - phải lấy khối SAU dấu "KẾT QUẢ:", nếu không sẽ đọc phải JSON nằm
                        trong phần suy luận (nếu model có trích JSON ở giữa).

Dấu "KẾT QUẢ:" là QUY ƯỚC CỦA DỰ ÁN (đặt trong configs/prompts/*.txt), không phải chuẩn
của Qwen - nên bộ đọc nhận cả vài biến thể gõ thiếu dấu, và luôn có đường lui: không thấy
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

# Dấu mã nhãn ở cuối một dòng SUY LUẬN, ví dụ "mã 2" (không phân biệt hoa thường).
_CODE_RE = re.compile(r"mã\s*\d", re.I)

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
    chuỗi - ví dụ review có chứa dấu "{" hoặc "}". Đây là chỗ dễ sai nhất khi viết bằng
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

    labels: dict {khía cạnh: mã}. Chỉ chứa khía cạnh ĐỌC ĐƯỢC - thiếu khía cạnh nào thì
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


def parse_evidence(answer, aspects):
    """Đọc phần trích dẫn (quote) và lí do (reason) trong khối SUY LUẬN.

    Hàm THUẦN này chỉ phục vụ HIỂN THỊ, KHÔNG dùng để chấm điểm: mã nhãn vẫn do
    ``parse_labels`` đọc từ khối KẾT QUẢ. Trả về ``{khía cạnh: {"quote": ..., "reason": ...}}``
    cho MỌI khía cạnh trong ``aspects``, với ``None`` khi model không viết dòng tương ứng.

    Tuyệt đối không suy diễn hay bịa thêm: chỉ lấy đúng chuỗi model đã sinh. Vì vậy chuỗi
    ``"không nhắc tới"`` do model viết (không kèm ngoặc kép) được giữ NGUYÊN VĂN, không bị
    đổi thành ``None`` - người xem cần thấy đó là câu model thật sự trả lời.

    Định dạng mỗi dòng (sau dấu ``-``, ``*`` hoặc ``•``)::

        - colour: "màu 102 rất bợt" | màu lệch và bợt so với kỳ vọng | mã 2

    Phần trước dấu ``:``/``：`` là một hoặc nhiều khía cạnh (cách nhau bởi dấu phẩy).
    Phần sau chia bởi ``|``: đoạn đầu là quote, đoạn cuối nếu chứa ``mã <số>`` là mã nhãn
    (bỏ qua), các đoạn còn lại ghép thành reason. Dòng không có ``|`` hoặc không có khía
    cạnh hợp lệ bị bỏ qua. Hàm không ném lỗi với đầu vào dị dạng.
    """
    aspects = [str(name) for name in (aspects or [])]
    result = {
        aspect.strip(): {"quote": None, "reason": None} for aspect in aspects
    }

    canonical = {}
    for aspect in result:
        canonical.setdefault(aspect.lower(), aspect)

    if not answer:
        return result

    text = str(answer).replace("\\n", "\n")
    text, _had_thinking = strip_thinking(text)

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line[0] not in "-*•":
            continue
        line = line[1:].strip()
        if not line:
            continue

        parts = re.split(r"[:：]", line, maxsplit=1)
        if len(parts) != 2:
            continue
        aspect_part, rest = parts
        if "|" not in rest:
            continue

        names = []
        for raw_name in aspect_part.split(","):
            name = raw_name.strip().lower()
            if name == "packaging":
                name = "packing"
            aspect = canonical.get(name)
            if aspect is not None and aspect not in names:
                names.append(aspect)
        if not names:
            continue

        segments = [segment.strip() for segment in rest.split("|")]
        quote = segments[0]
        if len(quote) >= 2 and (
            (quote[0] == '"' and quote[-1] == '"')
            or (quote[0] == "“" and quote[-1] == "”")
        ):
            quote = quote[1:-1]
        quote = quote.strip() or None

        reason_segments = segments[1:]
        if reason_segments and _CODE_RE.search(reason_segments[-1]):
            reason_segments = reason_segments[:-1]
        reason = " | ".join(
            segment for segment in reason_segments if segment
        ).strip()
        if len(reason) >= 2 and (
            (reason[0] == '"' and reason[-1] == '"')
            or (reason[0] == "“" and reason[-1] == "”")
        ):
            reason = reason[1:-1]
        reason = reason.strip() or None

        for aspect in names:
            entry = result[aspect]
            if entry["quote"] is None and quote is not None:
                entry["quote"] = quote
            if entry["reason"] is None and reason is not None:
                entry["reason"] = reason

    return result

