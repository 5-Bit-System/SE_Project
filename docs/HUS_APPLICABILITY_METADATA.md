# Phạm vi và metadata áp dụng của nguồn HUS

P1 ngày 2026-10-26: phân biệt đề xuất tự động với giá trị đã xác minh, giữ unknown riêng với
general và chặn hai trang ngoài bốn ngành. Chỉ áp dụng cho `app/hus`; không thêm ngành vào
catalog học phần, không thay eligibility hoặc dữ liệu sinh viên.

## 1. Ba phạm vi khác nhau

- `unknown`: chưa đủ căn cứ xác định phạm vi. Không được tự coi là tài liệu dùng chung.
- `general`: có tín hiệu đề xuất phạm vi chung rõ ràng, như áp dụng cho tất cả sinh viên toàn
  trường/khoa hoặc tiêu đề nói rõ nhiều ngành. Đây vẫn chỉ là đề xuất đến khi có review.
- `out_of_scope`: đề xuất ngoài bốn ngành hiện hỗ trợ, dùng để giữ bằng chứng/phát hiện nguồn;
  không được xuất vào corpus/index trả lời của bốn ngành.

`infer_major()` không chuyển None thành general nữa. Tín hiệu URL chỉ xét path, không xét query
hay tên host. Lead phân loại bỏ dòng Markdown link/menu và bảng; không dùng mọi từ xuất hiện
trong nội dung chung để suy ngành. URL/tiêu đề của hai chương trình Địa chất, Địa lý được nhận
diện trước tín hiệu Toán trong menu/nội dung phụ. Source Markdown/raw được giữ nguyên để audit,
không xóa nội dung trong bản nguồn chỉ để làm cho bộ phân loại cho kết quả mong muốn.

## 2. Model và bằng chứng theo từng trường

`ApplicabilityMetadata` trong `app/hus/models.py` có các trường:
`major`, `education_level`, `program`, `program_variant`, `admission_cohort`, `academic_year`,
`validity_status`, `effective_from`, `effective_to`. Mỗi trường là `MetadataField` độc lập:

| Thuộc tính | Ý nghĩa |
| --- | --- |
| `proposed` | Nhãn/giá trị đề xuất hoặc unknown. |
| `proposal_method`, `proposal_evidence` | Quy tắc/tín hiệu dùng đề xuất; không phải review. |
| `verified` | Giá trị đã xác minh hoặc unknown; không fallback từ proposed. |
| `evidence` | Locator thực trong nguồn hỗ trợ giá trị được xác minh. |
| `reviewer`, `reviewed_at` | Người chịu trách nhiệm và timestamp ISO có múi giờ. |

Mọi giá trị verified khác unknown bắt buộc có evidence, reviewer không rỗng và reviewed_at có
múi giờ. Locator có `field`, `start`, `end`, `quote`: trường nguồn title/source_url/content_markdown
hoặc parent_url, offset ký tự `[start,end)` và đoạn trích phải khớp đúng, nằm trong nguồn.
Metadata còn gắn URL và content_hash để không tái dùng bằng chứng cho nguồn khác/đã thay đổi.
Quote rỗng hoặc chỉ khoảng trắng bị từ chối. Riêng parent_url không đủ để xác minh metadata
của tệp đính kèm; chỉ được dùng làm tín hiệu đề xuất kế thừa.

Đề xuất tự động chỉ nhận các tín hiệu rõ: quy tắc ngành, bậc học nói trong tiêu đề, khóa hoặc
năm học có câu chỉ định trong tiêu đề. Nếu nhiều bậc học cùng được nêu, giữ unknown để review,
không chọn bậc đầu tiên. Không suy năm học/khóa/hiệu lực từ fetched_at hoặc một năm bất kỳ
trong tên URL. Program/variant và hiệu lực thiếu căn cứ giữ unknown; không tự điền cho đủ schema.

Khi cập nhật proposal, giá trị verified chỉ được giữ nếu còn khớp nguồn/locator hiện tại.
Title thay đổi cũng phải xây lại metadata, kể cả body hash không đổi, vì title có thể là bằng
chứng. Gate kiểm tra ngày review metadata không sau as_of nếu build có ngày này. Metadata hiệu
lực đã xác minh phải nhất quán với hiệu lực trong ReviewDecision khi xuất corpus/index.
Kiểm tra contract không tự chứng minh reviewer đúng về nội dung học vụ hoặc còn hiệu lực.

## 3. Lớp bổ sung cho snapshot đã ghim

`data/hus/corpus/applicability.json` là lớp metadata versioned cho đủ 106 document ID của snapshot
0404f37. Không sửa source catalog, Markdown/raw, source_manifest hoặc các quyết định review cũ.
Nhãn mathematics trong catalog nguồn của hai trang được giữ như bằng chứng lịch sử về crawler;
không được dùng như kết quả áp dụng đã xác minh. Corpus/index xử lý metadata bổ sung trước khi
xuất, nên không cần viết lại nguồn chỉ để sửa nhãn hoặc phá tính tái lập snapshot.

