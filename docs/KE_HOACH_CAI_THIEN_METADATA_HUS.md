# Kế hoạch cải thiện metadata HUS và tài liệu cần cung cấp

Ngày lập: **21/10/2026**. Cập nhật đối chiếu nhánh Vinh: **22/10/2026**. Kế hoạch đã được triển khai một phần; các điều kiện nghiệm thu học vụ vẫn còn mở.

## Cập nhật để Vinh tiếp tục thực hiện (22/10/2026)

Phạm vi đối chiếu: commit `8c60434` trên `origin/feat/vinh-database-tests`, so với kế hoạch này. Commit đó cũng là đầu nhánh `fix/hus-metadata-vi-en-20261021` tại lúc rà soát. Lượt đối chiếu ban đầu dựa trên mã nguồn và báo cáo đã đưa lên Git; người rà soát **chưa đọc lại độc lập các PDF**. Kết quả kiểm thử sau đó được ghi riêng ngay dưới đây và vẫn không thay thế nghiệm thu nguồn học thuật.

**Cập nhật sau khi kiểm thử và merge local (22/10/2026):** Commit `8c60434` đạt 263 test offline, 31 test PostgreSQL, `verify_data` 26/26, Ruff, kiểm tra fixture tổng hợp và cú pháp JavaScript. `codebase` local đã fast-forward tới commit này; chưa push lên `origin/codebase` và chưa publish metadata mới vào database runtime. Mười ca `full_catalog_acceptance` vẫn chờ bộ nguồn được review độc lập.

**Ước lượng tiến độ toàn kế hoạch: khoảng 40%.** Đây là ước lượng theo sáu giai đoạn và điều kiện hoàn thành, không phải tỷ lệ dòng dữ liệu đã được chuyên môn xác minh. Không dùng con số này để nâng trạng thái catalog.

### Đã làm được trên nhánh

- Có manifest nguồn ghi tên file, SHA-256, quyết định, khóa 2022 và trang bảng của bốn PDF chương trình; PDF QĐ 3566 được liệt kê để tham chiếu ngoài bốn catalog. Giá trị metadata mới có locator theo trang/dòng/cột. Xem `database/data/hus_source.json`.
- Bổ sung `name_en` cho **290/290** học phần theo chương trình và `hours` cho **282/290**. Tám ô giờ GDQP/GDTC trống trong PDF vẫn là `null`, không chuyển thành 0. `coverage.json` có số liệu trước/sau theo chương trình.
- Bộ dựng catalog áp dụng metadata theo `program_id` và mã môn, yêu cầu bằng chứng cho giá trị khác `null`, và không cho metadata ghi đè tiên quyết, tín chỉ hoặc quota. Có kiểm thử tập trung cho dữ liệu song ngữ, giờ học và ràng buộc này.
- Theo báo cáo triển khai, đã đối chiếu tên Anh và giờ học trên 22 trang bảng, cập nhật tên nhóm V.2.2 của Toán tin theo PDF và tên MAT3366 riêng trong Toán tin. PHI1002 Toán học vẫn giữ PHI1006 theo PDF hiện có. MAT3423/MAT3402 và hai điều kiện MAT3325 vẫn được giữ ở trạng thái chưa rõ/xung đột để xử lý an toàn.
- Có giao diện chọn tên học phần Việt/Anh, tìm kiếm theo hai tên hoặc mã, và hiển thị giờ học. Đây là chế độ tên môn song ngữ, chưa phải giao diện tiếng Anh toàn diện.
- Có báo cáo độ đầy đủ, bảng dòng nguồn, rubric tư vấn **bản nháp** và mẫu thu thập review. Báo cáo triển khai ghi nhận lượt kiểm tra offline, demo local, sao lưu và publish bằng công cụ HUS; bằng chứng runtime chi tiết nằm trong `backups/` bị Git bỏ qua.

### Chưa hoàn thành hoặc chưa đủ bằng chứng nghiệm thu

