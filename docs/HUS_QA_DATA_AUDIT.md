# Kiểm kê và lọc dữ liệu hỏi đáp F1–F3 — 2026-10-28

**Vị trí quản lý chung hiện tại: [data/hus/rag/](../data/hus/rag/README.md)**, chia thành
`f1/`, `f2/`, `f3/`. Các release trong `qa/` phía dưới là nguồn gốc để tái tạo; thư mục
chung giữ bản sao nguyên byte, nhãn review/generated và manifest đối chiếu.

## Quyết định mới: duyệt 10 nguồn F1 trên Markdown

Theo yêu cầu trực tiếp của người dùng, đã loại trang nghề nghiệp trộn Toán Cơ và duyệt
24 phần F1 trong 10 tài liệu đính kèm trên chính bản Markdown đã crawl. F1 hiện có
**15 nguồn / 69 chunks**, hàng đợi rỗng. Năm nguồn trước đã đối chiếu HTML; mười nguồn
bổ sung ghi `include_markdown`, `raw_original_verified=false`, scope mô tả và giữ riêng
năm/hệ. Không giả xác nhận đã kiểm PDF/DOCX hoặc thay review gate chung. Tập hiện tại ở
`data/hus/rag/f1/`; cách tái tạo và bằng chứng tại
[F1 duyệt Markdown](../data/hus/qa/20261028/f1_markdown_approved/README.md).
Các thống kê 5 nguồn/42 chunks và 27 đoạn chờ dưới đây thuộc release lịch sử.

## F1 mở rộng từ dữ liệu crawl

Đã rà lại đủ 106 nguồn theo F1 chương trình: **5 nguồn / 42 đoạn RAG nguyên văn**, gồm
bài CLC mới qua đối chiếu và các đơn vị giới thiệu/mục tiêu/nghề nghiệp/học tiếp từ bốn
bài cũ. Không sinh thêm F1 hoặc lấy mục tiêu từng học phần F3 làm mục tiêu chương trình.
42 đoạn không phải 42 nguồn; corpus cũ 4 nguồn/8 chunks được giữ làm artifact lịch sử.
Có 27 đoạn ứng viên thuộc 11 nguồn còn chờ raw/whole-document scope review, không vào
tập trả lời. Dữ liệu dùng hiện tại và giới hạn tại
[hướng dẫn F1 mở rộng](../data/hus/qa/20261028/f1_expanded/README.md).
Nghiệm thu F1 hiện tại: 8 test mới đạt, toàn repo **526 passed, 26 skipped**, Ruff/diff
đạt; tám file release tái tạo byte-identical. Các số lượng 4 nguồn/8 chunks, 501 hoặc
518 test ở các phần lịch sử bên dưới không mô tả bản F1 mở rộng mới này.

## Bổ sung F3 tham khảo theo yêu cầu mới

Đã tạo bộ F3 AI sinh đầy đủ cho **290 cặp môn–ngành / 174 mã môn**, từ F2 main được ghim:
90 Toán học, 68 Toán tin, 67 KH máy tính và thông tin, 65 KHDL. Mỗi hồ sơ có nội dung,
mục tiêu và gợi ý đánh giá; xuất **870 chunks RAG** trong collection dữ liệu riêng.
Phác thảo gồm 154 chủ đề môn học, không nhân bản một mô tả rỗng cho mọi môn.
Các trường F3 chính thức/tỷ lệ điểm vẫn null, không đổi review gate hoặc corpus F1 đã duyệt.
Đây là bước sau ba ví dụ thử nghiệm ban đầu được mô tả trong báo cáo phía dưới.
Nguồn, schema, cách dùng RAG và lệnh tái tạo tại
[hướng dẫn bộ F3 đầy đủ](../data/hus/qa/20261028/f3_reference/README.md).
Nghiệm thu F3 bổ sung: 17 test mới đạt; toàn repo **518 passed, 26 skipped**, Ruff/diff
đạt, bảy file release tái tạo byte-identical. 16 câu hỏi contract đạt; chưa chạy vector
index/LLM hoặc xác minh F3 học vụ chính thức. Các số 501 test và ba ví dụ bên dưới là
bằng chứng lịch sử của bước kiểm kê trước khi yêu cầu sinh đầy đủ F3.

