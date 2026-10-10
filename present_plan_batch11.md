# present_plan_batch11 - Kế hoạch đợt 11: trả lời 11 câu hỏi phản biện

> Đây là kế hoạch **ĐANG THỰC THI** của đợt 11, đặt ở gốc repo. Kế hoạch của đợt trước nằm ở
> `present_plan.md` (đợt 7 → đợt 10) và **giữ nguyên, không sửa**. Tệp này ghi cả TRẠNG THÁI
> (mục 7) để không phải mở tệp thứ hai.

## 1. Vì sao có đợt này

11 câu hỏi sẽ bị hỏi khi đem dự án so với công bố tham chiếu. Kiểm kê trên đĩa (09/10/2026):
**3 câu đã trả lời được**, **8 câu còn là lỗ hổng thật**.

| # | Câu hỏi | Trạng thái trước đợt |
| --- | --- | --- |
| 1 | LoRA so với KHÔNG LoRA | thiếu: `TRAINERS` chỉ có `lora` |
| 2 | Tiền xử lý train khác nhau (icon / segmentation / segmenter) | thiếu: chỉ một phiên bản pipeline; chỉ ĐO token |
| 3 | Chọn `model/best` theo F1 hay theo accuracy | thiếu: mọi lượt dùng `sentiment_f1` |
| 4 | Train head hay không | ĐÃ CÓ: 6 cặp + 4 lượt `head.aspect_marker` |
| 5 | Đổi tham số LoRA | thiếu: hằng số ở mọi lượt |
| 6 | Ngoài `weighted_ce` | thiếu: chỉ `ce` / `weighted_ce` |
| 7 | Cách train khác LoRA | thiếu: chỉ `lora` |
| 8 | Qwen3-0.6B không bằng Qwen3-4B | ĐÃ CÓ (ba cơ chế hỏng đo được) |
| 9 | Qwen3 lớn hơn 4B | thiếu |
| 10 | LLM khác họ / mới hơn 4B | thiếu |
| 11 | Cách đo để so công bằng với công bố | ĐÃ CÓ (chỉ cần LIỆT KÊ bước) |

## 2. Chốt của người dùng (đã khoá, không đổi)

- **Không ghim lại 67 notebook cũ.** Mỗi lượt mới = một notebook MỚI ghim commit mới.
- Nhánh `icon` = **bỏ emoji ở `train` và `val`**; **`test` giữ nguyên từng ký tự**.
- Nhánh `segmenter` = thử **cả `underthesea` và `pyvi`**.
- Mục 3 ở `phobert-base-v2`: ghép với **cả** `lora/exp002` (đầu đóng băng) **và** `lora/exp005` (đầu học)
  ⇒ bảng 2×2 (cơ chế đầu phân loại × tiêu chí chọn best).
- Cột ở mục báo cáo M8 tên là **`Dùng được để so?`** (CÓ/KHÔNG), kèm chú thích "CÓ khi đọc được ≥ 95%".
- `loss.type: focal` khởi đầu `gamma: 2`.
- Mục 11 trong báo cáo chỉ **liệt kê bước/điều kiện so**, không bảng chứng minh, không bảng "không so được".

## 3. Quy tắc bắt buộc (nhắc lại trước khi làm)

1. **Commit**: Conventional Commits tiếng Anh, một commit = một task nhỏ, tách theo miền, không gộp.
2. **Kiểm sau mỗi nhóm việc**: `python scripts/ci_checks.py` và `python -m unittest discover -s tests`
   (Windows: `$env:PYTHONUTF8=1`), cả hai phải thoát mã 0.
3. **CI xanh trước khi ghim notebook** (luật 22): merge → push → đợi CI GitHub xanh → mới `pin.py`.
4. **Bất biến**: `configs/paths.yaml` là nguồn đường dẫn duy nhất; `configs/pipeline/*`, `configs/models/*`,
   `configs/datasets/*/*` **bất biến khi đã dùng** (đổi thì tạo phiên bản mới); cặp prompt + ví dụ + system
   **bất biến khi đã dùng**; `test` không bao giờ bị sửa; thiếu khoá là lỗi.
5. **Mỗi lượt chỉ khác parent đúng MỘT khoá đo được.**
6. **Tệp `.md` ghi không BOM.**
7. **Cây làm việc phải sạch** trước khi `new_experiment.py` / `pin.py` chạy.

## 4. Tổng quan 8 đợt

| Đợt | Nội dung | Lượt (kế hoạch) | Đã tạo | ~GPU | Mục |
| --- | --- | --- | --- | --- | --- |
| Đ1 | `trainer: none` (SÀN + PROBE) ×2 model · `best_metric: accuracy_cell` ×3 · thước nhiễu head ×2 | 9 | 9 | ~2 h | 1, 3, 4 |
| Đ2 | Tiền xử lý: segmentation ×3 · `underthesea` ×3 · `pyvi` ×3 · icon ×3 + pipeline `v0.3.0` | 12 | 12 | ~3 h | 2 |
| Đ3 | Wave 1 tham số LoRA ×2 model | 10 | 10 | ~2,5 h | 5 |
| Đ4 | `focal` · `inverse_by_aspect` · DoRA ×2 model | 6 | 6 | ~1,5 h | 6, 7 |
| Đ5 | Full fine-tune ×2 model (+ partial FT tuỳ chọn ×2) | 2 (+2 tuỳ chọn) | **3** | ~1,5-3 h | 1, 7 |
| Đ6 | Qwen3-8B ×3 mức · Qwen3-4B-Thinking (DÒ + 1 lượt) | 5 | 5 | ~2-4 h | 9 |
| Đ7 | Llama-3.1-8B · Mistral-7B · Vistral-7B ×3 mức | 9 | **3** (6 lượt Llama/Vistral CHƯA TẠO: repo GATED) | ~5 h | 10 |
| Đ8 | Viết báo cáo (10 mục) | 0 | 0 (báo cáo; xem §7) | 0 | 8, 11 |

**Cộng: kế hoạch 53 lượt bắt buộc (+2 tuỳ chọn) → ĐÃ TẠO 48** = 9 + 12 + 10 + 6 + 3 + 5 + 3. Hai chỗ lệch
kế hoạch: Đ5 nhiều hơn **1** lượt (thêm `cafebert/full/exp001` khi tách `lr` của PhoBERT), Đ7 thiếu **6** lượt
GATED. Đây cũng đúng là con số của gói bàn giao (48 notebook), và **0/48 lượt đã chạy** (kiểm 09/10/2026:
không lượt nào trong 48 có thư mục kết quả - xem mục rà soát ở §7).

