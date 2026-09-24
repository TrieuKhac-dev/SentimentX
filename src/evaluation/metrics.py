# -*- coding: utf-8 -*-
"""Chỉ số đánh giá cho bài toán ABSA (đánh giá model) - hàm THUẦN, không cần torch.

VÌ SAO CÁC CHỈ SỐ NÀY
---
Bài toán có 7 khía cạnh, mỗi khía cạnh một nhãn 0/1/2/3 (0 = KHÔNG nhắc tới). Với model
sinh, có hai câu hỏi khác nhau và phải tách ra:

    1. Model có NHẬN RA khía cạnh nào được nhắc tới hay không? (nhị phân 0 vs khác 0)
       -> đo bằng precision / recall / F1 của lớp "có nhắc tới".
    2. Khi đã nhận ra, model có chọn ĐÚNG mã cảm xúc không? (4 lớp)
       -> đo bằng độ chính xác trên các mẫu CÓ nhắc tới.

Gộp hai câu hỏi làm một (chỉ báo accuracy) sẽ che mất kiểu lỗi thật của model 4B: nó
thường "thấy" khía cạnh nhưng chọn sai sắc thái, hoặc ngược lại - bỏ qua khía cạnh nhưng
đoán đúng các khía cạnh còn lại.

Nhãn KHÔNG đọc được (JSON lỗi) bị tính là SAI, không được bỏ khỏi mẫu số: bỏ đi thì tỉ lệ
lỗi định dạng trở thành một cách "nâng điểm" vô tình.

Chỉ số tổng hợp
---
    acc macro     : trung bình độ chính xác của 7 khía cạnh (mỗi khía cạnh một phiếu)
    acc micro     : đúng trên tổng số ô (7 ô/review)
    khớp hoàn toàn: tỉ lệ review đoán đúng CẢ 7 khía cạnh - chỉ số khắt khe nhất
    F1 nhắc (macro/micro): cho bài toán nhị phân "có nhắc tới khía cạnh này hay không"
"""


def _binary_counts(gold, pred, positive=0):
    """Đếm TP/FP/FN/TN cho phép phân loại nhị phân "có nhắc tới" vs "không nhắc tới".

    Quy ước: `positive=0` là mã "KHÔNG nhắc tới", nên lớp DƯƠNG mà ta đo là **có nhắc tới**
    (mã khác 0). Từ đó:

        TP: nhãn đúng != 0 và model đoán != 0     -> tìm đúng khía cạnh có được nhắc
        FP: nhãn đúng == 0 nhưng model đoán != 0  -> model "thấy" khía cạnh không có
        FN: nhãn đúng != 0 nhưng model đoán == 0  -> model bỏ sót khía cạnh có
        TN: cả hai đều == 0

    ĐÃ TỪNG SAI Ở ĐÂY (lỗi im lặng, phát hiện khi số liệu không khớp): hai nhánh FP và FN bị
    hoán vị. F1 không đổi (đối xứng) nên bảng kết quả vẫn "trông hợp lí", nhưng cột
    Precision và Recall bị ĐỔI CHỖ cho nhau. Vì vậy `tests/test_metrics.py` giờ khoá đúng
    quy ước này bằng hai ca BẤT ĐỐI XỨNG (chỉ dương tính giả, và chỉ âm tính giả).

    `pred` là None nghĩa là ô đó KHÔNG đọc được -> coi như model không nêu khía cạnh nào.
    """
    tp = fp = fn = tn = 0
    for truth, guess in zip(gold, pred):
        if guess is None:
            if truth == positive:
                tn += 1          # đoán sai, nhưng "không nhắc tới" là mặc định của lớp âm
            else:
                fn += 1
            continue
        if truth == positive and guess == positive:
            tn += 1
        elif truth != positive and guess != positive:
            tp += 1
        elif truth == positive:
            fp += 1              # nhãn đúng: không nhắc; model: có nhắc
        else:
            fn += 1              # nhãn đúng: có nhắc; model: không nhắc
    return tp, fp, fn, tn


def _prf(tp, fp, fn):
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return precision, recall, f1


def score(gold_rows, pred_rows, aspects):
    """Chấm điểm. Trả về (bảng theo khía cạnh, chỉ số tổng hợp).

    gold_rows: list[dict {khía cạnh: mã đúng}]  (mã 0 = không nhắc tới)
    pred_rows: list[dict {khía cạnh: mã}|None]  (None = không đọc được kết quả)
    """
    aspects = list(aspects)
    n = len(gold_rows)
    rows = []
    total_cells = total_correct = 0
    exact = 0
    micro = [0, 0, 0]

    for aspect in aspects:
        gold = [row.get(aspect, 0) for row in gold_rows]
        pred = [
            None if prediction is None else prediction.get(aspect)
            for prediction in pred_rows
        ]
        correct = sum(1 for truth, guess in zip(gold, pred) if guess == truth)
        mentioned = [(truth, guess) for truth, guess in zip(gold, pred) if truth != 0]
        mentioned_correct = sum(1 for truth, guess in mentioned if guess == truth)
        tp, fp, fn, _tn = _binary_counts(gold, pred, positive=0)
        precision, recall, f1 = _prf(tp, fp, fn)

        total_cells += n
        total_correct += correct
        micro[0] += tp
        micro[1] += fp
        micro[2] += fn

        rows.append({
            "khía cạnh": aspect,
            "số mẫu": n,
            "đúng": correct,
            "acc": round(100 * correct / n, 2) if n else 0.0,
            "có nhắc tới": len(mentioned),
            "acc khi có nhắc": round(
                100 * mentioned_correct / len(mentioned), 2) if mentioned else None,
            "P nhắc": round(precision, 3),
            "R nhắc": round(recall, 3),
            "F1 nhắc": round(f1, 3),
        })

    for truth, prediction in zip(gold_rows, pred_rows):
        if prediction is None:
            continue
        if all(prediction.get(aspect) == truth.get(aspect, 0) for aspect in aspects):
            exact += 1

    micro_precision, micro_recall, micro_f1 = _prf(*micro)
    summary = {
        "số review": n,
        "acc macro": round(
            sum(row["acc"] for row in rows) / len(rows), 2) if rows else 0.0,
        "acc micro": round(100 * total_correct / total_cells, 2) if total_cells else 0.0,
        "khớp hoàn toàn": round(100 * exact / n, 2) if n else 0.0,
        "P nhắc micro": round(micro_precision, 3),
        "R nhắc micro": round(micro_recall, 3),
        "F1 nhắc micro": round(micro_f1, 3),
        "F1 nhắc macro": round(
            sum(row["F1 nhắc"] for row in rows) / len(rows), 3) if rows else 0.0,
    }
    return rows, summary


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
