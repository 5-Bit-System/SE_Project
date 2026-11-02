# Test suite

Các test được chia theo chức năng của ứng dụng. Vào thư mục tương ứng để xem phạm vi chi tiết:

- `advisor/`: tạo lời khuyên và giải thích khóa học.
- `catalogs/`: dữ liệu chương trình, metadata, builder và seed catalog.
- `database/`: schema, migration, lưu trữ và runtime PostgreSQL/HUS.
- `eligibility/`: điều kiện tiên quyết và xác định khóa học đủ điều kiện.
- `progress/`: tiến độ chương trình, tín chỉ và GPA.
- `recommendations/`: xếp hạng và kết quả gợi ý.
- `storage/`: backend lưu trữ và hành vi đọc/ghi.
- `support/`: helper và dữ liệu fixture dùng chung; cấu hình pytest nằm ở `conftest.py`.
- `transcript/`: bảng điểm, môn đã hoàn thành và kiểm tra major.

Các fixture trong `support/fixtures/` là dữ liệu tổng hợp dành riêng cho test, không phải dữ liệu chương trình chính thức.
