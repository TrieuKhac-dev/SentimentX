# exp005 (Qwen3-0.6B) - nhánh BẬT suy nghĩ, mức 1 ví dụ

**Hỏi:** lượt tắt suy nghĩ ở đúng mức này (`prompt-cot/exp002`) chỉ đọc được **21,63%** ô - bật suy nghĩ có
làm model in ra khối JSON đủ để chấm không?

**Khác `exp002`:** đúng MỘT cơ chế, hai khoá đi liền nhau - `preprocess.enable_thinking: true` và trần
`decoding.max_new_tokens: 1985` (trần ĐO từ lượt DÒ `exp004`, p99 1.323 × 1,5). Prompt, ví dụ, system,
split, `batch_size` giữ nguyên.

**Kết quả:** `results/<hash8>/`. Đọc **`% đọc được`** (cửa 95%) và **tỉ lệ chạm trần** TRƯỚC khi đọc điểm:
lượt DÒ đọc được 98,33%, nên đây là lượt đọc được để SO với `exp002`.

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
