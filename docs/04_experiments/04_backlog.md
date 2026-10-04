# Việc ĐÃ BIẾT nhưng CHƯA LÀM (backlog)

> Đọc file này khi: chọn việc làm tiếp.
> Liên quan: `docs/06_plan/README.md`, `docs/04_experiments/01_models.md`

File này ghi lại những việc dự án đã nhận diện được nhưng **cố ý chưa làm** trong đợt
này, để lần sau không quên và để người đọc tài liệu biết chỗ nào còn thiếu (thay vì
tưởng đã xong). Mỗi mục ghi: việc gì, vì sao hoãn, và làm tiếp thì bắt đầu từ đâu.

Nguyên tắc: chỉ ghi việc **có căn cứ** (đã đo, đã đọc mã nguồn, đã thử) - không ghi ý
tưởng chung chung.

## 1. ViTASA - gác lại, chưa đưa vào thực nghiệm

**Việc:** đưa ViTASA vào cùng bảng so sánh với PhoBERT / ViSoBERT / Qwen3.

**Vì sao hoãn:** repo `kh4nh12/ViTASA` hiện chỉ có `LICENSE`, `README.md` và 3 file
`.jsonl` - không có mã model, không có checkpoint, không có script huấn luyện. Hugging
Face Hub cũng không có dataset/model nào tên `vitasa`. Nghĩa là chưa có gì chạy được:
viết thêm code chỉ là suy đoán, không phải tái lập.

**Làm tiếp từ đâu:** khi repo có checkpoint -> viết `src/preprocessing/vitasa.py` theo
đúng định dạng đầu vào của nó (khung đã có: `to_absa_tuples`, `to_label_ids`,
`describe_format`), rồi thêm một dict vào `MODELS` trong `src/preprocessing/token_stats.py`
(`MODEL_NAME`, `tokenizer`, `encode`, `words`, `info`) để đo được độ dài
input như 4 model còn lại. Docstring của `vitasa.py` ghi sẵn 4 bước.

## 2. Chạy Qwen3 theo hướng PROMPT (prompt + CoT) - ĐÃ DỰNG (đợt 2)

*Cập nhật 25/09/2026:* ba mức ví dụ của công bố đã thành ba thí nghiệm
(`qwen3-4b-instruct-2507/prompt-cot/exp002` 0 ví dụ, `exp003` 1 ví dụ, `exp004` 5 ví dụ) cạnh hai lượt
LoRA cho encoder. Cả năm chấm trên tập `test` và đã ghim cùng một bản code, chờ máy GPU của Colab để ra
số. Phần mô tả dưới đây giữ nguyên vì nó giải thích VÌ SAO đi hướng này.

*Cập nhật 29/09/2026:* hướng prompt nay có **bảy** thí nghiệm trên bản 4B (ba mức ví dụ 4-bit
`prompt-cot/exp002..004`, prompt MỘT LƯỢT `prompt-one-turn/exp001`, và ba lượt đối chứng KHÔNG lượng hoá
`prompt-cot/exp005..007` của đúng ba mức ví dụ đó), cộng **ba** lượt `qwen3-0.6b/prompt-cot/exp001..003`
cho model thứ tư - model nhỏ, cùng tokenizer, để đo khoảng cách do quy mô. Mười lượt này cùng hai lượt
LoRA cho encoder chấm trên cùng tập `test` và ghim cùng một bản code; xem `docs/06_plan/P7_rerun.md` mục 2
cho lý do của từng nhóm.

**Việc:** cho Qwen3 trả lời tập test bằng prompt (zero-shot / few-shot / CoT), rồi đo tỉ
lệ JSON hợp lệ và F1. **Không fine-tune.**

**Vì sao đi hướng này:** Qwen3 là LLM 4B tham số, full fine-tune cần ~64-80 GB VRAM (chỉ
riêng trọng số ở bf16 đã 8 GB) nên **không thể** trên GPU 6 GB của máy này. Hướng đúng bản
chất phép so sánh của dự án là dùng nó như model đa năng bằng prompt - tức "LLM thì thử
prompt + CoT", còn PhoBERT (135M) và ViSoBERT (~108M) thì **huấn luyện bằng LoRA** (encoder
gốc đóng băng, chỉ học adapter hạng thấp cộng một đầu phân loại riêng cho mỗi khía cạnh) -
xem `docs/04_experiments/06_lora_encoder.md`.

**Cần gì:** `pip install torch` (bản CUDA phù hợp) + lượng hóa 4-bit lúc CHẠY
(`bitsandbytes`) - chỉ để model 4B vừa 6 GB VRAM, **không phải** huấn luyện - rồi dùng
`qwen.build_inputs()` (đã bọc chat template sẵn).

**QLoRA là phương án TUY CHỌN, không bắt buộc:** chỉ đặt ra khi kết quả prompt + CoT kém và
muốn trả lời thêm câu hỏi "fine-tune LLM có hơn prompt không". Nếu làm thì phải lên kế
hoạch riêng (QLoRA trên 6 GB rất chật; phương án thay thế là GPU 16 GB trên Colab/Kaggle).

## 3. Prompt CoT và few-shot - đã viết, đã ĐO input, và đã có hạ tầng để chạy

**Việc:** thêm prompt chain-of-thought / few-shot cho Qwen3, biết trước nó tốn bao nhiêu
token, và chạy model để biết chất lượng.

**Đã xong (đợt này):**

- Prompt cho Qwen3, đủ để tách riêng ảnh hưởng của "có suy luận" và "bao nhiêu ví dụ":
  `absa_one_turn_v1` (một lượt, 0 ví dụ - bản CHÍNH THỨC, thí nghiệm `prompt-one-turn/exp001`),
  `absa_cot_zeroshot_v1` (0 ví dụ), `absa_cot_1shot_v1` (1 ví dụ), `absa_cot_v1` (2 ví dụ),
  `absa_cot_5shot_v1` (5 ví dụ - mức của công bố), và `absa_direct_v1` (bản một lượt CŨ, không tách
  system prompt; giữ lại để tra số liệu đã đo, không thí nghiệm nào dùng).
- Khối **system prompt** của mọi prompt nằm ở FILE RIÊNG (`configs/prompts/system/`); không viết câu
  hệ thống vào file prompt (xem `docs/05_config/06_experiment.md`).
- **Chi phí input đã đo** (train): 257,50 (một lượt) -> 372,50 (0 ví dụ) -> 721,50 (1 ví dụ) ->
  990,50 (2 ví dụ) -> 1.877,50 (5 ví dụ) token/review. Mỗi ví dụ khoảng 287-305 token. Ngưỡng
  1280 đủ cho các bản tới 2 ví dụ (dài nhất 1.235 token) nhưng **KHÔNG** đủ cho bản 5 ví dụ (dài
  nhất 2.122 token, tức 100% review bị cắt mất phần đuôi) - nên Qwen3-4B đặt
  `preprocess.max_length: 2304`. Bảng đầy đủ ở [02_model_input.md mục 4.2](02_model_input.md).
