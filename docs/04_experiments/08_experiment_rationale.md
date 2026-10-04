# 08. Vì sao có từng thí nghiệm

> Đọc file này khi: muốn biết một thí nghiệm hỏi câu gì, khác gì lượt bên cạnh, và kết quả đã ra sao.
> Liên quan: `docs/04_experiments/07_evolution.md` (cây), `docs/06_plan/P7_rerun.md` (đợt chạy), `data/reports/metrics_matrix/` (số)

Mười bảy lượt đang có kết quả thuộc **bốn nhóm theo câu hỏi** - A (hai encoder học LoRA, 4 lượt),
B (Qwen3-4B hỏi bằng prompt, 9 lượt), E (ba biến thể bộ 1 ví dụ, 3 lượt), F (Qwen3-4B hỏi một lượt, 1
lượt); nhóm **G** (Qwen3-0.6B) chưa có kết quả. Mỗi lượt chỉ khác lượt bên cạnh **một biến**; đó là điều
kiện để con số chênh lệch có nghĩa.

## 1. Bối cảnh chung (áp cho MỌI lượt)

| Hạng mục | Giá trị |
| --- | --- |
| Bài toán | ABSA tiếng Việt trên review son mỹ phẩm Shopee; 7 khía cạnh; `label_space: binary` (positive/negative) + "có nhắc tới hay không" là quyết định riêng (`not_mentioned: separate`); neutral bị loại (`neutral_policy: drop`) |
| Đích so | Công bố *Applying Prompt Engineering to Sentiment Analysis of Vietnamese Reviews* (GPT-4o-mini, CoT 0/1/5-shot). `test` của ta chính là tập test của công bố (khớp blob sha) |
| Dữ liệu | `cosmetics-ds0.2.0-pl0.2.0-srccosmetics@0.1.0-e616c1e3` - train 12.268, val 1.535, test 1.623 |
| Cách chấm | `evaluation.n: null` (chấm cả split `test`), `decoding.mode: greedy` (tất định), năm scorer: `accuracy`, `aspect_detection`, `prf`, `aggregate`, `confusion` |
| Hai cơ sở đo | `all` = mọi ô có nhãn đúng khác `neutral` (số trong `metrics.json::scores`) · `paper` = chỉ ô mà CẢ nhãn đúng và nhãn đoán là positive/negative (đúng cách công bố đếm) → **so công bố phải đọc cơ sở `paper`** |
| Mỗi lượt sinh ra | `results/<hash8>/`: `run.log`, `run_meta.json`, `metrics.json`, `metrics.csv`, `mispredictions.csv`, `predictions.csv`, `model/{last,best}` (chỉ hai lượt LoRA) + một run MLflow. `<hash8>` = băm của cấu hình + prompt + dữ liệu + commit đã ghim |
| Bật học? | `training.enabled: false` mặc định - chỉ **bốn** lượt LoRA bật `true` (`phobert-base-v2/lora/exp001` + `exp002`, `visobert/lora/exp001` + `exp002`) |
| Cách sinh | `greedy`, `max_new_tokens` 400, `max_length` 2304 (đường prompt); encoder `max_length` 256 |

## 2. Nhóm A - hai encoder học LoRA (4 lượt, nhóm DUY NHẤT phải huấn luyện)

Vì sao hướng này: Qwen3-4B không fine-tune được trên GPU 6 GB, còn PhoBERT (135M) và ViSoBERT (~108M)
học LoRA vừa máy. Hai encoder chọn để đối chứng **có tách từ** và **không tách từ**. Mỗi encoder có HAI
lượt: `exp001` là lượt học gốc, `exp002` là bản thêm `loss.type: weighted_ce` + `loss.class_weight:
inverse` - đúng MỘT biến so với `exp001`, trả lời câu "dữ liệu mất cân bằng có phải là gốc của việc mất
lớp âm hay không".

