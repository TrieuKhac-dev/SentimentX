# -*- coding: utf-8 -*-
"""Đo tokenizer THẬT của từng model trên dữ liệu ĐÃ XỬ LÝ (tiền xử lý cho model).

Cách dùng:
    python run_token_stats.py
    python run_token_stats.py --dataset cosmetics
    python run_token_stats.py --prompt qwen_absa_v1      # đo một prompt khác
    python run_token_stats.py --segmenter vncorenlp      # chọn bộ tách từ cho PhoBERT
    python run_token_stats.py --list-prompts             # xem đang có prompt nào
    python run_token_stats.py --list-segmenters          # xem máy đã cài bộ tách từ nào

Vì sao cần: EDA đếm TỪ (utils.tokenize) để khảo sát dữ liệu, nhưng model đọc SUBWORD
của tokenizer riêng. Cùng một review có thể thành 20 token với model này và 60 token
với model khác, và con số quyết định là bao nhiêu review vượt `max_length` (bị cắt).
Phép đo này chỉ làm được bằng chính tokenizer của model, xem chi tiết ở đầu
src/preprocessing/token_stats.py.

Kết quả (trong thư mục theo phiên bản):
    data/reports/model_input/versions/<mã>/token_stats.csv
    data/reports/model_input/versions/<mã>/token_stats__prompt-X__seg-Y.csv  (khi đổi
        prompt/bộ tách từ so với mặc định - KHÔNG ghi đè lên số liệu cũ)

Chỉ cần thư viện `transformers` (không cần torch). Model nào không đo được sẽ được bỏ
qua kèm lí do: PhoBERT cần một bộ tách từ (bộ chính chủ là RDRSegmenter/VnCoreNLP, cần
Java - xem `--list-segmenters`).
"""

import argparse
import difflib
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
from src.preprocessing import qwen, segmenters, token_stats


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Đo tokenizer thật của từng model trên dữ liệu đã xử lý."
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
        help="Tên prompt dùng cho Qwen3 (mặc định: prompt ghi trong "
             "file cấu hình model). Dùng để thử prompt mới mà không phải sửa "
             "config.",
    )
    parser.add_argument(
        "--segmenter", default=None,
        help="Bộ tách từ cho PhoBERT: auto (mặc định: bộ chính chủ nếu có, không thì "
             "pyvi) | vncorenlp | pyvi | underthesea | none.",
    )
    parser.add_argument(
        "--max-length", dest="max_length", action="append", default=None,
        metavar="N|MODEL=N",
        help="Ghi đè ngưỡng cắt input cho một lần chạy. Dạng 'N' (áp cho mọi model, "
             "báo lỗi nếu vượt trần của model nào) hoặc 'qwen=1280' (chỉ model đó; lặp "
             "lại được nhiều lần). Ngưỡng mặc định: configs/models/<model>.yaml, còn "
             "không thì hằng số MAX_LENGTH trong module model.",
    )
    parser.add_argument(
        "--list-prompts", action="store_true",
        help="In danh sách prompt trong configs/prompts/ rồi thoát.",
    )
    parser.add_argument(
        "--list-segmenters", action="store_true",
        help="In các bộ tách từ và tình trạng cài đặt trên máy này rồi thoát.",
    )
    return parser.parse_args(argv)


