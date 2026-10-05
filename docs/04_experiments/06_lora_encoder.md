# 04.06. Chạy model encoder bằng LoRA

> Đọc file này khi: chạy thí nghiệm PhoBERT hoặc ViSoBERT, hoặc sửa cách huấn luyện.
> Liên quan: `docs/04_experiments/03_training_eval.md`, `docs/05_config/04_models.md`,
> `docs/05_config/05_experiments_shared.md`

## Hai đường chạy, chọn bằng `approach`

`configs/models/<model_id>.yaml` khai `approach`. Giá trị đó quyết định đường chạy, và không có giá
trị mặc định trong code:

| `approach` | Model | Đường chạy | Cần gì |
| --- | --- | --- | --- |
| `prompt` | `qwen3-4b-instruct-2507`, `qwen3-0.6b`, `qwen2.5-0.5b-instruct` | `src/evaluation/runner.py`: gửi prompt rồi đọc câu trả lời | GPU, prompt của thí nghiệm |
| `encoder` | `visobert`, `phobert-base-v2`, `phobert-large`, `vibert-base-cased`, `cafebert`, `xlm-roberta-base` | `src/experiments/encoder_run.py`: huấn luyện LoRA rồi suy luận | GPU, `peft`, ba vai |

Model encoder KHÔNG có prompt để tự trả lời, nên thí nghiệm dùng nó bắt buộc khai `enabled: true`
(khoá ở lớp `configs/experiments/training.yaml`; guard ở `src/experiments/experiments.py::check`).

## Một lượt chạy encoder gồm gì

1. **Đọc dữ liệu ba vai**: `train` để học, `val` để chọn `model/best`, `eval` (split `test`) để chấm.
2. **Chiếu nhãn** sang không gian nhãn của thí nghiệm
   (`src/preprocessing/loader.project_multi_head`): ô neutral bị loại mang `mask = 0` - không vào
   loss và không được chấm, nhưng KHÔNG làm mất các khía cạnh khác của cùng review.
3. **Huấn luyện LoRA**: encoder gốc đóng băng, học adapter hạng thấp, cộng một đầu phân loại riêng cho
   mỗi khía cạnh (`khía cạnh × mã nhãn`). **Đầu phân loại ĐÓNG BĂNG ở mặc định** - `peft` đóng băng mọi
   tham số không phải adapter, nên mặc định chỉ adapter học; `head.trainable: true` mới mở đầu ra (mục
   "Đầu phân loại" bên dưới).
4. **Chọn `model/best` theo `checkpoints.best_metric` trên `val`** (mặc định `sentiment_f1` = macro-F1
   sắc thái), rồi **suy luận trên split `eval`**.
5. **Chấm điểm và ghi kết quả** bằng đúng bộ chấm của đường prompt (`src/evaluation/scorers/`), nên
   hai đường cho ra bảng điểm so được với nhau và với công bố.
6. **Ghi thêm XÁC SUẤT từng ô** ra `probabilities.csv`: một dòng cho mỗi (review, khía cạnh), cột
   `p(mã <mã>)` mang ĐÚNG mã nhãn đã huấn luyện (không phải số thứ tự). Tệp này **chỉ đường encoder có**,
   và phần chấm điểm **không** dùng nó - bước KẾT HỢP mới cần (dò ngưỡng theo khía cạnh, ensemble nhiều
   encoder, luật lai encoder + LLM). Nó **không** nằm trong danh sách "7 tệp nhẹ" gửi kèm mọi lượt: nhóm
   encoder gửi thêm tệp này (ghi rõ ở README của gói bàn giao và `present_plan.md` mục 7.4), và **cũng
   không vào git** - cùng loại với `predictions.csv` (`.gitignore`); bản rút gọn có commit dùng cho bước
   kết hợp là `data/reports/fusion/inputs/`.

## Đầu phân loại: ĐÓNG BĂNG (mặc định) hay HỌC (`head.trainable`)

`peft` đóng băng **mọi** tham số không phải adapter, và đầu phân loại của dự án nằm trong số đó. Hệ quả
là ở chế độ mặc định đầu phân loại chỉ là một phép chiếu NGẪU NHIÊN CỐ ĐỊNH: nó được khởi tạo rồi đứng
yên, mọi thứ học được đều nằm ở adapter. Đó là **hiện trạng đã đo**, không phải phỏng đoán:

- `head.pt` của bốn lượt LoRA đầu tiên (`phobert-base-v2/lora/exp001`, `exp002`, `visobert/lora/exp001`,
  `exp002`) giống nhau **TỪNG BYTE** giữa các checkpoint của cùng một lượt chạy (`checkpoint-1000`,
  `checkpoint-1100`, `best`, `last`) - đó là điều cần đo: đầu phân loại không đổi suốt lượt chạy. Giữa các
  MODEL thì đọc theo từng cặp, không suy từ một con số chung: `phobert-base-v2/lora/` và `visobert/lora/`
  (mọi lượt `exp001`-`exp004`) cùng ra `9679E0F37C5B`; `vibert-base-cased/lora/exp001` và
  `xlm-roberta-base/lora/exp001` cùng ra `31BFB2E2D82E`; `cafebert/lora/exp001` ra `06586C994F70`; còn
  `phobert-large/lora/exp001` ra `6AC8C9ED7BB0`. **Giá trị cụ thể là của model đó**; điều lặp lại được ở MỌI
  lượt đóng băng là đầu phân loại KHÔNG đổi - kể cả giữa hai lượt chạy của cùng một model trên hai bản mã
  khác nhau (bản `8bfe96e0` và bản đã sửa lỗi `59579e57`: `vibert-base-cased/lora/exp001` ở `a525cefe` và
  `ba615bcb`, `xlm-roberta-base/lora/exp001` ở `491e81cb` và `a2f22f02` - bốn thư mục, cùng một hash);
- lượt bật `head.trainable: true` thì `head.pt` KHÁC hẳn VÀ còn khác nhau giữa các checkpoint (ví dụ
  `phobert-base-v2/lora/exp005`: `03900CDA196A` ở `checkpoint-1000`, `BA6E1553699A` ở `best`,
  `4EDC06D56D50` ở `last`) - tức đầu phân loại CÓ học;
- `trainable_params` trong `metrics.json` bằng **đúng** tổng tham số adapter (2.678.784), tức đầu phân
  loại không nằm trong optimizer.

Vì sao vẫn để mặc định là đóng băng: đổi nó là đổi **CƠ CHẾ HỌC**, không phải sửa lỗi - bốn lượt đã
chạy vẫn hợp lệ và đang là mốc so sánh của dự án.

| Khoá | Ở đâu | Nghĩa |
| --- | --- | --- |
| `head.trainable: false` | `configs/experiments/training.yaml` (mặc định, mọi thí nghiệm thừa hưởng) | chỉ adapter học - đúng cơ chế của bốn lượt đã chạy |
| `head.trainable: true` | khai ở config CỦA THÍ NGHIỆM để đè lớp dùng chung | đầu phân loại học cùng adapter, dùng CHUNG `lr` (cố ý **không** có `lr` riêng: một biến mỗi thí nghiệm) |

Sáu lượt ablation trả lời câu hỏi "đóng băng hay không khác gì nhau": `phobert-base-v2/lora/exp005`,
`visobert/lora/exp005`, `cafebert/lora/exp002`, `phobert-large/lora/exp002`,
`vibert-base-cased/lora/exp002`, `xlm-roberta-base/lora/exp002` - mỗi lượt khác lượt gốc của nó **đúng
một khoá đo được** (`head.trainable`); xem `08_experiment_rationale.md`.

**Dấu vết để kiểm một lượt có thật sự học đầu hay không** (đọc TRƯỚC khi so điểm): `trainable_params`
phải lớn hơn lượt đóng băng đúng bằng số tham số đầu phân loại = `số khía cạnh × (số ẩn × số mã nhãn +
số mã nhãn)` = 7 × (768 × 3 + 3) = **16.149** (PhoBERT-large 1.024 ẩn: **21.525**); và `head.pt` giữa
`best` với `last` phải KHÁC nhau. Cơ chế của lượt chạy được ghi vào `run.log` (dòng
`[CONFIG] đầu phân loại:`), `run_meta.json` (khối `run.training.head_trainable`) và thẻ MLflow
(`info.training.head_trainable`) - nhìn bảng điểm thì KHÔNG thể phân biệt hai cơ chế.

**Hai đường phải cùng bật/tắt.** Lượt MỚI: `get_peft_model` đóng băng hết rồi `set_head_trainable` mở
lại đầu. Lượt CHẠY TIẾP: `PeftModel.from_pretrained(is_trainable=True)` chỉ mở **adapter** - đầu phân
loại VẪN đóng băng (đo được), nên phải gọi `set_head_trainable` thêm một lần. Quên vế thứ hai thì lượt
chạy mới và lượt chạy tiếp là hai cơ chế khác nhau mà không có dấu hiệu nào trong kết quả.

