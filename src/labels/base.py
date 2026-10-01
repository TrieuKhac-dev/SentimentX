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

# Bốn mã nhãn của dataset (xem src/core/config.py::LABEL_TO_ID).
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


# ---
# Bộ lọc của CÔNG BỐ - biến thể đo `paper`
# ---

# Hai nhãn mà công bố giữ lại khi đo (bài loại neutral và OTHERS khỏi phần đánh giá chính). Ghi
# bằng TÊN nhãn chứ không bằng mã số: bảng nhãn của dataset có thể đánh số khác, còn tên thì không.
PAPER_LABELS = ("positive", "negative")


def named_codes(id_to_label, names):
    """Mã nhãn ứng với các TÊN nhãn, tra trong bảng tên của dataset (`label_map.json`).

    Bảng tên đi kèm mỗi phiên bản dữ liệu nên tra qua nó là cách duy nhất còn đúng khi dataset đổi
    cách đánh số. Thiếu tên là LỖI chứ không bỏ qua: thiếu tên thì bộ lọc không lọc được gì và
    người đọc số không có cách nào biết mình đang đọc số của một đường đo khác.
    """
    wanted = {str(name).strip().lower() for name in names}
    found, have = set(), set()
    for code, label in (id_to_label or {}).items():
        key = str(label).strip().lower()
        if key not in wanted:
            continue
        try:
            found.add(int(code))
        except (TypeError, ValueError):
            continue
        have.add(key)
    missing = sorted(wanted - have)
    if missing:
        raise LabelError(
            "Bảng nhãn của dataset không có tên {} (đang có: {}). Bộ lọc hai chiều viết theo TÊN "
            "nhãn nên thiếu tên là không đo được.".format(
                ", ".join(missing),
                ", ".join(sorted(str(value) for value in (id_to_label or {}).values()))))
    return found


def two_sided_positions(gold, pred, codes):
    """VỊ TRÍ các ô mà CẢ nhãn đúng VÀ nhãn đoán thuộc `codes` - cách lọc HAI CHIỀU của công bố.

    Trả về `(vị trí, bị loại, không đọc được)`:
        vị trí          chỉ số (0-based) các ô được giữ, theo ĐÚNG thứ tự của `gold`
        bị loại         nhãn đúng hoặc nhãn đoán nằm ngoài `codes` (kể cả "không nhắc tới")
        không đọc được  ô mà model trả lời không đọc được (`pred` là None)

    Hai con số đếm RIÊNG vì đây là cách lọc duy nhất bỏ ô theo NHÃN ĐOÁN: không đếm thì tỉ lệ lỗi
    định dạng trở thành một cách nâng điểm im lặng.

    VÌ SAO TRẢ VỊ TRÍ chứ không trả giá trị: bộ chấm điểm cần biết ô được giữ là ô của REVIEW nào.
    Suy lại từ giá trị của hai dãy là ĐOÁN SAI: ô bị loại vì NHÃN ĐOÁN vẫn có thể trùng nhãn đúng
    với ô được giữ (ví dụ nhãn đúng `1` mà model trả lời `0` bị loại, trong khi một ô khác cũng
    nhãn đúng `1` mà model trả lời đúng được giữ) - khi đó không có cách ghép dãy con nào là đúng.
    Đi kèm vị trí nên phép ghép này đúng theo CẤU TRÚC, không phải theo suy đoán.
    """
    wanted = set(codes)
    positions, dropped, unreadable = [], 0, 0
    for index, (gold_code, pred_code) in enumerate(zip(gold, pred)):
        if pred_code is None:
            unreadable += 1
            continue
        if gold_code not in wanted or pred_code not in wanted:
            dropped += 1
            continue
        positions.append(index)
    return positions, dropped, unreadable


def keep_two_sided(gold, pred, codes):
    """Bản theo GIÁ TRỊ của `two_sided_positions`: `(gold, pred, bị loại, không đọc được)`.

    LUẬT LỌC nằm ở `two_sided_positions`; hàm này chỉ định dạng lại kết quả theo giá trị, để không
    tồn tại hai bản luật lọc sớm muộn lệch nhau.
    """
    positions, dropped, unreadable = two_sided_positions(gold, pred, codes)
    return ([gold[index] for index in positions],
            [pred[index] for index in positions], dropped, unreadable)
