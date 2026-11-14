# VT-102 — Risk-based strategy và Equivalence Partitioning

## Scope, review và layers

Người dùng đã yêu cầu tiếp tục code/báo cáo/publication và đã xác nhận log RED
qua câu trả lời: **“Đã review RED, tiếp tục GREEN và hoàn tất bài”**. RED gốc
chạy trên baseline `7aa9d939ddca47461dbc7a55972fdfbec7c434fe`: 25 instances,
12 assertion FAIL, 13 PASS, 0 setup errors; log và hash test được giữ nguyên.

Ưu tiên Integration/API vì rủi ro nằm ở ranh giới request → job → collector →
save → response. Unit helper thuần được thực thi qua API với coverage branch;
không tạo test chỉ assert lại tên hằng số. Một E2E bằng Chrome kiểm tra lost ACK,
key, progress, feedback đúng một lần, EN/mobile/logout. Không cần screenshot
pixel-perfect, cross-browser matrix hay gọi VNU thật để chứng minh dedup trong
slice này. DB thật, crash recovery, nhiều process là phần chưa được chứng minh.

## Phân vùng tương đương

| Input/state | Phân vùng | Đại diện đã chọn và lý do |
| --- | --- | --- |
| Header key | Thiếu; hợp lệ 16–128; rỗng; ngắn; dài; ký tự sai; nhiều header | None; 16/128 chữ a; chuỗi rỗng; short; 129 ký tự; khoảng trắng; header lặp. Kết hợp EP và kiểm tra biên. |
| Intent | Same key active; same key terminal; new key owner busy; same key khác phiên | Retry phải replay; thao tác mới bị busy; phiên khác không nhìn thấy receipt cũ. |
| Body | Rỗng/{} hợp lệ; list/null/owner/password sai | Canonical body không thể dùng để đưa danh tính hoặc credential vào sync. |
| Progress | Queued0; collecting25; saving75; done100; failed/cancelled giữ mốc | Đây là các mốc thực tế, không tạo fake percent trong 1–99 để giả đo số dòng. |
| Auth | App hợp lệ/hết hạn; thiếu CSRF; provider hết hạn | 202, 401, 403 hoặc reauth_required không tạo job. |
| Delivery | ACK nhận; ACK mất; concurrent replay | Kiểm tra identity/counts, không chỉ snapshot digest hoặc status 200. |

## Bảng cases

P0: correctness/privacy/idempotency; P1: compatibility/UX/concurrency.

| ID | Risk/Requirement | Level | Precondition/Input | Expected Result | Priority |
| --- | --- | --- | --- | --- | --- |
| TC01 | AC01/03 async progress | API | Collector bị giữ bằng Event | POST202 trước completion; GET collecting25; save0 | P0 |
| TC02 | AC02 retry active | API | Same key, job running | Same id, 1 collector/save | P0 |
| TC03 | AC02 lost ACK after commit | API/failure | Lần đầu đã save, client bỏ response | Replay id cũ; counts không tăng | P0 |
| TC04 | AC04 key invalid | API/negative | Empty/short/129/spaces | 400, không side effect | P0 |
| TC05 | Key valid partitions | API | Length16/128 | 202; một logical job | P1 |
| TC06 | AC04 body invalid | API/negative | [], null, owner, password | 400, zero jobs | P0 |
| TC07 | Legacy | API | Không header | Contract cũ vẫn hoạt động | P1 |
| TC08 | AC03 mapping mutation | API | Save hoàn tất | state done, phase finished, progress_percent=100 literal | P0 |
| TC09 | Failed retry | API/failure | Provider lỗi trước save | Replay failed id; collector1/save0; progress25 | P0 |
| TC10 | Concurrent retry | API | 40 threads, same key | 40 replay202; id/counts1 | P0 |
| TC11 | Private job | API/negative | Owner giống, session khác | GET404 | P0 |
| TC12 | Expired app | API/negative | expires_in=0 | 401, zero jobs | P0 |
| TC13 | Different intent | API | Key mới khi owner busy | 409, không thêm job | P1 |
| TC14 | Save boundary | API | Save chặn bằng Event | saving75 trước commit | P0 |
| TC15 | Cancel | API/failure | Hủy khi collector chờ | cancelled25; save0, không 100 | P0 |
| TC16 | Replay validation | API/negative | Key cũ + body owner khác | 400 trước replay | P0 |
| TC17 | Reauth compatibility | API | Provider state hết hạn | 200 reauth_required; zero jobs | P1 |
| TC18 | CSRF | API/negative | Không token | 403, zero jobs | P0 |
| TC19 | NFC40 and queue | API/integration | 40 owner, retry, provider giữ | 40 jobs/save; max2 collector; 160 HTTP calls | P0 |
| TC20 | AC05 end to end | Chrome | Response đầu mất | Same key, 25/100, feedback1, logout cleanup | P1 |
| TC21 | Replay before resume | API | Done rồi provider hết hạn | Same key202; key mới reauth; không recrawl | P0 |
| TC22 | Ambiguous key | API/negative | Hai Idempotency-Key headers | 400, zero jobs | P1 |
| TC23 | Queue revocation race | API/failure | Job đã chờ slot, cookie bị revoke | Không spawn VNU; failed0 | P0 |

TC01–18 được viết trước product patch; TC19 bổ sung RED queue trước patch.
TC21/22 là regression bổ sung; TC23 đã tái hiện FAIL rồi sửa recheck tại thời
điểm lấy slot. Browser attempt đầu bị chặn bởi refresh-bar luôn hidden ở baseline;
log đó là lỗi precondition, **không được tính RED hợp lệ**. Bằng chứng RED hợp lệ
để mở GREEN là 12 assertion fail API đã được người dùng review.

## Flakiness và giới hạn

1. Race giữa collector/save và poll: dùng Event ở đúng boundary, gather task
   thay cho sleep tùy ý. Timeout3/5 giây chỉ chống test treo, không định nghĩa
   thời gian sản phẩm. TC23 dùng semaphore báo đã acquire-wait để không vô tình
   kiểm tra revoke trước khi job thật sự vào queue.
2. State RAM chung và asyncio loop: mỗi test monkeypatch sessions/jobs/tasks/slots,
   giải phóng gate và drain trong finally; không dùng event/semaphore đã bind
   vào loop cũ. Harness 40 actor có cookie/CSRF độc lập, không xoay chung cookie.
3. Thread scheduling và browser poll: Barrier40 tạo contention có chủ đích nhưng
   timeout không phải SLO. Browser dùng expect theo điều kiện DOM; số đo p95 nằm
   trong harness riêng, không suy từ pytest duration hoặc số lần rerun.