## Checkpoint

| Thư mục | Trong đó có gì | Dùng để |
| --- | --- | --- |
| `model/last` | adapter + `head.pt` + `optimizer.pt` + `scheduler.pt` + `trainer_state.json` | chạy tiếp sau khi bị ngắt |
| `model/best` | adapter + `head.pt` + `head_config.json` | suy luận, chấm điểm |
| `model/checkpoint-<bước>` | như `model/last`, giữ `keep_last_k` cái gần nhất | ảnh chụp trung gian để chạy tiếp |

Phần này KHÔNG nằm trong trainer: chính sách lưu + `Store` ở `src/training/checkpoints.py`, còn CÁCH
GHI trọng số ở writer `src/training/savers/adapter.py` - nhờ vậy một cách huấn luyện khác (full
fine-tune) dùng lại đúng chính sách đó mà chỉ cần thêm writer của nó.
`trainer_state.json` giữ vân tay ba giá trị (`config_sha256`, mã phiên bản dữ liệu, commit đã ghim).
Chạy tiếp chỉ hợp lệ khi cả ba y nguyên; khác thì báo lỗi và yêu cầu xoá thư mục kết quả, vì trộn
hai phép đo vào cùng một bảng là lỗi không nhìn thấy được.

Một chi tiết của đường này: văn bản được mã hoá theo TỪNG LÔ (để không dựng cả tập train trong bộ
nhớ), rồi các lô được nối lại - nên `lora.encode` pad mọi lô về **cùng một độ rộng**. Không pad như
vậy thì `torch.cat` ném `RuntimeError: Sizes of tensors must match except in dimension 0` ngay khi
tập train có nhiều lô (đã gặp thật với ~4.000 review; phép chạy thử ở máy chỉ có 40 review nên chỉ
một lô và không lộ ra).

**`model/best` được cập nhật ở HAI chỗ**, không phải một: bước lưu theo chu kỳ (`every_n_steps` - có in
`đã lưu model/best`), và **cuối mỗi epoch** (cũng có in từ nay). Muốn biết bản đang được chấm là bước
nào thì đọc `model/best/trainer_state.json` (trường `best.step`): lượt PhoBERT 26/09/2026 có `model/best`
ở bước **1153** trong khi console chỉ in ở bước 1100.

**Hai `checkpoint-*` trong `model/` là bình thường**, không phải rác: `checkpoints.keep_last_k: 2` cộng
`delete_intermediate: true` giữ lại đúng hai ảnh chụp gần nhất để chạy tiếp. Với `every_n_steps: 100` và
1.153 bước thì `model/` gồm `best`, `last`, `checkpoint-1000`, `checkpoint-1100`; ảnh chụp cũ bị xoá
ngay sau mỗi lần lưu.

## Chọn `model/best`, dừng sớm, và curve train/val

- **Chọn best theo `checkpoints.best_metric`** (mặc định `sentiment_f1` = macro-F1 sắc thái). Vì sao
  KHÔNG dùng accuracy: dữ liệu mất cân bằng (ở `train`: `price` **2.581 dương / 15 âm / 21 trung tính**;
  `stayingpower` 1.232 / 753 / 246) nên accuracy bị lớp trội chi phối. Đổi chỉ số chỉ cần sửa config,
  không sửa code.
  - **Cảnh báo đo được**: `val` có **0 ô** `price` âm (train 15, test 6) nên **không thể dò ngưỡng cho
    `price`** trên `val`; xem `08_experiment_rationale.md` §7.
- **`val` đo bằng ĐÚNG engine của `test`** (`src/evaluation/scorers`), nên `val` có đủ
  `sentiment_precision/recall/f1`, `detection_f1`, `accuracy_cell`, `loss` - không có định nghĩa metric
  thứ hai. Nhờ vậy đổi hàm chấm điểm là đổi cho cả `val` lẫn `test`.
- **Dừng sớm** (`early_stop.enabled: true`): khi chỉ số best không tăng quá `min_delta` trong `patience`
  lần đo liên tiếp thì dừng, ghi `dừng sớm ...` vào `run.log`.
