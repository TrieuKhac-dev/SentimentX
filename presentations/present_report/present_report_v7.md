# Báo cáo phân tích định tính hai mô hình dẫn đầu (present_report_v7)

**Bài toán:** đánh giá cảm xúc theo khía cạnh trên bài đánh giá mỹ phẩm tiếng Việt · **Ngày:** 21/10/2026

Báo cáo giải thích vì sao hai mô hình có điểm cao nhất trong hai nhánh của `present_report_v6.md` vẫn mắc những lỗi có cấu trúc. Mọi số xếp hạng, mức chênh và điều kiện lọt bảng do v6 quy định; báo cáo không xếp hạng lại và không thay thế v6.

## Tóm tắt điều hành

Bối cảnh đánh giá gồm 1.623 review test, 7 khía cạnh và hai mô hình: CafeBERT + LoRA (Low-Rank Adaptation) `exp027` — điểm ước lượng tốt nhất của nhánh mô hình mã hoá — và Qwen3-4B + CoT (chuỗi suy luận) `exp009` — cột mô hình ngôn ngữ lớn tốt nhất trong v6. Trên cơ sở chấm của công bố, hai mô hình đạt 98,56 và 97,77. Hai con số này không nằm trên cùng một mẫu số, vì Qwen để 445 lần nhắc có nhãn chuẩn ra ngoài phép chấm, còn CafeBERT để 25 lần nhắc.

Câu hỏi trung tâm không phải mô hình nào cao hơn, mà là điểm cao có đồng nghĩa mô hình hiểu phần nào của review đang làm bằng chứng cho khía cạnh nào hay không. Kết quả định tính cho thấy câu trả lời là không hoàn toàn.

Ba phát hiện chính:

1. **Sao chép trung thành nhưng không tách ý theo khía cạnh.** Mô hình chép đúng câu chữ, nhưng khi một câu chứa hai ý cho hai khía cạnh, mô hình thường dùng cả câu cho cả hai và không buộc từng cụm từ vào đúng khía cạnh. Bài đánh giá số 44 là ví dụ điển hình: “hơi bện” nói về chất son, “không đều” nói về màu/độ phủ, nhưng cả hai dòng đều dùng chung một đoạn trích.
2. **Một khía cạnh có thể có nhiều nhận xét, nhưng đầu ra chỉ có một nhãn.** Cả hai mô hình trả một nhãn cho mỗi khía cạnh; mô hình mã hoá còn không thể cho biết lần nhắc nào đã đẩy nhãn. Trong 73 ô ứng viên có nhiều nhận xét, 43 đoạn trích của Qwen đã chứa cả tín hiệu tích cực lẫn tiêu cực nhưng mô hình vẫn chỉ phát ra một nhãn.
3. **Nhãn “không nhắc tới” đang bị quá tải.** Có 526/3.181 đoạn trích thật đi kèm nhãn này; 200 ô trung lập bị loại khỏi phép chấm; nhãn “không nhắc tới” đang được dùng cho cả ba trạng thái: không nhắc tới, trung lập và không chắc chắn.

Khuyến nghị chính là thay đổi cách biểu diễn đầu ra: cho phép nhiều kết quả trên mỗi khía cạnh, mỗi kết quả có span và sắc thái riêng; tách ba trạng thái “không nhắc tới”, “trung lập” và “không chắc chắn”; đánh giá ở mức span thay vì chỉ kiểm tra sự tồn tại của đoạn trích.

Ghi chú về thứ hạng: v6 là nguồn chuẩn cho xếp hạng và mức chênh. Bảy cột dẫn đầu trong v6 chỉ chênh nhau 0,25 điểm phần trăm, nhỏ hơn biên nhiễu; vì vậy “dẫn đầu” trong báo cáo này là nhãn mô tả, không phải kết luận khoa học.

## 1. Bối cảnh và phạm vi

### 1.1. Bài toán đánh giá cảm xúc theo khía cạnh

Bài toán đánh giá cảm xúc theo khía cạnh (aspect-based sentiment analysis, ABSA) yêu cầu mô hình trả lời, cho từng thuộc tính sản phẩm, thuộc tính đó được nhắc tới theo hướng nào. Một review son môi có thể khen màu, chê chất son, không nói gì về mùi, phàn nàn về vận chuyển và đánh giá cao giá tiền. Đầu ra đúng không phải một nhãn cảm xúc chung, mà là bảy nhãn gắn với bảy khía cạnh: màu, chất son, mùi, giá, vận chuyển, đóng gói và độ bền màu.

Mỗi khía cạnh có ba trạng thái: tích cực, tiêu cực hoặc không nhắc tới. Dữ liệu gốc còn có ô trung lập, nhưng nhóm này nằm ngoài cơ sở chấm chính. Sự phân biệt giữa “không nhắc tới” và “trung lập” quan trọng vì hai trạng thái này bị gộp trong nhiều đầu ra hiện tại, làm mất thông tin về việc mô hình có nhìn thấy tín hiệu hay không.

### 1.2. Vì sao chọn hai mô hình này

v6 xác định `exp027` là điểm ước lượng tốt nhất của nhánh mô hình mã hoá và `exp009` là cột mô hình ngôn ngữ lớn tốt nhất. Tuy vậy, bảy cột đầu chỉ chênh nhau 0,25 điểm phần trăm (98,56 → 98,31), nhỏ hơn biên nhiễu; “dẫn đầu” vì thế là cách gọi mô tả, không phải kết luận khoa học. Cặp này được chọn vì cấu trúc đối lập: một mô hình mã hoá chỉ trả nhãn, một mô hình ngôn ngữ lớn trả đoạn trích, lý do và nhãn, cho phép so sánh không chỉ độ chính xác mà còn khả năng quan sát bằng chứng.

### 1.3. Dữ liệu, mẫu số và biên nhiễu

Tập đánh giá gồm 1.623 review test, 7 khía cạnh, tương ứng 11.361 ô thô. Sau khi loại 200 ô trung lập, còn 11.161 ô trên cơ sở all. Trong 11.361 ô, có 2.769 ô mà nhãn chuẩn là tích cực hoặc tiêu cực; đây là mẫu số của accuracy mức mention.

Trên cơ sở paper, CafeBERT đạt 98,56 trên 2.744 ô; Qwen đạt 97,77 trên 2.324 ô. Hai mẫu số không giống nhau: Qwen để 445 lần nhắc có nhãn chuẩn ra ngoài, CafeBERT để 25 lần nhắc. Cơ chế của công bố chỉ tính ô khi cả nhãn chuẩn và nhãn đoán đều là tích cực hoặc tiêu cực; vì vậy một mô hình có thể nâng điểm bằng cách nói “không nhắc tới” thường xuyên hơn. Accuracy mức mention — tính trên toàn bộ 2.769 lần nhắc, coi “không nhắc tới” là sai — là 97,65 cho CafeBERT và 82,30 cho Qwen.

Biên nhiễu dùng trong toàn báo cáo: ±0,2 giữa hai lần chạy cùng cấu hình; ±0,7 giữa các lượt khác seed. Chênh lệch nhỏ hơn các mức này được ghi là cùng hạng, không kết luận.

### 1.4. Báo cáo này bổ sung gì

Báo cáo không tạo bảng xếp hạng mới. Phần đóng góp là mô tả định tính có bằng chứng về ba kiểu lỗi: sao chép văn bản nhưng không phân đoạn ngữ nghĩa, nén nhiều nhận xét vào một nhãn, và để một nhóm lớn đoạn trích đi kèm nhãn “không nhắc tới”. Các quan sát này giải thích vì sao điểm paper cao vẫn có thể đi kèm lỗ hổng biểu diễn.

## 2. Thuật ngữ và cách đọc số liệu

### 2.1. Bảng thuật ngữ

