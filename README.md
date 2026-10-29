# SE_Project — Explainable Course Recommender (AI-07)

Ứng dụng web giúp sinh viên xem tiến độ học tập, xác định các môn đủ điều kiện và nhận gợi ý môn học có giải thích. Backend dùng FastAPI, giao diện HTML/CSS/JavaScript tĩnh và runtime đọc catalog HUS từ PostgreSQL (Neon hoặc Docker tùy cấu hình).

## Trạng thái hiện tại

- Runtime dùng database HUS `ai07` theo `DATABASE_URL`. Có thể dùng Neon hoặc Docker local (`127.0.0.1:5433`, container `se_hus_db`); không mặc định hai máy dùng cùng cấu hình.
- Có bốn catalog HUS: Toán học, Toán tin, Khoa học máy tính và thông tin, và Khoa học dữ liệu. Snapshot hiện có lần lượt 65, 67, 90 và 68 học phần; 174 mã học phần dùng chung tạo thành 290 membership trong các chương trình. Catalog được giữ theo revision và công bố cùng một transaction.
- Catalog hiện mang trạng thái `draft_unverified`: import thành công không đồng nghĩa nguồn PDF hoặc quy định học vụ đã được xác minh. Điều kiện tiên quyết chưa rõ sẽ khóa môn liên quan.
- Sinh viên đăng nhập trực tiếp bằng tài khoản cổng đào tạo VNU; admin dùng tài khoản/mật khẩu riêng. Không cần đăng ký email cá nhân. Bảng điểm nguồn được lưu theo tài khoản đã xác minh; giao diện nhập điểm thủ công đã được gỡ.
- Database legacy và volume cũ được giữ riêng để rollback. Hướng dẫn cutover và rollback nằm trong [database/HUS_RUNTIME.md](database/HUS_RUNTIME.md).

## Chức năng hiện có

- Xem hồ sơ, bảng điểm và thống kê mô tả từ nguồn VNU; giữ nguyên các lượt học và điểm nguồn.
- Lấy hồ sơ và bảng điểm mới từ VNU khi đăng nhập; giữ dữ liệu đã lưu nếu lần lấy nguồn mới gặp lỗi.
- Quản trị viên quản lý tài khoản/quyền/trạng thái, không mặc định xem bảng điểm người khác.
- Backend tính eligibility, progress, recommendation và advisor được giữ; luồng cá nhân từ VNU còn chờ completeness, mapping chương trình và chính sách học vụ được xác minh. Giao diện chưa mở kết quả học vụ khi thiếu các điều kiện này.

Các gợi ý không xác nhận môn có được mở trong một học kỳ cụ thể hay không. Hệ thống không xếp lịch học, xử lý xung đột lớp hoặc chứng nhận quy định chính thức của trường.

## Giới hạn và phạm vi chưa triển khai

- Đã có đăng nhập VNU qua connector, phiên app trong DB, lưu/cập nhật bảng điểm và đăng nhập admin riêng. Chưa tích hợp OAuth/SSO chính thức, OCR bảng điểm hoặc RAG HUS hoạt động.
- API cá nhân dùng `/me/profile`; các `/profiles/...` legacy đã đóng với 410. Không có tự động đồng bộ VNU hằng tuần.
- `data/curricula/` chỉ giữ một mẫu metadata Khoa học dữ liệu 2022; mẫu này không phải nguồn catalog runtime và không đủ để seed bốn catalog.
- `database/data/hus_source.json` là nguồn catalog HUS dùng bởi publisher. Không chứa hồ sơ sinh viên.
- Không có tự động fallback sang JSON khi PostgreSQL lỗi. Muốn dùng JSON phải chọn rõ backend và cung cấp bộ catalog phù hợp.

Xem [lưu nhiều kế hoạch học kỳ](docs/SEMESTER_PLANS.md) trong tab Điều kiện học.

## Cấu trúc repository

| Đường dẫn | Nội dung |
|---|---|
| `app/` | FastAPI, API schemas/routes, nghiệp vụ transcript, eligibility, progress, recommendations, advisor và giao diện tĩnh. |
| `database/` | HUS PostgreSQL, migration riêng, catalog builder/publisher, công cụ kiểm tra và hướng dẫn vận hành. |
| `database/data/hus_source.json` | Export catalog HUS dùng để xây dựng và công bố các revision. |
| `data/` | Mẫu metadata được giữ lại; không phải catalog runtime đầy đủ. |
| `tests/` | Test được chia theo chức năng; xem [tests/README.md](tests/README.md). |
| `docs/` | Đặc tả hệ thống, thiết kế dữ liệu và bằng chứng/kế hoạch kỹ thuật. |
| `modules/` | Tài liệu phân chia trách nhiệm module; không phải bằng chứng rằng module đã hoàn thành. |
| `.agent/` | Memory dự án và hướng dẫn cho agent; xem [`.agent/AGENTS.md`](.agent/AGENTS.md). |

