# -*- coding: utf-8 -*-
"""`local_json`: ghi bản ghi của lần chạy thành một file JSON trong cây báo cáo của repo.

Dùng khi không muốn (hoặc chưa thể) gọi máy chủ nhưng vẫn muốn có chỗ tra cứu: file nhỏ, đọc được
bằng mắt, và gom nhiều lần chạy vào một thư mục để so.

VÌ SAO KHÔNG PHẢI LÀ `run_meta.json`
`run_meta.json` nằm TRONG thư mục kết quả (thư mục đó có thể ở Drive), còn file ở đây nằm trong
cây báo cáo của repo. Hai chỗ khác nhau nên hai việc khác nhau: một cái mô tả lần chạy, một cái
gom lại để so.
"""

from pathlib import Path

from src import paths, runlog, utils
from src.tracking import base

NAME = "local_json"
DESCRIPTION = "Ghi bản ghi lần chạy ra JSON trong nhóm report experiment_registry."


def file_name(out_dir, info=None):
    """Tên file bản ghi: ghép các mảnh nhận dạng được, thiếu mảnh nào thì bỏ mảnh đó.

    Có mảnh model/method/exp thì hai thí nghiệm khác nhau không ghi đè lên nhau, kể cả khi trùng
    tên thư mục kết quả (tên thư mục chỉ gồm prompt, split và cách sinh).
    """
    info = dict(info or {})
    parts = [info.get("model"), info.get("method"), info.get("exp_id"), Path(out_dir).name]
    return "__".join(str(part) for part in parts if part) + ".json"


def path_for(out_dir, info=None):
    """Đường dẫn file bản ghi của một lần chạy."""
    return paths.report("experiment_registry") / "runs" / file_name(out_dir, info)


class _Session(base.Session):
    NAME = NAME

    def __init__(self, path):
        super().__init__(active=True)
        self.path = Path(path)

    def close(self, ok=True):
        """Ghi bản ghi. Ghi hỏng thì ghi lại vào `notes` chứ không ném."""
        payload = {
            "status": "FINISHED" if ok else "FAILED",
            "recorded_at": runlog.now(),
            "file": self.path.name,
            "params": self.params,
            "metrics": self.metrics,
            "artifacts": [path.name for path in self.artifacts],
        }
        try:
            utils.write_json(payload, self.path)
            self.note("đã ghi bản ghi lần chạy: {}".format(utils.rel(self.path)))
        except OSError as exc:
            self.note("không ghi được bản ghi lần chạy: {}".format(exc))
        return self.notes


def begin(config, dagshub, out_dir, info=None, log=None):
    """Mở phiên ghi bản ghi JSON. Không cần token, không cần mạng."""
    session = _Session(path_for(out_dir, info))
    if log is not None:
        log.step("bản ghi lần chạy: {}".format(utils.rel(session.path)))
    return session
