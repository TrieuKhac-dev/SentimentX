# 01. Luồng làm việc

> Đọc file này khi: mới vào nhóm, hoặc không nhớ bước tiếp theo là gì.
> Liên quan: `docs/00_workflow/02_rules.md`, `docs/00_workflow/07_colab.md`, `docs/06_plan/README.md`

## Vai trò các thành phần

| Thành phần                  | Vai trò                                                      |
| --------------------------- | ------------------------------------------------------------ |
| GitHub                      | nơi chứa code và config, là nguồn duy nhất                   |
| Nhánh `experiment`          | nhánh duy nhất notebook kéo code                             |
| Nhánh `experiment/<name>`   | nhánh làm việc riêng, tạo từ `experiment`, xoá sau khi merge |
| Colab của giảng viên        | nơi chạy notebook                                            |
| Google Drive của giảng viên | nơi chứa dữ liệu vào và kết quả ra                           |
| DagsHub                     | nơi xem lại thí nghiệm qua MLflow                            |

## Tạo thí nghiệm mới

```bash
python scripts/new_experiment.py --model qwen3-4b-instruct-2507 --method prompt-cot --notes "CoT 1 shot"
```

Lệnh này làm 6 việc:

1. Kiểm cây làm việc sạch. Còn thay đổi chưa commit thì dừng (khi tạo thật; `--dry-run` miễn điều
   kiện này vì không ghi gì, còn cờ `--allow-dirty` là đường thoát khi tạo thật và sẽ in cảnh báo).
2. Chạy `git fetch origin experiment` (fetch hỏng - mất mạng - thì chỉ **cảnh báo** rồi đi tiếp).
3. Kiểm nhánh hiện tại đã chứa `origin/experiment`. Chưa chứa thì dừng và yêu cầu merge trước.
4. Quét `experiments/<model>/<method>/exp*` trong cây làm việc và trong `origin/experiment`,
   lấy số `expNNN` kế tiếp.
5. Copy `templates/experiment/` thành `experiments/<model>/<method>/expNNN/`.
6. Điền `exp_id`, `model`, `method`, `parent`, `notes` và in ra các bước tiếp theo.

Vì sao không trùng số: số kế tiếp luôn được tính từ trạng thái đã hợp nhất trên `origin/experiment`,
nên hai người không thể cùng nhận một số.

Nếu không muốn dùng lệnh: vẫn có thể copy tay `templates/experiment/`, đặt đúng đường dẫn rồi điền tay.

## Luồng một thí nghiệm

1. Tạo thí nghiệm mới bằng lệnh ở trên.
2. Viết config và các file của thí nghiệm (bản mẫu ở `templates/`, xem `templates/README.md`):
   - `config.yaml`: bắt buộc cho mọi thí nghiệm.
   - `prompt.txt` và `examples.txt`: chỉ dùng cho model dạng LLM, ví dụ Qwen3.
     Model encoder như PhoBERT, ViSoBERT không dùng prompt.
   - `system.txt`: **system prompt của thí nghiệm, ở FILE RIÊNG** - không viết câu hệ thống vào
     `prompt.txt`. Dùng chung cho nhiều thí nghiệm thì để ở `configs/prompts/system/<tên>.txt`.
3. Chạy thử trên máy cá nhân: mở `notebook.ipynb` và chạy toàn bộ.
4. Merge nhánh riêng vào nhánh `experiment` và giải quyết mọi xung đột ở bước này.
5. Ghim bản code: `python scripts/pin.py <model>/<method>/<expNNN>`.
6. `git push`, rồi gửi **thư mục Drive đã chuẩn bị**: dữ liệu (gốc và đã xử lý), file notebook, và
   `.env.colab` nếu có token. Cách dựng và gửi thư mục: `docs/00_workflow/07_colab.md`.
7. Giảng viên: mở notebook và bấm **Run all**. Ô bootstrap tự mount Drive, tự tìm thư mục nhóm (nhận
   ra bằng file đánh dấu `.sentimentx_root`, KHÔNG cần biết tên thư mục), tự đặt hai gốc đường dẫn và
   tự cài gói máy ảo còn thiếu. Việc duy nhất phải làm tay là bấm **Allow** khi Colab hỏi quyền truy
   cập Drive - việc Google không cho tự động hoá.
