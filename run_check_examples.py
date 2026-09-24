# -*- coding: utf-8 -*-
"""Kiểm tra file ví dụ few-shot: cấu trúc, nhãn, và RÒ RỈ với val/test.

Cách dùng:
    python run_check_examples.py                       # kiểm mọi prompt có file ví dụ
    python run_check_examples.py --prompt absa_cot_v1
    python run_check_examples.py --max-overlap 5        # siết ngưỡng cảnh báo

VÌ SAO CẦN PHÉP KIỂM NÀY
---
Ví dụ few-shot nằm TRONG PROMPT, nghĩa là model ĐÃ NHÌN THẤY chúng. Nếu một ví dụ trùng
với câu trong val/test thì điểm đánh giá bị thổi lên mà nhìn vào bảng điểm không thể biết
- không có phép kiểm này thì đó là một giả định, không phải một sự thật đã đo. Ví dụ lấy
TỪ DỮ LIỆU chỉ được phép lấy từ split train (lấy từ val/test là rò rỉ).

KIỂM NHỮNG GÌ
---
1. Cấu trúc: mỗi ví dụ phải có dòng "Review:" và một khối "KẾT QUẢ:" chứa JSON hợp lệ.
2. Nhãn  : khoá JSON phải ĐÚNG bằng bộ khía cạnh trong label_map.json, và mọi mã phải có
           trong bảng nhãn - ví dụ sai khoá/mã là prompt dạy sai định dạng ngay từ đầu.
3. Trùng lặp: câu ví dụ (so theo TỪ đã chuẩn hoá) đối chiếu CẢ 3 split đã xử lý:
   trùng nguyên câu, và cụm trùng dài nhất (mặc định dò tới 8 từ).

Kết quả: mã thoát 1 khi có lỗi (cấu trúc/nhãn, hoặc ví dụ trùng nguyên câu trong val/test,
hoặc cụm trùng >= --max-overlap trong val/test) để dùng được trong kiểm tra tự động.
"""

import argparse
import json
import re
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
from src.preprocessing import loader

SPLITS = ("train", "val", "test")

# Các độ dài cụm sẽ dò khi tìm "cụm trùng dài nhất" (từ dài xuống ngắn)
NGRAM_SIZES = (8, 6, 4, 3)

_REVIEW_RE = re.compile(r"^Review:\s*(.*)$")
_RESULT_RE = re.compile(r"^\s*KẾT QUẢ:\s*$")
_BLOCK_RE = re.compile(r"^\s*---.*---\s*$")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Kiểm cấu trúc + rò rỉ dữ liệu của các file ví dụ few-shot."
    )
    parser.add_argument(
        "--dataset", default=None,
        help="Tên dataset (mặc định: dataset đầu tiên trong configs/datasets/).",
    )
    parser.add_argument(
        "--version", default=None,
        help="Mã phiên bản dữ liệu đã xử lý (mặc định: bản mới nhất).",
    )
    parser.add_argument(
        "--prompt", default=None,
        help="Chỉ kiểm một prompt (mặc định: mọi prompt có ô nhớ {examples}).",
    )
    parser.add_argument(
        "--max-overlap", dest="max_overlap", type=int, default=6, metavar="N",
        help="Cụm trùng dài từ N từ trở lên trong val/test bị coi là RÒ RỈ (mặc định 6).",
    )
    return parser.parse_args(argv)


def split_blocks(body):
    """Tách phần hiệu lực của file ví dụ thành từng ví dụ: [(tiêu đề, các dòng)]."""
    blocks, current = [], None
    for line in body.split("\n"):
        if _BLOCK_RE.match(line):
            if current is not None:
                blocks.append(current)
            current = (line.strip(), [])
            continue
        if current is not None:
            current[1].append(line)
    if current is not None:
        blocks.append(current)
    return blocks


def parse_block(title, lines):
    """Lấy (câu review, object JSON kết quả) của MỘT ví dụ.

    Trả về (None, None) khi không tìm thấy - nơi gọi báo lỗi cấu trúc. Phần JSON lấy đúng
    dòng đầu tiên KHÔNG RỖNG sau dòng "KẾT QUẢ:" (đó là cách prompt yêu cầu model trả lời,
    nên ví dụ phải làm gương đúng như vậy).
    """
    review, payload, seen_result = None, None, False
    for line in lines:
        match = _REVIEW_RE.match(line)
        if match and review is None:
            review = match.group(1).strip().strip('"').strip()
            continue
        if _RESULT_RE.match(line):
            seen_result = True
            continue
        if seen_result and line.strip():
            payload = line.strip()
            break
    return review, payload


