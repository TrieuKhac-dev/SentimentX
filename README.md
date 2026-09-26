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
RAW DATA (data/raw/<tên>/<phiên bản>/)
    |
    +--> EDA            "Dữ liệu đang thế nào?"      (src/eda/)
    |
    +--> DATA PIPELINE  "Ta xử lý thế nào?"          (src/pipeline/)
             |
             v
    dataset có phiên bản: data/processed/<mã>/
        train.csv, val.csv, test.csv, label_map.json, processing_log.json,
        eval_lock.json, pipeline/ (báo cáo), eda/ (số đo)
             |
             v
    THÍ NGHIỆM (experiments/<model_id>/<method>/<expNNN>/)
        approach: prompt  -> Qwen3-4B / Qwen3-0.6B: gửi câu chỉ dẫn rồi đọc trả lời
        approach: encoder -> PhoBERT / ViSoBERT: học LoRA rồi suy luận
             |
             v
    KẾT QUẢ: experiments/**/results/<hash8>/  (metrics.json, run.log, ...)
             |
             v
    BÁO CÁO TỔNG HỢP: data/reports/  (dataset_registry, experiment_registry,
    model_input, metrics_matrix)

(ViTASA đang gác - xem docs/04_experiments/04_backlog.md)
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

Ba file requirements, mỗi nơi một việc: `requirements.txt` cho máy cá nhân, `requirements-colab.txt`
cho Colab (**KHÔNG** cài lại `torch`: Colab đã có bản khớp CUDA của nó) và `requirements-ci.txt` cho
CI (rất ngắn, vì CI không chạy model và không đọc dữ liệu). Lý do từng dòng và cách chạy trên Colab:
`docs/00_workflow/07_colab.md`.

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
`dùng được = có`. Trên Colab thì **không phải làm gì**: ô bootstrap của notebook PhoBERT tự
cài `default-jdk` + `py-vncorenlp`, đặt `JAVA_HOME`, và model VnCoreNLP đã nằm trong
`data/models/vncorenlp/` của gói bàn giao — thí nghiệm PhoBERT khai đường dẫn đó ở
`requires_extra` nên preflight chặn trước khi nạp model nếu thiếu
([docs/00_workflow/07_colab.md §2](docs/00_workflow/07_colab.md)).
Máy chưa cài được Java mà vẫn muốn chạy ngay thì dùng
`--segmenter pyvi` (`pip install pyvi`), nhưng phải ghi rõ đã dùng bộ nào vì số liệu
của hai bộ không so sánh ngang nhau được. Chi tiết (vì sao cài bằng ZIP thay vì `winget`,
vì sao không dùng `py_vncorenlp.download_model`): xem
[docs/04_experiments/02_model_input.md §5](docs/04_experiments/02_model_input.md).


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
python run_token_stats.py --prompt absa_direct_v1     # đo với một prompt khác
python run_token_stats.py --segmenter pyvi          # đo với một bộ tách từ khác
python run_token_stats.py --max-length qwen=1280    # đo với ngưỡng cắt khác (thử nhanh)

# 6) (Pha 3) Kiểm file ví dụ few-shot: cấu trúc, nhãn, và RÒ RỈ với val/test
python run_check_examples.py

# 7) (Pha 4) Chạy thí nghiệm Qwen3 bằng chỉ dẫn (prompt một lượt / CoT) rồi chấm điểm
#    Mở notebook của thí nghiệm và bấm Run all - đó là đường chạy chính, tự kéo đúng commit
#    đã ghim rồi kiểm trước. (Xem notebooks ở experiments/qwen3-4b-instruct-2507/…)

