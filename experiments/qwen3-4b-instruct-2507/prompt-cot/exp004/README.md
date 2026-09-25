# exp004 - Qwen3-4B, CoT 5 ví dụ, chấm trên test

## Thí nghiệm này hỏi câu gì

**Đúng mức COT+5-shot của công bố: năm ví dụ mẫu có tốt hơn 0 và 1 ví dụ không?** Cùng tập `test`,
cùng cách sinh, cùng cách chấm như `exp002` và `exp003`; đây là mức cao nhất của công bố.

## Khác gì những lần chạy trước

`parent: null` - ba mức ví dụ là ba thí nghiệm NGANG HÀNG.

| Lựa chọn | Giá trị | Vì sao |
| --- | --- | --- |
| Prompt | `configs/prompts/absa_cot_5shot_v1.txt` | Câu chỉ dẫn + ô nhớ `{examples}` |
| Bộ ví dụ | `configs/prompts/examples/absa_cot_5shot_v1.txt` (5 khối) | Cùng prompt dài hơn nên chi phí input cao hơn: 1.866 token/review trung bình (đo ở `docs/04_experiments/02_model_input.md`) |
| Ngưỡng cắt | `preprocess.max_length: 2304` (từ `configs/models/qwen3-4b-instruct-2507.yaml`) | Ở ngưỡng 1280 thì 100% review mất phần đuôi, tức mất luôn yêu cầu định dạng đầu ra |
| Split chấm | `test` (1.518 review) | Con số để SO VỚI CÔNG BỐ |

## Kết quả nằm ở đâu

`results/<hash8>/`: `run.log`, `run_meta.json`, `metrics.json`, `metrics.csv`, `mispredictions.csv`,
`predictions.csv` (có cột prompt đã gửi model), `predictions/part_*.jsonl`.

## Chạy lại

Bấm **Run all** trong `notebook.ipynb`; bị ngắt thì chạy lại, nó tiếp tục từ mẫu đã xong. Muốn chạy
lại từ đầu thì **xoá thư mục `results/<hash8>/`**. Lượt này tốn thời gian nhất trong ba mức ví dụ vì
prompt dài nhất.

