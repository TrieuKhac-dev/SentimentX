# -*- coding: utf-8 -*-
"""KẾT HỢP các lượt chạy: dò ngưỡng theo khía cạnh, ensemble encoder, luật lai, biểu quyết.

VÌ SAO CÓ MODULE NÀY
Ba việc này không chạy model: chúng đọc `predictions.csv` (nhãn cứng) và `probabilities.csv` (xác suất
từng ô - chỉ đường encoder có) rồi CHẤM LẠI bằng ĐÚNG engine của dự án (`src/evaluation/scorers/`).
Nhờ vậy số của bước kết hợp so được với số của từng lượt, và không có "định nghĩa metric thứ hai".

HAI LUẬT BẮT BUỘC (đã ghi ở `present_plan.md` mục 8.4/8.5 và `docs/04_experiments/metrics.md`)
1. **Luật chốt trên `val`, áp lên `test`** - không được xem `test` rồi mới chọn.
2. **`price` không có ngưỡng**: `val` có 0 ô `price` âm (train 15, test 6) nên không có gì để dò; hàm
   nào cũng trả `None` kèm lí do cho khía cạnh đó, và các ô `price` giữ nguyên quyết định của model gốc.

ĐƯỜNG NGƯỠNG CÓ HAI BƯỚC, HAI LỆNH
`fit_thresholds` DÒ trên `val` rồi ghi tệp luật ĐÓNG BĂNG; `applied_report` ÁP tệp luật đó lên một lượt
khác (thường là `test`) rồi chấm lại. Số báo cáo là số của bước thứ hai - luật 1 ở trên nói vì sao không
được gộp hai bước làm một.

Xem `docs/04_experiments/09_fusion.md`.
"""

import csv
import json
from pathlib import Path

from src.core import paths, utils
from src.evaluation import records, rescore, scorers

# Ngưỡng dò mặc định: từ chối đoán lớp âm (0,95) tới sẵn sàng đoán (0,05). Bước 0,05 để bảng dò đọc
# được bằng mắt; đổi lưới là đổi tham số, không phải sửa code.
GRID = [round(0.05 * step, 2) for step in range(1, 20)]

# Nếu áp ngưỡng làm MẤT quá 5% số ô thì dừng: "kiêng trả lời" để lấy điểm không phải là tiến bộ.
MAX_CELLS_DROP = 0.05


class FusionError(Exception):
    """Không kết hợp được: thiếu tệp, thiếu xác suất, hoặc tham số không hợp lệ."""


def _read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle) or {}
    except (OSError, ValueError):
        return {}


def read_probabilities(out_dir):
    """Đọc `probabilities.csv` -> `{(chỉ số, khía cạnh): {mã: xác suất}}`, và danh sách mã.

    Trả `(bảng, mã)`, hoặc `(None, None)` khi lượt chạy KHÔNG có tệp này (đường prompt không có xác
    suất) - chỗ gọi tự báo lỗi kèm lí do thay vì đoán.
    """
    path = Path(out_dir) / paths.pattern("probabilities")
    if not path.is_file():
        return None, None
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise FusionError("{} rỗng.".format(utils.rel(path)))
    codes = []
    for name in rows[0]:
        if name.startswith("p(mã ") and name.endswith(")"):
            codes.append(int(name[len("p(mã "):-1]))
    if not codes:
        raise FusionError(
            "{} không có cột 'p(mã <mã>)' nào: tệp xác suất phải do đường encoder ghi.".format(
                utils.rel(path)))
    table = {}
    for row in rows:
        key = (str(row.get("chỉ số", "")), str(row.get("khía cạnh", "")))
        table[key] = {code: float(row.get("p(mã {})".format(code)) or 0.0) for code in codes}
    return table, codes

