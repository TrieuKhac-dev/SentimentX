# exp005 - Qwen3-4B, CoT 0 ví dụ, KHÔNG lượng hoá (fp16)

## Thí nghiệm này hỏi câu gì

**Lượng hoá 4-bit làm mất bao nhiêu điểm?** Đây là bản đối chứng của
`qwen3-4b-instruct-2507/prompt-cot/exp002`: cùng model, cùng prompt, cùng tập `test`, chỉ khác cách
nạp trọng số. exp002 chạy trên máy 6 GB VRAM (buộc phải 4-bit); lượt này chạy trên Colab T4 (16 GB).

## Khác gì những lần chạy trước

`parent: qwen3-4b-instruct-2507/prompt-cot/exp002` - hai thứ khác, và cả hai đều được ghi lại:

| Lựa chọn | exp002 (4-bit) | exp005 (lượt này) | Vì sao |
| --- | --- | --- | --- |
| `inference.quantization` | `4bit` | `null` (không lượng hoá) | Đây là BIẾN của thí nghiệm |
| `inference.batch_size` | `8` | `4` | Bản fp16 tốn gấp ~4 lần bộ nhớ (khoảng 8 GB trọng số), nên phải hạ lô cho vừa T4 |
| `inference.dtype` | `auto` | `float16` | T4 không có bf16; khai thẳng số cụ thể thay vì để máy tự chọn |
| Prompt / ví dụ / split / cách sinh | `absa_cot_zeroshot_v1`, `test`, greedy | y hệt | Giữ nguyên mọi thứ khác để chênh lệch đọc được là do lượng hoá |

`batch_size` cũng nằm trong mã băm danh tính lượt chạy, nên **không được quy hết chênh lệch cho lượng
hoá**. Muốn tách bạch thì so từng dòng `predictions.csv` của hai lượt (repo đã có sẵn cột dự đoán theo
từng review), thay vì chỉ nhìn hai con số điểm.

## Kết quả nằm ở đâu

`results/<hash8>/` (khác `<hash8>` của exp002 vì lượng hoá và lô đều khác). Bản tổng hợp để so nhiều
lượt nằm ở `data/reports/metrics_matrix.csv` sau khi chạy `scripts/collect_reports.py`.

## Chạy lại

Bấm **Run all** trong `notebook.ipynb`. Lượt này cần GPU 16 GB (T4) - máy 6 GB VRAM sẽ hết bộ nhớ khi
chạy bản fp16 của model 4B, đó là lý do nó nằm trong nhóm chạy trên Colab.
