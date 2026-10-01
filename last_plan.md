# last_plan - kế hoạch đang triển khai (chi tiết)

> File này ghi ĐẦY ĐỦ nội dung từng mục của kế hoạch đã chốt trong cuộc trao đổi.
> Trạng thái nhanh nằm ở `check_last_plan.md`. Sửa kế hoạch thì sửa CẢ HAI file.
> Quy ước trạng thái: `[ ]` chưa làm · `[~]` đang làm dở · `[x]` xong · `[!]` chặn/quay lui.

Mục tiêu cao nhất: đo chỉ số và so THÍ NGHIỆM với CÔNG BỐ (nguồn số phải khớp giữa
metrics của lượt chạy, rescore, và collect_reports).

## Trạng thái tổng

- Đang ở: ĐANG DỞ. Xong Nhóm 0 (0-1..0-6), code Nhóm A (A-1..A-4; A-5/A-6 chặn), B-2/B-3/B-6, C-2.
  Còn lại: C-1, C-3, D-1..D-6, E-1..E-2, F-1..F-4, G-1..G-7, H-1..H-7.
- Nhánh: `experiment`. Mỗi mục xong = một commit (xem `git log`).
- CI sạch, test 774 OK (skipped=2) ở thời điểm dừng.

---

## Nhóm 0 - Sửa 5 chỗ docs lệch code

- [x] **0-1** `scripts/ci_checks.py`: docstring ghi "CHÍN KIỂM TRA" nhưng chỉ liệt kê 8 mục; thêm mục
  thứ 9 ("tài liệu trỏ đường dẫn mã nguồn") cho khớp `src/workflow/checks.py` và
  `docs/00_workflow/03_ci.md`.
- [x] **0-2** `docs/05_config/02_pipeline.md`: bỏ ví dụ `steps.normalize.teencode` (khoá không tồn tại
  trong `configs/pipeline/*.yaml`, trái chủ trương "pipeline không có công tắc teencode").
- [x] **0-3** `docs/00_workflow/02_rules.md` luật 20: thêm `eval_lock.json` vào danh sách file PHẢI
  commit (khớp `03_ci.md` check 1, `paths.yaml`, `.gitignore`, `changelog.md`).
- [x] **0-4** `docs/05_config/03_datasets.md`: ví dụ dùng `version: "0.3.0"` (thiếu tiền tố `v`) trong
  khi file thật là `vX.Y.Z`; sửa cho nhất quán.
- [x] **0-5** `README.md` mục quy ước
  nói rõ **4 `run_*.py`** (`run_eda`, `run_pipeline`, `run_token_stats`, `run_check_examples`) +
  `build_report.py` = **5 file**.
- [x] **0-6** (phát hiện khi chạy test) `tests/workflow/test_build_package.py::zip_names`: glob `*002*.zip`
  khớp NHẦM vì dấu ngày `%y%m%d` cũng chứa "002" (ngày 261002) -> 2 test DeltaTest đỏ. Lỗi CÓ SẴN,
  phụ thuộc ngày, KHÔNG do thay đổi của đợt này. Sửa: khoá glob thành `SentimentX-goi-<số>-*.zip`
  (siết chặt, không nới).

---

## Nhóm A - Sửa 3 lỗi đang chặn đường LoRA (ưu tiên tuyệt đối)

- [x] **A-1** Fix `KeyError: 'every_n_steps'` (lượt ViSoBERT).
  - Nguyên nhân: `src/experiments/encoder_run.py` dòng 317 trả `"training": found`, mà
    `found = lora.settings(...)` KHÔNG có khoá checkpoint; `log_config` (dòng 77-79) đọc
    `plan_data["training"]["every_n_steps"]` -> KeyError.
  - Sửa: dòng 317 -> `"training": {**found, **checkpoints.settings(config_data)}` (superset an toàn:
    giữ mọi khoá lora + thêm khoá checkpoint).
  - Test: chốt `plan()["training"]` có `every_n_steps`, và `log_config` không ném.

