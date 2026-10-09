# batch11_report - Trả lời 11 câu hỏi phản biện (đợt 11)

> **Trạng thái: ĐANG VIẾT.** Nội dung dưới đây để **GHÉP** vào `presentations/present_report/present_report.md`
> khi bạn cho phép - hiện tệp đó bạn đang sửa nên tôi không đụng vào.
>
> Quy ước số (giống `present_report.md`): cơ sở `paper` (chỉ ô mà CẢ nhãn đúng và nhãn đoán là
> positive/negative - đúng cách công bố đếm), split `test` 1.623 review, **luôn đọc kèm SỐ Ô**; mục nào ghi rõ
> cơ sở `all` thì đọc theo `all`. Số lấy từ `experiments/**/results/<hash8>/metrics.json`, KHÔNG lấy từ
> `data/reports/**`. Mục nào còn chờ lượt chạy thì ghi **CHỜ KẾT QUẢ**.

## Trạng thái đợt 11: 48 lượt mới đã tạo + ghim (Đ1-Đ7) - **0/48 đã chạy**; 6 lượt LLM còn chặn vì repo GATED

Mọi lượt dưới đây **đã tạo, đã ghim vào một commit có thật trên `origin/experiment`, và đã đóng gói bàn
giao** (`handover/out/`, gói duy nhất **029** - thay cho 022/023/024/026/027/028; bản 029 chỉ sửa TÀI LIỆU
trong README của gói, 48 notebook y nguyên). Cột "khác cha" là khoá DUY
NHẤT khác lượt cha - đã kiểm bằng phép so cấu hình ĐÃ HỢP NHẤT, không bằng mắt.

**Lỗi chặn đã sửa 09/10/2026 (trước khi có lượt nào chạy xong).** Người chạy mở 8 notebook đầu tiên của
gói 027 và cả 8 đều DỪNG ở ô kiểm trước với cùng một việc: *"Thí nghiệm khai `data.version` v0.2.0 nhưng
file config dataset khai v0.3.0"*. Nguyên nhân không nằm ở config (45/48 lượt khai v0.2.0 là **cố ý** -
chúng phải so với kết quả cũ vốn chấm trên bản đó), mà ở ba chỗ nạp file phiên bản dữ liệu: ô cấu hình của
notebook, `preflight`, và phần chọn chế độ chạy (`plan`) đều gọi hàm nạp mà **không truyền `data.version`**
- hàm đó khi thiếu version lấy bản **mới nhất theo tên file**, nên:

1. preflight so `data.version` (v0.2.0) với bản nó vừa tự nạp (v0.3.0) → báo lệch → DỪNG người chạy (45/48
   lượt; chỉ 3 lượt nhánh emoji khai v0.3.0 mới qua);
2. và **nếu chỉ bỏ phép kiểm thì mọi lượt sẽ lặng lẽ chấm trên bộ v0.3.0** trong khi config khai v0.2.0 -
   tức phép ablation so với cha (chạy trên v0.2.0) mất tính "một biến", mà lại còn giấu đi.

Cách sửa (3 commit `7d69b32`, `4f65864`, `c96dec8`): nạp file phiên bản dữ liệu qua **một chỗ duy nhất**
`experiments.dataset_of(config)` cho cả ô cấu hình notebook, `preflight`, `checks` và `plan`; khai một bản
CŨ là hợp lệ (chỉ còn một **dòng ghi chú** "đọc bản thí nghiệm khai, KHÔNG phải bản mới nhất"); khai một bản
**không tồn tại** thì vẫn DỪNG kèm danh sách bản đang có. Khoá bằng 5 test mới, và kiểm bằng chính công cụ
của dự án: `run_notebook.py <exp> --preflight-only` cho **48/48 notebook xanh** ở commit ghim mới
(`4f65864`), trong đó có đủ 8 notebook đã chặn người chạy hôm nay. Gói **029** (nối tiếp **028**) mang đúng 48 notebook đó,
giữ nguyên cấu hình và thứ tự chạy.

