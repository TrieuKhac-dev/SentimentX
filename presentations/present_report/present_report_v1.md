# present_report_v1 - Đối chiếu dự án với công bố tham chiếu (thêm model MỚI và bốn thước đo F1 có trọng số `n`)

> Đọc file này khi: trình bày kết quả dự án so với công bố tham chiếu, hoặc chọn model để báo cáo.
> Liên quan: `present_report_v0.md` (bản cũ, chỉ có model CŨ), `docs/04_experiments/metrics.md`,
> `docs/04_experiments/reference_publication.md`, `data/reference_publication/`.
> Nguồn số: công bố lấy từ `data/reference_publication/*.csv` (đã đối chiếu Table 3-6 của `announcement.md`);
> dự án lấy từ `experiments/**/results/<hash8>/metrics.json` (cơ sở `paper`), KHÔNG lấy từ `data/reports/**`.

## 0. File này khác `present_report_v0.md` ở đâu

| Hạng mục | `present_report_v0.md` | `present_report_v1.md` (file này) |
| --- | --- | --- |
| Model | chỉ model **CŨ** (đóng băng ở `cafebert/lora/exp004` = 98,26) | model CŨ **+ 5 lượt MỚI** của đợt 11 (`cafebert/lora/exp011`, `exp013`, `exp015`, `exp017`, `exp019`) |
| Thước đo | Accuracy macro + Precision/Recall/F1 theo khía cạnh và sắc thái | **giữ nguyên** các thước đo đó, **thêm BỐN thước đo F1 mới có trọng số `n`** (mục 3) |
| Điểm yếu còn lại của v0 | dùng `neg F1 macro` gộp cả 7 khía cạnh, nên 2 khía cạnh `n` nhỏ (`price` 6, `packing` 10) kéo lệch mà không cảnh báo | nói rõ `n` từng khía cạnh (mục 2) và tách "thước đo có `n` đủ lớn" khỏi "thước đo bị nhiễu" |

Ba thước đo CŨ của v0 được giữ nguyên trong file này: **Accuracy theo khía cạnh** (mục 4),
**Precision/Recall/F1 theo khía cạnh và sắc thái** (mục 5, 6, 7), và các **dòng MACRO** của chúng.

## 1. Quy ước đọc số

- Cơ sở `paper`: chỉ giữ ô mà **CẢ** nhãn đúng **VÀ** nhãn đoán là `positive`/`negative` - đúng cách công bố đếm. Đây là cơ sở dùng để so với công bố.
- Split: `test`, **1.623 review**; dữ liệu `cosmetics-ds0.2.0-pl0.2.0-srccosmetics@0.1.0-e616c1e3`.
- Đơn vị: mọi Accuracy/Precision/Recall/F1 ghi theo **%**; chênh lệch dùng **pp (điểm phần trăm)**, ví dụ 98,35 % - 97,70 % = **+0,65 pp**.
- `n` trong mục 4-7 là số ô của **nhãn ĐÚNG** cho cặp (khía cạnh × sắc thái); giống nhau ở mọi cột vì mọi lượt chấm trên cùng một tập `test`.
- Cột công bố: `CB 0-shot`, `CB 1-shot`, `CB 5-shot` = GPT-4o-mini + Chain-of-Thought (công bố).
- Encoder không có khái niệm shot nên được so với **cả ba** mức của công bố; lượt prompt được so với **đúng mức shot của chính nó**.
- **Biên nhiễu đường encoder đã đo = ±0,33 … ±0,67 điểm** (ba lượt chạy lại cha với `decoding.seed: 7`); lấy mức làm việc **±0,7** - chênh lệch dưới mức đó KHÔNG kết luận.

Dùng mục 2 để biết thước đo nào có `n` đủ lớn trước khi đọc mục 3.

## 2. `n` - thước đo nào đáng tin (điểm v0 chưa nói rõ)

| Khía cạnh | `n` dương | `n` âm | Đọc F1 lớp âm ở dòng này |
| --- | ---: | ---: | --- |
| shipping | 334 | **174** | đáng tin nhất (chi phối bảng micro) |
| stayingpower | 141 | 96 | đáng tin |
| texture | 346 | 83 | đáng tin |
| colour | 622 | 54 | đáng tin |
| smell | 252 | 48 | đáng tin (biên dưới) |
| packing | 282 | **10** | **NHIỄU**: mỗi ô ≈ 0,10 F1 |
| price | 321 | **6** | **NHIỄU**: mỗi ô ≈ 0,17 F1 |

- 5 khía cạnh `n` lớn (`n` âm = 48 … 174) chiếm **455 ô = 96,6 %** tổng số ô âm.
- `price` (6) + `packing` (10) chỉ chiếm **16 ô = 3,4 %**, nhưng trong một "macro 7 khía cạnh" thì chúng chiếm **2/7 = 28,6 %** trọng số ⇒ **bóp méo kết luận**.

Vì vậy file này định nghĩa thêm hai thước đo có `n`:

| Tên (mới) | Cách tính | Vì sao dùng |
| --- | --- | --- |
| **`neg F1 macro (5 n lớn)`** | F1 lớp âm trung bình trên 5 khía cạnh `n` = 48 … 174 | bỏ hẳn `price`/`packing`; mỗi khía cạnh còn lại có `n` ≥ 48 ⇒ đọc được |
| **`neg F1 micro (theo n)`** | F1 lớp âm gộp mọi ô, **trọng số = số ô** | `shipping` (174 ô) nặng gấp 29 lần `price` (6 ô); không thể "ăn điểm" bằng 1-2 ô |

Thước đo CŨ `neg F1 macro (7)` của v0 **vẫn được giữ** ở các bảng dưới để đối chiếu, nhưng phải đọc kèm cảnh báo trên: gần như toàn bộ chênh lệch giữa các lượt ở dòng đó đến từ `price`/`packing`.

## 3. BỐN thước đo (2 cũ + 2 mới) - bảng đối đầu công bố ↔ model CŨ ↔ model MỚI

Cột `neg F1 macro (7)` là thước đo **của bản cũ**; cột `neg F1 macro (5 n lớn)` và `neg F1 micro (theo n)` là hai thước đo **mới có `n`**.

| Lượt chạy (nguồn) | Loại | Accuracy macro | pos F1 macro | neg F1 macro (7) | **neg F1 macro (5 n lớn)** | **neg F1 micro (theo n)** | prf micro F1 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **CB 0-shot** | công bố | 97,36 | 98,49 | 74,45 | 88,23 | 91,14 | - |
| **CB 1-shot** | công bố | **97,70** | 98,48 | 74,20 | 87,88 | 89,11 | - |
| **CB 5-shot** | công bố | 96,74 | 97,51 | 73,35 | 82,69 | 86,86 | - |
| `phobert-base-v2/lora/exp001` (ce) | CŨ | 88,40 | 93,33 | 14,66 | - | - | 0,905 |
| `phobert-base-v2/lora/exp002` (wce) | CŨ | 96,62 | 97,67 | 77,57 | 89,56 | 90,41 | 0,967 |
| `phobert-large/lora/exp002` | CŨ | 97,69 | 98,51 | 78,11 | 93,00 | 92,80 | 0,977 |
| `qwen3-4b…/prompt-cot/exp009` (1-shot 4-bit) | CŨ | 97,77 | 98,41 | 87,20 | - | - | 0,928 |
| **`cafebert/lora/exp002`** (seed 42) | **CŨ** | 97,88 | 98,61 | 84,73 | 92,62 | 93,78 | 0,978 |
| **`cafebert/lora/exp004`** (seed 7, **TOP CŨ**) | **CŨ** | 98,26 | 98,87 | 80,90 | 94,32 | 94,54 | 0,983 |
| `cafebert/lora/exp011` (pipeline v0.3.0) | MỚI | 98,05 | 98,74 | 80,17 | 93,30 | 93,75 | 0,980 |
| **`cafebert/lora/exp013`** (LoRA r=32) | **MỚI** | 98,33 | **98,93** | **88,93** | 94,14 | **95,12** | 0,983 |
| **`cafebert/lora/exp015`** (lr 4e-4) | **MỚI (TOP MỚI)** | **98,35** | **98,93** | 81,23 | **94,78** | 94,94 | **0,984** |
| `cafebert/lora/exp017` (focal γ2) | MỚI | 98,06 | 98,73 | 79,80 | 93,94 | 93,93 | 0,981 |
| `cafebert/lora/exp019` (DoRA) | MỚI | 97,99 | 98,66 | 88,09 | 92,96 | 94,34 | 0,980 |

Đỉnh công bố theo từng cột (để tính chênh lệch): Accuracy **97,70** · pos F1 **98,49** · neg F1 (7) **74,45** · neg F1 (5 n lớn) **88,23** · neg F1 micro **91,14** · prf micro F1 (công bố không báo).

### 3.1 Vượt công bố ở ĐÂU, và có vượt **cả Accuracy lẫn F1** không

| Lượt (CafeBERT) | Acc vs 97,70 | pos F1 vs 98,49 | neg F1 **5 n lớn** vs 88,23 | neg F1 **micro** vs 91,14 | Vượt cả Acc và F1? |
| --- | --- | --- | --- | --- | --- |
| exp002 (CŨ) | +0,18 | +0,12 | +4,39 | +2,64 | CÓ |
| **exp004 (TOP CŨ)** | +0,56 | +0,38 | +6,09 | +3,40 | CÓ |
| exp011 (MỚI) | +0,35 | +0,25 | +5,07 | +2,61 | CÓ |
| **exp013 (MỚI)** | +0,63 | +0,44 | +5,91 | +3,98 | CÓ |
| **exp015 (TOP MỚI)** | **+0,65** | **+0,44** | **+6,55** | **+3,80** | **CÓ (mạnh nhất)** |
| exp017 (MỚI) | +0,36 | +0,24 | +5,71 | +2,79 | CÓ |
| exp019 (MỚI) | +0,29 | +0,17 | +4,73 | +3,20 | CÓ |

