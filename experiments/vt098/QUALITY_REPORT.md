# VT-098 — Who tests the tests? (yêu cầu 4)

Dương Văn Tài — 23001925 — SE2026-T25 — AI-07. Date: 2026-10-30 (Asia/Bangkok).
Phạm vi: executable SQLite harness cho bản nháp rỗng, chưa nối production.
Code thực nghiệm ở commit `682496291524ae28f51574085a6023ef8ff1478a`; baseline dự
án vẫn là `7b387a394e334e217733a571ee76a573157a24f2`.

## Mutation có control và nhánh tạm

- Control dùng `len(key) > 64`. Mutant đổi **đúng một toán tử** thành `>= 64`.
- Lần đầu ở commit tạm `55f03c7` phát hiện lỗi bằng test hiện có. Sau khi bổ sung
  test body 16 KiB theo coverage, chạy lại trên cặp source/test 19 methods giống
  nhau, mutant ở `0a057964cb2819cda5af0abbadd4b748536f8600` (parent `6824962`).
- Lệnh focused test: `python -X utf8 -m unittest experiments.vt098.test_harness.HarnessTests.test_valid_key_boundaries -v`.
- Control exit 0. Mutant exit 1: parameter `length=64` nhận
  `HarnessError: invalid_idempotency_key`; count cuối `(2,2,2)` thay vì `(3,3,3)`.
- `evidence/mutation.json` xác nhận test bytes giống nhau và source runtime khác
  đúng một phép thay toán tử. `mutation-initial.json` giữ lần đầu, không xóa
  evidence khi test suite phát triển. Không cần sửa test để giết mutant vì nó đã
  bị test sẵn có phát hiện. Đây là một mutant được chọn, không phải mutation score
  tổng quát. Nhánh nộp giữ nguyên `harness.py` như `91b2030`.

Nhánh mutation tạm: `vt098/23001925-boundary-mutation-reviewed`. Không merge.

## Line/branch coverage và lỗ hổng còn lại

Coverage.py 7.17.0 đo branch khi chạy toàn bộ suite; chỉ báo cáo scope hai module
harness/loader, không gán tỷ lệ cho production hoặc cho chính runner `quality.py`.

| Scope | Line coverage | Branch coverage | Diễn giải |
|---|---:|---:|---|
| harness.py, trước bổ sung (18 methods) | 84/85 = 98,82% | 17/18 = 94,44% | Thiếu nhánh body vượt 16.384 byte |
| harness.py, sau bổ sung (19 methods) | 85/85 = 100% | 18/18 = 100% | Thêm test đúng 16.384 / 16.385 byte; giữ nguyên runtime |
| schema.py | 13/14 = 92,86% | 1/2 = 50% | Chưa chạm guard thiếu/trùng class schema, dòng 20 |
| Hai file sau bổ sung | 98/99 = 98,99% | 19/20 = 95% | Không suy ra correctness từ con số này |

Raw `coverage-full.json` còn ghi phần class động tại tên file gốc
`app/api/academic.py` do AST compile giữ filename. Chỉ declaration của schema
chạy; routes/auth không được thực thi. Tỷ lệ raw của file này không phải API
coverage và không thuộc denominator hai module nêu trên. Giữ raw report để người
đọc kiểm tra scope. Coverage branch không phải mọi tổ hợp điều kiện/MC/DC hoặc
mọi interleaving. Không thêm test chỉ để che guard còn thiếu.

| Acceptance criterion / risk | Evidence ở mức harness | Giới hạn risk coverage |
|---|---|---|
| AC1 / RK1 | First create, SQL counts, new-load 150; plan/audit/receipt cùng transaction | Chỉ empty draft SQLite; chưa API/PostgreSQL/eligibility |
| AC2 / RK1 | Replay JSON/version, reopen connection, hot-key load, quota/delete tests | Chưa kill process/OS hoặc retry HTTP thật |
| AC3 / RK2, RK5 | Same-key/body conflict, invalid key, key 64 mutant, body byte limit | Status là result code harness; chưa HTTP middleware |
| AC4 / RK2 | Cùng key hai account tách biệt, key mới giữ ý định mới | **Partial**: principal do test cấp, auth/CSRF thật chưa kiểm chứng |
| AC5 / RK3 | Fault sau từng write rollback hết; fault sau commit replay receipt | Controlled exception, không power loss/TCP loss/distributed transaction |
| NFC2 / RK4 | Sáu lần chạy với clock/order/hash seed/network guard | Finite scenarios, không chứng minh không còn flaky |

## Flaky-test review thực thi

`quality flaky` chạy sáu process mới: normal/reverse/shuffle, hash seeds 1/2/7/29,
wall clock giả ở epoch 0 hoặc năm 2100. Tất cả **114 method executions** pass.
`time.sleep`, DNS và `socket.connect` bị chặn bằng assertion; số attempt bằng 0.

