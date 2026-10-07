# present_report - Đối chiếu dự án với công bố tham chiếu

> Đọc file này khi: trình bày kết quả dự án so với công bố tham chiếu.
> Liên quan: `docs/04_experiments/reference_publication.md`, `data/reference_publication/`, `table3_accuracy_by_aspect.csv`

## 1. Tóm tắt

Công bố tham chiếu (GPT-4o-mini, Chain-of-Thought 0/1/5-shot) đạt accuracy rất cao
(macro 96,74-97,70%) nhưng chỉ trên **một mô hình**, **một thước đo dễ** (lọc hai chiều) và
**bỏ qua lớp khó nhất**. Dự án không nhắm vượt công bố ở accuracy tổng (lệch chỉ 0,1-0,5 điểm,
trong cỡ nhiễu), mà nhắm thẳng vào bốn điểm yếu có bằng chứng dưới đây.

## 2. Điểm yếu của công bố (có bằng chứng)

| # | Điểm yếu | Bằng chứng |
| --- | --- | --- |
| W1 | Không đo "có nhắc tới hay không" (phát hiện khía cạnh) | `announcement.md` chỉ có bảng positive/negative; `reference_publication.md` xác nhận bài không có số cho detection |
| W2 | Lớp âm ở khía cạnh chủ quan sụp | Tables 4-6: SMELL-âm F1 = 66,67 / 66,67 / 50; PRICE-âm = 0 ở cả ba mức; bài tự viết "negative F1 ... around 50%" |
| W3 | Thước hai chiều làm mẫu số phụ thuộc model, che ô model trả lời sai; không công bố số ô | Dựng lại Table 3: SMELL chỉ ~37 ô hai chiều, lớp âm chỉ ~2 ô |
| W4 | Một mô hình, không ablation, không bảo đảm tái lập | Chỉ GPT-4o-mini; artifact `accuracy_by_aspect.csv` từng lệch nhãn cột một hàng |

## 3. Bảy thử nghiệm được chọn

Ba lượt LLM = tốt nhất ở **mỗi mức ví dụ**; bốn lượt encoder = hai mạnh nhất + một **cặp đối chứng hàm mất mát**.

| # | Lượt | Mức / Vai | Căn cứ (số của CHÍNH lượt đó, cơ sở `paper`) | Trục |
| --- | --- | --- | --- | --- |
| P1 | `qwen3-4b-instruct-2507/prompt-cot/exp008` | 0 ví dụ | acc macro 97,26; Stayingpower acc 98,54 & F1-âm 0,981 | mức ví dụ 0 |
| P2 | `qwen3-4b-instruct-2507/prompt-cot/exp009` | 1 ví dụ | acc macro 97,77 (> công bố 97,70); Smell F1-âm 0,933 (43 ô) vs 0,667 | mức ví dụ 1 |
| P3 | `qwen3-4b-instruct-2507/prompt-cot/exp010` | 5 ví dụ | acc macro 97,19 (> công bố 96,74); Smell F1-âm 0,907 vs 0,50 | mức ví dụ 5 |
| E1 | `cafebert/lora/exp002` | encoder | acc macro 97,88 (> mức tốt nhất công bố 97,70); detection macro-F1 0,967 | encoder mạnh nhất |
| E2 | `phobert-large/lora/exp002` | encoder | acc macro 97,69; Texture acc 98,11 & F1-âm 0,951 (tốt nhất dự án) | quy mô lớn |
| E3 | `phobert-base-v2/lora/exp001` | encoder (đối chứng) | nhánh CE của cặp hàm mất mát (acc 88,40; F1-âm 14,7%) | hàm mất mát - nhánh đối chứng |
| E4 | `phobert-base-v2/lora/exp002` | encoder | nhánh weighted_ce (acc 96,62; F1-âm 77,6%); Packing tốt nhất dự án 99,65 | hàm mất mát - nhánh xử lý |

