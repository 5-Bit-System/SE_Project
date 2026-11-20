# Đối chiếu20 câu tự nhiên: lexical và hybrid v4

Ngày14/11/2026 · nhánh `hus-llm-rag` · đồ án sinh viên.

**Kết quả chính:** hai chế độ cùng9 answered/6 no-information/5 cần làm rõ. Trong bộ này chưa có câu được trả lời thêm nhờ hybrid.9 câu thực sự search có cùng tập top5; thứ tự đổi ở4 câu. Một đáp án đổi nguồn/edition và ít chi tiết hơn.

**Tác giả câu hỏi và review: Codex(AI).** Đây là20 câu nháp cho nhóm,5 mỗi ngành, không sao chép nguyên câu menu. Chưa có câu hỏi/review người thật do nhóm gửi; không gọi đây là bộ nhóm tự viết hoặc nghiệm thu độc lập. Bộ đã phơi lộ/tuning phải giữ làm dev.

## Cách đo và giới hạn

- Lưu câu hỏi, ý định kỳ vọng và packet nguồn trước inference; không đổi sau kết quả.
- Cùng snapshot v4/index/profile/code; một lần mỗi câu mỗi mode, thứ tự luân phiên. Cold preflight riêng. Không sửa router/guard/index hoặc chạy lại để lấy số đẹp.
- **Google0, LLM tắt:** đây là kiểm RAG, không phải Gemini live/used/fallback. Không sửa hoặc chấm lại run30 câu/A7 cũ.
- Lexical bình thường top5; hybrid20+20 gộp RRF lấy5. Đây là so sánh luồng vận hành, không phải ablation cùng ngân sách để quy công riêng cho embedding.
- Target của AI chỉ là đoạn canonical liên quan theo field/unit. Hit target/answered không chứng minh entailment, đầy đủ ý hay độ đúng;001/017 còn ambiguity về ý hỏi.

## Số liệu vận hành

| Chỉ số | Lexical | Hybrid |
| --- | --- | --- |
| answered |9/20 |9/20 |
| no-information |6/20 |6/20 |
| cần làm rõ |5/20 |5/20 |
| có gọi retrieval |9/20 |9/20 |
| không gọi retrieval |11/20 |11/20 |
| min/median/max RAG của9 câu có search |0,003/0,007/0,032s |5,734/6,058/6,566s |

Cold hybrid riêng **155,333s**. Không gộp11 câu không search vào median để làm hybrid có vẻ nhanh;3 câu trong nhóm đó trả dữ kiện F2 trực tiếp,8 câu còn lại bị chặn/làm rõ. Mỗi câu chỉ có một quan sát thời gian/mode trên cùng máy Windows; chưa gồm Google/UI/network, chưa là benchmark ổn định hoặc latency đã tối ưu.

## Những gì học được

1. **Router/cú pháp là chỗ chặn lớn:**002/005/008 chứa “thì”, bị accent-fold thành `thi` rồi route F3/suggested_assessment. Diagnostic riêng bỏ “thì” vẫn ra route unknown, nên sửa một token chưa đủ. Không xóa `thi` toàn cục vì vẫn cần nhận biết câu hỏi thi thật.004 chưa hiểu “gặp các khái niệm gì”;001/017 cần làm rõ field/cấp ngành trước kết luận sai routing.
2. **Đếm môn chưa được triển khai:**005 còn bị route assessment trước khi tới nhãn unsupported-operation. Packet tính90 mã duy nhất trong danh mục Toán học v4 để tham khảo, không có nghĩa mọi sinh viên phải học90 môn và chưa được nối vào chat.
3. **Có target nhưng guard chặn:**006 introduction rank1 và019 unit Khái quát/điều chuẩn rank3 đều đã lấy được ở cả hai chế độ. Cần review request grammar/paraphrase và bằng chứng toàn câu; không đổ cho Chroma/BM25.
4. **Chưa có lợi ích retrieval đo được trong bộ này:**9 tập top5 giống nhau; 009 target từ rank1 thành2,019 vẫn rank3. Nhiều scope chỉ có1–5 đoạn nên semantic không có nhiều ứng viên mới để bổ sung. Không suy ra hybrid luôn kém trên mọi corpus; bộ này nhỏ, phần lớn bị giới hạn bởi routing/guard.
5. **HN20-012 cần quy tắc nguồn/edition:** lexical chọn DOCX2023 có bậc và các lĩnh vực học tiếp; hybrid chọn PDF2015 chỉ nêu bậc. Câu “những hướng nào” có thể cần lĩnh vực, nên bản hybrid ít chi tiết hơn. Câu chưa ghim edition; không ép ranking theo target, đổi gold hoặc coi hai đoạn tương đương. Cần review wording/edition và chính sách chọn nguồn khi không nêu phiên bản.
6. **Ý trả lời còn dư:**009/014 có nội dung được hỏi nhưng kèm tổng quan/unit khác. F2 trả đúng4/3/3 tín chỉ ở003/013/018, giữ trạng thái review và warning; hỏi tiên quyết008 chưa tới đúng F2.010/015/020 giữ biên scope/opt-in/môn không có.

## Từng câu và thời gian

Đây là trạng thái hệ thống, không phải bảng điểm chính xác. Ý nhận xét là AI sơ bộ.

