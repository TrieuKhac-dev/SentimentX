# -*- coding: utf-8 -*-
"""Các hàm dùng chung cho EDA và Data Pipeline.

Nhóm chức năng:
1. Đọc / ghi file (CSV, JSON, JSONL).
2. Chuẩn hoá văn bản (unicode, khoảng trắng, bỏ dấu).
3. Phát hiện đặc điểm văn bản (emoji, ký tự lặp, teencode, gibberish, quảng cáo).
4. Thống kê mô tả (phân vị p50 / p95 / p99).
"""

import json
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from src import config

# ---
# 1. ĐỌC / GHI FILE
# ---


def read_csv(path):
    """Đọc CSV luôn ở dạng chuỗi (string).

    Dùng encoding 'utf-8-sig' để xử lý được CẢ HAI trường hợp:
    - file có BOM (data_train.csv, data_val.csv, data_test.csv)
    - file không có BOM (full_data.csv)

    keep_default_na=False: ô trống giữ nguyên là chuỗi rỗng "", không bị
    đổi thành NaN. Nhờ vậy việc kiểm tra "ô trống" rõ ràng và nhất quán.
    """
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")


def write_csv(rows, columns, path):
    """Ghi danh sách các dòng (list of list) ra CSV."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows, columns=columns)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def rel(path):
    """Đổi đường dẫn thành dạng tương đối so với gốc dự án, cho dễ đọc."""
    try:
        return Path(path).relative_to(config.ROOT_DIR).as_posix()
    except ValueError:
        return str(path)


def write_json(data, path):
    """Ghi dữ liệu ra JSON (dễ đọc, giữ tiếng Việt nguyên vẹn)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def write_jsonl(records, path):
    """Ghi danh sách dict ra JSONL (mỗi dòng 1 JSON object)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return path


# ---
# 2. CHUẨN HOÁ VĂN BẢN
# ---

# Bảng nguyên âm tiếng Việt (đã bao gồm cả dạng có dấu) - dùng cho việc đoán từ
VI_VOWELS = set(
    "aeiouy"
    "àáảãạăằắẳẵặâầấẩẫậ"
    "èéẻẽẹêềếểễệ"
    "ìíỉĩị"
    "òóỏõọôồốổỗộơờớởỡợ"
    "ùúủũụưừứửữự"
    "ỳýỷỹỵ"
)


def normalize_unicode(text):
    """Đưa về dạng Unicode dựng sẵn (NFC).

    Tiếng Việt có 2 cách mã hoá cho cùng một chữ (tổ hợp dấu vs dựng sẵn).
    Bình thường hoá giúp hai chuỗi "nhìn giống nhau" được coi là giống nhau.
    """
    return unicodedata.normalize("NFC", text)


def normalize_whitespace(text):
    """Chuẩn hoá xuống dòng và khoảng trắng thừa."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)      # nhiều space/tab -> 1 space
    text = re.sub(r" *\n *", "\n", text)     # bỏ space quanh xuống dòng
    text = re.sub(r"\n{2,}", "\n", text)     # nhiều dòng trống -> 1
    return text.strip()


def remove_diacritics(text):
    """Bỏ dấu tiếng Việt: 'đẹp' -> 'dep'. Dùng cho việc tạo khoá so trùng."""
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text.replace("đ", "d").replace("Đ", "D")


