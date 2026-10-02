# P8 - Đợt "đo lường + MLflow" (mốc 02/10/2026)

> Đọc file này khi: cần tra vì sao có các thay đổi về đo lường, rescore, curve train/val, loss và
> MLflow; hoặc đang chuẩn bị **phát hành lại** (sửa CI -> ghim -> gói bàn giao).
> Liên quan: [README.md](README.md), [P4_logging_mlflow.md](P4_logging_mlflow.md),
> [P6_reports_ci.md](P6_reports_ci.md), [P7_rerun.md](P7_rerun.md),
> [../04_experiments/07_evolution.md](../04_experiments/07_evolution.md) (bản NGƯỜI ĐỌC của các chốt).
>
> File này GỘP hai file kế hoạch tạm trước đây ở gốc repo (`check_last_plan.md` + `last_plan.md`):
> mục 2 là "trạng thái nhanh", mục 3 là nội dung chi tiết. Trạng thái tổng cũng nằm ở bảng trong
> [README.md](README.md).

## 1. Mục tiêu giai đoạn

Đo chỉ số và so THÍ NGHIỆM với CÔNG BỐ với **nguồn số khớp nhau** (metrics của lượt chạy, rescore, và
`collect_reports`); hoàn thiện đường huấn luyện encoder (LoRA) cùng curve train/val, loss chống lệch,
và ghi nhận MLflow (một phép đo = một run).

## 2. Trạng thái

xong (trừ A-6 để cuối). Nhóm 0; A-1..A-5; B; C; D; E; F; G; H đều xong.

- Nhánh: `experiment` (= `origin/experiment`). Mỗi mục xong = một commit.
- Cả 12 notebook ghim `1954681`; gói bàn giao **008** đã dựng (việc còn lại: GỬI gói 008).
- Thời điểm dừng đợt: CI sạch, test 806 OK (skipped=2).
- Còn lại: **A-6** (dọn run MLflow rỗng/treo `cd0cd000...`) - chỉ làm khi chạy notebook trên Colab
  (cần mạng + token DagsHub): `python scripts/reset_experiment.py --dry-run` rồi `--run <runName|run_id>`.
  Việc cần mạng tương tự: `python scripts/log_reference_run.py` (ghi run tham chiếu công bố).

## 3. Task nhỏ (mỗi mục xong = một commit)

### Nhóm 0 - Sửa docs lệch code

- [x] **0-1** `scripts/ci_checks.py`: docstring ghi "CHÍN KIỂM TRA" nhưng chỉ liệt kê 8 mục; thêm mục thứ
  9 ("tài liệu trỏ đường dẫn mã nguồn") cho khớp `src/workflow/checks.py` và
  [../00_workflow/03_ci.md](../00_workflow/03_ci.md).
- [x] **0-2** [../05_config/02_pipeline.md](../05_config/02_pipeline.md): bỏ ví dụ `steps.normalize.teencode`
  (khoá không tồn tại trong `configs/pipeline/*.yaml`, trái chủ trương "pipeline không có công tắc teencode").
- [x] **0-3** [../00_workflow/02_rules.md](../00_workflow/02_rules.md) luật 20: thêm `eval_lock.json` vào
  danh sách file PHẢI commit (khớp `03_ci.md` check 1, `paths.yaml`, `.gitignore`, `changelog.md`).
- [x] **0-4** [../05_config/03_datasets.md](../05_config/03_datasets.md): ví dụ dùng `version: "0.3.0"`
  (thiếu tiền tố `v`) trong khi file thật là `vX.Y.Z`; sửa cho nhất quán.
- [x] **0-5** [../../README.md](../../README.md) mục quy ước: nói rõ **4 `run_*.py`** (`run_eda`,
  `run_pipeline`, `run_token_stats`, `run_check_examples`) + `build_report.py` = **5 file**.
- [x] **0-6** (phát hiện khi chạy test) `tests/workflow/test_build_package.py::zip_names`: glob `*002*.zip`
  khớp NHẦM vì dấu ngày `%y%m%d` cũng chứa "002" (ngày 261002) -> 2 test DeltaTest đỏ. Lỗi CÓ SẴN, phụ
  thuộc ngày, KHÔNG do thay đổi của đợt này. Sửa: khoá glob thành `SentimentX-goi-<số>-*.zip` (siết chặt).

