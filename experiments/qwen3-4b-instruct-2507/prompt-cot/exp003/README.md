# exp003 - Qwen3-4B, CoT 1 ví dụ, chấm trên test

## Thí nghiệm này hỏi câu gì

**Đúng mức COT+1-shot của công bố: thêm MỘT ví dụ mẫu có làm tăng điểm không?** Chấm trên đúng tập
`test` của công bố, cùng cách sinh và cùng cách chấm như `exp002` (0 ví dụ) và `exp004` (5 ví dụ).

## Khác gì những lần chạy trước

`parent: null` - ba mức ví dụ là ba thí nghiệm NGANG HÀNG.

| Lựa chọn | Giá trị | Vì sao |
| --- | --- | --- |
| Prompt | `configs/prompts/absa_cot_1shot_v1.txt` | Câu chỉ dẫn + ô nhớ `{examples}` |
| Bộ ví dụ | `configs/prompts/examples/absa_cot_1shot_v1.txt` (1 khối) | Prompt khai bằng ĐƯỜNG DẪN nên file ví dụ phải khai TƯỜNG MINH; test `tests/test_prompts.py` khoá số khối phải khớp tên `1shot` |
| Split chấm | `test` (1.518 review) | Con số để SO VỚI CÔNG BỐ |
| Số mẫu | cả split (`n: null`) | Chấm tập con rồi đem so là so hai phép đo khác nhau |

## Kết quả nằm ở đâu

`results/<hash8>/`: `run.log`, `run_meta.json`, `metrics.json`, `metrics.csv`, `mispredictions.csv`,
`predictions.csv` (có cột prompt đã gửi model để tra từng mẫu), `predictions/part_*.jsonl`.

## Chạy lại

Bấm **Run all** trong `notebook.ipynb`; bị ngắt thì chạy lại, nó tiếp tục từ mẫu đã xong. Muốn chạy
lại từ đầu thì **xoá thư mục `results/<hash8>/`**.

