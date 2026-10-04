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
| định danh  | `approach`                         | `prompt` (model sinh: gửi prompt rồi đọc trả lời) hoặc `encoder` (model phân loại: HỌC từ dữ liệu rồi suy luận). Quyết định đường chạy, nên bắt buộc khai. Xem `docs/04_experiments/06_lora_encoder.md` |
| bài toán   | `task.*`                           | ràng buộc của model, **áp sau tất cả các lớp**: `configs/experiments/task.yaml` không ghi đè được, vì đó là giới hạn của chính model (ví dụ model chỉ làm 2 nhãn) |
| tiền xử lý | `preprocess.max_length`            | ngưỡng cắt input theo token                                                               |
| tiền xử lý | `preprocess.add_generation_prompt` | chèn lượt trợ lý rỗng cho model dùng prompt                                                   |
| tiền xử lý | `preprocess.segmenter`             | bộ tách từ, chỉ model cần tách từ mới khai (`vncorenlp` cho PhoBERT, `none` cho ViSoBERT)  |
| tiền xử lý | `preprocess.enable_thinking`       | tắt/bật **suy nghĩ** của model sinh (Qwen3). Chỉ khai khi model có biến này trong chat template; **để trống KHÁC `false`**: trống = không truyền gì (giữ mặc định của model), `false` = chỉ định tắt. `qwen3-0.6b` khai `false` vì bản 0.6B mặc định bật suy nghĩ, ăn hết trần token rồi không in ra JSON |
| huấn luyện | `lora.target_modules`              | tên module được gắn adapter LoRA. **Tên khác nhau theo kiến trúc** (Qwen3: `q_proj`, `k_proj`; PhoBERT và ViSoBERT: `query`, `key`, `value`, `dense`), nên khoá này thuộc config của model chứ không nằm ở file huấn luyện dùng chung |
| suy luận   | `inference.dtype`                  | `auto` = mã chọn theo máy: bf16 khi GPU hỗ trợ **thật**, fp16 khi không (T4), fp32 trên CPU. Khai tường minh `float16`/`bfloat16`/`float32` thì chạy ĐÚNG giá trị đó; máy không đáp ứng được là **LỖI** (không hạ cấp) - một hàm giải duy nhất cho cả đường prompt và đường encoder (`src/experiments/model_config.py::resolve_dtype`) |
| suy luận   | `inference.quantization`           | `4bit` thì phải có `bitsandbytes`; để trống/`null` là chạy KHÔNG lượng hoá. Giá trị này đi vào mã băm của lượt chạy, nên `4bit` và không lượng hoá là hai thư mục kết quả khác nhau |
| suy luận   | `inference.batch_size`             | số review mỗi lượt sinh (đường prompt) hoặc mỗi lượt chấm (đường encoder)                  |

## Tên model đang dùng

| `model_id`               | Ghi chú                             |
| ------------------------ | ----------------------------------- |
| `qwen3-4b-instruct-2507` | chỉ dùng cho thí nghiệm prompt      |
| `qwen3-0.6b`             | model THỨ TƯ của thử nghiệm: cùng ba mức ví dụ của công bố để đo khoảng cách của một model nhỏ (chạy được cả CPU). **Mặc định BẬT suy nghĩ** nên đã khai `preprocess.enable_thinking: false` |
| `qwen2.5-0.5b-instruct`  | model nhỏ KHÁC HỌ (thế hệ `qwen2`): mốc "nhỏ thì kém" thứ hai, để kết luận về quy mô không phụ thuộc một họ model |
| `phobert-base-v2`        | encoder, huấn luyện LoRA hoặc QLoRA |
| `phobert-large`          | encoder: cùng kho tiền huấn luyện, cùng bộ tách từ với bản base - chỉ khác số tham số (một biến sạch) |
| `visobert`               | encoder, huấn luyện LoRA hoặc QLoRA |
| `vibert-base-cased`      | encoder: kho tiền huấn luyện tiếng Việt KHÁC (FPT), vẫn tách từ như PhoBERT |
| `cafebert`               | encoder: XLM-R rồi tiền huấn luyện TIẾP trên văn bản tiếng Việt - bậc thang giữa PhoBERT và XLM-R; dùng SentencePiece (KHÔNG tách từ) |
| `xlm-roberta-base`       | **đối chứng NGUỒN tiền huấn luyện** (đa ngữ, phần tiếng Việt rất nhỏ). ⚠️ cũng khác bộ tách từ, nên so với PhoBERT là so HAI biến - xem `src/preprocessing/xlmroberta.py` |

## Thêm model mới

1. Viết một module trong `src/preprocessing/` theo hợp đồng ở `src/preprocessing/__init__.py`.
   Encoder kiểu BERT (tokenizer + tuỳ chọn tách từ) thì KHÔNG cần chép mã: dùng `src/preprocessing/bert_like.py`
   rồi khai ba hằng số (`MODEL_NAME`, `CONFIG_NAME`, `SEGMENTER`) và gọi sang - xem `xlmroberta.py` làm mẫu.
2. Thêm file YAML trong `configs/models/` với `model_id` trùng tên file.
3. Đăng ký module vào HAI registry: `src/training/encoders.py` (nếu `approach: encoder`, để huấn luyện được)
   và `MODELS` trong `src/preprocessing/token_stats.py` (để đo input thật). Cập nhật `src/core/registry.py`.