| Nhóm | Lượt | Số | Khác cha ở đâu | Trạng thái |
| --- | --- | --- | --- | --- |
| **Đ1** "điểm đến từ đâu" | `phobert-base-v2/none/exp001-002`, `cafebert/none/exp001-002`, `phobert-base-v2/lora/exp008-011`, `cafebert/lora/exp007` | 9 | `trainer: none` / `head.trainable` / `checkpoints.best_metric` / `decoding.seed` | đã ghim, chờ chạy |
| **Đ2** tiền xử lý | `phobert-base-v2/lora/exp012-015`, `visobert/lora/exp006-009`, `cafebert/lora/exp008-011` | 12 | `preprocess.segmenter` (3 bộ) hoặc `data.version: v0.3.0` | đã ghim, chờ chạy |
| **Đ3** tham số LoRA | `phobert-base-v2/lora/exp016-020`, `cafebert/lora/exp012-016` | 10 | `lora.r` / `lr` / `lora.target_modules` | đã ghim, chờ chạy |
| **Đ4** mất mát & cách học | `phobert-base-v2/lora/exp021-023`, `cafebert/lora/exp017-019` | 6 | `loss.type: focal` / `loss.class_weight: inverse_by_aspect` / `lora.use_dora` | đã ghim, chờ chạy |
| **Đ5** full fine-tune | `phobert-base-v2/full/exp001-002`, `cafebert/full/exp001` | 3 | `method` + `trainer: full` (+ `lr` ở `exp002`) | đã ghim, chờ chạy |
| **Đ6/Đ7** LLM lớn hơn & khác họ | `qwen3-8b` (0/1/5 ví dụ) · `qwen3-4b-thinking-2507` (DÒ + 1 lượt) · `mistral-7b-instruct-v0.3` (0/1/5 ví dụ) | 8 | `model` (+ các khoá thuộc LỚP MODEL: checkpoint, batch, ngưỡng cắt đo được) | đã ghim, chờ chạy |
| **Đ6/Đ7** phần CHẶN | `llama-3.1-8b-instruct` · `vistral-7b-chat` | 6 | - | **CHƯA TẠO: repo GATED**, cần `HF_TOKEN` |

Bảng này là **cái để đối chiếu khi có kết quả**: mỗi nhóm ghi số vào đúng mục M của báo cáo này
(Đ1 → M1/M3 · Đ2 → M2 · Đ3 → M5 · Đ4 → M6/M7 · Đ5 → M7 · Đ6/Đ7 → M9).

## M1. Ba bậc: KHÔNG học gì / học chỉ đầu phân loại / LoRA - **CHỜ KẾT QUẢ**

| Bậc | PhoBERT-base | CafeBERT | Trả lời |
| --- | --- | --- | --- |
| **SÀN** - không tối ưu gì (encoder đóng băng + đầu phân loại NGẪU NHIÊN) | `phobert-base-v2/none/exp001` | `cafebert/none/exp001` | mục 1 |
| **LINEAR PROBE** - encoder đóng băng, CHỈ đầu phân loại học | `phobert-base-v2/none/exp002` | `cafebert/none/exp002` | mục 1 |
| **LoRA** - adapter + đầu phân loại (mốc so) | `phobert-base-v2/lora/exp002` = **96,62** | `cafebert/lora/exp002` = **97,88** | mốc so |

Chờ 4 lượt `none` của Đ1. Kỳ vọng đọc số: SÀN ở mức đoán theo tần suất và F1 âm ~ 0; PROBE hơn SÀN rõ nhưng
**dưới LoRA**. Nếu SÀN **không** xấu thì đó là lỗi ống dẫn (nạp checkpoint / chấm điểm), không phải kết luận.

## M2. Tiền xử lý: emoji & tách từ - **MỘT PHẦN**

**Emoji:** đo trực tiếp trên dữ liệu gốc (`data/raw/cosmetics/v0.1.0/`), cùng định nghĩa emoji mà EDA dùng
(`utils.EMOJI_PATTERN`, gồm tông màu da và chuỗi nối ZWJ):

| split | review CÓ emoji | tỉ lệ | tổng số emoji |
| --- | --- | --- | --- |
| train | 1.931 / 12.981 | 14,9% | 12.504 |
| val | 233 / 1.623 | 14,4% | 1.463 |
| test | 222 / 1.623 | 13,7% | 1.219 |

Nhánh `icon` **bỏ emoji ở `train` và `val`; `test` giữ nguyên từng ký tự** (điều kiện để vẫn so được với công bố).
Đọc trước: chỉ ~14% review bị chạm, và **không** review nào của `test` bị chạm - nên phép so công bố vẫn nguyên vẹn.

