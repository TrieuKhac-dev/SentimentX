# SentimentX — ABSA tiếng Việt cho review mỹ phẩm

Dự án phân tích cảm xúc theo khía cạnh (**ABSA** — Aspect-Based Sentiment Analysis) cho
review son mỹ phẩm tiếng Việt.

## 1. Bài toán

Mỗi review có thể nhắc tới nhiều khía cạnh (aspect) khác nhau, và mỗi khía cạnh có
một sắc thái riêng. Ví dụ:

> "Son đẹp nhưng ship lâu"
> → `colour` = positive, `shipping` = negative

Ta giải quyết **7 aspect**: `stayingpower`, `texture`, `smell`, `price`, `colour`,
`shipping`, `packing`. Mỗi aspect nhận 1 trong 4 trạng thái:
`positive`, `negative`, `neutral`, hoặc **không được nhắc tới**.

## 2. Ba pha độc lập

Dự án tách rõ ba việc khác nhau, **không trộn vào nhau**:

```
                  RAW DATA  (data/raw/<tên dataset>)
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
        EDA                    DATA PIPELINE
 "Dữ liệu đang thế nào?"   "Ta sẽ xử lý thế nào?"
         │                           │
         └─────────────┬─────────────┘
                       ▼
              FILE KẾT QUẢ (JSON + CSV)
             data/reports/<pha>/versions/<mã>/
                       │
                       ▼
                  BUILD REPORT
      Plotly (biểu đồ) + Jinja2 (giao diện) → HTML / MD
                       │
                       ▼
            MODEL PREPROCESSING (Pha 3)
       PhoBERT / ViSoBERT / Qwen3-4B
     (ViTASA đang gác — xem docs/04_experiments/04_backlog.md)
```

| Pha | Trả lời câu hỏi | Ở đâu trong repo |
|-----|------------------|------------------|
| **EDA** | Dữ liệu đang như thế nào? | `src/eda/` |
| **Data Pipeline** | Ta làm gì với dữ liệu? | `src/pipeline/` |
| **Model preprocessing** | Chuẩn bị input cho từng model ra sao? | `src/preprocessing/` (pha sau) |
| **Đo input thật** | Input của từng model dài bao nhiêu token, có bị cắt không? | `run_token_stats.py` (pha 3) |

Nguyên tắc quan trọng:

- **EDA chỉ đo lường, không sửa dữ liệu.**
- **Pipeline mới là nơi biến đổi dữ liệu**, theo đúng policy đã chốt.
- **Validation cuối pipeline là "cổng chất lượng"**, không phải EDA lần hai.
- **Teencode / từ lạ chỉ được ĐO, không bao giờ bị loại bỏ hay thay thế**: dự án
  không có bằng chứng khoa học để nói một cách viết lóng là "sai", nên bộ quy tắc
  nhận diện nằm hoàn toàn ở EDA và pipeline không có công tắc nào cho việc này.
- **Không bỏ dấu tiếng Việt ở bất kỳ chỗ nào**: văn bản đi vào model giữ nguyên dấu
  (`"Son đẹp"`, không phải `"son dep"`), và cả **khoá so trùng** của bước Clean cũng
  giữ dấu — `clean.deduplicate.ignore_diacritics: false`. Bước Final Validate có hạng
  mục "Văn bản chỉ đổi hình thức" đối chiếu từng ký tự để chứng minh điều này.
- Pipeline **không tự động "clean hết mức có thể"**: mỗi phép biến đổi đều
  **bật/tắt được** và **được ghi lại** cùng phiên bản config.

## 3. Cài đặt

```bash
pip install -r requirements.txt
```

Gồm `pandas`, `numpy`, `PyYAML` (xử lý dữ liệu) và `plotly`, `jinja2` (sinh báo cáo).
Riêng dataset dùng định dạng Parquet thì cài thêm `pyarrow`.

### Riêng pha 3 (đo input thật của model): cần thêm JAVA

Bộ tách từ **chính chủ** của PhoBERT (RDRSegmenter, nằm trong VnCoreNLP) là một chương
trình Java, được gọi từ Python qua pyjnius. Vì vậy máy nào muốn đo / huấn luyện PhoBERT
thì cài thêm hai thứ dưới đây — **cả nhóm nên chạy đúng hai lệnh này** để dùng cùng một
bản (không cần quyền admin, gỡ ra chỉ cần xoá thư mục):

