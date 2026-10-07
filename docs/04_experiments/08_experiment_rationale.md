# 08. Vì sao có từng thí nghiệm

> Đọc file này khi: muốn biết một thí nghiệm hỏi câu gì, khác gì lượt bên cạnh, và kết quả đã ra sao.
> Liên quan: `docs/04_experiments/07_evolution.md` (cây), `docs/06_plan/P7_rerun.md` (đợt chạy), `data/reports/metrics_matrix/` (số)

Mười bảy lượt đang có kết quả thuộc **bốn nhóm theo câu hỏi** - A (hai encoder học LoRA, 4 lượt),
B (Qwen3-4B hỏi bằng prompt, 9 lượt), E (ba biến thể bộ 1 ví dụ, 3 lượt), F (Qwen3-4B hỏi một lượt, 1
lượt). **Cập nhật 06/10/2026:** nhóm **G** (Qwen3-0.6B) NAY ĐÃ có kết quả nhưng **cả ba lượt gốc đều dưới cửa
đọc được**, và **hai nhánh chống lưng đều không cứu được** (một-lượt: đọc được nhưng điểm thấp; bật suy nghĩ:
đọc được nhưng phá phát hiện khía cạnh) - xem §5. Mỗi lượt chỉ khác lượt bên cạnh **một biến**; đó là điều
kiện để con số chênh lệch có nghĩa.

Ngoài 17 lượt đó, **§2b** liệt kê **6 lượt ablation đầu phân loại** (đã chạy trong đợt 7) trả lời câu "đóng băng hay
HỌC đầu phân loại thì khác gì nhau" - mỗi lượt khác lượt gốc của nó **đúng một khoá đo được**
(`head.trainable: true`).

## 1. Bối cảnh chung (áp cho MỌI lượt)

| Hạng mục | Giá trị |
| --- | --- |
| Bài toán | ABSA tiếng Việt trên review son mỹ phẩm Shopee; 7 khía cạnh; `label_space: binary` (positive/negative) + "có nhắc tới hay không" là quyết định riêng (`not_mentioned: separate`); neutral bị loại (`neutral_policy: drop`) |
| Đích so | Công bố *Applying Prompt Engineering to Sentiment Analysis of Vietnamese Reviews* (GPT-4o-mini, CoT 0/1/5-shot). `test` của ta chính là tập test của công bố (khớp blob sha) |
| Dữ liệu | `cosmetics-ds0.2.0-pl0.2.0-srccosmetics@0.1.0-e616c1e3` - train 12.268, val 1.535, test 1.623 |
| Cách chấm | `evaluation.n: null` (chấm cả split `test`), `decoding.mode: greedy` (tất định), năm scorer: `accuracy`, `aspect_detection`, `prf`, `aggregate`, `confusion` |
| Hai cơ sở đo | `all` = mọi ô có nhãn đúng khác `neutral` (số trong `metrics.json::scores`) · `paper` = chỉ ô mà CẢ nhãn đúng và nhãn đoán là positive/negative (đúng cách công bố đếm) → **so công bố phải đọc cơ sở `paper`** |
| Mỗi lượt sinh ra | `results/<hash8>/`: `run.log`, `run_meta.json`, `metrics.json`, `metrics.csv`, `mispredictions.csv`, `predictions.csv`, `model/{last,best}` (chỉ lượt encoder LoRA) + một run MLflow. `<hash8>` = băm của cấu hình + prompt + dữ liệu + commit đã ghim |
| Bật học? | `enabled: false` mặc định - nay có **21** lượt LoRA bật `true` (đếm theo `experiments/**/config.yaml`): bốn lượt của §2, sáu lượt của §2b, và các lượt về sau (đợt 7/8/10) |
| Đầu phân loại | **ĐÓNG BĂNG** ở mọi lượt dùng mặc định; chỉ lượt khai `head.trainable: true` mới mở đầu ra (nay **7** config, gồm sáu lượt của §2b và lượt `cafebert/lora/exp004` của đợt 10) - một cơ chế học riêng, xem §2b |
| Cách sinh | `greedy`, `max_new_tokens` 400, `max_length` 2304 (đường prompt); encoder `max_length` 256. Nhánh BẬT suy nghĩ của Qwen3-0.6B dùng trần **1985** (đo từ lượt DÒ, §5.2) |

