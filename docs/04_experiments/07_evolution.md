# 07. Cây phát triển thí nghiệm

> Đọc file này khi: muốn biết một thí nghiệm SINH RA từ đâu, hoặc vì sao dự án đi bước tiếp theo là bước đó.
> Liên quan: `docs/04_experiments/04_backlog.md` (việc chưa làm), `docs/06_plan/P7_rerun.md` (đợt chạy lại)

File này là bản NGƯỜI ĐỌC của dòng phát triển thí nghiệm: **thí nghiệm nào sinh ra thí nghiệm nào, và
VÌ SAO**. Bảng máy đọc nằm ở `data/reports/experiment_registry/` (mỗi lượt chạy một dòng); ở đây ghi
phần một dòng CSV không chứa được - **lý do** và **quan hệ cha - con** giữa các bước.

Quy ước ghi một nút:

```
<expNNN hoặc mã lượt chạy>  <-  <nút cha>            (vì sao đi bước này)
    Kết quả: <số nhanh>       Kết luận: <giữ / bỏ / đổi hướng>
```

File này ĐỂ TRỐNG nội dung cây lúc tạo và được ghi DẦN: mỗi khi chốt một bước phát triển mới (thêm
thí nghiệm, đổi loss, hoãn một kỹ thuật, ...) thì thêm một nút kèm lý do và mốc ngày.

---

## Chốt kỹ thuật của đợt "đo lường + MLflow" (mốc 02/10/2026)

Các mục dưới đây là QUYẾT ĐỊNH đã chốt; việc CHƯA làm nằm ở `docs/04_experiments/04_backlog.md`.

### Chọn `model/best` và dừng sớm

- Chọn best theo `checkpoints.best_metric` (mặc định `sentiment_f1` = macro-F1 sắc thái). Vì sao KHÔNG
  dùng `accuracy_cell`: dữ liệu mất cân bằng (ví dụ `price` 3.238 dương / 21 âm) nên accuracy bị lớp
  trội chi phối, còn macro-F1 cho mỗi khía cạnh một phiếu.
- `val` đo bằng ĐÚNG engine của `test` (`src/evaluation/scorers`), nên `val` có đủ P/R/F1 và detection
  F1 - không có định nghĩa metric thứ hai.
- `early_stop.enabled: true` thì dừng khi chỉ số val không tăng quá `min_delta` trong `patience` lần đo
  liên tiếp. CHỈ đường huấn luyện encoder; model prompt không train nên không đụng tới.

### Hai mục đích, HAI cơ sở đo (đừng lẫn)

| Mục đích | Cơ sở đo | Tập | Nguồn số |
| --- | --- | --- | --- |
| SO VỚI CÔNG BỐ | `paper` | `test` | `metrics.json::scores_paper`, `metrics.csv` (basis=`paper`) |
| CHỌN `model/best` / dừng sớm / vẽ curve | `all` | `val` | `training_history.csv`, khối `training` của `metrics.json` |

KHÔNG đem số `all` đi so công bố, và KHÔNG đưa chỉ số chọn-best (val) vào bảng `metrics_matrix`.

### Rescore là CHẤM THÊM, không ghi đè

`scripts/rescore.py --dir <results/<hash8>>` đọc `predictions.csv` rồi ghi `metrics_rescored.json` /
`metrics_rescored.csv`; `metrics.json`/`metrics.csv` của lượt chạy KHÔNG bị chạm tới. Bảng
`metrics_matrix` hiển thị HAI họ cột `(gốc)` / `(rescored)` khi lượt đó có rescore - không trộn hai
nguồn trong cùng một ô.

### Một phép đo = MỘT run MLflow

`run_meta.json` giữ `tracking.run_id`; phiên chạy tiếp (RESUME) NỐI vào đúng run đó thay vì mở run
mới. Tham số phẳng gửi ngay khi biết; phần SỐ của cấu trúc lớn (`read_rate`, `cost`, `resume`) đi qua
metric (không bị giới hạn 500 ký tự như param). Số cơ sở `paper` lên MLflow với tiền tố `paper.`; run
tham chiếu công bố do `scripts/log_reference_run.py` ghi (chạy tay khi có mạng).

### Ma trận nhầm ở artifact, không lên MLflow

`confusion` chỉ nằm trong `metrics.json` (khoá `tables.confusion`) và `plots/accuracy.html`; đưa lên
MLflow thì `numeric()` làm phẳng thành hàng trăm metric rời và mất dạng ma trận.

### Chống mất cân bằng

`loss.type: weighted_ce` + `loss.class_weight: inverse` (nghịch đảo tần suất, chuẩn hoá trung bình 1)
là TUỲ CHỌN trong config. Đổi loss đổi `config_sha256` nên ra **thư mục kết quả mới** - kết quả cũ
không bị ghi đè.

### Hoãn có chủ ý

**Optuna** (tìm siêu tham số) hoãn một nhịp: objective/loss vừa đổi, tối ưu sớm là tối ưu nhầm.
**focal loss / trọng số theo khía cạnh** làm sau khi curve cho thấy lớp hiếm bị bỏ. Chi tiết ở backlog.
