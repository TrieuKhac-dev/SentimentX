# present_plan_batch12 - Kế hoạch đợt 12 và SỔ TRẠNG THÁI

> Đây là kế hoạch **ĐANG THỰC THI** của đợt 12, đặt ở gốc repo, và cũng là **sổ trạng thái** để không phải
> mở file thứ hai. Kế hoạch đợt trước (`present_plan_batch11.md`, `present_plan.md`) **giữ nguyên, không sửa**.
> Quy ước trạng thái (giống `check_present_plan.md`): `CHƯA LÀM` · `ĐANG LÀM` · `XONG <ngày>` ·
> `CHỜ NGƯỜI DÙNG` · `BỎ QUA <lí do>`.
> **Luật của sổ này:** mọi lỗi gặp phải và mọi thay đổi so với kế hoạch **phải** ghi vào **mục 6 - Nhật ký**,
> kèm ngày và lí do. Không sửa mục 4-5 cho khớp việc đã làm mà không ghi vào mục 6.

## 1. Mục tiêu

Mỗi lượt mới phải **giữ hoặc tăng F1** và **tăng Accuracy** so với các lượt đang trong top
(bench ở mục 3). Mục tiêu kép: *giữ F1, tăng Acc* **hoặc** *tăng cả Acc lẫn F1*.

## 2. Luật đọc số

- Cơ sở `paper` (chỉ ô mà CẢ nhãn đúng và nhãn đoán là positive/negative), split `test`, 1.623 review.
- Biên nhiễu đường encoder đã đo = **±0,33 … ±0,67**; lấy mức làm việc **±0,7**.
- Một lượt chỉ được gọi là **"tăng"** khi hơn lượt so sánh **> 0,7 ở CẢ Accuracy VÀ ≥ 1 chỉ số F1 có `n`**;
  dưới mức đó ghi **ĐỒNG HẠNG**.
- Mọi bảng kèm **số ô** (`paper.cells`) và **`% đọc được`** (cửa `read_rate_min = 95`).
- **Hai thước đo F1 có trọng số `n`** (thêm ở đợt này, xem `present_report_v1.md`):
  `neg F1 macro (5 khía cạnh n lớn)` = trung bình F1 lớp âm trên 5 khía cạnh `n` = 48…174;
  `neg F1 micro (theo n)` = F1 lớp âm gộp mọi ô, trọng số = số ô.
- **`price`**: `n` âm = 6 ở `test`, **0 ở `val`** ⇒ mọi số `price` phải ghi kèm "n = 6, không kết luận".
  (Đợt này **KHÔNG** làm tập chẩn đoán giá - người dùng đã bỏ.)

## 3. Bench cần đánh bại (5 kỷ lục thuộc 5 lượt khác nhau)

| Thước đo | Kỷ lục | Lượt giữ |
| --- | ---: | --- |
| Accuracy macro (`paper`) | 98,35 | `cafebert/lora/exp015` |
| pos F1 macro | 98,93 | `exp013` / `exp015` |
| neg F1 macro (7 khía cạnh) | 91,16 | `exp012` |
| neg F1 macro (5 khía cạnh `n` lớn) | 94,78 | `exp015` |
| neg F1 micro (theo `n`) | 95,12 | `exp013` |
| all acc (cả "không nhắc tới") | 98,21 | `exp017` |
| đỉnh của báo cáo CŨ (`present_report_v0.md`) | 98,26 | `exp004` |

## 4. Các nhóm thử nghiệm

Quy ước: mọi lượt `cafebert/lora` khác cha **ĐÚNG 1 khoá**; số `expNNN` nối tiếp `exp019`.
"NHÓM" gom theo **câu hỏi**; "ĐỢT" (mục 5) gom theo **thứ tự chạy**.

### NHÓM 1 - Nối hai trục đang dẫn (`lr` x `r` x scaling) - 4 lượt
| Lượt | Cha | Đổi 1 khoá |
| --- | --- | --- |
| `exp020` | `exp015` | `lora.r: 32` |
| `exp021` | `exp015` | `lora.r: 8` |
| `exp022` | `exp013` | `lora.alpha: 64` |
| `exp023` | `exp012` | `lora.alpha: 16` |