- **Sửa một lỗi định dạng trong prompt CoT:** phần mô tả schema cũ viết
  `{"khía cạnh": mã, ...}` - JSON KHÔNG hợp lệ và mâu thuẫn với chính các ví dụ ngay trên
  nó, nên model có thể copy nguyên si. Đã thay bằng `{example}` (JSON hợp lệ, sinh theo
  đúng bộ khía cạnh của phiên bản dữ liệu).
- **Truy vết bộ ví dụ:** `prompt_sha` KHÔNG đổi khi đổi số ví dụ (nó chỉ tính nội dung file
  prompt), nên `prompts.examples_info()` trả thêm `examples_sha` và tên file CSV có `ex-<sha4>`
  kể cả khi chạy bằng cấu hình dự án. Không có mã đó thì hai thí nghiệm (1 ví dụ vs 2 ví dụ)
  mang cùng một dấu vết và ghi đè lên nhau.
- **Kiểm rò rỉ:** `run_check_examples.py` đối chiếu từng ví dụ với cả 3 split. Phép kiểm
  này đã **bắt được lỗi thật**: ví dụ 1 (bản cũ) trùng cụm 6 từ với val/test
  (`chất son mịn không bị khô`); hai ví dụ đã được viết lại, hiện cụm trùng dài nhất chỉ
  3-4 từ (các cụm thông dụng).
- **Hạ tầng chạy model:** `src/evaluation/{parse,metrics,runner}.py` + notebook của thí nghiệm
  (đọc khối `KẾT QUẢ:`, đếm tỉ lệ đọc được, chỉ số theo khía cạnh, ghi kết quả theo phiên
  bản) và `tests/` (27 test cho bộ đọc + chỉ số, chạy không cần GPU).

**Đã có kết quả chất lượng (đợt này):** bốn cấu hình prompt chạy trên cùng tập con 100
review của `val` (greedy, 4-bit): `absa_direct_v1` **90,86** acc macro / F1 nhắc 0,891 **46**
token sinh/review **104 s**; `absa_cot_zeroshot_v1` **91,43** / 0,884 / 233 token /
564 s; `absa_cot_1shot_v1` 89,29 / 0,825 / 217 token / 676 s; `absa_cot_v1` 91,14
/ 0,870 / 217 token / 739 s. Kết luận: **CoT không thắng rõ** (chênh lệch nằm trong khoảng
nhiễu của 700 ô) nhưng đắt gấp ~5 lần ở output và ~5-7 lần thời gian; CoT chỉ **đổi kiểu
lỗi** (thận trọng hơn: precision cao hơn, recall thấp hơn). Bảng đầy đủ + hạn chế:
[03_training_eval.md mục 6](03_training_eval.md).

**Còn thiếu:**

1. **Tăng cỡ tập con** (300-500 review) và **đo dao động** (`--sample`) - chưa làm, vì một
   lượt CoT 100 review đã tốn 10-12 phút GPU.
2. ~~**So với 3 encoder**: PhoBERT (× số bộ tách từ) và ViSoBERT vẫn chưa có script huấn luyện.~~
   **ĐÃ LÀM (đợt 2, 25/09/2026):** `src/training/lora.py` (registry `TRAINERS`) và `src/experiments/encoder_run.py`,
   hai thí nghiệm `visobert/lora/exp001` + `phobert-base-v2/lora/exp001`. Việc còn lại là NHÂN với số bộ
   tách từ, ghi ở mục 4 (cần GPU).
3. **Self-consistency** (lấy mẫu nhiều lần rồi bỏ phiếu) là bước mở rộng tự nhiên của CoT
   (Wang et al., 2022) - chưa làm; hạ tầng đã có `--sample --seed`.

Lưu ý Qwen3 Instruct-2507 là bản **non-thinking** (không sinh `<think>`), nên "CoT" ở đây là
CoT do prompt yêu cầu, không phải chế độ của model. Bộ đọc vẫn ĐẾM số câu trả lời có
`<think>` thay vì giả định là không có.

## 4. Tác động của việc tách từ lên KẾT QUẢ CUỐI - chưa làm

**Việc:** trả lời "tách từ giúp bao nhiêu" ở mức F1, không chỉ ở mức số token.

**Đã xong:** số liệu token của cả 4 bộ trên PhoBERT (bảng ở
[02_model_input.md mục 4.1](02_model_input.md)): bộ chính chủ cho input ngắn nhất (29,96
token/review so với 33,67 khi không tách từ) và ít `<unk>` hơn hẳn (3,88% so với 5,28%);
`pyvi` bám sát (+1,0%). ViSoBERT và Qwen không đổi một con số nào ở cả 4 file - đúng như
thiết kế, chỉ PhoBERT nhận `--segmenter`.

**Còn thiếu:** huấn luyện PhoBERT với từng bộ tách từ rồi so F1. Vì tokenizer không đổi,
khác biệt thật sự chỉ hiện ra ở bước này.

## 5. Task nhỏ đã biết

- **JDK 11 dự phòng:** nếu VnCoreNLP gặp lỗi lạ với JDK 17 trên máy khác, chạy
  `powershell -ExecutionPolicy Bypass -File scripts\setup\setup_java.ps1 -Major 11 -Force`
  (jar VnCoreNLP là bản 2020; tài liệu của gói chỉ yêu cầu Java 1.8+).
- **Báo cáo HTML cho tiền xử lý cho model:** `run_token_stats.py` mới ghi CSV + in console, chưa có
  `*_result.json` để `build_report.py` vẽ như EDA/pipeline. Chưa làm vì phép đo còn đang
  thay đổi (prompt, bộ tách từ) nên chưa chốt được metric để trình bày.
- **`transformers` chưa ghim phiên bản:** `requirements.txt` để trôi nổi. Khi chốt kết
  quả cuối nên ghim, vì tokenizer có thể đổi giữa các bản và như vậy số token sẽ đổi.
- **Test tự động mới có một phần:** `tests/` phủ bộ đọc kết quả, chỉ số, đường dẫn, cấu hình, ghim
  code, prompt, resume, báo cáo (`python -m unittest discover -s tests`) - đúng những chỗ mà một lỗi
  sẽ làm sai toàn bộ điểm số. CI chạy test này cùng 7 kiểm tra cấu trúc mỗi lần đẩy lên nhánh
  `experiment` (xem [00_workflow/03_ci.md](../00_workflow/03_ci.md)), nên lỗi loại này không lọt qua
  được nữa. `runner.py` **không có test** vì nó cần GPU + model 8 GB - bù lại, các quyết định ở đó
  (padding_side, chat template, cắt phần đã sinh) đều được kiểm bằng script chạy thật trong quá
  trình làm.
  **Cập nhật 27/09/2026:** `runner.py` nay CÓ test cho hai quyết định KHÔNG cần GPU
  (`tests/evaluation/test_runner.py`: `chat_template` rỗng, và bỏ phần đệm bên trái khi dựng lại cột `prompt`).
  Phần `generate()` (cắt đúng đoạn model sinh ra) vẫn phải kiểm bằng lượt chạy thật: model giả chỉ
  chứng minh được phép cắt, không chứng minh phép cắt đó đúng với đầu ra của model.
