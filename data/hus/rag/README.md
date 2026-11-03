# Dữ liệu F1, F2, F3 dùng chung

**Phạm vi RAG hiện hành:** F1/F2/F3 và trò chuyện cơ bản. Demo độc lập chạy bằng
`python -m tools.run_hus_rag_demo`, không cần bảng điểm/eligibility và không nối
ranking/explanation. Xem [cách mở demo](../../../docs/HUS_RAG_MANUAL_DEMO.md).
P0-4/P0-5 bên dưới là lịch sử tích hợp trước khi người dùng chỉnh phạm vi; gói dữ
liệu/review không đổi. Bản main tích hợp cần nghiệm thu lại với endpoint HUS riêng.

P0-4 đã tích hợp gói này vào API/UI/auth active của main trong worktree riêng.
Gói nguồn/registry/review giữ nguyên; [biên bản P0-4](../../../docs/RAG_P04_MAIN_INTEGRATION.md)
ghi vị trí code, patch tái tạo và cách kiểm thử. Root crawldata vẫn có UI legacy.

P0-5 đã chuẩn bị CI, receipt và chuyển active/rollback trong worktree `p05-main`;
[biên bản P0-5](../../../docs/RAG_P05_RELEASE_PREPARATION.md) ghi cách tái tạo và kiểm thử.
CURRENT nguồn vẫn prepared, review giữ nguyên; chưa commit tích hợp/CI remote hoặc
kích hoạt production. Mọi diễn tập chuyển selector chỉ chạy trên bản sao.

P0-2 local đã bổ sung contract dẫn chứng và binary nguồn tại
`data/hus/citation_assets/` (12 PDF, 2 DOCX). Chatbot mở PDF qua resolver kiểm hash/trang,
web qua URL gốc, F3 hiện “kiến thức AI”; DOCX tải đúng loại, nguồn thiếu hiện lý do.
Xem [hướng dẫn P0-2](../../../docs/RAG_P02_CITATIONS.md). Binary có registry ghim với
v3 riêng, không thay đổi payload/manifest release hay nâng trạng thái review.

## Nguồn runtime hiện tại — P0-1

Runtime local chọn **`CURRENT.json` → `releases/hus-data-20261031-v3`**. Adapter kiểm
46 payload, ghim một snapshot cho mỗi request và không fallback về legacy nếu pointer/
hash sai. Có 65 F1, 336 F2 và 870 F3 chunks; F2 vẫn được API tra cấu trúc, không nạp
lặp text chunks. Canonical F2 giữ 67 membership KHMTTT có sign-off cấp dự án và 223
membership draft; F3 vẫn chưa xác minh. `CURRENT.state` prepared được giữ nguyên,
không phải phát hành production. Chi tiết, diff ID/hash/quote/edition/review và cách
bật generated tại [biên bản P0-1](../../../docs/RAG_P01_DATA_SELECTION.md).

Các thư mục `f1/`, `f2/`, `f3/` và `manifest.json` 19 payload bên dưới là **gói legacy**
được giữ nguyên để audit/tái tạo. Không ghép với portable release hoặc bản trong `qa/`.

Đây là thư mục bàn giao chung hiện tại để quản lý dữ liệu hỏi đáp. Các đầu ra gốc dưới
`data/hus/qa/20261028/` được giữ nguyên để bảo toàn review, provenance và quy trình tái tạo.

