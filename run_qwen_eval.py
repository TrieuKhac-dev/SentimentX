# -*- coding: utf-8 -*-
"""Chạy Qwen3 bằng CHỈ DẪN (prompt một lượt / CoT) rồi chấm điểm (đánh giá model).

Cách dùng:
    python run_qwen_eval.py --dataset cosmetics --split val
    python run_qwen_eval.py --split val --prompt absa_direct_v1
    python run_qwen_eval.py --split val --prompt absa_cot_v1 --limit 200
    python run_qwen_eval.py --split val --prompt absa_cot_v1 --limit 200 --sample

VÌ SAO PHẢI CHẠY TRÊN VAL TRƯỚC
---
`val` là tập để LỰA CHỌN (prompt nào, ngưỡng nào, bao nhiêu ví dụ). Chạy test từ đầu rồi
chọn theo test là tự lừa mình: mọi con số trên test sau đó mất ý nghĩa so sánh. Vì vậy mặc
định của script là `val`, và muốn chạy test phải gõ tay `--split test` (khi đó kết quả được
ghi vào file riêng, không ghi đè kết quả val).

VÌ SAO CÓ `--limit`
---
Máy đang dùng có GPU 6 GB (phải lượng hóa 4-bit), nên một lượt val đầy đủ (1.524 review,
prompt CoT sinh ~250 token/mẫu) tốn khoảng một giờ. `--limit N` chạy trên một TẬP CON chọn
bằng `random.Random(seed)` (tái lập được), và tên file ghi rõ `n<N>` - không bao giờ lẫn
kết quả tập con với kết quả toàn tập.
"""

import argparse
import random
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Trên Windows, console mặc định có thể không phải UTF-8 (ví dụ cp1252),
# khiến việc in tiếng Việt bị lỗi. Ép stdout/stderr sang UTF-8.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from src import config, dataset, prompts, utils, versioning
from src.evaluation import metrics, runner
from src.preprocessing import loader, qwen

# Cột của file chỉ số theo khía cạnh (mỗi lần chạy một file)
METRIC_COLUMNS = ["prompt", "split", "mẫu", "khía cạnh", "số mẫu", "đúng", "acc",
                  "có nhắc tới", "acc khi có nhắc", "P nhắc", "R nhắc", "F1 nhắc"]

# Cấu hình lấy mẫu theo khuyến nghị trong model card của Qwen3-4B-Instruct-2507
# (Temperature=0.7, TopP=0.8, TopK=20). Chỉ dùng khi chạy `--sample`.
CARD_SETTINGS = {"temperature": 0.7, "top_p": 0.8, "top_k": 20}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Chạy Qwen3 bằng chỉ dẫn (prompt/CoT) trên một split rồi chấm điểm.")
    parser.add_argument("--dataset", default=None,
                        help="Tên dataset (mặc định: dataset đầu tiên trong configs/datasets/).")
    parser.add_argument("--version", default=None,
                        help="Mã phiên bản dữ liệu đã xử lý (mặc định: bản mới nhất).")
    parser.add_argument("--split", default="val", choices=["val", "test", "train"],
                        help="Tập để chạy. Mặc định 'val' - tập LỰA CHỌN, không phải test.")
    parser.add_argument("--prompt", required=True,
                        help="Tên prompt. Bắt buộc: prompt thuộc config của thí nghiệm, "
                             "không lấy từ config model.")
    parser.add_argument("--model", default=None,
                        help="Ghi đè tên model trên Hugging Face (mặc định: "
                             "Qwen/Qwen3-4B-Instruct-2507 trong src/preprocessing/qwen.py). "
                             "Dùng để chạy thử đường ống bằng một model nhỏ cùng họ trước "
                             "khi tải model 4B.")
    parser.add_argument("--limit", type=int, default=0, metavar="N",
                        help="Chạy trên một tập con N mẫu lấy NGẪU NHIÊN (dùng --seed để "
                             "tái lập); 0 = cả split. Tên file ghi rõ n<N> để không lẫn "
                             "với kết quả toàn tập.")
    parser.add_argument("--seed", type=int, default=42,
                        help="Seed chọn tập con và lấy mẫu (ghi vào kết quả).")
    parser.add_argument("--batch-size", dest="batch_size", type=int, default=4,
                        help="Số review mỗi lô (mặc định 4; tăng lên nếu VRAM còn chỗ).")
    parser.add_argument("--max-new-tokens", dest="max_new_tokens", type=int,
                        default=runner.DEFAULT_MAX_NEW_TOKENS,
                        help="Số token tối đa model được sinh cho mỗi review.")
    parser.add_argument("--max-length", dest="max_length", type=int, default=None,
                        help="Ngưỡng cắt input (mặc định: lấy từ qwen.limit()).")
    parser.add_argument("--quant", default="auto", choices=["auto", "4bit", "bf16"],
                        help="Cách nạp model: 4-bit (nhẹ VRAM) | bf16 | auto.")
    parser.add_argument("--sample", action="store_true",
                        help="Lấy mẫu theo khuyến nghị của model card (nhiệt độ 0.7, top_p "
                             "0.8, top_k 20) thay vì greedy. Khi đó `seed` được ghi lại.")
    parser.add_argument("--quiet", action="store_true",
                        help="Không in tiến độ từng lô (vẫn in bảng kết quả).")
    return parser.parse_args(argv)



