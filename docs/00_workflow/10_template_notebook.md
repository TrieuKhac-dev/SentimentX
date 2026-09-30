# Ô notebook và bản mẫu

> Đọc file này khi: thêm/sửa/xoá một ô trong `templates/experiment/notebook.ipynb`, hoặc tạo notebook cho
> một thí nghiệm mới.
> Liên quan: `docs/00_workflow/01_flow.md` (tạo thí nghiệm, ghim code), `docs/00_workflow/09_cli.md`
> (`run_notebook.py`, `pin.py`), `templates/README.md` (các file trong bản mẫu).

## 1. Bản mẫu là MẪU, không phải CHUẨN

`templates/experiment/` là chỗ để **bắt đầu**, không phải bản mà mọi notebook phải giống.

VÌ SAO ĐỔI CÁCH NHÌN NÀY
Trước đây có một test bắt mọi notebook thí nghiệm phải giống hệt bản mẫu. Hệ quả: sửa một câu trong
bản mẫu trở thành một NGHĨA VỤ - dựng lại cả 12 notebook, ghim lại cả 12, rồi dựng lại gói bàn giao -
kể cả với những lượt chạy đã xong và số đã báo cáo. Notebook của một thí nghiệm đã chạy là **bản ghi
của lượt chạy đó**, không phải thứ phải cập nhật theo bản mẫu: ghim lại nó là đổi bản code đứng sau
con số đã công bố.

VẬY CÁI GÌ ĐƯỢC KIỂM
Bỏ phần "giống bản mẫu", giữ lại đúng những thứ làm hỏng lượt chạy. Với TỪNG notebook thí nghiệm
(`tests/workflow/test_templates.py::TestExperimentNotebooks`):

| Phép kiểm | Vì sao |
| --- | --- |
| Ô ghim trỏ đúng thí nghiệm của chính nó | notebook sai `EXP_DIR` thì kết quả ghi vào thư mục thí nghiệm KHÁC, vẫn ra số bình thường |
| Ô ghim là ô code ĐẦU TIÊN | `scripts/pin.py` và ô bootstrap đều dựa vào vị trí đó |
| Mọi ô code biên dịch được | notebook không được biên dịch ở đâu cả; lỗi cú pháp chỉ lộ ra khi bấm Run all |

Cộng thêm `tests/api/test_api.py` (ô notebook chỉ được import từ `src.api` - mục 3) và
`tests/workflow/test_bootstrap.py` (hành vi của ô bootstrap, kiểm bằng điểm tiêm chứ không đọc chuỗi
trong ô).

## 2. Một notebook gồm những ô nào

Bảng dưới là **sáu ô CODE**, theo đúng thứ tự; thứ tự đó là hợp đồng giữa notebook,
`scripts/pin.py` và `scripts/run_notebook.py`. Notebook ĐẦY ĐỦ có **tám ô**: sáu ô code này
cộng **hai ô markdown** - ô mở đầu (giới thiệu notebook) và ô "Kết quả nằm ở đâu" (ngay
trước ô kết thúc). Hai ô markdown không nằm trong hợp đồng, nhưng đừng xoá: đó là phần
người nhận đọc trước tiên.

| # | Ô | Nội dung | Nhận ra bằng |
| --- | --- | --- | --- |
| 1 | Ô GHIM | chỉ hằng số: `REPO_URL`, `REPO_BRANCH`, `REPO_SHA`, `EXP_DIR` | `src/workflow/notebooks.MARKER` |
| 2 | Ô bootstrap | kéo mã nguồn (phải làm TRƯỚC khi import `src`), rồi gọi `bootstrap.prepare`, `bootstrap.verify_checkout`, `bootstrap.install_packages`, `bootstrap.model_assets` | chuỗi `from src.api import bootstrap` |
| 3 | Ô cấu hình | nạp config, chọn đường chạy (prompt / encoder), in ra đang chạy gì | - |
| 4 | Ô kiểm trước khi chạy | gọi `preflight.run(...)`, in danh sách việc phải sửa, DỪNG nếu có vấn đề; ngắt phiên SAU khi in và TRƯỚC khi dừng | `preflight.run` |
| 5 | Ô chạy | đúng MỘT lời gọi `experiment_run.run(...)` (hoặc `encoder_run.run(...)`) | `src/workflow/notebooks.RUN_MARKER` |
| 6 | Ô kết thúc | in link DagsHub nếu lượt chạy đã được ghi nhận, rồi ngắt phiên Colab | - |

Việc chuẩn bị môi trường (mount Drive, dò thư mục nhóm, nạp env, đặt hai gốc đường dẫn, cài gói còn
thiếu, tải tài nguyên model) nằm trong `src/workflow/bootstrap.py`, KHÔNG nằm trong ô: ô dài 317 dòng
thì mỗi lần sửa phải sửa ở mọi notebook, mà notebook đã ghim thì không sửa được nữa.

## 3. Ba việc: THÊM, SỬA, XOÁ ô

