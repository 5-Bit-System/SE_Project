# Các module của hệ thống

Module là một thành phần có chức năng, đầu vào/đầu ra và ranh giới rõ ràng trong hệ thống. Số module được xác định theo chức năng, không theo số người trong nhóm. Một người có thể tham gia nhiều module; một module có thể do nhiều người cùng phát triển.

| Module | Vai trò trong hệ thống | Đặc tả |
|---|---|---|
| Catalog | Nạp và kiểm tra dữ liệu của đúng ngành đã chọn | [01-catalog.md](01-catalog.md) |
| Hồ sơ sinh viên | Tiếp nhận và kiểm tra ngành, môn đã qua, mục tiêu, giới hạn tín chỉ | [02-profile-api.md](02-profile-api.md) |
| Điều kiện học | Kiểm tra tiên quyết, nhóm tự chọn và quy định chương trình | [03-rules.md](03-rules.md) |
| Đề xuất môn học | Điều phối việc gợi ý, xếp hạng, kiểm tra kết quả và giải thích | [04-ranking-llm.md](04-ranking-llm.md) |
| Giao diện | Nhận thông tin, hiển thị gợi ý và thử tình huống what-if | [05-web-ui.md](05-web-ui.md) |

Các số 01–05 chỉ dùng để sắp xếp tài liệu, không phải số thứ tự thành viên. Bốn ngành là bốn bộ dữ liệu của cùng module Catalog, không phải bốn module riêng. LLM là dịch vụ bên ngoài mà module Đề xuất môn học có thể gọi. API không phải một module nghiệp vụ riêng: mỗi module có thể có các API của nó.

## Cấu trúc code theo module — mục tiêu, chưa refactor

```text
app/
├── main.py                         # Khởi tạo FastAPI, ghép các router
├── modules/
│   ├── __init__.py
│   ├── catalog/
│   │   ├── __init__.py
│   │   ├── router.py               # API danh sách ngành và môn
│   │   ├── service.py              # Kiểm tra và cung cấp catalog
│   │   ├── repository.py           # Đọc JSON của ngành đã chọn
│   │   └── schemas.py              # Course, Program, Catalog
│   ├── profile/
│   │   ├── __init__.py
│   │   ├── service.py              # Kiểm tra hồ sơ sinh viên
│   │   └── schemas.py              # Các trường thông tin sinh viên
│   ├── eligibility/
│   │   ├── __init__.py
│   │   ├── service.py              # Bộ kiểm tra điều kiện học
│   │   └── schemas.py              # Kết quả và lý do loại môn
│   └── recommendation/
│       ├── __init__.py
│       ├── router.py               # API nhận yêu cầu gợi ý
│       ├── service.py              # Điều phối, kiểm tra kết quả cuối
│       ├── schemas.py              # Request và response gợi ý
│       ├── ranking.py              # Xếp hạng dự phòng
│       └── llm_adapter.py          # Gọi LLM, timeout và parse kết quả
└── static/                         # Module giao diện hiện tại
    ├── index.html
    ├── app.js
    └── styles.css
```

Đây là cấu trúc đề xuất, chưa phải cây thư mục đã có. Bản nền vẫn dùng `app/catalog.py`, `app/models.py`, `app/rules.py`, `app/ranking.py`, `app/service.py` và `app/main.py`. Từng đặc tả chỉ rõ code hiện tại và vị trí mục tiêu.

Không phải module nào cũng cần đủ router/service/repository. Catalog đọc JSON nên có repository; hồ sơ hiện chỉ được gửi trong request, không có tài khoản hoặc lưu hồ sơ nên chưa cần database, CRUD hay repository riêng. Trong FastAPI, router đóng vai trò nhận request tương tự controller ở ví dụ Java.

Một lần gợi ý đi theo luồng: Giao diện → Recommendation router → Recommendation service → Profile + Catalog + Eligibility → bộ xếp hạng → kiểm tra kết quả → Giao diện. Một request không nhất thiết đi qua database.

Thư mục này chỉ chứa đặc tả kỹ thuật: vai trò, interface, chức năng, ranh giới và tiêu chí kiểm thử. Nhân sự, task, nhánh Git và review nằm trong [bản chia việc](../docs/PHAN_CHIA_CONG_VIEC.md). Xem sơ đồ và luồng xử lý tại [kiến trúc hệ thống](../docs/KIEN_TRUC_HE_THONG.md).
