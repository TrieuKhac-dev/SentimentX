# Phân tích kết quả 17 lượt và hướng phát triển tiếp

> Đọc file này khi: báo cáo kết quả các lượt đã chạy và chọn việc làm tiếp theo.
> Liên quan: `presentations/experiment_rationale.md`, `docs/04_experiments/08_experiment_rationale.md`,
> `data/reports/metrics_matrix/`

Mọi số dưới đây là **cơ sở `paper`** (cách công bố đếm: chỉ giữ ô mà CẢ nhãn đúng và nhãn đoán là
positive/negative), trên split `test` 1.623 review; riêng §3 ghi rõ là cơ sở `all`. **Luôn đọc kèm số ô**:
bản 4-bit trả lời ít hơn 5–6% số ô so với bản fp16, nên điểm cao hơn một phần là nhờ **kiêng trả lời**.

> **Cập nhật 09/10/2026:** tệp này là bản phân tích của **17 lượt** có kết quả tại thời điểm **04/10/2026**.
> Sau đó repo đã có nhiều lượt nữa - đo trên đĩa ngày 09/10/2026 là **61 thư mục kết quả có `metrics.json`**
> (xem Bảng B trong `docs/04_experiments/01_models.md`). Các bảng số dưới đây vẫn là **mốc so với công bố
> của 17 lượt đó**; số của các lượt mới nằm ở `data/reports/metrics_matrix/`, sinh bằng
> `python scripts/collect_reports.py`.

17 lượt chia thành bốn nhóm:

- **nhóm B - Qwen3-4B hỏi bằng prompt (9 lượt)**: 4-bit lô 8 = `exp002/003/004`; fp16 lô 4 =
  `exp005/006/007`; 4-bit lô 4 = `exp008/009/010`. Ba lượt trong mỗi bộ là ba **mức ví dụ 0 / 1 / 5**;
  `exp008/009/010` là cặp đối chứng **sạch một biến** (chỉ khác lượng hoá) của `exp005/006/007`.
- **nhánh E - ba biến thể bộ 1 ví dụ (3 lượt)**: `exp011` (ví dụ có nhãn âm), `exp012` (thêm bước quét phàn
  nàn), `exp013` (lưu ý lệch nhãn) - mỗi lượt khác `exp003` đúng một thứ.
- **nhánh F (1 lượt)**: `prompt-one-turn/exp001` (bỏ suy luận từng bước).
- **nhóm A - encoder học LoRA (4 lượt)**: `phobert-base-v2/lora/exp001` và `exp002`,
  `visobert/lora/exp001` và `exp002` (`exp002` = `exp001` + `weighted_ce`/`inverse`).

## 1. Accuracy theo khía cạnh

### 1.1 Nhóm prompt: ba mức ví dụ × ba cấu hình sinh, so với công bố

| Khía cạnh       | CB 0  | CB 1  | CB 5  | 4-bit l8 0 | 4-bit l8 1 | 4-bit l8 5 | fp16 l4 0 | fp16 l4 1 | fp16 l4 5 | 4-bit l4 0 | 4-bit l4 1 | 4-bit l4 5 |
| --------------- | ----- | ----- | ----- | ---------- | ---------- | ---------- | --------- | --------- | --------- | ---------- | ---------- | ---------- |
| colour          | 97,37 | 96,61 | 94,74 | 97,66      | 98,81      | 96,56      | 97,41     | 98,27     | 96,92     | 97,67      | **98,82**  | 96,56      |
| packing         | 98,25 | 98,11 | 100,0 | 97,91      | 97,89      | 97,89      | 97,21     | 98,26     | 98,26     | 97,90      | 97,90      | 97,89      |
| price           | 97,22 | 100,0 | 100,0 | 96,25      | 98,49      | 98,07      | 95,86     | 98,20     | 97,37     | 96,25      | 98,49      | 98,45      |
| shipping        | 100,0 | 98,89 | 96,70 | 97,50      | 98,51      | 97,74      | 98,16     | 98,12     | 96,72     | 97,51      | 98,72      | 97,94      |
| smell           | 94,59 | 96,15 | 92,86 | 95,29      | 97,01      | 96,09      | 96,17     | 95,08     | 95,67     | 95,26      | **97,44**  | 96,09      |
| stayingpower    | 100,0 | 94,12 | 92,86 | 97,83      | 96,15      | 97,37      | 94,54     | 92,50     | 94,61     | **98,54**  | 96,15      | 97,37      |
| texture         | 94,12 | 100,0 | 100,0 | 97,66      | 97,17      | 96,07      | 96,96     | 95,80     | 95,83     | 97,67      | 96,86      | 96,06      |
| **Trung bình**  | 97,36 | 97,70 | 96,74 | 97,16      | 97,72      | 97,11      | 96,62     | 96,60     | 96,48     | 97,26      | **97,77**  | 97,19      |
| Lệch so công bố | -     | -     | -     | −0,20      | +0,02      | +0,37      | −0,74     | −1,10     | −0,26     | −0,10      | **+0,07**  | +0,45      |
| Số ô            | -     | -     | -     | 2.415      | 2.315      | 2.378      | 2.580     | 2.461     | 2.520     | 2.414      | 2.324      | 2.375      |