# 8) Test tự động (không cần GPU, không cần model)
python -m unittest discover -s tests
```

Mọi kết quả đều thuộc một thí nghiệm và nằm ở
`experiments/<model>/<method>/<expNNN>/results/<hash8>/`, trong đó `<hash8>` là **mã băm danh tính**
của lượt chạy (nội dung cấu hình + prompt + bộ ví dụ + mã phiên bản dữ liệu + **commit đã ghim**).
Tên thư mục KHÔNG mô tả gì để nó **giống nhau trên Colab và trên máy cá nhân** — copy kết quả từ
Drive về repo là copy thẳng; muốn biết thư mục đó là gì thì mở `run_meta.json` (khối `run`) hoặc
`python scripts/collect_reports.py` (bảng `experiment_registry` có `hash`, `repo_sha`, `prompt`,
`split`, `n`, `quant`, `dtype`, điểm).

Một lượt chạy luôn chạy trên tập do **config của thí nghiệm** quyết định (`data.roles.eval`, tức
`val` cho tới khi chốt); chọn theo test là tự lừa mình. Cách sinh cũng theo config
(`evaluation.decoding`): mặc định **greedy** (tái lập được), muốn dùng cấu hình khuyến nghị của
model card thì khai `sample` (nhiệt độ 0.7, top_p 0.8, top_k 20 — và `seed` sẽ được ghi lại).
Số mẫu khai ở `n` trong config thí nghiệm; `n` khác nhau cho ra **hash khác** nên kết quả tập con
**không bao giờ lẫn** với kết quả toàn tập.

`--prompt`, `--segmenter` và `--max-length` ghi ra **file CSV riêng**
(`token_stats__prompt-X.csv`, `token_stats__seg-Y.csv`, `...__maxlen-qwen-1280.csv`), không
ghi đè số liệu của cấu hình mặc định — nhờ vậy so hai thí nghiệm vẫn còn nguyên cả hai bên.
Prompt nào dùng khối ví dụ few-shot (`{examples}`) thì tên file có thêm **`ex-<sha4>`** — mã
của BỘ VÍ DỤ, kể cả khi chạy bằng cấu hình dự án: hai bộ ví dụ khác nhau (một ví dụ vs hai
ví dụ) là hai thí nghiệm, mà `prompt_sha` của chúng lại giống nhau nên không có mã đó thì
chúng sẽ ghi đè lên nhau. Xem `python run_token_stats.py --list-prompts` để biết prompt nào
đang có bao nhiêu ví dụ và đường dẫn file ví dụ.
Đổi prompt chỉ cần thêm một file `configs/prompts/<tên>.txt`; prompt mà một thí nghiệm dùng thì
ghi ở config của chính thí nghiệm đó, không ghi ở `configs/models/`. Ngưỡng cắt thì đổi được ở
**cả hai chỗ**, ưu tiên từ trên xuống: `--max-length` → `preprocess.max_length` trong
`configs/models/<model_id>.yaml` (chi tiết: [docs/04_experiments/02_model_input.md](docs/04_experiments/02_model_input.md)).



`--dataset cosmetics` là mặc định nên có thể bỏ qua, nhưng **`--version` thì bắt buộc**: mỗi phiên bản
dataset cho ra một bộ dữ liệu khác nhau. Tên dataset trùng tên thư mục `configs/datasets/<tên>/`;
gõ sai (ví dụ `consmetics`) thì lệnh dừng ngay và in ra tên đúng, không đi tìm file kết quả.

Ba lệnh trên sinh ra kết quả nằm trong **một thư mục theo mã phiên bản**:

| Muốn xem gì | Mở file |
|-------------|---------|
| Báo cáo EDA | `data/processed/<mã>/eda/report.html` (đo trên dữ liệu gốc: `data/raw/<tên>/<phiên bản>/eda/`) |
| Báo cáo Pipeline | `data/processed/<mã>/pipeline/report.html` |
| Dataset đã xử lý | `data/processed/<mã>/train.csv` (kèm `val.csv`, `test.csv`, `label_map.json`) |
| Độ dài input thật của từng model | `data/reports/model_input/<mã>/token_stats.csv` |
| Chạy một thí nghiệm + điểm số | `experiments/<model>/<method>/<expNNN>/results/<hash8>/` (gồm `run.log`, `run_meta.json`, `metrics.json`, `metrics.csv`, `mispredictions.csv`) |
| Bảng tổng hợp cả nhóm | `data/reports/{dataset_registry,experiment_registry,model_input,metrics_matrix}/` - sinh bằng `python scripts/collect_reports.py` |

Mã phiên bản có dạng `cosmetics-ds0.1.0-pl0.1.0-srccosmetics@0.1.0-e0ccc484`: đọc ra được phiên bản
dataset, phiên bản pipeline, nguồn, và 8 ký tự băm của **nội dung config + nội dung dữ liệu gốc**.
Đổi config hoặc đổi dữ liệu ⇒ mã mới ⇒ **kết quả cũ không bị ghi đè**. Phép băm bỏ qua kiểu xuống
dòng (CRLF/LF), nên cùng một bộ dữ liệu cho ra cùng một mã trên Windows và trên Colab.
`build_report.py` vẽ HTML cho EDA và pipeline (mở luôn bằng trình duyệt, thêm `--no-open` nếu không
muốn); bảng tổng hợp thì có cả `csv` để máy đọc, `html` để người đọc và `md` chứa sơ đồ Mermaid.

## 5. Cấu trúc thư mục

```
SentimentX/
├── data/                       # KHÔNG vào git, trừ metadata và bảng chi tiết (luật 20)
│   ├── raw/<tên>/<phiên bản>/  # dữ liệu GỐC + raw_meta.yaml + eda/ (kết quả đo, KHÔNG sửa dữ liệu)
│   ├── processed/<mã>/         # dữ liệu đã xử lý: train.csv, val.csv, test.csv, label_map.json,
│   │   │                       # processing_log.json (dấu vết của lần chạy pipeline)
│   │   ├── eda/                # kết quả EDA đo trên dữ liệu ĐÃ xử lý
│   │   └── pipeline/           # bảng chi tiết từng bước + report.html
│   ├── models/                 # model tải về (bỏ qua nội dung, giữ README)
│   ├── reports/                # bảng tổng hợp sinh tự động: 4 nhóm, xem scripts/collect_reports.py
│   └── reference_publication/  # số liệu công bố tham chiếu, để so kết quả
├── configs/
│   ├── paths.yaml              # NGUỒN DUY NHẤT của đường dẫn và mẫu tên file
│   ├── dagshub.yaml            # hạ tầng MLflow/DagsHub (KHÔNG chứa token)
│   ├── datasets/<tên>/<phiên bản>.yaml    # schema dataset; file phiên bản là BẤT BIẾN
│   ├── pipeline/<phiên bản>.yaml          # bật/tắt từng phép biến đổi (độc lập dataset)
│   ├── models/<tên>.yaml                  # model chạy thế nào: dtype, lượng hoá, batch, max_length
│   ├── experiments/{repo,task,evaluation,training,tracking}.yaml   # dùng chung cho mọi thí nghiệm
│   └── prompts/<tên>.txt + prompts/examples/<tên>.txt              # nội dung prompt và ví dụ
├── experiments/<model>/<method>/<expNNN>/  # ĐỊNH NGHĨA thí nghiệm: config.yaml, notebook.ipynb,
│                                           # README.md; kết quả chạy ở results/<hash8>/ (mã băm
│                                           # danh tính: cấu hình + prompt + ví dụ + dữ liệu + commit)
├── templates/                  # bản mẫu để tạo thí nghiệm mới (scripts/new_experiment.py dùng)
├── src/
│   ├── paths.py                # API đường dẫn, đọc configs/paths.yaml
│   ├── runtime.py              # máy đang chạy (colab/local), nạp biến môi trường, tìm thư mục Drive
│   ├── repo.py                 # kéo ĐÚNG commit đã ghim rồi kiểm lại
│   ├── notebooks.py            # đọc/ghi notebook và ô GHIM (dùng chung với scripts/pin.py)
│   ├── experiments.py          # hợp nhất các tầng config + dấu vân tay cấu hình
│   ├── model_config.py         # đọc config model
│   ├── dataset.py              # đọc config dataset, đưa dữ liệu về dạng chuẩn nội bộ
│   ├── versioning.py           # mã phiên bản dữ liệu, guard bất biến, đường dẫn theo phiên bản
│   ├── preflight.py            # kiểm TRƯỚC khi chạy: dữ liệu, GPU, quyền ghi, NEW hay RESUME
│   ├── experiment_run.py       # vòng chạy thí nghiệm: plan() không cần GPU -> run()
│   ├── resume.py               # dừng hay đi tiếp theo các khối predictions/part_*.jsonl
│   ├── reports.py              # sinh bảng tổng hợp (4 nhóm)
│   ├── checks.py               # các kiểm tra cấu trúc cho CI
│   ├── runlog.py               # ghi run.log theo dòng, không đệm
│   ├── prompts.py              # nạp + KIỂM TRA file prompt
│   ├── labels/                 # bảng mã nhãn
│   ├── loaders/                # đọc csv / jsonl / parquet (thêm định dạng mới ở đây)
│   ├── registry.py             # đăng ký bước EDA / pipeline (điểm mở rộng)
│   ├── reporting/              # result.py (file kết quả), charts.py (Plotly), render.py + templates/
│   ├── eda/                    # 5 module EDA
│   ├── pipeline/               # 7 bước pipeline
│   ├── evaluation/             # chấm điểm: records, metrics, scorers/ (5 cách chấm)
│   ├── tracking/               # ghi nhận: mlflow/DagsHub, local_json, run_meta.json
│   └── preprocessing/          # PHA 3: input riêng cho từng model, bộ tách từ, đo input thật
├── configs/
│   ├── pipeline.yaml           # bật/tắt từng phép biến đổi (độc lập dataset)
│   ├── datasets/cosmetics.yaml # schema của dataset
│   ├── prompts/<tên>.txt       # NỘI DUNG prompt cho model sinh (sửa không cần đụng code)
│   └── models/<tên>.yaml       # model dùng prompt nào (mặc định: qwen.yaml)
├── scripts/            # cửa vào dòng lệnh: pin.py (ghim commit vào notebook), new_experiment.py
│                       # (tạo expNNN), collect_reports.py (bảng tổng hợp), ci_checks.py (kiểm tra
│                       # cấu trúc), setup_java.ps1 + setup_vncorenlp.ps1 (cài đặt tái lập được)
├── docs/               # tài liệu: README.md (mục lục) + 00_workflow/, 01_dataset/, 02_eda/,
│                       # 03_pipeline/, 04_experiments/, 05_config/, 06_plan/
├── tests/              # test chạy bằng `unittest`, không cần GPU
├── run_eda.py          # tính + ghi file kết quả EDA (KHÔNG vẽ báo cáo)
├── run_pipeline.py     # tính + ghi dataset (KHÔNG vẽ báo cáo) - BẮT BUỘC ghi rõ --version
├── run_token_stats.py  # (pha 3) đo input thật của từng tokenizer -> token_stats.csv
├── build_report.py     # đọc file kết quả -> Plotly + Jinja2 -> HTML (mở luôn)
├── requirements.txt        # máy cá nhân (torch cài riêng, xem §3)
├── requirements-ci.txt     # CI: rất ngắn, vì CI không chạy model và không đọc dữ liệu
└── requirements-colab.txt  # Colab: KHÔNG ghim torch (Colab đã có bản khớp CUDA)
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

