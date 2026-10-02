# Vì sao có từng thí nghiệm (bản báo cáo)

> Đọc file này khi: báo cáo trước lớp/giảng viên về 12 thí nghiệm đã khai của đợt chạy (9 đã có kết quả).
> Liên quan: `docs/04_experiments/08_experiment_rationale.md` (bản đầy đủ), `presentations/experiment_tree.md` (cây)

## Bối cảnh chung (áp cho MỌI lượt)

| Hạng mục     | Giá trị                                                                                                                                                  |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Bài toán     | ABSA tiếng Việt trên review son mỹ phẩm Shopee; 7 khía cạnh; `binary` (positive/negative) + "có nhắc tới hay không" là quyết định riêng; neutral bị loại |
| Đích so      | Công bố _Applying Prompt Engineering to Sentiment Analysis of Vietnamese Reviews_ (GPT-4o-mini, CoT 0/1/5-shot)                                          |
| Dữ liệu      | `cosmetics-ds0.2.0-...-e616c1e3` - train 12.268 · val 1.535 · test 1.623                                                                                 |
| Cách chấm    | chấm cả split `test`, sinh `greedy` (tất định), 5 scorer                                                                                                 |
| Hai cơ sở đo | `all` (cách dự án) · `paper` (cách công bố) → so công bố đọc `paper`                                                                                     |
| Bật học?     | chỉ hai lượt LoRA encoder; mười lượt prompt không huấn luyện                                                                                             |

## Bốn nhóm, mười hai thí nghiệm (chín đã có kết quả)

### A. Hai encoder nhỏ học LoRA (2 lượt) - nhóm duy nhất phải huấn luyện

| Thí nghiệm                    | Câu hỏi                                                | Kết quả (acc TB · F1 macro)                            |
| ----------------------------- | ------------------------------------------------------ | ------------------------------------------------------ |
| `visobert/lora/exp001`        | Encoder đọc nguyên bản, học LoRA thì bằng nào công bố? | 94,86 · 0,765 (phát hiện khía cạnh tốt nhất: F1 0,966) |
| `phobert-base-v2/lora/exp001` | Encoder có tách từ, học LoRA thì bằng nào?             | 88,40 · 0,540 (`stayingpower` 64,71)                   |

### B. Qwen3-4B + CoT (6 lượt) - tái hiện công bố + đối chứng lượng hoá

| Thí nghiệm          | Câu hỏi                                  | Kết quả               | So công bố           |
| ------------------- | ---------------------------------------- | --------------------- | -------------------- |
| `prompt-cot/exp002` | Đúng mức COT+0-shot của công bố          | 97,16 · 0,895         | −0,21                |
| `prompt-cot/exp003` | COT+1-shot: thêm một ví dụ có tăng điểm? | **97,72** · **0,926** | **+0,02**            |
| `prompt-cot/exp004` | COT+5-shot, mức nặng nhất của công bố    | 97,11 · 0,902         | **+0,38**            |
| `prompt-cot/exp005` | 4-bit mất bao nhiêu điểm - mức 0 ví dụ   | 96,62 · 0,896         | (đối chứng `exp002`) |
| `prompt-cot/exp006` | ... mức 1 ví dụ                          | 96,60 · 0,909         | (đối chứng `exp003`) |
| `prompt-cot/exp007` | ... mức 5 ví dụ                          | 96,48 · 0,899         | (đối chứng `exp004`) |

### C. Qwen3-4B hỏi MỘT lượt (1 lượt) - mốc so cho CoT

| Thí nghiệm               | Câu hỏi                                      | Kết quả                                            |
| ------------------------ | -------------------------------------------- | -------------------------------------------------- |
| `prompt-one-turn/exp001` | Bỏ suy luận từng bước thì 4B được bao nhiêu? | 95,33 · 0,871 → **thấp hơn CoT 0 ví dụ 1,83 điểm** |

### D. Qwen3-0.6B + CoT (3 lượt) - biến về QUY MÔ

| Thí nghiệm                          | Câu hỏi                                 | Trạng thái                                                                     |
| ----------------------------------- | --------------------------------------- | ------------------------------------------------------------------------------ |
| `qwen3-0.6b/prompt-cot/exp001..003` | Model nhỏ hơn ~7 lần thì kém bao nhiêu? | **không dùng** - ba lượt nạp nhầm trọng số 4B, kết quả đã xoá; là việc kế tiếp |

## Ba điều phải nói khi trình bày số

1. Số so công bố là cơ sở `paper`; bảng `experiment_registry` in cơ sở `all` - hai số khác nhau cách đếm.
2. Lượt chạy tiếp (RESUME) ghi `n_samples` là mẫu của **phiên cuối**, không phải số mẫu đã chấm.
3. Nhóm fp16 khác nhóm 4-bit hai biến (lượng hoá và `batch_size`), nên chưa quy chênh lệch cho lượng hoá.
