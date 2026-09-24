# -*- coding: utf-8 -*-
"""Model preprocessing cho Qwen3 (Qwen/Qwen3-4B-Instruct-2507).

Chuỗi bước:

    văn bản đã làm sạch
        -> PROMPT chỉ dẫn   (nội dung ở configs/prompts/<tên>.txt)
        -> chat template    (định dạng hội thoại của Qwen)
        -> tokenizer
        -> input_ids / attention_mask

Đây là mô hình sinh (không phải bộ phân loại), nên ta không "gắn đầu ra 7 lớp",
mà **mô tả bài toán bằng lời** rồi để model sinh ra JSON.

PROMPT NẰM Ở FILE, KHÔNG NẰM Ở ĐÂY
---
Nội dung prompt ở configs/prompts/<tên>.txt (cách nạp và kiểm tra: src/prompts.py);
model dùng cấu hình nào do configs/models/<model_id>.yaml quyết định (src/model_config.py);
Nhờ vậy đổi câu chỉ dẫn = thêm/sửa một file .txt rồi đổi một dòng YAML, không phải
sửa code; và vì prompt KHÔNG nằm trong configs/pipeline.yaml nên đổi prompt không
làm sinh ra mã phiên bản dữ liệu mới (xem src/versioning.py).
"""

from src import model_config, prompts
from src.preprocessing import loader

MODEL_NAME = "Qwen/Qwen3-4B-Instruct-2507"

# Tên file cấu hình trong configs/models/ (không cần đuôi .yaml); phải trùng `model_id`
# khai trong file đó. Bản 0.6B dùng cùng module này nhưng có file cấu hình riêng
# (configs/models/qwen3-0.6b.yaml).
CONFIG_NAME = "qwen3-4b-instruct-2507"

# Ngưỡng cắt input KHÔNG có hằng số ở đây nữa: nó là `preprocess.max_length` trong
# configs/models/qwen3-4b-instruct-2507.yaml = 1280. SỐ ĐO để chọn số đó: prompt CoT + 2 ví
# dụ few-shot tốn 861 token/review, review dài nhất 1.106 token, nên ngưỡng 1024 làm
# 4/12.302 mẫu train bị cắt mất phần đuôi - mà với prompt dạng chat, phần cuối chính là yêu
# cầu định dạng đầu ra. Nơi ĐO (token_stats) và nơi DÙNG (build_inputs) đều đọc qua `limit()`
# nên không thể lệch; lệch là mọi kết luận "input có bị cắt hay không" sai hết.

_TOKENIZER = None


def limit():
    """Ngưỡng cắt đang dùng: (giá trị, nguồn) - đọc từ file cấu hình của model."""
    return model_config.max_length(CONFIG_NAME)


# ---
# Prompt: prompt thuộc thí nghiệm, KHÔNG thuộc model
# ---


def config():
    """Cấu hình dùng chung của model (configs/models/<CONFIG_NAME>.yaml)."""
    return model_config.load(CONFIG_NAME)


def default_add_generation_prompt():
    """Giá trị mặc định của `add_generation_prompt`, lấy từ config của model.

    Đặt tên có `default_` vì trong `encode()`/`build_inputs()` còn một THAM SỐ cùng tên; gọi
    trùng tên sẽ bị che và không gọi được hàm.
    """
    return bool(model_config.preprocess(CONFIG_NAME)["add_generation_prompt"])


_PROMPTS = {}


def load_prompt(value, base_dir=None, examples=None, system=None):
    """Nạp prompt đã kiểm tra. Prompt thuộc THÍ NGHIỆM nên phải ghi rõ tên hoặc đường dẫn.

    Prompt trong thư viện dùng chung thì ghi tên (`absa_cot_v1`); prompt riêng của một thí nghiệm
    thì ghi đường dẫn tính từ thư mục thí nghiệm (`prompt.txt`) - xem `prompts.resolve`.

    Khoá nhớ của `prompts.load` gồm CẢ `base_dir`, `examples` và `system`: cùng một tên prompt
    nhưng hai thí nghiệm khai file ví dụ hoặc khối hệ thống khác nhau là hai cấu hình khác nhau,
    nhớ theo tên không thôi thì thí nghiệm thứ hai dùng nhầm cấu hình của thí nghiệm thứ nhất.
    """
    if not value:
        raise ValueError(
            "Thiếu prompt. Prompt nằm trong config của thí nghiệm, không lấy từ config "
            "model; hãy truyền tên prompt (ví dụ 'absa_cot_v1') hoặc đường dẫn tới file prompt "
            "của thí nghiệm."
        )
    # Các bước sau chỉ còn cầm một cái TÊN prompt, nên prompt đã nạp được tra theo "sổ" này. Chỉ
    # tra khi nơi gọi KHÔNG khai gì thêm: có `base_dir`/`examples`/`system` nghĩa là đang nạp một
    # cấu hình cụ thể, phải nạp đúng cấu hình đó.
    if base_dir is None and examples is None and system is None:
        found = _PROMPTS.get(str(value))
        if found is not None:
            return found
    return use_prompt(prompts.load(value, base_dir, examples, system))