```bash
# JDK 17 LTS (Temurin) -> %USERPROFILE%\.jdks\temurin-17, có kiểm SHA256
powershell -ExecutionPolicy Bypass -File scripts\setup_java.ps1

# Thư viện py-vncorenlp + model VnCoreNLP -> data/models/vncorenlp (đã có trong .gitignore)
powershell -ExecutionPolicy Bypass -File scripts\setup_vncorenlp.ps1
```

Kiểm tra: `python run_token_stats.py --list-segmenters` — dòng `vncorenlp` phải hiện
`dùng được = có`. Máy chưa cài được Java mà vẫn muốn chạy ngay thì dùng
`--segmenter pyvi` (`pip install pyvi`), nhưng phải ghi rõ đã dùng bộ nào vì số liệu
của hai bộ không so sánh ngang nhau được. Chi tiết (vì sao cài bằng ZIP thay vì `winget`,
vì sao không dùng `py_vncorenlp.download_model`): xem
[docs/04_experiments/02_phase3_input.md §5](docs/04_experiments/02_phase3_input.md).


### Riêng pha 4 (chạy Qwen3 bằng chỉ dẫn): cần `torch` bản CUDA

`transformers` không đủ để chạy model. Pha 4 cần thêm `torch` bản **CUDA** (2,6 GB, phải tải
từ kho riêng nên không nằm trong `requirements.txt`), `accelerate` và `bitsandbytes`:

```bash
# 1) torch bản CUDA 12.6 cho GPU NVIDIA
pip install torch --index-url https://download.pytorch.org/whl/cu126

# 2) các gói của dự án, gồm accelerate + bitsandbytes
pip install -r requirements.txt
```

Mạng chậm thì dùng mirror (đã gặp thật: tải từ `download-r2.pytorch.org` bị **treo ở 630 MB**):
`pip install torch --index-url https://mirrors.aliyun.com/pytorch-wheels/cu126/`.

**Vì sao cần lượng hóa 4-bit:** Qwen3-4B ở bf16 là **8 GB**, GPU của máy phát triển có **6 GB**.
Đây là lượng hóa **khi chạy** (không phải để huấn luyện) — dự án **không** fine-tune Qwen3:
Qwen3 dùng như model đa năng qua **chỉ dẫn**, còn PhoBERT (135M) và ViSoBERT (~108M) thì
fine-tune toàn bộ, không cần LoRA.

Phiên bản đã chạy thật ở máy này: `torch 2.14.0+cu126`, `transformers 5.17.0`,
`accelerate 1.15.0`, `bitsandbytes 0.50.2`.

### Tải trọng số Qwen3 (8 GB) — cả nhóm dùng cùng một bản

```bash
powershell -ExecutionPolicy Bypass -File scripts\setup_qwen_model.ps1
```

Script tải trọng số từ **ModelScope** (mirror chính thức của Qwen), chia mỗi file thành nhiều
khối tải **song song**, tự nối tiếp khi đứt mạng, và **kiểm lại kích thước từng file** trước
khi báo xong. Trọng số nằm ở `data/models/` (đã có trong `.gitignore` — 8 GB thì không đưa
vào git được), tải xong thì nạp bằng `--model data/models/Qwen3-4B-Instruct-2507`.

Vì sao phải có script riêng thay vì `hf download` (đều là lỗi đã gặp thật, không phải phòng xa):

| Hiện tượng | Nguyên nhân | Cách xử lý trong script |
|-----------|-------------|-------------------------|
| Tải đứng ở ~95–116 MB rồi không tiến triển, dừng tiến trình thì cache còn **0 GB** | Đường Xet của hub đời mới | Tải từ ModelScope, kiểm kích thước sau khi nối |
| Hai tiến trình tải chạy chồng nhau, cả hai đứng ở `Still waiting to acquire lock ... elapsed 170s` | Giành **file khoá** trong `.locks/` | Một tiến trình; script dùng thư mục khối riêng, không qua hub cache |
| Vòng lặp gọi `curl` tuần tự chỉ đạt 0,06–0,5 MB/s | Mỗi lúc chỉ **một** kết nối | Mỗi khối một tiến trình → đo được 6–8 MB/s |
| Script chạy "xong" mà không tải gì | `curl -I` tới ModelScope trả về **rỗng** nên số khối tính ra 0 | Lấy kích thước từ API của HF và **kiểm lại** kích thước cuối cùng |


## 4. Chạy

