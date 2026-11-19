# Kiểm nội dung sau sửa router — 15/11/2026

Đã chạy **24 câu offline** trên v4/lexical, LLM tắt, không gọi Google. Có
**11 answered, 7 no-information, 6 cần làm rõ**. Phát hiện một câu nghề nghiệp
Toán tin bị từ chối vì xưng hô “em”; chưa sửa runtime trong lượt review này.

Đây là câu và nhận xét do Codex(AI) soạn, gồm cả cách hỏi dev đã phơi lộ.
**Chưa có review/nghiệm thu người thật**, chưa chứng minh mọi câu ngoài menu
hoặc Gemini đều hoạt động. Kết quả run20 câu cũ giữ nguyên.

## Đã kiểm những gì?

| Nhóm | Kết quả và nhận xét |
| --- | --- |
| Nghề nghiệp bốn ngành, RC24-001–004 |3 answered từ đúng nhóm F1/careers; Toán tin002 bị `evidence_rejected`. Toán học/KHDL dùng web có hệ/edition unknown; KHMTTT dùng DOCX2023 hệ chuẩn, giữ trạng thái include_markdown. Không xác nhận nguồn đang có hiệu lực hoặc các edition tương đương. |
| Khái niệm bốn ngành, RC24-005–008 |4 answered F3/content, đúng môn/ngành/phiên bản và nhãn AI. MAT2300 gồm5 nhóm khái niệm; MAT1202 gồm4 chủ đề; Học máy gồm4 chủ đề. Nội dung/ ví dụ theo hồ sơ AI đã lưu, không là đủ đề cương HUS. Câu trả lời còn dài so với yêu cầu liệt kê khái niệm. |
| Tiên quyết, RC24-009–012 |4 answered F2, không bật quyền F3. Giá trị giống nguyên dòng nguồn; trạng thái xác minh/cảnh báo vẫn giữ. Chi tiết bên dưới. |
| Câu cấp ngành001/017 và tương tự, RC24-013–016 |4 cần làm rõ mục tiêu/giới thiệu, nghề nghiệp hay danh mục. Không yêu cầu mã môn cho cả ngành. Đây là đúng hợp đồng hiện tại, chưa kết luận hỏi lại là trải nghiệm tốt nhất; nhóm cần đọc và quyết định. |
| Thi thật, phủ định, sai ngành, opt-out, phép lọc, chủ đề ngoài nguồn, RC24-017–024 |8 câu không tạo đáp án/citation sai. Phân biệt thiếu nguồn đánh giá chính thức, retrieval rỗng, guard, scope, quyền F3 và phép toán chưa hỗ trợ. Lời nhắc018 chưa sát nguyên nhân thiếu field đánh giá. |

### F2 giữ nguyên dữ kiện

| Môn/ngành | Nguồn và phản hồi |
| --- | --- |
| MAT2300 / Toán học |PDF QD3565-2023 trang9: ô tiên quyết `null`, trả **chưa rõ**; không suy thành “không có tiên quyết”. Quote vẫn4 tín chỉ. |
| MAT1202 / Toán tin |PDF QD3567-2023 trang10: giữ `MAT2505`, `draft_unverified`. |
| MAT1202 / KHMTTT |PDF QD3568-2023 trang11: giữ `MAT2505`, verified cấp dự án; response nói rõ không là chứng nhận của trường. |
| MAT3533 / KHDL |PDF QD3569-2023 trang11: giữ `MAT2406/` xuống dòng `MAT2323`, cảnh báo unresolved MAT2406. Không tự sửa mã hoặc diễn giải `/` thành AND/OR. |

Cả bốn câu đều giữ cảnh báo dữ liệu không kết luận người hỏi đủ điều kiện đăng ký.
31 citation trong toàn bộ run khớp quote/locator/review của dữ liệu canonical;
kiểm khớp kỹ thuật không thay review học thuật/đủ ý.

## Lỗi quan sát được và hướng sửa tiếp

**RC24-002:** “Sau khi tốt nghiệp ngành Toán tin, em có thể làm việc ở những đâu?”
route đúng F1/careers, top5 đã có nguồn nghề nghiệp. Trace guard cho thấy
`specific = ["em"]`, từ này không có trong body nguồn nên bị từ chối.