| Document ID | Đề xuất mới | Verified | Xử lý |
| --- | --- | --- | --- |
| `d73edbb5ad3fc8e5` | out_of_scope | unknown | Giữ source, chặn xuất trả lời bốn ngành. |
| `741abe805f966790` | out_of_scope | unknown | Giữ source, chặn xuất trả lời bốn ngành. |

Phân bố proposal hiện tại: Toán học 25, Khoa học dữ liệu 4, Khoa học máy tính 12, Toán–Tin 10,
unknown 53, out_of_scope 2. Chưa có nguồn nào được xác minh ngành; tất cả verified major là
unknown. Con số 53 unknown phản ánh thiếu căn cứ phân loại, không phải 53 nguồn đã bị loại.

`BuildConfig.applicability_metadata` chọn file bổ sung, tương đối với config. Snapshot ID và tập
ID phải khớp hoàn toàn; hash/locator sai làm build fail. Khi dùng API Python, truyền ApplicabilityFile
làm đối số thứ năm của build_artifacts. Nếu config khai báo file mà caller không truyền lớp bổ
sung, API báo lỗi để tránh bỏ qua curation. Chỉ khi config không khai báo file, API mới dùng
metadata có trên document hoặc tính proposal bảo thủ; không tự đọc một file khác.

## 4. Dựng lại và review

```powershell
python -X utf8 -m tools.propose_hus_metadata --source-root data/hus --manifest data/hus/corpus/source_manifest.json --out backups/rag_preparation/NEW_APPLICABILITY.json
python -X utf8 -m tools.prepare_hus_corpus build --out backups/rag_preparation/NEW_METADATA_BUILD
python -X utf8 -m tools.prepare_hus_corpus verify --out backups/rag_preparation/NEW_METADATA_BUILD
```

Lệnh proposal chỉ đọc nguồn đã ghim và ghi file mới, từ chối ghi đè. Không đánh dấu verified.
Để đưa đề xuất mới vào build, review/cập nhật bản metadata versioned hoặc đặt đường dẫn metadata
trong một bản config mới. Không thay hồ sơ đã review bằng output proposal mới một cách mù quáng;
khi làm trên source có metadata được duyệt, tool giữ trường verified còn khớp nguồn.

Reviewer đối chiếu từng giá trị với source, điền verified/evidence/reviewer/reviewed_at; nếu thiếu
bằng chứng tiếp tục giữ unknown. Không được dùng proposal_evidence hoặc parent label như một
quyết định review. Ví dụ bằng chứng bậc học không đồng thời chứng minh điều kiện dự tuyển hoặc
khóa áp dụng; các trường này có hồ sơ riêng. Nguồn hiện thiếu raw vẫn phải qua cổng review raw
trước khi có thể được dùng trả lời, kể cả đã có một số metadata được xác minh từ title/text.

## 5. Contract đầu ra và nghiệm thu

Corpus/index xuất `major` từ verified; đề xuất có trường riêng `proposed_major`. Corpus giữ
`legacy_crawler_major` để audit và `applicability` đầy đủ; index cũng giữ legacy/proposed riêng.
Chunk có ApplicabilityMetadata. Không dùng legacy major hoặc proposed major để mở rộng phạm vi
câu trả lời, lọc theo ngành như thể đã xác minh hoặc unlock học phần. Các nhãn document_type/
published_at legacy khác chưa có nghiệm thu độc lập chỉ vì metadata áp dụng được bổ sung.

Nguồn có proposal/verified out_of_scope hoặc URL nhận diện ngoài bốn ngành bị chặn tại cùng
require_review cho corpus/chunk/index, kể cả có quyết định include. Unknown không tự chuyển
sang general. Scope chưa xác minh vẫn cần được giới hạn khi thiết kế retrieval/answering;
P1 này không xây retriever, không thêm bộ lọc API trả lời hiện hành.

Pipeline corpus 1.3 thêm artifact applicability.json và hash riêng trong build ID; build mới
có 117 artifact, dùng cùng snapshot nguồn và giữ 100 needs_review + 6 pending_ocr, 0 include.
Build 1.2 cũ giữ nguyên trong backups/Git; cần code/config của phiên bản cũ để verify chúng.

```powershell
python -m pytest -q tests/hus/test_applicability.py
```

Kiểm thử gồm hai trang ngoài phạm vi và menu gây nhiễu, query URL, unknown/general, thiếu reviewer/
timestamp/evidence, locator sai/vượt nguồn, hash/URL sai, vocabulary, review tương lai, kế thừa
parent không tự verified, giữ review còn khớp nguồn và baseline bổ sung không sửa source.
