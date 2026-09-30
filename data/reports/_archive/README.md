# Kho lịch sử bảng số đo

Thư mục này để **chuyển ra** những bảng `token_stats*.csv` KHÔNG còn tái lập được:

```
data/reports/_archive/<mã phiên bản>/<tên bảng>.csv
```

## Vì sao phải có thư mục này

Tên bảng số đo mang băm NỘI DUNG của bộ ví dụ (`token_stats__prompt-<tên>__ex-<sha8>__...`). Sửa nội
dung file ví dụ **tại chỗ** là bảng của bộ cũ thành **mồ côi**: không lệnh nào sinh lại được nó nữa,
mà `scripts/collect_reports.py` quét MỌI `token_stats*.csv` trong `model_input/` (kể cả thư mục con)
rồi tính nó vào `model_input.csv` như một phép đo hợp lệ.

Vì vậy chỗ để bảng cũ phải nằm **NGOÀI** `model_input/` - đó là lý do thư mục này là **anh em** của
`model_input/`, không phải con của nó.

## Dùng thế nào

- `run_token_stats.py` **cảnh báo** (không tự xoá, không tự dời) khi trong thư mục phiên bản có bảng
  lệch với cặp prompt + ví dụ hiện tại; kiểm 8 của CI báo đỏ (`docs/00_workflow/03_ci.md`).
- Cách sửa, chọn một: chuyển bảng đó vào đây; hoặc khôi phục nội dung file ví dụ cũ; hoặc tạo **cặp
  mới** (`configs/prompts/<tên>_v2.txt` + `examples/<tên>_v2.txt`) rồi trỏ config sang tên mới - luật
  21 ở `docs/00_workflow/02_rules.md` và mục 2.2 của `docs/04_experiments/02_model_input.md`.
- Nội dung thư mục này **không vào git** (`.gitignore`); chỉ file README này được theo dõi.