### Nhóm A - Sửa lỗi đang chặn đường LoRA (ưu tiên tuyệt đối)

- [x] **A-1** Fix `KeyError: 'every_n_steps'` (lượt ViSoBERT).
  - Nguyên nhân: `src/experiments/encoder_run.py` trả `"training": found`, mà `found = lora.settings(...)`
    KHÔNG có khoá checkpoint; `log_config` đọc `plan_data["training"]["every_n_steps"]` -> KeyError.
  - Sửa: `"training": {**found, **checkpoints.settings(config_data)}` (giữ mọi khoá lora + thêm khoá checkpoint).
  - Test: chốt `plan()["training"]` có `every_n_steps`, và `log_config` không ném.
- [x] **A-2** Fix "PhoBERT báo thiếu model VnCoreNLP dù đã có trên Drive".
  - Nguyên nhân: `src/core/config.py` tính HẰNG đường dẫn NGAY LÚC IMPORT; trên Colab
    `SENTIMENTX_DATA_ROOT` chưa được đặt khi `src.api` -> `config` được import nên hằng bị "đóng băng"
    vào repo `data/models`, không phải Drive.
  - Sửa: bỏ kiểu "hằng đường dẫn đóng băng"; dùng `paths.*` TẠI CHỖ GỌI; `vncorenlp.MODEL_DIR` tính LÚC GỌI.
  - Test: đặt `SENTIMENTX_DATA_ROOT` vẫn cho đường dẫn đúng; `vncorenlp` không dùng giá trị đóng băng.
- [x] **A-3** Hint VnCoreNLP theo MÔI TRƯỜNG: Colab -> "Restart session rồi Run all (ô bootstrap tự tải)
  hoặc chép `data/models/vncorenlp/` từ gói bàn giao"; local -> giữ hướng dẫn `.ps1`.
  Test: `available()` cho hai môi trường.
- [x] **A-4** Lượt chạy encoder lỗi KHÔNG ngắt phiên Colab (tốn quota): `encoder_run.run` thiếu
  `runtime.end_session_on_error()`, nay bọc như đường prompt. Test: chốt lỗi đường encoder gọi `unassign`.
- [x] **A-5** Ghim lại notebook LoRA + chạy lại. ĐÃ PUSH nhánh `experiment`; `visobert/lora/exp001` ghim
  `ffa19f1`, `phobert-base-v2/lora/exp001` ghim `c56d20e9`. Kết quả cũ `91f50523`/`6aaa0f2f` không dùng nữa.
- [ ] **A-6** Dọn run MLflow rỗng/treo `cd0cd000...`. ĐỂ CUỐI: chỉ làm khi chạy notebook trên Colab
  (lúc đó mới có mạng + token DagsHub). Cách làm: `python scripts/reset_experiment.py --dry-run` rồi
  `--run <runName|run_id>`.

### Nhóm B - Đồng bộ nguồn số (collect_reports phải khớp mọi nguồn)

Mục tiêu: không xảy ra "lượt chạy đo một đằng, rescore đo một nẻo, collect_reports lấy một nẻo".

Bảng NGUỒN SỐ DUY NHẤT:

| Con số | Nguồn duy nhất | Ai đọc |
| --- | --- | --- |
| Đo của dự án trên test (all) | `metrics.json::scores` + `metrics.csv` (basis=`all`) | HTML lượt chạy, MLflow (không tiền tố) |
| Để SO CÔNG BỐ (paper) | `metrics.json::scores_paper` + `metrics.csv` (basis=`paper`) | `metrics_matrix` (cột `reference`), MLflow (`paper.`), `mispredictions_paper.csv` |
| Đo THÊM (rescore) | `metrics_rescored.json` / `metrics_rescored.csv` | `metrics_matrix` (họ cột `(rescored)` khi có) |
| Chọn best / early-stop (val) | `training_history.csv` + `metrics.json` (khối training) | người/MLflow; KHÔNG vào `metrics_matrix` |
| Curve train/val | `training_history.csv` + `plots/training.html` | người/MLflow step-metric |

