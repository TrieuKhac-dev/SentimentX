# exp001 - Qwen3-0.6B, CoT 0 ví dụ (zero-shot), chấm trên test

## Thí nghiệm này hỏi câu gì

**Bản 0.6B có tự trả nhãn cho 7 khía cạnh mà không có ví dụ nào không, và nó kém bản 4B bao nhiêu?**
Đây là mức **COT+0-shot** của công bố, chạy trên **cùng tập test** và cùng prompt với
`qwen3-4b-instruct-2507/prompt-cot/exp002`.

## Khác gì những lần chạy trước

`parent: null` - thí nghiệm đầu tiên của bản 0.6B. So với `exp002` của bản 4B, **model là thứ duy nhất
khác**: cùng tokenizer (bản 0.6B có `tokenizer.json` giống từng byte), cùng ngưỡng cắt 2304, cùng prompt.

| Lựa chọn | Giá trị | Vì sao |
| --- | --- | --- |
| Model | `qwen3-0.6b` (`configs/models/qwen3-0.6b.yaml`) | Model THỨ TƯ của thử nghiệm: đo khoảng cách của một model nhỏ hơn ~10 lần |
| Prompt | `configs/prompts/absa_cot_zeroshot_v1.txt` + khối hệ thống `absa_cot` | Bản 0 ví dụ; KHÔNG khai `examples` vì prompt không có ô nhớ `{examples}` |
| Split chấm | `test` (cả split của bộ dữ liệu đang dùng) | Con số để SO VỚI CÔNG BỐ |
| Số mẫu | cả split (`n: null`) | Chấm một tập con rồi đem so là so hai phép đo khác nhau |
| Cách sinh | `greedy` | Tất định nên tái lập được |

## Kết quả nằm ở đâu

`results/<hash8>/`: `run.log`, `run_meta.json`, `metrics.json`, `metrics.csv`, `mispredictions.csv`,
`predictions.csv` (kèm cột prompt đã gửi model), `predictions/part_*.jsonl`.

## Chạy lại

Bấm **Run all** trong `notebook.ipynb`. Bị ngắt thì chạy lại: nó tiếp tục từ `predictions/part_*.jsonl`.
Muốn chạy lại từ đầu thì **xoá thư mục `results/<hash8>/`**.