## 2. Nhóm A - hai encoder học LoRA (4 lượt ĐANG có kết quả; nhóm đầu phân loại ở §2b)

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

**Một điều áp cho CẢ bốn lượt, đọc trước khi diễn giải điểm số:** đầu phân loại **KHÔNG học** - `peft`
đóng băng mọi tham số không phải adapter, nên mọi thứ học được đều nằm ở adapter. §2b có bằng chứng đo
được và sáu lượt ablation trả lời câu "đóng băng hay không khác gì nhau".

**Hai điều rút ra:** (a) `weighted_ce` nâng F1 lớp âm mạnh nhất ở PhoBERT (`0,540 → 0,876`) - tức hàm mất
mát chính là chỗ sửa được, đúng như ba lượt sửa câu chữ prompt ở §3b thất bại; (b) **đảo thứ hạng**: ở
`exp001`, ViSoBERT hơn PhoBERT **6,46 điểm**; sang `exp002`, PhoBERT (96,62) vượt ViSoBERT (95,61) **1,01
điểm** ⇒ thứ hạng hai encoder phụ thuộc hàm mất mát, không chỉ model.

## 2b. Nhóm đầu phân loại - sáu lượt ablation (đã đủ 6/6 kết quả)

`peft` đóng băng **mọi** tham số không phải adapter, và đầu phân loại của dự án nằm trong số đó. Nên ở cả
bốn lượt của §2, **đầu phân loại không hề học**: nó là một phép chiếu ngẫu nhiên CỐ ĐỊNH. Bằng chứng ĐO
ĐƯỢC, không phải suy đoán (chi tiết ở `06_lora_encoder.md` mục "Đầu phân loại"):

- `head.pt` giống nhau TỪNG BYTE giữa các checkpoint của cùng một lượt chạy (`checkpoint-1000`,
  `checkpoint-1100`, `best`, `last`) - và giữa hai lượt chạy của cùng một model trên hai bản mã khác nhau;
- `trainable_params` bằng đúng tổng tham số adapter (2.678.784), tức đầu phân loại không nằm trong optimizer.

Sáu lượt dưới đây trả lời câu "ĐÓNG BĂNG hay HỌC đầu phân loại thì khác gì nhau", mỗi lượt khác lượt gốc
của nó **đúng một khoá đo được** (`head.trainable: true`, mặc định là `false`):

| Model | Lượt ĐÓNG BĂNG (cha) | acc TB | F1 macro | F1 âm macro | Lượt HỌC đầu (con) | acc TB | F1 macro | F1 âm macro | Δ acc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `phobert-large` | `lora/exp001` | 96,54 | 0,875 | 0,775 | `lora/exp002` | **97,69** | 0,883 | 0,781 | **+1,15** |
| `xlm-roberta-base` | `lora/exp001` | 95,20 | 0,853 | 0,740 | `lora/exp002` | **96,36** | 0,857 | 0,740 | **+1,16** |
| `phobert-base-v2` | `lora/exp002` | 96,62 | 0,876 | 0,776 | `lora/exp005` | **97,59** | 0,884 | 0,784 | **+0,97** |
| `visobert` | `lora/exp002` | 95,61 | 0,836 | 0,700 | `lora/exp005` | **96,28** | 0,849 | 0,723 | **+0,67** |
| `vibert-base-cased` | `lora/exp001` | 94,99 | 0,828 | 0,692 | `lora/exp002` | 94,84 | 0,822 | 0,679 | −0,15 |
| `cafebert` | `lora/exp001` | **97,67** | **0,886** | 0,788 | `lora/exp002` | **97,88** | **0,917** | **0,847** | **+0,21** |

Số ở cơ sở `paper`; `% đọc được` = 100 và `greedy` ở cả **SÁU** cặp (xem `metrics.md` luật 1). Cặp `cafebert`
đã chạy lại xong ngày 05/10/2026 (`results/93448395`: 2-3 phút, dùng lại checkpoint đã có, KHÔNG huấn luyện
lại) nên bảng nay đủ **6/6**: `lora/exp002` cho **97,88 · 0,917 · 0,847** trên 2.737 ô.

Đọc thế nào:

