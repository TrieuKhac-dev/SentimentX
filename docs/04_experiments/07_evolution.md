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

## Cây tính tới 04/10/2026 - mười bảy lượt có kết quả

Sáu nhánh: hai encoder học LoRA (nhóm A, 4 lượt), Qwen3-4B hỏi bằng prompt ở ba mức ví dụ với ba cấu
hình (nhóm B: `exp002-004` 4-bit lô 8; `exp005-007` fp16 lô 4; `exp008-010` 4-bit lô 4), ba biến thể
prompt 1 ví dụ (nhánh E: `exp011-013`), một biến về CÁCH HỎI (nhánh F: một lượt, bỏ suy luận), và một
biến về QUY MÔ model (nhánh G: 0.6B, CHƯA có kết quả). Số dưới đây là cơ sở `paper` trên split `test`,
đọc từ `data/reports/metrics_matrix/`; câu hỏi và điểm riêng của từng lượt ở
`docs/04_experiments/08_experiment_rationale.md`.

**Cập nhật 05/10/2026:** cây này là bản chụp **17 lượt CÓ kết quả**. Ngoài ra đã tạo **6 lượt ablation đầu
phân loại** (CHƯA chạy - xem §2b của `08_experiment_rationale.md`) và registry nay có **sáu** encoder chứ
không phải hai; nhóm mới chưa có số nên không nằm dưới đây.

