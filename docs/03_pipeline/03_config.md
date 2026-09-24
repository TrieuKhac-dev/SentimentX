# Cấu hình pipeline (`configs/pipeline/v0.1.0.yaml`)

## 1. Cách đọc file này

- Mọi phép biến đổi đều **bật / tắt được**. Quy ước: `true` = BẬT (có thực hiện biến
  đổi), `false` = TẮT (giữ nguyên).
- Cấu hình được **ghi lại nguyên vẹn** vào `processing_log.json` mỗi lần chạy, và in
  thành bảng "Cấu hình đã dùng cho lần chạy này" ở cuối báo cáo pipeline - nên luôn
  truy vết được một phiên bản dữ liệu được tạo ra bằng cấu hình nào.
- Nếu file thiếu một khoá, `src/utils.py::load_pipeline_config` bổ sung giá trị mặc
  định theo nguyên tắc **an toàn nhất = tắt biến đổi**; riêng
  `clean.deduplicate.ignore_diacritics` dự phòng là `false` để đúng chính sách
  "không bỏ dấu tiếng Việt ở bất kỳ chỗ nào" của dự án.
- Trạng thái **đang chạy** (bảng tóm tắt) nằm ở [01_flow.md mục 3](01_flow.md). File này
  giải thích chi tiết từng khoá.

Bảng điều khiển `on_off()` đổi `true/false` thành `Bật/Tắt` khi in lên báo cáo; giá
trị gốc vẫn nguyên trong `processing_log.json`.

## 2. Step 2 - Validate

| Khoá                     | Mặc định | Ý nghĩa                       |
| ------------------------ | -------- | ----------------------------- |
| `validate.check_schema`  | `true`   | kiểm tra đủ cột, đúng tên cột |
| `validate.check_content` | `true`   | kiểm tra review rỗng, nhãn lạ |

Bước này chỉ ghi nhận lỗi, không sửa dữ liệu - chi tiết ở
[02_steps.md mục 2](02_steps.md).

## 3. Step 3 - Clean

| Khoá                                  | Mặc định       | Ý nghĩa                                                                                                                                                                                                                                                     |
| ------------------------------------- | -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `clean.remove_empty`                  | `true`         | loại review rỗng                                                                                                                                                                                                                                            |
| `clean.remove_gibberish`              | `true`         | loại chuỗi ký tự vô nghĩa                                                                                                                                                                                                                                   |
| `clean.remove_ads`                    | `true`         | loại quảng cáo / tin nhắn nhà mạng                                                                                                                                                                                                                          |
| `clean.remove_code`                   | `true`         | loại dòng chứa mã HTML / SQL / code (nhóm rất nhỏ, luật đã viết chặt)                                                                                                                                                                                       |
| `clean.deduplicate.exact`             | `true`         | loại trùng lặp chính xác                                                                                                                                                                                                                                    |
| `clean.deduplicate.normalized`        | `true`         | loại trùng lặp **theo khoá so trùng** (bỏ hoa/thường, dấu câu, gộp khoảng trắng) - không phải bước Normalize                                                                                                                                                |
| `clean.deduplicate.ignore_diacritics` | `false`        | khoá so trùng có bỏ dấu tiếng Việt hay không ("son dep" = "son đẹp"). **Giữ ở `false`**: dự án không bỏ dấu tiếng Việt ở bất kỳ chỗ nào - đo trên cosmetics, bật lên chỉ loại thêm 5 dòng (0,03%) mà lại gộp cả những cặp câu chỉ giống nhau sau khi bỏ dấu |
| `clean.deduplicate.scope`             | `within_split` | phạm vi so trùng: `within_split` hoặc `global`                                                                                                                                                                                                              |
| `clean.deduplicate.conflict_policy`   | `quarantine`   | cùng review nhưng nhãn khác nhau thì làm gì                                                                                                                                                                                                                 |
| `clean.leakage.remove_eval_overlap`   | `true`         | loại khỏi val/test những review đã có trong train (chống rò rỉ dữ liệu)                                                                                                                                                                                     |

**Về `conflict_policy`:**

- `quarantine`: đưa **tất cả** bản ghi của nhóm đó ra khỏi tập, ghi vào
  `quarantine_records.csv`. Pipeline **không tự quyết định** - người nghiên cứu
  xem lại bằng tay. Đây là mặc định.
