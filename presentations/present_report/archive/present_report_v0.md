# present_report - Đối chiếu dự án với công bố tham chiếu

> Đọc file này khi: trình bày kết quả dự án so với công bố tham chiếu.
> Liên quan: `docs/04_experiments/reference_publication.md`, `data/reference_publication/`, `table3_accuracy_by_aspect.csv`

## Tóm tắt

Tài liệu này đặt kết quả của **Dự án** cạnh kết quả của **công bố tham chiếu** trên cùng tập kiểm tra, để xem dự án đang mạnh và yếu ở đâu.

Điểm quan trọng cần hiểu trước khi đọc bảng: phần so sánh chính sử dụng cách đánh giá mà công bố tham chiếu đã dùng. Cách này chỉ giữ lại những review mà cả nhãn thật và dự đoán đều thuộc hai nhóm **tích cực** hoặc **tiêu cực**. Vì vậy, điểm số trong phần này chưa phản ánh đầy đủ khả năng xử lý review không nhắc đến khía cạnh.

- Số liệu của công bố được lấy từ `data/reference_publication/*.csv` và đã được đối chiếu với Table 3–6 trong `announcement.md`.
- Số liệu của dự án được lấy từ `experiments/**/results/<hash8>/metrics.json`, với cơ sở `paper`; không dùng `data/reports/**`.
- Tất cả Accuracy/Precision/Recall/F1 đều tính theo **%**.
- Chênh lệch giữa hai kết quả dùng **điểm phần trăm (pp)**. Ví dụ, 98.26% cao hơn 97.70% là **+0.56 pp**, không phải +56%.
- Hai bên được đánh giá trên cùng tập `test` gồm **1.623 review** (`…-e616c1e3`).
- Các encoder không có khái niệm shot, nên được so sánh với cả ba thiết lập 0-shot, 1-shot và 5-shot của công bố.

## Các kết quả trong bảng tương ứng với những lượt chạy nào?

| Cột                            | Lượt chạy thật                                                |
| ------------------------------ | ------------------------------------------------------------- |
| CB 0/1/5-shot                  | GPT-4o-mini, Chain-of-Thought (công bố)                       |
| Qwen3-4B 0-shot (4-bit)        | `qwen3-4b-instruct-2507/prompt-cot/exp008`                    |
| Qwen3-4B 1-shot (4-bit)        | `qwen3-4b-instruct-2507/prompt-cot/exp009`                    |
| Qwen3-4B 5-shot (fp16)         | `qwen3-4b-instruct-2507/prompt-cot/exp007`                    |
| Qwen3-4B 5-shot (4-bit)        | `qwen3-4b-instruct-2507/prompt-cot/exp010`                    |
| CafeBERT head.train seed42     | `cafebert/lora/exp002` (`head.trainable: true`, seed 42)      |
| CafeBERT head.train seed7      | `cafebert/lora/exp004` (như exp002, **seed 7**)               |
| Pb-large head.train            | `phobert-large/lora/exp002` (`head.trainable: true`)          |
| Pb-base Cross-Entropy          | `phobert-base-v2/lora/exp001` (mất mát thường, đầu đóng băng) |
| Pb-base Weighted Cross-Entropy | `phobert-base-v2/lora/exp002` (trọng số lớp nghịch đảo)       |

## Bảng 3 — Accuracy theo khía cạnh (%, cơ sở `paper`)

| Aspect       | CB 0-shot | CB 1-shot | CB 5-shot | Qwen3-4B 0-shot (4-bit) | Qwen3-4B 1-shot (4-bit) | Qwen3-4B 5-shot (fp16) | Qwen3-4B 5-shot (4-bit) | CafeBERT head.train seed42 | CafeBERT head.train seed7 | Pb-large head.train | Pb-base Cross-Entropy | Pb-base Weighted Cross-Entropy |
| ------------ | --------- | --------- | --------- | ----------------------- | ----------------------- | ---------------------- | ----------------------- | -------------------------- | ------------------------- | ------------------- | --------------------- | ------------------------------ |
| Smell        | 94.59     | 96.15     | 92.86     | 95.26                   | 97.44                   | 95.67                  | 96.09                   | 96.28                      | 96.96                     | 96.92               | 84.48                 | 95.92                          |
| Price        | 97.22     | 100.00    | 100.00    | 96.25                   | 98.49                   | 97.37                  | 98.45                   | 99.07                      | 98.45                     | 98.13               | 98.45                 | 98.14                          |
| Texture      | 94.12     | 100.00    | 100.00    | 97.67                   | 96.86                   | 95.83                  | 96.06                   | 97.42                      | 97.90                     | 98.11               | 83.86                 | 95.55                          |
| Colour       | 97.37     | 96.61     | 94.74     | 97.67                   | 98.82                   | 96.92                  | 96.56                   | 97.60                      | 98.35                     | 97.28               | 92.27                 | 96.41                          |
| Stayingpower | 100.00    | 94.12     | 92.86     | 98.54                   | 96.15                   | 94.61                  | 97.37                   | 97.45                      | 97.87                     | 96.98               | 64.71                 | 92.67                          |
| Packing      | 98.25     | 98.11     | 100.00    | 97.90                   | 97.90                   | 98.26                  | 97.89                   | 99.30                      | 99.65                     | 98.61               | 96.83                 | 99.65                          |
| Shipping     | 100.00    | 98.89     | 96.70     | 97.51                   | 98.72                   | 96.72                  | 97.94                   | 98.02                      | 98.61                     | 97.82               | 98.19                 | 98.02                          |
| **MACRO**    | **97.36** | **97.70** | **96.74** | **97.26**               | **97.77**               | **96.48**              | **97.19**               | **97.88**                  | **98.26**                 | **97.69**           | **88.40**             | **96.62**                      |
| **Δ vs CB**  | —         | —         | —         | −0.10 (vs CB0)          | +0.07 (vs CB1)          | −0.26 (vs CB5)         | +0.45 (vs CB5)          | +0.18 (vs CB1)             | +0.56 (vs CB1)            | −0.01 (vs CB1)      | −9.30 (vs CB1)        | −1.08 (vs CB1)                 |