## 5. Đ1 - chi tiết (đợt đang làm)

Mã:

| Tệp | Việc |
| --- | --- |
| `src/training/lora.py` | Vòng lặp huấn luyện tách thành `fit_generic(..., build=, writer_name=)`; `fit`/`predict` thành VỎ MỎNG. **KHÔNG đổi hành vi** (979 test cũ vẫn xanh) |
| `src/training/savers/head_only.py` (mới) | Writer chỉ ghi đầu phân loại (`head.pt` + `head_config.json`), vì đường `none` không có `save_pretrained` để gọi |
| `src/training/none.py` (mới) | `NAME="none"`; `head.trainable: false` ⇒ KHÔNG tối ưu gì (SÀN); `true` ⇒ tối ưu CHỈ đầu phân loại (LINEAR PROBE) |
| `src/training/__init__.py` | Thêm `none` vào `TRAINERS` |
| `tests/training/test_none.py` (mới) | `check()` rỗng; SÀN ⇒ 0 tham số học và `head.pt` không đổi; PROBE ⇒ đúng số tham số đầu phân loại |
| `docs/04_experiments/06_lora_encoder.md` | Thêm mục "Cách huấn luyện `none`" |

Thí nghiệm (9 lượt; `expNNN` là số DỰ KIẾN, `new_experiment.py` tự chọn số kế tiếp):

| # | Thí nghiệm | Parent | Khoá đè |
| --- | --- | --- | --- |
| 1 | `phobert-base-v2/none/exp001` | `phobert-base-v2/lora/exp002` | `trainer: none`, `head.trainable: false` (SÀN) |
| 2 | `phobert-base-v2/none/exp002` | `phobert-base-v2/none/exp001` | `head.trainable: true` (PROBE) |
| 3 | `cafebert/none/exp001` | `cafebert/lora/exp001` | `trainer: none`, `head.trainable: false` |
| 4 | `cafebert/none/exp002` | `cafebert/none/exp001` | `head.trainable: true` |
| 5 | `cafebert/lora/exp007` | `cafebert/lora/exp002` | `checkpoints.best_metric: accuracy_cell` |
| 6 | `phobert-base-v2/lora/exp008` | `phobert-base-v2/lora/exp005` | `checkpoints.best_metric: accuracy_cell` |
| 7 | `phobert-base-v2/lora/exp009` | `phobert-base-v2/lora/exp002` | `checkpoints.best_metric: accuracy_cell` |
| 8 | `phobert-base-v2/lora/exp010` | `phobert-base-v2/lora/exp002` | `decoding.seed: 7` (thước nhiễu, đầu đóng băng) |
| 9 | `phobert-base-v2/lora/exp011` | `phobert-base-v2/lora/exp005` | `decoding.seed: 7` (thước nhiễu, đầu học) |

Chung cho #1-#4: `enabled: true`, `roles: {train: train, val: val, eval: test}`,
`loss: {type: weighted_ce, class_weight: inverse}`. Ở hai lượt SÀN, `train` **không dùng** - ghi rõ
trong `README.md` của thí nghiệm để không ai tưởng là lỗi.

### 5.1 Thứ tự CHẠY 9 lượt (thời gian TĂNG DẦN)

Chạy đúng thứ tự này: rẻ nhất trước. Hai lượt SÀN đứng đầu vì chúng còn là **bước kiểm ống dẫn** - nếu
SÀN KHÔNG xấu (acc ~ mức đoán theo tần suất, F1 âm ~ 0) thì có gì đó sai, và ta biết sau ~3 phút thay
vì sau 2 giờ. Nhóm PhoBERT cũng nằm sớm, nên nếu thiếu Java/VnCoreNLP thì lộ ra ngay ở lượt đầu.

| # | Lượt | Là gì | ~T4 |
| --- | --- | --- | --- |
| 1 | `phobert-base-v2/none/exp001` | SÀN PhoBERT - KHÔNG vòng lặp huấn luyện | ~3 phút |
| 2 | `cafebert/none/exp001` | SÀN CafeBERT | ~4 phút |
| 3 | `phobert-base-v2/none/exp002` | PROBE PhoBERT - chỉ đầu phân loại học | ~10 phút |
| 4 | `cafebert/none/exp002` | PROBE CafeBERT | ~15 phút |
| 5 | `phobert-base-v2/lora/exp009` | LoRA PhoBERT, đầu ĐÓNG BĂNG, `accuracy_cell` | ~12-15 phút |
| 6 | `phobert-base-v2/lora/exp010` | LoRA PhoBERT, đầu ĐÓNG BĂNG, `seed 7` | ~12-15 phút |
| 7 | `phobert-base-v2/lora/exp008` | LoRA PhoBERT, đầu HỌC, `accuracy_cell` | ~13-16 phút |
| 8 | `phobert-base-v2/lora/exp011` | LoRA PhoBERT, đầu HỌC, `seed 7` | ~13-16 phút |
| 9 | `cafebert/lora/exp007` | LoRA CafeBERT, đầu HỌC, `accuracy_cell` | ~15-20 phút |

Cơ sở xếp thứ tự: **SÀN < PROBE < LoRA** theo số việc phải tối ưu (SÀN không tối ưu gì; PROBE chỉ học
đầu phân loại với encoder đóng băng, không backward qua encoder), rồi **PhoBERT-base (135M) trước
CafeBERT (278M)** vì mỗi bước chậm hơn; trong nhóm LoRA, đầu ĐÓNG BĂNG ít tham số học hơn đầu HỌC
(chênh 16.149 tham số - nằm trong nhiễu, nên đây chỉ là thứ tự cho gọn). Tổng **~1,5-2 giờ**.

Sáu lượt `phobert-base-v2` cần **VnCoreNLP** (Java + model 27 MB); ô bootstrap của notebook tự cài khi
`configs/models/phobert-base-v2.yaml` khai `segmenter: vncorenlp`.

## 6. Đ2 - Đ8 (tóm tắt; chi tiết khi tới đợt)

