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

### NHÓM 6 - Đo độ vững (seed) - **10 lượt** - danh sách ĐỔI 11/10/2026 theo CỤM ĐỒNG HẠNG
| Cấu hình | Vì sao vào nhóm | seed chạy thêm | Lượt |
| --- | --- | --- | --- |
| `exp021` | **đỉnh MỚI** (98,41) - giữ 3 kỷ lục | 7, 13 | `exp040`, `exp041` |
| `exp027` | 98,37 (`epochs 6`) | 7, 13 | `exp042`, `exp043` |
| `exp015` | **đỉnh CŨ** (98,35) - giữ kỷ lục `neg F1 (5 n lớn)` | 7, 13 | `exp044`, `exp045` |
| `exp028` | giữ kỷ lục `neg F1 (5 n lớn)` = 94,84 | 7, 13 | `exp046`, `exp047` |
| `exp004` (v0) | đỉnh của báo cáo CŨ (`present_report_v0.md`) | 13 | `exp048` |
| `exp002` (v0) | cha gốc của cả họ CafeBERT | 13 | `exp049` |

**BỎ `exp012` khỏi nhóm seed (đổi 11/10/2026):** kỷ lục duy nhất của nó nằm ở thước đo **NHIỄU**
(`neg F1 (7)`, đến từ **6 ô** `price`), và `exp021` đã **vượt nó trên MỌI thước đo có `n`**.

Vì sao BẮT BUỘC: `exp004` (đỉnh của báo cáo cũ) chỉ kém kỷ lục Accuracy **0,09** => nằm trong nhiễu.
Không có nhóm này thì KHÔNG được viết "đã vượt v0", chỉ được viết "cùng dải nhiễu".

### NHÓM 7 - Mở đường KẾT HỢP (`eval: val`) - 5 lượt
`exp050` ← `exp015` · `exp051` ← `exp021` · `exp052` ← `exp013` · `exp053` ← `exp019` · `exp054` ← `exp018`
(mỗi lượt đổi `data.roles.eval: val`).
Vì sao: ngưỡng theo khía cạnh / ensemble / router chỉ đọc được tác dụng khi có >= 5 ứng viên `val`; hiện chỉ
`cafebert/lora/exp005` và `exp006` là `val`, và KHÔNG phải lượt nào đang dẫn đầu.

### NHÓM 8 - Đổi chỉ số chọn `model/best` sang lớp âm - 1 sửa mã + 3 lượt
Sửa `src/training/lora.py` + `KNOWN_KEYS` (`src/experiments/experiments.py`) + test => thêm một lựa chọn
`checkpoints.best_metric` tính F1 lớp âm. Lượt áp: `exp055` ← `exp015`, `exp056` ← `exp021`, `exp057` ← `exp013`.
**Điều kiện:** chỉ làm SAU khi NHÓM 11 kết luận `best_metric` hiện tại có tác dụng hay không.

### NHÓM 9 - Tầng PHƯƠNG PHÁP (0 GPU, dùng script có sẵn) - 3 việc
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

### Danh sách HOÃN (7 lượt) - **kèm LÝ DO và ĐIỀU KIỆN HỒI SINH** (chốt 11/10/2026)

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

## 5. Các đợt (thứ tự chạy)

| Đợt | Nhóm | Việc | GPU |
| --- | --- | --- | --- |
| **0** | 11 + 12 (phần hủy) + 14 (phần Phụ lục A) | Sửa Phụ lục A · ghi trạng thái HỦY · chẩn đoán 2 nghi lỗi | 0 |
| **1** | 1, 2, 3, 4, 5 (8 lượt ưu tiên) | `exp020` -> `exp024` -> `exp025` -> `exp027` -> `exp028` -> `exp033` -> `exp021` -> `exp030` | ~2,5 h |
| **2** | 6 + 7 | **10 lượt seed** (`exp040`-`exp049`) + **5 lượt `val`** (`exp050`-`exp054`) | ~3,5 h |
| **3** | phần còn lại của 4 + 5 | `exp034` `exp035` `exp036` `exp037` `exp038` (đúng **5 lượt**; 7 lượt vặn-số đã chuyển **HOÃN**) | ~1,5 h |
| **4** | 8 | sửa mã `best_metric` + `exp055` `exp056` `exp057` | ~45 phút |
| **5** | 10 | **3 lượt ví dụ lấy từ `train`** (`qwen3-4b-instruct-2507/prompt-cot/exp022`-`exp024`), sau khi tạo cặp prompt mới + kiểm rò rỉ | ~8-9 h |
| **6** | 9 | ensemble 5 top · dò ngưỡng 6/7 khía cạnh · biểu quyết 3 seed | 0 |
| **7** | 14 (phần cuối) | báo cáo chốt + `collect_reports.py` + commit | 0 |

**Tổng:** **31 lượt encoder** (8 đã xong + **23 còn lại**) + **7 lượt HOÃN** (không tính vào 31) + **3 lượt
prompt** (ví dụ từ `train`). Đã HỦY/BỎ: `qwen3-4b-thinking` ×2, `qwen3-8b` ×3, `mistral-7b` ×3,
`llama-3.1-8b`, `vistral-7b`; đã BỎ nhánh `full` (1 lượt) và tập chẩn đoán giá.
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
- [ ] Tạo + ghim **10 notebook seed**: `exp040` `exp041` (exp021) · `exp042` `exp043` (exp027) ·
      `exp044` `exp045` (exp015) · `exp046` `exp047` (exp028) · `exp048` (exp004) · `exp049` (exp002)