(`CB` = công bố; `l8` = lô 8, `l4` = lô 4.) Đỉnh của cả 17 lượt là **`exp009` 97,77** - hơn công bố 0,07 điểm,
tức **nằm trong nhiễu của một lần chạy greedy**, không phải "vượt công bố".

### 1.2 Nhóm encoder và lượt "một lượt"

| Khía cạnh    | Một lượt | PhoBERT gốc | PhoBERT `weighted_ce` | ViSoBERT gốc | ViSoBERT `weighted_ce` |
| ------------ | -------- | ----------- | --------------------- | ------------ | ---------------------- |
| colour       | 96,68    | 92,27       | 96,41                 | 93,84        | 94,68                  |
| packing      | 97,93    | 96,83       | **99,65**             | 96,88        | 97,56                  |
| price        | 97,79    | 98,45       | 98,14                 | 98,43        | 98,44                  |
| shipping     | 95,10    | 98,19       | 98,02                 | 97,18        | 96,95                  |
| smell        | 96,19    | 84,48       | 95,92                 | 92,47        | 93,84                  |
| stayingpower | 91,12    | **64,71**   | 92,67                 | 90,04        | 93,51                  |
| texture      | 92,52    | 83,86       | 95,55                 | 95,16        | 94,30                  |
| **Trung bình** | 95,33  | 88,40       | **96,62**             | 94,86        | 95,61                  |
| Số ô         | 2.663    | 2.665       | 2.736                 | 2.688        | 2.701                  |

**Đảo thứ hạng**: ở lượt gốc, ViSoBERT hơn PhoBERT **6,46 điểm**; sau `weighted_ce`, PhoBERT (96,62) vượt
ViSoBERT (95,61) **1,01 điểm** ⇒ thứ hạng phụ thuộc **hàm mất mát**, không chỉ model.

## 2. F1 theo LỚP

Hai chỉ số trả lời hai câu khác nhau, đo ở hai cơ sở khác nhau - trộn lại là sai:

| Chỉ số                | Trả lời câu gì                                      | Cơ sở đo                                                     |
| --------------------- | --------------------------------------------------- | ------------------------------------------------------------ |
| F1 lớp âm / lớp dương | khía cạnh ĐÃ được nhắc thì chọn đúng sắc thái chưa  | `paper` (chỉ ô mà cả nhãn đúng và nhãn đoán là positive/negative) |
| phát hiện khía cạnh   | model có NHẬN RA khía cạnh được nhắc hay không      | `all` (còn cả ô "không nhắc tới"), scorer `aspect_detection` |

### 2.1 F1 lớp ÂM - nhóm prompt (so thẳng với Tables 4-6 của công bố)