Không cần sửa code EDA, pipeline hay báo cáo — chỉ thêm dữ liệu và một file cấu hình **phiên bản**:

```bash
# 1) Đặt dữ liệu gốc vào thư mục riêng, kèm raw_meta.yaml (ghi nguồn, ngày nhận, cách tải)
mkdir data/raw/newdata/v0.1.0
#    copy data_train.csv, data_val.csv, data_test.csv, full_data.csv vào đó

# 2) Tạo cấu hình từ mẫu rồi sửa: name, version, format, splits, schema
mkdir configs/datasets/newdata
copy configs\datasets\cosmetics\v0.1.0.yaml configs\datasets\newdata\v0.1.0.yaml

# 3) Chạy như bình thường - mỗi bước phải ghi rõ phiên bản
python run_eda.py --dataset newdata --raw-version v0.1.0
python run_pipeline.py --dataset newdata --version v0.1.0
python build_report.py --dataset newdata --version <mã in ra ở bước 2>
python scripts/collect_reports.py
```

Trong cấu hình dataset có khoá `version`. **Tạo FILE MỚI khi dữ liệu gốc thay đổi** (ví dụ
`v0.2.0.yaml`), **không sửa file đã dùng**: nội dung file phiên bản đi vào mã phiên bản dữ liệu, nên
sửa tại chỗ là hai định nghĩa khác nhau mang cùng một nhãn và kết quả cũ không còn tra được. Guard
(`versioning.guard_versions`) sẽ chặn nếu bạn sửa file phiên bản đã dùng - chi tiết ở
`docs/06_plan/P2_versioning.md`.

