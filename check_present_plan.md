# check_present_plan — Trạng thái thực thi (đối chiếu với `present_plan.md`)

> Cách dùng: mỗi mục nhỏ trong `present_plan.md` có **một dòng** ở đây. Trạng thái dùng các nhãn:
> `CHƯA LÀM` · `ĐANG LÀM` · `XONG <ngày>` · `CHỜ NGƯỜI DÙNG` · `BỎ QUA <lí do>`.
> Mỗi lần làm xong một mục nhỏ thì sửa đúng dòng đó, ghi ngắn: đã làm gì, tệp nào, kết quả.

## Mục 1. Quy tắc bắt buộc của repo
- 1.1 Quy tắc commit — XONG 04/10/2026: đã đọc `docs/00_workflow/05_git_commits.md` (Conventional
  Commits tiếng Anh, một commit một task nhỏ, tách theo miền, không gộp fix với refactor).
- 1.2 `ci_checks` + `unittest` sau mỗi nhóm — XONG 04/10/2026: đã đọc `docs/06_plan/P8_measurement_mlflow.md` §4.
- 1.3 Lỗi khó → quay lui git — XONG 04/10/2026: đã đọc, ghi nhận nguyên văn "Lỗi không fix được / quá
  khó -> quay lui (git) và xem xét lại kế hoạch".
- 1.4 Bất biến dự án — XONG 04/10/2026: đã đọc `docs/00_workflow/02_rules.md` (luật 7, 8, 9, 10, 21).
- 1.5 CI xanh mới ghim/gửi gói — XONG 04/10/2026: luật 22 trong `02_rules.md`.
- 1.6 Ghi tệp không BOM — XONG 04/10/2026: ghi nhận từ cuộc trò chuyện, áp dụng từ đây.
- 1.7 Thay đổi kế hoạch phải được duyệt — XONG 04/10/2026: người dùng yêu cầu rõ trong tin nhắn.

## Mục 2. Dọn dẹp kết quả lỗi
- 2.1 Xoá 6 thư mục kết quả lỗi — XONG 04/10/2026: đã xoá đủ 6 thư mục `results/<hash8>` ở máy; kiểm lại
  `experiments/qwen3-0.6b/prompt-cot/exp001..003` nay chỉ còn `results` (trống), `config.yaml`,
  `notebook.ipynb`, `README.md`. Bằng chứng trước khi xoá (ảnh chụp `metrics.json`):
  | Thư mục | `metrics.model` | `repo_sha` | `% đọc được` | `paper.cells` |
  | --- | --- | --- | --- | --- |
  | `exp001/results/8db40559` | `Qwen/Qwen3-4B-Instruct-2507` | `88d12e68…` | 100,0 | 2580 |
  | `exp002/results/db6efb02` | `Qwen/Qwen3-4B-Instruct-2507` | `88d12e68…` | 99,94 | 2461 |
  | `exp003/results/30c9e674` | `Qwen/Qwen3-4B-Instruct-2507` | `88d12e68…` | 99,94 | 2520 |
  | `exp001/results/bc32904d` | `Qwen/Qwen3-0.6B` | `8bfe96e0…` | 3,33 | 31 |
  | `exp002/results/edc0797a` | `Qwen/Qwen3-0.6B` | `8bfe96e0…` | 1,36 | 19 |
  | `exp003/results/d5b8e7fc` | `Qwen/Qwen3-0.6B` | `8bfe96e0…` | 1,73 | 17 |
  Ghi chú: 3 dòng đầu là lượt **4B nạp nhầm** vào thư mục 0.6B (số ô trùng khít bộ 4B fp16 lô 4, ba
  thư mục này đều là `RESUME` trong cùng thư mục: 916 / 1280 / 1436 mẫu dùng lại); 3 dòng cuối là lượt
  **0.6B bật suy nghĩ** (`<think>` 999 / 714 / 788 lần, lí do lỗi "không thấy JSON nào" 1549 / 1561 /
  1536). `RESUME` trong cùng thư mục là hợp lệ theo luật 13 (`config_sha256`, `data.build`, `repo.sha`
  không đổi).
- 2.2 Drive đã xoá đủ 6 thư mục — CHỜ NGƯỜI DÙNG: người dùng xác nhận.
- 2.3 Kiểm toàn vẹn 17 thư mục còn lại — XONG 04/10/2026: quét `experiments/**/results/*` được **đúng 17**
  thư mục; **17/17** có đủ `run_meta.json`, `metrics.json`, `metrics.csv`; `% đọc được` thấp nhất 99,88
  (`exp004`, `exp010` — hai lượt chạy tiếp).