def use_prompt(prompt):
    """Ghi nhớ một prompt ĐÃ NẠP, để các bước sau dùng lại đúng nó.

    VÌ SAO CẦN: các hàm dưới đây nhận `prompt_name` (một cái TÊN) chứ không nhận prompt, nên
    prompt nằm trong thư mục thí nghiệm - vốn không có trong thư viện dùng chung - sẽ không tìm
    lại được theo tên. Nạp một lần rồi ghi vào đây thì mọi bước sau dùng đúng prompt đó, thay vì
    mỗi nơi tự ghép lại đường dẫn.

    Prompt mang theo ĐƯỜNG DẪN ĐÃ GIẢI của file ví dụ và khối hệ thống, nên bước sau dựng prompt
    được mà không cần biết thư mục thí nghiệm ở đâu.
    """
    _PROMPTS[prompt.name] = prompt
    return prompt


def values(text, aspects=None, label_map=None, prompt=None):
    """Giá trị điền vào các ô nhớ của prompt, cho MỘT review.

    `aspects` và `label_map` mặc định lấy từ phiên bản dữ liệu MỚI NHẤT; nơi gọi
    (run_token_stats.py) truyền vào phiên bản cụ thể để prompt mô tả đúng bộ khía
    cạnh của chính phiên bản đang đo - dùng nhầm phiên bản là prompt sai mà nhìn vào
    vẫn tưởng đúng.

    Chỉ tính những ô nhớ mà prompt THẬT SỰ dùng: prompt không có {example} thì không
    phải sinh ví dụ, prompt không có {examples} thì không đọc file few-shot.
    """
    prompt = prompt or load_prompt()
    needed = set(prompt.placeholders)

    result = {"text": text}
    if needed & {"aspects", "label_guide", "example", "examples"}:
        label_map = label_map if label_map is not None else loader.load_label_map()
        aspects = list(aspects or label_map["aspects"])
        if "aspects" in needed:
            result["aspects"] = ", ".join(aspects)
        if "label_guide" in needed:
            result["label_guide"] = prompts.label_guide(label_map)
        if "example" in needed:
            result["example"] = "{" + ", ".join(
                '"{}": 0'.format(aspect) for aspect in aspects) + "}"
        if "examples" in needed:
            # Đọc theo đường dẫn prompt ĐÃ GIẢI lúc nạp: các bước sau chỉ còn biết TÊN prompt nên
            # không tự giải lại đường dẫn được (xem prompts.Prompt.examples_text).
            result["examples"] = prompt.examples_text()
    if "system_prompt" in needed:
        result["system_prompt"] = prompt.system_text()
    return result


def build_prompt(text, aspects=None, label_map=None, prompt_name=None):
    """Câu lệnh chỉ dẫn hoàn chỉnh cho một review, ở dạng ĐỌC ĐƯỢC.

    Dùng để xem/in ra prompt đang gửi cho model; KHÔNG dùng cho việc đo token, vì việc
    đó cần cả chat template (xem `encode`). Prompt nhiều lượt được in thành bản ghi có
    nhãn vai (SYSTEM/USER/ASSISTANT) - xem `Prompt.transcript` để biết vì sao không in
    các dòng đánh dấu.
    """
    template = load_prompt(prompt_name)
    return template.transcript(values(text, aspects, label_map, template))


def conversations(texts, aspects=None, label_map=None, prompt_name=None):
    """Bọc mỗi review thành hội thoại đúng dạng Qwen3 cần.

    Prompt một lượt (không có dòng đánh dấu) cho ra MỘT message người dùng như trước;
    prompt có [SYSTEM]/[USER]/[ASSISTANT] cho ra hội thoại nhiều lượt (few-shot/CoT) -
    hợp đồng file prompt ghi ở src/prompts.py.
    """
    template = load_prompt(prompt_name)
    return [
        template.messages(values(text, aspects, label_map, template))
        for text in texts
    ]



def use_tokenizer(found):
    """Ép dùng MỘT tokenizer cụ thể cho mọi hàm của module này.

    Vì sao cần: đường vào model và đường vào tokenizer phải là MỘT. Khi chạy với model nạp
    từ thư mục cục bộ (`run_qwen_eval.py --model <thư mục>`), nếu prompt vẫn đi qua
    `tokenizer()` mặc định thì hai chuyện xấu xảy ra: (a) máy phải tải tokenizer từ HF dù
    model đã có sẵn trên đĩa, (b) tokenizer có thể là của BẢN KHÁC với model đang chạy -
    chat template khác nhau thì phép so sánh mất ý nghĩa mà không có gì báo lỗi.
    """
    global _TOKENIZER
    _TOKENIZER = found
    return found


def tokenizer():
    """Nạp tokenizer (kèm chat template) của Qwen3 một lần duy nhất."""
    global _TOKENIZER
    if _TOKENIZER is None:
        try:
            from transformers import AutoTokenizer
        except ImportError as exc:  # pragma: no cover - phụ thuộc môi trường
            raise ImportError(
                "Thiếu thư viện transformers. Cài bằng:\n"
                "    pip install transformers torch"
            ) from exc
        _TOKENIZER = AutoTokenizer.from_pretrained(MODEL_NAME)
    return _TOKENIZER