def parse_max_length(values, model_keys):
    """Đọc các giá trị `--max-length` thành dict {tên model: số token}.

    Nhận hai dạng:
        --max-length 128         đặt 128 cho MỌI model
        --max-length qwen=1280   chỉ đặt cho model 'qwen' (lặp lại được nhiều lần)

    Kiểm tra ngay tại đây, trước khi tải dữ liệu (mỗi lần chạy tốn vài phút): tên model
    phải có thật, giá trị phải là số nguyên dương, và KHÔNG được vượt trần kiến trúc của
    model (PhoBERT 258, ViSoBERT 514, Qwen 262.144) - vượt trần thì model sẽ cắt hoặc sai
    vị trí mà bảng số liệu vẫn báo "0% bị cắt".
    """
    overrides = {}
    ceilings = token_stats.position_limits()

    for raw in values or []:
        text = str(raw).strip()
        name, _, number = text.partition("=")
        if not number:
            number, name = name, ""

        try:
            value = int(number)
        except ValueError:
            raise ValueError(
                "Giá trị của --max-length phải là số nguyên, đang nhận '{}'. Ví dụ: "
                "--max-length 128 hoặc --max-length qwen=1280.".format(text))
        if value <= 0:
            raise ValueError(
                "Giá trị của --max-length phải lớn hơn 0, đang nhận {}.".format(value))

        targets = [name.strip().lower()] if name.strip() else list(model_keys)
        for key in targets:
            if key not in model_keys:
                hint = difflib.get_close_matches(key, model_keys, n=1, cutoff=0.5)
                raise ValueError(
                    "Không có model '{}' trong --max-length. Các model đang đo: {}.{}"
                    .format(key, ", ".join(model_keys),
                            " Có phải bạn muốn '{}'?".format(hint[0]) if hint else ""))

            ceiling = ceilings.get(key)
            if ceiling and value > ceiling:
                raise ValueError(
                    "Ngưỡng cắt {} vượt trần của {} ({} vị trí). Phần vượt sẽ bị model "
                    "cắt hoặc sai vị trí mà bảng số liệu vẫn báo '0% bị cắt'. Dùng giá "
                    "trị nhỏ hơn, hoặc chỉ định riêng cho từng model: --max-length "
                    "{}=<số>.".format(value, key, ceiling, key))
            overrides[key] = value

    return overrides


def print_table(rows, columns):
    """In bảng số liệu ra console, cột căn trái theo nội dung."""
    if not rows:
        print("  (không có số liệu)")
        return
    widths = [
        max(len(str(value)) for value in [columns[index]]
            + [row[index] for row in rows])
        for index in range(len(columns))
    ]
    def line(values):
        return "  " + "  ".join(
            "{:<{}}".format(str(values[index]), widths[index])
            for index in range(len(columns))
        )
    print(line(columns))
    print("  " + "  ".join("-" * width for width in widths))
    for row in rows:
        print(line(row))



def list_prompts():
    """In danh sách prompt đang có trong configs/prompts/ (mỗi prompt một dòng).

    Có cả cột `số ví dụ` (kèm mã sha của FILE VÍ DỤ): bộ ví dụ few-shot là một biến thí
    nghiệm, mà prompt one-shot và two-shot dùng chung nội dung prompt nên cột `sha` của
    prompt in ra sẽ GIỐNG nhau - chỉ cột này mới phân biệt được chúng.
    """
    keys = ("name", "sha", "kiểu", "số ví dụ", "ô nhớ", "file")
    print_table([[row[key] for key in keys] for row in prompts.describe_all()],
                ["prompt", "sha", "kiểu", "số ví dụ", "ô nhớ", "file"])
    print("\nPrompt đang dùng ghi ở configs/models/qwen.yaml. Muốn thử prompt khác "
          "trong một lần chạy: --prompt <tên>.")
    print("Số ví dụ là biến thí nghiệm ĐỔI ĐƯỢC mà không phải sửa prompt: bỏ/thêm khối "
          "'--- Ví dụ n ---' trong configs/prompts/examples/<tên>.txt.")
    return 0


def list_segmenters():
    """In tình trạng các bộ tách từ trên máy này.

    Lệnh này KHÔNG khởi động JVM (chỉ kiểm tra file/thư viện), nên chạy rất nhanh -
    dùng để biết ngay còn thiếu gì trước khi chạy phép đo tốn vài phút.
    """
    keys = ("tên", "chính chủ", "dùng được", "gói", "phiên bản")
    rows = segmenters.status()
    print_table([[row[key] for key in keys] for row in rows],
                ["bộ tách từ", "chính chủ", "dùng được", "gói", "phiên bản"])
    for row in rows:
        print("\n  - {}: {}".format(row["tên"], row["ghi chú"]))
    print("\nBộ tách từ chỉ áp dụng cho PhoBERT (ViSoBERT và Qwen đọc văn bản nguyên "
          "bản).\nBộ chính chủ: {}. Cách cài: chạy scripts\\setup_vncorenlp.ps1.".format(
              ", ".join(segmenters.official_names())))
    return 0


def _segmenter_label(spec):
    """Chuỗi mô tả bộ tách từ sẽ dùng, hoặc lí do chưa dùng được (không báo lỗi)."""
    try:
        name, module = segmenters.resolve(spec)
    except segmenters.SegmenterError as exc:
        lines = [line for line in str(exc).strip().splitlines() if line.strip()]
        return "chưa dùng được - {} (xem --list-segmenters)".format(
            lines[0] if lines else exc)

    meta = module.info()
    java = ", {}".format(meta["java_version"]) if meta.get("java_version") else ""
    return "{} ({}{}), gói {} {}".format(
        name, "chính chủ" if module.OFFICIAL else "KHÔNG chính chủ", java,
        meta.get("package") or "-", meta.get("version") or "?")


