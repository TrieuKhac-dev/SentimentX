# Công bố tham chiếu

> Đọc file này khi: so kết quả của dự án với mốc cần vượt.
> Liên quan: `docs/04_experiments/metrics.md`, `data/reference_publication/`

## Công bố

"Applying Prompt Engineering to Sentiment Analysis of Vietnamese Reviews".

| Thông tin                    | Giá trị                                                          |
| ---------------------------- | ---------------------------------------------------------------- |
| Dữ liệu                      | 16.227 đánh giá son môi Shopee                                   |
| Số cặp khía cạnh và sắc thái | 32.775                                                           |
| Model                        | GPT-4o-mini                                                      |
| Cách chạy                    | Chain-of-Thought kết hợp 0-shot, 1-shot và 5-shot                |
| Accuracy theo khía cạnh      | 0-shot 94,12 đến 100 phần trăm                                   |
| Accuracy theo khía cạnh      | 1-shot 94,12 đến 100 phần trăm                                   |
| Accuracy theo khía cạnh      | 5-shot 92,86 đến 100 phần trăm                                   |
| Ngoài ra                     | có báo cáo Precision, Recall, F1 theo từng khía cạnh và sắc thái |

Công bố **loại neutral và OTHERS** khỏi phần đánh giá chính, nên các số trên không đại diện cho
toàn bộ bài toán ABSA đa lớp.

## Dữ liệu của ta và của công bố

`data/raw/cosmetics/v0.1.0/` với `train`, `val`, `test`, `full` là dữ liệu lấy từ công bố.
Split `test` của ta **chính là** tập test của công bố, và ta so sánh **trực tiếp**.

Lưu ý theo phiên bản dữ liệu: điều đó chỉ đúng khi `test` KHÔNG bị sửa. Bản pipeline `v0.1.0` (dữ liệu
`...-e0ccc484`) có sửa `test` - nó bỏ 105 dòng khỏi tập này - nên số của bản đó **không** so được với
công bố. Bản `v0.2.0` (`...-e616c1e3`) để `test` nguyên bản (1.623 dòng) và từ 01/10/2026 là bản mọi
thí nghiệm dùng; xem `docs/01_dataset/changelog.md`.

Hai điểm đã khớp sẵn: cột `others` bị loại trong schema của dataset, và neutral bị loại
theo `neutral_policy: drop`.

## Số của công bố được lưu ở đâu

`data/reference_publication/` gồm năm file số liệu, chép nguyên từ thư mục `observation_announcement/`
do giảng viên cung cấp. Nội dung gốc của thư mục đó lưu ở `observation_announcement.md` trong cùng thư mục này.
Bản thân bài báo (Table 3 và Tables 4-6) lưu ở `announcement.md`, dùng làm nguồn đối chiếu số.

| File                                | Nội dung                                                                                                       |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `accuracy_by_aspect.csv`            | accuracy theo khía cạnh, bảy hàng, cột là 0-shot, 1-shot, 5-shot                                                |
| `prf_by_aspect_sentiment_0shot.csv` | Precision, Recall, F1 theo khía cạnh và sắc thái, biến thể 0-shot                                              |
| `prf_by_aspect_sentiment_1shot.csv` | như trên, biến thể 1-shot                                                                                      |
| `prf_by_aspect_sentiment_5shot.csv` | như trên, biến thể 5-shot                                                                                      |
| `sentiment_distribution.csv`        | phân bố nhãn của dataset                                                                                       |

Các file này là số liệu tham chiếu, **không** được sinh tự động và không sửa - trừ **một lần chữa cột
nhãn** ngày 01/10/2026 (số không đổi, xem ngay dưới).

### Lần chữa cột nhãn ngày 01/10/2026

Bản `accuracy_by_aspect.csv` nhận ngày 24/09/2026 bị **lệch cột nhãn đúng một hàng** so với Table 3
của bài: hàng `Smell` bị thiếu, hàng cuối bị ghi tên `Aspect`, và số của mỗi hàng là số của khía cạnh
ĐỨNG TRƯỚC nó trong Table 3. Hệ quả: mọi khía cạnh đều bị đem so với số của một khía cạnh khác (ví dụ
`colour` bị so với 94,12 vốn là số của `Smell`) - và bảng vẫn trông hợp lý, nên lỗi nằm im từ 24/09
đến 01/10/2026. Hàng `Aspect` đó thật ra là số của `Shipping` (100 / 98,89 / 96,70).

Cách chữa: đối chiếu **từng số** với Table 3 rồi đặt lại tên bảy hàng (`Smell`, `Price`, `Texture`,
`Colour`, `Stayingpower`, `Packing`, `Shipping`) - **không sửa một con số nào** - và bỏ hàng `Aspect`
vì đó là tên sai của `Shipping`. Ba file `prf_*` kiểm lại thì **không** lệch (khớp Tables 4-6).

Hai chốt chặn để lỗi này không tái diễn:

1. `tests/reporting/test_reference_file.py` đọc **file thật** và khoá lại đúng bảy tên khía cạnh cùng
   từng con số của Table 3, và bộ khía cạnh của Tables 4-6.
2. `src/reporting/reports.py::load_reference` **không** đổi tên hàng nào nữa (trước đây hàng `Aspect`
   được đọc thành chỉ số `aspect_detection`, nên một hàng lệch nhãn hiện ra như một chỉ số nghe hợp
   lý - đó chính là đường đi của con số sai vào bảng so công bố).

