# Giải thích chi tiết Project: Explainable Course Recommender (AI-07)

> Tài liệu này viết cho người mới, giải thích từ đầu, kèm nghĩa tiếng Việt cho mọi từ tiếng Anh khó.

## 0. Từ điển Anh – Việt (đọc trước để đỡ ngợp)

| Từ tiếng Anh | Nghĩa tiếng Việt dễ hiểu |
|---|---|
| **Course Recommender** | Hệ thống gợi ý môn học |
| **Explainable** | Giải thích được — không chỉ đưa ra môn, mà còn nói *vì sao* gợi ý môn đó |
| **Catalog** | Danh mục chương trình đào tạo: toàn bộ môn của 1 ngành, gồm mã môn, tên, tín chỉ, môn tiên quyết… |
| **Curriculum** | Khung chương trình đào tạo (gần nghĩa catalog, nhưng nhấn mạnh khung của nhà trường) |
| **Transcript** | Bảng điểm: danh sách môn sinh viên đã học + điểm |
| **Profile** | Hồ sơ demo: 1 sinh viên giả lập (ngành nào, học kỳ mấy, đã qua môn gì, muốn làm gì) |
| **Eligibility** | Điều kiện được học: môn này bạn *có được phép học* không? |
| **Eligible course** | Môn đủ điều kiện (được phép gợi ý) |
| **Blocked course** | Môn bị chặn (chưa được học, kèm lý do: thiếu tiên quyết, sai track…) |
| **Prerequisite** | Môn tiên quyết: môn phải học *trước* mới được học môn này. Ví dụ: phải qua Toán rời rạc mới học Thuật toán |
| **AND / OR (tiên quyết)** | Nhóm ngoài là AND (phải thỏa *tất cả* nhóm), trong 1 nhóm là OR (chỉ cần *1 trong các môn*). Ví dụ: “(A hoặc B) VÀ C” |
| **Track** | Hướng/học phần chuyên sâu trong ngành (ví dụ hướng Lý thuyết vs Ứng dụng) |
| **Graduation path / branch** | Nhánh tốt nghiệp (ví dụ tốt nghiệp theo hướng nghiên cứu hay thực hành) |
| **Choice group / elective group** | Nhóm môn tự chọn + chỉ tiêu tín chỉ (ví dụ: phải học đủ 12 tín chỉ tự chọn) |
| **Credits (TC)** | Tín chỉ — đơn vị tính khối lượng học |
| **GPA** | Điểm trung bình tích lũy (thang 10 hoặc thang 4) |
| **Preference** | Mong muốn của sinh viên, trích từ câu chat (“muốn học nhẹ, thích thị giác máy tính…”) |
| **Ranking** | Xếp hạng: sắp xếp các môn đủ điều kiện từ hợp nhất đến ít hợp nhất |
| **Score** | Điểm phù hợp từ 0 → 1 (1 là hợp nhất) |
| **Fallback** | Phương án dự phòng: khi AI/LLM lỗi thì dùng cách tính tay, đơn giản nhưng luôn chạy được |
| **Deterministic** | Tất định — cùng đầu vào thì luôn ra cùng kết quả, không ngẫu nhiên |
| **Validation / Validate** | Kiểm tra tính hợp lệ (mã môn có tồn tại không, có trùng không, có phải môn bị chặn không…) |
| **Explanation** | Lời giải thích cho từng môn được gợi ý |
| **Grounded explanation** | Giải thích *dựa trên dữ liệu thật* của backend, không bịa |
| **LLM (Large Language Model)** | Mô hình AI ngôn ngữ lớn (ở đây dùng Gemini). Nó chỉ làm 3 việc: hiểu mong muốn, xếp hạng, viết giải thích |
| **Gemini API** | Cổng gọi AI Gemini của Google (hoặc qua cổng trung gian Beeknoee) |
| **API key** | Chìa khóa bí mật để gọi AI, chỉ giữ ở server, không đưa xuống trình duyệt |
| **Advisor / Chatbot** | Trợ lý chat: nút chat nổi, trả lời câu hỏi gợi ý môn |
| **Guardrail** | Rào chắn: từ chối lịch sự các câu hỏi ngoài phạm vi (xếp thời khóa biểu, đánh giá giảng viên) |
| **Heuristic** | Cách tính theo mẹo/quy tắc đơn giản do người lập trình viết sẵn (không cần AI) |
| **What-if** | Thử giả định: “nếu tôi muốn học nhẹ hơn thì ranking đổi thế nào?” — không sửa hồ sơ thật |
| **Backend / Frontend** | Backend = máy chủ xử lý (Python/FastAPI). Frontend = giao diện web người dùng thấy |
| **Static frontend** | Giao diện web tĩnh (file HTML/JS/CSS, không cần build phức tạp) |
| **Endpoint** | 1 địa chỉ API, ví dụ `POST /recommendations` |
| **Request / Response** | Yêu cầu gửi lên / Phản hồi trả về |
| **Schema / Model (Pydantic)** | Khuôn dữ liệu: quy định 1 object phải có những trường gì, kiểu gì |
| **Repository** | Lớp đọc/ghi dữ liệu (che giấu việc đọc từ JSON hay Postgres) |
| **PostgreSQL (Postgres)** | Hệ quản trị cơ sở dữ liệu quan hệ — nơi lưu catalog + profile khi chạy thật |
| **JSON seed** | File JSON gốc, dùng để kiểm tra và nạp dữ liệu vào database |
| **Migration (Alembic)** | Script nâng cấp cấu trúc database theo phiên bản, chạy bằng `alembic upgrade head` |
| **Docker Compose** | Công cụ chạy database Postgres trong container, không cần cài Postgres tay |
| **Major isolation** | Cô lập ngành: mọi tính toán chỉ dùng đúng 1 ngành đã chọn, không trộn môn ngành khác |
| **Foreign code** | Mã môn lạ — không thuộc ngành đang chọn |
| **Offering status** | Trạng thái mở lớp (kỳ này có mở không). Project luôn trả `unknown` = chưa xác minh |
| **Source status** | Trạng thái nguồn: dữ liệu đã xác minh (`verified`) hay còn nháp (`draft_unverified`) hay xung đột (`source_conflict`) |
| **RAG / Crawler (phần HUS)** | RAG = AI trả lời dựa trên tài liệu tìm được; Crawler = trình thu thập trang web. Phần này mới ở mức kế hoạch |

