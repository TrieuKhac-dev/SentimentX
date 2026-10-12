# -*- coding: utf-8 -*-
"""Kiểm ví dụ few-shot KHÔNG RÒ RỈ từ split đánh giá. KHÔNG chạy model.

VÌ SAO CÓ
Ví dụ few-shot nằm TRONG ĐẦU VÀO của model (khe `{examples}` của prompt). Nếu một ví dụ được lấy từ
`val`/`test` thì model đã nhìn thấy đáp án của chính ô nó sắp được chấm - điểm lên mà không ai kiểm được,
và không có dấu vết nào trong `metrics.json`. Đây là lỗi im lặng, nên phải có một cửa chạy được TRƯỚC khi
giao notebook cho người chạy.

QUY ƯỚC ĐỌC FILE VÍ DỤ (đúng định dạng `configs/prompts/examples/*.txt`)
- Dòng bắt đầu bằng `#` là CHÚ THÍCH của dự án, KHÔNG gửi cho model ⇒ bỏ qua khi quét ví dụ.
- Một ví dụ được nhận diện bằng dòng `Review: "<văn bản>"`; văn bản lấy từ dấu `"` đầu tới dấu `"` cuối
  TRÊN CÙNG DÒNG đó.
- So khớp sau khi CHUẨN HOÁ: gộp mọi khoảng trắng thành một dấu cách, bỏ khoảng trắng đầu/cuối, chữ
  thường. Không so "gần đúng" - gần đúng thì không nói được là có rò rỉ hay không.

HAI ĐIỀU KIỆN
1. (LUÔN kiểm) Không ví dụ nào trùng văn bản với một review của `val`/`test`.
2. (chỉ khi `require_train=True`) Mọi ví dụ phải CÓ trong `train` - điều kiện cho ví dụ lấy từ dữ liệu,
   như ghi trong chú thích của chính file ví dụ ("CHỈ được lấy từ split train, ghi rõ train, dòng N").

KHÔNG ĐỌC ĐƯỢC DỮ LIỆU LÀ LỖI, KHÔNG PHẢI "SẠCH": thiếu `data/processed/<mã>/` thì hàm NÉM lỗi, vì
"không kiểm được" mà báo "không rò rỉ" là nói dối kiểu khác.
"""

import json
from pathlib import Path

from src.core import config, dataset as dataset_module, paths, utils, versioning
from src.preprocessing import loader

# Dấu nhận diện một ví dụ trong file few-shot, và dấu chú thích không gửi cho model.
REVIEW_PREFIX = "Review:"
COMMENT_PREFIX = "#"
# Hai split bị coi là "đáp án": có ví dụ trùng ở đây là rò rỉ.
EVAL_SPLITS = ("val", "test")


class ExamplesLeakError(Exception):
    """Không kiểm được (thiếu file/dữ liệu) hoặc file ví dụ sai định dạng."""


def normalize(text):
    """Chuẩn hoá văn bản để so trùng: gộp khoảng trắng, bỏ đầu/cuối, chữ thường."""
    return " ".join(str(text).split()).lower()


def example_reviews(path):
    """Danh sách `(số dòng, văn bản review)` của một file ví dụ; bỏ dòng chú thích/trống."""
    path = Path(path)
    if not path.is_file():
        raise ExamplesLeakError("Không thấy file ví dụ {}.".format(utils.rel(path)))
    found = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith(COMMENT_PREFIX) or not line.startswith(REVIEW_PREFIX):
            continue
        text = line[len(REVIEW_PREFIX):].strip()
        first, last = text.find('"'), text.rfind('"')
        if first < 0 or last <= first:
            raise ExamplesLeakError(
                "Dòng {} của {} có `Review:` nhưng không có văn bản trong hai dấu \": {!r}.".format(
                    number, utils.rel(path), line))
        found.append((number, text[first + 1:last].strip()))
    if not found:
        raise ExamplesLeakError(
            "Không thấy dòng nào bắt đầu bằng `{} \"...\"` trong {} - kiểm lại định dạng file ví dụ."
            .format(REVIEW_PREFIX, utils.rel(path)))
    return found


