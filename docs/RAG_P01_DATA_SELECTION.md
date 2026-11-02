# P0-1 — Chốt dữ liệu và adapter RAG

## Quyết định

Runtime local sử dụng **duy nhất portable `hus-data-20261031-v3`** qua
`data/hus/rag/CURRENT.json`, release SHA256
`27bdf3714216292af6d6c6da10e7edd164fa6cf8a286fca7338d18bcb05501f4`.

Đã nhập nguyên byte từ `feat/hus-data-ready-20261031` commit
`a543cf8d1fac273db41a65a14fb7ae0a05b2d965`: 47 file release (46 payload + manifest),
CURRENT và bốn module validation/reader/utilities upstream. Danh mục/hash tại
[PORTABLE_IMPORT.json](../data/hus/rag/PORTABLE_IMPORT.json). Không merge ứng dụng,
auth, UI hay DB của nhánh khác; không thay 19 payload legacy hoặc review gate cũ.
Không nhập các binary PDF vào kho portable trong P0-1.

`CURRENT.state` vẫn là `prepared_not_runtime_activated`. Đây là lựa chọn snapshot cho
runtime local theo yêu cầu P0-1, không phải phát hành production hay cấp review học vụ.
Release gồm 65 F1 +336 F2 +870 F3 =1.271 chunks; API chỉ index F1/F3, còn F2 tra cấu
trúc theo mã–ngành–phiên bản, không nạp lặp 336 F2 chunks như một nguồn thứ hai.

## Diff ID/hash/quote/edition/review

Bảng chi tiết có thể tái tạo tại
[reconciliation.json](../data/hus/qa/20261102/p01/reconciliation.json): mỗi đơn vị F1 có
ID cũ/mới, SHA quote từng chunk, span, SHA toàn đoạn nguồn, edition/variant/review;
mỗi record F3 có hash trước/sau và binding F2. Không chỉ so số chunks.

| Thành phần | Kết quả |
| --- | --- |
| F1 selected unit IDs | Cùng **63** đơn vị được truy xuất; không mất hoặc thêm unit |
| F1 chunks | 69 →65 do đổi cách chia đoạn ở đúng bốn unit dưới đây |
| F1 quote/hash | Nguồn cùng hash; span bao phủ cùng vị trí; mọi quote khớp file evidence. Ghép nội dung không kể khoảng trắng giữ đủ toàn bộ nội dung của từng unit |
| F1 edition/variant/review | Không đổi giữa unit cũ/mới; các quyết định Markdown vẫn `include_markdown`, không biến thành duyệt toàn PDF hoặc xác minh học vụ |
| F1 display | V3 có chỉnh hiển thị đã khai báo trong `display_edits`; source_quote và offset vẫn nguyên gốc |
| F2 bảng nghiệp vụ | Toàn bộ bảng giống bản legacy: mã/tên/tín chỉ/membership/nhóm/297 dòng nguồn/348 option không đổi |
| F2 metadata | Chỉ đổi `source`, `metadata_source_manifest`, thêm `catalog_reviews` |
| F3 | 290 record/870 chunks; generated content/objectives/suggested assessment, reviewer, review_status và official-null giữ nguyên; cập nhật binding tới canonical F2 mới, còn binding cũ trong `legacy_f2_binding` |

| Source ID / mục tiêu F1 | Số chunk cũ →mới | Span gốc giữ nguyên |
| --- | --- | --- |
| `0dd9aaaeefcbd7d7` / chuẩn đầu ra Toán tin | 3 →2 | `[16, 3304)` |
| `1c16ddf8a6f1f409` / mục tiêu CLC | 2 →1 | `[7475, 9203)` |
| `31b55b4ee6f451a6` / chuẩn đầu ra KHMTTT | 3 →2 | `[363, 4039)` |
| `f7f470e712738589` / mục tiêu chương trình KHMTTT | 2 →1 | `[1159, 3550)` |

63 là số unit thực sự có trong legacy chunks; file unit cũ còn giữ ba unit CLC trùng
để bảo toàn provenance. Không cộng các unit/chunk lịch sử hoặc cả hai release vào index.
Chunk IDs v3 khác do schema/chia đoạn mới; dùng crosswalk trong receipt, không coi đổi ID
là mất nguồn hoặc tự lấy ID cũ gán cho nội dung mới.

## Canonical F2 và sign-off

| Nguồn | Git blob | SHA256 bytes |
| --- | --- | --- |
| Legacy | `79dd58bc54998def1f0f5fe60016d068affc0433` | `6cd94644f6df4a6bfd75f3354cc78c287a6fe161662e2b2729d01390c9edc15a` |
| Canonical trong v3 | `38be5742a07e47de2ca868c4d570393828d0738e` | `e0449d63cd73e90042880941df784d78800a9f7743c2dc99d7b251c4a1a06c6c` |

Đã đối chiếu lại `main` tại `5239b7333a8f8cdf0f919e6b0505af0def99fe23`: blob F2 đúng
`38be5742…`. Release ghim canonical từ `94b7d05988d4118df283ad09a12ff75cef3161fc` với
cùng blob, nên không trôi theo HEAD main khi có request mới.