## 1. Project này làm gì? (kể bằng ví dụ)

Tưởng tượng bạn là sinh viên năm 2 ngành Khoa học dữ liệu:

1. **Chọn ngành:** bạn chọn “Khoa học dữ liệu”.
2. **Nhập bảng điểm:** bạn tick các môn đã qua, ví dụ `MAT1093 Giải tích 1`, `INT1006 Lập trình`.
3. **Xem tiến độ:** hệ thống tính bạn được 20 tín chỉ, GPA 3.2, còn thiếu nhóm tự chọn.
4. **Xem điều kiện học:** hệ thống chia môn thành 2 nhóm:
   - Đủ điều kiện: ví dụ `INT2013 Học máy` (vì bạn đã qua Lập trình).
   - Bị chặn: ví dụ `INT3015 Thị giác máy tính` (vì thiếu `INT2013 Học máy`), kèm lý do rõ ràng.
5. **Chat mong muốn:** bạn gõ “Kỳ này muốn học nhẹ, thích thị giác máy tính”.
6. **Nhận gợi ý:** hệ thống trả 3–5 môn, mỗi môn có: mã, tên, tín chỉ, điểm phù hợp, *lý do đủ điều kiện* + *lý do phù hợp*, và cảnh báo “chưa xác minh môn có mở lớp”.
7. **Hỏi thêm:** nút chatbot nổi để hỏi tiếp (“ưu tiên thực hành hơn thì sao?”).

Điều hệ thống **KHÔNG làm**: xếp thời khóa biểu, xem trùng lịch, đảm bảo môn có mở lớp, đăng ký môn hộ, đoán ngành tự động, dùng điểm thật.

## 2. Công nghệ dùng là gì? (giải thích nôm na)

- **FastAPI (Python):** thư viện viết máy chủ API nhanh. Bạn gửi yêu cầu HTTP → nó chạy hàm Python → trả JSON.
- **Pydantic:** thư viện kiểm tra khuôn dữ liệu. Ví dụ: điểm phải 0–10, mã môn không được rỗng. Sai là báo lỗi ngay.
- **PostgreSQL:** két sắt chứa dữ liệu thật khi chạy (4 ngành, ~290 môn, 12 hồ sơ demo).
- **JSON trong `data/`:** bản gốc để kiểm tra và nạp vào két sắt. Hiện chỉ còn mẫu Data Science để bàn giao nên seed full chưa chạy được.
- **SQLAlchemy + Alembic:** SQLAlchemy là cách Python nói chuyện với Postgres; Alembic là sổ phiên bản cấu trúc database (`upgrade head` = nâng lên bản mới nhất).
- **Docker Compose:** bật Postgres bằng 1 lệnh `docker compose up -d db`, không cần cài đặt lằng nhằng.
- **Frontend tĩnh (`app/static/`):** 1 trang `index.html` + `app.js` + `styles.css`. Không cần React, mở là chạy.
- **Gemini LLM:** AI viết chữ cho hay. Nhưng AI **không được quyết định môn nào đủ điều kiện** — việc đó do code `rules.py` quyết.

## 3. Cấu trúc file và nhiệm vụ từng file

### 3.1 Nhóm khởi động và cấu hình

- **`app/main.py`** — Cửa chính của máy chủ.
  - Tạo app FastAPI, gắn thư mục `static`, gắn các API.
  - Có 3 địa chỉ kiểm tra: `/` (trả trang web), `/health` (máy chủ còn sống không?), `/ready` (database + catalog đã sẵn sàng chưa?).
  - Nếu database mất kết nối → lỗi 503; dữ liệu sai → lỗi 500. Không tự đổi sang JSON lén lút.
  - *Mã giả:* `khởi động → check_storage_ready() → nếu Postgres thì đếm đủ 4 catalog đang active, nếu JSON thì đếm đủ 4 file → gắn routes → chạy`.

- **`app/config.py`** — Đọc cấu hình ở đúng 1 chỗ.
  - Đọc file `.env`: `STORAGE_BACKEND` (dùng `postgres` hay `json`), `DATABASE_URL` (địa chỉ Postgres), `GEMINI_API_KEY/BASE_URL/MODEL` (cấu hình AI).
  - Mặc định là `postgres`. Sai là báo lỗi ngay khi khởi động.

- **`app/errors.py`** — Định nghĩa các loại lỗi: mất kết nối (`StorageUnavailable`), dữ liệu sai (`StorageDataError`), không thấy catalog (`CatalogError`).

### 3.2 Nhóm dữ liệu: khuôn + đọc dữ liệu

- **`app/models.py`** — Khuôn dữ liệu trung tâm (ai cũng dùng chung).
  - `Program`: 1 ngành (mã, tên, tổng tín chỉ, trạng thái, các nhóm tự chọn, track, nhánh tốt nghiệp).
  - `Course`: 1 môn (mã, tên, tín chỉ, khối, `prerequisites` dạng danh sách-trong-danh-sách, nhóm tự chọn, trang nguồn PDF…).
  - `Catalog`: 1 ngành + toàn bộ môn của ngành đó.
  - `StructuredPreference`: mong muốn đã chuẩn hóa (nhẹ/nặng, dễ/khó, lý thuyết/thực hành, chủ đề quan tâm, muốn mấy tín chỉ…).
  - `RecommendationRequest/Response`, `EligibilityResult`, `BlockedCourse`…

