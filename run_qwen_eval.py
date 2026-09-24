# -*- coding: utf-8 -*-
"""Chạy Qwen3 bằng CHỈ DẪN (prompt một lượt / CoT) rồi chấm điểm (đánh giá model).

Cách dùng:
    python run_qwen_eval.py --list-scorers          # đang có chỉ số nào
    python run_qwen_eval.py --dataset cosmetics --split val
    python run_qwen_eval.py --split val --prompt absa_direct_v1
    python run_qwen_eval.py --split val --prompt absa_cot_v1 --limit 200
    python run_qwen_eval.py --split val --prompt absa_cot_v1 --limit 200 --sample

Một lần chạy ghi vào MỘT thư mục riêng (`<phiên bản>/<hậu tố cấu hình>/`): `predictions.csv`,
`metrics.json`, `metrics.csv`, `mispredictions.csv`. Tên file cố định, đọc từ
`configs/paths.yaml`; cấu hình nằm ở tên THƯ MỤC nên hai lần chạy không ghi đè nhau.

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

from src import config, dataset, experiments, labels, paths, prompts, runlog, utils, versioning
from src.evaluation import metrics, runner, scorers
from src.preprocessing import loader, qwen

# Cột của file chỉ số do `src/evaluation/scorers/` quyết định (bảng dài: aspect, sentiment,
# metric, value) - không khai lại ở đây, để không có hai nguồn sự thật cho cùng một bảng.

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
    parser.add_argument("--prompt", default=None,
                        help="Tên prompt. Bắt buộc khi chạy: prompt thuộc config của thí "
                             "nghiệm, không lấy từ config model.")
    parser.add_argument("--list-scorers", dest="list_scorers", action="store_true",
                        help="In các bộ chấm điểm đang có (registry SCORERS) rồi thoát.")
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


def task_settings():
    """Cách nhìn bài toán đang dùng, lấy từ `configs/experiments/task.yaml`.

    Không chép giá trị mặc định vào đây: chép thì sửa config mà kết quả không đổi, và người đọc
    số liệu sẽ tưởng đang đo một bài toán khác với bài toán đã khai.
    """
    return experiments.shared("task")


def evaluation_settings():
    """Cách chấm điểm đang dùng, lấy từ `configs/experiments/evaluation.yaml`."""
    return experiments.shared("evaluation")


def label_names(label_map):
    """Bảng tên nhãn để in kết quả (mã -> tên). Khoá là số vì bảng đếm dùng mã bằng số."""
    return {int(code): name for code, name in (label_map.get("id_to_label") or {}).items()}


def print_scores(scores):
    """In các con số tổng hợp của từng bộ chấm. Bảng chi tiết in bằng `scorers.table`."""
    for name, values in scores.items():
        print("  {}".format(name))
        for key, value in values.items():
            if isinstance(value, dict):
                flat = "  ".join("{}={}".format(inner, item) for inner, item in value.items()
                                 if isinstance(item, (int, float, str)))
                if flat:
                    print("    {:<20} {}".format(key, flat))
            else:
                print("    {:<20} {}".format(key, value))


def main(argv=None):
    args = parse_args(argv)

    if args.list_scorers:
        print("Các bộ chấm điểm đang có (khai trong evaluation.scores):")
        for line in scorers.describe():
            print("  " + line)
        return 0

    print("=" * 70)
    print("QWEN3 BẰNG CHỈ DẪN - chạy model rồi chấm điểm (đánh giá model)")
    print("=" * 70)

    if not args.prompt:
        print("LỖI: thiếu --prompt. Prompt thuộc config của thí nghiệm, không lấy từ config "
              "model. Xem `run_token_stats.py --list-prompts` để biết đang có prompt nào.")
        return 2

    try:
        ds = dataset.load_config(args.dataset)
        task = task_settings()
        evaluation = evaluation_settings()
        names = scorers.check(evaluation.get("scores"))
    except (dataset.DatasetError, experiments.ExperimentError, scorers.ScorerError) as exc:
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
        # Lọc bảng mã nhãn theo không gian nhãn TRƯỚC khi đưa cho model: đưa một nhãn mà bài
        # toán không dùng là mọi câu trả lời mang nhãn đó đều bị tính sai.
        label_map = labels.filter_label_map(label_map, task["label_space"],
                                            task["neutral_policy"])
        aspects = labels.task_aspects(task, label_map["aspects"])
    except (FileNotFoundError, experiments.ExperimentError, labels.base.LabelError) as exc:
        print("LỖI: {}".format(exc))
        return 2

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

    # Một thư mục kết quả cho MỘT cấu hình chạy: log, chỉ số và bản ghi lần chạy nằm cạnh nhau.
    # Dựng thư mục và mở log TRƯỚC khi nạp model - nạp model hỏng là trường hợp hay gặp nhất
    # (thiếu bitsandbytes, hết VRAM), nên phải có chỗ ghi lại ngay.
    tag = build_tag(prompt, args.split, args.limit, generation, args.quant)
    out_dir = runner.run_dir(version_id, tag)
    info = {
        "dataset": ds["name"], "version_id": version_id, "split": args.split,
        "prompt": prompt.name, "prompt_sha": prompt.sha,
        "model": args.model or qwen.MODEL_NAME, "quant": args.quant,
        "max_length": max_length, "generation": generation,
        "subset": {"limit": args.limit, "seed": args.seed}, "n_samples": len(texts),
    }

    with runlog.start(out_dir, mode="NEW", info=info) as log:
        log.step("nạp model: {} (quant={})".format(info["model"], args.quant))
        try:
            model, tokenizer, model_info = runner.load(args.quant, model_name=args.model)
        except (ImportError, RuntimeError, OSError) as exc:
            # `requires` là thứ còn thiếu để chạy được, để lần sau không phải đoán.
            log.error("Không nạp được model: {}".format(exc), exc=exc,
                      context={"model": info["model"], "quant": args.quant},
                      requires=["bitsandbytes + accelerate (lượng hóa 4-bit)",
                                "VRAM trống đủ cho model 4B"])
            print("LỖI: {}".format(exc))
            return 2
        log.step("đã nạp model: {}, {}".format(
            model_info.get("quant"), model_info.get("cách nạp")), seconds=log.elapsed())

        examples = prompts.examples_info(prompt.name)
        print_config(prompt, examples, args.split, args.limit, len(texts), max_length,
                     generation, model_info)
        print("Đang sinh...")
        log.step("bắt đầu sinh {} mẫu của split {} (batch {})".format(
            len(texts), args.split, args.batch_size))

        rows, infos, preds, meta = runner.run(
            args.split, texts, golds, aspects, label_map, prompt.name, model, tokenizer,
            batch_size=args.batch_size, max_length=max_length, generation=generation,
            row_index=row_index, quiet=args.quiet)
        log.step("sinh xong {} mẫu".format(len(rows)), seconds=meta["giây"])

        read = metrics.read_rate(infos)
        log.step("đọc được {}% kết quả ({} mẫu không đọc được)".format(
            read["% đọc được"], read["tổng"] - read["đọc được"]))
        samples = scorers.Samples.build(
            aspects, golds, preds, task=task, labels=label_names(label_map),
            sample_ids=[str(index) for index in row_index],
            meta={"split": args.split, "dataset": ds["name"], "version_id": version_id})
        result = scorers.run_all(samples, names=names)
        log.step("chấm xong {} chỉ số: {}".format(len(names), ", ".join(names)))
        if samples.meta["dropped_neutral"]:
            log.step("loại {} ô neutral theo neutral_policy={}".format(
                samples.meta["dropped_neutral"], task["neutral_policy"]))

        print("\nĐọc kết quả:")
        for key, value in read.items():
            if key != "lí do lỗi":
                print("  {:<18}: {}".format(key, value))
        for reason, count in read["lí do lỗi"].items():
            print("      lỗi: {:<44} {}".format(reason, count))

        print("\nSố theo khía cạnh và sắc thái:")
        table_rows, table_columns = scorers.table(result["rows"])
        print_table(table_rows, table_columns)
        print("\nTổng hợp:")
        print_scores(result["scores"])
        print("\nChi phí: {} token sinh/review TB, {} giây, {} token sinh/giây".format(
            meta["token sinh TB"], meta["giây"], meta["token sinh/giây"]))

        extra = dict(info)
        extra.update({
            "prompt_examples": examples,
            "model_info": model_info,
            "subset": {"limit": args.limit, "seed": args.seed,
                       "how": "random.Random(seed).sample trên split, giữ chỉ số dòng gốc"},
            "read_rate": read,
            "cost": meta,
            "scores_order": result["names"],
        })
        return _write_all(out_dir, tag, rows, samples, result, evaluation, extra, log)


def _write_all(out_dir, tag, rows, samples, result, evaluation, extra, log):
    """Ghi kết quả của lần chạy vào thư mục riêng của nó. Trả về mã thoát.

    Thư mục riêng cho mỗi cấu hình nên tên file TRONG đó là tên cố định; cấu hình nằm ở tên thư
    mục. Nhờ vậy không bao giờ ghi đè số liệu của lần chạy khác, và cũng không phải ghép tên file
    từ cấu hình (ghép chuỗi là nguồn sự thật thứ hai, lệch lúc nào không biết).
    """
    save = dict(evaluation.get("save") or {})
    shown = {}
    if save.get("predictions", True):
        shown[paths.pattern("predictions")] = runner.write(
            rows, runner.PREDICTION_COLUMNS, out_dir)
        log.step("ghi {} dòng dự đoán".format(len(rows)))
    shown.update(scorers.write(out_dir, samples, names=result["names"],
                               save_confusion=bool(save.get("confusion", True)),
                               extra=extra))
    log.step("đã ghi: {}".format(", ".join(sorted(shown))))

    print("Hoàn tất. Đã ghi vào {}:".format(utils.rel(out_dir)))
    for name, path in shown.items():
        print("  - {:<18} {}".format(name, utils.rel(path)))
    print("  (tên thư mục '{}' ghi rõ cấu hình của lần chạy này)".format(tag))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

