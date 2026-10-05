# present_plan — Kế hoạch đang chạy: đợt 7 → đợt 10

> Đây là kế hoạch **ĐANG THỰC THI**, đặt ở gốc repo. Tệp đi kèm `check_present_plan.md` có **cùng mục,
> cùng mục nhỏ**, chỉ ghi trạng thái (đã làm gì) để đọc lại nhanh; mỗi lần làm xong một mục nhỏ thì
> đánh dấu vào tệp đó.
>
> Kế hoạch của đợt trước đã được hợp nhất vào `docs/06_plan/P8_measurement_mlflow.md`. Cặp tệp này sẽ
> được hợp nhất vào `docs/06_plan/P9_batch7.md` khi kết thúc đợt (đây là **đề xuất**, chờ người dùng
> duyệt; chưa làm).
>
> Bối cảnh xuất phát: còn **17 lượt chạy dùng được** (9 lượt cũ + 8 lượt mới); ba lượt `qwen3-0.6b`
> bật suy nghĩ **không đọc được JSON** nên phải xoá rồi chạy lại sau khi tắt suy nghĩ; ba lượt 4B
> nạp nhầm model (nằm trong thư mục thí nghiệm 0.6B) cũng phải xoá; MLflow đã mất (DagsHub xoá mềm
> experiment) và **không khôi phục**.

## Mục 1. Quy tắc bắt buộc của repo (nhắc lại trước khi làm)

- **1.1 Commit**: theo Conventional Commits **tiếng Anh** (`type(scope): subject`, động từ `add`/`fix`/
  `remove`, tiêu đề ≤ 72 ký tự). **Một commit = một task nhỏ**, tách theo miền; sau mỗi commit dự án
  vẫn phải chạy được; **không** gộp sửa lỗi với đổi cấu trúc trong cùng một commit.
- **1.2 Kiểm tra sau mỗi nhóm việc**: chạy `python scripts/ci_checks.py` và
  `python -m unittest discover -s tests` (Windows: `$env:PYTHONUTF8=1`), **cả hai phải thoát mã 0**.
- **1.3 Khi lỗi lớn khó sửa**: **quay lui bằng git** về commit xanh gần nhất rồi mới xem lại kế hoạch;
  **báo người dùng** trước khi đi tiếp bằng cách khác.
- **1.4 Bất biến dự án**: không hardcode đường dẫn (dùng `configs/paths.yaml`); không đặt giá trị mặc
  định trong mã (thiếu khoá là lỗi); **notebook đã ghim KHÔNG sửa** (muốn có hiệu lực phải ghim mới);
  cặp `configs/prompts/<tên>.txt` + `examples/<tên>.txt` đã dùng là **bất biến** (đổi thì tạo cặp mới);
  `test` không bị sửa; config phiên bản dữ liệu/pipeline là bất biến.
- **1.5 CI phải XANH trước khi ghim notebook và trước khi dựng/gửi gói bàn giao.**
- **1.6 Ghi tệp**: tệp `.md` ghi **không BOM**; văn bản tiếng Việt dùng công cụ sửa tệp với nội dung đã
  mã hoá sẵn, **không** dùng here-string trong PowerShell (làm hỏng mã hoá).
- **1.7 Thay đổi kế hoạch**: mọi thay đổi so với tệp này phải **được người dùng đồng ý trước**; việc gì
  phát sinh thì báo cáo, không tự ý đổi.

## Mục 2. Dọn dẹp kết quả lỗi (không cần GPU)

- **2.1** Xoá **6 thư mục kết quả lỗi** ở máy (mỗi thí nghiệm 0.6B có đúng hai thư mục, một tốt-một-lỗi):
  - ba lượt **4B nạp nhầm model**: `qwen3-0.6b/prompt-cot/exp001/results/8db40559`,
    `exp002/results/db6efb02`, `exp003/results/30c9e674` — `repo_sha 88d12e68…`, đọc được ~100% nhưng
    `model` là `Qwen/Qwen3-4B-Instruct-2507` (thời điểm mã còn lấy sai model), số ô 2580 / 2461 / 2520
    trùng khít bộ lượt 4B fp16 lô 4;
  - ba lượt **0.6B bật suy nghĩ**: `exp001/results/bc32904d`, `exp002/results/edc0797a`,
    `exp003/results/d5b8e7fc` — `repo_sha 8bfe96e…`, `% đọc được` chỉ **3,33 / 1,36 / 1,73**, có khối
    `<think>` 999 / 714 / 788 lần, lí do lỗi chính là "không thấy JSON nào" (1549 / 1561 / 1536).
  - **Trước khi xoá**: in lại bằng chứng (`model`, `repo_sha`, `read_rate`, `paper.cells` từ
    `metrics.json`) để ghi vào `check_present_plan.md`.
- **2.2** Xác nhận trên Drive đã xoá đúng **6** thư mục tương ứng (người dùng đã xoá 3 thư mục 4B cũ).
- **2.3** Kiểm tra toàn vẹn **17 thư mục kết quả còn lại**: mỗi thư mục có đủ `run_meta.json`,
  `metrics.json`, `metrics.csv`.
- **2.4** Lập danh mục 17 lượt (nhãn thư mục, mã băm 8 ký tự, model, lượng hoá, cỡ lô, số ví dụ, tập
  đánh giá) để dán vào `docs/04_experiments/08_experiment_rationale.md`.

## Mục 3. Sinh lại bảng số 17 lượt và viết lại kết luận (không cần GPU)

- **3.1** Chạy `scripts/collect_reports.py` → sinh lại **5 nhóm bảng** trong `data/reports/`; kiểm
  `attempt_registry` có **đúng 17 dòng**.
- **3.2** **Đối chiếu từng ô**: so `accuracy_by_aspect.csv` và `prf_by_aspect_sentiment.csv` với
  `scores_paper` của từng lượt; kiểm `mispredictions_paper.csv` có số dòng = `cells` − `correct`.
  Chỉ khi bước này sạch mới được viết bất kỳ con số nào vào tài liệu.
- **3.3** Viết lại **mục lượng hoá**: 4-bit hơn fp16 **0,64 / 1,17 / 0,71 điểm** trên cơ sở `paper`
  (macro) ở ba mức 0 / 1 / 5 ví dụ, nhưng **trả lời ít hơn 5–6% số ô** (`cells` 2414 / 2324 / 2375 so
  với 2580 / 2461 / 2520); F1 lớp âm của khía cạnh `price` ở mức 0 ví dụ: fp16 0,43 so với 4-bit 0,27.
  Nêu rõ lợi thế điểm số một phần **đến từ việc kiêng trả lời**.
- **3.4** Viết lại **mục ba biến thể prompt** là **kết quả ÂM**: `exp011` 97,63 · `exp012` 96,52 ·
  `exp013` 92,66 (số ô chỉ còn 1972) so với gốc `exp003` 97,72; F1 lớp âm của `price`: 0,60 → 0,31 /
  0,60 / 0,17.
