# present_report_v5 - Đối chiếu dự án với công bố tham chiếu (10 lượt dẫn đầu: 9 encoder + 1 LLM)

> **BẢN MỚI NHẤT - thay thế `present_report_v4.md`, `present_report_v3.md`, `present_report_v2.md`,
> `present_report_v1.md` và `present_report_v0.md`.** Bảng 10 cột ở đây lấy **10 lượt dẫn đầu trong 80 lượt ĐỦ
> ĐIỀU KIỆN**, sau khi áp **ba quy tắc của dòng báo cáo này**: (a) **loại mọi lượt chỉ đổi `decoding.seed`** so với cha
> (dò nhiễu, không phải model/method mới); (b) **chỉ nhận lượt KIỂM ĐƯỢC overfit** - lượt phải có **lịch sử huấn luyện
> theo epoch** và **không dính mẫu overfit** theo định nghĩa ở mục 2.2; (c) **so `decoding.seed` theo GIÁ TRỊ HIỆU LỰC**
> (khoá vắng mặt = **mặc định 42**). **Quy tắc (c) là điểm khác DUY NHẤT so với `present_report_v4.md`**, và nó **đưa
> `cafebert/lora/exp055` vào bảng ở hạng 7** (xem mục 0 và 8.1).

> Đọc file này khi: trình bày kết quả dự án so với công bố tham chiếu, hoặc chọn model để báo cáo.
> **Nguồn số của DỰ ÁN: `experiments/**/results/<hash8>/metrics.json` khoá `scores_paper` (và `mispredictions.csv`)
> của CHÍNH từng lượt - KHÔNG lấy từ `data/reports/**`, KHÔNG lấy từ bất kỳ file tài liệu nào.**
> **Nguồn số của CÔNG BỐ: `data/reference_publication/*.csv`.**

> ⛔ **GHI CHÚ 16/10/2026 - HAI LƯỢT TRONG BẢNG ĐÃ BỊ THAY; BẢNG NÀY KHÔNG CÒN LÀ BẢN ĐANG DÙNG.**
> `cafebert/lora/exp027` và `cafebert/lora/exp073` đã được **chạy lại liền mạch**. Bản trong file này bị ngắt giữa
> phiên rồi chạy tiếp từ checkpoint, nên `training_history.csv` chỉ còn các epoch cuối - đúng như chính mục 2.2
> của file này đã ghi ("cửa sổ bị cắt"). Số cũ → số mới: `exp027` **98,37 → 98,56**; `exp073` **98,52 → 98,31**.
> **Hai bản cũ bị bỏ**, không dùng để báo cáo (giữ trong `_scratch/replaced/`).
> Ngoài ra bản này áp luật overfit bằng cách đếm **tổng** số lần `val_loss` tăng nên loại `exp064`, trong khi câu chữ
> ở mục 2.2 ghi "tăng **liên tiếp**"; đọc đúng câu chữ thì `exp064` **không** overfit và phải có mặt trong bảng.
> **Bảng đang dùng: [`present_report_v6.md`](present_report_v6.md).**

> **Hai lỗi nữa của bản này (ghi để không lặp lại).** Mục 2.2 gán nhãn **UNDERFIT** cho `exp015`, `exp021`, `exp055`
> — **sai**: theo đúng định nghĩa "ở lần đo cuối, **cả** `train_loss` **và** `val_loss` vẫn còn giảm", thì
> `train_loss` của cả ba lượt đều **TĂNG** ở mốc cuối (`exp015` 0,0522 → 0,0613; `exp021`/`exp055` 0,0364 → 0,0605)
> ⇒ đúng ra là **"không kết luận được"**. Con số đúng cho 9 cột của v6 là
> **0 overfit · 6 `val_loss` còn giảm ở mốc cuối · 3 không kết luận**.
> Và câu "**7/9 lượt UNDERFIT (còn dư địa nếu tăng số epoch)**" là **hứa quá**: đòn "tăng số epoch" đã **thử và ĐÓNG**
> ở Đợt 13.1/13.2 — `val_loss` còn giảm **không** đồng nghĩa còn điểm để lấy. Chi tiết: `present_report_v6.md` mục 1.

## 0. Bản này khác `present_report_v4.md` ở đâu

| Hạng mục | `present_report_v4.md` | `present_report_v5.md` (bản này) |
| --- | --- | --- |
| Cách đếm điều kiện 10/11 (seed) | so **sự có mặt** của khoá `decoding.seed` | **so GIÁ TRỊ HIỆU LỰC**: khoá vắng mặt = **42** (`experiment_run.SEED_DEFAULT`) ⇒ lượt **khai lại đúng 42** KHÔNG bị coi là "đổi seed" |
| Số lượt Tier B | **9** - gồm `exp055` bị **liệt OAN** | **8** = `exp056`/`exp057` (`best_metric`+seed), `exp091`/`exp092`/`exp093` (nhánh R + seed), `prompt-cot/exp025`/`exp026`/`exp027` (`decoding.mode`+seed) |
| Số lượt đủ điều kiện / kết quả phân biệt | **79** / **75** (**51** encoder + 24 LLM) | **80** / **76** (**52** encoder + 24 LLM) |
| 9 lượt encoder | `exp073` · `exp021` · `exp027` · `exp015` · `exp020` · `exp013` · `exp017` · `exp008` · `exp019` | **`exp073` · `exp021` · `exp027` · `exp015` · `exp020` · `exp013` · `exp055` · `exp017` · `exp008`** (E7 = `exp055` thay `exp019`; `exp019` 97,99 xuống **hạng 10 của pool** ⇒ bị **điều kiện 9** thay bằng cột LLM) |
| Lượt LLM | `qwen3-4b-instruct-2507/prompt-cot/exp009` | **không đổi** (`exp009`) - vẫn là lượt LLM tốt nhất toàn dự án (97,77) |
| Accuracy macro của 9 cột encoder | 97,99 … 98,52 (Δ so mốc 97,70 = +0,29 … +0,82) | **98,03 … 98,52** (Δ **+0,33 … +0,82**) |
| `neg F1 macro (5 khía cạnh n lớn)` | 92,96 … 94,90 (Δ so mốc 87,88 = +5,08 … +7,02) | **93,66 … 94,90** (Δ **+5,78 … +7,02**) |
| `neg P macro (5 khía cạnh n lớn)` | 90,16 … 94,72 | **90,40 … 94,72** |
| Ba nhánh PHỤ của bảng | `E7` (`focal`) · `E8` (`vncorenlp`) · `E9` (DoRA) | **`E7` (thước chọn mốc `negative_f1`) · `E8` (`focal`) · `E9` (`vncorenlp`)** |
| 42 ô P/R/F1 · chẩn đoán hội tụ | 14 thua hết · 17 thắng hết · 11 hỗn hợp · 7/9 UNDERFIT · 0 overfit | **không đổi** (đổi cột, KHÔNG đổi kết luận) |
| Nguồn số | `experiments/**/results/<hash8>/metrics.json` + `data/reference_publication/*.csv` | **không đổi** |

> **`present_report_v4.md` nay là file ghi-chú-chuyển-hướng** (nó **chưa từng được commit vào git** - xem ghi chú ở
> đầu file đó). Chuỗi phiên bản đọc được: `v0` → `v1` → `v2` → `v3` → `v4` → **`v5` (bản này)**.

## 1. Quy ước đọc số

- **Cơ sở đo "paper"**: mỗi ô (review × khía cạnh) chỉ được tính khi **cả** ground truth **và** predict đều là
  `positive` hoặc `negative`. Đây là cách công bố đếm, và là cơ sở của MỌI số trong file này.
- **Tập đánh giá**: 1.623 review của tập `test` (tập test công khai của bài nguồn, giữ nguyên từng ký tự; khoá tập
  đánh giá `records_sha256 = 73d39d84…`). Mọi lượt trong bảng đều `n_samples = 1623`, `split = test`,
  `label_space: binary`, `neutral_policy: drop`, `not_mentioned: separate`, **% đọc được = 100,00**.
- **Đơn vị**: mọi chỉ số ghi theo **%**, dùng **dấu phẩy thập phân** (98,52). Chênh lệch dùng **điểm phần trăm (pp)**.
- **Mốc đối chiếu** (dùng cho mọi bảng delta): **mức COT+1-shot của công bố** - mức có **Accuracy macro cao nhất**
  trong ba mức 0/1/5-shot (97,70 so với 97,36 và 96,74). Xem bảng ở mục 4.
- **Δ** = số của lượt − mốc đối chiếu ở **đúng ô đó** (dòng `MACRO` thì so với chính dòng `MACRO` của mốc).
  **Δ dương = vượt công bố.** Delta được tính từ **hai số ĐÃ HIỂN THỊ** nên đọc lại bằng phép trừ là khớp.
- **`n`** = số ô **ground truth** của cặp (khía cạnh × sắc thái). Số này **cố định** cho mọi cột.
- **Số ô THẬT SỰ được tính** của mỗi lượt thì **KHÁC nhau** (2.724 … 2.748 ở đường encoder; **2.324** ở L1):
  mẫu số của cơ sở `paper` phụ thuộc cả nhãn **đoán**, nên lượt nào trả lời "neutral / không nhắc tới" nhiều hơn
  thì mẫu số nhỏ hơn. Vì vậy **không so tuyệt đối** hai lượt nếu bỏ qua cột số ô (mục 9.3).
- **Cả 9 lượt encoder đều ở seed HIỆU LỰC 42**: 8 lượt **không khai** `decoding.seed` (⇒ mặc định **42**,
  `src/experiments/experiment_run.py::SEED_DEFAULT`), **E7 `exp055` khai tường minh 42**. Khai hay không khai là
  **cùng một giá trị**, nên bảng vẫn là **so sánh MỘT BIẾN**: mỗi cột khác cha đúng **một đòn**, seed giữ nguyên ở mọi cột.
- **Encoder không có khái niệm số ví dụ** nên được đối chiếu với **cả ba** mức của công bố; lượt LLM đối chiếu với
  **đúng mức số ví dụ của chính nó** (LLM ở đây ở mức 1-shot, trùng mốc).
- **Biên nhiễu của đường encoder đã đo = ±0,33 … ±0,67 điểm** (đo trên các lượt chạy lại cùng cấu hình, khác seed);
  lấy mức làm việc **±0,7** - chênh lệch nhỏ hơn mức đó **KHÔNG kết luận**. Kèm cảnh báo của luật 10: **thứ hạng
  E1…E9 không phải thứ hạng cấu hình** (mục 8).
- **Hai thước đo lớp negative** (vì `price` chỉ có 6 ô và `packing` 10 ô ground truth, quá ít để đọc riêng):
  - **`neg F1 macro (5 khía cạnh n lớn)`** = trung bình F1 lớp negative trên 5 khía cạnh **`colour` · `shipping` ·
    `smell` · `stayingpower` · `texture`** (54 · 174 · 48 · 96 · 83 ô âm).
  - **`neg F1 micro (theo n)`** = trung bình F1 lớp negative **có trọng số bằng số ô ground truth của từng khía
    cạnh** (`smell 48 · price 6 · texture 83 · colour 54 · stayingpower 96 · packing 10 · shipping 174`, tổng 471).
    Trọng số **giống nhau ở mọi cột** (kể cả 3 cột công bố) nên các cột so ngang được; `shipping` (174 ô) nặng gấp
    29 lần `price` (6 ô) nên **không thể "ăn điểm" bằng 1-2 ô**.
  - **Bảng Precision và bảng Recall cũng có hai dòng cùng công thức nhưng tính trên chính chỉ số của bảng đó.**

## 2. Điều kiện lọt bảng và chẩn đoán chất lượng lượt chạy

### 2.1. Điều kiện để một lượt được vào bảng

| # | Điều kiện | Cách kiểm (đã kiểm cho từng lượt) |
| --- | --- | --- |
| 1 | **Cùng tập đánh giá**: tập `test` phải là đúng tập test công khai của bài nguồn, 1.623 review | khoá tập đánh giá của phiên bản dữ liệu: vân tay **tập bản ghi** `73d39d84…` (khoá, lệch là lỗi) và vân tay **byte** `af349bf5…` (lệch chỉ là ghi chú) |
| 2 | **Cùng bài toán**: chỉ hai sắc thái `positive`/`negative`, ô `neutral` bị loại khỏi phần chấm | `label_space: binary`, `neutral_policy: drop`, `not_mentioned: separate` của từng lượt |
| 3 | **Chấm trọn tập**: cả 1.623 review, không chạy tập con, không chấm trên `val` | `n_samples = 1623` và `split = test` |
| 4 | **Đọc được kết quả**: tỉ lệ đọc được **≥ 95 %** | `read_rate` của lượt (cả 10 lượt trong bảng đều **100,00 %**) |
| 5 | **KHÔNG overfit** (định nghĩa ở mục 2.2) | đường cong huấn luyện theo epoch của lượt |
| 6 | **PHẢI KIỂM ĐƯỢC overfit** - lượt phải có **lịch sử huấn luyện theo epoch** (≥ 3 mốc đo `val_loss`). **Điều kiện MỚI của bản này.** Lượt chỉ có 1-2 mốc, hoặc lịch sử rỗng, thì **không có gì để kiểm** ⇒ loại; lượt KHÔNG huấn luyện (đường prompt/LLM) được **miễn** vì không thể overfit | `training_history.csv` của lượt: số dòng `kind=epoch` và các cột `train_loss`/`val_loss` |
| 7 | **Không trùng lặp**: hai lượt cho ra **cùng bộ 7 số Accuracy** coi là MỘT kết quả | so từng khía cạnh |
| 8 | **Xếp hạng theo Accuracy macro** (cơ sở `paper`), giảm dần | 7 số Accuracy của lượt |
| 9 | **Có ít nhất 1 lượt LLM trong 10 cột**: nếu không lượt LLM nào lọt top 10 thì **bỏ lượt encoder thứ 10**, thay bằng lượt LLM tốt nhất | danh sách xếp hạng |
| 10 | **KHÔNG phải lượt chỉ đổi `decoding.seed`** - **điều kiện MỚI của bản này**: lượt chỉ khác cha **đúng một khoá `decoding.seed`** là **dò nhiễu**, không phải model/method mới | diff **cấu hình đã hợp nhất** (7 lớp, hàm `src/experiments/experiments.py::load`) giữa con và cha, **so theo GIÁ TRỊ HIỆU LỰC**: `decoding.seed` vắng mặt = **42** (`src/experiments/experiment_run.py::SEED_DEFAULT`) ⇒ **khai lại 42 không phải là đổi seed**; trên đường encoder `decoding.seed` **chính là hạt giống huấn luyện** (`src/training/lora.py:940-943` seed `random`/`torch`/`cuda`, `:1001-1002` seed cho `shuffle=True`) |
| 11 | **KHÔNG trộn seed với khoá khác** (nhóm "Tier B"): lượt vừa đổi `decoding.seed` **vừa** đổi thứ khác thì không tách được tác dụng của biến nào | cùng phép diff ở điều kiện 10 - **vẫn so theo giá trị hiệu lực**: nhóm Tier B của bản này = `exp056`/`exp057` (`best_metric`+seed), `exp091`/`exp092`/`exp093` (nhánh R + seed), `prompt-cot/exp025`/`exp026`/`exp027` (`decoding.mode`+seed) |

> **Vì sao phải so GIÁ TRỊ HIỆU LỰC chứ không so SỰ CÓ MẶT của khoá:** `decoding.seed` vắng mặt **nghĩa là 42**, nên
> lượt nào **ghi lại đúng 42** (ví dụ `exp055`) không phải lượt dò nhiễu. Bản dựng trước đếm theo *sự có mặt* nên đã
> **liệt oan `exp055` vào Tier B**; đếm lại theo giá trị hiệu lực: **43 lượt** chỉ-đổi-seed (không đổi) và **8 lượt**
> Tier B (thay vì 9) ⇒ `exp055` được xếp hạng và **vào bảng ở hạng 7**.

