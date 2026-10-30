# Risk-based strategy và test design

Risk chính R1: breaking schema/API làm hỏng consumer cũ; R2: nondeterministic
pagination; R3: swallowed exception giả empty success; R4: phạm vi ngành/metadata;
R5: quá tải. Highest priority R1/R3 (contract), sau đó R2/R4 (API + unit).
Không dùng snapshot tự sinh từ output production. Oracle là danh sách mã/chữ/tín
chỉ cố định thiết kế trước patch, và baseline response Course công bố.

| ID | AC/risk | Level | Preconditions/input | Expected | Priority |
|---|---|---|---|---|---|
| TC01 | AC04/R1 | consumer contract | request cũ chỉ program_id | list đủ 8 môn, nguyên input order, fields/types/nullable/extras | P0 |
| TC02 | AC01/R4 | API | q ` DATA `, block major, elective | C02,C04; giữ draft flags | P1 |
| TC03 | AC01 | API | q tên VI/EN/code, case variants | mã literal định sẵn | P1 |
| TC04 | AC02/R1 | provider contract | query defaults | envelope đúng keys/types, total8/page1/size20, code tăng | P0 |
| TC05 | AC02/R2 | API | 8 rows, size3, pages1..3 | 3+3+2, ghép C01..C08 không trùng/mất | P0 |
| TC06 | AC03/R2 | API/unit | sort credits và name, tie rows; reversed input | đúng order có code tie-breaker | P0 |
| TC07 | AC02 | API | page4 size3 và q không khớp | empty hợp lệ, total lần lượt8/0 | P1 |
| TC08 | AC02/R1 | negative API | page0/-1/nonint; size0/101 | 422 detail list xác định query field | P0 |
| TC09 | AC01/R1 | negative API | enum sai, q>120, thiếu program | 422 không âm thầm bỏ query sai | P0 |
| TC10 | AC05/R3 | failure contract | load_catalog raise StorageUnavailable | 503 JSON detail string, không items/default | P0 |
| TC11 | AC05/R3 | failure contract | StorageDataError / unexpected RuntimeError | 500, không default success/không lộ internals | P0 |
| TC12 | AC04/05/R1 | contract | unknown program, missing required, legacy outage | 404/422/503/500 giữ semantics | P0 |
| TC13 | AC01/R4 | API | hai program khác nhau cùng route | chỉ môn program đó, canonical program_id | P1 |
| TC14 | AC01 | API | q `%`, literal accent, blank; unknown block | literal match/trim, không SQL wildcard | P1 |
| TC15 | AC03/R2 | unit | calls nhiều lần filter/page/sort trên cùng object | catalog không bị mutate, order lặp lại | P1 |
| TC16 | AC02 | boundary API | size1/100, page rất lớn | đúng page metadata/slice; không cap total | P1 |
| TC17 | NFC01/R5 | HTTP load | 100 worker barrier, warm-up, 6000 measured | 0 error/violation, p95≤3000ms | P1 |
| TC18 | AC01..04 | browser/API smoke | Chromium fetch actual local endpoints | legacy list + filtered search envelope đúng | P1 |

Fixture: 8 học phần giả C01..C08, input cố ý đảo; nhiều credits=3, hai tên cùng
casefold, name_en=None, có metadata mở rộng/unknown, block general/major,
requirement_type required/elective/required_excluded/graduation; program khác F01.
Benchmark dùng 240 mã S0000..S0239, hai block và parity-based type, từng 3 môn
trùng name, credits theo modulo. Oracle closed-form, không gọi production service.

Unit kiểm sort và immutability. API tích hợp real router/model/handler; loader
thay bằng controlled Catalog để injection lỗi và đổi order. Contract kiểm request
legacy + toàn bộ schema needed + new envelope + status/errors (không chỉ 200).
HTTP harness bổ sung actual JSON file repository, socket HTTP và serialization;
browser smoke dùng fetch không mock route. Không E2E login VNU/real DB vì public
catalog slice không đổi auth/storage schema; PostgreSQL-specific test không cần
để chứng minh pure search logic. Không khẳng định harness chứng minh performance
PostgreSQL, academic correctness, official university data hoặc UI tìm kiếm mới.
Các job PostgreSQL CI vẫn để chạy remote trên DB test cô lập nếu publication được.
