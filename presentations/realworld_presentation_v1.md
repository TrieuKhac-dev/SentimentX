# realworld_presentation_v1 - Đánh giá thực tế 60 review Shopee

> **Báo cáo RIÊNG cho đánh giá thực tế, KHÔNG phải bảng xếp hạng `v8`.**
> Không gộp số trong file này vào `present_report_v8.md`, không dùng nó để đổi thứ hạng hay kết luận
> model nào "tốt nhất" trên benchmark `v0.2.0`. Đây là phép đo khác: dữ liệu khác, cơ sở đếm khác, mẫu nhỏ.
>
> **Nguồn số:** `experiments/realworld/cafebert_exp027/a07f1c22/` và
> `experiments/realworld/qwen3_4b_exp009/27c3fa64/` - `metrics.json`, `run_meta.json`,
> `predictions.csv`. Mọi số dưới đây đọc trực tiếp từ hai thư mục đó.
>
> **Dữ liệu:** `data/raw/realworld/v0.1.0/shoppe_absa.csv`, sha256
> `3248709c8b6e36ca28c66fbe10b9efb57761f70e79f3245d09671afe59996af0` (giống nhau ở cả hai lượt).
>
> **Hai model:** CafeBERT `cafebert/lora/exp027@43e40f61` (lượt `a07f1c22`) và Qwen3-4B
> `qwen3-4b-instruct-2507/prompt-cot/exp009@7cf3331e` (lượt `27c3fa64`).

## 1. Tóm tắt điều hành

- **Mẫu:** 60 review Shopee x 7 khía cạnh = **420 ô**; **272 ô có nhắc tới**, **148 ô không nhắc tới**,
  **0 ô neutral**, **0 ô không đọc được**.
- **Qwen3-4B:** Accuracy **90,00%** (378/420); F1 phát hiện **92,4 macro / 92,6 micro**; exact review
  **28/60**; chỉ **3 ô đảo cực**.
- **CafeBERT:** Accuracy **86,90%** (365/420); F1 phát hiện **91,6 macro / 92,0 micro**; exact review
  **23/60**; **13 ô đảo cực**.
- **Qwen hơn 3,10 điểm phần trăm (pp)**, đúng **13 ô**, hơn rõ ở polarity (3 so với 13 ô đảo cực) và F1
  positive (0,951 so với 0,899). Nhưng Qwen **bỏ sót negative nhiều hơn** ở `price`, `texture`, `shipping`.
- **CafeBERT yếu nhất ở `packing`:** recall phát hiện **0,625**, bỏ **15/40** ô có nhắc tới; ở `price`,
  **7 ô NEG bị đoán thành POS**.
- **Cả hai bỏ sót negative nhiều hơn positive:** CafeBERT 18 NEG so với 14 POS; Qwen 19 NEG so với 10 POS.
- **Mẫu nhỏ:** mỗi khía cạnh 60 ô nên **1 ô = 1,67 pp**; không kiểm định ý nghĩa, không xếp hạng lại.

## 2. Dữ liệu và cách đo

### 2.1. Phân bố nhãn gold

| Khía cạnh    | Không nhắc tới | Positive | Negative | Tổng |
| ------------ | -------------: | -------: | -------: | ---: |
| Stayingpower |             21 |       19 |       20 |   60 |
| Texture      |             20 |       20 |       20 |   60 |
| Smell        |             23 |       19 |       18 |   60 |
| Price        |             23 |       19 |       18 |   60 |
| Colour       |             16 |       22 |       22 |   60 |
| Shipping     |             25 |       18 |       17 |   60 |
| Packing      |             20 |       22 |       18 |   60 |
| **Tổng**     |        **148** |  **139** |  **133** | **420** |

Tỉ lệ có nhắc tới: **64,8%** (272/420). Cấu hình chấm là `label_space: binary`,
`neutral_policy: drop`, `not_mentioned: separate`; số ô neutral bị drop = 0, số ô không đọc được = 0;
nhãn dự đoán chỉ chứa 0/1/2.

