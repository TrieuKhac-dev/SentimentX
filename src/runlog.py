# -*- coding: utf-8 -*-
"""Nhật ký của MỘT lần chạy: `run.log` luôn có, `errors.json` chỉ khi thật có lỗi.

VÌ SAO PHẢI CÓ
Trên Colab, khi notebook dừng giữa chừng thì người đọc chỉ còn file trên Drive: không có log thì
không biết đã chạy tới đâu, dừng ở bước nào, vì sao. `errors.json` là bản máy đọc được của phần
lỗi, để lần chạy sau (và CI) không phải dò mắt trong log.

BỐN QUY TẮC
    1. Ghi NGAY, không đệm: mỗi dòng `flush()` xuống đĩa. Tiến trình bị dừng đột ngột thì log vẫn
       còn tới dòng cuối cùng đã chạy - nhờ vậy biết được đã đi tới đâu.
    2. `run.log` mở ở ĐẦU lần chạy, chế độ ghi thêm, nên chạy vào cùng thư mục lần sau vẫn giữ
       được log của lần trước (mỗi lần chạy có một khối tiêu đề riêng).
    3. `errors.json` CHỈ được tạo khi thật có lỗi. Không tạo file rỗng cho có: file rỗng làm
       người đọc tưởng đã từng có lỗi, còn thiếu file thì rõ ràng là không lỗi.
    4. Mỗi dòng bắt đầu bằng mục trong ngoặc vuông, để `grep '\\[TAG\\]'` là ra:

        [RUN]   bắt đầu / kết thúc lần chạy, chế độ NEW hay RESUME, cấu hình đang dùng
        [STEP]  bước đang chạy, kèm số giây nếu bước đó tốn thời gian
        [WARN]  việc không làm chết run nhưng người đọc phải biết
        [ERROR] lỗi - đồng thời được ghi vào `errors.json`
        [TRACK] ghi kết quả lên máy chủ MLflow: thành công hay thất bại

       Mục đứng ở ĐẦU dòng (không có tiền tố thời gian) để dòng log đọc và tìm được bằng máy;
       mốc thời gian nằm ở khối tiêu đề của mỗi lần chạy và trong `errors.json`.

CÁCH DÙNG
    with runlog.start(out_dir, mode="NEW", info={"prompt": prompt.name}) as log:
        log.step("sinh xong 100 mẫu", seconds=123.4)
        log.warn("chưa log được lên MLflow: thiếu DAGSHUB_TOKEN")
    # Lỗi thoát ra khỏi khối `with` -> errors.json được ghi RỒI mới ném tiếp, nên người đọc
    # vẫn có file để xem dù chương trình dừng.

`requires` là danh sách thứ còn thiếu để chạy được (JVM, model trên Hugging Face, VRAM...).
Thiếu thứ gì thì ghi rõ thứ đó: `errors.json` là chỗ tra cho câu hỏi "máy này còn thiếu gì".
"""

import json
import platform
import sys
import traceback
from datetime import datetime
from pathlib import Path

from src import paths, utils

# Các mục được phép. Mục lạ là lỗi lập trình, không phải lỗi lúc chạy.
# `CONFIG` là cấu hình ĐANG dùng: khoá nào bị lớp nào đè, và giá trị hiệu lực của các khoá quyết
# định kết quả. Bảng đó cũng được in ra màn hình, nhưng notebook nộp cho giảng viên không giữ
# output, nên muốn tra lại thì phải có trong file.
TAGS = ("RUN", "CONFIG", "STEP", "WARN", "ERROR", "TRACK")