**Bất biến đã ĐO được của nhánh icon** (so TỪNG DÒNG hai phiên bản dữ liệu v0.2.0 và v0.3.0, cùng
`test` gốc): số dòng **không đổi** (12.268 / 1.535 / 1.623), bộ cột **không đổi**, và văn bản khác nhau ở
**đúng 1.877 dòng `train` + 227 dòng `val`** - tức đúng bằng số review CÓ emoji, không dòng nào khác bị
chạm; **`test` 0 dòng đổi**. Đây là phép kiểm "chỉ đổi một biến" của nhánh này, và cũng là phép kiểm bắt
được một lỗi thật: bản đầu của `remove_emoji` dùng `\s+ -> " "` nên nuốt luôn ký tự XUỐNG DÒNG, làm
**4.158** dòng `train` đổi (hơn gấp đôi số dòng có emoji) - đã sửa và khoá bằng test.
Lưu ý đọc số: 1.877 và 227 là số đo trên dữ liệu ĐÃ QUA bước Clean (nên nhỏ hơn con số thô 1.931 / 233
ở bảng trên, vốn đếm trên dữ liệu gốc).

**Tách từ (thang 4 bậc mỗi model):**

| Model | gốc | bậc A (bật/tắt) | bậc B1 | bậc B2 |
| --- | --- | --- | --- | --- |
| `phobert-base-v2` | `vncorenlp` (`lora/exp005`) | `none` | `underthesea` | `pyvi` |
| `visobert` | `none` (`lora/exp005`) | `vncorenlp` | `underthesea` | `pyvi` |
| `cafebert` | `none` (`lora/exp002`) | `vncorenlp` | `underthesea` | `pyvi` |

Chờ 12 lượt Đ2. Đoán trước khi đọc số: `phobert-base-v2` **giảm** khi tắt tách từ (tokenizer không khớp tiền huấn
luyện); `visobert`/`cafebert` **giảm** khi bật tách từ (SentencePiece đọc văn bản nguyên bản).

## M3. Chọn `model/best` theo **F1** hay theo **accuracy** - **CHỜ KẾT QUẢ**

Tiêu chí mặc định của dự án là `checkpoints.best_metric: sentiment_f1` (**macro-F1 của SẮC THÁI**, đo trên `val`)
vì dữ liệu mất cân bằng. Lượt mới đổi **đúng một khoá** sang `accuracy_cell`:

| Cơ chế đầu phân loại ↓ / Tiêu chí → | `sentiment_f1` (đã có) | `accuracy_cell` (chờ) |
| --- | --- | --- |
| **ĐÓNG BĂNG** | `phobert-base-v2/lora/exp002` = **96,62** | `phobert-base-v2/lora/exp009` |
| **HỌC** | `phobert-base-v2/lora/exp005` = **97,59** | `phobert-base-v2/lora/exp008` |
| **HỌC** (CafeBERT) | `cafebert/lora/exp002` = **97,88** | `cafebert/lora/exp007` |

Đọc kèm `model/best/trainer_state.json::best.step` của **cả hai** lượt: nếu cùng một bước thì hai tiêu chí chọn
cùng checkpoint và điểm **giống hệt** - đó cũng là kết luận hợp lệ ("tiêu chí không đổi kết quả ở model này").
Lưu ý kỹ thuật: **không thể** lấy lượt cũ chọn lại theo accuracy, vì `checkpoints.keep_last_k: 2` +
`delete_intermediate: true` đã xoá các checkpoint trung gian.

## M4. Đầu phân loại: ĐÓNG BĂNG hay HỌC - **ĐÃ ĐỦ** (6 cặp; 2 lượt nhiễu mới của Đ1 đang chờ)

Sáu cặp, mỗi cặp khác cha **đúng một khoá** `head.trainable: true`; cơ sở `paper`; `% đọc được` = 100 và `greedy`
ở cả sáu cặp:

| Model | ĐÓNG BĂNG | acc TB | F1 âm macro | HỌC | acc TB | F1 âm macro | Δ acc |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `phobert-large` | `lora/exp001` | 96,54 | - | `lora/exp002` | **97,69** | - | **+1,15** |
| `xlm-roberta-base` | `lora/exp001` | 95,20 | - | `lora/exp002` | **96,36** | - | **+1,16** |
| `phobert-base-v2` | `lora/exp002` | 96,62 | 0,876 | `lora/exp005` | **97,59** | 0,884 | **+0,97** |
| `visobert` | `lora/exp002` | 95,61 | 0,836 | `lora/exp005` | **96,28** | 0,849 | **+0,67** |
| `cafebert` | `lora/exp001` | **97,67** | 0,886 | `lora/exp002` | **97,88** | 0,917 | **+0,21** |
| `vibert-base-cased` | `lora/exp001` | 94,99 | 0,828 | `lora/exp002` | 94,84 | 0,822 | **−0,15** |

**Thước nhiễu (đo 05/10/2026 - chạy lại cha với `decoding.seed: 7`):** `cafebert/lora/exp003` **98,00** (so 97,67) ·
`cafebert/lora/exp004` **98,26** (so 97,88) · `vibert-base-cased/lora/exp003` **95,66** (so 94,99)
⇒ **biên nhiễu ±0,33 … ±0,67 điểm**.

Năm điều đọc được:

1. **5/6 cặp nhỉnh hơn (+0,21 → +1,16), cùng chiều ở năm họ model** ⇒ tín hiệu **yếu nhưng nhất quán**. Trong đó
   chỉ **2 cặp vượt biên nhiễu**: `phobert-large` **+1,15** và `xlm-roberta-base` **+1,16**.
2. **CafeBERT là chỗ phải đọc kỹ nhất** vì nó có **HAI lần rút thăm mỗi nhánh** (seed 42 và seed 7): đóng băng
   {97,67 · 98,00} so với học-đầu {97,88 · 98,26} ⇒ **hai khoảng CHỒNG nhau** ⇒ ở CafeBERT **không kết luận được**
   là có khác biệt. Đây chính là lý do "đầu phân loại HỌC" **không** được dùng để thay lượt cha trong bảng chính.
3. **Đường lớp âm gần như đứng yên** (+0,008 · +0,013 · +0,006 · 0,000 · −0,013), riêng `cafebert` nhích
   **+0,059** (0,788 → 0,847).
4. **Chỗ đổi rõ nhất không phải tổng điểm mà là DỊCH CHUYỂN giữa các khía cạnh**: học đầu làm `packing` rơi ở 4/6
   cặp (`phobert-base-v2` 0,952→0,900 · `phobert-large` 0,900→0,818 · `vibert` 0,533→0,455 · `xlm-r` 0,889→0,706)
   trong khi `stayingpower`/`texture` tăng (PhoBERT 0,915→0,968 và 0,893→0,936) ⇒ học đầu **bớt dựa vào đoán theo
   tần suất**: khía cạnh ít ô hơn mất, khía cạnh khó hơn được.
5. **Chọn MODEL quan trọng hơn chọn đầu phân loại**: lượt học-đầu tốt nhất (`cafebert/lora/exp002`, 97,88) vẫn là
   **cùng model** với lượt đóng-băng tốt nhất (`cafebert/lora/exp001`, 97,67); không model nào đổi thứ hạng.

**Cơ chế đã thử và BỊ LOẠI: `head.aspect_marker`** (khía cạnh đi vào ĐẦU VÀO của đầu phân loại). Bố cục 2×2 trên
`phobert-base-v2`, cơ sở `all`: `exp002` **93,28** / `exp006` **51,60** (đầu đóng băng) và `exp005` **97,25** /
`exp007` **50,51** (đầu học) ⇒ phá **phát hiện khía cạnh** (0,891→0,495 và 0,959→0,489), biến model thành máy
**báo động giả** (precision "có nhắc" macro 0,825→0,356), mất **−41,68** và **−46,74** điểm. Cho đầu phân loại
**HỌC cũng không cứu được** (hai lượt marker xấp xỉ nhau) ⇒ nguyên nhân là **CẤU TRÚC**: khía cạnh chỉ vào được
như một **hằng số riêng** (`W[:,H:]·e_a`), và năng lực đầu bị cắt **16.149 → 2.328** tham số. **Giữ mặc định `false`.**

**Chờ** hai lượt nhiễu mới `phobert-base-v2/lora/exp010` (đầu đóng băng) và `exp011` (đầu học) để PhoBERT-base cũng
có **hai lần rút thăm mỗi nhánh** như CafeBERT.

