# 08. Vì sao có từng thí nghiệm

> Đọc file này khi: muốn biết một thí nghiệm hỏi câu gì, khác gì lượt bên cạnh, và kết quả đã ra sao.
> Liên quan: `docs/04_experiments/07_evolution.md` (cây), `docs/06_plan/P7_rerun.md` (đợt chạy), `data/reports/metrics_matrix/` (số)

Chín lượt đang có kết quả chia thành bốn nhóm theo **câu hỏi**, không theo thứ tự chạy. Mỗi lượt chỉ
khác lượt bên cạnh **một biến**; đó là điều kiện để con số chênh lệch có nghĩa.

## 1. Bối cảnh chung (áp cho MỌI lượt)

| Hạng mục | Giá trị |
| --- | --- |
| Bài toán | ABSA tiếng Việt trên review son mỹ phẩm Shopee; 7 khía cạnh; `label_space: binary` (positive/negative) + "có nhắc tới hay không" là quyết định riêng (`not_mentioned: separate`); neutral bị loại (`neutral_policy: drop`) |
| Đích so | Công bố *Applying Prompt Engineering to Sentiment Analysis of Vietnamese Reviews* (GPT-4o-mini, CoT 0/1/5-shot). `test` của ta chính là tập test của công bố (khớp blob sha) |
| Dữ liệu | `cosmetics-ds0.2.0-pl0.2.0-srccosmetics@0.1.0-e616c1e3` - train 12.268, val 1.535, test 1.623 |
| Cách chấm | `evaluation.n: null` (chấm cả split `test`), `decoding.mode: greedy` (tất định), năm scorer: `accuracy`, `aspect_detection`, `prf`, `aggregate`, `confusion` |
| Hai cơ sở đo | `all` = mọi ô có nhãn đúng khác `neutral` (số trong `metrics.json::scores`) · `paper` = chỉ ô mà CẢ nhãn đúng và nhãn đoán là positive/negative (đúng cách công bố đếm) → **so công bố phải đọc cơ sở `paper`** |
| Mỗi lượt sinh ra | `results/<hash8>/`: `run.log`, `run_meta.json`, `metrics.json`, `metrics.csv`, `mispredictions.csv`, `predictions.csv`, `model/{last,best}` (chỉ hai lượt LoRA) + một run MLflow. `<hash8>` = băm của cấu hình + prompt + dữ liệu + commit đã ghim |
| Bật học? | `training.enabled: false` mặc định - chỉ hai lượt LoRA bật `true` |
| Cách sinh | `greedy`, `max_new_tokens` 400, `max_length` 2304 (đường prompt); encoder `max_length` 256 |

## 2. Nhóm A - hai encoder học LoRA (2 lượt, nhóm DUY NHẤT phải huấn luyện)

Vì sao hướng này: Qwen3-4B không fine-tune được trên GPU 6 GB, còn PhoBERT (135M) và ViSoBERT (~108M)
học LoRA vừa máy. Hai encoder chọn để đối chứng **có tách từ** và **không tách từ**.

| Thí nghiệm | Câu hỏi | Điểm riêng | Kết quả (cơ sở `paper`) | Kết luận |
| --- | --- | --- | --- | --- |
| `phobert-base-v2/lora/exp001` | Encoder tiếng Việt có tách từ, học LoRA thì bằng nào công bố? | Tách từ `vncorenlp` (cần Java + model 27 MB, khai ở `requires_extra`); `max_length` 256; LoRA `query/key/value/dense`; `batch_size` 16 khi suy luận | acc TB khía cạnh **88,40** · F1 sắc thái macro **0,540** · khớp hoàn toàn 85,83% · `stayingpower` **64,71** | GIỮ làm mốc ĐỐI CHỨNG: **không đoán được lớp âm** (F1 âm = 0 ở 5/7 khía cạnh) |
| `visobert/lora/exp001` | Encoder đọc nguyên bản, học LoRA thì bằng nào? | `segmenter: none`; `max_length` 256 (cùng ngân sách input với PhoBERT); cùng tham số LoRA | acc TB **94,86** · F1 macro **0,765** · khớp hoàn toàn 92,54% · phát hiện khía cạnh F1 macro **0,966** | GIỮ: nhận ra khía cạnh tốt nhất bảng, nhưng lớp âm yếu (`colour` 0,50 · `price` 0 · `packing` 0) |

Dùng chung cho cả hai: `training.yaml` LoRA r16 / alpha32 / dropout 0,05, lr 2e-4, batch 8, epochs 3,
grad_accum 4; chọn `model/best` theo `sentiment_f1` (macro-F1 sắc thái, không dùng accuracy vì dữ liệu
mất cân bằng); `parent: null` cả hai.