| Thí nghiệm | Câu hỏi | Điểm riêng | Kết quả (cơ sở `paper`) | Kết luận |
| --- | --- | --- | --- | --- |
| `phobert-base-v2/lora/exp001` | Encoder tiếng Việt có tách từ, học LoRA thì bằng nào công bố? | Tách từ `vncorenlp` (cần Java + model 27 MB, khai ở `requires_extra`); `max_length` 256; LoRA `query/key/value/dense`; `batch_size` 16 khi suy luận | acc TB khía cạnh **88,40** · F1 sắc thái macro **0,540** · khớp hoàn toàn 85,83% · `stayingpower` **64,71** | GIỮ làm mốc ĐỐI CHỨNG: **không đoán được lớp âm** (F1 âm = 0 ở 5/7 khía cạnh) |
| `phobert-base-v2/lora/exp002` | Dữ liệu mất cân bằng có phải là gốc của việc mất lớp âm không? | Y hệt `exp001`, chỉ thêm `loss.type: weighted_ce` + `loss.class_weight: inverse` | acc TB khía cạnh **96,62** (+8,22 điểm) · F1 sắc thái macro **0,876** (+0,336) · `price` âm vẫn **0,00** (lớp này `val` không có ô nào) · số ô **2.736** | GIỮ - **cứu lớp âm là việc của HÀM MẤT MÁT, không phải của câu chữ** |
| `visobert/lora/exp001` | Encoder đọc nguyên bản, học LoRA thì bằng nào? | `segmenter: none`; `max_length` 256 (cùng ngân sách input với PhoBERT); cùng tham số LoRA | acc TB **94,86** · F1 macro **0,765** · khớp hoàn toàn 92,54% · phát hiện khía cạnh F1 macro **0,966** | GIỮ: nhận ra khía cạnh tốt nhất bảng, nhưng lớp âm yếu (`colour` 0,50 · `price` 0 · `packing` 0) |
| `visobert/lora/exp002` | cùng câu hỏi như `phobert-base-v2/lora/exp002` | Y hệt `visobert/lora/exp001`, chỉ thêm `weighted_ce` + `inverse` | acc TB **95,61** (+0,75 điểm) · F1 macro **0,836** (+0,071) · `price` âm vẫn **0,00** · số ô **2.701** | GIỮ - cùng cơ chế nhưng lợi ít hơn hẳn PhoBERT |

Dùng chung cho cả bốn lượt: `training.yaml` LoRA r16 / alpha32 / dropout 0,05, lr 2e-4, batch 8, epochs 3,
grad_accum 4; chọn `model/best` theo `sentiment_f1` (macro-F1 sắc thái, không dùng accuracy vì dữ liệu
mất cân bằng); `parent: null`; `batch_size` 16 khi suy luận; `% đọc được` = 100 ở cả bốn lượt.

**Hai điều rút ra:** (a) `weighted_ce` nâng F1 lớp âm mạnh nhất ở PhoBERT (`0,540 → 0,876`) - tức hàm mất
mát chính là chỗ sửa được, đúng như ba lượt sửa câu chữ prompt ở §3b thất bại; (b) **đảo thứ hạng**: ở
`exp001`, ViSoBERT hơn PhoBERT **6,46 điểm**; sang `exp002`, PhoBERT (96,62) vượt ViSoBERT (95,61) **1,01
điểm** ⇒ thứ hạng hai encoder phụ thuộc hàm mất mát, không chỉ model.

## 3. Nhóm B - Qwen3-4B hỏi bằng prompt (9 lượt): ba mức ví dụ × ba cấu hình sinh

Ba lượt đầu (`exp002/003/004`) là **ba mức ví dụ của công bố**, NGANG HÀNG nhau (`parent: null`), không
phải bản làm lại của nhau; ba lượt giữa (`exp005/006/007`) là **đối chứng fp16** của đúng ba mức đó; ba
lượt cuối (`exp008/009/010`) là **đối chứng 4-bit ở LÔ 4** - cùng lô với nhóm fp16, nên phép so lượng hoá ở
ba lượt này chỉ còn MỘT biến.

