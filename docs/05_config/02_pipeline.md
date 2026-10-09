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
| `steps`      | bật tắt từng bước xử lý, ví dụ `steps.clean.deduplicate`, `steps.clean.remove_ads` |
| `steps.<tên>.apply_to` | PHẠM VI: các split mà bước đó được SỬA. Không khai thì bước sửa mọi split (hành vi `v0.1.0`). `v0.2.0` khai `[train, val]` cho Clean và Normalize, nên `test` giữ nguyên bản dữ liệu gốc |
| `steps.clean.leakage.keep_priority` | thứ tự ưu tiên khi một review xuất hiện ở nhiều split: giữ ở tập đứng trước, loại khỏi các tập sau. `v0.2.0` khai `[test, val, train]`, nên `test` không bao giờ bị loại |
| `steps.clean.leakage.remove_eval_overlap` | luật của `v0.1.0`: bỏ khỏi val/test, giữ trong train. Còn trong code để bản dữ liệu cũ tái lập được; khai CẢ HAI luật là lỗi |
| `steps.normalize.remove_emoji` | bỏ emoji khỏi văn bản (`v0.3.0`). Bản không khai khoá này thì phép đó coi như TẮT, nên báo cáo của chúng **không đổi một dòng** nào so với trước |
| `thresholds` | ngưỡng dùng trong các bước                                               |

## Luật

- `test` **không bị sửa**: mỗi bước chỉ được sửa split có tên trong `apply_to` của nó, và bước Final
  Validate chứng minh **từng dòng** của split ngoài phạm vi bằng ĐÚNG văn bản gốc.
- **Rò rỉ dữ liệu** xử lý ở phía tập HỌC: `steps.clean.leakage.keep_priority` giữ bản ghi ở tập ưu tiên
  cao hơn và loại khỏi các tập thấp hơn (`[test, val, train]` nghĩa là `test` không bao giờ bị loại).
  Luật cũ của `v0.1.0` (`remove_eval_overlap`) loại ở val/test; nó vẫn chạy được để bản dữ liệu cũ tái
  lập được, nhưng không dùng cho phiên bản mới.
- Đổi **code** xử lý thì phải tăng `version` của pipeline, vì logic nằm ở code chứ không nằm ở file này.
- Chạy phải nói rõ phiên bản: `python run_pipeline.py --name cosmetics --version v0.3.0` (bản đang
  dùng; `v0.2.0` vẫn chạy được và cho đúng bộ dữ liệu cũ).

## Liên quan tới mã phiên bản dữ liệu

`mã = <name>-ds<dataset_version>-pl<pipeline_version>-src<nguồn>@<phiên bản>-<hash8>`

Trong đó `hash8` băm từ: file dataset version, file pipeline version, và tên cộng nội dung mọi file raw của các nguồn.
