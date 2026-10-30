# serving — Web serving cho SentimentX

Đóng gói các model ABSA đã huấn luyện thành một web service (FastAPI) để dự đoán 7 aspect của một
review son mỹ phẩm tiếng Việt.

## Mục đích

- Cung cấp `POST /predict` nhận một hoặc nhiều review, trả nhãn + xác suất cho từng aspect.
- Giao diện web tại `GET /`, mặc định là bản v2.

## Model registry / config toggle

`configs/serving.yaml` là nguồn sự thật. Mỗi model có khoá `enabled`:

```yaml
models:
  cafebert_exp027:
    enabled: true
    kind: encoder
    # ...
  qwen3_4b_exp009:
    enabled: false
    kind: llm
    # ...
```

- Chỉ model `enabled: true` được nạp; `enabled: false` hiện ở `/models` với trạng thái `DISABLED`.
- Nạp **lazy** khi có request đầu tiên; **idle unload** khi không dùng sau `idle_unload_s` giây.
- `gpu_policy: sequential`: hai model chạy tuần tự trên cùng một GPU 6 GB.

## Hai model hiện có

| id | Loại | Nguồn |
| --- | --- | --- |
| `cafebert_exp027` | encoder (LoRA) | `experiments/cafebert/lora/exp027/results/43e40f61/model/best` + base `uitnlp/CafeBERT` |
| `qwen3_4b_exp009` | LLM (prompt) | `data/models/Qwen3-4B-Instruct-2507` (4-bit), prompt `absa_cot_1shot_v1` |

## Bật / tắt model

- Qua config: đổi `enabled` trong `configs/serving.yaml` rồi khởi động lại.
- Qua CLI: `python -m serving.app --model cafebert_exp027` chỉ nạp model được liệt kê;
  `--model cafebert_exp027,qwen3_4b_exp009` nạp cả hai.

## Thêm model sau này

Thêm một YAML block vào `configs/serving.yaml` (id, `kind`, `load`, `runtime`). Không sửa code registry —
runtime được chọn theo `kind` trong block.

## File tree

```
serving/
├── __init__.py         # phiên bản gói
├── config.py           # entry point config: re-export `load_settings`
├── specs.py            # ModelSpec, Settings, đọc + validate configs/serving.yaml
├── schemas.py          # Pydantic request/response
├── errors.py           # lỗi chuẩn (APIError + lỗi con)
├── cache.py            # TTL cache trong bộ nhớ (mặc định tắt)
├── load_coordinator.py # điều phối nạp model nền (latest-wins)
├── middleware.py       # request-id, log, envelope lỗi
├── app.py              # entrypoint duy nhất: FastAPI app + route
├── registry.py         # registry: lazy load, idle unload, sequential
├── inference/          # runtime suy luận
│   ├── base.py         # interface chung
│   ├── encoder.py      # CafeBERT + LoRA
│   ├── llm.py          # Qwen3-4B 4-bit
│   ├── loader.py       # chọn runtime theo `kind`
│   └── fake.py         # runtime giả cho test
├── static/
│   └── v2/             # UI v2, phục vụ tại `/`
│       ├── index.html
│       ├── app.js
│       ├── style.css
│       └── samples.js
├── tests/              # unittest cho registry + API
└── README.md
```

## API examples

`GET /health`:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/health
```

`GET /models`:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/models
```

`POST /predict` (curl):

```bash
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" -d '{"text": "Son lên màu đẹp nhưng thâm nhanh"}'
```

`POST /predict` (PowerShell):

```powershell
$body = @{ text = "Son lên màu đẹp nhưng thâm nhanh" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/predict -Body $body -ContentType "application/json"
```

`POST /predict/{model_id}`:

```powershell
$body = @{ texts = @("Son đẹp, ship hơi lâu") } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/predict/cafebert_exp027 -Body $body -ContentType "application/json"
```

`POST /predict/hybrid` trả `501 Not Implemented` (dành cho P2).

## Memory / latency

- CafeBERT (encoder): base fp16 ~550 MB + adapter/head nhỏ; p95 mục tiêu < 300 ms/review (GPU).
- Qwen3-4B (LLM): 4-bit ~2.5 GB; sinh tới 400 token nên chậm hơn nhiều so với encoder.
- VRAM 6 GB → hai model chạy **tuần tự** (`gpu_policy: sequential`), idle unload để nhả VRAM.

## Troubleshooting

- **Thiếu CafeBERT base (HF cache)**: base `uitnlp/CafeBERT` không nằm trong repo (`local_files_only:
  true`). Máy chưa chạy encoder sẽ báo thiếu cache; chạy thử một lượt encoder hoặc tải base về trước.
- **OOM**: Qwen 4-bit ~2.5 GB, nhưng cộng thêm head/encoder + buffer dễ vượt 6 GB. Tắt model kia, giảm
  `max_batch`, hoặc kiểm tra `gpu_policy` đang là `sequential`.
- **4-bit**: lượng hoá 4-bit không deterministic; nếu cần tái lập thì dùng greedy (`do_sample: false`) và
  cố định `seed` (kết quả vẫn có thể lệch nhẹ giữa các lần chạy).

## Trạng thái

P0 đang triển khai. Các số về memory/latency và "tests pass" ở trên là **mục tiêu P0**, chưa phải kết
quả đã đo; không tuyên bố test pass cho tới khi triển khai xong.