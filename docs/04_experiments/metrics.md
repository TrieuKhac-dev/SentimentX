# Chỉ số đánh giá

> Đọc file này khi: viết báo cáo, hoặc kiểm tra cách tính một chỉ số.
> Liên quan: `docs/04_experiments/reference_publication.md`, `src/evaluation/metrics.py`

Metric lấy theo công bố tham chiếu, không tự thêm bớt khi so sánh.
Mọi lượt chạy phải chấm trên **cùng một tập đánh giá**, do thí nghiệm khai ở `data.roles.eval`
(các thí nghiệm hiện tại đều trỏ `eval: test`; `src/experiments/experiment_run.py::split_of` chặn
`eval` trùng `train`). Số dùng để so với công bố ở `data/reports/metrics_matrix/` là số trên split
`test` nguyên bản.

## Hai câu hỏi phải tách rời

1. Model có nhận ra khía cạnh nào được nhắc tới hay không. Đây là bài toán nhị phân.
2. Khi đã nhận ra, model có chọn đúng sắc thái hay không.

Gộp hai câu hỏi làm một sẽ che mất kiểu lỗi thật: model thấy khía cạnh nhưng chọn sai sắc thái,
hoặc bỏ qua khía cạnh nhưng đoán đúng các khía cạnh còn lại.

## Danh sách chỉ số

| Chỉ số                                           | Tên trong `scores`          | Định nghĩa                                                               |
| ------------------------------------------------ | --------------------------- | ------------------------------------------------------------------------ |
| Độ chính xác theo khía cạnh                      | `accuracy`                  | số ô đúng chia cho số ô, tính riêng cho từng khía cạnh                   |
| Chính xác khi có nhắc tới                        | `accuracy`                  | chỉ tính trên các ô mà nhãn đúng khác "không nhắc tới"                   |
| Phát hiện khía cạnh                              | `aspect_detection`          | bài toán nhị phân có nhắc tới hay không: accuracy, precision, recall, F1 |
| Precision, Recall, F1 theo khía cạnh và sắc thái | `prf`                       | tính riêng cho từng cặp khía cạnh và nhãn, ví dụ `price` và `negative`   |
| Trung bình macro và micro                        | `aggregate`                 | gộp theo khía cạnh hoặc gộp theo ô                                       |
| Khớp hoàn toàn                                   | `aggregate`                 | tỉ lệ review đoán đúng cả bảy khía cạnh                                  |
| Ma trận nhầm theo khía cạnh                      | `confusion`                 | bảng đếm nhãn đúng so với nhãn đoán, dùng để vẽ                          |
| Tỉ lệ đọc được                                   | không phải chỉ số chấm điểm | tỉ lệ kết quả đọc được, kèm phân bố lí do lỗi                            |

## Hai cơ sở đo

Mỗi lượt chạy được chấm **hai lần trên cùng một đầu ra model**, và hai con số KHÁC NHAU:

| Cơ sở   | Giữ ô nào                                                    | Mẫu số phụ thuộc | Ghi ở đâu |
| ------- | ------------------------------------------------------------ | ---------------- | --------- |
| `all`   | mọi ô có nhãn đúng khác `neutral` - quy ước của dự án         | chỉ nhãn đúng    | `scores`, `tables`; dòng `basis=all` của `metrics.csv` |
| `paper` | chỉ ô mà **cả** nhãn đúng **và** nhãn đoán là `positive`/`negative` | cả nhãn đoán | `scores_paper`, `tables_paper`, `paper`; dòng `basis=paper` |

- `paper` là cách **công bố** đếm (bài loại `neutral` và `OTHERS` khỏi phần đánh giá chính), nên đây
  là cơ sở dùng để so với cột tham chiếu trong `data/reports/metrics_matrix/`.
- Mẫu số của `paper` **phụ thuộc chất lượng model**: ô model trả lời `neutral` hoặc "không nhắc tới"
  bị loại, nên điểm cao hơn `all` một cách máy móc. Vì thế phải đọc kèm khoá `paper` của
  `metrics.json`:
  - `label_filter` (`positive`, `negative`) và `codes`: bộ lọc viết theo **TÊN nhãn** rồi tra mã qua
    `label_map.json` của phiên bản dữ liệu, nên dataset đổi cách đánh số thì bộ lọc vẫn đúng;
  - `cells`: số ô còn lại;
  - `dropped_not_two_sided`: số ô bị loại vì nhãn đúng hoặc nhãn **đoán** không phải hai cực đó;
  - `dropped_unreadable`: số ô bị loại vì model trả lời không đọc được;
  - hai con số cuối đều có bản theo khía cạnh (`..._by_aspect`).
