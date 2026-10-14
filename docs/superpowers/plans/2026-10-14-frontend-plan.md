# Frontend Reliability Implementation Plan

> **For agentic workers:** Use local `project-toolkit/sources/superpowers/skills/executing-plans/SKILL.md`, inline. Read webapp-testing only when executing browser tests; no dependency installation during planning.

**Goal:** Chặn dữ liệu phản hồi cũ, render catalog an toàn và so sánh What-if theo cùng baseline.

**Architecture:** Giữ static frontend. Context epoch thay đổi theo ngành/hồ sơ/transcript/track/path; mỗi request giữ snapshot và chỉ commit khi snapshot còn hiện hành. Giữ DOM và state reset đồng thời. What-if giữ baseline trong phiên, không persist database.

**Tech Stack:** JavaScript, HTML/CSS, browser tests với API mock; FastAPI/Pydantic cho What-if contract.

**Spec:** `docs/SYSTEM_SPECIFICATION.md`; findings U01–U03/F03/F04 trong audit.

## Global Constraints

- Đổi ngành xóa transcript và chat context; không auto trộn profile/ngành.
- Giữ FastAPI/static frontend, không chuyển React hoặc redesign ngoài mục sửa.
- Không lưu chat/transcript người dùng vào DB hay localStorage.

## Review Focus

- Response ngành A về sau B, hoặc profile A1 về sau A2 (C1).
- Summary cũ trộn passed codes cũ với program mới ở request kế tiếp (C1).
- Request bị invalidated không chạy finally reset nút (C1).
- Course/reason có HTML và chat cũ còn trên DOM (C1/C2).
- Baseline thay transcript/revision giữa hai lần What-if (C3).

## File Structure

- Tạo `app/static/request-context.js` quản lý epoch/token/snapshot; import từ app.js qua script module.
- Tạo `tests/browser/test_context_races.py`, `test_safe_rendering.py`, `test_what_if.py`; dùng công cụ browser có sẵn lúc execution, cài thêm chỉ khi cần test thật và trong scope.
- Đăng ký marker `browser` trong pyproject; browser suite chạy explicit ở job riêng với dependency browser, không làm default offline suite yêu cầu trình duyệt. Khi explicit chạy mà thiếu dependency phải báo lỗi, không silent skip.
- Tách render helper nhỏ ở `app/static/rendering.js`; không chia tất cả JS trước khi sửa lỗi.

### C1: Context epoch và reset state/DOM

**Files:** Create `app/static/request-context.js`, `tests/browser/test_context_races.py`; Modify `app/static/app.js`, `app/static/index.html`.

**Interfaces:** `captureContext(state) -> frozen snapshot`, `isCurrent(snapshot, state) -> boolean`, `invalidateContext(state) -> void`; mỗi channel có request sequence riêng, mỗi button có owner token. Snapshot có epoch/program/profile/transcript/track/path; mọi request chain dùng snapshot đầu vào, không đọc state mới giữa await.

- [ ] Test API mock delay courses A sau B → chỉ courses B hiện; profile P1 sau P2 cùng ngành → chỉ P2; eligibility T1 sau T2 → chỉ T2. Chat A về sau đổi B → không append history/DOM B.
- [ ] Test đổi ngành xóa ngay courses/KPI/rules/chat DOM và state; buttons cũ được reset, không cần chờ response. Recommendation/what-if chạy nối tiếp không để nút của request cũ disabled mãi.
- [ ] Chạy browser tests red; cài token/context snapshot cho courses/profiles/summary/eligibility/recommendation/what-if/chat và reset routines chung. Dùng AbortController khi có ích, vẫn cần token check vì abort không đảm bảo response không về.
- [ ] Chạy tests PASS trên API mock; smoke browser với server cấu hình rõ ràng, không seed DB hiện hành để test.

### C2: Render an toàn và progress/clarification

**Files:** Create `app/static/rendering.js`, `tests/browser/test_safe_rendering.py`; Modify `app/static/app.js`, `index.html`, `styles.css`.

**Interfaces:** `createTextElement(tag, className, value) -> HTMLElement`; `renderProgress(progress)`, `renderClarification(questions)`. Dùng progress A5 và questions B4; thiếu trường thì hiển thị chưa có dữ liệu.

- [ ] Test tên/reason `<img src=x onerror=...>` được hiển thị nguyên văn, không tạo element/action; các link citation sau D3 chỉ URL allowlisted http(s), không javascript.
- [ ] Test keyboard submit/focus/chat close, loading/error/empty states; progress quota đa nhóm không làm tăng tổng TC và dữ liệu unknown không hiển thị 0 chắc chắn.
- [ ] Chạy browser tests red; thay các innerHTML có dữ liệu server bằng DOM/textContent. Giữ static markup khi không có nội dung dữ liệu; không đưa prefix tên backend/mode kỹ thuật vào flow tư vấn.
- [ ] Chạy PASS, kiểm tra không có console error; chưa có A5/B4 thì triển khai render helper riêng, nối contract sau khi dependencies hoàn tất.

### C3: Baseline What-if và rank delta

**Files:** Modify `app/models.py`, `app/service.py`, `app/api/routes.py`, `app/static/app.js`; Create `tests/test_what_if_baseline.py`, `tests/browser/test_what_if.py`.

**Interfaces:** RecommendationResponse thêm `context_fingerprint` (SHA-256 catalog revision + passed codes + selectors + hard eligibility cap); WhatIfRequest thêm `baseline_context_fingerprint`, `baseline_order: list[str]`. Response thêm `rank_deltas: dict[str, int | None]`; delta=baseline_rank-new_rank, null khi chưa có baseline rank. Baseline client chỉ là dữ liệu so sánh, không có quyền cấp eligibility.

- [ ] Test đổi weights/preferences giữ cùng input → fingerprint/eligible set giữ nguyên; ranking có thể đổi và delta đúng; baseline code lạ không thành candidate.
- [ ] Test revision/transcript/track/path/hard cap đổi → baseline mismatch 422, UI yêu cầu chạy lại recommendation và xóa so sánh cũ; không cho baseline tự mở khóa môn.
- [ ] Chạy `.venv/Scripts/python.exe -m pytest tests/test_what_if_baseline.py -q` red; cài fingerprint/delta và baseline session, giữ min target limits B2 ở selection.
- [ ] Chạy unit/browser tests PASS; không persist baseline/profile/chat. Update SYSTEM_SPECIFICATION mô tả contract so sánh mới.
