# 05.05. Cấu hình dùng chung cho thí nghiệm

> Đọc file này khi: đổi cách chấm điểm, cách huấn luyện, hoặc cách ghi nhận kết quả.
> Liên quan: `docs/05_config/06_experiment.md`, `docs/04_experiments/metrics.md`

Năm file trong `configs/experiments/`. Chúng hợp nhất với nhau và với cấu hình riêng của thí nghiệm.

## repo.yaml

| Khoá               | Ý nghĩa                                                |
| ------------------ | ------------------------------------------------------ |
| `url`              | địa chỉ repo GitHub                                    |
| `branch`           | nhánh duy nhất notebook kéo code, hiện là `experiment` |
| `allowed_branches` | danh sách nhánh được phép; để trống thì tắt kiểm       |

## task.yaml - định nghĩa bài toán

| Khoá             | Giá trị                                                 | Ý nghĩa                                                                                                                                                               |
| ---------------- | ------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `label_space`    | `binary` (mặc định) hoặc `full`                         | `binary`: chỉ positive và negative, cộng một quyết định nhị phân riêng là "có nhắc tới hay không". `full`: bốn trạng thái gồm không nhắc, positive, negative, neutral |
| `neutral_policy` | `drop` (mặc định), `as_negative`, `as_positive`, `keep` | cách xử lý ô có nhãn `neutral` khi ở `binary`. Số ô bị loại được ghi vào `metrics.json`                                                                               |
| `not_mentioned`  | `separate` (mặc định), `as_class`                       | `separate`: "có nhắc tới hay không" là quyết định nhị phân riêng, đúng như công bố. `as_class`: coi đó là một lớp                                                     |
| `aspects`        | `all` hoặc danh sách                                    | giới hạn khía cạnh dùng cho thí nghiệm                                                                                                                                |

Việc chiếu nhãn theo `label_space` là một bước của **tiền xử lý cho model**, không phải của pipeline.
Pipeline giữ nguyên bốn trạng thái.

## evaluation.yaml - cách chấm điểm

| Khoá               | Ý nghĩa                                                                                                     |
| ------------------ | ----------------------------------------------------------------------------------------------------------- |
| `n`                | số mẫu dùng để chấm; `null` nghĩa là toàn bộ split                                                          |
| `decoding`         | cách sinh văn bản: `greedy` chọn token xác suất cao nhất nên tất định; `sample` có `temperature` và `top_p` |
| `scores`           | danh sách tên chỉ số cần tính; tên phải có trong registry `SCORERS`, thiếu tên thì báo lỗi                  |
| `group_by`         | chiều phân rã bảng chỉ số, ví dụ theo `aspect` và `sentiment`                                               |
| `save.predictions` | ghi `predictions.csv` hay không                                                                             |
| `save.plots`       | ghi thư mục `plots/` hay không                                                                              |
| `save.confusion`   | ghi ma trận nhầm theo khía cạnh hay không                                                                   |

## training.yaml - huấn luyện

| Khoá                                                          | Ý nghĩa                                                                                 |
| ------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| `enabled`                                                     | `true` với thí nghiệm LoRA hoặc QLoRA. Khi `true`, `roles` bắt buộc có `train` và `val` |
| `lora.r`, `lora.alpha`, `lora.dropout`, `lora.target_modules` | tham số LoRA                                                                            |
| `lr`, `batch`, `epochs`, `grad_accum`, `weight_decay`         | tham số huấn luyện. `weight_decay` là weight decay thật                                 |
| `checkpoint.every_n_steps`                                    | lưu checkpoint mỗi bao nhiêu bước                                                       |
| `checkpoint.keep_last_k`                                      | giữ bao nhiêu checkpoint gần nhất để resume; cũ hơn thì xoá                             |
| `checkpoint.save_last`                                        | lưu `model/last` đủ để chạy tiếp                                                        |
| `checkpoint.save_best`                                        | lưu `model/best` theo chỉ số trên `val`                                                 |
| `checkpoint.delete_intermediate`                              | xoá ngay các `checkpoint-*` trung gian sau mỗi lần lưu, để tiết kiệm Drive              |

## tracking.yaml - ghi nhận kết quả

| Khoá          | Ý nghĩa                                                                                              |
| ------------- | ---------------------------------------------------------------------------------------------------- |
| `tracker`     | `mlflow`, `local_json` hoặc `none`; tên phải có trong registry `TRACKERS`                            |
| `experiment`  | tên experiment trên máy chủ MLflow                                                                   |
| `mlflow_tags` | nhãn của run trên DagsHub, không phải git tag. Giá trị `auto` nghĩa là notebook tự lấy từ `run_meta` |
| `artifacts`   | danh sách file nhỏ được tải lên; không tải checkpoint                                                |