| Thuật ngữ | Định nghĩa | Ví dụ |
| --- | --- | --- |
| Khía cạnh (aspect) | Thuộc tính sản phẩm được đánh giá riêng. | Màu, chất son, mùi, giá, vận chuyển, đóng gói, độ bền màu. |
| Bài đánh giá (review) | Một nhận xét của người dùng về sản phẩm. | Một review son có thể nhắc màu, chất, mùi, giá. |
| Precision / Recall | Precision đo tỉ lệ báo đúng trong các lần báo có; recall đo tỉ lệ bắt được trong các trường hợp thật. | Báo 10 lần, đúng 8 → precision 80%; có 10 trường hợp thật, bắt 8 → recall 80%. |
| F1 | Trung bình điều hoà của precision và recall. | F1 cao khi mô hình vừa ít báo nhầm vừa ít bỏ sót. |
| Sắc thái (polarity) | Hướng đánh giá của một lần nhắc. | Tích cực, tiêu cực hoặc không nhắc tới. |
| Nhãn chuẩn (gold label) | Đáp án do người gán cho từng ô review × khía cạnh; có thể mơ hồ hoặc sai. | Cùng một câu có từ “bện” nhưng nhãn chuẩn vẫn có thể là không nhắc tới. |
| Đoạn trích (quote) | Phần văn bản mô hình sao lại từ review để làm bằng chứng. | “son lên môi hơi bện và không đều”. |
| Đoạn văn bản liên tục (span) | Một mạch chữ liền trong review; một đoạn trích có thể chứa nhiều span. | Trong câu trên, “hơi bện” là span về chất son, “không đều” là span về màu/độ phủ. |
| Lần nhắc (mention) | Một lần xuất hiện của một khía cạnh trong review. | “Màu 301 rất ok nhưng màu 102 rất bợt” có hai lần nhắc về màu. |
| Kiểu hành vi (pattern) | Cách xử lý lặp lại của mô hình khi đọc một đoạn trích. | Tách đúng hai ý; chỉ ghi nhận một ý; dùng lại đoạn trích cho khía cạnh khác. |
| Câu lệnh (prompt) | Văn bản hướng dẫn mô hình trả lời theo một khuôn dạng. | Câu lệnh yêu cầu liệt kê từng khía cạnh, trích đoạn và trả nhãn. |
| Lược đồ đầu ra (schema) | Quy định cấu trúc và các trường mà đầu ra phải có. | Một lược đồ có thể buộc mỗi khía cạnh trả danh sách span thay vì một nhãn. |
| Kiểm tra thủ công (audit) | Đọc và đối chiếu một mẫu đầu ra bằng người, không dựa hoàn toàn vào tự động. | Kiểm tra thủ công 60 đoạn trích đa khía cạnh để đo độ chính xác của bộ lọc. |
| Token (đơn vị từ) | Đơn vị nhỏ của văn bản sau khi tách từ; dùng khi quy công nhãn cho từng phần của review. | Cơ chế quy công ở mức token gắn nhãn với đúng cụm từ đã tạo ra nhãn. |
| Cơ sở paper | Cách chấm của công bố: chỉ tính ô mà cả nhãn chuẩn và nhãn đoán đều là tích cực hoặc tiêu cực. | Ô nhãn chuẩn tích cực, mô hình đoán tiêu cực vẫn được tính; ô nhãn chuẩn không nhắc tới bị loại. |
| Cơ sở all | Cách chấm mở rộng: tính cả ô “không nhắc tới”. | Ô nhãn chuẩn không nhắc tới, mô hình đoán tích cực được tính là lỗi. |
| Bảng chuyển đổi lỗi (confusion matrix) | Bảng đối chiếu nhãn chuẩn (hàng) với nhãn mô hình (cột); ô ngoài đường chéo là lỗi. | Hàng tích cực, cột không nhắc tới là số lần mô hình bỏ một nhận xét tích cực. |
| Ước lượng tự động (heuristic) | Phép đếm dựa trên từ khoá và quy tắc, dùng để sàng lọc chứ không phải nhãn chuẩn. | Đếm số đoạn trích chứa từ khoá mạnh của ít nhất hai khía cạnh. |
| Nhiều kết quả (multi-result) | Trả về danh sách đánh giá cho cùng một khía cạnh, mỗi đánh giá có span và sắc thái riêng. | Chất son: một span “mềm mịn” tích cực, một span “khó tán” tiêu cực. |
| Mô hình mã hoá (encoder) / Mô hình ngôn ngữ lớn (LLM) | Mô hình mã hoá đọc cả review và trả nhãn; mô hình ngôn ngữ lớn sinh văn bản gồm đoạn trích, lý do và nhãn. | CafeBERT trả 7 số nguyên; Qwen viết đoạn trích, lý do rồi trả 7 số nguyên. |
| Accuracy macro / mức mention / exact-review | Macro là trung bình trên 7 khía cạnh; mức mention tính trên toàn bộ lần nhắc chuẩn; exact-review là tỉ lệ review khớp cả 7 khía cạnh. | Một review chỉ khớp toàn bộ khi cả 7 nhãn đều đúng, kể cả các ô không nhắc tới. |

Trong dữ liệu gốc, các nhãn được mã hoá là 0, 1, 2: không nhắc tới = 0, tích cực = 1, tiêu cực = 2. Dữ liệu còn dùng mã 3 cho ô trung lập; 200 ô như vậy bị loại khỏi cơ sở paper. Báo cáo dùng chữ thay cho mã để người đọc ngoài dự án không phải tra bảng.

### 2.2. Cách đọc số

Báo cáo dùng dấu phẩy thập phân (98,56), dấu chấm phân cách hàng nghìn (2.744) và “pp” cho điểm phần trăm. Các tỉ lệ được giữ như trong nguồn, không tính lại. Con số nào là ước lượng tự động đều được ghi rõ; không có kiểm định ý nghĩa thống kê, và các đợt kiểm tra thủ công do một người đọc. Vì vậy các phép đếm ước lượng tự động chỉ dùng để sàng lọc, không dùng làm nhãn chuẩn.

Cần phân biệt ba mẫu số. Cơ sở paper dùng 2.744 ô với CafeBERT và 2.324 ô với Qwen. Cơ sở all dùng 11.161 ô sau khi bỏ 200 ô trung lập. Accuracy mức mention dùng 2.769 lần nhắc có nhãn chuẩn. Một con số chỉ có nghĩa khi đi kèm mẫu số của nó.

## 3. Hai mô hình và bức tranh lỗi tổng quát

### 3.1. Nhận diện hai mô hình

| Mô hình / phương pháp | Mã băm (hash) | Accuracy macro (paper) | Ô paper (đúng/tổng) | Accuracy mức mention | Exact-review | Lỗi cơ sở all | Chi phí |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| CafeBERT + LoRA `r=16`, 6 epoch (6 vòng huấn luyện), không lượng hoá | `43e40f61` | 98,56 | 2.704/2.744 | 97,65 | 1.288/1.623 = 79,36% | 200 | 3.763,7 giây huấn luyện; 2.301 bước; mốc tốt nhất ở bước 2.000 (87%) |
| Qwen3-4B-Instruct-2507, CoT 1-shot (một ví dụ), lượng hoá 4-bit, lô 4 (batch 4) | `7cf3331e` | 97,77 | 2.279/2.324 | 82,30 | 962/1.623 = 59,27% | 727 (4 ô không đọc được) | 10.001,2 giây; 356.007 token; 219,4 token/review |

Exact-review là tỉ lệ review khớp cả 7 khía cạnh, kể cả các ô “không nhắc tới”; Qwen thấp hơn một phần vì mô hình bỏ nhiều lần nhắc. Khác biệt với khoá `exact_match` trong `metrics.json` được ghi ở Phụ lục C.

### 3.2. Cảnh báo mẫu số

Hai điểm paper không đo cùng một tập ô. CafeBERT phát ra sắc thái cho 2.744 trong 2.769 lần nhắc có nhãn chuẩn, bỏ qua 25 lần nhắc. Qwen phát ra sắc thái cho 2.324 ô, bỏ qua hoặc không đọc được 445 ô. Vì cơ sở paper loại mọi ô mà một trong hai phía là “không nhắc tới”, điểm của Qwen chỉ là độ chính xác có điều kiện: trong số các ô mà mô hình đã chọn nêu sắc thái, 97,77% là đúng. Trên toàn bộ lần nhắc, con số tương ứng là 82,30. Với CafeBERT, 98,56% được tính trên 2.744 trong 2.769 lần nhắc; mức mention là 97,65.

