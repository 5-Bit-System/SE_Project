# Tích hợp local và kế hoạch hoàn thiện luồng Admin — 03/11/2026

## Cập nhật: các sửa lỗi đã triển khai local

Sau khi xem bản tích hợp, người dùng yêu cầu sửa toàn bộ các mục còn lại. Phần
review/kế hoạch bên dưới được giữ làm lịch sử; trạng thái hiện tại là bảng này.
Mã sửa thuộc nhánh `integration/admin-console-20261103`. Người dùng đã yêu cầu
commit và bàn giao qua issue GitHub riêng cho các lỗi luồng Admin; trạng thái
commit và CI được ghi trong issue bàn giao. Không cập nhật GitHub main, không
thay cấu hình hoặc công bố catalog thật.

| Mục | Kết quả sửa và kiểm chứng |
|---|---|
| P0.1 Publish runtime | Tạo snapshot bất biến trong `hus_catalog_revisions` cùng transaction với trạng thái Admin và audit. CSV cập nhật các mã đã có trên một base revision cố định; mã mới cần gói nguồn HUS JSON đầy đủ qua builder hiện hành. Kiểm tra base cũ, schema, groups, quota, AND/OR và identity trước đổi active pointer. |
| P0.2 Validation | Một validator dùng cho import/revalidate/approve/publish; chặn tín chỉ âm, không hữu hạn, ngoài miền, không nguyên, tên rỗng, mã trùng, điều kiện sai và payload digest cũ. Không dùng source digest để thay cho payload digest. |
| P0.3 Bất biến/rollback | Dùng cùng advisory transaction lock với publisher HUS; published không được revalidate/review/sửa tại chỗ. Editor tạo draft mới. Rollback kiểm checksum manifest v2, payload, snapshot runtime và tài liệu nguồn trước đổi hai pointer. |
| P0.4 Nguồn mẫu | GET hàng đợi chỉ đọc. Thiếu tệp không sinh dữ liệu mẫu hay URL HUS giả. Explicit import chỉ nhận tài liệu có URL/title/hash thật; chặn mẫu legacy/synthetic khỏi publication và public retrieval. |
| P1.5 Document version | Sửa metadata đã duyệt/xuất bản tạo document ID mới, giữ lineage trong metadata. Bản cũ và manifest không đổi; published source không được đổi review tại chỗ. UI theo ID mới để duyệt lại. |
| P1.6 Test isolation | Test Admin chỉ nhận `HUS_TEST_DATABASE_URL` tường minh, dùng savepoint trong transaction rollback. Không đọc `.env` để chọn DB test. Có runner tracked và fixtures đủ 105 tài liệu; XSS/pagination không còn bỏ qua khi fixture thiếu. |
| P1.7 Phiên/giao diện/metrics | Bỏ response cũ theo session và lượt tải; xóa state khi logout/đổi tài khoản/quyền; test đảo thứ tự response và logout. Ghi metric từ `/me/recommendations`, chỉ lưu mã lỗi, có mốc bắt đầu và ghi rõ số liệu của phiên chạy hiện tại. |

Approval là quyết định xuất bản trong ứng dụng. Catalog nhập qua Admin vẫn là
`draft_unverified`; không tự cấp chứng nhận học vụ. Tệp CSV là tập thay đổi cho
mã đã có, không được dùng để xóa ngầm phần catalog còn lại. Gói JSON đầy đủ dùng
cùng định dạng nguồn với `database/data/hus_source.json`; builder kiểm định đầy đủ
trước tạo candidate. Bản nháp dựa trên snapshot đã cũ cần nhập/duyệt lại.

Nghiệm thu lần sửa:

- Full offline/PDF: **1.303 passed**, 106 DB deselected; thêm **2 test bảo vệ
  target DB** chạy riêng đạt. Chỉ còn cảnh báo Starlette/httpx đã tồn tại.
- Full PostgreSQL trên DB mới riêng: **106 passed**. Có test hai publisher đồng
  thời, audit failure, stale base, manifest/payload bị sửa, rollback và full-source.
- **14 suite Admin** đạt tổng hợp, gồm suite session/filter race mới; các ca lỗi
  ở lượt đầu đã được sửa và chạy lại. Runner tracked cũng chạy shell/race đạt.
- **7 suite sinh viên**, **50 ca RAG Chromium**, Node citation/model/analytics,
  Ruff, pip check, JS syntax, diff và hai catalog builders đạt.
- Bổ sung job `admin_console` trên CI với PostgreSQL và Chrome/Chromium riêng.
  YAML kiểm tra local đạt; kết quả ở đây là lần kiểm thử trước khi bàn giao.
  Trạng thái CI remote sau khi push được theo dõi riêng trong issue GitHub.
