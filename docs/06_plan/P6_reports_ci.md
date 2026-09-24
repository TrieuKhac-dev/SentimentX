# P6 - Reports, CI, docs

> Đọc file này khi: sinh bảng tổng hợp, hoặc khi CI báo đỏ.
> Liên quan: `docs/00_workflow/03_ci.md`, `docs/05_config/*`

## 1. Mục tiêu giai đoạn

Có bảng tổng hợp sinh tự động, có CI chặn lỗi cấu trúc trên nhánh `experiment`,
và tài liệu đầy đủ cho cả nhóm.

## 2. Trạng thái

chưa làm

## 3. Task nhỏ (mỗi task một commit)

- [ ] T1. `scripts/collect_reports.py`: quét `run_meta.json` và các `metrics.csv` để sinh bốn nhóm report
      (`dataset_registry`, `experiment_registry`, `model_input`, `metrics_matrix`), mỗi nhóm có
      `csv` nguồn, `html` trình bày, `md` chỉ chứa sơ đồ Mermaid; nhận nhiều gốc bằng `--root`.
      -> `feat(scripts): generate registry model input and metrics matrix reports`
- [ ] T2. `scripts/ci_checks.py`: sáu kiểm tra (không có dữ liệu bị git theo dõi, `.gitignore` đúng,
      notebook sạch output, mọi registry hợp lệ, mọi config thí nghiệm hợp lệ, `REPO_SHA` hợp lệ và tồn tại).
      -> `feat(ci): add repository checks script`
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