### NHÓM 2 - `focal` CÓ trọng số lớp (2 cơ chế chưa từng đi cùng) - 3 lượt
Lí do (đã chốt: KHÔNG vì `price`, mà vì lớp âm nói chung): `focal gamma 2` cho `all acc` cao nhất dự án
(98,21, lượt `exp017`) và `detection_f1` trên `val` cao nhất (0,972); `weighted_ce + inverse` là thứ cứu
F1 lớp âm ở mọi cặp `ce -> wce`.

| Lượt | Cha | Đổi |
| --- | --- | --- |
| `exp024` | `exp002` | `loss.type: focal` + `loss.gamma: 2` + `loss.class_weight: inverse` |
| `exp025` | `exp015` | y như `exp024` |
| `exp026` | `exp025` | `loss.gamma: 1` |

### NHÓM 3 - Nút siêu tham số CHƯA TỪNG VẶN (cùng giá trị ở cả 30 lượt) - 6 lượt
| Lượt | Cha | Đổi 1 khoá |
| --- | --- | --- |
| `exp027` | `exp015` | `epochs: 6` |
| `exp028` | `exp015` | `checkpoints.every_n_steps: 50` |
| `exp029` | `exp015` | `weight_decay: 0.0` |
| `exp030` | `exp015` | `lora.dropout: 0.0` |
| `exp031` | `exp015` | `lora.dropout: 0.1` |
| `exp032` | `exp015` | `grad_accum: 2` |

### NHÓM 4 - Tiền xử lý x cấu hình dẫn đầu - 4 lượt
| Lượt | Cha | Đổi 1 khoá | Ghi chú |
| --- | --- | --- | --- |
| `exp033` | `exp015` | `preprocess.segmenter: vncorenlp` | `exp008` cho +0,15 |
| `exp034` | `exp015` | `data.version: v0.3.0` | đổi DỮ LIỆU => bảng RIÊNG |
| `exp035` | `exp019` | `lr: 4e-4` | DoRA |
| `exp036` | `exp018` | `lr: 4e-4` | `inverse_by_aspect` |

### NHÓM 5 - Đầu phân loại + dừng sớm - 3 lượt
| Lượt | Cha | Đổi 1 khoá |
| --- | --- | --- |
| `exp037` | `exp015` | `head.trainable: false` |
| `exp038` | `exp013` | `head.trainable: false` |
| `exp039` | `exp027` | `early_stop.enabled: true` |

### NHÓM 6 - Đo độ vững (seed) - 8 lượt
| Cấu hình | seed đã có | chạy thêm | Lượt |
| --- | --- | --- | --- |
| `exp015` | 42 | 7, 13 | `exp040`, `exp041` |
| `exp013` | 42 | 7, 13 | `exp042`, `exp043` |
| `exp012` | 42 | 7, 13 | `exp044`, `exp045` |
| `exp002` (v0) | 42 và 7 (= `exp004`) | 13 | `exp046` |
| `exp004` (v0) | 7 | 13 | `exp047` |

Vì sao BẮT BUỘC: `exp004` (đỉnh của báo cáo cũ) chỉ kém kỷ lục Accuracy **0,09** => nằm trong nhiễu.
Không có nhóm này thì KHÔNG được viết "đã vượt v0", chỉ được viết "cùng dải nhiễu".

### NHÓM 7 - Mở đường KẾT HỢP (`eval: val`) - 5 lượt
`exp048` ← `exp015` · `exp049` ← `exp013` · `exp050` ← `exp012` · `exp051` ← `exp019` · `exp052` ← `exp018`
(mỗi lượt đổi `data.roles.eval: val`).
Vì sao: ngưỡng theo khía cạnh / ensemble / router chỉ đọc được tác dụng khi có >= 5 ứng viên `val`; hiện chỉ
`cafebert/lora/exp005` và `exp006` là `val`, và KHÔNG phải lượt nào đang dẫn đầu.

### NHÓM 8 - Đổi chỉ số chọn `model/best` sang lớp âm - 1 sửa mã + 3 lượt
Sửa `src/training/lora.py` + `KNOWN_KEYS` (`src/experiments/experiments.py`) + test => thêm một lựa chọn
`checkpoints.best_metric` tính F1 lớp âm. Lượt áp: `exp053` ← `exp015`, `exp054` ← `exp013`, `exp055` ← `exp012`.
**Điều kiện:** chỉ làm SAU khi NHÓM 11 kết luận `best_metric` hiện tại có tác dụng hay không.

