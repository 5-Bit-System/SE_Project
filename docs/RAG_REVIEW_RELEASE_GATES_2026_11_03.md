# Holdout mới, phép đo ghim phiên bản và điều kiện xuất bản

**Chính sách hiện hành — 03/11/2026:** bạn đã bỏ điều kiện người thật review,
chấp nhận review AI cho đợt này. Phần quy trình người review bên dưới là lịch sử,
không còn là điều kiện chặn phép đo AI. Kết quả dùng `reviewer_kind=ai`, không
tính thành chữ ký người thật hoặc chứng nhận holdout độc lập. Xem
[gói review AI](../data/hus/evaluation/holdout_v2_ai_review_v1/README.md).
Bản gốc/worksheet/baseline giữ nguyên; gold sửa ở bản dẫn xuất trước khi đo.
Lọc ngành/phiên bản, bằng chứng, review nguồn và AI opt-in vẫn áp dụng.
Điều kiện xuất bản/triển khai và duyệt nguồn official vẫn tách riêng.

**Kết quả theo chính sách mới:** review AI56/56, sửa ba gold/rubric ở bản dẫn
xuất; đo trên snapshot ghim:Recall16/20=80%,F2 strict11/16,từ chối sai20/36.
Gate người thật đã bỏ; gate chất lượng vẫn chưa đạt. Xem
[báo cáo và nguyên nhân lỗi](RAG_AI_REVIEW_AND_MEASUREMENT_2026_11_03.md).
Đánh giá này đã lộ, không chứng nhận holdout độc lập; các bảng bên dưới mô tả
thời điểm chuẩn bị trước khi đổi chính sách, không phải trạng thái mới.

## Quy trình người review trước khi đổi chính sách (lịch sử)

Ngày03/11/2026, local `crawldata`. Bạn đã nhận làm reviewer; **chưa có quyết định
review thật từng câu**. Chuẩn bị kỹ thuật không thay nghiệm thu của người review.
Chưa commit/push, chưa chọn máy chủ hoặc triển khai production.

## Gói để bạn bắt đầu review

- [Hướng dẫn và mẫu review](../data/hus/evaluation/holdout_v2_review/README.md).
- [Worksheet CSV](../data/hus/evaluation/holdout_v2_review/review_worksheet.csv):56 dòng,
  chứa câu hỏi, đáp án nháp, evidence IDs, hàng xóm dev và các ô bạn cần điền.
- [Gói đọc nguồn/đáp án](../data/hus/evaluation/holdout_v2_candidate/reviewer_packet.md).
- [Evidence gốc](../data/hus/evaluation/holdout_v2_candidate/evidence.jsonl),
  [gợi ý thay thế](../data/hus/evaluation/holdout_v2_review/alternative_evidence_candidates.jsonl).
- [Đối chiếu với các bộ cũ](../data/hus/evaluation/holdout_v2_review/overlap_v2/report.json).

56 câu/14 mỗi ngành,44 evidence IDs. Nhóm:12 F1,16 F2,8 F3 bật AI,8 thiếu nguồn,
8 ngoài phạm vi,4 chưa opt-in. Tác giả là AI và biết runtime/dev; không tuyên bố
độc lập người soạn. Bạn cần loại/sửa câu trùng ý hoặc thiên theo cách sửa runtime,
không chỉ dựa kết quả0 trùng chữ. Có8 gợi ý nguồn thay thế cùng scope/edition/field;
chưa được người thật duyệt tương đương ý. Không coi không tìm thấy gợi ý là không
tồn tại nguồn khác. Không tự nâng gold/review để giúp điểm số.

Đã đối chiếu99.344 cặp với1.774 occurrence câu hỏi cũ (có bản sao ở nhiều file),
gồm1.050 chuỗi development duy nhất và120 prompt literal từ AST test.0 exact duplicate,
0 strong lexical flag theo ngưỡng khai báo; **không chứng minh không trùng ý**.
Mỗi câu vẫn có3 hàng xóm gần nhất để bạn mở và tự xét.
AST không bao phủ mọi f-string/template động; reviewer cần xem thêm các test có
câu được dựng động. Audit v1 được giữ làm lịch sử; v2 bổ sung keyword literal
`question=` sau kiểm tra kỹ thuật, không chạy RAG hoặc chọn lại câu để nâng điểm.

Copy template sang file review riêng. Accept cần tên thật, thời gian thực có
múi giờ, độc lập với tuning bộ mới, kiểm nguồn/đáp án/semantic overlap/alternative
evidence và lý do. Reject/revise/pending không tính vào40. Ít nhất40 accepted,
bốn ngành tối thiểu8/ngành và đủ sáu nhóm trước khi đề nghị bạn xác nhận freeze.
Không sửa frozen candidate để hợp thức hóa kết quả; thay câu/gold thì tạo bản mới.

```powershell
python -X utf8 -m tools.validate_hus_holdout --pack data/hus/evaluation/holdout_v2_candidate
python -X utf8 -m tools.validate_hus_holdout_review --reviews <file-review-cua-ban.csv> --evidence-catalog data/hus/evaluation/holdout_v2_review/evidence_catalog.jsonl
```

Hai lệnh chỉ kiểm file, không hỏi RAG. Công cụ kiểm các lời khai review và binding,
không xác minh danh tính hoặc ký thay bạn; `independent_holdout_certified=false`.

## Phép đo sau khi bạn review và chốt

Chưa chạy bộ H2 qua app hoặc retriever. **Mục tiêu Recall@5≥90% trên holdout độc
lập vẫn chưa đạt/chưa được đo.** Điểm39/40 của dev sau sửa không thay kết quả này.

