# Kế hoạch Đợt 13 — số epoch + early stop · Optuna · lô suy luận LLM · dữ liệu v0.3.0

> File này GIỮ KẾ HOẠCH của đợt 13 (chốt 13/10/2026). Nhật ký chạy ghi DẦN vào đây.
> Liên quan: `present_plan_batch12.md` (đợt 8–12), `presentations/present_report/present_report_v3.md`
> (bảng số đang dùng), `docs/04_experiments/07_evolution.md`, `docs/04_experiments/04_backlog.md` §9.1.

## A. Mục tiêu (định lượng) và BẢNG ĐÍCH

**Mục tiêu (người dùng chốt):** tăng `Accuracy macro` **và/hoặc** `neg F1 macro (5 khía cạnh n lớn)`,
**không được giảm cái còn lại**; tốt nhất tăng cả hai; **ưu tiên khía cạnh có `n` lớn** — hiện tại
P/R/F của dự án ở nhóm đó còn thấp.

**Công thức đạt** (trên **3 seed độc lập**, so với họ `lr 4e-4` hiện tại có mean `Accuracy macro` = **98,283**):
- `Δ Accuracy macro ≥ 0` **và** `Δ neg F1 macro (5 khía cạnh n lớn) ≥ 0`, **ít nhất một cái > 0**;
- "không giảm" = mức giảm **≤ 0,2 pp** (nằm trong nhiễu);
- "có ý nghĩa" ⟺ vượt **> 0,7 pp** (biên nhiễu 1 lượt) **và** **Welch p < 0,05** (nhiều lượt);
- **bắt buộc khai** Δ cho **từng khía cạnh `n` lớn** ở cả **P / R / F1**.

**Bảng ĐÍCH — ô dự án còn DƯỚI công bố ở khía cạnh `n` lớn** (công bố = cột COT+1-shot; dự án = tốt
nhất trong 10 lượt của `present_report_v3`):

| Khía cạnh | Sắc thái | Chỉ số | Công bố | Dự án tốt nhất | Khoảng cách |
|---|---|---|---:|---:|---:|
| **texture** | negative | P | 100,00 | 95,2 | **−4,8** |
| **texture** | negative | F1 | 100,00 | 95,9 | **−4,1** |
| **texture** | negative | R | 100,00 | 98,6 | −1,4 |
| **texture** | positive | R | 100,00 | 98,8 | −1,2 |
| **texture** | positive | F1 | 100,00 | 99,0 | −1,0 |
| **texture** | positive | P | 100,00 | 99,6 | −0,4 |
| **smell** | negative | **R** | 100,00 | 97,9 | **−2,1** |
| **shipping** | negative | **R** | 100,00 | 98,8 | **−1,2** |
| shipping | positive | P | 100,00 | 99,4 | −0,6 |
| shipping | positive | F1 | 99,21 | 99,0 | −0,21 |
| shipping | negative | F1 | 98,11 | 98,1 | −0,01 |
| smell | positive | P | 100,00 | 99,6 | −0,4 |

⇒ **Đích số 1 = `texture`** (6 ô, sâu nhất −4,8). **Đích số 2 = Recall lớp `negative` của `smell` (−2,1)
và `shipping` (−1,2).** Công bố có **R = 100,00 ở CẢ 5 khía cạnh `n` lớn** ⇒ **Recall là trục yếu chung**.
`colour` và `stayingpower`: **đã đạt/vượt ở mọi ô**.

**Lever đã CẠN (đừng thử lại):** `focal` (`exp017` 93,94 · `exp024/025` < cha) · `inverse_by_aspect` trên nền
2e-4 (`exp018` 92,40) · `DoRA` (`exp019` 92,96) · `dropout 0` (`exp030` 94,62) ·
`best_metric: negative_f1` (`exp055/056/057` = 94,06/93,72/94,44 — **đều kém**) ·
**ngưỡng theo khía cạnh** (`data/reports/fusion/thresholds.json`: cả 6 khía cạnh chốt ngưỡng `0,95` với
`f1_âm_gốc == f1_âm_sau` ⇒ **rỗng**) · ensemble/biểu quyết/router/gộp-hai-tầng (âm/rỗng) ·
`segmenter: vncorenlp` (không tái lập).

## B. Đợt 13.0 — Việc NỀN (không tốn GPU)

