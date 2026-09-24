# -*- coding: utf-8 -*-
"""EDA 03 - Chất lượng dữ liệu và nhiễu.

Đo lường (KHÔNG sửa) các nhóm nhiễu: review rỗng, trùng chính xác, trùng theo
KHOÁ so trùng, ứng viên gibberish, emoji, ký tự lặp, teencode / từ lạ, dấu hiệu
quảng cáo và dấu hiệu code / HTML. Số liệu là căn cứ để chọn policy cho Data
Pipeline (configs/pipeline.yaml).

Khoá so trùng được đọc từ `clean.deduplicate.ignore_diacritics` trong
configs/pipeline.yaml, nên khi đổi quy tắc so trùng thì số liệu EDA đổi theo
ĐÚNG như pipeline (hai bên không lệch nhau).

TEENCODE / TỪ LẠ CHỈ ĐƯỢC ĐO Ở ĐÂY. Pipeline KHÔNG loại bỏ, KHÔNG thay thế và
KHÔNG viết lại teencode - không có bằng chứng khoa học nào để khẳng định một cách
viết lóng là "sai" và cần sửa, nên việc duy nhất làm được là đo và ghi lại. Bước
Final Validate của pipeline chứng minh điều này bằng số liệu (hạng mục "Văn bản
chỉ đổi hình thức").

Báo cáo chỉ có số liệu: không có câu giải thích, mỗi số liệu chỉ xuất hiện một
lần (bảng HOẶC biểu đồ), bản đầy đủ nằm ở CSV.
"""

import random
from collections import Counter

from src import config, utils

# Số mục phổ biến nhất đưa vào bảng/biểu đồ
TOP_N = 20

# Số lần xuất hiện tối thiểu để một từ lạ được xếp vào bảng
# (từ chỉ xuất hiện 1 lần là nhiễu vặt, không đáng đưa vào báo cáo)
MIN_CANDIDATE_COUNT = 3

# Số từ phổ biến nhất dùng cho phép KIỂM TRA DƯƠNG TÍNH GIẢ: những từ nằm trong
# nhóm này chắc chắn là từ thật, nên nếu có từ nào bị gắn cờ thì quy tắc đang sai.
AUDIT_TOP_WORDS = 300

# Ví dụ minh hoạ: số ví dụ mỗi nhóm mỗi split ghi ra CSV (bảng chỉ hiện ví dụ đầu)
EXAMPLES_PER_SPLIT_CSV = 3
EXAMPLES_PER_SPLIT_TABLE = 1

# Hạt giống cố định cho việc lấy mẫu: chạy lại cho ra đúng những ví dụ cũ
EXAMPLE_SEED = 20240917

# Các nhóm nhiễu được lấy ví dụ minh hoạ
EXAMPLE_GROUPS = (
    ("ứng viên gibberish", utils.is_gibberish),
    ("chỉ emoji / dấu câu", utils.is_only_emoji_and_punct),
    ("có ký tự lặp", utils.has_repeated_chars),
    ("có dấu hiệu quảng cáo", utils.is_advertisement),
    ("có dấu hiệu code / HTML", utils.is_code_like),
)


def _collect_metrics(texts, key_of):
    """Tính các chỉ số chất lượng cho một dãy văn bản.

    `key_of` là khoá so trùng (xem `run`) - truyền vào để EDA và pipeline dùng
    ĐÚNG cùng một quy tắc so trùng.
    """
    keys = texts.map(key_of)
    return {
        "review rỗng": int((texts.str.strip() == "").sum()),
        "trùng chính xác": int(texts.duplicated().sum()),
        "trùng theo khoá so trùng": int(keys.duplicated().sum()),
        "ứng viên gibberish": int(texts.map(utils.is_gibberish).sum()),
        "có emoji": int(texts.map(utils.has_emoji).sum()),
        "chỉ emoji / dấu câu": int(texts.map(utils.is_only_emoji_and_punct).sum()),
        "có ký tự lặp": int(texts.map(utils.has_repeated_chars).sum()),
        "có dấu hiệu quảng cáo": int(texts.map(utils.is_advertisement).sum()),
        "có dấu hiệu code / HTML": int(texts.map(utils.is_code_like).sum()),
    }


def _sample_examples(texts, predicate, limit, rng):
    """Chọn NGẪU NHIÊN (hạt giống cố định) các review thoả điều kiện.

    Trả về danh sách [(vị trí dòng, văn bản)] đã sắp theo vị trí.
    """
    matched = [(index, text) for index, text in enumerate(texts) if predicate(text)]
    if len(matched) <= limit:
        return matched
    return sorted(rng.sample(matched, limit))