- `aspect_detection` **không** có trên cơ sở `paper`: mọi ô giữ lại đều "có nhắc tới", nên câu hỏi
  đó không còn gì để đo (bài cũng không có bảng số cho nó). Danh sách chỉ số của cơ sở này khai ở
  `evaluation.scores_paper`; bỏ khoá đó thì suy ra từ `scores` (mọi chỉ số trừ `aspect_detection`).
- Lượt chạy cũ (trước 01/10/2026) chỉ có cơ sở `all`; hai lượt khác cơ sở này bị cột `comparable`
  đánh dấu là không so được (xem bảng dưới).

## Quy ước bắt buộc

- Ô không đọc được tính là **sai**, không được bỏ khỏi mẫu số. Bỏ đi thì tỉ lệ lỗi định dạng
  trở thành cách nâng điểm vô tình.
- Với bài toán nhị phân, lớp dương là "có nhắc tới", tức mã khác 0.
- Khi ở `label_space: binary`, các ô nhãn `neutral` bị loại theo `neutral_policy`;
  số ô bị loại ghi vào `metrics.json`.

## Bộ chấm điểm là registry

`configs/experiments/evaluation.yaml` khai `scores` là danh sách tên. Mỗi tên là một module trong
`src/evaluation/scorers/`:

| Tên                | Module                        | Nội dung                                                            |
| ------------------ | ----------------------------- | ------------------------------------------------------------------- |
| `accuracy`         | `scorers/accuracy.py`         | độ chính xác theo khía cạnh, và độ chính xác khi đã nhắc tới         |
| `aspect_detection` | `scorers/aspect_detection.py` | nhị phân "có nhắc tới hay không": accuracy, precision, recall, F1    |
| `prf`              | `scorers/prf.py`              | precision/recall/F1 cho từng cặp (khía cạnh, sắc thái)               |
| `aggregate`        | `scorers/aggregate.py`        | trung bình macro/micro và tỉ lệ khớp hoàn toàn                       |
| `confusion`        | `scorers/confusion.py`        | ma trận nhầm theo khía cạnh (chỉ vào `metrics.json`, không vào CSV)  |

Thêm một cách chấm mới: viết một module theo hợp đồng ở `scorers/base.py` rồi thêm một dòng vào
`SCORERS`. Tên lạ trong `scores` bị báo lỗi kèm danh sách, không im lặng bỏ qua.

Điểm macro chỉ lấy trung bình trên các đơn vị CÓ dữ liệu để chấm: một khía cạnh không được nhắc
trong tập con đang chấm không bị tính là 0 - tính là 0 thì điểm tụt mà không có lỗi nào cả. Số ô
của từng đơn vị vẫn nằm trong `metrics.csv` nên cách tính này không che mất thông tin.

## File kết quả

| File                 | Nội dung                                                                      |
| -------------------- | ----------------------------------------------------------------------------- |
| `metrics.json`       | toàn metric, kèm `label_space`, `neutral_policy`, số ô bị loại, và CẢ HAI cơ sở đo (`scores` cho `all`, `scores_paper` + `paper` cho `paper`) |
| `metrics.csv`        | bảng dài: `aspect`, `sentiment`, `metric`, `value`, `basis`, để so giữa các thí nghiệm        |
| `mispredictions.csv` | chỉ các dòng đoán sai theo cơ sở `all`, kèm khía cạnh, nhãn đúng, nhãn đoán |
| `mispredictions_paper.csv` | chỉ các dòng đoán sai theo cơ sở `paper`: TẬP CON của tệp trên, nên không bao giờ có nhãn `không nhắc` hay `không đọc được` ở hai cột nhãn. Số dòng theo khía cạnh = `paper.cells` trừ số ô đúng của `scores_paper.accuracy` |
| `plots/`             | biểu đồ của lượt chạy: `plots/accuracy.html`, HTML tự chứa, mở được khi không có mạng; tắt bằng `save.plots: false` |