- [ ] Tạo + ghim **5 notebook `val`**: `exp050` (từ exp015) `exp051` (exp021) `exp052` (exp013)
      `exp053` (exp019) `exp054` (exp018)

### Đợt 3
- [ ] Tạo + ghim **5 notebook**: `exp034` (bỏ emoji) `exp035` (DoRA × lr 4e-4) `exp036`
      (`inverse_by_aspect` × lr 4e-4) `exp037` `exp038` (`head.trainable: false`)
- [x] **7 lượt vặn-số chuyển HOÃN 11/10/2026** (`exp022` `exp023` `exp026` `exp029` `exp031` `exp032`
      `exp039`) - lý do + điều kiện hồi sinh ở mục 4

### Đợt 4
- [ ] Sửa mã: thêm lựa chọn `checkpoints.best_metric` cho F1 lớp âm (+ `KNOWN_KEYS` + test)
- [ ] Tạo + ghim `exp055` `exp056` `exp057`
- [x] **BỎ** `cafebert/full/exp002` (nhánh `full` đã bị bỏ hẳn - mục 9.2)

### Đợt 5
- [x] **BỎ phần Llama 11/10/2026** (chi phí: cùng cỡ 8B như `qwen3-8b` = 3 ngày/3 lượt)
- [ ] Tạo **cặp prompt + ví dụ MỚI** lấy từ `train` (0/1/5 ví dụ) - xem NHÓM 10
- [ ] Chạy `run_check_examples.py` cho cả 1shot và 5shot - phải ra **"không rò rỉ"**
- [ ] Tạo + ghim 3 notebook `qwen3-4b-instruct-2507/prompt-cot/exp022-024`

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
| 11/10/2026 | Lỗi (đã hiểu, không phải lỗi mã) | **CI đỏ ở `558ea0e` và `2ba65ea`** - nguyên nhân: `ci_checks` trả mã 1 khi có việc phải sửa, mà hai commit đó chứa notebook **chưa ghim** (`REPO_SHA = '<chua-ghim>'`) | Đây là thế "con gà - quả trứng" **đúng luồng dự án**: push (đỏ) -> ghim -> push. Sau khi ghim, **CI XANH ở `4f9819d`**. Xin ghi lại để người sau khỏi tưởng mã sai |
| 11/10/2026 | Vướng | `pin.py` ghim xong lượt đầu thì **từ chối lượt sau** vì cây bẩn (nó chỉ cho commit ghim đổi ĐÚNG file notebook) | Ghim `exp020` bình thường, 7 lượt còn lại dùng `--allow-dirty` rồi commit ghim **một lượt** (giống đợt 11 ghim 48 notebook) |
| 11/10/2026 | Đợt 1 | **GHIM XONG 8/8** vào `2ba65ea`; `ci_checks` **Sạch**; **CI XANH** ở `4f9819d`. Gói **032** dựng xong | Người dùng đã chạy 8 notebook trên Colab |
| 11/10/2026 | **Đợt 1 (kết quả)** | **8/8 xong: KHÔNG có lượt nào THẮNG** - mọi mức vượt ≤ **0,24** < 0,70. Kỷ lục mới: `exp021` (Acc 98,41 · pos F1 98,99 · neg micro 95,36) và `exp028` (neg F1 n-lớn 94,84) | Đã ghi **mục 10**; **NHÓM 2 ĐÓNG** (`focal` + trọng số **thất bại**: 97,75/97,71 < cả hai cha); kết quả vào git `96e20c1`, bảng dựng lại `8da35fb` |
| 11/10/2026 | Phát hiện (LLM) | `qwen3-8b` **chạm trần 100 %** (TB **399,8/400**) ⇒ đọc được **0,12-1,05 %** vì model bật suy nghĩ mặc định; `mistral-7b` đọc được **60-72 %** (~32 % không có JSON) | Người dùng chốt **HỦY cả 6 lượt** (3 ngày Colab cho 0 kết quả dùng được) |
| 11/10/2026 | Thay đổi (người dùng chốt) | **BỎ `llama-3.1-8b`** (chi phí: cùng cỡ 8B như `qwen3-8b`) và **BỎ `vistral-7b`** (GATED) | NHÓM 10 co còn **3 lượt** (ví dụ từ `train` trên Qwen3-4B); đã ghi NHÓM 10 + NHÓM 12 |
| 11/10/2026 | Thay đổi | **NHÓM 6 đổi danh sách**: bỏ `exp012`, thêm `exp021`/`exp027`/`exp028` ⇒ **10 lượt**; **NHÓM 7** sang ID `exp050`-`exp054`; **NHÓM 8** sang `exp055`-`exp057` | Theo "cụm đồng hạng" mới |
| 11/10/2026 | Thay đổi | **Cắt Đợt 3 từ 12 → 5 lượt**; **7 lượt vặn-số chuyển HOÃN** kèm lý do + điều kiện hồi sinh | Mục "Danh sách HOÃN" ở phần 4 |

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