def load_run(out_dir, need_probabilities=False):
    """Nạp một lượt chạy để kết hợp: nhãn, xác suất, bài toán, bảng tên nhãn.

    Dùng lại `rescore.settings/labels_of/task_of` vì đó là chỗ đã biết đọc `run_meta.json`, bảng tên
    nhãn và bài toán - viết lại ở đây là hai chỗ có thể lệch nhau.
    """
    context = rescore.settings(out_dir)
    rows = rescore._read_predictions(context["predictions"])
    if not rows:
        raise FusionError("{} rỗng.".format(utils.rel(context["predictions"])))
    aspects = rescore.aspects_of(rows) or list(context["metrics"].get("aspects") or [])
    golds, preds, infos = records.to_arrays(rows, aspects)
    table, codes = read_probabilities(out_dir)
    if need_probabilities and table is None:
        raise FusionError(
            "Lượt '{}' không có {}: bước kết hợp cần xác suất. Chạy lại đường encoder bằng bản mã có "
            "ghi tệp xác suất (xem docs/04_experiments/06_lora_encoder.md mục 6).".format(
                utils.rel(out_dir), paths.pattern("probabilities")))
    meta = context["meta"]
    return {
        "dir": Path(out_dir),
        "rows": rows,
        "aspects": aspects,
        "golds": golds,
        "preds": preds,
        "infos": infos,
        "probabilities": table,
        "codes": codes,
        "labels": rescore.labels_of(meta),
        "task": rescore.task_of(meta, context["metrics"]),
        "meta": meta,
        "metrics": context["metrics"],
        "split": str(meta.get("split") or context["metrics"].get("split") or ""),
        "sample_ids": [str(row.get("chỉ số", "")) for row in rows],
    }


def negative_code(run):
    """Mã nhãn của lớp ÂM trong không gian nhãn của lượt chạy (tra qua `label_map.json`).

    Không suy từ thứ tự mã: không gian nhãn là `{1: positive, 2: negative, 3: neutral, 0: ''}` và đổi
    theo `label_space`, nên phải tra TÊN.
    """
    found = [int(code) for code, name in (run["labels"] or {}).items() if str(name) == "negative"]
    if not found:
        raise FusionError("Bảng tên nhãn không có nhãn 'negative' (labels={}).".format(run["labels"]))
    return found[0]


def samples_of(run, preds=None):
    """`Samples` cho một bộ nhãn đoán cụ thể (mặc định: nhãn gốc của lượt chạy)."""
    return scorers.Samples.build(run["aspects"], run["golds"], preds or run["preds"],
                                 task=run["task"], labels=run["labels"],
                                 sample_ids=run["sample_ids"])


def scores_of(samples, names=("accuracy", "prf")):
    """Chấm hai cơ sở đo và trả `(scores, scores_paper)` - đúng engine của lượt chạy."""
    names = list(names)
    return (scorers.run_all(samples, names=names)["scores"],
            scorers.run_all(samples.paper(), names=names)["scores"])


def negative_f1(scores_paper, aspect):
    """F1 lớp âm của một khía cạnh trên cơ sở `paper`; `None` khi KHÔNG có ô âm nào để bắt.

    Vì sao `None` chứ không phải 0,0: F1 = 0 khi không có ô âm nào là chuyện của THƯỚC ĐO, không phải
    của model - xem `docs/04_experiments/08_experiment_rationale.md` §7.
    """
    found = ((scores_paper.get("prf") or {}).get("by_aspect") or {}).get(aspect) or {}
    negative = found.get("negative") or {}
    if not negative.get("support"):
        return None
    return float(negative.get("f1") or 0.0)


def cells_of(scores_paper):
    """Số ô của cơ sở `paper` (mẫu số thật của phép chấm)."""
    return int((scores_paper.get("accuracy") or {}).get("cells") or 0)


def apply_thresholds(run, thresholds, negative=None):
    """Áp ngưỡng theo khía cạnh lên một lượt chạy, trả **bộ nhãn đoán MỚI** (không sửa bản gốc).

    Quy tắc cho từng khía cạnh:
    - ngưỡng `None` (ví dụ `price`) -> **giữ nguyên** nhãn của model;
    - có ngưỡng τ -> nếu `p(mã âm) >= τ` thì đoán mã ÂM, ngược lại giữ nguyên nhãn của model.

    Vì sao chỉ ĐẨY về lớp âm: mục tiêu của cả hướng này là lớp âm - lớp duy nhất mọi lượt đều yếu -
    nên đổi cả lớp dương chỉ mở thêm một trục sai số mà không ai kiểm được.
    """
    negative = negative_code(run) if negative is None else int(negative)
    table = run["probabilities"] or {}
    preds = [dict(pred) for pred in run["preds"]]
    for position, sample_id in enumerate(run["sample_ids"]):
        for aspect in run["aspects"]:
            tau = (thresholds or {}).get(aspect)
            if tau is None:
                continue
            probs = table.get((sample_id, aspect))
            if not probs:
                continue
            if probs.get(negative, 0.0) >= float(tau):
                preds[position][aspect] = negative
    return preds


