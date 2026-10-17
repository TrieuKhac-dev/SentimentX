> **ĐÂY LÀ KẾ HOẠCH HIỆN TẠI — CHƯA CHỐT TOÀN BỘ.**
> Chỉ **Phase 0 (P0 — web serving)** được chốt và triển khai trước. Các phase P1–P4 (baseline/hybrid/ML/test) sẽ được cập nhật sau; mọi thay đổi sẽ ghi vào tài liệu này hoặc file kế hoạch kế tiếp.

# P0 — Web Serving

Kế hoạch triển khai **Phase 0**: đóng gói hai model đã có thành một web service để người dùng gửi một
review tiếng Việt và nhận về dự đoán ABSA trên 7 aspect. Tài liệu này chỉ chốt **P0**; các phase sau
(P1–P4) chưa chốt, xem §10.

## 1. Mục tiêu P0

Serving đúng **2 model**:

### `cafebert_exp027` — encoder (LoRA)

| Mục | Giá trị |
| --- | --- |
| Adapter / checkpoint | `experiments/cafebert/lora/exp027/results/43e40f61/model/best` |
| Base model | `uitnlp/CafeBERT`, revision `af76fcf2...` |
| `max_length` | 256 |
| Segmenter | `none` (SentencePiece trên văn bản nguyên bản) |
| `dtype` | `float16` |

Đầu phân loại (`head.pt`) đọc từ `head_config.json` trong chính checkpoint: 7 aspect
`stayingpower, texture, smell, price, colour, shipping, packing`, 3 mã `[0, 1, 2]`.

### `qwen3_4b_exp009` — LLM (prompt)

| Mục | Giá trị |
| --- | --- |
| Checkpoint | `data/models/Qwen3-4B-Instruct-2507` |
| Lượng hoá | `4bit` (NF4), compute dtype `float16` |
| `max_length` | 2304 |
| `max_new_tokens` | 400 |
| Decoding | greedy |
| Prompt | `absa_cot_1shot_v1` |
| `prompt_sha` | `9b862ed0` |
| `examples_sha` | `5d530f7c` |
| `system_sha` | `ee1ed0e1` |

## 2. Kiến trúc registry

`configs/serving.yaml` là **nguồn sự thật** (single source of truth). Mỗi model là một block YAML có
khoá `enabled`:

- Chỉ model có `enabled: true` mới được nạp.
- Model `enabled: false` **không nạp** nhưng vẫn hiện ở `GET /models` với trạng thái `DISABLED`.
- Nạp theo kiểu **lazy load**: chỉ nạp khi có request đầu tiên.
- **Idle unload**: model không được dùng sau một khoảng thời gian (`idle_unload_s`) thì được giải phóng
  khỏi VRAM.
- `gpu_policy: sequential`: hai model không bao giờ chiếm GPU cùng lúc (VRAM 6 GB không đủ cho cả hai).
- Thêm model sau này chỉ cần thêm một YAML block — không sửa code registry.

## 3. API

| Method | Path | Mô tả |
| --- | --- | --- |
| `GET` | `/health` | Trạng thái service (`ready`/`starting`), GPU, model nào đã nạp |
| `GET` | `/models` | Danh sách model + trạng thái (`READY`/`LOADING`/`DISABLED`/`NOT_LOADED`) |
| `GET` | `/` | Giao diện web (UI tiếng Việt) |
| `POST` | `/predict` | Dự đoán; body có `model` (không bắt buộc), `text` (một chuỗi) hoặc `texts` (mảng) |
| `POST` | `/predict/{model_id}` | Dự đoán bằng đúng một model |
| `POST` | `/predict/hybrid` | Trả `501 Not Implemented` (dành cho P2) |

## 4. UI

Giao diện web (tiếng Việt) gồm:

- **textarea** để dán review cần dự đoán.
- **model selector** đổ từ `GET /models` (chỉ liệt kê model `enabled`).
- **bảng 7 aspect** (`stayingpower, texture, smell, price, colour, shipping, packing`), mỗi dòng: aspect, nhãn, badge màu theo `positive`/`negative`/`neutral`/không nhắc tới.
- **confidence bar** cho xác suất của từng aspect.
- **JSON raw** hiển thị payload gốc để debug.
- Toàn bộ nhãn/điều khiển bằng tiếng Việt, tài nguyên tĩnh phục vụ **offline** (không CDN).

