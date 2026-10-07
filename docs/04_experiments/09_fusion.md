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

**Lần chạy ĐẦU (06/10/2026, 2 ứng viên) - để thử đường ống, KHÔNG phải một thành tích.** Bộ ứng viên lúc đó
chỉ **2 lượt `val`** (`phobert-base-v2/lora/exp003`, `visobert/lora/exp003`):

| | acc macro | F1 âm macro (`paper`) | số ô `paper` |
| --- | --- | --- | --- |
| trên **`val`** (tập để CHỌN): `--criterion f1_âm` | 93,08 | **0,9005** | 2.755 |
| trên **`val`**: `--criterion accuracy` | **95,97** | 0,8562 | 2.740 |
| trên **`val`**: trần chọn-theo-khía-cạnh (oracle `val`) | **95,97** | - | - |
| trên `test` (ĐỐI CHIẾU, không dùng để chọn): `f1_âm` | 93,28 | **0,7757** | 2.736 |
| trên `test`: `accuracy` | **96,16** | 0,7543 | 2.716 |
| trên `test`: oracle theo khía cạnh | 96,17 | - | - |

Ba điều đọc được (và đây là lí do phải đo lại): `accuracy` **đạt ĐÚNG trần `val`** (95,97) nên lựa chọn trên
`val` chuyển được sang `test`; `f1_âm` **thoái hoá** thành "lấy phoBERT cho MỌI khía cạnh"; hai tiêu chí là
một ĐÁNH ĐỔI thật (2,88 điểm accuracy so 0,021 F1 âm). Luật + `điểm` của mọi ứng viên:
`aspect_router_f1am_2model.json`, `aspect_router_accuracy_2model.json`.

**Lần chạy THỨ HAI (07/10/2026, 6 ứng viên) - mỗi encoder nay đã có MỘT lượt `val`** (bốn lượt `val` mới:
`cafebert/lora/exp005`, `phobert-large/lora/exp003`, `vibert-base-cased/lora/exp004`,
`xlm-roberta-base/lora/exp003`), nên bộ ứng viên đủ rộng để đo **TRẦN** của việc chọn-theo-khía-cạnh:

| | acc macro (`all`) | acc macro (`paper`) | F1 âm macro (`paper`) | số ô `paper` |
| --- | --- | --- | --- | --- |
| trên **`val`** (CHỌN): router, **cả hai tiêu chí** | 97,46 | 97,92 | 0,923 | 2.740 |
| trên **`val`**: **TRẦN** chọn-theo-khía-cạnh (oracle) | **97,46** | - | - | - |
| trên **`val`**: lượt đơn tốt nhất (`cafebert/lora/exp005`) | 97,38 | - | - | 2.741 |
| trên `test` (ĐỐI CHIẾU): router, **cả hai tiêu chí** | **97,66** | 97,72 | 0,795 | 2.741 |
| trên `test`: **TRẦN** oracle | **97,67** | - | - | - |
| trên `test`: lượt đơn tốt nhất (`cafebert/lora/exp001`) | 97,63 | - | - | 2.745 |

Đọc bảng này:

- **HAI TIÊU CHÍ NAY CHỌN CÙNG MỘT ROUTER** - `cafebert` 6/7 khía cạnh, chỉ `packing` lấy
  `phobert-base-v2` - nên hai dòng trùng số và router **không còn là một đánh đổi** như ở bộ 2 lượt. Hai tệp
  luật vẫn đóng băng riêng theo tiêu chí (`aspect_router_f1am.json`, `aspect_router_accuracy.json`) và mỗi
  tệp ghi `điểm` của MỌI ứng viên ở MỌI khía cạnh (cả hai tiêu chí + số ô) nên lựa chọn kiểm lại được.
- **TRẦN của việc chọn-theo-khía-cạnh ở bộ 6 ứng viên chỉ hơn lượt đơn tốt nhất +0,08 (`val`) / +0,04
  (`test`)**; router đo được **+0,03** trên `test` (97,66 so 97,63). Nói thẳng: ở bộ ứng viên này bước router
  **không đáng kể**.
- **ĐÍNH CHÍNH con số "+0,51" (ghi 06/10/2026).** Số đó là một ƯỚC LƯỢNG đọc từ bộ ứng viên 2 lượt, KHÔNG
  phải số đo của bộ 6 lượt; số ĐO được là như bảng trên. Mọi chỗ đã ghi "+0,51" đã được sửa theo số đo (xem
  `check_present_plan.md` mục 17).