- **Đ2**: mã `utils.remove_emoji` (dùng `EMOJI_PATTERN` đã có) + nhánh `remove_emoji` trong
  `pipeline/normalize.py::normalize_steps` + schema `core/dataset.py` + `configs/pipeline/v0.3.0.yaml` +
  `configs/datasets/cosmetics/v0.3.0.yaml` (`apply_to: [train, val]`) + cài bộ tách từ theo model trong
  `workflow/bootstrap.py` + `requirements-colab.txt`. 12 lượt: `phobert-base-v2/lora/exp012-015`,
  `visobert/lora/exp006-009`, `cafebert/lora/exp008-011` (A=none/vncorenlp, B1=underthesea, B2=pyvi, C=icon).
- **Đ3**: không cần mã. `phobert-base-v2/lora/exp016-020`, `cafebert/lora/exp012-016`
  (`lora.r` 8 và 32, `lr` 1e-4 và 4e-4, `lora.target_modules: [query, value]`).
- **Đ4**: mã `focal` + `inverse_by_aspect` + `lora.use_dora` (+ `KNOWN_KEYS`).
  `phobert-base-v2/lora/exp021-023`, `cafebert/lora/exp017-019`.
- **Đ5**: mã `src/training/full.py` + `src/training/savers/state_dict.py`.
  `phobert-base-v2/full/exp001`, `cafebert/full/exp001` (+ partial FT `exp002` tuỳ chọn).
- **Đ6/Đ7**: mã `src/preprocessing/chat_like.py` + 5 module model + 5 `configs/models/*.yaml` +
  `token_stats.MODELS`. `qwen3-8b/prompt-cot/exp001-003`, `qwen3-4b-thinking-2507/prompt-cot/exp001` (DÒ) và
  `exp002`, `llama-3.1-8b-instruct|mistral-7b-instruct-v0.3|vistral-7b-chat/prompt-cot/exp001-003`.
- **Đ8** (0 GPU): 10 mục trong `presentations/present_report/present_report.md` - M1 không LoRA/học chỉ
  đầu/LoRA · M2 tiền xử lý emoji & tách từ · M3 F1 hay accuracy · M4 đóng băng hay học đầu · M5 tham số LoRA ·
  M6 hàm mất mát · M7 cách huấn luyện · M8 model nhỏ hơn (cột `Dùng được để so?`) · M9 LLM lớn hơn & khác họ ·
  M10 điều kiện so công bằng (8 gạch đầu dòng).

## 7. Trạng thái

- [x] Chốt kế hoạch, ghi ra tệp này
- [x] Đ1: mã `lora.fit_generic` + `none.py` + `savers/head_only.py` + test (994 test xanh theo từng phần)
- [x] Đ1: tạo 9 thí nghiệm + commit (`e38bb7d`); đã CHỨNG MINH mỗi lượt khác parent đúng 1 khoá đo được
- [x] Đ1: push code (`1e34ffd`), ghim 9 notebook → `de20984` (CI **ĐỎ**: 4 test mới giả định máy có `torch`)
- [x] Đ1: **sửa gốc** - `none.py` kiểm cấu hình TRƯỚC khi import thư viện nặng; sửa test lọc thông báo
      "chưa cài thư viện". **Mô phỏng CI** bằng stub chặn `torch`/`transformers`: 15/15 test của
      `test_none` chạy được, 2 test cần torch bỏ qua đúng cách
- [x] Đ1: push `4a1dec8` + `017d9b1`, rồi **ghim lại 9 notebook vào `017d9b1`** → `398f80f` → push.
      Trạng thái cuối: `ci_checks` 9/9 sạch + **994 test xanh** (chín nhánh)
- [x] Revert đúng yêu cầu: trả `README.md`, `src/workflow/checks.py`, `tests/workflow/test_checks.py` về bản
      git; **không đụng** `presentations/` (cây chỉ còn dirty trong `presentations/present_report/`)
- [x] Đẩy hai commit `docs(plan)` đang ở máy (`c204c5a`, `cc435ca`)
- [x] **Báo cáo phần viết được ngay** vào `batch11_report.md` (10 mục M1-M10) - commit `b9fa990`. Tệp nằm ở
      GỐC repo vì `presentations/present_report/` đang do bạn sửa; sẽ ghép vào đó khi bạn cho phép
- [x] Đ2: mã - `utils.remove_emoji` + nhánh `remove_emoji` trong `normalize_steps` +
      `configs/pipeline/v0.3.0.yaml` + `configs/datasets/cosmetics/v0.3.0.yaml`; dữ liệu đã sinh
      `...-daebf6ba` (`eval_lock` khớp BYTE của v0.2.0: `af349bf5`, 1.623 dòng) - commit `618e811`
- [x] Đ2: **sửa LỖI THẬT trong đường huấn luyện** - `lora.encode()` gọi `build_inputs()` mà KHÔNG truyền bộ
      tách từ, nên `preprocess.segmenter` chỉ là khoá trang trí ở đường huấn luyện: mọi bộ tách từ sẽ ra
      cùng một kết quả mà không có gì báo. Nay giá trị đó đi tới ĐÚNG chỗ chia văn bản; `cafebert` /
      `visobert` / `xlm-roberta` nhận `segmenter` như `phobert` / `vibert` / `phobert-large` đã nhận;
      bootstrap cài gói theo cấu hình ĐÃ HỢP NHẤT (`SEGMENTER_PACKAGES`) - commit `c00822d`, `3717521`
- [x] Đ2: bắt và sửa một lỗi thật thứ hai - bản đầu `remove_emoji` dùng `\s+ -> " "` nên nuốt cả ký tự
      XUỐNG DÒNG: **4.158** dòng `train` đổi trong khi chỉ 1.877 dòng có emoji. Nay khác nhau ĐÚNG ở
      review có emoji (1.877 / 227 / test 0), khoá bằng test
- [x] Đ2: 12 thí nghiệm + chứng minh mỗi lượt khác cha ĐÚNG MỘT khoá đo được (`preprocess.segmenter`, hoặc
      `data.version` cho nhánh emoji) - commit `9645322`; ghim 12 notebook → `c0c953e` → `b739b53`, push
- [x] Đ2: `ci_checks` sạch + **1.012 test xanh** (chín nhánh) + docs cập nhật (`618e811`...`c0c953e`)
- [x] Đ1: **CI GitHub XANH trên `398f80f`** - đã xác nhận bằng `gh` (run `37908033692`, success). Ghi chú
      dùng lại: `gh.exe` nằm ở `G:\my_app\GitHub CLI\gh.exe`; PATH của shell trong VS Code còn cũ nên phải
      gọi bằng đường dẫn đầy đủ, và phải `cd` vào repo trước (gh tìm repo theo thư mục hiện tại)