- 2.4 Danh mục 17 lượt — XONG 04/10/2026: bảng dưới đây (dán vào `docs/04_experiments/08_experiment_rationale.md`
  ở mục 3.x):
  | # | Thí nghiệm | hash8 | model | lượng hoá | `% đọc được` | số ô | prompt / ví dụ | `repo_sha` | chế độ |
  | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
  | 1 | `phobert-base-v2/lora/exp001` | `363c224e` | `vinai/phobert-base-v2` | fp16 | 100,0 | 2665 | – | `aca047df` | NEW |
  | 2 | `phobert-base-v2/lora/exp002` | `61097598` | `vinai/phobert-base-v2` | fp16 | 100,0 | 2736 | – | `8bfe96e0` | NEW |
  | 3 | `visobert/lora/exp001` | `83dff5ee` | `uitnlp/visobert` | fp16 | 100,0 | 2688 | – | `aca047df` | NEW |
  | 4 | `visobert/lora/exp002` | `384b271d` | `uitnlp/visobert` | fp16 | 100,0 | 2701 | – | `8bfe96e0` | NEW |
  | 5 | `qwen3-4b/…/exp002` | `8d2a31b4` | `Qwen/Qwen3-4B-Instruct-2507` | 4-bit | 100,0 | 2415 | `absa_cot_zeroshot_v1` | `88d12e68` | NEW |
  | 6 | `qwen3-4b/…/exp003` | `4553090a` | `Qwen/Qwen3-4B-Instruct-2507` | 4-bit | 100,0 | 2315 | `absa_cot_1shot_v1` | `88d12e68` | NEW |
  | 7 | `qwen3-4b/…/exp004` | `8b07affe` | `Qwen/Qwen3-4B-Instruct-2507` | 4-bit | 99,88 | 2378 | `absa_cot_5shot_v1` | `88d12e68` | **RESUME** |
  | 8 | `qwen3-4b/…/exp005` | `d4c5f94b` | `Qwen/Qwen3-4B-Instruct-2507` | fp16 | 100,0 | 2580 | `absa_cot_zeroshot_v1` | `88d12e68` | NEW |
  | 9 | `qwen3-4b/…/exp006` | `43aeb425` | `Qwen/Qwen3-4B-Instruct-2507` | fp16 | 99,94 | 2461 | `absa_cot_1shot_v1` | `88d12e68` | NEW |
  | 10 | `qwen3-4b/…/exp007` | `1d3e96c4` | `Qwen/Qwen3-4B-Instruct-2507` | fp16 | 99,94 | 2520 | `absa_cot_5shot_v1` | `88d12e68` | NEW |
  | 11 | `qwen3-4b/…/exp008` | `d2ef77a9` | `Qwen/Qwen3-4B-Instruct-2507` | 4-bit | 100,0 | 2414 | `absa_cot_zeroshot_v1` | `8bfe96e0` | NEW |
  | 12 | `qwen3-4b/…/exp009` | `7cf3331e` | `Qwen/Qwen3-4B-Instruct-2507` | 4-bit | 100,0 | 2324 | `absa_cot_1shot_v1` | `8bfe96e0` | NEW |
  | 13 | `qwen3-4b/…/exp010` | `7011d28f` | `Qwen/Qwen3-4B-Instruct-2507` | 4-bit | 99,88 | 2375 | `absa_cot_5shot_v1` | `8bfe96e0` | **RESUME** |
  | 14 | `qwen3-4b/…/exp011` | `3c5cf0a0` | `Qwen/Qwen3-4B-Instruct-2507` | 4-bit | 100,0 | 2359 | `absa_cot_1shot_v2` | `8bfe96e0` | NEW |
  | 15 | `qwen3-4b/…/exp012` | `33c2d270` | `Qwen/Qwen3-4B-Instruct-2507` | 4-bit | 100,0 | 2305 | `absa_cot_1shot_v3` | `8bfe96e0` | NEW |
  | 16 | `qwen3-4b/…/exp013` | `779e8738` | `Qwen/Qwen3-4B-Instruct-2507` | 4-bit | 100,0 | 1972 | `absa_cot_1shot_v4` | `8bfe96e0` | NEW |
  | 17 | `qwen3-4b/…/prompt-one-turn/exp001` | `63c3bf0a` | `Qwen/Qwen3-4B-Instruct-2507` | 4-bit | 100,0 | 2663 | `absa_one_turn_v1` | `88d12e68` | NEW |
  (`qwen3-4b/…` = `qwen3-4b-instruct-2507/prompt-cot`; dòng 17 là `prompt-one-turn`.)

