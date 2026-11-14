# SE2026 — Bài tập cá nhân 3 — VT-102 — Bước 1

**Sinh viên:** Vũ Khắc Huy Vinh — **MSSV:** 23001956

**Nhóm/vai trò:** SE2026-T25 / Thành viên

**Dự án:** AI-07 — Explainable Course Recommender

**Repository:** https://github.com/5-Bit-System/SE_Project

**Ngày khảo sát:** 14/11/2026, Asia/Saigon
**Trạng thái:** SPEC/PLAN CHỜ REVIEW. Chưa viết test VT-102, chưa sửa code sản phẩm.

## 1. Baseline và phạm vi đã khảo sát

- **Baseline Commit Hash:** `7aa9d939ddca47461dbc7a55972fdfbec7c434fe`.
- Nhánh hiện tại: `feat/recommendation-conversation-ui`; commit ngày 04/11/2026.
- Trước khảo sát không có tracked changes; `.vscode/settings.json` là file local
  chưa theo dõi, được giữ nguyên. Không fetch/pull trong Bước 1: đây là baseline
  của checkout thực tế, không khẳng định là phiên bản mới nhất của `main`.
- **Nhánh đề xuất:** `feat/vt102-async-task-progress`, tạo từ đúng baseline trên
  sau khi duyệt Bước 1. Chưa tạo nhánh, commit hoặc push. Không merge vào main.

Lệnh đề xuất cho lần chuyển nhánh sau review:

```powershell
git switch -c feat/vt102-async-task-progress 7aa9d939ddca47461dbc7a55972fdfbec7c434fe
```

| Thành phần thực tế | Trách nhiệm và ý nghĩa đối với VT-102 |
| --- | --- |
| `app/main.py`, `app/api/` | FastAPI; cookie authentication, origin/CSRF và API học vụ/VNU. |
| `app/api/portal.py` | Đã có `POST /me/portal-sync` trả 202, `GET /me/portal-sync/{job_id}`, cancel và password-only reauth. |
| `app/integrations/daotao/runtime.py` | Session/job/task trong RAM; `asyncio.Semaphore(2)` giới hạn collector; timeout subprocess 120 giây. |
| `app/integrations/daotao/store.py` | Transaction, khóa owner/generation và lưu snapshot; không phải durable job registry. |
| `app/auth/portal.py` | Ràng buộc account/session/VNU owner, kiểm tra quyền và transaction khi ghi nguồn. |
| `app/static/portal.js` | Frontend thuần JS; đã poll job mỗi 1 giây và hiển thị lỗi/hoàn tất, chưa có thanh tiến trình định lượng. |
| `app/services/`, `app/api/academic.py` | Nghiệp vụ gợi ý; `/me/recommendations` hiện đợi `asyncio.to_thread(recommend, ...)` xong rồi trả kết quả. Không chọn thay đổi luồng này trong slice đầu. |
| `tests/integrations/`, `tests/frontend/`, `tests/database/` | Có test vòng đời job, phiên, hủy lúc commit, snapshot/DB và browser. Test offline dùng dữ liệu giả, chặn outbound HTTP. |
| `pyproject.toml`, `requirements*.txt` | pytest/Ruff; DB/PDF acceptance là nhóm riêng. Có httpx và Playwright; chưa cài coverage, pytest-cov hoặc pytest-asyncio trong venv khảo sát. |

**Bằng chứng code quan trọng tại baseline:**

1. `portal.start_job()` gọi `asyncio.create_task(sync_job(...))`; POST đã là
   bất đồng bộ. Nếu owner đang có job running/saving, request mới nhận `409 busy`,
   không được trả lại receipt/id của lần đầu. Sau khi job terminal, request mới
   có thể tạo job khác. Chưa đọc `Idempotency-Key` trong đường này.
2. `portal.job_status()` hiện chỉ allowlist `state`, `error`, `result`; POST trả
   `{id, state}`. Chưa có `progress_percent` hoặc một serializer response chung.
3. `store.save()` kiểm tra `(owner, digest)`; migration
   `database/hus_alembic/versions/20261023_03_portal.py` có UNIQUE tương ứng.
   Vì vậy không được kết luận baseline “chưa chống trùng dữ liệu”. Bảo vệ này
   không chống lần gọi collector/save lặp hoặc job/feedback mới khi retry.