- **3.5** Viết lại **mục encoder**: `weighted_ce` thắng (ViSoBERT 94,86 → 95,61; PhoBERT-base 88,40 →
  96,62), F1 lớp âm 0,56 → 0,70 và 0,15 → 0,78, số ô tăng, `price` vẫn 0,00, và **thứ hạng hai encoder
  đảo nhau**; sửa câu sai "PhoBERT không đoán được lớp âm" ở
  `docs/04_experiments/08_experiment_rationale.md`, `docs/04_experiments/06_lora_encoder.md`,
  `docs/04_experiments/01_models.md`.
- **3.6** Thêm mục **"`price` là điểm mù chung, kể cả của công bố"** (F1 = 0 ở cả ba mức của công bố) và
  câu trung thực: đỉnh đạt được `exp009` 98,06 (micro) / 97,77 (macro) so với công bố 97,70 ⇒ khoảng
  chênh **0,07 nằm trong nhiễu của một lần chạy greedy**, không được coi là "vượt công bố".
- **3.7** Cập nhật cây thí nghiệm: `docs/04_experiments/07_evolution.md`,
  `presentations/experiment_tree.md`, `presentations/experiment_tree.drawio` (thêm 8 nhánh mới,
  **bỏ nét đỏ D**, kiểm tệp XML còn hợp lệ).
- **3.8** Cập nhật `presentations/experiment_rationale.md` và `presentations/result_analysis.md`.
- **3.9** `docs/04_experiments/metrics.md`: thêm **năm luật đo** — (a) cửa `% đọc được ≥ 95%`; (b) `token
  sinh trung bình ≥ 95% trần` thì coi là **bị cắt**; (c) **luôn đọc kèm số ô** (`cells`); (d) ghi rõ
  macro hay micro; (e) F1 ghi theo tỉ lệ 0..1 — và ghi thêm **quyết định biểu quyết 3 mẫu** (mở rộng
  5 mẫu chỉ khi thấy có ích ở đợt sau).
- **3.10** Sửa **bảng thời gian** ở `handover/README.md`, `docs/00_workflow/07_colab.md`,
  `docs/00_workflow/01_flow.md`, `docs/04_experiments/04_backlog.md`: điền **số đo thật của 17 lượt**,
  đánh dấu `exp004` và `exp010` là **lượt CHẠY TIẾP** (dùng lại 1304 và 1576 mẫu nên số giây ghi được
  chỉ là một phần), **xoá giả thuyết sai** "5 ví dụ sinh ít token hơn".
- **3.11** Quét số liệu cũ: "chín lượt" → "17 lượt"; "mười hai notebook" / "12 notebook" → "20 notebook"
  (ở `docs/00_workflow/10_template_notebook.md` 2 chỗ, `07_colab.md`, `handover/README.md`); "12 thí
  nghiệm" trong `docs/01_dataset/changelog.md`; soát lại `docs/06_plan/P7_rerun.md` §9,
  `docs/06_plan/README.md`, `docs/README.md`.
- **3.12** Ghi chú rõ trong tài liệu: `docs/04_experiments/02_model_input.md` **không sửa ở đợt này**
  (còn 228 dòng / 19 tệp) — sẽ sửa ở mục 4.12.
- **3.13** Rà và xoá/cập nhật các chỗ còn **nhắc cờ `--exclude`** đã lỗi thời (ví dụ
  `docs/00_workflow/09_cli.md`).
- **3.14** `docs/04_experiments/04_backlog.md`: đóng §10.2, §10.3, §10.4 (kèm số cụ thể); sửa §10.1
  (model 0.6B) thành "đang sửa mã + sẽ chạy lại"; thêm ba mục mới: **"lỗi đã gặp: model bật suy nghĩ ăn
  hết trần token"**, **"thăng cấp luật lai thành một `method` nếu thắng"**, và **"trọng số lớp theo TỪNG
  khía cạnh (`loss.class_weight: inverse_by_aspect`) — làm nếu đường ngưỡng chưa đủ"**.
- **3.15** Chạy `ci_checks` + `unittest` sạch; commit theo chủ đề; `git push` ⇒ **MỐC DỪNG #1**.

## Mục 4. Mã và cấu hình mới (không cần GPU)

- **4.1** Cài khoá `preprocess.enable_thinking`: `src/preprocessing/qwen.py` (hàm `encode` và
  `build_inputs`) **chỉ truyền khoá khi mẫu chat của model thật sự có biến đó**; sửa cùng đường trong
  `src/preprocessing/token_stats.py`; cho phép khai khoá trong `src/experiments/model_config.py`;
  thêm kiểm thử; cập nhật `docs/05_config/04_models.md`.
- **4.2** Cho trần token sinh **đọc được từ cấu hình thí nghiệm**: khoá **`decoding.max_new_tokens`**
  (nhóm `decoding` đã có: `mode`, `temperature`, `top_p`), thứ tự ưu tiên: tham số `max_new_tokens` truyền
  vào lúc chạy > khoá này > 400. *Tên cũ*: kế hoạch bản đầu ghi `generation.max_new_tokens` - đó là **tên
  cũ**, không phải khoá thứ hai (nhóm `generation` không tồn tại trong lược đồ cấu hình; `generation` chỉ
  là tên dict lúc chạy). Kèm kiểm thử cho cả hai hàm `thinking_of` / `max_new_tokens_of`.
- **4.3** Cửa chặn `% đọc được < 95%` ⇒ ghi `valid: false` **kèm lí do** (+ kiểm thử + ghi vào
  `docs/04_experiments/metrics.md`).
- **4.4** Ghi luật **"một cơ chế, hai khoá không được tách rời"** (ví dụ bật suy nghĩ phải đi kèm trần
  token) vào **`docs/00_workflow/02_rules.md`** - *tệp luật THẬT của dự án (22 luật); kế hoạch ghi nhầm
  `docs/05_config/02_rules.md`, tệp đó không tồn tại*. Luật mới là **luật 23**.
- **4.5** Đường encoder xuất **xác suất từng ô** `p(mã 0..3)`: thêm tệp xác suất, khai trong
  `configs/paths.yaml`, có kiểm thử; **không** thêm tệp này vào danh sách tệp nhẹ trong tài liệu,
  nhưng README gói phải ghi rõ **nhóm encoder gửi thêm tệp xác suất**.
- **4.6** Viết `scripts/fit_thresholds.py` (dò ngưỡng theo từng khía cạnh trên tập `val`, ràng buộc số ô
  giảm dưới 5%) + kiểm thử.
- **4.7** Viết `scripts/ensemble.py` (trung bình xác suất N encoder; trọng số bằng nhau hoặc theo
  macro-F1 trên `val`) + kiểm thử.
- **4.8** Viết `scripts/fuse.py` (bảng luật lai theo khía cạnh; chấm bằng engine chấm hiện có) + kiểm thử.
- **4.9** Viết `scripts/vote.py` (bỏ phiếu **từng ô** trên **ba** lượt lấy mẫu; ô chỉ được bỏ phiếu nếu
  đọc được ở ít nhất một lượt; khi hoà thì lấy mã của lượt có **seed nhỏ nhất**) + kiểm thử.
- **4.10** Tạo `data/reports/fusion/` và `data/reports/fusion/inputs/`; viết
  `docs/04_experiments/09_fusion.md`; cập nhật `docs/README.md`.