`metrics.json` gồm: `label_space`, `neutral_policy`, `not_mentioned`, `dropped_neutral` (và
`dropped_neutral_by_aspect`), `n_reviews`, `aspects`, `scores` (mỗi bộ chấm một khối, cơ sở `all`),
`tables` (ma trận nhầm theo khía cạnh), `scores_order_paper`, `scores_paper`, `tables_paper` và
`paper` (cơ sở đo của công bố, xem mục "Hai cơ sở đo"), và thông tin của lần chạy (prompt, model,
cách sinh, chi phí).
Khoá `rescored` xuất hiện khi lượt chạy có **đo THÊM** chỉ số từ `predictions.csv` bằng
`scripts/rescore.py` (không chạy lại model, **không ghi đè** `metrics.json`/`metrics.csv`). Đây là công
cụ **đo thêm** đang dùng; công cụ **chấm lại** cũ (`run_rescore_eval.py`, ghi đè số gốc) đã bỏ
25/09/2026. Phân biệt rõ: *đo thêm* = thêm `metrics_rescored.*`, giữ nguyên số gốc; *chấm lại* (bản cũ)
= thay số gốc - chỉ bản cũ bị bỏ, không phải `scripts/rescore.py`.

Trong `metrics.csv`, giá trị `all` ở cột `aspect` hoặc `sentiment` nghĩa là "gộp mọi giá trị của
cột đó" - ví dụ dòng `all, all, accuracy_macro` là con số tổng hợp. `plots/` do bước sinh báo cáo
vẽ từ `metrics.json` và `predictions.csv`, không phải do phần chấm điểm.

## Bảng tổng hợp

`data/reports/metrics_matrix/accuracy_by_aspect.csv` có dòng là khía cạnh, cột là từng thí nghiệm
và một cột `reference` chứa số của công bố.
`data/reports/metrics_matrix/prf_by_aspect_sentiment.csv` có cùng định dạng với bảng P R F1 của công bố.
Số của **lượt chạy** trong hai bảng này lấy ở **cơ sở đo `paper`** - đúng cách công bố đo, nên cột
`reference` mới có nghĩa; cơ sở `all` vẫn nằm trong `metrics.json`/`metrics.csv` của từng lượt. Trang
HTML của nhóm này cũng in ghi chú đó ở đầu trang (`src/reporting/reports.py::COMPARISON_NOTE`).

### Hai cột nói lượt chạy có DÙNG ĐƯỢC trong bảng so hay không

`experiment_registry` có thêm ba cột, sinh bằng cách hỏi chính git và chính bản ghi của lượt chạy:

| Cột | Nghĩa | Vì sao cần |
| --- | --- | --- |
| `valid` | commit của lượt chạy có nằm trên nhánh đã ghim (`origin/<nhánh>` trong `run_meta.json`) không: `yes` / `no` / `chưa rõ` | lượt chấm bằng commit CHƯA merge vẫn ra số, nhưng không ai tái lập được từ bản code đã công bố |
| `comparable` | cơ sở đo (`data.build`, `label_space`, `neutral_policy`, `not_mentioned`, `split`, bộ chấm, **bộ chấm + nhãn lọc của cơ sở `paper`**) có khớp lượt CHUẨN không - lượt chuẩn là lượt `FINISHED` sớm nhất trong bảng | hai cột cạnh nhau mà khác cơ sở đo thì lệch vì ĐO KHÁC, không phải vì model khác. Lượt cũ chưa có cơ sở `paper` bị đánh dấu `no` khi đứng cạnh lượt mới |
| `invalid_reason` | lý do gộp của cả hai cột trên, rỗng khi cả hai đều `yes` | người đọc biết ngay vì sao, không phải mở `run.log` dò |

`chưa rõ` là giá trị riêng, không gộp vào `no`: máy không có git, thiếu ref, hoặc `run_meta.json` không
ghi commit thì **không kiểm được** - ghi thành "không hợp lệ" là nói dối kiểu khác. Việc gọi git đi qua
`src/workflow/repo.py` và mỗi cặp (commit, nhánh) chỉ hỏi một lần, nên bảng nhiều dòng vẫn chỉ tốn một lệnh.

### Hai bộ bảng, tách rõ: toàn bộ và chỉ lượt thành công

`python scripts/collect_reports.py` sinh năm nhóm, mỗi nhóm ba định dạng (`.csv`, `.html`, `.md`):

