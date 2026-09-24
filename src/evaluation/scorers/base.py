# -*- coding: utf-8 -*-
"""Hợp đồng của một BỘ CHẤM ĐIỂM, và mọi phép đếm dùng chung cho các scorer.

MỘT MODULE CẦN CÓ
    NAME            tên dùng trong config (khoá `evaluation.scores`)
    DESCRIPTION     một dòng mô tả
    run(samples)    -> {"values": {...}, "rows": [...], "tables": {...}}
        values  con số tổng hợp, ghi vào `metrics.json`
        rows    dòng của `metrics.csv`, dạng (aspect, sentiment, metric, value)
        tables  bảng nhiều chiều (ma trận nhầm), ghi vào `metrics.json` khi config bật

QUY ƯỚC BẮT BUỘC - xem docs/04_experiments/metrics.md
    1. Ô KHÔNG ĐỌC ĐƯỢC (nhãn đoán là None) tính là SAI và KHÔNG được bỏ khỏi mẫu số. Bỏ đi
       thì tỉ lệ lỗi định dạng trở thành một cách nâng điểm vô tình.
    2. Lớp dương của câu hỏi "có nhắc tới hay không" là CÓ nhắc tới (mã khác 0): Precision và
       Recall đo việc TÌM RA khía cạnh, không đo việc chọn sắc thái. Hai câu hỏi này phải tách
       rời, gộp lại sẽ che mất kiểu lỗi thật.
    3. Ô bị loại theo `neutral_policy` do `src/labels` quyết định TRƯỚC khi tới đây, và số ô bị
       loại được ghi vào `metrics.json`.
    4. MỌI PHÉP ĐẾM NẰM Ở LỚP `Samples`. Scorer chỉ định dạng lại con số, không đếm lại - nhờ
       vậy hai scorer không thể đưa ra hai con số khác nhau cho cùng một đại lượng.

VÌ SAO LÀ REGISTRY
Thêm một cách chấm mới (ví dụ chỉ số theo công bố khác) là thêm một module và một dòng trong
`SCORERS`; không phải sửa scorer đang có.
"""

from src.labels import NOT_MENTIONED, project as project_labels

# Nhãn cho ô mà model trả lời KHÔNG đọc được. Chỉ dùng khi in bảng (ma trận nhầm), không phải
# một mã nhãn của dataset - nhờ vậy ma trận nhầm vẫn đếm đủ mọi ô.
UNREADABLE = "không đọc được"

TASK_KEYS = ("label_space", "neutral_policy", "not_mentioned")


class ScorerError(Exception):
    """Lỗi dùng bộ chấm điểm: tên lạ, thiếu config bài toán, hoặc dữ liệu không khớp."""


# ---
# Hàm tính dùng chung
# ---


def percent(part, total):
    """Tỉ lệ phần trăm (2 chữ số). Mẫu số 0 thì trả 0.0 thay vì chia cho 0."""
    return round(100.0 * part / total, 2) if total else 0.0


def mean(values):
    """Trung bình của các giá trị CÓ dữ liệu. Rỗng thì trả 0.0.

    Dùng cho điểm macro, và quy ước đi kèm: đơn vị KHÔNG có dữ liệu bị loại khỏi trung bình chứ
    không bị tính là 0. Ví dụ một khía cạnh không được nhắc trong tập con đang chấm: nếu tính nó
    là 0 thì điểm macro tụt mà không có lỗi nào cả, còn nếu loại nó ra thì điểm nói về những gì
    thật sự có để chấm. Số ô của từng đơn vị luôn có trong `metrics.csv` nên việc loại này không
    che mất thông tin.
    """
    values = list(values)
    return round(sum(values) / len(values), 3) if values else 0.0



def prf(tp, fp, fn):
    """Precision, Recall, F1. Không có gì để tìm (mẫu số 0) thì trả 0.0."""
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return round(precision, 3), round(recall, 3), round(f1, 3)


def row(aspect, sentiment, metric, value):
    """Một dòng của `metrics.csv` (bảng dài: aspect, sentiment, metric, value)."""
    return {"aspect": aspect, "sentiment": sentiment, "metric": metric, "value": value}


