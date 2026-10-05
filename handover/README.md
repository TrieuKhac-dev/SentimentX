# Hướng dẫn chạy thí nghiệm (SentimentX)

Đây là bản README đi kèm MỌI gói bàn giao (nguồn của nó ở `handover/README.md` trong repo).
Gói chứa mọi thứ cần để chạy. Bạn **không cần cài gì, không cần sửa file nào**.

## Bốn bước

1. Giải nén gói này vào Google Drive của bạn, ví dụ thành thư mục `MyDrive/SentimentX/`.
   Giữ nguyên cấu trúc bên trong (đừng di chuyển `data/` đi chỗ khác).
   Nếu bạn đã có gói trước đó: **giải nén đè lên đúng thư mục đó** - gói mới chỉ chứa file mới hoặc
   đã đổi, không chứa lại những file bạn đang có.
2. Mở **một** notebook trong `notebooks/` **từ Drive** bằng Colab (`File > Open notebook > Google
   Drive`). Bảng dưới cho biết mỗi notebook trả lời câu gì.
3. Bấm **Run all**.
4. Bấm **Allow** khi Colab hỏi quyền truy cập Drive (một lần cho mỗi phiên).

Hết. Notebook tự làm phần còn lại.

## Notebook trong gói: 23 lượt của đợt 7 + 4 lượt của đợt 8

**Chưa lượt nào trong bảng đợt 7 từng cho ra kết quả dùng được khi bảng được viết**, nên cột thời gian ghi **ước tính**; chỗ nào
ước tính dựa trên một lượt đã chạy thật thì ghi rõ số đo thật đó để bạn đối chiếu (ba lượt `qwen3-0.6b` đã
chạy ngày 02/10/2026 nhưng hỏng vì bật suy nghĩ ăn hết trần token, nên nay chạy lại với
`enable_thinking: false`). Bảng xếp theo **thứ tự nên chạy** (rẻ và lượt chặn đường trước - lượt DÒ chốt
trần token cho nhánh suy nghĩ của đợt sau).

