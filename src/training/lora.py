# -*- coding: utf-8 -*-
"""LoRA (peft) trên model encoder, đầu phân loại riêng cho mỗi khía cạnh.

VÌ SAO KHÔNG FULL FINE-TUNE
Hai encoder nhỏ như PhoBERT và ViSoBERT chỉ học qua LoRA/QLoRA (docs/00_workflow/02_rules.md). LoRA
giữ nguyên trọng số gốc và chỉ học thêm ma trận hạng thấp, nên checkpoint nhẹ (vài MB) và hợp với
GPU 6 GB hoặc Colab T4.

NHÃN ĐƯA VÀO MODEL
Mỗi khía cạnh là MỘT bài toán con của cùng một review, nên đầu ra là `khía cạnh × mã nhãn` và
những ô bị loại (neutral khi `neutral_policy: drop`) mang `mask = 0`: chúng không vào loss và
không được chấm, nhưng KHÔNG làm mất các khía cạnh khác của cùng review
(xem `src/preprocessing/loader.project_multi_head`).

CHECKPOINT
    model/last   adapter + optimizer.pt + scheduler.pt + trainer_state.json  -> đủ để chạy tiếp
    model/best   CHỈ adapter + head.pt + head_config.json                    -> để suy luận
`keep_last_k` giữ bao nhiêu ảnh chụp `model/checkpoint-<bước>`; `delete_intermediate` xoá ảnh chụp
cũ ngay sau mỗi lần lưu để khỏi đầy Drive.

`torch`, `transformers`, `peft` được import BÊN TRONG hàm: CI không cài chúng mà vẫn phải import
được module này để gọi `check()`.
"""

import json
import math
import random
import re
import shutil
from pathlib import Path

from src import model_config, paths, utils
from src.training import encoders

NAME = "lora"
DESCRIPTION = "LoRA (peft) trên model encoder, một đầu phân loại cho mỗi khía cạnh."

# Khoá bắt buộc của lượt huấn luyện, chia theo NƠI KHAI. Thiếu khoá nào thì báo đúng khoá đó kèm nơi
# khai: giá trị mặc định trong code là thứ âm thầm khác với giá trị đang chạy.
REQUIRED_MODEL = ("lora.target_modules", "preprocess.max_length", "inference.batch_size",
                  "inference.dtype")
REQUIRED_SHARED = ("trainer", "lora.r", "lora.alpha", "lora.dropout", "lr", "batch", "epochs",
                   "grad_accum", "weight_decay", "checkpoints.every_n_steps",
                   "checkpoints.keep_last_k", "checkpoints.save_last", "checkpoints.save_best",
                   "checkpoints.delete_intermediate")


def where(key):
    """Nơi khai một khoá, để thông báo lỗi chỉ đúng file mà người đọc phải mở."""
    if str(key) in REQUIRED_MODEL:
        return "file cấu hình của model, khoá `{}` (docs/05_config/04_models.md)".format(key)
    return ("file cấu hình huấn luyện dùng chung, khoá `{}` "
            "(docs/05_config/05_experiments_shared.md)".format(key))

# Kiểu số hợp lệ. `auto` để mã chọn theo máy: T4 (Turing) không có bf16, nên chọn fp16.
DTYPES = ("auto", "float16", "bfloat16", "float32")

HEAD_CONFIG = "head_config.json"
HEAD_WEIGHTS = "head.pt"
STATE_FILE = "trainer_state.json"
OPTIMIZER_FILE = "optimizer.pt"
SCHEDULER_FILE = "scheduler.pt"

SNAPSHOT_PREFIX = "checkpoint-"


class TrainingError(Exception):
    """Thiếu khoá cấu hình, sai kiến trúc, hoặc không nạp/ghi được thứ mà huấn luyện cần."""


def _get(config, key, note=None):
    """Đọc một khoá dạng dấu chấm trong config đã hợp nhất; thiếu là LỖI kèm nơi khai."""
    node = config
    for part in str(key).split("."):
        if not isinstance(node, dict) or part not in node:
            raise TrainingError(
                "Thiếu khoá '{}' trong cấu hình đã hợp nhất. Khai ở {}.".format(
                    key, note or where(key)))
        node = node[part]
    if node is None or node == "":
        raise TrainingError("Khoá '{}' đang để trống. Khai ở {}.".format(key, note or where(key)))
    return node