Ghi chú: E3 và E4 là **một cặp** - khác nhau ĐÚNG khoá `loss.type` (CE <-> weighted_ce). Cặp này là
bằng chứng duy nhất trong dự án chứng minh **lớp âm sửa được bằng hàm mất mát** (F1-âm macro
14,7% -> 77,6%). E3 được đưa vào với vai **đối chứng**, không phải "vượt trội" - thiếu nó thì trục
hàm mất mát không hiện được trong bảng.

Quy tắc phân bổ trong các bảng dưới: **P1 chỉ ở bảng 0 ví dụ; P2 chỉ ở bảng 1 ví dụ; P3 chỉ ở
bảng 5 ví dụ; bốn lượt encoder (E1-E4) có mặt ở CẢ bốn bảng** (Table 3 và Tables 4-6).

## 4. Table 3 - Accuracy theo khía cạnh (%)

`table3_accuracy_by_aspect.csv`. Mỗi lượt dự án đứng cạnh mức ví dụ của chính nó; encoder đứng cuối bảng.

| Aspect | COT+0-shot | exp008 (0) | COT+1-shot | exp009 (1) | COT+5-shot | exp010 (5) | cafebert/lora/exp002 | phobert-large/lora/exp002 | phobert-base-v2/lora/exp001 | phobert-base-v2/lora/exp002 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Smell | 94.59 | 95.26 | 96.15 | **97.44** | 92.86 | **96.09** | 96.28 | 96.92 | 84.48 | 95.92 |
| Price | 97.22 | 96.25 | 100 | 98.49 | 100 | 98.45 | 99.07 | 98.13 | 98.45 | 98.14 |
| Texture | 94.12 | **97.67** | 100 | 96.86 | 100 | 96.06 | 97.42 | **98.11** | 83.86 | 95.55 |
| Colour | 97.37 | 97.67 | 96.61 | **98.82** | 94.74 | 96.56 | 97.60 | 97.28 | 92.27 | 96.41 |
| Stayingpower | 100 | 98.54 | 94.12 | **96.15** | 92.86 | **97.37** | 97.45 | 96.98 | 64.71 | 92.67 |
| Packing | 98.25 | 97.90 | 98.11 | 97.90 | 100 | 97.89 | 99.30 | 98.61 | 96.83 | **99.65** |
| Shipping | 100 | 97.51 | 98.89 | 98.72 | 96.70 | **97.94** | 98.02 | 97.82 | 98.19 | 98.02 |
| **Macro** | 97.36 | 97.26 | 97.70 | **97.77** | 96.74 | **97.19** | **97.88** | 97.69 | 88.40 | 96.62 |

Đọc nhanh: dự án **hơn** ở Smell / Colour / Stayingpower (khía cạnh chủ quan), **thua** ở Texture /
Price / Packing / Shipping (khía cạnh định lượng - nơi công bố chạm 100).

## 5. Tables 4-6 - Precision / Recall / F1 theo khía cạnh và sắc thái

Mỗi nguồn là **ba cột** `P`, `R`, `F1`; mỗi ô ghi **`positive / negative`** (ví dụ `97.06 / 66.67`
= precision lớp dương 97,06 và lớp âm 66,67). Cách này gọn một nửa so với tách riêng
`Positive Precision` ... `Negative F1-score` thành sáu cột như công bố.

Tên nguồn trên tiêu đề cột chính là tên lượt chạy: `COT+0shot / COT+1shot / COT+5shot` = công bố;
`exp008 / exp009 / exp010` = ba lượt Qwen3-4B; `cafebert_lora_exp002`, `phobert-large_lora_exp002`,
`phobert-base-v2_lora_exp001`, `phobert-base-v2_lora_exp002` = bốn lượt encoder (có mặt ở cả ba bảng).
(Số gốc: `table4_prf_0shot.csv`, `table5_prf_1shot.csv`, `table6_prf_5shot.csv`.)

