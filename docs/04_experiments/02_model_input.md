# Tiền xử lý cho model - chuẩn bị input cho từng model

> Đọc file này khi: đo độ dài input thật, hoặc chọn `max_length`.
> Liên quan: `docs/04_experiments/01_models.md`, `docs/05_config/04_models.md`

## 1. Khung mã nguồn (đã dựng sẵn)

```
configs/
+-- prompts/<tên>.txt        NỘI DUNG prompt (sửa được không cần đụng code)
+-- prompts/examples/<tên>.txt  khối ví dụ few-shot (tuỳ chọn, khi prompt dùng {examples})
\-- models/<model_id>.yaml   ngưỡng cắt input, cách nạp model (mặc định: qwen3-4b-instruct-2507.yaml)

src/
+-- prompts.py               nạp + KIỂM TRA file prompt (ô nhớ, dòng đánh dấu, sha)
+-- model_config.py          đọc configs/models/<model_id>.yaml
\-- preprocessing/
    +-- loader.py            ĐỌC dữ liệu đã xử lý (mọi model dùng chung)
    +-- phobert.py           tách từ + tokenizer
    +-- visobert.py          tokenizer (không tách từ)
    +-- qwen.py              prompt + chat template + tokenizer
    +-- vitasa.py            gác lại - xem [04_backlog.md](04_backlog.md) mục 1
    +-- token_stats.py       ĐO độ dài input thật (chạy: run_token_stats.py)
    \-- segmenters/          các BỘ TÁCH TỪ có thể thay thế cho nhau
        +-- base.py          hợp đồng của một bộ tách từ
        +-- vncorenlp.py     RDRSegmenter - bộ CHÍNH CHỦ của PhoBERT (cần Java)
        +-- pyvi.py          bộ legacy (dự phòng khi chưa cài được Java)
        +-- underthesea.py   bộ bên thứ ba (đối chứng)
        \-- none.py          không tách từ (baseline)
```

`loader.py` là cửa vào duy nhất: nó đọc bảng multi_head trong
`data/processed/<mã>/`, và sinh ra dạng dữ liệu mà từng model cần
(`to_multi_head_arrays` cho encoder, `to_absa_records` cho model sinh).
`project_multi_head` chiếu ma trận nhãn theo không gian nhãn của thí nghiệm và trả về `mask`,
nên ô bị loại (ví dụ ô neutral khi `neutral_policy: drop`) không được tính vào loss mà cũng
không làm mất các khía cạnh khác của cùng review.
Các file model còn lại **không tự đọc file CSV** - nhờ vậy đổi dataset hay đổi
phiên bản preprocessing không phải sửa code model.

Khi chạy, các file này **báo lỗi rõ ràng nếu thiếu thư viện / thiếu Java / thiếu model**,
chứ không âm thầm dùng một thứ khác.

## 2. Prompt nằm ở FILE, không nằm trong code

Câu chỉ dẫn gửi cho Qwen3 là một **biến thực nghiệm**: cùng một dữ liệu, đổi câu chỉ dẫn
là đổi kết quả. Vì vậy nội dung prompt nằm ở `configs/prompts/<tên>.txt`, còn thí nghiệm
nào dùng prompt nào do config của chính thí nghiệm quyết định (khoá `prompt`).

`configs/prompts/` là **thư viện prompt dùng chung**: file ở đây tái sử dụng được cho nhiều
model và nhiều thí nghiệm. Vì là thư viện dùng chung nên **tên file đặt theo NỘI DUNG của
prompt** (`absa_direct_v1`, `absa_cot_v1`, `absa_cot_1shot_v1`), không đặt theo model hay theo
thí nghiệm: model và phương pháp đã nằm trong đường dẫn `experiments/<model_id>/<method>/<expNNN>/`,
ghi thêm vào tên file là hai nguồn sự thật cho cùng một việc.

Prompt riêng của một thí nghiệm thì để ngay trong thư mục thí nghiệm (`prompt.txt`) và trỏ tới
bằng khoá `prompt`; dùng file trong thư viện chung cũng được. Cả hai đều là đường dẫn tính từ
thư mục thí nghiệm trước, rồi tới gốc repo.