def settings(config, model_id):
    """Cấu hình HIỆU LỰC của một lượt huấn luyện, đã kiểm đủ khoá.

    Trả về dict phẳng để ghi vào `run.log`/`run_meta.json`: cùng một lượt chạy không thể có hai
    cách hiểu về số epoch hay hệ số LoRA.

    Khoá thiếu được báo theo ĐÚNG thứ tự khai trong dict dưới đây, để thông báo lỗi ổn định và
    trỏ đúng file mà người đọc phải mở.
    """
    found = {
        "trainer": str(_get(config, "trainer")).strip(),
        "lora_r": int(_get(config, "lora.r")),
        "lora_alpha": int(_get(config, "lora.alpha")),
        "lora_dropout": float(_get(config, "lora.dropout")),
        "target_modules": [str(item) for item in _get(config, "lora.target_modules")],
        "lr": float(_get(config, "lr")),
        "batch": int(_get(config, "batch")),
        "epochs": int(_get(config, "epochs")),
        "grad_accum": int(_get(config, "grad_accum")),
        "weight_decay": float(_get(config, "weight_decay")),
        "every_n_steps": int(_get(config, "checkpoints.every_n_steps")),
        "keep_last_k": int(_get(config, "checkpoints.keep_last_k")),
        "save_last": bool(_get(config, "checkpoints.save_last")),
        "save_best": bool(_get(config, "checkpoints.save_best")),
        "delete_intermediate": bool(_get(config, "checkpoints.delete_intermediate")),
        "max_length": int(_get(config, "preprocess.max_length")),
        "eval_batch": int(_get(config, "inference.batch_size")),
        "dtype": str(_get(config, "inference.dtype")).strip().lower(),
        "quantization": str(((config.get("inference") or {}).get("quantization")) or "none"),
        "model_id": model_id,
        "checkpoint": model_config.checkpoint(model_id),
    }
    if found["dtype"] not in DTYPES:
        raise TrainingError(
            "`inference.dtype` là {!r} nhưng chỉ nhận {}.".format(found["dtype"], ", ".join(DTYPES)))
    return found



def check(config, model_id=None):
    """Kiểm lượt huấn luyện có chạy được không. Trả về danh sách việc phải sửa (rỗng là chạy được)."""
    import importlib.util

    problems = []
    if not (config or {}).get("enabled"):
        return ["lora: `training.enabled: false` mà vẫn gọi huấn luyện"]
    try:
        encoders.get(model_id)
    except encoders.EncoderError as exc:
        problems.append("lora: {}".format(exc))
    try:
        found = settings(config, model_id)
    except (TrainingError, model_config.ModelConfigError) as exc:
        # Thiếu khoá hoặc thiếu file cấu hình model: đó là việc phải sửa, không phải lỗi làm sập
        # preflight (preflight gom hết rồi báo một lần).
        return problems + ["lora: {}".format(exc)]
    if found["trainer"] != NAME:
        problems.append("lora: `trainer` là {!r} nhưng đang gọi trình huấn luyện {!r}".format(
            found["trainer"], NAME))
    if not found["target_modules"]:
        problems.append("lora: `lora.target_modules` rỗng")
    for name in ("torch", "transformers", "peft"):
        if importlib.util.find_spec(name) is None:
            problems.append(
                "lora: chưa cài thư viện `{}` (pip install -r requirements.txt)".format(name))
    if found["quantization"] == "4bit" and importlib.util.find_spec("bitsandbytes") is None:
        problems.append("lora: `inference.quantization: 4bit` nhưng máy chưa có `bitsandbytes`")
    return problems


# ---
# Đường dẫn checkpoint và trạng thái
# ---


def checkpoint_dir(out_dir, key="ckpt_last"):
    """Thư mục checkpoint trong thư mục kết quả: `model/last` hoặc `model/best`.

    Tên lấy từ `configs/paths.yaml`, nên đổi tên thư mục không phải sửa code.
    """
    return Path(out_dir) / paths.pattern(key)


def snapshots(out_dir):
    """Các ảnh chụp trung gian `model/checkpoint-<bước>`, sắp theo số bước tăng dần."""
    parent = checkpoint_dir(out_dir).parent
    if not parent.is_dir():
        return []
    found = []
    for path in parent.iterdir():
        matched = re.match(r"^{}(\d+)$".format(re.escape(SNAPSHOT_PREFIX)), path.name)
        if path.is_dir() and matched:
            found.append((int(matched.group(1)), path))
    return [path for _step, path in sorted(found)]


