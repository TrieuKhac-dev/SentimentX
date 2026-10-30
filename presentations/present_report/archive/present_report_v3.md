# present_report_v3 - Đối chiếu dự án với công bố tham chiếu (10 lượt dẫn đầu: 9 encoder + 1 LLM)

> ⚠️ **BẢN CŨ - đã được thay bởi [`present_report_v5.md`](present_report_v5.md)** (qua `present_report_v4.md`; bảng 10 cột
> dựng lại theo kết quả Đợt 13.1 + 13.2 **và các điều kiện lọc mới**: loại lượt **chỉ đổi `decoding.seed`** - so theo
> **giá trị hiệu lực**, loại lượt dính **overfit**, và **chỉ nhận lượt KIỂM ĐƯỢC overfit**; ngày 16/10/2026). Bảng trong
> file này là **mốc 13/10/2026** và khối ⚠️ ở mục 2.5 đã ghi rõ điều đó. Giữ file này làm **dấu vết lịch sử**, không
> dùng số của nó để báo cáo.

> ⛔ **GHI CHÚ 16/10/2026 - HAI LƯỢT ĐÃ BỊ THAY.** `cafebert/lora/exp073` (`227bfb70`) và `cafebert/lora/exp027`
> (`43e40f61`) đã được **chạy lại liền mạch**, vì bản ghi trong file này là lượt **bị ngắt phiên rồi chạy tiếp từ
> checkpoint** nên `training_history.csv` chỉ còn các epoch cuối. Hai bản cũ **bị bỏ**: `exp073` **98,52 → 98,31**;
> `exp027` **98,37 → 98,56**. Cây phát triển ở mục 8 của file này vì thế đọc `exp027` = 98,37 là **số cũ**.
> Bảng đang dùng: [`present_report_v6.md`](../present_report_v6.md).

> **BẢN MỚI NHẤT - thay thế `present_report_v2.md`, `present_report_v1.md` và `present_report_v0.md`.**
> Bản này gộp 10 lượt dẫn đầu của **toàn bộ dự án** vào MỘT bảng (9 lượt encoder + 1 lượt LLM), thêm hai cây
> phát triển, thêm mục **điều kiện lọt bảng** và **chẩn đoán chất lượng lượt chạy**, thêm mục **hạn chế từng lượt**.

> Đọc file này khi: trình bày kết quả dự án so với công bố tham chiếu, hoặc chọn model để báo cáo.
> **Nguồn số của DỰ ÁN: `experiments/**/results/<hash8>/metrics.json` khoá `scores_paper` (và `mispredictions.csv`)
> của CHÍNH từng lượt - KHÔNG lấy từ `data/reports/**`, KHÔNG lấy từ bất kỳ file tài liệu nào.**
> **Nguồn số của CÔNG BỐ: `data/reference_publication/*.csv`.**

## 0. Bản này khác các bản trước ở đâu

| Hạng mục | `present_report_v1.md` | `present_report_v3.md` (bản này) |
| --- | --- | --- |
| Số lượt trong bảng | 5 lượt MỚI của một đợt | **10 lượt dẫn đầu TOÀN dự án** (9 encoder + **1 LLM**), đã qua mục 2 |
| Mốc đối chiếu | lấy max từng chỉ số trên 3 mức theo từng khía cạnh | **một mức duy nhất**: mức COT của công bố có **Accuracy macro cao nhất** (1-shot) |
| Hai thước đo lớp negative | chỉ ở bảng F1 | có **mặt ở cả 3 bảng** Precision, Recall, F1 |
| Bảng delta | chỉ có ở một mục | **một bảng delta riêng nằm NGAY DƯỚI mỗi bảng số** |
| Điều kiện lọt bảng | không có | **có** (mục 2.1) |
| Chẩn đoán chất lượng lượt chạy (overfit / underfit / mốc chọn model) | không có | **có** (mục 2.2 và 2.3) |
| Cây phát triển | không có | **có 2 cây** (mục 8) |
| Hạn chế từng lượt | không có | **có** (mục 9) |
| Kết luận | 8 gạch đầu dòng rời | **4 mục** (mục 10) |

## 1. Quy ước đọc số

- **Cơ sở đo "paper"**: mỗi ô (review × khía cạnh) chỉ được tính khi **cả** ground truth **và** predict đều là
  `positive` hoặc `negative`. Đây là cách công bố đếm, và là cơ sở của MỌI số trong file này.
- **Tập đánh giá**: 1.623 review của tập `test` (tập test công khai của bài nguồn, giữ nguyên từng ký tự).
- **Đơn vị**: mọi chỉ số ghi theo **%**, dùng **dấu phẩy thập phân** (98,41). Chênh lệch dùng **điểm phần trăm (pp)**.
- **Mốc đối chiếu** (dùng cho mọi bảng delta): **mức COT+1-shot của công bố** - mức có **Accuracy macro cao nhất**
  trong ba mức 0/1/5-shot (97,70 so với 97,36 và 96,74). Xem bảng ở mục 4.
- **Δ** = số của lượt − mốc đối chiếu ở **đúng ô đó** (dòng `MACRO` thì so với chính dòng `MACRO` của mốc).
  **Δ dương = vượt công bố.** Delta được tính từ **hai số ĐÃ HIỂN THỊ** nên đọc lại bằng phép trừ là khớp.
- **`n`** = số ô **ground truth** của cặp (khía cạnh × sắc thái). Số này **cố định** cho mọi cột vì mọi lượt chấm
  trên cùng một tập `test`.
- **Encoder không có khái niệm số ví dụ** nên được đối chiếu với **cả ba** mức của công bố; lượt LLM đối chiếu với
  **đúng mức số ví dụ của chính nó** (LLM ở đây ở mức 1-shot, trùng mốc).
- **Biên nhiễu của đường encoder đã đo = ±0,33 … ±0,67 điểm** (đo trên các lượt chạy lại cùng cấu hình, khác seed);
  lấy mức làm việc **±0,7** - chênh lệch nhỏ hơn mức đó **KHÔNG kết luận**.
- **Hai thước đo lớp negative** (dùng vì `price` chỉ có 6 ô và `packing` 10 ô ground truth, quá ít để đọc riêng):
  - **`neg F1 macro (5 khía cạnh n lớn)`** = trung bình F1 lớp negative trên 5 khía cạnh **`colour` · `shipping` ·
    `smell` · `stayingpower` · `texture`** - đây là 5 khía cạnh có số ô ground truth negative nhiều nhất
    (54 · 174 · 48 · 96 · 83).
  - **`neg F1 micro (theo n)`** = trung bình F1 lớp negative **có trọng số bằng số ô ground truth của từng khía
    cạnh**: `smell 48 · price 6 · texture 83 · colour 54 · stayingpower 96 · packing 10 · shipping 174` (tổng 471).
    Trọng số này **giống nhau ở mọi cột** (kể cả 3 cột công bố) nên các cột so ngang được; khía cạnh nhiều ô
    (`shipping` 174 ô) nói nhiều hơn khía cạnh ít ô (`price` 6 ô), nên **không thể "ăn điểm" bằng 1-2 ô**.
  - **Bảng Precision và bảng Recall cũng có hai dòng cùng công thức nhưng tính trên chính chỉ số của bảng đó**:
    `neg P macro (5 khía cạnh n lớn)` / `neg P micro (theo n)` (bảng Precision) và
    `neg R macro (5 khía cạnh n lớn)` / `neg R micro (theo n)` (bảng Recall).

## 2. Điều kiện lọt bảng và chẩn đoán chất lượng lượt chạy

### 2.1. Điều kiện để một lượt được vào bảng

| # | Điều kiện | Cách kiểm (đã kiểm cho từng lượt) |
| --- | --- | --- |
| 1 | **Cùng tập đánh giá**: tập `test` phải là đúng tập test công khai của bài nguồn, 1.623 review | khoá tập đánh giá của phiên bản dữ liệu: vân tay **tập bản ghi** `73d39d84…` (đây là khoá, lệch là lỗi) và vân tay **byte** `af349bf5…` (lệch chỉ là ghi chú) |
| 2 | **Cùng bài toán**: chỉ hai sắc thái `positive` / `negative`; ô `neutral` bị loại khỏi phần chấm; câu hỏi "khía cạnh này có được nhắc tới hay không" là một quyết định **riêng**, không gộp vào hai sắc thái | đọc từ bản ghi của lượt |
| 3 | **Chấm trọn tập**: chấm cả 1.623 review (không chạy trên tập con, không chấm trên tập `val`) | bản ghi của lượt |
| 4 | **Đọc được kết quả**: tỉ lệ đọc được **≥ 95 %** | bản ghi của lượt |
| 5 | **Không overfit** (chẩn đoán ở mục 2.2) | đường cong huấn luyện của lượt |
| 6 | **Không trùng lặp**: hai lượt cho ra **cùng bộ 7 số Accuracy** coi là MỘT kết quả | so từng khía cạnh |
| 7 | **Xếp hạng theo Accuracy macro** (cơ sở "paper"), giảm dần | 7 số Accuracy của lượt |
| 8 | **Có ít nhất 1 lượt LLM trong 10 cột**: nếu không lượt LLM nào lọt top 10 thì **bỏ lượt encoder thứ 10**, thay bằng **lượt LLM tốt nhất** | danh sách xếp hạng |

**Kết quả áp dụng cho bản này:**
- Tổng số lượt có kết quả trên đĩa: **144**. Qua các cửa 1-2-3-4: **107** lượt.
- Sau khi **gộp trùng** (cửa 6): **100** kết quả phân biệt.
- Qua cửa 5: **1** lượt bị loại vì **overfit** (`cafebert/lora/exp042` đứng ngoài top nên không ảnh hưởng), **1** lượt
  **không chẩn đoán được** vì lịch sử huấn luyện rỗng (`cafebert/lora/exp012`, 98,14) ⇒ xếp ngoài bảng.
- Xếp theo Accuracy macro, **9 lượt đầu là encoder CafeBERT** (98,41 → 98,28); lượt encoder thứ 10 là
  `cafebert/lora/exp004` (98,26).
- **Lượt LLM tốt nhất** là `qwen3-4b-instruct-2507/prompt-cot/exp009` (97,77) ⇒ theo điều kiện 8, lượt này **thay
  cho lượt encoder thứ 10**. Bảng có **10 cột: E1…E9 + L1**.

### 2.2. Chẩn đoán hội tụ (overfit / underfit) - tách riêng khỏi việc chọn mốc model

**Phương pháp** (theo cách đọc đường cong huấn luyện tiêu chuẩn: chẩn đoán dựa trên **cặp** đường cong
train ↔ validation, không dựa trên một con số của epoch cuối):

- **Dữ liệu**: toàn bộ các mốc đo trong `results/<hash8>/training_history.csv` - `train_loss` và `val_loss` được
  ghi ở **mỗi epoch**, chỉ số chọn model tốt nhất (macro-F1 sắc thái) được ghi ở **mỗi mốc lưu checkpoint**.
- **OVERFIT** = `val_loss` **tăng liên tục ≥ 2 lần đo** trong khi `train_loss` **vẫn giảm** (mô hình bắt đầu học
  nhiễu của tập train).
- **UNDERFIT** = ở lần đo cuối, **cả** `train_loss` **và** `val_loss` **vẫn còn giảm** (mô hình chưa bão hoà).
- **HỘI TỤ** = `val_loss` đã tới đáy rồi đi ngang, khe train–val ổn định.

