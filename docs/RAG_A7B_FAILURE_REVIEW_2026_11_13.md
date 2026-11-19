# A7B — review 9 refusal và 2 control trước chọn sửa

Ngày **13/11/2026**, nhánh `hus-llm-rag`. Đã review đủ **11 ca** bằng request/response/trace đã lưu và code hiện tại. **Chưa sửa runtime, dữ liệu, test, gold, scorer hoặc run/review cũ.** Giữ A7B **Recall22/24, F2 facts12/12, đủ ý27/36, checker controls11/12, semantic controls10/12**. Đây là diagnostic root AI đã biết nguồn/output, human0, không nghiệm thu độc lập hay điểm mới.

[Receipt](../data/hus/qa/20261113/a7b_failure_review_r1/report.json) · [trace từng ca](../data/hus/qa/20261113/a7b_failure_review_r1/diagnostic.json) · [probe ngôn ngữ/negative](../data/hus/qa/20261113/a7b_failure_review_r1/probes.json) · [kiểm quan hệ cơ sở](../data/hus/qa/20261113/a7b_failure_review_r1/basis_boundary.json).

## Nguyên nhân đã đối chiếu

| Ca A7B | Điểm chặn thực tế | Hướng sửa có giới hạn nếu được chọn |
| --- | --- | --- |
| **Q001** | Target CLC/unknown/mốc2018 có rank1. Guard còn `specific={tuyen,vao}`, body thiếu `vao`: câu hỏi “bắt đầu tuyển sinh **vào** năm nào” không khớp cách ghi “từ năm2018”. Probe đổi riêng “vào” thành “từ” trên đúng hit cũ thì guard nhận. Không phải thiếu nguồn/variant hoặc lý do mượn mốc2012. | Nhận cụm hỏi mốc thời gian có giới hạn. Giữ năm/edition/CLC và dữ kiện địa điểm thật; không thêm `vao` vào stopword toàn cục. |
| **Q009/Q021/Q033/Q045** | Cả4 target objectives F3 có rank1. Câu ghi quyền AI ở một mệnh đề, sau đó “hồ sơ môn CODE… mục tiêu học tập…”. `AI_PROFILE_LOCATOR` chỉ nhận `trong/theo/từ hồ sơ AI tham khảo…`, nên còn `ho/so/tap`; body mỗi môn thiếu một phần các từ đó. Cả4 probe dùng locator AI đang được nhận đều qua guard trên cùng hit. | Nhận locator hồ sơ theo cấu trúc/ngữ cảnh F3 và “mục tiêu học tập” là cụm field khi phù hợp. Quyền API boolean vẫn quyết định; câu tự nói đã bật không cấp quyền. Giữ code/ngành/edition/nhãn AI; “lập hồ sơ”, số học hoặc chủ đề học tập thật vẫn là yêu cầu nội dung. |
| **Q014** | `_graduate_role_requested` thấy “vai trò công tác nào… ở các đơn vị trường” nhưng loại vì câu có `gioi thieu`, dù đó là **“Nguồn giới thiệu…”**. Sau đó classifier chọn introduction thay careers. Giữ nguyên câu nhưng đưa đúng target careers vào **direct guard diagnostic** thì guard nhận. | Phân biệt locator của nguồn giới thiệu với ý hỏi giới thiệu chương trình hoặc vai trò của trường. Không xóa `gioi thieu`/đổi field toàn cục, không chuyển năng lực môn học thành việc làm. |
| **Q015** | Router nhận `khả năng học tập nâng cao` là further_study; guard vẫn coi `tap` là yêu cầu từ vựng, trong khi quote viết “theo học sau đại học…”. Đổi sang “khả năng học tiếp” trong direct guard thì qua. | Đồng bộ cụm hỏi học tiếp giữa router và guard. Giữ bậc học, điều kiện, nơi và hoạt động nguồn; không trung hòa từ `tap` trong mọi lĩnh vực. |
| **Q027** | Đúng PDF2015/standard/target. Router nhận cụm học nâng cao mới, nhưng `learning_basis` của guard chỉ dùng `FURTHER_STUDY_TERMS` cũ. Kết quả **false** dù câu hỏi có “dựa trên” và source ghi “là tiền đề”; dư `dua/tren`. Đây không phải lỗi proof định dạng PDF. | Dùng cùng nhận diện yêu cầu further-study có giới hạn để bật kiểm quan hệ cơ sở. Vẫn đòi nguồn cùng scope nói rõ quan hệ tích cực; không chỉ bỏ `dua/tren` hoặc ghép danh sách kỹ năng bất kỳ. |
| **Q032** | Tên chủ đề content **“Dự báo và kiểm tra mô hình”** chứa `kiem tra`; field detector bắt cả content và suggested_assessment. Guard nhiều field làm rõ **trước search**. Đặt title trong ngoặc kép vẫn không giải quyết; câu yêu cầu content + assessment thật cũng đi cùng detector. | Nhận topic object trong câu hỏi content, giữ các mệnh đề yêu cầu assessment độc lập. Không bỏ `kiem tra` toàn cục, không cho content luôn thắng hoặc dùng code/QID đặc biệt. Cần regression cùng chủ đề và negative cho câu hỏi hai field thật. |
| **Q012** | `basic_reply` dùng tập chuỗi trùng toàn bộ: “Chào bạn” được nhận, “Chào bạn, chúc…” không được. Route null rồi trả hus_rag/no_information. Không phải lỗi retrieval hay LLM. | Nhận chào hỏi + lời chúc vô hại theo cấu trúc giới hạn. Không dùng prefix-only “chào…” để nuốt câu hỏi tín chỉ, điều kiện đăng ký, tài khoản hoặc hành động ở mệnh đề sau. |
| **Q036** | “Nội dung hai **chương trình**…” không có code nhưng route F3/content do keyword `noi dung`. `_answer` chặn thiếu code ở dòng121, trước kiểm nhiều hệ F1 ở dòng133. Vì vậy hỏi mã học phần thay vì làm rõ phạm vi so sánh CTĐT. | Phân biệt chương trình và môn trước lời làm rõ thiếu mã môn; trả đúng lý do cho nhiều scope chương trình. Không tự trả so sánh, hợp nhất hệ hoặc quyết định ca liệt kê DEV-Q002 đang mở. |