def state_of(directory):
    """Đọc `trainer_state.json` của một checkpoint; trả về {} nếu chưa có hoặc file hỏng."""
    path = Path(directory) / STATE_FILE
    if not path.is_file():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle) or {}
    except (OSError, ValueError):
        return {}


def resume_state(out_dir, fingerprint, require=True):
    """Trạng thái của `model/last` nếu nó thuộc ĐÚNG lượt chạy này; None nếu không dùng lại được.

    Điều kiện là vân tay ba giá trị (cấu hình, dữ liệu, commit) y như lúc checkpoint được ghi,
    cùng điều kiện với `src/resume.py`. Khác thì chạy lại từ đầu thay vì trộn hai phép đo.
    """
    directory = checkpoint_dir(out_dir, "ckpt_last")
    state = state_of(directory)
    if not state:
        return None
    if dict(state.get("fingerprint") or {}) != dict(fingerprint or {}):
        if require:
            raise TrainingError(
                "Checkpoint {} thuộc một lượt chạy KHÁC (cấu hình hoặc dữ liệu đã đổi). Muốn chạy "
                "tiếp thì khôi phục đúng bản code và cấu hình cũ; muốn chạy mới thì xoá thư mục "
                "kết quả {}.".format(utils.rel(directory), utils.rel(out_dir)))
        return None
    return state


def write_state(directory, state):
    """Ghi `trainer_state.json` của một checkpoint. Trả về đường dẫn file."""
    return Path(utils.write_json(state, Path(directory) / STATE_FILE))


# ---
# Chuẩn bị dữ liệu và mô hình
# ---


def describe():
    """Một dòng mô tả cách huấn luyện này, để in ra khi cần."""
    return "{} | đầu phân loại riêng cho mỗi khía cạnh".format(DESCRIPTION)


def device_of():
    """Thiết bị sẽ dùng: `cuda` nếu có GPU, còn lại CPU."""
    import torch

    return "cuda" if torch.cuda.is_available() else "cpu"


def torch_dtype(name, device):
    """Kiểu số THẬT SỰ dùng sau khi giải `auto`.

    `auto` = bf16 khi máy hỗ trợ (Ampere trở lên), fp16 khi không (T4 là Turing), fp32 trên CPU -
    chọn sai ở T4 làm mất tốc độ, chọn bf16 trên CPU làm sai số học.
    """
    import torch

    if name == "float32":
        return torch.float32
    if name == "float16":
        return torch.float16
    if name == "bfloat16":
        return torch.bfloat16
    if device == "cuda":
        return torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    return torch.float32


def encode(module, texts, max_length, batch=64):
    """Mọi văn bản đã tách từ (nếu model cần), đã cắt và đã pad: hai tensor cùng số dòng.

    Dùng `build_inputs()` của chính module model, nên ngưỡng cắt ở đây đúng bằng ngưỡng mà
    `token_stats` đã đo - không có đường thứ hai để lệch nhau.
    """
    import torch

    ids, masks = [], []
    for start in range(0, len(texts), batch):
        chunk = module.build_inputs(list(texts[start:start + batch]), max_length=max_length)
        ids.append(chunk["input_ids"])
        masks.append(chunk["attention_mask"])
    if not ids:
        empty = torch.empty((0, 0), dtype=torch.long)
        return empty, empty
    return torch.cat(ids, dim=0), torch.cat(masks, dim=0)


def targets_from(labels, codes):
    """Đổi MÃ NHÃN của dataset thành CHỈ SỐ lớp của đầu phân loại.

    Ô bị loại (`mask = 0`, ví dụ neutral khi `neutral_policy: drop`) không vào loss, nhưng chỉ số
    của nó vẫn phải hợp lệ để tensor không lỗi - nên nó được gán lớp 0 rồi bị mask loại.
    """
    import torch

    index = {int(code): position for position, code in enumerate(codes)}
    return torch.tensor([[index.get(int(code), 0) for code in row] for row in labels],
                        dtype=torch.long)


