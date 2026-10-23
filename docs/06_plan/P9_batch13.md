# P9 - Bàn giao thi hành Đợt 13.2 → 13.6 (sau 14/10/2026)

> Đọc file này khi: bạn là **người tiếp nhận** việc sau ngày **14/10/2026** và phải làm nốt **Đợt 13**.
> Nguồn gốc: `docs/06_plan/archive/batches/present_plan_batch13.md` (kế hoạch đợt 13, mục A–H) ·
> `presentations/present_report/present_report_v3.md` (bảng số đang dùng của báo cáo).
>
> **Trạng thái:** Đợt **13.0** và **13.1** ĐÃ XONG và đã đẩy lên `origin/experiment` (mục 2).
> Phần còn lại là mục **4 → 6** của file này: Bước 2 (thêm chỉ số, 0 GPU) · Bước 3 (tạo 15 lượt, 0 GPU) ·
> Bước 4 (chạy Colab + đọc số) · rồi 13.3 → 13.6 (mục 8).

## 1. Bắt buộc đọc trước (5 phút)

**Dự án làm gì:** ABSA tiếng Việt trên dữ liệu mỹ phẩm: 7 khía cạnh, mỗi khía cạnh 1 trong 3 nhãn
`positive` / `negative` / `không nhắc tới`. Đường đang dẫn là **encoder CafeBERT + LoRA**, chấm trên split
`test` (1.623 review, 11.161 ô). Đích của đợt 13: **tăng `Accuracy macro` VÀ `neg F1 (5 khía cạnh `n` lớn)`
mà không làm giảm cái còn lại**.

**Bảy luật của repo, không được vi phạm:**

1. **Một task = một commit**, Conventional Commits **tiếng Anh** (`type(scope): subject`), tiêu đề ≤ 72 ký tự.
2. Sau mỗi nhóm việc chạy **cả hai** lệnh, **cả hai phải xanh**:
   `python scripts/ci_checks.py` và `python -m unittest discover -s tests`
   (Windows: đặt `$env:PYTHONUTF8=1`).
3. **Không sửa notebook đã ghim** (`experiments/**/notebook.ipynb`). Muốn có hiệu lực: tạo lượt mới rồi ghim lại.
4. **Không hardcode** đường dẫn/giá trị; **không đặt mặc định trong code** (thiếu khoá ⇒ báo lỗi rõ).
5. Cặp `configs/prompts/<tên>.txt` + `examples/<tên>.txt` đã dùng là **bất biến**; `test` **không được sửa**.
6. Tệp `.md` ghi **không BOM**; văn bản tiếng Việt ghi bằng công cụ sửa tệp (đừng dùng here-string PowerShell).
7. **Mọi thay đổi so với kế hoạch phải được người dùng đồng ý trước.** Việc gì phát sinh thì **báo cáo**,
   không tự ý đổi.

**Lỗi test CÓ SẴN (đừng đi tìm cách sửa, đừng coi là hỏng):**
`tests/training/test_full.py::test_every_parameter_is_trainable` — khi chạy **cả bộ** (1129 test) thì báo
`errors=1`; đã đối chứng bằng `git stash` trên cây sạch: **bản gốc cũng lỗi đúng bài đó** (phụ thuộc thứ tự
chạy; chạy riêng bài đó thì qua). Ngoài bài đó ra, mọi test phải qua.

**Hai cơ sở đo, đừng lẫn (đây là bẫy đã có luật):**

| Cơ sở | Nghĩa | Ở đâu |
|---|---|---|
| `all` | MỌI ô có nhãn (kể cả khía cạnh chỉ có một chiều) | `metrics.json → scores`, và **số chọn mốc ở tầng `val`** |
| `paper` | CHỈ ô hai chiều (`positive`/`negative`) - đúng cách công bố đếm | `metrics.json → scores_paper`; cột `acc_paper_macro` và `neg_f1_big5` của bảng chuẩn |

⇒ Mọi con số **báo cáo** đọc ở cơ sở `paper`; số **chọn mốc** (val) nằm ở cơ sở `all`. Hai số lệch nhau
~1–3 điểm trên CÙNG một lượt nhưng **cùng chiều** ở cả 15 lượt của đợt 13.1 (đã kiểm).

## 2. Đã xong - ĐỪNG LÀM LẠI

### 2.1 Đợt 13.0 - sửa code (commit `7f3b52a`)

| # | Việc | Ở đâu |
|---|---|---|
| 1 | `early_stop.min_delta` **dùng thật** (`is_improved(value, previous, min_delta)`; `record()` dùng cho CẢ `model/best` lẫn con đếm `stale`) | `src/training/lora.py` + 4 test `EarlyStopImprovementTest` |
| 2 | Thêm chỉ số `neg_f1_big5` (TB F1 lớp âm trên 5 khía cạnh `n` lớn) vào `measure()` + `MEASURED_METRICS` | `src/training/lora.py` + 5 test |
| 3 | `metrics.json::cost` ghi **số epoch thực chạy** (`epoch đã chạy`) và **cờ dừng sớm** (`dừng sớm`) | `src/experiments/encoder_run.py` |
| 4 | `optuna` vào `requirements.txt` (KHÔNG vào `requirements-ci.txt`) | - |
| 5 | Tài liệu + config đồng bộ: `configs/experiments/training.yaml`, `docs/05_config/05_experiments_shared.md`, `docs/04_experiments/06_lora_encoder.md`, `docs/04_experiments/07_evolution.md` | - |

