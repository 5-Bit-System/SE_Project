# Review guard, edition và độ gọn của đáp án — 14/11/2026

Đã đối chiếu năm ca với source inventory v4, trace lexical hiện tại và run
hybrid/lexical đã seal. **Đây là review/thiết kế của Codex(AI), chưa sửa runtime,
prompt hoặc validator; không phải review chuyên môn/nghiệm thu người thật.**
Không gọi Google cho bước này, không đổi data/index/ranking/metadata/gold cũ.

[Diagnostic riêng](../data/hus/review/guard_edition_design_20261114_r1/diagnostic.json)
ghi query còn lại sau tách grammar, `specific`, top5, inventory và quote/hash.
Không chạy lại hybrid; phần hybrid bên dưới lấy từ observations lịch sử.

## Kết luận từng ca

| Ca | Nguyên nhân đã kiểm | Hướng sửa chung trong thiết kế |
| --- | --- | --- |
|006 |Guard còn đúng2 yêu cầu lexical `khai`, `quat`, cả hai không có trong body. Inventory introduction Toán tin chỉ1 đoạn, edition/hệ unknown; top1 đã là đoạn giới thiệu liên quan. |Coi **toàn cụm request** “bức tranh khái quát về ngành” là câu yêu cầu tổng quan, chỉ trong intent introduction. Giữ tên ngành, mọi topic/điều kiện khác; không xóa `khai`/`quat` toàn cục hoặc đổi nguồn unknown. |
|019 |Guard còn `doan/kem/moi/thuoc/tren`, trong đó `kem/thuoc` không xuất hiện trong toàn raw top5. Unit “Khái quát và điều chuẩn” có ghi “có thể ghi nhớ nhiễu trong mẫu huấn luyện, làm sai khác tăng trên dữ liệu mới”, cùng quá khớp/điều chuẩn/độ phức tạp. |Xem cách nói đời thường như **ứng viên chủ đề quá khớp**, cần ánh xạ có điều kiện vào đúng nội dung môn và đoạn giải thích, không chỉ title/score. Không khẳng định mọi trường hợp dự đoán kém đều do quá khớp. Không nới guard chỉ để trả được ca này. |
|012 |Có5 đoạn:2015/standard,2023/standard,2019/high_quality,web unknown/high_quality vàweb unknown/unknown. Lexical chọn2023 có bậc **và lĩnh vực**; hybrid chọn2015 chỉ nêu bậc. |Giải quyết **nguồn + edition + hệ** trước sinh. Khi chưa ghim mà có nhiều scope, hỏi người dùng chọn; không chọn năm mới nhất hoặc top1 làm mặc định “đúng”. Unknown vẫn unknown. |
|009 |Guard chỉ còn `specific={'thua'}`. Các từ “đối/tượng” bị neutral hóa vì xuất hiện trong tên môn Lập trình hướng đối tượng, dù câu chỉ dùng mã MAT1202. Guard lấy overview/unit kế thừa/hợp thành vì cùng khớp phần từ; unit0 Đối tượng, lớp và bất biến đã có trong top5 nhưng không được chọn. |Chỉ tiêu thụ **toàn tên môn** nếu nó được dùng như locator; không bỏ mọi từ thành phần của tên khỏi yêu cầu. Tách hai ý “đối tượng” và “kế thừa”, lấy mô tả trực tiếp cho cả hai; không lấy overview/danh mục title làm chứng cứ giải thích đủ ý. |
|014 |Guard còn `cau/dan/dat/han/pham`. Nó nhận cả5 unit vì mỗi unit khớp một phần, dù unit0 đã trực tiếp giải thích câu hỏi nghiên cứu/phạm vi. |Chọn mô tả trực tiếp cho các ý hỏi cùng phần điều kiện cần thiết; không trả tất cả unit chỉ vì chúng có một vài token chung. |

006 là grammar tổng quan.019 là paraphrase về một khái niệm; hai vấn đề khác
nhau, không chữa chung bằng thêm mọi từ đời thường vào stopwords. Có target
không chứng minh đủ ý; ví dụ009 có unit kế thừa nhưng vẫn cần định nghĩa đối
tượng và quan hệ lớp–đối tượng để trả trọn câu.

## Phần nội dung phải giữ

- 009: đối tượng là thể hiện cụ thể với trạng thái/vòng đời; kế thừa là chuyên
  biệt hóa; phần giải thích khả năng thay thế phải giữ yêu cầu lớp con giữ cam
  kết của nơi sử dụng, không giản lược thành “cùng tên phương thức”.
- 014: câu hỏi xác định hiện tượng/đối tượng/kiểu hiểu biết; phạm vi giới hạn điều
  có thể kết luận. Giữ phần định nghĩa/quan sát nếu chọn trọn đoạn mô tả để giải thích.
- 019: “có thể”, “nhiễu”, “mẫu huấn luyện”, “dữ liệu mới” và sự cân bằng độ khớp/
  độ nhạy là ý thực chất. Không biến thành khẳng định chắc chắn hoặc mẹo áp dụng
  cho mọi mô hình. Chỉ là kiến thức AI tham khảo, không đề cương/quy định chính thức.
- 012: nếu chọn2023 thì có các lĩnh vực trong quote2023; nếu chọn2015 thì chỉ trả
  điều đoạn2015 thực sự ghi. Cả hai giữ đủ điều kiện/có nhu cầu và trạng thái review.

Các nhận xét này là yêu cầu thiết kế từ nội dung đã đọc, không chỉnh gold cũ
hoặc xác nhận hai edition tương đương về học thuật.

## Quy tắc nguồn chốt trong thiết kế

1. Mã/ngành/phiên bản F2 đã chọn tiếp tục ràng buộc F2/F3. Không lấy phiên bản
   quyết định F2 làm edition tài liệu F1, không tự suy hệ F1 từ selector F2.
2. F1 có edition/hệ/source selector rõ: lọc trước retrieval, rồi chỉ dùng đúng
   scope đó. Sai/không có nguồn thì nói rõ; không mượn edition khác để có đáp án.
3. Chưa chọn mà inventory đủ điều kiện có nhiều edition/hệ/source family: hỏi
   chọn nguồn, nêu năm/hệ/loại tài liệu/review bằng metadata thật. Không hỏi Google
   để đoán nguồn “hiện hành”. Chỉ một scope thì dùng nó kèm trạng thái chưa xác minh.
4. Không ghép2015+2023 hoặc chuẩn+CLC để phủ đủ ý. Nếu một nguồn không đủ ý,
   nêu thiếu hoặc cho người dùng chọn nguồn khác; không ép ranking theo target.
5. “Unknown” không phải năm hiện tại/hệ chuẩn. Nếu có nhiều web/source IDs cùng
   unknown thì vẫn coi là các nguồn riêng, không ngầm xem là một bản tương đương.

Các quy tắc trên **chưa được nối vào API/UI**. Lựa chọn cụ thể012 trong runtime
hiện vẫn chịu ranking; đây là giới hạn còn lại, không gọi đã sửa bằng tài liệu.

[Thiết kế prompt/validator](superpowers/specs/2026-11-14-hus-focused-answer-design.md) ·
[Run20 câu lịch sử](RAG_HYBRID_NATURAL20_2026_11_14.md) ·
[Kế hoạch tiến độ](RAG_PROGRESS_AND_NEXT_PLAN.md)