| Lượt | train_loss theo epoch | val_loss theo epoch | **Kết luận** |
| --- | --- | --- | --- |
| `exp021` | 0,168 → 0,036 → 0,060 | 0,1325 → 0,0882 → **0,0857** | **UNDERFIT** |
| `exp040` | 0,126 → 0,126 → 0,101 | 0,1370 → 0,1008 → **0,0820** | **UNDERFIT** |
| `exp045` | 0,301 → 0,054 → 0,232 | 0,1274 → 0,0938 → **0,0839** | **UNDERFIT** |
| `exp015` | 0,167 → 0,052 → 0,061 | 0,1273 → 0,0946 → **0,0837** | **UNDERFIT** |
| `exp020` | 0,153 → 0,112 → 0,053 | 0,1521 → 0,0994 → **0,0842** | **UNDERFIT** |
| `exp013` | 0,206 → 0,097 → 0,069 | 0,1351 → 0,1007 → **0,0866** | **UNDERFIT** |
| `exp058` | 0,274 → 0,104 → 0,056 | 0,1404 → 0,0927 → **0,0902** | **UNDERFIT** |
| `exp027` | **0,086 → 0,035 → 0,025 → 0,010** | 0,1004 → 0,0831 → **0,0812** → 0,0822 | **HỘI TỤ** (mức +0,0010 sau đáy là nhiễu) |
| `exp028` | *(lịch sử chỉ ghi 1 epoch)* | *(chỉ ghi 1 epoch)* | **không chẩn đoán được** bằng đường cong epoch; chuỗi mốc cho thấy chỉ số val đạt đỉnh 0,933 ở bước 950 rồi lùi 0,021 và hồi phục |
| `L1` (LLM) | không huấn luyện | không huấn luyện | **không áp dụng** |

**Đọc mục 2.2:**
- **Không lượt nào trong bảng bị overfit.** Mức tăng `val_loss` sau đáy lớn nhất trong bảng là **+0,0010**
  (`exp027`) - nằm trong nhiễu.
- **7/9 lượt encoder là UNDERFIT**: ở epoch cuối `val_loss` vẫn giảm ⇒ **val chưa bão hoà**. Đây là **ghi chú về dư
  địa** (còn có thể cải thiện bằng thêm epoch), **không phải lỗi** và **không loại lượt**.
- Ba lượt overfit thật đều **ngoài bảng** (điểm thấp): `cafebert/none/exp002` (val_loss 0,817 → **0,825**, Accuracy
  trên val 63,9 → **63,1**), `phobert-base-v2/lora/exp006` (0,879 → **0,931**; 48,8 → **46,0**),
  `phobert-base-v2/lora/exp007` (0,864 → **0,903**; 48,7 → **47,2**).

### 2.3. Chất lượng mốc chọn model - việc RIÊNG, không gọi là overfit

Phương pháp chọn model của dự án là lấy mốc có **chỉ số val tốt nhất** (đúng cách làm tiêu chuẩn, không phải lỗi).
Mục này kiểm **mốc được chọn nằm ở đâu** so với đáy của `val_loss`:

| Lượt | epoch của mốc được chọn | epoch có `val_loss` đáy | Vị trí |
| --- | ---: | ---: | --- |
| `exp021` · `exp040` · `exp045` · `exp015` · `exp020` · `exp013` · `exp058` | 3 | 3 | **đúng tại đáy** |
| `exp027` | **4** | 3 | **ngay sau đáy** (mức vượt đáy **+0,0010** - trong nhiễu) |
| `exp028` | 3 | *(chỉ ghi 1 epoch)* | theo chuỗi mốc: mốc được chọn **đúng đỉnh** chuỗi (0,933), sau đó chỉ số lùi 0,021 |
| `L1` (LLM) | không huấn luyện | không huấn luyện | không áp dụng |

**Đọc mục 2.3:** 9/9 lượt encoder có mốc được chọn **tại đúng đáy `val_loss`** của lượt mình, trừ `exp027` (ngay
sau đáy nhưng mức vượt chỉ 0,001). Vì vậy **không lượt nào bị loại ở mục này**; đây thuần là **cảnh báo chất lượng**.

### 2.4. Bảng tra nhãn cột

**A. Cấu hình DÙNG CHUNG cho 9 lượt encoder** (chỉ nêu cái chung; cái riêng ghi ở bảng B):

| Hạng mục | Giá trị dùng chung |
| --- | --- |
| Model nền | CafeBERT, gắn thêm adapter LoRA vào 4 module `query` · `key` · `value` · `dense` |
| Đầu phân loại | HỌC cùng adapter |
| Cách chia trọng số lớp khi huấn luyện | weighted cross-entropy, trọng số lớp = nghịch đảo tần suất |
| Hệ số LoRA | `alpha` 32, `dropout` 0,05 |
| Số epoch | 3 (trừ `exp027` dùng 6) |
| Độ dài input tối đa | 256 token |
| Chỉ số để chọn mốc model tốt nhất | macro-F1 sắc thái, đo trên tập `val` |
| Số review mỗi lô khi suy luận | 16 |

**B. Từng lượt** (số liệu lấy từ chính bản ghi của mỗi lượt):

| Nhãn | Lượt chạy | Khác cấu hình dùng chung | Tỉ lệ đọc được | **Số ô được tính** |
| --- | --- | --- | ---: | ---: |
| **E1** | `cafebert/lora/exp021:4653ddfc` | tốc độ học 4e-4, LoRA `r` = 8 | 100,00 % | 2.743 |
| **E2** | `cafebert/lora/exp040:49a248c4` | như E1, **seed 7** | 100,00 % | 2.742 |
| **E3** | `cafebert/lora/exp027:43e40f61` | tốc độ học 4e-4, LoRA `r` = 16, **6 epoch** | 100,00 % | 2.741 |
| **E4** | `cafebert/lora/exp045:880624f8` | tốc độ học 4e-4, LoRA `r` = 16, **seed 13** | 100,00 % | 2.747 |
| **E5** | `cafebert/lora/exp015:eb2b6cfa` | tốc độ học 4e-4, LoRA `r` = 16 | 100,00 % | 2.742 |
| **E6** | `cafebert/lora/exp020:2c63348a` | tốc độ học 4e-4, LoRA `r` = 32 | 100,00 % | 2.745 |
| **E7** | `cafebert/lora/exp013:bb5a16ba` | LoRA `r` = 32 (tốc độ học 2e-4, mặc định) | 100,00 % | 2.743 |
| **E8** | `cafebert/lora/exp028:d17056e5` | tốc độ học 4e-4, LoRA `r` = 16, **lưu mốc mỗi 50 bước** (mặc định 100) | 100,00 % | 2.739 |
| **E9** | `cafebert/lora/exp058:a11f564b` | **seed 1** (tốc độ học 2e-4, LoRA `r` = 16) | 100,00 % | 2.734 |
| **L1** | `qwen3-4b-instruct-2507/prompt-cot/exp009:7cf3331e` | prompt CoT **1 ví dụ**, lượng hoá 4-bit, lô suy luận 4, cắt 2.304 token (không huấn luyện) | 100,00 % | **2.324** |

**C. Ghi chú RIÊNG cho lượt L1** (không phải cấu hình dùng chung):

- L1 có **4 ô không đọc được** (đều ở khía cạnh `stayingpower`) và chỉ **2.324 ô được tính** - **ít hơn encoder
  khoảng 420 ô**. Nguyên nhân: model sinh trả lời **"không nhắc tới" nhiều hơn**, mà ô "không nhắc tới" bị loại
  khỏi phần chấm, nên mẫu số của L1 nhỏ hơn. Vì vậy điểm của L1 **không so tuyệt đối** với encoder được.

### 2.5. Đợt 13.2 (15/10/2026) - KẾT QUẢ NHÁNH và trạng thái bảng 10 lượt dẫn đầu

15 lượt `exp079`–`exp093` (B4 × seed 1…6 · B1 × seed 1…6 · R × seed 1…3) đã chạy xong: **15/15 `FINISHED`**,
`n = 1.623` review, `resume.mode = NEW`, `repo_sha = 22910c0`, dữ liệu `v0.2.0`, tỉ lệ đọc **100 %**. Số trên
`test`, cơ sở `paper`, so với **họ 12 lượt `lr 4e-4`** (**98,283** · **94,377**):

| Nhánh | n | `Accuracy macro` (sd) | Δ | `neg F1 (5n)` (sd) | Δ | Welch p (Acc / F1) | Đọc |
|---|---:|---:|---:|---:|---:|---|---|
| **B4** `best_metric: neg_f1_big5` | 9 | 98,367 (0,313) | **+0,084** | 94,491 (1,278) | **+0,114** | 0,463 / 0,801 | **KHÔNG xác nhận** - ứng viên "bàn đạp thứ 17" **bị rút lại** |
| B1 `sentiment_f1` (đối chứng) | 9 | 98,167 (0,328) | −0,116 | 94,016 (1,213) | −0,361 | 0,330 / 0,411 | nhánh đối chứng ghép cặp |
| **R** `best_metric: neg_recall_big5` | 3 | 97,567 (0,316) | −0,716 | 91,987 (1,480) | −2,390 | 0,055 / 0,105 | **ĐÓNG trục** (bán Precision quá đắt) |

Ghép cặp **cùng seed** B4 − B1 (n = 9): Acc **+0,200** `p = 0,122`, `neg F1` **+0,476** `p = 0,391`
(6/9 cặp dương). Hiệu ứng **co lại** so với n = 3 (+0,240 / +0,783) ⇒ kết quả n = 3 là **may mắn rút thăm**.

**Bằng chứng mạnh nhất:** `exp090` là lượt **B1** - thước CHỌN MỐC **CŨ** `sentiment_f1` - vẫn đạt
**98,60 / 95,76**. ⇒ Các đỉnh mới là do **hạt giống**, KHÔNG do núm chọn mốc.

**Kỷ lục LƯỢT ĐƠN mới** (luật 10: không phải kết luận về cấu hình): **`exp080` 98,65** (Accuracy macro cao
nhất của đường encoder trên `test`) và **`exp079` 95,86** (`neg F1 (5n)` cao nhất).

#### ⚠️ Bảng 10 lượt dẫn đầu (mục 2.1, 4, 5, 6, 7, 8, 9) CHƯA được dựng lại theo kết quả này

Các lượt mới **cao hơn** mọi cột encoder hiện có (E1 = `exp021` 98,41) ⇒ **9 cột encoder phải xếp lại**;
riêng `exp082`/`exp088` **trùng số** nên theo điều kiện 6 của mục 2.1 chỉ tính **MỘT** kết quả. Việc dựng lại
gồm 6 bảng (~600 ô) và phải tính lại cả mục 2.2 (chẩn đoán hội tụ) và 2.3 (chất lượng mốc) cho các cột mới -
**chưa làm ở Đợt 13.2** để KHÔNG chép tay số. Trạng thái này được khai rõ thay vì để bảng cũ đứng im:
**số của Đợt 13.2 đọc ở bảng nhánh trên; bảng 10 lượt dưới đây là của mốc 13/10/2026.**
Danh sách encoder mới (Acc macro ↓; đã loại lượt `val` `exp005`/`exp006`/`exp050`–`exp054` và đã gộp trùng):
`exp080` 98,65 · `exp090` 98,60 · `exp079` 98,59 · `exp074` 98,55 · `exp073` 98,52 · `exp082`=`exp088` 98,51 ·
`exp075` 98,50 · `exp021` 98,41 · `exp040` 98,38 · `exp027` 98,37.

## 3. Độ tin cậy theo số ô (`n`)

