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
Phần `model/last`, `model/best`, `model/checkpoint-<bước>` và `trainer_state.json` KHÔNG nằm ở đây:
LoRA chỉ là MỘT cách huấn luyện, nên chính sách lưu và chỗ lưu dùng chung ở
`src/training/checkpoints.py`, còn cách ghi trọng số nằm ở writer `src/training/savers/adapter.py`.

`torch`, `transformers`, `peft` được import BÊN TRONG hàm: CI không cài chúng mà vẫn phải import
được module này để gọi `check()`.
"""

import math
import random
from pathlib import Path

from src.experiments import model_config
from src.core import paths, utils
from src.training import checkpoints, encoders, savers

NAME = "lora"
DESCRIPTION = "LoRA (peft) trên model encoder, một đầu phân loại cho mỗi khía cạnh."

# Khoá bắt buộc của lượt huấn luyện, chia theo NƠI KHAI. Thiếu khoá nào thì báo đúng khoá đó kèm nơi
# khai: giá trị mặc định trong code là thứ âm thầm khác với giá trị đang chạy.
REQUIRED_MODEL = ("lora.target_modules", "preprocess.max_length", "inference.batch_size",
                  "inference.dtype")
REQUIRED_SHARED = ("trainer", "lora.r", "lora.alpha", "lora.dropout", "lr", "batch", "epochs",
                   "grad_accum", "weight_decay")


def where(key):
    """Nơi khai một khoá, để thông báo lỗi chỉ đúng file mà người đọc phải mở."""
    if str(key) in REQUIRED_MODEL:
        return "file cấu hình của model, khoá `{}` (docs/05_config/04_models.md)".format(key)
    return ("file cấu hình huấn luyện dùng chung, khoá `{}` "
            "(docs/05_config/05_experiments_shared.md)".format(key))

# Kiểu số hợp lệ. Một nguồn duy nhất: `src/experiments/model_config.py` (hàm giải `auto` cũng ở đó, dùng chung
# cho cả đường encoder và đường prompt - xem `model_config.resolve_dtype`).
DTYPES = model_config.DTYPES

# Tên file của checkpoint nằm ở writer `src/training/savers/adapter.py`.


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


# ---


def describe():
    """Một dòng mô tả cách huấn luyện này, để in ra khi cần."""
    return "{} | đầu phân loại riêng cho mỗi khía cạnh".format(DESCRIPTION)


def device_of():
    """Thiết bị sẽ dùng: `cuda` nếu có GPU, còn lại CPU."""
    import torch

    return "cuda" if torch.cuda.is_available() else "cpu"


def torch_dtype(name, device):
    """Kiểu số THẬT SỰ dùng sau khi giải `auto` - gọi hàm DÙNG CHUNG với đường prompt.

    VÌ SAO KHÔNG CÒN BẢN RIÊNG Ở ĐÂY: bản cũ gọi `torch.cuda.is_bf16_supported()` KHÔNG kèm
    `including_emulation=False`, nên trên T4 (Turing, không có bf16 phần cứng) nó vẫn chọn bf16 giả
    lập - chậm bất thường. Nay cả hai đường chạy `src/experiments/model_config.resolve_dtype`, nên không thể lệch
    nhau về cách giải `auto`, và khai tường minh mà máy không đáp ứng được là LỖI chứ không hạ cấp.
    """
    return model_config.resolve_dtype(name, device)


def encode(module, texts, max_length, batch=64):
    """Mọi văn bản đã tách từ (nếu model cần), đã cắt và ĐÃ PAD CÙNG MỘT ĐỘ RỘNG.

    Dùng `build_inputs()` của chính module model, nên ngưỡng cắt ở đây đúng bằng ngưỡng mà
    `token_stats` đã đo - không có đường thứ hai để lệch nhau.

    VÌ SAO PHẢI PAD LẠI CHO CÙNG ĐỘ RỘNG: `build_inputs` pad theo văn bản DÀI NHẤT TRONG LÔ (đúng cho
    phép đo token, vì đo từng lô văn bản thật), mà hàm này mã hoá theo TỪNG LÔ rồi nối lại. Hai lô có
    văn bản dài ngắn khác nhau thì hai tensor rộng khác nhau, và `torch.cat` ném `RuntimeError: Sizes
    of tensors must match except in dimension 0` - lỗi thật đã gặp trên Colab với ~4.000 review (nhiều
    lô), trong khi phép chạy thử ở máy chỉ có 40 review (một lô) nên không lộ ra. Ở đây pad thêm cho
    bằng lô rộng nhất: id 0 là token pad, mask 0 nghĩa là không chú ý tới - model không nhìn thấy gì
    khác so với không pad.
    """
    import torch

    chunks = [module.build_inputs(list(texts[start:start + batch]), max_length=max_length)
              for start in range(0, len(texts), batch)]
    if not chunks:
        empty = torch.empty((0, 0), dtype=torch.long)
        return empty, empty

    width = max(chunk["input_ids"].size(1) for chunk in chunks)
    ids, masks = [], []
    for chunk in chunks:
        rows, columns = chunk["input_ids"].shape
        if columns == width:
            ids.append(chunk["input_ids"])
            masks.append(chunk["attention_mask"])
            continue
        padding = chunk["input_ids"].new_zeros((rows, width - columns))
        ids.append(torch.cat([chunk["input_ids"], padding], dim=1))
        masks.append(torch.cat([chunk["attention_mask"], padding], dim=1))
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

        def forward(self, input_ids=None, attention_mask=None, **kwargs):
            """`**kwargs` để chịu được tham số phụ do lớp bọc (peft) hoặc Trainer truyền vào.

            Tham số phụ như `inputs_embeds` không đổi phép tính của đầu phân loại, nên bỏ qua thay
            vì lỗi: chặn ở đây sẽ làm cả lượt huấn luyện dừng ở bước đầu tiên.
            """
            output = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
            # Ép về kiểu số của CHÍNH đầu phân loại: encoder ở bf16/fp16 còn đầu ở fp32 (máy tính
            # bằng bf16 nhưng tham số học ở fp32), và `matmul` đòi hai vế cùng kiểu. Phép ép này
            # vẫn cho gradient đi qua, nên không mất gì.
            pooled = output.last_hidden_state[:, 0].to(self.head.weight.dtype)
            # Token đầu tiên là đại diện cả câu (<s> của PhoBERT và của XLM-R/ViSoBERT).
            return self.head(pooled).view(-1, self.n_aspects, self.n_codes)

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
        try:
            model = PeftModel.from_pretrained(classifier, str(adapter_dir))
        except ImportError as exc:
            raise _peft_error(exc) from exc
        classifier.head.load_state_dict(
            torch.load(str(Path(adapter_dir) / savers.get().HEAD_WEIGHTS), map_location="cpu"))
        return model, classifier.head

    if str(found.get("quantization") or "none") == "4bit":
        classifier.encoder = prepare_model_for_kbit_training(classifier.encoder)
    try:
        model = get_peft_model(classifier, LoraConfig(
            r=found["lora_r"], lora_alpha=found["lora_alpha"], lora_dropout=found["lora_dropout"],
            target_modules=list(found["target_modules"]), bias="none",
            task_type="FEATURE_EXTRACTION"))
    except ImportError as exc:
        raise _peft_error(exc) from exc
    return model, classifier.head


TORCHAO_HINT = (
    "Máy này có gói `torchao` cũ hơn mức `peft` cần, và `peft` ném lỗi ngay khi bọc LoRA dù dự án "
    "KHÔNG dùng torchao. Gỡ nó rồi chạy lại:\n    pip uninstall -y torchao\n"
    "Trên Colab, ô bootstrap của notebook tự làm việc này nên không phải gõ lệnh."
)


def _peft_error(exc):
    """Câu thông báo khi `peft` không bọc được LoRA, kèm cách sửa cho ca hay gặp.

    Lỗi thật trên Colab: `Found an incompatible version of torchao. Found version 0.10.0, but only
    versions above 0.16.0 are supported` làm chết lượt chạy LoRA sau khi đã tải và nạp xong model -
    thông báo gốc chỉ nói về một gói mà dự án không dùng, nên người đọc không biết phải làm gì.
    """
    first = (str(exc).splitlines() or [""])[0].strip()
    if "torchao" in str(exc):
        return TrainingError("Không bọc được LoRA bằng `peft`: {}\n{}".format(first, TORCHAO_HINT))
    return TrainingError("Không bọc được LoRA bằng `peft`: {}".format(first))


def read_head_config(directory):
    """Đọc `head_config.json` của một checkpoint: số khía cạnh, số lớp, thứ tự khía cạnh.

    Việc đọc thuộc writer (`src/training/savers/adapter.py`) vì chính nó ghi file đó ra, nên dùng lại
    checkpoint của một cách huấn luyện khác cũng đi qua đúng chỗ ấy.
    """
    return savers.get().read_metadata(directory)


def masked_loss(logits, targets, mask, n_codes, weights=None):
    """Cross-entropy trên từng ô ĐƯỢC TÍNH: ô `mask = 0` không vào tử số lẫn mẫu số.

    Mẫu số là số ô được tính (không phải số ô), nên một review chỉ nhắc một khía cạnh vẫn đóng góp
    đúng trọng số của nó thay vì bị pha loãng bởi sáu khía cạnh không nhắc.

    `weights` (tuỳ chọn): trọng số theo LỚP (`class_weight: inverse`) để chống mất cân bằng - lớp
    hiếm được đẩy trọng số lên. `None` nghĩa là cross-entropy thường.
    """
    import torch

    flat = torch.nn.functional.cross_entropy(
        logits.reshape(-1, int(n_codes)), targets.reshape(-1), reduction="none")
    if weights is not None:
        flat = flat * weights.to(flat.dtype)[targets.reshape(-1)]
    weights_mask = mask.reshape(-1).to(flat.dtype)
    return (flat * weights_mask).sum() / weights_mask.sum().clamp(min=1.0)


def loss_settings(config):
    """Cấu hình hàm mất mát. Thiếu khoá là LỖI kèm nơi khai (không đặt mặc định trong code)."""
    kind = str(_get(config, "loss.type")).strip().lower()
    if kind not in ("ce", "weighted_ce"):
        raise TrainingError(
            "`loss.type` = '{}' không hợp lệ. Chọn `ce` hoặc `weighted_ce`.".format(kind))
    class_weight = str(_get(config, "loss.class_weight")).strip().lower()
    if class_weight not in ("none", "inverse"):
        raise TrainingError(
            "`loss.class_weight` = '{}' không hợp lệ. Chọn `none` hoặc `inverse`.".format(class_weight))
    if kind == "weighted_ce" and class_weight != "inverse":
        raise TrainingError(
            "`loss.type: weighted_ce` cần `loss.class_weight: inverse` (đang là '{}').".format(
                class_weight))
    return {"type": kind, "class_weight": class_weight}


def class_weights(labels, mask, codes, device):
    """Trọng số lớp = NGHỊCH ĐẢO tần suất, chuẩn hoá để trung bình bằng 1.

    Đếm trên các ô ĐƯỢC TÍNH của tập train (ô bị loại không vào đếm). Lớp không xuất hiện nhận trọng
    số 0 - nó không có ô nào nên trọng số không ảnh hưởng gì.
    """
    import torch

    counts = {int(code): 0 for code in codes}
    for row, keep in zip(labels, mask):
        for value, flag in zip(row, keep):
            if flag and int(value) in counts:
                counts[int(value)] += 1
    total = sum(counts.values())
    if not total:
        return None
    k = len(codes)
    values = [total / (k * counts[int(code)]) if counts[int(code)] else 0.0 for code in codes]
    return torch.tensor(values, dtype=torch.float32, device=device)


def parameter_counts(model):
    """(số tham số học, tổng số tham số) - để biết LoRA nhỏ cỡ nào so với model gốc."""
    total = sum(item.numel() for item in model.parameters())
    trainable = sum(item.numel() for item in model.parameters() if item.requires_grad)
    return trainable, total


def measure(model, module, data, found, codes, device, aspects, task, labels):
    """Đo `val` bằng ĐÚNG engine chấm điểm của lượt chạy (`src/evaluation/scorers`).

    Trả về dict gồm `loss` (cross-entropy trên các ô được tính) và các chỉ số của `Samples`:
    `accuracy_cell` (gộp), `accuracy_macro`, `sentiment_f1`/`sentiment_precision`/`sentiment_recall`,
    `detection_f1`, `cells`, `correct`.

    Vì sao dùng `Samples`: `val` phải có ĐÚNG bộ chỉ số như `test`, nên việc chọn `model/best` và
    dừng sớm KHÔNG phải định nghĩa lại metric lần thứ hai.

    `data["labels"]` đã ở KHÔNG GIAN NHÃN của thí nghiệm (ô bị loại mang mã neutral), nên đưa thẳng
    vào `Samples.build` với cùng `task` là ĐÚNG: phép chiếu lặp lại không đổi gì.
    """
    import torch

    from src.evaluation import scorers

    if not data or not data.get("texts"):
        return None
    ids, masks = encode(module, data["texts"], found["max_length"])
    # `logits` ở dưới nằm trên GPU, nên hai tensor này PHẢI cùng device với nó: cross_entropy không so
    # được hai thiết bị khác nhau. Bản `measure` CŨ so trên CPU (`logits.argmax(dim=-1).cpu()`) nên
    # không cần cast; bản dùng `loss` thì cần - thiếu là RuntimeError ngay ở lần ĐO val đầu tiên, tức
    # là sau khi đã huấn luyện xong một đoạn (mất cả lượt chạy, không kịp ghi checkpoint nào).
    targets = targets_from(data["labels"], codes).to(device)
    keep = torch.tensor(data["mask"], dtype=torch.float32, device=device)
    was_training = model.training
    model.eval()
    loss_sum, weight_sum, answers = 0.0, 0.0, []
    with torch.no_grad():
        for start in range(0, ids.size(0), found["eval_batch"]):
            stop = start + found["eval_batch"]
            logits = model(input_ids=ids[start:stop].to(device),
                           attention_mask=masks[start:stop].to(device))
            weight = keep[start:stop].reshape(-1)
            flat = torch.nn.functional.cross_entropy(
                logits.reshape(-1, len(codes)), targets[start:stop].reshape(-1), reduction="none")
            loss_sum += float((flat * weight).sum().item())
            weight_sum += float(weight.sum().item())
            answers.extend(logits.argmax(dim=-1).cpu().tolist())
    if was_training:
        model.train()

    gold_rows = [dict(zip(aspects, row)) for row in data["labels"]]
    pred_rows = [dict(zip(aspects, row)) for row in answers]
    samples = scorers.Samples.build(aspects, gold_rows, pred_rows, task=task, labels=labels)
    accuracy = samples.accuracy()
    sentiment = samples.per_sentiment()["macro"]
    detection = samples.detection()["macro"]
    return {
        "loss": round(loss_sum / weight_sum, 6) if weight_sum else None,
        "accuracy_cell": round(accuracy["micro"], 6),
        "accuracy_macro": round(accuracy["macro"], 6),
        "sentiment_f1": round(sentiment["f1"], 6),
        "sentiment_precision": round(sentiment["precision"], 6),
        "sentiment_recall": round(sentiment["recall"], 6),
        "detection_f1": round(detection["f1"], 6),
        "cells": accuracy["cells"],
        "correct": accuracy["correct"],
    }

    return removed


# Chỉ số mà `measure()` có thể tính - `checkpoints.best_metric` phải nằm trong đây.
MEASURED_METRICS = ("accuracy_cell", "accuracy_macro", "sentiment_f1", "sentiment_precision",
                    "sentiment_recall", "detection_f1", "loss")


def early_settings(config):
    """Chính sách DỪNG SỚM. Thiếu khoá là LỖI kèm nơi khai (không đặt mặc định trong code).

    CHỈ đường huấn luyện encoder dùng; model prompt không huấn luyện nên không đụng tới.
    """
    found = {}
    for key, caster in (("enabled", bool), ("patience", int), ("min_delta", float)):
        found[key] = caster(_get(config, "early_stop.{}".format(key)))
    if found["patience"] < 1:
        raise TrainingError(
            "`early_stop.patience` phải >= 1 (đang là {}). Khai ở configs/experiments/training.yaml."
            .format(found["patience"]))
    return found


def fit(config, model_id, out_dir, train, val, aspects, codes, fingerprint, seed=42, source=None,
        labels=None, on_point=None, log=None):
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
    # Chính sách lưu + CÁCH GHI trọng số: dùng chung cho mọi cách huấn luyện, xem
    # src/training/checkpoints.py (chính sách, chỗ lưu) và src/training/savers/ (writer).
    policy = checkpoints.settings(config)
    store = checkpoints.Store(out_dir, policy)
    early = early_settings(config)
    loss_policy = loss_settings(config)
    task = {key: _get(config, key) for key in ("label_space", "neutral_policy", "not_mentioned")}
    labels = dict(labels or {})
    metric = policy["best_metric"]
    if metric not in MEASURED_METRICS:
        raise TrainingError(
            "`checkpoints.best_metric` = '{}' không phải chỉ số mà `measure()` tính. Chọn một trong: "
            "{}.".format(metric, ", ".join(MEASURED_METRICS)))
    writer = savers.get()

    random.seed(seed)
    torch.manual_seed(seed)
    if device == "cuda":
        torch.cuda.manual_seed_all(seed)

    head_config = {"n_aspects": len(aspects), "n_codes": len(codes),
                   "codes": [int(code) for code in codes],
                   "aspects": [str(name) for name in aspects]}
    state = store.resume_state(fingerprint, require=False)
    adapter = store.last_dir() if state else None
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
    # Trọng số lớp (chống mất cân bằng) chỉ dùng khi config khai `weighted_ce` + `inverse`.
    loss_weights = None
    if loss_policy["type"] == "weighted_ce" and loss_policy["class_weight"] == "inverse":
        loss_weights = class_weights(train["labels"], train["mask"], codes, device)
        found["loss_weights"] = [float(value) for value in loss_weights.tolist()] if loss_weights is not None else None
    else:
        found["loss_weights"] = None
    found["loss_policy"] = dict(loss_policy)
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
        folder = store.last_dir()
        if (folder / writer.OPTIMIZER_FILE).is_file():
            optimizer.load_state_dict(
                torch.load(str(folder / writer.OPTIMIZER_FILE), map_location="cpu"))
        if (folder / writer.SCHEDULER_FILE).is_file():
            scheduler.load_state_dict(
                torch.load(str(folder / writer.SCHEDULER_FILE), map_location="cpu"))
        start_epoch = int(state.get("epoch") or 0)
        step = int(state.get("step") or 0)
        best = state.get("best") or None
        if log is not None:
            log.step("chạy tiếp từ checkpoint: epoch {} (đã {} bước)".format(start_epoch, step))


    history = []
    started = time.time()
    model.train()
    pending = 0
    epoch_loss_sum, epoch_weight = 0.0, 0.0
    stale, stopped_early = 0, False
    patience, min_delta = early["patience"], early["min_delta"]

    def record(epoch_done, metrics, snapshot):
        """Ghi trạng thái hiện tại: `model/best` khi TỐT HƠN theo `checkpoints.best_metric`.

        Metric do config quyết định (không hardcode): mặc định `sentiment_f1` (macro-F1 sắc thái) vì
        `accuracy_cell` bị lớp trội chi phối khi dữ liệu mất cân bằng.
        """
        nonlocal best
        improved = False
        value = (metrics or {}).get(metric)
        if value is not None:
            improved = best is None or value > float(best.get(metric) or -1)
            if improved:
                best = {"epoch": epoch_done, "step": step, "metric": metric, **metrics}
                if policy["save_best"]:
                    store.save(store.best_dir(), writer, payload(epoch_done, metrics),
                               checkpoint_payload(), weights_only=True)
        if snapshot:
            store.save(store.snapshot_dir(step), writer, payload(epoch_done, metrics),
                       checkpoint_payload())
            if policy["delete_intermediate"]:
                store.prune()
        return improved

    def checkpoint_payload():
        """Đối tượng writer cần để ghi trọng số, cộng mô tả bài toán để dùng lại checkpoint.

        Trainer biết nó có gì, writer biết cách ghi - chỗ nối của hai bên là dict này. Writer khác
        (ví dụ full fine-tune) sẽ cần đối tượng khác, nên nó nằm ở đây chứ không nằm trong `Store`.
        """
        return {"model": model, "head": head, "head_config": head_config,
                "optimizer": optimizer, "scheduler": scheduler}

    def payload(epoch_done, metrics):
        """Nội dung `trainer_state.json`: vân tay, chỗ đã đi tới, và bài toán đang học."""
        return {"head_config": head_config, "fingerprint": dict(fingerprint), "epoch": epoch_done,
                "step": step, "best": best, "metrics": metrics, "source": found["source"],
                "settings": found}

    for epoch in range(start_epoch, found["epochs"]):
        for index, batch in enumerate(loader):
            batch = {key: value.to(device) for key, value in batch.items()}
            logits = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"])
            loss = masked_loss(logits, batch["labels"], batch["mask"], len(codes), loss_weights)
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
            if step % policy["every_n_steps"]:
                continue
            metrics = measure(model, module, val, found, codes, device, aspects, task, labels)
            # `detach()` trước khi đổi sang số: `loss` còn gắn đồ thị tính đạo hàm, và PyTorch cảnh báo
            # (`Converting a tensor with requires_grad=True to a scalar...`) - cảnh báo đã hiện trong
            # run.log của lượt chạy thật, làm log khó đọc mà không có lỗi nào thật.
            loss_value = float(loss.detach())
            weight_now = float(batch["mask"].to(torch.float32).sum().item())
            epoch_loss_sum += loss_value * weight_now
            epoch_weight += weight_now
            history.append({"kind": "step", "step": step, "epoch": epoch + 1,
                            "loss": round(loss_value, 6),
                            "lr": round(float(scheduler.get_last_lr()[0]), 8), "val": metrics})
            improved = record(epoch + 1, metrics, snapshot=True)
            if on_point is not None and metrics:
                on_point(metrics, step)
            message = "bước {} | loss {:.4f} | val {} | {}".format(
                step, loss_value, value_text(metrics, metric),
                "đã lưu model/best" if improved else "chưa tốt hơn")
            print("  " + message)
            if log is not None:
                log.step(message)
            stale = 0 if improved else stale + 1
            if early["enabled"] and stale >= patience:
                stopped_early = True
                note = ("dừng sớm: '{}' không tăng quá {} trong {} lần đo liên tiếp (bước {})"
                        .format(metric, min_delta, patience, step))
                print("  " + note)
                if log is not None:
                    log.step(note)
                break

        metrics = measure(model, module, val, found, codes, device, aspects, task, labels)
        # Cuối epoch cũng có thể là bước TỐT NHẤT: khối `if improved` trong `record` ghi `model/best`
        # KHÔNG phụ thuộc `snapshot`, nên bản tốt nhất có thể ở đây. Không nói ra thì người đọc console
        # tưởng bản đang chấm là bước in ra gần nhất - đã gặp thật: `model/best` ở bước 1153 trong khi
        # console chỉ in "đã lưu model/best" ở bước 1100.
        best_now = record(epoch + 1, metrics, snapshot=False)
        if on_point is not None and metrics:
            on_point(metrics, step)
        store.save(store.last_dir(), writer, payload(epoch + 1, metrics), checkpoint_payload())
        # Một dòng LỊCH SỬ cho cả epoch: loss train trung bình + loss/chỉ số val - dữ liệu để vẽ curve
        # train/val (`training_history.csv`) và để nhìn ra overfit.
        history.append({"kind": "epoch", "step": step, "epoch": epoch + 1,
                        "train_loss": round(epoch_loss_sum / epoch_weight, 6) if epoch_weight else None,
                        "val_loss": (metrics or {}).get("loss"), "val": metrics})
        epoch_loss_sum, epoch_weight = 0.0, 0.0
        print("hết epoch {}/{}: {} bước, val {} | {}".format(
            epoch + 1, found["epochs"], step, value_text(metrics, metric),
            "đã lưu model/best" if best_now else "chưa tốt hơn"))
        stale = 0 if best_now else stale + 1
        if early["enabled"] and stale >= patience:
            stopped_early = True
            note = ("dừng sớm sau epoch {}: '{}' không tăng quá {} trong {} lần đo liên tiếp"
                    .format(epoch + 1, metric, min_delta, patience))
            print("  " + note)
            if log is not None:
                log.step(note)
        if stopped_early:
            break

    seconds = round(time.time() - started, 1)
    if policy["save_best"] and best is None:
        message = ("Không có `val` để chọn `model/best`: khai `data.roles.val` khi huấn luyện. "
                   "Lượt này chỉ có `model/last`.")
        print("  LƯU Ý: " + message)
        if log is not None:
            log.warn(message)
    return {"device": device, "dtype": found["dtype_used"], "quantization": found["quantization"],
            "steps": step, "epochs": found["epochs"], "seconds": seconds,
            "trainable_params": trainable, "total_params": total, "best": best,
            "history": history, "settings": found, "head_config": head_config,
            "last_dir": str(store.last_dir()),
            "best_dir": (str(store.best_dir()) if store.best_dir().is_dir() else None)}


def value_text(metrics, metric="accuracy_cell"):
    """Điểm val để IN RA: `chưa có val` khi lượt huấn luyện không có tập val."""
    if not metrics or metrics.get(metric) is None:
        return "chưa có val"
    return "{}={:.4f} ({} ô)".format(metric, metrics[metric], metrics.get("cells", 0))


def predict(config, model_id, adapter_dir, texts, source=None):
    """Suy luận ra MÃ NHÃN và XÁC SUẤT từng ô.

    Trả về `(mã theo khía cạnh, xác suất theo (khía cạnh, mã), head_config)`.

    Mã nhãn trả về là mã của KHÔNG GIAN NHÃN đã huấn luyện (đọc từ `head_config.json` của
    checkpoint), nên phần chấm điểm dùng chung với đường prompt mà không phải đoán.

    Xác suất là thứ bước KẾT HỢP cần (dò ngưỡng theo khía cạnh, ensemble nhiều encoder, luật lai
    encoder + LLM): ba bước đó phải so XÁC SUẤT chứ không chỉ so nhãn cứng. Thứ tự mã trong mỗi hàng
    là thứ tự của `head_config["codes"]`, và `encoder_run` ghi lại ĐÚNG thứ tự đó vào tên cột.
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
    answers, probabilities = [], []
    with torch.no_grad():
        for start in range(0, ids.size(0), found["eval_batch"]):
            stop = start + found["eval_batch"]
            logits = model(input_ids=ids[start:stop].to(device),
                           attention_mask=masks[start:stop].to(device))
            # `softmax` tính trên float32: logits có thể ở fp16 (T4), mà softmax fp16 cho ra xác suất
            # bị làm tròn thô - sai số đó lan thẳng vào ngưỡng của bước kết hợp.
            probs = torch.softmax(logits.float(), dim=-1).cpu().tolist()
            for row, prob_row in zip(logits.argmax(dim=-1).cpu().tolist(), probs):
                answers.append([index_to_code[int(position)] for position in row])
                probabilities.append([[round(float(value), 6) for value in per_code]
                                      for per_code in prob_row])
    return answers, probabilities, head_config

