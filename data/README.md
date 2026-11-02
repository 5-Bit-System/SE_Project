# Dữ liệu mẫu để xây dựng catalog

Thư mục `data/curricula` giữ **một ngành mẫu: Khoa học dữ liệu (khóa 2022), 65 học phần**.

Xem [hướng dẫn bàn giao](curricula/khdl_7460108_2022/README.md) và [đặc tả metadata](../docs/COURSE_METADATA_SPECIFICATION.md).

Các catalog ngành khác, profile tổng hợp và báo cáo cũ đã được gỡ khỏi `data` theo yêu cầu. Bản sao trước thay đổi nằm tại `backups/data_before_single_major_sample_20261014.zip`, bên ngoài thư mục này.

Mẫu dùng hợp đồng metadata mục tiêu, không phải bộ seed runtime hiện hành. Các lệnh kiểm tra/seed vốn yêu cầu đủ bốn ngành sẽ không dùng được nguyên trạng. PostgreSQL hiện có chưa bị thay đổi bởi việc chuẩn bị mẫu này.

Trong `data/hus/releases/` còn [phần lưu lại của lượt crawl cũ](hus/releases/2026-10-22-3a45aae-candidate/README.md).
Ngày 26/10/2026, 106 file Markdown crawl và `processed/catalog.json` chứa bản sao
nội dung Markdown đã được xóa theo yêu cầu để chờ dữ liệu thay thế. Chỉ còn HTML
gốc và metadata nguồn; bộ này đã ngừng sử dụng, không phải corpus RAG được phê duyệt.
