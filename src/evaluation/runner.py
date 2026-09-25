# -*- coding: utf-8 -*-
"""Chạy Qwen3 để SINH kết quả cho một prompt (đánh giá model) - chỉ suy luận, không huấn luyện.

VÌ SAO KHÔNG HUẤN LUYỆN QWEN3
---
Qwen3-4B full fine-tune cần ~64-80 GB VRAM; riêng trọng số bf16 đã 8 GB, trong khi GPU của
máy này có 6 GB. Hướng đúng bản chất phép so sánh của dự án: Qwen3 dùng như model đa năng
qua CHỈ DẪN (prompt / CoT), còn PhoBERT (135M) và ViSoBERT (~108M) thì fine-tune toàn bộ.
Lượng hóa 4-bit ở đây là để model **VỪA VRAM khi suy luận**, không phải để huấn luyện.

CÁC QUYẾT ĐỊNH KỸ THUẬT VÀ LÍ DO
---
1. **Greedy (`do_sample=False`) là mặc định.** Kết quả phải TÁI LẬP được: chạy lại phải ra
   đúng câu trả lời đó. Model card của Qwen3-4B-Instruct-2507 khuyến nghị
   `Temperature=0.7, TopP=0.8, TopK=20` cho chất lượng cảm nhận, nhưng khi ĐO thì yếu tố
   tái lập quan trọng hơn; muốn đối chiếu thì chạy thêm với `--sample` (và khi đó phải ghi
   cả `seed`).
2. **Cắt phần đuôi ở `max_length`** (mặc định 1280, lấy từ `qwen.limit()`): prompt CoT có
   max 1.019 token/review nên 0% bị cắt. Với prompt chat, phần bị cắt là phần CUỐI - tức
   chính yêu cầu định dạng đầu ra, nên ngưỡng này phải chọn bằng số đo (xem
   docs/04_experiments/02_model_input.md, mục 4.2).
3. **`padding_side = "left"`**: khi sinh theo lô, đầu ra của các câu dài ngắn khác nhau phải
   thẳng hàng về BÊN PHẢI để cắt phần đã sinh bằng `out[:, len(input):]`. Để mặc định
   (right) thì phép cắt đó lấy nhầm chỗ và câu trả lời đọc ra là vô nghĩa - một lỗi im lặng
   rất dễ mắc khi chạy lô.
4. **Đếm token sinh ra** để báo cáo chi phí đầu ra thật (khác hẳn số token của prompt).
5. **Không tin vào model card về `<think>`**: bản 2507 là non-thinking theo tài liệu, nhưng
   tokenizer vẫn có token `<think>`, nên bộ đọc ĐẾM số câu trả lời có `<think>` thay vì
   giả định là không có.

Chỉ module này cần `torch`; `parse.py` và `metrics.py` là hàm thuần nên test được không
cần GPU (`python -m unittest discover -s tests`).
"""

import time
from pathlib import Path

from src import config, paths, utils
from src.evaluation import metrics, parse, records
from src.preprocessing import qwen

# Cột của bảng dự đoán: định nghĩa ở `records.py` để chỗ ghi CSV, chỗ ghi khối `part_*.jsonl` và
# chỗ chấm lại từ file dùng CÙNG một tên cột. Bảng của đường chạy có prompt thêm một cột so với bảng
# gốc (`records.columns(with_prompt=True)`); muốn bảng của model encoder thì dùng `records.COLUMNS`.
PREDICTION_COLUMNS = records.columns(with_prompt=True)

# Cấu hình sinh mặc định
DEFAULT_MAX_NEW_TOKENS = 400


def settings(quant="auto", max_new_tokens=None, do_sample=False, temperature=None,
             top_p=None, top_k=None, seed=None):
    """Cấu hình sinh đang dùng, dạng dict để IN RA và GHI VÀO mục lục.

    Trả về cả những giá trị KHÔNG dùng (ghi `None`) - nhờ vậy báo cáo luôn nói rõ là chạy
    greedy hay lấy mẫu, thay vì để người đọc đoán theo mặc định của thư viện.
    """
    return {
        "quant": quant,
        "max_new_tokens": int(max_new_tokens or DEFAULT_MAX_NEW_TOKENS),
        "do_sample": bool(do_sample),
        "temperature": temperature if do_sample else None,
        "top_p": top_p if do_sample else None,
        "top_k": top_k if do_sample else None,
        "seed": seed if do_sample else None,
    }