Kết luận mục 3: mục tiêu của đợt thí nghiệm MỚI - **"giữ F1 tăng, đồng thời tăng Accuracy để vượt công bố ở cả hai"** - **đã đạt**, và lượt đạt tốt nhất là **`cafebert/lora/exp015`**.

### 3.2 Cảnh báo `n`: `neg F1 macro (7)` nói SAI về `exp013`

| Khía cạnh âm | `n` | exp002 | exp004 | exp013 | exp015 |
| --- | ---: | ---: | ---: | ---: | ---: |
| shipping | 174 | 97,10 | 98,00 | 97,70 | **98,00** |
| stayingpower | 96 | 96,90 | 97,40 | **97,90** | **97,90** |
| texture | 83 | 93,30 | 94,70 | 94,70 | 93,00 |
| colour | 54 | 86,70 | 90,40 | 90,40 | **93,70** |
| smell | 48 | 89,10 | 91,10 | 90,00 | **91,30** |
| packing | **9-10** | 90,00 | 94,70 | 94,70 | 94,70 |
| price | **4-6** | 40,00 | **0,00** | **57,10** | **0,00** |
| **macro (7)** | - | 84,73 | 80,90 | **88,93** | 81,23 |
| **macro (5 n lớn)** | - | 92,62 | 94,32 | 94,14 | **94,78** |
| **micro (theo n)** | - | 93,78 | 94,54 | **95,12** | 94,94 |

Đọc đúng: `exp013` "vô địch" ở cột macro-7 **chỉ vì** `price` âm: 57,10 % (n = 5) so với 0,00 % (n = 4) của `exp015` - chênh lệch **1 ô**. Trên 5 khía cạnh `n` lớn thì `exp013` (94,14) **thua** `exp015` (94,78). Vì vậy:

- Nếu chọn model để **báo cáo chất lượng thật** ⇒ dùng `exp015` (đỉnh cả Accuracy lẫn F1 có `n`).
- Nếu buộc phải dẫn con số macro-7 ⇒ **phải ghi kèm `n` của `price`/`packing`** và câu "khoản hơn đến từ `price` n = 5, không kết luận được".

Cùng lý do đó, "tradeoff mất F1" khi đi từ `exp002` (seed 42) sang `exp004` (seed 7) cũng là ảo giác của macro-7: macro-7 giảm 84,73 → 80,90 nhưng trên `n` lớn thì F1 TĂNG 92,62 → 94,32 **và** Accuracy TĂNG 97,88 → 98,26.

## 4. Bảng 3 - Accuracy theo khía cạnh (%, cơ sở `paper`) - GIỮ NGUYÊN v0 + 2 cột MỚI

Hai cột in đậm ở giữa là lượt MỚI của đợt 11; mọi cột còn lại y nguyên bảng của `present_report_v0.md`.

| Aspect | CB 0-shot | CB 1-shot | CB 5-shot | Qwen3-4B 0-shot (4-bit) | Qwen3-4B 1-shot (4-bit) | Qwen3-4B 5-shot (fp16) | Qwen3-4B 5-shot (4-bit) | CafeBERT exp002 (seed42) | CafeBERT exp004 (seed7) | **CafeBERT exp013 (r=32)** | **CafeBERT exp015 (lr 4e-4)** | Pb-large exp002 | Pb-base exp001 (ce) | Pb-base exp002 (wce) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Smell | 94.59 | 96.15 | 92.86 | 95.26 | 97.44 | 95.67 | 96.09 | 96.28 | 96.96 | 96.63 | 96.96 | 96.92 | 84.48 | 95.92 |
| Price | 97.22 | 100.00 | 100.00 | 96.25 | 98.49 | 97.37 | 98.45 | 99.07 | 98.45 | 99.07 | 98.76 | 98.13 | 98.45 | 98.14 |
| Texture | 94.12 | 100.00 | 100.00 | 97.67 | 96.86 | 95.83 | 96.06 | 97.42 | 97.90 | 97.89 | 97.20 | 98.11 | 83.86 | 95.55 |
| Colour | 97.37 | 96.61 | 94.74 | 97.67 | 98.82 | 96.92 | 96.56 | 97.60 | 98.35 | 98.35 | 98.95 | 97.28 | 92.27 | 96.41 |
| Stayingpower | 100.00 | 94.12 | 92.86 | 98.54 | 96.15 | 94.61 | 97.37 | 97.45 | 97.87 | 98.30 | 98.30 | 96.98 | 64.71 | 92.67 |
| Packing | 98.25 | 98.11 | 100.00 | 97.90 | 97.90 | 98.26 | 97.89 | 99.30 | 99.65 | 99.66 | 99.65 | 98.61 | 96.83 | 99.65 |
| Shipping | 100.00 | 98.89 | 96.70 | 97.51 | 98.72 | 96.72 | 97.94 | 98.02 | 98.61 | 98.41 | 98.61 | 97.82 | 98.19 | 98.02 |
| **MACRO** | **97.36** | **97.70** | **96.74** | **97.26** | **97.77** | **96.48** | **97.19** | **97.88** | **98.26** | **98.33** | **98.35** | **97.69** | **88.40** | **96.62** |
| Δ vs mức công bố tốt nhất | - | - | - | −0.10 (vs CB0) | +0.07 (vs CB1) | −0.26 (vs CB5) | +0.45 (vs CB5) | +0.18 (vs CB1) | +0.56 (vs CB1) | **+0.63 (vs CB1)** | **+0.65 (vs CB1)** | −0.01 (vs CB1) | −9.30 (vs CB1) | −1.08 (vs CB1) |