**Kết quả áp dụng cho bản này** (đếm lại trên cây làm việc, 16/10/2026):

| Bước | Còn lại | Ghi chú |
| --- | ---: | --- |
| Tổng lượt có bản ghi trên đĩa | **174** | = số dòng `experiment_registry.csv` |
| Loại ở cửa 1-2-3-4 | 144 | loại **30** lượt = **13** chấm trên `val` + **9** có `% đọc được < 95` (`mistral-7b` 60,38 · 72,15 · 63,46; `qwen3-0.6b` 42,02 · 21,63 · 84,41; `qwen3-8b` 1,05 · 0,92 · 0,12) + **8** lượt chỉ chấm **một khía cạnh** (`prompt-aspect/exp001…007`, `prompt-cot/exp016`) |
| Chốt phiên bản dữ liệu | **141** | 3 lượt còn lại chạy trên `v0.3.0` (`test` y đúc nên vẫn so được, nhưng để nhất quán bảng chỉ lấy phiên bản `v0.2.0`) |
| Loại ở cửa 10 (**chỉ đổi seed hiệu lực**) | **98** | **43 lượt** - gồm 7 lượt `exp074/075/079/080/082/086/090` của Đợt 13.2, `exp072`, `exp084`, `exp040`, `exp045/047`, `exp058`, `exp004`… |
| Loại ở cửa 11 (**Tier B**) | **90** | **8 lượt** = **5 encoder** `exp056`/`exp057` (`best_metric`+seed), `exp091`/`exp092`/`exp093` (nhánh R + seed) + **3 lượt LLM** `prompt-cot/exp025`/`exp026`/`exp027` (`decoding.mode`+seed). *(Bản dựng trước đếm **9** vì xếp `exp055` vào đây theo **sự có mặt** của khoá `decoding.seed`; xem ghi chú ở bảng điều kiện.)* |
| Loại ở cửa 5 (**OVERFIT**) | **89** | **1 lượt**: `cafebert/lora/exp064` (đòn `epochs 3→15` + bật dừng sớm; `val_loss` tăng liên tiếp khi `train_loss` vẫn giảm) |
| Loại ở cửa 6 (**không kiểm được overfit**) | **80** | **9 lượt** = **6** lượt lịch sử **rỗng** (`exp012`, `cafebert/none/exp001`, `phobert-base-v2/full/exp001-002`, `phobert-base-v2/lora/exp017`, `phobert-base-v2/none/exp001`) + **3** lượt chỉ có **1-2 mốc epoch** (`exp028` 1 mốc, `exp030` 1 mốc, `exp033` 2 mốc) |
| Gộp trùng (cửa 7) | **76 kết quả phân biệt** | **52 encoder** + **24 lượt LLM**; cặp trùng đã gặp: `exp045`=`exp047`, `exp082`=`exp088` (cả hai đã bị loại ở cửa 10) |
| Bảng cuối (cửa 8 + 9) | **9 encoder + 1 LLM** | 9 lượt encoder: 98,52 … 98,03; lượt LLM tốt nhất `qwen3-4b-instruct-2507/prompt-cot/exp009` **97,77** ⇒ thay cho **lượt encoder hạng 10 của pool** (`exp019`, 97,99) |

> **Lưu ý về điều kiện 9:** lượt encoder hạng 10 của pool (`exp019`, 97,99) và các lượt kế tiếp (`exp010` 97,95,
> `exp018` 97,93, `exp067` 97,90) đều **cao hơn** lượt LLM tốt nhất (97,77) ⇒ **cột L1 có mặt vì LUẬT, không vì
> chất lượng**. Mọi so sánh "LLM ngang encoder" phải đọc kèm ghi chú này.

### 2.2. Chẩn đoán hội tụ (overfit / underfit) - và vì sao đây là **điều kiện lọt bảng**

**Phương pháp** (cách đọc đường cong huấn luyện tiêu chuẩn: chẩn đoán dựa trên **cặp** đường cong train ↔ validation,
không dựa trên một con số của epoch cuối):

- **Dữ liệu**: các mốc đo trong `results/<hash8>/training_history.csv` - `train_loss` và `val_loss` ghi ở **mỗi epoch**.
- **OVERFIT** = `val_loss` **tăng liên tiếp ≥ 2 lần đo** trong khi `train_loss` **vẫn giảm**.
- **UNDERFIT** = ở lần đo cuối, **cả** `train_loss` **và** `val_loss` **vẫn còn giảm**.
- **Không kết luận được** = không rơi vào hai mẫu trên (ví dụ `val_loss` tăng đúng 1 lần ở mốc cuối).

| Lượt | epoch đọc được | train_loss | val_loss | **Kết luận** |
| --- | --- | --- | --- | --- |
| `exp073` [E1] | 9 → 12 *(cửa sổ bị cắt - chạy tiếp từ epoch 8)* | 0,0695 → 0,0079 → 0,0097 → 0,0014 | 0,0934 → 0,0915 → **0,0909** → 0,0912 | **không kết luận được** (val tăng đúng 1 lần, ở mốc cuối) |
| `exp021` [E2] | 1 → 3 | 0,1678 → 0,0364 → 0,0605 | 0,1325 → 0,0882 → **0,0857** | **UNDERFIT** |
| `exp027` [E3] | 3 → 6 *(cửa sổ bị cắt - chạy tiếp từ epoch 2)* | 0,0864 → 0,0348 → 0,0249 → 0,0104 | 0,1004 → 0,0831 → **0,0812** → 0,0822 | **không kết luận được** (val tăng đúng 1 lần, ở mốc cuối) |
| `exp015` [E4] | 1 → 3 | 0,1666 → 0,0522 → 0,0613 | 0,1273 → 0,0946 → **0,0837** | **UNDERFIT** |
| `exp020` [E5] | 1 → 3 | 0,1533 → 0,1120 → 0,0528 | 0,1521 → 0,0994 → **0,0842** | **UNDERFIT** |
| `exp013` [E6] | 1 → 3 | 0,2063 → 0,0968 → 0,0686 | 0,1351 → 0,1007 → **0,0866** | **UNDERFIT** |
| `exp055` [E7] | 1 → 3 *(trùng khớp từng chữ số với `exp021` - xem ghi chú dưới bảng)* | 0,1678 → 0,0364 → 0,0605 | 0,1325 → 0,0882 → **0,0857** | **UNDERFIT** |
| `exp017` [E8] | 1 → 3 | 0,0459 → 0,0143 → 0,0128 | 0,1615 → 0,1429 → **0,1245** | **UNDERFIT** |
| `exp008` [E9] | 1 → 3 | 0,1894 → 0,0990 → 0,0604 | 0,1578 → 0,0990 → **0,0936** | **UNDERFIT** |
| `L1` (LLM) | không huấn luyện | — | — | **không áp dụng** |

**Đọc mục 2.2:**

- **0/9 lượt overfit** - đúng như yêu cầu của điều kiện 5; **7/9 lượt UNDERFIT** (còn dư địa nếu tăng số epoch);
  **2/9 lượt không kết luận được** (`exp073`, `exp027` - val tăng đúng 1 lần ở mốc cuối, không đủ thành mẫu overfit).
- **Cả 9 lượt đều thoả điều kiện 6** (có ≥ 3 mốc đo `val_loss`), nhưng **`exp073` và `exp027` có cửa sổ epoch bị cắt**:
  file lịch sử chỉ còn các epoch của **tiến trình cuối** (`exp073`: 9-12; `exp027`: 3-6), vì phiên Colab bị ngắt rồi
  **chạy tiếp từ checkpoint** và `encoder_run.py:524` ghi **cả file một lần từ danh sách trong bộ nhớ của tiến trình
  hiện tại**. Hai lượt này vì thế **đủ để kiểm mẫu overfit**, nhưng **không** có toàn bộ đường cong.
- **Vì sao đây là điều kiện lọt bảng, không chỉ là ghi chú:** lượt không có lịch sử theo epoch thì **không có gì để
  kiểm** - nên dự án **loại** chúng thay vì nhận vào rồi ghi chú. Cụ thể bản này loại **9** lượt vì lý do đó:
  `exp012` + 5 lượt SÀN/full (lịch sử rỗng) và `exp028`, `exp030`, `exp033` (chỉ 1-2 mốc).
- **Ba lượt bị loại vì lịch sử bị cắt - ghi rõ để người sau chạy lại:** `exp028` và `exp030` **đã chạy đủ 3 epoch**
  (`settings.epochs: 3`, `step: 1150`, log `huấn luyện xong: 1150 bước`) và đạt 98,31 / 98,25 - **điểm tốt hơn 3 cột
  của bảng này** - nhưng `training_history.csv` của chúng **chỉ còn 1 dòng `epoch`** (epoch 3) do cùng cơ chế chạy
  tiếp ở trên, nên **không kiểm được overfit** ⇒ bị loại ở **điều kiện 6**. Muốn đưa chúng vào bảng thì phải **xoá
  thư mục kết quả và chạy lại liền mạch** (lưu ý: chạy lại sẽ ra số hơi khác, vì `decoding.seed` seed cả thứ tự
  xáo trộn dữ liệu và generator được **tạo mới ở mỗi tiến trình** - `lora.py:1001-1002`).

- **`exp055` [E7] dùng CHÍNH lần huấn luyện của `exp021` [E2]:** hai lượt có **siêu tham số giống nhau** và **cùng
  seed hiệu lực 42**, nên **đường `train_loss`/`val_loss` trùng khớp từng chữ số** (`0,167829 → 0,036372 → 0,060476`
  và `0,132467 → 0,088233 → 0,085669`) - chúng khác nhau **đúng ở thước CHỌN MỐC** (`sentiment_f1` so với
  `negative_f1`). Đây **không phải hai model khác nhau**: đọc E2 ↔ E7 là **so hai cách chọn mốc trên cùng một lần
  huấn luyện** (mục 2.4 B, 8.1).

### 2.3. Chất lượng mốc chọn model - việc RIÊNG, không gọi là overfit

Phương pháp chọn model của dự án là lấy mốc có **chỉ số val tốt nhất** (đúng cách làm tiêu chuẩn, không phải lỗi).
Nguồn: `model/best/trainer_state.json` (khoá `epoch`, `step`) đối chiếu `training_history.csv`.

| Lượt | epoch của mốc được chọn | epoch có `val_loss` đáy | Vị trí |
| --- | ---: | ---: | --- |
| `exp073` [E1] | 10 (bước 3.700) | 11 *(theo cửa sổ đọc được)* | **trước đáy** 1 epoch |
| `exp021` [E2] | 3 (bước 900) | 3 | **đúng tại đáy** |
| `exp027` [E3] | 4 (bước 1.200) | 5 *(theo cửa sổ đọc được)* | **trước đáy** 1 epoch |
| `exp015` [E4] | 3 (bước 1.150) | 3 | **đúng tại đáy** |
| `exp020` [E5] | 3 (bước 1.150) | 3 | **đúng tại đáy** |
| `exp013` [E6] | 3 (bước 900) | 3 | **đúng tại đáy** |
| `exp055` [E7] | 3 (bước 1.150) | 3 | **đúng tại đáy** |
| `exp017` [E8] | 3 (bước 1.150) | 3 | **đúng tại đáy** |
| `exp008` [E9] | 3 (bước 1.150) | 3 | **đúng tại đáy** |
| `L1` (LLM) | không huấn luyện | không huấn luyện | không áp dụng |

**Đọc mục 2.3:** **7/9 lượt lấy mốc đúng tại đáy** `val_loss`; hai lượt còn lại lấy mốc **trước đáy 1 epoch** và
**không lượt nào bị loại ở mục này** (thuần là **cảnh báo chất lượng**).

### 2.4. Bảng tra nhãn cột

**A. Cấu hình DÙNG CHUNG cho 9 lượt encoder** (chỉ nêu cái chung; cái riêng ghi ở bảng B):