- Đã nạp mã sửa vào server local: `/health`, `/ready` 200, 23 static asset khớp
  disk; truy cập Admin/course-status vô danh vẫn 401. Không đăng nhập tài khoản
  thật, đọc bảng điểm, gọi model hay gửi email trong quá trình sửa/kiểm thử.

Chạy lại browser trên checkout sạch bằng [runner](../tools/verify_admin_console.py):
chuẩn bị DB PostgreSQL **tạm riêng** tên `ai07`, migrate/publish chỉ vào target đó,
đặt `HUS_TEST_DATABASE_URL`, `TEST_BASE_URL=http://127.0.0.1:8031`, rồi chạy
`python -m tools.verify_admin_console --reset-fixtures`. Cờ reset cho phép thay
fixture của DB tạm; runner từ chối target DB cấu hình của ứng dụng và cổng 8000.
Không chạy lệnh reset đối với DB thật. CI job tự cấp DB tạm từ checkout sạch.

Log/JUnit/probe lần sửa: `backups/admin_repair_20261103/`. Đây là bằng chứng local
ignored, không phải kết quả CI remote hay chứng nhận độ đúng học vụ của nguồn.
Hai database test tạm được dọn; database runtime, cấu hình và release HUS giữ
nguyên. Server được khởi động lại để nạp backend mới; phiên VNU RAM cũ không còn.

## Phạm vi và trạng thái

Yêu cầu: tích hợp nhánh Admin vào checkout local hiện tại, giữ đầy đủ các commit
của main và đề xuất kế hoạch sửa các luồng chưa hoàn chỉnh. Đây là tích hợp local,
chưa push, tạo PR, cập nhật GitHub main hoặc kích hoạt database thật.

- Baseline main: `05ffe0fa0d8aad9042f271a8b170876e2eff4c63`.
- Nhánh nguồn: `feat/dashboard-semester-drilldown-20261028`, tip
  `5b6e3716d9c1846113ed56b9f4e22055f290360f`.
- Nhánh tích hợp: `integration/admin-console-20261103`, tạo từ baseline main.
- Merge commit local: `d30f2e1b741a942d1b13d6d62e4a14dcf4aeb67c`, hai parent
  đúng baseline main và tip Admin ở trên. Kiểm tra không còn commit nào của
  `origin/main` hoặc nhánh nguồn nằm ngoài ancestry của bản tích hợp: `0 / 0`.
- Trước tích hợp: main có 127 commit riêng, nhánh Admin có 45 commit riêng.
  Merge giữ nguyên ancestry của cả hai bên, không cherry-pick/squash/rebase.
- Không có xung đột văn bản. Giữ giao diện recommendation, course map, auth/VNU,
  dependency lock và RAG demo riêng đang có trên main.
- Thay đổi test bổ sung chỉ sửa phạm vi selector, thứ tự sáu tab và đường dẫn
  chụp ảnh để kiểm thử bản tích hợp; chưa triển khai các sửa lỗi nghiệp vụ dưới đây.
  Merge cũng chuẩn hóa các dòng trắng/thừa khoảng trắng bị `git diff --check`
  phát hiện trong mã nguồn nhập từ nhánh Admin, không đổi hành vi.

Theo quy định repository, main vẫn giữ nguyên. Checkout local chuyển sang nhánh
tích hợp; mọi lần đưa kết quả lên main sau này phải qua PR/Create a merge commit.
Giữ nguyên tác giả và commit nguồn của đồng đội.

## Kiểm chứng

Tất cả thao tác database dùng container tạm riêng
`se_admin_integration_20261103`, loopback `55443`, PostgreSQL 16, database `ai07`
và `se_project_test`. Không dùng volume, account, phiên VNU hoặc database thật.
Server kiểm thử Admin dùng loopback `8031`, chỉ có tài khoản và tài liệu giả lập.

| Kiểm tra | Kết quả |
|---|---|
| Offline/PDF, bật bộ acceptance có sẵn | 1.285 passed, 99 deselected |
| PostgreSQL legacy/HUS/Admin | 99 passed, 1.285 deselected |
| Migration mới 09–12; publisher dry-run và publish vào DB tạm | Đạt |
| Giao diện sinh viên | 7 suite Chrome đạt sau sửa selector VNU-only |
| Giao diện Admin | 13 suite đạt; 8 suite chạy lại nguyên script sau sửa selector/portability và chuẩn hóa fixture |
| RAG riêng | Chromium smoke 50 câu hỏi đạt |
| Node citation, recommendation model, analytics | Đạt |
| Ruff, pip check, JS syntax, hai catalog fixture builder | Đạt |

Lần chạy offline đầu có cảnh báo Starlette/httpx đã tồn tại và hai cảnh báo
encoding của subprocess Windows. Chạy lại đủ 8 test metadata-builder với
`PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8`: đạt, không còn cảnh báo encoding.