| Khía cạnh    | CB 0   | CB 1   | CB 5   | 4-bit l4 0 | 4-bit l4 1 | 4-bit l4 5 | fp16 l4 0 | fp16 l4 1 | fp16 l4 5 | 4-bit l8 0 | 4-bit l8 1 | 4-bit l8 5 |
| ------------ | ------ | ------ | ------ | ---------- | ---------- | ---------- | --------- | --------- | --------- | ---------- | ---------- | ---------- |
| colour       | 0,875  | 0,8571 | 0,800  | 0,860      | **0,925**  | 0,817      | 0,847     | 0,897     | 0,828     | 0,860      | 0,923      | 0,817      |
| packing      | 0,800  | 0,800  | 1,000  | 0,750      | 0,769      | 0,750      | 0,692     | 0,783     | 0,783     | 0,769      | 0,750      | 0,750      |
| price        | 0,000  | 0,000  | 0,000  | 0,267      | 0,600      | 0,500      | **0,435** | 0,545     | 0,462     | 0,267      | 0,600      | 0,444      |
| shipping     | 1,000  | 0,9811 | 0,9455 | 0,963      | 0,981      | 0,970      | 0,972     | 0,972     | 0,951     | 0,963      | 0,978      | 0,967      |
| smell        | 0,6667 | 0,6667 | 0,500  | 0,874      | **0,933**  | 0,907      | 0,893     | 0,874     | 0,880     | 0,874      | 0,923      | 0,905      |
| stayingpower | 1,000  | 0,8889 | 0,8889 | **0,981**  | 0,962      | 0,970      | 0,933     | 0,921     | 0,937     | 0,972      | 0,962      | 0,970      |
| texture      | 0,8696 | 1,000  | 1,000  | 0,946      | 0,934      | 0,910      | 0,930     | 0,909     | 0,902     | 0,945      | 0,940      | 0,910      |

### 2.2 F1 lớp ÂM - ba biến thể, lượt "một lượt" và bốn lượt encoder

| Khía cạnh    | `exp011` (ví dụ âm) | `exp012` (quét phàn nàn) | `exp013` (lưu ý lệch) | Một lượt | PhoBERT gốc | PhoBERT `weighted_ce` | ViSoBERT gốc | ViSoBERT `weighted_ce` |
| ------------ | ------------------- | ------------------------ | --------------------- | -------- | ----------- | --------------------- | ------------ | ---------------------- |
| colour       | 0,857               | 0,852                    | 0,874                 | 0,771    | 0,000       | 0,812                 | 0,500        | 0,729                  |
| packing      | 0,783               | 0,741                    | 0,714                 | 0,727    | 0,000       | **0,952**             | 0,000        | 0,588                  |
| price        | 0,308               | 0,600                    | **0,167**             | 0,462    | 0,000       | 0,000                 | 0,000        | 0,000                  |
| shipping     | 0,979               | 0,972                    | 0,984                 | 0,918    | 0,973       | 0,971                 | 0,960        | 0,958                  |
| smell        | 0,943               | 0,851                    | 0,849                 | 0,882    | 0,000       | 0,887                 | 0,756        | 0,836                  |
| stayingpower | 0,972               | 0,941                    | 0,816                 | 0,881    | 0,053       | 0,915                 | 0,873        | 0,925                  |
| texture      | 0,899               | 0,933                    | 0,855                 | 0,762    | 0,000       | 0,893                 | 0,859        | 0,867                  |

Đọc khối này: (a) **`weighted_ce` là thứ duy nhất cứu được lớp âm của encoder** (PhoBERT 0,000 → 0,812 ở
`colour`, 0,000 → 0,952 ở `packing`, 0,053 → 0,915 ở `stayingpower`); (b) `price` âm **vẫn 0,000 ở cả bốn
lượt encoder** - xem §4.9; (c) ba biến thể prompt **không cứu được gì**, `exp011` còn kéo `price` âm từ 0,600
xuống 0,308.

### 2.3 F1 lớp DƯƠNG (nhóm 4-bit lô 4 + encoder, để thấy chỗ mất điểm KHÔNG phải lớp dương)

| Khía cạnh    | 4-bit l4 0 | 4-bit l4 1 | 4-bit l4 5 | Một lượt | PhoBERT gốc | PhoBERT `weighted_ce` | ViSoBERT gốc | ViSoBERT `weighted_ce` |
| ------------ | ---------- | ---------- | ---------- | -------- | ----------- | --------------------- | ------------ | ---------------------- |
| colour       | 0,987      | 0,994      | 0,981      | 0,982    | 0,960       | 0,980                 | 0,967        | 0,971                  |
| packing      | 0,989      | 0,989      | 0,989      | 0,989    | 0,984       | **0,998**             | 0,984        | 0,987                  |
| price        | 0,981      | 0,992      | 0,992      | 0,989    | 0,992       | 0,991                 | 0,992        | 0,992                  |
| shipping     | 0,981      | 0,990      | 0,984      | 0,965    | 0,986       | 0,985                 | 0,978        | 0,976                  |
| smell        | 0,971      | 0,984      | 0,975      | 0,977    | **0,916**   | 0,975                 | 0,955        | 0,962                  |
| stayingpower | 0,988      | 0,961      | 0,976      | 0,929    | **0,783**   | 0,936                 | 0,918        | 0,943                  |
| texture      | 0,985      | 0,979      | 0,975      | 0,956    | **0,912**   | 0,972                 | 0,971        | 0,964                  |