| Giai đoạn | Trạng thái đối chiếu | Phần Vinh cần hoàn tất hoặc bàn giao |
|---|---|---|
| 1. Chốt nguồn và phiên bản | Có manifest/hash và phạm vi khóa 2022; chưa đủ kết luận về ngày ban hành, văn bản điều chỉnh và hiệu lực. | Ghi ngày ban hành, nguồn của từng quyết định, danh sách văn bản điều chỉnh đã kiểm tra hoặc xác nhận chưa có/chưa biết; xác nhận phạm vi khóa áp dụng với người phụ trách. |
| 2. Điểm bất nhất ưu tiên | V.2.2 và MAT3366 đã sửa theo phần PDF được báo cáo; P0 MAT3402 và MAT3325 chưa chốt; PHI1002 còn khác biệt với web. | Lập sổ vấn đề có giá trị hiện tại, locator, tác động, người kết luận và trạng thái. Xin khoa/phòng đào tạo xác nhận MAT3402 hoặc tương đương, cách áp dụng hai điều kiện MAT3325 theo định hướng, và văn bản hiệu lực cho PHI1002 nếu có. Giữ chặn an toàn khi chưa rõ. |
| 3. Đối chiếu toàn bộ khung | Có `row-audit.csv` nhưng `human_review=pending`; chưa có bộ nguồn được review cho `full_catalog_acceptance`. | Review độc lập từng dòng và chú thích PDF: mã/tên/tín chỉ/nhóm, AND/OR, quota, nhánh tốt nghiệp, môn không tính tín chỉ, tổng tín chỉ theo lựa chọn. Ghi sai lệch và phạm vi review. Chuẩn bị dữ liệu acceptance đúng định dạng nếu yêu cầu nghiệm thu. |
| 4. Metadata có nguồn trực tiếp | Hoàn thành tên Anh và phần lớn giờ học. `instruction_language`, `year`, `suggested_term` và URL nguồn chính thức vẫn chưa có. | Chỉ điền khi có đề cương/kế hoạch học kỳ đúng phiên bản; giữ `null` và lý do khi thiếu. Bổ sung reviewer/thời gian review sau khi review thật. Không suy ngôn ngữ giảng dạy từ tên tiếng Anh hoặc tạo URL giả từ file local. |
| 5. Metadata tư vấn | Mới có rubric dự thảo và mẫu review. `topics`, `orientation`, `difficulty`, `workload`, `description`, `career_paths` vẫn **0/290**. | Thu thập đề cương, chuẩn đầu ra và nguồn đánh giá; chốt từ vựng/rubric với chuyên môn; review từng giá trị trước khi đưa vào ranking. Nếu chưa có nguồn, bàn giao rubric/mẫu và giữ giá trị môn học chưa biết. |
| 6. Kiểm tra và công bố | Báo cáo nhánh ghi đã test và publish demo local; bằng chứng backup, revision và snapshot nằm ngoài Git. Chưa có nghiệm thu học vụ đầy đủ. | Bàn giao báo cáo có thể kiểm tra được về revision trước/sau, phạm vi database, kết quả dry-run/publish, `/ready`, API/UI, rollback và các test liên quan. Tách rõ kiểm thử fixture, kiểm thử PostgreSQL và nghiệm thu nguồn đã review. |

**Lưu ý về bằng chứng:** Trong `database/tools/metadata_report.py`, cột `core_source_consistency` của `row-audit.csv` được gán sẵn `matched` từ source export; cột đó **không chứng minh** đã đối chiếu độc lập từng dòng với PDF. Chỉ dùng kết quả review có locator, người review và kết luận để đánh dấu đã xác minh. Bốn catalog tiếp tục là `draft_unverified` cho đến khi đủ bằng chứng theo phạm vi review.

**Tài liệu trên nhánh để bàn giao:** `reports/hus-metadata-2026-10-21/IMPLEMENTATION.md`, `coverage.json`, `row-audit.csv`, `docs/HUS_METADATA_RUBRIC_DRAFT.md`, `database/data/hus_source.json`. Nếu bàn giao chứng cứ local trong `backups/`, chỉ cung cấp qua kênh phù hợp; không đưa dump database, `.env` hoặc thông tin đăng nhập lên Git.