def words(text):
    """Chuỗi TỪ của một câu, dùng cùng định nghĩa "từ" với EDA (utils.tokenize)."""
    return utils.tokenize(utils.normalize_unicode(text))


def ngrams(tokens, size):
    return {tuple(tokens[index:index + size]) for index in range(len(tokens) - size + 1)}


def build_split_index(frames):
    """Chỉ mục của 3 split: câu đã chuẩn hoá, và các tập cụm theo độ dài đang dò."""
    index = {}
    for name, frame in frames.items():
        texts = frame[config.TEXT_COLUMN].astype(str).tolist()
        token_rows = [words(text) for text in texts]
        index[name] = {
            "số câu": len(token_rows),
            "câu": {" ".join(tokens) for tokens in token_rows if tokens},
            "cụm": {
                size: {gram for tokens in token_rows for gram in ngrams(tokens, size)}
                for size in NGRAM_SIZES
            },
        }
    return index


def compare(tokens, index):
    """So một ví dụ với chỉ mục 3 split: (trùng nguyên câu?, cụm trùng dài nhất)."""
    sentence = " ".join(tokens)
    result = {}
    for name, data in index.items():
        longest, found = 0, None
        for size in sorted(NGRAM_SIZES, reverse=True):
            if len(tokens) < size:
                continue
            hits = ngrams(tokens, size) & data["cụm"][size]
            if hits:
                longest, found = size, " ".join(sorted(hits)[0])
                break
        result[name] = {
            "trùng câu": bool(sentence) and sentence in data["câu"],
            "cụm": longest,
            "ví dụ cụm": found,
        }
    return result



def check_prompt(name, label_map, index, max_overlap):
    """Kiểm MỘT prompt: cấu trúc + nhãn + trùng lặp. Trả về (dòng bảng, lỗi, cảnh báo)."""
    aspects = set(label_map["aspects"])
    codes = {int(value) for value in label_map["label_to_id"].values()}
    rows, problems, warnings = [], [], []

    prompt = prompts.load(name)
    if "examples" not in prompt.placeholders:
        return rows, problems, warnings
    info = prompts.examples_info(prompt.examples_value)
    if info["missing"]:
        return rows, ["{}: prompt cần {{examples}} mà chưa có file ví dụ {}".format(
            name, info["file"])], warnings

    blocks = split_blocks(prompts.examples(prompt.examples_value))
    if not blocks:
        return rows, ["{}: file ví dụ {} không có khối '--- Ví dụ n ---' nào".format(
            name, info["file"])], warnings

    for title, lines in blocks:
        review, payload = parse_block(title, lines)
        notes = []
        if not review:
            problems.append("{} / {}: thiếu dòng 'Review:'".format(name, title))
            notes.append("lỗi cấu trúc")
        if payload is None:
            problems.append("{} / {}: thiếu khối 'KẾT QUẢ:' với JSON".format(name, title))
            notes.append("lỗi cấu trúc")
        else:
            try:
                parsed = json.loads(payload)
            except ValueError as exc:
                problems.append("{} / {}: JSON ở khối KẾT QUẢ không hợp lệ ({})".format(
                    name, title, exc))
                notes.append("lỗi cấu trúc")
                parsed = None
            if parsed is not None and not isinstance(parsed, dict):
                problems.append("{} / {}: khối KẾT QUẢ phải là object JSON".format(
                    name, title))
                notes.append("lỗi cấu trúc")
            elif parsed is not None:
                missing = aspects - set(parsed)
                extra = set(parsed) - aspects
                if missing:
                    problems.append("{} / {}: thiếu khía cạnh {}".format(
                        name, title, ", ".join(sorted(missing))))
                if extra:
                    problems.append("{} / {}: khía cạnh lạ {}".format(
                        name, title, ", ".join(sorted(extra))))
                bad = {key: value for key, value in parsed.items()
                       if not isinstance(value, int) or value not in codes}
                if bad:
                    problems.append("{} / {}: mã không hợp lệ {}".format(
                        name, title, bad))

        tokens = words(review or "")
        hits = compare(tokens, index) if tokens else {}
        exact = [split for split in SPLITS if hits.get(split, {}).get("trùng câu")]
        grams = {split: hits.get(split, {}).get("cụm", 0) for split in SPLITS}
        eval_gram = max(grams["val"], grams["test"])
        # In ra CHÍNH cụm bị trùng: một cảnh báo không kèm cụm cụ thể thì không sửa được,
        # và người đọc buộc phải tin thay vì kiểm.
        matched = "; ".join(
            "{}: {}".format(split, hits[split]["ví dụ cụm"])
            for split in ("val", "test")
            if hits.get(split, {}).get("ví dụ cụm")
        )

        if exact and set(exact) & {"val", "test"}:
            problems.append("{} / {}: RÒ RỈ - câu ví dụ có nguyên văn trong {}".format(
                name, title, ", ".join(exact)))
            notes.append("RÒ RỈ")
        elif eval_gram >= max_overlap:
            problems.append("{} / {}: RÒ RỈ - cụm {} từ trùng với val/test".format(
                name, title, eval_gram))
            notes.append("RÒ RỈ")
        elif grams["train"] >= max_overlap or eval_gram:
            warnings.append("{} / {}: trùng cụm với dữ liệu (train {}, val/test {})".format(
                name, title, grams["train"], eval_gram))
            notes.append("lưu ý")

        rows.append([
            name, title, len(tokens),
            ", ".join(exact) or "-",
            "{} từ".format(grams["train"]) if grams["train"] else "-",
            "{} từ".format(eval_gram) if eval_gram else "-",
            matched or "-",
            "; ".join(notes) or "OK",
        ])
    return rows, problems, warnings


