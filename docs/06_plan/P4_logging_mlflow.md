# P4 - Log, MLflow/DagsHub, resume

> Đọc file này khi: chạy thí nghiệm, xem log, hoặc gặp lỗi khi log lên DagsHub.
> Liên quan: `docs/05_config/05_experiments_shared.md`, `docs/00_workflow/02_rules.md`, `docs/04_experiments/metrics.md`

## 1. Mục tiêu giai đoạn

Mỗi lần chạy có log và dấu vết đầy đủ, chỉ số tính theo đúng công bố, kết quả lên DagsHub,
và resume được khi bị ngắt giữa chừng.

## 2. Trạng thái

đang làm - T1, T2, T3, T4, T5, T6, T7 xong (cổng MLflow đạt).

## 3. Task nhỏ (mỗi task một commit)

- [x] T1. `src/labels/`: registry `LABEL_SPACES` với `binary` và `full`; `neutral_policy`
      (`drop`/`as_negative`/`as_positive`/`keep`), `not_mentioned` (`separate`/`as_class`);
      hợp đồng ở `src/labels/base.py` gồm `check()` và `project()`. (Chung commit với T2, và
      commit đó cũng mang phần cập nhật trạng thái P1-P3 của tài liệu kế hoạch.)
- [x] T2. Chiếu nhãn cho model: `src/labels/allowed_codes()`, `filter_label_map()` (bảng mã nhãn đưa
      cho model), và `preprocessing.loader.project_multi_head()` trả `(nhãn, mask)` - ô neutral bị
      loại thì mask 0 chứ không xoá cả dòng; `dropped_cells()` để ghi vào metrics.json.
- [x] T3. `src/evaluation/scorers/`: registry `SCORERS` gồm `accuracy`, `aspect_detection`, `prf`,
      `aggregate`, `confusion`; ghi `metrics.json` và `metrics.csv`.
      -> `feat(evaluation): add scorers registry`
- [x] T4. `src/runlog.py`: `run.log` luôn có, `errors.json` chỉ khi có lỗi, ghi được khi crash.
      -> `feat(runlog): write run log and error file only on failure`
- [x] T5. `src/tracking/`: registry `TRACKERS` gồm `mlflow`, `local_json`, `none`.
      -> `feat(tracking): add trackers registry`
- [x] T6. `run_meta.json`: đủ trường, có `attempts[]`, `files[]` kèm `role`, không ghi đường dẫn tuyệt đối.
      -> `feat(tracking): write run metadata with attempts and provenance`
- [x] T7. MLflow lên DagsHub theo `configs/dagshub.yaml`; **chạy smoke run và xác nhận run xuất hiện**
      trên `https://dagshub.com/TrieuKhac-dev/SentimentX`; log lỗi không làm chết run.
      -> `feat(mlflow): configure dagshub remote and smoke test`
      Cổng ĐẠT ngày 24/09/2026: run smoke xuất hiện trong experiment `sentimentx-absa` ở
      `https://dagshub.com/TrieuKhac-dev/SentimentX.mlflow` (địa chỉ có đuôi `.mlflow`, khác trang
      repo - trang repo chỉ hiện dữ liệu của DagsHub nên nhìn như rỗng). Các run kiểm tra đều được
      gắn nhãn `smoke=true` và dọn bằng `python scripts/smoke_tracking.py --clean`, nên mục
      Experiments chỉ còn kết quả thật.
- [ ] T8. Resume: ghi kết quả theo khối `predictions/part_*.jsonl`, chạy lại thì bỏ qua mẫu đã xử lý;
      điều kiện resume là `config_sha256` + mã phiên bản + `repo.sha` đều không đổi.
      -> `feat(resume): chunk predictions and resume by sample`
- [ ] T9. Test cho các chỉ số theo định nghĩa trong `docs/04_experiments/metrics.md`.
      -> `test(evaluation): add metric tests`

Việc sửa theo góp ý khi rà soát (header tài liệu đúng hai dòng, và đổi tên prompt dùng chung
theo nội dung thay vì theo model) nằm chung một commit `623c053`, vì ba file tài liệu bị cả hai
việc. Không phải một task của P4, ghi ở đây để tra lại nguồn gốc thay đổi.

T7 đã có phần cấu hình và công cụ (`configs/dagshub.yaml`, `src/tracking/mlflow_tracker.py`,
`scripts/smoke_tracking.py`), nhưng **cổng chưa chạy được**: cần `DAGSHUB_TOKEN` của chủ tài khoản
DagsHub (`TrieuKhac-dev`) và cần mạng. Chưa có token thì `python scripts/smoke_tracking.py` in ra
đúng hai việc còn thiếu (token, thư viện `mlflow`) và kết thúc với mã thoát 2 - đúng như thiết kế:
ghi nhận hỏng không được làm hỏng lần chạy.

## 4. Điều kiện hoàn thành (DoD)

- Cổng MLflow đạt: run smoke xuất hiện trên DagsHub.
- Ngắt giữa chừng rồi chạy lại: `run.log` có dòng `[RUN] mode=RESUME`, tiếp tục từ mẫu đã dừng.
- `metrics.json` ghi rõ `label_space`, `neutral_policy`, số ô neutral bị loại.
- MLflow lỗi thì vẫn có `metrics.json` và `run_meta.json` trong thư mục kết quả.

## 5. Rủi ro / lưu ý

- Không đạt cổng MLflow thì dừng, báo cáo và đưa giải pháp; không triển khai tiếp phần phụ thuộc MLflow.
- DagsHub free: private tối đa 100 run, owner cộng 2 cộng tác viên, 20 GB. Không đẩy checkpoint lên DagsHub.
- Token nằm trong `.env.colab` hoặc Colab Secrets, tuyệt đối không commit.

## 6. Phụ thuộc

P3 xong (đã có config đã hợp nhất và `config_sha256`).
