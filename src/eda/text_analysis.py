# -*- coding: utf-8 -*-
"""EDA 04 — Đặc điểm văn bản.

Đo lường: các từ hay gặp, cụm 2 từ (bigram) theo từng aspect, và tỉ lệ review
viết có dấu / không dấu. Kích thước từ vựng và dấu câu chỉ ghi ra CSV.

Đây là phân tích MÔ TẢ. Pipeline không dùng những phép đếm này để lọc dữ liệu.

Mọi thống kê đo trên CẢ 3 split. Riêng "từ hay gặp" và "bigram" quét toàn bộ
dữ liệu (3 split).
"""

import re
from collections import Counter

from src import config, utils

# Một số từ rất phổ biến nhưng ít mang thông tin, loại ra để bảng dễ đọc.
# Đây KHÔNG phải stopword dùng cho pipeline — pipeline không xoá stopword.
COMMON_WORDS = {
    "và", "là", "của", "có", "thì", "mà", "nên", "rất", "cũng", "được",
    "mình", "em", "nó", "này", "cho", "với", "nhưng", "không", "đã", "ở",
    "ra", "vào", "lên", "xuống", "một", "hai", "các", "những", "khi", "để",
}

# Số mục tối đa đưa vào bảng/biểu đồ
TOP_WORDS = 25
TOP_BIGRAMS = 5
PUNCTUATION = ["!", "?", ".", ",", "...", ":", ";", "-", "~", "@"]

# Nội dung review chia làm 3 nhóm khi đo "viết có dấu / không dấu".
# Nhãn đặt ngắn để không phải xoay nhãn trục (tên dài bị xoay trông rất khó đọc).
ACCENT_GROUPS = (
    "Có dấu tiếng Việt",
    "Viết không dấu",
    "Không có chữ cái (emoji / số / ký hiệu)",
)


def _bigrams(tokens):
    """Ghép các cặp 2 từ liền nhau."""
    return ["{} {}".format(tokens[i], tokens[i + 1]) for i in range(len(tokens) - 1)]


def _all_tokens(splits, name):
    """Danh sách token của một split, theo đúng thứ tự dòng trong file."""
    texts = splits[name][config.TEXT_COLUMN].astype(str)
    return [token for text in texts for token in utils.tokenize(text)]