- **Kiểm DẤU VẾT trước khi so điểm** - không có bước này thì không biết lượt nào đã thật sự học đầu:
  `trainable_params` phải LỚN HƠN lượt gốc đúng bằng số tham số đầu phân loại = `số khía cạnh × (số ẩn ×
  số mã nhãn + số mã nhãn)` = 7 × (768 × 3 + 3) = **16.149** (PhoBERT-large 1.024 ẩn: **21.525**); và
  `head.pt` giữa `best` với `last` phải KHÁC nhau (ở lượt gốc chúng giống hệt nhau). Cả sáu lượt đều ĐẠT
  phép kiểm này. Cơ chế của lượt chạy cũng được ghi vào `run.log` (dòng `[CONFIG] đầu phân loại:`),
  `run_meta.json` và thẻ MLflow.
- **Cho đầu phân loại học KHÔNG tạo ra bước nhảy, nhưng cũng không phá gì.** **5/6** cặp nhỉnh hơn **+0,21 →
  +1,16 điểm** độ chính xác, cùng chiều ở năm họ model khác nhau; cặp còn lại (`vibert-base-cased`) kém
  **0,15 điểm**. Đường lớp âm gần như đứng yên ở năm cặp (+0,008 · +0,013 · +0,006 · 0,000 · −0,013 F1 âm
  macro), riêng `cafebert` nhích **+0,059** (0,788 → 0,847).
- **Chỗ đổi rõ nhất không phải tổng điểm mà là DỊCH CHUYỂN giữa các khía cạnh.** Học đầu làm `packing` rơi
  ở 4/6 cặp - `phobert-base-v2` 0,952→**0,900**, `phobert-large` 0,900→**0,818**, `vibert-base-cased`
  0,533→**0,455**, `xlm-roberta-base` 0,889→**0,706** (ViSoBERT tăng: 0,588→0,667; và `cafebert` cũng TĂNG:
  0,982→**0,993**) - trong khi
  `stayingpower` và `texture` tăng: PhoBERT 0,915→**0,968** và 0,893→**0,936**; XLM-R 0,870→**0,891** và
  0,872→**0,927**. Nói cách khác: đầu phân loại HỌC được thì **bớt dựa vào việc đoán theo tần suất**, nên
  khía cạnh ít ô hơn mất và khía cạnh khó hơn được.
- **Chọn MODEL quan trọng hơn chọn đầu phân loại.** Lượt HỌC-đầu tốt nhất bảng (`cafebert/lora/exp002`,
  97,88 · 0,917) vẫn là **cùng model** với lượt ĐÓNG BĂNG tốt nhất (`cafebert/lora/exp001`, 97,67 · 0,886):
  đổi cơ chế đầu phân loại KHÔNG đưa model nào khác lên đầu bảng. Lượt HỌC-đầu tốt nhất của model khác
  (`phobert-large/lora/exp002`, 97,69 · 0,883) vẫn dưới cả hai lượt CafeBERT. Vì vậy sáu lượt này được giữ
  như **phép đo cơ chế**, KHÔNG phải để thay các lượt cha trong bảng chính: đổi cha là đổi luôn mọi so sánh
  đang có.
- **ĐÃ CÓ thước nhiễu cho encoder (đo 05/10/2026).** Ba lượt chạy lại cha với `decoding.seed: 7`:
  `cafebert/lora/exp003` **98,00** (so 97,67), `cafebert/lora/exp004` **98,26** (so 97,88),
  `vibert-base-cased/lora/exp003` **95,66** (so 94,99) ⇒ **biên nhiễu +-0,33 ... +-0,67**. Hệ quả: **+0,21 -> +1,16**
  (cùng chiều ở 5/6 cặp) là tín hiệu **yếu nhưng nhất quán**, còn **-0,15** của `vibert-base-cased` và **+0,21**
  của "đầu phân loại HỌC" ở CafeBERT **nằm trong nhiễu** (không kết luận được). Kỷ lục hiện tại của dự án là
  **`cafebert/lora/exp004` = 98,26**. Chi tiết bằng chứng: `06_lora_encoder.md`.