Import nguyên trạng **67 membership KHMTTT `verified` theo `explicit_user_attestation`**
đã có trong canonical; **223 membership còn lại vẫn `draft_unverified`**. Giữ reviewer,
thời gian, hash nguồn và statement trong `catalog_review`; đây là sign-off cấp dự án,
`institutional_certification=false`, không phải chứng nhận mới do trợ lý/trường cấp.
F3 của KHMTTT vẫn `needs_review`, `academic_verified=false`; F2 được sign-off không biến
đề cương AI thành nội dung chính thức. Các metadata recovery F1 được giữ đúng mức
selected-prose comparison, không chứng minh byte-equivalence với bản crawl lịch sử.

## Adapter và một release cho mỗi request

- `HUSRAGData.load_current()` là đường runtime, đọc CURRENT một lần và kiểm ID/hash,
  inventory, kích thước, mọi payload và semantic validation của portable release.
- `portable_adapter.py` chụp bytes đã kiểm vào snapshot riêng trước validation và
  mapping. F1, F2, F3, chương trình và review đều từ cùng snapshot; không đọc legacy,
  `qa/` hoặc nguồn main ở thời điểm trả lời.
- F2 sử dụng bảng canonical cùng `f2_records.catalog_review` của chính release đó.
  Quote, portable chunk/record, citation gốc và release identity được giữ trong metadata.
- Mỗi `HUSAnswer` có `release_id`, `release_sha256`, `generated_reference_allowed`, kể
  cả khi không có thông tin. Request không đổi release giữa tra ngành, F2 và retrieval.
- Service cache một snapshot. Khi cập nhật CURRENT, request đang chạy vẫn dùng snapshot
  cũ hợp lệ; muốn nạp bản mới phải restart hoặc `get_hus_answerer.cache_clear()`. Đây chưa
  phải cơ chế hot activation/rollback của production.
- CURRENT hoặc payload sai/mất →503, **không fallback** về gói legacy. `HUSRAGData.load()`
  còn giữ cho audit/test legacy có chủ đích, không được service tự gọi khi v3 hỏng.

## Generated opt-in

Mặc định **không truy xuất/không trả F3 AI sinh**. Điều này không tạo thêm thẩm định cho
nguồn; chỉ là lựa chọn sử dụng kiến thức tham khảo trong request hiện tại.

| Lớp | Cách bật tường minh |
| --- | --- |
| Loader | `data.chunks("f3", major=..., allow_generated=True)` |
| Retriever | `search(..., dataset="f3", allow_generated=True)` |
| `/hus/chat` và `/advisor/chat` | JSON `allow_generated_reference: true` |
| Chat UI | Chọn “Cho phép kiến thức AI tham khảo (chưa được xác minh)” |

Request chưa opt-in nhận `needs_clarification` cho F3 có định danh phù hợp. Cho phép
trong một request không tự cho phép request sau; UI bỏ chọn khi đổi ngành/hồ sơ.
Hỏi tỷ lệ/hình thức thi chính thức vẫn `no_information` kể cả đã opt-in.

```python
from app.hus.rag_loader import HUSRAGData
from app.hus.answering import HUSAnswerer
from app.schemas.hus import HUSQuestion

data = HUSRAGData.load_current()
answer = HUSAnswerer(data).answer(HUSQuestion(
    question="Nội dung MAT3533?", major="data_science", version="QD3569-2023",
    allow_generated_reference=True,
))
assert answer.release_id == "hus-data-20261031-v3"
```

## Kiểm chứng và tái tạo

```powershell
python -X utf8 -m tools.compare_hus_releases --out backups/p01-diff-new.json
python -m pytest -q tests/hus/test_portable_adapter.py
node --test tests/frontend/chat.test.cjs
python -X utf8 -m tools.verify_hus_e2e --out backups/hus_e2e/p01-new --with-browser
```

Các output phải mới. Diff deterministic phải khớp receipt đã lưu. Test bao gồm sai
pointer/hash/path/policy, không fallback legacy, không đọc file qa/legacy, pointer hoặc
file đổi sau validation, giữ một snapshot/request, opt-in không rò sang request sau,
giữ sign-off và không nâng F3.

Biên bản HTTP/Chromium mới: [hus_p01_v3_report.json](acceptance/hus_p01_v3_report.json),
**2.318 ca HTTP và 29 ca Chromium đạt**. Dùng gói v3 thật, UI fixture độc lập; kiểm
thêm bật/tắt generated, release identity và review từng chương trình. Không gọi LLM,
không thay database sản phẩm. Các receipt legacy vẫn giữ riêng làm lịch sử.

Toàn bộ suite Python hiện tại **656 passed, 26 skipped**; **3/3 test Node** đạt,
Ruff, cú pháp JS và diff đạt. Report cuối ở `backups/hus_e2e/p01-v3-run02/` được sao
chép nguyên byte vào receipt trên. Các text payload và bốn module upstream được ghim
LF trong `.gitattributes` để clone Windows không làm lệch hash.

P0-1 không giải quyết P0-2: citation F2 vẫn chưa mở PDF trực tiếp, nhãn citation AI
chưa đổi toàn bộ sang “kiến thức AI”. Không dùng biên bản này để đánh dấu các yêu cầu
đó đã đạt. Tích hợp UI/auth main và phát hành remote cũng vẫn là công việc riêng.