| Nhóm | Gồm những lượt nào | Dùng để |
| --- | --- | --- |
| `attempt_registry` | **MỌI lần thử**, kể cả lượt HỎNG, kèm `status`, thời lượng và `reason` (lý do dừng đọc từ `errors.json`) | bản tổng hợp TOÀN BỘ: đã thử gì, hỏng vì sao, tốn bao lâu |
| `metrics_matrix`, `experiment_registry`, `model_input`, `dataset_registry` | mặc định **chỉ lượt `FINISHED`** | đọc số và so với công bố |

Vì sao tách: lượt hỏng không có `metrics.json`, nên mọi ô số của nó đều trống - đưa vào bảng số là làm
nhiễu đúng chỗ dùng để đọc kết quả (đã gặp thật: bảng hiện bốn dòng PhoBERT, ba dòng rỗng). Muốn bảng số
liệt kê cả lượt hỏng thì thêm `--only all`; nhóm `attempt_registry` thì **luôn** liệt kê đủ, không phụ
thuộc cờ này.

## Nguồn số duy nhất (đừng để hai chỗ đo hai kiểu)

Bảng dưới là HỢP ĐỒNG giữa ba nơi: lượt chạy ghi số, `scripts/rescore.py` đo lại, và
`scripts/collect_reports.py` lấy số để dựng bảng so công bố.

| Con số | Nguồn DUY NHẤT | Ai đọc |
| --- | --- | --- |
| Đo của dự án trên `test` (cơ sở `all`) | `metrics.json::scores` + `metrics.csv` (basis=`all`) | HTML lượt chạy, MLflow (không tiền tố) |
| Để SO VỚI CÔNG BỐ (cơ sở `paper`) | `metrics.json::scores_paper` + `metrics.csv` (basis=`paper`) | `metrics_matrix` (cột `reference`), MLflow (tiền tố `paper.`), `mispredictions_paper.csv` |
| **Số TIÊU ĐỀ của một lượt**: `acc_paper_macro` = Acc macro cơ sở `paper` · `neg_f1_big5` = TB F1 lớp âm 5 khía cạnh `n` lớn (`colour` · `shipping` · `smell` · `stayingpower` · `texture`) | `experiment_registry.csv` - tính từ `scores_paper` của lượt | báo cáo, `present_report_*.md`, phép so theo NHÓM (TB nhiều lượt) |
| Số đo THÊM (đo lại) | `metrics_rescored.json` / `metrics_rescored.csv` | `metrics_matrix` (họ cột `(rescored)`) |
| Chọn `model/best`, dừng sớm, vẽ curve (`val`) | `training_history.csv` + khối `training` của `metrics.json` | người đọc, MLflow (chuỗi theo bước); KHÔNG vào `metrics_matrix` |

Hai điều dễ lẫn, nói thẳng:

- **Hai MỤC ĐÍCH khác nhau dùng hai CƠ SỞ ĐO khác nhau.** Chọn `model/best` / dừng sớm dùng `val` với
  cơ sở `all` (`checkpoints.best_metric`, mặc định `sentiment_f1`); SO VỚI CÔNG BỐ dùng `test` với cơ
  sở `paper`. KHÔNG đem số `all` đi so công bố, và KHÔNG đưa chỉ số chọn-best vào `metrics_matrix`.
- **Ma trận nhầm ở artifact, không lên MLflow.** `confusion` nằm trong `metrics.json`
  (khoá `tables.confusion`) và `plots/accuracy.html`; đưa lên MLflow thì `numeric()` làm phẳng thành
  hàng trăm metric rời và mất dạng ma trận.

`scripts/rescore.py` CHỈ THÊM số đo: nó không bao giờ ghi đè `metrics.json`/`metrics.csv` của lượt chạy.


## Luật đo bắt buộc khi đọc số (chốt 04/10/2026, áp cho MỌI lượt)

1. **Luôn đọc kèm SỐ Ô** (`paper.cells`). Bản 4-bit trả lời ít hơn 5-6% số ô so với bản fp16, nên điểm cao
   hơn một phần có thể là nhờ **kiêng trả lời**: số ô tụt mà điểm tăng là dấu hiệu phải kiểm, không phải
   tin ngay.
