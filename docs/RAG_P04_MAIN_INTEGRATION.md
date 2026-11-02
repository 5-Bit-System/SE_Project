# P0-4 — RAG trong API, chatbot và UI active của main

**Lịch sử trước khi sửa phạm vi:** người dùng đã chốt RAG chỉ F1/F2/F3 và trò chuyện
cơ bản, không nối ranking/explanation. Demo mới dùng handler/app riêng; xem
[hướng dẫn hiện hành](HUS_RAG_MANUAL_DEMO.md). Router `/me/advisor/chat` trong biên bản
này cần thay bằng endpoint HUS tách biệt trước phát hành; giữ auth/binding/revision
và chạy lại nghiệm thu. Worktree/bundle/receipt cũ giữ nguyên để đối chiếu.

Ngày 02/11/2026. **Đạt nghiệm thu local trên main đã ghim**, chưa merge/push.
Working tree gốc vẫn ở `crawldata` với các thay đổi P0-1/P0-2/P0-3 được giữ nguyên.

| Thành phần | Vị trí |
| --- | --- |
| Main làm nền | `5239b7333a8f8cdf0f919e6b0505af0def99fe23`, đã fetch từ origin/main |
| Branch tích hợp | `integration/hus-rag-p04-20261102` |
| Worktree chạy/test | `backups/hus_integration/p04-main/` |
| Bản tái tạo đã kiểm | `backups/hus_integration/p04-replay-check03/` |
| Gói bàn giao trong crawldata | [manifest và patch](../integration/hus-rag-p04/README.md) |
| Receipt HTTP/browser | [hus_p04_authenticated_report.json](acceptance/hus_p04_authenticated_report.json) |

Code tích hợp nằm trong worktree main riêng. Chạy ứng dụng tại root crawldata vẫn
là phiên bản legacy của nhánh đó. Patch và công cụ tái tạo giúp review/apply đúng nền
main; toàn bộ dữ liệu RAG dùng lại từ crawldata theo checksum.

## API và ranh giới tài khoản

`POST /me/advisor/chat` giữ nguyên chuỗi `operation()` → xác thực/session → body
validation → `resolve_context()` → `ready(expected_revision)` trước khi gọi RAG.
Sau xử lý, `ensure_current()` đọc lại owner/session/source/binding/revision trước khi
trả kết quả. Bộ xử lý HUS không nhận ngành hay phiên bản tùy ý từ client: lấy scope
RAG theo catalog đã qua binding của tài khoản.

| Thay đổi | Kết quả |
| --- | --- |
| `app/services/hus_advisor.py` | Adapter HUS sau gate ngữ cảnh; F1 giữ edition nguồn, F2/F3 ghim phiên bản thuộc program; lỗi package trả 503 an toàn |
| `AcademicOperation` / `AdvisorRequest` | Thêm `allow_generated_reference` strict boolean, mặc định false từng request |
| `AdvisorResponse` | Thêm `mode=hus_rag`, `hus_answer`; response giữ `context_revision` hiện có |
| Legacy `/advisor/chat` | Câu hỏi HUS trả 409 `use_academic_context`; luồng khuyến nghị/guardrail hiện tại được giữ |
| `/hus/chat` | Không mở endpoint trả lời công khai trên main |
| `/hus/sources/{sha256}` | GET/HEAD qua verified account; middleware kiểm host/Origin boundary và `no-store`; binary/hash/page/range như P0-2 |

CSRF vẫn bắt buộc với POST; Origin/host không đúng bị từ chối trước xử lý. Body
không nhận owner, major, facts hoàn thành hoặc system history do client tự khai.
Thay tài khoản, token, nguồn hoặc binding trong khi RAG chạy không được trả kết quả
của ngữ cảnh cũ. HUS không gọi model provider để điền dữ kiện.

**Gate `ready` của main được giữ nguyên.** Tài khoản chưa xác nhận chương trình,
nguồn thiếu hoặc catalog/policy chưa đủ review vẫn bị chặn theo main. P0-4 không mở
khóa các catalog draft và không nâng sign-off F2 hay nội dung AI. Các catalog/policy
được đánh dấu ready trong nghiệm thu đều là fixture riêng, không phải dữ liệu sản phẩm.

## UI active được mở rộng theo module

Thêm `app/static/hus-chat.js` và `hus-chat.css`, hai include trong `index.html` cùng
thông báo ngữ cảnh nhỏ trong `course-status.js`. Các module auth/workspace/portal,
course board, kế hoạch và layout hiện có tiếp tục hoạt động; không dùng khung chat
legacy từ `app.js` để thay UI main.

Module dùng `window.systemAuth.request` cho cookie/CSRF, lấy binding server từ
`GET /me/academic-program`, sau đó đọc `GET /me/academic-context` để gửi program,
selection và revision hiện tại tới `/me/advisor/chat`. Không suy ngành từ tên hồ sơ.
Chat chỉ lưu trong bộ nhớ; history gửi đi có giới hạn, không lưu vào storage.