def _require(name):
    """Nạp một thư viện, báo lỗi kèm đúng lệnh cần chạy."""
    try:
        return __import__(name)
    except ImportError as exc:
        raise ImportError(
            "Thiếu thư viện '{}'. Cài bằng:\n"
            "    pip install torch transformers accelerate bitsandbytes\n"
            "    (bản CUDA: pip install torch --index-url "
            "https://download.pytorch.org/whl/cu126)".format(name)) from exc


def _ensure_chat_template(tokenizer, model_name):
    """Bảo đảm tokenizer CÓ chat template, nạp lại từ đĩa nếu cần.

    VÌ SAO PHẢI KIỂM (lỗi đã gặp thật, mất khá nhiều thời gian để tìm): khi nạp tokenizer
    từ thư mục cục bộ, `chat_template` có thể rỗng - và khi rỗng thì `apply_chat_template`
    trả về chuỗi **RỖNG mà không báo lỗi**, rồi `model.generate` chết ở giữa với thông báo
    chẳng liên quan (`IndexError: attention_mask[:, -1] ... dimension of size 0`).

    Nguyên nhân cụ thể đã gặp: thư mục model có file `chat_template.jinja` **0 byte** (do
    tải một đường dẫn không tồn tại), và file rỗng đó CHE MẤT template hợp lệ nằm trong
    `tokenizer_config.json`. Vì vậy ở đây thử theo thứ tự: file .jinja (chỉ khi có nội
    dung) -> khoá `chat_template` trong tokenizer_config.json.
    """
    if getattr(tokenizer, "chat_template", None):
        return tokenizer

    folder = Path(model_name)
    if folder.is_dir():
        jinja = folder / "chat_template.jinja"
        if jinja.exists() and jinja.stat().st_size > 0:
            tokenizer.chat_template = jinja.read_text(encoding="utf-8")
        if not getattr(tokenizer, "chat_template", None):
            config_path = folder / "tokenizer_config.json"
            if config_path.exists():
                import json
                with open(config_path, "r", encoding="utf-8") as handle:
                    stored = (json.load(handle) or {}).get("chat_template")
                # Có thể là chuỗi, hoặc danh sách nhiều template (mỗi mục một điều kiện).
                if isinstance(stored, list) and stored:
                    stored = stored[0].get("template") if isinstance(stored[0], dict) \
                        else stored[0]
                if stored:
                    tokenizer.chat_template = stored

    if not getattr(tokenizer, "chat_template", None):
        raise RuntimeError(
            "Tokenizer của '{0}' KHÔNG có chat template, nên prompt sẽ rỗng và model sinh "
            "ra rác. Template thường nằm ở file 'chat_template.jinja' (phải có nội dung) "
            "hoặc khoá 'chat_template' trong tokenizer_config.json - tải lại bằng:\n"
            "    powershell -ExecutionPolicy Bypass -File scripts\\setup_qwen_model.ps1"
            .format(model_name))
    return tokenizer


def generate(inputs, model, tokenizer, generation):
    """Sinh cho MỘT lô input. Trả về (câu trả lời, số token sinh TỪNG dòng, giây của lô).

    Số token sinh được đếm theo TỪNG dòng (không phải pad) vì chi phí đầu ra là số liệu
    thật của thí nghiệm: prompt CoT khiến model sinh thêm cả phần suy luận, nên "đắt" ở cả
    hai đầu (input dài hơn VÀ output dài hơn).
    """
    torch = _require("torch")
    device = next(model.parameters()).device
    inputs = {key: value.to(device) for key, value in inputs.items()}

    kwargs = {
        "max_new_tokens": generation["max_new_tokens"],
        "do_sample": generation["do_sample"],
        "eos_token_id": tokenizer.eos_token_id,
        "pad_token_id": tokenizer.pad_token_id,
    }
    if generation["do_sample"]:
        kwargs["temperature"] = generation["temperature"]
        if generation["top_p"] is not None:
            kwargs["top_p"] = generation["top_p"]
        if generation["top_k"] is not None:
            kwargs["top_k"] = generation["top_k"]

    started = time.perf_counter()
    with torch.no_grad():
        output = model.generate(**inputs, **kwargs)
    elapsed = time.perf_counter() - started

    prompt_length = int(inputs["input_ids"].shape[1])
    produced = output[:, prompt_length:]
    answers = tokenizer.batch_decode(produced, skip_special_tokens=True)
    lengths = (produced != tokenizer.pad_token_id).sum(dim=1).tolist()
    return answers, [int(value) for value in lengths], elapsed


