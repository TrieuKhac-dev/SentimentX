# Cây phát triển thí nghiệm (trạng thái 02/10/2026)

> Đọc file này khi: trình bày dự án đi từ đâu tới đâu, và vì sao mỗi bước lại có mặt.
> Liên quan: `docs/04_experiments/07_evolution.md` (bản đầy đủ), `docs/04_experiments/08_experiment_rationale.md`

Chín lượt có kết quả, một nhánh chưa có. Mũi tên là quan hệ **cha - con** (lượt con khác cha đúng những
gì ghi trên mũi tên); đường nét đứt là **đối chiếu** (so kết quả, không phải chạy lại).

```mermaid
flowchart TD
    REF["Công bố: GPT-4o-mini + CoT 0/1/5-shot<br/>mốc cần so"]:::ref

    subgraph "A. Hai encoder học LoRA (2)"
        A1["visobert/lora/exp001<br/>94,86"]:::keep
        A2["phobert-base-v2/lora/exp001<br/>88,40"]:::keep
    end

    subgraph "B. Qwen3-4B + CoT (6)"
        B2["prompt-cot/exp002<br/>COT+0-shot · 97,16"]:::keep
        B3["prompt-cot/exp003<br/>COT+1-shot · 97,72"]:::best
        B4["prompt-cot/exp004<br/>COT+5-shot · 97,11"]:::keep
        B5["prompt-cot/exp005<br/>fp16 · 96,62"]:::keep
        B6["prompt-cot/exp006<br/>fp16 · 96,60"]:::keep
        B7["prompt-cot/exp007<br/>fp16 · 96,48"]:::keep
    end

    subgraph "C. Qwen3-4B một lượt (1)"
        C1["prompt-one-turn/exp001<br/>95,33"]:::keep
    end

    subgraph "D. Qwen3-0.6B + CoT (3) - CHƯA có kết quả"
        D1["prompt-cot/exp001..003<br/>nạp nhầm trọng số 4B"]:::drop
    end

    REF -.->|so với| B2
    REF -.->|so với| B3
    REF -.->|so với| B4
    REF -.->|so với| A1
    REF -.->|so với| A2

    B2 -->|"chỉ đổi cách nạp: 4-bit sang fp16"| B5
    B3 -->|"chỉ đổi cách nạp: 4-bit sang fp16"| B6
    B4 -->|"chỉ đổi cách nạp: 4-bit sang fp16"| B7
    B2 -.->|"chỉ bỏ phần suy luận"| C1
    B2 -.->|"cùng prompt, khác model (~7 lần nhỏ hơn)"| D1

    classDef ref fill:#E0A93B33,stroke:#E0A93B,stroke-width:1.5px;
    classDef keep fill:#5FA36B33,stroke:#5FA36B,stroke-width:1.5px;
    classDef best fill:#5B7FBD33,stroke:#5B7FBD,stroke-width:2.5px;
    classDef drop fill:#C0504D22,stroke:#C0504D,stroke-width:2.5px;
```

## Bốn nhánh trả lời bốn câu khác nhau

| Nhánh | Câu hỏi | Số lượt | Trạng thái |
| --- | --- | --- | --- |
| A | Encoder nhỏ học LoRA bằng nào công bố, có tách từ và không tách từ khác nhau ra sao? | 2 | xong |
| B | Qwen3-4B tái hiện được mức 0/1/5 ví dụ của công bố không, và lượng hoá 4-bit mất mấy điểm? | 6 | xong |
| C | Bỏ suy luận từng bước thì mất bao nhiêu điểm? | 1 | xong |
| D | Model nhỏ hơn ~7 lần thì kém bao nhiêu? | 3 | **không dùng** - đã xoá kết quả, là việc kế tiếp |

## Một nút đọc thế nào

```
<lượt chạy>  <-  <lượt cha>              (vì sao đi bước này)
    Kết quả: acc TB khía cạnh · F1 sắc thái macro · khớp hoàn toàn     Kết luận: giữ / bỏ / đổi hướng
```

Số trong sơ đồ là **accuracy trung bình theo khía cạnh trên cơ sở `paper`** (cách công bố đếm), tập `test`
1.623 review. Nhánh D **không có số** vì ba lượt đó chạy nhầm trọng số 4B - chi tiết ở
`docs/04_experiments/08_experiment_rationale.md` §5.

Bản đồ hoạ để chiếu/sửa tay: `presentations/experiment_tree.drawio` (mở bằng draw.io Desktop, diagrams.net,
hoặc extension Draw.io Integration trong VS Code). Sơ đồ Mermaid ở trên là bản văn bản để review và để
GitHub render; **hai bản phải giữ cùng nội dung** - sửa một bên thì sửa cả bên.
