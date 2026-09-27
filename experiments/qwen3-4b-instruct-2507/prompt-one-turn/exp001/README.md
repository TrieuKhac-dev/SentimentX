# exp001 - Qwen3-4B, prompt một lượt (0 ví dụ), chấm trên test

## Thí nghiệm này hỏi câu gì

**Hỏi model MỘT lượt, không bắt suy luận từng bước: 4B trả nhãn cho 7 khía cạnh thì được bao nhiêu?**
Đây là MỐC SO SÁNH cho ba mức CoT của công bố (`exp002` 0 ví dụ, `exp003` 1 ví dụ, `exp004` 5 ví dụ):
cùng model, cùng tập `test`, khác đúng một thứ - có bắt model viết phần suy luận hay không.

## Khác gì những lần chạy trước

`parent: null`. Trước đây mức "một lượt" chỉ được đo nhanh trên 100 review của `val`
(`docs/04_experiments/03_training_eval.md` mục 6); thí nghiệm này cho nó con số CHÍNH THỨC trên `test`.

| Lựa chọn | Giá trị | Vì sao |
| --- | --- | --- |
| Prompt | `configs/prompts/absa_one_turn_v1.txt` | Một lượt: chỉ hỏi và chốt mã, không yêu cầu suy luận từng bước |
| System prompt | `configs/prompts/system/absa_one_turn.txt` (file riêng) | Khối hệ thống không nằm trong file prompt |
| Ví dụ | không | 0 ví dụ - mức rẻ nhất trong bốn mức |
| Split chấm | `test` (1.518 review) | Cùng tập với `exp002`/`exp003`/`exp004` nên so được với nhau |
| Số mẫu | cả split (`n: null`) | Chấm một tập con rồi đem so là so hai phép đo khác nhau |
| Cách sinh | `greedy` | Tất định nên tái lập được |

## Kết quả nằm ở đâu

`results/<hash8>/`: `run.log`, `run_meta.json`, `metrics.json`, `metrics.csv`, `mispredictions.csv`,
`predictions.csv` (kèm cột prompt đã gửi model), `predictions/part_*.jsonl`.

## Chạy lại

Bấm **Run all** trong `notebook.ipynb`. Bị ngắt thì chạy lại: nó tiếp tục từ `predictions/part_*.jsonl`.
Muốn chạy lại từ đầu thì **xoá thư mục `results/<hash8>/`**.