## 1. Mục tiêu và phạm vi

Cải thiện dữ liệu của bốn chương trình HUS đang được ứng dụng sử dụng: Toán học, Toán tin, Khoa học máy tính và thông tin, Khoa học dữ liệu. Thứ tự ưu tiên là xác minh thông tin học vụ, xử lý tiên quyết, bổ sung metadata có nguồn, rồi cải thiện thông tin phục vụ tư vấn.

Phạm vi dự kiến giữ bộ chương trình áp dụng từ khóa tuyển sinh 2022, theo các quyết định năm 2023. Cần xác nhận phạm vi này trước khi lựa chọn tài liệu để cập nhật. Nếu hỗ trợ thêm khóa hoặc phiên bản khác, phải quản lý catalog riêng, không ghi đè quy tắc giữa các khóa.

Kế hoạch không bao gồm đăng nhập, đồng bộ cổng đào tạo, lưu bảng điểm sinh viên, OCR thành tính năng sản phẩm hoặc HUS Q&A/RAG. Đọc ảnh PDF scan để rà soát nguồn là một bước kiểm tra dữ liệu.

## 2. Cơ sở lập kế hoạch

Lượt rà soát ngày 21/10/2026 đã đọc trực tiếp database local `ai07`: 179 mã học phần, 290 liên kết học phần–chương trình, 297 dòng nguồn, 348 quan hệ tiên quyết, 41 nhóm và 4 catalog active.

| Chương trình | Số học phần trong catalog | Số dòng nguồn | Tín chỉ yêu cầu |
|---|---:|---:|---:|
| Toán học | 90 | 96 | 135 |
| Toán tin | 68 | 69 | 132 |
| Khoa học máy tính và thông tin | 67 | 67 | 129 |
| Khoa học dữ liệu | 65 | 65 | 127 |

Các con số là snapshot của lượt rà soát, cần lấy lại trước khi triển khai. Một môn có thể thuộc nhiều chương trình hoặc xuất hiện ở nhiều nhóm nên số mã, số liên kết và số dòng nguồn khác nhau.

Kết quả làm cơ sở:

- Chưa phát hiện lệch tín chỉ giữa bảng học phần, metadata, snapshot active và bản chép nguồn. Đối chiếu bảng web HUS cho thấy 297 dòng khớp tín chỉ; hai dòng GDQP/GDTC của Toán học ghép theo tên/STT vì web thiếu mã.
- Cả 290 dòng metadata thiếu 11 trường: `name_en`, `hours`, `instruction_language`, `year`, `suggested_term`, `topics`, `orientation`, `difficulty`, `workload`, `description`, `career_paths`.
- Cả 4 chương trình thiếu `official_source_url`; 290 liên kết thiếu `suggested_semester`.
- `courses.difficulty_level=2` ở 179 mã là giá trị mặc định, chưa phải đánh giá có căn cứ. Runtime giữ `difficulty=NULL`.
- Còn các vấn đề tiên quyết và nhãn dữ liệu nêu trong mục 5.
- Catalog vẫn là `draft_unverified`. Tính nhất quán nội bộ và việc khớp bảng HTML không chứng nhận mọi thông tin đúng PDF của quyết định năm 2023.

Bằng chứng local của lượt rà soát nằm ở `backups/metadata_audit_20261021/`: `REPORT.md`, `row_audit.csv`, `all_empty_fields.json`, `web_row_comparison.json` và các snapshot. Thư mục này bị Git bỏ qua, không có sẵn trong một bản clone mới. Báo cáo lịch sử có trong [VINH_PDF_SOURCE_REVIEW.md](VINH_PDF_SOURCE_REVIEW.md); cần phân biệt bằng chứng lịch sử với lượt đọc lại PDF mới.

## 3. Người dùng cần cung cấp những gì?

### 3.1. Bộ tối thiểu để bắt đầu