- **4.11** Tạo **năm cấu hình model mới** (đo `max_length` thật trước khi khai):
  `qwen2.5-0.5b-instruct`, `phobert-large`, `vibert-base-cased`, `cafebert`, `xlm-roberta-base` — model
  cuối cùng ghi nhãn **"đối chứng NGUỒN tiền huấn luyện (đa ngữ, ít tiếng Việt); lưu ý cũng khác bộ tách
  từ nên không phải so sánh sạch một biến"**.
- **4.12** Thêm **5 model** vào `MODELS` trong `src/preprocessing/token_stats.py` ⇒ **đo lại 11 bảng
  token** ⇒ `model_input.csv` **228 → 513 dòng** ⇒ cập nhật `docs/04_experiments/02_model_input.md`
  (đã báo trước ở mục 3.12), cập nhật `docs/04_experiments/04_backlog.md`, chạy lại `ci_checks`.
- **4.13** Chạy `ci_checks` + `unittest` sạch; commit mã và cấu hình **theo từng miền** (không gộp sửa
  lỗi với đổi cấu trúc).

## Mục 5. Tạo thí nghiệm và tài liệu cho các đợt (không cần GPU)

- **5.1** Tạo/sửa **cấu hình và README cho 17 thí nghiệm đợt 7**; mỗi README ghi rõ **"khác `parent`
  đúng một thứ"**. Quy ước `parent` phải theo đúng lối đã dùng ở nhóm 4B:
  - ba mức 0 / 1 / 5 ví dụ là **ba lượt độc lập**, mỗi lượt **`parent: null`** (đúng như `exp002`,
    `exp003`, `exp004` của nhóm 4B) — áp cho cả ba lượt `qwen3-0.6b` (chạy lại) và ba lượt
    `qwen2.5-0.5b-instruct`;
  - các lượt **dẫn xuất** trỏ về **đúng lượt gốc cùng số ví dụ** (ví dụ lượt bật suy nghĩ 0 ví dụ trỏ về
    lượt 0 ví dụ; lượt 1 ví dụ trỏ về lượt 1 ví dụ);
  - README của ba lượt `qwen3-0.6b` chạy lại phải ghi rõ **lí do chạy lại**: khoá `enable_thinking:
    false` đã thêm vào cấu hình model vì lượt cũ (bật suy nghĩ) chỉ đọc được 1,36–3,33%.
- **5.2** Tạo **cấu hình và README cho 9 thí nghiệm đợt 8** (2 lượt `test` có ngưỡng; 3 lượt 0.6B bật
  suy nghĩ; 4 lượt lấy mẫu). **Cập nhật 05/10/2026:** bốn notebook đợt 8 đã tạo - ba lượt 0.6B bật suy nghĩ
  (trần **1985** đo từ lượt DÒ) **cộng MỘT lượt `qwen3-0.6b/prompt-one-turn/exp001`** (bỏ suy luận, chỉ trả
  JSON). Lượt thêm mới trả lời câu "ba lượt 0,6B vướng ĐỊNH DẠNG hay vướng SUY LUẬN" với chi phí rẻ nhất;
  ⇒ **đợt 8 là 8-10 notebook**. Hai lượt `test` có ngưỡng đã chạy xong ở đợt 7.
- **5.3** Tạo **cấu hình và README cho 3 thí nghiệm đợt 9**, mỗi README ghi rõ **rủi ro chạm trần token**
  và cách chạy theo luật ở mục 9.1.
- **5.4** Viết `docs/06_plan/P8_batch7.md`: luật chia mức cho nhánh suy nghĩ, luật kết hợp, thứ tự ưu
  tiên, số phiên, các mốc dừng, **quyết định biểu quyết 3 mẫu**.
- **5.5** `handover/README.md`: bảng notebook đợt 7 gồm **17 dòng**, ghi rõ số đo thật hay ước tính, ghi
  **nhánh suy nghĩ đắt gấp khoảng 5 lần** + luật chống chạm trần, và ghi **nhóm encoder gửi thêm tệp xác
  suất**.
- **5.6** Chạy `ci_checks` + `unittest` sạch; commit.

## Mục 6. Ghim notebook và dựng gói 012 (rồi 013, 014, 015)

- **6.1** `git push` ⇒ **đợi CI GitHub xanh** ⇒ ghim **17 notebook** đợt 7 vào commit xanh đó ⇒ commit
  phần ghim.
- **6.2** Chạy `scripts/build_package.py` ⇒ **gói 012** ⇒ commit sổ gói ⇒ `git push` ⇒ **MỐC DỪNG #2**.
  **Đã thực thi 04/10/2026 (lệch nhỏ, có lí do):** đợt 7 đóng **ba** gói nối tiếp - **012** (23 notebook),
  **013** (chỉ `README.md` sửa) và **014** (sửa `README.md` lần nữa: danh sách gửi lại + hai câu mô tả sai,
  xem `check_present_plan.md` mục 14). Gói sau giải nén **đè lên** gói trước. Vì vậy số gói của các đợt sau
  dịch: đợt 8 = **015**, gói cuối = **016** *(số này nay là LỊCH SỬ - con số đang dùng ở mục 6.3)*.
- **6.3 Đã thực thi 05/10/2026 (đợt 7 nay đóng bốn gói).** Hai lỗi thật được sửa và một cơ chế được thêm
  (xem mục 15 của `check_present_plan.md`), rồi **6 lượt ablation đầu phân loại** được tạo:
  - bản mã **bắt buộc** phải ghim lại, vì Lỗi A (`write_csv` sai thứ tự tham số) làm chết lượt chạy ở
    **dòng cuối** - 4 encoder mới + lượt chạy tiếp của `xlm-roberta-base` đều đã chết vì nó;
  - vậy **14 notebook** được ghim lại: 6 lượt mới + **8 lượt encoder** của đợt 7 (4 encoder mới + 2 lượt
    `val` + 2 lượt `test` có ngưỡng của đợt 8, tất cả đều đi đường encoder);
  - **gói 015** chở 14 notebook ghim lại + `README.md` viết lại + tài liệu của cơ chế mới;
  - **số gói dịch MỘT bậc:** đợt 8 = **016**, gói cuối = **017**. **Cập nhật 05/10/2026 (ba hướng mới, mục 14):**
    đợt 8 đã đóng **016**; tiếp theo là **gói 017** (xử lý đợt 8 + bốn notebook thước nhiễu / đầu phân loại
    theo khía cạnh của đợt 10), rồi **gói 018** nếu hướng 2/3 sửa mã ⇒ **gói cuối = 018**.

## Mục 7. Người dùng chạy đợt 7 (23 notebook, khoảng 11–14 giờ GPU)

