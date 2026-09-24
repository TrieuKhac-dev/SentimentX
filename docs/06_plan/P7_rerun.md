# P7 - Chạy lại từ đầu và so với công bố

> Đọc file này khi: bắt đầu sinh kết quả chính thức cho báo cáo.
> Liên quan: `docs/04_experiments/metrics.md`, `docs/04_experiments/reference_publication.md`

## 1. Mục tiêu phase

Sinh lại toàn bộ dữ liệu và kết quả từ đầu theo cấu trúc mới, so được trực tiếp với công bố tham chiếu,
và có một vòng bàn giao hoàn chỉnh cho giảng viên.

## 2. Trạng thái

chưa làm

## 3. Task nhỏ (mỗi task một commit)

- [ ] T1. Chạy lại pipeline để sinh phiên bản dataset đầu tiên theo cấu trúc mới.
      -> `feat(data): rebuild dataset version from raw`
- [ ] T2. Chạy lại EDA trên raw và trên dataset; sinh report tương ứng.
      -> `feat(data): regenerate eda and pipeline reports`
- [ ] T3. Chạy baseline prompt 0-shot, 1-shot, 5-shot trên tập `test` đúng như công bố.
      -> `feat(experiments): run baseline prompt experiments`
- [ ] T4. Sinh bảng so sánh với cột `reference`; ghi lại kết quả và khoảng cách.
      -> `docs(experiments): record baseline results against reference`
- [ ] T5. Giao notebook cho giảng viên: đẩy dữ liệu, notebook và `.env.colab` lên Drive, gửi hướng dẫn.
      (không tạo commit)

## 4. Điều kiện hoàn thành (DoD)

- `data/reports/metrics_matrix/accuracy_by_aspect.csv` có cột `reference` và cột cho từng `expNNN`.
- Tập `test` không đổi: `sha256` khớp `eval_lock` trong file dataset version.
- Một thí nghiệm chạy trọn vẹn trên Colab của giảng viên, kết quả nằm trên Drive và trên DagsHub.

## 5. Rủi ro / lưu ý

- Nếu giảng viên chỉ có TPU, QLoRA không chạy: giữ Qwen3 ở dạng prompt và huấn luyện encoder.
- Kết quả sinh trên Colab nằm trên Drive; muốn vào git thì phải copy phần nhẹ về.

## 6. Phụ thuộc

P6 xong (đã có report và CI).
