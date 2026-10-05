# P8 - Đợt 7 → đợt 9 (từ 04/10/2026): chạy nốt, chốt luật, kết hợp

> Đọc file này khi: chuẩn bị chạy hoặc gửi notebook của **đợt 7 / 8 / 9**, hoặc cần tra vì sao có ba lượt
> `qwen3-0.6b` chạy lại, ba lượt về khía cạnh `price`, hai lượt `val` cho encoder, bốn lượt lấy mẫu, và
> bốn bước **KẾT HỢP** (ngưỡng / ensemble / lai / biểu quyết).
> Liên quan: [README.md](README.md), [P7_rerun.md](P7_rerun.md),
> [P8_measurement_mlflow.md](P8_measurement_mlflow.md), [../../present_plan.md](../../present_plan.md),
> [../../check_present_plan.md](../../check_present_plan.md),
> [../04_experiments/08_experiment_rationale.md](../04_experiments/08_experiment_rationale.md) (bản NGƯỜI ĐỌC),
> [../04_experiments/09_fusion.md](../04_experiments/09_fusion.md) (đặc tả bốn bước kết hợp).

## 1. Mục tiêu giai đoạn

1. **Chạy nốt** phần còn thiếu của vòng so công bố: **23 notebook đợt 7** = 17 notebook đã ghim (gói
   **012 + 013 + 014**) + **6 lượt ablation đầu phân loại** (gói **015**), rồi 8-10 notebook đợt 8 (gói
   **016**), và 3 notebook đợt 9 khi cần mốc quy mô lớn.
2. **Chốt luật trên `val` rồi mới áp lên `test`** (ngưỡng theo khía cạnh, trọng số ensemble, bảng luật
   lai) - không chọn bằng `test`.
3. Báo cáo **bốn bước kết hợp** là phần MỚI của báo cáo: ngưỡng, ensemble encoder, lai encoder + LLM,
   biểu quyết 3 mẫu.
4. Nói rõ cái gì **không vượt nhiễu**, thay vì chỉ khoe cái tăng: độ chênh giữa ba mẫu lấy mẫu chính là
   thước đo nhiễu phải vượt.

## 2. Trạng thái

- Nhánh: `experiment` (= `origin/experiment`). Mỗi mục xong = một commit.
- **04/10/2026**: đã dọn 6 thư mục kết quả hỏng, còn **17 lượt dùng được**; đã viết lại toàn bộ tài liệu
  theo 17 lượt đó; đã thêm 5 model (4 encoder + `qwen2.5-0.5b-instruct`) và mã cho bốn bước kết hợp.
- Đợt 7: 17 notebook đã có cấu hình + README, đã **ghim `4571648`** và nằm trong **gói 012** (kèm **gói
  013** và **gói 014** chỉ chở `README.md` sửa - xem mục 9; gói sau đè lên gói trước).
- Đợt 8 và đợt 9: xem mục 4 và 5 (đợt 9 chỉ chạy khi muốn mốc quy mô lớn).
- **05/10/2026**: sửa **hai lỗi thật**, thêm **một cơ chế**, tạo **6 lượt ablation** (gói **015**):
  1. **Lỗi A** - `utils.write_csv` bị gọi sai thứ tự tham số ở DÒNG CUỐI của mọi lượt encoder (chữ ký là
     `(rows, columns, path)`), nên lượt chạy `TypeError` **sau khi đã huấn luyện + suy luận xong** và mất
     trắng kết quả. Đã giết **5 lượt** (4 encoder mới + lượt chạy tiếp của `xlm-roberta-base`). Nay tách
     hàm `write_probabilities()` (thuần, test gọi thẳng được).
  2. **Lỗi B** - `PeftModel.from_pretrained` mặc định `is_trainable=False` nên đóng băng **mọi** tham số,
     kể cả adapter vừa nạp ⇒ lượt CHẠY TIẾP chết ở `optimizer got an empty parameter list`.
  3. **Cơ chế `head.trainable`** (mặc định `false`): `peft` đóng băng mọi tham số không phải adapter nên ở
     cả bốn lượt LoRA đã chạy **đầu phân loại KHÔNG học** (`head.pt` giống nhau TỪNG BYTE). Sáu lượt mới
     khác lượt gốc **đúng một khoá đo được** để trả lời "đóng băng hay không khác gì nhau".
  4. **Sửa `requires_extra`** cho `phobert-large/lora/exp001` và `vibert-base-cased/lora/exp001` (thiếu mục
     VnCoreNLP dù cả hai `segmenter: vncorenlp`, nên notebook không kiểm trước khi chạy).