Diagnostic bổ sung, tách khỏi run đã lưu:

- Giữ nguyên câu gốc: `no_information/evidence_rejected`.
- Chỉ bỏ “em ”: `answered`, `specific=[]`.
- Cách hỏi đã từng hoạt động “Học xong ngành Toán tin thì làm việc ở đâu?”:
  `answered`.

Hướng sửa khi triển khai: nhận xưng hô theo vị trí/ngữ cảnh câu hỏi và thêm
regression tương tự/negative; giữ tên riêng, thuật ngữ, điều kiện và phủ định.
Không bỏ token toàn cục hoặc nới kiểm nội dung. Không sửa run này để đổi kết quả.

**RC24-018:** “MAT2300 thi gi?” vẫn được nhận là câu đánh giá, không xóa `thi`.
Không có field tương ứng nên retrieval rỗng; lời nhắc kiểm tên/mã môn chưa nói
đúng rằng dữ liệu đánh giá còn thiếu. Có thể cải thiện thông báo riêng sau.

Hai câu phủ định019/020 bị guard từ chối, không mượn câu “Nếu có đủ điều kiện…”
trong nguồn Toán học để khẳng định trường hợp **chưa** đủ điều kiện. Câu sai
ngành021 nêu đúng KHDL/Toán học; opt-out022 yêu cầu quyền F3; lọc023 không dùng
số toàn danh mục thay cho số môn sau lọc; chủ đề lượng tử024 không được bịa.

## Gói nhóm review và phần còn lại

- Mở [đáp án/quote](RAG_ROUTER_CONTENT_RESPONSES_2026_11_15.md), điền tên/ngày,
  đúng ý/đủ ý/dữ kiện/citation/lỗi trong
  [CSV nhóm trả](../data/hus/review/router_content_dev_20261115_r1/review_group_return.csv).
  Đọc cả câu từ chối/làm rõ; bổ sung câu tự viết ở cột `new_group_question`.
- Có [nhận xét AI riêng cho24 câu](../data/hus/review/router_content_dev_20261115_r1/AI_review.csv),
  không điền thay cột người thật.24 xác nhận nhóm còn trống/pending.
- Nếu chọn sửa xưng hô hoặc lời nhắc, thêm regression trước, giữ scope/điều kiện/
  quyền F3 rồi lưu kết quả mới. Guard/context tập trung vẫn là thiết kế chưa triển khai.
- Gemini cần thống nhất ngân sách mới, kể cả call hiểu ý định. Lượt này không đọc
  key/file môi trường, không dùng provider giả lập hoặc thật, không đổi cấu hình demo.

## Khả năng đối chiếu

Đã lưu câu hỏi/kỳ vọng chức năng AI và inventory nguồn **trước** chat inference;
không sửa theo kết quả. Kiểm kỹ thuật chức năng23/24 chỉ là đối chiếu dataset/
field/trạng thái/quyền, **không phải độ chính xác nội dung23/24**.

- [Pack/cases](../data/hus/evaluation/router_content_dev_20261115_r1/cases.json),
  [nguồn](../data/hus/evaluation/router_content_dev_20261115_r1/sources.json),
  [protocol/code pins](../data/hus/evaluation/router_content_dev_20261115_r1/protocol.json).
  Manifest SHA256 `9aa9028e4538a00a32b80db7692b3560cbed43281d031a44b4dcf0c32fd347e7`.
- [Run/response/retrieval/checks](../data/hus/evaluation/runs/router_content_dev_20261115_r1/observations.json).
  Manifest SHA256 `2bed42ef7d5902e85193d1d0250107521f4bed1d2bc03744950b8d3037466e2c`.
- [Diagnostic riêng](../data/hus/review/router_content_dev_20261115_r1/diagnosis.json)
  có trace ba câu đối chiếu và inventory học tiếp Toán học.
- 63 file được bảo vệ của dữ liệu/index/CURRENT và các run cũ giữ hash. Không
  sửa runtime, gold, run20, run latency hoặc IF2 live; không chấm lại điểm cũ.
  Không chạy lại suite rộng khi chưa sửa code;53/636 test của lượt router trước
  vẫn là kết quả lịch sử, không cộng vào24 quan sát này.

[Tiến độ và bước tiếp theo](RAG_PROGRESS_AND_NEXT_PLAN.md)
