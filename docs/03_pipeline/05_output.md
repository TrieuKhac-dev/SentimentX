# Định dạng dữ liệu đầu ra

> Đọc file này khi: đọc file mà pipeline ghi ra.
> Liên quan: `docs/03_pipeline/02_steps.md`, `docs/04_experiments/02_model_input.md`

## 1. Vì sao là CSV, không phải Parquet

Đầu ra là **CSV** (`{split}.csv`). Đã cân nhắc dùng Parquet nhưng chọn CSV
vì: dữ liệu chỉ ~16k dòng nên tốc độ đọc/ghi không phải vấn đề; CSV mở được bằng
Excel để kiểm tra bằng mắt; và `git diff` đọc được từng dòng khi dữ liệu gốc thay đổi.

Muốn đổi kết quả sang Parquet: cài `pyarrow`, thêm hàm ghi Parquet trong `src/core/utils.py`
rồi gọi ở bước Export (`src/pipeline/export.py`) thay cho `write_csv`. Lưu ý mã phiên
bản chỉ tính từ **config + dữ liệu gốc**, không tính mã nguồn - nên đổi định dạng đầu
ra sẽ ghi đè chính thư mục phiên bản đó; muốn giữ lại bản CSV cũ để so sánh thì tăng
`version` trong `configs/datasets/<name>/<version>.yaml` trước khi chạy lại.

## 2. `train.csv` (dạng multi_head)

Cột văn bản + 7 cột khía cạnh, mỗi ô là **mã nhãn**:

| Mã  | Nghĩa                         |
| --- | ----------------------------- |
| `0` | khía cạnh không được nhắc tới |
| `1` | positive                      |
| `2` | negative                      |
| `3` | neutral                       |

Ví dụ:

```csv
text,stayingpower,texture,smell,price,colour,shipping,packing
"Son đẹp nhưng ship lâu",0,0,0,0,1,2,0
```

Số dòng của ba file này cộng lại **đúng bằng** số dòng được giữ sau Clean (không
mất dòng nào, kể cả dòng không có nhãn khía cạnh nào) - đó là hạng mục "số dòng khớp"
ở Step 6 ([02_steps.md mục 6](02_steps.md)).

**Ô nhiều dòng được giữ NGUYÊN** - khác với bảng dự đoán: review có thể chứa ký tự xuống dòng, và
`src/pipeline/export.py` gọi `utils.write_csv(..., single_line=False)` để ghi đúng như vậy. Hai lý do,
đổi là hỏng:

1. `eval_lock` băm BYTE của `{split}.csv` (xem mục 5), nên đổi cách ghi là đổi khoá tập đánh giá của
   mọi kết quả đã công bố;
2. đổi xuống dòng thành hai ký tự `\n` là phép biến đổi **mất mát**: đọc lại file ra văn bản khác với
   văn bản đưa cho model (test của phiên bản hiện tại: 334/1.518 bản ghi có ô nhiều dòng).

Hệ quả: ba file này có **nhiều dòng vật lý hơn số bản ghi**, nên mọi chỗ đếm phải đếm BẢN GHI
(`preflight.count_rows`, `reports._row_count`). Luật "một bản ghi = một dòng vật lý" áp cho **bảng cho
người đọc** - xem [04_experiments/05_predictions.md](../04_experiments/05_predictions.md).

## 3. Mẫu ABSA (sinh khi cần)

Mỗi mẫu **chỉ chứa các khía cạnh thực sự được nhắc tới**:

```json
{
  "split": "train",
  "text": "Son đẹp nhưng ship lâu",
  "labels": { "colour": "positive", "shipping": "negative" }
}
```

Dạng này không được Export ghi ra đĩa; nó được sinh từ bảng multi_head khi cần
(`src/preprocessing/loader.py::to_absa_records`). Vì sao số mẫu ABSA nhỏ hơn số
dòng: [02_steps.md mục 5](02_steps.md).

## 4. `label_map.json`

```json
{
  "dataset": "cosmetics",
  "version_id": "cosmetics-ds0.1.0-pl0.1.0-srccosmetics@0.1.0-ab12cd34",
  "aspects": ["stayingpower", "..."],
  "labels": ["positive", "negative", "neutral"],
  "label_to_id": { "": 0, "positive": 1, "negative": 2, "neutral": 3 },
  "id_to_label": { "0": "", "1": "positive", "2": "negative", "3": "neutral" }
}
```

Model đọc **chính file này** để biết danh sách khía cạnh và mã nhãn của phiên bản dữ
liệu đang dùng (`loader.known_aspects()`), nên đổi dataset không phải sửa code model.
Thêm dataset có nhãn mới (ví dụ `mixed`) thì mã nhãn mới được cấp tự động, các nhãn
quen thuộc giữ nguyên mã - xem [01_dataset/03_new_dataset.md](../01_dataset/03_new_dataset.md).

