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
Vì vậy split `test` của ta **chính là** tập test của công bố, và ta so sánh **trực tiếp**.

Hai điểm đã khớp sẵn: cột `others` bị loại trong schema của dataset, và neutral bị loại
theo `neutral_policy: drop`.

## Số của công bố được lưu ở đâu

`data/reference_publication/` gồm năm file số liệu, chép nguyên từ thư mục `observation_announcement/`
do giảng viên cung cấp. Nội dung gốc của thư mục đó lưu ở `observation_announcement.md` trong cùng thư mục này.

| File                                | Nội dung                                                                                                       |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `accuracy_by_aspect.csv`            | accuracy theo khía cạnh, cột là 0-shot, 1-shot, 5-shot, cộng dòng `Aspect` là độ chính xác phát hiện khía cạnh |
| `prf_by_aspect_sentiment_0shot.csv` | Precision, Recall, F1 theo khía cạnh và sắc thái, biến thể 0-shot                                              |
| `prf_by_aspect_sentiment_1shot.csv` | như trên, biến thể 1-shot                                                                                      |
| `prf_by_aspect_sentiment_5shot.csv` | như trên, biến thể 5-shot                                                                                      |
| `sentiment_distribution.csv`        | phân bố nhãn của dataset                                                                                       |

Các file này là số liệu tham chiếu, **không** được sinh tự động và không sửa.

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

## Cách so

`data/reports/metrics_matrix/accuracy_by_aspect.csv` có một cột `reference`.
So cột của từng thí nghiệm với cột này để thấy khoảng cách theo từng khía cạnh.

## Kết quả dự kiến theo giai đoạn

| Giai đoạn        | Việc làm                                                             |
| ---------------- | -------------------------------------------------------------------- |
| Tái hiện         | Qwen3 prompt với CoT 0-shot, 1-shot, 5-shot, đúng ba mức của công bố |
| Cải thiện prompt | CoT có cấu trúc, ràng buộc định dạng, ví dụ few-shot lấy từ train    |
| Cải thiện model  | LoRA hoặc QLoRA trên PhoBERT và ViSoBERT                             |
