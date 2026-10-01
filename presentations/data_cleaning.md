# Module Data Cleaning — chi tiết

> Đọc file này khi: trình bày bước làm sạch văn bản lúc inference.
> Liên quan: `presentations/inference_pipeline.md`, `presentations/model_preprocessing.md`

Lúc inference, Data Cleaning **chỉ chuẩn hoá HÌNH THỨC** — **không** viết lại teencode và **không**
bỏ dấu tiếng Việt. Chỉ có hai bước:

```mermaid
flowchart LR
    IN["📥 Văn bản thô"]:::io
    U["1 · Chuẩn hoá Unicode<br/>(NFC)"]:::step
    W["2 · Chuẩn hoá khoảng trắng<br/>&nbsp;&nbsp;gộp space/tab thừa<br/>&nbsp;&nbsp;gộp dòng trống<br/>&nbsp;&nbsp;cắt hai đầu"]:::step
    OUT["✅ Văn bản đã làm sạch"]:::io

    IN --> U --> W --> OUT

    classDef io    fill:#5B7FBD33,stroke:#5B7FBD,stroke-width:1.5px,rx:14,ry:14,padding:18px;
    classDef step  fill:#5FA36B33,stroke:#5FA36B,stroke-width:1.5px,rx:12,ry:12,padding:12px;
```

| Bước | Làm gì | Ví dụ |
| --- | --- | --- |
| 1 · Unicode (NFC) | gộp ký tự có dấu về **một** dạng chuẩn (NFD → NFC) | ký tự `e` ghép với dấu sắc → một ký tự `é` |
| 2 · Khoảng trắng | gộp space/tab thừa thành 1 space; gộp nhiều dòng trống thành 1; cắt khoảng trắng hai đầu | `"Son  đẹp\t\tquá  "` → `"Son đẹp quá"` |

**Không** làm: không viết lại teencode (`xjnk` giữ nguyên), không bỏ dấu (`đẹp` giữ nguyên), và
**không loại review nào** — lúc inference ta **đánh giá** review, không vứt nó đi.
