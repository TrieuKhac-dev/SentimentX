# 07. Chạy notebook trên Colab (Drive + .env.colab)

> Đọc file này khi: chuẩn bị máy Colab để chạy một thí nghiệm đã ghim, hoặc khi notebook báo
> `Drive : CHƯA thấy`.
> Liên quan: `docs/05_config/01_paths.md`, `docs/05_config/07_env.md`, `docs/00_workflow/01_flow.md`,
> `docs/06_plan/P5_notebook_pin.md`

## 1. Ba gốc đường dẫn - đọc trước khi làm gì

| Thứ | Lấy từ đâu | Trên Colab (đúng thiết kế) |
| --- | --- | --- |
| **Code** | luôn `/content/SentimentX` (ô bootstrap kéo đúng commit đã ghim) | `/content/SentimentX` |
| **Gốc dữ liệu** | `SENTIMENTX_DATA_ROOT`, mặc định `<repo>/data` | `<Drive>/data` |
| **Gốc kết quả** | `SENTIMENTX_RESULTS_ROOT`, mặc định `<repo>/experiments` | `<Drive>/experiments` |
| **Định nghĩa thí nghiệm** (`expNNN/config.yaml`, notebook) | luôn trong repo | trong repo |

Cách code tìm Drive (`src/runtime.py`): thử `/content/drive/MyDrive/{folder}` rồi
`/content/drive/Shareddrives/{folder}`, trong đó `{folder}` là biến `SENTIMENTX_DRIVE_FOLDER`, và
**chỉ nhận nếu thư mục đó có file đánh dấu `.sentimentx_root`**. Không đoán theo tên thư mục, vì
`MyDrive` và Shared drives trông giống nhau.

## 2. Trên Drive phải có gì (làm một lần)

```
MyDrive/SentimentX/                                    ← thư mục gốc trên Drive, tên tùy ý
├── .sentimentx_root                                   ← FILE RỖNG, bắt buộc
├── env/.env.colab                                     ← biến môi trường (KHÔNG commit, chứa token)
├── data/
│   ├── raw/cosmetics/v0.1.0/data_train.csv
│   ├── raw/cosmetics/v0.1.0/data_val.csv
│   ├── raw/cosmetics/v0.1.0/data_test.csv
│   ├── raw/cosmetics/v0.1.0/full_data.csv
│   └── processed/cosmetics-ds0.1.0-pl0.1.0-srccosmetics@0.1.0-e0ccc484/
│         train.csv, val.csv, test.csv, label_map.json
└── experiments/                                       ← để TRỐNG, code tự tạo và ghi kết quả vào
```

**Dữ liệu GỐC là bắt buộc**, không chỉ dữ liệu đã xử lý: mã phiên bản dữ liệu được băm từ nội dung
file gốc, nên thiếu raw thì Colab tính ra một mã khác và preflight báo thiếu dataset. Dữ liệu không
nằm trong git (luật 20 của `docs/00_workflow/02_rules.md`), nên bản clone sạch chỉ có `raw_meta.yaml`.

**`env/.env.colab`** - KHÔNG bắt buộc. Notebook tự đặt hai gốc đường dẫn từ thư mục Drive tìm được,
nên một lượt chạy bình thường không cần file này. Chỉ cần khi muốn chỉ đích danh thư mục, ghi đè
đường dẫn, hoặc giữ token DagsHub trong file (nhóm sao chép `.env.colab.example` rồi điền):

```
SENTIMENTX_DATA_ROOT=/content/drive/MyDrive/SentimentX/data
SENTIMENTX_RESULTS_ROOT=/content/drive/MyDrive/SentimentX/experiments
SENTIMENTX_ENV=colab
HF_HOME=/content/hf_cache
DAGSHUB_TOKEN=<token DagsHub>
```

- Dùng Shared drive thì thay bằng `/content/drive/Shareddrives/<tên>/...`.
- `DAGSHUB_TOKEN` để trống cũng chạy được: thiếu token thì phần ghi MLflow tự hạ cấp thành ghi chú
  trong `run.log`, không làm hỏng lượt chạy.
- `HF_HOME` **không** để trên Drive: model 4B tải về Drive rất chậm. Cần bản gốc: `.env.colab.example`.

## 3. Nhóm chuẩn bị thư mục trên Drive (làm một lần, rồi chia sẻ)

Việc này là của **nhóm làm dự án**, không phải của người chạy notebook. Thư mục phải có những gì ở
mục 2: file đánh dấu, dữ liệu gốc, dữ liệu đã xử lý. Đưa lên bằng cách mở Drive, tạo thư mục, rồi
kéo 4 file CSV vào `data/raw/cosmetics/v0.1.0/` và thư mục đã xử lý vào `data/processed/<mã>/`.