def build_classes():
    """Định nghĩa lớp mô hình và dataset. Torch chỉ được import ở ĐÂY, không ở cấp module."""
    import torch
    from torch import nn

    class MultiHeadClassifier(nn.Module):
        """Encoder + một đầu tuyến tính cho mỗi khía cạnh (khía cạnh × mã nhãn).

        Vì sao nhiều đầu thay vì một: bảy khía cạnh độc lập nhau, gộp thành một bài toán nhiều lớp
        sẽ buộc model chọn đúng MỘT khía cạnh cho mỗi review.
        """

        def __init__(self, encoder, n_aspects, n_codes):
            super().__init__()
            self.encoder = encoder
            self.n_aspects = int(n_aspects)
            self.n_codes = int(n_codes)
            self.head = nn.Linear(int(encoder.config.hidden_size), self.n_aspects * self.n_codes)

        def forward(self, input_ids, attention_mask):
            output = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
            # Token đầu tiên là đại diện cả câu (<s> của PhoBERT và của XLM-R/ViSoBERT).
            return self.head(output.last_hidden_state[:, 0]).view(
                -1, self.n_aspects, self.n_codes)

        def loss(self, logits, targets, mask):
            """Cross-entropy trên từng ô ĐƯỢC TÍNH: `mask = 0` nghĩa là ô đó không có nhãn dùng được."""
            flat = nn.functional.cross_entropy(
                logits.reshape(-1, self.n_codes), targets.reshape(-1), reduction="none")
            weights = mask.reshape(-1).to(flat.dtype)
            return (flat * weights).sum() / weights.sum().clamp(min=1.0)

    class Rows(torch.utils.data.Dataset):
        """Các dòng đã mã hoá sẵn, để không tách từ lại ở mỗi epoch."""

        def __init__(self, input_ids, attention_mask, targets, mask):
            self.items = list(zip(input_ids, attention_mask, targets, mask))

        def __len__(self):
            return len(self.items)

        def __getitem__(self, position):
            ids, attention, target, keep = self.items[position]
            return {"input_ids": ids, "attention_mask": attention, "labels": target, "mask": keep}

    return MultiHeadClassifier, Rows




def build_model(found, device, n_aspects=None, n_codes=None, adapter_dir=None, source=None):
    """Nạp encoder, gắn LoRA và đầu phân loại. Trả về `(model, head)`.

    `adapter_dir` để nạp lại một checkpoint đã lưu (suy luận hoặc chạy tiếp): khi đó số khía cạnh và
    số lớp đọc từ `head_config.json` của chính checkpoint đó, vì dùng lại checkpoint cho một bài
    toán khác là lỗi im lặng nguy hiểm nhất của đường huấn luyện.
    """
    import torch
    from peft import LoraConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training
    from transformers import AutoModel

    MultiHeadClassifier, _Rows = build_classes()
    if adapter_dir is not None:
        head_config = read_head_config(adapter_dir)
        n_aspects = int(head_config["n_aspects"])
        n_codes = int(head_config["n_codes"])
    if not n_aspects or not n_codes:
        raise TrainingError(
            "Thiếu `n_aspects`/`n_codes`: số đầu và số lớp của đầu phân loại phải biết trước "
            "(suy từ bộ khía cạnh và không gian nhãn của thí nghiệm).")

    kwargs = {}
    if device == "cuda":
        kwargs["torch_dtype"] = torch_dtype(found["dtype"], device)
    if str(found.get("quantization") or "none") == "4bit":
        if device != "cuda":
            raise TrainingError("Lượng hoá 4-bit cần CUDA; máy này không có GPU dùng được.")
        from transformers import BitsAndBytesConfig

        kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch_dtype(found["dtype"], device))
        kwargs["device_map"] = {"": 0}
    encoder = AutoModel.from_pretrained(source or found["source"], **kwargs)
    classifier = MultiHeadClassifier(encoder, n_aspects, n_codes)

    if adapter_dir is not None:
        model = PeftModel.from_pretrained(classifier, str(adapter_dir))
        classifier.head.load_state_dict(
            torch.load(str(Path(adapter_dir) / HEAD_WEIGHTS), map_location="cpu"))
        return model, classifier.head

    if str(found.get("quantization") or "none") == "4bit":
        classifier.encoder = prepare_model_for_kbit_training(classifier.encoder)
    model = get_peft_model(classifier, LoraConfig(
        r=found["lora_r"], lora_alpha=found["lora_alpha"], lora_dropout=found["lora_dropout"],
        target_modules=list(found["target_modules"]), bias="none", task_type="FEATURE_EXTRACTION"))
    return model, classifier.head


