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
- Biên nhiễu đường encoder **đã đo thật (đợt 2): sd = 0,11-0,16**; có cấu hình spread tới **0,28**. (Con số
  ±0,33…±0,67 ghi trước đó là ước lượng từ 2 lượt; số mới là số đo từ 10 lượt seed.)
- **Số của một lượt encoder = TRUNG BÌNH của >= 3 hạt giống**, KHÔNG lấy 1 lượt làm "kỷ lục" (xem luật 10 của
  `docs/04_experiments/metrics.md`).
- Một cấu hình chỉ được gọi là **"tăng"** khi hơn **> 0,25 ở CẢ Accuracy macro VÀ >= 1 chỉ số F1 có `n`**, với
  **n >= 3**. Dưới mức đó ghi **ĐỒNG HẠNG**.
- Lượt **bị ngắt ở tầng HUẤN LUYỆN rồi chạy tiếp** KHÔNG tính là một lần rút thăm sạch (dấu vết:
  `training_history.csv` không bắt đầu ở bước 100 / epoch 1) - xem luật 11 của `metrics.md`.
- Mọi bảng kèm **số ô** (`paper.cells`) và **`% đọc được`** (cửa `read_rate_min = 95`).
- **Hai thước đo F1 có trọng số `n`** (thêm ở đợt này, xem `present_report_v1.md`):
  `neg F1 macro (5 khía cạnh n lớn)` = trung bình F1 lớp âm trên 5 khía cạnh `n` = 48…174;
  `neg F1 micro (theo n)` = F1 lớp âm gộp mọi ô, trọng số = số ô.
- **`price`**: `n` âm = 6 ở `test`, **0 ở `val`** ⇒ mọi số `price` phải ghi kèm "n = 6, không kết luận".
  (Đợt này **KHÔNG** làm tập chẩn đoán giá - người dùng đã bỏ.)

## 3. Bench cần đánh bại - **ĐỔI 11/10/2026: dùng TRUNG BÌNH nhiều lượt, không dùng 1 lượt**

Lý do đổi: đợt 2 đo được biên nhiễu thật **sd = 0,11-0,16**, nên số của MỘT lượt là lượt-may-nhất, không phải
năng lực của cấu hình (xem mục 11).

| Thước đo | Công bố (đỉnh) | **v0 (`lr 2e-4`, TB 4 lượt)** | **Họ `lr 4e-4` (TB 11 lượt)** |
| --- | ---: | ---: | ---: |
| Accuracy macro (`paper`) | 97,70 | 98,06 | **98,29** |
| pos F1 macro | 98,49 | ~98,6 | ~98,90 |
| `neg F1 (5 khía cạnh n lớn)` | 88,23 | 93,60 | **94,41** |

**Ngưỡng phát hiện (thay cho ±0,7 khi so 1-1):** một cấu hình mới chỉ được gọi là **"tăng"** khi hơn **> 0,25 ở
CẢ Accuracy macro VÀ một chỉ số F1 lớp âm có `n`**, với **n >= 3 lượt**. Số của MỘT lượt chỉ để tham khảo.

**Dư địa còn lại (đã định lượng 11/10/2026):** lớp âm còn **~22 ô sai / 467 (4,7 %)**, rải ở các khía cạnh `n`
LỚN ⇒ đây là loại lỗi mà **KẾT HỢP (Đợt 6)** sửa được, không phải vặn nút.

## 4. Các nhóm thử nghiệm

Quy ước: mọi lượt `cafebert/lora` khác cha **ĐÚNG 1 khoá**; số `expNNN` nối tiếp `exp019`.
"NHÓM" gom theo **câu hỏi**; "ĐỢT" (mục 5) gom theo **thứ tự chạy**.

### NHÓM 1 - Nối hai trục đang dẫn (`lr` x `r` x scaling) - 4 lượt - **ĐÃ CHẠY 2** (`exp020` 98,34 · `exp021` **98,41**), **2 HOÃN** (`exp022`, `exp023`)
| Lượt | Cha | Đổi 1 khoá |
| --- | --- | --- |
| `exp020` | `exp015` | `lora.r: 32` |
| `exp021` | `exp015` | `lora.r: 8` |
| `exp022` | `exp013` | `lora.alpha: 64` |
| `exp023` | `exp012` | `lora.alpha: 16` |

### NHÓM 2 - `focal` CÓ trọng số lớp - **ĐÓNG 11/10/2026: THẤT BẠI**
Lí do (đã chốt: KHÔNG vì `price`, mà vì lớp âm nói chung): `focal gamma 2` cho `all acc` cao nhất dự án
(98,21, lượt `exp017`) và `detection_f1` trên `val` cao nhất (0,972); `weighted_ce + inverse` là thứ cứu
F1 lớp âm ở mọi cặp `ce -> wce`.

| Lượt | Cha | Đổi |
| --- | --- | --- |
| `exp024` | `exp002` | `loss.type: focal` + `loss.gamma: 2` + `loss.class_weight: inverse` |
| `exp025` | `exp015` | y như `exp024` |
| `exp026` | `exp025` | `loss.gamma: 1` |

**KẾT QUẢ 11/10/2026 - hướng này ĐÓNG.** `exp024` = **97,75** và `exp025` = **97,71** — **kém CẢ HAI cha**
(`exp002` 97,88 và `exp015` 98,35). Kết luận: **`focal` + trọng số lớp KHÔNG ghép được**; lợi thế của
`focal` (`all acc` 98,21 / `detection_f1` 0,972 ở `exp017`) **biến mất** khi thêm trọng số lớp. `exp026`
chuyển HOÃN. Đây là **kết quả ÂM có giá trị** - đã ghi vào `08_experiment_rationale.md`.

### NHÓM 3 - Nút siêu tham số CHƯA TỪNG VẶN - **ĐÃ CHẠY 3** (`exp027` 98,37 · `exp028` 98,31 · `exp030` 98,25), **3 HOÃN** (`exp029`, `exp031`, `exp032`)
| Lượt | Cha | Đổi 1 khoá |
| --- | --- | --- |
| `exp027` | `exp015` | `epochs: 6` |
| `exp028` | `exp015` | `checkpoints.every_n_steps: 50` |
| `exp029` | `exp015` | `weight_decay: 0.0` |
| `exp030` | `exp015` | `lora.dropout: 0.0` |
| `exp031` | `exp015` | `lora.dropout: 0.1` |
| `exp032` | `exp015` | `grad_accum: 2` |

