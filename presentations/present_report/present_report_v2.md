# present_report_v2 - Báo cáo CHỐT: mức hơn đã có Ý NGHĨA THỐNG KÊ, và ba đường cuối đã cạn

> Đọc file này khi: cần con số CHỐT của dự án so với công bố tham chiếu. Đây là bản thay thế
> `present_report_v1.md` (giữ lại làm dấu vết: nó viết trước khi có 6 hạt giống v0 của Đợt 8).
> Liên quan: `docs/04_experiments/metrics.md` (luật đọc số), `present_plan_batch12.md` mục 14 (nhật ký Đợt 8),
> `data/reports/experiment_registry/experiment_registry.csv` (**nguồn số duy nhất** cho mọi số dưới đây).

## 0. File này khác `present_report_v1.md` ở đâu

| Hạng mục | `present_report_v1.md` | `present_report_v2.md` (file này) |
| --- | --- | --- |
| Số lượt của họ v0 | **3 lượt ĐỘC LẬP** (hạt giống 42 · 7 · 13) | **9 lượt độc lập** (+ 6 hạt giống 1-6 của Đợt 8/8A) |
| Ý nghĩa thống kê của mức hơn v0 | Welch **p = 0,21 / 0,30** ⇒ "gợi ý mạnh, CHƯA đủ" | Welch **p = 0,0035 (Acc) / 0,0070 (`neg F1`)** ⇒ **ĐẠT p < 0,05 ở cả hai trục** |
| Ba đường còn lại | "hai khe còn lại: prompt LLM + chọn checkpoint" (chưa thử) | **đã thử và cả ba đều ÂM** (mục 3: few-shot · bỏ phiếu · `best_metric`) |
| Số "Accuracy macro (paper)" | viết trong văn xuôi | cột **`acc_paper_macro`** trong bảng chuẩn (một nguồn duy nhất) |
| Giả định phương sai | chưa đo được `n` đủ | sd của hai họ **đã đo trên 9 và 12 lượt** |

## 1. Quy ước đọc số (kế thừa v1 + các luật chốt trong Đợt 8)

- **Cơ sở `paper`** là cách công bố đếm (chỉ giữ ô mà CẢ nhãn đúng VÀ nhãn đoán là `positive`/`negative`) -
  đây là cơ sở của mọi số so với công bố. **Cảnh báo bắt buộc đi kèm:** mẫu số phụ thuộc chất lượng model,
  nên **phải đọc kèm `paper.cells`**; lượt LLM chỉ có **2.387-2.571 ô** trong khi lượt encoder có
  **2.734-2.740 ô** (ô model trả lời "không nhắc tới" bị loại khỏi mẫu số).
- **Bàn đo là TRUNG BÌNH nhiều lượt**, không lấy lượt may nhất (luật 10): sd đo được của họ `lr 4e-4` là
  **0,107** ⇒ mọi chênh lệch dưới ~0,25-0,30 điểm KHÔNG kết luận.
- **`neg F1 macro (7 khía cạnh)` KHÔNG dùng làm kỷ lục** (luật 13): `price` (5-6 ô) và `packing` (9-10 ô)
  chi phối, 1-2 ô đảo chiều làm số nhảy 0,09. Thước đo lớp âm dùng ở đây là **`neg F1 (5 khía cạnh `n` lớn)`**
  = `neg_f1_big5`: trung bình F1 lớp âm của `colour` 54 · `shipping` 174 · `smell` 48 · `stayingpower` 96 ·
  `texture` 83 (455 ô ≈ 96,6 % tổng số ô âm).
- **Bảng chính chỉ nhận lượt giữ nguyên BÀI TOÁN và DỮ LIỆU** của công bố (luật 14):
  `(binary, drop, separate)` + `cosmetics-ds0.2.0-…-e616c1e3`, split `test`, 1.623 review.
- Trên **đường encoder**, cùng `decoding.seed` = **cùng một lần rút thăm huấn luyện** (luật 12) ⇒ đếm `n`
  theo HẠT GIỐNG, không theo số thư mục.
- Ngắt ở tầng **HUẤN LUYỆN** ⇒ lượt đó **bỏ** (luật 11). Ngắt ở tầng **ĐÁNH GIÁ** (đường LLM) ⇒ dùng được
  nếu `FINISHED` + `read_rate.valid` + số nằm trong dải anh em, và **phải khai số ô tái dùng** (luật 15).
