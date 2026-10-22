# Kế hoạch cải thiện test database sau khi nhập nhánh Vinh

Ngày cập nhật: **22/10/2026**. Nhánh làm việc: `codebase` local, sau khi nhập commit `8c60434`. Kế hoạch test suite calibration ngày 17/10 và các mục đã hoàn thành của bản kế hoạch cũ là hồ sơ lịch sử; tài liệu này chỉ ghi công việc tiếp theo.

## 1. Trạng thái hiện tại và mục tiêu

Trên đúng commit `8c60434`, bản sao độc lập của nhánh đã đạt **263 passed / 41 deselected** offline và **31 passed / 273 deselected** với PostgreSQL. `database.tools.verify_data` đạt **26/26**; Ruff, bốn fixture tổng hợp, cú pháp JavaScript và `git diff --check` đạt. Test dùng database migration tạm đã dọn sau khi chạy; các bảng `accounts`, `students`, `course_attempts` vẫn rỗng. CI hiện có ba job và ba artifact JUnit riêng. Đây là mốc kiểm thử mã và database, không phải nghiệm thu PDF.

Đã có test cho migration, publisher idempotent, rollback giữa lúc upsert, hai publisher đồng thời với cùng bundle, revision/rollback, constraint PostgreSQL, dữ liệu nguồn bốn ngành, tiên quyết và kiểm tra SQL. Không viết lại các ca này chỉ để tăng số lượng test.

**Mục tiêu cải thiện:** bảo vệ database dùng cho test trước khi kết nối, kiểm tra các ranh giới transaction và khả năng đọc metadata sau khi publish, rồi bàn giao kết quả có thể đối chiếu trên commit mới. Mười ca `full_catalog_acceptance` là cổng nghiệm thu nguồn riêng và hiện chưa chạy vì thiếu bộ dữ liệu đã review độc lập. Bốn catalog vẫn là `draft_unverified`.

## 2. Công việc theo thứ tự ưu tiên

### P0 — Chặn nhầm đích database ở mọi fixture tích hợp

**Trạng thái 22/10/2026: hoàn thành.** Validator chung chạy trước khi tạo engine ở cả ba fixture PostgreSQL. URL HUS chỉ nhận local `ai07`; URL legacy chỉ nhận local `se_project_test`; query có thể chuyển hướng bị từ chối. Sau thay đổi, 28 ca URL mới cùng các ca cũ chạy offline; toàn suite đạt 291 passed / 41 deselected, PostgreSQL đạt 31 passed / 301 deselected, Ruff đạt. Các mục dưới đây ghi tiêu chí đã thực hiện để theo dõi lịch sử.

**Trước khi thực hiện:** `tests/database/test_hus_migration_runtime.py` kiểm tra URL trước khi tạo engine; `tests/database/test_hus_postgres.py` kiểm tra host/database sau khi tạo engine. Các test legacy nhận `TEST_DATABASE_URL` rồi tạo schema ngẫu nhiên.

- Đưa quy tắc xác thực đích test vào helper dùng chung, gọi trước mọi `create_engine` trong fixture PostgreSQL. Với HUS, chỉ cho phép PostgreSQL loopback, database `ai07` và tham số kết nối không thể chuyển host/database. Với legacy, dùng database thử nghiệm được chỉ định rõ và schema riêng; xác định quy tắc tương ứng trước khi sửa fixture.
- Thêm ca offline chứng minh URL từ xa, sai database, sai driver và query chuyển hướng bị từ chối trước khi tạo engine/kết nối. Giữ ca URL hợp lệ của Docker và CI.
- Chạy lại hai job PostgreSQL để chắc việc siết đích test không làm mất phạm vi integration.

**Hoàn thành khi:** cấu hình nhầm không thể mở kết nối hoặc chạy DDL; cấu hình local hợp lệ vẫn chạy hết các ca tích hợp.

### P1 — Kiểm tra rollback đúng lúc đổi revision active

**Trạng thái 22/10/2026: hoàn thành.** Ca mới trong `test_hus_migration_runtime.py` gây lỗi trước lệnh kích hoạt revision mới, sau lệnh tắt active cũ. Snapshot của mọi bảng publisher không đổi sau rollback; bốn revision cũ vẫn active, repository vẫn `ready`, và publish lại bundle mới thành công. Ca tập trung và toàn nhóm HUS PostgreSQL (16 passed) đạt trên database tạm.

**Trước khi thực hiện:** ca rollback của HUS publisher gây lỗi giữa lúc upsert và xác nhận toàn bộ bảng không đổi. Chưa có ca gây lỗi ngay sau bước tắt các revision active.

- Trên database tạm của `runtime_engine`, publish bundle A, chụp toàn bộ bảng publisher có thể sửa cùng bốn revision active.
- Publish bundle B hợp lệ và gây lỗi tại bước đổi active bằng hook trong test. Dùng connection mới so sánh snapshot: không có hàng ghi dở, mỗi ngành vẫn trỏ revision A, repository vẫn `ready`.
- Bỏ hook và publish lại bundle B để xác nhận transaction cùng advisory lock được giải phóng.

**Hoàn thành khi:** lỗi ở ranh giới kích hoạt rollback toàn bộ bốn ngành và lần publish kế tiếp thành công.

### P1 — Kiểm tra publish đồng thời với hai bundle khác nhau

**Trạng thái 22/10/2026: hoàn thành.** Ca mới dùng hai bundle tổng hợp khác nhau về `source`, `name_en` và bằng chứng test; hai publisher bắt đầu qua barrier trên database tạm. Kết quả active của cả bốn ngành phải trọn vẹn thuộc một bundle, cùng source digest; metadata lưu trong `curriculum_courses` phải khớp bundle thắng. Ca tập trung và toàn nhóm HUS PostgreSQL (17 passed) đạt.