## Đính chính sau đối chiếu nhánh main

Kiểm tra trực tiếp GitHub xác nhận `main` mới nhất ở commit
`cfb2ec4c7f3f8e80428abc3db535dad0cc5db41d` **đã có F2 cho đủ bốn ngành** tại
`database/data/hus_source.json`, cùng SQL `database/sql/10_official_curricula_2023.sql`,
builder `database/hus_db/catalog_builder.py` và năm PDF trong `docs/pdf/`.
Kết luận trước đó rằng chỉ có mẫu KHDL/thiếu PDF chỉ đúng với snapshot local `crawldata`,
không đúng cho toàn repository trên các nhánh. Đã bỏ sót main trong lượt kiểm kê đầu.

| Ngành | Phiên bản / khóa | Mã môn riêng trong ngành | Dòng nguồn (có lặp theo nhóm) |
| --- | --- | ---: | ---: |
| Toán học | QD3565-2023 / 2022 | 90 | 96 |
| Toán tin | QD3567-2023 / 2022 | 68 | 69 |
| KH máy tính và thông tin | QD3568-2023 / 2022 | 67 | 67 |
| Khoa học dữ liệu | QD3569-2023 / 2022 | 65 | 65 |
| Tổng | Bốn chương trình | 290 membership | 297 |

Đã tự kiểm tra JSON trên main: cả 297 dòng có mã/tín chỉ và locator PDF/trang; mọi dòng
tham chiếu được tên môn và membership; mọi membership có dòng nguồn. Có 42 nhóm và
348 option tiên quyết với `group_no`, raw riêng và trạng thái parse. Đây là nguồn F2
cần ưu tiên tái sử dụng, không cần crawl lại chỉ vì ba thư mục catalog vắng ở crawldata.

Nguồn main vẫn giữ `draft_unverified`. Hồ sơ đối chiếu tiên quyết và mã/trang đã có,
nhưng không đồng nghĩa mọi ô/hiệu lực đã được xác minh; còn `MAT3402` chưa có định nghĩa,
`MAT3325` có điều kiện xung đột. Đọc báo cáo nghiệm thu cũ không thay cho chạy lại test/PDF.
PDF được xác nhận hiện diện từ Git tree, chưa tải binary hoặc đối chiếu lại ảnh trong lượt này.
Chi tiết commit/blob, pointer 297 dòng và kiểm tra thực chạy:
[`main_f2_comparison.json`](../data/hus/qa/20261028/main_f2_comparison.json).

Ma trận và thống kê `audit/` dưới đây vẫn là artifact bất biến của snapshot local đã ghim,
chưa nhập bundle main hoặc đưa F2 vào corpus trả lời. Không dùng số thiếu nguồn của
snapshot đó làm kết luận thiếu F2 toàn dự án. Chưa merge/chuyển nhánh hay publish database.

Phạm vi nghiệm thu là chuẩn bị dữ liệu offline, không phải hoàn thiện chatbot, retrieval,
LLM, giao diện hay database. Checkout khi bắt đầu: nhánh `crawldata`, HEAD `38a5ddb`.
Ba tệp có sẵn chưa được Git theo dõi (`docs/HUS_MANUAL_TEST.md` và hai raw HTML
`diagnostic-*`) được giữ nguyên, không đưa vào nguồn của lần kiểm kê này.

## Kết quả có thể sử dụng

