# Bản chia việc cho nhóm 5 người

Mỗi người nhận các đầu việc lập trình, một phần dữ liệu để review, kiểm thử phần mình và review code của một bạn khác. Bốn bảng đã được số hóa đầy đủ ngày 07/10/2026; công việc dữ liệu tiếp theo là đối chiếu và xử lý ghi chú nguồn. [Module](../modules/README.md) là thành phần hệ thống, không phải phần việc độc quyền của một người. Điền tên thật vào bảng trước khi tạo nhánh.

## Phân công theo đầu việc

Chưa có danh sách tên đầy đủ nên dùng Người 1–5 để điền tên. Người chịu trách nhiệm merge: ______. Các đường dẫn trong bảng là code đang có; cấu trúc `app/modules/` trong [đặc tả hệ thống](../modules/README.md) là mục tiêu, chưa refactor. Nếu chuyển code sang package, cả nhóm thống nhất đường dẫn mới trước khi tách nhánh tính năng.

| Người | Tên | Đầu việc chính ban đầu | Phạm vi thay đổi ban đầu | Nhánh theo task |
|---|---|---|---|---|
| 1 | ______ | Báo lỗi catalog rõ ràng, bổ sung kiểm tra và test dữ liệu | `app/catalog.py`, `tools/build_catalogs.py`, test catalog | `feat/catalog-validation` |
| 2 | ______ | Kiểm tra hồ sơ đầu vào, thông báo lỗi và test API | `app/models.py`, `app/main.py`, `app/service.py`, test API | `feat/profile-validation` |
| 3 | ______ | Hoàn thiện điều kiện học, quota và lý do môn bị loại | `app/rules.py`, test luật | `feat/eligibility-rules` |
| 4 | ______ | Adapter LLM, timeout, parse kết quả và test mock | `app/ranking.py`, adapter mới, test ranker | `feat/llm-ranking` |
| 5 | ______ | Form hồ sơ, hiển thị kết quả/cảnh báo và test luồng UI | `app/static/`, checklist UI | `feat/profile-form` |

Đây là đầu việc để khởi động song song, không phải quy định một người sở hữu một module. Khi xong task, mỗi người tiếp tục nhận phần phối hợp dưới đây. Người giữ quyền merge vẫn nhận task lập trình và có người khác review trước khi merge.

## Công việc cụ thể của từng người

### Người 1 — Dữ liệu, catalog và API đọc danh sách môn

- **P1-01:** Bổ sung xử lý lỗi file thiếu, JSON sai và dữ liệu không hợp lệ trong `app/catalog.py`; giữ việc chọn ngành theo các thư mục hợp lệ, không nhận đường dẫn tùy ý từ người dùng.
- **P1-02:** Hoàn thiện kiểm tra catalog trong `tools/build_catalogs.py`: mã môn duy nhất, nhóm tồn tại, độ phủ nguồn và xung đột tiên quyết. Không tự sửa mâu thuẫn của PDF bằng phỏng đoán.
- **P1-03:** Chuẩn bị hợp đồng dữ liệu cho `GET /programs`, `GET /courses?program_id=...`; cùng Người 2 test status/response, cùng Người 5 test đổi ngành trên UI. Router thuộc Catalog khi thực hiện refactor.
- **P1-04:** Viết `tests/test_catalog.py` (cần tạo), bổ sung `tests/test_curriculum_data.py`; review phần PDF trong bảng dữ liệu bên dưới.

**Đầu ra:** loader/validator, test catalog và ví dụ response danh sách ngành/môn. **Đạt khi:** nạp được cả bốn catalog riêng, phát hiện dữ liệu sai và không gộp môn khác ngành. **Review code:** Người 2.

### Người 2 — Kiểm tra hồ sơ, API gợi ý và điều phối kết quả