| Notebook | Trả lời câu gì | Thời gian trên T4 |
| --- | --- | --- |
| `notebooks/phobert-large/lora/exp001.ipynb` | Encoder LỚN hơn: cùng kho tiền huấn luyện và cùng bộ tách từ với PhoBERT-base, chỉ khác số tham số | ước tính 15 đến 20 phút (lượt cùng cấu hình đã chạy thật: 14 phút) |
| `notebooks/vibert-base-cased/lora/exp001.ipynb` | Encoder tiếng Việt **khác kho** tiền huấn luyện (FPT) | ước tính 15 đến 20 phút (đã chạy thật: 12 đến 14 phút) |
| `notebooks/cafebert/lora/exp001.ipynb` | XLM-R rồi tiền huấn luyện TIẾP bằng tiếng Việt - bậc thang giữa PhoBERT và XLM-R | ước tính 15 đến 20 phút |
| `notebooks/xlm-roberta-base/lora/exp001.ipynb` | **Đối chứng NGUỒN tiền huấn luyện**: model đa ngữ (ít tiếng Việt) kém hơn bao nhiêu | ước tính 15 đến 20 phút |
| `notebooks/phobert-base-v2/lora/exp005.ipynb` | **ĐẦU PHÂN LOẠI**: cho đầu phân loại **HỌC** cùng adapter (ở bốn lượt LoRA đã chạy nó bị **ĐÓNG BĂNG** vì `peft` đóng băng mọi tham số không phải adapter) - so với `exp002` | ước tính 15 đến 20 phút |
| `notebooks/visobert/lora/exp005.ipynb` | như trên, cho ViSoBERT - so với `exp002` | ước tính 15 đến 20 phút |
| `notebooks/phobert-large/lora/exp002.ipynb` | như trên - so với `exp001` của đúng model này | ước tính 15 đến 20 phút |
| `notebooks/vibert-base-cased/lora/exp002.ipynb` | như trên - so với `exp001` của đúng model này | ước tính 15 đến 20 phút |
| `notebooks/cafebert/lora/exp002.ipynb` | như trên - so với `exp001` của đúng model này | ước tính 15 đến 20 phút |
| `notebooks/xlm-roberta-base/lora/exp002.ipynb` | như trên - so với `exp001` của đúng model này | ước tính 15 đến 20 phút |
| `notebooks/qwen3-0.6b/prompt-cot/exp004.ipynb` | **LƯỢT DÒ**: bật suy nghĩ thì phần ` thinking` dài bao nhiêu token (chỉ 60 mẫu, trần 8.192) | ước tính 20 đến 40 phút |
| `notebooks/qwen3-0.6b/prompt-cot/exp001.ipynb` | Qwen3 0.6B CoT 0 ví dụ (**đã tắt suy nghĩ**) | ước tính 20 đến 40 phút |
| `notebooks/qwen3-0.6b/prompt-cot/exp002.ipynb` | Qwen3 0.6B CoT 1 ví dụ | ước tính 20 đến 40 phút |
| `notebooks/qwen3-0.6b/prompt-cot/exp003.ipynb` | Qwen3 0.6B CoT 5 ví dụ | ước tính 20 đến 40 phút |
| `notebooks/qwen2.5-0.5b-instruct/prompt-cot/exp001.ipynb` | Cùng cỡ nhỏ nhưng **khác họ model**: 0 ví dụ | ước tính 15 đến 25 phút |
| `notebooks/qwen2.5-0.5b-instruct/prompt-cot/exp002.ipynb` | như trên - 1 ví dụ | ước tính 15 đến 25 phút |
| `notebooks/qwen2.5-0.5b-instruct/prompt-cot/exp003.ipynb` | như trên - 5 ví dụ | ước tính 15 đến 25 phút |
| `notebooks/phobert-base-v2/lora/exp003.ipynb` | Lượt **`val`** (không phải `test`) để **chốt ngưỡng** theo khía cạnh; ghi **thêm** tệp xác suất | ước tính ~15 phút (lượt `test` cùng cấu hình: 14 phút) |
| `notebooks/visobert/lora/exp003.ipynb` | như trên, cho ViSoBERT | ước tính ~15 phút (đã chạy thật: 12 phút) |
| `notebooks/qwen3-4b-instruct-2507/prompt-cot/exp014.ipynb` | **GIÁ**: định nghĩa lời chê giá gián tiếp ngay trong prompt | ước tính ~2 giờ (lượt 1 ví dụ cùng model đã chạy thật: 2 giờ 04 phút) |
| `notebooks/qwen3-4b-instruct-2507/prompt-cot/exp015.ipynb` | **GIÁ**: ví dụ dạy có MỘT ô giá mã 2 (chê giá gián tiếp) | ước tính ~2 giờ |
| `notebooks/qwen3-4b-instruct-2507/prompt-cot/exp016.ipynb` | **CHẨN ĐOÁN**: chỉ hỏi ĐÚNG khía cạnh giá (tập ô khác nên **không** so với công bố) | ước tính 30 đến 40 phút |
| `notebooks/qwen3-4b-instruct-2507/prompt-cot/exp017.ipynb` | Lượt **`val`** phía LLM: điều kiện để chốt luật **lai** encoder + LLM | ước tính 1,5 đến 2 giờ (lượt `test` cùng cấu hình: 2 giờ 47 phút) |

Mỗi notebook ghi vào thư mục kết quả riêng nên chạy song song nhiều phiên cũng không giẫm lên nhau: mọi
notebook đều chạy được cùng lúc vì mỗi lượt có thư mục riêng theo mã băm danh tính.

**Trạng thái 6 notebook gửi kèm sẵn ở các gói TRƯỚC (cập nhật 05/10/2026 - đọc trước khi chạy):**