- [x] **A-2** Fix "PhoBERT báo thiếu model VnCoreNLP dù đã có trên Drive".
  - Nguyên nhân: `src/core/config.py` tính HẰNG đường dẫn NGAY LÚC IMPORT (dòng 22-35:
    `DATA_DIR = paths.data_root()`, `MODEL_ASSETS_DIR = paths.data("models")`, ...). Trên Colab,
    `SENTIMENTX_DATA_ROOT` chưa được đặt khi `src.api` -> `config` được import, nên hằng bị "đóng băng"
    vào repo `data/models`, không phải Drive. `vncorenlp.py` dòng 72 dùng hằng đóng băng đó.
  - Sửa (b) refactor triệt để: bỏ kiểu "hằng đường dẫn đóng băng" trong `config.py`; dùng `paths.*`
    TẠI CHỖ GỌI. `vncorenlp.MODEL_DIR` tính LÚC GỌI (`paths.data("models") / "vncorenlp"`).
  - Audit mọi chỗ dùng `config.*_DIR`: `ROOT_DIR`, `DATA_DIR`, `RAW_ROOT`, `PROCESSED_DIR`,
    `REPORT_DIR`, `MODEL_INPUT_REPORT_DIR`, `ASSETS_DIR`, `MODEL_ASSETS_DIR`, `CONFIG_DIR`,
    `DATASET_CONFIG_DIR`, `MODEL_CONFIG_DIR`, `PROMPT_DIR`.
  - Giữ TƯƠNG THÍCH: nơi khác còn import tên cũ thì giữ tên đó dưới dạng tính LÚC GỌI (không phá test),
    rồi dọn dần.
  - Test: đặt `SENTIMENTX_DATA_ROOT` vẫn cho đường dẫn đúng; `vncorenlp` không dùng giá trị đóng băng.

- [x] **A-3** Hint VnCoreNLP theo MÔI TRƯỜNG.
  - `src/preprocessing/segmenters/vncorenlp.py` (`available()`, `INSTALL_HINT`) + preflight: đang in
    "chạy scripts/setup/setup_vncorenlp.ps1" (script Windows) cả trên Colab.
  - Colab: "Restart session rồi Run all (ô bootstrap tự tải) hoặc chép `data/models/vncorenlp/` từ
    gói bàn giao"; local: giữ hướng dẫn `.ps1`.
  - Test: `available()` cho hai môi trường.

- [x] **A-4** Lượt chạy encoder lỗi KHÔNG ngắt phiên Colab (tốn quota).
  - Nguyên nhân: `experiment_run.run` có `with runtime.end_session_on_error(), runlog.start(...)`
    (dòng 716), nhưng với encoder nó `return encoder_run.run(...)` (dòng 709) TRƯỚC khối đó;
    `encoder_run.run` (dòng 396) chỉ có `with runlog.start(...)` -> THIẾU end_session.
  - Sửa: `encoder_run.run` -> `with runtime.end_session_on_error(), runlog.start(...) as active:`.
  - Test: chốt lỗi đường encoder gọi `unassign`.

- [!] **A-5** Ghim lại notebook LoRA + chạy lại. CHẶN: `scripts/pin.py` đòi commit đã nằm trên
  `origin/experiment`, mà đợt này CHƯA push lên GitHub -> chờ push rồi ghim.
  - Ghim lại `phobert-base-v2/lora/exp001` và `visobert/lora/exp001`; kết quả cũ `91f50523`
    (visobert) / `6aaa0f2f` (phobert) KHÔNG dùng nữa.
  - Cập nhật `docs/06_plan/P7_rerun.md`.

- [!] **A-6** Dọn run MLflow rỗng/treo `cd0cd000...`. CHẶN: cần MẠNG + token DagsHub (không chắc
  môi trường này có) -> để lại, chạy khi có mạng (dùng `scripts/smoke_tracking.py` để xoá theo mã run).

---

## Nhóm B - Đồng bộ nguồn số (collect_reports phải khớp mọi nguồn)

Mục tiêu: không xảy ra "lượt chạy đo một đằng, rescore đo một nẻo, collect_reports lấy một nẻo".

Bảng NGUỒN SỐ DUY NHẤT:

| Con số | Nguồn duy nhất | Ai đọc |
| --- | --- | --- |
| Đo của dự án trên test (all) | `metrics.json::scores` + `metrics.csv` (basis=`all`) | HTML lượt chạy, MLflow (không tiền tố) |
| Để SO CÔNG BỐ (paper) | `metrics.json::scores_paper` + `metrics.csv` (basis=`paper`) | `metrics_matrix` (cột `reference`), MLflow (`paper.`), `mispredictions_paper.csv` |
| Đo THÊM (rescore) | `metrics_rescored.json` / `metrics_rescored.csv` | `metrics_matrix` (họ cột `(rescored)` khi có) |
| Chọn best / early-stop (val) | `training_history.csv` + `metrics.json` (khối training) | người/MLflow; KHÔNG vào `metrics_matrix` |
| Curve train/val | `training_history.csv` + `plots/training.html` | người/MLflow step-metric |