- [x] **B-1** Ghi bảng nguồn số trên vào [../04_experiments/metrics.md](../04_experiments/metrics.md)
  + [../04_experiments/reference_publication.md](../04_experiments/reference_publication.md).
- [x] **B-2** `src/reporting/reports.py::metric_map` đọc thêm `metrics_rescored.csv` (giữ cột `basis`);
  KHÔNG trộn nguồn theo từng ô.
- [x] **B-3** Hiển thị HAI HỌ CỘT có nhãn `(gốc)` / `(rescored)` cho mỗi lượt (chỉ khi lượt đó có
  rescored). Nhãn phải KHÁC nhau (đã có test chống trùng nhãn).
- [x] **B-4** Giữ `metrics.json::scores_paper` + `metrics.csv(basis=paper)` là nguồn so công bố;
  `reference` vẫn lấy từ `data/reference_publication/`.
- [x] **B-5** KHÔNG đưa chỉ số chọn-best (val) vào `metrics_matrix`.
- [x] **B-6** Test `tests/reporting/test_reports.py` cho hai họ cột + nguồn.

### Nhóm C - Engine đo chung + rescore (tách train/đo)

- [x] **C-1** `lora.measure()` -> **val đi qua `Samples`** (đủ P/R/F1/detection/exact như test). CHỈ đường
  encoder (prompt không train nên không có `measure()`; đường prompt ĐÃ dùng `Samples` cho split chấm điểm).
- [x] **C-2** Rescore CHỈ THÊM (bỏ hoàn toàn "thay số"): `metrics_rescored.json/.csv` (pattern mới ở
  `configs/paths.yaml`), khối `rescored` (thời điểm/lý do/danh sách chỉ số THÊM), KHÔNG ghi đè bản gốc.
  Áp dụng CẢ encoder LẪN prompt (đọc `predictions.csv`).
- [x] **C-3** Test BẤT ĐỐI XỨNG (P ≠ R ≠ F1) cho mọi thay đổi hàm chấm điểm.

### Nhóm D - Early stop + biểu đồ train/val

- [x] **D-1** `early_stop: {enabled, patience, min_delta}` ở `configs/experiments/training.yaml`; `metric`
  dùng chung `checkpoints.best_metric`; guard danh sách hợp lệ; in + log `[STEP] dừng sớm`; CHỈ LoRA
  (prompt bỏ qua). + test.
- [x] **D-2** `checkpoints.best_metric` = `sentiment_f1` (macro-F1 sắc thái) + LUÔN ghi kèm P/R.
- [x] **D-3** `measure()` thêm `val_loss` + P/R/F1 + detection F1 (dùng `Samples`).
- [x] **D-4** `training_history.csv` (pattern mới), entry CUỐI MỖI EPOCH: train_loss TB, val_loss, P/R/F1.
- [x] **D-5** `plots/training.html` bằng plotly + jinja2 (`src/reporting/render.py` + `templates/`); thêm
  kind `line` vào `src/reporting/charts.py`; vẽ P/R/F1 + loss train/val. (Lưu ý: bản `check_last_plan.md`
  cũ để `[ ]` mục này do lệch trạng thái; bản chi tiết và mã nguồn đã XONG.)
- [x] **D-6** Log step-metric lên MLflow (để MLflow tự vẽ curve) + gửi CSV artifact; Drive có cả CSV lẫn
  HTML (HTML không lên MLflow).

### Nhóm E - Loss chống lệch (làm ngay)

- [x] **E-1** `loss` config-driven: `weighted_ce(class_weight: inverse)` cho encoder (focal/trọng số khía
  cạnh để SAU).
- [x] **E-2** Ghi rõ: đổi loss -> `config_sha256` đổi -> thư mục kết quả MỚI (không ghi đè).

### Nhóm F - MLflow

- [x] **F-1** Thêm `run.log` + `training_history.csv` vào `configs/experiments/tracking.yaml::artifacts`.
- [x] **F-2** Params bị cắt 500: SỐ PHẲNG -> metric (`read_rate.% đọc được`, `cost.giây`, `cost.số bước`);
  CẤU TRÚC LỚN -> artifact JSON (`read_rate` phân bố lý do, `model_info`, `subset`). + test.
