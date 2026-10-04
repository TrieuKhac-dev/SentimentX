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
- 3.1 Chạy `collect_reports.py`, kiểm `attempt_registry` 17 dòng — XONG 04/10/2026: `--dry-run` và chạy
  thật đều báo **17 lượt, tất cả FINISHED**; kết quả: `dataset_registry` 2 dòng, `experiment_registry`
  17 dòng, `attempt_registry` **17 dòng**, `model_input` **228 dòng**, `metrics_matrix` 22 dòng
  (`accuracy_by_aspect.csv` 8 dòng, `prf_by_aspect_sentiment.csv` 14 dòng). 11 tệp báo cáo được ghi lại.
- 3.2 Đối chiếu từng ô với `scores_paper`; kiểm `mispredictions_paper.csv` — **XONG 04/10/2026, KẾT QUẢ
  PASS**: với từng lượt, khớp **đúng một** cột ở cả hai bảng (khớp theo **giá trị**, không theo tên cột,
  nên bắt được cả lỗi gán nhãn cột); **không** cột nào bị hai lượt cùng khớp; ba cột công bố
  (`COT+0-shot`, `COT+1-shot`, `COT+5-shot`) **không** khớp lượt nào (đúng như phải thế); **17/17** lượt
  có `mispredictions_paper.csv` = `cells − correct`; dòng `aspect_detection` của bảng accuracy khớp
  **17/17** với `scores.aggregate.detection.micro.accuracy`. Ghi chú: `by_aspect` và
  `when_mentioned_by_aspect` của 17 lượt này **trùng nhau** vì các lượt đều trả lời được mọi ô.
- 3.3 Viết lại mục lượng hoá — **XONG 04/10/2026**: §3 của `08_experiment_rationale.md` (ba cấu hình sinh;
  nhóm lô 4 sạch MỘT biến; delta **0,64 / 1,17 / 0,71 điểm**; số ô 2.414/2.324/2.375 so với 2.580/2.461/2.520;
  "một phần lợi thế đến từ việc kiêng trả lời"), §3 của cây `07_evolution.md`, và §1.1 + §4.4 của
  `presentations/result_analysis.md` (bảng ba cấu hình × ba mức ví dụ đã viết lại toàn bộ).
- 3.4 Viết lại mục ba biến thể prompt (kết quả âm) — **XONG 04/10/2026**: **§3b** ở
  `08_experiment_rationale.md` (exp011 −0,09 / exp012 −1,20 / exp013 −5,06; F1 `price` âm 0,308 / 0,600 /
  0,167; mất 343 ô ở exp013), ba nút trong cây `07_evolution.md`, và §2.2 + §4.5 của
  `presentations/result_analysis.md`.
- 3.5 Viết lại mục encoder + sửa câu sai về PhoBERT — **XONG 04/10/2026**: §2 `08_experiment_rationale.md`, hai
  nút cây `07_evolution.md`, §1.2/§2.2/§2.3/§3/§4.6/§4.7 của `presentations/result_analysis.md`,
  `docs/04_experiments/06_lora_encoder.md` (bảng "Kết quả hai hàm mất mát" 4 lượt + 3 điều đọc kèm + sửa con
  số `price` sai), `docs/04_experiments/01_models.md` (trạng thái 4 model, cảnh báo `enable_thinking`, bỏ câu
  sai về PhoBERT). Số đã kiểm: PhoBERT 88,40 → 96,62 (F1 âm 0,540 → 0,876); ViSoBERT 94,86 → 95,61 (0,765 →
  0,836); **đảo thứ hạng**; `weighted_ce` **hạ phát hiện khía cạnh** 98,05 → 94,14 và 98,29 → 97,06.
- 3.6 Thêm mục `price` là điểm mù chung + câu về nhiễu so công bố — **XONG 04/10/2026**: **§7** ở
  `08_experiment_rationale.md`, §6.3/§6.4 mới, §2.1/§2.2 của `presentations/result_analysis.md`, và **§4.9** +
  §5 của `result_analysis.md`; cỡ mẫu lớp âm `price` = **train 15 / val 0 / test 6** (kiểm cả dữ liệu GỐC
  `data/raw/cosmetics/v0.1.0/eda/02_label_aspect_distribution.csv`).
  **Người dùng đã duyệt 04/10/2026** (xem mục 8.4): `price` không có ngưỡng; đọc bằng đếm + danh sách 6 ô;
  tập chẩn đoán giá đưa vào backlog (sẽ ghi ở mục 3.14).
- 3.7 Cập nhật cây thí nghiệm (3 tệp) — **XONG 04/10/2026**: `07_evolution.md` (đã xong ở mục 3.3),
  `presentations/experiment_tree.md` (mermaid 17 nút/5 nhánh A-B-E-F-G + bảng "Năm nhánh"), và
  `presentations/experiment_tree.drawio` **viết lại từ đầu** (26 nút, 20 cạnh, không trùng id; đã kiểm bằng
  `xml.etree.ElementTree`: **parse OK, mọi cạnh trỏ đúng id**). Bỏ nút D cũ, thêm nhóm E/F/G và các cặp
  sạch-một-biến (B2→B8, B5→B8, B6→B9, B7→B10).
- 3.8 Cập nhật `presentations/experiment_rationale.md`, `result_analysis.md` — **XONG 04/10/2026**:
  `experiment_rationale.md` viết lại (đầu tệp, "Bật học?", "Năm nhánh, mười bảy lượt", A/B/E/F/G, "Bốn điều
  phải nói"); `result_analysis.md` **viết lại toàn bộ** (§1 hai bảng accuracy, §2 ba bảng F1 theo lớp, §3
  phát hiện khía cạnh, §4 **chín** kết luận, §5 hạn chế, §6 mười việc tiếp theo).
  **Ghi chú dọn lỗi 04/10/2026 (kiểm tra chéo đợt 7):** hai mục 3.7/3.8 từng bị chép HAI lần trong tệp này
  (một bản `XONG` kèm bằng chứng ở đây, một bản `CHƯA LÀM` ở dưới) - bản `CHƯA LÀM` là bản cũ còn sót, đã xoá.
