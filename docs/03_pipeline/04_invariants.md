# Ba bất biến của pipeline - và cách chứng minh

Ba điều dưới đây **không được phép xảy ra** ở bất kỳ bước nào. Mỗi điều đều có một
phép kiểm tự động riêng, in kết quả lên báo cáo pipeline (Step 4 và Step 6).

## 1. Nhãn không bị thay đổi

> **"Text cleaning không được vô tình làm biến đổi label."**

Dự án kiểm chứng điều này bằng **dấu vân tay nhãn**:

1. Trước khi chuẩn hoá, tính một chuỗi "vân tay" cho toàn bộ nhãn
   (`src/pipeline/normalize.py::labels_signature`).
2. Sau khi chuẩn hoá, tính lại.
3. Nếu hai chuỗi **giống nhau** -> chứng minh được nhãn không bị chạm tới.

Final Validate kiểm tra lại một lần nữa và ghi kết quả vào `final_validation.json`.

Kết quả trên dữ liệu hiện tại: **ĐẠT** - nhãn không bị thay đổi.

**Thẻ "Nhãn có bị bước này thay đổi?" ở Step 4** chính là phép kiểm này, viết lại
cho người đọc: giá trị `Không` nghĩa là **dấu vân tay nhãn trước và sau chuẩn hoá
trùng khớp** (chuỗi SHA-256 của toàn bộ ô nhãn, tính theo từng split và từng khía
cạnh). Nếu ai đó sửa code khiến bước chuẩn hoá chạm vào cột nhãn, thẻ này sẽ hiện
`CÓ` và Step 6 báo LỖI - đó là mục đích của nó.

Vì sao phải kiểm bằng dấu vân tay mà không so từng ô? Vì so từng ô sẽ phải giữ lại
một bản sao nhãn nữa trong bộ nhớ; vân tay chỉ cần một chuỗi ngắn mà vẫn chứng minh
được "không đổi một ô nào".

## 2. Văn bản không mất dấu tiếng Việt

Nhãn được bảo vệ bằng dấu vân tay, còn **văn bản** được bảo vệ bằng một phép đối
chiếu từng dòng (hạng mục "Văn bản chỉ đổi hình thức" ở Step 6):

1. Bước Load giữ lại **văn bản gốc** của từng dòng (đúng thứ tự gốc).
2. Bước Clean giữ lại **vị trí gốc** của những dòng được giữ.
3. Bước Final Validate lấy từng dòng trong `train.csv`, `val.csv`, `test.csv`, áp lại đúng quy tắc
   chuẩn hoá (`normalize_steps` - cùng hàm mà bước Normalize dùng) lên dòng gốc
   tương ứng, rồi so **từng ký tự**.

Kết quả trên cosmetics: **ĐẠT - 15344/15344 dòng khớp đúng dòng gốc sau chuẩn hoá**.
Vì phép so là từng ký tự, kết luận rút ra được:

- **Văn bản không mất một dấu tiếng Việt nào**, và khoá so trùng cũng vậy: config đang
  để `steps.clean.deduplicate.ignore_diacritics: false`, nên bỏ dấu không xảy ra ở **bất kỳ
  chỗ nào** trong dự án;
- bước xoá trùng lặp / xử lý rò rỉ **chỉ bỏ dòng**, không sửa chữ của dòng được giữ;
- nếu ai đó thêm một phép "bỏ dấu" vào `normalize_steps`, hạng mục này **lập tức
  báo LỖI** kèm 5 dòng sai đầu tiên (dòng gốc, kết quả mong đợi, kết quả thực tế).

Vì sao không bỏ dấu tiếng Việt ở bất kỳ chỗ nào (kể cả trong khoá so trùng): xem
[02_eda/02_metrics.md mục 5](../02_eda/02_metrics.md) - bỏ dấu chỉ loại thêm 5 dòng
(0,03%) mà lại gộp cả những cặp câu chỉ giống nhau sau khi bỏ dấu.

## 3. Điều pipeline KHÔNG làm: teencode

Bộ quy tắc nhận diện teencode / từ lạ nằm **hoàn toàn ở EDA**
(`src/eda/quality_noise.py` gọi `utils.teencode_reasons`). Trong `src/pipeline/`
**không có** phép loại bỏ, thay thế hay viết lại teencode, và
`configs/pipeline/v0.1.0.yaml` **không có** config nào cho việc đó - tìm chữ "teencode"
trong `src/pipeline/` chỉ thấy ghi chú, không thấy code.

Lý do: dự án không có bằng chứng khoa học nào để nói một cách viết lóng là "sai";
viết lại văn bản người dùng còn làm dữ liệu không còn là điều họ nói. Bốn phép duy
nhất được phép sửa văn bản là `lowercase`, `unicode`, `whitespace`, `repeated_chars`
(ba phép đầu/sau đều tuỳ chọn), và bước Final Validate **chứng minh** rằng ngoài bốn
phép đó không ký tự nào bị đổi
([mục 2](#2-văn-bản-không-mất-dấu-tiếng-việt) của file này).

---

Xem thêm: [02_steps.md mục 4](02_steps.md) - chi tiết bốn phép chuẩn hoá;
[02_eda/02_metrics.md mục 8](../02_eda/02_metrics.md) - vì sao teencode chỉ được đo.