| Cần cung cấp | Nội dung cụ thể | Mục đích |
|---|---|---|
| PDF/ZIP khung chương trình gốc | QĐ 3565: Toán học; QĐ 3567: Toán tin; QĐ 3568: KHMT và thông tin; QĐ 3569: Khoa học dữ liệu, năm 2023 | Đối chiếu từng dòng mã, tên, tín chỉ, tiên quyết và nhóm lựa chọn |
| PDF QĐ 3566 năm 2023 | Chương trình Toán học tài năng | Kiểm tra các học phần tham chiếu ngoài bốn catalog; không tự thêm catalog thứ năm |
| Phạm vi khóa áp dụng | Xác nhận giữ bộ áp dụng từ khóa 2022 hay bổ sung khóa khác | Tránh trộn các phiên bản chương trình |
| Văn bản điều chỉnh nếu có | Quyết định sửa đổi, phụ lục thay thế hoặc thông báo chính thức liên quan | Xác định nguồn có hiệu lực khi tài liệu khác nhau |

Có thể gửi file, ZIP hoặc đường dẫn thư mục trên máy. Nên cung cấp toàn bộ tài liệu gồm trang quyết định, khung chương trình và chú thích; các trang bảng riêng lẻ có thể thiếu quy tắc giải thích dấu `/`, nhóm tự chọn hoặc điều kiện tốt nghiệp.

Chỉ cần bộ này là có thể bắt đầu giai đoạn xác minh học vụ. Nếu chưa có văn bản điều chỉnh, ghi rõ “chưa có/chưa biết” để lưu giới hạn xác minh.

### 3.2. Tài liệu cần cho các phần bổ sung

| Tài liệu/thông tin | Phần công việc sử dụng | Khi chưa có |
|---|---|---|
| Đề cương chi tiết học phần đúng phiên bản | Mô tả, nội dung, mục tiêu, giờ học, phương pháp đánh giá; cơ sở gán chủ đề | Chỉ bổ sung trường có trong nguồn hiện có, các trường còn lại giữ chưa biết |
| Kế hoạch đào tạo theo học kỳ | `year`, `suggested_term`/`suggested_semester` | Không tự suy ra học kỳ từ mã môn hoặc chuỗi tiên quyết |
| Quy chế học vụ áp dụng cho khóa | Cách tính tín chỉ/GPA, điều kiện tốt nghiệp, môn tương đương/thay thế và tiên quyết | Chỉ xác nhận phần đã được quy định rõ trong khung; ghi nhận phần chưa kiểm chứng |
| Email/văn bản xác nhận của khoa hoặc phòng đào tạo | Giải quyết MAT3402, MAT3325, PHI1002 và khác biệt chưa kết luận được | Lập câu hỏi cụ thể sau khi đọc PDF; giữ trạng thái chưa rõ/xung đột phù hợp |
| Nguồn đánh giá độ khó và khối lượng học tập | `difficulty`, `workload`: đề cương, đánh giá giảng viên hoặc khảo sát | Xây dựng rubric và mẫu thu thập trước; không tự gán mức cho từng môn |
| Nguồn về định hướng nghề nghiệp | `orientation`, `career_paths`: đề cương, chuẩn đầu ra, tài liệu khoa và ý kiến chuyên môn | Có thể đề xuất ánh xạ để review; không coi suy luận là nội dung chính thức |
| Người chịu trách nhiệm review | Người/đơn vị xác nhận nội dung và phạm vi được xác nhận | Không tạo thông tin reviewer giả hoặc nâng trạng thái verified thiếu bằng chứng |

Không cần gửi lại mật khẩu, API key, dữ liệu tài khoản hoặc bảng điểm cá nhân. Kết nối local đã được sử dụng trong lượt rà soát; khi triển khai chỉ cần kiểm tra Docker/database sẵn sàng.

### 3.3. Phạm vi thực hiện cần thống nhất

Khi yêu cầu triển khai, nêu rõ cho phép sửa source/code, chạy kiểm tra và publish vào database local hay chỉ chuẩn bị thay đổi để xem. Chỉ hỏi thêm khi phạm vi mới chưa được cho phép; không hỏi lại quyền đã được xác nhận trong phiên làm việc.

