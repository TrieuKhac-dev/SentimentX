# -*- coding: utf-8 -*-
"""KẾT HỢP các lượt chạy: dò ngưỡng theo khía cạnh, ensemble encoder, luật lai, biểu quyết, router.

VÌ SAO CÓ MODULE NÀY
Năm việc này không chạy model: chúng đọc `predictions.csv` (nhãn cứng) và `probabilities.csv` (xác suất
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
    Dùng CHUNG cho cả năm bước kết hợp (ngưỡng, ensemble, lai, biểu quyết, router) để chúng không mỗi bước
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


# ---------------------------------------------------------------------------------------------
# ROUTER THEO KHÍA CẠNH (đợt 10) - bước kết hợp thứ NĂM
#
# VÌ SAO CẦN BƯỚC NÀY
# `ensemble_predictions` gộp xác suất bằng MỘT bộ trọng số cho MỌI khía cạnh, mà các lượt encoder
# mạnh yếu KHÁC NHAU theo từng khía cạnh: chọn-theo-khía-cạnh có trần cao hơn lượt đơn tốt nhất
# khoảng 0,5 điểm (`docs/04_experiments/09_fusion.md` mục 3.5). Router giữ KHUNG Ô của lượt đầu rồi,
# cho TỪNG khía cạnh, lấy nhãn của một lượt đã chốt làm nguồn.
#
# LUẬT ĐÃ CHỐT - đóng băng vào tệp JSON TRƯỚC khi áp lên `test` (luật 1 ở đầu tệp này; luật 1.4 của
# `docs/00_workflow/02_rules.md`): đổi luật sau khi đã thấy `test` là chọn bằng tập sẽ báo cáo.
#   1. tiêu chí: **F1 lớp ÂM của chính khía cạnh đó trên `val`** (cơ sở `paper`);
#   2. khía cạnh **không có ô âm nào trên `val`** (ca `price`): chuyển sang **accuracy của ô thuộc
#      khía cạnh** (cơ sở `all`), và GHI LÍ DO vào tệp luật - đổi tiêu chí mà im lặng là chọn mò;
#   3. HOÀ: xét **accuracy ô của khía cạnh**; vẫn hoà: lượt **ĐẦU** trong danh sách người chạy đưa
#      vào - nên THỨ TỰ truyền vào là một phần của luật, và tệp luật ghi lại thứ tự đó;
#   4. khoá của tệp luật là **TÊN MODEL**, vì lượt `val` và lượt `test` của cùng một encoder nằm ở
#      hai thư mục khác nhau (`.../exp003` và `.../exp004` - xem `weights_for` ở trên).
# ---------------------------------------------------------------------------------------------

ROUTER_CRITERIA = {
    "f1_âm": "F1 lớp ÂM của khía cạnh đó trên `val` (cơ sở `paper`) - luật của dự án khi chỉ được chọn "
             "MỘT số, vì lớp âm là chỗ mọi lượt đều yếu",
    "accuracy": "accuracy của ô thuộc khía cạnh trên `val` (cơ sở `all`) - sát chỉ số BÁO CÁO hơn, nên "
                "kỳ vọng tăng được nhiều hơn, nhưng KHÔNG nhìn tới lớp âm",
}

ROUTER_LAW = {
    "tiêu_chí": "CHỌN MỘT trong `ROUTER_CRITERIA`; chốt LÚC DỰNG luật và ghi vào tệp - `--apply` đọc lại "
                "từ tệp nên KHÔNG đổi được sau khi đã thấy `test` (luật 1.4 của 02_rules.md)",
    "không_có_ô_âm_trên_val": "chuyển sang ACCURACY của ô thuộc khía cạnh (cơ sở `all`); lí do ghi vào "
                             "từng khía cạnh của tệp luật",
    "hoà": "xét theo tiêu chí còn lại; vẫn hoà thì lượt ĐẦU trong danh sách truyền vào",
    "khoá_luật": "tên model (lượt val và lượt test của cùng encoder nằm ở hai thư mục khác nhau)",
    "đơn_vị_chọn": "MỘT lượt cho MỖI khía cạnh; KHÔNG trộn xác suất (đó là việc của ensemble)",
}


def aspect_scores(run):
    """Điểm của TỪNG khía cạnh ở MỘT lượt - đầu vào duy nhất của router.

    Hai số, hai cơ sở, cố ý: **F1 lớp âm** trên cơ sở `paper` (tiêu chí chính, và `None` khi khía
    cạnh không có ô âm nào để so) và **accuracy** trên cơ sở `all` (đọc thẳng `by_aspect` của bộ
    chấm `accuracy`, không tự đếm - dự án chỉ có MỘT định nghĩa metric).

    Số ô cũng trả về, để người đọc tệp luật thấy ngay khía cạnh nào chỉ có 1-6 ô (`price`).
    """
    scores, paper = scores_of(samples_of(run))
    accuracy = scores.get("accuracy") or {}
    paper_accuracy = paper.get("accuracy") or {}
    cells = accuracy.get("cells_by_aspect") or {}
    paper_cells = paper_accuracy.get("cells_by_aspect") or {}
    found = {}
    for aspect in run["aspects"]:
        found[aspect] = {
            "f1_âm": negative_f1(paper, aspect),
            "accuracy": (accuracy.get("by_aspect") or {}).get(aspect),
            "ô": int(cells.get(aspect) or 0),
            "ô_paper": int(paper_cells.get(aspect) or 0),
        }
    return found


def _criterion_value(item, name):
    """`(có số không, giá trị)` của một tiêu chí ở một khía cạnh - `None` khác hẳn 0,0."""
    if name == "accuracy":
        value = item.get("accuracy")
    else:
        value = item.get("f1_âm")
    return (value is not None, float(value or 0.0))


def _router_prefers(left, right, criterion="f1_âm"):
    """`left` có thắng `right` cho một khía cạnh không - ĐÚNG luật ở `ROUTER_LAW`.

    Thứ tự: **tiêu chí đã chốt** -> **tiêu chí còn lại** -> (là chuyện của chỗ gọi) thứ tự truyền vào.
    Một bên `None` (không có số) mà bên kia có thì bên CÓ SỐ thắng: `price` trên `val` không có ô âm nào
    nên F1 lớp âm là `None` ở MỌI lượt - đúng ca phải rơi xuống accuracy.
    """
    order = ("accuracy", "f1_âm") if criterion == "accuracy" else ("f1_âm", "accuracy")
    for name in order:
        left_has, left_value = _criterion_value(left, name)
        right_has, right_value = _criterion_value(right, name)
        if left_has != right_has:
            return left_has
        if left_has and left_value != right_value:
            return left_value > right_value
    return False


def _router_reason(item, criterion="f1_âm"):
    """Vì sao khía cạnh này chọn lượt đó - câu người đọc kiểm lại được, không phải mã lỗi."""
    if criterion == "accuracy":
        return "accuracy ô của khía cạnh cao nhất trên val ({})".format(
            round(float(item.get("accuracy") or 0.0), 4))
    if item.get("f1_âm") is None:
        return ("val không có ô âm nào của khía cạnh này (ô {}): chuyển sang accuracy"
                .format(item.get("ô")))
    return "F1 lớp âm cao nhất trên val ({})".format(round(float(item["f1_âm"]), 4))


def fit_aspect_router(runs, criterion="f1_âm"):
    """Chốt ROUTER trên các lượt `val`: `{khía cạnh: {model, lượt, lí_do, điểm}}`.

    `criterion` là tiêu chí chốt (một khoá của `ROUTER_CRITERIA`); mặc định `f1_âm` là luật của dự án
    khi chỉ được chọn MỘT số. Tiêu chí này ĐI VÀO tệp luật (`router_document`), nên đổi nó giữa chừng là
    nhìn thấy được.

    Vì sao khoá là TÊN MODEL (không phải đường dẫn): cùng một encoder chạy `val` ở thư mục này và
    `test` ở thư mục khác, nên chỉ tên model sống qua được hai tập - y như `fit_weights_by_model`.

    Chỉ chốt trên `val`: đưa lượt `test` vào là LỖI (luật 1). Mỗi model đúng MỘT lượt: hai lượt cùng
    model thì không biết lấy ô của lượt nào, nên báo lỗi chứ không im lặng chọn một.

    Bảng `điểm` giữ số của MỌI ứng viên cho khía cạnh đó (cả hai tiêu chí): nhờ vậy người đọc kiểm lại
    được lựa chọn, và tệp luật tự nó đủ để dò lại bằng tiêu chí khác - không phải chạy lại model.
    """
    if not runs:
        raise FusionError("Không có lượt nào để chốt router.")
    criterion = str(criterion or "")
    if criterion not in ROUTER_CRITERIA:
        raise FusionError(
            "Tiêu chí router '{}' không có. Chọn ĐÚNG MỘT trong: {} - và phải chốt TRƯỚC khi áp lên "
            "`test` (luật 1.4 của 02_rules.md).".format(criterion,
                                                        ", ".join(sorted(ROUTER_CRITERIA))))
    wrong = [run for run in runs if str(run["split"]) != "val"]
    if wrong:
        raise FusionError(
            "Router chỉ chốt được trên `val`, nhưng có lượt không phải `val`: {}. Chốt trên `val` rồi "
            "áp lên tập khác bằng `--router-file`.".format(
                ", ".join("{} (split={})".format(utils.rel(run["dir"]), run["split"] or "?")
                          for run in wrong)))
    tables = []
    seen = {}
    for run in runs:
        model = model_of(run)
        if model in seen:
            raise FusionError(
                "Hai lượt cùng model '{}' trong một lần chốt router; luật khoá theo tên model nên bảng "
                "điểm của chúng sẽ ghi đè nhau. Mỗi model đúng một lượt.".format(model))
        seen[model] = run
        tables.append((run, aspect_scores(run)))
    router = {}
    for aspect in runs[0]["aspects"]:
        best_run, best_item = None, None
        for run, table in tables:
            item = table[aspect]
            if best_item is None or _router_prefers(item, best_item, criterion):
                best_run, best_item = run, item
        router[aspect] = {
            "model": model_of(best_run),
            "lượt": utils.rel(best_run["dir"]),
            "lí_do": _router_reason(best_item, criterion),
            "điểm": {model_of(run): table[aspect] for run, table in tables},
        }
    return router


def router_document(runs, router, criterion="f1_âm"):
    """Nội dung tệp luật router: LUẬT + tiêu chí đã chốt + nguồn chốt + lựa chọn + ĐIỂM mọi ứng viên.

    Ghi cả `điểm` của mọi ứng viên (hai tiêu chí, số ô): tệp luật tự nó đủ để người đọc dò lại lựa chọn
    và thấy lựa chọn khác sẽ ra sao - ĐÓ là điều kiện để việc đóng băng luật có nghĩa.
    """
    return {
        "khoá": "model",
        "tiêu_chí": criterion,
        "luật": dict(ROUTER_LAW),
        "chốt_trên": [{"model": model_of(run), "lượt": utils.rel(run["dir"]), "split": run["split"]}
                      for run in runs],
        "thứ_tự_hoà": [model_of(run) for run in runs],
        "router": {aspect: {"model": item["model"], "lí_do": item["lí_do"], "điểm": item["điểm"]}
                   for aspect, item in router.items()},
    }


def load_router(path):
    """Đọc tệp luật router do `ensemble_aspect.py --write-router` ghi; sai định dạng là LỖI."""
    table = _read_json(path).get("router")
    if not isinstance(table, dict) or not table:
        raise FusionError(
            "Tệp router '{}' không có khoá `router`; đây không phải tệp do "
            "`ensemble_aspect.py --write-router` ghi.".format(utils.rel(path)))
    chosen = {}
    for aspect, item in table.items():
        model = str((item or {}).get("model") or "").strip()
        if not model:
            raise FusionError(
                "Tệp router '{}' thiếu `model` cho khía cạnh '{}': không ráp được với các lượt đang "
                "áp.".format(utils.rel(path), aspect))
        chosen[str(aspect)] = model
    return chosen


def router_for(runs, table, source=""):
    """Ráp bảng luật router (khoá tên model) vào các lượt đang có -> `{khía cạnh: đường dẫn lượt}`.

    Thiếu model nào là LỖI kèm TÊN và khía cạnh đang cần nó: im lặng quay về lượt đầu là tự đổi luật
    đã đóng băng.
    """
    by_model = {}
    for run in runs:
        model = model_of(run)
        if model in by_model:
            raise FusionError(
                "Hai lượt cùng model '{}' trong một lần áp router; luật khoá theo tên model nên không "
                "ráp được. Mỗi model đúng một lượt.".format(model))
        by_model[model] = run
    missing = {}
    for aspect, model in dict(table or {}).items():
        if model not in by_model:
            missing.setdefault(model, []).append(aspect)
    if missing:
        raise FusionError(
            "Bảng luật router{} chọn model không có trong các lượt đang áp: {}. Đang có: {}.".format(
                " ({})".format(source) if source else "",
                "; ".join("{} (khía cạnh {})".format(model, ", ".join(aspects))
                          for model, aspects in sorted(missing.items())),
                ", ".join(sorted(by_model)) or "(rỗng)"))
    return {aspect: str(by_model[model]["dir"]) for aspect, model in dict(table or {}).items()}


def router_predictions(base_run, runs, choices):
    """Nhãn của bản ROUTER: giữ KHUNG Ô của `base_run`, mỗi khía cạnh lấy nhãn của lượt đã chốt.

    Trả `(nhãn, đếm)`. Khía cạnh không có trong luật hoặc ô mà nguồn không có thì **giữ nhãn của
    `base_run`** và ĐẾM RIÊNG (`không_có_trong_luật`, `thiếu_ô`): đổi luật âm thầm mới là lỗi, còn hai
    ca này phải nhìn thấy được trong báo cáo.
    """
    lookup = {str(run["dir"]): {sid: dict(pred) for sid, pred in zip(run["sample_ids"], run["preds"])}
              for run in runs}
    preds = [dict(pred) for pred in base_run["preds"]]
    per_aspect, missing, not_in_law = {}, 0, set()
    for position, sample_id in enumerate(base_run["sample_ids"]):
        for aspect in base_run["aspects"]:
            source = (choices or {}).get(aspect)
            if source is None:
                not_in_law.add(aspect)
                continue
            found = (lookup.get(source) or {}).get(sample_id) or {}
            if aspect not in found:
                missing += 1
                continue
            preds[position][aspect] = found[aspect]
            per_aspect[aspect] = per_aspect.get(aspect, 0) + 1
    return preds, {"theo_khía_cạnh": dict(sorted(per_aspect.items())),
                   "thiếu_ô": missing, "không_có_trong_luật": sorted(not_in_law)}


def members_report(runs):
    """Số của TỪNG lượt thành viên trên cùng tập - bắt buộc để đọc số của bản gộp/router.

    Vì sao nằm ở đây: `docs/04_experiments/09_fusion.md` mục 4 nói bản kết hợp chỉ có nghĩa khi đứng
    cạnh số của từng thành viên trên CÙNG tập; để chỗ gọi tự ráp là mở đường cho việc so sai tập.
    """
    found = []
    for run in runs:
        report = report_of(run)
        found.append({"lượt": utils.rel(run["dir"]), "split": run["split"],
                      "f1_âm_macro": report["f1_âm_macro"],
                      "accuracy_all": report["accuracy_all"],
                      "cells_paper": report["cells_paper"]})
    return found


# ---------------------------------------------------------------------------------------------
# GỘP HAI TẦNG (đợt 10, mục 14.9/14.10): KHUNG Ô từ ENCODER, SẮC THÁI từ lượt MỘT khía cạnh.
#
# LUẬT ĐÃ CHỐT - ghi TRƯỚC khi chạy bảy lượt một-khía-cạnh (luật 1.4 của `02_rules.md`; mục 14.10
# của `present_plan.md`). Đổi luật sau khi đã thấy `test` là chọn bằng tập sẽ báo cáo:
#   1. KHUNG Ô (dòng nào, khía cạnh nào) lấy từ lượt ENCODER - lượt ĐẦU trong danh sách;
#   2. SẮC THÁI của mỗi khía cạnh lấy từ lượt MỘT-khía-cạnh của CHÍNH khía cạnh đó;
#   3. LỆCH về "không nhắc tới" (một bên nói có nhắc, bên kia nói không): giữ quyết định của
#      ENCODER - phát hiện khía cạnh là điểm mạnh ĐÃ ĐO của encoder (macro-F1 0,967 so ~0,86 của
#      đường prompt), và đây là chỗ hai nguồn lệch nhau nhiều nhất;
#   4. THIẾU (lượt một-khía-cạnh không có ô nào, hoặc khía cạnh không có lượt riêng): giữ nhãn của
#      ENCODER và ĐẾM riêng.
# Số ô lệch được ĐẾM và in trong báo cáo: luật 3 ĐỔI kết quả, nên nó phải nhìn thấy được.
# ---------------------------------------------------------------------------------------------

TWO_TIER_LAW = {
    "khung_ô": "lấy từ lượt ENCODER (lượt đầu trong danh sách)",
    "sắc_thái": "mỗi khía cạnh lấy mã của lượt MỘT-khía-cạnh tương ứng",
    "lệch_về_không_nhắc_tới": "giữ quyết định của ENCODER (phát hiện khía cạnh là điểm mạnh đã đo "
                              "của encoder: macro-F1 0,967)",
    "thiếu_ô": "giữ nhãn của encoder và đếm riêng",
    "đơn_vị_gộp": "một lượt MỘT-khía-cạnh cho MỖI khía cạnh; cùng không gian nhãn với encoder",
}


def not_mentioned_code(run):
    """Mã nhãn của "không nhắc tới" - tra qua TÊN nhãn RỖNG của `label_map.json`.

    Không lấy hằng số 0: không gian nhãn đổi theo `label_space`, nên phải tra tên như `negative_code`.
    """
    found = [int(code) for code, name in (run["labels"] or {}).items() if str(name) == ""]
    if not found:
        raise FusionError(
            "Bảng tên nhãn không có nhãn 'không nhắc tới' (tên rỗng), nên không biết mã nào là "
            "'không nhắc tới' (labels={}).".format(run["labels"]))
    return found[0]


def merge_two_tier(encoder_run, aspect_runs, not_mentioned=None):
    """Nhãn của bản HAI TẦNG: khung ô từ `encoder_run`, sắc thái từng khía cạnh từ lượt một-khía-cạnh.

    Luật ở `TWO_TIER_LAW` (chốt TRƯỚC khi chạy): khung ô của ENCODER; sắc thái của khía cạnh lấy từ
    lượt một-khía-cạnh của CHÍNH khía cạnh đó; LỆCH về "không nhắc tới" thì giữ của ENCODER; thiếu ô
    thì giữ của encoder và ĐẾM riêng. Không trộn xác suất (`ensemble` / `ensemble_aspect` làm việc đó).

    Trả `(nhãn, đếm)`; `đếm` có số ô lấy từ mỗi lượt một-khía-cạnh, số ô LỆCH về "không nhắc tới" theo
    từng khía cạnh, và số ô thiếu. Ba con số đó là thứ duy nhất nói được luật 3 đã đổi bao nhiêu ô -
    thiếu chúng thì bản gộp chỉ còn là một con số không kiểm được.
    """
    if not aspect_runs:
        raise FusionError("Không có lượt một-khía-cạnh nào để gộp.")
    frame = encoder_run
    blank = int(not_mentioned_code(frame) if not_mentioned is None else not_mentioned)
    special = {}
    for run in aspect_runs:
        if len(run["aspects"]) != 1:
            raise FusionError(
                "Mỗi lượt một-khía-cạnh phải chấm ĐÚNG MỘT khía cạnh, nhưng '{}' chấm {} khía cạnh. "
                "Lượt nhiều khía cạnh là đường prompt thường, không dùng cho bước gộp này.".format(
                    utils.rel(run["dir"]), len(run["aspects"])))
        aspect = run["aspects"][0]
        if aspect in special:
            raise FusionError(
                "Hai lượt cùng khía cạnh '{}' ({} và {}): không biết lấy ô của lượt nào.".format(
                    aspect, utils.rel(special[aspect]["dir"]), utils.rel(run["dir"])))
        if int(not_mentioned_code(run)) != blank:
            raise FusionError(
                "Lượt '{}' dùng mã 'không nhắc tới' {} còn lượt encoder dùng {}: hai không gian nhãn "
                "khác nhau, gộp vào là đọc lệch ô.".format(utils.rel(run["dir"]),
                                                          not_mentioned_code(run), blank))
        special[aspect] = run
    missing = [aspect for aspect in frame["aspects"] if aspect not in special]
    if missing:
        raise FusionError(
            "Thiếu lượt một-khía-cạnh cho: {}. Cần đúng MỘT lượt cho mỗi khía cạnh của lượt encoder."
            .format(", ".join(missing)))
    lookup = {aspect: {sid: dict(pred).get(aspect)
                       for sid, pred in zip(run["sample_ids"], run["preds"])}
              for aspect, run in special.items()}
    preds = [dict(pred) for pred in frame["preds"]]
    counts = {"từ_một_khía_cạnh": {}, "lệch_giữ_encoder": {}, "thiếu_ô": 0}
    for position, sample_id in enumerate(frame["sample_ids"]):
        for aspect in frame["aspects"]:
            theirs = lookup[aspect].get(sample_id)
            if theirs is None:
                counts["thiếu_ô"] += 1
                continue
            mine = preds[position].get(aspect)
            if (mine == blank) != (theirs == blank):
                counts["lệch_giữ_encoder"][aspect] = counts["lệch_giữ_encoder"].get(aspect, 0) + 1
                continue
            preds[position][aspect] = theirs
            counts["từ_một_khía_cạnh"][aspect] = counts["từ_một_khía_cạnh"].get(aspect, 0) + 1
    counts["từ_một_khía_cạnh"] = dict(sorted(counts["từ_một_khía_cạnh"].items()))
    counts["lệch_giữ_encoder"] = dict(sorted(counts["lệch_giữ_encoder"].items()))
    counts["tổng_lệch"] = sum(counts["lệch_giữ_encoder"].values())
    return preds, counts