- `price` là **điểm mù** ở CẢ HAI nhánh (F1 âm = 0,000 ở mọi lượt) - đúng như §7, đừng đọc cột đó.
- **Nhóm `head.aspect_marker` - cơ chế KHÁC, không vào bảng trên (có kết quả 07/10/2026).** Lượt
  `phobert-base-v2/lora/exp006` (cha `exp002`, khác đúng một khoá `head.aspect_marker: true`) **ÂM RẤT
  MẠNH**: acc TB 93,28 &#8594; **51,60**, cơ sở `paper` 96,62 &#8594; **74,05**, phát hiện khía cạnh F1 macro
  0,891 &#8594; **0,495** (precision macro 0,356; `tp` 2.433 / `fp` 4.426). Đọc từ mã: cách cài đặt cho đầu
  phân loại dùng CHUNG một lớp nên khía cạnh chỉ thêm được một **hằng số riêng**, và năng lực đầu giảm từ
  **16.149** xuống **2.328** tham số ⇒ lượt này **giảm NĂNG LỰC** chứ không thêm thông tin. **Bỏ khoá này**
  (giữ mặc định `false`). Vì đầu phân loại đóng băng, kết quả này CHƯA trả lời được câu hỏi về ý tưởng - lượt
  trả lời là `phobert-base-v2/lora/exp007`. Chi tiết: `06_lora_encoder.md`.

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

## 5. Nhóm G - Qwen3-0.6B hỏi bằng prompt (3 lượt chạy lại + 1 lượt DÒ + 1 lượt một-lượt + 1 lượt bật suy nghĩ)

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

### 5.1. Ba lượt chạy lại: ĐỌC ĐƯỢC, nhưng VẪN DƯỚI CỬA - và KHÔNG phải vì trần token

| Lượt | `% đọc được` | Cửa 95% | p50 / p95 / p99 / max token sinh | mẫu chạm trần 400 | trung bình/trần |
| --- | --- | --- | --- | --- | --- |
| `exp001` (0 ví dụ) | **42,02** | **KHÔNG ĐẠT** | 108 / 276 / 400 / 400 | 24 (1,48%) | 0,36 |
| `exp002` (1 ví dụ) | **21,63** | **KHÔNG ĐẠT** | 176 / 280 / 391 / 400 | 16 (0,99%) | 0,46 |
| `exp003` (5 ví dụ) | **84,41** | **KHÔNG ĐẠT** | 215 / 357 / 400 / 400 | 48 (2,96%) | 0,56 |

Cả ba bị gắn `read_rate.valid = false` kèm lí do, đúng luật của `metrics.md`, nên **điểm của chúng KHÔNG
được dùng để so**. Nhưng nguyên nhân KHÔNG phải trần token - đây là điều phải nói cho đúng:

- `scripts/probe_tokens.py` trả lời theo **luật 3 của `metrics.md`**: số mẫu chạm trần đều **dưới 5%** và
  `trung bình/trần` chỉ **0,36-0,56**, nên cả ba lượt **KHÔNG bị cắt**;
- thứ thiếu là **ĐỊNH DẠNG ĐẦU RA**: model trả lời bằng lời rồi **không in khối JSON cuối** mà bộ đọc cần
  (vẫn cùng lí do "không thấy JSON nào" như hai lần hỏng trước);
- lượt DÒ ngay dưới đây chứng minh điều đó từ phía đối diện: **bật suy nghĩ + trần rộng thì đọc được 98,33%**.

Nói cách khác: 0,6B **không** vấp vì hết chỗ, mà vì phải dồn sức vào định dạng.

### 5.2. Lượt DÒ `prompt-cot/exp004` (bật suy nghĩ, trần 8.192, 60 mẫu) - đã có kết quả

| p50 | p95 | p99 | max | trung bình | `% đọc được` |
| --- | --- | --- | --- | --- | --- |
| 642 | 1.072 | **1.323** | 1.434 | 688 | **98,33** |

⇒ **Trần chốt theo luật 23a: `max_new_tokens = 1985`** = làm tròn lên (1.323 × 1,5); cửa sổ ngữ cảnh của
Qwen3-0.6B là 32.768 vị trí nên trần này hợp lệ. Lượt bật suy nghĩ ĐỌC ĐƯỢC gần hết (98,33%), khác hẳn
trần 400.

Hai điều phải ghi rõ khi đọc: (a) số token sinh của nhánh bật suy nghĩ **gấp khoảng 3-6 lần** nhánh tắt
suy nghĩ (p50 642 so với 108-215) - đó là giá của cơ chế, không phải của model; (b) lượt DÒ chạy ở **mức 1
ví dụ**, nên 1985 là số ĐO ĐƯỢC cho mức đó; hai lượt 0 và 5 ví dụ dùng **cùng trần này** và **chưa có lượt
DÒ riêng** - ghi ra để người đọc không tưởng là đã đo riêng từng mức.

