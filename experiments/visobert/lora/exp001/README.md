# exp001 - ViSoBERT học LoRA, chấm trên test

## Thí nghiệm này hỏi câu gì

**Một model encoder nhỏ học bằng LoRA thì chấm được bao nhiêu so với công bố?** ViSoBERT (~108M tham
số) đọc review nguyên bản (không tách từ), học từ `train`, chọn `model/best` theo `val`, rồi chấm
trên `test` - đúng tập test của công bố tham chiếu.

## Khác gì những lần chạy trước

Không có lần chạy trước (`parent: null`). Bốn lựa chọn của thí nghiệm này:

| Lựa chọn | Giá trị | Vì sao |
| --- | --- | --- |
| Cách học | LoRA (`training.enabled: true`) | Quyết định của dự án: hai encoder nhỏ chỉ học qua LoRA/QLoRA, không full fine-tune |
| Tham số | `configs/experiments/training.yaml`, module LoRA ở `configs/models/visobert.yaml` | Tên module khác nhau theo kiến trúc, nên `target_modules` thuộc config của model |
| Split chấm | `test` (1.518 review) | Con số để SO VỚI CÔNG BỐ; `val` chỉ dùng để chọn `model/best` |
| Số mẫu | cả split | So với công bố thì phải chấm hết tập test |

## Kết quả nằm ở đâu

`results/<hash8>/` (mã băm danh tính: cấu hình + dữ liệu + **commit đã ghim**), gồm `run.log`,
`run_meta.json`, `metrics.json`, `metrics.csv`, `mispredictions.csv`, `predictions.csv`, và
`model/{last,best}`. `model/last` đủ để chạy tiếp; `model/best` chỉ có adapter để suy luận.

Không chép số liệu vào README này: số liệu nằm trong `metrics.json`, bản tổng hợp do
`scripts/collect_reports.py` sinh.

## Chạy lại

Bấm **Run all** trong `notebook.ipynb`. Bị ngắt giữa chừng: chạy lại - phần huấn luyện tiếp tục từ
`model/last`, phần suy luận tiếp tục từ `predictions/part_*.jsonl`. Muốn chạy lại từ đầu thì **xoá
thư mục `results/<hash8>/`**.

