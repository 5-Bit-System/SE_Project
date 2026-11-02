# HUS Retrieval Implementation Plan

> **For agentic workers:** Use local `project-toolkit/sources/superpowers/skills/executing-plans/SKILL.md`, inline. Execution is a separate task; this plan does not authorize crawling or publishing.

**Goal:** Thêm nhánh HUS Q&A có nguồn trong chatbot, tách khỏi dữ liệu môn học.

**Architecture:** Router tách recommendation/HUS/out-of-scope trước catalog lookup. Allowlisted documents được clean/chunk vào index riêng; retrieval lexical deterministic là bản đầu, chưa cần embedding/vector database. LLM chỉ chọn dẫn chứng/facts từ retrieved chunks; backend kiểm tra citation trước trả lời.

**Tech Stack:** Python 3.11, httpx, standard-library HTML parsing/JSON, Pydantic, pytest, FastAPI/static frontend.

**Spec:** `docs/SYSTEM_SPECIFICATION.md` mục chatbot HUS, `docs/DATABASE_DESIGN.md` mục HUS tách riêng; finding F05.

## Global Constraints

- Chỉ phạm vi thông tin đào tạo Khoa Toán – Cơ – Tin học HUS; không trộn vào courses/source rows/catalog revisions.
- Không có evidence thì nói chưa tìm thấy; nguồn conflict phải thông báo và hướng dẫn xác nhận với đơn vị phụ trách.
- Không cần chọn ngành để hỏi HUS. Chat vẫn session-scoped, thay ngành vẫn clear chat.
- Không crawl thực tế trước khi có URL allowlist đã xác minh. Mock HTML dùng để kiểm tra code, không được trình bày như nguồn HUS thật.

## Review Focus

- HUS query trước khi chọn ngành hoặc khi catalog storage lỗi (D1).
- Redirect/link ra ngoài host/path allowlist, URL nội bộ và tài liệu chứa chỉ thị (D2).
- Không kết quả, kết quả lệch phạm vi hoặc nguồn mâu thuẫn (D3).
- Model bịa URL/title/update hoặc thêm quy định không có trong chunks (D3).
- Một chunk thay đổi nội dung, link đổi và index chạy lại (D2).

## File Structure

- `app/hus/`: intent.py, models.py, crawler.py, cleaning.py, index.py, retrieval.py, answering.py.
- `data/hus/allowlist.json`: explicit approved URL/path rules và phạm vi; khởi tạo rỗng, không tự coi mọi HUS domain là được phép.
- `tools/build_hus_index.py`: công cụ dry-run/build riêng; output chỉ chứa tài liệu công khai, không chứa lịch sử người dùng.
- `tests/fixtures/hus/`: HTML giả lập; `tests/test_hus_*.py`: network/model mock.

### D1: Intent router và contract HUS

**Files:** Create `app/hus/__init__.py`, `intent.py`, `models.py`, `tests/test_hus_intent.py`; Modify `app/api/routes.py`, `app/schemas/advisor.py`, `app/services/advisor_service.py`.

**Interfaces:** `route_intent(message: str, history: list[AdvisorMessage]) -> Literal['recommendation','hus_information','out_of_scope','clarification']`; AdvisorRequest.program_id nullable, bắt buộc riêng recommendation. HUSCitation gồm chunk_id, url, title, updated_at nullable, retrieved_at; không đoán ngày.

- [ ] Test câu HUS không có program → HUS branch; recommendation không program → hỏi chọn ngành; câu mixed intent → hỏi làm rõ; unrelated → refusal. Mock catalog lookup ném lỗi nhưng HUS vẫn chạy.
- [ ] Chạy `.venv/Scripts/python.exe -m pytest tests/test_hus_intent.py -q` red; router chạy trước load_catalog, guardrails theo intent, không gửi query HUS vào course ranking.
- [ ] Chạy PASS; chat UI cho phép nhập HUS trước khi chọn ngành, không thay đổi behavior major isolation.

### D2: Allowlisted crawl, clean/chunk và index

**Files:** Create `app/hus/crawler.py`, `cleaning.py`, `index.py`, `retrieval.py`, `tools/build_hus_index.py`, `data/hus/allowlist.json`, `tests/test_hus_crawl.py`, `tests/fixtures/hus/`.

**Interfaces:** `crawl_document(url: str, allowlist: Allowlist, client: httpx.Client) -> HUSDocument`; `chunk_document(document: HUSDocument, max_chars: int = 1200) -> list[HUSChunk]`; `retrieve(query: str, index: HUSIndex, limit: int = 5) -> list[HUSChunk]`. Mỗi document có hash, URL canonical, title, ngày nguồn nullable và crawl time; mỗi chunk có ID ổn định theo hash/vị trí.

- [ ] Test allowlist rỗng không gọi mạng; URL ngoài path/host, redirect ngoài phạm vi hoặc localhost/private address đều bị chặn trước fetch. Timeout, HTTP lỗi, response quá 2 MiB → kết quả lỗi không publish index dở.
- [ ] Test bỏ menu/script/style nhưng giữ headings/title/source link; chunk giữ provenance; crawl lặp không duplicate, đổi hash thay index document atomically. Retrieval tiếng Việt có/không dấu và unrelated query trả [] khi không có term liên quan.
- [ ] Chạy `.venv/Scripts/python.exe -m pytest tests/test_hus_crawl.py -q` red; cài lexical index tách riêng, limit network/time/payload, coi nội dung trang là dữ liệu không phải instruction.
- [ ] Chạy PASS bằng mock. URL thật được thẩm định và nhập riêng khi người dùng yêu cầu triển khai nội dung; không tự crawl trong giai đoạn kế hoạch.

### D3: Answer/citation validation và UI

**Files:** Create `app/hus/answering.py`, `tests/test_hus_answers.py`; Modify `app/services/advisor_service.py`, `app/schemas/advisor.py`, `app/static/app.js`, `app/static/rendering.js`.

**Interfaces:** `answer_hus(question: str, chunks: list[HUSChunk], provider: object | None = None) -> HUSAnswer`; model output gồm answer units tham chiếu fact/chunk IDs, backend gắn citation URL/title/update từ index. Không cho model cung cấp citation URL tùy ý; không có fact được validate thì fallback trích đoạn ngắn thay vì free-text quy định.

- [ ] Test empty retrieval → thông báo chưa tìm thấy, không đoán; out-of-scope → từ chối; conflict giữa nguồn → giữ cả citations và chỉ dẫn xác nhận, không chọn quy định tùy ý.
- [ ] Test fabricated chunk ID/URL/update, injected instruction trong document, model timeout → reject/fallback có nguồn; không có API key vẫn đưa được excerpt citation.
- [ ] Chạy `.venv/Scripts/python.exe -m pytest tests/test_hus_answers.py -q` red; cài grounding/citation validator và UI links safe của C2, thêm riêng mode HUS không biến thành menu FAQ.
- [ ] Chạy PASS và browser mock test citation; nghiệm thu nội dung thật cần URL/documents đã thẩm định, kiểm tra truy xuất bằng bộ câu hỏi HUS được review. Update SYSTEM_SPECIFICATION/checklist, không claim nguồn đang hiệu lực chỉ vì crawl thành công.