## 3. Nhóm B - Qwen3-4B hỏi bằng prompt (6 lượt): tái hiện công bố + đối chứng lượng hoá

Ba lượt đầu là **ba mức ví dụ của công bố**, NGANG HÀNG nhau (`parent: null`), không phải bản làm lại
của nhau. Ba lượt sau là **đối chứng KHÔNG lượng hoá** của đúng ba mức đó.

| Thí nghiệm | Câu hỏi | Prompt | Cha | Kết quả (cơ sở `paper`) |
| --- | --- | --- | --- | --- |
| `prompt-cot/exp002` | Đúng mức **COT+0-shot** của công bố | `absa_cot_zeroshot_v1` + system `absa_cot` | null | acc TB **97,16** (công bố 97,36 → **−0,21**) · F1 sắc thái macro 0,895 · khớp hoàn toàn 96,12% |
| `prompt-cot/exp003` | **COT+1-shot**: thêm một ví dụ có tăng điểm? | `absa_cot_1shot_v1` + `examples/...1shot` | null | acc TB **97,72** (công bố 97,70 → **+0,02**) · F1 macro **0,926** · khớp hoàn toàn **97,23%** - cao nhất chín lượt |
| `prompt-cot/exp004` | **COT+5-shot**, mức nặng nhất của công bố | `absa_cot_5shot_v1` + `examples/...5shot` | null | acc TB **97,11** (công bố 96,74 → **+0,38**) · F1 macro 0,902 · 63 ô hỏng định dạng |
| `prompt-cot/exp005` | 4-bit mất bao nhiêu điểm ở mức 0 ví dụ? | y hệt `exp002` | `exp002` | 96,62 · 0,896 (thấp hơn bản 4-bit **0,54**) |
| `prompt-cot/exp006` | ... ở mức 1 ví dụ | y hệt `exp003` | `exp003` | 96,60 · 0,909 (thấp hơn **1,12**) |
| `prompt-cot/exp007` | ... ở mức 5 ví dụ (nặng bộ nhớ nhất) | y hệt `exp004` | `exp004` | 96,48 · 0,899 (thấp hơn **0,63**; lâu nhất: 13.833 giây) |

Đọc nhóm này thế nào:

- **Tái hiện công bố: ĐẠT.** Mức 1 ví dụ và 5 ví dụ ngang hoặc nhỉnh hơn công bố; mức 0 ví dụ thấp hơn
  0,21 điểm - trong khoảng dao động của một lần chạy greedy.
- **Thêm ví dụ không tăng điểm mãi**: 1 ví dụ (97,72) > 0 ví dụ (97,16) > 5 ví dụ (97,11). Mức 1 ví dụ
  là cấu hình tốt nhất hiện có.
- **Bản KHÔNG lượng hoá thấp hơn bản 4-bit** ở cả ba mức (0,54 / 1,12 / 0,63 điểm). Nhưng ba lượt này
  buộc phải hạ `batch_size` 8 → 4 (fp16 tốn ~4 lần bộ nhớ), và `batch_size` nằm trong mã băm danh tính,
  nên **chưa tách được** nguyên nhân là lượng hoá hay là batch - xem §6.
- Cấu hình gốc ba lượt 4-bit: `4bit`, `batch_size` 8, `max_length` 2304. `prompt-cot/exp001` (CoT 2 ví
  dụ - mức nội bộ, không phải mức của công bố) đã bị xoá, nên nhóm này bắt đầu từ `exp002`.

## 4. Nhóm C - Qwen3-4B hỏi MỘT lượt (1 lượt)

| Thí nghiệm | Câu hỏi | Điểm riêng | Kết quả (cơ sở `paper`) |
| --- | --- | --- | --- |
| `prompt-one-turn/exp001` | Bỏ suy luận từng bước thì 4B được bao nhiêu? | `absa_one_turn_v1` + system `absa_one_turn` (file riêng); 0 ví dụ; `parent: null` | acc TB **95,33** · F1 macro 0,871 · khớp hoàn toàn 93,04% · 289 ô không đọc được |

Đây là **mốc so sánh cho ba mức CoT**: cùng model, cùng tập `test`, cùng 0 ví dụ, khác đúng một thứ -
có bắt viết phần suy luận hay không. Chênh lệch **−1,83 điểm** (95,33 so với 97,16 của `exp002`) là bằng
chứng CoT có tác dụng thật, không chỉ tốn token. Lượt này cũng nhanh nhất (1.081,6 giây so với 5.634,9
giây của `exp002`), vì câu trả lời ngắn.