## M5. Tham số LoRA - **CHỜ KẾT QUẢ** (Đ3, 10 lượt)

Hiện **mọi lượt dùng CÙNG một bộ**: `lora.r 16 · alpha 32 · dropout 0,05 · lr 2e-4 · epochs 3 · batch 8 ·
grad_accum 4 · weight_decay 0,01`. Wave 1 đổi **mỗi lượt đúng một khoá**:

| Khoá đè | Giá trị | PhoBERT-base (cha `lora/exp005`) | CafeBERT (cha `lora/exp002`) |
| --- | --- | --- | --- |
| `lora.r` | 8 / 32 | `exp016` / `exp017` | `exp012` / `exp013` |
| `lr` | 1e-4 / 4e-4 | `exp018` / `exp019` | `exp014` / `exp015` |
| `lora.target_modules` | `[query, value]` | `exp020` | `exp016` |

Hai điều phải ghi khi đọc: đổi `r` mà giữ `alpha` là **đổi luôn tỉ lệ scaling** `α/r`; và luôn đọc **cặp chỉ số**
(F1 lớp âm **và** `detection_f1`) vì `weighted_ce` đã biết là **hạ phát hiện khía cạnh**.

**Trạng thái:** 10 lượt đã **tạo + ghim** (commit `606c35b`); mỗi lượt khác lượt cha **đúng một khoá đo
được** - đã kiểm bằng phép so cấu hình ĐÃ HỢP NHẤT của con với cha, không phải bằng mắt. Chưa có kết quả:
cột số sẽ điền khi chạy xong trên Colab.

## M6. Hàm mất mát - **MỘT PHẦN** (đã có `ce` → `weighted_ce`; `focal` và `inverse_by_aspect` đang chờ)

| Hàm mất mát | Lượt | acc TB | F1 âm macro | detection F1 |
| --- | --- | --- | --- | --- |
| `ce` | `phobert-base-v2/lora/exp001` | 88,40 | 0,540 | **0,957** |
| `weighted_ce` + `inverse` | `phobert-base-v2/lora/exp002` | **96,62** | **0,876** | 0,891 |
| `ce` → `weighted_ce` + `inverse` | `visobert/lora/exp001` → `exp002` | 94,86 → **95,61** | 0,765 → **0,836** | 0,966 → 0,944 |

Đọc: `weighted_ce` **cứu được lớp âm** (+8,22 điểm acc ở PhoBERT; F1 âm 0,540 → 0,876) và **đảo thứ hạng** hai
encoder (lượt gốc ViSoBERT hơn PhoBERT 6,46 điểm; sang `weighted_ce` thì PhoBERT hơn 1,01) - **nhưng cái giá là
phát hiện khía cạnh giảm** (PhoBERT 98,05 → 94,14 accuracy micro, cơ sở `all`). Vì thế mọi kết luận về hàm mất mát
phải đưa **cặp chỉ số**, không chỉ một chỉ số.

**Hai hướng mới của đợt 11** (đã tạo + ghim ở `f230ef0`, chưa có số):

| Hướng | Lượt | Trạng thái |
| --- | --- | --- |
| `focal` (`gamma: 2`, **không** trọng số lớp) | `phobert-base-v2/lora/exp021` · `cafebert/lora/exp017` | chờ chạy |
| `weighted_ce` + `inverse_by_aspect` (đếm trọng số RIÊNG từng khía cạnh) | `phobert-base-v2/lora/exp022` · `cafebert/lora/exp018` | chờ chạy |

Đọc kèm hai điều: (a) lượt `focal` **không** dùng trọng số lớp, nên so nó với lượt cha `weighted_ce` là so
**hai biến** (hàm mất mát VÀ trọng số) - muốn tách hẳn thì so từng dòng `predictions.csv`; lượt
`inverse_by_aspect` mới là lượt so **sạch** với cha (cùng hàm mất mát, chỉ khác chỗ đếm trọng số); (b) dự án
**từ chối** cấu hình `ce` + trọng số vì nó TRÙNG `weighted_ce` - hai tên cho một phép tính thì bảng so sánh
sẽ có hai dòng trông như hai thí nghiệm khác nhau.

