# check_last_plan - trạng thái nhanh

> Chỉ gồm mã mục + trạng thái. Chi tiết ở `last_plan.md`. Sửa kế hoạch thì sửa CẢ HAI file.
> `[ ]` chưa làm · `[~]` đang dở · `[x]` xong · `[!]` chặn/quay lui

## Nhóm 0 - docs nhỏ
- [x] 0-1 ci_checks.py docstring 8 -> 9 mục
- [x] 0-2 02_pipeline.md bỏ ví dụ teencode
- [x] 0-3 02_rules.md luật 20 thêm eval_lock.json
- [x] 0-4 03_datasets.md ví dụ v0.3.0
- [x] 0-5 README.md 4 run_*.py + build_report.py = 5 file
- [x] 0-6 fix test build_package zip_names glob (lỗi có sẵn theo ngày)

## Nhóm A - sửa lỗi chặn LoRA
- [x] A-1 encoder_run.plan: training gộp checkpoints (fix KeyError every_n_steps)
- [x] A-2 config.py refactor + vncorenlp tính MODEL_DIR lúc gọi
- [x] A-3 hint VnCoreNLP theo môi trường
- [x] A-4 encoder_run.run thêm end_session_on_error
- [x] A-5 ghim lại notebook LoRA + P7_rerun.md (ĐÃ PUSH: visobert pin ffa19f1, phobert pin c56d20e9, cả hai trên origin/experiment)
- [ ] A-6 dọn run MLflow rỗng (ĐỂ CUỐI: làm khi chạy notebook trên Colab) - nay có tool: `scripts/reset_experiment.py`

## Nhóm B - đồng bộ nguồn số
- [x] B-1 docs bảng nguồn số duy nhất
- [x] B-2 metric_map đọc metrics_rescored (không trộn ô)
- [x] B-3 hai họ cột (gốc)/(rescored)
- [x] B-4 giữ paper = nguồn so công bố
- [x] B-5 không đưa chọn-best vào metrics_matrix
- [x] B-6 test reports hai họ cột

## Nhóm C - engine đo chung + rescore
- [x] C-1 lora.measure -> Samples (val, chỉ encoder)
- [x] C-2 rescore CHỈ THÊM metrics_rescored.* (cả prompt)
- [x] C-3 test bất đối xứng

## Nhóm D - early stop + curve
- [x] D-1 early_stop config (best_metric, chỉ LoRA)
- [x] D-2 checkpoints.best_metric = sentiment_f1
- [x] D-3 measure() thêm val_loss + P/R/F1
- [x] D-4 training_history.csv (entry cuối epoch)
- [ ] D-5 plots/training.html (plotly + jinja2, kind line)
- [x] D-6 log step-metric + CSV lên MLflow

## Nhóm E - loss chống lệch
- [x] E-1 weighted_ce(class_weight: inverse)
- [x] E-2 docs: đổi loss -> thư mục mới

## Nhóm F - MLflow
- [x] F-1 run.log + training_history.csv vào artifacts
- [x] F-2 params 500: số->metric, dict->artifact JSON
- [x] F-3 log scores_paper prefix paper. + run tham chiếu
- [x] F-4 A8: run_id vào run_meta, params ở begin, nối run khi resume

## Nhóm G - lưu vết/docs/test/hạ tầng
- [x] G-1 04_backlog.md: Optuna, focal
- [x] G-2 07_evolution.md (mới, trống) + đăng ký docs/README.md
- [x] G-3 ghi chú A7 (ma trận ở artifact)
- [x] G-4 docs kèm các nhóm
- [x] G-5 cập nhật tests
- [x] G-6 hạ tầng: paths.yaml / tracking.yaml / training.yaml / evaluation.yaml / .gitignore
- [x] G-7 ci_checks.py + unittest sau mỗi nhóm

## Nhóm H - chốt thiết kế (ghi docs)
- [x] H-1 .. H-7 ghi các chốt thiết kế (07_evolution.md + metrics.md)

## Trạng thái tổng
- XONG: Nhóm 0; A-1..A-5 (A-5 ĐÃ PUSH + ghim lại); B (B-1..B-6); C (C-1..C-3); D (D-1..D-6);
  E (E-1/E-2); F (F-1..F-4); G (G-1..G-7); H (H-1..H-7).
- CÒN LẠI: A-6 - ĐỂ CUỐI, chỉ làm khi chạy notebook trên Colab (cần mạng + token DagsHub).
  Việc tương tự cần mạng: `scripts/log_reference_run.py` (ghi run tham chiếu công bố) chạy tay khi online.
  Nay A-6 có tool riêng: `scripts/reset_experiment.py` (`--dry-run` trước, rồi `--run <runName|run_id>`).
- Ghim: CẢ 12 notebook -> `1954681` (commit CI XANH), đã push.
- Gói bàn giao: **gói 008** `handover/out/SentimentX-goi-008-74fc846-261002.zip` (12 notebook đổi, 36 file
  y nguyên). Gói 007 KHÔNG dùng (dựng từ bản CI đỏ). Việc còn lại: GỬI gói 008.
- CI: sạch (`CI_EXIT=0`). Test: 806 tests OK (skipped=2).

## Giai đoạn phát hành lại (sửa CI -> ghim -> gói 008)
- [x] R1 sửa CI (curves best-effort + import trong hàm; test_curves guard; test_imports mới;
  bootstrap plotly/jinja2; requirements-colab bỏ chú thích; docs)
- [x] R2 commit + PUSH bản sửa; CI GitHub XANH ở commit 1954681
- [x] R3 ghim lại CẢ 12 notebook vào 1954681 + push (commit 74fc846)
- [x] R4 dựng gói 008 + commit sổ + push (KHÔNG gửi gói 007). Còn lại: GỬI gói 008.
- Lý do: bản 2f8c362 đỏ CI vì encoder_run import src.reporting.curves ở cấp module -> jinja2.

