# 06. Quy ước code, cấu hình, tài liệu

> Đọc file này khi: viết code, viết cấu hình hoặc viết tài liệu mới.
> Liên quan: `docs/00_workflow/05_git_commits.md` · `docs/05_config/*`

## Chú thích

- Ngắn gọn, rõ ràng. Mỗi khối tối đa hai câu.
- Nêu **vì sao** khi có bẫy, không kể lại việc code đang làm gì.
- Giữ các cảnh báo chống lỗi im lặng, ví dụ quy ước đếm dương tính giả trong chỉ số.
- Trong tệp YAML, mỗi khoá có một dòng chú thích: giá trị hợp lệ và mặc định.

## Trình bày

- Không dùng dải gạch dài để phân mục trong code, cấu hình hay tài liệu. Tối đa dùng `---`.
- Không vẽ khung hoặc hình bằng ký tự.
- Tên tệp, tên thư mục, tên khoá: chữ thường, dùng gạch dưới cho khoá cấu hình,
  dùng gạch ngang cho tên tệp tài liệu.

## Cấu hình

- Không hardcode đường dẫn: đọc từ `configs/paths.yaml` qua `src/paths.py`.
- Không đặt giá trị mặc định trong code. Thiếu khoá thì báo lỗi rõ kèm danh sách tệp đã đọc.
- Mọi khoá có thể thay đổi theo thí nghiệm phải nằm trong `configs/**`.

## Mở rộng

- Mọi trục mở rộng là một registry: thêm mới thì thêm một module và một dòng đăng ký.
- Mỗi registry có hàm `check()` báo lỗi rõ, và có lệnh `--list-*` để liệt kê.
- Thêm registry mới thì cập nhật `src/registry.py`, vì đó là hướng dẫn mở rộng trung tâm.

## Tài liệu

- Mỗi tệp tài liệu mở đầu bằng hai dòng: `> Đọc file này khi:` và `> Liên quan:`.
- Mỗi tệp chỉ nói một chủ đề, không quá dài. Nội dung dài thì tách thành nhiều tệp nhỏ.
- `docs/README.md` là mục lục duy nhất: nhóm, tệp, nội dung, đọc khi nào.