- Phương sai hai họ lệch nhau (0,19 vs 0,107 ở Acc) ⇒ báo cáo **Welch** (không dùng kiểm định gộp).


## 2. BẢNG CHÍNH - công bố ↔ v0 (9 lượt) ↔ họ `lr 4e-4` (12 lượt)

Số của dự án **chấm lại bằng engine** trên cơ sở `paper`, đọc từ cột `acc_paper_macro` / `neg_f1_big5`
của `experiment_registry.csv`. Cả 21 lượt đều cùng bài toán `(binary, drop, separate)` và cùng dữ liệu
`v0.2.0` (luật 14), đều `FINISHED`, đều `valid`/`comparable = yes`.

| Thước đo | Công bố (đỉnh) | **v0 (`lr 2e-4`) - 9 lượt ĐỘC LẬP** | **họ `lr 4e-4` - 12 lượt** | Chênh (họ − v0) | **Welch (2 phía)** |
| --- | ---: | ---: | ---: | ---: | --- |
| **Accuracy macro (`paper`)** | 97,70 | **98,091** (sd 0,138) | **98,283** (sd 0,107) | **+0,19** | t = 3,47 → **p = 0,0035** ✅ |
| **`neg F1 (5 n lớn)`** | 88,23 | **93,60** (sd 0,64) | **94,38** (sd 0,39) | **+0,77** | t = 3,23 → **p = 0,0070** ✅ |
| `neg F1 macro (7)` (thước đo NHIỄU - luật 13) | 74,45 | 80,80 (**sd 1,5**) | 84,05 (**sd 3,5**) | +3,25 | không dùng để kết luận |

Dòng cuối là **bằng chứng định lượng cho luật 13**: trên CÙNG họ `lr 4e-4`, `neg F1 macro (7)` có
**sd = 3,5 điểm** - gấp **9 lần** sd của `neg F1 (5 n lớn)` (0,39) - vì nó lấy trung bình đều 7 khía cạnh nên
`price` (5-6 ô) và `packing` (9-10 ô) chi phối. Cùng để nói "mức hơn v0", thước đo 7-khía-cạnh cho +3,25 còn
thước đo có `n` cho +0,77: **thước đo nhiễu khuếch đại chênh lệch lên ~4 lần**.

Đọc bảng này thế nào:

1. **Mức hơn công bố là của CẢ HỌ, không phải của một lượt:** 21/21 lượt đều trên công bố ở **cả hai trục** -
   Acc thấp nhất là `cafebert/lora/exp002` **97,88** (> 97,70) và `neg F1` thấp nhất là `exp002` **92,62**
   (> 88,23). Mức vượt ở `neg F1 (5 n lớn)` là **+5,4 … +6,6** tuỳ lượt.
2. **Mục tiêu "giữ F1 và tăng Acc" so với bản CŨ: ĐẠT, và nay có ý nghĩa thống kê.** Họ `lr 4e-4` hơn họ v0
   **+0,19 Acc** và **+0,77 `neg F1`**, Welch **p = 0,0035 / 0,0070** (< 0,05). Trước Đợt 8 (khi v0 mới có
   3 lượt) hai số này là **p = 0,21 / 0,30** - không kết luận được. Kế hoạch dự đoán `p ≈ 0,015`, thực đo tốt
   hơn (**0,0035 / 0,0070**).
3. **Sáu hạt giống mới KHÔNG lệch hệ thống:** chúng nằm trong dải cũ `[97,88 … 98,26]`, và phép so "v0 cũ (3)
   vs v0 mới (6)" - cùng cấu hình, chỉ khác hạt giống - cho **p = 0,93 (Acc) / 0,90 (`neg F1`)**, tức hai
   nhóm này là MỘT tổng thể. Đây là đối chứng chứng minh phép đo không bị lệch theo đợt chạy.
4. **Bên trong họ `lr 4e-4` mọi biến thể ĐỒNG HẠNG** (sd 0,107): `r 8` 98,31 · `r 16` 98,30 ·
   `every_n_steps 50` 98,28 · `epochs 6` 98,25 ⇒ `r`, `epochs` và mật độ checkpoint **không tạo ra khác biệt
   đo được** (xem `present_plan_batch12.md` mục 11).
