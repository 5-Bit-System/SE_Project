# Rà soát và dọn dẹp dự án — 2026-10-29

Đã thực hiện đủ năm giai đoạn trong phạm vi có thể xác minh an toàn. Xóa 360
file cache sinh tự động, tổng cộng **5.403.157 bytes (~5,15 MiB)**; sửa nhỏ hai
file Python để bỏ một helper không dùng và một nhánh code trùng. Không xóa file
mã nguồn, dependency, tài liệu, PDF, SQL, dữ liệu nguồn hay cấu hình.

## 1. Phạm vi và trạng thái ban đầu

- Workspace: `D:/SE_Project`; dùng Python trong `.venv` và toolkit local.
- Nhánh hiện tại: `chore/remove-old-crawl-markdown-20261026`, HEAD `65d981f`
  (`chore: retire old HUS crawl markdown`). Commit này đã tồn tại trước lần rà
  soát; không phải commit do tác vụ này tạo. Memory cũ ghi `7650c12`, nên báo cáo
  dùng trạng thái Git thực tế cho lần làm việc này.
- Có **446 file tracked** và **3 file untracked** trước khi làm. Git đã báo 12
  file tracked bị sửa, gồm memory, README, VNU backend/UI/tests và RAG handoff;
  ba file untracked nằm trong `.vscode/`, `tests/integrations/` và `tools/`.
  Toàn bộ các thay đổi có sẵn được giữ nguyên byte.
- Đã đọc hướng dẫn dự án, README, cấu hình dependency/pytest/Ruff/CI/Compose,
  entry points, các router/service và tài liệu bảo toàn dữ liệu. Quét AST toàn
  bộ **168 file Python** trong nguồn/test hiện có; lập danh sách import và định
  nghĩa, tìm tên không được tham chiếu và hàm trùng để kiểm tra tiếp.
- Kiểm tra **11 file JavaScript/MJS**, liên kết tài nguyên HTML/CSS và đối chiếu
  hash file trong các bản lưu. Không coi kết quả tìm tên/import là bằng chứng
  duy nhất để xóa. Không review/sửa mã thư viện trong `.venv` hoặc vendor của
  `project-toolkit`; không đọc nội dung credentials hay bảng điểm cá nhân.

## 2. Công nghệ, entry points và phụ thuộc

| Nhóm | Entry point / quan hệ chính | Kết luận khi dọn |
|---|---|---|
| Web/API | `tools/run_local.py` kiểm tra kết nối trước khi chạy Uvicorn; `app/main.py` tạo FastAPI, middleware, lifespan, static mount và bốn router | Giữ launcher, router và các hàm được đăng ký bằng decorator |
| Sinh viên VNU | `/auth/vnu` → worker Python/Chrome/Playwright → bằng chứng xác thực → `app/auth/portal.py` → app session và snapshot theo chủ sở hữu | Giữ kiểm tra identity, CSRF/origin, owner/generation, giới hạn và lỗi mạng |
| Hồ sơ/cập nhật | `/me/profile`, `/me/portal-*` → RAM VNU session/job → snapshot parser/store → PostgreSQL | Cookie VNU ở RAM; không xóa session/source hoặc chạy đăng nhập thật |
| Quản trị | `/auth/login`, `/admin/users`, `/me/password` → auth repository/security/settings | Route và repository có kiểm tra quyền riêng; helper bị bỏ không tham gia các luồng này |
| Học vụ cá nhân | Xác nhận chương trình/khóa → binding/policy → AcademicContext → eligibility/progress/course board | Giữ mọi gate về completeness, phạm vi và kết quả chưa rõ |
| Xếp hạng/advisor | API → service → eligibility → ranker deterministic/LLM → validation/explanation | Hai ranker dùng chung lời gọi; adapter tùy chọn và fallback vẫn cần |
| Giao diện hiện hành | `index.html` tải theme, i18n, auth, workspace, portal, course-status, analytics và CSS tương ứng | Cả 15 tài nguyên trực tiếp đều tồn tại; không xóa CSS theo tìm kiếm tên class |
| Catalog/storage | `catalog.py` → adapter HUS PostgreSQL hoặc adapter legacy/JSON theo cấu hình | Import trong hàm và lựa chọn backend là phụ thuộc thật |
| Database | `database.tools.*`, `database/hus_alembic/`, SQL và nguồn `hus_source.json`; legacy có `alembic/`, `app/db/`, Compose riêng | Giữ cả hai migration history, công cụ kiểm tra và tài nguyên rollback |
| RAG/HUS ngoại tuyến | Công cụ tham chiếu trong root; implementation/dataset mới nằm ở checkout và output local trong `backups/` | Chưa phát hành vào runtime; không xóa source, manifest, quarantine hay checkout chưa xuất bản |
| Kiểm thử/CI | pytest, Ruff, Node assertions và script Chrome; CI có nhóm PostgreSQL riêng | Fixture, migration, entry point CLI và script chạy trực tiếp không phải file thừa |

