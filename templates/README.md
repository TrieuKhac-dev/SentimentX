# Bản mẫu để tạo thí nghiệm mới

Đây là **bản mẫu**, không phải thí nghiệm thật. Sao chép ra `experiments/<model>/<method>/<expNNN>/`
bằng lệnh (khuyến nghị, vì nó tự chọn số `expNNN` kế tiếp):

```bash
python scripts/new_experiment.py --model qwen3-4b-instruct-2507 --method prompt-cot --title "CoT 2 ví dụ"
```

| Thư mục       | Dùng khi nào                                                                 |
| ------------- | ---------------------------------------------------------------------------- |
| `experiment/` | Mọi thí nghiệm: config, notebook, README của chính thí nghiệm                 |
| `prompt/`     | Thí nghiệm dùng model sinh (Qwen3...): câu chỉ dẫn, ví dụ few-shot, khối hệ thống |

Model encoder (PhoBERT, ViSoBERT) **không dùng prompt**: chúng học từ dữ liệu, không hỏi bằng câu.

Ba file trong `templates/prompt/`:

| File           | Dùng khi                                                                     |
| -------------- | ---------------------------------------------------------------------------- |
| `prompt.txt`   | câu chỉ dẫn, có các ô nhớ `{aspects}`, `{label_guide}`, `{text}`              |
| `examples.txt` | khối ví dụ few-shot, khi prompt có ô nhớ `{examples}`                         |
| `system.txt`   | khối chỉ dẫn hệ thống, khi muốn NHIỀU prompt dùng chung một câu hệ thống      |

`system.txt` chỉ chứa đúng câu gửi cho model (không viết chú thích trong đó: cả file được gửi đi).
Prompt dùng nó thì viết ô nhớ `{system_prompt}` và khai khoá `system_prompt` trong `config.yaml`.

## Sau khi sao chép thì làm gì

1. Sửa `config.yaml`: `model`, `method`, `data.roles`, `prompt` (xem `experiment/README.md`).
2. Mở `notebook.ipynb`, chạy thử **trên máy cá nhân** cho tới khi trôi.
3. `python scripts/pin.py <model>/<method>/<expNNN>` để ghim bản code vào cell đầu.
4. Ghi lại file notebook vào git, đẩy lên nhánh `experiment`.

Từ bước 3 trở đi thì **không sửa** thư mục thí nghiệm nữa cho tới khi người nhận chạy xong
(`docs/06_plan/P5_notebook_pin.md`, mục rủi ro): sửa sau khi ghim nghĩa là kết quả chạy ra không
ứng với bản code đã ghim.
