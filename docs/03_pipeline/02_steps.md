# Chi tiết từng bước Pipeline

Mỗi bước là một module trong `src/pipeline/` với hàm `run(context)`. `context` mà
mọi bước nhận và trả về:

| Khoá              | Nội dung                                                                                            |
| ----------------- | --------------------------------------------------------------------------------------------------- |
| `splits`          | dict `{"train": DataFrame, "val": ..., "test": ...}` - bước ĐỌC và bước SỬA đều dùng chính dict này     |
| `out_dir`         | thư mục báo cáo của phiên bản (nơi ghi CSV/JSON số liệu)                                            |
| `processed_dir`   | thư mục `data/processed/<mã>` (nơi ghi dữ liệu đã xử lý)                                            |
| `dataset`         | cấu hình dataset: `name`, `aspects`, `labels`, `text_column`, `drop_columns`, `splits`, `_raw_dir`... |
| `pipeline_config` | nội dung `configs/pipeline/v0.1.0.yaml` (đã bổ sung giá trị mặc định)                               |
| `version_id`      | mã phiên bản                                                                                        |
| `raw_texts`       | văn bản gốc của từng dòng (bước Load giữ lại để bước 6 đối chiếu)                                   |
| `raw_positions`   | vị trí gốc của những dòng được giữ (bước Clean ghi lại)                                             |

Bước nào **sửa dữ liệu** thì ghi thẳng vào `context["splits"]`; bước nào **chỉ đo**
(Validate, Final Validate) thì không sửa gì.

## 1. Step 1 - Load (`src/pipeline/load.py`)

Vào: cấu hình dataset + `data/raw/<tên>/<file>` cho từng split.
Làm: gọi loader theo `format` (CSV đọc bằng `utf-8-sig` để nuốt BOM), **bỏ** những
cột khai báo ở `drop_columns` (với cosmetics là `others`), đổi tên cột văn bản
(`text_column`) thành `text`.
Ra: `context["splits"]` = 3 DataFrame đã thống nhất schema `text` + các cột khía cạnh.

Điểm cần nhớ:

- thiếu cột khía cạnh nào thì loader **tự thêm cột rỗng** để chạy tiếp và ghi lại
  việc đó (bước 2 sẽ báo);
- văn bản gốc của từng dòng được giữ lại trong `context["raw_texts"]` - đây là mốc
  để bước 6 chứng minh văn bản không bị viết lại
  ([04_invariants.md mục 2](04_invariants.md)).

## 2. Step 2 - Validate (`src/pipeline/validate.py`)

Vào: `context["splits"]` sau khi Load.
Làm: kiểm tra **schema** (đủ cột, đúng tên, không thừa cột) và **nội dung** (review
rỗng, nhãn nằm ngoài danh sách hợp lệ).
Ra: `validation_report.csv` (từng lỗi) + bảng "Số lỗi theo loại" trên báo cáo.

Bước này **chỉ ghi nhận, không sửa** - mọi lỗi nằm trong `validation_report.csv`.
Bật/tắt bằng `steps.validate.check_schema` và `steps.validate.check_content`
([03_config.md mục 2](03_config.md)).

### Cách đọc bảng "Kiểm tra schema"

Hai cột "cột thiếu so với config" và "cột thừa so với config" được xét **so với khai
báo của dataset trong `configs/datasets/<name>/<version>.yaml`** - tức bộ cột mong đợi là
`text` + 7 cột khía cạnh (`dataset.expected_columns`), không phải so với file gốc:

- **thiếu** = config khai báo cột đó nhưng dữ liệu đã nạp không có -> loader đã tự
  thêm cột rỗng để chạy tiếp, và lỗi được ghi lại;
- **thừa** = dữ liệu đã nạp có cột mà config không khai báo -> thường là dấu hiệu
  file gốc đổi cấu trúc, cần xem lại `drop_columns`.

Vì là **so với config**, bảng này cũng là phép kiểm cho việc thêm dataset mới: nếu
khai báo sai `aspects`, bảng sẽ hiện ngay cột thiếu / thừa thay vì im lặng.