| Notebook | Trạng thái nay |
| --- | --- |
| `notebooks/phobert-base-v2/lora/exp004.ipynb`, `notebooks/visobert/lora/exp004.ipynb` | **ĐÃ CHẠY XONG 05/10/2026** (hai lượt `test` để đo tác dụng của NGƯỠNG; thời lượng thật 771,8 và 703,8 giây). **ĐỪNG chạy lại**: nguyên nhân gốc sai và cũng làm ra thư mục kết quả thứ hai trùng số |
| `notebooks/qwen3-4b-instruct-2507/prompt-cot/exp018.ipynb`, `exp019.ipynb`, `exp020.ipynb`, `exp021.ipynb` | **CHƯA chạy, chưa cần chạy**: bốn lượt **lấy mẫu** (đo dao động + đầu vào biểu quyết). Ngưỡng, ensemble và luật lai đã chốt xong trên `val` nên chúng chỉ cần cho bước BIỂU QUYẾT và thước nhiễu - chạy sau |

### Đợt 8 - 4 notebook MỚI trong gói này (016): thứ tự chạy

Gói **016** mang thêm **bốn** notebook (chúng chưa từng nằm trong gói nào trước đây). Thứ tự dưới đây xếp
theo **rẻ và mở đường trước**:

| # | Notebook | Việc | Thời gian trên T4 | Trả lời câu gì |
| --- | --- | --- | --- | --- |
| 1 | `notebooks/qwen3-0.6b/prompt-one-turn/exp001.ipynb` | chạy mới | ước tính **20 đến 40 phút** (câu trả lời ngắn, không viết phần suy luận) | Ba lượt `qwen3-0.6b` tắt suy nghĩ đọc không nổi vì **ĐỊNH DẠNG** hay vì **SUY LUẬN**? Đây là lượt rẻ nhất trả lời câu đó |
| 2 | `notebooks/qwen3-0.6b/prompt-cot/exp005.ipynb` | chạy mới | **2 đến 8 giờ** (2-3 phiên Colab; bị ngắt thì Run all lại) | Nhánh **BẬT suy nghĩ** ở mức 1 ví dụ: bật suy nghĩ có sửa được lỗi định dạng không (trần token **1.985** đã đo từ lượt DÒ `exp004`) |
| 3 | `notebooks/qwen3-0.6b/prompt-cot/exp006.ipynb`, `exp007.ipynb` | **CHỈ chạy nếu lượt số 2 xong trong khoảng ≤ 3 giờ** | 2 đến 8 giờ mỗi lượt | Như trên ở 0 và 5 ví dụ. Không chạy cũng không sao: ghi rõ "chưa chạy" thay vì để trống |

Điều kiện ở lượt số 3 là chủ ý: cùng một cơ chế nhưng **gấp khoảng 5 lần** chi phí của nhánh tắt suy nghĩ,
nên chỉ mở rộng khi phiên chạy thật chứng minh là kịp. Hai lượt `exp006`/`exp007` khác `exp005` **đúng số
ví dụ**, dùng **cùng** trần 1.985 (trần này đo ở mức 1 ví dụ; hai mức 0 và 5 dùng chung và **chưa có lượt DÒ
riêng** - đọc `run.log` để thấy tỉ lệ chạm trần trước khi tin điểm).

Năm nhóm MỚI của đợt này (mỗi lượt chỉ khác **một** thứ so với lượt gốc, nên đọc kết quả là đọc được
nguyên nhân):

- **Bốn encoder mới** (`phobert-large`, `vibert-base-cased`, `cafebert`, `xlm-roberta-base`) trả lời: điểm
  của PhoBERT đến từ **kiến trúc**, từ **kho văn bản tiền huấn luyện tiếng Việt**, hay từ **bộ tách từ**?
  `xlm-roberta-base` là **đối chứng đa ngữ** (phần tiếng Việt rất nhỏ). Đọc bằng **F1 lớp âm** và
  macro-F1, KHÔNG bằng độ chính xác: đoán mã 1 cho mọi ô vẫn ra độ chính xác cao mà lớp âm thì bằng 0.
