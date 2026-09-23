# 05.02. Cấu hình xử lý dữ liệu (pipeline)

> Đọc file này khi: sửa cách làm sạch dữ liệu.
> Liên quan: `docs/03_pipeline/01_flow.md` · `docs/05_config/03_datasets.md`

Tệp: `configs/pipeline/<version>.yaml`. Mỗi phiên bản là một tệp riêng và **bất biến**.

## Vì sao tách theo phiên bản

Nội dung tệp này đi vào mã phiên bản dữ liệu. Nếu sửa tại chỗ thì hai định nghĩa khác nhau
sẽ mang cùng một nhãn phiên bản, và kết quả cũ không còn tra được. Vì vậy muốn đổi thì tạo tệp mới.

## Các khoá

| Khoá | Ý nghĩa |
|---|---|
| `version` | nhãn phiên bản, trùng tên tệp |
| `parent` | phiên bản trước đó, `null` nếu là bản đầu |
| `notes` | vì sao có phiên bản này |
| `steps` | bật tắt từng bước xử lý, ví dụ `clean.deduplicate`, `normalize.teencode` |
| `thresholds` | ngưỡng dùng trong các bước |

## Luật

- `test` chỉ đi qua pipeline ở chế độ không biến đổi văn bản, để so được với công bố tham chiếu.
- Đổi **code** xử lý thì phải tăng `version` của pipeline, vì logic nằm ở code chứ không nằm ở tệp này.
- Chạy phải nói rõ phiên bản: `python run_pipeline.py --dataset cosmetics --version v0.2.0`.

## Liên quan tới mã phiên bản dữ liệu

`mã = <name>-ds<dataset_version>-pl<pipeline_version>-src<nguồn>@<phiên bản>-<hash8>`

Trong đó `hash8` băm từ: tệp dataset version, tệp pipeline version, và tên cộng nội dung mọi tệp raw của các nguồn.