**Vì sao mục 1 quan trọng:** trước đó `min_delta` chỉ xuất hiện trong câu log, code so `value > best` nên val
nhiễu ±0,02–0,07 làm `stale` bị reset liên tục ⇒ **early stop không bao giờ chạy**.

### 2.2 Đợt 13.1 - 15 lượt chạy (commit `8f4eb49` tạo, `20db080` ghim, `e9f3d3b` ghi kết quả)

15 lượt = **5 nhánh × 3 seed** (`42 · 7 · 13`), `cafebert/lora/exp064` … `exp078`, tất cả trên nền
`lr 4e-4` · `r 16` (trừ B2 `r 8`) · `max_length 256` · `batch 8 × grad_accum 4` · `epochs 15` ·
`early_stop {enabled, patience 12 (B3: 24), min_delta 0,002}` · dữ liệu `v0.2.0` (`…-e616c1e3`) ·
`repo_sha 8f4eb49`.

| Nhánh | n | `Accuracy macro` | Δ vs họ | `neg F1 (5n)` | Δ vs họ | Welch p (Acc / F1) | Kết luận |
|---|---:|---:|---:|---:|---:|---|---|
| **B4** `best_metric: neg_f1_big5` | 3 | **98,523** | **+0,240** | **95,160** | **+0,783** | **9,5e-06 / 0,0086** | ✅ **ĐẠT** |
| B1 `epochs 15` + ES (đối chứng) | 3 | 98,170 | −0,113 | 93,867 | −0,510 | 0,251 / 0,217 | ⛔ đóng trục `epochs` |
| B3 `every_n_steps 50` + patience 24 | 3 | 97,907 | −0,377 | 93,180 | −1,197 | 0,368 / 0,371 | ⛔ đóng |
| B5 `class_weight: inverse_by_aspect` | 3 | 97,713 | −0,570 | 92,147 | −2,230 | 0,140 / 0,106 | ⛔ đóng VĨNH VIỄN |
| B2 `lora.r 8` + `epochs 15` | 3 | 97,830 | −0,453 | 92,920 | −1,457 | 0,0058 / 0,0041 | ❌ âm có ý nghĩa |

**Họ đối chứng** (12 lượt `lr 4e-4` của báo cáo v2, nguồn: `experiment_registry.csv`):
98,283 (sd 0,107) và 94,377 (sd 0,387). Thành viên: `exp015 · 021 · 027 · 028 · 040 · 041 · 042 · 043 ·
044 · 045 · 046 · 047`.

Từng lượt (test, `paper`; `Accuracy macro` / `neg F1 (5n)` / **epoch thực chạy** / phút):

| Lượt | Seed | Acc | F1 5n | Epoch | Phút |
|---|---|---:|---:|---:|---:|
| `exp064` B1 | 42 | 98,31 | 94,20 | 6 | 56 |
| `exp065` B1 | 7 | 98,07 | 93,28 | 6 | 58 |
| `exp066` B1 | 13 | 98,13 | 94,12 | 6 | 54 |
| `exp067` B2 | 42 | 97,90 | 93,30 | 5 | 46 |
| `exp068` B2 | 7 | 97,88 | 92,74 | 6 | 58 |
| `exp069` B2 | 13 | 97,71 | 92,72 | 6 | 52 |
| `exp070` B3 | 42 | 97,29 | 91,36 | 4 | 37 |
| `exp071` B3 | 7 | 98,03 | 93,20 | 6 | 73 |
| `exp072` B3 | 13 | 98,40 | 94,98 | 15 | 33 |
| `exp073` B4 | 42 | 98,52 | 94,90 | 12 | 43 |
| `exp074` B4 | 7 | 98,55 | 95,18 | 11 | 119 |
| `exp075` B4 | 13 | 98,50 | 95,40 | 6 | 63 |
| `exp076` B5 | 42 | 97,27 | 90,62 | 4 | 40 |
| `exp077` B5 | 7 | 97,77 | 92,48 | 4 | 43 |
| `exp078` B5 | 13 | 98,10 | 93,34 | 6 | 65 |

**Ba bằng chứng độc lập cho B4** (chép lại nguyên văn vì sẽ phải trích vào báo cáo):

1. **Cả 3 lượt B4 vượt TRẦN của họ 12 lượt ở CẢ HAI trục** (trần họ: Acc 98,47 · F1 94,86) ⇒ xác suất
   thuần hoán vị = `1/C(15,3)` = **1/455 ≈ 0,0022** mỗi trục.
2. **Welch B4 vs họ 12 lượt:** Acc `t = 7,01 → p = 9,5e-06`; `neg F1 (5n)` `t = 4,28 → p = 0,0086`.
   sd của B4: **0,025 Acc / 0,251 F1** (so với họ: 0,107 / 0,387) - cấu hình ổn định nhất từng đo.
3. **Ghép cặp CÙNG SEED** (chỉ khác ĐÚNG khoá `checkpoints.best_metric`):
   `exp064→073` +0,21/+0,70 · `exp065→074` +0,48/+1,90 · `exp066→075` +0,37/+1,28
   ⇒ trung bình **+0,353 Acc / +1,293 F1**, 3/3 dương ở cả hai trục, `ttest_rel`
   **p = 0,0459 (Acc) / 0,0649 (F1)**.

