# Luồng Data Pipeline (xử lý dữ liệu)

## 1. Pipeline để làm gì

Pipeline trả lời đúng **một** câu hỏi:

> **"Ta sẽ làm gì với dữ liệu?"**

Nó **thực sự biến đổi** dữ liệu: loại bản ghi lỗi, xử lý trùng lặp, chuẩn hoá văn
bản, chuyển sang dạng model dùng được, rồi ghi ra `data/processed/`.

Pipeline **bắt đầu từ raw data**, không bắt đầu từ EDA - xem
[02_eda/01_flow.md mục 7](../02_eda/01_flow.md).

## 2. Luồng tổng quát: bảy bước

```
RAW DATA (data/raw/<tên>/data_train.csv, data_val.csv, data_test.csv)
   |
   -> 1. LOAD           đọc 3 file split, bỏ cột `drop_columns`, đổi tên cột văn bản -> `text`
   -> 2. VALIDATE       kiểm tra schema + nội dung (CHỈ ghi nhận, không sửa)
   -> 3. CLEAN          loại nhiễu, trùng lặp, cách ly xung đột nhãn, xử lý rò rỉ
   -> 4. NORMALIZE      chuẩn hoá văn bản (từng phép bật/tắt theo config)
   -> 5. TRANSFORM      chuyển sang dạng ABSA: bảng multi_head + bản ghi ABSA
   -> 6. FINAL VALIDATE cổng chất lượng: nhãn không đổi, văn bản không bị viết lại
   -> 7. EXPORT         ghi ra đĩa + log truy vết
PROCESSED DATA (data/processed/<mã>/)
```

Thứ tự này **đúng bằng** `src/registry.py::pipeline_steps()`. Trên báo cáo, tiêu đề
mỗi mục là **"Step n - ..."** (Step 1 ... Step 7) cho khớp với thứ tự đó; số `n` không
phải số hiệu phiên bản.

| Bước              | File                             | Làm gì                                                                                          | Chi tiết                      |
| ----------------- | -------------------------------- | ----------------------------------------------------------------------------------------------- | ----------------------------- |
| 1. Load           | `src/pipeline/load.py`           | Nạp dữ liệu qua loader (CSV đọc với `utf-8-sig`), bỏ cột thừa, đổi tên cột văn bản thành `text` | [02_steps.md mục 1](02_steps.md) |
| 2. Validate       | `src/pipeline/validate.py`       | Kiểm tra cột thiếu/thừa, review rỗng, nhãn lạ. **Ghi nhận, không sửa**                          | [02_steps.md mục 2](02_steps.md) |
| 3. Clean          | `src/pipeline/clean.py`          | Loại nhiễu & trùng lặp, cách ly xung đột nhãn, xử lý rò rỉ dữ liệu                              | [02_steps.md mục 3](02_steps.md) |
| 4. Normalize      | `src/pipeline/normalize.py`      | Unicode, khoảng trắng, ký tự lặp (tuỳ chọn). **Không thay teencode**                            | [02_steps.md mục 4](02_steps.md) |
| 5. Transform      | `src/pipeline/transform.py`      | Bảng multi_head (mã nhãn 0/1/2/3) + bản ghi ABSA                                                | [02_steps.md mục 5](02_steps.md) |
| 6. Final Validate | `src/pipeline/final_validate.py` | Schema, text rỗng, nhãn hợp lệ, **nhãn không bị đổi**, số dòng khớp                             | [02_steps.md mục 6](02_steps.md) |
| 7. Export         | `src/pipeline/export.py`         | Ghi bảng multi_head + `label_map.json` + log truy vết                                           | [05_output.md](05_output.md)  |

## 3. Cấu hình đang bật / tắt

Mọi phép biến đổi đều **bật / tắt được** trong `configs/pipeline/v0.1.0.yaml`. Bảng dưới
đây là trạng thái **đang chạy trong repo** (ý nghĩa từng khoá và cách đổi để thực
nghiệm: [03_config.md](03_config.md)):

