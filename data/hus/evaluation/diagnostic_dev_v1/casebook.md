# Casebook — diagnostic/dev v1

Gold nháp có AI hỗ trợ; source pointers nằm trong P1-1 đã ghim. Không phải nghiệm thu.

| ID | Parent | Ngành | Opt-in | Tags | Câu hỏi | Kỳ vọng |
| --- | --- | --- | --- | --- | --- | --- |
| DEV-Q001 | P11-Q001 | mathematics | False | natural_language, synonym | Bạn kể giúp các hệ đào tạo cử nhân ngành Toán mà khoa giới thiệu được không? | answered; f1; introduction |
| DEV-Q002 | P11-Q001 | mathematics | False | natural_language | Theo trang giới thiệu đã lưu, Toán học có hệ chuẩn và hệ tài năng như thế nào? | answered; f1; introduction |
| DEV-Q003 | P11-Q002 | mathematics | False | natural_language, synonym | Ra trường ngành Toán có thể làm ở đâu theo tài liệu đã lưu? | answered; f1; careers |
| DEV-Q004 | P11-Q002 | mathematics | False | natural_language, negation | Mình không hỏi mức lương; chỉ muốn biết tài liệu nêu những nơi làm việc nào cho cử nhân Toán. | answered; f1; careers |
| DEV-Q005 | P11-Q003 | mathematics | False | natural_language, synonym | Cử nhân Toán muốn học lên thạc sĩ, tiến sĩ thì trang khoa mô tả khả năng và điều kiện gì? | answered; f1; further_study |
| DEV-Q006 | P11-Q003 | mathematics | False | natural_language, negation | Không cần tư vấn chọn môn, mình chỉ muốn đọc khả năng học tiếp sau cử nhân Toán trong nguồn đã lưu. | answered; f1; further_study |
| DEV-Q007 | P11-Q004 | mathematics | False | natural_language, course_name, synonym | Môn Lý thuyết bản và vỏ mỏng trong bản chương trình Toán học đã chọn có khối lượng bao nhiêu tín chỉ? | answered; f2; credits |
| DEV-Q008 | P11-Q004 | mathematics | False | course_code, negation | Không hỏi lương hay xếp hạng: mình chỉ tra số tín chỉ của MAT3422 trong bản chương trình Toán học đã chọn. | answered; f2; credits |
| DEV-Q009 | P11-Q005 | mathematics | False | course_code, natural_language, synonym | Tra giúp mat3411 là môn gì trong danh mục Toán học. | answered; f2; course_name |
| DEV-Q010 | P11-Q005 | mathematics | False | course_code, synonym | Mã học phần MAT3411 mang tên đầy đủ nào trong bản chương trình Toán học? | answered; f2; course_name |
| DEV-Q011 | P11-Q006 | mathematics | False | course_code, natural_language, synonym | Trước môn MAT3415 của Toán học, bảng nguồn ghi phải học những mã nào? | answered; f2; prerequisites.raw_variants |
| DEV-Q012 | P11-Q006 | mathematics | False | course_code, negation, synonym | Không kết luận đủ điều kiện đăng ký: chỉ chép dòng học trước của MAT3415 theo bản chương trình Toán học. | answered; f2; prerequisites.raw_variants |
| DEV-Q013 | P11-Q007 | mathematics | True | natural_language, course_code, synonym | Bạn phác họa các phần sẽ học trong MAT3408 cho mình được không? Mình đang hỏi ở mức kiến thức AI tham khảo. | answered; f3; content |
| DEV-Q014 | P11-Q007 | mathematics | True | course_code, negation | Không yêu cầu đề cương chính thức: cho mình xem nội dung MAT3408 từ phần kiến thức AI tham khảo. | answered; f3; content |
| DEV-Q015 | P11-Q008 | mathematics | True | course_code, synonym | Với phần AI tham khảo đã bật, MAT3418 hướng người học tới các năng lực gì? | answered; f3; objectives |
| DEV-Q016 | P11-Q008 | mathematics | True | course_code, negation | Không coi là chuẩn đầu ra chính thức; mình đồng ý đọc mục tiêu tham khảo do AI gợi ý cho MAT3418. | answered; f3; objectives |
| DEV-Q017 | P11-Q009 | mathematics | False | course_code, natural_language | Mình cần tỷ lệ thi cuối kỳ chính thức của MAT3408, có nguồn đã xác minh không? | no_information; f3; official_assessment |
| DEV-Q018 | P11-Q009 | mathematics | False | course_code, negation | Không lấy gợi ý AI: hãy xác nhận hình thức và phần trăm điểm thi chính thức của MAT3408. | no_information; f3; official_assessment |
| DEV-Q019 | P11-Q010 | mathematics | False | course_code, natural_language, synonym | Kỳ sắp tới MAT3422 của Toán học mở lớp lúc nào, học ở đâu? | no_information; f2; current_offering |
| DEV-Q020 | P11-Q010 | mathematics | False | course_code, negation | Không cần nội dung môn, mình cần thông tin hiện tại về giảng viên, chỗ trống và lịch lớp MAT3422 của Toán học. | no_information; f2; current_offering |
| DEV-Q021 | P11-Q011 | mathematics | False | out_of_scope, natural_language | Hãy xếp hạng môn Toán học theo độ dễ lấy điểm và chọn hộ mình 20 tín chỉ. | no_information; None; None |
| DEV-Q022 | P11-Q011 | mathematics | False | out_of_scope, negation | Đăng nhập email rồi gửi thư xin nghỉ học cho mình; không cần thông tin ngành Toán học. | no_information; None; None |
| DEV-Q023 | P11-Q012 | mathematics | False | natural_language, course_code, synonym | Bạn phác họa các phần sẽ học trong MAT3408 cho mình được không? Mình đang hỏi ở mức kiến thức AI tham khảo. | needs_clarification; f3; content |
| DEV-Q024 | P11-Q012 | mathematics | False | course_code, negation | Không yêu cầu đề cương chính thức: cho mình xem nội dung MAT3408 từ phần kiến thức AI tham khảo. | needs_clarification; f3; content |
| DEV-Q025 | P11-Q013 | mathematics_informatics | False | natural_language, synonym | Ngành Toán tin được mở từ khi nào và tên gọi ban đầu là gì theo trang khoa? | answered; f1; introduction |
| DEV-Q026 | P11-Q013 | mathematics_informatics | False | natural_language, synonym | Kể giúp lịch sử hình thành Toán tin: thời điểm bắt đầu và tên ngành trước đây. | answered; f1; introduction |
| DEV-Q027 | P11-Q014 | mathematics_informatics | False | natural_language, synonym | Ra trường Toán tin có thể đảm nhiệm công việc nào trong doanh nghiệp theo tài liệu? | answered; f1; careers |
| DEV-Q028 | P11-Q014 | mathematics_informatics | False | natural_language, negation | Không cần dự báo lương, bạn chỉ đọc các vị trí việc làm Toán tin được ghi trong nguồn nhé. | answered; f1; careers |
| DEV-Q029 | P11-Q015 | mathematics_informatics | False | natural_language, synonym | Từ cử nhân Toán tin có thể học lên cao học, nghiên cứu sinh ở lĩnh vực nào nếu đủ điều kiện? | answered; f1; further_study |
| DEV-Q030 | P11-Q015 | mathematics_informatics | False | natural_language, negation | Mình không nhờ lập lộ trình học; tài liệu Toán tin nói gì về các hướng học tiếp sau đại học? | answered; f1; further_study |
| DEV-Q031 | P11-Q016 | mathematics_informatics | False | natural_language, course_name, synonym | Môn Thực hành tính toán trong bản chương trình Toán tin đã chọn có khối lượng bao nhiêu tín chỉ? | answered; f2; credits |
| DEV-Q032 | P11-Q016 | mathematics_informatics | False | course_code, negation | Không hỏi lương hay xếp hạng: mình chỉ tra số tín chỉ của MAT3525 trong bản chương trình Toán tin đã chọn. | answered; f2; credits |
| DEV-Q033 | P11-Q017 | mathematics_informatics | False | course_code, natural_language, synonym | Tra giúp mat3509 là môn gì trong danh mục Toán tin. | answered; f2; course_name |
| DEV-Q034 | P11-Q017 | mathematics_informatics | False | course_code, synonym | Mã học phần MAT3509 mang tên đầy đủ nào trong bản chương trình Toán tin? | answered; f2; course_name |
| DEV-Q035 | P11-Q018 | mathematics_informatics | False | course_code, natural_language, synonym | Trước môn MAT3565 của Toán tin, bảng nguồn ghi phải học những mã nào? | answered; f2; prerequisites.raw_variants |
| DEV-Q036 | P11-Q018 | mathematics_informatics | False | course_code, negation, synonym | Không kết luận đủ điều kiện đăng ký: chỉ chép dòng học trước của MAT3565 theo bản chương trình Toán tin. | answered; f2; prerequisites.raw_variants |
| DEV-Q037 | P11-Q019 | mathematics_informatics | True | natural_language, course_code, synonym | Bạn phác họa các phần sẽ học trong MAT3531 cho mình được không? Mình đang hỏi ở mức kiến thức AI tham khảo. | answered; f3; content |
| DEV-Q038 | P11-Q019 | mathematics_informatics | True | course_code, negation | Không yêu cầu đề cương chính thức: cho mình xem nội dung MAT3531 từ phần kiến thức AI tham khảo. | answered; f3; content |
| DEV-Q039 | P11-Q020 | mathematics_informatics | True | course_code, synonym | Với phần AI tham khảo đã bật, MAT3545 hướng người học tới các năng lực gì? | answered; f3; objectives |
| DEV-Q040 | P11-Q020 | mathematics_informatics | True | course_code, negation | Không coi là chuẩn đầu ra chính thức; mình đồng ý đọc mục tiêu tham khảo do AI gợi ý cho MAT3545. | answered; f3; objectives |
| DEV-Q041 | P11-Q021 | mathematics_informatics | False | course_code, natural_language | Mình cần tỷ lệ thi cuối kỳ chính thức của MAT3531, có nguồn đã xác minh không? | no_information; f3; official_assessment |
| DEV-Q042 | P11-Q021 | mathematics_informatics | False | course_code, negation | Không lấy gợi ý AI: hãy xác nhận hình thức và phần trăm điểm thi chính thức của MAT3531. | no_information; f3; official_assessment |
| DEV-Q043 | P11-Q022 | mathematics_informatics | False | course_code, natural_language, synonym | Kỳ sắp tới MAT3525 của Toán tin mở lớp lúc nào, học ở đâu? | no_information; f2; current_offering |
| DEV-Q044 | P11-Q022 | mathematics_informatics | False | course_code, negation | Không cần nội dung môn, mình cần thông tin hiện tại về giảng viên, chỗ trống và lịch lớp MAT3525 của Toán tin. | no_information; f2; current_offering |
| DEV-Q045 | P11-Q023 | mathematics_informatics | False | out_of_scope, natural_language | Hãy xếp hạng môn Toán tin theo độ dễ lấy điểm và chọn hộ mình 20 tín chỉ. | no_information; None; None |
| DEV-Q046 | P11-Q023 | mathematics_informatics | False | out_of_scope, negation | Dự báo thời tiết Huế ngày mai cho mình, không tra cứu chương trình Toán tin. | no_information; None; None |
| DEV-Q047 | P11-Q024 | mathematics_informatics | False | natural_language, course_code, synonym | Bạn phác họa các phần sẽ học trong MAT3531 cho mình được không? Mình đang hỏi ở mức kiến thức AI tham khảo. | needs_clarification; f3; content |
| DEV-Q048 | P11-Q024 | mathematics_informatics | False | course_code, negation | Không yêu cầu đề cương chính thức: cho mình xem nội dung MAT3531 từ phần kiến thức AI tham khảo. | needs_clarification; f3; content |
| DEV-Q049 | P11-Q025 | computer_science | False | natural_language, synonym | Ngành KHMTTT đào tạo để xử lý những vấn đề thông tin và dữ liệu nào? | answered; f1; objectives |
| DEV-Q050 | P11-Q025 | computer_science | False | natural_language, synonym | Mục đích đào tạo của Khoa học máy tính và thông tin được tài liệu nguồn mô tả ra sao? | answered; f1; objectives |
| DEV-Q051 | P11-Q026 | computer_science | False | natural_language, synonym | Ra trường KHMTTT có những hướng công việc nào trong bản chương trình đã lưu? | answered; f1; careers |
| DEV-Q052 | P11-Q026 | computer_science | False | natural_language, negation | Không dự đoán thu nhập, chỉ kể các vai trò nghề nghiệp của KHMTTT trong tài liệu hệ chuẩn. | answered; f1; careers |
| DEV-Q053 | P11-Q027 | computer_science | False | natural_language, synonym | Sau cử nhân KHMTTT, nguồn nói có thể học cao học hoặc nghiên cứu sinh ở những chuyên ngành nào? | answered; f1; further_study |
| DEV-Q054 | P11-Q027 | computer_science | False | natural_language, negation | Không cần khuyên mình chọn ngành, hãy trích các hướng học tiếp sau đại học được nêu cho KHMTTT. | answered; f1; further_study |
| DEV-Q055 | P11-Q028 | computer_science | False | natural_language, course_name, synonym | Môn Lập trình mobile trong bản chương trình KHMTTT đã chọn có khối lượng bao nhiêu tín chỉ? | answered; f2; credits |
| DEV-Q056 | P11-Q028 | computer_science | False | course_code, negation | Không hỏi lương hay xếp hạng: mình chỉ tra số tín chỉ của MAT3558 trong bản chương trình KHMTTT đã chọn. | answered; f2; credits |
| DEV-Q057 | P11-Q029 | computer_science | False | course_code, natural_language, synonym | Tra giúp mat3541e là môn gì trong danh mục KHMTTT. | answered; f2; course_name |
| DEV-Q058 | P11-Q029 | computer_science | False | course_code, synonym | Mã học phần MAT3541E mang tên đầy đủ nào trong bản chương trình KHMTTT? | answered; f2; course_name |
| DEV-Q059 | P11-Q030 | computer_science | False | course_code, natural_language, synonym | Trước môn MAT3563 của KHMTTT, bảng nguồn ghi phải học những mã nào? | answered; f2; prerequisites.raw_variants |
| DEV-Q060 | P11-Q030 | computer_science | False | course_code, negation, synonym | Không kết luận đủ điều kiện đăng ký: chỉ chép dòng học trước của MAT3563 theo bản chương trình KHMTTT. | answered; f2; prerequisites.raw_variants |
| DEV-Q061 | P11-Q031 | computer_science | True | natural_language, course_code, synonym | Bạn phác họa các phần sẽ học trong MAT3550E cho mình được không? Mình đang hỏi ở mức kiến thức AI tham khảo. | answered; f3; content |
| DEV-Q062 | P11-Q031 | computer_science | True | course_code, negation | Không yêu cầu đề cương chính thức: cho mình xem nội dung MAT3550E từ phần kiến thức AI tham khảo. | answered; f3; content |
| DEV-Q063 | P11-Q032 | computer_science | True | course_code, synonym | Với phần AI tham khảo đã bật, MAT3552E hướng người học tới các năng lực gì? | answered; f3; objectives |
| DEV-Q064 | P11-Q032 | computer_science | True | course_code, negation | Không coi là chuẩn đầu ra chính thức; mình đồng ý đọc mục tiêu tham khảo do AI gợi ý cho MAT3552E. | answered; f3; objectives |
| DEV-Q065 | P11-Q033 | computer_science | False | course_code, natural_language | Mình cần tỷ lệ thi cuối kỳ chính thức của MAT3550E, có nguồn đã xác minh không? | no_information; f3; official_assessment |
| DEV-Q066 | P11-Q033 | computer_science | False | course_code, negation | Không lấy gợi ý AI: hãy xác nhận hình thức và phần trăm điểm thi chính thức của MAT3550E. | no_information; f3; official_assessment |
| DEV-Q067 | P11-Q034 | computer_science | False | course_code, natural_language, synonym | Kỳ sắp tới MAT3558 của KHMTTT mở lớp lúc nào, học ở đâu? | no_information; f2; current_offering |
| DEV-Q068 | P11-Q034 | computer_science | False | course_code, negation | Không cần nội dung môn, mình cần thông tin hiện tại về giảng viên, chỗ trống và lịch lớp MAT3558 của KHMTTT. | no_information; f2; current_offering |
| DEV-Q069 | P11-Q035 | computer_science | False | out_of_scope, natural_language | Hãy xếp hạng môn KHMTTT theo độ dễ lấy điểm và chọn hộ mình 20 tín chỉ. | no_information; None; None |
| DEV-Q070 | P11-Q035 | computer_science | False | out_of_scope, negation | Mình không cần đọc tài liệu KHMTTT, hãy tư vấn mua điện thoại trong ngân sách của mình. | no_information; None; None |
| DEV-Q071 | P11-Q036 | computer_science | False | natural_language, course_code, synonym | Bạn phác họa các phần sẽ học trong MAT3550E cho mình được không? Mình đang hỏi ở mức kiến thức AI tham khảo. | needs_clarification; f3; content |
| DEV-Q072 | P11-Q036 | computer_science | False | course_code, negation | Không yêu cầu đề cương chính thức: cho mình xem nội dung MAT3550E từ phần kiến thức AI tham khảo. | needs_clarification; f3; content |
| DEV-Q073 | P11-Q037 | data_science | False | natural_language, synonym | KHDL kết hợp ba nền tảng nào và nhằm làm gì theo mô tả ngành? | answered; f1; introduction |
| DEV-Q074 | P11-Q037 | data_science | False | natural_language, synonym | Bạn giải thích giúp nền tảng ba lĩnh vực của Khoa học dữ liệu trong tài liệu giới thiệu. | answered; f1; introduction |
| DEV-Q075 | P11-Q038 | data_science | False | natural_language, synonym | Học KHDL xong có thể làm nghiên cứu phát triển ở đâu theo nguồn chương trình? | answered; f1; careers |
| DEV-Q076 | P11-Q038 | data_science | False | natural_language, negation | Không hỏi công ty đang tuyển, mình chỉ muốn biết các đơn vị nghiên cứu phát triển mà tài liệu KHDL nhắc tới. | answered; f1; careers |
| DEV-Q077 | P11-Q039 | data_science | False | natural_language, synonym | Tài liệu KHDL mô tả cơ hội học cao hơn và tiếp tục nghiên cứu sau cử nhân thế nào? | answered; f1; further_study |
| DEV-Q078 | P11-Q039 | data_science | False | natural_language, negation | Không nhờ lập kế hoạch học, mình chỉ cần mô tả khả năng học tiếp sau cử nhân Khoa học dữ liệu theo nguồn. | answered; f1; further_study |
| DEV-Q079 | P11-Q040 | data_science | False | natural_language, course_name, synonym | Môn Một số vấn đề ứng dụng của khoa học dữ liệu trong bản chương trình KHDL đã chọn có khối lượng bao nhiêu tín chỉ? | answered; f2; credits |
| DEV-Q080 | P11-Q040 | data_science | False | course_code, negation | Không hỏi lương hay xếp hạng: mình chỉ tra số tín chỉ của MAT3397 trong bản chương trình KHDL đã chọn. | answered; f2; credits |
| DEV-Q081 | P11-Q041 | data_science | False | course_code, natural_language, synonym | Tra giúp mat3399 là môn gì trong danh mục KHDL. | answered; f2; course_name |
| DEV-Q082 | P11-Q041 | data_science | False | course_code, synonym | Mã học phần MAT3399 mang tên đầy đủ nào trong bản chương trình KHDL? | answered; f2; course_name |
| DEV-Q083 | P11-Q042 | data_science | False | course_code, natural_language, synonym | Trước môn MAT3534 của KHDL, bảng nguồn ghi phải học những mã nào? | answered; f2; prerequisites.raw_variants |
| DEV-Q084 | P11-Q042 | data_science | False | course_code, negation, synonym | Không kết luận đủ điều kiện đăng ký: chỉ chép dòng học trước của MAT3534 theo bản chương trình KHDL. | answered; f2; prerequisites.raw_variants |
| DEV-Q085 | P11-Q043 | data_science | True | natural_language, course_code, synonym | Bạn phác họa các phần sẽ học trong MAT3535 cho mình được không? Mình đang hỏi ở mức kiến thức AI tham khảo. | answered; f3; content |
| DEV-Q086 | P11-Q043 | data_science | True | course_code, negation | Không yêu cầu đề cương chính thức: cho mình xem nội dung MAT3535 từ phần kiến thức AI tham khảo. | answered; f3; content |
| DEV-Q087 | P11-Q044 | data_science | True | course_code, synonym | Với phần AI tham khảo đã bật, MAT3398 hướng người học tới các năng lực gì? | answered; f3; objectives |
| DEV-Q088 | P11-Q044 | data_science | True | course_code, negation | Không coi là chuẩn đầu ra chính thức; mình đồng ý đọc mục tiêu tham khảo do AI gợi ý cho MAT3398. | answered; f3; objectives |
| DEV-Q089 | P11-Q045 | data_science | False | course_code, natural_language | Mình cần tỷ lệ thi cuối kỳ chính thức của MAT3535, có nguồn đã xác minh không? | no_information; f3; official_assessment |
| DEV-Q090 | P11-Q045 | data_science | False | course_code, negation | Không lấy gợi ý AI: hãy xác nhận hình thức và phần trăm điểm thi chính thức của MAT3535. | no_information; f3; official_assessment |
| DEV-Q091 | P11-Q046 | data_science | False | course_code, natural_language, synonym | Kỳ sắp tới MAT3397 của KHDL mở lớp lúc nào, học ở đâu? | no_information; f2; current_offering |
| DEV-Q092 | P11-Q046 | data_science | False | course_code, negation | Không cần nội dung môn, mình cần thông tin hiện tại về giảng viên, chỗ trống và lịch lớp MAT3397 của KHDL. | no_information; f2; current_offering |
| DEV-Q093 | P11-Q047 | data_science | False | out_of_scope, natural_language | Hãy xếp hạng môn KHDL theo độ dễ lấy điểm và chọn hộ mình 20 tín chỉ. | no_information; None; None |
| DEV-Q094 | P11-Q047 | data_science | False | out_of_scope, negation | Vào tài khoản ngân hàng chuyển tiền học phí giúp mình, không cần thông tin ngành KHDL. | no_information; None; None |
| DEV-Q095 | P11-Q048 | data_science | False | natural_language, course_code, synonym | Bạn phác họa các phần sẽ học trong MAT3535 cho mình được không? Mình đang hỏi ở mức kiến thức AI tham khảo. | needs_clarification; f3; content |
| DEV-Q096 | P11-Q048 | data_science | False | course_code, negation | Không yêu cầu đề cương chính thức: cho mình xem nội dung MAT3535 từ phần kiến thức AI tham khảo. | needs_clarification; f3; content |