- **Bài học về test (đã trả giá):** lỗi hoán vị FP/FN trong `metrics._binary_counts` lọt qua
  27 test đầu tiên vì các ca test lúc đó **đối xứng** (hoặc chỉ có một loại lỗi), mà F1 lại
  đối xứng nên không đổi. Nó chỉ lộ ra khi đối chiếu bảng điểm với **số đếm thô** (cấu hình
  nêu thừa nhiều nhất lại được báo precision cao nhất). Từ nay: hàm chấm điểm phải có ca test
  **bất đối xứng** (chỉ dương tính giả / chỉ âm tính giả), và con số tổng hợp phải được kiểm
  chéo với số đếm. Kết quả đã ghi được chấm lại từ file dự đoán (không cần GPU).
- ~~**Cột đếm `<unk>`:** bảng `token_stats` chỉ có `% token <unk>` (đã làm tròn), nên muốn nói
  "giảm bao nhiêu token `<unk>`" thì phải đo bằng script riêng - đã phải làm vậy một lần
  (21.886 -> 14.302 token `<unk>` trên train). Thêm cột đếm sẽ không phải suy ngược từ tỉ lệ.~~
  **ĐÃ LÀM (27/09/2026):** cột `số token <unk>` đứng cạnh `% token <unk>` trong `token_stats.COLUMNS`
  (`feat(preprocessing): count unk tokens instead of only the share`). Hai giá trị `-` khi tokenizer
  không khai báo token `<unk>` (Qwen), KHÁC với `0`.
- ~~**Cơ chế của việc tách từ chưa được lưu thành số liệu:** đã đo trong phiên làm việc là
  "mảnh/đơn vị 1,618 -> 1,445" cùng vài ca cụ thể (`Công_dụng` = 1 token so với `Công` +
  `dụng` = 2; `dụng:` = 3 mảnh so với `dụng` + `:` = 2), nhưng **chưa ghi vào file/doc nào**
  nên muốn trích dẫn lại thì phải đo lại. Nên đưa thành một script nhỏ hoặc một mục riêng
  trong [02_model_input.md](02_model_input.md).~~
  **ĐÃ LÀM (27/09/2026):** mục 4.1.1 của [02_model_input.md](02_model_input.md) có bảng cơ chế đo lại
  được (ba ca, kèm lệnh đo) và ba file số liệu `token_stats__…__seg-{vncorenlp,pyvi,none}.csv`
  (`docs(experiments): record the segmentation effect with reproducible numbers`). Con số "mảnh/đơn vị"
  cũ không tái lập được nên đã thay bằng cột `subword / từ` của chính bảng: 1,55 khi không tách từ so với
  1,38 khi dùng bộ chính chủ.
- **Ví dụ few-shot dạng LƯỢT hội thoại:** hiện `{examples}` là MỘT khối văn bản nằm trong
  lượt người dùng. Muốn ví dụ thành các cặp `[USER]`/`[ASSISTANT]` thật (cách chat model
  thường được dạy) thì cần thêm một khối hoặc ô nhớ mới cho loader prompt.
- ~~Mục lục có thể trỏ tới file báo cáo đã bị xoá~~ - **đã xử lý:** `versioning.prune_missing()`
  bỏ những dòng có `report` không còn tồn tại, và `record()` gọi hàm này mỗi lần ghi nên mục
  lục tự dọn (đã dùng để dọn 2 dòng trỏ tới các lần chạy thử `n4`/`n8`). Có test riêng:
  `tests/core/test_versioning.py` (4 ca, dùng manifest trong thư mục tạm, không đụng mục lục thật).

## 6. Chưa làm so với kế hoạch refactor (ghi 25/09/2026)

Rà lại toàn bộ kế hoạch trong `docs/06_plan/` so với code đang có. Những việc dưới đây là CHƯA LÀM
hoặc CỐ Ý LÀM KHÁC, ghi lại để không ai đọc kế hoạch mà tưởng đã xong.

| Việc | Trạng thái | Ghi chú |
| ---- | ---------- | ------- |
| Máy kiểm "kết quả trước merge" (`valid`, `invalid_reason`, `comparable` trong `experiment_registry`) | **ĐÃ LÀM 27/09/2026** | `feat(reports): mark runs that are not on the pinned branch`. `valid` hỏi git qua `src/workflow/repo.py` (`merge-base --is-ancestor` so với `origin/<nhánh>` ghi trong `run_meta.json`) - không phải `git rev-list`; `comparable` so cơ sở đo (dữ liệu, không gian nhãn, neutral, split, bộ chấm) với lượt CHUẨN (lượt `FINISHED` sớm nhất); `invalid_reason` gộp lý do. Không có git thì cả hai cột ghi `chưa rõ`, KHÔNG ghi `no` |
| `dataset_registry` có cột `parent` + changelog người đọc (`docs/01_dataset/changelog.md`) | **ĐÃ LÀM 27/09/2026** | `feat(reports): show dataset lineage and count records, not lines`: cột `parent` (không khai thì ghi "sinh từ dữ liệu gốc", không để ô trống) và `docs/01_dataset/changelog.md` là bản người đọc. Cùng commit đó sửa một lỗi thật: bảng ĐẾM DÒNG thay vì đếm BẢN GHI, nên ghi `test=2271` trong khi `eval_lock` ghi 1.518 |
| `src/sources/` (registry `SOURCE_KINDS`) và `src/models/` (registry `ADAPTERS`) | **ĐÓNG - làm khác có chủ ý** | `kind` (`raw`/`dataset`) kiểm trong `src/core/dataset.py`; model sinh nạp ở `src/evaluation/runner.py`, model encoder ở `src/preprocessing/`. Chức năng tương đương, khác chỗ đặt: hai thư mục registry chỉ để gom chỗ ĐẶT, mà chỗ đặt đã có chủ. Không làm nữa |
| `run_rescore_eval.py` và `config.MODEL_EVAL_REPORT_DIR` | **ĐÃ BỎ 25/09/2026** | Trước đó giữ có chủ ý làm "đường chạy tay". Nay MỌI kết quả đều thuộc một thí nghiệm: `experiments/<model>/<method>/<expNNN>/results/<hash8>/`, thiếu định danh thí nghiệm là lỗi. Muốn tính lại điểm thì chạy lại thí nghiệm (xem [05_predictions.md](05_predictions.md) §5) |
| `nbstripout` cài trên từng máy | **ĐÃ CẤU HÌNH 27/09/2026** | `chore(git): strip notebook outputs with nbstripout`: `.gitattributes` khai bộ lọc, máy nào cài `nbstripout` thì git tự bỏ output khi commit; kiểm 3 của CI vẫn là chốt cuối |
| `mlflow_tags` đủ 8 nhãn và `artifacts` có `plots` | **ĐÃ LÀM 27/09/2026** | `feat(tracking): carry the eight mlflow tags and upload the plot`: nhãn `model`, `method`, `exp_id`, `dataset`, `version_id`, `split`, `repo_sha`, `config_sha256`; phát hiện thêm một lỗi - `resolve_tags` chỉ tra khoá mức ngoài nên `method`/`exp_id` (nằm trong khối `experiment`) bị BỎ ÂM THẦM, nay tra cả khối đó. `artifacts` thêm `plots/accuracy.html` |
| Thư mục `data/reports/model_eval/**` | **ĐÃ BỎ 25/09/2026** | Bằng chứng của lượt kiểm resume ngày 24/09/2026 nằm ở đó (xem `docs/06_plan/P4_logging_mlflow.md` T8) đã bị xoá cùng lần dựng lại dữ liệu; kết quả của nhóm nay chỉ nằm trong `experiments/**/results/<hash8>/` |
| Huấn luyện LoRA cho PhoBERT / ViSoBERT | **ĐÃ LÀM (đợt 2, 25/09/2026)** | `src/training/lora.py` (registry `TRAINERS`) và `src/experiments/encoder_run.py`, hai thí nghiệm `visobert/lora/exp001` + `phobert-base-v2/lora/exp001`. Từ đợt này `training.yaml` hết là khai báo suông: `trainer`, `checkpoints.*` đều có nơi đọc |
| `src/sources/` (registry `SOURCE_KINDS`) và `src/models/` (registry `ADAPTERS`) | vẫn làm khác | Đường encoder mới dùng `ENCODERS` (`src/training/encoders.py`) cho model có thể huấn luyện, và `TRAINERS` cho cách huấn luyện; `kind` của nguồn vẫn kiểm ở `src/core/dataset.py` |
| `save.plots` trong `configs/experiments/evaluation.yaml` | **ĐÃ LÀM 27/09/2026** | `feat(evaluation): make save.plots write a plot into the run folder`: `true` thì lượt chạy ghi `plots/accuracy.html` (độ chính xác từng khía cạnh + ma trận nhầm, HTML tự chứa, không cần `plotly`); `false` thì không tạo thư mục rỗng |
| Writer `state_dict` cho full fine-tune (checkpoint đã tách khỏi trainer) | CHƯA LÀM | Chính sách + `Store` đã ở `src/training/checkpoints.py`, writer `adapter` ở `src/training/savers/`. Full fine-tune chỉ cần thêm một writer ghi `state_dict` + một dòng trong `SAVERS` - xem `src/core/registry.py` mục 11 |