def dedup_key(text, ignore_diacritics=False):
    """Tạo KHOÁ so trùng cho một review.

    QUAN TRỌNG: khoá này CHỈ dùng để phát hiện trùng lặp.
    Nó KHÔNG BAO GIỜ thay thế văn bản gốc của review - đây KHÔNG phải bước
    Normalize. Bước Normalize chỉ sửa Unicode / khoảng trắng / ký tự lặp
    (xem src/pipeline/normalize.py) và KHÔNG bỏ dấu tiếng Việt.

    Các bước tạo khoá:
        1. NFC  - gộp hai cách mã hoá dấu tiếng Việt về một dạng;
        2. lower
        3. gộp khoảng trắng / xuống dòng
        4. (tuỳ chọn) bỏ dấu tiếng Việt: "đẹp" -> "dep"
        5. thay mọi ký tự không phải chữ/số (dấu câu, emoji) bằng khoảng trắng
        6. gộp khoảng trắng lần nữa

    Vì sao bước 5 cần: nếu giữ dấu câu thì "Son đẹp!!!" và "Son đẹp" ra hai khoá
    khác nhau và không bị coi là trùng; thay dấu câu bằng khoảng trắng giúp hai
    câu đó có cùng một khoá.

    `ignore_diacritics=False` (mặc định) giữ dấu tiếng Việt trong khoá, nên
    "son dep" và "son đẹp" là HAI khoá khác nhau - dự án không bỏ dấu tiếng Việt
    ở bất kỳ chỗ nào, kể cả trong khoá so trùng. Muốn thí nghiệm thì bật bằng
    `clean.deduplicate.ignore_diacritics: true` trong configs/pipeline.yaml.
    """
    key = normalize_unicode(text).lower()
    key = normalize_whitespace(key)
    if ignore_diacritics:
        key = remove_diacritics(key)
    key = re.sub(r"[^\w\s]", " ", key)   # bỏ dấu câu, emoji
    key = re.sub(r"\s+", " ", key).strip()
    return key


def collapse_repeated_chars(text, max_repeat=2):
    """Rút gọn ký tự lặp liên tiếp: 'đẹppppp' -> 'đẹpp' (khi max_repeat=2)."""
    pattern = re.compile(r"(.)\1{%d,}" % max_repeat, re.UNICODE)
    return pattern.sub(lambda m: m.group(1) * max_repeat, text)


def diff_window(before, after, radius=30):
    """Cắt hai đoạn văn bản QUANH VỊ TRÍ KHÁC NHAU ĐẦU TIÊN.

    Vì sao cần: nếu chỉ cắt N ký tự đầu của review để làm ví dụ "trước / sau",
    phần bị chuẩn hoá có thể nằm ngoài đoạn cắt (ví dụ khoảng trắng ở cuối), nên
    hai ô trông giống hệt nhau và ví dụ trở nên vô nghĩa.

    Xuống dòng được hiện thành '⏎' để nhìn thấy được. Khi hai đoạn chỉ khác nhau
    ở khoảng trắng, khoảng trắng được hiện thành '␣' - nếu để nguyên, trình duyệt
    sẽ gộp chúng lại và ví dụ trông như không có gì thay đổi.

    Trả về (đoạn trước, đoạn sau), đã thêm '...' nếu bị cắt.
    """
    limit = min(len(before), len(after))
    position = next((i for i in range(limit) if before[i] != after[i]), limit)
    start = max(0, position - radius)

    def _cut(text):
        stop = min(len(text), position + radius)
        snippet = text[start:stop]
        # Hiện rõ ký tự điều khiển: '\r' (kiểu xuống dòng Windows, CRLF) in thành
        # "\r" còn xuống dòng in thành '⏎'. Nếu chỉ in '⏎' cho cả hai thì phép
        # chuẩn hoá "\r\n -> \n" - phép phổ biến nhất - sẽ trông như không đổi gì.
        snippet = snippet.replace("\r", "\\r").replace("\n", "⏎")
        if start > 0:
            snippet = "..." + snippet
        if stop < len(text):
            snippet = snippet + "..."
        return snippet

    before_snippet, after_snippet = _cut(before), _cut(after)
    if before_snippet.replace(" ", "") == after_snippet.replace(" ", ""):
        before_snippet = before_snippet.replace(" ", "␣")
        after_snippet = after_snippet.replace(" ", "␣")
    return before_snippet, after_snippet


# ---
# 3. PHÁT HIỆN ĐẶC ĐIỂM VĂN BẢN
# ---