def read_head_config(directory):
    """Đọc `head_config.json` của một checkpoint: số khía cạnh, số lớp, thứ tự khía cạnh."""
    path = Path(directory) / HEAD_CONFIG
    if not path.is_file():
        raise TrainingError(
            "Checkpoint {} thiếu {}. Không biết nó được huấn luyện với bộ khía cạnh nào thì không "
            "dùng lại được.".format(utils.rel(directory), HEAD_CONFIG))
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle) or {}


def save_checkpoint(model, head, directory, state, optimizer=None, scheduler=None,
                    adapter_only=False):
    """Ghi một checkpoint. `adapter_only` dùng cho `model/best` (chỉ để suy luận, nhẹ nhất)."""
    import torch

    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(directory))
    torch.save(head.state_dict(), str(directory / HEAD_WEIGHTS))
    utils.write_json(dict(state.get("head_config") or {}), directory / HEAD_CONFIG)
    if not adapter_only:
        if optimizer is not None:
            torch.save(optimizer.state_dict(), str(directory / OPTIMIZER_FILE))
        if scheduler is not None:
            torch.save(scheduler.state_dict(), str(directory / SCHEDULER_FILE))
    return write_state(directory, state)


def prune_snapshots(out_dir, keep):
    """Xoá ảnh chụp trung gian cũ, chỉ giữ `keep` cái gần nhất (xem `keep_last_k`)."""
    keep = int(keep)
    found = snapshots(out_dir)
    old = found[:-keep] if keep > 0 else found
    removed = []
    for path in old:
        shutil.rmtree(path, ignore_errors=True)
        removed.append(path.name)
    return removed


def masked_loss(logits, targets, mask, n_codes):
    """Cross-entropy trên từng ô ĐƯỢC TÍNH: ô `mask = 0` không vào tử số lẫn mẫu số.

    Mẫu số là số ô được tính (không phải số ô), nên một review chỉ nhắc một khía cạnh vẫn đóng góp
    đúng trọng số của nó thay vì bị pha loãng bởi sáu khía cạnh không nhắc.
    """
    import torch

    flat = torch.nn.functional.cross_entropy(
        logits.reshape(-1, int(n_codes)), targets.reshape(-1), reduction="none")
    weights = mask.reshape(-1).to(flat.dtype)
    return (flat * weights).sum() / weights.sum().clamp(min=1.0)


def parameter_counts(model):
    """(số tham số học, tổng số tham số) - để biết LoRA nhỏ cỡ nào so với model gốc."""
    total = sum(item.numel() for item in model.parameters())
    trainable = sum(item.numel() for item in model.parameters() if item.requires_grad)
    return trainable, total


def measure(model, module, data, found, codes, device):
    """Độ chính xác theo Ô của một tập (dùng `val` để chọn `model/best`).

    Mỗi ô là một cặp (review, khía cạnh) được tính, nên đây là con số cùng họ với chỉ số của phần
    chấm điểm; ô bị loại không vào mẫu số.
    """
    import torch

    if not data or not data.get("texts"):
        return None
    ids, masks = encode(module, data["texts"], found["max_length"])
    targets = targets_from(data["labels"], codes)
    keep = torch.tensor(data["mask"], dtype=torch.float32)
    correct, total = 0, 0
    was_training = model.training
    model.eval()
    with torch.no_grad():
        for start in range(0, ids.size(0), found["eval_batch"]):
            stop = start + found["eval_batch"]
            logits = model(input_ids=ids[start:stop].to(device),
                           attention_mask=masks[start:stop].to(device))
            guess = logits.argmax(dim=-1).cpu()
            weight = keep[start:stop]
            correct += int(((guess == targets[start:stop]) * weight).sum().item())
            total += int(weight.sum().item())
    if was_training:
        model.train()
    return {"accuracy_cell": round(correct / total, 6) if total else None,
            "cells": total, "correct": correct}

    return removed