- **Lịch sử huấn luyện** ghi ra `training_history.csv` (một điểm đo mỗi dòng: `kind=step` hoặc
  `kind=epoch`, kèm loss train/val và P/R/F1), và biểu đồ cho người đọc ghi ra `plots/training.html`
  (plotly + jinja2). Tắt biểu đồ bằng `save.plots: false`. Vẽ biểu đồ là **best-effort**: thiếu
  `plotly`/`jinja2` thì chỉ MẤT BIỂU ĐỒ - `training_history.csv` vẫn có và lượt chạy vẫn xong (ô
  bootstrap của notebook tự cài hai gói này; xem `docs/00_workflow/06_conventions.md` mục "Import").
- **Chuỗi theo bước lên MLflow**: mỗi điểm val được gửi kèm `step`, nên MLflow tự vẽ curve - phiên bị
  ngắt giữa chừng vẫn còn phần đã chạy.
- **Hàm mất mát** (`loss.type`): `ce` mặc định, `weighted_ce` + `loss.class_weight: inverse` khi muốn
  chống mất cân bằng. Đổi loss đổi `config_sha256` nên ra thư mục kết quả MỚI.

### Kết quả hai hàm mất mát (số đo thật, bốn lượt LoRA)

| Lượt | Model | acc TB khía cạnh | F1 sắc thái macro | F1 âm `colour` | F1 âm `packing` | F1 âm `stayingpower` | phát hiện khía cạnh (F1 macro) | số ô |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `phobert-base-v2/lora/exp001` | PhoBERT + `ce` | 88,40 | 0,540 | 0,000 | 0,000 | 0,053 | **0,957** | 2.665 |
| `phobert-base-v2/lora/exp002` | PhoBERT + `weighted_ce` | **96,62** | **0,876** | 0,812 | 0,952 | 0,915 | 0,891 | 2.736 |
| `visobert/lora/exp001` | ViSoBERT + `ce` | 94,86 | 0,765 | 0,500 | 0,000 | 0,873 | **0,966** | 2.688 |
| `visobert/lora/exp002` | ViSoBERT + `weighted_ce` | 95,61 | 0,836 | 0,729 | 0,588 | 0,925 | 0,944 | 2.701 |

Ba điều phải đọc kèm:
1. `weighted_ce` **cứu được lớp âm** (+8,22 điểm ở PhoBERT, +0,75 ở ViSoBERT) và **đảo thứ hạng** hai
   encoder: ở lượt gốc ViSoBERT hơn PhoBERT 6,46 điểm, sang lượt `weighted_ce` PhoBERT hơn 1,01 điểm.
2. **Giá phải trả là PHÁT HIỆN khía cạnh giảm**: PhoBERT 98,05 → 94,14 (accuracy micro, cơ sở `all`),
   ViSoBERT 98,29 → 97,06 ⇒ báo cáo phải đưa **cặp chỉ số** (F1 lớp âm + phát hiện khía cạnh), không chỉ
   một chỉ số.
3. `price` âm vẫn **0,000 ở cả bốn lượt**, nhưng đó là **giới hạn của thước** (test chỉ có 6 ô `price` âm,
   `val` có 0 ô) - xem `08_experiment_rationale.md` §7.

## Chạy trên Colab

Mọi notebook LoRA (sáu model encoder) chạy được trên T4 (4-bit không bắt buộc: LoRA cơ bản vẫn vừa
6 GB VRAM). Ô bootstrap
tự cài `peft`, và với PhoBERT (`preprocess.segmenter: vncorenlp`) thì tự cài thêm `default-jdk` +
`py-vncorenlp`, đặt `JAVA_HOME` cho tiến trình, rồi tự tải model VnCoreNLP (27 MB) về gốc dữ liệu nếu
thiếu - người chạy không phải chép thư mục nào bằng tay.
`inference.dtype: auto` nghĩa là mã chọn bf16 khi máy hỗ trợ, fp16 khi không (T4 là Turing), fp32 trên
CPU - kiểu số đã dùng được ghi vào `run.log` và `run_meta.json`.

## Mở rộng

- Thêm cách huấn luyện khác (full fine-tune, QLoRA cho LLM): một module trong `src/training/` + một
  dòng trong `TRAINERS`, rồi khai `training.trainer` ở config.
- Thêm encoder: một module trong `src/preprocessing/` + một dòng trong `src/training/encoders.py` +
  file `configs/models/<model_id>.yaml` có `approach: encoder`.