# ---
# EMOJI - bắt TRỌN CHUỖI emoji, không đếm từng điểm mã rời rạc
# ---
# Một emoji có thể gồm nhiều điểm mã: ký tự gốc + dấu biến thể (U+FE0F)
# + tông màu da (U+1F3FB..U+1F3FF) + nối bằng ZWJ (U+200D).
# Nếu đếm từng điểm mã rời thì "❤️" bị tính thành 2 emoji và "🏻" (tông màu
# da) bị tính như một emoji riêng - sai hẳn. Danh sách điểm mã dưới đây là
# TOÀN BỘ dải emoji của Unicode, không phải danh sách chọn tay vài emoji.
_EMOJI_BASES = (
    "\U0001F000-\U0001FAFF"   # mặt cười, đồ vật, trái tim...
    "\U00002600-\U000027BF"   # ký hiệu, mũi tên, bàn tay, dấu kiểm...
    "\U00002B00-\U00002BFF"   # ký hiệu bổ sung (⭐ ⬛ ...)
    "\U00002190-\U000021FF"   # mũi tên
    "\U00002300-\U000023FF"   # ký hiệu kỹ thuật (⌚ ⏰ ...)
)
_EMOJI_SKIN = "\U0001F3FB-\U0001F3FF"    # tông màu da
_EMOJI_VARIATION = "\uFE0F"              # dấu biến thể emoji

EMOJI_PATTERN = re.compile(
    "(?:[\U0001F1E6-\U0001F1FF][\U0001F1E6-\U0001F1FF])"       # cờ quốc gia
    "|(?:[0-9#*]" + _EMOJI_VARIATION + "?\u20E3)"              # phím số 1️⃣
    "|(?:[" + _EMOJI_BASES + "]" + _EMOJI_VARIATION + "?"
    "[" + _EMOJI_SKIN + "]?"
    "(?:\u200D[" + _EMOJI_BASES + "]" + _EMOJI_VARIATION + "?"
    "[" + _EMOJI_SKIN + "]?)*)"                                # cả chuỗi ZWJ
)


def emoji_key(sequence):
    """Khoá gộp emoji giống nhau khi đếm.

    Bỏ dấu biến thể U+FE0F (chỉ ảnh hưởng cách hiển thị), nên "❤️" và "❤"
    được tính chung một dòng - đúng với cảm nhận của người đọc báo cáo.
    """
    return sequence.replace(_EMOJI_VARIATION, "")


def has_emoji(text):
    """Review có chứa emoji hay không."""
    return bool(EMOJI_PATTERN.search(text))


def count_emoji(text):
    """Đếm số lượng emoji trong review (mỗi chuỗi emoji tính là 1)."""
    return len(EMOJI_PATTERN.findall(text))


def has_repeated_chars(text, min_repeat=config.REPEATED_CHAR_MIN):
    """Review có ký tự lặp liên tiếp từ min_repeat lần trở lên hay không."""
    pattern = re.compile(r"(.)\1{%d,}" % (min_repeat - 1), re.UNICODE)
    return bool(pattern.search(text))


def is_only_emoji_and_punct(text):
    """Review chỉ gồm emoji / dấu câu / khoảng trắng (không có chữ hay số)."""
    stripped = EMOJI_PATTERN.sub("", text)
    stripped = re.sub(r"[\W_]+", "", stripped, flags=re.UNICODE)
    return len(stripped) == 0


def _looks_like_word(token):
    """Đoán một token có "giống một từ" hay không.

    Một token bị coi là bất thường nếu:
    - không chứa nguyên âm nào, hoặc
    - dài từ 15 ký tự trở lên (gần như không phải từ tiếng Việt).
    Đây chỉ là HÌNH THỨC ĐOÁN, không phải kết luận tuyệt đối.
    """
    if len(token) <= 2:
        return True
    if not any(c in VI_VOWELS for c in token.lower()):
        return False
    if len(token) >= 15:
        return False
    return True


def gibberish_ratio(text):
    """Tỉ lệ token "bất thường" trong review (0.0 -> 1.0)."""
    tokens = re.findall(r"\w+", text, flags=re.UNICODE)
    if not tokens:
        return 1.0
    bad = sum(1 for t in tokens if not _looks_like_word(t))
    return bad / len(tokens)