- [x] **Sửa test đỏ đã làm CI đỏ ở `c0c953e`…`f1721bd`** (4 lượt liền): `test_encode_chuyen_tiep_segmenter`
      chạm `import torch`, mà `requirements-ci.txt` CỐ Ý không cài `torch`. Nay đoạn dựng chunk (chỉ gọi
      module model, không cần tensor) chạy TRƯỚC `import torch` ⇒ phép kiểm "bộ tách từ đi tới
      `build_inputs()`" chạy được cả trên CI. Đã mô phỏng CI bằng stub chặn torch (1 test OK) và ở máy
      (130 test OK) - commit `f1721bd`
- [x] Đ3: 10 thí nghiệm (`phobert-base-v2/lora/exp016-020`, `cafebert/lora/exp012-016`) + chứng minh mỗi
      lượt khác cha ĐÚNG MỘT khoá đo được (`lora.r`, `lr`, `lora.target_modules`) - commit `f1721bd`
- [x] Đ3: ghim 10 notebook → `f1721bd` → `606c35b`, push; `ci_checks` sạch
- [x] **CI GitHub XANH trên `606c35b`** (run `37915580140`, success) - các lượt đỏ liền trước đều do ĐÚNG
      một test thiếu torch, không có lỗi nào khác (đã đọc log của run `37914121125`)
- [x] **Sửa KHE HỞ đã biết:** `preflight` in bộ tách từ theo FILE MODEL và `bootstrap` tải 27 MB model Java
      theo file model, trong khi lớp thí nghiệm ĐÈ được `preprocess.segmenter` ⇒ dòng in trong notebook
      nói một bộ còn dữ liệu chia bằng bộ khác, và lượt khai `vncorenlp` cho model khai `none` thì máy ảo
      **thiếu** đúng thứ nó cần (lỗi chỉ hiện ra sau khi đã tải trọng số). Nay cả hai đọc cấu hình **ĐÃ HỢP
      NHẤT** - cùng nguồn với đường huấn luyện. Thêm 1 test `preflight` + 2 test `bootstrap` (hai chiều
      ĐÈ) + `setUp` vá `load` cho cả lớp `ModelAssetsTest` - commit `9515701`
- [x] Ghim lại **cả 31 notebook** (Đ1 9 + Đ2 12 + Đ3 10) vào `9515701` → `a32e829`; CI GitHub XANH ở
      `9515701` (run `37917152136`) và ở `a32e829` (run `37917258537`)
- [x] **Bàn giao gói 022**: `handover/out/SentimentX-goi-022-a32e829-261009.zip` (69 file: 31 notebook + 31
      README thí nghiệm + 6 file dữ liệu **v0.3.0** train/val/test + README bàn giao). `handover/README.md`
      nay có mục "Đợt 11 - 31 notebook MỚI trong gói này (022)" với bảng 31 lượt (thứ tự chạy · câu hỏi ·
      khoá khác cha · thời gian), và con số notebook trong gói 67 → **98**
- [ ] Đ1 (CỔNG 1): chạy 9 notebook trên Colab
- [ ] Đ2 (CỔNG 2): chạy 12 notebook trên Colab (ba nhóm × bốn: bộ tách từ A/B1/B2 + nhánh emoji)
- [ ] Đ3 (CỔNG 3): chạy 10 notebook trên Colab (r = 8/32, lr = 1e-4/4e-4, 2 module thay vì 4)
- [x] Đ4: mã - `loss.type: focal` (kèm `loss.gamma` BẮT BUỘC > 0), `class_weight: inverse_by_aspect` (bảng
      `A x C`, đếm riêng từng khía cạnh), `lora.use_dora` (khoá TUỲ CHỌN), `KNOWN_KEYS` += 2 khoá, và 2 quy
      tắc mới: `ce` + trọng số bị TỪ CHỐI (trùng `weighted_ce`) - commit `ff4fd26`. **Hai lỗi thật bắt được
      bằng test số học:** (1) hàng nhãn có ĐÚNG `A` ô (một ô = một khía cạnh, KHÔNG phải `A x C`) nên công
      thức chia ô bản đầu của tôi sai - nó sẽ rơi trọng số sang khía cạnh khác mà không có gì báo; (2) công
      thức chuẩn hoá trọng số toàn cục phải giữ NGUYÊN, nếu không thì lượt `weighted_ce` đã chạy không còn
      là mốc so sánh
- [x] Đ4: 6 thí nghiệm (`phobert-base-v2/lora/exp021-023`, `cafebert/lora/exp017-019`) + chứng minh mỗi lượt
      khác cha ĐÚNG MỘT khoá; ghim 6 notebook → `ff4fd26` → `f230ef0`; `ci_checks` sạch + 9 bộ test xanh
- [x] **Bàn giao gói 023** (`handover/out/SentimentX-goi-023-f230ef0-261009.zip`, 13 file); `handover/README.md`
      thêm mục "Đợt 11 - 6 notebook MỚI (023)" + con số notebook 98 → **104**
- [x] Đ5: mã - `src/training/full.py` (mọi tham số học) + `src/training/savers/state_dict.py` (ghi CẢ model)
      + đăng ký `TRAINERS`/`SAVERS` + `head_state_of` cho vòng lặp dùng chung - commit `0d41b00`. Hai chẩn
      đoán mới: 4-bit bị TỪ CHỐI (đó là QLoRA, không phải full fine-tune); và **sửa một dòng IN SAI có sẵn**
      - lượt `none` mức SÀN trước đây in nhãn mặc định của đường LoRA ("chỉ adapter học") trong khi nó
      không có adapter nào
- [x] Đ5: 3 thí nghiệm (`phobert-base-v2/full/exp001-002`, `cafebert/full/exp001`) - chứng minh khác cha
      ĐÚNG `method` + `trainer` (riêng `exp002` thêm `lr`), nên phép so chỉ đổi MỘT biến: cơ chế học; ghim
      `0d41b00` → `a130424`; `ci_checks` sạch + bộ test xanh (test mới: `tests/training/test_full.py`)
- [x] **Bàn giao gói 024** (`handover/out/SentimentX-goi-024-a130424-261009.zip`, 7 file); README thêm mục
      "Đợt 11 - 3 notebook MỚI (024): FULL FINE-TUNE" + con số notebook 104 → **107**