### NHÓM 9 - Tầng PHƯƠNG PHÁP (0 GPU, dùng script có sẵn) - 3 việc
| Việc | Lệnh | Cần trước |
| --- | --- | --- |
| Ensemble / biểu quyết 5 lượt dẫn đầu | `scripts/ensemble.py`, `scripts/vote.py` | NHÓM 7 |
| Dò ngưỡng theo khía cạnh (6/7 khía cạnh; `price` bị loại vì `val` không có ô âm) | `scripts/fit_thresholds.py` | 1 lượt `val` |
| Biểu quyết 3 seed (trung bình xác suất) | `scripts/vote.py` | NHÓM 6 |
| ~~Gộp hai tầng (`fuse_aspect.py`)~~ | - | **ĐÃ BỎ** cùng mọi kế hoạch liên quan tới `price` |

### NHÓM 10 - Nhánh model SINH (prompt) - 10-12 lượt
| Lượt | Trạng thái |
| --- | --- |
| `llama-3.1-8b-instruct/prompt-cot/exp001-003` (0/1/5 ví dụ) | MỚI MỞ => phải tạo (config + `_chat_spec` + ĐO token) |
| `qwen3-8b/prompt-cot/exp001-003` | đã tạo + ghim, CHƯA CHẠY |
| `mistral-7b-instruct-v0.3/prompt-cot/exp001-003` | đã tạo + ghim, CHƯA CHẠY |
| Ví dụ few-shot lấy từ `train` cho `qwen3-4b` | hướng mới, 1-3 lượt |

Bước 1 BẮT BUỘC của phần Llama: `python _scratch/check_hf_access.py`. Không tải được thì DỪNG, KHÔNG đăng ký
(đăng ký một model không tải được sẽ làm đỏ phép đo token của MỌI model khác trong cùng lần chạy).

### NHÓM 11 - CHẨN ĐOÁN trước khi tin 2 kết luận (0 GPU)
| Ca | Bằng chứng | Nghi vấn |
| --- | --- | --- |
| A. `cafebert/lora/exp002` == `exp007` | giống y hệt MỌI chỉ số (`98,88 / 0,9861 / 0,8473 / 0,9262 / 0,9378`) dù `exp007` khác cha đúng 1 khoá `checkpoints.best_metric: accuracy_cell` | `best_metric` **không có tác dụng**? |
| B. `phobert-base-v2/full/exp001` == `exp002` | khác `lr` 10 lần (`2e-4` vs `2e-5`) mà cùng `all acc 75,12` và `paper.cells 0` | nhánh `full` **có lỗi mã**? |

### NHÓM 12 - HỦY / sửa
| Việc | Chi tiết |
| --- | --- |
| **HỦY** `qwen3-4b-thinking-2507/prompt-cot/exp001`, `exp002` | Lí do người dùng chốt: **quá chậm, kể cả lượt DÒ**. Sửa 5 file: `present_plan_batch11.md`, `batch11_report.md`, `docs/04_experiments/01_models.md`, `handover/README.md`, `configs/models/qwen3-4b-thinking-2507.yaml` |
| ~~`cafebert/full/exp002` ← `exp001`, `lr: 2e-5`~~ **BỎ 11/10/2026** | Người dùng chốt **bỏ hẳn nhánh `full`**: cả 3 lượt đã chạy đều thoái hoá (mục 9.2) ⇒ không còn là mốc đối chứng. 3 lượt GIỮ làm bản ghi "đã thử và hỏng" |
| `Viet-Mistral/Vistral-7B-Chat` | vẫn **GATED** => giữ trạng thái "CHẶN" |

### NHÓM 13 - Tập chẩn đoán GIÁ - **ĐÃ BỎ**
Người dùng chốt bỏ, cùng mọi kế hoạch liên quan. Hệ quả đã ghi nhận: `price` âm chỉ còn **6 ô ở `test`** nên
mọi con số `price` phải ghi kèm "n = 6, không kết luận"; dò ngưỡng chỉ chạy được cho **6/7** khía cạnh.

