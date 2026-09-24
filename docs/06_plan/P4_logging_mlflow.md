# P4 - Log, MLflow/DagsHub, resume

> Đọc file này khi: chạy thí nghiệm, xem log, hoặc gặp lỗi khi log lên DagsHub.
> Liên quan: `docs/05_config/05_experiments_shared.md`, `docs/00_workflow/02_rules.md`, `docs/04_experiments/metrics.md`

## 1. Mục tiêu giai đoạn

Mỗi lần chạy có log và dấu vết đầy đủ, chỉ số tính theo đúng công bố, kết quả lên DagsHub,
và resume được khi bị ngắt giữa chừng.

## 2. Trạng thái

xong (T1..T9). Cả mục cuối của mục 4 - "ngắt giữa chừng rồi chạy lại trên MỘT LƯỢT CHẠY THẬT" - đã
kiểm ngày 24/09/2026 bằng một lượt chạy Qwen3-4B-Instruct-2507 (4-bit) trên máy cá nhân; xem chi
tiết ở T8. Không còn mục nào phải chờ P7.

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
- [x] T8. Resume: ghi kết quả theo khối `predictions/part_*.jsonl`, chạy lại thì bỏ qua mẫu đã xử lý;
      điều kiện resume là `config_sha256` + mã phiên bản + `repo.sha` đều không đổi.
      -> `feat(resume): chunk predictions and resume by sample`
      Kiểm bằng test (17 ca mới: quyết định NEW/RESUME/STOP, dòng viết dở được đếm lại, khối cũ
      được chuyển sang thư mục con, điểm số dùng cả mẫu cũ) và bằng một LƯỢT CHẠY THẬT ngày
      24/09/2026 (`--prompt absa_cot_v1 --limit 4`, Qwen3-4B-Instruct-2507 4-bit, chạy ngoài thí
      nghiệm nên kết quả ở `data/reports/model_eval/`):
        - lần 1 `mode=NEW`; ngắt MỀM (Ctrl+Break, giống bấm Stop trong Colab) ngay sau khi khối
          `predictions/part_0001.jsonl` đầu tiên đã nằm trên đĩa. `run.log` ghi `[RUN] mode=NEW`,
          tiến trình tự thoát (mã `0xC000013A`) - tức là ngắt giữa chừng được, không chỉ hỏng giả.
        - lần 2 chạy ĐÚNG lệnh đó: `run.log` ghi `[RUN] mode=RESUME`; `[RUN] n_samples=3` (chỉ 3 mẫu
          còn lại, không chạy lại mẫu đã xong); `metrics.json` có
          `resume = {mode: RESUME, reason: "chạy tiếp từ 1 mẫu đã xong của lần chạy trước",
          reused: 1, new: 3}`; lượt này xong sau 49,6 giây.
        - lần 3 thêm `--new`: `mode=NEW`, `[RUN] stashed=.../predictions/_bo-qua-2026-09-24-205105`
          (kết quả cũ được CHUYỂN sang thư mục con, không xoá), `resume = {mode: NEW, reused: 0,
          new: 4}`, mã thoát 0.
      Thư mục bằng chứng (file nhỏ nên để trong git, cùng lý do `.gitignore` giữ chúng cho thí
      nghiệm): `data/reports/model_eval/cosmetics-ds0.1.0-pl0.1.0-srccosmetics@0.1.0-bf68b1c5/`
      `prompt-absa_cot_v1__val__n4__greedy__Qwen3-4B-Instruct-2507/` - đọc `run.log` trước, rồi
      `metrics.json` (khoá `resume`), rồi `predictions/_bo-qua-*/part_0001.jsonl` và khối hiện tại.
- [x] T9. Test cho các chỉ số theo định nghĩa trong `docs/04_experiments/metrics.md`.
      -> `test(evaluation): add metric tests`
      Kiểm từng cam kết một: độ chính xác của bài toán nhắc tới (cả hai lớp), macro/micro và khớp
      hoàn toàn, `acc khi có nhắc`, điểm macro bỏ qua lớp không có ô nào, không gian `full` giữ mã
      0 như một lớp, trục ma trận nhầm có đủ nhãn, `metrics.csv` đúng dạng bảng dài, và
      `mispredictions.csv` chỉ có ô đoán sai.

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
