# 05.02. Cấu hình xử lý dữ liệu (pipeline)

> Đọc file này khi: sửa cách làm sạch dữ liệu.
> Liên quan: `docs/03_pipeline/01_flow.md`, `docs/05_config/03_datasets.md`

File: `configs/pipeline/<version>.yaml`. Mỗi phiên bản là một file riêng và **bất biến**.

## Vì sao tách theo phiên bản

Nội dung file này đi vào mã phiên bản dữ liệu. Nếu sửa tại chỗ thì hai định nghĩa khác nhau
sẽ mang cùng một nhãn phiên bản, và kết quả cũ không còn tra được. Vì vậy muốn đổi thì tạo file mới.

## Các khoá

| Khoá         | Ý nghĩa                                                                  |
| ------------ | ------------------------------------------------------------------------ |
| `version`    | nhãn phiên bản, trùng tên file                                           |
| `parent`     | phiên bản trước đó, `null` nếu là bản đầu                                |
| `notes`      | vì sao có phiên bản này                                                  |
| `steps`      | bật tắt từng bước xử lý, ví dụ `steps.clean.deduplicate`, `steps.normalize.teencode` |
| `thresholds` | ngưỡng dùng trong các bước                                               |

## Luật

- `test` chỉ đi qua pipeline ở chế độ không biến đổi văn bản, để so được với công bố tham chiếu.
- Đổi **code** xử lý thì phải tăng `version` của pipeline, vì logic nằm ở code chứ không nằm ở file này.
- Chạy phải nói rõ phiên bản: `python run_pipeline.py --dataset cosmetics --version v0.2.0`.

## Liên quan tới mã phiên bản dữ liệu

`mã = <name>-ds<dataset_version>-pl<pipeline_version>-src<nguồn>@<phiên bản>-<hash8>`

Trong đó `hash8` băm từ: file dataset version, file pipeline version, và tên cộng nội dung mọi file raw của các nguồn.