### 2.2. Bốn cách đo, không thay thế nhau

| Cách đo | Mẫu số | Trả lời câu hỏi |
| --- | ---: | --- |
| Accuracy `all` | 420 ô | Đúng cả nhãn lẫn việc nhận ra khía cạnh hay không |
| Accuracy `when-mentioned` | 272 ô gold có nhắc tới | Khi review có nói tới, model đọc đúng sắc thái không |
| Phát hiện khía cạnh (P/R/F1) | 420 ô | Có phân biệt "có nhắc tới" với "không nhắc tới" không |
| Exact review | 60 review | Đúng cả 7 ô của một review không |

`when-mentioned` vẫn **tính sai** khi model bỏ sót một ô có nhắc tới, nên nó thấp hơn Accuracy `all` ở cả
hai model (CafeBERT 83,56 so với 86,90; Qwen 88,10 so với 90,00, tính macro). Phát hiện khía cạnh là bài
toán nhị phân: `positive`/`negative` gộp thành "có nhắc tới", so với `not_mentioned`. Sentiment trên ô có
nhắc tới dùng đúng 272 ô gold; ô bị đoán thành `not_mentioned` là FN, không bị loại khỏi mẫu số.

### 2.3. Tập con `paper` 240/243 ô KHÔNG so được

`metrics.json` có thêm khối `scores_paper`: chỉ giữ ô mà **cả gold và dự đoán** là POS/NEG. Cách lọc này
cho **240 ô** ở CafeBERT (94,81%) và **243 ô** ở Qwen (98,79%), nhưng **không dùng để so hai model**:

- Mỗi model bị chấm trên tập con **do chính nó chọn**: CafeBERT bỏ 180 ô, Qwen bỏ 177 ô.
- Theo cách lọc, mọi ô bỏ sót và báo nhầm đều biến mất; F1 phát hiện vì thế bằng **1,000** một cách máy móc.
- Hai mẫu số khác nhau (240 so với 243) nên 94,81 so với 98,79 là hai phép đo trên hai tập khác nhau.

Mọi so sánh trong file này dùng **`scores` (all-basis)**; không trích 94,81/98,79 làm số tiêu đề.
Độ phân giải: 60 ô/khía cạnh -> **1 ô = 1,67 pp**; toàn bộ 420 ô -> 1 ô = 0,24 pp. Chênh 2 ô = 3,33 pp,
chênh 3 ô = 5,00 pp; với mẫu 60 và không có khoảng tin cậy, mức này **nằm trong nhiễu lấy mẫu**.

## 3. Kết quả tổng

| Thước đo | CafeBERT | Qwen3-4B | Δ (Qwen - CB) |
| --- | ---: | ---: | ---: |
| Accuracy macro | 86,90 | **90,00** | +3,10 pp |
| Accuracy micro | 86,90 | **90,00** | +3,10 pp |
| When-mentioned macro | 83,56 | **88,10** | +4,54 pp |
| When-mentioned micro | 83,46 | **88,24** | +4,78 pp |
| Ô đúng / tổng | 365/420 | **378/420** | +13 ô |
| Exact review | 23/60 (38,33%) | **28/60 (46,67%)** | +5 review (+8,34 pp) |
| F1 phát hiện macro | 0,916 | **0,924** | +0,008 |
| F1 phát hiện micro | 0,920 | **0,926** | +0,006 |
| F1 sentiment macro (272 ô) | 0,863 | **0,912** | +0,049 |
| F1 sentiment micro (272 ô) | 0,870 | **0,914** | +0,044 |

**Phát hiện khía cạnh:**

