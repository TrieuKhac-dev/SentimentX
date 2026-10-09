# -*- coding: utf-8 -*-
"""Cách huấn luyện `none`: KHÔNG gói adapter, và có thể KHÔNG học gì cả.

VÌ SAO CÓ
Câu hỏi "tại sao phải LoRA / phải huấn luyện?" chỉ trả lời được bằng một ĐỐI CHỨNG ÂM. Cách này là
đối chứng đó, và nó có HAI mức, chọn bằng `head.trainable` (cùng khoá với đường LoRA):

    `head.trainable: false`   KHÔNG tối ưu gì cả: encoder đóng băng + đầu phân loại là phép chiếu
                              NGẪU NHIÊN CỐ ĐỊNH. Đây là mức SÀN - "không làm gì".
    `head.trainable: true`    encoder vẫn đóng băng nhưng CHỈ đầu phân loại học (linear probe).

Thang ba bậc của báo cáo vì vậy là: SÀN  <  học-chỉ-đầu  <  LoRA (+ đầu phân loại), cả ba đọc trên cùng
một tập `test`.

KHÔNG CÓ ADAPTER, NÊN KHÔNG DÙNG WRITER `adapter`
Trọng số của lượt chạy chỉ nằm ở đầu phân loại, nên checkpoint do writer `head_only` ghi
(`src/training/savers/head_only.py`). Vòng lặp huấn luyện KHÔNG chép lại: nó ở `lora.fit_generic`, và
cách này truyền vào đúng hai thứ khác nhau - hàm dựng model và tên writer.

VÒNG LẶP RỖNG LÀ CHỦ Ý
Ở mức SÀN không có tham số nào học, nên `fit_generic` bỏ qua vòng lặp (không tạo optimizer: `AdamW` với
danh sách rỗng ném `optimizer got an empty parameter list`) nhưng VẪN đo `val` và ghi `model/best` +
`model/last`, để bước suy luận có checkpoint đọc.

KHOÁ CẤU HÌNH `lora.*` VẪN PHẢI CÓ
`settings()` dùng chung với đường LoRA nên vẫn đọc `lora.r/alpha/dropout/target_modules` (chúng nằm ở
`configs/experiments/training.yaml` và `configs/models/<model_id>.yaml`). Lượt `none` KHÔNG dùng tới các
giá trị đó, nhưng bản ghi lượt chạy (`encoder_run.log_config`) đọc chúng, nên giữ nguyên hình dạng
`settings()` là điều kiện để hai đường dùng chung một bản ghi.

`torch`, `transformers` được import BÊN TRONG hàm: CI không cài chúng mà vẫn phải import được module này
để gọi `check()`.
"""

import importlib.util
from pathlib import Path

from src.experiments import model_config
from src.training import encoders, lora, savers

NAME = "none"
DESCRIPTION = "Không gói adapter: đầu phân loại đóng băng (không học gì) hoặc học một mình."

# Writer của cách huấn luyện này: chỉ ghi đầu phân loại.
WRITER = "head_only"


# Cấu hình hiệu lực của một lượt huấn luyện: DÙNG CHUNG với đường LoRA. Lượt `none` không dùng tới
# `lora_r/alpha/dropout/target_modules`, nhưng bản ghi lượt chạy đọc chúng, nên hai đường phải trả về
# CÙNG một hình dạng dict.
settings = lora.settings


def describe():
    """Một dòng mô tả cách huấn luyện này, để in ra khi cần."""
    return "{} | vòng lặp dùng chung ở lora.fit_generic".format(DESCRIPTION)


def head_state_of(found):
    """Nhãn nói CHÍNH XÁC cái gì đang học ở cách `none`.

    Nhãn mặc định của đường LoRA ("ĐÓNG BĂNG - chỉ adapter học") SAI ở đây: cách `none` không có adapter
    nào, nên mức SÀN phải được in là KHÔNG học gì - nếu không, người đọc `run.log` của lượt SÀN sẽ tưởng
    có một adapter đang học, và mất luôn ý nghĩa của phép đối chứng âm.
    """
    if found.get("head_trainable"):
        return "CHỈ đầu phân loại học - encoder đóng băng (linear probe)"
    return "KHÔNG tệp nào học - SÀN (encoder đóng băng + đầu phân loại ngẫu nhiên)"