## Số lượng review trong tập test cho từng nhãn

Các con số dưới đây là số review **trong chính tập test 1.623 review** có nhãn tích cực hoặc tiêu cực tương ứng với từng khía cạnh. Nói cách khác, đây là số lượng mẫu thật dùng để đánh giá từng trường hợp; các model đều được đánh giá trên cùng những mẫu này.

Số lượng review giữa các khía cạnh không giống nhau, đặc biệt nhóm tiêu cực ở `price` và `packing` có rất ít mẫu. Vì vậy, các chỉ số của những trường hợp này cần được đọc thận trọng.

| Khía cạnh    | Review tích cực trong test | Review tiêu cực trong test |
| ------------ | -------------------------: | -------------------------: |
| stayingpower |                        141 |                         96 |
| texture      |                        346 |                         83 |
| smell        |                        252 |                         48 |
| price        |                        321 |                      **6** |
| colour       |                        622 |                         54 |
| shipping     |                        334 |                        174 |
| packing      |                        282 |                     **10** |

Ví dụ, `price` chỉ có **6 review tiêu cực** và `packing` chỉ có **10**. Vì vậy, điểm F1 ở hai dòng này rất dễ dao động mạnh chỉ vì một vài dự đoán thay đổi.

## Bảng 4 — Precision theo khía cạnh và sắc thái (%, `paper`)

| Aspect       | Sentiment |   n | CB 0-shot | CB 1-shot | CB 5-shot | Qwen3-4B 0-shot (4-bit) | Qwen3-4B 1-shot (4-bit) | Qwen3-4B 5-shot (fp16) | Qwen3-4B 5-shot (4-bit) | CafeBERT head.train seed42 | CafeBERT head.train seed7 | Pb-large head.train | Pb-base Cross-Entropy | Pb-base Weighted Cross-Entropy |
| ------------ | --------- | --: | --------- | --------- | --------- | ----------------------- | ----------------------- | ---------------------- | ----------------------- | -------------------------- | ------------------------- | ------------------- | --------------------- | ------------------------------ |
| Smell        | positive  | 252 | 97.06     | 100.00    | 96.15     | 99.10                   | 99.50                   | 98.70                  | 99.40                   | 98.80                      | 99.20                     | 99.60               | 84.50                 | 99.60                          |
| Smell        | negative  |  48 | 66.67     | 50.00     | 50.00     | 80.40                   | 89.40                   | 83.00                  | 84.60                   | 84.90                      | 86.80                     | 85.50               | 0.00                  | 81.00                          |
| Price        | positive  | 321 | 100.00    | 100.00    | 100.00    | 100.00                  | 99.60                   | 100.00                 | 100.00                  | 99.10                      | 98.50                     | 98.10               | 98.40                 | 98.10                          |
| Price        | negative  |   6 | 0.00      | 0.00      | 0.00      | 15.40                   | 50.00                   | 30.00                  | 33.30                   | 100.00                     | 0.00                      | 0.00                | 0.00                  | 0.00                           |
| Texture      | positive  | 346 | 92.68     | 100.00    | 100.00    | 99.60                   | 99.60                   | 98.30                  | 98.50                   | 98.50                      | 99.10                     | 98.80               | 83.90                 | 99.10                          |
| Texture      | negative  |  83 | 100.00    | 100.00    | 100.00    | 91.00                   | 88.70                   | 87.10                  | 87.70                   | 92.80                      | 93.00                     | 95.10               | 0.00                  | 83.20                          |
| Colour       | positive  | 622 | 100.00    | 100.00    | 100.00    | 99.30                   | 100.00                  | 99.50                  | 99.50                   | 99.70                      | 99.70                     | 99.80               | 92.30                 | 99.70                          |
| Colour       | negative  |  54 | 77.78     | 75.00     | 66.67     | 80.70                   | 86.00                   | 73.80                  | 72.30                   | 78.80                      | 85.20                     | 75.70               | 0.00                  | 70.30                          |
| Stayingpower | positive  | 141 | 100.00    | 100.00    | 100.00    | 98.80                   | 98.70                   | 96.80                  | 98.80                   | 98.60                      | 97.90                     | 97.80               | 64.40                 | 98.40                          |
| Stayingpower | negative  |  96 | 100.00    | 80.00     | 80.00     | 98.10                   | 93.80                   | 91.80                  | 95.60                   | 95.90                      | 97.90                     | 95.70               | 100.00                | 85.80                          |
| Packing      | positive  | 282 | 100.00    | 100.00    | 100.00    | 100.00                  | 100.00                  | 99.60                  | 99.60                   | 100.00                     | 100.00                    | 99.60               | 96.80                 | 100.00                         |
| Packing      | negative  |  10 | 66.67     | 66.67     | 100.00    | 60.00                   | 62.50                   | 69.20                  | 64.30                   | 81.80                      | 90.00                     | 75.00               | 0.00                  | 90.90                          |
| Shipping     | positive  | 334 | 100.00    | 100.00    | 96.88     | 98.40                   | 99.00                   | 96.60                  | 98.40                   | 99.10                      | 100.00                    | 99.40               | 98.50                 | 99.10                          |
| Shipping     | negative  | 174 | 100.00    | 96.30     | 96.30     | 95.70                   | 98.10                   | 96.90                  | 97.00                   | 96.00                      | 96.10                     | 94.90               | 97.60                 | 96.00                          |
| **MACRO**    | positive  |   — | 98.53     | 100.00    | 99.00     | 99.31                   | 99.49                   | 98.50                  | 99.17                   | 99.11                      | 99.20                     | 99.01               | 88.40                 | 99.14                          |
| **MACRO**    | negative  |   — | 73.02     | 66.85     | 70.42     | 74.47                   | 81.21                   | 75.97                  | 76.40                   | 90.03                      | 78.43                     | 74.56               | 28.23                 | 72.46                          |

