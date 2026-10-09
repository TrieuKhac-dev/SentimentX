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

| Đợt | Nội dung | Lượt | ~GPU | Mục |
| --- | --- | --- | --- | --- |
| Đ1 | `trainer: none` (SÀN + PROBE) ×2 model · `best_metric: accuracy_cell` ×3 · thước nhiễu head ×2 | 9 | ~2 h | 1, 3, 4 |
| Đ2 | Tiền xử lý: segmentation ×3 · `underthesea` ×3 · `pyvi` ×3 · icon ×3 + pipeline `v0.3.0` | 12 | ~3 h | 2 |
| Đ3 | Wave 1 tham số LoRA ×2 model | 10 | ~2,5 h | 5 |
| Đ4 | `focal` · `inverse_by_aspect` · DoRA ×2 model | 6 | ~1,5 h | 6, 7 |
| Đ5 | Full fine-tune ×2 model (+ partial FT tuỳ chọn ×2) | 2 (+2) | ~1,5-3 h | 1, 7 |
| Đ6 | Qwen3-8B ×3 mức · Qwen3-4B-Thinking (DÒ + 1 lượt) | 5 | ~2-4 h | 9 |
| Đ7 | Llama-3.1-8B · Mistral-7B · Vistral-7B ×3 mức | 9 | ~5 h | 10 |
| Đ8 | Viết báo cáo (10 mục) | 0 | 0 | 8, 11 |

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
- [ ] **HAI model GATED chưa làm được**: `meta-llama/Llama-3.1-8B-Instruct` (họ Llama) và
      `Viet-Mistral/Vistral-7B-Chat` (tiếng Việt chuyên biệt, cùng cỡ Mistral). Đã THỬ TẢI và bị từ chối
      (`You are trying to access a gated repo`). Cần: `HF_TOKEN` (điền vào `.env` cho máy này và
      `.env.colab` cho Colab) + bấm nhận điều khoản trên trang model. Máy này KHÔNG có token HF nào trong
      `.env`/`.env.colab` (chỉ có `DAGSHUB_TOKEN` + `HF_HOME`). Sau khi có token, chỉ cần: 2 file
      `configs/models/*.yaml` + 2 dòng `_chat_spec` + đo token + 6 notebook.
- [ ] Đ8 (báo cáo): các mục M1/M2/M3/M5/M6/M7/M9 còn thiếu SỐ, chờ các cổng chạy