## Mục 3. Sinh lại bảng số 17 lượt và viết lại kết luận
- 3.1 Chạy `collect_reports.py`, kiểm `attempt_registry` 17 dòng — CHƯA LÀM.
- 3.2 Đối chiếu từng ô với `scores_paper`; kiểm `mispredictions_paper.csv` — CHƯA LÀM.
- 3.3 Viết lại mục lượng hoá — CHƯA LÀM.
- 3.4 Viết lại mục ba biến thể prompt (kết quả âm) — CHƯA LÀM.
- 3.5 Viết lại mục encoder + sửa câu sai về PhoBERT — CHƯA LÀM.
- 3.6 Thêm mục `price` là điểm mù chung + câu về nhiễu so công bố — CHƯA LÀM.
- 3.7 Cập nhật cây thí nghiệm (3 tệp) — CHƯA LÀM.
- 3.8 Cập nhật `presentations/experiment_rationale.md`, `result_analysis.md` — CHƯA LÀM.
- 3.9 `metrics.md`: 5 luật đo + quyết định biểu quyết 3 mẫu — CHƯA LÀM.
- 3.10 Sửa bảng thời gian (4 tệp) + đánh dấu lượt CHẠY TIẾP + xoá giả thuyết sai — CHƯA LÀM.
- 3.11 Quét số liệu cũ ("chín lượt", "12 notebook", "12 thí nghiệm") — CHƯA LÀM.
- 3.12 Ghi chú `02_model_input.md` không sửa đợt này — CHƯA LÀM.
- 3.13 Rà chỗ nhắc cờ `--exclude` lỗi thời — CHƯA LÀM.
- 3.14 `04_backlog.md`: đóng §10.2/10.3/10.4, sửa §10.1, thêm 3 mục mới — CHƯA LÀM.
- 3.15 `ci_checks` + `unittest` + commit + push ⇒ **MỐC DỪNG #1** — CHƯA LÀM.

## Mục 4. Mã và cấu hình mới
- 4.1 Khoá `preprocess.enable_thinking` — CHƯA LÀM.
- 4.2 `generation.max_new_tokens` đọc từ cấu hình thí nghiệm — CHƯA LÀM.
- 4.3 Cửa chặn `% đọc được < 95%` ⇒ `valid: false` — CHƯA LÀM.
- 4.4 Luật "một cơ chế, hai khoá không tách rời" vào `05_config/02_rules.md` — CHƯA LÀM.
- 4.5 Đường encoder xuất xác suất từng ô — CHƯA LÀM.
- 4.6 `scripts/fit_thresholds.py` — CHƯA LÀM.
- 4.7 `scripts/ensemble.py` — CHƯA LÀM.
- 4.8 `scripts/fuse.py` — CHƯA LÀM.
- 4.9 `scripts/vote.py` (3 mẫu; hoà → seed nhỏ nhất) — CHƯA LÀM.
- 4.10 `data/reports/fusion/` + `docs/04_experiments/09_fusion.md` — CHƯA LÀM.
- 4.11 Năm cấu hình model mới — CHƯA LÀM.
- 4.12 Năm model vào `token_stats.MODELS` + đo lại bảng token + `model_input.csv` 228 → 513 — CHƯA LÀM.
- 4.13 `ci_checks` + `unittest` + commit mã/cấu hình — CHƯA LÀM.

## Mục 5. Tạo thí nghiệm và tài liệu cho các đợt
- 5.1 Cấu hình + README cho 17 thí nghiệm đợt 7 (quy ước `parent`) — CHƯA LÀM.
- 5.2 Cấu hình + README cho 9 thí nghiệm đợt 8 — CHƯA LÀM.
- 5.3 Cấu hình + README cho 3 thí nghiệm đợt 9 — CHƯA LÀM.
- 5.4 `docs/06_plan/P8_batch7.md` — CHƯA LÀM.
- 5.5 `handover/README.md` (bảng 17 notebook) — CHƯA LÀM.
- 5.6 `ci_checks` + `unittest` + commit — CHƯA LÀM.