| Model | P macro | R macro | F1 macro | P micro | R micro | F1 micro |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| CafeBERT | 0,963 | 0,884 | 0,916 | 0,960 | 0,882 | 0,920 |
| Qwen3-4B | 0,963 | **0,891** | **0,924** | 0,960 | **0,893** | **0,926** |

Precision macro **bằng nhau** (0,963); chênh lệch phát hiện đến từ recall, tức Qwen bỏ sót ít hơn (29 so
với 32 ô). Cả hai cùng báo nhầm **10 ô**.

**Sentiment trên các ô có nhắc tới:**

| Model | P macro | R macro | F1 macro | P micro | R micro | F1 micro |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| CafeBERT | 0,919 | 0,835 | 0,863 | 0,908 | 0,835 | 0,870 |
| Qwen3-4B | **0,954** | **0,880** | **0,912** | **0,949** | **0,882** | **0,914** |

**Theo nhãn:**

| Nhãn | CafeBERT P / R / F1 | Qwen P / R / F1 |
| --- | --- | --- |
| Positive | 0,905 / 0,892 / 0,899 | **0,992** / **0,914** / **0,951** |
| Negative | **0,912** / 0,774 / 0,837 | 0,904 / **0,850** / **0,876** |

Qwen gần như không báo nhầm positive: **1 FP** trên 128 ô được đoán positive (precision 0,992). Ngược
lại, điểm yếu lớn nhất của CafeBERT là **recall negative 0,774** - bỏ sót 30 ô negative, so với 20 ô của
Qwen. Đây là lý do chính khiến Qwen hơn ở cả accuracy lẫn F1 sentiment, dù precision negative của
CafeBERT nhỉnh hơn.

## 4. Theo khía cạnh

Δ là **Qwen trừ CafeBERT**, tính trên số đã làm tròn; chênh 0,01 do làm tròn có thể xuất hiện.

| Khía cạnh | Cafe acc | Qwen acc | Δ (pp) | F1 phát hiện CB | F1 phát hiện Qwen |
| --- | ---: | ---: | ---: | ---: | ---: |
| Stayingpower | **91,67** | 88,33 | -3,34 | **0,947** | 0,911 |
| Texture | **83,33** | 80,00 | -3,33 | **0,907** | 0,868 |
| Smell | 95,00 | 95,00 | 0,00 | **0,961** | 0,959 |
| Price | 83,33 | **86,67** | +3,34 | **0,959** | 0,879 |
| Colour | 88,33 | **93,33** | +5,00 | 0,944 | **0,966** |
| Shipping | 91,67 | 91,67 | 0,00 | **0,925** | 0,923 |
| Packing | 75,00 | **95,00** | +20,00 | 0,769 | **0,962** |

- **Packing là khoảng cách lớn nhất: +20,00 pp = 12 ô.** Đây là khác biệt duy nhất vượt xa mức nhiễu.
  CafeBERT bỏ 15/40 ô packing có nhắc tới (recall 0,625); Qwen bỏ 2/40 (recall 0,950).
- **Colour +5,00 pp = 3 ô** - đúng ngưỡng nhiễu, chưa đủ kết luận. Qwen **kém hơn** ở `stayingpower` và
  `texture`, mỗi khía cạnh 2 ô (-3,34 và -3,33 pp).
- **Price:** accuracy Qwen hơn 3,34 pp nhưng F1 phát hiện **kém 0,080**. Qwen bỏ 8 ô price có nhắc tới
  (recall phát hiện 0,784) so với 2 ô của CafeBERT (0,946); bù lại Qwen không báo nhầm ô price nào
  (precision 1,000).
- **Smell tốt nhất ở cả hai** (cùng 95,00). **Texture là đáy chung** (83,33 và 80,00); xét tuyệt đối, đáy
  của CafeBERT là `packing` 75,00 - điểm yếu riêng của model này.

