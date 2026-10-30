# Publication receipt — executed và verified

Git push nhánh riêng đã **executed/passed**, exit0; `git ls-remote` trả SHA đúng
`2e864fc565e525da3b967f6c607e1ba5860f67f5`. Khi xác minh, GitHub main vẫn
`7b387a394e334e217733a571ee76a573157a24f2` như baseline GĐ0.
Evidence: `evidence/push-initial.log/json`, `remote-verification.log/json`.

[Branch GitHub](https://github.com/5-Bit-System/SE_Project/tree/bt3/23001953-VT-101-search-contract).
Không force-push, không merge main/nhánh chung, không sửa tác giả Git đã cấu hình.

| Checkpoint | Commit thật | Nội dung |
|---|---|---|
| Baseline |7b387a394e334e217733a571ee76a573157a24f2 |main chính thức lúc bắt đầu |
| Test-first |a5aab95c9d8453093621453b25f5807e584e15a3 |spec/test/evidence, intentional RED |
| Implementation |cb3b35d944364e74fec65af4b299a79fcb90df36 |search API đúng, contract/regression GREEN |
| Experiments/docs |2e864fc565e525da3b967f6c607e1ba5860f67f5 |harness/mutation/coverage/load và full handoff, published |

Receipt này và hai sửa metadata tool (tách review result khỏi runner record,
đổi nhãn timestamp mutation thành recorded_utc) nằm trong commit tiếp theo.
Không đổi production hoặc pytest cases đã kiểm chứng. Lấy tip/cuối receipt bằng
`git rev-parse HEAD` hoặc `git log -1 --format=%H --` trên file này; không ghi
SHA chưa tồn tại vào chính commit chứa nó. Final response cung cấp SHA cuối.

## GitHub Actions

[Run41097122762](https://github.com/5-Bit-System/SE_Project/actions/runs/41097122762),
head2e864fc: **offline passed, postgres passed, hus_postgres passed**; GitHub API
xác nhận completed/success cả3job tại2026-10-30T17:17:11Z. Receipt API ở
`evidence/github-checks-code.json` (initial receipt giữ trạng thái in_progress
trước đó). PostgreSQL CI dùng test DB riêng theo workflow, không DB cá nhân/nhóm.
Chưa trích log count PG từ API nên không bịa số test remote. Các số619/79/46
là số local có command/log.

## Pull request và review

PR **chưa tạo**; không khẳng định draft tồn tại. Môi trường không có `gh` hay
GitHub write app tool. Push dùng Git credential manager nội bộ; không trích
token/credential để tự làm REST write. Tạo PR là tùy chọn trong yêu cầu lượt này.
Đã chuẩn bị [PR_DRAFT.md](PR_DRAFT.md) và
[link mở PR](https://github.com/5-Bit-System/SE_Project/pull/new/bt3/23001953-VT-101-search-contract).
Nếu sinh viên tạo, chọn Draft, nêu bài cá nhân và chờ nhóm review; không merge.

**Known limitation:** p95≤3s chưa đạt ổn định ở cả hai cấu hình; không vì CI xanh
mà nâng performance thành passed. Chưa có human approval, production proof hoặc PDF.