## Bảng 5 — Recall theo khía cạnh và sắc thái (%, `paper`)

| Aspect       | Sentiment |   n | CB 0-shot | CB 1-shot | CB 5-shot | Qwen3-4B 0-shot (4-bit) | Qwen3-4B 1-shot (4-bit) | Qwen3-4B 5-shot (fp16) | Qwen3-4B 5-shot (4-bit) | CafeBERT head.train seed42 | CafeBERT head.train seed7 | Pb-large head.train | Pb-base Cross-Entropy | Pb-base Weighted Cross-Entropy |
| ------------ | --------- | --: | --------- | --------- | --------- | ----------------------- | ----------------------- | ---------------------- | ----------------------- | -------------------------- | ------------------------- | ------------------- | --------------------- | ------------------------------ |
| Smell        | positive  | 252 | 97.06     | 96.00     | 96.15     | 95.20                   | 97.40                   | 96.10                  | 95.70                   | 96.80                      | 97.20                     | 96.70               | 100.00                | 95.50                          |
| Smell        | negative  |  48 | 66.67     | 100.00    | 50.00     | 95.70                   | 97.70                   | 93.60                  | 97.80                   | 93.80                      | 95.80                     | 97.90               | 0.00                  | 97.90                          |
| Price        | positive  | 321 | 97.22     | 100.00    | 100.00    | 96.20                   | 98.90                   | 97.30                  | 98.40                   | 100.00                     | 100.00                    | 100.00              | 100.00                | 100.00                         |
| Price        | negative  |   6 | 0.00      | 0.00      | 0.00      | 100.00                  | 75.00                   | 100.00                 | 100.00                  | 25.00                      | 0.00                      | 0.00                | 0.00                  | 0.00                           |
| Texture      | positive  | 346 | 100.00    | 100.00    | 100.00    | 97.50                   | 96.30                   | 96.40                  | 96.40                   | 98.30                      | 98.30                     | 98.80               | 100.00                | 95.40                          |
| Texture      | negative  |  83 | 76.92     | 100.00    | 100.00    | 98.40                   | 98.60                   | 93.70                  | 94.70                   | 93.90                      | 96.40                     | 95.10               | 0.00                  | 96.30                          |
| Colour       | positive  | 622 | 97.10     | 96.23     | 94.12     | 98.10                   | 98.70                   | 97.20                  | 96.80                   | 97.70                      | 98.50                     | 97.20               | 100.00                | 96.40                          |
| Colour       | negative  |  54 | 100.00    | 100.00    | 100.00    | 92.00                   | 100.00                  | 94.10                  | 94.00                   | 96.30                      | 96.30                     | 98.10               | 0.00                  | 96.30                          |
| Stayingpower | positive  | 141 | 100.00    | 92.31     | 90.00     | 98.80                   | 93.70                   | 93.80                  | 96.50                   | 97.10                      | 98.60                     | 97.10               | 100.00                | 89.20                          |
| Stayingpower | negative  |  96 | 100.00    | 100.00    | 100.00    | 98.10                   | 98.70                   | 95.70                  | 98.50                   | 97.90                      | 96.80                     | 96.80               | 2.70                  | 97.80                          |
| Packing      | positive  | 282 | 98.18     | 98.04     | 100.00    | 97.80                   | 97.80                   | 98.60                  | 98.20                   | 99.30                      | 99.60                     | 98.90               | 100.00                | 99.60                          |
| Packing      | negative  |  10 | 100.00    | 100.00    | 100.00    | 100.00                  | 100.00                  | 90.00                  | 90.00                   | 100.00                     | 100.00                    | 90.00               | 0.00                  | 100.00                         |
| Shipping     | positive  | 334 | 100.00    | 98.44     | 98.41     | 97.80                   | 99.00                   | 98.40                  | 98.40                   | 97.90                      | 97.90                     | 97.30               | 98.80                 | 97.90                          |
| Shipping     | negative  | 174 | 100.00    | 100.00    | 92.86     | 96.90                   | 98.10                   | 93.40                  | 97.00                   | 98.20                      | 100.00                    | 98.80               | 97.00                 | 98.30                          |
| **MACRO**    | positive  |   — | 98.51     | 97.29     | 96.95     | 97.34                   | 97.40                   | 96.83                  | 97.20                   | 98.16                      | 98.59                     | 98.00               | 99.83                 | 96.29                          |
| **MACRO**    | negative  |   — | 77.66     | 85.71     | 77.55     | 97.30                   | 95.44                   | 94.36                  | 96.00                   | 86.44                      | 83.61                     | 82.39               | 14.24                 | 83.80                          |