### NHÓM 14 - TÀI LIỆU (làm khi có kết quả)
| Việc | File |
| --- | --- |
| Sửa **Phụ lục A** (3 lượt nay ĐÃ XONG; `cafebert/full/exp001` hỏng vì **phân kỳ**, không phải bị ngắt) | `presentations/present_report/present_report_v1.md` |
| Thêm cột **nguồn** (v0 / đợt 11 / mới) + xếp hạng **2 trục** (Acc và F1) + gộp **đồng hạng** theo biên nhiễu | `present_report_v1.md` |
| Ghi trạng thái HỦY `qwen3-4b-thinking` | 5 file ở NHÓM 12 |
| Cập nhật 12 -> 13 model (thêm Llama) | `docs/04_experiments/01_models.md` |
| Nếu lượt mới vượt top => viết `present_report_v2.md`; `collect_reports.py` + commit phần nhẹ | `presentations/`, `data/reports/**` |

## 5. Các đợt (thứ tự chạy)

| Đợt | Nhóm | Việc | GPU |
| --- | --- | --- | --- |
| **0** | 11 + 12 (phần hủy) + 14 (phần Phụ lục A) | Sửa Phụ lục A · ghi trạng thái HỦY · chẩn đoán 2 nghi lỗi | 0 |
| **1** | 1, 2, 3, 4, 5 (8 lượt ưu tiên) | `exp020` -> `exp024` -> `exp025` -> `exp027` -> `exp028` -> `exp033` -> `exp021` -> `exp030` | ~2,5 h |
| **2** | 6 + 7 | 8 lượt seed (`exp040`-`exp047`) + 5 lượt `val` (`exp048`-`exp052`) | ~3,5 h |
| **3** | phần còn lại của 1, 2, 3, 4, 5 | `exp022` `exp023` `exp026` `exp029` `exp031` `exp032` `exp034` `exp035` `exp036` `exp037` `exp038` `exp039` | ~3,5 h |
| **4** | 8 | sửa mã `best_metric` + `exp053` `exp054` `exp055` | ~45 phút |
| **5** | 10 | Llama x3 (tạo mới) + Qwen3-8B x3 + Mistral x3 + prompt-từ-train (1-3) | ~8-12 h |
| **6** | 9 | ensemble 5 top · dò ngưỡng 6/7 khía cạnh · biểu quyết 3 seed | 0 |
| **7** | 14 (phần cuối) | báo cáo chốt + `collect_reports.py` + commit | 0 |

**Tổng:** **36** lượt encoder (đã bỏ 1 lượt nhánh `full`) + 10-12 lượt LLM; GPU ~20-25 h (rải trên Colab được).
Không còn việc người.
**Lưu ý thực thi:** các lượt cần **GPU** không chạy được ở máy này; phần làm được ở đây là tạo notebook +
config + README, chạy `--preflight-only`, ghim (`pin.py`) và đóng gói; **kết quả do người dùng chạy trên Colab**.

## 6. Sổ trạng thái (đánh dấu khi làm xong)

### Đợt 0 - 0 GPU
- [x] 0.1 **XONG 11/10/2026** - Sửa Phụ lục A của `present_report_v1.md`: 3 lượt (`cafebert/lora/exp010`,
      `exp012`, `phobert-base-v2/lora/exp017`) nay **ĐÃ XONG**; chỉ `cafebert/full/exp001` hỏng.
      Commit `83a1376`
- [x] 0.2 **XONG 11/10/2026** - Ghi trạng thái **HỦY** cho `qwen3-4b-thinking-2507/prompt-cot/exp001-002`
      ở 5 file; tiện thể cập nhật luôn Llama = **đã mở quyền**. Commit `126657d`
- [x] 0.3 **XONG 11/10/2026** - Chẩn đoán ca A: **KHÔNG có lỗi** - `best_metric` ĐƯỢC đọc (mục 9)
- [x] 0.4 **XONG 11/10/2026** - Chẩn đoán ca B: **CÓ vấn đề thật** ở nhánh `full` (mục 9) -
      **cần người dùng quyết** trước khi làm NHÓM 12 phần `full`
