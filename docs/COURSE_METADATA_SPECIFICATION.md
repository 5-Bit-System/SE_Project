# Đặc tả dữ liệu và metadata môn học

Đây là hợp đồng thiết kế mục tiêu cho Explainable Course Recommender, không phải xác nhận toàn bộ trường đã được nhập hoặc được backend kiểm tra. Phạm vi tài liệu là cấu trúc và ý nghĩa metadata; triển khai, nhập dữ liệu và thay đổi database là công việc riêng.

## 1. Cấu trúc và trách nhiệm

| Nhóm | Trách nhiệm |
|---|---|
| Nhận diện và khung chương trình | Xác định học phần trong chương trình và phiên bản cụ thể; tên, tín chỉ, khối kiến thức. |
| Điều kiện học vụ | Biểu diễn tiên quyết, liên kết nhóm tự chọn và nhánh tốt nghiệp. Backend quyết định eligibility trước xếp hạng. |
| Metadata tư vấn | Mô tả chủ đề, định hướng, mức độ nội dung và khối lượng học tập có bằng chứng; hỗ trợ xếp hạng và giải thích. |
| Nguồn và thẩm định | Cho biết thông tin lấy từ đâu, đã đối soát hay chưa và có mâu thuẫn không. |

Đây là các nhóm ý nghĩa, không bắt buộc chia thành bốn object hoặc bốn bảng. Điểm xếp hạng, lý do đủ điều kiện, độ phù hợp với sinh viên và số môn được mở khóa là kết quả tính toán theo ngữ cảnh, không phải metadata tĩnh.

Khóa nhận diện đầy đủ là `(program_id, catalog_revision, code)`. Cùng mã môn ở khác chương trình hoặc phiên bản không mặc nhiên có cùng nội dung, tín chỉ hay tiên quyết. `program_id` và `catalog_revision` có thể nằm ở cấp catalog, không cần lặp trong mỗi môn.

## 2. Quy ước giá trị chưa biết

- Trường bắt buộc không được thiếu hoặc `null`, trừ khi định nghĩa cho phép rõ ràng.
- Trường tùy chọn bị thiếu nghĩa là chưa được cung cấp. Khi xuất bản ghi theo đặc tả này, dùng `null` để biểu diễn chưa biết ở các trường cho phép `null`.
- `null` không tương đương `0`, `false`, mức trung bình hoặc chuỗi rỗng. Chỉ dùng chuỗi `unknown` trong enum trạng thái có định nghĩa giá trị này.
- `[]` nghĩa là đã xác định danh sách rỗng. `topics: null` là chưa phân loại; `topics: []` là đã xem xét nhưng chưa có nhãn phù hợp trong từ điển.
- `prerequisites: []` chỉ có nghĩa không có tiên quyết khi nguồn cho phép kết luận đó. Nếu chưa đọc được hoặc đang mâu thuẫn, trạng thái tiên quyết phải thể hiện điều này; mảng rỗng không tự mở khóa môn.
- Không suy đoán metadata từ tên, mã môn, số tín chỉ hay câu trả lời của LLM.

## 3. Định nghĩa các trường

### 3.1. Nhận diện và khung chương trình

| Trường | Kiểu | Yêu cầu và ý nghĩa |
|---|---|---|
| `code` | `string` | Bắt buộc; mã theo nguồn, bỏ khoảng trắng thừa và chuẩn hóa chữ hoa; không rỗng, duy nhất trong phiên bản catalog. |
| `name` | `string` | Bắt buộc; tên tiếng Việt theo nguồn, không rỗng. |
| `name_en` | `string \| null` | Tùy chọn; tên tiếng Anh có nguồn, không coi bản dịch tự tạo là tên chính thức. |
| `credits` | `int` | Bắt buộc; số nguyên dương, không đặt giới hạn tối đa tùy ý. |
| `block` | `string` | Bắt buộc; `general`, `field`, `discipline`, `group`, `major`: khối chung, lĩnh vực, khối ngành, nhóm ngành, ngành. Giữ phân loại của khung chương trình; không thay bằng `fundamental`/`specialized` khi chưa có ánh xạ. |
| `requirement_type` | `string` | Bắt buộc; `required`, `elective`, `required_excluded`, `graduation`: bắt buộc, tự chọn, bắt buộc không tính tổng tín chỉ, học phần thuộc yêu cầu/nhánh tốt nghiệp. |
| `counted_in_total` | `bool` | Bắt buộc; có tính vào tổng tín chỉ chương trình hay không. `required_excluded` phải là `false`. Không suy từ số tín chỉ. |
| `hours` | `object \| null` | Tùy chọn; `lecture`, `practice`, `self_study` nhận số nguyên không âm hoặc `null`. `0` là nguồn ghi không có giờ loại đó, `null` là chưa biết. |