def print_config(prompt, segmenter_spec, max_length_overrides=None):
    """In cấu hình đo, để người đọc biết bảng số liệu dưới đây ứng với cái gì."""
    ceilings = token_stats.position_limits()
    print("Cấu hình đo:")
    print("  prompt     : {} ({}), sha {}".format(
        prompt.name, prompt.where, prompt.sha))
    if prompt.multiline:
        print("               hội thoại nhiều lượt: {}".format(
            " -> ".join(name.upper() for name, _ in prompt.sections)))
    examples = prompts.examples_info(prompt.name)
    if examples:
        print("  ví dụ      : {} - {} ví dụ, sha {}".format(
            examples["file"], examples["examples"],
            examples["sha"] or "THIẾU FILE (prompt cần {examples} mà chưa có file)"))
        if examples["note"]:
            print("               nguồn: {}".format(
                examples["note"].splitlines()[0]))
    print("  bộ tách từ : {}".format(_segmenter_label(segmenter_spec)))
    print("               (chỉ PhoBERT dùng; ViSoBERT và Qwen đọc văn bản nguyên bản)")
    print("  max_length :")
    for key, value, source, differs, _from_cli in token_stats.limits(max_length_overrides):
        print("      {:<9}{:>7} token   nguồn: {}{}   trần model: {}".format(
            key, value, source, "  (KHÁC mặc định)" if differs else "",
            ceilings.get(key) or "không rõ"))
    print()


def build_tag(args, max_length_overrides=None, prompt=None):
    """Tên phụ cho file CSV: ghi rõ lần chạy này khác mặc định ở chỗ nào.

    Chỉ sinh tag khi có tham số KHÁC mặc định, để lần chạy thường vẫn ghi ra
    `token_stats.csv` như trước - không đẻ thêm file cho cùng một việc.

    Quy tắc rõ ràng: **chỉ cờ dòng lệnh** (`--prompt`, `--segmenter`, `--max-length`) mới
    làm tên file có đuôi, vì đó là "chạy khác đi một lần". Còn sửa
    `configs/models/<model>.yaml` là **cấu hình của dự án** (giá trị đang dùng), nên vẫn
    ghi vào file mặc định - nếu không, chỉ đổi một dòng YAML là file mặc định biến mất,
    khó tra cứu. Giá trị hiệu lực vẫn luôn được ghi lại: cột `max_length` trong CSV, dòng
    `max_length` ở banner, và khoá `limits` trong mục lục.

    NGOẠI LỆ duy nhất: `ex-<sha4>` của BỘ VÍ DỤ few-shot, và nó có mặt **kể cả khi chạy
    bằng config của dự án**. Lí do: hai bộ ví dụ (một ví dụ vs hai ví dụ) là hai thí
    nghiệm thật, trong khi `prompt_sha` của chúng GIỐNG nhau (prompt chỉ khác ở file ví
    dụ) - ghi chung một file thì thí nghiệm sau xoá mất số liệu của thí nghiệm trước.
    """
    parts = []
    if args.prompt:
        parts.append("prompt-{}".format(args.prompt))
    info = prompts.examples_info(prompt.name) if prompt is not None else None
    if info and info["sha"]:
        parts.append("ex-{}".format(info["sha"]))
    if args.segmenter:
        parts.append("seg-{}".format(args.segmenter))
    for key, value, _source, _differs, from_cli in token_stats.limits(max_length_overrides):
        if from_cli:
            parts.append("maxlen-{}-{}".format(key, value))
    return "__".join(parts) or None