**⚠️ "Bàn đạp thứ 17" - ỨNG VIÊN, ĐÃ BỊ ĐỢT 13.2 BÁC BỎ (xem §2.3).** Ở **n = 3**, đây là nhánh **đầu tiên**
đạt công thức "Δ ≥ 0 ở cả hai trục, ít nhất một cái > 0". Cơ chế: **đổi thước CHỌN MỐC**
(`checkpoints.best_metric`) chứ không đổi kiến trúc, dữ liệu hay siêu tham số huấn luyện. Nhưng n = 3 là
**quá ít**: khi lên n = 9, hiệu ứng co còn **+0,084 / +0,114** (`p = 0,463 / 0,801`) ⇒ **đọc là ĐỒNG HẠNG**.

**Núm P/R đã lộ ra (số phải trích khi viết báo cáo).** Lớp ÂM trên 5 khía cạnh `n` lớn,
họ 12 → B1 → **B4** (cơ sở `paper`, %):

| Khía cạnh | P | R | F1 |
|---|---:|---:|---:|
| `colour` | 85,8 → 84,7 → **91,4** | 95,2 → 93,7 → 92,5 | 90,2 → 88,9 → **91,9** |
| `smell` | 86,7 → 85,4 → **90,9** | 96,9 → 97,2 → 94,5 | 91,5 → 90,9 → **92,5** |
| `texture` | 92,8 → 92,0 → **96,7** | 96,8 → 96,0 → 94,3 | 94,7 → 93,9 → **95,5** |
| `stayingpower` | 97,1 → 98,6 → **98,6** | 98,3 → 97,2 → 97,9 | 97,7 → 97,9 → **98,2** |
| `shipping` | 97,2 → 97,3 → 97,3 | 98,2 → 98,3 → 98,0 | 97,7 → 97,8 → 97,7 |

Lớp DƯƠNG: **Recall tăng** +0,7…+1,0 ở 4/5 khía cạnh, Precision phẳng (−0,2…−0,5), F1 +0,2…+0,3.

⇒ **Đích #1 (`texture` âm) tiến bộ thật** (P 92,8 → 96,7; khoảng cách với công bố rút từ −4,8 → −3,3).
⇒ **Đích #2 (Recall âm `smell`/`shipping`/`texture`) XA THÊM.** Vì chọn mốc theo thước F1 thì model
nghiêng về Precision. **Đây chính là lý do Bước 2 tồn tại.**

**Điều phải KHAI khi báo cáo (đừng giấu, đây là chỗ người phản biện sẽ chọc):**

- B4 **tối ưu trực tiếp trên `val` bằng chính thước `neg_f1_big5`** ⇒ phần thắng ở `neg F1` có yếu tố
  "được chọn". Vì thế kết luận **phải** dựa trên n = 9 (Bước 3) + phép ghép cặp, và **không** được tự khen
  trên đúng thước đo nó tối ưu mà không khai.
- Ngưỡng đã chốt TRƯỚC khi chạy: *"có ý nghĩa"* ⟺ vượt **> 0,7 pp** **VÀ** Welch `p < 0,05`.
  B4 đạt ở `neg F1` (+0,783, p = 0,0086) nhưng **KHÔNG đạt ngưỡng 0,7 ở `Accuracy`** (+0,240) dù
  `p = 9,5e-06`. Ghi đúng cả hai vế, **không nới ngưỡng sau khi thấy số**.

### 2.3 Đợt 13.2 - ĐÃ ĐO (15/10/2026): **KẾT LUẬN ÂM**

15 lượt `exp079`–`exp093`, ghim `22910c0`: tất cả `FINISHED`, `n_samples 1623`, `resume.mode NEW`,
`data.build …-e616c1e3`, `repo_sha 22910c0…`, `cost` có `epoch đã chạy` + `dừng sớm`. Số trên `test`,
cơ sở `paper`, so với họ 12 lượt `lr 4e-4` (**98,283** · **94,377**):

| Nhánh | n | `Accuracy macro` (sd) | Δ | `neg F1 (5n)` (sd) | Δ | Welch p (Acc / F1) | Đọc |
|---|---:|---:|---:|---:|---:|---|---|
| **B4** `best_metric: neg_f1_big5` | 9 | 98,367 (0,313) | **+0,084** | 94,491 (1,278) | **+0,114** | 0,463 / 0,801 | **ĐỒNG HẠNG** - ứng viên bàn đạp 17 **BỊ RÚT LẠI** |
| B1 `sentiment_f1` (đối chứng) | 9 | 98,167 (0,328) | −0,116 | 94,016 (1,213) | −0,361 | 0,330 / 0,411 | nhánh đối chứng ghép cặp |
| **R** `best_metric: neg_recall_big5` | 3 | 97,567 (0,316) | −0,716 | 91,987 (1,480) | −2,390 | 0,055 / 0,105 | **ĐÓNG trục** |

**Ghép cặp cùng seed B4 − B1 (n = 9):** Acc **+0,200** `p = 0,122`; `neg F1` **+0,476** `p = 0,391`;
**6/9 cặp dương**. Hiệu ứng **co lại** so với n = 3 (+0,240 / +0,783) và `sd` **nở ra** (0,025 → 0,313 Acc).

**Bằng chứng mạnh nhất:** `exp090` là lượt **B1** - thước CHỌN MỐC **CŨ** `sentiment_f1` - vẫn đạt
**98,60 / 95,76**. ⇒ Các đỉnh mới là do **hạt giống**, KHÔNG do núm chọn mốc.