### 5.1. Table 4 - 0 ví dụ (`table4_prf_0shot.csv`)

| Aspect | COT+0shot P | COT+0shot R | COT+0shot F1 | exp008 P | exp008 R | exp008 F1 | cafebert_lora_exp002 P | cafebert_lora_exp002 R | cafebert_lora_exp002 F1 | phobert-large_lora_exp002 P | phobert-large_lora_exp002 R | phobert-large_lora_exp002 F1 | phobert-base-v2_lora_exp001 P | phobert-base-v2_lora_exp001 R | phobert-base-v2_lora_exp001 F1 | phobert-base-v2_lora_exp002 P | phobert-base-v2_lora_exp002 R | phobert-base-v2_lora_exp002 F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Smell | 97.06 / 66.67 | 97.06 / 66.67 | 97.06 / 66.67 | 99.1 / 80.4 | 95.2 / 95.7 | 97.1 / 87.4 | 98.8 / 84.9 | 96.8 / 93.8 | 97.8 / 89.1 | 99.6 / 85.5 | 96.7 / 97.9 | 98.1 / 91.3 | 84.5 / 0 | 100 / 0 | 91.6 / 0 | 99.6 / 81.0 | 95.5 / 97.9 | 97.5 / 88.7 |
| Price | 100 / 0 | 97.22 / 0 | 98.59 / 0 | 100 / 15.4 | 96.2 / 100 | 98.1 / 26.7 | 99.1 / 100 | 100 / 25.0 | 99.5 / 40.0 | 98.1 / 0 | 100 / 0 | 99.1 / 0 | 98.4 / 0 | 100 / 0 | 99.2 / 0 | 98.1 / 0 | 100 / 0 | 99.1 / 0 |
| Texture | 92.68 / 100 | 100 / 76.92 | 96.20 / 86.96 | 99.6 / 91.0 | 97.5 / 98.4 | 98.5 / 94.6 | 98.5 / 92.8 | 98.3 / 93.9 | 98.4 / 93.3 | 98.8 / 95.1 | 98.8 / 95.1 | 98.8 / 95.1 | 83.9 / 0 | 100 / 0 | 91.2 / 0 | 99.1 / 83.2 | 95.4 / 96.3 | 97.2 / 89.3 |
| Colour | 100 / 77.78 | 97.10 / 100 | 98.53 / 87.50 | 99.3 / 80.7 | 98.1 / 92.0 | 98.7 / 86.0 | 99.7 / 78.8 | 97.7 / 96.3 | 98.7 / 86.7 | 99.8 / 75.7 | 97.2 / 98.1 | 98.5 / 85.5 | 92.3 / 0 | 100 / 0 | 96.0 / 0 | 99.7 / 70.3 | 96.4 / 96.3 | 98.0 / 81.2 |
| Stayingpower | 100 / 100 | 100 / 100 | 100 / 100 | 98.8 / 98.1 | 98.8 / 98.1 | 98.8 / 98.1 | 98.6 / 95.9 | 97.1 / 97.9 | 97.8 / 96.9 | 97.8 / 95.7 | 97.1 / 96.8 | 97.5 / 96.3 | 64.4 / 100 | 100 / 2.7 | 78.3 / 5.3 | 98.4 / 85.8 | 89.2 / 97.8 | 93.6 / 91.5 |
| Packing | 100 / 66.67 | 98.18 / 100 | 99.08 / 80 | 100 / 60.0 | 97.8 / 100 | 98.9 / 75.0 | 100 / 81.8 | 99.3 / 100 | 99.6 / 90.0 | 99.6 / 75.0 | 98.9 / 90.0 | 99.3 / 81.8 | 96.8 / 0 | 100 / 0 | 98.4 / 0 | 100 / 90.9 | 99.6 / 100 | 99.8 / 95.2 |
| Shipping | 100 / 100 | 100 / 100 | 100 / 100 | 98.4 / 95.7 | 97.8 / 96.9 | 98.1 / 96.3 | 99.1 / 96.0 | 97.9 / 98.2 | 98.5 / 97.1 | 99.4 / 94.9 | 97.3 / 98.8 | 98.3 / 96.8 | 98.5 / 97.6 | 98.8 / 97.0 | 98.6 / 97.3 | 99.1 / 96.0 | 97.9 / 98.3 | 98.5 / 97.1 |

