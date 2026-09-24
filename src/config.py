# -*- coding: utf-8 -*-
"""Cấu hình KỸ THUẬT dùng chung cho toàn bộ dự án.

File này CHỈ chứa những thứ không phụ thuộc vào dataset:
    - đường dẫn thư mục
    - quy ước nội bộ (tên cột văn bản, mã nhãn)
    - mẫu nhận diện nội dung không phải review (quảng cáo, tin nhắn nhà mạng)
    - các ngưỡng (threshold)

SCHEMA CỦA DỮ LIỆU (tên cột, danh sách aspect, nhãn hợp lệ, file nào ở đâu)
KHÔNG nằm ở đây mà nằm trong configs/datasets/<tên>.yaml.
Nhờ vậy thêm dataset mới không phải sửa file này.
"""

from src import paths

# ---
# 1. ĐƯỜNG DẪN
# ---
# Mọi đường dẫn lấy từ configs/paths.yaml qua src/paths.py, KHÔNG viết cứng ở đây.
# Đổi cây thư mục thì sửa configs/paths.yaml: docs/05_config/01_paths.md.
ROOT_DIR = paths.root()

DATA_DIR = paths.data_root()
RAW_ROOT = paths.data("raw")               # dữ liệu gốc, mỗi dataset một thư mục con
PROCESSED_DIR = paths.data("processed")    # dữ liệu đã qua pipeline
REPORT_DIR = paths.reports_dir()
MODEL_INPUT_REPORT_DIR = paths.report("model_input")  # phép đo input thật
ASSETS_DIR = paths.assets_dir()            # tài nguyên dùng chung (plotly.min.js)
MODEL_ASSETS_DIR = paths.data("models")    # tài nguyên của model (vd: model VnCoreNLP)

CONFIG_DIR = paths.configs_dir()
DATASET_CONFIG_DIR = paths.config_path("datasets")
PIPELINE_CONFIG_PATH = paths.config_path("pipeline.yaml")
MODEL_CONFIG_DIR = paths.config_path("models")   # "model đọc dữ liệu thế nào"
PROMPT_DIR = paths.config_path("prompts")        # nội dung prompt, mỗi prompt một file .txt

# CÒN LẠI TỪ CẤU TRÚC CŨ, sẽ bỏ khi chuyển xong:
#   EDA_REPORT_DIR, PIPELINE_REPORT_DIR  -> P2 (kết quả EDA và pipeline ghi cạnh dữ liệu của chúng)
#   MODEL_EVAL_REPORT_DIR                -> P4 (kết quả đánh giá ghi vào thư mục thí nghiệm)
EDA_REPORT_DIR = REPORT_DIR / "eda"
PIPELINE_REPORT_DIR = REPORT_DIR / "pipeline"
MODEL_EVAL_REPORT_DIR = REPORT_DIR / "model_eval"

# Tên file kết quả do run_eda.py / run_pipeline.py ghi ra
RESULT_FILE_SUFFIX = "_result.json"

# ---
# 2. QUY ƯỚC NỘI BỘ
# ---
# Sau khi loader nạp dữ liệu, cột văn bản LUÔN được đặt tên là "text",
# bất kể tên cột trong file gốc là gì (khai báo ở khoá `text_column`).
TEXT_COLUMN = "text"

# Ô trống ở cột aspect nghĩa là "aspect này KHÔNG được nhắc tới" (null).
# Đây là null, KHÔNG phải là neutral.
NULL_LABEL = ""

# Bảng mã nhãn chuẩn của dự án (dùng để chuyển nhãn chữ <-> mã số cho model).
# Dataset có nhãn mới sẽ được cấp mã tiếp theo, xem src/dataset.py.
LABEL_TO_ID = {
    NULL_LABEL: 0,   # không nhắc tới aspect
    "positive": 1,
    "negative": 2,
    "neutral": 3,
}
ID_TO_LABEL = {value: key for key, value in LABEL_TO_ID.items()}

# ---
# 3. DẤU HIỆU NỘI DUNG KHÔNG PHẢI REVIEW
# ---
# Quảng cáo, tin nhắn nhà mạng, nội dung rác
AD_PATTERNS = [
    r"\[qc\]",
    r"\[tb\]",
    r"\bviettel\b",
    r"\bmobifone\b",
    r"\bvinaphone\b",
    r"https?://",
    r"www\.",
    r"bit\.ly",
    r"lh\s*198",
    r"tổng đài",
    r"soạn\s+\S+\s+gửi",
]

# Dấu hiệu CODE / HTML / SQL - review bị dán từ nơi khác (trang web, câu lệnh).
#
# Cố tình CHẶT để ít dương tính giả: chỉ bắt cú pháp thật, không bắt ký hiệu
# thông thường. Ví dụ KHÔNG đưa vào: "=>" (người viết vẫn dùng làm mũi tên),
# "{...}" (kaomoji như "{•~• ^~^}"), "//" (dấu gạch chéo trong văn bản).
#
# Mức xuất hiện trong dataset cosmetics: chỉ 1/16.227 dòng khớp (0,01%, là một
# entity "&quot;"). Sáu review còn lại của nhóm "dán từ nơi khác" là URL có tham
# số - đã bị AD_PATTERNS bắt trước. Đo lại khi đổi dataset.
CODE_PATTERNS = [
    r"</?[a-z][a-z0-9]*(\s[^>]{0,40})?/?>",              # thẻ HTML: <p>, </div>, <br/>
    r"&(nbsp|amp|quot|lt|gt|#x?[0-9a-f]{2,6});",         # entity HTML: &nbsp; &quot;
    r"\b(select|insert\s+into|drop\s+table)\b[\s\S]{0,60}\b(from|into|table|where)\b",
    r"\b(function|console\.log|printf|public\s+static)\s*\(",
    r"\bdef\s+\w+\s*\(|\bclass\s+\w+\s*[:{]|\{\{|\}\}",
    r"#include\s*<|<\?php",
]

# ---
# 5. NGƯỠNG (THRESHOLD) DÙNG CHUNG
# ---
# Ngưỡng coi một review là "ứng viên gibberish" (chuỗi ký tự vô nghĩa)
GIBBERISH_RATIO_THRESHOLD = 0.5
# Số ký tự lặp liên tiếp bị coi là "repeated characters" (vd: đẹppppp)
REPEATED_CHAR_MIN = 3