- Đổi account/session, snapshot/profile, binding, track/path hoặc revision: xóa chat,
  history và opt-in; phản hồi cũ bị bỏ qua dù request trước đó hoàn tất thành công.
- Refresh cùng identity/source/revision giữ hội thoại; GET cũ thất bại không được
  xóa kết quả refresh mới.
- Handshake event lấy selection đã có trước lúc module chat được tải; xác nhận
  binding phát event riêng để reset đúng ngữ cảnh.
- Dẫn chứng dùng contract P0-2: AI hiện “kiến thức AI” khi URL null; PDF đúng hash/trang
  qua resolver; web URL gốc; DOCX và nguồn thiếu hiển thị trung thực. Hai trang cùng
  PDF được giữ riêng.

## Nghiệm thu

| Bộ kiểm | Kết quả |
| --- | --- |
| Toàn bộ main offline sau tích hợp | **652 passed, 10 skipped, 80 deselected**; 80 ca DB loại theo marker, 10 ca cần source acceptance riêng |
| Backend/security mới | **41 passed**, nằm trong 652 ở trên |
| Node cho UI mới | **9 passed** |
| Uvicorn HTTP thật | **43 ca đạt**: bốn scope F1/F2/F3, opt-in, auth/CSRF/Origin, revision/binding, legacy bypass và source binary |
| Chromium với UI/auth/API thật | **14 ca đạt**, gồm AI null-link, refresh giữ chat, response cũ sau đổi account, đổi nguồn/binding và hết phiên |
| PDF | 4 binary canonical kiểm GET/HEAD/range/checksum; browser mở MAT3325 ở trang **13 và 12**, chờ plugin xác nhận cuộn thực trước chụp |
| Bản tái tạo từ gói patch | Hash 34 source outputs và 77 input khớp; chạy lại **41 backend + 9 Node đạt** trên worktree tái tạo |

Ruff, syntax JavaScript và `git diff --check` đạt. Còn warning deprecation TestClient
của Starlette. Hồi quy main dùng marker `not postgres and not hus_postgres`.

Receipt ghim base main, branch, toàn bộ app code, sáu file test/fixture, 63 input
data/registry/binary và bốn ảnh chụp tại:
`backups/hus_integration/p04-main/backups/p04-live-run02/`.
Ảnh `chat-active-ai.png` ghi UI main với thẻ AI; hai ảnh PDF ghi đúng MAT3325 trang12/13.
JUnit toàn main tại `backups/hus_integration/p04-main/backups/p04-main-regression.xml`.

Harness dùng repository tài khoản in-memory, profile/catalog/policy giả lập; giữ
nguyên middleware, phụ thuộc auth và code ngữ cảnh thật. Không dùng DB sản phẩm,
đăng nhập VNU hay model provider. Kết quả này không chứng nhận giao dịch PostgreSQL,
nguồn học vụ hiện hành, website ngoài hoặc CI/remote deployment.

## Chạy lại hoặc mở bản tích hợp

Từ root crawldata, tạo worktree mới bằng gói đã ghim:

```powershell
python -X utf8 -m tools.prepare_hus_main_integration --target backups/hus_integration/p04-new
```

Nếu clone chưa có object main đã ghim, fetch commit đó trước. Công cụ từ chối thư
mục đích đã tồn tại, kiểm checksum mọi input/patch rồi tạo worktree detached từ đúng
main, copy nguồn dùng chung và apply patch. Không reset checkout hoặc tạo commit.

Trong worktree tích hợp, dùng interpreter đã có dependency theo `requirements-dev.txt`
và `requirements-lock.txt`. Lần nghiệm thu này dùng venv tách biệt
`backups/hus_integration/p04-venv/`, không sửa Python toàn hệ thống.

```powershell
Set-Location backups/hus_integration/p04-main
& ../p04-venv/Scripts/python.exe -X utf8 -m pytest -p no:cacheprovider -m "not postgres and not hus_postgres" -q
node --test tests/frontend/hus-chat.test.cjs
& ../p04-venv/Scripts/python.exe -X utf8 -m tools.verify_hus_authenticated_e2e --out backups/p04-new-run --with-browser
```

Lệnh browser tự mở Uvicorn loopback với fixture, chụp bằng full Chromium và kết thúc
server. Chọn output chưa tồn tại; không trỏ harness vào instance/DB tài khoản thật.

P0-5 tiếp theo: cập nhật nền tích hợp nếu main đổi, giữ ancestry của các nhánh nguồn,
chốt commit reviewable, mở PR theo quy định repository, chạy CI và nghiệm thu trên
commit tích hợp cụ thể. Chưa có commit/push/merge hoặc kích hoạt production trong P0-4.
