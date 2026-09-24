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

**`env/.env.colab`** (nhóm sao chép từ `.env.colab.example` rồi điền):

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

## 3. Chuẩn bị ở máy cá nhân

```powershell
# 1. Lấy notebook và code mới nhất (ô ghim đổi mỗi lần sửa code)
git pull origin experiment

# 2. Nén dữ liệu cần đưa lên (chạy ở gốc repo)
Compress-Archive -Force -Path `
  'data\raw\cosmetics\v0.1.0\data_train.csv','data\raw\cosmetics\v0.1.0\data_val.csv',`
  'data\raw\cosmetics\v0.1.0\data_test.csv','data\raw\cosmetics\v0.1.0\full_data.csv' `
  -DestinationPath "$HOME\Desktop\sentimentx-raw.zip"

# 3. Tùy chọn: gói dữ liệu đã xử lý để Colab khỏi phải chạy pipeline
Compress-Archive -Force -Path `
  'data\processed\cosmetics-ds0.1.0-pl0.1.0-srccosmetics@0.1.0-e0ccc484\*' `
  -DestinationPath "$HOME\Desktop\sentimentx-processed.zip"
```

## 4. Trên Colab - thứ tự bắt buộc

### 4.1. Ô thêm ở trên cùng, chạy TRƯỚC mọi ô của notebook

```python
import os
os.environ["SENTIMENTX_DRIVE_FOLDER"] = "SentimentX"   # phải có TRƯỚC ô bootstrap
os.environ["HF_HOME"] = "/content/hf_cache"

from google.colab import drive
drive.mount("/content/drive")

from pathlib import Path
root = Path("/content/drive/MyDrive/SentimentX")
(root / "env").mkdir(parents=True, exist_ok=True)
(root / ".sentimentx_root").touch()                    # file đánh dấu, rỗng
(root / "data" / "raw" / "cosmetics" / "v0.1.0").mkdir(parents=True, exist_ok=True)
(root / "experiments").mkdir(parents=True, exist_ok=True)
print("sẵn sàng:", sorted(item.name for item in root.iterdir()))
```

Lần đầu còn phải tạo `env/.env.colab` với nội dung ở mục 2 (đặt bằng code trong Colab, không tạo
tay trên web Drive, để chắc chắn tên file đúng).

### 4.2. Chạy ô 1 (ghim) và ô 2 (bootstrap) của notebook

Đợi dòng cuối cùng của ô 2. Kỳ vọng:

```
Drive       : /content/drive/MyDrive/SentimentX
Gốc dữ liệu : /content/drive/MyDrive/SentimentX/data
Gốc kết quả : /content/drive/MyDrive/SentimentX/experiments
Code        : dùng bản code đang có | /content/SentimentX | <8 ký tự đầu của commit đã ghim>
```

### 4.3. Đưa dữ liệu lên Drive

Upload hai file zip bằng file explorer của Colab (kéo vào `/content`), rồi:

```python
!unzip -o /content/sentimentx-raw.zip -d /content/drive/MyDrive/SentimentX/data/raw/cosmetics/v0.1.0
!unzip -o /content/sentimentx-processed.zip -d /content/drive/MyDrive/SentimentX/data/processed/cosmetics-ds0.1.0-pl0.1.0-srccosmetics@0.1.0-e0ccc484
```

Không có `sentimentx-processed.zip` thì tạo dữ liệu đã xử lý ngay trên Colab:

```python
!pip install -q -r /content/SentimentX/requirements-colab.txt
!cd /content/SentimentX && python run_pipeline.py --dataset cosmetics --version v0.1.0
```

### 4.4. Cài gói còn thiếu

```python
!pip install -q -r /content/SentimentX/requirements-colab.txt
```

⚠️ Không chạy `pip install -r requirements.txt` trên Colab: file đó ghim cả `torch` cho máy
cá nhân Windows, có thể thay bản torch mà Colab đang dùng và làm hỏng CUDA.

### 4.5. Run all

Ô preflight phải in `Không có việc nào phải sửa.` Nếu chưa, đọc danh sách nó in ra - dòng đầu là
nguyên nhân gốc (thường là thiếu dữ liệu gốc).

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
| `Drive : CHƯA thấy (mount Drive rồi chạy lại ô này)` | chưa mount; hoặc `SENTIMENTX_DRIVE_FOLDER` chưa đặt; hoặc thiếu `.sentimentx_root` | mount trước; đặt env **trước** ô bootstrap; tạo file đánh dấu đúng tên (mục 4.1) |
| `Gốc dữ liệu : /content/SentimentX/data` dù đã mount | chưa có `env/.env.colab`, hoặc `SENTIMENTX_DATA_ROOT` sai | kiểm file env (mục 2); biến trong `os.environ` thắng biến trong file |
| `git clone ... -> 128 ... not an empty directory` | thư mục còn từ lần chạy trước | bootstrap nay bỏ qua bước clone khi thư mục đã là repo; nếu là thư mục lạ thì nó DỪNG kèm `rm -rf` để bạn tự xoá |
| `Thiếu N file dữ liệu GỐC` | chưa đưa raw lên | mục 4.3 |
| `Model config khai inference.quantization: 4bit nhưng máy chưa có bitsandbytes` | thiếu gói | `pip install -r requirements-colab.txt` |
| `Thiếu tập đánh giá .../test.csv` | chưa có dữ liệu đã xử lý | upload `sentimentx-processed.zip`, hoặc chạy `run_pipeline.py` (mục 4.3) |
| `Mã phiên bản đang dùng (...) khác mã tính từ config` | dữ liệu gốc trên Drive khác bản ở máy | dùng đúng 4 file của `cosmetics/v0.1.0`. Khác kiểu xuống dòng CRLF/LF **không** còn làm lệch mã |
| `CUDA out of memory` | batch quá lớn cho GPU của máy ảo | giảm `batch` trong `configs/experiments/training.yaml` |
| Vẫn `ModuleNotFoundError: No module named 'src'` | kernel còn nhớ kết luận "không có gói `src`" từ lúc máy trống | Runtime -> Restart session rồi Run all; ô bootstrap đã tự xoá bộ nhớ đệm import |
| Muốn chạy lại từ đầu | | `python run_qwen_eval.py ... --new` (kết quả cũ chuyển sang `predictions/_bo-qua-*`), hoặc xoá thư mục kết quả trên Drive |

## 8. Đừng đổi thứ tự nếu chưa hiểu vì sao

- **Mount Drive và `SENTIMENTX_DRIVE_FOLDER` phải xong TRƯỚC ô bootstrap.** Ô bootstrap gọi
  `runtime.drive_dir()` ngay khi chạy, và biến này không thể đọc từ `env/.env.colab` - file đó nằm
  *trong* Drive (vòng luẩn quẩn).
- **Phải có `.sentimentx_root`.** `MyDrive` và Shared drives trông giống nhau; không có file đánh dấu
  thì code sẽ ghi kết quả vào một thư mục cùng tên của người khác mà không ai thấy sai.
- **Ô bootstrap kéo code TRƯỚC khi `import src`,** và kéo đúng commit đã ghim. Test
  `tests/test_templates.py::TestBootstrap` khoá thứ tự này cho mọi notebook thí nghiệm.
- **`HF_HOME` để ở `/content`,** không để trên Drive.
- Sau khi ghim, **không sửa** `experiments/**/expNNN/**` cho tới khi người nhận chạy xong
  (`docs/00_workflow/02_rules.md`).

