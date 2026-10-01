# exp003 - Qwen3-0.6B, CoT 5 ví dụ, chấm trên test

## Thí nghiệm này hỏi câu gì

**Năm ví dụ có kéo bản 0.6B lên gần bản 4B không?** Đây là mức **COT+5-shot** của công bố, chạy trên cùng
tập `test` và cùng prompt với `qwen3-4b-instruct-2507/prompt-cot/exp004` của bản 4B.

## Khác gì những lần chạy trước

`parent: null` - ba mức ví dụ (0/1/5) là ba thí nghiệm NGANG HÀNG, không phải bản làm lại của nhau.

| Lựa chọn | Giá trị | Vì sao |
| --- | --- | --- |
| Model | `qwen3-0.6b` | Cùng tokenizer và cùng ngưỡng cắt với bản 4B, nên đây là biến duy nhất được đổi |
| Prompt | `absa_cot_5shot_v1` + bộ ví dụ `absa_cot_5shot_v1` + khối hệ thống `absa_cot` | Đúng mức 5 ví dụ của công bố |
| Split chấm | `test` (cả split của bộ dữ liệu đang dùng) | Con số để SO VỚI CÔNG BỐ |
| Số mẫu | cả split (`n: null`) | Chấm tập con rồi đem so là so hai phép đo khác nhau |
| Cách sinh | `greedy` | Tất định nên tái lập được |

Bản 5 ví dụ là mức prompt DÀI NHẤT của công bố (1.877,5 token trung bình, dài nhất 2.122), nên đây cũng là
mức dễ vượt ngưỡng cắt 2304 nhất - `run_meta.json` ghi lại số lượt bị cắt để kiểm điều đó.

## Kết quả nằm ở đâu

`results/<hash8>/`: `run.log`, `run_meta.json`, `metrics.json`, `metrics.csv`, `mispredictions.csv`,
`predictions.csv` (kèm cột prompt đã gửi model), `predictions/part_*.jsonl`.

## Chạy lại

Bấm **Run all** trong `notebook.ipynb`. Bị ngắt thì chạy lại: nó tiếp tục từ `predictions/part_*.jsonl`.
Muốn chạy lại từ đầu thì **xoá thư mục `results/<hash8>/`**.
