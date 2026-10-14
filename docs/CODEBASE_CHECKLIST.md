# Checklist codebase

Trạng thái ngày 2026-10-14, sau khi chuyển dữ liệu sang mẫu bàn giao một ngành.

- [x] Có cấu hình PostgreSQL/Docker, SQLAlchemy, Alembic và seed theo định dạng runtime cũ.
- [x] Có mẫu metadata Khoa học dữ liệu, 65 học phần, bằng chứng theo trường và hướng dẫn bàn giao.
- [x] Loại skill, secrets, môi trường, cache và backup khỏi nội dung publish.
- [ ] Hoàn thiện và thẩm định dữ liệu các ngành theo đặc tả metadata.
- [ ] Tích hợp envelope/metadata mới với loader, builder, validator và seed.
- [ ] Bổ sung lại fixture profile phù hợp và đưa các test catalog về trạng thái đạt.
- [ ] Chạy lại test PostgreSQL với database test được chỉ định.
- [ ] Hoàn thiện phân trách nhiệm backend và bảo vệ frontend trước phản hồi bất đồng bộ cũ.
- [ ] Hoàn thiện các tính năng module còn thiếu theo đặc tả hệ thống.

Kiểm tra hiện tại: Ruff đạt; pytest 22 passed, 21 failed, 11 skipped. Mốc 54/54 trước đây là kết quả lịch sử trước khi thay đổi dataset. Checklist này không chứng nhận toàn bộ sản phẩm đã hoàn tất.