Chỉ số `aspect_detection` thì **không** lấy từ file công bố: bài có nêu task phát hiện khía cạnh nhưng
**không có bảng số** cho nó, nên dòng `aspect_detection` trong `metrics_matrix` lấy số từ **lượt chạy**
và để **trống** ô công bố.

Rà soát cùng lượt (01/10/2026): **không kết luận nào** trong tài liệu dựa vào cột tham chiếu bị ảnh
hưởng - chỉ có hai chỗ nhắc tới nhãn cột là trang này (đã sửa ở trên) và một dòng trong bản ghi lịch sử
`docs/06_plan/P6_reports_ci.md` (giữ nguyên, không sửa). Số ở `docs/04_experiments/03_training_eval.md`
mục 6 đo trên dữ liệu của dự án, không lấy từ file công bố.

## Điều kiện để so sánh hợp lệ

1. Dùng đúng split `test`, không đổi tập này. Guard là khoá tập đánh giá
   (`data/processed/<mã>/eval_lock.json`), ghi ngay từ bản dữ liệu đầu tiên.
2. Dùng đúng metric trong `docs/04_experiments/metrics.md`.
3. Loại neutral và OTHERS giống công bố.
4. Kết quả chỉ được dùng khi commit đã ghim nằm trên nhánh `experiment`, và khi merge vào nhánh đó
   không phải sửa file nào (`docs/00_workflow/02_rules.md` luật 3-4). Cột `valid`/`comparable` trong
   bảng tổng hợp để máy tự kiểm điều này là việc **chưa làm** - xem
   `docs/04_experiments/04_backlog.md` mục 6.

Phần **huấn luyện và pipeline xử lý dữ liệu thì được tự do thay đổi**, miễn là giữ tập test
và metric. Mục tiêu là kết quả **nhỉnh hơn** công bố, không chỉ tái hiện.

## Khác biệt có thể làm lệch số

Ba khác biệt giữa cách công bố đo và cách dự án đo - đọc trước khi so từng con số:

1. **Phép lọc ô: một chiều so với hai chiều.** Cách đo cũ của dự án lọc theo MỘT chiều: giữ mọi ô có
   nhãn đúng khác `neutral`, kể cả ô mà model trả lời "không nhắc tới" hay một sắc thái khác. Công bố
   lọc theo HAI chiều: chỉ giữ ô mà **cả** nhãn đúng **và** nhãn đoán đều là `positive` hoặc
   `negative`. Ô bị loại không nằm trong mẫu số của họ, nên mẫu số của họ phụ thuộc chất lượng model,
   còn mẫu số của ta thì không.
2. **Ô không đọc được.** Cách đo cũ của dự án tính ô model trả lời không đọc được là **SAI** và vẫn
   giữ nó trong mẫu số; công bố không nêu cách xử lý các ô này.
3. **Lớp âm của Precision/Recall/F1.** Cách đo cũ tính ô mà model đoán âm trong khi nhãn đúng là
   "không nhắc tới" là **dương tính giả** của lớp âm, nên Precision/Recall/F1 của lớp âm bị kéo
   xuống một cách máy móc; bảng của công bố chỉ có hai lớp `positive`/`negative`, không có ô
   "không nhắc tới" nào.

Vì ba khác biệt này, hai con số cùng tên "accuracy theo khía cạnh" **không** tự động so được với nhau;
phải nói rõ đang đo bằng cách nào.

## Cách so

`data/reports/metrics_matrix/accuracy_by_aspect.csv` có **cột công bố theo từng mức ví dụ**
(`COT+0-shot`, `COT+1-shot`, `COT+5-shot`). Mỗi lượt chạy được so với cột của **đúng mức ví dụ của
chính nó** (đọc từ `metrics.json -> prompt_examples.examples`, suy ra trong `src/reporting/reports.py::shot_of`);
lượt không có mức ví dụ (model encoder, lượt chạy tay) dùng cột do
`python scripts/collect_reports.py --reference-shot <0|1|5>` chọn. So cột của từng lượt với cột công
bố cùng mức để thấy khoảng cách theo từng khía cạnh.

Số của công bố được so với **biến thể `paper`** trên **tập `test` nguyên bản**: hai bảng của
`metrics_matrix` lấy số của lượt chạy ở cơ sở đo `paper` (chỉ giữ ô mà cả nhãn đúng và nhãn đoán là
`positive`/`negative` - đúng cách công bố đếm), còn `scores` trong `metrics.json` của mỗi lượt là cơ
sở `all` của dự án. Hai cơ sở này cho hai con số khác nhau trên cùng một đầu ra model, nên đọc số phải
biết đang đọc cơ sở nào - xem `docs/04_experiments/metrics.md` mục "Hai cơ sở đo".

## Kết quả dự kiến theo giai đoạn

| Giai đoạn        | Việc làm                                                             |
| ---------------- | -------------------------------------------------------------------- |
| Tái hiện         | Qwen3 prompt với CoT 0-shot, 1-shot, 5-shot, đúng ba mức của công bố |
| Cải thiện prompt | CoT có cấu trúc, ràng buộc định dạng, ví dụ few-shot lấy từ train    |
| Cải thiện model  | LoRA hoặc QLoRA trên PhoBERT và ViSoBERT                             |
