# P0 — Web Serving

Kế hoạch triển khai **Phase 0**: đóng gói hai model đã có thành một web service để người dùng gửi một
review tiếng Việt và nhận về dự đoán ABSA trên 7 aspect. P0 đang hoàn thiện; P1–P4 nằm ngoài phạm vi giai
đoạn cuối và không được mô tả như đã chốt.

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
| `POST` | `/models/{model_id}/load` | Yêu cầu nạp trước một model; trả `202` kèm trạng thái hiện tại |
| `GET` | `/` | Giao diện web v2 (mặc định tại `/`) |
| `POST` | `/predict` | Dự đoán; body có `model` (không bắt buộc), `text` (một chuỗi) hoặc `texts` (mảng) |
| `POST` | `/predict/{model_id}` | Dự đoán bằng đúng một model |
| `POST` | `/predict/hybrid` | Trả `501 Not Implemented` (dành cho P2) |

## 4. UI

Giao diện v2 phục vụ tại `/` từ `serving/static/v2/index.html` và `serving/static/v2/app.js`.

- **Chọn mô hình**: `select` đổ từ `GET /models`, chỉ lấy model `enabled: true`. Mặc định
  `cafebert_exp027`, fallback encoder đầu tiên.
- **Nạp mô hình**: tự động khi đổi model. UI gọi `POST /models/{id}/load` rồi poll `GET /models` mỗi
  500 ms, hiện "Đang nạp mô hình · N%" rồi "Sẵn sàng". Không có nút load riêng.
- **Ô nhập review**: `textarea` có đếm ký tự; giới hạn 4.000 ký tự cho encoder, 6.000 cho LLM. Nút
  "Phân tích đánh giá" và nút hủy khi đang chạy.
- **Mẫu gợi ý**: ba nút Tích cực / Tiêu cực / Hỗn hợp lấy từ `serving/static/v2/samples.js`; bấm lại để
  chuyển mẫu kế tiếp.
- **Bảng 7 aspect**: đúng thứ tự `stayingpower, texture, smell, price, colour, shipping, packing` với
  nhãn tiếng Việt (Độ bền, Chất son, Mùi hương, Giá cả, Màu sắc, Vận chuyển, Đóng gói). Mỗi dòng có pill
  màu theo Tích cực / Tiêu cực / Trung lập / Không nhắc tới / Không đọc được.
- **Cột theo loại model**: encoder hiện `Độ tin cậy` (phần trăm); LLM hiện `Đoạn trích` và `Lý do mô
  hình đưa ra`, có nút "Xem thêm" khi nội dung bị cắt.
- **Chế độ so sánh**: chọn hai model khác nhau, có nút đổi chỗ; bảng hai bên theo từng aspect, gắn nhãn
  "Khác" khi nhãn lệch nhau.
- **Không có JSON raw**: v2 không hiển thị payload gốc; lỗi và tiến trình hiện qua banner trạng thái.
- Tài nguyên tĩnh phục vụ **offline** (không CDN).

## 5. File ownership / chống overwrite

Mỗi agent **chỉ sửa file thuộc nhóm của mình**; cần đụng file nhóm khác thì phối hợp qua board/PR,
không tự ý sửa — tránh hai agent ghi đè lên cùng một file.

| Nhóm | File | Agent |
| --- | --- | --- |
| Core — config/specs/schemas/errors | `configs/serving.yaml`, `serving/config.py`, `serving/specs.py`, `serving/schemas.py`, `serving/errors.py` | Agent core |
| Registry / base / loader | `serving/registry.py`, `serving/inference/base.py`, `serving/inference/loader.py` | Agent registry |
| Encoder | `serving/inference/encoder.py` | Agent encoder |
| LLM | `serving/inference/llm.py` | Agent LLM |
| App / middleware | `serving/app.py`, `serving/middleware.py`, `serving/load_coordinator.py`, `serving/cache.py` | Agent API |
| UI | `serving/static/v2/*`, `serving/static/*` (asset cũ không còn phục vụ) | Agent UI |
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

Hai chỉ tiêu p95 encoder và LLM ≥ 95% readable là mục tiêu, chưa đo trên GPU thật.

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

## 10. Ghi chú ngoài phạm vi P0 (chưa chốt)

- **P1 — baseline**: chạy lại `cafebert_exp027` với `n ≥ 3` seed để có số liệu ổn định.
- **P2 — hybrid**: kết hợp encoder + LLM (điểm gắn `POST /predict/hybrid`).
- **P3 — ML**: đưa thêm model/đường huấn luyện ML nếu có.
- **P4 — test/report**: chạy bộ test cuối và viết báo cáo.

P1–P4 nằm ngoài phạm vi giai đoạn cuối; tài liệu này không cam kết cập nhật chúng.