1. **`early_stop.min_delta` phải dùng THẬT.** Code hiện chỉ so `value > best` (`src/training/lora.py`
   L972, L1042) nên `min_delta` **chỉ xuất hiện trong câu log** (L1046, L1074). Với val nhiễu ±0,02-0,07
   thì `stale` bị reset liên tục ⇒ **early stop không bao giờ chạy**. Sửa thành `value > best + min_delta`
   + test.
2. **Thêm chỉ số `neg_f1_big5`** — gộp TP/FP/FN trên **5 khía cạnh `n` lớn** (`colour · shipping · smell ·
   stayingpower · texture`), thêm vào `MEASURED_METRICS` ⇒ dùng được làm `checkpoints.best_metric`.
   Lý do: `sentiment_f1` bị `price`/`packing` chi phối, và `negative_f1` (gộp 7 khía cạnh) **cũng** bị
   (đúng bẫy luật 13 của `docs/04_experiments/metrics.md`). + test.
3. **Ghi `stopped_early` + số epoch thực chạy** vào `metrics.json` (hiện chỉ có trong `run.log`).
4. **`optuna`** vào `requirements.txt` (**KHÔNG** vào `requirements-ci.txt`); **import trong hàm**.
5. CI xanh. *(Chốt **Cách A**: KHÔNG đổi lịch lr; confound `epochs ↔ lịch lr` khai rõ trong `notes`.)*


## C. Các đợt CHẠY (mỗi đợt thiết kế đúng **15 slot** để dùng hết 1 phiên Colab)

### Đợt 13.1 — "số epoch + early stop" — **15 slot = 5 nhánh × 3 seed** (seed `42`, `7`, `13`)

| Nhánh | Cha | Nhóm khoá thay đổi (1 nhóm/cha) | Mục đích |
|---|---|---|---|
| **B1** | `exp015` (lr 4e-4, r16, 3 epoch) | `epochs: 15` + `early_stop {enabled: true, patience: 12 (≈3 epoch), min_delta: 0,002}` | trả lời "underfit có thật không" |
| **B2** | `exp021` (lr 4e-4, r8) | như B1 | nhánh dẫn đầu |
| **B3** | `exp028` (r16, `every_n_steps` 50) | `epochs: 15` + `early_stop {true, patience: 24 (≈3 epoch), min_delta: 0,002}` | nền giữ kỷ lục `neg F1 big5` = 94,84 |
| **B4** | **B1** (tạo trước trong cùng đợt) | + `checkpoints.best_metric: neg_f1_big5` | **chọn mốc theo ĐÚNG đích** |
| **B5** | **B1** | + `loss.class_weight: inverse_by_aspect` | **hồi sinh `exp036`** trên nền lr 4e-4 + early stop, nhắm `texture` |

Giữ nguyên mọi thứ khác: `batch 8` · `grad_accum 4` · `alpha 32` · `lora_dropout 0,05` ·
`weight_decay 0,01` · `max_length 256` · `loss.type weighted_ce` · `every_n_steps 100` (B1/B2/B4/B5).
Lưu ý `patience` đếm **lần ĐO** chứ không đếm epoch: `every_n_steps 100` ⇒ ~3,84 lần đo/epoch; `every_n_steps 50` ⇒ ~7,69.

Chi phí: ~1,6 s/bước × 5.760 bước ≈ **2,5 h/lượt nếu không dừng sớm**, ~1-1,5 h nếu early stop cắt ở epoch 5-8
⇒ **cả 15 chạy song song ≈ 2,5-3 h wall clock (1 phiên)**. Không cần chạy lại đối chứng: họ `lr 4e-4`
**đã có 12 lượt** trên đĩa (mean 98,283).

### Đợt 13.2 — Chốt / đào sâu (≤15 slot, chỉ chạy khi 13.1 có nhánh đạt)
- Nhánh thắng: **thêm 6 seed** (n = 9) để hạ Welch p.
- Nếu nhánh thắng là B4/B5: chạy thêm **B1 với đúng 6 seed đó** để so cặp sạch.
- **Nếu không nhánh nào đạt: ĐÓNG trục `epochs`**, ghi bằng chứng **n = 3** (thay kết luận cũ chỉ dựa 1 lượt `exp027`).