8. Xem kết quả:
   - Trên DagsHub: xem ngay, không cần copy gì.
   - Trên máy cá nhân: phải copy thư mục kết quả từ Drive về repo trước,
     vì kết quả chạy trên Colab nằm trên Drive.
9. Sinh lại bảng tổng hợp: `python scripts/collect_reports.py`.

## Ghim code vào notebook

Cell đầu của mỗi notebook chỉ có **bốn hằng số**: `REPO_URL`, `REPO_BRANCH`, `REPO_SHA` (commit đã
ghim) và `EXP_DIR` (thư mục thí nghiệm). `python scripts/pin.py <model>/<method>/<expNNN>` ghi bốn
giá trị đó; ô đã ghim được tìm **theo dấu**, nên ghim lại thì cập nhật đúng ô cũ chứ không thêm ô
thứ hai.

Cell bootstrap (do `templates/` sinh ra) kéo **đúng** commit đó rồi mới `import src`; phần chuẩn bị môi
trường nằm trong `src/workflow/bootstrap.py` (ô chỉ gọi 4 hàm qua mặt tiền `src.api`, bên trong
`bootstrap.prepare()` mới gọi `repo.prepare(...)`). Nhờ vậy:

- Notebook chạy trên máy cá nhân: thư mục code đang đúng commit rồi nên **không cần mạng**.
- Notebook chạy trên Colab: kéo code theo sha (fetch theo sha, không được thì
  `clone --filter=blob:none` rồi `checkout`), sau đó kiểm lại `git rev-parse HEAD` **phải** bằng
  đúng sha - lệch thì dừng, không chạy trên bản code không rõ là bản nào.
- Commit đã ghim phải nằm trên nhánh cho phép (mặc định `experiment`); chưa thì cảnh báo, vì không
  ai khác tải lại được đúng bản code đã sinh ra kết quả.

Notebook của một thí nghiệm đã chạy là **bản ghi** của lượt chạy đó: đừng dựng lại nó theo bản mẫu,
và đừng sửa ô của nó. Quy tắc thêm/sửa/xoá ô, thứ tự các ô, và quy trình 5 bước để đổi bản mẫu:
`docs/00_workflow/10_template_notebook.md`.

SÁU Ô CODE của một notebook, theo thứ tự - đây là hợp đồng giữa notebook, `scripts/pin.py` và
`scripts/run_notebook.py`:

| # | Ô | Nội dung | Nhận ra bằng |
| --- | --- | --- | --- |
| 1 | GHIM | `REPO_URL`, `REPO_BRANCH`, `REPO_SHA`, `EXP_DIR` | dấu `notebooks.MARKER` |
| 2 | bootstrap | kéo mã nguồn (phải xong TRƯỚC khi `import src`), rồi 4 hàm của `src/workflow/bootstrap.py` | `from src.api import bootstrap` |
| 3 | cấu hình | nạp config, in ra đang chạy gì, tính mã phiên bản dữ liệu | - |
| 4 | kiểm trước | `preflight.run(...)`, in danh sách việc phải sửa và DỪNG nếu có | `preflight.run` |
| 5 | CHẠY | đúng MỘT lời gọi `experiment_run.run(...)` (hoặc `encoder_run.run(...)`) | dấu `notebooks.RUN_MARKER` |
| 6 | KẾT THÚC | in link DagsHub nếu có, nhắc ghim, rồi **ngắt phiên Colab** | `print(end_session())` |

Notebook ĐẦY ĐỦ có **tám ô**: sáu ô code này cộng **hai ô markdown** - ô mở đầu (giới thiệu) và ô
"Kết quả nằm ở đâu". Hai ô markdown KHÔNG nằm trong hợp đồng, nhưng đừng xoá: đó là phần người nhận
đọc trước tiên (`10_template_notebook.md`).