### NHÓM 4 - Tiền xử lý x cấu hình dẫn đầu - **ĐÃ CHẠY 1** (`exp033` = 98,00 - KHÔNG tái lập), **3 còn lại**

**KẾT QUẢ `exp033`:** `segmenter: vncorenlp` trên `lr 4e-4` = **98,00** so cha 98,35 = **−0,35** ⇒ thay đổi
từng cho +0,15 trên cha `exp002` **KHÔNG tái lập**. Trục tiền xử lý vừa yếu vừa **không ổn định**.
| Lượt | Cha | Đổi 1 khoá | Ghi chú |
| --- | --- | --- | --- |
| `exp033` | `exp015` | `preprocess.segmenter: vncorenlp` | `exp008` cho +0,15 |
| `exp034` | `exp015` | `data.version: v0.3.0` | đổi DỮ LIỆU => bảng RIÊNG |
| `exp035` | `exp019` | `lr: 4e-4` | DoRA |
| `exp036` | `exp018` | `lr: 4e-4` | `inverse_by_aspect` |

### NHÓM 5 - Đầu phân loại + dừng sớm - 3 lượt - **2 còn** (`exp037`, `exp038`), **1 HOÃN** (`exp039`)
| Lượt | Cha | Đổi 1 khoá |
| --- | --- | --- |
| `exp037` | `exp015` | `head.trainable: false` |
| `exp038` | `exp013` | `head.trainable: false` |
| `exp039` | `exp027` | `early_stop.enabled: true` |

### NHÓM 6 - Đo độ vững (seed) - **13 lượt** - **10 ĐÃ CHẠY** + **3 MỚI (Đợt 2b)**

**KẾT QUẢ 11/10/2026 (10 lượt đã chạy).** Bảng `training_history.csv` phát hiện `exp049` **bị ngắt ở tầng
huấn luyện rồi chạy tiếp** (bắt đầu ở bước 400/epoch 2, không phải 100/epoch 1) ⇒ **loại khỏi nhóm seed** và
giữ làm bản ghi (luật 11). `exp042` chạy xong trên Colab nhưng **thiếu file nhẹ ở máy**.
| Cấu hình | Vì sao vào nhóm | seed chạy thêm | Lượt |
| --- | --- | --- | --- |
| `exp021` | **đỉnh MỚI** (98,41) - giữ 3 kỷ lục | 7, 13 | `exp040`, `exp041` |
| `exp027` | 98,37 (`epochs 6`) | 7, 13 | `exp042`, `exp043` |
| `exp015` | **đỉnh CŨ** (98,35) - giữ kỷ lục `neg F1 (5 n lớn)` | 7, 13 | `exp044`, `exp045` |
| `exp028` | giữ kỷ lục `neg F1 (5 n lớn)` = 94,84 | 7, 13 | `exp046`, `exp047` |
| `exp004` (v0) | đỉnh của báo cáo CŨ (`present_report_v0.md`) | 13 | `exp048` |
| `exp002` (v0) | cha gốc của cả họ CafeBERT | 13 | `exp049` |

**Ba lượt MỚI của Đợt 2b (11/10/2026)** - thêm lần rút thăm cho phía v0 (đang chỉ có 3 lượt SẠCH sau khi loại
`exp049`), vì phép so "họ `lr 4e-4` > v0" hiện ở **p ~ 0,06**: tăng `n` của nhóm YẾU là cách rẻ nhất để hạ p.

| Lượt | Cha | Đổi 1 khoá | Ghi chú |
| --- | --- | --- | --- |
| `exp058` | `cafebert/lora/exp002` | `decoding.seed: 1` | |
| `exp059` | `cafebert/lora/exp002` | `decoding.seed: 2` | |
| `exp060` | `cafebert/lora/exp002` | `decoding.seed: 3` | |

**BỎ `exp012` khỏi nhóm seed (đổi 11/10/2026):** kỷ lục duy nhất của nó nằm ở thước đo **NHIỄU**
(`neg F1 (7)`, đến từ **6 ô** `price`), và `exp021` đã **vượt nó trên MỌI thước đo có `n`**.

Vì sao BẮT BUỘC: `exp004` (đỉnh của báo cáo cũ) chỉ kém kỷ lục Accuracy **0,09** => nằm trong nhiễu.
Không có nhóm này thì KHÔNG được viết "đã vượt v0", chỉ được viết "cùng dải nhiễu".

### NHÓM 7 - Mở đường KẾT HỢP (`eval: val`) - 5 lượt - ✅ **ĐÃ CHẠY 11/10/2026**

| Lượt | Từ cấu hình | Acc macro trên `val` | `neg F1 (5 n lớn)` | số ô |
| --- | --- | ---: | ---: | ---: |
| `exp052` | `exp013` (`r 32`) | **98,73** | 94,94 | 2.751 |
| `exp053` | `exp019` (DoRA) | 98,62 | 94,14 | 2.750 |
| `exp051` | `exp021` (đỉnh mới) | 98,47 | 94,34 | 2.752 |
| `exp050` | `exp015` (đỉnh cũ) | 98,44 | 94,42 | 2.754 |
| `exp054` | `exp018` (`inverse_by_aspect`) | 98,31 | 93,16 | 2.746 |

**Đây là số trên `val` (1.535 review) - KHÔNG so được với số `test`**; chúng là **nguyên liệu** cho Đợt 6, và mỗi
lượt đều có `probabilities.csv` ở máy ⇒ **Đợt 6 chạy được ngay, 0 GPU**.
`exp050` ← `exp015` · `exp051` ← `exp021` · `exp052` ← `exp013` · `exp053` ← `exp019` · `exp054` ← `exp018`
(mỗi lượt đổi `data.roles.eval: val`).
Vì sao: ngưỡng theo khía cạnh / ensemble / router chỉ đọc được tác dụng khi có >= 5 ứng viên `val`; hiện chỉ
`cafebert/lora/exp005` và `exp006` là `val`, và KHÔNG phải lượt nào đang dẫn đầu.

### NHÓM 8 - Đổi chỉ số chọn `model/best` sang lớp âm - 1 sửa mã + 3 lượt
Sửa `src/training/lora.py` + `KNOWN_KEYS` (`src/experiments/experiments.py`) + test => thêm một lựa chọn
`checkpoints.best_metric` tính F1 lớp âm. Lượt áp: `exp055` ← `exp015`, `exp056` ← `exp021`, `exp057` ← `exp013`.
**Điều kiện:** chỉ làm SAU khi NHÓM 11 kết luận `best_metric` hiện tại có tác dụng hay không.