| Thí nghiệm | Câu hỏi | Prompt / cấu hình sinh | Cha | Kết quả (cơ sở `paper`) |
| --- | --- | --- | --- | --- |
| `prompt-cot/exp002` | Đúng mức **COT+0-shot** của công bố | `absa_cot_zeroshot_v1` + system `absa_cot`; 4-bit, lô 8 | null | acc TB **97,16** (công bố 97,36 → **−0,21**) · F1 macro 0,895 · 2.415 ô |
| `prompt-cot/exp003` | **COT+1-shot**: thêm một ví dụ có tăng điểm? | `absa_cot_1shot_v1` + `examples/...1shot`; 4-bit, lô 8 | null | acc TB **97,72** (công bố 97,70 → **+0,02**) · F1 macro **0,926** · 2.315 ô |
| `prompt-cot/exp004` | **COT+5-shot**, mức nặng nhất của công bố | `absa_cot_5shot_v1` + `examples/...5shot`; 4-bit, lô 8 | null | acc TB **97,11** (công bố 96,74 → **+0,38**) · F1 macro 0,902 · 2.378 ô · đọc được 99,88% |
| `prompt-cot/exp005` | Bỏ lượng hoá thì mất bao nhiêu ở mức 0 ví dụ? | y hệt `exp002`, chỉ đổi **fp16 + lô 4** | `exp002` | 96,62 · 0,896 · **2.580 ô** |
| `prompt-cot/exp006` | ... ở mức 1 ví dụ | y hệt `exp003`, chỉ đổi **fp16 + lô 4** | `exp003` | 96,60 · 0,909 · **2.461 ô** |
| `prompt-cot/exp007` | ... ở mức 5 ví dụ (nặng bộ nhớ nhất) | y hệt `exp004`, chỉ đổi **fp16 + lô 4** | `exp004` | 96,48 · 0,899 · **2.520 ô** (lâu nhất 17 lượt: 13.833 giây) |
| `prompt-cot/exp008` | Lượng hoá 4-bit ở CÙNG lô 4 thì sao - mức 0 ví dụ | y hệt `exp002`, chỉ đổi **4-bit + lô 4** | `exp002` | **97,26** · 0,894 · 2.414 ô |
| `prompt-cot/exp009` | ... ở mức 1 ví dụ | y hệt `exp003`, chỉ đổi **4-bit + lô 4** | `exp003` | **97,77** · **0,928** · 2.324 ô - ĐỈNH của 17 lượt (hơn công bố 0,07 điểm) |
| `prompt-cot/exp010` | ... ở mức 5 ví dụ | y hệt `exp004`, chỉ đổi **4-bit + lô 4** | `exp004` | 97,19 · 0,907 · 2.375 ô (chạy TIẾP, dùng lại 1.576 mẫu) |

Đọc nhóm này thế nào:

- **Tái hiện công bố: ĐẠT.** Mức 1 ví dụ và 5 ví dụ nhỉnh hơn công bố; mức 0 ví dụ thấp hơn 0,21 điểm -
  trong khoảng dao động của một lần chạy greedy.
- **Thêm ví dụ không tăng điểm mãi**: 1 ví dụ (97,72) > 0 ví dụ (97,16) > 5 ví dụ (97,11).
- **Lượng hoá sạch MỘT biến (nhóm lô 4)**: 4-bit hơn fp16 **0,64 / 1,17 / 0,71 điểm** ở ba mức, F1 macro
  hơn 0,018 / 0,019 / 0,008. Nhưng 4-bit **trả lời ít hơn 5-6% số ô** (2.414/2.324/2.375 so với
  2.580/2.461/2.520) ⇒ một phần lợi thế là nhờ **kiêng trả lời**; luôn phải đọc kèm số ô.