**Trước khi thực hiện:** ca đồng thời dùng hai bản của cùng một bundle và xác nhận một revision active cho mỗi ngành.

- Chạy hai publisher với hai bundle hợp lệ **khác nhau** trên database tạm; đồng bộ bằng barrier và dùng timeout hữu hạn.
- Chấp nhận một trong hai thứ tự commit. Snapshot cuối phải là trọn bộ bốn revision của một bundle, không pha giữa hai bundle; mỗi ngành có đúng một active revision và repository đọc được.
- Nếu kiểm tra reader trong lúc publish, xác nhận reader chỉ thấy snapshot cũ hoặc mới theo một transaction đọc nhất quán. Tránh assert thứ tự chạy theo thời gian sleep.

**Hoàn thành khi:** chạy lặp lại ổn định, không có revision pha trộn và database tạm được dọn cả khi test lỗi.

### P1 — Xác nhận metadata mới đi qua PostgreSQL và API

**Trạng thái 22/10/2026: hoàn thành.** Hai ca HUS PostgreSQL mới đối chiếu toàn bộ 290 học phần từ source-built catalog qua repository, kiểm tra `runtime_metadata` trong SQL và `/courses` trên repository thật của database tạm. Tám giá trị giờ trống vẫn `null`. Thay đổi metadata có bằng chứng tạo revision mới; publish lặp lại không tạo thêm revision, còn tín chỉ và tiên quyết không đổi. Toàn nhóm HUS đạt 19 passed.

**Trước khi thực hiện:** test metadata kiểm tra source-built catalog và API giả lập; migration test đã publish và đọc catalog từ PostgreSQL nhưng chưa assert cụ thể các trường vừa thêm.

- Publish bundle hiện tại vào database tạm, đọc lại catalog qua `HusRepository` và kiểm tra mẫu đại diện có `name_en`, `hours`, `field_evidence` đúng theo chương trình; kiểm tra tám giá trị giờ trống vẫn `null`.
- Kiểm tra revision/digest đổi khi metadata có bằng chứng đổi, publish lại cùng bundle không tạo revision mới, và metadata không làm thay đổi credits/eligibility/prerequisites.
- Kiểm tra đường API đọc từ repository thật trên database tạm cho một vài mã đại diện, kể cả tên riêng của MAT3366 trong Toán tin.

**Hoàn thành khi:** source, hàng lưu PostgreSQL, snapshot active và API trả cùng metadata; dữ liệu chưa biết vẫn chưa biết.

### P2 — Cập nhật bằng chứng kiểm thử và hướng dẫn chạy

- Chạy đúng ba nhóm CI trên commit hoàn thiện: offline, `postgres`, `hus_postgres`; lưu số passed/failed/skipped/deselected riêng, cùng kết quả Ruff và `verify_data`.
- Cập nhật `tests/database/README.md` và `docs/VINH_DATABASE_TEST_REPORT.md` bằng commit, môi trường, lệnh chạy và mốc mới. Các số liệu từ commit cũ phải được ghi là lịch sử.
- Kiểm tra sau chạy không còn database/schema tạm, không có bản ghi sinh viên tổng hợp tồn lưu. Không dùng việc test pass để đổi trạng thái catalog.

**Hoàn thành khi:** người khác có thể đối chiếu kết quả theo commit và biết rõ phần nào chưa được nghiệm thu.

## 3. Cổng nghiệm thu nguồn học thuật riêng

Khi có bộ nguồn đã được review độc lập, chuẩn bị `--full-catalog-root` đúng định dạng dự án rồi chạy đủ mười ca `full_catalog_acceptance`. Expected data cần lấy từ kết luận rà PDF và người review, không sinh từ chính `hus_source.json` hay catalog builder. Ghi ngoại lệ MAT3402, MAT3325, PHI1002 và phạm vi đã xác minh. Việc này phối hợp với [kế hoạch metadata HUS](KE_HOACH_CAI_THIEN_METADATA_HUS.md), không chặn các mục P0/P1 ở trên.

## 4. Thông tin cần người dùng cung cấp

**Để bắt đầu P0–P2 trên Docker local hiện có: chưa cần cung cấp thêm.** Repo đã có cấu hình Docker local bị Git bỏ qua; không gửi mật khẩu hoặc dump database. Nếu muốn test legacy trên database thử nghiệm khác `se_project_test`, cần cho biết tên database và giới hạn được phép tạo/xóa schema trước khi đổi quy tắc an toàn.

**Để hoàn tất cổng nghiệm thu nguồn:** cần PDF/ZIP quyết định đúng phiên bản và mọi văn bản điều chỉnh, xác nhận khóa áp dụng, bảng review độc lập có locator/kết luận và người hoặc đơn vị chịu trách nhiệm xác nhận. Chỉ ZIP PDF chưa đủ để chạy `--full-catalog-root`; cần bộ expected data đã review theo định dạng test.

## 5. Quy tắc thực hiện

Mỗi thay đổi test phải bắt một rủi ro cụ thể và chạy trên database/schema tạm. Giữ `ai07` runtime, legacy database, volume Docker, cấu hình bí mật và dữ liệu người dùng nguyên vẹn. Không publish catalog vào runtime, commit hay push như một phần của việc viết kế hoạch này. Khi triển khai, báo riêng tiến độ test kỹ thuật và tiến độ nghiệm thu nguồn.