Commit/push là yêu cầu riêng. Nếu có yêu cầu công bố Git, cần xác định nhánh đích; không suy ra từ `origin/HEAD`.

Mẫu thông tin có thể gửi:

```text
Thư mục/ZIP PDF: ...
Khóa áp dụng: giữ bộ từ khóa 2022 / phạm vi khác: ...
Văn bản điều chỉnh: ... / chưa có
Đề cương học phần: ... / chưa có
Kế hoạch học kỳ và quy chế: ... / chưa có
Nguồn đánh giá độ khó, workload, nghề nghiệp: ... / chưa có
Người/đơn vị review nội dung: ... / chưa xác định
Phạm vi thực hiện: chuẩn bị thay đổi / sửa source-code và kiểm tra /
                   sửa, kiểm tra và publish database local
Commit/push: chưa thực hiện / yêu cầu cụ thể và nhánh đích: ...
```

## 4. Các giai đoạn triển khai

### Giai đoạn 1 — Chốt nguồn và phiên bản

- Lập danh mục tài liệu: chương trình, khóa áp dụng, số quyết định, ngày ban hành, URL hoặc tên file, SHA-256.
- Đọc cả chú thích và phần quy định lựa chọn; phân biệt số trang PDF với số trang in.
- Ghi nhận văn bản sửa đổi và phạm vi hiệu lực. Không tự mặc định web mới hơn thay thế PDF cũ.
- Lấy snapshot dữ liệu hiện tại để báo cáo không dựa vào số liệu cũ.

**Đầu ra:** manifest nguồn và danh sách phần còn thiếu. **Điều kiện hoàn thành:** xác định được nguồn dùng để đối chiếu cho từng chương trình.

### Giai đoạn 2 — Xử lý các điểm bất nhất ưu tiên

- Đọc trực tiếp các ô nguồn trong mục 5; lưu vị trí và bằng chứng kết luận.
- Đánh giá tác động đến điều kiện học, nhánh lựa chọn và các môn phụ thuộc.
- Nếu cần tiên quyết theo định hướng, thiết kế hành vi rõ ràng rồi mới sửa mô hình/rule; không chọn một variant tùy ý.
- Phân biệt “sửa được từ bằng chứng” với “cần đơn vị chuyên môn xác nhận”.

**Đầu ra:** sổ vấn đề với giá trị hiện tại, bằng chứng, đề xuất, ảnh hưởng và trạng thái. **Điều kiện hoàn thành:** mọi vấn đề có kết luận hoặc lý do chưa giải quyết; các trường hợp chưa rõ vẫn được xử lý an toàn.

### Giai đoạn 3 — Đối chiếu toàn bộ khung chương trình

- Rà đủ từng dòng nguồn theo từng nhóm, kể cả học phần xuất hiện nhiều lần.
- Kiểm tra mã, tên, tín chỉ, nhóm, loại yêu cầu, tiên quyết AND/OR và tham chiếu ngoài ngành.
- Kiểm tra hạn mức tự chọn, định hướng, phương án tốt nghiệp, môn không tính tổng tín chỉ.
- Tính lại tổng theo quy tắc lựa chọn, không cộng toàn bộ môn trong catalog.
- Kiểm tra độ thống nhất giữa source export, bảng quan hệ, runtime metadata và snapshot active.

**Đầu ra:** bảng đối chiếu từng dòng và danh sách thay đổi. **Điều kiện hoàn thành:** không còn sai lệch chưa ghi nhận; có bằng chứng và phạm vi review cho từng kết luận. Nếu cần nghiệm thu `full_catalog_acceptance`, chuẩn bị bộ dữ liệu đã review đúng định dạng của dự án; không truyền ZIP PDF trực tiếp làm bộ acceptance.

### Giai đoạn 4 — Bổ sung metadata có nguồn trực tiếp

