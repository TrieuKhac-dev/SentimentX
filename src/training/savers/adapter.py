# -*- coding: utf-8 -*-
"""Writer cho LoRA: peft adapter + đầu phân loại, kèm optimizer/scheduler khi cần chạy tiếp.

Checkpoint của LoRA nhẹ (vài MB) vì trọng số gốc đóng băng. ``model/last`` giữ adapter + head +
optimizer + scheduler + ``trainer_state.json`` (đủ để chạy tiếp); ``model/best`` chỉ giữ adapter + head
(để suy luận).
"""

import importlib.util
import json
from pathlib import Path

from src import utils

NAME = "adapter"
DESCRIPTION = "LoRA (peft): adapter + một đầu phân loại cho mỗi khía cạnh."

HEAD_CONFIG = "head_config.json"
HEAD_WEIGHTS = "head.pt"
OPTIMIZER_FILE = "optimizer.pt"
SCHEDULER_FILE = "scheduler.pt"


def save(directory, weights_only=False, model=None, head=None, head_config=None, optimizer=None,
         scheduler=None):
    """Ghi adapter + đầu phân loại vào ``directory``.

    ``weights_only=True`` (dùng cho ``model/best``) bỏ optimizer/scheduler: bản đó chỉ để suy luận.
    """
    import torch

    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(directory))
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
    """Thư viện cần có để ghi/đọc adapter (rỗng là chạy được)."""
    problems = []
    for name in ("torch", "transformers", "peft"):
        if importlib.util.find_spec(name) is None:
            problems.append(
                "adapter: chưa cài thư viện `{}` (pip install -r requirements.txt)".format(name))
    return problems