| Model | Ô yếu nhất | F1 |
| --- | --- | ---: |
| CafeBERT | `price` negative (P 0,900 / R 0,500) | **0,643** |
| CafeBERT | `packing` positive (P 1,000 / R 0,591) | **0,743** |
| CafeBERT | `texture` negative (P 0,882 / R 0,750) | 0,811 |
| Qwen3-4B | `texture` negative (P 0,789 / R 0,750) | **0,769** |
| Qwen3-4B | `price` negative (P 1,000 / R 0,667) | 0,800 |

Ở `packing`, CafeBERT precision positive 1,000 nhưng recall 0,591: chỉ gán positive khi cue rất rõ, còn
lại đẩy về "không nhắc tới". Ở `price`, precision negative 0,900 nhưng recall 0,500: một nửa ô negative
bị bỏ hoặc bị lật. **Cảnh báo nhiễu:** mọi chênh lệch 1-3 ô (kể cả colour +5,00) **không đủ kết luận**;
chỉ packing +20,00 pp là khác biệt lớn.

## 5. Lỗi và nguyên nhân

### 5.1. Cơ cấu lỗi

| Model | Tổng lỗi | Bỏ sót | Báo nhầm | Đảo cực |
| --- | ---: | ---: | ---: | ---: |
| CafeBERT | 55 | 32 (18 NEG / 14 POS) | 10 | 13 (12 NEG->POS, 1 POS->NEG) |
| Qwen3-4B | 42 | 29 (19 NEG / 10 POS) | 10 | 3 (1 NEG->POS, 2 POS->NEG) |

Cả hai cùng báo nhầm 10 ô. Chênh lệch 13 lỗi nằm ở **bỏ sót ít hơn 3 ô** và **đảo cực ít hơn 10 ô**.

### 5.2. Lỗi phổ biến nhất

| Model | Chuyển nhãn | Số ô |
| --- | --- | ---: |
| CafeBERT | packing POS -> NM | **9** |
| CafeBERT | price NEG -> POS | **7** |
| CafeBERT | packing NEG -> NM | **6** |
| CafeBERT | texture NEG -> NM | 3 |
| CafeBERT | texture POS -> NM | 3 |
| CafeBERT | smell NM -> NEG | 3 |
| CafeBERT | shipping NEG -> NM | 3 |
| Qwen3-4B | price NEG -> NM | **6** |
| Qwen3-4B | stayingpower NM -> NEG | **4** |
| Qwen3-4B | texture NEG -> NM | **4** |
| Qwen3-4B | shipping NEG -> NM | **4** |
| Qwen3-4B | texture POS -> NM | 3 |
| Qwen3-4B | texture NM -> NEG | 3 |

### 5.3. Trùng lặp giữa hai model

- **19 ô cùng sai**; **36 ô chỉ CafeBERT sai**; **23 ô chỉ Qwen sai**.
- Theo review: **16 review cả hai cùng đúng**, **25 review cả hai cùng sai**, **7 review chỉ CafeBERT
  đúng**, **12 review chỉ Qwen đúng**.

25/60 review cùng sai cho thấy phần lớn lỗi không phải "model này dở hơn model kia" mà là **độ khó chung
của dữ liệu và nhãn**.

### 5.4. Cơ chế lỗi của CafeBERT

- **Từ vựng packing bị bỏ qua.** 15/40 ô packing có nhắc tới bị đoán thành `not_mentioned`; 12/15 ô đó
  chứa ít nhất một từ khoá đóng gói (`vỏ`, `hộp`, `bao bì`, `nắp`, `bọc`), ví dụ row 1 (`vỏ`), row 2
  (`bao bì`), row 9 (`hộp`), row 58 (`vỏ`), row 59 (`bao bì`, `vỏ`). Precision packing 1,000 nhưng recall
  0,625: model chỉ gán khi cue trùng mẫu huấn luyện.
- **Polarity `price`:** 7 ô NEG thành POS. Row 9 viết "son tệ nhất trong phân khúc **giá rẻ**" - cụm "giá
  rẻ" bị đọc thành tín hiệu positive, trong khi "tệ nhất" mới là nhãn gold.