```text
data/hus/rag/
├── f1/
│   ├── rag_chunks.jsonl           # 69 đoạn F1 hiện tại
│   ├── documents.jsonl            # 15 nguồn: 5 đối chiếu raw, 10 duyệt Markdown
│   ├── f1_units.jsonl
│   ├── source_map.jsonl
│   ├── source_inventory.jsonl
│   ├── pending_F1_sections.jsonl   # Hiện rỗng: đã xử lý các tài liệu chờ
│   ├── markdown_review_decisions.json # Hồ sơ duyệt thêm 10 nguồn Markdown
│   ├── acceptance_questions.jsonl
│   └── manifest.json
├── f2/
│   ├── hus_source.json            # F2 đủ 4 ngành: 290 môn–ngành / 297 dòng nguồn
│   └── source_comparison.json     # Đối chiếu nguồn main, commit/blob và số lượng
├── f3/
│   ├── rag_chunks.jsonl           # 870 đoạn AI sinh tham khảo
│   ├── rag_documents.jsonl        # 290 tài liệu văn bản
│   ├── records.jsonl              # 290 hồ sơ cấu trúc
│   ├── source_map.jsonl
│   ├── coverage.jsonl
│   ├── acceptance_questions.jsonl
│   ├── manifest.json
│   └── inputs/blueprints.psv      # Phác thảo nội dung và mục tiêu theo mã môn
├── manifest.json                 # Danh sách bản sao, đường nguồn và SHA-256
└── README.md
```

## Các tệp chính

| Phần | Tệp chính | Trạng thái |
| --- | --- | --- |
| F1: giới thiệu, mục tiêu, nghề nghiệp ngành | [f1/rag_chunks.jsonl](f1/rag_chunks.jsonl) | 69 chunks từ 15 nguồn: 5 nguồn đối chiếu HTML và 10 nguồn duyệt phần F1 trên Markdown theo yêu cầu người dùng; chỉ dùng mô tả, chưa xác minh hiệu lực hiện tại. |
| F2: chương trình, môn, tín chỉ, tiên quyết | [f2/hus_source.json](f2/hus_source.json) | Nguồn cấu trúc đủ bốn ngành từ main đã ghim; giữ `draft_unverified` và các mâu thuẫn/điều kiện chưa xác minh. |
| F3: nội dung, mục tiêu, gợi ý đánh giá học phần | [f3/rag_chunks.jsonl](f3/rag_chunks.jsonl) | AI sinh tham khảo, phải giữ nhãn generated; không phải đề cương chính thức. |

F2 là JSON cấu trúc gồm các bảng trong `tables`, không phải file chunks RAG. F3 cấu trúc
đầy đủ ở [f3/records.jsonl](f3/records.jsonl); các trường `official_*`, tỷ lệ điểm và hình
thức thi chính thức vẫn null. Giữ metadata ngành/phiên bản và nhãn nguồn khi truy xuất.
Hàng đợi F1 hiện rỗng; trang nghề nghiệp trộn Toán Cơ đã bị loại khỏi phần bổ sung.
Không index toàn inventory. Các chunk `include_markdown` phải giữ nhãn chưa đối chiếu PDF/DOCX
gốc; hồ sơ duyệt không tự xác nhận chính xác bản gốc hoặc hiệu lực học vụ.

## Nguồn gốc và cập nhật

Các file dữ liệu được sao chép nguyên byte; `manifest.json` ở thư mục này ghi `origin`,
SHA-256 và kích thước của từng bản sao. Hai manifest riêng F1/F3 được giữ nguyên từ release
gốc. Chỉ dùng một bản dữ liệu khi index để tránh nạp lặp cả bản tại đây và bản trong `qa/`.

Đây là bản đóng gói dữ liệu trong repository, chưa phải archive nguồn độc lập: các trường
F1 `markdown_path`/`raw_path` vẫn tính từ `data/hus`, còn `review.evidence_locator` tính từ
repository root. Những nguồn đó vẫn tồn tại ở vị trí cũ. Blueprint F3 được đặt ở
`f3/inputs/blueprints.psv` để giữ đúng locator của hồ sơ F3.

Khi tái tạo hoặc cập nhật một phần, kiểm lại release gốc rồi đồng bộ bản sao và manifest
chung. Hướng dẫn tái tạo đầy đủ vẫn ở
[F1](../qa/20261028/f1_markdown_approved/README.md) và
[F3](../qa/20261028/f3_reference/README.md).
Các lệnh verify pipeline gốc áp dụng cho thư mục release gốc; thư mục bàn giao F3 ở đây
có thêm inputs nên kiểm các bản sao bằng manifest chung.