2. **Cửa `% đọc được` = 95%** (khoá `read_rate_min` ở `configs/experiments/evaluation.yaml`). Lượt có
   `% đọc được` dưới ngưỡng được ghi thêm ba khoá trong khối `read_rate` của `metrics.json`: `ngưỡng`,
   `valid: false` và `reason`, kèm một dòng `KHÔNG ĐẠT CỬA CHẤT LƯỢNG` trong `run.log`. Cửa **KHÔNG xoá
   dữ liệu**, chỉ để con số đó không bị đem đi so. Đây là cách phát hiện sớm lỗi kiểu "model bật suy nghĩ
   ăn hết trần token" (đã gặp: 3,33% và 1,36%). Vì sao 95%: các lượt tốt đều ≥ 99,88%, còn lượt hỏng thì
   dưới 5%. Lưu ý: `scripts/rescore.py` hiện KHÔNG áp cửa này khi chấm lại (khối `read_rate` ở đó không
   có `valid`).
3. **Token sinh chạm trần thì lượt đó là lượt BỊ CẮT.** Nếu số token sinh trung bình **≥ 95%** của
   `decoding.max_new_tokens` thì phải coi kết quả là bị cắt và chạy lại với trần cao hơn; riêng lượt
   **bật suy nghĩ** phải chạy một lượt **DÒ** để chốt trần trước (xem `present_plan.md` mục 9.1).
4. **Ghi rõ CƠ SỞ và KIỂU TRUNG BÌNH**: cơ sở `paper` (để so công bố) hay `all` (đo của dự án), và
   **macro** hay **micro** - hai con số khác nhau, không được trộn trong cùng một ô.
5. **F1 ghi theo TỈ LỆ 0..1** (không ghi phần trăm) trong `metrics.csv` và các bảng; accuracy và
   `% đọc được` ghi theo phần trăm. Ô có **1-6 mẫu** (như `price` âm) là **nhiễu**, phải ghi kèm cỡ mẫu.

**Hai quyết định kèm theo (cùng ngày):**

6. **Biểu quyết (self-consistency) dùng 3 mẫu** cho đợt này (ba `seed`); chỉ mở rộng lên 5 mẫu nếu thấy có
   ích ở đợt sau.
7. **KHÔNG dò ngưỡng cho khía cạnh có 0 ô âm trên `val`** (hiện là `price`): ngưỡng chỉ áp cho **6 khía
   cạnh** còn lại; `price` đọc bằng **số lần model gán mã 2 + danh sách ô âm của `test`** (6 ô).

**Một lưu ý về TÊN KHOÁ (để khỏi thắc mắc về sau, chốt 04/10/2026):** trần token sinh được khai bằng khoá
**`decoding.max_new_tokens`** (nhóm `decoding` đã có sẵn: `mode`, `temperature`, `top_p`). Kế hoạch đợt 7
và một số ghi chú trước đó gọi khoá này là **`generation.max_new_tokens`** - đó là **TÊN CŨ**, không phải
một khoá thứ hai. Chỉ `decoding.max_new_tokens` được `KNOWN_KEYS` nhận và có tác dụng; không khai thì trần
là 400 (`runner.DEFAULT_MAX_NEW_TOKENS`).

## Hai luật THÊM (chốt 11/10/2026, từ hai ca THẬT của đợt 12)

**8. Model 8B trên T4 (4-bit) là QUÁ CHẬM để chạy một split đầy đủ.** Ca thật:
`qwen3-8b/prompt-cot/exp001-003` + `mistral-7b-instruct-v0.3/prompt-cot/exp001-003` = **6 lượt, ~3 ngày
Colab**, và **0 lượt dùng được** (cả 6 `read_rate.valid = false`). Trước khi giao một lượt 8B cho người
chạy, **PHẢI** chạy một **lượt DÒ `n` nhỏ (~60 mẫu)** để đo thời gian thật, hoặc cắt bằng `n` (subset).
Ước lượng cũ trong `handover/README.md` (kiểu "~40-60 phút") đã **SAI một bậc**: số đo thật là **~1 ngày/lượt**.

**9. Model "bật suy nghĩ MẶC ĐỊNH" phải khai `preprocess.enable_thinking: false`**, nếu không nó viết hết
trần token trong khối ` thinking` và **không bao giờ in JSON**. Ca thật: `Qwen/Qwen3-8B` chạm trần **100 %**
(`token sinh TB` = **399,8 / 399,8 / 400,0** với trần 400) ⇒ `% đọc được` = **1,05 / 0,92 / 0,12 %**.
Đã biết thuộc nhóm này: `Qwen/Qwen3-8B`, `meta-llama/Llama-3.1-8B-Instruct` (bản `-Instruct-2507` thì KHÔNG).
Luật 3a (chạy lượt DÒ để chốt trần) áp cho mọi model loại này.