- **7.1** Giải nén **lần lượt gói 012, 013, 014 rồi 015** đè lên thư mục Drive (gói sau đè lên gói trước).
- **7.2** Chạy **theo đúng thứ tự** sau (thứ tự này để lượt rẻ và lượt chặn đường chạy trước):
  1. bốn **encoder mới** (15–20 phút mỗi lượt, rẻ nhất và không phụ thuộc gì);
  2. lượt **DÒ** `qwen3-0.6b/prompt-cot/exp004` (chốt trần token cho nhánh suy nghĩ);
  3. ba lượt `qwen3-0.6b/prompt-cot/exp001`, `exp002`, `exp003` (**tắt suy nghĩ**, 0 / 1 / 5 ví dụ);
  4. ba lượt `qwen2.5-0.5b-instruct/prompt-cot/exp001`, `exp002`, `exp003`;
  5. hai lượt **`val`** cho encoder (`phobert-base-v2/lora/exp003`, `visobert/lora/exp003`);
  6. **ba lượt về giá**: `qwen3-4b-instruct-2507/prompt-cot/exp014`, `exp015`, `exp016`;
  7. `qwen3-4b-instruct-2507/prompt-cot/exp017` (lượt **`val`** cho phía LLM, 1,5–2 giờ);
  8. **sáu lượt ablation "đầu phân loại"** (`phobert-base-v2/lora/exp005`, `visobert/lora/exp005`,
     `cafebert/lora/exp002`, `phobert-large/lora/exp002`, `vibert-base-cased/lora/exp002`,
     `xlm-roberta-base/lora/exp002`) - 15–20 phút mỗi lượt, chạy được bất cứ lúc nào sau khi 4 encoder mới
     xong (chúng là `parent` của bốn lượt trong nhóm này).
- **7.3** Điều kiện của **mỗi lượt**: `% đọc được ≥ 95%`; lượt **DÒ** phải ghi lại **p50 / p95 / max số
  token sinh**; lượt bị ngắt thì bấm **Run all** lần nữa để chạy tiếp trong **cùng thư mục kết quả**.
- **7.4** Gửi về cho tôi: **7 tệp nhẹ** của mọi lượt (thêm `predictions.csv` - bước kết hợp dựng đầu vào từ
  nó, và lượt DÒ cần nó để đo p50/p95/p99); **thêm tệp xác suất** cho **12 lượt encoder** (sáu lượt encoder
  của đợt 7/8 cộng sáu lượt ablation đầu phân loại); và **thời gian
  thực tế** của từng lượt.

## Mục 8. Xử lý đợt 7 và chốt luật (không cần GPU)

- **8.1** Chạy `scripts/collect_reports.py` + **đối chiếu từng ô** như ở mục 3.2.
- **8.2** Từ lượt **DÒ**: ghi số đo + **trần token đã chốt** vào
  `experiments/qwen3-0.6b/prompt-cot/exp004/README.md` và
  `docs/04_experiments/08_experiment_rationale.md`; quyết định nhánh suy nghĩ chạy **ba mức hay một mức**.
- **8.3** Đọc kết quả **ba lượt về giá** (`exp014`, `exp015`, `exp016`) và viết kết luận — **không huỷ**
  gì, cả ba đã chạy.
- **8.4** Dò ngưỡng theo khía cạnh trên **hai lượt `val` của encoder** ⇒ **tệp luật JSON** (commit).
  **Đã chốt với người dùng ngày 04/10/2026**: ngưỡng chỉ áp cho **SÁU khía cạnh** (`stayingpower`, `texture`,
  `smell`, `colour`, `shipping`, `packing`); **`price` KHÔNG có ngưỡng** vì `val` có **0 ô** âm ⇒ tệp luật
  ghi `price: null` kèm trường lí do `"val có 0 ô âm"`, và các ô `price` giữ nguyên quyết định của model gốc
  (argmax, không dịch điểm cắt). Kèm theo bốn yêu cầu:
  1. báo cáo phải ghi rõ cột `price` **không đổi** khi thêm ngưỡng (đúng thiết kế, **không** phải lỗi);
  2. điểm macro của bảng ngưỡng trình bày **cả hai cách** - trên 7 khía cạnh và trên 6 khía cạnh có ngưỡng -
     để nhiễu 6 ô của `price` không làm loãng kết luận;
  3. ghi **bằng chứng quét thử** cho `price` vào tệp luật (quét ngưỡng 0,05 → 0,50 trên `val`: F1 không phụ
     thuộc ngưỡng vì không có ô âm nào để bắt) - đây là tài liệu hoá, không phải một ngưỡng;
  4. đọc kết quả `price` của `exp014/015/016` bằng **số lần model gán mã 2 + danh sách 6 ô âm của `test`**
     (đúng/sai từng ô), **không** dùng F1.
  Phương án dự phòng **KHÔNG chọn**: dò ngưỡng `price` trên `train` (15 ô) - quá ít, dễ khớp nhiễu, phá luật
  "ngưỡng dò trên `val`".
- **8.5** Chốt **bảng luật lai** trên `val` (dùng `exp017` + hai lượt `val` của encoder) ⇒ **tệp luật
  JSON** (commit).
- **8.6** Viết kết luận cho nhóm A (0.6B tắt suy nghĩ), nhóm B (Qwen2.5-0.5B), bốn encoder mới, ba lượt
  về giá; kiểm lại luật "khác `parent` đúng một thứ" của từng lượt.
- **8.7** Hai thí nghiệm `test` có ngưỡng **đã tạo sẵn ở gói 012**; mục này nay chỉ còn: tạo **ba thí nghiệm
  0.6B bật suy nghĩ** (trần token biết sau lượt DÒ) ⇒ **ghim** ⇒ **gói 016** ⇒ commit + `git push` ⇒
  **MỐC DỪNG #4**. **Cập nhật 05/10/2026:** đã tạo **BỐN** notebook (ba lượt 0.6B bật suy nghĩ, trần 1985,
  cộng `qwen3-0.6b/prompt-one-turn/exp001` - lượt thứ tư THÊM MỚI để trả lời "0,6B vướng ĐỊNH DẠNG hay vướng
  SUY LUẬN": lượt một-lượt đọc được **99,94%**), ghim `3942144`, **gói 016 đã gửi** (`git push` xong).

## Mục 9. Người dùng chạy đợt 8 (8–10 notebook, khoảng 14–25 giờ GPU)

- **9.1** **Luật chống chạm trần token** nay đã được chính thức hoá thành **luật 23** của
  `docs/00_workflow/02_rules.md` và **CÔNG CỤ HOÁ** bằng `scripts/probe_tokens.py` (05/10/2026) - đọc luật đó
  là đủ, phần dưới là bản nhắc lại cho ba lượt lớn ở đợt 9
  (`qwen3-4b-thinking-2507/prompt-cot/exp001`, `qwen3-8b/prompt-cot/exp001`, `qwen3-14b/prompt-cot/exp001`),
  vì đã gặp lỗi: model bật suy nghĩ ăn hết trần `max_new_tokens` trong khối ` thinking` rồi không in ra JSON.
  Các bước:
  1. chạy **lượt DÒ cỡ 60 mẫu trước** với cùng cấu hình sẽ dùng;
  2. đo **p50 / p95 / max** số token sinh ra;
  3. chọn `max_new_tokens = làm tròn lên (p99 × 1,5)`, và **không được vượt cửa sổ ngữ cảnh** của model;
  4. ở lượt đầy đủ, nếu **trên 5% mẫu chạm trần** thì đánh dấu lượt là **bị cắt** và chạy lại với trần
     cao hơn;
  5. luôn báo cáo **tỉ lệ chạm trần** đặt cạnh `% đọc được`.

  **Đã tự động hoá 05/10/2026:** `scripts/probe_tokens.py` làm đúng các bước trên từ tệp kết quả của lượt DÒ
  (in p50 / p95 / p99 / max số token sinh, kiểm **luật bị cắt** của `docs/04_experiments/metrics.md`, kiểm
  trần không vượt **cửa sổ ngữ cảnh** của model) và chốt trần theo **luật 23a**. Trần đã chốt cho nhánh suy
  nghĩ của Qwen3-0.6B: **`max_new_tokens: 1985`** (p99 1.323 × 1,5, làm tròn lên).