Các dependency trực tiếp có vai trò cụ thể: FastAPI/Uvicorn phục vụ web,
Pydantic kiểm tra dữ liệu, SQLAlchemy/psycopg2/Alembic phục vụ storage/migration,
python-dotenv đọc cấu hình, Argon2 xử lý mật khẩu, httpx phục vụ adapter và test,
pytest/Ruff phục vụ kiểm chứng, Playwright phục vụ connector/Chrome.
`email-validator` vẫn được import khi nạp `app/auth/security.py`; chưa thể gỡ
package mà giữ nguyên module hiện tại. Không thay requirements hay lock file.

## 3. Phân loại và quyết định

### Nhóm 1 — Có đủ bằng chứng để dọn

| Đối tượng | Bằng chứng | Thực hiện |
|---|---|---|
| 353 file `__pycache__/*.pyc` ở root và hai checkout local, gồm cache parser dependency | Bytecode sinh bởi Python/pytest; không tracked trong repository tương ứng; không phải nguồn/manifest | Đã xóa từng file |
| 2 file `.pytest_cache`: `CACHEDIR.TAG`, `v/cache/nodeids` | Cache và chỉ mục test tự sinh; không phải báo cáo nghiệm thu | Đã xóa |
| 5 file `.ruff_cache`: `CACHEDIR.TAG` và 4 file cache phiên bản | Cache linter; không phải cấu hình lint | Đã xóa |
| `app/auth/dependencies.py::require_admin` | Quét AST và tìm tên trong source/test/config không có caller, import, export hoặc đăng ký động; chỉ còn nhắc tên trong kế hoạch lịch sử | Bỏ helper cùng khoảng trắng kèm theo, 7 dòng |
| Hai nhánh `KeywordRanker`/`LLMRanker` trong `recommend()` | Cùng gọi `rank(candidates, goal, preference=..., weights=...)`; đây là hai class thông thường | Gộp điều kiện `isinstance(..., (KeywordRanker, LLMRanker))`; giữ nhánh custom ranker và fallback |

Tổng thay đổi mã nguồn: **1 dòng thêm, 15 dòng bỏ**, giảm ròng 14 dòng.
Không thay endpoint, schema request/response, chính sách học vụ hay cấu hình.

Mỗi file cache được kiểm tra đường dẫn tuyệt đối nằm trong workspace, không
qua reparse point, đúng kiểu cache đã cho phép, đúng kích thước và SHA-256 ngay
trước khi xóa. Không dùng recursive delete, wildcard xóa hay `git clean`.
README và hai `.gitignore` trong cache vẫn được giữ theo yêu cầu bảo toàn tài
liệu/cấu hình. Cache có thể được tạo lại khi chạy ứng dụng hoặc công cụ.

### Nhóm 2 — Còn nghi vấn hoặc cần quyết định riêng; giữ nguyên