- [x] 0.5 **XONG 11/10/2026** - Người dùng chốt **BỎ hẳn nhánh `full`** (cả 3 lượt thoái hoá) ⇒ NHÓM 12 bỏ
      `cafebert/full/exp002`; tổng encoder **37 -> 36** lượt; đã ghi "không dùng được" vào
      `docs/04_experiments/06_lora_encoder.md`, `batch11_report.md`, `present_plan_batch11.md`,
      `present_report_v1.md`

### Đợt 1 - 8 lượt ưu tiên
- [x] **TẠO XONG 11/10/2026** - 8 notebook của Đợt 1: `exp020` `exp021` `exp024` `exp025` `exp027` `exp028`
      `exp030` `exp033` (config LoRA + README; `ci_checks` chỉ còn báo "chưa ghim `REPO_SHA`" - đúng dự kiến)
- [ ] **GHIM** 8 notebook - cần **CI XANH** trên commit chứa chúng (luật 22) rồi mới `pin.py`
- [ ] Người dùng chạy trên Colab; copy kết quả về; `collect_reports.py`; commit

### Đợt 2
- [ ] Tạo + ghim 8 notebook seed: `exp040` `exp041` `exp042` `exp043` `exp044` `exp045` `exp046` `exp047`
- [ ] Tạo + ghim 5 notebook `val`: `exp048` `exp049` `exp050` `exp051` `exp052`

### Đợt 3
- [ ] Tạo + ghim 12 notebook: `exp022` `exp023` `exp026` `exp029` `exp031` `exp032` `exp034` `exp035`
      `exp036` `exp037` `exp038` `exp039`

### Đợt 4
- [ ] Sửa mã: thêm lựa chọn `checkpoints.best_metric` cho F1 lớp âm (+ `KNOWN_KEYS` + test)
- [ ] Tạo + ghim `exp053` `exp054` `exp055`
- [ ] Tạo + ghim `cafebert/full/exp002` (đổi `lr: 2e-5`)

### Đợt 5
- [ ] Kiểm quyền tải Llama: `python _scratch/check_hf_access.py` (không được thì DỪNG)
- [ ] Thêm `configs/models/llama-3.1-8b-instruct.yaml` + dòng `_chat_spec` trong `token_stats.MODELS`
- [ ] ĐO token rồi chốt `max_length` + `batch_size`
- [ ] Tạo + ghim 3 notebook `llama-3.1-8b-instruct/prompt-cot/exp001-003`
- [ ] (tuỳ chọn) cặp prompt + ví dụ lấy từ `train` cho `qwen3-4b`

### Đợt 6 - 0 GPU
- [ ] Ensemble / biểu quyết 5 lượt dẫn đầu
- [ ] Dò ngưỡng theo khía cạnh (6/7 khía cạnh)
- [ ] Biểu quyết 3 seed

### Đợt 7 - 0 GPU
- [ ] Báo cáo chốt (+ `present_report_v2.md` nếu có lượt vượt top) + `collect_reports.py` + commit

## 7. Nhật ký thay đổi và lỗi

