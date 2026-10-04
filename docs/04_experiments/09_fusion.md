# 04.09. Bước KẾT HỢP: ngưỡng, ensemble, luật lai, biểu quyết

> Đọc file này khi: chạy một trong bốn bước kết hợp, hoặc đọc số của chúng.
> Liên quan: `metrics.md` (luật đo), `06_lora_encoder.md` (tệp xác suất), `08_experiment_rationale.md`
> §7 (`price`), `present_plan.md` mục 8.4/8.5 và 10.2-10.4, `data/reports/fusion/README.md`.

## 1. Vì sao có bước kết hợp

Ba hướng đã cho thấy ba điểm mạnh KHÁC NHAU, nên ghép lại có cơ sở:

| Hướng | Mạnh ở đâu | Số cho thấy |
| --- | --- | --- |
| encoder học LoRA | **phát hiện khía cạnh** (F1 macro 0,957-0,966) và sau `weighted_ce` là **lớp âm** (0,876) | `06_lora_encoder.md` |
| Qwen3-4B hỏi bằng prompt | sắc thái tổng thể (accuracy TB 97,77) | `08_experiment_rationale.md` §3 |
| ba lượt lấy mẫu | đo **dao động** giữa các seed | `07_evolution.md` |

Bốn bước dưới đây KHÔNG chạy model: chúng đọc `predictions.csv` (nhãn cứng) và `probabilities.csv` (xác
suất từng ô - chỉ đường encoder có, xem `06_lora_encoder.md` mục 6), **chọn lại nhãn**, rồi chấm bằng
ĐÚNG engine của dự án. Số gốc của từng lượt KHÔNG bị chạm tới.

## 2. Hai luật bắt buộc

1. **Luật và ngưỡng chốt trên `val`, rồi mới áp lên `test`.** Xem `test` để chọn là tự lừa mình; tệp
   luật ghi vào repo (đóng băng) trước khi áp.
2. **`price` không có ngưỡng.** `val` có **0 ô** `price` âm (train 15, test 6) nên không có gì để dò:
   tệp ngưỡng ghi `null` + lí do, các ô `price` **giữ nguyên** quyết định của model gốc (nên cột `price`
   KHÔNG đổi khi thêm ngưỡng - đó là thiết kế, không phải lỗi), và `price` được đọc bằng **số lần model
   gán mã 2 + danh sách ô âm**, KHÔNG bằng F1 (xem `08_experiment_rationale.md` §7).

## 3. Bốn bước, bốn lệnh

### 3.1. Ngưỡng theo khía cạnh - `scripts/fit_thresholds.py`

```
python scripts/fit_thresholds.py --run experiments/<model>/<encoder>/<expNNN>/results/<hash8>
```

Đọc một lượt **`val`** của đường encoder. Với từng khía cạnh: quét lưới ngưỡng (mặc định 0,05 → 0,95),
tính F1 lớp âm của **chính khía cạnh đó**, chọn ngưỡng tốt nhất (hoà thì chọn ngưỡng **lớn** hơn - đổi
ít ô hơn). Quy tắc áp: `p(mã âm) >= τ` thì đoán mã âm, ngược lại giữ nguyên nhãn của model.

Ràng buộc đã chốt: nếu áp TẤT CẢ ngưỡng cùng lúc làm **số ô giảm quá 5%** thì bỏ dần ngưỡng của khía
cạnh ít lợi nhất - "kiêng trả lời để lấy điểm" không phải là tiến bộ.

Ghi `data/reports/fusion/thresholds.json`: ngưỡng chốt từng khía cạnh, F1 âm trước/sau, số ô trước/sau,
**bảng quét đầy đủ** của từng khía cạnh (làm bằng chứng), và macro theo **hai cách** (trên các khía cạnh
có ô âm, và trên các khía cạnh đang có F1 âm > 0) - cách thứ hai để nhiễu `price` không làm loãng kết luận.

Bước **ÁP** là lệnh thứ hai, và là lệnh sinh **số báo cáo** (dò trên `val`, áp lên `test`):

```
python scripts/fit_thresholds.py --apply-to experiments/<model>/<encoder>/<expNNN>/results/<hash8>
```

Đọc bảng ngưỡng ĐÃ ĐÓNG BĂNG (`--thresholds`, mặc định `thresholds.json`) rồi áp lên lượt đang có; ghi
`data/reports/fusion/thresholds_applied.json` với F1 âm từng khía cạnh **trước/sau**, số ô trước/sau, và
macro **ba cách** (trên khía cạnh có ô âm, trên khía cạnh đang dương, và trên MỌI khía cạnh - cách thứ ba
tính `price` là 0,0). Bảng luật chốt cho một **không gian nhãn** cụ thể, nên áp lên lượt khác mã âm là
**LỖI** (cột xác suất sẽ bị đọc lệch) chứ không phải cảnh báo bỏ qua. Không chạy model, không sửa bản gốc.

