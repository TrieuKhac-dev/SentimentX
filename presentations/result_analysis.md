# Phân tích kết quả và hướng phát triển tiếp

> Đọc file này khi: báo cáo kết quả chín lượt đã chạy và chọn việc làm tiếp theo.
> Liên quan: `presentations/experiment_rationale.md`, `docs/04_experiments/08_experiment_rationale.md`, `data/reports/metrics_matrix/`

Mọi số dưới đây là **cơ sở `paper`** (cách công bố đếm: chỉ giữ ô mà cả nhãn đúng và nhãn đoán là
positive/negative), trên split `test` 1.623 review. Lượt chạy: 4-bit = `exp002/003/004`,
không lượng hoá (fp16) = `exp005/006/007`, một lượt = `prompt-one-turn/exp001`, hai encoder = LoRA.

## 1. Accuracy theo khía cạnh, so từng mức ví dụ của công bố

| Khía cạnh       | Công bố 0-shot | 4-bit 0-shot | fp16 0-shot | Công bố 1-shot | 4-bit 1-shot | fp16 1-shot | Công bố 5-shot | 4-bit 5-shot | fp16 5-shot | Một lượt | PhoBERT   | ViSoBERT |
| --------------- | -------------- | ------------ | ----------- | -------------- | ------------ | ----------- | -------------- | ------------ | ----------- | -------- | --------- | -------- |
| smell           | 94,59          | 95,29        | 96,17       | 96,15          | 97,01        | 95,08       | 92,86          | 96,09        | 95,67       | 96,19    | 84,48     | 92,47    |
| price           | 97,22          | 96,25        | 95,86       | 100            | 98,49        | 98,20       | 100            | 98,07        | 97,37       | 97,79    | 98,45     | 98,43    |
| texture         | 94,12          | 97,66        | 96,96       | 100            | 97,17        | 95,80       | 100            | 96,07        | 95,83       | 92,52    | 83,86     | 95,16    |
| colour          | 97,37          | 97,66        | 97,41       | 96,61          | 98,81        | 98,27       | 94,74          | 96,56        | 96,92       | 96,68    | 92,27     | 93,84    |
| stayingpower    | 100            | 97,83        | 94,54       | 94,12          | 96,15        | 92,50       | 92,86          | 97,37        | 94,61       | 91,12    | **64,71** | 90,04    |
| packing         | 98,25          | 97,91        | 97,21       | 98,11          | 97,89        | 98,26       | 100            | 97,89        | 98,26       | 97,93    | 96,83     | 96,88    |
| shipping        | 100            | 97,50        | 98,16       | 98,89          | 98,51        | 98,12       | 96,70          | 97,74        | 96,72       | 95,10    | 98,19     | 97,18    |
| **Trung bình**  | **97,36**      | **97,16**    | 96,62       | **97,70**      | **97,72**    | 96,60       | 96,74          | 97,11        | 96,48       | 95,33    | 88,40     | 94,86    |
| Lệch so công bố | -              | −0,21        | −0,75       | -              | **+0,02**    | −1,09       | -              | **+0,38**    | −0,25       | −2,03    | **−8,97** | −2,51    |

## 2. F1 theo LỚP và phát hiện khía cạnh

Hai chỉ số ở đây trả lời HAI câu khác nhau, và đọc ở HAI cơ sở đo khác nhau - trộn lại là sai:

| Chỉ số                | Trả lời câu gì                                     | Cơ sở đo                                                          |
| --------------------- | -------------------------------------------------- | ----------------------------------------------------------------- |
| F1 lớp âm / lớp dương | khía cạnh ĐÃ được nhắc thì chọn đúng sắc thái chưa | `paper` (chỉ ô mà cả nhãn đúng và nhãn đoán là positive/negative) |
| phát hiện khía cạnh   | model có NHẬN RA khía cạnh được nhắc hay không     | `all` (còn cả ô "không nhắc tới"), scorer `aspect_detection`      |

Trên `paper`, mỗi khía cạnh còn ĐÚNG hai lớp nên P/R/F1 theo lớp so thẳng được với Tables 4-6 của công
bố. Còn phát hiện khía cạnh thì trên `paper` không còn gì để đo (mọi ô giữ lại đều đã "có nhắc tới"), nên
nó phải đo ở cơ sở `all`. Số trong ngoặc của bảng âm là **số ô của lớp đó** (cỡ mẫu); cỡ mẫu phụ thuộc
câu trả lời của model nên mỗi lượt một khác, đây ghi số của lượt 0-shot.

### 2.1. F1 lớp ÂM

