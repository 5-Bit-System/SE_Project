# Engineering evidence — VT-098

Dương Văn Tài — 23001925 — SE2026-T25 — thành viên — AI-07.
Repository: https://github.com/5-Bit-System/SE_Project.
Baseline: `7b387a394e334e217733a571ee76a573157a24f2`.
Nhánh nộp: [`vt098/23001925-idempotency`](https://github.com/5-Bit-System/SE_Project/tree/vt098/23001925-idempotency).
Không có PR: connector trả 403 khi tạo draft PR. Không merge.

## Quy ước evidence và scope

- T = [`experiments/vt098/test_harness.py`](https://github.com/5-Bit-System/SE_Project/blob/682496291524ae28f51574085a6023ef8ff1478a/experiments/vt098/test_harness.py).
- Q = [`experiments/vt098/quality.py`](https://github.com/5-Bit-System/SE_Project/blob/682496291524ae28f51574085a6023ef8ff1478a/experiments/vt098/quality.py).
- R = [`a20c996`](https://github.com/5-Bit-System/SE_Project/commit/a20c996f65b017b4dc1a2e3d9b692a25fec42f94): reviewed tests đỏ trước patch.
- P = [`91b2030`](https://github.com/5-Bit-System/SE_Project/commit/91b20308dc86daa8b1067db3e558aba350635e61): patch, 18 methods xanh.
- C = [`6824962`](https://github.com/5-Bit-System/SE_Project/commit/682496291524ae28f51574085a6023ef8ff1478a): thêm test body boundary, 19 methods xanh và quality evidence.
- D = [`cf167fe`](https://github.com/5-Bit-System/SE_Project/commit/cf167febb52899baae8d63ffc128dadab62e939e): log mutation cuối và diễn giải.
- M = [`0a05796`](https://github.com/5-Bit-System/SE_Project/commit/0a057964cb2819cda5af0abbadd4b748536f8600): mutant tạm, không thuộc ancestry nhánh nộp.

TC01–TC20 là ID thiết kế trong báo cáo. Kết quả dưới phân biệt rõ bản kiểm chứng
trong harness với API/PostgreSQL/E2E dự kiến. Không gán PASS cho test chưa tạo.
Nội dung không thay thế kiểm tra quyền/nguồn học vụ của production.

## Traceability: AC/risk → case → file/method → commit → kết quả

| Acceptance criterion / risk | Test case | Test file / method (permalink dòng) | Commit | Kết quả / artifact |
|---|---|---|---|---|
| AC1–2 / RK1: ghi mới, replay giữ kết quả | TC01, TC05 | [T:64 `test_retry_response_and_counts`](https://github.com/5-Bit-System/SE_Project/blob/682496291524ae28f51574085a6023ef8ff1478a/experiments/vt098/test_harness.py#L64) | R → P; C | Harness pass; JSON/version/SQL counts. `reviewed-red.json` → `green.json`; `coverage.json` |
| AC1–4 / RK1–2: key/body/account/dispatch | TC01–TC08 | [T:100 `test_pairwise_create_replay_conflict_and_scope`](https://github.com/5-Bit-System/SE_Project/blob/682496291524ae28f51574085a6023ef8ff1478a/experiments/vt098/test_harness.py#L100), [T:92 pair coverage](https://github.com/5-Bit-System/SE_Project/blob/682496291524ae28f51574085a6023ef8ff1478a/experiments/vt098/test_harness.py#L92) | P, C | 8 subcases pass trong SQLite, 24/24 cặp; API/PostgreSQL level chưa chạy |
| AC3 / RK2: key cũ/body khác | TC03 | [T:182 `test_conflict_keeps_original_unchanged`](https://github.com/5-Bit-System/SE_Project/blob/682496291524ae28f51574085a6023ef8ff1478a/experiments/vt098/test_harness.py#L182) | P, C | Harness 409 conflict, không thêm/sửa dữ liệu gốc; `coverage.json` |
| AC3 / RK5: biên key hợp lệ và key sai | TC09–10 | [T:142 valid boundaries](https://github.com/5-Bit-System/SE_Project/blob/682496291524ae28f51574085a6023ef8ff1478a/experiments/vt098/test_harness.py#L142), [T:148 invalid keys](https://github.com/5-Bit-System/SE_Project/blob/682496291524ae28f51574085a6023ef8ff1478a/experiments/vt098/test_harness.py#L148) | P, C | Harness pass cho 1/63/64 và các key sai; chưa HTTP header/middleware |
| AC2–3 / RK5: default/order/body fingerprint | TC11 | [T:157 `test_canonicalization_uses_real_schema_defaults`](https://github.com/5-Bit-System/SE_Project/blob/682496291524ae28f51574085a6023ef8ff1478a/experiments/vt098/test_harness.py#L157) | P, C | Unit/helper pass; default/object order giữ fingerprint, đổi giá trị/array order thì khác |
| AC3/NFC3 / RK5: payload byte limit | B1 (bổ sung sau coverage) | [T:168 `test_normalize_body_byte_limit`](https://github.com/5-Bit-System/SE_Project/blob/682496291524ae28f51574085a6023ef8ff1478a/experiments/vt098/test_harness.py#L168) | C | Đúng 16.384 byte hợp lệ, thêm 1 byte bị 413; `coverage-initial.json` / `coverage.json` |
| AC4 / RK2: phiên hết hạn, CSRF sai trước replay | TC12–13 | Dự kiến `tests/integrations/test_semester_plan_idempotency.py` — **chưa có file** | — | **Chưa chạy**; principal của harness do test cấp, không thay test auth/CSRF |
| AC5 / RK3: rollback và retry | TC14 | [T:73 `test_failure_before_commit_rolls_back_then_retry`](https://github.com/5-Bit-System/SE_Project/blob/682496291524ae28f51574085a6023ef8ff1478a/experiments/vt098/test_harness.py#L73) | R → P; C | Harness pass: lỗi sau plan/audit/receipt rollback hết, retry tạo đúng một lần |
| AC2, AC5 / RK1, RK4: commit rồi mất return | TC15 | [T:190 `test_lost_response_after_commit_replays_receipt`](https://github.com/5-Bit-System/SE_Project/blob/682496291524ae28f51574085a6023ef8ff1478a/experiments/vt098/test_harness.py#L190) | P, C | Harness pass bằng hook sau commit; **không phải TCP loss thật** |
| AC2 / RK1: durability qua mở lại connection | TC16 | [T:85 `test_retry_after_reopen_preserves_result`](https://github.com/5-Bit-System/SE_Project/blob/682496291524ae28f51574085a6023ef8ff1478a/experiments/vt098/test_harness.py#L85) | `9b18b7d` đỏ → P; C | Connection/object reopen pass; không chứng minh process/OS restart |
| AC2/I1 / RK5: deleted/stale plan không được tạo lại | TC17 | [T:243 deleted](https://github.com/5-Bit-System/SE_Project/blob/682496291524ae28f51574085a6023ef8ff1478a/experiments/vt098/test_harness.py#L243), [T:252 current basis](https://github.com/5-Bit-System/SE_Project/blob/682496291524ae28f51574085a6023ef8ff1478a/experiments/vt098/test_harness.py#L252) | P, C | Replay gốc pass, không resurrect; GET/needs_review production chưa chạy |
| AC2/NFC3 / RK5: retry ở quota 100 | TC18 | [T:233 `test_replay_at_limit_does_not_create_again`](https://github.com/5-Bit-System/SE_Project/blob/682496291524ae28f51574085a6023ef8ff1478a/experiments/vt098/test_harness.py#L233) | P, C | Retry pass, key mới bị limit; vẫn 100 plan/audit/receipt |
| AC2, AC4–5 / RK2, RK4–5: UI retry và ý định mới | TC19–20 | Dự kiến `tests/frontend/check_plan_idempotency.py` — **chưa có file** | — | **Chưa chạy E2E**; mock browser baseline không chứng minh invariant ghi DB |
| AC3 / RK5: test có bắt bug biên? | M1, TC09 | [T:142](https://github.com/5-Bit-System/SE_Project/blob/682496291524ae28f51574085a6023ef8ff1478a/experiments/vt098/test_harness.py#L142), [Q:67 `mutation`](https://github.com/5-Bit-System/SE_Project/blob/682496291524ae28f51574085a6023ef8ff1478a/experiments/vt098/quality.py#L67) | C control / M mutant; D log | `mutation.json`: control exit 0, mutant exit 1, same test bytes; `integrity.json`: nhánh nộp sạch |
| NFC2 / RK4: flaky time/order/network/concurrency | F1 | [Q:148 `flaky_run`](https://github.com/5-Bit-System/SE_Project/blob/682496291524ae28f51574085a6023ef8ff1478a/experiments/vt098/quality.py#L148) + T | C | `flaky.json`: 6 process, 114 executions pass, dependency attempts rỗng; không chứng minh mọi lịch |
| NFC1 / RK1, RK4: tải và invariant | P1–P3 | [Q:248 `load_run`](https://github.com/5-Bit-System/SE_Project/blob/682496291524ae28f51574085a6023ef8ff1478a/experiments/vt098/quality.py#L248) | C | `load.json`: 150 task/burst × 9, 1.350 mẫu, max burst p95 3,0686 s, 0 lỗi; **không phải SLA HTTP** |

Các artifact nằm trong [`evidence/` tại D](https://github.com/5-Bit-System/SE_Project/tree/cf167febb52899baae8d63ffc128dadab62e939e/experiments/vt098/evidence).
Các test T có kết quả cuối trong `coverage.json` (19 methods OK). `green.json`
giữ riêng lần test-first 18 methods tại P; không ghi đè lịch sử để nhận là 19.
File test ở R/P giống nhau; C thêm đúng test B1 sau xem coverage.

## Hai output AI hợp lý nhưng không đáng tin ngay

1. **D1 — hai lần 201 nghĩa là retry an toàn.** Code executable ở `9b18b7d`
   pass dù ID khác. Sửa thành T:64 ở `a20c996`, thêm so sánh toàn JSON/version và
   đếm SQL từ connection độc lập. `draft-red.json` chứng minh false confidence;
   `reviewed-red.json` → `green.json` chứng minh oracle mạnh hơn.
2. **D2 — thêm một happy path tương tự làm suite đáng tin hơn.** Test cũ lặp lại
   hành vi D1, không đi qua điểm lỗi giữa plan/audit/receipt. Thay bằng T:73 ở
   `a20c996`, inject lỗi sau từng write, kiểm tra rollback rồi retry. Trước/sau
   code có trong Git; không lấy hai sửa plan R1/R2 để nhận là đã sửa hai test.

Review này do agent thực hiện. Không giả nhận sinh viên đã tự kiểm tra độc lập.
Không suy từ 100% wrapper branch coverage ra đúng toàn hệ thống; loader guard
chưa test, auth/CSRF và PostgreSQL vẫn là risk chưa chứng minh.

## Lệnh tái chạy

Xem [README.md](README.md): unittest cho harness, quality coverage/flaky/load,
mutation worktree riêng. Mỗi JSON lưu command thật, môi trường và source hashes.
Source `harness.py` nhánh nộp giữ nguyên `91b2030`; không merge mutant hoặc main.

## Reflection và AI Usage Log

[REFLECTION.md](REFLECTION.md) chứa reflection 250–350 từ theo whitespace token;
[AI_USAGE.md](AI_USAGE.md) khai công cụ/prompt/output/sửa-bác bỏ/evidence.
Nội dung được tạo riêng từ phiên này, không sao chép artefact thành viên khác.
Đây là bản do AI hỗ trợ; sinh viên còn cần tự đọc và xác nhận trước khi nộp.
