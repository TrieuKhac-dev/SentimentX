# exp007 (PhoBERT-base-v2) - Đầu phân loại HỌC + khía cạnh vào ĐẦU VÀO (`aspect_marker`)

**Hỏi:** `exp006` (`head.aspect_marker: true` nhưng đầu phân loại **ĐÓNG BĂNG**) đã **SỤP**: acc macro
**51,60** so cha 93,28, detection F1 0,891 → **0,495**, precision "có nhắc" 0,825 → 0,356. Câu hỏi còn treo:
cho đầu phân loại **HỌC** thì cơ chế này có cứu được không?

**Khác `phobert-base-v2/lora/exp005`:** đúng MỘT khoá - `head.aspect_marker: true`.

**KẾT QUẢ (đọc 07/10/2026): KHÔNG cứu được - và đó là điều đáng giá nhất lượt này mang lại.** acc TB
**50,51** (`all`) · 78,55 (`paper`) so cha `exp005` (đầu CŨNG học) **97,25** ⇒ **−46,74**; detection F1 macro
0,959 → **0,489**; F1 âm macro 0,719 → **0,236**. Hai lượt marker (đóng băng 51,60 và học 50,51) cho kết quả
**xấp xỉ nhau** ⇒ lỗi là của **CẤU TRÚC**, KHÔNG phải của việc đầu có học: cách cài đặt dùng **CHUNG một lớp**
(`logit = W[:,:H]·h + W[:,H:]·e_khía_cạnh + b`) nên khía cạnh chỉ vào được như một **HẰNG SỐ riêng** - nó
không đổi được CÁCH ánh xạ review → sắc thái, mà ABSA cần đúng thứ đó. **Khoá `head.aspect_marker` đã bị BỎ**
(giữ mặc định `false`), nên đọc lượt này như bằng chứng cho KẾT LUẬN, không phải như lượt để chọn tham số.

**Kết quả:** `results/3e52a2a3/`. Cần VnCoreNLP (xem `requires_extra`).

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