| Bước | Khoá                                  | Đang chạy      | Nghĩa ngắn                                                                  |
| ---- | ------------------------------------- | -------------- | --------------------------------------------------------------------------- |
| 2    | `steps.validate.check_schema`               | **Bật**        | kiểm tra đủ cột, đúng tên cột                                               |
| 2    | `steps.validate.check_content`              | **Bật**        | kiểm tra review rỗng, nhãn lạ                                               |
| 3    | `steps.clean.remove_empty`                  | **Bật**        | loại review rỗng                                                            |
| 3    | `steps.clean.remove_gibberish`              | **Bật**        | loại chuỗi ký tự vô nghĩa                                                   |
| 3    | `steps.clean.remove_ads`                    | **Bật**        | loại quảng cáo / tin nhắn nhà mạng                                          |
| 3    | `steps.clean.remove_code`                   | **Bật**        | loại dòng chứa mã HTML / SQL / code (rất nhỏ: 1 dòng)                       |
| 3    | `steps.clean.deduplicate.exact`             | **Bật**        | loại trùng lặp chính xác                                                    |
| 3    | `steps.clean.deduplicate.normalized`        | **Bật**        | loại trùng theo **khoá so trùng** (không phải bước Normalize)               |
| 3    | `steps.clean.deduplicate.ignore_diacritics` | **Tắt**        | khoá so trùng **giữ dấu** tiếng Việt (`son dep` khác `son đẹp`)                |
| 3    | `steps.clean.deduplicate.scope`             | `within_split` | so trùng trong từng split (`global` là phương án thực nghiệm)               |
| 3    | `steps.clean.deduplicate.conflict_policy`   | `quarantine`   | cùng văn bản nhưng nhãn khác nhau -> cách ly, không tự chọn                  |
| 3    | `steps.clean.leakage.remove_eval_overlap`   | **Bật**        | loại khỏi val/test những review đã có trong train                           |
| 4    | `steps.normalize.lowercase`                 | **Tắt**        | giữ hoa/thường (tokenizer subword phân biệt, và chữ hoa có thể là tín hiệu) |
| 4    | `steps.normalize.unicode`                   | **Bật**        | NFC                                                                         |
| 4    | `steps.normalize.whitespace`                | **Bật**        | chuẩn hoá khoảng trắng / xuống dòng                                         |
| 4    | `steps.normalize.repeated_chars`            | **Tắt**        | **không** rút gọn `đẹppppp` -> `đẹpp` (ký tự lặp mang cảm xúc)               |
| 4    | thresholds.repeated_chars_max``        | `2`            | chỉ có tác dụng khi `repeated_chars: true`                                  |
| 5    | `steps.transform.format`                    | `multi_head`   | dạng dữ liệu đầu ra duy nhất                                                |

Tóm lại, pipeline hiện chỉ **sửa văn bản** bằng bốn phép - `lowercase`, `unicode`,
`whitespace`, `repeated_chars` (ba phép cuối bật theo config) - và **hai phép cuối
đang tắt**. Ngoài bốn phép đó không ký tự nào bị đổi; điều này được **chứng minh
bằng số liệu** ở Step 6 ([04_invariants.md](04_invariants.md)).

Hai bảng chứng minh cấu hình ngay trên báo cáo (không phải suy đoán):

- bảng **"Thiết lập Clean đang áp dụng"** (Step 3) và bảng **"Thiết lập Normalize
  đang áp dụng"** (Step 4) - in đúng trạng thái Bật/Tắt của từng khoá;
- bảng **"Cấu hình đã dùng cho lần chạy này"** (cuối báo cáo) - in toàn bộ
  `configs/pipeline/v0.1.0.yaml`, và config nguyên vẹn cũng được ghi vào
  `processing_log.json` của chính phiên bản dữ liệu đó.

## 4. Con số cộng lại được

Mỗi dòng trước Clean kết thúc ở đúng một trong ba nhóm - **giữ lại (sau Clean)**,
**bị loại**, **bị cách ly** - nên biểu đồ xếp chồng "sau Clean (giữ lại) / bị loại /
cách ly" cộng lại bằng số dòng trước Clean:

```
số dòng trước Clean = số dòng sau Clean + số dòng bị loại + số dòng bị cách ly
            16227 = 15344 + 840 + 43
```

Con số trên là của dataset `cosmetics` (3 split gộp lại). Nếu muốn đối chiếu với
EDA: EDA 03 đo trên **dữ liệu gốc** nên số của nó lớn hơn một chút (ví dụ 91 dòng
val/test trùng train ở EDA so với 84 dòng bị loại do rò rỉ ở đây, vì 7 dòng kia đã
bị loại từ bước xoá nhiễu chạy trước) - xem
[02_metrics.md mục 12](../02_eda/02_metrics.md).