**Nhánh R không đạt ("bán Precision quá đắt"):** Recall âm 5 khía cạnh chỉ về **đúng mức họ 12 đã có**
(97,060 vs 97,068) mà trả giá `Accuracy` −0,716 và `neg F1` −2,390. Số từng khía cạnh (cơ sở `paper`, %),
lớp ÂM, thứ tự **P / R / F1**:

| Khía cạnh | Họ 12 | B1 (n=9) | **B4 (n=9)** | R (n=3) |
|---|---|---|---|---|
| `colour` | 85,8 / 95,2 / 90,2 | 84,1 / 94,8 / 89,1 | **88,7 / 91,9 / 90,1** | 72,7 / 96,9 / 83,0 |
| `shipping` | 97,2 / 98,2 / 97,7 | 96,9 / 98,3 / 97,6 | 97,3 / 98,4 / 97,8 | 94,4 / 98,6 / 96,5 |
| `smell` | 86,7 / 96,9 / 91,5 | 87,1 / 95,8 / 91,2 | **88,5 / 94,9 / 91,5** | 88,2 / 95,8 / 91,8 |
| `stayingpower` | 97,1 / 98,3 / 97,7 | 97,9 / 97,3 / 97,6 | **98,3 / 97,1 / 97,7** | 95,6 / 97,5 / 96,5 |
| `texture` | 92,8 / 96,8 / 94,7 | 93,7 / 95,6 / 94,6 | **96,0 / 94,8 / 95,3** | 88,4 / 96,4 / 92,2 |

⇒ **Đích #1** (`texture` âm P) vẫn tiến bộ ở ĐÚNG một ô (92,8 → **96,0**) nhưng **không kéo được macro**;
**Đích #2** (Recall âm) **ĐI LÙI** ở B4 (97,068 → 95,400).

**Hai điều PHẢI KHAI (không phải lỗi):**
- `exp082` (B4 seed 4) và `exp088` (B1 seed 4) **trùng số** do chọn trúng **cùng mốc**; `config_sha256` KHÁC
  nhau và thời gian huấn luyện khác (4.229,6 s vs 4.268,1 s) ⇒ **hai lượt thật**, không phải copy nhầm.
- n = 9 của B4 **trộn hai `repo_sha`** (`8f4eb49` ×3 + `22910c0` ×6); `git diff` `src/training/lora.py` giữa
  hai sha là **thuần THÊM MỚI** (một hàm + một khoá `measure()` + một phần tử `MEASURED_METRICS`), **không
  chạm phép tính huấn luyện**.

**Kỷ lục LƯỢT ĐƠN mới** (luật 10: KHÔNG phải kết luận về cấu hình): `exp080` **98,65** (Acc cao nhất đường
encoder trên `test`) · `exp079` **95,86** (`neg F1 5n` cao nhất).

**Hệ quả:** sau 13.2 có **SÁU trục đã đóng** - `epochs` · `every_n_steps`/`patience` · `lora.r 8` ·
`class_weight: inverse_by_aspect` (13.1) · **thước CHỌN MỐC `neg_f1_big5`** · **thước thiên Recall
`neg_recall_big5`** (13.2). Không gian tìm kiếm của 13.3 vì thế **RÚT** `best_metric` + `epochs` +
`every_n_steps` (xem §8).


## 3. Việc còn lại - bảng tổng

| Bước | Việc | GPU | Trạng thái | Commit / kết quả |
|---|---|---|---|---|
| **2** | Thêm chỉ số `neg_recall_big5` (đo được + cột bảng chuẩn) + test + tài liệu | không | ✅ **XONG** | `8e7fe11` · `b7dcff7` · `945eb78` |
| **3** | Tạo 15 lượt Đợt 13.2 (`exp079`…`exp093`), ghim, đóng gói 036 | không | ✅ **XONG** | `22910c0` · `e34d508` · `7e0c42e` · `77752db` |
| **4** | Chạy 15 notebook trên Colab (song song) rồi trả kết quả về | **có** (15 phiên) | ✅ **XONG** - 15/15 `FINISHED` | - |
| **5** | Ghi kết quả + **kết luận ÂM** vào báo cáo, bảng chuẩn và nhật ký | không | ✅ **XONG** | `8d5e00d` + commit tài liệu |
| **6** | 13.3 → 13.6 (khung ở §8 - **đã sửa theo kết quả 13.2**) | tuỳ | ⏳ **chờ người dùng duyệt** | - |

## 4. Bước 2 - Thêm chỉ số `neg_recall_big5` (0 GPU)

**Mục đích:** có một thước **thiên Recall** để làm `checkpoints.best_metric`, nhắm **Đích #2** (Recall lớp âm
của `smell` / `shipping` / `texture` còn cách công bố 1–2 điểm). Số của 13.1 cho thấy thước chọn mốc
**điều khiển được** thế cân bằng Precision↔Recall ⇒ đây là cách duy nhất hiện có để kéo Recall lên.

### 4.1 Đặc tả hàm (bắt chước y hệt `neg_f1_big5_of` đã có)

| Mục | Yêu cầu |
|---|---|
| Tên | `neg_recall_big5_of(samples, labels, aspects=BIG_ASPECTS)` - đặt ngay dưới `neg_f1_big5_of` |
| Nghĩa | **Trung bình Recall của lớp ÂM trên 5 khía cạnh `n` lớn** (`colour · shipping · smell · stayingpower · texture`) |
| Quy ước bỏ ô rỗng | Khía cạnh **không có ô âm** (`support` rỗng) thì **BỎ**, không tính là 0 - y hệt `neg_f1_big5_of` và `fusion.negative_f1` |
| Trả `None` khi | bảng nhãn không có lớp `negative`, hoặc không khía cạnh nào trong nhóm có ô âm |
| Làm tròn | `round(..., 6)` (theo bộ đang có) |
| Tên trong `measure()` | khoá `"neg_recall_big5"` (cùng chỗ với `"neg_f1_big5"`) |
| Vào `MEASURED_METRICS` | **bắt buộc** - không thêm thì `checkpoints.best_metric: neg_recall_big5` bị chặn ngay khi khởi động (đúng thiết kế, đừng gỡ chốt đó) |