**10. Số của một lượt encoder phải là TRUNG BÌNH của >= 3 hạt giống.** Biên nhiễu thật đã đo ở đợt 12 (10 lượt
seed): **sd = 0,11-0,16 điểm**, có cấu hình **spread tới 0,28**. Hệ quả đo được: `cafebert/lora/exp021` báo
**98,41** nhưng TB của chính nó (3 lượt) là **98,31**; đỉnh báo cáo cũ `exp004` báo **98,26** nhưng TB của họ
đó là **98,06**. ⇒ **KHÔNG lấy 1 lượt làm "kỷ lục"**, và mọi phép so cấp cấu hình phải có **n >= 3**.
Ngưỡng phát hiện đi kèm: hơn **> 0,25** ở **CẢ** Accuracy macro **VÀ** một chỉ số F1 lớp âm có `n`.

**11. Lượt bị NGẮT ở tầng HUẤN LUYỆN rồi chạy tiếp KHÔNG phải một lần rút thăm sạch.** Dấu vết để nhận:
**`training_history.csv` không bắt đầu ở bước 100 / epoch 1** (lượt sạch luôn có điểm đo từ bước 100). Ca thật:
`cafebert/lora/exp049` (cùng cấu hình, cùng `decoding.seed: 13` với `exp048`) chỉ có 10 dòng và bắt đầu ở
**bước 400 / epoch 2** ⇒ `best.step = 766` thay vì 900, và điểm **98,00 thay vì 98,11**. Lưu ý ĐỪNG đọc nhầm
khoá `resume` trong `metrics.json`: khoá đó nói về tầng **SUY LUẬN** (cả hai lượt đều `NEW`), còn resume ở tầng
**huấn luyện** chỉ lộ ra qua `training_history.csv`. ⇒ Lượt như vậy **giữ làm bản ghi** nhưng **loại khỏi nhóm
seed** (hoặc chạy lại sạch nếu cần một lần rút thăm hợp lệ).

> **Cập nhật 12/10/2026:** `cafebert/lora/exp049` (và `exp042`) đã được người dùng **xoá kết quả cũ và chạy lại
> HOÀN TOÀN**; lượt sạch của `exp049` = **98,11** và **TRÙNG KHÍT `exp048` từng khía cạnh** ⇒ đây chính là bằng
> chứng cho **luật 12** dưới đây, và là lý do v0 chỉ còn **3 lượt độc lập**.

## Ba luật THÊM (chốt 12/10/2026, từ chính hai ca của đợt 12 + một ràng buộc so sánh)

**12. `decoding.seed` trên ĐƯỜNG ENCODER chính là HẠT GIỐNG HUẤN LUYỆN, nên hai lượt cùng khoá này là MỘT lần rút
thăm - kể cả khi chúng có CHA khác nhau.** Ca thật: `cafebert/lora/exp048` (←`exp004`) và `exp049` (←`exp002`) chỉ
khác `exp_id`/`parent`/`notes`, cùng `decoding.seed: 13` ⇒ kết quả **trùng khít từng ô** (`colour` 0,909 ·
`packing` 0,900 · `price` 0,000 · `shipping` 0,974 · `smell` 0,909 · `stayingpower` 0,973 · `texture` 0,936) và
trên cơ sở `all` cũng trùng (`accuracy_micro` 97,93 · `f1_macro` 0,859). Hệ quả: **`exp049` KHÔNG phải lượt thứ tư
của họ v0** - họ v0 chỉ có **3 lượt độc lập** (hạt giống 42/7/13), nên `n` của mọi phép so phải đếm theo HẠT GIỐNG
chứ không theo số thư mục. Muốn thêm một lần rút thăm cho họ encoder thì phải đổi `decoding.seed` sang một giá trị
CHƯA DÙNG.

