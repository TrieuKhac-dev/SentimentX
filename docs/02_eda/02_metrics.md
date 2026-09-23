# Cách tính từng chỉ số của EDA

Đọc file này **trước khi đọc báo cáo EDA**: mọi chỉ số ở đây đều là quy ước do
dự án chọn, không phải một chuẩn học thuật. Nơi nào là "chọn tay" thì đều được nói rõ.

## 1. Cách đọc các con số p50, p95, p99

Đây là **phân vị** (percentile). Cách hiểu đơn giản: xếp toàn bộ review theo độ
dài từ ngắn đến dài, rồi nhìn vào vị trí phần trăm.

| Ký hiệu | Nghĩa | Dùng để |
|---------|-------|---------|
| **p50** (trung vị) | **một nửa** số review ngắn hơn hoặc bằng mức này | biết độ dài "điển hình" |
| **p95** | **95%** review ngắn hơn hoặc bằng mức này (chỉ 5% dài hơn) | biết "phần đuôi" bắt đầu từ đâu |
| **p99** | **99%** review ngắn hơn hoặc bằng mức này (chỉ 1% dài hơn) | phát hiện review cực dài, bất thường |

Ví dụ với tập train của dự án: p50 = 81 ký tự, p95 = 222 ký tự, p99 = 299 ký tự,
dài nhất = 635 ký tự. Nghĩa là một nửa số review ngắn hơn 81 ký tự; phần vượt
299 ký tự là rất hiếm và thường là nội dung bị **dán** từ nơi khác.

> Vì sao dùng p50 thay vì trung bình? Vì trung bình bị vài review siêu dài "kéo
> lệch". p50 không bị ảnh hưởng bởi các giá trị cực đoan.

## 2. Đếm emoji

Emoji được bắt theo CHUỖI Unicode (`utils.EMOJI_PATTERN`), gồm cả tông màu da và
chuỗi nối bằng ZWJ, nên mỗi chuỗi tính là 1 emoji và `❤` / `❤️` được gộp chung khi
đếm.

## 3. Ví dụ minh hoạ nhóm nhiễu — dữ liệu THẬT, lấy mẫu có hạt giống

Ví dụ trong bảng "Ví dụ minh hoạ theo nhóm nhiễu" là **dòng thật** của dữ liệu
gốc, không phải ví dụ viết tay: với mỗi nhóm nhiễu, mỗi split lấy NGẪU NHIÊN một
dòng (rút gọn 120 ký tự) bằng `random.Random(EXAMPLE_SEED)` — hạt giống cố định
nên chạy lại cho ra đúng những ví dụ cũ. Bảng trên báo cáo hiện 1 ví dụ mỗi
nhóm mỗi split; file CSV ghi 3 ví dụ.

Cột **"dòng trong file"** là số thứ tự của dòng dữ liệu trong
`data_train.csv` / `data_val.csv` / `data_test.csv` (dòng 1 = dòng đầu tiên sau
dòng tiêu đề). Muốn mở đúng dòng đó trong Excel: cộng thêm 1 cho dòng tiêu đề.

## 4. "Ứng viên gibberish" là POLICY, không phải chuẩn đo

Ngưỡng nhận diện nằm trong `src/config.py` và `src/pipeline/clean.py`, không phải
một chuẩn học thuật: một review bị coi là gibberish khi **≥ 50% token "không giống
từ"**, trong đó token bị coi bất thường nếu (dài hơn 2 ký tự và không có nguyên âm)
hoặc (dài từ 15 ký tự); token ≤ 2 ký tự luôn được coi là bình thường, và review
CHỈ toàn emoji được miễn (emoji là tín hiệu cảm xúc thật).

Vì sao vẫn dùng: đo trên dữ liệu gốc `cosmetics` cho thấy nhóm này chiếm **3,00%**
(train 2,99% / val 2,40% / test 3,70%) và mẫu rơi vào nhóm này gần như toàn bộ là
chuỗi gõ bàn phím (`Obdhsjdbdhdjdjdjsgs...`, `Hy…jjjjjjjj`), tức nó lọc đúng thứ cần
lọc. Các ngưỡng là chọn tay, nên trong báo cáo chỉ số này xuất hiện **một dòng**
trong bảng "Chỉ số chất lượng theo split"; bật/tắt bằng
`clean.remove_gibberish` trong `configs/pipeline.yaml`, và mọi dòng bị loại đều được
ghi lại ở `removed_records.csv`.