- **Báo nhầm smell/shipping:** 3 ô smell và 1 ô shipping bị gán negative, confidence thường thấp (0,544;
  0,627; 0,772), riêng row 49 là 1,000 - confidence không đáng tin.
- **Confidence không calibrated:** trung bình **0,968 ở ô đúng** và **0,824 ở ô sai**. Khoảng cách 0,144
  đúng hướng, nhưng có ô sai với confidence 1,000, nên **không dùng confidence làm ngưỡng tin cậy**.

### 5.5. Cơ chế lỗi của Qwen3-4B

- **Bỏ sót negative** là lỗi chính: 19 NEG->NM so với 10 POS->NM, tập trung ở `price` (6), `texture` (4),
  `shipping` (4). Lý do model đưa ra thường là "không có thông tin về giá" hoặc "chỉ nêu giá, không đánh
  giá" - Qwen đòi cue tường minh hơn gold.
- **Báo nhầm negative ở `stayingpower`:** 4 ô NM->NEG (row 9, 20, 22, 25), thường do cue khô môi/chất
  lượng kém bị quy về độ bền.
- **Chỉ 3 ô đảo cực**, so với 13 của CafeBERT: Qwen ít lật dấu hơn hẳn, kể cả khi bỏ sót.

### 5.6. Cùng sai và cùng đúng

| Nhóm | Review | Nội dung |
| --- | --- | --- |
| Cùng sai | 45 | "Giữ màu tố" nhưng cả hai để `stayingpower` = NM; gold = 1 |
| Cùng sai | 21 | So sánh ngầm với "lần trước ... ẩm hơn nhiều"; cả hai để `texture` = NM; gold = 2 |
| Cùng sai | 49 | "không có mùi thơm"; cả hai gán `smell` = NEG; gold = 0 (nhãn đáng ngờ) |
| Cùng đúng | 19 | Cả 7 khía cạnh đều POS, cả hai đúng 7/7 |
| Cùng đúng | 6 | Cả 7 khía cạnh đúng, gồm 5 NEG và 2 NM |

## 6. Đọc kèm chất lượng nhãn

| Review | Khía cạnh | Gold | Cả hai đoán | Cue trong text | Vấn đề |
| ---: | --- | ---: | ---: | --- | --- |
| 25 | stayingpower | 0 | 2 | "để một khoảng thời gian nó trôi đi môi lại khô" | Cue negative rõ nhưng gold để NM |
| 23 | packing | 1 | 0 | "k bị tràn son ra" | Cue positive rất mờ, chỉ là phủ định sự cố |
| 49 | smell | 0 | 2 | "không có mùi thơm" | Câu phủ định bị đọc là negative, gold để NM |
| 7 | price, shipping | 2, 2 | 0, 0 | mất quà tặng, "hộp ... bị mốp" | Gold suy ra từ quà/bao bì, text không nói trực tiếp |

Không dùng bốn ca này để **bào chữa** cho 55/42 lỗi - chúng chỉ chiếm một phần nhỏ. Nhưng chúng đủ để nói
rằng **trần accuracy trên mẫu này bị giới hạn bởi chất lượng nhãn**, và mọi tuyên bố deployment cần một
vòng audit nhãn riêng.

## 7. So sánh và diễn giải

| Tiêu chí | CafeBERT | Qwen3-4B | Đọc |
| --- | --- | --- | --- |
| Accuracy all | 86,90 | **90,00** | Qwen hơn 3,10 pp = 13 ô |
| Polarity | 13 ô đảo | **3 ô đảo** | Qwen ít lật dấu hơn hẳn |
| F1 positive | 0,899 | **0,951** | Qwen gần như không báo nhầm POS |
| F1 negative | 0,837 | **0,876** | Qwen hơn nhờ recall 0,850 so với 0,774 |
| Phát hiện `price` | **0,959** | 0,879 | CB hơn nhờ recall 0,946 so với 0,784 |
| Phát hiện `packing` | 0,769 | **0,962** | Qwen hơn 0,193 |
| Thời gian | **66,792 s** | 1.263,742 s | Qwen chậm ~18,9 lần |