### 3.2. Ensemble encoder - `scripts/ensemble.py`

```
python scripts/ensemble.py --run <val A> --run <val B> [--weights val]
```

Trung bình **xác suất** của nhiều lượt encoder theo từng ô (ô chỉ có ở một phần các lượt thì lấy trung
bình của các lượt CÓ ô đó), rồi `argmax` theo từng khía cạnh. `--weights val` dùng trọng số theo macro-F1
lớp âm trên `val`, chuẩn hoá tổng = 1; mặc định trọng số bằng nhau. Lượt đầu tiên là lượt **giữ khung ô**.

### 3.3. Luật lai encoder + LLM - `scripts/fuse.py`

```
python scripts/fuse.py --fit --llm <val LLM> --encoder <val encoder> --out data/reports/fusion/rules.json
python scripts/fuse.py --apply --rules data/reports/fusion/rules.json --llm <test LLM> --encoder <test encoder>
```

Bước `--fit` chốt trên `val`: mỗi khía cạnh lấy nguồn có **F1 lớp âm cao hơn**; **hoà thì chọn LLM**
(nguồn mạnh về sắc thái) và ghi rõ hai số F1 để người đọc thấy đó là hoà. Khía cạnh không nguồn nào có ô
âm (như `price`) vẫn được ghi một dòng kèm lí do - bảng luật phủ HẾT khía cạnh, không để ô trống.

Bước `--apply` áp luật ĐÃ ĐÓNG BĂNG lên tập đang có và **đếm số ô lấy từ mỗi nguồn** (ô nào nguồn đã
chốt không có thì giữ nhãn của lượt LLM và đếm vào `thiếu`). Số của bản lai phải được so với **từng
nguồn một mình trên CÙNG tập** - thiếu phép so đó thì con số lai không nói lên gì.

### 3.4. Biểu quyết - `scripts/vote.py`

```
python scripts/vote.py --run <seed1> --run <seed2> --run <seed3>
```

Bỏ phiếu **từng ô** trên các lượt lấy mẫu; **ba mẫu** cho đợt này (luật 6 của `metrics.md`). Ô chỉ được
bỏ phiếu nếu **đọc được ở ít nhất một lượt**; **hoà thì lấy nhãn của lượt ĐẦU TIÊN** - nên phải truyền
các lượt theo thứ tự `seed` TĂNG DẦN (1, 2, 3). JSON ghi cả **số của từng mẫu** (để đo dao động) và
**thống kê phiếu** (số ô đủ phiếu, số ô hoà, số ô không lượt nào đọc được).

## 4. Đọc số của bước kết hợp thế nào

- **Luôn kèm số ô** (`cells_paper`) và **nói rõ cơ sở** (`all` hay `paper`) - hai luật đầu của `metrics.md`.
- **Macro hai cách** (có ô âm / đang có F1 âm > 0): `price` chỉ 1-6 ô nên một con số macro duy nhất cho 7
  khía cạnh là để nhiễu đó làm loãng kết luận.
- **So với từng thành phần trên cùng tập**: bản gộp/lai/chốt ngưỡng chỉ có nghĩa khi đứng cạnh số của
  từng lượt thành viên trên cùng `test` (hoặc cùng `val`).
- **`price` đọc riêng**, bằng số lần gán mã 2 và danh sách ô âm - không dùng F1.

## 5. Đầu vào rút gọn được COMMIT (vì sao)

Lượt chạy thật nằm trên Drive; repo KHÔNG commit `results/`. Muốn con số kết hợp tái lập được từ repo thì
phải giữ lại đúng phần mà bước kết hợp dùng: `data/reports/fusion/inputs/<model>_<method>_<exp>_<hash8>.csv`
(gồm `chỉ số`, `split`, `khía cạnh`, `nhãn đúng`, `nhãn đoán`, `p(mã âm)`, `p(mã dương)`; vài trăm KB mỗi
lượt; KHÔNG chứa văn bản review). Xem `data/reports/fusion/README.md`.

## 6. Bàn giao: nhóm encoder gửi thêm tệp xác suất

**Bảy tệp nhẹ** (`run.log`, `run_meta.json`, `metrics.json`, `metrics.csv`, `mispredictions.csv`,
`mispredictions_paper.csv`, `predictions.csv`) là bộ chuẩn cho MỌI lượt. `predictions.csv` là tệp thứ
BẢY (từ 04/10/2026): bước kết hợp dựng `inputs/*.csv` từ nó (khung ô + nhãn đúng/đoán), và lượt **DÒ**
cần nó để đo số token sinh. Riêng **nhóm encoder** gửi thêm `probabilities.csv` - thiếu nó thì người nhận
không chạy lại được ngưỡng/ensemble/lai. Ghi rõ ở `handover/README.md` và `present_plan.md` mục 7.4.
