# -*- coding: utf-8 -*-
"""Hợp đồng của một KHÔNG GIAN NHÃN.

Không gian nhãn là cách một thí nghiệm nhìn bài toán:

    full    giữ đủ bốn trạng thái, kể cả neutral -> bài toán phân loại nhiều lớp
    binary  chỉ positive/negative, và "có nhắc tới hay không" là một quyết định nhị phân riêng

MỘT MODULE CẦN CÓ
    NAME                    tên dùng trong config (khoá `label_space`)
    DESCRIPTION             một dòng mô tả
    CODES                   các mã nhãn hợp lệ
    SEPARATE_NOT_MENTIONED  True nếu mã 0 được chấm như một quyết định riêng
    check()                 báo lỗi rõ nếu cách khai không dùng được
    project()               chiếu (nhãn đúng, nhãn đoán) sang dạng mà metric dùng

VÌ SAO PHẢI LÀ REGISTRY
Thêm một không gian nhãn mới (ví dụ gộp neutral vào negative) là thêm một module và một dòng
đăng ký trong `src/labels/__init__.py`; metric không phải sửa.
"""

# Bốn mã nhãn của dataset (xem src/config.py::LABEL_TO_ID).
NOT_MENTIONED = 0
POSITIVE = 1
NEGATIVE = 2
NEUTRAL = 3

NEUTRAL_POLICIES = ("drop", "as_negative", "as_positive", "keep")
NOT_MENTIONED_MODES = ("separate", "as_class")


class LabelError(Exception):
    """Lỗi khai báo không gian nhãn: tên lạ, hoặc tổ hợp tham số không dùng được."""


def check_common(neutral_policy, not_mentioned):
    """Kiểm hai tham số chung của mọi không gian nhãn."""
    if neutral_policy not in NEUTRAL_POLICIES:
        raise LabelError(
            "neutral_policy phải là một trong {}, đang là {!r}.".format(
                ", ".join(NEUTRAL_POLICIES), neutral_policy))
    if not_mentioned not in NOT_MENTIONED_MODES:
        raise LabelError(
            "not_mentioned phải là một trong {}, đang là {!r}.".format(
                ", ".join(NOT_MENTIONED_MODES), not_mentioned))


def keep_when(gold, pred, test):
    """Lọc các ô mà nhãn ĐÚNG thoả `test`. Trả về (gold, pred, số ô bị loại).

    Lọc theo nhãn ĐÚNG, không theo nhãn đoán: lọc theo nhãn đoán thì mẫu số phụ thuộc vào chất
    lượng model - đoán sai nhiều làm mẫu số nhỏ đi và điểm trông đẹp hơn. Đó là lỗi im lặng.
    """
    kept_gold, kept_pred, dropped = [], [], 0
    for gold_code, pred_code in zip(gold, pred):
        if test(gold_code):
            kept_gold.append(gold_code)
            kept_pred.append(pred_code)
        else:
            dropped += 1
    return kept_gold, kept_pred, dropped


def apply_neutral_policy(gold, pred, policy):
    """Xử lý các ô có nhãn đúng là `neutral` theo `neutral_policy`.

    Trả về (gold, pred, số ô bị loại). Số ô bị loại được ghi vào `metrics.json`, vì nó là mức độ
    phải đưa ra khỏi tập đánh giá để so được với công bố tham chiếu (công bố cũng loại neutral).
    """
    check_common(policy, "separate")
    if policy == "keep":
        return list(gold), list(pred), 0
    if policy in ("as_negative", "as_positive"):
        target = NEGATIVE if policy == "as_negative" else POSITIVE
        return ([target if code == NEUTRAL else code for code in gold],
                [target if code == NEUTRAL else code for code in pred], 0)
    return keep_when(gold, pred, lambda code: code != NEUTRAL)


def split_mentioned(gold, pred):
    """Tách thành hai câu hỏi: nhận ra khía cạnh, và chọn sắc thái cho ô đã nhận ra.

    Trả về (detection, polarity) trong đó mỗi phần là (gold, pred):
        detection  nhị phân: 0 = không nhắc tới, 1 = có nhắc tới
        polarity   chỉ các ô có nhắc tới, nhãn giữ nguyên
    """
    detection_gold = [NOT_MENTIONED if code == NOT_MENTIONED else 1 for code in gold]
    detection_pred = [NOT_MENTIONED if code == NOT_MENTIONED else 1 for code in pred]
    polarity_gold, polarity_pred, _dropped = keep_when(
        gold, pred, lambda code: code != NOT_MENTIONED)
    return (detection_gold, detection_pred), (polarity_gold, polarity_pred)