- **Số gói dịch MỘT bậc từ đây:** đợt 7 nay đóng **012 + 013 + 014 + 015** (015 chở 6 lượt ablation cùng bản
  mã đã sửa và bản ghim mới); đợt 8 = **gói 016**, gói cuối = **017**.
- **Mốc dừng:** **#2** sau khi gửi **gói 012 + 013 + 014** (đợt 7); **#3** sau **gói 015** (6 lượt ablation);
  **#4** sau **gói 016** (đợt 8); **#5** sau khi xử lý đợt 8 xong (**gói 017** nếu có sửa mã).
- **05/10/2026 (xử lý kết quả đợt 7):** 22/23 notebook đợt 7 đã về. Bốn việc đã xong: (1) **chốt trần
  token 1985** cho nhánh bật suy nghĩ của 0,6B (đo từ lượt DÒ, luật 23a); (2) xác nhận hai lỗi đã sửa
  **KHÔNG đổi số** - `phobert-base-v2/lora/exp004` trùng khít `lora/exp002` từng dòng `metrics.csv`;
  (3) chốt xong **ba bước kết hợp trên `val`** (ngưỡng, trọng số ensemble, luật lai) rồi áp lên `test`;
  (4) đọc ra nguyên nhân ba lượt 0,6B tắt suy nghĩ bị gắn `read_rate.valid = false`: **lỗi ĐỊNH DẠNG đầu
  ra**, không phải trần token. Một lượt **phải chạy lại**: `cafebert/lora/exp002` (thư mục kết quả sao chép
  thiếu). Bốn notebook **đợt 8** đã tạo: `qwen3-0.6b/prompt-cot/exp005`/`exp006`/`exp007` (bật suy nghĩ,
  trần 1985) + `qwen3-0.6b/prompt-one-turn/exp001` (bỏ suy luận, chỉ trả JSON).


## 3. Đợt 7 - gói 012 (rồi 013, 014) + gói 015, 23 notebook, khoảng 11-14 giờ GPU

