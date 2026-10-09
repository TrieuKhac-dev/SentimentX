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

## Notebook trong gói

> **Đợt 11 gửi trong MỘT gói: `SentimentX-goi-029-<mã>-261009.zip`** - 48 notebook, và **cả 48 ghim vào
> cùng một revision** (cùng một bản code, nên không thể lẫn hai bản giữa các lượt). Các gói **022/023/024/
> 026/027/028** là những lần gửi TRƯỚC của chính các notebook đó (gói **025** bị **026** thay thế, **027** bị
> **028** thay thế, **028** bị **029** thay thế) - nếu bạn đã tải chúng thì cứ dùng **029** là đủ, khỏi ghép
> nhiều gói. Bốn mục "Đợt 11" bên dưới nói từng nhóm trả lời câu gì; thứ tự chạy thì xem bảng ở mục
> "Đợt 11 - thứ tự chạy" (gần cuối file này).
>
> **Vì sao 028 bị 029 thay (09/10/2026):** bản 029 chỉ sửa **TÀI LIỆU trong chính file này** - không sửa một
> dòng code, một config hay một notebook nào (48 notebook y nguyên, cùng revision). Hai chỗ gây **đếm sai**
> đã sửa: (1) dòng "~13-16 phút" ghi `exp011` → `exp023` là "14 lượt" trong khi khoảng đó có **13** lượt (14
> là số của **cả dòng**, tính thêm `exp008`) - đã có người đọc bảng này và đếm ra 49 lượt; (2) lượt
> `qwen3-4b-thinking-2507/prompt-cot/exp002` chưa được đánh dấu rõ là **CHỜ NHÓM GHIM LẠI**. Nay ngay dưới
> tiêu đề bảng có **dòng cộng đủ 48**, và lượt `exp002` có nhãn riêng. Bản 028 (và 027 trở về trước) không
> có gì sai về nội dung chạy - nhưng nếu đã tải 028 thì cứ dùng **029** cho khỏi lẫn khi đếm.
>
> **Vì sao gói 027 bị 028 thay (09/10/2026):** bản 027 chạy ra lỗi ngay ở ô kiểm trước và dừng **45/48**
> notebook: *"Thí nghiệm khai `data.version` v0.2.0 nhưng file config dataset khai v0.3.0"*. Lỗi nằm ở phía
> NHÓM, không phải ở config của bạn: cả ba chỗ nạp file phiên bản dữ liệu (ô cấu hình của notebook,
> `preflight`, bước chọn chế độ chạy) đều gọi hàm nạp mà KHÔNG truyền `data.version`, nên hàm đó lấy bản
> **mới nhất** - rồi preflight so hai giá trị, thấy lệch (do chính nó gây ra) và DỪNG. Nếu chỉ bỏ phép kiểm
> thì tệ hơn: đường chạy sẽ LẶNG LẼ chấm trên bộ v0.3.0 trong khi config khai v0.2.0. Nay MỘT chỗ quyết định
> (`experiments.dataset_of`); khai một bản cũ là hợp lệ (chỉ còn một dòng ghi chú *"KHÔNG phải bản mới
> nhất"*), còn khai một bản **không tồn tại** thì vẫn DỪNG kèm danh sách bản đang có. Bản 028 giữ nguyên 48
> notebook, thứ tự chạy và mọi cấu hình; **chỉ bản code bên trong đổi**. Đã kiểm bằng chính công cụ của dự
> án: chạy `run_notebook.py <exp> --preflight-only` cho **48/48 notebook khoanh vùng xanh** ở commit ghim mới.

> **Số notebook đang có trong gói (đo 09/10/2026, sổ `handover/ledger.csv`): 115.** Con số này TĂNG theo
> từng gói - các gói đầu chỉ mang một phần, phần lớn lượt về sau ở lớp `kept` (bản bạn đang giữ vẫn
> đúng, không phải làm gì). Muốn biết một gói **NNN** mang thêm gì thì mở
> `handover/packages/NNN/manifest.csv` và đọc cột `class`. Bảng dưới liệt kê các lượt theo **thứ tự nên
> chạy**, kèm mỗi lượt trả lời câu gì.

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

### Đợt 10 - 3 notebook MỚI trong gói này (017): thước nhiễu cho đường encoder

Gói **017** mang thêm **ba** notebook (chưa từng nằm trong gói nào trước đây). Đây là **THƯỚC NHIỄU**, KHÔNG
phải lượt lấy điểm cao: mỗi lượt chạy lại một lượt đã có với **một hạt giống khác** (`decoding.seed: 7`; mặc
định cũ là 42) để đo xem chênh lệch do hạt giống là bao nhiêu điểm. Không có nó thì các chênh lệch nhỏ của
nhóm đầu phân loại (**+0,21** và **−0,15** điểm) không tách được khỏi nhiễu.

| # | Notebook | Việc | Thời gian trên T4 | Trả lời câu gì |
| --- | --- | --- | --- | --- |
| 1 | `notebooks/cafebert/lora/exp003.ipynb` | chạy mới | ước tính 15 đến 20 phút | Biên nhiễu của lượt gốc đem so công bố (`cafebert/lora/exp001`, 97,67) là bao nhiêu |
| 2 | `notebooks/cafebert/lora/exp004.ipynb` | chạy mới | ước tính 15 đến 20 phút | Chênh **+0,21** của vế "đầu phân loại HỌC" (`exp001 -> exp002`) có nằm NGOÀI biên nhiễu không |
| 3 | `notebooks/vibert-base-cased/lora/exp003.ipynb` | chạy mới (**cần VnCoreNLP**) | ước tính 15 đến 20 phút | Chênh **−0,15** của cặp `vibert-base-cased exp001 -> exp002` có nằm TRONG biên nhiễu không |

Ba lượt này **không** phải bản sao của nhau: mỗi lượt chạy lại **đúng một** lượt gốc khác nhau (xem cột "Trả
lời câu gì"). Đọc kết quả: so `cafebert/lora/exp003` với `cafebert/lora/exp001`, `cafebert/lora/exp004` với
`cafebert/lora/exp002`, `vibert-base-cased/lora/exp003` với `vibert-base-cased/lora/exp001` - chênh lệch giữa
hai lượt **cùng cấu hình khác hạt giống** CHÍNH LÀ biên nhiễu.

Ba lượt này **khác đúng MỘT khoá** so với lượt gốc của chúng (`decoding.seed`); mã nguồn đường encoder KHÔNG
đổi giữa commit của lượt gốc (`59579e5`) và commit đã ghim - bằng chứng `git diff` RỖNG nằm trong `README.md`
của từng lượt.

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

### Đợt 10 - 2 notebook TUỲ CHỌN trong gói này (020) - ĐÃ CHẠY 07/10/2026

Gói **020** mang thêm **hai** notebook (chưa từng nằm trong gói nào trước đây). **Cả hai là TUỲ CHỌN** - kết
luận của đợt đã đứng vững mà không cần chúng - và **bạn đã chạy xong cả hai ngày 07/10/2026**. Mục này giữ
nguyên để biết gói 020 chứa gì; số đo cùng kết luận đã được ghi vào `docs/04_experiments/`.

| # | Notebook | Việc | Thời gian trên T4 | Trả lời câu gì |
| --- | --- | --- | --- | --- |
| 1 | `notebooks/cafebert/lora/exp006.ipynb` | chạy mới (ĐÁNH GIÁ trên `val`, dùng lại checkpoint `exp002`) | ước tính 2 đến 5 phút | Đưa một lượt **đầu phân loại HỌC** vào bộ ứng viên `val` thì trần chọn-theo-khía-cạnh của router có dâng lên không (hiện chỉ **+0,04**) |
| 2 | `notebooks/phobert-base-v2/lora/exp007.ipynb` | chạy mới (**cần VnCoreNLP**; huấn luyện lại vì đổi kiến trúc đầu) | ước tính 15 đến 30 phút | Cơ chế "khía cạnh đi vào ĐẦU VÀO" (`head.aspect_marker: true`) có cứu được không khi đầu phân loại ĐƯỢC HỌC |

**Vì sao (1) có ích:** sáu ứng viên `val` hiện có đều thuộc **cùng một họ** (`lora` + `weighted_ce`, đầu phân
loại đóng băng) nên chúng sai giống nhau, và trần chọn-theo-khía-cạnh chỉ hơn lượt đơn tốt nhất **+0,04** trên
`test`. Thêm một model **đầu HỌC** (CafeBERT - cũng là model mạnh thứ nhì dự án) là cách duy nhất kiểm tra xem
cái trần đó là hạn chế của **bộ ứng viên** hay của chính ý tưởng router.

**Kết quả (1):** `cafebert/lora/exp006` cho acc TB **97,84** (`all`) · **98,53** (`paper`) trên `val` (lượt đầu
đóng băng cùng model `exp005`: 97,38). Nhờ đó **lượt đơn tốt nhất trên `test` nhảy 97,63 &#8594; 97,89** và
**router nhảy 97,66 &#8594; 97,86**, còn F1 âm macro của nhánh `f1_âm` nhảy 0,795 &#8594; **0,857** - nhưng
router **vẫn không vượt** lượt đơn (97,86 so 97,89) và trần chọn-theo-khía-cạnh trên `test` nay **~0,00**. ⇒
Thứ nâng điểm là **ỨNG VIÊN**, không phải việc định tuyến.

**Kết quả (2) - và đây là chỗ tôi DỰ ĐOÁN SAI một nửa:** `phobert-base-v2/lora/exp007` cho acc TB **50,51**
so cha `exp005` (đầu CŨNG học) **97,25** ⇒ **−46,74**, detection F1 macro 0,959 &#8594; **0,489**. Đúng là
"vẫn kém hơn mặc định" như đã đoán, nhưng LÍ DO thì khác: hai lượt marker (đóng băng **51,60** và học **50,51**)
cho kết quả **xấp xỉ nhau** ⇒ lỗi là của **CẤU TRÚC**, không phải của việc đầu có học hay không. Cách cài đặt
dùng **CHUNG một lớp**, nên khía cạnh chỉ vào được như một **HẰNG SỐ riêng** (`W[:, :H] · h + W[:, H:] ·
e_a + b`) - nó không đổi được CÁCH ánh xạ review &#8594; sắc thái, mà ABSA cần đúng thứ đó; năng lực đầu cũng
bị cắt **16.149 &#8594; 2.328** tham số. **Khoá `head.aspect_marker` đã bị BỎ** (giữ mặc định `false`).

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
- **`head.aspect_marker` ĐÃ CHẠY ĐỦ HAI LƯỢT (07/10/2026) - CẢ HAI ĐỀU ÂM, và lí do là CẤU TRÚC.** Bố cục 2x2
  (có/không marker × đầu ĐÓNG BĂNG/HỌC): `exp002` 93,28 vs `exp006` **51,60** (đầu đóng băng) và `exp005`
  97,25 vs `exp007` **50,51** (đầu học); detection F1 macro 0,891 &#8594; 0,495 và 0,959 &#8594; 0,489. **Cho
  đầu phân loại HỌC không cứu được** ⇒ lỗi là **CẤU TRÚC** (khía cạnh chỉ vào như một HẰNG SỐ riêng, một lớp
  dùng chung cho 7 khía cạnh; năng lực cắt 16.149 &#8594; 2.328 tham số) ⇒ **BỎ khoá** (giữ mặc định `false`).
  Chi tiết + dấu vết: `docs/04_experiments/06_lora_encoder.md`.
- **Sáu bước kết hợp: NĂM bước đầu đã chốt xong** - ngưỡng theo khía cạnh, trọng số ensemble, luật lai,
  biểu quyết và **router theo khía cạnh** nằm trong `data/reports/fusion/` (repo), không cần GPU. Router đã
  chạy **BA lần** (2 &#8594; 6 &#8594; 6 ứng viên có một lượt đầu HỌC; luật hai lần cũ giữ ở hậu tố
  `_2model`/`_6model`) và lần BA là số đang dùng: router **97,86** (`accuracy`) so lượt đơn tốt nhất **97,89**
  ⇒ **router không vượt lượt đơn**, trần chọn-theo-khía-cạnh trên `test` nay **~0,00**. Thứ nâng điểm của đợt
  là **ỨNG VIÊN** (97,63 &#8594; 97,89), không phải định tuyến (lí do tồn tại notebook (1) ở mục trên).
- **Bước thứ SÁU (gộp HAI TẦNG, `scripts/fuse_aspect.py`) ĐÃ CHẠY (07/10/2026)** trên bảy lượt một-khía-cạnh
  `prompt-aspect/exp001..007`, đo trên BA khung: `price` âm khác 0 ở CẢ BA (0,000 &#8594; **0,357 / 0,320 /
  0,261**), nhưng F1 âm macro `paper` **chỉ tăng khi khung YẾU** (0,7757 &#8594; 0,8159 và 0,7876 &#8594; 0,8124)
  - ở khung MẠNH NHẤT (`cafebert/lora/exp002`) nó **giảm** 0,8473 &#8594; 0,8064, và accuracy luôn giảm. ⇒ hướng
  PHỤ, không thay bảng chính. Chứng cứ: `fuse_aspect_test.json` + `fuse_aspect_test_cafebert_exp001.json` +
  `fuse_aspect_test_cafebert_exp002.json`. Lưu ý: lượt một-khía-cạnh **KHÔNG** cần `probabilities.csv` (luật
  gộp chỉ dùng nhãn cứng).


### Đợt 11 - 31 notebook: "điểm đến từ đâu" · tiền xử lý · tham số LoRA + hai lỗi thật đã sửa

Ba nhóm dưới đây trả lời ba câu phản biện, **chạy theo đúng thứ tự trong bảng** (rẻ trước; nhóm PhoBERT
đứng đầu để lộ ngay nếu máy ảo thiếu Java/VnCoreNLP). Mỗi lượt khác lượt CHA của nó **đúng MỘT khoá đo
được** - đã kiểm bằng phép so cấu hình ĐÃ HỢP NHẤT của con với cha, nên cột "khác cha" là dấu vết bạn đối
chiếu được với `run_meta.json` của lượt chạy.

> **Vì sao cả 31 notebook phải ghim lại trong gói này:** hai lỗi thật đã được sửa. (1) Đường huấn luyện
> **bỏ qua** bộ tách từ mà lượt chạy khai (`preprocess.segmenter`), nên một lượt khai `pyvi` vẫn chạy bằng
> bộ mặc định của model - phép đo sẽ ra "mọi bộ tách từ như nhau" mà không có gì báo. (2) Bước bỏ emoji bản
> đầu nuốt luôn ký tự XUỐNG DÒNG: 4.158 dòng `train` đổi trong khi chỉ 1.877 dòng có emoji. Bản ghim cũ có
> cả hai lỗi; bản này không.

**Nhóm 1 - KHÔNG học gì / chỉ học đầu phân loại / LoRA (9 lượt, ~1,5-2 giờ).** Trả lời "điểm đến từ đâu".
SÀN = encoder đóng băng + đầu phân loại NGẪU NHIÊN, không có vòng lặp huấn luyện; PROBE = encoder đóng
băng, chỉ đầu phân loại học. SÀN đứng đầu vì nó còn là **bước kiểm ống dẫn**: SÀN mà KHÔNG xấu thì có gì
đó sai, và biết sau ~3 phút thay vì sau 2 giờ.

| # | Notebook | Trả lời câu gì | Khác cha ở đâu | T4 |
| --- | --- | --- | --- | --- |
| 1 | `notebooks/phobert-base-v2/none/exp001.ipynb` | SÀN - không tối ưu gì | `trainer: none` (cha là lượt LoRA) | ~3 phút |
| 2 | `notebooks/cafebert/none/exp001.ipynb` | SÀN cho model lớn hơn | `trainer: none` | ~4 phút |
| 3 | `notebooks/phobert-base-v2/none/exp002.ipynb` | LINEAR PROBE - chỉ đầu phân loại học | `head.trainable: true` | ~10 phút |
| 4 | `notebooks/cafebert/none/exp002.ipynb` | LINEAR PROBE cho CafeBERT | `head.trainable: true` | ~15 phút |
| 5 | `notebooks/phobert-base-v2/lora/exp009.ipynb` | chọn `model/best` theo ACCURACY thay vì F1 (đầu ĐÓNG BĂNG) | `checkpoints.best_metric: accuracy_cell` | ~12-15 phút |
| 6 | `notebooks/phobert-base-v2/lora/exp010.ipynb` | thước nhiễu thứ hai cho đầu ĐÓNG BĂNG | `decoding.seed: 7` | ~12-15 phút |
| 7 | `notebooks/phobert-base-v2/lora/exp008.ipynb` | chọn `model/best` theo ACCURACY (đầu HỌC) | `checkpoints.best_metric: accuracy_cell` | ~13-16 phút |
| 8 | `notebooks/phobert-base-v2/lora/exp011.ipynb` | thước nhiễu thứ hai cho đầu HỌC | `decoding.seed: 7` | ~13-16 phút |
| 9 | `notebooks/cafebert/lora/exp007.ipynb` | chọn `model/best` theo ACCURACY trên model mạnh nhất | `checkpoints.best_metric: accuracy_cell` | ~15-20 phút |

**Nhóm 2 - TIỀN XỬ LÝ: bộ tách từ và emoji (12 lượt, ~3 giờ).** Cùng một model, chỉ khác khâu chia văn
bản - trả lời "tiền xử lý có đáng công không". `icon` là nhánh bỏ emoji ở `train`/`val` (test KHÔNG bị
sửa), và nó là biến thể duy nhất đổi `data.version` (v0.2.0 -> v0.3.0). Bộ tách từ dự phòng
(`underthesea`, `pyvi`) do ô bootstrap tự cài; `vncorenlp` cần Java + model 27 MB, cũng do ô đó lo.

| # | Notebook | Trả lời câu gì | Khác cha ở đâu | T4 |
| --- | --- | --- | --- | --- |
| 10 | `notebooks/phobert-base-v2/lora/exp012.ipynb` | PhoBERT KHÔNG tách từ (bộ chính chủ là vncorenlp) | `preprocess.segmenter: none` | ~13-16 phút |
| 11 | `notebooks/phobert-base-v2/lora/exp014.ipynb` | PhoBERT + `pyvi` | `preprocess.segmenter: pyvi` | ~13-16 phút |
| 12 | `notebooks/phobert-base-v2/lora/exp013.ipynb` | PhoBERT + `underthesea` | `preprocess.segmenter: underthesea` | ~13-16 phút |
| 13 | `notebooks/phobert-base-v2/lora/exp015.ipynb` | PhoBERT + BỎ EMOJI ở train/val | `data.version: v0.3.0` | ~13-16 phút |
| 14 | `notebooks/visobert/lora/exp006.ipynb` | ViSoBERT + `vncorenlp` (gốc là không tách từ) | `preprocess.segmenter: vncorenlp` | ~12-15 phút |
| 15 | `notebooks/visobert/lora/exp008.ipynb` | ViSoBERT + `pyvi` | `preprocess.segmenter: pyvi` | ~12-15 phút |
| 16 | `notebooks/visobert/lora/exp007.ipynb` | ViSoBERT + `underthesea` | `preprocess.segmenter: underthesea` | ~12-15 phút |
| 17 | `notebooks/visobert/lora/exp009.ipynb` | ViSoBERT + BỎ EMOJI ở train/val | `data.version: v0.3.0` | ~12-15 phút |
| 18 | `notebooks/cafebert/lora/exp008.ipynb` | CafeBERT + `vncorenlp` (gốc là không tách từ) | `preprocess.segmenter: vncorenlp` | ~15-20 phút |
| 19 | `notebooks/cafebert/lora/exp010.ipynb` | CafeBERT + `pyvi` | `preprocess.segmenter: pyvi` | ~15-20 phút |
| 20 | `notebooks/cafebert/lora/exp009.ipynb` | CafeBERT + `underthesea` | `preprocess.segmenter: underthesea` | ~15-20 phút |
| 21 | `notebooks/cafebert/lora/exp011.ipynb` | CafeBERT + BỎ EMOJI ở train/val | `data.version: v0.3.0` | ~15-20 phút |

**Nhóm 3 - THAM SỐ LoRA (10 lượt, ~2,5 giờ).** Hiện mọi lượt dùng CÙNG một bộ (`r 16 · alpha 32 · lr
2e-4 · 2-4 module`). Mỗi lượt ở đây đổi **đúng một** tham số. Ghi khi đọc: đổi `r` mà GIỮ `alpha` là đổi
luôn tỉ lệ scaling `alpha / r` (8 -> 4 và 1); lượt `exp020`/`exp016` giảm số module được gắn adapter, nên
`trainable_params` trong `metrics.json` **GIẢM** - đó là dấu vết để kiểm trước khi đọc điểm.

| # | Notebook | Trả lời câu gì | Khác cha ở đâu | T4 |
| --- | --- | --- | --- | --- |
| 22 | `notebooks/phobert-base-v2/lora/exp016.ipynb` | hạng adapter NHỎ hơn (r 16 -> 8) | `lora.r: 8` | ~13-16 phút |
| 23 | `notebooks/phobert-base-v2/lora/exp017.ipynb` | hạng adapter LỚN hơn (r 16 -> 32) | `lora.r: 32` | ~13-16 phút |
| 24 | `notebooks/phobert-base-v2/lora/exp018.ipynb` | học CHẬM hơn (lr 2e-4 -> 1e-4) | `lr: 0.0001` | ~13-16 phút |
| 25 | `notebooks/phobert-base-v2/lora/exp019.ipynb` | học NHANH hơn (lr 2e-4 -> 4e-4) | `lr: 0.0004` | ~13-16 phút |
| 26 | `notebooks/phobert-base-v2/lora/exp020.ipynb` | gắn adapter vào 2 module thay vì 4 | `lora.target_modules: [query, value]` | ~13-16 phút |
| 27 | `notebooks/cafebert/lora/exp012.ipynb` | (như #22, model mạnh nhất) | `lora.r: 8` | ~15-20 phút |
| 28 | `notebooks/cafebert/lora/exp013.ipynb` | (như #23) | `lora.r: 32` | ~15-20 phút |
| 29 | `notebooks/cafebert/lora/exp014.ipynb` | (như #24) | `lr: 0.0001` | ~15-20 phút |
| 30 | `notebooks/cafebert/lora/exp015.ipynb` | (như #25) | `lr: 0.0004` | ~15-20 phút |
| 31 | `notebooks/cafebert/lora/exp016.ipynb` | (như #26) | `lora.target_modules: [query, value]` | ~15-20 phút |

**Cách đọc số của cả 31 lượt:** luôn đọc theo **CẶP chỉ số** - F1 lớp âm + macro-F1 **và** số ô - không
chỉ accuracy; và nhớ **biên nhiễu của đường encoder là +-0,33 ... +-0,67 điểm** (ba lượt chạy lại cha với
`decoding.seed: 7`, xem `docs/04_experiments/06_lora_encoder.md`). Chênh lệch nhỏ hơn mức đó thì kết luận
là "chưa thấy khác biệt", KHÔNG phải "không khác biệt". Nếu một lượt cho số lạ (ví dụ SÀN mà accuracy cao
bất thường), gửi lại nguyên thư mục kết quả để nhóm dò ống dẫn trước khi đọc tiếp.

### Đợt 11 - 6 notebook: hàm mất mát (focal, trọng số theo khía cạnh) và DoRA

Sáu lượt này cũng dùng hai lượt cha như bảng trên (`phobert-base-v2/lora/exp005`, `cafebert/lora/exp002`),
và mỗi lượt đổi **đúng một** khoá đo được. Trả lời "còn cách nào khác để chữa mất cân bằng / tăng chất
lượng adapter không", và trả lời ĐỘC LẬP với ba nhóm 1-3 ở trên.

| # | Notebook | Trả lời câu gì | Khác cha ở đâu | T4 |
| --- | --- | --- | --- | --- |
| 32 | `notebooks/phobert-base-v2/lora/exp021.ipynb` | hàm mất mát **FOCAL** (gamma 2): dồn sức vào ô model còn yếu, KHÔNG dùng trọng số lớp | `loss.type: focal` + `loss.gamma: 2` | ~13-16 phút |
| 33 | `notebooks/phobert-base-v2/lora/exp022.ipynb` | trọng số lớp đếm **RIÊNG từng khía cạnh** (`price` gần như chỉ có nhãn dương nên bị pha loãng khi đếm chung) | `loss.class_weight: inverse_by_aspect` | ~13-16 phút |
| 34 | `notebooks/phobert-base-v2/lora/exp023.ipynb` | **DoRA**: adapter học cả ĐỘ LỚN của cập nhật, không chỉ hướng | `lora.use_dora: true` | ~13-16 phút |
| 35 | `notebooks/cafebert/lora/exp017.ipynb` | (như #32, trên model mạnh nhất) | `loss.type: focal` + `loss.gamma: 2` | ~15-20 phút |
| 36 | `notebooks/cafebert/lora/exp018.ipynb` | (như #33) | `loss.class_weight: inverse_by_aspect` | ~15-20 phút |
| 37 | `notebooks/cafebert/lora/exp019.ipynb` | (như #34) | `lora.use_dora: true` | ~15-20 phút |

**Ba điều cần biết khi đọc sáu lượt này:** (a) lượt `focal` và lượt `DoRA` KHÔNG dùng trọng số lớp, nên
so chúng với cha `weighted_ce` là so HAI biến (hàm mất mát VÀ trọng số) - muốn tách hẳn thì so từng dòng
`predictions.csv`, đừng chỉ nhìn chênh lệch điểm; (b) `inverse_by_aspect` (#33/#36) mới là lượt so SẠCH
với cha: cùng hàm mất mát, chỉ khác chỗ đếm trọng số; (c) `trainable_params` của lượt DoRA **KHÁC** lượt
cha (DoRA thêm tham số độ lớn) - đó là dấu vết để kiểm trước khi đọc điểm.

### Đợt 11 - 3 notebook: FULL FINE-TUNE (học toàn bộ model)

Ba lượt này trả lời câu "nếu cho model học **TẤT CẢ** tham số (encoder + đầu phân loại) thay vì chỉ sửa
adapter thì hơn bao nhiêu" - mốc đối chứng của cả nhóm LoRA, và là mốc mà các bài báo ABSA thường công bố.
Chúng nằm ở thư mục `full/` (đường chạy mới), không phải `lora/`.

| # | Notebook | Trả lời câu gì | Khác cha ở đâu | T4 |
| --- | --- | --- | --- | --- |
| 38 | `notebooks/phobert-base-v2/full/exp001.ipynb` | full fine-tune, **giữ nguyên `lr` 2e-4** ⇒ phép so chỉ đổi MỘT biến: cơ chế học | `method` + `trainer: full` | ~20-30 phút |
| 39 | `notebooks/cafebert/full/exp001.ipynb` | như #38, trên model mạnh nhất | `method` + `trainer: full` | ~30-45 phút |
| 40 | `notebooks/phobert-base-v2/full/exp002.ipynb` | full fine-tune + **`lr` 2e-5** (mức thông lệ cho full fine-tune) | `method` + `trainer: full` + `lr: 0.00002` | ~20-30 phút |

**Ba điều cần biết trước khi chạy nhóm này:** (a) mỗi lượt chiếm **đĩa lớn** - checkpoint chứa CẢ model
cộng optimizer (cỡ hàng GB, xem `src/training/savers/state_dict.py`), nên chạy xong thì tải thư mục kết
quả về rồi xoá bớt `model/last` trên Drive nếu chật; (b) kiểm **`trainable_params` phải BẰNG `total_params`**
trong `metrics.json` - nhỏ hơn nghĩa là đã rơi về đóng băng một phần, và lượt chạy KHÔNG còn là full
fine-tune; (c) `trainer: full` **không đi** với `inference.quantization: 4bit` (4 bit đóng băng trọng số
gốc, đó là QLoRA) - notebook sẽ báo lỗi ngay ở ô kiểm tra nếu ai đó khai như vậy.

### Đợt 11 - 8 notebook: LLM LỚN HƠN, KHÁC CHẾ ĐỘ, KHÁC HỌ

Ba model MỚI (đều là repo MỞ, tải được không cần token). Mỗi lượt dùng **đúng cấu hình prompt/ví dụ của
lượt cha 4B cùng mức**, khác đúng MỘT khoá: `model`.

| # | Notebook | Trả lời câu gì | T4 |
| --- | --- | --- | --- |
| 41 | `notebooks/qwen3-8b/prompt-cot/exp001.ipynb` | 8B + CoT 0 ví dụ | ~40-60 phút |
| 42 | `notebooks/qwen3-8b/prompt-cot/exp002.ipynb` | 8B + CoT 1 ví dụ | ~40-60 phút |
| 43 | `notebooks/qwen3-8b/prompt-cot/exp003.ipynb` | 8B + CoT 5 ví dụ | ~60-90 phút |
| 44 | `notebooks/qwen3-4b-thinking-2507/prompt-cot/exp001.ipynb` | **LƯỢT DÒ**: bản "luôn suy nghĩ" tốn bao nhiêu token (60 mẫu, trần 8.192) | ~30-45 phút |
| 45 | `notebooks/qwen3-4b-thinking-2507/prompt-cot/exp002.ipynb` | cùng cỡ, KHÁC CHẾ ĐỘ: suy nghĩ trước khi trả lời, 1 ví dụ | ~40-60 phút |
| 46 | `notebooks/mistral-7b-instruct-v0.3/prompt-cot/exp001.ipynb` | HỌ KHÁC (Mistral) + CoT 0 ví dụ | ~40-60 phút |
| 47 | `notebooks/mistral-7b-instruct-v0.3/prompt-cot/exp002.ipynb` | HỌ KHÁC + CoT 1 ví dụ | ~40-60 phút |
| 48 | `notebooks/mistral-7b-instruct-v0.3/prompt-cot/exp003.ipynb` | HỌ KHÁC + CoT 5 ví dụ | ~60-90 phút |

**CHẠY #44 TRƯỚC #45** (thứ tự có lý do): #45 là lượt mang tên "suy nghĩ", và trần sinh của nó phải lấy từ
số ĐO của #44. Trong config của #45, `decoding.max_new_tokens` đang là **giá trị tạm 4.096**; sau khi #44
xong, con số đúng là `làm tròn lên (p99 × 1,5)` - nhóm sẽ cập nhật rồi ghim lại notebook đó (một thao tác,
không cần chạy lại #44).

**Ba model mới chỉ cần internet để tải tokenizer** (~10-50 MB, giống mọi lượt Qwen hiện có): notebook tự
tải khi chạy, KHÔNG phải chép gì lên Drive. Nếu muốn chạy offline thì trỏ `SENTIMENTX_MODEL` trong
`env/.env.colab` vào một thư mục tokenizer/trọng số trên Drive (đường đó áp cho MỘT model mỗi lần).

> **HAI model của nhóm này CHƯA gửi được:** `llama-3.1-8b-instruct` (họ Llama) và `vistral-7b-chat` (tiếng
> Việt chuyên biệt, cùng cỡ Mistral) là repo **GATED** - máy dự án đã thử tải và bị từ chối. Cần `HF_TOKEN`
> có quyền + bấm nhận điều khoản trên trang model; khi có thì nhóm thêm 6 notebook mà không phải sửa gì
> trong gói cũ.

### Đợt 11 - thứ tự chạy 48 notebook (xếp theo thời gian GIẢM DẦN)

**Cộng cả bảng: 2 + 4 + 2 + 1 + 2 + 14 + 14 + 6 + 1 + 1 + 1 = 48 notebook.** Số trong ngoặc của một dòng
là số lượt **của khoảng `exp` ghi ngay trước nó**, KHÔNG phải số lượt của cả dòng - hai chỗ dễ đếm sai:
dòng ~15-20 phút có 13 lượt `cafebert/lora` **cộng** `cafebert/none/exp002` = 14; dòng ~13-16 phút có 13
lượt `phobert-base-v2/lora` **cộng** `lora/exp008` = 14.

| Bậc | Notebook | Trả lời câu gì |
| --- | --- | --- |
| ~60-90 phút | `qwen3-8b/prompt-cot/exp003` · `mistral-7b-instruct-v0.3/prompt-cot/exp003` | LLM 5 ví dụ - đắt nhất, nên vào **phiên Colab mới** |
| ~40-60 phút | `qwen3-8b/prompt-cot/exp001` · `exp002` · `mistral-7b-instruct-v0.3/prompt-cot/exp001` · `exp002` | 0 và 1 ví dụ của hai họ LLM mới |
| ~30-45 phút | `qwen3-4b-thinking-2507/prompt-cot/exp001` (**lượt DÒ**) · `cafebert/full/exp001` | DÒ chốt trần token; full fine-tune model lớn nhất |
| ~40-60 phút | `qwen3-4b-thinking-2507/prompt-cot/exp002` - **CHỜ NHÓM GHIM LẠI: ĐỪNG chạy ở lượt này** (xem ghi chú 1) | lượt "suy nghĩ" 1 ví dụ; trần sinh đang là giá trị **TẠM** nên phải chờ số đo của lượt DÒ |
| ~20-30 phút | `phobert-base-v2/full/exp001` · `exp002` | full fine-tune, hai mức `lr` (giữ nguyên 2e-4 và hạ 2e-5) |
| ~15-20 phút | `cafebert/lora/exp007` → `exp019` (13 lượt) · `cafebert/none/exp002` | 14 lượt CafeBERT: tiêu chí chọn best, tiền xử lý, tham số LoRA, mất mát, DoRA, linear probe |
| ~13-16 phút | `phobert-base-v2/lora/exp008` · `exp011` → `exp023` (13 lượt; **cả dòng** là 14) | 14 lượt PhoBERT cùng nhóm câu hỏi |
| ~12-15 phút | `phobert-base-v2/lora/exp009` · `exp010` · `visobert/lora/exp006-009` | tiêu chí chọn `model/best` + thước nhiễu; ViSoBERT ×4 (bộ tách từ + emoji) |
| ~10 phút | `phobert-base-v2/none/exp002` | LINEAR PROBE - encoder đóng băng, chỉ đầu phân loại học |
| ~4 phút | `cafebert/none/exp001` | SÀN CafeBERT |
| ~3 phút | `phobert-base-v2/none/exp001` | SÀN PhoBERT - **bước KIỂM ỐNG DẪN** (xem ghi chú dưới bảng) |

**Hai ghi chú về thứ tự** - chúng KHÔNG theo thời gian mà theo phụ thuộc/nghiệp vụ:

1. **Lượt DÒ phải chạy trước lượt "suy nghĩ"**: trần sinh của `qwen3-4b-thinking-2507/prompt-cot/exp002`
   đang là giá trị **TẠM 4.096**; số đúng là `làm tròn lên (p99 × 1,5)` lấy từ số đo của `exp001`. Gửi
   kết quả `exp001` về, nhóm cập nhật rồi ghim lại **đúng một** notebook này (không phải chạy lại `exp001`).
   ⇒ Trong lượt này **BỎ QUA `exp002`**: nó vẫn nằm trong `notebooks/` (vì cả 48 lượt đi trong một gói) nhưng
   CHƯA nên chạy - nhóm sẽ ghim lại nó vào commit mới có trần đúng rồi gửi trong gói kế tiếp. Chạy sớm thì
   lượt đó sinh quá trần, bị luật cắt (trung bình ≥ 95% trần) đánh dấu và **phải chạy lại**, tốn 40-60 phút.
2. **Về chẩn đoán, hai lượt SÀN (~3 và ~4 phút) đứng đầu bảng thứ tự RẺ trước vẫn hơn** (đúng như kế
   hoạch đã xếp cho nhóm 1): SÀN = encoder đóng băng + đầu phân loại NGẪU NHIÊN, nên nếu SÀN **không xấu**
   thì có gì đó sai ở ống dẫn - biết sau 3 phút thay vì sau 90 phút. Nếu bạn đi theo đúng bảng giảm dần
   ở trên, hãy chạy **hai lượt SÀN trong cùng phiên đầu tiên** với một lượt dài.

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