**Chỗ sửa (đọc kỹ trước khi sửa):** `src/training/lora.py` — `BIG_ASPECTS` và `neg_f1_big5_of` ở khoảng
dòng 715–745; `measure()` trả dict ở khoảng dòng 796–812; `MEASURED_METRICS` ở khoảng dòng 817–823.
Dữ liệu để tính nằm ở `(samples.per_sentiment() or {}).get("by_aspect")` → `[tên_khía_cạnh][mã_lớp]` →
`{"precision", "recall", "f1", "support"}` (mã lớp lấy qua `negative_code(labels)`).

**Cạm bẫy đã gặp, đừng lặp lại:**

- Có một chốt an toàn ở khoảng dòng 1026: *"`checkpoints.best_metric` = '…' nhưng lần đo này KHÔNG có chỉ số
  đó"* ⇒ lượt chạy **DỪNG NGAY**. Nếu hàm trả `None` ở lần đo đầu (val chưa có ô âm nào) thì cả lượt chết.
  Hàm này **không** được trả `None` khi lớp âm có ô - và phải có test cho cả hai nhánh.
- `docs/05_config/05_experiments_shared.md` và `configs/experiments/training.yaml` đang liệt kê danh sách
  chỉ số hợp lệ: **phải thêm tên mới vào cả hai** (đồng bộ tài liệu là việc bắt buộc, không phải tuỳ chọn).

### 4.2 Cột chuẩn cho bảng tổng hợp (khuyến nghị mạnh - làm luôn trong bước này)

`src/reporting/reports.py`: thêm **cột `neg_recall_big5`** (cơ sở `paper`) vào `REGISTRY_COLUMNS`, tính bằng
một hàm gương của `negative_f1_of_aspects` nhưng lấy `"negative" → "recall"`.
Lý do: **Đích #2 phải có MỘT nguồn số duy nhất** (bảng chuẩn), không được tính tay rồi viết vào văn xuôi -
đó là luật đã có của dự án cho hai cột `neg_f1_*`.

### 4.3 Test phải thêm (gương bộ test của `neg_f1_big5`, xem `tests/training/test_training.py`)

1. Trả `None` khi bảng nhãn không có lớp `negative`.
2. Trả `None` khi không khía cạnh nào trong nhóm có ô âm.
3. Bỏ khía cạnh không có ô âm (không tính là 0) - khoá quy ước.
4. Giá trị = trung bình Recall của đúng 5 khía cạnh `BIG_ASPECTS` (số dựng tay, không lấy từ chính hàm).
5. `"neg_recall_big5"` có mặt trong `MEASURED_METRICS` (để config không bị chặn oan).
6. (nếu làm 4.2) `reports.py`: cột mới có trong `REGISTRY_COLUMNS` và tính đúng trên dữ liệu dựng tay.

### 4.4 Điều kiện xong (DoD) của Bước 2

- `python scripts/ci_checks.py` → *"Không có việc nào phải sửa"*.
- `python -m unittest discover -s tests` → xanh, **trừ** lỗi có sẵn ở §1 (đúng 1 bài).
- Tài liệu đã thêm tên chỉ số: `configs/experiments/training.yaml`,
  `docs/05_config/05_experiments_shared.md`, `docs/04_experiments/06_lora_encoder.md`,
  `docs/04_experiments/07_evolution.md`.
- Commit tách riêng, ví dụ `feat(training): add neg_recall_big5 as a checkpoint selection metric`.

## 5. Bước 3 - Tạo 15 lượt cho Đợt 13.2 (0 GPU)

### 5.1 Thiết kế 15 lượt (chốt với người dùng: "vừa A vừa B")

| Lượt | Nhánh | Cha | Khoá KHÁC cha | Vì sao |
|---|---|---|---|---|
| `exp079`…`exp084` | **B4** (`best_metric: neg_f1_big5`) × seed **1 … 6** | `exp074` (B4 seed 7) | **`decoding.seed`** (1 khoá) | nâng nhánh thắng từ n = 3 lên **n = 9** |
| `exp085`…`exp090` | **B1** (`best_metric: sentiment_f1`) × seed **1 … 6** | `exp064` (B1 seed 42) | **`decoding.seed`** (1 khoá) | **nhánh đối chứng ghép cặp**: cùng seed ⇒ tách được đúng tác dụng của khoá `best_metric` |
| `exp091`…`exp093` | **R** (`best_metric: neg_recall_big5`) × seed **1, 2, 3** | `exp074` (B4) | **`decoding.seed`** + **`checkpoints.best_metric`** (2 khoá) | đánh **Đích #2** (Recall âm) - cần chỉ số của Bước 2 |

Seed `1…6` là 6 hạt giống **chưa dùng** (dự án đã dùng `42 · 7 · 13`). Bốn lượt/thí nghiệm cha phải giữ
NGUYÊN: `data.version v0.2.0` · `roles {train, val, test}` · `head.trainable true` · `lr 0.0004` ·
`max_length 256` · `batch 8 × grad_accum 4` · `epochs 15` · `early_stop {enabled, patience 12,
min_delta 0.002}` · `every_n_steps 100` · `answer_from logits` (mặc định) · `checkpoints.save_best true`.