## 5. "Trùng theo KHOÁ so trùng" — và nó KHÁC bước Normalize thế nào

Chỉ số "trùng theo khoá so trùng" (EDA 03, EDA 05) **không** dùng văn bản gốc để
so, mà so **khoá so trùng** do `utils.dedup_key()` tạo. Khoá này đi qua 6 bước:

1. **NFC** — gộp hai cách mã hoá dấu tiếng Việt (tổ hợp dấu vs dựng sẵn) về một dạng;
2. `lower()` — chuyển hết về chữ thường;
3. `normalize_whitespace()` — gộp khoảng trắng/tab, bỏ khoảng trắng quanh xuống dòng;
4. **tuỳ chọn** `remove_diacritics()` — bỏ dấu tiếng Việt (`đẹp` → `dep`); hiện đang
   **TẮT** (xem đoạn dưới);
5. thay mọi ký tự **không phải chữ/số** (dấu câu, emoji) bằng khoảng trắng;
6. gộp khoảng trắng lần nữa.

> ⚠️ **Đừng lẫn hai chữ "chuẩn hoá" trong dự án:**
>
> | | Bước Normalize (Step 4) | Khoá so trùng (`dedup_key`) |
> |---|---|---|
> | Sửa văn bản thật? | **Có** | **Không** — chỉ để so |
> | Làm gì | chữ thường (tuỳ chọn), NFC, khoảng trắng, ký tự lặp (tuỳ chọn) | lower, NFC, khoảng trắng, bỏ dấu câu — **bỏ dấu tiếng Việt chỉ khi bật `ignore_diacritics` (đang TẮT)** |
> | Ở đâu | `src/pipeline/normalize.py` | `src/utils.py`, dùng bởi bước Clean |
>
> Bước Normalize **không bao giờ bỏ dấu tiếng Việt**. Văn bản đi vào model vẫn là
> `"Son đẹp lắm"`, không phải `"son dep lam"`.

**Vì sao bước 5 (bỏ dấu câu) cần:** `"Son đẹp!!!"` và `"Son đẹp"` là hai khoá khác
nhau nếu giữ dấu câu, nên chúng không bị coi là trùng. Đổi dấu câu thành khoảng
trắng rồi gộp khoảng trắng giúp hai câu đó về cùng một khoá.

**Vì sao khoá so trùng có bước 4 (bỏ dấu tiếng Việt) — và vì sao nó đang TẮT:** bỏ dấu
giúp bắt được trường hợp một review được đăng hai lần, một lần có dấu và một lần không
dấu (`"Chat luong san pham tuyet voi"` vs `"Chất lượng sản phẩm tuyệt vời"`). Rủi ro
là tiếng Việt bỏ dấu có thể trùng nhau giữa hai câu khác nghĩa, nên bước này đã được
**đo riêng** để có cơ sở quyết định: trên dataset cosmetics, khoá **giữ dấu** (đang
dùng) loại 242 dòng ở train và 291 dòng trên 3 split, còn khoá **bỏ dấu** loại 246
dòng ở train và 296 dòng trên 3 split — bỏ dấu chỉ loại **thêm 5 dòng** (0,03%), mà
lại gộp cả những cặp câu chỉ giống nhau sau khi bỏ dấu.

Kết luận: dự án **không bỏ dấu tiếng Việt ở bất kỳ chỗ nào**, kể cả trong khoá so
trùng — nên `clean.deduplicate.ignore_diacritics` trong `configs/pipeline.yaml` để
`false`. Đây vẫn là công tắc thật: đổi giá trị thì **cả EDA lẫn pipeline** đổi theo —
EDA 03 và EDA 05 đọc chính khoá đó từ config, nên hai bên không bao giờ lệch nhau.
Báo cáo pipeline có một dòng "deduplicate.ignore_diacritics" trong bảng "Thiết lập
Clean đang áp dụng" để chứng minh đang chạy ở chế độ nào.

Khoá này cũng được dùng cho **rò rỉ dữ liệu** (loại val/test trùng train), cùng
một quy tắc.