def binary_counts(gold, pred):
    """TP/FP/FN/TN cho câu hỏi "khía cạnh này có được nhắc tới hay không".

    Lớp DƯƠNG là "có nhắc tới" (mã khác 0), nên:
        TP  nhãn đúng có nhắc, model cũng nói có nhắc   -> tìm đúng khía cạnh
        FP  nhãn đúng KHÔNG nhắc, model nói có nhắc     -> model "thấy" khía cạnh không có
        FN  nhãn đúng có nhắc, model nói không nhắc     -> model bỏ sót khía cạnh
        TN  cả hai đều không nhắc

    Ô không đọc được coi như model không nêu khía cạnh nào: mất Recall ở ô đáng ra có nhắc,
    nhưng KHÔNG sinh ra dương tính giả. (Bản cũ từng hoán vị FP/FN; F1 không đổi vì đối xứng
    nên bảng vẫn "trông hợp lí" trong khi Precision/Recall đổi chỗ cho nhau.)
    """
    tp = fp = fn = tn = 0
    for truth, guess in zip(gold, pred):
        found_truth = truth != NOT_MENTIONED
        found_guess = guess is not None and guess != NOT_MENTIONED
        if found_truth and found_guess:
            tp += 1
        elif not found_truth and found_guess:
            fp += 1
        elif found_truth and not found_guess:
            fn += 1
        else:
            tn += 1
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


def kept_indexes(raw, kept):
    """Vị trí (theo review gốc) của các ô CÒN LẠI sau khi chiếu nhãn.

    Suy từ hai dãy: dãy nhãn đúng TRƯỚC khi chiếu và dãy SAU khi chiếu. Phép chiếu của
    `src/labels` chỉ BỎ ô hoặc ĐỔI MÃ neutral, không đổi thứ tự, nên có hai trường hợp:
        - dài bằng nhau  -> không bỏ ô nào (as_negative / as_positive / keep / full)
        - ngắn hơn       -> dãy sau là DÃY CON của dãy trước, các ô bị bỏ là ô neutral

    Nhờ vậy lấy lại được ô nào đã bị bỏ mà KHÔNG phải chép lại luật `neutral_policy` ở đây -
    chép lại là có hai nơi, sớm muộn lệch nhau.
    """
    if len(raw) == len(kept):
        return list(range(len(raw)))
    indexes, cursor = [], 0
    for index, value in enumerate(raw):
        if cursor < len(kept) and kept[cursor] == value:
            indexes.append(index)
            cursor += 1
    if len(indexes) != len(kept):
        raise ScorerError(
            "Không khớp được {} ô sau khi chiếu với {} ô trước khi chiếu: phép chiếu đã ĐỔI giá "
            "trị chứ không chỉ bỏ ô. Kiểm lại `src/labels`.".format(len(kept), len(raw)))
    return indexes


# ---
# Dữ liệu đã chiếu để chấm điểm
# ---