`n` là **số ô ground truth** trong tập `test` cho mỗi cặp (khía cạnh × sắc thái). Số này cố định cho mọi cột.

| Khía cạnh | `n` positive | `n` negative | 1 ô đổi chiều làm F1 lớp `negative` nhảy ≈ | Sai số chuẩn | Đọc F1 lớp `negative` ở dòng này |
| --- | ---: | ---: | ---: | ---: | --- |
| shipping | 334 | **174** | 0,57 pp | **1,12 pp** | **tin cậy nhất** - cũng là khía cạnh chi phối hai thước đo theo `n` |
| stayingpower | 141 | 96 | 1,04 pp | 1,52 pp | chấp nhận được |
| texture | 346 | 83 | 1,20 pp | 2,49 pp | nhiễu nhẹ |
| colour | 622 | 54 | 1,85 pp | 3,86 pp | **nhiễu** |
| smell | 252 | 48 | 2,08 pp | 4,03 pp | **nhiễu** (dòng ít ô nhất trong nhóm "nhiều ô") |
| packing | 282 | **10** | **10,00 pp** | **8,56 pp** | **rất nhiễu** |
| price | 321 | **6** | **16,67 pp** | **18,01 pp** | **rất nhiễu** |

*(Mốc so: biên nhiễu đo được của đường encoder là **±0,7 pp**; chi tiết ở mục 9.3.)*

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
**mọi bảng delta** trong file này. Các giá trị theo từng khía cạnh của mức đó:

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
| Smell | 94,59 | 96,15 | 92,86 | 97,30 | 97,64 | 96,96 | 96,96 | 96,96 | 96,95 | 96,63 | 96,96 | 96,62 | 97,44 |
| Price | 97,22 | 100,00 | 100,00 | 99,07 | 98,46 | 99,07 | 98,46 | 98,76 | 98,77 | 99,07 | 98,46 | 98,76 | 98,49 |
| Texture | 94,12 | 100,00 | 100,00 | 97,89 | 97,90 | 97,90 | 98,36 | 97,20 | 97,66 | 97,89 | 97,89 | 98,36 | 96,86 |
| Colour | 97,37 | 96,61 | 94,74 | 98,35 | 98,50 | 98,06 | 98,21 | 98,95 | 98,20 | 98,35 | 98,95 | 98,64 | 98,82 |
| Stayingpower | 100,00 | 94,12 | 92,86 | 98,31 | 98,29 | 98,72 | 98,30 | 98,30 | 98,72 | 98,30 | 97,87 | 97,87 | 96,15 |
| Packing | 98,25 | 98,11 | 100,00 | 99,31 | 99,66 | 99,65 | 99,65 | 99,65 | 99,65 | 99,66 | 99,65 | 99,30 | 97,90 |
| Shipping | 100,00 | 98,89 | 96,70 | 98,62 | 98,21 | 98,21 | 98,62 | 98,61 | 98,42 | 98,41 | 98,41 | 98,41 | 98,72 |
| **MACRO** | 97,36 | 97,70 | 96,74 | 98,41 | 98,38 | 98,37 | 98,37 | 98,35 | 98,34 | 98,33 | 98,31 | 98,28 | 97,77 |

### 4c. Delta Accuracy so với mốc đối chiếu (pp)

| Khía cạnh | CB 0-shot | CB 1-shot | CB 5-shot | E1 | E2 | E3 | E4 | E5 | E6 | E7 | E8 | E9 | L1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Smell | -1,56 | +0,00 | -3,29 | +1,15 | +1,49 | +0,81 | +0,81 | +0,81 | +0,80 | +0,48 | +0,81 | +0,47 | +1,29 |
| Price | -2,78 | +0,00 | +0,00 | -0,93 | -1,54 | -0,93 | -1,54 | -1,24 | -1,23 | -0,93 | -1,54 | -1,24 | -1,51 |
| Texture | -5,88 | +0,00 | +0,00 | -2,11 | -2,10 | -2,10 | -1,64 | -2,80 | -2,34 | -2,11 | -2,11 | -1,64 | -3,14 |
| Colour | +0,76 | +0,00 | -1,87 | +1,74 | +1,89 | +1,45 | +1,60 | +2,34 | +1,59 | +1,74 | +2,34 | +2,03 | +2,21 |
| Stayingpower | +5,88 | +0,00 | -1,26 | +4,19 | +4,17 | +4,60 | +4,18 | +4,18 | +4,60 | +4,18 | +3,75 | +3,75 | +2,03 |
| Packing | +0,14 | +0,00 | +1,89 | +1,20 | +1,55 | +1,54 | +1,54 | +1,54 | +1,54 | +1,55 | +1,54 | +1,19 | -0,21 |
| Shipping | +1,11 | +0,00 | -2,19 | -0,27 | -0,68 | -0,68 | -0,27 | -0,28 | -0,47 | -0,48 | -0,48 | -0,48 | -0,17 |
| **MACRO** | -0,34 | +0,00 | -0,96 | +0,71 | +0,68 | +0,67 | +0,67 | +0,65 | +0,64 | +0,63 | +0,61 | +0,58 | +0,07 |

**Nhận xét bảng 3:**
- **`MACRO`**: 9 lượt encoder đều **vượt mốc** (+0,58 … +0,71); lượt LLM **L1** vượt **+0,07**.
- **`smell` · `colour` · `stayingpower`**: dự án **vượt ở cả ba khía cạnh** (+0,47 … +1,49 · +1,45 … +2,34 · +3,75 … +4,60).
- **`packing`**: phần lớn lượt **vượt nhẹ** (+1,19 … +1,55); riêng **L1 dưới** (−0,21).
- **`price` và `texture`**: công bố đạt **100,00** ở mốc nên **không thể vượt** - mọi lượt của dự án đều **dưới**.
- **`shipping`**: mốc **98,89** ⇒ mọi lượt encoder đều **dưới** (−0,27 … −0,68).
- ⇒ **Lợi thế của dự án nằm ở `MACRO` và ở 3 khía cạnh `smell` / `colour` / `stayingpower`, KHÔNG nằm ở từng ô.**

## 5. Bảng 4 - Precision theo khía cạnh và sắc thái (%, cơ sở "paper")

> Hai dòng cuối là hai thước đo lớp `negative` **theo số ô**, tính trên **chính Precision** của bảng này
> (`neg P macro (5 khía cạnh n lớn)` và `neg P micro (theo n)`).

| Khía cạnh | Sắc thái | n | CB 0-shot | CB 1-shot | CB 5-shot | E1 | E2 | E3 | E4 | E5 | E6 | E7 | E8 | E9 | L1 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Smell | positive | 252 | 97,06 | 100,00 | 96,15 | 99,60 | 99,60 | 99,60 | 99,60 | 99,60 | 99,60 | 98,80 | 99,20 | 98,80 | 99,50 |
| Smell | negative | 48 | 66,67 | 50,00 | 50,00 | 87,00 | 88,70 | 85,50 | 85,50 | 85,50 | 85,50 | 86,50 | 86,80 | 86,50 | 89,40 |
| Price | positive | 321 | 100,00 | 100,00 | 100,00 | 99,10 | 98,50 | 99,10 | 98,50 | 98,80 | 98,80 | 99,10 | 98,50 | 98,80 | 99,60 |
| Price | negative | 6 | 0,00 | 0,00 | 0,00 | 100,00 | 0,00 | 100,00 | 0,00 | 0,00 | 100,00 | 100,00 | 0,00 | 0,00 | 50,00 |
| Texture | positive | 346 | 92,68 | 100,00 | 100,00 | 99,10 | 99,10 | 99,10 | 99,40 | 99,10 | 99,40 | 99,40 | 98,80 | 99,10 | 99,60 |
| Texture | negative | 83 | 100,00 | 100,00 | 100,00 | 93,00 | 93,00 | 93,00 | 94,20 | 89,90 | 91,00 | 92,00 | 94,00 | 95,20 | 88,70 |
| Colour | positive | 622 | 100,00 | 100,00 | 100,00 | 99,70 | 99,70 | 99,30 | 99,70 | 99,80 | 99,70 | 99,70 | 99,50 | 99,80 | 100,00 |
| Colour | negative | 54 | 77,78 | 75,00 | 66,67 | 85,20 | 86,70 | 84,70 | 83,90 | 89,70 | 83,90 | 85,20 | 92,60 | 86,90 | 86,00 |
| Stayingpower | positive | 141 | 100,00 | 100,00 | 100,00 | 98,60 | 98,60 | 100,00 | 99,30 | 98,60 | 99,30 | 98,60 | 98,60 | 98,60 | 98,70 |
| Stayingpower | negative | 96 | 100,00 | 80,00 | 80,00 | 97,90 | 97,90 | 96,90 | 96,90 | 97,90 | 97,90 | 97,90 | 96,90 | 96,90 | 93,80 |
| Packing | positive | 282 | 100,00 | 100,00 | 100,00 | 99,60 | 100,00 | 100,00 | 100,00 | 100,00 | 100,00 | 100,00 | 100,00 | 100,00 | 100,00 |
| Packing | negative | 10 | 66,67 | 66,67 | 100,00 | 90,00 | 90,00 | 90,00 | 90,90 | 90,00 | 90,00 | 90,00 | 90,00 | 81,80 | 62,50 |
| Shipping | positive | 334 | 100,00 | 100,00 | 96,88 | 99,10 | 99,10 | 98,80 | 99,40 | 99,40 | 99,10 | 99,10 | 99,10 | 99,10 | 99,00 |
| Shipping | negative | 174 | 100,00 | 96,30 | 96,30 | 97,70 | 96,50 | 97,10 | 97,20 | 97,10 | 97,10 | 97,10 | 97,10 | 97,10 | 98,10 |
| **MACRO** | positive |  | 98,53 | 100,00 | 99,00 | 99,26 | 99,23 | 99,41 | 99,41 | 99,33 | 99,41 | 99,24 | 99,10 | 99,17 | 99,49 |
| **MACRO** | negative |  | 73,02 | 66,85 | 70,42 | 92,97 | 78,97 | 92,46 | 78,37 | 78,59 | 92,20 | 92,67 | 79,63 | 77,77 | 81,21 |
| **neg P macro (5 khía cạnh n lớn)** |  |  | 88,89 | 80,26 | 78,59 | 92,16 | 92,56 | 91,44 | 91,54 | 92,02 | 91,08 | 91,74 | 93,48 | 92,52 | 91,20 |
| **neg P micro (theo n)** |  |  | 92,07 | 84,61 | 84,37 | 94,25 | 92,88 | 93,62 | 92,52 | 92,58 | 93,38 | 93,81 | 93,56 | 92,91 | 91,92 |

### 5b. Delta Precision so với mốc đối chiếu (pp)