| Nhóm | Thí nghiệm | `parent` | Vì sao có mặt | Chi phí |
| --- | --- | --- | --- | --- |
| A. 0.6B chạy lại | `qwen3-0.6b/prompt-cot/exp001`, `exp002`, `exp003` | `null` (ba lượt độc lập) | Lượt cũ **hỏng hai kiểu**: nạp nhầm trọng số 4B, và bật suy nghĩ ăn hết trần token (chỉ đọc được 3,33 / 1,36 / 1,73%). Nay `configs/models/qwen3-0.6b.yaml` khai `enable_thinking: false` | 20-30 phút mỗi lượt |
| DÒ | `qwen3-0.6b/prompt-cot/exp004` | `exp002` | **Đo** phần suy nghĩ dài bao nhiêu token ở `n: 60` để chốt trần cho đợt 8 | 20-40 phút |
| B. Qwen2.5-0.5B | `qwen2.5-0.5b-instruct/prompt-cot/exp001`, `exp002`, `exp003` | `null` | Mốc "model nhỏ" thứ hai, **khác họ model**: kết luận "nhỏ thì kém" có lặp lại không | 15-25 phút mỗi lượt |
| C. 4 encoder mới | `phobert-large/lora/exp001`, `vibert-base-cased/lora/exp001`, `cafebert/lora/exp001`, `xlm-roberta-base/lora/exp001` | `null` | Tách **nguồn** điểm số: kho tiền huấn luyện tiếng Việt, kiến trúc, bộ tách từ (`xlm-roberta-base` là đối chứng đa ngữ) | 15-20 phút mỗi lượt |
| D. hai lượt `val` | `phobert-base-v2/lora/exp003`, `visobert/lora/exp003` | `lora/exp002` | Điều kiện để **chốt ngưỡng và trọng số ensemble trên `val`**; bản mã ghi thêm `probabilities.csv` | ~15 phút mỗi lượt |
| E. ba lượt về `price` | `qwen3-4b-instruct-2507/prompt-cot/exp014` (câu chữ prompt), `exp015` (ví dụ có ô giá mã 2), `exp016` (chẩn đoán: chỉ hỏi một khía cạnh) | `exp003` | `price` âm có **6 ô** ở `test`, 15 ở `train`, **0 ở `val`**; cả 17 lượt cũ và công bố đều bỏ sót khía cạnh này | ~2 giờ / lượt (exp016: 30-40 phút) |
| F. `val` phía LLM | `qwen3-4b-instruct-2507/prompt-cot/exp017` | `exp009` | Điều kiện của **luật lai**: khía cạnh nào lấy từ LLM, khía cạnh nào lấy từ encoder | 1,5-2 giờ |
| H. đầu phân loại (gói **015**) | `phobert-base-v2/lora/exp005`, `visobert/lora/exp005` (parent `lora/exp002`) và `cafebert/lora/exp002`, `phobert-large/lora/exp002`, `vibert-base-cased/lora/exp002`, `xlm-roberta-base/lora/exp002` (parent `lora/exp001`) | xem cột trước | `peft` đóng băng MỌI tham số không phải adapter, nên ở bốn lượt LoRA đã chạy **đầu phân loại KHÔNG học** - `head.pt` giống nhau TỪNG BYTE. Sáu lượt này khác lượt gốc **đúng một khoá đo được** (`head.trainable: true`) để biết "đóng băng hay không khác gì nhau", và là phép so ĐẦU TIÊN trong dự án đo phần đầu phân loại | 15-20 phút mỗi lượt |

**Thứ tự chạy** (rẻ và lượt chặn đường trước): C → DÒ (exp004) → A → B → D → E → F → **H** (H chạy được bất
cứ lúc nào sau khi C xong, vì `parent` của bốn lượt H là nhóm C).

**Vì sao nhóm đầu phân loại là `H`, không phải `G`** (05/10/2026, thuần tài liệu): chữ **G** đã mang nghĩa
khác trong tài liệu cũ - `../04_experiments/08_experiment_rationale.md` §5 và `presentations/*` gọi **G** là
Qwen3-0.6B, còn `P8_measurement_mlflow.md` dùng **A-H** cho nhóm việc hạ tầng (H ở đó là "chốt thiết kế").
Chữ cái nhóm chỉ có phạm vi **trong từng tài liệu**, nên đổi tên ở đây để người đọc không lẫn ba nghĩa của
một chữ. `handover/README.md` (bản nằm trong gói 015) **không dùng chữ cái nhóm** - nó gọi đủ tên "sáu lượt
đầu phân loại" - nên việc đổi tên này **không phải ghim lại** và **không phải dựng gói mới**.

## 4. Đợt 8 - gói 016, 8-10 notebook, khoảng 14-25 giờ GPU

| Thí nghiệm | `parent` | Vì sao có mặt | Chi phí |
| --- | --- | --- | --- |
| `phobert-base-v2/lora/exp004`, `visobert/lora/exp004` | `lora/exp002` | Encoder trên `test` để **áp ngưỡng** đã chốt trên `val` | ~15 phút mỗi lượt |
| `qwen3-0.6b/prompt-cot/exp005` | `exp002` | Nhánh **bật suy nghĩ** chạy đầy đủ ở mức 1 ví dụ (trần chốt từ lượt DÒ) | 2-8 giờ |
| `qwen3-0.6b/prompt-cot/exp006`, `exp007` | `exp001`, `exp003` | Như trên ở 0 và 5 ví dụ - **chỉ chạy khi mỗi lượt ≤ khoảng 3 giờ** (quyết định ở mục 6.3) | 2-8 giờ mỗi lượt |
| `qwen3-4b-instruct-2507/prompt-cot/exp018`, `exp019`, `exp020` | đỉnh sau đợt 7 (mặc định `exp009`) | **Lấy mẫu** seed 1 / 2 / 3: đo dao động và làm đầu vào biểu quyết | 2,5-3 giờ mỗi lượt |
| `qwen3-4b-instruct-2507/prompt-cot/exp021` | `exp006` | **Đối chứng fp16 khi lấy mẫu** (so `exp018`, cùng seed 1): lượng hoá × lấy mẫu có tương tác không | ~2,5 giờ |