def is_gibberish(text, threshold=config.GIBBERISH_RATIO_THRESHOLD):
    """Review có phải là chuỗi ký tự vô nghĩa hay không.

    Lưu ý quan trọng: review CHỈ có emoji (ví dụ "😍😍😍") KHÔNG bị coi là
    gibberish, vì emoji mang tín hiệu cảm xúc rõ ràng. Nếu xoá nhóm này,
    ta sẽ mất dữ liệu sentiment hợp lệ.
    """
    if has_emoji(text) and is_only_emoji_and_punct(text):
        return False
    return gibberish_ratio(text) >= threshold


def find_matches(text, patterns):
    """Trả về danh sách các mẫu (pattern) khớp trong text."""
    low = text.lower()
    return [p for p in patterns if re.search(p, low)]


def is_advertisement(text):
    """Review có mang dấu hiệu quảng cáo / tin nhắn nhà mạng hay không."""
    return len(find_matches(text, config.AD_PATTERNS)) > 0


def is_code_like(text, patterns=None):
    """Review có dấu hiệu CODE / HTML / SQL hay không.

    Dùng cho việc ĐO (EDA 03) và một công tắc riêng ở bước Clean
    (`clean.remove_code`, config đang BẬT vì nhóm này rất nhỏ: 1/16.227 dòng).
    Danh sách mẫu cố tình chặt, xem `config.CODE_PATTERNS`. Đo trên dataset
    cosmetics: 1/16.227 dòng (0,01%).
    """
    return len(find_matches(text, patterns or config.CODE_PATTERNS)) > 0


# ---
# TEENCODE / TỪ LẠ - TÌM TỪ DỮ LIỆU BẰNG QUY TẮC CẤU TRÚC
# ---
# Dùng cho ĐO LƯỜNG (EDA 03 liệt kê từ bị gắn cờ). Pipeline KHÔNG thay thế
# teencode: văn bản giữ nguyên như người viết.
#
# Các quy tắc dưới đây KHÔNG đoán ngữ âm tiếng Việt. Đoán kiểu đó (ví dụ "phải
# là âm tiết hợp lệ") gắn cờ oan các từ thật như "siêu", "tiền", "chuyển", nên
# không dùng. Hệ quả: teencode vẫn đúng cấu trúc âm tiết như "ko", "tui" không
# bị bắt bằng quy tắc.
#
# QUY ƯỚC CHỐNG DƯƠNG TÍNH GIẢ (rất quan trọng khi đọc bảng EDA 03):
# - Từ chứa chữ KHÔNG PHẢI chữ Latin (ký tự trang trí 𝐭, ᴗ, ω, chữ Hàn/Ả Rập...)
#   được xếp riêng một lí do và KHÔNG bị xét các quy tắc còn lại - chúng không
#   phải "teencode tiếng Việt" nên không thể bị dán nhãn sai.
# - "Một ký tự phụ âm" chỉ xét đúng các chữ cái Latin cơ bản (k, r, n, m, t...),
#   không xét ký tự trang trí / chữ nước ngoài.
# - Số thuần (2023) không bao giờ bị gắn cờ: quy tắc yêu cầu phải có chữ cái.
# - Mọi từ tiếng Việt đều có nguyên âm, nên quy tắc "không có nguyên âm" không
#   thể gắn cờ oan một từ tiếng Việt bình thường.
VI_LETTERS = set(
    "aàáảãạăằắẳẵặâầấẩẫậbcdđeèéẻẽẹêềếểễệghiìíỉĩịklmnoòóỏõọôồốổỗộơờớởỡợ"
    "pqrstuùúủũụưừứửữựvxyỳýỷỹỵ"
)

# Chữ cái Latin cơ bản (a-z) + "đ": dùng để nhận ra chữ của hệ chữ khác.
LATIN_BASIC = set("abcdefghijklmnopqrstuvwxyzđ")

