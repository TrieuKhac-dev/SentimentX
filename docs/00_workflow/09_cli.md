# 09. Dòng lệnh

> Đọc file này khi: chạy bất kỳ tool nào của repo, hoặc vừa gõ một lệnh bị từ chối.
> Liên quan: `docs/00_workflow/04_terms.md` (thuật ngữ), `docs/03_pipeline/01_flow.md` (luồng pipeline)

## 1. Bốn khái niệm dễ lẫn

| Gọi là | Ví dụ | Nằm ở đâu | Cờ dùng |
| --- | --- | --- | --- |
| Tên dataset | `cosmetics` | thư mục `configs/datasets/<tên>/` | `--name` |
| Phiên bản cấu hình dataset | `v0.1.0` | tên file `configs/datasets/<tên>/<phiên bản>.yaml` | `run_pipeline.py --version` |
| Nhãn `raw_version` | `v0.1.0` | thư mục `data/raw/<tên>/<nhãn>/` | `--on raw --version` |
| Phiên bản dữ liệu đã xử lý: mã + `hash8` | mã `cosmetics-ds0.1.0-pl0.1.0-srccosmetics@0.1.0-e0ccc484`, `hash8` = `e0ccc484` | `run_pipeline.py` in ra khi chạy; tên thư mục `data/processed/<mã>/` | `--hash` |

Hai giá trị `v0.1.0` ở bảng trên là **hai thứ khác nhau**: một cái là tên file cấu hình dataset, một cái
là tên thư mục dữ liệu gốc. Vì vậy `--version` luôn đi kèm ngữ cảnh: `run_pipeline.py --name <tên>
--version <phiên bản>` là cấu hình dataset, còn `--on raw --version <nhãn>` là dữ liệu gốc.

`--hash` nhận cả hai cách viết của cùng một phiên bản dữ liệu:

```bash
--hash e0ccc484                                              # 8 ký tự hex cuối mã
--hash cosmetics-ds0.1.0-pl0.1.0-srccosmetics@0.1.0-e0ccc484 # mã đầy đủ
```

Không khớp gì, hoặc `hash8` khớp nhiều phiên bản, đều là LỖI kèm danh sách đang có. Mã dài và có `@`,
nên khi dán vào shell thì để trong nháy đơn, hoặc chạy `python build_report.py --list` để lấy lệnh
sẵn sàng dán.

`<hash8>` trong tên thư mục `results/<hash8>/` là chuyện KHÁC: đó là mã băm danh tính của LƯỢT
CHẠY (8 hex **đầu** của `config_sha256`), nên cờ `--hash` KHÔNG nhận giá trị đó - xem
`docs/00_workflow/04_terms.md`.

## 2. Lệnh hợp lệ

| Việc | Lệnh |
| --- | --- |
| Xử lý dữ liệu, tạo dataset + khoá tập đánh giá | `python run_pipeline.py --name cosmetics --version v0.1.0` |
| EDA trên dữ liệu gốc | `python run_eda.py --on raw --name cosmetics --version v0.1.0` |
| EDA trên dataset đã xử lý | `python run_eda.py --on dataset --hash e0ccc484` |
| Vẽ báo cáo EDA của dữ liệu gốc | `python build_report.py --phase eda --on raw --name cosmetics --version v0.1.0` |
| Vẽ báo cáo EDA của dataset | `python build_report.py --phase eda --on dataset --hash e0ccc484` |
| Vẽ báo cáo pipeline | `python build_report.py --phase pipeline --on dataset --hash e0ccc484` |
| Vẽ HẾT mọi đích đang có | `python build_report.py --all` (thu hẹp: `--phase eda --all`) |
| Vẽ hết rồi mở hết bằng trình duyệt | `python build_report.py --all --open` |
| Xem đang có gì + lệnh copy được | `python build_report.py --list` |
| Đo input thật của tokenizer | `python run_token_stats.py --hash e0ccc484 --prompt absa_cot_v1` |
| Liệt kê prompt / bộ tách từ | `python run_token_stats.py --list-prompts` · `--list-segmenters` |
| Đo khi prompt dùng khối hệ thống | `python run_token_stats.py --hash e0ccc484 --prompt absa_cot_v1 --system absa_cot` |
| Kiểm ví dụ few-shot (rò rỉ) | `python run_check_examples.py --hash e0ccc484` |
| Kiểm MỘT prompt, hoặc đổi ngưỡng cụm trùng | `python run_check_examples.py --hash e0ccc484 --prompt absa_cot_5shot_v1 --max-overlap 8` |
| Vẽ báo cáo mở được KHÔNG cần mạng | thêm `--plotlyjs local` (mặc định) hoặc `--plotlyjs cdn` khi muốn dùng CDN |
| Không tự mở trình duyệt | thêm `--no-open` (nay là mặc định; cờ giữ cho câu lệnh cũ) |
| Sinh 5 bảng tổng hợp | `python scripts/collect_reports.py` |
| Kiểm tĩnh của CI | `python scripts/ci_checks.py` |
| Dọn rác máy sinh ra (`__pycache__`, `*.pyc`, `.ipynb_checkpoints`) | `python scripts/clean.py` (xem trước: `--dry-run`; không bao giờ xoá file đang được git theo dõi) |
| Dựng gói bàn giao tăng dần (chỉ file mới/đã đổi) | `python scripts/build_package.py` (xem trước: `--dry-run`; `--number NNN` để đặt số gói; `--allow-red` khi đã hiểu rõ cảnh báo đỏ; `--no-zip` khi chỉ muốn ghi sổ) |
| Chạy một notebook trên máy cá nhân, không cần Jupyter | `python scripts/run_notebook.py <model>/<method>/<expNNN>` (dừng trước ô CHẠY: `--preflight-only`) |
| Các ô của notebook: luật thêm/sửa/xoá, thứ tự, khối bảo vệ | `docs/00_workflow/10_template_notebook.md` (không phải cờ dòng lệnh, nhưng là thứ hay phải tra cùng trang này) |