## Bảng 6 — F1 theo khía cạnh và sắc thái (%, `paper`)

F1 là chỉ số kết hợp Precision và Recall. Vì vậy, nó thường dễ đọc hơn khi muốn nhìn tổng thể khả năng nhận diện một nhóm.

| Aspect       | Sentiment |   n | CB 0-shot | CB 1-shot | CB 5-shot | Qwen3-4B 0-shot (4-bit) | Qwen3-4B 1-shot (4-bit) | Qwen3-4B 5-shot (fp16) | Qwen3-4B 5-shot (4-bit) | CafeBERT head.train seed42 | CafeBERT head.train seed7 | Pb-large head.train | Pb-base Cross-Entropy | Pb-base Weighted Cross-Entropy |
| ------------ | --------- | --: | --------- | --------- | --------- | ----------------------- | ----------------------- | ---------------------- | ----------------------- | -------------------------- | ------------------------- | ------------------- | --------------------- | ------------------------------ |
| Smell        | positive  | 252 | 97.06     | 97.06     | 96.15     | 97.10                   | 98.40                   | 97.40                  | 97.50                   | 97.80                      | 98.20                     | 98.10               | 91.60                 | 97.50                          |
| Smell        | negative  |  48 | 66.67     | 66.67     | 50.00     | 87.40                   | 93.30                   | 88.00                  | 90.70                   | 89.10                      | 91.10                     | 91.30               | 0.00                  | 88.70                          |
| Price        | positive  | 321 | 98.59     | 100.00    | 100.00    | 98.10                   | 99.20                   | 98.70                  | 99.20                   | 99.50                      | 99.20                     | 99.10               | 99.20                 | 99.10                          |
| Price        | negative  |   6 | 0.00      | 0.00      | 0.00      | 26.70                   | 60.00                   | 46.20                  | 50.00                   | 40.00                      | 0.00                      | 0.00                | 0.00                  | 0.00                           |
| Texture      | positive  | 346 | 96.20     | 100.00    | 100.00    | 98.50                   | 97.90                   | 97.40                  | 97.50                   | 98.40                      | 98.70                     | 98.80               | 91.20                 | 97.20                          |
| Texture      | negative  |  83 | 86.96     | 100.00    | 100.00    | 94.60                   | 93.40                   | 90.20                  | 91.00                   | 93.30                      | 94.70                     | 95.10               | 0.00                  | 89.30                          |
| Colour       | positive  | 622 | 98.53     | 98.08     | 96.97     | 98.70                   | 99.40                   | 98.30                  | 98.10                   | 98.70                      | 99.10                     | 98.50               | 96.00                 | 98.00                          |
| Colour       | negative  |  54 | 87.50     | 85.71     | 80.00     | 86.00                   | 92.50                   | 82.80                  | 81.70                   | 86.70                      | 90.40                     | 85.50               | 0.00                  | 81.20                          |
| Stayingpower | positive  | 141 | 100.00    | 96.00     | 94.74     | 98.80                   | 96.10                   | 95.30                  | 97.60                   | 97.80                      | 98.20                     | 97.50               | 78.30                 | 93.60                          |
| Stayingpower | negative  |  96 | 100.00    | 88.89     | 88.89     | 98.10                   | 96.20                   | 93.70                  | 97.00                   | 96.90                      | 97.40                     | 96.30               | 5.30                  | 91.50                          |
| Packing      | positive  | 282 | 99.08     | 99.01     | 100.00    | 98.90                   | 98.90                   | 99.10                  | 98.90                   | 99.60                      | 99.80                     | 99.30               | 98.40                 | 99.80                          |
| Packing      | negative  |  10 | 80.00     | 80.00     | 100.00    | 75.00                   | 76.90                   | 78.30                  | 75.00                   | 90.00                      | 94.70                     | 81.80               | 0.00                  | 95.20                          |
| Shipping     | positive  | 334 | 100.00    | 99.21     | 94.74     | 98.10                   | 99.00                   | 97.50                  | 98.40                   | 98.50                      | 98.90                     | 98.30               | 98.60                 | 98.50                          |
| Shipping     | negative  | 174 | 100.00    | 98.11     | 94.55     | 96.30                   | 98.10                   | 95.10                  | 97.00                   | 97.10                      | 98.00                     | 96.80               | 97.30                 | 97.10                          |
| **MACRO**    | positive  |   — | 98.49     | 98.48     | 97.51     | 98.31                   | 98.41                   | 97.67                  | 98.17                   | 98.61                      | 98.87                     | 98.51               | 93.33                 | 97.67                          |
| **MACRO**    | negative  |   — | 74.45     | 74.20     | 73.35     | 80.59                   | 87.20                   | 82.04                  | 83.20                   | 84.73                      | 80.90                     | 78.11               | 14.66                 | 77.57                          |