def sent_prompts(tokenizer, inputs, columns):
    """Chuỗi ĐÃ GỬI cho model của từng dòng trong lô (rỗng nếu bảng không có cột prompt).

    Dịch ngược token id thành chữ SAU khi đã cắt ở `max_length`, nên đây đúng là thứ model nhận -
    không phải bản prompt "đầy đủ" trên lý thuyết. Bảng của model encoder không có cột này nên
    không tốn công dịch.
    """
    if records.PROMPT_COLUMN not in columns:
        return [""] * len(inputs["input_ids"])
    tokenizer = tokenizer or qwen.tokenizer()
    mask = inputs.get("attention_mask") if hasattr(inputs, "get") else None
    texts = []
    for index, row in enumerate(inputs["input_ids"]):
        ids = row
        if mask is not None:
            # Bỏ phần PAD: đệm nằm ở BÊN TRÁI (padding_side="left"), nếu không bỏ thì prompt in ra
            # bắt đầu bằng hàng loạt token đệm và người đọc sẽ tưởng model nhận rác.
            ids = row[mask[index].bool()]
        texts.append(tokenizer.decode(ids.tolist(), skip_special_tokens=False))
    return texts


def run(split, texts, golds, aspects, label_map, prompt_name, model, tokenizer,
        batch_size=4, max_length=None, generation=None, row_index=None, quiet=False,
        store=None, columns=None):
    """Sinh + đọc kết quả cho cả một split (hoặc một tập con).

    `golds` là list[dict {khía cạnh: mã đúng}]; `row_index` là chỉ số dòng gốc trong file
    dữ liệu (cần khi chạy trên tập con, để luôn tra ngược được về review nào).
    Trả về (các dòng bảng, thông tin đọc kết quả, nhãn DỰ ĐOÁN, meta).

    Trả về cả `nhãn dự đoán` đã đọc sẵn (không phải đọc lại từ chuỗi JSON trong bảng) để
    nơi chấm điểm dùng ĐÚNG kết quả mà bộ đọc đã phân tích - nếu không, việc chấm điểm và
    việc báo cáo tỉ lệ đọc được có thể nói hai chuyện khác nhau.

    `store` (tuỳ chọn) là `src.resume.Parts`: mỗi lô xong được ghi xuống đĩa NGAY, nên bị ngắt
    giữa chừng thì lần chạy sau biết mẫu nào đã xong. Không truyền thì kết quả chỉ nằm trong bộ
    nhớ cho tới lúc ghi file cuối cùng.

    `columns` là cột của bảng dự đoán (xem `records.columns`). Mặc định có cột `prompt gửi model`
    vì đường chạy này LUÔN gửi prompt cho model; model encoder sẽ truyền bảng không có cột đó.
    """
    generation = generation or settings()
    aspects = list(aspects)
    codes = list(label_map["label_to_id"].values())
    columns = list(columns or records.columns(with_prompt=True))
    rows, infos, preds = [], [], []
    total_tokens, total_seconds, total_items = 0, 0.0, 0
    starts = list(range(0, len(texts), batch_size))

    for order, start in enumerate(starts, 1):
        chunk = list(texts[start:start + batch_size])
        inputs = qwen.build_inputs(chunk, max_length=max_length, aspects=aspects,
                                   label_map=label_map, prompt_name=prompt_name)
        answers, lengths, seconds = generate(inputs, model, tokenizer, generation)
        prompts = sent_prompts(tokenizer, inputs, columns)

        batch_rows = []
        for offset, answer in enumerate(answers):
            position = start + offset
            labels, info = parse.parse_labels(answer, aspects, codes)
            infos.append(info)
            preds.append(labels or None)
            total_tokens += lengths[offset]
            total_items += 1
            values = {
                "chỉ số": (row_index[position] if row_index else position),
                "split": split, "prompt": prompt_name, "kiểu đọc": info["kiểu đọc"],
                "đọc được": "có" if info["valid"] else "KHÔNG",
                records.REASON_COLUMN: info["reason"],
                "text": texts[position], "nhãn đúng": _as_json(golds[position]),
                "nhãn đoán": _as_json(labels), "token sinh": lengths[offset],
                "giây": round(seconds / len(chunk), 2),
                "có suy luận": "có" if info["has_reasoning"] else "không",
                "có <think>": "có" if info["had_thinking"] else "không",
                records.PROMPT_COLUMN: prompts[offset],
                records.ANSWER_COLUMN: answer.strip(),
            }
            # Ghi theo ĐÚNG thứ tự cột của đường chạy này: bảng của model encoder không có cột
            # prompt, nên chỗ này phải theo `columns` chứ không phải theo danh sách cứng.
            batch_rows.append([values[column] for column in columns])
        rows.extend(batch_rows)
        if store is not None:
            # Ghi NGAY sau mỗi lô: đây là thứ khiến việc chạy tiếp trở nên rẻ.
            store.append(batch_rows, columns)
        total_seconds += seconds
        if not quiet:
            print("    lô {}/{}: {} câu | {:.1f} giây | {:.1f} token sinh/giây".format(
                order, len(starts), len(chunk), seconds,
                (sum(lengths) / seconds) if seconds else 0.0))

    meta = {
        "split": split,
        "số mẫu": total_items,
        "token sinh": total_tokens,
        "token sinh TB": round(total_tokens / total_items, 1) if total_items else 0.0,
        "giây": round(total_seconds, 1),
        "token sinh/giây": round(total_tokens / total_seconds, 1) if total_seconds else 0.0,
        "lô": batch_size,
    }
    return rows, infos, preds, meta