| Khía cạnh | Sắc thái | n | CB 0-shot | CB 1-shot | CB 5-shot | E1 | E2 | E3 | E4 | E5 | E6 | E7 | E8 | E9 | L1 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Smell | positive | 252 | -2,94 | +0,00 | -3,85 | -0,40 | -0,40 | -0,40 | -0,40 | -0,40 | -0,40 | -1,20 | -0,80 | -1,20 | -0,50 |
| Smell | negative | 48 | +16,67 | +0,00 | +0,00 | +37,00 | +38,70 | +35,50 | +35,50 | +35,50 | +35,50 | +36,50 | +36,80 | +36,50 | +39,40 |
| Price | positive | 321 | +0,00 | +0,00 | +0,00 | -0,90 | -1,50 | -0,90 | -1,50 | -1,20 | -1,20 | -0,90 | -1,50 | -1,20 | -0,40 |
| Price | negative | 6 | +0,00 | +0,00 | +0,00 | +100,00 | +0,00 | +100,00 | +0,00 | +0,00 | +100,00 | +100,00 | +0,00 | +0,00 | +50,00 |
| Texture | positive | 346 | -7,32 | +0,00 | +0,00 | -0,90 | -0,90 | -0,90 | -0,60 | -0,90 | -0,60 | -0,60 | -1,20 | -0,90 | -0,40 |
| Texture | negative | 83 | +0,00 | +0,00 | +0,00 | -7,00 | -7,00 | -7,00 | -5,80 | -10,10 | -9,00 | -8,00 | -6,00 | -4,80 | -11,30 |
| Colour | positive | 622 | +0,00 | +0,00 | +0,00 | -0,30 | -0,30 | -0,70 | -0,30 | -0,20 | -0,30 | -0,30 | -0,50 | -0,20 | +0,00 |
| Colour | negative | 54 | +2,78 | +0,00 | -8,33 | +10,20 | +11,70 | +9,70 | +8,90 | +14,70 | +8,90 | +10,20 | +17,60 | +11,90 | +11,00 |
| Stayingpower | positive | 141 | +0,00 | +0,00 | +0,00 | -1,40 | -1,40 | +0,00 | -0,70 | -1,40 | -0,70 | -1,40 | -1,40 | -1,40 | -1,30 |
| Stayingpower | negative | 96 | +20,00 | +0,00 | +0,00 | +17,90 | +17,90 | +16,90 | +16,90 | +17,90 | +17,90 | +17,90 | +16,90 | +16,90 | +13,80 |
| Packing | positive | 282 | +0,00 | +0,00 | +0,00 | -0,40 | +0,00 | +0,00 | +0,00 | +0,00 | +0,00 | +0,00 | +0,00 | +0,00 | +0,00 |
| Packing | negative | 10 | +0,00 | +0,00 | +33,33 | +23,33 | +23,33 | +23,33 | +24,23 | +23,33 | +23,33 | +23,33 | +23,33 | +15,13 | -4,17 |
| Shipping | positive | 334 | +0,00 | +0,00 | -3,12 | -0,90 | -0,90 | -1,20 | -0,60 | -0,60 | -0,90 | -0,90 | -0,90 | -0,90 | -1,00 |
| Shipping | negative | 174 | +3,70 | +0,00 | +0,00 | +1,40 | +0,20 | +0,80 | +0,90 | +0,80 | +0,80 | +0,80 | +0,80 | +0,80 | +1,80 |
| **MACRO** | positive |  | -1,47 | +0,00 | -1,00 | -0,74 | -0,77 | -0,59 | -0,59 | -0,67 | -0,59 | -0,76 | -0,90 | -0,83 | -0,51 |
| **MACRO** | negative |  | +6,17 | +0,00 | +3,57 | +26,12 | +12,12 | +25,61 | +11,52 | +11,74 | +25,35 | +25,82 | +12,78 | +10,92 | +14,36 |
| **neg P macro (5 khía cạnh n lớn)** |  |  | +8,63 | +0,00 | -1,67 | +11,90 | +12,30 | +11,18 | +11,28 | +11,76 | +10,82 | +11,48 | +13,22 | +12,26 | +10,94 |
| **neg P micro (theo n)** |  |  | +7,46 | +0,00 | -0,24 | +9,64 | +8,27 | +9,01 | +7,91 | +7,97 | +8,77 | +9,20 | +8,95 | +8,30 | +7,31 |

**Nhận xét bảng 4:**
- **Lớp `positive`**: Precision của công bố ở mốc là **100,00** ⇒ cả 10 lượt đều **dưới** (99,10 … 99,49; Δ −0,51 … −0,90).
- **Lớp `negative` (theo từng khía cạnh)**: công bố chỉ đạt **66,85** ⇒ cả 10 lượt **vượt rất mạnh** (77,77 … 92,97; Δ **+10,92 … +26,12**), cao nhất `exp013` (E7, 92,67).
- **`neg P macro (5 khía cạnh n lớn)`**: mốc **80,26** ⇒ cả 10 lượt vượt (**+10,82 … +13,22**), cao nhất `exp028` (E8, 93,48).
- **`neg P micro (theo n)`**: mốc **84,61** ⇒ cả 10 lượt vượt (**+7,31 … +9,64**), cao nhất `exp021` (E1, 94,25).
- ⇒ **Đây là trục mạnh nhất của dự án**: Precision lớp `negative` là chỗ khoảng cách với công bố lớn nhất.

## 6. Bảng 5 - Recall theo khía cạnh và sắc thái (%, cơ sở "paper")

| Khía cạnh | Sắc thái | n | CB 0-shot | CB 1-shot | CB 5-shot | E1 | E2 | E3 | E4 | E5 | E6 | E7 | E8 | E9 | L1 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Smell | positive | 252 | 97,06 | 96,00 | 96,15 | 97,20 | 97,60 | 96,80 | 96,80 | 96,80 | 96,80 | 97,20 | 97,20 | 97,20 | 97,40 |
| Smell | negative | 48 | 66,67 | 100,00 | 50,00 | 97,90 | 97,90 | 97,90 | 97,90 | 97,90 | 97,90 | 93,80 | 95,80 | 93,80 | 97,70 |
| Price | positive | 321 | 97,22 | 100,00 | 100,00 | 100,00 | 100,00 | 100,00 | 100,00 | 100,00 | 100,00 | 100,00 | 100,00 | 100,00 | 98,90 |
| Price | negative | 6 | 0,00 | 0,00 | 0,00 | 40,00 | 0,00 | 40,00 | 0,00 | 0,00 | 20,00 | 40,00 | 0,00 | 0,00 | 75,00 |
| Texture | positive | 346 | 100,00 | 100,00 | 100,00 | 98,30 | 98,30 | 98,30 | 98,50 | 97,40 | 97,70 | 98,00 | 98,60 | 98,80 | 96,30 |
| Texture | negative | 83 | 76,92 | 100,00 | 100,00 | 96,40 | 96,40 | 96,40 | 97,60 | 96,40 | 97,60 | 97,60 | 95,10 | 96,40 | 98,60 |
| Colour | positive | 622 | 97,10 | 96,23 | 94,12 | 98,50 | 98,70 | 98,50 | 98,40 | 99,00 | 98,40 | 98,50 | 99,30 | 98,70 | 98,70 |
| Colour | negative | 54 | 100,00 | 100,00 | 100,00 | 96,30 | 96,30 | 92,60 | 96,30 | 98,10 | 96,30 | 96,30 | 94,30 | 98,10 | 100,00 |
| Stayingpower | positive | 141 | 100,00 | 92,31 | 90,00 | 98,60 | 98,60 | 97,90 | 97,90 | 98,60 | 98,60 | 98,60 | 97,90 | 97,90 | 93,70 |
| Stayingpower | negative | 96 | 100,00 | 100,00 | 100,00 | 97,90 | 97,90 | 100,00 | 98,90 | 97,90 | 98,90 | 97,90 | 97,90 | 97,90 | 98,70 |
| Packing | positive | 282 | 98,18 | 98,04 | 100,00 | 99,60 | 99,60 | 99,60 | 99,60 | 99,60 | 99,60 | 99,60 | 99,60 | 99,30 | 97,80 |
| Packing | negative | 10 | 100,00 | 100,00 | 100,00 | 90,00 | 100,00 | 100,00 | 100,00 | 100,00 | 100,00 | 100,00 | 100,00 | 100,00 | 100,00 |
| Shipping | positive | 334 | 100,00 | 98,44 | 98,41 | 98,80 | 98,20 | 98,50 | 98,50 | 98,50 | 98,50 | 98,50 | 98,50 | 98,50 | 99,00 |
| Shipping | negative | 174 | 100,00 | 100,00 | 92,86 | 98,30 | 98,20 | 97,70 | 98,80 | 98,80 | 98,30 | 98,20 | 98,20 | 98,30 | 98,10 |
| **MACRO** | positive |  | 98,51 | 97,29 | 96,95 | 98,71 | 98,71 | 98,51 | 98,53 | 98,56 | 98,51 | 98,63 | 98,73 | 98,63 | 97,40 |
| **MACRO** | negative |  | 77,66 | 85,71 | 77,55 | 88,11 | 83,81 | 89,23 | 84,21 | 84,16 | 87,00 | 89,11 | 83,04 | 83,50 | 95,44 |
| **neg R macro (5 khía cạnh n lớn)** |  |  | 88,72 | 100,00 | 88,57 | 97,36 | 97,34 | 96,92 | 97,90 | 97,82 | 97,80 | 96,76 | 96,26 | 96,90 | 98,62 |
| **neg R micro (theo n)** |  |  | 91,26 | 98,73 | 90,99 | 96,69 | 96,36 | 96,69 | 97,00 | 96,79 | 97,07 | 96,66 | 95,69 | 96,19 | 98,23 |

### 6b. Delta Recall so với mốc đối chiếu (pp)

| Khía cạnh | Sắc thái | n | CB 0-shot | CB 1-shot | CB 5-shot | E1 | E2 | E3 | E4 | E5 | E6 | E7 | E8 | E9 | L1 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Smell | positive | 252 | +1,06 | +0,00 | +0,15 | +1,20 | +1,60 | +0,80 | +0,80 | +0,80 | +0,80 | +1,20 | +1,20 | +1,20 | +1,40 |
| Smell | negative | 48 | -33,33 | +0,00 | -50,00 | -2,10 | -2,10 | -2,10 | -2,10 | -2,10 | -2,10 | -6,20 | -4,20 | -6,20 | -2,30 |
| Price | positive | 321 | -2,78 | +0,00 | +0,00 | +0,00 | +0,00 | +0,00 | +0,00 | +0,00 | +0,00 | +0,00 | +0,00 | +0,00 | -1,10 |
| Price | negative | 6 | +0,00 | +0,00 | +0,00 | +40,00 | +0,00 | +40,00 | +0,00 | +0,00 | +20,00 | +40,00 | +0,00 | +0,00 | +75,00 |
| Texture | positive | 346 | +0,00 | +0,00 | +0,00 | -1,70 | -1,70 | -1,70 | -1,50 | -2,60 | -2,30 | -2,00 | -1,40 | -1,20 | -3,70 |
| Texture | negative | 83 | -23,08 | +0,00 | +0,00 | -3,60 | -3,60 | -3,60 | -2,40 | -3,60 | -2,40 | -2,40 | -4,90 | -3,60 | -1,40 |
| Colour | positive | 622 | +0,87 | +0,00 | -2,11 | +2,27 | +2,47 | +2,27 | +2,17 | +2,77 | +2,17 | +2,27 | +3,07 | +2,47 | +2,47 |
| Colour | negative | 54 | +0,00 | +0,00 | +0,00 | -3,70 | -3,70 | -7,40 | -3,70 | -1,90 | -3,70 | -3,70 | -5,70 | -1,90 | +0,00 |
| Stayingpower | positive | 141 | +7,69 | +0,00 | -2,31 | +6,29 | +6,29 | +5,59 | +5,59 | +6,29 | +6,29 | +6,29 | +5,59 | +5,59 | +1,39 |
| Stayingpower | negative | 96 | +0,00 | +0,00 | +0,00 | -2,10 | -2,10 | +0,00 | -1,10 | -2,10 | -1,10 | -2,10 | -2,10 | -2,10 | -1,30 |
| Packing | positive | 282 | +0,14 | +0,00 | +1,96 | +1,56 | +1,56 | +1,56 | +1,56 | +1,56 | +1,56 | +1,56 | +1,56 | +1,26 | -0,24 |
| Packing | negative | 10 | +0,00 | +0,00 | +0,00 | -10,00 | +0,00 | +0,00 | +0,00 | +0,00 | +0,00 | +0,00 | +0,00 | +0,00 | +0,00 |
| Shipping | positive | 334 | +1,56 | +0,00 | -0,03 | +0,36 | -0,24 | +0,06 | +0,06 | +0,06 | +0,06 | +0,06 | +0,06 | +0,06 | +0,56 |
| Shipping | negative | 174 | +0,00 | +0,00 | -7,14 | -1,70 | -1,80 | -2,30 | -1,20 | -1,20 | -1,70 | -1,80 | -1,80 | -1,70 | -1,90 |
| **MACRO** | positive |  | +1,22 | +0,00 | -0,34 | +1,42 | +1,42 | +1,22 | +1,24 | +1,27 | +1,22 | +1,34 | +1,44 | +1,34 | +0,11 |
| **MACRO** | negative |  | -8,05 | +0,00 | -8,16 | +2,40 | -1,90 | +3,52 | -1,50 | -1,55 | +1,29 | +3,40 | -2,67 | -2,21 | +9,73 |
| **neg R macro (5 khía cạnh n lớn)** |  |  | -11,28 | +0,00 | -11,43 | -2,64 | -2,66 | -3,08 | -2,10 | -2,18 | -2,20 | -3,24 | -3,74 | -3,10 | -1,38 |
| **neg R micro (theo n)** |  |  | -7,47 | +0,00 | -7,74 | -2,04 | -2,37 | -2,04 | -1,73 | -1,94 | -1,66 | -2,07 | -3,04 | -2,54 | -0,50 |