| Hạng mục | Giá trị dùng chung |
| --- | --- |
| Model nền | **CafeBERT**, adapter LoRA trên 4 module `query` · `key` · `value` · `dense` |
| Đầu phân loại | **HỌC** cùng adapter (`head.trainable: true`) |
| Hàm mất mát | `weighted_ce` + `class_weight: inverse` - trừ **E8** (`focal`) |
| Hệ số LoRA | `alpha` 32, `dropout` 0,05; `r` = 16 - trừ **E2**/**E7** (`r` 8) và **E5**/**E6** (`r` 32) |
| Số epoch | 3 - trừ **E1** (15 + dừng sớm) và **E3** (6) |
| Tốc độ học | 4e-4 (**E1-E5**, **E7**) hoặc 2e-4 (**E6**, **E8**/**E9**) |
| Độ dài input tối đa | 256 token |
| Bộ tách từ | `none` - trừ **E9** (`vncorenlp`) |
| Chỉ số chọn mốc model tốt nhất | `sentiment_f1` trên `val` - trừ **E1** (`neg_f1_big5`) và **E7** (`negative_f1`) |
| Số review mỗi lô khi suy luận | 16 |
| Hạt giống | **42 ở CẢ 9 lượt**: **8 lượt không khai** `decoding.seed` (⇒ mặc định 42, `experiment_run.SEED_DEFAULT`), **E7 khai tường minh 42** ⇒ **seed HIỆU LỰC giống nhau ở cả 9 lượt** |

**B. Từng lượt - ĐÒN THAY ĐỔI so với cha** (diff **cấu hình đã hợp nhất**, đã bỏ khoá mô tả; cột cuối là `seed` hiệu lực):

| Nhãn | Lượt | Cha | Khoá khác cha (đã bỏ khoá mô tả) | seed |
| --- | --- | --- | --- | ---: |
| E1 | `cafebert/lora/exp073` | `cafebert/lora/exp064` | `checkpoints.best_metric` | 42 |
| E2 | `cafebert/lora/exp021` | `cafebert/lora/exp015` | `lora.r` | 42 |
| E3 | `cafebert/lora/exp027` | `cafebert/lora/exp015` | `epochs` | 42 |
| E4 | `cafebert/lora/exp015` | `cafebert/lora/exp002` | `lr` | 42 |
| E5 | `cafebert/lora/exp020` | `cafebert/lora/exp015` | `lora.r` | 42 |
| E6 | `cafebert/lora/exp013` | `cafebert/lora/exp002` | `lora.r` | 42 |
| E7 | `cafebert/lora/exp055` | `cafebert/lora/exp021` | `checkpoints.best_metric` | 42 |
| E8 | `cafebert/lora/exp017` | `cafebert/lora/exp002` | `loss.class_weight`, `loss.gamma`, `loss.type` | 42 |
| E9 | `cafebert/lora/exp008` | `cafebert/lora/exp002` | `preprocess.segmenter` | 42 |
| L1 | `qwen3-4b-instruct-2507/prompt-cot/exp009` | `qwen3-4b-instruct-2507/prompt-cot/exp003` | `inference.batch_size`, `inference.dtype` | 42 |


**Đọc bảng B - ba điều bắt buộc phải khai:**

1. **`exp055` [E7] là lượt DUY NHẤT không thay model/method, chỉ thay thước CHỌN MỐC.** Nó khác cha `exp021` **đúng
   một khoá** `checkpoints.best_metric` (`sentiment_f1` → `negative_f1`), và dùng **cùng một lần huấn luyện** với
   `exp021` (đường loss trùng khớp - mục 2.2). Kết quả **98,12 · 94,06** so với cha **98,41 · 94,64** ⇒ **kém ở CẢ
   HAI trục** (−0,29 / −0,58), nhưng chênh lệch **nằm trong biên nhiễu ±0,7** ⇒ đọc là **"thước chọn mốc `negative_f1`
   không giúp"**, KHÔNG đọc là "một model tốt hơn `exp021`".
2. **`exp017` [E8] là lượt có LỚP ÂM YẾU NHẤT bảng.** Đòn của nó là **`loss` focal** (`loss.type`, `loss.gamma`,
   `loss.class_weight`) trên nền `exp002`; nó **lọt bảng theo xếp hạng Accuracy macro** (98,06). Số lớp âm của nó
   **kém**: `neg F1 (5n)` **93,94** và `neg F1 micro` **93,80** - **sàn của cả bảng** ở hai thước đo đó; `price`
   negative F1 **0,00**; `stayingpower` positive Precision chỉ **95,90** (thấp nhất 9 lượt).
   ⇒ Đọc `focal` là **"đã thử và kém"**, KHÔNG đọc là "một trong 9 model tốt nhất".
3. **`exp008` [E9] là đòn TIỀN XỬ LÝ, khác loại với 8 lượt còn lại.** Nó đổi `preprocess.segmenter`:
   `none` → **`vncorenlp`** (tách từ tiếng Việt bằng RDRSegmenter/Java), tức **đầu vào văn bản khác hẳn**.
   Con số vẫn **so được với công bố** (cùng tập `test`, khoá tập đánh giá không đổi), nhưng: (a) nó **không cùng loại
   đòn** với 8 lượt kia; (b) tài liệu dự án xếp `segmenter: vncorenlp` vào danh sách lever **đã cạn và KHÔNG TÁI LẬP**
   (`docs/06_plan/archive/batches/present_plan_batch13.md`) ⇒ lượt này **không lặp lại được** ở lần chạy sau.

**C. Ghi chú RIÊNG cho lượt L1** (`qwen3-4b-instruct-2507/prompt-cot/exp009`):

- L1 đổi **`inference.batch_size` 8 → 4** (và khai `inference.dtype`) so với gốc `exp003`; **không huấn luyện**.
- L1 có **4 ô không đọc được** (đều ở khía cạnh `stayingpower`) và chỉ **2.324 ô được tính** - **ít hơn encoder
  khoảng 420 ô**, vì model sinh trả lời **"không nhắc tới" nhiều hơn** và ô "không nhắc tới" bị loại khỏi phần chấm
  ⇒ điểm của L1 **không so tuyệt đối** với encoder được (mục 9.3).

### 2.5. Vì sao **7 cột** của bản `v3`/`v4` trước phải rời bảng (Đợt 13.2 + điều kiện 10)

15 lượt của Đợt 13.1 (`exp064`…`exp078`) và 15 lượt của Đợt 13.2 (`exp079`…`exp093`) đã chạy xong: **30/30
`FINISHED`**, `n = 1.623`, `split = test`, dữ liệu `v0.2.0`, tỉ lệ đọc **100 %**. Số trên `test`, cơ sở `paper`, so
với **họ 12 lượt `lr 4e-4`** (**98,283** · **94,377**):

| Nhánh | n | `Accuracy macro` (sd) | Δ | `neg F1 (5n)` (sd) | Δ | Welch p (Acc / F1) | Đọc |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| **B4** `best_metric: neg_f1_big5` | 9 | 98,367 (0,313) | +0,084 | 94,491 (1,278) | +0,114 | 0,463 / 0,801 | **KHÔNG xác nhận** - ứng viên "bàn đạp thứ 17" bị rút lại |
| B1 `sentiment_f1` (đối chứng) | 9 | 98,167 (0,328) | −0,116 | 94,016 (1,213) | −0,361 | 0,330 / 0,411 | nhánh đối chứng ghép cặp |
| **R** `best_metric: neg_recall_big5` | 3 | 97,567 (0,316) | −0,716 | 91,987 (1,480) | −2,390 | 0,055 / 0,105 | **ĐÓNG trục** (`colour` Precision sụp 85,8 → **72,7**) |

Ghép cặp **cùng seed** B4 − B1 (n = 9): Acc **+0,200** `p = 0,122`; `neg F1` **+0,476** `p = 0,391` (6/9 cặp dương).
**Bằng chứng mạnh nhất:** `exp090` là lượt **B1** - thước CHỌN MỐC **CŨ** `sentiment_f1` - vẫn đạt **98,60 / 95,76**.

**Kỷ lục lượt đơn của đợt đó:** `exp080` **98,65** và `exp079` **95,86** - nhưng **7/8 lượt mới của đợt chỉ khác cha
ĐÚNG MỘT KHOÁ `decoding.seed`**, nên theo **điều kiện 10** chúng là **dò nhiễu**:

| Cột của bản trước | Cha | Khác cha | Quyết định |
| --- | --- | --- | --- |
| `exp080` | `exp074` | `decoding.seed` 7 → **2** | **RỜI bảng** (chỉ đổi seed) |
| `exp090` | `exp064` | `decoding.seed` 42 → **6** | **RỜI bảng** (chỉ đổi seed; *và* dính mẫu overfit) |
| `exp079` | `exp074` | `decoding.seed` 7 → **1** | **RỜI bảng** (chỉ đổi seed) |
| `exp074` | `exp073` | `decoding.seed` 42 → **7** | **RỜI bảng** (chỉ đổi seed - chính nó cũng là một lần rút thăm lại) |
| `exp082` (= `exp088`) | `exp074` | `decoding.seed` 7 → **4** | **RỜI bảng** (chỉ đổi seed; *và* trùng số với `exp088`) |
| `exp075` | `exp073` | `decoding.seed` 42 → **13** | **RỜI bảng** (chỉ đổi seed) |
| `exp086` | `exp064` | `decoding.seed` 42 → **2** | **RỜI bảng** (chỉ đổi seed) |
| `exp073` | `exp064` | `checkpoints.best_metric` | **Ở LẠI** (E1) - đòn *phương pháp* |
| `exp021` | `exp015` | `lora.r` | **Ở LẠI** (E2) - đòn *siêu tham số* |
| `exp009` (L1) | `exp003` | `inference.batch_size`, `inference.dtype` | **Ở LẠI** (L1) - lượt LLM tốt nhất |

**Một cột nữa rời bảng ở lần dựng này - KHÔNG phải vì chất lượng:** `exp019` (`adapter: dora`) là **cột E9 của bản
`v4`**, **tụt xuống hạng 10 của pool** (97,99) vì **`exp055` (98,12) lọt vào trên nó**, và vì thế bị **điều kiện 9**
thay bằng lượt LLM tốt nhất. Nó vẫn **hơn cha `exp002`** (+0,11 / +0,34) và vẫn **đủ 10 điều kiện** - chỉ **không đủ
hạng** (xem Phụ lục A).

#### ✅ Bảng 10 lượt dẫn đầu (mục 2.1, 4, 5, 6, 7, 8, 9) đã dựng lại theo 10 điều kiện mới

Danh sách encoder mới (Accuracy macro ↓; đã loại lượt `val`, lượt chỉ-đổi-seed, Tier B, overfit và lượt không kiểm
được overfit; đã gộp trùng):

`exp073` 98,52 · `exp021` 98,41 · `exp027` 98,37 · `exp015` 98,35 · `exp020` 98,34 · `exp013` 98,33 ·
`exp055` 98,12 · `exp017` 98,06 · `exp008` 98,03 **|** `exp019` 97,99 · `exp010` 97,95 · `exp018` 97,93
*(ba lượt cuối là hạng 10-12 của pool, không vào bảng)*.

## 3. Độ tin cậy theo số ô (`n`)

`n` là **số ô ground truth** trong tập `test` cho mỗi cặp (khía cạnh × sắc thái). Số này **cố định** cho mọi cột.

| Khía cạnh | `n` positive | `n` negative | 1 ô đổi chiều làm F1 lớp `negative` nhảy ≈ | Sai số chuẩn | F1 lớp `negative` trung bình 10 lượt | Đọc F1 lớp `negative` ở dòng này |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| shipping | 334 | **174** | 0,57 pp | **1,12 pp** | 97,76 | **tin cậy nhất** - cũng là khía cạnh chi phối hai thước đo theo `n` |
| stayingpower | 141 | 96 | 1,04 pp | 1,54 pp | 97,66 | chấp nhận được |
| texture | 346 | 83 | 1,20 pp | 2,56 pp | 94,22 | nhiễu nhẹ |
| colour | 622 | 54 | 1,85 pp | 4,00 pp | 90,44 | **nhiễu** |
| smell | 252 | 48 | 2,08 pp | 4,03 pp | 91,49 | **nhiễu** |
| packing | 282 | **10** | **10,00 pp** | **9,71 pp** | 89,45 | **rất nhiễu** |
| price | 321 | **6** | **16,67 pp** | **19,80 pp** | 37,88 | **rất nhiễu** |

*(Mốc so: biên nhiễu đo được của đường encoder là **±0,7 pp**. Cột "sai số chuẩn" và "F1 trung bình" tính trên
**10 lượt của bản này** - xem Bảng A ở mục 9.3.)*

Vì vậy hai thước đo lớp `negative` dưới đây được dùng thay cho việc đọc từng khía cạnh:

| Tên | Cách tính | Vì sao dùng |
| --- | --- | --- |
| **`neg F1 macro (5 khía cạnh n lớn)`** | trung bình F1 lớp `negative` trên 5 khía cạnh `colour` · `shipping` · `smell` · `stayingpower` · `texture` | loại hẳn `price` và `packing` (hai khía cạnh nhiễu nặng nhất); **nhưng vẫn còn `smell` và `colour` ở mức nhiễu** (sai số chuẩn ~4 pp) |
| **`neg F1 micro (theo n)`** | trung bình F1 lớp `negative` **có trọng số bằng `n`** của từng khía cạnh | `shipping` (174 ô) nặng gấp 29 lần `price` (6 ô), nên **không thể "ăn điểm" bằng 1-2 ô** |

**Năm khía cạnh `colour` · `shipping` · `smell` · `stayingpower` · `texture`** cộng lại có **455 ô `negative`
= 96,6 %** tổng số ô `negative` của tập `test`, còn **`price` (6 ô) và `packing` (10 ô)** chỉ chiếm **16 ô = 3,4 %**.
Nhưng nếu lấy trung bình cộng đơn giản trên 7 khía cạnh thì hai khía cạnh ít ô này chiếm tới **2/7 = 28,6 %** trọng
số - đủ để bóp méo kết luận. Đó là lý do dòng `macro (7)` vẫn được in nhưng **phải đọc kèm hai thước đo theo `n`**.

## 4. Bảng 3 - Accuracy theo khía cạnh (%, cơ sở "paper")

### 4a. Mốc tốt nhất của công bố trên Accuracy macro

Trong ba mức của công bố, mức **COT+1-shot** có **Accuracy macro cao nhất (97,70 %)**; đây là mốc đối chiếu cho
**mọi bảng delta** trong file này:

| Khía cạnh | Mốc đối chiếu (công bố, COT+1-shot) |
| --- | ---: |
| Smell | 96,15 |
| Price | 100,00 |
| Texture | 100,00 |
| Colour | 96,61 |
| Stayingpower | 94,12 |
| Packing | 98,11 |
| Shipping | 98,89 |
| **MACRO** | **97,70** |

*(Hai mức còn lại có Accuracy macro thấp hơn: 0-shot 97,36 và 5-shot 96,74.)*

### 4b. Bảng Accuracy đầy đủ (3 mức của công bố + 10 lượt)

| Khía cạnh | CB 0-shot | CB 1-shot | CB 5-shot | E1 | E2 | E3 | E4 | E5 | E6 | E7 | E8 | E9 | L1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Smell | 94,59 | 96,15 | 92,86 | 96,95 | 97,30 | 96,96 | 96,96 | 96,95 | 96,63 | 96,62 | 97,29 | 97,30 | 97,44 |
| Price | 97,22 | 100,00 | 100,00 | 99,07 | 99,07 | 99,07 | 98,76 | 98,77 | 99,07 | 99,07 | 98,45 | 98,14 | 98,49 |
| Texture | 94,12 | 100,00 | 100,00 | 98,60 | 97,89 | 97,90 | 97,20 | 97,66 | 97,89 | 97,42 | 97,65 | 97,44 | 96,86 |
| Colour | 97,37 | 96,61 | 94,74 | 98,50 | 98,35 | 98,06 | 98,95 | 98,20 | 98,35 | 98,50 | 98,34 | 97,75 | 98,82 |
| Stayingpower | 100,00 | 94,12 | 92,86 | 99,15 | 98,31 | 98,72 | 98,30 | 98,72 | 98,30 | 97,87 | 97,01 | 97,87 | 96,15 |
| Packing | 98,25 | 98,11 | 100,00 | 98,96 | 99,31 | 99,65 | 99,65 | 99,65 | 99,66 | 98,97 | 99,31 | 99,31 | 97,90 |
| Shipping | 100,00 | 98,89 | 96,70 | 98,41 | 98,62 | 98,21 | 98,61 | 98,42 | 98,41 | 98,41 | 98,39 | 98,42 | 98,72 |
| **MACRO** | 97,36 | 97,70 | 96,74 | 98,52 | 98,41 | 98,37 | 98,35 | 98,34 | 98,33 | 98,12 | 98,06 | 98,03 | 97,77 |


### 4c. Delta Accuracy so với mốc đối chiếu (pp)

| Khía cạnh | CB 0-shot | CB 1-shot | CB 5-shot | E1 | E2 | E3 | E4 | E5 | E6 | E7 | E8 | E9 | L1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Smell | -1,56 | +0,00 | -3,29 | +0,80 | +1,15 | +0,81 | +0,81 | +0,80 | +0,48 | +0,47 | +1,14 | +1,15 | +1,29 |
| Price | -2,78 | +0,00 | +0,00 | -0,93 | -0,93 | -0,93 | -1,24 | -1,23 | -0,93 | -0,93 | -1,55 | -1,86 | -1,51 |
| Texture | -5,88 | +0,00 | +0,00 | -1,40 | -2,11 | -2,10 | -2,80 | -2,34 | -2,11 | -2,58 | -2,35 | -2,56 | -3,14 |
| Colour | +0,76 | +0,00 | -1,87 | +1,89 | +1,74 | +1,45 | +2,34 | +1,59 | +1,74 | +1,89 | +1,73 | +1,14 | +2,21 |
| Stayingpower | +5,88 | +0,00 | -1,26 | +5,03 | +4,19 | +4,60 | +4,18 | +4,60 | +4,18 | +3,75 | +2,89 | +3,75 | +2,03 |
| Packing | +0,14 | +0,00 | +1,89 | +0,85 | +1,20 | +1,54 | +1,54 | +1,54 | +1,55 | +0,86 | +1,20 | +1,20 | -0,21 |
| Shipping | +1,11 | +0,00 | -2,19 | -0,48 | -0,27 | -0,68 | -0,28 | -0,47 | -0,48 | -0,48 | -0,50 | -0,47 | -0,17 |
| **MACRO** | -0,34 | +0,00 | -0,96 | +0,82 | +0,71 | +0,67 | +0,65 | +0,64 | +0,63 | +0,42 | +0,36 | +0,33 | +0,07 |


**Nhận xét bảng 3:**
- **`MACRO`**: **cả 9 lượt encoder vượt mốc** (+0,33 … +0,82); lượt LLM **L1** vượt **+0,07**.
- **`stayingpower`**: dự án **vượt ở cả 9 lượt** (+2,89 … +5,03) - khía cạnh vượt mạnh nhất; **`colour`** (+1,14 …
  +2,34) và **`smell`** (+0,47 … +1,15) cũng vượt ở cả 9 lượt.
- **`packing`**: 8/9 lượt **vượt nhẹ** (+0,85 … +1,55); riêng **L1 dưới** (−0,21).
- **`price` và `texture`**: công bố đạt **100,00** ở mốc nên **không thể vượt** - mọi lượt đều **dưới**
  (`price` −0,93 … −1,86; `texture` −1,40 … −3,14).
- **`shipping`**: **9/9 lượt dưới** (−0,27 … −0,68).
- ⇒ **Lợi thế của dự án nằm ở `MACRO` và ở 3 khía cạnh `smell` / `colour` / `stayingpower`, KHÔNG nằm ở từng ô.**

## 5. Bảng 4 - Precision theo khía cạnh và sắc thái (%, cơ sở "paper")

> Hai dòng cuối là hai thước đo lớp `negative` **theo số ô**, tính trên **chính Precision** của bảng này.

| Khía cạnh | Sắc thái | n | CB 0-shot | CB 1-shot | CB 5-shot | E1 | E2 | E3 | E4 | E5 | E6 | E7 | E8 | E9 | L1 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Smell | positive | 252 | 97,06 | 100,00 | 96,15 | 98,80 | 99,60 | 99,60 | 99,60 | 99,60 | 98,80 | 99,60 | 99,20 | 99,60 | 99,50 |
| Smell | negative | 48 | 66,67 | 50,00 | 50,00 | 88,20 | 87,00 | 85,50 | 85,50 | 85,50 | 86,50 | 83,90 | 88,50 | 87,00 | 89,40 |
| Price | positive | 321 | 100,00 | 100,00 | 100,00 | 99,10 | 99,10 | 99,10 | 98,80 | 98,80 | 99,10 | 99,10 | 98,50 | 98,10 | 99,60 |
| Price | negative | 6 | 0,00 | 0,00 | 0,00 | 100,00 | 100,00 | 100,00 | 0,00 | 100,00 | 100,00 | 100,00 | 0,00 | 0,00 | 50,00 |
| Texture | positive | 346 | 92,68 | 100,00 | 100,00 | 98,60 | 99,10 | 99,10 | 99,10 | 99,40 | 99,40 | 99,40 | 98,50 | 99,40 | 99,60 |
| Texture | negative | 83 | 100,00 | 100,00 | 100,00 | 98,70 | 93,00 | 93,00 | 89,90 | 91,00 | 92,00 | 90,00 | 94,00 | 90,00 | 88,70 |
| Colour | positive | 622 | 100,00 | 100,00 | 100,00 | 99,20 | 99,70 | 99,30 | 99,80 | 99,70 | 99,70 | 99,70 | 99,30 | 99,70 | 100,00 |
| Colour | negative | 54 | 77,78 | 75,00 | 66,67 | 90,70 | 85,20 | 84,70 | 89,70 | 83,90 | 85,20 | 86,70 | 87,50 | 80,00 | 86,00 |
| Stayingpower | positive | 141 | 100,00 | 100,00 | 100,00 | 99,30 | 98,60 | 100,00 | 98,60 | 99,30 | 98,60 | 97,90 | 95,90 | 97,90 | 98,70 |
| Stayingpower | negative | 96 | 100,00 | 80,00 | 80,00 | 98,90 | 97,90 | 96,90 | 97,90 | 97,90 | 97,90 | 97,90 | 98,90 | 97,90 | 93,80 |
| Packing | positive | 282 | 100,00 | 100,00 | 100,00 | 99,60 | 99,60 | 100,00 | 100,00 | 100,00 | 100,00 | 99,60 | 99,60 | 99,60 | 100,00 |
| Packing | negative | 10 | 66,67 | 66,67 | 100,00 | 80,00 | 90,00 | 90,00 | 90,00 | 90,00 | 90,00 | 81,80 | 88,90 | 90,00 | 62,50 |
| Shipping | positive | 334 | 100,00 | 100,00 | 96,88 | 99,10 | 99,10 | 98,80 | 99,40 | 99,10 | 99,10 | 99,10 | 99,10 | 99,10 | 99,00 |
| Shipping | negative | 174 | 100,00 | 96,30 | 96,30 | 97,10 | 97,70 | 97,10 | 97,10 | 97,10 | 97,10 | 97,10 | 97,00 | 97,10 | 98,10 |
| **MACRO** | positive |  | 98,53 | 100,00 | 99,00 | 99,10 | 99,26 | 99,41 | 99,33 | 99,41 | 99,24 | 99,20 | 98,59 | 99,06 | 99,49 |
| **MACRO** | negative |  | 73,02 | 66,85 | 70,42 | 93,37 | 92,97 | 92,46 | 78,59 | 92,20 | 92,67 | 91,06 | 79,26 | 77,43 | 81,21 |
| **neg P macro (5 khía cạnh n lớn)** |  |  | 88,89 | 80,26 | 78,59 | 94,72 | 92,16 | 91,44 | 92,02 | 91,08 | 91,74 | 91,12 | 93,18 | 90,40 | 91,20 |
| **neg P micro (theo n)** |  |  | 92,07 | 84,61 | 84,37 | 95,78 | 94,25 | 93,62 | 92,58 | 93,38 | 93,81 | 93,19 | 93,50 | 91,63 | 91,92 |


### 5b. Delta Precision so với mốc đối chiếu (pp)

| Khía cạnh | Sắc thái | n | CB 0-shot | CB 1-shot | CB 5-shot | E1 | E2 | E3 | E4 | E5 | E6 | E7 | E8 | E9 | L1 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Smell | positive | 252 | -2,94 | +0,00 | -3,85 | -1,20 | -0,40 | -0,40 | -0,40 | -0,40 | -1,20 | -0,40 | -0,80 | -0,40 | -0,50 |
| Smell | negative | 48 | +16,67 | +0,00 | +0,00 | +38,20 | +37,00 | +35,50 | +35,50 | +35,50 | +36,50 | +33,90 | +38,50 | +37,00 | +39,40 |
| Price | positive | 321 | +0,00 | +0,00 | +0,00 | -0,90 | -0,90 | -0,90 | -1,20 | -1,20 | -0,90 | -0,90 | -1,50 | -1,90 | -0,40 |
| Price | negative | 6 | +0,00 | +0,00 | +0,00 | +100,00 | +100,00 | +100,00 | +0,00 | +100,00 | +100,00 | +100,00 | +0,00 | +0,00 | +50,00 |
| Texture | positive | 346 | -7,32 | +0,00 | +0,00 | -1,40 | -0,90 | -0,90 | -0,90 | -0,60 | -0,60 | -0,60 | -1,50 | -0,60 | -0,40 |
| Texture | negative | 83 | +0,00 | +0,00 | +0,00 | -1,30 | -7,00 | -7,00 | -10,10 | -9,00 | -8,00 | -10,00 | -6,00 | -10,00 | -11,30 |
| Colour | positive | 622 | +0,00 | +0,00 | +0,00 | -0,80 | -0,30 | -0,70 | -0,20 | -0,30 | -0,30 | -0,30 | -0,70 | -0,30 | +0,00 |
| Colour | negative | 54 | +2,78 | +0,00 | -8,33 | +15,70 | +10,20 | +9,70 | +14,70 | +8,90 | +10,20 | +11,70 | +12,50 | +5,00 | +11,00 |
| Stayingpower | positive | 141 | +0,00 | +0,00 | +0,00 | -0,70 | -1,40 | +0,00 | -1,40 | -0,70 | -1,40 | -2,10 | -4,10 | -2,10 | -1,30 |
| Stayingpower | negative | 96 | +20,00 | +0,00 | +0,00 | +18,90 | +17,90 | +16,90 | +17,90 | +17,90 | +17,90 | +17,90 | +18,90 | +17,90 | +13,80 |
| Packing | positive | 282 | +0,00 | +0,00 | +0,00 | -0,40 | -0,40 | +0,00 | +0,00 | +0,00 | +0,00 | -0,40 | -0,40 | -0,40 | +0,00 |
| Packing | negative | 10 | +0,00 | +0,00 | +33,33 | +13,33 | +23,33 | +23,33 | +23,33 | +23,33 | +23,33 | +15,13 | +22,23 | +23,33 | -4,17 |
| Shipping | positive | 334 | +0,00 | +0,00 | -3,12 | -0,90 | -0,90 | -1,20 | -0,60 | -0,90 | -0,90 | -0,90 | -0,90 | -0,90 | -1,00 |
| Shipping | negative | 174 | +3,70 | +0,00 | +0,00 | +0,80 | +1,40 | +0,80 | +0,80 | +0,80 | +0,80 | +0,80 | +0,70 | +0,80 | +1,80 |
| **MACRO** | positive |  | -1,47 | +0,00 | -1,00 | -0,90 | -0,74 | -0,59 | -0,67 | -0,59 | -0,76 | -0,80 | -1,41 | -0,94 | -0,51 |
| **MACRO** | negative |  | +6,17 | +0,00 | +3,57 | +26,52 | +26,12 | +25,61 | +11,74 | +25,35 | +25,82 | +24,21 | +12,41 | +10,58 | +14,36 |
| **neg P macro (5 khía cạnh n lớn)** |  |  | +8,63 | +0,00 | -1,67 | +14,46 | +11,90 | +11,18 | +11,76 | +10,82 | +11,48 | +10,86 | +12,92 | +10,14 | +10,94 |
| **neg P micro (theo n)** |  |  | +7,46 | +0,00 | -0,24 | +11,17 | +9,64 | +9,01 | +7,97 | +8,77 | +9,20 | +8,58 | +8,89 | +7,02 | +7,31 |


**Nhận xét bảng 4:**
- **Lớp `positive`**: mốc đối chiếu là **100,00** ⇒ **cả 10 lượt đều DƯỚI** (−0,51 … −1,41); sát nhất **L1 (−0,51)**,
  rồi **E3 `exp027` (−0,59)** và **E5 `exp020` (−0,59)**; xa nhất **E8 `exp017` (−1,41)**. Đây là **tính chất của mốc**:
  mức 1-shot của công bố đạt trần ở lớp dương.
- **Lớp `negative`**: mốc **66,85** ⇒ **10/10 lượt vượt rất xa** (+10,58 … +26,52), cao nhất **E1 `exp073` 93,37**;
  thấp nhất **E9 `exp008` 77,43**.
- **`neg P macro (5 khía cạnh n lớn)`**: mốc **80,26** ⇒ **10/10 lượt vượt** (**+10,14 … +14,46**), cao nhất
  **E1 `exp073` 94,72**; thấp nhất **E9 `exp008` 90,40**.
- **`neg P micro (theo n)`**: mốc **84,61** ⇒ **10/10 lượt vượt** (**+7,02 … +11,17**).
- ⇒ **Toàn bộ lợi thế lớp `negative` của dự án nằm ở PRECISION**, không ở Recall - xem bảng 5 ngay dưới.

## 6. Bảng 5 - Recall theo khía cạnh và sắc thái (%, cơ sở "paper")

> Hai dòng cuối là hai thước đo lớp `negative` **theo số ô**, tính trên **chính Recall** của bảng này.

| Khía cạnh | Sắc thái | n | CB 0-shot | CB 1-shot | CB 5-shot | E1 | E2 | E3 | E4 | E5 | E6 | E7 | E8 | E9 | L1 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Smell | positive | 252 | 97,06 | 96,00 | 96,15 | 97,60 | 97,20 | 96,80 | 96,80 | 96,80 | 97,20 | 96,40 | 97,60 | 97,20 | 97,40 |
| Smell | negative | 48 | 66,67 | 100,00 | 50,00 | 93,80 | 97,90 | 97,90 | 97,90 | 97,90 | 93,80 | 97,90 | 95,80 | 97,90 | 97,70 |
| Price | positive | 321 | 97,22 | 100,00 | 100,00 | 100,00 | 100,00 | 100,00 | 100,00 | 100,00 | 100,00 | 100,00 | 100,00 | 100,00 | 98,90 |
| Price | negative | 6 | 0,00 | 0,00 | 0,00 | 40,00 | 40,00 | 40,00 | 0,00 | 20,00 | 40,00 | 40,00 | 0,00 | 0,00 | 75,00 |
| Texture | positive | 346 | 100,00 | 100,00 | 100,00 | 99,70 | 98,30 | 98,30 | 97,40 | 97,70 | 98,00 | 97,40 | 98,50 | 97,40 | 96,30 |
| Texture | negative | 83 | 76,92 | 100,00 | 100,00 | 93,90 | 96,40 | 96,40 | 96,40 | 97,60 | 97,60 | 97,60 | 94,00 | 97,60 | 98,60 |
| Colour | positive | 622 | 97,10 | 96,23 | 94,12 | 99,20 | 98,50 | 98,50 | 99,00 | 98,40 | 98,50 | 98,70 | 98,90 | 97,90 | 98,70 |
| Colour | negative | 54 | 100,00 | 100,00 | 100,00 | 90,70 | 96,30 | 92,60 | 98,10 | 96,30 | 96,30 | 96,30 | 92,50 | 96,30 | 100,00 |
| Stayingpower | positive | 141 | 100,00 | 92,31 | 90,00 | 99,30 | 98,60 | 97,90 | 98,60 | 98,60 | 98,60 | 98,60 | 99,30 | 98,60 | 93,70 |
| Stayingpower | negative | 96 | 100,00 | 100,00 | 100,00 | 98,90 | 97,90 | 100,00 | 97,90 | 98,90 | 97,90 | 96,80 | 93,60 | 96,80 | 98,70 |
| Packing | positive | 282 | 98,18 | 98,04 | 100,00 | 99,30 | 99,60 | 99,60 | 99,60 | 99,60 | 99,60 | 99,30 | 99,60 | 99,60 | 97,80 |
| Packing | negative | 10 | 100,00 | 100,00 | 100,00 | 88,90 | 90,00 | 100,00 | 100,00 | 100,00 | 100,00 | 90,00 | 88,90 | 90,00 | 100,00 |
| Shipping | positive | 334 | 100,00 | 98,44 | 98,41 | 98,50 | 98,80 | 98,50 | 98,50 | 98,50 | 98,50 | 98,50 | 98,50 | 98,50 | 99,00 |
| Shipping | negative | 174 | 100,00 | 100,00 | 92,86 | 98,20 | 98,30 | 97,70 | 98,80 | 98,30 | 98,20 | 98,20 | 98,20 | 98,30 | 98,10 |
| **MACRO** | positive |  | 98,51 | 97,29 | 96,95 | 99,09 | 98,71 | 98,51 | 98,56 | 98,51 | 98,63 | 98,41 | 98,91 | 98,46 | 97,40 |
| **MACRO** | negative |  | 77,66 | 85,71 | 77,55 | 86,34 | 88,11 | 89,23 | 84,16 | 87,00 | 89,11 | 88,11 | 80,43 | 82,41 | 95,44 |
| **neg R macro (5 khía cạnh n lớn)** |  |  | 88,72 | 100,00 | 88,57 | 95,10 | 97,36 | 96,92 | 97,82 | 97,80 | 96,76 | 97,36 | 94,82 | 97,38 | 98,62 |
| **neg R micro (theo n)** |  |  | 91,26 | 98,73 | 90,99 | 95,34 | 96,69 | 96,69 | 96,79 | 97,07 | 96,66 | 96,65 | 94,18 | 96,17 | 98,23 |


### 6b. Delta Recall so với mốc đối chiếu (pp)

| Khía cạnh | Sắc thái | n | CB 0-shot | CB 1-shot | CB 5-shot | E1 | E2 | E3 | E4 | E5 | E6 | E7 | E8 | E9 | L1 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Smell | positive | 252 | +1,06 | +0,00 | +0,15 | +1,60 | +1,20 | +0,80 | +0,80 | +0,80 | +1,20 | +0,40 | +1,60 | +1,20 | +1,40 |
| Smell | negative | 48 | -33,33 | +0,00 | -50,00 | -6,20 | -2,10 | -2,10 | -2,10 | -2,10 | -6,20 | -2,10 | -4,20 | -2,10 | -2,30 |
| Price | positive | 321 | -2,78 | +0,00 | +0,00 | +0,00 | +0,00 | +0,00 | +0,00 | +0,00 | +0,00 | +0,00 | +0,00 | +0,00 | -1,10 |
| Price | negative | 6 | +0,00 | +0,00 | +0,00 | +40,00 | +40,00 | +40,00 | +0,00 | +20,00 | +40,00 | +40,00 | +0,00 | +0,00 | +75,00 |
| Texture | positive | 346 | +0,00 | +0,00 | +0,00 | -0,30 | -1,70 | -1,70 | -2,60 | -2,30 | -2,00 | -2,60 | -1,50 | -2,60 | -3,70 |
| Texture | negative | 83 | -23,08 | +0,00 | +0,00 | -6,10 | -3,60 | -3,60 | -3,60 | -2,40 | -2,40 | -2,40 | -6,00 | -2,40 | -1,40 |
| Colour | positive | 622 | +0,87 | +0,00 | -2,11 | +2,97 | +2,27 | +2,27 | +2,77 | +2,17 | +2,27 | +2,47 | +2,67 | +1,67 | +2,47 |
| Colour | negative | 54 | +0,00 | +0,00 | +0,00 | -9,30 | -3,70 | -7,40 | -1,90 | -3,70 | -3,70 | -3,70 | -7,50 | -3,70 | +0,00 |
| Stayingpower | positive | 141 | +7,69 | +0,00 | -2,31 | +6,99 | +6,29 | +5,59 | +6,29 | +6,29 | +6,29 | +6,29 | +6,99 | +6,29 | +1,39 |
| Stayingpower | negative | 96 | +0,00 | +0,00 | +0,00 | -1,10 | -2,10 | +0,00 | -2,10 | -1,10 | -2,10 | -3,20 | -6,40 | -3,20 | -1,30 |
| Packing | positive | 282 | +0,14 | +0,00 | +1,96 | +1,26 | +1,56 | +1,56 | +1,56 | +1,56 | +1,56 | +1,26 | +1,56 | +1,56 | -0,24 |
| Packing | negative | 10 | +0,00 | +0,00 | +0,00 | -11,10 | -10,00 | +0,00 | +0,00 | +0,00 | +0,00 | -10,00 | -11,10 | -10,00 | +0,00 |
| Shipping | positive | 334 | +1,56 | +0,00 | -0,03 | +0,06 | +0,36 | +0,06 | +0,06 | +0,06 | +0,06 | +0,06 | +0,06 | +0,06 | +0,56 |
| Shipping | negative | 174 | +0,00 | +0,00 | -7,14 | -1,80 | -1,70 | -2,30 | -1,20 | -1,70 | -1,80 | -1,80 | -1,80 | -1,70 | -1,90 |
| **MACRO** | positive |  | +1,22 | +0,00 | -0,34 | +1,80 | +1,42 | +1,22 | +1,27 | +1,22 | +1,34 | +1,12 | +1,62 | +1,17 | +0,11 |
| **MACRO** | negative |  | -8,05 | +0,00 | -8,16 | +0,63 | +2,40 | +3,52 | -1,55 | +1,29 | +3,40 | +2,40 | -5,28 | -3,30 | +9,73 |
| **neg R macro (5 khía cạnh n lớn)** |  |  | -11,28 | +0,00 | -11,43 | -4,90 | -2,64 | -3,08 | -2,18 | -2,20 | -3,24 | -2,64 | -5,18 | -2,62 | -1,38 |
| **neg R micro (theo n)** |  |  | -7,47 | +0,00 | -7,74 | -3,39 | -2,04 | -2,04 | -1,94 | -1,66 | -2,07 | -2,08 | -4,55 | -2,56 | -0,50 |


**Nhận xét bảng 5:**
- **Lớp `positive`**: Recall của công bố là **97,29** ⇒ **cả 10 lượt vượt** (97,40 … 99,09; Δ **+0,11 … +1,80**).
  Lượt rộng tay nhất **E1 `exp073` 99,09 (+1,80)**.
- **Lớp `negative` (theo từng khía cạnh, `macro` 7 khía cạnh)**: mốc **85,71** ⇒ **7 lượt vượt** (`L1` **95,44**
  Δ +9,73 đứng đầu, rồi `E3` 89,23 · `E6` 89,11 · `E2`/`E7` 88,11 · `E5` 87,00 · `E1` 86,34), **3 lượt dưới**
  (`E4` 84,16 · `E9` 82,41 · `E8` 80,43).
- **`neg R macro (5 khía cạnh n lớn)`**: mốc **100,00** ⇒ **CẢ 10 lượt đều DƯỚI** (94,82 … 98,62;
  Δ **−1,38 … −5,18**) - đây là **trục yếu nhất và ổn định nhất** của dự án.
- **`neg R micro (theo n)`**: mốc **98,73** ⇒ **cả 10 lượt đều dưới** (94,18 … 98,23; Δ **−0,50 … −4,55**).
- ⇒ **Kết luận quan trọng:** ở hai thước đo theo số ô, dự án **KHÔNG** bắt được nhiều ô `negative` hơn công bố -
  Recall lớp `negative` của dự án **thấp hơn**. Vậy lợi thế lớp `negative` ở bảng 6 đến từ **Precision** (khi đã đoán
  `negative` thì đoán đúng hơn), **không** phải từ việc đoán rộng hơn.

## 7. Bảng 6 - F1 theo khía cạnh và sắc thái (%, cơ sở "paper")

Đây là **bảng điểm chính để so với công bố**. Hai dòng cuối là hai thước đo lớp `negative` theo số ô (mục 3).

| Khía cạnh | Sắc thái | n | CB 0-shot | CB 1-shot | CB 5-shot | E1 | E2 | E3 | E4 | E5 | E6 | E7 | E8 | E9 | L1 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Smell | positive | 252 | 97,06 | 97,06 | 96,15 | 98,20 | 98,40 | 98,20 | 98,20 | 98,20 | 98,00 | 98,00 | 98,40 | 98,40 | 98,40 |
| Smell | negative | 48 | 66,67 | 66,67 | 50,00 | 90,90 | 92,20 | 91,30 | 91,30 | 91,30 | 90,00 | 90,40 | 92,00 | 92,20 | 93,30 |
| Price | positive | 321 | 98,59 | 100,00 | 100,00 | 99,50 | 99,50 | 99,50 | 99,40 | 99,40 | 99,50 | 99,50 | 99,20 | 99,10 | 99,20 |
| Price | negative | 6 | 0,00 | 0,00 | 0,00 | 57,10 | 57,10 | 57,10 | 0,00 | 33,30 | 57,10 | 57,10 | 0,00 | 0,00 | 60,00 |
| Texture | positive | 346 | 96,20 | 100,00 | 100,00 | 99,10 | 98,70 | 98,70 | 98,20 | 98,50 | 98,70 | 98,40 | 98,50 | 98,40 | 97,90 |
| Texture | negative | 83 | 86,96 | 100,00 | 100,00 | 96,30 | 94,70 | 94,70 | 93,00 | 94,20 | 94,70 | 93,60 | 94,00 | 93,60 | 93,40 |
| Colour | positive | 622 | 98,53 | 98,08 | 96,97 | 99,20 | 99,10 | 98,90 | 99,40 | 99,00 | 99,10 | 99,20 | 99,10 | 98,80 | 99,40 |
| Colour | negative | 54 | 87,50 | 85,71 | 80,00 | 90,70 | 90,40 | 88,50 | 93,70 | 89,70 | 90,40 | 91,20 | 89,90 | 87,40 | 92,50 |
| Stayingpower | positive | 141 | 100,00 | 96,00 | 94,74 | 99,30 | 98,60 | 98,90 | 98,60 | 98,90 | 98,60 | 98,20 | 97,50 | 98,20 | 96,10 |
| Stayingpower | negative | 96 | 100,00 | 88,89 | 88,89 | 98,90 | 97,90 | 98,40 | 97,90 | 98,40 | 97,90 | 97,40 | 96,20 | 97,40 | 96,20 |
| Packing | positive | 282 | 99,08 | 99,01 | 100,00 | 99,50 | 99,60 | 99,80 | 99,80 | 99,80 | 99,80 | 99,50 | 99,60 | 99,60 | 98,90 |
| Packing | negative | 10 | 80,00 | 80,00 | 100,00 | 84,20 | 90,00 | 94,70 | 94,70 | 94,70 | 94,70 | 85,70 | 88,90 | 90,00 | 76,90 |
| Shipping | positive | 334 | 100,00 | 99,21 | 94,74 | 98,80 | 99,00 | 98,60 | 98,90 | 98,80 | 98,80 | 98,80 | 98,80 | 98,80 | 99,00 |
| Shipping | negative | 174 | 100,00 | 98,11 | 94,55 | 97,70 | 98,00 | 97,40 | 98,00 | 97,70 | 97,70 | 97,70 | 97,60 | 97,70 | 98,10 |
| **MACRO** | positive |  | 98,49 | 98,48 | 97,51 | 99,09 | 98,99 | 98,94 | 98,93 | 98,94 | 98,93 | 98,80 | 98,73 | 98,76 | 98,41 |
| **MACRO** | negative |  | 74,45 | 74,20 | 73,35 | 87,97 | 88,61 | 88,87 | 81,23 | 85,61 | 88,93 | 87,59 | 79,80 | 79,76 | 87,20 |
| **neg F1 macro (5 khía cạnh n lớn)** |  |  | 88,23 | 87,88 | 82,69 | 94,90 | 94,64 | 94,06 | 94,78 | 94,26 | 94,14 | 94,06 | 93,94 | 93,66 | 94,70 |
| **neg F1 micro (theo n)** |  |  | 91,17 | 90,30 | 87,06 | 95,40 | 95,24 | 94,92 | 94,60 | 94,77 | 95,01 | 94,66 | 93,80 | 93,77 | 94,82 |


### 7b. Delta F1 so với mốc đối chiếu (pp)

| Khía cạnh | Sắc thái | n | CB 0-shot | CB 1-shot | CB 5-shot | E1 | E2 | E3 | E4 | E5 | E6 | E7 | E8 | E9 | L1 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Smell | positive | 252 | +0,00 | +0,00 | -0,91 | +1,14 | +1,34 | +1,14 | +1,14 | +1,14 | +0,94 | +0,94 | +1,34 | +1,34 | +1,34 |
| Smell | negative | 48 | +0,00 | +0,00 | -16,67 | +24,23 | +25,53 | +24,63 | +24,63 | +24,63 | +23,33 | +23,73 | +25,33 | +25,53 | +26,63 |
| Price | positive | 321 | -1,41 | +0,00 | +0,00 | -0,50 | -0,50 | -0,50 | -0,60 | -0,60 | -0,50 | -0,50 | -0,80 | -0,90 | -0,80 |
| Price | negative | 6 | +0,00 | +0,00 | +0,00 | +57,10 | +57,10 | +57,10 | +0,00 | +33,30 | +57,10 | +57,10 | +0,00 | +0,00 | +60,00 |
| Texture | positive | 346 | -3,80 | +0,00 | +0,00 | -0,90 | -1,30 | -1,30 | -1,80 | -1,50 | -1,30 | -1,60 | -1,50 | -1,60 | -2,10 |
| Texture | negative | 83 | -13,04 | +0,00 | +0,00 | -3,70 | -5,30 | -5,30 | -7,00 | -5,80 | -5,30 | -6,40 | -6,00 | -6,40 | -6,60 |
| Colour | positive | 622 | +0,45 | +0,00 | -1,11 | +1,12 | +1,02 | +0,82 | +1,32 | +0,92 | +1,02 | +1,12 | +1,02 | +0,72 | +1,32 |
| Colour | negative | 54 | +1,79 | +0,00 | -5,71 | +4,99 | +4,69 | +2,79 | +7,99 | +3,99 | +4,69 | +5,49 | +4,19 | +1,69 | +6,79 |
| Stayingpower | positive | 141 | +4,00 | +0,00 | -1,26 | +3,30 | +2,60 | +2,90 | +2,60 | +2,90 | +2,60 | +2,20 | +1,50 | +2,20 | +0,10 |
| Stayingpower | negative | 96 | +11,11 | +0,00 | +0,00 | +10,01 | +9,01 | +9,51 | +9,01 | +9,51 | +9,01 | +8,51 | +7,31 | +8,51 | +7,31 |
| Packing | positive | 282 | +0,07 | +0,00 | +0,99 | +0,49 | +0,59 | +0,79 | +0,79 | +0,79 | +0,79 | +0,49 | +0,59 | +0,59 | -0,11 |
| Packing | negative | 10 | +0,00 | +0,00 | +20,00 | +4,20 | +10,00 | +14,70 | +14,70 | +14,70 | +14,70 | +5,70 | +8,90 | +10,00 | -3,10 |
| Shipping | positive | 334 | +0,79 | +0,00 | -4,47 | -0,41 | -0,21 | -0,61 | -0,31 | -0,41 | -0,41 | -0,41 | -0,41 | -0,41 | -0,21 |
| Shipping | negative | 174 | +1,89 | +0,00 | -3,56 | -0,41 | -0,11 | -0,71 | -0,11 | -0,41 | -0,41 | -0,41 | -0,51 | -0,41 | -0,01 |
| **MACRO** | positive |  | +0,01 | +0,00 | -0,97 | +0,61 | +0,51 | +0,46 | +0,45 | +0,46 | +0,45 | +0,32 | +0,25 | +0,28 | -0,07 |
| **MACRO** | negative |  | +0,25 | +0,00 | -0,85 | +13,77 | +14,41 | +14,67 | +7,03 | +11,41 | +14,73 | +13,39 | +5,60 | +5,56 | +13,00 |
| **neg F1 macro (5 khía cạnh n lớn)** |  |  | +0,35 | +0,00 | -5,19 | +7,02 | +6,76 | +6,18 | +6,90 | +6,38 | +6,26 | +6,18 | +6,06 | +5,78 | +6,82 |
| **neg F1 micro (theo n)** |  |  | +0,87 | +0,00 | -3,24 | +5,10 | +4,94 | +4,62 | +4,30 | +4,47 | +4,71 | +4,36 | +3,50 | +3,47 | +4,52 |


**Nhận xét bảng 6:**
- **`MACRO positive`**: mốc 98,48 ⇒ **9/10 lượt vượt** (+0,25 … +0,61), riêng **L1 dưới (−0,07)**.
  Cao nhất **E1 `exp073` 99,09 (+0,61)**.
- **`MACRO negative` (7 khía cạnh)**: mốc 74,20 ⇒ cả 10 lượt vượt (**+5,56 … +14,73**). **Nhưng dòng này bị `price` và
  `packing` chi phối** (mục 9.3): lượt cao nhất `E6` **88,93** đứng đầu phần lớn nhờ `price` negative đúng **2/5 ô**
  (`price` F1 **57,10**).
- **`neg F1 macro (5 khía cạnh n lớn)`** - thước đo **đáng tin**: mốc 87,88 ⇒ **cả 10 lượt vượt**
  (**+5,78 … +7,02**), cao nhất **E1 `exp073` 94,90** (rồi E4 94,78 · L1 94,70 · E2 94,64).
- **`neg F1 micro (theo n)`**: mốc 90,30 ⇒ **cả 10 lượt vượt** (**+3,47 … +5,10**), cao nhất **E1 `exp073` 95,40**.
- **Theo từng khía cạnh**: dự án **vượt ở cả `smell`, `colour`, `stayingpower`** (cả hai sắc thái) nhưng **thua ở
  `texture`** (cả hai sắc thái), ở **`price` positive** và ở **`shipping`** (cả hai sắc thái; ô sát nhất là
  `shipping` negative F1 của `E2` **98,00** vs mốc 98,11 = **−0,11**); `packing` chia đôi (positive: 9/10 vượt;
  negative: 9/10 vượt, **L1 dưới**).
- **Không lượt nào thắng công bố ở MỌI ô**: trong **42 ô** (7 khía cạnh × 2 sắc thái × 3 chỉ số P/R/F1), dự án **thua hết
  ở 14 ô**, **thắng hết ở 17 ô** và **11 ô hỗn hợp** (đọc kèm mục 9.3: các ô `price`/`packing` chỉ có **4-10 ô** ground
  truth).

## 8. Hai cây phát triển của các lượt trong bảng

Cây lấy quan hệ **cha - con** từ file cấu hình của từng thí nghiệm; **thay đổi ở mỗi cạnh** được tính bằng cách so
**cấu hình đã hợp nhất** (7 lớp) của con với cha (bảng B ở mục 2.4 là bản chi tiết). Mỗi cạnh đổi **đúng MỘT** thông
số. Số cạnh mỗi nút là **Accuracy macro · `neg F1 macro (5 khía cạnh n lớn)`** (cơ sở `paper`).

### 8.1. Cây dòng ENCODER (CafeBERT + LoRA) - **9 lượt của bảng nằm ở 9 vị trí, nhưng chỉ 7 nhánh: `exp055` [E7] là CON của `exp021` [E2]**

```
cafebert/lora/exp001   <- GỐC          97,67 · 92,26   [đầu phân loại ĐÓNG BĂNG]
   │
   │   cho đầu phân loại HỌC cùng adapter
   ▼
cafebert/lora/exp002   <- exp001      97,88 · 92,62   *** BASELINE của mọi nhánh dưới ***
   │
   ├── tăng tốc độ học 2e-4 -> 4e-4
   │      ▼
   │   cafebert/lora/exp015   <- exp002   98,35 · 94,78   [E4]
   │      ├── giảm LoRA r 16 -> 8
   │      │      ▼
   │      │   cafebert/lora/exp021  <- exp015   98,41 · 94,64   [E2]
   │      │      └── đổi thước CHỌN MỐC  sentiment_f1 -> negative_f1
   │      │             ▼
   │      │          cafebert/lora/exp055  <- exp021   98,12 · 94,06   [E7]
   │      │          (CÙNG lần huấn luyện với exp021 - chỉ khác mốc được chọn)
   │      ├── số epoch 3 -> 6
   │      │      ▼
   │      │   cafebert/lora/exp027  <- exp015   98,37 · 94,06   [E3]
   │      ├── tăng LoRA r 16 -> 32
   │      │      ▼
   │      │   cafebert/lora/exp020  <- exp015   98,34 · 94,26   [E5]
   │      └── số epoch 3 -> 15 + bật dừng sớm
   │             ▼
   │          cafebert/lora/exp064  <- exp015   98,31 · 94,20   *** LOẠI: dính mẫu OVERFIT ***
   │             └── đổi thước CHỌN MỐC  sentiment_f1 -> neg_f1_big5
   │                    ▼
   │                 cafebert/lora/exp073  <- exp064   98,52 · 94,90   [E1]   << DẪN ĐẦU
   │
   ├── tăng LoRA r 16 -> 32
   │      ▼
   │   cafebert/lora/exp013  <- exp002   98,33 · 94,14   [E6]
   │
   ├── đổi HÀM MẤT MÁT  weighted_ce -> focal (type + gamma + class_weight)
   │      ▼
   │   cafebert/lora/exp017  <- exp002   98,06 · 93,94   [E8]   << sàn lớp âm của bảng
   │
   ├── đổi BỘ TÁCH TỪ  none -> vncorenlp
   │      ▼
   │   cafebert/lora/exp008  <- exp002   98,03 · 93,66   [E9]
   │
   └── đổi KIẾN TRÚC ADAPTER  lora -> dora (use_dora: true)
          ▼
       cafebert/lora/exp019  <- exp002   97,99 · 92,96   *** NGOÀI BẢNG: hạng 10 của pool ***
```

**Thay đổi ở mỗi bước (dòng encoder):**

| Cạnh | Thay đổi (đúng 1 thông số) | Δ Accuracy | Δ `neg F1 macro (5 khía cạnh n lớn)` |
| --- | --- | ---: | ---: |
| exp001 → **exp002** | cho đầu phân loại HỌC cùng adapter | **+0,21** | **+0,36** |
| exp002 → **exp015** [E4] | tốc độ học 2e-4 → 4e-4 | **+0,47** | **+2,16** |
| exp015 → **exp021** [E2] | LoRA `r` 16 → 8 | +0,06 | −0,14 |
| exp021 → **exp055** [E7] | thước chọn mốc `sentiment_f1` → `negative_f1` | −0,29 | −0,58 |
| exp015 → **exp027** [E3] | số epoch 3 → 6 | +0,02 | −0,72 |
| exp015 → **exp020** [E5] | LoRA `r` 16 → 32 | −0,01 | −0,52 |
| exp015 → exp064 *(LOẠI: overfit)* | số epoch 3 → 15 + bật dừng sớm | −0,04 | −0,58 |
| exp064 → **exp073** [E1] | thước chọn mốc `sentiment_f1` → `neg_f1_big5` | **+0,21** | **+0,70** |
| exp002 → **exp013** [E6] | LoRA `r` 16 → 32 | **+0,45** | **+1,52** |
| exp002 → **exp017** [E8] | hàm mất mát `weighted_ce` → `focal` | +0,18 | +1,32 |
| exp002 → **exp008** [E9] | bộ tách từ `none` → `vncorenlp` | +0,15 | +1,04 |
| exp002 → exp019 *(ngoài bảng)* | adapter `lora` → `dora` | +0,11 | +0,34 |

**Đọc mục 8.1:**

1. **Đòn lớn nhất của cả cây là `lr` 2e-4 → 4e-4** (`exp002` → `exp015`): **+0,47 Accuracy** và **+2,16 lớp âm** -
   đây là **bước duy nhất vượt mức làm việc ±0,7 ở trục lớp âm**, còn ở Accuracy thì **+0,47 vẫn nằm trong biên nhiễu**.
   **Mọi đòn còn lại đều |Δ Accuracy| ≤ 0,45**; trên trục lớp âm chỉ thêm **một** đòn vượt ±0,7 là `lora.r` 32 trên
   nền `lr` 2e-4 (`exp013`: **+1,52**).
2. **`lora.r` là đòn TƯƠNG TÁC với `lr`** - đọc kỹ vì hai cột E5 và E6 cùng đòn `lora.r` nhưng **khác nền**:
   `r` 32 **giúp rõ** trên nền `lr` 2e-4 (`exp013`: **+0,45 / +1,52**) nhưng **không giúp** trên nền `lr` 4e-4
   (`exp020`: −0,01 / −0,52); còn `r` 8 trên nền 4e-4 thì **trung tính** (`exp021`: +0,06 / −0,14).
3. **Ba nhánh PHỤ - `exp055` (thước chọn mốc) / `exp017` (focal) / `exp008` (tách từ)**: `exp017` và `exp008` **hơn cha
   `exp002`** ở cả hai trục (+0,15…+0,18 / +1,04…+1,32) nhưng **kém nhánh dẫn `exp015`** (chênh **−0,29 … −0,32**
   Accuracy và **−0,84 … −1,12** lớp âm); `exp055` thì **kém chính cha `exp021`** (−0,29 / −0,58, trong biên nhiễu).
   ⇒ Cả ba đọc là **"các hướng đã thử, không vượt nhánh dẫn"**, không phải model tốt nhất.
4. **Chín cột encoder là chín cấu hình KHÁC NHAU ở CÙNG seed hiệu lực 42** ⇒ đây là **so sánh một biến**, không phải
   chọn hạt giống đẹp. Dải điểm chỉ **0,49 pp** (98,52 → 98,03) nằm trong **biên nhiễu ±0,7 pp** ⇒ **thứ hạng E1…E9
   KHÔNG phải thứ hạng cấu hình**; chỉ hai kết luận đứng vững: (a) nhánh `lr` 4e-4 hơn nhánh `lr` 2e-4 (+2,16 lớp âm -
   vượt biên; +0,47 Accuracy - trong biên), (b) phần còn lại **đồng hạng**. Lưu ý riêng: **E2 và E7 chia sẻ CÙNG một lần
   huấn luyện** (chỉ khác thước chọn mốc) nên đọc cặp này là **so hai thước chọn mốc**, không phải hai model.

### 8.2. Cây dòng LLM (Qwen3-4B + prompt CoT)

```
qwen3-4b-instruct-2507/prompt-cot/exp003  <- GỐC   97,72 · 94,52
        [prompt CoT ĐÚNG MỨC COT+1-shot của công bố; lượng hoá 4-bit; lô suy luận 8; cắt 2.304 token]
   │
   │   giảm lô suy luận 8 -> 4   (và khai dtype float16; trên GPU T4 thì mặc định "auto" vốn đã là float16)
   ▼
qwen3-4b-instruct-2507/prompt-cot/exp009  <- exp003   97,77 · 94,70   [L1]
```

| Cạnh | Thay đổi | Δ Accuracy | Δ `neg F1 macro (5 khía cạnh n lớn)` |
| --- | --- | ---: | ---: |
| exp003 → **exp009** [L1] | lô suy luận 8 → 4 | +0,05 | +0,18 |

⇒ Lượt LLM dẫn đầu **cùng cấu hình** với gốc, **chỉ khác cỡ lô**, chênh lệch **+0,05** nằm sâu trong biên nhiễu.
**Khoảng cách encoder - LLM nay là 0,75 pp** (98,52 so với 97,77) ⇒ toàn bộ lợi thế của dự án nằm ở **đường encoder**.

## 9. Hạn chế của các lượt trong bảng

Nguồn: `results/<hash8>/mispredictions.csv` của **chính từng lượt**. File này ghi mọi ô đoán sai trên **toàn bộ**
1.623 review × 7 khía cạnh = **11.361 ô**, tức **bao gồm cả ô "không nhắc tới"** - nên số ô sai ở đây **lớn hơn** số
ô sai trong các bảng 4-7 (các bảng đó chỉ tính phần đã lọc ở mục 1). Ký hiệu hướng sai: `X → Y` = ground truth `X`,
predict `Y`; `(không nhắc tới)` là ô trống.

### 9.1. Chín lượt encoder

* **E1** `cafebert/lora/exp073` - TỔNG **201** ô sai
  * sai nhiều nhất: `colour` 47 · `texture` 40 · `packing` 35
  * theo khía cạnh: colour 47 · texture 40 · packing 35 · smell 23 · shipping 23 · price 18 · stayingpower 15
  * hướng sai (top 5): (không nhắc tới) → positive = 106 · positive → (không nhắc tới) = 24 · (không nhắc tới) → negative = 23 · negative → positive = 21 · positive → negative = 20
* **E2** `cafebert/lora/exp021` - TỔNG **227** ô sai
  * sai nhiều nhất: `texture` 54 · `colour` 44 · `packing` 43
  * theo khía cạnh: texture 54 · colour 44 · packing 43 · shipping 27 · smell 21 · stayingpower 20 · price 18
  * hướng sai (top 5): (không nhắc tới) → positive = 125 · (không nhắc tới) → negative = 32 · positive → negative = 29 · positive → (không nhắc tới) = 22 · negative → positive = 15
* **E3** `cafebert/lora/exp027` - TỔNG **211** ô sai
  * sai nhiều nhất: `colour` 51 · `texture` 47 · `shipping` 31
  * theo khía cạnh: colour 51 · texture 47 · shipping 31 · packing 30 · stayingpower 20 · smell 16 · price 16
  * hướng sai (top 5): (không nhắc tới) → positive = 105 · positive → negative = 32 · (không nhắc tới) → negative = 31 · positive → (không nhắc tới) = 22 · negative → positive = 15
* **E4** `cafebert/lora/exp015` - TỔNG **219** ô sai
  * sai nhiều nhất: `texture` 55 · `colour` 44 · `packing` 35
  * theo khía cạnh: texture 55 · colour 44 · packing 35 · shipping 23 · stayingpower 21 · smell 21 · price 20
  * hướng sai (top 5): (không nhắc tới) → positive = 110 · (không nhắc tới) → negative = 38 · positive → negative = 31 · positive → (không nhắc tới) = 20 · negative → positive = 13
* **E5** `cafebert/lora/exp020` - TỔNG **230** ô sai
  * sai nhiều nhất: `texture` 54 · `colour` 49 · `packing` 40
  * theo khía cạnh: texture 54 · colour 49 · packing 40 · smell 24 · price 22 · shipping 22 · stayingpower 19
  * hướng sai (top 5): (không nhắc tới) → positive = 124 · (không nhắc tới) → negative = 35 · positive → negative = 34 · positive → (không nhắc tới) = 20 · negative → positive = 13
* **E6** `cafebert/lora/exp013` - TỔNG **249** ô sai
  * sai nhiều nhất: `texture` 62 · `colour` 53 · `packing` 40
  * theo khía cạnh: texture 62 · colour 53 · packing 40 · shipping 25 · smell 24 · stayingpower 23 · price 22
  * hướng sai (top 5): (không nhắc tới) → positive = 138 · (không nhắc tới) → negative = 39 · positive → negative = 31 · positive → (không nhắc tới) = 20 · negative → positive = 15
* **E7** `cafebert/lora/exp055` - TỔNG **225** ô sai
  * sai nhiều nhất: `texture` 55 · `colour` 46 · `packing` 36
  * theo khía cạnh: texture 55 · colour 46 · packing 36 · shipping 29 · smell 22 · stayingpower 19 · price 18
  * hướng sai (top 5): (không nhắc tới) → positive = 112 · positive → negative = 35 · (không nhắc tới) → negative = 34 · positive → (không nhắc tới) = 24 · negative → positive = 15
* **E8** `cafebert/lora/exp017` - TỔNG **199** ô sai
  * sai nhiều nhất: `colour` 48 · `texture` 42 · `shipping` 28
  * theo khía cạnh: colour 48 · texture 42 · shipping 28 · packing 23 · stayingpower 20 · smell 19 · price 19
  * hướng sai (top 5): (không nhắc tới) → positive = 92 · positive → (không nhắc tới) = 33 · negative → positive = 26 · positive → negative = 25 · negative → (không nhắc tới) = 12
* **E9** `cafebert/lora/exp008` - TỔNG **236** ô sai
  * sai nhiều nhất: `texture` 57 · `colour` 53 · `packing` 41
  * theo khía cạnh: texture 57 · colour 53 · packing 41 · shipping 25 · price 23 · smell 19 · stayingpower 18
  * hướng sai (top 5): (không nhắc tới) → positive = 124 · positive → negative = 37 · (không nhắc tới) → negative = 36 · positive → (không nhắc tới) = 19 · negative → positive = 18
* **L1** `qwen3-4b-instruct-2507/prompt-cot/exp009` - TỔNG **727** ô sai
  * sai nhiều nhất: `texture` 161 · `colour` 135 · `packing` 119
  * theo khía cạnh: texture 161 · colour 135 · packing 119 · stayingpower 107 · price 78 · smell 75 · shipping 52
  * hướng sai (top 5): positive → (không nhắc tới) = 382 · (không nhắc tới) → positive = 173 · negative → (không nhắc tới) = 62 · (không nhắc tới) → negative = 61 · positive → negative = 38


**Nhận xét chung (9 lượt encoder):**
- **Tổng ô sai: 199 - 249** (trung bình ~222) trên 11.361 ô. Lượt **sạch nhất là `E8 exp017` (199 ô)** và lượt
  **nhiều lỗi nhất là `E6 exp013` (249 ô)** - tức **"ít lỗi tổng" KHÔNG đi kèm "lớp âm tốt"**: `exp017` (đòn `focal`)
  có **ít lỗi nhất** nhưng `neg F1 (5n)` **thấp nhất bảng** (93,94) vì nó **bỏ sót khía cạnh**
  (`positive → (không nhắc tới)` 33 ô - **cao nhất trong 9 lượt encoder**).
- Kiểu sai **chủ đạo vẫn là GÁN THỪA khía cạnh**: `(không nhắc tới) → positive` chiếm **92-138 ô** trong khoảng
  199-249 ô sai. Kiểu sai này **không** nằm trong mẫu số của các bảng 4-7 (đã lọc hai chiều) nhưng là điểm yếu thật
  khi chạy thực tế.
- Ba khía cạnh sai nhiều nhất **vẫn luôn** là `texture`, `colour`, `packing` - nhóm **chủ quan**.
- Nhóm "đếm được" (`price`, `shipping`, `stayingpower`) sai **ít ô hơn**, nhưng lỗi ở `price` lại **nặng về F1** vì mẫu
  số chỉ còn **4-6 ô** (mục 9.3).
- **0/9 lượt overfit, 7/9 UNDERFIT** (mục 2.2) - đây là **điểm mạnh của bản này** so với các bản trước.

### 9.2. Lượt LLM (L1 - `qwen3-4b-instruct-2507/prompt-cot/exp009`)

1. **Sai 727 ô** - **gấp 3,7 lần** lượt encoder sạch nhất (199 ô) và **gấp 2,9 lần** lượt encoder nhiều lỗi nhất
   (249 ô). Kiểu sai **chủ đạo ngược hẳn đường encoder**: `positive → (không nhắc tới)` **382 ô** (bỏ sót khía cạnh),
   rồi `(không nhắc tới) → positive` 173 ô. Đường encoder thì **gán thừa**; đường LLM thì **bỏ sót và "im lặng"** -
   và vì ô "không nhắc tới" bị loại khỏi phần chấm, việc "im lặng" **vừa mất điểm ở đời thực vừa làm mẫu số nhỏ đi**
   (2.324 ô so với 2.724-2.748 của encoder), **không thể so tuyệt đối với encoder**.
2. **`stayingpower` yếu nhất**: Accuracy 96,15 (thấp nhất trong 7 khía cạnh của L1) và Recall lớp `positive` chỉ
   **93,70** - cũng là khía cạnh duy nhất có ô không đọc được (**4 ô**).
3. **`packing` negative chỉ F1 76,90** - thấp nhất trong 10 lượt (dù chỉ có 10 ô).
4. **`price` negative F1 60,00** - cao nhất 10 lượt, nhưng chỉ trên **4 ô**; `texture` negative P **88,70** - thấp nhất
   10 lượt (mốc công bố là 100,00).
5. **F1 lớp `positive` là 98,41**, **dưới** mốc 98,48 (−0,07) - đây là trục duy nhất L1 **không** vượt công bố.

### 9.3. Cảnh báo bắt buộc: các khía cạnh ít ô làm `macro (7)` thành thước đo NHIỄU

Hai nguồn gây nhiễu dưới đây tác động lên **nhiều khía cạnh**, không chỉ `price`:

**Bảng A - độ nhạy của từng khía cạnh** (F1 lớp `negative`; `n` = số ô ground truth):

| Khía cạnh | n ground truth | 1 ô đổi chiều làm F1 nhảy ≈ | Sai số chuẩn (nhị thức) | F1 trung bình 10 lượt |
| --- | ---: | ---: | ---: | ---: |
| `price` | 6 | 16,67 pp | 19,80 pp | 37,88 |
| `packing` | 10 | 10,00 pp | 9,71 pp | 89,45 |
| `smell` | 48 | 2,08 pp | 4,03 pp | 91,49 |
| `colour` | 54 | 1,85 pp | 4,00 pp | 90,44 |
| `texture` | 83 | 1,20 pp | 2,56 pp | 94,22 |
| `stayingpower` | 96 | 1,04 pp | 1,54 pp | 97,66 |
| `shipping` | 174 | 0,57 pp | 1,12 pp | 97,76 |


**Bảng B - vì sao `price` có 6 ô trong dữ liệu mà F1 lại tính trên 4-6 ô:** phần chấm chỉ giữ ô mà **cả** ground
truth **và** predict đều là positive/negative, nên ô model trả lời `neutral` / "không nhắc tới" / không đọc được
**bị loại khỏi mẫu số**.

| | Smell | Price | Texture | Colour | Stayingpower | Packing | Shipping |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **n ground truth** | 48 | 6 | 83 | 54 | 96 | 10 | 174 |
| E1 | 48 | 5 | 82 | 54 | 95 | 9 | 171 |
| E2 | 48 | 5 | 83 | 54 | 95 | 10 | 172 |
| E3 | 48 | 5 | 83 | 54 | 95 | 9 | 171 |
| E4 | 48 | 4 | 83 | 53 | 95 | 9 | 172 |
| E5 | 48 | 5 | 83 | 54 | 95 | 9 | 173 |
| E6 | 48 | 5 | 83 | 54 | 95 | 9 | 171 |
| E7 | 48 | 5 | 83 | 54 | 95 | 10 | 171 |
| E8 | 48 | 5 | 83 | 53 | 94 | 9 | 167 |
| E9 | 48 | 6 | 83 | 54 | 95 | 10 | 173 |
| L1 | 43 | 4 | 72 | 43 | 77 | 10 | 160 |


**Bảng C - hệ quả lên dòng `macro (7)`:**

| Lượt | n (price negative) | price F1 | packing F1 | neg F1 macro (7) | neg F1 macro (5 khía cạnh n lớn) |
| --- | ---: | ---: | ---: | ---: | ---: |
| E1 | 5 | 57,10 | 84,20 | 87,97 | 94,90 |
| E2 | 5 | 57,10 | 90,00 | 88,61 | 94,64 |
| E3 | 5 | 57,10 | 94,70 | 88,87 | 94,06 |
| E4 | 4 | 0,00 | 94,70 | 81,23 | 94,78 |
| E5 | 5 | 33,30 | 94,70 | 85,61 | 94,26 |
| E6 | 5 | 57,10 | 94,70 | 88,93 | 94,14 |
| E7 | 5 | 57,10 | 85,70 | 87,59 | 94,06 |
| E8 | 5 | 0,00 | 88,90 | 79,80 | 93,94 |
| E9 | 6 | 0,00 | 90,00 | 79,76 | 93,66 |
| L1 | 4 | 60,00 | 76,90 | 87,20 | 94,70 |


**Nhận xét mục 9.3:**
- **`price` và `packing` là nhiễu NẶNG**: một ô đổi chiều làm F1 nhảy **16,67 pp** và **10,00 pp**.
- **`smell` và `colour` cũng là nguồn nhiễu** (sai số chuẩn **4,03 pp** và **4,00 pp**, gấp ~6 lần biên nhiễu ±0,7)
  ⇒ hai thước đo "5 khía cạnh n lớn" **chỉ "đỡ nhiễu hơn" `macro (7)`**, KHÔNG sạch; chỉ `shipping` (và phần nào
  `stayingpower`) là đọc được ở mức một lượt.
- **`price` negative F1 = 0,00 ở 3/9 lượt encoder** (`E4 exp015`, `E8 exp017`, `E9 exp008`) và **khác 0,00 ở 6 lượt**
  (`E1`/`E2`/`E3`/`E6`/`E7` = 57,10; `E5` = 33,30; L1 = 60,00). Đây là **cải thiện thật so với bản `v3`** (bản đó chỉ
  3 lượt khác 0,00), nhưng **vẫn không thể coi là "đã sửa"**: mẫu số chỉ **4-6 ô**.
- **`macro (7)` KHÔNG dùng được để xếp hạng lượt**: `E6 exp013` **88,93** và `E4 exp015` **81,23** xếp trên/dưới nhau
  chỉ vì `price` negative đúng 2/5 ô hay 0/4 ô; trên thước đo có `n` thì `E1 exp073` mới là lượt dẫn đầu
  (94,90 / 95,40). Vì vậy mọi kết luận về lớp `negative` đọc theo **hai thước đo có `n`**.

## 10. Kết luận

### 10.1. Ưu điểm của công bố

1. **Rất mạnh ở nhóm khía cạnh "ngữ nghĩa rõ"**: đạt **100 %** Accuracy ở `price`, `texture` (mức 1-shot và 5-shot)
   và `stayingpower` (mức 0-shot). Trong 10 lượt, **không lượt nào đạt 100 %** ở các ô đó.
2. **Recall lớp `negative` cao**: **100,00** (`macro 5 khía cạnh n lớn`) và **98,73** (`micro theo n`) - **cả 10 lượt
   của dự án đều DƯỚI** hai mốc này. Đây là trục **duy nhất công bố thắng rõ**.
3. **F1 lớp `positive` cao**: 98,48 ở mốc đối chiếu; chỉ **E1** vượt được đáng kể (+0,61), phần còn lại vượt rất ít
   (+0,25 … +0,51), còn **L1 thì dưới** (−0,07).
4. **Không cần huấn luyện**: chỉ dùng prompt + ví dụ, chạy được với model đóng, không cần GPU riêng, không cần dữ liệu
   gán nhãn.
5. **1-shot là điểm ngọt của chính công bố**: Accuracy macro 97,36 (0-shot) → **97,70 (1-shot)** → 96,74 (5-shot) -
   thêm ví dụ **không** giúp thêm.

### 10.2. Nhược điểm của công bố

1. **Lớp `negative` yếu**: ở mốc đối chiếu, Precision lớp `negative` chỉ **66,85**, `neg F1 macro (7)` **74,20**,
   `neg F1 macro (5 khía cạnh n lớn)` **87,88**, `neg F1 micro (theo n)` **90,30**. Đây là trục dự án vượt xa nhất.
2. **Sai hẳn một khía cạnh**: F1 lớp `negative` của `price` = **0,00 ở CẢ BA mức** (0/1/5-shot) - công bố không đúng
   ô `negative` nào của `price`.
3. **Không ổn định ở `smell` negative**: F1 **66,67 → 66,67 → 50,00** khi tăng số ví dụ.
4. **Kết quả 100 % ở nhóm ít ô KHÔNG đảm bảo độ ổn định**: `price` chỉ có **6 ô** và `packing` **10 ô** ground truth;
   một ô đổi chiều làm F1 nhảy **16,67 pp** và **10,00 pp** ⇒ các ô 100 % ở hai khía cạnh này **không phải bằng chứng
   mạnh** về năng lực của model.
5. **Recall lớp `negative` cao nhưng Precision thấp**: 85,71 so với 66,85 ở mốc đối chiếu ⇒ công bố đoán rộng tay ở
   lớp `negative`; và cách đếm của công bố (chỉ tính ô mà cả ground truth và predict đều là positive/negative) khiến
   mẫu số **phụ thuộc chất lượng model**.
6. **Không đo khả năng nhận diện khía cạnh**: cách chấm chỉ chấm **sắc thái** trên các ô đã lọc hai chiều, nên **không
   trả lời được** câu "model có nhận ra khía cạnh được nhắc tới hay không"; dự án có đo phần này.
7. **Chỉ một model, không có mốc huấn luyện**: không có đối chứng encoder, nên không tách được "lợi thế thuộc model"
   hay "thuộc cách hỏi".
8. **Bảng chỉ có hai lớp**: pos/neg, **không có ô "không nhắc tới"** trong báo cáo, và bài **không nêu** cách xử lý ô
   model trả lời không đọc được - hai thứ mà dự án đo tường minh (tỉ lệ đọc được, `aspect_detection`).

### 10.3. Ưu điểm của dự án

1. **Vượt công bố ở Accuracy macro bằng encoder được huấn luyện**: 9 lượt encoder đạt **98,03 … 98,52**, tức
   **+0,33 … +0,82** so với mốc 97,70; lượt LLM **+0,07**. Mức hơn **không phụ thuộc một lượt may** (cả 9 lượt đều trên
   mốc, và **52 kết quả phân biệt** của đường encoder đều trên mốc).
2. **Vượt mạnh ở LỚP `negative` - và vượt ở PRECISION, không phải ở RECALL**:
   - Precision lớp `negative`: **77,43 … 93,37** ⇒ **+10,58 … +26,52**;
   - `neg P macro (5 khía cạnh n lớn)`: **90,40 … 94,72** ⇒ **+10,14 … +14,46**;
   - `neg P micro (theo n)`: **91,63 … 95,78** ⇒ **+7,02 … +11,17**;
   - `neg F1 macro (5 khía cạnh n lớn)`: **93,66 … 94,90** ⇒ **+5,78 … +7,02**;
   - `neg F1 micro (theo n)`: **93,77 … 95,40** ⇒ **+3,47 … +5,10**;
   - **Ngược lại, Recall lớp `negative` của dự án THẤP hơn mốc** (−1,38 … −5,18 ở macro-5; −0,50 … −4,55 ở micro),
     **nhưng `price` negative đã KHÁC 0,00 ở 6/9 lượt encoder** (bản `v3` chỉ 3 lượt).
3. **Qwen3-4B xử lý lớp `negative` tốt hơn công bố ở CẢ BA mức số ví dụ** (F1 lớp `negative` gộp 7 khía cạnh):
   `exp008` **80,59** (0-shot, công bố 74,45) · `exp009` **87,20** (1-shot, công bố 74,20) · `exp007` **82,04**
   (5-shot fp16, công bố 73,35) · `exp010` **83,20** (5-shot 4-bit).
4. **Weighted cross-entropy là bước có tác dụng THẬT**: đổi hàm mất mát từ cross-entropy thường sang weighted trên
   `phobert-base-v2/lora`: Accuracy **88,40 → 96,62**, F1 lớp `negative` gộp 7 khía cạnh **14,66 → 77,57**,
   `stayingpower` negative **5,30 → 91,50**.
5. **Đòn vượt biên nhiễu đều nằm ở "cách học"**: (a) **tăng `lr` lên 4e-4** (**+2,16** ở lớp âm - vượt biên; +0,47 ở
   Accuracy - trong biên), (b) **cho đầu phân loại học** (+0,36 lớp âm / +0,21 Accuracy - trong biên); riêng ở lớp âm
   thì `lora.r` 32 trên nền 2e-4 cũng vượt biên (**+1,52**). Núm mới nhất (`best_metric: neg_f1_big5`, +0,21 / +0,70 ở
   n = 3) sau khi nâng lên **n = 9** thì **không xác nhận** (`p = 0,463 / 0,801`) và **dự án tự rút lại kết luận** -
   điểm mạnh về phương pháp.
6. **Bảng là so sánh MỘT BIẾN ở CÙNG seed hiệu lực 42**: 9 lượt encoder là **9 cấu hình khác nhau**, mỗi cột khác cha
   **đúng một đòn** (mục 2.4 B, 8.1) - khác hẳn các bản trước, nơi bảng bị chi phối bởi các lượt **chỉ đổi seed**.
7. **Thắng ở các khía cạnh chủ quan** - nơi công bố yếu: `stayingpower` **+2,89 … +5,03** · `colour`
   **+1,14 … +2,34** · `smell` **+0,47 … +1,15** (Accuracy theo khía cạnh).
8. **Đo được thứ công bố không đo**: tỉ lệ đọc được (**100 %** ở mọi lượt trong bảng), khả năng **nhận diện khía cạnh**
   (`aspect_detection`), **số ô thật sự được tính** - nhờ đó bảng này **tự khai** được giới hạn nhiễu của chính nó
   (mục 9.3).
9. **Hạ tầng tái lập**: 174 lượt có bản ghi, `config_sha256`/`repo.sha`/`data.build` khoá từng lượt, tập đánh giá khoá
   bằng vân tay (`73d39d84…`/`af349bf5…`), MLflow/DagsHub ghi từng lượt, **76 kết quả phân biệt** để chọn mốc, và
   **quy trình lọc có thể chạy lại** (mục 2.1 ghi rõ từng bước phễu).
10. **Mọi cột đều KIỂM ĐƯỢC hội tụ** (điều kiện 6): 7/9 lượt có đường cong 3 epoch đầy đủ, 2 lượt còn lại có 4 mốc
    đo liên tiếp ⇒ **0 lượt overfit** trong bảng và **0 lượt "không kiểm được"**.

### 10.4. Nhược điểm của dự án

1. **Vẫn thua ở 3/7 khía cạnh**: `texture` **thua CẢ 6 ô** (P/R/F1 × 2 sắc thái) vì mốc của công bố là **100,00 ở cả
   6 ô** - `texture` negative Precision cao nhất của bảng chỉ **98,70** (`E1`) ⇒ **Đích #1 của Đợt 13 CHƯA đạt**;
   `price` positive (Accuracy −0,93 … −1,86; F1 −0,50 … −0,90) và `shipping` (Accuracy −0,27 … −0,68) cũng thua ở
   **cả 10 lượt**.
2. **Recall lớp `negative` vẫn DƯỚI ở cả 10 lượt** trên hai thước đo theo `n` (`neg R macro5` −1,38 … −5,18;
   `neg R micro` −0,50 … −4,55). Đường "thước thiên Recall" đã **bị đóng sau 3 lượt** (Accuracy −0,716,
   `neg F1` −2,390, `colour` Precision sụp 85,8 → 72,7) ⇒ **trục này hiện không có lối đi trong ngân sách đã thử**.
3. **`price` negative vẫn hỏng ở 3/9 lượt encoder** (`E4 exp015`, `E8 exp017`, `E9 exp008` = F1 **0,00**) và mẫu số chỉ **4-6 ô**.
4. **Nhiễu 1-2 ô vẫn chi phối một dòng của báo cáo**: `price` 16,67 pp/ô, `packing` 10,00 pp/ô; `smell`/`colour` sai
   số chuẩn ~4 pp ⇒ **`macro (7)` không dùng được để kết luận** (mục 9.3).
5. **Thứ hạng E1…E9 KHÔNG có ý nghĩa**: dải điểm chỉ **0,49 pp** (98,52 → 98,03), **nhỏ hơn biên nhiễu ±0,7**; và 9
   lượt là 9 cấu hình khác nhau ở **cùng** seed hiệu lực 42, nên khác biệt giữa cột 1 và cột 9 **không** phải "cấu hình tốt hơn".
6. **Ba cột của bảng là nhánh PHỤ (đã thử, không vượt nhánh dẫn)**: `E7` (thước chọn mốc `negative_f1`), `E8` (`focal`),
   `E9` (bộ tách từ `vncorenlp`) - `E8`/`E9` **hơn cha `exp002`** nhưng **kém nhánh dẫn** `exp015` (`lr` 4e-4: −0,29 …
   −0,32 Accuracy, −0,84 … −1,12 lớp âm), còn `E7` **kém chính cha `exp021`** (−0,29 / −0,58, trong biên nhiễu) ⇒ chúng
   có mặt vì **xếp hạng Accuracy macro**, không vì là hướng đi tốt hơn.
7. **Hai cột có bằng chứng hội tụ KHÔNG đầy đủ và một cột không tái lập**: `E1 exp073` (epoch 9-12) và `E3 exp027`
   (epoch 3-6) có **cửa sổ epoch bị cắt** do chạy tiếp từ checkpoint; `E9 exp008` dùng `segmenter: vncorenlp` - thứ tài
   liệu dự án đã xếp vào nhóm **không tái lập**.
8. **Ngân sách LLM gần như cạn**: `qwen3-8b` (đọc **0,12-1,05 %** vì chạm trần token), `mistral-7b` (60-72 %),
   `qwen3-0.6b` (21-84 %), `qwen3-4b-thinking` **huỷ vì quá chậm**; Llama-3.1-8B và Vistral-7B **chưa chạy** ⇒ chưa kết
   luận được "LLM lớn hơn có vượt encoder hay không".
9. **Lợi thế tập trung ở MỘT model**: mọi lượt trong bảng đều là **CafeBERT**; các encoder khác thấp hơn rõ (ViSoBERT
   ~95-97, PhoBERT-base 96,62, PhoBERT-large 96,32) ⇒ chưa chứng minh được "cách học LoRA + `weighted_ce` vượt công bố
   trên **mọi** encoder tiếng Việt".
10. **Nghịch lý mẫu số của L1**: lượt LLM "im lặng" nhiều hơn nên chỉ có **2.324 ô** được tính (ít hơn encoder ~420 ô) ⇒
    Accuracy macro của nó **không so tuyệt đối** với encoder; đọc sai chỗ này sẽ **thổi phồng** khoảng cách hai đường.

### 10.5. Cách diễn giải tổng thể

> **Dự án vượt công bố ở Accuracy macro và ở LỚP `negative` (ở PRECISION), nhưng thua ở 3/7 khía cạnh - nặng nhất là
> `texture` với cả 6 ô - và ở RECALL lớp `negative`.**
>
> **Lượt dẫn đầu `cafebert/lora/exp073` (E1)**: Accuracy **98,52** (+0,82), F1 lớp `positive` **99,09** (+0,61),
> `neg F1 macro (5 khía cạnh n lớn)` **94,90** (+7,02), `neg F1 micro (theo n)` **95,40** (+5,10) - dẫn đầu cả ba thước
> đo của dự án.
>
> **Lượt LLM dẫn đầu `qwen3-4b-instruct-2507/prompt-cot/exp009` (L1)**: Accuracy **97,77** (+0,07),
> `neg F1 macro (5 khía cạnh n lớn)` **94,70** (+6,82), nhưng F1 lớp `positive` **98,41** (−0,07) và **727 ô sai (gấp
> 3,7 lần encoder sạch nhất)** - tức **chỉ ngang, không vượt**; khoảng cách encoder - LLM là **0,75 pp**.
>
> **Bảng này là so sánh MỘT BIẾN và là bảng "có bằng chứng"**: 9 cột encoder = **9 cấu hình khác nhau ở cùng seed hiệu
> lực 42** (mục 2.4 B, 8.1), **0 lượt overfit**, **0 lượt không kiểm được hội tụ** (mục 2.2). Đổi lại phải khai **hai
> cảnh báo**: (a) **thứ hạng giữa 9 cột không có ý nghĩa** (dải 0,49 pp < biên nhiễu ±0,7; chỉ kết luận vững là nhánh
> `lr` 4e-4 hơn nhánh 2e-4 - và E2 ↔ E7 là **cùng một lần huấn luyện, chỉ khác thước chọn mốc**), (b) **ba cột
> `E7`/`E8`/`E9` là nhánh PHỤ: đã thử, không vượt nhánh dẫn**.

## 11. Nguồn số và quy ước

- **Số của dự án**: `experiments/**/results/<hash8>/metrics.json` - Accuracy = `scores_paper.accuracy.by_aspect`,
  Precision/Recall/F1 = `scores_paper.prf.by_aspect[<khía cạnh>][<sắc thái>]`, `n` (số ô thật sự được tính) = trường
  `support`, số ô của cả lượt = `paper.cells`, số ô không đọc được = `paper.dropped_unreadable`; `mispredictions.csv`
  cho mục 9; `model/best/trainer_state.json` (`epoch`, `step`) + `training_history.csv` cho mục 2.2-2.3.
  **KHÔNG dùng `data/reports/**`, KHÔNG dùng bất kỳ file tài liệu nào.**
- **Bộ quy tắc lọc (mục 2.1)** không đọc từ file kết quả: nó tính bằng **diff cấu hình đã hợp nhất** giữa con và cha
  (`src/experiments/experiments.py::load`, 7 lớp) và bằng **số mốc epoch** trong `training_history.csv`.
- **Số của công bố**: `data/reference_publication/accuracy_by_aspect.csv` (Table 3) và
  `prf_by_aspect_sentiment_{0,1,5}shot.csv` (Tables 4-6).
- **Mốc đối chiếu**: cột **COT+1-shot** - mức có Accuracy macro cao nhất trong ba mức (97,70). Mọi bảng delta đều trừ về
  mốc này; **không** lấy max từng ô trên 3 mức (cách đó làm ngưỡng cao giả tạo).
- **Hai dòng dẫn xuất** (`neg F1 macro (5 khía cạnh n lớn)`, `neg F1 micro (theo n)`) tính **từ chính `prf.by_aspect`**
  (F1 và `support`) - không có đường tính thứ hai; bảng Precision và Recall cũng có hai dòng tương ứng.
- **`n` trong các bảng 4-7** đếm trực tiếp trên
  `data/processed/cosmetics-ds0.2.0-pl0.2.0-srccosmetics@0.1.0-e616c1e3/test.csv` theo mã sắc thái (`1` = positive,
  `2` = negative; `3` = neutral và `0` = không nhắc tới không tính vào `n`).
- **Khoá kỹ thuật**: bài toán của mọi lượt là `label_space: binary`, `neutral_policy: drop`, `not_mentioned: separate`;
  tập đánh giá là `eval: test` với `n_samples: 1623`; cả 9 lượt encoder ở `decoding.seed = 42`.
- **Cách chẩn đoán hội tụ / mốc chọn model** (mục 2.2, 2.3) theo cách đọc đường cong huấn luyện tiêu chuẩn: Google
  Machine Learning Crash Course - *Overfitting: Interpreting loss curves* và scikit-learn - *Validation curves*.
- **Trạng thái on-disk khi viết (16/10/2026)**: **174** lượt có bản ghi; **144** lượt qua cửa 1-2-3-4; **141** lượt trên
  đúng phiên bản dữ liệu `v0.2.0`; loại tiếp **43** lượt chỉ đổi seed (**so theo giá trị hiệu lực**), **8** lượt Tier B,
  **1** lượt overfit, **9** lượt không kiểm được hội tụ ⇒ **80 lượt đủ điều kiện** ⇒ **76 kết quả phân biệt**
  (**52** encoder + 24 LLM).

### Phụ lục A - Lượt đủ điểm nhưng KHÔNG vào bảng

| Lượt | Accuracy macro | Lý do không vào bảng |
| --- | ---: | --- |
| `cafebert/lora/exp080:db6524ed` | **98,65** | **chỉ đổi `decoding.seed`** so với cha `exp074` (điều kiện 10) |
| `cafebert/lora/exp090:a5c8d52e` | 98,60 | chỉ đổi seed (`exp064`, 42→6) - *và* dính mẫu overfit |
| `cafebert/lora/exp079:282eaeb7` | 98,59 | chỉ đổi seed (`exp074`, 7→1) |
| `cafebert/lora/exp074:a7c01ccd` | 98,55 | chỉ đổi seed (`exp073`, 42→7) |
| `cafebert/lora/exp082:b07ad0b5` = `exp088:07325ac8` | 98,51 | chỉ đổi seed (`exp074`, 7→4) - *và* trùng số nhau |
| `cafebert/lora/exp075:ef3ba439` | 98,50 | chỉ đổi seed (`exp073`, 42→13) |
| `cafebert/lora/exp086:855fcd6d` | 98,45 | chỉ đổi seed (`exp064`, 42→2) |
| `cafebert/lora/exp072:218fa9ee` | 98,40 | chỉ đổi seed (`exp070`, 42→13) - *và* dính mẫu overfit |
| `cafebert/lora/exp040:49a248c4` | 98,38 | chỉ đổi seed (`exp021`, 42→7) |
| `cafebert/lora/exp045:880624f8` = `exp047:dd2a2ecd` | 98,37 | chỉ đổi seed (`exp015`, 42→13) - *và* trùng số nhau |
| `cafebert/lora/exp028:d17056e5` | 98,31 | **không kiểm được overfit**: lịch sử chỉ còn **1 dòng `epoch`** (chạy tiếp từ checkpoint) - điều kiện 6 |
| `cafebert/lora/exp064:ec7541ce` | 98,31 | **OVERFIT** (điều kiện 5); cũng là cha của `exp073` (E1) |
| `cafebert/lora/exp084:dcc6c1ed` | 98,29 | chỉ đổi seed (`exp074`, 7→6) |
| `cafebert/lora/exp058:a11f564b` | 98,28 | chỉ đổi seed (`exp002`, 42→1) |
| `cafebert/lora/exp004:43e6c243` | 98,26 | chỉ đổi seed (`exp002`, 42→7) |
| `cafebert/lora/exp030:1ce21c75` | 98,25 | **không kiểm được overfit**: lịch sử chỉ còn **1 dòng `epoch`** - điều kiện 6 |
| `cafebert/lora/exp057:36ee5314` | 98,18 | **Tier B**: `best_metric` + seed (điều kiện 11) |
| `cafebert/lora/exp012:688c32bc` | 98,14 | lịch sử huấn luyện **rỗng** ⇒ không kiểm được (điều kiện 6) |
| `cafebert/lora/exp056:bf042ab8` | 98,10 | **Tier B**: `best_metric` + seed (điều kiện 11) |
| `cafebert/lora/exp011:c5224186` | 98,05 | chạy trên **phiên bản dữ liệu `v0.3.0`** (bỏ emoji ở train/val) ⇒ để nhất quán, bảng chỉ lấy `v0.2.0` |
| `cafebert/lora/exp033:a60e9302` | 98,00 | **không kiểm được overfit**: chỉ **2 mốc epoch** (điều kiện 6) |
| `cafebert/lora/exp019:850333b8` | 97,99 | **hạng 10 của pool** ⇒ bị điều kiện 9 thay bằng lượt LLM tốt nhất; **đủ 10 điều kiện**, chỉ không đủ hạng (cột E9 của bản `v4`) |
| `cafebert/lora/exp010` | 97,95 | **hạng 11 của pool** ⇒ cùng lý do (điều kiện 9); xem `experiment_registry` |

> **Cách đọc Phụ lục A:** các lượt 98,65 · 98,60 · 98,59 · 98,55 · 98,51 · 98,50 · 98,45 · 98,40 · 98,38 · 98,37 ·
> 98,28 · 98,26 **KHÔNG bị loại vì chất lượng** - chúng là **cùng một cấu hình với cha, chạy lại ở một hạt giống khác**,
> nên con số của chúng là **ước lượng nhiễu của chính cấu hình cha**. Đó là lý do bảng chính **không** dùng chúng: nếu
> dùng, bảng sẽ bị chi phối bởi **hạt giống đẹp nhất** chứ không phải bởi phương pháp. Muốn đưa một trong các cấu hình đó
> vào bảng thì phải chạy nó với một **đòn thay đổi thật** (điều kiện 10); `exp028`/`exp030` muốn vào bảng thì phải **xoá
> thư mục kết quả và chạy lại liền mạch** để có đủ mốc epoch (điều kiện 6).