5. **Cái "kỷ lục" của bản cũ chỉ là lượt may nhất của nó:** đỉnh `present_report_v0.md`
   (`cafebert/lora/exp004`, 98,26) nằm TRONG dải của họ v0 mà trung bình họ v0 chỉ **98,08**; lượt đỉnh của
   họ mới (`exp021`, 98,41) cũng vậy (TB họ **98,28**). Không lấy số của một lượt làm kết luận (luật 10).

## 3. Đợt 8 - BA ĐƯỜNG CUỐI ĐÃ THỬ VÀ CẢ BA ĐỀU ÂM

Ba đường này là toàn bộ những gì còn lại sau khi các trục siêu tham số (Đợt 2) và đường kết hợp (Đợt 6)
đã chứng minh bão hoà. Cả ba đều được ghép cặp/khoá đúng MỘT biến nhờ W1-W8 của Đợt 8
(xem `present_plan_batch12.md` mục 13) - và cả ba đều không vượt ngưỡng phát hiện **> 0,25 ở CẢ HAI trục**.

### 3.1 Prompt/few-shot của LLM (8B) - **VÍ DỤ LẤY TỪ `train` LÀM LLM TỆ ĐI**

| Lượt | Số ví dụ | Acc macro (`paper`) | `neg F1 (5 n lớn)` | ô `paper` | Đọc được |
| --- | ---: | ---: | ---: | ---: | ---: |
| `qwen3-4b-instruct-2507/prompt-cot/exp022` | **0** | **97,62** | **0,9300** | 2.387 | 100 % |
| `…/prompt-cot/exp023` | 1 | 96,83 | 0,9062 | 2.476 | 100 % |
| `…/prompt-cot/exp024` | 5 | 96,41 | 0,9066 | 2.571 | 99,94 % |
| *mốc LLM sẵn có* `…/prompt-cot/exp009` (1 ví dụ viết tay) | 1 | 97,77 | **0,9470** | — | — |

- Trong CÙNG một cặp prompt mới (cùng câu chữ, cùng system, cùng không gian nhãn - `show_prompt` xác nhận),
  **0 ví dụ > 1 ví dụ > 5 ví dụ** ở cả hai trục. Ví dụ lấy từ `train` đã qua cửa kiểm rò rỉ
  (`scripts/check_examples.py`: 1/1 và 5/5 ví dụ nằm trong `train`, KHÔNG rò rỉ) - tức **giá trị âm này
  không phải lỗi dữ liệu**.
- Cả ba đều **DƯỚI** mốc LLM cũ `exp009` (0,9470) và cách xa họ encoder (93,60-94,38) ⇒ **"thế hoà ở lớp âm"
  mà kế hoạch giả định KHÔNG tồn tại**: LLM không phải khe hở của bài toán này.
- Nhớ cảnh báo mẫu số: LLM chỉ được chấm trên 2.387-2.571 ô (so với 2.734-2.740 ô của encoder), tức cách
  đếm đã **thiên vị nhẹ cho LLM**, vậy mà vẫn thua.

### 3.2 Lấy mẫu + bỏ phiếu tự-đồng-thuận (8C) - **RỖNG**

| | Acc macro (`paper`) | Acc (`all`, micro) | `neg F1 (5 n lớn)` |
| --- | ---: | ---: | ---: |
| `exp025` (seed 1) | 96,64 | 93,86 | 0,8966 |
| `exp026` (seed 2) | 96,85 | 93,78 | 0,9100 |
| `exp027` (seed 3) | 96,68 | 93,79 | 0,8922 |
| **BẢN BỎ PHIẾU** | 96,67 | **94,01** | **0,8039** |

- Ba mẫu rất giống nhau (đồng thuận từng cặp **98,05-98,27 %**, cả ba khớp **97,28 %**; 11.307 ô chung) ⇒
  bỏ phiếu gần như không có gì để sửa.
- Bản bỏ phiếu **nhích Acc lên 0,15-0,23** (94,01 vs TB 93,81) nhưng **`neg F1` TỤT còn 0,8039** - dưới cả
  mẫu thấp nhất (0,8922) và dưới trung bình ba mẫu (0,8126). **Bỏ phiếu KHÔNG giúp**, đúng như Đợt 6 đo trên
  ba hạt giống encoder.
