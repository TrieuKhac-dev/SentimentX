# 05. Bảng dự đoán — đọc `predictions.csv` thế nào

> Đọc file này khi: mở `predictions.csv` của một lượt chạy và cần biết từng cột nói gì, hoặc cần tra
> "review này đã thành prompt nào rồi model trả lời ra sao".
> Liên quan: `docs/04_experiments/metrics.md`, `docs/04_experiments/03_training_eval.md`,
> `docs/00_workflow/01_flow.md`

## 1. File nằm ở đâu

`experiments/<model_id>/<method>/expNNN/results/<mã dữ liệu>/<hậu tố>/predictions.csv`

- `<hậu tố>` ghi rõ cấu hình của lượt chạy: `prompt-<tên prompt>__<split>__n<số>__greedy[__<model>]`.
  Ví dụ `prompt-absa_cot_v1__val__n200__greedy` = prompt `absa_cot_v1`, chấm trên `val`, 200 mẫu,
  sinh greedy. Phần `__<model>` chỉ xuất hiện khi lượt chạy dùng model KHÁC `checkpoint` trong config
  (ví dụ trọng số có sẵn trên đĩa của máy cá nhân).
- Đây là file **nặng**: mỗi dòng mang cả prompt đã gửi và câu trả lời nguyên văn, nên `.gitignore`
  chặn nó khỏi git. Muốn đưa cho người khác thì gửi kèm, đừng commit.
- Mỗi DÒNG = một **ô** (một review × không phải một khía cạnh): mỗi dòng là một review với cả 7 khía
  cạnh nằm trong hai cột `nhãn đúng` (JSON) và `nhãn đoán` (JSON).

## 2. Ý nghĩa từng cột

| Cột | Nghĩa | Dùng để làm gì |
| --- | --- | --- |
| `chỉ số` | Số thứ tự của review trong file dữ liệu của split | Tra ngược về đúng review; cũng là khoá để chạy tiếp đúng mẫu đã xong |
| `split` | Tập đang chạy (`val`, `test`, `train`) | Chống nhầm: cùng prompt nhưng chấm trên tập khác là hai thí nghiệm |
| `prompt` | **TÊN** prompt trong thư viện (`absa_cot_v1`), không phải nội dung | Biết dùng cấu hình nào; nội dung + sha nằm ở `run_meta.json` |
| `kiểu đọc` | Bộ đọc lấy nhãn bằng ĐƯỜNG NÀO (xem bảng dưới) | `khối KẾT QUẢ` là đường chính; kiểu khác là đường lui, cần biết để đánh giá chất lượng định dạng |
| `đọc được` | `có` / `KHÔNG` — bộ đọc có lấy được bộ nhãn hợp lệ | Đọc được thì mới chấm; tỉ lệ này là chỉ số sức khoẻ của prompt |
| `lí do` | Vì sao `có`/`KHÔNG`, hoặc lý do đọc được nhưng chưa trọn vẹn (xem bảng dưới) | Tìm nguyên nhân khi tỉ lệ đọc được thấp |
| `text` | Review gốc tiếng Việt, nguyên văn | Đối chiếu câu trả lời với dữ liệu thật; kiểm "trích dẫn có đúng nguyên văn" |
| `nhãn đúng` | Đáp án thật, JSON `{khía cạnh: mã}` | So với `nhãn đoán` để biết đúng/sai từng khía cạnh |
| `nhãn đoán` | Model đoán, cùng dạng JSON; rỗng nếu `đọc được = KHÔNG` | Là thứ được chấm; rỗng được tính là sai cả hai ô (xem `metrics.md`) |
| `token sinh` | Số token model sinh ra cho review này | Chi phí đầu ra thật (khác số token của prompt) |
| `giây` | Thời gian sinh bình quân mỗi mẫu trong lô chứa nó | Ước lượng thời gian cho lượt sau |
| `có suy luận` | Câu trả lời có khối `SUY LUẬN:` (CoT) không | Kiểm prompt CoT có thật sự tạo suy luận |
| `có <think>` | Model có sinh token suy nghĩ nội bộ `<think>` không | Bản Qwen3-4B-Instruct-2507 là non-thinking nên luôn `không`; cột vẫn ĐẾM thay vì giả định |
| **`prompt gửi model`** | **Chuỗi ĐÚNG đã gửi cho model** — sau chat template và sau khi cắt ở `max_length` | Chỉ có ở đường chạy LLM. Đây là cột trả lời "mẫu này thành prompt nào" mà không cần chạy lại |
| `câu trả lời` | Nguyên văn model sinh (cả phần suy luận lẫn JSON) | Đối chiếu định dạng với yêu cầu trong prompt; tìm lỗi suy luận |

Hai cột `prompt gửi model` và `câu trả lời` nằm cạnh nhau, nên đọc một dòng là thấy liền mạch:
**câu hỏi → câu trả lời → nhãn đọc được**.

**Mỗi bản ghi nằm gọn trên MỘT dòng vật lý.** Ô có ký tự xuống dòng thật (prompt, câu trả lời) được
ghi thành hai ký tự `\n` khi ra CSV (`src/utils.py`, hàm `write_csv`). Chuẩn CSV cho phép ô nhiều
dòng, nhưng trình xem nào coi "một dòng = một bản ghi" (Notepad, VSCode, công cụ tự viết) sẽ thấy
dòng dừng ở giữa và tưởng các cột phía sau biến mất. Văn bản nhiều dòng nguyên gốc vẫn còn trong
`predictions/part_*.jsonl` và trong `câu trả lời` của `mispredictions.csv`.