## Mục 6. Ghim notebook và dựng gói 012
- 6.1 Push, đợi CI xanh, ghim 17 notebook — CHƯA LÀM.
- 6.2 Dựng gói 012 ⇒ **MỐC DỪNG #2** — CHƯA LÀM.

## Mục 7. Người dùng chạy đợt 7
- 7.1 Giải nén gói 012 lên Drive — CHỜ NGƯỜI DÙNG.
- 7.2 Chạy theo thứ tự 7 nhóm — CHỜ NGƯỜI DÙNG.
- 7.3 Điều kiện mỗi lượt (`% đọc được ≥ 95%`, DÒ ghi p50/p95/max) — CHỜ NGƯỜI DÙNG.
- 7.4 Gửi 6 tệp nhẹ + tệp xác suất + thời gian thực tế — CHỜ NGƯỜI DÙNG.

## Mục 8. Xử lý đợt 7 và chốt luật
- 8.1 `collect_reports.py` + đối chiếu từng ô — CHƯA LÀM.
- 8.2 Chốt trần token từ lượt DÒ — CHƯA LÀM.
- 8.3 Đọc kết quả ba lượt về giá (`exp014`, `exp015`, `exp016`) — CHƯA LÀM.
- 8.4 Dò ngưỡng theo khía cạnh trên `val` ⇒ tệp luật JSON — CHƯA LÀM.
- 8.5 Chốt bảng luật lai trên `val` ⇒ tệp luật JSON — CHƯA LÀM.
- 8.6 Viết kết luận nhóm A, B, encoder mới, ba lượt giá — CHƯA LÀM.
- 8.7 Hai thí nghiệm `test` có ngưỡng ⇒ ghim ⇒ gói 013 ⇒ **MỐC DỪNG #3** — CHƯA LÀM.

## Mục 9. Người dùng chạy đợt 8
- 9.1 Luật chống chạm trần token — CHỜ NGƯỜI DÙNG.
- 9.2 Hai lượt `test` có ngưỡng — CHỜ NGƯỜI DÙNG.
- 9.3 Nhánh suy nghĩ đầy đủ (0.6B) — CHỜ NGƯỜI DÙNG.
- 9.4 Bốn lượt lấy mẫu — CHỜ NGƯỜI DÙNG.

## Mục 10. Xử lý đợt 8
- 10.1 `collect_reports.py` + đối chiếu từng ô — CHƯA LÀM.
- 10.2 Báo cáo ngưỡng — CHƯA LÀM.
- 10.3 Báo cáo ensemble + lai — CHƯA LÀM.
- 10.4 Báo cáo biểu quyết + tương tác lượng hoá × lấy mẫu — CHƯA LÀM.
- 10.5 Cập nhật tài liệu, đóng backlog, gói 014 ⇒ **MỐC DỪNG #4** — CHƯA LÀM.

## Mục 11. Danh mục thí nghiệm theo đợt
- 11.1 Đã chạy xong (đối chiếu) — XONG 04/10/2026: ghi danh mục trong `present_plan.md`; số liệu thật sẽ
  đối chiếu ở mục 3.1/3.2.
- 11.2 Đợt 7 (17 lượt) — CHƯA LÀM: danh mục đã ghi, chờ tạo cấu hình ở mục 5.1.
- 11.3 Đợt 8 (9 lượt) — CHƯA LÀM.
- 11.4 Đợt 9 (3 lượt) — CHƯA LÀM.

## Mục 12. Việc để ngỏ
- 12.1 Danh sách việc mở — CHƯA LÀM: đã ghi danh sách trong `present_plan.md`.
- 12.2 MLflow (đã mất, không khôi phục) — XONG 04/10/2026: ghi nhận quyết định "kệ MLflow" của người dùng;
  không backfill.

## Mục 13. Điều còn chờ người dùng trả lời
- 13.1 Giữ `xlm-roberta-base` làm đối chứng — CHỜ NGƯỜI DÙNG (mặc định: GIỮ).
- 13.2 Commit đầu vào cho bước kết hợp vào `data/reports/fusion/inputs/` — CHỜ NGƯỜI DÙNG (mặc định: CÓ).
- 13.3 Cửa `% đọc được ≥ 95%` chỉ đánh dấu, không xoá dữ liệu — CHỜ NGƯỜI DÙNG (mặc định: 95%, có đánh dấu).

<!-- DIEM-NOI-TIEP -->




