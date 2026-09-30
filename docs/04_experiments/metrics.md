# Chỉ số đánh giá

> Đọc file này khi: viết báo cáo, hoặc kiểm tra cách tính một chỉ số.
> Liên quan: `docs/04_experiments/reference_publication.md`, `src/evaluation/metrics.py`

Metric lấy theo công bố tham chiếu, không tự thêm bớt khi so sánh.
Mọi chỉ số tính trên **cùng một tập đánh giá** là split `test` của dataset.

## Hai câu hỏi phải tách rời

1. Model có nhận ra khía cạnh nào được nhắc tới hay không. Đây là bài toán nhị phân.
2. Khi đã nhận ra, model có chọn đúng sắc thái hay không.

Gộp hai câu hỏi làm một sẽ che mất kiểu lỗi thật: model thấy khía cạnh nhưng chọn sai sắc thái,
hoặc bỏ qua khía cạnh nhưng đoán đúng các khía cạnh còn lại.

## Danh sách chỉ số

| Chỉ số                                           | Tên trong `scores`          | Định nghĩa                                                               |
| ------------------------------------------------ | --------------------------- | ------------------------------------------------------------------------ |
| Độ chính xác theo khía cạnh                      | `accuracy`                  | số ô đúng chia cho số ô, tính riêng cho từng khía cạnh                   |
| Chính xác khi có nhắc tới                        | `accuracy`                  | chỉ tính trên các ô mà nhãn đúng khác "không nhắc tới"                   |
| Phát hiện khía cạnh                              | `aspect_detection`          | bài toán nhị phân có nhắc tới hay không: accuracy, precision, recall, F1 |
| Precision, Recall, F1 theo khía cạnh và sắc thái | `prf`                       | tính riêng cho từng cặp khía cạnh và nhãn, ví dụ `price` và `negative`   |
| Trung bình macro và micro                        | `aggregate`                 | gộp theo khía cạnh hoặc gộp theo ô                                       |
| Khớp hoàn toàn                                   | `aggregate`                 | tỉ lệ review đoán đúng cả bảy khía cạnh                                  |
| Ma trận nhầm theo khía cạnh                      | `confusion`                 | bảng đếm nhãn đúng so với nhãn đoán, dùng để vẽ                          |
| Tỉ lệ đọc được                                   | không phải chỉ số chấm điểm | tỉ lệ kết quả đọc được, kèm phân bố lí do lỗi                            |

## Quy ước bắt buộc

- Ô không đọc được tính là **sai**, không được bỏ khỏi mẫu số. Bỏ đi thì tỉ lệ lỗi định dạng
  trở thành cách nâng điểm vô tình.
- Với bài toán nhị phân, lớp dương là "có nhắc tới", tức mã khác 0.
- Khi ở `label_space: binary`, các ô nhãn `neutral` bị loại theo `neutral_policy`;
  số ô bị loại ghi vào `metrics.json`.

## Bộ chấm điểm là registry

`configs/experiments/evaluation.yaml` khai `scores` là danh sách tên. Mỗi tên là một module trong
`src/evaluation/scorers/`:

| Tên                | Module                        | Nội dung                                                            |
| ------------------ | ----------------------------- | ------------------------------------------------------------------- |
| `accuracy`         | `scorers/accuracy.py`         | độ chính xác theo khía cạnh, và độ chính xác khi đã nhắc tới         |
| `aspect_detection` | `scorers/aspect_detection.py` | nhị phân "có nhắc tới hay không": accuracy, precision, recall, F1    |
| `prf`              | `scorers/prf.py`              | precision/recall/F1 cho từng cặp (khía cạnh, sắc thái)               |
| `aggregate`        | `scorers/aggregate.py`        | trung bình macro/micro và tỉ lệ khớp hoàn toàn                       |
| `confusion`        | `scorers/confusion.py`        | ma trận nhầm theo khía cạnh (chỉ vào `metrics.json`, không vào CSV)  |

Thêm một cách chấm mới: viết một module theo hợp đồng ở `scorers/base.py` rồi thêm một dòng vào
`SCORERS`. Tên lạ trong `scores` bị báo lỗi kèm danh sách, không im lặng bỏ qua.

Điểm macro chỉ lấy trung bình trên các đơn vị CÓ dữ liệu để chấm: một khía cạnh không được nhắc
trong tập con đang chấm không bị tính là 0 - tính là 0 thì điểm tụt mà không có lỗi nào cả. Số ô
của từng đơn vị vẫn nằm trong `metrics.csv` nên cách tính này không che mất thông tin.

## File kết quả