Các vị trí liên quan: [guard locator](../app/hus/answer_support.py#L83), [learning basis](../app/hus/answer_support.py#L236), [token coverage](../app/hus/answer_support.py#L367), [role detector](../app/hus/question_routing.py#L258), [field/route](../app/hus/question_routing.py#L322), [basic chat](../app/hus/chat.py#L22), [thứ tự guard trong answerer](../app/hus/answering.py#L104). Vị trí/hash thuộc code đã kiểm ở receipt; không là chứng minh hành vi sau một bản sửa tương lai.

## Probe và giới hạn chứng minh

- Tái dựng đúng hits/score/matched_terms và snapshot từ run, gọi trực tiếp guard cho **8 ca có search**; classifier probe cho11 ca. Không search lại hoặc gọi answerer/API, không dùng target làm input request runtime.
- **7 edited-question guard probe**, một direct-gold-source guard probe Q014, **14 router probe**, **6 basic-reply probe**, **5 guard boundary probe**. Đây là diagnostic, không test regression hoặc A7 mới; không dùng kết quả edited question để sửa câu hỏi/gold cũ.
- Q027 có thêm **4 probe**: thay “học tập nâng cao” bằng “học tiếp” nhưng giữ nguyên **PDF/edition2015/hệ chuẩn** thì guard nhận; thiếu quan hệ cơ sở, phủ định quan hệ hoặc sai edition đều bị từ chối. Hai counterexample nguồn là bản sao trong bộ nhớ, không ghi vào dữ liệu/source/gold. Probe trước có bỏ locator PDF được giữ trong lịch sử với giới hạn đã ghi; kết quả giữ đầy đủ locator xác định đây là vấn đề nhận diện quan hệ.
- Các negative vẫn giữ khác biệt: vai trò **của** tổ chức, mục tiêu giảng dạy của môn; content hai yêu cầu độc lập; nội dung **của** gợi ý đánh giá; câu chào kèm yêu cầu dữ kiện/hành động; yêu cầu chủ đề ngoài nguồn và phủ định nguồn. Không suy hữu hạn probe đã chứng minh giải pháp an toàn cho mọi cú pháp.

Guard từ vựng là lớp kiểm hỗ trợ, không chứng minh entailment học thuật. Một số từ còn dư có thể có nghĩa thật; giải pháp sau này phải dựa vào cụm/vị trí/chủ thể/phủ định và source scope, không xóa các từ gây fail để làm điểm xanh.

## Hợp đồng và điểm được giữ nguyên

**Q036:** checker hiện ghi status làm rõ là đạt, nên giữ controls11/12. Review nghĩa có thêm Q036 fail, giữ10/12 và hash exact response. Nếu muốn checker kiểm lý do làm rõ, cần hợp đồng/evaluator được ghim **trước phép đo mới**, không đổi scorer để chấm lại lượt này.

**A7R-Q025/Q037/DEV-Q002:** không chọn nhánh nguồn/định hướng/liệt kê-vs-so sánh mới. Câu source-scoped hoặc lịch sử hẹp của A7B không chứng minh các câu cũ đạt. Giữ assertion DEV-Q002, không xfail/skip, không mượn scope CLC hoặc gán unknown thành standard. Không sửa gold/run/review cũ.

A7B nay đã được dùng chẩn đoán và chuẩn bị hướng sửa: giữ làm **dev/exposed** nếu tiếp tục tuning. Sau bản sửa được chọn phải freeze **bộ khác ≥48 câu, 12 mỗi ngành**, nguồn/gold trước inference; Routed Recall@5 gồm no-call ≥90% cùng facts/citation/đủ ý/controls. Review AI vẫn không thành nghiệm thu độc lập.

## Kiểm chứng và bước sau

**3.014 file bảo vệ nguyên SHA**; runtime/tests/data/gold/scorer/run/review cũ không đổi. Cached replay A7B/A7R tái hiện điểm; A7B vẫn stale đúng test fixture đã sửa từ lượt trước, L5r5 vẫn stale. Không lặp suite vì không sửa runtime/test, không gọi Google hoặc đọc key/env/DB. Giữ v4/lexical/LLMoff, mọi budget Google đã hết; không stage/commit/push/PR/Actions/deploy.

Receipt manifest `a5976b33d87c9bcf51f2751b02099b3d8079a221b0372840d524099182b1898d`.

**Nếu chọn triển khai tiếp:** viết regression tương tự/negative trước cho các cụm mốc tuyển sinh, hồ sơ AI/mục tiêu học tập, học nâng cao/cơ sở; sau đó tách source locator, named-topic và programme-vs-course context, cuối cùng chào hỏi giới hạn. Kiểm opt-in/edition/hệ/phủ định/đủ ý và không nuốt yêu cầu phụ. Đây là đề xuất sau review; **chưa triển khai bản sửa** hoặc thay hợp đồng cũ.