| ID | Câu hỏi tự nhiên | Kết quả hai mode | L/H giây | Nhóm nguyên nhân/ghi chú |
| --- | --- | --- | --- | --- |
|HN20-001 |Ngành Toán học đào tạo người học theo định hướng nào? |no_information; evidence_rejected |0.007/5.813 |routing_review |
|HN20-002 |Tốt nghiệp Toán học thì có thể làm việc ở những đâu? |needs_clarification; clarification_required |0.032/0.030 |routing_grammar |
|HN20-003 |Môn Đại số tuyến tính 1 có số tín chỉ là mấy? |answered; answered |0.114/0.070 |answered_facts |
|HN20-004 |Tôi muốn biết trong môn Đại số tuyến tính 1 sẽ gặp các khái niệm gì? |no_information; routing_unknown |0.002/0.002 |routing_unknown |
|HN20-005 |Nếu tính mỗi mã học phần một lần thì ngành Toán học có bao nhiêu môn trong danh mục? |needs_clarification; clarification_required |0.034/0.028 |routing_and_operation |
|HN20-006 |Cho mình một bức tranh khái quát về ngành Toán tin. |no_information; evidence_rejected |0.003/6.352 |guard_after_target |
|HN20-007 |Học xong Toán tin có thể tiếp tục học lên những bậc nào? |answered; answered |0.004/5.817 |answered_with_conditions |
|HN20-008 |Muốn học Lập trình hướng đối tượng thì phải hoàn thành môn nào trước? |needs_clarification; permission_required |0.029/0.020 |routing_wrong_consent |
|HN20-009 |Trong nội dung MAT1202, các đối tượng và kế thừa được giải thích thế nào? |answered; answered |0.032/6.556 |answered_broad |
|HN20-010 |Ngành Khoa học dữ liệu có định hướng nghề nghiệp nào? |no_information; scope_conflict |0.002/0.002 |expected_scope_boundary |
|HN20-011 |Người tốt nghiệp KHMTTT có thể đảm nhiệm những công việc gì? |answered; answered |0.032/5.837 |answered_source_scoped |
|HN20-012 |Nếu muốn học tiếp sau KHMTTT thì có những hướng nào? |answered; answered |0.006/5.734 |edition_policy_review |
|HN20-013 |Cho mình biết số tín chỉ của môn Phương pháp nghiên cứu khoa học. |answered; answered |0.090/0.055 |answered_facts |
|HN20-014 |Nội dung MAT1204 hướng dẫn đặt câu hỏi nghiên cứu và giới hạn phạm vi ra sao? |answered; answered |0.032/6.566 |answered_broad |
|HN20-015 |Giải thích nội dung MAT1204 giúp mình. |needs_clarification; permission_required |0.020/0.018 |expected_F3_permission |
|HN20-016 |Theo tài liệu ngành, sinh viên KHDL có thể làm những loại công việc nào? |answered; answered |0.005/6.058 |answered_source_scoped |
|HN20-017 |Bạn mô tả ngắn gọn ngành Khoa học dữ liệu đang học những lĩnh vực gì được không? |needs_clarification; clarification_required |0.020/0.026 |routing_ambiguity |
|HN20-018 |MAT3533 được ghi nhận bao nhiêu tín chỉ trong khung chương trình? |answered; answered |0.052/0.097 |answered_facts |
|HN20-019 |Nội dung MAT3533 lý giải chuyện mô hình học thuộc dữ liệu cũ nhưng dự đoán kém trên dữ liệu mới như thế nào? |no_information; evidence_rejected |0.032/6.291 |guard_after_target |
|HN20-020 |Mã MAT9999 có số tín chỉ là bao nhiêu? |no_information; evidence_unavailable |0.019/0.020 |expected_missing_course |

## Việc tiếp theo

- Review và sửa chung “thì/thi”, cách hỏi nghề nghiệp/tiên quyết/nội dung ngành và môn; thêm regression tương tự/negative, không vá theo QID.
- Chốt ý định/cấp truy vấn, phép đếm F2 và quy tắc edition trước khi kết luận cần đổi retrieval. Review006/019 để điều chỉnh guard có bằng chứng, không bỏ kiểm đủ ý.
- Profile riêng chi phí encoding/Chroma/identity/inventory trước tối ưu latency. Không bỏ kiểm pin/scope chỉ để chạy nhanh; giữ hybrid selectable và lexical đối chiếu.
- Nhóm đọc đủ20 đáp án/nguồn, điền người/ngày và ý kiến riêng. Google tiếp theo cần budget mới; nếu sửa code thì đo lại bằng run mới, giữ kết quả này.

[Đáp án/nguồn/trace dễ đọc](RAG_HYBRID_NATURAL20_RESPONSES_2026_11_14.md) · [CSV nhóm điền](../data/hus/review/hybrid_natural20_20261114_r1/review_group_return.csv) · [Câu/kỳ vọng đã lưu trước đo](../data/hus/evaluation/hybrid_natural20_20261114_r1/cases.json) · [Packet nguồn trước đo](../data/hus/evaluation/hybrid_natural20_20261114_r1/source_packets.json) · [Kết quả raw đã seal](../data/hus/evaluation/runs/hybrid_natural20_local_20261114_r1/observations.json).
