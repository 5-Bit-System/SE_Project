# Module 05 — Giải thích và kiểm tra kết quả LLM

## Mục tiêu

Tạo explanation có căn cứ và kiểm tra mọi output từ LLM trước khi trả ra frontend.

## Phạm vi

- Validate preference extraction.
- Validate ranking output.
- Validate explanation output.
- Tạo explanation fallback bằng template từ facts backend.
- Tách rõ lý do đủ điều kiện và lý do phù hợp.
- Gắn source status và offering uncertainty vào response.

## Không làm

- Không để LLM quyết định eligibility.
- Không cho LLM đưa course ngoài eligible set vào kết quả.
- Không cho LLM bịa topic, workload, difficulty, prerequisite hoặc offering.
- Không đưa API key xuống frontend.
- Không coi lời văn của LLM là dữ liệu sự thật nếu không có fact backend.

## Các sự kiện backend cung cấp

- Metadata môn học.
- Eligibility reasons.
- Missing prerequisite/group reasons.
- Preference matches.
- Score contributions.
- Catalog status và source status.

## Dữ liệu đầu ra

Mỗi recommendation nên có:

- course code, name, credits.
- rank/score.
- eligible_because.
- fit_reasons.
- source_status.
- warnings.
- explanation_status.

## Kiểm tra kết quả

- Code phải thuộc eligible set.
- Không trùng code.
- Không chứa completed hoặc blocked course.
- Rank và limit hợp lệ.
- Explanation không mâu thuẫn với facts.
- Khi validation fail, dùng fallback code-based.

## Tiêu chí hoàn thành

- Có fixture cho hallucinated course code.
- Có fixture cho duplicate/malformed output.
- Có fallback không cần API key.
- Explanation luôn chứa cảnh báo catalog/offering khi cần.