- Nhóm 4-bit lô 8 (`exp002/003/004`) giữ nguyên là mốc lịch sử, nhưng so với nhóm fp16 lô 4 thì đổi HAI
  biến (lượng hoá và lô) nên chỉ dùng để tham chiếu, **không** dùng để kết luận về lượng hoá.
- `prompt-cot/exp001` (CoT 2 ví dụ - mức nội bộ, không phải mức của công bố) đã bị xoá, nên nhóm này bắt
  đầu từ `exp002`.

## 3b. Nhánh E - ba biến thể bộ 1 ví dụ (3 lượt): CẢ BA ĐỀU ÂM

Ba lượt này đều lấy `prompt-cot/exp003` làm cha (cùng mức 1 ví dụ, cùng 4-bit lô 8) và **mỗi lượt đổi ĐÚNG
MỘT thứ**, để trả lời câu "lớp âm kém là do câu chữ hay do cách học?".

| Thí nghiệm | Đổi đúng một thứ | Kết quả | F1 `price` âm |
| --- | --- | --- | --- |
| `prompt-cot/exp011` | Nội dung VÍ DỤ: bản v2 có nhãn âm ở `texture`, `stayingpower`, `packing` (prompt giống v1 từng byte) | 97,63 (**−0,09**) · F1 macro 0,902 · 2.359 ô | **0,308** (exp003: 0,600) |
| `prompt-cot/exp012` | CÂU CHỮ prompt: thêm bước 0 "tự quét lại toàn bộ review để nhận ra MỌI lời phàn nàn" (ví dụ giữ nguyên) | 96,52 (**−1,20**) · 0,908 · 2.305 ô | 0,600 |
| `prompt-cot/exp013` | CÂU CHỮ prompt: thêm "lưu ý dữ liệu: rất nhiều ô mã 1, đừng lấy mã 1 làm mặc định" | 92,66 (**−5,06**) · 0,842 · **1.972 ô** (mất 343 ô) | **0,167** |

Kết luận: **sửa ví dụ và sửa câu chữ đều KHÔNG cứu được lớp âm**, còn có lượt làm tệ đi (`exp011` kéo F1
`price` âm từ 0,600 xuống 0,308; `exp013` làm model kiêng trả lời nên mất 343 ô). So với đó, sửa **hàm mất
mát** ở hai encoder (`weighted_ce`) nâng F1 lớp âm ở PhoBERT từ 0,540 lên 0,876 - xem §2. Đây là lý do ba
biến thể này **bị bỏ** và hướng tiếp theo của dự án là HỌC, không phải câu chữ.

## 4. Nhóm F - Qwen3-4B hỏi MỘT lượt (1 lượt)

| Thí nghiệm | Câu hỏi | Điểm riêng | Kết quả (cơ sở `paper`) |
| --- | --- | --- | --- |
| `prompt-one-turn/exp001` | Bỏ suy luận từng bước thì 4B được bao nhiêu? | `absa_one_turn_v1` + system `absa_one_turn` (file riêng); 0 ví dụ; `parent: null` | acc TB **95,33** · F1 macro 0,871 · khớp hoàn toàn 93,04% · 289 ô không đọc được |

Đây là **mốc so sánh cho ba mức CoT**: cùng model, cùng tập `test`, cùng 0 ví dụ, khác đúng một thứ -
có bắt viết phần suy luận hay không. Chênh lệch **−1,83 điểm** (95,33 so với 97,16 của `exp002`) là bằng
chứng CoT có tác dụng thật, không chỉ tốn token. Lượt này cũng nhanh nhất (1.081,6 giây so với 5.634,9
giây của `exp002`), vì câu trả lời ngắn.

## 5. Nhóm G - Qwen3-0.6B hỏi bằng prompt (3 lượt chạy lại + 1 lượt DÒ): CHƯA có kết quả