## 3. Câu lệnh bị từ chối, và mã thoát

| Câu lệnh | Vì sao bị từ chối | Mã thoát |
| --- | --- | --- |
| `build_report.py` (không tham số) | thiếu `--phase` và `--on`; muốn vẽ hết thì `--all` | 2 |
| `build_report.py --phase eda` | thiếu `--on` | 2 |
| `build_report.py --phase eda --on raw` | thiếu `--name` và `--version` | 2 |
| `build_report.py --phase eda --on dataset` | thiếu `--hash` | 2 |
| `build_report.py --phase pipeline` | thiếu `--on` | 2 |
| `build_report.py --phase pipeline --on raw` | pipeline chỉ có nguồn là dataset đã xử lý | 2 |
| `build_report.py --phase all` | cú pháp không còn được nhận; dùng `--all` | 2 |
| `build_report.py --dataset <tên>` | cú pháp không còn được nhận; dùng `--name` | 2 |
| `build_report.py --on raw --hash e0ccc484` | `--hash` thuộc dataset đã xử lý | 2 |
| `build_report.py --on raw --version <mã>` | mã phiên bản không phải nhãn `raw_version` | 2 |
| `build_report.py --on dataset --version v0.1.0` | với dataset thì dùng `--hash` | 2 |
| `--hash` không khớp phiên bản nào | in danh sách mã đang có | 2 |
| `run_eda.py` thiếu `--on`, hoặc `--on raw` thiếu `--name`/`--version` | phải chỉ đích danh nơi đo | 2 |
| `run_token_stats.py --prompt <tên>` thiếu `--hash` | số liệu ghi vào thư mục theo phiên bản | 2 |
| `run_check_examples.py` thiếu `--hash` | kết luận rò rỉ phải thuộc đúng bộ split đã đọc | 2 |
| `run_pipeline.py` thiếu `--name` hoặc `--version` | mỗi tổ hợp cho ra một bộ dữ liệu khác nhau | 2 |
| Đích hợp lệ nhưng CHƯA có kết quả | in kèm lệnh cần chạy trước (`run_eda.py` / `run_pipeline.py`) | 1 |
| Mọi câu lệnh ở mục 2 | - | 0 |

Riêng `run_check_examples.py` dùng mã **1** cho trường hợp phép kiểm phát hiện lỗi ví dụ hoặc rò rỉ,
để dùng được trong kiểm tra tự động.

## 4. Vì sao phải ghi rõ đích

Để tool tự chọn "bản mới nhất" là **đoán**, và đoán sai ở đây thì im lặng:

- `run_token_stats.py` ghi bảng số liệu vào thư mục của phiên bản dữ liệu; đoán sai là bảng nằm ở
  phiên bản khác mà nhìn vào vẫn hợp lý.
- `run_check_examples.py` kết luận về rò rỉ theo 3 split nó đã đọc; đọc sai phiên bản là kết luận
  sai mà vẫn tin là đúng.
- `build_report.py` vẽ báo cáo cho đích nào cũng ra một file HTML trông như nhau.

`--hash` chỉ bảo đảm câu lệnh nói rõ đích; nó không bảo đảm đích là bản bạn cần. Vì vậy mỗi tool còn
in **đích đã resolve** trước khi làm việc, và hai tool đo/kiểm còn in thêm phiên bản dữ liệu nào
đang được các lượt chạy dùng (`run_meta.json`, khoá `data.build`).

## 5. Quy ước khi viết tool mới

- Một cờ một nghĩa. Tên dataset là `--name`; `--version` chỉ dùng cho phiên bản file cấu hình dataset
  (`run_pipeline.py`) và cho nhãn `raw_version` (khi có `--on raw`); phiên bản dữ liệu đã xử lý luôn
  là `--hash`.
- Mã thoát: `0` xong, `1` hợp lệ nhưng chưa có kết quả (hoặc phép kiểm phát hiện lỗi, hoặc người dùng
  trả lời KHÔNG khi công cụ hỏi), `2` câu lệnh chưa rõ hoặc cú pháp không còn được nhận. Không để ngoại
  lệ thoát ra thành traceback.
- `build_package.py` dùng thêm mã `3`: gói **không** được dựng vì phát hiện nội dung của một phiên bản
  dữ liệu ĐÃ GỬI bị đổi (người nhận đang giữ cùng một mã phiên bản với nội dung khác). Đây không phải
  lỗi cú pháp mà là việc phải sửa trước khi gửi.
- Đổi cờ thì sửa đồng thời: trang này, docstring của tool, và `tests/workflow/test_cli.py`.
- Không viết cứng đường dẫn trong chuỗi help: dựng từ `configs/paths.yaml` qua `src/core/paths.py`
  (`tests/core/test_paths.py` chặn).
- `docs/06_plan/P0..P2` là bản ghi lịch sử: đừng copy lệnh từ đó.