```bash
python run_token_stats.py --list-prompts          # đang có prompt nào, sha nào
python run_token_stats.py --prompt absa_direct_v1    # đo một prompt khác mặc định
```

| Quyết định thiết kế | Vì sao |
|--------------------|--------|
| Prompt ở file `.txt`, không phải chuỗi trong Python | Sửa/so sánh (diff) như văn bản; giữ nguyên dấu ba nháy, xuống dòng, ngoặc nhọn |
| Tên prompt ở config của THÍ NGHIỆM (`experiments/<model_id>/<method>/<expNNN>/config.yaml`), **không** ở `configs/models/<model_id>.yaml` hay `configs/pipeline/<v>.yaml` | `pipeline.yaml` đi vào hash để sinh **mã phiên bản dữ liệu**, nên để prompt ở đó sẽ đẻ ra mã phiên bản mới vô nghĩa cho cùng một dataset. Còn config model là "model đọc dữ liệu thế nào", không phải "thí nghiệm hỏi thế nào" |
| File `.txt` không chứa siêu dữ liệu | Một nguồn sự thật cho "prompt nào đang dùng"; tên file + sha được in ra và ghi vào mục lục |
| Sai ô nhớ / thiếu `{text}` / dòng đánh dấu lạ -> **lỗi ngay khi nạp** | Chạy 15.000 review bằng một prompt sai là mất một buổi; thà dừng ở giây đầu |

Các ô nhớ được phép dùng: `{text}` (bắt buộc), `{aspects}`, `{label_guide}`,
`{example}`, `{examples}`. Prompt một lượt là mặc định; prompt nhiều lượt (few-shot) dùng
các dòng đánh dấu `[SYSTEM]`, `[USER]`, `[ASSISTANT]` - chi tiết ghi ở đầu
`src/prompts.py`. Bảng mã nhãn trong prompt (`{label_guide}`) **sinh từ
`label_map.json`** của đúng phiên bản dữ liệu, nên dataset khác bộ nhãn thì prompt đổi
theo.

### 2.1. Ví dụ few-shot là file RIÊNG (và là một biến thực nghiệm)

| Điều | Chi tiết |
|------|----------|
| File ở đâu | `configs/prompts/examples/<tên prompt>.txt` - **tên file phải trùng tên prompt**, vì đường dẫn được suy ra từ tên prompt |
| Bắt buộc không | Không. Prompt không dùng `{examples}` thì không cần file. Prompt dùng mà thiếu file -> **lỗi ngay khi nạp**, kèm đường dẫn đang mong đợi |
| Nội dung gửi cho model | Mỗi khối `--- Ví dụ n ---` gồm câu review, chuỗi suy luận và dòng `KẾT QUẢ:` với JSON **hợp lệ** (khoá thật, mã thật) |
| Chú thích nguồn gốc | File **được phép** mở đầu bằng các dòng `#` để ghi nguồn ví dụ (viết tay hay lấy từ split nào). Khối này bị **cắt trước khi chèn vào prompt** (xem `prompts._split_examples_note`), nên model không thấy, và sửa mỗi lời chú thích thì số token không đổi |
| `{example}` khác `{examples}` | `{example}` = MỘT object JSON mẫu sinh tự động theo danh sách khía cạnh; `{examples}` = khối ví dụ đọc từ file |
| **Số ví dụ đổi được mà KHÔNG sửa prompt** | Bỏ/thêm khối `--- Ví dụ n ---` trong file ví dụ là xong. Đây là biến thực nghiệm rẻ nhất của hướng LLM |
| Truy vết | `prompt_sha` **không đổi** khi đổi số ví dụ (nó chỉ tính nội dung file prompt), nên `prompts.examples_info()` trả thêm `examples_sha` + số ví dụ; tên file CSV có thêm `ex-<sha4>` **kể cả khi chạy bằng cấu hình dự án** - hai bộ ví dụ là hai thí nghiệm, không được ghi cùng một file |
| Kiểm tra nguồn | `python run_check_examples.py` - kiểm cấu trúc, kiểm khoá/mã JSON có khớp `label_map.json`, và **đối chiếu từng ví dụ với cả 3 split** (trùng nguyên câu, cụm trùng dài nhất) |

