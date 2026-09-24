# 05.01. Cấu hình đường dẫn

> Đọc file này khi: đổi cấu trúc thư mục, hoặc thêm một loại file kết quả mới.
> Liên quan: `docs/00_workflow/06_conventions.md`, `src/paths.py`

File: `configs/paths.yaml`. Đây là **nguồn duy nhất** khai báo đường dẫn của dự án.

## Các nhóm khoá

| Nhóm        | Nội dung                                                                                    |
| ----------- | ------------------------------------------------------------------------------------------- |
| `version`   | phiên bản của chính file cấu hình này                                                       |
| `roots`     | thư mục gốc: `data`, `configs`, `experiments`, `templates`, `docs`                          |
| `data`      | `raw`, `processed`, `models`, `reports`, `assets`, `reference_publication`                  |
| `reports`   | bốn nhóm report: `dataset_registry`, `experiment_registry`, `model_input`, `metrics_matrix` |
| `configs`   | `datasets`, `models`, `prompts`, `pipeline`, `experiment`, `paths`, `dagshub`               |
| `patterns`  | mẫu tên thư mục và file kết quả                                                             |
| `colab`     | đường dẫn Drive cần thử, file đánh dấu, đường dẫn file env của Colab                        |
| `canonical` | `ordered_lists`: danh sách nào có thứ tự có nghĩa khi băm cấu hình                          |

## Mẫu tên quan trọng

| Khoá             | Mẫu                                                                | Ví dụ                                         |
| ---------------- | ------------------------------------------------------------------ | --------------------------------------------- |
| `data_version`   | `{name}-ds{dataset_version}-pl{pipeline_version}-src{src}-{hash8}` | `cosmetics-ds0.3.0-pl0.2.0-src0.2.0-9c0d1e2f` |
| `run_log`        | `run.log`                                                          |                                               |
| `run_meta`       | `run_meta.json`                                                    |                                               |
| `metrics_json`   | `metrics.json`                                                     |                                               |
| `metrics_csv`    | `metrics.csv`                                                      |                                               |
| `errors`         | `errors.json`                                                      | chỉ tạo khi có lỗi                            |
| `predictions`    | `predictions.csv`                                                  |                                               |
| `mispredictions` | `mispredictions.csv`                                               |                                               |
| `model_input`    | `model_input.csv`                                                  |                                               |
| `pred_parts`     | `predictions/part_{n:04d}.jsonl`                                   | khối tiến độ để resume                        |
| `plots`          | `plots`                                                            |                                               |
| `ckpt_last`      | `model/last`                                                       | đủ để resume                                  |
| `ckpt_best`      | `model/best`                                                       | chỉ adapter                                   |

## Cách dùng trong code

```python
from src import paths
paths.root()
paths.data("raw")
paths.processed(ma)
paths.report("experiment_registry")
paths.experiment_dir(model_id, method, exp_id)
paths.results_dir(model_id, method, exp_id, ma)
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
