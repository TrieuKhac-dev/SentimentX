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

Thứ tự này là hợp đồng giữa notebook, `scripts/pin.py` và `scripts/run_notebook.py`:

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