| Khía cạnh         | Công bố 0-shot | 4-bit 0-shot | fp16 0-shot | Công bố 1-shot | 4-bit 1-shot | fp16 1-shot | Công bố 5-shot | 4-bit 5-shot | fp16 5-shot | Một lượt | PhoBERT | ViSoBERT |
| ----------------- | -------------- | ------------ | ----------- | -------------- | ------------ | ----------- | -------------- | ------------ | ----------- | -------- | ------- | -------- |
| smell (47)        | 66,67          | 87,4         | 89,3        | 66,67          | **92,3**     | 87,4        | 50,0           | 90,5         | 88,0        | 88,2     | **0**   | 75,6     |
| price (2)         | 0              | 26,7         | 43,5        | 0              | 60,0         | 54,5        | 0              | 44,4         | 46,2        | 46,2     | 0       | 0        |
| texture (61)      | 86,96          | 94,5         | 93,0        | 100            | 94,0         | 90,9        | 100            | 91,0         | 90,2        | 76,2     | **0**   | 85,9     |
| colour (50)       | 87,5           | 86,0         | 84,7        | 85,71          | **92,3**     | 89,7        | 80,0           | 81,7         | 82,8        | 77,1     | **0**   | 50,0     |
| stayingpower (55) | 100            | **97,2**     | 93,3        | 88,89          | 96,2         | 92,1        | 88,89          | 97,0         | 93,7        | 88,1     | 5,3     | 87,3     |
| packing (10)      | 80,0           | 76,9         | 69,2        | 80,0           | 75,0         | 78,3        | 100            | 75,0         | 78,3        | 72,7     | **0**   | 0        |
| shipping (160)    | 100            | 96,3         | 97,2        | 98,11          | 97,8         | 97,2        | 94,55          | 96,7         | 95,1        | 91,8     | 97,3    | 96,0     |

### 2.2. F1 lớp DƯƠNG

| Khía cạnh    | Công bố 0-shot | 4-bit 0-shot | fp16 0-shot | Công bố 1-shot | 4-bit 1-shot | fp16 1-shot | Công bố 5-shot | 4-bit 5-shot | fp16 5-shot | Một lượt | PhoBERT  | ViSoBERT |
| ------------ | -------------- | ------------ | ----------- | -------------- | ------------ | ----------- | -------------- | ------------ | ----------- | -------- | -------- | -------- |
| smell        | 97,06          | 97,1         | 97,7        | 97,06          | 98,1         | 96,9        | 96,15          | 97,5         | 97,4        | 97,7     | 91,6     | 95,5     |
| price        | 98,59          | 98,1         | 97,9        | 100            | 99,2         | 99,1        | 100            | 99,0         | 98,7        | 98,9     | 99,2     | 99,2     |
| texture      | 96,20          | 98,5         | 98,1        | 100            | 98,1         | 97,3        | 100            | 97,5         | 97,4        | 95,6     | 91,2     | 97,1     |
| colour       | 98,53          | 98,7         | 98,6        | 98,08          | 99,4         | 99,1        | 96,97          | 98,1         | 98,3        | 98,2     | 96,0     | 96,7     |
| stayingpower | 100            | 98,2         | 95,4        | 96,00          | 96,1         | 92,9        | 94,74          | 97,6         | 95,3        | **92,9** | **78,3** | 91,8     |
| packing      | 99,08          | 98,9         | 98,5        | 99,01          | 98,9         | 99,1        | 100            | 98,9         | 99,1        | 98,9     | 98,4     | 98,4     |
| shipping     | 100            | 98,1         | 98,6        | 99,21          | 98,9         | 98,6        | 94,74          | 98,3         | 97,5        | 96,5     | 98,6     | 97,8     |

Lớp dương rất vững: 9 lượt nằm trong khoảng **0,918-0,992**, chỗ thấp nhất là `stayingpower` (PhoBERT
0,783 · một lượt và fp16 1 ví dụ 0,929 · ViSoBERT 0,918). Nghĩa là chỗ mất điểm của hai encoder **không**
nằm ở lớp dương.

### 2.3. Phát hiện khía cạnh (cơ sở `all`)

| Chỉ số             | 4-bit 0-shot | 4-bit 1-shot | 4-bit 5-shot | fp16 0-shot | fp16 1-shot | fp16 5-shot | Một lượt | PhoBERT | ViSoBERT  |
| ------------------ | ------------ | ------------ | ------------ | ----------- | ----------- | ----------- | -------- | ------- | --------- |
| accuracy micro (%) | 94,69        | 93,84        | 94,52        | 95,98       | 94,41       | 95,24       | 92,83    | 98,05   | **98,29** |
| F1 micro (%)       | 89,1         | 87,1         | 88,6         | 92,0        | 88,7        | 90,5        | 86,9     | 96,1    | **96,6**  |
| F1 macro (%)       | 87,4         | 85,7         | 86,9         | 91,0        | 87,5        | 89,3        | 86,3     | 95,7    | **96,6**  |

