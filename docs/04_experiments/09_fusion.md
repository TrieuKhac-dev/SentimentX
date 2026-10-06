# 04.09. Bước KẾT HỢP: ngưỡng, ensemble, luật lai, biểu quyết, router, gộp hai tầng

> Đọc file này khi: chạy một trong sáu bước kết hợp, hoặc đọc số của chúng.
> Liên quan: `metrics.md` (luật đo), `06_lora_encoder.md` (tệp xác suất), `08_experiment_rationale.md`
> §7 (`price`), `present_plan.md` mục 8.4/8.5 và 10.2-10.4, `data/reports/fusion/README.md`.

## 1. Vì sao có bước kết hợp

Ba hướng đã cho thấy ba điểm mạnh KHÁC NHAU, nên ghép lại có cơ sở:

| Hướng | Mạnh ở đâu | Số cho thấy |
| --- | --- | --- |
| encoder học LoRA | **phát hiện khía cạnh** (F1 macro 0,957-0,966) và sau `weighted_ce` là **lớp âm** (0,876) | `06_lora_encoder.md` |
| Qwen3-4B hỏi bằng prompt | sắc thái tổng thể (accuracy TB 97,77) | `08_experiment_rationale.md` §3 |
| ba lượt lấy mẫu | đo **dao động** giữa các seed | `07_evolution.md` |

Sáu bước dưới đây KHÔNG chạy model: chúng đọc `predictions.csv` (nhãn cứng) và `probabilities.csv` (xác
suất từng ô - chỉ đường encoder có, xem `06_lora_encoder.md` mục 6), **chọn lại nhãn**, rồi chấm bằng
ĐÚNG engine của dự án. Số gốc của từng lượt KHÔNG bị chạm tới.

## 2. Hai luật bắt buộc

1. **Luật và ngưỡng chốt trên `val`, rồi mới áp lên `test`.** Xem `test` để chọn là tự lừa mình; tệp
   luật ghi vào repo (đóng băng) trước khi áp.
2. **`price` không có ngưỡng.** `val` có **0 ô** `price` âm (train 15, test 6) nên không có gì để dò:
   tệp ngưỡng ghi `null` + lí do, các ô `price` **giữ nguyên** quyết định của model gốc (nên cột `price`
   KHÔNG đổi khi thêm ngưỡng - đó là thiết kế, không phải lỗi), và `price` được đọc bằng **số lần model
   gán mã 2 + danh sách ô âm**, KHÔNG bằng F1 (xem `08_experiment_rationale.md` §7).

## 3. Sáu bước, sáu lệnh

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
# 1) CHỐT trọng số trên val (và ghi số của bản gộp trên val)
python scripts/ensemble.py --run <val A> --run <val B> --weights val \
    --out data/reports/fusion/ensemble_val.json \
    --write-weights data/reports/fusion/weights_val.json
# 2) ÁP trọng số đã chốt lên test (KHÔNG tính lại trọng số trên test)
python scripts/ensemble.py --run <test A> --run <test B> \
    --weights-file data/reports/fusion/weights_val.json
```

Trung bình **xác suất** của nhiều lượt encoder theo từng ô (ô chỉ có ở một phần các lượt thì lấy trung
bình của các lượt CÓ ô đó), rồi `argmax` theo từng khía cạnh. Lượt đầu tiên là lượt **giữ khung ô**.
`--weights val` dùng trọng số theo macro-F1 lớp âm, chuẩn hoá tổng = 1; mặc định trọng số bằng nhau.

**Vì sao trọng số phải đi qua TỆP (chốt 05/10/2026):** `--weights val` tính trọng số từ CHÍNH các lượt
đang truyền vào, nên gọi nó trên các lượt `test` là chọn trọng số bằng tập sẽ báo cáo - đúng thứ luật 1
cấm; công cụ **chặn** ca đó (mã thoát 1). Lượt `val` và lượt `test` của cùng một encoder nằm ở hai thư
mục khác nhau (`.../exp003` và `.../exp004`), nên tệp trọng số khoá theo **TÊN MODEL** - đó là khoá duy
nhất sống qua được hai tập. `--weights-file` ráp theo model và **báo lỗi kèm tên model** nếu thiếu, chứ
không im lặng quay về trọng số bằng nhau.

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

### 3.5. Router theo khía cạnh - `scripts/ensemble_aspect.py`

```
# 1) CHỐT luật trên val (ghi tệp luật + số của bản router trên val)
python scripts/ensemble_aspect.py --fit --criterion f1_âm --run <val A> --run <val B> \
    --write-router data/reports/fusion/aspect_router.json \
    --out data/reports/fusion/router_val.json