Thư mục này chưa được nạp vector index hoặc triển khai lên môi trường từ xa.
API local có thể đọc gói qua luồng trả lời được mô tả bên dưới; không tự nâng trạng thái
review hoặc `active_release` của dữ liệu.

## Đọc dữ liệu bằng Python

`app.hus.rag_loader.HUSRAGData` nạp một snapshot của gói này, kiểm đủ file/kích thước/
SHA-256 theo manifest trước khi sử dụng. Bộ nạp đọc F1/F3 từ `rag_chunks.jsonl`, không
nạp lặp `rag_documents.jsonl` hoặc bản release trong `qa/`. F2 được tra trực tiếp từ
các bảng nguồn, không chuyển thành chunks và không gọi mạng, LLM hoặc database.

```python
from app.hus.rag_loader import HUSRAGData

data = HUSRAGData.load_current()  # Ghim portable CURRENT, không fallback legacy.
f1 = data.chunks("f1", major="mathematics_informatics")
f3 = data.chunks("f3", major="data_science", version="QD3569-2023",
                 course_code="MAT3533", field="content", allow_generated=True)
course = data.get_f2_course("MAT3533", major="data_science", version="QD3569-2023")
if course is not None:
    print(course.course["credits"], course.review_status, course.source_rows)
```

Ngành phải dùng một trong `mathematics`, `mathematics_informatics`, `computer_science`,
`data_science`. Mọi truy vấn yêu cầu ngành; F2 còn bắt buộc phiên bản. Không tìm thấy
đúng mã–ngành–phiên bản thì F2 trả `None`, không lấy môn cùng mã ở ngành hoặc phiên bản
khác. Mã môn được bỏ khoảng trắng ngoài và chuyển thành chữ hoa. Mã chỉ dùng tham chiếu,
không thuộc chương trình, cũng không được trả như một membership.

Phiên bản F1 là `program_version` theo nguồn (ví dụ `2015`), F2/F3 là
`curriculum_version` (ví dụ `QD3569-2023`). Bộ nạp không tự đồng nhất hai hệ nhãn.
Nếu truyền phiên bản, chỉ khớp chính xác; các nguồn F1 `unknown` không được coi là
khớp mọi phiên bản. Khi không truyền phiên bản, caller có thể nhận nhiều phiên bản
và phải giữ nhãn riêng. F1 có thể lọc thêm `program_variant`, F3 lọc thêm `course_code`.

`RAGChunk.text` giữ nguyên nội dung; `RAGChunk.metadata` giữ tất cả trường JSON gốc
còn lại, gồm review, locator, quote/provenance và warning F3. Đối tượng có thêm
`package_path`/`package_sha256` để dẫn về file đã nạp. Kết quả F2 giữ course, curriculum,
membership, tất cả dòng/bản nhóm nguồn, tiên quyết theo `group_no`, metadata theo trường,
hồ sơ nguồn và pointer dòng JSON. `review_status` giữ trạng thái nguồn, chưa nâng thành
đã thẩm định; `unresolved_prerequisites` và `has_prerequisite_conflict` giữ vấn đề còn mở.
Đây là tra cứu dữ kiện, không phải tính eligibility hoặc xác nhận môn đang được mở.

Các kết quả trả về là bản sao độc lập để caller không sửa ngầm snapshot đã nạp.
Thiếu file, sai checksum hoặc identity/nhãn nguồn không nhất quán gây `RAGDataError`.
Checksum chứng minh tính toàn vẹn của gói, không chứng minh độ chính xác học vụ. Bộ nạp
không kiểm lại raw hoặc hồ sơ review bên ngoài gói, không chuyển `active_release` thành
true và không thay cổng review corpus/index cũ. Khi cập nhật nguồn/review, phải tái tạo
gói và gọi `load()` lại; đối tượng đang giữ không tự theo dõi thay đổi trên đĩa.

## Truy xuất tài liệu

