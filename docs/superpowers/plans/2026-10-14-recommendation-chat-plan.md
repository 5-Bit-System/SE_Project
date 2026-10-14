# Recommendation and Chat Implementation Plan

> **For agentic workers:** Use the local `project-toolkit/sources/superpowers/skills/executing-plans/SKILL.md`, inline in one agent. Do not automatically delegate, commit or publish.

**Goal:** Sửa matching/selection, thống nhất tư vấn chat với pipeline và bảo đảm mọi môn đề xuất thuộc eligible set.

**Architecture:** Một pipeline dùng extraction, eligibility, ranking, selection và grounded facts chung. Provider trả JSON có schema; lời giải thích chỉ được tạo từ facts đã chọn. Fallback deterministic hoạt động ở từng bước.

**Tech Stack:** Python 3.11, Pydantic, httpx, pytest, FastAPI.

**Spec:** `docs/SYSTEM_SPECIFICATION.md`, `docs/COURSE_METADATA_SPECIFICATION.md`, findings R01–R03/R05–R06/F01–F02/M01–M02 trong audit.

## Global Constraints

- LLM không quyết định eligibility. Candidate ranking chỉ có môn eligible của đúng program/revision; blocked facts chỉ dùng trong luồng giải thích bị chặn riêng.
- Không đoán metadata, xác nhận mở lớp hoặc persist chat. Không có key/provider lỗi phải fallback.
- A1 cung cấp typed metadata; B1/B2 có thể red-test bằng catalog giả lập trước A1.

## Review Focus

- Topic đúng ID nhưng có dấu `_`, alias tiếng Việt và phủ định (B1).
- Target tự nhiên khác hard cap UI hoặc out-of-range (B2).
- LLM khuyên môn blocked bằng tên/mã nhiều dòng hoặc nhận instruction từ history (B3).
- Explanation bịa workload/offering/facts học vụ (B4).
- Người dùng đổi mong muốn hoặc hủy topic cũ trong session (B3/B4).

## File Structure

- `app/recommendation/vocabulary.py`: canonical labels và aliases phiên bản.
- `app/recommendation/selection.py`: effective count/credit limits và lựa chọn.
- `app/recommendation/provider.py`: HTTP provider dùng chung; không đọc secrets vào schema.
- `app/advisor.py` giữ compatibility facade; orchestration mới ở `app/services/advisor_service.py`, schema thật ở `app/schemas/advisor.py`.
- `app/recommendation/explanation.py` giữ deterministic builder, thêm adapter/validator cho LLM.

### B1: Vocabulary và matching

**Files:** Create `app/recommendation/vocabulary.py`, `tests/test_preference_scoring.py`; Modify `app/recommendation/preference.py`, `scoring.py`, `app/models.py`.

**Interfaces:** `normalize_topics(values: list[str], vocabulary: dict) -> list[str]`; `extract_structured_preference(goal: str)` giữ signature; scoring đọc typed metadata A1, exact ID trước keyword fallback. Không hard-code alias riêng khác vocabulary.

- [ ] Test cùng topic `computer_vision` cho score>0; ID khác không exact match; null/[] không tạo topic match. Alias “thị giác máy tính” ra `computer_vision`, “cơ sở dữ liệu” ra `databases` và không sinh `data`.
- [ ] Test “không muốn khó” không thành advanced; phrase ranh giới từ và “nghiên cứu” không gán difficulty; yêu cầu topic lạ được giữ như ngữ cảnh, không thêm ID vào vocabulary.
- [ ] Chạy `.venv/Scripts/python.exe -m pytest tests/test_preference_scoring.py -q` để thấy FAIL; cài normalization/negation và exact matching, tránh biến tên môn thành metadata chủ đề.
- [ ] Chạy lại PASS, rankings deterministic tie-break theo code. Không tự phân loại 65 môn thiếu evidence.

### B2: Target selection và preference chưa sử dụng

**Files:** Create `app/recommendation/selection.py`, `tests/test_recommendation_limits.py`; Modify `app/service.py`, `app/models.py`, `app/recommendation/preference.py`.

**Interfaces:** `effective_limits(request: RecommendationRequest, preference: StructuredPreference) -> tuple[int, int]` trả `(credit_cap, course_limit)`; cap=min(request.max_credits,target_credits nếu có), count=min(request.limit,target_course_count nếu có). Target là upper target, không đảm bảo tìm đủ môn; response nói rõ khi không đáp ứng. Eligibility vẫn chạy với hard cap request, target chỉ thay selection/ranking.