- Bổ sung `name_en`, `hours`, `instruction_language` từ tài liệu phù hợp.
- Điền nguồn truy cập chính thức khi có; nguồn chỉ ở file local phải được lưu bằng tên/hash/locator thay vì tạo URL giả.
- Bổ sung năm/học kỳ khi có kế hoạch đào tạo đúng phiên bản.
- Giữ provenance và `field_evidence`, reviewer, thời gian review theo schema.
- Phân loại NULL, chuỗi trống và mảng rỗng; không coi `false` hoặc `0` là thiếu dữ liệu.

**Đầu ra:** metadata bổ sung và bảng độ đầy đủ trước/sau. **Điều kiện hoàn thành:** mọi giá trị mới truy được về nguồn; trường chưa biết có lý do, không điền cho đủ số lượng.

### Giai đoạn 5 — Xây dựng metadata tư vấn

- Xây bộ từ vựng cho chủ đề và nghề nghiệp, cùng quy tắc ánh xạ từ nội dung học phần.
- Viết mô tả ngắn dựa trên đề cương; phân biệt nội dung nguồn với diễn giải.
- Định nghĩa rubric có phiên bản cho độ khó/workload và cách xử lý ý kiến đánh giá khác nhau.
- Review ánh xạ trước khi dùng trong xếp hạng. Không biến giá trị mặc định `difficulty_level=2` thành kết luận.
- Giữ eligibility độc lập: thay đổi trọng số tư vấn/what-if không được thay đổi điều kiện học hay sự thật catalog.

**Đầu ra:** bộ từ vựng, rubric và metadata tư vấn có bằng chứng. **Điều kiện hoàn thành:** cách đánh giá nhất quán và có nguồn; nếu thiếu dữ liệu đánh giá, bàn giao rubric/mẫu thu thập và giữ giá trị môn học chưa biết.

### Giai đoạn 6 — Kiểm tra và công bố catalog

- Kiểm tra các tình huống thay đổi thực tế: biểu thức AND/OR, trạng thái chưa rõ/xung đột, môn ngoài ngành, lựa chọn định hướng và chuỗi môn phụ thuộc.
- Kiểm tra tổng tín chỉ, tiến độ, recommendations và what-if; đổi ngành phải xóa transcript/chat context.
- Dùng fixture tổng hợp cho regression; tách kiểm tra nguồn đã review khỏi kiểm thử logic. Chạy kiểm tra PostgreSQL trên môi trường được chỉ định phù hợp.
- Khi được phép publish local: sao lưu database và ghi lại revision active, chạy dry-run, publish bằng công cụ HUS, rồi kiểm tra `/ready` và các luồng API/UI chịu ảnh hưởng.
- Dùng `database.tools.publish_catalogs`; migration HUS nếu cần dùng `database.tools.migrate`. Không chạy root Alembic hoặc SQL import lịch sử lên runtime HUS đã migrate.
- Giữ `.env`, database legacy, volume và lịch sử revision. Theo [HUS_RUNTIME.md](../database/HUS_RUNTIME.md) để rollback.

**Đầu ra:** báo cáo kiểm tra, thay đổi trước/sau, revision mới và phương án rollback. **Điều kiện hoàn thành:** kiểm tra liên quan đạt, dữ liệu công bố khớp bản đã review và khả năng quay lại revision trước được ghi rõ.

## 5. Danh sách vấn đề cần ưu tiên