- **P2-01:** Tách rõ phần kiểm tra hồ sơ: ngành hợp lệ, môn đã qua thuộc ngành, xử lý mã lặp, mục tiêu và giới hạn TC. Hiện sửa `app/models.py`/`app/service.py`; mục tiêu là `profile/service.py` và `schemas.py` trong cấu trúc module.
- **P2-02:** Giữ hợp đồng `POST /recommendations`, xử lý lỗi 404/422 và request/response; đăng ký router trong `app/main.py` khi các module được tách package. Không bổ sung đăng nhập hoặc lưu hồ sơ ngoài phạm vi.
- **P2-03:** Viết guard trong `app/service.py`: chặn mã lạ, trùng, ngoài ngành/tập ứng viên và giới hạn tổng TC; cùng Người 3 ghép kiểm tra danh sách cuối, cùng Người 4 ghép lý do/fallback. Đây là công việc trong module Recommendation, không chỉ module Profile.
- **P2-04:** Viết `tests/test_profile.py`, `tests/test_api.py` (cần tạo) và bổ sung test service hiện có; cung cấp ví dụ request/response để Người 5 nối UI; review phần PDF được giao.

**Đầu ra:** kiểm tra hồ sơ, API/guard, test và hợp đồng request/response. **Đạt khi:** dữ liệu sai bị từ chối, kết quả luôn giữ đúng ngành/tập hợp lệ và chạy được khi không có LLM. **Review code:** Người 3.

### Người 3 — Kiểm tra điều kiện học và giải thích điều kiện

- **P3-01:** Hoàn thiện `app/rules.py`: tiên quyết AND/OR, môn đã qua, môn đang có xung đột nguồn; không viết cứng quy định của một ngành.
- **P3-02:** Kiểm tra nhóm tự chọn, hướng học và phương án tốt nghiệp theo metadata; phân biệt môn đủ điều kiện riêng lẻ với một danh sách môn có thể chọn cùng nhau. Cùng Người 1 kiểm tra ý nghĩa các trường JSON.
- **P3-03:** Trả lý do loại có cấu trúc như `already_passed`, `missing_prerequisite`, `group_full`, `credit_limit`, và cảnh báo trường hợp chưa xác minh. Cùng Người 2 chốt schema/ghép API, cùng Người 5 kiểm tra cách hiển thị.
- **P3-04:** Viết `tests/test_rules.py` (cần tạo): AND/OR, nhóm đủ TC, môn thuộc nhiều nhóm, hướng học, lựa chọn tốt nghiệp và kiểm tra danh sách cuối; review phần PDF được giao.

**Đầu ra:** bộ kiểm tra ứng viên/danh sách, lý do và test luật. **Đạt khi:** dữ liệu fixture cho kết quả đúng, không cộng lặp tín chỉ và không khẳng định hợp lệ khi quy định còn chưa xác minh. **Review code:** Người 4.

### Người 4 — Xếp hạng, adapter LLM và lý do gợi ý

- **P4-01:** Giữ `KeywordRanker` trong `app/ranking.py` làm baseline chạy được không cần API key; tạo test thứ tự ổn định trên hồ sơ giả lập.
- **P4-02:** Thêm adapter LLM (file mới, ví dụ `app/llm_adapter.py` trước refactor): chỉ gửi tập ứng viên và mục tiêu; đặt timeout, kiểm tra định dạng và xử lý lỗi. Không train/fine-tune model.
- **P4-03:** Cùng Người 2 chốt kết quả ranker khi cần lý do cá nhân hóa; service kiểm tra mã/lý do trước khi hiển thị. Lý do về tiên quyết phải lấy từ Người 3, không để LLM tự khẳng định.
- **P4-04:** Viết `tests/test_ranking.py` (cần tạo) với mock: mã lạ/trùng, JSON sai, rỗng, timeout, thiếu key; cùng Người 5 chuẩn bị hai tình huống what-if và bảng đánh giá baseline/LLM; review phần PDF được giao.

**Đầu ra:** baseline, adapter LLM, mock/test, hướng dẫn cấu hình và đánh giá nhỏ. **Đạt khi:** app không phụ thuộc API key để chạy; lỗi LLM có fallback; không có khóa bí mật trong Git. **Review code:** Người 5.

### Người 5 — Giao diện nhập hồ sơ, kết quả và what-if

- **P5-01:** Hoàn thiện `app/static/index.html`, `app.js`, `styles.css`: chọn ngành, tải môn của ngành, chọn môn đã qua, mục tiêu, giới hạn TC; đổi ngành xóa lựa chọn/kết quả cũ.
- **P5-02:** Nối API theo hợp đồng của Người 1 và 2; hiển thị loading, lỗi 404/422, mã/tên/TC/lý do/cảnh báo. Không chèn HTML từ LLM hoặc tự tính điều kiện học thay backend.
- **P5-03:** Hiển thị lý do loại từ Người 3; làm what-if lưu hai tình huống tạm trong trình duyệt và so sánh môn thêm/bớt, thứ tự đổi. Dùng fixture của Người 4, không sửa JSON chương trình.
- **P5-04:** Viết checklist kiểm thử UI trong `docs/` và lưu kết quả: đổi ngành, hồ sơ sai, LLM lỗi, màn hình nhỏ, what-if; chuẩn bị demo bốn ngành và review phần PDF được giao.

