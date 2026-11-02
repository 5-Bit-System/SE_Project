# Rubric metadata tư vấn HUS — 0.1-draft

Ngày: 21/10/2026. Đây là đề xuất để chuyên môn review, chưa phải thang đánh giá
đã được phê duyệt. Chưa gán nhãn cho môn thật và chưa dùng rubric này để xếp hạng.

Đối tượng tham chiếu: sinh viên đại học trong đúng chương trình và khóa 2022,
đã có kiến thức nền mà nguồn học phần yêu cầu. Đánh giá nội dung học phần,
không dự đoán điểm số hay độ khó riêng của từng sinh viên.

## Nội dung và định hướng

Dùng ID chủ đề/nghề nghiệp trong [đặc tả metadata](COURSE_METADATA_SPECIFICATION.md).
Tên hiển thị Việt/Anh là nhãn của cùng ID, không tạo hai hệ phân loại.
Không phân loại chỉ từ tên môn. Đọc mục tiêu, nội dung, chuẩn đầu ra và hình thức
đánh giá trong đề cương đúng phiên bản; dẫn mục/trang cho từng ánh xạ.

| Trường | Căn cứ cần thu thập |
|---|---|
| `topics` | Chủ đề xuất hiện trực tiếp trong nội dung và mục tiêu; ghi ID và mục/trang. |
| `orientation` | `theory` khi trọng tâm là mô hình/lập luận; `practice` khi trọng tâm là triển khai/thực hành; `research` khi trọng tâm là câu hỏi mở/phương pháp nghiên cứu. Nếu không có trọng tâm rõ thì giữ null. |
| `career_paths` | Liên hệ giữa chuẩn đầu ra và nhiệm vụ nghề cụ thể; cần người có chuyên môn review, không suy từ tên môn. |
| `description` | Hai bản tóm tắt `vi`, `en` dựa trên cùng đề cương, có nguồn và người review bản dịch. Bản dịch phải được ghi là bản dịch biên tập nếu không có văn bản tiếng Anh chính thức. |

Hợp đồng runtime hiện có `description` dạng chuỗi; trước khi đưa mô tả song ngữ
vào API cần bổ sung hợp đồng locale và kiểm tra tương thích. Đợt này chỉ tên môn
song ngữ được lấy trực tiếp từ bảng PDF, không tự tạo mô tả cho đủ dữ liệu.

## Độ phức tạp nội dung

Tham chiếu dự kiến: `docs/HUS_METADATA_RUBRIC_DRAFT.md#difficulty-0.1-draft`.
Ghi riêng kiến thức nền, mức trừu tượng, độ sâu và mức tự chủ cần thiết.

| ID | Nhãn vi / en | Tiêu chí đề xuất |
|---|---|---|
| `easy` | Cơ bản / Foundational | Chủ yếu vận dụng khái niệm và quy trình được hướng dẫn trực tiếp. |
| `moderate` | Trung gian / Intermediate | Kết hợp nhiều khái niệm/phương pháp, lựa chọn cách giải và giải thích lựa chọn. |
| `advanced` | Chuyên sâu / Advanced | Lập luận trừu tượng hoặc tổng hợp chuyên sâu, xử lý bài toán mở với mức tự chủ cao. |

Không lấy tín chỉ, mã môn hoặc `courses.difficulty_level=2` làm bằng chứng.
Nếu các chiều không thống nhất, ghi nhận từng chiều và giữ nhãn null chờ review.

## Khối lượng học tập

Tham chiếu dự kiến: `docs/HUS_METADATA_RUBRIC_DRAFT.md#workload-0.1-draft`.
Đơn vị dự kiến: tổng giờ học thực tế/tuần/môn, gồm giờ trên lớp, bài tập, dự án
và tự học, trong các tuần giảng dạy của đúng phiên bản đề cương.

Ngưỡng đề xuất để chuyên môn hiệu chỉnh: `light` ≤ 6 giờ, `moderate` > 6 đến
10 giờ, `heavy` > 10 giờ. Các ngưỡng chưa được hiệu chuẩn; không áp dụng cho môn
thật trước khi review. Ghi riêng trung vị tuần thường và tuần cao điểm, số tuần,
cỡ mẫu và phương pháp khảo sát. Không suy `workload` trực tiếp từ số tín chỉ
hay ba cột giờ học trong khung chương trình.

## Thu thập và xử lý bất đồng

Mỗi đánh giá cần program/cohort/revision/code, phiên bản đề cương, hash/URL,
locator, giá trị đề xuất, căn cứ, rubric version, người review và thời điểm có múi giờ.
Thu thập đánh giá độc lập trước khi thảo luận. Không bình quân nhãn phân loại.
Giữ các ý kiến, lý do khác nhau và trạng thái conflict; trường tư vấn tương ứng
giữ null cho tới khi người phụ trách kết luận. Không tự điền reviewer.

Mẫu nhập: [advisory-review-template.csv](../reports/hus-metadata-2026-10-21/advisory-review-template.csv).