Hai trường hợp đặc biệt:

- Dữ liệu không phải CSV (JSONL, Parquet...): đổi khoá `format` trong YAML.
  Định dạng chưa có thì viết thêm một hàm `read(path)` trong `src/loaders/`.
- Bộ nhãn khác (ví dụ có `mixed`): khai báo trong `labels`; mã nhãn mới sẽ được
  cấp tự động, các nhãn quen thuộc giữ nguyên mã để model không phải đổi.

## 8. Tài liệu chi tiết

Bắt đầu từ **[docs/README.md](docs/README.md)** — có mục lục đầy đủ và lộ trình đọc.

| Nhóm tài liệu | Nội dung |
|----------|----------|
| [docs/00_workflow/](docs/00_workflow/) | Luồng làm việc, luật bắt buộc, CI, thuật ngữ, quy ước commit/code, **cách chạy trên Colab** |
| [docs/01_dataset/](docs/01_dataset/) | Dữ liệu gốc: file, encoding, schema, ý nghĩa nhãn, cách thêm dataset mới |
| [docs/02_eda/](docs/02_eda/) | EDA: luồng + công tắc đang áp dụng, cách tính từng chỉ số, chi tiết 5 module, quy ước báo cáo |
| [docs/03_pipeline/](docs/03_pipeline/) | Pipeline: luồng 7 bước + cấu hình đang bật/tắt, chi tiết từng bước, cấu hình, bất biến, đầu ra |
| [docs/04_experiments/](docs/04_experiments/) | Kế hoạch thực nghiệm 3 model (ViTASA gác lại), bộ tách từ, đo input thật, chỉ số đánh giá, và **việc chưa làm** |
| [docs/05_config/](docs/05_config/) | Từng file config (đường dẫn, dataset, model, pipeline, thí nghiệm, biến môi trường) |
| [docs/06_plan/](docs/06_plan/) | Kế hoạch triển khai P0..P7, điều kiện hoàn thành từng giai đoạn, và bảng toàn bộ commit |