| Ưu tiên | Vấn đề | Việc cần làm | Nếu chưa đủ bằng chứng |
|---|---|---|---|
| P0 | MAT3423 tham chiếu MAT3402 chưa có định nghĩa | Tìm định nghĩa trong PDF/phụ lục; xác nhận mã hoặc tương đương từ nguồn có thẩm quyền | Giữ `unknown`; không hiểu `prerequisites=[]` là không có tiên quyết |
| P0 | MAT3325 có hai điều kiện theo nhóm ở Toán học | Xác nhận khác biệt có chủ đích theo định hướng hay là lỗi tài liệu; xác định hành vi phù hợp | Giữ conflict; không gộp hoặc chọn một điều kiện tùy ý |
| P1 | PHI1002 Toán học: source có PHI1006, web để trống | Đối chiếu PDF đúng quyết định và văn bản sửa đổi | Ghi nhận khác biệt; không tự xóa tiên quyết |
| P1 | V.2.2 Toán tin ghi tên định hướng Tin học, web ghi Tính toán khoa học | Kiểm tra tên nhóm, thành viên và hạn mức; cập nhật đồng bộ source/runtime nếu xác nhận | Giữ issue chờ xác minh |
| P1 | MAT3366: “Hệ máy tính”/“Hệ thống máy tính” | Chốt tên theo tài liệu đúng phiên bản, xem tác động vì mã môn dùng chung | Ghi nhận biến thể tên, chưa kết luận bên nào sai |
| P1 | Thiếu provenance/reviewer và URL nguồn | Hoàn thiện manifest, locator và bằng chứng review | Không nâng `verified` thiếu căn cứ |
| P2 | Metadata mô tả và tư vấn thiếu | Bổ sung theo giai đoạn 4–5 | Giữ NULL có giải thích |

Trong phép kiểm tra chuỗi tiên quyết từ transcript trống, MAT3423 ảnh hưởng thêm MAT3407, MAT3408, MAT3415, MAT3412, MAT3362 và MAT3422. Đây là phạm vi cần kiểm tra hồi quy, không phải khẳng định mọi sinh viên đều bị chặn các môn này trong mọi tình huống.

## 6. Nguyên tắc nghiệm thu và cập nhật tiến độ

- Báo cáo tiến độ thường xuyên theo công việc đã hoàn thành: số tài liệu/trang/dòng đã rà, số vấn đề đã chốt, phần còn thiếu và bước kế tiếp.
- Tách tiến độ rà dữ liệu, triển khai code, xác minh học vụ và publish. Không coi test pass là sản phẩm hoặc nguồn học thuật đã được nghiệm thu.
- Không nâng toàn bộ catalog thành `verified` chỉ vì khớp nội bộ hoặc khớp website. Trạng thái phải phù hợp phạm vi review thực tế và các yêu cầu của schema.
- Không đoán tên/tín chỉ môn tham chiếu, môn tương đương, lịch mở lớp hoặc học kỳ giảng dạy.
- Trường hợp thiếu tài liệu: tiếp tục phần độc lập, ghi rõ phần chưa xác minh và tài liệu cần bổ sung.
- Chỉ cập nhật dữ liệu/code/database trong phạm vi triển khai đã được người dùng cho phép. Việc lập tài liệu này chưa phải yêu cầu publish hay commit/push.

## 7. Checklist bàn giao

- [ ] Manifest nguồn, phiên bản và khóa áp dụng.
- [ ] Bảng đối chiếu toàn bộ dòng nguồn, có locator và kết luận.
- [ ] Danh sách vấn đề đã giải quyết/chưa giải quyết, kèm tác động.
- [ ] Metadata có nguồn trực tiếp và thống kê trường còn trống.
- [ ] Bộ từ vựng/rubric tư vấn và danh sách giá trị đã review.
- [ ] Báo cáo kiểm tra dữ liệu, hành vi ứng dụng và giới hạn nghiệm thu.
- [ ] Nếu publish: bằng chứng sao lưu, revision trước/sau, kiểm tra runtime và hướng dẫn rollback.

Đợt đầu ưu tiên giai đoạn 1–3. Chỉ triển khai các phần metadata tư vấn khi có nguồn và tiêu chí phù hợp; không cần đợi đủ mọi tài liệu để bắt đầu rà khung chương trình.

## 8. Tài liệu liên quan

- [Đặc tả metadata](COURSE_METADATA_SPECIFICATION.md)
- [Thiết kế database](DATABASE_DESIGN.md)
- [Vận hành HUS](../database/HUS_RUNTIME.md)
- [Báo cáo review PDF trước đây](VINH_PDF_SOURCE_REVIEW.md)
- [Checklist triển khai hiện tại](CODEBASE_CHECKLIST.md)