**Bằng chứng khoá này KHÔNG hề bỏ dấu trong dữ liệu** (câu hỏi rất dễ lo): bước
Final Validate có hạng mục **"Văn bản chỉ đổi hình thức"** — nó lấy từng dòng được
giữ lại, áp lại đúng quy tắc chuẩn hoá lên dòng gốc, rồi so với văn bản trong
`processed_*.csv`. Trên cosmetics: **ĐẠT — 15344/15344 dòng khớp đúng dòng gốc sau
chuẩn hoá (không mất dấu tiếng Việt)**. Nghĩa là khoá so trùng chỉ dùng để **so**;
văn bản xuất ra không mất một dấu nào. Chi tiết phép kiểm:
[04_invariants.md §2](../03_pipeline/04_invariants.md).

## 6. "Có ký tự lặp" — quy tắc và mốc chọn

Đếm số review có **một ký tự lặp liên tiếp từ 3 lần trở lên** (`đẹppppp`, `ok.....`).
Mốc 3 là chọn tay (`config.REPEATED_CHAR_MIN`) vì lặp 2 lần xuất hiện trong từ tiếng
Việt bình thường. Chỉ số này chỉ để **đo**: cấu hình hiện tại
`normalize.repeated_chars: false` vì ký tự lặp mang thông tin cảm xúc (`đẹppppp`
khác `đẹp`); muốn thí nghiệm thì bật và chạy lại pipeline để ra phiên bản mới.

## 7. Dấu hiệu quảng cáo và dấu hiệu code / HTML

**Quảng cáo / tin nhắn nhà mạng** — so khớp (regex, không phân biệt hoa thường) với
`config.AD_PATTERNS`: `[qc]`, `[tb]`, `viettel`, `mobifone`, `vinaphone`,
`http(s)://`, `www.`, `bit.ly`, `lh 198`, `tổng đài`, `soạn <X> gửi`. Đây là
**danh sách gõ tay** các dấu hiệu gặp trong dữ liệu, không phải một bộ phân loại học
máy: nó chỉ bắt được những dạng đã thấy và có thể bỏ sót quảng cáo viết theo cách
khác. Công tắc: `clean.remove_ads`; mọi dòng bị loại đều nằm trong
`removed_records.csv` để kiểm lại bằng tay.

**Code / HTML / SQL** — review bị dán từ nơi khác (mã trang web, câu lệnh) cũng là
nhiễu, nên được **đo riêng** bằng `config.CODE_PATTERNS`: thẻ HTML (`<p>`, `</div>`,
`<br/>`), entity HTML (`&nbsp;`, `&quot;`), câu lệnh SQL (`select … from`,
`insert into`, `drop table`), từ khoá code có cú pháp (`function(`, `console.log(`,
`def …(`, `{{`, `}}`, `#include <`, `<?php`).

Danh sách này **cố tình chặt** để ít dương tính giả: những ký hiệu người viết vẫn
dùng trong câu bình thường **không** bị tính là code — ví dụ `=>` (mũi tên),
`{•~• ^~^}` (kaomoji), `//` (gạch chéo trong văn bản). Đo trên dataset cosmetics:
**1/16.227 dòng (0,01%)** khớp — đúng một entity `&quot;`. (Sáu review còn lại của
nhóm "dán từ nơi khác" là URL có tham số, đã bị `AD_PATTERNS` bắt trước, nên chúng
nằm ở dòng "có dấu hiệu quảng cáo".)

Vì con số rất nhỏ và luật đã viết chặt, công tắc `clean.remove_code` **đang BẬT**:
dòng có `&quot;` đó bị loại ở bước Clean (nằm trong `removed_records.csv` với lí do
"chứa mã HTML / SQL / code"). Muốn kiểm chứng bằng mắt: bảng "Ví dụ minh hoạ theo
nhóm nhiễu" có một dòng cho nhóm "có dấu hiệu code / HTML".

