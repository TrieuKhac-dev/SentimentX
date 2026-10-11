# cafebert/lora/exp020 - NỐI HAI TRỤC ĐANG DẪN: `lr 4e-4` (của `exp015`) x `lora.r 32` (của `exp013`)

**Hỏi:** hai thứ ĐANG dẫn đầu thuộc **hai trục khác nhau** và **chưa gặp nhau**: `exp015` dẫn nhờ
`lr 4e-4` (với `lora.r = 16`), còn `exp013` dẫn nhờ `lora.r = 32` (với `lr = 2e-4`). Ghép lại thì
**cộng tính** hay **triệt tiêu**?

**Khác `exp015` (cha):** đúng **MỘT khoá ĐO ĐƯỢC** - `lora.r: 32`. Giữ nguyên `lr: 0.0004`,
`head.trainable: true`, `loss: weighted_ce + inverse`, cùng seed 42, cùng 3 epoch.

**Đối chiếu tại thời điểm tạo** (cơ sở `paper`, split `test`, 1.623 review):

| Lượt | Acc macro | pos F1 | neg F1 (7) | neg F1 (5 n lớn) | neg micro |
| --- | ---: | ---: | ---: | ---: | ---: |
| `exp015` (cha, `lr 4e-4`, r = 16) | **98,35** | 98,93 | 81,23 | **94,78** | 94,94 |
| `exp013` (`r 32`, lr 2e-4) | 98,33 | 98,93 | 88,93 | 94,14 | **95,12** |
| công bố (đỉnh CB 1-shot) | 97,70 | 98,48 | 74,20 | 87,88 | 89,11 |

**Điều kiện gọi là THÀNH CÔNG:** hơn **cả** `Acc macro` **và** một chỉ số F1 lớp âm **> 0,7 điểm**
(biên nhiễu đã đo ±0,33…±0,67). Dưới mức đó ghi **ĐỒNG HẠNG**, không nói "tốt hơn".

**Dấu vết phải kiểm TRƯỚC khi đọc điểm:** `trainable_params` phải **tăng** so với `exp015` (r 16 → 32);
`read_rate.valid` phải `true` (`% đọc được` ≥ 95); luôn ghi kèm `paper.cells` (số ô).

**Đọc kèm:** `present_plan_batch12.md` NHÓM 1, mục 2 (luật đọc số) và mục 3 (bench cần đánh bại).

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
