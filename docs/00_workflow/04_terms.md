# 04. Thuật ngữ

> Đọc file này khi: gặp một từ không rõ nghĩa trong tài liệu hoặc trong code.
>
> Liên quan: `docs/05_config/01_paths.md`, `docs/04_experiments/metrics.md`

## Các nhóm việc của dự án

Tài liệu này **không dùng cách gọi "pha 1, pha 2, pha 3"**. Mỗi nhóm việc được gọi theo tên
công việc và theo thư mục tài liệu:

| Nhóm tài liệu         | Việc                                                      |
| --------------------- | --------------------------------------------------------- |
| `docs/01_dataset`     | dữ liệu gốc: file, cách đặt tên, phiên bản                |
| `docs/02_eda`         | đo lường dữ liệu: dữ liệu đang như thế nào                |
| `docs/03_pipeline`    | xử lý dữ liệu: làm sạch và tạo dataset                    |
| `docs/04_experiments` | thí nghiệm: tiền xử lý cho model, chạy model, chấm metric |

Nếu gặp tài liệu cũ ghi "xử lý dữ liệu" hay "tiền xử lý cho model" thì hiểu là: "xử lý dữ liệu" là xử lý dữ liệu,
"tiền xử lý cho model" là tiền xử lý cho model.

## Hai loại preprocessing, không được lẫn

|                             | Xử lý dữ liệu                                   | Tiền xử lý cho model                                                               |
| --------------------------- | ----------------------------------------------- | ---------------------------------------------------------------------------------- |
| Trả lời câu hỏi             | Làm sạch và chuyển dạng dữ liệu gốc             | Chuẩn bị đầu vào cho một model ở một thí nghiệm cụ thể                             |
| Code                        | `src/pipeline/`                                 | `src/preprocessing/`                                                               |
| Config                      | `configs/pipeline/<v>.yaml`                     | `configs/models/<model_id>.yaml`, và config riêng của thí nghiệm có thể ghi đè lên |
| Kết quả                     | `data/processed/<mã>/pipeline/`                 | `data/reports/model_input/` và số đo trong thư mục kết quả                         |
| Đi vào mã phiên bản dữ liệu | có                                              | không, chỉ vào `config_sha256`                                                     |
| Ví dụ                       | lọc trùng, chuẩn hoá teencode, chuyển dạng ABSA | tách từ, tokenizer, dựng prompt, cắt `max_length`, lược neutral                    |

## Hai mã dùng để tra cứu

| Tên                  | Là gì                                                                                                                                                                     | Nằm ở đâu                                                                    |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| mã phiên bản dữ liệu | Chuỗi định danh một phiên bản dataset, dạng `<name>-ds<version>-pl<pipeline_version>-src<nguồn>@<phiên bản>-<hash8>`, ví dụ `cosmetics-ds0.3.0-pl0.2.0-srccosmetics@0.2.0-9c0d1e2f` | Tên thư mục `data/processed/<mã>/` và trường `data.ma` trong `run_meta.json` |
| `config_sha256`      | Dấu vân tay của config đã hợp nhất, cộng văn bản prompt đã hợp nhất. Đổi config hoặc đổi câu chữ prompt thì dấu vân tay đổi                                               | Trường `config_sha256` trong `run_meta.json`                                 |

## Từ khoá

| Từ          | Nghĩa                                                                                                                                              |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| raw         | dữ liệu gốc, mỗi phiên bản một thư mục `data/raw/<name>/<raw_version>/`                                                                            |
| dataset     | kết quả sau khi raw đi qua pipeline                                                                                                                |
| thí nghiệm  | một định nghĩa gồm config, prompt, examples, notebook; định danh bằng `expNNN`                                                                     |
| lần chạy    | một lần thực thi một thí nghiệm trên một phiên bản dữ liệu; thư mục `results/<mã>/`                                                                |
| attempt     | một lần thử trong cùng một lần chạy: `fresh` hoặc `resume`                                                                                         |
| ghim code   | ghi sha của commit vào notebook để luôn kéo đúng bản đó                                                                                            |
| role        | vai của một split: `train`, `val`, `eval`                                                                                                          |
| detection   | quyết định nhị phân "khía cạnh này có được nhắc tới hay không"                                                                                     |
| polarity    | sắc thái của một khía cạnh: positive, negative, neutral                                                                                            |
| label space | tập nhãn dùng cho huấn luyện và đánh giá: `binary` hoặc `full`                                                                                     |
| eval_lock   | dấu vân tay của tập đánh giá, dùng để chặn việc đổi tập test                                                                                       |
| valid       | kết quả có được dùng hay không. Điều kiện: commit đã ghim nằm trên nhánh `experiment`, và khi merge vào nhánh `experiment` không phải sửa file nào |
| comparable  | kết quả có so được với công bố tham chiếu hay không                                                                                                |
| report      | bảng tổng hợp sinh tự động trong `data/reports/`                                                                                                   |
| shard       | một file số liệu nhỏ, ghi một lần, dùng để sinh report                                                                                             |
