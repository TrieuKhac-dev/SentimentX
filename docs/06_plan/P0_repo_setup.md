# P0 - Dựng cây mới, commit đầu tiên, tạo nhánh

> Đọc file này khi: làm bước đầu tiên của dự án.
> Liên quan: `docs/06_plan/README.md`, `docs/00_workflow/01_flow.md`, `docs/00_workflow/02_rules.md`

## 1. Mục tiêu phase

Có một repo sạch ở `SentimentX/SentimentX/` với cấu trúc mới, commit đầu tiên không chứa dữ liệu,
và hai nhánh `main` + `experiment` trên GitHub.

## 2. Trạng thái

xong

## 3. Task nhỏ (mỗi task một commit)

- [x] T1. Tạo `SentimentX/SentimentX/`; copy `src/`, `configs/`, `docs/`, `tests/`, `scripts/`
      và các file gốc `README.md`, `requirements.txt`, `.gitattributes`, 7 script chạy
      (`run_eda.py`, `run_pipeline.py`, `run_token_stats.py`, `run_check_examples.py`,
      `build_report.py`, `run_qwen_eval.py`, `run_rescore_eval.py`).
      -> `chore(repo): scaffold refactored project tree`
- [x] T2. Copy `data/reports/assets/plotly.min.js` sang `data/assets/plotly.min.js`.
      -> `chore(assets): move shared plotly asset into data/assets`
- [x] T3. Chuyển `data/raw/` và `data/models/` sang cây mới (không commit, chỉ là file trên đĩa).
- [x] T4. Thêm `.gitignore` (ignore dữ liệu theo đuôi file), `.gitattributes`, các `.gitkeep`
      và `data/models/README.md`.
      -> `chore(git): ignore data by extension and keep folder placeholders`
- [x] T5. Thêm `.env.example` và `.env.colab.example`.
      -> `docs(env): add env templates for local and colab`
- [x] T6. `git init`, commit đầu tiên, push `main`, tạo nhánh `experiment`.
      -> `chore: initial import of refactored project` (commit `6fa0d32`)
- [x] T7. Xoá `.git` ở cây cũ (làm cuối cùng, không thể hoàn tác).

## 4. Điều kiện hoàn thành (DoD)

- Commit đầu tiên **không** chứa `data/raw`, `data/processed`, `data/models`.
- `git status` sạch sau commit.
- Trên GitHub có nhánh `main` và `experiment`.
- `data/models/Qwen3-4B-Instruct-2507/` và `data/raw/cosmetics/v0.1.0/` vẫn còn trên đĩa.

## 5. Rủi ro / lưu ý

- `git push` có thể cần xác thực GitHub. Nếu terminal chưa đăng nhập, dừng ở commit local và báo lại.
- Xoá `.git` cây cũ là không thể hoàn tác. Cây cũ vẫn giữ file làm tham chiếu, chỉ mất lịch sử git.
- Từ commit đầu tiên trở đi: không rebase, không amend, không force-push.

## 6. Phụ thuộc

Không. Đây là phase đầu tiên.
