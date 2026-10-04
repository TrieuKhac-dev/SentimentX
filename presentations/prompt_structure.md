# Cấu trúc một prompt gửi model sinh (LLM)

> Đọc file này khi: cần biết một prompt gồm những phần nào, và xem ví dụ thật.
> Liên quan: `presentations/llm_batch_size.md`, `presentations/token_limit.md`, `docs/04_experiments/02_model_input.md`

Mỗi review → **một prompt**, và prompt là **một hội thoại** gồm lượt `system` và lượt `user` (rồi model sinh
lượt `assistant`). Ví dụ few-shot được **chèn vào lượt user**, không phải thành các lượt `assistant`.

## 1. Một prompt gồm những phần nào

| Phần                                       | Lấy từ đâu                                        | Ví dụ (bản đang dùng)                                                                        |
| ------------------------------------------ | ------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| **System**                                 | `configs/prompts/system/<tên>.txt`                | "Bạn là chuyên gia phân tích cảm xúc theo khía cạnh (ABSA) cho review mỹ phẩm tiếng Việt. …" |
| **Nhiệm vụ**                               | file prompt, đầu lượt user                        | "với mỗi khía cạnh … hãy chọn đúng một mã cảm xúc"                                           |
| **Bảng mã nhãn** `{label_guide}`           | `label_map.json` + không gian nhãn của thí nghiệm | `0 = không nhắc tới…`, `1 = positive`, `2 = negative`                                        |
| **Danh sách khía cạnh** `{aspects}`        | `label_map.json`                                  | `stayingpower, texture, smell, price, colour, shipping, packing`                             |
| **Examples (ví dụ few-shot)** `{examples}` | `configs/prompts/examples/<tên>.txt`              | 1 hoặc 5 khối                                                                                |
| **Review** `{text}`                        | dữ liệu đã xử lý                                  | review thật                                                                                  |
| **Khuôn JSON** `{example}`                 | sinh theo danh sách khía cạnh                     | `{"stayingpower": 0, …}` (điền mã thật vào)                                                  |

## 2. Dạng cho NGƯỜI ĐỌC

### 2.1. CoT (`absa_cot_1shot_v1`, 1 ví dụ)

```text
### SYSTEM
Bạn là chuyên gia phân tích cảm xúc theo khía cạnh (ABSA) cho review mỹ phẩm tiếng Việt.
Bạn luôn trả lời đúng định dạng được yêu cầu và không thêm bất kỳ lời nào khác.

### USER
Nhiệm vụ: với mỗi khía cạnh trong danh sách, hãy chọn đúng một mã cảm xúc và nói rõ vì sao.

  0 = không nhắc tới khía cạnh này
  1 = positive (tích cực)
  2 = negative (tiêu cực)

Danh sách khía cạnh: stayingpower, texture, smell, price, colour, shipping, packing

Quy trình cho TỪNG khía cạnh:
1. Trích nguyên văn đoạn văn nói về khía cạnh đó. Nếu review không nhắc tới, ghi "không nhắc tới".
2. Nêu ngắn gọn vì sao đoạn đó là tích cực hay tiêu cực.
3. Chốt mã số.

Ví dụ:
--- Ví dụ 1 ---
Review: "Thỏi son lên màu đỏ gạch tươi tắn, tán đều tệp vào da ngăm nhìn vẫn tự nhiên. Đánh từ sáng tới chiều muộn vẫn chưa phải dặm lại. Mùi hương thoang thoảng dễ chịu, vỏ hộp cứng cáp cầm chắc tay."
SUY LUẬN:
- colour: "lên màu đỏ gạch tươi tắn, tán đều tệp vào da ngăm" | khen màu lên đẹp | mã 1
- stayingpower: "đánh từ sáng tới chiều muộn vẫn chưa phải dặm lại" | giữ màu lâu | mã 1
- texture: "tán đều tệp vào da" | chất son dễ tán, không bị khô | mã 1
- smell: "mùi hương thoang thoảng dễ chịu" | mùi dễ chịu | mã 1
- packing: "vỏ hộp cứng cáp cầm chắc tay" | đóng gói tốt | mã 1
- price: "không nhắc tới" | review không nói về giá | mã 0
- shipping: "không nhắc tới" | review không nói về vận chuyển | mã 0
KẾT QUẢ:
{"colour": 1, "stayingpower": 1, "texture": 1, "smell": 1, "packing": 1, "price": 0, "shipping": 0}

Review cần phân tích:
"""
Cảm giác son bên trong rất là ít luôn í, đóng gói cẩn thận, dịch nhưng mà giao hàng khá nhanh
"""

Trả lời ĐÚNG định dạng sau, không thêm gì khác:
SUY LUẬN:
- <khía cạnh>: <trích dẫn> | <lí do ngắn> | mã <số>     (một dòng cho MỖI khía cạnh)
KẾT QUẢ:
{"stayingpower": 0, "texture": 0, "smell": 0, "price": 0, "colour": 0, "shipping": 0, "packing": 0}
  (dòng KẾT QUẢ trên chỉ là KHUÔN JSON: điền mã THẬT của từng khía cạnh vào đó, KHÔNG chép nguyên các số 0)
```

