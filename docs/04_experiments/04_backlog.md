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
input như 3 model còn lại. Docstring của `vitasa.py` ghi sẵn 4 bước.

## 2. Chạy Qwen3 theo hướng CHỈ DẪN (prompt + CoT) - chưa làm

**Việc:** cho Qwen3 trả lời tập test bằng prompt (zero-shot / few-shot / CoT), rồi đo tỉ
lệ JSON hợp lệ và F1. **Không fine-tune.**

**Vì sao đi hướng này:** Qwen3 là LLM 4B tham số, full fine-tune cần ~64-80 GB VRAM (chỉ
riêng trọng số ở bf16 đã 8 GB) nên **không thể** trên GPU 6 GB của máy này. Hướng đúng bản
chất phép so sánh của dự án là dùng nó như model đa năng bằng chỉ dẫn - tức "LLM thì thử
prompt + CoT", còn PhoBERT (135M) và ViSoBERT (~108M) thì **fine-tune toàn bộ** (hai
encoder nhỏ này vừa 6 GB và **không cần** LoRA/QLoRA).

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

- Bốn prompt, đủ để tách riêng ảnh hưởng của "có suy luận" và "bao nhiêu ví dụ":
  `absa_direct_v1` (một lượt, 0 ví dụ), `absa_cot_zeroshot_v1` (0 ví dụ) ,
  `absa_cot_1shot_v1` (1 ví dụ), `absa_cot_v1` (2 ví dụ).
- **Chi phí input đã đo** (train): 229,50 -> 376,50 -> 681,50 -> 950,50 token/review. Mỗi ví
  dụ khoảng 287-305 token; prompt CoT dài nhất cần 1.195 token -> ngưỡng 1280 giữ 0% bị cắt ở
  mọi split. Bảng đầy đủ ở [02_model_input.md mục 4.2](02_model_input.md).
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
2. **So với 3 encoder**: PhoBERT (× số bộ tách từ) và ViSoBERT vẫn chưa có script huấn luyện.
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
  `powershell -ExecutionPolicy Bypass -File scripts\setup_java.ps1 -Major 11 -Force`
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
- **Bài học về test (đã trả giá):** lỗi hoán vị FP/FN trong `metrics._binary_counts` lọt qua
  27 test đầu tiên vì các ca test lúc đó **đối xứng** (hoặc chỉ có một loại lỗi), mà F1 lại
  đối xứng nên không đổi. Nó chỉ lộ ra khi đối chiếu bảng điểm với **số đếm thô** (cấu hình
  nêu thừa nhiều nhất lại được báo precision cao nhất). Từ nay: hàm chấm điểm phải có ca test
  **bất đối xứng** (chỉ dương tính giả / chỉ âm tính giả), và con số tổng hợp phải được kiểm
  chéo với số đếm. Kết quả đã ghi được chấm lại từ file dự đoán (không cần GPU).
- **Cột đếm `<unk>`:** bảng `token_stats` chỉ có `% token <unk>` (đã làm tròn), nên muốn nói
  "giảm bao nhiêu token `<unk>`" thì phải đo bằng script riêng - đã phải làm vậy một lần
  (21.886 -> 14.302 token `<unk>` trên train). Thêm cột đếm sẽ không phải suy ngược từ tỉ lệ.
- **Cơ chế của việc tách từ chưa được lưu thành số liệu:** đã đo trong phiên làm việc là
  "mảnh/đơn vị 1,618 -> 1,445" cùng vài ca cụ thể (`Công_dụng` = 1 token so với `Công` +
  `dụng` = 2; `dụng:` = 3 mảnh so với `dụng` + `:` = 2), nhưng **chưa ghi vào file/doc nào**
  nên muốn trích dẫn lại thì phải đo lại. Nên đưa thành một script nhỏ hoặc một mục riêng
  trong [02_model_input.md](02_model_input.md).
- **Ví dụ few-shot dạng LƯỢT hội thoại:** hiện `{examples}` là MỘT khối văn bản nằm trong
  lượt người dùng. Muốn ví dụ thành các cặp `[USER]`/`[ASSISTANT]` thật (cách chat model
  thường được dạy) thì cần thêm một khối hoặc ô nhớ mới cho loader prompt.
- ~~Mục lục có thể trỏ tới file báo cáo đã bị xoá~~ - **đã xử lý:** `versioning.prune_missing()`
  bỏ những dòng có `report` không còn tồn tại, và `record()` gọi hàm này mỗi lần ghi nên mục
  lục tự dọn (đã dùng để dọn 2 dòng trỏ tới các lần chạy thử `n4`/`n8`). Có test riêng:
  `tests/test_versioning.py` (4 ca, dùng manifest trong thư mục tạm, không đụng mục lục thật).

## 6. Chưa làm so với kế hoạch refactor (ghi 25/09/2026)

Rà lại toàn bộ kế hoạch trong `docs/06_plan/` so với code đang có. Những việc dưới đây là CHƯA LÀM
hoặc CỐ Ý LÀM KHÁC, ghi lại để không ai đọc kế hoạch mà tưởng đã xong.

| Việc | Trạng thái | Ghi chú |
| ---- | ---------- | ------- |
| Máy kiểm "kết quả trước merge" (`valid`, `invalid_reason`, `comparable` trong `experiment_registry`) | chưa làm | Kế hoạch P6 nêu; cần `git rev-list --ancestry-path` so với `origin/experiment`. Cột hiện chưa có, nên bảng tổng hợp chưa nói được kết quả nào chạy trước khi merge |
| `dataset_registry` có cột `parent` + changelog người đọc (`docs/01_dataset/changelog.md`) | chưa làm | Hiện có `dataset`, `version`, `ma`, `on_disk`, `splits`, `rows`, `eval_locked`, `aspects`, `raw_dir`, `config`; dòng dõi nằm trong khoá `parent` của file cấu hình |
| `src/sources/` (registry `SOURCE_KINDS`) và `src/models/` (registry `ADAPTERS`) | làm khác | `kind` (`raw`/`dataset`) kiểm trong `src/dataset.py`; model sinh nạp ở `src/evaluation/runner.py`, model encoder ở `src/preprocessing/`. Chức năng tương đương, khác chỗ đặt |
| `run_rescore_eval.py` và `config.MODEL_EVAL_REPORT_DIR` (kế hoạch ban đầu định bỏ) | giữ có chủ ý | Là đường chạy TAY: đo thử prompt, chấm lại từ file dự đoán khi không có GPU. Kết quả không thuộc thí nghiệm nào nên nằm ở `data/reports/model_eval/`; chạy trong thí nghiệm vẫn ghi vào `experiments/**/results/<mã>/` |
| `nbstripout` cài trên từng máy | chưa cài | CI kiểm notebook sạch output ở kiểm tra 3, nên vẫn chặn được notebook kèm output |
| `mlflow_tags` đủ 8 nhãn và `artifacts` có `plots` | làm gọn hơn | Hiện gắn `model`, `method`, `exp_id`; `sha` và `config_sha256` đã nằm trong `run_meta.json` (được tải lên làm artifact) nên tra được từ run |
| Thư mục `data/reports/model_eval/**` | giữ có chủ ý | Là bằng chứng của lần chạy thật đã kiểm cơ chế resume (xem `docs/06_plan/P4_logging_mlflow.md`, T8) |

