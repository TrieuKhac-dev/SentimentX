# -*- coding: utf-8 -*-
"""Phần đọc kết quả của model sinh: tỉ lệ đọc được và phân bố lí do lỗi.

Hàm THUẦN (không model, không I/O) nên kiểm được bằng test mà không cần GPU.

CHỈ SỐ đã chuyển sang registry `src/evaluation/scorers/` (mỗi cách chấm một module, chọn bằng
`evaluation.scores` trong config). Module này giữ lại phần ĐỌC KẾT QUẢ vì nó không phải chỉ số:
nó nói model trả lời được bao nhiêu phần và hỏng ở đâu, để biết một điểm thấp là do model hay do
bộ đọc. Xem docs/04_experiments/metrics.md.
"""


def read_rate(infos, min_rate=None):
    """Tỉ lệ đọc được kết quả + phân bố lí do lỗi (để báo cáo, không để chấm điểm).

    `min_rate` (phần trăm) là **CỬA CHẤT LƯỢNG**: truyền vào thì kết quả có thêm ba khoá `ngưỡng`,
    `valid` và `reason`. Vì sao cần cửa: một lượt chỉ đọc được vài phần trăm vẫn sinh ra `metrics.json`
    "hợp lệ" và rất dễ bị đem đi so - đã gặp thật với `Qwen/Qwen3-0.6B` (3,33% và 1,36%). Cửa **KHÔNG
    xoá dữ liệu**: nó chỉ gắn cờ để người đọc biết con số đó không dùng được (luật 2 của
    `docs/04_experiments/metrics.md`).
    """
    total = len(infos)
    parsed = sum(1 for info in infos if info.get("valid"))
    reasons = {}
    for info in infos:
        if not info.get("valid"):
            key = info.get("reason", "không rõ")
            reasons[key] = reasons.get(key, 0) + 1
    report = {
        "tổng": total,
        "đọc được": parsed,
        "% đọc được": round(100 * parsed / total, 2) if total else 0.0,
        "có khối suy luận": sum(1 for info in infos if info.get("has_reasoning")),
        "có <think>": sum(1 for info in infos if info.get("had_thinking")),
        "thiếu khía cạnh": sum(1 for info in infos if info.get("thiếu")),
        "lí do lỗi": reasons,
    }
    if min_rate is not None:
        rate = report["% đọc được"]
        report["ngưỡng"] = float(min_rate)
        report["valid"] = bool(rate >= float(min_rate))
        report["reason"] = None if report["valid"] else (
            "chỉ đọc được {}% (dưới ngưỡng {}%): điểm của lượt này KHÔNG dùng được".format(
                rate, float(min_rate)))
    return report