**Về `price`:** CafeBERT tốt hơn detection price **nhưng chỉ ở recall và F1**. Precision detection của
Qwen là 1,000, cao hơn 0,972 của CafeBERT; CafeBERT hơn vì bắt 35/37 ô price có nhắc tới, còn Qwen bắt
29/37.

**Về tốc độ:** 66,792 s so với 1.263,742 s (**~18,9 lần**) không phải latency thuần của model. CafeBERT
chạy batch 16; Qwen chạy chunk 1, lượng tử 4-bit, sinh tối đa 400 token mỗi review. Con số này đo
**pipeline**, không đo kiến trúc.

**Không model nào production-ready trên mẫu này:** còn 42-55 lỗi/420 ô; exact review chỉ 23-28/60;
**25/60 review cả hai cùng sai**; không hỗ trợ neutral; nhãn có nhiễu; mẫu 60 review. Qwen cho **chất
lượng câu trả lời tốt hơn** nhưng chậm hơn nhiều và **bỏ sót negative** ở price/texture/shipping.
CafeBERT **nhanh hơn**, phát hiện price tốt hơn, nhưng hỏng `packing` và lật dấu price 7 ô.

### 7.1. Đặt cạnh benchmark `v0.2.0`

| Model | Test `v0.2.0` (paper) | Thực tế Shopee (all) | Chênh |
| --- | ---: | ---: | ---: |
| CafeBERT `exp027` | 98,56 | 86,90 | -11,66 pp |
| Qwen3-4B `exp009` | 97,77 | 90,00 | -7,77 pp |

Hai cột **không so trực tiếp được**: khác miền dữ liệu (test chuẩn so với review Shopee thật), khác cơ sở
đếm (paper so với all), khác quy trình gán nhãn, khác kích thước mẫu. Chênh lệch này **mô tả domain
shift**, không phải "model tụt 11 điểm". Tập con `paper` của chính đánh giá thực tế (94,81 và 98,79) càng
**không dùng làm số tiêu đề**: nó bị inflate vì đã bỏ mọi ô bỏ sót/báo nhầm, và mỗi model bị lọc trên một
tập khác nhau.

## 8. Hạn chế

- **60 review**, phân bố khá cân nhưng vẫn nhỏ; 60 ô/khía cạnh; **1 ô = 1,67 pp**; không có khoảng tin cậy
  và không kiểm định ý nghĩa.
- **Domain shift** so với `v0.2.0`: review Shopee ngắn, teencode, emoji, thiếu dấu.
- **Không có neutral** trong phép chấm; không đo được hành vi với sắc thái trung tính.
- **Nhãn thưa và có nhiễu** ở một số ô (mục 6); gold đôi khi suy luận từ ngữ cảnh thay vì câu chữ.
- **Qwen không có confidence** (`include_probs: false`); **confidence của CafeBERT chưa calibrated**
  (0,968 đúng so với 0,824 sai).
- Chỉ **hai model**, một lượt mỗi model; không suy rộng cho toàn bộ thương mại điện tử.
- Kết quả này là **mô tả**, không phải bảng xếp hạng mới và không thay đổi `v8`.

## 9. Kết luận

- Qwen3-4B **hơn accuracy (90,00 so với 86,90), polarity (3 so với 13 ô đảo cực) và F1 positive** trên
  mẫu thực tế này.
- CafeBERT **nhanh hơn ~18,9 lần** và phát hiện `price` tốt hơn (F1 0,959 so với 0,879), nhưng hỏng
  `packing` với recall 0,625.