def print_table(rows, columns):
    """In bảng ra console, cột căn trái theo nội dung."""
    if not rows:
        print("  (không có số liệu)")
        return
    widths = [
        max(len(str(value)) for value in [columns[index]] + [row[index] for row in rows])
        for index in range(len(columns))
    ]
    def line(values):
        return "  " + "  ".join(
            "{:<{}}".format(str(values[index]), widths[index])
            for index in range(len(columns)))
    print(line(columns))
    print("  " + "  ".join("-" * width for width in widths))
    for row in rows:
        print(line(row))


def build_tag(prompt, split, limit, generation, quant, extra=None):
    """Hậu tố tên file: ghi rõ lần chạy này là cấu hình nào.

    Mọi thứ ảnh hưởng tới con số đều phải có trong tên file: prompt (+ sha của bộ ví dụ),
    split, CỠ TẬP CON (`n200`), cách sinh (greedy/lấy mẫu) và mức lượng hóa. Nhờ vậy không
    bao giờ lẫn kết quả của tập con với toàn tập, hay kết quả greedy với lấy mẫu.
    """
    parts = ["prompt-{}".format(prompt.name)]
    info = prompts.examples_info(prompt.name)
    if info and info["sha"]:
        parts.append("ex-{}".format(info["sha"]))
    parts.append(split)
    if limit:
        parts.append("n{}".format(limit))
    parts.append("sample" if generation["do_sample"] else "greedy")
    if quant and quant != "auto":
        parts.append(quant)
    if extra:
        parts.append(extra)
    return "__".join(parts)


def print_config(prompt, examples, split, limit, total, max_length, generation, model_info):
    """In cấu hình chạy, để người đọc biết bảng điểm dưới đây ứng với cái gì."""
    print("Cấu hình chạy:")
    print("  prompt      : {} ({}), sha {}".format(
        prompt.name, prompt.where, prompt.sha))
    print("  ví dụ       : {}".format(
        "{} - {} ví dụ, sha {}".format(examples["file"], examples["examples"],
                                       examples["sha"]) if examples else "không dùng"))
    print("  tập dữ liệu : {} - {}{}".format(
        split, limit if limit else total,
        " (TẬP CON ngẫu nhiên, seed ở mục lục)" if limit and limit < total else ""))
    print("  ngưỡng cắt  : {} token (max_length của Qwen)".format(max_length))
    print("  sinh        : {}".format(
        "greedy (tái lập)" if not generation["do_sample"] else
        "lấy mẫu: temperature={}, top_p={}, top_k={}, seed={}".format(
            generation["temperature"], generation["top_p"], generation["top_k"],
            generation["seed"])))
    print("  tối đa sinh : {} token/review".format(generation["max_new_tokens"]))
    print("  model       : {} - {}, {}, {}".format(
        model_info["model"], model_info.get("quant"),
        model_info.get("cách nạp"), model_info.get("thiết bị")))
    print()


