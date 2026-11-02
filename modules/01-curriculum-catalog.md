# Module 01 — Catalog chương trình đào tạo

Cập nhật: 23/10/2026. **Hiện trạng:** có repository HUS, builder, validation và publication; bốn catalog vẫn draft_unverified.

## Trách nhiệm và code hiện có

Cung cấp snapshot chương trình đúng ngành/khóa/phiên bản cho transcript, progress, eligibility và ranking. Giữ provenance, prerequisite, choice groups, track/path và metadata có bằng chứng.

Nguồn export là database/data/hus_source.json; builder ở database/hus_db/catalog_builder.py. Runtime đọc PostgreSQL ai07 qua app/catalog.py và app/infrastructure/hus_repository.py. data/curricula/ chỉ là mẫu metadata một ngành, không phải nguồn đủ bốn catalog.

## Đầu vào và đầu ra

Đầu vào: bundle nguồn có provenance hoặc yêu cầu đọc program_id. Đầu ra: Catalog hợp lệ, metadata chương trình/revision, môn học, rules, trạng thái và cảnh báo nguồn.

Mã môn có thể dùng chung ở bảng nền nhưng tên/tín chỉ/điều kiện áp dụng phải theo membership từng chương trình. Không gộp ngữ nghĩa hai ngành chỉ vì trùng mã.

## Quy tắc

- Kiểm tra uniqueness, tham chiếu nhóm/track/path, prerequisite AND/OR và toàn vẹn snapshot.
- Giữ raw/source locator và variants; không coi unknown/conflict/external là không có tiên quyết.
- Không tự điền workload/difficulty/topics, môn tương đương hoặc lịch mở lớp.
- Chỉ khớp portal với catalog khi có bằng chứng ngành/khóa/phiên bản; không tự dùng catalog 2022 cho khóa khác.
- Publication dùng database.tools.publish_catalogs; migration dùng database.tools.migrate. Không chạy root Alembic lên HUS.
- Bốn catalog được kiểm tra và kích hoạt cùng transaction; lỗi giữ active cũ. Không tự fallback JSON khi storage lỗi.

## Kế hoạch cần làm

Rà MAT3402, MAT3325, PHI1002 và hiệu lực văn bản theo báo cáo nguồn. Sửa PDF acceptance resolver theo vị trí tài liệu mới, giữ kiểm tra hash. Đồng bộ đặc tả nguồn runtime và contract revision với các module tiêu thụ.

## Tiêu chí hoàn thành

Đọc đủ bốn chương trình, từ chối cấu trúc sai, giữ provenance và không mất snapshot cũ khi publish lỗi. Có bằng chứng revision trước/sau và rollback. Test pass không nâng catalog thành verified; xác nhận học vụ là cổng riêng.

Liên quan: [02](02-transcript-profile.md), [03](03-eligibility-engine.md), [vận hành HUS](../database/HUS_RUNTIME.md).