```bash
# 1) Khảo sát dữ liệu — chỉ đọc, không sửa; ghi file kết quả
python run_eda.py --dataset cosmetics

# 2) Xử lý dữ liệu theo config; ghi dataset + file kết quả
python run_pipeline.py --dataset cosmetics

# 3) Vẽ báo cáo từ file kết quả (không tính lại số liệu; mở luôn 2 file HTML)
python build_report.py --dataset cosmetics

# 4) (Pha 3) Đo input thật của từng tokenizer trên dữ liệu đã xử lý
python run_token_stats.py --dataset cosmetics

# 5) (Pha 3) Xem/phối hợp cấu hình đo: prompt nào, bộ tách từ nào, ngưỡng cắt nào
python run_token_stats.py --list-prompts            # đang có prompt nào (tên + sha)
python run_token_stats.py --list-segmenters         # máy này cài được bộ tách từ nào
python run_token_stats.py --prompt qwen_absa_v1     # đo với một prompt khác
python run_token_stats.py --segmenter pyvi          # đo với một bộ tách từ khác
python run_token_stats.py --max-length qwen=1280    # đo với ngưỡng cắt khác (thử nhanh)

# 6) (Pha 3) Kiểm file ví dụ few-shot: cấu trúc, nhãn, và RÒ RỈ với val/test
python run_check_examples.py

# 7) (Pha 4) Chạy Qwen3 bằng chỉ dẫn (prompt một lượt / CoT) rồi chấm điểm
python run_qwen_eval.py --split val --prompt qwen_absa_cot_v1 --limit 200

# 8) Test tự động (không cần GPU, không cần model)
python -m unittest discover -s tests

# 9) (Pha 4) Chấm lại kết quả từ file dự đoán đã lưu — không cần GPU
#    (dùng khi sửa cách chấm điểm; nhãn đã parse nằm sẵn trong file dự đoán nên không phải
#     chạy lại model, và mục lục sẽ ghi rõ là đã chấm lại)
python run_rescore_eval.py
```

`run_qwen_eval.py` mặc định chạy trên **val** (tập để LỰA CHỌN prompt/ngưỡng), không phải
test: chọn theo test là tự lừa mình. Mặc định sinh **greedy** (tái lập được); muốn dùng cấu
hình khuyến nghị của model card thì thêm `--sample` (nhiệt độ 0.7, top_p 0.8, top_k 20 — và
`--seed` sẽ được ghi lại). `--limit N` chạy trên tập con ngẫu nhiên có seed; tên file ghi rõ
`n<N>` nên **không bao giờ lẫn** kết quả tập con với kết quả toàn tập.

`--prompt`, `--segmenter` và `--max-length` ghi ra **file CSV riêng**
(`token_stats__prompt-X.csv`, `token_stats__seg-Y.csv`, `...__maxlen-qwen-1280.csv`), không
ghi đè số liệu của cấu hình mặc định — nhờ vậy so hai thí nghiệm vẫn còn nguyên cả hai bên.
Prompt nào dùng khối ví dụ few-shot (`{examples}`) thì tên file có thêm **`ex-<sha4>`** — mã
của BỘ VÍ DỤ, kể cả khi chạy bằng cấu hình dự án: hai bộ ví dụ khác nhau (một ví dụ vs hai
ví dụ) là hai thí nghiệm, mà `prompt_sha` của chúng lại giống nhau nên không có mã đó thì
chúng sẽ ghi đè lên nhau. Xem `python run_token_stats.py --list-prompts` để biết prompt nào
đang có bao nhiêu ví dụ và đường dẫn file ví dụ.
Đổi prompt chỉ cần thêm một file `configs/prompts/<tên>.txt`; đổi prompt mà model đang dùng
thì sửa `configs/models/qwen.yaml`. Ngưỡng cắt thì đổi được ở **cả ba chỗ**, ưu tiên từ trên
xuống: `--max-length` → `max_length` trong `configs/models/<model>.yaml` → hằng số
`MAX_LENGTH` trong module model (chi tiết: [docs/04_experiments/02_phase3_input.md §4](docs/04_experiments/02_phase3_input.md)).



`--dataset cosmetics` là mặc định nên có thể bỏ qua. Tên dataset phải trùng tên
file `configs/datasets/<tên>.yaml`; gõ sai (ví dụ `consmetics`) thì lệnh dừng ngay
và in ra tên đúng, không đi tìm file kết quả.

Ba lệnh trên sinh ra kết quả nằm trong **một thư mục theo phiên bản**:

| Muốn xem gì | Mở file |
|-------------|---------|
| Báo cáo EDA | `data/reports/eda/versions/<mã>/report.html` |
| Báo cáo Pipeline | `data/reports/pipeline/versions/<mã>/report.html` |
| Dataset đã xử lý | `data/processed/versions/<mã>/processed_train.csv` |
| Độ dài input thật của từng model | `data/reports/model_input/versions/<mã>/token_stats.csv` |
| Chạy Qwen3 + điểm số (pha 4) | `data/reports/model_eval/versions/<mã>/predictions__<hậu tố>.csv` (kèm `metrics__*.csv` và `summary__*.json`) |
| Danh sách phiên bản | `data/processed/manifest.json` (hoặc `python build_report.py --list`) |

Mã phiên bản có dạng `cosmetics-v0.1.0-e6ffefe4`, được tính từ **nội dung
config + nội dung dữ liệu gốc**. Đổi config hoặc đổi dữ liệu ⇒ mã mới ⇒ **kết quả
cũ không bị ghi đè**. Báo cáo cho người đọc chỉ có **một** định dạng là HTML
(bản Markdown đã bỏ vì chỉ lặp lại số liệu mà không có biểu đồ): chạy
`build_report.py --dataset cosmetics` thì hai file `report.html` (EDA + Pipeline)
được mở luôn bằng trình duyệt mặc định — thêm `--no-open` nếu không muốn mở.

## 5. Cấu trúc thư mục

```
SentimentX/
├── data/
│   ├── raw/<tên>/      # dữ liệu GỐC, mỗi dataset một thư mục — không bao giờ sửa
│   ├── processed/
│   │   ├── manifest.json       # mục lục mọi phiên bản đã chạy
│   │   └── versions/<mã>/      # processed_train.csv, label_map.json, processing_log.json
│   └── reports/
│       ├── assets/             # plotly.min.js (để HTML mở được offline)
│       ├── eda/versions/<mã>/      # eda_result.json, 0X_*.json, *.csv, report.html
│       ├── pipeline/versions/<mã>/ # pipeline_result.json, report.html, ...
│       └── model_input/versions/<mã>/  # token_stats.csv (đo input thật, pha 3)
├── src/
│   ├── config.py       # hằng số kỹ thuật: đường dẫn, mã nhãn, ngưỡng
│   ├── dataset.py      # đọc cấu hình dataset, đưa dữ liệu về dạng chuẩn nội bộ
│   ├── versioning.py   # tính mã phiên bản + ghi mục lục
│   ├── prompts.py      # nạp + KIỂM TRA file prompt (configs/prompts/<tên>.txt)
│   ├── model_config.py # model dùng prompt nào (configs/models/<tên>.yaml)
│   ├── loaders/        # đọc csv / jsonl / parquet (thêm định dạng mới ở đây)
│   ├── registry.py     # đăng ký bước EDA / pipeline (điểm mở rộng)
│   ├── utils.py        # hàm dùng chung
│   ├── reporting/      # result.py (file kết quả), charts.py (Plotly), render.py + templates/
│   ├── eda/            # 5 module EDA
│   ├── pipeline/       # 7 bước pipeline
│   └── preprocessing/  # PHA 3: input riêng cho từng model, các bộ tách từ, đo input thật
├── configs/
│   ├── pipeline.yaml           # bật/tắt từng phép biến đổi (độc lập dataset)
│   ├── datasets/cosmetics.yaml # schema của dataset
│   ├── prompts/<tên>.txt       # NỘI DUNG prompt cho model sinh (sửa không cần đụng code)
│   └── models/<tên>.yaml       # model dùng prompt nào (mặc định: qwen.yaml)
├── scripts/            # cài đặt tái lập được: setup_java.ps1 (JDK 17), setup_vncorenlp.ps1
├── docs/               # tài liệu chi tiết: README.md (mục lục) + 01_dataset/, 02_eda/, 03_pipeline/, 04_experiments/
├── run_eda.py          # tính + ghi file kết quả (KHÔNG vẽ báo cáo)
├── run_pipeline.py     # tính + ghi dataset (KHÔNG vẽ báo cáo)
├── run_token_stats.py  # (pha 3) đo input thật của từng tokenizer → token_stats.csv
└── build_report.py     # đọc file kết quả → Plotly + Jinja2 → HTML (mở luôn)
```

## 6. Quy ước về báo cáo

