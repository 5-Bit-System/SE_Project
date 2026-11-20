# Bốn hồ sơ mẫu — F3 tham khảo AI v2

Ngày hoàn thiện: 11/11/2026. Đây là nội dung AI tham khảo, chưa xác minh đề cương HUS. Mỗi ví dụ dưới đây hiển thị trọn phần nội dung và mục tiêu đã lưu, không phải output Gemini live.

## Toán học — MAT3360: Tối ưu hóa nâng cao

Phiên bản: `QD3565-2023` · Nhãn: tham khảo AI.

Tổng quan tham khảo:
Tối ưu hóa nâng cao mở rộng lập luận về nghiệm tối ưu sang đối ngẫu, điều kiện ràng buộc và thuật toán lặp. Hồ sơ tham khảo ưu tiên cấu trúc lồi để phân biệt bảo đảm toàn cục với kết quả cục bộ, đồng thời nối nhân tử Lagrange với độ nhạy và sai số dừng tính toán.
Các chủ đề tham khảo:
- Cấu trúc lồi và điều kiện tối ưu
- KKT và điều kiện ràng buộc
- Đối ngẫu và độ nhạy
- Thuật toán và kiểm soát hội tụ

Cấu trúc lồi và điều kiện tối ưu
Tập lồi giữ đoạn nối hai điểm khả thi trong tập, còn hàm lồi nằm dưới các dây cung. Với bài toán lồi, điều kiện tối ưu thích hợp có thể chứng nhận tối ưu toàn cục thay vì chỉ nhận diện ứng viên địa phương.
Khái niệm thành phần: tập lồi; hàm lồi; dưới gradient.
Ví dụ minh họa do AI biên soạn: Hàm trị tuyệt đối là lồi dù không khả vi tại gốc; dưới gradient vẫn diễn tả được điều kiện tối ưu ở điểm này.

KKT và điều kiện ràng buộc
Điều kiện KKT ghép dừng của Lagrangian, khả thi và bù trừ bổ sung. Chúng không tự đúng ở mọi nghiệm: điều kiện chính quy quyết định tính cần, còn tính lồi giúp nâng các điều kiện phù hợp thành chứng nhận đủ.
Khái niệm thành phần: Lagrangian; KKT; bù trừ bổ sung.
Ví dụ minh họa do AI biên soạn: Một ràng buộc còn dư có nhân tử bằng không theo bù trừ bổ sung, còn ràng buộc đang chạm biên có thể có nhân tử dương.

Đối ngẫu và độ nhạy
Hàm đối ngẫu tạo cận cho giá trị tối ưu bằng cách cực tiểu hóa Lagrangian theo biến gốc. Khi các điều kiện đối ngẫu mạnh phù hợp, khoảng cách đối ngẫu đóng lại và nhân tử có thể diễn giải biến thiên theo tài nguyên.
Khái niệm thành phần: đối ngẫu yếu; đối ngẫu mạnh; giá bóng.
Ví dụ minh họa do AI biên soạn: Nhân tử của một giới hạn tài nguyên cho biết mức thay đổi biên của chi phí tối ưu khi nới giới hạn, trong miền mà phân tích độ nhạy còn hợp lệ.

Thuật toán và kiểm soát hội tụ
Gradient dùng độ dốc, Newton dùng thêm độ cong và các phương pháp chiếu hoặc điểm trong xử lý miền khả thi. Dừng lặp cần gắn với phần dư tối ưu và khả thi, vì thay đổi nhỏ giữa hai bước chưa bảo đảm nghiệm tốt.
Khái niệm thành phần: gradient; Newton; phần dư KKT.
Ví dụ minh họa do AI biên soạn: Một bước lặp rất nhỏ có thể do chọn bước quá ngắn dù gradient còn lớn; phần dư điều kiện tối ưu giúp nhận ra tình huống dừng giả.