- `keep_first`: giữ bản ghi đầu tiên, bỏ phần còn lại.

Cơ chế chạy của hai giá trị này (gom nhóm, so nhãn, ghi file): [02_steps.md mục 3](02_steps.md).

**Về `scope`:** `within_split` xử lý trùng trong từng split (giữ nguyên ranh giới
train/val/test như lúc gán nhãn); `global` gộp cả 3 split khi xét trùng - dùng làm
phương án thực nghiệm khi muốn biết "dữ liệu đã thật sự sạch trên toàn bộ dataset
chưa".

## 4. Step 4 - Normalize

| Khoá                           | Mặc định | Ý nghĩa                                                                                                                                                                                                 |
| ------------------------------ | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `normalize.lowercase`          | `false`  | chuyển hết về chữ thường. **Mặc định TẮT**: 89,45% review có chữ hoa (phần lớn chỉ là chữ đầu câu) và tokenizer subword phân biệt hoa/thường, nên giữ nguyên giúp model còn dùng được tín hiệu viết hoa |
| `normalize.unicode`            | `true`   | chuẩn hoá Unicode (NFC)                                                                                                                                                                                 |
| `normalize.whitespace`         | `true`   | chuẩn hoá khoảng trắng / xuống dòng                                                                                                                                                                     |
| `normalize.repeated_chars`     | `false`  | rút gọn `đẹppppp` -> `đẹpp`. **Mặc định TẮT** vì ký tự lặp mang cảm xúc                                                                                                                                  |
| `normalize.repeated_chars_max` | `2`      | số lần ký tự được giữ lại                                                                                                                                                                               |

> ⚠️ Bước này **KHÔNG bỏ dấu tiếng Việt** và **KHÔNG thay teencode**: văn bản giữ
> nguyên như người viết. Không có khoá nào trong file này điều khiển việc bỏ dấu /
> viết lại teencode - đó là chủ ý, không phải thiếu sót
> ([04_invariants.md mục 3](04_invariants.md)).

Ví dụ của bốn phép và cách đọc biểu đồ "Số review bị thay đổi bởi từng phép chuẩn
hoá": [02_steps.md mục 4](02_steps.md).

## 5. Step 5 - Transform

| Khoá               | Mặc định     | Ý nghĩa                   |
| ------------------ | ------------ | ------------------------- |
| `transform.format` | `multi_head` | định dạng dữ liệu xuất ra |

Pipeline **chỉ xuất một dạng dữ liệu**; dạng JSONL cho model sinh (Qwen3 / ViTASA)
được sinh khi cần từ chính bảng đó (`src/preprocessing/loader.py`). Bảng mã nhãn và
ví dụ: [05_output.md](05_output.md).

## 6. Dùng cấu hình để thực nghiệm

Đây là lý do chính khiến mọi phép đều có config. Ví dụ muốn biết
"chuẩn hoá ký tự lặp có giúp model không?":

```yaml
# Lần 1 - config A
normalize:
  repeated_chars: false
```

```bash
python run_pipeline.py      # -> data/processed/cosmetics-v0.1.0-<hash A>/
```

```yaml
# Lần 2 - config B
normalize:
  repeated_chars: true
```

```bash
python run_pipeline.py      # -> data/processed/cosmetics-v0.1.0-<hash B>/
```

Hai phiên bản dataset **cùng tồn tại**, không đè lên nhau:

```bash
python build_report.py --list          # xem tất cả phiên bản đã chạy
```

Rồi huấn luyện model trên hai phiên bản và so kết quả. Vì mỗi phiên bản có
`processing_log.json` ghi lại toàn bộ config, ta luôn chứng minh được sự khác biệt
đến từ phép biến đổi nào - đúng yêu cầu của một khóa luận.

> **Lưu ý thực hành:** tăng `version` trong `pipeline.yaml` (hoặc trong
> `configs/datasets/<name>/<version>.yaml`) khi thay đổi cấu hình quan trọng, để tên phiên bản
> dễ đọc hơn (mã hash vẫn luôn khác nhau kể cả khi bạn quên tăng). Không cần copy
> thư mục `data/processed/` bằng tay nữa.

Xem thêm: [04_experiments/03_training_eval.md](../04_experiments/03_training_eval.md) mục 3

- danh sách câu hỏi thực nghiệm ứng với từng config.
