# 08. Chạy notebook trên máy cá nhân (GPU CUDA)

> Đọc file này khi: chạy một thí nghiệm đã ghim trên máy có GPU thay vì trên Colab.
> Liên quan: `docs/00_workflow/07_colab.md`, `docs/00_workflow/02_rules.md`, `docs/05_config/07_env.md`

## 1. Khác gì so với chạy trên Colab

| Việc | Colab | Máy cá nhân |
| --- | --- | --- |
| Gốc dữ liệu | `<Drive>/data` (ô bootstrap tự đặt) | `<repo>/data` |
| Gốc kết quả | `<Drive>/experiments` | `<repo>/experiments` |
| Mount Drive | có, người chạy bấm Allow | không |
| Nạp biến môi trường | Colab Secrets rồi `<Drive>/env/.env.colab` | file `.env` ở gốc repo |
| Cài gói | tự cài gói còn thiếu | `pip install -r requirements.txt` trước (một lần) |
| Model | tải từ Hugging Face | nên trỏ vào bản có sẵn: `data/models/<tên>/` |

Notebook tự nhận ra đang ở đâu (`runtime.is_colab()`), nên **cùng một file** chạy được cả hai nơi;
không có bản notebook riêng cho máy cá nhân.

## 2. Chuẩn bị (một lần)

```bash
pip install -r requirements.txt
# torch là bản CUDA, cài riêng theo hướng dẫn ở đầu requirements.txt
```

- `.env` ở gốc repo cần `DAGSHUB_TOKEN` nếu muốn kết quả lên DagsHub. Thiếu token vẫn chạy, chỉ là
  phần ghi nhận tự hạ cấp thành ghi chú trong `run.log`.
- Kiểm GPU trước khi chạy: `python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"`.
  GPU 6 GB chạy được Qwen3-4B nhờ lượng hoá 4-bit (`bitsandbytes`).
- Model 4B nên có sẵn trên đĩa để khỏi tải 8 GB mỗi lần: đặt vào `data/models/Qwen3-4B-Instruct-2507/`
  rồi đặt biến môi trường `SENTIMENTX_MODEL=data/models/Qwen3-4B-Instruct-2507` TRƯỚC khi mở Jupyter;
  bỏ trống thì notebook dùng `checkpoint` trong `configs/models/<model_id>.yaml` (tải một lần vào
  cache `~/.cache/huggingface`, các lần sau dùng lại). Nguồn trọng số KHÔNG vào tên thư mục kết quả,
  nên máy cá nhân và Colab vẫn ra cùng một thư mục cho cùng một phép đo.
- Kernel Jupyter phải có `ipykernel`. Thiếu gói này thì chọn kernel `base` xong bấm Run all KHÔNG
  chạy ô nào và cũng không hiện lỗi rõ ràng (kernel tắt ngay lúc khởi động). Kiểm rồi cài:

  ```bash
  python -c "import ipykernel; print(ipykernel.__version__)"   # lỗi ModuleNotFoundError thì:
  pip install ipykernel
  ```

  VS Code đã kèm sẵn tiện ích Jupyter (`ms-toolsai.jupyter`) nên chỉ cần đúng gói này; không cần
  `notebook` hay `jupyterlab` (chúng kéo theo cả một chồng gói nữa để mở giao diện trong trình duyệt).
  Sau khi cài, chọn lại kernel trong notebook rồi Run all.
- Lần đầu làm việc với repo: chạy `git fetch origin` một lần. Notebook kiểm commit đã ghim có nằm
  trên nhánh `experiment` bằng ref `origin/experiment`; repo mới `git init` rồi push mà chưa lần nào
  fetch thì không có ref nào cả, notebook in cảnh báo `Chưa có origin/experiment trong repo nên không
  kiểm được ...` (cảnh báo, không phải lỗi - `python scripts/ci_checks.py` trên CI là nơi kiểm chắc).

## 3. Trước khi bấm Run all: kiểm ô GHIM

Ô đầu notebook có `REPO_SHA`, do `python scripts/pin.py <model>/<method>/<expNNN>` ghi. Trên máy cá
nhân, `repo.prepare()` so `HEAD` với `REPO_SHA`:

- Trùng nhau thì notebook báo `dùng bản code đang có` và chạy tiếp, KHÔNG đụng vào cây làm việc.
- Khác nhau thì nó lấy thêm đúng commit đã ghim rồi `git checkout` commit đó (chế độ tách rời), tức
  là **đưa cây làm việc về bản cũ**; nhánh `experiment` và mọi ref `origin/*` giữ nguyên. Chỉ nên để
  việc đó xảy ra khi bạn đang không làm dở gì: `git status` sạch, không có việc chưa commit.
  Nếu commit đã ghim không có trên remote (chưa đẩy, hoặc gõ sai) thì notebook DỪNG ngay và nói rõ -
  nó không thử hai cách dành cho thư mục trống, vì hai cách đó gỡ `origin` và làm repo thành repo
  nông (`git log` cụt từ commit đó về sau).

Muốn chạy đúng bản code mới nhất của mình: commit, đẩy lên nhánh `experiment`, rồi **ghim lại**
(`python scripts/pin.py qwen3-4b-instruct-2507/prompt-cot/exp002`) trước khi Run all.

Sau khi chạy xong, thư mục code đang ở commit ghim (tách rời). **Trước lần Run all sau, chạy
`git switch experiment`.** Lý do: notebook đọc hằng số `REPO_SHA` từ FILE notebook, mà file đó lúc này
là bản của chính commit ghim - và bản ấy trỏ tới commit ghim của THẾ HỆ TRƯỚC (mỗi lần ghim lại là
một commit mới). Nên Run all lần nữa từ cây tách rời sẽ lùi repo thêm một đời code: vẫn ra kết quả,
nhưng là kết quả của mã cũ hơn, và chỉ có một dòng cảnh báo để nhận ra. Đã gặp thật ngày 25/09/2026.