def _check_encoded(rows):
    """Chặn input RỖNG - dấu hiệu tokenizer không có chat template.

    Nếu tokenizer thiếu chat template thì `apply_chat_template` trả về chuỗi RỖNG mà KHÔNG
    báo lỗi, và lỗi thật chỉ hiện ra ở tận `model.generate` với thông báo chẳng liên quan
    (`attention_mask[:, -1]` ... dimension of size 0). Kiểm ở đây để thông báo nói đúng
    nguyên nhân, ngay tại chỗ gây ra nó.
    """
    if len(rows) == 0 or not isinstance(rows[0], (list, tuple)):
        raise TypeError(
            "encode() phải trả về list[list[int]], đang nhận {}.".format(type(rows).__name__))
    empty = [index for index, row in enumerate(rows) if len(row) == 0]
    if empty:
        raise ValueError(
            "encode() cho ra input RỖNG ở {} mẫu (vị trí {}). Dấu hiệu tokenizer KHÔNG có "
            "chat template - kiểm `tokenizer.chat_template`, và xem "
            "src/evaluation/runner._ensure_chat_template để biết cách nạp từ file "
            "chat_template.jinja.".format(len(empty), empty[:5]))
    return rows


def encode(texts, add_generation_prompt=None, aspects=None, label_map=None,
           prompt_name=None):
    """Chuỗi id token của prompt ĐÃ bọc chat template (CHƯA pad, CHƯA cắt).

    Không cần torch, nên dùng được cho việc ĐO độ dài input thật trước khi huấn
    luyện (xem src/preprocessing/token_stats.py). Kết quả là list[list[int]].

    `add_generation_prompt` mặc định lấy từ `preprocess.add_generation_prompt` của config model
    - giá trị này phải GIỐNG giá trị lúc huấn luyện, nếu không số token đo được sẽ lệch đúng
    một lượt hội thoại.
    """
    if add_generation_prompt is None:
        add_generation_prompt = default_add_generation_prompt()
    return _check_encoded(tokenizer().apply_chat_template(
        conversations(texts, aspects, label_map, prompt_name),
        tokenize=True,
        add_generation_prompt=add_generation_prompt,
        return_dict=False,      # trả về list[list[int]] thay vì BatchEncoding
    ))


def build_inputs(texts, max_length=None, add_generation_prompt=None,
                 aspects=None, label_map=None, prompt_name=None):
    """Chuyển danh sách văn bản thành input cho Qwen3.

    Trả về dict của tokenizer. Nhờ `apply_chat_template`, prompt được bọc đúng
    định dạng hội thoại mà Qwen3 yêu cầu.

    `max_length` để None nghĩa là dùng ngưỡng ĐANG CÓ HIỆU LỰC (`limit()`: YAML của model
    > hằng số MAX_LENGTH) - cũng đúng giá trị mà token_stats dùng để đo, nên hai bước
    không thể lệch nhau. Truyền số cụ thể khi muốn ép cho một lần gọi.
    """
    if add_generation_prompt is None:
        add_generation_prompt = default_add_generation_prompt()
    if max_length is None:
        max_length = limit()[0]
    return tokenizer().apply_chat_template(
        conversations(texts, aspects, label_map, prompt_name),
        tokenize=True,
        add_generation_prompt=add_generation_prompt,
        padding=True,
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )


def info(prompt_name=None):
    """Thông tin để TRUY VẾT số liệu đo được: tokenizer, từ vựng, prompt, ngưỡng cắt.

    Nơi gọi truyền tên prompt đang dùng để dòng số liệu ghi đúng prompt nào đã sinh
    ra nó (`--prompt X` khác với prompt trong config).

    Có cả thông tin FILE VÍ DỤ (`examples`, `examples_sha`, `examples_count`) vì bộ ví dụ
    few-shot là một phần của cấu hình thí nghiệm: cùng một prompt mà đi với 0/1/2 ví dụ là
    ba thí nghiệm khác nhau, trong khi `prompt_sha` của cả ba lại GIỐNG NHAU (nó chỉ tính
    nội dung file prompt). Không ghi mã của file ví dụ thì ba thí nghiệm mang cùng dấu vết.
    Khối hệ thống dùng chung cũng vậy, nên nó có `system_sha` riêng.
    """
    found = tokenizer()
    template = load_prompt(prompt_name)
    value, source = limit()
    examples = template.examples_info() or {}
    system = template.system_info() or {}
    return {
        "tokenizer": type(found).__name__,
        "segmenter": "none",
        "vocab": found.vocab_size,
        "unk_id": found.unk_token_id,
        "prompt": template.name,
        "prompt_sha": template.sha,
        "examples": examples.get("file"),
        "examples_sha": examples.get("sha"),
        "examples_count": examples.get("examples") or None,
        "system": system.get("file"),
        "system_sha": system.get("sha"),
        "max_length": value,
        "max_length_source": source,
    }