- **Hai lượt `val`** (`phobert-base-v2/lora/exp003`, `visobert/lora/exp003`) chấm trên tập **`val`** chứ
  KHÔNG phải `test`: số này dùng để **chốt ngưỡng** theo từng khía cạnh, nên đừng đem so với công bố.
- **Ba lượt về khía cạnh `price`**: `exp014` (sửa câu chữ prompt), `exp015` (ví dụ dạy có ô giá mã 2),
  `exp016` (chỉ hỏi ĐÚNG một khía cạnh). Khía cạnh `price` chỉ có **6 ô âm** ở `test` và **0 ô** ở `val`,
  nên nó được đọc bằng **số lần model gán mã 2** cộng danh sách 6 ô đó, KHÔNG bằng F1.
- **`exp017`** là lượt **`val`** phía LLM: điều kiện để chốt **bảng luật lai** encoder + LLM.
- **Sáu lượt "đầu phân loại"** (`phobert-base-v2/lora/exp005`, `visobert/lora/exp005`,
  `cafebert/lora/exp002`, `phobert-large/lora/exp002`, `vibert-base-cased/lora/exp002`,
  `xlm-roberta-base/lora/exp002`) trả lời: **đóng băng hay không đóng băng đầu phân loại thì khác gì
  nhau?** Ở bốn lượt LoRA đã chạy, `peft` đóng băng MỌI tham số không phải adapter nên đầu phân loại chỉ
  là một phép chiếu ngẫu nhiên cố định (`head.pt` của chúng giống nhau **từng byte** giữa các checkpoint của
  cùng một lượt chạy - đây là số đo, không phải suy đoán; lượt bật `head.trainable: true` thì `head.pt`
  khác hẳn và khác cả giữa `best` và `last`). Mỗi lượt dưới đây khác lượt gốc **đúng một khoá**
  (`head.trainable: true`). Khi đọc:
  kiểm `trainable_params` trong `metrics.json` **lớn hơn** lượt gốc đúng **16.149** ở năm model 768 ẩn (PhoBERT-base, ViSoBERT, ViBERT, XLM-R) và **21.525** ở hai model 1.024 ẩn (**CafeBERT**, PhoBERT-large)
  trước đã, rồi mới so F1 lớp âm + macro-F1.

### Đã nhận đủ kết quả đợt 7 (05/10/2026) + hai lượt đợt 8

- **`cafebert/lora/exp002` (đầu phân loại) ĐÃ CHẠY LẠI XONG 05/10/2026** (`results/93448395`): thư mục kết
  quả trước bị **sao chép thiếu** (`run_meta.json` còn `RUNNING`, không có `metrics.json`); nay đủ và cho
  **97,88 · 0,917 · 0,847** trên 2.737 ô (`trainable_params` = 7.132.181) ⇒ nhóm đầu phân loại đủ **6/6**.
- **Ba lượt `qwen3-0.6b/prompt-cot/exp001`/`exp002`/`exp003` chạy XONG nhưng DƯỚI CỬA ĐỌC ĐƯỢC** (42,02 /
  21,63 / 84,41% so với cửa 95%) - và **KHÔNG phải vì trần token**: trung bình/trần chỉ 0,36-0,56 và dưới
  5% mẫu chạm trần, tức theo luật 3 của `metrics.md` chúng KHÔNG bị cắt. Thứ thiếu là **định dạng đầu ra**:
  model trả lời bằng lời rồi không in khối JSON cuối. Vì vậy **điểm ba lượt này không dùng để so**; nhánh
  BẬT suy nghĩ (`exp005`) là lượt đọc được để thay thế.
- **Lượt DÒ `qwen3-0.6b/prompt-cot/exp004` đã xong**: p50 **642** / p95 **1.072** / p99 **1.323** / max
  **1.434** token sinh, đọc được **98,33%** ⇒ trần chốt theo luật 23a là **`max_new_tokens: 1985`** cho ba
  lượt bật suy nghĩ của đợt 8 (`exp005` luôn chạy; `exp006`/`exp007` chỉ chạy khi mỗi lượt ≤ khoảng 3 giờ).
