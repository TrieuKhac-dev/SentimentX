# cafebert/lora/exp003 - THƯỚC NHIỄU cho lượt gốc (chạy lại `exp001` với hạt giống khác)

**Hỏi:** Con số của `cafebert/lora/exp001` (acc TB 97,67 · F1 macro 0,886) đứng ở đâu giữa HAI lần chạy cùng cấu hình mà khác hạt giống? Tức là **biên nhiễu của đường encoder** là bao nhiêu điểm - con số còn thiếu ở §2b của `docs/04_experiments/08_experiment_rationale.md`, nơi các chênh lệch nhỏ của nhóm đầu phân loại chưa tách được khỏi nhiễu.

**Khác `exp001`:** đúng MỘT khoá ĐO ĐƯỢC - `decoding.seed: 7` (mặc định ở lớp dùng chung là 42, đúng bằng hạt giống của mọi lượt cũ). Ở ĐƯỜNG ENCODER (luôn chạy `greedy`), khoá này là **hạt giống HUẤN LUYỆN**: khởi tạo trọng số đầu phân loại, dropout, xáo trộn dữ liệu - xem khối "NGOẠI LỆ Ở ĐƯỜNG ENCODER" trong `configs/experiments/evaluation.yaml`. Mọi thứ khác y hệt `exp001`: `weighted_ce` + `class_weight: inverse`, cùng số epoch, cùng tham số LoRA, đầu phân loại **ĐÓNG BĂNG**.

**Bằng chứng "khác đúng MỘT thứ" - mã KHÔNG đổi:**

```
$ git diff --stat 59579e5 HEAD -- src/training src/experiments src/preprocessing src/labels src/core
(không in gì ⇒ RỖNG)
```

`59579e5` là commit của lượt `exp001`. Giữa hai commit, trong `src/` có ĐÚNG một file đổi là `src/evaluation/fusion.py`, nhưng file đó **không thuộc đường chạy encoder**: chỉ `scripts/ensemble.py`, `scripts/fit_thresholds.py`, `scripts/fuse.py`, `scripts/vote.py` nhập nó - không file nào trong `src/experiments`/`src/training` nhập.

**Kết quả:** `results/<hash8>/`. Đây là **THƯỚC NHIỄU, KHÔNG phải lượt lấy điểm cao**: đọc nó để biết chênh lệch nào ở nhóm đầu phân loại là ĐO ĐƯỢC, chênh lệch nào chỉ là nhiễu. Kiểm DẤU VẾT trước khi đọc số: `trainable_params` phải BẰNG `exp001` (**7.110.656**) - lượt này vẫn ĐÓNG BĂNG đầu phân loại; nếu thấy 7.132.181 thì đã lẫn sang cơ chế của `exp002`/`exp004`. Không cần tài nguyên ngoài git (`segmenter: none`).

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