- **Vì sao trần thấp:** sáu ứng viên cùng MỘT họ huấn luyện (`lora` + `weighted_ce`, đầu phân loại đóng băng)
  nên chúng **sai giống nhau**; chọn theo khía cạnh không tạo ra thông tin chưa có. Muốn có đất thật thì bộ
  ứng viên phải khác nhau về CƠ CHẾ (ví dụ một lượt đầu phân loại HỌC) - đó là lí do tạo `cafebert/lora/exp006`.
- **`f1_âm` HẾT thoái hoá:** với 6 ứng viên nó chọn `cafebert` ở **5/6** khía cạnh có ô âm, chỉ thua `packing`
  (0,900 so `phobert-base-v2` **0,923**) - tức tiêu chí nay PHÂN BIỆT được.
- **Số ô `paper` vẫn phụ thuộc lựa chọn** (2.740 / 2.741 / 2.745 trên `test`): cơ sở `paper` phụ thuộc cả nhãn
  ĐOÁN nên đổi router là đổi mẫu số - luôn đọc số ô kèm con số (luật 1 của `metrics.md`).

**Vì sao `f1_âm` "thoái hoá" ở bộ 2 LƯỢT (lần chạy ĐẦU)** - bảng người thắng của TỪNG khía cạnh trên `val`:

| Khía cạnh | F1 âm trên `val` (phoBERT / ViSoBERT) | thắng | accuracy trên `val` (phoBERT / ViSoBERT) | thắng |
| --- | --- | --- | --- | --- |
| colour | 0,816 / 0,702 | phoBERT | 91,57 / **93,72** | ViSoBERT |
| packing | **0,923** / 0,476 | phoBERT | **98,17** / 97,20 | phoBERT |
| price | (0 ô âm) / (0 ô âm) | *rơi xuống accuracy* | **98,82** / 98,63 | phoBERT |
| shipping | **0,981** / 0,952 | phoBERT | **97,06** / 94,86 | phoBERT |
| smell | **0,925** / 0,873 | phoBERT | 98,09 / **98,36** | ViSoBERT |
| stayingpower | **0,891** / 0,832 | phoBERT | 85,51 / **94,95** | ViSoBERT |
| texture | **0,867** / 0,826 | phoBERT | 82,32 / **90,69** | ViSoBERT |

Ở bộ 2 lượt, `f1_âm` chọn **phoBERT cho CẢ 7 khía cạnh** nên bản router **trùng khít** lượt phoBERT chạy một
mình (`acc macro 93,28 · 2.736 ô · F1 âm macro 0,7757` trên `test`) - đó là nghĩa hẹp của "thoái hoá": tiêu
chí mất khả năng **phân biệt**. Ngược lại `accuracy` chọn **4 ViSoBERT + 3 phoBERT** ⇒ trộn thật.

**Bảng trên là DẤU VẾT của một hiện tượng đã hết:** nó thuộc bộ ứng viên **2 lượt**. Ở bộ 6 lượt (bảng đầu
mục này) cả hai tiêu chí đều chọn `cafebert` 6/7 khía cạnh, nên "thoái hoá" đến từ **bộ ứng viên quá hẹp**,
KHÔNG phải từ bản chất tiêu chí - đúng như dự đoán đã ghi lúc chốt và nay đã ĐO được.

**QUYẾT ĐỊNH (chốt 06/10/2026, giữ nguyên): BÁO CÁO CẢ HAI DÒNG.** Bảng router có **hai dòng** - một dòng
`--criterion accuracy`, một dòng `--criterion f1_âm` - mỗi dòng ghi rõ **tiêu chí của nó**, số ô, và số của
các lượt thành viên, gắn cứng với **một tệp luật đóng băng** (`aspect_router_accuracy.json`,
`aspect_router_f1am.json`): đây KHÔNG phải "chọn luật sau khi thấy `test`" - cả hai luật được chốt trên `val`
rồi mới áp lên `test`. **Dòng `accuracy` là dòng chính** (khớp bảng accuracy theo khía cạnh của dự án).
**Khác so với lúc chốt:** ở bộ 6 ứng viên hai tiêu chí chọn CÙNG một router nên hai dòng **trùng số**; giữ đủ
hai dòng vẫn cần vì nó là dấu vết cho thấy tiêu chí đã chốt TRƯỚC khi thấy `test`, và vì `điểm` của mọi ứng
viên nằm trong tệp luật nên người đọc dò lại được cả lựa chọn lẫn điều sẽ xảy ra nếu chọn tiêu chí kia.

