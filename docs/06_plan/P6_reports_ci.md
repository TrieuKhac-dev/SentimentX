# P6 - Reports, CI, docs

> Đọc file này khi: sinh bảng tổng hợp, hoặc khi CI báo đỏ.
> Liên quan: `docs/00_workflow/03_ci.md`, `docs/05_config/*`

## 1. Mục tiêu giai đoạn

Có bảng tổng hợp sinh tự động, có CI chặn lỗi cấu trúc trên nhánh `experiment`,
và tài liệu đầy đủ cho cả nhóm.

## 2. Trạng thái

xong T1..T7. Giai đoạn này đóng lại ở đây; việc còn lại của dự án nằm ở P7.

## 3. Task nhỏ (mỗi task một commit)

- [x] T1. `scripts/collect_reports.py`: quét `run_meta.json` và các `metrics.csv` để sinh bốn nhóm report
      (`dataset_registry`, `experiment_registry`, `model_input`, `metrics_matrix`), mỗi nhóm có
      `csv` nguồn, `html` trình bày, `md` chỉ chứa sơ đồ Mermaid; nhận nhiều gốc bằng `--root`.
      -> `feat(reports): generate registry model input and metrics matrix reports`
      Thư viện là `src/reports.py`, script chỉ là cửa vào mỏng (chọn gốc, chọn nhóm, in kết quả).
      Không chạy model và không đọc dữ liệu gốc: mọi con số đọc lại từ file mà chính lượt chạy đã
      ghi, nên không có đường tính thứ hai.
      Chạy thật (24/09/2026): quét 2 gốc được 2 lượt chạy; `dataset_registry` 1 dòng,
      `experiment_registry` 2 dòng, `model_input` 0 dòng (chưa đo, và báo cáo nói rõ là rỗng),
      `metrics_matrix` 22 dòng (8 khía cạnh × độ chính xác, 14 dòng khía cạnh × sắc thái).
      Cột đối chiếu lấy từ `data/reference_publication/` với `--reference-shot 0|1|5`
      (`COT+0-shot`); P/R/F1 của công bố (phần trăm) được đưa về cùng thang 0..1 với `metrics.csv`
      của dự án, còn độ chính xác thì cả hai bên đều theo phần trăm. Hai lỗi thật đã bắt được khi
      chạy: script quên truyền bảng công bố vào `build()` (mất cột đối chiếu), và phép đổi thang
      đo không chạy vì giá trị đọc từ CSV là chuỗi.
- [x] T2. `scripts/ci_checks.py`: sáu kiểm tra (không có dữ liệu bị git theo dõi, `.gitignore` đúng,
      notebook sạch output, mọi registry hợp lệ, mọi config thí nghiệm hợp lệ, `REPO_SHA` hợp lệ và tồn tại).
      -> `feat(ci): add repository checks script`
      Thư viện là `src/checks.py`, script chỉ là cửa vào mỏng (mã thoát 0/1 để CI đọc được). Không
      chạy model, không đọc `data/`, không gọi mạng - đúng như mục "CI không làm gì" của 03_ci.md.
      Chạy thật: 6/6 sạch trên cây hiện tại. Lần chạy đầu bắt được hai việc thật: `data/models/README.md`
      bị coi là dữ liệu (README trong `data/` là metadata, đã thêm vào danh sách cho phép và vào bảng
      của 03_ci.md), và phần kiểm `tracking` đòi `DAGSHUB_TOKEN` trong khi CI không giữ secret (nay
      kiểm từng cách ghi nhận bằng config tối thiểu, chỉ kiểm `mlflow` khi CÓ token).
      Chặn cả hai chiều: cây sạch thì im lặng, cây cố tình vi phạm thì báo đúng chỗ - và có một test
      khẳng định chính repo này đang sạch.
      Khi rà lại thì thấy thêm một lỗi im lặng trong chính công cụ kiểm: các lệnh git ở kiểm tra
      `REPO_SHA` không truyền gốc repo, mà `repo.run_git` mặc định chạy ở thư mục đang đứng - nên
      chạy `ci_checks.py` từ thư mục khác là kiểm NHẦM repo mà vẫn báo "sạch". Đã sửa (truyền `root`
      cho `object_exists`/`ref_exists`/`is_ancestor`) kèm test; phần sửa này nằm trong commit
      `fix(evaluation): sampling falls back to the model card, not to 1.0` vì cùng một lần commit.
- [x] T3. `.github/workflows/ci.yml` chạy khi push và pull request vào nhánh `experiment`.
      -> `ci: add github actions workflow for experiment branch`
      Ba việc, ba commit: `test(ci): skip dataset tests where there is no data` (bốn test của preflight
      cần dataset đã xử lý, mà bản clone sạch không có dữ liệu - nay chúng tự bỏ qua ở CI, vẫn chạy đủ
      ở máy cá nhân); `feat(ci): check documentation links` (kiểm tra 7: link trong `README.md` và
      `docs/**/*.md` phải trỏ tới file có thật - chính lỗi vừa gặp ở bước đồng bộ kế hoạch); và commit
      này (workflow: `fetch-depth: 0`, `requirements-ci.txt`, hai lệnh).
      Cách biết trước CI có xanh không, không cần chờ GitHub: chạy lại bộ test với hai gốc đường dẫn
      trỏ vào thư mục rỗng (giả lập máy sạch).
