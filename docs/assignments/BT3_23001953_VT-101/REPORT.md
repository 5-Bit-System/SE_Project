# Engineering report — trạng thái thực thi 31/10/2026 (Asia/Saigon)

Log UTC ghi ngày30/10; chênh ngày với giờ Việt Nam là đúng timezone.
Các số dưới lấy từ file evidence thật; không có PDF hoặc human sign-off.

## Spec → RED → patch → GREEN

| Mốc | Trạng thái | Kết quả/evidence |
|---|---|---|
| Repo/isolation | executed/passed | main local=GitHub7b387a3; root18dirty/untracked entry, staged0; worktree riêng |
| Spec/revised plan/strategy | executed | SPEC, PLAN, TEST_STRATEGY trước production patch |
| Related baseline | executed/passed |32passed; baseline.log/json, HEAD7b387a3 |
| Test-first | executed/failed như kỳ vọng |37failed5passed; red.log/json; endpoint404 thay vì200/422/503/500; không collection/import error |
| Checkpoint | executed | a5aab95 cố ý chứa test đỏ; parent7b387a3 |
| Patch/diff review | executed | PATCH_REVIEW; cb3b35d; legacy AST/function không sửa |
| Initial GREEN | executed/passed |78passed; green.log/json |
| Whole selected offline | executed/passed |619passed79deselected,0skipped; offline-green.log; gồm10PDF acceptance với explicit root |
| Mutation | executed/killed | pytest exit1:3failed39passed; mutation.patch/log/json |
| Back on correct branch | executed/passed |46passed; after-mutation.log |
| Coverage | executed | coverage-tests46passed; coverage.json, coverage-report.log |
| Hash-seed repeats | executed/passed |6process×46=276test executions; flaky-runs.log/json |
| Browser/API E2E slice | executed/passed |Chrome fetch actual HTTP; legacy array + search/filter/page + empty +422; browser.log/results.json |
| Default load SLO | executed/failed |6000correct,0error, one p95>3s; performance-results.json/requests.csv |
|8thread trial SLO | executed/failed |6000correct,0error, one p95>3s; performance-tuned-results.json/requests.csv |
| Local PG-specific suite | not applicable cho slice đã chọn |Không sửa SQL/schema/repository PG; chưa chạy local PG acceptance/performance |
| VNU login/real student/production load | not applicable |Public catalog API, không đăng nhập hoặc đọc điểm thật |
| Publication/remote CI | xem PUBLICATION |Chỉ ghi passed sau push/check thực sự, không suy từ test local |

Một cảnh báo Starlette/httpx deprecation có sẵn. Không đổi dependency runtime
để xử lý warning ngoài phạm vi. Builders4fixtures+mẫu65 và Node analytics đều
passed. Final regression/review có log `final-*` sau khi harness/docs hoàn thiện.

Root preservation:18file có sẵn giữ nguyên SHA-256, staging vẫn rỗng. Trong
lúc task chạy, root có thêm4dirty paths: analytics.css, analytics.js, index.html,
tests/frontend/check_charts.py; rồi root chuyển từ main7b387a3 sang
`feat/dashboard-remove-summary-20261030` tại6ffc293f401e2cdbb55c4ba3183416cbc8f3462c,
check_charts.py trở thành clean. Đó là hoạt động đồng thời ngoài worktree BT3;
task này không checkout/commit root hoặc sửa/copy các file đó. Exact equality
và root_refs_and_staging_preserved=false, strict audit exit1 do refs thay đổi,
nhưng preexisting_files_preserved=true. Không “sửa” refs để ép audit xanh. Baseline
BT3 vẫn đúng main chính thức **tại thời điểm GĐ0**, các commit RED/GREEN không đổi.

Final lint lần đầu phát hiện unused import và import order trong tools mới;
đã sửa và chạy lại, giữ log lỗi `final-lint-initial.*`. Raw pytest output có
trailing whitespace; không sửa byte log để làm đẹp diff. `.gitattributes` chỉ
tắt whitespace check cho chính BT3 raw .log/.patch evidence, code vẫn kiểm bình
thường. Root integrity lần đầu ghi exact mismatch nằm ở root-integrity-initial.json.

## Mutation đúng biến thể

Từ cb3b35d, worktree detached `backups/bt3_mutant_23001953` chỉ sửa
`app/api/routes.py::course_search`: sau handlers domain, thêm `except Exception`
trả CourseSearchPage(items=[],total=0). Python compile hợp lệ, API thật chạy được.

`test_failure_contract_never_returns_default_success` phát hiện hai trường hợp:
StorageUnavailable phải503 nhưng nhận200; StorageDataError phải500 nhưng nhận200.
`test_unexpected_exception_is_500_not_empty_success` phát hiện500 bị đổi200.
Các empty-query tests vẫn200 thành công: vì vậy test phân biệt **không khớp dữ
liệu** với **không đọc được dữ liệu**, không chỉ cấm list rỗng. Mutant killed,
không sống sót, không phải syntax/import failure. Không commit/cherry-pick mutant;
chỉ patch tĩnh làm evidence. Kết luận giới hạn một lỗi đã thử, không test perfection.

## Coverage và residual risk

Coverage.py7.17.0, branch=True; chỉ đo2file test BT3 trên3module production:

| Phạm vi | Line | Branch | Ý nghĩa |
|---|---|---|---|
| course_search_service.py |12/12=100% |4/4=100% |code/name/credits paths được chạy |
| schemas/catalog.py |14/14=100% |0 branch, not applicable |model declarations và serialization được dùng |
| routes.py toàn file |57/137≈41,61% |2/4=50% |phần lớn API ngoài scope chưa được tập BT3 chạy |
| routes.course_search riêng |6/6=100% |0 explicit branch được coverage đếm |success/domain-error lines đều chạy; failure tests kiểm exceptions |
| Tổng3file |83/163≈50,92% |6/8=75% |CLI combined metric52,05%, không gọi là line52% |

