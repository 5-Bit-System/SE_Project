# Module 04 — Đề xuất môn học (Recommendation)

**Use case:** UC04, UC05, UC06, UC07

**Trạng thái:** `app/ranking.py` có `KeywordRanker`; `app/service.py` lọc mã lạ/trùng, kiểm tra tổng TC và dùng thứ tự dự phòng khi ranker lỗi. Chưa gọi LLM thật.

## Mục tiêu

Tạo kết quả gợi ý từ hồ sơ và catalog: kiểm tra hồ sơ → lọc điều kiện → xếp hạng → kiểm tra danh sách cuối → trả môn/lý do/cảnh báo. Xếp hạng và adapter LLM là các thành phần bên trong module này, không phải phần việc của riêng một người. API key là tùy chọn; app vẫn chạy bằng baseline khi thiếu key hoặc dịch vụ lỗi.

## Đầu vào và đầu ra

- Đầu vào ngoài module: `RecommendationRequest`; đầu ra: `RecommendationResponse` qua `POST /recommendations`.
- `recommend(catalog, request, ranker=None)` điều phối các bước; ranker bên trong dùng `rank(candidates, goal) -> list[str]`.
- Adapter LLM cần bổ sung; nếu bổ sung lý do từ LLM thì phải mở rộng hợp đồng ranker, không coi interface hiện tại đã trả lý do.
- Baseline `KeywordRanker` hoạt động không cần API key; router nhận request và chuyển lỗi thành HTTP phù hợp.

## Thành phần triển khai

- Mục tiêu: `app/modules/recommendation/` gồm `router.py`, `service.py`, `schemas.py`, `ranking.py`, `llm_adapter.py`; chưa refactor code.
- Hiện tại: `app/service.py`, `app/ranking.py`, API gợi ý trong `app/main.py` và request/response trong `app/models.py`.
- Test điều phối/guard hiện có trong `tests/test_recommendations.py`; cần bổ sung test adapter/ranker.

## Chức năng cần đáp ứng

1. Gọi Catalog, Profile và Eligibility để xác định đúng tập ứng viên. Giữ interface xếp hạng `rank(candidates, goal) -> list[course_code]`; không gửi cả bốn catalog hoặc dữ liệu sinh viên thật cho LLM.
2. Yêu cầu đầu ra có cấu trúc và kiểm tra định dạng ở adapter. Service chặn mã lạ, mã trùng, môn đã qua hoặc ngoài tập ứng viên; kiểm tra tổng TC và quy định của danh sách cuối, không chỉ từng môn.
3. Đặt timeout, xử lý lỗi mạng/JSON và fallback về baseline. Không để request chờ vô hạn hoặc trả lỗi 500 chỉ vì LLM không hoạt động.
4. Tạo lý do ngắn bám thông tin mục tiêu/môn được chọn; phân biệt phần giải thích dựa trên luật (chắc chắn) và nhận xét xếp hạng (gợi ý). Không đưa ra khẳng định về lịch mở môn hay khả năng đậu.
5. So sánh baseline và LLM trên hồ sơ tổng hợp nhỏ, ghi lại cách đánh giá/giới hạn của phép thử. Không cần huấn luyện hay fine-tune model.

## Đầu ra và nghiệm thu

- Test khi LLM trả mã lạ, mã ngành khác, trùng mã, danh sách rỗng, JSON sai, timeout và thiếu API key; kết quả cuối vẫn chỉ chứa ứng viên hợp lệ.
- Không có khóa trong Git, log hoặc test fixture; hướng dẫn cấu hình bằng biến môi trường và `.env.example` nếu cần.
- `python -m pytest -q` đạt; tài liệu nêu provider/model được dùng, cách chạy **không cần key** và giới hạn chi phí sử dụng.

## Ranh giới

Module này dùng Catalog để lấy dữ liệu đúng ngành, Profile để kiểm tra hồ sơ và Eligibility để kiểm tra điều kiện. Giao diện gọi router của Recommendation. Ranker chỉ nhận tập ứng viên được service cung cấp; dùng mock để test lỗi provider.

Module này không sửa catalog và không quyết định điều kiện học vụ. LLM là bước ưu tiên mềm sau bộ lọc luật; nếu chưa có key, baseline vẫn là hành vi mặc định.
