# A7S — review bốn ca trước chọn sửa

Ngày **13/11/2026**, nhánh `hus-llm-rag`, nền `f61b0fd` + WIP.
Đã xác định nguyên nhân của ba refusal và một route sai từ exact response,
trace/source đã seal cùng code router/guard. **Chưa sửa runtime hoặc chấm lại**:
giữ Routed Recall@5 **23/24**, đủ ý **32/36**, controls **12/12**.

**Lượt triển khai sau review:** [sửa chung cú pháp/role scope](RAG_REQUEST_ROLE_REPAIR_2026_11_13.md)
đã thay runtime và thêm regression. Phần dưới là kết quả review trước sửa;
receipt/điểm cũ giữ nguyên, A7S nay là dev và pins cũ không còn khớp runtime.

[Receipt](../data/hus/qa/20261113/a7s_four_case_review_r1/report.json),
[diagnostic và các cặp wording](../data/hus/qa/20261113/a7s_four_case_review_r1/diagnostic.json),
[negative checks](../data/hus/qa/20261113/a7s_four_case_review_r1/negative_probes.json),
[yêu cầu regression cho lượt sửa](../data/hus/qa/20261113/a7s_four_case_review_r1/regression_requirements.json).

## Nguyên nhân đã đối chiếu

| Ca | Bằng chứng và nguyên nhân |
| --- | --- |
| **Q013 — KHDL careers** | Target rank1, đúng field/edition unknown. Trong `supported_hits`, yêu cầu “được nêu kèm điều kiện nào” còn token **`kem`**, không có trong body. Cùng tuple hit, bỏ riêng “kèm” thì guard chấp nhận; giữ “kèm” vẫn bị chặn. “Nêu” không phải token thiếu trong ca này. Điều kiện nguồn “tùy theo năng lực” có thật và không được bỏ khỏi câu trả lời tương lai. |
| **Q027 — Toán học học tiếp** | Target2015/standard rank1, scope filter giữ đúng hit. “Tài liệu ngành Toán học trình bày …” còn token **`bay`**. `COMMAND_SYNTAX` chỉ nhận mệnh lệnh đầu active clause; `_presentation_syntax` chưa xử lý kiểu chủ ngữ nguồn ở F1 này. Cùng hits, mệnh lệnh “hãy trình bày …” hoặc câu hỏi trực tiếp được chấp nhận. |
| **Q037 — Toán Tin objectives** | Target2015/standard rank1 và đúng scope. Đuôi bị động “được trình bày ra sao” cũng để lại **`bay`**; câu trực tiếp/mệnh lệnh tương ứng qua guard trên cùng hits. Đây là lỗi phân biệt cách hỏi với dữ kiện về năng lực trình bày, không phải thiếu target. |
| **Q015 — KHDL vai trò tại trường/viện** | `CAREER_TERMS` chưa có mẫu này; `role_at_work` chỉ nhận doanh nghiệp/công ty. Không thỏa nhánh careers, chữ “ngành” làm rơi xuống introduction; search bị filter introduction. Guard chấp nhận các đoạn giới thiệu vì yêu cầu từ vựng còn lại đã trung hòa, nhưng reply không trả vai trò nghề nghiệp. Kiểm target careers riêng bằng direct guard thì được chấp nhận; đây chỉ là can thiệp diagnostic, không phải retrieval hoặc đáp án mới. |

Code liên quan: [answer_support.py](../app/hus/answer_support.py)
(`COMMAND_SYNTAX`, `_presentation_syntax`, `supported_hits`) và
[question_routing.py](../app/hus/question_routing.py)
(`CAREER_TERMS`, `role_at_work`, fallback introduction trong `question_intent`).

## Phạm vi kiểm và hướng sửa cần giữ

Đã chạy **20 probe guard, 11 probe router và 8 direct guard checks bổ sung**.
Tái dựng tuple hit từ đúng ID/score/matched terms đã lưu; không gọi search hoặc
answerer. Dùng tracing local để ghi query sau scope/syntax, tokens bắt buộc,
tokens thiếu và hit còn lại. Không sửa hàm đang chạy hoặc monkeypatch luật cho
ra kết quả mong muốn. Các wording và nguồn đã lộ, reviewer root AI/human0.

Các đối chứng cho thấy đây là vấn đề chung của cú pháp, không cần luật theo QID.
Trong lượt sửa sau cần giữ các ranh giới sau:

- Chỉ nhận cụm hỏi về điều kiện đi kèm như request grammar trong ngữ cảnh phù
  hợp; vẫn giữ điều kiện thật trong nguồn. Không thêm từ đơn `kem` vào danh sách
  bỏ qua toàn cục hoặc xóa qualifiers khỏi câu hỏi.
- Phân biệt trình bày của nguồn/cách yêu cầu trả lời với **năng lực trình bày
  báo cáo** được hỏi như dữ kiện. Không trung hòa `bay` toàn cục: negative
  “lập trình máy bay” vẫn bị từ chối trên nguồn chỉ nói lập trình viên.
- Nhận vai trò nghề nghiệp tại trường/đại học/viện trong đúng cấu trúc hỏi.
  Không biến “vai trò của trường/viện/doanh nghiệp trong đào tạo” hoặc vai trò
  của một môn trong chương trình thành câu hỏi việc làm của sinh viên.
- Giữ edition/hệ và bằng chứng body: negative edition2015 trên source unknown,
  hệ CLC trên source unknown, lượng tử,997, chứng nhận ISO/kinh nghiệm đều không
  được mở qua guard. Không bỏ scope hoặc ghép các nguồn khác nhau để phủ câu hỏi.
- Thêm regression tương tự/negative trước khi sửa runtime; kiểm thêm negation,
  workplace/exclusion và nhiều ý độc lập. Probe router không tự chứng minh
  câu hỏi có bằng chứng để trả lời; chọn đúng careers vẫn cần source guard.

39 probe/check này là diagnostic đã lộ, **không phải 39 test regression mới**,
phép đo A7 mới hoặc bằng chứng chất lượng sau sửa. Không suy số câu sẽ đạt sau
một thay đổi chưa triển khai; không đổi source/gold để sửa điểm.

## Toàn vẹn và bước tiếp theo

**2.859/2.859 file cũ giữ SHA**; candidate, run/gold/review A7S/A7F nguyên vẹn.
Cached replay measurement/overlay A7S và overlay A7F tái hiện được, không
answerer/search/provider/network; pins A7S và prepared L5 r3 vẫn khớp hiện tại.
Không có runtime change nên không lặp suite runtime/LLM hoặc thêm test repository
chỉ để ghi nhận diagnostic. LLM giữ tắt, Google diagnostic1call chưa được duyệt;
không stage/commit/push/PR/Actions/deploy.

Receipt manifest: `cf32c1c557daf0bcccdb65fb4ae2044442aa25954b92f355a7879e2d198aa599`.

Review đã xong; bước tiếp theo là chọn sửa chung cú pháp request và phạm vi
vai trò nghề nghiệp, bắt đầu bằng regression tương tự/negative. A7S đã là nguồn
diagnostic lộ; nếu dùng kết quả này tuning thì giữ làm dev, freeze bộ khác sau
sửa và đo trên pins mới. Không dùng lại A7S để nghiệm thu bản sửa hoặc thay điểm
23/24–32/36–12/12. Review AI không là nghiệm thu độc lập/học vụ.
