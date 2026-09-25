# -*- coding: utf-8 -*-
"""Đăng ký các module EDA và các bước của Data Pipeline.

CÁCH MỞ RỘNG
---
1) Thêm một bước EDA mới:
   - Tạo file mới trong `src/eda/`, ví dụ `my_step.py`.
   - Trong file đó viết hàm `run(context) -> dict` trả về một section báo cáo
     (xem cấu trúc ở `src/reporting/result.py`).
   - Import module đó ở đây và thêm vào danh sách `EDA_MODULES`.

2) Thêm một bước Data Pipeline mới:
   - Tạo file mới trong `src/pipeline/`, ví dụ `my_step.py`.
   - Viết hàm `run(context) -> dict` trả về báo cáo của bước đó.
   - Thêm vào danh sách `PIPELINE_STEPS` theo ĐÚNG THỨ TỰ muốn chạy.

3) Thêm một dataset mới:
   - Đặt dữ liệu gốc vào `data/raw/<tên>/`.
   - Tạo file `configs/datasets/<tên>.yaml` (copy từ dataset có sẵn).
   - Nếu dataset dùng định dạng file mới (ví dụ .xlsx): thêm một loader
     trong `src/loaders/`.
   Không cần sửa EDA, pipeline hay báo cáo.

4) Thêm một loại biểu đồ mới:
   - Viết hàm dựng hình trong `src/reporting/charts.py` rồi đăng ký vào `_BUILDERS`.
   - Module EDA/pipeline chỉ cần khai báo `{"kind": "<tên mới>", ...}`.

5) Thêm một MODEL mới cho tiền xử lý cho model:
   - Viết file trong `src/preprocessing/`, ví dụ `my_model.py`, cung cấp:
         MODEL_NAME    tên trên Hugging Face
         CONFIG_NAME   tên file cấu hình trong configs/models/; `limit()` đọc
                       `preprocess.max_length` từ file đó (xem src/model_config.py)
         tokenizer()   nạp tokenizer một lần
         encode()      -> list[list[int]] CHƯA pad, CHƯA cắt
         info()        -> dict ghi lại tokenizer / từ vựng / ngưỡng cắt / bộ tách từ
         words()       chỉ khi model có bước riêng trước tokenizer (xem phobert.py)
     `encode()` KHÔNG được pad/cắt: token_stats đo độ dài thật dựa vào đó, và có kiểm
     tra để phát hiện việc pad/cắt lẫn vào.
   - Thêm một dict vào `MODELS` trong `src/preprocessing/token_stats.py`.
   - Thêm `configs/models/<model_id>.yaml` với `model_id` trùng tên file.
   - Prompt KHÔNG khai ở đây: prompt thuộc config của thí nghiệm, vì cùng một model có thể
     chạy nhiều prompt khác nhau.
   - Nếu model cần một BỘ TÁCH TỪ mới: xem hợp đồng ở
     `src/preprocessing/segmenters/base.py` (thêm file rồi đăng ký trong `SEGMENTERS`).
     Tuyệt đối KHÔNG nhét bước tách từ vào pipeline chung.

6) Thêm một CÁCH CHẤM ĐIỂM mới (chỉ số mới, hoặc chỉ số theo công bố khác):
   - Viết file trong `src/evaluation/scorers/`, ví dụ `per_review.py`, theo hợp đồng ở
     `src/evaluation/scorers/base.py` (`NAME`, `DESCRIPTION`, `run(samples)`).
   - Thêm một dòng vào `SCORERS` trong `src/evaluation/scorers/__init__.py`.
   - Thêm tên vào `scores` trong `configs/experiments/evaluation.yaml`, nếu muốn nó chạy.
     Mọi phép đếm lấy từ `samples` (lớp `Samples`), KHÔNG tự đếm lại: hai chỗ đếm là hai con
     số có thể lệch nhau cho cùng một đại lượng.

7) Thêm một KHÔNG GIAN NHÃN mới (cách nhìn bài toán: chỉ hai nhãn, hay giữ đủ bốn trạng thái):
   - Viết file trong `src/labels/`, ví dụ `three_way.py`, theo hợp đồng ở `src/labels/base.py`
     (`NAME`, `DESCRIPTION`, `CODES`, `SEPARATE_NOT_MENTIONED`, `check()`, `project()`).
   - Thêm một dòng vào `LABEL_SPACES` trong `src/labels/__init__.py`.
   - Không sửa metric: metric đọc nhãn ĐÃ CHIẾU và `dropped_neutral` từ kết quả chiếu.

8) Thêm một TRÌNH GHI NHẬN mới (ví dụ ghi lên một máy chủ khác, hoặc ghi vào Google Sheet):
   - Viết file trong `src/tracking/`, ví dụ `sheet.py`, theo hợp đồng ở `src/tracking/base.py`
     (`NAME`, `DESCRIPTION`, `begin(config, dagshub, out_dir, info, log) -> Session`).
   - Thêm một dòng vào `TRACKERS` trong `src/tracking/__init__.py`.
   - Ghi nhận KHÔNG BAO GIỜ được ném ra ngoài: máy chủ hỏng thì thành dòng `[WARN]`, còn file kết
     quả vẫn phải nguyên. Xem quy tắc ở đầu `src/tracking/base.py`.

9) Thêm một CÁCH HUẤN LUYỆN mới (ví dụ full fine-tune, hoặc QLoRA cho LLM):
   - Viết file trong `src/training/`, ví dụ `qlora.py`, theo hợp đồng ở `src/training/__init__.py`
     (`NAME`, `DESCRIPTION`, `check()`, `fit()`, `predict()`).
   - Thêm một dòng vào `TRAINERS`. Thí nghiệm chọn bằng `training.trainer` trong config.
   - `fit()` phải ghi `model/last` (đủ để chạy tiếp) và `model/best` (chỉ adapter) theo
     `configs/experiments/training.yaml`; tên thư mục lấy từ `configs/paths.yaml`.

10) Thêm một MODEL ENCODER mới cho huấn luyện:
   - Viết module trong `src/preprocessing/` theo hợp đồng ở điểm 5 (thêm `build_inputs()`).
   - Thêm một dòng vào `ENCODERS` trong `src/training/encoders.py`, và một file
     `configs/models/<model_id>.yaml` có `approach: encoder`.

Định dạng file kết quả do run_eda.py / run_pipeline.py ghi ra được mô tả ở
`src/reporting/result.py`. build_report.py đọc lại file đó để vẽ báo cáo.
"""