### Đợt 13.3 — Optuna trên MÁY CÁ NHÂN (0 slot Colab, 1-2 ngày)
- **Đa mục tiêu NSGA-II: (`accuracy_macro`, `neg_f1_big5`) trên `val`** — đọc **Pareto front**, không lấy 1 điểm.
- `n` nhỏ cố định trên `val` (500 mẫu) để mỗi trial ~5-8 phút; `batch 4 × grad_accum 8` cho vừa VRAM 6 GB
  (giữ effective batch = 32).
- Không gian: `lr` log-uniform 1e-4…1e-3 · `lora.r` {4,8,16,32,64} · `alpha` {8,16,32,64,128} ·
  `dropout` {0, 0.05, 0.1, 0.2} · `weight_decay` {0, 0.01, 0.05, 0.1} ·
  `class_weight` {inverse, none, inverse_by_aspect} · `use_dora` {false,true} · `head.trainable` {true,false} ·
  `max_length` {192,256,320,384} · `epochs` {3…8} + early stop · `best_metric` {sentiment_f1, neg_f1_big5}.
- **Chống thiên lệch:** chỉ chọn trên **`val`**, KHÔNG chạm `test`; chọn-best-of-N bị thiên lệch LÊN nên kết
  luận chỉ đến từ Đợt 13.4. Dừng khi 30 trial liên tiếp không cải thiện > 0,1 pp.

### Đợt 13.4 — Xác nhận ứng viên Optuna trên Colab (9 slot)
- Lấy **3 điểm** trên Pareto front (nghiêng `accuracy_macro` · nghiêng `neg_f1_big5` · cân bằng) × **3 seed**.
- Chạy **full 1623** `test`, `batch 8 × grad_accum 4` đúng chuẩn. So incumbent bằng **Welch**.

### Đợt 13.5 — LLM: lô suy luận (DÒ 3 slot → full 1-2 slot)
- **DÒ (3 slot):** cùng **200 review cố định**, 3 lượt: `batch 4` (đối chứng) · `batch 2` · `batch 1`.
  Đo **lệch ô so với batch 4** và **Δ Accuracy macro**. ≈ 1,7 h.
- **Chạy full 1623 CHỈ KHI** lệch **> 0,5 pp** HOẶC **> 2 % ô**. Full: batch 2 ≈ 4-5 h, batch 1 ≈ 7-11 h
  (dùng **RESUME**; ngắt ở tầng ĐÁNH GIÁ thì áp **luật 15** và khai số ô tái dùng).
- Dưới ngưỡng ⇒ **đóng trục batch**, ghi "batch không phải siêu tham số có ý nghĩa với L1".

### Đợt 13.6 — `exp034`: dữ liệu `v0.3.0` (3 seed = 3 slot) — **CHỐT: bảng CHÍNH kèm chú thích**
- Cấu hình = **nhánh thắng của 13.1** (hoặc `exp015` nếu chưa có nhánh thắng), chỉ đổi `data.version: v0.3.0`.
- `test` **y đúc** v0.2.0/raw 0.1.0 (đã kiểm từng ký tự) nên số so được; **rule 14** đòi cùng phiên bản dữ
  liệu cho bảng chính, nên `exp034` **vào BẢNG CHÍNH** kèm chú thích cố định:
  *"train/val khác phiên bản dữ liệu (v0.3.0 bỏ emoji); `test` y đúc v0.2.0"* — người dùng đã chốt.

### Đợt 13.7 — Nếu thắng: đẩy lên n = 9 cho kết luận (≤15 slot)
Chỉ để hạ p < 0,05 trên nhánh cuối cùng thắng; KHÔNG mở trục mới.

## D. Bảng tổng hợp đợt