- [x] **Đ6/Đ7 (PHẦN LÀM ĐƯỢC)**: thêm **3 model MỞ** - `qwen3-8b`, `qwen3-4b-thinking-2507`,
      `mistral-7b-instruct-v0.3` (`configs/models/*.yaml` + đăng ký `_chat_spec` trong `token_stats.MODELS`
      + ĐO token bằng prompt 5 ví dụ). **KHÔNG cần `chat_like.py`**: đã KIỂM `src/preprocessing/qwen.py`
      generic theo `model_id` (bản 0.6B và Qwen2.5 đang dùng chính nó; khoá `enable_thinking` chỉ được
      truyền khi config khai) - viết thêm một module nữa là tạo hai nguồn sự thật cho cùng một đường chat,
      đúng thứ dự án cấm. Đổi tên helper `_qwen_spec` -> `_chat_spec` cho đúng nghĩa.
- [x] Đ6/Đ7 (phần làm được): **8 notebook đã tạo + ghim + đóng gói** (gói **025** rồi **026** sau khi ghim
      lại vào bản CI xanh `0d9de8a`): `qwen3-8b/prompt-cot/exp001-003` (0/1/5 ví dụ),
      `qwen3-4b-thinking-2507/prompt-cot/exp001` (DÒ) + `exp002` (lượt chạy), `mistral-7b-instruct-v0.3/
      prompt-cot/exp001-003`. Mỗi lượt khác cha ĐÚNG khoá thuộc lớp model - đã kiểm, và script kiểm còn
      khẳng định `prompt`/`examples`/`system_prompt`/`n`/`decoding.*`/`data.version`/`data.roles` GIỐNG HỆT
      cha. **Phép ĐO token bắt được một lỗi thật:** tokenizer Llama-BPE của Mistral cho **3.194
      token/review** (Qwen3: 1.877) nên ngưỡng 2.304 sẽ **cắt 100% review** ⇒ đã nâng lên **3.584** (làm
      tròn lên của mẫu dài nhất 3.522) và ghi số đo vào config; Qwen3-8B/Thinking giữ 2.304 vì cùng họ
      tokenizer và **0% bị cắt**.
- [ ] **HAI model GATED chưa làm được**: `meta-llama/Llama-3.1-8B-Instruct` (họ Llama) và
      `Viet-Mistral/Vistral-7B-Chat` (tiếng Việt chuyên biệt, cùng cỡ Mistral). Đã THỬ TẢI và bị từ chối
      (`You are trying to access a gated repo`). Cần: `HF_TOKEN` (điền vào `.env` cho máy này và
      `.env.colab` cho Colab) + bấm nhận điều khoản trên trang model. Máy này KHÔNG có token HF nào trong
      `.env`/`.env.colab` (chỉ có `DAGSHUB_TOKEN` + `HF_HOME`). Sau khi có token, chỉ cần: 2 file
      `configs/models/*.yaml` + 2 dòng `_chat_spec` + đo token + 6 notebook.
      **Kiểm lại 10/10/2026 (theo yêu cầu người dùng): token HF KHÔNG tồn tại ở bất kỳ đâu** - không có chuỗi
      `hf_...` trong repo, không có `~/.cache/huggingface/token` hay `~/.huggingface/token`, không có biến
      `HF_TOKEN`/`HUGGING_FACE_HUB_TOKEN` trong môi trường máy, và không file env nào có khoá đó. Nay khoá đã
      **KHAI SẴN ở cả bốn tệp env**: `.env` và `.env.colab` để TRỐNG cho người dùng dán (khoá rỗng bị bỏ qua
      nên để trống vẫn chạy bình thường); `.env.example` + `.env.colab.example` (nơi DUY NHẤT khai biến mới,
      theo `docs/05_config/07_env.md`) có kèm chú thích cách lấy token; tài liệu env đã thêm dòng `HF_TOKEN`.
      **KHÔNG phải sửa mã**: Colab Secrets đọc tên này từ trước (`runtime._from_colab_secrets`) và
      `scripts/run_notebook.py::forward_env` chuyển tiếp MỌI khoá không-trống của `.env` cho kernel.
      Việc còn lại chỉ NGƯỜI DÙNG làm được: tạo token quyền Read ở https://huggingface.co/settings/tokens →
      bấm **Agree** trên cả hai trang model GATED → dán vào `.env` (máy này) và Colab Secrets (Colab).
      Kiểm bằng `python _scratch/check_hf_access.py` (in tên tài khoản + thử tải `config.json` của từng repo).
- [x] **Sửa một LỖI THẬT phát hiện khi kiểm lại đường ghim**: 3 notebook Đ5 (`full/exp001-002`,
      `cafebert/full/exp001`) ghim vào `0d41b00` - commit đó **chỉ chứa mã, KHÔNG chứa `config.yaml`** của
      chúng (config được thêm ở commit sau), nên notebook sẽ clone repo rồi chết ở ô kiểm trước vì thiếu
      file cấu hình. Kiểm bằng `git ls-tree` trên từng commit đã ghim (Đ1-Đ3 `9515701` ✓, Đ4 `ff4fd26` ✓,
      Đ6/Đ7 `0d9de8a` ✓). **Đã ghim lại CẢ 48 notebook vào MỘT revision xanh `4aaac5c`** - commit `e0e87b0`,
      kiểm lại: 48/48 ghim đúng, **0 notebook còn "chưa ghim"**
- [x] **Bàn giao lại thành MỘT gói**: `handover/out/SentimentX-goi-027-e0e87b0-261009.zip` (**49 file: 48
      notebook + README**) - một revision, một gói, nên không thể lẫn hai bản code giữa các lượt.
      `handover/README.md` nay nói rõ: dùng **027** là đủ (022/023/024/026 là bản gửi trước, 025 bị 026 thay
      thế), và có thêm mục **"Đợt 11 - thứ tự chạy 48 notebook (giảm dần theo thời gian)"** + 2 ghi chú về
      thứ tự (DÒ trước lượt "suy nghĩ"; hai lượt SÀN nên nằm ở phiên đầu để kiểm ống dẫn)