- Bằng chứng chính thức (0 GPU): `data/reports/fusion/vote_llm_1shot.json` +
  `data/reports/fusion/inputs/vote_llm_1shot__nhan_tung_o.csv`; thống kê phiếu: 11.356 ô đủ phiếu, **8 ô hoà**,
  5 ô không lượt nào đọc được.

### 3.3 Chọn checkpoint theo lớp âm (8D, `best_metric: negative_f1`) - **THUA**

| Cặp (cùng hạt giống) | Acc macro (`paper`) | `neg F1 (5 n lớn)` | Chênh |
| --- | ---: | ---: | --- |
| `exp055` (seed 42) vs `exp021` | 98,12 / **98,41** | 94,06 / **94,64** | **−0,29 / −0,58** |
| `exp056` (seed 7) vs `exp040` | 98,10 / **98,38** | 93,72 / **94,86** | **−0,28 / −1,14** |
| `exp057` (seed 13) vs `exp041` | **98,18** / 98,13 | **94,44** / 94,26 | +0,05 / +0,18 |
| **Trung bình** | | | **−0,17 / −0,51** |

- Đây là phép so GHÉP CẶP đúng cách: mỗi lượt `best_metric: negative_f1` đứng cạnh chính lượt cha của nó
  (cùng cấu hình, cùng hạt giống), nên nhiễu giữa các hạt giống bị loại khỏi phép so.
- Kết quả: **thua ở 2/3 hạt giống trên CẢ HAI trục**, và trung bình âm ở cả hai ⇒ **chọn checkpoint theo lớp
  âm không phải nút thắt**. Điều kiện hồi sinh của Đợt 4 (nhóm 8) nay ĐÓNG.

## 4. Trần đã chạm: MƯỜI HAI bàn đạp đã thử, không bàn đạp rẻ nào vượt > 0,25 ở CẢ HAI trục

| # | Bàn đạp | Bằng chứng | Kết |
| --- | --- | --- | --- |
| 1 | `lr` 2e-4 → 4e-4 (Đợt 2) | mục 2: +0,19 Acc / +0,77 `neg F1`, **Welch p = 0,0035 / 0,0070** | ✅ **THẮNG có ý nghĩa** |
| 2-4 | `lora.r` 8 vs 16 · `epochs` 3 vs 6 · `every_n_steps` 100 vs 50 (Đợt 2) | bốn nhóm TB 98,25-98,31 (sd 0,107) | ĐỒNG HẠNG |
| 5-13 | **9 bàn đạp KẾT HỢP** (Đợt 6 + 5 bàn đạp trước đó): ensemble 6 model · ensemble 5 lượt cafebert · ngưỡng theo khía cạnh · biểu quyết 3 hạt giống encoder · router theo khía cạnh · gộp hai tầng · … | `data/reports/fusion/**`; chi tiết bảng ở `present_plan_batch12.md` mục 12 | ÂM / RỖNG |
| 14 | **few-shot LLM từ `train`** (8B) | mục 3.1: 0 ví dụ 97,62/0,9300 > 1 ví dụ 96,83/0,9062 > 5 ví dụ 96,41/0,9066 | THUA |
| 15 | **bỏ phiếu tự-đồng-thuận 3 mẫu LLM** (8C) | mục 3.2: `neg F1` 0,8039 < mọi mẫu (0,8922-0,9100) | RỖNG |
| 16 | **chọn checkpoint theo lớp âm** (8D) | mục 3.3: −0,17 Acc / −0,51 `neg F1` | THUA |

Ngoài ra ba hướng đã bị LOẠI về mặt phương pháp, không phải vì yếu: nhánh `full` fine-tune (thoái hoá, mục 9.2
của kế hoạch), đổi chỉ số `price` (đã bỏ NHÓM 13), và đổi định nghĩa bài toán (đã rút NHÓM 15 + luật 14).

## 5. Dư địa còn lại - chỉ ba lý do được phép mở lại kế hoạch

1. **Thêm dữ liệu** - người dùng đã chốt **KHÔNG** (mọi ý dùng dữ liệu ngoài, distillation, hard-negative
   mining đã bị xoá khỏi kế hoạch). Đây là lý do MẠNH NHẤT còn lại nếu đổi ràng buộc.