| File                 | Nội dung                                                                      |
| -------------------- | ----------------------------------------------------------------------------- |
| `metrics.json`       | toàn metric, kèm `label_space`, `neutral_policy`, số ô bị loại                |
| `metrics.csv`        | bảng dài: `aspect`, `sentiment`, `metric`, `value`, để so giữa các thí nghiệm |
| `mispredictions.csv` | chỉ các dòng đoán sai, kèm khía cạnh, nhãn đúng, nhãn đoán                    |
| `plots/`             | biểu đồ của lượt chạy: `plots/accuracy.html`, HTML tự chứa, mở được khi không có mạng; tắt bằng `save.plots: false` |

`metrics.json` gồm: `label_space`, `neutral_policy`, `not_mentioned`, `dropped_neutral` (và
`dropped_neutral_by_aspect`), `n_reviews`, `aspects`, `scores` (mỗi bộ chấm một khối), `tables`
(ma trận nhầm theo khía cạnh), và thông tin của lần chạy (prompt, model, cách sinh, chi phí).
Khoá `rescored` xuất hiện khi file được chấm lại từ `predictions.csv` thay vì chạy lại model - công cụ
chấm lại (`run_rescore_eval.py`) đã bỏ 25/09/2026, nên khoá này chỉ còn trong các file cũ.

Trong `metrics.csv`, giá trị `all` ở cột `aspect` hoặc `sentiment` nghĩa là "gộp mọi giá trị của
cột đó" - ví dụ dòng `all, all, accuracy_macro` là con số tổng hợp. `plots/` do bước sinh báo cáo
vẽ từ `metrics.json` và `predictions.csv`, không phải do phần chấm điểm.

## Bảng tổng hợp

`data/reports/metrics_matrix/accuracy_by_aspect.csv` có dòng là khía cạnh, cột là từng thí nghiệm
và một cột `reference` chứa số của công bố.
`data/reports/metrics_matrix/prf_by_aspect_sentiment.csv` có cùng định dạng với bảng P R F1 của công bố.

### Hai cột nói lượt chạy có DÙNG ĐƯỢC trong bảng so hay không

`experiment_registry` có thêm ba cột, sinh bằng cách hỏi chính git và chính bản ghi của lượt chạy:

| Cột | Nghĩa | Vì sao cần |
| --- | --- | --- |
| `valid` | commit của lượt chạy có nằm trên nhánh đã ghim (`origin/<nhánh>` trong `run_meta.json`) không: `yes` / `no` / `chưa rõ` | lượt chấm bằng commit CHƯA merge vẫn ra số, nhưng không ai tái lập được từ bản code đã công bố |
| `comparable` | cơ sở đo (`data.build`, `label_space`, `neutral_policy`, `not_mentioned`, `split`, bộ chấm) có khớp lượt CHUẨN không - lượt chuẩn là lượt `FINISHED` sớm nhất trong bảng | hai cột cạnh nhau mà khác cơ sở đo thì lệch vì ĐO KHÁC, không phải vì model khác |
| `invalid_reason` | lý do gộp của cả hai cột trên, rỗng khi cả hai đều `yes` | người đọc biết ngay vì sao, không phải mở `run.log` dò |

`chưa rõ` là giá trị riêng, không gộp vào `no`: máy không có git, thiếu ref, hoặc `run_meta.json` không
ghi commit thì **không kiểm được** - ghi thành "không hợp lệ" là nói dối kiểu khác. Việc gọi git đi qua
`src/workflow/repo.py` và mỗi cặp (commit, nhánh) chỉ hỏi một lần, nên bảng nhiều dòng vẫn chỉ tốn một lệnh.

### Hai bộ bảng, tách rõ: toàn bộ và chỉ lượt thành công

`python scripts/collect_reports.py` sinh năm nhóm, mỗi nhóm ba định dạng (`.csv`, `.html`, `.md`):

| Nhóm | Gồm những lượt nào | Dùng để |
| --- | --- | --- |
| `attempt_registry` | **MỌI lần thử**, kể cả lượt HỎNG, kèm `status`, thời lượng và `reason` (lý do dừng đọc từ `errors.json`) | bản tổng hợp TOÀN BỘ: đã thử gì, hỏng vì sao, tốn bao lâu |
| `metrics_matrix`, `experiment_registry`, `model_input`, `dataset_registry` | mặc định **chỉ lượt `FINISHED`** | đọc số và so với công bố |

Vì sao tách: lượt hỏng không có `metrics.json`, nên mọi ô số của nó đều trống - đưa vào bảng số là làm
nhiễu đúng chỗ dùng để đọc kết quả (đã gặp thật: bảng hiện bốn dòng PhoBERT, ba dòng rỗng). Muốn bảng số
liệt kê cả lượt hỏng thì thêm `--only all`; nhóm `attempt_registry` thì **luôn** liệt kê đủ, không phụ
thuộc cờ này.
