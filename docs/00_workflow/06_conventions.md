# 06. Quy ước code, config, tài liệu

> Đọc file này khi: viết code, viết config hoặc viết tài liệu mới.
> Liên quan: `docs/00_workflow/05_git_commits.md`, `docs/05_config/01_paths.md`

## Chú thích

- Ngắn gọn, rõ ràng. Mỗi khối tối đa hai câu.
- Nêu **lý do** khi có lỗi ngầm, không kể lại việc code đang làm gì.
- Giữ các cảnh báo chống lỗi im lặng, ví dụ quy ước đếm dương tính giả trong metric.
- Trong file YAML, chỉ thêm chú thích khi giá trị hợp lệ thật sự cần giải thích.
  Đừng chú thích tràn lan mọi khoá.

## Trình bày

- Không tự vẽ dải gạch dài để phân mục trong code, config hay tài liệu. Tối đa dùng `---`.
- Dải gạch do IDE tự format, ví dụ khi kẻ bảng trong markdown, thì không tính là vi phạm.
- Không vẽ khung hoặc hình bằng ký tự.
- Chỉ dùng ký tự gõ được trên bàn phím.

## Tên file và tên khoá

- Tên file, tên thư mục, tên khoá: chữ thường, dùng **gạch dưới** `_`.
  Ví dụ: `01_raw_data.md`, `run_pipeline.py`, `model_input.csv`, `label_space`.
- Không dùng gạch ngang `-` trong tên file, trừ khi công cụ bắt buộc.

## Config

- Không hardcode đường dẫn: đọc từ `configs/paths.yaml` qua `src/paths.py`.
- Không đặt giá trị mặc định trong code. Thiếu khoá thì báo lỗi rõ kèm danh sách file đã đọc.
- Mọi khoá có thể thay đổi theo thí nghiệm phải nằm trong `configs/**`.

## Mở rộng

- Mọi trục mở rộng là một registry: thêm mới thì thêm một module và một dòng đăng ký.
- Mỗi registry có hàm `check()` báo lỗi rõ, và có lệnh `--list-*` để liệt kê.
- Thêm registry mới thì cập nhật `src/registry.py`, vì đó là hướng dẫn mở rộng trung tâm.

## Tài liệu

- Mỗi file tài liệu mở đầu bằng **đúng hai dòng**, ngay sau dòng tiêu đề `#`:
  `> Đọc file này khi:` rồi `> Liên quan:`. Hai dòng này **liền nhau**, không có dòng `>` trống
  ở giữa, và không thêm dòng `>` nào khác (chú thích dài thì viết thành câu văn bên dưới).
- Mỗi file chỉ nói một chủ đề, không quá dài. Nội dung dài thì tách thành nhiều file nhỏ.
- `docs/README.md` là mục lục duy nhất: nhóm, file, nội dung, đọc khi nào.
- Không ghi số liệu hay đặc trưng của dữ liệu vào tài liệu. Muốn xem thì mở đúng thư mục
  `data/raw/` hoặc `data/processed/`.
- Không ghi lịch sử cũ của dự án vào tài liệu. Người mới chỉ cần biết hiện tại như thế nào.
