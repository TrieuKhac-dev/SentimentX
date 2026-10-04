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

## Mười bảy notebook trong gói (đợt 7)

**Chưa lượt nào chạy trước đây**, nên cột thời gian ghi **ước tính**; chỗ nào ước tính dựa trên một lượt
đã chạy thật thì ghi rõ số đo thật đó để bạn đối chiếu. Bảng xếp theo **thứ tự nên chạy** (rẻ và lượt
chặn đường trước - lượt DÒ chốt trần token cho nhánh suy nghĩ của đợt sau).

| Notebook | Trả lời câu gì | Thời gian trên T4 |
| --- | --- | --- |
| `notebooks/phobert-large/lora/exp001.ipynb` | Encoder LỚN hơn: cùng kho tiền huấn luyện và cùng bộ tách từ với PhoBERT-base, chỉ khác số tham số | ước tính 15 đến 20 phút (lượt cùng cấu hình đã chạy thật: 14 phút) |
| `notebooks/vibert-base-cased/lora/exp001.ipynb` | Encoder tiếng Việt **khác kho** tiền huấn luyện (FPT) | ước tính 15 đến 20 phút (đã chạy thật: 12 đến 14 phút) |
| `notebooks/cafebert/lora/exp001.ipynb` | XLM-R rồi tiền huấn luyện TIẾP bằng tiếng Việt - bậc thang giữa PhoBERT và XLM-R | ước tính 15 đến 20 phút |
| `notebooks/xlm-roberta-base/lora/exp001.ipynb` | **Đối chứng NGUỒN tiền huấn luyện**: model đa ngữ (ít tiếng Việt) kém hơn bao nhiêu | ước tính 15 đến 20 phút |
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

Bốn nhóm MỚI của đợt này (mỗi lượt chỉ khác **một** thứ so với lượt gốc, nên đọc kết quả là đọc được
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

### Nhóm encoder gửi thêm tệp xác suất

Sáu lượt encoder (bốn encoder mới + hai lượt `val`) ghi **thêm** `probabilities.csv` cạnh các tệp kết quả
thường: mỗi dòng là một ô (review × khía cạnh) kèm xác suất từng mã. Hai bước **ngưỡng** và **ensemble**
không chạy notebook nào - chúng đọc tệp này, nên khi gửi kết quả về **nhớ gửi kèm tệp xác suất**; thiếu nó
thì hai bước đó không chạy được.

### Nhánh suy nghĩ (đợt sau): đắt gấp khoảng 5 lần

Notebook `qwen3-0.6b/prompt-cot/exp004` (lượt **DÒ** trong gói này) tồn tại để **chốt trần token** cho nhánh
bật suy nghĩ ở đợt sau: model bật suy nghĩ viết phần ` thinking` rất dài, và nếu trần token thấp thì nó viết
hết trần rồi không còn chỗ in JSON - đã gặp thật (ba lượt 0,6B ngày 02/10/2026 chỉ đọc được 3,33 / 1,36 /
1,73%). Vì vậy nhánh suy nghĩ **chậm hơn hẳn** (ước tính xấp xỉ **5 lần** nhánh tắt suy nghĩ), và **mọi
lượt bật suy nghĩ đều phải chạy lượt DÒ trước** để chọn `max_new_tokens = làm tròn lên (p99 × 1,5)`.


Cần chạy GPU: `Runtime > Change runtime type > T4 GPU`. Hai notebook LoRA cần thêm thư viện `peft`
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
    model/last          adapter đủ để chạy tiếp (chỉ có ở hai notebook LoRA)
    model/best          adapter để suy luận (chỉ có ở hai notebook LoRA)
```

Máy đứt giữa chừng thì cứ bấm Run all lần nữa: notebook tự chạy tiếp, không làm lại phần đã xong.
Phiên Colab hết thời gian giữa lượt chạy dài là chuyện bình thường, và đó chính là lúc cơ chế chạy
tiếp có tác dụng.

## Cần gửi lại gì

Sáu file **nhẹ**: `run.log`, `metrics.json`, `metrics.csv`, `run_meta.json`, `mispredictions.csv`,
`mispredictions_paper.csv`.
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