**13. `neg F1 macro (7 khía cạnh)` là THƯỚC ĐO NHIỄU - không được dùng làm "kỷ lục".** Vì nó lấy trung bình đều 7
khía cạnh, hai khía cạnh tí hon chi phối toàn bộ: `price` (5-6 ô `test`) và `packing` (9-10 ô). Ca thật (CÙNG một
cấu hình `lr4e-4, r8`, chỉ khác hạt giống): `neg F1 (7)` = **0,886 · 0,813 · 0,796** (chênh 0,09) trong khi
`neg F1 (5 n lớn)` = **94,640 · 94,860 · 94,260** (chênh 0,006) - riêng `price` cho F1 **0,571 · 0,000 · 0,000**
(1-2 ô đảo chiều). ⇒ Khi nói về lớp âm PHẢI đọc **`neg F1 (5 khía cạnh n lớn)`** (hoặc chỉ số theo `n`/micro), và
phải ghi kèm số ô của khía cạnh nào dưới 10.

**14. Bảng số CHÍNH chỉ nhận lượt giữ nguyên BÀI TOÁN và PHIÊN BẢN DỮ LIỆU của công bố:**
`label_space: binary` · `neutral_policy: drop` · `not_mentioned: separate` · cùng `version_id` (hiện `v0.2.0`).
Lý do (đã kiểm trong mã): `neutral_policy` đổi **NHÃN** (và cả bảng nhãn huấn luyện - `experiment_run.py` L674
`filter_label_map(label_map, label_space, neutral_policy)`) ⇒ đổi **tập/bài toán**; còn `not_mentioned` **không** đổi
nhãn huấn luyện mà chỉ đổi **khung chấm** (`scorers/base.py` L249-250 bỏ mã "không nhắc" khỏi khung hai chiều;
`scorers/prf.py` coi nó là một LỚP) ⇒ cùng model, cùng dự đoán, **hai con số khác nhau**. Cả hai trường hợp đều là
lỗi im lặng nếu đem so với bảng của công bố. Lượt khác bài toán (nếu có) chỉ được nằm ở **phụ lục**, ghi rõ "khác
bài toán", và muốn so thì phải **chấm lại trên khung công bố** rồi ghi kèm CẢ HAI số.

## Luật 15 (chốt 12/10/2026 tối, từ 2 lượt LLM của Đợt 8)

**15. Lượt bị ngắt ở tầng ĐÁNH GIÁ rồi chạy tiếp (đường prompt/LLM) KHÁC lượt bị ngắt ở tầng HUẤN LUYỆN
(luật 11): nó vẫn dùng được, nhưng phải khai số ô tái dùng.** Cơ chế: công cụ ghi `predictions/part_*.jsonl`
theo lô, nên lần chạy sau **tái dùng** phần đã tính và chỉ sinh phần còn thiếu - `metrics.json` ghi
`resume.mode = RESUME`, `reused`, `new` (ca thật: `exp024` tái dùng 652 ô, `exp027` 1.336 ô; cả hai có 2
`attempt`, lượt đầu `INTERRUPTED`).
Ba điều kiện để lượt như vậy được vào bảng số: (a) `status = FINISHED`; (b) `read_rate.valid = true`; (c)
số nằm trong **dải của các lượt anh em** cùng cấu hình. Đủ ba thì dùng, và **ghi số ô tái dùng** khi báo cáo
(với 3 mẫu LLM ở đây: `exp024` 5-ví-dụ và `exp027` seed 3 đều nằm giữa hai lượt chạy sạch về mọi chỉ số).
KHÁC hẳn luật 11: ngắt ở tầng HUẤN LUYỆN làm `model/best` chọn trên lịch sử thiếu ⇒ lượt đó **bỏ**, không
phải khai báo.

**15b (cùng ca, ghi cho người đọc mã):** `fusion.vote` đã **sửa 12/10/2026** - nó gọi `dict(pred)` nên **sập**
khi một lượt có review KHÔNG đọc được (`preds[i]` là `None`, xem `records.to_arrays`). Lượt encoder đọc
được 100 % nên lỗi ẩn từ Đợt 6, tới lượt LLM (đọc được 99,94 %) mới lộ. Luật bỏ phiếu không đổi: ô không đọc
được ở một lượt thì **lượt đó không có phiếu**, và ô không lượt nào đọc được thì giữ `None` - **không được
điền 0**, vì "không đọc được" (tính là SAI) khác "không nhắc tới" (có thể đúng).


## Luật 16 (chốt 14/10/2026, từ 15 lượt của Đợt 13.1)

**16. Thước CHỌN MỐC (`checkpoints.best_metric`) là một SIÊU THAM SỐ đo được, và nó điều khiển thế cân
bằng Precision↔Recall của lớp âm.** Vì vậy mọi kết luận "tăng F1" phải khai kèm **P và R**, không được
khoe F1 mà giấu việc Recall tụt.

