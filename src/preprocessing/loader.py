# -*- coding: utf-8 -*-
"""Đọc dữ liệu ĐÃ XỬ LÝ để đưa cho model.

Dùng chung cho mọi model preprocessing, để mọi model đọc CÙNG một dataset.

Pipeline chỉ xuất MỘT dạng dữ liệu: bảng multi_head trong
data/processed/processed_<split>.csv (cột "text" + một cột cho mỗi aspect,
mỗi ô là mã nhãn 0/1/2/3).

Mọi dạng khác mà model cần đều được SINH TỪ bảng đó ngay tại đây:
    - to_multi_head_arrays() : (văn bản, ma trận nhãn) cho PhoBERT / ViSoBERT
    - to_absa_records()      : mẫu {"text", "labels"} cho Qwen3 (và ViTASA, khi có
                               checkpoint - hiện đang gác, xem docs/04_experiments/
                               04_backlog.md)

`known_aspects()` và `load_label_map()` nhận `version_id`: nơi gọi PHẢI truyền đúng
phiên bản đang xử lý (không để mặc định "bản mới nhất"), vì prompt của Qwen mô tả bộ
khía cạnh - dùng nhầm phiên bản là prompt mô tả sai bài toán mà nhìn vào vẫn thấy hợp lí.
"""

import json

from src import config, labels, utils, versioning


def _require(path):
    """Báo lỗi rõ ràng nếu chưa chạy pipeline."""
    if not path.exists():
        raise FileNotFoundError(
            "Chưa có {}. Hãy chạy 'python run_pipeline.py' trước.".format(
                utils.rel(path))
        )
    return path


def data_dir(version_id=None, dataset=None):
    """Thư mục dữ liệu đã xử lý của một phiên bản.

    Không truyền gì thì lấy phiên bản dataset mới nhất đang có trên đĩa.
    """
    version_id = version_id or versioning.latest_dataset(dataset)
    if not version_id:
        raise FileNotFoundError(
            "Chưa có dataset nào trong {}. Hãy chạy 'python run_pipeline.py' trước.".format(
                utils.rel(config.PROCESSED_DIR))
        )
    return versioning.processed_dir(version_id)


def load_label_map(version_id=None, dataset=None):
    """Đọc bảng mã nhãn: dataset, danh sách aspect, nhãn chữ <-> mã số."""
    path = data_dir(version_id, dataset) / "label_map.json"
    with open(_require(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def known_aspects(version_id=None, dataset=None):
    """Danh sách aspect của dataset đã xử lý (đọc từ label_map.json)."""
    return list(load_label_map(version_id, dataset)["aspects"])


def load_processed(split="train", version_id=None, dataset=None):
    """Đọc bảng multi_head đã xử lý: cột văn bản + các cột aspect chứa mã nhãn."""
    path = data_dir(version_id, dataset) / "{}.csv".format(split)
    return utils.read_csv(_require(path))


def to_multi_head_arrays(df, aspects=None):
    """Tách DataFrame đã xử lý thành (danh sách văn bản, ma trận nhãn).

    Trả về:
        texts  : list[str]         - độ dài N
        labels : list[list[int]]   - N x số aspect, mỗi ô là 0/1/2/3
    """
    aspects = aspects or known_aspects()
    texts = df[config.TEXT_COLUMN].astype(str).tolist()
    labels = df[aspects].astype(int).to_numpy().tolist()
    return texts, labels


def project_multi_head(matrix, projection):
    """Chiếu ma trận nhãn (N×A) sang không gian nhãn của thí nghiệm. Trả về (labels, mask).

    Vì sao trả về MASK chứ không xoá ô: với model mã hoá, mỗi ô là một bài toán con của cùng một
    review. "Loại một ô" nghĩa là ô đó không được tính vào loss và không được chấm, chứ không phải
    bỏ cả dòng - bỏ dòng thì mất luôn các khía cạnh khác của cùng review đó.

    `projection` là kết quả của `src.labels.project` (hoặc dict có `neutral_policy` và `codes`):
        neutral_policy drop          -> ô neutral: mask 0
        neutral_policy as_*          -> ô neutral: đổi sang cực đã chọn, mask 1
        neutral_policy keep          -> giữ nguyên, mask 1
        mã không có trong `codes`    -> mask 0 (giữ mã để tra lại, nhưng không tính)

    Tham số đặt tên `matrix` chứ không phải `labels`: `labels` là tên module của registry không
    gian nhãn ở đầu file, đặt trùng tên thì hàm sẽ không gọi được module đó.
    """
    policy = projection["neutral_policy"]
    codes = {int(code) for code in projection["codes"]}
    out, mask = [], []
    for row in matrix:
        out_row, mask_row = [], []
        for value in row:
            code = int(value)
            if code == labels.NEUTRAL and policy in ("as_negative", "as_positive"):
                out_row.append(labels.NEGATIVE if policy == "as_negative" else labels.POSITIVE)
                mask_row.append(1)
            else:
                out_row.append(code)
                mask_row.append(1 if code in codes else 0)
        out.append(out_row)
        mask.append(mask_row)
    return out, mask


def dropped_cells(mask):
    """Số ô bị loại khỏi tính toán, để ghi vào `metrics.json` cùng `dropped_neutral`."""
    return sum(1 for row in mask for value in row if not value)


def to_absa_records(split="train", aspects=None, version_id=None, dataset=None):
    """Sinh mẫu ABSA từ bảng đã xử lý.

    Mỗi mẫu: {"split": ..., "text": ..., "labels": {aspect: nhãn chữ}}
    Chỉ giữ các aspect THỰC SỰ được nhắc tới (mã khác 0), vì model sinh
    cần biết khía cạnh nào thật sự có trong câu.
    """
    label_map = load_label_map(version_id, dataset)
    id_to_label = {int(key): value for key, value in label_map["id_to_label"].items()}
    aspects = aspects or label_map["aspects"]

    frame = load_processed(split, version_id, dataset)
    texts = frame[config.TEXT_COLUMN].astype(str).tolist()
    codes = frame[aspects].astype(int).to_numpy().tolist()

    records = []
    for text, row_codes in zip(texts, codes):
        labels = {
            aspect: id_to_label.get(code, str(code))
            for aspect, code in zip(aspects, row_codes)
            if code != 0
        }
        records.append({"split": split, "text": text, "labels": labels})
    return records


def write_absa_records(split="train", path=None, aspects=None,
                       version_id=None, dataset=None):
    """Ghi mẫu ABSA ra JSONL (sinh từ bảng đã xử lý). Trả về đường dẫn file."""
    if path is None:
        path = data_dir(version_id, dataset) / "absa_{}.jsonl".format(split)
    records = to_absa_records(split, aspects=aspects, version_id=version_id,
                              dataset=dataset)
    return utils.write_jsonl(records, path)
