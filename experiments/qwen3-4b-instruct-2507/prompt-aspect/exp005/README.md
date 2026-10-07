# exp005 (Qwen3-4B-Instruct-2507) - MỘT TẦNG của bản GỘP HAI TẦNG: khía cạnh `shipping`

**Hỏi:** nếu chỉ hỏi model MỘT khía cạnh, với cặp prompt/khối hệ thống viết riêng cho khía cạnh đó, thì sắc
thái của khía cạnh ấy có tốt hơn lượt hỏi cả 7 khía cạnh không?

**Vì sao lượt này tồn tại:** nó là MỘT TẦNG của bản gộp hai tầng (`scripts/fuse_aspect.py`): lượt ENCODER
giữ khung ô (phát hiện khía cạnh là điểm mạnh đã đo của nó), còn sắc thái khía cạnh `shipping` lấy từ lượt
này. **Đừng đọc điểm của lượt này như một lượt so điểm** - tập ô của nó khác hẳn bài 7 khía cạnh (chỉ một
khía cạnh), nên nó KHÔNG vào bảng cơ sở `paper` (tiền lệ: `prompt-cot/exp016`).

**Khác `prompt-cot/exp003`:** ba thứ - cặp prompt/khối hệ thống viết riêng cho một khía cạnh,
`aspects: [shipping]`, và không có khối ví dụ. Đây là khía cạnh bị chê nhiều thứ hai (31% ô âm), và dễ lẫn
với `packing` (bao bì) - khối hệ thống đã nói rõ cách tách.

**Kết quả:** `results/<hash8>/`; đọc bằng số ô + F1 lớp âm của khía cạnh này, và đặt cạnh số của lượt encoder
trên cùng tập (`fuse_aspect_test.json` ghi `thành_viên`).

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