def check(config, model_id=None):
    """Kiểm lượt `none` có chạy được không. Trả về danh sách việc phải sửa (rỗng là chạy được)."""
    problems = []
    if not (config or {}).get("enabled"):
        return ["none: `training.enabled: false` mà vẫn gọi huấn luyện"]
    try:
        encoders.get(model_id)
    except encoders.EncoderError as exc:
        problems.append("none: {}".format(exc))
    try:
        found = lora.settings(config, model_id)
    except (lora.TrainingError, model_config.ModelConfigError) as exc:
        # Thiếu khoá hoặc thiếu file cấu hình model: đó là việc phải sửa, không phải lỗi làm sập
        # preflight (preflight gom hết rồi báo một lần).
        return problems + ["none: {}".format(exc)]
    if found["trainer"] != NAME:
        problems.append("none: `trainer` là {!r} nhưng đang gọi trình huấn luyện {!r}".format(
            found["trainer"], NAME))
    for name in ("torch", "transformers"):
        if importlib.util.find_spec(name) is None:
            problems.append(
                "none: chưa cài thư viện `{}` (pip install -r requirements.txt)".format(name))
    return problems


def build_model(found, device, n_aspects=None, n_codes=None, adapter_dir=None, source=None,
                trainable=False):
    """Nạp encoder + đầu phân loại, KHÔNG gói LoRA. Trả về `(model, head)`.

    Cùng hợp đồng với `lora.build_model`, chỉ khác: không có `peft`, nên không có adapter nào để nạp
    hay để mở. `adapter_dir` vì vậy là thư mục checkpoint của `head_only` (chỉ `head.pt` +
    `head_config.json`).

    ĐÓNG BĂNG HẾT rồi mới mở đầu phân loại theo `head.trainable` - đi qua ĐÚNG `set_head_trainable` của
    đường LoRA, để cơ chế "đóng băng hay học" chỉ có một định nghĩa.
    """
    aspect_marker = bool((found or {}).get("head_aspect_marker", False))
    if adapter_dir is not None:
        head_config = lora.read_head_config(adapter_dir)
        n_aspects = int(head_config["n_aspects"])
        n_codes = int(head_config["n_codes"])
        # KIẾN TRÚC đầu phân loại lấy từ CHÍNH checkpoint; lệch với cấu hình lượt này là LỖI vì
        # `head.pt` của hai kiến trúc không nạp lẫn nhau (cùng luật với đường LoRA).
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

    # Hai cổng chặn trên CHỈ đọc cấu hình, nên chạy được cả khi máy chưa có thư viện nặng (CI cố ý
    # không cài `torch`/`transformers`). Tới đây mới nạp chúng - và `lora.build_classes()` gọi
    # `import torch` BÊN TRONG, nên nó cũng phải nằm SAU hai cổng chặn: đặt trước thì một CẤU HÌNH sai
    # lại báo lỗi "thiếu thư viện", tức là chỉ đúng triệu chứng chứ không chỉ đúng nguyên nhân.
    import torch
    from transformers import AutoModel

    MultiHeadClassifier, _Rows = lora.build_classes()
    kwargs = {}
    if device == "cuda":
        kwargs["torch_dtype"] = lora.torch_dtype(found["dtype"], device)
    if str(found.get("quantization") or "none") == "4bit":
        if device != "cuda":
            raise lora.TrainingError("Lượng hoá 4-bit cần CUDA; máy này không có GPU dùng được.")
        from transformers import BitsAndBytesConfig

        kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=lora.torch_dtype(found["dtype"], device))
        kwargs["device_map"] = {"": 0}
    encoder = AutoModel.from_pretrained(
        source or found.get("source") or found["checkpoint"], **kwargs)
    classifier = MultiHeadClassifier(encoder, n_aspects, n_codes, aspect_marker=aspect_marker)
    if adapter_dir is not None:
        classifier.head.load_state_dict(torch.load(
            str(Path(adapter_dir) / savers.get(WRITER).HEAD_WEIGHTS), map_location="cpu"))
    for parameter in classifier.parameters():
        parameter.requires_grad = False
    if trainable:
        lora.set_head_trainable(classifier.head, found.get("head_trainable"))
    return classifier, classifier.head


def fit(config, model_id, out_dir, train, val, aspects, codes, fingerprint, seed=42, source=None,
        labels=None, on_point=None, log=None):
    """Chạy một lượt `none`: vòng lặp dùng chung, chỉ khác cách dựng model và cách ghi checkpoint."""
    return lora.fit_generic(config, model_id, out_dir, train, val, aspects, codes, fingerprint,
                            seed=seed, source=source, labels=labels, on_point=on_point, log=log,
                            build=build_model, writer_name=WRITER, head_state_of=head_state_of)


def predict(config, model_id, adapter_dir, texts, source=None):
    """Suy luận từ checkpoint `head_only`; trả `(mã theo khía cạnh, xác suất, head_config)`."""
    return lora.predict_generic(config, model_id, adapter_dir, texts, source=source,
                                build=build_model)