## 1. Điểm mạnh của công bố tham chiếu

### 1.1. Model lớn tận dụng tốt khả năng hiểu ngữ nghĩa và làm theo hướng dẫn

Công bố dùng GPT-4o-mini với Chain-of-Thought và 0/1/5-shot. Model không được huấn luyện lại trên dữ liệu của bài toán mà dựa vào kiến thức đã học, khả năng hiểu ngữ nghĩa và các ví dụ được đưa vào prompt.

Điểm mạnh của phương pháp này là khi review có tín hiệu rõ ràng, model lớn có thể nhận ra mối liên hệ giữa nội dung review, khía cạnh và sắc thái mà không cần xây dựng một model riêng. Vì vậy, công bố có nhiều trường hợp đạt **100%** (`texture` và `price` ở 1-shot/5-shot, `shipping` và `stayingpower` ở 0-shot).

Các kết quả **100%** cho thấy GPT-4o-mini đã phân loại đúng toàn bộ các mẫu thuộc những nhóm đó trong phép đo của công bố. Đây là kết quả nổi bật, đặc biệt ở `texture` và `shipping` vì đây là các nhóm có số lượng mẫu tương đối lớn.

### 1.2. Few-shot có lợi khi cung cấp một lượng ví dụ phù hợp

Kết quả của công bố cho thấy việc đưa ví dụ vào prompt giúp cải thiện kết quả ở 1-shot. Accuracy macro tăng từ **97.36% ở 0-shot lên 97.70% ở 1-shot**, tương ứng **+0.34 pp**. F1 macro của `positive` gần như giữ nguyên (**98.49% → 98.48%**), trong khi F1 macro của `negative` giảm nhẹ (**74.45% → 74.20%**). Như vậy, lợi ích của 1-shot thể hiện rõ nhất ở Accuracy macro tổng thể.

Ở 5-shot, Accuracy macro đạt **96.74%**. Theo công bố, số lượng ví dụ lớn hơn làm prompt dài hơn và không tiếp tục mang lại lợi ích như 1-shot. Kết quả này cho thấy few-shot có hiệu quả khi lượng ví dụ được lựa chọn phù hợp; **nhiều ví dụ hơn không đồng nghĩa với kết quả tốt hơn**.

## 2. Điểm yếu của công bố tham chiếu

### 2.1. Công bố yếu rõ rệt ở nhóm negative

F1 macro của `positive` đạt **98.49% ở 0-shot, 98.48% ở 1-shot và 97.51% ở 5-shot**, nhưng `negative` chỉ đạt **74.45%, 74.20% và 73.35%**. Khoảng cách này cho thấy GPT-4o-mini nhận diện review tích cực ổn định hơn nhiều so với review tiêu cực trong chính cấu hình prompt được thử nghiệm.

Một nguyên nhân có thể thấy từ đặc điểm của bài toán là tín hiệu tiêu cực không phải lúc nào cũng được diễn đạt trực tiếp; chúng có thể phụ thuộc vào ngữ cảnh hoặc cách diễn đạt cụ thể. Prompt và các ví dụ few-shot của công bố chưa giúp model xử lý tốt đồng đều những trường hợp này. Kết quả ở `smell` negative giảm từ **66.67% xuống 50.00%** giữa các thiết lập 0-shot và 5-shot, còn `price` negative có **F1 = 0 ở cả ba thiết lập**. Số liệu không cho phép xác định một nguyên nhân duy nhất, nhưng cho thấy phương pháp prompt của công bố chưa xử lý ổn định các trường hợp tiêu cực này.

### 2.2. Một số kết quả 100% không đồng nghĩa với khả năng xử lý toàn bộ bài toán

Trong tập test **1.623 review**, `price` chỉ có **6 review tiêu cực** và `packing` chỉ có **10 review tiêu cực**. Vì vậy, những kết quả rất cao ở các nhóm có ít mẫu có độ ổn định thấp hơn so với các nhóm có nhiều mẫu.

Riêng `price` negative có **F1 = 0 ở cả 0, 1 và 5-shot**. Đây là một điểm yếu rõ của công bố ở nhóm này, dù chỉ có 6 mẫu nên kết quả riêng của nhóm `price` negative có độ ổn định thấp.

### 2.3. Phép đo của công bố chưa phản ánh đầy đủ khả năng xử lý review

Phép đo của công bố chỉ tính điểm trên những ô mà **nhãn thật và dự đoán cùng xác định một khía cạnh là positive hoặc negative**. Những ô mà model **dự đoán thiếu khía cạnh, dự đoán sai khía cạnh hoặc không tạo ra dự đoán đọc được** không được đưa vào mẫu số của Accuracy theo phép đo này.

Vì vậy, phép đo của công bố đánh giá tốt câu hỏi **“khi model đã đưa ra một dự đoán phù hợp để chấm, dự đoán đó đúng đến mức nào?”**, nhưng chưa phản ánh đầy đủ câu hỏi **“model có nhận diện đúng tất cả khía cạnh được nhắc tới trong review và có xử lý được cả những trường hợp dự đoán khó hay không?”**. Đây là giới hạn quan trọng khi dùng điểm số này để đánh giá toàn bộ khả năng xử lý review.

## 3. Điểm mạnh của dự án

### 3.1. Qwen3-4B xử lý nhóm negative tốt hơn trong cấu hình prompt đã thử nghiệm

