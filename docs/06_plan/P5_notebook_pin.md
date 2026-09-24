# P5 - Ghim code và notebook

> Đọc file này khi: tạo thí nghiệm mới, ghim bản code, hoặc giao notebook cho giảng viên.
> Liên quan: `docs/00_workflow/01_flow.md`, `docs/05_config/06_experiment.md`

## 1. Mục tiêu giai đoạn

Notebook chạy được cả trên Colab và trên máy cá nhân, luôn kéo đúng bản code đã ghim,
và có công cụ tạo thí nghiệm mới nhanh, chính xác, không xung đột.

## 2. Trạng thái

chưa làm

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
- [ ] T3. `templates/`: `README.md`, `templates/experiment/{README.md, config.yaml, notebook.ipynb}`,
      `templates/prompt/{prompt.txt, examples.txt, system.txt}`.
      -> `feat(templates): add experiment and prompt templates`
- [ ] T4. Notebook thí nghiệm đầu tiên `exp001`: cell tiêu đề, bootstrap, cấu hình đang dùng,
      preflight, cell thí nghiệm, cell kết thúc.
      -> `feat(notebook): add first experiment notebook`
- [ ] T5. Preflight: kiểm `requires` và `requires_extra`, mã phiên bản, `roles`, GPU và quantization,
      Java khi cần, quyền ghi Drive, trạng thái FRESH hay RESUME.
      -> `feat(preflight): check paths device and drive`
- [ ] T6. `scripts/new_experiment.py`: tạo thí nghiệm mới, tự chọn số `expNNN` kế tiếp từ trạng thái
      đã hợp nhất, từ chối nếu nhánh hiện tại chưa chứa `origin/experiment`.
      -> `feat(scripts): add new experiment scaffolder`

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