Mục tiêu tham khảo do AI đề xuất:
- Phân tích tính lồi và điều kiện tối ưu bậc nhất
- Giải thích điều kiện KKT cùng giả thiết áp dụng
- Diễn giải đối ngẫu và nhân tử theo độ nhạy
- So sánh cơ chế gradient, Newton và phương pháp có ràng buộc

Tài liệu đối chiếu khái niệm, không xác nhận đề cương HUS:

- [Nguồn 1](https://web.stanford.edu/~boyd/cvxbook/)

## Toán tin — MAT3500: Toán rời rạc

Phiên bản: `QD3567-2023` · Nhãn: tham khảo AI.

Tổng quan tham khảo:
Toán rời rạc nghiên cứu các cấu trúc gồm những phần tử tách biệt như tập hợp, quan hệ, đồ thị và tổ hợp. Hướng tham khảo nối cách biểu diễn cấu trúc với chứng minh và đếm, làm nền cho lập luận về mạng, dữ liệu hữu hạn và thuật toán mà không dựa vào trực giác hình học đơn thuần.
Các chủ đề tham khảo:
- Tập hợp và quan hệ
- Nguyên lý đếm
- Quy nạp và truy hồi
- Đồ thị và cây

Tập hợp và quan hệ
Quan hệ trên tập hợp mô tả cặp phần tử có liên hệ theo quy tắc. Các tính chất phản xạ, đối xứng và bắc cầu tạo quan hệ tương đương; quan hệ thứ tự dùng những điều kiện khác để biểu diễn khả năng so sánh.
Khái niệm thành phần: quan hệ tương đương; lớp tương đương; thứ tự bộ phận.
Ví dụ minh họa do AI biên soạn: Quan hệ có cùng số dư khi chia cho một số chia chia các số nguyên thành lớp, trong khi quan hệ là tập con có thể để hai tập không so sánh được.

Nguyên lý đếm
Quy tắc cộng áp dụng cho các khả năng rời nhau, còn quy tắc nhân ghép các giai đoạn lựa chọn. Khi những tập lựa chọn chồng lấn, bao hàm–loại trừ điều chỉnh phần bị đếm nhiều lần.
Khái niệm thành phần: hoán vị; tổ hợp; bao hàm–loại trừ.
Ví dụ minh họa do AI biên soạn: Chọn một nhóm người chỉ xét thành viên khác với xếp chính những người đó vào hàng vì việc đổi vị trí không tạo nhóm mới.

Quy nạp và truy hồi
Quy nạp chứng minh một tính chất lan từ trường hợp đầu sang các bước tiếp theo. Quan hệ truy hồi mô tả giá trị qua các giá trị trước, nhưng vẫn cần điều kiện đầu để xác định một dãy cụ thể.
Khái niệm thành phần: quy nạp; điều kiện đầu; truy hồi.
Ví dụ minh họa do AI biên soạn: Số cách đi lên cầu thang bằng bước một hoặc hai bậc có thể tách theo loại bước cuối, tạo liên hệ với hai trường hợp trước.

Đồ thị và cây
Đồ thị mô tả liên hệ giữa các đỉnh bằng cạnh; đường đi diễn tả khả năng tiếp cận. Cây liên thông không chu trình nên có đường đơn duy nhất giữa hai đỉnh, hữu ích để biểu diễn phân cấp và mạng nối tối giản.
Khái niệm thành phần: đỉnh; cạnh; liên thông; cây.
Ví dụ minh họa do AI biên soạn: Một mạng liên lạc hình cây nối được mọi địa điểm nhưng mất một cạnh sẽ tách mạng vì không còn đường vòng thay thế.

Mục tiêu tham khảo do AI đề xuất:
- Phân biệt quan hệ tương đương với quan hệ thứ tự
- Sử dụng nguyên lý đếm phù hợp sự phân biệt và thứ tự
- Giải thích phép quy nạp và quan hệ truy hồi
- Diễn giải liên thông, đường đi và cây trong đồ thị

Tài liệu đối chiếu khái niệm, không xác nhận đề cương HUS:

- [Nguồn 1](https://ocw.mit.edu/courses/6-042j-mathematics-for-computer-science-spring-2015/pages/readings/)

## Khoa học máy tính và thông tin — MAT3552E: Thiết kế và đánh giá thuật toán

Phiên bản: `QD3568-2023` · Nhãn: tham khảo AI.

Tổng quan tham khảo:
Thiết kế và đánh giá thuật toán nghiên cứu cách xây dựng thủ tục giải quyết vấn đề và lập luận về tài nguyên cần dùng. Hướng tham khảo nối đặc tả, chứng minh tính đúng và các chiến lược thiết kế, giúp giải thích vì sao hai thuật toán cùng cho kết quả đúng vẫn phù hợp những quy mô khác nhau.
Các chủ đề tham khảo:
- Đặc tả và tính đúng
- Chi phí và tăng trưởng
- Chia để trị và tham lam
- Quy hoạch động

Đặc tả và tính đúng
Thuật toán cần mô tả miền đầu vào, kết quả mong muốn và lý do các bước giữ ý nghĩa đó. Chứng minh tính đúng bao gồm quan hệ kết quả và việc dừng; chạy đúng trên vài dữ liệu chỉ minh họa chứ chưa bao quát mọi trường hợp.
Khái niệm thành phần: đặc tả; bất biến; tính dừng.
Ví dụ minh họa do AI biên soạn: Trong tìm kiếm nhị phân, khoảng còn xét luôn chứa vị trí có thể có của khóa và ngắn dần sau mỗi bước trên dãy đã sắp thứ tự.

Chi phí và tăng trưởng
Chi phí được mô tả theo kích thước đầu vào và phép toán chi phối. Ký hiệu tiệm cận bỏ qua một số hằng số để so sánh tốc độ tăng, nhưng không tự quyết định thời gian thực tế ở mọi kích thước.
Khái niệm thành phần: Big-O; trường hợp xấu nhất; chi phí bộ nhớ.
Ví dụ minh họa do AI biên soạn: Một thuật toán tuyến tính có thể nhanh hơn thuật toán bậc hai khi dữ liệu lớn, dù phiên bản tuyến tính có phần khởi tạo tốn hơn.

Chia để trị và tham lam
Chia để trị tách bài toán rồi kết hợp nghiệm con, còn tham lam chọn quyết định cục bộ không quay lui. Tính đúng của tham lam cần thuộc tính cấu trúc như lập luận trao đổi, không chỉ dựa vào kết quả có vẻ hợp lý.
Khái niệm thành phần: chia để trị; tham lam; lập luận trao đổi.
Ví dụ minh họa do AI biên soạn: Sắp xếp trộn ghép hai nửa đã sắp; chọn hoạt động kết thúc sớm trong bài toán khoảng dùng lý do cấu trúc khác với việc ghép nghiệm con.

Quy hoạch động
Khi bài toán có trạng thái con lặp lại và cấu trúc tối ưu thích hợp, quy hoạch động lưu kết quả thay vì tính lại. Trạng thái phải giữ đủ thông tin ảnh hưởng tương lai, rồi quan hệ chuyển nối các trạng thái với nhau.
Khái niệm thành phần: trạng thái; quan hệ chuyển; bài toán con.
Ví dụ minh họa do AI biên soạn: Bảng đường đi ngắn trong lưới có thể lưu chi phí tốt nhất đến từng ô khi các phép chuyển chỉ đến từ những ô đã xử lý.

Mục tiêu tham khảo do AI đề xuất:
- Phát biểu điều kiện đầu vào và kết quả của thuật toán
- Giải thích bất biến và quy nạp trong chứng minh tính đúng
- Phân biệt chia để trị, tham lam và quy hoạch động
- Liên hệ độ phức tạp với quy mô và cấu trúc dữ liệu

Tài liệu đối chiếu khái niệm, không xác nhận đề cương HUS:

- [Nguồn 1](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/pages/lecture-notes/)

## Khoa học dữ liệu — MAT3379: Phân tích hồi quy và ứng dụng

Phiên bản: `QD3569-2023` · Nhãn: tham khảo AI.

Tổng quan tham khảo:
Phân tích hồi quy và ứng dụng mô tả quan hệ giữa đầu ra và các biến giải thích để diễn giải hoặc dự báo. Nội dung tham khảo nhấn mạnh cấu trúc mô hình, ước lượng, chẩn đoán phần dư và bất định, đồng thời giữ rõ giới hạn khi diễn giải hệ số quan sát như tác động nhân quả.
Các chủ đề tham khảo:
- Mô hình và diễn giải hệ số
- Ước lượng và bất định
- Chẩn đoán mô hình
- Dự báo và giới hạn nhân quả

Mô hình và diễn giải hệ số
Hồi quy biểu diễn đặc trưng có điều kiện của đầu ra theo các biến giải thích. Hệ số phụ thuộc cách mã hóa, đơn vị và những biến được giữ trong mô hình; một hệ số riêng không có ý nghĩa tách khỏi cấu trúc đó.
Khái niệm thành phần: biến giải thích; hệ số hồi quy; tương tác.
Ví dụ minh họa do AI biên soạn: Trong mô hình giá nhà có diện tích và khu vực, hệ số diện tích diễn tả thay đổi gắn với diện tích khi giữ khu vực trong cách mô hình đã biểu diễn.

Ước lượng và bất định
Bình phương tối thiểu chọn hệ số để giảm tổng bình phương phần dư. Các giả thiết về sai số ảnh hưởng tính chất suy luận và độ lệch chuẩn, trong khi điều kiện hạng của ma trận thiết kế quyết định khả năng nhận diện hệ số.
Khái niệm thành phần: bình phương tối thiểu; ma trận thiết kế; sai số chuẩn.
Ví dụ minh họa do AI biên soạn: Hai cột giải thích gần trùng nhau có thể cho dự báo khá ổn nhưng hệ số riêng dao động mạnh, biểu hiện hậu quả của đa cộng tuyến.

Chẩn đoán mô hình
Phần dư theo giá trị dự báo hoặc theo thứ tự quan sát có thể lộ phi tuyến, phương sai thay đổi hoặc phụ thuộc. Điểm có đòn bẩy cao và điểm có phần dư lớn là hai khía cạnh khác nhau của ảnh hưởng.
Khái niệm thành phần: phần dư; phương sai thay đổi; đòn bẩy.
Ví dụ minh họa do AI biên soạn: Một điểm xa trung tâm của các biến giải thích có thể kéo đường hồi quy mạnh dù phần dư sau khi khớp không quá lớn.

Dự báo và giới hạn nhân quả
Dự báo cho quan sát mới gồm bất định về trung bình và nhiễu của cá thể, nên khác suy luận về trung bình. Diễn giải nhân quả còn cần thiết kế và giả thiết về yếu tố gây nhiễu, không thể lấy từ hệ số đơn thuần.
Khái niệm thành phần: khoảng dự báo; ngoại suy; yếu tố gây nhiễu.
Ví dụ minh họa do AI biên soạn: Quan hệ giữa doanh thu và chi quảng cáo có thể bị ảnh hưởng bởi mùa mua sắm; hệ số dương chưa tách được tác động riêng của quảng cáo.

Mục tiêu tham khảo do AI đề xuất:
- Diễn giải hệ số trong mô hình có nhiều biến giải thích
- Phân biệt sai số quan sát với phần dư ước lượng
- Nhận diện đa cộng tuyến, ngoại lệ và phương sai thay đổi
- Phân biệt khoảng tin cậy trung bình với khoảng dự báo

Tài liệu đối chiếu khái niệm, không xác nhận đề cương HUS:

- [Nguồn 1](https://www.statlearning.com/)
- [Nguồn 2](https://mc-stan.org/docs/stan-users-guide/regression.html)