Đọc bảng này: **hai encoder nhận ra khía cạnh TỐT HƠN LLM** (98 so với 93-96) nhưng vẫn thua ở lớp âm -
chỗ mất điểm của encoder là **chọn sắc thái**, không phải tìm khía cạnh. Công bố **không** có bảng số cho
phát hiện khía cạnh, nên bảng này không có cột đối chiếu (đúng như dòng cuối của
`data/reports/metrics_matrix/accuracy_by_aspect.csv`).

## 3. Sáu kết luận

1. **Tái hiện công bố: ĐẠT.** Mức 1 ví dụ **+0,02** và 5 ví dụ **+0,38** so công bố; mức 0 ví dụ −0,21.
2. **Mức 1 ví dụ là cấu hình tốt nhất** (97,72 · F1 0,926 · khớp hoàn toàn 97,23%) - thêm ví dụ đến 5
   không còn tăng điểm.
3. **CoT có tác dụng thật**: cùng model, cùng test, cùng 0 ví dụ, bỏ phần suy luận mất **1,83 điểm**.
4. **Bản 4-bit KHÔNG thua bản không lượng hoá** (4-bit cao hơn 0,54 / 1,12 / 0,63 điểm ở ba mức) - nhưng
   hai nhóm khác nhau HAI biến (lượng hoá và `batch_size` 8 so với 4) nên chưa kết luận được nguyên nhân.
5. **Hai encoder mất điểm ở LỚP ÂM, không phải ở việc nhận ra khía cạnh**: PhoBERT F1 âm = 0 ở 5/7 khía
   cạnh, ViSoBERT = 0 ở `price`/`packing` và 0,50 ở `colour`. Đây là chỗ cải thiện rõ nhất.
6. **Dự án vượt công bố ở đúng chỗ công bố yếu**: F1 âm `smell` 87,4-92,3 so với 50-66,67; `colour` lên
   92,3 so với 80-87,5. Riêng `price` âm chỉ có 2-5 ô nên số ở đó là nhiễu (công bố cũng ghi 0).

## 4. Hướng phát triển tiếp, theo thứ tự ưu tiên

| #   | Việc                                                                                               | Vì sao (từ số đo)                                                                     | Cần gì                   |
| --- | -------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | ------------------------ |
| 1   | **Chạy lại Qwen3-0.6B** sau khi sửa cách chọn checkpoint                                           | Cả ba lượt nhóm D đã chạy nhầm trọng số 4B nên chưa trả lời được câu hỏi quy mô       | sửa 1 hàm + 3 lượt Colab |
| 2   | **Chạy lại nhóm fp16 ở `batch_size` 8** (hoặc 4-bit ở batch 4)                                     | Để phép so lượng hoá chỉ còn MỘT biến                                                 | 3 lượt Colab             |
| 3   | **`loss.type: weighted_ce` + `class_weight: inverse` cho hai encoder**                             | PhoBERT F1 âm = 0 ở 5/7 khía cạnh; dữ liệu mất cân bằng (`price` 3.238 dương / 21 âm) | 2 lượt LoRA              |
| 4   | **Sửa bộ ví dụ few-shot: thêm ví dụ có nhãn TIÊU CỰC** cho `texture`, `stayingpower`               | Là hai khía cạnh yếu nhất ở mọi mức ví dụ                                             | 1 lượt Colab             |
| 5   | **Đo dao động**: `decoding: sample` + vài `seed` ở cấu hình tốt nhất                               | Mức "+0,02 so công bố" quá nhỏ để chắc với một lần chạy greedy                        | 3 lượt Colab             |
| 6   | **Rescore từ `predictions.csv`** để tách "phát hiện khía cạnh" khỏi "chọn sắc thái" khi đọc P/R/F1 | Lớp âm là gốc của mọi khoảng cách; công cụ đã có                                      | **không cần GPU**        |
| 7   | QLoRA trên Qwen3-4B (GPU ≥ 16 GB)                                                                  | Trả lời "fine-tune có hơn prompt không"                                               | máy lớn                  |

## 5. Hạn chế của đợt này (phải nói khi báo cáo)

- Mỗi cấu hình chạy **một lần greedy**, chưa đo dao động giữa các lần chạy.
- Nhóm fp16 đổi cả lượng hoá lẫn `batch_size` → chưa tách được biến.
- `price` và `packing` lớp âm có 2-10 ô; mọi kết luận trên hai khía cạnh đó là yếu.
- Nhóm D (0.6B) **không có kết quả** - ba lượt cũ đã xoá vì chạy nhầm model.
- Số `n_samples`/`seconds` trong `experiment_registry` là của **phiên cuối** với lượt chạy tiếp.
