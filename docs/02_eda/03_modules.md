# Chi tiết từng module EDA

Mỗi module trong `src/eda/` là một **mục báo cáo**: nhận cùng một `context` từ
`run_eda.py` và trả về một dict mô tả mục đó. Thứ tự dưới đây **đúng bằng** thứ tự
trên báo cáo (`src/registry.py::EDA_MODULES`).

`context` mà mọi module nhận được:

| Khoá              | Nội dung                                                                                            |
| ----------------- | --------------------------------------------------------------------------------------------------- |
| `splits`          | dict `{"train": DataFrame, "val": ..., "test": ...}` - dữ liệu gốc đã đọc                               |
| `full`            | DataFrame của file gộp (`full_data.csv`), có thể `None`                                             |
| `out_dir`         | thư mục phiên bản, nơi module ghi CSV/JSON của mình                                                 |
| `dataset`         | cấu hình dataset: `name`, `aspects`, `labels`, `text_column`, `drop_columns`, `splits`, `_raw_dir`... |
| `version_id`      | mã phiên bản (dùng cho phần đầu báo cáo)                                                            |
| `missing_columns` | cột khía cạnh khai báo trong config nhưng thiếu ở file gốc (EDA 01 dùng)                            |

## 1. EDA 01 - Tổng quan (`src/eda/overview.py`)

Đo: cấu trúc từng FILE GỐC (tên file, số dòng, số cột, cột khía cạnh nào thiếu), ô
trống từng cột (ghi ra CSV), độ dài review theo số ký tự và số từ (cả 3 split) kèm
p50 / p95 / p99 (ghi ra CSV - p50/p95/p99 không in thành bảng, vì biểu đồ phân bố ngay
dưới đã cho thấy hình dạng độ dài, và bảng đó lặp lại gần hết con số trong biểu đồ).

Ghi ra: `01_overview.json` + `01_*.csv` trong thư mục phiên bản.

Bảng "Cấu trúc các file dữ liệu" nằm **ngay dưới phần thẻ số liệu, trước biểu đồ**
để trả lời câu hỏi đầu tiên của người đọc: báo cáo này nói về file nào. Vì vậy số
dòng mỗi file chỉ xuất hiện một lần (ở bảng), không vẽ thêm biểu đồ cột.

Giúp trả lời: dữ liệu có lớn không? Mỗi con số đến từ file nào? Review dài hay ngắn?
Cách đọc p50/p95/p99: [02_metrics.md mục 1](02_metrics.md).

## 2. EDA 02 - Nhãn và khía cạnh (`src/eda/label_aspect.py`)

Đo: mỗi khía cạnh có bao nhiêu `positive` / `negative` / `neutral` / ô trống; tỉ lệ
khía cạnh được nhắc tới; một review nhắc bao nhiêu khía cạnh; số dòng không có nhãn
khía cạnh nào; **ma trận xuất hiện cùng nhau** giữa các khía cạnh; và có nhãn nào
nằm ngoài danh sách hợp lệ không.

Ghi ra: `02_label_aspect.json` + `02_*.csv`.

Phân bố nhãn theo khía cạnh là một biểu đồ cột xếp chồng 100% chia thành **3 khung,
mỗi split một khung** (`charts._stacked_grid`): nhìn trong một khung thì biết khía
cạnh nào nghiêng về nhãn gì, nhìn ngang thì so được cùng một khía cạnh giữa ba
split. Trước đây ba split bị nhồi vào một biểu đồ với nhãn dạng "khía cạnh, split",
người đọc phải tự tách lại nên rất khó xem.

Nhóm "không có nhãn khía cạnh nào" được nêu bằng **một thẻ số liệu riêng** và bị
loại khỏi biểu đồ "số khía cạnh được nhắc trong một review" (biểu đồ này lấy mẫu số
là số review có nhãn) - xem [02_metrics.md mục 11](02_metrics.md). Ma trận xuất hiện
cùng nhau tính trên toàn bộ dữ liệu và chỉ có một hình thức trình bày (bản đồ nhiệt).
Bảng "nhãn không hợp lệ" chỉ xuất hiện khi thật sự có nhãn sai.

Giúp trả lời: dữ liệu có mất cân bằng không? Khía cạnh nào hiếm? Nhãn nào sai? Bao
nhiêu dòng không dùng được cho ABSA?

## 3. EDA 03 - Chất lượng và nhiễu (`src/eda/quality_noise.py`)