Đọc bảng 3: MACRO vượt công bố (97,70) ở **mọi** lượt CafeBERT, nhưng **5/7 khía cạnh công bố đạt 100 %** (`price`, `texture`, `stayingpower`, `packing`, `shipping`) thì mọi lượt của dự án vẫn thấp hơn - lợi thế nằm ở **MACRO**, không nằm ở từng khía cạnh. `exp013`/`exp015` **không** sửa được khoảng cách đó; chúng chỉ nhích MACRO thêm +0,07 … +0,09 so với `exp004` - **nằm trong biên nhiễu ±0,7**.

## 5. Bảng 4 - Precision theo khía cạnh và sắc thái (%, cơ sở `paper`) - GIỮ NGUYÊN v0 + 2 cột MỚI

| Aspect | Sentiment | n | CB 0-shot | CB 1-shot | CB 5-shot | Qwen3-4B 0-shot (4-bit) | Qwen3-4B 1-shot (4-bit) | Qwen3-4B 5-shot (fp16) | Qwen3-4B 5-shot (4-bit) | CafeBERT exp002 | CafeBERT exp004 | **CafeBERT exp013** | **CafeBERT exp015** | Pb-large exp002 | Pb-base exp001 (ce) | Pb-base exp002 (wce) |
| --- | --- | --: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Smell | positive | 252 | 97.06 | 100.00 | 96.15 | 99.10 | 99.50 | 98.70 | 99.40 | 98.80 | 99.20 | 98.80 | 99.60 | 99.60 | 84.50 | 99.60 |
| Smell | negative | 48 | 66.67 | 50.00 | 50.00 | 80.40 | 89.40 | 83.00 | 84.60 | 84.90 | 86.80 | 86.50 | 85.50 | 85.50 | 0.00 | 81.00 |
| Price | positive | 321 | 100.00 | 100.00 | 100.00 | 100.00 | 99.60 | 100.00 | 100.00 | 99.10 | 98.50 | 99.10 | 98.80 | 98.10 | 98.40 | 98.10 |
| Price | negative | 6 | 0.00 | 0.00 | 0.00 | 15.40 | 50.00 | 30.00 | 33.30 | 100.00 | 0.00 | 100.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| Texture | positive | 346 | 92.68 | 100.00 | 100.00 | 99.60 | 99.60 | 98.30 | 98.50 | 98.50 | 99.10 | 99.40 | 99.10 | 98.80 | 83.90 | 99.10 |
| Texture | negative | 83 | 100.00 | 100.00 | 100.00 | 91.00 | 88.70 | 87.10 | 87.70 | 92.80 | 93.00 | 92.00 | 89.90 | 95.10 | 0.00 | 83.20 |
| Colour | positive | 622 | 100.00 | 100.00 | 100.00 | 99.30 | 100.00 | 99.50 | 99.50 | 99.70 | 99.70 | 99.70 | 99.80 | 99.80 | 92.30 | 99.70 |
| Colour | negative | 54 | 77.78 | 75.00 | 66.67 | 80.70 | 86.00 | 73.80 | 72.30 | 78.80 | 85.20 | 85.20 | 89.70 | 75.70 | 0.00 | 70.30 |
| Stayingpower | positive | 141 | 100.00 | 100.00 | 100.00 | 98.80 | 98.70 | 96.80 | 98.80 | 98.60 | 97.90 | 98.60 | 98.60 | 97.80 | 64.40 | 98.40 |
| Stayingpower | negative | 96 | 100.00 | 80.00 | 80.00 | 98.10 | 93.80 | 91.80 | 95.60 | 95.90 | 97.90 | 97.90 | 97.90 | 95.70 | 100.00 | 85.80 |
| Packing | positive | 282 | 100.00 | 100.00 | 100.00 | 100.00 | 100.00 | 99.60 | 99.60 | 100.00 | 100.00 | 100.00 | 100.00 | 99.60 | 96.80 | 100.00 |
| Packing | negative | 10 | 66.67 | 66.67 | 100.00 | 60.00 | 62.50 | 69.20 | 64.30 | 81.80 | 90.00 | 90.00 | 90.00 | 75.00 | 0.00 | 90.90 |
| Shipping | positive | 334 | 100.00 | 100.00 | 96.88 | 98.40 | 99.00 | 96.60 | 98.40 | 99.10 | 100.00 | 99.10 | 99.40 | 99.40 | 98.50 | 99.10 |
| Shipping | negative | 174 | 100.00 | 96.30 | 96.30 | 95.70 | 98.10 | 96.90 | 97.00 | 96.00 | 96.10 | 97.10 | 97.10 | 94.90 | 97.60 | 96.00 |
| **MACRO** | positive | - | 98.53 | 100.00 | 99.00 | 99.31 | 99.49 | 98.50 | 99.17 | 99.11 | 99.20 | 99.24 | **99.33** | 99.01 | 88.40 | 99.14 |
| **MACRO** | negative | - | 73.02 | 66.85 | 70.42 | 74.47 | 81.21 | 75.97 | 76.40 | 90.03 | 78.43 | **92.67** | 78.59 | 74.56 | 28.23 | 72.46 |

