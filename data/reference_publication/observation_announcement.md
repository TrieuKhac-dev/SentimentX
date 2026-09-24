# Applying Prompt Engineering to Sentiment Analysis of Vietnamese Reviews

Đây là một **công bố tham chiếu quan trọng** cần được theo dõi trong quá trình phát triển dự án, đặc biệt về hướng **ABSA trên đánh giá sản phẩm tiếng Việt và sử dụng LLM + Prompt Engineering**.

## Kết quả chính

Công bố sử dụng **16.227 đánh giá son môi Shopee**, với **32.775 cặp aspect–sentiment**, đánh giá GPT-4o-mini bằng **Chain-of-Thought kết hợp 0-shot, 1-shot và 5-shot**.

Kết quả Accuracy theo aspect đạt:

- **0-shot:** 94,12–100%
- **1-shot:** 94,12–100%
- **5-shot:** 92,86–100%

Công bố cũng báo cáo Precision, Recall và F1 theo từng aspect và polarity.

## Vì sao cần theo dõi?

Đây là **mốc kết quả tham chiếu (benchmark)** cho dự án. Các kết quả, cách xây dựng dữ liệu, prompt và thiết lập thực nghiệm của công bố cần được quan sát để:

- Xác định khoảng cách giữa dự án và công bố hiện tại.
- Tìm điểm còn hạn chế để phát triển phương pháp tốt hơn.
- Thiết kế thực nghiệm chứng minh đóng góp của dự án.
- Tránh chỉ lặp lại cách tiếp cận đã được công bố.

**Mục tiêu của dự án:** xây dựng phương pháp có cơ sở thực nghiệm rõ ràng và **cải thiện vượt qua các kết quả tham chiếu của công bố này**, thay vì chỉ tái hiện kết quả.

> Lưu ý: Công bố loại **neutral** và **OTHERS** khỏi phần đánh giá chính, do đó các kết quả trên không đại diện cho toàn bộ bài toán ABSA đa lớp.