| Ngành | F1: giới thiệu / mục tiêu / nghề nghiệp | F2 | F3 chính thức |
| --- | --- | --- | --- |
| Toán học | Đủ nguồn mô tả đã đối chiếu, phiên bản/hiệu lực unknown | Có các chương trình 2015 hệ chuẩn/tài năng, tiên tiến 2008; chưa đủ điều kiện trả lời | Có đoạn tóm tắt trong chương trình, chưa ánh xạ đủ từng môn/trường, chưa duyệt |
| Toán tin | Đủ nguồn mô tả đã đối chiếu, phiên bản/hiệu lực unknown | Có bảng chương trình 2015; đề cương 2021; scan mới chưa đọc/kiểm tra được | Trích được 62 mục có mã học phần trong đề cương 2021, thiếu raw/review |
| Khoa học máy tính và thông tin | Đủ nguồn mô tả đã đối chiếu, phiên bản/hiệu lực unknown | Có 2015, CLC bìa 2019 và bản khác chưa rõ năm, DOCX 2023; còn mâu thuẫn | Có 44 mục trong bộ đề cương ban hành 2024, chưa xác minh đầy đủ bậc/phiên bản/phạm vi từng môn, thiếu raw/review |
| Khoa học dữ liệu | Đủ nguồn mô tả đã đối chiếu, phiên bản/hiệu lực unknown | Có 65 học phần mẫu 2022, toàn bộ `draft_unverified` | Chưa có đề cương riêng đủ bằng chứng cho chương trình 2022; có 3 mẫu suy luận tách riêng |

“Đủ F1” chỉ cho phép thuật lại nội dung bài giới thiệu đã lưu, kèm URL và giới hạn;
không xác nhận chương trình đang có hiệu lực năm 2026, áp dụng cho khóa nào hoặc đang mở môn.
Ngày bắt đầu đào tạo, năm quyết định mở ngành và năm trong link không được tự coi là phiên bản.
Tên ngành trong bài là tên nguồn; không tự đồng nhất các mã ngành/chương trình khác nhau.

Tập trả lời đã xuất: **4 tài liệu, 8 chunks**, mỗi ngành một bài giới thiệu.
Tập này ở `data/hus/qa/20261028/audit/answer_{documents,chunks,source_map}.jsonl`;
bốn bản `normalized/*.md` đi kèm để giải ngược locator. Đây là corpus ứng viên,
`active_release: false`, chưa được nạp vào index hoặc hệ thống đang chạy.

Review mới được ghi minh bạch là **Codex đối chiếu tự động extraction và đọc toàn bộ nội dung**,
không phải reviewer của HUS hoặc phê duyệt học vụ. Cả bốn HTML đều khớp hash nội dung catalog,
không có bảng/trang PDF phải duyệt. Review áp dụng toàn tài liệu, scope `descriptive`,
validity/effective dates vẫn unknown/null. Chỉ ngành và bậc đại học được ghi verified với
quote/locator/reviewer/time cụ thể trong contract mới. Không nới cổng trang/ô bảng hoặc xuất
một phần của tài liệu chưa duyệt. Các link trong bài chỉ dẫn tới nguồn khác, không xác nhận
nội dung các trang đích. Đề cập khả năng học tiếp thạc sĩ/tiến sĩ là thông tin sau tốt nghiệp
của cử nhân, không phải đưa chương trình sau đại học vào tập trả lời.

## Vì sao có báo cáo 0 và thông tin “30 chunks”?

Baseline Git ở `data/hus/corpus/` dùng snapshot `hus-0404f37-20261026`, nguồn cố định:
`0404f37c1b6c3864b7fe2e9938a8a21f777663f0:data/hus`.
Baseline có **100 needs_review, 6 pending_ocr, 0 include, 0 chunks**. Đã kiểm tra catalog,
contract, baseline build manifest, Git log và các build local dưới `backups/rag_preparation/`.
Cả bảy `validation_report.json` local tìm thấy đều ghi 0 include/chunks. Không tìm thấy
artifact sản phẩm chứa 30 chunks hoặc contract review của build07 trong checkout/backups
hiện có; index JSON duy nhất tìm thấy trong backups là fixture tổng hợp của runbook.

Tài liệu lịch sử `HUS_CORPUS_PREPARATION.md` nhắc build07 và sáu trang từng được chọn,
nhưng không có hồ sơ/hash/snapshot đủ để nhập lại quyết định đó. Vì vậy **không xác minh
được tuyên bố “30 chunks đã review”**, cũng không thể gán nó vào commit hiện tại.
Con số 0 của baseline là đúng với contract cũ. Con số **8** của lần này thuộc contract
mới tại `qa/20261028/contract`, build ID nằm trong `audit/report.json`; đây là lần
đối chiếu riêng có hồ sơ, không phải phục dựng hay đổi tên 30 chunks cũ.