## 3. Step 3 - Clean (`src/pipeline/clean.py`)

Vào: `context["splits"]` sau Validate + các khoá `steps.clean.*` trong config.
Làm: **loại bỏ và cách ly bản ghi**, theo đúng thứ tự dưới đây (thứ tự quan trọng -
xem ghi chú ở cuối mục).
Ra: `context["splits"]` đã lọc; `removed_records.csv` (dòng bị loại, kèm lí do và
văn bản); `quarantine_records.csv` (dòng bị cách ly).

**Bước này loại gì và phát hiện thế nào?** Năm nhóm, theo thứ tự chạy:

| Nhóm              | Cách phát hiện                                                                                                                                                          | Khoá trong báo cáo                                                       |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| **rỗng**          | `text.strip() == ""`                                                                                                                                                    | `Loại do nhiễu`                                                          |
| **nhiễu**         | `utils.is_gibberish` (>=50% token "không giống từ") hoặc `utils.is_advertisement` (khớp `AD_PATTERNS`) hoặc `utils.is_code_like` (khớp `CODE_PATTERNS`, config đang BẬT) | `Loại do nhiễu` (cosmetics: 487 gibberish + 78 quảng cáo + 1 code = 566) |
| **trùng lặp**     | hai lượt: khoá = **văn bản nguyên văn** (chính xác), rồi khoá = `utils.dedup_key`                                                                                       | `Loại do trùng chính xác` / `Loại do trùng theo khoá so trùng`           |
| **rò rỉ dữ liệu** | khoá so trùng của dòng val/test đã có trong tập khoá của train                                                                                                          | `Loại do rò rỉ dữ liệu`                                                  |

Nhóm "rỗng + nhiễu" được gộp chung vào thẻ `Loại do nhiễu` và tách riêng trong biểu
đồ "Số dòng bị loại theo lý do" (`removed_records.csv` giữ nguyên văn bản từng dòng
bị loại để kiểm lại bằng tay).

Các hàm nhận diện ở đây là **cùng bộ hàm** mà EDA 03 dùng để đo
([02_eda/03_modules.md mục 3](../02_eda/03_modules.md)), nên định nghĩa "nhiễu" của hai
bên giống nhau; chỉ khác thời điểm đo.

> **Khoá so trùng khác bước Normalize.** Khoá so trùng bỏ dấu câu (và bỏ dấu tiếng Việt
> khi `ignore_diacritics: true` - config đang để `false`); nó **không bao giờ sửa văn
> bản**, chỉ dùng để _so_. Bước Normalize (Step 4) mới là bước sửa văn bản, và nó
> **không** bỏ dấu. Bảng "Thiết lập Clean đang áp dụng" trên báo cáo in rõ
> `deduplicate.ignore_diacritics` đang Bật hay Tắt. Chi tiết khoá này:
> [02_eda/02_metrics.md mục 5](../02_eda/02_metrics.md).

### Cách ly (quarantine) hoạt động thế nào

1. Bước xử lý trùng lặp gom các bản ghi có cùng khoá lại thành nhóm (lượt 1 dùng
   văn bản nguyên văn, lượt 2 dùng khoá so trùng).
2. Nếu trong nhóm **mọi bản ghi cùng bộ nhãn** -> đây là trùng lặp bình thường: giữ
   bản ghi đầu, bỏ phần còn lại (đếm vào "Loại do trùng ...").
3. Nếu trong nhóm có **nhãn khác nhau** -> pipeline không đủ căn cứ để chọn: với
   `quarantine`, **toàn bộ** bản ghi của nhóm bị đưa ra khỏi tập và ghi vào
   `quarantine_records.csv` kèm split, dòng gốc, lí do
   (`trùng lặp chính xác + xung đột nhãn`) và 200 ký tự văn bản.