def fit_thresholds(run, grid=None, max_cells_drop=MAX_CELLS_DROP, log=None):
    """Dò ngưỡng theo TỪNG khía cạnh trên một lượt `val`; trả bảng luật (KHÔNG ghi file).

    Thủ tục (cố ý đơn giản, để đọc lại là kiểm được):
    1. Chấm lượt chạy ở trạng thái GỐC -> số ô gốc và F1 âm gốc của từng khía cạnh.
    2. Với MỖI khía cạnh, quét lưới ngưỡng (các khía cạnh khác giữ nguyên) và tính F1 âm của chính
       khía cạnh đó. Khía cạnh **không có ô âm nào trên `val`** -> ngưỡng `None` + lí do (ca `price`).
    3. Chọn ngưỡng tốt nhất cho từng khía cạnh; **hoà thì chọn ngưỡng LỚN hơn** (đổi ít ô hơn).
    4. Áp TẤT CẢ ngưỡng đã chọn CÙNG LÚC; nếu tổng số ô giảm quá `max_cells_drop` thì bỏ ngưỡng của
       khía cạnh ÍT LỢI NHẤT rồi thử lại - ràng buộc chống "kiêng trả lời để lấy điểm".
    """
    grid = list(grid or GRID)
    negative = negative_code(run)
    base_scores, base_paper = scores_of(samples_of(run))
    base_cells = cells_of(base_paper)

    found = {}
    for aspect in run["aspects"]:
        base_f1 = negative_f1(base_paper, aspect)
        sweep = []
        for tau in grid:
            preds = apply_thresholds(run, {aspect: tau}, negative=negative)
            _, paper = scores_of(samples_of(run, preds))
            sweep.append({"ngưỡng": tau, "f1_âm": negative_f1(paper, aspect),
                          "cells": cells_of(paper)})
        usable = [item for item in sweep if item["f1_âm"] is not None]
        if base_f1 is None or not usable:
            found[aspect] = {
                "ngưỡng": None, "f1_âm_gốc": base_f1, "f1_âm_sau": base_f1,
                "lí do": "val không có ô âm nào của khía cạnh này: không có gì để dò",
                "sweep": sweep}
            continue
        best = max(usable, key=lambda item: (item["f1_âm"], item["ngưỡng"]))
        found[aspect] = {"ngưỡng": best["ngưỡng"], "f1_âm_gốc": base_f1,
                         "f1_âm_sau": best["f1_âm"], "lí do": None, "sweep": sweep}

    # Bước 4: áp cùng lúc rồi kiểm ràng buộc số ô. Bỏ dần khía cạnh ít lợi nhất (chênh F1 nhỏ nhất)
    # cho tới khi số ô không giảm quá ngưỡng cho phép.
    chosen = {aspect: item["ngưỡng"] for aspect, item in found.items() if item["ngưỡng"] is not None}
    while chosen:
        _, paper = scores_of(samples_of(run, apply_thresholds(run, chosen, negative=negative)))
        cells = cells_of(paper)
        if base_cells and cells >= base_cells * (1 - max_cells_drop):
            break
        worst = min(chosen, key=lambda aspect: (found[aspect]["f1_âm_sau"] - found[aspect]["f1_âm_gốc"],
                                               -chosen[aspect]))
        found[worst]["lí do"] = ("bỏ ngưỡng: áp cùng lúc làm số ô giảm quá {}%"
                                 .format(round(100 * max_cells_drop, 2)))
        found[worst]["f1_âm_sau"] = found[worst]["f1_âm_gốc"]
        found[worst]["ngưỡng_đã_bỏ"] = chosen[worst]
        del chosen[worst]
    final_scores, final_paper = scores_of(samples_of(run, apply_thresholds(run, chosen,
                                                                          negative=negative)))
    if log is not None:
        log("dò ngưỡng trên {}: {} khía cạnh có ngưỡng, số ô {} -> {}".format(
            utils.rel(run["dir"]), len(chosen), base_cells, cells_of(final_paper)))
    return {
        "nguồn": utils.rel(run["dir"]),
        "split": run["split"],
        "mã_âm": negative,
        "lưới": grid,
        "ràng buộc_ô": max_cells_drop,
        "khía_cạnh": found,
        "ngưỡng_chốt": dict(sorted(chosen.items())),
        "cells_gốc": base_cells,
        "cells_sau": cells_of(final_paper),
        "f1_âm_macro_gốc": _macro(base_paper, run["aspects"]),
        "f1_âm_macro_sau": _macro(final_paper, run["aspects"]),
        "ghi_chú": ("ngưỡng chốt trên {}; áp lên tập KHÁC (test) mới là số báo cáo"
                    .format(run["split"] or "val")),
    }


def _delta(after, before):
    """Chênh lệch `sau - trước`; `None` khi một đầu không có số (không tự đổi `None` thành 0,0)."""
    if after is None or before is None:
        return None
    return round(float(after) - float(before), 6)