Lớp dương rất vững: 17 lượt nằm trong khoảng **0,724–0,998**; chỗ thấp nhất là `exp013` ở `stayingpower`
0,724 (lượt tệ nhất, là ngoại lệ) - còn lại đều từ 0,783 trở lên. Nghĩa là **chỗ mất điểm là CHỌN sắc thái
âm, không phải tìm khía cạnh**; F1 lớp dương của encoder gốc cũng đã 0,783–0,998.

## 3. Phát hiện khía cạnh (cơ sở `all`)

| Lượt chạy              | accuracy micro | F1 micro | F1 macro | P / R         |
| ---------------------- | -------------- | -------- | -------- | ------------- |
| 4-bit l8, 0 ví dụ      | 94,69          | 0,891    | 0,874    | 0,910 / 0,872 |
| 4-bit l8, 1 ví dụ      | 93,84          | 0,871    | 0,857    | 0,908 / 0,836 |
| 4-bit l8, 5 ví dụ      | 94,52          | 0,886    | 0,869    | 0,915 / 0,859 |
| fp16 l4, 0 ví dụ       | **95,98**      | **0,920**| **0,910**| 0,908 / 0,932 |
| fp16 l4, 1 ví dụ       | 94,41          | 0,887    | 0,875    | 0,886 / 0,889 |
| fp16 l4, 5 ví dụ       | 95,24          | 0,905    | 0,893    | 0,899 / 0,910 |
| 4-bit l4, 0 ví dụ      | 94,67          | 0,890    | 0,873    | 0,910 / 0,872 |
| 4-bit l4, 1 ví dụ      | 93,92          | 0,873    | 0,858    | 0,909 / 0,839 |
| 4-bit l4, 5 ví dụ      | 94,50          | 0,886    | 0,868    | 0,915 / 0,858 |
| `exp011` (ví dụ âm)    | 93,77          | 0,872    | 0,858    | 0,892 / 0,852 |
| `exp012` (quét phàn nàn)| 93,46         | 0,863    | 0,848    | 0,897 / 0,832 |
| `exp013` (lưu ý lệch)  | **91,17**      | 0,800    | 0,786    | 0,913 / 0,712 |
| một lượt               | 92,83          | 0,869    | 0,863    | 0,793 / 0,962 |
| PhoBERT gốc            | 98,05          | 0,961    | 0,957    | 0,959 / 0,962 |
| PhoBERT `weighted_ce`  | 94,14          | 0,893    | 0,891    | 0,815 / 0,988 |
| ViSoBERT gốc           | **98,29**      | **0,966**| **0,966**| 0,961 / 0,971 |
| ViSoBERT `weighted_ce` | 97,06          | 0,943    | 0,944    | 0,912 / 0,975 |

Công bố **không** có bảng số cho phát hiện khía cạnh, nên bảng này không có cột đối chiếu (đúng như dòng
cuối của `data/reports/metrics_matrix/accuracy_by_aspect.csv`). Hai điều đọc được: (a) encoder phát hiện
khía cạnh tốt hơn hẳn model prompt (0,961–0,966 so với 0,800–0,920); (b) **`weighted_ce` có GIÁ PHẢI TRẢ** -
nó nâng F1 lớp âm nhưng **hạ phát hiện khía cạnh** (PhoBERT 98,05 → 94,14; ViSoBERT 98,29 → 97,06).

## 4. Chín kết luận

1. **Tái hiện công bố: ĐẠT.** Nhóm sạch một biến (4-bit lô 4): mức 1 ví dụ **+0,07**, mức 5 ví dụ **+0,45**,
   mức 0 ví dụ −0,10. Nhưng đỉnh `exp009` 97,77 chỉ hơn công bố 0,07 điểm ⇒ **nằm trong nhiễu của một lần
   chạy greedy**, không được nói là "vượt công bố" (chưa đo dao động).
2. **Mức 1 ví dụ là cấu hình tốt nhất** (97,77 · F1 macro 0,928 · 2.324 ô). Thêm ví dụ tới 5 không tăng:
   0 ví dụ 97,26 > 5 ví dụ 97,19 ở nhóm lô 4.
