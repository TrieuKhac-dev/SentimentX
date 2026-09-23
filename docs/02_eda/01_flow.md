# Luồng EDA (khảo sát dữ liệu)

## 1. EDA để làm gì

EDA trả lời đúng **một** câu hỏi:

> **"Dữ liệu đang như thế nào?"**

EDA **không sửa** dữ liệu. Nó không xoá dòng trùng, không chuẩn hoá văn bản,
không lọc nhiễu. Nó chỉ **đo** và **ghi số liệu**, để ta có căn cứ chọn policy
cho pipeline.

Hệ quả về mặt kỹ thuật: **đầu vào của EDA là `data/raw/`** và mọi thứ EDA sinh ra
chỉ nằm trong `data/reports/eda/versions/<mã>/`. Không có file nào trong
`data/processed/` bị EDA chạm tới.

## 2. Luồng tổng quát

```
data/raw/<tên>/data_train.csv, data_val.csv, data_test.csv      (chỉ đọc)
        │
        │  src/dataset.py + src/loaders/  : đọc bằng utf-8-sig, bỏ cột `drop_columns`,
        │                                   đổi tên cột văn bản thành `text`
        ▼
run_eda.py --dataset <tên>
        │   • đọc config: configs/datasets/<tên>.yaml + configs/pipeline.yaml
        │   • tính mã phiên bản (src/versioning.py) → thư mục phiên bản
        │   • lần lượt gọi 5 module theo src/registry.py::EDA_MODULES, mỗi module
        │     nhận cùng một `context` và trả về một MỤC báo cáo (dict)
        ▼
EDA 01 overview → EDA 02 label_aspect → EDA 03 quality_noise → EDA 04 text_analysis
                                                        → EDA 05 split_leakage
        │   mỗi module: ĐO → tự ghi CSV/JSON chi tiết vào thư mục phiên bản
        ▼
data/reports/eda/versions/<mã>/
        eda_result.json      (gộp đủ 5 mục — file mà build_report.py đọc)
        01_overview.json …   (file kết quả riêng của từng mục)
        0X_<mục>_*.csv       (bảng số liệu chi tiết của từng mục)
        │
        ▼
build_report.py --phase eda --dataset <tên>   →   report.html   (mở bằng trình duyệt)
```

Bảng dưới đây là **bản đồ 5 mục**; chi tiết từng mục ở
[03_modules.md](03_modules.md):

| Mục | Module (`src/eda/`) | Đo gì (một dòng) | File số liệu chính |
|-----|---------------------|------------------|--------------------|
| EDA 01 | `overview.py` | cấu trúc từng file gốc, ô trống từng cột, độ dài review theo ký tự và theo từ | `01_overview.json`, `01_*.csv` |
| EDA 02 | `label_aspect.py` | phân bố `positive`/`negative`/`neutral`/ô trống theo khía cạnh, số khía cạnh mỗi review, dòng không có nhãn nào, ma trận xuất hiện cùng nhau | `02_label_aspect.json`, `02_*.csv` |
| EDA 03 | `quality_noise.py` | rỗng, trùng chính xác, trùng theo khoá so trùng, gibberish, emoji, ký tự lặp, teencode / từ lạ, quảng cáo, code / HTML | `03_quality_noise.json`, `03_*.csv` |
| EDA 04 | `text_analysis.py` | từ hay gặp, cụm 2 từ theo khía cạnh, tỉ lệ có dấu / không dấu, kích thước từ vựng | `04_text_analysis.json`, `04_*.csv` |
| EDA 05 | `split_leakage.py` | trùng lặp giữa các split (hai cách đếm) và xung đột nhãn | `05_split_leakage.json`, `05_*.csv` |

Thứ tự chạy **chính là** thứ tự xuất hiện trên báo cáo; muốn chèn một mục mới thì
chỉ cần thêm module vào `EDA_MODULES` — xem [05_extend.md](05_extend.md).

## 3. Công tắc và ngưỡng đang áp dụng

EDA **không có công tắc bật/tắt riêng**: nó là phép đo, luôn chạy đủ 5 mục. Các
tham số dưới đây quyết định *đo như thế nào*; giá trị ghi ở đây là giá trị **đang
dùng trong repo**:

| Tham số | Nơi khai báo | Giá trị hiện tại | Ảnh hưởng |
|---------|--------------|------------------|-----------|
| `clean.deduplicate.ignore_diacritics` | `configs/pipeline.yaml` | **`false`** (TẮT) | khoá so trùng của EDA 03 và EDA 05 **giữ dấu tiếng Việt** — đúng bằng khoá mà pipeline dùng, nên hai bên không bao giờ lệch nhau. Đây là **công tắc duy nhất** của pipeline mà EDA đọc |
| `GIBBERISH_RATIO_THRESHOLD` | `src/config.py` | `0.5` | review bị coi là "ứng viên gibberish" khi ≥ 50% token không giống từ (định nghĩa token bất thường: [02_metrics.md](02_metrics.md) §4) |
| `REPEATED_CHAR_MIN` | `src/config.py` | `3` | ký tự lặp liên tiếp từ 3 lần trở lên mới tính là "có ký tự lặp" |
| `AD_PATTERNS` | `src/config.py` | 11 mẫu gõ tay (`[qc]`, `[tb]`, `viettel`, `http(s)://`, `bit.ly`, `soạn … gửi`…) | nhóm "có dấu hiệu quảng cáo" |
| `CODE_PATTERNS` | `src/config.py` | 6 mẫu (thẻ HTML, entity HTML, SQL, `function(`, `#include <`…) | nhóm "có dấu hiệu code / HTML" |
| quy tắc teencode | `src/utils.py::teencode_reasons` | 5 quy tắc cấu trúc | bảng từ bị gắn cờ (mức TOKEN, không phải mức review) |
| `TOP_N` | `src/eda/quality_noise.py` | `20` | số mục nhiều nhất đưa vào bảng / biểu đồ |
| `MIN_CANDIDATE_COUNT` | `src/eda/quality_noise.py` | `3` | từ lạ phải xuất hiện ≥ 3 lần mới vào bảng |
| `AUDIT_TOP_WORDS` | `src/eda/quality_noise.py` | `300` | số từ phổ biến nhất đem ra **tự kiểm dương tính giả** |
| `EXAMPLE_SEED` | `src/eda/quality_noise.py` | `20240917` | hạt giống lấy mẫu ví dụ minh hoạ — chạy lại ra đúng ví dụ cũ |
| `EXAMPLES_PER_SPLIT_TABLE` / `_CSV` | `src/eda/quality_noise.py` | `1` / `3` | số ví dụ mỗi nhóm mỗi split trên bảng / trong CSV |
| `TOP_WORDS` / `TOP_BIGRAMS` | `src/eda/text_analysis.py` | `25` / `5` | số từ hay gặp và số cụm 2 từ mỗi khía cạnh |

> **Muốn đổi cách đo** thì sửa hằng số trong `src/config.py` (ngưỡng dùng chung cho
> cả EDA lẫn pipeline) hoặc trong `src/eda/*.py` (chỉ EDA dùng). Những thay đổi này
> **không** làm đổi mã phiên bản dữ liệu, vì mã phiên bản chỉ tính từ config dataset
> + `configs/pipeline.yaml` + nội dung dữ liệu gốc.

## 4. Chạy

EDA tách thành hai việc: **tính** và **vẽ**.

```bash
# 1) Tính toán và ghi số liệu (không sinh HTML)
python run_eda.py --dataset cosmetics

# 2) Vẽ báo cáo từ số liệu đã ghi
python build_report.py --phase eda --dataset cosmetics
```

Kết quả nằm trong một thư mục **theo phiên bản**:

| File | Nội dung |
|------|----------|
| `data/reports/eda/versions/<mã>/report.html` | **báo cáo duy nhất cho người đọc** — mở bằng trình duyệt |
| `data/reports/eda/versions/<mã>/eda_result.json` | số liệu mà báo cáo đọc lại (đủ 5 phần) |
| `data/reports/eda/versions/<mã>/0X_<phần>.json` | file kết quả riêng của từng phần, ví dụ `01_overview.json` |
| `data/reports/eda/versions/<mã>/0X_<phần>_*.csv` | số liệu chi tiết từng phần |

Báo cáo chỉ có **một** định dạng là HTML: bản Markdown đã bỏ vì nó lặp lại đúng
bấy nhiêu số liệu mà không có biểu đồ. Khi chạy
`python build_report.py --dataset cosmetics`, công cụ **mở luôn hai file HTML**
(EDA và Pipeline) bằng trình duyệt mặc định; thêm `--no-open` nếu không muốn mở.

Vì bước tính và bước vẽ tách rời, muốn đổi loại biểu đồ hay sửa giao diện chỉ cần
chạy lại `build_report.py`, **không phải chạy lại EDA**.

Cách mở báo cáo cũ, hoặc danh sách phiên bản đã chạy:

```bash
python build_report.py --list                       # xem mọi phiên bản
python build_report.py --version cosmetics-v0.1.0-b37ecfce --phase eda
```