## Nguồn F2 thực sự tìm được

1. `data/curricula/khdl_7460108_2022/{courses,curriculum,source_rows}.json`:
   65 mã, tên, tín chỉ, khối, nhóm tự chọn, nhánh tốt nghiệp, biểu thức tiên quyết,
   source page/row và field evidence. `catalog_revision=khdl_2022_metadata_sample_v1`.
   Loader ở `app/catalog.py`, hợp đồng metadata/validator ở `app/catalog_validation.py`,
   builder ở `tools/build_catalogs.py`. Đây là bản chép chưa đối soát PDF, không phải
   nguồn đã duyệt. Cả 65 tên/mã/tín chỉ khớp `source_rows`; việc khớp hai bản chép
   không xác minh PDF. `source_issues` và tham chiếu tiên quyết ngoài catalog được giữ nguyên.
2. Các Markdown của snapshot HUS, dẫn bằng document ID trong manifest:

| ID | Nội dung / phiên bản đề xuất | Số dòng F2 trích được |
| --- | --- | ---: |
| `23a0c1df14a5708a` | Toán tin ứng dụng, bìa 2015 | 54 |
| `89d4b39494d72217` | Toán học chuẩn, bìa 2015 | 71 |
| `1e3ad5f9915aa051` | Máy tính và khoa học thông tin, bìa 2015 | 56 |
| `1c16ddf8a6f1f409` | CLC, bìa 2019, khác năm trong tên tệp | 66 |
| `8afffd3cada3d048` | CLC, chưa xác định năm từ bìa | 130 |
| `f7f470e712738589` | KH máy tính và thông tin, bìa 2023 | 266 |

Tổng **643 dòng ứng viên**, gồm nhiều dòng lặp ở bảng chương trình, tài liệu tham khảo,
nhân sự giảng dạy và các bảng so sánh. Không diễn giải thành 643 môn hoặc cộng với mẫu
65 môn thành danh mục chuẩn. `f2_course_checks.jsonl` liệt kê số lần xuất hiện, các tên,
tín chỉ và mâu thuẫn theo document/mã. Hai mã `MAT1206E`, `MAT2034` trong DOCX 2023
có cả giá trị 3 và 4 tín chỉ; chưa chọn giá trị nào là đúng. Ma trận CĐR/Bloom không được
đọc như cột tín chỉ; bảng so sánh hai chương trình không tự hợp nhất thành một danh mục.

Các nguồn bổ trợ vẫn được giữ trong manifest/hàng đợi: Toán tài năng 2015
`d4fae066858f0b94` có header xoay bị lỗi; tiên tiến 2008 `d006f60211246633` có layout
so sánh và mã tách dòng; bản đồ `c6e4ea5514b8c3f4`, các ma trận CĐR và sáu scan chưa OCR.
Chưa ánh xạ tự động được bảng thì ghi rõ `F2_table_not_mapped`, không đoán tín chỉ.
Không dùng fixtures dưới `tests/fixtures/catalogs` làm nguồn học vụ; không khôi phục ba
catalog sản phẩm đã bị gỡ, không đọc/seed database để lấp chỗ thiếu.

Quan hệ tiên quyết/học trước/song hành: giữ nguyên dòng/header và biểu thức đã chép;
`relation_types_verified: false`, `prerequisite_answer_status`/interpretation = unknown.
Ô trống, `[]` hoặc raw null không được biến thành kết luận “không có tiên quyết”. Không
chuyển sơ đồ học kỳ hoặc tên môn thành quan hệ AND/OR đã xác minh.

## F3 có nguồn và F3 suy luận