4. `runtime.reap()` giữ terminal job theo `created < now - 1800`; shutdown xóa
   registry RAM. `owned_job()` đòi **đúng đối tượng session**, kể cả cùng owner.
5. Collector hiện fail-fast `busy` khi hai slot đã dùng. Nhận HTTP nhanh với
   hàng loạt job failed/busy không phải bằng chứng đáp ứng 40 tác vụ thành công.

## 2. Problem Statement và vertical slice đề xuất

Người dùng cập nhật bảng điểm VNU có thể chờ lâu hoặc mất phản hồi nhận job.
Nếu gửi lại, client hiện không có receipt ổn định để phân biệt yêu cầu đã được
nhận với yêu cầu mới. Busy theo owner và UNIQUE snapshot chỉ bảo vệ từng phần;
chúng không giải quyết đầy đủ retry ở API và phản hồi hoàn tất trên giao diện.
Người dùng cũng chưa thấy rõ tác vụ đang chờ, đang đọc hay đang ghi dữ liệu.

**Slice đề xuất:** bổ sung retry có idempotency và tiến trình theo giai đoạn cho
luồng **Cập nhật bảng điểm bằng phiên VNU đang còn hiệu lực**. Tận dụng POST/GET
và UI đã có; không tạo endpoint giả để minh họa assignment. Job đi qua
accept → chờ slot → collector → save → poll/UI completion.

Đây là mở rộng có kiểm thử một luồng async sẵn có. Nhận xét “đã có async” phải
được giữ trong báo cáo, không trình bày toàn bộ khả năng đó là code mới của BT3.

**Phạm vi chống trùng đề xuất để review:** một process/event loop và cùng phiên
app còn hiệu lực. Không hứa exactly-once xuyên restart, nhiều worker hoặc mất
storage. Nếu bài cần phạm vi đó, phải đổi thiết kế sang ledger DB + uniqueness
và worker bền vững trước GREEN; không chỉ thêm một dictionary rồi tuyên bố đạt.

## 3. Acceptance Criteria — năm tiêu chí kiểm thử được

| ID | Given / When | Kết quả bắt buộc |
| --- | --- | --- |
| **AC-01 — Nhận tác vụ không đợi hoàn tất** | Phiên app/phiên VNU hợp lệ, collector được test giữ bằng event; gửi POST có key hợp lệ. | API trả `202` và `id` trong khi collector còn bị giữ. GET cùng id đọc được state/phase/progress; UI hiện đang chờ/đang thực hiện, không báo thành công sớm. Không dùng việc POST mất bao lâu một mình để suy ra async. |
| **AC-02 — Retry cùng ý định không nhân đôi** | Cùng owner, cùng app session, cùng operation và key; request hợp lệ được gửi lại khi đang chờ/chạy, sau terminal hoặc sau khi response đầu bị mất. | Mọi response nhận việc tham chiếu **cùng id**; một lần collector và tối đa một lần gọi save cho logical job. Khi collector thành công, save được gọi đúng một lần; khi lỗi trước save thì không gọi save. Same key terminal không tự chạy lại; muốn thử một nghiệp vụ mới phải dùng key mới. UI phát feedback hoàn tất tối đa một lần/job. |
| **AC-03 — Tiến trình và schema nhất quán** | Poll ở từng mốc; inject lỗi/hủy trước hoặc trong commit. | Giữ field `state` hiện có; bổ sung `id`, `phase`, `progress_percent`. Tiến trình đúng mapping ở bảng dưới, không giảm trong một job, không trả 100 cho failed/cancelled. Chỉ done sau kết quả save `saved` hoặc `unchanged`; hủy khi đang commit vẫn đợi kết quả thật, giữ bảo vệ shield hiện có. |
| **AC-04 — Request sai, owner khác và vòng đời an toàn** | Key có mặt nhưng sai định dạng; body khác rỗng/{}; session hết hạn; owner/session khác poll id; key mới khi cùng owner đã có job active. | Key/body sai → 400 trước tạo việc; hết phiên app → 401; job ngoài phiên → 404; key mới khi owner bận → 409. Các request bị từ chối không sinh job/collector/save. Giữ kiểm tra origin/CSRF. Phiên VNU hết hạn vẫn theo contract `200 {state: reauth_required}`, không tạo job. |
| **AC-05 — UI hoàn chỉnh và tương thích** | Người dùng bấm cập nhật, mất ACK hoặc lần poll tạm lỗi rồi retry; sau đó done/failed/cancelled/logout. | Client giữ cùng key cho retry truyền tải, nhận lại id và poll tiếp; hiện nhãn giai đoạn và thanh tiến trình có accessible label, dừng poll/feedback cũ sau logout. Key mới chỉ cho thao tác cập nhật mới rõ ràng. Request không có header vẫn theo luồng legacy; reauth bằng mật khẩu không tự gửi lại credential. |

