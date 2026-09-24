# Thêm một dataset mới

> Đọc file này khi: thêm một dataset mới.
> Liên quan: `docs/01_dataset/02_schema.md`, `docs/05_config/03_datasets.md`

Xem hướng dẫn đầy đủ ở [README, mục 7](../README.md). Tóm tắt:

1. Đặt dữ liệu gốc vào `data/raw/<tên>/` (mỗi dataset một thư mục riêng).
2. Copy `configs/datasets/cosmetics/v0.1.0.yaml` thành `configs/datasets/<name>/<version>.yaml`
   rồi sửa: `name`, `format`, `raw_dir`, `text_column`, `aspects`, `labels`, `splits`.
3. Chạy `python run_eda.py --dataset <tên> --raw-version <phiên bản raw>` (và `run_pipeline.py`, `build_report.py`
   tương tự).

**Tên dataset phải trùng tên file YAML.** Nếu gõ sai tên, công cụ dừng ngay với
thông báo "không tìm thấy dataset" kèm gợi ý tên gần đúng (mã thoát `2`), chứ không
chạy tiếp rồi báo "chưa có file kết quả".

Không cần sửa `run_eda.py`, `run_pipeline.py` hay bất kỳ module EDA/pipeline nào.
Ba trường hợp cần thêm việc:

| Trường hợp                      | Cần làm gì                                                         |
| ------------------------------- | ------------------------------------------------------------------ |
| Định dạng file mới (vd `.xlsx`) | viết hàm `read(path)` trong `src/loaders/` rồi đăng ký ở `LOADERS` |
| Tên cột văn bản khác            | sửa khoá `text_column` trong YAML                                  |
| Bộ nhãn khác (vd thêm `mixed`)  | khai báo thêm trong `labels`; mã nhãn mới được cấp tự động         |

Sau khi thêm dataset, chạy đủ ba nhóm việc theo đúng thứ tự: EDA (khảo sát) -> pipeline
(xử lý) -> thực nghiệm. Cách chạy từng pha: [02_eda/01_flow.md](../02_eda/01_flow.md) mục 4
và [03_pipeline/01_flow.md](../03_pipeline/01_flow.md) mục 5.