def run(context):
    splits = context["splits"]
    out_dir = context["out_dir"]
    cfg = context["dataset"]
    aspects = cfg["aspects"]
    files = []

    # -----------------------------------------------------------------
    # 1. Kích thước từ vựng theo split — chỉ ghi ra CSV
    # -----------------------------------------------------------------
    tokens_by_split = {name: _all_tokens(splits, name) for name in splits}
    vocab_by_split = {name: set(tokens) for name, tokens in tokens_by_split.items()}

    vocab_rows = []
    for name, tokens in tokens_by_split.items():
        n_reviews = len(splits[name])
        others = set()
        for other_name, other_vocab in vocab_by_split.items():
            if other_name != name:
                others |= other_vocab
        own_only = len(vocab_by_split[name] - others)
        vocab_rows.append([
            name,
            (cfg.get("splits") or {}).get(name, "-"),
            n_reviews,
            len(tokens),
            round(len(tokens) / n_reviews, 2) if n_reviews else 0,
            len(vocab_by_split[name]),
            own_only,
        ])

    vocab_columns = ["split", "tệp gốc", "số review", "tổng số token",
                     "token trung bình / review", "số từ vựng (token duy nhất)",
                     "từ vựng riêng của split"]
    files.append(utils.rel(utils.write_csv(
        vocab_rows, vocab_columns, out_dir / "04_text_vocabulary.csv")))

    # Bảng từ vựng chi tiết nằm ở CSV. Trên báo cáo chỉ giữ hai con số đã có thẻ
    # (số từ vựng, token/review) nên không dựng thêm bảng cho cùng số liệu đó.

    # -----------------------------------------------------------------
    # 2. Từ xuất hiện nhiều nhất — quét toàn bộ dữ liệu (cả 3 split)
    # -----------------------------------------------------------------
    all_counter = Counter()
    for tokens in tokens_by_split.values():
        all_counter.update(tokens)

    top_words = [
        [word, count] for word, count in all_counter.most_common(400)
        if word not in COMMON_WORDS
    ][:TOP_WORDS]

    files.append(utils.rel(utils.write_csv(
        top_words,
        ["từ", "số lần xuất hiện"],
        out_dir / "04_text_top_words.csv",
    )))

    top_word_chart = {
        # Từ quá phổ biến (và, là, của...) đã bị loại khỏi danh sách để bảng đọc
        # được — nêu ngay trong tiêu đề để người đọc không thắc mắc vì sao thiếu.
        "title": ("{} từ xuất hiện nhiều nhất, không tính các từ phổ biến như "
                  "'và', 'là', 'của' (3 split)").format(TOP_WORDS),
        "kind": "bar",
        "x": [row[0] for row in top_words],
        "y": [row[1] for row in top_words],
        "x_label": "từ",
        "y_label": "số lần xuất hiện",
        "orientation": "h",
    }

    # -----------------------------------------------------------------
    # 3. Cụm 2 từ (bigram) đặc trưng cho từng aspect — toàn bộ dữ liệu
    # -----------------------------------------------------------------
    bigram_rows = []
    for aspect in aspects:
        counter = Counter()
        n_mentioned = 0
        for name, df in splits.items():
            texts = df[config.TEXT_COLUMN].astype(str).tolist()
            flags = (df[aspect].astype(str).str.strip() != "").tolist()
            for index, is_mentioned in enumerate(flags):
                if is_mentioned:
                    n_mentioned += 1
                    counter.update(_bigrams(utils.tokenize(texts[index])))
        top = counter.most_common(TOP_BIGRAMS)
        bigram_rows.append([
            aspect,
            n_mentioned,
            ", ".join("{} ({})".format(phrase, count) for phrase, count in top),
        ])

    bigram_columns = ["khía cạnh", "số review nhắc khía cạnh (3 split)",
                      "{} cụm 2 từ hay gặp nhất".format(TOP_BIGRAMS)]
    files.append(utils.rel(utils.write_csv(
        bigram_rows, bigram_columns,
        out_dir / "04_text_bigrams_by_aspect.csv")))

    bigram_table = {
        # Cụm 2 từ được đếm trên TOÀN BỘ review có nhắc khía cạnh đó, không chỉ
        # trong câu chứa khía cạnh: dữ liệu không có nhãn ở mức câu, nên không
        # thể tách ra câu nào nói về khía cạnh nào.
        "title": ("{} cụm 2 từ hay gặp nhất trong các review có nhắc từng khía cạnh "
                  "(3 split)").format(TOP_BIGRAMS),
        "columns": bigram_columns,
        "rows": bigram_rows,
        "num_columns": [1],
        "narrow_columns": [1],
    }

    # -----------------------------------------------------------------
    # 4. Dấu câu — cả 3 split
    # -----------------------------------------------------------------
    patterns = [(label, re.compile(re.escape(label))) for label in PUNCTUATION]
    punct_rows = []
    for name, df in splits.items():
        texts = df[config.TEXT_COLUMN].astype(str).tolist()
        total = len(texts) or 1
        for label, pattern in patterns:
            n_reviews = sum(1 for text in texts if pattern.search(text))
            n_hits = sum(len(pattern.findall(text)) for text in texts)
            rate = round(100 * n_reviews / total, 2)
            punct_rows.append([name, label, n_reviews, n_hits, rate])

    # Dấu câu chỉ ghi ra CSV: Normalize không sửa dấu câu, nên bảng/biểu đồ dấu
    # câu không dẫn tới quyết định nào.
    files.append(utils.rel(utils.write_csv(
        punct_rows,
        ["split", "dấu câu", "số review có chứa", "tổng số lần xuất hiện", "tỉ lệ %"],
        out_dir / "04_text_punctuation.csv",
    )))

    # -----------------------------------------------------------------
    # 5. Review có dấu / không dấu — cả 3 split
    # -----------------------------------------------------------------
    accent_rows = []
    accent_counts = {name: {} for name in splits}
    for name, df in splits.items():
        texts = df[config.TEXT_COLUMN].astype(str).tolist()
        total = len(texts) or 1
        n_no_letters = sum(1 for text in texts
                           if not any(ch.isalpha() for ch in text))
        n_plain = sum(1 for text in texts
                      if any(ch.isalpha() for ch in text)
                      and utils.remove_diacritics(text) == text)
        values = [len(texts) - n_no_letters - n_plain, n_plain, n_no_letters]
        for label, value in zip(ACCENT_GROUPS, values):
            rate = round(100 * value / total, 2)
            accent_rows.append([name, label, value, rate])
            accent_counts[name][label] = value

    files.append(utils.rel(utils.write_csv(
        accent_rows,
        ["split", "nhóm", "số review", "tỉ lệ %"],
        out_dir / "04_text_accent.csv",
    )))

    # Mỗi cột là MỘT split, ba phần cộng lại đúng 100% số review của split đó.
    # Trên mỗi phần hiện cả số review và tỉ lệ: tỉ lệ để so train (12981 dòng)
    # với val/test (1623 dòng), số lượng để biết con số thật là bao nhiêu.
    accent_chart = {
        "title": "Review viết có dấu / không dấu, theo split (số review và tỉ lệ %)",
        "kind": "stacked_bar",
        "barnorm": "percent",
        "label_mode": "count_and_percent",
        "x": list(splits),
        "series": {
            label: [accent_counts[name][label] for name in splits]
            for label in ACCENT_GROUPS
        },
        "y_label": "tỉ lệ % số review",
        "height": 430,
    }

    no_letter_total = sum(row[2] for row in accent_rows
                          if row[1] == ACCENT_GROUPS[2])

    return {
        "id": "text_analysis",
        "title": "EDA 04 — Đặc điểm văn bản",
        "cards": [
            {"label": "Số từ vựng (số từ khác nhau) — train / val / test",
             "value": " / ".join("{}".format(row[5]) for row in vocab_rows)},
            {"label": "Số từ / review (đếm từ, không phải subword) — train / val / test",
             "value": " / ".join("{}".format(row[4]) for row in vocab_rows)},
            {"label": "Số dòng không có chữ cái (3 split)",
             "value": "{}".format(no_letter_total)},
        ],
        "charts": [top_word_chart, accent_chart],
        "tables": [bigram_table],
        "files": files,
    }