Cơ chế lọc hai chiều tạo ra một điểm mù: mô hình có thể tăng điểm paper bằng cách nói “không nhắc tới” nhiều hơn, vì các ô bị bỏ không còn nằm trong mẫu số. Đây không phải lỗi của một mô hình cụ thể mà là thuộc tính của giao thức chấm. Mọi so sánh giữa hai mô hình phải nêu rõ mẫu số và đọc kèm accuracy mức mention.

### 3.3. Bảng chuyển đổi lỗi

Bảng dưới là dạng rút gọn của bảng chuyển đổi lỗi: chỉ hiển thị các ô sai, bỏ các ô đúng trên đường chéo. Cách đọc là “nhãn chuẩn → nhãn mô hình”. Bảng tính trên 11.161 ô của cơ sở all, sau khi loại 200 ô trung lập.

| Nhãn chuẩn → Nhãn mô hình | CafeBERT | Qwen |
| --- | ---: | ---: |
| không nhắc tới → tích cực | 112 | 173 |
| không nhắc tới → tiêu cực | 23 | 61 |
| tích cực → không nhắc tới | 17 | 382 |
| tiêu cực → không nhắc tới | 8 | 62 |
| tích cực → tiêu cực | 24 | 38 |
| tiêu cực → tích cực | 16 | 7 |
| không đọc được | 0 | 4 |
| **Tổng lỗi** | **200** | **727** |

Dòng “không đọc được” là 4 ô Qwen trả về trống hoặc không có nhãn, không phải một nhãn dự đoán. Bốn ô này được tính vào tổng lỗi nhưng không nằm trong cột chuyển đổi nào.

### 3.4. Hai hướng sai trái ngược

CafeBERT gán thừa. Mô hình báo có nhắc tới khi nhãn chuẩn nói không nhắc tới trong 112 trường hợp tích cực và 23 trường hợp tiêu cực, tổng cộng 135 lần báo thừa. Ở chiều ngược lại, mô hình bỏ 17 nhận xét tích cực và 8 nhận xét tiêu cực, tổng cộng 25 lần bỏ sót. Với mô hình mã hoá, lỗi nghiêng về việc thêm tín hiệu không có trong nhãn chuẩn.

Qwen bỏ sót. Mô hình nói “không nhắc tới” khi nhãn chuẩn có sắc thái trong 382 trường hợp tích cực và 62 trường hợp tiêu cực, tổng cộng 444 lần bỏ sót, cộng thêm 4 ô không đọc được. Chiều ngược lại có 173 báo thừa tích cực và 61 báo thừa tiêu cực, tổng cộng 234. Với LLM, lỗi nghiêng về việc im lặng trước tín hiệu có thật.

Cần phân biệt 445 với cột “→ không nhắc tới”. Con số 445 là chênh lệch mẫu số paper (2.769 − 2.324), không phải tổng của cột “→ không nhắc tới”. Trong 4 ô không đọc được, không phải ô nào cũng có nhãn chuẩn là tích cực hoặc tiêu cực; vì vậy không thể cộng trực tiếp 382, 62 và 4 để được 445.

Cả hai đều đảo chiều. CafeBERT đảo 24 nhận xét tích cực thành tiêu cực và 16 nhận xét tiêu cực thành tích cực. Qwen đảo 38 và 7. Đây là lỗi hiểu sai hướng, không chỉ bỏ sót hoặc thêm nhãn.

### 3.5. Hệ quả

Hai mô hình sai theo hai hướng khác nhau, nên điểm paper không so sánh trực tiếp được. Qwen đạt 97,77 với điều kiện đã phát ra một sắc thái; nếu tính cả các lần nhắc bị bỏ, mức đúng là 82,30. CafeBERT đạt 98,56 trên 2.744 trong 2.769 lần nhắc. Đây là khác biệt cấu trúc về cách mô hình đối xử với “không nhắc tới”, không phải một bảng xếp hạng. v6 vẫn là nơi quy định thứ hạng và mức chênh.

## 4. Phát hiện 1 — Mô hình trích đúng nhưng không tách được ý theo khía cạnh

Phần này trình bày một hiện tượng với hai biểu hiện: dùng lại cùng một đoạn trích cho hai khía cạnh, và trích cả một câu gộp nhiều khía cạnh rồi gán một nhãn cho một khía cạnh. Hai biểu hiện trông khác nhau nhưng có cùng một nguyên nhân: mô hình sao chép được văn bản nhưng chưa gắn được từng phần nhỏ của câu với ngữ nghĩa khía cạnh. Đây không phải hiện tượng đoạn trích bị bịa; mọi đoạn trích trong mục này đều tồn tại trong review.

### 4.1. Ví dụ điển hình: bài đánh giá số 44

Bài đánh giá số 44, nguyên văn:

> Son lên môi hơi bện và không đều, nhưng tiền nào của đấy, xài cũng ổn 1 tí nên ok

Ba dòng suy luận của Qwen cho ba khía cạnh:

| Khía cạnh | Đoạn trích | Lý do mô hình đưa ra | Nhãn |
| --- | --- | --- | --- |
| Chất son | “son lên môi hơi bện và không đều” | cảm giác bện và không đều cho thấy chất son không tốt | tiêu cực |
| Màu | “son lên môi hơi bện và không đều” | không có thông tin về màu sắc | không nhắc tới |
| Giá | “tiền nào của đấy” | câu chỉ ngầm nói giá hợp lý, chưa đủ rõ chiều đánh giá | không nhắc tới |

Nhãn chuẩn của review 44 là chất son không nhắc tới, màu không nhắc tới và giá tích cực. CafeBERT dự đoán chất son tiêu cực, giá tích cực và màu không nhắc tới. Như vậy CafeBERT bắt được tín hiệu giá mà Qwen bỏ qua, nhưng lại gán tiêu cực cho chất son trong khi nhãn chuẩn không ghi nhận khía cạnh này.

Câu review chứa hai ý khác nhau. “Hơi bện” mô tả chất son; “không đều” mô tả màu hoặc độ phủ. Mô hình dùng cả câu cho cả hai khía cạnh. Ở dòng màu, mô hình trích đúng câu đó nhưng kết luận “không có thông tin về màu sắc” và gán “không nhắc tới”. Đây không phải lỗi sao chép: đoạn trích có thật. Lỗi nằm ở phân đoạn ngữ nghĩa (semantic segmentation): mô hình không chia câu thành hai span và không buộc mỗi span vào đúng khía cạnh.

Nhãn chuẩn cũng gán “không nhắc tới” cho cả chất son và màu. Đây là một biên chú thích riêng, có thể vì người gán coi cả câu là một nhận xét chung hoặc vì quy ước gán nhãn không tách câu. Biên chú thích này không làm thay đổi điểm ngữ nghĩa: câu vẫn chứa hai tín hiệu thuộc hai khía cạnh, và mô hình vẫn dùng chung một đoạn cho cả hai.

Kết luận: hai biểu hiện — dùng lại một đoạn cho hai khía cạnh và trích cả câu gộp nhiều khía cạnh — có cùng một nguyên nhân là mô hình chưa phân tách được ngữ nghĩa theo khía cạnh.

### 4.2. Kết quả trên toàn bộ dữ liệu