### 5.2. Table 5 - 1 ví dụ (`table5_prf_1shot.csv`)

| Aspect | COT+1shot P | COT+1shot R | COT+1shot F1 | exp009 P | exp009 R | exp009 F1 | cafebert_lora_exp002 P | cafebert_lora_exp002 R | cafebert_lora_exp002 F1 | phobert-large_lora_exp002 P | phobert-large_lora_exp002 R | phobert-large_lora_exp002 F1 | phobert-base-v2_lora_exp001 P | phobert-base-v2_lora_exp001 R | phobert-base-v2_lora_exp001 F1 | phobert-base-v2_lora_exp002 P | phobert-base-v2_lora_exp002 R | phobert-base-v2_lora_exp002 F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Smell | 100 / 50 | 96 / 100 | 97.06 / 66.67 | 99.5 / 89.4 | 97.4 / 97.7 | 98.4 / 93.3 | 98.8 / 84.9 | 96.8 / 93.8 | 97.8 / 89.1 | 99.6 / 85.5 | 96.7 / 97.9 | 98.1 / 91.3 | 84.5 / 0 | 100 / 0 | 91.6 / 0 | 99.6 / 81.0 | 95.5 / 97.9 | 97.5 / 88.7 |
| Price | 100 / 0 | 100 / 0 | 100 / 0 | 99.6 / 50.0 | 98.9 / 75.0 | 99.2 / 60.0 | 99.1 / 100 | 100 / 25.0 | 99.5 / 40.0 | 98.1 / 0 | 100 / 0 | 99.1 / 0 | 98.4 / 0 | 100 / 0 | 99.2 / 0 | 98.1 / 0 | 100 / 0 | 99.1 / 0 |
| Texture | 100 / 100 | 100 / 100 | 100 / 100 | 99.6 / 88.7 | 96.3 / 98.6 | 97.9 / 93.4 | 98.5 / 92.8 | 98.3 / 93.9 | 98.4 / 93.3 | 98.8 / 95.1 | 98.8 / 95.1 | 98.8 / 95.1 | 83.9 / 0 | 100 / 0 | 91.2 / 0 | 99.1 / 83.2 | 95.4 / 96.3 | 97.2 / 89.3 |
| Colour | 100 / 75 | 96.23 / 100 | 98.08 / 85.71 | 100 / 86.0 | 98.7 / 100 | 99.4 / 92.5 | 99.7 / 78.8 | 97.7 / 96.3 | 98.7 / 86.7 | 99.8 / 75.7 | 97.2 / 98.1 | 98.5 / 85.5 | 92.3 / 0 | 100 / 0 | 96.0 / 0 | 99.7 / 70.3 | 96.4 / 96.3 | 98.0 / 81.2 |
| Stayingpower | 100 / 80 | 92.31 / 100 | 96 / 88.89 | 98.7 / 93.8 | 93.7 / 98.7 | 96.1 / 96.2 | 98.6 / 95.9 | 97.1 / 97.9 | 97.8 / 96.9 | 97.8 / 95.7 | 97.1 / 96.8 | 97.5 / 96.3 | 64.4 / 100 | 100 / 2.7 | 78.3 / 5.3 | 98.4 / 85.8 | 89.2 / 97.8 | 93.6 / 91.5 |
| Packing | 100 / 66.67 | 98.04 / 100 | 99.01 / 80 | 100 / 62.5 | 97.8 / 100 | 98.9 / 76.9 | 100 / 81.8 | 99.3 / 100 | 99.6 / 90.0 | 99.6 / 75.0 | 98.9 / 90.0 | 99.3 / 81.8 | 96.8 / 0 | 100 / 0 | 98.4 / 0 | 100 / 90.9 | 99.6 / 100 | 99.8 / 95.2 |
| Shipping | 100 / 96.3 | 98.44 / 100 | 99.21 / 98.11 | 99.0 / 98.1 | 99.0 / 98.1 | 99.0 / 98.1 | 99.1 / 96.0 | 97.9 / 98.2 | 98.5 / 97.1 | 99.4 / 94.9 | 97.3 / 98.8 | 98.3 / 96.8 | 98.5 / 97.6 | 98.8 / 97.0 | 98.6 / 97.3 | 99.1 / 96.0 | 97.9 / 98.3 | 98.5 / 97.1 |

