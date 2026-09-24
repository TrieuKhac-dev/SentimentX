# Quy ước trình bày báo cáo

> Đọc file này khi: viết hoặc sửa nội dung báo cáo.
> Liên quan: `docs/02_eda/03_modules.md`, `src/reporting/`

Áp dụng cho **cả** báo cáo EDA và báo cáo Pipeline - hai báo cáo dùng chung
`src/reporting/` (Jinja2 + Plotly), chỉ khác dữ liệu đầu vào.

## 1. Cách gọi tên trong báo cáo

| Trong báo cáo         | Nghĩa                                     | Ghi chú                                                                                                                                             |
| --------------------- | ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| **khía cạnh**         | một `aspect` của bài toán ABSA            | tên cột trong config và trong dữ liệu vẫn là tiếng Anh (`stayingpower`, `colour`...); báo cáo viết tiếng Việt nên dùng "khía cạnh" thay vì "aspect" |
| **split**             | một trong ba tập `train` / `val` / `test` | giữ nguyên thuật ngữ, không dịch                                                                                                                    |
| **Step 1...7**          | các bước của Data Pipeline                | báo cáo pipeline đánh số "Step n" cho khớp với `src/pipeline/`                                                                                      |
| **dòng** / **review** | một bản ghi                               | ở EDA, một dòng là một review; ở pipeline, cột "dòng trong file" là vị trí gốc của bản ghi đó                                                       |

## 2. Quy ước trình bày

Mỗi số liệu chỉ được trình bày MỘT lần trên báo cáo HTML - hoặc bằng bảng, hoặc
bằng biểu đồ:

- nếu bảng chỉ lặp lại đúng những con số của biểu đồ thì bỏ bảng;
- nếu bảng có thêm cột mà biểu đồ không thể hiện được (lí do bị gắn cờ, tên file
  gốc, nhãn của từng split) thì giữ bảng và không vẽ biểu đồ cho cùng số liệu đó.

Báo cáo **không có câu giải thích**: chỉ gồm thẻ số liệu, bảng và biểu đồ. Bản số
liệu đầy đủ (mọi cột, mọi dòng) luôn nằm ở file CSV/JSON trong cùng thư mục phiên
bản - thư mục đó được ghi **một lần** ở đầu báo cáo ("Thư mục số liệu chi tiết");
báo cáo không liệt kê từng file nữa vì mỗi mục đã có 4-6 file.

Biểu đồ cột **ngang** (từ hay gặp, emoji, lí do loại) luôn sắp **giảm dần từ
trên xuống**: Plotly đặt nhóm đầu tiên ở đáy, nên trục được đảo lại cho khớp
thứ tự người đọc mong đợi (`src/reporting/charts.py::_bar`).

> **Không có khoá `summary` hay `note`** trong file kết quả. Báo cáo chỉ chứa số liệu
> và biểu đồ, không có câu giải thích nào - kể cả trong tiêu đề mục. Đó là lí do mọi
> phần "vì sao / nghĩa là gì" đều nằm trong tài liệu này, không nằm trên báo cáo.

Cách bảng được canh lề và cắt chữ (các khoá tuỳ chọn của một bảng):
[05_extend.md mục 2](05_extend.md). Danh sách loại biểu đồ: [05_extend.md mục 3](05_extend.md).
