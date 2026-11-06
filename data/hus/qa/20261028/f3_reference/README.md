# F3 tham khảo đầy đủ cho bốn ngành — 2026-10-28

Tập này phục vụ **RAG thử nghiệm với nội dung AI sinh**, theo yêu cầu của người dùng.
Mỗi bản ghi có nội dung, mục tiêu học tập và gợi ý đánh giá. Đây không phải đề cương
chính thức, xác nhận học vụ hoặc dữ liệu được thêm vào corpus nguồn đã duyệt.

| Chương trình | Phiên bản F2 / khóa khai báo | Hồ sơ F3 | Chunks |
| --- | --- | ---: | ---: |
| Toán học | QD3565-2023 / 2022 | 90 | 270 |
| Toán tin | QD3567-2023 / 2022 | 68 | 204 |
| KH máy tính và thông tin | QD3568-2023 / 2022 | 67 | 201 |
| Khoa học dữ liệu | QD3569-2023 / 2022 | 65 | 195 |
| Tổng | Bốn chương trình | **290** | **870** |

290 là số cặp môn–ngành; có 174 mã môn trong bốn chương trình. Năm mã chỉ dùng tham chiếu
từ chương trình Toán tài năng không được sinh hồ sơ. 297 dòng nguồn F2 có lặp theo nhóm
được giữ ở provenance; không sinh thêm hồ sơ trùng từ những dòng đó.

## Nguồn và phương pháp sinh

- `inputs/hus_source.json`: bản sao nguyên nội dung nguồn F2 trên main tại commit
  `cfb2ec4c7f3f8e80428abc3db535dad0cc5db41d`, đường dẫn gốc
  `database/data/hus_source.json`. Git blob SHA-1 là
  `79dd58bc54998def1f0f5fe60016d068affc0433`; builder tính lại và bắt buộc khớp.
  Dữ kiện F2 giữ `draft_unverified`, không được tự nâng trạng thái khi sinh F3.
- `inputs/blueprints.psv`: 154 phác thảo chủ đề do Codex soạn cho 174 mã, phương pháp
  `codex_authored_concept_blueprints_v1`. Các mã cùng chủ đề như tên môn tương ứng giữa
  hai chương trình có thể dùng chung phác thảo, nhưng mỗi hồ sơ/chunk luôn giữ ngành,
  mã, phiên bản và tín chỉ nguồn riêng. Không tự coi các môn là tương đương học vụ.
- Mỗi phác thảo có ít nhất 3 chủ đề nội dung, 2 mục tiêu, 2 hoạt động đánh giá đề xuất
  và 2 tiêu chí. Đây là đề xuất kiến thức theo tên môn và khái niệm chuyên môn, không
  phải suy ra rằng HUS chắc chắn giảng dạy các chủ đề đó. Môn “chọn lọc”/xêmina dùng
  phương án chuyên đề tự chọn, không bịa chủ đề đã được trường quyết định.
- Tên/mã/tín chỉ/nhóm và tiên quyết chỉ lấy từ F2, với pointer từng dòng và locator PDF.
  Không đoán quan hệ tiên quyết mới; raw rỗng không được tự diễn giải là không có điều kiện.
- Có liên kết tới đề cương thật đã trích xuất trước đây khi mã/ngành khớp, trong
  `official_source_candidates`. Các ứng viên vẫn chưa đủ review/phiên bản, không được
  dùng làm bằng chứng xác nhận nội dung sinh hoặc đánh giá chính thức.
- Không có gọi API LLM, tải nguồn mới hoặc sinh danh tính reviewer. `authored_by=Codex`,
  `reviewer=null`, `review_status=needs_review`, `academic_verified=false`.

Nguồn F2 chỉ chứng minh danh tính và dữ kiện đầu vào. **Không dùng URL PDF/F2 làm citation
để khẳng định các chủ đề, mục tiêu hay cách đánh giá do AI sinh là đề cương của HUS.**

## Các file có thể sử dụng

Trong `release/`:

| File | Vai trò |
| --- | --- |
| `records.jsonl` | 290 hồ sơ cấu trúc; giữ provenance F2, nội dung sinh, mục tiêu, gợi ý đánh giá và trường chính thức null. |
| `rag_documents.jsonl` | 290 tài liệu văn bản có nhãn AI sinh và metadata để nạp bộ chỉ mục riêng. |
| `rag_chunks.jsonl` | **870 chunks**, mỗi môn–ngành 3 phần: `content`, `objectives`, `suggested_assessment`. Đây là file nạp RAG thuận tiện nhất. |
| `source_map.jsonl` | Ánh xạ chunk tới bản ghi, trường, offset và dòng blueprint. Offset áp dụng cho nội dung trường được render từ `records.jsonl`, không tính context lặp. |
| `coverage.jsonl` | Kiểm kê đủ ba phần cho từng cặp môn–ngành; độ bao phủ này chỉ là nội dung tham khảo sinh. |
| `acceptance_questions.jsonl` | 16 câu hỏi/contract: bốn ngành, nội dung/mục tiêu/gợi ý đánh giá và câu hỏi về tỷ lệ thi chính thức. |
| `manifest.json` | Hash nguồn/blueprint/mã/output, số lượng và kết quả contract; không có timestamp tùy thời điểm để giữ tái lập. |

`official_content`, `official_objectives`, `official_assessment` luôn null. Trong phần gợi ý,
`weights_percent` và `official_exam_format` cũng null. Không có lịch học, giáo trình,
giảng viên, chuẩn đầu ra hoặc tỷ lệ điểm chính thức được bịa thêm.

Mỗi chunk tự chứa cảnh báo AI sinh và thông tin ngành/mã/phiên bản để không mất nhãn khi
truy xuất riêng lẻ. `citation_label` ghi “F3 do AI sinh”, không giả citation nguồn chính thức.

## Hợp đồng tích hợp RAG

Nạp `rag_chunks.jsonl` vào collection/namespace riêng, chẳng hạn `hus_f3_generated_reference`.
Giữ nguyên `text`, `chunk_id`, `program_id`, `major`, `course_code`, `curriculum_version`,
`cohort_year`, `field`, `content_origin`, `dataset_kind`, `usage_scope`, `disclosure_required`
và provenance. Lọc đúng chương trình/phiên bản trước khi truy xuất cho một sinh viên.

Chỉ bật collection này khi chấp nhận câu trả lời tham khảo sinh. Với câu hỏi tên môn,
truy vấn cả ba field của đúng môn; với câu hỏi nội dung/mục tiêu/đánh giá, chọn field phù hợp.
Tên khóa/phiên bản là khai báo của F2, chưa phải kết luận độc lập về hiệu lực hiện tại.

Câu trả lời phải nêu nội dung do AI đề xuất, chưa phải đề cương chính thức. Với câu hỏi
“thi chính thức chiếm bao nhiêu phần trăm?”, phải trả lời chưa có thông tin đã xác minh;
có thể đưa gợi ý đánh giá sau khi gắn nhãn gợi ý, không điền tỷ lệ. Không đưa các record
này qua gate `include` như nguồn đã duyệt hoặc tự trộn vào `data/hus/corpus`.

Tập này đã sẵn sàng về định dạng dữ liệu để nạp RAG; **chưa chạy embedding, tạo vector index,
truy vấn model hoặc triển khai chatbot**. 16 contract kiểm tra bằng chứng/trạng thái trong
dữ liệu, không phải điểm chất lượng retrieval hoặc câu trả lời LLM.

Ba ví dụ cũ tại `../experimental/f3_inferred.json` là artifact của bước trước. Khi dùng
tập đầy đủ này, không index thêm ba ví dụ cũ để tránh lặp nội dung cùng môn.

## Tái tạo và kiểm chứng

Chạy từ repository root bằng dependency hiện có, không cần mạng/API key/database:

```powershell
python -X utf8 -m tools.prepare_hus_f3_reference verify --out data/hus/qa/20261028/f3_reference/release
python -X utf8 -m tools.prepare_hus_f3_reference build --out backups/rag_preparation/f3-reference-new01
python -X utf8 -m tools.prepare_hus_f3_reference verify --out backups/rag_preparation/f3-reference-new01
python -m pytest -q tests/hus/test_f3_reference.py
```

Build từ chối ghi đè hoặc ghi vào raw/processed/catalog/corpus nguồn. Verify dựng lại và
so từng byte của đủ bảy file. Sửa blueprint hoặc nguồn phải tạo release mới; nguồn F2
khác commit/blob cần cập nhật contract rõ ràng. Bộ test kiểm đủ 290 membership, provenance,
nhãn từng chunk, trường chính thức null, loại mã tham chiếu, nguồn stale và khả năng tái lập.

Nghiệm thu thực chạy: **17 test mới đạt**, toàn repository **518 passed, 26 skipped**;
Ruff và diff check đạt. Verify tái tạo đúng bảy file; 16 câu hỏi contract đều đạt.
Các kiểm tra PostgreSQL/full-source cần cấu hình riêng vẫn bị skip; chưa đo chất lượng
embedding/retrieval hoặc câu trả lời LLM. Corpus nguồn, catalog học vụ và raw được giữ nguyên.