Qwen3-4B có F1 macro của `negative` cao hơn công bố ở cả ba mức: **80.59% so với 74.45% ở 0-shot**, **87.20% so với 74.20% ở 1-shot** và **82.04% so với 73.35% ở 5-shot fp16**. Bản 5-shot 4-bit đạt **83.20%**.

Chênh lệch lớn nhất xuất hiện ở 1-shot: F1 macro của `negative` tăng **13 pp**, trong khi Accuracy macro chỉ tăng **0.07 pp** (từ **97.70% lên 97.77%**). Điều này cho thấy lợi thế của Qwen không đơn thuần là tăng điểm chung mà chủ yếu nằm ở khả năng cân bằng tốt hơn giữa Precision và Recall của nhóm tiêu cực.

Vì cả hai bên đều dùng phương pháp prompt, kết quả này không thể quy riêng cho việc Qwen có kích thước nhỏ hơn hay lớn hơn. Khác biệt có thể đến từ năng lực riêng của từng model và cách chúng diễn giải chỉ dẫn, CoT cùng ví dụ few-shot. Số liệu hiện có không tách riêng được mức đóng góp của từng yếu tố; kết luận chắc chắn là cấu hình Qwen đã thử nghiệm phân loại nhóm `negative` tốt hơn theo F1 trên tập test này.

### 3.2. Encoder được huấn luyện trực tiếp có lợi thế chuyên biệt hóa

CafeBERT seed7 đạt **98.26% Accuracy macro**, cao hơn **0.56 pp** so với mức cao nhất của công bố là **97.70%**. F1 macro cũng cao hơn ở cả hai nhóm: `positive` đạt **98.87%**, cao hơn mức cao nhất **98.49%** của công bố; `negative` đạt **80.90%**, cao hơn mức cao nhất **74.45%** của công bố.

Tuy nhiên, CafeBERT seed7 không vượt công bố ở mọi nhóm. Chẳng hạn, ở một số aspect mà công bố đã đạt kết quả rất cao, F1 của CafeBERT vẫn thấp hơn. Vì vậy, kết quả này cho thấy lợi thế của việc chuyên biệt hóa model cho bài toán, nhưng không có nghĩa model được huấn luyện đã thắng ở mọi aspect.

### 3.3. Weighted Cross-Entropy giúp tăng mức chú ý đến nhãn hiếm

Cross-Entropy là hàm mất mát dùng để đo mức độ sai của dự đoán trong quá trình huấn luyện. Weighted Cross-Entropy giữ nguyên nguyên tắc này nhưng **gán trọng số lớn hơn cho những lớp có ít mẫu**, nên lỗi ở lớp hiếm ảnh hưởng nhiều hơn đến quá trình cập nhật model.

Ví dụ, với **100 review tích cực và 10 review tiêu cực**, một model có thể đạt **Accuracy cao** nếu dự đoán đúng phần lớn review tích cực, dù bỏ sót nhiều review tiêu cực. Weighted Cross-Entropy làm cho các lỗi ở 10 review tiêu cực có trọng số lớn hơn, từ đó quá trình huấn luyện chú ý nhiều hơn đến nhóm này.

Kết quả của Dự án cho thấy tác động rõ rệt: với PhoBERT-base, Accuracy macro tăng từ **88.40% lên 96.62%**, tương ứng **+8.22 pp**, khi chuyển từ Cross-Entropy sang Weighted Cross-Entropy. Đồng thời, F1 macro của `negative` tăng mạnh từ **14.66% lên 77.57%**, tương ứng **+62.91 pp**. Ở `smell` negative, F1 tăng từ **66.67% lên 93.30%**; ở `stayingpower` negative tăng từ **88.89% lên 97.40%**. Như vậy, Weighted Cross-Entropy không chỉ cải thiện nhóm `negative` mà còn làm Accuracy tổng thể tăng đáng kể trong thí nghiệm này.

### 3.4. Phép đo `all` ngăn việc tăng điểm bằng cách kiêng trả lời

Ngoài phép đo của công bố để so sánh trực tiếp, Dự án sử dụng thêm phép đo `all`. Phép đo này giữ lại mọi ô có nhãn thật là positive hoặc negative, bao gồm cả ô không nhắc tới khía cạnh; dự đoán sai hoặc không đọc được vẫn được tính là sai và nằm trong mẫu số.

Cách tính này có hai ưu điểm quan trọng. **Model không thể tăng điểm chỉ bằng cách kiêng trả lời ở những ô khó**, vì ô không đọc được vẫn bị tính là sai. Đồng thời, **mẫu số được cố định theo nhãn thật**, không giảm đi khi model đưa ra ít dự đoán hợp lệ hơn. Nhờ vậy, điểm số giữa các model có cơ sở so sánh công bằng hơn. Phép đo `all` còn đánh giá `aspect_detection` — khả năng nhận diện đúng khía cạnh được nhắc tới — trong khi phép đo của công bố không đo phần này.

Dự án dùng phép đo `all` để lựa chọn model tốt nhất (`model/best`) và thực hiện dừng sớm dựa trên tập validation (`val`). Như vậy, đây không chỉ là một phép đo bổ sung để báo cáo; nó trực tiếp tham gia vào quá trình lựa chọn và huấn luyện model.

Hai thí nghiệm cho thấy vì sao cần phép đo này:

- **Qwen3-4B 5-shot fp16 và 4-bit:** cùng prompt và cùng lô dữ liệu, phép đo của công bố cho bản 4-bit **97.19% Accuracy**, cao hơn **96.48%** của fp16. Nhưng bản 4-bit chỉ có **2.375 ô** được tính điểm và thiếu **53 khía cạnh**, trong khi fp16 có **2.520 ô** và thiếu **14 khía cạnh**. Theo phép đo `all`, kết quả đảo chiều: fp16 đạt **94.31% Accuracy macro**, cao hơn **93.39%** của 4-bit. Điểm theo phép đo của công bố có thể trông cao hơn vì nhiều ô khó không đi vào mẫu số; phép đo `all` cho thấy bản 4-bit không thực sự tốt hơn trong đánh giá này.
- **PhoBERT-base với hai hàm mất mát:** khi chuyển từ Cross-Entropy sang Weighted Cross-Entropy, F1 macro của nhóm `negative` tăng từ **14.66% lên 77.57%**, trong khi Accuracy macro cũng tăng từ **88.40% lên 96.62%**. Trường hợp này cho thấy cần xem đồng thời chỉ số tổng thể và chỉ số theo từng sắc thái: chỉ nhìn Accuracy hoặc chỉ nhìn phép đo của công bố sẽ không thể hiện đầy đủ mức cải thiện ở nhóm tiêu cực.

Tóm lại, **phép đo của công bố dùng để đối chiếu với công bố; phép đo `all` cho biết model có thực sự xử lý được nhiều trường hợp hơn hay chỉ đạt điểm cao nhờ kiêng trả lời ở các ô khó**. Đây là một ưu điểm của phép đo và cũng là ưu điểm thực tế trong quy trình đánh giá, lựa chọn model của Dự án.

## 4. Điểm yếu của dự án

### 4.1. Một số aspect mà công bố đã rất mạnh vẫn có F1 cao hơn Dự án

Xét theo F1, công bố đạt **100%** ở `texture` negative trong 1-shot/5-shot và `price` positive trong 1-shot/5-shot. CafeBERT seed7 đạt **94.70%** ở `texture` negative và **99.20%** ở `price` positive. Như vậy, Dự án chưa tái hiện được toàn bộ kết quả rất cao của công bố ở những nhóm này.

Sự chênh lệch phù hợp với mục tiêu tối ưu khác nhau của hai phương pháp. GPT-4o-mini dự đoán trực tiếp theo prompt và có thể đạt kết quả rất cao ở những nhóm mà ngữ nghĩa thể hiện rõ; encoder được huấn luyện của Dự án học ranh giới phân loại từ dữ liệu huấn luyện và tối ưu theo mục tiêu huấn luyện chung, nên không bảo đảm đạt 100% ở từng aspect. Đồng thời, Dự án ưu tiên cải thiện nhóm `negative`, nơi công bố còn yếu. Đây là đánh đổi có chủ đích ở cấp độ kết quả, nhưng không có bằng chứng để quy mọi mức giảm ở từng aspect cho riêng việc ưu tiên F1 hay một thay đổi phương pháp duy nhất.

### 4.2. Một số hạn chế trong việc xử lý các nhóm ít mẫu vẫn còn tồn tại

Trong tập test **1.623 review**, `price` negative chỉ có **6 mẫu** và `packing` negative chỉ có **10 mẫu**. Vì vậy, các kết quả ở những nhóm này vẫn có độ ổn định thấp, tương tự hạn chế mà công bố gặp phải.

### 4.3. Một số kết quả theo phép đo của công bố vẫn phụ thuộc vào số lượng dự đoán đủ điều kiện để chấm

Qwen3-4B 5-shot 4-bit có Accuracy **97.19%** theo phép đo của công bố, cao hơn **96.48%** của bản 5-shot fp16. Tuy nhiên, bản 4-bit chỉ còn **2.375 ô** đủ điều kiện tính điểm, trong khi fp16 còn **2.520 ô**; số khía cạnh bị thiếu lần lượt là **53 và 14**.

Đây là hạn chế của chính phép đo mà Dự án sử dụng để đối chiếu với công bố: điểm số cao hơn có thể đi cùng với việc có ít ô được đưa vào tính điểm hơn. Thực tế, khi chuyển sang phép đo `all`, kết quả đảo chiều: fp16 đạt **94.31% Accuracy macro**, cao hơn **93.39%** của 4-bit. Vì vậy, kết quả theo phép đo của công bố không đủ để kết luận bản 4-bit thực sự tốt hơn bản fp16.

## Kết luận

### 5.1. Kết quả đối chiếu tổng thể

**Dự án vượt công bố chủ yếu ở đúng phần mà công bố còn yếu, đồng thời chấp nhận giảm một ít ở một số nhóm mà công bố đã làm rất tốt.** Phần cải thiện nổi bật đến từ encoder được huấn luyện cho bài toán cụ thể và cách xử lý nhãn hiếm.

### 5.2. Kết quả tốt nhất về Accuracy và F1

**CafeBERT head.train seed7 đạt 98.26% Accuracy macro**, cao hơn **0.56 pp** so với mức tốt nhất của công bố là **97.70%**. Về F1 macro, CafeBERT seed7 đạt **98.87% ở positive** và **80.90% ở negative**, đều cao hơn mức cao nhất tương ứng của công bố là **98.49%** và **74.45%**. Tuy nhiên, CafeBERT vẫn thấp hơn công bố ở một số aspect cụ thể.

