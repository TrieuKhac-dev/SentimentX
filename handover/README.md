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

## Hai mươi notebook trong gói

Mười bảy notebook đã chạy xong nên cột thời gian ghi **số phút ĐO THẬT** (lấy từ `run_meta.json` của
chính lượt đó); **ba notebook 0.6B chưa chạy lần nào** nên ghi rõ là **ước tính**.

| Notebook | Trả lời câu gì | Thời gian trên T4 |
| --- | --- | --- |
| `notebooks/qwen3-0.6b/prompt-cot/exp001.ipynb` | Qwen3 0.6B CoT 0 ví dụ - model nhỏ hơn 10 lần thì kém bao nhiêu | ước tính 20 đến 40 phút |
| `notebooks/qwen3-0.6b/prompt-cot/exp002.ipynb` | Qwen3 0.6B CoT 1 ví dụ | ước tính 20 đến 40 phút |
| `notebooks/qwen3-0.6b/prompt-cot/exp003.ipynb` | Qwen3 0.6B CoT 5 ví dụ | ước tính 20 đến 40 phút |
| `notebooks/qwen3-4b-instruct-2507/prompt-one-turn/exp001.ipynb` | Qwen3 MỘT LƯỢT (0 ví dụ) - mốc so sánh với ba mức CoT | **18 phút** |
| `notebooks/qwen3-4b-instruct-2507/prompt-cot/exp002.ipynb` | Qwen3 4-bit CoT 0 ví dụ (zero-shot) | **1 giờ 34 phút** |
| `notebooks/qwen3-4b-instruct-2507/prompt-cot/exp003.ipynb` | Qwen3 4-bit CoT 1 ví dụ | **2 giờ 04 phút** |
| `notebooks/qwen3-4b-instruct-2507/prompt-cot/exp004.ipynb` | Qwen3 4-bit CoT 5 ví dụ | **42 phút** *(lượt CHẠY TIẾP: chỉ là phần còn lại)* |
| `notebooks/qwen3-4b-instruct-2507/prompt-cot/exp005.ipynb` | Lượng hoá 4-bit làm mất bao nhiêu điểm - mức 0 ví dụ | **2 giờ 04 phút** |
| `notebooks/qwen3-4b-instruct-2507/prompt-cot/exp006.ipynb` | như trên - mức 1 ví dụ | **2 giờ 20 phút** |
| `notebooks/qwen3-4b-instruct-2507/prompt-cot/exp007.ipynb` | như trên - mức 5 ví dụ | **3 giờ 51 phút** |
| `notebooks/qwen3-4b-instruct-2507/prompt-cot/exp008.ipynb` | 4-bit nhưng LÔ 4 (exp002 dùng lô 8): tách "lượng hoá" khỏi "kích thước lô" | **2 giờ 36 phút** |
| `notebooks/qwen3-4b-instruct-2507/prompt-cot/exp009.ipynb` | như exp008 - mức 1 ví dụ (cấu hình tốt nhất hiện có) | **2 giờ 47 phút** |
| `notebooks/qwen3-4b-instruct-2507/prompt-cot/exp010.ipynb` | như exp008 - mức 5 ví dụ | **7 phút** *(lượt CHẠY TIẾP: chỉ là phần còn lại)* |
| `notebooks/qwen3-4b-instruct-2507/prompt-cot/exp011.ipynb` | Ví dụ dạy CÓ nhãn âm (thay vì ví dụ toàn nhãn dương) | **2 giờ 05 phút** |
| `notebooks/qwen3-4b-instruct-2507/prompt-cot/exp012.ipynb` | Quét mọi lời phàn nàn TRƯỚC khi gán mã | **2 giờ 10 phút** |
| `notebooks/qwen3-4b-instruct-2507/prompt-cot/exp013.ipynb` | Nói rõ dữ liệu lệch nhãn, cấm lấy mã 1 làm mặc định | **2 giờ 17 phút** |
| `notebooks/visobert/lora/exp001.ipynb` | ViSoBERT học LoRA thì bằng nào công bố | **12 phút** |
| `notebooks/visobert/lora/exp002.ipynb` | ViSoBERT + trọng số lớp âm (chống đoán mã 1) | **12 phút** |
| `notebooks/phobert-base-v2/lora/exp001.ipynb` | PhoBERT học LoRA thì bằng nào công bố | **13 phút** |
| `notebooks/phobert-base-v2/lora/exp002.ipynb` | PhoBERT + trọng số lớp âm | **14 phút** |

Mỗi notebook chấm trên **cùng tập `test` (cả split của bộ dữ liệu đang dùng)** - đó là con số để so với công bố. Mỗi
notebook ghi vào thư mục kết quả riêng nên chạy song song nhiều phiên cũng không giẫm lên nhau: mọi
notebook đều chạy được cùng lúc vì mỗi lượt có thư mục riêng theo mã băm danh tính.

Ba notebook `exp005`, `exp006`, `exp007` là **bản đối chứng KHÔNG lượng hoá (fp16)** của ba mức ví dụ
4-bit: cùng model, cùng prompt, cùng tập test, chỉ khác cách nạp trọng số - nên chúng trả lời câu
"lượng hoá 4-bit làm mất bao nhiêu điểm". Đây là nhóm **nặng nhất và lâu nhất** (bản không lượng hoá tốn
gấp ~4 lần bộ nhớ), hãy chạy khi phiên Colab còn đủ thời gian. Ba notebook 0.6B thì nhẹ nhất, chạy
trước để làm quen cũng được.

Ba nhóm MỚI của đợt này (mỗi lượt chỉ khác một thứ so với lượt gốc, nên đọc kết quả là đọc được
nguyên nhân):

- `exp008..010` - vẫn 4-bit nhưng hạ lô xuống 4, để so sạch với nhóm fp16 (`exp005..007` cũng lô 4):
  chênh lệch còn lại chỉ có thể do LƯỢNG HOÁ.
- `exp011..013` - ba biến thể prompt ở mức 1 ví dụ: `exp011` đổi nội dung ví dụ (dạy bằng ví dụ có
  nhãn âm), `exp012` thêm bước quét lời phàn nàn trước khi gán mã, `exp013` thêm đoạn nói rõ dữ liệu
  lệch nhãn. Cả ba đều hỏi cùng một câu: **làm sao nhận ra lời chê**, vì đó là chỗ yếu nhất của cả ba
  model.
- `visobert/lora/exp002` và `phobert-base-v2/lora/exp002` - thêm trọng số lớp âm (`weighted_ce`).
  Đọc kết quả bằng **F1 lớp âm** và macro-F1, KHÔNG bằng độ chính xác: đoán mã 1 cho mọi ô vẫn ra độ
  chính xác cao mà lớp âm thì bằng 0.


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
