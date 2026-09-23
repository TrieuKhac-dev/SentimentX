# Dữ liệu gốc (`data/raw`)

## 1. Vì sao dữ liệu nằm ở `data/raw` mà không phải `datasets`

Trước đây dữ liệu nằm ở thư mục `datasets/`. Cách gọi đó chưa chính xác:

- **"Dataset"** thường dùng cho dữ liệu **đã qua xử lý, đã kiểm duyệt, sẵn sàng dùng**.
- Dữ liệu ban đầu ở đây mới chỉ được **gán nhãn và chia split**, **chưa qua bất kỳ
  bước xử lý nào** (còn review rỗng, còn trùng lặp, còn nhiễu).

Vì vậy dự án tách thành:

| Thư mục | Nội dung |
|---------|----------|
| `data/raw/<tên dataset>/` | Dữ liệu gốc, chỉ đọc — **không bao giờ sửa** |
| `data/processed/versions/<mã>/` | Dữ liệu **đã qua pipeline** — phần này mới đúng nghĩa "dataset" |

Mỗi dataset có **một thư mục riêng** dưới `data/raw/` (`data/raw/cosmetics/`,
`data/raw/newdata/`...). Thư mục `datasets/` cũ đã được **xoá**; nội dung của nó
đã được chuyển vào `data/raw/cosmetics/` nguyên vẹn từng byte.

## 2. Các file dữ liệu

| File | Số dòng | Ghi chú |
|------|---------|---------|
| `data/raw/cosmetics/data_train.csv` | 12.981 | tập huấn luyện |
| `data/raw/cosmetics/data_val.csv` | 1.623 | tập kiểm định trong lúc huấn luyện |
| `data/raw/cosmetics/data_test.csv` | 1.623 | tập đánh giá cuối cùng |
| `data/raw/cosmetics/full_data.csv` | 16.227 | bản gộp của cả 3 tập trên |

Tổng 3 split = 16.227 dòng, đúng bằng `full_data.csv`, nên `full_data.csv` chỉ là
bản nối lại — **pipeline xử lý 3 file split riêng biệt** để không phá vỡ ranh giới
train / val / test.

Danh sách file nào thuộc split nào do `configs/datasets/<tên>.yaml` khai báo (khoá
`splits`), không viết cứng trong code.

## 3. Vấn đề encoding (quan trọng khi đọc file)

Khi kiểm tra byte đầu file:

- `data_train.csv`, `data_val.csv`, `data_test.csv` → có **BOM** (`EF BB BF`)
- `full_data.csv` → **không có BOM**

Nếu không xử lý, tên cột đầu tiên có thể bị đọc thành `\ufeffdata` thay vì `data`.
Dự án luôn đọc bằng `encoding="utf-8-sig"` (`src/utils.py::read_csv`), cách này
đúng cho **cả hai trường hợp**.

## 4. Đặc điểm dữ liệu đã biết

Đây là các đặc điểm cần lưu ý khi thiết kế pipeline (EDA đo lại chính xác bằng số —
xem [02_eda/02_metrics.md](../02_eda/02_metrics.md)):

| Đặc điểm | Ví dụ |
|----------|-------|
| Teencode | `ko`, `cx`, `sp`, `mn`, `r`, `n`, `trc` |
| Viết không dấu | `son dep lam` |
| Ký tự lặp (nhấn mạnh cảm xúc) | `đẹpppppp`, `thíchhhh` |
| Emoji | `😍😍😍`, `❤️` |
| Chuỗi vô nghĩa | `fjfiidkxsksososxkxncnfrooeodk...` |
| Quảng cáo / tin nhắn nhà mạng | `[QC] Giảm 3% khi thanh toán...`, `Viettel tặng 20%...` |
| Nội dung template | `Công dụng: ... Kết cấu: ... Độ bền màu: ...` |

## 5. Lưu ý về dữ liệu gốc

`data/raw/` là **nguồn sự thật duy nhất**. Toàn bộ code chỉ đọc từ đó; mọi thay đổi
đều ghi ra `data/processed/`.

Nội dung dữ liệu gốc còn được đưa vào **mã phiên bản** (`src/versioning.py`), nên
chỉ cần sửa một dòng trong file CSV là kết quả sẽ thuộc một phiên bản mới — không
có chuyện kết quả cũ bị ghi đè mà không biết.

Repo cũng khai báo `.gitattributes` để Git **không tự đổi kiểu xuống dòng** (LF ⇄ CRLF)
cho các file trong `data/`. Nếu không, cùng một file trên hai máy sẽ cho ra hai mã
phiên bản khác nhau dù dữ liệu không hề thay đổi.

---

Xem tiếp: [02_schema.md](02_schema.md) — schema và ý nghĩa nhãn;
[03_new_dataset.md](03_new_dataset.md) — thêm dataset mới.
