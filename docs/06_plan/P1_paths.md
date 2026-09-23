# P1 — Đường dẫn tập trung

> Đọc file này khi: sửa hoặc thêm đường dẫn trong dự án.
> Liên quan: `docs/05_config/01_paths.md` · `docs/00_workflow/02_rules.md`

## 1. Mục tiêu phase

Mọi đường dẫn của dự án lấy từ một nguồn duy nhất là `configs/paths.yaml`, qua `src/paths.py`.
Đổi cấu trúc thư mục thì chỉ sửa một tệp cấu hình.

## 2. Trạng thái

chưa làm

## 3. Việc nhỏ (mỗi task một commit)

- [ ] T1. Thêm `configs/paths.yaml`: `roots`, `data`, `reports`, `configs`, `patterns`, `colab`, `canonical`.
      → `feat(config): add central paths config`
- [ ] T2. Thêm `src/paths.py`: nạp một lần, cấp API `root()`, `data()`, `processed()`, `report()`,
      `experiment_dir()`, `results_dir()`, `pattern()`; hỗ trợ ghi đè bằng biến môi trường
      `SENTIMENTX_DATA_ROOT`, `SENTIMENTX_RESULTS_ROOT`.
      → `feat(paths): add paths module with env overrides`
- [ ] T3. Thêm `src/runtime.py`: `is_colab()`, biến `SENTIMENTX_ENV`, hàm nạp biến môi trường
      theo thứ tự Colab Secrets, `.env.colab`, `os.environ`, `.env`.
      → `feat(runtime): add colab detection and env loading`
- [ ] T4. Chuyển `src/config.py`, `src/versioning.py`, `src/reporting/`, các `run_*.py` sang dùng
      `src/paths.py`; bỏ các hằng số đường dẫn cũ như `MODEL_EVAL_REPORT_DIR`.
      → `refactor(config): route all paths through paths module`
- [ ] T5. Bỏ khoá `raw_dir` trong config dataset; suy ra từ `paths.yaml` + `name` + `raw_version`.
      → `refactor(datasets): derive raw dir from paths`
- [ ] T6. Thêm test cho `src/paths.py` (đường dẫn mặc định và khi có biến môi trường).
      → `test(paths): cover resolution and env overrides`

## 4. Điều kiện hoàn thành (DoD)

- Đổi một dòng trong `configs/paths.yaml` thì mọi nơi dùng đường dẫn đó đổi theo.
- Không còn đường dẫn dạng `data/...` viết cứng trong `src/` và các `run_*.py`
  (kiểm bằng tìm kiếm chuỗi).
- Chạy được `python run_eda.py --dataset cosmetics --version v0.1.0` sau khi P2 xong.

## 5. Rủi ro / lưu ý

- `.gitignore` và `.gitattributes` không đọc được YAML, nên khi đổi cây thư mục vẫn phải sửa tay hai tệp này.
- Thứ duy nhất còn nằm trong code là `ROOT_DIR` suy từ `__file__`, vì cần nó để tìm ra `paths.yaml`.

## 6. Phụ thuộc

P0 xong (đã có cây mới và repo git).