- [x] T4. `requirements-ci.txt`, `requirements-colab.txt` (không cài lại torch).
      -> `chore(deps): add ci colab and base requirements`
      Danh sách KHÔNG đoán: quét `ast` các import ở CẤP MODULE của `src/` và `tests/` thì chỉ có
      `pandas`, `numpy`, `PyYAML` (thêm `jinja2`, `plotly` riêng cho `src/reporting/`), còn `torch`,
      `transformers`, `bitsandbytes`, `mlflow`, `pyvi`, `vncorenlp` đều được import BÊN TRONG hàm -
      nên CI cài một file rất ngắn, và cũng không được cài nặng hơn thế. File Colab KHÔNG ghim
      `torch` vì Colab đã có bản khớp CUDA.
      Kèm theo: `docs/00_workflow/07_colab.md` - runbook chạy trên Colab, viết ra từ hai lần chạy
      thật (mục 2 Drive cần gì, mục 4 ba bước của người chạy, mục 7 bảng tra lỗi).
      Bản đầu của runbook liệt kê một chuỗi thao tác tay (mount, khai tên thư mục, tạo `.env.colab`,
      nén rồi giải nén dữ liệu, cài gói) - tức là tôi viết lại việc đáng lẽ notebook phải tự làm.
      Người dùng phản hồi đúng: thiết kế là "copy thư mục vào Drive rồi bấm Run all". Nên đã sửa tận
      gốc: `runtime.drive_dir()` tìm thư mục nhóm BẰNG FILE ĐÁNH DẤU chứ không cần biết tên (quét một
      cấp trong `MyDrive`/`Shareddrives`, ưu tiên thư mục có `data/`), và ô bootstrap tự mount Drive,
      tự đặt hai gốc, tự cài gói còn thiếu. Runbook còn ba bước: copy thư mục + notebook, mở notebook,
      bấm Run all (và bấm Allow khi Colab hỏi quyền Drive - việc duy nhất Google không cho tự động).
- [x] T5. Docs nhóm quy trình: `01_flow`, `02_rules`, `03_ci`, `04_terms`, `05_git_commits`, `06_conventions`.
      -> `docs(workflow): add workflow rules ci terms commits and conventions`
      Soát lại (25/09/2026) bằng máy trước, đọc sau: mọi link trong `README.md` và `docs/**/*.md` tồn
      tại (kiểm tra 7 của CI nay khoá điều này), mọi lệnh `python <script> ...` trỏ tới script có thật
      với tham số có thật, mọi đường dẫn tương đối trong `src/` tồn tại. Nội dung khớp code hiện tại:
      luật 20 khớp `.gitignore`, luật 11 khớp `eval_lock`, luật 16 khớp runbook. Ba việc phát hiện và
      đã sửa: `01_flow` bước 6-7 còn tả cơ chế cũ (giảng viên tự mount Drive), README gốc còn cây thư
      mục trước P1-P3 kèm một link chết, và `--title` được tài liệu hướng dẫn nhưng script chưa có.
- [x] T6. Docs tham chiếu cấu hình: `05_config/01..07`.
      -> `docs(config): add configuration reference`
      Soát cùng lượt: 7 file đều tồn tại và có nội dung thật (33-86 dòng). Đối chiếu code:
      `CARD_SETTINGS` đúng ở `src/experiment_run.py`, năm scorer đúng tên module trong
      `src/evaluation/scorers/`, `TRACKERS` đúng ba trình ghi nhận, thứ tự hợp nhất bảy lớp đúng.
      Sửa một lỗi thật: `06_experiment.md` ghi `prompt` "tính từ gốc repo", trong khi
      `experiments.requires` tính từ THƯ MỤC THÍ NGHIỆM trước rồi tới gốc repo - đúng loại lỗi làm
      config đúng mà vẫn thiếu file.
- [x] T7. Docs đánh giá: `04_experiments/metrics.md`, `04_experiments/reference_publication.md`;
      cập nhật `docs/README.md` làm mục lục duy nhất.
      -> `docs(experiments): add metrics and reference publication pages`
      Soát cùng lượt: hai file khớp code (năm cách chấm đúng tên module, `metrics.csv` đúng bảng dài
      `aspect,sentiment,metric,value`, `metrics_matrix` đúng hai bảng có cột `reference`).
      `docs/README.md` nay liệt kê đủ bảy nhóm tài liệu - trước đó bảng thiếu hẳn `00_workflow`,
      `05_config`, `06_plan`, và thiếu trang `07_colab.md`.

## 4. Điều kiện hoàn thành (DoD)

- Bốn nhóm report sinh được từ dữ liệu thật, không ghi đè lẫn nhau.
- CI xanh trên nhánh `experiment`; cố tình vi phạm một kiểm tra thì CI đỏ đúng chỗ.
- `docs/README.md` liệt kê đủ mọi nhóm tài liệu, mỗi dòng ghi rõ đọc khi nào.

## 5. Rủi ro / lưu ý

- Report sinh ở nơi có kết quả: chạy trên Colab thì sinh vào Drive, nên report trong repo chỉ có
  kết quả đã copy về.
- Không để CI chạy model hoặc đọc dữ liệu: dữ liệu không nằm trong repo.

## 6. Phụ thuộc

P5 xong (đã có notebook và template).