| Đợt | Việc | Slot Colab | Thời gian | Cho ra cái gì |
|---|---|---|---|---|
| **13.0** | Sửa code: `min_delta` dùng thật · thêm `neg_f1_big5` · log `stopped_early` · `optuna` vào requirements · CI xanh | 0 | ~0,5 ngày | Điều kiện để mọi đợt sau có nghĩa |
| **13.1** | Epochs 15 + early stop, 5 nhánh × 3 seed | 15 | ~3 h | Trả lời `underfit`; nhánh `neg_f1_big5`; hồi sinh `exp036` |
| **13.2** | +6 seed cho nhánh thắng *(hoặc đóng trục)* | ≤15 | ~3 h | Welch p < 0,05 |
| **13.3** | Optuna NSGA-II trên máy cá nhân | 0 | 1-2 ngày | Pareto front trên `val` |
| **13.4** | 3 ứng viên Pareto × 3 seed, full test | 9 | ~3 h | Kết luận HPO (Welch) |
| **13.5** | LLM: DÒ batch 4/2/1 → (tuỳ) full | 3 → +1-2 | 2 h → 5-11 h | Đóng/mở trục batch |
| **13.6** | `exp034` dữ liệu `v0.3.0` × 3 seed | 3 | ~2-3 h | Lever dữ liệu duy nhất còn lại |
| **13.7** | n = 9 cho nhánh cuối | ≤15 | ~3 h | Chốt thống kê |

**Tổng: ~4-6 phiên Colab (~3 h/phiên) + 1-2 ngày máy cá nhân.**

## E. Luật áp dụng (không đổi)

Mỗi lượt = 1 thí nghiệm qua `scripts/new_experiment.py`, khác cha **1 khoá/nhóm khoá** · `merge` vào
`experiment` rồi **chạy lại trên `experiment`** nếu merge phải sửa file · **CI xanh trước `pin.py`** ·
ghim `REPO_SHA` rồi mới gửi gói · `collect_reports.py` sau khi có kết quả ·
**rule 14** (cùng bài toán + cùng `v0.2.0`; `exp034` khác ⇒ vào bảng chính **kèm chú thích**) ·
đọc lớp `negative` bằng **hai thước đo có `n`**, KHÔNG bằng `macro (7)` ·
**n đếm theo seed**, không đếm thư mục.

## F. Rủi ro & cách chặn

| Rủi ro | Chặn |
|---|---|
| Early stop không chạy vì `min_delta` chưa dùng | **13.0.1 — XONG**: `lora.is_improved` + 4 test mới |
| `patience` bị hiểu nhầm là epoch (nó đếm LẦN ĐO) | Ghi rõ trong `notes` từng lượt: B1/B2/B4/B5 `patience 12 ≈ 3 epoch`; B3 `patience 24 ≈ 3 epoch` |
| Tăng epoch kèm đổi lịch lr (confound) | **Cách A** đã chốt ⇒ khai rõ trong `notes` + báo cáo |
| Optuna "tune trên test" | Mục C.13.3 — chỉ `val`; kết luận từ 13.4 |
| Colab ngắt giữa 15 tab | RESUME theo `predictions/part_*.jsonl`; luật 15 cho ngắt tầng ĐÁNH GIÁ |
| Chi phí vượt ngân sách | 13.2/13.4 "không đạt thì đóng trục"; 13.5 "dưới ngưỡng thì đóng" |

## G. Chốt của người dùng (13/10/2026)

1. **ĐỒNG Ý** thêm chỉ số `neg_f1_big5` làm `best_metric` ⇒ Đợt 13.1 giữ đủ **5 nhánh** (B4 là nhánh mới).
2. **`exp034` vào BẢNG CHÍNH kèm chú thích** "train/val khác phiên bản dữ liệu (v0.3.0 bỏ emoji); `test` y đúc v0.2.0".
3. **Cách A** cho confound `epochs ↔ lịch lr`: giữ nguyên lịch, khai rõ trong `notes`/báo cáo.
4. **15 slot Colab song song** ⇒ mỗi đợt thiết kế đúng 15 lượt, chạy thẳng 3 seed (trừ Đ3 vì rất đắt/lượt).

## H. Nhật ký chạy

### 13.0 — Việc nền (XONG 13/10/2026)