- **`app/catalog.py`** — Người gác cổng đọc catalog.
  - Hàm `load_catalog(program_id)` và `list_catalogs()`.
  - *Mã giả:* `nếu xin backend json → đọc file JSON; nếu postgres → hỏi PostgresRepository`.

- **`app/infrastructure/json_catalog_repository.py`** — Đọc catalog từ file `data/curricula/<mã_ngành>.json`. Dùng khi offline.

- **`app/infrastructure/postgres_repository.py`** — Đọc catalog từ Postgres.
  - Đọc `catalog_revisions` đang `active` → đọc `courses` theo thứ tự → ráp tiên quyết (bảng `prerequisite_groups/options`) → ráp nhóm tự chọn → trả về `Catalog` → kiểm tra lại bằng `validate_curriculum_selections`.
  - Hàm `ready()`: thử `SELECT 1` + đếm đủ 4 revision đang active.

- **`app/catalog_validation.py`** — Kiểm tra catalog có hợp lệ không: track/path có trỏ đúng nhóm không, tiên quyết có tạo vòng tròn không, mã môn có trùng không…

- **`app/transcript.py`** — Bảng điểm người dùng nhập tay.
  - `TranscriptRecord`: 1 dòng bảng điểm (mã môn viết hoa, điểm 0–10, kỳ 1–12, đậu/rớt; có điểm thì tự tính đậu nếu ≥ 5).
  - `StudentTranscript`: cả bảng điểm gắn với đúng 1 ngành.
  - Biết tính: môn nào đậu, môn nào rớt, tổng tín chỉ, GPA thang 10, GPA thang 4, và kiểm tra “môn này có thuộc ngành đang chọn không” (`validate_major_isolation`).
  - Có từ điển bí danh ngành `PROGRAM_ALIASES` (gõ `khdl` cũng hiểu là `khdl_7460108_2022`).

- **`app/profiles.py`** — 12 hồ sơ sinh viên giả lập (mỗi ngành 3 hồ sơ).
  - `DemoProfile`: mã profile, ngành, kỳ hiện tại, hướng muốn theo, mục tiêu nghề nghiệp, danh sách môn đã học.
  - `validate_profile()`: kiểm tra gắt — không trùng môn, môn nào cũng phải có kỳ học, kỳ học không vượt quá kỳ hiện tại, môn học sau phải có tiên quyết học ở kỳ *trước đó* (học cùng kỳ không tính), hướng theo phải có trong catalog.

### 3.3 Nhóm luật: ai được học môn nào?

- **`app/rules.py`** — Bộ máy kiểm tra điều kiện (quan trọng nhất, chạy trước AI).
  - Hàm `evaluate_eligibility(catalog, passed_codes, max_credits, track?, path?)`.
  - *Mã giả chi tiết:*
    ```
    1. Kiểm tra ngân sách tín chỉ > 0, mã đã qua phải thuộc ngành này,
       track/path phải tồn tại và hợp nhau.
    2. Tính tín chỉ đã tích lũy cho từng nhóm tự chọn.
    3. Với từng môn trong ngành:
       - Nếu đã qua → cho vào nhóm "hoàn thành", bỏ qua.
       - Nếu nguồn PDF bị xung đột → chặn (source_conflict).
       - Kiểm tra tiên quyết: mỗi nhóm ngoài phải có ít nhất 1 môn đã qua.
         Thiếu nhóm nào → chặn (missing_prerequisites), ghi rõ thiếu môn nào.
       - Nếu chọn track mà môn thuộc track khác → chặn (track_mismatch).
       - Nếu chọn nhánh tốt nghiệp mà môn thuộc nhánh khác → chặn (graduation_path_mismatch).
       - Nếu mọi nhóm tự chọn của môn đều đã đủ chỉ tiêu → chặn (choice_group_full).
       - Nếu 1 môn mà nặng hơn cả ngân sách (ví dụ môn 5 TC mà ngân sách 4 TC) → chặn (credits_exceeded).
       - Không bị gì → cho vào nhóm đủ điều kiện.
    4. Trả về: eligible[], blocked[] (kèm lý do), completed[], số lượng từng loại.
    ```

### 3.4 Nhóm gợi ý: hiểu mong muốn → chấm điểm → giải thích

- **`app/recommendation/preference.py`** — Biến câu chat thành mong muốn có cấu trúc (bản không cần AI, luôn chạy được).
  - *Mã giả:* `bỏ dấu tiếng Việt → tìm từ khóa ("nhẹ"→light, "khó"→advanced, "thực hành"→practice, "thị giác máy tính"→computer_vision…) → tìm số ("6 tín chỉ", "3 môn") → trả về StructuredPreference`.

- **`app/recommendation/scoring.py`** — Chấm điểm từng môn từ 0→1.
  - Ghép chữ của môn (mã + tên + tên tiếng Anh + khối + chủ đề + định hướng) thành 1 đoạn chữ.
  - Đếm chủ đề quan tâm xuất hiện bao nhiêu, loại môn có khớp không, định hướng/độ khó/khối lượng có khớp metadata không (thiếu metadata = 0 điểm, không đoán bừa), cộng điểm trùng từ khóa.
  - Nhân với trọng số (`RankingWeights`: chủ đề 0.6, từ khóa 0.25, loại môn 0.15…) rồi chia trung bình.
  - `fit_reason()`: viết 1 câu vì sao hợp (“tên môn có chứa chủ đề bạn nêu…”, hoặc “chưa đủ metadata để kết luận”).