- **9.2** Chạy **hai lượt `test` có ngưỡng**: `phobert-base-v2/lora/exp004`, `visobert/lora/exp004` (gửi
  **7 tệp nhẹ** + **tệp xác suất**).
- **9.3** Chạy **nhánh suy nghĩ đầy đủ**: `qwen3-0.6b/prompt-cot/exp005` (1 ví dụ), và `exp006` (0 ví dụ),
  `exp007` (5 ví dụ) **chỉ khi mỗi lượt ≤ khoảng 3 giờ**; đây là quyết định ở mục 8.2. Mỗi lượt 2–8 giờ,
  chia 2–3 phiên, chạy theo **luật 9.1**.
- **9.4** Chạy **bốn lượt lấy mẫu**: `qwen3-4b-instruct-2507/prompt-cot/exp018`, `exp019`, `exp020` (4-bit,
  seed 1 / 2 / 3) và `exp021` (fp16, seed 1) — khoảng 11 giờ, chia bốn phiên.

## Mục 10. Xử lý đợt 8 (không cần GPU)

- **10.1** Chạy `scripts/collect_reports.py` + **đối chiếu từng ô** như ở mục 3.2.
- **10.2** Báo cáo **ngưỡng**: encoder + ngưỡng so với encoder thuần và so với LLM, trình bày trên **cả
  hai cơ sở**, kèm **số ô** và **`% đọc được`**; ghi rõ ngưỡng áp cho **6 khía cạnh** và **`price` không có
  ngưỡng** (nên cột `price` không đổi - xem mục 8.4), kèm điểm macro tính **cả trên 7 và trên 6 khía cạnh**.
- **10.3** Báo cáo **ensemble** và **lai** trên `test` ở **bảng riêng**, kèm **tệp luật / trọng số** và
  **đầu vào rút gọn đã commit** để tái lập được.
- **10.4** Báo cáo **biểu quyết**: ba điểm riêng lẻ (đo dao động) + điểm của **bản bỏ phiếu 3 mẫu**;
  **kết luận tương tác lượng hoá × lấy mẫu** (so `exp018` với `exp021`, đối chiếu khoảng chênh greedy đã
  biết là **1,17 điểm**); kết luận **chênh so với công bố có vượt nhiễu hay không**.
- **10.5** Cập nhật toàn bộ tài liệu, kết luận, cây thí nghiệm; đóng backlog; nếu có sửa mã thì ghim lại
  và dựng **gói 017**; chạy `ci_checks` + `unittest` + commit + `git push` ⇒ **MỐC DỪNG #5**. **Lưu ý số gói:**
  đợt 8 đã đóng **016**, nên gói đầu tiên sau đây là **017**, và đợt 10 (mục 14) mở tiếp từ **018**.

## Mục 11. Danh mục thí nghiệm theo từng đợt

- **11.1 Đã chạy xong (để đối chiếu)**: `qwen3-4b-instruct-2507/prompt-cot/exp002` → `exp013` (ba mức
  0/1/5 ví dụ với 4-bit lô 8; ba mức fp16 lô 4; ba mức 4-bit lô 4; ba biến thể prompt v2 / v3 / v4),
  `qwen3-4b-instruct-2507/prompt-one-turn/exp001`, `visobert/lora/exp001` → `exp002`,
  `phobert-base-v2/lora/exp001` → `exp002`.
- **11.2 Đợt 7 — gói 012 (rồi 013, 014) + gói 015, 23 notebook, khoảng 11–14 giờ GPU:**

| Thí nghiệm | `parent` | Mục đích | Khác `parent` đúng một thứ | Chi phí |
| --- | --- | --- | --- | --- |
| `qwen3-0.6b/prompt-cot/exp001` | `null` | 0.6B **tắt suy nghĩ**, 0 ví dụ | chạy lại lượt cũ với `enable_thinking: false` | 1–1,5 giờ |
| `qwen3-0.6b/prompt-cot/exp002` | `null` | như trên, 1 ví dụ | chạy lại lượt cũ với `enable_thinking: false` | 1–1,5 giờ |
| `qwen3-0.6b/prompt-cot/exp003` | `null` | như trên, 5 ví dụ | chạy lại lượt cũ với `enable_thinking: false` | 1–1,5 giờ |
| `qwen3-0.6b/prompt-cot/exp004` | `qwen3-0.6b/prompt-cot/exp002` | **DÒ**: suy nghĩ có ra JSON không, dài bao nhiêu ⇒ chốt trần token | bật suy nghĩ + trần 8192 (một cơ chế, hai khoá đi liền nhau) | 20–40 phút |
| `qwen2.5-0.5b-instruct/prompt-cot/exp001` | `null` | model nhỏ **khác họ, không suy nghĩ**, 0 ví dụ | model mới | 20–40 phút |
| `qwen2.5-0.5b-instruct/prompt-cot/exp002` | `null` | như trên, 1 ví dụ | số ví dụ | 20–40 phút |
| `qwen2.5-0.5b-instruct/prompt-cot/exp003` | `null` | như trên, 5 ví dụ | số ví dụ | 20–40 phút |
| `phobert-large/lora/exp001` | `null` | encoder **lớn hơn** có vượt 96,62 của PhoBERT-base không | model mới + `weighted_ce`/`inverse` | 15–20 phút |
| `vibert-base-cased/lora/exp001` | `null` | encoder khác **kho văn bản tiền huấn luyện** | model mới + `weighted_ce`/`inverse` | 15–20 phút |
| `cafebert/lora/exp001` | `null` | thêm một encoder tiếng Việt | model mới + `weighted_ce`/`inverse` | 15–20 phút |
| `xlm-roberta-base/lora/exp001` | `null` | **đối chứng NGUỒN tiền huấn luyện** (đa ngữ, ít tiếng Việt) | model mới + `weighted_ce`/`inverse` | 15–20 phút |
| `phobert-base-v2/lora/exp003` | `phobert-base-v2/lora/exp002` | lượt **`val`** + ghi **xác suất từng ô** | vai trò tập = `val` | ~15 phút |
| `visobert/lora/exp003` | `visobert/lora/exp002` | như trên | vai trò tập = `val` | ~15 phút |
| `qwen3-4b-instruct-2507/prompt-cot/exp014` | `qwen3-4b-instruct-2507/prompt-cot/exp003` | **GIÁ** — định nghĩa lời chê giá gián tiếp trong prompt | chỉ đổi câu chữ prompt | ~2 giờ |
| `qwen3-4b-instruct-2507/prompt-cot/exp015` | `qwen3-4b-instruct-2507/prompt-cot/exp003` | **GIÁ** — ví dụ có ô `price` = mã 2 | chỉ đổi nội dung ví dụ | ~2 giờ |
| `qwen3-4b-instruct-2507/prompt-cot/exp016` | `qwen3-4b-instruct-2507/prompt-cot/exp003` | **CHẨN ĐOÁN**: chỉ hỏi **một** khía cạnh `price` (khác tập ô nên báo cáo riêng) | `task.aspects: [price]` + prompt và ví dụ riêng | 30–40 phút |
| `qwen3-4b-instruct-2507/prompt-cot/exp017` | `qwen3-4b-instruct-2507/prompt-cot/exp009` | lượt **`val`** cho phía LLM (điều kiện của hướng lai) | vai trò tập = `val` | 1,5–2 giờ |
| `phobert-base-v2/lora/exp005` | `phobert-base-v2/lora/exp002` | **ĐẦU PHÂN LOẠI**: để đầu phân loại **HỌC** cùng adapter (bốn lượt LoRA đã chạy bị ĐÓNG BĂNG) | `head.trainable: true` (mặc định `false`) | 15–20 phút |
| `visobert/lora/exp005` | `visobert/lora/exp002` | như trên | `head.trainable: true` | 15–20 phút |
| `cafebert/lora/exp002` | `cafebert/lora/exp001` | như trên | `head.trainable: true` | 15–20 phút |
| `phobert-large/lora/exp002` | `phobert-large/lora/exp001` | như trên | `head.trainable: true` | 15–20 phút |
| `vibert-base-cased/lora/exp002` | `vibert-base-cased/lora/exp001` | như trên | `head.trainable: true` | 15–20 phút |
| `xlm-roberta-base/lora/exp002` | `xlm-roberta-base/lora/exp001` | như trên | `head.trainable: true` | 15–20 phút |