**THÊM một ô.** Đặt ngay dưới ô cấu hình (trước ô kiểm trước khi chạy) nếu nó chỉ để xem thông tin.
Logic đi vào THƯ VIỆN (`src/...`), ô chỉ gọi:

```python
from src.api import <tên>          # mặt tiền: ô KHÔNG import thẳng vào ruột src/
```

Vì sao: notebook ghim MỘT commit rồi chạy rất lâu sau đó, còn `src/` thì đổi chỗ. Mặt tiền `src/api/`
là chỗ duy nhất notebook trỏ tới, nên chuyển nhà một file trong `src/` chỉ sửa file trong `src/api/`.
Câu in ra nên là tiếng Việt và nói được chuyện gì đang xảy ra: `run.log` là thứ người đọc dò lỗi sau
này.

**SỬA một ô.** Hỏi trước: việc này có đổi CÁCH ĐO không?

| Sửa gì | Làm gì |
| --- | --- |
| Cách đo (prompt, số ví dụ, tham số model, cách chấm) | Thí nghiệm MỚI (`scripts/new_experiment.py`), không sửa thí nghiệm cũ |
| Chỉ câu chữ in ra, thêm dòng ghi chú | Sửa, rồi ghim lại - nhưng CHỈ khi thí nghiệm đó chưa chạy ở đâu |

**XOÁ một ô.** Hai ô không được xoá: ô GHIM (mọi thứ khác dựa vào nó) và ô bootstrap (không còn nó
thì notebook không có `src/` để chạy). Ô khác xoá được, nhưng nhớ: `scripts/run_notebook.py` tìm ô
chạy bằng dấu `RUN_MARKER`, nên xoá ô chạy là notebook không chạy được nữa - thiếu dấu bị báo thành
LỖI kèm cách sửa, chứ không im lặng bỏ qua.

Một luật không đổi: **ô notebook chỉ import từ `src.api`**. Test `tests/api/test_api.py` chặn, và nó
chặn cả việc viết logic vào file mặt tiền.

### 3.1. Bảng tra nhanh: muốn gì → làm gì → luật phải giữ → AI BẮT LỖI

| Muốn gì | Làm gì | Luật phải giữ | Ai bắt lỗi |
| --- | --- | --- | --- |
| Thêm ô chỉ để XEM thông tin | Chèn ngay dưới ô cấu hình | Ô không chứa logic; chỉ gọi `src.api` | `tests/api/test_api.py` (a) + mọi ô phải biên dịch (`test_templates.py`) |
| Đổi CÁCH ĐO (prompt, số ví dụ, tham số, cách chấm) | **Thí nghiệm mới** | Notebook đã chạy là bản ghi: ghim lại là đổi bản code sau con số đã công bố | Người duyệt + `run_meta.json` (config_sha256) |
| Sửa câu chữ trong ô của thí nghiệm CHƯA chạy | Sửa rồi `pin.py` ghim lại | ô GHIM vẫn là ô code đầu tiên | `test_templates.py` (`o_ghim_la_o_code_dau_tien`) |
| Xoá ô | Được, trừ ô GHIM và ô bootstrap | Đúng MỘT ô mang `RUN_MARKER` | `test_templates.py` (đếm ô chạy) |
| Thêm ô TRƯỚC ô CHẠY | Nhớ: nó **cũng chạy** ở `--preflight-only` | `--preflight-only` là cờ của `scripts/run_notebook.py`, dừng TRƯỚC ô mang dấu | `tests/workflow/test_run_notebook.py` |
| Thêm ô SAU ô CHẠY | Nhớ: nó **không** chạy ở `--preflight-only` (đọc `run_result`) | Ô sau ô chạy phải chịu được việc `run_result` chưa có | `test_run_notebook.py` (cắt từ ô CHẠY trở đi) |
| Đổi bản mẫu cho thí nghiệm MỚI | Sửa `templates/experiment/`, chạy test | Không bắt 12 notebook đang có phải cập nhật theo | `tests/workflow/test_templates.py` |
| Cập nhật cell cho CẢ BỘ notebook | Mục 4.1 dưới đây (script một lần) | Giữ ô GHIM; `EXP_DIR` đúng; migrate + ghim CÙNG một lượt | `test_templates.py` (per-notebook) |
| Sửa logic | **Sửa `src/`**, không sửa ô | Ô chỉ là lớp gọi mỏng | `test_templates.py::test_o_bootstrap_mong_...` |

### 3.2. Ô nào lỗi cũng phải ngắt phiên Colab

Phiên Colab tính vào hạn mức GPU theo thời gian mở, kể cả khi không ai lập trình nữa. Ô nào lỗi thì
Jupyter dừng ngay tại ô đó, nên mọi việc ở các ô SAU - kể cả ô kết thúc - không chạy. Vì vậy các ô code
được bọc trong **khối bảo vệ** `runtime.end_session_on_error()` (mặt tiền: `from src.api import
end_session_on_error`), với luật: **IN xong rồi mới NGẮT**; không ngắt khi người dùng bấm Stop
(`KeyboardInterrupt`).

