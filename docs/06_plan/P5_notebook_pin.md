# P5 - Ghim code và notebook

> Đọc file này khi: tạo thí nghiệm mới, ghim bản code, hoặc giao notebook cho giảng viên.
> Liên quan: `docs/00_workflow/01_flow.md`, `docs/05_config/06_experiment.md`

## 1. Mục tiêu giai đoạn

Notebook chạy được cả trên Colab và trên máy cá nhân, luôn kéo đúng bản code đã ghim,
và có công cụ tạo thí nghiệm mới nhanh, chính xác, không xung đột.

## 2. Trạng thái

xong (T1..T6) trên máy cá nhân. Ba mục của mục 4: "kéo code theo sha trên Colab" đã có bằng chứng
thật (hai lần chạy Colab, lần thứ hai in `fetch -> 0`, `checkout -> 0` và `repo.prepare()` xác nhận
đúng commit trên nhánh), "gốc kết quả nằm trên Drive" thì CHƯA: lần chạy đó không mount Drive nên
preflight dừng ở việc thiếu dữ liệu. Vì vậy P5 chưa đóng hẳn; phần còn lại kiểm ở P7 cùng lượt chạy
đầy đủ.

## 3. Task nhỏ (mỗi task một commit)

- [x] T1. `src/repo.py`: `prepare()` kéo đúng commit đã ghim (fetch theo sha, có phương án dự phòng
      `clone --filter=blob:none`), kiểm `git rev-parse HEAD`, đọc config từ chính commit đó.
      -> `feat(repo): fetch and verify pinned commit`
- [x] T2. `scripts/pin.py`: ghi `REPO_URL`, `REPO_SHA`, `EXP_DIR` vào cell đầu của notebook
      (dùng `nbformat`), kiểm commit chỉ đổi đúng file notebook, cảnh báo nếu sha chưa nằm trên nhánh `experiment`.
      -> `feat(scripts): add pin script writing repo url sha and exp dir`
      Ghi cả `REPO_BRANCH`. Không BẮT BUỘC `nbformat`: việc là sửa nguồn của đúng một ô nên `json`
      của thư viện chuẩn là đủ, có `nbformat` thì còn kiểm cấu trúc trước khi ghi - lệnh ghim phải
      chạy được trên mọi máy.
- [x] T3. `templates/`: `README.md`, `templates/experiment/{README.md, config.yaml, notebook.ipynb}`,
      `templates/prompt/{prompt.txt, examples.txt, system.txt}`.
      -> `feat(templates): add experiment and prompt templates`
      Notebook mẫu có 8 ô: tiêu đề, ô GHIM (do `pin.py` ghi), bootstrap (`repo.prepare` +
      `runtime.load_env` + tìm Drive), cấu hình đang dùng, preflight (dừng nếu có việc phải sửa),
      chạy qua chính `src/experiment_run.py` (`plan` rồi `run`) - notebook gọi THƯ VIỆN, không gọi
      script dòng lệnh (`run_qwen_eval.py` chỉ là cửa vào mỏng cho lúc chạy nhanh trên dòng lệnh,
      nó gọi đúng hai hàm đó), kết quả nằm ở đâu, và ô kết thúc.
      Kèm hai thứ mà bootstrap cần: `runtime.drive_dir()`/`drive_env_file()` (nhận Drive bằng FILE
      ĐÁNH DẤU, không đoán theo tên - MyDrive và Shared drives trông giống nhau), và `device_report`
      bắt thêm `OSError` khi nạp `torch` (torch cài hỏng thì báo thành việc phải sửa, không để
      ngoại lệ hệ điều hành làm dừng notebook).
      Ô BOOTSTRAP phải kéo mã nguồn TRƯỚC khi `import src`, và kéo ĐÚNG COMMIT ĐÃ GHIM chứ không
      phải nhánh mặc định: lần chạy notebook trên Colab (24/09/2026) lộ ra
      `ModuleNotFoundError: No module named 'src'` vì notebook `import src` trong khi máy chưa có
      mã nguồn; còn `git clone` trần thì lấy nhánh MẶC ĐỊNH, mà mã nguồn nằm trên nhánh `experiment`.
      Đã kiểm lại bằng cách kéo vào một thư mục TRỐNG từ remote thật
      (`clone --filter=blob:none --no-checkout` -> `fetch --depth 1 origin <sha>` ->
      `checkout --detach <sha>`): có `src/`, và `repo.prepare()` báo "dùng bản code đang có",
      trên nhánh, không cảnh báo. Test khoá thứ tự này cho cả notebook mẫu và mọi notebook
      thí nghiệm (`tests/test_templates.py::TestBootstrap`).
      **Lần chạy Colab thật thứ hai (25/09/2026, exp001, commit 8e79c0d)** xác nhận phần kéo code:
      `fetch -> 0`, `checkout -> 0`, `repo.prepare()` báo "dùng bản code đang có | trên nhánh |
      8e79c0d5". Hai việc còn lại lộ ra trong cùng lần chạy đó, đều đã sửa:
      (a) `git clone` vào thư mục `/content/SentimentX` còn sót từ lần chạy trước in mã thoát 128
      (`destination path ... already exists and is not an empty directory`) - dòng lỗi đỏ làm người
      đọc tưởng hỏng, nên bootstrap nay kiểm thư mục đã là git repo chưa rồi mới kéo, và DỪNG kèm
      cách sửa nếu thư mục có sẵn mà không phải repo;
      (b) mã phiên bản dữ liệu hai máy lệch nhau (`...-2d9fc48b` trên Colab so với `...-bf68b1c5` ở
      máy cá nhân) vì băm thẳng byte, xem `docs/06_plan/P2_versioning.md`.
      Điều còn thiếu của P5 là gốc kết quả trên Drive: lần chạy trên không thấy Drive (chưa mount),
      nên preflight dừng ở việc thiếu dữ liệu.