**Nhận xét bảng 5:**
- **Lớp `positive`**: Recall của công bố là **97,29** ⇒ cả 10 lượt **vượt** (97,40 … 98,73; Δ +0,11 … +1,44).
- **Lớp `negative` (theo từng khía cạnh)**: mốc **85,71** ⇒ **6 lượt vượt** (cao nhất `L1` **95,44**, Δ +9,73; rồi `exp013` 89,11, Δ +3,40) nhưng **4 lượt dưới** (`exp058` −2,21 · `exp015` −1,55 · `exp045` −1,50 · `exp040` −1,90 · `exp028` −2,67).
- **`neg R macro (5 khía cạnh n lớn)`**: mốc **100,00** ⇒ **CẢ 10 lượt đều DƯỚI** (96,26 … 98,62; Δ **−1,38 … −3,74**).
- **`neg R micro (theo n)`**: mốc **98,73** ⇒ **cả 10 lượt đều dưới** (95,69 … 98,23; Δ **−0,50 … −3,04**).
- ⇒ **Kết luận quan trọng:** ở hai thước đo theo số ô, dự án **KHÔNG** bắt được nhiều ô `negative` hơn công bố - Recall lớp `negative` của dự án **thấp hơn**. Vậy lợi thế lớp `negative` ở bảng 6 đến từ **Precision** (khi đã đoán `negative` thì đoán đúng hơn), **không** phải từ việc đoán rộng hơn.

## 7. Bảng 6 - F1 theo khía cạnh và sắc thái (%, cơ sở "paper")

Đây là **bảng điểm chính để so với công bố**. Hai dòng cuối là hai thước đo lớp `negative` theo số ô (mục 3).

| Khía cạnh | Sắc thái | n | CB 0-shot | CB 1-shot | CB 5-shot | E1 | E2 | E3 | E4 | E5 | E6 | E7 | E8 | E9 | L1 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Smell | positive | 252 | 97,06 | 97,06 | 96,15 | 98,40 | 98,60 | 98,20 | 98,20 | 98,20 | 98,20 | 98,00 | 98,20 | 98,00 | 98,40 |
| Smell | negative | 48 | 66,67 | 66,67 | 50,00 | 92,20 | 93,10 | 91,30 | 91,30 | 91,30 | 91,30 | 90,00 | 91,10 | 90,00 | 93,30 |
| Price | positive | 321 | 98,59 | 100,00 | 100,00 | 99,50 | 99,20 | 99,50 | 99,20 | 99,40 | 99,40 | 99,50 | 99,20 | 99,40 | 99,20 |
| Price | negative | 6 | 0,00 | 0,00 | 0,00 | 57,10 | 0,00 | 57,10 | 0,00 | 0,00 | 33,30 | 57,10 | 0,00 | 0,00 | 60,00 |
| Texture | positive | 346 | 96,20 | 100,00 | 100,00 | 98,70 | 98,70 | 98,70 | 99,00 | 98,20 | 98,50 | 98,70 | 98,70 | 99,00 | 97,90 |
| Texture | negative | 83 | 86,96 | 100,00 | 100,00 | 94,70 | 94,70 | 94,70 | 95,90 | 93,00 | 94,20 | 94,70 | 94,50 | 95,80 | 93,40 |
| Colour | positive | 622 | 98,53 | 98,08 | 96,97 | 99,10 | 99,20 | 98,90 | 99,00 | 99,40 | 99,00 | 99,10 | 99,40 | 99,30 | 99,40 |
| Colour | negative | 54 | 87,50 | 85,71 | 80,00 | 90,40 | 91,20 | 88,50 | 89,70 | 93,70 | 89,70 | 90,40 | 93,50 | 92,20 | 92,50 |
| Stayingpower | positive | 141 | 100,00 | 96,00 | 94,74 | 98,60 | 98,60 | 98,90 | 98,60 | 98,60 | 98,90 | 98,60 | 98,20 | 98,20 | 96,10 |
| Stayingpower | negative | 96 | 100,00 | 88,89 | 88,89 | 97,90 | 97,90 | 98,40 | 97,90 | 97,90 | 98,40 | 97,90 | 97,40 | 97,40 | 96,20 |
| Packing | positive | 282 | 99,08 | 99,01 | 100,00 | 99,60 | 99,80 | 99,80 | 99,80 | 99,80 | 99,80 | 99,80 | 99,80 | 99,60 | 98,90 |
| Packing | negative | 10 | 80,00 | 80,00 | 100,00 | 90,00 | 94,70 | 94,70 | 95,20 | 94,70 | 94,70 | 94,70 | 94,70 | 90,00 | 76,90 |
| Shipping | positive | 334 | 100,00 | 99,21 | 94,74 | 99,00 | 98,60 | 98,60 | 98,90 | 98,90 | 98,80 | 98,80 | 98,80 | 98,80 | 99,00 |
| Shipping | negative | 174 | 100,00 | 98,11 | 94,55 | 98,00 | 97,40 | 97,40 | 98,00 | 98,00 | 97,70 | 97,70 | 97,70 | 97,70 | 98,10 |
| **MACRO** | positive |  | 98,49 | 98,48 | 97,51 | 98,99 | 98,96 | 98,94 | 98,96 | 98,93 | 98,94 | 98,93 | 98,90 | 98,90 | 98,41 |
| **MACRO** | negative |  | 74,45 | 74,20 | 73,35 | 88,61 | 81,29 | 88,87 | 81,14 | 81,23 | 85,61 | 88,93 | 81,27 | 80,44 | 87,20 |
| **neg F1 macro (5 khía cạnh n lớn)** |  |  | 88,23 | 87,88 | 82,69 | 94,64 | 94,86 | 94,06 | 94,56 | 94,78 | 94,26 | 94,14 | 94,84 | 94,62 | 94,70 |
| **neg F1 micro (theo n)** |  |  | 91,17 | 90,30 | 87,06 | 95,24 | 94,58 | 94,92 | 94,67 | 94,60 | 94,77 | 95,01 | 94,61 | 94,48 | 94,82 |

### 7b. Delta F1 so với mốc đối chiếu (pp)

| Khía cạnh | Sắc thái | n | CB 0-shot | CB 1-shot | CB 5-shot | E1 | E2 | E3 | E4 | E5 | E6 | E7 | E8 | E9 | L1 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Smell | positive | 252 | +0,00 | +0,00 | -0,91 | +1,34 | +1,54 | +1,14 | +1,14 | +1,14 | +1,14 | +0,94 | +1,14 | +0,94 | +1,34 |
| Smell | negative | 48 | +0,00 | +0,00 | -16,67 | +25,53 | +26,43 | +24,63 | +24,63 | +24,63 | +24,63 | +23,33 | +24,43 | +23,33 | +26,63 |
| Price | positive | 321 | -1,41 | +0,00 | +0,00 | -0,50 | -0,80 | -0,50 | -0,80 | -0,60 | -0,60 | -0,50 | -0,80 | -0,60 | -0,80 |
| Price | negative | 6 | +0,00 | +0,00 | +0,00 | +57,10 | +0,00 | +57,10 | +0,00 | +0,00 | +33,30 | +57,10 | +0,00 | +0,00 | +60,00 |
| Texture | positive | 346 | -3,80 | +0,00 | +0,00 | -1,30 | -1,30 | -1,30 | -1,00 | -1,80 | -1,50 | -1,30 | -1,30 | -1,00 | -2,10 |
| Texture | negative | 83 | -13,04 | +0,00 | +0,00 | -5,30 | -5,30 | -5,30 | -4,10 | -7,00 | -5,80 | -5,30 | -5,50 | -4,20 | -6,60 |
| Colour | positive | 622 | +0,45 | +0,00 | -1,11 | +1,02 | +1,12 | +0,82 | +0,92 | +1,32 | +0,92 | +1,02 | +1,32 | +1,22 | +1,32 |
| Colour | negative | 54 | +1,79 | +0,00 | -5,71 | +4,69 | +5,49 | +2,79 | +3,99 | +7,99 | +3,99 | +4,69 | +7,79 | +6,49 | +6,79 |
| Stayingpower | positive | 141 | +4,00 | +0,00 | -1,26 | +2,60 | +2,60 | +2,90 | +2,60 | +2,60 | +2,90 | +2,60 | +2,20 | +2,20 | +0,10 |
| Stayingpower | negative | 96 | +11,11 | +0,00 | +0,00 | +9,01 | +9,01 | +9,51 | +9,01 | +9,01 | +9,51 | +9,01 | +8,51 | +8,51 | +7,31 |
| Packing | positive | 282 | +0,07 | +0,00 | +0,99 | +0,59 | +0,79 | +0,79 | +0,79 | +0,79 | +0,79 | +0,79 | +0,79 | +0,59 | -0,11 |
| Packing | negative | 10 | +0,00 | +0,00 | +20,00 | +10,00 | +14,70 | +14,70 | +15,20 | +14,70 | +14,70 | +14,70 | +14,70 | +10,00 | -3,10 |
| Shipping | positive | 334 | +0,79 | +0,00 | -4,47 | -0,21 | -0,61 | -0,61 | -0,31 | -0,31 | -0,41 | -0,41 | -0,41 | -0,41 | -0,21 |
| Shipping | negative | 174 | +1,89 | +0,00 | -3,56 | -0,11 | -0,71 | -0,71 | -0,11 | -0,11 | -0,41 | -0,41 | -0,41 | -0,41 | -0,01 |
| **MACRO** | positive |  | +0,01 | +0,00 | -0,97 | +0,51 | +0,48 | +0,46 | +0,48 | +0,45 | +0,46 | +0,45 | +0,42 | +0,42 | -0,07 |
| **MACRO** | negative |  | +0,25 | +0,00 | -0,85 | +14,41 | +7,09 | +14,67 | +6,94 | +7,03 | +11,41 | +14,73 | +7,07 | +6,24 | +13,00 |
| **neg F1 macro (5 khía cạnh n lớn)** |  |  | +0,35 | +0,00 | -5,19 | +6,76 | +6,98 | +6,18 | +6,68 | +6,90 | +6,38 | +6,26 | +6,96 | +6,74 | +6,82 |
| **neg F1 micro (theo n)** |  |  | +0,87 | +0,00 | -3,24 | +4,94 | +4,28 | +4,62 | +4,37 | +4,30 | +4,47 | +4,71 | +4,31 | +4,18 | +4,52 |