### NHÓM 9 - Tầng PHƯƠNG PHÁP (0 GPU, dùng script có sẵn) - 3 việc - 🎯 **ĐANG LÀM (Đợt 6)**
| Việc | Lệnh | Cần trước |
| --- | --- | --- |
| Ensemble / biểu quyết 5 lượt dẫn đầu | `scripts/ensemble.py`, `scripts/vote.py` | NHÓM 7 |
| Dò ngưỡng theo khía cạnh (6/7 khía cạnh; `price` bị loại vì `val` không có ô âm) | `scripts/fit_thresholds.py` | 1 lượt `val` |
| Biểu quyết 3 seed (trung bình xác suất) | `scripts/vote.py` | NHÓM 6 |
| ~~Gộp hai tầng (`fuse_aspect.py`)~~ | - | **ĐÃ BỎ** cùng mọi kế hoạch liên quan tới `price` |

### NHÓM 10 - Nhánh model SINH (prompt) - **co lại còn 3 lượt** (chốt 11/10/2026)

| Lượt | Trạng thái 11/10/2026 |
| --- | --- |
| ~~`llama-3.1-8b-instruct/prompt-cot/exp001-003`~~ | **BỎ vì CHI PHÍ** (cùng cỡ 8B ⇒ dự kiến như `qwen3-8b`: **3 ngày Colab cho 3 lượt**). Quyền truy cập đã có nên **không còn là rào cản** - rào cản bây giờ là **chi phí** |
| ~~`qwen3-8b/prompt-cot/exp001-003`~~ | **HỦY sau khi chạy**: đọc được **1,05 % / 0,92 % / 0,12 %**; `token sinh TB` = **399,8 / 399,8 / 400,0** với trần 400 ⇒ **CHẠM TRẦN 100 %** vì `Qwen/Qwen3-8B` **bật suy nghĩ mặc định** |
| ~~`mistral-7b-instruct-v0.3/prompt-cot/exp001-003`~~ | **HỦY sau khi chạy**: đọc được **60,4 % / 72,2 % / 63,5 %** (~32 % trả lời **không có khối JSON**) |
| `qwen3-4b-instruct-2507/prompt-cot/exp022` (0 ví dụ) · `exp023` (1 ví dụ) · `exp024` (5 ví dụ) | **CÒN LẠI** - ví dụ few-shot **lấy từ `train`**, trên model **4B** (chạy ~1,5-4 h/lượt) |