- 3.9 `metrics.md`: 5 luật đo + quyết định biểu quyết 3 mẫu — **XONG 04/10/2026**: thêm mục "Luật đo bắt buộc
  khi đọc số" (5 luật: đọc kèm số ô; cửa `% đọc được` 95%; token chạm trần ⇒ lượt bị cắt; ghi rõ cơ sở và
  kiểu trung bình; F1 theo tỉ lệ 0..1) + "Hai quyết định kèm theo" (biểu quyết **3 mẫu**; không dò ngưỡng
  cho khía cạnh có 0 ô âm trên `val`).
- 3.10 Sửa bảng thời gian (4 tệp) + đánh dấu lượt CHẠY TIẾP + xoá giả thuyết sai — **XONG 04/10/2026**:
  `handover/README.md` (17 notebook = số đo thật; `exp004`/`exp010` đánh dấu *lượt CHẠY TIẾP*),
  `docs/00_workflow/07_colab.md` (bảng đo thật cho cả 8 lượt còn lại + **xoá giả thuyết sai** "5 ví dụ sinh ít
  token", thay bằng nguyên nhân RESUME kèm số mẫu dùng lại 1.304 / 1.576), `docs/00_workflow/01_flow.md`
  (12 phút → 3 giờ 51, kèm cảnh báo hai lượt chạy tiếp), `docs/04_experiments/04_backlog.md` (dòng "thay thời
  gian ước tính" nay ghi **17 lượt**).
- 3.11 Quét số liệu cũ — **XONG 04/10/2026**: sửa các chỗ nói TRẠNG THÁI HIỆN TẠI
  (`10_template_notebook.md` 2 chỗ, `templates/README.md`, `06_plan/README.md` dòng P7,
  `08_experiment_rationale.md` "bốn lượt LoRA") và **giữ nguyên** các bản ghi LỊCH SỬ có ngày
  (`P7_rerun.md` §8, `P8_measurement_mlflow.md` R3/R4, `APPENDIX_commits.md`); chỗ nào vẫn cần đọc được theo
  hiện tại thì thêm dòng "Cập nhật 04/10/2026" (`01_dataset/changelog.md`, `P8` trạng thái).
- 3.12 Ghi chú `02_model_input.md` không sửa đợt này — **XONG 04/10/2026**: thêm khối "Cập nhật 04/10/2026
  (chưa sửa số ở đoạn trên)" nói rõ sẽ thêm 5 model ⇒ 228 → **513 dòng**, và cố ý chưa sửa cho tới khi đo.
- 3.13 Rà chỗ nhắc cờ `--exclude` lỗi thời — **XONG 04/10/2026**: quét toàn bộ `docs/**, presentations/**,
  handover/**, scripts/*.py, src/**` chỉ thấy `09_cli.md` (2 chỗ) và mã nguồn; cả hai chỗ tài liệu đều
  **đúng** với hành vi hiện tại nên không xoá, chỉ thêm một câu làm rõ: lượt HỎNG thì **xoá thư mục kết quả**
  chứ không phải loại khỏi bảng.
- 3.14 `04_backlog.md`: đóng §10.2/10.3/10.4, sửa §10.1, thêm mục mới — **XONG 04/10/2026**: §10.2 XONG (0,64 /
  1,17 / 0,71 điểm; số ô thấp hơn 5-6%), §10.3 XONG (F1 âm 0,540 → 0,876 và 0,765 → 0,836; nợ mới: phát hiện
  khía cạnh giảm), §10.4 XONG (cả ba đều âm), §10.1 "CHƯA XONG, đã hỏng HAI lần" + cách chạy lại, §10.5/10.7
  cập nhật trạng thái, dòng thời gian ở §8.3 nay ghi 17 lượt; thêm **§11** gồm 11.1 (lỗi bật suy nghĩ ăn hết
  trần token), 11.2 (thăng cấp luật lai thành `method` nếu thắng), 11.3 (trọng số lớp theo từng khía cạnh
  `inverse_by_aspect`), 11.4 (**tập chẩn đoán giá** - quyết định người dùng 04/10/2026).
- 3.15 `ci_checks` + `unittest` + commit + push ⇒ **MỐC DỪNG #1** — **XONG 04/10/2026**:
  `python scripts/ci_checks.py` = **0** (9 mục, không có việc nào phải sửa) và
  `python -m unittest discover -s tests` = **0**; bốn commit theo miền (`934545b` metrics, `ba48ce9` workflow,
  `9214005` experiments, `712752e` plan) rồi `git push origin experiment`. Tổng cộng cả Mục 2-3: **9 commit**
  (gồm `34d4a4e`, `d45e14f`, `7cf3b3d`, `04b35a7`, `6954e95`, `63c39a2`, `85e90b0`).

## Mục 4. Mã và cấu hình mới
- 4.1 Khoá `preprocess.enable_thinking` — **XONG 04/10/2026**:
  `src/preprocessing/qwen.py` thêm `default_enable_thinking()` + `_chat_kwargs()` (khoá CHỈ được truyền
  khi model/thí nghiệm khai; để trống = giữ mặc định của model) và luồn `enable_thinking` qua **cả**
  `encode()` (đường ĐO) lẫn `build_inputs()` (đường DÙNG); `src/experiments/model_config.py` kiểm giá
  trị phải là bool + thêm hàm `enable_thinking(name)`; `src/experiments/experiments.py` thêm
  `preprocess.enable_thinking` vào `KNOWN_KEYS`; `configs/models/qwen3-0.6b.yaml` khai
  `enable_thinking: false` (bump `config_version` 3 → 4); `docs/05_config/04_models.md` thêm dòng giải
  thích. Kiểm thử: `tests/preprocessing/test_qwen.py` (mới, 5 test: không khai thì KHÔNG truyền khoá;
  khai false/true thì truyền đúng; `encode` đi qua đúng đường và nhận ghi đè) +
  `tests/experiments/test_model_config.py::EnableThinkingTest` (4 test: trống = None ≠ false; true/false;
  giá trị không phải bool là lỗi).
  Ghi chú thiết kế: **lớp THÍ NGHIỆM ghi đè được lớp model** (đọc từ cấu hình ĐÃ HỢP NHẤT), nên cùng
  model 0.6B chạy được cả hai chế độ, và hai chế độ rơi vào hai thư mục kết quả khác nhau.
- 4.2 Trần token sinh đọc từ cấu hình — **XONG 04/10/2026**: `experiment_run.max_new_tokens_of()` với thứ
  tự ưu tiên: tham số `max_new_tokens` truyền vào lúc chạy > **`decoding.max_new_tokens`** của cấu hình đã
  hợp nhất > hằng số 400 của `runner`; `run_generation()` dùng hàm này; `experiments.py` thêm
  `decoding.max_new_tokens` vào `KNOWN_KEYS`; `runner.run()` nhận `enable_thinking` và truyền xuống
  `qwen.build_inputs`; `plan_data` và bản ghi `run_meta` mang thêm khoá `enable_thinking`, `print_config`
  in thêm dòng "suy nghĩ". Kiểm thử: `tests/experiments/test_experiment_run.py::ThinkingAndCeilingTest`
  (5 test).
  ✅ **ĐÃ CHỐT 04/10/2026**: giữ `decoding.max_new_tokens` và **ghi rõ `generation.max_new_tokens` là TÊN
  CŨ** ở ba chỗ: `docs/04_experiments/metrics.md`, `docs/05_config/05_experiments_shared.md`, docstring
  `experiment_run.max_new_tokens_of`. (Kiểm thêm: `"generation" in cfg` = **False** - nhóm khoá `generation`
  không tồn tại; `generation` chỉ là tên dict lúc chạy.)
- 4.3 Cửa chặn `% đọc được < 95%` ⇒ `valid: false` — **XONG 04/10/2026**: `metrics.read_rate(infos,
  min_rate=None)` thêm ba khoá `ngưỡng` / `valid` / `reason` (chỉ khi có truyền ngưỡng);
  `experiment_run.read_rate_min_of(config_data)` đọc khoá **`read_rate_min`** từ cấu hình đã hợp nhất (đã
  khai `read_rate_min: 95` ở `configs/experiments/evaluation.yaml`, thêm vào `KNOWN_KEYS`); `finish()` ghi
  thêm dòng `KHÔNG ĐẠT CỬA CHẤT LƯỢNG` vào `run.log` khi dưới ngưỡng. Kiểm thử:
  `tests/evaluation/test_metrics.py::TestReadRateGate` (4 test: không truyền ngưỡng thì KHÔNG có cờ; dưới
  ngưỡng ⇒ `valid=false` + lí do có cả hai số; đúng bằng ngưỡng và trên ngưỡng ⇒ đạt). Đã ghi vào
  `docs/04_experiments/metrics.md` luật 2, kèm ghi chú `scripts/rescore.py` **không** áp cửa này.
- 4.4 Luật "một cơ chế, hai khoá không tách rời" — **XONG 04/10/2026**: đã thêm **luật 23** vào
  `docs/00_workflow/02_rules.md`. ⚠️ **Sửa đường dẫn so với kế hoạch**: kế hoạch ghi
  `docs/05_config/02_rules.md` nhưng **tệp đó KHÔNG tồn tại** (đã kiểm bằng `read_files`); tệp luật thật là
  `docs/00_workflow/02_rules.md` (22 luật cũ + luật 23 mới). Luật 23 gồm ba phần: (a) chạy lượt DÒ (~60
  mẫu) đo p50/p95/max token sinh rồi chốt `max_new_tokens = round_up(p99 × 1,5)`, không vượt cửa sổ ngữ
  cảnh; (b) giữ cửa `read_rate_min` 95%; (c) khai cả hai khoá trong CẤU HÌNH vì chúng đi vào mã băm danh
  tính. Đã cập nhật cả `present_plan.md` mục 4.4 cho khớp.
- 4.5 Đường encoder xuất xác suất từng ô — **XONG 04/10/2026**: `lora.predict()` trả thêm xác suất
  (softmax trên float32 - fp16 làm tròn thô, sai số lan vào ngưỡng); `encoder_run.probability_columns()`
  + `probability_rows()` (hàm thuần) và `run()` ghi `probabilities.csv` (một dòng cho mỗi (review, khía
  cạnh), cột `p(mã <mã>)` theo ĐÚNG mã đã huấn luyện); mẫu tên khai ở `configs/paths.yaml`
  (`probabilities`). Kiểm thử: `tests/experiments/test_encoder_run.py` (6 test). Tài liệu:
  `docs/04_experiments/06_lora_encoder.md` mục 6 + `09_fusion.md` mục 6 (nhóm encoder gửi thêm tệp này).
- 4.6 `scripts/fit_thresholds.py` — **XONG 04/10/2026**: dò ngưỡng theo khía cạnh trên `val` (lưới
  0,05-0,95; hoà chọn ngưỡng LỚN hơn; ràng buộc số ô giảm < 5%; `price` ⇒ `null` + lí do + bảng quét làm
  bằng chứng; macro hai cách). Ghi `data/reports/fusion/thresholds.json`. Lõi ở
  `src/evaluation/fusion.py::fit_thresholds` + `apply_thresholds`.
- 4.7 `scripts/ensemble.py` — **XONG 04/10/2026**: trung bình xác suất nhiều lượt encoder rồi `argmax`
  theo khía cạnh; `--weights val` (macro-F1 lớp âm trên val, chuẩn hoá tổng 1) hoặc bằng nhau. Ghi
  `ensemble.json` + đầu vào rút gọn vào `data/reports/fusion/inputs/`.
- 4.8 `scripts/fuse.py` — **XONG 04/10/2026**: `--fit` chốt luật lai trên `val` (mỗi khía cạnh lấy nguồn
  F1 âm cao hơn; hoà ⇒ LLM; khía cạnh không nguồn nào có ô âm vẫn có dòng + lí do) ghi `rules.json`;
  `--apply` áp luật ĐÓNG BĂNG lên tập khác, đếm ô theo từng nguồn + số ô thiếu.
- 4.9 `scripts/vote.py` — **XONG 04/10/2026**: bỏ phiếu từng ô trên **3 mẫu**; ô phải đọc được ở ít nhất
  một lượt; hoà ⇒ nhãn của lượt ĐẦU TIÊN (truyền theo `seed` tăng dần); ghi `vote.json` kèm số của TỪNG
  mẫu (đo dao động) và thống kê phiếu, và ghi nhãn từng ô vào `inputs/`.
- 4.10 `data/reports/fusion/` + `docs/04_experiments/09_fusion.md` — **XONG 04/10/2026**: thư mục có
  `README.md` (bảng tệp + hai luật + vì sao commit `inputs/`) và `inputs/README.md`; tài liệu 09_fusion.md
  mô tả bốn bước, lệnh, cách đọc số, hai luật, đầu vào rút gọn; `docs/README.md` + `docs/00_workflow/09_cli.md`
  đã thêm dòng cho 4 lệnh mới. Kiểm thử toàn bộ: `tests/evaluation/test_fusion.py` (14 test) +
  `tests/experiments/test_encoder_run.py` (6 test).
- 4.11 Năm cấu hình model mới — **XONG 04/10/2026 (kèm 4 module mã mới)**: **kiểm id trên Hugging Face
  TRƯỚC khi khai** (tải tokenizer thật, 8/8 OK) và **đo trần kiến trúc**: phobert-large 258, ViBERT 512,
  CafeBERT 514, XLM-R 514, Qwen2.5-0.5B 32.768 ⇒ chọn `max_length` 256 cho 4 encoder (cùng ngân sách input
  với PhoBERT/ViSoBERT) và 2304 cho Qwen2.5 (cùng bộ prompt với Qwen3). Mã dùng chung: **mới**
  `src/preprocessing/bert_like.py` (nạp tokenizer theo tên cấu hình, tách từ tuỳ model, encode/build_inputs/info)
  + 4 module mỏng `phobert_large.py`, `vibert.py`, `cafebert.py`, `xlmroberta.py` (mỗi module khai 3 hằng số);
  đăng ký vào `src/training/encoders.py` (6 encoder) và `MODELS` của `token_stats.py` (9 model).
  5 cấu hình: `phobert-large`, `vibert-base-cased`, `cafebert`, `xlm-roberta-base` (encoder, `segmenter`
  vncorenlp/none theo từng họ) + `qwen2.5-0.5b-instruct` (prompt, KHÔNG khai `enable_thinking` vì template
  Qwen2.5 không có biến đó). Kiểm thử: `tests/preprocessing/test_encoders.py` (9 test: registry sạch, id
  checkpoint khớp, bộ tách từ từng model, ngưỡng dưới trần kiến trúc, `token_stats.MODELS` phủ 9 model) +
  cập nhật `tests/training/test_training.py` (danh sách encoder). Tài liệu: `docs/04_experiments/01_models.md`
  (9 model) + `docs/05_config/04_models.md` (bảng model + cách thêm model qua `bert_like`).
- 4.12 Năm model vào `token_stats.MODELS` + đo lại bảng token — **ĐANG LÀM (dừng giữa chừng 04/10/2026,
  người dùng cần tắt máy)**: đã xong phần **mã + đăng ký** (5 model vào `MODELS` ⇒ bảng đo từ 4 model
  thành **9 model**, tức mỗi bảng 12 → 27 dòng). Đã đo lại **10/19 bảng**: cả **8 bảng** của phiên bản
  `…-e0ccc484` + `absa_cot_1shot_v1` và `absa_cot_zeroshot_v1` của phiên bản `…-e616c1e3`.
  **CÒN 9 bảng**, tất cả ở phiên bản `…-e616c1e3` — chạy đúng 9 lệnh này (mỗi lệnh ghi một bảng):
  ```
  python run_token_stats.py --hash e616c1e3 --prompt absa_cot_5shot_v1 --system absa_cot
  python run_token_stats.py --hash e616c1e3 --prompt absa_cot_v1 --system absa_cot
  python run_token_stats.py --hash e616c1e3 --prompt absa_cot_1shot_v2 --system absa_cot
  python run_token_stats.py --hash e616c1e3 --prompt absa_cot_1shot_v3 --system absa_cot
  python run_token_stats.py --hash e616c1e3 --prompt absa_cot_1shot_v4 --system absa_cot
  python run_token_stats.py --hash e616c1e3 --prompt absa_direct_v1 --segmenter none
  python run_token_stats.py --hash e616c1e3 --prompt absa_direct_v1 --segmenter pyvi
  python run_token_stats.py --hash e616c1e3 --prompt absa_direct_v1 --segmenter vncorenlp
  python run_token_stats.py --hash e616c1e3 --prompt absa_one_turn_v1 --system absa_one_turn
  ```
  Thời lượng đo được: 1 ví dụ 113 giây · 5 ví dụ **400 giây** (bảng chậm nhất) · CoT 2 ví dụ 143 giây ·
  0 ví dụ 91 giây · một lượt 79 giây · `absa_direct_v1` 43-55 giây ⇒ còn khoảng **18 phút**.
  **Kiểm toàn vẹn ĐÃ CHẠY 04/10/2026 (không có bảng nào hỏng)**: mỗi bảng đã đo có đúng **27 dòng / 9
  model**, mỗi bảng chưa đo còn **12 dòng / 4 model**; sau khi xong 9 bảng trên thì
  `python scripts/collect_reports.py --group model_input` cho bảng gộp **513 dòng** (228 + 5 model × 19
  bảng × 3 split).
  **Trạng thái đã commit + push**: 10 bảng + bảng gộp (378 dòng = 10×27 + 9×12, tự khớp với các bảng
  thành phần) ở commit `chore(data): regenerate the token tables for the five new models (part 1 of 2)`.
  **Hai phát hiện cần ghi vào tài liệu khi hoàn tất** (chưa ghi): (a) `qwen3-0.6b` **+4 token** ở MỌI
  split (368 → 372 trung bình - **câu này SAI, xem ghi chú sửa lỗi ở mục 4.12 bên dưới**) vì chat template
  chế độ KHÔNG suy nghĩ chèn một khối ` thinking` rỗng - đây là bằng chứng `enable_thinking: false` có tác
  dụng thật; (b) `cafebert` và `xlm-roberta-base` cho
  số liệu **giống hệt nhau** (cùng tokenizer SentencePiece, vocab 250.002) - điều đúng cần ghi lại,
  không phải lỗi trùng lặp (cùng lối với cặp Qwen3).
  **CÒN LẠI của mục 4.12** — **XONG 04/10/2026**, xem dòng dưới.
- 4.12 **XONG 04/10/2026**: đo đủ **19 bảng**, mỗi bảng **27 dòng / 9 model** ✓; bảng gộp `model_input.csv`
  = **513 dòng** ✓ khớp công thức 228 + 5 model × 19 bảng × 3 split. Tài liệu đã cập nhật:
  `docs/04_experiments/02_model_input.md` (9 model/27 dòng, 5 model mới, hai phát hiện) và
  `docs/04_experiments/04_backlog.md` (§11.5 mới + §10.1 ghi trạng thái "đã sẵn sàng chạy").
  **Hai phát hiện đã ghi, kèm số đo lại cho đúng:** (a) `cafebert` và `xlm-roberta-base` trùng số ở **cả 15
  cột** — cùng `XLMRobertaTokenizer`, cùng vocab 250.002, mà bảng chỉ đo **độ dài input**, nên trùng là
  ĐÚNG (khác trọng số tiền huấn luyện là chuyện của bảng kết quả, không phải bảng này); (b) `qwen3-0.6b`
  nhiều hơn `qwen3-4b-instruct-2507` đúng **+4 token/review** ở mọi split, và con số đó đã **đo trực tiếp
  bằng tokenizer**: khuôn chat cho **10 token** khi bật/không truyền `enable_thinking`, **14 token** khi
  truyền `false` (khối ` thinking` rỗng) ⇒ bằng chứng cửa đã đi tới khuôn chat. Ghi chú sửa lỗi: câu
  "368 → 372" viết ở bản trước là **so sai chiều** — đó là so 0,6B với 4B, không phải trước/sau.
- 4.13 **XONG 04/10/2026**: `ci_checks` chỉ còn 20 dòng "chưa ghim" (đúng trạng thái trước Mục 6), và
  `unittest` 889 test với **1 lỗi DUY NHẤT** là `RealTreeTest.test_sau_kiem_tra_deu_sach` — cũng vì các
  notebook chưa ghim, tự hết sau Mục 6.1. Commit: `feat(experiments): read the sampling seed from the
  config` · `feat(experiments): add the six batch-8 experiments` · `chore(data): regenerate the token tables
  for the five new models (part 2 of 2)` · `docs(plan): add the batch-7 plan and update the token, backlog
  and handover docs` · `docs(presentations): add the LLM batch-size and prompt-structure write-ups`
  (hai tệp thuyết trình này **còn sót chưa commit** từ phiên trước, nay đã vào git).

## Mục 5. Tạo thí nghiệm và tài liệu cho các đợt
- 5.1 **XONG 04/10/2026**: tạo 14 thư mục mới bằng `scripts/new_experiment.py` (0.6B DÒ `exp004`; Qwen2.5
  `exp001..003`; 4 encoder mới; 2 lượt `val` `lora/exp003`; `exp014/015/016/017`), rồi viết lại config +
  README cho từng thí nghiệm (README ghi rõ "khác `parent` đúng một thứ"). Ba lượt 0.6B chạy lại
  (`exp001..003`) giữ cấu hình, `parent: null`, README ghi lí do chạy lại (`enable_thinking: false`).
  Hai cặp prompt/ví dụ mới: `absa_cot_1shot_v5` (**đổi câu chữ**, ví dụ byte-identical với v1) và
  `absa_cot_1shot_v6` (prompt byte-identical với v1, **ví dụ có ô giá mã 2**), cộng prompt chẩn đoán
  `absa_price_probe_v1` + system `absa_price_probe`. Danh sách tập-đóng trong `tests/experiments/test_prompts.py`
  đã cập nhật (thêm v5, v6 — cả hai vẫn đúng 1 ví dụ nên phép so với `exp003` chỉ lệch một biến).
  **Lỗi bẫy phát hiện được:** `new_experiment.py` sinh config với `data.version: v0.1.0` (bản dữ liệu CŨ) —
  cả 14 config đã sửa thành `v0.2.0`.
- 5.2 **XONG một phần 04/10/2026 (6/9)**: đã tạo + viết config/README cho 6 thí nghiệm chốt được cấu hình
  ngay (`phobert-base-v2/lora/exp004`, `visobert/lora/exp004`, `qwen3-4b-instruct-2507/prompt-cot/exp018`,
  `exp019`, `exp020`, `exp021`). **Ba lượt 0.6B bật suy nghĩ (`exp005/006/007`) CHƯA tạo** — trần token của
  chúng chỉ biết sau lượt DÒ (`exp004`), và mục 8.2/9.3 còn phải quyết chạy **ba mức hay một mức**; tạo ở
  mục 8.7 (trước gói 015) để không ghi vào repo một cấu hình có trần đoán mò.
  **Lỗ hổng mã đã bịt trong lúc làm:** hạt giống sinh văn bản nằm CỨNG trong mã (`seed=42`) nên ba lượt lấy
  mẫu sẽ ra **cùng một thư mục kết quả** ⇒ biểu quyết 3 mẫu thành vô nghĩa. Đã thêm khoá **`decoding.seed`**
  (vào `KNOWN_KEYS`, đọc từ config trong `run_generation`/`plan`, ghi vào `evaluation.yaml`, +5 test); mặc
  định vẫn là 42 nên các lượt cũ **không** đổi dấu vân tay.
- 5.3 **CHƯA LÀM — cần người dùng quyết:** 3 thí nghiệm đợt 9 cần 3 file `configs/models/*.yaml` mới
  (`qwen3-4b-thinking-2507`, `qwen3-8b`, `qwen3-14b`) và nên thêm 3 model đó vào `token_stats.MODELS` ⇒
  kéo theo **đo lại cả 19 bảng token lần nữa** (~18 phút) mới giữ được nhất quán "bảng = mọi model đang
  dùng". Đợt 9 vốn được ghi là "mở rộng, chạy khi muốn" nên tôi **để nguyên**, chờ quyết định.
- 5.4 **XONG 04/10/2026**: `docs/06_plan/P8_batch7.md` — 10 mục: mục tiêu, trạng thái, bảng 17 + 9 + 3 thí
  nghiệm, luật chống chạm trần, điều kiện mỗi lượt, luật chia mức nhánh suy nghĩ, **bốn luật kết hợp**, thứ
  tự ưu tiên, số phiên + mốc dừng, quy ước thực thi.
- 5.5 **XONG 04/10/2026**: `handover/README.md` thay bảng 20 notebook bằng **17 dòng đợt 7** xếp theo thứ tự
  nên chạy; cột thời gian ghi **ước tính** kèm số đo thật để đối chiếu; thêm mục **"Nhóm encoder gửi thêm
  tệp xác suất"** và mục **"Nhánh suy nghĩ đắt gấp khoảng 5 lần"** + luật chống chạm trần.
- 5.6 **XONG 04/10/2026**: `ci_checks` + `unittest` + commit + push (xem 4.13).

## Mục 6. Ghim notebook và dựng gói 012 (rồi 013, 014)
- 6.1 **XONG 04/10/2026**: push `4571648` ⇒ **ghim 23 notebook** (14 mới đợt 7 + 3 chạy lại + 6 đợt 8) vào
  đúng commit đó ⇒ `ci_checks` **sạch (mã thoát 0)** + `unittest` **889 OK** ⇒ commit ghim `002086b` ⇒ push.
  **Lệch nhỏ so với câu chữ của kế hoạch (có lí do):** với thí nghiệm MỚI, CI **không thể** xanh TRƯỚC lần
  ghim đầu — chính mục 6 của `ci_checks` là chỗ bắt notebook phải có `REPO_SHA` hợp lệ. Luồng đúng (và
  trùng `docs/00_workflow/01_flow.md` dòng 110-117) là: đẩy commit code ⇒ ghim ⇒ commit ghim ⇒ push ⇒
  **commit ghim đó mới xanh**. Cũng vì vậy 3 notebook 0.6B đã gửi ở gói trước phải **ghim lại** (từ
  `8bfe96e` sang bản code có `enable_thinking: false`).
- 6.2 **XONG 04/10/2026**: `scripts/build_package.py` ⇒ **gói 012**
  (`handover/out/SentimentX-goi-012-002086b-261004.zip`: 23 notebook MỚI + 3 notebook ĐỔI + `README.md` đổi;
  60 file y nguyên không gửi lại) ⇒ commit sổ gói `c8c8baf` ⇒ push.
  **Phát hiện sau khi dựng gói (bẫy thật, đã xử lý):** tôi thêm một ghi chú vào `handover/README.md` (cảnh báo
  6 notebook của đợt sau **đừng chạy vội**), mà `README.md` **nằm trong gói** ⇒ bản 012 đang giữ README cũ.
  Công cụ **từ chối ghi lại số 012** ("số gói là bản ghi của một lần gửi… sửa gì thì gửi gói MỚI") ⇒ đã dựng
  **gói 013** (`handover/out/SentimentX-goi-013-34bbe45-261004.zip`, 11 KB: 103 file `kept` + **1 file
  `changed`** là `README.md`) ⇒ **phải gửi `012` RỒI `013`** (đúng cơ chế gói tăng dần; `013` một mình chỉ có
  README).
  **Hệ quả về số gói (cập nhật 04/10/2026 sau khi dựng gói 014):** gói của đợt 7 là **012 + 013 + 014** ⇒
  đợt 8 = **gói 015**, gói cuối = **016** (đã sửa ở `P8_batch7.md` mục 1/2/4/9, `present_plan.md` mục
  6.2/7.1/8.7/10.5/11.3 và `docs/06_plan/README.md`). Không có gì phải ghim lại: hai commit sau `002086b`
  (`dfa8511` tài liệu, `34bbe45` khuôn mẫu) **không** đụng `src/` nên notebook vẫn dùng đúng bản mã đã ghim.
  ⇒ **MỐC DỪNG #2** ✓ (chờ người dùng chạy đợt 7).
- Ghi chú thêm: `templates/experiment/config.yaml` đã sửa `version: v0.1.0` → `v0.2.0` (bịt bẫy "thí nghiệm mới
  lặng lẽ chấm trên bộ dữ liệu cũ"); `ci_checks` + `unittest` xanh sau khi sửa (`34bbe45`).

- 6.3 **XONG 05/10/2026** (sau khi sửa các phát hiện D1-D8 ở mục 14): `scripts/build_package.py` ⇒ **gói 014**
  (`handover/out/SentimentX-goi-014-2eba2dc-261005.zip`, **3 file `changed`**: `README.md` bàn giao +
  `experiments/phobert-base-v2/lora/exp004/README.md` + `experiments/visobert/lora/exp004/README.md`; 101 file
  `kept`, 0 `new`, 0 `deleted`) ⇒ commit sổ gói `60c4adf`. `ci_checks` **sạch (mã thoát 0)** + `unittest`
  **898 OK**. ⇒ **MỐC DỪNG #2** vẫn nguyên: ba gói **012 + 013 + 014** phải giải nén **lần lượt** lên cùng thư
  mục Drive (gói sau đè lên gói trước).

## Mục 7. Người dùng chạy đợt 7
- 7.1 Giải nén **lần lượt** gói 012 rồi 013 rồi **014** lên cùng thư mục Drive (gói sau đè lên gói trước) —
  CHỜ NGƯỜI DÙNG.
- 7.2 Chạy theo thứ tự 7 nhóm — CHỜ NGƯỜI DÙNG.
- 7.3 Điều kiện mỗi lượt (`% đọc được ≥ 95%`, DÒ ghi p50/p95/max) — CHỜ NGƯỜI DÙNG.
- 7.4 Gửi **7 tệp nhẹ** (thêm `predictions.csv` từ 04/10/2026) **+ tệp xác suất** cho 6 lượt encoder +
  thời gian thực tế — CHỜ NGƯỜI DÙNG.

## Mục 8. Xử lý đợt 7 và chốt luật
- 8.1 `collect_reports.py` + đối chiếu từng ô — CHƯA LÀM.
- 8.2 Chốt trần token từ lượt DÒ — CHƯA LÀM.
- 8.3 Đọc kết quả ba lượt về giá (`exp014`, `exp015`, `exp016`) — CHƯA LÀM.
- 8.4 Dò ngưỡng theo khía cạnh trên `val` ⇒ tệp luật JSON — CHƯA LÀM: **đã chốt cách làm** (04/10/2026) -
  ngưỡng cho **6 khía cạnh**, `price: null` + lí do "val có 0 ô âm", kèm bằng chứng quét thử, báo cáo macro cả
  trên 7 và trên 6 khía cạnh.
- 8.5 Chốt bảng luật lai trên `val` ⇒ tệp luật JSON — CHƯA LÀM.
- 8.6 Viết kết luận nhóm A, B, encoder mới, ba lượt giá — CHƯA LÀM.
- 8.7 Hai thí nghiệm `test` có ngưỡng + **ba thí nghiệm 0.6B bật suy nghĩ**(tạo ở đây vì trần token chỉ biết
  sau lượt DÒ) ⇒ ghim ⇒ **gói 015** ⇒ **MỐC DỪNG #3** — CHƯA LÀM. (Hai thí nghiệm `test` đã TẠO SẴN ở gói
  012; mục này nay chỉ còn tạo 3 lượt 0.6B + ghim + đóng gói.)

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
- 10.5 Cập nhật tài liệu, đóng backlog, **gói 016** (nếu có sửa mã; không sửa mã thì không cần gói mới) ⇒
  **MỐC DỪNG #4** — CHƯA LÀM.

## Mục 11. Danh mục thí nghiệm theo đợt
- 11.1 Đã chạy xong (đối chiếu) — XONG 04/10/2026: ghi danh mục trong `present_plan.md`; số liệu thật sẽ
  đối chiếu ở mục 3.1/3.2.
- 11.2 Đợt 7 (17 lượt) — **XONG phần tạo + ghim 04/10/2026**: 17 notebook đã có cấu hình + README, đã ghim
  `4571648` và nằm trong **gói 012**; phần chạy là mục 7 (chờ người dùng).
- 11.3 Đợt 8 (9 lượt) — **6/9 XONG phần tạo + ghim 04/10/2026**: 6 notebook (2 lượt `test` có ngưỡng + 4
  lượt lấy mẫu) đã ghim `4571648` và nằm trong **gói 012**; 3 lượt 0.6B bật suy nghĩ chờ mục 8.2 rồi tạo ở
  mục 8.7 (đi kèm **gói 015**).
- 11.4 Đợt 9 (3 lượt) — **CHƯA LÀM, chờ quyết định** (mục 13.4): cần 3 config model mới + cân nhắc đo lại
  19 bảng token. Danh mục đã ghi trong `present_plan.md` mục 11.4.

## Mục 12. Việc để ngỏ
- 12.1 Danh sách việc mở — CHƯA LÀM: đã ghi danh sách trong `present_plan.md`; **đã thêm** mục "lập tập chẩn
  đoán giá" theo quyết định 04/10/2026 (làm sau, không thuộc kế hoạch đợt này); sẽ chép vào
  `docs/04_experiments/04_backlog.md` ở mục 3.14.
- 12.2 MLflow (đã mất, không khôi phục) — XONG 04/10/2026: ghi nhận quyết định "kệ MLflow" của người dùng;
  không backfill.

## Mục 13. Điều còn chờ người dùng trả lời
- 13.1 Giữ `xlm-roberta-base` làm đối chứng — CHỜ NGƯỜI DÙNG (mặc định: GIỮ).
- 13.2 Commit đầu vào cho bước kết hợp vào `data/reports/fusion/inputs/` — CHỜ NGƯỜI DÙNG (mặc định: CÓ).
- 13.3 Cửa `% đọc được ≥ 95%` chỉ đánh dấu, không xoá dữ liệu — CHỜ NGƯỜI DÙNG (mặc định: 95%, có đánh dấu).
- 13.4 **Đợt 9 (3 thí nghiệm lớn) có làm trong đợt này không?** Đợt 9 cần 3 file `configs/models/*.yaml` mới
  cho `qwen3-4b-thinking-2507`, `qwen3-8b`, `qwen3-14b`; nếu thêm 3 model đó vào `token_stats.MODELS` thì
  phải **đo lại cả 19 bảng token** (~18 phút) để giữ nhất quán "bảng = mọi model đang dùng". Mặc định tôi
  đang dùng: **để nguyên, không tạo bây giờ** (kế hoạch vốn ghi đợt 9 là "mở rộng, chạy khi muốn"). Chọn
  "làm luôn" thì chi phí thêm là 3 config + 18 phút đo lại (không cần GPU).

## Mục 14. Kiểm tra chéo trước khi người dùng chạy đợt 7 (04/10/2026, chỉ đọc)

Mục đích: dò lỗi NGẦM trong phần vừa làm xong (mã, cấu hình, 23 notebook, gói 012/013) TRƯỚC khi người
dùng bỏ 10-12 giờ GPU. Cách kiểm: chạy lại chính công cụ của dự án thay vì đọc suông -
`run_notebook.py <exp> --preflight-only` cho **23/23 notebook (mã thoát 0)**, quét `data.version` của **40
config** (40/40 = `v0.2.0`), đối chiếu `EXP_DIR` + `REPO_SHA` từng notebook, mở zip đếm file gói 012/013, đếm
dòng **19 bảng token** (28 dòng = 1 header + 9 model × 3 split), `model_input.csv` **513 dòng**, `MODELS` = 9,
và kiểm lại cỡ mẫu `price` từ EDA GỐC.

**Kết luận: KHÔNG có lỗi nào chặn đợt 7.** Tám phát hiện, nay đều đã xử lý:

| # | Phát hiện | Mức | Trạng thái |
| --- | --- | --- | --- |
| D1 | Không có lệnh nào ÁP được `thresholds.json` lên lượt `test`, nên mục 10.2 của kế hoạch chưa có đường chạy tái lập | lỗ hổng mã | **ĐÃ SỬA** - `scripts/fit_thresholds.py --apply-to` + `fusion.applied_report` (commit `70112ad`; +4 test `tests/evaluation/test_fusion.py`, +5 test `tests/workflow/test_cli.py`). Đã chạy thử đầu-cuối trên lượt giả: số ô giữ nguyên, `price` để nguyên kèm lí do, macro ba cách |
| D2 | Hai `README.md` + hai `config.yaml` của `lora/exp004` ghi `fit_thresholds.py --apply` - cờ KHÔNG tồn tại | chỉ dẫn sai | **ĐÃ SỬA** (commit `bc36b97`). Chỉ chú thích/README: `config_sha256` băm GIÁ TRỊ cấu hình đã hợp nhất (không băm byte file) và notebook kéo commit đã ghim, nên hai lượt chạy không đổi |
| D3 | Mục 3.7/3.8 của chính tệp này bị chép HAI lần (một bản `XONG` kèm bằng chứng, một bản `CHƯA LÀM`) | tệp trạng thái tự mâu thuẫn | **ĐÃ SỬA** - xoá bản `CHƯA LÀM` còn sót và xếp lại thứ tự 3.5 → 3.6 → 3.7 → 3.8 |

| D4 | Số gói lệch ở 7 chỗ sau khi đợt 7 thành **012 + 013** (rồi +014) | tài liệu | **ĐÃ SỬA** - đợt 8 = **gói 015**, gói cuối = **016**, ở `check_present_plan.md`, `present_plan.md` (6.2/7.1/8.7/10.5/11.3) và `P8_batch7.md` (1/2/4/9) |
| D5 | `P8_measurement_mlflow.md` còn "**20 notebook** ghim cùng bản code, gói mới nhất là **011**" | tài liệu | **ĐÃ SỬA** - nay là **23 notebook** ghim `4571648` (tổng 40 notebook trong repo), gói mới nhất 014 |
| D6 | `handover/README.md` viết "**Chưa lượt nào chạy trước đây**" (sai: ba lượt 0.6B đã chạy ngày 02/10/2026 và hỏng), và câu về hai lượt `test` ngụ ý phụ thuộc ngưỡng LÚC CHẠY (ngưỡng áp NGOÀI) | tài liệu | **ĐÃ SỬA** trong gói 014 |
| D7 | Khối lịch sử mục 4.12 còn câu sai "368 → 372" dù dòng ngay sau đã đính chính | dễ đọc sai | **ĐÃ SỬA** - chèn cảnh báo tại chỗ trỏ xuống ghi chú sửa lỗi |
| D8 | Danh sách gửi lại gọi là "sáu tệp nhẹ" nhưng (a) `09_fusion.md` liệt kê 7 tên, (b) **thiếu `predictions.csv`** - mà bước kết hợp dựng `inputs/*.csv` từ nó và lượt DÒ cần nó để đo p50/p95/p99 | thiếu sót thật khi bàn giao | **ĐÃ SỬA** - nay là **7 tệp nhẹ** (thêm `predictions.csv`) ở `handover/README.md`, `present_plan.md` (4.5/7.4/9.2), `P8_batch7.md`, `check_present_plan.md` (7.4), `09_fusion.md`, `configs/paths.yaml` |

Ba phép kiểm riêng, đều ĐẠT:
1. lượt **DÒ** có cột `token sinh` + `có <think>` trong `predictions.csv` ⇒ đo được p50/p95/p99/max, nên
   mục 8.2 làm được (nếu chỉ gửi 6 tệp nhẹ cũ thì bước này bất khả thi - chính là D8);
2. `max_length` 2304 + `max_new_tokens` 8192 < 32.768 ⇒ lượt DÒ không vượt cửa sổ ngữ cảnh;
3. ba checkpoint HF mới (`uitnlp/CafeBERT`, `FPTAI/vibert-base-cased`, `vinai/phobert-large`) đều tồn tại,
   công khai, không gate (bốn encoder còn lại đã có tiền sử chạy được).

<!-- DIEM-NOI-TIEP -->