1. **Time/network:** test không cần Internet hoặc ngủ chờ TTL; receipt không có
   TTL. Chỉ freeze `time.time`, không freeze `perf_counter` dùng đo tải. SQLite
   C-level busy wait vẫn thực; không nhận kết quả này làm chứng cứ session expiry
   hay timeout VNU/Gemini production.
2. **Order/shared state:** mỗi method có TemporaryDirectory/database mới; các
   parameter pairwise có file riêng, patch global BASIS dùng context để restore.
   Đảo/shuffle order không làm rò state trong sáu lần quan sát. Chưa chạy mọi order.
3. **Concurrency/random:** bốn pairwise hàng dùng hai connection qua barrier;
   sáu lần chạy cho 24 race scenarios đó. Không dùng sleep để tạo race. UUID ngẫu
   nhiên chỉ so sánh identity/quan hệ, không hard-code expected UUID; shuffle seed
   được ghi lại. Hai task chưa bao phủ mọi lịch; tải 150 bổ sung stress thực tế.

Không auto-retry test fail để biến suite thành xanh. Không quan sát flake trong
các lần này không có nghĩa xác suất flake bằng 0.

## Tải 150 tác vụ đồng thời và p95 <= 4.0 giây

Mỗi burst khởi tạo **150 worker threads**, chờ barrier rồi phát cùng lúc; mỗi call
dùng SQLite connection riêng. Peak call thực tế 150 ở 7 burst, 149 ở 2 burst:
báo đầy đủ thay vì coi mọi request đều chạy vật lý cùng một thời điểm.

Ba workload, ba vòng cố định, DB file mới cho mỗi burst:

- **new:** 150 account tổng hợp riêng, mỗi account một key mới, tránh quota 100.
- **hot-key:** 150 call cùng account/key/body chưa commit; đúng một create và
  các replay, không seed trước. Kỳ vọng cuối `(plan,audit,receipt)=(1,1,1)`.
- **mixed:** seed 75 account ngoài thời gian đo; burst có 75 replay và 75 create
  cho account khác. Cuối `(150,150,150)`, đúng 150 response IDs riêng.

| Workload | p95 vòng 1 (s) | p95 vòng 2 (s) | p95 vòng 3 (s) | Lỗi | Kỳ vọng DB |
|---|---:|---:|---:|---:|---|
| new | 1,9618 | 2,8022 | 3,0686 | 0 | 150/150/150 |
| hot-key | 1,9927 | 1,3026 | 1,7401 | 0 | 1/1/1 |
| mixed | 2,6054 | 2,4936 | 2,3009 | 0 | 150/150/150 |

Tổng **1.350 mẫu**, không bỏ sample lỗi/chậm, không bỏ vòng đầu. Tất cả status
201, oracle độc lập SQL count/unique ID pass. Mọi p95 burst <= 4.0 s; cao nhất
3,0686327 s, max toàn mẫu 3,357376 s. Các p95 create/replay trong mixed được lưu
riêng; cao nhất của các nhóm là 2,7310265 s.

Đồng hồ `time.perf_counter` thực; latency từ mốc chung barrier release đến return
hoặc error của `create()`, bao gồm OS dispatch/SQLite lock waiting, loại setup,
preseed và network. Nearest-rank: `sorted(samples)[ceil(0.95*n)-1]`; n=150 lấy
mẫu thứ 143. Timeout SQLite writer 10 giây; journal `delete`, synchronous=2.
Observer connection có busy_timeout=5.000 ms, không nhầm với writer 10.000 ms.
Windows-10-10.0.26300, Python 3.11.9, SQLite 3.45.1, Pydantic 2.12.5, 24 logical
CPUs; payload 173 byte (số chính xác nằm trong JSON). Không diễn giải số CPU
như cấu hình deployment hoặc số core vật lý.

**Kết luận có giới hạn:** mục tiêu đạt trong chín burst giả lập này. Không chứng
nhận p95 HTTP người dùng thật, PostgreSQL lock/pool, auth/CSRF, mạng, LLM, lớp dữ
liệu lớn, cold start hoặc sustained/soak load. Độ trễ ba vòng biến động rõ; không
suy ra confidence interval từ 3 vòng. Gate tiếp theo có giá trị là API+PostgreSQL
test với tài khoản tổng hợp, cùng workload và xác nhận quyền trước replay.

## Evidence và AI

`quality.py`, `requirements-quality.txt`, các JSON `coverage*`, `mutation*`,
`flaky.json`, `load.json` có lệnh, source hash, environment và raw results.
README hướng dẫn chạy lại. Git evidence không thay code bằng ảnh.

AI tự sinh runner/test body boundary và đọc kết quả; agent review thấy filename
AST làm raw coverage có thêm file API nên báo scope riêng, và thấy peak thực tế
149 ở hai burst nên không khai nhận peak 150 mọi vòng. Chưa có independent human
review. Prompt thực tế là yêu cầu 4 người dùng cung cấp trong phiên; không dùng
prompt/test data/mutation/reflection của thành viên khác. Yêu cầu 5 được bổ sung
trong ENGINEERING_EVIDENCE.md, AI_USAGE.md và REFLECTION.md.
