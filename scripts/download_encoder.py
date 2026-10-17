# -*- coding: utf-8 -*-
"""Tải base CafeBERT về máy để encoder runtime chạy OFFLINE.

Đây là công cụ CHẠY TAY: ``serving/inference/encoder.py`` chỉ BÁO thiếu base rồi trỏ tới
lệnh này, không tự gọi mạng.

CÁCH DÙNG
    python scripts/download_encoder.py
    python scripts/download_encoder.py --repo uitnlp/CafeBERT ^
        --revision af76fcf2a04096b2b54b348a3e4eb48253c93c5d --dest data/models/cafebert-base

Nếu ``--dest`` đã có đủ file cần thiết thì không tải lại (mã thoát 0).
"""

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Trên Windows, console mặc định có thể không phải UTF-8 nên in tiếng Việt bị lỗi.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_REPO = "uitnlp/CafeBERT"
DEFAULT_REVISION = "af76fcf2a04096b2b54b348a3e4eb48253c93c5d"
DEFAULT_DEST = "data/models/cafebert-base"

# Các file base CafeBERT cần có để AutoModel/AutoTokenizer nạp được.
REQUIRED_FILES = (
    "config.json",
    "model.safetensors",
    "sentencepiece.bpe.model",
    "special_tokens_map.json",
    "tokenizer_config.json",
)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Tải base CafeBERT về máy.")
    parser.add_argument("--repo", default=DEFAULT_REPO, help="Repo Hugging Face.")
    parser.add_argument("--revision", default=DEFAULT_REVISION, help="Commit/revision cần ghim.")
    parser.add_argument("--dest", default=DEFAULT_DEST, help="Thư mục đích (tương đối gốc repo).")
    return parser.parse_args(argv)


def size_of(directory):
    return sum(path.stat().st_size for path in Path(directory).rglob("*") if path.is_file())


def has_all(directory):
    return all((Path(directory) / name).is_file() for name in REQUIRED_FILES)


def main(argv=None):
    args = parse_args(argv)
    dest = Path(args.dest)
    if not dest.is_absolute():
        dest = ROOT_DIR / dest

    if dest.is_dir() and has_all(dest):
        print("Đã có base CafeBERT tại {} ({} bytes). Không tải lại.".format(dest, size_of(dest)))
        return 0

    from huggingface_hub import snapshot_download

    path = snapshot_download(repo_id=args.repo, revision=args.revision, local_dir=str(dest))
    print("Đã tải về: {}".format(path))
    print("Kích thước: {} bytes".format(size_of(dest)))
    if not has_all(dest):
        print("CẢNH BÁO: thiếu file cần thiết trong {}.".format(dest), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())