- [x] **F-3** Log `scores_paper` với tiền tố `paper.` + tạo 1 run tham chiếu công bố; giữ `metrics_matrix`.
  (`scripts/log_reference_run.py` ghi run tham chiếu; chạy tay khi có mạng.)
- [x] **F-4** A8: `run_id` vào `run_meta.json` (sửa CÙNG dict `record`; carry `tracking` qua `previous`),
  GỬI PARAMS Ở `begin()`, LOG TĂNG DẦN, NỐI RUN khi resume (`mlflow.start_run(run_id=...)`), ánh xạ
  N attempt : 1 result dir : 1 run. Chốt: cùng result dir chạy 2 máy => cùng run (env ghi theo attempt).
  + test.
  > **Sửa kèm (02/10/2026):** `session.run_id()` được gọi vô điều kiện trong
  > `src/experiments/experiment_run.py` và `src/experiments/encoder_run.py`, nhưng chỉ phiên MLflow mới
  > có phương thức này. Phiên TẮT (tracker `none`/`local_json`/MLflow lỗi) trả về `Session` nền -> ném
  > `AttributeError` giữa lúc chạy. Đã thêm `run_id()` trả `""` vào `src/tracking/base.py::Session`
  > (đúng luật "ghi nhận không làm chết lần chạy") + ca test CI-visible `SessionRunIdTest`.

### Nhóm G - Lưu vết, docs, test, hạ tầng

- [x] **G-1** [../04_experiments/04_backlog.md](../04_experiments/04_backlog.md): Optuna (hoãn một nhịp),
  focal/trọng số khía cạnh (sau `weighted_ce` + bằng chứng curve).
- [x] **G-2** [../04_experiments/07_evolution.md](../04_experiments/07_evolution.md) - file MỚI, TRỐNG chờ
  ghi dần; đăng ký [../README.md](../README.md).
- [x] **G-3** Ghi chú A7: ma trận nhầm ở artifact/report, không lên MLflow.
- [x] **G-4** Docs kèm: `06_lora_encoder.md`, `05_experiments_shared.md`, `01_paths.md`, `metrics.md`,
  `05_predictions.md`, `P7_rerun.md`.
- [x] **G-5** Tests: `tests/training/test_training.py`, `tests/training/test_tracking.py`,
  `tests/evaluation/test_scorers.py`, `tests/evaluation/test_rescore.py`,
  `tests/evaluation/test_asymmetric.py`, `tests/reporting/test_reports.py`, `tests/reporting/test_curves.py`,
  `tests/core/test_paths.py`, `tests/preprocessing/test_segmenters.py`.
- [x] **G-6** Hạ tầng: `configs/paths.yaml` (pattern `training_history`, `metrics_rescored_*`),
  `configs/experiments/tracking.yaml` (`run.log`, `training_history.csv`),
  `configs/experiments/training.yaml` (`early_stop`, `loss`, `checkpoints.best_metric`),
  `src/experiments/experiments.py` (whitelist khoá mới).
- [x] **G-7** Sau mỗi nhóm: `python scripts/ci_checks.py` + `python -m unittest discover -s tests`.

### Nhóm H - Chốt thiết kế (ghi docs, không code riêng)

- [x] **H-1** So công bố = `paper.accuracy`; chọn best/early-stop = `sentiment_f1` (kèm P/R trong
  CSV/HTML); theo dõi `detection_f1`. Ghi ở `07_evolution.md` + `metrics.md`.
- [x] **H-2** Chọn best (all, val) KHÁC so công bố (paper, test) - không đem số `all` đi so công bố.
- [x] **H-3** Rescore = **đo THÊM**, không ghi đè; hiển thị hai họ cột `(gốc)`/`(rescored)`.
- [x] **H-4** Optuna: hoãn một nhịp.
- [x] **H-5** Giữ bất biến cũ: `test` không bị sửa; không bỏ dấu; teencode chỉ đo; `eval_lock`.
- [x] **H-6** A8: 1 result dir <-> 1 run; nhiều attempt nối cùng run; 2 máy cùng dir => cùng run.
- [x] **H-7** "Engine đo chung" hoàn thiện cho encoder; CẢ HAI đường dùng chung ở rescore.