File `.sentimentx_root` phải tạo bằng code (web Drive không tạo được tên bắt đầu bằng dấu chấm). Sau
khi đã mount Drive trong Colab:

```python
from pathlib import Path
root = Path("/content/drive/MyDrive/SentimentX")   # sửa thành thư mục của bạn
(root / ".sentimentx_root").touch()                # file rỗng, đánh dấu thư mục của nhóm
print("sẵn sàng:", sorted(item.name for item in root.iterdir()))
```

Không cần nén, không cần `.env.colab`, không cần khai tên thư mục: xem mục 4.

## 4. Người chạy notebook - ba bước

1. **Copy** thư mục nhóm đã chuẩn bị **và file `notebook.ipynb`** vào Drive của mình. Ngay cả khi
   `config.yaml` không được copy theo thì cũng không sao: định nghĩa thí nghiệm nằm trong bản code
   mà ô bootstrap kéo về, không nằm cạnh file notebook.
2. **Mở notebook** từ Drive (Colab: `File > Open notebook > Google Drive`) rồi bấm **Run all**.
3. Khi Colab hỏi quyền truy cập Drive, bấm **Allow** - một lần cho mỗi phiên. Đây là việc duy nhất
   Google không cho tự động hoá.

Hết. Ô bootstrap tự làm phần còn lại và in ra bằng chứng:

| Notebook tự làm | In ra |
| --- | --- |
| Mount Drive nếu chưa mount | `Chưa mount Drive - đang mount (Colab hỏi quyền, bấm Allow)...` |
| Tìm thư mục nhóm bằng FILE ĐÁNH DẤU, **không cần biết tên** | `Drive : /content/drive/MyDrive/SentimentX (nhận ra bằng file đánh dấu)` |
| Đặt gốc dữ liệu và gốc kết quả vào Drive | `Gốc dữ liệu : .../data`, `Gốc kết quả : .../experiments` |
| Kéo ĐÚNG commit đã ghim | `Code : dùng bản code đang có | /content/SentimentX | <sha>` |
| Cài gói máy ảo còn thiếu | `Thiếu gói bitsandbytes - đang cài...` |

Tên thư mục trên Drive không quan trọng: "SentimentX", "SentimentX (1)", hay tên giảng viên đặt đều
được. Nếu trong Drive có nhiều thư mục cùng mang file đánh dấu, code chọn thư mục **có `data/`** -
dấu hiệu thư mục đã được chuẩn bị. Muốn chỉ đích danh một thư mục thì đặt `SENTIMENTX_DRIVE_FOLDER`
**trước** khi chạy notebook, hoặc tạo `env/.env.colab` (xem mục 2 và `docs/05_config/07_env.md`).

### 4.1. Chạy không dùng Drive (chỉ để thử nhanh)

Nếu không có thư mục nào trên Drive, notebook vẫn chạy nhưng ghi dữ liệu và kết quả vào máy ảo, và
**mất khi hết phiên**. Chỉ dùng để xem lượt chạy có chạy không; kết quả không nằm trên Drive nghĩa là
chưa đạt yêu cầu bàn giao.

### 4.2. Nếu ô preflight vẫn báo có việc phải sửa

Đọc danh sách nó in ra: dòng đầu là nguyên nhân gốc (thường là thiếu dữ liệu gốc trên Drive). Bảng ở
mục 7 có cách xử lý cho từng dòng.

## 5. Coi là thành công khi thấy gì

- Ô preflight: `dữ liệu gốc: đủ (4 file)`, `dataset: <đường dẫn trên Drive>`,
  `trạng thái: NEW`, `GPU: ...`, `Không có việc nào phải sửa.`
- Ô chạy: `Chế độ chạy: NEW` rồi `Chế độ: NEW | thư mục: <Drive>/experiments/...`.
- Kết quả nằm ở
  `<Drive>/experiments/<model>/<method>/<expNNN>/results/<mã dữ liệu>/`, gồm `run.log`,
  `run_meta.json`, `metrics.json`, `metrics.csv`, `mispredictions.csv`, thư mục `predictions/`.
- Mở `run.log` trước: nó ghi từng bước, và ghi rõ khi chạy tiếp (`[RUN] mode=RESUME`).

Máy đứt giữa chừng thì cứ Run all lần nữa: phần đã xong nằm trong `predictions/part_*.jsonl` và
điểm số vẫn tính trên cả split.

## 6. Mang kết quả nhẹ về repo để commit

Kết quả sinh trên Colab nằm trên Drive; muốn vào git thì copy phần nhẹ về (P7 mục 5). Trong Colab:

```python
!cd /content && tar czf /content/ket-qua.tar.gz -C /content/drive/MyDrive/SentimentX/experiments \
   <model>/<method>/<expNNN>/results
```