- **`app/ranking.py`** — `KeywordRanker`: sắp xếp môn theo điểm giảm dần, bằng điểm thì theo mã môn (để luôn tái lập được).

- **`app/recommendation/llm.py`** — `LLMRanker` (bản dùng AI) + `configured_adapters()`: nếu có API key thì dùng AI xếp hạng, không thì dùng `KeywordRanker`.

- **`app/recommendation/validation.py`** — Gác cổng output của AI.
  - *Mã giả:* `nếu output không phải danh sách → bỏ hết + cảnh báo; với từng mã: sai kiểu/không thuộc eligible → bỏ + đếm invalid; trùng → bỏ + đếm duplicate; còn lại giữ`.

- **`app/recommendation/explanation.py`** — Ghép 2 câu: “Đủ điều kiện vì…” (từ backend) + “Phù hợp vì…” (từ điểm số). Không bịa workload, độ khó, lịch mở lớp.

- **`app/service.py`** — Nhạc trưởng `recommend()`, nối tất cả lại:
  ```
  1. Mã ngành phải khớp catalog; mã đã qua phải thuộc ngành.
  2. Chạy/lấy eligibility → chỉ còn môn đủ điều kiện.
  3. Lấy preference (AI hoặc regex, lỗi thì regex + cảnh báo).
  4. Xếp hạng (AI hoặc KeywordRanker, lỗi thì danh sách rỗng + cảnh báo).
  5. Lọc output AI, bổ sung fallback cho đủ.
  6. Đi theo thứ tự xếp hạng, nhặt môn sao cho tổng tín chỉ ≤ max_credits và đủ limit.
  7. Mỗi môn: chấm điểm + viết giải thích + gắn source_status + offering_status=unknown.
  8. Thống kê blocked theo loại + thêm cảnh báo (catalog chưa xác minh, mở lớp chưa xác minh).
  ```

### 3.5 Nhóm chatbot cố vấn

- **`app/advisor.py`** — Chatbot nút nổi.
  - `check_scope_guardrails()`: thấy từ “thời khóa biểu, xếp lịch, trùng tiết” → từ chối TKB; thấy “giảng viên, thầy nào, cho điểm cao” → từ chối đánh giá giảng viên.
  - `chat_advisor()`:
    ```
    1. Ngành phải khớp catalog.
    2. Guardrail trước.
    3. Chạy eligibility (ngân sách 40 TC cho chat).
    4. Trích preference: ưu tiên câu mới nhất, thiếu gì thì lấy từ lịch sử chat.
    5. Dựng facts từ môn eligible (điểm + giải thích tái dùng từ recommendation).
    6. Nếu có API key: dựng prompt (ngành, đã học gì, eligible, preference, facts, blocked mẫu, history)
       → gọi Gemini (qua Beeknoee hoặc Google) → kiểm tra AI có dụ học môn bị chặn không
       → chỉ giữ mã eligible, che mã ngoài catalog → trả lời.
    7. Không key/lỗi mạng → heuristic_advisor: top 4 môn + 2 môn bị chặn mẫu + lời khuyên học môn cơ sở trước.
    ```

### 3.6 Nhóm API và frontend

- **`app/api/routes.py`** — Danh sách địa chỉ API (xem mục 5 bên dưới).
  - Nhiệm vụ: gọi đúng service, đổi lỗi domain thành mã HTTP (không thấy → 404, dữ liệu sai → 422).

- **`app/schemas/`** — Khuôn riêng cho API (mỗi endpoint 1 khuôn request/response, tránh lộ cấu trúc nội bộ).

- **`app/services/`** — Lớp bọc mỏng (`catalog_service`, `transcript_service`, `eligibility_service`, `recommendation_service`, `profile_service`, `advisor_service`) để routes không gọi thẳng domain.

- **`app/db/schema.py` + `session.py`** — Khung bảng Postgres + cách mở kết nối (có pool, tái dùng).

- **`app/static/index.html / app.js / styles.css`** — Giao diện 3 tab + chatbot:
  - Tab 1 Hồ sơ: chọn ngành, chọn profile mẫu, tick môn đã qua, xem tín chỉ + GPA.
  - Tab 2 Điều kiện: danh sách đủ điều kiện / bị chặn + lý do.
  - Tab 3 Gợi ý: nhập mong muốn + số tín chỉ + số môn + trọng số what-if → xem ranking.
  - `app.js` giữ `state`, gọi `fetch()`, đổi ngành là xóa transcript + lịch sử chat.

### 3.7 Nhóm công cụ, database, test, tài liệu

- **`tools/build_catalogs.py`** — Kiểm tra lái catalog: `python -X utf8 tools/build_catalogs.py --check` (không sửa file), thêm `--report` để in chi tiết.
- **`tools/seed_database.py`** — Nạp dữ liệu vào Postgres: kiểm tra 4 catalog + 12 profile → băm thành `revision_id` → nạp trong 1 transaction; chạy lại mà dữ liệu không đổi thì không tạo bản mới.
- **`alembic/` + `docker-compose.yml`** — Phiên bản database + cách bật Postgres local.
- **`tests/`** — Kiểm thử: transcript, luật, gợi ý, advisor, storage, database, dữ liệu chương trình.
- **`docs/`** — `SYSTEM_SPECIFICATION.md` (đặc tả chuẩn), `DATABASE_DESIGN.md` (thiết kế bảng), `CODEBASE_CHECKLIST.md`, `COURSE_METADATA_SPECIFICATION.md`.
- **`modules/README.md`** — Chia việc 9 module theo thứ tự phụ thuộc.

## 4. Các file liên kết với nhau thế nào? (đi theo 1 ví dụ)