- **File kết quả** (`*_result.json`, `*.csv`, `*.json`) → để máy đọc, tra cứu lại.
- **File cho người đọc** → HTML, sinh bởi `build_report.py` (một định dạng duy nhất).
- Báo cáo **chỉ trình bày số liệu và biểu đồ**. Mọi câu giải thích, diễn giải,
  khuyến nghị nằm trong `docs/`.
- Trong báo cáo, mỗi số liệu chỉ hiện **một lần** (bảng hoặc biểu đồ); số chi tiết
  đầy đủ nằm ở CSV/JSON trong **cùng thư mục phiên bản**, và báo cáo chỉ ghi một
  dòng "Thư mục số liệu chi tiết" ở đầu thay vì liệt kê từng file.
- Số trên biểu đồ hiện **đủ chữ số** (`16227`, không phải `16.2k`), chú thích màu
  nằm dưới biểu đồ; biểu đồ cột ngang sắp giảm dần từ trên xuống.
- Cách gọi tên: báo cáo dùng tiếng Việt ("khía cạnh" cho `aspect`) và đánh số bước
  pipeline là `Step 1…7`; các thuật ngữ kỹ thuật (`split`, `multi_head`, tên cột
  khía cạnh) giữ nguyên.
- Ô **văn bản** trong bảng in **nguyên văn như trong CSV**, kể cả xuống dòng (kể cả
  dòng người viết tự gõ bằng `•`): copy một ô dán vào ô tìm kiếm của CSV là thấy.
  Đừng gộp xuống dòng thành khoảng trắng khi hiển thị — làm vậy là mất khả năng tra
  ngược về dòng gốc.

Vì `build_report.py` đọc lại file kết quả, bạn có thể sửa giao diện báo cáo hoặc
đổi loại biểu đồ rồi vẽ lại **mà không phải chạy lại EDA / pipeline**.

## 7. Thêm một dataset mới

Không cần sửa code EDA, pipeline hay báo cáo — chỉ thêm dữ liệu và một file cấu hình:

```bash
# 1) Đặt dữ liệu gốc vào một thư mục riêng
mkdir data/raw/newdata
#    copy data_train.csv, data_val.csv, data_test.csv vào đó

# 2) Tạo cấu hình từ mẫu có sẵn rồi sửa: name, format, raw_dir,
#    text_column, aspects, labels, splits
copy configs\datasets\cosmetics.yaml configs\datasets\newdata.yaml

# 3) Chạy như bình thường
python run_eda.py --dataset newdata
python run_pipeline.py --dataset newdata
python build_report.py --dataset newdata
```

Trong cấu hình dataset có khoá `version`. **Tăng số này mỗi khi dữ liệu gốc thay
đổi**, để phiên bản mới được đặt tên rõ ràng (ví dụ `newdata-v0.2.0-1a2b3c4d`).

Hai trường hợp đặc biệt:

- Dữ liệu không phải CSV (JSONL, Parquet...): đổi khoá `format` trong YAML.
  Định dạng chưa có thì viết thêm một hàm `read(path)` trong `src/loaders/`.
- Bộ nhãn khác (ví dụ có `mixed`): khai báo trong `labels`; mã nhãn mới sẽ được
  cấp tự động, các nhãn quen thuộc giữ nguyên mã để model không phải đổi.

## 8. Tài liệu chi tiết

Bắt đầu từ **[docs/README.md](docs/README.md)** — có mục lục đầy đủ và lộ trình đọc.

| Nhóm tài liệu | Nội dung |
|----------|----------|
| [docs/01_dataset/](docs/01_dataset/) | Dữ liệu gốc: file, encoding, schema, ý nghĩa nhãn, cách thêm dataset mới |
| [docs/02_eda/](docs/02_eda/) | EDA: luồng + công tắc đang áp dụng, cách tính từng chỉ số, chi tiết 5 module, quy ước báo cáo |
| [docs/03_pipeline/](docs/03_pipeline/) | Pipeline: luồng 7 bước + cấu hình đang bật/tắt, chi tiết từng bước, cấu hình, bất biến, đầu ra |
| [docs/04_experiments/](docs/04_experiments/) | Kế hoạch thực nghiệm 3 model (ViTASA gác lại), bộ tách từ, đo input thật, chỉ số đánh giá, và **việc chưa làm** |

Mỗi nhóm có **một file luồng riêng** (`01_flow.md`) ghi luồng tổng quát, cấu hình
đang bật/tắt và đường dẫn tới file chi tiết từng bước.