2. **Đổi định nghĩa bài toán** - đã chứng minh PHÁ tính so sánh với công bố (`neutral_policy` đổi cả nhãn
   huấn luyện; `not_mentioned` đổi khung chấm) ⇒ nếu làm thì phải mở BẢNG RIÊNG, ghi rõ "khác bài toán"
   (luật 14), và KHÔNG được trộn vào bảng chính.
3. **Model khác** - chưa thử hết: encoder khác (XLM-R, ViBERT... đã có trong dự án nhưng chưa chưng cất đủ
   lượt), hoặc LLM LỚN hơn. Chi phí đã đo: Qwen3-4B ≈ **2,6 h/lượt**, còn cỡ 8B đã chứng minh **hỏng định
   dạng** (`qwen3-8b` 100 % ô trả lời sai định dạng) ⇒ muốn thử phải đổi cả giao thức sinh.

**Dư địa KỸ THUẬT** (không phải lý do mở đợt mới, nhưng đáng ghi): lượt dẫn đầu còn **≈ 22 ô âm sai / 467 ô
(4,7 %)** ở lớp âm, tập trung ở các khía cạnh `n` lớn. Ba đường rẻ nhất để chạm vào đó (kết hợp 6 model, ngưỡng
theo khía cạnh, chọn checkpoint) đều ĐÃ THỬ và không cái nào vượt ngưỡng ⇒ muốn cải thiện phải quay lại một
trong ba lý do trên.

## 6. Phụ lục A - 21 lượt trong bảng chính + 9 lượt Đợt 8 (nhãn để tái lập)

`cafebert/lora` - họ **v0** (`lr 2e-4`), 9 lượt độc lập: `exp002:93448395` 97,88/0,9262 ·
`exp004:43e6c243` 98,26/0,9432 · `exp048:d27389b7` 98,11/0,9402 · `exp058:a11f564b` 98,28/0,9462 ·
`exp059:3961e38f` 98,05/0,9324 · `exp060:df801bfa` 98,14/0,9330 · `exp061:0b542ad0` 97,95/0,9312 ·
`exp062:6df2a531` 97,98/0,9336 · `exp063:a60e9302` 98,17/0,9382.

`cafebert/lora` - họ **`lr 4e-4`**, 12 lượt độc lập: `exp015:eb2b6cfa` 98,35/0,9478 ·
`exp021:4653ddfc` 98,41/0,9464 · `exp027:43e40f61` 98,37/0,9406 · `exp028:d17056e5` 98,31/0,9484 ·
`exp040:49a248c4` 98,38/0,9486 · `exp041:73e9f9aa` 98,13/0,9426 · `exp042:5a6882ac` 98,24/0,9402 ·
`exp043:2f85368a` 98,14/0,9424 · `exp044:311e79fa` 98,17/0,9364 · `exp045:880624f8` 98,37/0,9456 ·
`exp046:05e29d98` 98,16/0,9406 · `exp047:dd2a2ecd` 98,37/0,9456.

`cafebert/lora` - **tám-D** (`best_metric: negative_f1`): `exp055:52297bc2` 98,12/0,9406 ·
`exp056:bf042ab8` 98,10/0,9372 · `exp057:36ee5314` 98,18/0,9444.

`qwen3-4b-instruct-2507/prompt-cot` - **tám-B** (few-shot từ `train`): `exp022:1e71c49e` 97,62/0,9300 ·
`exp023:29ed4226` 96,83/0,9062 · `exp024:5f6161b6` 96,41/0,9066. **tám-C** (3 mẫu): `exp025:ad4136a1`
96,64/0,8966 · `exp026:0842e93d` 96,85/0,9100 · `exp027:af67f011` 96,68/0,8922.

Hai con số mỗi lượt là **`acc_paper_macro`** / **`neg_f1_big5`**, lấy từ
`data/reports/experiment_registry/experiment_registry.csv` (sinh bằng `python scripts/collect_reports.py`);
chúng tính từ `scores_paper` trong `metrics.json` của chính lượt chạy - không có phép tính thứ hai.
Hai lượt của tám-C/tám-B có **2 `attempt`** (Colab ngắt ở tầng đánh giá rồi chạy tiếp): `exp024`
(tái dùng 652 ô) và `exp027` (1.336 ô) - hợp lệ theo **luật 15**, và số của chúng nằm giữa các lượt anh em.