3. **CoT có tác dụng thật**: cùng model, cùng test, cùng 0 ví dụ, bỏ phần suy luận mất **1,83 điểm**
   (95,33 so với 97,16) và phát hiện khía cạnh giảm (92,83 so với 94,69).
4. **Lượng hoá 4-bit KHÔNG thua fp16** khi so sạch một biến: **+0,64 / +1,17 / +0,71 điểm** ở ba mức ví dụ.
   Nhưng 4-bit **trả lời ít hơn 5–6% số ô** (2.414/2.324/2.375 so với 2.580/2.461/2.520) ⇒ một phần lợi thế
   đến từ **kiêng trả lời**; mọi so sánh phải đọc kèm số ô.
5. **Sửa câu chữ và sửa ví dụ của prompt KHÔNG cứu được lớp âm**: `exp011` −0,09 (còn kéo F1 `price` âm
   0,600 → 0,308), `exp012` −1,20, `exp013` −5,06 (mất 343 ô vì model kiêng trả lời). Ba lượt này **bị bỏ**.
6. **Sửa HÀM MẤT MÁT thì cứu được**: `weighted_ce` + `inverse` cho **+8,22 điểm** (PhoBERT 88,40 → 96,62) và
   **+0,75 điểm** (ViSoBERT 94,86 → 95,61); F1 lớp âm của PhoBERT 0,540 → 0,876; và **đảo thứ hạng** hai
   encoder (ViSoBERT hơn 6,46 điểm → PhoBERT hơn 1,01 điểm). **Giá phải trả**: hạ **phát hiện khía cạnh**
   (PhoBERT 98,05 → 94,14; ViSoBERT 98,29 → 97,06) ⇒ hai chỉ số này phải được báo cáo CẶP.
7. **Chỗ mất điểm của encoder là CHỌN sắc thái âm, không phải tìm khía cạnh**: lớp dương 0,783–0,998 ở mọi
   lượt; phát hiện khía cạnh của encoder gốc là tốt nhất bảng (F1 macro 0,957 và 0,966 so với 0,786–0,910
   của model prompt).
8. **Dự án vượt công bố ở đúng chỗ công bố yếu**: F1 âm `smell` 0,874–0,943 so với 0,500–0,6667 của công bố;
   `colour` 0,817–0,925 so với 0,800–0,875.
9. **`price` âm: thước `paper` KHÔNG ĐO ĐƯỢC, không phải "model mù".** Đếm trong dữ liệu gốc
   (`data/raw/cosmetics/v0.1.0/eda/02_label_aspect_distribution.csv`): `price` âm có **15 ô train, 0 ô val,
   6 ô test**; nên mọi F1 ở lớp này là nhiễu 1–6 ô (bảng công bố cũng ghi `0,000`). Từ nay `price` phải đọc
   bằng **số lần model gán mã 2 + danh sách 6 ô âm**, và **không có ngưỡng cho `price`** vì `val` có 0 ô âm
   (ngưỡng chỉ áp cho 6 khía cạnh còn lại). Muốn có thước thật cho `price` thì phải **lập tập chẩn đoán giá**
   - đã ghi vào backlog.

## 5. Hạn chế của đợt này (phải nói khi báo cáo)

- Mỗi cấu hình chạy **một lần greedy**: chưa đo dao động giữa các lần chạy (bốn lượt lấy mẫu
  `exp018/019/020` + đối chứng fp16 `exp021` sẽ làm ở đợt sau).
- `exp004` và `exp010` là lượt **CHẠY TIẾP (RESUME)**: `seconds` ghi được chỉ là phần của phiên cuối
  (2.533,3 giây cho 319 mẫu còn lại; 411,3 giây) - **không** phải thời gian cả lượt, và `n_samples` trong
  `metrics.json` cũng là của phiên cuối (số mẫu cả split nằm ở `run_meta.json::run.n_samples` = 1.623).
- Lớp âm của `price` (6 ô test) và `packing` (10 ô test) quá ít: mọi kết luận trên hai khía cạnh này rất yếu.
- **Nhóm G (Qwen3-0.6B) và model Qwen2.5-0.5B chưa có kết quả** - nhóm G đã hỏng hai lần (nạp nhầm 4B; bật
  suy nghĩ ăn hết trần token), sáu thư mục kết quả đã xoá ngày 04/10/2026.
- Số `seconds` giữa các lượt **không so trực tiếp được**: mỗi lượt ở một phiên Colab khác nhau, trạng thái
  máy khác nhau (cùng một lượt có thể chênh 1,5–2 lần).