| Chỉ số | Giá trị | Ghi chú |
| --- | ---: | --- |
| Đoạn trích thật (không phải “không nhắc tới”) | 3.181 | Mẫu số của các tỉ lệ trong mục này |
| Đoạn trích có tín hiệu mạnh cho ít nhất hai khía cạnh | 220 (6,9%) | Ước lượng tự động; tương ứng 187 review (11,5%) |
| Kiểm tra thủ công 60 đoạn trích đa khía cạnh | 53/60 = 88,3% | 7 dương tính giả; một người đọc |
| Nhóm (review, đoạn trích chuẩn hoá) dùng lại cho ít nhất hai khía cạnh | 53 nhóm / 109 dòng (3,4% số dòng trích dẫn) | Kiểm tra thủ công toàn bộ 53 nhóm |
| Trong 53 nhóm: đoạn trích thật sự mang tín hiệu cho hai khía cạnh | 15/53 | Kiểm tra thủ công |
| Trong 53 nhóm: dùng lại không phù hợp | 38/53 | Đoạn chỉ đúng một khía cạnh hoặc không đúng khía cạnh nào |
| Cặp khớp mờ ở ngưỡng 0,9 | 61 cặp / 52 review | Con số 53 nhóm khớp chính xác là con số vững hơn |
| Đoạn trích không chứa tín hiệu của chính khía cạnh | 368/3.181 (11,6%) | Ước lượng tự động |
| Đoạn trích không chứa tín hiệu nào | 260/3.181 (8,2%) | Ước lượng tự động |

Hai con số 53 xuất hiện ở hai phép đếm khác nhau. “53/60” là số đoạn đúng trong đợt kiểm tra 60 đoạn. “53 nhóm” là số nhóm (review, đoạn trích chuẩn hoá) bị dùng lại cho ít nhất hai khía cạnh. Không nên cộng hoặc so trực tiếp hai con số này.

Phân bố cặp dùng lại nhiều nhất: màu và chất son 57; độ bền màu và chất son 35; màu và độ bền màu 32; mùi và chất son 23; màu và mùi 17; đóng gói và vận chuyển 16; màu và vận chuyển 14; đóng gói và chất son 12; giá và chất son 9; đóng gói và mùi 8. Phần còn lại có không quá 5 cặp.

Các đoạn trích đa khía cạnh dài hơn và giống mệnh đề hơn. Trung vị là 29 ký tự, 7 từ và 37,8% có nhiều mệnh đề; đoạn một khía cạnh có trung vị 18 ký tự, 4 từ và 15,4% nhiều mệnh đề. Chênh lệch tương ứng khoảng 1,6 lần về độ dài và 2,5 lần về tỉ lệ nhiều mệnh đề. Điều này phù hợp với giả thuyết rằng câu càng gộp nhiều ý thì mô hình càng dễ dùng chung một đoạn cho nhiều khía cạnh.

Có 368 đoạn trích (11,6%) không chứa tín hiệu của chính khía cạnh mà nó được gắn vào, và 260 đoạn (8,2%) không chứa tín hiệu khía cạnh nào. Nhận xét: mô hình sao chép văn bản tốt, nhưng đoạn trích không phải lúc nào cũng là bằng chứng hợp lệ cho khía cạnh đi kèm. Việc kiểm tra “đoạn trích có tồn tại trong review” không đủ để kết luận “đoạn trích làm bằng chứng cho nhãn”.

### 4.3. Năm kiểu hành vi khi đọc phần suy luận

| Kiểu hành vi | Mô tả | Ví dụ |
| --- | --- | --- |
| Tách đúng hai ý | Đoạn trích chứa tín hiệu cho hai khía cạnh và mô hình gán đúng cả hai. | 706: “chất bột” cho chất son, “nhanh trôi” cho độ bền màu, cả hai tiêu cực. 1127: “hộp móp do vận chuyển” cho vận chuyển và đóng gói, cả hai tiêu cực. |
| Chỉ ghi nhận một ý, bỏ qua ý còn lại | Đoạn trích có hai tín hiệu nhưng mô hình chỉ ghi nhận một, khía cạnh kia bị gán không nhắc tới. | 46, 810, 781, 1135. |
| Dùng lại đoạn trích của khía cạnh này cho khía cạnh khác | Đoạn trích chỉ đúng một khía cạnh nhưng bị dùng cho khía cạnh thứ hai. | 149: đoạn chỉ nói về màu, bị dùng cho chất son và độ bền màu. 124: một câu hỏi không mang thông tin bị dùng cho bốn khía cạnh. |
| Dùng tiêu đề hoặc từ khoá làm bằng chứng | Đoạn trích mở bằng tiêu đề khía cạnh; mô hình không coi phần sau là phát biểu. | 1345: “Độ bền màu:” được trích nhưng mô hình kết luận không có phát biểu về độ bền. |
| Đoạn trích và nhãn mâu thuẫn | Đoạn trích có mặt, nhưng nhãn là không nhắc tới. | 44 (màu), 781 (màu), 1135 (mùi và chất son). |

Kiểu thứ nhất là đối chứng dương: dùng lại một đoạn không tự động sai. Review 706 dùng “chất bột và nhanh trôi” cho chất son và độ bền màu, cả hai tiêu cực, nhãn chuẩn cũng tiêu cực cho cả hai. Review 1127 dùng “Hộp hơi móp cho do bên vận chuyển” cho vận chuyển và đóng gói, cả hai tiêu cực; đoạn thật sự chứa tín hiệu vận chuyển và tín hiệu bao bì, nhưng nhãn chuẩn chỉ gán vận chuyển tiêu cực, đóng gói không nhắc tới. Đây là biên chú thích, không phải đoạn trích bịa.

Kiểu thứ hai xảy ra khi mô hình có tín hiệu nhưng không quy công. Review 46 dùng cùng một đoạn “Màu V21 lúc đánh chất kem sẽ đặc và lâu khô hơn so với 901” cho độ bền màu và chất son; chất son được gán tiêu cực, độ bền màu vẫn không nhắc tới. Đoạn này nói về chất son và bề mặt (đặc, lâu khô), nên dùng nó cho độ bền màu là kéo tín hiệu sang khía cạnh khác. Review 810 có bốn dòng khía cạnh xoay quanh hai tiêu đề “Kết cấu:” và “Độ bền màu:”; chỉ màu được gán tích cực. Review 781 trích “mùi thơm màu khá đẹp” cho cả mùi (tích cực) và màu (không nhắc tới), dù “màu khá đẹp” là tín hiệu màu rõ. Review 1135 trích “son thơm mịn lắm nha” cho cả chất son và mùi, cả hai đều bị gán không nhắc tới, dù “thơm” và “mịn” là hai tín hiệu tích cực.

Kiểu thứ ba là dùng lại đoạn trích không đúng khía cạnh; review 149 dùng một đoạn chỉ nói về màu cho chất son và độ bền màu, cả hai không nhắc tới, còn review 124 dùng câu hỏi “ch dùng kb lên màu như nào” cho bốn khía cạnh, tất cả không nhắc tới.

Kiểu thứ tư liên quan đến tiêu đề: review 1345 trích “độ bền màu: màu lên cũng không lì lắm nên dùng vẫn okii” rồi kết luận không có phát biểu về độ bền; tiêu đề tự nó không phải tín hiệu, còn “không lì” là ca biên.

Kiểu thứ năm là đoạn trích và nhãn mâu thuẫn, như review 44 ở dòng màu, review 781 ở dòng màu và review 1135 ở hai dòng mùi, chất son; đây là nhóm 526 trường hợp được phân tích ở mục 5.3.

Năm kiểu hành vi không phải năm lỗi rời rạc. Chúng là biến thể của cùng một vấn đề: mô hình đối xử với đoạn trích như một túi từ, không phải một tập hợp đơn vị nghĩa được gắn với khía cạnh.

### 4.4. Nhận xét và hệ quả

Mô hình sao chép chính xác ở mức cao. Sau chuẩn hoá Unicode, chữ hoa/thường và khoảng trắng, 96,35% đoạn trích khớp với review. Nhưng mô hình không phân đoạn “hơi bện” và “không đều”. Đây không phải vấn đề bỏ sót (recall): tín hiệu đã nằm trong đoạn trích. Đây là vấn đề biên khía cạnh và quy công.

