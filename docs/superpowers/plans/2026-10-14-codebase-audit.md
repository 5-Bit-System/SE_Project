# Rà soát codebase và thứ tự chỉnh sửa

Ngày: 2026-10-14. Phạm vi: đọc mã nguồn, đối chiếu memory/đặc tả, kiểm tra offline và lập kế hoạch bằng project-toolkit/writing-plans. Không sửa implementation, seed, migration, database hay dữ liệu bàn giao.

## Kết luận

Codebase có nền tảng FastAPI, storage adapters, PostgreSQL/Alembic, transcript, eligibility AND/OR, ranking/fallback và chatbot nổi. Vấn đề lớn nhất là hợp đồng metadata mới chưa đi vào runtime và test còn phụ thuộc bộ dữ liệu đã được chủ động xóa. Ngoài điểm này, có lỗi logic tái hiện được ở scoring, tổng tín chỉ, giới hạn recommendation và kiểm tra lời khuyên chatbot; có rủi ro phản hồi cũ trên frontend. HUS RAG và một số hành vi trong đặc tả chưa triển khai.

## Kiểm tra đã thực hiện

| Kiểm tra | Kết quả hiện tại |
|---|---|
| `.venv/Scripts/python.exe -m pytest -q` | 22 passed, 21 failed, 11 skipped; lỗi chủ yếu là thiếu catalog/profile và định dạng envelope |
| `.venv/Scripts/python.exe -m ruff check app tests tools alembic` | Đạt; cấu hình hiện chỉ bật nhóm lỗi cú pháp/runtime E9/F63/F7/F82 |
| `.venv/Scripts/python.exe -X utf8 tools/build_catalogs.py --check` | Thất bại: `Catalog differs from source transcription` ở mẫu KHDL |
| `.venv/Scripts/python.exe project-toolkit/scripts/sources.py --check` | 3 repository pinned, 12 skill nguyên vẹn |
| PostgreSQL, browser thật, API model thật, CI remote | Chưa kiểm chứng trong lần rà soát này |

Không suy từ 21 test lỗi thành 21 lỗi sản phẩm độc lập. Không suy từ các bài kiểm tra PostgreSQL bị skip thành database hiện tại bị hỏng. Không dùng kết quả 54/54 lịch sử làm trạng thái hiện hành.

## Vấn đề có bằng chứng

P0: chặn khả năng tái lập từ clone. P1: sai kết quả hoặc làm yếu invariant. P2: thiếu tính năng/chất lượng theo đặc tả. Các mức này không phải chứng nhận mức độ hoàn thiện sản phẩm.