### 5.4. Lượt bật suy nghĩ `prompt-cot/exp005` (1 ví dụ, trần 1.985) - ĐÃ XONG: NHÁNH NÀY BỊ BỎ

| `% đọc được` | acc TB | **detection F1 (cơ sở `all`)** | F1 âm macro | số ô `paper` |
| --- | --- | --- | --- | --- |
| 96,98 (QUA cửa 95%) | 90,92 | **0,479** | 0,356 | 1.638 |

Bật suy nghĩ giúp **đọc được** (96,98%) nhưng **phá PHÁT HIỆN khía cạnh**: detection F1 tụt còn **0,479**, so
với **0,86-0,91** của nhánh TẮT suy nghĩ cùng model; `stayingpower` acc chỉ 70,09. Kết luận: **BỎ nhánh 0.6B
bật suy nghĩ**; `exp006` (0 ví dụ) và `exp007` (5 ví dụ) **HUỶ - KHÔNG chạy** (chốt 06/10/2026) vì cùng cơ chế
ở mức ví dụ khác và cơ chế đã biết không cứu được.

**Tổng kết nhóm G (0.6B) - chốt:** ba lượt gốc **dưới cửa đọc được** (21,63-84,41%); lượt một-lượt **đọc được
99,94% nhưng điểm thấp** (F1 âm macro 0,211; chỉ 877 ô); lượt bật suy nghĩ **đọc được 96,98% nhưng phá
detection** (0,479) ⇒ **0.6B không dùng được cho nhiệm vụ này ở cả ba cách hỏi**.

### 5.3. Lượt `prompt-one-turn/exp001` (0,6B, bỏ suy luận, chỉ trả JSON) - ĐÃ XONG 05/10/2026

| `% đọc được` | acc TB | F1 macro | F1 âm macro | số ô `paper` | mẫu thiếu khía cạnh |
| --- | --- | --- | --- | --- | --- |
| **99,94** | 87,04 | 0,610 | 0,211 | **877** | 283 |

Đây là lượt **trả lời dứt điểm câu hỏi của §5.1**: ba lượt 0,6B hỏng vì **ĐỊNH DẠNG ĐẦU RA**, KHÔNG phải vì
trần token. Cùng model, cùng tập `test`, cùng trần `max_new_tokens: 400` như ba lượt hỏng, chỉ đổi **cách
hỏi** (một lượt, bỏ suy luận, bắt trả JSON ngay), và `% đọc được` nhảy từ 21,63-84,41% lên **99,94%** ⇒
**vượt cửa 95%**.

Đọc kèm hai điều: (a) `% đọc được` cao **KHÔNG** có nghĩa là điểm cao - "số ô `paper`" chỉ **877** (các lượt
4B: 2.315-2.580) và F1 âm macro chỉ **0,211**, tức nó cũng **kiêng trả lời** giống 0,5B ở §5b, chỉ khác là
không hỏng định dạng; (b) lượt này trả lời được **cơ chế hỏng**, không phải để lấy điểm - nó vẫn là model
0,6B, đừng đem so thẳng với các lượt 4B.

## 5b. Mốc "model nhỏ họ KHÁC" - Qwen2.5-0.5B (3 lượt, dùng lại đúng ba mức ví dụ của công bố)

Ba lượt `qwen2.5-0.5b-instruct/prompt-cot/exp001`/`exp002`/`exp003` (0 / 1 / 5 ví dụ, `parent: null`) trả
lời câu "kết luận *nhỏ thì kém* có lặp lại ở họ model khác không". Số ở cơ sở `paper`, `test`, `greedy`:

| Lượt | Mức ví dụ | `% đọc được` | acc TB | F1 macro | F1 âm macro | số ô `paper` | mẫu toàn mã 0 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `exp001` | 0 ví dụ | 95,81 | 32,79 | 0,299 | 0,257 | **464** | **73,4%** (1.192/1.623) |
| `exp002` | 1 ví dụ | 97,29 | 83,61 | 0,478 | 0,056 | **256** | **82,1%** (1.332/1.623) |
| `exp003` | 5 ví dụ | 100,0 | 95,12 | 0,681 | **0,000** | **239** | **78,6%** (1.276/1.623) |