AC-02 là invariant trong **phạm vi key hợp lệ**. Client legacy không gửi key
không được gán cam kết idempotency mới. Không gửi email hay tạo hệ thống
notification mới chỉ để chứng minh “không trùng thông báo”; trong slice này
notification là feedback UI hoàn tất, không bao gồm delivery qua email/broker.

## 4. Contract và invariant cần bảo vệ

### 4.1. Request và receipt

```http
POST /me/portal-sync
Idempotency-Key: 9ec184ae-cbbc-4a22-a6da-5da67eaee7e6
X-CSRF-Token: <token trong phiên; không lưu trong evidence>
Content-Type: application/json

{}
```

Đề xuất key 16–128 ký tự ASCII `[A-Za-z0-9_-]`, không khoảng trắng. Thiếu header
giữ legacy; có header nhưng rỗng/quá dài/sai ký tự trả 400. Body rỗng và `{}` là
**một payload chuẩn hóa**; mọi body khác vẫn bị từ chối, kể cả khi key đã tồn tại.
Không mở thêm tham số owner/subject/password từ browser cho endpoint sync.

Scope registry là `(app_session_id, owner, operation=portal-sync, key)`; xác thực
và validation trước lookup. Lookup/replay phải diễn ra trước resume cookie và
kiểm tra owner busy để một response đã mất vẫn lấy lại được job sau khi cookie
VNU được xoay vòng/hết hạn, miễn app session và ownership còn hợp lệ. Replay
không bỏ qua logout, xóa dữ liệu, generation fence hoặc kiểm tra session hiện tại.

Trong cùng event loop, lookup → giữ chỗ key → tạo job phải nguyên tử; không
`await` I/O giữa check-then-create. Nếu có lock, không giữ nó trong lúc chạy
collector/save. Concurrent requests không được cùng thắng để tạo hai job.

Key đã nhận giữ liên kết tới job tới khi app session hết hiệu lực, tối đa 30 phút
từ acceptance; không thu hồi job active chỉ vì bộ dọn terminal. Dọn key/job liên
quan đồng bộ và khi logout/delete. Ngoài phạm vi phiên/process không nhận lại
job cũ; restart là residual risk được công bố, không replay ngầm thành công.

### 4.2. Response và tiến trình theo mốc

Response job đề xuất dùng một serializer allowlist chung cho POST/GET:

```json
{
  "id": "opaque-job-id",
  "state": "running",
  "phase": "queued",
  "progress_percent": 0,
  "error": null,
  "result": null
}
```

| State | Phase | progress_percent | Ý nghĩa |
| --- | --- | ---: | --- |
| running | queued | 0 | Đã nhận, chờ slot. |
| running | collecting | 25 | Collector thực sự bắt đầu sau admission. |
| saving | saving | 75 | Đã đọc xong nguồn, đang ghi transaction. |
| done | finished | 100 | Save đã trả saved/unchanged. |
| failed | failed | Giữ mốc gần nhất: 0, 25 hoặc 75 | Không đánh tráo thất bại thành hoàn tất. |
| cancelled | cancelled | Giữ mốc gần nhất: 0, 25 hoặc 75 | Chưa hoàn tất; commit đã bắt đầu phải được phân xử bằng kết quả thật. |

