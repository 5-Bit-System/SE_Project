# HUS RAG scope correction implementation plan

> **For agentic workers:** dùng executing-plans cho implementation trực tiếp; review độc lập khi xong. Không commit/push trong yêu cầu này.

**Goal:** demo RAG chỉ F1/F2/F3 và trò chuyện cơ bản, không chạy recommendation.
**Architecture:** service chat độc lập bọc answerer hiện có; app demo FastAPI riêng,
giao diện riêng và launcher loopback. Không sửa worktree/receipt P0-4/P0-5 đã đóng băng.
**Tech Stack:** Python/FastAPI/Pydantic, HTML/CSS/JavaScript, Playwright hiện có.
**Spec:** [scope design](../specs/2026-11-02-hus-rag-scope-design.md).

## Constraints / review focus

Không đổi release/review. Không gọi DB/auth/VNU/provider hoặc ranking/explanation.
Không để câu có lời chào che truy vấn học vụ; không dùng version quyết định F2 lọc F1.
Không biến gợi ý chọn môn thành facts; không gắn citation cho lời xã giao. Đổi ngành
phải bỏ response cũ. Cấu hình hỏng phải fail closed, không giả kết quả thiếu nguồn.

## Task 1 — Chat/API độc lập

- [x] Viết test `tests/hus/test_chat_scope.py`, chạy RED trước khi thêm code.
- [x] Thêm `app/hus/chat.py`: HUSChatReply, basic_reply, chat(request, answerer).
- [x] Thêm `app/hus/demo.py`: app, GET /hus/config, POST /hus/chat, source endpoint,
  phục vụ giao diện riêng. Dùng HUSQuestion/HUSAnswer có sẵn, không import advisor.
- [x] GREEN: test xã giao, F1/F2/F3, no-information, API lỗi/hash và subprocess chặn
  import recommendation/eligibility/profile/auth/provider trong ứng dụng demo.

## Task 2 — Giao diện và launcher

- [x] Thêm `app/static/hus-rag-demo.{html,js,css}` theo contract Task1.
- [x] Chuyển launcher local sang app demo, không giả account/catalog/binding.
- [x] Browser kiểm hội thoại hỗn hợp bốn ngành, AI opt-in/nhãn, binary/citation,
  đổi ngành trong khi chờ và bỏ phản hồi cũ. Giữ tên lệnh mở demo hiện có.

## Task 3 — Tài liệu và nghiệm thu

- [x] Sửa các sơ đồ RAG trong SYSTEM_SPECIFICATION; cập nhật tiến độ/memory/demo guide.
- [x] Chạy test phù hợp, Ruff/JS syntax/diff, review độc lập và receipt mới.
- [x] Ghi rõ main integration/CI/commit/phát hành cần nghiệm thu lại cho scope mới;
  không dùng receipt cũ để tuyên bố phần này đã xong.

## K?t qu? local

- RED?GREEN:18 ca scope/API; c? subprocess ch?n import product stack v? ca edition F1.
- To?n b? crawldata:717 passed/26 skipped, m?t warning TestClient;5 Node legacy ??t.
- Demo m?i:50 c?u h?i Chromium tr?n4 ng?nh, hai trang PDF13/12, scope race v? AI reset.
- Review ??c l?p kh?ng c? finding quan tr?ng c?n m?; edition F1 ???c s?a v?i test RED?GREEN.
- Receipt: docs/acceptance/hus_rag_scope_report.json. P04/P05 outputs v?63 data input gi? hash.
- K? ho?ch n?y ho?n t?t ph?n local. Main integration c? auth, commit/CI/ph?t h?nh l?
  c?ng vi?c ti?p theo ???c ghi ri?ng trong RAG_PROGRESS_AND_NEXT_PLAN.md; ch?a l?m.