Mỗi nhóm có **một file luồng riêng** (`01_flow.md`) ghi luồng tổng quát, cấu hình
đang bật/tắt và đường dẫn tới file chi tiết từng bước.

## 9. Chạy một thí nghiệm và giao cho giảng viên

```bash
# 1) Tạo thí nghiệm mới (tự chọn expNNN kế tiếp, từ chối nếu nhánh chưa có origin/experiment)
python scripts/new_experiment.py --model qwen3-4b-instruct-2507 --method prompt-cot --title "CoT 1 shot"

# 2) Viết config.yaml của thí nghiệm, rồi chạy thử ở MÁY CÁ NHÂN: mở notebook.ipynb và bấm Run all

# 3) Ghim bản code vào notebook (phải push lên nhánh experiment trước)
git push origin experiment
python scripts/pin.py qwen3-4b-instruct-2507/prompt-cot/exp002
```

Giao cho giảng viên: dựng **thư mục Drive** gồm dữ liệu (gốc + đã xử lý), file notebook và
`.env.colab` nếu có token, rồi gửi hướng dẫn. Người nhận chỉ việc **mở notebook, bấm Run all và bấm
Allow** khi Colab hỏi quyền truy cập Drive - ô bootstrap tự mount Drive, tự tìm thư mục nhóm (bằng
file đánh dấu, không cần biết tên), tự đặt gốc dữ liệu/kết quả và tự cài gói còn thiếu. Chi tiết:
`docs/00_workflow/07_colab.md`.

Xem kết quả: DagsHub xem ngay (không phải copy gì); muốn đưa vào git thì copy **phần nhẹ** từ Drive về
(`run.log`, `run_meta.json`, `metrics.json`, `metrics.csv`, `mispredictions.csv`) rồi chạy
`python scripts/collect_reports.py`. Toàn bộ vòng bàn giao: `docs/06_plan/P7_rerun.md`.
