# Ngưỡng token đầu vào và giới hạn của model

> Đọc file này khi: trình bày ngưỡng cắt token đầu vào (`max_length`) và giới hạn của model.
> Liên quan: `presentations/model_preprocessing.md`, `docs/04_experiments/02_model_input.md`

Prompt gửi cho model sinh (Qwen3) gồm **system + review + ví dụ few-shot**, nên độ dài input phải đo bằng
chính tokenizer của model. Mỗi model có một **trần kiến trúc** riêng; dự án **cắt** prompt ở `max_length`
và **chặn** mọi ngưỡng vượt trần, nên input không bao giờ lớn hơn khả năng nhận của model.

## 1. Trần model so với ngưỡng cắt đang dùng

Trần đọc từ `max_position_embeddings` trong config của model.

| Model                  | Trần kiến trúc (`max_position_embeddings`) | `max_length` dự án | Dư      |
| ---------------------- | ------------------------------------------ | ------------------ | ------- |
| PhoBERT                | 258                                        | 256                | 2       |
| ViSoBERT               | 514                                        | 256                | 258     |
| Qwen3-4B-Instruct-2507 | 262.144                                    | 2304               | 259.840 |
| Qwen3-0.6B             | 40.960                                     | 2304               | 38.656  |

> **Nguồn trần kiến trúc:** đọc từ `config.json` của model - `data/models/Qwen3-4B-Instruct-2507/config.json` cho `max_position_embeddings = 262.144`; `data/models/Qwen3-0.6B/config.json` cho `40.960`. Với **Qwen3-0.6B**: giới hạn **cứng** của kiến trúc là **40.960**, còn **ngữ cảnh native được huấn luyện** là **32.768** (phạm vi đảm bảo chất lượng). Dự án chặn theo giá trị của `config.json` (`40.960`).

## 2. Đo và cắt là hai việc tách rời

```mermaid
flowchart LR
    P["📥 prompt<br/>system + review + ví dụ"]:::in
    M["📏 ĐO (KHÔNG cắt)<br/>tokenizer của model"]:::step
    C["✂️ CẮT ở max_length<br/>truncation = True"]:::step
    MOD["🧠 model"]:::model
    R["📊 % review vượt max_length"]:::io

    P --> M --> R
    P --> C --> MOD

    classDef in    fill:#E0A93B33,stroke:#E0A93B,stroke-width:1.5px,rx:12,ry:12,padding:12px;
    classDef step  fill:#5FA36B33,stroke:#5FA36B,stroke-width:1.5px,rx:12,ry:12,padding:12px;
    classDef model fill:#9B6FD133,stroke:#9B6FD1,stroke-width:1.5px,rx:12,ry:12,padding:12px;
    classDef io    fill:#5B7FBD33,stroke:#5B7FBD,stroke-width:1.5px,rx:14,ry:14,padding:18px;
```

- **ĐO** bằng chính tokenizer của model và **không** cắt → biết độ dài input THẬT và bao nhiêu mẫu vượt ngưỡng.
- **DÙNG** truyền `truncation=True, max_length=<ngưỡng của model>` → **toàn bộ prompt** (một chuỗi) bị **cắt còn tối đa `max_length`** token; prompt **ngắn hơn** ngưỡng thì nhận **trọn vẹn** (không mất gì). Ngưỡng từng model: xem bảng §1.
- Nơi ĐO (`encode()`) và nơi DÙNG (`build_inputs()`) đọc **cùng một** `limit()` từ
  `configs/models/<model_id>.yaml`, nên không thể lệch nhau.
- `max_length` **không được vượt trần model**.
- Phần **đầu ra** tách riêng: `max_new_tokens = 400` (mặc định).

## 3. Qwen3: token/review thật theo bộ prompt (split `train`, 12.268 review của bộ `v0.2.0`)

Số liệu được đo cho **cả 3 split** (`train`/`val`/`test`) của mọi model; bảng dưới trích `train`, số đầy
đủ ở các file `token_stats__*.csv`.