Chứng cứ đã commit: `aspect_router_f1am.json` / `aspect_router_accuracy.json` (LUẬT, 6 ứng viên),
`router_aspect_val_f1am.json` / `router_aspect_val_accuracy.json` (số trên `val`),
`router_aspect_f1am.json` / `router_aspect_accuracy.json` (số trên `test`), mỗi tệp kèm `thành_viên` = số của
TỪNG lượt trên cùng tập, và `inputs/*.csv` của **12 lượt** tham gia. Bộ **2 ứng viên** giữ làm dấu vết bằng
hậu tố `_2model` (`*_2model.json` của lần chạy đầu); tái lập bằng hai lệnh ở đầu mục 3.5 với `--criterion`
và `--write-router` tương ứng.

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

**KẾT QUẢ ĐO (07/10/2026, `test`, cùng bảy lượt một-khía-cạnh)** - hai khung, để thấy luật "lệch về không
nhắc tới thì giữ encoder" đổi kết quả thế nào. Bảy lượt một-khía-cạnh là `qwen3-4b-instruct-2507/prompt-aspect/exp001..007`
(`price`, `texture`, `packing`, `stayingpower`, `shipping`, `smell`, `colour`):

| Bản | acc TB (`all`) | acc TB (`paper`) | F1 âm macro (`paper`) | `price` F1 âm | ô lệch giữ encoder | số ô `paper` |
| --- | --- | --- | --- | --- | --- | --- |
| `phobert-base-v2/lora/exp004` một mình (mốc) | **93,28** | **96,62** | 0,7757 | **0,000** | - | 2.736 |
| **gộp hai tầng**, khung `phobert-base-v2/lora/exp004` | 93,15 | 95,87 | **0,8159** | **0,357** | 1.058 | 2.736 |
| `cafebert/lora/exp001` một mình (mốc) | **97,63** | **97,72** | 0,7876 | **0,000** | - | 2.745 |
| **gộp hai tầng**, khung `cafebert/lora/exp001` | **97,38** | 96,42 | 0,8124 | 0,320 | 653 | 2.745 |

Đọc cho đúng:

- **Đây là thứ ĐẦU TIÊN làm F1 âm của `price` khác 0** (0,000 &#8594; 0,357) và đẩy F1 âm macro `paper` lên
  **+0,040** - đó là TOÀN BỘ phần được, và nó vẫn chỉ tính trên **6 ô** (đọc như §7 của
  `08_experiment_rationale.md`: "có đường chạm tới lớp âm", KHÔNG phải "model đã giỏi `price`").
- **Giá phải trả:** khung phobert mất **−0,75** acc TB `paper` (96,62 &#8594; 95,87) và 0,13 điểm acc TB `all`;
  khung cafebert mất ít hơn trên `all` (−0,25) nhưng nhiều hơn trên `paper` (−1,30). **Khung nào cũng đánh đổi
  ~0,75 điểm `paper` để lấy +0,040 F1 âm macro** - vì vậy bản hai tầng **không** thay bảng chính.
- **Luật "lệch về không nhắc tới thì giữ encoder" KHÔNG phải chi tiết nhỏ:** nó giữ lại **1.058 ô** (khung
  phobert) / **653 ô** (khung cafebert). Thiếu con số đó thì không biết bản gộp lấy bao nhiêu ô từ mỗi bên,
  và `price` là khía cạnh lệch nhiều nhất trong nhóm dùng được (`stayingpower` 320 · `texture` 298 ở khung
  phobert).
- **Lượt một-khía-cạnh KHÔNG cần `probabilities.csv`**: luật gộp chỉ dùng **nhãn cứng** (`merge_two_tier`), mà
  đường prompt không ghi tệp xác suất - `scripts/fuse_aspect.py` đã bỏ đòi hỏi đó (kèm test chống tái phát),
  nếu không thì bước này không chạy được trên đúng bảy lượt nó sinh ra để dùng.
- Chứng cứ đã commit: `fuse_aspect_test.json` (khung phobert) + `fuse_aspect_test_cafebert.json` (khung
  cafebert) + `inputs/*.csv` của **8 lượt** tham gia (1 encoder + 7 lượt một-khía-cạnh).

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