class Samples:
    """Nhãn đã chiếu theo bài toán của thí nghiệm, kèm mọi phép đếm.

    gold_rows   list[dict {khía cạnh: mã đúng}]
    pred_rows   list[dict {khía cạnh: mã đoán} | None]  (None = KHÔNG đọc được kết quả)

    Ô `None` đi qua phép chiếu nguyên vẹn: `src/labels` chỉ đổi mã neutral và lọc theo nhãn
    ĐÚNG, nên một ô không đọc được vẫn là "không đọc được" sau khi chiếu.
    """

    def __init__(self, aspects, cells, raw_gold=None, meta=None, labels=None,
                 sample_ids=None, n_reviews=0, dropped=None):
        self.aspects = list(aspects)
        self.cells = {name: (list(gold), list(pred)) for name, (gold, pred) in cells.items()}
        self.raw_gold = {name: list(codes) for name, codes in (raw_gold or {}).items()}
        self.meta = dict(meta or {})
        self.labels = dict(labels or {})
        self.sample_ids = list(sample_ids or [])
        self.n_reviews = int(n_reviews)
        self.dropped = dict(dropped or {})
        self._cache = {}

    # --- dựng ---

    @classmethod
    def build(cls, aspects, gold_rows, pred_rows, task=None, labels=None, meta=None,
              sample_ids=None):
        """Chiếu nhãn theo config bài toán (`configs/experiments/task.yaml`) rồi đóng gói.

        Dùng ĐÚNG `src.labels.project` như phần huấn luyện, nên chấm điểm và huấn luyện không
        thể hiểu nhãn theo hai cách khác nhau.
        """
        task = dict(task or {})
        missing = [key for key in TASK_KEYS if not task.get(key)]
        if missing:
            raise ScorerError(
                "Thiếu {} trong config bài toán (configs/experiments/task.yaml).".format(
                    ", ".join(missing)))
        if len(gold_rows) != len(pred_rows):
            raise ScorerError("Số nhãn đúng ({}) khác số nhãn đoán ({}).".format(
                len(gold_rows), len(pred_rows)))

        aspects = list(aspects)
        cells, raw_gold, dropped, projected = {}, {}, {}, None
        for aspect in aspects:
            gold = [row.get(aspect, NOT_MENTIONED) for row in gold_rows]
            pred = [None if prediction is None else prediction.get(aspect)
                    for prediction in pred_rows]
            projected = project_labels(gold, pred, task["label_space"],
                                       task["neutral_policy"], task["not_mentioned"])
            raw_gold[aspect] = gold
            cells[aspect] = (projected["gold"], projected["pred"])
            dropped[aspect] = int(projected["dropped_neutral"])

        info = dict(meta or {})
        info.update({key: projected[key] for key in TASK_KEYS})
        info["separate_not_mentioned"] = bool(projected["separate_not_mentioned"])
        info["codes"] = list(projected["codes"])
        info["dropped_neutral"] = sum(dropped.values())
        info["dropped_neutral_by_aspect"] = dict(dropped)
        return cls(aspects, cells, raw_gold=raw_gold, meta=info, labels=labels,
                   sample_ids=sample_ids, n_reviews=len(gold_rows), dropped=dropped)

    # --- tiện ích ---

    def _memo(self, key, build):
        if key not in self._cache:
            self._cache[key] = build()
        return self._cache[key]

    def code_for(self, code):
        """Tên nhãn để in bảng; không có bảng tên thì dùng chính mã."""
        if code in self.labels:
            return self.labels[code]
        return self.labels.get(str(code), str(code))

    def sentiments(self):
        """Các mã được chấm như một SẮC THÁI riêng.

        Bỏ mã "không nhắc tới" khi nó là quyết định nhị phân riêng (không gian `binary`), vì khi
        đó nó đã có chỉ số riêng ở `aspect_detection`; giữ lại khi nó là một LỚP (`full`).
        """
        codes = list(self.meta.get("codes") or [])
        if self.meta.get("separate_not_mentioned"):
            codes = [code for code in codes if code != NOT_MENTIONED]
        return codes

    def kept(self, aspect):
        """Vị trí theo review gốc của các ô còn lại của một khía cạnh."""
        return self._memo("kept:" + aspect,
                          lambda: kept_indexes(self.raw_gold.get(aspect, []),
                                               self.cells[aspect][0]))

    # --- các phép đếm ---

    def accuracy(self):
        """Độ chính xác: theo từng khía cạnh, và macro/micro trên ô."""
        def compute():
            by_aspect, correct_total, cell_total = {}, 0, 0
            for aspect in self.aspects:
                gold, pred = self.cells[aspect]
                correct = sum(1 for truth, guess in zip(gold, pred) if guess == truth)
                by_aspect[aspect] = {"correct": correct, "cells": len(gold),
                                     "accuracy": percent(correct, len(gold))}
                correct_total += correct
                cell_total += len(gold)
            macro = round(mean([item["accuracy"] for item in by_aspect.values()
                                if item["cells"]]), 2)
            return {"by_aspect": by_aspect, "correct": correct_total, "cells": cell_total,
                    "macro": macro, "micro": percent(correct_total, cell_total)}
        return self._memo("accuracy", compute)

    def when_mentioned(self):
        """Độ chính xác CHỈ trên các ô mà nhãn đúng có nhắc tới.

        Đây là câu hỏi "khi đã nhận ra khía cạnh, model chọn sắc thái có đúng không", tách khỏi
        câu hỏi nhận ra khía cạnh ở `detection()`.
        """
        def compute():
            by_aspect, correct_total, cell_total = {}, 0, 0
            for aspect in self.aspects:
                gold, pred = self.cells[aspect]
                pairs = [(truth, guess) for truth, guess in zip(gold, pred)
                         if truth != NOT_MENTIONED]
                correct = sum(1 for truth, guess in pairs if guess == truth)
                by_aspect[aspect] = {"correct": correct, "cells": len(pairs),
                                     "accuracy": percent(correct, len(pairs))}
                correct_total += correct
                cell_total += len(pairs)
            macro = round(mean([item["accuracy"] for item in by_aspect.values()
                                if item["cells"]]), 2)
            return {"by_aspect": by_aspect, "correct": correct_total, "cells": cell_total,
                    "macro": macro, "micro": percent(correct_total, cell_total)}
        return self._memo("when_mentioned", compute)

    def detection(self):
        """Bài toán nhị phân "có nhắc tới hay không": theo khía cạnh, macro và micro."""
        def compute():
            by_aspect, totals = {}, {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
            for aspect in self.aspects:
                gold, pred = self.cells[aspect]
                item = binary_counts(gold, pred)
                item["cells"] = item["tp"] + item["fp"] + item["fn"] + item["tn"]
                item["accuracy"] = percent(item["tp"] + item["tn"], item["cells"])
                item["precision"], item["recall"], item["f1"] = prf(
                    item["tp"], item["fp"], item["fn"])
                by_aspect[aspect] = item
                for key in totals:
                    totals[key] += item[key]

            precision, recall, f1 = prf(totals["tp"], totals["fp"], totals["fn"])
            micro = dict(totals)
            micro["cells"] = totals["tp"] + totals["fp"] + totals["fn"] + totals["tn"]
            micro.update({"precision": precision, "recall": recall, "f1": f1,
                          "accuracy": percent(totals["tp"] + totals["tn"], micro["cells"])})
            macro = {key: mean([item[key] for item in by_aspect.values() if item["cells"]])
                     for key in ("precision", "recall", "f1", "accuracy")}
            support = {
                "mentioned": sum(item["tp"] + item["fn"] for item in by_aspect.values()),
                "not_mentioned": sum(item["fp"] + item["tn"] for item in by_aspect.values()),
            }
            return {"by_aspect": by_aspect, "macro": macro, "micro": micro, "support": support}
        return self._memo("detection", compute)

    def per_sentiment(self):
        """Precision/recall/F1 cho từng cặp (khía cạnh, sắc thái), kiểu một-chọi-phần-còn-lại.

        Ô không đọc được tính là "không thuộc lớp này", tức là SAI - đúng quy ước chung.
        """
        def compute():
            codes = self.sentiments()
            by_aspect = {}
            totals = {code: {"tp": 0, "fp": 0, "fn": 0, "support": 0} for code in codes}
            for aspect in self.aspects:
                gold, pred = self.cells[aspect]
                per_code = {}
                for code in codes:
                    tp = fp = fn = 0
                    for truth, guess in zip(gold, pred):
                        is_truth, is_guess = truth == code, guess == code
                        if is_truth and is_guess:
                            tp += 1
                        elif not is_truth and is_guess:
                            fp += 1
                        elif is_truth and not is_guess:
                            fn += 1
                    precision, recall, f1 = prf(tp, fp, fn)
                    support = sum(1 for truth in gold if truth == code)
                    per_code[code] = {"tp": tp, "fp": fp, "fn": fn, "support": support,
                                      "precision": precision, "recall": recall, "f1": f1}
                    for key in totals[code]:
                        totals[code][key] += per_code[code][key]
                by_aspect[aspect] = per_code

            pairs = [item for aspect in self.aspects for item in by_aspect[aspect].values()
                     if item["support"] or (item["tp"] + item["fp"] + item["fn"])]
            macro = {key: mean([item[key] for item in pairs])
                     for key in ("precision", "recall", "f1")}
            precision, recall, f1 = prf(
                sum(item["tp"] for item in totals.values()),
                sum(item["fp"] for item in totals.values()),
                sum(item["fn"] for item in totals.values()))
            micro = {"precision": precision, "recall": recall, "f1": f1,
                     "support": sum(item["support"] for item in totals.values())}
            return {"by_aspect": by_aspect, "macro": macro, "micro": micro,
                    "totals": totals}
        return self._memo("per_sentiment", compute)

    def exact(self):
        """Khớp hoàn toàn: tỉ lệ review đoán đúng CẢ bộ khía cạnh được chấm.

        Ô bị loại theo `neutral_policy` không được tính, vì nó không thuộc tập đánh giá. Review
        mà mọi ô đều bị loại thì tính là đúng - không còn gì để đoán sai.
        """
        def compute():
            positions = {aspect: {index: position
                                  for position, index in enumerate(self.kept(aspect))}
                         for aspect in self.aspects}
            correct = 0
            for index in range(self.n_reviews):
                ok = True
                for aspect in self.aspects:
                    position = positions[aspect].get(index)
                    if position is None:
                        continue
                    gold, pred = self.cells[aspect]
                    if pred[position] != gold[position]:
                        ok = False
                        break
                correct += 1 if ok else 0
            return {"reviews": self.n_reviews, "correct": correct,
                    "percent": percent(correct, self.n_reviews)}
        return self._memo("exact", compute)

    def confusion(self, aspect):
        """Bảng đếm nhãn đúng (dòng) so với nhãn đoán (cột) của một khía cạnh.

        Ô không đọc được gom vào một cột riêng, nên bảng đếm ĐỦ mọi ô - nhìn vào bảng là biết
        phần nào của sai số đến từ việc model trả lời hỏng định dạng.
        """
        gold, pred = self.cells[aspect]
        table = {}
        for truth, guess in zip(gold, pred):
            truth_name = self.code_for(truth)
            guess_name = UNREADABLE if guess is None else self.code_for(guess)
            counts = table.setdefault(truth_name, {})
            counts[guess_name] = counts.get(guess_name, 0) + 1
        return table

    def mispredictions(self):
        """Các ô đoán sai (để ghi `mispredictions.csv`), kèm chỉ số review trong split."""
        found = []
        for aspect in self.aspects:
            gold, pred = self.cells[aspect]
            indexes = self.kept(aspect)
            for position, (truth, guess) in enumerate(zip(gold, pred)):
                if guess == truth:
                    continue
                index = indexes[position]
                found.append({
                    "review": self.sample_ids[index]
                    if index < len(self.sample_ids) else str(index),
                    "aspect": aspect,
                    "gold": self.code_for(truth),
                    "pred": UNREADABLE if guess is None else self.code_for(guess),
                })
        return found