def _as_json(labels):
    """Nhãn -> JSON gọn, giữ nguyên thứ tự khoá để đọc CSV bằng mắt được."""
    import json
    return json.dumps(labels, ensure_ascii=False)


def run_dir(version_id, tag):
    """Thư mục của MỘT lần chạy: `<thư mục kết quả đánh giá>/<mã phiên bản>/<hậu tố>/`.

    Mỗi cấu hình chạy (prompt, split, cách sinh) có thư mục riêng, nên tên file TRONG đó là tên
    cố định đọc từ `configs/paths.yaml` (`predictions.csv`, `metrics.json`) thay vì ghép chuỗi.
    Ghép chuỗi thì tên file là nguồn sự thật thứ hai, và nó lệch khỏi config lúc nào không biết.
    """
    return config.MODEL_EVAL_REPORT_DIR / str(version_id) / str(tag)


def write(rows, columns, out_dir, name=None):
    """Ghi một bảng CSV vào thư mục của lần chạy. Trả về đường dẫn file."""
    return utils.write_csv(rows, columns,
                           Path(out_dir) / (name or paths.pattern("predictions")))


def compute_dtype_name(bf16_supported):
    """Tên kiểu số dùng để nạp model: `bfloat16` nếu máy hỗ trợ, còn lại `float16`.

    VÌ SAO PHẢI CHỌN THEO MÁY: bf16 chỉ có từ Ampere trở lên (RTX 30xx, A100, L4). T4 của Colab là
    Turing nên KHÔNG có bf16; ép bf16 ở đó là hoặc lỗi, hoặc chậm bất thường mà không rõ nguyên nhân.
    fp16 thì GPU nào cũng có, nên nó là lựa chọn an toàn.
    """
    return "bfloat16" if bf16_supported else "float16"


def _model_dtype(torch):
    """`(kiểu số, tên)` để nạp model, chọn theo máy đang chạy. Xem `compute_dtype_name`.

    Phải hỏi bản torch mới bằng `including_emulation=False`: mặc định của tham số này là True, nghĩa
    là GPU KHÔNG có bf16 thật (T4 là Turing) vẫn trả về "có", vì torch chạy bf16 bằng giả lập phần
    mềm - đúng và chậm hơn nhiều. Đã gặp thật: lượt chạy trên T4 với torch 2.11 vẫn chọn bf16.
    """
    try:
        supported = bool(torch.cuda.is_available()
                         and torch.cuda.is_bf16_supported(including_emulation=False))
    except TypeError:
        # Bản torch cũ không có tham số này; hàm khi đó vốn chỉ kiểm hỗ trợ PHẦN CỨNG.
        try:
            supported = bool(torch.cuda.is_available() and torch.cuda.is_bf16_supported())
        except (AttributeError, RuntimeError):
            supported = False
    except (AttributeError, RuntimeError):
        # Thiếu hàm, hoặc driver hỏng: coi như không hỗ trợ.
        supported = False
    name = compute_dtype_name(supported)
    return getattr(torch, name), name