- [ ] **B-1** Ghi bảng nguồn số trên vào `docs/04_experiments/metrics.md` +
  `docs/04_experiments/reference_publication.md`.
- [x] **B-2** `src/reporting/reports.py::metric_map` đọc thêm `metrics_rescored.csv` (giữ cột `basis`);
  KHÔNG trộn nguồn theo từng ô.
- [x] **B-3** Hiển thị HAI HỌ CỘT có nhãn `(gốc)` / `(rescored)` cho mỗi lượt (chỉ khi lượt đó có
  rescored). Mở rộng `column_labels`; nhãn phải KHÁC nhau (có test chống trùng nhãn sẵn).
- [ ] **B-4** Giữ `metrics.json::scores_paper` + `metrics.csv(basis=paper)` là nguồn so công bố;
  `reference` vẫn lấy từ `data/reference_publication/`.
- [ ] **B-5** KHÔNG đưa chỉ số chọn-best (val) vào `metrics_matrix`.
- [x] **B-6** Test `tests/reporting/test_reports.py` cho hai họ cột + nguồn.

---

## Nhóm C - Engine đo chung + rescore (tách train/đo)

- [ ] **C-1** `lora.measure()` -> **val đi qua `Samples`** (đủ P/R/F1/detection/exact như test).
  CHỈ đường encoder (prompt không train nên không có `measure()`; đường prompt ĐÃ dùng `Samples` cho
  split chấm điểm qua `experiment_run.finish`).
- [x] **C-2** Rescore CHỈ THÊM (bỏ hoàn toàn "thay số"): `metrics_rescored.json/.csv` (pattern mới ở
  `configs/paths.yaml`), khối `rescored` (thời điểm/lý do/danh sách chỉ số THÊM), KHÔNG ghi đè bản gốc.
  Áp dụng CẢ encoder LẪN prompt (đọc `predictions.csv`).
- [ ] **C-3** Test BẤT ĐỐI XỨNG (P ≠ R ≠ F1) cho mọi thay đổi hàm chấm điểm.

---

## Nhóm D - Early stop + biểu đồ train/val

- [ ] **D-1** `early_stop: {enabled, metric, patience, min_delta}` ở `configs/experiments/training.yaml`;
  `metric` mặc định `sentiment_f1_macro`; guard danh sách hợp lệ; in + log `[STEP] dừng sớm`; CHỈ LoRA
  (prompt bỏ qua). + test + docs.
- [ ] **D-2** `checkpoints.best_metric` = `sentiment_f1_macro` (+ LUÔN ghi kèm P/R).
- [ ] **D-3** `measure()` thêm `val_loss` + P/R/F1 (metric train nếu bật).
- [ ] **D-4** `training_history.csv` (pattern mới), entry CUỐI MỖI EPOCH: train_loss TB, val_loss, P/R/F1.
- [ ] **D-5** `plots/training.html` bằng plotly + jinja2 (`src/reporting/render.py` + `templates/`); thêm
  kind `line` vào `src/reporting/charts.py`; vẽ P/R/F1 + loss train/val.
- [ ] **D-6** Log step-metric lên MLflow (để MLflow tự vẽ curve) + gửi CSV artifact; Drive có cả CSV
  lẫn HTML (HTML không lên MLflow).

---

## Nhóm E - Loss chống lệch (làm ngay)

- [ ] **E-1** `loss` config-driven: `weighted_ce(class_weight: inverse)` cho encoder (focal/trọng số
  khía cạnh để SAU).
- [ ] **E-2** Ghi rõ: đổi loss -> `config_sha256` đổi -> thư mục kết quả MỚI (không ghi đè).

---

## Nhóm F - MLflow

- [ ] **F-1** Thêm `run.log` vào `configs/experiments/tracking.yaml::artifacts` (+ `training_history.csv`;
  cân nhắc `metrics_rescored.*`). + test + docs.
- [ ] **F-2** Params bị cắt 500: SỐ PHẲNG -> metric (`read_rate.% đọc được`, `cost.giây`, `cost.số bước`);
  CẤU TRÚC LỚN -> artifact JSON (`read_rate` phân bố lý do, `model_info`, `subset`). + test.
- [ ] **F-3** Log `scores_paper` với tiền tố `paper.` + tạo 1 run tham chiếu công bố; giữ `metrics_matrix`.
- [ ] **F-4** A8: `run_id` vào `run_meta.json` (sửa CÙNG dict `record`; carry `tracking` qua `previous`),
  GỬI PARAMS Ở `begin()`, LOG TĂNG DẦN, NỐI RUN khi resume (`mlflow.start_run(run_id=...)`), ánh xạ
  N attempt : 1 result dir : 1 run. Chốt: cùng result dir chạy 2 máy => cùng run (env ghi theo attempt).
  + test (attempts còn nguyên; resume không mở run mới; resume.decide không đổi).