Vì sao không tự chọn nhãn: chọn bừa một nhãn sẽ **tạo nhãn sai cho model học**; đưa
ra ngoài thì mất một ít dữ liệu nhưng không làm hỏng nhãn. Số dòng bị cách ly được
đếm riêng trên báo cáo ("Số dòng bị cách ly (xung đột nhãn)") và **không** nằm trong
`removed_records.csv` - chúng chưa phải "đã xử lý" mà đang chờ quyết định của con
người. Trên cosmetics: 43 dòng (tất cả ở train), tập trung vào vài văn bản bị lặp
nhiều lần với nhãn khác nhau - EDA 05 đã liệt kê đúng những ô nhãn xung đột này.

Giá trị khác của khoá này là `keep_first` (giữ bản ghi đầu tiên, bỏ phần còn lại);
chi tiết: [03_config.md mục 3](03_config.md).

### Xử lý rò rỉ dữ liệu (`steps.clean.leakage.remove_eval_overlap`)

EDA 05 phát hiện có review xuất hiện ở **cả train và val/test** (18 cặp trùng chính
xác giữa train ↔ val, 18 cặp giữa train ↔ test). Nếu để nguyên, điểm đánh giá model
sẽ **cao giả tạo** vì model đã thấy trước dữ liệu đó.

Cách xử lý: **giữ trong train, loại khỏi val/test**. Lý do:

- tập train cần dữ liệu để học, xoá đi sẽ mất thông tin;
- tập đánh giá phải "sạch" thì con số đo mới đáng tin.

Bật mặc định (`true`). Nếu muốn giữ nguyên dữ liệu gốc để đối chứng, đặt `false`.

**Vì sao con số rò rỉ ở pipeline nhỏ hơn con số của EDA:** Clean xoá nhiễu **trước**
rồi mới xử lý rò rỉ, nên những dòng đã bị loại vì nhiễu không còn xuất hiện trong
bước này (cosmetics: EDA đếm 91 dòng, pipeline loại 84 dòng). Chi tiết:
[02_eda/02_metrics.md mục 12](../02_eda/02_metrics.md).

## 4. Step 4 - Normalize (`src/pipeline/normalize.py`)

Vào: `context["splits"]` sau Clean + các khoá `steps.normalize.*`.
Làm: **sửa hình thức văn bản** bằng bốn phép dưới đây, theo đúng thứ tự này, phép nào
được bật thì chạy:
Ra: `context["splits"]` với cột `text` đã chuẩn hoá (chỉ cột `text` bị sửa - nhãn
không bị chạm, xem [04_invariants.md mục 1](04_invariants.md)); các file số liệu về mức
độ ảnh hưởng của từng phép.

**Bốn phép này thực sự làm gì?**

| Phép             | Việc làm                                                                                                                                                      | Ví dụ                                                   |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| `lowercase`      | chuyển mọi ký tự về chữ thường                                                                                                                                | `Son ĐẸP` -> `son đẹp`                                   |
| `unicode`        | đưa chữ về dạng dựng sẵn NFC - tiếng Việt có hai cách mã hoá cho cùng một chữ (tổ hợp dấu vs dựng sẵn), NFC để hai chuỗi "nhìn giống nhau" thật sự giống nhau | `e` + dấu sắc (tổ hợp) -> `é` (một ký tự)                |
| `whitespace`     | `\r\n` và `\r` -> `\n`; nhiều space/tab -> 1 space; bỏ space quanh xuống dòng; nhiều dòng trống -> 1; bỏ space ở hai đầu                                         | `"Son  đẹp\r\n\r\n\r\nHàng ok "` -> `"Son đẹp\nHàng ok"` |
| `repeated_chars` | rút gọn mọi dãy ký tự lặp còn `repeated_chars_max` ký tự                                                                                                      | `đẹpppppp` -> `đẹpp` (khi max = 2)                       |

`repeated_chars_max` **chỉ có tác dụng khi `repeated_chars: true`**, và nó là số ký
tự **giữ lại** (không phải số ký tự bị xoá): `max = 2` biến `đẹppppp` thành `đẹpp`,
`max = 3` thành `đẹppp`. Đặt `1` là mạnh nhất (mọi dãy lặp còn 1 ký tự).