**Nhận xét bảng 6:**
- **`MACRO positive`**: mốc 98,48 ⇒ **9/10 lượt vượt** (+0,42 … +0,51), riêng **L1 dưới (−0,07)**.
- **`MACRO negative` (7 khía cạnh)**: mốc 74,20 ⇒ cả 10 lượt vượt (+6,24 … +14,73). **Nhưng dòng này bị `price`
  và `packing` chi phối** (xem cảnh báo ở mục 9.3).
- **`neg F1 macro (5 khía cạnh n lớn)`** - thước đo **đáng tin**: mốc 87,88 ⇒ cả 10 lượt vượt
  (**+6,18 … +6,98**), cao nhất `exp040` (94,86).
- **`neg F1 micro (theo n)`**: mốc 90,30 ⇒ cả 10 lượt vượt (**+4,18 … +4,94**), cao nhất `exp021` (95,24).
- **Theo từng khía cạnh**: dự án **vượt ở cả `smell`, `colour`, `stayingpower`** (cả hai sắc thái) nhưng **thua ở
  `price` positive, `texture` (cả hai sắc thái) và `shipping` (cả hai sắc thái)** - vì công bố đã đạt mức tuyệt đối
  hoặc rất cao ở các ô đó. `packing` thì chia đôi (positive: phần lớn vượt; negative: chỉ L1 dưới).
- **Không lượt nào thắng công bố ở cả 7 khía cạnh** (mức cao nhất là **4/7**, ví dụ `exp021` thắng `smell`, `colour`,
  `stayingpower`, `packing`).

## 8. Hai cây phát triển của các lượt trong bảng

Cây lấy quan hệ **cha – con** từ file cấu hình của từng thí nghiệm, và **thay đổi ở mỗi cạnh** được tính bằng cách
so **cấu hình đã hợp nhất** (7 lớp: model + 5 lớp dùng chung + lớp thí nghiệm) của con với của cha. Mỗi cạnh chỉ
đổi **MỘT** thông số. Số cạnh mỗi nút là **Accuracy macro · `neg F1 macro (5 khía cạnh n lớn)`** (cơ sở "paper").

### 8.1. Cây dòng ENCODER (CafeBERT + LoRA)

```
cafebert/lora/exp001   <- GỐC          97,67 · 92,26   [CafeBERT + weighted cross-entropy; đầu phân loại ĐÓNG BĂNG]
   │
   │   cho đầu phân loại HỌC cùng adapter
   ▼
cafebert/lora/exp002   <- exp001      97,88 · 92,62   *** BASELINE của mọi nhánh dưới ***
   │
   ├── tăng tốc độ học 2e-4 -> 4e-4
   │      ▼
   │   cafebert/lora/exp015   <- exp002   98,35 · 94,78   [E5]
   │      ├── giảm LoRA r 16 -> 8
   │      │      ▼
   │      │   cafebert/lora/exp021  <- exp015   98,41 · 94,64   [E1]   << DẪN ĐẦU
   │      │      └── đổi seed 42 -> 7
   │      │             ▼
   │      │          cafebert/lora/exp040  <- exp021   98,38 · 94,86   [E2]
   │      ├── tăng số epoch 3 -> 6
   │      │      ▼
   │      │   cafebert/lora/exp027  <- exp015   98,37 · 94,06   [E3]
   │      ├── tăng LoRA r 16 -> 32
   │      │      ▼
   │      │   cafebert/lora/exp020  <- exp015   98,34 · 94,26   [E6]
   │      ├── đổi seed 42 -> 13
   │      │      ▼
   │      │   cafebert/lora/exp045  <- exp015   98,37 · 94,56   [E4]
   │      └── lưu mốc model mỗi 100 -> 50 bước
   │             ▼
   │          cafebert/lora/exp028  <- exp015   98,31 · 94,84   [E8]
   │
   ├── tăng LoRA r 16 -> 32
   │      ▼
   │   cafebert/lora/exp013  <- exp002   98,33 · 94,14   [E7]
   │
   ├── đổi seed 42 -> 1
   │      ▼
   │   cafebert/lora/exp058  <- exp002   98,28 · 94,62   [E9]
   │
   └── đổi seed 42 -> 7
          ▼
       cafebert/lora/exp004  <- exp002   98,26 · 94,32   (hạng 10 của encoder ⇒ ngoài bảng, xem mục 2.1)
```

**Thay đổi ở mỗi bước (dòng encoder):**

| Cạnh | Thay đổi (đúng 1 thông số) | Δ Accuracy | Δ `neg F1 macro (5 khía cạnh n lớn)` |
| --- | --- | ---: | ---: |
| exp001 → **exp002** | cho đầu phân loại HỌC cùng adapter | **+0,21** | **+0,36** |
| exp002 → **exp015** [E5] | tốc độ học 2e-4 → 4e-4 | **+0,47** | **+2,16** |
| exp015 → **exp021** [E1] | LoRA `r` 16 → 8 | +0,06 | −0,14 |
| exp021 → **exp040** [E2] | seed 42 → 7 | −0,03 | +0,22 |
| exp015 → **exp027** [E3] | số epoch 3 → 6 | +0,02 | −0,72 |
| exp015 → **exp020** [E6] | LoRA `r` 16 → 32 | −0,01 | −0,52 |
| exp015 → **exp045** [E4] | seed 42 → 13 | +0,02 | −0,22 |
| exp015 → **exp028** [E8] | lưu mốc model mỗi 100 → 50 bước | −0,04 | +0,06 |
| exp002 → **exp013** [E7] | LoRA `r` 16 → 32 | +0,45 | +1,52 |
| exp002 → **exp058** [E9] | seed 42 → 1 | +0,40 | +2,00 |
| exp002 → exp004 | seed 42 → 7 | +0,38 | +1,70 |

**Chỉ HAI bước là cải tiến vượt biên nhiễu (±0,7):** cho **đầu phân loại học** và **tăng tốc độ học lên 4e-4**.
Mọi bước còn lại (đổi LoRA `r`, số epoch, mật độ lưu mốc, seed) đều **|Δ Accuracy| ≤ 0,06** ⇒ **đồng hạng trong biên
nhiễu**; chúng chỉ khác nhau ở các thước đo lớp `negative` (và cả những khác biệt đó cũng nhỏ hơn 1 điểm).

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

⇒ Lượt LLM dẫn đầu là **cùng một cấu hình** với gốc, **chỉ khác cỡ lô**, và chênh lệch **+0,05** nằm sâu trong biên
nhiễu. Đây là lý do toàn bộ lợi thế của dự án nằm ở **đường encoder**.

## 9. Hạn chế của các lượt trong bảng

Nguồn: `results/<hash8>/mispredictions.csv` của **chính từng lượt**. File này ghi mọi ô đoán sai trên **toàn bộ**
1.623 review × 7 khía cạnh = **11.361 ô**, tức **bao gồm cả ô "không nhắc tới"** - nên số ô sai ở đây **lớn hơn** số
ô sai trong các bảng 4-7 (các bảng đó chỉ tính phần đã lọc ở mục 1). Ký hiệu hướng sai: `X → Y` = ground truth `X`,
predict `Y`; ô trống là "không nhắc tới"; "không đọc được" = model không trả về sắc thái đọc được cho ô đó.

### 9.1. Chín lượt encoder

**E1 `exp021`** - 227 ô sai
- 3 khía cạnh sai nhiều nhất: `texture` 54 · `colour` 44 · `packing` 43.
- Hướng sai lớn nhất: `"không nhắc tới" → positive` **125** ô (gán khía cạnh cho review KHÔNG nhắc tới).
- Hạn chế: hay "thấy khía cạnh" quá mức; `price` negative chỉ đúng **2/5 ô** (F1 57,10); thua công bố ở `stayingpower` và `shipping`; **underfit** (mục 2.2).

**E2 `exp040`** - 224 ô sai
- 3 khía cạnh sai nhiều nhất: `texture` 54 · `colour` 50 · `packing` 35.
- Hướng sai lớn nhất: `"không nhắc tới" → positive` **122** ô.
- Hạn chế: `price` negative **sai hết** (F1 **0,00**, 5 ô); `colour` negative Precision chỉ 86,70; **underfit** (mục 2.2).
**E3 `exp027`** - 211 ô sai
- 3 khía cạnh sai nhiều nhất: `colour` 51 · `texture` 47 · `shipping` 31.
- Hướng sai lớn nhất: `"không nhắc tới" → positive` **105** ô.
- Hạn chế: `colour` negative yếu nhất bảng (Precision 84,70); `shipping` sai 31 ô; mốc model được chọn ở epoch 4 (**ngay sau đáy `val_loss`**, xem mục 2.3).

**E4 `exp045`** - 227 ô sai
- 3 khía cạnh sai nhiều nhất: `colour` 55 · `texture` 50 · `packing` 41.
- Hướng sai lớn nhất: `"không nhắc tới" → positive` **127** ô.
- Hạn chế: `price` negative F1 **0,00**; `colour` negative Precision 83,90 - **thấp nhất bảng**; **underfit** (mục 2.2).

**E5 `exp015`** - 219 ô sai
- 3 khía cạnh sai nhiều nhất: `texture` 55 · `colour` 44 · `packing` 35.
- Hướng sai lớn nhất: `"không nhắc tới" → positive` **110** ô.
- Hạn chế: `texture` negative Precision chỉ 89,90; `price` negative F1 **0,00**; **underfit** (mục 2.2).
**E6 `exp020`** - 230 ô sai
- 3 khía cạnh sai nhiều nhất: `texture` 54 · `colour` 49 · `packing` 40.
- Hướng sai lớn nhất: `"không nhắc tới" → positive` **124** ô.
- Hạn chế: `price` negative Recall chỉ **20 %** (1/5 ô); `smell` negative sai 24 ô; **underfit** (mục 2.2).

**E7 `exp013`** - **249** ô sai (nhiều nhất bảng)
- 3 khía cạnh sai nhiều nhất: `texture` **62** · `colour` 53 · `packing` 40.
- Hướng sai lớn nhất: `"không nhắc tới" → positive` **138** ô.
- Hạn chế: sai nhiều ô nhất trong 9 lượt; `texture` negative sai nhiều nhất (62 ô).
- Ghi chú: đứng đầu `neg F1 macro (7)` **chỉ vì** `price` negative đúng 2/5 ô (xem mục 9.3).

**E8 `exp028`** - **208** ô sai (ít nhất bảng)
- 3 khía cạnh sai nhiều nhất: `colour` 46 · `texture` 45 · `packing` 30.
- Hướng sai lớn nhất: `"không nhắc tới" → positive` **111** ô.
- Hạn chế: vẫn gán thừa khía cạnh nhiều; `price` negative F1 **0,00**; lịch sử huấn luyện **chỉ ghi 1 epoch** nên **không chẩn đoán được hội tụ** bằng đường cong epoch (mục 2.2).