## 7. Mục duy nhất của đợt 27/09/2026 CHƯA làm: báo cáo HTML cho `token_stats`

### 8.3. Việc PHƯƠNG PHÁP còn nợ (ghi 30/09/2026)

| Việc | Trạng thái | Ghi chú |
| ---- | ---------- | ------- |
| **ViTASA** vào bảng so sánh cùng PhoBERT / ViSoBERT / Qwen3 | **GÁC LẠI** (mục 1 ở trên) | Repo `kh4nh12/ViTASA` chỉ có `LICENSE`, `README.md` và 3 tệp `.jsonl`: không có mã model, không checkpoint, không script huấn luyện; Hugging Face Hub cũng không có dataset/model nào tên `vitasa`. Chưa có gì chạy được thì viết code chỉ là SUY ĐOÁN. Làm tiếp khi có checkpoint: viết `src/preprocessing/vitasa.py` theo khung đã ghi sẵn trong docstring của nó, rồi thêm một dict vào `MODELS` của `src/preprocessing/token_stats.py` |
| **8 tệp `token_stats__*.csv` thiếu dòng của `qwen3-0.6b`** | **ĐÃ LÀM 30/09/2026** | `qwen3-0.6b` vào danh sách `MODELS` của `src/preprocessing/token_stats.py` ngày 29/09/2026 (`a30a5da`), nhưng lượt sinh lại ĐẦU TIÊN chỉ làm MỘT tệp (`1acffd5`, `absa_direct_v1__seg-none.csv`) - nên lúc đó đúng là chỉ 1 trong 9 tệp đủ 4 model. `da4ed98` (30/09/2026) sinh lại 7 tệp còn lại (mỗi tệp **+3 dòng** = 1 model × 3 split) và **bỏ luôn tệp mồ côi** `token_stats__prompt-absa_cot_5shot_v1__ex-2799b4c8.csv`, nên thư mục còn 8 tệp. Kiểm lại 01/10/2026: mỗi phiên bản dữ liệu có **8 tệp × 12 dòng = 4 model × 3 split** (cả `e0ccc484` lẫn `e616c1e3`), và bảng gộp `model_input.csv` có **192 dòng** (16 tệp × 12) - không còn tổ hợp nào thiếu. Con số "9 tệp" và chữ "CHƯA LÀM" trong ô này là số liệu của ngày 29/09, đã bị chính commit 30/09 vượt qua. **Cập nhật 02/10/2026**: thêm ba bảng của ba prompt một-ví-dụ mới (`absa_cot_1shot_v2/v3/v4`) nên nay là **228 dòng** (19 tệp × 12) |
| **Thay thời gian chạy ƯỚC TÍNH bằng SỐ THẬT** | **ĐÃ LÀM 04/10/2026 cho cả 17 lượt** | Số giây thật (đọc từ `run_meta.json` / `attempt_registry.csv`) đã thay vào `handover/README.md` (bảng 20 notebook), `docs/00_workflow/07_colab.md` (bảng đo thật) và `docs/00_workflow/01_flow.md`. Nay chỉ còn **ba notebook 0.6B** ghi **ước tính** (chúng chưa chạy được lần nào vì hai kiểu hỏng - xem mục 10.1). **Lưu ý:** `exp004` (42 phút) và `exp010` (7 phút) là lượt **CHẠY TIẾP** nên số ghi được chỉ là phần phiên cuối; giả thuyết cũ "5 ví dụ sinh ít token" đã bị bác bỏ |
| **`mispredictions_paper.csv`** - danh sách ô sai theo CƠ SỞ ĐO `paper` | **ĐÃ LÀM 01/10/2026** | Mỗi lượt chạy nay ghi thêm tệp thứ sáu: `mispredictions_paper.csv`, TẬP CON của `mispredictions.csv` theo từng dòng (cùng cột, cùng chỉ số review gốc). Cùng một định nghĩa "ô sai" (`Samples.mispredictions`), chỉ khác bộ ô: bộ đã lọc hai chiều ⇒ không bao giờ có nhãn `không nhắc`/`không đọc được`, và số dòng theo khía cạnh khớp `paper.cells` trừ `scores_paper.accuracy.correct`. Việc phải sửa: `configs/paths.yaml`, `src/evaluation/scorers/__init__.py` (chỗ ghi), sáu danh sách "tệp nhẹ" trong tài liệu (nay SÁU tệp), `configs/experiments/tracking.yaml` (tệp nhẹ của cơ sở `paper` lên DagsHub - đảo chốt "cơ sở `paper` không lên MLflow" của 01/10/2026 sáng cùng ngày), và một lần **ghim lại 12 notebook + phát hành gói 004**: tệp mới chỉ ra đời khi bản code đã ghim có phần ghi nó, mà ghim lại là hợp lệ vì 12 thí nghiệm đó CHƯA chạy ở đâu và cách đo không đổi (`docs/00_workflow/10_template_notebook.md`) |
| **Lỗi ánh xạ chỉ số review khi lọc hai chiều** (lộ ra khi làm tệp trên) | **ĐÃ SỬA 01/10/2026** | `Samples.restrict` cũ truyền `raw_gold` GỐC cho bộ đã lọc, rồi suy vị trí ô từ hai dãy NHÃN. Sai ở hai đường: (a) `neutral_policy: as_negative`/`as_positive` ĐỔI mã neutral nên phép ghép không khớp ⇒ `ScorerError` làm **cả lượt chạy chết ở bước ghi kết quả** (chưa lộ vì bộ chỉ số của cơ sở `paper` không gọi `kept()`); (b) ô bị bỏ vì NHÃN ĐOÁN có thể trùng nhãn đúng với ô được giữ ⇒ ghép dãy con trỏ sang review KHÁC, **im lặng**. Nay `Samples` ghi nhớ `row_indexes` của từng ô, và `restrict` lấy vị trí trực tiếp từ bộ lọc (`src.labels.base.two_sided_positions`, nay là chỗ DUY NHẤT giữ luật lọc hai chiều) |