def _macro_over_all(values):
    """Trung bình F1 lớp âm trên MỌI khía cạnh; khía cạnh không có ô âm (như `price`) tính là 0,0.

    Đây là cách đọc thứ HAI mà `present_plan.md` mục 8.4 yêu cầu, đứng cạnh `_macro`. Số này bị `price`
    kéo xuống, nhưng `price` đóng góp 0,0 ở CẢ trước lẫn sau nên nó không làm lệch phần chênh lệch -
    đó chính là lí do phải in cả hai cách.
    """
    numbers = [(value if value is not None else 0.0) for value in values.values()]
    return round(sum(numbers) / len(numbers), 6) if numbers else None


def applied_report(run, rules, negative=None):
    """Số của một lượt chạy SAU KHI áp bảng ngưỡng ĐÃ ĐÓNG BĂNG - không chạy model, không sửa bản gốc.

    Vì sao cần bước riêng: `fit_thresholds` chỉ so được trên CHÍNH lượt nó đọc (luật 1: chốt trên `val`),
    nên số báo cáo - số khi áp lên `test` - phải có một chỗ ráp hai bước lại: đọc tệp luật đã ghi ->
    `apply_thresholds` -> chấm bằng ĐÚNG engine của dự án.

    Bảng luật chốt cho một KHÔNG GIAN NHÃN cụ thể (khoá `mã_âm`), nên lượt bị áp phải cùng không gian
    nhãn: khác mã âm là LỖI (cột xác suất sẽ bị đọc lệch), không phải chuyện bỏ qua được.

    Trả về: ngưỡng dùng, khía cạnh để nguyên (`price`), số của lượt TRƯỚC và SAU (hai cơ sở, số ô, F1 âm
    từng khía cạnh, macro hai cách), và chênh lệch từng khía cạnh.
    """
    rules = rules or {}
    thresholds = dict(rules.get("ngưỡng_chốt") or {})
    negative = negative_code(run) if negative is None else int(negative)
    saved = rules.get("mã_âm")
    if saved is not None and int(saved) != negative:
        raise FusionError(
            "Bảng ngưỡng chốt cho mã âm {} nhưng lượt '{}' dùng mã âm {}: cột xác suất sẽ bị đọc lệch, "
            "không áp được.".format(saved, utils.rel(run["dir"]), negative))
    used = {aspect: thresholds[aspect] for aspect in run["aspects"]
            if thresholds.get(aspect) is not None}
    untouched = [aspect for aspect in run["aspects"] if thresholds.get(aspect) is None]
    reasons = sorted({str(((rules.get("khía_cạnh") or {}).get(aspect) or {}).get("lí do") or "")
                      for aspect in untouched} - {""})
    before = report_of(run)
    after = report_of(run, apply_thresholds(run, thresholds, negative=negative))
    return {
        "lượt": utils.rel(run["dir"]),
        "split": run["split"],
        "nguồn_luật": rules.get("nguồn"),
        "nguồn_split": rules.get("split"),
        "ngưỡng_dùng": used,
        "khía_cạnh_để_nguyên": untouched,
        "khía_cạnh_có_ngưỡng_không_có_ở_lượt_này": sorted(
            aspect for aspect in thresholds if aspect not in run["aspects"]),
        "số_ô_trước": before["cells_paper"],
        "số_ô_sau": after["cells_paper"],
        "accuracy_all_trước": before["accuracy_all"],
        "accuracy_all_sau": after["accuracy_all"],
        "accuracy_paper_trước": before["accuracy_paper"],
        "accuracy_paper_sau": after["accuracy_paper"],
        "f1_âm_từng_khía_cạnh_trước": before["f1_âm_từng_khía_cạnh"],
        "f1_âm_từng_khía_cạnh_sau": after["f1_âm_từng_khía_cạnh"],
        "chênh_f1_âm_từng_khía_cạnh": {
            aspect: _delta(after["f1_âm_từng_khía_cạnh"].get(aspect),
                           before["f1_âm_từng_khía_cạnh"].get(aspect))
            for aspect in run["aspects"]},
        "f1_âm_macro_trước": before["f1_âm_macro"],
        "f1_âm_macro_sau": after["f1_âm_macro"],
        "chênh_f1_âm_macro": {key: _delta(after["f1_âm_macro"].get(key),
                                          before["f1_âm_macro"].get(key))
                              for key in before["f1_âm_macro"]},
        "macro_trên_mọi_khía_cạnh": {
            "trước": _macro_over_all(before["f1_âm_từng_khía_cạnh"]),
            "sau": _macro_over_all(after["f1_âm_từng_khía_cạnh"]),
            "cách_đọc": "khía cạnh không có ô âm (price) tính là 0,0 ⇒ số này bị kéo xuống; đóng góp "
                        "của price là 0,0 ở CẢ hai bên nên không làm lệch chênh lệch",
        },
        "ghi_chú_đọc_số": ("ngưỡng chốt trên '{}'; lượt này là '{}'. Khía cạnh để nguyên: {}{}. "
                           "Số ô luôn đọc kèm (luật 1 của metrics.md)."
                           .format(rules.get("split") or "val", run["split"] or "?",
                                   ", ".join(untouched) or "không có",
                                   " ({})".format("; ".join(reasons)) if reasons else "")),
    }