## 6. Bảng 5 - Recall theo khía cạnh và sắc thái (%, cơ sở `paper`) - GIỮ NGUYÊN v0 + 2 cột MỚI

| Aspect | Sentiment | n | CB 0-shot | CB 1-shot | CB 5-shot | Qwen3-4B 0-shot (4-bit) | Qwen3-4B 1-shot (4-bit) | Qwen3-4B 5-shot (fp16) | Qwen3-4B 5-shot (4-bit) | CafeBERT exp002 | CafeBERT exp004 | **CafeBERT exp013** | **CafeBERT exp015** | Pb-large exp002 | Pb-base exp001 (ce) | Pb-base exp002 (wce) |
| --- | --- | --: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Smell | positive | 252 | 97.06 | 96.00 | 96.15 | 95.20 | 97.40 | 96.10 | 95.70 | 96.80 | 97.20 | 97.20 | 96.80 | 96.70 | 100.00 | 95.50 |
| Smell | negative | 48 | 66.67 | 100.00 | 50.00 | 95.70 | 97.70 | 93.60 | 97.80 | 93.80 | 95.80 | 93.80 | 97.90 | 97.90 | 0.00 | 97.90 |
| Price | positive | 321 | 97.22 | 100.00 | 100.00 | 96.20 | 98.90 | 97.30 | 98.40 | 100.00 | 100.00 | 100.00 | 100.00 | 100.00 | 100.00 | 100.00 |
| Price | negative | 6 | 0.00 | 0.00 | 0.00 | 100.00 | 75.00 | 100.00 | 100.00 | 25.00 | 0.00 | 40.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| Texture | positive | 346 | 100.00 | 100.00 | 100.00 | 97.50 | 96.30 | 96.40 | 96.40 | 98.30 | 98.30 | 98.00 | 97.40 | 98.80 | 100.00 | 95.40 |
| Texture | negative | 83 | 76.92 | 100.00 | 100.00 | 98.40 | 98.60 | 93.70 | 94.70 | 93.90 | 96.40 | 97.60 | 96.40 | 95.10 | 0.00 | 96.30 |
| Colour | positive | 622 | 97.10 | 96.23 | 94.12 | 98.10 | 98.70 | 97.20 | 96.80 | 97.70 | 98.50 | 98.50 | 99.00 | 97.20 | 100.00 | 96.40 |
| Colour | negative | 54 | 100.00 | 100.00 | 100.00 | 92.00 | 100.00 | 94.10 | 94.00 | 96.30 | 96.30 | 96.30 | 98.10 | 98.10 | 0.00 | 96.30 |
| Stayingpower | positive | 141 | 100.00 | 92.31 | 90.00 | 98.80 | 93.70 | 93.80 | 96.50 | 97.10 | 98.60 | 98.60 | 98.60 | 97.10 | 100.00 | 89.20 |
| Stayingpower | negative | 96 | 100.00 | 100.00 | 100.00 | 98.10 | 98.70 | 95.70 | 98.50 | 97.90 | 96.80 | 97.90 | 97.90 | 96.80 | 2.70 | 97.80 |
| Packing | positive | 282 | 98.18 | 98.04 | 100.00 | 97.80 | 97.80 | 98.60 | 98.20 | 99.30 | 99.60 | 99.60 | 99.60 | 98.90 | 100.00 | 99.60 |
| Packing | negative | 10 | 100.00 | 100.00 | 100.00 | 100.00 | 100.00 | 90.00 | 90.00 | 100.00 | 100.00 | 100.00 | 100.00 | 90.00 | 0.00 | 100.00 |
| Shipping | positive | 334 | 100.00 | 98.44 | 98.41 | 97.80 | 99.00 | 98.40 | 98.40 | 97.90 | 97.90 | 98.50 | 98.50 | 97.30 | 98.80 | 97.90 |
| Shipping | negative | 174 | 100.00 | 100.00 | 92.86 | 96.90 | 98.10 | 93.40 | 97.00 | 98.20 | 100.00 | 98.20 | 98.80 | 98.80 | 97.00 | 98.30 |
| **MACRO** | positive | - | 98.51 | 97.29 | 96.95 | 97.34 | 97.40 | 96.83 | 97.20 | 98.16 | 98.59 | **98.63** | 98.56 | 98.00 | 99.83 | 96.29 |
| **MACRO** | negative | - | 77.66 | 85.71 | 77.55 | 97.30 | 95.44 | 94.36 | 96.00 | 86.44 | 83.61 | **89.11** | 84.16 | 82.39 | 14.24 | 83.80 |

