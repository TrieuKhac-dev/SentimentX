# Tiền xử lý cho model - chuẩn bị input cho từng model

> Đọc file này khi: đo độ dài input thật, hoặc chọn `max_length`.
> Liên quan: `docs/04_experiments/01_models.md`, `docs/05_config/04_models.md`

## 1. Khung mã nguồn (đã dựng sẵn)

```
configs/
+-- prompts/<tên>.txt        NỘI DUNG prompt (sửa được không cần đụng code)
+-- prompts/examples/<tên>.txt  khối ví dụ few-shot (tuỳ chọn, khi prompt dùng {examples})
\-- models/<model_id>.yaml   ngưỡng cắt input, cách nạp model (mỗi model một file, tên trùng `model_id`)

src/
+-- experiments/             nạp + KIỂM TRA prompt, đọc config model, chạy thí nghiệm
|   +-- prompts.py           nạp + KIỂM TRA file prompt (ô nhớ, dòng đánh dấu, sha)
|   \-- model_config.py      đọc configs/models/<model_id>.yaml
\-- preprocessing/
    +-- loader.py            ĐỌC dữ liệu đã xử lý (mọi model dùng chung)
    +-- bert_like.py         khuôn chung cho encoder kiểu BERT (khai ba hằng số rồi gọi sang)
    +-- phobert.py           tách từ + tokenizer
    +-- phobert_large.py     PhoBERT bản LỚN (cùng kho tiền huấn luyện + bộ tách từ, khác số tham số)
    +-- visobert.py          tokenizer (không tách từ)
    +-- vibert.py            encoder FPT (kho tiền huấn luyện khác, vẫn tách từ)
    +-- cafebert.py          XLM-R tiền huấn luyện tiếp bằng tiếng Việt (SentencePiece)
    +-- xlmroberta.py        đối chứng nguồn tiền huấn luyện (đa ngữ, SentencePiece)
    +-- qwen.py              prompt + chat template + tokenizer
    +-- vitasa.py            gác lại - xem [04_backlog.md](04_backlog.md) mục 1
    +-- token_stats.py       ĐO độ dài input thật (chạy: run_token_stats.py --hash <hash8> --prompt <tên>)
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

Prompt gửi cho Qwen3 là một **biến thực nghiệm**: cùng một dữ liệu, đổi prompt
là đổi kết quả. Vì vậy nội dung prompt nằm ở `configs/prompts/<tên>.txt`, còn thí nghiệm
nào dùng prompt nào do config của chính thí nghiệm quyết định (khoá `prompt`).

`configs/prompts/` là **thư viện prompt dùng chung**: file ở đây tái sử dụng được cho nhiều
model và nhiều thí nghiệm. Vì là thư viện dùng chung nên **tên file đặt theo NỘI DUNG của
prompt** (`absa_one_turn_v1`, `absa_cot_v1`, `absa_cot_5shot_v1`), không đặt theo model hay theo
thí nghiệm: model và phương pháp đã nằm trong đường dẫn `experiments/<model_id>/<method>/<expNNN>/`,
ghi thêm vào tên file là hai nguồn sự thật cho cùng một việc.

Prompt riêng của một thí nghiệm thì để ngay trong thư mục thí nghiệm (`prompt.txt`) và trỏ tới
bằng khoá `prompt`; dùng file trong thư viện chung cũng được. Cả hai đều là đường dẫn tính từ
thư mục thí nghiệm trước, rồi tới gốc repo.

```bash
python run_token_stats.py --list-prompts          # đang có prompt nào, sha nào (không cần --hash)
python run_token_stats.py --hash e616c1e3 --prompt absa_direct_v1    # prompt một lượt, KHÔNG dùng system prompt
python run_token_stats.py --hash e616c1e3 --prompt absa_cot_5shot_v1 --system absa_cot   # dùng {system_prompt}
```

Prompt nào dùng ô nhớ `{system_prompt}` thì **phải** truyền `--system <tên|đường dẫn>`: khối hệ thống
cũng tốn token, nên đo mà bỏ nó là đo một phép đo khác. Tên file sinh ra có thêm `sys-<tên>` để hai lần
đo khác khối hệ thống không ghi đè nhau.

| Quyết định thiết kế | Vì sao |
|--------------------|--------|
| Prompt ở file `.txt`, không phải chuỗi trong Python | Sửa/so sánh (diff) như văn bản; giữ nguyên dấu ba nháy, xuống dòng, ngoặc nhọn |
| Tên prompt ở config của THÍ NGHIỆM (`experiments/<model_id>/<method>/<expNNN>/config.yaml`), **không** ở `configs/models/<model_id>.yaml` hay `configs/pipeline/<v>.yaml` | `pipeline.yaml` đi vào hash để sinh **mã phiên bản dữ liệu**, nên để prompt ở đó sẽ đẻ ra mã phiên bản mới vô nghĩa cho cùng một dataset. Còn config model là "model đọc dữ liệu thế nào", không phải "thí nghiệm hỏi thế nào" |
| File `.txt` không chứa siêu dữ liệu | Một nguồn sự thật cho "prompt nào đang dùng"; tên file + sha được in ra và ghi vào mục lục |
| Sai ô nhớ / thiếu `{text}` / dòng đánh dấu lạ -> **lỗi ngay khi nạp** | Chạy 15.000 review bằng một prompt sai là mất một buổi; thà dừng ở giây đầu |

Các ô nhớ được phép dùng: `{text}` (bắt buộc), `{aspects}`, `{label_guide}`,
`{example}`, `{examples}`. Prompt một lượt là mặc định; prompt nhiều lượt (few-shot) dùng
các dòng đánh dấu `[SYSTEM]`, `[USER]`, `[ASSISTANT]` - chi tiết ghi ở đầu
`src/experiments/prompts.py`. Bảng mã nhãn trong prompt (`{label_guide}`) **sinh từ
`label_map.json`** của đúng phiên bản dữ liệu, nên dataset khác bộ nhãn thì prompt đổi
theo, **và bị lọc theo `label_space` + `neutral_policy`** của thí nghiệm: bài toán
`binary` + `drop` thì bảng mã chỉ còn `0/1/2` (lỗi đã sửa 25/09/2026: trước đó bảng mã vẫn
dạy `3 = neutral` vì chỉ lọc một chiều, tức dạy model một mã mà không gian nhãn không có).
`{example}` là KHUÔN JSON đủ khoá theo bộ khía cạnh, mã toàn số 0 - nên prompt nói rõ đó là
khuôn để điền, không phải đáp án.

### 2.1. Ví dụ few-shot là file RIÊNG (và là một biến thực nghiệm)

| Điều | Chi tiết |
|------|----------|
| File ở đâu | `configs/prompts/examples/<tên prompt>.txt` - **tên file phải trùng tên prompt**, vì đường dẫn được suy ra từ tên prompt |
| Bắt buộc không | Không. Prompt không dùng `{examples}` thì không cần file. Prompt dùng mà thiếu file -> **lỗi ngay khi nạp**, kèm đường dẫn đang mong đợi |
| Nội dung gửi cho model | Mỗi khối `--- Ví dụ n ---` gồm câu review, chuỗi suy luận và dòng `KẾT QUẢ:` với JSON **hợp lệ** (khoá thật, mã thật) |
| Chú thích nguồn gốc | File **được phép** mở đầu bằng các dòng `#` để ghi nguồn ví dụ (viết tay hay lấy từ split nào). Khối này bị **cắt trước khi chèn vào prompt** (xem `prompts._split_examples_note`), nên model không thấy, và sửa mỗi lời chú thích thì số token không đổi |
| `{example}` khác `{examples}` | `{example}` = MỘT object JSON mẫu sinh tự động theo danh sách khía cạnh; `{examples}` = khối ví dụ đọc từ file |
| **Số ví dụ đổi được mà KHÔNG sửa prompt** | Bỏ/thêm khối `--- Ví dụ n ---` trong file ví dụ là xong. Đây là biến thực nghiệm rẻ nhất của hướng LLM |
| Truy vết | `prompt_sha` **không đổi** khi đổi số ví dụ (nó chỉ tính nội dung file prompt), nên `prompts.examples_info()` trả thêm `examples_sha` + số ví dụ; tên file CSV có thêm `ex-<sha8>` **kể cả khi chạy bằng cấu hình dự án** - hai bộ ví dụ là hai thí nghiệm, không được ghi cùng một file |
| Kiểm tra nguồn | `python run_check_examples.py --hash <hash8>` - kiểm cấu trúc, kiểm khoá/mã JSON có khớp `label_map.json`, và **đối chiếu từng ví dụ với cả 3 split** (trùng nguyên câu, cụm trùng dài nhất) |