| Prompt                 | ví dụ | token/review TB | p50   | p95   | p99   | max       | % > 2304 |
| ---------------------- | ----- | --------------- | ----- | ----- | ----- | --------- | -------- |
| `absa_one_turn_v1`     | 0     | 257,50          | 252   | 296   | 326   | 502       | 0,00     |
| `absa_direct_v1`       | 0     | 229,50          | 224   | 268   | 298   | 474       | 0,00     |
| `absa_cot_zeroshot_v1` | 0     | 372,50          | 367   | 411   | 441   | 617       | 0,00     |
| `absa_cot_1shot_v1`    | 1     | 721,50          | 716   | 760   | 790   | 966       | 0,00     |
| `absa_cot_v1`          | 2     | 990,50          | 985   | 1.029 | 1.059 | 1.235     | 0,00     |
| `absa_cot_5shot_v1`    | 5     | 1.877,50        | 1.872 | 1.916 | 1.946 | **2.122** | 0,00     |

- Mức **5 ví dụ** (mức công bố so) dài nhất **2.122 token** ở train, nên ngưỡng **2304** giữ **0% bị cắt**;
  ngưỡng 1280 trước đây cắt mất phần đuôi của **100%** review ở cả ba split.
- **Nếu** một prompt vượt ngưỡng thì **mất phần cuối** - đúng chỗ đặt yêu cầu định dạng đầu ra và khuôn JSON, nên mẫu đó **mất luôn hướng dẫn định dạng**.
- Một lượt CoT: input **≤ 2304** + output **≤ 400** = **≤ 2704** token, cách xa trần 262.144 của model.

### Vì sao 2.304 chứ không sát 2.122, và vì sao không dùng trần model

- `max` của mỗi split: train **2.122**, val **2.029**, test **1.993**. Muốn 0% bị cắt thì ngưỡng phải
  ≥ max của MỌI split, và 2.304 chừa biên 182 token (8,58%) cho lần sửa prompt/ví dụ sau này.
- `max_length` là **TRẦN CẮT**, không phải độ dài thật: không mẫu nào vượt trần thì padding theo lô
  không đổi, nên **nâng trần không tốn thêm tính toán**.
- Không đặt trần bằng trần model (262.144): trần cắt còn để **chặn ca xấu** vì một mẫu bất thường đủ
  làm phình cả lô; và với Qwen3-0.6B thì 262.144 **vượt cả trần** 40.960 của model đó.

## 4. Vì sao 4 ngưỡng khác nhau

| Model      | Input gồm gì            | `max_length` | Căn cứ                                                                                   |
| ---------- | ----------------------- | ------------ | ---------------------------------------------------------------------------------------- |
| PhoBERT    | CHỈ review (đã tách từ) | 256          | ngưỡng chính chủ; trần 258; vài review dài 301 (vượt cả trần) nên **0,02% train bị cắt** |
| ViSoBERT   | CHỈ review (nguyên bản) | 256          | review dài nhất 229 (**0% cắt**); bằng PhoBERT để cùng ngân sách input                   |
| Qwen3-4B   | prompt + review + ví dụ | 2304         | mức 5 ví dụ dài nhất 2.122 → **0% cắt**                                                  |
| Qwen3-0.6B | prompt + review + ví dụ | 2304         | cùng tokenizer + cùng prompt như bản 4B ⇒ cùng số token ⇒ cùng ngưỡng                    |

- **Khác nhau vì input khác nhau**: encoder nhận **chỉ review** (TB ~30–44 token; dài nhất **229** ở ViSoBERT, **301** ở PhoBERT), LLM nhận **cả prompt** (TB ~230–1.878 token; dài nhất **2.122**).
- **Cùng nhóm bằng nhau**: hai encoder để 256 cho **cùng ngân sách input** (so sánh công bằng); hai Qwen cùng tokenizer/prompt nên cùng số token nên cùng ngưỡng.