- [x] **SỬA LỖI CHẶN do chính nhóm gây ra, rồi gói lại (09/10/2026)**: người chạy mở 8 notebook đầu của gói
      027 → cả 8 DỪNG ở ô kiểm trước: *"Thí nghiệm khai `data.version` v0.2.0 nhưng file config dataset khai
      v0.3.0"*. Ba chỗ nạp file phiên bản dữ liệu (ô cấu hình notebook, `preflight`, `plan`) đều gọi hàm nạp
      mà THIẾU `data.version` ⇒ hàm đó lấy bản mới nhất ⇒ preflight tự tạo ra cái lệch rồi DỪNG (45/48 lượt
      khai v0.2.0), còn đường chạy thì sẽ **lặng lẽ chấm trên v0.3.0** nếu ai bỏ phép kiểm - đúng loại lỗi
      im lặng dự án cấm. Sửa: MỘT chỗ quyết định - `experiments.dataset_of(config)` cho cả notebook,
      `preflight`, `checks` và `plan` (commit `7d69b32`, `4f65864`); bản cũ = một **dòng ghi chú**, bản
      KHÔNG tồn tại = DỪNG kèm danh sách bản đang có; **+5 test** (kể cả test khoá mẫu notebook). Ghim lại
      **48/48** notebook vào `4f65864` (commit `c96dec8`); kiểm bằng chính công cụ dự án:
      `run_notebook.py <exp> --preflight-only` cho **48/48 xanh** (có đủ 8 notebook đã chặn). Gói mới:
      **`SentimentX-goi-028-c96dec8-261009.zip`** (49 file) - giữ nguyên 48 notebook, cấu hình và thứ tự chạy.
      Sau đó phát hành **`SentimentX-goi-029-...`** (09/10/2026): bản này **chỉ sửa TÀI LIỆU trong
      `handover/README.md`** - thêm **dòng cộng đủ 48** ngay dưới tiêu đề bảng thứ tự chạy, sửa cách đếm dòng
      "~13-16 phút" (`exp011` → `exp023` là **13** lượt, không phải 14), và gắn nhãn **CHỜ NHÓM GHIM LẠI** cho
      `qwen3-4b-thinking-2507/prompt-cot/exp002`. 48 notebook y nguyên, cùng một revision; không sửa code,
      config hay dữ liệu.
- [x] **Kiểm OFFLINE tokenizer 3 LLM mới + 3 bộ tách từ (09/10/2026)**: prompt dựng đúng chat template
      từng họ (`<|im_start|>system...` cho hai bản Qwen, `<s>[INST] ...` cho Mistral) và số token đo lại
      **khớp đúng** bảng đã ghi: 5 ví dụ ở `test` - `qwen3-8b` TB 1.878,34 / max **1.993** (ngưỡng 2304,
      0% cắt), `qwen3-4b-thinking-2507` TB 1.880,34 / max **1.995** (2304, 0% cắt), `mistral-7b-instruct-v0.3`
      TB 3.194,50 / max **3.380** test - **3.522** train (ngưỡng **3584**, 0% cắt). Ba bộ tách từ đối chứng
      đều chạy được trên máy này (`pyvi` 0.1.1, `underthesea` 9.5.0, `vncorenlp` Java 17) và **cho kết quả
      khác nhau thật** (PhoBERT: `none` TB 33,68 vs `pyvi` 30,29; ViBERT 37,16 vs 40,20; `<unk>` 0,90% vs
      8,03%) ⇒ phép ablation có tín hiệu, không phải lượt trùng. Số này nay ghi ở
      `docs/04_experiments/02_model_input.md` (mục 4.3, phần "Đợt 11").
- [ ] Bảng token ĐÃ GHI của Mistral còn cột `max_length` cũ (2304 - thời điểm bảng được dựng) nên vẫn ghi
      `% review > max_length = 100.0`. **Số ĐO trong bảng vẫn đúng** (TB/p99/max đã kiểm chéo khớp từng con số);
      chỉ cột ngưỡng là cũ, và nó **không ảnh hưởng lượt chạy** (config đọc 3584). Để bảng khớp config thì chạy
      `python run_token_stats.py --hash e616c1e3 --prompt absa_cot_5shot_v1 --system absa_cot` - **trên Colab
      hoặc máy có mạng tới HF Hub**: trên máy này (09/10/2026) lượt đo đứng im ở bước nạp bộ tách từ/ tokenizer
      của các encoder quá 25 phút dù CPU vẫn chạy, nên đã dừng; công cụ này không in tiến độ nên không biết
      đang ở model nào. KHÔNG chạy nền kèm chuyển hướng output: `py-vncorenlp` trao đổi với tiến trình Java
      qua stdio nên chuyển hướng là treo.
- [x] **RÀ SOÁT TOÀN KẾ HOẠCH (09/10/2026) - đếm lại bằng chính file trên đĩa, không bằng trí nhớ**:
      **115** thí nghiệm trong repo = **48** lượt đợt 11 (tất cả ghim `4f65864`) + **67** lượt cũ (12 revision cũ).
      **0/48** lượt mới có thư mục kết quả ⇒ 48 lượt "đã tạo + đã ghim + đã gói" nhưng **CHƯA CHẠY**; **61** thư mục
      kết quả trên đĩa đều của lượt cũ, trong đó 5 thư mục có 2 bản ghi = đúng "năm thư mục kết quả HỎNG 04/10"
      mà `handover/README.md` nói. **CHƯA TẠO**: 6 lượt GATED (`llama-3.1-8b-instruct` ×3, `vistral-7b-chat` ×3 -
      không có thư mục `experiments/llama*`/`vistral*` nào) + 2 lượt partial FT tuỳ chọn của Đ5 (không có thư mục
      method `partial` nào). **6 lượt CŨ không có kết quả**: `qwen3-0.6b/prompt-cot/exp006-007` và
      `qwen3-4b-instruct-2507/prompt-cot/exp018-021` - cần xác nhận là cố ý (ngoài phạm vi đợt 11).
      **Hai lỗi ĐẾM trong tài liệu (không phải lỗi code/config) đã sửa**: `handover/README.md` ghi dòng "~13-16
      phút" là "(14 lượt)" cho `exp011` → `exp023` (đúng: **13**; 14 là số của cả dòng) - chính lỗi này làm một
      người đọc bảng đếm ra 49 lượt; và bảng §4 ở trên ghi Đ5 "2" trong khi đã tạo **3**. Nay bảng thứ tự chạy có
      **dòng cộng 2+4+2+1+2+14+14+6+1+1+1 = 48**, lượt `qwen3-4b-thinking-2507/prompt-cot/exp002` có nhãn **CHỜ
      NHÓM GHIM LẠI**, và §4 có thêm cột **Đã tạo**. **CI (luật 22)**: mọi run từ `0d9de8a` trở đi đều XANH;
      riêng `4f65864` không có run mang đúng SHA đó vì `4f65864` và `c96dec8` đi trong CÙNG một lần `push` nên
      GitHub chỉ chạy cho đỉnh (`c96dec8` = xanh) - nội dung `4f65864` đã được CI kiểm trong run đó, bản ghim là
      đáng tin; ai muốn có run mang đúng SHA thì đẩy thêm một commit rỗng, **không** cần ghim lại notebook nào.