### 8.4. Những điểm LỆCH so với kế hoạch, đã cân nhắc và chấp nhận

| Điểm | Kế hoạch | Đã làm | Lý do |
| ---- | -------- | ------ | ----- |
| Migrate + ghim | cùng MỘT commit | **hai** commit liền nhau | Bản ghim chỉ được nêu một commit ĐÃ TỒN TẠI, và phải là commit có `src/` mà ô mới gọi; ghim vào commit trước thì notebook gọi `src.api` trong khi commit đó chưa có mặt tiền, còn `--amend` thì đổi chính sha vừa ghi |
| Ngắt phiên ở đường kiểm-trước-dừng | trong `src/workflow/preflight.py` | trong **ô KIỂM TRƯỚC** (khối bảo vệ) | Thư viện chỉ TÍNH và trả báo cáo; việc IN báo cáo do ô gọi (`print_report`). Đặt việc ngắt trong thư viện thì phiên chết TRƯỚC khi báo cáo hiện ra - mất đúng thứ người đọc cần. Hiệu quả về quota như nhau, vì đường kiểm trước trên Colab chỉ có ô gọi |
| Số hàm của `bootstrap` | 3 (`prepare`, `install_packages`, `model_assets`) | **4** (thêm `verify_checkout`) | Kiểm lại sha/nhánh là bước riêng, tách ra thì test được bằng điểm tiêm mà không phải chạy cả `prepare` |
| Ô bootstrap sau khi dời logic | ~50 dòng | 109 dòng | 114 dòng đầu là khối KÉO CODE bắt buộc ở lại ô (chạy TRƯỚC khi có `src/`), phần còn lại là 4 lời gọi + khối bảo vệ. Đợt này dọn cho SẠCH (gộp câu lệnh, bỏ chú thích trùng), không nhắm con số |
| Vùng mặt tiền `tracking` | xuất tên `base` và `run_meta` | xuất `run_meta` và **gói** `tracking` | E3 của kế hoạch yêu cầu ô cuối viết `from src.api import paths, tracking, utils`; muốn vậy phải có tên `tracking` trên mặt tiền. Ô cuối dùng `tracking.base.dagshub_config()` - đọc là "gói `tracking`, file `base`" |
| Bắt lỗi trong `end_session` | chỉ `RuntimeManagementError`/`ImportError` | **`Exception`** | Hàm chạy ở CUỐI một lượt tốn hàng chục phút: ném ra là lượt chạy xong bị báo là hỏng, và trong đường lỗi thì nó che mất lỗi gốc. Thông báo in kèm tên lớp lỗi + nội dung, không nuốt im |
| Số nhóm trong `tests/` | DoD ghi "7 nhóm" | **8 nhóm** | Bảng §I của kế hoạch liệt kê 8 (có `api/`); DoD ghi 7. Theo bảng §I, vì `tests/api/` là chỗ duy nhất giữ 5 luật mặt tiền |
| Lược đồ sổ bàn giao | `files.csv` chứa cả băm lẫn first/last | **3 tệp** chia vai (`files.csv` = ứng viên hiện tại; `ledger.csv` = đã gửi; `manifest.csv` = nội dung một gói) | Một tệp vừa là "hiện tại" vừa là "luỹ kế" thì không nói được cái nào là sự thật khi chúng lệch nhau |
| Cờ `--allow-red` | không có | **có** | Cảnh báo đỏ là chốt chặn, nhưng người đã hiểu rõ vẫn cần một đường thoát - và khi dùng thì cảnh báo được ghi vào manifest |

### 8.5. Hai đường dừng KHÔNG ngắt được phiên (đã biết, có lý do)

1. **Lỗi ở ô bootstrap TRƯỚC khi kéo được mã nguồn** (không `fetch` được commit; thư mục còn sót không
   phải git repo). Lúc đó `src/` CHƯA tồn tại nên không gọi được hàm ngắt phiên. Phiên chỉ vừa mở, chưa
   nạp model, và người chạy đang ngồi trước máy để Restart rồi chạy lại.
2. **Người dùng bấm Stop** (`KeyboardInterrupt`): giữ phiên cho họ sửa rồi chạy lại.

Ngoài hai đường đó, mọi ô code đều có khối bảo vệ và ngắt phiên sau khi in xong
(`docs/00_workflow/10_template_notebook.md` mục 3.2).


Mục "Báo cáo HTML cho tiền xử lý cho model" ở mục 5 nói **vẫn mở**, và lý do hoãn cũ không còn: số đo
đã chốt (mục 4.1 và 4.1.1 của [02_model_input.md](02_model_input.md)) và mỗi bộ tách từ đã có file riêng.
Việc cần làm, theo đúng đường có sẵn của dự án:

1. `run_token_stats.py` ghi `token_stats_result.json` cạnh CSV, dựng payload bằng
   `src/reporting/result.make_payload(phase="token_stats", ...)` rồi `write_result` - cùng khuôn với
   `eda_result.json` / `pipeline_result.json`.
2. `build_report.py`: thêm `token_stats` vào `PHASE_LABELS` và `--phase`; `targets()` trỏ vào
   `data/reports/model_input/<mã>/`; `draw()` gọi `render.write_reports`.
3. Nếu không muốn `render.py` phải biết thêm một loại payload: `src/reports.html_page()` đã dựng được
   trang bảng tự chứa (không cần `plotly`), đủ cho bảng token theo model × split.

Vì sao chưa làm trong đợt này: đây là đường VẼ mới, còn mọi mục khác của đợt chỉ thêm cột hoặc chú
thích; làm ẩu cho xong thì ra một báo cáo trông đúng mà số sai - đúng loại lỗi mà cả đợt này đang sửa.