Uncovered: `_raise_profile_error` branches47→48/49 và các programs/profiles/
recommendations/transcript/eligibility/advisor lines liệt kê trong coverage.json.
Đây không phải chứng cứ những API đó hỏng hoặc chưa từng được regression khác
chạy. Coverage không đếm mọi short-circuit điều kiện trong comprehension như một
branch domain; cases q/nullable/filter/ties cung cấp bằng chứng bổ sung.
Chưa chứng minh Unicode normalization, dataset cực lớn, live PG source revision
đổi giữa trang hoặc mọi schema evolution tương lai. Risk map ở TRACEABILITY.

## Flaky review

1. **Order/shared state**: repository không cam kết thứ tự nguồn; `.sort()` tại
   chỗ có thể làm lần gọi sau phụ thuộc lần trước. Kiểm soát bằng sorted list mới,
   literal expected,24 hoán vị4tied rows/sort, reverse input và10 vòng lặp cùng
   catalog. Sáu subprocess với hash seed1/17/231953, mỗi seed2lượt, fixture reset:
   tất cả46passed. Không randomness trong dataset; không dựa set order.
2. **Concurrency/time**: worker chưa thật đồng thời hoặc startup ngủ cố định có
   thể tạo false confidence. Dùng100 tasks đợi Event và ready queue, observed
   peak100; server readiness theo HTTP marker từng run, không giả định ngủ là
   sẵn sàng. Mỗi run server/temp fixture mới, cùng immutable data, mọi response
   kiểm oracle;12000/12000correct trong6lượt chính thức, không race correctness
   quan sát được. Latency biến thiên đã làm SLO fail, nên không đặt threshold timing
   dễ flaky vào offline pytest/không rerun chỉ chọn số đẹp. UUID chỉ nhận diện
   process lifecycle, không làm random test data. Không kết luận mọi race đều loại trừ.

Network kiểm soát thêm: autouse `isolated_runtime` chặn HTTP outbound ở pytest,
LLM disabled; HTTP experiment chỉ gọi test loopback và fake mail. Không gọi VNU.

## Performance:100 concurrent client tasks

App cb3b35d; Windows26300 AMD64, AMD Family25Model116,12logical CPU;
Python3.11.9/FastAPI0.143.0/Uvicorn0.54.0/HTTPX0.28.1/Pydantic2.14.1.
Client và Uvicorn riêng process, một server worker; trên cùng máy chia sẻ CPU.
Không tài nguyên production/shared, không DB, không paid/external provider.
JSON repo thật đọc/normalize/validate từng request; OS file cache ấm, không app cache.
240 môn ở program đo,3catalog khác mỗi cái1môn; tên/tín chỉ tie có chủ đích.

Mỗi cấu hình3server mới×(50warmup+100workers×20requests)=6000measured;
150warmup loại khỏi số đo.10query cases chia đều600request/case/cấu hình,
gồm search/filter/page/sort/empty/out-of-range và10%legacy full-array. Async Event
barrier và max_connections100; mỗi worker chờ response xong mới gửi request kế.
Peak100 client in-flight **không** có nghĩa100thread CPU hay100VNU sessions.
Latency ms đo trước client.get tới sau decode/assert response; percentile nearest
rank `sorted[ceil(p*n)-1]`. Correctness errors hoặc non200 đều làm run fail.

| Cấu hình/run | Requests đúng/lỗi | Thời lượng s | p50 ms | p95 ms | max ms |SLO |
|---|---|---|---|---|---|---|
| Default/1 |2000/0 |21,4456 |585,938 |3534,735 |8406,780 |failed |
| Default/2 |2000/0 |12,0341 |353,538 |1698,054 |5120,046 |passed |
| Default/3 |2000/0 |18,7440 |561,377 |2590,135 |6987,699 |passed |
|8tokens/1 |2000/0 |23,2960 |714,045 |3293,964 |8556,463 |failed |
|8tokens/2 |2000/0 |18,3326 |539,580 |2501,387 |8904,938 |passed |
|8tokens/3 |2000/0 |19,8545 |565,802 |2742,991 |6002,047 |passed |

NFC-01 **failed ở cả hai cấu hình theo tiêu chí mọi lượt phải đạt**. Không đổi
data/mix/percentile/warmup để che kết quả. Không kết luận vượtSLO có nguyên nhân
duy nhất: profile500serial đọc+search mất1,698s, loader1,599s, service0,100s
(profile.log). Đây gợi ý loading/validation chiếm khoảng94%, nhưng profile serial
không chứng minh toàn bộ tail latency concurrent. Giả thuyết thread contention
được thử bằng8tokens (chỉ wrapper test, không đổi runtime); không cải thiện ổn
định, không áp dụng vào production. Không thêm cache để trả dữ liệu cũ khi storage
hỏng vì có thể vi phạm AC05. Follow-up có giá trị: profile concurrent riêng client/
server, benchmark PG test cô lập và xem cache revision-aware có giữ lỗi503 hay không.

Các lần bootstrap/ready/cleanup thất bại giữ log riêng; không tính vào6000request
chính thức. Lỗi alias module, PID launcher Windows, quyền cleanup được chẩn đoán,
sửa marker/graceful shutdown; hai PID test sót27036/27028 đã được xác minh command
line và dừng thành công bằng taskkill riêng, không đụng app chính. Browser và6run
chính thức dùng wrapper đã sửa; shutdown/new temp directory hoàn tất.