Giải nén vào `experiments/` của repo **chỉ giữ** `run.log`, `run_meta.json`, `metrics.json`,
`metrics.csv`, `mispredictions.csv`. Ba thứ nặng (`predictions*`, `plots/`, `model/`) đã bị
`.gitignore` chặn sẵn - đúng chủ ý, vì đó là bản sao dữ liệu chứ không phải bằng chứng.

## 7. Gặp lỗi thì tra bảng này

| Triệu chứng | Nguyên nhân | Cách sửa |
| --- | --- | --- |
| `Drive : CHƯA thấy - dữ liệu và kết quả sẽ nằm trong máy ảo...` | thư mục nhóm chưa lên Drive; hoặc thiếu `.sentimentx_root`; hoặc chưa bấm Allow cho Drive | đưa thư mục nhóm lên Drive (mục 3), bấm Allow, rồi chạy lại ô bootstrap |
| `Gốc dữ liệu : /content/SentimentX/data` dù đã mount | notebook không tìm thấy thư mục nhóm, nên dùng gốc mặc định trong máy ảo; hoặc `.env.colab` ghi đè sai đường dẫn | kiểm file đánh dấu `.sentimentx_root` trong thư mục nhóm; kiểm `SENTIMENTX_DATA_ROOT` nếu có file env |
| `git clone ... -> 128 ... not an empty directory` | thư mục còn từ lần chạy trước | bootstrap bỏ qua bước clone khi thư mục đã là repo; nếu là thư mục lạ thì nó DỪNG kèm `rm -rf` để bạn tự xoá |
| `Thiếu N file dữ liệu GỐC` | thư mục nhóm trên Drive chưa có dữ liệu gốc | thêm 4 file CSV vào `data/raw/cosmetics/v0.1.0/` (mục 3) |
| `Model config khai inference.quantization: 4bit nhưng máy chưa có bitsandbytes` | máy ảo thiếu gói | bình thường notebook tự cài (`Thiếu gói bitsandbytes - đang cài...`). Nếu `pip install ->` khác 0 thì đọc dòng lỗi in ngay dưới |
| `Thiếu tập đánh giá .../test.csv` | thư mục nhóm chưa có dữ liệu đã xử lý | thêm thư mục `data/processed/<mã>/`, hoặc chạy `python run_pipeline.py --dataset cosmetics --version v0.1.0` trong `/content/SentimentX` |
| `Mã phiên bản đang dùng (...) khác mã tính từ config` | dữ liệu gốc trên Drive khác bản ở máy | dùng đúng 4 file của `cosmetics/v0.1.0`. Khác kiểu xuống dòng CRLF/LF **không** còn làm lệch mã |
| `CUDA out of memory` | batch quá lớn cho GPU của máy ảo | giảm `batch` trong `configs/experiments/training.yaml` |
| Vẫn `ModuleNotFoundError: No module named 'src'` | kernel còn nhớ kết luận "không có gói `src`" từ lúc máy trống | Runtime -> Restart session rồi Run all; ô bootstrap đã tự xoá bộ nhớ đệm import |
| Muốn chạy lại từ đầu | | `python run_qwen_eval.py ... --new` (kết quả cũ chuyển sang `predictions/_bo-qua-*`), hoặc xoá thư mục kết quả trên Drive |

## 8. Đừng đổi thứ tự nếu chưa hiểu vì sao

- **Người chạy chỉ bấm Allow một lần cho Drive, rồi Run all.** Mount, tìm thư mục, đặt hai gốc và
  cài gói thiếu đều nằm trong ô bootstrap; đừng chuyển chúng ra thành các bước tay, vì bước tay thì
  sớm muộn cũng bị bỏ qua hoặc làm sai thứ tự.
- **Phải có `.sentimentx_root`.** `MyDrive` và Shared drives trông giống nhau; không có file đánh dấu
  thì notebook không tìm được thư mục nhóm và sẽ ghi kết quả vào máy ảo (mất khi hết phiên). Tên thư
  mục thì không quan trọng - đây là điều khiến bản giao chỉ còn "copy thư mục rồi bấm Run all".
- **Chỉ định thư mục bằng `SENTIMENTX_DRIVE_FOLDER` hay `env/.env.colab` thì phải xong TRƯỚC ô
  bootstrap:** biến môi trường đọc lúc chạy, còn file env nằm *trong* Drive nên không thể nói Drive ở đâu.
- **Ô bootstrap kéo code TRƯỚC khi `import src`,** và kéo đúng commit đã ghim. Test
  `tests/test_templates.py::TestBootstrap` khoá thứ tự này cho mọi notebook thí nghiệm.
- **`HF_HOME` để ở `/content`,** không để trên Drive.
- Sau khi ghim, **không sửa** `experiments/**/expNNN/**` cho tới khi người nhận chạy xong
  (`docs/00_workflow/02_rules.md`).

