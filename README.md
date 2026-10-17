# SE_Project — Explainable Course Recommender (AI-07)

Ứng dụng web giúp sinh viên xem tiến độ học tập, xác định các môn đủ điều kiện và nhận gợi ý môn học có giải thích. Backend dùng FastAPI, giao diện HTML/CSS/JavaScript tĩnh và runtime hiện đọc catalog HUS từ PostgreSQL chạy bằng Docker.

## Trạng thái hiện tại

- Runtime chính dùng database `ai07` tại `127.0.0.1:5433`, container `se_hus_db`, volume `se_hus_pgdata`.
- Có bốn catalog HUS: Toán học, Toán tin, Khoa học máy tính và thông tin, và Khoa học dữ liệu. Snapshot hiện có lần lượt 65, 67, 90 và 68 học phần; 174 mã học phần dùng chung tạo thành 290 membership trong các chương trình. Catalog được giữ theo revision và công bố cùng một transaction.
- Catalog hiện mang trạng thái `draft_unverified`: import thành công không đồng nghĩa nguồn PDF hoặc quy định học vụ đã được xác minh. Điều kiện tiên quyết chưa rõ sẽ khóa môn liên quan.
- Bảng `accounts`, `students` và `course_attempts` đang trống. Người dùng nhập bảng điểm thủ công; transcript chỉ tồn tại trong phiên trình duyệt và bị xóa khi đổi ngành.
- Database legacy và volume cũ được giữ riêng để rollback. Hướng dẫn cutover và rollback nằm trong [database/HUS_RUNTIME.md](database/HUS_RUNTIME.md).

## Chức năng hiện có

- Chọn một ngành và chỉ làm việc với catalog của ngành đó; đổi ngành sẽ xóa transcript và kết quả gợi ý hiện tại.
- Nhập môn đã đạt hoặc nhập điểm hệ 10; xem tín chỉ tích lũy, GPA và tiến độ chương trình.
- Kiểm tra điều kiện môn học dựa trên tiên quyết, nhánh học, giới hạn tín chỉ và quy tắc chương trình đã có trong catalog.
- Gợi ý và xếp hạng các môn đủ điều kiện. What-if có thể đổi trọng số/xếp hạng nhưng không thay đổi eligibility.
- Advisor hỗ trợ định hướng môn học và giải thích kết quả. Khi tắt LLM, hệ thống có thể dùng xếp hạng offline.

Các gợi ý không xác nhận môn có được mở trong một học kỳ cụ thể hay không. Hệ thống không xếp lịch học, xử lý xung đột lớp hoặc chứng nhận quy định chính thức của trường.

## Giới hạn và phạm vi chưa triển khai

- Chưa có đăng nhập, đồng bộ cổng đào tạo, lưu transcript sinh viên, nhập bảng điểm bằng OCR hoặc crawler/knowledge base để hỏi đáp quy định HUS.
- Profile API hiện trả danh sách rỗng vì dữ liệu sinh viên/profile runtime chưa được nạp.
- `data/curricula/` chỉ giữ một mẫu metadata Khoa học dữ liệu 2022; mẫu này không phải nguồn catalog runtime và không đủ để seed bốn catalog.
- `database/data/hus_source.json` là nguồn catalog HUS dùng bởi publisher. Không chứa hồ sơ sinh viên.
- Không có tự động fallback sang JSON khi PostgreSQL lỗi. Muốn dùng JSON phải chọn rõ backend và cung cấp bộ catalog phù hợp.

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

## Chạy local trên Windows

Yêu cầu Python 3.11+, Docker Desktop và PowerShell. Các bước dưới đây giữ nguyên file cấu hình có sẵn; chỉ tạo file mẫu nếu file đích chưa tồn tại.

### 1. Tạo môi trường Python

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt -c requirements-lock.txt
```

### 2. Chuẩn bị cấu hình local

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
if (!(Test-Path database/.env.docker)) { Copy-Item database/.env.example database/.env.docker }
```

Đặt mật khẩu local trong `database/.env.docker`. Trong `.env`, đặt `DATABASE_URL` trỏ tới cùng database `ai07` ở cổng `5433`, đặt `DATABASE_MODEL=hus` và `STORAGE_BACKEND=postgres`. Ví dụ dạng URL:

```text
postgresql+psycopg2://ai07:<local-password>@127.0.0.1:5433/ai07?sslmode=disable
```

Không ghi credentials vào Git hoặc gửi chúng về frontend. Công cụ database đọc `HUS_DATABASE_URL` từ process hoặc file local `database/.env.docker`; FastAPI đọc `DATABASE_URL` từ process hoặc `.env` ở gốc repository.

### 3. Khởi động database và công bố catalog

```powershell
docker compose --env-file database/.env.docker -f database/docker-compose.yml up -d --wait
python -m database.tools.migrate upgrade
python -m database.tools.publish_catalogs --dry-run
python -m database.tools.publish_catalogs
```

Lệnh publish kiểm tra đủ bốn catalog trước khi thay đổi active revisions. Chạy lại với nội dung không đổi sẽ dùng lại revision theo content hash. Không dùng root `alembic upgrade head` cho HUS; đó là migration history của database legacy. Không chạy `docker compose down -v` nếu cần giữ dữ liệu.

### 4. Chạy ứng dụng

Để chạy offline, đặt `RECOMMENDATION_LLM_ENABLED=false` trong `.env`:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Mở <http://127.0.0.1:8000/>. `/health` kiểm tra tiến trình, `/ready` kiểm tra kết nối và catalog, còn `/docs` hiển thị OpenAPI. Nếu bật LLM, cấu hình API key ở server-side trong `.env`; không đưa key vào JavaScript hoặc response API.

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
- `GET /profiles`, `GET /profiles/{profile_id}`: profile demo nếu được nạp.
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
