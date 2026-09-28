# Nhật ký phiên bản dữ liệu

> Đọc file này khi: muốn biết một mã phiên bản dữ liệu sinh ra từ đâu, hoặc cần tra dòng dõi.
> Liên quan: `docs/01_dataset/01_raw_data.md`, `docs/05_config/03_datasets.md`, `docs/03_pipeline/05_output.md`

File này là bản NGƯỜI ĐỌC của dòng dõi dataset. Bảng máy đọc nằm ở
`data/reports/dataset_registry/dataset_registry.csv` (cột `parent`), sinh bằng
`python scripts/collect_reports.py`. Ở đây ghi **vì sao** có phiên bản đó và nó thay cái gì - thứ mà
một dòng CSV không chứa được.

Mã phiên bản có dạng `<dataset>-ds<phiên bản>-pl<phiên bản pipeline>-src<nguồn>@<phiên bản>-<hash8>`;
hash8 băm cả file cấu hình dataset, file cấu hình pipeline và **nội dung dữ liệu gốc**, nên cùng một
nhãn `v0.1.0` mà sửa dữ liệu gốc là ra mã KHÁC (`docs/05_config/03_datasets.md`).

## cosmetics

### `cosmetics-ds0.1.0-pl0.1.0-srccosmetics@0.1.0-e0ccc484` - bản dùng cho mọi kết quả hiện có

| Thứ | Giá trị |
| --- | --- |
| Cấu hình dataset | `configs/datasets/cosmetics/v0.1.0.yaml`, `sha256` `e40c156b…` |
| Cấu hình pipeline | `configs/pipeline/v0.1.0.yaml`, `sha256` `54731c64…` |
| `parent` | không khai - bản đầu tiên, sinh trực tiếp từ dữ liệu gốc |
| Lý do có phiên bản này | bản đầu tiên dưới cấu trúc mã phiên bản mới; dữ liệu gốc `v0.1.0` đi qua pipeline `v0.1.0` |

Dữ liệu gốc đi vào (đếm theo dòng, `sha256` băm từ file nhận được):

| File | Dòng | `sha256` (rút gọn) |
| --- | --- | --- |
| `data/raw/cosmetics/v0.1.0/data_train.csv` | 19.152 | `53486079…` |
| `data/raw/cosmetics/v0.1.0/data_val.csv` | 2.366 | `6d8c959f…` |
| `data/raw/cosmetics/v0.1.0/data_test.csv` | 2.410 | `4c615750…` |
| `data/raw/cosmetics/v0.1.0/full_data.csv` | 23.928 | `edaa7722…` |

Đi ra (`data/processed/<mã>/`): `train.csv` 12.302 dòng, `val.csv` 1.524, `test.csv` 1.518,
`label_map.json`, `processing_log.json`. Pipeline bỏ 883 dòng tính trên cả ba split (trước: 12.981 /
1.623 / 1.623), và 0 vấn đề ở bước kiểm schema.

Khoá tập đánh giá (`eval_lock.json`):

```json
{"test": {"file": "test.csv",
          "sha256": "e25581375bf4573a5781df6a6b004474ab043f97e9a2462a3c62209594a6c67e",
          "rows": 1518}}
```

Mọi kết quả trong `docs/06_plan/P7_rerun.md` và mọi thí nghiệm trong `experiments/` chấm trên **đúng**
`test.csv` này; đổi nó là mọi con số cũ không còn so được.

Cập nhật 28/09/2026 - khoá có thêm **vân tay DỮ LIỆU**:

```json
{"test": {"schema": 1,
          "file": "test.csv",
          "sha256": "e2558137...",
          "records_sha256": "fa91b1d9...",
          "rows": 1518}}
```

`sha256` **không đổi** so với giá trị đã ghi 25/09/2026 (byte của file y nguyên), nên vẫn là dấu vân tay
byte của bản đã công bố. `records_sha256` là vân tay của **tập bản ghi** và từ nay là căn cứ phán quyết:
đổi cách ghi file không còn làm mất quyền so với công bố. Xem `docs/03_pipeline/05_output.md` mục 5.

**Sự việc 25/09/2026 - đổi cách ghi CSV làm lệch khoá byte.** Commit
`fix(utils): keep one CSV record per physical line` (25/09 13:48) đổi `utils.write_csv` để ký tự xuống
dòng trong ô ra hai ký tự `\n` (để bảng dự đoán đọc được bằng Notepad), và `{train,val,test}.csv` của
dataset cũng theo đó. Byte đổi nên `sha256` của `test.csv` thành `9ac701de…` dù **1.518 bản ghi y
nguyên**; lượt chạy 27/09 vì thế dừng ở `VersionError` ("khoá đã có và KHÁC lần này"). Đã sửa theo hai
hướng: `export` ghi dataset bằng `single_line=False` (byte trở lại đúng `e2558137…`), và khoá thêm
`records_sha256` để lần sau đổi cách ghi không còn là sự cố.

### `…-bf68b1c5` - bản đã XOÁ (lỗi băm, 25/09/2026)

Tồn tại rất ngắn: nó ra đời trước khi lỗi băm ở P2 được sửa (`hash8` chưa gồm đủ đầu vào), nên mã phiên
bản không phân biệt được hai bộ dữ liệu khác nhau. Đã xoá và dựng lại thành `…-e0ccc484`; dữ liệu bên
trong hai bản giống nhau, chỉ mã khác. Số đo của tập đánh giá lúc đó là `64dbf812…` với 2.271 "dòng"
- con số 2.271 là ĐẾM DÒNG chứ không phải số bản ghi, xem `docs/06_plan/P5_notebook_pin.md`.

## Thêm một phiên bản mới thì ghi gì vào đây

1. Chạy pipeline cho phiên bản mới: `python run_pipeline.py --dataset <tên> --version <phiên bản>`.
2. Khai `parent` trong `configs/datasets/<tên>/<phiên bản>.yaml` = mã phiên bản trước đó.
3. Chép vào đây một mục như trên: mã, cấu hình + `sha256`, `parent`, lý do có phiên bản này, số dòng
   vào/ra, và `eval_lock` nếu tập đánh giá đổi. Lý do là phần quan trọng nhất - cột `parent` trong
   `dataset_registry.csv` chỉ nói "kế thừa từ đâu", không nói "vì sao".
4. Chạy lại `python scripts/collect_reports.py` để cột `parent` trong bảng khớp với file này.
