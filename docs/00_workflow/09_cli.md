# 09. Dòng lệnh

> Đọc file này khi: chạy bất kỳ tool nào của repo, hoặc vừa gõ một lệnh bị từ chối.
> Liên quan: `docs/00_workflow/04_terms.md` (thuật ngữ), `docs/03_pipeline/01_flow.md` (luồng pipeline)

## 1. Bốn khái niệm dễ lẫn

| Gọi là | Ví dụ | Nằm ở đâu | Cờ dùng |
| --- | --- | --- | --- |
| Tên dataset | `cosmetics` | thư mục `configs/datasets/<tên>/` | `--name` |
| Phiên bản cấu hình dataset | `v0.1.0` | tên file `configs/datasets/<tên>/<phiên bản>.yaml` | `run_pipeline.py --version` |
| Nhãn `raw_version` | `v0.1.0` | thư mục `data/raw/<tên>/<nhãn>/` | `--on raw --version` |
| Phiên bản dữ liệu đã xử lý: mã + `hash8` | mã `cosmetics-ds0.2.0-pl0.2.0-srccosmetics@0.1.0-e616c1e3`, `hash8` = `e616c1e3` | `run_pipeline.py` in ra khi chạy; tên thư mục `data/processed/<mã>/` | `--hash` |

Hai giá trị `v0.1.0` ở bảng trên là **hai thứ khác nhau**: một cái là tên file cấu hình dataset, một cái
là tên thư mục dữ liệu gốc. Vì vậy `--version` luôn đi kèm ngữ cảnh: `run_pipeline.py --name <tên>
--version <phiên bản>` là cấu hình dataset, còn `--on raw --version <nhãn>` là dữ liệu gốc.

`--hash` nhận cả hai cách viết của cùng một phiên bản dữ liệu:

```bash
--hash e616c1e3                                              # 8 ký tự hex cuối mã
--hash cosmetics-ds0.2.0-pl0.2.0-srccosmetics@0.1.0-e616c1e3 # mã đầy đủ
```

Không khớp gì, hoặc `hash8` khớp nhiều phiên bản, đều là LỖI kèm danh sách đang có. Mã dài và có `@`,
nên khi dán vào shell thì để trong nháy đơn, hoặc chạy `python build_report.py --list` để lấy lệnh
sẵn sàng dán.

`hash8` ở trang này (ví dụ `e616c1e3`) là của **bộ dữ liệu đang có trên máy**: nó sinh từ NỘI DUNG hai
file cấu hình + nội dung dữ liệu gốc, nên đổi dữ liệu/cấu hình là `run_pipeline.py` in ra `hash8` KHÁC.
Vì vậy hãy dùng đúng giá trị mà lệnh in ra, coi các ví dụ ở đây chỉ là mẫu.

`<hash8>` trong tên thư mục `results/<hash8>/` là chuyện KHÁC: đó là mã băm danh tính của LƯỢT
CHẠY (8 hex **đầu** của `config_sha256`), nên cờ `--hash` KHÔNG nhận giá trị đó - xem
`docs/00_workflow/04_terms.md`.

## 2. Lệnh hợp lệ