**Kết luận "nhỏ thì kém" ĐÚNG, nhưng cơ chế hỏng KHÁC hẳn 0,6B - và đây là chỗ dễ đọc sai nhất của cả
báo cáo:**

- ba lượt này **VƯỢT cửa 95%** (`% đọc được` 95,81 / 97,29 / 100,0), tức định dạng thì ổn - khác 0,6B,
  vốn đọc không nổi 42,02-84,41% vì không in khối JSON;
- thứ 0,5B làm là **KIÊNG TRẢ LỜI**: 73,4-82,1% số review bị nó gán mã 0 (**"không nhắc tới"**) cho MỌI
  khía cạnh, trong khi chỉ 1.311/1.623 review là thật sự không có nhãn nào (`test` có 1.311 review mà mọi
  khía cạnh đều "không nhắc tới"). Hệ quả: **số ô `paper` tụt xuống 239-464** (các lượt 4B: 2.315-2.580),
  nên **F1** được tính trên một phần rất nhỏ của tập - và F1 lớp âm macro sụp về **0,000** ở mức 5 ví dụ.
- vì vậy **điểm `paper` của 0,5B KHÔNG so được với các lượt khác**: "acc TB 95,12" ở `exp003` là độ chính
  xác trên **239 ô** mà model chịu nói, không phải trên cả tập. Muốn so thì phải đọc kèm **số ô** (luật 1
  của `metrics.md`) - đây là ví dụ rõ nhất của cả dự án cho luật đó.
- cơ chế "kiêng trả lời" này cũng có mặt ở 0,6B (`exp003`: 59,2% review toàn mã 0) nhưng **nhẹ hơn**; còn
  0,6B cộng thêm lỗi định dạng. Hai model nhỏ hỏng theo hai kiểu khác nhau - cùng một kết luận "kém",
  hai nguyên nhân khác nhau, và cách sửa cũng khác nhau.

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

Ba lượt tiếp theo về giá nhằm cải thiện và ĐO riêng khía cạnh này. **Cả ba đều KHÔNG cải thiện được `price`
âm** (số ở cơ sở `paper`, cùng `test`, cùng `greedy`; cột "gán mã 2" là số ô model gán nhãn âm cho `price`):

| Lượt | Đổi đúng một thứ | acc TB | F1 macro | số ô | `price` âm: bắt được / 6 ô | gán mã 2 | F1 `price` âm |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `exp003` (**cha**, 1 ví dụ) | - | 97,72 | 0,926 | 2.315 | 3 / 6 | 7 | **0,600** |
| `exp014` | Câu chữ prompt: định nghĩa lời chê giá gián tiếp | 97,01 (**−0,71**) | 0,906 | 2.228 | 4 / 6 | **22** | **0,320** |
| `exp015` | Ví dụ dạy CÓ ô `price` mã 2 | 97,39 (**−0,33**) | 0,915 | 2.436 | 3 / 6 | 10 | 0,500 |
| `exp016` | Chẩn đoán: chỉ hỏi ĐÚNG một khía cạnh | *đo trên tập ô khác (295 ô)* | 0,690 | 295 | 4 / 6 | 18 | 0,400 |

Đọc cho đúng:

- **Bắt thêm một ô đổi lấy cả chục báo động giả.** `exp014` bắt được 4/6 ô âm (hơn cha 1 ô) nhưng gán mã 2
  cho **22** ô (cha: 7) ⇒ F1 **rơi** 0,600 → 0,320. `exp015` giữ 3/6 và gán mã 2 cho 10 ô ⇒ 0,500. Đây
  đúng là hình dạng vấn đề ở §6.4: trên **6 ô** thì mỗi ô là ~0,17 F1, còn báo động giả thì nhiều vô kể.
- **HAI ô không lượt nào bắt được.** Sáu ô `price` âm của `test` là cùng sáu review ở MỌI lượt
  (chỉ số 52, 154, 250, 693, 1283, 1417). Chỉ số **154** và **693** không lượt nào (kể cả `exp003`,
  `exp009` đỉnh 17 lượt, `exp004`, `exp014`, `exp015`, `exp016`) gán mã âm - đó là dữ liệu để người đọc
  sau viết lại định nghĩa ô âm nếu muốn đi tiếp hướng này.