# 2) ÁP lên test (đọc ĐÚNG tệp luật; KHÔNG chốt lại trên test)
python scripts/ensemble_aspect.py --apply --run <test A> --run <test B> \
    --router-file data/reports/fusion/aspect_router.json \
    --out data/reports/fusion/router_test.json
```

KHÁC ensemble (3.2): ensemble **trộn xác suất** bằng MỘT bộ trọng số cho mọi khía cạnh; router KHÔNG trộn -
mỗi khía cạnh lấy nhãn của **MỘT** lượt đã chốt. Lượt ĐẦU trong `--run` giữ **khung ô**, và **thứ tự truyền
vào là một phần của luật** (dùng khi hoà).

**Tiêu chí chốt là BẮT BUỘC và chỉ truyền được ở `--fit`** (`--criterion`), vì hai tiêu chí cho hai router
KHÁC NHAU - và tối ưu hai thứ khác nhau:

| Tiêu chí | Đo gì trên `val` | Kỳ vọng |
| --- | --- | --- |
| `f1_âm` | F1 lớp ÂM của chính khía cạnh (cơ sở `paper`) | sát luật của dự án (lớp âm là chỗ mọi lượt yếu), nhưng KHÔNG tối ưu accuracy |
| `accuracy` | accuracy ô của khía cạnh (cơ sở `all`) | sát chỉ số BÁO CÁO (bảng accuracy theo khía cạnh) |

Luật đầy đủ ở `fusion.ROUTER_LAW`: xét tiêu chí đã chốt -> tiêu chí còn lại -> **lượt ĐẦU** trong danh
sách; khía cạnh **không có ô âm nào trên `val`** (ca `price`) rơi xuống `accuracy` và tệp luật GHI RÕ lí do.

**Chống "chọn luật sau khi thấy `test`"** (luật 1.4): `--apply` **không nhận** `--criterion` - nó đọc tiêu
chí từ CHÍNH tệp luật; và tệp luật ghi kèm `điểm` của MỌI ứng viên (cả hai tiêu chí + số ô), nên người đọc
kiểm lại được lựa chọn và thấy lựa chọn khác sẽ ra sao mà không phải chạy lại model nào.

**Số phải đọc kèm**: `router_aspect.json` có `thành_viên` = số của TỪNG lượt trên cùng tập (mục 4); và nhớ
rằng **lượt đầu giữ khung ô** - nếu các lượt có tập ô cơ sở `paper` khác nhau thì đổi thứ tự `--run` là đổi
số ô báo cáo (không đổi luật, nhưng đổi mẫu số).

**Chạy thử HAI tiêu chí trên cùng bộ ứng viên (06/10/2026)** - để CHỌN tiêu chí đúng luật 1 (chọn trên `val`).
Bộ ứng viên đang có ở máy chỉ **2 lượt `val`** (`phobert-base-v2/lora/exp003`, `visobert/lora/exp003`); bốn
encoder còn lại CHƯA có lượt `val` nên không làm ứng viên được:

| | acc macro | F1 âm macro (`paper`) | số ô `paper` |
| --- | --- | --- | --- |
| trên **`val`** (tập để CHỌN): `--criterion f1_âm` | 93,08 | **0,9005** | 2.755 |
| trên **`val`**: `--criterion accuracy` | **95,97** | 0,8562 | 2.740 |
| trên **`val`**: trần chọn-theo-khía-cạnh (oracle `val`) | **95,97** | - | - |
| trên `test` (ĐỐI CHIẾU, không dùng để chọn): `f1_âm` | 93,28 | **0,7757** | 2.736 |
| trên `test`: `accuracy` | **96,16** | 0,7543 | 2.716 |
| trên `test`: oracle theo khía cạnh | 96,17 | - | - |

Đọc bảng này:

- **`--criterion accuracy` đạt ĐÚNG trần trên `val` (95,97)** và cũng sát trần trên `test` (96,16 so 96,17):
  lựa chọn trên `val` chuyển sang `test` được, và hơn **cả hai** lượt thành viên (trên `val`: 95,97 so 95,49
  và 93,08).
- **`--criterion f1_âm` thoái hoá thành "lấy phoBERT cho MỌI khía cạnh"** ở bộ ứng viên này: phoBERT thắng F1
  lớp âm ở cả 6 khía cạnh có ô âm trên `val` (xem khoá `điểm` trong `aspect_router_f1am.json`), nên router
  KHÔNG đổi gì so với một lượt đơn; nó chỉ giữ được F1 âm tốt hơn (0,7757 so 0,7543 trên `test`).
- **Hai tiêu chí là một ĐÁNH ĐỔI thật**: `accuracy` hơn 2,88 điểm accuracy nhưng kém 0,021 F1 âm macro. Chọn
  cái nào là quyết định của người dùng; điều KHÔNG được làm là đổi tiêu chí sau khi đã thấy `test` mà không
  nói ra.
- **Số ô `paper` ĐỔI theo lựa chọn** (2.736 / 2.716 trên `test`): cơ sở `paper` phụ thuộc cả nhãn ĐOÁN, nên
  đổi router là đổi mẫu số - luôn đọc số ô kèm con số (luật 1 của `metrics.md`).

**ĐỀ XUẤT (chờ người dùng xác nhận): dùng `accuracy`** cho số báo cáo - vì nó đạt trần trên `val` (tập dùng để
chọn) và hơn cả hai thành viên, còn `f1_âm` không chọn được gì khác ngoài lượt mạnh nhất. Nếu chốt `f1_âm` thì
phải đọc kèm cả accuracy và nói rõ router chỉ bằng một lượt đơn.

Chứng cứ đã commit: `aspect_router_f1am.json`, `aspect_router_accuracy.json`, `router_aspect_val_*.json`,
`router_aspect_*.json` và `inputs/*.csv` của 4 lượt tham gia (tái lập bằng hai lệnh ở đầu mục 3.5 với
`--criterion` tương ứng và `--write-router` khác tên).

### 3.6. Gộp HAI TẦNG theo khía cạnh - `scripts/fuse_aspect.py`

```
python scripts/fuse_aspect.py --encoder <lượt encoder> \
    --aspect <lượt một-khía-cạnh của colour> --aspect <... của packing> --aspect <... của price> \
    --aspect <... của shipping> --aspect <... của smell> --aspect <... của stayingpower> \
    --aspect <... của texture> \
    --out data/reports/fusion/fuse_aspect_test.json
```

Hướng HAI TẦNG: lượt **encoder** giữ **khung ô** (nó phát hiện khía cạnh tốt nhất đã đo: macro-F1
0,967), còn sắc thái **từng khía cạnh** lấy từ một lượt **một-khía-cạnh** của đường prompt (prompt
`absa_aspect_<khía cạnh>_v1` + khối hệ thống `system/absa_aspect_<khía cạnh>.txt`).

**LUẬT ĐÃ CHỐT TRƯỚC KHI CHẠY** (mục 14.10 của `present_plan.md`; hằng số `fusion.TWO_TIER_LAW`):

| Ca | Luật |
| --- | --- |
| khung ô | lấy từ lượt ENCODER (mọi dòng/khía cạnh của lượt đó) |
| sắc thái | mỗi khía cạnh lấy mã của lượt MỘT-khía-cạnh của chính khía cạnh đó |
| hai bên LỆCH về "không nhắc tới" | **giữ quyết định của ENCODER** - và ĐẾM riêng số ô đó |
| thiếu ô ở lượt một-khía-cạnh | giữ nhãn của encoder và đếm riêng |
| thiếu LƯỢT cho một khía cạnh, lượt chấm nhiều khía cạnh, lượt trùng khía cạnh, khác mã "không nhắc tới" | **LỖI**, không im lặng bỏ qua |

`đếm_ô.lệch_giữ_encoder` là con số phải đọc kèm: luật "giữ của encoder" ĐỔI kết quả, nên nếu không đếm
thì bản gộp chỉ còn một con số không kiểm được. Bản gộp này KHÔNG vào bảng `paper` cho tới khi được
chốt thành `method: fuse` (tiền lệ: `exp016`) - xem mục 11.3 và `present_plan.md` mục 14.11.

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