## 7. Bảng 6 - F1-score theo khía cạnh và sắc thái (%, cơ sở `paper`) - GIỮ NGUYÊN v0 + 2 cột MỚI

| Aspect | Sentiment | n | CB 0-shot | CB 1-shot | CB 5-shot | Qwen3-4B 0-shot (4-bit) | Qwen3-4B 1-shot (4-bit) | Qwen3-4B 5-shot (fp16) | Qwen3-4B 5-shot (4-bit) | CafeBERT exp002 | CafeBERT exp004 | **CafeBERT exp013** | **CafeBERT exp015** | Pb-large exp002 | Pb-base exp001 (ce) | Pb-base exp002 (wce) |
| --- | --- | --: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Smell | positive | 252 | 97.06 | 97.06 | 96.15 | 97.10 | 98.40 | 97.40 | 97.50 | 97.80 | 98.20 | 98.00 | 98.20 | 98.10 | 91.60 | 97.50 |
| Smell | negative | 48 | 66.67 | 66.67 | 50.00 | 87.40 | 93.30 | 88.00 | 90.70 | 89.10 | 91.10 | 90.00 | 91.30 | 91.30 | 0.00 | 88.70 |
| Price | positive | 321 | 98.59 | 100.00 | 100.00 | 98.10 | 99.20 | 98.70 | 99.20 | 99.50 | 99.20 | 99.50 | 99.40 | 99.10 | 99.20 | 99.10 |
| Price | negative | 6 | 0.00 | 0.00 | 0.00 | 26.70 | 60.00 | 46.20 | 50.00 | 40.00 | 0.00 | 57.10 | 0.00 | 0.00 | 0.00 | 0.00 |
| Texture | positive | 346 | 96.20 | 100.00 | 100.00 | 98.50 | 97.90 | 97.40 | 97.50 | 98.40 | 98.70 | 98.70 | 98.20 | 98.80 | 91.20 | 97.20 |
| Texture | negative | 83 | 86.96 | 100.00 | 100.00 | 94.60 | 93.40 | 90.20 | 91.00 | 93.30 | 94.70 | 94.70 | 93.00 | 95.10 | 0.00 | 89.30 |
| Colour | positive | 622 | 98.53 | 98.08 | 96.97 | 98.70 | 99.40 | 98.30 | 98.10 | 98.70 | 99.10 | 99.10 | 99.40 | 98.50 | 96.00 | 98.00 |
| Colour | negative | 54 | 87.50 | 85.71 | 80.00 | 86.00 | 92.50 | 82.80 | 81.70 | 86.70 | 90.40 | 90.40 | 93.70 | 85.50 | 0.00 | 81.20 |
| Stayingpower | positive | 141 | 100.00 | 96.00 | 94.74 | 98.80 | 96.10 | 95.30 | 97.60 | 97.80 | 98.20 | 98.60 | 98.60 | 97.50 | 78.30 | 93.60 |
| Stayingpower | negative | 96 | 100.00 | 88.89 | 88.89 | 98.10 | 96.20 | 93.70 | 97.00 | 96.90 | 97.40 | 97.90 | 97.90 | 96.30 | 5.30 | 91.50 |
| Packing | positive | 282 | 99.08 | 99.01 | 100.00 | 98.90 | 98.90 | 99.10 | 98.90 | 99.60 | 99.80 | 99.80 | 99.80 | 99.30 | 98.40 | 99.80 |
| Packing | negative | 10 | 80.00 | 80.00 | 100.00 | 75.00 | 76.90 | 78.30 | 75.00 | 90.00 | 94.70 | 94.70 | 94.70 | 81.80 | 0.00 | 95.20 |
| Shipping | positive | 334 | 100.00 | 99.21 | 94.74 | 98.10 | 99.00 | 97.50 | 98.40 | 98.50 | 98.90 | 98.80 | 98.90 | 98.30 | 98.60 | 98.50 |
| Shipping | negative | 174 | 100.00 | 98.11 | 94.55 | 96.30 | 98.10 | 95.10 | 97.00 | 97.10 | 98.00 | 97.70 | 98.00 | 96.80 | 97.30 | 97.10 |
| **MACRO** | positive | - | **98.49** | **98.48** | 97.51 | 98.31 | 98.41 | 97.67 | 98.17 | 98.61 | 98.87 | **98.93** | **98.93** | 98.51 | 93.33 | 97.67 |
| **MACRO** | negative | - | 74.45 | 74.20 | 73.35 | 80.59 | 87.20 | 82.04 | 83.20 | 84.73 | 80.90 | **88.93** | 81.23 | 78.11 | 14.66 | 77.57 |