- **Lượt `qwen3-0.6b/prompt-one-turn/exp001` ĐÃ XONG 05/10/2026: đọc được 99,94%** (VƯỢT cửa 95%) - xác nhận
  dứt điểm: ba lượt 0,6B `exp001..003` hỏng vì **ĐỊNH DẠNG ĐẦU RA**, KHÔNG vì trần token. Nhưng điểm vẫn thấp
  (acc TB 87,04 · F1 macro 0,610 · F1 âm macro 0,211 · chỉ 877 ô `paper`) ⇒ vẫn là model quá nhỏ để so điểm.
- **Sáu lượt đầu phân loại: đủ 6/6 kết quả.** Đọc nhanh: cho đầu phân loại HỌC thì **5/6** cặp nhỉnh hơn
  **+0,21 → +1,16 điểm** độ chính xác, cặp `vibert-base-cased` kém **0,15**
  (chưa tách được khỏi nhiễu), còn **F1 lớp âm gần như đứng yên** - chi tiết và cách đọc ở
  `docs/04_experiments/08_experiment_rationale.md` §2b. **Lượt THƯỚC NHIỄU cho encoder** đã lên kế hoạch ở
  đợt 10 (chạy lại 3 nhánh với hạt giống khác; xem `present_plan.md` mục 14).
- **Bốn bước kết hợp đã chốt xong trên `val`**: ngưỡng theo khía cạnh, trọng số ensemble, luật lai và biểu
  quyết nằm trong `data/reports/fusion/` (repo), không cần GPU và không cần notebook.


### Năm thư mục kết quả HỎNG từ 04/10/2026 - GIỮ NGUYÊN, đừng đọc, đừng chạy lại vì chúng

Trong thư mục kết quả của bạn còn năm thư mục có `run_meta.json` ghi `"status": "FAILED"` và **không có**
`metrics.json`. Chúng là **bằng chứng của một lỗi thật đã sửa**: ở DÒNG CUỐI của mọi lượt encoder, hàm ghi
tệp xác suất bị gọi sai thứ tự tham số (`utils.write_csv`) nên lượt chạy `TypeError` **sau khi đã huấn luyện
và suy luận xong** và mất trắng kết quả (lượt `xlm-roberta-base` hỏng tới hai lần). Nay hàm đó đã tách
riêng (`write_probabilities()`) và đã có phép kiểm gọi thẳng được.

| Thư mục | Lượt |
| --- | --- |
| `results/61dbdddb` | `cafebert/lora/exp001` |
| `results/843cd8e9` | `phobert-base-v2/lora/exp003` |
| `results/a525cefe` | `vibert-base-cased/lora/exp001` |
| `results/8346cb0d` | `visobert/lora/exp003` |
| `results/a2f22f02` | `xlm-roberta-base/lora/exp001` |

**Giữ nguyên năm thư mục này** trong repo (chúng ghi lại lỗi, không phải nhiễu cần dọn). Bản **dùng được**
của cả năm lượt nằm ở thư mục khác (`61871aed`, `c0033f3c`, `ba615bcb`, `8b4aeafa`, `491e81cb`) - đó mới là
thư mục phải đọc số.

### Nhóm encoder gửi thêm tệp xác suất

Mười hai lượt encoder (bốn encoder mới + hai lượt `val` + **sáu lượt "đầu phân loại"**) ghi **thêm**
`probabilities.csv` cạnh các tệp kết quả
thường: mỗi dòng là một ô (review × khía cạnh) kèm xác suất từng mã. Hai bước **ngưỡng** và **ensemble**
không chạy notebook nào - chúng đọc tệp này, nên khi gửi kết quả về **nhớ gửi kèm tệp xác suất**; thiếu nó
thì hai bước đó không chạy được.

### Nhánh suy nghĩ (đợt sau): đắt gấp khoảng 5 lần

