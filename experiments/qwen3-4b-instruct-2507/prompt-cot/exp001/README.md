# exp001 - Qwen3-4B-Instruct-2507 bằng prompt CoT, chấm trên val

## Thí nghiệm này hỏi câu gì

Model 4B đã được tinh chỉnh theo chỉ dẫn, đọc một review mỹ phẩm tiếng Việt và tự trả về nhãn cho
từng khía cạnh (7 khía cạnh, nhãn -1/0/1): **nếu đưa chuỗi suy luận rồi mới đòi JSON kết quả thì
chấm được bao nhiêu, và đọc ra được bao nhiêu phần trăm?**

Đây là thí nghiệm ĐẦU TIÊN và là mốc so sánh cho các thí nghiệm sau. Câu hỏi phụ đã trả lời trước
khi chạy: prompt này tốn 861 token/review nên `preprocess.max_length` phải là 1280 (xem
`configs/models/qwen3-4b-instruct-2507.yaml`).

## Khác gì những lần chạy trước

Không có lần chạy trước (`parent: null`). Ba lựa chọn của thí nghiệm này:

| Lựa chọn | Giá trị | Vì sao |
| --- | --- | --- |
| Prompt | `configs/prompts/absa_cot_v1.txt` (CoT + 2 ví dụ) | Phương pháp là `prompt-cot`; thêm ví dụ là biến rẻ nhất của hướng này, đổi số ví dụ mà KHÔNG phải sửa prompt |
| Split chấm | `val` (1.524 review) | `val` là tập để LỰA CHỌN; test chỉ dùng cho con số cuối cùng |
| Số mẫu | `n: 200` | Đủ để phân biệt hai prompt, chạy gọn trên GPU 6 GB trong một buổi |
| Cách sinh | `greedy` (mặc định) | Tất định nên tái lập được; lấy mẫu chỉ dùng khi muốn đo dao động |

## Kết quả nằm ở đâu

`results/<mã phiên bản dữ liệu>/<hậu tố cấu hình>/`, mỗi lần chạy một thư mục:

| File | Nội dung |
| --- | --- |
| `run.log` | từng bước đã chạy, kèm lí do khi dừng; tìm `[RUN] mode=RESUME` khi chạy tiếp |
| `run_meta.json` | bản ghi lần chạy: code, config, dữ liệu, các attempt |
| `metrics.json` | chỉ số, kèm cách chấm (`label_space`, `neutral_policy`, số ô neutral bị loại) |
| `metrics.csv` | bảng dài `aspect, sentiment, metric, value` để so với các lần chạy khác |
| `mispredictions.csv` | chỉ các ô đoán sai |
| `predictions/part_*.jsonl` | kết quả ghi dần, để chạy tiếp khi bị ngắt |

Không chép số liệu vào README này: số liệu nằm trong `metrics.json`, bản tổng hợp do
`scripts/collect_reports.py` sinh.

## Chạy lại

Bấm **Run all** trong `notebook.ipynb` (nó tự kéo đúng commit đã ghim rồi kiểm trước khi chạy), hoặc
trên dòng lệnh:

```
python run_qwen_eval.py --experiment qwen3-4b-instruct-2507/prompt-cot/exp001
```

Sau khi commit đã ghim: **KHÔNG sửa** `config.yaml`, `prompt`/`examples` hay notebook của thí nghiệm
này nữa, cho tới khi người nhận chạy xong. Cần thử cách khác thì tạo thí nghiệm mới
(`python scripts/new_experiment.py`) và đặt `parent` trỏ về đây để còn đối chiếu.