## 4. Quy ước thực thi (bắt buộc)

1. Commit sau mỗi mục đã xong, theo Conventional Commits tiếng Anh
   ([../00_workflow/05_git_commits.md](../00_workflow/05_git_commits.md)).
2. Sau mỗi nhóm: `python scripts/ci_checks.py` + `python -m unittest discover -s tests`
   (Windows: `$env:PYTHONUTF8=1`).
3. Lỗi không fix được / quá khó -> quay lui (git) và xem xét lại kế hoạch.
4. Giữ bất biến dự án: không hardcode đường dẫn (dùng `configs/paths.yaml`); không đặt mặc định trong
   code (thiếu khoá là lỗi); notebook đã ghim KHÔNG sửa (muốn hiệu lực thì ghim mới).
5. **CI phải XANH trước khi ghim.** Sau khi `git push`, đợi CI GitHub của commit đó chạy xong và báo
   XANH rồi mới ghim lại notebook / dựng-gửi gói. CI đỏ thì sửa rồi push tiếp, **KHÔNG** ghim từ bản đỏ.
   Xem [../00_workflow/02_rules.md](../00_workflow/02_rules.md) luật 22.

## 5. Mặc định đã chốt cho file mới

- `metrics_rescored.csv` + `training_history.csv`: git theo dõi (file nhẹ) + đẩy MLflow (artifact).
- `plots/training.html`: KHÔNG vào git (`plots/` bị `.gitignore`) và KHÔNG lên MLflow.

## 6. Giai đoạn phát hành lại (02/10/2026) - sửa CI rồi mới ghim và dựng gói

**Lý do:** bản `2f8c362` (và các commit cùng đợt) bị **CI đỏ**: `src/experiments/encoder_run.py` import
`src/reporting/curves` ở **cấp module**, mà `curves` kéo `jinja2` (qua `render`), còn CI chỉ cài `pandas`,
`numpy`, `PyYAML` - vi phạm luật đã ghi trong `requirements-ci.txt`.

- [x] **R1** Sửa lỗi CI + bảo đảm chạy được trên Colab:
  - `src/reporting/curves.py`: bỏ import `render` ở cấp module (import trong hàm); thêm `available()`;
    `write_html` **best-effort** (thiếu `plotly`/`jinja2` thì trả `None` + cảnh báo, KHÔNG ném).
  - `src/experiments/encoder_run.py`: import `curves` **trong hàm** ở bước ghi biểu đồ.
  - `tests/reporting/test_curves.py`: `skipUnless` có `plotly`+`jinja2`, import nặng trong `setUp`.
  - `tests/core/test_imports.py` (MỚI): import các module CI dùng trong **tiến trình con** rồi khẳng định
    `plotly`/`jinja2`/`torch`/... **không** bị kéo vào cấp module.
  - `src/workflow/bootstrap.py`: `WANTED_PACKAGES` thêm `plotly`, `jinja2` (notebook tự cài).
  - `requirements-colab.txt`: bỏ chú thích `plotly`, `jinja2`.
  - Docs: `06_conventions.md` (mục "Import trong `src/`"), `06_lora_encoder.md` (biểu đồ best-effort),
    `P7_rerun.md` (gói 007 không dùng).
- [x] **R2** Commit + **PUSH** bản sửa; CI GitHub **xanh** ở commit `1954681`.
- [x] **R3** Ghim lại CẢ 12 notebook vào `1954681` -> commit `74fc846` + push. Đã xác nhận 12/12 cùng sha.
- [x] **R4** Dựng **gói 008** (`handover/out/SentimentX-goi-008-74fc846-261002.zip`, 12 notebook đã đổi) ->
  commit sổ gói -> push. **KHÔNG gửi gói 007.** Việc còn lại: GỬI gói 008 cho người nhận.

**Ghi chú:** gói 007 (`handover/out/SentimentX-goi-007-c01fba0-261002.zip`) đã dựng bằng bản CI đỏ, nên bị
thay bằng gói 008; sổ gói vẫn giữ dấu vết của 007 (lịch sử gửi).