from src.eda import (
    label_aspect,
    overview,
    quality_noise,
    split_leakage,
    text_analysis,
)

# ---
# Thứ tự chạy EDA = thứ tự xuất hiện trong báo cáo
# ---
EDA_MODULES = [
    overview,        # 01 - tổng quan
    label_aspect,    # 02 - nhãn & aspect
    quality_noise,   # 03 - chất lượng & nhiễu
    text_analysis,   # 04 - đặc điểm văn bản
    split_leakage,   # 05 - quan hệ split & rò rỉ
]


# ---
# Thứ tự chạy Data Pipeline
#
# Dùng import muộn để khi chỉ chạy EDA thì không cần nạp các module pipeline.
# ---


def pipeline_steps():
    """Trả về danh sách các bước pipeline theo ĐÚNG THỨ TỰ thực thi."""
    from src.pipeline import (
        clean,
        export,
        final_validate,
        load,
        normalize,
        transform,
        validate,
    )

    return [
        load,             # 1. đọc dữ liệu gốc
        validate,         # 2. kiểm tra schema + nội dung
        clean,            # 3. xử lý bản ghi lỗi, trùng lặp, xung đột
        normalize,        # 4. chuẩn hoá văn bản (có bật/tắt)
        transform,        # 5. chuyển sang dạng ABSA
        final_validate,   # 6. cổng chất lượng cuối
        export,           # 7. ghi ra đĩa + log truy vết
    ]