Phần lý do do mô hình sinh ra đôi khi thừa nhận điều đó. Ở review 44, ngay sau khi trích một tín hiệu màu, dòng màu ghi “không có thông tin về màu sắc”. Mâu thuẫn này cho thấy mô hình nhìn thấy chuỗi nhưng không quyết định được chuỗi đó có thuộc khía cạnh hay không. Hệ quả cho thiết kế câu lệnh là phải yêu cầu tín hiệu tối thiểu cho từng khía cạnh, cấm dùng lại cùng một đoạn trích và buộc có một span riêng cho mỗi khía cạnh. Hệ quả cho đánh giá là phải kiểm tra tính duy nhất của span và độ khớp giữa span với tín hiệu khía cạnh, không chỉ kiểm tra sự tồn tại của đoạn trích.

## 5. Phát hiện 2 — Một khía cạnh, nhiều nhận xét, nhưng chỉ một nhãn

### 5.1. Vì sao cần nhiều kết quả

Một review có thể vừa khen vừa chê cùng một khía cạnh. Người viết có thể thích một tông màu và chê tông còn lại; thấy chất son mềm nhưng khó tán; thấy mùi ban đầu hắc nhưng về sau dễ chịu; thấy đóng gói sơ sài nhưng hộp không móp. Trong các trường hợp này, một nhãn duy nhất cho khía cạnh không biểu diễn được toàn bộ nhận xét. Câu trả lời đúng về mặt biểu diễn là một danh sách kết quả, mỗi kết quả gồm một span và một sắc thái.

| Review | Khía cạnh | Đoạn trích | Nhãn mô hình | Nhãn chuẩn | Diễn giải |
| ---: | --- | --- | --- | --- | --- |
| 1064 | Màu | “màu 301 xinh xỉu”, “màu k giống ảnh nhìn chán lắm” | tiêu cực | trung lập | Hai tông màu, hai chiều; mô hình nén thành một nhãn. |
| 551 | Màu | “màu 301 rất ok nhưng màu 102 rất bợt” | không nhắc tới | trung lập | Khen một tông, chê tông kia; mô hình bỏ cả hai. |
| 494 | Chất son | “chất son mềm mịn hơn dòng cũ nhưng vẫn khá khó tán” | không nhắc tới | tích cực | Khen và chê trong một câu; mô hình bỏ cả hai. |
| 758 | Đóng gói | “đóng gói sơ sài nhưng vỏ son không bị móp” | tiêu cực | trung lập | Chê đóng gói, khen vỏ; mô hình chỉ giữ vế chê. |
| 1179 | Chất son; mùi | “chất son hơi khô nhưng rất mềm và mịn”; “mùi thơm” | không nhắc tới; không nhắc tới | tích cực; tích cực | Tín hiệu tích cực ở cả hai khía cạnh bị bỏ. |
| 976 | Màu; chất son | “lên màu chuẩn”; “bặm môi cái là bị không đều nữa” | tích cực; tiêu cực | tích cực; không nhắc tới | “Không đều” bị đẩy sang chất son thay vì màu/độ phủ. |
| 1125 | Mùi | “mùi ban đầu hơi hắc nhưng sau đó thơm” | tích cực | tích cực | Giữ được kết luận nhưng mất vế tiêu cực ban đầu. |
| 891 | Màu | “son xinh xỉu nha” | tiêu cực | tích cực | Đoạn trích khen, nhãn chê: mâu thuẫn giữa đoạn trích và nhãn. |

“Trung lập” trong bảng tương ứng mã 3 của dữ liệu gốc. Đây là nhóm 200 ô bị loại khỏi cơ sở paper; nhãn này không đồng nghĩa với “không nhắc tới”. Review 71 là một ca phụ: đoạn trích “son mịn” mang nghĩa tích cực, nhưng lý do mô hình dẫn “hơi bột” và gán tiêu cực; nhãn chuẩn là trung lập. Ca này cho thấy ngay cả khi đoạn trích tồn tại, lý do và nhãn có thể lấy từ một phần khác của câu.

Định dạng đề xuất là một danh sách cho mỗi khía cạnh, mỗi phần tử gồm span và sắc thái. Với khía cạnh không xuất hiện, trả trạng thái “không nhắc tới”; với trường hợp có tín hiệu nhưng không rõ chiều, trả “trung lập” hoặc “không chắc chắn”. Cách biểu diễn này giữ được thông tin mà một nhãn duy nhất đang phá huỷ.

### 5.2. Bằng chứng định lượng

| Chỉ số | Giá trị | Ghi chú |
| --- | ---: | --- |
| Ô (review, khía cạnh) có ít nhất hai lần nhắc đánh giá | 245 | 15,1% nếu quy theo 1.623 dòng; không phải số review duy nhất; ước lượng tự động |
| Trong đó: cùng sắc thái | 149 | Ước lượng tự động |
| Trong đó: ngược sắc thái | 96 | Ngưỡng thấp; kiểm tra thủ công cho độ chính xác của bộ lọc khoảng 20–25% |
| 50 review đọc mù | 5/50 = 10% | Khoảng tin cậy 95% xấp xỉ 4–21% |
| Kiểm tra thủ công 30 ứng viên | 14/30 = 46,7% | 16/82 ô ứng viên là nhãn chuẩn trung lập |
| Qwen trên 73 ô ứng viên có dự đoán sắc thái | 43/73 = 58,9% | Đoạn trích có cả tín hiệu tích cực và tiêu cực nhưng mô hình vẫn một nhãn |
| Qwen trên 73 ô ứng viên có dự đoán sắc thái: một chiều | 30/73 = 41,1% | 27 đúng chiều, 3 ngược chiều; ước lượng tự động |

Con số 245 là số ô (review, khía cạnh) có ít nhất hai lần nhắc đánh giá theo bộ từ khoá. Nếu quy theo 1.623 dòng thì tương đương 15,1%, nhưng đây không phải số review duy nhất và cũng không phải nhãn chuẩn. Trong 245 ô, 149 ô có cùng sắc thái và 96 ô có sắc thái ngược. Con số 96 là ngưỡng thấp: kiểm tra thủ công cho thấy chỉ khoảng 20–25% ứng viên là trường hợp ngược chiều thật, nên đây là giới hạn dưới của hiện tượng chứ không phải số lượng đầy đủ.

Đợt đọc mù 50 review cho 5/50 = 10% review có ít nhất một trường hợp cùng khía cạnh nhưng khác chiều, khoảng tin cậy 95% xấp xỉ 4–21%. Đợt kiểm tra thủ công 30 ứng viên cho 14/30 = 46,7% là trường hợp thật; 16/82 ô ứng viên có nhãn chuẩn trung lập. Hai đợt kiểm tra này có mục đích khác nhau: một ước lượng tỉ lệ trong review, một kiểm tra độ chính xác của bộ lọc ứng viên. Vì mẫu nhỏ và chỉ một người đọc, các con số chỉ nên dùng để định hướng.

Trên 73 ô ứng viên có dự đoán sắc thái của Qwen, 43 đoạn trích (58,9%) chứa cả tín hiệu tích cực và tiêu cực nhưng mô hình vẫn chỉ phát ra một nhãn. 30 trường hợp còn lại (41,1%) là một chiều: 27 đoạn đúng với nhãn, 3 đoạn ngược với nhãn. Không nên suy rộng 41,1% cho toàn bộ 3.181 đoạn trích, vì 73 ô này là tập ứng viên được chọn theo tiêu chí có nhiều lần nhắc.

Nhận xét: mô hình thường đã có cả hai vế trong đoạn trích. Vấn đề không nằm ở việc mô hình không nhìn thấy thông tin, mà ở chỗ lược đồ một nhãn buộc nó phải chọn một phía. Thông tin bị mất ở bước biểu diễn, sau khi mô hình đã trích đúng văn bản.

### 5.3. “Trích dẫn nhưng gán nhãn không nhắc tới”

Có 526 trong 3.181 đoạn trích thật (16,5%) đi kèm nhãn “không nhắc tới”. Đây không phải lỗi sao chép: đoạn trích tồn tại trong review. Đây là vấn đề quyết định và quy công: mô hình không xác định được đoạn trích có thuộc khía cạnh hay không, hoặc có nên coi đó là một đánh giá hay không.

