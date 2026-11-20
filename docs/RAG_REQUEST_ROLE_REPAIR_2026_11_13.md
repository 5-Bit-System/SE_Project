# Sửa cú pháp hỏi và phạm vi vai trò nghề nghiệp — 13/11/2026

Nhánh `hus-llm-rag`, nền `f61b0fd` + WIP, chỉ làm local. Đã triển khai yêu cầu
sau [review bốn ca](RAG_A7S_FOUR_CASE_REVIEW_2026_11_13.md), giữ v4/lexical/LLM tắt.

## Thay đổi

- Nhận cụm hỏi “nêu/ghi/liệt kê kèm điều kiện nào/gì/ra sao”; cần đoạn điều kiện
  cùng source scope. Điều kiện thật, kể cả phủ định theo sau, vẫn cần có trong
  body. Không thêm `kem` vào nhóm từ bỏ qua hoặc sửa câu trích.
- Nhận chủ ngữ tài liệu/nguồn/ngành/chương trình với tên ngành đã biết và đuôi
  hỏi “được trình bày ra sao/như thế nào/thế nào”. Năng lực trình bày, lập trình
  máy bay và yêu cầu phủ định không được đổi thành cú pháp yêu cầu trả lời.
- Nhận vai trò nghề nghiệp tại trường/đại học/viện trong cấu trúc hỏi phù hợp.
  Vai trò của nhà trường, viện, doanh nghiệp hoặc môn học vẫn được phân biệt.
- Mỗi nơi làm việc được yêu cầu, kể cả danh sách có dấu phẩy, cần evidence
  trong cùng source scope. “Viên nghiên cứu” và “thị trường/môi trường” không
  được dùng làm bằng chứng cho viện/trường. Metadata title không thay body.

Runtime chỉ đổi `app/hus/answer_support.py` và `app/hus/question_routing.py`;
regression trong `tests/hus/test_request_role_language.py`. Không đổi ranking,
schema response, dữ liệu, gold hoặc ngưỡng. Các phép kiểm vẫn là luật lexical
có giới hạn, không chứng minh entailment cho mọi cách diễn đạt.

## Kiểm chứng

Đã viết test trước runtime: lượt đầu 24 fail/28 pass; các ranh giới viện/viên,
phủ định và review đều có lượt fail trước khi sửa. **77 regression mới** cùng
nhóm support/scope/routing hiện đạt **233 test**; các nhóm có giao nhau, không
cộng thành tổng. Scoped Ruff đạt.

Một lượt review code bằng AI ở ngữ cảnh riêng tìm bốn điểm Important: trường
với thị trường, danh sách nơi làm việc có dấu phẩy, chủ thể nhà trường và điều
kiện phủ định. Đã thêm cặp regression và sửa cả bốn. Đây không là review học vụ
hoặc nghiệm thu độc lập của người thật.

Bốn request A7S đã lộ được chạy riêng như **diagnostic dev**, đều `answered`,
giữ canonical quote/citation; Q013 giữ “tùy theo năng lực”. Q015 trả cả các
đoạn nghề nghiệp của cùng nguồn, không chỉ vai trò tại trường/viện; chưa đánh
giá độ ngắn gọn. Không tạo run A7 mới hay chấm lại gold.

**2.876/2.878 file cũ giữ SHA**; hai file thay đổi là runtime nêu trên. Toàn bộ
dữ liệu và artifact cũ giữ nguyên. Cached replay A7S tái hiện điểm đã seal:
**Recall 23/24, đủ ý 32/36, controls 12/12**. A7S đã dùng tuning nên là dev.

Pins A7S và L5 prepared r3 **không còn khớp code hiện tại** sau sửa; đó là thay
đổi được dự kiến, không sửa pins trong artifact cũ để làm khớp. Chưa prepare
L5 mới, không gọi Google/model-list/tokenizer, không đọc key hoặc `.env`.
Không stage/commit/push/PR/Actions/deploy.

Lượt offline toàn repository sau review: **3.058 pass, 1 fail, 2 skip,
90 deselected** trong 19 phút. **Không phải suite xanh toàn repository.**
Lỗi duy nhất là
`tests/hus/test_routing_diagnostic.py::test_exposed_dev_requests_preserve_facts_scope_and_consent[DEV-Q002]`:
gold dev cũ đòi `answered` cho câu hỏi đồng thời hệ chuẩn và tài năng, còn hợp
đồng scope hiện tại yêu cầu làm rõ một hệ trước search. Đã tái hiện đúng lỗi
trên bản trước lượt sửa, có hash ba file support/routing/answering khớp snapshot
ban đầu. Giữ nguyên test/gold/run/review; cần review hợp đồng test cũ riêng,
không bỏ guard để làm xanh suite.

Hai test skip do Windows không cho tạo symlink: `test_passage_artifact` và
`test_vector_index_contract`; các nhánh path/redirected-root khác vẫn được kiểm.
Có ba warning: Starlette/httpx cũ và hai lỗi decode của thread đọc subprocess
ở `tests/catalogs/test_metadata_builder.py`. Không nhận warnings là đã xử lý.

[Receipt và kết quả từng nhóm](../data/hus/qa/20261113/request_role_repair_r1/report.json),
[bằng chứng lỗi có trước](../data/hus/qa/20261113/request_role_repair_r1/baseline_legacy_failure.json).
Manifest: `f98e47800fc79bb255bdf81e28059f4169aac4df600dda6fd1cd7c5900583cd4`.
Không dùng lượt toàn suite bị ngắt trước đó làm bằng chứng đạt.

## Tiếp theo

Freeze bộ A7 khác tối thiểu 48 câu/12 mỗi ngành, source/gold trước inference,
ghim code/data/config và khai báo exposure/reviewer. Routed Recall phải gồm
no-call, cùng facts/citation/đủ ý/controls; AI review không là nghiệm thu độc lập.
Nếu chọn L5, prepare/preflight mới trước, rồi xin ngân sách riêng trước mọi
Google call. Giữ LLM tắt và chưa xét L6 từ diagnostic/test mock/fallback.
