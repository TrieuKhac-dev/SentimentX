# -*- coding: utf-8 -*-
"""Model preprocessing cho ViTASA (https://github.com/kh4nh12/ViTASA).

TRẠNG THÁI: **GÁC LẠI** - chưa dùng trong thực nghiệm (ghi ở
docs/04_experiments/04_backlog.md mục 1).

Vì sao: repo `kh4nh12/ViTASA` hiện chỉ có LICENSE, README.md và 3 file .jsonl - không
có mã model, không có checkpoint, không có script huấn luyện; Hugging Face Hub cũng
không có dataset/model nào tên "vitasa". Viết chi tiết hơn ở đây chỉ là suy đoán chứ
không phải tái lập, nên module này giữ ở mức KHUNG: nó chuyển dữ liệu đã xử lý sang
dạng bộ ba (câu, khía cạnh, cảm xúc) - dạng dữ liệu mà hầu hết hệ thống ABSA/TASA dùng
- rồi khi có checkpoint thì chỉnh lại cho khớp đúng yêu cầu của repo.

VIỆC CẦN LÀM khi triển khai thật:
    1. Đọc phần "Data format" trong README của repo ViTASA.
    2. So sánh với `to_absa_tuples()` bên dưới.
    3. Nếu khác, chỉnh lại phần này - KHÔNG sửa Data Pipeline.
    4. Thêm một dict vào `MODELS` trong src/preprocessing/token_stats.py (MODEL_NAME,
       MAX_LENGTH, tokenizer, encode, words, info) để đo được input như 3 model kia.

Ghi chú: khác với PhoBERT/ViSoBERT (bộ mã hoá câu), ViTASA thường cần biết khía cạnh cụ
thể đang được xét, nên input của nó là (câu, khía cạnh) chứ không chỉ là câu.
"""

from src.preprocessing import loader


def to_absa_tuples(records):
    """Chuyển mẫu ABSA thành danh sách bộ ba (câu, khía cạnh, cảm xúc).

    Đầu vào: danh sách mẫu dạng
        {"split": ..., "text": ..., "labels": {"colour": "positive", ...}}

    Đầu ra: danh sách
        [(câu, khía cạnh, cảm xúc), ...]

    Một review nhắc 3 khía cạnh sẽ tạo ra 3 dòng, mỗi dòng ứng với một khía cạnh.
    """
    tuples = []
    for record in records:
        text = record.get("text", "")
        labels = record.get("labels", {})
        for aspect, sentiment in labels.items():
            tuples.append((text, aspect, sentiment))
    return tuples


def to_label_ids(tuples, label_map):
    """Đổi nhãn chữ thành mã số để model dùng.

    `label_map` là dict đọc từ data/processed/label_map.json.
    """
    label_to_id = label_map["label_to_id"]
    return [
        (text, aspect, label_to_id.get(sentiment, 0))
        for text, aspect, sentiment in tuples
    ]


def describe_format(aspects=None):
    """In ra mô tả định dạng đang dùng, để đối chiếu với repo ViTASA."""
    return {
        "model": "ViTASA",
        "source": "https://github.com/kh4nh12/ViTASA",
        "aspects": aspects or loader.known_aspects(),
        "expected_unit": "(câu, khía cạnh, cảm xúc)",
        "note": "Hãy kiểm tra lại với README của repo và chỉnh module này nếu cần.",
    }