## M7. Cách huấn luyện - **CHỜ KẾT QUẢ** (DoRA ở Đ4, full fine-tune ở Đ5)

| Cách huấn luyện | Lượt | Trạng thái |
| --- | --- | --- |
| `lora` (adapter peft) - cách của MỌI lượt encoder hiện có | tất cả | đã có |
| `none` (KHÔNG adapter: SÀN + linear probe) | 4 lượt ở Đ1 | chờ |
| `lora` + **DoRA** (`lora.use_dora: true`) | `phobert-base-v2/lora/exp023` · `cafebert/lora/exp019` | đã tạo + ghim (`f230ef0`), chờ chạy |
| `full` (toàn bộ encoder + đầu phân loại) | `phobert-base-v2/full/exp001` · `exp002` (lr 2e-5) · `cafebert/full/exp001` | đã tạo + ghim (`a130424`), chờ chạy |

Đọc kèm hai điều của lượt `full`: (a) **`trainable_params` phải BẰNG `total_params`** - nhỏ hơn nghĩa là đã
rơi về đóng băng một phần và lượt chạy KHÔNG còn là full fine-tune; (b) hai lượt `exp001` giữ nguyên `lr`
2e-4 (mức của LoRA) để phép so chỉ đổi MỘT biến, còn `exp002` hạ xuống 2e-5 theo mức thông lệ - nếu
`exp001` phân kỳ thì **đó cũng là kết quả** (nói rằng `lr` của LoRA không dùng được cho full fine-tune), và
`exp002` là lượt trả lời câu hỏi chính.

## M8. Model NHỎ HƠN cho Qwen3-4B: Qwen3-0.6B - **ĐÃ ĐỦ** (mục RIÊNG, KHÔNG trộn vào bảng best model)

### M8.1 Bảng "Dùng được để so?"

| Lượt 0,6B | `% đọc được` | **Dùng được để so?** | Số ô chấm được | Ghi chú |
| --- | --- | --- | --- | --- |
| `prompt-cot/exp001` (0 ví dụ) | 42,02 | **KHÔNG** | - | model không in ra JSON đọc được |
| `prompt-cot/exp002` (1 ví dụ) | 21,63 | **KHÔNG** | - | như trên |
| `prompt-cot/exp003` (5 ví dụ) | 84,41 | **KHÔNG** | - | như trên |
| `prompt-one-turn/exp001` (một lượt) | 99,94 | CÓ | **877** | đọc được nhưng **kiêng trả lời** |
| `prompt-cot/exp005` (bật suy nghĩ, trần 1.985) | 96,98 | CÓ | 1.638 | đọc được nhưng **phá phát hiện khía cạnh** |
| `prompt-cot/exp004` (lượt DÒ, 60 mẫu) | 98,33 | CÓ | - | chỉ để **chốt trần token** (`max_new_tokens = 1.985`) |

> **`Dùng được để so?` = CÓ khi model đọc được ≥ 95%** số review (cửa chất lượng của dự án). Dưới mức đó, con số
> **không** được dùng để so với công bố.

### M8.2 Qwen3-4B so với Qwen3-0.6B (cùng prompt, cùng `test`, cơ sở `paper`)

| | 0 ví dụ | 1 ví dụ | 5 ví dụ |
| --- | --- | --- | --- |
| **Qwen3-4B** acc TB | 97,26 (`exp002`) | **97,77** (`exp003`) | 97,19 (`exp004`) |
| **Qwen3-4B** số ô | 2.415 | 2.315 | 2.378 |
| **Qwen3-4B** F1 âm macro | 0,806 | **0,872** | 0,820 |
| **Qwen3-0.6B** acc TB | **KHÔNG đọc được** | **KHÔNG đọc được** | **KHÔNG đọc được** |

**Vì sao ô của 0,6B để trống: cả ba lượt đều DƯỚI CỬA đọc được** (21,63 - 84,41%), nên mọi con số `paper` của
chúng là số tính trên **một phần rất nhỏ** của tập và **không so được** với 4B. Đây **không phải thiếu thí nghiệm** -
**đó chính là kết quả**. (Cũng vì thế không có bảng accuracy/PRF theo khía cạnh cho 0,6B: mẫu số không còn là tập
test nữa.)

