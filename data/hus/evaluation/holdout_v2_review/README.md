# Bàn giao cho người review thật

Bạn đã nhận review trong hội thoại ngày03/11/2026. Hiện **0/56 câu được duyệt**.
Không điền tên hay check thay người review. Ít nhất40 accepted, có cả bốn ngành
(tối thiểu8/ngành) và sáu nhóm câu hỏi mới đủ để đề nghị bạn chốt bộ cuối.

## Các bước review

1. Mở ../holdout_v2_candidate/reviewer_packet.md và README của candidate.
   Bộ này là nháp AI; tác giả AI đã biết code/dev, chưa có chứng nhận độc lập.
2. Copy review_worksheet.csv sang reviews/<ten-that>_<ngay>.csv hoặc copy
   review_template.jsonl sang file review riêng. Không sửa candidate/template gốc.
3. Với từng câu, mở source_ref trong evidence.jsonl: đúng record/chunk ID và
   JSON pointer; kiểm quote/giá trị, edition/ngành/mã/version/review. Citation có
   SHA/physical PDF locator hoặc URL nguồn; source JSON chỉ là provenance.
4. Kiểm câu hỏi tự nhiên, đáp án đúng và đủ ý; phản ánh thiếu nguồn đúng cách.
   F3 là AI tham khảo, không phải đề cương/đánh giá chính thức. Kiểm opt-in.
5. Đọc overlap_v2/neighbors.jsonl hoặc cột nearest_prior_texts. Mở các bộ dev
   để xét TRÙNG Ý, không chỉ trùng chữ. Có thể cùng chủ đề nhưng phải ghi lý do
   có thể chấp nhận. Câu chỉ thay mã/tên hoặc bám cách sửa runtime phải revise/reject.
6. Xem alternative_evidence_candidates.jsonl và evidence_catalog.jsonl. Đây chỉ
   là gợi ý cùng scope/edition/field, KHÔNG phải nguồn đã được duyệt đủ ý.
   Kiểm nguyên văn, mức hỗ trợ claim và review. F2 kiểm tất cả source_occurrences;
   F3 không được mượn PDF F2 để làm nguồn nội dung. Nếu chưa có nguồn tương đương,
   ghi rõ đã tìm/đối chiếu và chưa tìm thấy, không đánh dấu nguồn giả.
7. Điền decision=accept/reject/revise; reviewer=tên thật; reviewer_kind=human;
   reviewed_at=thời điểm THỰC TẾ có múi giờ (+07:00); independent_of_runtime_tuning=true
   chỉ nếu bạn không dùng bộ này để chỉnh runtime. Không dùng thời gian mẫu làm chữ ký.
   Accept cần cả4 check=true, overlap_decision=distinct/acceptable_shared_topic,
   overlap_notes, alternative_evidence_notes và notes có lý do. Alternative IDs là
   mảng JSON, mặc định []; chỉ thêm IDs đã tự kiểm trong catalog. Nếu tìm nguồn
   khác chưa có catalog, ghi locator/hash trong notes và yêu cầu bổ sung evidence.
8. Reject/revise/pending không tính vào40. Đáp án/câu cần sửa phải tạo candidate
   phiên bản mới và rebind/review phần đổi; không sửa frozen v2 để hợp thức hóa.

Kiểm file review (CSV hoặc JSONL), chỉ kiểm kỹ thuật, không chạy RAG:

python -X utf8 -m tools.validate_hus_holdout_review --reviews <file-review-cua-ban> --evidence-catalog data/hus/evaluation/holdout_v2_review/evidence_catalog.jsonl

Validator chỉ đọc các quyết định bạn khai; không xác minh danh tính hay tự chứng
nhận công việc của người thật. Khi đủ điều kiện, nó báo ready_for_human_freeze_confirmation,
vẫn independent_holdout_certified=false cho tới khi bạn xác nhận chốt phạm vi.
Sau khi bạn duyệt/chốt mới tạo subset>=40 đã ghim và chạy phép đo độc lập.
Trong lúc này không hỏi app bằng bộ H2, không tuning theo nội dung H2, không
commit/push hoặc triển khai. Dữ liệu RAG/review/CURRENT/official F3 giữ nguyên.
