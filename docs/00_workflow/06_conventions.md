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
- Ngoại lệ đã có trong repo, và chỉ có ngoại lệ này: `model_id` và `method` dùng gạch ngang vì
  chúng là **tên riêng** (`phobert-base-v2`, `qwen3-4b-instruct-2507`, `prompt-cot`,
  `prompt-one-turn`), đi thẳng vào đường dẫn `experiments/<model_id>/<method>/<expNNN>/`, và tên
  file `configs/models/<model_id>.yaml` phải trùng `model_id`. Thư mục trọng số tải về
  (`data/models/Qwen3-4B-Instruct-2507/`) giữ đúng tên trên Hugging Face.

## Config

- Không hardcode đường dẫn: đọc từ `configs/paths.yaml` qua `src/core/paths.py`.
- Không đặt giá trị mặc định trong code. Thiếu khoá thì báo lỗi rõ kèm danh sách file đã đọc.
- Mọi khoá có thể thay đổi theo thí nghiệm phải nằm trong `configs/**`.

## Mở rộng

- Mọi trục mở rộng là một registry: thêm mới thì thêm một module và một dòng đăng ký.
- Mỗi registry có hàm `check()` báo lỗi rõ, và có lệnh `--list-*` để liệt kê.
- Thêm registry mới thì cập nhật `src/core/registry.py`, vì đó là hướng dẫn mở rộng trung tâm.
- Sửa ô notebook (thêm, sửa, xoá) là việc riêng, có luật riêng: `docs/00_workflow/10_template_notebook.md`.

## Sửa một test đang đỏ

Một guard mới làm đỏ test cũ thì chỉ có **ba cách hợp lệ**:

1. Test cũ **không nói về** điều kiện mới: ghi rõ tiền đề của nó (thêm cờ/điều kiện tường minh), **và**
   khẳng định **đúng lý do** chứ không chỉ mã thoát.
2. Guard **quá rộng**: thu hẹp guard (ví dụ điều kiện chỉ áp cho việc GHI, không áp cho `--dry-run`).
3. Guard là thật sự mới: viết test mới cho nó, dựng **môi trường thật** (repo tạm trong `tempfile`),
   không giả lập.

**Cấm**: xoá assertion, hạ độ chặt, `skipTest` để tránh đỏ, hoặc mock môi trường chỉ để test xanh -
mock không chứng minh được gì về môi trường thật và che mất hành vi vừa thêm.

Khẳng định **lý do** là bắt buộc với mọi test "phải từ chối": mã thoát `2` được dùng cho nhiều lý do
khác nhau, nên `assertEqual(code, 2)` một mình vẫn xanh kể cả khi công cụ từ chối **vì chuyện khác**.

## Sửa tệp văn bản có chữ tiếng Việt (Windows)

- Không sửa bằng `Get-Content` rồi `Set-Content` mặc định của PowerShell 5.1: `Get-Content` đọc tệp
  UTF-8 không BOM theo ANSI, nên chữ tiếng Việt hỏng ngay khi ghi lại. Ca thật: `env/.env.colab`
  trong gói bàn giao bị biến `# Biến môi trường` thành `# Biáº¿n mÃ´i trÆ°á»ng`, và người nhận nhìn
  thấy "lỗi font".
- Dùng editor, hoặc `[System.IO.File]::ReadAllText` / `WriteAllText` với `UTF8Encoding` và ghi rõ
  encoding ở cả hai chiều. Code đọc tệp cấu hình bằng `utf-8-sig` để chịu được BOM.
- Tệp `scripts/*.ps1` có chữ tiếng Việt **phải có BOM UTF-8** (`EF BB BF`). `powershell.exe` 5.1 đọc
  tệp `.ps1` không BOM theo ANSI, nên chuỗi tiếng Việt vỡ và **script không parse được**. Ca thật:
  `scripts/setup/setup_qwen_model.ps1` báo `The string is missing the terminator` ở một dòng chỉ có chữ tiếng
  Việt, trong khi `setup_java.ps1` và `setup_vncorenlp.ps1` (có BOM) chạy bình thường - nghĩa là lệnh
  `powershell -File scripts\...` mà README hướng dẫn chỉ chạy được khi tệp có BOM. Kiểm nhanh:
  `[System.IO.File]::ReadAllBytes($p)[0..2] -join ','` → `239,187,191` là có BOM.
- Mọi tool CLI (`run_*.py`, `scripts/*.py`) tự gọi
  `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` trước khi in. Cần vậy vì khi CHUYỂN HƯỚNG
  output ra tệp hoặc pipe trên Windows, Python dùng codepage hệ thống (cp1252 ở máy này) và chữ tiếng Việt
  làm chết chương trình: `UnicodeEncodeError: 'charmap' codec can't encode character '\u0111'`. Ca thật,
  tái hiện được: `python -c "print('đ')" > out.txt`. Script tự viết mà gọi thẳng hàm trong `src/` (ví dụ
  `experiment_run.plan` có `print`) thì tự đặt `PYTHONUTF8=1`, hoặc gọi `reconfigure` y như các tool.

## Dòng lệnh

- Cú pháp của các tool (`run_pipeline.py`, `run_eda.py`, `run_token_stats.py`, `build_report.py`,
  `run_check_examples.py`) nằm ở [09_cli.md](09_cli.md). Đổi cờ thì sửa đồng thời trang đó, docstring
  của tool, và `tests/workflow/test_cli.py`.
- Tool phải chỉ ĐÍCH DANH thứ nó tác động (`--name`, `--version`, `--hash`); mặc định kiểu "bản mới
  nhất" là đoán, nên không được dùng.
- Mã thoát thống nhất: `0` xong · `1` hợp lệ nhưng chưa có kết quả · `2` câu lệnh chưa rõ.
- Chuỗi help không viết cứng đường dẫn: dựng từ `configs/paths.yaml` qua `src/core/paths.py`.

## Tài liệu

- Mỗi file tài liệu mở đầu bằng **đúng hai dòng**, ngay sau dòng tiêu đề `#`:
  `> Đọc file này khi:` rồi `> Liên quan:`. Hai dòng này **liền nhau**, không có dòng `>` trống
  ở giữa, và không thêm dòng `>` nào khác (chú thích dài thì viết thành câu văn bên dưới).
- Mỗi file chỉ nói một chủ đề, không quá dài. Nội dung dài thì tách thành nhiều file nhỏ.
- `docs/README.md` là mục lục duy nhất: nhóm, file, nội dung, đọc khi nào.
- Không ghi số liệu hay đặc trưng của dữ liệu vào tài liệu. Muốn xem thì mở đúng thư mục
  `data/raw/` hoặc `data/processed/`.
- Không ghi lịch sử cũ của dự án vào tài liệu. Người mới chỉ cần biết hiện tại như thế nào.