### 2.2. One-turn (`absa_one_turn_v1`, không ví dụ)

```text
### SYSTEM
Bạn là chuyên gia phân tích cảm xúc theo khía cạnh (ABSA) cho review mỹ phẩm tiếng Việt.
Bạn luôn trả lời đúng định dạng được yêu cầu và không thêm bất kỳ lời nào khác.

### USER
Nhiệm vụ: với mỗi khía cạnh dưới đây, hãy chọn đúng một mã cảm xúc.
  0 = không nhắc tới khía cạnh này
  1 = positive (tích cực)
  2 = negative (tiêu cực)

Danh sách khía cạnh: stayingpower, texture, smell, price, colour, shipping, packing

Review:
"""
Cảm giác son bên trong rất là ít luôn í, đóng gói cẩn thận, dịch nhưng mà giao hàng khá nhanh
"""

Chỉ trả về DUY NHẤT một object JSON, khóa là tên khía cạnh, giá trị là mã số.
Ví dụ định dạng: {"stayingpower": 0, "texture": 0, "smell": 0, "price": 0, "colour": 0, "shipping": 0, "packing": 0}
```

## 3. Dạng NGUYÊN MẪU gửi model (sau chat template của tokenizer)

Bọc bởi **chat template của tokenizer** model (Qwen3 dùng markup `<|im_start|>…<|im_end|>`); các mốc
`<|im_start|>`/`<|im_end|>` và lượt `assistant` trống ở cuối là do template thêm, **không** nằm trong file
prompt.

### 3.1. CoT