> ⚠️ Bước này **KHÔNG bỏ dấu tiếng Việt** và **KHÔNG thay teencode**: văn bản giữ
> nguyên như người viết. Dự án cũng không bỏ dấu ở bất kỳ chỗ nào khác - khoá so trùng
> của bước Clean (`steps.clean.deduplicate.ignore_diacritics`) đang để `false`, và dù có bật
> thì khoá đó cũng chỉ dùng để _so_, không sửa văn bản.

**Phép nào ảnh hưởng tới bao nhiêu review?** Báo cáo vẽ biểu đồ "Số review bị thay
đổi bởi từng phép chuẩn hoá", mỗi cột là một split, mỗi chuỗi là một phép **đang
bật**. Con số này được đếm bằng cách áp từng phép theo thứ tự và ghi lại phép nào
thật sự làm văn bản đổi, nên khi bật/tắt một phép trong config, biểu đồ và bảng tự
thay đổi theo - không cần sửa code. Một review có thể bị **nhiều phép** cùng đổi,
nên tổng các cột của biểu đồ lớn hơn tổng số review bị thay đổi.

**Ví dụ trước / sau khi chuẩn hoá** không in lên báo cáo (bảng dài mà không dẫn tới
quyết định nào): các dòng thật đã bị chuẩn hoá nằm trong `normalize_samples.csv`, cùng
thư mục phiên bản mà báo cáo ghi ở dòng "Thư mục số liệu chi tiết" trên đầu. Trong file
đó, ký tự điều khiển được in cho nhìn thấy được:

- `⏎` là xuống dòng, `\r` là ký tự xuống dòng kiểu Windows (CRLF);
- `␣` là khoảng trắng, chỉ hiện ở những dòng mà **khác biệt duy nhất** là khoảng
  trắng - nếu để trống, hai ô sẽ trông giống hệt nhau;
- đoạn in ra là **đoạn quanh vị trí khác nhau đầu tiên** (không phải 80 ký tự đầu của
  review), nên cột "trước" và "sau" luôn cho thấy đúng chỗ bị sửa; `...` báo hiệu đoạn
  bị cắt hai đầu.

Bước Normalize **KHÔNG thay teencode**. Việc nhận diện teencode / từ lạ chỉ để **đo**
(EDA 03, mức token), không dùng để viết lại văn bản. Đầy đủ hơn:
[02_eda/02_metrics.md mục 8](../02_eda/02_metrics.md).

Nếu ai đó thêm một phép "bỏ dấu" hay "viết lại teencode" vào `normalize_steps`, hạng
mục "Văn bản chỉ đổi hình thức" ở Step 6 sẽ **báo LỖI ngay** - xem
[04_invariants.md mục 2](04_invariants.md).

## 5. Step 5 - Transform (`src/pipeline/transform.py`)

Vào: `context["splits"]` sau Normalize + khoá `steps.transform.format`.
Làm: chuyển nhãn chữ sang **mã số** và sinh hai dạng dữ liệu: bảng multi_head (để
huấn luyện và để Export ghi ra đĩa) và bản ghi ABSA (dạng dùng cho model sinh và để
đọc bằng mắt).
Ra: `context["splits"]` đã ở dạng multi_head + số liệu về số bản ghi ABSA.

Pipeline **chỉ xuất một dạng dữ liệu** (bảng multi_head). Dạng JSONL cho model sinh
(Qwen3 / ViTASA) được sinh khi cần, từ chính bảng đó:

```python
from src.preprocessing import loader

records = loader.to_absa_records("train")        # mẫu dạng {"text", "labels"}
loader.write_absa_records("train")               # ghi ra JSONL nếu cần file
```

**`multi_head` nghĩa là gì?** Mô hình được thiết kế để đoán **một lúc nhiều khía
cạnh** ("multi-head" = nhiều đầu ra, mỗi đầu ra phụ trách một khía cạnh). Vì vậy dữ
liệu phải ở dạng **một dòng = một review + một mã nhãn cho MỖI khía cạnh**:

```csv
text,stayingpower,texture,smell,price,colour,shipping,packing
"Son đẹp nhưng ship lâu",0,0,0,0,1,2,0
```