Ba bước kết hợp **không cần notebook và không tốn GPU**: ensemble encoder, lai encoder + LLM theo khía
cạnh, biểu quyết 3 mẫu. Luật và trọng số đóng băng trong repo (`data/reports/fusion/`).

**Cập nhật 05/10/2026 - sau khi xử lý kết quả đợt 7 (đọc kỹ ở mục 2):**

1. **Trần token đã CHỐT: `max_new_tokens: 1985`** cho MỌI lượt bật suy nghĩ của 0,6B. Số này ĐO từ lượt
   DÒ `qwen3-0.6b/prompt-cot/exp004` theo luật 23a (p99 1.323 × 1,5), và ba notebook `exp005`/`exp006`/
   `exp007` đã được tạo với đúng giá trị đó. Ghi rõ một điều để không đọc sai: lượt DÒ chạy ở **mức 1 ví
   dụ**, nên 0 và 5 ví dụ dùng CHUNG trần này và **chưa có lượt DÒ riêng**.
2. **Thêm MỘT thí nghiệm ngoài bảng trên: `qwen3-0.6b/prompt-one-turn/exp001`** (bản 0,6B của đối chứng
   một lượt đã chạy ở 4B). Vì sao phải thêm: ba lượt tắt suy nghĩ của 0,6B chạy xong nhưng **dưới cửa đọc
   được** (42,02 / 21,63 / 84,41%) vì model **không in khối JSON**, KHÔNG phải vì trần token. Nhánh bật
   suy nghĩ sửa được lỗi đó nhưng **đắt gấp khoảng 5 lần**; nhánh một lượt trả lời đúng câu hỏi "vướng
   ĐỊNH DẠNG hay vướng SUY LUẬN" với chi phí rẻ nhất (câu trả lời ngắn). ⇒ **đợt 8 nay là 8-10 notebook.**
3. **Chưa cần chạy `exp018`/`exp019`/`exp020`/`exp021` ngay**: chúng phục vụ bước BIỂU QUYẾT và thước nhiễu,
   mà bốn bước kết hợp kia đã chốt xong trên `val`.

## 5. Đợt 9 - 3 notebook, khoảng 15-25 giờ, chạy khi cần mốc quy mô lớn

| Thí nghiệm | `parent` | Mục đích |
| --- | --- | --- |
| `qwen3-4b-thinking-2507/prompt-cot/exp001` | `null` | Ở **cùng cỡ 4B**, bật suy nghĩ có hơn không |
| `qwen3-8b/prompt-cot/exp001` | `null` | Mốc quy mô lớn hơn (thế hệ 4/2025 - khai báo trung thực) |
| `qwen3-14b/prompt-cot/exp001` | `null` | Mốc lớn nhất vừa T4 16 GB |

Cả ba **bắt buộc** theo luật chống chạm trần ở mục 6.1 (nhánh suy nghĩ là nhánh dễ chạm trần nhất).

## 6. Luật bắt buộc khi chạy

### 6.1 Luật chống chạm trần token

Bắt buộc cho **mọi lượt bật suy nghĩ** (và cả lượt DÒ). Lỗi đã gặp thật: model bật suy nghĩ ăn hết trần
`max_new_tokens` trong khối ` thinking` rồi không in ra JSON - ba lượt Qwen3-0.6B ngày 02/10/2026 chỉ đọc
được 3,33 / 1,36 / 1,73%.

1. chạy **lượt DÒ khoảng 60 mẫu trước** với **cùng cấu hình** sẽ dùng;
2. đo **p50 / p95 / max** số token sinh ra;
3. chọn `max_new_tokens = làm tròn lên (p99 × 1,5)`, và **không được vượt cửa sổ ngữ cảnh** của model
   (Qwen3-0.6B: 32.768 vị trí);
