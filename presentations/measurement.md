# Cách đo của dự án (SentimentX)

> Đọc file này khi: trình bày cách dự án đo chất lượng model, hoặc giải thích một con số trong báo cáo.
> Liên quan: `docs/04_experiments/metrics.md`, `docs/04_experiments/reference_publication.md`

## 1. Đo trên tập nào

Chấm trên **split `test`** - chính là **tập test công khai của bài nguồn** (đã đối chiếu từng byte;
xem `docs/04_experiments/reference_publication.md`). Pipeline **không sửa** `test`, và tập này bị khoá
bằng `eval_lock.json`, nên số đo so trực tiếp được với công bố.

## 2. Hai câu hỏi phải tách rời

| Câu hỏi | Metric | Ý nghĩa |
| --- | --- | --- |
| Khía cạnh này **có được nhắc** không? | `aspect_detection` | nhị phân "có/không": P/R/F1 của việc NHẬN RA khía cạnh |
| Đã nhận ra thì **chọn đúng sắc thái** chưa? | `accuracy`, `prf` | độ chính xác và P/R/F1 khi chọn `positive`/`negative` |

Gộp hai câu hỏi là che mất kiểu lỗi thật: thấy khía cạnh nhưng chọn sai sắc thái, hoặc bỏ sót khía cạnh.

## 3. Hai cơ sở đo và "ô không đọc được"

Mỗi lượt chạy được đo **hai lần** trên cùng một đầu ra model. Mỗi ô là một cặp (review × khía cạnh):
**ground truth** = nhãn đúng, **predict** = nhãn model đoán.

| Cơ sở | Giữ ô nào | Dùng để | Nằm ở đâu |
| --- | --- | --- | --- |
| `all` (cách của dự án) | mọi ô có ground truth ≠ neutral; ô không đọc được tính là **sai** | số nội bộ, khắt khe | `scores` trong `metrics.json` |
| `paper` (cách của công bố) | chỉ ô mà **cả** ground truth **và** predict là `positive`/`negative` | **so với công bố** | `scores_paper`; cột `reference` của `metrics_matrix` |

### "Ô không đọc được tính là sai" nghĩa là gì

Với model sinh (Qwen3), predict không đến trực tiếp mà phải **đọc** từ câu trả lời văn bản. **"Không
đọc được"** = câu trả lời **không phân tích thành một nhãn hợp lệ**: JSON hỏng, **thiếu khoá khía
cạnh**, hoặc **mã nhãn lạ** (không nằm trong bảng cho phép). Khi đó ô **không có predict**
(`predict = None`).

Ở cơ sở **`all`** (cách của dự án): ô đó bị tính là **SAI** và **vẫn nằm trong mẫu số**
(`predict != ground truth` là sai; `None` coi như không khớp). **Vì sao không bỏ đi:** nếu bỏ, thì
model trả lời hỏng ở đúng các ô khó lại **được điểm cao hơn** (mẫu số nhỏ đi) → "lỗi định dạng" biến
thành một cách **nâng điểm im lặng**. Nên phải phạt.

Ở cơ sở **`paper`** (cách của công bố): ô không đọc được **bị loại khỏi mẫu số** (vì predict không
phải `positive`/`negative`). Đây là một trong các khác biệt giữa hai cơ sở - nên so với công bố thì
đọc ở `paper`, còn số nội bộ khắt khe là `all`.

### Phép lọc hai chiều của công bố

> *Retain only the samples where **both** the ground-truth **and predicted** labels fall into the two
> sentiment classes: positive and negative.*

Ví dụ một review:

| khía cạnh | ground truth | predict | giữ? |
| --- | --- | --- | --- |
| colour | positive | positive | giữ (đúng) |
| shipping | negative | positive | giữ (sai) |
| price | neutral | positive | **loại** (ground truth không nằm trong {positive, negative}) |
| texture | positive | *(không nhắc)* | **loại** (predict không nằm trong {positive, negative}) |
| smell | *(không nhắc)* | positive | **loại** (ground truth không nằm trong {positive, negative}) |

### Vì sao mẫu số của `paper` phụ thuộc model

Accuracy của công bố = `số ô đúng / số ô được giữ`. Số ô được giữ **không cố định**: nó bớt đi ở những
ô mà model trả lời `neutral` hoặc "không nhắc". Nghĩa là model **càng "kiêng" trả lời** thì mẫu số càng
nhỏ, nên phần trăm càng dễ cao - **dù số ô đúng không đổi**.

Xét một ô có **ground truth** `positive`:

| predict | cơ sở `all` | cơ sở `paper` |
| --- | --- | --- |
| `positive` | giữ · đúng | giữ · đúng |
| `negative` | giữ · **sai** | giữ · **sai** |
| `neutral` | giữ · **sai** | **loại** (không vào mẫu số) |
| *(không nhắc)* | giữ · **sai** | **loại** (không vào mẫu số) |

Cùng là "không chọn đúng": kiểu `negative` **bị trừ điểm** ở cả hai cơ sở; kiểu `neutral`/không-nhắc
thì cơ sở `all` **trừ điểm** còn cơ sở `paper` **bỏ qua**. Vì vậy khi đọc số cơ sở `paper` phải đọc
kèm **mẫu số** và **lý do bị gỡ**: `paper.cells` (số ô được giữ), `dropped_not_two_sided` (gỡ vì
predict là neutral / không nhắc), `dropped_unreadable` (gỡ vì trả lời hỏng định dạng).

## 4. Ý nghĩa từng chỉ số

| Tên (config `scores`) | Là gì | Trả lời câu hỏi |
| --- | --- | --- |
| `accuracy` | tỉ lệ ô đúng / tổng ô theo khía cạnh; kèm bản "chỉ trên ô có nhắc" | model chọn sắc thái tốt cỡ nào |
| `aspect_detection` | nhị phân có-nhắc: accuracy, precision, recall, F1 | model nhận ra khía cạnh tốt cỡ nào (P thấp = nêu thừa, R thấp = bỏ sót) |
| `prf` | Precision/Recall/F1 cho từng cặp (khía cạnh, sắc thái), đếm một-chọi-phần-còn-lại | khía cạnh hoặc lớp nào yếu |
| `aggregate` | trung bình **macro** và **micro**; tỉ lệ khớp **hoàn toàn** (đúng cả bộ khía cạnh) | con số gộp để so giữa các thí nghiệm |
| `confusion` | ma trận nhầm theo khía cạnh | **nhìn** lỗi, không phải một con số |

Cách đọc nhanh: **macro** = mỗi khía cạnh một phiếu (khía cạnh hiếm không bị át); **micro** = cân theo
số ô. Hai số lệch nhiều = model tốt ở nhóm khía cạnh này và bỏ hẳn nhóm khác.

## 5. Khi nào một con số "so được" với công bố

1. `data.roles.eval: test` và chấm **cả split** (`n: null`).
2. `label_space: binary` và `neutral_policy: drop` (đổi là đổi bài toán).
3. Đọc ở **cơ sở `paper`** (cột `reference` của `metrics_matrix`), không lấy `scores` (`all`).
4. Mỗi lượt so với **đúng cột mức ví dụ của nó** (`COT+0-shot` / `1-shot` / `5-shot`).

Thiếu một điều kiện là con số **không** so được - và hệ thống đánh dấu (cột `basis`, `eval_lock`,
`paper.cells`) thay vì im lặng.
