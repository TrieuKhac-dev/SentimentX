# -*- coding: utf-8 -*-
"""Writer cho cách huấn luyện KHÔNG có adapter: chỉ đầu phân loại.

Dùng cho cách huấn luyện `none` (``src/training/none.py``): encoder KHÔNG được gói LoRA, nên không có
``save_pretrained`` để gọi - thứ duy nhất thay đổi giữa các lượt là đầu phân loại (``head.pt``). Writer
này vì vậy ghi ĐÚNG những file mà ``adapter`` ghi, chỉ bỏ phần trọng số của model.

VÌ SAO KHÔNG DÙNG LẠI ``adapter``: ``adapter.save`` gọi ``model.save_pretrained(...)``, mà ``model`` của
đường ``none`` là ``MultiHeadClassifier`` thuần (không phải ``PeftModel``) nên không có hàm đó. Tách
writer là cách đúng theo hợp đồng ở ``src/training/savers/base.py`` (cách huấn luyện khác thì thêm
writer của nó, KHÔNG chép lại phần chính sách lưu).

TÊN FILE TRÙNG với ``adapter`` là CHỦ Ý: ``head_config.json`` và ``head.pt`` là ĐỊNH DẠNG của đầu phân
loại, không phải của một cách huấn luyện - nhờ vậy ``lora.read_head_config`` đọc được checkpoint của
``none`` mà không cần đường thứ hai.
"""

import importlib.util
import json
from pathlib import Path

from src.core import utils

NAME = "head_only"
DESCRIPTION = "Chỉ đầu phân loại (không adapter): dùng cho cách huấn luyện `none`."

HEAD_CONFIG = "head_config.json"
HEAD_WEIGHTS = "head.pt"
OPTIMIZER_FILE = "optimizer.pt"
SCHEDULER_FILE = "scheduler.pt"


def save(directory, weights_only=False, model=None, head=None, head_config=None, optimizer=None,
         scheduler=None):
    """Ghi đầu phân loại vào ``directory``.

    ``model`` được NHẬN RỒI BỎ QUA: vòng lặp huấn luyện dùng chung đưa cùng một ``payload`` cho mọi
    writer (``Store.save`` chuyển tiếp nguyên dict), nên writer nào cũng nhận khoá này - chỉ ``adapter``
    mới dùng tới nó.

    ``weights_only=True`` (dùng cho ``model/best``) bỏ optimizer/scheduler: bản đó chỉ để suy luận.
    """
    import torch

    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
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
    """Thư viện cần có để ghi/đọc đầu phân loại (rỗng là chạy được)."""
    problems = []
    for name in ("torch", "transformers"):
        if importlib.util.find_spec(name) is None:
            problems.append(
                "head_only: chưa cài thư viện `{}` (pip install -r requirements.txt)".format(name))
    return problems