def _load_model(model_name, quantization, torch):
    """Nạp model, thử lần lượt các cách cho tới khi được; ghi lại cách ĐÃ dùng.

    Vì sao phải thử lần lượt thay vì chọn một cách: cách nạp phụ thuộc môi trường
    (`accelerate` có hay không, `transformers` bản nào dùng `dtype` hay `torch_dtype`), và
    một lỗi ở đây làm hỏng cả buổi chạy. Cách nào THÀNH CÔNG thì được ghi vào mục lục, nên
    kết quả vẫn truy vết được đã chạy bằng đường nào.
    """
    from transformers import AutoModelForCausalLM

    dtype, short = _model_dtype(torch)
    attempts = []
    if quantization is not None:
        attempts.append(("4-bit + device_map=auto ({})".format(short),
                         {"dtype": dtype, "quantization_config": quantization,
                          "device_map": "auto"}))
        attempts.append(("4-bit ({})".format(short),
                         {"dtype": dtype, "quantization_config": quantization}))
    attempts.append(("{} + device_map=auto".format(short), {"dtype": dtype, "device_map": "auto"}))
    attempts.append((short, {"dtype": dtype}))
    attempts.append(("{} (torch_dtype, bản transformers cũ)".format(short),
                     {"torch_dtype": dtype, "device_map": "auto"}))

    errors = []
    for label, kwargs in attempts:
        try:
            model = AutoModelForCausalLM.from_pretrained(model_name, **kwargs)
            model.eval()
            return model, label
        except Exception as exc:  # noqa: BLE001 - thử cách khác là chủ ý ở đây
            errors.append("{}: {}".format(label, type(exc).__name__))
    raise RuntimeError(
        "Không nạp được {} bằng cách nào. Đã thử: {}. Kiểm tra VRAM (6 GB cần lượng hóa "
        "4-bit) và đã cài `accelerate`/`bitsandbytes` chưa.".format(
            model_name, "; ".join(errors)))


def load(quant="auto", model_name=None):
    """Nạp model + tokenizer để SINH. Trả về (model, tokenizer, info).

    `quant`: "4bit" (bắt buộc phải có bitsandbytes) | "bf16" | "auto" (thử 4-bit trước).
    """
    torch = _require("torch")
    dtype, short = _model_dtype(torch)
    model_name = model_name or qwen.MODEL_NAME
    if model_name == qwen.MODEL_NAME:
        tokenizer = qwen.tokenizer()
    else:
        # Model khác (ví dụ chạy thử bằng model nhỏ cùng họ, hoặc model nạp từ thư mục cục
        # bộ): lấy ĐÚNG tokenizer của model đó, vì chat template và bộ token có thể khác -
        # dùng tokenizer của model khác thì đường vào model không còn là đường thật.
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_name)
    # Ép module qwen dùng chính tokenizer này: nếu không, phần dựng prompt (chat template)
    # vẫn đi tìm tokenizer mặc định trên Hugging Face - vừa thừa, vừa có thể lệch bản.
    _ensure_chat_template(tokenizer, model_name)
    qwen.use_tokenizer(tokenizer)
    # Xem quyết định (3) ở đầu file: bắt buộc để cắt đúng phần đã sinh khi chạy theo lô.
    tokenizer.padding_side = "left"

    info = {"model": model_name, "quant": None, "cách nạp": None, "thiết bị": None}
    quantization = None
    if quant in ("4bit", "auto"):
        try:
            import bitsandbytes  # noqa: F401
            from transformers import BitsAndBytesConfig
            quantization = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=dtype,
                bnb_4bit_use_double_quant=True)
        except ImportError as exc:
            if quant == "4bit":
                raise ImportError(
                    "Thiếu bitsandbytes nên không lượng hóa 4-bit được (model 4B cần ~8 GB "
                    "VRAM nếu để bf16). Cài bằng: pip install bitsandbytes\n"
                    "    (trên Windows, bản bitsandbytes >= 0.43 có sẵn bản dựng).") from exc

    model, how = _load_model(model_name, quantization, torch)
    # Ghi cả kiểu số THẬT đã dùng: cùng một cấu hình chạy trên T4 (fp16) và trên RTX 30xx (bf16) cho
    # ra hai phép đo khác nhau, nên bản ghi phải nói rõ đã chạy bằng kiểu nào.
    info["quant"] = "4-bit nf4 (tính bằng {})".format(short) \
        if quantization is not None and how.startswith("4-bit") else short
    info["cách nạp"] = how
    info["thiết bị"] = str(next(model.parameters()).device)
    if torch.cuda.is_available():
        info["gpu"] = torch.cuda.get_device_name(0)
        info["vram_gb"] = round(
            torch.cuda.memory_allocated() / 1024 ** 3, 2)
    # Xoá các thiết lập lấy mẫu thừa hưởng từ model card: để nguyên `temperature` cùng với
    # `do_sample=False` sẽ sinh cảnh báo và dễ khiến người đọc tưởng đang lấy mẫu.
    model.generation_config.temperature = None
    model.generation_config.top_p = None
    model.generation_config.top_k = None
    return model, tokenizer, info