- **11.3 Đợt 8 — gói 016, 8–10 notebook, khoảng 14–25 giờ GPU:**

| Thí nghiệm | `parent` | Mục đích | Khác `parent` đúng một thứ | Chi phí |
| --- | --- | --- | --- | --- |
| `phobert-base-v2/lora/exp004` | `phobert-base-v2/lora/exp002` | encoder trên `test` **có ngưỡng chốt trên `val`** | ngưỡng đóng băng trong cấu hình | ~15 phút - **đã chạy xong 05/10/2026** |
| `visobert/lora/exp004` | `visobert/lora/exp002` | như trên | ngưỡng đóng băng trong cấu hình | ~15 phút - **đã chạy xong 05/10/2026** |
| `qwen3-0.6b/prompt-cot/exp005` | `qwen3-0.6b/prompt-cot/exp002` | lượt **đầy đủ** 0.6B bật suy nghĩ (1 ví dụ) | `enable_thinking: true` + trần **1985** (đo từ lượt DÒ) | 2–8 giờ, 2–3 phiên |
| `qwen3-0.6b/prompt-cot/exp006` *(chỉ khi ≤ ~3 giờ)* | `qwen3-0.6b/prompt-cot/exp001` | như trên ở 0 ví dụ | `enable_thinking: true` + trần **1985** | 2–8 giờ |
| `qwen3-0.6b/prompt-cot/exp007` *(chỉ khi ≤ ~3 giờ)* | `qwen3-0.6b/prompt-cot/exp003` | như trên ở 5 ví dụ | `enable_thinking: true` + trần **1985** | 2–8 giờ |
| `qwen3-0.6b/prompt-one-turn/exp001` | `null` | **vì sao ba lượt 0,6B tắt suy nghĩ không đọc được**: vướng ĐỊNH DẠNG hay vướng SUY LUẬN | prompt `absa_one_turn_v1` + system riêng (0 ví dụ, tắt suy nghĩ) | ~30–40 phút (câu trả lời ngắn) |
| `qwen3-4b-instruct-2507/prompt-cot/exp018` | đỉnh sau đợt 7 (mặc định `exp009`) | **lấy mẫu lần 1** (đo dao động + đầu vào biểu quyết) | `mode: sample`, `seed: 1`, nhiệt độ 0,7 / top_p 0,8 / top_k 20 | 2,5–3 giờ |
| `qwen3-4b-instruct-2507/prompt-cot/exp019` | như trên | **lấy mẫu lần 2** | `seed: 2` | 2,5–3 giờ |
| `qwen3-4b-instruct-2507/prompt-cot/exp020` | như trên | **lấy mẫu lần 3** | `seed: 3` | 2,5–3 giờ |
| `qwen3-4b-instruct-2507/prompt-cot/exp021` | `qwen3-4b-instruct-2507/prompt-cot/exp006` | **đối chứng fp16 khi lấy mẫu** (so `exp018`) | `quantization: null`, `dtype: float16`, `seed: 1` | ~2,5 giờ |

  **Ba việc kết hợp không cần notebook và không tốn GPU**: ensemble encoder (từ tệp xác suất của 4
  encoder mới + 2 lượt `test` có ngưỡng), lai encoder + LLM theo khía cạnh (từ `exp017` và các lượt
  `test`), biểu quyết **3 mẫu** (`exp018` + `exp019` + `exp020`). Luật và trọng số đóng băng trong repo.
- **11.4 Đợt 9 — 3 notebook, khoảng 15–25 giờ**, mở rộng khi người dùng muốn:

| Thí nghiệm | `parent` | Mục đích | Chi phí |
| --- | --- | --- | --- |
| `qwen3-4b-thinking-2507/prompt-cot/exp001` | `null` (model khác) | ở **cùng cỡ 4B**, bật suy nghĩ có hơn không | 8–12 giờ |
| `qwen3-8b/prompt-cot/exp001` | `null` | mốc quy mô lớn hơn (thế hệ 4/2025 — khai báo trung thực) | 4–6 giờ |
| `qwen3-14b/prompt-cot/exp001` | `null` | mốc lớn nhất vừa T4 16 GB | 8–12 giờ |

  Cả ba lượt này **bắt buộc** chạy theo **luật chống chạm trần** (nay là **luật 23**; xem mục 9.1).

- **11.5 Đợt 10 — 4 notebook (đợt A) + 2-6 notebook (đợt B, chạy dần), khoảng 6-12 giờ GPU** — ba hướng mới
  (quyết định ở mục 13.5-13.7, chi tiết ở mục 14):