## 8. Nợ phát hiện khi làm Batch 5b (ghi 30/09/2026)

Đợt Batch 5b (thêm tự ngắt phiên Colab; dời logic notebook vào thư viện; mặt tiền `src/api/`; bản mẫu
là MẪU chứ không phải chuẩn; xếp lại `src/` + `tests/`; công cụ dọn rác; gói bàn giao tăng dần) để lại
những khoản dưới đây. Ghi lại để người sau không phải phát hiện lại, và để không ai đọc kế hoạch mà
tưởng đã xong hết.

### 8.1. Nợ ảnh hưởng tới SỐ ĐÃ BÁO CÁO

| Việc | Trạng thái | Ghi chú |
| ---- | ---------- | ------- |
| 12 notebook thí nghiệm ghim `a7ac72a` (bản code TRƯỚC Batch 5b) | **ĐÃ LÀM 02/10/2026** | Cả 12 notebook đã dựng lại theo bản mẫu mới và ghim lại (gói `009`); hai notebook encoder ghim tiếp ở gói `010`. Nay mỗi notebook mang commit của đúng lượt chạy nó sinh ra: 9 lượt prompt ở `88d12e6`, hai lượt LoRA ở `aca047d` |
| Đổi một tệp TRONG phiên bản dữ liệu đã gửi | Có chốt chặn từ 30/09/2026 | `scripts/build_package.py` DỪNG (mã thoát 3): người nhận đang giữ cùng một mã phiên bản với nội dung khác, nên kết quả họ chạy không còn so được. Cách sửa đúng là tạo phiên bản dữ liệu MỚI |
| Đổi `config.yaml` của một thí nghiệm ĐÃ chạy | KHÔNG chặn, chỉ ghi lại | `run_meta.json` giữ `config_sha256` lúc chạy, nên sửa file sau đó là bản ghi không còn dựng lại được từ chính file đó. Chưa có phép kiểm nào chặn; luật là: sửa thì phải chạy lại và nói rõ |
| Số ở `docs/04_experiments/03_training_eval.md` mục 6 đo trên `val` của bộ dữ liệu `v0.1.0` | **ĐÃ GHI RÕ 01/10/2026** | Mục 6.3 nay nói rõ đó là bản ghi LỊCH SỬ: `val` của `v0.2.0` có 1.535 dòng (bản cũ 1.524), nên tập con 100 review (seed 42) không rút lại y hệt. Số để so với công bố nằm ở cột `reference` của `data/reports/metrics_matrix/` (đo trên `test`) |
| Token DagsHub nằm trong gói bàn giao | Đã biết, cố ý | Đổi/ thu hồi là việc THỦ CÔNG khi kết thúc đồ án. Sổ gói không chứa token (`docs/05_config/07_env.md` §Bảo mật) |

### 8.2. Nợ kỹ thuật

| Việc | Vì sao để lại | Cách sửa khi cần |
| ---- | ------------- | ---------------- |
| Tên module TRÙNG nhau giữa các gói (`base` ở 5 nơi, `loader` ở 2, `metrics`/`qwen` ở 2) | Việc chuyển nhà `src/` phải sửa tay ba lượt vì không thể suy ra gói từ tên; hai file vùng mặt tiền còn tự import chính mình, mà test cũ vẫn xanh vì tên "có tồn tại" | `tests/api/test_api.py` nay chặn hai lỗi đó. Muốn hết tận gốc thì đổi tên file theo gói (`label_base.py`, ...) - việc riêng, đổi tên file là đổi `run_meta` của các lượt sau |
| `paths.ROOT_DIR` suy từ `__file__` (nay `parents[2]`) | Đổi ĐỘ SÂY của `src/core/paths.py` là gốc repo sai LẶNG LẼ, không có gì báo | Thêm một phép kiểm `assignments/<file cấu hình>` lúc import, hoặc suy gốc từ `paths.yaml` tìm ngược lên |
| CI không kiểm tài liệu trỏ đúng file | **ĐÃ SỬA**: nhiều file tài liệu còn trỏ đường dẫn PHẲNG cũ (dạng `src/<tên>.py`, `tests/test_<tên>.py`) sau khi chuyển nhà | Check số 9 của CI (`documentation_source_paths` trong `src/workflow/checks.py`): mọi đường dẫn dạng `src/<tên>.py` và `tests/<tên>.py` nhắc trong tài liệu phải tồn tại (miễn file lịch sử P0..P2 + `APPENDIX_commits.md`) |
| Sổ bàn giao chưa kiểm phía NGƯỜI NHẬN | Sổ ghi được là nhóm đã GỬI gì, không biết người nhận đã xoá đúng những mục `deleted` chưa | Thêm một cột "đã xác nhận" vào `handover/ledger.csv`, hoặc một hàm so thư mục Drive nhận được với manifest |
| `scripts/` vẫn còn 8 công cụ `.py` phẳng | Ba file cài đặt `.ps1` đã vào `scripts/setup/`; các công cụ `.py` chưa chia nhóm | Chia tiếp khi số công cụ tăng: `scripts/notebook/`, `scripts/data/` |
| Bảng số đo của khối hệ thống bị GHI ĐÈ khi nội dung system đổi | Thẻ tên bảng chỉ ghi **TÊN** file system (`sys-<tên>`), không ghi băm nội dung, nên sửa `configs/prompts/system/<tên>.txt` mà giữ nguyên tên file thì tên bảng không đổi - lượt chạy sau **ghi đè** số cũ và mất bằng chứng. Guard và kiểm 8 của CI chỉ đối chiếu được ở mức TÊN, nên ca này chúng không thấy (`docs/04_experiments/02_model_input.md` mục 2.2) | Cho `sys-` mang thêm 8 hex của nội dung (`sys-<tên>-<sha8>`): `prompts.tag_parts` chấp nhận phần đuôi tuỳ chọn nên bảng cũ vẫn đọc được; các lần chạy sau sẽ có tên mới. Đụng định dạng thẻ nên làm thành một đợt riêng, có ghim lại |
| Bảng số đo không ghi PHIÊN BẢN bộ tách từ | Thẻ chỉ có `seg-<tên>` (ví dụ `pyvi`), và cột `segmenter` trong CSV cũng chỉ có tên - nâng cấp gói là số đo đổi mà tên bảng không đổi, cùng họ với ca `sys-` ở trên | Thêm phiên bản gói vào `info()` của bộ tách từ rồi đưa vào thẻ (và/hoặc một cột trong CSV); đụng định dạng bảng đã công bố nên làm cùng đợt với `sys-` |

## 9. Hoãn CÓ CHỦ Ý trong đợt "đo lường + MLflow" (ghi 02/10/2026)

Cây phát triển (nút nào sinh ra nút nào, vì sao) nằm ở `docs/04_experiments/07_evolution.md`. Ba mục
dưới đây là việc ĐÃ BIẾT và CỐ Ý chưa làm trong đợt này.

### 9.1. Tìm siêu tham số bằng Optuna - HOÃN một nhịp