### M8.3 Bảng "cơ chế hỏng": hai model nhỏ hỏng HAI KIỂU khác nhau

| Model / cách hỏi | Hỏng ở đâu | Bằng chứng |
| --- | --- | --- |
| **Qwen3-0.6B** (0/1/5 ví dụ) | **ĐỊNH DẠNG ĐẦU RA** - không in khối JSON | `% đọc được` 42,02 / 21,63 / 84,41 |
| **Qwen3-0.6B** (một lượt, bỏ suy luận) | **KIÊNG TRẢ LỜI** (định dạng đã ổn) | đọc **99,94%** nhưng chỉ **877 ô** và F1 âm **0,211**; 283 mẫu thiếu khía cạnh |
| **Qwen3-0.6B** (bật suy nghĩ, trần 1.985) | **PHÁ PHÁT HIỆN KHIẾN CẠNH** | detection F1 **0,479** (nhánh TẮT suy nghĩ cùng model: 0,86-0,91); `stayingpower` acc 70,09 |
| **Qwen2.5-0.5B** (họ KHÁC, 0/1/5 ví dụ) | **KIÊNG TRẢ LỜI**, định dạng ỔN | đọc **95,81 / 97,29 / 100,0** nhưng **73,4 / 82,1 / 78,6%** review bị gán mã 0 cho MỌI khía cạnh; số ô `paper` chỉ **464 / 256 / 239** (4B: 2.315-2.580) ⇒ F1 âm sụp về **0,000** ở mức 5 ví dụ |

### M8.4 Kết luận

1. **Qwen3-0.6B không dùng được cho nhiệm vụ này ở CẢ BA cách hỏi** (0/1/5 ví dụ · một lượt · bật suy nghĩ) - mỗi
   cách hỏng một kiểu, và **cả ba đều đo được**, không phải phỏng đoán.
2. **"Nhỏ thì kém" lặp lại ở họ KHÁC** (Qwen2.5-0.5B, thế hệ `qwen2`) nhưng **cơ chế hỏng khác**: 0,5B **đọc được**
   (≥95%) mà **kiêng trả lời**; 0,6B thì **không đọc nổi** ở ba lượt gốc. Cùng kết luận, hai nguyên nhân, hai cách
   sửa khác nhau.
3. Vì vậy **Qwen3-4B là LLM tốt nhất hiện tại của dự án**, và điều đó **không** phải do 0,6B "thiếu may mắn": lượt
   DÒ chốt trần token chứng minh lỗi **không** nằm ở trần token, và lượt một-lượt chứng minh lỗi **không** nằm ở định
   dạng - mà ở CHÍNH model.
4. **Luật đọc số quan trọng nhất của cả báo cáo nằm ở mục này**: điểm của model nhỏ **không so được** khi số ô tụt -
   phải đọc kèm **số ô** (luật 1 của `metrics.md`).

## M9. LLM LỚN HƠN & KHÁC HỌ - **CHỜ KẾT QUẢ** (Đ6/Đ7, 14 lượt)

| Nhóm | Model | Số lượt | Trạng thái |
| --- | --- | --- | --- |
| Cùng họ, LỚN hơn | `qwen3-8b` (4-bit) | 3 (0/1/5 ví dụ) | đã tạo + ghim, chờ chạy |
| Cùng cỡ, khác CHẾ ĐỘ | `qwen3-4b-thinking-2507` | 1 DÒ + 1 chạy (1 ví dụ) | đã tạo + ghim, chờ chạy |
| Khác họ | `mistral-7b-instruct-v0.3` | 3 (0/1/5 ví dụ) | đã tạo + ghim, chờ chạy |
| Khác họ | `llama-3.1-8b-instruct` | 3 | **CHẶN: repo GATED** (cần `HF_TOKEN` + nhận điều khoản) |
| Tiếng Việt chuyên biệt | `vistral-7b-chat` | 3 | **CHẶN: repo GATED** (như trên) |

Vì sao "khác họ" quan trọng: nếu Qwen3-4B/8B và một họ hoàn toàn khác (Mistral, chat template `[INST]`,
tokenizer Llama-BPE) đều cho CÙNG kết luận về mức ví dụ và cách hỏi, thì kết luận không còn là chuyện riêng
của một họ model. `qwen3-4b-thinking-2507` là lượt trả lời trực tiếp bài học 0.6B: model bật suy nghĩ ăn hết
trần token rồi không in JSON - nên **lượt DÒ (`exp001`, 60 mẫu, trần 8.192) phải chạy TRƯỚC**, rồi trần của
lượt chạy (`exp002`) cập nhật theo công thức `làm tròn lên (p99 × 1,5)`.