| Việc | Kết quả |
|---|---|
| 1. `min_delta` dùng thật | `src/training/lora.py`: thêm `is_improved(value, previous, min_delta)`; `record()` dùng nó cho CẢ `model/best` lẫn con đếm `stale` |
| 2. Chỉ số `neg_f1_big5` | `lora.BIG_ASPECTS` + `neg_f1_big5_of()`; thêm vào `measure()` và `MEASURED_METRICS` ⇒ dùng được làm `checkpoints.best_metric` |
| 3. Epoch thực + dừng sớm vào `metrics.json` | `fit_generic` trả `epochs_run`/`stopped_early`; `encoder_run.py` ghi vào `cost` (`epoch đã chạy`, `dừng sớm`) + `[STEP] dừng sớm ở epoch …` |
| 4. `optuna` | `requirements.txt` (không vào `requirements-ci.txt`; import trong hàm khi viết script HPO) |
| 5. Test + CI | +9 test mới (`EarlyStopImprovementTest`, 5 test `neg_f1_big5`) ⇒ **1129 test**, CI tĩnh SẠCH |
| 6. Tài liệu | `configs/experiments/training.yaml` · `docs/05_config/05_experiments_shared.md` · `docs/04_experiments/06_lora_encoder.md` · `docs/04_experiments/07_evolution.md` |

**Bằng chứng test:** `python -m unittest discover -s tests` → 1129 test, **1 lỗi CÓ SẴN** (không do đợt này):
`tests/training/test_full.py::test_every_parameter_is_trainable` — đã đối chứng bằng cách `git stash` 5 tệp
đã sửa rồi chạy lại: bản gốc **1120 test cũng lỗi đúng bài đó** (lỗi phụ thuộc thứ tự chạy; chạy riêng bài đó thì OK).
`python scripts/ci_checks.py` → "Không có việc nào phải sửa."

### 13.1 — ĐÃ TẠO + GHIM (13/10/2026), chờ chạy trên Colab

15 lượt = **5 nhánh × 3 seed**, `cafebert/lora/exp064` … `exp078`, ghim commit **`8f4eb49`**:

| Nhóm | Lượt (seed 42 · 7 · 13) | Cha | Biến của nhóm |
|---|---|---|---|
| **B1** | `exp064` · `exp065` · `exp066` | `exp015` (lr 4e-4, r16) | `epochs 15` + `early_stop {enabled, patience 12, min_delta 0,002}` |
| **B2** | `exp067` · `exp068` · `exp069` | `exp021` (lr 4e-4, r8) | như B1 |
| **B3** | `exp070` · `exp071` · `exp072` | `exp028` (r16, `every_n_steps 50`) | như B1, `patience 24` (đo ~2 lần/epoch) |
| **B4** | `exp073` · `exp074` · `exp075` | **`exp064`** (B1 seed 42) | + `checkpoints.best_metric: neg_f1_big5` |
| **B5** | `exp076` · `exp077` · `exp078` | **`exp064`** (B1 seed 42) | + `loss.class_weight: inverse_by_aspect` |

**Bằng chứng "khác cha ĐÚNG một khoá/nhóm khoá"** — lấy bằng chính bộ nạp config của dự án
(`_scratch/check_d13.py` in ra `d:\TrieuKhac\Documents\SentimentX\_scratch\d13_check.txt`):

| Lượt | Số khoá khác cha | Khoá khác |
|---|---|---|
| `exp064` `exp067` `exp070` | 4 (MỘT nhóm) | `epochs` 3→15 · `early_stop.enabled` · `.patience` · `.min_delta` |
| các lượt seed 7/13 (10 lượt) | 1 | `decoding.seed` (`null` → 7 / 13) |
| `exp073` (B4 seed 42) | 1 | `checkpoints.best_metric` `sentiment_f1` → `neg_f1_big5` |
| `exp076` (B5 seed 42) | 1 | `loss.class_weight` `inverse` → `inverse_by_aspect` |

Mọi lượt giữ: `data.version v0.2.0` · `roles {train,val,test}` · `head.trainable true` · `lr 0.0004` ·
`max_length 256` · `batch 8 × grad_accum 4`; B3 giữ `every_n_steps 50`, các nhánh khác 100.

Đã làm: tạo config + notebook bằng `scripts/new_experiment.py` (`_scratch/make_d13.py`, có tự-kiểm YAML)
→ commit `8f4eb49` → **push** → `scripts/pin.py` cả 15 (`REPO_SHA` = `8f4eb49714eee261c60458cb6425fc872d94e97c`)
→ `ci_checks.py` SẠCH (9/9 mục) → gói bàn giao **035**.

**Bước tiếp (người dùng):** chạy 15 notebook song song trên Colab (~2,5-3 h) → trả kết quả về → chấm
`collect_reports.py` → đọc theo luật ở mục C (Đợt 13.1) và `handover/README.md`.



