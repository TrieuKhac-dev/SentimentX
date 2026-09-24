# Dữ liệu gốc

> Đọc file này khi: làm việc với dữ liệu gốc.
>
> Liên quan: `docs/01_dataset/02_schema.md`, `docs/05_config/03_datasets.md`

## 1. Nơi lưu và cách đánh phiên bản

```
data/raw/<name>/<raw_version>/
```

| Thành phần      | Nghĩa                        | Ví dụ       |
| --------------- | ---------------------------- | ----------- |
| `<name>`        | tên dataset                  | `cosmetics` |
| `<raw_version>` | phiên bản của bộ dữ liệu gốc | `v0.1.0`    |

Ví dụ: `data/raw/cosmetics/v0.1.0/data_train.csv`.

Luật: **tăng `<raw_version>` mỗi khi dữ liệu gốc thay đổi**, và **giữ nguyên bản cũ**.
Nhờ vậy vẫn tạo lại được một phiên bản dataset cũ từ đúng bộ dữ liệu gốc của nó.

## 2. Hai thư mục khác nhau, không được lẫn

| Thư mục                          | Nội dung                                |
| -------------------------------- | --------------------------------------- |
| `data/raw/<name>/<raw_version>/` | Dữ liệu gốc, chỉ đọc, không bao giờ sửa |
| `data/processed/<mã>/`           | Dữ liệu đã qua xử lý, tức dataset       |

## 3. Thông tin của một phiên bản dữ liệu gốc

Mỗi phiên bản có file `raw_meta.yaml` nằm ngay trong thư mục của nó, ghi: nguồn thu thập,
giấy phép, ngày thu thập, và với từng file: số byte, số dòng, `sha256`.

File này **được commit**, vì dữ liệu gốc thì không.

Muốn xem số liệu hay đặc trưng của dữ liệu thì mở đúng thư mục dữ liệu:
`data/raw/<name>/<raw_version>/` hoặc `data/processed/<mã>/`. Tài liệu này không chép lại số liệu.

## 4. Đọc file gốc cho đúng

Một số file CSV có BOM ở đầu file, một số không. Nếu đọc sai thì tên cột đầu tiên thành `\ufeffdata`.
Dự án luôn đọc bằng `encoding="utf-8-sig"`, cách này đúng cho cả hai trường hợp.

## 5. Git không đổi kiểu xuống dòng

`.gitattributes` khai `data/** -text` để Git không tự đổi LF thành CRLF. Nếu không,
cùng một file trên hai máy sẽ cho ra hai mã phiên bản khác nhau dù dữ liệu không đổi.

---

Xem tiếp: [02_schema.md](02_schema.md) - schema và ý nghĩa nhãn;
[03_new_dataset.md](03_new_dataset.md) - thêm dataset mới.