def print_table(rows, columns):
    """In bảng ra console, cột căn trái theo nội dung."""
    if not rows:
        print("  (không có gì để in)")
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


def main(argv=None):
    args = parse_args(argv)

    print("=" * 70)
    print("KIỂM VÍ DỤ FEW-SHOT - cấu trúc, nhãn, rò rỉ với val/test")
    print("=" * 70)

    try:
        ds = dataset.load_config(args.dataset)
    except dataset.DatasetError as exc:
        print("LỖI: {}".format(exc))
        return 2
    version_id = args.version or versioning.compute_id(ds)

    try:
        label_map = loader.load_label_map(version_id, dataset=ds["name"])
    except FileNotFoundError as exc:
        print("LỖI: {}".format(exc))
        return 2

    if args.prompt:
        names = [args.prompt]
    else:
        names = [name for name in prompts.available()
                 if "examples" in prompts.load(name).placeholders]
    if not names:
        print("Không có prompt nào dùng ô nhớ {{examples}} - không có gì để kiểm.")
        return 0

    frames = {
        split: loader.load_processed(split, version_id=version_id, dataset=ds["name"])
        for split in SPLITS
    }
    index = build_split_index(frames)

    print("Dataset  : {} (phiên bản dữ liệu: {})".format(ds["name"], version_id))
    print("Đối chiếu: câu đã chuẩn hoá theo TỪ (utils.tokenize) với 3 split đã xử lý.\n")

    columns = ["prompt", "ví dụ", "số từ", "trùng câu", "cụm (train)", "cụm (val/test)",
               "cụm trùng với val/test", "kết luận"]
    rows, problems, warnings = [], [], []
    for name in names:
        info = prompts.examples_info(prompts.load(name).examples_value)
        if info and info["note"]:
            print("Nguồn ví dụ của '{}': {}".format(name, info["note"].splitlines()[0]))
            print("  ({} - {} ví dụ, sha {})".format(
                info["file"], info["examples"], info["sha"]))
        one_rows, one_problems, one_warnings = check_prompt(
            name, label_map, index, args.max_overlap)
        rows.extend(one_rows)
        problems.extend(one_problems)
        warnings.extend(one_warnings)

    print()
    print_table(rows, columns)

    if warnings:
        print("\n  LƯU Ý (không phải lỗi):")
        for item in warnings:
            print("      {}".format(item))
    if problems:
        print("\n  LỖI - phải sửa file ví dụ:")
        for item in problems:
            print("      {}".format(item))
        print("\n  Nguyên tắc: ví dụ lấy TỪ DỮ LIỆU chỉ được lấy từ split train (lấy từ")
        print("  val/test là rò rỉ đánh giá). Ngưỡng báo lỗi hiện tại: cụm >= {} từ "
              "trùng val/test.".format(args.max_overlap))
        return 1

    print("\nKết luận: {} ví dụ đã kiểm - không có lỗi cấu trúc/nhãn, không rò rỉ với "
          "val/test.".format(len(rows)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
