# P3 - Tầng config thí nghiệm

> Đọc file này khi: tạo hoặc sửa cấu hình của một thí nghiệm.
> Liên quan: `docs/05_config/05_experiments_shared.md`, `docs/05_config/06_experiment.md`

## 1. Mục tiêu giai đoạn

Cấu hình thí nghiệm được hợp nhất từ 7 lớp, biết rõ mỗi khoá đến từ file nào,
có dấu vết để tra cứu, và chặn được các lỗi im lặng (thiếu vai, rò rỉ dữ liệu, trùng thí nghiệm).

## 2. Trạng thái

đang làm, xong T1

## 3. Task nhỏ (mỗi task một commit)

- [x] T1. Thêm config dùng chung: `configs/experiments/repo.yaml`, `task.yaml`, `evaluation.yaml`,
      `training.yaml`, `tracking.yaml`.
- [ ] T1b. Chuẩn hoá `configs/models/<model_id>.yaml` theo cấu trúc mới (`model_id`, `checkpoint`,
      `config_version`, `task.*`, `preprocess.*`, `inference.*`), đổi tên file theo `model_id`;
      cập nhật `src/model_config.py` và các module đang đọc khoá cũ.
      -> `refactor(config): restructure model configs by model id`
- [ ] T2. `src/experiments.py`: hợp nhất 7 lớp theo thứ tự, ghi lại nguồn của từng khoá,
      in bảng ghi đè.
      -> `feat(experiments): merge config layers with per-key source tracking`
- [ ] T3. `config_sha256`: băm JSON chuẩn hoá của config đã hợp nhất, cộng văn bản prompt đã hợp nhất
      (`prompt_merged`).
      -> `feat(experiments): hash merged config and merged prompt`
- [ ] T4. Kiểm tra: `roles` bắt buộc khai; một dataset duy nhất; `splits` phải có trong file dataset version;
      chặn `eval` trỏ vào `train`.
      -> `feat(experiments): validate roles single dataset and leakage`
- [ ] T5. Sinh danh sách `requires` từ dataset version, mã phiên bản và `roles`; cộng `requires_extra`.
      -> `feat(experiments): derive required paths`
- [ ] T6. Guard trùng: so `(config_sha256, mã, exp_id)` với mọi `run_meta.json` đã có.
      -> `feat(experiments): add duplicate guard`
- [ ] T7. Test cho thứ tự hợp nhất, bảng ghi đè và các lỗi kiểm tra.
      -> `test(experiments): cover merge overrides and validation`

## 4. Điều kiện hoàn thành (DoD)

- Notebook in được bảng ghi đè và giá trị hiệu lực của một thí nghiệm mẫu.
- Config thiếu `roles` hoặc `eval` trỏ `train` đều báo lỗi rõ ràng, kèm file đã đọc.
- Đổi một khoá trong config dùng chung làm `config_sha256` đổi.

## 5. Rủi ro / lưu ý

- Ghi đè phải ghi rõ nguồn, nếu không thì rất khó tra khi có nhiều lớp.
- Chuẩn hoá phải ổn định: khoá sắp xếp, mọi danh sách coi là tập hợp và sắp xếp,
  trừ danh sách khai trong `canonical.ordered_lists`.

## 6. Phụ thuộc

P2 xong (đã có mã phiên bản dữ liệu).