### 5.2 Lệnh tạo lượt

`scripts/new_experiment.py` là công cụ duy nhất để tạo lượt (nó sinh `config.yaml` + `notebook.ipynb` +
`README.md` từ một lượt cha). Cách dùng đã dùng ở đợt 13.1: một script dùng-một-lần trong `_scratch/`
(gitignored) gọi `new_experiment` cho từng lượt, **có tự-kiểm YAML sau khi ghi**.

Điểm BẮT BUỘC:
- `new_experiment.py` **từ chối khi cây làm việc bẩn** ⇒ commit trước mỗi lần tạo (hoặc dùng `--allow-dirty`
  rồi commit ngay sau đó, như đã làm ở đợt 8/13).
- Notebook sinh ra có sẵn mục **"CÁCH ĐỌC (chốt TRƯỚC khi chạy)"** trong `config.yaml` - **sửa lại cho khớp
  Đợt 13.2** (so với họ 12 lượt; ba nhánh; ngưỡng 0,7 pp + Welch; nhánh R đo thêm Recall âm 5 khía cạnh).
- Sau khi tạo: **kiểm bằng script** rằng mỗi lượt khác cha **đúng** các khoá ở bảng 5.1 và **không** khác gì
  khác (đọc bằng chính bộ nạp config của dự án, không so chuỗi văn bản).

### 5.3 Trình tự bắt buộc (đúng thứ tự, mỗi mục một commit)

1. `python scripts/new_experiment.py …` × 15 (hoặc vòng lặp trong script `_scratch/`).
2. Kiểm "khác cha đúng các khoá đã thiết kế" ⇒ **commit** `experiment(stage-13.2): add the fifteen seed and recall-metric runs`.
3. **Push** lên `experiment` (pin.py cần commit có trên `origin/experiment`).
4. `python scripts/pin.py <nhãn> --allow-dirty` cho TỪNG lượt (ghim `REPO_SHA` vào notebook) ⇒ kiểm cả 15
   notebook có `REPO_SHA` = sha mới ⇒ **commit** `chore(experiments): pin the fifteen stage-13.2 notebooks to <sha8>`.
5. `python scripts/ci_checks.py` **phải xanh** (mục "REPO_SHA đã ghim" và "notebook sạch output").
6. `python scripts/build_package.py` ⇒ **gói 036** (tự động chỉ gửi file mới/đổi); cập nhật `handover/README.md`
   (mục "Đợt 13.2" - xem §6.4) ⇒ **commit** `chore(handover): package 036 with the fifteen stage-13.2 notebooks`; **push**.

### 5.4 Vì sao đúng 15 lượt này (đừng đổi mà không hỏi người dùng)

- **A** (12 lượt: B4 × 6 + B1 × 6) đưa B4 lên **n = 9** và cho **9 cặp ghép cùng seed** ⇒ đây là phép trả lời
  dứt điểm "chọn mốc có thật không", và giữ đúng ngưỡng đã chốt trước.
- **B** (thêm 3 lượt **R**) là mũi duy nhất đánh **Đích #2**; B chỉ thêm đúng 3 lượt so với A nên gộp lại
  thành 15, **không trùng lượt nào**.
- Chạy 15 phiên Colab song song đã chứng minh được ở đợt 13.1 (15/15 `FINISHED`, ~2,5–3 h wall clock).

## 6. Bước 4 - Chạy trên Colab và ĐỌC SỐ (luật đã chốt TRƯỚC)

### 6.1 Người chạy Colab làm gì

1. Giải nén **gói 036** đè lên thư mục Drive đang dùng (giữ nguyên cây thư mục của gói).
2. Mở **15 notebook** `notebooks/cafebert/lora/exp079.ipynb` … `exp093.ipynb`, chạy **song song** (mỗi phiên
   một GPU T4). KHÔNG chạy nối tiếp: 15 phiên song song ≈ 2,5–3 h, nối tiếp ≈ 8–10 h.
3. Kiểm dấu vết **trước khi đọc điểm**:
   - `training.epochs = 15` và `early_stop.enabled = true`;
   - cuối lượt `metrics.json::cost` **phải có** hai khoá `epoch đã chạy`, `dừng sớm`
     (vắng hai khoá này = đang chạy code cũ ⇒ DỪNG, ghim lại đúng sha);
   - lượt nhánh **R** phải có `checkpoints.best_metric = neg_recall_big5`.
4. Trả kết quả về: copy **15 thư mục** `experiments/cafebert/lora/exp0NN/results/<hash8>/` vào repo, **chỉ cần**
   `metrics.json`, `metrics.csv`, `training_history.csv`, `mispredictions*.csv`, `run.log`, `run_meta.json`
   (bỏ `model/`, `plots/`, `predictions/` - nặng vô ích). **Đúng cấp `results/<hash8>/`** - đợt 13.1 đã có
   một lượt bị copy sai cấp và phải sửa tay.

### 6.2 Khi kết quả về, người tiếp nhận làm gì (0 GPU)

1. Kiểm đủ 15 lượt: `metrics.json` tồn tại, `n_samples = 1623`, `resume.mode = NEW`, `repo_sha` = sha đã ghim.
2. `python scripts/collect_reports.py` → `experiment_registry.csv` phải có thêm **15 dòng** với
   `valid = comparable = yes`; đối chiếu vài ô với `metrics.json`.
