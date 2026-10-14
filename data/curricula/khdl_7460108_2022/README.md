# Bộ dữ liệu mẫu bàn giao: Khoa học dữ liệu 2022

Mẫu theo [đặc tả metadata](../../../docs/COURSE_METADATA_SPECIFICATION.md), gồm **65 học phần** của `khdl_7460108_2022`. Dữ kiện khung chương trình kế thừa bản chép hiện có, chưa được đối soát PDF gốc. Đây là mẫu cấu trúc để xây dựng dữ liệu, không phải dữ liệu đã thẩm định đầy đủ.

## Các file cần gửi

- `courses.json`: envelope có phiên bản schema, từ điển, ngành, revision và mảng `courses`; mỗi môn đủ các trường mục tiêu, bằng chứng riêng theo trường.
- `curriculum.json`: quy tắc cấp chương trình, khối kiến thức, nhóm tự chọn, nhánh tốt nghiệp, ghi chú mâu thuẫn và danh mục nguồn.
- `source_rows.json`: bản chép từng dòng nguồn, giữ để đối soát; không coi đây là bằng chứng đã xác minh.
- `vocabulary.json`: nhãn và enum theo đặc tả 1.0; alias hiện chỉ minh họa, cần bổ sung có kiểm soát.
- File hướng dẫn này và `docs/COURSE_METADATA_SPECIFICATION.md` trong dự án.

PDF gốc có tên và SHA-256 trong `curriculum.json`, nhưng chưa có trong repository. Cần gửi PDF gốc kèm bộ mẫu để người nhập có thể đối soát. `source_ref` tương đối được tính từ thư mục ngành; `locator` xác định trang/dòng hoặc vị trí trong JSON.

## Cách xây dựng dữ liệu mỗi ngành

1. Tạo thư mục ngành riêng, sao chép cấu trúc file; đặt đúng `program_id`, tên và thông tin nguồn. Không sao chép các môn/tiên quyết/quota của ngành mẫu làm dữ kiện cho ngành khác.
2. Chép bảng khung chương trình vào `source_rows.json`. Giữ mã, tên, tín chỉ, giờ, tiên quyết nguyên văn và số trang. Ô trống giờ chưa rõ dùng `null`, không tự điền `0`.
3. Xây dựng `curriculum.json`: nhóm, quota, khối, nhánh tốt nghiệp và các điểm nguồn cần xác minh. Không tự sửa chênh lệch tổng tín chỉ trong PDF.
4. Xây dựng các bản ghi trong `courses.json`, giữ AND giữa nhóm và OR trong nhóm. Mã ngoài catalog giữ nguyên và đánh dấu `external_prerequisite_codes`; không xóa khỏi biểu thức. Mâu thuẫn lưu các phương án cùng nguồn, đặt `conflict`.
5. Metadata tư vấn chỉ điền khi có nguồn: `topics`, `orientation`, `difficulty`, `workload`, `description`, `career_paths`. Không có nguồn để `null`. Tên môn hoặc số tín chỉ không đủ để suy ra nội dung, độ khó, độ nhẹ hoặc nghề nghiệp.
6. Mỗi trường đã có giá trị cần bằng chứng trong `field_evidence`. Với phân loại chủ quan dùng `curated_mapping`, ghi `rubric_ref` có phiên bản; lưu rubric được tham chiếu cùng bộ bàn giao. `difficulty`/`workload` chưa có rubric thì giữ `null`.
7. Sau đối soát, cập nhật trạng thái đúng từng trường, `reviewed_by` và `reviewed_at` có múi giờ. Không nâng mọi metadata lên `verified` chỉ vì đã kiểm tra tên môn. `offering_status` vẫn `unknown`.
8. Đặt `catalog_revision` mới khi dữ liệu thay đổi; dùng cùng revision giữa curriculum và courses. Giữ `metadata_schema_version`/`vocabulary_version` nhất quán, không tự đổi nghĩa enum.

## Những gì mẫu đã và chưa làm

Mẫu có đủ các loại môn, nhóm tự chọn, nhánh tốt nghiệp và các tham chiếu ngoài catalog của ngành. Toàn bộ dữ liệu nguồn giữ `draft_unverified`; tiên quyết có tham chiếu ngoài dùng `unresolved_external`. Metadata tư vấn, năm và học kỳ khuyến nghị đều `null` vì chưa có nguồn đủ căn cứ. `instruction_language` và `source_rows` là thông tin bổ sung kế thừa, không thay thế các trường chuẩn.

Bằng chứng cấp môn tham chiếu bản chép dòng hoặc cấu trúc chương trình; chưa chứng minh PDF gốc chính xác. Cần người nhập kiểm tra lại trang, dòng, biểu thức tiên quyết và mâu thuẫn đã ghi trong `source_issues`.

## Checklist trước khi bàn giao ngành hoàn chỉnh

- Mã không trùng trong ngành; mọi tham chiếu nội bộ, nhóm và nhánh có định nghĩa đúng phiên bản.
- Không có nhóm OR rỗng, tự tham chiếu hoặc chu trình tiên quyết nội bộ.
- Tham chiếu ngoài chưa xác minh không mở khóa môn; mâu thuẫn không bị bỏ điều kiện.
- Kiểu dữ liệu, enum, `null` và `[]` đúng đặc tả; nhãn thuộc từ điển.
- Trường đã điền có nguồn riêng; trường đã xác minh có người và thời điểm review.
- Rubric phân loại được gửi kèm; không hứa dễ lấy điểm, nhẹ bài hoặc đảm bảo việc làm.
- Giữ nguyên các điểm chưa giải quyết và cung cấp PDF gốc đúng hash.

Định dạng envelope mới là hợp đồng bàn giao; loader, builder, seed và test hiện tại chưa được chỉnh để nhận mẫu này. Không chạy `build_catalogs.py --write` lên mẫu vì có thể ghi đè metadata; việc tích hợp runtime là nhiệm vụ riêng.