Ngoại lệ duy nhất: lời gọi `experiment_run.run(plan)` ở ô CHẠY để ở mức ngoài cùng - đường lỗi của LƯỢT
CHẠY do chính thư viện ngắt (nhật ký đóng trước, rồi mới ngắt), bọc thêm là ngắt hai lần cho cùng một
lượt. Ai sửa ô này thì `test_templates.py::test_moi_o_co_the_loi_deu_co_khoi_bao_ve` báo ngay.

## 4. Quy trình 5 bước

1. **Sửa bản mẫu** `templates/experiment/notebook.ipynb` (và `config.yaml`, `README.md` nếu cần).
2. **Chạy test**: `python -m unittest discover -s tests`. Test biên dịch từng ô code, nên lỗi cú pháp
   lộ ra ở đây chứ không phải lúc người nhận bấm Run all.
3. **Chạy thử trên máy cá nhân**, không cần Jupyter:
   ```bash
   python scripts/run_notebook.py <model>/<method>/<expNNN> --preflight-only   # chỉ tới ô kiểm trước
   python scripts/run_notebook.py <model>/<method>/<expNNN> --limit 8          # chạy nhanh 8 mẫu
   ```
   `--limit` chỉ đổi `n` trong RAM, không ghi file nào. Hai cờ này là của `scripts/run_notebook.py`;
   notebook thật trên Colab không có cờ nào.
4. **Ghim rồi commit**: `python scripts/pin.py <model>/<method>/<expNNN>` - một mình file notebook,
   rồi đẩy lên nhánh `experiment` (`docs/00_workflow/01_flow.md`).
5. **KHÔNG dựng lại notebook của thí nghiệm đã chạy.** Chỉ khi bản ghi đó thật sự sai (ví dụ trỏ sai
   `EXP_DIR`) thì mới sửa, và khi đó phải ghim lại + chạy lại + nói rõ trong commit vì sao con số cũ
   không còn dùng được.

## 5. CI kiểm gì cho phần này

CI chạy **toàn bộ** test (`python -m unittest discover -s tests`) cùng `python scripts/ci_checks.py`;
không có danh sách test riêng cho notebook, nên test mới thêm ở đâu trong `tests/` cũng được chạy.

| Nhóm test | Kiểm gì |
| --- | --- |
| `tests/workflow/test_templates.py` | bản mẫu và MỌI notebook thí nghiệm: hợp lệ nbformat, ô code biên dịch, ô ghim đúng thí nghiệm, ô chạy có dấu, thứ tự ô bootstrap |
| `tests/api/test_api.py` | ô notebook chỉ import `src.api`; tên trên mặt tiền phải có thật; file mặt tiền chỉ re-export |
| `tests/workflow/test_bootstrap.py` | hành vi ô bootstrap (mount, env, cài gói, kiểm commit, tài nguyên model) qua điểm tiêm |
| `tests/workflow/test_run_notebook.py` | `run_notebook.py`: giữ ô nào, chèn prelude `--limit` ở đâu |

Thấy CI đỏ ở nhóm nào thì đọc `docs/00_workflow/03_ci.md`: mỗi test ở đây ứng với một cách hỏng cụ
thể của lượt chạy, không phải một quy ước hình thức.

### 4.1. Cập nhật cell cho CẢ BỘ notebook (việc một lần)

Đôi khi cả bộ notebook cần nhận CÙNG một thay đổi cell (đợt Batch 5b là một ví dụ: ô bootstrap mỏng đi,
thêm khối bảo vệ, sửa đường dẫn cũ trong chú thích). Việc đó là việc MỘT LẦN, không phải một cơ chế
chạy thường trực - bất biến "mọi notebook phải giống bản mẫu" đã bị bỏ, và script `sync_notebooks.py`
theo nó cũng bị bỏ.

Quy trình:

1. Sửa bản mẫu (`templates/experiment/notebook.ipynb`) và chạy test.
2. Dựng lại ô của cả bộ: **một script một lần**, chạy `--dry-run` trước (nó in ô nào không có trong bản
   mẫu để bạn kịp nhìn), rồi `--yes`. Script giữ ô GHIM và `EXP_DIR`, và **không** tự ghim commit.
3. Ghim lại cả bộ: `python scripts/pin.py <model>/<method>/<expNNN> --allow-dirty` cho từng thí nghiệm.
4. Commit **cùng một lượt**: bộ ô mới và bản ghim phải nằm cạnh nhau, nếu không sẽ tồn tại một trạng
   thái "ô mới nhưng ghim bản code cũ".

Script đó đã chạy xong và đã bị XOÁ khỏi cây làm việc (giữ trong lịch sử git). Lấy lại khi cần:

```bash
git show 1abb88d:scripts/migrate_notebooks_5b.py > scripts/migrate_notebooks_5b.py
```

(commit `1abb88d` là commit đưa nó vào; `3bba9ce` là commit xoá nó.)
