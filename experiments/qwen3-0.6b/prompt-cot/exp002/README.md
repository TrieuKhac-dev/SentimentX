# exp002 - Qwen3-0.6B, CoT 1 ví dụ, chấm trên test

## Thí nghiệm này hỏi câu gì

**Một ví dụ few-shot có giúp bản 0.6B không?** Đây là mức **COT+1-shot** của công bố, chạy trên cùng tập
`test` và cùng prompt với `qwen3-4b-instruct-2507/prompt-cot/exp003` của bản 4B.

## Khác gì những lần chạy trước

`parent: null` - ba mức ví dụ (0/1/5) là ba thí nghiệm NGANG HÀNG, không phải bản làm lại của nhau.

| Lựa chọn | Giá trị | Vì sao |
| --- | --- | --- |
| Model | `qwen3-0.6b` | Cùng tokenizer và cùng ngưỡng cắt với bản 4B, nên đây là biến duy nhất được đổi |
| Prompt | `absa_cot_1shot_v1` + bộ ví dụ `absa_cot_1shot_v1` + khối hệ thống `absa_cot` | Đúng mức 1 ví dụ của công bố |
| Split chấm | `test` (1.518 review) | Con số để SO VỚI CÔNG BỐ |
| Số mẫu | cả split (`n: null`) | Chấm tập con rồi đem so là so hai phép đo khác nhau |
| Cách sinh | `greedy` | Tất định nên tái lập được |

So với `exp001` (0 ví dụ), thí nghiệm này trả lời "thêm MỘT ví dụ thì được gì".

## Kết quả nằm ở đâu

`results/<hash8>/`: `run.log`, `run_meta.json`, `metrics.json`, `metrics.csv`, `mispredictions.csv`,
`predictions.csv` (kèm cột prompt đã gửi model), `predictions/part_*.jsonl`.

## Chạy lại

Bấm **Run all** trong `notebook.ipynb`. Bị ngắt thì chạy lại: nó tiếp tục từ `predictions/part_*.jsonl`.
Muốn chạy lại từ đầu thì **xoá thư mục `results/<hash8>/`**.