Notebook `qwen3-0.6b/prompt-cot/exp004` (lượt **DÒ** trong gói này) tồn tại để **chốt trần token** cho nhánh
bật suy nghĩ ở đợt sau: model bật suy nghĩ viết phần ` thinking` rất dài, và nếu trần token thấp thì nó viết
hết trần rồi không còn chỗ in JSON - đã gặp thật (ba lượt 0,6B ngày 02/10/2026 chỉ đọc được 3,33 / 1,36 /
1,73%). Vì vậy nhánh suy nghĩ **chậm hơn hẳn** (ước tính xấp xỉ **5 lần** nhánh tắt suy nghĩ), và **mọi
lượt bật suy nghĩ đều phải chạy lượt DÒ trước** để chọn `max_new_tokens = làm tròn lên (p99 × 1,5)`.


Cần chạy GPU: `Runtime > Change runtime type > T4 GPU`. Notebook LoRA (tám lượt trong gói này) cần thêm
thư viện `peft`
(notebook tự cài). Notebook PhoBERT cần thêm **Java + `py-vncorenlp`** cho bộ tách từ chính chủ: máy
ảo chưa có thì notebook tự cài (bạn sẽ thấy `apt-get -> 0`, `JAVA_HOME -> ...`, `pip install -> 0`).
Model VnCoreNLP (~27 MB) đã có trong `data/models/vncorenlp/` của gói, và nếu thiếu thì notebook tự
tải về - bạn **không phải chép tay** thư mục nào.

## Trong gói có file `MANIFEST.csv`

Cột `class` cho biết gói này mang file đó vì lý do gì:

| `class` | Nghĩa |
| --- | --- |
| `new` | file mới, giải nén ra là có |
| `changed` | file đã có nhưng nội dung đổi, giải nén đè lên là xong |
| `kept` | **không** có trong gói: bản bạn đang giữ vẫn đúng, không phải làm gì |
| `deleted` | **hãy XOÁ** khỏi thư mục Drive của bạn - bản cũ không còn dùng nữa |

**Áp gói theo THỨ TỰ.** Cột `depends_on` cho biết gói này phải giải nén **sau** gói nào (gói `001` để
trống vì nó là gói gốc). Gói sau giả định bạn đã có gói trước - bỏ qua một gói thì thiếu file, mà
không có gì báo cho bạn biết ngay lúc giải nén.

Nếu thiếu file thì **ô kiểm trước trong notebook sẽ báo**: nó liệt kê đường dẫn còn thiếu trong danh
sách việc phải sửa, trước khi nạp model. Đó là lúc nên giải nén lại gói còn thiếu, chứ không phải chạy
tiếp.

## Notebook tự làm gì (bạn sẽ thấy in ra)

| Việc | Dòng in ra |
| --- | --- |
| Mount Drive (Colab hỏi quyền, bấm Allow) | `Chưa mount Drive - đang mount...` |
| Tìm thư mục này bằng file đánh dấu hoặc bằng cấu trúc gói | `Drive : ... (nhận ra bằng file đánh dấu)` |
| Trỏ dữ liệu và kết quả vào thư mục này | `Gốc dữ liệu : .../data`, `Gốc kết quả : .../experiments` |
| Kéo đúng bản code đã ghim từ GitHub | `Code : dùng bản code đang có | /content/SentimentX | <commit>` |
| Cài gói máy ảo còn thiếu | `Thiếu gói bitsandbytes - đang cài...` |
| Kiểm trước khi chạy | `Không có việc nào phải sửa.` |
| Ngắt phiên khi chạy xong (hoặc khi lượt chạy lỗi) | `Đang ngắt phiên Colab ...` |

Notebook **tự ngắt phiên** khi chạy xong hoặc khi lượt chạy dừng vì lỗi: Colab giới hạn số giờ GPU
mỗi ngày, mà phiên bỏ không vẫn tính giờ. Muốn giữ phiên (ví dụ để chạy tiếp một ô) thì đặt
`SENTIMENTX_END_SESSION=0` trong `env/.env.colab`. Bấm dừng giữa chừng (Ctrl-C) thì notebook **không**
ngắt phiên: lúc đó bạn đang cần phiên còn sống.