Các test đạt không chứng minh luồng xuất bản Admin đã hoàn chỉnh. Các probe bổ
sung dưới đây đã tái hiện những trường hợp chưa được bộ test hiện tại bao phủ.
JUnit, log, ảnh và JSON probe nằm ở thư mục ignored
`backups/admin_integration_20261103/`; các file này không đi cùng fresh clone.

Lần browser đầu phát hiện shell còn giả định chỉ có ba tab, assertion overview
đọc cả số liệu của vùng khác và fixture tài khoản không khớp email mà test users
yêu cầu. Hai assertion được sửa để kiểm đúng UI hiện hành; harness dùng đúng
tài khoản giả lập mà test users yêu cầu. Không sửa dữ liệu hoặc tài khoản thật.

## P0 — Cần sửa trước khi cho phép xuất bản dữ liệu thật

### 1. Nối xuất bản Admin với catalog runtime

**Đã xác nhận:** [publication_gate.py](../app/curriculum/publication_gate.py)
bật `curriculum_revisions.is_active`, nhưng
[HusRepository](../app/infrastructure/hus_repository.py) đọc
`hus_catalog_revisions.active`. Probe xuất bản một revision Admin mới; revision
runtime trước và sau vẫn giống nhau.

**Cách sửa:** giữ bảng Admin làm staging/review; đưa bản đã duyệt qua bộ dựng và
publisher HUS hiện hành để tạo snapshot runtime hợp lệ. CSV hiện tại chỉ chứa
một phần dữ liệu, không được coi là catalog runtime hoàn chỉnh. Phải giữ nhóm,
quota, AND/OR, định danh ngành/cohort, provenance và trạng thái xác minh. Duyệt
CSV không tự biến dữ liệu thành `verified`.

**Nghiệm thu:** import → validate → approve → publish làm API catalog đọc đúng
revision mới; `/ready` đạt; binding/kế hoạch cũ bị xử lý đúng khi revision đổi.
Rollback trả đúng snapshot runtime cũ. Gây lỗi giữa giao dịch phải giữ nguyên
toàn bộ active catalog trước đó. Có kiểm tra hai admin publish đồng thời.

### 2. Dùng cùng bộ validation khi nhập và kiểm tra lại

**Đã tái hiện qua API:** CSV có `credits=-3` bị đánh `valid=false`, approve trả
400. Gọi `POST .../validate` lại trả `valid=true`; approve và publish đều trả 200.
Nguyên nhân: [validate_full_revision_payload](../app/curriculum/rule_service.py)
không kiểm đầy đủ tín chỉ/tên như
[validate_and_parse_csv](../app/curriculum/import_service.py).

**Cách sửa:** một validator payload chuẩn dùng cho import, edit, revalidate,
approve và publish. Kiểm định danh, mã/tên, tín chỉ hữu hạn và miền giá trị theo
schema, mã trùng, prerequisite, provenance. Validation phải gắn digest payload
hiện tại; không chấp nhận một source digest cũ thay cho nội dung đã thay đổi.

**Nghiệm thu:** tín chỉ âm/quá miền/NaN/Infinity, tên rỗng, mã trùng, vòng lặp,
thiếu prerequisite và digest cũ luôn bị chặn qua mọi đường vào. Active runtime
không đổi sau bất kỳ lần từ chối nào.

### 3. Giữ snapshot đã xuất bản bất biến và siết rollback

**Đã tái hiện qua API:** publish A → publish B → validate A → sửa prerequisite A
→ rollback A đều thành công. A được kích hoạt lại với payload có hash khác
manifest lần xuất bản ban đầu.

**Cách sửa:** revision đã published chỉ được đọc; muốn chỉnh phải clone sang ID
nháp mới. Revalidate không được hạ trạng thái snapshot đã xuất bản để mở lại
quyền sửa. Rollback kiểm đúng payload hash, manifest, scope và trạng thái đã
xuất bản, không chỉ kiểm có `published_at` và một manifest cũ. Dùng lock/CAS và
một transaction cho kiểm tra, đổi active pointer, audit; ngăn publish/edit/review
đồng thời làm lọt validation cũ.

**Nghiệm thu:** khóa được chuỗi thao tác trên; A và manifest giữ nguyên bytes.
Chỉ snapshot hợp lệ từng xuất bản mới rollback được; test cạnh tranh và lỗi
audit chứng minh không có active pointer hoặc dữ liệu cập nhật dở dang.

### 4. Bỏ tài liệu mẫu tự sinh trong luồng dữ liệu thật

**Đã xác nhận bằng mã:**
[seed_crawled_documents_from_disk](../app/crawler/document_review_service.py)
tạo nội dung mẫu gắn URL HUS khi thiếu thư mục/tài liệu. GET hàng đợi có thể gọi
hàm seed. Đây không phải dữ liệu thu thập đã có bằng chứng.