## 5. File ownership / chống overwrite

Mỗi agent **chỉ sửa file thuộc nhóm của mình**; cần đụng file nhóm khác thì phối hợp qua board/PR,
không tự ý sửa — tránh hai agent ghi đè lên cùng một file.

| Nhóm | File | Agent |
| --- | --- | --- |
| Core — config/specs/schemas/errors | `configs/serving.yaml`, `serving/config.py`, `serving/specs.py`, `serving/schemas.py`, `serving/errors.py` | Agent core |
| Registry / base / loader | `serving/registry.py`, `serving/base.py`, `serving/loaders/*` | Agent registry |
| Encoder | `serving/encoders/*` | Agent encoder |
| LLM | `serving/llm/*` | Agent LLM |
| App / middleware | `serving/app.py` (+ middleware) | Agent API |
| UI | `serving/static/*`, `serving/templates/*` | Agent UI |
| Tests | `serving/tests/*` | Agent test |
| Docs | `docs/07_serving/*`, `serving/README.md` | Agent docs |

## 6. Điều kiện chấp nhận P0

- `python -m serving.app --check` pass (không nạp model, chỉ kiểm config + import).
- `GET /health` trả `ready`.
- `GET /models` liệt kê đủ **2 model** đã khai.
- `POST /predict` trả về đủ **7 aspect**.
- Bật/tắt model được bằng **config** (`enabled`) và bằng **CLI** (`--model`).
- Encoder p95 < **300 ms/review** (GPU, giá trị tham chiếu).
- LLM đạt ≥ **95% readable** trên 20 input mẫu.
- **Không** đọc test labels trong lúc serving.
- UI chạy **offline** (không phụ thuộc CDN).
- Tests pass: `python -m unittest discover -s serving/tests -v`.

## 7. Lệnh chạy (PowerShell, conda base)

```powershell
pip install -r requirements-serving.txt

python -m serving.app --check --model cafebert_exp027

python -m serving.app --model cafebert_exp027

python -m serving.app --model cafebert_exp027,qwen3_4b_exp009

python -m unittest discover -s serving/tests -v
```

## 8. Rủi ro

- **CafeBERT base chỉ có trong HF cache**: base `uitnlp/CafeBERT` không nằm trong repo (`local_files_only:
  true`); máy chưa từng chạy encoder sẽ không có cache, `--check` phải cảnh báo trước khi nạp.
- **Adapter `base_model_name_or_path: null`**: `adapter_config.json` không ghi base model, nên loader
  phải tự gán `uitnlp/CafeBERT` + revision `af76fcf2...` (không đoán từ adapter).
- **Qwen 4-bit ~2.5 GB**: VRAM 6 GB phải tính kỹ vùng đệm khi nạp thêm head/encoder.
- **Sequential vì 6 GB VRAM**: không nạp đồng thời hai model; idle unload là bắt buộc.
- **4-bit không deterministic**: kết quả Qwen có thể lệch giữa các lần chạy, không dùng để so số liệu.
- **Prompt truncation**: `max_length` 2304 đủ cho `absa_cot_1shot_v1`, nhưng input dài bất thường vẫn có
  thể bị cắt — không âm thầm cắt, phải báo trong response.
- **Không log raw text**: review thô không được ghi vào log (`log_text: false`).

## 9. Commit convention

Theo Conventional Commits, viết bằng **tiếng Anh**. Ví dụ:

- `docs(serving): record the P0 web serving plan`
- `feat(serving): add configurable model registry`
- `feat(serving): serve CafeBERT exp027`
- `feat(serving): serve Qwen3-4B exp009`
- `feat(serving): add P0 web interface`
- `test(serving): add registry and API tests`

## 10. Ghi chú cập nhật sau (chưa chốt, không nằm trong P0)

- **P1 — baseline**: chạy lại `cafebert_exp027` với `n ≥ 3` seed để có số liệu ổn định.
- **P2 — hybrid**: kết hợp encoder + LLM (điểm gắn `POST /predict/hybrid`).
- **P3 — ML**: đưa thêm model/đường huấn luyện ML nếu có.
- **P4 — test/report**: chạy bộ test cuối và viết báo cáo.

Các mục này **chưa chốt**; khi chốt sẽ ghi vào tài liệu này hoặc file kế hoạch kế tiếp, không đưa vào P0.