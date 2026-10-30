# Review trước commit implementation

Thực hiện bởi Codex sau GREEN 78 tests, trước implementation commit; chưa có
review/approval của sinh viên hay teammate.

| Câu hỏi | Evidence/decision |
|---|---|
| Breaking shape/status của client cũ? | Hàm `routes.courses` không sửa; response_model list[Course] không sửa. Legacy request array/fields/types/order/extras/error tests pass. |
| Schema Course/nguồn/catalog bị thay? | Không sửa Course, source, revision hoặc migration; page model riêng trong schemas/catalog.py. |
| Pipeline đúng? | `search_courses`: filter AND và q OR → sorted toàn tập → len → slice; total không phải độ dài trang. |
| Ties có xác định? | Name: `(name.casefold(),code)`; credits: `(credits,code)`; code unique theo repository. Unit thử 24 hoán vị các bản ghi tie cho mỗi sort. |
| Tránh state mutation? | Comprehension + sorted tạo list mới; không `.sort()` trên catalog.courses. Repeated/model_dump equality test pass. |
| Có catch/default giả thành công? | Không catch exception trong service; route chỉ bắt domain CatalogError/ValueError theo pattern hiện hữu. Storage handlers giữ 503/500. Failure contract pass. |
| Có query unsafe? | Không ghép SQL hoặc tên đường dẫn từ query mới; dùng loader hiện có, q substring literal `%` không wildcard. |
| Dependency/migration/scope? | Ba file production (route/schema/service), README API note; không runtime dependency, không DB write hoặc UI/VNU thay đổi. |
| Test oracle đáng tin? | Mã kết quả cố định từ test specification, không import service để tính expected; legacy serialization bổ sung assertions fields/type có thật mà consumer dùng. |
| Còn giới hạn? | Offset không snapshot qua nhiều request; sort không phải Vietnamese collation; chỉ benchmark JSON synthetic, không PostgreSQL. |

RED `a5aab95c9d8453093621453b25f5807e584e15a3`: `red.log/json`.
GREEN đầu `green.log/json`: 78 passed; Ruff `lint-initial`: exit0.
Full offline/builder/analytics có log riêng; kết quả tổng hợp cuối ở REPORT.md.
