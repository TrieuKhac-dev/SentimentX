# exp002 - Qwen3-4B, CoT 0 ví dụ (zero-shot), chấm trên test

## Thí nghiệm này hỏi câu gì

**Đúng mức COT+0-shot của công bố: 4B tự trả nhãn cho 7 khía cạnh mà không có ví dụ nào thì được bao
nhiêu?** Đây là một trong ba mức 0/1/5 ví dụ của công bố, chấm trên đúng tập `test` của họ.

## Khác gì những lần chạy trước

`parent: null` - ba mức ví dụ là ba thí nghiệm NGANG HÀNG, không phải bản làm lại của nhau.

| Lựa chọn | Giá trị | Vì sao |
| --- | --- | --- |
| Prompt | `configs/prompts/absa_cot_zeroshot_v1.txt` | Bản 0 ví dụ; KHÔNG khai `examples` vì prompt không có ô nhớ `{examples}` |
| Split chấm | `test` (1.518 review) | Con số để SO VỚI CÔNG BỐ |
| Số mẫu | cả split (`n: null`) | Chấm một tập con rồi đem so là so hai phép đo khác nhau |
| Cách sinh | `greedy` | Tất định nên tái lập được |

So với `exp001` (CoT 2 ví dụ) và `exp004` (CoT 5 ví dụ), thí nghiệm này trả lời câu "ví dụ có giúp
không" ở mức 0.

## Kết quả nằm ở đâu

`results/<hash8>/`: `run.log`, `run_meta.json`, `metrics.json`, `metrics.csv`, `mispredictions.csv`,
`predictions.csv` (kèm cột prompt đã gửi model), `predictions/part_*.jsonl`.

## Chạy lại

Bấm **Run all** trong `notebook.ipynb`. Bị ngắt thì chạy lại: nó tiếp tục từ `predictions/part_*.jsonl`.
Muốn chạy lại từ đầu thì **xoá thư mục `results/<hash8>/`**.