def main(argv=None):
    args = parse_args(argv)

    print("=" * 70)
    print("TOKEN STATS - đo input THẬT của từng model (tiền xử lý cho model)")
    print("=" * 70)

    if args.list_prompts:
        return list_prompts()
    if args.list_segmenters:
        return list_segmenters()

    # Tham số sai phải dừng NGAY, trước khi tải dữ liệu và tokenizer (mỗi lần chạy tốn
    # vài phút), và gõ sai tên là lỗi hay gặp nhất. In một dòng gọn kèm gợi ý thay vì để
    # traceback che mất thông báo.
    try:
        prompt = qwen.load_prompt(args.prompt)
    except prompts.PromptError as exc:
        print("LỖI: {}".format(exc))
        return 2
    if args.segmenter:
        try:
            segmenters.resolve(args.segmenter)
        except segmenters.SegmenterError as exc:
            print("LỖI: {}".format(exc))
            return 2
    try:
        max_length_overrides = parse_max_length(
            args.max_length, [spec["key"] for spec in token_stats.MODELS])
    except ValueError as exc:
        print("LỖI: {}".format(exc))
        return 2

    try:
        ds = dataset.load_config(args.dataset)
    except dataset.DatasetError as exc:
        print("LỖI: {}".format(exc))
        return 2
    version_id = args.version or versioning.compute_id(
        ds)
    print("Dataset: {} (phiên bản dữ liệu: {})".format(ds["name"], version_id))
    print("Nguồn dữ liệu: {}\n".format(
        utils.rel(versioning.processed_dir(version_id))))
    print_config(prompt, args.segmenter, max_length_overrides)

    rows, skipped, context = token_stats.run(
        dataset=ds["name"], version_id=version_id,
        prompt_name=args.prompt, segmenter=args.segmenter,
        max_length=max_length_overrides)
    print_table(rows, token_stats.COLUMNS)

    # KHÔNG có dòng nào nghĩa là KHÔNG đo được model nào (thiếu thư viện, thiếu Java, hoặc
    # một tiến trình cài đặt đang chạy giữa chừng...). Ghi một bảng rỗng lên file cũ là XOÁ
    # MẤT số liệu cũ mà trong thư mục vẫn thấy file tồn tại - đúng loại mất mát im lặng mà
    # dự án đang cố tránh. Từ chối ghi, báo lỗi, và để nguyên số liệu cũ.
    if not rows:
        print("\n  LỖI: không đo được model nào nên KHÔNG ghi file và KHÔNG ghi mục lục")
        print("        (ghi một bảng rỗng sẽ xoá số liệu cũ mà không ai biết).")
        for name, reason in skipped:
            print("        ! {}: {}".format(name, reason))
        print("        Sửa lí do trên rồi chạy lại; thiếu Java thì xem "
              "`--list-segmenters`.")
        return 1

    # Cắt mất phần đuôi là mất DỮ LIỆU (và với prompt chat, phần đuôi còn chứa cả yêu
    # cầu định dạng đầu ra), nên không để nó lặng lẽ nằm trong một ô của bảng số liệu.
    cut_index = token_stats.COLUMNS.index("% review > max_length")
    cut = [(row[0], row[1], row[cut_index]) for row in rows
           if float(row[cut_index]) > 0]
    if cut:
        print("\n  LƯU Ý: có review BỊ CẮT MẤT PHẦN ĐUÔI (ngưỡng cắt nhỏ hơn input dài "
              "nhất):")
        for model, split, percent in cut:
            print("      {:<9} {:<6} {:.2f}% review bị cắt".format(model, split, percent))
        print("      Cách xử lý: nâng ngưỡng cắt - sửa `max_length` trong "
              "file cấu hình của model,")
        print("      hoặc chạy lại với --max-length <model>=<số> (xem trần của model ở "
              "banner phía trên).")

    for name, reason in skipped:
        print("\n  ! Bỏ qua model '{}': {}".format(name, reason))
    if skipped:
        print("\n    (chạy `--list-segmenters` để biết máy còn thiếu gì, rồi chạy lại)")

    unk_index = token_stats.COLUMNS.index("% token <unk>")
    if any(row[unk_index] == token_stats.NOT_APPLICABLE for row in rows):
        print("\n  Ghi chú: '{}' ở cột '% token <unk>' nghĩa là KHÔNG TÍNH ĐƯỢC, "
              "không phải bằng 0\n    (tokenizer của model không khai báo token "
              "<unk>).".format(token_stats.NOT_APPLICABLE))


    tag = build_tag(args, max_length_overrides, prompt)
    path = token_stats.write(rows, version_id, tag=tag)

    print("Hoàn tất. Đã ghi số liệu:")
    print("  - {}".format(utils.rel(path)))
    if tag:
        print("    (tên file có đuôi '{}' vì lần chạy này khác cấu hình mặc định, "
              "nên KHÔNG ghi đè số liệu cũ)".format(tag))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
