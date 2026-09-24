# Kế hoạch triển khai - mục lục

> Đọc file này khi: bắt đầu làm việc, hoặc muốn biết đang ở bước nào.
> Liên quan: `docs/00_workflow/01_flow.md`, `docs/00_workflow/05_git_commits.md`, `docs/README.md`

## Cách dùng

- Mỗi giai đoạn là một file. Trong mỗi file, mục **3. Task nhỏ** là danh sách task có checkbox.
- Một task = **một commit** (Conventional Commits, tiếng Anh). Commit message ghi ngay cạnh task.
- Trạng thái ghi ở **mục 2** của từng file: `chưa làm` / `đang làm` / `xong`.
- Chỉ chuyển giai đoạn khi mục **4. Điều kiện hoàn thành (DoD)** đã đạt.

## Trạng thái tổng

| Giai đoạn | Nội dung                                 | File                   | Trạng thái |
| ----- | ---------------------------------------- | ---------------------- | ---------- |
| P0    | Dựng cây mới, commit đầu tiên, tạo nhánh | `P0_repo_setup.md`     | xong       |
| P1    | Đường dẫn tập trung                      | `P1_paths.md`          | xong       |
| P2    | Versioning dữ liệu và guard              | `P2_versioning.md`     | xong       |
| P3    | Tầng config thí nghiệm                   | `P3_config_layer.md`   | xong       |
| P4    | Log, MLflow/DagsHub, resume              | `P4_logging_mlflow.md` | chưa làm   |
| P5    | Ghim code và notebook                    | `P5_notebook_pin.md`   | chưa làm   |
| P6    | Reports, CI, docs                        | `P6_reports_ci.md`     | chưa làm   |
| P7    | Chạy lại từ đầu và so với công bố        | `P7_rerun.md`          | chưa làm   |
| -     | Bảng toàn bộ commit                      | `APPENDIX_commits.md`  | -          |

## Cổng kiểm tra bắt buộc

Trước khi làm bất cứ việc gì phụ thuộc MLflow, phải đạt **cổng ở P4**:

1. Chạy một smoke run: log 1 run giả (params, metrics, 1 artifact nhỏ).
2. Mở `https://dagshub.com/TrieuKhac-dev/SentimentX` và xác nhận run xuất hiện.

Không đạt thì dừng, báo cáo và đưa giải pháp, không triển khai tiếp phần phụ thuộc MLflow.

## Quy ước chung cho mọi giai đoạn

- Không hardcode đường dẫn và giá trị: đọc từ `configs/paths.yaml` và `configs/**`.
- Không đặt giá trị mặc định trong code: thiếu khoá thì báo lỗi rõ kèm danh sách file đã đọc.
- Chú thích ngắn gọn, rõ ràng; không dùng dải gạch dài để phân mục trong code.
- Sau mỗi commit, dự án vẫn phải chạy được.
