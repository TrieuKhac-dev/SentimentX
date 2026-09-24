# -*- coding: utf-8 -*-
"""Không gian nhãn `binary`: hai nhãn positive/negative.

"Khía cạnh này có được nhắc tới hay không" là một QUYẾT ĐỊNH RIÊNG (nhị phân), đúng như công bố
tham chiếu: bước một nhận ra khía cạnh, bước hai chọn sắc thái. Gộp hai bước làm một sẽ che mất
kiểu lỗi thật (bỏ qua khía cạnh nhưng đoán đúng các khía cạnh còn lại).
"""

from src.labels import base

NAME = "binary"
DESCRIPTION = "Hai nhãn positive/negative; \"có nhắc tới hay không\" là quyết định riêng."
SEPARATE_NOT_MENTIONED = True

# Mã 0 vẫn có mặt vì nó là câu trả lời hợp lệ cho câu hỏi "có nhắc tới không".
CODES = (base.NOT_MENTIONED, base.POSITIVE, base.NEGATIVE)


def check(neutral_policy="drop", not_mentioned="separate"):
    """Kiểm cách khai không gian này."""
    base.check_common(neutral_policy, not_mentioned)


def project(gold, pred, neutral_policy="drop", not_mentioned="separate"):
    """Chiếu sang không gian hai nhãn.

    `neutral_policy`: `drop` bỏ các ô neutral, `as_negative`/`as_positive` gộp chúng vào một cực,
    `keep` giữ neutral như một nhãn nữa (khi đó bài toán giống `full`, chỉ khác cách chấm câu hỏi
    "có nhắc tới hay không").
    """
    check(neutral_policy, not_mentioned)
    gold, pred, dropped = base.apply_neutral_policy(gold, pred, neutral_policy)
    return {
        "label_space": NAME,
        "neutral_policy": neutral_policy,
        "not_mentioned": not_mentioned,
        "separate_not_mentioned": not_mentioned == "separate",
        "codes": list(CODES) + ([base.NEUTRAL] if neutral_policy == "keep" else []),
        "gold": gold,
        "pred": pred,
        "dropped_neutral": dropped,
    }