### 5.3. Table 6 - 5 ví dụ (`table6_prf_5shot.csv`)

| Aspect | COT+5shot P | COT+5shot R | COT+5shot F1 | exp010 P | exp010 R | exp010 F1 | cafebert_lora_exp002 P | cafebert_lora_exp002 R | cafebert_lora_exp002 F1 | phobert-large_lora_exp002 P | phobert-large_lora_exp002 R | phobert-large_lora_exp002 F1 | phobert-base-v2_lora_exp001 P | phobert-base-v2_lora_exp001 R | phobert-base-v2_lora_exp001 F1 | phobert-base-v2_lora_exp002 P | phobert-base-v2_lora_exp002 R | phobert-base-v2_lora_exp002 F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Smell | 96.15 / 50 | 96.15 / 50 | 96.15 / 50 | 99.4 / 84.6 | 95.7 / 97.8 | 97.5 / 90.7 | 98.8 / 84.9 | 96.8 / 93.8 | 97.8 / 89.1 | 99.6 / 85.5 | 96.7 / 97.9 | 98.1 / 91.3 | 84.5 / 0 | 100 / 0 | 91.6 / 0 | 99.6 / 81.0 | 95.5 / 97.9 | 97.5 / 88.7 |
| Price | 100 / 0 | 100 / 0 | 100 / 0 | 100 / 33.3 | 98.4 / 100 | 99.2 / 50.0 | 99.1 / 100 | 100 / 25.0 | 99.5 / 40.0 | 98.1 / 0 | 100 / 0 | 99.1 / 0 | 98.4 / 0 | 100 / 0 | 99.2 / 0 | 98.1 / 0 | 100 / 0 | 99.1 / 0 |
| Texture | 100 / 100 | 100 / 100 | 100 / 100 | 98.5 / 87.7 | 96.4 / 94.7 | 97.5 / 91.0 | 98.5 / 92.8 | 98.3 / 93.9 | 98.4 / 93.3 | 98.8 / 95.1 | 98.8 / 95.1 | 98.8 / 95.1 | 83.9 / 0 | 100 / 0 | 91.2 / 0 | 99.1 / 83.2 | 95.4 / 96.3 | 97.2 / 89.3 |
| Colour | 100 / 66.67 | 94.12 / 100 | 96.97 / 80 | 99.5 / 72.3 | 96.8 / 94.0 | 98.1 / 81.7 | 99.7 / 78.8 | 97.7 / 96.3 | 98.7 / 86.7 | 99.8 / 75.7 | 97.2 / 98.1 | 98.5 / 85.5 | 92.3 / 0 | 100 / 0 | 96.0 / 0 | 99.7 / 70.3 | 96.4 / 96.3 | 98.0 / 81.2 |
| Stayingpower | 100 / 80 | 90 / 100 | 94.74 / 88.89 | 98.8 / 95.6 | 96.5 / 98.5 | 97.6 / 97.0 | 98.6 / 95.9 | 97.1 / 97.9 | 97.8 / 96.9 | 97.8 / 95.7 | 97.1 / 96.8 | 97.5 / 96.3 | 64.4 / 100 | 100 / 2.7 | 78.3 / 5.3 | 98.4 / 85.8 | 89.2 / 97.8 | 93.6 / 91.5 |
| Packing | 100 / 100 | 100 / 100 | 100 / 100 | 99.6 / 64.3 | 98.2 / 90.0 | 98.9 / 75.0 | 100 / 81.8 | 99.3 / 100 | 99.6 / 90.0 | 99.6 / 75.0 | 98.9 / 90.0 | 99.3 / 81.8 | 96.8 / 0 | 100 / 0 | 98.4 / 0 | 100 / 90.9 | 99.6 / 100 | 99.8 / 95.2 |
| Shipping | 96.88 / 96.3 | 98.41 / 92.86 | 94.74 / 94.55 | 98.4 / 97.0 | 98.4 / 97.0 | 98.4 / 97.0 | 99.1 / 96.0 | 97.9 / 98.2 | 98.5 / 97.1 | 99.4 / 94.9 | 97.3 / 98.8 | 98.3 / 96.8 | 98.5 / 97.6 | 98.8 / 97.0 | 98.6 / 97.3 | 99.1 / 96.0 | 97.9 / 98.3 | 98.5 / 97.1 |