Hai ô mang DẤU (không theo số thứ tự) vì cả hai công cụ phải tìm được chúng kể cả khi notebook đã
thêm/bớt ô: `pin.py` tìm ô GHIM, `run_notebook.py --preflight-only` tìm ô CHẠY. Ô nào lỗi cũng ngắt
phiên Colab (trừ khi bấm Stop) - chi tiết ở `10_template_notebook.md` mục 3.2.

Trước khi ghi, `pin.py` còn kiểm **cây làm việc phải sạch ngoài file notebook**: commit ghim chỉ
được đổi đúng một file. Sau khi ghim thì không sửa `experiments/**/expNNN/**` nữa cho tới khi
giảng viên chạy xong (P5, mục rủi ro). Hệ quả cần nhớ: sửa code thì phải **ghim lại**, và từ lúc giao
notebook (P7 T5) thư mục thí nghiệm **đóng băng** - mọi thay đổi sau đó đều phải đi qua một lần ghim
mới, nếu không notebook của người nhận vẫn chạy bản cũ.
**Ghim lại CẢ BỘ (khi bản code đổi):** notebook ghim *bản code*, nên HEAD nhích thì MỌI notebook phải
ghim lại cùng lúc, không chỉ cái vừa sửa. Cách làm: đẩy commit code lên nhánh trước, rồi chạy
`python scripts/pin.py <exp> --allow-dirty` cho từng thí nghiệm và commit đúng những file
`notebook.ipynb` đó trong MỘT commit. Ở đây `--allow-dirty` là hợp lệ và có chủ ý: cây đang bẩn CHÍNH
VÌ các notebook vừa ghim, mà commit ghim lại chỉ được chứa notebook - cờ này không được dùng để trộn
lần ghim với thay đổi khác. Commit ghim lại nằm SAU commit code (sha ghi trong notebook trỏ về commit
code, không phải về commit ghim lại); `ci_checks.py` mục 6 chỉ đòi sha đó **nằm trên** nhánh
(`repo.is_ancestor`), nên commit ghim lại không cần nằm trong sha đã ghim.



## Ba điều quan trọng nhất

- Notebook luôn kéo đúng bản code đã ghim, không kéo bản khác, để tránh sai lệch phiên bản code.
- Tập test và metric không đổi, vì phải so được với công bố tham chiếu.
- Kết quả chỉ được dùng khi commit đã ghim nằm trên nhánh `experiment`,
  và khi merge vào nhánh `experiment` không phải sửa bất kỳ file nào.

## Nhật ký một lần chạy

Mỗi lần chạy có một thư mục kết quả riêng. Trong đó:

| File            | Khi nào có     | Nội dung                                                                 |
| --------------- | -------------- | ------------------------------------------------------------------------ |
| `run.log`       | luôn có        | từng bước đã chạy, kèm số giây của bước tốn thời gian                     |
| `errors.json`   | chỉ khi có lỗi | kiểu lỗi, vết gọi, thứ còn thiếu (`requires`), máy đã chạy               |
| `metrics.json`  | khi chấm xong  | chỉ số, kèm `label_space`, `neutral_policy`, số ô neutral bị loại         |
| `run_meta.json` | khi chấm xong  | bản ghi lần chạy để tra cứu, và để MLflow gắn nhãn cho run               |
| `mispredictions*.csv` | khi chấm xong | ô đoán sai theo cơ sở `all` (`mispredictions.csv`) và theo cơ sở `paper` (`mispredictions_paper.csv`) |

Trong `run.log`, mỗi dòng bắt đầu bằng một mục, nên tìm bằng `grep`:

| Mục        | Nội dung                                                          |
| ---------- | ----------------------------------------------------------------- |
| `[RUN]`    | bắt đầu/kết thúc lần chạy, `mode=NEW` hay `mode=RESUME`, cấu hình  |
| `[CONFIG]` | cấu hình ĐANG dùng: khoá nào bị lớp nào đè, giá trị hiệu lực       |
| `[STEP]`   | bước đang chạy                                                    |
| `[WARN]`   | việc không làm chết run nhưng người đọc phải biết                  |
| `[ERROR]`  | lỗi - đồng thời được ghi vào `errors.json`                         |
| `[TRACK]`  | ghi kết quả lên MLflow: thành công hay thất bại (kèm mã run)       |

