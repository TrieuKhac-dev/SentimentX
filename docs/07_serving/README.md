# 07 — Serving

> Đọc file này khi: cần biết P0 serving là gì, chạy thế nào, đang ở đâu.

## P0 là gì

**P0 — web serving** là bước đóng gói hai model đã huấn luyện (`cafebert_exp027` và
`qwen3_4b_exp009`) thành một web service để gửi một review tiếng Việt và nhận về dự đoán ABSA trên
7 aspect (`stayingpower, texture, smell, price, colour, shipping, packing`).

## Tài liệu

| File | Nội dung |
| --- | --- |
| [`P0_PLAN.md`](./P0_PLAN.md) | Kế hoạch chi tiết P0: mục tiêu, registry, API, UI, điều kiện chấp nhận, rủi ro, commit |

## Cách chạy

```powershell
pip install -r requirements-serving.txt

python -m serving.app --model cafebert_exp027

python -m serving.app --model cafebert_exp027,qwen3_4b_exp009

python -m unittest discover -s serving/tests -v
```

## Trạng thái hiện tại

**Đang triển khai (implementation in progress).** P0 chưa xong; các điều kiện chấp nhận ở
`P0_PLAN.md` là mục tiêu, chưa phải kết quả đã đạt.