3. `python scripts/ci_checks.py` → xanh.
4. Commit + push kết quả (`experiment(stage-13.2): record the fifteen ... results`).
5. Tính số theo §6.3 và **viết vào**: `presentations/present_report/present_report_v3.md` (bảng nhánh),
   `docs/06_plan/archive/batches/present_plan_batch13.md` (nhật ký 13.2), `docs/04_experiments/07_evolution.md` (kết luận).

### 6.3 Luật đọc số 13.2 (chốt trước khi chạy - KHÔNG nới sau khi thấy số)

**Trục so sánh:** `Accuracy macro` (cột `acc_paper_macro`) **và** `neg F1 (5 khía cạnh `n` lớn)`
(cột `neg_f1_big5`), cả hai đọc ở **cơ sở `paper`**, so với **họ 12 lượt** (98,283 · 94,377).

| Nhánh | n | Cách đọc | Kết luận nếu… |
|---|---:|---|---|
| **B4** | 9 | Welch 2 phía vs họ 12 **+** `ttest_rel` ghép cặp với B1 cùng seed (n = 9) | *Đạt* = Δ ≥ 0 cả hai trục, ≥ 1 cái > 0. *Có ý nghĩa* = vượt **> 0,7 pp** **VÀ** `p < 0,05` |
| **B1** | 9 | Chỉ là nhánh đối chứng ghép cặp (không cần kết luận riêng) | - |
| **R** | 3 | Đo **TB Recall lớp âm 5 khía cạnh, cơ sở `paper`** (cột `neg_recall_big5` của Bước 2) | *Đạt* = Recall **≥ +0,7** so với B4 **mà** `Accuracy` không giảm > 0,2 **và** `neg F1` không giảm > 0,7 |

- **Bắt buộc khai Δ từng khía cạnh `n` lớn ở cả P / R / F1** cho mọi nhánh (đã là luật của Đợt 13).
- Nhánh **R** là ý MỚI, chưa từng chạy: rủi ro đã biết là **Precision sụp** khi chọn mốc theo Recall
  (đúng vì thế mới cần hàng so sánh ghép cặp cùng seed 1, 2, 3 với B4/B1). Nếu R đạt ⇒ **đợt sau mới** lên
  n = 9 cho R; nếu không đạt ⇒ **đóng** và đi tiếp 13.3, ghi rõ là kết quả ÂM.
- ~~Nếu B4 ở n = 9 **xác nhận** ⇒ đây là kết luận chính của đợt 13 ...~~ **ĐÃ ĐỌC SỐ (15/10/2026): B4
  KHÔNG xác nhận ở n = 9** - **+0,084 / +0,114**, `p = 0,463 / 0,801`; ghép cặp cùng seed **+0,200 / +0,476**,
  `p = 0,122 / 0,391` (6/9 cặp dương). ⇒ Kết luận chính của đợt 13 là **ÂM**: *thước CHỌN MỐC chỉ là **núm
  chỉnh P↔R**, KHÔNG phải bàn đạp thắng*; kết quả n = 3 của 13.1 là **may mắn rút thăm**. Nhánh **R** cũng
  **KHÔNG đạt** (Recall chỉ về đúng mức họ 12 mà trả giá Acc −0,716 / F1 −2,390) ⇒ **ĐÓNG trục** thước thiên
  Recall. Số đầy đủ theo nhánh + từng khía cạnh: **§2.3**.

### 6.4 Mục cần viết vào `handover/README.md` cho gói 036

- 15 notebook MỚI (`exp079`…`exp093`) + sha đã ghim + bảng ba nhánh (§5.1).
- Dấu vết phải thấy (§6.1.3) + cách trả kết quả (§6.1.4, nhấn "đúng cấp `results/<hash8>/`").
- Luật đọc số (§6.3) - dán nguyên bảng, vì người chạy đọc file này TRƯỚC khi chạy.

## 7. Quy ước số liệu (đừng vi phạm)

- **Luật 10:** không lấy số của MỘT lượt làm kết luận; đọc theo **họ/nhánh** (mean ± sd, Welch).
- **Luật 12:** trên đường encoder, **cùng `decoding.seed` = cùng một lần rút thăm huấn luyện** ⇒ đếm `n` theo
  **hạt giống**, không theo số thư mục. (Đợt 13.1 có 2 lượt phải chạy lại vì copy thiếu file: vẫn 1 lượt/hạt
  giống, dùng số của lần chạy mới nhất.)
- **Luật 13:** `neg F1 macro (7 khía cạnh)` là **thước đo NHIỄU** (`price` 5–6 ô, `packing` 9–10 ô chi phối;
  sd 3,5 điểm trên chính họ 12 lượt). **Không** dùng nó để kết luận; thước đúng là
  `neg F1 (5 khía cạnh `n` lớn)`.
- **Luật 14:** bảng chính chỉ nhận lượt giữ nguyên **bài toán + dữ liệu** của công bố
  (`binary, drop, separate` + `cosmetics-ds0.2.0-…-e616c1e3`, split `test`, 1.623 review).
- **Luật 15:** ngắt ở tầng ĐÁNH GIÁ thì dùng được nếu `FINISHED` + `read_rate.valid` + **khai số ô tái dùng**;
  ngắt ở tầng HUẤN LUYỆN thì lượt đó **bỏ**.
