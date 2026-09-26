# exp001 - PhoBERT-base-v2 học LoRA, chấm trên test

## Thí nghiệm này hỏi câu gì

**PhoBERT (135M tham số, đã tách từ bằng VnCoreNLP) học LoRA thì chấm được bao nhiêu so với công
bố?** Học từ `train`, chọn `model/best` theo `val`, chấm trên `test` - đúng tập test của công bố.

## Khác gì những lần chạy trước

Không có lần chạy trước (`parent: null`). Bốn lựa chọn của thí nghiệm này:

| Lựa chọn | Giá trị | Vì sao |
| --- | --- | --- |
| Cách học | LoRA (`training.enabled: true`) | Hai encoder nhỏ chỉ học qua LoRA/QLoRA, không full fine-tune |
| Tách từ | `vncorenlp` (bộ chính chủ của PhoBERT) | PhoBERT được tiền huấn luyện trên văn bản đã tách từ; bỏ bước này là giảm chất lượng |
| Split chấm | `test` (1.518 review) | Con số để SO VỚI CÔNG BỐ; `val` chỉ dùng để chọn `model/best` |
| Số mẫu | cả split | So với công bố thì phải chấm hết tập test |

Cần hai thứ không có trong git: Java (bootstrap trên Colab tự cài `default-jdk` + `py-vncorenlp`) và
model VnCoreNLP (~27 MB, khai ở `requires_extra` nên notebook kiểm trước khi chạy; gói bàn giao đã
kèm sẵn trong `data/models/vncorenlp/`). Trên máy cá nhân xem `scripts/setup_java.ps1` và
`scripts/setup_vncorenlp.ps1`.

## Kết quả nằm ở đâu

`results/<hash8>/` (mã băm danh tính: cấu hình + dữ liệu + **commit đã ghim**), gồm `run.log`,
`run_meta.json`, `metrics.json`, `metrics.csv`, `mispredictions.csv`, `predictions.csv`, và
`model/{last,best}`.

## Chạy lại

Bấm **Run all** trong `notebook.ipynb`. Bị ngắt: chạy lại - huấn luyện tiếp tục từ `model/last`, suy
luận tiếp tục từ `predictions/part_*.jsonl`. Muốn chạy lại từ đầu thì **xoá thư mục `results/<hash8>/`**.

