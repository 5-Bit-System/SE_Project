# A1b — Dữ kiện chương trình và nhóm kiến thức

Triển khai local trên `crawldata`, chỉ cho chatbot hỏi đáp HUS. Giữ release
`hus-data-20261031-v3` và tất cả nguồn/review/gold/baseline cũ.

| Loại câu hỏi | Dữ kiện và cách trả lời |
| --- | --- |
| Tổng tín chỉ chương trình | `field=program_credits`, trả `credits_required` được ghi, không cộng từ nhóm hoặc môn. Bốn ngành: Toán học 135, Toán tin 132, KHMT&TT 129, KHDL 127. |
| Danh sách nhóm kiến thức | `field=program_groups`, giữ toàn bộ nhóm, kể cả nhóm cha/con; số nhóm lần lượt 12/9/9/12. |
| Quy định/ghi chú một nhóm | `field=group_rules`, mã nhóm trong câu hoặc `group_key`, ví dụ `II`, `V.2`, `V.2.1`. Trả tên, heading, yêu cầu tối thiểu nếu chọn, tín chỉ được liệt kê và ghi chú gốc. |

Câu cấp chương trình không cần mã môn, vẫn cần ngành và phiên bản đúng. Sai hệ,
kể cả hệ ghi trong câu khác metadata chọn, không lấy dữ kiện hệ chuẩn để trả.
Mã nhóm chưa rõ hỏi lại, không chọn nhóm gần giống; nhóm ngoài phạm vi không có
thông tin. Hỏi đồng thời nhiều nhóm hoặc trộn chương trình/môn/nội dung ngành yêu
cầu làm rõ, không trả một phần rồi coi là đủ. Explicit field hint không thay đổi
điều câu hỏi thực sự yêu cầu. Giữ cách hỏi một lượt và quyền F3 theo A1.

Nhóm II ghi yêu cầu 5 và liệt kê 13, không coi hai số là một. Ô `null` giữ nguyên
và hiển thị “chưa ghi”. Ghi chú ngoại ngữ chọn 1/7, các môn không tính vào tổng,
phương án thay thế khóa luận và điều kiện lựa chọn giữ nguyên. KHDL V.2 ghi
28/63, trong khi các nhóm con có số liệu riêng; không cộng, sửa hoặc suy điều
kiện tốt nghiệp. Danh sách học phần theo nhóm chưa thuộc hợp đồng này.

Lookup lấy bản sao từ chương trình/nhóm trong snapshot đã kiểm. Khi nạp, hàm
thuần của exporter được dùng trong bộ nhớ để kiểm lại bản ghi với canonical và
input manifest: giá trị, đủ dòng, scope, review, URL, Git blob và JSON pointer.
Không ghi/build lại release hoặc index. Loader legacy không tự đọc nguồn khác.

Citation trỏ URL canonical đã ghim commit, kèm hash snapshot và JSON pointer.
Quote gồm đúng các field nguồn được dùng; không tự gán trang PDF. URL web chưa
được tải lại trong request. Review giữ từ nguồn: KHMT&TT `verified` cấp dự án,
ba chương trình còn lại `draft_unverified`; không xác nhận hiệu lực hiện tại hay
chứng nhận của trường.

Menu thêm 50 câu cấp chương trình/nhóm sau khi API trả được; tổng 2.414 câu mẫu.
Help/UI phân biệt câu cấp chương trình không cần mã với câu cấp môn cần mã/tên.
Test menu cũ được sửa đúng giả định `course_code` nay chỉ dành cho câu cấp môn.

Dev v5 đóng băng 12 ca nguồn trước tuning, không phải holdout; thêm test về scope,
null, cha/con, bản ghi khác canonical, review/URL/blob, tên hệ, phủ định và câu nhiều
ý. Technical reviewer là AI; không có human review hoặc chứng nhận độc lập.
Exposure H2 đã tuning vẫn 25 câu từ các bước trước, không thêm câu H2 trong A1b.

Kết quả và pins: [receipt A1b](acceptance/hus_program_questions_a1b_report.json).
Các phép đo dev cũ giữ scorer/gold; không suy điểm dev thành Recall độc lập ≥90%.
Chưa tích hợp embedding/Chroma, LLM, bật official F3 hoặc commit/push/deploy.