> Mã phiên bản đổi mỗi khi **config hoặc dữ liệu gốc** đổi (mã hash tính từ cả
> hai), nên hãy lấy mã đúng từ `--list`. Vì vậy sau mỗi lần sửa
> `configs/pipeline.yaml` sẽ có thêm một thư mục phiên bản mới, không ghi đè bản cũ.

Nếu gõ sai tên dataset, `run_eda.py` dừng ngay với dòng `LỖI: …` kèm gợi ý tên gần
đúng và trả **mã thoát `2`** (không in traceback, không ghi thư mục rỗng).

## 5. EDA liên hệ với Pipeline như thế nào

```
EDA  ──►  phát hiện vấn đề  ──►  quyết định policy  ──►  DATA PIPELINE
```

Ví dụ cụ thể:

| EDA phát hiện (số liệu của dataset cosmetics) | Pipeline làm gì |
|---------------|-----------------|
| 184 dòng trùng chính xác trong train (221 trên 3 split) | Bật `deduplicate.exact: true` |
| 242 dòng trùng theo khoá so trùng trong train (291 trên 3 split) | Bật `deduplicate.normalized: true` — khoá **giữ dấu**; `ignore_diacritics: false` vì bỏ dấu chỉ loại thêm 5 dòng (0,03%) |
| 4 review / 4 ô nhãn xung đột nhãn giữa các split | `conflict_policy: quarantine` (cách ly, không tự chọn) |
| 388 ứng viên gibberish trong train (487 trên 3 split) | Bật `remove_gibberish: true` |
| 59 dòng có dấu hiệu quảng cáo trong train (78 trên 3 split) | Bật `remove_ads: true` |
| 1 dòng có dấu hiệu code / HTML trong train (1 trên 3 split) | Bật `remove_code: true` (loại 1 dòng) |
| 3604 dòng có ký tự lặp trong train | `repeated_chars: false` (giữ, vì mang cảm xúc) — bật chỉ để thực nghiệm |
| **68 dòng val/test trùng train (91 theo khoá so trùng)** | Bật `clean.leakage.remove_eval_overlap: true` |
| 2884 dòng không có nhãn khía cạnh nào (3 split) | Giữ lại trong `processed_*.csv` nhưng không sinh bản ghi ABSA |
| Teencode / từ lạ: token hay gặp nhất là `k`, `mn`, `đc`, `mng`, `sp`, `vs`... | **Không thay** — giữ nguyên văn bản gốc, chỉ ghi nhận để phân tích |

> Hai con số ở dòng "rò rỉ dữ liệu" và dòng ở pipeline (84 dòng bị loại) **không
> bằng nhau** là đúng như thiết kế: EDA đo trên dữ liệu gốc còn Clean xoá nhiễu
> trước rồi mới xử lý rò rỉ. Chi tiết: [02_metrics.md](02_metrics.md) §12.

Bảng policy đầy đủ (kèm công tắc hiện tại): [03_pipeline/01_flow.md](../03_pipeline/01_flow.md) §4.

## 6. Điều EDA KHÔNG làm

Các phép sau **thuộc về EDA**, pipeline **không cần**:

- đếm emoji, đếm token teencode / từ lạ
- tìm top n-gram
- tính phân phối nhãn theo từng khía cạnh
- tính độ dài review theo ký tự / từ (p50, p95, p99)
- tìm ứng viên typo

Pipeline chỉ giữ lại những gì **thực sự làm thay đổi dữ liệu**.

## 7. Vì sao EDA không nằm trong pipeline

Có thể hình dung sai thành:

```
Raw → EDA → Pipeline → EDA   ← cách này rối
```

Cách đúng là **ba pha độc lập**:

```
PHA 1: Raw → EDA → hiểu dữ liệu → chốt policy
PHA 2: Raw → Pipeline → processed data
PHA 3 (nếu cần): processed data → Data Quality Report
```

`Data Quality Report` ở pha 3 **không phải EDA lần hai** — nó là **cổng chất lượng**
của pipeline: kiểm tra dữ liệu đầu ra có hợp lệ không, số dòng có khớp không, nhãn
có bị đổi không. Việc này nằm ở `final_validate` trong pipeline — xem
[03_pipeline/02_steps.md](../03_pipeline/02_steps.md) §6.

Nhờ tách như vậy, pipeline **bắt đầu từ raw data**, không bắt đầu từ EDA.

---

Xem tiếp: [02_metrics.md](02_metrics.md) — cách tính từng chỉ số;
[03_modules.md](03_modules.md) — chi tiết từng module EDA.

