# 05.01. Cấu hình đường dẫn

> Đọc file này khi: đổi cấu trúc thư mục, hoặc thêm một loại file kết quả mới.
> Liên quan: `docs/00_workflow/06_conventions.md`, `src/core/paths.py`

File: `configs/paths.yaml`. Đây là **nguồn duy nhất** khai báo đường dẫn của dự án.

## Các nhóm khoá

| Nhóm        | Nội dung                                                                                    |
| ----------- | ------------------------------------------------------------------------------------------- |
| `version`   | phiên bản của chính file cấu hình này                                                       |
| `roots`     | thư mục gốc: `data`, `configs`, `experiments`, `templates`, `docs`                          |
| `data`      | `raw`, `processed`, `models`, `reports`, `assets`, `reference_publication`                  |
| `reports`   | năm nhóm report của `scripts/collect_reports.py`: `dataset_registry`, `experiment_registry`, `attempt_registry` (mọi lần thử, kể cả lượt hỏng), `model_input`, `metrics_matrix` - cộng nhóm `fusion` (bảng KẾT HỢP của sáu script hợp nhất; **không** đi qua `collect_reports.py`) |
| `configs`   | `datasets`, `models`, `prompts`, `pipeline`, `experiment`, `paths`, `dagshub`               |
| `patterns`  | mẫu tên thư mục và file kết quả                                                             |
| `colab`     | đường dẫn Drive cần thử, file đánh dấu, đường dẫn file env của Colab                        |
| `canonical` | `ordered_lists`: danh sách nào có thứ tự có nghĩa khi băm cấu hình                          |

## Mẫu tên quan trọng

| Khoá             | Mẫu                                                                | Ví dụ                                         |
| ---------------- | ------------------------------------------------------------------ | --------------------------------------------- |
| `data_version`   | `{name}-ds{dataset_version}-pl{pipeline_version}-src{src}-{hash8}` với `{src}` là `<tên nguồn>@<phiên bản>` | `cosmetics-ds0.2.0-pl0.2.0-srccosmetics@0.1.0-e616c1e3` |
| `run_log`        | `run.log`                                                          |                                               |
| `run_meta`       | `run_meta.json`                                                    |                                               |
| `run_meta_dir`   | `results`                                                          | thư mục chứa các lượt chạy (một tầng; con là `<hash8>`) |
| `metrics_json`   | `metrics.json`                                                     |                                               |
| `metrics_csv`    | `metrics.csv`                                                      |                                               |
| `errors`         | `errors.json`                                                      | chỉ tạo khi có lỗi                            |
| `predictions`    | `predictions.csv`                                                  |                                               |
| `mispredictions` | `mispredictions.csv`                                               | ô đoán sai theo cơ sở `all`                   |
| `mispredictions_paper` | `mispredictions_paper.csv`                                   | ô đoán sai theo cơ sở `paper` (tập con)       |
| `model_input`    | `model_input.csv`                                                  |                                               |
| `pred_parts`     | `predictions/part_{n:04d}.jsonl`                                   | khối tiến độ để resume                        |
| `plots`          | `plots`                                                            |                                               |
| `ckpt_last`      | `model/last`                                                       | đủ để resume                                  |
| `ckpt_best`      | `model/best`                                                       | chỉ adapter                                   |
| `ckpt_snapshot`  | `model/checkpoint-{step}`                                          | ảnh chụp trung gian để chạy tiếp               |
| `token_stats`    | `token_stats.csv`                                                  | số đo input thật, cấu hình mặc định           |
| `token_stats_tagged` | `token_stats__{tag}.csv`                                       | số đo khi truyền `--prompt`/`--segmenter`     |
| `archive_dir`    | `_archive`                                                         | kho LỊCH SỬ bảng số đo: bảng của một bộ ví dụ/khối hệ thống không còn tái lập được thì chuyển vào đây (nằm NGOÀI `model_input/`; xem `docs/04_experiments/02_model_input.md` mục 2.2) |
| `raw_meta`       | `raw_meta.yaml`                                                    | nguồn + sha256 của một phiên bản dữ liệu gốc  |
| `processing_log` | `processing_log.json`                                              | dấu vết của lần chạy pipeline                 |
| `label_map`      | `label_map.json`                                                   | danh sách khía cạnh + mã nhãn                 |
| `eval_lock`      | `eval_lock.json`                                                   | khoá tập đánh giá, ghi một lần khi tạo dữ liệu |
| `metrics_rescored_json` | `metrics_rescored.json`                                      | số đo THÊM (rescore) - KHÔNG ghi đè `metrics.json` |
| `metrics_rescored_csv` | `metrics_rescored.csv`                                        | bảng dài của số đo THÊM                            |
| `training_history` | `training_history.csv`                                           | lịch sử huấn luyện (loss/chỉ số theo bước và theo epoch) của lượt chạy encoder |
| `probabilities`  | `probabilities.csv`                                                | xác suất từng ô `p(mã)` - CHỈ đường encoder; bước kết hợp cần (không vào git) |
| `eda_dir`        | `eda`                                                              | thư mục kết quả EDA                           |
| `pipeline_dir`   | `pipeline`                                                         | thư mục báo cáo của lần chạy pipeline         |
| `experiment_config` | `config.yaml`                                                   | config riêng của một thí nghiệm               |
| `experiment_tmp` | `_tmp`                                                             | thư mục tạm của một thí nghiệm                |


## Cách dùng trong code

```python
from src.core import paths
paths.root()
paths.data("raw")
paths.processed(ma)
paths.report("experiment_registry")
paths.experiment_dir(model_id, method, exp_id)
paths.results_dir(model_id, method, exp_id)     # .../<model>/<method>/<exp>/results/ (một tầng;
                                                # thư mục lượt chạy là con, tên = mã băm danh tính)
paths.pattern("run_meta")
```

## Ghi đè khi chạy trên Colab

Hai biến môi trường đổi gốc đường dẫn, không cần symlink:

| Biến                      | Ý nghĩa                           |
| ------------------------- | --------------------------------- |
| `SENTIMENTX_DATA_ROOT`    | gốc thay cho `<repo>/data`        |
| `SENTIMENTX_RESULTS_ROOT` | gốc thay cho `<repo>/experiments` |

## Giới hạn đã biết

- `.gitignore` và `.gitattributes` không đọc được YAML, nên khi đổi cây thư mục vẫn phải sửa tay hai file đó.
- Trong code chỉ còn `ROOT_DIR` suy từ `__file__`, vì cần nó để tìm ra file cấu hình này.
