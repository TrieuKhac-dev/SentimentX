# -*- coding: utf-8 -*-
"""Đọc/ghi notebook và ô GHIM của notebook thí nghiệm.

VÌ SAO CÓ MODULE NÀY
Hai công cụ cùng sửa notebook: `scripts/pin.py` (ghi commit đã ghim) và `scripts/new_experiment.py`
(đặt `EXP_DIR` cho thí nghiệm mới). Nếu mỗi nơi tự biết "ô ghim là ô nào" thì sớm muộn chúng lệch
nhau, và lúc đó notebook đã giao chạy nhầm thí nghiệm mà không ai thấy. Định nghĩa ô ghim nằm ở đây,
một chỗ duy nhất.

KHÔNG CẦN `nbformat`
Việc ở đây chỉ là đọc/sửa/thay nguồn của một ô, nên `json` của thư viện chuẩn là đủ và các lệnh
chạy được trên mọi máy. `nbformat` chỉ cần khi muốn kiểm cấu trúc đầy đủ (pin.py làm việc đó nếu
máy có).
"""

import json

MARKER = "# --- BẢN CODE ĐÃ GHIM (do scripts/pin.py ghi; sửa tay sẽ bị ghi đè) ---"

EXP_DIR_PREFIX = "EXP_DIR = "


class NotebookError(Exception):
    """Notebook không đọc được, hoặc không có ô ghim."""


def read(path):
    """Đọc notebook. File hỏng thì báo lỗi rõ ràng kèm đường dẫn."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise NotebookError("{}: không đọc được notebook ({})".format(path, exc))


def write(path, notebook):
    """Ghi notebook, giữ nguyên định dạng đang dùng (thụt 1, không escape chữ có dấu)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(notebook, indent=1, ensure_ascii=False)
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8")


def source_of(cell):
    """Nguồn của một ô, dù nó lưu dạng chuỗi hay danh sách dòng."""
    source = cell.get("source") or []
    return source if isinstance(source, str) else "".join(source)


def pinned_cell(notebook, required=False):
    """Ô GHIM của notebook (ô mã có dấu MARKER), hoặc None.

    `required=True` thì thiếu ô ghim là lỗi: notebook thí nghiệm mà không biết nó ghim bản code nào
    thì không được chạy.
    """
    for cell in notebook.get("cells") or []:
        if cell.get("cell_type") == "code" and MARKER in source_of(cell):
            return cell
    if required:
        raise NotebookError("Notebook không có ô ghim ({}). Sửa bằng `python scripts/pin.py`."
                            .format(MARKER))
    return None


def set_exp_dir(notebook, experiment):
    """Đặt `EXP_DIR` trong ô GHIM thành `<model>/<method>/<expNNN>`. Trả về notebook đã sửa.

    Chỉ đổi dòng `EXP_DIR = ...`; các dòng khác của ô ghim (địa chỉ repo, nhánh, commit) để nguyên:
    commit do `scripts/pin.py` điền, và nó phải điền sau khi thí nghiệm đã có tên.
    """
    cell = pinned_cell(notebook, required=True)
    lines = []
    replaced = False
    for line in source_of(cell).splitlines():
        if line.startswith(EXP_DIR_PREFIX):
            lines.append("{}'{}'".format(EXP_DIR_PREFIX, experiment))
            replaced = True
        else:
            lines.append(line)
    if not replaced:
        raise NotebookError("Ô ghim không có dòng {!r} để đặt thí nghiệm.".format(EXP_DIR_PREFIX))
    cell["source"] = "\n".join(lines) + "\n"
    return notebook