### 3.2. Điều kiện học vụ

| Trường | Kiểu | Yêu cầu và ý nghĩa |
|---|---|---|
| `prerequisites` | `list[list[string]]` | Bắt buộc; AND giữa các nhóm, OR giữa các mã trong nhóm. Nhóm con không được rỗng. Giữ cấu trúc logic nguồn. |
| `prerequisites_raw` | `string \| null` | Tùy chọn; văn bản tiên quyết nguyên gốc để đối soát. |
| `prerequisite_status` | `string` | Bắt buộc trong hợp đồng mục tiêu; `verified`, `draft_unverified`, `unresolved_external`, `conflict`, `unknown`. Phản ánh riêng chất lượng thông tin tiên quyết. |
| `prerequisite_variants` | `list[list[list[string]]]` | Tùy chọn; các biểu thức AND/OR khác nhau khi nguồn mâu thuẫn. Với `conflict`, phải có ít nhất hai phương án khác nhau kèm bằng chứng riêng. |
| `external_prerequisite_codes` | `list[string]` | Các mã tham chiếu chưa đối chiếu được trong catalog hiện tại. Giữ chúng trong biểu thức gốc; trường này chỉ đánh dấu tham chiếu chưa giải quyết. |
| `choice_group_ids` | `list[string]` | Liên kết nhóm tự chọn cùng phiên bản; quota nằm ở định nghĩa nhóm. `[]` khi xác nhận không thuộc nhóm nào. |
| `graduation_path_ids` | `list[string]` | Liên kết nhánh tốt nghiệp cùng phiên bản; không có nghĩa môn bắt buộc cho mọi nhánh. |
| `year` | `int \| null` | Tùy chọn; năm học khuyến nghị có nguồn, số nguyên dương trong thời lượng chương trình. Không phải điều kiện cứng. |
| `suggested_term` | `int \| null` | Tùy chọn; học kỳ khuyến nghị có nguồn trong phạm vi chương trình. Không xác nhận lịch mở lớp hoặc tạo kế hoạch học tự động. |

| Biểu thức minh họa | Ý nghĩa |
|---|---|
| `[]` | Không có tiên quyết nếu trạng thái nguồn cho phép kết luận này. |
| `[["DEMO101"]]` | Cần hoàn thành DEMO101. |
| `[["DEMO101"], ["DEMO102"]]` | Cần DEMO101 và DEMO102. |
| `[["DEMO101"], ["DEMO102", "DEMO103"]]` | Cần DEMO101 và ít nhất một trong DEMO102, DEMO103. |

Tham chiếu ngoài catalog không được mở khóa môn và không được xóa khỏi biểu thức vì sẽ làm yếu điều kiện AND/OR. Một lựa chọn nội bộ đã hoàn thành có thể thỏa nhóm OR; lựa chọn ngoài chưa xác minh luôn chưa được coi là hoàn thành. `conflict` hoặc `unknown` không được trình bày là đã xác nhận đủ điều kiện. `draft_unverified` chỉ cho kết quả tạm theo dữ liệu phiên âm, kèm cảnh báo. Trạng thái phải phản ánh vấn đề đang tồn tại; bằng chứng theo trường lưu các giới hạn còn lại nếu một trạng thái không diễn đạt hết.

### 3.3. Metadata tư vấn

Mọi trường dưới đây tùy chọn và cho phép `null`. Giá trị khác `null` phải có bằng chứng theo mục 4. Thiếu metadata không làm môn mất eligibility và không mặc định là phù hợp hoặc không phù hợp.

| Trường | Kiểu | Giá trị và định nghĩa |
|---|---|---|
| `topics` | `list[string] \| null` | Nhãn kiến thức chính từ mục 5, không trùng lặp. Không gán nhãn chỉ liên quan gián tiếp. |
| `orientation` | `string \| null` | `theory`, `practice`, `research`: định hướng nổi trội theo mục tiêu, nội dung và đánh giá. Không đủ căn cứ thì để `null`. |
| `difficulty` | `string \| null` | `easy`, `moderate`, `advanced`: độ phức tạp nội dung theo rubric chung, tương ứng cơ bản, trung gian, chuyên sâu. `easy` không có nghĩa dễ đạt điểm cao; không đo độ khó riêng cho từng sinh viên. |
| `workload` | `string \| null` | `light`, `moderate`, `heavy`: khối lượng học tập theo rubric có phạm vi và ngưỡng rõ ràng, dựa trên đề cương hoặc khảo sát có phương pháp. Thiếu rubric/bằng chứng thì để `null`. |
| `description` | `string \| null` | Tóm tắt ngắn nội dung có nguồn; không thêm công nghệ, hình thức đánh giá hoặc lời hứa về kết quả học tập chưa xác nhận. |
| `career_paths` | `list[string] \| null` | Nhãn nghề nghiệp có phiên bản; thể hiện liên hệ kiến thức với nghề, không đảm bảo việc làm hoặc chứng nhận năng lực. |