| Thí nghiệm | Câu hỏi | Điểm riêng |
| --- | --- | --- |
| `prompt-cot/exp001` | Mức 0 ví dụ: nhỏ hơn ~7 lần thì kém bao nhiêu? | Đối chiếu với bản 4B `prompt-cot/exp002` |
| `prompt-cot/exp002` | Mức 1 ví dụ | Đối chiếu với `prompt-cot/exp003` |
| `prompt-cot/exp003` | Mức 5 ví dụ | Đối chiếu với `prompt-cot/exp004` |

Đây là biến sạch nhất của dự án: cùng `tokenizer.json` giống từng byte, cùng `max_length` 2304, cùng
prompt, cùng tập `test` - model là thứ duy nhất khác. `quantization: null` (0.6B quá nhỏ, không cần
lượng hoá), `batch_size` 4, `parent: null`.

**Nhóm này đã chạy hai lần và hỏng hai kiểu KHÁC NHAU** (cả sáu thư mục kết quả đã xoá ngày 04/10/2026):

| Kiểu hỏng | Thư mục | Bằng chứng |
| --- | --- | --- |
| Nạp NHẦM trọng số 4B | `exp001/results/8db40559`, `exp002/results/db6efb02`, `exp003/results/30c9e674` | `metrics.json::model` = `Qwen/Qwen3-4B-Instruct-2507`; `% đọc được` ~100; số ô 2.580 / 2.461 / 2.520 trùng khít nhóm fp16 lô 4 (`exp005/006/007`) |
| Đúng 0.6B nhưng **BẬT SUY NGHĨ** | `exp001/results/bc32904d`, `exp002/results/edc0797a`, `exp003/results/d5b8e7fc` | `metrics.json::model` = `Qwen/Qwen3-0.6B`; `% đọc được` chỉ **3,33 / 1,36 / 1,73**; có khối `<think>` 999 / 714 / 788 lượt; lí do hỏng chính là "không thấy JSON nào" (1.549 / 1.561 / 1.536) |

Nguyên nhân kiểu 1: `run_model` chọn model theo thứ tự "tham số truyền vào → `hf_model` của config → hằng
số của module". Khoá `hf_model` **không config nào khai**, nên mọi lượt rơi về hằng số
`Qwen3-4B-Instruct-2507`; `configs/models/qwen3-0.6b.yaml` khai `checkpoint: Qwen/Qwen3-0.6B`, nhưng khoá
đúng đó không được đọc ở nhánh này. Đã sửa ở commit `8bfe96e` (đọc `checkpoint` của config; `hf_model` chỉ
còn là ghi đè).

Nguyên nhân kiểu 2: `Qwen/Qwen3-0.6B` (bản 4/2025) **mặc định bật suy nghĩ**, nên nó tiêu hết trần
`max_new_tokens: 400` trong khối ` thinking` rồi không còn chỗ để in JSON. Đây là lỗi **một cơ chế, hai
khoá đi liền nhau**: bật suy nghĩ thì phải chốt trần token tương ứng.

Xử lý: chạy lại ba lượt với `preprocess.enable_thinking: false` trong cấu hình model (mỗi lượt rơi vào
thư mục kết quả MỚI vì commit và cấu hình nằm trong mã băm danh tính); lượt **bật** suy nghĩ trở thành
nhánh riêng, mở đầu bằng một lượt **DÒ** (`prompt-cot/exp004`, trần 8.192) để đo p50/p95/max số token sinh
rồi mới chốt trần cho lượt chạy đầy đủ.

## 6. Bốn điều phải nhớ khi đọc số

1. **Nói rõ cơ sở đo.** Số so công bố là cơ sở `paper` (`data/reports/metrics_matrix/`, `metrics.csv` với
   `basis=paper`). `data/reports/experiment_registry/` in số cơ sở `all`; hai bảng KHÁC nhau một cách hợp
   lệ - ví dụ `exp002` khớp hoàn toàn 96,12% ở `paper` so với 67,78% ở `all`.