- `exp016` đo trên **tập ô khác** (295 ô, chỉ khía cạnh `price`) nên **phải báo cáo RIÊNG**, không trộn vào
  bảng `paper`; nó trả lời câu "khi chỉ phải để ý MỘT khía cạnh thì bắt được mấy ô": 4/6 - tức kể cả khi
  không phải chia sự chú ý cho 7 khía cạnh, model vẫn bỏ sót 2 ô.
- **Hạn chế đã biết của bộ ví dụ `v6` (ghi 06/10/2026).** `python run_check_examples.py --hash e616c1e3`
  báo `absa_cot_1shot_v6` **rò rỉ**: cụm 6 từ `chất son mịn lên màu chuẩn` trùng với **1 review `test`**
  (và **5 review `train`**; `val` **0**). Đọc cho đúng: cụm đó nằm ở **câu KHEN** (`texture`/`colour`
  dương), **không** nằm ở câu chê giá - mà câu chê giá mới là biến của `v6` - nên **kết luận của bảng trên
  về `price` KHÔNG đổi** (0,500 · 3/6 ô · 10 báo động giả). Cụm này còn xuất hiện **5 lần trong `train`**,
  tức là câu khen thông thường của ngành son, không phải câu riêng của review nào. **`v6` KHÔNG được sửa
  tại chỗ** (luật 1.4): `exp015` đã ghi `examples_sha 7f766223` vào `run_meta.json` + `metrics.json`, và
  file ví dụ là một phần của `config_sha256` (luật 13) - sửa là số đã chạy không tái lập được. Bản sạch
  thay thế là **`absa_cot_1shot_v7`** (prompt byte-identical v1, câu khen viết lại, giữ nguyên câu chê giá):
  công cụ kết luận **"không rò rỉ"**, còn 1 cụm 4 từ dưới ngưỡng 6 - như MỌI ví dụ khác của thư viện
  (`v1/v2/v3/v4/v5/5shot` đều có cụm 3-4 từ). **`v7` chưa được chạy** nên chưa có số.
  Hệ quả: `run_check_examples.py` ở chế độ **quét cả thư viện** vẫn **đỏ đúng 1 mục** (`v6`) và điều đó là
  CỐ Ý - CI không chạy công cụ này (xem `docs/00_workflow/03_ci.md`), nên `ci_checks` + `unittest` vẫn xanh.
- **Lượt `val` phía LLM `exp017`** cho biết trạng thái của `val` (điều kiện chốt luật lai): `val` có
  **0 ô `price` âm** (đúng như §6.4) nhưng model vẫn gán mã 2 cho **6 ô** - tức 6 báo động giả. Vì vậy tệp
  luật ghi `price: null` kèm lí do và ô `price` giữ nguyên `argmax` của model (`09_fusion.md`).
- **Bản gộp HAI TẦNG là thứ ĐẦU TIÊN làm `price` âm khác 0 (07/10/2026).** Lấy KHUNG Ô từ lượt encoder
  (`phobert-base-v2/lora/exp004`) và sắc thái `price` từ lượt một-khía-cạnh
  (`qwen3-4b-instruct-2507/prompt-aspect/exp001`, prompt `absa_aspect_price_v1`): `price` F1 âm
  **0,000 &#8594; 0,357** (2 trong 6 ô), F1 âm macro `paper` 0,7757 &#8594; **0,8159** (+0,040); giá phải trả là
  acc TB (`paper`) 96,62 &#8594; 95,87 và acc TB (`all`) 93,28 &#8594; 93,15. Con số 0,357 vẫn được tính trên
  **6 ô**, nên đọc đúng như trên: nó chứng minh "**có đường chạm tới lớp âm của `price`**", KHÔNG chứng minh
  model đã giỏi `price`. Luật đã đóng băng TRƯỚC khi chạy (`fusion.TWO_TIER_LAW`) và chứng cứ nằm ở
  `data/reports/fusion/fuse_aspect_test.json` - chi tiết ở `09_fusion.md` §3.6.

## 8. Nguồn số và xem tiếp

Số lấy từ chính lượt chạy ghi ra: `metrics.json` (số chính), `metrics.csv` (bảng dài, có cột `basis`) và
bảng tổng hợp `data/reports/metrics_matrix/` do `python scripts/collect_reports.py` dựng lại từ các file
đó - không có đường tính thứ hai. Phân tích kết quả và hướng phát triển tiếp:
`presentations/result_analysis.md`. Cây phát triển: `07_evolution.md`.