| Đối tượng | Vì sao chưa xóa | Việc cần làm nếu muốn tinh gọn tiếp |
|---|---|---|
| `app/static/app.js`, `dashboard.js` và CSS cho giao diện nhập tay cũ | HTML hiện hành không tải hai script, nhưng memory chủ động giữ để tham chiếu/rollback; code và test lịch sử có liên quan | Xác định chính thức phạm vi retirement trước khi bỏ cả bộ client và test liên quan |
| `tests/frontend/check_language.mjs` | Kiểm tra cú pháp đạt nhưng script thao tác DOM nhập tay cũ và cần CDP đang mở | Chuyển các assertion còn có ý nghĩa sang UI VNU hiện hành; chưa chạy script này lên phiên browser của người dùng |
| Email registration/verification cũ: `app/auth/mail.py`, một số hàm repository/security và copy UI | Route công khai đã trả 410, nhưng test vẫn import/patch mail và gọi `register`/`verify_email` để tạo fixture; cấu hình SMTP cần bảo toàn | Retirement phải xử lý cùng test/setup/dependency; không xóa lẻ module hoặc package |
| `validate_demo_profiles()` và loader profile legacy | Không thấy caller trực tiếp cho helper tổng kiểm tra, nhưng là API validation/nguồn tham chiếu của luồng legacy | Đánh giá contract CLI/library và rollback cùng luồng profile; không suy là rác từ số caller |
| 815 nhóm file có cùng hash trong tập file được bảo vệ ban đầu | Nhiều bản là cùng mã nguồn trong checkout riêng hoặc cùng payload gắn locator/manifest khác nhau | Kiểm tra vai trò, manifest và khả năng tái lập từng nhóm; chưa xóa bản nào chỉ vì trùng byte |
| Các bản build/delivery/review HUS lớn trong `backups/` | Có output bàn giao, original attachment, provenance và công việc chưa push; memory yêu cầu giữ | Chỉ dọn thêm khi chứng minh bản thay thế đầy đủ và không phá receipt/handoff |
| `tools/prepare_hus_corpus.py` và test đi kèm | Pipeline thử cũ đã ngừng, nhưng memory giữ source/test làm tham chiếu | Chờ quyết định retirement; không tự chạy lại trial hay tạo corpus mới |

### Nhóm 3 — Cần giữ

- Route FastAPI, dependency trong decorator, Pydantic validators, callback/parser
  methods, `__init__.py`, schema re-export và `__getattr__` lazy loader. Những
  tên này có thể không có lời gọi trực tiếp trong AST nhưng vẫn được framework dùng.
- CLI `main()`, Alembic `env.py`, `upgrade()`/`downgrade()`, cả SQL lịch sử và
  schema legacy: được gọi qua framework/cấu hình hoặc phục vụ rollback.
- PDF gốc, policy PDF phục vụ route, OCR/TXT/CSV/PNG bằng chứng, HTML raw, nguồn
  catalog, fixture tổng hợp, manifest/hash/receipt, báo cáo và tài liệu lịch sử.
- `.env`, `.env.auth`, `database/.env.docker`, file ví dụ/cấu hình, `.vscode/`,
  dữ liệu người dùng, secret và private handoff. Chỉ đối chiếu hash; không in giá trị.
- Hai checkout có công việc riêng dưới `backups/hus_pipeline_worktree_20261026`
  và `backups/vnu_login_network_20261028/source`. Đã so sánh Git status trước/sau;
  không đổi code, commit, branch hay index của chúng.
- Database dump, volume Docker, Git history, nguồn vendor và môi trường `.venv`.
  Không chạy migration, seed, publish catalog, database test hoặc thao tác Docker.

## 4. Kết quả kiểm chứng