Giả sử sinh viên ngành `khdl_7460108_2022`, đã qua `INT1006`, muốn học về thị giác máy tính:

```
index.html/app.js
  → GET /programs → catalog_service.list_catalogs() → PostgresRepository (4 ngành)
  → GET /courses?program_id=khdl... → load_catalog(khdl)
  → tick INT1006 → POST /transcript/summary {program_id, records:[INT1006]}
      → transcript_service → tính earned_credits, GPA, isolation
  → POST /eligibility {program_id, passed:[INT1006]}
      → rules.evaluate_eligibility()
      → INT2013 đủ điều kiện; INT3015 bị chặn vì thiếu INT2013
  → POST /recommendations {program_id, passed:[INT1006], goal:"thích thị giác máy tính, học nhẹ"}
      → service.recommend():
         preference.py trích topic=[computer_vision], workload=light
         scoring.py chấm INT2013 cao hơn vì metadata có computer_vision
         validation.py loại mã lạ
         explanation.py viết lý do
      → trả 3 môn + warnings
  → POST /advisor/chat {message, passed, history}
      → advisor.chat_advisor(): guardrail → eligibility → facts → Gemini/heuristic
```

Đổi ngành giữa chừng → `app.js` xóa `transcript` + `chatHistory`; backend cũng từ chối mã ngành cũ vì `resolve_program_id` không khớp.

## 5. API có những địa chỉ nào? (kèm ví dụ)

- `GET /` → trang web. `GET /health` → `{"status":"ok"}`. `GET /ready` → kiểm tra database.
- `GET /programs` → danh sách 4 ngành + số môn.
- `GET /courses?program_id=khdl_7460108_2022` → toàn bộ môn ngành đó.
- `GET /profiles` / `GET /profiles/{profile_id}` → hồ sơ demo.
- `POST /transcript/summary`:
  ```json
  {"program_id": "khdl_7460108_2022", "records": [{"course_code": "INT1006", "grade": 8.5}]}
  ```
  → trả `earned_credits, gpa, passed_courses, isolation`.
- `POST /eligibility`:
  ```json
  {"program_id": "khdl_7460108_2022", "passed_course_codes": ["INT1006"], "max_credits": 30}
  ```
  → trả `eligible_courses[], blocked_courses[] (kèm reasons), completed[]`.
- `POST /recommendations`:
  ```json
  {"program_id": "khdl_7460108_2022", "passed_course_codes": ["INT1006"],
   "goal": "muốn học nhẹ về thị giác máy tính", "max_credits": 12, "limit": 5}
  ```
  → trả `recommendations[{code,name,credits,rank,score,eligibility_reason,fit_reason}] + warnings + preference`.
- `POST /recommendations/what-if` → giống trên nhưng thêm `ranking_weights`, dùng lại eligibility cũ để so sánh “đổi ý thì ranking đổi thế nào”.
- `POST /advisor/chat`:
  ```json
  {"program_id": "khdl_7460108_2022", "message": "nên học gì kỳ tới?",
   "passed_course_codes": ["INT1006"], "history": []}
  ```
  → trả `reply, mode (gemini_llm/heuristic_fallback/guardrail_rejected), suggested_courses[]`.
- Lỗi: không thấy ngành/profile → 404; mã môn ngoài ngành, track sai, ngân sách sai → 422 với tiền tố máy đọc được (`unknown_passed_course_codes`, `invalid_track_id`…).

## 6. Mã giả tổng hợp (đọc 1 mạch là hiểu pipeline)

```
# Pipeline gợi ý môn
NGUOI_DUNG chon nganh + tich mon da qua + go cau mong muon
CATALOG = load_catalog(nganh)                      # chi lay dung 1 nganh
TRANSCRIPT = StudentTranscript(nganh, records)     # chuan hoa + tinh GPA
ELIG = evaluate_eligibility(CATALOG, mon_da_qua)   # chia du dieu kien / bi chan
PREF = hieu_cau_chat(cau_mong_muon)                # AI hoac regex
UBNG_VIEN = ELIG.du_dieu_kien                      # AI chi duoc nhin thay nhung mon nay
XEP_HANG = rank(UNG_VIEN, PREF)                    # AI hoac KeywordRanker
XEP_HANG_SACH = loc_ma_la_va_trung(XEP_HANG) + fallback
KET_QUA = chon theo ngan sach tin chi + gioi han so mon
MOI_MON: diem = cham_diem(mon, PREF); loi giai thich = ghep(ly do du dieu kien + ly do phu hop)
TRA_VE + canh bao "mo lop chua xac minh"

# Pipeline chatbot
CAU_HOI = nhan tu khung chat
NEU hoi TKB / giang vien -> tu choi lich su
ELIG = evaluate_eligibility(...)                    # tinh lai cho chac
PREF = merge(cau moi nhat + lich su chat)
FACTS = sap xep mon du dieu kien theo diem
NEU co API key: hoi Gemini voi prompt chua FACTS -> kiem tra ma mon -> che ma la -> tra loi
NEU khong: dung heuristic (top 4 + 2 mon bi chan mau)
```

## 7. Chạy thử nhanh

```bash
python -m venv .venv
python -m pip install -r requirements-dev.txt -c requirements-lock.txt
cp .env.example .env   # điền DATABASE_URL, GEMINI_API_KEY, giữ bí mật ở server
docker compose up -d db
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
# mở http://127.0.0.1:8000, tài liệu API ở /docs
python -m ruff check app tests tools alembic
python -m pytest -q
```

> Tình trạng dữ liệu lúc viết tài liệu này: `data/` chỉ còn mẫu Data Science 2022 (65 học phần, envelope mới, chưa seed được). Database local đã seed từ trước vẫn giữ để chạy demo. Test mặc định báo 22 passed / 21 failed (do thiếu catalog cũ) + 11 test Postgres bị bỏ qua nếu chưa đặt `TEST_DATABASE_URL`.