## 5. Chạy và kết quả

Pipeline cũng tách thành hai việc: **tính** và **vẽ**.

```bash
# 1) Xử lý dữ liệu và ghi dataset + file kết quả
python run_pipeline.py --dataset cosmetics

# 2) Vẽ báo cáo từ số liệu đã ghi
python build_report.py --phase pipeline --dataset cosmetics
```

Kết quả:

| File                                                  | Nội dung                           |
| ----------------------------------------------------- | ---------------------------------- |
| `data/processed/<mã>/pipeline/report.html`            | **báo cáo duy nhất cho người đọc** |
| `data/processed/<mã>/train.csv` ...           | dữ liệu đã xử lý                   |
| `data/processed/<mã>/label_map.json`                  | danh sách khía cạnh + mã nhãn      |
| `data/processed/<mã>/processing_log.json`             | config + số liệu để truy vết       |
| `data/processed/manifest.json`                        | mục lục mọi phiên bản đã chạy      |
| `data/processed/<mã>/pipeline/removed_records.csv`    | danh sách dòng bị loại             |
| `data/processed/<mã>/pipeline/quarantine_records.csv` | danh sách dòng bị cách ly          |

`<mã>` là mã phiên bản (ví dụ `cosmetics-v0.1.0-b37ecfce`), được tính từ nội dung
config và nội dung dữ liệu gốc. **Mỗi lần đổi config hoặc đổi dữ liệu sẽ ra một
thư mục mới, nên kết quả cũ không bao giờ bị ghi đè.**

Các lệnh phụ trợ:

```bash
python build_report.py --list                            # xem mọi phiên bản đã chạy
python build_report.py --phase pipeline --no-open        # vẽ nhưng không mở trình duyệt
```

**Mã thoát (exit code) của ba entrypoint** - dùng được trong script:

| Mã  | Nghĩa                                                                            |
| --- | -------------------------------------------------------------------------------- |
| `0` | chạy xong                                                                        |
| `1` | không có gì để vẽ (chưa chạy nhóm việc đó, hoặc phiên bản không có file kết quả) |
| `2` | dùng sai: **tên dataset không tồn tại** / không có file kết quả nào để vẽ        |

Gõ sai tên dataset (ví dụ `--dataset consmetics`) sẽ dừng **ngay** với một dòng
`LỖI: ...` kèm gợi ý tên gần đúng, thay vì chạy tiếp rồi báo nhầm là "chưa có file kết
quả". Chi tiết cách thêm dataset mới: [01_dataset/03_new_dataset.md](../01_dataset/03_new_dataset.md).

## 6. Phân biệt ba loại "kiểm tra"

Đây là chỗ rất dễ nhầm:

| Loại                        | Ở đâu                  | Mục đích                                    |
| --------------------------- | ---------------------- | ------------------------------------------- |
| **EDA**                     | Nhóm riêng, `src/eda/` | Hiểu dữ liệu: "Có bao nhiêu dòng trùng?"    |
| **Pipeline Validate**       | Bước 2                 | Dữ liệu có thoả điều kiện để đi tiếp không? |
| **Pipeline Final Validate** | Bước 6                 | Dữ liệu đầu ra có hợp lệ, có bị hỏng không? |

`Final Validate` **không phải EDA lần hai**. Nó là **cổng chất lượng**: chỉ trả lời
ĐẠT / LỖI, không phân tích, không vẽ biểu đồ.

## 7. Điều pipeline KHÔNG làm

Ba điều dưới đây không phải "chưa làm" mà là **quyết định thiết kế**, và đều được
chứng minh bằng số liệu ở Step 6 ([04_invariants.md](04_invariants.md)):

- **không viết lại teencode** - không có config nào cho việc này trong
  `configs/pipeline/v0.1.0.yaml`; việc nhận diện teencode chỉ để ĐO (EDA 03);
- **không bỏ dấu tiếng Việt**, kể cả trong khoá so trùng
  (`steps.clean.deduplicate.ignore_diacritics: false`);
- **không chạm vào cột nhãn** - chứng minh bằng dấu vân tay nhãn trước/sau bước
  Normalize.

---

Xem tiếp: [02_steps.md](02_steps.md) - chi tiết từng bước;
[03_config.md](03_config.md) - ý nghĩa từng khoá cấu hình.