Luật đọc: mọi lượt 4-bit **in kèm SỐ Ô** - bản 4-bit trả lời ít hơn **5-6%** số ô, và trên cặp Qwen3-4B 5-shot đã có
ca **đảo chiều** khi đổi cơ sở đo (xem §4.3 của `present_report.md`).

## M10. Điều kiện SO CÔNG BẰNG với công bố - **ĐÃ ĐỦ**

Tám điều kiện đang được áp. Nhìn vào chúng là biết phép so có công bằng hay không:

1. **Cùng tập test**: `test` = **1.623 review**, và pipeline **không sửa `test`** - mọi bước biến đổi văn bản chỉ
   khai `apply_to: [train, val]`, nên văn bản `test` **giống từng ký tự** bản gốc.
2. **Khoá tập đánh giá**: `data/processed/<mã>/eval_lock.json` ghi vân tay **tập bản ghi** của `test`; lệch là **LỖI**
   (không phải cảnh báo), nên `test` không thể bị đổi giữa các lượt.
3. **Đo đúng cách công bố**: cơ sở `paper` = chỉ giữ ô mà **CẢ** nhãn đúng **VÀ** nhãn đoán là positive/negative.
4. **Cùng bài toán**: 7 khía cạnh; `others` bị loại ở schema; `neutral` bị loại (`neutral_policy: drop`); "có nhắc tới
   hay không" là **quyết định riêng** (`not_mentioned: separate`).
5. **So đúng mức ví dụ**: mỗi lượt được so với cột công bố **cùng mức shot** của chính nó (0/1/5).
6. **Luôn đọc kèm SỐ Ô**, cộng **cửa đọc được ≥ 95%** (`read_rate.valid`), và **luật cắt**: nếu số token sinh trung
   bình ≥ 95% trần thì lượt đó coi là **bị cắt** và phải chạy lại với trần cao hơn.
7. **Biên nhiễu ±0,7 điểm** (đo từ ba lượt `seed 7`): chênh lệch **dưới mức đó không kết luận**.
8. **Tái lập được**: sinh `greedy` (tất định) + mã băm danh tính gồm **config + prompt + ví dụ + khối hệ thống +
   phiên bản dữ liệu + commit đã ghim** ⇒ cùng phép đo ra cùng thư mục kết quả trên mọi máy.

## Nguồn số

- Lượt chạy: `experiments/**/results/<hash8>/metrics.json` (cơ sở `paper`; mục nào ghi rõ `all` thì đọc theo `all`).
- Số emoji: đo trên `data/raw/cosmetics/v0.1.0/data_{train,val,test}.csv` bằng `utils.has_emoji` / `utils.count_emoji`
  (cùng định nghĩa với EDA 03).
- Cặp đầu phân loại, thước nhiễu, nhánh 0,6B/0,5B: `docs/04_experiments/06_lora_encoder.md` và
  `docs/04_experiments/08_experiment_rationale.md`.



## Cập nhật 10/10/2026 - bốn lỗi nhỏ tìm ra khi chạy smoke

- Bốn bản sửa (kèm test) đã vào `e2bfefd`, `4606df7`, `09598eb`, `9a50b92`; cờ `--smoke`/`--epochs` vào
  `31da713`; tài liệu vào `2c55487`. Chi tiết + bằng chứng ở `present_plan_batch11.md` §9.
- **KHÔNG ảnh hưởng số trong báo cáo này**: cả bốn đều là lỗi CHỮ NGHĨA / ĐƯỜNG CHẠY (nhãn in sai, thiếu
  cảnh báo khi bị đè model, mất phần ghi nhận DagsHub, ô cuối ném `NameError`) - không lỗi nào đổi cách
  chấm điểm. Ba lượt smoke chạy trên bản code TRƯỚC khi sửa cũng chỉ để xác nhận ống dẫn, và nằm ở thư mục
  kết quả riêng (`subset.limit: 8` ghi rõ trong `metrics.json` của chúng).