---

## Nhóm G - Lưu vết, docs, test, hạ tầng

- [ ] **G-1** `docs/04_experiments/04_backlog.md`: Optuna (hoãn một nhịp), focal/trọng số khía cạnh (sau
  `weighted_ce` + bằng chứng curve) - mỗi mục *việc gì / vì sao hoãn / bắt đầu từ đâu* + mốc ngày.
- [ ] **G-2** `docs/04_experiments/07_evolution.md` - file MỚI, TRỐNG chờ ghi dần; header 2 dòng; đăng ký
  `docs/README.md`.
- [ ] **G-3** Ghi chú A7: ma trận nhầm ở artifact/report, không lên MLflow.
- [ ] **G-4** Docs kèm: `06_lora_encoder.md`, `05_experiments_shared.md`, `01_paths.md`, `metrics.md`,
  `01_flow.md`, `05_predictions.md`, `07_colab.md` (sự cố VnCoreNLP), `P7_rerun.md`, `README.md`.
- [ ] **G-5** Tests: `tests/training/test_training.py`, `test_tracking.py`, `tests/evaluation/test_scorers.py`,
  `tests/workflow/test_runtime.py`, `test_templates.py`, `tests/experiments/test_experiment_run.py`,
  `tests/reporting/test_reports.py`.
- [ ] **G-6** Hạ tầng: `configs/paths.yaml` (pattern `training_history`, `metrics_rescored`),
  `configs/experiments/tracking.yaml` (`run.log`, `training_history.csv`),
  `configs/experiments/training.yaml` (`early_stop`, `loss`, `checkpoints.best_metric`),
  `configs/experiments/evaluation.yaml` (nếu cần); `.gitignore` cho file mới (track `metrics_rescored.csv`,
  `training_history.csv`; `plots/` vốn đã bỏ qua).
- [ ] **G-7** Sau mỗi nhóm: `python scripts/ci_checks.py` + `python -m unittest discover -s tests`
  (kiểm 4/5/7/8/9).

---

## Nhóm H - Chốt thiết kế (ghi docs, không code riêng)

- [ ] **H-1** So công bố = `paper.accuracy`; chọn best/early-stop = `sentiment_f1_macro` (kèm P/R trong
  CSV/HTML); theo dõi `detection_f1_macro`.
- [ ] **H-2** Chọn best (all, val) KHÁC so công bố (paper, test) - không đem số `all` đi so công bố.
- [ ] **H-3** Rescore = chấm THÊM, không ghi đè; hiển thị hai họ cột `(gốc)`/`(rescored)`.
- [ ] **H-4** Optuna: hoãn một nhịp.
- [ ] **H-5** Giữ bất biến cũ: `test` không bị sửa; không bỏ dấu; teencode chỉ đo; `eval_lock`.
- [ ] **H-6** A8: 1 result dir <-> 1 run; nhiều attempt nối cùng run; 2 máy cùng dir => cùng run.
- [ ] **H-7** "Engine đo chung" hoàn thiện cho encoder; CẢ HAI đường dùng chung ở rescore.

---

## Quy ước thực thi (bắt buộc)

1. Commit sau mỗi mục đã xong, theo Conventional Commits tiếng Anh (`docs/00_workflow/05_git_commits.md`).
2. Sửa kế hoạch thì sửa CẢ `last_plan.md` và `check_last_plan.md`. Hạn chế sửa kế hoạch.
3. Sau mỗi nhóm: chạy `python scripts/ci_checks.py` + `python -m unittest discover -s tests`
   (Windows: `$env:PYTHONUTF8=1`).
4. Lỗi không fix được / quá khó -> quay lui (git) và xem xét lại kế hoạch.
5. Giữ bất biến dự án: không hardcode đường dẫn (dùng `configs/paths.yaml`); không đặt mặc định trong
   code (thiếu khoá là lỗi); notebook đã ghim KHÔNG sửa (muốn hiệu lực thì ghim mới).

## Mặc định đã chốt cho file mới

- `metrics_rescored.csv` + `training_history.csv`: git theo dõi (file nhẹ) + đẩy MLflow (artifact).
- `plots/training.html`: KHÔNG vào git (`plots/` bị `.gitignore`) và KHÔNG lên MLflow.
- Trạng thái file này: ĐÃ GHI KẾ HOẠCH, chưa triển khai.