def now():
    """Mốc thời gian đang dùng trong log. Kiểu sắp xếp được, không phụ thuộc vùng."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log_path(out_dir):
    """Đường dẫn `run.log` của một thư mục kết quả."""
    return Path(out_dir) / paths.pattern("run_log")


def errors_path(out_dir):
    """Đường dẫn `errors.json` của một thư mục kết quả."""
    return Path(out_dir) / paths.pattern("errors")


def flatten(data, prefix=""):
    """Đổi dict lồng nhau thành các cặp 'khoá.con' -> giá trị, để ghi vào log một dòng một mục."""
    found = {}
    for key, value in (data or {}).items():
        name = "{}.{}".format(prefix, key) if prefix else str(key)
        if isinstance(value, dict):
            found.update(flatten(value, name))
        elif isinstance(value, (list, tuple)):
            found[name] = ", ".join(str(item) for item in value)
        else:
            found[name] = value
    return found


def read_errors(out_dir):
    """Đọc `errors.json` của một thư mục kết quả. Chưa có file (tức là không lỗi) thì trả None."""
    path = errors_path(out_dir)
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


class RunLog:
    """Log của một lần chạy. Mỗi thư mục kết quả có một `run.log`."""

    def __init__(self, out_dir, mode="NEW", info=None):
        self.out_dir = Path(out_dir)
        self.mode = str(mode).upper()
        self.info = dict(info or {})
        self.errors = []
        self.warnings = []
        self._closers = []
        self.started = datetime.now()
        self.path = log_path(self.out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        # newline="\n": log được đọc ở cả Linux (Colab) và Windows. Để hệ điều hành tự đổi thì
        # cùng một file sẽ có hai kiểu xuống dòng tuỳ máy nào ghi nó.
        self._handle = open(self.path, "a", encoding="utf-8", newline="\n")
        self._raw("=== lần chạy {} - mode={} ===".format(now(), self.mode))
        # Dòng này là mốc cho người đọc và cho kiểm tra tự động: NEW là lần chạy đầu, RESUME là
        # chạy tiếp sau khi bị ngắt (P4 T8).
        self.line("RUN", "mode={}".format(self.mode))
        for key, value in flatten(self.info).items():
            self.line("RUN", "{}={}".format(key, value))

    # --- ghi ---

    def _raw(self, text):
        """Ghi một dòng và đẩy xuống đĩa ngay. Dùng cho tiêu đề (không có mục)."""
        self._handle.write(text + "\n")
        self._handle.flush()
        return text

    def line(self, tag, message):
        """Ghi một dòng có mục. Mục lạ là lỗi lập trình nên báo ngay."""
        tag = str(tag).upper()
        if tag not in TAGS:
            raise ValueError("Mục log '{}' không có trong {}. Sửa lại chỗ gọi.".format(
                tag, ", ".join(TAGS)))
        return self._raw("[{}] {}".format(tag, message))

    def run(self, message):
        """Mốc của lần chạy: bắt đầu, kết thúc, chế độ NEW/RESUME, cấu hình."""
        return self.line("RUN", message)

    def step(self, message, seconds=None):
        """Bước đang chạy. `seconds` là thời gian bước đó đã tốn, nếu đo được."""
        if seconds is not None:
            message = "{} | {:.1f} giây".format(message, float(seconds))
        return self.line("STEP", message)

    def config(self, message):
        """Cấu hình hiệu lực hoặc một khoá bị lớp sau đè (bảng ghi đè)."""
        return self.line("CONFIG", message)

    def track(self, message):
        """Ghi nhận kết quả lên máy chủ MLflow: thành công hay thất bại."""
        return self.line("TRACK", message)

    def warn(self, message, context=None):
        """Việc không làm chết run nhưng người đọc phải biết (KHÔNG tạo `errors.json`)."""
        self.warnings.append({"at": now(), "message": str(message),
                              "context": dict(context or {})})
        return self.line("WARN", message)

    def error(self, message, exc=None, context=None, requires=None):
        """Ghi một lỗi vào log và vào `errors.json` (không ném). Trả về bản ghi vừa thêm.

        `requires` là danh sách thứ còn thiếu để chạy được (JVM, model trên Hugging Face, VRAM).
        """
        entry = self._entry("ERROR", message, exc=exc, context=context, requires=requires)
        self.errors.append(entry)
        self.line("ERROR", message)
        self.line("ERROR", "chi tiết (kiểu lỗi, vết gọi, thứ còn thiếu): {}".format(
            paths.pattern("errors")))
        return entry

    def exception(self, exc=None, context=None, requires=None):
        """Ghi lỗi đang bắt được (dùng trong khối `except`). Không ném lại."""
        exc = exc if exc is not None else sys.exc_info()[1]
        message = "{}: {}".format(type(exc).__name__, exc) if exc is not None else "lỗi không rõ"
        return self.error(message, exc=exc, context=context, requires=requires)

    def _entry(self, level, message, exc=None, context=None, requires=None):
        entry = {"at": now(), "level": level, "message": str(message)}
        if exc is not None:
            entry["type"] = type(exc).__name__
            entry["traceback"] = "".join(
                traceback.format_exception(type(exc), exc, exc.__traceback__))
        if context:
            entry["context"] = dict(context)
        if requires:
            entry["requires"] = list(requires)
        return entry

    # --- kết thúc ---

    def elapsed(self):
        """Số giây đã chạy."""
        return (datetime.now() - self.started).total_seconds()

    def payload(self):
        """Nội dung `errors.json`: thông tin lần chạy, lỗi, và cảnh báo (để có ngữ cảnh).

        Chỉ ghi tên thư mục, không ghi đường dẫn tuyệt đối: file này được đem từ Colab về máy
        khác, đường dẫn tuyệt đối của máy cũ chỉ gây nhiễu.
        """
        return {
            "run": {
                "mode": self.mode,
                "out_dir": self.out_dir.name,
                "log": paths.pattern("run_log"),
                "started": self.started.strftime("%Y-%m-%d %H:%M:%S"),
                "finished": now(),
                "seconds": round(self.elapsed(), 1),
                "info": self.info,
                # Máy đã chạy: lỗi trên Colab và lỗi trên máy cá nhân khác nhau rất nhiều, mà
                # errors.json có thể bị đem từ máy này sang máy khác trước khi có người đọc.
                "machine": {
                    "system": platform.platform(),
                    "python": platform.python_version(),
                },
            },
            "errors": self.errors,
            "warnings": self.warnings,
        }

    def close(self):
        """Ghi `errors.json` nếu có lỗi, rồi đóng log. Gọi lại lần nữa không sao.

        Việc đã đăng ký bằng `on_close` được chạy TRƯỚC khi file đóng, nên chúng vẫn ghi được
        dòng `[TRACK]`/`[WARN]` cuối cùng. `ok=False` nghĩa là lần chạy đã có lỗi.
        """
        if self._handle.closed:
            return None
        ok = not self.errors
        for callback in self._closers:
            try:
                callback(ok=ok)
            except Exception as exc:  # noqa: BLE001 - đang đóng log, không được ném
                self.line("WARN", "việc lúc đóng log hỏng: {}: {}".format(
                    type(exc).__name__, exc))
        payload = self.payload() if self.errors else None
        if payload is not None:
            utils.write_json(payload, errors_path(self.out_dir))
        self._handle.close()
        return payload

    def on_close(self, callback):
        """Đăng ký một hàm chạy lúc đóng log: `callback(ok=...)`.

        Dùng cho việc PHẢI xong dù lần chạy thành công hay hỏng, ví dụ kết thúc phiên ghi nhận
        lên máy chủ (xem `src/tracking/`). Hàm được gọi bằng từ khoá `ok` nên chỉ cần nhận `ok`.
        """
        self._closers.append(callback)
        return callback

    def __enter__(self):
        return self

    def __exit__(self, kind, exc, tb):
        """Đóng log; lỗi thoát ra khỏi khối `with` được ghi lại TRƯỚC khi ném tiếp.

        Bắt cả `BaseException` nên `KeyboardInterrupt` cũng vào log: người dùng dừng notebook
        giữa chừng là việc phải tra lại được, không phải việc bỏ qua.
        """
        if exc is not None:
            self.error("{}: {}".format(type(exc).__name__, exc), exc=exc,
                       context={"kind": getattr(kind, "__name__", str(kind))})
            self.run("kết thúc vì lỗi sau {:.1f} giây".format(self.elapsed()))
        else:
            self.run("kết thúc sau {:.1f} giây".format(self.elapsed()))
        self.close()
        return False


def start(out_dir, mode="NEW", info=None):
    """Mở log của một lần chạy. Dùng như context manager để lỗi luôn được ghi lại.

    `mode`: `NEW` cho lần chạy đầu, `RESUME` khi chạy tiếp sau khi bị ngắt (P4 T8). Chế độ được
    ghi thành dòng `[RUN] mode=...` nên đọc log là biết con số trong thư mục này do lần chạy nào
    sinh ra, và lần đó có chạy liền mạch hay không.
    """
    return RunLog(out_dir, mode=mode, info=info)