Hai dòng MACRO ở bảng 6 là **bảng điểm chính để so công bố** của cả hai bản báo cáo:
`MACRO positive` (công bố tốt nhất 98,49) và `MACRO negative` (công bố tốt nhất 74,45).

## 8. Kết luận

1. **Dự án vượt công bố ở Accuracy macro** (97,70) ở **mọi** lượt CafeBERT, kể cả lượt CŨ: `exp002` +0,18 · `exp004` +0,56 · `exp013` +0,63 · `exp015` +0,65.
2. **Mục tiêu của đợt thí nghiệm MỚI đã đạt.** Bản CŨ (báo cáo v0) đạt lợi thế bằng đánh đổi (F1 lớp âm tăng mạnh, một phần Accuracy ở các khía cạnh công bố 100 % bị mất). Bản MỚI **giữ F1 tăng VÀ tăng Accuracy**: `exp015` cùng lúc đạt **Accuracy macro 98,35** (đỉnh) và **neg F1 macro (5 n lớn) 94,78** (đỉnh) và **pos F1 98,93** (đỉnh ngang `exp013`) ⇒ **vượt công bố ở cả Accuracy lẫn F1**.
3. **Top model CŨ = `cafebert/lora/exp004`** (98,26 %; khoảng nhiễu của cặp `exp002`-`exp004` là 97,88 … 98,26).
4. **Top model MỚI = `cafebert/lora/exp015`** (98,35 %; `lr 4e-4`). Về **F1 lớp âm**, `exp013` (`lora.r = 32`) cao nhất ở `macro (7)` (88,93) và `micro (theo n)` (95,12), nhưng khoản hơn ở `macro (7)` đến từ `price` `n = 5`.
5. **Chưa vượt ở 5/7 khía cạnh**: `price`, `texture`, `stayingpower`, `packing`, `shipping` mà công bố đạt 100 % thì dự án vẫn dưới. Đây là đánh đổi có chủ đích, không phải lỗi.
6. **Mức vượt so với bản CŨ nằm trong nhiễu.** `exp015` − `exp004` = +0,09 Accuracy · +0,46 F1 `n` lớn · +0,40 F1 micro, đều **dưới biên nhiễu ±0,7**. Mức vượt so CÔNG BỐ (+0,65 Accuracy, +6,55 F1 `n` lớn) thì **vượt biên nhiễu** nên đọc được.
7. **Trạng thái hợp lệ:** các lượt MỚI hiện **chưa được commit** vào `git` (đang `??`), nên theo luật 3-4 của `docs/00_workflow/02_rules.md` **chưa phải kết quả "dùng được"** cho tới khi commit đã ghim nằm trên nhánh `experiment` và đã chạy `scripts/collect_reports.py`.
8. **Đề xuất để chốt kết luận:** chạy thêm 2-3 seed cho hai cấu hình `lr 4e-4` và `lora.r = 32` (như đã làm cho `exp004`) để tách khỏi nhiễu, rồi mới đưa `exp015`/`exp013` lên làm đỉnh chính thức.

## 9. Nguồn số

- Công bố: `data/reference_publication/accuracy_by_aspect.csv` (Table 3) và `prf_by_aspect_sentiment_{0,1,5}shot.csv` (Table 4-6), đã đối chiếu từng ô với `announcement.md`.
- Dự án: `experiments/**/results/<hash8>/metrics.json`, khoá `scores_paper` (Accuracy) và `scores_paper.prf.by_aspect` (P/R/F1 + `support` = `n`).
- Hai thước đo mới (`neg F1 macro (5 n lớn)`, `neg F1 micro (theo n)`) **tính từ chính `prf.by_aspect`** (F1 và `support`) - không có đường tính thứ hai.
- Số của model CŨ trong mục 4-7 khớp đúng bảng của `present_report_v0.md`; số của model MỚI lấy từ `metrics.json` của chúng.

## Phụ lục A - Trạng thái các thí nghiệm (đo trên đĩa)

Tổng: **115 notebook** đã ghim; **100 lượt đã có `metrics.json`** (tất cả đã vào git ngày 11/10/2026).