def fit(config, model_id, out_dir, train, val, aspects, codes, fingerprint, seed=42, source=None,
        log=None):
    """Huấn luyện LoRA rồi trả về số liệu của lượt huấn luyện.

    `train` và `val` là dict `{"texts": [...], "labels": [[mã nhãn]], "mask": [[0/1]]}` với nhãn ĐÃ
    CHIẾU sang không gian nhãn của thí nghiệm (`src/preprocessing/loader.project_multi_head`).

    Chạy tiếp: nếu `model/last` có vân tay y như lượt này thì nạp lại adapter + optimizer +
    scheduler rồi đi tiếp từ epoch đã ghi. Khác vân tay thì báo lỗi, không trộn hai phép đo.
    """
    import time

    import torch
    from torch.utils.data import DataLoader
    from transformers import get_linear_schedule_with_warmup

    found = settings(config, model_id)
    module = encoders.get(model_id)
    device = device_of()
    found["device"] = device
    found["source"] = source or found["checkpoint"]
    found["dtype_used"] = str(torch_dtype(found["dtype"], device)).replace("torch.", "")

    random.seed(seed)
    torch.manual_seed(seed)
    if device == "cuda":
        torch.cuda.manual_seed_all(seed)

    head_config = {"n_aspects": len(aspects), "n_codes": len(codes),
                   "codes": [int(code) for code in codes],
                   "aspects": [str(name) for name in aspects]}
    state = resume_state(out_dir, fingerprint, require=False)
    adapter = checkpoint_dir(out_dir, "ckpt_last") if state else None
    if adapter is not None and dict(read_head_config(adapter)) != head_config:
        raise TrainingError(
            "Checkpoint {} thuộc một bài toán KHÁC (bộ khía cạnh hoặc số lớp khác). Xoá thư mục kết "
            "quả {} rồi chạy lại nếu muốn huấn luyện bài toán này.".format(
                utils.rel(adapter), utils.rel(out_dir)))

    model, head = build_model(found, device, n_aspects=len(aspects), n_codes=len(codes),
                              adapter_dir=adapter, source=found["source"])
    if device == "cuda":
        model = model.to(device)
    trainable, total = parameter_counts(model)

    ids, masks = encode(module, train["texts"], found["max_length"])
    targets = targets_from(train["labels"], codes)
    keep = torch.tensor(train["mask"], dtype=torch.float32)
    _Multi, Rows = build_classes()
    loader = DataLoader(Rows(ids, masks, targets, keep), batch_size=found["batch"], shuffle=True,
                        generator=torch.Generator().manual_seed(seed))
    optimizer = torch.optim.AdamW([item for item in model.parameters() if item.requires_grad],
                                  lr=found["lr"], weight_decay=found["weight_decay"])
    per_epoch = max(1, math.ceil(len(loader) / found["grad_accum"]))
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=0, num_training_steps=max(1, per_epoch * found["epochs"]))

    start_epoch, step, best = 0, 0, None
    if state:
        folder = checkpoint_dir(out_dir, "ckpt_last")
        if (folder / OPTIMIZER_FILE).is_file():
            optimizer.load_state_dict(
                torch.load(str(folder / OPTIMIZER_FILE), map_location="cpu"))
        if (folder / SCHEDULER_FILE).is_file():
            scheduler.load_state_dict(
                torch.load(str(folder / SCHEDULER_FILE), map_location="cpu"))
        start_epoch = int(state.get("epoch") or 0)
        step = int(state.get("step") or 0)
        best = state.get("best") or None
        if log is not None:
            log.step("chạy tiếp từ checkpoint: epoch {} (đã {} bước)".format(start_epoch, step))


    history = []
    started = time.time()
    model.train()
    pending = 0

    def record(epoch_done, metrics, snapshot):
        """Ghi trạng thái hiện tại: `model/best` khi tốt hơn, và ảnh chụp khi được yêu cầu."""
        nonlocal best
        improved = False
        value = (metrics or {}).get("accuracy_cell")
        if value is not None:
            improved = best is None or value > float(best.get("accuracy_cell") or -1)
            if improved:
                best = {"epoch": epoch_done, "step": step, **metrics}
                if found["save_best"]:
                    save_checkpoint(model, head, checkpoint_dir(out_dir, "ckpt_best"),
                                    payload(epoch_done, metrics), adapter_only=True)
        if snapshot:
            folder = checkpoint_dir(out_dir).parent / "{}{}".format(SNAPSHOT_PREFIX, step)
            save_checkpoint(model, head, folder, payload(epoch_done, metrics), optimizer, scheduler)
            if found["delete_intermediate"]:
                prune_snapshots(out_dir, found["keep_last_k"])
        return improved

    def payload(epoch_done, metrics):
        """Nội dung `trainer_state.json`: vân tay, chỗ đã đi tới, và bài toán đang học."""
        return {"head_config": head_config, "fingerprint": dict(fingerprint), "epoch": epoch_done,
                "step": step, "best": best, "metrics": metrics, "source": found["source"],
                "settings": found}

    for epoch in range(start_epoch, found["epochs"]):
        for index, batch in enumerate(loader):
            batch = {key: value.to(device) for key, value in batch.items()}
            logits = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"])
            loss = masked_loss(logits, batch["labels"], batch["mask"], len(codes))
            (loss / found["grad_accum"]).backward()
            pending += 1
            if pending < found["grad_accum"]:
                continue
            torch.nn.utils.clip_grad_norm_(
                [item for item in model.parameters() if item.requires_grad], 1.0)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad(set_to_none=True)
            pending = 0
            step += 1
            if step % found["every_n_steps"]:
                continue
            metrics = measure(model, module, val, found, codes, device)
            history.append({"step": step, "epoch": epoch + 1, "loss": round(float(loss), 6),
                            "lr": round(float(scheduler.get_last_lr()[0]), 8), "val": metrics})
            improved = record(epoch + 1, metrics, snapshot=True)
            message = "bước {} | loss {:.4f} | val {} | {}".format(
                step, float(loss), value_text(metrics),
                "đã lưu model/best" if improved else "chưa tốt hơn")
            print("  " + message)
            if log is not None:
                log.step(message)

        metrics = measure(model, module, val, found, codes, device)
        record(epoch + 1, metrics, snapshot=False)
        save_checkpoint(model, head, checkpoint_dir(out_dir, "ckpt_last"), payload(epoch + 1, metrics),
                        optimizer, scheduler)
        print("hết epoch {}/{}: {} bước, val {}".format(
            epoch + 1, found["epochs"], step, value_text(metrics)))

    seconds = round(time.time() - started, 1)
    if found["save_best"] and best is None:
        message = ("Không có `val` để chọn `model/best`: khai `data.roles.val` khi huấn luyện. "
                   "Lượt này chỉ có `model/last`.")
        print("  LƯU Ý: " + message)
        if log is not None:
            log.warn(message)
    return {"device": device, "dtype": found["dtype_used"], "quantization": found["quantization"],
            "steps": step, "epochs": found["epochs"], "seconds": seconds,
            "trainable_params": trainable, "total_params": total, "best": best,
            "history": history, "settings": found, "head_config": head_config,
            "last_dir": str(checkpoint_dir(out_dir, "ckpt_last")),
            "best_dir": (str(checkpoint_dir(out_dir, "ckpt_best"))
                         if checkpoint_dir(out_dir, "ckpt_best").is_dir() else None)}


