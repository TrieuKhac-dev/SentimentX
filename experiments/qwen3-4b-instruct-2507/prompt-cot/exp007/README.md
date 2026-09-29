# exp007 - Qwen3-4B, CoT 5 ví dụ, KHÔNG lượng hoá (fp16)

## Thí nghiệm này hỏi câu gì

**Lượng hoá 4-bit làm mất bao nhiêu điểm ở prompt dài nhất?** Bản đối chứng của
`qwen3-4b-instruct-2507/prompt-cot/exp004`: cùng model, cùng prompt 5 ví dụ, cùng tập `test`, chỉ khác
cách nạp trọng số. Đây là lượt khó nhất về bộ nhớ trong ba mức ví dụ.

## Khác gì những lần chạy trước

`parent: qwen3-4b-instruct-2507/prompt-cot/exp004` (bản 4-bit của cùng mức ví dụ).

| Lựa chọn | Giá trị | Vì sao |
| --- | --- | --- |
| `inference.quantization` | `null` | Biến của thí nghiệm: không lượng hoá |
| `inference.dtype` | `float16` | T4 không có bf16; khai thẳng thay vì để máy tự chọn |
| `inference.batch_size` | `4` (config model là `8`) | Bản fp16 tốn gấp ~4 lần bộ nhớ, và prompt 5 ví dụ dài nhất (trung bình 1.877,5 token, dài nhất 2.122) |
| Prompt / ví dụ / split / cách sinh | `absa_cot_5shot_v1`, `test`, greedy | Giữ nguyên mọi thứ khác |

Cách so đúng: đối chiếu **từng dòng** trong `predictions.csv` của `exp004` và lượt này, vì `batch_size`
cũng nằm trong mã băm danh tính.

## Kết quả nằm ở đâu

`results/<hash8>/` (khác `<hash8>` của `exp004`). Bản tổng hợp để so nhiều lượt nằm ở
`data/reports/metrics_matrix.csv` sau khi chạy `scripts/collect_reports.py`.

## Chạy lại

Bấm **Run all** trong `notebook.ipynb`. Cần GPU 16 GB (T4). Nếu hết bộ nhớ, hạ `inference.batch_size`
xuống `2` **và ghi lại lý do**: `batch_size` nằm trong mã băm, nên đổi nó là đổi lượt chạy chứ không phải
chỉnh một tham số vặt.