**Cách sửa:** GET chỉ đọc, thiếu nguồn trả hàng đợi rỗng/trạng thái thiếu dữ liệu.
Chuyển fixture sang test/demo tường minh, có nhãn synthetic. Nguồn thật cần tệp,
hash và locator gốc; không tự chế URL thay thế và không quét nguồn khi mở trang.
Giữ chính sách release corpus thủ công, không thêm scheduler/crawler dispatch.

**Nghiệm thu:** DB trống và nguồn thiếu không phát sinh document/job; dữ liệu mẫu
không lọt vào endpoint published hoặc RAG. Giữ nguyên release HUS đã ghim.

## P1 — Hoàn thiện vận hành và khả năng kiểm chứng

### 5. Phiên bản tài liệu và sự nhất quán nguồn

Bản hiện tại thu hồi approval/publication khi sửa metadata, nhưng vẫn sửa trên
cùng document ID. Cần giữ bản đã duyệt bất biến và tạo phiên bản nháp mới để
manifest đã xuất bản luôn trỏ tới đúng metadata/hash. Thu hồi/reject tài liệu
phải có quy tắc cho các revision đang tham chiếu nó; không âm thầm sửa lịch sử.

Nghiệm thu: sửa/reject/review cạnh tranh, nguồn trùng và thiếu tệp; manifest cũ
vẫn tái lập đúng. Không nâng mức review hoặc trộn dữ liệu AI vào nguồn chính thức.

### 6. Test database và trình duyệt tái lập được

Một số test Admin vẫn đọc `.env` và có thể commit vào `DATABASE_URL` khi thiếu
`HUS_TEST_DATABASE_URL`. Cần chuyển sang target validator hiện có, chỉ nhận test
URL tường minh, dùng transaction rollback hoặc DB tạm do fixture sở hữu. Test
không được tự dùng DB runtime vì đang chạy trên máy lập trình viên.

Các sửa nhỏ đã thực hiện trong lần tích hợp: VNU-only chỉ cấm upload ngoài Admin;
shell kiểm đủ sáu tab; metric unavailable chỉ kiểm vùng overview; bỏ đường dẫn
ảnh theo máy cá nhân và cho audit/provenance nhận `TEST_BASE_URL`.

Việc còn lại: một harness/fixture chuẩn tạo tài khoản, 101+ tài liệu, bản nháp và
bản published có manifest thật của fixture. Không skip nhánh pagination/XSS chỉ
vì dữ liệu chưa có. Bổ sung regression cho từng P0 trước khi sửa implementation.
Chạy CI trên checkout sạch và database mới, không dựa vào ảnh/log local cũ.

### 7. Rà soát phiên, trạng thái lỗi và telemetry

Kiểm thử response Admin đến muộn sau logout/đổi quyền, đổi bộ lọc liên tiếp,
401/403/500/timeout, giữ dữ liệu stale và retry, focus/dialog/mobile, VI/EN.
Rà soát lại toàn bộ trường dữ liệu render và URL bằng hostile-string fixtures.

Telemetry hiện lưu bộ đếm giới hạn trong RAM. Cần ghi rõ khoảng đo và reset khi
restart; nối việc ghi nhận vào endpoint `/me/recommendations` đang được UI dùng,
không suy chất lượng tư vấn từ số liệu của route legacy. Phân biệt không có dữ
liệu, mất nguồn và số 0 đo được. Các mục này cần kiểm thử bổ sung, chưa được coi
là lỗi đã tái hiện đầy đủ trong lần tích hợp này.

## Thứ tự triển khai đề xuất

1. Viết regression cho bốn P0; sửa validation và bất biến/rollback trước.
2. Nối publisher với catalog runtime bằng payload đầy đủ; bỏ synthetic fallback.
3. Hoàn thiện document versioning, test isolation và các ca phiên/giao diện.
4. Chạy lại offline/PDF, PostgreSQL, browser sinh viên/Admin và RAG; kiểm digest
   cấu hình/release; review diff và ancestry trên nhánh tính năng.
5. Khi được yêu cầu phát hành: backup DB thật, thử restore và upgrade từ HEAD 08
   lên 12 trên DB tạm trước; tạo PR, chờ CI đúng commit, Create a merge commit.
   Việc migration thật/restart cần bàn giao rõ vì restart làm mất VNU cookies RAM.

Các mục P0/P1 trên đã được triển khai và kiểm chứng local theo cập nhật đầu tài
liệu. Việc review nguồn học vụ, CI remote và quy trình PR/phát hành vẫn là các
bước riêng; không suy chứng nhận dữ liệu học vụ từ số test đạt.