**Vì sao giữ phần lấy ví dụ từ `train`:** `qwen3-4b/prompt-cot/exp009` đang giữ **`neg F1 (5 n lớn)` = 94,70**
(#2 toàn dự án, chỉ sau `exp015` 0,08), mà **toàn bộ ví dụ hiện nay do người viết tay**, chưa lấy từ dữ liệu.

**Cách làm (bám sát luật 21 - cặp prompt + ví dụ BẤT BIẾN khi đã dùng):** tạo **cặp MỚI**, KHÔNG sửa file cũ:
`configs/prompts/absa_cot_trainfshot_v1.txt` +
`configs/prompts/examples/absa_cot_trainfshot_{0,1,5}shot_v1.txt`; mỗi ví dụ ghi rõ **`train, dòng N`**.
Trước khi chạy **PHẢI** chạy `python run_check_examples.py --hash e616c1e3 --prompt absa_cot_trainfshot_1shot_v1`
(và bản 5shot) và phải ra **"không rò rỉ"**; đỏ thì **đổi dòng khác trong `train`**, KHÔNG sửa ngưỡng.

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
| **HỦY (sau khi chạy)** `qwen3-8b/prompt-cot/exp001-003` | Đọc được **1,05 / 0,92 / 0,12 %**; `token sinh TB` = **399,8/399,8/400,0** với trần 400 ⇒ **chạm trần 100 %** (model bật suy nghĩ mặc định). **3 ngày Colab cho 0 kết quả dùng được** |
| **HỦY (sau khi chạy)** `mistral-7b-instruct-v0.3/prompt-cot/exp001-003` | Đọc được **60,4 / 72,2 / 63,5 %** (~32 % trả lời không có khối JSON); `read_rate.valid = false` |
| **BỎ (chưa tạo)** `llama-3.1-8b-instruct` | **Chi phí**: cùng cỡ 8B như `qwen3-8b`. Quyền truy cập đã có (11/10/2026) nhưng không đủ để bù chi phí |
| **BỎ (chưa tạo)** `Viet-Mistral/Vistral-7B-Chat` | Vẫn **GATED**, và cùng nhóm chi phí đã bị bỏ |
| 6 thư mục kết quả của `qwen3-8b` + `mistral` | **GIỮ** làm bản ghi "đã chạy và hỏng" (như 3 lượt `full`), KHÔNG xoá |

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

### Danh sách HOÃN (15 lượt) - **kèm LÝ DO và ĐIỀU KIỆN HỒI SINH** (bổ sung 11/10/2026 sau Đợt 2)

Nghĩa của `HOÃN` (theo `check_present_plan.md` §17 dùng chữ này): **chưa chạy BÂY GIỜ, KHÔNG xoá khỏi kế
hoạch, và có điều kiện hồi sinh rõ ràng**. Khác `BỎ QUA <lí do>`.

| Lượt | Nút | LÝ DO HOÃN (căn cứ SỐ ĐO) | Hồi sinh khi |
| --- | --- | --- | --- |
| `exp022` | `r 32` + `alpha 64` (tách scaling khỏi bậc tự do) | `exp020` (`r 32` × `lr 4e-4`) = **98,34 ≈ cha 98,35** ⇒ **"nhiều tham số hơn" KHÔNG phải đòn bẩy** ⇒ tách scaling gần như vô nghĩa | có lượt `r` lớn KHÁC thắng thật (sau khi chạy seed) |
| `exp023` | `r 8` + `alpha 16` | `exp021` (`r 8`, `alpha/r = 4`) đã ≈ đỉnh ⇒ scaling 4 không cản trở gì | `exp021` thắng thật sau khi chạy seed |
| `exp026` | `focal` với `gamma 1` | **`focal` + trọng số ĐÃ THẤT BẠI** (`exp024` 97,75 · `exp025` 97,71, kém CẢ HAI cha) ⇒ cả hướng focal yếu đi | có bằng chứng `focal` (không trọng số) hơn `weighted_ce` trên `n` lớn |
| `exp029` | `weight_decay: 0.0` | `exp030` (`dropout 0.0`) = **98,25 ≈ cha 98,35** ⇒ **"bớt regularize" không cứu được gì** | `exp031` (`dropout 0.1`) **TĂNG rõ** ⇒ regularize thành đòn bẩy |
| `exp031` | `dropout: 0.1` | chiều ngược của `exp030`, cùng căn cứ | như trên |
| `exp032` | `grad_accum: 2` (batch hiệu dụng 32 → 16) | batch hiệu dụng 32 ở **CẢ 30 lượt**; chưa có bằng chứng nào batch là nút thắt | `lr`/`r` thắng nhưng kết quả **không ổn định** giữa các seed |
| `exp039` | `early_stop.enabled` | chỉ có nghĩa khi đi kèm `epochs: 6`; mà `exp027` (`epochs 6`) = **98,37 ≈ 98,35** ⇒ **học lâu hơn không giúp** | quay lại dùng `epochs` lớn vì lý do khác |

**Bổ sung 11/10/2026 (sau Đợt 2 - đã đo được sd = 0,11-0,16):**

| Lượt | Nút | LÝ DO HOÃN (căn cứ SỐ ĐO) | Hồi sinh khi |
| --- | --- | --- | --- |
| `exp034` | bỏ emoji (pipeline `v0.3.0`) | `exp011` từng cho **+0,17** - nhưng đó là **MỘT lượt**, mà sd đo được là **0,11-0,16** ⇒ +0,17 **dưới ngưỡng phát hiện** | muốn thử lại thì phải **>= 3 seed** mới đáng GPU |
| `exp035` | DoRA × `lr 4e-4` | DoRA (`exp019` **97,99**) nằm **trong dải nhiễu** của họ `lr 4e-4` (98,25-98,31) | có bằng chứng `n >= 3` rằng DoRA hơn |
| `exp036` | `inverse_by_aspect` × `lr 4e-4` | `exp018` **97,93** - cũng trong dải nhiễu | như trên |
| `exp037` `exp038` | `head.trainable: false` | cặp cũ (`exp001` 97,67 vs `exp002` 97,88) lệch **0,21 < 1 sd** | như trên |
| `exp055` `exp056` `exp057` | `checkpoints.best_metric` tính F1 lớp âm (+ 1 sửa mã) | Đợt 2 cho thấy **chọn checkpoint KHÔNG phải nút thắt**: `every_n_steps 50` ≈ `100` (98,28 vs 98,30) và `epochs 6` ≈ `3` (98,25 vs 98,30) | có bằng chứng checkpoint đang bị chọn lệch (ví dụ khoảng cách lớn giữa `model/best` và `model/last`) |

## 5. Các đợt (thứ tự chạy)

| Đợt | Nhóm | Việc | GPU | Trạng thái |
| --- | --- | --- | --- | --- |
| **0** | 11 + 12 (phần hủy) + 14 (Phụ lục A) | Sửa Phụ lục A · ghi trạng thái HỦY · chẩn đoán 2 nghi lỗi | 0 | ✅ **XONG** |
| **1** | 1, 2, 3, 4, 5 | 8 lượt ưu tiên: `exp020` `exp021` `exp024` `exp025` `exp027` `exp028` `exp030` `exp033` | ~2,5 h | ✅ **XONG** - *không lượt nào thắng* |
| **2** | 6 + 7 | **10 lượt seed** (`exp040`-`exp049`) + **5 lượt `val`** (`exp050`-`exp054`) | ~3,5 h | ✅ **XONG** (14/15 có `metrics.json`) |
| **2b** | 6 | **3 lượt v0 + seed 1/2/3**: `exp058` `exp059` `exp060` | ~3 h | ⬜ **MỚI** |
| ~~3~~ | 4 + 5 | ~~`exp034` `exp035` `exp036` `exp037` `exp038`~~ | – | ⏸ **HOÃN cả 5** |
| ~~4~~ | 8 | ~~sửa mã `best_metric` + `exp055` `exp056` `exp057`~~ | – | ⏸ **HOÃN** |
| **5** | 10 | **3 lượt ví dụ lấy từ `train`** (`qwen3-4b-instruct-2507/prompt-cot/exp022`-`exp024`), sau khi tạo cặp prompt mới + kiểm rò rỉ | ~8-9 h | ⬜ giữ |
| **6** | 9 | ensemble 5 top · dò ngưỡng 6/7 khía cạnh · biểu quyết 3 seed | **0** | 🎯 **ĐANG LÀM** |
| **7** | 14 | báo cáo chốt (+ `present_report_v2.md` nếu Đợt 6 hơn > 0,25 ở CẢ 2 trục) | **0** | sau Đợt 6 |

**Tổng:** **128 lượt đã chạy có `metrics.json`**; còn phải chạy **6 lượt** (3 encoder Đợt 2b + 3 prompt Đợt 5);
**15 lượt HOÃN** (7 vặn-số + 5 Đợt 3 + 3 Đợt 4). Đã HỦY/BỎ: `qwen3-4b-thinking` ×2, `qwen3-8b` ×3, `mistral-7b` ×3,
`llama-3.1-8b`, `vistral-7b`, nhánh `full` (1 lượt + 3 đã chạy), và tập chẩn đoán giá.
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
- [x] **GHIM XONG 11/10/2026** - 8 notebook ghim vào `2ba65ea`, đẩy lên `origin/experiment`,
      **CI XANH** trên commit ghim `4f9819d` (`ci_checks` ở máy: exit 0, Sạch). Commit `chore(experiments): pin the eight stage-1 notebooks to 2ba65ea`
- [x] **GÓI XONG 11/10/2026** - `handover/out/SentimentX-goi-032-686e759-261011.zip`
      (17 file: 8 notebook + 8 README + MANIFEST; 259 file y nguyên không gửi lại). Commit `chore(handover): package 032 with the eight stage-1 notebooks`
- [x] **KẾT QUẢ ĐÃ VỀ 11/10/2026** - 8/8 lượt chạy xong, đã vào git (`96e20c1`), `collect_reports.py` đã chạy
      (`8da35fb`) ⇒ **KHÔNG có lượt nào "thắng"** (mọi mức vượt ≤ 0,24 < 0,70). Xem **mục 10**

### Đợt 2
- [x] **TẠO XONG 11/10/2026** - 15 notebook: 10 seed (`exp040`-`exp049`) + 5 `val` (`exp050`-`exp054`).
      Config + README cho từng lượt; `ci_checks` xác nhận **cấu hình hợp lệ**
- [x] **GHIM XONG 11/10/2026** - cả 15 ghim vào `6347f57`; **CI XANH** ở commit ghim `8799fb3`
- [x] **GÓI XONG 11/10/2026** - `handover/out/SentimentX-goi-033-8799fb3-261011.zip` (31 file: 15 notebook +
      15 README + MANIFEST). Commit `chore(handover): package 033 with the fifteen stage-2 notebooks`
- [x] **KẾT QUẢ ĐÃ VỀ 11/10/2026** - 14/15 lượt chạy xong; đã vào git (`7efb530`), `collect_reports.py`
      (`3f0cf82`) ⇒ **đo được biên nhiễu sd = 0,11-0,16**; **họ `lr 4e-4` ĐỒNG HẠNG**; hơn v0 **+0,22 Acc /
      +0,81 neg F1** (p ≈ 0,06/0,10). Xem **mục 11**
- [x] Hai lượt bất thường đã xử lý: `exp042` chạy xong nhưng **thiếu file nhẹ ở máy** (cần copy từ Drive);
      `exp049` **bị ngắt ở tầng huấn luyện** ⇒ loại khỏi nhóm seed (luật 11)

### Đợt 2b - 3 lượt v0 + seed 1/2/3 (mới 11/10/2026)
- [ ] Tạo + ghim 3 notebook: `exp058` `exp059` `exp060` (cha `exp002`, khác cha đúng 1 khoá `decoding.seed`)
- [ ] Đóng gói chung với Đợt 5 thành **gói 034**

### Đợt 3 - ĐÃ CHUYỂN HOÃN (11/10/2026)
- [x] **5 lượt chuyển HOÃN** (`exp034` `exp035` `exp036` `exp037` `exp038`) vì Đợt 2 chứng minh **các trục
      siêu tham số đã BÃO HOÀ** (sd 0,11-0,16 > mọi khác biệt có thể tạo ra) - lý do + điều kiện hồi sinh ở mục 4
- [x] **7 lượt vặn-số đã HOÃN từ trước** (`exp022` `exp023` `exp026` `exp029` `exp031` `exp032` `exp039`)

### Đợt 4 - ĐÃ CHUYỂN HOÃN (11/10/2026)
- [x] **HOÃN 3 lượt + 1 sửa mã** (`exp055` `exp056` `exp057`) vì Đợt 2 cho thấy **chọn checkpoint KHÔNG phải
      nút thắt** (`every_n_steps 50` ≈ `100`; `epochs 6` ≈ `3`) - lý do + điều kiện hồi sinh ở mục 4
- [x] **BỎ** `cafebert/full/exp002` (nhánh `full` đã bị bỏ hẳn - mục 9.2)

### Đợt 5
- [x] **BỎ phần Llama 11/10/2026** (chi phí: cùng cỡ 8B như `qwen3-8b` = 3 ngày/3 lượt)
- [ ] Tạo **cặp prompt + ví dụ MỚI** lấy từ `train` (0/1/5 ví dụ) - xem NHÓM 10
- [ ] Chạy `run_check_examples.py` cho cả 1shot và 5shot - phải ra **"không rò rỉ"**
- [ ] Tạo + ghim 3 notebook `qwen3-4b-instruct-2507/prompt-cot/exp022-024`

### Đợt 6 - 0 GPU - 🎯 ĐANG LÀM
- [ ] **6.1** Ensemble 5 lượt dẫn đầu (`scripts/ensemble.py`, chốt trọng số trên `val` rồi áp lên `test`)
- [ ] **6.2** Dò ngưỡng theo khía cạnh (6/7 khía cạnh; `price` loại vì `val` có 0 ô âm) - `scripts/fit_thresholds.py`
- [ ] **6.3** Biểu quyết 3 seed - `scripts/vote.py` trên `exp021`/`exp040`/`exp041` và `exp028`/`exp046`/`exp047`
- [ ] Luật đọc: bản gộp **chỉ có nghĩa khi đứng cạnh số của TỪNG thành viên trên cùng tập**; phải hơn
      **> 0,25 ở CẢ Acc và neg F1 (5 n lớn)** mới gọi là tiến bộ

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
| 11/10/2026 | Lỗi (đã hiểu, không phải lỗi mã) | **CI đỏ ở `558ea0e` và `2ba65ea`** - nguyên nhân: `ci_checks` trả mã 1 khi có việc phải sửa, mà hai commit đó chứa notebook **chưa ghim** (`REPO_SHA = '<chua-ghim>'`) | Đây là thế "con gà - quả trứng" **đúng luồng dự án**: push (đỏ) -> ghim -> push. Sau khi ghim, **CI XANH ở `4f9819d`**. Xin ghi lại để người sau khỏi tưởng mã sai |
| 11/10/2026 | Vướng | `pin.py` ghim xong lượt đầu thì **từ chối lượt sau** vì cây bẩn (nó chỉ cho commit ghim đổi ĐÚNG file notebook) | Ghim `exp020` bình thường, 7 lượt còn lại dùng `--allow-dirty` rồi commit ghim **một lượt** (giống đợt 11 ghim 48 notebook) |
| 11/10/2026 | Đợt 1 | **GHIM XONG 8/8** vào `2ba65ea`; `ci_checks` **Sạch**; **CI XANH** ở `4f9819d`. Gói **032** dựng xong | Người dùng đã chạy 8 notebook trên Colab |
| 11/10/2026 | **Đợt 1 (kết quả)** | **8/8 xong: KHÔNG có lượt nào THẮNG** - mọi mức vượt ≤ **0,24** < 0,70. Kỷ lục mới: `exp021` (Acc 98,41 · pos F1 98,99 · neg micro 95,36) và `exp028` (neg F1 n-lớn 94,84) | Đã ghi **mục 10**; **NHÓM 2 ĐÓNG** (`focal` + trọng số **thất bại**: 97,75/97,71 < cả hai cha); kết quả vào git `96e20c1`, bảng dựng lại `8da35fb` |
| 11/10/2026 | Phát hiện (LLM) | `qwen3-8b` **chạm trần 100 %** (TB **399,8/400**) ⇒ đọc được **0,12-1,05 %** vì model bật suy nghĩ mặc định; `mistral-7b` đọc được **60-72 %** (~32 % không có JSON) | Người dùng chốt **HỦY cả 6 lượt** (3 ngày Colab cho 0 kết quả dùng được) |
| 11/10/2026 | Thay đổi (người dùng chốt) | **BỎ `llama-3.1-8b`** (chi phí: cùng cỡ 8B như `qwen3-8b`) và **BỎ `vistral-7b`** (GATED) | NHÓM 10 co còn **3 lượt** (ví dụ từ `train` trên Qwen3-4B); đã ghi NHÓM 10 + NHÓM 12 |
| 11/10/2026 | Thay đổi | **NHÓM 6 đổi danh sách**: bỏ `exp012`, thêm `exp021`/`exp027`/`exp028` ⇒ **10 lượt**; **NHÓM 7** sang ID `exp050`-`exp054`; **NHÓM 8** sang `exp055`-`exp057` | Theo "cụm đồng hạng" mới |
| 11/10/2026 | Thay đổi | **Cắt Đợt 3 từ 12 → 5 lượt**; **7 lượt vặn-số chuyển HOÃN** kèm lý do + điều kiện hồi sinh | Mục "Danh sách HOÃN" ở phần 4 |
| 11/10/2026 | Đợt 2 | **TẠO + GHIM + ĐÓNG GÓI xong** 15 notebook (`exp040`-`exp054`) vào `6347f57`; **CI XANH** ở `8799fb3`; **gói 033** = `handover/out/SentimentX-goi-033-8799fb3-261011.zip` (31 file) | Còn lại: **người dùng chạy trên Colab** |
| 11/10/2026 | Ghi nhận (cách làm) | Khi phải tạo nhiều config giống nhau, đã dùng 2 script dùng-một-lần trong `_scratch/` (`make_seed_configs.py`, `prepend_readme_stage2.py`) thay vì sửa tay 15 file | Script nằm ở `_scratch/` (đã gitignore); KHÔNG vào git, không ảnh hưởng CI |
| 11/10/2026 | **Đợt 2 (kết quả)** | 14/15 lượt xong. **Đo được biên nhiễu sd = 0,11-0,16**; **4 cấu hình họ `lr4e-4` ĐỒNG HẠNG** (TB 98,25-98,31); họ `lr4e-4` hơn v0 **+0,22 Acc / +0,81 neg F1** (p≈0,06/0,10); mọi "kỷ lục" cũ là lượt MAY NHẤT | Ghi **mục 11**; bàn đo đổi sang **TB nhiều lượt** (mục 3); kết quả vào git `7efb530` + `3f0cf82` |
| 11/10/2026 | **Bất thường** | `exp042` **thiếu file nhẹ ở máy** (đã chạy xong trên Drive); `exp049` **bị ngắt ở tầng HUẤN LUYỆN** (`training_history.csv` bắt đầu ở bước 400/epoch 2) ⇒ cùng cấu hình + cùng seed với `exp048` mà ra 98,00 vs 98,11 | `exp049` **loại khỏi nhóm seed**; `exp042` cần copy từ Drive; **luật 11** đã thêm vào `metrics.md` |
| 11/10/2026 | Thay đổi (người dùng chốt) | **Đợt 3 + Đợt 4 → HOÃN** (11 lượt: 5 vặn-nút + 3 `best_metric` + 3 cũ đã hoãn); **thêm Đợt 2b** (3 lượt v0 seed 1/2/3); **Đợt 6 làm NGAY** | Đã cập nhật mục 3, 4, 5, 6; danh sách HOÃN nay **15 lượt** |
| 11/10/2026 | Ghi nhận | 5 lượt `val` (NHÓM 7) chạy xong và **`probabilities.csv` có sẵn ở máy** | ⇒ **Đợt 6 (0 GPU) chạy được ngay**, không phải chờ |

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
   → **CHỐT 11/10/2026 (người dùng): BỎ hẳn nhánh `full`** (nghi overfit/thoái hoá). Đã ghi "không dùng
   được" vào `06_lora_encoder.md`, `batch11_report.md`, `present_plan_batch11.md`, `present_report_v1.md`.

---

## 10. Kết quả Đợt 1 (11/10/2026) - **KHÔNG có lượt nào THẮNG**

8/8 lượt chạy xong trên Colab. Số cơ sở `paper`, split `test` (1.623 review), `% đọc được` = 100 % ở mọi lượt:

| Lượt | Thay đổi | Acc macro | pos F1 | neg F1 (7) | **neg F1 (5 n lớn)** | neg micro | số ô |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **`exp021`** | `lora.r 8` × `lr 4e-4` | **98,41** | **98,99** | 88,61 | 94,64 | **95,36** | 2.743 |
| `exp027` | `epochs 6` | 98,37 | 98,94 | **88,87** | 94,06 | 95,04 | 2.741 |
| `exp020` | `lora.r 32` × `lr 4e-4` | 98,34 | 98,94 | 85,61 | 94,26 | 95,07 | 2.745 |
| `exp028` | `every_n_steps 50` | 98,31 | 98,90 | 81,27 | **94,84** | 94,76 | 2.739 |
| `exp030` | `dropout 0.0` | 98,25 | 98,86 | 81,11 | 94,62 | 94,64 | 2.747 |
| `exp033` | `segmenter vncorenlp` | 98,00 | 98,69 | 80,26 | 93,42 | 93,69 | 2.745 |
| `exp024` | `focal gamma 2` + trọng số (trên `exp002`) | 97,75 | 98,54 | 82,74 | 92,98 | 93,78 | 2.747 |
| `exp025` | như trên (trên `exp015`) | 97,71 | 98,53 | 79,20 | 92,70 | 92,75 | 2.752 |

**Kỷ lục sau Đợt 1** - và mức vượt so với trước:

| Thước đo | Kỷ lục mới | Lượt | Cũ | Mức vượt |
| --- | ---: | --- | ---: | ---: |
| Accuracy macro | 98,41 | `exp021` | 98,35 | **+0,06** |
| pos F1 | 98,99 | `exp021` | 98,93 | **+0,06** |
| neg F1 (7) | 91,16 | `exp012` (giữ nguyên) | - | `exp027` 88,87 vẫn dưới |
| neg F1 (5 n lớn) | 94,84 | `exp028` | 94,78 | **+0,06** |
| neg micro | 95,36 | `exp021` | 95,12 | **+0,24** |

**Mọi mức vượt ≤ 0,24 < 0,70 (biên nhiễu) ⇒ tất cả ĐỒNG HẠNG.** "Top" nay là một **CỤM 6 lượt trải trong
0,10 điểm** (98,31 … 98,41) - bằng chứng định lượng cho thấy **các trục siêu tham số đã BÃO HOÀ**.

### Năm kết luận (2 là kết quả ÂM có giá trị)

1. **`lr 4e-4` × `r 32` KHÔNG cộng tính**: `exp020` = 98,34 ≈ cha 98,35 ⇒ hai trục đã chạm trần.
2. **`r 8` × `lr 4e-4` (`exp021`) là lượt giữ NHIỀU kỷ lục nhất (3/5)** - nhưng vượt ≤ 0,24 ⇒ chưa đủ tuyên bố.
3. **`focal` + trọng số lớp = THẤT BẠI rõ** (`exp024` 97,75 · `exp025` 97,71, kém CẢ HAI cha) ⇒ **NHÓM 2 ĐÓNG**.
4. **`segmenter: vncorenlp` KHÔNG tái lập** trên `lr 4e-4` (98,00 so 98,35 = **−0,35**) ⇒ trục tiền xử lý yếu
   và không ổn định.
5. **`epochs 6` ≈ `epochs 3`** (98,37 vs 98,35) và **`dropout 0.0` ≈ `0.05`** (98,25) ⇒ "học lâu hơn" và
   "bớt regularize" **KHÔNG phải nút thắt**.

### Phần LLM (6 lượt) - **cả 6 HỎNG, hai nguyên nhân khác nhau**

| Họ | Đọc được | Số đo quyết định | Chẩn đoán |
| --- | ---: | --- | --- |
| `qwen3-8b` ×3 | 1,05 % / 0,92 % / 0,12 % | `token sinh TB` = **399,8 / 399,8 / 400,0** với trần **400**; 96 % lỗi "không thấy JSON nào" | **chạm trần 100 %**: `Qwen/Qwen3-8B` **bật suy nghĩ mặc định** ⇒ viết hết trần trong ` thinking` |
| `mistral-7b` ×3 | 60,4 % / 72,2 % / 63,5 % | KHÔNG chạm trần (TB 244-309) nhưng ~32 % trả lời **không có khối JSON** | cần nới trần + siết yêu cầu định dạng |

Cả 6 `read_rate.valid = false` ⇒ **HỦY** (người dùng chốt: 3 ngày Colab cho 0 kết quả dùng được).
Luật 3 của `metrics.md` (chạm trần = lượt bị cắt) **đã bắt đúng** ca `qwen3-8b`.

---

## 11. Kết quả Đợt 2 (11/10/2026) - **ĐO ĐƯỢC BIÊN NHIỄU; họ `lr 4e-4` ĐỒNG HẠNG**

14/15 lượt có `metrics.json` (`exp042` chạy xong trên Colab nhưng thiếu file nhẹ ở máy). Gom theo CẤU HÌNH:

| Cấu hình (cha + các seed) | Acc macro từng lượt | **TB** | sd | **neg F1 (5 n lớn) TB** |
| --- | --- | ---: | ---: | ---: |
| `lr4e-4, r8` (`exp021` 42 · `exp040` 7 · `exp041` 13) | 98,41 · 98,38 · 98,13 | **98,31** | 0,15 | 94,59 |
| `lr4e-4, r16` (`exp015` 42 · `exp044` 7 · `exp045` 13) | 98,35 · 98,17 · 98,37 | **98,30** | 0,11 | 94,33 |
| `lr4e-4, every_n_steps 50` (`exp028` · `exp046` · `exp047`) | 98,31 · 98,16 · 98,37 | **98,28** | 0,11 | 94,49 |
| `lr4e-4, epochs 6` (`exp027` 42 · `exp043` 13 · `exp042` thiếu) | 98,37 · 98,14 | **98,25** | 0,16 | 94,15 |
| **`lr 2e-4` = v0** (`exp002` 42 · `exp004` 7 · `exp048` 13 · `exp049` 13) | 97,88 · 98,26 · 98,11 · 98,00 | **98,06** | 0,16 | **93,60** |

### Bốn kết luận

1. **BỐN cấu hình trong họ `lr 4e-4` ĐỒNG HẠNG TUYỆT ĐỐI** (TB 98,25-98,31, sd 0,11-0,16 ⇒ chênh giữa các TB
   ≤ 0,06 chỉ bằng 1/3 sd). ⇒ **`r 8` vs `r 16`, `epochs 3` vs `6`, `every_n_steps 100` vs `50`: KHÔNG có
   khác biệt đo được.** `exp021` (98,41) **không còn là "đỉnh" riêng**.
2. **Họ `lr 4e-4` hơn cấu hình v0 (`lr 2e-4`)**: **+0,22 Acc** (98,29 vs 98,06) và **+0,81 `neg F1 (5 n lớn)`**
   (94,41 vs 93,60); **đúng chiều ở MỌI lượt**. Ước lượng ý nghĩa: Acc **t ≈ 2,6 (p ≈ 0,06)**; neg F1
   **t ≈ 2,1 (p ≈ 0,10)** ⇒ **gợi ý mạnh, CHƯA đạt p < 0,05**. Cách rẻ nhất để hạ p: thêm lượt cho nhóm YẾU
   (v0) ⇒ **Đợt 2b**.
3. **Mọi "kỷ lục" cũ đều là LƯỢT MAY NHẤT của nó**: `exp021` 98,41 (TB 98,31); đỉnh báo cáo cũ `exp004`
   98,26 (TB họ v0 98,06). ⇒ **dùng 1 lượt làm kỷ lục đã nói quá 0,10-0,20 điểm**.
4. **Dư địa còn lại nằm ở lớp ÂM, rải ở khía cạnh `n` LỚN**: `exp021` còn **~22 ô sai / 467 ô âm (4,7 %)**,
   phân bố `colour` 5,2 · `texture` 4,4 · `smell` 3,7 · `shipping` 3,4 · `stayingpower` 2,0 · `price` 2,1 ·
   `packing` 1,0. ⇒ đây là **loại lỗi mà KẾT HỢP (Đợt 6) sửa được**, không phải vặn nút.

### Hai bất thường (đã xử lý)

- **`exp042`**: `run.log` ghi kết thúc 4.050,1 giây + "đã ghi `metrics.json`" + FINISHED, nhưng thư mục ở máy
  chỉ có `model/`, `run.log`, `run_meta.json` ⇒ **file nhẹ chưa copy từ Drive về**. → cần copy (hoặc chạy lại).
- **`exp048` vs `exp049`** (cùng cấu hình + cùng `decoding.seed: 13` nhưng 98,11 vs 98,00; best step 900 vs
  766): `training_history.csv` của `exp049` **chỉ 10 dòng và bắt đầu ở bước 400 / epoch 2** ⇒ lượt đó **bị
  ngắt ở tầng HUẤN LUYỆN rồi chạy tiếp** ⇒ **loại khỏi nhóm seed** (giữ làm bản ghi). Xem **luật 11**.

### Hệ quả cho kế hoạch

- Bàn đo đổi sang **TRUNG BÌNH nhiều lượt** (mục 3); ngưỡng phát hiện **> 0,25 với n >= 3**.
- **Đợt 3 + Đợt 4 CHUYỂN HOÃN** (11 + 3 lượt): vặn nút không còn tạo ra khác biệt đo được.
- **Thêm Đợt 2b** (3 lượt v0 + seed 1/2/3) để chốt phép so với v0.
- **Đợt 6 (KẾT HỢP) thành con đường CHÍNH** cho mục tiêu "tăng cả Acc và F1", vì dư địa nằm ở ô âm `n` lớn
  và 5 lượt `val` dẫn đầu đã có sẵn `probabilities.csv` ở máy.

## 12. Đợt 6 - BA VIỆC KẾT HỢP (12/10/2026): **CẢ BA ĐỀU KHÔNG CẢI THIỆN**

Đợt 6 là con đường CHÍNH còn lại (0 GPU; 5 lượt `val` dẫn đầu đã có `probabilities.csv` ở máy). Đã chạy đủ 3
việc: trọng số và ngưỡng **chốt trên `val`**, số báo cáo là số khi **áp lên `test`** (đúng luật 1 của `metrics.md`).
Mọi số dưới đây do CHÍNH công cụ chấm; "mạnh nhất" = lượt tốt nhất trong bộ đem đi gộp.

| Việc | Bằng chứng | Acc (`paper` macro) | neg F1 macro (7 khía cạnh) | So với mạnh nhất | Kết |
| --- | --- | ---: | ---: | --- | --- |
| 6.1 ensemble **6 model KHÁC NHAU** | `fusion/ensemble.json` · `ensemble_val.json` · `weights_val.json` | **97,87** | **0,795** | `exp013` 98,33 / 0,889 ⇒ **−0,46 / −0,094** | **THUA** |
| 6.1b ensemble **5 lượt cafebert** (trọng số đều) | `fusion/ensemble_cluster.json` | **98,26** | **0,856** | `exp013` 98,33 / 0,889 ⇒ −0,07 / −0,033 | **THUA nhẹ** |
| 6.2 **ngưỡng theo khía cạnh** (6/7 khía cạnh; `price` để nguyên) | `fusion/thresholds.json` · `thresholds_applied.json` | 98,33 → **98,33** | 0,889 → **0,889** | 0,000 / 0,000 | **RỖNG** |
| 6.3 **biểu quyết 3 seed** | `fusion/vote.json` | **98,41** | **0,809** | `exp021` 98,41 / 0,886 ⇒ 0,00 / **−0,077** | **NGANG acc, THUA F1** |

### Vì sao (phần đáng ghi lại)

- **Ensemble thắng TRUNG BÌNH thành viên nhưng thua THÀNH VIÊN MẠNH NHẤT.** 6 model: TB thành viên trên `test`
  ~96,89 → bản gộp **97,87** (**+0,98**), nhưng vẫn kém `cafebert/exp013` (**98,33**). Trọng số chốt trên `val`
  (cafebert 0,187 · phobert-base 0,180 · phobert-large 0,176 · xlm-roberta 0,161 · visobert 0,156 · vibert 0,141)
  **không đủ** để vô hiệu hoá các encoder yếu (`vibert` 94,84 · `visobert` 96,53) ⇒ **kết hợp chỉ có lợi khi các
  thành viên ĐỒNG HẠNG**; ở đây chúng lệch nhau tới 3,5 điểm.
- **Các lượt mạnh là 5 BIẾN THỂ CỦA CÙNG MỘT ENCODER** nên gộp chúng **không khử được lỗi**: bản gộp 5 lượt
  **98,26** ≈ TB họ `lr4e-4` **98,29** (lệch 0,03 < sd 0,11-0,16) - cả 5 mắc CÙNG lỗi.
- **Ngưỡng theo khía cạnh là bàn đạp RỖNG, và đây là bằng chứng quét:** lưới 0,05-0,95 cho `colour` trên `val`
  được 0,788 → 0,810 → 0,806 → 0,833 → 0,847 → 0,862 → … → **0,877** (không ngưỡng) ⇒ F1 âm **tăng đơn điệu về
  điểm gốc**, tức MỌI ngưỡng đều LÀM HỎNG ⇒ ngưỡng tốt nhất = 0,95 = "không làm gì". Xác suất lớp âm **đã xếp
  hạng đúng**: các ô âm thật đứng đầu, hạ ngưỡng chỉ thêm ô dương bị đoán âm.
- **Biểu quyết 3 seed không sửa được ô âm**: nâng Acc lên đỉnh (98,41 = ngang `exp021`) nhưng neg F1 **0,809**,
  thấp hơn cả `exp040` (0,813) và `exp021` (0,886); 11.361 ô đủ phiếu nhưng chỉ **8 ô hoà** ⇒ không có gì để phân
  xử, và 3 lượt **mắc cùng lỗi** nên bỏ phiếu không tạo thông tin mới.

### Kết luận Đợt 6 + hệ quả

**Không việc nào vượt > 0,25 trên CẢ HAI trục so với từng thành viên** ⇒ theo luật đã chốt ở mục 8, Đợt 6
**không sinh ra kết quả để báo cáo** (không có `present_report_v2.md`). Bằng chứng được GIỮ trong
`data/reports/fusion/` (kèm `inputs/` để tái lập từ repo, không cần Drive).

⇒ Cùng với việc các trục siêu tham số đã bão hoà (mục 11), **bàn đạp "kết hợp" nay cũng đã cạn**: dự án đang ở
trần của cấu hình hiện tại **~98,29 Acc / ~94,41 neg F1 (`n` lớn)**, vượt công bố **+0,59 Acc / +6,18 F1 âm**.
Muốn vượt trần này phải đổi **loại** (thêm dữ liệu / đổi loại lỗi), không phải đổi **núm**.