| Việc | Lệnh |
| --- | --- |
| Xử lý dữ liệu, tạo dataset + khoá tập đánh giá | `python run_pipeline.py --name cosmetics --version v0.2.0` |
| EDA trên dữ liệu gốc | `python run_eda.py --on raw --name cosmetics --version v0.1.0` |
| EDA trên dataset đã xử lý | `python run_eda.py --on dataset --hash e616c1e3` |
| Vẽ báo cáo EDA của dữ liệu gốc | `python build_report.py --phase eda --on raw --name cosmetics --version v0.1.0` |
| Vẽ báo cáo EDA của dataset | `python build_report.py --phase eda --on dataset --hash e616c1e3` |
| Vẽ báo cáo pipeline | `python build_report.py --phase pipeline --on dataset --hash e616c1e3` |
| Vẽ HẾT mọi đích đang có | `python build_report.py --all` (thu hẹp: `--phase eda --all`) |
| Vẽ hết rồi mở hết bằng trình duyệt | `python build_report.py --all --open` |
| Xem đang có gì + lệnh copy được | `python build_report.py --list` |
| Đo input thật của tokenizer | `python run_token_stats.py --hash e616c1e3 --prompt absa_cot_v1` |
| Liệt kê prompt / bộ tách từ | `python run_token_stats.py --list-prompts` · `--list-segmenters` |
| Đo khi prompt dùng khối hệ thống | `python run_token_stats.py --hash e616c1e3 --prompt absa_cot_v1 --system absa_cot` |
| Kiểm ví dụ few-shot (rò rỉ) | `python run_check_examples.py --hash e616c1e3` |
| Kiểm MỘT prompt, hoặc đổi ngưỡng cụm trùng | `python run_check_examples.py --hash e616c1e3 --prompt absa_cot_5shot_v1 --max-overlap 8` |
| Đo THÊM chỉ số của một lượt chạy từ `predictions.csv` (không chạy model, không ghi đè) | `python scripts/rescore.py --dir experiments/<model>/<method>/<expNNN>/results/<hash8>` (`--reason "..."`, `--no-confusion`) |
| Vẽ báo cáo mở được KHÔNG cần mạng | thêm `--plotlyjs local` (mặc định) hoặc `--plotlyjs cdn` khi muốn dùng CDN |
| Không tự mở trình duyệt | thêm `--no-open` (nay là mặc định; cờ giữ cho câu lệnh cũ) |
| Sinh 5 bảng tổng hợp | `python scripts/collect_reports.py` (`--exclude <nhãn|hash8>` để bỏ lượt khỏi BẢNG SỐ - lượt bị loại VẪN nằm trong `attempt_registry`; lặp lại để loại nhiều lượt. **Lưu ý:** đây là cờ để dựng bảng so KHÔNG có một lượt nào đó; lượt HỎNG thì nên **xoá thư mục kết quả** chứ không phải loại khỏi bảng - cách xử lý sáu thư mục hỏng ngày 04/10/2026 ở `present_plan.md` mục 2.1) |
| Dò NGƯỠNG theo khía cạnh trên `val` | `python scripts/fit_thresholds.py --run experiments/<model>/<method>/<expNNN>/results/<hash8>` (ghi `data/reports/fusion/thresholds.json`; cần tệp `probabilities.csv` của đường encoder) |
| Áp bảng ngưỡng ĐÃ CHỐT lên một lượt khác (thường là `test`) | `python scripts/fit_thresholds.py --apply-to experiments/<model>/<method>/<expNNN>/results/<hash8>` (đọc `--thresholds` mặc định `thresholds.json`; ghi `data/reports/fusion/thresholds_applied.json`; KHÔNG chạy model) |
| Gộp nhiều encoder (ensemble): CHỐT trọng số trên `val` | `python scripts/ensemble.py --run <val A> --run <val B> --weights val --out data/reports/fusion/ensemble_val.json --write-weights data/reports/fusion/weights_val.json` (ghi số của bản gộp trên `val` + tệp trọng số khoá theo TÊN MODEL) |
| Gộp nhiều encoder (ensemble): ÁP trọng số đã chốt lên `test` | `python scripts/ensemble.py --run <test A> --run <test B> --weights-file data/reports/fusion/weights_val.json` (ghi `ensemble.json` + đầu vào rút gọn vào `data/reports/fusion/inputs/`) |
| Đo phân vị token SINH RA để chốt trần `max_new_tokens` | `python scripts/probe_tokens.py --run experiments/<model>/<method>/<expNNN>/results/<hash8>` (`--ceiling` để kiểm luật bị cắt, `--context-window` để chặn trần vượt cửa sổ ngữ cảnh) |
| Chốt LUẬT LAI trên `val`, rồi áp lên `test` | `python scripts/fuse.py --fit --llm <val> --encoder <val>` · `python scripts/fuse.py --apply --rules <rules.json> --llm <test> --encoder <test>` |
| Bỏ phiếu từng ô trên các mẫu (`seed` tăng dần) | `python scripts/vote.py --run <seed1> --run <seed2> --run <seed3>` (ghi `vote.json`) |
| Kiểm tĩnh của CI | `python scripts/ci_checks.py` |
| Dọn rác máy sinh ra (`__pycache__`, `*.pyc`, `.ipynb_checkpoints`) | `python scripts/clean.py` (xem trước: `--dry-run`; không bao giờ xoá file đang được git theo dõi) |
| Dựng gói bàn giao tăng dần (chỉ file mới/đã đổi) | `python scripts/build_package.py` (xem trước: `--dry-run`; `--number NNN` để đặt số gói; `--allow-red` khi đã hiểu rõ cảnh báo đỏ; `--no-zip` khi chỉ muốn ghi sổ) |
| Chạy một notebook trên máy cá nhân, không cần Jupyter | `python scripts/run_notebook.py <model>/<method>/<expNNN>` (dừng trước ô CHẠY: `--preflight-only`) |
| Xem run nào sẽ bị xoá trên MLflow (không xoá gì) | `python scripts/reset_experiment.py --dry-run` |
| Dọn sạch nơi GHI NHẬN để lượt sau đếm lại từ đầu | `python scripts/reset_experiment.py` (hỏi xác nhận; `--yes` bỏ hỏi; `--keep-experiment` giữ experiment) |
| Xoá vài run theo tên hiện trên DagsHub | `python scripts/reset_experiment.py --run 07637bcf` (nhận runName HOẶC run_id; không đụng experiment) |
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
| `build_report.py --on raw --hash e616c1e3` | `--hash` thuộc dataset đã xử lý | 2 |
| `build_report.py --on raw --version <mã>` | mã phiên bản không phải nhãn `raw_version` | 2 |
| `build_report.py --on dataset --version v0.1.0` | với dataset thì dùng `--hash` | 2 |
| `--hash` không khớp phiên bản nào | in danh sách mã đang có | 2 |
| `run_eda.py` thiếu `--on`, hoặc `--on raw` thiếu `--name`/`--version` | phải chỉ đích danh nơi đo | 2 |
| `run_token_stats.py --prompt <tên>` thiếu `--hash` | số liệu ghi vào thư mục theo phiên bản | 2 |
| `run_check_examples.py` thiếu `--hash` | kết luận rò rỉ phải thuộc đúng bộ split đã đọc | 2 |
| `collect_reports.py --exclude <tên lạ>` | mẫu không khớp lượt chạy nào; in kèm danh sách nhãn đang có | 2 |
| `fit_thresholds.py` thiếu CẢ `--run` và `--apply-to`, hoặc có CẢ HAI | hai chế độ khác nhau (dò trên `val` vs áp bảng đã chốt); chọn nhầm là ra số của bước khác | 2 |
| `fit_thresholds.py --apply-to ... --grid/--max-cells-drop` | `--grid` và `--max-cells-drop` quyết định bảng ngưỡng SINH RA, chỉ có nghĩa ở chế độ dò | 2 |
| `fit_thresholds.py --apply-to` mà chưa có tệp ngưỡng | chưa dò thì chưa có gì để áp; in kèm lệnh dò cần chạy trước | 1 |
| `ensemble.py` truyền CẢ `--weights val` và `--weights-file` | hai nguồn trọng số khác nhau cho cùng một lần gộp | 2 |
| `ensemble.py --write-weights` mà không có `--weights val`, hoặc đi cùng `--weights-file` | chỉ có gì để ghi khi vừa CHỐT trọng số; chép lại một tệp đã đọc là việc vô nghĩa | 2 |
| `ensemble.py --val ...` mà không có `--weights val` | `--val` là các lượt để CHỐT trọng số | 2 |
| `ensemble.py --weights val` trên lượt KHÔNG phải `val` | chọn trọng số bằng chính tập sẽ báo cáo (luật 1 của `metrics.md`); in kèm cách dùng `--weights-file` | 1 |
| `ensemble.py --weights-file <tệp>` thiếu model nào của các lượt `--run` | trọng số khoá theo tên model; thiếu thì không ráp được, in kèm danh sách model đang có | 1 |
| `probe_tokens.py --factor/--ceiling/--context-window` không phải số dương | trần token sai là cả lượt chạy sai | 2 |
| `probe_tokens.py` thiếu `predictions.csv` / `run_meta.json` / cột `token sinh` | không đo được chi phí đầu ra; in kèm tệp và cột đang thiếu | 1 |
| `probe_tokens.py` có trần đề xuất VƯỢT `--context-window` | luật 23a: không hạ trần rồi chạy im lặng; in kèm hai con số | 1 |
| `run_pipeline.py` thiếu `--name` hoặc `--version` | mỗi tổ hợp cho ra một bộ dữ liệu khác nhau | 2 |
| `reset_experiment.py --dry-run --yes` | `--dry-run` chỉ xem trước nên không đi với `--yes` | 2 |
| `reset_experiment.py --run <tên> --keep-experiment` | `--run` đã không đụng tới experiment, nên cờ kia là thừa | 2 |
| `reset_experiment.py --run <tên>` mà tên không khớp run nào | in kèm danh sách `runName` đang có | 2 |
| `reset_experiment.py` mà experiment chưa có run nào | không xoá gì; in các experiment đang có để phát hiện tên gõ sai | 1 |
| `reset_experiment.py` không tra được máy chủ (thiếu token / thiếu `mlflow` / mất mạng) | in đúng thứ còn thiếu | 2 |
| Đích hợp lệ nhưng CHƯA có kết quả | in kèm lệnh cần chạy trước (`run_eda.py` / `run_pipeline.py`) | 1 |
| Mọi câu lệnh ở mục 2 | - | 0 |

Riêng `run_check_examples.py` dùng mã **1** cho trường hợp phép kiểm phát hiện lỗi ví dụ hoặc rò rỉ,
để dùng được trong kiểm tra tự động.

`--run` của `scripts/reset_experiment.py` nhận **cả hai** cách gọi tên một run: `runName` (`<hash8>`,
đúng cột hiện trên giao diện DagsHub, ví dụ `07637bcf`) và `run_id` (mã dài của máy chủ, ghi ở HAI chỗ:
`run.log` và khoá `tracking.run_id` trong `run_meta.json`). Lý do nhận cả hai: người chạy đọc `runName`
trên giao diện, còn muốn mở lại đúng run thì tra `run_id` - bắt chuyển tay giữa hai cách viết là chỗ dễ
xoá nhầm.

`runName` **không duy nhất**: chạy lại (hoặc chạy tiếp) cùng một thư mục kết quả sinh nhiều run cùng
tên, nên `--run 07637bcf` có thể xoá nhiều hơn một run. Script in số run khớp cho **từng** tên trước
khi xoá; muốn chắc chắn đúng MỘT run thì dùng `run_id`.

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
