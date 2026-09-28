# Bản mẫu để tạo thí nghiệm mới

Đây là **bản mẫu**, không phải thí nghiệm thật. Sao chép ra `experiments/<model>/<method>/<expNNN>/`
bằng lệnh (khuyến nghị, vì nó tự chọn số `expNNN` kế tiếp):

```bash
python scripts/new_experiment.py --model qwen3-4b-instruct-2507 --method prompt-cot --notes "CoT 2 ví dụ"
```

| Thư mục       | Dùng khi nào                                                                 |
| ------------- | ---------------------------------------------------------------------------- |
| `experiment/` | Mọi thí nghiệm: config, notebook, README của chính thí nghiệm                 |
| `prompt/`     | Thí nghiệm dùng model sinh (Qwen3...): `prompt.txt`, `system.txt`, `examples.txt` |

Model encoder (PhoBERT, ViSoBERT) **không dùng prompt**: chúng học từ dữ liệu, không hỏi bằng câu.

Ba file trong `templates/prompt/`:

| File           | Dùng khi                                                                     |
| -------------- | ---------------------------------------------------------------------------- |
| `prompt.txt`   | phần NGƯỜI DÙNG gửi model: `{aspects}`, `{label_guide}`, `{text}`, `{examples}`, `{system_prompt}` |
| `examples.txt` | khối ví dụ few-shot, khi prompt có ô nhớ `{examples}`                         |
| `system.txt`   | **system prompt riêng của thí nghiệm này** - bắt buộc khi `prompt.txt` dùng ô nhớ `{system_prompt}`; không viết câu hệ thống vào `prompt.txt` |

`system.txt` chỉ chứa đúng câu gửi cho model (không viết chú thích trong đó: cả file được gửi đi).
Thí nghiệm khai `system_prompt: system.txt` để dùng nó, và `prompt.txt` viết ô nhớ `{system_prompt}`.
Nhiều thí nghiệm dùng chung một câu hệ thống thì để file ở `configs/prompts/system/<tên>.txt` và trỏ
`system_prompt` vào đó - khi đó không cần `system.txt` trong thư mục thí nghiệm.

## Sau khi sao chép thì làm gì

1. Sửa `config.yaml`: `model`, `method`, `data.roles`, `prompt`, và `system_prompt` khi prompt dùng `{system_prompt}` (xem `experiment/README.md`).
2. Mở `notebook.ipynb`, chạy thử **trên máy cá nhân** cho tới khi trôi.
3. `python scripts/pin.py <model>/<method>/<expNNN>` để ghim bản code vào cell đầu.
4. Ghi lại file notebook vào git, đẩy lên nhánh `experiment`.

Từ bước 3 trở đi thì **không sửa** thư mục thí nghiệm nữa cho tới khi người nhận chạy xong
(`docs/06_plan/P5_notebook_pin.md`, mục rủi ro): sửa sau khi ghim nghĩa là kết quả chạy ra không
ứng với bản code đã ghim.