4. ở lượt đầy đủ, nếu **trên 5% mẫu chạm trần** thì đánh dấu lượt là **bị cắt** và chạy lại với trần cao hơn;
5. luôn báo cáo **tỉ lệ chạm trần** đặt cạnh `% đọc được`.

Trần token đọc từ cấu hình (`decoding.max_new_tokens`), **không** gõ tay ở dòng lệnh - nó đi vào dấu vân
tay của lượt chạy, nên gõ tay là lần sau không tái lập được.

### 6.2 Điều kiện của mỗi lượt

- `% đọc được ≥ 95%`. Cửa này nằm ở `read_rate_min: 95` trong `configs/experiments/evaluation.yaml`; lượt
  dưới cửa bị gắn `read_rate.valid = false` kèm lí do trong `metrics.json` và một dòng
  `KHÔNG ĐẠT CỬA CHẤT LƯỢNG` trong `run.log`. **Cửa KHÔNG xoá dữ liệu** - nó chỉ để người đọc biết con số
  đó không dùng được.
- Lượt **bị ngắt** thì bấm **Run all** lần nữa: chạy tiếp trong **cùng thư mục kết quả**.
- Gửi về: **7 tệp nhẹ** của mọi lượt (`metrics.json`, `metrics.csv`, `run_meta.json`, `run.log`,
  `mispredictions*.csv`, `predictions.csv`), **thêm `probabilities.csv`** cho **12 lượt encoder** (6 lượt
  nhóm C/D + 6 lượt ablation nhóm H; các lượt prompt KHÔNG có tệp này), và **thời gian
  thực tế**. `predictions.csv` là tệp thứ bảy từ 04/10/2026: bước kết hợp dựng đầu vào rút gọn từ nó, và
  lượt DÒ cần nó để đo p50/p95/p99.

### 6.3 Luật chia mức cho nhánh suy nghĩ

- `qwen3-0.6b/prompt-cot/exp005` (1 ví dụ) **luôn chạy** - đó là lượt so chính với nhánh tắt suy nghĩ.
- `exp006` (0 ví dụ) và `exp007` (5 ví dụ) **chỉ chạy khi mỗi lượt ≤ khoảng 3 giờ**, ước lượng từ thời gian
  thật của `exp005`. Không chạy thì ghi rõ trong tài liệu là **chưa chạy**, không để trống.
- Nhánh suy nghĩ **đắt gấp khoảng 5 lần** nhánh tắt suy nghĩ (cùng 0,6B, cùng prompt).

### 6.4 Kết thúc mỗi lượt

Ô cuối notebook in link DagsHub (nếu có) rồi **ngắt phiên Colab** - giữ quota GPU cho lượt sau.

## 7. Luật kết hợp (mọi luật chốt trên `val`, rồi mới áp lên `test`)

Đặc tả đầy đủ ở [../04_experiments/09_fusion.md](../04_experiments/09_fusion.md); dưới đây là các quyết
định đã chốt, để lượt chạy và báo cáo không lệch nhau.

1. **Ngưỡng theo khía cạnh** - áp cho **SÁU** khía cạnh (`stayingpower`, `texture`, `smell`, `colour`,
   `shipping`, `packing`). **`price` KHÔNG có ngưỡng** vì `val` có **0 ô âm** (train 15, test 6): tệp luật
   ghi `price: null` kèm lí do, và ô `price` **giữ nguyên argmax của model**. Kèm theo: (a) báo cáo phải
   ghi rõ cột `price` **không đổi** khi thêm ngưỡng - đúng thiết kế, không phải lỗi; (b) điểm macro trình
   bày **cả hai cách** (7 khía cạnh và 6 khía cạnh có ngưỡng); (c) ghi **bằng chứng quét thử** ngưỡng
   0,05 → 0,50 cho `price` (F1 không phụ thuộc ngưỡng vì không có ô âm để bắt); (d) đọc `price` bằng **số
   lần gán mã 2 + danh sách 6 ô âm của `test`**, không dùng F1.
2. **Ensemble encoder** - trung bình **xác suất** từng ô với trọng số là **macro-F1 trên `val`** của
   từng encoder; không trộn `test` để chọn trọng số.