- [x] T4. Notebook thí nghiệm đầu tiên `exp001`: cell tiêu đề, bootstrap, cấu hình đang dùng,
      preflight, cell thí nghiệm, cell kết thúc.
      -> `feat(experiments): create exp001 - Qwen3-4B CoT prompt, scored on val`
      Tạo bằng CHÍNH `new_experiment.py` (ăn thử công cụ) rồi `scripts/pin.py` ghim commit
      `fe180947` vào ô đầu (`chore(experiments): pin commit fe180947 into the exp001 notebook`).
      exp001 chấm trên `val` với `n: 200`, prompt CoT lấy từ thư viện dùng chung bằng ĐƯỜNG DẪN.
      Preflight cho exp001 báo 0 việc phải sửa. Lượt chạy 200 mẫu của exp001 để dành cho P7; đường
      chạy đã chứng minh bằng một lượt 4 mẫu thật ngoài thí nghiệm (xem P4 T8).
      Làm T4 thì lộ ra và sửa hai lỗi thật: đường dẫn prompt trong config thiếu một cấp `../`
      (đúng loại lỗi preflight sinh ra để bắt), và `preflight.run()` để lỗi đó thoát ra thành
      traceback thay vì kể thành việc-phải-sửa.
- [x] T5. Preflight: kiểm `requires` và `requires_extra`, mã phiên bản, `roles`, GPU và quantization,
      Java khi cần, quyền ghi Drive, trạng thái FRESH hay RESUME.
      -> `feat(preflight): check paths device and drive`
      Làm TRƯỚC T3 để template notebook gọi được hàm đã có sẵn. Chạy thử trên máy thật: nhận ra
      dataset đang có, `test.csv` chưa chốt `eval_lock` (đo được `64dbf812...`, 2271 dòng - con số
      2271 là ĐẾM DÒNG, sai; xem `fix(preflight): eval_lock counts records, not lines`), GPU
      RTX 3050 6GB + torch 2.14.0+cu126 + bitsandbytes, cả hai gốc ghi được, trạng thái NEW - và
      bắt được một LỖI THẬT: tôi đã so `data.version` (phiên bản file config dataset) với mã
      phiên bản dữ liệu ĐÃ XỬ LÝ, hai thứ khác nhau, nên báo lỗi sai.
- [x] T6. `scripts/new_experiment.py`: tạo thí nghiệm mới, tự chọn số `expNNN` kế tiếp từ trạng thái
      đã hợp nhất, từ chối nếu nhánh hiện tại chưa chứa `origin/experiment`.
      -> `feat(experiments): add scripts/new_experiment.py to scaffold an experiment`
      Kèm `src/notebooks.py` (một định nghĩa ô ghim dùng chung với `pin.py`, để hai công cụ không
      thể hiểu ô ghim khác nhau) và `experiments.list_experiments()`/`next_exp_id()` trong thư viện
      (chọn số kế tiếp theo số LỚN NHẤT đã có, nên xoá một thí nghiệm ở giữa không đụng số khác).
      Từ chối khi: thí nghiệm đã có, config model chưa có, nhánh ghim chưa lên remote.

## 4. Điều kiện hoàn thành (DoD)

- Cùng một notebook: chạy trên máy cá nhân thì ghi kết quả vào repo, chạy trên Colab thì ghi vào Drive.
- Kéo code theo sha thành công trên Colab thật (có ghi lại kết quả thử).
- `python scripts/new_experiment.py --model ... --method ...` tạo đúng thư mục `expNNN` kế tiếp,
  không đụng thí nghiệm cũ.

## 5. Rủi ro / lưu ý

- GitHub phải cho phép fetch theo sha. Nếu không, dùng phương án dự phòng trong `src/repo.py`.
- Sau khi giao notebook, không sửa `experiments/**/expNNN/**` cho tới khi giảng viên chạy xong.

## 6. Phụ thuộc

P4 xong (đã có tracking, log, resume).
