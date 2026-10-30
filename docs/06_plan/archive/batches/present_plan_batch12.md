# present_plan_batch12 - Kế hoạch đợt 12 và SỔ TRẠNG THÁI

> Đây là kế hoạch **ĐANG THỰC THI** của đợt 12, đặt ở gốc repo, và cũng là **sổ trạng thái** để không phải
> mở file thứ hai. Kế hoạch đợt trước (`docs/06_plan/archive/batches/present_plan_batch11.md`, `docs/06_plan/archive/P7-P10/present_plan.md`) **giữ nguyên, không sửa**.
> Quy ước trạng thái (giống `docs/06_plan/archive/P7-P10/check_present_plan.md`): `CHƯA LÀM` · `ĐANG LÀM` · `XONG <ngày>` ·
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
- **Hai thước đo F1 có trọng số `n`** (thêm ở đợt này, xem `presentations/present_report/archive/present_report_v1.md`):
  `neg F1 macro (5 khía cạnh n lớn)` = trung bình F1 lớp âm trên 5 khía cạnh `n` = 48…174;
  `neg F1 micro (theo n)` = F1 lớp âm gộp mọi ô, trọng số = số ô.
- **`price`**: `n` âm = 6 ở `test`, **0 ở `val`** ⇒ mọi số `price` phải ghi kèm "n = 6, không kết luận".
  (Đợt này **KHÔNG** làm tập chẩn đoán giá - người dùng đã bỏ.)

## 3. Bench cần đánh bại - **ĐỔI 11/10/2026: dùng TRUNG BÌNH nhiều lượt, không dùng 1 lượt**

Lý do đổi: đợt 2 đo được biên nhiễu thật **sd = 0,11-0,16**, nên số của MỘT lượt là lượt-may-nhất, không phải
năng lực của cấu hình (xem mục 11).

| Thước đo | Công bố (đỉnh) | **v0 (`lr 2e-4`, TB 9 lượt ĐỘC LẬP)** | **Họ `lr 4e-4` (TB 12 lượt)** | Welch (họ − v0) |
| --- | ---: | ---: | ---: | --- |
| Accuracy macro (`paper`) | 97,70 | 98,09 (sd 0,14) | **98,28** (sd 0,11) | **p = 0,0035** ✅ |
| pos F1 macro | 98,49 | ~98,6 | ~98,90 | (theo lượt) |
| `neg F1 (5 khía cạnh n lớn)` | 88,23 | 93,60 (sd 0,64) | **94,38** (sd 0,39) | **p = 0,0070** ✅ |

**CẬP NHẬT CUỐI 12/10/2026 (tối, sau Đợt 8/8A).** Bảng trên đã đổi `n` của v0 từ **3 → 9 lượt độc lập** (6 hạt
giống 1-6 về trong Đợt 8), và **mức hơn của họ `lr 4e-4` nay ĐẠT p < 0,05 ở CẢ HAI trục**:
**t = 3,47 → p = 0,0035 (Acc)** · **t = 3,23 → p = 0,0070 (`neg F1`)**. Đối chứng: v0 cũ (3) vs v0 mới (6) -
cùng cấu hình - cho p = 0,93/0,90 ⇒ hai nhóm là một tổng thể, 6 lượt mới **không lệch hệ thống**.
Báo cáo chốt: `presentations/present_report/archive/present_report_v2.md`.

**SỬA 12/10/2026 (sau khi `exp042`/`exp049` về - xem mục 11).** Bảng trên trước đây ghi `v0 = 98,06` (đếm 4 lượt)
và `họ lr 4e-4 = 98,29` (11 lượt). Sai ở chỗ: `exp049` chạy lại cho **98,11 - trùng KHÍT `exp048` từng khía cạnh**
(cùng hạt giống huấn luyện 13) ⇒ nó là **BẢN SAO, không phải lượt thứ tư** ⇒ v0 lúc đó chỉ có **3 lượt độc lập**
(97,88 · 98,26 · 98,11 = hạt giống 42/7/13). Và `exp042` (98,24) đã lấp đủ nhóm `epochs 6` ⇒ họ `lr 4e-4` là
**12 lượt**. Ở `n = 3` đó, mức hơn đọc bằng Welch là **0,21 (Acc) · 0,30 (`neg F1`)** - **chưa** đạt p < 0,05;
chính vì thế mới cần 6 hạt giống v0 của **8A**, và tới 12/10 tối thì câu hỏi đã chốt (khối trên).

**Ngưỡng phát hiện (thay cho ±0,7 khi so 1-1):** một cấu hình mới chỉ được gọi là **"tăng"** khi hơn **> 0,25 ở
CẢ Accuracy macro VÀ một chỉ số F1 lớp âm có `n`**, với **n >= 3 lượt**. Số của MỘT lượt chỉ để tham khảo.

**Dư địa còn lại (đã định lượng 11/10/2026):** lớp âm còn **~22 ô sai / 467 (4,7 %)**, rải ở các khía cạnh `n`
LỚN. **Cập nhật 12/10/2026:** đường KẾT HỢP nay đã chứng minh là **cạn** (Đợt 6, mục 12: 9 bàn đạp, không cái nào
vượt > 0,25), và đường VẶN NÚT cũng cạn (mục 11). Sau ràng buộc mới của người dùng (**không thêm dữ liệu, không
đổi định nghĩa bài toán**), hai khe cuối là **(a) không gian PROMPT của LLM** (0/1/5 ví dụ từ `train` + lấy mẫu -
chính là giao thức công bố) và **(b) tiêu chí CHỌN CHECKPOINT** (`best_metric` = F1 lớp âm).

**ĐÓNG HAI KHE ĐÓ - 12/10/2026 (tối, kết quả Đợt 8):** cả hai đều **ÂM** và đã có bằng chứng -
(a) few-shot LLM: 0 ví dụ (97,62/0,9300) > 1 ví dụ (96,83/0,9062) > 5 ví dụ (96,41/0,9066), tất cả DƯỚI mốc LLM
sẵn có `exp009` (97,77/0,9470); (b) `best_metric: negative_f1`: **−0,17 Acc / −0,51 `neg F1`** khi ghép cặp theo
hạt giống. Thêm bỏ phiếu 3 mẫu LLM (RỖNG) ⇒ **16 bàn đạp đã thử, chỉ `lr` 2e-4 → 4e-4 là thắng có ý nghĩa**.
Ba lý do DUY NHẤT còn được phép mở lại kế hoạch: **thêm dữ liệu · đổi định nghĩa bài toán · model khác** -
chi tiết và chi phí ở `presentations/present_report/archive/present_report_v2.md` mục 5.

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

**KẾT QUẢ 11/10/2026 (10 lượt đã chạy) + CẬP NHẬT 12/10/2026 (2 lượt về sau cùng).**
Bảng `training_history.csv` đã phát hiện `exp049` **bị ngắt ở tầng huấn luyện rồi chạy tiếp** (bắt đầu ở
bước 400/epoch 2) ⇒ lượt đó không phải một lần rút thăm sạch (luật 11). Người dùng đã **xoá thư mục kết quả và
chạy lại HOÀN TOÀN** cả `exp042` và `exp049`; nay cả hai là lượt SẠCH:

- **`exp042` = 98,24** (`paper` macro; `training_history.csv` **29 dòng, đủ 6 epoch**; đọc 100 %) ⇒ nhóm
  `epochs 6` đủ **3 lượt**: 98,37 · **98,24** · 98,14 → **TB 98,25, sd 0,12** ⇒ xác nhận lại "4 cấu hình đồng hạng".
- **`exp049` = 98,11 - TRÙNG KHÍT `exp048`** (2.739 ô; `colour` 0,909 · `packing` 0,900 · `price` 0,000 ·
  `shipping` 0,974 · `smell` 0,909 · `stayingpower` 0,973 · `texture` 0,936). Nguyên nhân đã kiểm trong mã/tài
  liệu: trên **đường encoder**, khoá `decoding.seed` **CHÍNH LÀ HẠT GIỐNG HUẤN LUYỆN** (khởi tạo đầu phân loại,
  dropout, xới trộn dữ liệu) ⇒ `exp048` (←`exp004`, seed 13) và `exp049` (←`exp002`, seed 13) là **MỘT lần rút
  thăm**, không phải hai. **Luật 12** đã thêm vào `metrics.md` để chặn lỗi đếm này.

⇒ **v0 thực chất chỉ có 3 lượt ĐỘC LẬP**: seed 42 = 97,88 (`exp002`) · seed 7 = 98,26 (`exp004`) · seed 13 =
98,11 (`exp048` = `exp049`) → **TB 98,08, sd 0,19**. Con số cũ ghi trong kế hoạch (98,06) đếm lượt bị ngắt; con số
98,09 sẽ là đếm bản sao - cả hai đều sai cách đếm.

**Vì sao nhóm này BẮT BUỘC (không đổi):** `exp004` (đỉnh báo cáo CŨ) chỉ kém đỉnh mới **0,09** ⇒ nằm trong nhiễu.
Không có nhóm này thì KHÔNG được viết "đã vượt v0", chỉ được viết "cùng dải nhiễu".

**SÁU lượt MỚI của Đợt 8 (12/10/2026)** - mở rộng v0 từ 3 lên **9 lượt độc lập**, vì mức hơn "+0,20 Acc" hiện có
**p = 0,21 (Welch)** - chưa đạt p < 0,05 (mục 11):

| Lượt | Cha | Đổi 1 khoá | Ghi chú |
| --- | --- | --- | --- |
| `exp058` … `exp063` | `cafebert/lora/exp002` | `decoding.seed`: **1, 2, 3, 4, 5, 6** | 6 hạt giống MỚI THẬT (khác 42/7/13 đã có) |

