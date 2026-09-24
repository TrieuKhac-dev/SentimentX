# 02. Luật bắt buộc

> Đọc file này khi: trước khi chạy hoặc giao một thí nghiệm.
> Liên quan: `docs/00_workflow/01_flow.md`, `docs/05_config/03_datasets.md`

## Nhánh và code

1. Notebook **chỉ kéo nhánh `experiment`**. Không kéo nhánh cá nhân.
2. Vẫn được chạy thử thí nghiệm trên nhánh riêng, trên Colab hoặc trên máy cá nhân.
3. Kết quả chỉ được dùng khi commit đã ghim nằm trên nhánh `experiment`,
   và khi merge vào nhánh `experiment` không phải sửa bất kỳ file nào.
4. Nếu khi merge phải sửa file, cách làm là: merge xong, **chạy lại trên nhánh `experiment`**,
   rồi lấy kết quả của lần chạy lại. Kết quả chạy trước khi merge không dùng nữa.
5. Sau commit đầu tiên: **không rebase, không amend, không force-push**.
   Bản code ghim trong notebook phải luôn còn tồn tại.
6. Xoá nhánh riêng **chỉ sau khi** đã merge.

## Ghim code

7. `REPO_SHA` trong notebook do `scripts/pin.py` ghi, không sửa tay.
8. Muốn chạy lại một bản cũ để đối chiếu thì dùng `git checkout <sha>`, không sửa file config.

## Dữ liệu và tập đánh giá

9. File config của phiên bản (`configs/pipeline/<v>.yaml`, `configs/datasets/<name>/<v>.yaml`)
   là **bất biến**. Muốn đổi thì tạo phiên bản mới.
10. Mọi biến đổi văn bản của pipeline **chỉ áp cho train và val**.
11. `test.csv` phải khớp `eval_lock`. `eval_lock` là dấu vân tay của tập đánh giá, khai trong
    file config dataset version: gồm tên file, số dòng và `sha256`. Pipeline phải xuất ra `test.csv`
    đúng dấu vân tay này, lệch thì báo lỗi. Chi tiết ở `docs/05_config/03_datasets.md`.
12. Metric lấy theo công bố tham chiếu, không tự thêm bớt khi so sánh.

## Resume

13. Resume chỉ hợp lệ khi ba giá trị sau **đều không đổi**. Cả ba đều nằm trong
    `results/<mã>/run_meta.json`:
    - `config_sha256`: dấu vân tay của config đã hợp nhất và văn bản prompt đã hợp nhất.
    - `data.ma`: mã phiên bản dữ liệu, ví dụ `cosmetics-ds0.3.0-pl0.2.0-srccosmetics@0.2.0-9c0d1e2f`.
    - `repo.sha`: commit đã ghim trong notebook.
14. Code đổi thì **không resume**: chạy lại từ đầu và ghi thành một `attempt` mới.

## Checkpoint

15. Chỉ lưu `model/last` và `model/best`; xoá các checkpoint trung gian.
16. Copy checkpoint và kết quả là việc thủ công ở cả hai chiều:
    - Chạy trên Colab: kết quả nằm trên Drive. Muốn xem ở máy cá nhân hoặc đưa vào git thì
      phải copy từ Drive về repo, chỉ copy phần nhẹ.
    - Chạy trên máy cá nhân: kết quả nằm trong repo. Muốn đưa lên Drive thì phải tự copy.

## Secret

17. `.env.colab` chứa token thật, **không bao giờ commit**; gửi cho giảng viên qua kênh riêng.
18. Nên dùng token của một tài khoản riêng chỉ có quyền trên repo DagsHub này.
19. Đổi token sau khi kết thúc đồ án.

## Dữ liệu không vào git

20. `data/raw`, `data/processed`, `data/models` không commit.
    Nhưng `raw_meta.yaml`, `processing_log.json`, `label_map.json`, `pipeline/`, `eda/` thì **phải commit**.
    Trên Drive của người chạy, `data/processed/<mã>/` mang đúng bộ file mà lượt chạy cần: train, val,
    test, `label_map.json` và `processing_log.json`; những mục cố ý không lên Drive được liệt kê ở
    `docs/00_workflow/07_colab.md` mục 2.