## Cài đặt và chạy local

Hướng dẫn chuẩn: **[docs/LOCAL_SETUP.md](docs/LOCAL_SETUP.md)** — cài mới bằng
Conda `SE_Project` hoặc `.venv`, Playwright/Chrome, Neon hoặc Docker, cấu hình
`.env`/`.env.auth`, migration, catalog và cách xử lý lỗi khởi động.

Nếu máy đã cài đủ dependency và database đã nâng cấp:

```bash
conda activate SE_Project
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Mở <http://127.0.0.1:8000/>. `/health` kiểm tra tiến trình; `/ready` kiểm tra
schema/catalog. Sau pull có migration mới, sao lưu DB rồi chạy
`python -m database.tools.migrate upgrade`. Head hiện tại `hus_20261028_08`.
Giữ nguyên cấu hình và khóa đã có; không seed/publish lại chỉ để chạy app.
Worker VNU dùng Google Chrome chạy nền. Dùng một worker; restart/reload mất
cookie VNU trong RAM. Tắt LLM bằng `RECOMMENDATION_LLM_ENABLED=false` nếu cần.

## Kiểm thử và kiểm tra dữ liệu

```powershell
python -m pytest -q -m "not postgres and not hus_postgres and not full_catalog_acceptance"
python -m ruff check .
python -X utf8 tools/build_catalogs.py --check
python -X utf8 tools/build_catalogs.py --check --root tests/support/fixtures/catalogs
```

Test mặc định dùng fixture tổng hợp và không gọi dịch vụ AI hay mạng thật. Test PostgreSQL có marker `postgres`, cần `TEST_DATABASE_URL` và chỉ tạo/xóa schema ngẫu nhiên riêng. Test HUS có marker `hus_postgres`, cần `HUS_TEST_DATABASE_URL` trỏ tới HUS Docker `ai07` trên loopback: một nhóm test tạo rồi xóa database tạm, nhóm kiểm tra schema ghi dữ liệu tổng hợp trong transaction và rollback. Không dùng URL Neon hoặc database production cho test. Acceptance test cần nguồn catalog đã được review có thể được bỏ qua nếu chưa truyền `--full-catalog-root`.

## API chính

- `GET /programs`, `GET /courses?program_id=...`: danh sách ngành và môn học.
- `POST /transcript/summary`, `POST /eligibility`: tổng hợp bảng điểm và kiểm tra điều kiện.
- `POST /recommendations`, `POST /recommendations/what-if`: gợi ý và xếp hạng lại trên tập đủ điều kiện.
- `POST /auth/vnu`: sinh viên đăng nhập VNU trực tiếp; `POST /auth/login`: admin local.
- `GET /me/profile`, các `/me/portal-*`: hồ sơ nguồn/cập nhật bảng điểm theo tài khoản.
- `GET /admin/users`, `PATCH /admin/users/{account_id}`: quản lý tài khoản, chỉ dành cho admin.
- `POST /advisor/chat`: tư vấn trong phạm vi sản phẩm.

## Tài liệu thêm

- [HUS runtime, migration và rollback](database/HUS_RUNTIME.md)
- [Kiến trúc và hành vi sản phẩm](docs/SYSTEM_SPECIFICATION.md)
- [Thiết kế database](docs/DATABASE_DESIGN.md)
- [Đặc tả metadata catalog](docs/COURSE_METADATA_SPECIFICATION.md)
- [Checklist nền tảng](docs/CODEBASE_CHECKLIST.md)
- [Quyết định kiến trúc HUS/legacy](docs/adr/0001-hus-runtime-and-rollback.md)
- [Hướng dẫn cộng tác](docs/CONTRIBUTING.md)
- [Kế hoạch dự án lịch sử](.agent/KE_HOACH_DU_AN.md)

Kế hoạch lịch sử và tài liệu module không ghi đè trạng thái runtime hiện tại trong README, memory dự án và tài liệu HUS runtime.
