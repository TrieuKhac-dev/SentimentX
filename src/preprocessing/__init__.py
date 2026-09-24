# -*- coding: utf-8 -*-
"""TIỀN XỬ LÝ CHO MODEL - Model preprocessing.

Chuẩn bị input RIÊNG cho từng model, KHÔNG nhét vào Data Pipeline chung.

Lý do tách riêng: mỗi model cần một dạng input khác nhau (tách từ, tokenizer,
prompt, chat template...). Nếu đưa các bước này vào pipeline, pipeline sẽ bị
phụ thuộc vào một model cụ thể và không dùng lại được cho model khác.

Ví dụ rõ nhất: **tách từ tiếng Việt là bước riêng của PhoBERT**, không phải một
bước cleaning chung.

Các file:
    phobert.py    -> tách từ + tokenizer của PhoBERT
    visobert.py   -> tokenizer của ViSoBERT (KHÔNG tách từ)
    qwen.py       -> prompt chỉ dẫn + chat template + tokenizer
    vitasa.py     -> định dạng theo repo ViTASA (đang gác, xem docs .../04_backlog.md)
    token_stats.py -> ĐO độ dài input thật (p95, % bị cắt, % <unk>) - chạy run_token_stats.py
    loader.py     -> ĐỌC dữ liệu đã xử lý (mọi model dùng chung)

Nội dung thay đổi được KHÔNG nằm trong Python:
    configs/prompts/<tên>.txt   nội dung prompt  (nạp/kiểm tra: src/prompts.py)
    configs/models/<model_id>.yaml  ngưỡng cắt input, cách nạp model (đọc: src/model_config.py)

Bộ tách từ (word segmentation) nằm ở một gói riêng, THAY ĐƯỢC:
    segmenters/   các bộ tách từ có thể chọn (chính chủ: VnCoreNLP/RDRSegmenter)
                  Dùng: python run_token_stats.py --segmenter <tên>
                  Xem: python run_token_stats.py --list-segmenters
Tách từ KHÁC tokenizer: đổi bộ tách từ KHÔNG làm đổi tokenizer, nên câu hỏi "tách từ có
giúp không" trả lời được bằng số đo. Hợp đồng của một bộ tách từ ở segmenters/base.py.

token_stats.py là phép đo đầu tiên của tiền xử lý cho model và chỉ cần `transformers`, nên chạy
được trước khi huấn luyện. EDA cố ý KHÔNG đo phần này vì EDA không được phụ thuộc
vào tokenizer của một model cụ thể.

Đây là TIỀN XỬ LÝ CHO MODEL: chỉ bắt đầu sau khi EDA và Data Pipeline đã hoàn tất.
"""