| Thí nghiệm | `parent` | Mục đích | Khác `parent` **đúng một thứ** (đo được) | Chi phí |
| --- | --- | --- | --- | --- |
| `cafebert/lora/exp003` | `cafebert/lora/exp001` | **THƯỚC NHIỄU** cho lượt gốc đem so công bố (97,67) | `decoding.seed: 7` (lượt encoder chạy `greedy`, khoá này là **hạt giống HUẤN LUYỆN**) | 15–20 phút |
| `cafebert/lora/exp004` | `cafebert/lora/exp002` | thước nhiễu cho vế **ĐẦU PHÂN LOẠI HỌC** | `decoding.seed: 7` | 15–20 phút |
| `vibert-base-cased/lora/exp003` | `vibert-base-cased/lora/exp001` | thước nhiễu cho cặp có **Δ ÂM (−0,15)** — cặp dễ bị nhiễu nhất | `decoding.seed: 7` | 15–20 phút |
| `phobert-base-v2/lora/exp006` | `phobert-base-v2/lora/exp002` | **ĐẦU PHÂN LOẠI theo khía cạnh** (khía cạnh vào ĐẦU VÀO, không qua ô nhớ prompt) | `head.aspect_marker: true` (mặc định `false`) | 15–60 phút |
| 6 lượt một-khía-cạnh (**chỉ chạy 2 trước**: `price`, `smell`) | `qwen3-4b-instruct-2507/prompt-cot/exp003` | **HAI TẦNG theo khía cạnh**: lượt LLM một-khía-cạnh gộp với encoder | `task.aspects: [<một khía cạnh>]` + cặp prompt/system MỚI | ~2 giờ/lượt |

  **Đợt 10 KHÁC ba việc đã làm** (đừng đọc nhầm): (a) "đo dao động bằng ba lượt lấy mẫu" (mục 11.3) là thước
  nhiễu của **đường prompt**, KHÔNG dùng được cho encoder; (b) mục 8.5 ("bảng luật lai") dùng đúng **một lượt
  LLM 7 khía cạnh**, còn hướng 3 chạy **thêm lượt LLM một khía cạnh**; (c) hướng 2 **thêm một DÒNG MỚI** vào
  bảng dấu vết của đầu phân loại, không thay đầu phân loại hiện có. Lượt một-khía-cạnh **khác tập ô** nên
  **báo cáo riêng**, không trộn bảng `paper` (tiền lệ: `exp016`).

## Mục 12. Việc để ngỏ (ghi lại để không quên)

- **12.1** Danh sách việc mở: `Qwen/Qwen3-4B-Thinking-2507` (chỉ khi nhánh suy nghĩ 0.6B tỏ ra có ích) ·
  `Qwen/Qwen3-8B` · `Qwen/Qwen3-14B` (4-bit, **khác thế hệ**) · `Qwen3-30B-A3B-Instruct-2507` **không vừa
  T4 16 GB** · ViTASA · trang HTML cho `token_stats` · writer `state_dict` · tag `sys-<mã băm>` · QLoRA
  (cần ≥ 24 GB) · tiêu chí hoàn thành P7 · đo dao động diện rộng · hiệu ứng bộ tách từ · thăng cấp luật
  lai thành một `method` · trọng số lớp theo từng khía cạnh · **lập tập chẩn đoán giá** (200–300 review có
  nhắc giá, gán nhãn "chê giá / khen giá / không nhắc" theo quy tắc viết TRƯỚC, lưu tách hẳn ở
  `data/reports/price_probe/`, không trộn vào bảng `paper`) - cách duy nhất để có thước đo thật cho `price`;
  việc của người, 0 GPU, **người dùng chốt để làm SAU, chưa đưa vào kế hoạch đợt này** · và **hợp nhất hai
  tệp `present_plan.md` + `check_present_plan.md` vào `docs/06_plan/P9_batch7.md`** khi kết thúc đợt (đề
  xuất, **chờ người dùng duyệt**). **Cập nhật 05/10/2026:** hai việc "đo dao động diện rộng (đường encoder)"
  và "đầu phân loại theo khía cạnh / hai tầng theo khía cạnh" nay đã **rời danh sách để ngỏ** và thành **đợt 10**
  (mục 14, bảng ở mục 11.5); "thăng cấp luật lai thành một `method`" vẫn để ngỏ nhưng **gần** hướng 3, phải
  tách rõ khi viết.
- **12.2** MLflow: experiment `sentimentx-absa` đã bị xoá mềm trên DagsHub nên 23 lượt không được theo
  dõi; người dùng đã quyết **không khôi phục**. Muốn theo dõi lại thì tạo experiment mới trên DagsHub —
  ghi lại để biết, **chưa làm**.

## Mục 13. Điều còn chờ người dùng trả lời (kèm mặc định tôi sẽ dùng)