def model_of(run):
    """Tên model của một lượt (khoá `experiment.model` trong `run_meta.json`).

    Đây là KHOÁ để ráp trọng số chốt trên `val` với lượt cần áp trên `test`: hai bên là hai thí nghiệm
    KHÁC NHAU (`.../exp003` là `val`, `.../exp004` là `test`) nên đường dẫn không khớp - chỉ tên model
    khớp. Thiếu khoá thì không ráp được, nên báo LỖI thay vì đoán.
    """
    experiment = (run.get("meta") or {}).get("experiment") or {}
    name = str(experiment.get("model") or "").strip()
    if not name:
        raise FusionError(
            "Không đọc được `experiment.model` của lượt '{}' nên không ráp được trọng số chốt trên "
            "`val`.".format(utils.rel(run.get("dir") or "")))
    return name


def negative_macro_of(run):
    """Macro-F1 lớp âm của CHÍNH lượt đang xét - đại lượng dùng làm TRỌNG SỐ nguồn trong ensemble."""
    _scores, paper = scores_of(samples_of(run))
    return float(_macro(paper, run["aspects"])["macro_trên_khía_cạnh_có_ô_âm"] or 0.0)


def _normalise(values):
    """Chuẩn hoá trọng số cho tổng bằng 1; mọi giá trị 0 thì trả trọng số BẰNG NHAU (không chia cho 0)."""
    total = sum(values.values())
    if total <= 0:
        return {key: round(1.0 / len(values), 6) for key in values}
    return {key: round(value / total, 6) for key, value in values.items()}


def fit_ensemble_weights(runs):
    """Trọng số cho ensemble: macro-F1 lớp âm trên `val` của từng lượt, chuẩn hoá tổng bằng 1.

    Vì sao chuẩn hoá: chỉ ĐỘ LỚN tương đối có nghĩa khi trung bình xác suất; để tổng bằng 1 thì trọng
    số in ra đọc được như tỉ lệ đóng góp. Mọi lượt đều 0 (không lượt nào có ô âm) thì trả trọng số
    BẰNG NHAU - không chia cho 0, và cũng không im lặng coi như lượt nào cũng tốt.

    Khoá của bảng là ĐƯỜNG DẪN thư mục kết quả, nên bảng này chỉ dùng được cho chính các lượt vừa chốt.
    Muốn chốt trên `val` rồi áp lên `test`: dùng `fit_weights_by_model` + `weights_for`.
    """
    return _normalise({str(run["dir"]): negative_macro_of(run) for run in runs})


def fit_weights_by_model(runs):
    """Trọng số ensemble khoá theo TÊN MODEL - dạng chốt trên `val` rồi áp lên `test` được.

    Vì sao cần thêm hàm này: `fit_ensemble_weights` khoá theo đường dẫn thư mục kết quả, mà lượt `val`
    và lượt `test` của cùng một encoder nằm ở hai thư mục khác nhau (`.../exp003` và `.../exp004`).
    Muốn giữ luật "chốt trên `val`, áp lên `test`" thì bảng trọng số phải mang khoá SỐNG QUA hai tập -
    đó là tên model.

    Hai lượt cùng model trong một lần gọi là LỖI: khi đó không biết lấy ô nào của lượt nào, và im lặng
    chọn một trong hai đúng là kiểu lỗi cần chặn.
    """
    values = {}
    for run in runs:
        model = model_of(run)
        if model in values:
            raise FusionError(
                "Hai lượt cùng model '{}' trong một lần chốt trọng số; trọng số khoá theo tên model nên "
                "không ráp được. Mỗi model đúng một lượt.".format(model))
        values[model] = negative_macro_of(run)
    return _normalise(values)


