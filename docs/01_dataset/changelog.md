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

### `cosmetics-ds0.2.0-pl0.2.0-srccosmetics@0.1.0-e616c1e3` - bản so được với công bố (01/10/2026)

| Thứ | Giá trị |
| --- | --- |
| Cấu hình dataset | `configs/datasets/cosmetics/v0.2.0.yaml`, `sha256` `a5cae2b8…` |
| Cấu hình pipeline | `configs/pipeline/v0.2.0.yaml`, `sha256` `b7f6e8fc…` |
| `parent` | `cosmetics-ds0.1.0-pl0.1.0-srccosmetics@0.1.0-e0ccc484` |
| Lý do có phiên bản này | `test` phải bằng ĐÚNG dữ liệu gốc thì con số mới đặt được cạnh bảng của công bố, và rò rỉ dữ liệu phải được xử lý ở phía tập HỌC để điểm của lượt học không bị "phồng" |

Dữ liệu gốc đi vào: **y như bản trên** - cùng bốn file, cùng `sha256` (đổi cách xử lý, không đổi đầu vào).

Đi ra (`data/processed/<mã>/`): `train.csv` 12.268 dòng, `val.csv` 1.535, `test.csv` **1.623**.

**Khác bản v0.1.0 đúng một điều**: Clean và Normalize chỉ SỬA `train` và `val`
(`steps.clean.apply_to: [train, val]`, `steps.normalize.apply_to: [train, val]`), nên `test.csv` giữ
nguyên từng ký tự của dữ liệu gốc. Ba phép kiểm bằng máy:

- 1.623 dòng, **0 dòng lệch văn bản và 0 ô lệch nhãn** so với `data_test.csv`;
- bước Final Validate của chính pipeline in: *"1623 dòng thuộc test bằng ĐÚNG bản gốc, không bị sửa ký
  tự nào"*;
- **0 cặp trùng** theo `utils.dedup_key` giữa ba tập: `train∩val = train∩test = val∩test = 0`.

Rò rỉ dữ liệu vì vậy được xử lý ở phía tập HỌC: `steps.clean.leakage.keep_priority: [test, val, train]`
giữ bản ghi ở tập ưu tiên cao hơn và loại khỏi các tập thấp hơn, nên `test` không bao giờ bị loại. Số
dòng bị loại của bước Clean: `train` 706 (trong đó 226 dòng trùng `test`, 23 dòng trùng `val`),
`val` 86, `test` **0**.

Ba tập đều khác bản cũ: `train` −34 dòng, `val` +11 dòng, `test` +105 dòng (69 dòng nhiễu mà bản cũ đã
bỏ khỏi test, cộng các dòng trùng train mà bản cũ cũng bỏ khỏi test). Bản v0.1.0 **giữ nguyên** trong
`data/processed/` làm dấu vết, không xoá.

Khoá tập đánh giá (`eval_lock.json`) - hai giá trị này đã khai trong config TRƯỚC lần chạy chính thức:

```json
{"test": {"schema": 1, "file": "test.csv",
          "sha256": "af349bf51739884b545e277ac5e0f8492e6a59aaba2739cd9fcb171ed3beba38",
          "records_sha256": "73d39d84536b14e35c07bc2012e8059ee9867165629b029ed24bddcf3eda3cb6",
          "rows": 1623}}
```

Cách so với công bố: `test` nguyên bản + **cơ sở đo `paper`** - xem
`docs/04_experiments/reference_publication.md` mục "Cách so" và `docs/04_experiments/metrics.md` mục
"Hai cơ sở đo". Cả 12 thí nghiệm trong `experiments/` đã chuyển sang phiên bản này.

### `cosmetics-ds0.1.0-pl0.1.0-srccosmetics@0.1.0-e0ccc484` - bản cũ, giữ làm dấu vết

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

Mọi kết quả trong `docs/06_plan/P7_rerun.md` mục 2 và mọi thí nghiệm trong `experiments/` **trước
01/10/2026** chấm trên *đúng* `test.csv` này; đổi nó là mọi con số cũ không còn so được. Từ 01/10/2026,
`experiments/` chấm trên bản `…-e616c1e3` ở trên (test = dữ liệu gốc, 1.623 dòng); bản này giữ nguyên
trong `data/processed/` như dấu vết của cơ sở so sánh cũ.

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

1. Chạy pipeline cho phiên bản mới: `python run_pipeline.py --name <tên> --version <phiên bản>`.
2. Khai `parent` trong `configs/datasets/<tên>/<phiên bản>.yaml` = mã phiên bản trước đó.
3. Chép vào đây một mục như trên: mã, cấu hình + `sha256`, `parent`, lý do có phiên bản này, số dòng
   vào/ra, và `eval_lock` nếu tập đánh giá đổi. Lý do là phần quan trọng nhất - cột `parent` trong
   `dataset_registry.csv` chỉ nói "kế thừa từ đâu", không nói "vì sao".
4. Chạy lại `python scripts/collect_reports.py` để cột `parent` trong bảng khớp với file này.
