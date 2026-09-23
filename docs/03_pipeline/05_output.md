# Định dạng dữ liệu đầu ra

## 1. Vì sao là CSV, không phải Parquet

Đầu ra là **CSV** (`processed_{split}.csv`). Đã cân nhắc dùng Parquet nhưng chọn CSV
vì: dữ liệu chỉ ~16k dòng nên tốc độ đọc/ghi không phải vấn đề; CSV mở được bằng
Excel để kiểm tra bằng mắt; và `git diff` đọc được từng dòng khi dữ liệu gốc thay đổi.

Muốn đổi kết quả sang Parquet: cài `pyarrow`, thêm hàm ghi Parquet trong `src/utils.py`
rồi gọi ở bước Export (`src/pipeline/export.py`) thay cho `write_csv`. Lưu ý mã phiên
bản chỉ tính từ **config + dữ liệu gốc**, không tính mã nguồn — nên đổi định dạng đầu
ra sẽ ghi đè chính thư mục phiên bản đó; muốn giữ lại bản CSV cũ để so sánh thì tăng
`version` trong `configs/datasets/<tên>.yaml` trước khi chạy lại.

## 2. `processed_train.csv` (dạng multi_head)

Cột văn bản + 7 cột khía cạnh, mỗi ô là **mã nhãn**:

| Mã | Nghĩa |
|----|-------|
| `0` | khía cạnh không được nhắc tới |
| `1` | positive |
| `2` | negative |
| `3` | neutral |

Ví dụ:

```csv
text,stayingpower,texture,smell,price,colour,shipping,packing
"Son đẹp nhưng ship lâu",0,0,0,0,1,2,0
```

Số dòng của ba file này cộng lại **đúng bằng** số dòng được giữ sau Clean (không
mất dòng nào, kể cả dòng không có nhãn khía cạnh nào) — đó là hạng mục "số dòng khớp"
ở Step 6 ([02_steps.md §6](02_steps.md)).

## 3. Mẫu ABSA (sinh khi cần)

Mỗi mẫu **chỉ chứa các khía cạnh thực sự được nhắc tới**:

```json
{"split": "train", "text": "Son đẹp nhưng ship lâu", "labels": {"colour": "positive", "shipping": "negative"}}
```

Dạng này không được Export ghi ra đĩa; nó được sinh từ bảng multi_head khi cần
(`src/preprocessing/loader.py::to_absa_records`). Vì sao số mẫu ABSA nhỏ hơn số
dòng: [02_steps.md §5](02_steps.md).

## 4. `label_map.json`

```json
{
  "dataset": "cosmetics",
  "version_id": "cosmetics-v0.1.0-b37ecfce",
  "aspects": ["stayingpower", "..."],
  "labels": ["positive", "negative", "neutral"],
  "label_to_id": {"": 0, "positive": 1, "negative": 2, "neutral": 3},
  "id_to_label": {"0": "", "1": "positive", "2": "negative", "3": "neutral"}
}
```

Model đọc **chính file này** để biết danh sách khía cạnh và mã nhãn của phiên bản dữ
liệu đang dùng (`loader.known_aspects()`), nên đổi dataset không phải sửa code model.
Thêm dataset có nhãn mới (ví dụ `mixed`) thì mã nhãn mới được cấp tự động, các nhãn
quen thuộc giữ nguyên mã — xem [01_dataset/03_new_dataset.md](../01_dataset/03_new_dataset.md).

## 5. Các file truy vết

| File | Nội dung |
|------|----------|
| `data/processed/versions/<mã>/processing_log.json` | config đã dùng + số liệu chính của lần chạy. Nằm **cùng thư mục** với dataset mà nó mô tả |
| `data/processed/manifest.json` | mục lục mọi phiên bản đã chạy (dùng để tìm phiên bản mới nhất) |
| `data/reports/pipeline/versions/<mã>/removed_records.csv` | dòng bị loại, kèm lí do + văn bản |
| `data/reports/pipeline/versions/<mã>/quarantine_records.csv` | dòng bị cách ly vì xung đột nhãn |
| `data/reports/pipeline/versions/<mã>/validation_report.csv` | lỗi phát hiện ở Step 2 (chỉ ghi nhận) |
| `data/reports/pipeline/versions/<mã>/final_validation.json` | kết quả cổng chất lượng ở Step 6 |

Danh sách đầy đủ file số liệu của một lần chạy nằm ngay trong thư mục phiên bản —
báo cáo chỉ ghi **một dòng** "Thư mục số liệu chi tiết" ở đầu, không liệt kê từng file
([02_eda/04_report_rules.md §2](../02_eda/04_report_rules.md)).

---

Xem tiếp: [06_extend.md](06_extend.md) — thêm một bước pipeline mới.
