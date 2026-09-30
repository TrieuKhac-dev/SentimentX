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

Notebook gồm những ô nào, sửa một ô thì phải làm gì, và vì sao notebook của thí nghiệm đã chạy
không dựng lại theo bản mẫu: `docs/00_workflow/10_template_notebook.md`.

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

## Sửa bản mẫu

Sửa `templates/experiment/` là việc **cho thí nghiệm MỚI**. Notebook của một thí nghiệm đã chạy là BẢN GHI
của lượt đó, không phải bản sao của bản mẫu - nên sửa bản mẫu KHÔNG bắt 12 notebook đang có phải cập
nhật theo. Quy tắc thêm/sửa/xoá một ô, thứ tự các ô, và quy trình khi cần cập nhật CẢ BỘ notebook (việc
một lần, bằng script rồi ghim lại cùng lượt):
**`docs/00_workflow/10_template_notebook.md`**.

Hai điều dễ sai khi sửa bản mẫu:

- Ô nào cũng phải ở trong **khối bảo vệ** `end_session_on_error()` (ô CHẠY là ngoại lệ có lý do), nếu
  không thì một ô lỗi sẽ để phiên Colab sống tiếp và vẫn tính vào hạn mức GPU.
- Ô notebook chỉ được `from src.api import ...` - logic thuộc `src/`, và file trong `src/api/` chỉ
  re-export.

## Sau khi sao chép thì làm gì

1. Sửa `config.yaml`: `model`, `method`, `data.roles`, `prompt`, và `system_prompt` khi prompt dùng `{system_prompt}` (xem `experiment/README.md`).
2. Mở `notebook.ipynb`, chạy thử **trên máy cá nhân** cho tới khi trôi.
3. `python scripts/pin.py <model>/<method>/<expNNN>` để ghim bản code vào cell đầu.
4. Ghi lại file notebook vào git, đẩy lên nhánh `experiment`.

Từ bước 3 trở đi thì **không sửa** thư mục thí nghiệm nữa cho tới khi người nhận chạy xong
(`docs/06_plan/P5_notebook_pin.md`, mục rủi ro): sửa sau khi ghim nghĩa là kết quả chạy ra không
ứng với bản code đã ghim.