def run(context):
    splits = context["splits"]
    out_dir = context["out_dir"]
    files = []

    # Quy tắc của KHOÁ so trùng: đọc từ config pipeline để EDA và bước Clean dùng
    # đúng một quy tắc (khi tắt `ignore_diacritics`, khoá sẽ giữ dấu tiếng Việt).
    dedup_cfg = utils.load_pipeline_config()["steps"]["clean"]["deduplicate"]
    ignore_diacritics = bool(dedup_cfg.get("ignore_diacritics", False))

    def _key(text):
        return utils.dedup_key(text, ignore_diacritics=ignore_diacritics)

# ---
    # 1. Chỉ số chất lượng theo từng split
# ---
    metric_rows = []
    per_split = {}
    token_counter = Counter()
    emoji_counter = Counter()

    for name, df in splits.items():
        texts = df[config.TEXT_COLUMN].astype(str)
        metrics = _collect_metrics(texts, _key)
        per_split[name] = metrics
        n_rows = len(texts)
        for label, value in metrics.items():
            metric_rows.append([
                name, label, value,
                round(100 * value / n_rows, 2) if n_rows else 0.0,
            ])
        for text in texts:
            token_counter.update(utils.tokenize(text))
            for sequence in utils.EMOJI_PATTERN.findall(text):
                emoji_counter[utils.emoji_key(sequence)] += 1

    files.append(utils.rel(utils.write_csv(
        metric_rows,
        ["split", "chỉ số", "số lượng", "tỉ lệ %"],
        out_dir / "03_quality_metrics.csv",
    )))

    metric_labels = list(next(iter(per_split.values())).keys())

    # Số lượng review theo từng nhóm nhiễu: chỉ trình bày một lần, ở dạng bảng.
    # Tỉ lệ % tương ứng nằm trong file 03_quality_metrics.csv.
    metric_table = {
        "title": "Chỉ số chất lượng theo split",
        "columns": ["chỉ số"] + list(splits) + ["tổng 3 split"],
        "rows": [
            [label]
            + [per_split[name][label] for name in splits]
            + [sum(per_split[name][label] for name in splits)]
            for label in metric_labels
        ],
        "num_columns": list(range(1, len(splits) + 2)),
    }

# ---
    # 2. Teencode / từ lạ: quét toàn bộ token của cả 3 split
    #
    # Chỉ báo cáo ở mức TOKEN. Không báo cáo "số review có teencode" vì tỉ lệ
    # review dính chỉ tiêu này là ~44% (gần một nửa dữ liệu) nên không phân biệt
    # được gì; danh sách token mới là thông tin dùng được.
# ---
    candidate_rows = []
    reason_tokens = Counter()
    reason_hits = Counter()
    for token, count in token_counter.most_common():
        reasons = utils.teencode_reasons(token)
        if not reasons:
            continue
        candidate_rows.append([token, count, " + ".join(reasons)])
        for reason in reasons:
            reason_tokens[reason] += 1
            reason_hits[reason] += count

    files.append(utils.rel(utils.write_csv(
        candidate_rows,
        ["từ", "số lần xuất hiện", "lí do bị gắn cờ"],
        out_dir / "03_quality_teencode_candidates.csv",
    )))

    # Quy mô từng quy tắc gắn cờ. Bảng này cho thấy đây là các quy tắc CẤU TRÚC
    # (không có nguyên âm, chữ ngoài bảng chữ cái tiếng Việt...), không phải một
    # từ điển teencode: nó vừa bắt được cách viết tắt thật, vừa gắn cờ cả từ
    # tiếng Anh / tên thương hiệu trong review.
    reason_rows = [
        [reason, reason_tokens[reason], reason_hits[reason]]
        for reason in utils.REASON_ORDER
    ]

    reason_table = {
        "title": "Các quy tắc gắn cờ và quy mô mỗi quy tắc (3 split)",
        "columns": ["lí do bị gắn cờ", "số từ khác nhau",
                    "tổng số lần xuất hiện"],
        "rows": reason_rows,
        "num_columns": [1, 2],
    }

    candidate_table = {
        "title": ("Top {} từ bị gắn cờ teencode / từ lạ, xuất hiện từ {} lần "
                  "(3 split)").format(TOP_N, MIN_CANDIDATE_COUNT),
        "columns": ["từ", "số lần", "lí do bị gắn cờ"],
        "rows": [row for row in candidate_rows
                 if row[1] >= MIN_CANDIDATE_COUNT][:TOP_N],
        "num_columns": [1],
    }

    flagged_distinct = sum(
        1 for row in candidate_rows if row[1] >= MIN_CANDIDATE_COUNT
    )

    # KIỂM TRA DƯƠNG TÍNH GIẢ (ghi ra CSV, không lên báo cáo): trong AUDIT_TOP_WORDS
    # từ phổ biến nhất của dữ liệu - chắc chắn là từ thật - có từ nào bị gắn cờ
    # không? Với dữ liệu cosmetics: 13 từ, và cả 13 đều là viết tắt thật
    # (k, mn, đc, mng, sp, kh, r, n, vs, ng, cx, m, t) -> không có dương tính giả
    # trên từ thông thường.
    common_flagged = []
    for token, count in token_counter.most_common(AUDIT_TOP_WORDS):
        reasons = utils.teencode_reasons(token)
        if reasons:
            common_flagged.append([token, count, " + ".join(reasons)])

    files.append(utils.rel(utils.write_csv(
        common_flagged or [["-", 0, "không có từ phổ biến nào bị gắn cờ"]],
        ["từ phổ biến bị gắn cờ", "số lần xuất hiện", "lí do bị gắn cờ"],
        out_dir / "03_quality_teencode_common_flagged.csv",
    )))

