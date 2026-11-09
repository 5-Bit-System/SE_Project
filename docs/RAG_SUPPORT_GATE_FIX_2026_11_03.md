# Sửa gate bằng chứng — mục 2

Nhánh local `crawldata`, base `1287e2a`; release `hus-data-20261031-v3` giữ nguyên.
Chưa commit, xuất bản hoặc triển khai. [Receipt](acceptance/hus_support_gate_v3_report.json).

## Phạm vi và nguyên nhân

Tách 16 ca từ chối sau retrieval và bốn preview đã route đúng sang
[diagnostic dev v3](../data/hus/evaluation/diagnostic_dev_v3_support/README.md)
**trước sửa runtime**. Giữ nguyên request/gold/evidence từ bản H2 AI review;
không chèn field hoặc đáp án vào request. Đây là tập dev đã xem, không phải holdout.
Manifest: `54469f2117eb691d5130ebbe27a325bfc932bd05c635b0b5ef51bbc9cde24ac0`.

Đã tái hiện 20/20: routing đúng và có search, nhưng gate đòi “edition”, năm
phiên bản, “trình bày”, “kèm cảnh báo” xuất hiện trong thân trích đoạn. Ngoài ra,
`[:2]` làm thiếu hai trong bốn nhóm nghề nghiệp Khoa học dữ liệu.

## Thay đổi

Chỉ sửa hai runtime file: `app/hus/answer_support.py` và một dòng trong
`app/hus/answering.py`. Không sửa retriever, routing, loader, dữ liệu, review,
catalog/UI, citation hoặc AI opt-in.

- Phiên bản `edition`/`phiên bản`/QĐ được kiểm bằng metadata của hit. Năm và số
  không nằm trong định danh phiên bản vẫn là yêu cầu dữ kiện; không bỏ số tùy ý.
- Chỉ nhận diện các cụm yêu cầu có giới hạn, theo từng mệnh đề. Không ghép một
  phủ định với yêu cầu sau dấu câu/“nhưng” để che yêu cầu cần chứng cứ.
- “Trình bày”, “trích đoạn”, “chép” chỉ được bỏ ở đầu mệnh đề mang vai trò yêu
  cầu. “Năng lực trình bày” trong mục tiêu môn vẫn phải có bằng chứng. Review
  phát hiện lỗi này ở bản đầu; đã có test đỏ rồi sửa và reviewer kiểm lại.
- Các đoạn có thể bổ sung cho nhau chỉ khi cùng nguồn/hash/package, ngành,
  phiên bản, hệ, môn, field, origin và review. Chọn một nhóm nguồn đủ bằng chứng;
  không lấy từ nguồn khác để bù một khẳng định còn thiếu.
- Bỏ giới hạn hai chunk, giữ thứ tự đoạn trong nguồn. Vẫn chỉ xét **top 5 cũ**;
  không tăng truy xuất hoặc đọc nguồn candidate. Chưa bảo đảm mọi field của các
  release tương lai dài hơn top 5 sẽ luôn được trích đủ.

## Kết quả đã ghim

| Chỉ số trên 20 ca dev | Trước | Sau |
| --- | ---: | ---: |
| Routing đúng / có search | 20/20 / 20/20 | 20/20 / 20/20 |
| Câu trả lời có nguồn khớp anchor | 0/20 | 20/20 |
| Từ chối sai | 20/20 | 0/20 |
| Toàn bộ trích đoạn gold nằm trong citation trả về | 0/20 | 20/20 |

Q043 đủ hai phần mục tiêu; Q044 đủ bốn nhóm nghề nghiệp và bốn citation; bốn
preview trả F3 với nhãn AI. Top 5, môi trường, evaluator và runner không đổi;
trong các artifact trước/sau chỉ hai file runtime nói trên đổi hash.

Run trước: `dev_v3_support_before_v2`; sau cuối:
`dev_v3_support_after_command_guard`. Các run trung gian/collector dở dang được
giữ nguyên, không dùng thay run cuối. Có [AI review coverage và nguồn thay thế](../data/hus/review/support_gate_v3_response_review/review.json);
không chứng nhận độc lập ngữ nghĩa hoặc nâng trạng thái nguồn.

Dev cũ 96 câu được chạy riêng trên code cuối: Recall 39/40, F2 24/24, guard 32/32,
opt-in 8/8, integrity 64/64, từ chối sai 0/64. **Khớp anchor raw 60/64**, so với
mốc lịch sử 61/64; không sửa gold hoặc cộng nguồn thay thế vào điểm raw. Bốn lệch
anchor là Q004/Q027/Q049/Q050: chọn một nguồn nhất quán khác anchor, gồm Q004
nguồn **hệ tài năng 2015**, cần giữ giới hạn phạm vi này; Q027 chuẩn 2015,
Q049/Q050 DOCX chuẩn 2023. Q006 nay trích cả điều kiện và Thạc sĩ/Tiến sĩ từ cùng
nguồn web, có thêm đoạn nền tảng học tiếp. Không suy ra đủ điều kiện học/đăng ký.

**1.633 test offline đạt/90 deselected**, gồm 78 test gate mới; 171 test gate và
guard/routing đạt. 50 ca Chromium cũ, ba ca UI thực mới (bốn citation, từ chối
chưa opt-in, preview có opt-in), năm test Node và scoped Ruff đạt. PDF binary/hash
và trang phân biệt 13/12 đạt qua regression cũ; không chạy lại viewer PDF thực.
421 input cũ giữ hash; baseline/H2/review/source và các receipt cũ không đổi.

Mục tiêu Recall@5 độc lập ≥90% vẫn chưa được chứng minh; chưa chạy lại toàn bộ
56 câu H2. Giờ có 24 câu H2 được dùng chỉnh runtime qua dev v2/v3, trong đó bốn
preview trùng hai pack. Việc tiếp theo: biểu diễn/chấm tiên quyết unknown ở F2,
giữ điểm raw và ghi nhận nguồn thay thế riêng, sau đó đo toàn bộ snapshot cuối.
