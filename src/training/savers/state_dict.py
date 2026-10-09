# -*- coding: utf-8 -*-
"""Writer cho FULL FINE-TUNE: toàn bộ trọng số (encoder + đầu phân loại).

VÌ SAO CẦN
``adapter`` gọi ``model.save_pretrained()`` - chỉ ``PeftModel`` mới có - còn ``head_only`` chỉ ghi đầu
phân loại. Full fine-tune sửa MỌI tham số của encoder, nên checkpoint phải chứa cả encoder: không còn
trọng số gốc nào trên Hugging Face để nạp lại thay cho nó.

TÊN FILE
    ``model.pt``        state_dict của CẢ model (encoder + đầu phân loại)
    ``head.pt``         đầu phân loại. TÊN TRÙNG ``adapter``/``head_only`` là CHỦ Ý: ``head.pt`` và
    ``head_config.json``   ``head_config.json`` là ĐỊNH DẠNG của đầu phân loại, không phải của một cách
                        huấn luyện, nên ``lora.read_head_config`` đọc được checkpoint này mà không cần
                        đường thứ hai.
    ``optimizer.pt``, ``scheduler.pt``   chỉ có ở ``model/last`` (để chạy tiếp).

CHI PHÍ ĐĨA - đọc trước khi bật full fine-tune: ``model.pt`` cỡ bằng cả model (PhoBERT-base fp16 ~270 MB,
CafeBERT fp16 ~550 MB) và ``optimizer.pt`` của AdamW cỡ GẤP ĐÔI model; chính sách ``keep_last_k: 2`` +
``save_best`` nhân số đó lên. Đó là lý do full fine-tune chỉ chạy ở vài lượt ĐỐI CHỨNG.
"""

import importlib.util
import json
from pathlib import Path

from src.core import utils

NAME = "state_dict"
DESCRIPTION = "Toàn bộ trọng số (encoder + đầu phân loại): dùng cho cách huấn luyện `full`."

HEAD_CONFIG = "head_config.json"
HEAD_WEIGHTS = "head.pt"
MODEL_WEIGHTS = "model.pt"
OPTIMIZER_FILE = "optimizer.pt"
SCHEDULER_FILE = "scheduler.pt"


def save(directory, weights_only=False, model=None, head=None, head_config=None, optimizer=None,
         scheduler=None):
    """Ghi TOÀN BỘ trọng số của ``model`` + đầu phân loại vào ``directory``.

    ``weights_only=True`` (dùng cho ``model/best``) bỏ optimizer/scheduler: bản đó chỉ để suy luận.
    """
    import torch

    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), str(directory / MODEL_WEIGHTS))
    torch.save(head.state_dict(), str(directory / HEAD_WEIGHTS))
    utils.write_json(dict(head_config or {}), directory / HEAD_CONFIG)
    if not weights_only:
        if optimizer is not None:
            torch.save(optimizer.state_dict(), str(directory / OPTIMIZER_FILE))
        if scheduler is not None:
            torch.save(scheduler.state_dict(), str(directory / SCHEDULER_FILE))
    return directory


def read_metadata(directory):
    """Số khía cạnh + bộ mã nhãn của checkpoint, để dùng lại ĐÚNG bài toán đã huấn luyện."""
    from src.training import checkpoints

    path = Path(directory) / HEAD_CONFIG
    if not path.is_file():
        raise checkpoints.CheckpointError(
            "Checkpoint {} thiếu {}. Không biết nó được huấn luyện với bộ khía cạnh nào thì không "
            "dùng lại được.".format(utils.rel(directory), HEAD_CONFIG))
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle) or {}


def check():
    """Thư viện cần có để ghi/đọc trọng số (rỗng là chạy được). KHÔNG cần `peft`: không có adapter."""
    problems = []
    for name in ("torch", "transformers"):
        if importlib.util.find_spec(name) is None:
            problems.append(
                "state_dict: chưa cài thư viện `{}` (pip install -r requirements.txt)".format(name))
    return problems
