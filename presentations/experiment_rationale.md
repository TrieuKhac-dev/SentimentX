# Vì sao có từng thí nghiệm (bản báo cáo)

> Đọc file này khi: báo cáo trước lớp/giảng viên về các thí nghiệm đã chạy của dự án (17 lượt đã có kết quả).
> Liên quan: `docs/04_experiments/08_experiment_rationale.md` (bản đầy đủ), `presentations/experiment_tree.md` (cây),
> `presentations/result_analysis.md` (bảng số và kết luận)

## Bối cảnh chung (áp cho MỌI lượt)

| Hạng mục     | Giá trị                                                                                                                                                  |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Bài toán     | ABSA tiếng Việt trên review son mỹ phẩm Shopee; 7 khía cạnh; `binary` (positive/negative) + "có nhắc tới hay không" là quyết định riêng; neutral bị loại |
| Đích so      | Công bố _Applying Prompt Engineering to Sentiment Analysis of Vietnamese Reviews_ (GPT-4o-mini, CoT 0/1/5-shot)                                          |
| Dữ liệu      | `cosmetics-ds0.2.0-...-e616c1e3` - train 12.268 · val 1.535 · test 1.623                                                                                 |
| Cách chấm    | chấm cả split `test`, sinh `greedy` (tất định), 5 scorer                                                                                                 |
| Hai cơ sở đo | `all` (cách dự án) · `paper` (cách công bố) → so công bố đọc `paper`                                                                                     |
| Bật học?     | chỉ bốn lượt LoRA encoder; mười ba lượt prompt không huấn luyện                                                                                             |

## Năm nhánh, mười bảy lượt có kết quả (A: 4 · B: 9 · E: 3 · F: 1; nhánh G chưa có kết quả)

### A. Hai encoder nhỏ học LoRA (4 lượt) - nhóm duy nhất phải huấn luyện

| Thí nghiệm                    | Câu hỏi                                                | Kết quả (acc TB · F1 macro)                            |
| ----------------------------- | ------------------------------------------------------ | ------------------------------------------------------ |
| `visobert/lora/exp001`        | Encoder đọc nguyên bản, học LoRA thì bằng nào công bố? | 94,86 · 0,765 (phát hiện khía cạnh tốt nhất: F1 0,966) |
| `visobert/lora/exp002`        | Thêm `weighted_ce` + `inverse` có cứu lớp âm không?    | 95,61 · 0,836 (F1 lớp âm 0,765 → 0,836)                |
| `phobert-base-v2/lora/exp001` | Encoder có tách từ, học LoRA thì bằng nào?             | 88,40 · 0,540 (`stayingpower` 64,71)                   |
| `phobert-base-v2/lora/exp002` | như trên, chỉ thêm `weighted_ce` + `inverse`           | **96,62** · **0,876** (F1 lớp âm 0,540 → 0,876)        |

Điều đắt giá nhất của nhánh này: **sửa HÀM MẤT MÁT cứu được lớp âm** (+8,22 điểm ở PhoBERT, F1 âm
0,540 → 0,876) còn sửa câu chữ prompt thì không (nhánh E); và **đảo thứ hạng** hai encoder (gốc ViSoBERT
hơn 6,46 điểm, sau đó PhoBERT hơn 1,01 điểm). Giá phải trả: **phát hiện khía cạnh giảm** (PhoBERT
98,05 → 94,14; ViSoBERT 98,29 → 97,06) nên hai chỉ số phải báo cáo theo cặp.

### B. Qwen3-4B + CoT (9 lượt) - tái hiện công bố + đối chứng lượng hoá