- **Bỏ sót negative là điểm yếu chung**: 18/32 lỗi bỏ sót của CafeBERT và 19/29 của Qwen là NEG; recall
  negative 0,774 so với 0,850.
- **Packing là khoảng cách riêng của model**, không phải của dữ liệu: +20,00 pp, 12 ô, do từ vựng
  `vỏ`/`hộp`/`bao bì` không được CafeBERT nhận ra.
- Chênh lệch 1-3 ô (1,67-5,00 pp) **nằm trong nhiễu**; chỉ packing là khác biệt lớn.
- Cần **mẫu lớn hơn và audit nhãn** trước mọi tuyên bố deployment; không gộp báo cáo này vào `v8`.

## 10. Nguồn và kiểm lại

| Việc | Tệp |
| --- | --- |
| CafeBERT metrics | `experiments/realworld/cafebert_exp027/a07f1c22/metrics.json` |
| CafeBERT provenance | `experiments/realworld/cafebert_exp027/a07f1c22/run_meta.json` |
| CafeBERT dự đoán từng ô | `experiments/realworld/cafebert_exp027/a07f1c22/predictions.csv` |
| Qwen metrics | `experiments/realworld/qwen3_4b_exp009/27c3fa64/metrics.json` |
| Qwen provenance | `experiments/realworld/qwen3_4b_exp009/27c3fa64/run_meta.json` |
| Qwen dự đoán từng ô | `experiments/realworld/qwen3_4b_exp009/27c3fa64/predictions.csv` |
| Dữ liệu gốc | `data/raw/realworld/v0.1.0/shoppe_absa.csv` |

- **Cùng một file dữ liệu:** `csv_sha256` =
  `3248709c8b6e36ca28c66fbe10b9efb57761f70e79f3245d09671afe59996af0` ở cả hai lượt.
- **0 lỗi runtime:** `n_rows` = 60, `n_errors` = 0, `runtime_errors` = [] ở cả hai.
- **Ma trận nhầm lẫn tái lập được:** 420 = 272 có nhắc tới + 148 không nhắc tới; 365 + 55 = 420
  (CafeBERT) và 378 + 42 = 420 (Qwen).
- **Tập con paper:** 240 ô (CafeBERT) và 243 ô (Qwen), khớp `paper.cells`; `dropped_unreadable` = 0.
- **Đối chiếu chéo:** các ca ở mục 5.6 và 6 (row 45, 21, 49, 19, 6, 25, 23, 7) đã được kiểm trực tiếp
  trên `predictions.csv`.

### 10.1. Phiên bản và cấu hình

| Thành phần | CafeBERT | Qwen3-4B |
| --- | --- | --- |
| `model_version` | `cafebert/lora/exp027@43e40f61` | `qwen3-4b-instruct-2507/prompt-cot/exp009@7cf3331e` |
| Base / checkpoint | `uitnlp/CafeBERT` @ `af76fcf2...`, best `43e40f61` | `Qwen3-4B-Instruct-2507` snapshot `cdbee75f...` |
| `max_length` | 256 | 2.304 |
| Lượng tử | `auto` | 4-bit |
| `chunk` | 16 | 1 |
| `include_probs` | true | false |
| Thời gian | 66,792 s | 1.263,742 s |
| Config layers | 7 (`model`, `repo`, `task`, `evaluation`, `training`, `tracking`, `experiment`) | 7 (như nhau) |

### 10.2. Lưu ý provenance của CafeBERT

Bản **`a07f1c22` là lượt chạy lại hợp lệ**: 0 lỗi runtime, 60/60 review, Accuracy 86,90. Không dùng một
kết quả 0,0 của lượt hỏng trước đó nếu nó xuất hiện ở nơi khác; con số 0,0 là lỗi chạy, không phải năng
lực model.

Báo cáo này không sửa và không thay đổi bất kỳ nội dung nào của present_report_v8.md.