### 5.3. Kết quả khi dùng prompt tương tự công bố

Qwen3-4B cũng cho thấy lợi thế rõ ở F1 của `negative`: **80.59% ở 0-shot, 87.20% ở 1-shot và 82.04% ở 5-shot fp16**, đều cao hơn công bố tương ứng là **74.45%, 74.20% và 73.35%**. Bản 5-shot 4-bit đạt **83.20%**.

Về Accuracy macro, Qwen3-4B đạt **97.26% ở 0-shot, 97.77% ở 1-shot và 96.48% ở 5-shot fp16**, tương ứng thấp hơn **0.10 pp**, cao hơn **0.07 pp** và thấp hơn **0.26 pp** so với công bố. Như vậy, lợi thế của Qwen khi dùng prompt thể hiện rõ hơn ở nhóm `negative` theo F1, còn Accuracy tổng thể chỉ tương đương công bố.

### 5.4. Vai trò của phép đo `all`

Phép đo của công bố cần thiết để so sánh trực tiếp với kết quả tham chiếu, nhưng có thể cho điểm cao hơn khi model không tạo ra dự đoán hợp lệ cho một số ô khó, vì các ô đó không được tính vào mẫu số. Phép đo `all` khắc phục điểm này: dự đoán sai hoặc không đọc được vẫn bị tính là sai, mẫu số cố định theo nhãn thật, đồng thời đánh giá thêm khả năng nhận diện khía cạnh.

Bằng chứng rõ nhất là cặp Qwen3-4B 5-shot: theo phép đo của công bố, bản 4-bit đạt **97.19% Accuracy**, cao hơn **96.48%** của fp16; theo phép đo `all`, fp16 đạt **94.31% Accuracy macro**, cao hơn **93.39%** của 4-bit. Bản 4-bit cũng có ít ô được tính điểm hơn (**2.375 so với 2.520**) và thiếu nhiều khía cạnh hơn (**53 so với 14**). Vì vậy, phép đo `all` giúp phân biệt model thực sự xử lý tốt hơn với model có điểm cao hơn do nhiều ô khó không được tính. Dự án dùng chỉ số này để chọn `model/best` và dừng sớm trên tập validation, thay vì lựa chọn model chỉ dựa vào điểm theo phép đo của công bố.

### 5.5. Cách diễn giải tổng thể

> **Hướng đi của Dự án không phải là thắng công bố ở mọi aspect. Dự án chấp nhận giảm một ít ở những nhóm công bố vốn đã rất mạnh để đổi lấy mức cải thiện lớn hơn ở những nhóm công bố còn yếu, đặc biệt là `negative`.**
>
> **Kết quả cho thấy sự đánh đổi này có hiệu quả: Accuracy macro cao hơn ở CafeBERT seed7, F1 của `negative` cao hơn rõ rệt ở cả Qwen3-4B và CafeBERT, trong khi một số aspect mà công bố đã đạt mức rất cao vẫn còn thấp hơn.**

Mức **98.26%** ở trên là kết quả theo **phép đo của công bố**, tức cùng cách đo được dùng để đối chiếu công bằng với công bố. Dự án sử dụng thêm phép đo `all` để đánh giá đầy đủ hơn khả năng xử lý review và lựa chọn model.

## 6. Nguồn và quy ước

- Số dự án: lấy từ `results/<hash8>/metrics.json` của TỪNG lượt (không lấy từ báo cáo tổng hợp).
- Số công bố: `data/reference_publication/accuracy_by_aspect.csv` (Table 3) và
  `prf_by_aspect_sentiment_{0,1,5}shot.csv` (Tables 4-6).
- Cơ sở đo: `paper` = lọc hai chiều (chỉ ô mà CẢ nhãn đúng và nhãn đoán là positive/negative) -
  đúng cách công bố đếm; `all` = của dự án (không dùng trong báo cáo này, trừ ghi chú).
- Mọi số lấy trên split `test` (1.623 dòng) trừ `exp017` (ghi rõ nếu dùng, ở đây không dùng).
- Cỡ nhiễu của ĐƯỜNG ENCODER đo 05/10/2026 là **±0,33 … ±0,67 điểm** (ba lượt chạy lại với
  `decoding.seed: 7`); lấy làm việc **±0,7** - chênh lệch dưới mức đó không kết luận.
- `cafebert/lora/exp002` (97,88) và `cafebert/lora/exp004` (98,26) là HAI lần rút thăm của **cùng một cấu
  hình** (chỉ khác hạt giống huấn luyện) - đọc như một khoảng **97,88 … 98,26** và là **đỉnh của dự án**.
- Số của ba bước kết hợp (mục 5b): `data/reports/fusion/` - luật router (`aspect_router_accuracy.json`,
  `aspect_router_f1am.json`), số router trên `val`/`test` (`router_aspect_*.json`), bản gộp hai tầng
  (`fuse_aspect_test.json`, `fuse_aspect_test_cafebert_exp001.json`, `fuse_aspect_test_cafebert_exp002.json`), và **đầu vào rút gọn** của mọi lượt tham gia ở
  `inputs/`. Lần chạy router ĐẦU chỉ có 2 ứng viên - luật của lần đó giữ ở các tệp hậu tố `_2model`.
