# present_report_v4 - Đối chiếu dự án với công bố tham chiếu (10 lượt dẫn đầu: 9 encoder + 1 LLM)

> ⚠️ **BẢN CŨ - đã được thay bởi [`present_report_v5.md`](present_report_v5.md).** File này **chỉ còn giữ các con số
> ĐẶC TRƯNG của bản `v4`** để làm dấu vết phiên bản; **KHÔNG dùng số ở đây để báo cáo.**

> ⛔ **GHI CHÚ 16/10/2026 - HAI LƯỢT ĐÃ BỊ THAY.** `cafebert/lora/exp073` (`227bfb70`) và `cafebert/lora/exp027`
> (`43e40f61`) đã được **chạy lại liền mạch**. Lý do: bản ghi trong file này (và trong `v3`/`v5`) là lượt **bị ngắt
> giữa phiên rồi chạy tiếp từ checkpoint**, nên `training_history.csv` chỉ còn các epoch cuối ⇒ không kiểm được hội tụ.
> Số cũ → số mới: **`exp073` 98,52 → 98,31**; **`exp027` 98,37 → 98,56**. Hai bản cũ **bị bỏ**.
> Bảng đang dùng: [`present_report_v6.md`](present_report_v6.md).

> **Vì sao file này là bản RÚT GỌN:** `present_report_v4.md` **chưa từng được commit vào git** (git chỉ thấy
> `present_report_v3.md` là bản được theo dõi), và **toàn văn của nó đã bị bản `v5` ghi đè** khi dựng lại bảng theo
> cách đếm seed đã sửa ⇒ **toàn văn `v4` không khôi phục được từ git**. Các số dưới đây lấy từ chính lần dựng `v4`
> (đã đối chiếu `experiments/**/results/<hash8>/metrics.json` của 10 lượt) nên vẫn là **bản ghi trung thực** của bản đó.

## 1. Bản `v4` là bản nào

| Hạng mục | `present_report_v4.md` |
| --- | --- |
| Bảng | 10 lượt dẫn đầu trong **79 lượt đủ điều kiện** ⇒ **75 kết quả phân biệt** (**51** encoder + 24 LLM) |
| 9 lượt encoder | `exp073` 98,52 · `exp021` 98,41 · `exp027` 98,37 · `exp015` 98,35 · `exp020` 98,34 · `exp013` 98,33 · `exp017` 98,06 · `exp008` 98,03 · `exp019` 97,99 |
| Lượt LLM | `qwen3-4b-instruct-2507/prompt-cot/exp009` **97,77** |
| Accuracy macro (9 cột encoder) | **97,99 … 98,52** (Δ so mốc 97,70 = **+0,29 … +0,82**) |
| `neg F1 macro (5 khía cạnh n lớn)` | **92,96 … 94,90** (Δ so mốc 87,88 = **+5,08 … +7,02**) |
| `neg P macro (5 khía cạnh n lớn)` | **90,16 … 94,72** |
| 42 ô P/R/F1 so với công bố | **14 thua hết · 17 thắng hết · 11 hỗn hợp** |
| Chẩn đoán hội tụ | **7/9 UNDERFIT · 2/9 không kết luận được · 0 overfit** |
| Ba nhánh phụ của bảng | `E7` (`focal`) · `E8` (`segmenter: vncorenlp`) · `E9` (`adapter: dora`) |
| Tier B | **9 lượt** - gồm `exp055` (`best_metric` + **khai** `decoding.seed: 42`) |

## 2. Vì sao `v5` thay `v4`

- `v4` đếm **điều kiện 10/11** theo **SỰ CÓ MẶT** của khoá `decoding.seed`, nên xếp **OAN** `cafebert/lora/exp055`
  (98,12) vào **Tier B** - dù nó **khai đúng giá trị mặc định 42**, tức **không phải lượt dò nhiễu**.
- Đếm lại theo **GIÁ TRỊ HIỆU LỰC** (`decoding.seed` vắng mặt = **42**, `experiment_run.SEED_DEFAULT`): Tier B còn
  **8 lượt**, **80 lượt đủ điều kiện**, **76 kết quả phân biệt** (**52** encoder + 24 LLM) ⇒ `exp055` **vào bảng ở
  hạng 7** và `exp019` xuống **hạng 10 của pool** (bị **điều kiện 9** thay bằng cột LLM).
- Vì vậy **điểm sàn của bảng tăng**: Accuracy **97,99 → 98,03**, `neg F1 macro (5n)` **92,96 → 93,66**,
  `neg P macro (5n)` **90,16 → 90,40**. **Mọi kết luận khác KHÔNG đổi** (14 thua hết · 17 thắng hết · 11 hỗn hợp;
  7/9 UNDERFIT · 0 overfit).

> → Bảng đang dùng: **[`present_report_v5.md`](present_report_v5.md)**. Bản trước đó nữa:
> [`present_report_v3.md`](present_report_v3.md).