**Ba lượt DỰ TRỮ (chỉ dùng ở Đợt 9 nếu `p` vẫn > 0,05):** `exp064` … `exp066` = cùng cha, `decoding.seed` **7, 8, 9**.
| Cấu hình | Vì sao vào nhóm | seed chạy thêm | Lượt |
| --- | --- | --- | --- |
| `exp021` | **đỉnh MỚI** (98,41) - giữ 3 kỷ lục | 7, 13 | `exp040`, `exp041` |
| `exp027` | 98,37 (`epochs 6`) | 7, 13 | `exp042`, `exp043` |
| `exp015` | **đỉnh CŨ** (98,35) - giữ kỷ lục `neg F1 (5 n lớn)` | 7, 13 | `exp044`, `exp045` |
| `exp028` | giữ kỷ lục `neg F1 (5 n lớn)` = 94,84 | 7, 13 | `exp046`, `exp047` |
| `exp004` (v0) | đỉnh của báo cáo CŨ (`presentations/present_report/archive/present_report_v0.md`) | 13 | `exp048` |
| `exp002` (v0) | cha gốc của cả họ CafeBERT | 13 | `exp049` |

**Ba lượt MỚI của Đợt 2b (11/10/2026) - ĐÃ THAY BẰNG 6 LƯỢT ở bảng trên (12/10/2026).** Lý do đổi: mức hơn
"họ `lr 4e-4` > v0" đọc lại bằng **Welch** cho **p = 0,21**, chứ không phải `p ~ 0,06` như bản ghi cũ (bản cũ đếm
`exp049` thành lượt thứ tư). Ba lượt (seed 1/2/3) chỉ đưa df lên ~6 ⇒ p ~ 0,05 (sát ngưỡng); **6 lượt** đưa df lên
~12 ⇒ **p ~ 0,015**. Số `exp058`/`exp059`/`exp060` nay thuộc 6 lượt mới (seed 1/2/3 nằm trong dãy 1-6).

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

### NHÓM 8 - Đổi chỉ số chọn `model/best` sang lớp âm - 1 sửa mã + 3 lượt - **HỒI SINH 12/10/2026 (thành 8D)**

Sửa `src/training/lora.py` + test ⇒ thêm một lựa chọn `checkpoints.best_metric` tính **F1 lớp âm**.
(`KNOWN_KEYS` đã có sẵn khoá `checkpoints.best_metric`, nên **chỉ sửa `lora.py` + test**; đo được `measure()` hiện
chỉ tính `accuracy_cell`, `accuracy_macro`, `sentiment_f1`, `sentiment_precision`, `sentiment_recall`,
`detection_f1` - **KHÔNG có F1 lớp âm**.)

**Lượt áp (chốt 12/10/2026): `exp055` · `exp056` · `exp057` = cha `cafebert/lora/exp021`, khác cha ĐÚNG 1 khoá
`checkpoints.best_metric: negative_f1`, seed 42/7/13.** (Bản 11/10/2026 ghi 3 cha khác nhau `exp015`/`exp021`/
`exp013`; đổi thành **3 seed của CÙNG một cha** để phép so chỉ còn MỘT biến, đúng quy ước của cả kế hoạch.)

**VÌ SAO HỒI SINH (12/10/2026):** đây là lượt **DUY NHẤT trong 15 lượt HOÃN nhắm TRỰC TIẾP lớp âm mà KHÔNG phá
tính so sánh** (không thêm dữ liệu, không đổi bài toán, không đổi khung chấm - chỉ đổi **lượt checkpoint được lưu
là `model/best`**). Lý do HOÃN cũ vẫn có giá trị một phần (`every_n_steps 50` ≈ `100`; `epochs 6` ≈ `3` ⇒ **mật độ**
checkpoint không phải nút thắt), nhưng lý do đó **chưa hề kiểm TIÊU CHÍ CHỌN khác đi**. Kỳ vọng: **thấp-trung bình**.

**Điều kiện tiên quyết:** NHÓM 11 đã kết luận `best_metric` hiện tại **có tác dụng** (ca A, mục 9.1) ⇒ đủ điều kiện.

### NHÓM 9 - Tầng PHƯƠNG PHÁP (0 GPU, dùng script có sẵn) - 3 việc - 🎯 **ĐANG LÀM (Đợt 6)**
| Việc | Lệnh | Cần trước |
| --- | --- | --- |
| Ensemble / biểu quyết 5 lượt dẫn đầu | `scripts/ensemble.py`, `scripts/vote.py` | NHÓM 7 |
| Dò ngưỡng theo khía cạnh (6/7 khía cạnh; `price` bị loại vì `val` không có ô âm) | `scripts/fit_thresholds.py` | 1 lượt `val` |
| Biểu quyết 3 seed (trung bình xác suất) | `scripts/vote.py` | NHÓM 6 |
| ~~Gộp hai tầng (`fuse_aspect.py`)~~ | - | **ĐÃ BỎ** cùng mọi kế hoạch liên quan tới `price` |

### NHÓM 10 - Nhánh model SINH (prompt) - **6 lượt** (3 few-shot + 3 lấy mẫu; chốt 12/10/2026)

| Lượt | Trạng thái 11/10/2026 |
| --- | --- |
| ~~`llama-3.1-8b-instruct/prompt-cot/exp001-003`~~ | **BỎ vì CHI PHÍ** (cùng cỡ 8B ⇒ dự kiến như `qwen3-8b`: **3 ngày Colab cho 3 lượt**). Quyền truy cập đã có nên **không còn là rào cản** - rào cản bây giờ là **chi phí** |
| ~~`qwen3-8b/prompt-cot/exp001-003`~~ | **HỦY sau khi chạy**: đọc được **1,05 % / 0,92 % / 0,12 %**; `token sinh TB` = **399,8 / 399,8 / 400,0** với trần 400 ⇒ **CHẠM TRẦN 100 %** vì `Qwen/Qwen3-8B` **bật suy nghĩ mặc định** |
| ~~`mistral-7b-instruct-v0.3/prompt-cot/exp001-003`~~ | **HỦY sau khi chạy**: đọc được **60,4 % / 72,2 % / 63,5 %** (~32 % trả lời **không có khối JSON**) |
| `qwen3-4b-instruct-2507/prompt-cot/exp022` (0 ví dụ) · `exp023` (1 ví dụ) · `exp024` (5 ví dụ) | **CÒN LẠI** - ví dụ few-shot **lấy từ `train`**, trên model **4B** (chạy ~2,3-2,8 h/lượt; đây là **đường tới hạn** của Đợt 8) |
| `qwen3-4b-instruct-2507/prompt-cot/exp025` · `exp026` · `exp027` | **MỚI 12/10/2026** - cùng cặp prompt như `exp023`, `decoding.mode: sample` với `decoding.seed` 1/2/3 ⇒ **3 mẫu THẬT SỰ khác nhau** (khác 3 "seed" encoder trước đây là 3 MODEL khác nhau) để chạy **biểu quyết tự-đồng-thuận** bằng `scripts/vote.py` (**0 GPU**) |