## 5. `eval_lock.json` - khoá tập đánh giá

```json
{
  "test": {
    "schema": 1,
    "file": "test.csv",
    "sha256": "e2558137...",
    "records_sha256": "fa91b1d9...",
    "rows": 1518
  }
}
```

Hai dấu vân tay, hai vai trò:

| Trường            | Băm cái gì                                                                   | Lệch thì sao                                                    |
| ----------------- | ---------------------------------------------------------------------------- | --------------------------------------------------------------- |
| `records_sha256`  | TẬP BẢN GHI: thứ tự trong file; văn bản đã chuẩn hoá; mã nhãn theo thứ tự aspect (`versioning.records_sha256`) | **LỖI** - nội dung đánh giá đã đổi, hết quyền so với công bố     |
| `sha256`          | BYTE của file (`versioning.file_sha256`)                                      | **GHI CHÚ** - dữ liệu y nguyên, chỉ cách ghi file đổi            |
| `rows`            | số bản ghi                                                                    | ghi chú (số đối chiếu nhanh)                                     |
| `schema`          | công thức tính `records_sha256` (`versioning.RECORDS_LOCK_SCHEMA`)            | đổi công thức là bump số, không im lặng                          |

Vì sao có HAI dấu vân tay thay vì chỉ byte: 25/09/2026 một lần đổi cách ghi CSV làm `test.csv` khác
`sha256` (`e2558137…` -> `9ac701de…`) dù **1.518 bản ghi y nguyên** - khoá theo byte chặn nhầm một tập
đánh giá không hề đổi. Ngược lại, chỉ có vân tay dữ liệu thì mất khả năng truy vết "file nào đã sinh ra
con số đã công bố". Giữ cả hai: dữ liệu là **khoá**, byte là **dấu vết**.

Ghi MỘT LẦN trong cùng lần chạy đã tạo ra `test.csv`, và nằm ngay cạnh dữ liệu
(`data/processed/<mã>/`). Đây là thứ khiến tập đánh giá đóng băng được **từ bản dữ liệu đầu
tiên**: mọi lượt chạy sau - trên máy nào cũng vậy - đọc file này (`versioning.split_lock()`) và
so với `test.csv` đang có; lệch **tập bản ghi** là LỖI, không phải cảnh báo.

Hai trường hợp đặc biệt:

- Khoá cũ chưa có `records_sha256` (ghi trước 28/09/2026, ví dụ `…-e0ccc484`): lần chạy đầu tiên so
  `sha256` như trước, khớp thì **BỔ SUNG** trường mới - không đổi giá trị nào đã ghi.
- Vân tay dữ liệu khớp mà byte lệch: khoá được cập nhật lại `sha256`, người chạy thấy một dòng ghi chú
  `định dạng ghi ... đã đổi, dữ liệu KHÔNG đổi`.

Vì sao khoá không nằm trong file phiên bản dataset: giá trị chỉ biết được SAU khi
pipeline chạy lần đầu, mà file phiên bản thì bất biến. File phiên bản khai **chính sách**
(`eval_lock.enforce`, tên file) và, khi cần đối chiếu với một tập test bên ngoài, giá trị
**mong đợi** (`sha256` và/hoặc `records_sha256`). Chi tiết: [05_config/03_datasets.md](../05_config/03_datasets.md).

## 6. Các file truy vết

| File                                                  | Nội dung                                                                                  |
| ----------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `data/processed/<mã>/processing_log.json`             | config đã dùng + số liệu chính của lần chạy. Nằm **cùng thư mục** với dataset mà nó mô tả |
| `data/processed/<mã>/eval_lock.json`                  | khoá tập đánh giá (`sha256` + số dòng từng split đã khoá), ghi một lần lúc tạo dữ liệu     |
| `data/processed/<mã>/pipeline/removed_records.csv`    | dòng bị loại, kèm lí do + văn bản                                                         |
| `data/processed/<mã>/pipeline/quarantine_records.csv` | dòng bị cách ly vì xung đột nhãn                                                          |
| `data/processed/<mã>/pipeline/validation_report.csv`  | lỗi phát hiện ở Step 2 (chỉ ghi nhận)                                                     |
| `data/processed/<mã>/pipeline/final_validation.json`  | kết quả cổng chất lượng ở Step 6                                                          |

Danh sách đầy đủ file số liệu của một lần chạy nằm ngay trong thư mục phiên bản -
báo cáo chỉ ghi **một dòng** "Thư mục số liệu chi tiết" ở đầu, không liệt kê từng file
([02_eda/04_report_rules.md mục 2](../02_eda/04_report_rules.md)).

---

Xem tiếp: [06_extend.md](06_extend.md) - thêm một bước pipeline mới.