| Kiểm tra | Kết quả |
|---|---|
| Baseline pytest trước sửa | 537 passed, 76 PostgreSQL cases deselected |
| Pytest sau sửa, có `--full-catalog-root docs/acceptance/hus_2022` | **537 passed, 76 deselected**, không skipped |
| Ruff toàn root, `--no-cache` | Đạt trước và sau sửa |
| Syntax Python bằng `compile`, không ghi bytecode | 168 file đạt |
| Node `--check` | 11 JavaScript/MJS đạt |
| Local import module paths và HTML/CSS resources | Không thiếu module nội bộ được quét; 15 tài nguyên HTML hiện diện, không thiếu URL tài nguyên CSS được phát hiện |
| Catalog fixture builder | Cả 4 catalog tổng hợp đạt |
| Catalog metadata sample builder | Mẫu KHDL 65 môn đạt |
| `node tests/frontend/check_analytics.mjs` | Đạt: retake, dấu phẩy, zero, unknown, tín chỉ và bộ lọc năm |
| Chrome `check_portal_auth` | Đạt: fresh POST và các trường hợp từ chối login/identity/challenge |
| Chrome `check_portal_resume` | Đạt: login một lần, resume bằng browser mới, rotation, conflict, expiry và challenge |
| Chrome `check_portal_profile_source` | Đạt: thu thập profile sớm, giữ bảng điểm nguồn |
| `.venv/Scripts/python.exe -B -m pip check` | Không có dependency bị thiếu/xung đột theo metadata đã cài |
| SHA-256 và Git status | Đối chiếu **3.406 file duy nhất**; chỉ hai file mã nguồn nêu trên thay đổi có chủ đích. Không mất file bảo vệ, không đổi byte các sửa đổi có sẵn; hai checkout phụ giữ nguyên status |

Lệnh pytest dùng `-p no:cacheprovider`, `-B` và
`PYTHONDONTWRITEBYTECODE=1` để kiểm tra không tạo lại cache vừa dọn.
Còn một Starlette/httpx deprecation warning đã có từ baseline. Không cập nhật
dependency để xử lý warning trong tác vụ vệ sinh này.

Các ca Chrome dùng nguồn/identity giả lập và chặn/intercept mạng; không đăng
nhập VNU thật, không đọc điểm cá nhân, không gửi thư và không khởi động lại app.
76 test PostgreSQL được loại khỏi lần chạy này để không tạo/xóa schema/database
hay ghi dữ liệu trong tác vụ dọn dẹp. Kiểm chứng này không thay thế nghiệm thu
học vụ hoặc kiểm tra production.

## 5. Bằng chứng và bàn giao

Thư mục bằng chứng local, được Git ignore: `backups/cleanup_20261029/`.

- `deleted-files.csv`: liệt kê đủ **360 đường dẫn đã xóa**, kích thước và hash.
- `deleted-caches.json`, `delete-plan.json`: kết quả và danh sách xóa đã xác minh.
- `inventory.json`, `summary.json`, `python-imports.json`, `definitions.json`:
  kiểm kê và kết quả quét tự động, không phải chỉ thị tự động xóa.
- `duplicate-files-candidates-only.json`: nhóm trùng hash ban đầu, tất cả được giữ.
- `status-before.json`, `repositories-before.json`, `protected-before.json`,
  `backup-protected-before.json`, `verification.json`: đối chiếu bảo toàn thay đổi.
- `baseline-offline.xml`, `final-offline.xml`: kết quả pytest trước/sau.
- `originals/app/`: bản trước sửa của đúng hai file code để so sánh/hoàn tác riêng.

Số bytes ở đầu báo cáo là tổng payload cache đã xóa; hồ sơ audit mới cũng chiếm
dung lượng, nên không diễn giải con số này thành dung lượng trống tăng ròng.

Không commit, push, tạo/merge PR, triển khai hoặc thay đổi runtime/database.
Báo cáo và hai chỉnh sửa mã nguồn được để local cùng nguyên trạng công việc có
sẵn. Phần còn nghi vấn ở nhóm 2 được giữ; không có thao tác phá hủy dữ liệu đang
chờ phê duyệt để hoàn thành phạm vi an toàn của lần dọn này.