**Đầu ra:** form, màn hình kết quả/what-if và checklist demo có kết quả thực hiện. **Đạt khi:** UI không lẫn ngành, không hiển thị gợi ý giả, thông báo lỗi rõ và dùng được trên điện thoại. **Review code:** Người 1.

## File chung và thứ tự bàn giao

| File/hợp đồng | Người ghép thay đổi | Các bạn cung cấp đầu vào |
|---|---|---|
| `app/models.py`, request/response | Người 2 | 1: catalog; 3: kết quả luật; 4: kết quả ranker; 5: yêu cầu UI |
| `app/main.py`, đăng ký router | Người 2 | 1: API catalog; 2: API gợi ý |
| `app/service.py`, điều phối/guard | Người 2 | 3: kiểm tra danh sách cuối; 4: ranker, lý do và fallback |
| `data/curricula/` | Người sửa phần review được giao | Người review theo bảng dữ liệu; 1 kiểm tra công cụ |

Người ghép không phải chủ sở hữu độc quyền của module; đây chỉ là cách tránh sửa trùng file trong cùng đợt làm việc. Thứ tự: chốt schema/fixture → phát triển song song → ghép luật/ranker vào service → nối UI → kiểm thử chung. Trước khi refactor package, có một PR riêng chỉ chuyển cấu trúc/import và giữ nguyên các API/test; không để mỗi người tự tạo cấu trúc khác nhau.

## Đầu việc cùng làm và đi qua nhiều module

| Đầu việc | Người cùng làm | Module liên quan | Cách tách để tránh sửa trùng |
|---|---|---|---|
| Biểu diễn và kiểm tra hướng học/nhánh tốt nghiệp | 1 và 3 | Catalog, Bộ luật | 1 kiểm tra metadata; 3 viết logic và test luật |
| Đưa lý do loại môn và lựa chọn hướng học vào API | 2 và 3 | Profile, Eligibility, Recommendation | 2 sửa schema/service; 3 trả kết quả luật theo schema |
| Chặn mã LLM bịa, xử lý lỗi và hoàn thiện lý do gợi ý | 2 và 4 | Recommendation | 4 viết adapter/mock; 2 viết guard và test luồng cuối |
| Nạp môn theo ngành và kiểm tra form hồ sơ | 1 và 5 | Catalog, Giao diện | 1 test dữ liệu/loader; 5 viết UI và test đổi ngành |
| So sánh hai tình huống what-if | 4 và 5 | Recommendation, Giao diện | 4 tạo fixture xếp hạng ổn định; 5 viết giao diện so sánh |
| Kiểm thử tích hợp và demo 4 ngành | Cả 5 người | Toàn hệ thống | Mỗi người nhận ca test và sửa lỗi trong task riêng |

Các task phối hợp tạo nhánh riêng như `feat/graduation-rules`, `feat/recommendation-guard`, `feat/what-if`. Ghi người sửa từng file và thứ tự merge trong issue/PR trước khi bắt đầu; không cùng sửa một file chung trên hai nhánh lớn. Khối lượng được điều chỉnh theo thời gian và độ khó, không theo số module nhận.

## Cả năm người cùng review toàn bộ khung chương trình

Theo bảng đã số hóa: Toán học 89 STT và một dòng khóa luận không đánh STT; Toán tin 63, KHMTTT 61, KHDL 59. Tổng **272 STT và một dòng môn không đánh STT**. Phân công review như sau:

| Người | Phần bảng PDF cần đối chiếu | Tổng dòng nguồn | Người kiểm tra ghi chú/sửa lỗi |
|---|---|---:|---|
| 1 | Toán học STT 1–55 và dòng khóa luận `MAT4070` | 56 | 5 |
| 2 | Toán học STT 56–89; Toán tin STT 1–21 | 55 | 1 |
| 3 | Toán tin STT 22–63; KHMTTT STT 1–12 | 54 | 2 |
| 4 | KHMTTT STT 13–61; KHDL STT 1–5 | 54 | 3 |
| 5 | KHDL STT 6–59 | 54 | 4 |