## 8. Phụ lục: toàn bộ file còn lại + luồng + mã giả từng file

> Mục này liệt kê **mọi file** trong repo để bạn không bị sót. Mỗi file có 3 dòng: *làm gì, nhận gì → trả gì, mã giả*.

### 8.1 `app/__init__.py`, `app/api/__init__.py`, `app/services/__init__.py`, `app/db/__init__.py`, `app/infrastructure/__init__.py`, `app/schemas/__init__.py`, `app/recommendation/__init__.py`
- Làm gì: file rỗng hoặc gần rỗng, đánh dấu “đây là 1 package Python” để `import app.xxx` chạy được.
- Luồng: không có logic, chỉ để Python nhận diện thư mục.
- Mã giả: `(không có — file kỹ thuật)`.

### 8.2 `app/errors.py` — 3 loại lỗi dùng chung
- `CatalogError(ValueError)`: xin ngành không tồn tại → API trả 404.
- `StorageUnavailable(RuntimeError)`: không nối được database → API trả 503. Thông điệp không chứa mật khẩu.
- `StorageDataError(RuntimeError)`: nối được nhưng dữ liệu sai/thiếu (ví dụ chưa seed đủ 4 ngành) → API trả 500.
- Mã giả:
  ```
  NGUOI_DUNG xin catalog khong ton tai -> nem CatalogError -> routes bat -> HTTP 404
  Mat ket noi Postgres -> nem StorageUnavailable -> main bat -> HTTP 503
  Du lieu sai/thieu -> nem StorageDataError -> main bat -> HTTP 500
  ```

### 8.3 `app/catalog_validation.py` — Kiểm tra khung chương trình
- Hàm `validate_curriculum_selections(program, course_codes)`:
  - Nhóm tự chọn không trùng; track không trùng và chỉ trỏ nhóm có thật; nhánh tốt nghiệp không trùng, chỉ chứa môn/track có thật.
- Luồng: được gọi cuối `load_catalog` ở cả 2 backend (JSON và Postgres). Sai là chặn ngay, không cho chạy tiếp.
- Mã giả:
  ```
  NHAN program + tap ma mon
  NEU trung group/track/path -> nem loi
  NEU track tro nhom khong ton tai -> nem loi
  NEU path chua mon/track khong ton tai -> nem loi
  XONG -> khong tra gi (im lang la dat)
  ```

