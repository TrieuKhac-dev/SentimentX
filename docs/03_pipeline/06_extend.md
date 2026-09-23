# Thêm một bước Pipeline mới

1. Tạo file mới trong `src/pipeline/`, ví dụ `dedup_cross_split.py`.

2. Viết hàm `run(context)`, trong đó:
   - đọc dữ liệu từ `context["splits"]` (dict các DataFrame);
   - ghi kết quả trở lại `context["splits"]` nếu có biến đổi;
   - ghi file số liệu chi tiết vào `context["out_dir"]`;
   - trả về một **dict mô tả báo cáo** (giống module EDA: `id`, `title`, `cards`,
     `charts`, `tables`, `files`).

   Muốn ghi kết quả ra thư mục dữ liệu đã xử lý thì dùng `context["processed_dir"]`
   (đã trỏ sẵn vào `data/processed/versions/<mã phiên bản>`).

3. Mở `src/registry.py`, thêm vào `pipeline_steps()` **đúng vị trí** mong muốn.

Không cần sửa `run_pipeline.py` hay `build_report.py`.

## Lưu ý khi thêm bước

- **Vị trí quyết định ý nghĩa.** Ví dụ một bước "so trùng toàn cục" đặt trước hay sau
  bước Clean sẽ cho kết quả khác nhau; đặt sai vị trí là lỗi im lặng, vì pipeline
  không kiểm tra thứ tự giúp bạn.
- **Bước mới sửa văn bản thì phải khai với Final Validate.** Nếu bước của bạn thay
  đổi cột `text` ngoài bốn phép đã biết, hạng mục "Văn bản chỉ đổi hình thức" sẽ báo
  LỖI — đó là hành vi mong muốn, không phải lỗi cần tắt
  ([04_invariants.md §2](04_invariants.md)).
- **Số liệu phải cộng lại được.** Nếu bước mới loại bớt dòng, hãy ghi số dòng bị loại
  thành một mục riêng trong `removed_records.csv`-style, để bảng "sau Clean (giữ lại)
  / bị loại / cách ly" vẫn đối chiếu được với số dòng trước đó
  ([01_flow.md §4](01_flow.md)).
- **Thêm công tắc cho bước mới** ngay trong `configs/pipeline.yaml` (theo quy ước
  `true` = BẬT) rồi khai giá trị dự phòng an toàn trong
  `src/utils.py::load_pipeline_config`; nếu không, bước mới sẽ bật vô điều kiện và
  việc thực nghiệm (đổi một công tắc một lần) không làm được nữa
  ([03_config.md §6](03_config.md)).

---

Xem thêm: [02_steps.md](02_steps.md) — bảy bước hiện có;
[03_config.md](03_config.md) — cấu hình và cách thực nghiệm.