Đọc nhanh: mỗi ô là `positive / negative`. Dự án **hơn công bố rõ ở Smell**
(F1 âm 66,67 / 66,67 / 50 -> 87,4 / 93,3 / 90,7) và **ở Price** (0 -> 26,7 / 60,0 / 50,0);
**thua ở Texture / Stayingpower / Packing / Shipping** (công bố chạm 100 ở vài mức).

## 5b. Ba bước kết hợp của đợt 10 (không chạy model mới)

Ba bước này đọc lại các lượt ĐÃ CÓ nên không nằm trong "bảy thử nghiệm được chọn" ở mục 3; chúng trả lời ba
câu hỏi riêng. Mọi số lấy từ `data/reports/fusion/` (luật + đầu vào rút gọn đều có trong repo).

| # | Bước | Số (split `test`, 1.623 dòng) | Kết luận |
| --- | --- | --- | --- |
| F1 | **Router theo khía cạnh, tiêu chí `accuracy`** (chốt trên `val`, 6 ứng viên) | acc 97,66 (`all`) · 97,72 (`paper`) · F1 âm macro 0,795 · 2.741 ô | **KHÔNG đáng kể:** trần chọn-theo-khía-cạnh 97,67, lượt đơn tốt nhất 97,63 ⇒ hơn **+0,04**, dưới cả mức nhiễu (±0,7) |
| F2 | **Router theo khía cạnh, tiêu chí `f1_âm`** | **cùng số như F1** - hai tiêu chí chọn CÙNG một router (`cafebert` 6/7 khía cạnh) | Giữ đủ hai dòng vì tiêu chí chốt TRƯỚC khi xem `test`, nhưng đọc như MỘT kết quả |
| F3 | **Gộp HAI TẦNG** (khung ô từ `phobert-base-v2/lora/exp004`, sắc thái từ 7 lượt một-khía-cạnh) | acc 93,15 (`all`) · 95,87 (`paper`) · F1 âm macro **0,8159** (từ 0,7757) · **`price` F1 âm 0,000 &#8594; 0,357** | **Lần ĐẦU TIÊN `price` âm khác 0**; giá phải trả ~**0,75** điểm accuracy `paper` ⇒ giữ làm hướng phụ, KHÔNG thay bảng chính |
| C1 | **Nhánh `head.aspect_marker`** (`phobert-base-v2/lora/exp006`) | acc 51,60 (`all`) · 74,05 (`paper`) · phát hiện khía cạnh F1 macro 0,891 &#8594; **0,495** | **BỎ khoá này**: cách cài đặt giảm năng lực đầu phân loại (16.149 &#8594; 2.328 tham số) mà không thêm thông tin |

