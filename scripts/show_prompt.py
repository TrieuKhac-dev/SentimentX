# -*- coding: utf-8 -*-
"""In ra CÂU LỆNH THẬT đang gửi cho model, để kiểm bằng mắt chứ không tin vào suy đoán.

CÁCH DÙNG
    python scripts/show_prompt.py qwen3-4b-instruct-2507/prompt-cot/exp001
    python scripts/show_prompt.py <...> --split test --row 5
    python scripts/show_prompt.py <...> --text "Son này lên màu đẹp, giữ được lâu"

VÌ SAO CẦN
Đọc file prompt và đọc config không trả lời được câu hỏi "model thực sự nhận gì": còn phải qua
bảng mã nhãn sinh từ `label_map.json`, qua danh sách khía cạnh, qua chat template của tokenizer, và
qua ngưỡng cắt `max_length`. Bốn bước đó nằm ở bốn chỗ khác nhau, và sai ở bất kỳ bước nào thì
prompt vẫn "chạy ra số" - chỉ là số đo không còn nghĩa gì.

Công cụ in ba thứ, theo thứ tự đọc được:
    1. Nguồn: file prompt, file ví dụ, file khối hệ thống - kèm sha và số ví dụ.
    2. Bản ghi hội thoại (SYSTEM/USER/ASSISTANT) - để ĐỌC.
    3. Chuỗi sau chat template - ĐÚNG thứ model nhận, kèm số token và phần bị cắt ở đuôi (nếu có).

Số token lấy từ `qwen.encode`, đúng hàm mà bước đo `run_token_stats.py` dùng, nên hai chỗ không
thể lệch nhau.
"""

import argparse
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Trên Windows, console mặc định có thể không phải UTF-8 (ví dụ cp1252),
# khiến việc in tiếng Việt bị lỗi. Ép stdout/stderr sang UTF-8.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from src import config, dataset, experiments, labels, model_config, paths, versioning
from src.preprocessing import loader, qwen


class ShowPromptError(Exception):
    """Không in được: thiếu thí nghiệm/config/dữ liệu, hoặc không nạp được tokenizer."""


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="In prompt thật gửi cho model của một thí nghiệm.")
    parser.add_argument("target", help="`<model_id>/<method>/<expNNN>` hoặc đường dẫn config.yaml.")
    parser.add_argument("--split", default=None,
                        help="Split lấy review (mặc định: vai `eval` trong config thí nghiệm).")
    parser.add_argument("--row", type=int, default=0, help="Dòng thứ mấy của split (mặc định 0).")
    parser.add_argument("--text", default=None, help="Dùng review này thay vì lấy từ dữ liệu.")
    parser.add_argument("--max-length", dest="max_length", type=int, default=None,
                        help="Ngưỡng cắt để đối chiếu (mặc định: `preprocess.max_length` của model).")
    return parser.parse_args(argv)


def experiment_parts(target):
    """`<model_id>/<method>/<expNNN>` từ tham số dòng lệnh."""
    parts = [part for part in str(target).replace("\\", "/").split("/") if part]
    if len(parts) != 3:
        raise ShowPromptError(
            "Cần `<model_id>/<method>/<expNNN>` (ví dụ `qwen3-4b-instruct-2507/prompt-cot/exp001`); "
            "nhận được: {}".format(target))
    return parts


def use_run_tokenizer(model_id, checkpoint):
    """Dùng ĐÚNG tokenizer mà lượt chạy dùng: bản trên đĩa nếu có, không thì bản của checkpoint.

    Tokenizer khác bản model thì chat template khác, và prompt in ra sẽ không phải prompt đã chạy -
    đúng loại sai lệch mà công cụ này sinh ra để chặn.
    """
    local = os.environ.get("SENTIMENTX_MODEL") or None
    source = local or checkpoint
    try:
        from transformers import AutoTokenizer
    except ImportError:
        print("LƯU Ý: máy này không có `transformers`, nên KHÔNG in được chuỗi sau chat template "
              "và số token. Phần bản ghi hội thoại ở trên vẫn đúng.\n")
        return None, source
    try:
        tokenizer = AutoTokenizer.from_pretrained(source, local_files_only=bool(local))
    except Exception as error:                                   # thiếu mạng hoặc thiếu file
        print("LƯU Ý: không nạp được tokenizer từ {} ({}). Bỏ qua phần chuỗi sau chat template.\n"
              .format(source, error))
        return None, source
    qwen.use_tokenizer(tokenizer)
    return tokenizer, source