# ---
    # 3. Emoji phổ biến nhất - quét cả 3 split
# ---
    emoji_top = emoji_counter.most_common(TOP_N)

    files.append(utils.rel(utils.write_csv(
        [[glyph, count] for glyph, count in emoji_counter.most_common()],
        ["emoji", "số lần xuất hiện"],
        out_dir / "03_quality_emoji.csv",
    )))

    emoji_chart = {
        "title": "Emoji phổ biến nhất (3 split)",
        "kind": "bar",
        "x": [glyph for glyph, _ in emoji_top],
        "y": [count for _, count in emoji_top],
        "x_label": "emoji",
        "y_label": "số lần xuất hiện",
        "orientation": "h",
    }

# ---
    # 4. Ví dụ minh hoạ từng nhóm nhiễu: lấy mẫu ngẫu nhiên, cả 3 split
# ---
    rng = random.Random(EXAMPLE_SEED)
    example_rows = []
    table_rows = []
    for label, predicate in EXAMPLE_GROUPS:
        group_csv = []
        group_table = []
        for name, df in splits.items():
            texts = df[config.TEXT_COLUMN].astype(str).tolist()
            samples = _sample_examples(texts, predicate, EXAMPLES_PER_SPLIT_CSV, rng)
            group_csv.extend(
                [label, name, index + 1, text[:120]] for index, text in samples
            )
            group_table.extend(
                [label, name, index + 1, text[:120]]
                for index, text in samples[:EXAMPLES_PER_SPLIT_TABLE]
            )
        if group_csv:
            example_rows.extend(group_csv)
            table_rows.extend(group_table)

    example_columns = ["nhóm nhiễu", "split", "dòng trong file", "ví dụ"]
    files.append(utils.rel(utils.write_csv(
        example_rows or [["-", "-", 0, "không có ví dụ"]],
        example_columns,
        out_dir / "03_quality_examples.csv",
    )))

    return {
        "id": "quality_noise",
        "title": "EDA 03 - Chất lượng dữ liệu và nhiễu",
        "cards": [
            {"label": "Số chỉ số chất lượng đang đo", "value": len(metric_labels)},
            {"label": "Emoji khác nhau (3 split)", "value": len(emoji_counter)},
            {"label": "Từ bị gắn cờ xuất hiện từ {} lần (3 split)".format(
                MIN_CANDIDATE_COUNT),
             "value": flagged_distinct},
        ],
        "charts": [emoji_chart],
        "tables": [
            metric_table,
            candidate_table,
            reason_table,
            {
                "title": "Ví dụ minh hoạ theo nhóm nhiễu (mỗi split 1 ví dụ, lấy ngẫu nhiên)",
                "columns": example_columns,
                "rows": table_rows,
                "num_columns": [2],
                "narrow_columns": [2],
                # Cột "ví dụ" là đoạn đầu của review thật: giữ nguyên xuống dòng
                # để copy đi tìm trong CSV là thấy.
                "pre_wrap_columns": [3],
            },
        ],
        "files": files,
    }