Đọc kèm ba điều: (a) chênh lệch dưới **±0,7** trên đường encoder không kết luận được, nên F1/F2 là "không có
tác dụng", KHÔNG phải "có hại"; (b) F3 là đánh đổi thật nên phải nói CẢ HAI vế (F1 âm +0,040 và accuracy
`paper` −0,75); (c) F1/F2 dùng `test` chỉ để ĐỐI CHIẾU - cả hai luật được chốt trên `val`, và `điểm` của mọi
ứng viên nằm trong tệp luật.

## 6. Trade-off

| Được (nhắm W1-W4) | Mất (so công bố) |
| --- | --- |
| Lớp âm Smell hơn **+21 đến +41** điểm (trên mẫu lớn hơn nhiều: ~43 ô so ~2 ô) | **Texture**: công bố 100 (1/5 ví dụ) vs 96,9-97,4 |
| Lớp âm Price: công bố 0 -> dự án 26,7-60,0 | **Price (accuracy)**: 100 vs 98,5-99,1 |
| **Detection** macro-F1 0,967 (E1) - công bố KHÔNG đo | **Packing/Shipping/Stayingpower** ở các mức công bố đạt 100 |
| acc macro vượt ở 1 ví dụ (97,77 > 97,70), 5 ví dụ (97,19 > 96,74) và encoder (97,88 > 97,70) | acc macro **0 ví dụ** thấp hơn (-0,10); lợi thế biến mất nếu chỉ nhìn thước hai chiều |
| Chứng minh **cơ chế** sửa lớp âm (E3->E4: F1-âm 14,7% -> 77,6%) | Cần tập huấn luyện (encoder giám sát); LLM cần prompt engineering, dao động 92,66-97,77 |
| **Tái lập**: eval_lock khoá tập test + ghim commit; chạy trên GPU 6 GB | Thắng chỉ hiện trên **thước khó** (all-basis + detection + lớp âm mẫu lớn) |

## 7. Nguồn và quy ước

- Số dự án: lấy từ `results/<hash8>/metrics.json` của TỪNG lượt (không lấy từ báo cáo tổng hợp).
- Số công bố: `data/reference_publication/accuracy_by_aspect.csv` (Table 3) và
  `prf_by_aspect_sentiment_{0,1,5}shot.csv` (Tables 4-6).
- Cơ sở đo: `paper` = lọc hai chiều (chỉ ô mà CẢ nhãn đúng và nhãn đoán là positive/negative) -
  đúng cách công bố đếm; `all` = của dự án (không dùng trong báo cáo này, trừ ghi chú).
- Mọi số lấy trên split `test` (1.623 dòng) trừ `exp017` (ghi rõ nếu dùng, ở đây không dùng).
- Cỡ nhiễu của ĐƯỜNG ENCODER đo 05/10/2026 là **±0,33 … ±0,67 điểm** (ba lượt chạy lại với
  `decoding.seed: 7`); lấy làm việc **±0,7** - chênh lệch dưới mức đó không kết luận.
- `cafebert/lora/exp002` (97,88) và `cafebert/lora/exp004` (98,26) là HAI lần rút thăm của **cùng một cấu
  hình** (chỉ khác hạt giống huấn luyện) - đọc như một khoảng **97,88 … 98,26** và là **đỉnh của dự án**.
- Số của ba bước kết hợp (mục 5b): `data/reports/fusion/` - luật router (`aspect_router_accuracy.json`,
  `aspect_router_f1am.json`), số router trên `val`/`test` (`router_aspect_*.json`), bản gộp hai tầng
  (`fuse_aspect_test.json`, `fuse_aspect_test_cafebert.json`), và **đầu vào rút gọn** của mọi lượt tham gia ở
  `inputs/`. Lần chạy router ĐẦU chỉ có 2 ứng viên - luật của lần đó giữ ở các tệp hậu tố `_2model`.

