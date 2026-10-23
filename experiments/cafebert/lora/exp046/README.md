# cafebert/lora/exp046 - ĐO ĐỘ VỮNG: chạy lại `cafebert/lora/exp028` với `decoding.seed: 7`

**Hỏi:** `cafebert/lora/exp028` được chọn ở bước nào đó của đường `val`; nếu ĐỔI HẠT GIỐNG HUẤN LUYỆN thì kết quả còn
giữ được không? Đây là phép đo **biên nhiễu** cho chính cấu hình đang dẫn đầu.

**Khác `cafebert/lora/exp028` (cha):** đúng **MỘT khoá ĐO ĐƯỢC** - `decoding.seed` (mặc định 42 -> **7**). Ở ĐƯỜNG
ENCODER khoá này là **hạt giống HUẤN LUYỆN** (khởi tạo đầu phân loại, dropout, xáo trộn dữ liệu).

**Cách đọc:** biên nhiễu đường encoder đã đo là **+-0,33...+-0,67** (làm việc +-0,7). Các lượt dẫn đầu chỉ hơn
nhau **0,06 điểm**, nên **ba lần rút thăm** cho cùng một cấu hình mới biến "cụm đồng hạng" thành kết luận.
Chênh lệch dưới 0,7 ghi **ĐỒNG HẠNG**, không nói "tốt hơn".

**Dấu vết:** `run_meta.json` và `metrics.json` ghi `generation.seed: null` (đường encoder luôn `greedy`, không
rút thăm lúc suy luận) - ĐỪNG đọc nhầm là khoá bị bỏ qua; hạt giống nằm ở bước HUẤN LUYỆN.

**Đọc kèm:** `docs/06_plan/archive/batches/present_plan_batch12.md` NHÓM 6 và mục 10.

**Áp cho:** exp028 (giu ky luc neg F1 n lon 94,84).

---

# Một thí nghiệm gồm những gì

```
experiments/<model_id>/<method>/<expNNN>/
+-- config.yaml      BẮT BUỘC: phần riêng của thí nghiệm này (lớp cuối khi hợp nhất config)
+-- notebook.ipynb   notebook để chạy: mở ra và bấm Run all
+-- README.md        giải thích thí nghiệm này hỏi gì, để người đọc sau không phải đoán
+-- prompt.txt       prompt riêng (model sinh); có thể trỏ vào `configs/prompts/` thay vì để đây
+-- examples.txt     khối ví dụ few-shot, nếu prompt dùng ô nhớ {examples}
\\-- results/         KẾT QUẢ sinh ra khi chạy - không sửa tay, không commit file nặng
```

Kết quả nằm ở `results/<hash8>/`, mỗi lần chạy một thư mục (`<hash8>` = 8 ký tự đầu của mã băm danh
tính: cấu hình + prompt + ví dụ + dữ liệu + **commit đã ghim**; cùng phép đo trên Colab và trên máy cá
nhân ra cùng tên):
`run.log` (luôn có), `run_meta.json`, `metrics.json`, `metrics.csv`, `predictions/part_*.jsonl`
(ghi dần, để chạy tiếp khi bị ngắt), `predictions.csv` khi đã xong. Xem
`docs/00_workflow/01_flow.md` và `docs/04_experiments/05_predictions.md`.

## `config.yaml` - sửa gì

| Khoá             | Ghi gì                                                                                       |
| ---------------- | -------------------------------------------------------------------------------------------- |
| `model`          | `model_id`, phải trùng tên file `configs/models/<model_id>.yaml`                              |
| `method`         | tên phương pháp, cũng là tên thư mục cha                                                      |
| `data.dataset`   | **một** dataset duy nhất; khai danh sách là lỗi                                               |
| `data.version`   | phiên bản dataset, trỏ tới `configs/datasets/<name>/<version>.yaml`                           |
| `data.roles`     | mỗi vai dùng split nào; `eval` luôn cần, `train`/`val` khi huấn luyện. Trỏ vào `train` bị chặn |
| `prompt`         | đường dẫn file prompt: tính từ thư mục thí nghiệm trước, rồi tới gốc repo                     |
| `examples`       | khối ví dụ few-shot, nếu prompt có ô nhớ `{examples}`                                         |
| `requires_extra` | đường dẫn notebook phải kiểm thêm (model đã tải sẵn, tài nguyên ngoài repo...)                |

## `README.md` của thí nghiệm - ghi gì

Ba câu là đủ, miễn là trả lời được: thí nghiệm này **hỏi câu gì**, **khác thí nghiệm trước ở chỗ
nào**, và **kết quả nằm ở đâu**. Không chép số liệu vào đây: số liệu nằm trong `metrics.json`,
bản tổng hợp do `scripts/collect_reports.py` sinh.

## Notebook - chạy thế nào

Bấm **Run all**. Notebook tự làm phần khó: kéo ĐÚNG bản code đã ghim vào cell đầu (nên chạy trên
Colab hay máy cá nhân đều ra cùng kết quả), kiểm trước khi chạy, rồi chạy và chấm điểm. Nếu có gì
chưa đúng, nó **dừng và in ra danh sách việc phải sửa** thay vì chạy nửa chừng rồi hỏng.
