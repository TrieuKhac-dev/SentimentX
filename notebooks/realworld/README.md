# notebooks/realworld

## Mục đích

Đánh giá mô hình trên dữ liệu thật, **chỉ suy luận — không huấn luyện**. Không dùng tập này để chọn mô hình, chỉnh siêu tham số hay cập nhật trọng số.

## Dữ liệu

- 60 đánh giá son môi trên Shopee, tiếng Việt.
- Cột `text` + 7 khía cạnh: `stayingpower`, `texture`, `smell`, `price`, `colour`, `shipping`, `packing`.
- Nhãn mỗi khía cạnh là 0/1/2; **không có nhãn 3 (trung tính)**.
- `text` giữ nguyên như nguồn: không làm sạch, không chuẩn hoá, không tách từ (kể cả xuống dòng và dấu câu).
- 60 dòng, `row_id` 0..59, không nhãn thiếu, không text trùng.

## Đường dẫn CSV

- Trong repo: `notebooks/realworld/data/shoppe_absa.csv` (UTF-8 BOM, mở bằng Excel không lỗi dấu).
- Trên Drive: `<Drive>/SentimentX/data/raw/realworld/v0.1.0/shoppe_absa.csv`.

## Hai mô hình đánh giá

Nguồn: `presentations/present_report/present_report_v6.md`.

- `cafebert_exp027` — encoder CafeBERT, lượt E1.
- `qwen3_4b_exp009` — LLM Qwen3-4B, lượt L1 (`qwen3-4b-instruct-2507/prompt-cot/exp009`).

## Trọng số

Kỳ vọng trên Drive, dưới `<Drive>/SentimentX/models/`:

- `cafebert_exp027/best/` (adapter + head)
- `cafebert-base/`
- `Qwen3-4B-Instruct-2507/`

Trọng số nằm trong `.gitignore` và **không có trong bàn giao**; người dùng phải tự đưa lên Drive trước khi chạy.

## Tiền xử lý khi suy luận

- Đưa nguyên văn `text` vào mô hình: không làm sạch, không tách từ.
- CafeBERT: segmenter = none.
- Qwen: dùng prompt CoT như lượt L1.

## Đầu ra

Mỗi lần chạy ghi vào thư mục riêng, ví dụ `notebooks/realworld/outputs/<run>/`:

- `predictions.csv` — dự đoán từng khía cạnh cho từng `row_id`.
- `run_meta.json` — mô hình, trọng số, thời điểm, cấu hình suy luận.
- `errors.csv` — các dòng dự đoán sai.
- Chỉ số chấm bằng scorer của dự án (`src/evaluation/scorers/`), không tự viết lại công thức.

**Không** ghi vào `experiments/**/results/**` chính thức.