`audit/f3_source_fields.jsonl` ghi 106 mục có marker mã học phần, bao gồm 62 mục Toán tin
2021 và 44 mục trong bộ đề cương KH máy tính. Đây là **đã trích xuất**, chưa phải đề cương
được duyệt: raw thiếu, chưa đối chiếu trang/bảng, có mã `2502` thiếu tiền tố và `MAT1202`
lặp trong bộ KH máy tính. Không tự sửa mã hoặc ghép hai môn. Bộ này có phần nhắc KHDL
và Toán học, nhưng chưa đủ để chuyển toàn bộ nội dung sang các ngành đó.

`f3_course_coverage.jsonl` kiểm riêng content/objectives/assessment cho từng mục đề cương,
từng mã ở bảng F2 và 65 môn mẫu KHDL. Marker tiêu đề chỉ chứng minh có chỗ cần kiểm,
không chứng minh nội dung đầy đủ. Không ánh xạ được trường thì báo rõ; không kết luận
nguồn gốc thực sự không chứa trường đó. Chưa có mẫu số danh mục chuẩn đã duyệt nên
không tính phần trăm bao phủ đầy đủ của bất kỳ ngành/phiên bản nào.

Sau khi tìm nguồn thật và thử tải, tạo **3 ví dụ suy luận** KHDL 2022: `MAT3507`, `MAT3533`,
`MAT3386`, tại `experimental/f3_inferred.json`. Mỗi ví dụ truy về pointer/hash/revision,
tên/tín chỉ/tiên quyết raw của F2; mô tả phương pháp `codex_conservative_title_inference_v1`.
Chỉ có `inferred_content` và `inferred_objectives`; mọi trường `official_*`, assessment và
suggested_assessment là null. Reviewer null, verified false, không có API/provider gọi ngoài.
`experimental_coverage.jsonl` dùng trạng thái `generated_only`, nằm riêng với ma trận nguồn
chính thức; không nâng độ bao phủ chính thức. Không sinh 65 mô tả lặp để giả hoàn thành.

## Bổ sung nguồn có mục tiêu và blocker

Đã ưu tiên bốn đích Toán tin/KHDL (đề cương Toán tin 2021, scan khung Toán tin, scan
khung KHDL và trang khám phá KHDL), cộng đề cương KH máy tính để kiểm tra nội dung
có nhắc KHDL. URL đầy đủ/gap/ID nằm trong `targets.json`; giữ cấu hình hẹp riêng ở
`data/hus/config/qa_sources.json`, không tiếp tục dùng seed tuyển sinh/sau đại học rộng.

Hai lần chạy thật ở `acquisition/` và `acquisition02/` đều không lấy được nguồn mới.
Lần thứ hai ghi request kiểm tra `https://mim.hus.vnu.edu.vn/robots.txt` và bản HTTP,
đều **không có HTTP response**. Policy hiện có fail-closed nên cả năm target bị chặn
trước khi gửi GET tài liệu. Đây là không truy cập được robots, **không phải đã đọc được
quy tắc robots cấm từng URL hoặc server trả 404 tài liệu**. Không bỏ qua robots.
Tra cứu web chính thức cũng không trả kết quả/tải được hai trang ưu tiên trong lượt này.
Raw/provenance ledger của các lần thử được giữ; không có byte nguồn mới để xác minh.

Nguồn đã bổ sung cho Toán tin/KHDL trong bàn giao này là hồ sơ đối chiếu hai HTML
đang có và corpus F1 từ chúng; **không bổ sung được PDF/đề cương chính thức mới**.
Snapshot cũ vẫn thiếu 51 attachment gốc; báo cáo recovery cũ có hai candidate local,
không được tự chèn vào snapshot hoặc coi là phiên bản gốc đã duyệt.

## Artifact và cách chạy lại

Tất cả dữ liệu bàn giao ở `data/hus/qa/20261028/`:

- `contract/`: config mới, đủ 106 review/metadata, source comparisons cho bốn bài;
  vẫn tham chiếu manifest nguồn cũ, không sửa baseline hoặc catalog/raw/Markdown gốc.
- `audit/classification.jsonl`: 106 bản ghi kèm lý do, nội dung/locator, raw, ngành/bậc/năm
  đề xuất tách khỏi verified, quality flags và trạng thái xuất. 79 exclude, 11 quarantine,
  16 retain_candidate; trong số giữ lại có 4 answer_eligible. Không xóa raw.