2. **Lượt chạy tiếp (RESUME): đừng đọc `n_samples` như số mẫu đã chấm.** `metrics.json::n_samples` và
   `cost` là của **phiên cuối** (`exp004`: 319 mẫu, 2.533 giây), còn `run_meta.json::run.n_samples` là cả
   split (1.623). Điểm số vẫn đúng trên cả split, vì chấm điểm gộp `predictions/part_*.jsonl` trước khi tính.
3. **Đối chứng lượng hoá nay đã sạch MỘT biến** - nhóm lô 4: `exp008/009/010` (4-bit) so với
   `exp005/006/007` (fp16), cùng prompt, cùng lô ⇒ 4-bit hơn **0,64 / 1,17 / 0,71 điểm** nhưng trả lời ít
   hơn 5-6% số ô (xem §3). Nhóm 4-bit lô 8 (`exp002/003/004`) đổi HAI biến so với nhóm fp16 nên chỉ dùng
   để tham chiếu. Muốn chắc hơn thì so từng dòng `predictions.csv` với đúng lượt cha của nó.
4. **Ô lớp âm quá ít thì đừng kết luận.** Đếm trực tiếp trong `data/processed/cosmetics-ds0.2.0-...`:
   `price` âm có **15 ô ở train, 0 ô ở val, 6 ô ở test**; `packing` âm 85 / 6 / 10; các khía cạnh khác
   48-174 ô ở `test`. Trên tập hai chiều, `price` âm còn **1-6 ô** nên F1 ở đó là nhiễu; bảng của công bố
   ghi `PRICE negative = 0`. Hệ quả kèm theo: **không dò được ngưỡng cho `price` trên `val`** vì `val` có
   0 ô âm.

## 7. Điểm mù `price`: nói cho đúng

`price` là khía cạnh duy nhất mà **mọi lượt** đều có F1 lớp âm rất thấp (PhoBERT và ViSoBERT 0,00; các
lượt prompt 0,167-0,600). Nhưng đọc cho đúng thì đây **không phải bằng chứng "model mù"**: số ô âm của
`price` trong `test` chỉ là **6**, trong `val` là **0** (xem §6.4), nên mọi F1 ở lớp này được tính trên
1-6 ô - lệch một ô là đổi cả con số.

Vì vậy chỉ được nói:
- "Thước `paper` **không đo được** khả năng nhận ra lời chê giá" - đúng và đủ;
- "Muốn cải thiện `price` âm thì phải sửa DỮ LIỆU (thêm ô âm) hoặc phải có thước đo riêng" - đúng;
- "Model X mù `price`" - **không** được nói, vì thước không đủ ô để phân biệt.

Ba lượt tiếp theo về giá (`prompt-cot/exp014` sửa định nghĩa lời chê giá gián tiếp trong prompt,
`prompt-cot/exp015` thêm ví dụ có ô `price` = mã 2, `prompt-cot/exp016` chẩn đoán chỉ hỏi một khía cạnh
`price`) nhằm cải thiện và ĐO riêng khía cạnh này; kết quả của chúng phải báo cáo kèm **cỡ mẫu 6 ô** của
lớp âm, và riêng `exp016` đo trên tập ô khác nên phải báo cáo RIÊNG, không trộn vào bảng `paper`.

## 8. Nguồn số và xem tiếp

Số lấy từ chính lượt chạy ghi ra: `metrics.json` (số chính), `metrics.csv` (bảng dài, có cột `basis`) và
bảng tổng hợp `data/reports/metrics_matrix/` do `python scripts/collect_reports.py` dựng lại từ các file
đó - không có đường tính thứ hai. Phân tích kết quả và hướng phát triển tiếp:
`presentations/result_analysis.md`. Cây phát triển: `07_evolution.md`.