- **13.1** Giữ `xlm-roberta-base` làm đối chứng nguồn tiền huấn luyện (có dán nhãn cảnh báo "cũng khác
  bộ tách từ") hay bỏ để tiết kiệm 20 phút? → *Mặc định: GIỮ.*
- **13.2** Commit đầu vào cho bước kết hợp (xác suất từng ô + dự đoán từng ô, khoảng 200–450 KB mỗi
  model) vào `data/reports/fusion/inputs/` để con số lai và ensemble tái lập được ngay từ repo? →
  *Mặc định: CÓ.*
- **13.3** Ngưỡng cửa `% đọc được ≥ 95%` để gắn `valid: false` — chỉ **đánh dấu**, dữ liệu giữ nguyên,
  không xoá? → *Mặc định: 95%, có đánh dấu.*
- **13.4** Đợt 9 (3 thí nghiệm lớn: `qwen3-4b-thinking-2507`, `qwen3-8b`, `qwen3-14b`) có làm trong đợt này
  không? → *Mặc định: ĐỂ NGUYÊN, không tạo bây giờ* (kế hoạch vốn ghi đợt 9 là "mở rộng, chạy khi muốn").
  Tạo 3 config model + đo lại **19 bảng token** (~18 phút, không cần GPU) là giá phải trả nếu chọn "làm luôn".

**Ba quyết định ĐÃ CHỐT ngày 05/10/2026 (luật 1.7 - ghi lại vì đã đổi so với tệp này):**

- **13.5 CHỐT — thước nhiễu encoder làm theo phương án (a): dùng thẳng khoá `decoding.seed`** (khoảng **0 dòng
  mã**), chạy lại **P2 = 3 lượt**: `cafebert/lora/exp003` (thước nhiễu cho lượt đem so công bố),
  `cafebert/lora/exp004` (cho vế đầu phân loại HỌC), `vibert-base-cased/lora/exp003` (cho cặp có Δ ÂM).
  Cái giá đã biết trước: phải **sửa một câu chú thích** của khoá này (mục 14.2) vì câu hiện tại nói `greedy`
  không dùng khoá đó - chỉ đúng cho đường prompt.
- **13.6 CHỐT — hạt giống dùng để chạy lại = `decoding.seed: 7`** (khác mặc định 42, nên hạt giống huấn luyện
  thật sự đổi và lượt mới rơi vào **thư mục kết quả mới**).
- **13.7 CHỐT — ghim vào HEAD** (bản mã hiện tại) chứ không lùi về commit `59579e5` của các lượt gốc. Điều kiện
  bắt buộc để không phạm luật "khác `parent` đúng một thứ": phải dán **kết quả RỖNG** của
  `git diff --stat 59579e5 HEAD -- src/training src/experiments src/preprocessing src/evaluation` vào `README.md`
  của từng lượt mới (đã kiểm: rỗng, nên mã encoder **không đổi** giữa hai commit).

## Mục 14. Đợt 10 — ba hướng mới (thước nhiễu encoder · đầu phân loại theo khía cạnh · hai tầng theo khía cạnh)

Ba hướng này đã được người dùng đồng ý (mục 13.5-13.7). Cả ba dựa trên một **tiền lệ có sẵn** trong kế hoạch:
`qwen3-4b-instruct-2507/prompt-cot/exp016` là lượt **chẩn đoán** hỏi ĐÚNG một khía cạnh `price`, và vì **khác
tập ô** nên được **báo cáo riêng**, không trộn vào bảng `paper`.

- **14.1 (không cần GPU) Vệ sinh sổ sách sau hai lượt vừa xong.** Chạy `scripts/collect_reports.py` (5 nhóm
  bảng nay có hai lượt mới); sửa **ba chỗ ghi sai 16.149** thành **21.525** (`experiments/cafebert/lora/exp002/
  config.yaml` dòng "= 16.149", `README.md` cùng lượt, và bảng mục 15 của `check_present_plan.md`) — CafeBERT
  rộng **1.024** ẩn, ĐO ĐƯỢC: `7.132.181 − 7.110.656 = 21.525`; ghi kết quả hai lượt vào
  `08_experiment_rationale.md` (§2b nay **6/6** cặp, cafebert **+0,21**) và **§5.3 mới** (lượt `prompt-one-turn`
  của 0,6B: **99,94%** đọc được), cây ở `07_evolution.md`, `handover/README.md` (5/6 → 6/6); commit **bằng
  chứng RỒI commit tài liệu - HAI commit riêng** (luật 1.1); `ci_checks` + `unittest` + `git push`.
- **14.2 (không cần GPU) Ghi rõ ngữ nghĩa khoá `decoding.seed` cho đường ENCODER** ở
  `configs/experiments/evaluation.yaml` và `docs/05_config/05_experiments_shared.md`: với lượt encoder (chạy
  `greedy`), khoá này là **hạt giống HUẤN LUYỆN** (khởi tạo trọng số đầu phân loại, dropout, xáo trộn dữ liệu),
  KHÔNG phải hạt giống lấy mẫu — câu chú thích hiện tại ("`greedy` KHÔNG dùng tới khoá này") chỉ đúng cho
  **đường prompt**. Đây là cái giá của phương án (a): **0 dòng mã**, **1 lần sửa câu chữ**.
- **14.3 (không cần GPU) Tạo bốn notebook đợt 10** (bảng ở mục 11.5). Mỗi `README.md` phải ghi: hỏi gì; khác
  cha **ĐÚNG MỘT khoá**; đây là **thước nhiễu**, không phải lượt lấy điểm cao; và **BẰNG CHỨNG một-biến** =
  dán kết quả RỖNG của lệnh
  `git diff --stat 59579e5 HEAD -- src/training src/experiments src/preprocessing src/evaluation`.
  Bằng chứng này là **bắt buộc**: lượt thước nhiễu khác cha ở commit ghim, nên phải chứng minh mã KHÔNG đổi thì
  luật "khác `parent` đúng một thứ" (mục 5.1) mới đứng vững.
- **14.4 (không cần GPU) Ghim bốn notebook vào HEAD** (đã có bằng chứng `git diff` RỖNG) ⇒ `ci_checks` xanh ⇒
  commit ghim ⇒ đẩy ⇒ dựng **gói 017** ⇒ commit sổ gói ⇒ `git push`.
- **14.5 (người dùng chạy) Bốn lượt, khoảng 1,5-2 giờ GPU**: ba lượt thước nhiễu + một lượt `aspect_marker`.
  Mỗi lượt encoder gửi **8 tệp** (thêm tệp xác suất) như mục 7.4.
- **14.6 (không cần GPU) Đo BIÊN NHIỄU cho đường encoder** và viết vào `06_lora_encoder.md` +
  `08_experiment_rationale.md` §2b. Trả lời thẳng hai câu: (a) chênh **+0,21** (và +0,52) của nhóm đầu phân
  loại có **nằm NGOÀI** biên nhiễu không; (b) chênh **−0,15** của `vibert-base-cased` có **nằm TRONG** biên
  nhiễu không. Nếu biên ≥ khoảng 0,3 điểm thì §2b phải viết lại: **"+0,67 → +1,16" là tín hiệu yếu, chưa tách
  được khỏi nhiễu**. Commit.
- **14.7 (không cần GPU, SỬA MÃ) Hướng 2 - đầu phân loại theo khía cạnh.** Khai `head.aspect_marker: false` ở
  `configs/experiments/training.yaml` (KHÔNG đặt mặc định trong mã — luật 1.4), đọc **chặt** như
  `head.trainable` (`bool("flase")` là `True`); `src/training/lora.py` đưa vector khía cạnh vào đầu vào của đầu
  phân loại (7 lượt encode + review), **đầu ra vẫn 7 × 3**; ghi cơ chế vào `run.log` (dòng `[CONFIG]`),
  `run_meta.json`, thẻ MLflow; test mới; thêm **một DÒNG MỚI** vào bảng dấu vết của `06_lora_encoder.md`.
- **14.8 (người dùng chạy) MỘT lượt rẻ nhất trước** (`phobert-base-v2/lora/exp006`, 15-60 phút) để xem cơ chế
  mới có TÁC DỤNG không, rồi mới quyết có lan ra năm model kia hay không.
- **14.9 (không cần GPU, SỬA MÃ) Hướng 3 - hai tầng theo khía cạnh.** Tạo **sáu cặp prompt + system MỚI** (mỗi
  cặp một khía cạnh) — KHÔNG sửa cặp prompt cũ (luật 1.4: cặp prompt đã dùng là **bất biến**); cập nhật danh
  sách tập-đóng trong `tests/experiments/test_prompts.py` (không thì `ci_checks` đỏ); thêm hàm gộp vào
  `src/evaluation/fusion.py` + đường gọi ở `scripts/fuse.py` + test.
- **14.10 (không cần GPU) CHỐT LUẬT GỘP TRƯỚC KHI CHẠY** (luật 1 + luật 11 của `02_rules.md`): khung ô lấy từ
  **encoder**; khi encoder nói "có nhắc" mà lượt một-khía-cạnh nói "không nhắc" thì lấy **ai** — ghi vào
  `README.md` của lượt mới. **Không** được chọn luật sau khi đã thấy kết quả.
- **14.11 (người dùng chạy) HAI lượt một-khía-cạnh** (`qwen3-4b-instruct-2507` cho `price` và `smell`,
  ~4-5 giờ GPU) ⇒ gộp ⇒ **bảng RIÊNG**, không trộn bảng `paper` (tiền lệ: `exp016`).
- **14.12 (không cần GPU) Chốt sổ**: cập nhật `present_plan.md`, `check_present_plan.md`,
  `docs/06_plan/README.md` (hàng P8b), `handover/README.md`; dựng **gói 018** (nếu hướng 2/3 sửa mã);
  `ci_checks` + `unittest` + commit + `git push` ⇒ **MỐC DỪNG #6**.