def describe_sources(prompt_obj, label_map, aspects, split, row, tokenizer_name):
    """In nguồn của prompt: file nào, sha nào, bao nhiêu ví dụ, khối hệ thống, bảng mã nhãn."""
    print("Prompt      : {} | {}".format(prompt_obj.name, prompt_obj.path))
    print("  sha       : {}".format(prompt_obj.sha))
    examples = prompt_obj.examples_info()
    if examples:
        print("Ví dụ       : {} - {} ví dụ, sha {}".format(
            examples["file"], examples["examples"], examples["sha"]))
    else:
        print("Ví dụ       : không dùng")
    system = prompt_obj.system_info()
    print("Hệ thống    : {}".format(
        "{} ({})".format(system["file"], system["sha"]) if system else "không dùng"))
    print("Khía cạnh   : {}".format(", ".join(aspects)))
    print("Mã nhãn     : {}".format(
        ", ".join("{}={}".format(name or "(không nhắc)", code)
                  for name, code in sorted(label_map["label_to_id"].items(),
                                           key=lambda item: item[1]))))
    print("Dữ liệu     : split {} dòng {}".format(split, row))
    print("Tokenizer   : {}".format(tokenizer_name or "(không nạp được)"))
    print("Ô nhớ dùng  : {}".format(", ".join(sorted(prompt_obj.placeholders))))


def show_messages(messages):
    """In bản ghi hội thoại cho người đọc (đây là phần dễ kiểm bằng mắt nhất)."""
    print("\n--- BẢN GHI HỘI THOẠI (để đọc) ---")
    for message in messages:
        print("[{}]".format(str(message.get("role", "")).upper()))
        print(message.get("content", ""))
        print()


def show_chat_text(text, aspects, label_map, prompt_obj, max_length):
    """In đúng chuỗi model nhận, số token, và phần bị cắt ở đuôi nếu vượt ngưỡng."""
    try:
        tokenizer = qwen.tokenizer()
    except ImportError as error:
        print("Bỏ qua phần chat template: {}".format(error))
        return
    chat = tokenizer.apply_chat_template(
        qwen.conversations([text], aspects, label_map, prompt_obj.name),
        tokenize=False, add_generation_prompt=qwen.default_add_generation_prompt())
    # `apply_chat_template` trả về list (một phần tử cho mỗi hội thoại) dù truyền một hội thoại.
    if isinstance(chat, (list, tuple)):
        chat = chat[0]
    print("--- CHUỖI SAU CHAT TEMPLATE (đúng thứ model nhận) ---")
    print(chat)
    ids = qwen.encode([text], aspects=aspects, label_map=label_map,
                      prompt_name=prompt_obj.name)[0]
    print("--- ĐỘ DÀI ---")
    print("max_length đang dùng: {} token".format(max_length))
    print("Số token của mẫu này: {} token".format(len(ids)))
    if len(ids) <= max_length:
        print("Kết luận            : KHÔNG bị cắt (còn dư {} token).".format(max_length - len(ids)))
        return
    lost = tokenizer.decode(ids[max_length:], skip_special_tokens=False)
    print("Kết luận            : BỊ CẮT - mất {} token Ở ĐUÔI, đúng phần dễ mất chỉ dẫn nhất."
          .format(len(ids) - max_length))
    print("Phần bị mất (dịch lại từ token):\n{}".format(lost))


def main(argv=None):
    args = parse_args(argv)
    model_id, method, exp_id = experiment_parts(args.target)
    result = experiments.load(model_id, method, exp_id)
    merged = result["config"]
    experiment_dir = paths.experiment_dir(model_id, method, exp_id)

    ds = dataset.load_config(merged["data"]["dataset"])
    version_id = versioning.compute_id(ds)
    checkpoint = model_config.load(model_id).get("checkpoint")
    _tokenizer, tokenizer_name = use_run_tokenizer(model_id, checkpoint)

    prompt_obj = qwen.load_prompt(merged.get("prompt"), base_dir=experiment_dir,
                                  examples=merged.get("examples"),
                                  system=merged.get("system_prompt"))
    label_map = loader.load_label_map(version_id, dataset=ds["name"])
    label_map = labels.filter_label_map(label_map, merged["label_space"],
                                        merged["neutral_policy"])
    aspects = labels.task_aspects(merged, label_map["aspects"])

    split = args.split or (merged.get("data", {}).get("roles") or {}).get("eval") or "val"
    if args.text:
        text = args.text
    else:
        frame = loader.load_processed(split, version_id=version_id, dataset=ds["name"])
        if args.row < 0 or args.row >= len(frame):
            raise ShowPromptError("Dòng {} nằm ngoài split {} ({} dòng).".format(
                args.row, split, len(frame)))
        text = str(frame[config.TEXT_COLUMN].iloc[args.row])

    max_length = args.max_length or qwen.limit()[0]
    print("Thí nghiệm  : {}/{}/{}".format(model_id, method, exp_id))
    describe_sources(prompt_obj, label_map, aspects, split, args.row, tokenizer_name)
    print("\n--- REVIEW ĐƯA VÀO ---")
    print(text)
    values = qwen.values(text, aspects=aspects, label_map=label_map, prompt=prompt_obj)
    print("\n--- BẢN GHI CỦA PROMPT (bản đọc được) ---")
    print(prompt_obj.transcript(values))
    show_messages(qwen.conversations([text], aspects, label_map, prompt_obj.name)[0])
    show_chat_text(text, aspects, label_map, prompt_obj, max_length)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ShowPromptError as error:
        print("\nDỪNG: {}".format(error))
        raise SystemExit(2)