Số đo (Đợt 13.1, `test`, cơ sở `paper`, lớp ÂM trên 5 khía cạnh `n` lớn, họ 12 lượt `lr 4e-4` → nhánh
chọn mốc bằng `neg_f1_big5`, n = 3):

| Khía cạnh | P | R | F1 |
|---|---:|---:|---:|
| `colour` | 85,8 → **91,4** | 95,2 → 92,5 | 90,2 → **91,9** |
| `smell` | 86,7 → **90,9** | 96,9 → 94,5 | 91,5 → **92,5** |
| `texture` | 92,8 → **96,7** | 96,8 → 94,3 | 94,7 → **95,5** |
| `stayingpower` | 97,1 → **98,6** | 98,3 → 97,9 | 97,7 → **98,2** |
| `shipping` | 97,2 → 97,3 | 98,2 → 98,0 | 97,7 → 97,7 |

Lớp dương cùng lượt: **R tăng** +0,7…+1,0 ở 4/5 khía cạnh, P phẳng (−0,2…−0,5).

Ba hệ quả bắt buộc:

- **Muốn đổi P/R thì đổi thước chọn mốc**, không cần đụng kiến trúc/dữ liệu: cần Recall thì phải có một
  thước thiên Recall. **NHƯNG (đo 15/10/2026, Đợt 13.2):** đây là **núm CHỈNH P↔R**, **KHÔNG** phải núm nâng
  `Accuracy`/`F1` - xem khối cuối của luật này.
- **Chọn mốc xong thì số trên `test` có yếu tố "được chọn"**: mốc tối ưu trên `val` bằng chính thước đó ⇒
  không được tự khen trên đúng thước mà nó tối ưu, và kết luận phải dựa trên **nhiều seed + ghép cặp**, không
  phải một lượt (luật 10).
- **Hai cơ sở đo của hai tầng KHÁC nhau** (xem "Hai cơ sở đo" ở trên): `val` - chọn mốc, dừng sớm - ở cơ sở
  `all`; cột chuẩn của bảng số ở cơ sở `paper`. Cùng một lượt, `neg F1 (5n)` lệch nhau ~1-3 điểm giữa hai
  cơ sở, nên **không được** lấy số `val` đi so với cột `paper`, phải nói rõ cơ sở mỗi khi trích.

**15/10/2026 - HỆ QUẢ ÂM, đo được ở Đợt 13.2** (15 lượt `exp079`–`exp093`: nâng nhánh chọn mốc lên **n = 9**,
thêm 6 seed cho nhánh đối chứng, và thử một thước thiên Recall). Số trên `test`, cơ sở `paper`, so với họ 12
lượt `lr 4e-4` (**98,283** · **94,377**):

- `best_metric: neg_f1_big5` ở **n = 9**: **98,367 / 94,491** ⇒ **+0,084 / +0,114** (Welch `p = 0,463 / 0,801`).
  Ghép cặp **cùng seed** với nhánh đối chứng (`sentiment_f1`, n = 9): **+0,200 / +0,476**, `p = 0,122 / 0,391`.
  So với **n = 3** của Đợt 13.1 (**+0,240 / +0,783**) thì hiệu ứng **co lại và mất ý nghĩa** khi tăng `n`
  ⇒ kết quả n = 3 là **may mắn rút thăm**. Bằng chứng mạnh nhất: một lượt **đối chứng** dùng thước CHỌN MỐC CŨ
  (`exp090`, `sentiment_f1`) vẫn đạt **98,60 / 95,76** ⇒ các đỉnh mới do **hạt giống**, không do núm.
- Thước thiên Recall (`neg_recall_big5`, n = 3): Recall lớp âm 5 khía cạnh **97,060** ≈ đúng mức họ 12 lượt
  (**97,068**) nhưng `Accuracy` **−0,716** và `neg F1` **−2,390**; `colour` Precision sụp 85,8 → **72,7**.

⇒ **Luật 16 giữ nguyên phần "điều khiển được P↔R", nhưng KHÔNG được dùng để hứa hẹn "tăng F1"**: muốn nâng
`Accuracy`/`F1` thì phải đi đường khác (kiến trúc, dữ liệu, hàm mất mát), không phải thước chọn mốc.