def weights_document(runs, weights):
    """Nội dung tệp trọng số: khoá là TÊN MODEL, kèm nguồn chốt để người đọc kiểm lại được."""
    return {
        "khoá": "model",
        "chốt_trên": [{"model": model_of(run), "lượt": utils.rel(run["dir"]),
                       "split": run["split"]} for run in runs],
        "trọng_số": {model_of(run): weights[model_of(run)] for run in runs},
    }


def weights_for(runs, table, source=""):
    """Ráp bảng trọng số (khoá theo tên model) vào các lượt đang có; thiếu model nào là LỖI kèm tên.

    Trả về bảng khoá theo đường dẫn để `combine_probabilities` dùng được ngay.
    """
    table = {str(key): float(value) for key, value in dict(table or {}).items()}
    missing = sorted({model_of(run) for run in runs if model_of(run) not in table})
    if missing:
        raise FusionError(
            "Bảng trọng số{} không có model: {}. Bảng đang có: {}.".format(
                " ({})".format(source) if source else "", ", ".join(missing),
                ", ".join(sorted(table)) or "(rỗng)"))
    return {str(run["dir"]): table[model_of(run)] for run in runs}


def load_weights(path):
    """Đọc tệp trọng số do `ensemble.py --write-weights` ghi; sai định dạng là LỖI, không đoán."""
    table = _read_json(path).get("trọng_số")
    if not isinstance(table, dict) or not table:
        raise FusionError(
            "Tệp trọng số '{}' không có khoá `trọng_số`; đây không phải tệp do "
            "`ensemble.py --write-weights` ghi.".format(utils.rel(path)))
    return {str(key): float(value) for key, value in table.items()}


def combine_probabilities(runs, weights=None):
    """Trung bình xác suất của nhiều lượt chạy theo `(chỉ số, khía cạnh, mã)`.

    Trọng số mặc định **bằng nhau**; `weights` dùng trọng số theo `fit_ensemble_weights`. Ô nào chỉ có
    ở một phần các lượt thì lấy trung bình của các lượt CÓ ô đó (và số lượt tham gia được đếm lại) -
    đòi hỏi mọi lượt phải có đủ mọi ô là điều không lượt nào bảo đảm.
    """
    weights = weights or {str(run["dir"]): 1.0 for run in runs}
    totals, masses = {}, {}
    for run in runs:
        weight = float(weights.get(str(run["dir"]), 1.0))
        if weight <= 0:
            continue
        for key, probs in (run["probabilities"] or {}).items():
            bucket = totals.setdefault(key, {})
            for code, value in probs.items():
                bucket[code] = bucket.get(code, 0.0) + weight * float(value)
            masses[key] = masses.get(key, 0.0) + weight
    combined = {}
    for key, bucket in totals.items():
        mass = masses.get(key) or 1.0
        combined[key] = {code: value / mass for code, value in bucket.items()}
    return combined


def ensemble_predictions(run, runs, weights=None):
    """Nhãn đoán của bản ENSEMBLE: `argmax` trên xác suất TRUNG BÌNH, theo từng khía cạnh.

    `run` là lượt giữ KHUNG ô (chỉ số dòng + danh sách khía cạnh) - mọi lượt trong `runs` phải chấm
    cùng split nên cùng khung; ô nào không có xác suất trung bình thì giữ nhãn của `run`.
    """
    combined = combine_probabilities(runs, weights=weights)
    preds = [dict(pred) for pred in run["preds"]]
    for position, sample_id in enumerate(run["sample_ids"]):
        for aspect in run["aspects"]:
            probs = combined.get((sample_id, aspect))
            if probs:
                preds[position][aspect] = max(sorted(probs), key=lambda code: probs[code])
    return preds