Review 44 là ví dụ trung tâm. Đoạn trích chứa “hơi bện” (chất son) và “không đều” (màu/độ phủ). Mô hình dùng cả đoạn cho cả hai khía cạnh; dòng màu nói “không có thông tin về màu sắc” và gán “không nhắc tới”. Đây là nhầm lẫn phân đoạn ngữ nghĩa, không phải bịa đoạn trích.

526 trường hợp được chia thành bốn nhóm. Có 224 trường hợp bỏ sót tín hiệu tích cực (42,6%) và 38 trường hợp bỏ sót tín hiệu tiêu cực (7,2%): mô hình nhìn thấy bằng chứng nhưng không cam kết một sắc thái. Có 168 trường hợp (31,9%) mà theo người gán, đoạn trích không phải là một lần nhắc thật. Có 96 trường hợp (18,3%) nhãn chuẩn là trung lập, nhưng câu lệnh không có lựa chọn trung lập. Đây là phép đếm trực tiếp từ dữ liệu dự đoán, không phải ước lượng tự động.

Review 27 là một ví dụ khác: đoạn trích “vs giá đó thì ko mong nhiều” bị gán “không nhắc tới” cho giá, trong khi nhãn chuẩn là tích cực. Câu nói gián tiếp về giá bị mô hình coi là không đủ căn cứ.

Nhãn “không nhắc tới” vì thế đang bị quá tải: nó được dùng cho ba tình huống khác nhau là khía cạnh thật sự không xuất hiện, khía cạnh có tín hiệu nhưng trung lập hoặc mơ hồ, và khía cạnh có tín hiệu nhưng mô hình do dự.

Ở mức dữ liệu, 200 ô trung lập thuộc 177 review bị loại khỏi phép chấm. Có 96/184 ô trung lập có đoạn trích được mô hình gán “không nhắc tới” (52,2%). Đây là vấn đề của lược đồ nhãn, không phải hành vi riêng của mô hình: đầu ra không có mã trung lập nên mô hình buộc phải chọn một trong các nhãn còn lại.

Cần nêu thêm độ mơ hồ của nhãn chuẩn. Ở review 94 và 88, cả hai mô hình chọn sắc thái hiển nhiên theo ngữ nghĩa nhưng ngược với nhãn chuẩn; nhiều khả năng đây là nhiễu hoặc mơ hồ chú thích, không phải lỗi riêng của mô hình mã hoá. Trong 40 lỗi paper của CafeBERT, Qwen đúng ở 11 trường hợp, sai cùng chiều ở 16 và không đưa ra nhãn ở 13. Như vậy chỉ 11 lỗi là riêng của CafeBERT; 16 lỗi là lỗi chung, còn 13 trường hợp Qwen bỏ qua. Một phần lỗi vì thế là lỗi chung hoặc lỗi do nhãn, không phải đặc trưng của mô hình mã hoá.

### 5.4. Giới hạn của mô hình mã hoá

CafeBERT xuất 7 số nguyên; không có đoạn trích, không có lý do, không có span. Tệp `probabilities.csv` chỉ có xác suất cho ba nhãn (không nhắc tới, tích cực, tiêu cực) ở từng khía cạnh. Mô hình không thể nói lần nhắc nào đã đẩy nhãn, và người đọc cũng không có bằng chứng để kiểm tra.

Trên 82 ô ứng viên cùng khía cạnh nhưng khác chiều, CafeBERT đạt 58/63 = 92,06% trên cơ sở paper, so với 98,69% trên 2.681 ô còn lại. Cả 5 lỗi paper của tập con đều là tích cực → tiêu cực, thuộc các review 155, 552, 805, 1219 và 1240. Xác suất lớn nhất trung bình là 0,775; có một trường hợp 0,993. Đây là tập con được chọn và chỉ có 5 lỗi, nên kết quả chỉ mang tính mô tả, không đủ để suy luận thống kê.

Mô hình còn quá tự tin. Trên toàn bộ 40 lỗi paper, 65% có xác suất lớn nhất từ 0,90 trở lên; 35% từ 0,99 trở lên; 4 lỗi có xác suất lớp sai làm tròn 1,000. Độ tin cậy vì thế không dùng được để phát hiện review có nhiều lần nhắc hoặc mơ hồ.

Hai ví dụ về mùi cho thấy giới hạn biểu diễn rõ hơn. Review 1209 chê mùi vỏ son nhưng nói mùi son không có vấn đề; CafeBERT gán mùi tiêu cực, nhãn chuẩn là tích cực. Review 1531 nói son không có mùi nhưng vỏ nồng; CafeBERT gán tiêu cực, Qwen gán không nhắc tới, nhãn chuẩn là tích cực. Mô hình mã hoá không biểu diễn được mùi thuộc vật nào. Đoạn trích của Qwen có thể nêu tên vật, nhưng nhãn vẫn thường gộp hai vật vào một khía cạnh.

### 5.5. Vì sao có nhận định CafeBERT “kém hơn” trên review đa khía cạnh?

Cơ sở của nhận định là so sánh các tập con. Trên tập đa khía cạnh (có ít nhất hai khía cạnh được nhắc tới), accuracy paper của CafeBERT là 98,47% so với 98,97% trên tập một khía cạnh, chênh 0,50 điểm phần trăm. Trên tập đa sắc thái (có cả tích cực và tiêu cực), accuracy là 98,17% so với 98,97%, chênh 0,80 điểm phần trăm. Số lỗi tương ứng là 36/2.354 ô ở tập đa khía cạnh so với 4/390 ô ở tập một khía cạnh; và 16/875 ô ở tập đa sắc thái so với 4/390 ô ở tập một khía cạnh. Quy đổi phần trăm: 1,53% so với 1,03%, và 1,83% so với 1,03%. Đây là phép tính đứng sau nhãn “kém hơn”.

Nhận xét: các chênh lệch này nhỏ và không đủ để tạo một kết luận mạnh. Mức chênh chỉ 0,50–0,80 điểm phần trăm; số lỗi tuyệt đối nhỏ (36 so với 4; 16 so với 4); mẫu số của tập một khía cạnh chỉ có 390 ô; và chiều chênh không nhất quán khi tách theo sắc thái. Chênh lệch accuracy mức mention chỉ 0,08–0,33 điểm phần trăm. Vì vậy báo cáo mô tả đây là một khác biệt nhỏ có tính mô tả, không phải phát hiện vững; không dùng nó để nói “CafeBERT kém hơn nhiều trên review đa khía cạnh”.

Điểm yếu có cơ sở hơn là giới hạn cấu trúc: mô hình mã hoá không có trường bằng chứng, nên với một review có nhiều lần nhắc, mô hình không thể nói lần nhắc nào đã tạo ra nhãn. Đây là hạn chế định tính, độc lập với khoảng chênh 0,50–0,80 điểm phần trăm.

Kết luận: nếu chỉ dựa trên bảng, có thể nói CafeBERT “kém hơn” theo nghĩa hẹp; nhưng mức chênh nhỏ và số lỗi ít nên báo cáo không dùng đây làm kết luận mạnh. Điểm yếu có cơ sở hơn là thiếu khả năng quy công.

### 5.6. Đề xuất định dạng nhiều kết quả

```json
{
  "texture": [
    {"span": "chất son mềm mịn hơn dòng cũ", "polarity": "positive"},
    {"span": "vẫn khá khó tán", "polarity": "negative"}
  ],
  "colour": [
    {"span": "màu 301 rất ok", "polarity": "positive"},
    {"span": "màu 102 rất bợt", "polarity": "negative"}
  ],
  "price": {"status": "not_mentioned"}
}
```

Trong ví dụ trên, `span` là đoạn văn bản chính xác được trích từ review; `polarity` là tích cực hoặc tiêu cực; `status` là trạng thái không nhắc tới, trung lập hoặc không chắc chắn. Với mô hình mã hoá, cần cơ chế quy công ở mức token; nếu không, nhiều nhãn sẽ không kiểm tra được.

Các yêu cầu đặt lên câu lệnh gồm: liệt kê tất cả lần nhắc cho mỗi khía cạnh; mỗi lần nhắc là một span tối thiểu; không dùng lại span; nếu có cả tích cực và tiêu cực thì trả cả hai; dùng `not_mentioned` thay cho nhãn “không nhắc tới”; và cho phép trạng thái `uncertain` khi tín hiệu không đủ rõ.

