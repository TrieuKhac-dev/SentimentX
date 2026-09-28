# exp006 - Qwen3-4B, CoT 1 ví dụ, KHÔNG lượng hoá (fp16)

## Thí nghiệm này hỏi câu gì

**Lượng hoá 4-bit làm mất bao nhiêu điểm khi prompt có một ví dụ?** Bản đối chứng của
`qwen3-4b-instruct-2507/prompt-cot/exp003`: cùng model, cùng prompt 1 ví dụ, cùng tập `test`, chỉ khác
cách nạp trọng số. Lặp lại phép đo này ở mức 1 ví dụ vì prompt dài hơn thì lượng hoá có thể sai khác
nhiều hơn ở mức 0 ví dụ - một lượt chạy không đủ để nói.

## Khác gì những lần chạy trước

`parent: qwen3-4b-instruct-2507/prompt-cot/exp003` (bản 4-bit của cùng mức ví dụ).

| Lựa chọn | Giá trị | Vì sao |
| --- | --- | --- |
| `inference.quantization` | `null` | Biến của thí nghiệm: không lượng hoá, tức là bản `exp003` bị đổi ĐÚNG một thứ về mặt mô hình |
| `inference.dtype` | `float16` | T4 không có bf16; khai thẳng thay vì để máy tự chọn |
| `inference.batch_size` | `4` (config model là `8`) | Bản fp16 tốn gấp ~4 lần bộ nhớ, phải hạ lô cho vừa T4 |
| Prompt / ví dụ / split / cách sinh | `absa_cot_1shot_v1`, `test`, greedy | Giữ nguyên mọi thứ khác |

Cách so đúng: đối chiếu **từng dòng** trong `predictions.csv` của `exp003` và lượt này. `batch_size`
cũng nằm trong mã băm danh tính, nên chênh lệch giữa hai lượt **không** mặc nhiên là do lượng hoá.

## Kết quả nằm ở đâu

`results/<hash8>/` (khác `<hash8>` của `exp003`). Bản tổng hợp để so nhiều lượt nằm ở
`data/reports/metrics_matrix.csv` sau khi chạy `scripts/collect_reports.py`.

## Chạy lại

Bấm **Run all** trong `notebook.ipynb`. Cần GPU 16 GB (T4): bản fp16 của model 4B không vừa máy 6 GB VRAM.
