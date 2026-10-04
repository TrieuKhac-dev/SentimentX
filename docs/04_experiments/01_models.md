# Bốn model thực nghiệm - và vì sao tách preprocessing khỏi pipeline

> Đọc file này khi: thêm model mới, hoặc xem model nào chạy được trên máy nào.
> Liên quan: `docs/05_config/04_models.md`, `docs/04_experiments/02_model_input.md`,
> `docs/04_experiments/06_lora_encoder.md` (kết quả encoder), `docs/04_experiments/08_experiment_rationale.md` (câu hỏi từng lượt)

Tài liệu tiền xử lý cho model-4 (chuẩn bị input cho từng model, huấn luyện và đánh giá) chỉ bắt đầu
**sau khi** EDA và Data Pipeline đã xong.

## 1. Model sẽ thực nghiệm

| Model             | Nguồn                                              | Kiểu                                      |
| ----------------- | -------------------------------------------------- | ----------------------------------------- |
| PhoBERT           | https://huggingface.co/vinai/phobert-base-v2       | encoder tiếng Việt (BERT)                 |
| ViSoBERT          | https://huggingface.co/uitnlp/visobert             | encoder tiếng Việt (dữ liệu mạng xã hội)  |
| Qwen3-4B-Instruct | https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507 | mô hình sinh lớn (dùng theo dạng prompt) |
| Qwen3-0.6B        | https://huggingface.co/Qwen/Qwen3-0.6B             | mô hình sinh nhỏ (dùng theo dạng prompt) |

Bốn model này phủ **ba hướng tiếp cận** khác nhau, nên so sánh được với nhau: hai encoder tiếng Việt
(một loại cần tách từ, một loại không) và hai mô hình sinh dùng theo dạng prompt (prompt -> sinh JSON).
Hai bản Qwen3 là **một biến thực nghiệm về QUY MÔ**: cùng tokenizer (bản 0.6B có `tokenizer.json` giống
từng byte), cùng ba mức ví dụ của công bố, cùng tập test - nên câu hỏi "model nhỏ hơn 10 lần mất bao
nhiêu điểm" trả lời được **mà không đổi bất kỳ thứ gì khác**.

**Cảnh báo bắt buộc khi chạy Qwen3-0.6B:** bản `Qwen/Qwen3-0.6B` (4/2025) **mặc định BẬT suy nghĩ**, nên
nó tiêu hết trần `max_new_tokens` trong khối ` thinking` rồi không còn chỗ in JSON. Ngày 02/10/2026 ba lượt
0.6B vì thế chỉ đọc được **3,33 / 1,36 / 1,73%** số review. Muốn chạy 0.6B thì **phải** khai
`preprocess.enable_thinking: false` ở cấu hình model (và nếu muốn *bật* suy nghĩ thì phải chạy một lượt
**DÒ** trước để chốt trần token - xem `present_plan.md` mục 9.1).

**Trạng thái kết quả (tới 04/10/2026, tổng 17 lượt):**

| Model | Số lượt dùng được | Điểm đáng nhớ |
| --- | --- | --- |
| PhoBERT | 2 (`lora/exp001`, `lora/exp002`) | 88,40 → **96,62** khi thêm `weighted_ce`; F1 lớp âm 0,540 → 0,876; nhưng phát hiện khía cạnh 98,05 → 94,14 |
| ViSoBERT | 2 (`lora/exp001`, `lora/exp002`) | 94,86 → **95,61**; F1 lớp âm 0,765 → 0,836; phát hiện khía cạnh 98,29 → 97,06 (tốt nhất trong 17 lượt ở lượt gốc) |
| Qwen3-4B | 13 (12 lượt `prompt-cot` + 1 lượt `prompt-one-turn`) | đỉnh **97,77** (`exp009`, 1 ví dụ, 4-bit lô 4) - hơn công bố 0,07 điểm; 4-bit hơn fp16 **0,64 / 1,17 / 0,71 điểm** nhưng trả lời ít hơn 5-6% số ô |
| Qwen3-0.6B | **0** | hai lần chạy hỏng hai kiểu (nạp nhầm trọng số 4B; bật suy nghĩ ăn hết trần token); sáu thư mục kết quả đã xoá 04/10/2026; sẽ chạy lại với `enable_thinking: false` |

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
        \-- Qwen3     : prompt + system prompt  ->  chat template  ->  tokenizer
                          (prompt: `configs/prompts/<tên>.txt` hoặc file trong thư mục thí nghiệm;
                           system prompt: FILE RIÊNG - `configs/prompts/system/<tên>.txt` khi dùng chung,
                           hoặc `system.txt` trong thư mục thí nghiệm khi chỉ nó dùng)
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