| ID | Mức | Vấn đề và tác động | Bằng chứng trong code | Kế hoạch |
|---|---|---|---|---|
| D01 | P0 | JSON loader đọc `courses.json` như list trong khi mẫu là envelope; API offline có thể trả 500 | `app/infrastructure/json_catalog_repository.py:35`; test catalog/advisor/transcript lỗi | A1 |
| D02 | P0 | Schema prerequisite chỉ nhận `transcribed/source_conflict`; metadata mới có năm trạng thái, evidence/vocabulary chưa được kiểm tra đầy đủ | `app/models.py:55`, `app/catalog_validation.py` | A1–A2 |
| D03 | P0 | Builder tái tạo định dạng cũ; `--write` có nguy cơ ghi đè metadata tư vấn/evidence | `tools/build_catalogs.py:73`, `:213`; `--check` thất bại | A2 |
| D04 | P0 | Seed bắt buộc 4 ngành và 12 profile; dữ liệu hiện chỉ 1 mẫu, không có profile. Fresh clone chưa tái lập được demo đầy đủ | `tools/seed_database.py:215`, `app/profiles.py`; `data/` | A3–A4 |
| D05 | P0 | Test và CI vẫn yêu cầu dataset cũ; job offline chạy builder lỗi trước pytest, job PostgreSQL cũng dùng fixtures nguồn đã mất | `.github/workflows/checks.yml`, `tests/test_curriculum_data.py`, `tests/test_database.py` | A4 |
| R01 | P1 | Topic snake_case không match đúng chính nó: `computer_vision` được biến thành chuỗi có khoảng trắng nhưng metadata còn dấu `_` | `app/recommendation/scoring.py:49`; reproduction score = 0.0 | B1 |
| R02 | P1 | Fallback extraction không thống nhất vocabulary: “cơ sở dữ liệu” sinh cả `data` và `databases`, trong đó `data` không thuộc bộ nhãn chuẩn; phủ định bị hiểu sai | `app/recommendation/preference.py`; “không muốn khó” → `advanced` | B1 |
| R03 | P1 | `target_credits/target_course_count` được parse nhưng selection chỉ dùng request `max_credits/limit`; “1 môn” trả 2 trên fixture 2 môn | `app/service.py:103`, `app/models.py:89` | B2 |
| R07 | P2 | Default weights của orientation/difficulty/workload đều bằng 0; kể cả có metadata, yêu cầu “nhẹ/thực hành” không tác động các thành phần này nếu client không đặt weights | `app/models.py:RankingWeights`, `app/recommendation/scoring.py` | B2 |
| R04 | P1 | Tín chỉ tích lũy bỏ qua `counted_in_total=false` nếu môn không có trong danh sách loại trừ cấp chương trình | `app/transcript.py:139`; reproduction môn 3 TC bị loại vẫn cộng 3 | A5 |
| R05 | P1 | Chat trả văn bản tự do, validation dựa regex mã và động từ cùng dòng; lời khuyên nhiều dòng hoặc chỉ tên môn có thể vượt kiểm tra | `app/advisor.py:174`; “Bạn nên đăng ký:\n- MAT9999” với MAT9999 blocked → không bị phát hiện | B3 |
| R06 | P1 | Chat fallback không luôn thêm cảnh báo nguồn/mở lớp; nhánh chat không đi qua cùng bước extraction/ranking LLM có cấu trúc như endpoint recommendations | `app/advisor.py:270`, `chat_advisor`; fallback có facts an toàn nhưng chưa có cùng contract | B3 |
| U01 | P1 | Courses/profiles/summary/eligibility/chat chưa chặn response cũ sau đổi ngành/hồ sơ; chat cũ có thể ghi vào history mới | `app/static/app.js:158`, `:225`, `:264`, `:425`, chat submit khoảng `:873` | C1 |
| U02 | P1 | Chỉ reset mảng chatHistory khi đổi ngành, chưa xóa toàn bộ chat DOM, courses/KPI/eligibility cũ ngay lập tức; request invalidation có thể để nút disabled | `onProgramChanged`, `clearRecommendationResults`, `finally` của recommendation/what-if | C1 |
| U03 | P1 | Một số trường catalog/reason đưa thẳng vào `innerHTML`; dữ liệu nhập tương lai có thể bị trình duyệt diễn giải thành HTML | `app/static/app.js:496`, `:522`; đây là rủi ro tĩnh, chưa thử khai thác browser | C2 |
| F01 | P2 | Explanation recommendation hiện là template deterministic, chưa có adapter LLM explanation và validation grounded | `app/recommendation/explanation.py` | B4 |
| F02 | P2 | Không có contract hỏi làm rõ khi mong muốn mơ hồ; career goal/prerequisite tolerance được lưu nhưng chưa có chiến lược sử dụng rõ ràng | `StructuredPreference`, `preference.py`, `service.py`, `scoring.py` | B2–B4 |
| F03 | P2 | What-if tính lại theo request hiện tại, không có baseline fingerprint/rank delta để so sánh trước–sau | `app/api/routes.py:166`, `handleWhatIf` | C3 |
| F04 | P2 | Progress chỉ có tổng môn/TC/GPA; chưa trả thiếu hụt theo nhóm/track/path | `app/schemas/profile.py`, `app/transcript.py`, frontend KPI | A5 |
| F05 | P2 | HUS Q&A chưa có router, allowlist, crawl/clean/chunk/index, retrieval và citation; endpoint chat hiện luôn nạp catalog | `app/api/routes.py:249`, toàn bộ danh mục `app/` | D1–D3 |
| M01 | P2 | `schemas/*`, `services/*` nhiều file mới chỉ re-export implementation cũ; ownership còn tập trung ở models/advisor/service | `app/services/recommendation_service.py`, `app/services/advisor_service.py`, `app/schemas/catalog.py` | Chỉnh ở B3 khi thật sự cần; không refactor toàn repo trước sửa lỗi |
| M02 | P2 | Provider HTTP có hai implementation riêng, alias model chỉ được xử lý ở advisor; dễ lệch cấu hình/fallback | `app/advisor.py:call_gemini_api`, `app/recommendation/llm.py:_llm_text` | B3 |
| DATA | Phụ thuộc | 3 catalog bị xóa có chủ đích; PDF gốc không nằm trong repo; metadata tư vấn mẫu còn null vì thiếu bằng chứng | `data/curricula/khdl_7460108_2022/README.md`, memory | Gói dữ liệu riêng sau khi người dùng cung cấp/yêu cầu; không tự phục hồi |