## 6. So sánh mô hình mã hoá và mô hình ngôn ngữ lớn

| Tiêu chí | CafeBERT `exp027` | Qwen `exp009` |
| --- | --- | --- |
| Dạng đầu ra | 7 số nguyên | đoạn trích + lý do + 7 số nguyên |
| Bằng chứng | không có | đoạn trích văn bản tự do |
| Nhiều kết quả | không | không, nhưng đoạn trích có thể chứa cả hai vế |
| Quy công đa khía cạnh | không thể | có thể trong văn bản, nhưng thường bị nén |
| Độ tin cậy | xác suất cho ba nhãn, quá tự tin | không có độ tin cậy hiệu chuẩn trong văn bản |
| Mẫu số paper | 2.744 | 2.324 |
| Không đưa ra nhãn (abstention) | 25 | 445 |
| Accuracy mức mention | 97,65 | 82,30 |
| Khả năng nhìn thấy lỗi | vô hình, mô hình vẫn tự tin | nhìn thấy được, nhưng phải kiểm tra thủ công |
| Rủi ro chính | quy công ngầm | đoạn trích chọn lọc và mâu thuẫn giữa đoạn trích với nhãn |

Không nên nói “mô hình mã hoá kém hơn” hoặc “mô hình ngôn ngữ lớn tốt hơn”. v6 là nguồn chuẩn cho xếp hạng, và điểm paper của hai mô hình rất gần nhau. Khác biệt có ý nghĩa là khả năng kiểm tra thủ công: mô hình mã hoá không cung cấp bằng chứng, còn mô hình ngôn ngữ lớn cung cấp bằng chứng nhưng bằng chứng thường một chiều hoặc mâu thuẫn. Cho mục tiêu nhiều kết quả, cả hai chưa đủ; đầu ra của LLM là điểm khởi đầu tốt hơn vì đã có span.

Giới hạn của mô hình mã hoá có thể diễn đạt bằng một câu đơn giản. Nếu review nói “màu trên tay đẹp nhưng trên môi không đều”, một nhãn duy nhất không thể nói phần nào tích cực và phần nào tiêu cực. Ngay cả khi mở rộng mô hình để trả hai nhãn, nếu không có span thì vẫn không biết nhãn nào gắn với cụm từ nào.

## 7. Khuyến nghị

### 7.1. Lược đồ đầu ra

Cần thay một nhãn cho mỗi khía cạnh bằng một danh sách kết quả, mỗi kết quả gồm span và sắc thái. Ba trạng thái “không nhắc tới”, “trung lập” và “không chắc chắn” phải tách khỏi tích cực/tiêu cực. Nếu có thể, thêm vị trí ký tự (char offset) cho span để việc kiểm tra thủ công không phụ thuộc vào so khớp chuỗi.

### 7.2. Câu lệnh cho mô hình

Câu lệnh phải yêu cầu tín hiệu tối thiểu cho từng khía cạnh, liệt kê tất cả lần nhắc, không dùng lại span và trả cả hai sắc thái khi review có cả hai. Nên quy định một lược đồ JSON rõ ràng và có trường bỏ qua (abstain) khi mô hình không đủ căn cứ. Yêu cầu này biến việc “chọn một nhãn” thành việc “liệt kê bằng chứng”.

### 7.3. Dữ liệu

Cần chú thích span và nhiều sắc thái cho cùng một khía cạnh, thay vì chỉ một nhãn. Nhãn trung lập phải được giữ lại trong quá trình huấn luyện hoặc ít nhất trong quá trình đánh giá. Nên bổ sung quy ước quy công cho các trường hợp sản phẩm và vỏ/hộp, đồng thời xử lý các nhãn chuẩn mơ hồ bằng một bước phân xử.

### 7.4. Mô hình

Với LLM, cần ràng buộc đầu ra theo lược đồ để mỗi khía cạnh trả danh sách span và sắc thái. Với mô hình mã hoá, cần cơ chế quy công ở mức token; nếu không, nhiều nhãn sẽ không kiểm tra được. Một hướng kết hợp là dùng span của LLM và nhãn của mô hình mã hoá, nhưng chỉ khi có bước đối chiếu.

### 7.5. Đánh giá

Cần báo cáo precision, recall và F1 ở mức span; accuracy mức mention; tỉ lệ đoạn trích hợp lệ; và tỉ lệ nhất quán giữa đoạn trích với nhãn. Mọi bảng nên ghi cả cơ sở paper và cơ sở all hoặc mức mention. Không nên xếp hạng chỉ bằng điểm paper, vì cơ chế lọc hai chiều che mất khác biệt về “không nhắc tới”.

### 7.6. Ngắn hạn và dài hạn

Trong ngắn hạn, có thể bổ sung bước kiểm tra tính nhất quán giữa đoạn trích và nhãn, đo xem bao nhiêu ô trở nên biểu diễn được, và kiểm tra thủ công các khía cạnh độ bền màu và chất son. Trong dài hạn, cần một lược đồ chú thích mới. Không nên kỳ vọng thêm epoch hoặc sửa câu lệnh sẽ giải quyết vấn đề lược đồ, vì điểm nghẽn nằm ở cách biểu diễn chứ không ở số bước huấn luyện.

## 8. Kết luận

Bốn kết luận chính:

1. Cả hai mô hình mạnh trên cơ sở paper nhưng đều nén nhiều lần nhắc vào một nhãn cho mỗi khía cạnh.
2. Qwen sao chép văn bản tốt nhưng không tách được các span theo khía cạnh: trong 53 nhóm dùng lại đoạn trích, chỉ 15 nhóm là hai tín hiệu thật, 38 nhóm là dùng lại không phù hợp.
3. Có 526 đoạn trích đi kèm nhãn “không nhắc tới”; đây là vấn đề quy công và lược đồ nhãn, không phải lỗi sao chép. Việc tách “không nhắc tới”, “trung lập” và “không chắc chắn” là điều kiện để nhãn này có nghĩa.
4. Mô hình mã hoá không có bằng chứng và còn quá tự tin; cải thiện chính nằm ở lược đồ nhiều kết quả và đánh giá mức span.

| Kết luận có cơ sở | Kết luận cần tránh |
| --- | --- |
| Cả hai mô hình mạnh trên paper nhưng gộp nhiều lần nhắc vào một nhãn. | “CafeBERT kém hơn nhiều trên review đa khía cạnh.” Mức chênh chỉ 0,50–0,80 điểm phần trăm; số lỗi 36 so với 4 và 16 so với 4; chiều chênh không nhất quán khi tách theo sắc thái. |
| Qwen sao chép văn bản nhưng không tách tiểu span; 15/53 nhóm là hai tín hiệu thật, 38/53 là dùng lại không phù hợp. | “Qwen trích dẫn trung thực.” Trong 73 ô ứng viên, 41,1% đoạn trích chỉ một chiều; còn có mâu thuẫn giữa đoạn trích và nhãn. |
| 526 đoạn trích đi kèm “không nhắc tới”; nhãn này đang gộp ba trạng thái. | “Chỉ cần tăng epoch hoặc sửa câu lệnh.” Đây là vấn đề lược đồ biểu diễn, không phải tối ưu tham số. |
| Lược đồ nhiều kết quả và đánh giá mức span là hướng cải thiện chính. | — |

Kết luận dành cho người đọc ngoài dự án: điểm cao đo mức đồng thuận với giao thức gán nhãn, không đo mức hiểu đầy đủ về nhiều lần nhắc trong cùng một review. Bước tiếp theo không phải tăng điểm paper, mà là biểu diễn được nhiều đánh giá cho một khía cạnh và đánh giá ở mức span.

## Phụ lục A — Phương pháp, bộ từ khoá và kiểm tra thủ công

### A.1. Bộ từ khoá khía cạnh và sắc thái

