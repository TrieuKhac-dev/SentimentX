# SentimentX - mục lục tài liệu

> Đọc file này khi: cần tìm một tài liệu.
> Liên quan: `docs/06_plan/README.md` (kế hoạch triển khai), `docs/00_workflow/01_flow.md` (luồng làm việc)

## Lộ trình đọc cho người mới

1. `docs/00_workflow/01_flow.md` và `02_rules.md` để biết cách làm việc.
2. `docs/00_workflow/04_terms.md` để hiểu thuật ngữ và các nhóm việc của dự án.
3. `docs/05_config/*` để biết mỗi file config chứa gì.
4. `docs/04_experiments/metrics.md` và `reference_publication.md` để biết đích cần vượt.
5. `docs/06_plan/README.md` để biết đang ở bước nào.

## Nhóm tài liệu

| Nhóm           | File                       | Nội dung                                         | Đọc khi nào                         |
| -------------- | -------------------------- | ------------------------------------------------ | ----------------------------------- |
| 00_workflow    | `01_flow.md`               | luồng làm việc từ tạo thí nghiệm tới thu kết quả | mới vào nhóm                        |
| 00_workflow    | `02_rules.md`              | luật bắt buộc: nhánh, ghim code, resume, secret  | trước khi chạy hoặc giao thí nghiệm |
| 00_workflow    | `03_ci.md`                 | CI kiểm gì, CI không làm gì, cách sửa khi đỏ     | khi CI báo đỏ                       |
| 00_workflow    | `04_terms.md`              | thuật ngữ, các nhóm việc, hai loại preprocessing | khi gặp từ không rõ                 |
| 00_workflow    | `05_git_commits.md`        | quy ước commit và cách chia nhỏ task             | trước khi commit                    |
| 00_workflow    | `06_conventions.md`        | quy ước code, config, tài liệu                   | khi viết mới                        |
| 00_workflow    | `07_colab.md`              | chạy notebook trên Colab: Drive, env, thứ tự bước | trước khi chạy trên Colab          |
| 01_dataset     | `01_raw_data.md`           | dữ liệu gốc: nơi lưu, cách đặt tên, phiên bản    | làm việc với dữ liệu gốc            |
| 01_dataset     | `02_schema.md`             | schema của dữ liệu và cách khai trong config     | khi đọc hoặc sửa schema             |
| 01_dataset     | `03_new_dataset.md`        | cách thêm dataset mới                            | khi có dữ liệu mới                  |
| 02_eda         | `01_flow.md`               | luồng EDA và config đang áp dụng                 | chạy EDA                            |
| 02_eda         | `02_metrics.md`            | cách tính từng chỉ số EDA                        | đọc kết quả EDA                     |
| 02_eda         | `03_modules.md`            | chi tiết các module EDA                          | sửa EDA                             |
| 02_eda         | `04_report_rules.md`       | quy ước trình bày báo cáo                        | sinh báo cáo                        |
| 02_eda         | `05_extend.md`             | thêm bước EDA mới                                | mở rộng EDA                         |
| 03_pipeline    | `01_flow.md`               | luồng các bước xử lý dữ liệu và config bật tắt   | chạy pipeline                       |
| 03_pipeline    | `02_steps.md`              | chi tiết từng bước                               | sửa một bước                        |
| 03_pipeline    | `03_config.md`             | config của pipeline                              | đổi config                          |
| 03_pipeline    | `04_invariants.md`         | bất biến phải giữ                                | trước khi sửa pipeline              |
| 03_pipeline    | `05_output.md`             | đầu ra của pipeline                              | đọc kết quả pipeline                |
| 03_pipeline    | `06_extend.md`             | thêm bước pipeline mới                           | mở rộng pipeline                    |
| 04_experiments | `01_models.md`             | các model dùng cho thí nghiệm                    | chọn model                          |
| 04_experiments | `02_model_input.md`        | đo đầu vào thật của model                        | chọn `max_length`                   |
| 04_experiments | `03_training_eval.md`      | huấn luyện và đánh giá                           | chạy thí nghiệm                     |
| 04_experiments | `04_backlog.md`            | việc chưa làm                                    | lập kế hoạch                        |
| 04_experiments | `metrics.md`               | định nghĩa từng metric đánh giá                  | viết báo cáo                        |
| 04_experiments | `reference_publication.md` | số của công bố và cách so                        | so kết quả                          |
| 05_config      | `01_paths.md`              | đường dẫn và mẫu tên                             | đổi cấu trúc thư mục                |
| 05_config      | `02_pipeline.md`           | config xử lý dữ liệu                             | sửa cách làm sạch                   |
| 05_config      | `03_datasets.md`           | config dataset và schema                         | thêm hoặc sửa dataset               |
| 05_config      | `04_models.md`             | config dùng chung cho model                      | thêm hoặc sửa model                 |
| 05_config      | `05_experiments_shared.md` | config dùng chung cho thí nghiệm                 | đổi cách chấm hoặc huấn luyện       |
| 05_config      | `06_experiment.md`         | config riêng của thí nghiệm                      | tạo thí nghiệm                      |
| 05_config      | `07_env.md`                | biến môi trường và file env                      | cấu hình máy hoặc Colab             |
| 06_plan        | `README.md`                | mục lục kế hoạch và trạng thái từng bước         | hằng ngày                           |
| 06_plan        | `P0..P7`                   | task nhỏ của từng bước, kèm commit               | khi triển khai                      |
| 06_plan        | `APPENDIX_commits.md`      | bảng toàn bộ commit                              | khi commit                          |
