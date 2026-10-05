# phobert-large/lora/exp002 - đầu phân loại HỌC cùng adapter (không đóng băng)

**Hỏi:** Đóng băng đầu phân loại hay không thì khác gì nhau? Ở các lượt LoRA đã chạy, `peft` đóng băng MỌI tham số không phải adapter nên đầu phân loại chỉ là một phép chiếu ngẫu nhiên CỐ ĐỊNH: `head.pt` giống nhau TỪNG BYTE giữa các checkpoint và cả giữa hai model khác nhau - đó là SỐ ĐO, không phải suy đoán.

**Khác `exp001`:** đúng MỘT khoá ĐO ĐƯỢC - `head.trainable: true` (mặc định ở lớp dùng chung là `false`). Mọi thứ khác y hệt `exp001`: `weighted_ce` + `class_weight: inverse`, cùng hạt giống, cùng số epoch, cùng tham số LoRA.

**Thêm so với `exp001` (KHÔNG phải biến so sánh):** `requires_extra: [data/models/vncorenlp]`. `exp001` THIẾU mục này dù model là PhoBERT (`segmenter: vncorenlp`), nên notebook của nó không kiểm VnCoreNLP trước khi chạy - xem ghi chú trong `config.yaml`.

**Kết quả:** `results/<hash8>/`. Kiểm DẤU VẾT trước khi đọc số: `trainable_params` trong `metrics.json` phải LỚN HƠN `exp001` đúng **21.525** (= 7 khía cạnh × (1024 ẩn × 3 mã + 3) - PhoBERT-large rộng 1024). Đọc theo CẶP chỉ số - F1 lớp âm + macro-F1 + số ô - KHÔNG chỉ accuracy; đây cũng là lượt cho biết model LỚN hơn có đáng chi phí không. Mỗi nhánh mới có MỘT lượt nên chưa có thước nhiễu: chênh lệch nhỏ là chưa kết luận được gì. Cần VnCoreNLP (xem `requires_extra`).

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