- `coverage.jsonl`, `f3_course_coverage.jsonl`: ngành × phiên bản × biến thể × F1–F3 × trường,
  và chi tiết từng môn. Năm/biến thể đề xuất không được coi là khóa áp dụng đã xác minh.
- `source_gaps.jsonl`, `extraction_issues.jsonl`: ưu tiên 1 Toán tin/KHDL, ưu tiên 2 ngành khác;
  blocker raw/OCR/phạm vi/mã/bảng và việc cần đối chiếu. Kết quả tải nằm ở acquisition02.
- `f2_catalog_records.jsonl`, `f2_source_rows.jsonl`, `f2_course_checks.jsonl`,
  `f3_source_fields.jsonl`: bản kiểm kê, không phải tập trả lời.
- `acceptance_questions.jsonl`: 12 câu hỏi tiếng Việt, mỗi ngành đủ F1/F2/F3, căn cứ,
  phần được trả lời/phải báo thiếu, nhãn nguồn, kết quả kiểm tra contract offline.
  Đây không phải đánh giá chất lượng câu trả lời của chatbot/LLM.
- `answer_*.jsonl`, `normalized/`: dữ liệu được lọc qua cổng duyệt, nguồn và locator;
  `report.json` ghim hash mã/đầu vào/đầu ra và ID build corpus được tái tạo.

Chạy ở repository root, với Python/dependency sẵn có (không cần API key/database):

```powershell
python -X utf8 -m tools.audit_hus_scope verify --out data/hus/qa/20261028/audit
python -X utf8 -m tools.audit_hus_scope build --out backups/rag_preparation/qa-new01
python -X utf8 -m tools.audit_hus_scope verify --out backups/rag_preparation/qa-new01
python -m pytest -q tests/hus/test_scope_audit.py
python -m ruff check .
```

Build từ chối ghi đè và bảo vệ raw/processed/catalog/contract. Verify dựng lại qua
`build_artifacts()`/`require_review()` hiện có rồi đối chiếu mọi byte/tên file.
Lệnh mạng tùy chọn, chỉ chạy khi cần thử lại đúng danh sách thiếu, luôn chọn thư mục mới:

```powershell
python -X utf8 -m tools.fetch_hus_gaps --out backups/rag_preparation/qa-acquisition-new01
```

Sau khi lấy được nguồn mới, phải tạo snapshot/manifest/review mới theo
[quy trình corpus](HUS_CORPUS_PREPARATION.md); acquisition không tự cấp include hoặc cập nhật
contract đang ghim. Không tự merge/push; không có thay đổi runtime trả lời trong nhiệm vụ này.

## Kiểm chứng thực chạy trong lượt này

- `python -m pytest -q`: **501 passed, 26 skipped**, 1 cảnh báo deprecation sẵn có của
  FastAPI/Starlette test client; không lỗi test. Các kiểm tra PostgreSQL/full-source cần
  cấu hình/nguồn bên ngoài chưa được chạy. Không dùng kết quả CI hoặc báo cáo cũ thay thế.
- 19 test mới cho phân bậc, news/lab, version/variant, mixed scope, marker/locator từng môn,
  không đọc điểm CĐR thành tín chỉ, giữ unknown prerequisite, mã thiếu/suffix, nguồn sinh
  giả verified/stale input và robots lỗi fail-closed đều nằm trong lần chạy trên.
- Ruff toàn repo, `git diff --check`, builder check mẫu KHDL 65 môn/59 dòng đánh số: đạt.
- Audit versioned dựng lại qua gate chuẩn và verify đúng toàn bộ **19 file**; hash của
  18 output nằm trong `audit/report.json`, bản thân report được kiểm bằng build lại.
- 12 câu hỏi contract: 12 pass; bốn F1 đủ dữ liệu mô tả, tám F2/F3 phải thông báo chưa đủ
  nguồn đã duyệt. Không tuyên bố đã kiểm thử retrieval, browser hoặc provider LLM.
- Không thêm dependency, không sửa catalog/raw/Markdown nguồn, không merge/commit/push.
