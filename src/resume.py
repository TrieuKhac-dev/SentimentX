# -*- coding: utf-8 -*-
"""Chạy tiếp sau khi bị ngắt: khối kết quả `predictions/part_*.jsonl` và quyết định resume.

VÌ SAO GHI THEO KHỐI
Một lượt val đầy đủ tốn hàng chục phút GPU. Chỉ ghi kết quả ở CUỐI thì đứt mạng ở mẫu thứ 1500 là
mất hết công đã bỏ ra. Ghi theo khối và đẩy xuống đĩa ngay: mất tối đa khối đang viết, và lần
chạy sau biết chính xác mẫu nào đã xong.

BA ĐIỀU KIỆN RESUME (docs/00_workflow/02_rules.md mục 13)
    `config_sha256`  dấu vân tay của config đã hợp nhất và văn bản prompt đã hợp nhất
    `data` (ma)      mã phiên bản dữ liệu
    `sha`            commit đã ghim
Lệch MỘT trong ba giá trị thì kết quả cũ KHÔNG còn so được với kết quả mới: phải chạy lại từ đầu
và ghi thành attempt mới (mục 14). Kết quả cũ không bị xoá - chỉ được chuyển sang một thư mục con
để không lẫn vào lượt chạy mới.
"""

import json
from pathlib import Path

from src import paths, runlog
from src.evaluation import records
from src.tracking import run_meta

# Ba chế độ mà `decide` có thể trả về.
MODE_NEW = "NEW"
MODE_RESUME = "RESUME"
MODE_STOP = "STOP"

# Ba khoá dùng để so hai lần chạy.
RESUME_KEYS = ("config_sha256", "data", "sha")

# Số bản ghi tối đa trong một khối. Nhỏ thì an toàn hơn nhưng nhiều file hơn; 50 đủ để một lượt
# val đầy đủ có vài chục khối.
RECORDS_PER_PART = 50


def fingerprint(config_sha256, version_id, repo_sha):
    """Bộ ba quyết định resume của LẦN CHẠY NÀY."""
    return {"config_sha256": config_sha256, "data": version_id, "sha": repo_sha}


def matches(attempt, want):
    """Attempt của lần chạy trước có trùng khít bộ ba không."""
    attempt = attempt or {}
    return all(str(attempt.get(key, "")) == str(want.get(key, "")) for key in RESUME_KEYS)


def decide(record, want, parts, force_new=False):
    """Quyết định chạy mới, chạy tiếp, hay dừng. Trả về (chế độ, lí do).

    record     `run_meta.json` của lần chạy trước trong cùng thư mục (None nếu chưa có)
    want       bộ ba của lần chạy này
    parts      số bản ghi đã có trong các khối
    force_new  người dùng yêu cầu chạy lại từ đầu
    """
    if force_new:
        return MODE_NEW, "theo yêu cầu chạy lại từ đầu (--new)"

    attempt = run_meta.attempt_of(record)
    if attempt is None:
        return MODE_NEW, "chưa có lần chạy nào trong thư mục này"

    if attempt.get("status") == run_meta.STATUS_FINISHED:
        if matches(attempt, want):
            return MODE_STOP, ("lần chạy trước đã XONG với đúng code, config và dữ liệu này - "
                               "không có gì để chạy lại")
        return MODE_NEW, ("lần chạy trước đã xong nhưng với code/config/dữ liệu KHÁC - số liệu cũ "
                          "không so được với số liệu mới")

    if not matches(attempt, want):
        return MODE_NEW, ("lần chạy trước bị ngắt với code/config/dữ liệu KHÁC - kết quả đã ghi "
                          "không dùng lại được")
    if parts <= 0:
        return MODE_NEW, "lần chạy trước bị ngắt nhưng chưa ghi được mẫu nào"
    return MODE_RESUME, "chạy tiếp từ {} mẫu đã xong của lần chạy trước".format(parts)


class Parts:
    """Các khối kết quả `predictions/part_NNNN.jsonl` của MỘT lần chạy.

    Mỗi bản ghi một dòng JSON, ghi xong là đẩy xuống đĩa. Dòng viết dở (mất điện giữa chừng) không
    đọc được JSON nên bị nhận ra và ĐẾM LẠI (`torn`), và mẫu đó sẽ được chạy lại - đúng hơn là tin
    vào một dòng viết dở.
    """

    def __init__(self, out_dir, max_records=RECORDS_PER_PART):
        self.out_dir = Path(out_dir)
        self.max_records = int(max_records)
        self.torn = 0
        self._cache = None

    # --- đọc ---

    def directory(self):
        """Thư mục chứa các khối (suy từ mẫu tên trong configs/paths.yaml)."""
        return self.out_dir / Path(paths.pattern("pred_parts", n=1)).parent

    def paths(self):
        """Các khối đang có, theo thứ tự số."""
        folder = self.directory()
        if not folder.is_dir():
            return []
        return sorted(folder.glob("part_*.jsonl"))

    def records(self):
        """Mọi bản ghi, theo thứ tự ghi. Kết quả được nhớ lại cho tới lần ghi tiếp theo."""
        if self._cache is None:
            self.torn = 0
            found = []
            for path in self.paths():
                for line in path.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    try:
                        found.append(json.loads(line))
                    except json.JSONDecodeError:
                        self.torn += 1
            self._cache = found
        return self._cache

    def count(self):
        """Số bản ghi đã có."""
        return len(self.records())

    def keys(self):
        """Khoá (chỉ số dòng gốc) của các mẫu đã chạy xong."""
        return {records.key_of(record) for record in self.records()}

    def rows(self, columns=None):
        """Bản ghi dạng bảng, để ghi `predictions.csv`."""
        columns = list(columns or records.COLUMNS)
        return [[record.get(column, "") for column in columns] for record in self.records()]

    # --- ghi ---

    def target(self):
        """Khối sẽ ghi tiếp: khối cuối nếu còn chỗ, không thì mở khối mới."""
        existing = self.paths()
        if existing:
            last = existing[-1]
            if len(last.read_text(encoding="utf-8").splitlines()) < self.max_records:
                return last
            number = int(last.stem.split("_")[-1]) + 1
        else:
            number = 1
        path = self.out_dir / paths.pattern("pred_parts", n=number)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def append(self, rows, columns=None):
        """Ghi thêm các dòng vào khối. Trả về đường dẫn khối, hoặc None nếu không có dòng nào."""
        if not rows:
            return None
        columns = list(columns or records.COLUMNS)
        path = self.target()
        with open(path, "a", encoding="utf-8", newline="\n") as handle:
            for row in rows:
                handle.write(json.dumps(dict(zip(columns, row)), ensure_ascii=False) + "\n")
            handle.flush()
        self._cache = None
        return path

