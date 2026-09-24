# -*- coding: utf-8 -*-
"""Phần đọc kết quả của model sinh: tỉ lệ đọc được và phân bố lí do lỗi.

Hàm THUẦN (không model, không I/O) nên kiểm được bằng test mà không cần GPU.

CHỈ SỐ đã chuyển sang registry `src/evaluation/scorers/` (mỗi cách chấm một module, chọn bằng
`evaluation.scores` trong config). Module này giữ lại phần ĐỌC KẾT QUẢ vì nó không phải chỉ số:
nó nói model trả lời được bao nhiêu phần và hỏng ở đâu, để biết một điểm thấp là do model hay do
bộ đọc. Xem docs/04_experiments/metrics.md.
"""


def read_rate(infos):
    """Tỉ lệ đọc được kết quả + phân bố lí do lỗi (để báo cáo, không để chấm điểm)."""
    total = len(infos)
    parsed = sum(1 for info in infos if info.get("valid"))
    reasons = {}
    for info in infos:
        if not info.get("valid"):
            key = info.get("reason", "không rõ")
            reasons[key] = reasons.get(key, 0) + 1
    return {
        "tổng": total,
        "đọc được": parsed,
        "% đọc được": round(100 * parsed / total, 2) if total else 0.0,
        "có khối suy luận": sum(1 for info in infos if info.get("has_reasoning")),
        "có <think>": sum(1 for info in infos if info.get("had_thinking")),
        "thiếu khía cạnh": sum(1 for info in infos if info.get("thiếu")),
        "lí do lỗi": reasons,
    }