Quy ước dạy định dạng trong prompt CoT là **của dự án** (không phải chuẩn của Qwen):
khối `SUY LUẬN:` với các dòng `- <khía cạnh>: <trích dẫn> | <lí do ngắn> | mã <số>`, rồi
`KẾT QUẢ:` với một object JSON. Bản cũ của prompt CoT có phần mô tả schema viết dạng
`{"khía cạnh": mã, ...}` - **JSON không hợp lệ** và mâu thuẫn với chính các ví dụ ngay
trên nó (rủi ro model copy nguyên si dòng đó), nên đã thay bằng `{example}` (JSON hợp lệ,
sinh theo đúng bộ khía cạnh của phiên bản dữ liệu).

Ví dụ few-shot nằm TRONG prompt, tức là **model đã nhìn thấy nó**: ví dụ lấy từ dữ liệu
chỉ được lấy từ split **train**; lấy từ val/test là rò rỉ dữ liệu đánh giá. Hai ví dụ
hiện tại **do người viết dự án tự soạn**, đã kiểm bằng `run_check_examples.py`: không có
câu nào trùng val/test, cụm trùng dài nhất chỉ 3-4 từ (các cụm thông dụng như "cầm chắc
tay", "màu nhạt hơn").

## 3. Tách từ: chọn được, mặc định là bộ chính chủ

**Tách từ khác tokenizer.** Tách từ gộp các âm tiết của một từ lại ("Đại học Quốc gia" ->
"Đại_học Quốc_gia") và chạy TRƯỚC; tokenizer chẻ văn bản thành subword và chạy SAU.
Đổi bộ tách từ **không** làm đổi tokenizer - đó là điều kiện để đo được "tách từ giúp
bao nhiêu" thay vì chỉ trích dẫn khuyến nghị.

```bash
python run_token_stats.py --list-segmenters      # máy này cài được bộ nào
python run_token_stats.py --segmenter pyvi       # chỉ định đích danh một bộ
```

| Bộ | Chính chủ? | Vì sao có mặt |
|----|-----------|----------------|
| `vncorenlp` | **có** | RDRSegmenter - đúng bộ VinAI dùng để tiền huấn luyện PhoBERT. Mặc định của `auto` |
| `pyvi` | không | Dự phòng khi chưa cài được Java. `auto` chỉ dùng tới khi `vncorenlp` không chạy được |
| `underthesea` | không | Bộ bên thứ ba, để đối chứng |
| `none` | - | Tắt tách từ: baseline để đo tác động thật |

Nguyên tắc: `auto` **không bao giờ** tự chọn một bộ không chính chủ. Máy chưa cài được bộ
chính chủ thì phép đo báo lỗi kèm cách cài, chứ không lặng lẽ dùng bộ khác - số liệu đo
bằng bộ khác là số liệu của một thí nghiệm khác.

**Một chi tiết phải biết khi đọc lại output tách từ:** quy ước của VnCoreNLP là âm tiết
*đầu* một từ in ra sau một khoảng trắng, còn âm tiết *nối tiếp* in ra sau dấu `_` (nên
mới có "Đại_học"). Khi chạy trên MỘT câu riêng lẻ, từ đầu tiên đôi khi bị gán nhãn "nối
tiếp" dù không có từ nào trước nó, sinh ra output như `_Son` - đo trên 3.000 review
cosmetics thì 711 review (23,7%) mắc hiện tượng này. Dấu `_` đó không nối với từ nào nên
không mang thông tin gì, vì vậy `segmenters/vncorenlp.py` **bỏ nó** (hằng số
`STRIP_LEADING_BOUNDARY`, có ghi lại trong `info()` để truy vết). Dấu `_` do người viết
tự gõ (`^ _ ^`, "đẹp _ rẻ _ xịn") luôn đứng riêng một mình nên **không bị đụng tới**:
đã kiểm trên 3.000 review, không có review nào gõ `_` dính liền chữ.


## 4. Đo input THẬT của từng model (chạy trước khi huấn luyện)

EDA đếm TỪ (`utils.tokenize`) để khảo sát dữ liệu, còn model đọc **subword** của
tokenizer riêng. Cùng một review có thể thành 20 token với model này và 60 token với
model khác, nên độ dài thật phải đo bằng chính tokenizer của model - EDA không được
phụ thuộc vào model nào ([02_eda/02_metrics.md mục 9](../02_eda/02_metrics.md)).

```bash
python run_token_stats.py --dataset cosmetics
# -> data/reports/model_input/model_input.csv
```

Chỉ cần `transformers` (không cần torch), nên đo được trước khi huấn luyện. Model
nào chưa đo được sẽ bị bỏ qua kèm lí do, không ghi số liệu sai. Tên dataset sai thì
lệnh dừng ngay với gợi ý tên gần đúng (mã thoát `2`), giống các entrypoint khác.

Ngưỡng cắt `max_length` là một **khoá cấu hình**, không phải hằng số trong code: mỗi model
khai `preprocess.max_length` trong `configs/models/<model_id>.yaml`. Không chép lại con số
này ở chỗ nào khác, vì chép lại là có ngày lệch với lúc huấn luyện, và lệch ở đây thì mọi
kết luận "input có bị cắt hay không" đều sai.

Ngưỡng cắt `max_length` đọc theo thứ tự **trên xuống** - cả hai đường đi qua đúng một hàm
(`token_stats.effective_limit`), nên con số dùng để ĐO và con số dùng để CẮT khi huấn luyện
(`build_inputs` mặc định lấy cùng giá trị) không thể lệch nhau:

| # | Nguồn | Dùng khi nào | Đổi có làm bẩn version dữ liệu? |
|---|-------|--------------|--------------------------------|
| 1 | `--max-length 128` hoặc `--max-length qwen=1280` | thử nhanh một lần, không phải sửa file | không |
| 2 | `preprocess.max_length` trong `configs/models/<model_id>.yaml` | cấu hình của dự án | **không** - file này KHÔNG nằm trong hash sinh mã phiên bản dữ liệu |

Khi chạy, ngưỡng hiệu lực được in ra kèm **nguồn** và **trần của model**:

```
  max_length :
      phobert      256 token   nguồn: configs/models/phobert-base-v2.yaml   trần model: 258
      visobert     256 token   nguồn: configs/models/visobert.yaml          trần model: 514
      qwen        1280 token   nguồn: configs/models/qwen3-4b-instruct-2507.yaml   trần model: 262144
```

Ba chốt an toàn đi kèm:

1. **Không vượt trần kiến trúc** của model (PhoBERT 258, ViSoBERT 514, Qwen 262.144): vượt
   là bị chặn ngay, kèm gợi ý dùng `--max-length <model>=<số>`.
2. **Cờ dòng lệnh thì tên file có thêm `maxlen-<model>-<số>`** (ví dụ
   `token_stats__prompt-absa_cot_v1__maxlen-qwen-1024.csv`) -> chạy thử một giá trị
   khác không ghi đè lên số liệu của cấu hình chính. Ngược lại, sửa `preprocess.max_length`
   trong `configs/models/<model_id>.yaml` là đổi **cấu hình của dự án**, nên vẫn ghi vào file
   mặc định (`token_stats.csv`) - nếu không, chỉ đổi một dòng YAML là file mặc định biến mất,
   khó tra cứu. Giá trị hiệu lực thì **luôn** được ghi lại ở ba nơi: cột `max_length` trong
   CSV, dòng `max_length` ở banner, và khoá `limits` trong mục lục.
3. **Có review bị cắt thì in cảnh báo** nêu rõ model / split / tỉ lệ, thay vì để nó lặng lẽ
   nằm trong một ô của bảng số liệu.



| Model | Ngưỡng cắt đang dùng | Giới hạn thật | Nguồn của con số |
|-------|----------------------|---------------|------------------|
| PhoBERT | 256 | **258** vị trí (`max_position_embeddings`) | Bảng chính chủ của PhoBERT ghi "Max length 256"; 258 = 256 + 2 token đặc biệt |
| ViSoBERT | 256 | **514** vị trí | **Lựa chọn của dự án** (review dài nhất 229 token) - không phải "khớp model"; đặt bằng PhoBERT để hai encoder cùng ngân sách input |
| Qwen3-4B | **1280** | 262.144 vị trí (và `model_max_length` = 1.010.000) | **Lựa chọn của dự án**, ghi ở `configs/models/qwen3-4b-instruct-2507.yaml`: prompt CoT cần tới 1.106 token, nên 1024 làm cắt mất 4 mẫu train; 1280 cho 0% bị cắt ở mọi split |


| Cột | Nghĩa |
|-----|-------|
| `tokenizer` | lớp tokenizer thật đang dùng (ví dụ `PhobertTokenizer`) |
| `segmenter` | bộ tách từ đã dùng (`vncorenlp`, `pyvi`, `underthesea`, `none`) - cùng một review, đổi bộ này là đổi số token |
| `vocab` | kích thước từ vựng của tokenizer |
| `max_length` | ngưỡng cắt của model đó |
| `token/review TB`, `p50`, `p95`, `p99` | số token (subword) của một input, gồm cả token đặc biệt |
| `max` | input dài NHẤT trong split - đây mới là con số quyết định `max_length`: muốn **0% bị cắt** thì ngưỡng phải >= `max` của mọi split |
| `% review > max_length` | tỉ lệ input dài hơn `max_length` của model đó, tức **bị cắt mất phần đuôi** |
| `% token <unk>` | tỉ lệ token không có trong từ vựng của model. `-` nghĩa là **không tính được** (tokenizer không khai báo token `<unk>`), KHÁC với `0,00` |
| `subword / từ` | một "từ" bị chẻ thành bao nhiêu mảnh - càng cao thì input càng dài và tốn tính toán |


Số liệu đã đo cho dataset `cosmetics` (split `train`, phiên bản `cosmetics-ds0.1.0-pl0.1.0-srccosmetics@0.1.0-ab12cd34`,
bộ tách từ `vncorenlp`, prompt `absa_direct_v1`; bản đầy đủ cả 3 split nằm trong
`token_stats.csv`. Cấu hình có thể đã đổi, hãy chạy lại lệnh trên để lấy số của phiên
bản đang dùng):

| Model | max_length | token/review TB | p95 | p99 | % > max_length | % `<unk>` | subword / từ |
|-------|-----------|-----------------|-----|-----|----------------|-----------|--------------|
| PhoBERT | 256 | 29,96 | 62 | 87 | 0,02 | 3,88 | 1,38 |
| ViSoBERT | 256 | 43,45 | 89 | 125 | 0,00 | 0,11 | 2,02 |
| Qwen3-4B | 1024 | 229,50 | 268 | 298 | 0,00 | - | 10,68 |

Đọc bảng này:

- **ViSoBERT**: 95% review nằm trong 89 token nên `max_length = 256` không cắt mất gì.
- **PhoBERT**: ngắn nhất về số token vì tách từ gộp âm tiết lại (1,38 mảnh/từ), nhưng lại
  có `% <unk>` cao nhất - tokenizer của PhoBERT là BPE mức TỪ, gặp teencode/emoji là
  thành `<unk>`. Đây là số thật, không phải lỗi: nó cho thấy phần văn bản "lạ" của mạng
  xã hội bị model này nhìn thấy ít hơn hẳn so với ViSoBERT.
- **Qwen3-4B**: ~230 token là **cả prompt chỉ dẫn** (prompt dài hơn review), nhưng vẫn
  dưới 1024 nên chưa bị cắt. Cột `% <unk>` là `-` vì tokenizer của Qwen khai báo
  `unk_token = null`: model không có token `<unk>` nào, nên in `0,00` sẽ là nói sai
  (0% ngụ ý "có đo và bằng 0").
- **Tác động của việc tách từ** (cùng tokenizer, chỉ đổi bước tách từ): PhoBERT đạt
  29,96 token/review với bộ chính chủ và 33,67 khi không tách từ (`--segmenter none`) -
  tách từ làm input ngắn hơn ~12%, `% <unk>` cũng giảm (3,88% so với 5,28%).
- ViTASA chưa có số vì chưa có checkpoint để chạy: xem [04_backlog.md](04_backlog.md).

Khi `p95` tiến sát `max_length` hoặc cột `% review > max_length` khác 0 thì mới phải
tăng `max_length` (tốn tính toán hơn) hoặc chấp nhận cắt. Trên `cosmetics` hiện tại:
PhoBERT có 0,02% review train bị cắt (vài review), hai model kia không bị cắt mẩu nào.

### 4.1. So sánh các bộ tách từ - bằng số, không bằng trích dẫn

Cùng một tokenizer (PhoBERT), cùng một tập dữ liệu (train, 12.302 review), chỉ đổi bước
tách từ. Mỗi lần chạy ghi một file riêng nên so sánh luôn còn nguyên cả bốn bên:

```bash
python run_token_stats.py --dataset cosmetics --segmenter vncorenlp
python run_token_stats.py --dataset cosmetics --segmenter pyvi
python run_token_stats.py --dataset cosmetics --segmenter underthesea
python run_token_stats.py --dataset cosmetics --segmenter none
```

| Bộ tách từ | token/review TB | p50 | p95 | p99 | % > max_length | % `<unk>` | subword / từ |
|-----------|-----------------|-----|-----|-----|----------------|-----------|--------------|
| `vncorenlp` (chính chủ) | **29,96** | 25 | 62 | 87 | 0,02 | 3,88 | 1,38 |
| `pyvi` | 30,27 | 26 | 62 | 88 | 0,02 | 3,84 | 1,30 |
| `underthesea` | 31,78 | 27 | 66 | 91 | 0,02 | 3,65 | 1,27 |
| `none` (không tách từ) | 33,67 | 28 | 70 | 96 | 0,02 | 5,28 | 1,55 |

Đọc bảng này:

- Bộ **chính chủ cho input ngắn nhất** (29,96 so với 33,67 khi không tách từ, tức ngắn hơn
  **11,0%**) và **ít `<unk>` hơn hẳn**: theo tỉ lệ là 3,88% so với 5,28% (giảm 26,5% tương
  đối), theo số đếm là 14.302 so với 21.886 token `<unk>` trên toàn split train (giảm
  **34,7%**, tức khoảng một phần ba) - số đo này ủng hộ khuyến nghị của VinAI, thay vì chỉ
  trích dẫn lại.
- `pyvi` bám rất sát (+1,0%) nên là phương án dự phòng chấp nhận được khi máy chưa cài
  được Java - nhưng vẫn phải ghi rõ đã dùng bộ nào.
- `underthesea` có `subword / từ` thấp nhất (1,27) mà số token lại CAO hơn: nó gộp ít âm
  tiết hơn nên số "từ" nhiều hơn. Vì vậy **không đọc `subword / từ` một mình** để đoán độ
  dài input.
- ViSoBERT và Qwen giữ nguyên **từng con số** ở cả bốn file - đúng như thiết kế, chỉ
  PhoBERT nhận `--segmenter` (xem mục 3).

Còn thiếu: tác động của việc tách từ lên **kết quả cuối** (F1) - việc đó cần huấn luyện,
ghi ở [04_backlog.md](04_backlog.md).

### 4.2. Prompt: đo chi phí TRƯỚC khi chạy model (0 / 1 / 2 ví dụ)

Prompt cũng là một biến thực nghiệm, nên phải biết nó tốn bao nhiêu token trước khi đem đi
chạy. Số dưới đây là split `train` (12.302 review); bản đầy đủ cả 3 split nằm trong các file
của thư mục phiên bản:

| Prompt | ví dụ | file số liệu | token/review TB | p50 | p95 | p99 | max | % > 1280 |
|--------|-------|--------------|-----------------|-----|-----|-----|-----|----------|
| `absa_direct_v1` (một lượt) | 0 | `token_stats.csv` | 229,50 | 224 | 268 | 298 | 474 | 0,00 |
| `absa_cot_zeroshot_v1` | 0 | `...__prompt-absa_cot_zeroshot_v1.csv` | 376,50 | 371 | 415 | 445 | 621 | 0,00 |
| `absa_cot_1shot_v1` | 1 | `...__prompt-absa_cot_1shot_v1__ex-5d530f7c.csv` | 681,50 | 676 | 720 | 750 | 926 | 0,00 |
| `absa_cot_v1` | 2 | `...__prompt-absa_cot_v1__ex-c513f5a6.csv` | 950,50 | 945 | 989 | 1.019 | **1.195** | 0,00 |

Ba điều đọc ra từ bảng này:

1. **CoT đắt ở CẢ HAI đầu.** Input 950,50 token/review so với 229,50 của prompt một lượt
   (gấp 4,1 lần). Chưa hết: model còn phải SINH phần suy luận - theo định dạng trong file
   ví dụ là khoảng 210 token cho mỗi câu trả lời (xem `configs/prompts/examples/`). Cột
   trong bảng này chỉ nói phần INPUT.
2. **Mỗi ví dụ khoảng 287-305 token, và chi phí cộng thẳng:** 376,50 (0 ví dụ) -> 681,50 (1) ->
   950,50 (2). Đó là lí do "số ví dụ" là một biến thực nghiệm đáng thử: phương án 0 ví dụ rẻ
   hơn một nửa so với 2 ví dụ mà vẫn giữ phần suy luận.
3. Prompt CoT dài nhất cần **1.195 token** ở train (val 1.102, test 1.045) nên **ngưỡng
   1280 cho 0% bị cắt ở mọi split**. Ngưỡng 1024 cắt 0,67% train (82 mẫu), 0,59% val và
   0,53% test - và với prompt dạng chat, phần bị cắt là phần **CUỐI**, tức chính yêu cầu
   định dạng đầu ra. (Số liệu cũ hơn trong lịch sử - "4/12.302 mẫu, max 1.106" - tương ứng
   với bộ ví dụ CŨ; ví dụ hiện tại dài hơn, nên con số đã được đo lại toàn bộ.)

Vì vậy có hai lựa chọn ngưỡng cắt, **cả hai đều có số liệu** trong thư mục phiên bản:

| Ngưỡng cắt | File | Ảnh hưởng thật |
|-----------|------|----------------|
| 1280 (**đang dùng**, ghi ở `configs/models/qwen3-4b-instruct-2507.yaml`) | `token_stats__prompt-absa_cot_v1__ex-c513f5a6.csv` | 0 mẫu bị cắt ở **mọi** split |
| 1024 (phương án đã cân nhắc, giữ lại để đối chiếu) | `...__ex-c513f5a6__maxlen-qwen-1024.csv` (chạy bằng `--max-length qwen=1024`) | 82/12.302 mẫu **train** mất phần đuôi (0,67%); val 0,59%; test 0,53% |

**Quyết định:** dùng **1280** - số liệu ở cột `% review > max_length` khi đó bằng 0 ở mọi
split, và chi phí gần như bằng không (hai file có y hệt `token/review TB`, p95, p99).

Điểm cần hiểu đúng: **`max_length` không làm đổi phép đo** - nó quyết định **ai bị cắt khi
thật sự đưa input vào model**. Bằng chứng: hai file trên giống nhau mọi con số đo, chỉ khác
cột `max_length` và cột `% review > max_length`. Với prompt dạng chat, phần bị cắt là phần
CUỐI của hội thoại - mà trong prompt CoT này, phần cuối chính là yêu cầu định dạng đầu ra,
nên ở ngưỡng 1024, 4 mẫu đó còn mất luôn chỉ dẫn định dạng.





## 5. Cài đặt cho tiền xử lý cho model (cả nhóm dùng cùng một bản)

Ba việc, theo đúng thứ tự:

```bash
# 1) Thư viện Python của dự án (đã gồm transformers; torch để dành cho bước huấn luyện)
pip install -r requirements.txt

# 2) JAVA cho bộ tách từ chính chủ: JDK 17 LTS (Temurin) - KHÔNG cần quyền admin
powershell -ExecutionPolicy Bypass -File scripts\setup_java.ps1

# 3) Thư viện Python + model VnCoreNLP (jar + model tách từ)
powershell -ExecutionPolicy Bypass -File scripts\setup_vncorenlp.ps1
```

Vì sao cần Java, và vì sao phải là script chứ không phải "cài gì cũng được":

| Điều | Chi tiết |
|------|----------|
| Bộ tách từ chính chủ là chương trình **Java** | RDRSegmenter nằm trong `VnCoreNLP-1.2.jar`; `py-vncorenlp` gọi nó qua **pyjnius (JNI)**, không phải qua lệnh `java` |
| pyjnius tìm JVM qua biến môi trường | `JDK_HOME` rồi `JAVA_HOME`; không thấy thì báo `"Unable to find JAVA_HOME"` - một lỗi chung chung, dễ làm sập cả phép đo. Vì vậy dự án **kiểm tra Java trước** và báo lỗi kèm đúng lệnh cần chạy |
| Vì sao cài bằng ZIP thay vì `winget` | Cài vào `%USERPROFILE%\.jdks\temurin-17`: không cần quyền admin, gỡ ra chỉ cần xoá thư mục, và **mọi máy dùng cùng một dòng 17.0.x LTS** (script tải từ Adoptium API và kiểm SHA256) |
| Vì sao không dùng `py_vncorenlp.download_model()` | Hàm đó gọi `wget` qua `os.system`, mà Windows không có wget -> không tải được gì rồi báo lỗi khó hiểu. `scripts\setup_vncorenlp.ps1` tải bằng PowerShell và **kiểm kích thước từng file** |
| Phiên bản đang dùng | JDK: Temurin **17** (script in ra bản cụ thể khi cài; đã kiểm: 17.0.20.1). Model: `VnCoreNLP-1.2.jar` + `models/wordsegmenter/{vi-vocab, wordsegmenter.rdr}` trong `data/models/vncorenlp/` - thư mục này nằm trong `.gitignore`, cài lại bằng script chứ không commit |

Kiểm tra sau khi cài (không khởi động JVM nên rất nhanh):

```bash
python run_token_stats.py --list-segmenters
```

Dòng `vncorenlp` phải hiện `dùng được = có`. Máy nào chưa cài được Java mà vẫn muốn đo
PhoBERT ngay thì dùng `--segmenter pyvi` (cài `pip install pyvi`) - nhưng phải **ghi rõ**
đã dùng bộ nào, vì số liệu của hai bộ không so sánh ngang nhau được. Trên Windows, cửa sổ
terminal đang mở sẽ chưa thấy `JAVA_HOME` mới; dự án tự tìm JDK trong `.jdks` nên vẫn chạy
được ngay, không cần mở lại terminal.


## 6. Đưa dữ liệu vào model

Mọi model đọc **cùng một nguồn**: `data/processed/<mã>/`. Thư viện
`src/preprocessing/loader.py` tự tìm phiên bản mới nhất trên đĩa (thư mục mới nhất
trong `data/processed/`), hoặc bạn chỉ định rõ mã phiên bản:

```python
from src.preprocessing import loader

# Phiên bản mới nhất
texts, labels = loader.to_multi_head_arrays(loader.load_processed("train"))

# Một phiên bản cụ thể (để đối chiếu kết quả giữa các cấu hình)
texts_b, labels_b = loader.to_multi_head_arrays(
    loader.load_processed("train", version_id="cosmetics-ds0.1.0-pl0.1.0-srccosmetics@0.1.0-ab12cd34")
)

# Cho model sinh (Qwen3; ViTASA khi có checkpoint)
records = loader.to_absa_records("train")
```

Danh sách aspect cũng đọc từ `label_map.json` của chính phiên bản đó, nên khi đổi
dataset bạn không phải sửa code model:

```python
aspects = loader.known_aspects()
```

Điều này áp dụng cả cho **prompt**: prompt của Qwen mô tả bộ khía cạnh và bảng mã nhãn,
nên khi đo/huấn luyện phải truyền vào đúng phiên bản dữ liệu
(`qwen.values(text, aspects, label_map, ...)`). Dùng nhầm phiên bản là prompt mô tả sai
bài toán mà nhìn vào vẫn thấy hợp lí - `token_stats.run()` vì vậy đọc `label_map.json`
theo đúng `version_id` đang đo rồi truyền xuống model.

---

Xem tiếp: [03_training_eval.md](03_training_eval.md) - nhãn khi huấn luyện và chỉ số đánh
giá; [04_backlog.md](04_backlog.md) - những việc đã biết nhưng chưa làm.


