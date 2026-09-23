# P4 — Log, MLflow/DagsHub, resume

> Đọc file này khi: chạy thí nghiệm, xem log, hoặc gặp lỗi khi log lên DagsHub.
> Liên quan: `docs/05_config/05_experiments_shared.md` · `docs/00_workflow/02_rules.md` · `docs/04_experiments/metrics.md`

## 1. Mục tiêu phase

Mỗi lần chạy có log và dấu vết đầy đủ, chỉ số tính theo đúng công bố, kết quả lên DagsHub,
và resume được khi bị ngắt giữa chừng.

## 2. Trạng thái

chưa làm

## 3. Việc nhỏ (mỗi task một commit)

- [ ] T1. `src/labels/`: registry `LABEL_SPACES` với `binary` và `full`; `neutral_policy`,
      `not_mentioned`; hợp đồng `check()`.
      → `feat(labels): add label space registry`
- [ ] T2. Model preprocessing: chiếu nhãn theo `task.yaml` (lược neutral), tái sử dụng được,
      notebook gọi tới.
      → `feat(preprocessing): project labels from task config`
- [ ] T3. `src/evaluation/scorers/`: registry `SCORERS` gồm `accuracy`, `aspect_detection`, `prf`,
      `aggregate`, `confusion`; ghi `metrics.json` và `metrics.csv`.
      → `feat(evaluation): add scorers registry`
- [ ] T4. `src/runlog.py`: `run.log` luôn có, `errors.json` chỉ khi có lỗi, ghi được khi crash.
      → `feat(runlog): write run log and error file only on failure`
- [ ] T5. `src/tracking/`: registry `TRACKERS` gồm `mlflow`, `local_json`, `none`.
      → `feat(tracking): add trackers registry`
- [ ] T6. `run_meta.json`: đủ trường, có `attempts[]`, `files[]` kèm `role`, không ghi đường dẫn tuyệt đối.
      → `feat(tracking): write run metadata with attempts and provenance`
- [ ] T7. MLflow lên DagsHub theo `configs/dagshub.yaml`; **chạy smoke run và xác nhận run xuất hiện**
      trên `https://dagshub.com/TrieuKhac-dev/SentimentX`; log lỗi không làm chết run.
      → `feat(mlflow): configure dagshub remote and smoke test`
- [ ] T8. Resume: ghi kết quả theo khối `predictions/part_*.jsonl`, chạy lại thì bỏ qua mẫu đã xử lý;
      điều kiện resume là `config_sha256` + mã phiên bản + `repo.sha` đều không đổi.
      → `feat(resume): chunk predictions and resume by sample`
- [ ] T9. Test cho các chỉ số theo định nghĩa trong `docs/04_experiments/metrics.md`.
      → `test(evaluation): add metric tests`

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
