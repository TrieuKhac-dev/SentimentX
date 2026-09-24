# -*- coding: utf-8 -*-
"""Không gian nhãn `full`: giữ đủ bốn trạng thái.

Dùng khi câu hỏi nghiên cứu cần cả nhãn neutral, hoặc khi muốn báo cáo bài toán ABSA đa lớp đầy
đủ (công bố tham chiếu loại neutral khỏi phần đánh giá chính, nên kết quả `full` KHÔNG so trực
tiếp được với công bố - xem docs/04_experiments/reference_publication.md).
"""

from src.labels import base

NAME = "full"
DESCRIPTION = "Bốn trạng thái: không nhắc tới, positive, negative, neutral."
SEPARATE_NOT_MENTIONED = False

CODES = (base.NOT_MENTIONED, base.POSITIVE, base.NEGATIVE, base.NEUTRAL)


def check(neutral_policy="keep", not_mentioned="as_class"):
    """Kiểm cách khai không gian này.

    Ở không gian `full`, neutral là một LỚP và "không nhắc tới" cũng là một lớp, nên hai tham số
    kia chỉ có một giá trị đúng. Khai khác là đang nhầm với không gian `binary`.
    """
    base.check_common(neutral_policy, not_mentioned)
    if neutral_policy != "keep":
        raise base.LabelError(
            "label_space 'full' giữ neutral như một LỚP, nên neutral_policy phải là 'keep'; đang "
            "là {!r}. Muốn loại neutral thì dùng label_space 'binary'.".format(neutral_policy))
    if not_mentioned != "as_class":
        raise base.LabelError(
            "label_space 'full' coi \"không nhắc tới\" là một LỚP, nên not_mentioned phải là "
            "'as_class'; đang là {!r}. Muốn chấm nó như quyết định riêng thì dùng 'binary'.".format(
                not_mentioned))


def project(gold, pred, neutral_policy="keep", not_mentioned="as_class"):
    """Không gian `full` không chiếu gì: giữ nguyên nhãn, không loại ô nào."""
    check(neutral_policy, not_mentioned)
    return {
        "label_space": NAME,
        "neutral_policy": neutral_policy,
        "not_mentioned": not_mentioned,
        "separate_not_mentioned": False,
        "codes": list(CODES),
        "gold": list(gold),
        "pred": list(pred),
        "dropped_neutral": 0,
    }