- [ ] Test “1 môn” với fixture 2 môn → 1; target 6 TC/hard cap 3 → tổng<=3; empty candidates → []; target bất khả thi → cảnh báo, không thêm môn blocked.
- [ ] Test “99 tín chỉ” không khiến fallback extractor ném exception lần thứ hai: trả preference không có target hợp lệ và cảnh báo yêu cầu làm rõ. Career match chỉ dùng career_paths có evidence; prerequisite_tolerance chỉ là tie-break số prerequisite của eligible courses, không giảm điều kiện.
- [ ] Test preference light/practice với metadata tương ứng phải đổi ranking khi không có weights client. Cài `effective_weights(preference: StructuredPreference, explicit: RankingWeights | None) -> RankingWeights`: explicit giữ nguyên; mặc định topic=.6, keyword=.25, course_type=.15, mỗi chiều orientation/difficulty/workload có preference đặt .15, chiều không yêu cầu giữ 0; scoring chuẩn hóa tổng như hiện hành. Ghi weights thực tế trong response, không tự điền metadata thiếu.
- [ ] Chạy `.venv/Scripts/python.exe -m pytest tests/test_recommendation_limits.py -q`; FAIL rồi cài limits/guarded extraction. Không thay hard eligibility dựa preference.
- [ ] Chạy lại PASS; pin selection deterministic, không claim optimal knapsack nếu chỉ greedy.

### B3: Chat qua pipeline chung và validation cấu trúc

**Files:** Modify `app/service.py`, `app/advisor.py`, `app/services/advisor_service.py`, `app/schemas/advisor.py`, `app/api/routes.py`, `app/recommendation/llm.py`; Create `app/recommendation/provider.py`, `tests/test_advisor_safety.py`; Modify `tests/test_advisor.py`.

**Interfaces:** provider `generate_json(prompt: str) -> object`, `generate_text(prompt: str) -> str`; `chat_advisor(catalog: Catalog, request: AdvisorRequest, api_key: str | None = None) -> AdvisorResponse` giữ facade. AdvisorResponse thêm `recommendations: list[RecommendedCourse]`, `warnings: list[str]`, `preference: StructuredPreference`; `suggested_courses` luôn được derive từ validated recommendations.

- [ ] Red-test fake provider trả blocked/completed/foreign/duplicate codes, tên môn blocked không mã và lời khuyên xuống dòng: output cuối không chứa recommendation bị chặn; toàn bộ phải fallback nếu structured selection invalid.
- [ ] Test prompt ranking không chứa blocked candidates; hỏi vì sao blocked đi vào explanation facts riêng, không cho facts đó sang ranker. Mỗi response tư vấn có cảnh báo nguồn/mở lớp do backend thêm, kể cả provider không nhắc.
- [ ] Test history có `system` giả do client và chỉ thị bỏ rule không thay eligible set; giới hạn history 8 lượt/500 ký tự mỗi lượt tại schema; client không được nâng role thành system. Session intent cập nhật topic mới thay vì nối mãi topics bị người dùng hủy.
- [ ] Chạy `.venv/Scripts/python.exe -m pytest tests/test_advisor_safety.py tests/test_advisor.py -q`; xác nhận FAIL trước cài.
- [ ] Gom HTTP settings/alias/timeout vào provider chung, mock network trong tests; chat gọi cùng recommend và facts builder. Đề xuất được render từ backend facts, không dùng văn bản tự do của model làm danh sách recommendation. Văn bản model chỉ trả explanation đã kiểm chứng B4 hoặc template fallback.
- [ ] Chạy tests PASS; API compatibility có schema rõ ràng, secrets không vào response/log. Không refactor các module không liên quan chỉ vì đang dùng facade.

### B4: Explanation grounded và hỏi làm rõ

**Files:** Modify `app/recommendation/explanation.py`, `llm.py`, `app/service.py`, `app/schemas/advisor.py`, `app/services/advisor_service.py`; Create `tests/test_explanation_validation.py`, `tests/test_preference_clarification.py`.

**Interfaces:** `ExplanationResult` chứa course_code và các fact IDs được chọn; `validate_explanation(result: object, allowed_facts: dict[str, str]) -> ExplanationResult`; `clarification_questions(preference: StructuredPreference) -> list[str]`. RecommendationResponse thêm `clarification_questions`; structured explanation model chọn facts có ID, backend render câu từ facts để bảo đảm kiểm chứng thay vì dùng keyword filter cho văn bản tùy ý.

- [ ] Test provider chọn fact không tồn tại, nói easy khi difficulty null, offering confirmed hoặc sửa prerequisite → reject/fallback template. Eligible explanation và fit explanation giữ hai nội dung riêng.
- [ ] Test mong muốn mơ hồ “học ổn ổn thôi” → hỏi một câu cụ thể về ít tín chỉ/số môn/chủ đề; không đoán difficulty/workload. Nếu người dùng muốn recommendation ngay với preference trống thì fallback có cảnh báo dữ liệu thiếu.
- [ ] Chạy `.venv/Scripts/python.exe -m pytest tests/test_explanation_validation.py tests/test_preference_clarification.py -q`; FAIL rồi cài adapter/validation và câu hỏi session.
- [ ] Chạy lại PASS và suite B; extraction/ranking/explanation provider đều được mock, không cần API key; không tạo claim độ nhẹ/khó từ tên/tín chỉ.