Bảng ghi đè nằm trong `[CONFIG]` chứ không chỉ in ra màn hình: notebook gửi cho giảng viên đã được
làm sạch output, nên bản in trên màn hình không còn lại gì.

Hai quy tắc không được vi phạm:

- Mỗi dòng log được ghi xuống đĩa NGAY, không đệm. Tiến trình bị dừng đột ngột vẫn còn log tới
  dòng cuối cùng đã chạy, nên biết được đã đi tới đâu.
- `errors.json` KHÔNG được tạo khi không có lỗi. File rỗng làm người đọc tưởng đã từng có lỗi,
  còn thiếu file thì rõ ràng là không lỗi.

Xem `src/core/runlog.py` để biết cách gọi, và `docs/04_experiments/metrics.md` cho phần chỉ số.

`run_meta.json` là bản ghi của lần chạy: `run` (trạng thái, lúc bắt đầu/kết thúc), `experiment`
(model, method, exp_id), `data` (dataset, `build` là mã phiên bản dữ liệu, `roles`, `rows` là số bản
ghi của từng vai, `eval_lock` là dấu vân tay tập đánh giá đã khai), `repo` (nhánh và `sha` là commit
đã ghim), `config.sha256`, `task` (không gian nhãn, cách xử lý neutral), `overrides` (khoá bị lớp
sau đè), `env` (colab hay local, thiết bị, mức lượng hoá, thư viện), `attempts[]` và `files[]`.
Mỗi phần tử của `attempts[]` là MỘT lần chạy vào thư mục này, mang `sha`, `config_sha256`, `build`
của chính lần đó - nhìn là biết hai lần có so được với nhau hay không. Ba giá trị quyết định
resume nằm ở `config.sha256`, `data.build` và `repo.sha` (xem [02_rules.md](02_rules.md) mục 13).

Attempt mở khi lần chạy BẮT ĐẦU (`RUNNING`) và chốt khi kết thúc: `FINISHED`, `FAILED`, hoặc
`INTERRUPTED` khi phiên bị NỀN TẢNG ngắt (hết quota Colab, mất kết nối) - lúc đó không ai biết thời điểm
kết thúc, nên `finished`/`seconds` để TRỐNG chứ không bịa. Nếu bản ghi cũng chưa kịp ghi (ngắt trong vài
giây đầu), dấu vết còn lại là dòng `=== lần chạy <thời điểm> - mode=… ===` trong `run.log` và các
`predictions/part_*.jsonl`.

HAI CON SỐ THỜI GIAN KHÁC NHAU, và cả hai đều đúng:

| Con số | Đo cái gì | Dùng khi |
| --- | --- | --- |
| `metrics.json` -> `cost["giây"]` | chỉ phần việc NẶNG: thời gian model sinh câu trả lời (hoặc thời gian huấn luyện ở đường encoder) | so chi phí giữa hai model, hai cấu hình |
| `run_meta.json` -> `attempts[].seconds` | CẢ phiên: từ lúc mở bản ghi tới lúc chốt, gồm nạp model, chấm điểm và ghi file | biết một phiên chiếm máy bao lâu, tính thời gian chạy lại |
Mọi đường dẫn trong file đều TÍNH TỪ GỐC REPO, vì thư mục kết quả bị đem từ máy này sang máy khác.

## Chạy tiếp sau khi bị ngắt

Kết quả dự đoán được ghi theo KHỐI ngay khi từng lô xong: `predictions/part_0001.jsonl`, ... Ngắt
giữa chừng (đứt mạng, Colab hết thời gian, Ctrl+C) thì mất tối đa khối đang viết. Chạy lại đúng
lệnh cũ sẽ tự nhận ra và đi tiếp:

| Trong `run.log`    | Nghĩa là                                                                                          |
| ------------------ | ------------------------------------------------------------------------------------------------- |
| `[RUN] mode=NEW`   | chưa có gì để đi tiếp: chạy từ đầu                                                                 |
| `[RUN] mode=RESUME` | có kết quả dở, và ba giá trị bên dưới chưa đổi: chỉ chạy những mẫu còn thiếu                        |