| Ngày | Loại | Nội dung | Xử lý |
| --- | --- | --- | --- |
| 11/10/2026 | Thay đổi | Người dùng chốt **bỏ NHÓM 13** (tập chẩn đoán giá) và **bỏ mục "gộp hai tầng"** ở NHÓM 9 | `price` ghi kèm "n = 6, không kết luận"; dò ngưỡng chỉ còn **6/7** khía cạnh |
| 11/10/2026 | Thay đổi | Người dùng chốt **giữ 3 lượt `focal`** (NHÓM 2) nhưng **đổi lí do**: không vì `price`, mà vì **lớp âm nói chung** | Ghi ở NHÓM 2 |
| 11/10/2026 | Phát hiện | `metrics.json` tăng **97 -> 100**: `cafebert/lora/exp010`, `cafebert/lora/exp012`, `phobert-base-v2/lora/exp017` **đã có kết quả** (trước đó sổ ghi là "hỏng/chưa xong") | Xử lý ở 0.1; `exp012` (r=8) lọt top 4 |
| 11/10/2026 | Phát hiện | `cafebert/full/exp001` **không bị ngắt**: chạy xong 1.150 bước nhưng `loss nan` từ bước 100 => **phân kỳ** | Xếp vào NHÓM 12 (`cafebert/full/exp002`, `lr: 2e-5`) |
| 11/10/2026 | Lỗi công cụ | Lệnh `git log` bị shell chuyển hướng, sinh **file rác tên `e`** ở gốc repo => cây làm việc bẩn | Đã xoá file `e` |
| 11/10/2026 | Vướng | `_scratch/` chưa được gitignore nên `new_experiment.py` / `pin.py` coi cây là **bẩn** (hàm `worktree_dirty` tính cả file chưa theo dõi) | Đã thêm `_scratch/` vào `.gitignore` (commit `9e68f73`); `ci_checks` vẫn sạch |
| 11/10/2026 | Ghi nhận | Đã bỏ ý định nâng `preprocess.max_length` của encoder | Số đo: `% review bị cắt ở 256` = **0,00 %** cho mọi encoder => nút vô dụng |
| 11/10/2026 | Ghi nhận | Các lượt cần GPU **không chạy được ở máy này** | Phần làm ở đây: tạo notebook + config + README + `--preflight-only` + `pin.py` + đóng gói |
| 11/10/2026 | Đợt 0 | Ca A `best_metric`: **KHÔNG có lỗi** - `exp002` và `exp007` chọn CÙNG checkpoint bước 800 nên điểm trùng nhau là hợp lệ | NHÓM 8 giữ nguyên (đã có cơ sở) |
| 11/10/2026 | **LỖI (lớn)** | Ca B nhánh `full`: cả 3 lượt đoán **"không nhắc tới" cho MỌI ô** (`sentiment_f1 = 0`, `paper.cells = 0`, `all acc = 73,69 %`); hai lượt PhoBERT khác `lr` **10 lần** ra y hệt từng khía cạnh | Ghi ở mục 9.2; **ĐỔI NHÓM 12** (phải thêm `inference.dtype: float32`); **BÁO CÁO người dùng** (mục 6 việc 0.5) |
| 11/10/2026 | Phát hiện | `cafebert/full/exp001` **không có `metrics.json`** trên đĩa (mà `run.log` nói "đã ghi") - chỉ có `run.log`, `run_meta.json`, `model/` | Kết luận về lượt này lấy từ `run.log`; ghi rõ trong Phụ lục A |
| 11/10/2026 | Thay đổi (người dùng chốt) | **BỎ hẳn nhánh `full`** khỏi kế hoạch (lý do: full fine-tune bị overfit/thoái hoá). Đã ghi "không dùng được" vào `06_lora_encoder.md`, `batch11_report.md`, `present_plan_batch11.md`, `present_report_v1.md` | Tổng encoder **37 -> 36**; Đợt 4 nay chỉ còn NHÓM 8; 3 lượt `full` giữ làm bản ghi |
| 11/10/2026 | Đợt 1 | **TẠO XONG 8 thí nghiệm** `exp020` `exp021` `exp024` `exp025` `exp027` `exp028` `exp030` `exp033` (8 commit nhỏ `feat(experiments)`); mỗi lượt khác cha ĐÚNG 1 khoá/nhóm khoá | `ci_checks` xác nhận **cấu hình hợp lệ** (chỉ báo chưa ghim `REPO_SHA`); còn phải **ghim** sau khi CI xanh |
| 11/10/2026 | Ghi nhận | Phải **gitignore `_scratch/`** vì `worktree_dirty()` tính cả file chưa theo dõi; và `new_experiment.py` **từ chối khi cây bẩn** nên mỗi lượt tạo xong phải commit trước khi tạo lượt kế | Đã gitignore (`9e68f73`); 7 lượt sau dùng `--allow-dirty` rồi commit riêng từng lượt |

## 8. Đã xong TRƯỚC khi mở sổ này (11/10/2026)

| Việc | Commit |
| --- | --- |
| Dọn `presentations/`: chỉ còn báo cáo; bỏ 4 tài liệu cũ + 6 CSV; `present_report.md` -> `present_report_v0.md` | `fc62424` |
| Thêm `present_report_v1.md` (4 thước đo F1 có trọng số `n` + giữ nguyên Bảng 3-6 cũ) | `7b34fa2` |
| Trỏ lại 3 link tài liệu sang `present_report_v1.md` | `e87cc5c` |
| Đưa **276 file** kết quả nhẹ của **36 lượt** đợt 11 vào git | `ae5a532` |
| Dựng lại bảng tổng hợp (`collect_reports.py`: **100** experiment, **106** attempt) | `0166ed4` |
| Gitignore `_scratch/` để `new_experiment.py` / `pin.py` thấy cây sạch | `9e68f73` |

