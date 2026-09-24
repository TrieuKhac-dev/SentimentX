# Schema và ý nghĩa nhãn

> Đọc file này khi: sửa schema, hoặc cần biết ý nghĩa từng nhãn.
> Liên quan: `docs/01_dataset/01_raw_data.md`, `docs/05_config/03_datasets.md`

## 1. Schema

Mỗi dòng có 9 cột, nhưng **schema không còn được viết cứng trong code**. Nó nằm
trong `configs/datasets/cosmetics/v0.1.0.yaml`:

| Cột            | Kiểu    | Ý nghĩa                                                     |
| -------------- | ------- | ----------------------------------------------------------- |
| `data`         | văn bản | nội dung review (khai báo ở khoá `text_column`)             |
| `stayingpower` | nhãn    | độ bền màu                                                  |
| `texture`      | nhãn    | kết cấu / chất son                                          |
| `smell`        | nhãn    | mùi                                                         |
| `price`        | nhãn    | giá                                                         |
| `others`       | nhãn    | **đã loại bỏ** (xem mục 2) - khai báo ở khoá `drop_columns` |
| `colour`       | nhãn    | màu sắc                                                     |
| `shipping`     | nhãn    | giao hàng                                                   |
| `packing`      | nhãn    | đóng gói                                                    |

Sau khi bỏ `others`, dữ liệu còn **8 cột: 1 cột văn bản + 7 cột aspect**.
Loader đổi tên cột văn bản thành `text`, nên trong mọi bước sau đó dữ liệu luôn có
dạng: `text` + 7 cột aspect.

## 2. Vì sao loại bỏ khía cạnh `others`

Khi khảo sát, cột `others` trong tập train chỉ có hai giá trị:

- ô trống (khía cạnh không được nhắc tới): 10.690
- `neutral`: 2.291

Nó **không hề có `positive` hay `negative`**, nên hoàn toàn không mang tín hiệu
phân loại cảm xúc. Giữ lại chỉ làm bài toán phức tạp thêm mà không giúp gì.
Quyết định này được khai báo tại `configs/datasets/cosmetics/v0.1.0.yaml`
(`aspects` và `drop_columns`).

> **Hệ quả cần nhớ:** trong 2.291 dòng train có `others = neutral`, **2.287 dòng**
> không có nhãn ở bất kỳ khía cạnh nào khác. Sau khi bỏ `others`, chúng trở thành
> những dòng **không có nhãn khía cạnh nào** - xem
> [02_eda/02_metrics.md](../02_eda/02_metrics.md) mục 11 để biết báo cáo trình bày nhóm
> này thế nào và [03_pipeline/02_steps.md](../03_pipeline/02_steps.md) mục 5 để biết
> pipeline xử lý ra sao.

## 3. Ý nghĩa các nhãn

| Giá trị trong ô | Ý nghĩa                                     |
| --------------- | ------------------------------------------- |
| `positive`      | khía cạnh đó được khen                      |
| `negative`      | khía cạnh đó bị chê                         |
| `neutral`       | khía cạnh đó được nhắc tới nhưng trung tính |
| **(ô trống)**   | khía cạnh đó **KHÔNG được nhắc tới**        |

> **Điểm rất dễ nhầm:** ô trống **không phải** là `neutral`.
> Ô trống = "review này không nói gì về khía cạnh đó".
> Đây là _null_, một trạng thái riêng biệt.

Bộ nhãn này do config khai báo (khoá `labels`); mã nhãn dùng trong dữ liệu đã xử lý
được cấp tự động từ danh sách đó - xem
[03_pipeline/05_output.md](../03_pipeline/05_output.md).

---

Xem tiếp: [03_new_dataset.md](03_new_dataset.md) - thêm dataset mới.