1. Bạn chốt câu accepted và mọi nguồn thay thế hợp lệ. Tạo subset mới>=40 câu;
   ghim hash request/gold/evidence/review/overlap, không chọn ca dựa prediction.
2. Ghim code/UI/dependency lock/CURRENT/release/registry/binary. Snapshot chuẩn bị
   ở [runtime_snapshot.json](../data/hus/evaluation/holdout_v2_review/runtime_snapshot.json).
   Base Git là1287e2a, code sửa còn dirty; dùng hash thực, `tested_commit=null`,
   không gọi base commit là commit đã nghiệm thu. Nếu snapshot đã đổi, ghi rõ và
   review ảnh hưởng trước đo; không dùng receipt cũ cho code mới.
3. Gửi CHỈ request vào app độc lập. Lưu đủ prediction, trace, HTTP và identity
   trước bước chấm; không dùng category/field/gold để điều khiển router.
4. Chấm toàn bộ tập đã chốt, không bỏ lỗi/ca từ chối. Reviewer kiểm nguồn ngữ nghĩa,
   nguồn thay thế và các ca tự động chưa kết luận. Lưu artifact mới, không ghi đè.

| Nhóm báo cáo | Định nghĩa cần tách rõ |
| --- | --- |
| Routing | Tỷ lệ dataset/intent/field đúng theo gold đã duyệt; đếm riêng không gọi search và gọi nhầm field. F2 là lookup, không bắt buộc search |
| Retrieval | Routed Recall@5 trên toàn bộ F1/F3 đủ điều kiện, gồm ca router chặn. Báo thêm Recall@5 có điều kiện trong ca đã search, số filter loại evidence; không thay mẫu số chính bằng mẫu dễ hơn |
| F2 | Đúng facts/mã/ngành/version/raw rows/review, có đủ source occurrences; không gộp vào Recall@5 |
| Citation/source support | Tách quote/page/hash/link integrity với việc nguồn thực sự hỗ trợ đủ ý; chấp nhận nhóm nguồn thay thế tương đương do reviewer duyệt, không buộc mọi nguồn tương đương đều nằm top5 |
| Abstention | Từ chối đúng trên ca thiếu nguồn/ngoài scope, yêu cầu opt-in đúng, từ chối sai trên ca có đáp án; HTTP error là lỗi riêng |
| Scope | Sai ngành/mã/version, leakage facts/citation/AI khi không được phép; báo số ca và mẫu số, không suy0 lỗi quan sát thành chứng nhận mọi trường hợp |

Giữ null cho semantic metrics chưa được người thật chấm. Nếu xem lỗi rồi tuning
trên holdout này, ghi exposed và chuẩn bị holdout khác cho nghiệm thu tiếp theo.

## Regression và bằng chứng đang có

Runtime hiện không đổi kể từ [phép đo dev/sửa routing](RAG_ROUTING_FIXES_2026_11_03.md).
Receipt đó ghi1.444 Python offline pass/90 deselected,50 Chromium,5 Node citation;
API/UI/PDF/hash,đổi ngành khi chờ/reset opt-in đã kiểm. Đợt chuẩn bị review này
chỉ kiểm công cụ/data mới; không ghi các số cũ thành test vừa chạy lại.

Sau phép đo holdout đã duyệt, chạy regression lại trên đúng snapshot cuối:
offline suite,API source/error/boundary,Node citation và Chromium demo smoke.
PDF phải đúng binary/hash/trang (gồm13/12 cùng PDF); đổi ngành/phiên bản khi reply
đang chờ không nhận response/citation cũ; AI opt-in reset và mặc địnhfalse.
Nếu gắn UI sản phẩm thì cần nghiệm thu auth/CSRF/Origin/binding/context riêng.

## Nguồn và điều kiện xuất bản/production

[Gói review nguồn tiếp tục](RAG_SOURCE_REVIEW_FOLLOWUP_2026_11_03.md) có worksheet106
nguồn,37 raw thiếu,6 blocker và các identity/edition decisions.19 ảnh trang được
AI kiểm thêm, không phải chữ ký học vụ. Giữ official F3 và candidate chưa duyệt
ngoài mặc định. Chỉ các nguồn cần cho release dự kiến mới chặn release đó; đề xuất
hoãn nguồn ngoài scope cũng cần người review chốt, không tự xóa archive/blocker.

| Gate | Trạng thái lúc chuẩn bị |
| --- | --- |
| >=40 câu được reviewer thật review/chốt | Chưa có;0/56 accepted |
| Đo holdout độc lập,Recall@5>=90%,source support/abstention đạt tiêu chí đã chốt | Chưa chạy,không suy từ dev |
| Review nguồn cần cho phạm vi release | Còn pending;6 blocker chưa đóng |
| Xuất bản code/data/docs | Chưa làm; theo điều kiện bạn đặt, chỉ sau nghiệm thu, qua feature branch/PR/Create a merge commit |
| Đích production/config/bảo vệ điểm vào | Chưa chọn; không đưa demo loopback công khai thay endpoint được bảo vệ |
| Giám sát và activation/rollback ở đích thật | Chưa nghiệm thu;local P1-4 chỉ hai process cùng release |

Sau nghiệm thu mới chốt đích/OS/domain/TLS/quyền truy cập,commit/CI/artifact thực,
ngưỡng theo số liệu vận hành và retention log metadata. Phải diễn tập readiness,
hash/citation failures,outage,chuyển traffic và rollback tại đích thật; nếu nâng
release phải kiểm dữ liệu mới/cache/review withdrawal, không dùng thử đổi process
cùng release làm bằng chứng nâng dữ liệu. Crawl/build ở ngoài request/startup.
Không cấp quyền production, commit/push hay kích hoạt trong đợt chuẩn bị này.
