# -*- coding: utf-8 -*-
"""Chính sách và chỗ lưu checkpoint - tách khỏi CÁCH HUẤN LUYỆN.

VÌ SAO TÁCH
LoRA (``src/training/lora.py``) chỉ là MỘT cách huấn luyện; checkpoint là việc thứ hai và dùng chung
cho mọi cách: cùng chính sách ``checkpoints.*``, cùng thư mục ``model/last``, ``model/best``,
``model/checkpoint-<bước>``, cùng file ``trainer_state.json``. Trainer nào cũng gọi ``Store``; thứ
trainer cung cấp là CÁCH GHI TRỌNG SỐ - một writer trong registry ``SAVERS`` (``src/training/savers/``).

BA PHẦN, BA CHỖ
    chính sách   settings(config)     đọc ``checkpoints.*``; thiếu khoá là lỗi kèm nơi khai
    nơi lưu      Store(out_dir, ...)  đường dẫn (từ ``configs/paths.yaml``), ảnh chụp, dọn, state
    cách ghi     SAVERS                ``adapter`` (LoRA); full fine-tune thêm writer của nó, xem
                                       ``src/training/savers/base.py``

CHẠY TIẾP
``trainer_state.json`` giữ vân tay ba giá trị (``config_sha256``, mã phiên bản dữ liệu, commit đã ghim).
Khác vân tay nghĩa là checkpoint thuộc lượt chạy khác: ``resume_state()`` báo lỗi thay vì trộn hai phép đo.
"""

import json
import shutil
from pathlib import Path

from src import paths, utils

STATE_FILE = "trainer_state.json"

POLICY_KEYS = (
    "every_n_steps",
    "keep_last_k",
    "save_last",
    "save_best",
    "delete_intermediate",
)

BOOL_KEYS = ("save_last", "save_best", "delete_intermediate")


class CheckpointError(Exception):
    """Thiếu khoá chính sách, hoặc checkpoint không dùng lại được cho lượt chạy này."""


def _missing(key):
    return ("Thiếu khoá {!r} trong cấu hình đã hợp nhất. Khai ở configs/experiments/training.yaml "
            "(mục `checkpoints`) - xem docs/05_config/05_experiments_shared.md.".format(
                "checkpoints.{}".format(key)))


def _get(config, key):
    node = config
    for part in str(key).split("."):
        if not isinstance(node, dict) or part not in node:
            raise CheckpointError(_missing(key))
        node = node[part]
    if node is None or node == "":
        raise CheckpointError(_missing(key))
    return node


def settings(config):
    """Chính sách checkpoint ĐANG dùng, dạng dict phẳng để ghi vào ``run.log``/``run_meta.json``."""
    found = {}
    for key in POLICY_KEYS:
        value = _get(config, "checkpoints.{}".format(key))
        if key in BOOL_KEYS:
            found[key] = bool(value)
        else:
            found[key] = int(value)
    return found


def check(config):
    """Việc phải sửa để bước lưu checkpoint chạy được (rỗng là chạy được)."""
    problems = []
    try:
        settings(config)
    except CheckpointError as exc:
        problems.append("checkpoint: {}".format(exc))
    for key in ("ckpt_last", "ckpt_best", "ckpt_snapshot"):
        try:
            paths.pattern(key, step=1)
        except KeyError as exc:
            problems.append("checkpoint: {}".format(exc))
    return problems


class Store:
    """Chỗ lưu của MỘT lượt chạy: đường dẫn, ảnh chụp trung gian, và ``trainer_state.json``.

    Store KHÔNG biết gì về LoRA hay kiến trúc model: nó nhận một writer (``src/training/savers/``) và
    chuyển tiếp ``payload`` cho writer đó, nên cùng một chính sách dùng được cho mọi cách huấn luyện.
    """

    def __init__(self, out_dir, policy):
        self.out_dir = Path(out_dir)
        self.policy = dict(policy or {})

    def last_dir(self):
        """Thư mục ``model/last``: đủ để chạy tiếp."""
        return self.out_dir / paths.pattern("ckpt_last")

    def best_dir(self):
        """Thư mục ``model/best``: chỉ để suy luận."""
        return self.out_dir / paths.pattern("ckpt_best")

    def snapshot_dir(self, step):
        """Thư mục ảnh chụp trung gian của một bước."""
        return self.out_dir / paths.pattern("ckpt_snapshot", step=int(step))

    def snapshots(self):
        """Các ảnh chụp trung gian, sắp theo số bước tăng dần."""
        parent = self.last_dir().parent
        if not parent.is_dir():
            return []
        found = []
        for path in parent.iterdir():
            suffix = path.name.rsplit("-", 1)[-1]
            if path.is_dir() and suffix.isdigit():
                found.append((int(suffix), path))
        return [path for _step, path in sorted(found)]

    def state(self, directory):
        """Nội dung state của một checkpoint; {} nếu chưa có hoặc file hỏng."""
        path = Path(directory) / STATE_FILE
        if not path.is_file():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return json.load(handle) or {}
        except (OSError, ValueError):
            return {}

    def write_state(self, directory, state):
        """Ghi state của một checkpoint. Trả về đường dẫn file."""
        return Path(utils.write_json(state, Path(directory) / STATE_FILE))

    def resume_state(self, fingerprint, require=True):
        """State của ``model/last`` nếu nó thuộc ĐÚNG lượt chạy này; None nếu không dùng lại được."""
        directory = self.last_dir()
        state = self.state(directory)
        if not state:
            return None
        if dict(state.get("fingerprint") or {}) != dict(fingerprint or {}):
            if require:
                raise CheckpointError(
                    "Checkpoint {} thuộc một lượt chạy KHÁC (cấu hình hoặc dữ liệu đã đổi). Muốn chạy "
                    "tiếp thì khôi phục đúng bản code và cấu hình cũ; muốn chạy mới thì xoá thư mục "
                    "kết quả {}.".format(utils.rel(directory), utils.rel(self.out_dir)))
            return None
        return state

    def save(self, directory, writer, state, payload=None, weights_only=False):
        """Ghi MỘT checkpoint bằng ``writer``: writer lo trọng số, Store lo thư mục và state."""
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        writer.save(directory, weights_only=weights_only, **dict(payload or {}))
        return self.write_state(directory, state)

    def prune(self, keep=None):
        """Xoá ảnh chụp cũ, chỉ giữ ``keep`` cái gần nhất (mặc định: ``checkpoints.keep_last_k``)."""
        keep = int(self.policy.get("keep_last_k") if keep is None else keep)
        found = self.snapshots()
        old = found[:-keep] if keep > 0 else found
        removed = []
        for path in old:
            shutil.rmtree(path, ignore_errors=True)
            removed.append(path.name)
        return removed