# Chữ Latin KHÔNG có trong bảng chữ cái tiếng Việt - thường là tiếng Anh / tên
# thương hiệu (review, swatch, fenty...), không phải lỗi chính tả tiếng Việt.
LETTERS_OUTSIDE_VN = set("fjwz")

# Chữ cái được coi là "Latin" = chữ cái tiếng Việt (kể cả chữ có dấu) + f, j, w, z.
# CHÚ Ý: phải gộp VI_LETTERS vào đây, nếu không thì mọi chữ có dấu ("à", "ẹ",
# "ắ"...) sẽ bị xếp nhầm là "không phải chữ Latin" - đó là lỗi dương tính giả.
LATIN_LETTERS = VI_LETTERS | LETTERS_OUTSIDE_VN

# Phụ âm viết bằng chữ Latin cơ bản - dùng cho quy tắc "một ký tự phụ âm".
# Viết tắt 1 chữ cái trong tiếng Việt luôn nằm trong tập này (k = không, r = rồi,
# n, m, t, c, v, d, s, p, h...).
ASCII_CONSONANTS = set("bcdfghjklmnpqrstvwxz")

# Tên các lí do (dùng làm tiêu đề cột trong báo cáo EDA)
REASON_NOT_LATIN = "chữ không phải chữ Latin (ký tự trang trí / tiếng nước ngoài)"
REASON_OUTSIDE_ALPHABET = "chữ Latin ngoài bảng chữ cái tiếng Việt (f, j, w, z)"
REASON_LETTER_DIGIT = "trộn chữ và số"
REASON_SINGLE_CONSONANT = "một ký tự phụ âm"
REASON_NO_VOWEL = "không có nguyên âm"

REASON_ORDER = (
    REASON_NOT_LATIN,
    REASON_OUTSIDE_ALPHABET,
    REASON_LETTER_DIGIT,
    REASON_SINGLE_CONSONANT,
    REASON_NO_VOWEL,
)


def teencode_reasons(token):
    """Lí do một từ bị coi là ứng viên teencode / từ lạ (quy tắc cấu trúc).

    Trả về tuple rỗng nghĩa là từ KHÔNG bị gắn cờ. Xem quy ước chống dương tính
    giả ở đầu mục này.
    """
    if not any(char.isalpha() for char in token):
        return ()                    # số thuần (ví dụ "2023") không phải teencode

    # Chữ của hệ chữ khác / ký tự trang trí: xếp riêng, không xét tiếp, vì các
    # quy tắc "nguyên âm" chỉ có nghĩa với chữ Latin.
    if any(char.isalpha() and char.lower() not in LATIN_LETTERS for char in token):
        return (REASON_NOT_LATIN,)

    reasons = []
    if any(char.lower() in LETTERS_OUTSIDE_VN for char in token):
        reasons.append(REASON_OUTSIDE_ALPHABET)
    if any(char.isdigit() for char in token):
        reasons.append(REASON_LETTER_DIGIT)
    if len(token) == 1 and token.lower() in ASCII_CONSONANTS:
        reasons.append(REASON_SINGLE_CONSONANT)
    if not (set(token) & VI_VOWELS):
        reasons.append(REASON_NO_VOWEL)
    return tuple(reasons)


def tokenize(text):
    """Tách thành các token chữ/số (bỏ dấu câu và emoji).

    Đây là phép ĐẾM TỪ dùng cho thống kê mô tả (EDA), KHÔNG phải tokenizer của
    model: mỗi model có tokenizer riêng (xem src/preprocessing/) và chỉ dùng nó
    ở bước huấn luyện. Nhờ vậy EDA không phụ thuộc vào một model cụ thể.
    """
    return re.findall(r"\w+", text.lower(), flags=re.UNICODE)


# ---
# 4. THỐNG KÊ MÔ TẢ
# ---


