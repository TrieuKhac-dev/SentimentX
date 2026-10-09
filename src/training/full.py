# -*- coding: utf-8 -*-
"""Cách huấn luyện `full`: FULL FINE-TUNE - encoder và đầu phân loại cùng học.

VÌ SAO CÓ
LoRA chỉ sửa vài triệu tham số; câu hỏi "nếu cho model học TẤT CẢ thì hơn bao nhiêu?" chỉ trả lời được
bằng một lượt full fine-tune trên đúng cùng dữ liệu, cùng hàm mất mát, cùng số epoch. Đây là mốc ĐỐI
CHỨNG của cả nhóm LoRA, và là mốc mà các bài báo ABSA thường công bố.

KHÁC `none` Ở ĐÚNG MỘT CHỖ
`none` cũng không gói adapter, nhưng nó ĐÓNG BĂNG encoder (SÀN: không tối ưu gì; hoặc linear probe: chỉ
đầu phân loại học). Ở đây mọi tham số đều học, nên checkpoint phải chứa cả encoder - đó là lý do có writer
riêng `state_dict` (`src/training/savers/state_dict.py`). Vòng lặp huấn luyện KHÔNG chép lại: nó ở
`lora.fit_generic`, và cách này truyền vào ba thứ khác nhau - hàm dựng model, tên writer, và nhãn nói
CHÍNH XÁC cái gì đang học (nhãn đó được in ra và ghi vào `run.log`).

KHÔNG ĐI VỚI LƯỢNG HOÁ 4-BIT
`inference.quantization: 4bit` ĐÓNG BĂNG trọng số gốc ở 4 bit, nên "full fine-tune 4-bit" không phải
full fine-tune mà là QLoRA - muốn thế thì dùng `trainer: lora` với `quantization: 4bit`. Cấu hình đó bị
TỪ CHỐI ở `build_model` và ở `check()` thay vì chạy ra một lượt mang tên sai.

CHI PHÍ
Bộ nhớ và đĩa lớn hơn LoRA hàng chục lần (xem docstring của writer). Đây là lượt ĐỐI CHỨNG, không phải
lượt chạy cho mọi model. `lr` mặc định của dự án (2e-4) là mức của LoRA; full fine-tune thường cần thấp
hơn khoảng 10 lần, nên đợt 11 chạy HAI lượt: một giữ nguyên `lr` (để phép so chỉ đổi MỘT biến: cơ chế
học) và một hạ `lr` (mức thông lệ).

`torch`, `transformers` được import BÊN TRONG hàm: CI không cài chúng mà vẫn phải import được module này
để gọi `check()`.
"""

import importlib.util
from pathlib import Path

from src.experiments import model_config
from src.training import encoders, lora, savers

NAME = "full"
DESCRIPTION = "Full fine-tune: encoder và đầu phân loại cùng học (không adapter)."

# Writer của cách huấn luyện này: ghi TOÀN BỘ trọng số.
WRITER = "state_dict"


# Cấu hình hiệu lực của một lượt huấn luyện: DÙNG CHUNG với đường LoRA (cùng một bản ghi lượt chạy).
settings = lora.settings


def describe():
    """Một dòng mô tả cách huấn luyện này, để in ra khi cần."""
    return "{} | vòng lặp dùng chung ở lora.fit_generic".format(DESCRIPTION)


def head_state_of(found):
    """Nhãn nói CHÍNH XÁC cái gì đang học, in ra và ghi vào `run.log`.

    Lấy từ `head.trainable` chứ không viết cứng: cấu hình `head.trainable: false` vẫn chạy được (đầu
    phân loại đóng băng trong khi encoder học), và khi đó dòng in ra phải nói đúng như vậy - một dòng
    nói "học toàn bộ" trong khi đầu phân loại đứng yên là dòng sai ngay ở chỗ người đọc tin nhất.
    """
    if found.get("head_trainable"):
        return "HỌC TOÀN BỘ - encoder và đầu phân loại"
    return "ĐÓNG BĂNG đầu phân loại - CHỈ encoder học"


def check(config, model_id=None):
    """Kiểm lượt `full` có chạy được không. Trả về danh sách việc phải sửa (rỗng là chạy được)."""
    problems = []
    if not (config or {}).get("enabled"):
        return ["full: `training.enabled: false` mà vẫn gọi huấn luyện"]
    try:
        encoders.get(model_id)
    except encoders.EncoderError as exc:
        problems.append("full: {}".format(exc))
    try:
        found = lora.settings(config, model_id)
    except (lora.TrainingError, model_config.ModelConfigError) as exc:
        return problems + ["full: {}".format(exc)]
    if found["trainer"] != NAME:
        problems.append("full: `trainer` là {!r} nhưng đang gọi trình huấn luyện {!r}".format(
            found["trainer"], NAME))
    if str(found.get("quantization") or "none") == "4bit":
        problems.append(
            "full: `inference.quantization: 4bit` không đi với full fine-tune - 4 bit ĐÓNG BĂNG trọng "
            "số gốc, nên đó là QLoRA. Dùng `trainer: lora` với `quantization: 4bit`.")
    for name in ("torch", "transformers"):
        if importlib.util.find_spec(name) is None:
            problems.append("full: chưa cài thư viện `{}` (pip install -r requirements.txt)".format(name))
    return problems


