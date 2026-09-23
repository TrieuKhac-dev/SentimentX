# 04. Thuật ngữ

> Đọc file này khi: gặp một từ không rõ nghĩa trong tài liệu hoặc trong code.
> Liên quan: `docs/05_config/*` · `docs/04_experiments/metrics.md`

## Hai loại "preprocessing" — không được lẫn

| | Xử lý dữ liệu (pha 2) | Tiền xử lý cho model (pha 3) |
|---|---|---|
| Trả lời câu hỏi | Làm sạch và chuyển dạng dữ liệu gốc | Chuẩn bị đầu vào cho một model cụ thể |
| Code | `src/pipeline/` | `src/preprocessing/` |
| Cấu hình | `configs/pipeline/<v>.yaml` | `configs/models/<model_id>.yaml` |
| Kết quả | `data/processed/<mã>/pipeline/` | `data/reports/model_input/` và số đo trong thư mục kết quả |
| Đi vào mã phiên bản | có | không, chỉ vào `config_sha256` |
| Ví dụ | lọc trùng, chuẩn hoá teencode, chuyển dạng ABSA | tách từ, tokenizer, dựng prompt, cắt `max_length`, lược neutral |

## Từ khoá

| Từ | Nghĩa |
|---|---|
| raw | dữ liệu gốc, mỗi phiên bản một thư mục `data/raw/<name>/<raw_version>/` |
| dataset | kết quả sau khi raw đi qua pipeline |
| mã phiên bản dữ liệu | `<name>-ds<version>-pl<pipeline_version>-src<nguồn>@<phiên bản>-<hash8>` |
| thí nghiệm | một định nghĩa gồm config, prompt, examples, notebook; định danh bằng `expNNN` |
| lần chạy | một lần thực thi một thí nghiệm trên một phiên bản dữ liệu; thư mục `results/<mã>/` |
| attempt | một lần thử trong cùng một lần chạy: `fresh` hoặc `resume` |
| ghim code | ghi sha của commit vào notebook để luôn kéo đúng bản đó |
| vai (role) | `train`, `val`, `eval`: dùng split nào cho việc gì |
| detection | quyết định nhị phân "khía cạnh này có được nhắc tới hay không" |
| polarity | sắc thái của một khía cạnh: positive, negative, neutral |
| label space | tập nhãn dùng cho huấn luyện và đánh giá: `binary` hoặc `full` |
| eval_lock | dấu vân tay của tập đánh giá, dùng để chặn việc đổi tập test |
| valid | kết quả có được dùng hay không: sha phải nằm trên `experiment` và merge không sửa tệp |
| comparable | kết quả có so được với công bố tham chiếu hay không |
| report | bảng tổng hợp sinh tự động trong `data/reports/` |
| shard | một tệp số liệu nhỏ, ghi một lần, dùng để sinh report |