- [ ] Đ8 (báo cáo): các mục M1/M2/M3/M5/M6/M7/M9 còn thiếu SỐ, chờ các cổng chạy




## 9. Cập nhật 10/10/2026 - chạy smoke trên máy cá nhân, bốn lỗi nhỏ đã sửa

**Ba lượt smoke (bộ tối thiểu đã chốt), chạy THẬT trên RTX 3050 6 GB:**

| # | Lượt | Kết quả |
| --- | --- | --- |
| 1 | `phobert-base-v2/none/exp001` (SÀN) | **PASS** 6,9 giây: `trainable_params: 0` / `total_params: 135.014.421`, `số bước: 0`, sentiment macro-F1 0,126 (vô nghĩa ĐÚNG mức SÀN) ⇒ ống dẫn nạp-chấm-ghi đúng |
| 2 | `phobert-base-v2/none/exp002` (LINEAR PROBE) | Đường chạy ĐÚNG: in `16149 tham số học / 135014421 tổng`, val F1 0,188 → 0,329, có lưu `model/best`. **Chủ động dừng** ở bước ~600/4.602 vì `--limit` KHÔNG rút ngắn phần huấn luyện (xem lỗi 4) |
| 3 | `cafebert/none/exp001` (SÀN) | **PASS** 11,9 giây: `trainable_params: 0` / `total_params: 559.911.957`, `số bước: 0`, sentiment macro-F1 0,169 |

Cả ba ghi đủ 7 tệp (đường encoder thêm `probabilities.csv`), và preflight in đúng dòng "đọc bản thí nghiệm
khai v0.2.0, KHÔNG phải bản mới nhất" ⇒ **bản sửa lỗi chặn `data.version` của đợt 11 đã được xác nhận đầu-cuối**.

**Bốn lỗi nhỏ do chính lượt smoke tìm ra, đã sửa (mỗi lỗi kèm test):**

| Lỗi | Sửa | Test | Commit |
| --- | --- | --- | --- |
| `.env` còn dòng `SENTIMENTX_MODEL` ⇒ lượt PhoBERT nạp Qwen3-4B rồi chết `RuntimeError: bad allocation` | `plan()` **IN CẢNH BÁO** khi nguồn trọng số bị đè sang model KHÁC (`model_override_note`); trỏ vào thư mục CÙNG TÊN model thì im lặng | `test_experiment_run.py::ModelOverrideNoteTest` (4 ca) | `e2bfefd` |
| Lượt SÀN in nhãn "ĐÓNG BĂNG - chỉ adapter học" dù nó KHÔNG có adapter nào | Nhãn lấy từ CÁCH HUẤN LUYỆN (`training.head_state`) chứ không từ mỗi `head.trainable` | `test_training.py::HeadStateByTrainerTest` (7 ca) | `4606df7` |
| Mất sạch phần ghi nhận MLflow: `Cannot set a deleted experiment 'sentimentx-absa'` | Tự **KHÔI PHỤC** (hoặc TẠO LẠI) experiment rồi nối tiếp; không xong thì `[WARN] ... KHÔNG sửa được` | `test_tracking.py::DeletedExperimentTest` (7 ca) | `09598eb` |
| Ô cuối notebook ném `NameError: run_result` khi ô CHẠY lỗi (trái luật đã ghi ở `10_template_notebook.md`) | Ô kết thúc có khối `if "run_result" not in globals():` in ra việc cần làm | `test_templates.py::test_o_ket_thuc_chiu_duoc_khi_chua_co_ket_qua` | `9a50b92` |

**Thêm cờ `--smoke` / `--epochs` cho `scripts/run_notebook.py`** (`31da713`): `--limit` chỉ ép số MẪU CHẤM
nên lượt chạy thử vẫn học hết 12.268 review × 3 epoch (1-2 giờ trên GPU 6 GB). `--smoke` = `--limit 8
--epochs 1`; đã kiểm bằng tay rằng giá trị ép **đi tới tận** `plan()["training"]["epochs"] = 1`. Kèm theo
đó sửa câu nói **SAI** rằng tên thư mục kết quả có `n8` (tên thư mục là mã băm của danh tính lượt chạy,
không mang dấu nào) - muốn biết một thư mục là lượt chạy thử thì đọc `subset.limit` và `training.epochs`
trong chính `metrics.json` của nó. Tài liệu: `2c55487`.

**Ba thư mục kết quả smoke** (untracked, KHÔNG tính vào bảng điểm, xoá được bất cứ lúc nào):
`experiments/phobert-base-v2/none/exp001/results/`, `.../exp002/results/`, `experiments/cafebert/none/exp001/results/`.

**Một test đỏ CÓ SẴN TỪ TRƯỚC, không do đợt này**: `tests/training/test_full.py::FullBuildModelTest::
test_every_parameter_is_trainable` - `mock.patch("transformers.AutoModel")` gặp `KeyError: 'AutoModel'`
khi chạy CẢ bộ test nhưng PASS khi chạy riêng (`transformers` 5.17 nạp lười thuộc tính đó). Đã chứng minh
bằng cách cất TOÀN BỘ thay đổi của đợt này rồi chạy lại: `Ran 1054 ... FAILED (errors=1)` y hệt.

## 10. Cập nhật 10/10/2026 (chiều) - HAI lỗi THẬT do các lượt chạy trên Colab tìm ra, đã sửa + ghim lại

Người chạy báo về từ chính các notebook của gói **029**. Hai lỗi nằm ở **CODE** (không phải config, không
phải máy), và cả hai đều thuộc loại "chỉ hiện với MỘT SỐ model" nên đã lọt qua 48 lượt preflight, ba lượt
smoke trên RTX 3050 và cả bộ test.

