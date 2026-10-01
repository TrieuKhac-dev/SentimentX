# Inference pipeline — luồng dự đoán một review (tổng quát)

> Đọc file này khi: trình bày luồng inference khi đã có model (serving).
> Liên quan: `presentations/measurement.md`, `docs/00_workflow/04_terms.md`

Sơ đồ ở mức MODULE (không đi vào chi tiết bên trong). Đây là luồng lúc **serving**: một review vào,
cảm xúc trên các khía cạnh ra - không có đọc dataset, không chấm điểm, không ghi `metrics`.

```mermaid
flowchart TD
    RAW["Review tiếng Việt (văn bản thô)<br/>· Son đẹp nhưng ship lâu 😢<br/>· màu xjnk, lên môi hơi khô<br/>· oke nha shop, giao nhanh"]:::io
    CLEAN["Module Data Cleaning"]:::step
    PREP["Module Model Preprocessing"]:::step
    CLS["Module Aspect-based<br/>Sentiment Classification"]:::model
    OUT["Cảm xúc của bình luận<br/>trên các khía cạnh"]:::io

    RAW --> CLEAN
    CLEAN -->|văn bản đã làm sạch| PREP
    PREP -->|dữ liệu cho vào model| CLS
    CLS -->|kết quả| OUT

    classDef io    fill:#eef1f5,stroke:#9aa7b4,color:#1b1f23,stroke-width:1px;
    classDef step  fill:#eef1f5,stroke:#9aa7b4,color:#1b1f23,stroke-width:1px;
    classDef model fill:#e8eef7,stroke:#8ba0c4,color:#1b1f23,stroke-width:1px;
```

## Ghi chú

- `Module Data Cleaning` = làm sạch **HÌNH THỨC** (chuẩn hoá Unicode, khoảng trắng, gắn cờ nhiễu). Dự
  án **KHÔNG viết lại teencode** và **KHÔNG bỏ dấu tiếng Việt** - model đọc văn bản nguyên bản, nên
  review có icon/teencode vẫn đi tới model gần như nguyên vẹn.
- `Module Model Preprocessing` là bước **RIÊNG của từng model** (tách từ cho PhoBERT; tokenizer; hoặc
  dựng prompt cho Qwen3). Hai loại preprocessing này **không được lẫn** - xem
  `docs/00_workflow/04_terms.md`.
- Sơ đồ này là luồng lúc **serving**. Lúc **thử nghiệm** thì trước `Model` còn có bước đọc cả tập dữ
  liệu và sau `Classification` còn có bước chấm điểm - xem `presentations/measurement.md`.