`app.hus.retrieval.HUSRAGRetriever` tìm kiếm từ khóa có xếp hạng BM25 trên bộ nạp chung.
Chạy offline, hỗ trợ tiếng Việt có/không dấu và Unicode NFC/NFD, không cần API key hoặc
thư viện embedding. Ngành, phiên bản, mã môn, loại nội dung và hệ đào tạo được lọc
trước khi tính điểm và lấy top-k. Điểm chỉ so sánh trong cùng tập đã lọc.

```python
from app.hus.retrieval import HUSRAGRetriever

retriever = HUSRAGRetriever(data)  # data từ HUSRAGData.load() ở ví dụ trên.
# Hoặc HUSRAGRetriever.load() để đọc một snapshot mới của gói mặc định.
hits = retriever.search("học máy học những gì", dataset="f3", major="data_science",
                        version="QD3569-2023", course_code="MAT3533",
                        field="content", top_k=3, allow_generated=True)
for hit in hits:
    print(hit.score, hit.chunk.text, hit.chunk.metadata)

careers = retriever.search("cơ hội việc làm", dataset="f1",
                           major="mathematics_informatics", field="careers")
```

`dataset` phải là `f1` hoặc `f3`; ngành bắt buộc. Quy tắc phiên bản giữ nguyên như bộ
nạp: nếu truyền thì chỉ khớp chính xác, không truyền thì các phiên bản vẫn có nhãn riêng.
`top_k` nhận số nguyên từ 1 đến 50. Mã môn xuất hiện trong câu hỏi cũng là bộ lọc cứng:
`MAT3533` không được trả như một môn khác chỉ vì cùng chủ đề; mã không có trong phạm vi
đã chọn trả tập rỗng. F2 vẫn dùng `data.get_f2_course(...)` để tra dữ kiện cấu trúc.

Hệ thống xếp hạng theo nội dung nguồn, tên tài liệu/tên môn và nhãn loại nội dung.
Cảnh báo và context lặp đầu chunk F3 không được dùng như chủ đề để tính điểm, nhưng
`hit.chunk.text` và toàn bộ metadata vẫn giữ nguyên, gồm warning, review, quote,
locator/provenance và checksum. `hit.matched_terms` ghi các từ đã khớp sau chuẩn hóa.

Không quét thư mục hoặc đọc `origin` như một tập dữ liệu thứ hai: chỉ dùng F1/F3 chunks
được bộ nạp đọc từ gói đã chọn, không thêm bản ở `qa/`, `rag_documents.jsonl` hoặc file
ngoài manifest. Trong cùng phạm vi, các bản trùng nguyên văn cùng nguồn/loại nội dung
chỉ tính một lần; giữ một chunk đại diện và metadata của nó. Không gộp các môn, ngành,
phiên bản, hệ đào tạo hoặc URL nguồn khác nhau.

Không có từ khớp hoặc không có dữ liệu đúng bộ lọc thì trả tuple rỗng, không tự mở rộng
sang ngành/phiên bản khác. Đây là truy xuất từ khóa, chưa phải tìm kiếm ngữ nghĩa,
trả lời bằng LLM hoặc xác nhận nội dung đang có hiệu lực. Điểm cao không xác nhận một
câu trả lời đầy đủ; caller phải giữ citation và giới hạn nguồn khi tạo câu trả lời.

## Luồng trả lời và API

`app.hus.answering.HUSAnswerer` nối truy xuất vào câu trả lời trích xuất, không gọi LLM
để điền dữ kiện thiếu. API `POST /hus/chat` nhận câu hỏi cùng ngành, có thể chỉ rõ
dataset/phiên bản/mã môn/field/hệ. Ví dụ:

```json
{
  "question": "MAT3533 có bao nhiêu tín chỉ?",
  "major": "data_science",
  "version": "QD3569-2023"
}
```