def fit_rules(llm_run, encoder_run):
    """Bảng LUẬT LAI chốt trên `val`: mỗi khía cạnh lấy nguồn có F1 âm cao hơn.

    Trả `{khía cạnh: {"nguồn": "encoder"|"llm", "f1_âm_encoder", "f1_âm_llm", "lí do"}}`, phủ HẾT khía
    cạnh - không để ô trống cho người sau tự đoán.

    Quy tắc HOÀ: chọn **LLM**. Lý do: luật lai sinh ra để bù chỗ encoder yếu, còn LLM là nguồn mạnh về
    sắc thái; hoà thì giữ nguồn mạnh và ghi rõ hai số F1 để người đọc tự thấy đó là hoà.
    """
    _scores, llm_paper = scores_of(samples_of(llm_run))
    _other_scores, encoder_paper = scores_of(samples_of(encoder_run))
    rules = {}
    for aspect in llm_run["aspects"]:
        llm = negative_f1(llm_paper, aspect)
        encoder = negative_f1(encoder_paper, aspect)
        if llm is None and encoder is None:
            chosen, reason = "llm", "val không có ô âm nào của khía cạnh này (cả hai nguồn)"
        elif encoder is None:
            chosen, reason = "llm", "encoder không có ô âm nào để so trên val"
        elif llm is None:
            chosen, reason = "encoder", "LLM không có ô âm nào để so trên val"
        elif encoder > llm:
            chosen, reason = "encoder", "encoder hơn {} F1 âm trên val".format(round(encoder - llm, 4))
        elif encoder == llm:
            chosen, reason = "llm", "hoà F1 âm trên val -> giữ LLM (nguồn mạnh về sắc thái)"
        else:
            chosen, reason = "llm", "LLM hơn {} F1 âm trên val".format(round(llm - encoder, 4))
        rules[aspect] = {"nguồn": chosen, "f1_âm_encoder": encoder, "f1_âm_llm": llm,
                         "lí do": reason}
    return rules


def apply_rules(llm_run, encoder_run, rules):
    """Áp bảng luật lai: mỗi khía cạnh lấy nhãn của nguồn đã chốt, giữ KHUNG ô của `llm_run`.

    Ô nào nguồn đã chốt KHÔNG có (khác tập ô - ví dụ một nguồn chấm trên tập con) thì giữ nhãn của
    `llm_run` và ĐẾM lại vào `thiếu`, để chuyện đó không im lặng.
    """
    sources = {
        "llm": {sid: dict(pred) for sid, pred in zip(llm_run["sample_ids"], llm_run["preds"])},
        "encoder": {sid: dict(pred) for sid, pred in zip(encoder_run["sample_ids"],
                                                         encoder_run["preds"])},
    }
    preds = [dict(pred) for pred in llm_run["preds"]]
    counts = {"llm": 0, "encoder": 0, "thiếu": 0}
    for position, sample_id in enumerate(llm_run["sample_ids"]):
        for aspect in llm_run["aspects"]:
            name = (rules.get(aspect) or {}).get("nguồn") or "llm"
            found = sources[name].get(sample_id)
            if not found or aspect not in found:
                counts["thiếu"] += 1
                continue
            preds[position][aspect] = found[aspect]
            counts[name] += 1
    return preds, counts


def vote(runs):
    """Bỏ phiếu TỪNG Ô trên nhiều lượt chạy (self-consistency). Trả `(nhãn mới, thống kê)`.

    Luật đã chốt (`present_plan.md` mục 4.9, `docs/04_experiments/metrics.md` luật 6):
    - **ba mẫu** (`seed` 1/2/3) cho đợt này;
    - ô chỉ được bỏ phiếu nếu **đọc được ở ít nhất một lượt**; ô không lượt nào đọc được thì không có
      phiếu (giữ `None` - bộ chấm tính là sai, đúng như mọi lượt khác);
    - **hoà thì lấy nhãn của lượt ĐẦU TIÊN** trong `runs`, nên chỗ gọi phải truyền theo thứ tự `seed`
      tăng dần (1, 2, 3) - "đầu tiên" chính là "seed nhỏ nhất".
    """
    if not runs:
        raise FusionError("Không có lượt nào để bỏ phiếu.")
    frame = runs[0]
    lookup = [{sid: dict(pred) for sid, pred in zip(run["sample_ids"], run["preds"])}
              for run in runs]
    preds = [dict(pred) for pred in frame["preds"]]
    counts = {"ô đủ phiếu": 0, "ô hoà": 0, "ô không lượt nào đọc được": 0}
    for position, sample_id in enumerate(frame["sample_ids"]):
        for aspect in frame["aspects"]:
            votes = []
            for table in lookup:
                found = table.get(sample_id)
                if found and found.get(aspect) is not None:
                    votes.append(found[aspect])
            if not votes:
                counts["ô không lượt nào đọc được"] += 1
                continue
            tally = {}
            for code in votes:
                tally[code] = tally.get(code, 0) + 1
            best = max(tally.values())
            winners = sorted(code for code, count in tally.items() if count == best)
            if len(winners) > 1:
                counts["ô hoà"] += 1
                chosen = winners[0]
                for table in lookup:                      # lượt ĐẦU TIÊN có nhãn nằm trong nhóm hoà
                    found = table.get(sample_id)
                    if found and found.get(aspect) in winners:
                        chosen = found[aspect]
                        break
            else:
                chosen = winners[0]
            preds[position][aspect] = chosen
            counts["ô đủ phiếu"] += 1
    counts["số lượt bỏ phiếu"] = len(runs)
    return preds, counts


