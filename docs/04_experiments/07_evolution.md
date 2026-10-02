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

---

## Cây tính tới 02/10/2026 - chín lượt có kết quả

Bốn nhánh, ba hướng câu hỏi khác nhau: hai encoder học LoRA (nhóm A), Qwen3-4B hỏi bằng prompt (nhóm B và C,
tái hiện công bố), và một biến về QUY MÔ model (nhóm D). Số dưới đây là cơ sở `paper` trên split `test`,
đọc từ `data/reports/metrics_matrix/`; câu hỏi và điểm riêng của từng lượt ở
`docs/04_experiments/08_experiment_rationale.md`.

```
qwen3-4b-instruct-2507/prompt-cot/exp002   <- (gốc nhóm prompt)      đúng mức COT+0-shot của công bố
    Kết quả: acc TB khía cạnh 97,16 · F1 sắc thái macro 0,895 · khớp hoàn toàn 96,12%
    Kết luận: GIỮ - mốc gốc của nhóm, và là bản 4-bit để đo lượng hoá ở exp005

qwen3-4b-instruct-2507/prompt-cot/exp003   <- (gốc nhóm prompt)      mức COT+1-shot của công bố
    Kết quả: 97,72 · 0,926 · 97,23%   (cao nhất trong chín lượt)
    Kết luận: GIỮ - cấu hình tốt nhất hiện có, hơn công bố ở mức 1 ví dụ

qwen3-4b-instruct-2507/prompt-cot/exp004   <- (gốc nhóm prompt)      mức COT+5-shot của công bố
    Kết quả: 97,11 · 0,902 · 95,87%   (đọc được 99,88%; 63 ô hỏng định dạng)
    Kết luận: GIỮ - nhưng thêm ví dụ KHÔNG tăng điểm so với exp003

qwen3-4b-instruct-2507/prompt-cot/exp005   <- exp002                 lượng hoá 4-bit mất bao nhiêu - mức 0 ví dụ
    Kết quả: 96,62 · 0,896 · 95,32%   (bản KHÔNG lượng hoá thấp hơn bản 4-bit 0,54 điểm)
    Kết luận: GIỮ - chưa tách được biến vì batch_size đổi 8 sang 4 (08 §3)

qwen3-4b-instruct-2507/prompt-cot/exp006   <- exp003                 cùng câu hỏi ở mức 1 ví dụ
    Kết quả: 96,60 · 0,909 · 95,87%   (thấp hơn bản 4-bit 1,12 điểm)
    Kết luận: GIỮ - cùng hạn chế về batch

qwen3-4b-instruct-2507/prompt-cot/exp007   <- exp004                 cùng câu hỏi ở mức 5 ví dụ
    Kết quả: 96,48 · 0,899 · 95,07%   (thấp hơn bản 4-bit 0,63 điểm; lâu nhất: 13.833 giây)
    Kết luận: GIỮ - cùng hạn chế về batch

qwen3-4b-instruct-2507/prompt-one-turn/exp001  <- (gốc)               bỏ suy luận từng bước thì mất bao nhiêu
    Kết quả: 95,33 · 0,871 · 93,04%   (thấp hơn CoT 0 ví dụ 1,83 điểm)
    Kết luận: GIỮ - bằng chứng CoT có tác dụng thật, không chỉ tốn token

visobert/lora/exp001                       <- (gốc)                  encoder học LoRA - đọc nguyên bản, không tách từ
    Kết quả: 94,86 · 0,765 · 92,54%   (phát hiện khía cạnh tốt nhất: F1 macro 0,966)
    Kết luận: GIỮ - mất điểm ở lớp TIÊU CỰC: colour 0,50 · price 0 · packing 0

phobert-base-v2/lora/exp001                <- (gốc)                  encoder học LoRA - tách từ vncorenlp
    Kết quả: 88,40 · 0,540 · 85,83%   (stayingpower 64,71 - thấp nhất bảng)
    Kết luận: GIỮ làm mốc ĐỐI CHỨNG - gần như không đoán được lớp âm (F1 âm = 0 ở 5/7 khía cạnh)

qwen3-0.6b/prompt-cot/exp001..003          <- (gốc)                  model nhỏ hơn ~7 lần thì kém bao nhiêu
    Kết quả: KHÔNG DÙNG - ba lượt nạp nhầm trọng số 4B (metrics.model = Qwen/Qwen3-4B-Instruct-2507;
              số token sinh trùng khít exp005/006/007). Kết quả đã xoá 02/10/2026.
    Kết luận: ĐỔI HƯỚNG - nhóm D thành việc KẾ TIẾP, sau khi sửa cách chọn checkpoint
              (`run_model` đọc khoá `hf_model` không config nào khai, nên rơi về mặc định 4B)
```

Đọc cây này kèm `04_backlog.md` (việc chưa làm) và `08_experiment_rationale.md` (câu hỏi của từng lượt).
Nhánh D không có nút kết quả vì ba lượt đó không đo model 0.6B; xem `08_experiment_rationale.md` §5.