Response gồm `reply`, `status`, `dataset`, `major`, `version`, `citations`, `facts`,
`warnings`, `release_id`, `release_sha256`, `generated_reference_allowed`.
Generated mặc định tắt ở loader/retriever và API. Với F3, gửi
`allow_generated_reference: true` hoặc bật checkbox kiến thức AI trong chat. Request
chưa bật không được tự thừa kế lựa chọn trước; đổi ngành/hồ sơ sẽ bỏ chọn checkbox.
`status` là `answered`, `no_information` hoặc `needs_clarification`, mô tả
khả năng trả lời câu hỏi, không phải trạng thái thẩm định học vụ. Mỗi citation giữ
quote, locator, URL nếu có, review status và metadata nguồn/checksum.

- F1: trích nguyên đoạn nguồn, ghi URL và phiên bản/hệ theo nguồn; nhắc giới hạn hiệu
  lực và việc chưa đối chiếu PDF/DOCX đối với `include_markdown`.
- F2: trả dữ kiện cấu trúc theo mã–ngành–phiên bản, kèm trạng thái review của nguồn,
  PDF/trang/hash và pointer JSON. `open_url` mở PDF qua resolver, URL bản chép giữ trong
  provenance. Giữ từng dòng tiên quyết riêng; báo mâu thuẫn
  hoặc mã chưa giải quyết kể cả khi mã chỉ nằm trong raw text. Không dùng chúng để
  xác nhận eligibility. Các field hỗ trợ: `credits`, `prerequisites`, `name`, `hours`,
  `course_info`. Null hoặc số tín chỉ thiếu/mâu thuẫn không được tự điền.
- F3: hiện cảnh báo và nhãn dẫn chứng `kiến thức AI`, giữ nhãn gốc trong metadata,
  `needs_review` và
  `academic_verified=false`. URL nguồn F2 không được trình bày như đề cương F3 chính thức.

F2 cần mã môn và phiên bản; F3 cần mã môn. Thiếu định danh thì phản hồi yêu cầu bổ sung
trong `reply`, không tự chọn môn/phiên bản. Câu hỏi ngoài trường hỗ trợ, sai phạm vi,
không đủ từ khớp cụ thể, hiệu lực hiện hành hoặc thông tin chính thức chưa được xác minh
trả `no_information`, không tạo citation giả. Tỷ lệ điểm/hình thức thi chính thức không
được suy ra từ gợi ý F3. Bộ định tuyến từ khóa chỉ hỗ trợ các ý định thông tin rõ ràng;
không tự phân tích câu hỏi so sánh nhiều ngành hoặc nhiều mã môn thành một câu trả lời.

Khung chat hiện có vẫn gọi `POST /advisor/chat`: câu hỏi HUS được chuyển qua nhánh
`mode: hus_rag`, thêm `hus_answer` có cùng cấu trúc trên. Ngành/phiên bản F2 được lấy từ
đúng chương trình đã chọn; F1 không bị gán phiên bản quyết định F2. Câu hỏi khuyến nghị
tiếp tục đi qua advisor/eligibility cũ. Giao diện hiển thị reply, các link citation HTTP(S),
giữ nhãn F3, xóa ngữ cảnh khi đổi ngành/hồ sơ và bỏ phản hồi chat thuộc ngữ cảnh cũ.

Service nạp gói lazy và cache snapshot trong tiến trình. Sau khi tái tạo gói cần restart
server hoặc gọi `get_hus_answerer.cache_clear()` qua code quản trị; không có endpoint
reload công khai. Thiếu/sai checksum dữ liệu là HTTP 503, không được che thành câu trả
lời “chưa có thông tin”. Request sai schema là HTTP 422. Luồng này không gọi database
sản phẩm hoặc provider cho câu hỏi HUS, không thay cổng review raw/index cũ và không tự
chứng nhận hiệu lực học vụ. Đã nghiệm thu local 2.310 ca HTTP và 25 ca Chromium thực,
giao diện dùng fixture và HUS dùng gói thật; chưa nghiệm thu DB sản phẩm hoặc triển khai
remote. Chi tiết và lệnh chạy lại ở [biên bản đầu cuối](../../../docs/HUS_E2E_ACCEPTANCE.md).