| # | Lỗi (nguyên văn) | Nguyên nhân THẬT | Sửa | Test |
| --- | --- | --- | --- | --- |
| 1 | `ValueError: Asking to pad but the tokenizer does not have a padding token` ở `mistral-7b-instruct-v0.3/prompt-cot/exp001` (và `exp002`/`exp003`) | Tokenizer của Mistral **KHÔNG có `pad_token`**, mà sinh theo LÔ (`inference.batch_size: 4`) thì `apply_chat_template(padding=True)` bắt buộc phải đệm. Qwen3 **có sẵn** `pad_token` ⇒ các lượt khác không lộ: đường chạy trước đây chỉ đúng với model "may mắn có `pad_token`" | MỘT cửa duy nhất: `qwen.ensure_padding` (gọi trong `tokenizer()` và `use_tokenizer()`) lấy `eos_token` làm `pad_token` và đặt `padding_side = left`, in một dòng `tokenizer <model>: pad_token = eos_token ...` ở đầu lượt chạy. KHÔNG tự thêm token đệm (thêm là phải `resize_token_embeddings`) | `test_qwen.py::EnsurePaddingTest` (7 ca) |
| 2 | `torch.OutOfMemoryError` ở `qwen3-4b-thinking-2507/prompt-cot/exp001` (lượt DÒ) | Lô 8 × (ngưỡng cắt 2.304 + trần 8.192) = 83.968 vị trí; KV cache của Qwen3-4B là **144 KB mỗi token một chuỗi** (36 lớp × 8 đầu KV × 128 chiều × 2 × 2 byte) ⇒ **~11,5 GB**, vượt 14,56 GB của T4 | (a) `inference.batch_size` của model này 8 → **2** (~2,9 GB) + `config_version` 1 → 2; (b) thêm phép **ĐẾM TRƯỚC** `runner.check_generation_memory`: ước lượng KV cache rồi DỪNG ngay trước khi sinh nếu vượt 60% VRAM, kèm con số `inference.batch_size` nên đặt; (c) `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` đặt trước lần `import torch` đầu tiên | `test_runner.py::GenerationMemoryTest` (9 ca) |
| 3 | (không phải lỗi) lượt `qwen3-4b-thinking-2507/prompt-cot/exp002` chưa chạy | trần sinh đang là giá trị TẠM 4.096, chờ số đo của `exp001` | giữ nguyên: vẫn **CHỜ NHÓM GHIM LẠI** | - |

**Kiểm OFFLINE bằng chính hàm của đường chạy** (`_scratch/verify_kv.py`): với số kiến trúc đọc từ
`config.json` THẬT của từng model và VRAM của T4, phép đếm mới **KHÔNG chặn oan lượt nào** trong số các lượt
đường prompt, và **CHẶN ĐÚNG** lượt DÒ ở lô CŨ 8 - tức đúng thứ đã đổ trên Colab. Số của Mistral đã đối
chiếu: `config.json` của Mistral **không khai `head_dim`**, nên nhánh suy ra (`hidden_size` chia **số đầu
attention** = 128) mới là nhánh được dùng thật; bản đầu của phép đếm chia cho số đầu KV (512) và làm ước
lượng vống lên 4 lần - một test bắt được lỗi đó TRƯỚC khi ghim.

**Phép kiểm mới phải CHỊU được vật giả của test**: `check_generation_memory` gọi `int(...)` trên `config`, mà
test đưa vào một `Mock` ⇒ `TypeError`, làm đỏ `test_experiment_run.py::RunIdentityTest`. Đã sửa: chỉ nhận
**số nguyên dương thật** (`runner._positive_int`), thiếu thông tin thì BỎ QUA phép kiểm (không đoán).

**Ghim lại + gói**: 48/48 notebook ghim lại vào commit chứa hai bản sửa, `run_notebook.py --preflight-only`
xanh **48/48**, gói **030** (thay **029**). Ba lượt Mistral và lượt DÒ đã hỏng chỉ cần chạy lại (chế độ
RESUME, chưa có lô nào xong); lượt DÒ chạy ở lô 2 nên **dài hơn hẳn** (ước tính 2-4 giờ, đã ghi vào
`handover/README.md` cùng ghi chú 3 về thứ tự chạy).


## 11. Cập nhật 10/10/2026 (tối) - LỖI THẬT THỨ BA, do bốn lượt ViSoBERT tìm ra: thiếu `import bert_like`

Bốn lượt `visobert/lora/exp006..009` của gói 030 (revision `2850d03`) đổ NGAY ở bước dựng input:

    NameError: name 'bert_like' is not defined      (src/preprocessing/visobert.py, build_inputs)

Nguyên nhân: `visobert.py` viết tay; `build_inputs` gọi `bert_like.prepared(...)` để áp
`preprocess.segmenter`, nhưng file **không import `bert_like`**. Bốn encoder thêm ở đợt 7
(`phobert-large`, `vibert`, `cafebert`, `xlmroberta`) đều đi qua `bert_like` và đã import đúng, nên chỉ
ViSoBERT lộ. Đường ĐO (`encode`) không đụng `bert_like` nên `run_token_stats.py` vẫn xanh - đúng loại
lỗi chỉ hiện ở đường HUẤN LUYỆN (cùng họ với hai lỗi pad-token / KV-cache ở §10).

Sửa - commit `a0a5240`:
- `src/preprocessing/visobert.py`: thêm một dòng `from src.preprocessing import bert_like`.
- `tests/preprocessing/test_encoders.py`: `VisobertBuildInputsTest` (gọi `build_inputs` với tokenizer
  giả, khoá ĐÚNG ca này) + `EncoderModuleImportTest` (AST: module trong `src/preprocessing/` dùng
  `bert_like.`/`segmenters.`/`model_config.` thì phải import tên đó - chặn cả HỌ lỗi, không chỉ ca này;
  dò import bằng AST nên chịu được dạng `from ... import (a, b)`).

Kiểm: `ci_checks` sạch; `unittest` **1096 test, còn đúng 1 test đỏ CÓ SẴN của môi trường**
(`tests/training/test_full.py::test_every_parameter_is_trainable`, scipy/numpy - xem §9).

Ghim lại: CHỈ bốn notebook `visobert/lora/exp006..009` -> `a0a5240` (commit `556c48d`). 44 notebook còn
lại GIỮ NGUYÊN ghim `2850d03` vì không có gì khác đổi. Gói bàn giao: **031** (chỉ bốn notebook ViSoBERT
+ `handover/README.md`).