def build_model(found, device, n_aspects=None, n_codes=None, adapter_dir=None, source=None,
                trainable=False):
    """Dựng `(model, head)` cho full fine-tune: encoder + đầu phân loại, MỌI tham số đều học.

    Hai cổng chặn (thiếu số khía cạnh/lớp, checkpoint khác kiến trúc) đọc CHỈ cấu hình và file metadata,
    nên chạy được cả khi máy chưa có thư viện nặng - cùng lý do như đường `lora`/`none`: một cấu hình sai
    phải báo đúng nguyên nhân, không báo "thiếu thư viện".
    """
    aspect_marker = bool(found.get("head_aspect_marker", False))
    if adapter_dir is not None:
        head_config = lora.read_head_config(adapter_dir)
        n_aspects = int(head_config["n_aspects"])
        n_codes = int(head_config["n_codes"])
        checkpoint_marker = bool(head_config.get("aspect_marker", False))
        if checkpoint_marker != aspect_marker:
            raise lora.TrainingError(
                "Checkpoint {} huấn luyện với `head.aspect_marker: {}` nhưng lượt này khai `{}` - "
                "khác KIẾN TRÚC đầu phân loại.".format(
                    adapter_dir, str(checkpoint_marker).lower(), str(aspect_marker).lower()))
        aspect_marker = checkpoint_marker
    if not n_aspects or not n_codes:
        raise lora.TrainingError(
            "Thiếu `n_aspects`/`n_codes`: số đầu và số lớp của đầu phân loại phải biết trước "
            "(suy từ bộ khía cạnh và không gian nhãn của thí nghiệm).")
    if str(found.get("quantization") or "none") == "4bit":
        raise lora.TrainingError(
            "Full fine-tune không đi với `inference.quantization: 4bit`: 4 bit ĐÓNG BĂNG trọng số gốc "
            "nên đó là QLoRA, không phải full fine-tune. Dùng `trainer: lora` với lượng hoá 4 bit.")

    import torch
    from transformers import AutoModel

    MultiHeadClassifier, _Rows = lora.build_classes()
    kwargs = {}
    if device == "cuda":
        kwargs["torch_dtype"] = lora.torch_dtype(found["dtype"], device)
    encoder = AutoModel.from_pretrained(
        source or found.get("source") or found["checkpoint"], **kwargs)
    classifier = MultiHeadClassifier(encoder, n_aspects, n_codes, aspect_marker=aspect_marker)
    if adapter_dir is not None:
        # Trọng số của CẢ model nằm trong `model.pt` - điểm khác căn bản so với LoRA (chỉ adapter) và so
        # với `none` (chỉ đầu phân loại). Nạp xong không cần `head.pt`, nhưng writer vẫn ghi nó để mọi
        # checkpoint của dự án có CÙNG bộ file mô tả đầu phân loại.
        weights = torch.load(str(Path(adapter_dir) / savers.get(WRITER).MODEL_WEIGHTS),
                             map_location="cpu")
        classifier.load_state_dict(weights)
    if trainable:
        # ĐỊNH NGHĨA của full fine-tune: mọi tham số học. KHÔNG gọi `set_head_trainable` ở đây vì hàm đó
        # ĐÓNG BĂNG encoder - đúng cho LoRA, sai cho lượt này.
        for parameter in classifier.parameters():
            parameter.requires_grad = True
    return classifier, classifier.head


def fit(config, model_id, out_dir, train, val, aspects, codes, fingerprint, seed=42, source=None,
        labels=None, on_point=None, log=None):
    """Chạy một lượt full fine-tune: vòng lặp dùng chung, khác cách dựng model + cách ghi checkpoint."""
    return lora.fit_generic(config, model_id, out_dir, train, val, aspects, codes, fingerprint,
                            seed=seed, source=source, labels=labels, on_point=on_point, log=log,
                            build=build_model, writer_name=WRITER, head_state_of=head_state_of)


def predict(config, model_id, adapter_dir, texts, source=None):
    """Suy luận từ checkpoint `state_dict`; trả `(mã theo khía cạnh, xác suất, head_config)`."""
    return lora.predict_generic(config, model_id, adapter_dir, texts, source=source,
                                build=build_model)