```
qwen3-4b-instruct-2507/prompt-cot/exp002   <- (gốc nhóm prompt)      đúng mức COT+0-shot của công bố
    Kết quả: acc TB khía cạnh 97,16 · F1 sắc thái macro 0,895 · 2.415 ô
    Kết luận: GIỮ - mốc gốc của nhóm

qwen3-4b-instruct-2507/prompt-cot/exp003   <- (gốc nhóm prompt)      mức COT+1-shot của công bố
    Kết quả: 97,72 · 0,926 · 2.315 ô
    Kết luận: GIỮ - mốc 1 ví dụ, hơn công bố 0,02 điểm

qwen3-4b-instruct-2507/prompt-cot/exp004   <- (gốc nhóm prompt)      mức COT+5-shot của công bố
    Kết quả: 97,11 · 0,902 · 2.378 ô   (đọc được 99,88%; chạy TIẾP, dùng lại 1.304 mẫu)
    Kết luận: GIỮ - nhưng thêm ví dụ KHÔNG tăng điểm so với exp003

qwen3-4b-instruct-2507/prompt-cot/exp005   <- exp002                 fp16 + lô 4 - mức 0 ví dụ
    Kết quả: 96,62 · 0,896 · 2.580 ô
    Kết luận: GIỮ - đối chứng lượng hoá cho exp008

qwen3-4b-instruct-2507/prompt-cot/exp006   <- exp003                 fp16 + lô 4 - mức 1 ví dụ
    Kết quả: 96,60 · 0,909 · 2.461 ô
    Kết luận: GIỮ - đối chứng lượng hoá cho exp009

qwen3-4b-instruct-2507/prompt-cot/exp007   <- exp004                 fp16 + lô 4 - mức 5 ví dụ
    Kết quả: 96,48 · 0,899 · 2.520 ô   (lâu nhất trong 17 lượt: 13.833 giây)
    Kết luận: GIỮ - đối chứng lượng hoá cho exp010

qwen3-4b-instruct-2507/prompt-cot/exp008   <- exp002                 4-bit + lô 4 - mức 0 ví dụ
    Kết quả: 97,26 · 0,894 · 2.414 ô   (hơn exp005 0,64 điểm, nhưng bớt 166 ô)
    Kết luận: GIỮ - nửa đầu của phép so lượng hoá SẠCH MỘT BIẾN

qwen3-4b-instruct-2507/prompt-cot/exp009   <- exp003                 4-bit + lô 4 - mức 1 ví dụ
    Kết quả: 97,77 · 0,928 · 2.324 ô   (hơn exp006 1,17 điểm, nhưng bớt 137 ô)
    Kết luận: GIỮ - ĐỈNH của 17 lượt, hơn công bố 0,07 điểm (nằm trong nhiễu một lần chạy greedy)

qwen3-4b-instruct-2507/prompt-cot/exp010   <- exp004                 4-bit + lô 4 - mức 5 ví dụ
    Kết quả: 97,19 · 0,907 · 2.375 ô   (hơn exp007 0,71 điểm; chạy TIẾP, 411,3 giây)
    Kết luận: GIỮ - cùng chiều với hai lượt trên

qwen3-4b-instruct-2507/prompt-cot/exp011   <- exp003                 ví dụ 1 có NHÃN ÂM (texture/stayingpower/packing)
    Kết quả: 97,63 (kém exp003 0,09) · 0,902 · 2.359 ô · F1 `price` âm 0,308 (exp003: 0,600)
    Kết luận: BỎ - sửa VÍ DỤ không giúp, còn làm `price` âm tệ đi

qwen3-4b-instruct-2507/prompt-cot/exp012   <- exp003                 thêm bước 0 "quét mọi lời phàn nàn"
    Kết quả: 96,52 (kém 1,20) · 0,908 · 2.305 ô · F1 `price` âm 0,600
    Kết luận: BỎ - thêm quy trình dài vào CÂU CHỮ prompt không giúp

qwen3-4b-instruct-2507/prompt-cot/exp013   <- exp003                 thêm "lưu ý dữ liệu lệch nhãn"
    Kết quả: 92,66 (kém 5,06) · 0,842 · 1.972 ô   (mất 343 ô) · F1 `price` âm 0,167
    Kết luận: BỎ - lời nhắc lệch nhãn làm model kiêng trả lời, hại cả điểm lẫn số ô

qwen3-4b-instruct-2507/prompt-one-turn/exp001  <- (gốc)               bỏ suy luận từng bước thì mất bao nhiêu
    Kết quả: 95,33 · 0,871 · 2.663 ô   (kém CoT 0 ví dụ 1,83 điểm)
    Kết luận: GIỮ - bằng chứng CoT có tác dụng thật, không chỉ tốn token

phobert-base-v2/lora/exp001                <- (gốc)                  encoder + tách từ vncorenlp, học LoRA gốc
    Kết quả: 88,40 · 0,540 · 2.665 ô   (stayingpower 64,71 - thấp nhất bảng)
    Kết luận: GIỮ làm mốc ĐỐI CHỨNG

phobert-base-v2/lora/exp002                <- exp001                 chỉ thêm `weighted_ce` + `inverse`
    Kết quả: 96,62 (+8,22 điểm) · F1 macro 0,876 (+0,336) · 2.736 ô · `price` âm vẫn 0,00
    Kết luận: GIỮ - SỬA BẰNG HỌC là hướng hiệu quả nhất của dự án

visobert/lora/exp001                       <- (gốc)                  encoder đọc nguyên bản, không tách từ
    Kết quả: 94,86 · 0,765 · 2.688 ô   (phát hiện khía cạnh tốt nhất: F1 macro 0,966)
    Kết luận: GIỮ - mất điểm ở lớp TIÊU CỰC: colour 0,50 · price 0 · packing 0

visobert/lora/exp002                       <- exp001                 chỉ thêm `weighted_ce` + `inverse`
    Kết quả: 95,61 (+0,75 điểm) · F1 macro 0,836 (+0,071) · 2.701 ô
    Kết luận: GIỮ - cùng cơ chế nhưng lợi ít hơn hẳn; ĐẢO THỨ HẠNG hai encoder

qwen3-0.6b/prompt-cot/exp001..003          <- (gốc)                  model nhỏ hơn ~7 lần thì kém bao nhiêu
    Kết quả: KHÔNG DÙNG - đã chạy HAI lần, hỏng HAI kiểu khác nhau:
              (1) `8db40559`/`db6efb02`/`30c9e674` nạp NHẦM trọng số 4B (metrics.model =
                  Qwen/Qwen3-4B-Instruct-2507; số ô 2.580/2.461/2.520 trùng khít exp005/006/007);
              (2) `bc32904d`/`edc0797a`/`d5b8e7fc` đúng 0.6B nhưng BẬT SUY NGHĨ ăn hết trần 400 token
                  (đọc được 3,33/1,36/1,73%; `<think>` 999/714/788 lần). Cả sáu xoá 04/10/2026.
    Kết luận: ĐỔI HƯỚNG - chạy lại với `preprocess.enable_thinking: false`; lượt bật suy nghĩ thành
              nhánh RIÊNG, có bước DÒ (`exp004`) chốt trần token trước khi chạy đầy đủ
```

Đọc cây này kèm `04_backlog.md` (việc chưa làm) và `08_experiment_rationale.md` (câu hỏi của từng lượt).
Nhánh G (0.6B) chưa có nút kết quả vì cả sáu thư mục cũ đều không dùng được; xem
`08_experiment_rationale.md` §5.