**E9 `exp058`** - 223 ô sai
- 3 khía cạnh sai nhiều nhất: `texture` 51 · `colour` 48 · `packing` 34.
- Hướng sai lớn nhất: `"không nhắc tới" → positive` **112** ô.
- Hạn chế: `packing` negative Precision chỉ 81,80 - thấp nhất bảng; `price` negative F1 **0,00**; **underfit** (mục 2.2).

**Nhận xét chung:**
- Kiểu sai **chủ đạo là GÁN THỪA khía cạnh**: `"không nhắc tới" → positive` chiếm **105-138 ô** trong khoảng 208-249 ô sai.
- Kiểu sai này **không** nằm trong mẫu số của các bảng 4-7 (đã lọc hai chiều) nhưng là điểm yếu thật khi chạy thực tế.
- Ba khía cạnh sai nhiều nhất **luôn** là `texture`, `colour`, `packing` - nhóm **chủ quan**.
- Nhóm "đếm được" (`price`, `shipping`, `stayingpower`) sai **ít ô hơn**, nhưng lỗi ở `price` lại **nặng về F1** vì chỉ có **4-5 ô** trong phần được tính (xem mục 9.3).
- **Không lượt nào overfit**; 9 lượt encoder đều **UNDERFIT** hoặc **HỘI TỤ** (mục 2.2).

### 9.2. Lượt LLM (L1 - `qwen3-4b-instruct-2507/prompt-cot/exp009`)

| Hạng mục | Số | Ý nghĩa |
| --- | ---: | --- |
| Tổng ô sai | **727** | **gấp ~3,2 lần** mức sai của encoder (208-249) |
| `positive → "không nhắc tới"` (bỏ sót khía cạnh positive) | **382** | kiểu sai **LỚN NHẤT** - nói "không nhắc tới" trong khi review CÓ nhắc |
| `negative → "không nhắc tới"` | 62 | bỏ sót cả lớp negative |
| `"không nhắc tới" → positive` | 173 | gán thừa khía cạnh |
| `"không nhắc tới" → negative` | 61 | gán thừa khía cạnh |
| `positive → negative` | 38 | đảo sắc thái |
| `negative → positive` | 7 | đảo sắc thái |
| Ô **không đọc được** | **4** (đều ở `stayingpower`) | ô không có sắc thái đọc được |
| Khía cạnh sai nhiều nhất | texture 161 · colour 135 · packing 119 · **stayingpower 107** | trải rộng hơn encoder (encoder chỉ ~18-23 ô `stayingpower`) |
| **Số ô được tính** | **2.324** | **ít hơn encoder ~420 ô** (2.734-2.747) |

**Hạn chế riêng của L1:**
1. **Bỏ sót khía cạnh rất nhiều** (444 ô `positive`/`negative` → "không nhắc tới") ⇒ mẫu số của L1 teo còn 2.324 ô.
   Điểm của L1 vì thế **cao lên một phần do nhiều ô khó bị loại khỏi mẫu số**, không thể so tuyệt đối với encoder.
2. **`stayingpower` yếu nhất**: Accuracy 96,15 (thấp nhất trong 7 khía cạnh của L1) và Recall lớp `positive` chỉ
   93,70 - cũng là khía cạnh duy nhất có ô không đọc được.
3. **`packing` negative chỉ F1 76,90** - thấp nhất trong 10 lượt (dù chỉ có 10 ô).
4. **F1 lớp `positive` là 98,41**, **dưới** mốc 98,48 (−0,07) - đây là trục duy nhất L1 **không** vượt công bố.

### 9.3. Cảnh báo bắt buộc: các khía cạnh ít ô làm `macro (7)` thành thước đo NHIỄU

Có **hai** nguồn gây nhiễu, và chúng tác động lên **nhiều khía cạnh**, không chỉ `price`:

**Bảng A - độ nhạy của từng khía cạnh** (F1 lớp `negative`; `n` = số ô **ground truth**):

| Khía cạnh | `n` ground truth | 1 ô đổi chiều làm F1 nhảy ≈ | Sai số chuẩn (nhị thức) | F1 trung bình | Mức nhiễu |
| --- | ---: | ---: | ---: | ---: | --- |
| `price` | 6 | **16,67 pp** | **18,01 pp** | 26,5 | **rất nhiễu** |
| `packing` | 10 | **10,00 pp** | **8,56 pp** | 92,0 | **rất nhiễu** |
| `smell` | 48 | **2,08 pp** | **4,03 pp** | 91,5 | **nhiễu** |
| `colour` | 54 | 1,85 pp | 3,86 pp | 91,2 | **nhiễu** |
| `texture` | 83 | 1,20 pp | 2,49 pp | 94,6 | nhiễu nhẹ |
| `stayingpower` | 96 | 1,04 pp | 1,52 pp | 97,7 | chấp nhận được |
| `shipping` | 174 | 0,57 pp | 1,12 pp | 97,8 | **tin cậy nhất** |

*Mốc so: biên nhiễu đo được của đường encoder là **±0,7 pp**.*

**Bảng B - vì sao `price` có 6 ô trong dữ liệu mà F1 lại tính trên 4-5 ô:** phần chấm chỉ giữ ô mà **cả** ground
truth **và** predict đều là positive/negative, nên ô model trả lời `neutral` / "không nhắc tới" / không đọc được
**bị loại khỏi mẫu số**.

| | smell | **price** | texture | colour | stayingpower | **packing** | shipping |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **`n` ground truth** (cột `n` của bảng 4-7) | 48 | **6** | 83 | 54 | 96 | **10** | 174 |
| 9 lượt encoder (số ô **thật sự được tính**) | 48 | **4-5** | 82-83 | 53-54 | 94-95 | 9-10 | 170-173 |
| L1 | 43 | **4** | 72 | 43 | 77 | 10 | 160 |

⇒ Mẫu số của **cùng một khía cạnh khác nhau giữa các lượt** ⇒ ở nhóm ít ô, điểm **không so tuyệt đối** giữa các lượt.

**Bảng C - hệ quả lên dòng `macro (7)`:**

| Lượt | `n` (`price` negative) | `price` F1 | `packing` F1 | `neg F1 macro (7)` | `neg F1 macro (5 khía cạnh n lớn)` |
| --- | ---: | ---: | ---: | ---: | ---: |
| E1 | 5 | **57,10** | 90,00 | 88,61 | 94,64 |
| E2 | 5 | **0,00** | 94,70 | 81,29 | **94,86** |
| E3 | 5 | **57,10** | 94,70 | 88,87 | 94,06 |
| E4 | 5 | **0,00** | 95,20 | 81,14 | 94,56 |
| E5 | 4 | **0,00** | 94,70 | 81,23 | 94,78 |
| E6 | 5 | 33,30 | 94,70 | 85,61 | 94,26 |
| E7 | 5 | **57,10** | 94,70 | **88,93** | 94,14 |
| E8 | 5 | **0,00** | 94,70 | 81,27 | 94,84 |
| E9 | 4 | **0,00** | 90,00 | 80,44 | 94,62 |
| L1 | 4 | **60,00** | **76,90** | 87,20 | 94,70 |

**Nhận xét mục 9.3:**
- **`price` và `packing` là nhiễu NẶNG**: một ô đổi chiều làm F1 nhảy **16,67 pp** và **10,00 pp**.
- **`smell` và `colour` cũng là nguồn nhiễu**, không chỉ `price`: sai số chuẩn **4,03 pp** và **3,86 pp**, tức **gấp ~5-6 lần biên nhiễu ±0,7**.
- ⇒ Hai thước đo "5 khía cạnh n lớn" **vẫn chứa `smell` và `colour`**, nên chúng chỉ **"đỡ nhiễu hơn" `macro (7)`** chứ **không sạch**; chỉ `shipping` (và phần nào `stayingpower`) là đọc được ở mức một lượt.
- ⇒ **E7 đứng đầu `neg F1 macro (7)` (88,93) chỉ vì `price` negative đúng 2/5 ô**; trên `neg F1 macro (5 khía cạnh n lớn)` E7 (94,14) **thua** E2 (94,86), E5 (94,78) và E1 (94,64). Vì vậy mọi kết luận về lớp `negative` đọc theo **hai thước đo có `n`**, KHÔNG đọc theo `macro (7)`.

## 10. Kết luận

### 10.1. Ưu điểm của công bố

1. **Rất mạnh ở nhóm khía cạnh "ngữ nghĩa rõ"**: đạt **100 %** Accuracy ở `price`, `texture` (mức 1-shot và 5-shot)
   và `stayingpower` (mức 0-shot). Trong 10 lượt, **không lượt nào đạt 100 %** ở các ô đó.
2. **F1 lớp `positive` cao**: 98,48 ở mốc đối chiếu; chỉ **1 trong 10 lượt** vượt được (E1, +0,51), phần còn lại vượt
   rất ít (+0,42 … +0,48) hoặc kém hơn (L1, −0,07).
3. **Không cần huấn luyện**: chỉ dùng prompt + ví dụ, chạy được với model đóng, không cần GPU riêng, không cần dữ liệu
   gán nhãn.
4. **1-shot là điểm ngọt của chính công bố**: Accuracy macro 97,36 (0-shot) → **97,70 (1-shot)** → 96,74 (5-shot) -
   thêm ví dụ **không** giúp thêm.

### 10.2. Nhược điểm của công bố

1. **Lớp `negative` yếu**: ở mốc đối chiếu, Precision lớp `negative` chỉ **66,85**, `neg F1 macro (7)` **74,20**,
   `neg F1 macro (5 khía cạnh n lớn)` **87,88**, `neg F1 micro (theo n)` **90,30**. Đây là trục dự án vượt xa nhất.
2. **Sai hẳn một khía cạnh**: F1 lớp `negative` của `price` = **0,00 ở CẢ BA mức** (0/1/5-shot) - công bố không đúng
   ô `negative` nào của `price`.
3. **Không ổn định ở `smell` negative**: F1 **66,67 → 66,67 → 50,00** khi tăng số ví dụ.
4. **Kết quả 100 % ở nhóm ít ô KHÔNG đảm bảo độ ổn định**: `price` chỉ có **6 ô** và `packing` **10 ô** ground truth;
   một ô đổi chiều làm F1 nhảy **16,67 pp** và **10,00 pp**. Vì vậy các ô 100 % ở hai khía cạnh này **không phải
   bằng chứng mạnh** về năng lực của model.
5. **Recall lớp `negative` cao nhưng Precision thấp**: 85,71 so với 66,85 ở mốc đối chiếu ⇒ công bố đoán rộng tay ở
   lớp `negative`; và cách đếm của công bố (chỉ tính ô mà cả ground truth và predict đều là positive/negative)
   khiến mẫu số **phụ thuộc chất lượng model**.
6. **Không đo khả năng nhận diện khía cạnh**: cách chấm chỉ chấm **sắc thái** trên các ô đã lọc hai chiều, nên
   **không trả lời được** câu "model có nhận ra khía cạnh được nhắc tới hay không"; dự án có đo phần này.
7. **Chỉ một model, không có mốc huấn luyện**: không có đối chứng encoder, nên không tách được "lợi thế thuộc model"
   hay "thuộc cách hỏi".

### 10.3. Ưu điểm của dự án

