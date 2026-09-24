# 05.03. Cấu hình dataset

> Đọc file này khi: thêm dataset mới, sửa schema, hoặc tạo phiên bản dataset mới.
> Liên quan: `docs/01_dataset/02_schema.md`, `docs/05_config/02_pipeline.md`

File: `configs/datasets/<name>/<version>.yaml`. Mỗi phiên bản một file, **bất biến**.

## Ví dụ đầy đủ

```yaml
schema_version: 1
name: cosmetics
version: "0.3.0" # trùng tên file
sources: # danh sách nguồn; kind là trường của TỪNG phần tử
  - { kind: raw, name: cosmetics, raw_version: v0.2.0 }
pipeline_version: v0.2.0
format: csv
splits: { train: train.csv, val: val.csv, test: test.csv }
full: full_data.csv
schema:
  text: { column: data }
  id: { column: null }
  aspects: [stayingpower, texture, smell, price, colour, shipping, packing]
  labels: [positive, negative, neutral]
  drop: [others]
  keep: []
aspect_policy: union
parent: v0.2.0
notes: "dùng raw v0.2.0; gộp thêm nguồn shopee theo tỉ lệ 2:1"
eval_lock:
  test: { file: test.csv, sha256: "<hash>", rows: 1600 }
```

## Giải thích từng khoá

| Khoá                    | Ý nghĩa                                                                                                                               |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `schema_version`        | phiên bản của cách khai báo này; đổi khi đổi tên khoá                                                                                 |
| `name`                  | tên dataset, cũng là tên thư mục cha                                                                                                  |
| `version`               | nhãn phiên bản dataset, trùng tên file                                                                                                |
| `sources`               | danh sách nguồn đi vào dataset. Mỗi phần tử có `kind` riêng                                                                           |
| `sources[].kind`        | `raw` hoặc `dataset`. Hỗn hợp được, ví dụ phần tử thứ nhất là dataset, thứ hai là raw                                                 |
| `sources[].raw_version` | bắt buộc khi `kind: raw`                                                                                                              |
| `sources[].version`     | bắt buộc khi `kind: dataset`                                                                                                          |
| `pipeline_version`      | phiên bản pipeline dùng để tạo dataset này                                                                                            |
| `format`                | `csv`, `jsonl`, `parquet`; tương ứng một loader đã đăng ký                                                                            |
| `splits`                | tên file của ba split                                                                                                                 |
| `full`                  | file gộp toàn bộ dữ liệu, tuỳ chọn                                                                                                    |
| `schema`                | ánh xạ raw sang dataset: cột văn bản, cột định danh, danh sách khía cạnh, nhãn, cột bỏ, cột giữ                                       |
| `aspect_policy`         | cách xử lý khi các nguồn có bộ khía cạnh khác nhau: `union` (thiếu thì điền "không nhắc tới" và ghi cảnh báo) hoặc `strict` (báo lỗi) |
| `parent`                | phiên bản trước đó, dùng để dựng lại changelog                                                                                        |
| `notes`                 | vì sao có phiên bản này, gồm cả mô tả cách gộp nguồn                                                                                  |
| `eval_lock`             | dấu vân tay của tập đánh giá, xem mục dưới                                                                                            |

## eval_lock

Chốt tập đánh giá để kết quả so được với công bố tham chiếu:

- Pipeline phải xuất ra `test.csv` có `sha256` khớp giá trị trong `eval_lock`, nếu lệch thì báo lỗi.
- Mọi biến đổi văn bản chỉ áp cho train và val.
- Nếu muốn thử biến đổi cả test thì đặt `eval_lock.enforce: false`; kết quả sẽ bị đánh dấu
  `comparable: false` và không dùng để so với công bố.

## Luật bất biến

File phiên bản đã dùng thì không sửa. Guard so `sha256` của file với giá trị đã ghi trong mọi
`processing_log.json`; lệch thì báo lỗi và hướng dẫn tạo phiên bản mới.
