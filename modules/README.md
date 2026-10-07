# Các module của hệ thống

Module là một thành phần có chức năng, đầu vào/đầu ra và ranh giới rõ ràng trong hệ thống. Số module được xác định theo chức năng, không theo số người trong nhóm. Một người có thể tham gia nhiều module; một module có thể do nhiều người cùng phát triển.

| Module | Vai trò trong hệ thống | Đặc tả |
|---|---|---|
| Catalog | Nạp và kiểm tra dữ liệu của đúng ngành đã chọn | [01-catalog.md](01-catalog.md) |
| Hồ sơ, API và điều phối | Kiểm tra hồ sơ, gọi các thành phần, kiểm tra và trả kết quả cuối | [02-profile-api.md](02-profile-api.md) |
| Bộ luật | Xác định môn đủ điều kiện theo quy định trong JSON | [03-rules.md](03-rules.md) |
| Xếp hạng | Ưu tiên các môn hợp lệ theo mục tiêu; baseline hoặc adapter LLM | [04-ranking-llm.md](04-ranking-llm.md) |
| Giao diện | Nhận thông tin, hiển thị gợi ý và thử tình huống what-if | [05-web-ui.md](05-web-ui.md) |

Các số 01–05 chỉ dùng để sắp xếp tài liệu, không phải số thứ tự thành viên. Bốn ngành là bốn bộ dữ liệu của cùng module Catalog, không phải bốn module riêng. LLM là dịch vụ bên ngoài mà module Xếp hạng có thể gọi.

Thư mục này chỉ chứa đặc tả kỹ thuật: vai trò, interface, chức năng, ranh giới và tiêu chí kiểm thử. Nhân sự, task, nhánh Git và review nằm trong [bản chia việc](../docs/PHAN_CHIA_CONG_VIEC.md). Xem sơ đồ và luồng xử lý tại [kiến trúc hệ thống](../docs/KIEN_TRUC_HE_THONG.md).