## Kết quả nằm ở đâu

```
<Drive>/experiments/<model_id>/<method>/<expNNN>/results/<hash8>/
    run.log             từng bước đã chạy (mở file này trước)
    metrics.json        điểm số chính
    metrics.csv         bảng dài để so với thí nghiệm khác
    run_meta.json       bản ghi lần chạy: code, config, dữ liệu, thiết bị
    mispredictions.csv  các ô đoán sai (cách đo của dự án)
    mispredictions_paper.csv  các ô đoán sai theo cách CÔNG BỐ đo (tập con của tệp trên)
    predictions.csv     từng review: prompt đã gửi model (đường prompt), nhãn đúng/đoán
    predictions/        kết quả ghi theo khối, để chạy tiếp nếu bị ngắt
    model/last          adapter đủ để chạy tiếp (chỉ có ở các notebook LoRA - tám lượt)
    model/best          adapter để suy luận (chỉ có ở các notebook LoRA - tám lượt)
```

Máy đứt giữa chừng thì cứ bấm Run all lần nữa: notebook tự chạy tiếp, không làm lại phần đã xong.
Phiên Colab hết thời gian giữa lượt chạy dài là chuyện bình thường, và đó chính là lúc cơ chế chạy
tiếp có tác dụng.

## Cần gửi lại gì

**Bảy** file **nhẹ**: `run.log`, `metrics.json`, `metrics.csv`, `run_meta.json`, `mispredictions.csv`,
`mispredictions_paper.csv`, `predictions.csv`.
Nhóm **encoder** (12 lượt: bốn encoder mới + hai lượt `val` + sáu lượt "đầu phân loại") gửi **thêm
`probabilities.csv`**.
`predictions.csv` là tệp thứ BẢY (thêm từ 04/10/2026): bước KẾT HỢP dựng đầu vào rút gọn từ nó, và lượt
**DÒ** phải có nó mới đo được số token sinh (`p50`/`p95`/`max`) - thiếu nó thì hai việc đó không chạy được.
Gửi thẳng thư mục kết quả cũng được (các file nặng nằm trong `predictions/` và `model/`).

## Nếu có gì không chạy

Đọc dòng đầu tiên trong danh sách `CÒN N VIỆC PHẢI SỬA` mà notebook in ra, đó là nguyên nhân gốc.
Bảng tra lỗi đầy đủ nằm ở `docs/00_workflow/07_colab.md` mục 7 (trong repo GitHub của nhóm).

## Ghi chú

- `env/.env.colab` đã có sẵn token DagsHub của nhóm, nên kết quả tự hiện trên DagsHub. File này
  **không** được commit lên git; muốn dùng token riêng thì thay giá trị trong đó, hoặc thêm
  `DAGSHUB_TOKEN` vào Colab Secrets (Secrets được đọc trước, nên sẽ thắng tệp này).
- Hai khoá `SENTIMENTX_DATA_ROOT` và `SENTIMENTX_RESULTS_ROOT` trong tệp env để nguyên **dạng chú
  thích**: notebook tự đặt chúng theo thư mục Drive mà nó tìm được. Nếu tệp env khai chúng thì giá
  trị trong tệp sẽ **thắng**, nên chỉ bỏ chú thích khi bạn muốn chỉ đích danh thư mục của mình.
- `env/.env.colab.example` là bản mẫu để tham chiếu, không phải file đang dùng.
- Đừng nén lại thư mục `data/` hay đổi tên file trong đó: mã phiên bản dữ liệu được tính từ nội dung
  các file gốc, đổi tên hay thêm file là ra một mã khác và kết quả không còn so được với công bố.
- Notebook cần internet: nó kéo bản code đã ghim từ GitHub và tải trọng số model về máy ảo.
- Notebook trong gói là **bản đã ghim của đúng thí nghiệm đó**, không phải bản mẫu đang sửa trong
  repo. Đừng sửa notebook trong gói: kết quả phải tra được từ đúng bản code đã ghim.
