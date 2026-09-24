# 05.06. Cấu hình riêng của thí nghiệm

> Đọc file này khi: tạo thí nghiệm mới hoặc sửa cấu hình của một thí nghiệm.
> Liên quan: `docs/05_config/05_experiments_shared.md`, `docs/06_plan/P5_notebook_pin.md`

File: `experiments/<model_id>/<method>/<expNNN>/config.yaml`.

## Ví dụ

```yaml
exp_id: exp001
parent: null
model: qwen3-4b-instruct-2507
method: prompt-cot
data:
  dataset: cosmetics
  version: v0.3.0
  roles: { train: train, val: val, eval: test }
prompt: prompt.txt
examples: examples.txt
system_prompt: configs/prompts/system/absa_cot.txt
requires_extra: []
```

## Giải thích

| Khoá             | Ý nghĩa                                                                                      |
| ---------------- | -------------------------------------------------------------------------------------------- |
| `exp_id`         | định danh thí nghiệm, trùng tên thư mục                                                      |
| `parent`         | thí nghiệm gốc, ghi bằng đường dẫn đầy đủ `<model>/<method>/<expNNN>`; `null` nếu là bản gốc |
| `model`          | `model_id`, trỏ tới `configs/models/<model_id>.yaml`                                         |
| `method`         | tên phương pháp, cũng là tên thư mục cha                                                     |
| `data.dataset`   | **một** dataset duy nhất. Không được khai danh sách                                          |
| `data.version`   | phiên bản dataset, trỏ tới `configs/datasets/<name>/<version>.yaml`                          |
| `data.roles`     | **bắt buộc khai**, không kế thừa: mỗi vai dùng split nào của chính dataset đó                |
| `prompt`         | đường dẫn file prompt, tính từ gốc repo                                                      |
| `examples`       | đường dẫn file ví dụ few-shot                                                                |
| `system_prompt`  | đường dẫn file chứa khối `[SYSTEM]`; bắt buộc nếu prompt dùng ô nhớ `{system_prompt}`        |
| `requires_extra` | danh sách đường dẫn bổ sung mà notebook phải kiểm, cho thứ máy không suy ra được             |

## Quy tắc vai

| Vai     | Bắt buộc                     | Ghi chú                                                   |
| ------- | ---------------------------- | --------------------------------------------------------- |
| `eval`  | luôn                         | thí nghiệm chỉ prompt cũng cần, để biết chấm trên tập nào |
| `train` | khi `training.enabled: true` |                                                           |
| `val`   | khi `training.enabled: true` | là cơ sở chọn `model/best`                                |

Ngoài ra: giá trị của mỗi vai phải là khoá có thật trong `splits` của file dataset version.
Chấm trên `train` bị chặn, vì đó là rò rỉ dữ liệu.

## Thứ tự hợp nhất

```
configs/models/<model_id>.yaml
configs/experiments/repo.yaml
configs/experiments/task.yaml
configs/experiments/evaluation.yaml
configs/experiments/training.yaml
configs/experiments/tracking.yaml
experiments/<model_id>/<method>/<expNNN>/config.yaml     đè lên tất cả
```

Không hợp nhất: `configs/paths.yaml`, `configs/dagshub.yaml`, `configs/pipeline/<v>.yaml`,
`configs/datasets/<name>/<v>.yaml`, và các file prompt. Chúng được ghi vào `run_meta.files[]` kèm `role`.

## Cách ghi đè một giá trị dùng chung

Năm file trong `configs/experiments/` khai khoá ở mức cao nhất, nên muốn đè thì thí nghiệm ghi
**đúng đường dẫn khoá đó** ở mức cao nhất của `config.yaml`:

```yaml
# configs/experiments/evaluation.yaml khai "n: null"
n: 200                      # <= đè đúng khoá đó
preprocess:
  max_length: 1024          # <= đè khoá lồng của lớp model
```

Ghi `evaluation: {n: 200}` là **sai**: nó tạo ra một khoá `evaluation` mới mà không chỗ nào đọc,
trong khi `n` vẫn giữ giá trị cũ. Vì đây là lỗi im lặng, phần kiểm tra sẽ báo lỗi khi gặp khoá
lạ trong cấu hình đã hợp nhất.

## Tạo thí nghiệm mới

Dùng `python scripts/new_experiment.py --model ... --method ...`. Công cụ này tự chọn số `expNNN`
kế tiếp từ trạng thái đã hợp nhất, nên không thể trùng số với thí nghiệm trước.