def split_texts(split, version_id=None, dataset=None):
    """Tập văn bản ĐÃ CHUẨN HOÁ của một split trong phiên bản dữ liệu đã xử lý."""
    frame = loader.load_processed(split, version_id=version_id, dataset=dataset)
    column = config.TEXT_COLUMN
    if column not in frame.columns:
        raise ExamplesLeakError(
            "Bảng đã xử lý của split '{}' không có cột văn bản '{}' (có: {}).".format(
                split, column, ", ".join(str(name) for name in frame.columns)))
    return {normalize(value) for value in frame[column].astype(str).tolist()}


def _read_json(path):
    """Đọc JSON; file thiếu/hỏng trả `{}` (việc chọn phiên bản không được làm cửa kiểm chết)."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle) or {}
    except (OSError, ValueError):
        return {}


def newest_run_version():
    """Phiên bản dữ liệu của LƯỢT CHẠY MỚI NHẤT trên đĩa (đọc `metrics.json`), hoặc `None`.

    Vì sao không lấy "bản mới nhất" từ `configs/datasets/`: máy này có cả `v0.3.0` trên đĩa trong khi
    MỌI lượt đang chạy dùng `v0.2.0`. Kiểm ví dụ trên phiên bản khác là kiểm nhầm dữ liệu - và
    `src/preprocessing/loader.py` đã dặn đúng điều này ("nơi gọi PHẢI truyền đúng phiên bản đang xử lý,
    không để mặc định bản mới nhất").
    """
    newest = None
    for path in paths.experiments_dir().glob("*/*/*/results/*/" + paths.pattern("metrics_json")):
        try:
            stamp = path.stat().st_mtime
        except OSError:                                   # lượt chạy vừa bị xoá giữa vòng lặp
            continue
        if newest is None or stamp > newest[0]:
            newest = (stamp, path)
    return _read_json(newest[1]).get("version_id") if newest else None


def resolve_version(version_id=None, dataset=None):
    """`(mã phiên bản, NGUỒN của mã đó)` để kiểm.

    Thứ tự: cờ `--version` > phiên bản của lượt chạy mới nhất trên đĩa > cấu hình dataset mới nhất.
    Trả kèm nguồn để báo cáo in ra: người đọc phải biết con số được kiểm trên phiên bản nào và vì sao.
    """
    if version_id:
        return version_id, "cờ --version"
    from_newest = newest_run_version()
    if from_newest:
        return from_newest, "phiên bản của LƯỢT CHẠY MỚI NHẤT trên đĩa"
    return (versioning.compute_id(dataset_module.load_config(dataset)),
            "cấu hình dataset mới nhất (trên đĩa KHÔNG có lượt chạy nào)")


def check(path, version_id=None, dataset=None, require_train=False):
    """Kiểm một file ví dụ; trả bản ghi kết quả (không ném lỗi khi chỉ có rò rỉ).

    `rò rỉ` là danh sách `{"dòng": <số dòng trong file>, "split": "val"|"test"}`. `thiếu trong train`
    chỉ được điền khi `require_train=True`.
    """
    reviews = example_reviews(path)
    version_id, source = resolve_version(version_id, dataset)
    train = split_texts("train", version_id=version_id, dataset=dataset)
    eval_sets = {split: split_texts(split, version_id=version_id, dataset=dataset)
                 for split in EVAL_SPLITS}
    leaks, missing = [], []
    for number, text in reviews:
        normalized = normalize(text)
        for split, values in eval_sets.items():
            if normalized in values:
                leaks.append({"dòng": number, "split": split})
        if require_train and normalized not in train:
            missing.append({"dòng": number})
    return {
        "file": utils.rel(Path(path)),
        "version_id": version_id,
        "version_source": source,
        "examples": len(reviews),
        "in_train": sum(1 for _number, text in reviews if normalize(text) in train),
        "require_train": bool(require_train),
        "rò rỉ": leaks,
        "thiếu trong train": missing,
        "sạch": not leaks and not missing,
    }