Các khoảng chỉ dùng để chia review, không giới hạn số môn của sản phẩm. Một STT có thể chứa nhiều phương án; khi đối chiếu phải kiểm tra đủ mọi phương án và các lần môn xuất hiện ở nhóm khác. Đọc [hướng dẫn dữ liệu](../data/README.md) và kiểm tra năm dòng mẫu trước khi review toàn bộ. Trang bảng: Toán học PDF 8–14, Toán tin 8–12, KHMTTT/KHDL 9–13.

Số dòng là cách chia ban đầu; dòng khó đọc/tiên quyết phức tạp có thể mất nhiều thời gian hơn. Mỗi buổi họp ngắn, nhóm so khối lượng còn lại và điều chuyển task nhỏ nếu có người đang quá tải. Việc viết tool, test và review/merge đều được tính vào khối lượng.

## Làm trên nhánh riêng với dữ liệu đã có

Mỗi người đối chiếu phần được giao trong `data/curricula/<program_id>/source_rows.json` với PDF và ghi kết quả/điểm chưa chắc trong PR. Nếu cần sửa, sửa đúng dòng nguồn và metadata liên quan rồi chạy `python -X utf8 tools/build_catalogs.py --write`; tránh định dạng lại toàn bộ file nguồn vì các bạn khác cũng có thể sửa những dòng khác của cùng ngành. Người review dữ liệu kiểm tra thay đổi trước khi trưởng nhóm merge; người 1 hỗ trợ kiểm tra công cụ khi cần.

`courses.json` được sinh từ `source_rows.json` và `curriculum.json`; `python -X utf8 tools/build_catalogs.py --check` kiểm tra độ phủ và tính nhất quán. Mọi sửa lỗi nguồn phải giữ dấu vết để người khác kiểm tra. Catalog chỉ chuyển sang `verified` khi đủ review và xử lý các điểm cần xác minh.

## Cách phối hợp theo mốc

1. **Mốc khởi động:** cả nhóm clone, chạy bản nền và kiểm tra dữ liệu đã số hóa; chốt interface giữa các thành phần và tạo nhánh theo task.
2. **Mốc làm song song:** mỗi người gửi PR review/sửa dữ liệu và PR code riêng theo task nhỏ. Các module có thể dùng fixture/mock để phát triển độc lập; mỗi người có test hoặc checklist demo cho phần mình.
3. **Mốc tích hợp:** ghép các sửa lỗi dữ liệu, rồi Catalog → API → Luật → Xếp hạng → UI. Backend/UI có thể merge sớm với mock trong khi tiếp tục review dữ liệu.
4. **Mốc kiểm tra chung:** cả năm người cùng chạy tối thiểu sáu hồ sơ/ngành; chia ca test ngành, lỗi hồ sơ, tiên quyết/quota, lỗi LLM và what-if. Mỗi lỗi có người xử lý cụ thể, mọi người cùng viết phần báo cáo liên quan module mình.

## Quy tắc tránh xung đột

Mỗi task ghi rõ người sửa file chung trong issue/PR. Khi cần đổi interface/schema, người nhận task gửi PR nhỏ, thông báo các bạn làm tính năng phụ thuộc và merge hợp đồng trước. Người khác góp ý hoặc gửi patch phối hợp, thay vì tự sửa cùng file ở nhánh lớn. Review code theo vòng 1 → 2 → 3 → 4 → 5 → 1; trưởng nhóm chốt các quyết định tích hợp và merge.

## Checklist hoàn thành của mỗi người

- [ ] Có phần code chạy được và test/checklist cho các task được giao.
- [ ] Review đủ phần dữ liệu được giao, giữ trang/STT nguồn và ghi chỗ cần xác minh.
- [ ] Review code và lô dữ liệu của người kế tiếp; sửa lỗi nhận được từ reviewer.
- [ ] PR ghi cách kiểm tra; mọi thay đổi interface được cập nhật cho người dùng API.
- [ ] Hoàn thành task phối hợp, tham gia kiểm tra luồng chung và viết phần báo cáo/demo liên quan.