Đây là **phần trăm theo giai đoạn**, không đo số dòng VNU đã tải hay dự báo thời
gian còn lại. `result` chỉ null/saved/unchanged, `error` chỉ mã an toàn hoặc null;
không expose task, session object, cookie, password hay traceback. Nhánh
`reauth_required` là response tương tác riêng, không phải job thiếu field.
ACK/replay trả 202, kể cả receipt của job terminal; body phản ánh state hiện tại,
không luôn gán cứng running. UI phải đọc state khi nhận replay terminal.

**Invariant cốt lõi:** trong scope và lifetime trên, cùng logical request tạo
tối đa một job, một collector và một side-effect save; response của job đó luôn
phản ánh state/progress thật. UNIQUE snapshot tiếp tục là bảo vệ DB độc lập,
không dùng nó thay cho assertion đếm collector/save/feedback.

Mutation ở Bước 4 dự kiến đổi riêng serializer `progress_percent` cho done từ
100 thành 0 (hoặc map nhầm field). Assertion phải kiểm tra field thật trên wire,
không chỉ status HTTP hoặc tính expected bằng chính mapper đang bị mutation.

## 5. Non-functional Constraints và cách đo dự kiến

1. **NFC-01 — Tải/latency:** harness có 40 actor riêng, mỗi actor một phiên giả
   hợp lệ, gửi một logical job và poll cùng lúc, có cohort retry cùng key.
   **p95 ≤ 1.5 giây** đo riêng endpoint POST acceptance và GET status bằng
   monotonic timer, nearest-rank percentile; ghi min/avg/p95/error rate và số mẫu.
   40 job khác owner phải được nhận thành công khi còn capacity; retry cùng key
   không làm tăng số logical jobs. Không coi trả lỗi nhanh là đạt hiệu năng.
2. **NFC-02 — Tài nguyên/backpressure:** đề xuất capacity tối thiểu 40 active
   logical sync jobs, tối đa 2 collector chạy đồng thời, phần còn lại chờ slot.
   Duplicate lookup không chiếm capacity mới; vượt giới hạn trả 429, không giữ
   việc hoặc credentials vô hạn. Giới hạn runtime hiện tại 1.000 bản ghi tổng
   vẫn cần được tôn trọng cùng chính sách cleanup 30 phút.
3. **NFC-03 — Bảo mật/tính đúng:** giữ auth/origin/CSRF/owner-session/generation;
   không log credential hoặc dùng tài khoản thật làm fixture. Mutation, load và
   regression chạy bằng fake provider/store, không tải thử vào VNU công cộng.

Mục tiêu 1.5 giây là tiếp nhận/đọc trạng thái, **không phải thời gian hoàn thành
crawl và ghi toàn bộ bảng điểm**. Đo ASGI in-process chứng minh hành vi và tránh
trùng, chưa chứng minh TCP/TLS, DB thật, nhiều process hoặc độ trễ VNU. Bước 4
phải ghi rõ loại môi trường đo. Collector giả dùng event/barrier để giữ tác vụ
đang active; không dùng sleep tùy ý làm bằng chứng chạy bất đồng bộ.

## 6. Giả định để người dùng review/phản biện

Hai giả định ban đầu dễ được AI đề xuất nhưng **đã bị code thực tế bác bỏ**:

| ID | Giả định | Evidence thực tế và điều chỉnh |
| --- | --- | --- |
| A-01 | “Cập nhật bảng điểm đang xử lý hoàn toàn đồng bộ, phải xây async từ đầu.” | Sai: POST202, create_task và poll đã có. Chỉ thêm receipt retry, queue admission/progress và UI; không nhận công trạng code cũ. |
| A-02 | “DB chưa có chống trùng, chỉ cần thêm UNIQUE snapshot.” | Sai: UNIQUE(owner,digest), row lock/generation và nhánh unchanged đã tồn tại. Test phải chứng minh số job/collector/save/feedback, không chỉ đếm snapshot. |

Các giả định thiết kế **chưa được người dùng duyệt**, không coi là fact:

| ID | Đề xuất cần review | Căn cứ/rủi ro nếu không đúng |
| --- | --- | --- |
| A-03 | Slice là sync bằng cookie; không tự retry password-only reauth. | Repo xóa credential trong finally và có test cấm tự gửi lại. Nếu cần nhận việc async ngay cả bước nhập password, phải mở rộng contract/test trước GREEN. |
| A-04 | Scope idempotency một process/cùng phiên, lifetime tối đa 30 phút. | Runtime hiện chỉ có RAM và job private theo session. Nếu đòi survive restart/cross-worker, cần durable ledger; kế hoạch nhỏ hiện tại chưa đáp ứng. |
| A-05 | 0/25/75/100 biểu diễn milestone là đủ trực quan. | Worker chưa phát từng bước/row qua IPC. Nếu cần % thực, phải thiết kế stream event có nguồn và protocol worker riêng. |
| A-06 | 40 concurrent đo với fake VNU/store; 2 collector và queue chờ được chấp nhận. | Baseline fail-fast busy ở slot thứ ba. Phải thêm admission chờ có kiểm soát; kết quả synthetic không được tuyên bố là 40 browser VNU thật đồng thời. |
| A-07 | Thêm field không làm hỏng caller cũ; header có thể optional để tương thích. | UI cũ đọc một số field nhưng một số test so sánh JSON tuyệt đối. Cần regression trước GREEN; không giả định additive schema luôn vô hại. |

## 7. Implementation Plan — chỉ thực hiện sau các mốc review

1. **Review Bước 1:** chốt AC, scope một process/session, milestone progress,
   semantics key mới/cũ và tải 40 actor. Tạo nhánh đề xuất; giữ baseline nguyên vẹn.
2. **Bước 2, chỉ thiết kế test:** lập risk strategy và bảng ≥10 cases;
   Equivalence Partitioning cho header thiếu/hợp lệ/sai, same/new key,
   session/owner, queued/collecting/saving/done/failed/cancelled. Chỉ rõ ≥2
   negative tests và failure path mất ACK sau save. Dừng cho người dùng review.
3. **Bước 3 RED:** viết test trước; dùng event/barrier và fake account/provider/
   store, đếm invocation thực. Chạy contract test yêu cầu field progress + retry
   trả cùng id. Nếu baseline cho 409 busy hoặc thiếu field thì assertion RED
   đúng lý do; import/syntax/setup/network error không được tính. Lưu lệnh,
   exit code, stdout/stderr, JUnit và diff tests-only. **Dừng để người dùng xác
   nhận log FAIL trước bất kỳ dòng patch sản phẩm nào.**
4. **Bước 3 GREEN, sau xác nhận RED:** thêm registry receipt/serializer nhỏ, tích
   hợp vào admission hiện có, thêm wait-for-slot cho async sync mà giữ fail-fast
   mặc định của login. Cập nhật lifecycle và UI; kiểm tra reauth/cancel/shutdown
   giữ behavior cũ. Xuất full diff cho review trước commit, chạy regression phù
   hợp rồi toàn suite theo dependency/test marker. Không đổi source academic data.
5. **Bước 4:** mutation mapping response trên nhánh/worktree tạm, chạy test phải
   giết mutation rồi khôi phục. Đo line/branch coverage nếu cài công cụ được;
   harness 40 concurrent gồm duplicate retries; báo số đo thật và residual risk.
   Không tiêm mutation vào nhánh nộp bài hoặc bỏ qua fail để báo PASS.
6. **Bước 5:** traceability AC/risk → test → file → commit thật → log; 2 điểm AI
   cần review; Reflection 280–320 từ; `README_VT102.md` hướng dẫn chạy lại. Chỉ
   ghi hash/result khi đã thực hiện, không dùng placeholder như kết quả đã có.

### File dự kiến trong GREEN và các bước sau

