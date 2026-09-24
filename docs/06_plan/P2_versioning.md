# P2 - Versioning dữ liệu và guard

> Đọc file này khi: tạo phiên bản dữ liệu mới, hoặc sửa cách tính mã phiên bản.
> Liên quan: `docs/05_config/02_pipeline.md`, `docs/05_config/03_datasets.md`

## 1. Mục tiêu giai đoạn

Dữ liệu có phiên bản rõ ràng: raw, dataset, pipeline đều có mã; file phiên bản là bất biến và có guard.
Mã phiên bản dữ liệu đủ để tra ngược: nguồn nào, pipeline nào, nội dung nào.

## 2. Trạng thái

xong

## 3. Task nhỏ (mỗi task một commit)

- [x] T1. Chuyển `configs/pipeline.yaml` thành `configs/pipeline/<version>.yaml` (đã có `v0.1.0.yaml`
      với `version`, `parent`, `notes`, `steps`, `thresholds`); bỏ việc tự điền giá trị mặc định
      trong `load_pipeline_config`.
- [x] T2. `configs/datasets/cosmetics/v0.1.0.yaml` theo cấu trúc mới (`schema_version`, `name`,
      `version`, `sources`, `pipeline_version`, `format`, `splits`, `full`, `schema`, `aspect_policy`,
      `parent`, `notes`, `eval_lock`).
- [x] T3. `src/versioning.py`: mã dạng `<name>-ds<version>-pl<pipeline_version>-src<nguồn>@<phiên bản>-<hash8>`;
      bỏ tầng `versions/` và `manifest.json`; kết quả nằm ở `data/processed/<mã>/` (dataset +
      thư mục `pipeline/`); EDA ghi kết quả cạnh thứ nó đo; `processing_log.json` ghi đầy đủ dấu vết.
- [x] T4. Guard bất biến: `versioning.guard_versions()` so `sha256` của file phiên bản với giá trị
      đã ghi trong mọi `processing_log.json`; lệch thì báo lỗi và hướng dẫn tạo phiên bản mới.
      Gọi ở `run_pipeline.py` và `run_eda.py`.
- [x] T5. Bắt buộc `--version` ở `run_pipeline.py`; `run_eda.py` chọn nơi đo bằng `--raw-version`
      (đo dữ liệu gốc) hoặc `--version` (đo dataset đã xử lý).
- [x] T6. Test cho mã phiên bản, guard, và đường dẫn kết quả (`tests/test_versioning.py`).

Ghi chú khi làm:

- `eval_lock.test.sha256` để `null` ở phiên bản đầu; cuối lần chạy pipeline in ra giá trị vừa
  đo, và giá trị đó được chốt khi **tạo phiên bản dataset kế tiếp**. Không điền vào file đang
  dùng, vì file phiên bản đã dùng là bất biến và guard sẽ chặn.
- Kết quả sinh ra (`processing_log.json`, `report.html`, `pipeline_result.json`, kết quả EDA)
  hiện vẫn được commit; việc chọn nhóm report nào commit là việc của P6.
- Guard chặn cả trường hợp sửa một dòng chú thích trong file phiên bản đã dùng. Đó là chủ ý:
  nội dung file đi vào mã phiên bản, nên mọi thay đổi đều làm kết quả cũ không còn tra được.

## 4. Điều kiện hoàn thành (DoD)

- Chạy hai phiên bản dataset khác nhau ra hai mã khác nhau, hai thư mục khác nhau.
- Sửa file phiên bản đã dùng thì lệnh chạy báo lỗi đúng thông điệp đã định.
- `data/processed/<mã>/` chứa `train.csv`, `val.csv`, `test.csv`, `label_map.json`,
  `processing_log.json`, `pipeline/`.

## 5. Rủi ro / lưu ý

- Kết quả cũ trong `data/processed/` và `data/reports/*/versions/` sẽ không dùng nữa.
- Nếu chạy pipeline khi cây làm việc bẩn, ghi cảnh báo `git_dirty` để biết kết quả không tái lập được từ git.

## 6. Phụ thuộc

P1 xong (đường dẫn đã tập trung).
