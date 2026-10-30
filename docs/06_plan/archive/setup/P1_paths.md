# P1 - Đường dẫn tập trung

> Đọc file này khi: sửa hoặc thêm đường dẫn trong dự án.
> Liên quan: `docs/05_config/01_paths.md`, `docs/00_workflow/02_rules.md`

## 1. Mục tiêu giai đoạn

Mọi đường dẫn của dự án lấy từ một nguồn duy nhất là `configs/paths.yaml`, qua `src/paths.py`.
Đổi cấu trúc thư mục thì chỉ sửa một file cấu hình.

## 2. Trạng thái

xong

## 3. Task nhỏ (mỗi task một commit)

- [x] T1. Thêm `configs/paths.yaml`: `roots`, `data`, `reports`, `configs`, `patterns`, `colab`, `canonical`.
- [x] T2. Thêm `src/paths.py`: nạp một lần, cấp API `root()`, `data()`, `processed()`, `report()`,
      `experiment_dir()`, `results_dir()`, `pattern()`; hỗ trợ ghi đè bằng biến môi trường
      `SENTIMENTX_DATA_ROOT`, `SENTIMENTX_RESULTS_ROOT`.
- [x] T3. Thêm `src/runtime.py`: `is_colab()`, biến `SENTIMENTX_ENV`, hàm nạp biến môi trường
      theo thứ tự Colab Secrets, `.env.colab`, `os.environ`, `.env`.
- [x] T4. Chuyển `src/config.py`, `src/versioning.py`, `src/reporting/`, các `run_*.py` sang dùng
      `src/paths.py`.
- [x] T5. Bỏ khoá `raw_dir` trong config dataset; suy ra từ `paths.yaml` + `name` + `raw_version`.
      Kèm theo: dữ liệu gốc chuyển vào `data/raw/cosmetics/v0.1.0/` và thêm `raw_meta.yaml`.
- [x] T6. Thêm test cho `src/paths.py`: đường dẫn mặc định, ghi đè bằng biến môi trường, và
      luật không còn đường dẫn viết cứng trong `src/` và các `run_*.py`.

Ghi chú khi làm, khác kế hoạch ban đầu:

- `MODEL_EVAL_REPORT_DIR` chưa bỏ ở đây mà để tới P4, vì đúng lúc đó kết quả đánh giá mới
  chuyển sang thư mục thí nghiệm. Bỏ sớm thì phải sửa hai lần.
  *Cập nhật 25/09/2026:* nó ở lại tới hết P4 (không task nào bỏ), rồi **đã bỏ** cùng
  `run_rescore_eval.py` khi rà soát lại: mọi kết quả nay đều thuộc một thí nghiệm, và thư mục kết quả
  là `experiments/<model>/<method>/<expNNN>/results/<hash8>/`.
- `EDA_REPORT_DIR` và `PIPELINE_REPORT_DIR` để lại tới P2, vì P2 mới đổi chỗ ghi kết quả.
- T4, T5, T6 nằm chung một commit với việc dọn ký hiệu AI trong code, vì cùng sửa một số file.

## 4. Điều kiện hoàn thành (DoD)

- Đổi một dòng trong `configs/paths.yaml` thì mọi nơi dùng đường dẫn đó đổi theo.
- Không còn đường dẫn dạng `data/...` viết cứng trong `src/` và các `run_*.py`
  (kiểm bằng tìm kiếm chuỗi).
- Chạy được `python run_eda.py --dataset cosmetics --raw-version v0.1.0` sau khi P2 xong.

## 5. Rủi ro / lưu ý

- `.gitignore` và `.gitattributes` không đọc được YAML, nên khi đổi cây thư mục vẫn phải sửa tay hai file này.
- Thứ duy nhất còn nằm trong code là `ROOT_DIR` suy từ `__file__`, vì cần nó để tìm ra `paths.yaml`.

## 6. Phụ thuộc

P0 xong (đã có cây mới và repo git).