Quy ước dạy định dạng trong prompt CoT là **của dự án** (không phải chuẩn của Qwen):
khối `SUY LUẬN:` với các dòng `- <khía cạnh>: <trích dẫn> | <lí do ngắn> | mã <số>`, rồi
`KẾT QUẢ:` với một object JSON. Bản cũ của prompt CoT có phần mô tả schema viết dạng
`{"khía cạnh": mã, ...}` - **JSON không hợp lệ** và mâu thuẫn với chính các ví dụ ngay
trên nó (rủi ro model copy nguyên si dòng đó), nên đã thay bằng `{example}` (JSON hợp lệ,
sinh theo đúng bộ khía cạnh của phiên bản dữ liệu).

Ví dụ few-shot nằm TRONG prompt, tức là **model đã nhìn thấy nó**: ví dụ lấy từ dữ liệu
chỉ được lấy từ split **train**; lấy từ val/test là rò rỉ dữ liệu đánh giá. Hai ví dụ
hiện tại **do người viết dự án tự soạn**, đã kiểm bằng `run_check_examples.py --hash <hash8>`: không có
câu nào trùng val/test, cụm trùng dài nhất chỉ 3-4 từ (các cụm thông dụng như "cầm chắc
tay", "màu nhạt hơn").

### 2.2. Bộ ví dụ là BẤT BIẾN: đổi nội dung thì tạo CẶP MỚI

Tên bảng số đo có `ex-<sha8>` = băm **NỘI DUNG** file ví dụ (không phải tên file), nên sửa một chữ
trong file ví dụ là tên bảng đổi. Sửa **tại chỗ** để lại một bảng **mồ côi**: không lệnh nào tái lập
được nó nữa (nội dung cũ không còn), mà `scripts/collect_reports.py` **vẫn quét** mọi
`token_stats*.csv` trong `model_input/` (kể cả thư mục con) rồi tính nó vào `model_input.csv` như một
phép đo hợp lệ.

**LUẬT:** `configs/prompts/<tên>.txt` + `configs/prompts/examples/<tên>.txt` (+
`configs/prompts/system/<tên>.txt`) là **MỘT CẶP có phiên bản**, **bất biến khi đã dùng**. Đổi nội
dung thì tạo **cặp mới** (`absa_cot_5shot_v2.txt` + `examples/absa_cot_5shot_v2.txt`) rồi trỏ
config/prompt sang tên mới - cùng luật đã áp cho file phiên bản dataset/pipeline (luật 9 và 21 của
`docs/00_workflow/02_rules.md`).

Ba lớp chặn bảng mồ côi:

| Lớp | Ở đâu | Làm gì |
| --- | ----- | ------ |
| Cảnh báo lúc chạy | `run_token_stats.py` (qua `prompts.orphan_tables`) | Trước khi ghi, quét bảng đã có của phiên bản: bảng nào lệch `ex-`/`sys-` thì **in cảnh báo** - KHÔNG tự xoá, không tự dời |
| Kiểm tĩnh của CI | `src/workflow/checks.py`, kiểm 8 | Cây có bảng mồ côi là **CI đỏ**, kèm câu giải thích ([03_ci.md](../00_workflow/03_ci.md)) |
| Kho lịch sử | `data/reports/_archive/<mã>/` | Chỗ CHUYỂN bảng cũ ra: nằm NGOÀI `model_input/` nên bảng gộp không quét tới; nội dung không vào git |

**GIỚI HẠN ĐÃ BIẾT:** `sys-<tên>` chỉ ghi **TÊN** khối hệ thống, không ghi băm nội dung, nên đổi
NỘI DUNG file hệ thống mà giữ nguyên tên file thì tên bảng không đổi và bảng cũ bị **ghi đè** (mất số
cũ) - phép kiểm không thấy ca đó. Cùng họ: `seg-<tên>` chỉ ghi tên bộ tách từ, không ghi phiên bản
gói. Cả hai nằm ở [04_backlog.md](04_backlog.md).

## 3. Tách từ: chọn được, mặc định là bộ chính chủ

**Tách từ khác tokenizer.** Tách từ gộp các âm tiết của một từ lại ("Đại học Quốc gia" ->
"Đại_học Quốc_gia") và chạy TRƯỚC; tokenizer chẻ văn bản thành subword và chạy SAU.
Đổi bộ tách từ **không** làm đổi tokenizer - đó là điều kiện để đo được "tách từ giúp
bao nhiêu" thay vì chỉ trích dẫn khuyến nghị.

```bash
python run_token_stats.py --list-segmenters                    # máy này cài được bộ nào (không cần --hash)
python run_token_stats.py --hash e616c1e3 --segmenter pyvi     # chỉ định đích danh một bộ
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
python run_token_stats.py --hash e616c1e3 --prompt absa_cot_v1
# -> data/reports/model_input/<mã phiên bản>/token_stats*.csv
```

Tên file lấy từ mẫu trong `configs/paths.yaml`; chạy với tham số khác mặc định thì có thêm đuôi
(`token_stats__<tag>.csv`) nên không ghi đè số liệu cũ. Bảng tổng hợp `model_input` gom cả hai mẫu
tên đó, nên số đo luôn vào được báo cáo; chưa đo thì bảng rỗng và báo cáo nói rõ là rỗng (thư mục
`shards/` dành cho các bảng số đo tách nhỏ).

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
| 1 | `--max-length 128` hoặc `--max-length qwen3-4b-instruct-2507=1280` | thử nhanh một lần, không phải sửa file | không |
| 2 | `preprocess.max_length` trong `configs/models/<model_id>.yaml` | cấu hình của dự án | **không** - file này KHÔNG nằm trong hash sinh mã phiên bản dữ liệu |

Khi chạy, ngưỡng hiệu lực được in ra kèm **nguồn** và **trần của model**:

```
  max_length :
      phobert-base-v2               256 token   nguồn: configs/models/phobert-base-v2.yaml   trần model: 258
      visobert                      256 token   nguồn: configs/models/visobert.yaml   trần model: 514
      qwen3-4b-instruct-2507       2304 token   nguồn: configs/models/qwen3-4b-instruct-2507.yaml   trần model: 262144
```

Tên model trong bảng này là **tên file cấu hình** (`configs/models/<model_id>.yaml`) - cũng chính là giá
trị ở cột `model` của bảng số liệu, và là thứ `--max-length` nhận. Khối in trên **rút gọn còn ba dòng**;
danh sách đầy đủ hiện có **9 model** (xem `MODELS` của `src/preprocessing/token_stats.py`). Dòng cho `qwen3-0.6b` cũng có mặt vì
0.6B là model thử nghiệm chính thức (xem [01_models.md](01_models.md)); số liệu của nó **giống hệt** bản
4B vì dùng cùng tokenizer và cùng ngưỡng cắt - đó là điều đúng cần ghi lại, không phải lỗi trùng lặp.

*Ghi chú về số dòng:* mỗi lần đo hiện ra **9 model × 3 split = 27 dòng** (mỗi model một dòng cho `train`,
`val`, `test`). Bảng gộp `data/reports/model_input/model_input.csv` vì thế có **513 dòng**:
**19 tệp** `token_stats__*.csv` (8 tổ hợp prompt × ví dụ × bộ tách từ cho MỖI phiên bản dữ liệu
`…-e0ccc484` và `…-e616c1e3`, cộng 3 tệp của ba prompt một-ví-dụ mới `absa_cot_1shot_v2/v3/v4` - ba prompt
này chỉ đo ở phiên bản đang dùng) × 27 dòng. Tám tệp của bộ cũ từng chỉ có 9 dòng vì đo trước khi
Qwen3-0.6B vào thử nghiệm (đã chạy lại ngày 30/09/2026), và 19 tệp từng chỉ có 12 dòng cho tới khi thêm 5
model mới (đã chạy lại **04/10/2026**). Muốn kiểm lại: `python scripts/collect_reports.py --group
model_input` in ra số dòng của bảng gộp, và mỗi tệp phải có **27 dòng**.

**Năm model mới (04/10/2026)** đã vào `MODELS` của `src/preprocessing/token_stats.py`:
`qwen2.5-0.5b-instruct` (bản 0,5B khác họ model), `phobert-large` (encoder lớn hơn, cùng bộ tách từ),
`vibert-base-cased` (kho tiền huấn luyện khác), `cafebert` và `xlm-roberta-base` (hai model họ XLM-R; đo
để tách ảnh hưởng của *kho tiền huấn luyện* khỏi *bộ tách từ*). `max_length` của chúng: 256 token cho bốn
encoder (trần kiến trúc 512/514/514) và 2304 cho `qwen2.5-0.5b-instruct`.

Hai điều đọc ra từ 19 bảng đo ngày 04/10/2026 (đều là kết quả **đúng**, không phải lỗi chạy):

1. **`cafebert` và `xlm-roberta-base` ra số y hệt nhau** ở cả 15 cột, ở mọi bảng. Nguyên nhân: cùng bộ tách
   từ `XLMRobertaTokenizer` và cùng kho từ vựng 250.002 - khác nhau ở **trọng số tiền huấn luyện**, mà
   bảng này chỉ đo **độ dài input**. Đoạn mã không bị lỗi nhân bản: đó là đúng như dự đoán, và là bằng
   chứng cho thấy khác biệt giữa hai model này (nếu có) đến từ trọng số chứ không từ cách tách từ.
2. **`qwen3-0.6b` nhiều hơn `qwen3-4b-instruct-2507` đúng 4 token mỗi review, ở mọi split** (ví dụ prompt
   zero-shot: 376,51 so với 372,51 token/review). Nguyên nhân: cấu hình model của 0.6B khai
   `preprocess.enable_thinking: false`, và khuôn chat của Qwen3 khi **tắt** suy nghĩ chèn một khối
   ` thinking…<｜end▁of▁thinking｜>` **rỗng** - đúng **4 token** khi đếm bằng tokenizer cục bộ (10 token khi bật/không
   truyền, 14 token khi tắt). Đây là **bằng chứng cửa đã đi tới khuôn chat**, đúng thứ lượt 0.6B cần: lượt
   cũ bật suy nghĩ chỉ đọc được 3,33 / 1,36 / 1,73%. Khuôn của `qwen3-4b-instruct-2507` **không có** công
   tắc này (10 token với cả ba cách gọi), nên lượt 4B không đổi.

Ba chốt an toàn đi kèm:

1. **Không vượt trần kiến trúc** của model (PhoBERT 258, ViSoBERT 514, Qwen 262.144): vượt
   là bị chặn ngay, kèm gợi ý dùng `--max-length <model_id>=<số>`.
2. **Cờ dòng lệnh thì tên file có thêm `maxlen-<model_id>-<số>`** (ví dụ
   `token_stats__prompt-absa_cot_v1__maxlen-qwen3-4b-instruct-2507-1024.csv`) -> chạy thử một giá trị
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
| Qwen3-4B | **2304** | 262.144 vị trí (và `model_max_length` = 1.010.000) | **Lựa chọn của dự án**, ghi ở `configs/models/qwen3-4b-instruct-2507.yaml`: mức 5 ví dụ cần tới 2.122 token, nên 1280 cắt 100% và 1024 cắt 0,67% train; **2304 cho 0% bị cắt ở mọi split** |


| Cột | Nghĩa |
|-----|-------|
| `tokenizer` | lớp tokenizer thật đang dùng (ví dụ `PhobertTokenizer`) |
| `segmenter` | bộ tách từ đã dùng (`vncorenlp`, `pyvi`, `underthesea`, `none`) - cùng một review, đổi bộ này là đổi số token |
| `vocab` | kích thước từ vựng của tokenizer |
| `max_length` | ngưỡng cắt của model đó |
| `token/review TB`, `p50`, `p95`, `p99` | số token (subword) của một input, gồm cả token đặc biệt |
| `max` | input dài NHẤT trong split - đây mới là con số quyết định `max_length`: muốn **0% bị cắt** thì ngưỡng phải >= `max` của mọi split |
| `% review > max_length` | tỉ lệ input dài hơn `max_length` của model đó, tức **bị cắt mất phần đuôi** |
| `số token <unk>` | **số lượng** token không có trong từ vựng (cột đếm). Cần riêng cột đếm vì `% token <unk>` làm tròn nên không suy ngược ra số lượng được - muốn nói "tách từ giảm bao nhiêu token `<unk>`" thì phải có số đếm |
| `% token <unk>` | tỉ lệ token không có trong từ vựng của model. `-` nghĩa là **không tính được** (tokenizer không khai báo token `<unk>`), KHÁC với `0,00` |
| `subword / từ` | một "từ" bị chẻ thành bao nhiêu mảnh - càng cao thì input càng dài và tốn tính toán |


Số liệu đã đo cho dataset `cosmetics` (split `train`, phiên bản `cosmetics-ds0.1.0-pl0.1.0-srccosmetics@0.1.0-…`,
bộ tách từ `vncorenlp`, prompt `absa_direct_v1`; bản đầy đủ cả 3 split nằm ở file có tag của lượt đo —
`token_stats__prompt-absa_direct_v1__seg-<bộ tách từ>.csv`, vì `--prompt` là bắt buộc nên tên file luôn
có ít nhất tag `prompt-<tên>`. Cấu hình có thể đã đổi, hãy chạy lại lệnh trên để lấy số của phiên
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
- **Qwen3-4B**: ~230 token là **cả prompt** (prompt dài hơn review), nhưng vẫn
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
python run_token_stats.py --hash e616c1e3 --segmenter vncorenlp
python run_token_stats.py --hash e616c1e3 --segmenter pyvi
python run_token_stats.py --hash e616c1e3 --segmenter underthesea
python run_token_stats.py --hash e616c1e3 --segmenter none
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

#### 4.1.1. Cơ chế: mỗi ca cụ thể đổi bao nhiêu đơn vị (đo lại được)

Bảng trên cho biết tách từ được bao nhiêu trên CẢ split; dưới đây là cơ chế ở mức một ca, để đọc một
con số bất thường là biết đường tra. Cách đo (chạy được trên máy có Java, không cần GPU):

```bash
python -c "from src.preprocessing import phobert; t=phobert.tokenizer(); [print(repr(x), \
  t.convert_ids_to_tokens(phobert.encode([x], segmenter='vncorenlp')[0]), \
  t.convert_ids_to_tokens(phobert.encode([x], segmenter='none')[0])) for x in ('Công_dụng','Công dụng','dụng:')]"
```

| Văn bản vào | `vncorenlp` | không tách từ | Đọc ra |
| --- | --- | --- | --- |
| `Công dụng` (dấu cách) | **1** đơn vị (`Công_dụng`) | **2** mảnh (`Công`, `dụng`) | đúng ca mà tách từ sinh ra để xử lý: một TỪ tiếng Việt thành một đơn vị |
| `Công_dụng` (gạch dưới, dạng dữ liệu gốc) | **3** đơn vị (`Công`, `_`, `dụng`) | 1 mảnh (`Công_dụng`) | **dấu `_` là một đơn vị riêng** với bộ tách từ chính chủ |
| `dụng:` | **2** đơn vị (`dụng`, `:`) | **3** mảnh (`dụ@@`, `ng@@`, `:`) | âm tiết không có trong từ vựng bị chẻ thành nhiều mảnh con khi KHÔNG tách từ |

Hai điều đọc ra từ bảng này:

- Tách từ giúp ở **cả hai đầu**: gộp âm tiết thành từ (ít đơn vị hơn) và **tránh chẻ subword** ở những
  âm tiết hiếm - đó là nguồn của chênh lệch 21.886 so với 14.302 token `<unk>` ở bảng trên.
- Dữ liệu gốc nối âm tiết của từ khoá khía cạnh bằng `_` (`Công_dụng`), nhưng bộ tách từ chính chủ coi
  `_` là một đơn vị riêng: đưa nguyên dạng đó vào thì **đắt hơn** (3 đơn vị thay vì 1). Đây là ghi nhận
  để lần sau làm lại dữ liệu gốc thì viết `Công dụng`, **không** phải việc sửa bây giờ: đổi văn bản là
  đổi phiên bản dữ liệu và mọi kết quả đã chạy.

Số liệu của ba lần đo ở bảng trên nằm trong gói kết quả, mỗi bộ tách từ một file (đuôi `seg-<tên>` nên
không ghi đè nhau):

```
data/reports/model_input/<mã phiên bản>/token_stats__prompt-absa_direct_v1__seg-vncorenlp.csv
data/reports/model_input/<mã phiên bản>/token_stats__prompt-absa_direct_v1__seg-pyvi.csv
data/reports/model_input/<mã phiên bản>/token_stats__prompt-absa_direct_v1__seg-none.csv
```

Số đếm `<unk>` trong bảng trên nay đọc thẳng từ **cột `số token <unk>`** của ba file đó (mục 4), không
phải viết script riêng như lần đo đầu tiên.

### 4.2. Prompt: đo chi phí TRƯỚC khi chạy model (0 / 1 / 2 / 5 ví dụ)

Prompt cũng là một biến thực nghiệm, nên phải biết nó tốn bao nhiêu token trước khi đem đi
chạy. Số dưới đây là split `train` (12.302 review); bản đầy đủ cả 3 split nằm trong các file
của thư mục phiên bản:

| Prompt | ví dụ | file số liệu | token/review TB | p50 | p95 | p99 | max | % > ngưỡng |
|--------|-------|--------------|-----------------|-----|-----|-----|-----|----------|
| `absa_one_turn_v1` (một lượt, bản CHÍNH THỨC) | 0 | `...__prompt-absa_one_turn_v1__sys-absa_one_turn.csv` | 257,50 | 252 | 296 | 326 | 502 | 0,00 |
| `absa_direct_v1` (một lượt, bản cũ - không tách system prompt) | 0 | `...__prompt-absa_direct_v1__seg-vncorenlp.csv` | 229,50 | 224 | 268 | 298 | 474 | 0,00 |
| `absa_cot_zeroshot_v1` | 0 | `...__prompt-absa_cot_zeroshot_v1__sys-absa_cot.csv` | 372,50 | 367 | 411 | 441 | 617 | 0,00 |
| `absa_cot_1shot_v1` | 1 | `...__prompt-absa_cot_1shot_v1__ex-5d530f7c__sys-absa_cot.csv` | 721,50 | 716 | 760 | 790 | 966 | 0,00 |
| `absa_cot_v1` | 2 | `...__prompt-absa_cot_v1__ex-c513f5a6__sys-absa_cot.csv` | 990,50 | 985 | 1.029 | 1.059 | **1.235** | 0,00 |
| `absa_cot_5shot_v1` | 5 | `...__prompt-absa_cot_5shot_v1__ex-1e7c1be3__sys-absa_cot.csv` | 1.877,50 | 1.872 | 1.916 | 1.946 | **2.122** | 0,00 |

Cột cuối tính theo ngưỡng cắt của **từng lần đo**. Từ 27/09/2026 mọi dòng được đo lại ở ngưỡng hiện
tại (**2304**) và khối hệ thống đã tách thành file riêng - nên tên file có thêm `sys-...`; các tệp đo
cũ (không `sys-`, bốn dòng đo ở ngưỡng 1280) vẫn nằm trong thư mục để đối chiếu. Các cột `TB`, `p50`,
`p95`, `p99`, `max` là **độ dài input**, không phụ thuộc ngưỡng, nên giá trị không đổi giữa hai lần đo.

Ba điều đọc ra từ bảng này:

1. **CoT đắt ở CẢ HAI đầu.** Input 990,50 token/review so với 257,50 của prompt một lượt
   (gấp 3,8 lần). Chưa hết: model còn phải SINH phần suy luận - theo định dạng trong file
   ví dụ là khoảng 210 token cho mỗi câu trả lời (xem `configs/prompts/examples/`). Cột
   trong bảng này chỉ nói phần INPUT.
2. **Mỗi ví dụ khoảng 287-305 token, và chi phí cộng thẳng:** 372,50 (0 ví dụ) -> 721,50 (1) ->
   990,50 (2). Đó là lí do "số ví dụ" là một biến thực nghiệm đáng thử: phương án 0 ví dụ rẻ
   hơn một nửa so với 2 ví dụ mà vẫn giữ phần suy luận.
3. Prompt CoT dài nhất cần **2.122 token** ở train (bản 5 ví dụ; val 2.016, test 1.959) nên ngưỡng
   1280 cắt MẤT PHẦN ĐUÔI của **100% review ở cả ba split** khi chạy mức 5 ví dụ - với prompt dạng
   chat, phần bị cắt chính là yêu cầu định dạng đầu ra, nên mẫu đó mất luôn yêu cầu định dạng. Ngưỡng
   **2304** giữ 0% bị cắt cho cả bản 2 ví dụ lẫn bản 5 ví dụ. (Bản 2 ví dụ cần 1.235 token ở train
   nên ở ngưỡng 1280 vẫn 0% bị cắt - con số đó vẫn đúng cho bản 2 ví dụ.)

Vì vậy có hai lựa chọn ngưỡng cắt, **cả hai đều có số liệu** trong thư mục phiên bản:

| Ngưỡng cắt | Số liệu trong repo | Ảnh hưởng thật |
|-----------|------|----------------|
| 2304 (**đang dùng**, ghi ở `configs/models/qwen3-4b-instruct-2507.yaml`) | mọi file `token_stats__*.csv` của phiên bản, ví dụ `token_stats__prompt-absa_cot_5shot_v1__ex-2799b4c8.csv` | 0 mẫu bị cắt ở **mọi** split, cho cả bản 2 ví dụ lẫn bản 5 ví dụ |
| 1280 (ngưỡng cho tới 25/09/2026) | **không còn trong repo**: các file đã được đo lại ở ngưỡng 2304 | bản 2 ví dụ: 0 mẫu bị cắt; bản **5 ví dụ: 100% review ở cả ba split** mất phần đuôi - tức mất yêu cầu định dạng |
| 1024 (phương án đã cân nhắc, không giữ số liệu) | chạy lại bằng `--max-length qwen3-4b-instruct-2507=1024` nếu cần đối chiếu | 82/12.302 mẫu **train** mất phần đuôi (0,67%); val 0,59%; test 0,53% |

**Quyết định:** dùng **2304** - mức 5 ví dụ (mức mà công bố so) chỉ chạy được ở đây với 0% bị cắt, và
nâng ngưỡng **không làm đổi phép đo**: cột `% review > max_length` bằng 0 ở ngưỡng 2304, còn các
cột độ dài input y hệt nhau giữa hai ngưỡng.

Điểm cần hiểu đúng: **`max_length` không làm đổi phép đo** - nó quyết định **ai bị cắt khi
thật sự đưa input vào model**. Bằng chứng: cùng một ngưỡng thì hai lần đo khác prompt cho ra độ
dài input y hệt nhau, chỉ khác cột `% review > max_length`. **Nếu** một prompt vượt ngưỡng thì **mất phần
cuối** - đúng chỗ đặt yêu cầu định dạng đầu ra và khuôn JSON, nên mẫu đó **mất luôn hướng dẫn định dạng**
(hiện tại ở ngưỡng 2304 không mẫu nào vượt ngưỡng).





### 4.3. Trần token đầu vào và vì sao `max_length` khác nhau giữa 4 model

Mỗi model có một **trần kiến trúc** = `max_position_embeddings` trong config của model. Ngưỡng cắt
`max_length` của dự án luôn nhỏ hơn trần này, nên input đưa vào model **không bao giờ vượt** khả năng
nhận của nó. Trần đọc từ config của model, không phải từ `tokenizer.model_max_length` (tokenizer của
Qwen khai một số rất lớn, còn hai tokenizer RoBERTa/XLM-R trả số sentinel).

| Model | Trần kiến trúc (`max_position_embeddings`) | `max_length` đang dùng | Dư địa |
| --- | --- | --- | --- |
| `phobert-base-v2` | 258 | 256 | 2 |
| `visobert` | 514 | 256 | 258 |
| `qwen3-4b-instruct-2507` | 262.144 | 2304 | 259.840 |
| `qwen3-0.6b` | 40.960 | 2304 | 38.656 |

> **Nguồn trần:** đọc từ `config.json` của model - `data/models/Qwen3-4B-Instruct-2507/config.json` cho `max_position_embeddings = 262.144`; `data/models/Qwen3-0.6B/config.json` cho `40.960`. Với **Qwen3-0.6B**: giới hạn **cứng** của kiến trúc là **40.960**, còn **ngữ cảnh native được huấn luyện** là **32.768** (phạm vi đảm bảo chất lượng). Dự án chặn theo giá trị của `config.json` (`40.960`).

#### Bốn ngưỡng và căn cứ chọn

| Model | Input gồm gì | `max_length` | Căn cứ con số |
| --- | --- | --- | --- |
| `phobert-base-v2` | CHỈ review (đã tách từ) | 256 | "Max length" chính chủ của PhoBERT; trần 258. Vài review dài tới **301** (vượt cả trần) nên **0,02% train bị cắt** |
| `visobert` | CHỈ review (nguyên bản) | 256 | Lựa chọn của dự án: review dài nhất **229** < 256 (**0% cắt**), bằng PhoBERT để cùng ngân sách input |
| `qwen3-4b-instruct-2507` | prompt + review + ví dụ | 2304 | Số đo: mức 5 ví dụ dài nhất 2.122 → **0% cắt** |
| `qwen3-0.6b` | prompt + review + ví dụ | 2304 | Cùng tokenizer + cùng prompt như bản 4B ⇒ cùng số token ⇒ cùng ngưỡng |

#### Gốc rễ khác nhau: input của encoder và LLM khác nhau

| | Encoder (PhoBERT / ViSoBERT) | LLM (Qwen3) |
| --- | --- | --- |
| Input | CHỈ review | CẢ prompt (system + yêu cầu định dạng + ví dụ + review) |
| Độ dài thật (train) | PhoBERT TB 29,97 (max **301** → **0,02% cắt**, vượt cả trần 258); ViSoBERT TB 43,46 (max **229** → **0% cắt**) | `absa_cot_v1` TB 990,50 (max 1.235, 0% cắt); 5 ví dụ TB 1.877,50 (max **2.122**) |
| Trần model | nhỏ (258 / 514) | rất lớn (262.144 / 40.960) |
| Ai quyết định ngưỡng | trần model + so sánh công bằng | số đo (prompt dài ~2.000 token) |

Vì vậy **không thể dùng chung một ngưỡng**: 2304 làm encoder vượt trần (258/514), còn 256 thì Qwen bị cắt
gần hết prompt.

#### Vì sao trong cùng nhóm lại bằng nhau

- **Hai encoder = 256**: PhoBERT 256 gần như chạm trần (dư 2); ViSoBERT có thể tới 514 nhưng **cố tình**
  chọn 256 để hai encoder có **cùng ngân sách input** - so sánh mới công bằng.
- **Hai Qwen = 2304**: cùng `tokenizer.json` (giống từng byte) và cùng bộ prompt nên cùng số token; vẫn khai
  riêng mỗi model một file vì mỗi model một tokenizer.

#### Vì sao đúng 256 cho encoder

- **ViSoBERT**: review dài nhất 229 < 256 → **0% cắt**.
- **PhoBERT**: 256 = ngưỡng chính chủ; vài review dài tới **301 vượt cả trần 258** nên **không thể tránh** -
  nâng lên 258 cũng không cứu được. Mức cắt thực tế: **0,02% train** (vài mẫu), val/test **0%**.

Hai lớp bảo đảm, cùng đọc một nguồn (`src/preprocessing/token_stats.py`):

1. **Cắt khi dùng.** `build_inputs()` truyền `truncation=True, max_length=<limit()>`, nên **toàn bộ prompt**
   (system + review + ví dụ, sau chat template) là **một chuỗi** và bị **cắt còn tối đa `max_length`** token
   trước khi vào model. Prompt **≤ `max_length`** thì model nhận **trọn vẹn**; dài hơn thì chỉ mất **phần
   đuôi**. Dù dài bao nhiêu, model cũng không vượt trần.
2. **Chặn ngưỡng vượt trần.** `position_limits()` đọc `max_position_embeddings` của từng model;
   `run_token_stats.py` **từ chối** một `--max-length` lớn hơn trần (kèm gợi ý dùng giá trị nhỏ hơn), và
   bước ĐO (`_check_max_length`) cũng chặn `max_length` vượt giới hạn model. Nhờ vậy không có cấu hình
   nào khiến bảng số liệu báo "0% bị cắt" trong khi model thật đã cắt.

Nơi ĐO (`encode()`, **KHÔNG** cắt) và nơi DÙNG (`build_inputs()`, **CÓ** cắt) cùng đọc `limit()`, nên cột
`% review > max_length` phản ánh đúng số mẫu bị cắt khi chạy. Phần **đầu ra** tách riêng: `max_new_tokens`
(400) - một lượt CoT có input ≤ 2304 và output ≤ 400, tổng vẫn cách xa trần 262.144.

## 5. Cài đặt cho tiền xử lý cho model (cả nhóm dùng cùng một bản)

Ba việc, theo đúng thứ tự:

```bash
# 1) Thư viện Python của dự án (đã gồm transformers; torch để dành cho bước huấn luyện)
pip install -r requirements.txt

# 2) JAVA cho bộ tách từ chính chủ: JDK 17 LTS (Temurin) - KHÔNG cần quyền admin
powershell -ExecutionPolicy Bypass -File scripts\setup\setup_java.ps1

# 3) Thư viện Python + model VnCoreNLP (jar + model tách từ)
powershell -ExecutionPolicy Bypass -File scripts\setup\setup_vncorenlp.ps1
```

Trên Colab/Linux thì ba việc đó là (ô bootstrap của notebook PhoBERT làm tự động, không phải gõ tay):

```bash
pip install -r requirements.txt
apt-get install -y default-jdk                     # ảnh Colab đã có JDK (đã gặp JDK 21); chỉ cần ≥ 1.8
export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which javac))))   # pyjnius tìm JVM qua biến này
pip install py-vncorenlp
# model VnCoreNLP (27 MB): gói bàn giao đã kèm ở data/models/vncorenlp/, và nếu thiếu thì ô bootstrap
# của notebook PhoBERT tự tải về đúng gốc dữ liệu - không phải chép tay
```

Vì sao cần Java, và vì sao phải là script chứ không phải "cài gì cũng được":

| Điều | Chi tiết |
|------|----------|
| Bộ tách từ chính chủ là chương trình **Java** | RDRSegmenter nằm trong `VnCoreNLP-1.2.jar`; `py-vncorenlp` gọi nó qua **pyjnius (JNI)**, không phải qua lệnh `java` |
| pyjnius tìm JVM qua biến môi trường | `JDK_HOME` rồi `JAVA_HOME`; không thấy thì báo `"Unable to find JAVA_HOME"` - một lỗi chung chung, dễ làm sập cả phép đo. Vì vậy dự án **kiểm tra Java trước** và báo lỗi kèm đúng lệnh cần chạy |
| Vì sao cài bằng ZIP thay vì `winget` | Cài vào `%USERPROFILE%\.jdks\temurin-17`: không cần quyền admin, gỡ ra chỉ cần xoá thư mục, và **mọi máy dùng cùng một dòng 17.0.x LTS** (script tải từ Adoptium API và kiểm SHA256) |
| Vì sao không dùng `py_vncorenlp.download_model()` | Hàm đó gọi `wget` qua `os.system`, mà Windows không có wget -> không tải được gì rồi báo lỗi khó hiểu. `scripts\setup\setup_vncorenlp.ps1` tải bằng PowerShell và **kiểm kích thước từng file**. Trên Colab/Linux hàm đó chạy được, nhưng gói bàn giao vẫn kèm sẵn model để lượt chạy không phụ thuộc vào mạng |
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


