# Tích hợp Điều kiện học — 26/10/2026

Nguồn đóng góp: nhánh feat/vnu-curriculum-planning, commit `5e1a9bf`.
Nhánh tích hợp giữ ancestry của commit đó và cơ chế auth/session trên main
`e781ab3`. Các báo cáo nghiệm thu tài khoản thật ở workspace của nhánh nguồn
không được coi là nghiệm thu độc lập cho hệ thống này.

## Những điểm giải quyết khi ghép

- Giữ study_app_session, async session(), origin/CSRF và account–VNU ownership.
  Không khôi phục study_portal_session hoặc đăng nhập portal cũ.
- Bổ sung ghi binding qua app.auth.portal trong cùng transaction với kiểm tra
  account/session/link; giữ thứ tự khóa account → session → portal owner.
- Giữ save(connection=...), _last_synced_at, session revocation, VNU RAM cookies,
  resume/reauth và reminder hiện có khi thêm collector và chẩn đoán mới.
- Chỉ thay nội dung tab Điều kiện học và các phần phụ thuộc để bảng cá nhân
  hoạt động. Giữ recommendation_service, dashboard, analytics và workspace logic.
- Không đưa catalog/tra cứu Toán tài năng, màn hình reference hoặc CSV vào đây.
- Cache HTML/asset dùng hash phiên bản để tránh trình duyệt giữ UI cũ.

## Database và vận hành

Không cần migration hoặc backfill. Binding được xác nhận theo từng owner trong
JSONB profile hiện có, có binding_schema_version=1 và revision catalog/policy.
Không tự xác nhận enrollment hoặc completeness của dữ liệu đang lưu.
Catalog revision/policy không còn phù hợp thì kết quả học thuật tiếp tục bị chặn.

Collector mới có thể tạo snapshot có collection_evidence; giữ rollback khi nguồn
mới thay đổi mà chưa đầy đủ. Retention hai snapshot hiện hành không đổi.
Không đổi tài khoản, mật khẩu, Gmail SMTP, active catalogs hoặc điểm nguồn.

Trước khi nạp bản tích hợp vào runtime, tạo backup kiểm tra được. Restart làm
mất cookies VNU trong RAM; phiên ứng dụng trong DB vẫn được quản lý theo cơ chế
hiện tại và lần cập nhật tiếp theo có thể cần reauth. Không reset seed/volume.
Rollback ưu tiên quay lại ứng dụng trước tích hợp; không tự restore toàn DB vì
có thể làm mất cập nhật hợp lệ sau backup.

## Kiểm chứng

Bộ test của bản tích hợp bao gồm offline/PDF acceptance, PostgreSQL trên
container dùng một lần, browser fixture cho bảng điều kiện/binding/collector
và regression module hiện tại. Browser PostgreSQL còn kiểm tra đăng nhập →
xác nhận chương trình → ba nhóm qua API thật với dữ liệu tổng hợp, kèm admin,
reload phiên, sync, logout, khóa tài khoản, VI/EN và mobile.

Số liệu cuối và commit phát hành được ghi ở PR/memory của phiên tích hợp.
Tài khoản thật cần được chủ tài khoản nghiệm thu sau nạp bản mới; không suy
nghiệm thu học thuật từ số test hoặc tự nâng cờ dữ liệu để vượt điều kiện.

Hợp đồng sử dụng/API: [COURSE_STATUS_BOARD.md](COURSE_STATUS_BOARD.md).