**Kiểm sau khi mở sổ:** `python scripts/ci_checks.py` = **Sạch** (9/9 kiểm tra không có vấn đề).
`python -m unittest discover -s tests` = **1096 test, 1 lỗi CÓ SẴN của môi trường**
(`tests/training/test_full.py::test_every_parameter_is_trainable`, `ImportError: cannot load module more than
once per process` của numpy/scipy) - **không** do các thay đổi ở mục 8.

---

## 9. Cập nhật 11/10/2026 - kết quả Đợt 0

### 9.1 Ca A (`checkpoints.best_metric`) - **KHÔNG CÓ LỖI**, khoá có tác dụng

| Lượt | `model/best` | `best.step` | `best.metric` | `sentiment_f1` | `accuracy_cell` | `paper acc macro` |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| `cafebert/lora/exp002` | `93448395` | **800** | `sentiment_f1` | 0,916 | 97,85 | 97,88 |
| `cafebert/lora/exp007` | `be5d198b` | **800** | `accuracy_cell` | 0,916 | 97,85 | 97,88 |

Hai lượt **chọn đúng CÙNG một checkpoint (bước 800)** vì đường `val` đạt đỉnh ở cùng bước cho cả hai
chỉ số ⇒ điểm test trùng nhau là **hợp lệ**, không phải bug. Bằng chứng khoá ĐƯỢC đọc: `best.metric` ghi
giá trị khác nhau (`sentiment_f1` vs `accuracy_cell`) theo đúng config.
**Hệ quả:** NHÓM 8 (chọn `model/best` theo F1 lớp âm) **có cơ sở** - nếu chỉ số khác thì có thể chọn
checkpoint KHÁC (như `exp015` chọn bước 1150 còn `exp013` chọn bước 900).

### 9.2 Ca B (nhánh `full`) - **CÓ VẤN ĐỀ THẬT**, cả 3 lượt đều thoái hoá

Ma trận nhầm của `phobert-base-v2/full/exp002` (`lr 2e-5`) - **mọi khía cạnh**:

| nhãn đúng \ nhãn đoán | `""` (không nhắc) | positive | negative |
| --- | ---: | ---: | ---: |
| `""` | đúng | 0 | 0 |
| positive | **tất cả** | 0 | 0 |
| negative | **tất cả** | 0 | 0 |

⇒ Model dự đoán **"không nhắc tới" cho MỌI ô**: `sentiment_f1 = 0`, `detection_f1 = 0`,
`paper.cells = 0`, `all acc = 73,69 %` (= đúng tỉ lệ ô "không nhắc tới" của `val`, 10.554 ô).
`cafebert/full/exp001` cho cùng dạng (`run.log`: "cơ sở đo paper: **0 ô giữ lại**").

**Hai lượt PhoBERT khác `lr` 10 lần (`2e-4` vs `2e-5`) mà ra Y HỆT từng khía cạnh**
(85,03 / 72,48 / 81,33 / 79,84 / 57,00 / 68,19 / 81,99) ⇒ **không phải lỗi tối ưu, mà là hệ thống**.
`loss = nan` ở `exp001` (lr 2e-4). Giả thuyết mạnh nhất: **full fine-tune chạy ở fp16** (`inference.dtype: auto`
chọn fp16 trên T4 vì Turing không có bf16) **không có GradScaler** ⇒ encoder tràn số ⇒ `pooled` thành
nan/inf ⇒ `argmax` của nan trả về chỉ số 0 = "không nhắc tới" cho mọi ô.

**HỆ QUẢ PHẢI SỬA TRONG KẾ HOẠCH:**
1. **NHÓM 12 đổi**: `cafebert/full/exp002` phải khai **`inference.dtype: float32`** (không chỉ đổi `lr`).
2. Mốc đối chứng "full fine-tune" của tài liệu (`docs/04_experiments/06_lora_encoder.md`) **hiện không dùng
   được** - nó dựa trên 3 lượt đều thoái hoá.
3. Người dùng cần quyết: có điều tra tiếp nguyên nhân gốc không, hay chỉ chạy lại với `float32` để có mốc.