```text
<|im_start|>system
Bạn là chuyên gia phân tích cảm xúc theo khía cạnh (ABSA) cho review mỹ phẩm tiếng Việt.
Bạn luôn trả lời đúng định dạng được yêu cầu và không thêm bất kỳ lời nào khác.<|im_end|>
<|im_start|>user
Nhiệm vụ: với mỗi khía cạnh trong danh sách, hãy chọn đúng một mã cảm xúc và nói rõ vì sao.

  0 = không nhắc tới khía cạnh này
  1 = positive (tích cực)
  2 = negative (tiêu cực)

Danh sách khía cạnh: stayingpower, texture, smell, price, colour, shipping, packing

Quy trình cho TỪNG khía cạnh:
1. Trích nguyên văn đoạn văn nói về khía cạnh đó. Nếu review không nhắc tới, ghi "không nhắc tới".
2. Nêu ngắn gọn vì sao đoạn đó là tích cực hay tiêu cực.
3. Chốt mã số.

Ví dụ:
--- Ví dụ 1 ---
Review: "Thỏi son lên màu đỏ gạch tươi tắn, tán đều tệp vào da ngăm nhìn vẫn tự nhiên. Đánh từ sáng tới chiều muộn vẫn chưa phải dặm lại. Mùi hương thoang thoảng dễ chịu, vỏ hộp cứng cáp cầm chắc tay."
SUY LUẬN:
- colour: "lên màu đỏ gạch tươi tắn, tán đều tệp vào da ngăm" | khen màu lên đẹp | mã 1
- stayingpower: "đánh từ sáng tới chiều muộn vẫn chưa phải dặm lại" | giữ màu lâu | mã 1
- texture: "tán đều tệp vào da" | chất son dễ tán, không bị khô | mã 1
- smell: "mùi hương thoang thoảng dễ chịu" | mùi dễ chịu | mã 1
- packing: "vỏ hộp cứng cáp cầm chắc tay" | đóng gói tốt | mã 1
- price: "không nhắc tới" | review không nói về giá | mã 0
- shipping: "không nhắc tới" | review không nói về vận chuyển | mã 0
KẾT QUẢ:
{"colour": 1, "stayingpower": 1, "texture": 1, "smell": 1, "packing": 1, "price": 0, "shipping": 0}

Review cần phân tích:
"""
Cảm giác son bên trong rất là ít luôn í, đóng gói cẩn thận, dịch nhưng mà giao hàng khá nhanh
"""

Trả lời ĐÚNG định dạng sau, không thêm gì khác:
SUY LUẬN:
- <khía cạnh>: <trích dẫn> | <lí do ngắn> | mã <số>     (một dòng cho MỖI khía cạnh)
KẾT QUẢ:
{"stayingpower": 0, "texture": 0, "smell": 0, "price": 0, "colour": 0, "shipping": 0, "packing": 0}
  (dòng KẾT QUẢ trên chỉ là KHUÔN JSON: điền mã THẬT của từng khía cạnh vào đó, KHÔNG chép nguyên các số 0)<|im_end|>
<|im_start|>assistant
```

### 3.2. One-turn

```text
<|im_start|>system
Bạn là chuyên gia phân tích cảm xúc theo khía cạnh (ABSA) cho review mỹ phẩm tiếng Việt.
Bạn luôn trả lời đúng định dạng được yêu cầu và không thêm bất kỳ lời nào khác.<|im_end|>
<|im_start|>user
Nhiệm vụ: với mỗi khía cạnh dưới đây, hãy chọn đúng một mã cảm xúc.
  0 = không nhắc tới khía cạnh này
  1 = positive (tích cực)
  2 = negative (tiêu cực)

Danh sách khía cạnh: stayingpower, texture, smell, price, colour, shipping, packing

Review:
"""
Cảm giác son bên trong rất là ít luôn í, đóng gói cẩn thận, dịch nhưng mà giao hàng khá nhanh
"""

Chỉ trả về DUY NHẤT một object JSON, khóa là tên khía cạnh, giá trị là mã số.
Ví dụ định dạng: {"stayingpower": 0, "texture": 0, "smell": 0, "price": 0, "colour": 0, "shipping": 0, "packing": 0}<|im_end|>
<|im_start|>assistant
```

## 4. Ba điểm cần nhớ

- **Một prompt = một review.** N review → N prompt (xem `presentations/llm_batch_size.md`).
- **Vì sao ví dụ nằm ở lượt `user`, không ở lượt `assistant`:** định dạng file **có** cho phép `[ASSISTANT]`
  (`src/experiments/prompts.py`), nhưng thư viện hiện tại chèn ví dụ qua ô nhớ `{examples}` - một **KHỐI VĂN
  BẢN** nằm trong mục `[USER]`. Nhờ vậy **đổi số ví dụ chỉ cần đổi file `examples/`**, giữ nguyên prompt +
  config (biến thực nghiệm rẻ), và hội thoại chỉ còn **một lượt `assistant` = câu trả lời thật**, nên bộ đọc
  chỉ phân tích đúng phần model sinh ra.
- **`{label_guide}` theo không gian nhãn của thí nghiệm**: bài toán `binary` + `neutral_policy: drop` thì bảng
  mã chỉ còn `0/1/2` (bỏ `3 = neutral`), và `{example}` là **khuôn JSON toàn số 0** để model điền mã thật.
