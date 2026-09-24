# -*- coding: utf-8 -*-
"""Chấm lại kết quả đánh giá model từ FILE DỰ ĐOÁN đã lưu - không cần GPU, không chạy lại model.

Cách dùng:
    python run_rescore_eval.py                      # mọi cấu hình (n100) của phiên bản mới nhất
    python run_rescore_eval.py --version cosmetics-v0.1.0-b37ecfce
    python run_rescore_eval.py --all                # cả các tập con (n4, n8, ...) nếu còn

VÌ SAO CÓ CÔNG CỤ NÀY
---
File dự đoán lưu CẢ nhãn đúng và nhãn model đã trả lời, nên chấm điểm lại là phép tính
thuần trên dữ liệu đã có: đổi cách chấm thì KHÔNG phải chạy lại 4 cấu hình (mỗi cấu hình
10-15 phút GPU). Việc này đã dùng một lần thật: `metrics._binary_counts` bị hoán vị FP/FN,
F1 không đổi (đối xứng) nên bảng điểm vẫn "trông hợp lí" - chỉ Precision/Recall đổi chỗ.
Nhờ chấm lại từ file, 3 cấu hình đã chạy được sửa số liệu trong vài giây thay vì chạy lại.

Sau khi chấm lại, mục lục được cập nhật và ghi rõ `rescored` + lí do, để người đọc số liệu
biết con số này không phải do lần chạy model đầu tiên sinh ra.
"""

import argparse
import csv
import glob
import json
import os
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

from src import config, dataset, utils, versioning
from src.evaluation import metrics
from src.preprocessing import loader

COLUMNS = ["prompt", "split", "mẫu", "khía cạnh", "số mẫu", "đúng", "acc",
           "có nhắc tới", "acc khi có nhắc", "P nhắc", "R nhắc", "F1 nhắc"]

NOTE = ("Chấm lại bằng metrics đã sửa (trước đó hai nhánh FP/FN bị hoán vị nên cột "
        "Precision/Recall đổi chỗ cho nhau; F1 không đổi vì đối xứng)")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Chấm lại kết quả đánh giá model từ file dự đoán đã lưu (không cần GPU).")
    parser.add_argument("--dataset", default=None, help="Tên dataset (mặc định: bản đầu tiên).")
    parser.add_argument("--version", default=None, help="Mã phiên bản dữ liệu đã xử lý.")
    parser.add_argument("--all", action="store_true",
                        help="Chấm lại mọi tập con (n4, n8, ...), không chỉ tập n100.")
    parser.add_argument("--note", default=NOTE, help="Lí do chấm lại, ghi vào mục lục.")
    return parser.parse_args(argv)


def read_rows(path):
    with open(path, encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def rebuild(rows, aspects):
    """Dựng lại (nhãn đúng, nhãn đoán, thông tin đọc) từ file dự đoán."""
    golds, preds, infos = [], [], []
    for row in rows:
        gold = {aspect: int(json.loads(row["nhãn đúng"]).get(aspect, 0))
                for aspect in aspects}
        guess = {name: int(value)
                 for name, value in json.loads(row["nhãn đoán"]).items()}
        valid = row["đọc được"] == "có"
        golds.append(gold)
        preds.append(guess if valid else None)
        infos.append({
            "valid": valid,
            "reason": row["lí do"],
            "has_reasoning": row["có suy luận"] == "có",
            "had_thinking": row["có <think>"] == "có",
            "thiếu": [aspect for aspect in aspects if aspect not in guess],
        })
    return golds, preds, infos


def main(argv=None):
    args = parse_args(argv)

    try:
        ds = dataset.load_config(args.dataset)
    except dataset.DatasetError as exc:
        print("LỖI: {}".format(exc))
        return 2
    version_id = args.version or versioning.compute_id(ds, config.PIPELINE_CONFIG_PATH)
    report_dir = versioning.version_dir(config.MODEL_EVAL_REPORT_DIR, version_id)
    if not report_dir.is_dir():
        print("LỖI: chưa có {} - chạy run_qwen_eval.py trước.".format(
            utils.rel(report_dir)))
        return 2

    label_map = loader.load_label_map(version_id, dataset=ds["name"])
    aspects = list(label_map["aspects"])

    pattern = "*__greedy.csv" if args.all else "*n100__greedy.csv"
    paths = sorted(glob.glob(os.path.join(str(report_dir),
                                          "predictions__" + pattern)))
    if not paths:
        print("Không có file dự đoán nào khớp 'predictions__{}'.".format(pattern))
        return 2

    print("Chấm lại {} cấu hình (phiên bản {}):".format(len(paths), version_id))
    updated = {}
    for path in paths:
        rows = read_rows(path)
        golds, preds, infos = rebuild(rows, aspects)
        metric_rows, summary = metrics.score(golds, preds, aspects)
        read = metrics.read_rate(infos)

        metrics_path = path.replace("predictions__", "metrics__")
        old = read_rows(metrics_path)
        name = os.path.basename(path).split("predictions__")[1].split("__val")[0]
        print("  {:<34} P {:.3f} -> {:.3f} | R {:.3f} -> {:.3f}".format(
            name, float(old[0]["P nhắc"]), metric_rows[0]["P nhắc"],
            float(old[0]["R nhắc"]), metric_rows[0]["R nhắc"]))

        utils.write_csv([[name, "val", len(rows)] + [item[column]
                                                     for column in COLUMNS[3:]]
                         for item in metric_rows], COLUMNS, metrics_path)
        summary_path = path.replace("predictions__", "summary__").replace(".csv", ".json")
        with open(summary_path, encoding="utf-8") as handle:
            stored = json.load(handle)
        stored["chỉ số"] = summary
        stored["đọc kết quả"] = read
        stored["chấm lại"] = {"lúc": datetime.now().strftime("%d/%m/%Y %H:%M"),
                              "lí do": args.note}
        utils.write_json(stored, summary_path)
        updated[utils.rel(path)] = {"metrics": summary, "read": read}

    manifest = versioning.read_manifest()
    touched = 0
    for entry in manifest["entries"]:
        if entry.get("phase") != "qwen_eval":
            continue
        if entry.get("report") in updated:
            entry["metrics"] = updated[entry["report"]]["metrics"]
            entry["read"] = updated[entry["report"]]["read"]
            entry["rescored"] = args.note
            touched += 1
    utils.write_json(manifest, versioning.manifest_path())

    print("\nĐã ghi lại metrics + summary cho {} cấu hình và cập nhật {} dòng mục lục."
          .format(len(updated), touched))
    print("Ghi chú chấm lại: {}".format(args.note))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