### 8.4 `app/recommendation/llm.py` — Cắm AI vào pipeline gợi ý
- `LLMPreferenceExtractor(provider)`: bọc hàm gọi AI thành `extract(goal) -> StructuredPreference` (có validate Pydantic).
- `LLMRanker(provider)`: bọc hàm gọi AI thành `rank(candidates, goal, preference, weights)`. Nó đóng gói danh sách môn + preference/weights thành JSON rồi đưa cho AI, AI chỉ trả về thứ tự mã môn.
- `_parse_json_response`: gỡ markdown ```json, cắt đúng đoạn JSON đầu–cuối để `json.loads` không vỡ khi AI nói dông dài.
- `_llm_text(prompt)`: nếu `GEMINI_BASE_URL` là cổng Beeknoee/OpenAI-compatible → gọi `/chat/completions`; nếu không → gọi Google `generateContent`. Hết 20 giây không trả → lỗi → fallback.
- `configured_adapters()`: nếu tắt LLM hoặc thiếu key → trả `(None, None)` (dùng regex + KeywordRanker). Chỉ tạo hàm, không gọi mạng lúc import.
- Mã giả:
  ```
  FUNC configured_adapters():
    NEU tat LLM hoac thieu key: RETURN (None, None)
    DINH NGHIA preference_provider(goal): prompt "chi tra JSON preference" -> goi AI -> lay phan preference
    DINH NGHIA ranking_provider(danh sach mon, context): prompt "chi tra array {code}" -> goi AI -> boc tach ranking
    RETURN (LLMPreferenceExtractor, LLMRanker)
  ```

### 8.5 `app/infrastructure/json_catalog_repository.py` — Đọc catalog từ file
- `DATA_ROOT = data/curricula`. Mỗi ngành là 1 thư mục con chứa `curriculum.json` (thông tin ngành) + `courses.json` (danh sách môn).
- `load_catalog(program_id)`: chuẩn hóa bí danh → kiểm tra thư mục tồn tại → đọc 2 file → validate → kiểm tra `program_id` khớp tên thư mục, không trùng mã môn, nhóm tự chọn có thật.
- `list_catalogs()`: liệt kê mọi thư mục con rồi gọi `load_catalog` từng cái.
- Mã giả:
  ```
  FUNC load_catalog(ma_nganh):
    ma = resolve_program_id(ma_nganh)          # "khdl" -> "khdl_7460108_2022"
    NEU khong co thu muc ma: nem CatalogError (404)
    DOC curriculum.json -> Program; DOC courses.json -> list[Course]
    LOI doc/JSON/schema -> nem StorageDataError (500)
    validate_curriculum_selections(...)
    NEU trung ma mon hoac nhom sai -> nem StorageDataError
    RETURN Catalog(program, courses)
  ```

### 8.6 `app/db/session.py` — Mở kết nối database
- `engine_for_url(url)`: tạo engine SQLAlchemy có cache, pool 5 + tràn 5, `pool_pre_ping` (kiểm tra kết nối trước khi dùng), timeout 5 giây, giấu tham số (không in mật khẩu vào log).
- `get_engine()`: lấy `DATABASE_URL` từ settings rồi gọi hàm trên.
- Mã giả: `CAN engine: doc DATABASE_URL -> tao engine co pool -> cache lai -> tra ve`.

### 8.7 `app/db/schema.py` — Khung bảng database (236 dòng)
- Bảng: `programs` (ngành) → `catalog_revisions` (phiên bản catalog, mỗi ngành chỉ 1 bản `active`) → `courses` (môn, khóa chính gồm `revision_id + code`) → `prerequisite_groups/options` (nhóm AND + lựa chọn OR), `choice_group_courses` (môn thuộc nhóm tự chọn nào), `demo_profiles` + `transcript_records` (12 hồ sơ demo).
- Khóa ngoại kép `(revision_id, code)` để môn ngành A không bao giờ trỏ sang môn ngành B (cô lập ngành ngay trong database). Tiên quyết ngoài catalog lưu `external_code` + trạng thái chưa xác minh, không dùng để mở khóa. Chi tiết nguồn giữ trong cột JSON/JSONB, không suy diễn lại.
- Mã giả: `(định nghĩa bảng — không có hàm chạy, Alembic dùng metadata này để so drift)`.

### 8.8 Nhóm `app/services/*` — Lớp bọc mỏng (mỗi file vài dòng)
- `catalog_service.py`: tái xuất `load_catalog, list_catalogs`.
- `transcript_service.py`: tái xuất `StudentTranscript`.
- `eligibility_service.py`: tái xuất `evaluate_eligibility, eligible_courses`.
- `recommendation_service.py`: tái xuất `recommend`.
- `profile_service.py`: tái xuất `list_profiles, load_profile`.
- `advisor_service.py`: tái xuất `chat_advisor, check_scope_guardrails, AdvisorRequest/Response`.
- Vì sao tồn tại: để `routes.py` chỉ nói chuyện với `services`, sau này đổi logic nội bộ không phải sửa API. Mã giả: `NHAN giong domain -> UY THAC cho ham domain -> TRA VE nguyen`.

### 8.9 Nhóm `app/schemas/*` — Khuôn riêng của API
- `catalog.py`: `ProgramCatalogMetadata` (thông tin ngành + `course_count`), `Course`.
- `eligibility.py`: `EligibilityRequest/Result` cho endpoint `/eligibility`.
- `recommendation.py`: `RecommendationRequest/WhatIfRequest/Response` cho 2 endpoint gợi ý.
- `profile.py`: `ProfileSummary/Detail/TranscriptSummary` cho các endpoint profile/transcript.
- `advisor.py`: `AdvisorRequest/Response` cho `/advisor/chat`.
- `transcript.py`: `StudentTranscript` bản API.
- Luồng: routes nhận JSON → Pydantic validate theo schema → gọi service → gói kết quả lại theo schema response. Mã giả: `JSON vao -> validate kieu/gioi han -> goi service -> validate dau ra -> JSON ra`.

### 8.10 `tools/build_catalogs.py` — Kiểm tra/tái tạo catalog
- Đọc dòng nguồn, kiểm tra mã trùng, tiên quyết vòng tròn, track/path/nhóm, rồi có thể ghi lại 4 file catalog.
- Lệnh: `--check` (chỉ kiểm tra), `--check --report` (in chi tiết), `--write` (ghi lại — cấm chạy trên mẫu bàn giao hiện tại).
- Mã giả:
  ```
  DOC tung source row -> GOM theo nganh
  KIEM TRA trung ma, tien quyet la, track/path/nhom
  NEU --check: bao dat/hong, khong ghi file
  NEU --write: ghi curriculum.json + courses.json (dang cam voi mau hien tai)
  ```

### 8.11 `tools/seed_database.py` (312 dòng) — Nạp dữ liệu vào Postgres
- `check_curriculum()` từng ngành → băm `program + courses + sources + profiles` thành `revision_id` → mở 1 transaction: chèn `catalog_revisions(active=False)`, `courses`, tiên quyết, nhóm, profile → nếu dữ liệu giống cũ thì giữ, nếu khác thì tạo revision mới và đổi cờ `active` trong cùng transaction (idempotent = chạy lại không tạo rác).
- Hàm `_insert`, `_seed_revision` là thợ phụ chèn từng bảng.
- Mã giả:
  ```
  FOR moi nganh trong 4 JSON:
    validate catalog + profile
    revision_id = hash(noi dung)
    NEU revision da ton tai: BO QUA
    NGUOC LAI: trong 1 TRANSACTION: chen revision + mon + tien quyet + nhom + profile, bat active ban moi
  ```

### 8.12 Nhóm `tests/` — Kiểm thử
- `conftest.py`: ép test chạy offline — `STORAGE_BACKEND=json`, xóa key, chặn mọi HTTP thật (ai gọi mạng là fail), xóa cache settings trước/sau mỗi test.
- `test_transcript.py`: chuẩn hóa mã, điểm ≥ 5 là đậu, GPA, cô lập ngành.
- `test_rules.py`: tiên quyết AND/OR, track/path, nhóm đủ chỉ tiêu, ngân sách tín chỉ, tỷ lệ vi phạm eligibility = 0.
- `test_recommendations.py`: preference regex, chấm điểm, loại mã lạ/trùng, fallback khi LLM hỏng, what-if không mở khóa môn.
- `test_advisor.py`: guardrail TKB/giảng viên, heuristic fallback, che mã ngoài catalog.
- `test_storage.py` + `test_database.py`: JSON repo đọc đủ 4 catalog; Postgres repo cần `TEST_DATABASE_URL`, chỉ tạo/xóa schema ngẫu nhiên `se_test_*`.
- `test_curriculum_data.py`: 4 JSON catalog hợp lệ (hiện fail vì `data/` chỉ còn mẫu mới).
- Mã giả chung: `DUNG fixture catalog gia -> GOI ham -> ASSERT ket qua dung + khong co mon cam lot`.

### 8.13 Nhóm `alembic/` — Phiên bản database
- `alembic.ini`: file cấu hình (database URL lấy từ settings, thư mục versions).
- `env.py`: nối Alembic với `app.db.schema.metadata` để `alembic check` phát hiện lệch.
- `script.py.mako`: khuôn tạo migration mới.
- `schema_v1.py`: ảnh chụp schema v1 để đối chiếu.
- `versions/20261014_01_initial.py`: migration thay bảng legacy bằng schema versioned (đã chạy sau khi backup `backups/se_project_before_pg_v2_20261014.dump`).
- Mã giả: `alembic upgrade head -> mo ket noi -> chay migration con thieu theo thu tu -> ghi vao bang alembic_version`.

### 8.14 Nhóm gốc: `docker-compose.yml`, `pyproject.toml`, `requirements*.txt`, `alembic.ini`, `.env.example`
- `docker-compose.yml`: chạy Postgres 16 (`se_recommender_db`, user/pass/db lấy từ `.env`, mở cổng `127.0.0.1:5432`, volume `se_recommender_pgdata` giữ dữ liệu, healthcheck `pg_isready`). Chỉ chạy database, backend chạy bằng Python riêng.
- `pyproject.toml`: pytest tìm test trong `tests/`; ruff kiểm tra Python 3.11, dài dòng 100 ký tự.
- `requirements.txt` / `requirements-dev.txt` / `requirements-lock.txt`: thư viện chạy / làm dev / khóa phiên bản.
- `.env.example`: mẫu không-bí-mật (`DATABASE_URL`, `STORAGE_BACKEND`, `GEMINI_*`, `POSTGRES_*`). `.env` thật không bao giờ commit.
- Mã giả vận hành: `docker compose up -d db -> alembic upgrade head -> uvicorn app.main:app -> /ready phai ok`.

### 8.15 Nhóm web tĩnh còn lại: `index.html`, `styles.css`, `favicon.svg`
- `index.html`: khung 3 tab (hồ sơ / điều kiện / gợi ý) + nút chatbot nổi + select ngành/profile/track/nhánh + checklist môn + form gợi ý + khung chat.
- `app.js` (~1021 dòng): `state` toàn cục → `api()` bọc fetch + báo lỗi tiếng Việt → `initTabs()` chuyển tab → tải programs/profiles/courses → render checklist/KPI/eligible/blocked/recommendations → gửi chat kèm history → nút what-if đổi trọng số → đổi ngành thì xóa transcript + chat.
- `styles.css` + `favicon.svg`: trang trí + icon (không logic).
- Mã giả `app.js`:
  ```
  KHOI DONG: GET /programs -> do vao select nganh
  CHON NGANH: xoa transcript + chat -> GET courses + profiles cua nganh -> render checklist
  TICK MON: POST /transcript/summary -> ve KPI (tin chi, GPA)
  NUT DIEU KIEN: POST /eligibility -> ve 2 cot du dieu kien / bi chan
  NUT GOI Y: POST /recommendations -> ve the mon + diem + ly do + canh bao
  NUT WHAT-IF: POST /recommendations/what-if voi weights moi -> ve lai de so sanh
  CHAT: POST /advisor/chat {message + passed + history} -> them bong chat -> luu history (toi da 8)
  ```

### 8.16 Nhóm dữ liệu mẫu: `data/curricula/khdl_7460108_2022/*`
- `README.md`: hướng dẫn bàn giao mẫu.
- `curriculum.json`: thông tin ngành (tên, tổng tín chỉ, nhóm/track/nhánh).
- `courses.json`: 65 học phần (mã, tên, tín chỉ, khối, tiên quyết…).
- `source_rows.json`: dòng sao chép từ PDF nguồn (giữ trang nguồn, trạng thái).
- `vocabulary.json`: từ điển chủ đề (computer_vision, machine_learning…) để preference/scoring hiểu câu “thị giác máy tính”.
- Luồng: `source_rows` → `build_catalogs` → `curriculum/courses` → `seed_database` → Postgres. Hiện envelope mẫu mới chưa tương thích loader cũ nên không seed được.

### 8.17 Nhóm tài liệu và kế hoạch: `docs/*`, `modules/*`, `KE_HOACH_DU_AN.md`, `SE_Project.pdf`, `README.md`, `AGENTS.md`
- `docs/SYSTEM_SPECIFICATION.md`: đặc tả pipeline chuẩn (nguồn đúng nhất).
- `docs/DATABASE_DESIGN.md`: thiết kế revision, khóa ngoại kép, JSONB.
- `docs/COURSE_METADATA_SPECIFICATION.md`: hợp đồng metadata mục tiêu (topics, workload…).
- `docs/COURSE_SELECTION_REASONS.md`: lý do chọn môn mẫu.
- `docs/CODEBASE_CHECKLIST.md`: checklist hạ tầng, milestone nào xong khi test nào pass.
- `modules/01..09`: đặc tả trách nhiệm từng module (catalog → transcript/profile → eligibility → preference/ranking/what-if → explanation/validation → advisor → API → web UI → OCR planned). Đây là tài liệu chia việc, không phải bằng chứng đã làm xong.
- `KE_HOACH_DU_AN.md` + `SE_Project.pdf`: kế hoạch/bối cảnh lịch sử, tham khảo.
- `README.md` (gốc) + `data/README.md`: trạng thái dữ liệu thật hiện tại.
- `AGENTS.md` → trỏ sang `.agent/AGENTS.md`: luật cộng tác (dùng JSON seed versioned, Postgres mặc định, toolkit local-only, commit kèm `Co-authored-by`, báo tiến độ %, test/repro, không commit secret).

