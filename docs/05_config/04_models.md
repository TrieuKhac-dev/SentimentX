# 05.04. Cấu hình model

> Đọc file này khi: thêm model mới, hoặc đổi mặc định dùng chung cho một model.
> Liên quan: `docs/04_experiments/01_models.md`, `docs/05_config/05_experiments_shared.md`

File: `configs/models/<model_id>.yaml`.

File này chứa **mọi cấu hình dùng chung cho model đó**, tức mọi thứ không thuộc riêng một thí nghiệm.
Không chứa `prompt`, `examples`, `roles`, hay `dataset` - những thứ đó thuộc thí nghiệm.

## Ví dụ

```yaml
model_id: qwen3-4b-instruct-2507
checkpoint: Qwen/Qwen3-4B-Instruct-2507
config_version: 3
approach: prompt
preprocess:
  max_length: 2304
  add_generation_prompt: true
  segmenter: vncorenlp
inference:
  dtype: auto
  quantization: 4bit
  batch_size: 8
```

## Giải thích

| Nhóm       | Khoá                               | Ý nghĩa                                                                                   |
| ---------- | ---------------------------------- | ----------------------------------------------------------------------------------------- |
| định danh  | `model_id`                         | tên dùng cho mọi đường dẫn và nhãn MLflow; trùng tên file                                 |
| định danh  | `checkpoint`                       | tên model trên Hugging Face, để đối chiếu tránh nhầm model                                |
| định danh  | `config_version`                   | tăng mỗi khi sửa file này                                                                 |
| định danh  | `approach`                         | `prompt` (model sinh: gửi câu chỉ dẫn rồi đọc trả lời) hoặc `encoder` (model phân loại: HỌC từ dữ liệu rồi suy luận). Quyết định đường chạy, nên bắt buộc khai. Xem `docs/04_experiments/06_lora_encoder.md` |
| bài toán   | `task.*`                           | ràng buộc của model, **áp sau tất cả các lớp**: `configs/experiments/task.yaml` không ghi đè được, vì đó là giới hạn của chính model (ví dụ model chỉ làm 2 nhãn) |
| tiền xử lý | `preprocess.max_length`            | ngưỡng cắt input theo token                                                               |
| tiền xử lý | `preprocess.add_generation_prompt` | chèn lượt trợ lý rỗng cho model chỉ dẫn                                                   |
| tiền xử lý | `preprocess.segmenter`             | bộ tách từ, chỉ model cần tách từ mới khai (`vncorenlp` cho PhoBERT, `none` cho ViSoBERT)  |
| huấn luyện | `lora.target_modules`              | tên module được gắn adapter LoRA. **Tên khác nhau theo kiến trúc** (Qwen3: `q_proj`, `k_proj`; PhoBERT và ViSoBERT: `query`, `key`, `value`, `dense`), nên khoá này thuộc config của model chứ không nằm ở file huấn luyện dùng chung |
| suy luận   | `inference.dtype`                  | `auto` để mã chọn theo máy: bf16 khi GPU hỗ trợ, fp16 khi không (T4), fp32 trên CPU       |
| suy luận   | `inference.quantization`           | `4bit` thì phải có `bitsandbytes`; để trống là chạy không lượng hoá                       |
| suy luận   | `inference.batch_size`             | số review mỗi lượt sinh (đường prompt) hoặc mỗi lượt chấm (đường encoder)                  |

## Tên model đang dùng

| `model_id`               | Ghi chú                             |
| ------------------------ | ----------------------------------- |
| `qwen3-4b-instruct-2507` | chỉ dùng cho thí nghiệm prompt      |
| `qwen3-0.6b`             | bản nhỏ, chạy được cả CPU           |
| `phobert-base-v2`        | encoder, huấn luyện LoRA hoặc QLoRA |
| `visobert`               | encoder, huấn luyện LoRA hoặc QLoRA |

## Thêm model mới

1. Viết một module trong `src/preprocessing/` theo hợp đồng ở `src/preprocessing/__init__.py`.
2. Thêm file YAML trong `configs/models/` với `model_id` trùng tên file.
3. Đăng ký module vào registry `MODELS` và cập nhật `src/registry.py`.