- **Ngưỡng nhiễu 1 lượt:** ±0,7 pp. Phương sai hai họ lệch nhau ⇒ báo **Welch**, không dùng kiểm định gộp
  phương sai. Đơn vị: **điểm phần trăm (pp)** - viết `98,52`, không viết `0,9852`.

## 8. Sau 13.2 - khung 13.3 → 13.6 (chi tiết ở `docs/06_plan/archive/batches/present_plan_batch13.md` mục C) - **ĐÃ SỬA theo kết quả ÂM của 13.2**

| Đợt | Việc | GPU | Ghi chú đã cập nhật theo số của 13.1 |
|---|---|---|---|
| **13.3** | **Optuna NSGA-II** trên MÁY CÁ NHÂN, 2 mục tiêu `(accuracy_macro, neg_f1_big5)` trên `val` | 0 | **ĐÃ SỬA theo kết quả 13.2:** không gian **RÚT** `epochs` · `every_n_steps` · `best_metric` (cả ba vừa bị chứng minh là không đáng thử / không có tác dụng có ý nghĩa) và GIỮ CỐ ĐỊNH `checkpoints.best_metric: sentiment_f1`. Còn tìm: `lr` log-uniform `1e-4…1e-3` · `lora.r {4,8,16,32,64}` · `alpha {8,16,32,64,128}` · `lora_dropout {0, 0.05, 0.1, 0.2}` · `weight_decay {0, 0.01, 0.05, 0.1}` · `loss.class_weight {inverse, none, inverse_by_aspect}` · `use_dora {false,true}` · `head.trainable {true,false}` · `max_length {192,256,320,384}`. `n` nhỏ 500 mẫu `val`, `batch 4 × grad_accum 8` cho VRAM 6 GB; dừng khi 30 trial liên tiếp không cải thiện > 0,1 pp. Chỉ chọn trên `val`, KHÔNG chạm `test` |
| **13.4** | 3 điểm trên Pareto front × 3 seed, chạy **full 1.623** `test`, so bằng Welch | 9 | Chỉ tin kết luận từ đây (chọn-best-of-N trên `val` bị thiên lệch LÊN). **Bài học 13.2:** n = 3 KHÔNG đủ tin ⇒ thiết kế sẵn bước nâng nhánh thắng lên **n = 9** |
| **13.5** | LLM: DÒ lô suy luận `batch 4 / 2 / 1` trên **200 review cố định** (3 lượt) | 3 (+1–2 nếu đạt) | Ngưỡng mở full: lệch **> 0,5 pp** HOẶC **> 2 % ô**. Dưới ngưỡng ⇒ đóng trục batch |
| **13.6** | `exp034`: dữ liệu `v0.3.0` × 3 seed, nền = **cấu hình B4** (người dùng đã chốt) | 3 | B4 là **lựa chọn danh nghĩa tốt nhất** (+0,084 / +0,114; `texture` P +3,2) - **KHÔNG phải "đã xác nhận"** (xem §2.3). Giữ nó để 13.6 tách đúng **một** biến. `test` y đúc v0.2.0 nên số so được; `exp034` vào **BẢNG CHÍNH** kèm chú thích cố định: *"train/val khác phiên bản dữ liệu (v0.3.0 bỏ emoji); `test` y đúc v0.2.0"* (người dùng đã chốt) |

## 9. Nhật ký bàn giao

| Ngày | Việc | Commit / kết quả |
|---|---|---|
| 13/10/2026 | Đợt 13.0: `min_delta` dùng thật · thêm `neg_f1_big5` · ghi epoch thực + cờ dừng sớm · `optuna` vào requirements | `7f3b52a` |
| 13/10/2026 | Kế hoạch đợt 13 (mục A–H) | `0d3fd99` |
| 13/10/2026 | `present_report_v3.md` (báo cáo đang dùng) | `991af8c` |
| 13/10/2026 | 15 lượt 13.1: tạo · ghim · gói 035 | `8f4eb49` · `20db080` · `49f4342` · `dfe3e67` |
| 14/10/2026 | **Kết quả 15/15 lượt** + dựng lại bảng tổng hợp (`collect_reports.py`) | `e9f3d3b` |
| 14/10/2026 | Kết luận 13.1 (3 trục đóng, bàn đạp thứ 17, núm P/R) + file bàn giao này | `83db858` |
| 14/10/2026 | Dọn file nháp của đợt (xoá log/script dùng-một-lần ở `_scratch/`; còn 4 script tiện dụng) | `83db858` |
| 15/10/2026 | Bước 2: chỉ số `neg_recall_big5` (hàm + cột bảng chuẩn + 7 test + 4 tài liệu) | `8e7fe11` · `b7dcff7` · `945eb78` |
| 15/10/2026 | Bước 3: tạo 15 lượt 13.2 · ghim `22910c0` · gói 036 · mục "Đợt 13.2" trong `handover/README.md` | `22910c0` · `e34d508` · `7e0c42e` · `77752db` |
| 15/10/2026 | Bước 4: nhận đủ **15/15** kết quả (`FINISHED`, `n = 1623`, `NEW`, `repo_sha 22910c0`) | - |
| 15/10/2026 | Bước 5: ghi kết quả + **KẾT LUẬN ÂM**; **rút lại "bàn đạp thứ 17"**; sửa không gian 13.3 (§8) | `8d5e00d` · *(commit tài liệu)* |
| *còn lại* | **Bước 6**: 13.3 → 13.6 (§8 - **chờ người dùng duyệt**) | xem §3 |