| Nhóm | Số lượt | Đường dẫn |
| --- | ---: | --- |
| Đã có kết quả | 100 | `experiments/**/results/**/metrics.json` |
| **Chạy xong nhưng HỎNG (phân kỳ)** | 1 | `cafebert/full/exp001` (`trainer: full`, `lr 2e-4`) - `loss nan` từ bước 100, `val sentiment_f1 = 0`, `paper.cells = 0` |
| **Chưa chạy** (notebook đã ghim, chưa có `results/`) | 8 | `mistral-7b-instruct-v0.3/prompt-cot/exp001-003`, `qwen3-8b/prompt-cot/exp001-003`, `qwen3-4b-thinking-2507/prompt-cot/exp001-002` (`exp002` đang **CHỜ nhóm ghim lại**: trần token còn là giá trị tạm 4.096) |
| **HOÃN** | 4 | `qwen3-4b-instruct-2507/prompt-cot/exp018-021` (bốn lượt lấy mẫu seed 1/2/3 + đối chứng fp16 - "thước nhiễu đường prompt") |
| **HỦY BỎ (không bao giờ chạy)** | 2 | `qwen3-0.6b/prompt-cot/exp006`, `exp007` (nhánh BẬT suy nghĩ; HUỶ vì lượt `exp005` đọc được 96,98 % nhưng **detection F1 chỉ 0,479**) |
| **BỊ CHẶN (chưa tạo được notebook)** | - | `meta-llama/Llama-3.1-8B-Instruct`, `Viet-Mistral/Vistral-7B-Chat` - repo **GATED**, cần `HF_TOKEN` + nhận điều khoản |
| **Trong backlog, chưa từng tạo** | - | ViTASA (repo không có checkpoint); tập chẩn đoán GIÁ ~200-300 review; QLoRA cho Qwen3-4B; thăng cấp luật lai thành `method: fuse`; đo lại 19 bảng token khi thêm model |
| **Hướng đã CHẠY rồi BỎ (vẫn giữ kết quả làm bằng chứng)** | 2 | `head.aspect_marker` → `phobert-base-v2/lora/exp006`, `exp007` (kết quả tệ: 78,55 và 50,51 cơ sở `all`); hai tầng theo khía cạnh và router theo khía cạnh là **hướng phụ**, không vượt lượt đơn |

> **Đính chính 11/10/2026.** Bản trước của Phụ lục này ghi **4 lượt** "đã chạy nhưng hỏng / chưa xong". Số
> đúng là **1**: `cafebert/lora/exp010` (97,95), `cafebert/lora/exp012` (**98,14**) và
> `phobert-base-v2/lora/exp017` (95,44) **đã chạy xong và có đủ `metrics.json`** - chúng chỉ chưa có mặt
> trong lần đếm đầu của phiên làm việc. Trong đó `exp012` (`lora.r = 8`) **lọt top 4 toàn dự án** theo
> Accuracy và giữ **`neg F1 macro (7)` cao nhất (91,16)**. Chỉ `cafebert/full/exp001` là hỏng thật, và hỏng
> vì **phân kỳ** (`loss nan`), không phải bị ngắt.
>
> **Bổ sung 11/10/2026 (chẩn đoán đợt 12):** cả **ba** lượt nhánh `full` (`cafebert/full/exp001`,
> `phobert-base-v2/full/exp001`, `phobert-base-v2/full/exp002`) đều **thoái hoá**: dự đoán "không nhắc tới" cho
> **MỌI ô** ⇒ `sentiment_f1 = 0`, `paper.cells = 0` - hai lượt PhoBERT khác `lr` **10 lần** mà ra giống y hệt
> nhau. Vì vậy **mốc đối chứng "full fine-tune" trong tài liệu chưa dùng được.** Chi tiết:
> `present_plan_batch12.md` mục 9.2. `cafebert/full/exp001` còn **không có `metrics.json`** trên đĩa, nên kết
> luận về nó lấy từ `run.log`.
>
> **Chốt 11/10/2026 (người dùng):** nhánh `full` **BỊ BỎ khỏi kế hoạch** - không dùng làm mốc đối chứng nữa.
> Ba lượt giữ lại chỉ để đọc như "đã thử và hỏng".
>
> **Cập nhật 11/10/2026 - kết quả 8 lượt của đợt 12 (NHÓM 1-5) đã về.** `cafebert/lora/exp020/021/024/025/027/028/030/033`
> chạy xong, `% đọc được` = 100 % ở mọi lượt. **Không lượt nào vượt "top" quá 0,24 điểm** (biên nhiễu ±0,7)
> ⇒ **tất cả ĐỒNG HẠNG**, nên các bảng chính của báo cáo này **KHÔNG đổi**. Kỷ lục mới cần ghi:
> **Accuracy macro 98,41 %** và **pos F1 98,99 %** (`exp021`), **neg F1 micro 95,36 %** (`exp021`),
> **neg F1 (5 n lớn) 94,84 %** (`exp028`). Hai **kết quả ÂM**: `focal` + trọng số lớp **thất bại**
> (`exp024` 97,75 · `exp025` 97,71, kém CẢ HAI cha) và `segmenter: vncorenlp` trên `lr 4e-4` **không tái lập**
> (`exp033` 98,00 so cha 98,35). Chi tiết: `present_plan_batch12.md` mục 10.
>
> **Sáu lượt model sinh bị HỦY (11/10/2026):** `qwen3-8b` (đọc được 0,12-1,05 %) và `mistral-7b`
> (đọc được 60-72 %) - **3 ngày Colab cho 0 kết quả dùng được**; `llama-3.1-8b` và `vistral-7b` **bỏ trước khi
> tạo** (chi phí / GATED). ⇒ Báo cáo này **không có cột nào** cho bốn model đó.

Tra cứu chuẩn (không dùng tài liệu này): `python scripts/collect_reports.py --dry-run` → bảng `attempt_registry`; và `Get-ChildItem experiments/**/results/**/metrics.json` để đếm lượt đã xong.