> Ghi chú: trước đây dự án có thêm nhóm "có dấu hiệu nhận xu" (`nhận xu`, `lấy xu`,
> `kiếm xu`...). Nhóm này **đã bị bỏ khỏi dự án**: mẫu câu đó xuất hiện cả trong
> review có cảm nhận thật (khen màu son rồi chèn câu "hình ảnh chỉ mang tính chất
> nhận xu"), nên nó không phải dấu hiệu nhiễu đáng tin.

## 8. Teencode / từ lạ — quy tắc CẤU TRÚC, có dương tính giả

Báo cáo liệt kê **từ** bị gắn cờ (không báo "số review có teencode" vì tỉ lệ review
dính chỉ tiêu này ~44%, gần một nửa dữ liệu, nên không phân biệt được gì). Phép
quét chạy trên **cả 3 split**. Một từ bị gắn cờ khi rơi vào một trong các quy tắc
cấu trúc (`utils.teencode_reasons`):

| Lí do | Quy tắc | Ghi chú |
|-------|---------|---------|
| chữ không phải chữ Latin | từ chứa ký tự chữ không thuộc bảng chữ cái Latin (`𝐭`, `ᴗ`, `ω`, chữ Hàn/Ả Rập…) | xếp **riêng** và **không xét các quy tắc còn lại** — đây không phải teencode tiếng Việt nên không thể bị dán nhãn sai (217 từ) |
| chữ Latin ngoài bảng chữ cái tiếng Việt (f, j, w, z) | từ chứa f/j/w/z | tiếng Anh, tên thương hiệu (`review`, `swatch`, `focallure`), và cả chuỗi gõ bàn phím chứa các chữ này (2.736 từ) |
| trộn chữ và số | từ chứa cả chữ và số | giá viết tắt (`50k`), mốc thời gian (`2tuan`), và cả tên sản phẩm có số (`3ce`) (584 từ) |
| một ký tự phụ âm | từ dài **đúng 1 ký tự** và ký tự đó là **phụ âm Latin cơ bản** (`k` = không, `r` = rồi, `n`, `m`, `t`, `c`, `v`, `d`…) | **chỉ 20 từ** và đúng là 20 phụ âm ASCII — không còn bắt ký tự trang trí như trước |
| không có nguyên âm | từ không chứa nguyên âm nào | viết tắt thật: `mn`, `đc`, `mng`, `sp`, `kh`, `vs`, `cx`… (1.768 từ) |

> **Không dương tính giả trên từ thông thường — có kiểm chứng:** chương trình tự
> kiểm bằng cách soi **300 từ phổ biến nhất** của dữ liệu (chắc chắn là từ thật).
> Kết quả trên cosmetics: **13 từ bị gắn cờ, và cả 13 đều là viết tắt thật** —
> `k, mn, đc, mng, sp, kh, r, n, vs, ng, cx, m, t`. Danh sách này được ghi ra
> `03_quality_teencode_common_flagged.csv` để tra lại bất cứ lúc nào
> (`AUDIT_TOP_WORDS` trong `src/eda/quality_noise.py`).
>
> Ba quy tắc còn lại an toàn về nguyên tắc: mọi **từ tiếng Việt đều có nguyên âm**
> (nên "không có nguyên âm" không thể bắt oan từ thật), số thuần (`2023`) không bị
> gắn cờ vì quy tắc yêu cầu phải có chữ cái, và ký tự không phải chữ Latin được
> tách sang lí do riêng.

Hệ quả cần biết khi đọc bảng: đây là **danh sách ứng viên để phân tích**, KHÔNG phải
kết luận "từ này sai". Quy tắc đoán theo **hình thức**, không đoán ngữ âm tiếng
Việt (đoán kiểu "phải là âm tiết hợp lệ" sẽ gắn cờ oan cả `siêu`, `tiền`,
`chuyển`), nên teencode **trùng cấu trúc âm tiết** như `ko`, `tui` không bị bắt.
Pipeline **không** thay thế teencode: văn bản giữ nguyên như người viết. Bảng "Các
quy tắc gắn cờ và quy mô mỗi quy tắc" cho biết mỗi quy tắc bắt được bao nhiêu từ
khác nhau, giúp đọc bảng top từ mà biết phần nào là dương tính giả.

> **Vì sao teencode CHỈ được ĐO, không bao giờ bị loại bỏ / thay thế:** dự án không
> có bằng chứng khoa học nào để nói một cách viết lóng là "sai" — đoán nghĩa của
> teencode (kể cả bằng từ điển) đều là suy diễn, và viết lại văn bản sẽ tạo ra dữ
> liệu không còn là điều người dùng nói. Vì vậy:
>
> - bộ quy tắc này **không có công tắc nào trong `configs/pipeline.yaml`**; pipeline
>   không có phép loại bỏ / thay thế / viết lại teencode, cũng không có phép bỏ dấu
>   tiếng Việt;
> - bước Final Validate **chứng minh** điều đó bằng số liệu: hạng mục "Văn bản chỉ
>   đổi hình thức" đối chiếu từng ký tự của `processed_*.csv` với dòng gốc — nếu có
>   từ nào bị viết lại, hạng mục này báo LỖI ngay
>   ([04_invariants.md §2](../03_pipeline/04_invariants.md));
> - bảng cấu hình ở Step 4 in thẳng hai dòng "thay teencode … **Không**" và "bỏ dấu
>   tiếng Việt trong văn bản … **Không**" để người đọc báo cáo khỏi phải suy đoán.

## 9. Kích thước từ vựng và "số từ / review" — đếm TỪ, không phải subword

Cách đếm (`src/eda/text_analysis.py`) trên **từng split**:

| Chỉ số | Cách tính |
|--------|-----------|
| tổng số token | nối toàn bộ review của split rồi đếm bằng `utils.tokenize` |
| số từ (token) trung bình / review | tổng số token chia số review của split |
| số từ vựng (token duy nhất) | số token **khác nhau** trong split (kiểu `set`) |
| từ vựng riêng của split | số token chỉ xuất hiện ở split này, không có ở hai split kia |

`utils.tokenize` = `re.findall(r"\w+", text.lower())`: tách theo chữ/số, bỏ dấu câu
và emoji, **không** dùng tokenizer của model. Vì vậy "từ" ở đây là đơn vị để **khảo
sát dữ liệu**, không phải đơn vị model thật đọc — mỗi model chẻ câu thành subword
theo tokenizer riêng, và độ dài input thật được đo riêng ở pha 3 bằng
`run_token_stats.py` (xem [02_phase3_input.md §2](../04_experiments/02_phase3_input.md)).
Chỉ số "OOV so với train" ở mức từ đã bỏ khỏi EDA vì cả 4 model đều dùng tokenizer
subword, nên con số đó không dẫn tới quyết định nào.

Thẻ số liệu "Số từ vựng (token duy nhất)" và "Số từ (token) trung bình / review" đều
hiện cho cả **train / val / test**; cả hai đi qua đúng một đoạn code như bảng trên,
nên khi thêm split mới (hoặc đổi cách đếm) chúng tự cập nhật theo.

## 10. "x cụm 2 từ hay gặp nhất theo khía cạnh" — cách tính

Với mỗi khía cạnh, chương trình làm đúng ba bước:

1. lấy **mọi review có nhắc khía cạnh đó** (ô khía cạnh không trống) trong cả 3 split;
2. với mỗi review: `utils.tokenize` rồi ghép **mọi cặp 2 từ liền nhau** (bigram);
3. đếm số lần từng bigram xuất hiện rồi lấy **top 5**.

Điểm cần lưu ý: bigram được đếm trên **toàn bộ review**, không chỉ trong câu nói về
khía cạnh đó — dữ liệu chỉ có nhãn ở mức khía cạnh, không có nhãn ở mức câu, nên
không thể tách ra câu nào ứng với khía cạnh nào. Cột "số review nhắc khía cạnh
(3 split)" cho biết mẫu số của từng dòng, để phân biệt "bigram gặp nhiều vì khía cạnh
đó vốn có nhiều review" với "bigram đặc trưng cho khía cạnh".

## 11. Số dòng KHÔNG có nhãn khía cạnh nào — nhóm dễ đọc nhầm nhất

Một phần dữ liệu có **mọi cột khía cạnh đều trống** (cosmetics: train 2301 dòng
= 17,73% / val 271 / test 312 — tổng 2884 dòng). Đây không phải lỗi đọc dữ liệu:
trong file gốc, gần như toàn bộ nhóm này (2287/2301 dòng train) **chỉ có nhãn ở cột
`others`** — cột này bị bỏ theo config (`drop_columns`) vì nó chỉ mang nhãn
`neutral`, không ứng với khía cạnh nào của bài toán. 14 dòng còn lại thật sự không
có nhãn nào.

Cách báo cáo trình bày nhóm này (để không gây hiểu nhầm):

- nêu bằng **một thẻ số liệu riêng**: "Số dòng không có nhãn khía cạnh nào (3 split)";
- biểu đồ "Số khía cạnh được nhắc trong một review" **chỉ vẽ từ 1 trở lên** và lấy
  mẫu số là số review **có nhãn** — nhờ vậy người đọc thấy đúng hình dạng phân bố,
  không bị một cột "0 khía cạnh ≈ 17%" nằm ngay giữa biểu đồ nói về review có nhãn;
- bản CSV giữ đủ mọi giá trị 0…7, kèm **hai** tỉ lệ (trên toàn split và trên số
  review có nhãn) để tra cứu lại.

Liên hệ với pipeline: những dòng này vẫn được giữ trong `processed_*.csv` (dạng
multi_head với mọi ô = 0) để truy vết, nhưng **không sinh bản ghi ABSA** nào — đó là
lí do số bản ghi ABSA (13213 trên cosmetics) nhỏ hơn số dòng dữ liệu (15344).
Xem [03_pipeline/02_steps.md §5](../03_pipeline/02_steps.md).

## 12. Trùng lặp giữa các split — hai cách đếm KHÁC NHAU

Hai con số này hay bị đem so với nhau, nhưng chúng đo hai thứ khác nhau:

| Cách đếm | Đơn vị | Phạm vi | Ở đâu |
|----------|--------|---------|-------|
| số **văn bản** xuất hiện ở cả hai split của cặp (`train↔val`, `train↔test`, `val↔test`) | văn bản | mọi cặp split | biểu đồ EDA 05 + `05_split_duplicates.csv` |
| số **dòng** của val/test trùng train | dòng | chỉ so với train | thẻ số liệu EDA 05 + `05_split_duplicate_totals.csv` |

Con số ① **không cộng lại ra** tổng số văn bản bị trùng: một văn bản nằm ở cả 3 split
bị đếm ở cả 3 cặp, nên tổng theo cặp lớn hơn số văn bản thật sự bị trùng. Trên
cosmetics, chuỗi "trùng chính xác" có 18 + 18 + 5 = 41 theo cặp nhưng chỉ **31** văn
bản bị trùng; chuỗi "trùng theo khoá so trùng" có 23 + 22 + 9 = 54 theo cặp nhưng chỉ
**38** văn bản bị trùng. File `05_split_duplicate_totals.csv` ghi cả hai cách đếm để
đối chiếu.

Con số ② chính là phép mà bước Clean thực hiện khi
`clean.leakage.remove_eval_overlap = true`: lấy khoá so trùng của **train**, rồi
loại khỏi val/test mọi dòng có khoá đó. Vì vậy khi so EDA với pipeline, hãy so với
con số ② — và lưu ý Clean **xoá nhiễu TRƯỚC rồi mới xử lý rò rỉ**, nên số dòng bị
loại vì rò rỉ trong báo cáo pipeline luôn **nhỏ hơn hoặc bằng** con số ② của EDA
(cosmetics: EDA ② = 91 dòng, pipeline loại 84 vì 7 dòng trong số đó đã bị loại từ
bước xoá nhiễu).

## 13. Xung đột nhãn — "review" và "ô nhãn" là hai con số khác nhau

Khi cùng một văn bản (so bằng khoá so trùng) xuất hiện ở nhiều split nhưng nhãn
khác nhau, ta đếm hai mức:

- **số review bị xung đột** = số văn bản có **ít nhất một** ô nhãn xung đột;
- **số ô nhãn (review × khía cạnh) bị xung đột** = số cặp (văn bản, khía cạnh) bị
  gán nhãn khác nhau giữa các split.

Một review có thể xung đột ở 2–3 khía cạnh, nên số ô **≥** số review. Ở cosmetics
hai con số **tình cờ bằng nhau (4 và 4)** — không phải vì dữ liệu chỉ có 4 nhãn:
dữ liệu có **3 nhãn** (`positive` / `negative` / `neutral`) và **7 khía cạnh**, còn
"4 ô nhãn" là **kết quả đo**: chỉ 4 cặp (review, khía cạnh) thực sự bị gán nhãn khác
nhau giữa các split.

Bảng xung đột trên báo cáo là **danh sách đầy đủ, không cắt bớt**: mỗi dòng là một ô
nhãn xung đột, kèm nhãn của từng split (`-` = split đó không có văn bản này,
`(không nhắc tới)` = ô trống). Căn cứ vào số này, policy được chọn là
`conflict_policy: quarantine` — cách ly **toàn bộ** bản ghi của nhóm đó thay vì tự
chọn một nhãn (xem [03_pipeline/02_steps.md §3](../03_pipeline/02_steps.md)).

---

Xem tiếp: [03_modules.md](03_modules.md) — chi tiết từng module EDA.