| Nhóm (ba mức ví dụ 0/1/5)   | Câu hỏi                                              | Kết quả                | So công bố            | Số ô                     |
| --------------------------- | ---------------------------------------------------- | ---------------------- | --------------------- | ------------------------ |
| 4-bit lô 8 `exp002/003/004` | đúng ba mức COT+0/1/5-shot của công bố                | 97,16 · **97,72** · 97,11 | −0,21 · **+0,02** · +0,37 | 2.415 / 2.315 / 2.378    |
| fp16 lô 4 `exp005/006/007`  | bỏ lượng hoá (**đổi cả cỡ lô** vì fp16 tốn bộ nhớ hơn) | 96,62 · 96,60 · 96,48  | −0,74 · −1,10 · −0,26 | 2.580 / 2.461 / 2.520    |
| 4-bit lô 4 `exp008/009/010` | **chỉ** đổi lượng hoá, giữ lô 4 (một biến)             | 97,26 · **97,77** · 97,19 | −0,10 · **+0,07** · +0,45 | 2.414 / 2.324 / 2.375 |

Đọc bảng này: (a) **tái hiện công bố ĐẠT** ở mức 1 và 5 ví dụ; (b) **mức 1 ví dụ là tốt nhất**, thêm tới 5
ví dụ không tăng; (c) bản 4-bit **hơn** fp16 0,64 / 1,17 / 0,71 điểm khi so sạch một biến, **nhưng trả lời
ít hơn 5-6% số ô** ⇒ phải đọc kèm số ô; (d) đỉnh `exp009` 97,77 chỉ hơn công bố 0,07 điểm, tức **trong
nhiễu** của một lần chạy greedy.

### E. Ba biến thể bộ 1 ví dụ (3 lượt) - CẢ BA ĐỀU ÂM

| Thí nghiệm           | Đổi đúng một thứ so với `exp003`        | Kết quả                                       |
| -------------------- | --------------------------------------- | --------------------------------------------- |
| `prompt-cot/exp011`  | nội dung VÍ DỤ (bản v2 có ba nhãn âm)    | 97,63 (**−0,09**) · F1 `price` âm 0,600 → **0,308** |
| `prompt-cot/exp012`  | CÂU CHỮ prompt: thêm bước 0 quét phàn nàn | 96,52 (**−1,20**) · 2.305 ô                   |
| `prompt-cot/exp013`  | CÂU CHỮ prompt: thêm lưu ý lệch nhãn    | 92,66 (**−5,06**) · chỉ còn 1.972 ô (mất 343) |

### F. Qwen3-4B hỏi MỘT lượt (1 lượt) - mốc so cho CoT

| Thí nghiệm               | Câu hỏi                                      | Kết quả                                            |
| ------------------------ | -------------------------------------------- | -------------------------------------------------- |
| `prompt-one-turn/exp001` | Bỏ suy luận từng bước thì 4B được bao nhiêu? | 95,33 · 0,871 → **thấp hơn CoT 0 ví dụ 1,83 điểm** |

### G. Qwen3-0.6B + CoT (0 lượt dùng được) - biến về QUY MÔ

| Thí nghiệm                          | Câu hỏi                                 | Trạng thái                                                                                                                    |
| ----------------------------------- | --------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `qwen3-0.6b/prompt-cot/exp001..003` | Model nhỏ hơn ~7 lần thì kém bao nhiêu? | **chưa có kết quả**: sáu thư mục kết quả đã xoá 04/10/2026 - ba lượt nạp nhầm trọng số 4B, ba lượt đúng 0.6B nhưng **bật suy nghĩ** ăn hết trần 400 token; sẽ chạy lại với `enable_thinking: false` |

## Bốn điều phải nói khi trình bày số

1. Số so công bố là cơ sở `paper`; bảng `experiment_registry` in cơ sở `all` - hai số khác nhau cách đếm.
2. Lượt chạy tiếp (RESUME: `exp004`, `exp010`) ghi `seconds` và `n_samples` là của **phiên cuối**, không
   phải cả lượt.
3. Nhóm fp16 lô 4 khác nhóm 4-bit lô 8 **HAI biến** (lượng hoá và cỡ lô); muốn nói về lượng hoá thì dùng
   cặp **sạch một biến** `exp008/009/010` so với `exp005/006/007`, và **luôn đọc kèm số ô**.
4. `price` âm chỉ có **6 ô** ở `test` (train 15, `val` 0) ⇒ F1 ở lớp đó là nhiễu; `price` phải đọc bằng
   **đếm + danh sách 6 ô**, và **`price` không có ngưỡng** (vì `val` có 0 ô âm).