## Thứ tự triển khai đề xuất

1. [A — Metadata/runtime và nền kiểm thử](2026-10-14-metadata-runtime-plan.md): A1/A2/A4 trước để test không phụ thuộc dataset đã xóa; A3 kiểm chứng PostgreSQL trên fixtures riêng; A5 sửa progress/tín chỉ.
2. [B — Recommendation và chat](2026-10-14-recommendation-chat-plan.md): B1/B2 có thể kiểm tra trên catalog giả lập nhỏ; B3 đóng lỗ hổng văn bản tự do trước thêm explanation LLM.
3. [C — Frontend và What-if](2026-10-14-frontend-plan.md): C1/C2 có thể bắt đầu sớm với API mock; C3 dùng contract ổn định của A/B.
4. [D — HUS RAG](2026-10-14-hus-rag-plan.md): triển khai độc lập sau khi pipeline tư vấn an toàn; cần tập URL/nội dung đúng phạm vi đã xác minh để nghiệm thu nội dung thật.

Ưu tiên đầu tiên: runtime nhận đúng mẫu metadata, kiểm thử tái lập độc lập và đóng các lỗi P1. Không cần đợi hoàn thiện bốn catalog để kiểm tra logic bằng fixtures tổng hợp, nhưng demo bốn ngành chỉ nghiệm thu khi có bốn catalog và 12 profile hợp lệ.

## Giới hạn và điều kiện nghiệm thu

- Giữ FastAPI/static frontend/PostgreSQL; không thêm login, dữ liệu sinh viên thật, roadmap bốn năm hoặc tự đoán ngành.
- Không dùng tên môn/tín chỉ để bịa workload, difficulty, topics hoặc nghề nghiệp.
- Không xóa/sửa dữ kiện nguồn để đưa test về xanh; không skip test hồi quy nghiệp vụ chỉ để che lỗi.
- Test đơn vị và integration dùng fixture tổng hợp nhỏ riêng trong `tests/fixtures/`, không tái tạo catalog đã xóa dưới `data/`.
- Smoke/integration PostgreSQL chỉ trên URL test rõ ràng và schema `se_test_*`; chưa cho phép seed database hiện hành bởi tài liệu kế hoạch này.
- Các bảng audit recommendation, tài khoản, chat persistence, embedding/vector DB không phải điều kiện bắt buộc của đợt sửa này.
- Từng task được nghiệm thu bằng test đã ghi trong kế hoạch; toàn bộ sản phẩm vẫn cần kiểm tra dataset đầy đủ, browser và nội dung HUS thật riêng.

Các kế hoạch đã được tự rà soát về phạm vi, đường dẫn, interface, invariant eligibility và các tình huống đầu vào. Chưa thực hiện các task implementation.
