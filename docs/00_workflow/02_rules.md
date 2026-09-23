# 02. Luật bắt buộc

> Đọc file này khi: trước khi chạy hoặc giao một thí nghiệm.
> Liên quan: `docs/00_workflow/01_flow.md` · `docs/06_plan/P4_logging_mlflow.md`

## Nhánh và code

1. Notebook **chỉ kéo nhánh `experiment`**. Không kéo nhánh cá nhân.
2. Thí nghiệm cá nhân phải **merge vào `experiment` trước khi chạy**.
3. **Kết quả chạy trước khi merge không được dùng** nếu khi merge phải sửa tệp nào.
   Chạy lại trên `experiment` rồi lấy kết quả của lần chạy đó.
4. Sau commit đầu tiên: **không rebase, không amend, không force-push**.
   Bản code ghim trong notebook phải luôn còn tồn tại.
5. Xoá nhánh riêng **chỉ sau khi** đã merge.

## Ghim code

6. `REPO_SHA` trong notebook do `scripts/pin.py` ghi, không sửa tay.
7. Muốn chạy lại một bản cũ để đối chiếu thì dùng `git checkout <sha>`, không sửa tệp cấu hình.

## Dữ liệu và tập đánh giá

8. Tệp cấu hình phiên bản (`configs/pipeline/<v>.yaml`, `configs/datasets/<name>/<v>.yaml`)
   là **bất biến**. Muốn đổi thì tạo phiên bản mới.
9. Mọi biến đổi văn bản của pipeline **chỉ áp cho train và val**.
   `test.csv` phải khớp `eval_lock` trong tệp dataset version.
10. Bộ chỉ số lấy theo công bố tham chiếu, không tự thêm bớt khi so sánh.

## Resume

11. Resume chỉ hợp lệ khi `config_sha256`, mã phiên bản dữ liệu và `repo.sha` **đều không đổi**.
12. Code đổi thì **không resume**: chạy lại từ đầu, ghi thành một `attempt` mới.

## Checkpoint

13. Trên Colab: notebook tự copy checkpoint sang Drive.
    Trên máy cá nhân: kết quả nằm trong repo, **muốn đưa lên Drive thì tự copy**.
14. Chỉ lưu `model/last` và `model/best`; xoá các checkpoint trung gian.

## Bí mật

15. `.env.colab` chứa token thật, **không bao giờ commit**; gửi cho giảng viên qua kênh riêng.
16. Nên dùng token của một tài khoản riêng chỉ có quyền trên repo DagsHub này.
17. Đổi token sau khi kết thúc đồ án.

## Dữ liệu không vào git

18. `data/raw`, `data/processed`, `data/models` không commit.
    Nhưng `raw_meta.yaml`, `processing_log.json`, `label_map.json`, `pipeline/`, `eda/` thì **phải commit**.
