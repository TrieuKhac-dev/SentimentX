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
| P4    | Log, MLflow/DagsHub, resume              | `P4_logging_mlflow.md` | xong       |
| P5    | Ghim code và notebook                    | `P5_notebook_pin.md`   | xong T1..T6; DoD "kéo code theo sha trên Colab thật" ĐÃ có bằng chứng (hai lần chạy thật); còn DoD "gốc kết quả trên Drive" |
| P6    | Reports, CI, docs                        | `P6_reports_ci.md`     | xong T1..T7 (T5–T7 đã soát lại 25/09/2026) |
| P7    | Chạy lại từ đầu và so với công bố        | `P7_rerun.md`          | T1 (dataset v0.2.0 `...-e616c1e3`) và T2 (EDA + report) xong. T3 nay gồm **20 thí nghiệm**: 4 lượt LoRA encoder (PhoBERT và ViSoBERT, mỗi model một lượt `ce` + một lượt `weighted_ce`) + 13 lượt prompt Qwen3-4B (`prompt-cot/exp002..013` và `prompt-one-turn/exp001`) + 3 lượt Qwen3-0.6B, chấm trên `test`. **17 lượt đã có kết quả** (tới 04/10/2026): mức 4-bit lô 4 hơn công bố +0,07 (1 ví dụ) và +0,45 (5 ví dụ), đỉnh `exp009` 97,77; sửa **câu chữ prompt** không cứu được lớp âm nhưng sửa **hàm mất mát** (`weighted_ce`) thì có. Ba lượt Qwen3-0.6B hỏng HAI kiểu (nạp nhầm trọng số 4B; bật suy nghĩ ăn hết trần token) nên cả 6 thư mục kết quả đã xoá 04/10/2026 - **đã tạo lại và ghim ba lượt 0.6B trong gói 012 (04/10/2026), chờ chạy**. Còn T5 (vòng bàn giao) - chi tiết `P7_rerun.md` mục 2 và §8, `present_plan.md` (đợt 7-9) |
| P8    | Đợt "đo lường + MLflow" (rescore đo THÊM, early stop, curve train/val, loss, MLflow `run_id`)      | `P8_measurement_mlflow.md` | xong (trừ A-6 để cuối) |
| P8b   | Đợt 7 → đợt 9 (chạy nốt 17 + 9 + 3 notebook, chốt luật trên `val`, bốn bước kết hợp)            | `P8_batch7.md`         | đang chạy: đã tạo + ghim 23 notebook và đóng **gói 012** (04/10/2026); chờ người dùng chạy đợt 7 |
| -     | Bảng toàn bộ commit                      | `APPENDIX_commits.md`  | -          |

Bảng trên là **nguồn duy nhất** nói đang ở bước nào: sửa mục 2 của file con thì sửa luôn dòng tương
ứng ở đây, để không lặp lại việc tài liệu nói một đằng, việc đã làm một nẻo.

## Cổng kiểm tra bắt buộc

Trước khi làm bất cứ việc gì phụ thuộc MLflow, phải đạt **cổng ở P4**:

1. Chạy một smoke run: log 1 run giả (params, metrics, 1 artifact nhỏ).
2. Mở `https://dagshub.com/TrieuKhac-dev/SentimentX` và xác nhận run xuất hiện.

Không đạt thì dừng, báo cáo và đưa giải pháp, không triển khai tiếp phần phụ thuộc MLflow.

*Trạng thái 27/09/2026:* cổng này đạt ở lượt smoke trên máy cá nhân (P4 T7) nhưng **KHÔNG đạt trên Colab**
trong ba lượt chạy thật đầu tiên: ô bootstrap của notebook cài một danh sách gói cố định mà thiếu `mlflow`,
nên cả ba lượt đều ghi `[TRACK] không ghi nhận gì (tracker tắt)` và không run nào lên DagsHub. Đã sửa
(bootstrap cài `mlflow`, ô cuối chỉ in địa chỉ DagsHub khi có dòng `[TRACK]` thành công) - lượt chạy lại
theo P7 T3 là lần xác nhận cổng này. Chi tiết ở `docs/06_plan/P4_logging_mlflow.md` mục 4.

## Quy ước chung cho mọi giai đoạn

- Không hardcode đường dẫn và giá trị: đọc từ `configs/paths.yaml` và `configs/**`.
- Không đặt giá trị mặc định trong code: thiếu khoá thì báo lỗi rõ kèm danh sách file đã đọc.
- Chú thích ngắn gọn, rõ ràng; không dùng dải gạch dài để phân mục trong code.
- Sau mỗi commit, dự án vẫn phải chạy được.