Rubric `difficulty` phải nêu đối tượng tham chiếu, kiến thức nền, mức trừu tượng và độ sâu nội dung. Rubric `workload` phải nêu đơn vị, khoảng thời gian và ngưỡng phân loại. Không so sánh nhãn từ hai rubric khác nhau như cùng thang đo. Tín chỉ và giờ học là dữ kiện riêng, không tự quyết định `workload`.

Trọng số xếp hạng thuộc cấu hình thuật toán hoặc yêu cầu người dùng, không cố định trong đặc tả metadata. LLM chỉ dùng giá trị và bằng chứng được cung cấp; nhận định chưa thẩm định phải được diễn đạt là tạm thời.

## 4. Nguồn, bằng chứng và thẩm định

| Trường | Kiểu | Ý nghĩa |
|---|---|---|
| `source_page` | `int \| null` | Trang chứa bản ghi chính, đánh số từ 1 theo vị trí trong file PDF. Không đại diện nguồn của mọi metadata. |
| `source_status` | `string` | `verified` hoặc `draft_unverified`: trạng thái đối soát khung chương trình, không chứng nhận toàn bộ metadata tư vấn hoặc tiên quyết riêng. |
| `offering_status` | `string` | `unknown` trong phạm vi hiện tại; chưa xác minh môn đang mở lớp. |
| `field_evidence` | `object` | Ánh xạ tên trường sang danh sách bằng chứng cho dữ liệu khung chương trình, tiên quyết và metadata tư vấn. |

Mỗi bằng chứng có cấu trúc:

| Khóa | Kiểu | Yêu cầu |
|---|---|---|
| `source_ref` | `string` | Bắt buộc; đường dẫn, URL hoặc ID tài liệu truy xuất được, gắn đúng phiên bản nguồn. |
| `locator` | `string` | Bắt buộc; trang, mục, bảng hoặc ID bản ghi khảo sát cụ thể. |
| `method` | `string` | Bắt buộc; `transcription`, `curated_mapping`, `survey`: trích nguồn, phân loại theo rubric, khảo sát. |
| `status` | `string` | Bắt buộc; `verified`, `draft_unverified`, `conflict`. `verified` là đã đối soát, không đồng nghĩa nguồn có hiệu lực học vụ hiện hành. |
| `reviewed_by` | `string \| null` | ID người/nhóm thẩm định; bắt buộc khác `null` khi đã xác minh. |
| `reviewed_at` | `string \| null` | Thời điểm ISO 8601 có múi giờ; bắt buộc khi đã xác minh. |
| `rubric_ref` | `string \| null` | Tham chiếu rubric có phiên bản; bắt buộc cho `difficulty`, `workload` và các ánh xạ chủ quan. |
| `note` | `string \| null` | Căn cứ, giới hạn hoặc điểm mâu thuẫn; không thay nguồn truy xuất được. |

Một trường có thể có nhiều nguồn. Nguồn cho `name` không tự chứng minh `topics`, `workload` hoặc `career_paths`. Khi nguồn mâu thuẫn, giữ bằng chứng và đánh dấu `conflict`; trường tư vấn tương ứng để `null` đến khi giải quyết. Tiên quyết giữ các phương án ở `prerequisite_variants`, với bằng chứng chỉ rõ phương án tương ứng. Không khẳng định đã thẩm định hoặc gán metadata tư vấn nếu thiếu bằng chứng cho trường đó.

## 5. Từ điển chuẩn hóa

Catalog chỉ rõ `metadata_schema_version` và `vocabulary_version` ở cấp envelope. Nhãn lưu bằng ID `snake_case`; tên hiển thị và từ đồng nghĩa là alias, không phải ID. Thêm/đổi nhãn phải cập nhật phiên bản và ánh xạ alias; nhãn cũ không được âm thầm đổi nghĩa.

| Nhóm topics | ID hợp lệ khởi đầu |
|---|---|
| AI và dữ liệu | `artificial_intelligence`, `machine_learning`, `deep_learning`, `computer_vision`, `image_processing`, `natural_language_processing`, `data_science`, `big_data`, `databases` |
| Toán và tối ưu | `mathematics`, `calculus`, `algebra`, `discrete_mathematics`, `probability`, `statistics`, `optimization`, `numerical_analysis` |
| Lập trình và hệ thống | `programming`, `data_structures_and_algorithms`, `software_engineering`, `web_development`, `operating_systems`, `computer_networks`, `cybersecurity` |