| File | Dự kiến thay đổi/tạo | Mục đích |
| --- | --- | --- |
| `app/services/portal_sync_jobs.py` | Mới, module nhỏ | Registry keyed requests, canonical payload, atomic admission, capacity/cleanup và response mapping. Không tách lại toàn bộ Large Controller ngoài scope. |
| `app/api/portal.py` | Sửa | Đọc/validate header, replay đúng phiên trước busy/resume, dùng serializer cho receipt/poll; cập nhật mốc trong sync_job. |
| `app/integrations/daotao/runtime.py` | Sửa | Cơ chế chờ collector slot có opt-in, mốc collecting sau khi thực sự nhận slot, lifecycle cleanup key/job. Không đổi login thành hàng đợi vô hạn. |
| `app/static/portal.js` | Sửa | Key theo logical intent, retry mất ACK/poll, xử lý terminal replay và feedback một lần/job; giữ epoch guard. |
| `app/static/index.html`, `app/static/portal.css` | Sửa nhỏ | Progress element có label và phase text, phù hợp VI/EN và lỗi/hủy. Không redesign frontend. |
| `tests/unit/test_portal_sync_jobs.py` | Mới ở RED | EP của key, state/mapping, TTL/capacity, concurrent admission. Dùng asyncio.run, không bắt buộc pytest-asyncio. |
| `tests/integrations/test_vt102_async_progress.py` | Mới ở RED | Contract HTTP, retry/lost ACK, owner/CSRF, counts, progress, cancellation và 40 admission. |
| `tests/integrations/test_portal_api.py`, `test_portal_jobs.py`, `test_portal_sessions.py` | Chỉ sửa test cần thiết trước patch | Giữ regression schema/lifecycle, mock tương thích hook slot mới. Không nới assertion để che bug. |
| `tests/frontend/check_vt102_async_progress.py` | Mới ở RED | Browser slice từ click → trạng thái → completion, retry/lost response và cleanup. |
| `tools/vt102_load.py` | Mới ở Bước 4 | Httpx/asyncio với 40 actor, barrier, duplicate cohort, counts và JSON metrics. Không gọi VNU thật. |
| `requirements-dev.txt` và lock nếu thực sự cần | Có điều kiện | coverage/pytest-cov chưa có; chỉ thêm sau review, không hứa đã đo coverage. |
| `docs/vt102/`, `README_VT102.md` | Tài liệu/evidence | Spec, strategy, RED/GREEN/mutation/performance logs, matrix và Reflection. |

Không dự kiến migration DB cho scope một process. Durable idempotency là quyết
định mở rộng kiến trúc nếu A-04 bị bác bỏ; lúc đó cần sửa spec/test plan trước,
không lén thêm schema ở GREEN.

## 8. Evidence đã thực thi trong Bước 1 và giới hạn

- [Khảo sát Git/source/package](evidence/step1-repo-survey.txt): lệnh thực tế,
  baseline, cây file tracked, excerpt có số dòng và package availability.
- [Output baseline tests](evidence/step1-baseline-tests.txt) và
  [JUnit](evidence/step1-baseline-junit.xml): **56 passed, 1 warning, exit 0**;
  chạy đúng ba file test hiện có về portal API/job/session, không phải test mới VT-102.
- Warning Starlette/httpx có sẵn. Chưa chạy full suite, load, mutation hoặc
  coverage ở Bước 1. Chưa có bằng chứng đáp ứng p95 1.5 giây hoặc retry contract mới.
- Lần chạy baseline đầu thiếu thư mục cha của `--basetemp`, gây setup error
  WinError3. Đã tạo thư mục cha và chạy lại 56 pass; output/JUnit attempt đầu
  được giữ riêng trong `backups/vt102_step1/attempt1-*`. **Đó không phải RED của
  VT-102**, không đưa vào evidence chứng minh test phát hiện thiếu tính năng.

Lệnh đã chạy để kiểm tra baseline (PowerShell, từ repo root):

```powershell
$env:PYTHONUTF8 = '1'
New-Item -ItemType Directory -Force backups/vt102_step1 | Out-Null
.venv/Scripts/python.exe -m pytest tests/integrations/test_portal_api.py tests/integrations/test_portal_jobs.py tests/integrations/test_portal_sessions.py -q -p no:cacheprovider --basetemp backups/vt102_step1/pytest-run2 --junitxml docs/vt102/evidence/step1-baseline-junit.xml
```

Khi chạy lại, chọn thư mục `--basetemp` mới; giữ nguyên artifacts trước đó.
Không ghi đè evidence được dùng trong báo cáo. Mọi kết quả RED/GREEN/mutation/
performance và commit của feature sẽ được bổ sung sau khi thực sự chạy.

**Mốc dừng hiện tại:** người dùng review Bước 1. Chưa bắt đầu Bước 2 hoặc RED;
chưa thay đổi `app/`, test files, dependency, runtime DB, nhánh hay commit.
