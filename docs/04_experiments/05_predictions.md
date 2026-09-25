# 05. Bảng dự đoán — đọc `predictions.csv` thế nào

> Đọc file này khi: mở `predictions.csv` của một lượt chạy và cần biết từng cột nói gì, hoặc cần tra
> "review này đã thành prompt nào rồi model trả lời ra sao".
> Liên quan: `docs/04_experiments/metrics.md`, `docs/04_experiments/03_training_eval.md`,
> `docs/00_workflow/01_flow.md`

## 1. File nằm ở đâu

`experiments/<model_id>/<method>/expNNN/results/<hash8>/predictions.csv`

- `<hash8>` là **mã băm danh tính** của lượt chạy: 8 ký tự đầu của `config_sha256`, tính từ
  - nội dung **cấu hình đã hợp nhất** (bài toán, prompt nào, split, `n`, cách sinh, lượng hoá,
    `max_length`, `batch_size`…),
  - nội dung **file prompt + file ví dụ + khối hệ thống**,
  - **mã phiên bản dữ liệu** và **commit đã ghim**,
  - `generation` và `max_length` hiệu lực của lượt chạy.
- Tên thư mục **cố ý không mô tả gì**: đường dẫn đã nói thí nghiệm nào, còn cấu hình đầy đủ nằm trong
  chính mã băm và trong `run_meta.json` (khối `run`). Nhờ vậy cùng một phép đo chạy trên **Colab và
  trên máy cá nhân ra CÙNG một thư mục** - copy từ Drive về repo là copy thẳng.
- Muốn đọc nhanh "thư mục này là gì": mở `run_meta.json` khối `run`, hoặc xem bảng
  `data/reports/experiment_registry/` (`python scripts/collect_reports.py`) - bảng có `hash`,
  `run` (= `<model>/<method>/<expNNN>:<hash8>`), `repo_sha`, `prompt`, `split`, `subset`, `decoding`,
  `quant`, `dtype`, `max_length`, `version_id`, và điểm số.

### 1.1. Khi nào chung thư mục, khi nào khác

| Thay đổi | Thư mục kết quả | Vì sao |
| --- | --- | --- |
| **Model khác** (`model_id` khác, ví dụ `phobert-base-v2`) | **Khác thư mục ở cấp trên**: `experiments/<model_id>/…` | `model_id` nằm trong đường dẫn thí nghiệm |
| **Commit đã ghim đổi** (kể cả chỉ sửa tài liệu) | **KHÁC** (`<hash8>` khác) | Bản code là một phần của phép đo: hai bản code là hai thí nghiệm, và kết quả cũ phải giữ nguyên |
| Nội dung prompt / bộ ví dụ few-shot / khối hệ thống đổi | **Khác** | Prompt gửi model đã đổi |
| Lượng hoá đổi (`4bit` ↔ không lượng hoá), `max_length`, `batch_size`, `max_new_tokens`, cách sinh, `seed`, `n`, `split` | **Khác** | Đổi đầu vào hoặc đầu ra của phép đo |
| Phiên bản dữ liệu khác | **Khác** | Chấm trên bộ dữ liệu khác |
| Máy chạy khác (Colab ↔ local), kiểu số (fp16/bf16), **nguồn trọng số** (id HF hay `data/models/…`) | **CÙNG thư mục** | Ba thứ này không nằm trong mã băm; `run_meta.json` ghi lại (`env.device`, `env.gpu`, `env.dtype`, `env.quantization`) để báo cáo nói rõ máy nào chạy |

Nói gọn: **cái gì đổi phép đo thì đổi thư mục; cái gì chỉ là bản code hay cái máy thì dùng lại chỗ
cũ** (…trừ commit: commit nằm trong mã băm, nên bản code khác là thư mục khác).

### 1.2. Chạy tiếp (RESUME) hay chạy mới

Một thư mục kết quả giữ được nhiều "attempt" (mỗi lần chạy ghi một mục vào `run_meta.json`). Quyết
định nằm ở MỘT chỗ (`src/resume.py`) và dựa trên **bộ ba**: `config_sha256`, mã phiên bản dữ liệu, và
commit đã ghim - cả ba đã nằm TRONG mã băm (tên thư mục), nên trong một thư mục thì mọi attempt luôn
khớp nhau.

| Trạng thái trong thư mục | Kết quả |
| --- | --- |
| Chưa có attempt nào | `NEW` |
| Attempt trước XONG | `STOP` - không chạy lại (muốn chạy lại: **xoá thư mục kết quả** rồi chạy lại) |
| Attempt trước bị ngắt | `RESUME` - chạy tiếp từ `predictions/part_*.jsonl`, điểm vẫn tính trên cả split |
| Thư mục có khối kết quả mà bản ghi không khớp | **DỪNG kèm lỗi**: thư mục bị trộn bằng tay, xoá rồi chạy lại |

Không còn `predictions/_bo-qua-*`: muốn một phép đo mới (khác bản code, khác cấu hình) thì cứ ghim
lại/chạy - mã băm khác nên ra **thư mục khác**, kết quả cũ không bị chuyển đi và không bị ghi đè.

**Kiểm trước và lượt chạy phải nói cùng một chuyện.** Cả hai gọi `experiment_run.run_identity()` -
hàm duy nhất tính mã băm, thư mục kết quả và bộ ba - nên trạng thái in ở ô kiểm trước đúng bằng trạng
thái ô chạy sẽ dùng. (Trước 25/09/2026 thì không: ô kiểm trước nhìn thư mục PHIÊN BẢN nên báo `NEW`
trong khi ô chạy báo `RESUME - chạy tiếp từ 16 mẫu đã xong`.)

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
| `tình trạng đọc` | Vì sao `có`/`KHÔNG`, hoặc lý do đọc được nhưng chưa trọn vẹn (xem bảng dưới) | Tìm nguyên nhân khi tỉ lệ đọc được thấp |
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

### 2.2. `tình trạng đọc` — các giá trị

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

1. `đọc được` + `tình trạng đọc` — nếu `KHÔNG` thì các cột sau không có ý nghĩa, đọc `câu trả lời` để biết
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

## 5. Bảng này tự chứa đủ để tính lại điểm

`nhãn đúng` và `nhãn đoán` nằm ngay trong file, nên đổi cách chấm thì **không phải chạy lại model**:
đọc `predictions.csv` rồi tính lại là ra số mới, vì cả nhãn đúng lẫn nhãn model trả lời đều đã có sẵn
trong ô (hai cột này để dạng JSON trong một ô CSV chính vì lý do đó). Từ 25/09/2026 **không còn công cụ
dòng lệnh riêng** cho việc này (`run_rescore_eval.py` đã bỏ cùng đường chạy ngoài thí nghiệm): muốn
điểm theo cách chấm mới thì chạy lại thí nghiệm - hoặc tự tính trên file, dữ liệu đã đủ.
