# -*- coding: utf-8 -*-
"""Bảng dự đoán: tên cột, đổi thành dữ liệu để chấm, và gộp nhiều lượt chạy.

VÌ SAO TÊN CỘT Ở ĐÂY
Bảng dự đoán là ĐỊNH DẠNG dùng chung cho ba việc: ghi `predictions.csv`, ghi khối
`predictions/part_*.jsonl` để chạy tiếp, và gộp nhiều lượt chạy lại khi chấm. Ba chỗ đó phải nói
cùng một tên cột, nên tên cột nằm ở đây - module thuần, KHÔNG cần torch.

`nhãn đúng` và `nhãn đoán` là JSON trong một ô CSV: nhãn là dict theo khía cạnh, mà CSV chỉ có
một ô cho mỗi khía cạnh được. Nhờ vậy file dự đoán tự chứa đủ để chấm lại mà không cần đọc lại
dataset - đổi cách chấm thì không phải chạy lại model.
"""

import json

# Cột của bảng kết quả (cũng là cột file CSV dự đoán và khoá của từng dòng JSONL).
# `tình trạng đọc` (trước đây tên là `lí do`) là KẾT LUẬN của bộ đọc: `ok` khi đọc được trọn vẹn, còn
# lại là lý do cụ thể (xem bảng giá trị ở docs/04_experiments/05_predictions.md). Đổi tên vì "lí do"
# đọc như một trường tự do, trong khi đây là tập giá trị đóng do `src/evaluation/parse.py` quyết định.
COLUMNS = [
    "chỉ số", "split", "prompt", "kiểu đọc", "đọc được", "tình trạng đọc",
    "text", "nhãn đúng", "nhãn đoán",
    "token sinh", "giây", "có suy luận", "có <think>", "câu trả lời",
]

REASON_COLUMN = "tình trạng đọc"

# Cột nhận diện một mẫu. Dùng để bỏ qua mẫu đã chạy khi chạy tiếp.
KEY = COLUMNS[0]
KEY_INDEX = COLUMNS.index(KEY)

MENTIONED = "có"

# Cột chỉ có ở đường chạy dùng PROMPT (model chỉ dẫn - LLM): chuỗi ĐÃ GỬI cho model, sau chat
# template và sau khi cắt ở `max_length`. Nhờ nó, muốn biết "mẫu này thành prompt nào rồi model
# trả lời ra sao" thì đọc thẳng `predictions.csv`, không phải chạy lại gì.
#
# Model encoder (PhoBERT, ViSoBERT) học từ chuỗi thô, KHÔNG có prompt nào để ghi - bảng của chúng
# không có cột này. Vì vậy cột không nằm trong `COLUMNS` mà do `columns(with_prompt=True)` thêm vào.
PROMPT_COLUMN = "prompt gửi model"
ANSWER_COLUMN = "câu trả lời"


def columns(with_prompt=False):
    """Cột của bảng dự đoán cho MỘT đường chạy.

    `with_prompt=True` chèn cột prompt NGAY TRƯỚC cột `câu trả lời`, để đọc một dòng là thấy liền
    mạch: câu hỏi (prompt) -> câu trả lời -> nhãn đọc được. Thứ tự còn lại giữ nguyên như bảng cũ,
    nên file của model encoder và file của LLM chỉ khác nhau đúng một cột.
    """
    base = list(COLUMNS)
    if not with_prompt:
        return base
    index = base.index(ANSWER_COLUMN)
    return base[:index] + [PROMPT_COLUMN] + base[index:]


def as_dict(row, columns=None):
    """Một dòng có thể là dict (đọc từ JSONL) hoặc list (vừa chạy trong bộ nhớ): đưa về dict.

    Hai dạng cùng tồn tại là có lý: file khối tự mô tả bằng tên cột, còn lúc đang chạy thì dòng
    còn là list cho khớp với `csv`. Mọi chỗ đọc dòng đều đi qua đây để không phải đoán.
    """
    if isinstance(row, dict):
        return row
    return dict(zip(list(columns or COLUMNS), row))


def key_of(row):
    """Khoá của một dòng (chỉ số dòng gốc trong file dữ liệu), dạng chuỗi."""
    return str(as_dict(row).get(KEY, ""))


def merge(stored, new, columns=None):
    """Gộp dòng đã lưu với dòng vừa chạy, sắp theo chỉ số dòng gốc.

    Bản MỚI thắng khi trùng khoá: dòng đã lưu có thể đến từ lần chạy bị ngắt (nhãn đọc dở), mà
    chạy lại chính mẫu đó thì kết quả mới là kết quả đúng. `columns` để dòng đã lưu (dict) được
    đổi về cùng dạng bảng với dòng vừa chạy (list).
    """
    columns = list(columns or COLUMNS)
    index = {}
    for record in stored or []:
        index[key_of(record)] = [record.get(column, "") for column in columns]
    for row in new or []:
        index[key_of(dict(zip(columns, row)))] = list(row)

    def sort_key(row):
        raw = key_of(dict(zip(columns, row)))
        try:
            return (0, int(raw), "")
        except ValueError:
            return (1, 0, raw)

    return sorted(index.values(), key=sort_key)


def _labels(value):
    """Đọc ô nhãn (JSON trong một ô). Hỏng thì trả về dict rỗng, không ném."""
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(value or "{}")
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def to_arrays(rows, aspects):
    """Bảng dự đoán -> (nhãn đúng, nhãn đoán, thông tin đọc) để chấm điểm.

    `nhãn đoán` là None khi ô đó KHÔNG đọc được: bộ chấm phải biết để tính là sai (xem
    docs/04_experiments/metrics.md), nên None được giữ nguyên chứ không đổi thành 0.
    """
    aspects = list(aspects)
    columns = list(COLUMNS)
    golds, preds, infos = [], [], []
    for row in rows:
        row = as_dict(row, columns)
        gold = _labels(row.get("nhãn đúng"))
        guess = _labels(row.get("nhãn đoán"))
        valid = str(row.get("đọc được", "")) == MENTIONED
        golds.append({aspect: int(gold.get(aspect, 0)) for aspect in aspects})
        preds.append({name: int(value) for name, value in guess.items()} if valid else None)
        infos.append({
            "valid": valid,
            "reason": row.get(REASON_COLUMN, ""),
            "has_reasoning": str(row.get("có suy luận", "")) == MENTIONED,
            "had_thinking": str(row.get("có <think>", "")) == MENTIONED,
            "thiếu": [aspect for aspect in aspects if aspect not in guess],
        })
    return golds, preds, infos
