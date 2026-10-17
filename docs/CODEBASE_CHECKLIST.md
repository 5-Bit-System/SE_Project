# Checklist codebase

## HUS runtime cutover - 2026-10-17

- [x] Backup/restore both databases; preserve original source/legacy rows.
- [x] Independent migrations: adopt existing HUS and build fresh database.
- [x] Four validated snapshots, repeat import, invalid-source rejection and revision rollback.
- [x] Main API/UI uses ai07; profiles empty; four-major Chrome acceptance.
- [x] Restart persistence and legacy config rollback; 173 tests passed; Ruff/JS/diff passed.
- [ ] Reviewed PDF/source acceptance: 10 tests skipped for missing reviewed sources.
- [ ] Login/portal sync/new modules deferred by user; outside this change.

See [evidence and operations](../database/HUS_RUNTIME.md). Earlier checklist entries below are historical.


## Database HUS trên Docker — 2026-10-17

- [x] Container/volume riêng `se_hus_db` / `se_hus_pgdata`, PostgreSQL 16,
  database `ai07`, chỉ mở loopback `5433`; giữ nguyên database ứng dụng cũ.
- [x] Nạp schema và bốn CTĐT từ SQL của nhánh database; verify trực tiếp 26/26.
- [x] Test views, học lại, CHECK/FK/UNIQUE trên PostgreSQL thật; dữ liệu test rollback.
- [x] Nạp lại không tăng số bản ghi, dữ liệu giữ nguyên sau restart.
- [x] Full suite 157 passed, 10 skipped; Ruff đạt.
- [x] Hướng dẫn và bằng chứng tại [DOCKER_VERIFICATION.md](../database/DOCKER_VERIFICATION.md).
- [ ] Tích hợp schema HUS vào ứng dụng và luồng lấy bảng điểm từ cổng đào tạo.

## Nền tảng trước đợt Docker HUS

Trạng thái ngày 2026-10-15, sau khi hoàn thiện phần A — metadata/runtime/kiểm thử.

- [x] Có cấu hình PostgreSQL/Docker, SQLAlchemy, Alembic và seed theo định dạng runtime cũ.
- [x] Có mẫu metadata Khoa học dữ liệu, 65 học phần, bằng chứng theo trường và hướng dẫn bàn giao.
- [x] Loại skill, secrets, môi trường, cache và backup khỏi nội dung publish.
- [x] Dọn file ngày 2026-10-15: bỏ schema transcript chỉ re-export và không được sử dụng, bỏ kế hoạch phần A đã hoàn thành, giữ bản nghiệm thu/audit và kế hoạch B/C/D; sửa tham chiếu liên quan, dọn cache local.
- [ ] Hoàn thiện và thẩm định dữ liệu các ngành theo đặc tả metadata.
- [x] Tích hợp envelope metadata 1.0 với loader, builder, validator và seed; giữ compatibility legacy, identity/revision, null/evidence/vocabulary và AND/OR.
- [x] Thay fixture khôi phục từ backup bằng bộ giả lập nhỏ độc lập; test nghiệp vụ không phụ thuộc catalog sản phẩm đã xóa.
- [x] Chạy test PostgreSQL trên container test riêng, bao gồm round-trip, idempotence, revision history, rollback, constraints và migration upgrade/downgrade/upgrade.
- [x] Sửa counted_in_total cho tín chỉ/GPA, từ chối transcript trùng môn chưa có chính sách retake, bổ sung API progress theo nhóm/track/path.
- [x] Tách nghiệm thu nguồn bốn ngành qua full_catalog_acceptance; mặc định skip rõ ràng khi chưa được cung cấp nguồn, explicit missing path phải fail.
- [ ] Hoàn thiện phân trách nhiệm backend và bảo vệ frontend trước phản hồi bất đồng bộ cũ.
- [ ] Hoàn thiện các tính năng module còn thiếu theo đặc tả hệ thống.

Kết quả cuối cùng được ghi trong [execution ledger](superpowers/plans/2026-10-14-metadata-runtime-progress.md). Ruff và builder kiểm tra mẫu/fixtures đạt. Database sản phẩm, container và volume hiện hành không bị thay đổi; container test riêng được dọn sau kiểm thử. Các task B/C/D và dữ liệu bốn ngành còn thiếu chưa được nghiệm thu. Checklist này không chứng nhận toàn bộ sản phẩm đã hoàn tất.

Kiểm tra mặc định: **108 passed, 26 skipped** (16 PostgreSQL thiếu URL + 10 full-source acceptance). Với PostgreSQL test riêng được chỉ định: **124 passed, 10 skipped**; tất cả integration PostgreSQL đã chạy. Còn một deprecation warning Starlette/httpx; không nâng dependency trong phần A.

Sau đợt dọn file, đã chạy lại kiểm thử offline: **108 passed, 26 skipped**; Ruff, builder trên mẫu 65 môn và bốn fixture tổng hợp, cùng `git diff --check` đều đạt. Kết quả PostgreSQL ở trên thuộc lần nghiệm thu phần A; không chạy lại PostgreSQL, browser, model provider hay CI remote trong đợt dọn file.