1. **Vượt công bố ở Accuracy macro bằng encoder được huấn luyện**: 9 lượt encoder đạt **98,28 … 98,41**, tức
   **+0,58 … +0,71** so với mốc 97,70; lượt LLM **+0,07**. Mức hơn **không phụ thuộc một lượt may** (cả 9 lượt đều trên
   mốc).
2. **Vượt mạnh ở LỚP `negative` - và vượt ở PRECISION, không phải ở RECALL**:
   - Precision lớp `negative`: **77,77 … 92,97** ⇒ **+10,92 … +26,12**;
   - `neg P macro (5 khía cạnh n lớn)`: **91,08 … 93,48** ⇒ **+10,82 … +13,22**;
   - `neg P micro (theo n)`: **91,92 … 94,25** ⇒ **+7,31 … +9,64**;
   - `neg F1 macro (5 khía cạnh n lớn)`: **94,06 … 94,86** ⇒ **+6,18 … +6,98**;
   - `neg F1 micro (theo n)`: **94,48 … 95,24** ⇒ **+4,18 … +4,94**;
   - **Ngược lại, Recall lớp `negative` của dự án THẤP hơn mốc** (−1,38 … −3,74 ở macro-5; −0,50 … −3,04 ở micro)
     và F1 lớp `negative` của `price` **không còn 0,00** ở nhiều lượt (E1/E3/E7 = 57,10; L1 = 60,00).
3. **Qwen3-4B xử lý lớp `negative` tốt hơn công bố ở CẢ BA mức số ví dụ** (F1 lớp `negative` gộp 7 khía cạnh):
   `exp008` **80,59** (0-shot, công bố 74,45) · `exp009` **87,20** (1-shot, công bố 74,20) · `exp007` **82,04**
   (5-shot fp16, công bố 73,35) · `exp010` **83,20** (5-shot 4-bit).
4. **Weighted cross-entropy là bước có tác dụng THẬT** (không phải suy đoán): đổi hàm mất mát từ cross-entropy thường
   sang weighted (trọng số lớp nghịch đảo tần suất) trên `phobert-base-v2/lora`: Accuracy **88,40 → 96,62**,
   F1 lớp `negative` gộp 7 khía cạnh **14,66 → 77,57**, `stayingpower` negative **5,30 → 91,50**.
5. **Thắng ở 4/7 khía cạnh về Accuracy**: `smell` (**+0,47 … +1,49**), `colour` (**+1,45 … +2,34**), `stayingpower`
   (**+3,75 … +4,60**) và `packing` (+1,19 … +1,55 ở phần lớn lượt). Thua ở 3 khía cạnh: `price`, `texture`, `shipping`.
6. **Đo được độ tin cậy của số**: dự án có nhiều lượt độc lập và đã **đo biên nhiễu** (±0,33 … ±0,67), nên phân biệt
   được "hơn thật" với "đồng hạng", và biết khía cạnh nào đọc được (mục 3, 9.3) - điều công bố không có.
7. **Mẫu số lớn và đọc được 100 %**: mọi lượt encoder đọc được **100 %** và giữ **2.734-2.747 ô** được tính; mọi lượt
   đều có **chẩn đoán hội tụ** và **kiểm mốc chọn model** (mục 2.2, 2.3) nên biết rõ số đang đọc là số của model nào.
8. **Cơ sở chấm trên TOÀN BỘ ô ngăn việc tăng điểm bằng cách kiêng trả lời** - có bằng chứng cụ thể: cặp
   `qwen3-4b…/prompt-cot/exp007` (5 ví dụ, fp16) vs `exp010` (5 ví dụ, 4-bit): theo cơ sở "paper" thì **96,48 vs 97,19**
   nhưng bản 4-bit chỉ giữ **2.375 ô** (so với **2.520 ô**); đổi sang cơ sở toàn bộ ô thì **đảo chiều: 94,31 > 93,39**.
   ⇒ điểm "paper" cao hơn có thể chỉ vì **nhiều ô khó bị loại khỏi mẫu số**.

### 10.4. Nhược điểm của dự án

1. **Thua ở 3/7 khía cạnh**: `price` và `texture` (công bố đạt **100 %** nên không thể vượt) và `shipping` (mốc
   98,89). **Lợi thế của dự án nằm ở macro, không nằm ở từng khía cạnh**; không lượt nào thắng cả 7 khía cạnh
   (cao nhất **4/7**).
2. **Cả 10 lượt trong bảng chỉ thuộc HAI họ cấu hình** (CafeBERT `lr 4e-4` và CafeBERT `lr 2e-4`), và **9 lượt
   encoder là anh em của nhau** (khác seed hoặc một thông số nhỏ) ⇒ **đồng hạng**, không phải 9 hướng độc lập. Mục 8
   cho thấy **chỉ 2 bước** (cho đầu phân loại học; tăng tốc độ học lên 4e-4) tạo khác biệt thật.
3. **Lượt LLM dẫn đầu không vượt được lớp `positive`**: L1 có F1 lớp `positive` 98,41 < 98,48 (−0,07); độ hơn
   Accuracy chỉ **+0,07** (trong biên nhiễu) và mẫu số của L1 **nhỏ hơn ~420 ô**. **Đường LLM hiện không dẫn đầu.**
4. **7/9 lượt encoder là UNDERFIT** (mục 2.2): ở epoch cuối `val_loss` vẫn giảm ⇒ **còn dư địa**, nhưng thử tăng lên
   6 epoch (`exp027`) cho kết quả **đi ngang** (val_loss chỉ nhích +0,0010) ⇒ dư địa nằm ở nút khác, không phải
   "thêm epoch".
5. **Lớp `negative` ở nhóm ít ô vẫn nhiễu**: F1 lớp `negative` của `price` dao động **0,00 ↔ 60,00** trên 4-5 ô;
   `packing` trên 9-10 ô. Đây là hạn chế **của dữ liệu**, không phải của model, và dự án chưa có cách xử lý.
6. **Một số hướng đã thử và KHÔNG vượt**: các bước kết hợp (ensemble nhiều model, biểu quyết nhiều mẫu, ngưỡng theo
   khía cạnh, router theo khía cạnh, gộp hai tầng, chọn mốc theo lớp `negative`) đều **âm hoặc rỗng**; `focal loss`
   cũng kém; nhánh fine-tune toàn bộ **thoái hoá** (dự đoán "không nhắc tới" cho mọi ô).
7. **Chưa thử hết dải model**: `qwen3-8b` và `mistral-7b` **hỏng định dạng** (đọc được 0,12-1,05 % và 60-72 %);
   `qwen3-4b-thinking` **huỷ vì quá chậm**; Llama-3.1-8B và Vistral-7B **chưa chạy** ⇒ chưa kết luận được "LLM lớn
   hơn có vượt encoder hay không".

### 10.5. Cách diễn giải tổng thể

> **Dự án vượt công bố ở Accuracy macro và ở LỚP `negative`, nhưng thua ở 3/7 khía cạnh mà công bố đã đạt mức tuyệt
> đối.**
>
> **Lượt dẫn đầu `cafebert/lora/exp021` (E1)**: Accuracy **98,41** (+0,71), F1 lớp `positive` **98,99** (+0,51),
> `neg F1 macro (5 khía cạnh n lớn)` **94,64** (+6,76), `neg F1 micro (theo n)` **95,24** (+4,94).
>
> **Lượt LLM dẫn đầu `qwen3-4b-instruct-2507/prompt-cot/exp009` (L1)**: Accuracy **97,77** (+0,07),
> `neg F1 macro (5 khía cạnh n lớn)` **94,70** (+6,82), nhưng F1 lớp `positive` **98,41** (−0,07) - tức **chỉ ngang,
> không vượt**.
>
> **Phần lớn bảng là ĐỒNG HẠNG**: 9 lượt encoder là anh em của hai cấu hình gốc, khác nhau ở seed hoặc một thông số
> nhỏ (mục 8). Khi báo cáo phải ghi rõ **số lượt độc lập**, không đếm số thư mục.

## 11. Nguồn số và quy ước

- **Số của dự án**: `experiments/**/results/<hash8>/metrics.json` - Accuracy = `scores_paper.accuracy.by_aspect`,
  Precision/Recall/F1 = `scores_paper.prf.by_aspect[<khía cạnh>][<sắc thái>]`, `n` = trường `support`;
  và `mispredictions.csv` cho mục 9. **KHÔNG dùng `data/reports/**`, KHÔNG dùng bất kỳ file tài liệu nào.**
- **Số của công bố**: `data/reference_publication/accuracy_by_aspect.csv` (Table 3) và
  `prf_by_aspect_sentiment_{0,1,5}shot.csv` (Tables 4-6).
- **Mốc đối chiếu**: cột **COT+1-shot** - mức có Accuracy macro cao nhất trong ba mức (97,70). Mọi bảng delta đều
  trừ về mốc này; **không** lấy max từng ô trên 3 mức (cách đó làm ngưỡng cao giả tạo).
- **Hai dòng dẫn xuất** (`neg F1 macro (5 khía cạnh n lớn)`, `neg F1 micro (theo n)`) tính **từ chính `prf.by_aspect`**
  (F1 và `support`) - không có đường tính thứ hai.
- **`n` trong các bảng 4-7** đếm trực tiếp trên `data/processed/cosmetics-ds0.2.0-pl0.2.0-srccosmetics@0.1.0-e616c1e3/test.csv`
  theo mã sắc thái (`1` = positive, `2` = negative; `3` = neutral và `0` = không nhắc tới không tính vào `n`).
- **Khoá kỹ thuật** (để tra cứu, không cần để đọc bảng): bài toán của mọi lượt là `label_space: binary`,
  `neutral_policy: drop`, `not_mentioned: separate`; tập đánh giá là `eval: test` với `n_samples: 1623`.
- **Cách chẩn đoán hội tụ / mốc chọn model** (mục 2.2, 2.3) theo cách đọc đường cong huấn luyện tiêu chuẩn:
  Google Machine Learning Crash Course - *Overfitting: Interpreting loss curves* ("validation loss tách khỏi training
  loss ⇒ model đang overfit") và scikit-learn - *Validation curves* ("training score và validation score cùng thấp ⇒
  underfitting; training score cao mà validation score thấp ⇒ overfitting").
- **Trạng thái on-disk khi viết**: 144 lượt có bản ghi; **107** lượt qua cửa 1-2-3-4; **100** kết quả phân biệt;
  **1** lượt overfit (ngoài bảng); **1** lượt không chẩn đoán được (`exp012`).

### Phụ lục A - Lượt đủ điểm nhưng KHÔNG vào bảng

| Lượt | Accuracy macro | Lý do |
| --- | ---: | --- |
| `cafebert/lora/exp012:688c32bc` | 98,14 | lịch sử huấn luyện **rỗng** (0 dòng) ⇒ **không chẩn đoán được** overfit/underfit |
| `cafebert/lora/exp004:43e6c243` | 98,26 | hạng **10** của encoder ⇒ theo điều kiện 8, bị **lượt LLM tốt nhất thay** (không phải vì chất lượng) |
| `cafebert/lora/exp030:1ce21c75` | 98,25 | hạng **11** của encoder |
| `cafebert/lora/exp042:5a6882ac` | 98,24 | **overfit**: `val_loss` tăng +0,0034 ở epoch 3 rồi giảm tiếp, và chuỗi chỉ số val **dịch mức xuống** ở cuối lượt |

> Hai lượt `exp004` và `exp030` **không** bị loại vì chất lượng: chúng chỉ **xếp sau** 9 lượt encoder trong bảng nên
> không còn chỗ (bảng chỉ có 10 cột và đã dành 1 cột cho lượt LLM).