## 4. Chạy

**Cách khuyến nghị: dùng script, không cần tiện ích Jupyter.**

```bash
python scripts/run_notebook.py qwen3-4b-instruct-2507/prompt-cot/exp002
```

Script này tự làm đủ bốn việc: (1) đọc `REPO_SHA` từ chính ô GHIM của notebook, (2) kéo ĐÚNG commit
đó vào một thư mục TẠM, (3) chạy lần lượt các ô code trong một kernel `python3` như bấm Run all,
(4) để kết quả về thẳng `<repo>/experiments/...` (vì `SENTIMENTX_RESULTS_ROOT` trỏ vào repo).

Vì chạy trong thư mục tạm nên **repo của bạn không bị đụng**: file chưa commit, file chưa `git add`,
thư mục chưa theo dõi đều còn nguyên - cuối lượt chạy script tự so trạng thái trước/sau và in ra.

| Việc | Lệnh |
| --- | --- |
| Chạy đủ (như Run all) | `python scripts/run_notebook.py <model>/<method>/<expNNN>` |
| Kiểm trước khi chạy, chưa tốn GPU (~30 giây) | thêm `--preflight-only` |
| Chạy thử vài mẫu (`n = N`, KHÔNG sửa file nào) | thêm `--limit 8` |
| Ghi thêm toàn bộ đầu ra ra file | thêm `--log <đường dẫn>` |
| Giữ thư mục code tạm để soi | thêm `--keep` |

`--limit N` hoạt động bằng cách ép `n = N` ngay trong RAM sau khi nạp config, nên tên thư mục kết quả
có `nN` và không lẫn với lượt chạy đủ; config trong git vẫn nguyên.

**Cách thay thế: mở notebook bằng Jupyter/VS Code rồi bấm Run all.** Được, nhưng nhớ hai điều:
kernel phải có `ipykernel` (mục 2), và bootstrap sẽ `git checkout` commit ghim NGAY TRONG repo -
cây làm việc bị đưa về bản cũ, nên chỉ làm khi `git status` sạch. Xem mục 3.

Muốn xem **prompt thật** gửi cho model (không phải đọc file prompt rồi đoán):

```bash
python scripts/show_prompt.py qwen3-4b-instruct-2507/prompt-cot/exp002
```

Công cụ in nguồn (file prompt/ví dụ/hệ thống + sha), bản ghi hội thoại dễ đọc, chuỗi SAU chat
template - đúng thứ model nhận - số token, và phần bị cắt ở đuôi nếu vượt `max_length`.

1. Mở `experiments/<model_id>/<method>/expNNN/notebook.ipynb` bằng Jupyter hoặc VS Code (không phải
   Colab), chọn kernel có `torch` CUDA.
2. Run all. Ô bootstrap sẽ in `Nơi chạy : local`, `Gốc dữ liệu : <repo>/data`, `Gốc kết quả :
   <repo>/experiments`, `Code : ... <sha>`.
3. Ô preflight phải in `Không có việc nào phải sửa.` trước khi tới ô chạy. Preflight kiểm GPU, mức
   lượng hoá, dữ liệu, `eval_lock`, và trạng thái NEW/RESUME.

## 5. Kết quả và thời lượng

- Kết quả: `experiments/<model_id>/<method>/expNNN/results/<hash8>/` - `<hash8>` là mã băm danh tính
  (cấu hình + prompt + ví dụ + dữ liệu + commit); phần nhẹ (`run.log`, `run_meta.json`, `metrics.json`,
  `metrics.csv`, `mispredictions.csv`) vào git; phần nặng (`predictions/`, `predictions.csv`, `plots/`,
  `model/`) đã bị `.gitignore` chặn.
- Tham chiếu để ước lượng trên GPU 6 GB, Qwen3-4B 4-bit, prompt CoT 2 ví dụ: nạp model khoảng 25 đến
  35 giây, mỗi review khoảng 6 đến 10 giây. Tập `val` 1.524 mẫu vì thế nên chạy `n` nhỏ trước (khai
  `n: 8` trong config thí nghiệm) rồi mới chạy cả split; `n` khác nhau ra hash khác nên không lẫn.
- Bị ngắt giữa chừng (hết pin, tắt máy, Ctrl+C): Run all lại. Notebook chạy tiếp từ
  `predictions/part_*.jsonl` (`[RUN] mode=RESUME` trong `run.log`), và điểm số vẫn tính trên cả split.
  Muốn chạy lại từ đầu thì **xoá thư mục `results/<hash8>/`** rồi Run all.

## 6. Kết quả chỉ dùng để so khi nào

Theo `docs/00_workflow/02_rules.md` mục 3 và 4:

- Kết quả chỉ được dùng khi commit đã ghim nằm trên nhánh `experiment`, và khi đưa nhánh cá nhân vào
  `experiment` **không phải sửa file nào**.
- Nếu phải sửa file khi hợp nhất thì cách làm là: hợp nhất xong, **chạy lại trên nhánh `experiment`**
  rồi lấy kết quả của lần chạy lại; kết quả trước khi hợp nhất không dùng nữa.
- Chạy trên máy cá nhân ghi kết quả vào repo, nên muốn đưa chúng cho người khác thì commit phần nhẹ,
  hoặc copy sang Drive; kết quả chạy trên Colab thì làm ngược lại.
