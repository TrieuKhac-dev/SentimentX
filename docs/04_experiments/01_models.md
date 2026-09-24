# Ba model thực nghiệm - và vì sao tách preprocessing khỏi pipeline

Tài liệu tiền xử lý cho model-4 (chuẩn bị input cho từng model, huấn luyện và đánh giá) chỉ bắt đầu
**sau khi** EDA và Data Pipeline đã xong.

## 1. Model sẽ thực nghiệm

| Model             | Nguồn                                              | Kiểu                                      |
| ----------------- | -------------------------------------------------- | ----------------------------------------- |
| PhoBERT           | https://huggingface.co/vinai/phobert-base-v2       | encoder tiếng Việt (BERT)                 |
| ViSoBERT          | https://huggingface.co/uitnlp/visobert             | encoder tiếng Việt (dữ liệu mạng xã hội)  |
| Qwen3-4B-Instruct | https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507 | mô hình sinh lớn (dùng theo dạng chỉ dẫn) |

Ba model này đại diện cho **ba hướng tiếp cận khác nhau**, nên so sánh được với nhau:
hai encoder tiếng Việt (một loại cần tách từ, một loại không) và một mô hình lớn dùng
theo dạng chỉ dẫn (prompt -> sinh JSON).

**ViTASA: gác lại, chưa đưa vào thực nghiệm.** Repo `kh4nh12/ViTASA` hiện chỉ có
`LICENSE`, `README.md` và 3 file `.jsonl` - không có mã model, không có checkpoint, không
có script huấn luyện; Hugging Face Hub cũng không có dataset/model nào tên `vitasa`.
Nghĩa là chưa có gì để chạy, và viết thêm code chỉ là suy đoán chứ không phải tái lập.
Khung mã (`src/preprocessing/vitasa.py`) và các bước làm tiếp đã ghi ở
[04_backlog.md](04_backlog.md) mục 1.

## 2. Vì sao phải tách "Model preprocessing" khỏi Pipeline

Mỗi model cần một dạng input **khác nhau**:

```
PROCESSED DATA (data/processed)
        |
        +-- PhoBERT   : tách từ tiếng Việt  ->  tokenizer  ->  input_ids + attention_mask
        +-- ViSoBERT  :                        tokenizer  ->  input_ids + attention_mask
        \-- Qwen3     : prompt chỉ dẫn      ->  chat template  ->  tokenizer
                          (nội dung prompt ở configs/prompts/<tên>.txt)
```

Nếu nhét những bước này vào pipeline chung, pipeline sẽ **phụ thuộc vào một model
cụ thể** và không còn dùng lại được cho model khác.

Đặc biệt: **tách từ tiếng Việt là bước riêng của PhoBERT**, KHÔNG phải một bước
"cleaning" chung. Tương tự với tokenizer và với prompt.

Chính vì tách từ là bước riêng của model nên nó **thay được mà không ảnh hưởng ai
khác**: các bộ tách từ nằm trong `src/preprocessing/segmenters/`, chọn bằng
`--segmenter <tên>`, mặc định là bộ chính chủ RDRSegmenter/VnCoreNLP. Tách từ khác tokenizer,
nên đổi bộ tách từ không kéo theo việc đổi tokenizer - nhờ vậy câu hỏi "tách từ giúp bao
nhiêu" trả lời được bằng số đo (xem [02_model_input.md mục 3](02_model_input.md)).

Hệ quả về thiết kế: pipeline kết thúc ở dữ liệu đã sạch + dạng multi_head
([03_pipeline/05_output.md](../03_pipeline/05_output.md)), còn mọi thứ "model cần gì"
nằm ở `src/preprocessing/` - xem [02_model_input.md](02_model_input.md).

---

Xem tiếp: [02_model_input.md](02_model_input.md) - chuẩn bị input và đo token thật;
[04_backlog.md](04_backlog.md) - việc đã biết nhưng chưa làm (ViTASA, prompt CoT, ...).
