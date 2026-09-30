#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Xoá RÁC DO MÁY SINH RA trong cây làm việc. Không xoá gì khác.

VÌ SAO CẦN
`__pycache__/`, `*.pyc` và `.ipynb_checkpoints/` sinh ra khi chạy test hoặc mở notebook. Chúng bị
`.gitignore` chặn nên không lọt vào git, nhưng nằm lại trong cây làm việc: `git status` sạch mà thư
mục vẫn đầy file rác, và người sau không biết cái nào là rác cái nào là file thật.

LUẬT AN TOÀN (không thoả là KHÔNG xoá)
1. Chỉ đụng tới: thư mục `__pycache__/`, `.ipynb_checkpoints/`, và file `*.pyc`/`*.pyo`/`*.pyd`.
2. KHÔNG BAO GIỜ xoá file đang được git theo dõi, dù tên nó khớp mẫu rác. Đây là chốt chính: mã
   nguồn thì không bao giờ bị xoá vì một mẫu tên.

Cách dùng: python scripts/clean.py [--dry-run] [--root <thư mục>]
Mã thoát: `0` xong (kể cả khi không có gì để xoá) · `2` câu lệnh chưa rõ.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Trên Windows, console mặc định có thể không phải UTF-8 (ví dụ cp1252),
# khiến việc in tiếng Việt bị lỗi. Ép stdout/stderr sang UTF-8.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

JUNK_DIRS = ("__pycache__", ".ipynb_checkpoints")
JUNK_SUFFIXES = (".pyc", ".pyo", ".pyd")
SKIP_DIRS = (".git",)


def tracked_files(root):
    """Các đường dẫn đang được git theo dõi (dấu `/`), để TỪ CHỐI xoá nhầm."""
    try:
        done = subprocess.run(["git", "-C", str(root), "ls-files"],
                              capture_output=True, text=True)
    except OSError:
        return set()
    if done.returncode != 0:
        return set()
    return {line.strip().replace("\\", "/") for line in done.stdout.splitlines() if line.strip()}


def junk_paths(root):
    """Thư mục rác và file rác, để `clean()` quyết định xoá hay giữ.

    KHÔNG đi vào trong một thư mục rác: cả thư mục đó sắp bị xoá, nên đi vào chỉ để xoá lại lần hai
    (và lần hai thì file đã biến mất). Không đi vào `.git` vì ở đó không có rác của mình.
    """
    found = []
    for folder, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS]
        found.extend(Path(folder) / name for name in dirnames if name in JUNK_DIRS)
        dirnames[:] = [name for name in dirnames if name not in JUNK_DIRS]
        found.extend(Path(folder) / name for name in filenames
                     if Path(name).suffix in JUNK_SUFFIXES)
    return sorted(found)


def clean(root, dry_run=False, log=print):
    """Xoá rác, trả về danh sách đã xoá (hoặc sẽ xoá khi `dry_run`)."""
    tracked = tracked_files(root)
    removed, kept = [], []
    for path in junk_paths(root):
        relative = path.relative_to(root).as_posix()
        if relative in tracked:
            kept.append(relative)
            continue
        if path.is_dir():
            # Thư mục `__pycache__` đang được git theo dõi: không xoá, và cũng không xoá ruột nó.
            if any(item.startswith(relative + "/") for item in tracked):
                kept.append(relative)
                continue
            files = sorted(item for item in path.rglob("*") if item.is_file())
            log("  thư mục  {} ({} file)".format(relative, len(files)))
            if not dry_run:
                for item in files:
                    item.unlink()
                for folder in sorted((item for item in path.rglob("*") if item.is_dir()),
                                     key=lambda item: len(item.parts), reverse=True):
                    folder.rmdir()
                path.rmdir()
        else:
            log("  file     {}".format(relative))
            if not dry_run:
                path.unlink()
        removed.append(relative)
    for relative in kept:
        log("  GIỮ LẠI  {} (đang được git theo dõi)".format(relative))
    return removed


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Xoá rác do máy sinh ra (__pycache__, *.pyc, .ipynb_checkpoints).",
        epilog="Không bao giờ xoá file đang được git theo dõi.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Chỉ in ra thứ sẽ xoá, không xoá gì.")
    parser.add_argument("--root", default=None,
                        help="Gốc cây cần dọn (mặc định: gốc repo).")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    # Gốc repo suy từ `__file__`, GIỐNG các script khác - và KHÔNG import `src` ở đây: import là
    # Python ghi `src/**/__pycache__`, tức công cụ dọn rác tự sinh ra thứ nó vừa dọn (đã gặp thật:
    # chạy lần hai vẫn thấy 2 mục mới). Dọn rác phải chạy được cả khi `src/` đang hỏng.
    root = Path(args.root) if args.root else ROOT_DIR
    if not root.is_dir():
        print("LỖI: {} không phải thư mục.".format(root))
        return 2
    print("Dọn rác trong: {}".format(root))
    removed = clean(root, dry_run=args.dry_run)
    if not removed:
        print("Không có gì để xoá.")
    elif args.dry_run:
        print("--dry-run: {} mục SẼ bị xoá, chưa xoá gì.".format(len(removed)))
    else:
        print("Đã xoá {} mục.".format(len(removed)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
