# P2 - Versioning dữ liệu và guard

> Đọc file này khi: tạo phiên bản dữ liệu mới, hoặc sửa cách tính mã phiên bản.
> Liên quan: `docs/05_config/02_pipeline.md`, `docs/05_config/03_datasets.md`

## 1. Mục tiêu giai đoạn

Dữ liệu có phiên bản rõ ràng: raw, dataset, pipeline đều có mã; file phiên bản là bất biến và có guard.
Mã phiên bản dữ liệu đủ để tra ngược: nguồn nào, pipeline nào, nội dung nào.

## 2. Trạng thái

đang làm, xong T1

## 3. Task nhỏ (mỗi task một commit)

- [x] T1. Chuyển `configs/pipeline.yaml` thành `configs/pipeline/<version>.yaml` (đã có `v0.1.0.yaml`
      với `version`, `parent`, `notes`, `steps`, `thresholds`); bỏ việc tự điền giá trị mặc định
      trong `load_pipeline_config`.
- [ ] T2. Tách `configs/datasets/cosmetics/v0.1.0.yaml` thành `configs/datasets/cosmetics/<version>.yaml`
      với `schema_version`, `name`, `version`, `sources`, `pipeline_version`, `format`, `splits`,
      `full`, `schema`, `aspect_policy`, `parent`, `notes`.
      -> `refactor(config): split dataset config into per-version files`
- [ ] T3. Cập nhật `src/versioning.py`: mã dạng `<name>-ds<version>-pl<pipeline_version>-src<nguồn>@<phiên bản>-<hash8>`;
      bỏ tầng `versions/`; ghi `processing_log.json` đầy đủ.
      -> `feat(versioning): build data version id from ds pl and src segments`
- [ ] T4. Guard bất biến: so `sha256` của file phiên bản với giá trị đã ghi trong mọi
      `processing_log.json`; lệch thì báo lỗi và hướng dẫn tạo phiên bản mới.
      -> `feat(versioning): guard immutable versioned configs`
- [ ] T5. Bắt buộc `--version` ở `run_pipeline.py` và `run_eda.py`; `run_eda.py` nhận
      `--raw-version` khi EDA chạy trên raw.
      -> `refactor(cli): require explicit version in runners`
- [ ] T6. Test cho mã phiên bản và guard.
      -> `test(versioning): cover id and guard`

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
