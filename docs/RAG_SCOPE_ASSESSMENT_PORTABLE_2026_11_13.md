# Sửa scope/assessment và chạy HUS RAG từ checkout

Ngày13/11/2026, nhánh `hus-llm-rag`, nền `f61b0fd` + WIP. Thay đổi còn local, chưa commit/push, gọi Google hoặc deploy.

## Người tải dự án tự chạy và test

Luồng chính là [quickstart từ checkout](HUS_RAG_QUICKSTART.md).
`tools.run_hus_rag` lấy root theo vị trí source, dùng dữ liệu trong repository,
lexical và LLMoff. Cài `requirements-rag.txt` với constraints `requirements-lock.txt`
trên Python3.11. Không cần private `.env`, tài khoản, DB, vector model, key hoặc
dịch vụ trên máy tác giả. `--check` kiểm API/dữ liệu/menu/citation với provider
bị chặn; chạy server mở loopback8011 trên máy đó. Lệnh cũ
`tools.run_hus_submission` chuyển tiếp tới cùng launcher.

Đã export215 file source công khai sang đường dẫn Unicode khác, không có Git/
backups/`.env`, cài25 wheel đã kiểm vào venv mới, chạy từ working directory
khác. Pip check đạt;20 ca API/bốn ngành và menu2.124 đạt. Biến kế thừa trỏ root
sai/vector/LLMtrue được launcher thay bằng cấu hình local. Đây là kiểm
Windows/Python3.11.9 hiện tại, **chưa phải clone remote hoặc máy/OS khác**.

Workflow `.github/workflows/hus-rag.yml` cài minimal dependency/chạy check trên
Windows/Linux/macOS, không dùng secrets. Chưa có kết quả GitHub Actions;
người clone nhận thay đổi sau commit/push. Kit Windows cũ giữ nguyên, chứa
code trước sửa hiện tại; không là dependency của quickstart.

## Sửa baseline chung

- Chuẩn hóa cả cụm CLC/hệ chất lượng cao thành scope `high_quality`, lọc F1
  retrieval và kiểm metadata khi xác nhận bằng chứng. Không xóa từ đơn chung;
  unknown/hệ khác, xung đột scope, edition hoặc chi tiết thiếu trong body vẫn
  không được trả lời bằng nguồn sai phạm vi.
- “Nội dung của gợi ý đánh giá” là một field assessment. Không vượt ranh giới
  mệnh đề/liên từ; content/objectives/credits độc lập vẫn cần làm rõ. Thiếu
  assessment vẫn no_information, không tạo kiến thức AI.
- [Chính sách nguồn/edition](HUS_F1_SOURCE_EDITION_POLICY.md) áp dụng trước
  inference tiếp. Q003 giữ completeness fail lịch sử; không ép ranking, đổi
  gold hoặc suy hai danh sách học thuật tương đương.

47 regression mới bao phủ tương tự/negative, scope/edition, nhiều field và
opt-in. Một regression admission cũ sửa cách ghi nhận search khi filter trả
tập rỗng; vẫn đòi no_information/không citation, giữ unknown trong inventory.
Đợt runtime đầu có1 lỗi instrumentation này; JUnit RED/lỗi giữ lại, không hạ
tiêu chí nguồn. Kết quả cuối:656 runtime/RAG/API,525 LLM offline và98 evaluator/
package đạt. Các nhóm có giao nhau, không cộng thành tổng full-repo.

Diagnostic48 câu đã lộ chỉ thay A7F-Q002 thành answered đúng high_quality và
Q011 thành no_information khi thiếu assessment.46 response khác/Q003 và12 F2
nguyên vẹn. Không phải điểm A7 mới; run/gold/review lịch sử giữ nguyên:
Recall24/24, đủ ý34/36, controls11/12 không được chấm lại.

## Candidate và bước sau

Candidate `a7_scope_assessment_20261113_r1` nằm trong `candidates/`:
48 câu/12 mỗi ngành,36 bằng chứng, pins/nguồn/gold trước inference. Provider,
retrieval/answerer bị chặn trong freeze; **chưa chạy prediction**. Không trùng
wording trong31 input đã kiểm nhưng6 target F1 đã lộ/tái dùng. AI-author/
runtime/source exposed, human0; không coi là holdout độc lập. Bộ A7F cũ là dev.

Runtime mới khiến prepared L5 r2 cũ stale. Không Google call mới; hai ngân sách
24 calls đã hết. LLM vẫn off/L6keep_disabled; prepare mới, quyền Google/ngân
sách riêng và review bản sinh thật trước khi xét bật. Kit đã seal không ghi
đè; chỉ tạo revision mới khi cần bàn giao offline.

[Receipt kiểm chứng](../data/hus/qa/20261113/scope_assessment_portable_r1/report.json)
ghim kết quả, hash file cũ, proof source di chuyển và candidate freeze.