Ba giá trị quyết định resume (xem [02_rules.md](02_rules.md) mục 13): `config_sha256`, `data.build`
(mã phiên bản dữ liệu) và `repo.sha`. Cả ba đã nằm TRONG mã băm danh tính - tức tên thư mục kết quả
- nên trong một thư mục thì mọi attempt luôn khớp nhau: **không còn chuyện phải chuyển kết quả cũ đi
chỗ khác để chạy lại** (`predictions/_bo-qua-*` đã bỏ). Lần chạy trước đã XONG với đúng ba giá trị đó
thì lượt chạy DỪNG và báo; muốn chạy lại thật thì **xoá thư mục kết quả** rồi chạy lại - ghim lại
một bản code khác thì tự khắc ra thư mục mới.

Điểm số của một lượt chạy tiếp luôn là điểm của CẢ split (mẫu cũ đọc từ các khối, mẫu mới đọc từ
bộ nhớ), không phải điểm của phần còn lại. `metrics.json` ghi lại `resume.mode`, `resume.reused`
và `resume.new` để người đọc biết con số trước mặt sinh ra từ lượt chạy liền mạch hay không.

## Kiểm trước khi chạy

Cell preflight của notebook gọi `src/workflow/preflight.py` TRƯỚC khi nạp model. Một lượt chạy tốn từ
**12 phút** (encoder LoRA) tới **3 giờ 51** (bản KHÔNG lượng hoá, 5 ví dụ) theo **số đo thật của 17 lượt**
(bảng đầy đủ ở `docs/00_workflow/07_colab.md`); hai lượt CHẠY TIẾP chỉ tốn 42 phút và 7 phút vì chỉ làm
nốt phần còn lại, đừng lấy hai số đó làm chuẩn - nên phát hiện thiếu Java, thiếu `test.csv` hay Drive
chỉ đọc ở mẫu thứ 800 là mất cả buổi.
Preflight kiểm trong vài giây:

| Nhóm            | Kiểm gì                                                                              |
| --------------- | ------------------------------------------------------------------------------------ |
| Cấu hình        | `experiments.check`: khoá lạ, thiếu `data.roles`, nhiều dataset, vai trỏ vào `train`   |
| Đường dẫn       | `experiments.requires`: file dữ liệu của từng vai, bảng mã nhãn, prompt, `requires_extra` |
| Dữ liệu         | có dataset đã xử lý chưa, mã phiên bản tính từ config, `data.version` khớp config dataset |
| Tập đánh giá    | `test.csv` khớp `eval_lock` (rules.md mục 11)                                          |
| Thiết bị        | có GPU không, `inference.quantization` khai trong model config có dùng được không      |
| Bộ tách từ      | bộ mà model cần (ví dụ `vncorenlp` cho PhoBERT) chạy được chưa, thiếu gì              |
| Ghi được        | gốc dữ liệu và gốc kết quả (trên Colab: Drive phải mount)                              |
| Trạng thái      | lần này là chạy mới (NEW) hay chạy tiếp (RESUME), và vì sao                            |

Preflight **không ném**: nó gom hết vào `problems` để notebook in ra một lần, kèm cả những việc
không chặn chạy. Lỗi thiếu đường dẫn được ghi vào `errors.json` mục `requires` nếu có truyền `log`
- nhờ vậy câu hỏi "máy này còn thiếu gì" trả lời được ngay từ file kết quả.

## Khi có lỗi

| Hiện tượng                      | Xem ở đâu                               |
| ------------------------------- | --------------------------------------- |
| Notebook dừng giữa chừng        | `results/<hash8>/errors.json` và `run.log` |
| Không thấy kết quả trên DagsHub | `run.log`, mục `[TRACK]`                |
| Thiếu file dữ liệu trên Drive   | `errors.json`, mục `requires`           |
| CI báo đỏ                       | `docs/00_workflow/03_ci.md`             |