**Model encoder (PhoBERT, ViSoBERT) KHÔNG có cột `prompt gửi model`.** Chúng học trực tiếp từ chuỗi
thô chứ không đọc prompt nào, nên bảng của chúng giữ nguyên 14 cột — thêm một cột rỗng vào đó là nói
sai về dữ liệu. Chi tiết kỹ thuật: `src/evaluation/records.py` (`columns(with_prompt=...)`).

### 2.1. `kiểu đọc` — các giá trị

| Giá trị | Nghĩa |
| --- | --- |
| `khối KẾT QUẢ` | Tìm thấy dấu `KẾT QUẢ:` và đọc object JSON sau dấu đó — ĐƯỜNG CHÍNH của prompt CoT |
| `đường lui: object JSON cuối cùng` | Không thấy dấu `KẾT QUẢ:`, nên bộ đọc lấy object JSON cân bằng CUỐI CÙNG trong cả câu trả lời. Đọc được nhưng là đường lui: nếu tỉ lệ này cao thì prompt chưa dạy được định dạng |
| `không đọc được` | Chưa xác định được đường đọc (câu trả lời rỗng, hoặc không có JSON nào) |

Bộ đọc nhận cả vài biến thể gõ thiếu dấu (`KẾT QUA:`, `KET QUA:`, `KẾT QUẢ :`) vì model hay mắc khi
trả lời nhanh — chi tiết ở `src/evaluation/parse.py`.

### 2.2. `lí do` — các giá trị

| Giá trị | Nghĩa |
| --- | --- |
| `ok` | Đọc được, mã đều hợp lệ, và **đủ cả 7 khía cạnh** — không có gì để lưu ý. Vì thế cột này "toàn ok" ở một lượt chạy tốt; nó chỉ có ích khi có dòng KHÁC `ok` |
| `ok (thiếu texture, price)` | Đọc được nhưng JSON thiếu khía cạnh nào đó; ô thiếu bị tính là SAI (không được điền 0 hộ) |
| `không thấy khối kết quả` | Có dấu mở khối nhưng phần sau không có object JSON nào |
| `không thấy JSON nào` | Cả câu trả lời không có object JSON cân bằng nào |
| `JSON không hợp lệ (...)` | Object tìm thấy nhưng `json.loads` lỗi (kèm thông báo của Python) |
| `kết quả không phải object JSON` | JSON đọc được nhưng không phải object (ví dụ một mảng hoặc một chuỗi) |
| `khoá không khớp bộ khía cạnh` | Object không có khoá nào trùng bộ khía cạnh của dataset |
| `mã nhãn không hợp lệ` | Khoá đúng nhưng mã nằm ngoài bảng mã của không gian nhãn (ví dụ trả `3` khi bài toán là `binary`) |
| `câu trả lời rỗng` | Model trả về chuỗi rỗng |

## 3. Đọc một dòng theo thứ tự nào

1. `đọc được` + `lí do` — nếu `KHÔNG` thì các cột sau không có ý nghĩa, đọc `câu trả lời` để biết
   model trả về cái gì.
2. `nhãn đúng` và `nhãn đoán` — khác nhau ở khía cạnh nào? (`0` = không nhắc tới, `1` = positive,
   `2` = negative, `3` = neutral; mã lấy từ `label_map.json` của phiên bản dữ liệu.)
3. `câu trả lời` — suy luận có đúng không, có trích nguyên văn không, có mã nào ngoài bảng không.
4. `prompt gửi model` — nhìn lại câu hỏi mà model thật sự nhận. Nghi ngờ "code làm prompt sai ý" thì
   đây là chỗ đối chiếu, không phải file `.txt` trong `configs/prompts/`.
5. `token sinh` + `giây` — chi phí của mẫu đó.

## 4. Khi nào mở `predictions.csv`, khi nào dùng công cụ

| Việc | Dùng gì |
| --- | --- |
| Xem MỘT mẫu: prompt trông thế nào, vào model ra sao | `python scripts/show_prompt.py <model>/<method>/<expNNN>` |
| Xem mẫu nào thành prompt nào và model trả lời gì, cả lượt chạy | `predictions.csv` (cột `prompt gửi model`, `câu trả lời`) |
| Biết điểm số | `metrics.json` (số chính) → `metrics.csv` (bảng dài để so) |
| Biết đã chạy những gì, tốn bao lâu | `run.log` |
| Biết máy/config/dữ liệu của lượt chạy | `run_meta.json` |
| Chỉ xem các ô đoán sai | `mispredictions.csv` |

## 5. Bảng này tự chứa đủ để chấm lại

`nhãn đúng` và `nhãn đoán` nằm ngay trong file, nên đổi cách chấm thì **không phải chạy lại model**:
`python run_rescore_eval.py` chấm lại từ chính `predictions.csv` (xem `docs/04_experiments/metrics.md`).
Đó cũng là lý do hai cột nhãn là JSON trong một ô CSV thay vì tách thành 7 cột.