def length_stats(values, name="độ dài"):
    """Tính thống kê mô tả cho một dãy số (thường là độ dài review).

    Giải thích các phân vị (percentile):
    - p50 (trung vị): một nửa số mẫu có giá trị nhỏ hơn hoặc bằng mức này.
    - p95: 95% số mẫu nhỏ hơn hoặc bằng mức này, chỉ 5% lớn hơn.
    - p99: 99% số mẫu nhỏ hơn hoặc bằng mức này, chỉ 1% lớn hơn
           -> dùng để phát hiện các mẫu cực dài bất thường.
    """
    arr = np.asarray(list(values), dtype=float)
    if arr.size == 0:
        return {
            "chỉ số": name, "số lượng": 0, "nhỏ nhất": 0, "lớn nhất": 0,
            "trung bình": 0, "p50": 0, "p95": 0, "p99": 0,
        }
    return {
        "chỉ số": name,
        "số lượng": int(arr.size),
        "nhỏ nhất": int(arr.min()),
        "lớn nhất": int(arr.max()),
        "trung bình": round(float(arr.mean()), 2),
        "p50": int(np.percentile(arr, 50)),
        "p95": int(np.percentile(arr, 95)),
        "p99": int(np.percentile(arr, 99)),
    }


# ---
# 5. CẤU HÌNH PIPELINE
# ---


def load_pipeline_config(path=None):
    """Đọc configs/pipeline.yaml.

    Trả về dict cấu hình. Nếu thiếu khoá nào, hàm sẽ bổ sung giá trị mặc định
    (an toàn nhất = tắt biến đổi) để pipeline không bị lỗi.
    """
    path = Path(path) if path else (config.CONFIG_DIR / "pipeline.yaml")
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    cfg.setdefault("version", "unknown")
    cfg.setdefault("validate", {})
    cfg["validate"].setdefault("check_schema", True)
    cfg["validate"].setdefault("check_content", True)

    cfg.setdefault("clean", {})
    cfg["clean"].setdefault("remove_empty", True)
    cfg["clean"].setdefault("remove_gibberish", False)
    cfg["clean"].setdefault("remove_ads", False)
    cfg["clean"].setdefault("remove_code", False)
    cfg["clean"].setdefault("deduplicate", {})
    cfg["clean"]["deduplicate"].setdefault("exact", True)
    cfg["clean"]["deduplicate"].setdefault("normalized", False)
    cfg["clean"]["deduplicate"].setdefault("ignore_diacritics", False)
    cfg["clean"]["deduplicate"].setdefault("scope", "within_split")
    cfg["clean"]["deduplicate"].setdefault("conflict_policy", "quarantine")
    cfg["clean"].setdefault("leakage", {})
    cfg["clean"]["leakage"].setdefault("remove_eval_overlap", False)

    cfg.setdefault("normalize", {})
    cfg["normalize"].setdefault("lowercase", False)
    cfg["normalize"].setdefault("unicode", True)
    cfg["normalize"].setdefault("whitespace", True)
    cfg["normalize"].setdefault("repeated_chars", False)
    cfg["normalize"].setdefault("repeated_chars_max", 2)

    cfg.setdefault("transform", {})
    cfg["transform"].setdefault("format", "multi_head")

    cfg["_path"] = path
    return cfg


def on_off(value):
    """Đổi true/false thành 'Bật'/'Tắt' cho dễ đọc trên báo cáo.

    Cấu hình dùng true/false (đúng chuẩn YAML), nhưng báo cáo là tài liệu tiếng
    Việt cho người đọc nên in thẳng 'Bật' / 'Tắt'; giá trị nguyên vẹn vẫn nằm
    trong processing_log.json.
    """
    if isinstance(value, bool):
        return "Bật" if value else "Tắt"
    return value


def config_to_rows(cfg):
    """Chuyển config thành danh sách dòng để đưa vào báo cáo (dễ đọc)."""
    rows = [["version", cfg.get("version", "unknown")]]

    def _walk(prefix, node):
        for key, value in node.items():
            if key.startswith("_"):
                continue
            name = "{}.{}".format(prefix, key) if prefix else key
            if isinstance(value, dict):
                _walk(name, value)
            else:
                rows.append([name, on_off(value)])

    for section in ("validate", "clean", "normalize", "transform"):
        _walk("", {section: cfg.get(section, {})})
    return rows