Tập nhãn `career_paths` khởi đầu: `ai_engineer`, `computer_vision_engineer`, `data_scientist`, `data_analyst`, `software_engineer`, `quant_researcher`. Chỉ gán khi có bằng chứng ánh xạ; không yêu cầu mọi môn có nhãn nghề nghiệp.

“Thị giác máy tính” hoặc “computer vision” được chuẩn hóa thành `computer_vision` trước khi so khớp. `computer_vision` và `image_processing` có liên quan nhưng không tự động đồng nghĩa. Extraction, xếp hạng và giao diện dùng cùng phiên bản từ điển và enum.

## 6. Ví dụ JSON minh họa

Ví dụ hoàn toàn giả lập, không mô tả học phần có thật và không dùng seed catalog. Mã, nguồn và phiên bản chỉ là placeholder. Metadata tư vấn chưa có bằng chứng giữ `null`.

```json
{
  "metadata_schema_version": "1.0",
  "vocabulary_version": "1.0",
  "program_id": "demo_program",
  "catalog_revision": "demo_revision",
  "courses": [
    {
      "code": "DEMO201",
      "name": "Học phần minh họa",
      "name_en": null,
      "credits": 3,
      "block": "major",
      "requirement_type": "elective",
      "counted_in_total": true,
      "hours": {"lecture": 30, "practice": 15, "self_study": null},
      "prerequisites": [["DEMO101"], ["DEMO102", "DEMO103"]],
      "prerequisites_raw": "DEMO101 và (DEMO102 hoặc DEMO103)",
      "prerequisite_status": "draft_unverified",
      "prerequisite_variants": [],
      "external_prerequisite_codes": [],
      "choice_group_ids": ["demo_electives"],
      "graduation_path_ids": [],
      "year": null,
      "suggested_term": null,
      "topics": null,
      "orientation": null,
      "difficulty": null,
      "workload": null,
      "description": null,
      "career_paths": null,
      "source_page": 1,
      "source_status": "draft_unverified",
      "offering_status": "unknown",
      "field_evidence": {
        "prerequisites": [
          {
            "source_ref": "demo://curriculum-v1",
            "locator": "PDF page 1, row DEMO201",
            "method": "transcription",
            "status": "draft_unverified",
            "reviewed_by": null,
            "reviewed_at": null,
            "rubric_ref": null,
            "note": "Nguồn giả lập, chỉ minh họa định dạng."
          }
        ]
      }
    }
  ]
}
```

Đây là trích đoạn: DEMO101–103 và nhóm `demo_electives` phải được định nghĩa cùng phiên bản trong catalog hoàn chỉnh. Bản ghi thực tế cần bằng chứng cho từng trường đã trích hoặc phân loại; ví dụ chỉ minh họa một mục bằng chứng tiên quyết.

## 7. Điều kiện chấp nhận

1. Kiểu, enum và quy ước thiếu/`null`/`[]` nhất quán; không gán mặc định để che dữ liệu chưa biết.
2. Mã môn và liên kết được kiểm tra trong đúng chương trình, phiên bản; tham chiếu ngoài giữ nguyên logic nguồn và được đánh dấu.
3. Tiên quyết không có nhóm OR rỗng, mã trùng trong nhóm, tự tham chiếu hoặc chu trình giữa các môn nội bộ. Mâu thuẫn không được giải quyết bằng cách bỏ điều kiện.
4. Nhóm tự chọn và nhánh tốt nghiệp có định nghĩa riêng; môn chỉ chứa liên kết. Năm/học kỳ khuyến nghị không trở thành điều kiện cứng hoặc lịch mở lớp.
5. Metadata tư vấn có nguồn, rubric khi cần và trạng thái thẩm định riêng. Không khẳng định môn dễ lấy điểm, nhẹ bài tập hoặc phù hợp nghề nghiệp nếu thiếu căn cứ.
6. Đối soát khung chương trình không nâng toàn bộ metadata lên `verified`. Nội dung chưa thẩm định phải thể hiện giới hạn rõ ràng.
7. Dữ liệu tư vấn thiếu không thay đổi eligibility; LLM không tự bổ sung. Eligibility, điểm xếp hạng và giải thích là các đầu ra được kiểm tra riêng.

Tài liệu này không hướng dẫn sửa trực tiếp dữ liệu sinh tự động hoặc nhập lại catalog. Validator hiện có chỉ chứng minh quy tắc đã triển khai, không mặc nhiên chứng minh toàn bộ hợp đồng mục tiêu đã được hỗ trợ. Khi triển khai sau này cần kiểm tra riêng schema, bằng chứng theo trường và toàn vẹn liên kết.