Mã `0` = khía cạnh đó **không được nhắc tới** (ô nhãn trống ở dữ liệu gốc), `1/2/3`
= `positive` / `negative` / `neutral`. Khi huấn luyện, model bỏ qua các ô `0` khi
tính loss, nên một dòng chỉ có 1 khía cạnh vẫn dùng được.

**Bản ghi ABSA** (dạng dùng cho model sinh và để đọc bằng mắt) chỉ giữ những khía
cạnh **thực sự được nhắc tới**:

```json
{
  "split": "train",
  "text": "Son đẹp nhưng ship lâu",
  "labels": { "colour": "positive", "shipping": "negative" }
}
```

**Vì sao số bản ghi ABSA nhỏ hơn số dòng?** Vì một phần dữ liệu **không có nhãn khía
cạnh nào** (mọi ô = `0`) - xem [02_eda/02_metrics.md mục 11](../02_eda/02_metrics.md).
Trên cosmetics: 15344 dòng -> **13213** bản ghi ABSA, tức 2131 dòng không sinh bản ghi
nào. Những dòng đó **vẫn được giữ** trong `processed_*.csv` (để bảng đủ số dòng và
truy vết được), chỉ không xuất hiện trong dạng ABSA.

Chi tiết định dạng đầu ra và ví dụ đầy đủ: [05_output.md](05_output.md).

## 6. Step 6 - Final Validate (`src/pipeline/final_validate.py`)

Vào: `context["splits"]` sau Transform + `context["raw_texts"]` (văn bản gốc bước 1
giữ lại) + vị trí gốc của các dòng được giữ + `normalize_steps` của lần chạy này.
Làm: đây là **cổng chất lượng** của lần chạy, kiểm tra:

| Hạng mục                      | Kiểm gì                                                                                                                            |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| Schema                        | đủ cột khía cạnh, đúng tên                                                                                                         |
| Văn bản                       | không có text rỗng                                                                                                                 |
| Nhãn                          | mọi mã nhãn nằm trong `0/1/2/3`                                                                                                    |
| Số dòng                       | số dòng đầu ra khớp với số dòng được giữ sau Clean                                                                                 |
| **Nhãn không bị đổi**         | dấu vân tay nhãn trước / sau chuẩn hoá phải trùng - [04_invariants.md mục 1](04_invariants.md)                                        |
| **Văn bản chỉ đổi hình thức** | từng dòng đầu ra phải khớp với dòng gốc sau khi áp lại `normalize_steps` (so từng ký tự) - [04_invariants.md mục 2](04_invariants.md) |

Ra: `final_validation.json` + bảng hạng mục **ĐẠT / LỖI** trên báo cáo. Kết quả hiện
tại của dataset cosmetics: tất cả ĐẠT, trong đó "Văn bản chỉ đổi hình thức" là
**15344/15344 dòng khớp** - tức không có dòng nào bị viết lại, không mất dấu tiếng Việt.

Bước này **không phân tích, không vẽ biểu đồ**: nó chỉ trả lời ĐẠT hay LỖI. Xem thêm
mục "Phân biệt ba loại kiểm tra" ở [01_flow.md mục 6](01_flow.md).

## 7. Step 7 - Export (`src/pipeline/export.py`)

Vào: `context["splits"]` cuối cùng + `label_map` + config đã dùng.
Làm: ghi dữ liệu đã xử lý và mọi thứ cần để truy vết về sau, rồi ghi phiên bản vào
mục lục.
Ra (trong `data/processed/<mã>/`): `train.csv`, `val.csv`, `test.csv`,
`label_map.json`, `processing_log.json`; và một dòng mới trong
`data/processed/manifest.json`.

`processing_log.json` **nằm cùng thư mục với dataset mà nó mô tả**, nên chép riêng
thư mục phiên bản đi đâu vẫn giữ đủ dấu vết về cấu hình đã tạo ra nó. Chi tiết từng
file: [05_output.md](05_output.md).

---

Xem tiếp: [03_config.md](03_config.md) - ý nghĩa từng khoá cấu hình;
[04_invariants.md](04_invariants.md) - ba bất biến và cách chứng minh;
[06_extend.md](06_extend.md) - thêm một bước mới.