3. **Lai encoder + LLM theo khía cạnh** - bảng luật chốt trên `val` (dùng `exp017` + hai lượt `val` của
   encoder); **hoà thì lấy LLM**. Luật ghi ra tệp JSON trong `data/reports/fusion/`.
4. **Biểu quyết 3 mẫu** - `exp018` + `exp019` + `exp020` bỏ phiếu **từng ô**; ô nào không đọc được ở một
   lượt thì lượt đó bị bỏ phiếu trắng cho ô đó; **hoà thì lấy nhãn của lượt có hạt giống nhỏ nhất** (quy
   tắc "lượt đầu tiên", để kết quả tái lập được). Ghi lại **cả ba điểm riêng lẻ** - đó là mức nhiễu.

## 8. Thứ tự ưu tiên khi thiếu GPU hoặc thời gian

1. Lượt **rẻ + chặn đường**: 4 encoder mới, hai lượt `val` của encoder, lượt DÒ.
2. Sáu lượt **ablation đầu phân loại** (nhóm H): rẻ nhất trong các lượt còn lại (15-20 phút) và là câu hỏi
   về **cơ chế học**, nên trả lời được ngay cả khi phần còn lại của đợt 7 bị cắt.
3. `exp005` (suy nghĩ đầy đủ) và `exp018`/`exp019`/`exp020` (đầu vào của biểu quyết).
4. Ba lượt **về `price`** (`exp014`, `exp015`, `exp016`).
5. `exp017` (điều kiện của luật lai) và `exp021` (đối chứng fp16 khi lấy mẫu).
6. `exp006`/`exp007` và đợt 9.

Cắt lượt nào thì ghi vào tài liệu là **chưa chạy** kèm lí do; **không** suy diễn kết quả thay cho lượt
chưa chạy.

## 9. Số phiên dự kiến và mốc dừng

- **Đợt 7 (7-9 phiên):** phiên 1 = 4 encoder + lượt DÒ + 3 lượt 0.6B tắt suy nghĩ; phiên 2 = Qwen2.5-0.5B
  + hai lượt `val` encoder; phiên 3-4 = `exp014`, `exp015`, `exp016`; phiên 5-6 = `exp017`; phiên 7 = **6
  lượt ablation đầu phân loại** (nhóm H, gói 015) - một phiên là đủ vì mỗi lượt 15-20 phút.
- **Đợt 8 (5-7 phiên):** hai lượt `test` có ngưỡng chung một phiên; `exp018`/`exp019`/`exp020`/`exp021` mỗi
  lượt một phiên; `exp005` chia 2-3 phiên, và chạy theo luật 6.1.
- **Mốc dừng:** **#2** sau khi gửi **gói 012 + 013 + 014** (đợt 7; `013` và `014` chỉ chở `README.md` sửa,
  phải giải nén **sau** gói trước đó); **#3** sau **gói 015** (6 lượt ablation đầu phân loại); **#4** sau
  **gói 016** (đợt 8); **#5** sau khi xử lý đợt 8 xong.

## 10. Quy ước thực thi (bắt buộc)

1. Một mục xong = một commit, Conventional Commits tiếng Anh
   ([../00_workflow/05_git_commits.md](../00_workflow/05_git_commits.md)).
2. Sau mỗi nhóm: `python scripts/ci_checks.py` + `python -m unittest discover -s tests`
   (Windows: đặt `$env:PYTHONUTF8=1`).
3. **CI phải XANH rồi mới ghim lại notebook hoặc dựng-gửi gói** (luật 22). Lỗi không sửa được thì quay lui
   bằng git rồi xem lại kế hoạch.
4. Không hardcode đường dẫn (dùng `configs/paths.yaml`); không đặt giá trị mặc định trong code; notebook
   đã ghim **KHÔNG** sửa - muốn có hiệu lực thì **ghim mới**.
5. Ghim xong thì thư mục `experiments/**/<expNNN>/**` **đóng băng** cho tới khi người dùng chạy xong.
6. Kết quả chỉ được dùng khi commit đã ghim **nằm trên** nhánh `experiment`.