- **Không có MLflow cho lượt nào trong 17 lượt**: experiment `sentimentx-absa` đã bị xoá mềm trên DagsHub
  nên không có lịch sử run; đây là mất mát đã biết và **không khôi phục**.
- Đối chứng lượng hoá chỉ có ở **một model** (Qwen3-4B); chưa biết kết luận này có giữ với encoder hoặc
  model khác không.

## 6. Hướng phát triển tiếp, theo thứ tự ưu tiên

| #  | Việc                                                                                  | Vì sao (từ số đo)                                                                                   | Cần gì                        |
| -- | ------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ----------------------------- |
| 1  | **Chạy lại Qwen3-0.6B với `enable_thinking: false`** (3 lượt 0/1/5 ví dụ)              | Nhóm duy nhất trả lời "nhỏ hơn ~7 lần thì kém bao nhiêu"; hai lần chạy trước đều hỏng                 | 3 lượt Colab (1–1,5 giờ/lượt)  |
| 2  | **Thêm Qwen2.5-0.5B-Instruct** (3 lượt)                                                | Model nhỏ **khác họ**; kiểm "nhỏ thì kém" có lặp lại không                                             | 3 lượt Colab (20–40 phút/lượt) |
| 3  | **Bốn encoder mới**: `phobert-large`, `vibert-base-cased`, `cafebert`, `xlm-roberta-base` (đều `weighted_ce` + `inverse`) | Tìm encoder vừa giữ lớp âm vừa không mất phát hiện khía cạnh; XLM-R là đối chứng **nguồn tiền huấn luyện** | 4 lượt Colab (15–20 phút/lượt) |
| 4  | **Ngưỡng theo khía cạnh** (2 lượt `test`, ngưỡng chốt trên `val`)                       | Lớp âm có thể sửa **không cần huấn luyện lại**; riêng `price` **không áp dụng** (val 0 ô âm)           | 2 lượt Colab ngắn + 0 GPU      |
| 5  | **Kết hợp**: ensemble encoder, lai encoder + LLM theo khía cạnh, biểu quyết **3 mẫu**   | Ba cách ăn điểm khác nhau: encoder mạnh phát hiện (0,957–0,966), LLM mạnh sắc thái âm ở vài khía cạnh | 0 GPU (chấm lại + luật đóng băng) |
| 6  | **Ba lượt về giá**: `exp014` (định nghĩa trong prompt), `exp015` (ví dụ có ô `price` = mã 2), `exp016` (chẩn đoán một khía cạnh) | `price` âm là lớp duy nhất mọi lượt đều ~0; đọc bằng **đếm + danh sách 6 ô**                          | 3 lượt Colab (~4,5 giờ)        |
| 7  | **Đo dao động**: `exp018/019/020` (4-bit, seed 1/2/3) + `exp021` (fp16, seed 1)         | "Hơn công bố 0,07 điểm" chưa chắc vượt nhiễu; và kiểm **lượng hoá × lấy mẫu** có tương tác không       | 4 lượt Colab (~11 giờ)         |
| 8  | **Nhánh suy nghĩ của 0.6B** (1 lượt DÒ + tối đa 3 lượt, trần token chốt từ lượt DÒ)     | Bật suy nghĩ có hơn không, ở đúng model đã gây lỗi ăn hết trần token                                  | 20 phút cho DÒ, 2–8 giờ/lượt   |
| 9  | **Tập chẩn đoán giá** (200–300 review có nhắc giá, gán nhãn theo quy tắc viết trước)    | Cách **duy nhất** để `price` có thước thật - đã ghi vào backlog, làm sau                              | việc người, 0 GPU              |
| 10 | QLoRA Qwen3-4B; model lớn hơn: `Qwen3-8B`, `Qwen3-14B`, `Qwen3-4B-Thinking-2507`        | Trả lời "fine-tune có hơn prompt không" và mốc quy mô lớn hơn                                         | GPU ≥ 24 GB / Colab dài        |

Chi tiết việc chia đợt, người làm, mốc dừng và cách ghim/gói nằm ở `present_plan.md` (kế hoạch đang chạy) và
`check_present_plan.md` (trạng thái); câu hỏi và điểm riêng của từng lượt ở
`docs/04_experiments/08_experiment_rationale.md`; cây phát triển ở `docs/04_experiments/07_evolution.md`.




