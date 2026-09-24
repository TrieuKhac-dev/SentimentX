# P6 - Reports, CI, docs

> Đọc file này khi: sinh bảng tổng hợp, hoặc khi CI báo đỏ.
> Liên quan: `docs/00_workflow/03_ci.md`, `docs/05_config/*`

## 1. Mục tiêu giai đoạn

Có bảng tổng hợp sinh tự động, có CI chặn lỗi cấu trúc trên nhánh `experiment`,
và tài liệu đầy đủ cho cả nhóm.

## 2. Trạng thái

xong T1, T2. Còn T3..T7.

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
- [ ] T3. `.github/workflows/ci.yml` chạy khi push và pull request vào nhánh `experiment`.
      -> `ci: add github actions workflow for experiment branch`
- [ ] T4. `requirements-ci.txt`, `requirements-colab.txt` (không cài lại torch).
      -> `chore(deps): add ci colab and base requirements`
- [ ] T5. Docs nhóm quy trình: `01_flow`, `02_rules`, `03_ci`, `04_terms`, `05_git_commits`, `06_conventions`.
      -> `docs(workflow): add workflow rules ci terms commits and conventions`
- [ ] T6. Docs tham chiếu cấu hình: `05_config/01..07`.
      -> `docs(config): add configuration reference`
- [ ] T7. Docs đánh giá: `04_experiments/metrics.md`, `04_experiments/reference_publication.md`;
      cập nhật `docs/README.md` làm mục lục duy nhất.
      -> `docs(experiments): add metrics and reference publication pages`

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