def main(argv=None):
    args = parse_args(argv)

    print("=" * 70)
    print("QWEN3 BẰNG CHỈ DẪN - chạy model rồi chấm điểm (đánh giá model)")
    print("=" * 70)

    try:
        ds = dataset.load_config(args.dataset)
    except dataset.DatasetError as exc:
        print("LỖI: {}".format(exc))
        return 2
    version_id = args.version or versioning.compute_id(ds)

    try:
        prompt = qwen.load_prompt(args.prompt)
    except prompts.PromptError as exc:
        print("LỖI: {}".format(exc))
        return 2

    try:
        label_map = loader.load_label_map(version_id, dataset=ds["name"])
        frame = loader.load_processed(args.split, version_id=version_id,
                                      dataset=ds["name"])
    except FileNotFoundError as exc:
        print("LỖI: {}".format(exc))
        return 2

    aspects = list(label_map["aspects"])
    texts = frame[config.TEXT_COLUMN].astype(str).tolist()
    codes = frame[aspects].astype(int).to_numpy().tolist()
    golds = [dict(zip(aspects, row)) for row in codes]

    # Tập con (nếu có): chọn bằng random CÓ SEED để tái lập được, và giữ lại chỉ số dòng
    # gốc - không có nó thì không tra ngược được kết quả về review nào trong file dữ liệu.
    row_index = list(range(len(texts)))
    if args.limit and args.limit < len(texts):
        row_index = sorted(random.Random(args.seed).sample(row_index, args.limit))
        texts = [texts[index] for index in row_index]
        golds = [golds[index] for index in row_index]

    generation = runner.settings(
        quant=args.quant, max_new_tokens=args.max_new_tokens, do_sample=args.sample,
        temperature=CARD_SETTINGS["temperature"] if args.sample else None,
        top_p=CARD_SETTINGS["top_p"] if args.sample else None,
        top_k=CARD_SETTINGS["top_k"] if args.sample else None,
        seed=args.seed if args.sample else None)
    max_length = args.max_length or qwen.limit()[0]

    if args.split == "test":
        print("LƯU Ý: đang chạy trên TEST. Tập này chỉ dùng cho con số CUỐI CÙNG, sau khi đã")
        print("       chốt prompt và ngưỡng trên val - chọn theo test là tự lừa mình.\n")

    try:
        model, tokenizer, model_info = runner.load(args.quant, model_name=args.model)
    except (ImportError, RuntimeError, OSError) as exc:
        print("LỖI: {}".format(exc))
        return 2

    examples = prompts.examples_info(prompt.name)
    print_config(prompt, examples, args.split, args.limit, len(texts), max_length,
                 generation, model_info)
    print("Đang sinh...")

    rows, infos, preds, meta = runner.run(
        args.split, texts, golds, aspects, label_map, prompt.name, model, tokenizer,
        batch_size=args.batch_size, max_length=max_length, generation=generation,
        row_index=row_index, quiet=args.quiet)

    metric_rows, summary = metrics.score(golds, preds, aspects)
    read = metrics.read_rate(infos)

    print("\nĐọc kết quả:")
    for key, value in read.items():
        if key != "lí do lỗi":
            print("  {:<18}: {}".format(key, value))
    for reason, count in read["lí do lỗi"].items():
        print("      lỗi: {:<44} {}".format(reason, count))

    print("\nTheo khía cạnh:")
    print_table([[row[column] for column in METRIC_COLUMNS[3:]] for row in metric_rows],
                METRIC_COLUMNS[3:])
    print("\nTổng hợp:")
    for key, value in summary.items():
        print("  {:<18}: {}".format(key, value))
    print("\nChi phí: {} token sinh/review TB, {} giây, {} token sinh/giây".format(
        meta["token sinh TB"], meta["giây"], meta["token sinh/giây"]))
    return _write_all(args, ds, version_id, prompt, examples, generation, max_length,
                      model_info, rows, metric_rows, summary, read, meta)


def _write_all(args, ds, version_id, prompt, examples, generation, max_length,
               model_info, rows, metric_rows, summary, read, meta):
    """Ghi 3 file kết quả (dự đoán, chỉ số, tổng hợp) + một dòng vào mục lục."""
    tag = build_tag(prompt, args.split, args.limit, generation, args.quant)
    paths = {}
    paths["dự đoán"] = runner.write(rows, runner.PREDICTION_COLUMNS, version_id, tag)
    metric_file_rows = [
        [prompt.name, args.split, meta["số mẫu"]]
        + [row[column] for column in METRIC_COLUMNS[3:]]
        for row in metric_rows
    ]
    paths["chỉ số"] = runner.write(metric_file_rows, METRIC_COLUMNS, version_id, tag,
                                   kind="metrics")
    summary_path = paths["dự đoán"].parent / "summary__{}.json".format(tag)
    utils.write_json({
        "prompt": prompt.name,
        "prompt_sha": prompt.sha,
        "prompt_examples": examples,
        "dataset": ds["name"],
        "version_id": version_id,
        "split": args.split,
        "tập con": {"limit": args.limit, "seed": args.seed,
                    "cách chọn": "random.Random(seed).sample trên split, giữ chỉ số dòng gốc"},
        "model": model_info,
        "max_length": max_length,
        "sinh": generation,
        "đọc kết quả": read,
        "chỉ số": summary,
        "chi phí": meta,
    }, summary_path)
    paths["tổng hợp"] = summary_path

    print("Hoàn tất. Đã ghi:")
    for kind, path in paths.items():
        print("  - {:<10} {}".format(kind, utils.rel(path)))
    print("  (hậu tố tên file '{}' ghi rõ cấu hình - số liệu của lần chạy khác không bị "
          "ghi đè)".format(tag))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

