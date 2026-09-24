# -*- coding: utf-8 -*-
"""Chấm lại kết quả đánh giá từ FILE DỰ ĐOÁN đã lưu - không cần GPU, không chạy lại model.

Cách dùng:
    python run_rescore_eval.py                      # mọi lần chạy (greedy) của phiên bản mới nhất
    python run_rescore_eval.py --version cosmetics-ds0.1.0-pl0.1.0-srccosmetics@0.1.0-1a2b3c4d
    python run_rescore_eval.py --all                # cả các tập con (n4, n8, ...) nếu còn
    python run_rescore_eval.py --list-scorers       # đang có chỉ số nào

VÌ SAO CÓ CÔNG CỤ NÀY
File dự đoán lưu CẢ nhãn đúng và nhãn model đã trả lời, nên chấm lại là phép tính thuần trên dữ
liệu đã có: đổi cách chấm thì KHÔNG phải chạy lại model (mỗi lượt tốn 10-15 phút GPU). Việc này
đã dùng một lần thật: bộ đếm FP/FN từng bị hoán vị, F1 không đổi (đối xứng) nên bảng điểm vẫn
"trông hợp lí" - chỉ Precision/Recall đổi chỗ cho nhau. Nhờ file dự đoán, sửa lại số liệu chỉ mất
vài giây thay vì chạy lại model.

Chấm lại có thể ĐỔI SỐ khi `task` (label_space, neutral_policy) hoặc `evaluation.scores` đã đổi -
đó chính là mục đích: số liệu phải theo cách chấm hiện hành. `metrics.json` ghi lại khoá
`rescored` (lúc nào, vì sao) để người đọc biết con số không phải do lần chạy model đầu tiên sinh.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Trên Windows, console mặc định có thể không phải UTF-8 (ví dụ cp1252),
# khiến việc in tiếng Việt bị lỗi. Ép stdout/stderr sang UTF-8.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from src import config, dataset, experiments, paths, utils, versioning
from src.evaluation import metrics, records, scorers
from src.preprocessing import loader

NOTE = ("Chấm lại bằng cách chấm hiện hành (trước đó hai nhánh FP/FN bị hoán vị nên cột "
        "Precision/Recall đổi chỗ; F1 không đổi vì đối xứng)")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Chấm lại kết quả đánh giá model từ file dự đoán đã lưu (không cần GPU).")
    parser.add_argument("--dataset", default=None, help="Tên dataset (mặc định: bản đầu tiên).")
    parser.add_argument("--version", default=None, help="Mã phiên bản dữ liệu đã xử lý.")
    parser.add_argument("--all", action="store_true",
                        help="Chấm lại mọi lần chạy, kể cả tập con (n4, n8, ...).")
    parser.add_argument("--note", default=NOTE, help="Lí do chấm lại, ghi vào metrics.json.")
    parser.add_argument("--list-scorers", dest="list_scorers", action="store_true",
                        help="In các bộ chấm điểm đang có (registry SCORERS) rồi thoát.")
    return parser.parse_args(argv)



def read_rows(path):
    """Đọc file dự đoán (CSV) thành list[dict]; trả về cả tên cột."""
    frame = utils.read_csv(path)
    return frame.to_dict("records")


def rebuild(rows, aspects, task, label_map):
    """Dựng lại `scorers.Samples` từ file dự đoán: nhãn đúng, nhãn đoán, thông tin đọc.

    Dùng chung `src/evaluation/records.py` với đường chấm điểm chính (`run_qwen_eval.py`), nên
    chấm lại cho ra cùng một cách tính; khác số thì là do `task`/`evaluation` đã đổi, không phải
    do hai đường tính khác nhau.
    """
    golds, preds, infos = records.to_arrays(rows, aspects)
    samples = scorers.Samples.build(
        aspects, golds, preds, task=task, labels=label_names(label_map),
        sample_ids=[records.key_of(row) for row in rows],
        meta={"split": rows[0].get("split") if rows else None})
    return samples, infos


def label_names(label_map):
    """Bảng tên nhãn để in kết quả (mã -> tên). Khoá là số vì bảng đếm dùng mã bằng số."""
    return {int(code): name for code, name in (label_map.get("id_to_label") or {}).items()}


def is_subset(tag):
    """Tên thư mục có ghi cỡ tập con (`n100`) hay không."""
    return any(part[1:].isdigit() for part in tag.split("__") if part.startswith("n"))


def previous_payload(directory):
    """Nội dung `metrics.json` của lần chạy trước, để giữ lại thông tin của lần chạy.

    Chấm lại chỉ được đổi phần CHỈ SỐ. Thông tin như prompt, model, cách sinh phải giữ nguyên,
    nếu không thì con số mới nằm cạnh mô tả sai về lần chạy đã sinh ra nó.
    """
    path = directory / paths.pattern("metrics_json")
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as handle:
        stored = json.load(handle)
    for key in ("scores", "tables"):
        stored.pop(key, None)
    return stored


def main(argv=None):
    args = parse_args(argv)

    if args.list_scorers:
        print("Các bộ chấm điểm đang có (khai trong evaluation.scores):")
        for line in scorers.describe():
            print("  " + line)
        return 0

    try:
        ds = dataset.load_config(args.dataset)
        task = experiments.shared("task")
        evaluation = experiments.shared("evaluation")
        names = scorers.check(evaluation.get("scores"))
    except (dataset.DatasetError, experiments.ExperimentError, scorers.ScorerError) as exc:
        print("LỖI: {}".format(exc))
        return 2

    version_id = args.version or versioning.compute_id(ds)
    root = config.MODEL_EVAL_REPORT_DIR / version_id
    if not root.is_dir():
        print("LỖI: chưa có {} - chạy run_qwen_eval.py trước.".format(utils.rel(root)))
        return 2

    prediction_name = paths.pattern("predictions")
    runs = sorted(path.parent for path in root.glob("*/" + prediction_name))
    if not args.all:
        runs = [path for path in runs if not is_subset(path.name)]
    if not runs:
        print("Không có lần chạy nào có {} trong {}.".format(
            prediction_name, utils.rel(root)))
        return 2

    try:
        label_map = loader.load_label_map(version_id, dataset=ds["name"])
        label_map = labels.filter_label_map(label_map, task["label_space"],
                                            task["neutral_policy"])
        aspects = labels.task_aspects(task, label_map["aspects"])
    except (FileNotFoundError, labels.base.LabelError) as exc:
        print("LỖI: {}".format(exc))
        return 2

    save = dict(evaluation.get("save") or {})
    print("Chấm lại {} lần chạy (phiên bản {}), không cần GPU:".format(len(runs), version_id))
    print("  bài toán : label_space {}, neutral_policy {} ({} ô neutral bị loại)".format(
        task["label_space"], task["neutral_policy"], "(đếm khi chấm)"))
    print("  chỉ số   : {}".format(", ".join(names)))

    for directory in runs:
        rows = read_rows(directory / prediction_name)
        samples, infos = rebuild(rows, aspects, task, label_map)
        result = scorers.run_all(samples, names=names)
        read = metrics.read_rate(infos)

        before = previous_payload(directory)
        extra = dict(before)
        extra["read_rate"] = read
        extra["rescored"] = {"at": datetime.now().strftime("%d/%m/%Y %H:%M"),
                             "why": args.note}
        scorers.write(directory, samples, names=names,
                      save_confusion=bool(save.get("confusion", True)), extra=extra)

        accuracy = result["scores"].get("accuracy") or {}
        previous = (before.get("scores") or {})
        old_accuracy = (previous.get("accuracy") or {}).get("macro")
        print("  {:<52} accuracy macro {} -> {} | {} ô neutral bị loại".format(
            directory.name[:52], old_accuracy, accuracy.get("macro"),
            samples.meta["dropped_neutral"]))

    print("\nĐã ghi lại {} + {} + {} cho {} lần chạy.".format(
        paths.pattern("metrics_json"), paths.pattern("metrics_csv"),
        paths.pattern("mispredictions"), len(runs)))
    print("Ghi chú chấm lại: {}".format(args.note))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

