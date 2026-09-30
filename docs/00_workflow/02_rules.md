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
10. Mọi biến đổi văn bản của pipeline **chỉ áp cho train và val**: mỗi bước khai phạm vi của mình ở
    `steps.<tên>.apply_to`, và `test` không được có tên trong đó (pipeline `v0.2.0` khai
    `apply_to: [train, val]`). Bước Final Validate chứng minh điều này **từng dòng**: dòng của split
    không nằm trong `apply_to` phải bằng ĐÚNG văn bản gốc. Rò rỉ dữ liệu vì thế được xử lý ở phía TẬP
    HỌC (`steps.clean.leakage.keep_priority: [test, val, train]` giữ bản ghi ở tập ưu tiên cao hơn và
    loại khỏi các tập thấp hơn), chứ không loại khỏi tập đánh giá - xem
    `docs/03_pipeline/02_steps.md` và `docs/05_config/02_pipeline.md`.
11. `test.csv` phải khớp **khoá tập đánh giá**. Khoá do pipeline ghi MỘT LẦN, ngay từ bản dữ liệu
    đầu tiên, vào `data/processed/<mã>/eval_lock.json`, và gồm HAI dấu vân tay cho từng split đã khoá:
    `records_sha256` - **tập bản ghi** (đây là KHOÁ: lệch là báo lỗi, không chỉ cảnh báo) và `sha256` -
    byte của file (dấu vết của bản đã công bố: lệch chỉ là ghi chú, vì đổi cách ghi file không phải là
    đổi tập đánh giá). Kèm `rows` (số bản ghi) và `schema` (công thức tính vân tay dữ liệu). File config
    dataset version chỉ khai **chính sách** (`eval_lock.enforce`, tên file) và giá trị **mong đợi** khi
    cần đối chiếu với một tập test bên ngoài. Giá trị mong đợi (`sha256`, `rows`) phải điền TRƯỚC lần
    chạy chính thức - chạy thử một lượt lấy số rồi điền, vì file phiên bản là bất biến sau khi dùng. Chi
    tiết ở `docs/03_pipeline/05_output.md` và `docs/05_config/03_datasets.md`.
12. Metric lấy theo công bố tham chiếu, không tự thêm bớt khi so sánh.

## Resume

13. Resume chỉ hợp lệ khi ba giá trị sau **đều không đổi**. Cả ba đều nằm trong
    `results/<hash8>/run_meta.json`:
    - `config_sha256`: mã băm danh tính của lượt chạy - config đã hợp nhất (đã **loại các khoá mô tả**
      như `notes`), văn bản prompt, file ví dụ + khối hệ thống, mã phiên bản dữ liệu, và các giá trị chỉ
      có khi chạy. Nó cũng CHÍNH LÀ tên thư mục kết quả (`<hash8>` = 8 ký tự đầu).
    - `data.build`: mã phiên bản dữ liệu, ví dụ `cosmetics-ds0.3.0-pl0.2.0-srccosmetics@0.2.0-9c0d1e2f`.
    - `repo.sha`: commit đã ghim trong notebook.
14. Code đổi thì **không resume**: lượt chạy mới có `repo.sha` khác nên rơi vào **thư mục khác**
    (mã băm khác); kết quả cũ giữ nguyên, không bị chuyển đi đâu và không bị ghi đè.

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

## Prompt và file ví dụ

21. `configs/prompts/<tên>.txt` và các file đi kèm (`configs/prompts/examples/<tên>.txt`,
    `configs/prompts/system/<tên>.txt`) là **MỘT CẶP có phiên bản**, **bất biến khi đã dùng**.
    Đổi nội dung thì tạo **cặp mới** (`absa_cot_5shot_v2.txt` + `examples/absa_cot_5shot_v2.txt`) rồi
    trỏ config/prompt sang tên mới, **không sửa file đã dùng**: tên bảng số đo mang băm NỘI DUNG của bộ
    ví dụ (`ex-<sha8>`), nên sửa tại chỗ là bảng cũ thành **mồ côi** - không tái lập được nữa mà vẫn
    được tính vào `model_input.csv`. Ba lớp chặn (cảnh báo lúc chạy, kiểm 8 của CI, kho lịch sử
    `data/reports/_archive/`) ở `docs/04_experiments/02_model_input.md` mục 2.2.
