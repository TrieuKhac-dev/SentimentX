# 05.07. Biến môi trường và secret

> Đọc file này khi: cấu hình máy cá nhân, hoặc chuẩn bị file env để gửi giảng viên.
> Liên quan: `docs/00_workflow/02_rules.md`, `docs/05_config/01_paths.md`

## Các file env

| File                 | Commit    | Dùng cho                  | Nội dung                   |
| -------------------- | --------- | ------------------------- | -------------------------- |
| `.env.example`       | có        | máy cá nhân, bản mẫu      | tên biến, giá trị để trống |
| `.env`               | không     | máy cá nhân, bản thật     | giá trị thật               |
| `.env.colab.example` | có        | Colab, bản mẫu            | tên biến, giá trị để trống |
| `.env.colab`         | **không** | Colab, bản gửi giảng viên | **đầy đủ khoá secret**     |

## Các biến

| Biến                      | Ý nghĩa                                                       |
| ------------------------- | ------------------------------------------------------------- |
| `DAGSHUB_TOKEN`           | token truy cập DagsHub                                        |
| `SENTIMENTX_DATA_ROOT`    | gốc dữ liệu, trên Colab trỏ vào Drive                         |
| `SENTIMENTX_RESULTS_ROOT` | gốc kết quả, trên Colab trỏ vào Drive                         |
| `SENTIMENTX_ENV`          | `colab` hoặc `local`                                          |
| `HF_HOME`                 | nơi cache model; trên Colab để ở đĩa tạm, không để trên Drive |

## Thứ tự nạp

1. Colab Secrets, nếu giảng viên tự đặt.
2. File `<Drive>/env/.env.colab`.
3. `os.environ`.
4. File `.env` ở máy cá nhân.

Notebook in ra bảng biến nào có, biến nào thiếu. Chỉ in **tên biến**, không in giá trị.

## Kết nối DagsHub

File `configs/dagshub.yaml` giữ phần hạ tầng, không chứa token:

```yaml
dagshub:
  owner: TrieuKhac-dev
  repo: SentimentX
  mlflow_uri: "https://dagshub.com/{owner}/{repo}.mlflow"
  token_env: DAGSHUB_TOKEN
```

Cách dùng, cấu hình thủ công nên chỉ cần `mlflow`:

```
MLFLOW_TRACKING_URI      = https://dagshub.com/TrieuKhac-dev/SentimentX.mlflow
MLFLOW_TRACKING_USERNAME = TrieuKhac-dev
MLFLOW_TRACKING_PASSWORD = <token>
```

Cách thay thế, nếu cài thêm gói `dagshub`:

```python
import dagshub
dagshub.init(repo_owner="TrieuKhac-dev", repo_name="SentimentX",
             mlflow=True, patch_mlflow=True)
```

`patch_mlflow=True` làm cho lỗi khi ghi lên MLflow không dừng chương trình.

## Bảo mật

- `.env.colab` chứa token thật, không bao giờ commit, gửi cho giảng viên qua kênh riêng.
- Nên dùng token của một tài khoản riêng chỉ có quyền trên repo DagsHub này.
- Đổi token sau khi kết thúc đồ án.
- Có thể tắt thống kê của thư viện DagsHub bằng biến `DAGSHUB_DISABLE_ANALYTICS`.