| Khía cạnh | Tín hiệu chính (ví dụ) | Ca nhiễu |
| --- | --- | --- |
| Màu (`colour`) | màu, lên màu, tông, sắc, đều màu, bợt, chuẩn màu | “không đều” vừa nói về màu vừa nói về bề mặt |
| Chất son (`texture`) | mịn, mượt, khô, bột, lỏng, đặc, kem, tán, bết, vón | “bện”, “lì” |
| Mùi (`smell`) | mùi, thơm, hôi, hắc, nồng, nhẹ, socola | mùi của vỏ so với mùi của son |
| Giá (`price`) | giá, tiền, rẻ, đắt, đáng tiền, “tiền nào của đấy” | “ok” không nhất thiết nói về giá |
| Vận chuyển (`shipping`) | giao, ship, vận chuyển, nhanh, chậm, lâu | “hộp móp” do vận chuyển |
| Đóng gói (`packing`) | đóng gói, bao bì, hộp, vỏ, móp, sơ sài, cẩn thận | “packaging” viết sai |
| Độ bền màu (`stayingpower`) | lì, bền, trôi, bám, giữ màu, lâu, phai | “lì” là bề mặt hay độ bền? |

Bộ tín hiệu sắc thái gồm từ tích cực/tiêu cực, phủ định, dấu hiệu tương phản như “nhưng”, “mà”, “có điều”, và mức độ. Đây là ước lượng tự động dựa trên từ khoá, không phải mô hình suy luận ngôn ngữ tự nhiên. Các từ “lì”, “bền” và “không đều” mơ hồ giữa các khía cạnh; vì vậy mọi phép đếm dựa trên chúng chỉ dùng để sàng lọc.

### A.2. Giới hạn của phương pháp

Độ chính xác của bộ lọc đoạn trích đa khía cạnh là 88,3% trên 60 đoạn được kiểm tra thủ công; độ chính xác của bộ lọc ứng viên cùng khía cạnh khác chiều là 46,7% trên 30 ứng viên. Cả hai là ước lượng từ mẫu nhỏ, do một người đọc, không có kiểm định ý nghĩa thống kê. Các con số này không đại diện cho toàn bộ dữ liệu và không nên được trích dẫn như tỉ lệ quần thể.

### A.3. Các đợt kiểm tra thủ công

Đợt thứ nhất đọc 60 đoạn trích được bộ lọc đánh dấu là đa khía cạnh, nhằm đo độ chính xác của bộ lọc. Đợt thứ hai đọc 30 ứng viên cùng khía cạnh nhưng khác chiều, nhằm phân biệt trường hợp thật với trường hợp do nhãn trung lập hoặc do nhiễu. Đợt thứ ba đọc mù 50 review, không dựa vào danh sách ứng viên, nhằm ước lượng tỉ lệ review có ít nhất một trường hợp cùng khía cạnh khác chiều. Ba đợt này bổ sung cho nhau nhưng không thay thế một nghiên cứu có nhiều người gán nhãn.

## Phụ lục B — Bảng ví dụ

| Review | Khía cạnh | Đoạn trích rút gọn | Nhãn mô hình | Nhãn chuẩn | Kiểu hành vi |
| ---: | --- | --- | --- | --- | --- |
| 44 | Chất son; màu | “son lên môi hơi bện và không đều” | tiêu cực; không nhắc tới | không nhắc tới; không nhắc tới | Đoạn trích có thật nhưng nhãn màu là không nhắc tới; dùng chung một đoạn cho hai khía cạnh. |
| 46 | Độ bền màu; chất son | “đặc và lâu khô hơn so với 901” | không nhắc tới; tiêu cực | không nhắc tới; không nhắc tới | Đoạn nói về chất son/bề mặt bị dùng lại cho độ bền màu. |
| 149 | Chất son; độ bền màu | “lên tay nhìn như đỏ cam...” | không nhắc tới; không nhắc tới | không nhắc tới; không nhắc tới | Đoạn chỉ nói về màu bị dùng cho hai khía cạnh khác. |
| 693 | Độ bền màu; chất son | “ghi son lì nhưng lau tí là trôi” | tiêu cực; tiêu cực | tiêu cực; không nhắc tới | Hai tín hiệu, nhưng mô hình mở rộng sang chất son quá mức. |
| 706 | Độ bền màu; chất son | “chất bột và nhanh trôi” | tiêu cực; tiêu cực | tiêu cực; tiêu cực | Hai tín hiệu, tách đúng; đối chứng dương. |
| 1125 | Mùi | “mùi ban đầu hơi hắc nhưng sau đó thơm” | tích cực | tích cực | Một nhãn cho hai vế; mất vế tiêu cực ban đầu. |
| 859 | Mùi | “son thơm” | không nhắc tới | tích cực | Đoạn trích tích cực nhưng nhãn không nhắc tới. |
| 1209 | Mùi | “mùi của vỏ son hơi ghê” | tiêu cực | tích cực | Nhầm mùi vỏ với mùi son. |
| 1531 | Mùi | “hình như ko có mùi” / “vỏ son mùi khá nồng” | không nhắc tới | tích cực | Nhầm mùi vỏ với mùi son; mô hình bỏ tín hiệu tích cực. |
| 1345 | Độ bền màu | “độ bền màu: ... không lì lắm” | không nhắc tới | trung lập | Tiêu đề bị dùng làm bằng chứng; “không lì” là ca biên. |
| 1064 | Màu | “màu 301 xinh xỉu”, “màu k giống ảnh...” | tiêu cực | trung lập | Hai tông màu, hai chiều; một nhãn. |
| 494 | Chất son | “mềm mịn hơn dòng cũ nhưng vẫn khá khó tán” | không nhắc tới | tích cực | Khen và chê trong một câu; mô hình bỏ cả hai. |

Mọi nhãn trong bảng đã được đối chiếu với `predictions.csv`. “Trung lập” là mã 3 của dữ liệu gốc và bị loại khỏi cơ sở paper; “không nhắc tới” là mã 0.

## Phụ lục C — Nguồn, kiểm lại và các lưu ý về số cũ

| Việc | Tệp hoặc khoá |
| --- | --- |
| Điểm paper | `metrics.json`, khoá `scores_paper` (cells, correct, accuracy macro) |
| Phân tích lỗi | `metrics.json`, khoá `tables.confusion`; đối chiếu `mispredictions.csv` |
| Đoạn trích, lý do, nhãn | `predictions.csv`, các cột `câu trả lời`, `nhãn đúng`, `nhãn đoán` |
| Xác suất của mô hình mã hoá | `probabilities.csv` (xác suất cho không nhắc tới, tích cực, tiêu cực) |
| Nghĩa các cột | `docs/04_experiments/05_predictions.md` |

Số trong báo cáo này là mô tả. v6 là nguồn chuẩn cho xếp hạng và mức chênh; nếu có khác biệt về một con số xếp hạng, v6 thắng.

Một số lưu ý khi kiểm lại:

- Số cũ của v5: v5 mục 9.1 ghi `exp027` có 211 lỗi. Đó là lượt bị ngắt rồi chạy tiếp; bản liền mạch `43e40f61` có 200 lỗi. Không dùng lại 211.
- Loại ô trung lập: 200 ô, phân bố giống nhau ở hai lượt, là quy ước dữ liệu chứ không phải hành vi mô hình.
- So sánh `exp009` với `exp003`: chênh cấu hình lô +0,05, nằm trong biên nhiễu; không dựng “hiện tượng kích thước lô” từ chênh lệch này.
- Kiểm tra chéo: `mispredictions.csv` có đúng 200 dòng với CafeBERT và 727 dòng với Qwen, khớp số lỗi trên cơ sở all; `metrics.json` cho `cells` và `correct` khớp với các bảng.
- Khoá `exact_match` trong `metrics.json` dùng định nghĩa hẹp hơn exact-review 7/7: nó chỉ đối chiếu các ô mà cả nhãn chuẩn và nhãn đoán đều nêu sắc thái. Báo cáo dùng exact-review 7/7, tính cả các ô “không nhắc tới” và bỏ qua 4 ô không đọc được của Qwen.
