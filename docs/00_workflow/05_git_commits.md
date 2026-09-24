# 05. Quy ước commit

> Đọc file này khi: chuẩn bị commit.
> Liên quan: `docs/06_plan/APPENDIX_commits.md`

## Định dạng

```
type(scope): subject
```

- Viết **tiếng Anh**, và viết như một câu ra lệnh ngắn: dùng `add`, `fix`, `remove`,
  không dùng `added`, `fixed`, `removed`.
- Tiêu đề không quá 72 ký tự, không kết thúc bằng dấu chấm.
- Cần giải thích lý do thì thêm phần thân, cách tiêu đề một dòng trống.

## Type

| Type       | Dùng khi                                |
| ---------- | --------------------------------------- |
| `feat`     | thêm khả năng mới                       |
| `fix`      | sửa lỗi                                 |
| `refactor` | đổi cấu trúc, không đổi hành vi         |
| `test`     | thêm hoặc sửa test                      |
| `docs`     | tài liệu, chú thích, mẫu env            |
| `style`    | chỉ đổi định dạng, căn lề, khoảng trắng |
| `chore`    | cấu trúc, phụ thuộc, config git         |
| `ci`       | thay đổi CI                             |

## Scope

Dùng tên miền công việc, ví dụ: `repo`, `git`, `env`, `config`, `paths`, `datasets`,
`versioning`, `experiments`, `labels`, `preprocessing`, `evaluation`, `tracking`, `mlflow`,
`resume`, `templates`, `notebook`, `preflight`, `scripts`, `ci`, `docs`, `data`, `assets`.

## Cách chia nhỏ

- Một commit là **một task nhỏ**, đủ để hiểu và để kiểm tra riêng.
- Sau mỗi commit, dự án vẫn phải chạy được.
- Task nào sửa nhiều miền thì tách thành nhiều commit theo miền.
- Không gộp việc sửa lỗi với việc đổi cấu trúc trong cùng một commit.

## Ví dụ

```
feat(paths): add paths module with env overrides
fix(evaluation): swap precision and recall for the mentioned class
docs(config): explain aspect_policy and neutral_policy
refactor(config): route all paths through paths module
style(docs): reformat tables after editor auto format
test(versioning): cover id and guard
```