## 5. Nhóm D - Qwen3-0.6B hỏi bằng prompt (3 lượt): CHƯA có kết quả

| Thí nghiệm | Câu hỏi | Điểm riêng |
| --- | --- | --- |
| `prompt-cot/exp001` | Mức 0 ví dụ: nhỏ hơn ~7 lần thì kém bao nhiêu? | Đối chiếu với bản 4B `prompt-cot/exp002` |
| `prompt-cot/exp002` | Mức 1 ví dụ | Đối chiếu với `prompt-cot/exp003` |
| `prompt-cot/exp003` | Mức 5 ví dụ | Đối chiếu với `prompt-cot/exp004` |

Đây là biến sạch nhất của dự án: cùng `tokenizer.json` giống từng byte, cùng `max_length` 2304, cùng
prompt, cùng tập `test` - model là thứ duy nhất khác. `quantization: null` (0.6B quá nhỏ, không cần
lượng hoá), `batch_size` 4, `parent: null`.

Ba lượt **đã chạy xong nhưng KHÔNG đo model 0.6B**. Bằng chứng: `metrics.json::model` của cả ba là
`Qwen/Qwen3-4B-Instruct-2507`; hai lượt đầu trùng cả số token sinh (`380.489` = `380.489`; `354.196` =
`354.196`), còn cả ba lượt trùng **mọi chỉ số** tới hai chữ số thập phân, kể cả số ô được giữ; tốc độ sinh
gần bằng nhau (48,7 so với 51,1 token/giây, cùng máy khác phiên). Lượt 5 ví dụ không so được số token vì
`cost` là của phiên cuối (xem §6). Nghĩa là ba lượt đó là **cùng một phép đo với nhóm fp16**, không phải
một model khác.

Nguyên nhân: `run_model` chọn model theo thứ tự "tham số truyền vào → `hf_model` của config → hằng số
của module". Khoá `hf_model` **không config nào khai**, nên mọi lượt rơi về hằng số `Qwen3-4B-Instruct-2507`;
`configs/models/qwen3-0.6b.yaml` khai `checkpoint: Qwen/Qwen3-0.6B`, nhưng khoá đúng đó không được đọc ở
nhánh này.

Xử lý: ba thư mục kết quả đã **xoá** ngày 02/10/2026. Lượt chạy lại sẽ rơi vào thư mục kết quả MỚI (commit
nằm trong mã băm danh tính), nên không trộn với bản cũ. **Kết luận: ĐỔI HƯỚNG - nhóm D là việc kế tiếp**,
sau khi sửa cách chọn checkpoint.

## 6. Bốn điều phải nhớ khi đọc số

1. **Nói rõ cơ sở đo.** Số so công bố là cơ sở `paper` (`data/reports/metrics_matrix/`, `metrics.csv` với
   `basis=paper`). `data/reports/experiment_registry/` in số cơ sở `all`; hai bảng KHÁC nhau một cách hợp
   lệ - ví dụ `exp002` khớp hoàn toàn 96,12% ở `paper` so với 67,78% ở `all`.
2. **Lượt chạy tiếp (RESUME): đừng đọc `n_samples` như số mẫu đã chấm.** `metrics.json::n_samples` và
   `cost` là của **phiên cuối** (`exp004`: 319 mẫu, 2.533 giây), còn `run_meta.json::run.n_samples` là cả
   split (1.623). Điểm số vẫn đúng trên cả split, vì chấm điểm gộp `predictions/part_*.jsonl` trước khi tính.
3. **Nhóm fp16 khác nhóm 4-bit HAI biến** (lượng hoá và `batch_size` 8 → 4), nên các mức lệch 0,54 / 1,12
   / 0,63 điểm chưa nói được gì về riêng lượng hoá. Muốn kết luận thì so từng dòng `predictions.csv` với
   đúng lượt cha của nó.
4. **Ô lớp âm quá ít thì đừng kết luận.** Trên tập hai chiều, `price` âm chỉ còn 2-5 ô và `packing` âm
   9-10 ô (các khía cạnh khác 46-171 ô), nên F1 ở hai khía cạnh đó là nhiễu - bảng của công bố cũng ghi
   `PRICE negative = 0` vì đúng một ô đoán sai.

## 7. Nguồn số và xem tiếp

Số lấy từ chính lượt chạy ghi ra: `metrics.json` (số chính), `metrics.csv` (bảng dài, có cột `basis`) và
bảng tổng hợp `data/reports/metrics_matrix/` do `python scripts/collect_reports.py` dựng lại từ các file
đó - không có đường tính thứ hai. Phân tích kết quả và hướng phát triển tiếp:
`presentations/result_analysis.md`. Cây phát triển: `07_evolution.md`.