def report_of(run, preds=None, extra=None):
    """Số của một bộ nhãn đoán, dạng ghi được vào JSON: hai cơ sở, số ô, F1 âm từng khía cạnh.

    `preds=None` nghĩa là chấm CHÍNH nhãn của lượt chạy (dùng để làm mốc so trước/sau).
    Dùng CHUNG cho cả bốn bước kết hợp (ngưỡng, ensemble, lai, biểu quyết) để chúng không mỗi bước
    báo một kiểu số khác nhau - và để mọi bước đều kèm số ô theo luật 1 của `metrics.md`.
    """
    samples = samples_of(run, preds)
    scores, paper = scores_of(samples)
    return {
        "lượt": utils.rel(run["dir"]),
        "split": run["split"],
        "accuracy_all": (scores.get("accuracy") or {}),
        "accuracy_paper": (paper.get("accuracy") or {}),
        "cells_paper": cells_of(paper),
        "f1_âm_từng_khía_cạnh": {aspect: negative_f1(paper, aspect) for aspect in run["aspects"]},
        "f1_âm_macro": _macro(paper, run["aspects"]),
        **(extra or {}),
    }


def dump_inputs(run, out_path, negative=None):
    """Ghi ĐẦU VÀO RÚT GỌN của một lượt chạy để bước kết hợp tái lập được TỪ REPO.

    Lượt chạy thật nằm trên Drive (repo KHÔNG commit `results/`), nên nếu chỉ ghi kết luận thì không ai
    kiểm lại được. Tệp này giữ ĐÚNG những gì bước kết hợp dùng: khung ô (chỉ số + khía cạnh), nhãn
    đúng, nhãn đoán, và xác suất lớp âm/dương của CHÍNH lượt đó - vài trăm KB mỗi lượt.

    KHÔNG chứa văn bản review: bước kết hợp không cần, và không nên nhân bản dữ liệu ra chỗ thứ hai.
    """
    negative = negative_code(run) if negative is None else int(negative)
    found = [int(code) for code, name in (run["labels"] or {}).items() if str(name) == "positive"]
    positive = found[0] if found else None
    table = run["probabilities"] or {}
    columns = ["chỉ số", "split", "khía cạnh", "nhãn đúng", "nhãn đoán", "p(mã âm)", "p(mã dương)"]
    rows = []
    for position, sample_id in enumerate(run["sample_ids"]):
        for aspect in run["aspects"]:
            probs = table.get((sample_id, aspect)) or {}
            rows.append([sample_id, run["split"], aspect,
                         (run["golds"][position] or {}).get(aspect),
                         (run["preds"][position] or {}).get(aspect),
                         probs.get(negative),
                         probs.get(positive) if positive is not None else None])
    path = Path(out_path)
    utils.write_csv(rows, columns, path)
    return path



def _macro(scores_paper, aspects):
    """F1 âm macro theo hai cách, với tên khoá CỐ ĐỊNH (chỗ gọi không phải tự dựng tên khoá).

    - `macro_trên_khía_cạnh_có_ô_âm`: trung bình F1 âm của các khía cạnh CÓ ô âm trên `val`;
    - `macro_trên_khía_cạnh_đang_dương`: trung bình của các khía cạnh đang có F1 âm > 0 (bỏ các khía
      cạnh mà model chưa bắt được ô âm nào, vì 0,0 kéo trung bình xuống mà không thêm thông tin);
    - `số_khía_cạnh_có_ô_âm`: mẫu số của số thứ nhất (để người đọc biết trung bình trên bao nhiêu).

    Vì sao hai số: `price` chỉ có 1-6 ô (nhiễu), nên một con số macro duy nhất cho 7 khía cạnh là để
    nhiễu đó làm loãng kết luận về việc ngưỡng có ích hay không - xem `present_plan.md` mục 8.4.
    """
    values = [(aspect, negative_f1(scores_paper, aspect)) for aspect in aspects]
    usable = [value for _aspect, value in values if value is not None]
    macro_all = round(sum(usable) / len(usable), 6) if usable else None
    macro_positive = [value for _aspect, value in values if value is not None and value > 0.0]
    return {"macro_trên_khía_cạnh_có_ô_âm": macro_all,
            "macro_trên_khía_cạnh_đang_dương": (
                round(sum(macro_positive) / len(macro_positive), 6) if macro_positive else None),
            "số_khía_cạnh_có_ô_âm": len(usable)}