**Vì sao giữ phần lấy ví dụ từ `train`:** `qwen3-4b/prompt-cot/exp009` đang giữ **`neg F1 (5 n lớn)` = 94,70**
(#2 toàn dự án, chỉ sau `exp015` 0,08), mà **toàn bộ ví dụ hiện nay do người viết tay**, chưa lấy từ dữ liệu.

**Cách làm (bám sát luật 21 - cặp prompt + ví dụ BẤT BIẾN khi đã dùng) - ĐÃ LÀM 12/10/2026:** tạo **cặp MỚI**,
KHÔNG sửa file cũ:
- `configs/prompts/absa_cot_trainfshot_v1.txt` (có `{examples}`) - dùng cho lượt **1 ví dụ** và **5 ví dụ**;
- `configs/prompts/absa_cot_trainfshot_zeroshot_v1.txt` - **CÙNG câu chữ, chỉ bỏ khối "Ví dụ:"** (prompt có ô nhớ
  `{examples}` thì BẮT BUỘC khai `examples`, nên lượt 0 ví dụ cần file riêng; đặt tên `zeroshot` theo đúng quy ước
  đã có của dự án, `absa_cot_zeroshot_v1.txt`);
- `configs/prompts/examples/absa_cot_trainfshot_1shot_v1.txt` (1 ví dụ: **train dòng 59**) và
  `..._5shot_v1.txt` (5 ví dụ: **train dòng 23 · 24 · 59 · 103 · 112**) - ví dụ **1 ví dụ ⊂ 5 ví dụ**, phủ cả
  bốn mã 0/1/2/3.
Chú thích ghi nguồn **chỉ được nằm ở khối `#` ĐẦU file** (hàm `_split_examples_note` chỉ cắt khối đó; dấu `#`
sau dòng ví dụ đầu tiên sẽ bị gửi cho model). File **prompt** thì KHÔNG được có khối `#` nào - đã vấp lỗi này và
`show_prompt` bắt ngay.

**SỬA 12/10/2026 - công cụ kiểm rò rỉ CHƯA TỒN TẠI.** Bản kế hoạch cũ ghi
`python run_check_examples.py --hash ... --prompt ...`; tôi đã kiểm `scripts/` (**chỉ có `ci_checks.py`**) và
`src/workflow/checks.py` (**chỉ kiểm file prompt/ví dụ CÓ TỒN TẠI**, không kiểm rò rỉ) ⇒ **việc W5 là TẠO công cụ**
`scripts/check_examples.py`: đọc file ví dụ, tách các review ví dụ, đối chiếu với split `test` (không được trùng) và
với `train` (phải CÓ mặt); kèm test. Trước khi chạy `exp023`/`exp024` **PHẢI** ra **"không rò rỉ"**; đỏ thì **đổi
dòng khác trong `train`**, KHÔNG sửa ngưỡng.

### NHÓM 11 - CHẨN ĐOÁN trước khi tin 2 kết luận (0 GPU)
| Ca | Bằng chứng | Nghi vấn |
| --- | --- | --- |
| A. `cafebert/lora/exp002` == `exp007` | giống y hệt MỌI chỉ số (`98,88 / 0,9861 / 0,8473 / 0,9262 / 0,9378`) dù `exp007` khác cha đúng 1 khoá `checkpoints.best_metric: accuracy_cell` | `best_metric` **không có tác dụng**? |
| B. `phobert-base-v2/full/exp001` == `exp002` | khác `lr` 10 lần (`2e-4` vs `2e-5`) mà cùng `all acc 75,12` và `paper.cells 0` | nhánh `full` **có lỗi mã**? |

### NHÓM 12 - HỦY / sửa
| Việc | Chi tiết |
| --- | --- |
| **HỦY** `qwen3-4b-thinking-2507/prompt-cot/exp001`, `exp002` | Lí do người dùng chốt: **quá chậm, kể cả lượt DÒ**. Sửa 5 file: `docs/06_plan/archive/batches/present_plan_batch11.md`, `batch11_report.md`, `docs/04_experiments/01_models.md`, `handover/README.md`, `configs/models/qwen3-4b-thinking-2507.yaml` |
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
| Sửa **Phụ lục A** (3 lượt nay ĐÃ XONG; `cafebert/full/exp001` hỏng vì **phân kỳ**, không phải bị ngắt) | `presentations/present_report/archive/present_report_v1.md` |
| Thêm cột **nguồn** (v0 / đợt 11 / mới) + xếp hạng **2 trục** (Acc và F1) + gộp **đồng hạng** theo biên nhiễu | `presentations/present_report/archive/present_report_v1.md` |
| Ghi trạng thái HỦY `qwen3-4b-thinking` | 5 file ở NHÓM 12 |
| Cập nhật 12 -> 13 model (thêm Llama) | `docs/04_experiments/01_models.md` |
| Nếu lượt mới vượt top => viết `presentations/present_report/archive/present_report_v2.md`; `collect_reports.py` + commit phần nhẹ | `presentations/`, `data/reports/**` |

### NHÓM 15 - Đổi ĐỊNH NGHĨA BÀI TOÁN - **ĐÃ ĐỀ XUẤT rồi RÚT (12/10/2026), KHÔNG CHẠY**

**Đề xuất (bản nháp 12/10/2026):** đổi `neutral_policy` (`drop` → `as_negative`) và/hoặc `not_mentioned`
(`separate` → `as_class`) cho 6 lượt, vì tôi đo được **129/129 lượt đã chạy đều dùng ĐÚNG MỘT định nghĩa bài toán**
`(binary, drop, separate)` ⇒ đây là trục "chưa từng thử".

**NGƯỜI DÙNG BÁC ĐÚNG, và đây là bằng chứng đã kiểm trong mã:**

| Khoá | Tác động THẬT | Kết luận |
| --- | --- | --- |
| `neutral_policy` | `src/labels/binary.py::project` gọi `base.apply_neutral_policy(...)` (**đổi NHÃN**) và `experiment_run.py` L674 `labels.filter_label_map(label_map, label_space, neutral_policy)` (**đổi bảng nhãn HUẤN LUYỆN**) | **Đổi TẬP/BÀI TOÁN** ⇒ không so được với 97,70 / 88,23 (công bố **BỎ** ô neutral) |
| `not_mentioned` | `experiment_run.py` L674 **KHÔNG** dùng khoá này để lọc nhãn ⇒ **nhãn huấn luyện KHÔNG đổi**; chỉ `src/evaluation/scorers/base.py` L249-250 `if separate_not_mentioned: codes = [c for c in codes if c != NOT_MENTIONED]` + `scorers/prf.py` L10 (mã "không nhắc" thành **LỚP** thay vì thước `aspect_detection`) | **Đổi CÂY THƯỚC**, không phải thí nghiệm: cùng model, cùng dự đoán, khác số ⇒ tệ hơn cả đổi tập |

**Sai lầm của người lập kế hoạch:** lấy "chưa từng thử" làm "đáng thử". Sự thật là hai khoá này chưa từng thử **vì
chúng phá tính so sánh** - không phải vì bị bỏ sót. ⇒ Xoá hẳn NHÓM 15. Không có lượt nào của nhóm này được tạo.

**Luật bảo vệ mới (luật 14, đã thêm vào `metrics.md`):** bảng số CHÍNH chỉ nhận lượt giữ nguyên
**`(label_space: binary, neutral_policy: drop, not_mentioned: separate)`** và cùng phiên bản dữ liệu như công bố;
lượt khác bài toán chỉ được nằm ở **phụ lục** kèm dòng "khác bài toán".

**Hệ quả:** sau hai ràng buộc của người dùng (**không thêm dữ liệu** + **không đổi định nghĩa bài toán**), "trục mới"
chỉ còn **HAI khe**: **(a) không gian PROMPT của LLM** (NHÓM 10 - 0/1/5 ví dụ từ `train` + lấy mẫu; đây chính là
giao thức của công bố) và **(b) tiêu chí CHỌN CHECKPOINT** (NHÓM 8 - `best_metric` = F1 lớp âm).

### Danh sách HOÃN (**12 lượt** - cập nhật 12/10/2026) - **kèm LÝ DO và ĐIỀU KIỆN HỒI SINH**

Nghĩa của `HOÃN` (theo `docs/06_plan/archive/P7-P10/check_present_plan.md` §17 dùng chữ này): **chưa chạy BÂY GIỜ, KHÔNG xoá khỏi kế
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
| ~~`exp055` `exp056` `exp057`~~ | `checkpoints.best_metric` tính F1 lớp âm (+ 1 sửa mã) | **ĐÃ HỒI SINH 12/10/2026 (thành 8D)** - đây là lượt duy nhất trong 15 lượt HOÃN nhắm TRỰC TIẾP lớp âm mà KHÔNG phá tính so sánh. Lý do HOÃN cũ (`every_n_steps 50` ≈ `100`; `epochs 6` ≈ `3`) chỉ nói **mật độ** checkpoint không phải nút thắt, **chưa hề kiểm TIÊU CHÍ CHỌN** | đã hồi sinh; xem NHÓM 8 |

## 5. Các đợt (thứ tự chạy)

| Đợt | Nhóm | Việc | GPU | Trạng thái |
| --- | --- | --- | --- | --- |
| **0** | 11 + 12 (phần hủy) + 14 (Phụ lục A) | Sửa Phụ lục A · ghi trạng thái HỦY · chẩn đoán 2 nghi lỗi | 0 | ✅ **XONG** |
| **1** | 1, 2, 3, 4, 5 | 8 lượt ưu tiên: `exp020` `exp021` `exp024` `exp025` `exp027` `exp028` `exp030` `exp033` | ~2,5 h | ✅ **XONG** - *không lượt nào thắng* |
| **2** | 6 + 7 | **10 lượt seed** (`exp040`-`exp049`) + **5 lượt `val`** (`exp050`-`exp054`) | ~3,5 h | ✅ **XONG** (14/15 có `metrics.json`) |
| ~~2b~~ | 6 | ~~3 lượt v0 seed 1/2/3~~ | – | ❌ **HẤP THỤ VÀO ĐỢT 8** (12/10/2026: người dùng chạy được 15 lượt song song) |
| ~~3~~ | 4 + 5 | ~~`exp034` `exp035` `exp036` `exp037` `exp038`~~ | – | ⏸ **HOÃN cả 5** |
| ~~4~~ | 8 | ~~sửa mã `best_metric` + `exp055` `exp056` `exp057`~~ | – | ⬆ **HỒI SINH → 8D** |
| ~~5~~ | 10 | ~~3 lượt ví dụ lấy từ `train`~~ | – | ❌ **HẤP THỤ VÀO ĐỢT 8** (thành 8B + 8C: 6 lượt) |
| **6** | 9 | ensemble · dò ngưỡng 6/7 khía cạnh · biểu quyết 3 seed | **0** | ✅ **XONG 12/10/2026 - CẢ BA ÂM/RỖNG** (mục 12) |
| **8** | 6 + 10 + 8 | **15 LƯỢT CHẠY SONG SONG**: 6 v0 (seed 1-6) + 3 LLM few-shot (0/1/5 ví dụ) + 3 LLM lấy mẫu + 3 `best_metric` | 15 slot, **~3 h** (đường tới hạn = LLM 2,8 h) | 🟡 **ĐÃ GỬI 12/10/2026** - gói **034** (`...-ee24449-261012.zip`), ghim `5ec65f3`; chờ người dùng chạy |
| **9** | 6 + 10 + 8 + 9 | tuỳ kết quả Đợt 8: nhân bản biến thể THẮNG (≤ 6 lượt) + biểu quyết mẫu LLM (0 GPU) + luật lai (0 GPU) | ≤ 15 slot | ⬜ sau Đợt 8 |
| **7** | 14 | báo cáo chốt (+ `presentations/present_report/archive/present_report_v2.md` nếu Đợt 8/9 hơn > 0,25 ở CẢ 2 trục) | **0** | sau Đợt 8 (hoặc 9) |

**Tổng (12/10/2026):** **129 lượt đã chạy có `metrics.json`**; còn phải chạy **15 lượt Đợt 8** (+ tối đa 15 lượt
Đợt 9 tuỳ kết quả); **12 lượt HOÃN** (7 vặn-số + 5 Đợt 3). Đã HỦY/BỎ: `qwen3-4b-thinking` ×2, `qwen3-8b` ×3,
`mistral-7b` ×3, `llama-3.1-8b`, `vistral-7b`, nhánh `full` (1 lượt + 3 đã chạy), tập chẩn đoán giá, và **NHÓM 15**
(đổi định nghĩa bài toán - rút 12/10/2026, mục 4).
**Lưu ý thực thi (không đổi):** các lượt cần **GPU** không chạy được ở máy này; phần làm được ở đây là tạo notebook +
config + README, `--preflight-only`, ghim (`pin.py`) và đóng gói; **kết quả do người dùng chạy trên Colab**.

## 6. Sổ trạng thái (đánh dấu khi làm xong)

### Đợt 0 - 0 GPU
- [x] 0.1 **XONG 11/10/2026** - Sửa Phụ lục A của `presentations/present_report/archive/present_report_v1.md`: 3 lượt (`cafebert/lora/exp010`,
      `exp012`, `phobert-base-v2/lora/exp017`) nay **ĐÃ XONG**; chỉ `cafebert/full/exp001` hỏng.
      Commit `83a1376`
- [x] 0.2 **XONG 11/10/2026** - Ghi trạng thái **HỦY** cho `qwen3-4b-thinking-2507/prompt-cot/exp001-002`
      ở 5 file; tiện thể cập nhật luôn Llama = **đã mở quyền**. Commit `126657d`
- [x] 0.3 **XONG 11/10/2026** - Chẩn đoán ca A: **KHÔNG có lỗi** - `best_metric` ĐƯỢC đọc (mục 9)
- [x] 0.4 **XONG 11/10/2026** - Chẩn đoán ca B: **CÓ vấn đề thật** ở nhánh `full` (mục 9) -
      **cần người dùng quyết** trước khi làm NHÓM 12 phần `full`
- [x] 0.5 **XONG 11/10/2026** - Người dùng chốt **BỎ hẳn nhánh `full`** (cả 3 lượt thoái hoá) ⇒ NHÓM 12 bỏ
      `cafebert/full/exp002`; tổng encoder **37 -> 36** lượt; đã ghi "không dùng được" vào
      `docs/04_experiments/06_lora_encoder.md`, `batch11_report.md`, `docs/06_plan/archive/batches/present_plan_batch11.md`,
      `presentations/present_report/archive/present_report_v1.md`

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
      (`3f0cf82`) ⇒ **đo được biên nhiễu sd = 0,11-0,16**; **họ `lr 4e-4` ĐỒNG HẠNG**. Xem **mục 11**
- [x] **CHỐT LẠI 12/10/2026** - người dùng đã **xoá thư mục kết quả và chạy lại HOÀN TOÀN** `exp042` và `exp049`;
      cả hai nay là lượt SẠCH. Phát hiện: **`exp049` ≡ `exp048` từng ô** (cùng hạt giống huấn luyện 13) ⇒ v0 chỉ
      có **3 lượt ĐỘC LẬP** (TB 98,08) và mức hơn so v0 đọc lại bằng Welch là **p = 0,21 (Acc) / 0,30 (`neg F1`)**
      - KHÔNG phải 0,06/0,10 như bản ghi cũ. File nhẹ của hai lượt **chưa vào git** ⇒ việc **W1**
      → **CẬP NHẬT 12/10 tối:** `exp042`/`exp049` đã vào git (`006544c`); 6 hạt giống v0 của **8A** đưa v0 lên
      **9 lượt độc lập** ⇒ Welch **p = 0,0035 (Acc) / 0,0070 (`neg F1`)** ⇒ **ĐÃ ĐẠT p < 0,05** (mục 14.A)

### Đợt 8 - 15 lượt SONG SONG (mới 12/10/2026; THAY cho Đợt 2b + Đợt 5) - nhóm 6 + 10 + 8

**Việc 0 GPU phải xong TRƯỚC khi đóng gói:**

| # | Việc | File chạm tới |
| --- | --- | --- |
| **W1** | Commit file nhẹ `exp042`/`exp049` + `collect_reports.py` + dựng lại 5 bảng gộp | `experiments/cafebert/lora/exp04{2,9}/results/**`, `data/reports/**` |
| **W2** | **Luật 12** (đường encoder: cùng `decoding.seed` = cùng hạt giống ⇒ MỘT lần rút thăm) · **Luật 13** (cấm lấy `neg F1 macro (7)` làm kỷ lục - `price` 5-6 ô + `packing` 9-10 ô chi phối) · **Luật 14** (bảng chính chỉ nhận cùng bài toán + cùng phiên bản dữ liệu) | `docs/04_experiments/metrics.md` |
| **W3** | Sửa số: v0 = 98,08 (n=3) · Welch 0,21/0,30 · thêm `exp042`/`exp049`; bỏ câu "p ≈ 0,06/0,10" | mục 11 · `08_experiment_rationale.md` · `presentations/present_report/archive/present_report_v1.md` |
| **W4** | Bảng xếp hạng **`neg F1 (5 n lớn)` cho MỌI lượt `test`** | `data/reports/**` |
| **W5** | **TẠO công cụ** kiểm rò rỉ ví dụ few-shot + test | `scripts/check_examples.py`, `tests/workflow/**` |
| **W6** | Sửa nhỏ: `checkpoints.best_metric` nhận **F1 lớp âm** + test | `src/training/lora.py`, `tests/training/**` |
| **W7** | Viết cặp prompt + ví dụ MỚI (0/1/5 ví dụ) từ `train` | `configs/prompts/absa_cot_trainfshot_v1.txt` + `configs/prompts/examples/absa_cot_trainfshot_*` |
| **W8** | Tạo 15 config + README (`new_experiment.py`) → `--dry-run` → ghim (`pin.py`) → **gói 034** (`build_package.py`), `ci_checks` XANH | `experiments/**`, `handover/packages/034` |

- [x] **XONG TOÀN BỘ 12/10/2026** - thứ tự đã làm đúng kế hoạch: **W1** (`006544c` commit file nhẹ
      `exp042`/`exp049` + `03269bf` dựng lại bảng) → **W2+W3** (`5d7aefb`: luật 12-14 + sửa số 3 tài liệu) →
      **W4** (`fd48659`: thêm 2 cột `neg_f1_big5`/`neg_f1_macro7` vào bảng chuẩn, +4 test) → **W5** (`99de73a`:
      công cụ kiểm rò rỉ + 10 test + đối chứng âm trên dữ liệu thật) → **W7** (`d232442` cặp prompt/ví dụ mới)
      → **W6** (`830efbd`: `best_metric: negative_f1` + bộ chặn lỗi im lặng) → **W8** (`dce35af` tạo 15 config,
      `5ec65f3` sửa tên prompt 0-ví-dụ, `ee24449` ghim lại, `a5ce2f0` gói **034**)
- [x] **15 lượt đã TẠO + GHIM + ĐÓNG GÓI**: 8A `exp058`-`exp063` · 8B `exp022`-`exp024` · 8C `exp025`-`exp027` ·
      8D `exp055`-`exp057`. Cửa kiểm rò rỉ: **1-shot 1/1** và **5-shot 5/5** ví dụ *có trong `train`* và
      **KHÔNG RÒ RỈ**. `show_prompt` xác nhận phép so 0/1/5 ví dụ chỉ có **MỘT biến** (cùng prompt, cùng
      system, cùng không gian nhãn). `ci_checks` **XANH** ở commit ghim `5ec65f3`.
      Gói: `handover/out/SentimentX-goi-034-ee24449-261012.zip` (31 file: 15 notebook + 15 README + MANIFEST).
- [x] **✅ NGƯỜI DÙNG ĐÃ CHẠY XONG (12/10/2026 tối): 15/15 lượt `FINISHED`.** File nhẹ đã commit
      (`4b601c8`: 99 file), bảng chuẩn dựng lại, **mục 14** đã điền. Kết quả: **8A ĐẠT** (v0 lên 9 lượt độc
      lập ⇒ Welch **p = 0,0035 Acc / 0,0070 `neg F1`**), **8B/8C/8D đều ÂM**. ⇒ **Đợt 9 KHÔNG mở**; đi **Đợt 7**.
      Cửa kiểm gói + 2 ca `RESUME` + 1 lỗi công cụ đã sửa: xem **mục 14**.

### Đợt 9 - làn 2, chỉ mở khi Đợt 8 có tín hiệu (mới 12/10/2026) - ❌ **ĐÃ ĐÓNG 12/10/2026 (tối)**

Bảng điều kiện dưới đây là bảng CHỐT TRƯỚC khi thấy `test` của Đợt 8; đối chiếu thực tế ở **mục 14.C**:
cả ba hàng "có tín hiệu" đều KHÔNG thoả (LLM thua, 8D thua, `p` đã < 0,05) ⇒ không tiêu thêm GPU.
Duy chỉ có hàng cuối "cả ba hoà/thua" được kích hoạt ⇒ **đi thẳng Đợt 7**.

| Nếu Đợt 8 cho | Đợt 9 làm | Thực tế |
| --- | --- | --- |
| LLM hơn >= 0,25 ở `neg F1 (5 n lớn)` | 6 lượt LLM (biến thể 5-ví-dụ khác + 3 lượt lấy mẫu nữa) rồi **biểu quyết 5 mẫu**; nếu vẫn hơn thì bật lại **luật lai encoder+LLM** (`scripts/fuse.py`, **0 GPU**) | ❌ LLM **thua** (−0,017 ở lượt tốt nhất) |
| 8D thắng >= 0,25 | nhân bản `best_metric: negative_f1` sang 2 cấu hình còn lại (`r 16`, `every_n_steps 50`) × 3 seed | ❌ 8D **thua** (−0,17 Acc / −0,51 `neg F1`) |
| p(v0) vẫn > 0,05 | thêm 3 lượt v0 DỰ TRỮ (`exp064`-`exp066`, seed 7/8/9) | ❌ p = **0,0035 / 0,0070** ⇒ không cần |
| Cả ba hoà/thua | **không tiêu GPU nữa**, đi thẳng Đợt 7 và ghi rõ trần | ✅ **ĐANG ĐI** |

### Đợt 3 - ĐÃ CHUYỂN HOÃN (11/10/2026)
- [x] **5 lượt chuyển HOÃN** (`exp034` `exp035` `exp036` `exp037` `exp038`) vì Đợt 2 chứng minh **các trục
      siêu tham số đã BÃO HOÀ** (sd 0,11-0,16 > mọi khác biệt có thể tạo ra) - lý do + điều kiện hồi sinh ở mục 4
- [x] **7 lượt vặn-số đã HOÃN từ trước** (`exp022` `exp023` `exp026` `exp029` `exp031` `exp032` `exp039`)

### Đợt 4 - ĐÃ CHUYỂN HOÃN (11/10/2026)
- [x] **HOÃN 3 lượt + 1 sửa mã** (`exp055` `exp056` `exp057`) vì Đợt 2 cho thấy **chọn checkpoint KHÔNG phải
      nút thắt** (`every_n_steps 50` ≈ `100`; `epochs 6` ≈ `3`) - lý do + điều kiện hồi sinh ở mục 4
- [x] **BỎ** `cafebert/full/exp002` (nhánh `full` đã bị bỏ hẳn - mục 9.2)

### Đợt 5 - **ĐÃ HẤP THỤ VÀO ĐỢT 8** (12/10/2026)
- [x] **BỎ phần Llama 11/10/2026** (chi phí: cùng cỡ 8B như `qwen3-8b` = 3 ngày/3 lượt)
- [x] **Chuyển sang 8B + 8C** (6 lượt) vì người dùng chạy được 15 lượt song song: 3 lượt few-shot
      (`exp022`-`exp024`) + 3 lượt lấy mẫu (`exp025`-`exp027`)
- [x] Sửa lại điều kiện kiểm rò rỉ: công cụ `run_check_examples.py` **KHÔNG tồn tại** trong repo ⇒ việc **W5** là
      **tạo** `scripts/check_examples.py`; xem NHÓM 10

### Đợt 6 - 0 GPU - ✅ **XONG 12/10/2026: CẢ BA VIỆC ÂM/RỖNG** (chi tiết ở mục 12)
- [x] **6.1** Ensemble 5 lượt dẫn đầu - tổng quát thành **6 model KHÁC NHAU** (như tài liệu 09_fusion.md chỉ ra:
      chốt trọng số trên `val`, áp lên `test`) ⇒ **97,87 / 0,795 < `exp013` 98,33 / 0,889** = THUA
- [x] **6.1b** Ensemble 5 lượt `cafebert` (trọng số đều) ⇒ **98,26 / 0,856** ≈ TB họ `lr 4e-4` (98,28) = không lợi
- [x] **6.2** Dò ngưỡng theo khía cạnh (6/7; `price` để nguyên) ⇒ **RỖNG**: lưới quét cho thấy F1 âm **tăng đơn
      điệu VỀ điểm gốc** (`colour` 0,788 ở ngưỡng 0,05 → 0,877 khi không ngưỡng) ⇒ mọi ngưỡng đều LÀM HỎNG
- [x] **6.3** Biểu quyết 3 seed (`exp021`/`exp040`/`exp041`) ⇒ acc 98,41 (ngang `exp021`) nhưng `neg F1 (7)`
      **0,809** < 0,886 (thấp hơn cả `exp040` 0,813); 11.361 ô đủ phiếu, chỉ **8 ô hoà**
- [x] **Luật đọc đã áp đúng:** cả ba đều so với TỪNG thành viên trên cùng tập; **không việc nào vượt > 0,25 ở cả
      Acc và `neg F1`** ⇒ không sinh ra kết quả để báo cáo, bằng chứng giữ trong `data/reports/fusion/**`

### Đợt 7 - 0 GPU - báo cáo chốt - ✅ **XONG 12/10/2026 (tối)**
- [x] File nhẹ 15 lượt vào git (`4b601c8`) + **bảng chuẩn dựng lại** (`4051004` thêm cột `acc_paper_macro`;
      `b783431` dựng lại 144 dòng) + **mục 14** đã điền (`802306a`)
- [x] Bằng chứng 0 GPU cho 8C: `data/reports/fusion/vote_llm_1shot.json` (+ `inputs/…__nhan_tung_o.csv`);
      đường bỏ phiếu có **lỗi thật đã sửa** (`36736b0`, +3 test)
- [x] **`presentations/present_report/archive/present_report_v2.md`** (`75f4de7`): số chính **98,283 / 94,38 vs v0 98,091 / 93,60 (Welch p = 0,0035 /
      0,0070)**; ba kết quả ÂM; **16 bàn đạp** đã thử; ba lý do còn được phép mở lại
- [x] Sửa `docs/04_experiments/08_experiment_rationale.md` (bảng họ + Welch + hai khe đã đóng) và
      `presentations/present_report/archive/present_report_v1.md` (trỏ v2); `handover/README.md` ghi kết quả
- [x] `ci_checks` **XANH** + `unittest` **1120 test** (1 lỗi môi trường có sẵn, 0 FAIL) → commit → **đã push**
- [ ] **Gói 035: KHÔNG dựng** - không còn notebook nào cần chạy trên Colab (Đợt 9 đã đóng), và mọi kết quả đã
      nằm trong git. Chỉ dựng khi cần gửi lại bảng chuẩn: `python scripts/build_package.py`

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
| 11/10/2026 | Thay đổi (người dùng chốt) | **BỎ hẳn nhánh `full`** khỏi kế hoạch (lý do: full fine-tune bị overfit/thoái hoá). Đã ghi "không dùng được" vào `06_lora_encoder.md`, `batch11_report.md`, `docs/06_plan/archive/batches/present_plan_batch11.md`, `presentations/present_report/archive/present_report_v1.md` | Tổng encoder **37 -> 36**; Đợt 4 nay chỉ còn NHÓM 8; 3 lượt `full` giữ làm bản ghi |
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
| 12/10/2026 | **Đợt 6 (kết quả)** | Cả 3 việc kết hợp **ÂM/RỖNG**: ensemble 6 model 97,87/0,795; ensemble 5 lượt cafebert 98,26/0,856; ngưỡng theo khía cạnh **rỗng** (lưới quét tăng đơn điệu về điểm gốc); biểu quyết 3 seed acc 98,41 nhưng `neg F1 (7)` 0,809 | Ghi **mục 12**; cộng 5 bàn đạp cũ = **9 bàn đạp, không cái nào vượt > 0,25** ⇒ đường KẾT HỢP cạn |
| 12/10/2026 | Ghi nhận (2 lượt về sau) | Người dùng **xoá kết quả cũ + chạy lại hoàn toàn** `exp042` (98,24) và `exp049` (98,11) | Phát hiện **`exp049` ≡ `exp048` TỪNG Ô** ⇒ v0 chỉ có **3 lượt độc lập**; thêm **luật 12** |
| 12/10/2026 | Sửa số (số cũ lạc quan) | Mức hơn của họ `lr4e-4` so v0 đọc lại bằng **Welch: p = 0,21 (Acc) / 0,30 (`neg F1`)** - bản ghi cũ "t ≈ 2,6, p ≈ 0,06" vừa đếm `exp049` thành lượt thứ tư vừa dùng kiểm định gộp phương sai | Sửa mục 3, mục 11, `08_experiment_rationale.md`, `presentations/present_report/archive/present_report_v1.md` (`5d7aefb`) |
| 12/10/2026 | Ràng buộc mới (người dùng chốt) | **Chạy được 15 thử nghiệm CÙNG LÚC** · **tuyệt đối KHÔNG thêm dữ liệu** | Gộp Đợt 2b + Đợt 5 thành **Đợt 8 (15 slot)**; xoá mọi ý dùng dữ liệu (distillation, hard-negative mining) |
| 12/10/2026 | **RÚT NHÓM 15** (đề xuất rồi bỏ) | Đề xuất đổi `neutral_policy`/`not_mentioned` cho 6 lượt; kiểm mã cho thấy `neutral_policy` **đổi NHÃN + bảng nhãn huấn luyện** còn `not_mentioned` chỉ **đổi khung chấm** ⇒ cả hai phá tính so sánh với công bố | Xoá NHÓM 15; thêm **luật 14** để chặn tái diễn (mục 4) |
| 12/10/2026 | **Đợt 8: TẠO + GHIM + ĐÓNG GÓI xong** | 15 config/notebook (`exp055`-`exp057`, `exp058`-`exp063`, `exp022`-`exp027`); cửa kiểm rò rỉ **1-shot 1/1 · 5-shot 5/5** đều "KHÔNG RÒ RỈ"; `show_prompt` xác nhận biến duy nhất = **số ví dụ**; `ci_checks` XANH ở commit ghim | Gói **034** = `handover/out/SentimentX-goi-034-ee24449-261012.zip` (31 file; bản đầu `b438241` bị thay sau khi **sửa tên prompt 0-ví-dụ** `…_0shot_…` → `…_zeroshot_…` cho đúng tập ĐÓNG của `test_prompts.py`); commit `dce35af` → `5ec65f3` → `ee24449` → `a5ce2f0` |
| 12/10/2026 | Ghi nhận (cách làm) | Lại dùng script dùng-một-lần trong `_scratch/` (`make_d8_configs.py`, `leak_control.py`, `stats_grp.py`) để tạo 15 config và chạy đối chứng | Có **lỗi thật đã sửa**: prompt KHÔNG được có khối `#` ở đầu (chỉ file VÍ DỤ mới có) - `show_prompt` bắt được ngay |
| 12/10/2026 | **Đợt 8 (KẾT QUẢ)** | 15/15 lượt về đủ: mỗi thư mục ĐÚNG 1 lượt, `FINISHED`, ghim `5ec65f3`, không `errors.json`; `training_history.csv` 14 dòng (bước 100→1150) ⇒ không lượt nào bị ngắt; LLM đọc 99,94-100 %, token sinh 218-223/400. **8A ĐẠT: v0 lên 9 lượt độc lập ⇒ Welch p = 0,0035 (Acc) / 0,0070 (`neg F1`)**; **8B/8C/8D đều ÂM** (LLM few-shot 97,62→96,83→96,41 · bỏ phiếu `neg F1` 0,8039 · `best_metric` −0,17/−0,51) | Điền **mục 14**; **Đợt 9 ĐÓNG**; đi **Đợt 7** |
| 12/10/2026 | Phát hiện (cửa kiểm gói) | 2 lượt LLM bị Colab **ngắt ở tầng ĐÁNH GIÁ** rồi chạy tiếp (`exp024` tái dùng 652 ô, `exp027` 1.336 ô; lượt đầu `INTERRUPTED`) - khác hẳn ngắt tầng HUẤN LUYỆN của luật 11 | Thêm **luật 15** vào `metrics.md`: dùng được nếu `FINISHED` + `read_rate.valid` + số trong dải anh em, và **phải khai số ô tái dùng** |
| 12/10/2026 | **LỖI CÔNG CỤ (thật, đã sửa)** | `fusion.vote` gọi `dict(pred)` nên **SẬP** (`TypeError: 'NoneType' object is not iterable`) khi một lượt có review KHÔNG đọc được (`preds[i] = None`). Lượt encoder của Đợt 6 đọc được 100 % nên lỗi **ẩn**; lượt LLM (99,94 %) mới lộ | Sửa `src/evaluation/fusion.py` (bỏ sample không đọc được khỏi bảng tra; hàng của lượt đầu giữ `None`, chỉ điền ô CÓ phiếu) + **3 test** mới trong `tests/evaluation/test_fusion.py`; chạy lại `vote.py` thành công |
| 12/10/2026 | Cải thiện bảng chuẩn | Số tiêu đề "Acc macro (paper)" trước đây chỉ nằm trong văn xuôi ⇒ thêm cột **`acc_paper_macro`** (`scores_paper.accuracy.macro`) vào `experiment_registry` + 3 test; ghi vào bảng "Nguồn số duy nhất" của `metrics.md` | `src/reporting/reports.py`, `tests/reporting/test_reports.py`; `collect_reports.py` dựng lại (144 dòng) |


## 8. Đã xong TRƯỚC khi mở sổ này (11/10/2026)

| Việc | Commit |
| --- | --- |
| Dọn `presentations/`: chỉ còn báo cáo; bỏ 4 tài liệu cũ + 6 CSV; `present_report.md` -> `presentations/present_report/archive/present_report_v0.md` | `fc62424` |
| Thêm `presentations/present_report/archive/present_report_v1.md` (4 thước đo F1 có trọng số `n` + giữ nguyên Bảng 3-6 cũ) | `7b34fa2` |
| Trỏ lại 3 link tài liệu sang `presentations/present_report/archive/present_report_v1.md` | `e87cc5c` |
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
   được" vào `06_lora_encoder.md`, `batch11_report.md`, `docs/06_plan/archive/batches/present_plan_batch11.md`, `presentations/present_report/archive/present_report_v1.md`.

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

**CẬP NHẬT 12/10/2026** - 15/15 lượt đã có `metrics.json` (`exp042` và `exp049` đã được người dùng xoá kết quả cũ và
chạy lại hoàn toàn). Số dưới đây CHẤM LẠI bằng engine của dự án (`accuracy_paper.macro` và `neg F1 (5 n lớn)` =
trung bình F1 lớp âm của 5 khía cạnh `n` lớn: `colour` 54 · `shipping` 172 · `smell` 48 · `stayingpower` 95 ·
`texture` 83).

| Cấu hình (cha + các seed) | Acc macro từng lượt | **TB** | sd | **neg F1 (5 n lớn) TB** | sd |
| --- | --- | ---: | ---: | ---: | ---: |
| `lr4e-4, r8` (`exp021` 42 · `exp040` 7 · `exp041` 13) | 98,41 · 98,38 · 98,13 | **98,31** | 0,15 | 94,59 | 0,30 |
| `lr4e-4, r16` (`exp015` 42 · `exp044` 7 · `exp045` 13) | 98,35 · 98,17 · 98,37 | **98,30** | 0,11 | 94,33 | 0,61 |
| `lr4e-4, every_n_steps 50` (`exp028` 42 · `exp046` 7 · `exp047` 13) | 98,31 · 98,16 · 98,37 | **98,28** | 0,11 | 94,49 | 0,40 |
| `lr4e-4, epochs 6` (`exp027` 42 · **`exp042` 7** · `exp043` 13) | 98,37 · **98,24** · 98,14 | **98,25** | 0,12 | 94,11 | 0,12 |
| **họ `lr 4e-4` gộp (12 lượt)** | — | **98,28** | 0,11 | **94,38** | 0,39 |
| **`lr 2e-4` = v0 (3 lượt ĐỘC LẬP)** | 97,88 · 98,26 · 98,11 | **98,08** | 0,19 | **93,65** | 0,91 |

`neg F1 (5 n lớn)` **từng lượt** - `r8`: 94,640 · 94,860 · 94,260 · `r16`: 94,780 · 93,640 · 94,560 ·
`step50`: 94,840 · 94,060 · 94,560 · `epochs6`: 94,060 · 94,020 · 94,240 · `v0`: **92,620** · 94,320 · 94,020.

### Bốn kết luận (số đã sửa 12/10/2026)

1. **BỐN cấu hình trong họ `lr 4e-4` ĐỒNG HẠNG** (TB 98,25-98,31, sd 0,11-0,15 ⇒ chênh giữa các TB ≤ 0,06 chỉ bằng
   1/3-1/2 sd; nhóm `epochs 6` nay **đủ 3 lượt** nhờ `exp042` = 98,24). ⇒ **`r 8` vs `r 16`, `epochs 3` vs `6`,
   `every_n_steps 100` vs `50`: KHÔNG có khác biệt đo được.** `exp021` (98,41) **không phải "đỉnh" riêng**.
2. **Họ `lr 4e-4` hơn v0**: **+0,20 Acc** (98,283 vs 98,083) và **+0,72 `neg F1 (5 n lớn)`** (94,377 vs 93,653).
   **Đo lại bằng 2 kiểm định (2 phía, `scipy`), với n ĐÚNG của v0 = 3 lượt độc lập:**

   | Trục | Chênh | **Welch** t (df) → p | Gộp phương sai t (df) → p |
   | --- | ---: | --- | --- |
   | Accuracy macro | +0,20 | 1,74 (2,3) → **p = 0,206** | 2,50 (13) → p = 0,027 |
   | `neg F1 (5 n lớn)` | +0,72 | 1,35 (2,2) → **p = 0,300** | 2,23 (13) → p = 0,044 |

   ⇒ **Kết luận phụ thuộc hoàn toàn vào giả định phương sai.** Welch (đúng hơn khi `n` và sd lệch nhau - v0 sd 0,19
   gấp đôi họ kia 0,107) cho **p ≈ 0,21 / 0,30 ⇒ CHƯA đạt p < 0,05**. Bản ghi cũ ("t ≈ 2,6, p ≈ 0,06") vừa đếm
   `exp049` thành lượt thứ tư vừa dùng kiểm định gộp phương sai. ⇒ **Đợt 8/8A (6 lượt v0 nữa) là cách duy nhất để
   chốt**: v0 lên 9 lượt độc lập ⇒ Welch df ≈ 12 ⇒ p ≈ 0,015.
3. **Không lấy số của MỘT lượt làm kết luận** (luật 10): `exp021` 98,41 nhưng TB của chính nó **98,31**; đỉnh báo cáo
   CŨ `exp004` 98,26 nhưng TB họ v0 **98,08**.
4. **Thước đo `neg F1 macro (7)` là THƯỚC ĐO NHIỄU - cấm dùng làm kỷ lục (luật 13 mới):** trong CÙNG cấu hình `r8`,
   3 seed cho `neg F1 (7)` = **0,886 · 0,813 · 0,796** nhưng `neg F1 (5 n lớn)` = **94,640 · 94,860 · 94,260**
   (chênh 0,006). Nguyên nhân: `price` (5-6 ô) cho F1 **0,571 · 0,000 · 0,000** và `packing` (9-10 ô) 0,900 · 0,947 ·
   0,857 ⇒ 1-2 ô đảo chiều làm `neg F1 (7)` nhảy 0,09. ⇒ "kỷ lục `neg F1 (7)` = 0,886 của `exp021`" là **artefact của
   4/7 ô giá**; trên thước đo có `n`, **`exp040` (94,860) mới là lượt tốt nhất** của nhóm `r8`.
5. **Dư địa còn lại nằm ở lớp ÂM, rải ở khía cạnh `n` LỚN**: `exp021` còn **~22 ô sai / 467 ô âm (4,7 %)**
   (`colour` 5,2 · `texture` 4,4 · `smell` 3,7 · `shipping` 3,4 · `stayingpower` 2,0 · `price` 2,1 · `packing` 1,0).
   **Cập nhật 12/10/2026:** đường KẾT HỢP đã chứng minh CẠN (Đợt 6, mục 12: 9 bàn đạp, không cái nào > 0,25) ⇒ hai khe
   còn lại là **prompt/few-shot của LLM** (NHÓM 10) và **tiêu chí chọn checkpoint** (NHÓM 8).

### Hai bất thường (đã xử lý xong 12/10/2026)

- **`exp042`**: 11/10 chạy xong trên Colab nhưng thiếu file nhẹ ở máy. **12/10: người dùng xoá kết quả và chạy lại
  hoàn toàn** ⇒ **98,24**, `training_history.csv` 29 dòng đủ 6 epoch, đọc 100 %, lượt SẠCH.
- **`exp048` vs `exp049`**: 11/10 lệch 98,11 vs 98,00 vì `exp049` bị ngắt ở tầng huấn luyện (luật 11). **12/10: chạy
  lại hoàn toàn ⇒ 98,11 - TRÙNG KHÍT `exp048` TỪNG Ô** (`colour` 0,909 · `packing` 0,900 · `price` 0,000 ·
  `shipping` 0,974 · `smell` 0,909 · `stayingpower` 0,973 · `texture` 0,936; cùng 2.739 ô). Nguyên nhân: trên **đường
  encoder**, `decoding.seed` **CHÍNH LÀ HẠT GIỐNG HUẤN LUYỆN** ⇒ `exp048` (←`exp004`, seed 13) và `exp049` (←`exp002`,
  seed 13) là **MỘT lần rút thăm**. ⇒ **Luật 12** (mới) + v0 chỉ có **3 lượt độc lập**.

### Hệ quả cho kế hoạch (đã cập nhật trong file này)

- Bàn đo giữ **TRUNG BÌNH nhiều lượt** (mục 3); ngưỡng phát hiện **> 0,25 với n >= 3**.
- **Đợt 3 + Đợt 4**: Đợt 3 vẫn HOÃN (5 lượt); **Đợt 4 HỒI SINH thành 8D** (3 lượt + 1 sửa mã).
- **Đợt 2b (3 lượt) → 8A (6 lượt)** vì p thật là 0,21 chứ không phải 0,06.
- **Đợt 6 (KẾT HỢP) đã chạy và CẠN** (mục 12) ⇒ toàn bộ trọng tâm chuyển sang **Đợt 8**.

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
**không sinh ra kết quả để báo cáo** (không có `presentations/present_report/archive/present_report_v2.md`). Bằng chứng được GIỮ trong
`data/reports/fusion/` (kèm `inputs/` để tái lập từ repo, không cần Drive).

⇒ Cùng với việc các trục siêu tham số đã bão hoà (mục 11), **bàn đạp "kết hợp" nay cũng đã cạn**: dự án đang ở
trần của cấu hình hiện tại **~98,29 Acc / ~94,41 neg F1 (`n` lớn)**, vượt công bố **+0,59 Acc / +6,18 F1 âm**.
Muốn vượt trần này phải đổi **loại** (thêm dữ liệu / đổi loại lỗi), không phải đổi **núm**.

### Toàn cảnh 9 bàn đạp kết hợp đã thử (để khỏi thử lại)

| Bàn đạp | Tệp | Acc (`paper` macro) | neg F1 macro (7) | So `exp013` (98,33 / 0,889) |
| --- | --- | ---: | ---: | --- |
| ensemble 6 model khác nhau (Đợt 6) | `fusion/ensemble.json` | 97,87 | 0,795 | thua cả hai |
| ensemble 5 lượt cafebert (Đợt 6) | `fusion/ensemble_cluster.json` | 98,26 | 0,856 | thua cả hai |
| ngưỡng theo khía cạnh (Đợt 6) | `fusion/thresholds_applied.json` | 98,33 | 0,889 | **bằng** (rỗng) |
| biểu quyết 3 seed (Đợt 6) | `fusion/vote.json` | **98,41** | 0,809 | acc +0,08 · F1 −0,077 |
| router theo khía cạnh (07/10) | `fusion/router_aspect_accuracy.json` | 97,93 | 0,855 | thua cả hai |
| router theo khía cạnh, 2 model (07/10) | `fusion/router_aspect_accuracy_2model.json` | 96,02 | 0,754 | thua cả hai |
| router theo khía cạnh, 6 model (07/10) | `fusion/router_aspect_accuracy_6model.json` | 97,72 | 0,795 | thua cả hai |
| gộp HAI TẦNG theo khía cạnh (07/10) | `fusion/fuse_aspect_test.json` | 95,87 | 0,816 | thua cả hai |
| **luật lai encoder + LLM (05/10)** | `fusion/fuse.json` | 98,02 | **0,898** | acc −0,31 · F1 **+0,009** |

⇒ **9 bàn đạp, KHÔNG bàn đạp nào vượt > 0,25 trên CẢ HAI trục** so với lượt mạnh nhất
(`cafebert/lora/exp013` 98,33 / 0,889). Gần nhất là **luật lai encoder + LLM** (hơn 0,009 F1 âm, kém 0,31 Acc;
lại dùng encoder `phobert-base-v2` yếu, không phải `cafebert`) - vẫn xa ngưỡng 0,25.

## 13. CHỐT KẾ HOẠCH 12/10/2026 - Đợt 8 (15 slot) · 3 luật mới · RÚT NHÓM 15

Người dùng chốt: **chạy được 15 thử nghiệm CÙNG LÚC trên Colab** · **tuyệt đối không thêm dữ liệu** · bám kế hoạch.
Ba hệ quả đã ghi vào file này:

1. **Gộp Đợt 2b + Đợt 5 thành Đợt 8 (15 lượt / 1 làn)** - mục 5 và mục 6.
2. **RÚT NHÓM 15** (đổi định nghĩa bài toán) vì phá tính so sánh với công bố - mục 4 NHÓM 15.
3. **Hồi sinh Đợt 4 thành 8D** (`best_metric` = F1 lớp âm) - mục 4 NHÓM 8.

### 15 lượt của Đợt 8 (mỗi lượt khác cha ĐÚNG 1 khoá · cùng bài toán `(binary, drop, separate)` · cùng dữ liệu)

| Nhóm | Lượt | Cha | Khoá đổi | Seed | ~Giờ | Trả lời câu gì |
| --- | --- | --- | --- | --- | ---: | --- |
| **8A** | `cafebert/lora/exp058`–`exp063` | `exp002` (v0) | `decoding.seed` = 1,2,3,4,5,6 | 1-6 | 1,1 | v0 3→9 lượt độc lập ⇒ Welch **df ≈ 12, p ≈ 0,015** cho "+0,20 Acc" |
| **8B** | `qwen3-4b-instruct-2507/prompt-cot/exp022`–`exp024` | `exp009` | cặp prompt + `examples` từ `train` (0 / 1 / 5 ví dụ) | – | **2,8** | LLM có phá thế hoà lớp âm (94,70 vs 94,64 = **0,0006**) không |
| **8C** | `qwen3-4b-instruct-2507/prompt-cot/exp025`–`exp027` | `exp009` | `decoding.mode: sample` + `decoding.seed` = 1,2,3 | 1,2,3 | 2,8 | 3 MẪU THẬT SỰ khác nhau ⇒ nguyên liệu **biểu quyết tự-đồng-thuận** (0 GPU) |
| **8D** | `cafebert/lora/exp055`–`exp057` | `exp021` (đỉnh) | `checkpoints.best_metric: negative_f1` (+1 sửa mã) | 42,7,13 | 1,1 | Tiêu chí chọn checkpoint có cứu lớp âm không (khe duy nhất còn lại ở phía encoder) |

### Luật đọc số (giữ nguyên, đã áp cho Đợt 8 - chốt TRƯỚC khi thấy `test`)

- Ngưỡng phát hiện **> 0,25 ở CẢ HAI trục** (Accuracy macro **và** `neg F1 (5 n lớn)`) so với lượt mạnh nhất cùng
  bộ; **n >= 3 lượt**; phương sai lệch ⇒ báo cáo **Welch**; dưới ngưỡng thì ghi "cùng dải nhiễu".
- **Luật 12** (mới): đường encoder - cùng `decoding.seed` = cùng hạt giống huấn luyện ⇒ HAI lượt là MỘT lần rút thăm.
- **Luật 13** (mới): cấm lấy `neg F1 macro (7)` làm kỷ lục (`price` 5-6 ô + `packing` 9-10 ô chi phối) - đọc
  `neg F1 (5 n lớn)` hoặc chỉ số theo `n`.
- **Luật 14** (mới): bảng số CHÍNH chỉ nhận lượt cùng bài toán `(binary, drop, separate)` + cùng phiên bản dữ liệu.

### Việc 0 GPU (W1-W8) - thứ tự làm

`W1` commit `exp042`/`exp049` + `collect_reports` → `W2` 3 luật → `W3` sửa số 3 tài liệu → `W4` bảng xếp hạng
`neg F1 (5 n lớn)` toàn bộ lượt `test` → `W5` **tạo** `scripts/check_examples.py` (kiểm rò rỉ) → `W7` cặp prompt +
ví dụ mới từ `train` → `W6` `best_metric: negative_f1` → `W8` tạo 15 config + ghim + **gói 034** + `ci_checks` XANH.

## 14. Kết quả Đợt 8 (12/10/2026) - **8A ĐẠT · ba nhóm còn lại ÂM**

**Cửa kiểm gói 034 (15/15 lượt về đủ, KHÔNG sai sót nghiêm trọng):** mỗi thư mục kết quả có ĐÚNG **một**
lượt; 15/15 `FINISHED`, **không** lượt nào có `errors.json`, tất cả ghim đúng `5ec65f3`; bộ **file nhẹ** khớp
quy ước cũ (7 file mỗi lượt encoder, 6 file mỗi lượt LLM - LLM không có `probabilities.csv` /
`training_history.csv`, đúng như `exp016`/`exp017`); `training_history.csv` của 12 lượt encoder có **14 dòng,
bước 100 → 1150** ⇒ **không lượt nào bị ngắt tầng huấn luyện** (luật 11); 6 lượt LLM đọc được
**99,94-100 %** và token sinh TB **218-223 / trần 400** ⇒ **không chạm trần** (luật 3).
Hai lượt **bị Colab ngắt ở tầng ĐÁNH GIÁ rồi chạy tiếp** (`exp024` tái dùng 652 ô, `exp027` 1.336 ô) - cả hai
`FINISHED`, `read_rate` hợp lệ và số nằm trong dải anh em ⇒ dùng được, nhưng phải ghi số ô tái dùng
(**luật 15** mới ở `metrics.md`).

Số dưới đây **chấm lại bằng engine của dự án**, cột `acc macro (paper)` = `scores_paper.accuracy.macro`
(nay có cột riêng **`acc_paper_macro`** trong bảng chuẩn) và `neg_f1_big5` lấy từ
`data/reports/experiment_registry/experiment_registry.csv`.

| Nhóm | Lượt | acc macro (`paper`) | `neg_f1_big5` | Đối chứng để so | Kết |
| --- | --- | ---: | ---: | --- | --- |
| **8A** | `exp058`…`exp063` (v0 × seed 1-6) | 98,28 · 98,05 · 98,14 · 97,95 · 97,98 · 98,17 (TB **98,095**) | TB **0,9358** | v0 cũ: 97,88 (seed 42) · 98,26 (7) · 98,11 (13) | ✅ **ĐẠT** (xem D) |
| **8B** | `exp022` (0 ví dụ) | 97,62 | 0,9300 | `…/prompt-cot/exp009` (1 ví dụ viết tay, BIG5 0,9470) | ❌ **THUA** |
| **8B** | `exp023` (1 ví dụ) · `exp024` (5 ví dụ) | 96,83 · 96,41 | 0,9062 · 0,9066 | như trên | ❌ **THUA** (càng nhiều ví dụ càng tệ) |
| **8C** | `exp025` · `exp026` · `exp027` (3 mẫu) | 96,64 · 96,85 · 96,68 | 0,8966 · 0,9100 · 0,8922 | bản BỎ PHIẾU: 96,67 / **0,8039** | ❌ **RỖNG** |
| **8D** | `exp055` · `exp056` · `exp057` | 98,12 · 98,10 · 98,18 | 0,9406 · 0,9372 · 0,9444 | **ghép cặp hạt giống**: `exp021` (42) 98,41/0,9464 · `exp040` (7) 98,38/0,9486 · `exp041` (13) 98,13/0,9426 | ❌ **THUA** (−0,17 Acc · −0,51 neg F1) |


### A. Họ v0 nay có **9 lượt độc lập** - mức hơn `lr 4e-4` **đạt p < 0,05**

| Họ (cùng `(binary, drop, separate)`, cùng dữ liệu `v0.2.0`) | Acc macro (`paper`) | `neg_f1_big5` |
| --- | ---: | ---: |
| v0 cũ - 3 lượt ĐỘC LẬP (seed 42 · 7 · 13) | 98,083 (sd 0,191) | 0,9365 (sd 0,0091) |
| v0 MỚI - 6 lượt (seed 1-6) | 98,095 (sd 0,125) | 0,9358 (sd 0,0056) |
| **v0 gộp - 9 lượt độc lập** | **98,091** (sd 0,138) | **0,9360** (sd 0,0064) |
| **họ `lr 4e-4` - 12 lượt** (`exp015`/`exp021`/`exp027`/`exp028`/`exp040`-`exp047`) | **98,283** (sd 0,107) | **0,9438** (sd 0,0039) |
| **Welch (2 phía)** | t = 3,47 → **p = 0,0035** | t = 3,23 → **p = 0,0070** |

- Sáu hạt giống mới đều nằm TRONG dải cũ `[97,88 … 98,26]` ⇒ **không lượt nào bất thường**.
- **Đối chứng vô tư:** v0 cũ (3) vs v0 mới (6) - CÙNG cấu hình - cho **p = 0,93 / 0,90** ⇒ không khác nhau,
  đúng như phải thế ⇒ 6 hạt giống mới **không lệch hệ thống**.
- Kế hoạch dự đoán `p ≈ 0,015`; thực đo **0,0035 / 0,0070** ⇒ mục tiêu "hạ p xuống dưới 0,05" **ĐẠT ở cả
  hai trục** (trước Đợt 8 là 0,21 / 0,30).

### B. Ba nhóm còn lại - kết quả ÂM (giá trị nằm ở chỗ khoá lại đường đã thử)

- **8B (few-shot từ `train`):** trong CÙNG một cặp prompt mới, **0 ví dụ > 1 ví dụ > 5 ví dụ** (97,62 →
  96,83 → 96,41 Acc; 0,9300 → 0,9062 → 0,9066 `neg F1`). Cả ba đều DƯỚI mốc LLM sẵn có `exp009`
  (97,77 / 0,9470) và dưới họ encoder ⇒ **thế hoà lớp âm KHÔNG có thật**; NHÓM 10 đóng.
  *Đọc kèm cảnh báo mẫu số:* LLM chỉ có **2.387-2.571 ô** `paper` so với **2.734-2.740 ô** của encoder
  (ô model trả lời "không nhắc tới" bị loại khỏi mẫu số - `metrics.md`), tức cách đếm đã **thiên vị nhẹ
  cho LLM** mà LLM vẫn thua.
- **8C (3 mẫu tự-đồng-thuận):** ba mẫu rất giống nhau (đồng thuận từng cặp **98,05-98,27 %**, cả ba khớp
  **97,28 %**); **bản bỏ phiếu đạt 96,67 Acc nhưng `neg F1` tụt còn 0,8039** - dưới CẢ mẫu thấp nhất
  (0,8922) và dưới trung bình 3 mẫu (0,8126) ⇒ **bỏ phiếu không giúp**, đúng như Đợt 6 đo trên đường
  encoder. Bằng chứng chính thức: `data/reports/fusion/vote_llm_1shot.json` (+ `inputs/vote_llm_1shot__nhan_tung_o.csv`);
  8 ô hoà / 11.361 ô.
- **8D (`best_metric: negative_f1`):** ghép cặp theo hạt giống ⇒ **thua ở 2/3 lượt trên CẢ HAI trục**
  (`exp055` −0,29/−0,0058 · `exp056` −0,28/−0,0114; `exp057` +0,05/+0,0018), TB **−0,17 Acc / −0,51 neg F1**
  ⇒ **chọn checkpoint theo lớp âm không phải nút thắt**; điều kiện hồi sinh của Đợt 4 nay ĐÓNG.

### C. Quyết định (theo đúng bảng điều kiện ở mục 6)

| Hàng điều kiện | Thực tế Đợt 8 | Kết |
| --- | --- | --- |
| "LLM hơn ≥ 0,25 ở `neg F1`" → mở 6 lượt LLM + biểu quyết 5 mẫu | LLM **thua** (−0,017 ở lượt tốt nhất) | ❌ KHÔNG mở |
| "8D thắng ≥ 0,25" → nhân bản sang `r 16` / `every_n_steps 50` | 8D **thua** (−0,17 / −0,51) | ❌ KHÔNG mở |
| "p(v0) vẫn > 0,05" → thêm 3 lượt v0 dự trữ (`exp064`-`exp066`) | p = **0,0035 / 0,0070** | ❌ KHÔNG cần |
| "Cả ba hoà/thua" → **không tiêu GPU nữa, đi thẳng Đợt 7** | đúng | ✅ **ĐI ĐỢT 7** |

**Việc 0 GPU đã làm ngay khi số về (12/10/2026):**
1. `git add` **file nhẹ** 15 lượt (99 file: 9 lượt encoder × 7 + 6 lượt LLM × 6; phần nặng do `.gitignore`
   chặn) → commit `4b601c8`;
2. thêm cột **`acc_paper_macro`** vào bảng chuẩn (`src/reporting/reports.py` + 3 test) để số "Acc macro
   (paper)" có MỘT nguồn duy nhất, không viết tay trong văn xuôi;
3. chạy lại `collect_reports.py` (bảng chuẩn 144 dòng, 15 lượt mới vào);
4. chạy `scripts/vote.py` trên 3 mẫu LLM - **và phát hiện + sửa một LỖI THẬT của công cụ**: `fusion.vote`
   gọi `dict(None)` nên **SẬP** khi một lượt có review không đọc được (`preds[i] = None`). Lượt encoder
   đọc được 100 % nên lỗi ẩn từ Đợt 6; lượt LLM (99,94 %) mới lộ. Đã sửa + khoá bằng **3 test** mới
   (`tests/evaluation/test_fusion.py`), kèm **luật 15** vào `metrics.md`.
5. **Đợt 9 KHÔNG mở**; ba nhóm 8B/8C/8D và NHÓM 10 ghi vào "đã thử và ÂM" - không mở lại khi chưa có
   lý do MỚI (thêm dữ liệu / đổi định nghĩa bài toán / model khác là ba lý do duy nhất còn lại).

