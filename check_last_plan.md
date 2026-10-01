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
- [!] A-5 ghim lại notebook LoRA + P7_rerun.md (CHẶN: cần push GitHub)
- [!] A-6 dọn run MLflow rỗng (CHẶN: cần mạng + token)

## Nhóm B - đồng bộ nguồn số
- [ ] B-1 docs bảng nguồn số duy nhất
- [ ] B-2 metric_map đọc metrics_rescored (không trộn ô)
- [ ] B-3 hai họ cột (gốc)/(rescored)
- [ ] B-4 giữ paper = nguồn so công bố
- [ ] B-5 không đưa chọn-best vào metrics_matrix
- [ ] B-6 test reports hai họ cột

## Nhóm C - engine đo chung + rescore
- [ ] C-1 lora.measure -> Samples (val, chỉ encoder)
- [ ] C-2 rescore CHỈ THÊM metrics_rescored.* (cả prompt)
- [ ] C-3 test bất đối xứng

## Nhóm D - early stop + curve
- [ ] D-1 early_stop config (sentiment_f1_macro, chỉ LoRA)
- [ ] D-2 checkpoints.best_metric = sentiment_f1_macro
- [ ] D-3 measure() thêm val_loss + P/R/F1
- [ ] D-4 training_history.csv (entry cuối epoch)
- [ ] D-5 plots/training.html (plotly + jinja2, kind line)
- [ ] D-6 log step-metric + CSV lên MLflow

## Nhóm E - loss chống lệch
- [ ] E-1 weighted_ce(class_weight: inverse)
- [ ] E-2 docs: đổi loss -> thư mục mới

## Nhóm F - MLflow
- [ ] F-1 run.log + training_history.csv vào artifacts
- [ ] F-2 params 500: số->metric, dict->artifact JSON
- [ ] F-3 log scores_paper prefix paper. + run tham chiếu
- [ ] F-4 A8: run_id vào run_meta, params ở begin, nối run khi resume

## Nhóm G - lưu vết/docs/test/hạ tầng
- [ ] G-1 04_backlog.md: Optuna, focal
- [ ] G-2 07_evolution.md (mới, trống) + đăng ký docs/README.md
- [ ] G-3 ghi chú A7 (ma trận ở artifact)
- [ ] G-4 docs kèm các nhóm
- [ ] G-5 cập nhật tests
- [ ] G-6 hạ tầng: paths.yaml / tracking.yaml / training.yaml / evaluation.yaml / .gitignore
- [ ] G-7 ci_checks.py + unittest sau mỗi nhóm

## Nhóm H - chốt thiết kế (ghi docs)
- [ ] H-1 .. H-7 ghi các chốt thiết kế

## Trạng thái tổng
- Đang ở: Nhóm 0 XONG (0-1..0-6). Tiếp theo: Nhóm A.
- CI: sạch. Test: 761 tests OK (skipped=2).