def value_text(metrics):
    """Điểm val để IN RA: `chưa có val` khi lượt huấn luyện không có tập val."""
    if not metrics or metrics.get("accuracy_cell") is None:
        return "chưa có val"
    return "{:.4f} ({} ô)".format(metrics["accuracy_cell"], metrics["cells"])


def predict(config, model_id, adapter_dir, texts, source=None):
    """Suy luận ra MÃ NHÃN cho từng review. Trả về `(danh sách mã theo khía cạnh, head_config)`.

    Mã nhãn trả về là mã của KHÔNG GIAN NHÃN đã huấn luyện (đọc từ `head_config.json` của
    checkpoint), nên phần chấm điểm dùng chung với đường prompt mà không phải đoán.
    """
    import torch

    found = settings(config, model_id)
    module = encoders.get(model_id)
    device = device_of()
    found["device"] = device
    found["source"] = source or found["checkpoint"]
    model, _head = build_model(found, device, adapter_dir=adapter_dir, source=found["source"])
    if device == "cuda":
        model = model.to(device)
    head_config = read_head_config(adapter_dir)
    index_to_code = [int(code) for code in head_config["codes"]]

    ids, masks = encode(module, texts, found["max_length"])
    model.eval()
    answers = []
    with torch.no_grad():
        for start in range(0, ids.size(0), found["eval_batch"]):
            stop = start + found["eval_batch"]
            logits = model(input_ids=ids[start:stop].to(device),
                           attention_mask=masks[start:stop].to(device))
            for row in logits.argmax(dim=-1).cpu().tolist():
                answers.append([index_to_code[int(position)] for position in row])
    return answers, head_config