- **Việc:** tìm `r`, `alpha`, `lr`, `lora_dropout` cho LoRA (và sau này cho loss) bằng Optuna.
- **Vì sao hoãn:** objective và hàm mất mát VỪA đổi trong đợt này (`checkpoints.best_metric` =
  `sentiment_f1`, thêm `loss.type: weighted_ce`). Chạy Optuna ngay là tối ưu theo một objective có thể
  còn đổi, rồi phải làm lại từ đầu. Thêm nữa mỗi lượt LoRA tốn 30-90 phút GPU nên HPO phải chờ đường
  chạy ổn định.
- **Làm tiếp từ đâu:** (1) chốt objective = `sentiment_f1` (đã chốt); (2) chạy vài baseline LoRA; (3)
  Optuna trên **val với `n` nhỏ** (`run_token_stats`/`--limit` đã có); (4) chốt cấu hình rồi chạy full
  `test`. Không gian tìm: `training.lora.r/alpha/dropout`, `training.lr`.

### 9.2. Focal loss / trọng số theo khía cạnh - làm SAU khi có bằng chứng

- **Việc:** thêm `loss.type: focal` (và/hoặc trọng số riêng cho từng khía cạnh) để chống mất cân bằng
  mạnh hơn `class_weight: inverse`.
- **Vì sao hoãn:** nguyên tắc "mỗi lần đổi MỘT thứ". Đợt này đã thêm `weighted_ce`, nên thêm focal cùng
  lúc là không biết cái nào có tác dụng. Chỉ làm khi curve train/val (`plots/training.html`) hoặc F1
  theo lớp cho thấy lớp hiếm bị bỏ.
- **Làm tiếp từ đâu:** mở rộng `src/training/lora.py::loss_settings` thêm `type: focal` + `focal_gamma`,
  giữ nguyên chữ ký `masked_loss` (đã có tham số trọng số), thêm một ca test; rồi chạy một thí nghiệm
  đối chứng trên cùng dữ liệu.

### 9.3. Kiểm tự động cho `plots/training.html` trên CI

- **Việc:** CI hiện kiểm cấu trúc, không kiểm nội dung biểu đồ train/val.
- **Vì sao hoãn:** test hiện có (`tests/reporting/test_curves.py`) đã khoá payload và việc ghi file;
  kiểm sâu hơn (đọc HTML, đối chiếu toạ độ điểm) là việc riêng, không cần cho lượt chạy.
- **Làm tiếp từ đầu:** nếu biểu đồ bị sai số, thêm test đọc `training_history.csv` rồi so với chuỗi
  `data` nhúng trong HTML.


## 10. Việc của đợt "20 lượt" (ghi 02/10/2026; cập nhật trạng thái 04/10/2026)

Đợt này chạy thêm 8 thí nghiệm mới (xem `07_evolution.md` và `08_experiment_rationale.md`). Bảy mục dưới
đây nay đã có kết quả (10.2, 10.3, 10.4 - XONG) hoặc còn mở / chờ chạy lại (10.1, 10.5, 10.6, mục 10.7 nay
đã thành việc của đợt sau); mỗi mục ghi trạng thái và điều kiện quay lại.

### 10.1. Chạy lại Qwen3-0.6B - việc KẾ TIẾP (CHƯA XONG, đã hỏng HAI lần)

Lượt 1 (đợt trước): ba lượt `qwen3-0.6b/prompt-cot/exp001..003` nạp nhầm trọng số 4B vì `run_model` rơi về
hằng số của module. Đã sửa (`checkpoint` của config model là nguồn, có test khoá ở commit `8bfe96e`).

Lượt 2 (02/10/2026, sau khi sửa): ba thư mục **đúng** model `Qwen/Qwen3-0.6B` nhưng **bật suy nghĩ** - model
ăn hết trần `max_new_tokens: 400` trong khối ` thinking` rồi không in JSON, nên chỉ đọc được **3,33 / 1,36 /
1,73%**. Cả **sáu** thư mục kết quả (3 lượt nhầm 4B + 3 lượt bật suy nghĩ) đã xoá ngày 04/10/2026; bằng
chứng ở `check_present_plan.md` mục 2.1.

Xong khi: ba lượt chạy lại có `metrics.json` ghi `model = Qwen/Qwen3-0.6B` **và** `% đọc được ≥ 95%`. Cách
làm đã chốt: khoá `preprocess.enable_thinking: false` trong cấu hình model (việc 4.1 của `present_plan.md`),
chạy lại trong đợt 7 (mục 5.1); lượt **bật** suy nghĩ tách thành nhánh riêng, mở đầu bằng lượt **DÒ**
(`exp004`, trần 8.192) để chốt trần token trước (mục 9.1).

### 10.2. Tách biến lượng hoá - **XONG 04/10/2026**

Ba lượt `prompt-cot/exp008/009/010` (4-bit, lô 4) đã chạy xong, nên nay so được **sạch một biến** với nhóm
fp16 lô 4 (`exp005/006/007`). Kết quả: 4-bit hơn fp16 **0,64 / 1,17 / 0,71 điểm**; F1 macro hơn
0,018 / 0,019 / 0,008; **nhưng** số ô của cơ sở `paper` lại **thấp hơn 5-6%** (2.414/2.324/2.375 so với
2.580/2.461/2.520). Kết luận đã ghi ở `08_experiment_rationale.md` §3 và §6.3: lợi thế một phần đến từ việc
**kiêng trả lời**, nên mọi so sánh phải đọc kèm số ô.

### 10.3. Chống mất cân bằng lớp âm cho encoder - **XONG 04/10/2026**

Hai lượt `lora/exp002` (`weighted_ce` + `inverse`) đã chạy. Kết quả: PhoBERT **88,40 → 96,62** (F1 lớp âm
**0,540 → 0,876**), ViSoBERT **94,86 → 95,61** (F1 lớp âm 0,765 → 0,836); số ô tăng (2.665 → 2.736 và
2.688 → 2.701) nên điều kiện "F1 âm tăng VÀ số ô không giảm" **đạt**; và **đảo thứ hạng** hai encoder.
Điều kiện tiến bộ đã đạt. **Nợ mới phát hiện**: `weighted_ce` **hạ phát hiện khía cạnh** (PhoBERT
98,05 → 94,14; ViSoBERT 98,29 → 97,06, cơ sở `all`) - từ nay phải báo cáo **cặp** chỉ số (F1 lớp âm + phát
hiện khía cạnh), xem `06_lora_encoder.md`.

### 10.4. Ba biến thể prompt - ba cơ chế khác nhau - **XONG 04/10/2026, CẢ BA ĐỀU ÂM**

`exp011` 97,63 (**−0,09**), `exp012` 96,52 (**−1,20**), `exp013` 92,66 (**−5,06**, mất 343 ô). `exp011` còn
kéo F1 `price` âm từ 0,600 xuống 0,308. Kết luận: sửa **ví dụ** và sửa **câu chữ prompt** đều không cứu được
lớp âm - hướng đó đã bị bỏ; hướng có kết quả là sửa **hàm mất mát** (mục 10.3). Chi tiết: §3b của
`08_experiment_rationale.md`.

