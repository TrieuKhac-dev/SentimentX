# cafebert/lora/exp004 - THƯỚC NHIỄU cho vế ĐẦU PHÂN LOẠI HỌC (chạy lại `exp002` với hạt giống khác)

**Hỏi:** `cafebert/lora/exp002` (đầu phân loại HỌC) hơn `exp001` (đóng băng) **+0,21 điểm** (97,67 → 97,88). Chênh lệch đó có **nằm ngoài biên nhiễu** không? Lượt này là câu trả lời: chạy lại CHÍNH `exp002` với một hạt giống khác; chênh lệch giữa hai lượt ấy chính là biên nhiễu của cặp đó.

**Khác `exp002`:** đúng MỘT khoá ĐO ĐƯỢC - `decoding.seed: 7` (mặc định ở lớp dùng chung là 42). Ở ĐƯỜNG ENCODER (luôn chạy `greedy`), khoá này là **hạt giống HUẤN LUYỆN** - xem khối "NGOẠI LỆ Ở ĐƯỜNG ENCODER" trong `configs/experiments/evaluation.yaml`. Mọi thứ khác y hệt `exp002`: `head.trainable: true`, `weighted_ce` + `class_weight: inverse`, cùng số epoch, cùng tham số LoRA.

**Bằng chứng "khác đúng MỘT thứ" - mã KHÔNG đổi:**

```
$ git diff --stat 59579e5 HEAD -- src/training src/experiments src/preprocessing src/labels src/core
(không in gì ⇒ RỖNG)
```

`59579e5` là commit mà `exp001`/`exp002` đã chạy. Giữa hai commit, trong `src/` có ĐÚNG một file đổi là `src/evaluation/fusion.py`, nhưng file đó **không thuộc đường chạy encoder**: chỉ `scripts/ensemble.py`, `scripts/fit_thresholds.py`, `scripts/fuse.py`, `scripts/vote.py` nhập nó - không file nào trong `src/experiments`/`src/training` nhập.

**Thêm so với `exp001` (KHÔNG phải biến so sánh):** `head.trainable: true` được GIỮ NGUYÊN như `exp002` - nhờ vậy phép so `exp002` ↔ `exp004` chỉ có MỘT biến.

**Kết quả:** `results/<hash8>/`. Đây là **THƯỚC NHIỄU, KHÔNG phải lượt lấy điểm cao**. Kiểm DẤU VẾT trước khi đọc số: `trainable_params` phải BẰNG `exp002` (**7.132.181** = 7.110.656 + 21.525, tức CafeBERT rộng 1.024 ẩn); nếu thấy 7.110.656 thì đã lẫn sang cơ chế đóng băng. Không cần tài nguyên ngoài git (`segmenter: none`).

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
