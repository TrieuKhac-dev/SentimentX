# Inference pipeline — luồng dự đoán một review (tổng quát)

> Đọc file này khi: trình bày luồng inference khi đã có model (serving).
> Liên quan: `presentations/measurement.md`, `docs/00_workflow/04_terms.md`

Sơ đồ ở mức MODULE (không đi vào chi tiết bên trong). Đây là luồng lúc **serving**: một review vào,
cảm xúc trên các khía cạnh ra - không có đọc dataset, không chấm điểm, không ghi `metrics`.

```mermaid
flowchart LR
    RAW["📥 Review tiếng Việt<br/>(văn bản thô)<br/><br/>&nbsp;&nbsp;• Son đẹp mà ship lâu 😢<br/>&nbsp;&nbsp;&nbsp;&nbsp;• màu xjnk, lên môi hơi khô<br/>&nbsp;&nbsp;&nbsp;&nbsp;• oke nha shop, giao nhanh"]:::io

    CLEAN["🧹 Module<br/>&nbsp;&nbsp;&nbsp;&nbsp;Data Cleaning"]:::step
    PREP["⚙️ Module<br/>&nbsp;&nbsp;&nbsp;Model Preprocessing"]:::step
    CLS["🧠 Module Aspect-based<br/>Sentiment Classification"]:::model
    OUT["🎯 Cảm xúc của bình luận<br/>trên các khía cạnh"]:::io

    RAW  --> CLEAN
    CLEAN -->|<span style='font-size:16px'>văn bản đã làm sạch</span>| PREP
    PREP  -->|<span style='font-size:16px'>dữ liệu cho vào model</span>| CLS
    CLS   -->|<span style='font-size:16px'>kết quả</span>| OUT

    classDef io    fill:#5B7FBD33,stroke:#5B7FBD,stroke-width:1.5px,rx:14,ry:14,padding:18px;
    classDef step  fill:#5FA36B33,stroke:#5FA36B,stroke-width:1.5px,rx:12,ry:12,padding:12px;
    classDef model fill:#9B6FD133,stroke:#9B6FD1,stroke-width:1.5px,rx:12,ry:12,padding:12px;
```

## Ghi chú

- `Module Data Cleaning` = làm sạch **HÌNH THỨC** (chuẩn hoá Unicode, khoảng trắng, gắn cờ nhiễu). Dự
  án **KHÔNG viết lại teencode** và **KHÔNG bỏ dấu tiếng Việt** - model đọc văn bản nguyên bản, nên
  review có icon/teencode vẫn đi tới model gần như nguyên vẹn.
- `Module Model Preprocessing` là bước **RIÊNG của từng model** (tách từ cho PhoBERT; tokenizer; hoặc
  dựng prompt cho Qwen3). Hai loại preprocessing này **không được lẫn** - xem
  `docs/00_workflow/04_terms.md`.