Đo: review rỗng, trùng chính xác, trùng **theo khoá so trùng**, ứng viên
**gibberish**, emoji, review chỉ có emoji / dấu câu, ký tự lặp, teencode / từ lạ
(mức TOKEN), dấu hiệu quảng cáo và **dấu hiệu code / HTML**. Kèm **ví dụ minh hoạ**
cho từng nhóm ([02_metrics.md mục 3](02_metrics.md)) và **quy mô từng quy tắc gắn cờ**
teencode ([02_metrics.md mục 8](02_metrics.md)).

Ghi ra: `03_quality_noise.json`, `03_*.csv`, trong đó có
`03_quality_teencode_common_flagged.csv` (300 từ phổ biến nhất bị gắn cờ - phép tự
kiểm dương tính giả).

Khoá so trùng được đọc từ `steps.clean.deduplicate.ignore_diacritics` trong
`configs/pipeline/v0.1.0.yaml`, nên khi đổi quy tắc so trùng thì số liệu EDA đổi theo
đúng như pipeline ([02_metrics.md mục 5](02_metrics.md)). Cách phát hiện từng nhóm nhiễu:
[02_metrics.md](02_metrics.md) mục 4 (gibberish), mục 5 (khoá so trùng), mục 6 (ký tự lặp), mục 7
(quảng cáo và code), mục 8 (teencode). Không còn nhóm "có dấu hiệu nhận xu" - đã bỏ
khỏi dự án.

Bộ hàm nhận diện dùng ở đây (`utils.is_gibberish`, `utils.is_advertisement`,
`utils.is_code_like`) cũng chính là bộ hàm mà bước Clean của pipeline gọi lại, nên
con số EDA và số dòng bị loại ở pipeline cùng một định nghĩa - chỉ khác thời điểm đo:
EDA đo trên dữ liệu gốc, pipeline loại sau khi đã xoá nhiễu trước đó
([03_pipeline/02_steps.md mục 3](../03_pipeline/02_steps.md)).

Giúp trả lời: cần xử lý những nhóm nhiễu nào? Mỗi nhóm chiếm bao nhiêu?

## 4. EDA 04 - Đặc điểm văn bản (`src/eda/text_analysis.py`)

Đo: các **từ hay gặp** và **cụm 2 từ đặc trưng theo từng khía cạnh** trên toàn bộ dữ
liệu (3 split); tỉ lệ review viết có dấu / không dấu theo split; kích thước từ vựng
(ghi ra CSV và hai thẻ số liệu).

Ghi ra: `04_text_analysis.json` + `04_*.csv`.

Cách đếm từng chỉ số ở [02_metrics.md](02_metrics.md) mục 9 (từ vựng, số từ / review) và
mục 10 (cụm 2 từ). Hai điểm đã sửa cho dễ đọc:

- biểu đồ từ hay gặp **không tính các từ quá phổ biến** (`và`, `là`, `của`...) - điều
  này được ghi ngay trong tiêu đề biểu đồ;
- biểu đồ có dấu / không dấu là **một cột xếp chồng cho mỗi split**, trên mỗi phần
  hiện **cả số review và tỉ lệ %**: nhãn nhóm ngắn nên không phải xoay nhãn trục, và
  tỉ lệ vẫn so được giữa train (12981 dòng) với val/test (1623 dòng).

Giúp trả lời: mỗi khía cạnh có "từ khoá" riêng nào? Dữ liệu có nhiều văn bản không
dấu (cần chuẩn hoá) không?

## 5. EDA 05 - Quan hệ giữa các split (`src/eda/split_leakage.py`)

Đo: trùng lặp giữa train và val và test (chính xác và theo khoá so trùng) và **xung
đột nhãn** (cùng một review nhưng nhãn khác nhau).

Ghi ra: `05_split_leakage.json`, `05_split_duplicates.csv`,
`05_split_duplicate_totals.csv`.

Mục này có **hai cách đếm trùng lặp khác nhau** và cả hai đều được nêu rõ trên báo
cáo: biểu đồ theo cặp split (đơn vị: văn bản) và hai thẻ số liệu "số dòng val/test
trùng train" (đơn vị: dòng) - chính là con số dẫn tới policy chống rò rỉ dữ liệu
([02_metrics.md mục 12](02_metrics.md)). Xung đột nhãn có hai mức đếm là review và ô nhãn
([02_metrics.md mục 13](02_metrics.md)); danh sách xung đột trên báo cáo là **đầy đủ,
không cắt bớt**.

Giúp trả lời: có **rò rỉ dữ liệu** (leakage) không? Tức là dữ liệu của tập test lại
nằm trong tập train - điều này làm kết quả đánh giá model bị "đẹp giả tạo".

---

Xem tiếp: [04_report_rules.md](04_report_rules.md) - quy ước trình bày báo cáo;
[05_extend.md](05_extend.md) - thêm một mục EDA mới.