### 10.5. Hướng LAI encoder + LLM - có điều kiện

Bốn luật lai thô đã thử trên `test` (chỉ để ước lượng): trên cơ sở `paper` mọi luật đều THUA LLM một
mình; trên cơ sở `all` lai thắng cả hai (acc micro 97,22 so với 97,10 của encoder và 93,41 của LLM;
macro-F1 0,835 so với 0,738 và 0,779). Kết luận: lai **phải thắng trên `paper` bằng cách tăng độ chính
xác lớp âm**, không phải bằng cách phát hiện nhiều hơn. Ba điều kiện trước khi làm: (i) chốt thước đo
trước khi chạy; (ii) luật và ngưỡng chốt trên `val`, không phải `test`; (iii) cần **xác suất** từng ô
của encoder (hiện `predictions.csv` chỉ có nhãn cứng) nên phải sửa đường encoder để ghi thêm `p(mã)`.

**Trạng thái 04/10/2026:** (i) và (ii) đã vào kế hoạch (`present_plan.md` mục 8.4, 8.5 - luật chốt trên
`val` rồi mới áp lên `test`); (iii) là việc **4.5** (đường encoder ghi xác suất từng ô). Lượt `val` cần cho
lượt lai: `prompt-cot/exp017` (phía LLM) và `lora/exp003` của hai encoder. **Lưu ý:** luật lai **không áp
được cho `price`** vì `val` có 0 ô `price` âm (xem `08_experiment_rationale.md` §7). Nếu lượt lai thắng
trên cơ sở `paper`, bước tiếp theo là thăng cấp nó thành một `method` - xem mục 11.2.

### 10.6. QLoRA / fine-tune Qwen3-4B - KHÔNG làm được trên T4

Colab chỉ có T4 16 GB; bản 4B ở fp16 đã ~8 GB trọng số nên không còn chỗ cho optimizer/scheduler, còn
QLoRA 4-bit thì rất chật và dễ OOM giữa lượt. Câu hỏi "fine-tune có hơn prompt không" vì vậy để mở;
muốn làm cần GPU ≥ 24 GB.

### 10.7. Đo dao động - đã bỏ khỏi đợt này

`decoding: sample` + nhiều seed: hạ tầng đã có (`--sample`, `seed`), nhưng đợt này KHÔNG chạy (mỗi
seed là một thư mục kết quả mới). Giữ ở đây để lần sau nhớ rằng các kết luận kiểu "+0,02 so công bố"
mới là MỘT lần chạy greedy, chưa phải một phân bố.

**Cập nhật 04/10/2026:** đã đưa vào kế hoạch đợt 8 (`present_plan.md` mục 11.3): ba lượt lấy mẫu
`exp018/019/020` (4-bit, `seed` 1/2/3) + một lượt đối chứng fp16 `exp021` (cùng `seed` 1) để tách
**lượng hoá × lấy mẫu**; biểu quyết dùng **3 mẫu** (mục 9.4; luật 6 của `docs/04_experiments/metrics.md`).

## 11. Bốn mục mới (ghi 04/10/2026)

### 11.1. Lỗi đã gặp: model bật suy nghĩ ăn hết trần token

**Hiện tượng:** `Qwen/Qwen3-0.6B` (bản 4/2025) **mặc định bật suy nghĩ**; với `max_new_tokens: 400` nó viết
hết 400 token trong khối ` thinking` rồi không còn chỗ in JSON. Ba lượt 0.6B vì thế chỉ đọc được
**3,33 / 1,36 / 1,73%**, lí do hỏng chính là "không thấy JSON nào" (1.549 / 1.561 / 1.536 lượt).

**Cách xử lý (đã chốt):** bật suy nghĩ là **một cơ chế, hai khoá đi liền nhau** - phải khai thêm trần token
tương ứng; lượt nào bật suy nghĩ thì phải chạy **lượt DÒ** (~60 mẫu) đo p50/p95/max token sinh rồi chọn
`max_new_tokens = làm tròn lên (p99 × 1,5)`. Có **cửa chặn**: `% đọc được < 95%` ⇒ ghi `valid: false` kèm
lí do. Việc này nằm ở luật 2 và luật 3 của `docs/04_experiments/metrics.md` và mục 9.1 của
`present_plan.md`.

### 11.2. Thăng cấp LUẬT LAI thành một `method` - nếu nó thắng

Hiện luật lai (encoder + LLM theo khía cạnh) chỉ là một **script chấm lại** (`scripts/fuse.py`), không
phải một `method` trong `experiments/`. Nếu lượt lai thắng trên cơ sở `paper` và thắng **ổn định**, thì
thăng cấp thành `method: fuse` (một mục trong `src/experiments/` + `method` hợp lệ), để nó có
`config_sha256`, có luật đóng băng trong repo và chạy lại được như mọi lượt khác. Chưa làm vì chưa biết
thắng hay không.

### 11.3. Trọng số lớp theo TỪNG khía cạnh (`loss.class_weight: inverse_by_aspect`) - chỉ làm nếu ngưỡng không đủ

`weighted_ce` + `inverse` tính trọng số **dùng chung cho mọi khía cạnh**. Khía cạnh hiếm hơn (ví dụ
`packing` âm chỉ 10 ô ở `test`, 85 ở train) có thể cần trọng số riêng. Đây là việc rẻ (một lượt encoder
15 phút) **sau khi** biết kết quả đường ngưỡng: nếu ngưỡng theo khía cạnh đã kéo được lớp âm lên thì không
cần; nếu model không bao giờ đặt `p(mã 2)` cho khía cạnh đó cao hơn ~0,2 thì ngưỡng vô dụng và trọng số
theo khía cạnh là bước kế tiếp. Đụng vào `src/training/lora.py` (thêm một giá trị cho `loss.class_weight`)
+ test + docs.

### 11.4. Tập chẩn đoán GIÁ - theo quyết định người dùng 04/10/2026

**Vì sao cần:** `price` âm chỉ có **15 ô ở train, 0 ô ở val, 6 ô ở test** ⇒ F1 ở lớp này là nhiễu và
**không dò được ngưỡng cho `price`**. Muốn có thước thật cho `price` thì phải có tập đo riêng.

**Việc:** lập một tập ~200-300 review CÓ nhắc giá (lấy từ `val` + `test` của bộ dữ liệu đang dùng), gán
nhãn "chê giá / khen giá / không nhắc" theo **quy tắc viết TRƯỚC**, lưu tách hẳn ở
`data/reports/price_probe/` - **KHÔNG** trộn vào bảng `paper` (luật 9 và 11: bảng công bố là bất biến).
Khi có tập đó thì mới đo được recall/precision thật cho `price` và mới dò ngưỡng được trên tập `val` phụ.

**Trạng thái:** người dùng đã chốt **đưa vào backlog, làm SAU** (không thuộc kế hoạch đợt 7-9). Việc của
người, **0 GPU**.

