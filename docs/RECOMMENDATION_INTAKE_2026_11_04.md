# Điều chỉnh luồng gợi ý ngày 04/11/2026

## Thiết kế trước triển khai

Giữ bố cục hội thoại/lộ trình, phông Be Vietnam Pro và token màu hiện có:
paper `#F8F9FD`, ink `#24253C`, indigo `#6554E8`, lavender `#ECE8FF`,
mint `#147660`; chế độ tối tiếp tục dùng theme chung. Căn trái, giữ chuyển
bước có animation nhưng giảm số ô nhập cùng lúc.

```
Định hướng: các lựa chọn / Tự chọn -> ô nhập định hướng riêng
Tải học: chọn mức -> kéo tín chỉ trong khoảng tương ứng
Mốc tốt nghiệp: HK1/HK2 -> năm học thuộc thời hạn khóa
Nhánh tốt nghiệp nếu khung yêu cầu
Cuối luồng: tóm tắt + ô bổ sung mong muốn + tạo phương án
```

Tự chọn là sở thích do người dùng nhập. Nếu chương trình có hướng bắt buộc,
vẫn chọn một hướng thật trong khung; không dùng văn bản tự nhập làm ID học vụ.
Chat chỉ xuất hiện khi đã hoàn tất các lựa chọn. Light: 14–17, moderate: 18–20,
heavy: 21–30; đổi mức đưa tín chỉ về biên gần nhất của khoảng mới.

Khóa K68 tương ứng năm vào học 2023; K67 là 2022. Mục tiêu tốt nghiệp chỉ có
HK1/HK2 và các năm học còn lại trong tối đa 6 năm từ năm vào học. Với thời điểm
04/11/2026, K68 có 2026–2027, 2027–2028, 2028–2029; không thêm 2029–2030.
Nhãn đổi thành “Năm học dự kiến tốt nghiệp”. Không bịa khóa khi hồ sơ thiếu,
không coi thời điểm lựa chọn là xác nhận đủ điều kiện tốt nghiệp.

Rà soát brief: ô Tự chọn là input định hướng có nhãn, không phải ô chat bị
lặp lại. Không thay phong cách toàn trang, không thêm hiệu ứng nền hoặc luồng
đăng nhập mới. Các lựa chọn học vụ và kiểm tra server hiện có được giữ.

## Đối chiếu nguồn khung chương trình

Đã mở bộ ZIP người dùng cung cấp; 5 PDF có hash khớp toàn bộ manifest nguồn
đang lưu trong `database/data/hus_source.json`. Đọc trang 2 PDF 104 xác nhận
Điều 2 áp dụng từ khóa tuyển sinh 2022 (K67). Nguồn dự án đã có sign-off của
người dùng cho QĐ3568/KHMTTT; runtime local đang dùng bản cũ draft_unverified.
Các chương trình khác chưa tự được coi là đã xác minh vì đọc được file ZIP.

Sẽ dùng quy trình catalog hiện có và bằng chứng nguồn đã xác nhận để khắc phục
bản runtime cũ, ghi lại revision trước/sau và khả năng rollback. Binding theo
tài khoản vẫn do chủ tài khoản xác nhận khi revision thay đổi.

## Kiểm chứng dự kiến

Node: biên tín chỉ của từng mức, đổi mức, cohort/năm vào học, cửa sổ 6 năm,
khóa thiếu/tương lai/hết hạn và HK3 không hợp lệ. Chrome giả lập API: Tự chọn
và nhập trống, chat chỉ ở cuối, credit slider/number, mục tiêu K68, đổi tài
khoản/khóa, VI/EN, mobile/themes/reduced motion; regression lưu/so sánh cũ.
Đối chiếu ZIP bằng hash và kiểm tra catalog/builder trước khi đổi runtime.

## Kết quả thực hiện

- “Tự chọn” mở ô nhập định hướng riêng, tối đa 120 ký tự; không nhận chuỗi
  rỗng/toàn khoảng trắng. Chương trình yêu cầu hướng chính thức vẫn phải chọn
  ID hướng có thật trong catalog. Văn bản tự nhập không thay thế ID đó.
- Ô chat chỉ xuất hiện ở tóm tắt cuối sau khi đủ 3 bước, hoặc sau bước nhánh
  tốt nghiệp nếu chương trình có yêu cầu. Quay lại sửa lựa chọn sẽ ẩn ô chat.
- Cả slider, input số và payload đều kiểm tra các khoảng 14–17 / 18–20 / 21–30.
  Đổi mức kẹp giá trị vào khoảng mới, ví dụ 20 → Nhẹ nhàng là 17,
  17 → Tập trung là 21, 30 → Cân bằng là 20. Mặc định vẫn 20/Cân bằng.
- Mốc tốt nghiệp chỉ có HK1/HK2, tính năm vào học từ khóa hoặc năm tuyển sinh
  thật trong hồ sơ. Cửa sổ hiển thị từ năm học hiện tại tới năm vào học + 5;
  UI chuyển năm học vào tháng 8. Khóa thiếu/tương lai/hết khoảng 6 năm không
  được gán một năm giả. Đổi khóa trong cùng phiên hủy mốc cũ và kết quả cũ.
  Năm học lưu phương án là trường riêng, giữ hợp đồng API hiện có.
- Giới hạn tối đa 6 năm là tham số người dùng yêu cầu cho selector này. PDF104,
  trang 3 nêu thời gian chương trình thông thường 4 năm; selector không xác nhận
  quyền gia hạn, đủ tín chỉ hay điều kiện tốt nghiệp của từng người.
- Thông báo học vụ phân biệt kết quả môn cần đối chiếu, quy tắc nhóm/nhánh và
  dữ liệu khung chưa xác minh; không gọi mọi tình huống preview là cùng một lỗi.
- Định hướng dài được xuống dòng ở tóm tắt và lộ trình; không làm tràn mobile.

## Bản khung đã khôi phục ở local

ZIP SHA-256: `35935e648e2139fa6e1a0f063961f942eb68c4fa451a0cf69b78be4331132a25`.
PDF104 SHA-256: `bc070d7ae3713f77c36817d960b73dec53dcdeacda5e25e557c37a732abe09ab`.
Đã đọc trang 1/2/3: trang 1 là QĐ3568 ngày 18/10/2023; Điều 2 ở trang 2 áp dụng
từ khóa 2022. Trang 3 ghi QĐ3569 trong dòng dẫn, khác trang quyết định gốc;
giữ nguyên PDF và danh tính theo trang quyết định/manifest, không sửa nguồn scan.
Lượt này không tuyên bố review độc lập toàn bộ mọi ô của cả 5 PDF; việc khôi
phục dùng sign-off KHMTTT có sẵn, được ràng buộc đúng hash nguồn.

Runtime đang ở snapshot KHMTTT cũ `7aafa016...`, nên vẫn báo draft_unverified.
Đã dùng `publish_catalogs` hiện có, với engine ứng dụng được kiểm tra là
loopback, để xuất bản bundle nguồn hiện tại trong một transaction. Revision
KHMTTT mới là
`c46163d1629819649f9bc8d54db59156d8a46ee40deec6c6d1fdb923c731e1da`,
trạng thái program, source của 67 môn và các tiên quyết đều verified theo
sign-off đã có. Ba chương trình khác vẫn draft_unverified.

Publisher đồng bộ bốn snapshot theo thiết kế hiện hành. So sánh trước/sau
chứng minh không đổi mã, tên, tín chỉ, biểu thức tiên quyết hoặc loại môn.
KHDL bổ sung locator nhóm cha V.2/28–63 đã có trong source bundle; note khác
biệt với tổng nhóm con vẫn được giữ, không tự nâng mức review của ngành này.
Không sửa `hus_source.json`, tạo sign-off mới, sửa bảng điểm hoặc tự xác nhận
binding cho tài khoản thật. Revision cũ vẫn còn để rollback bằng công cụ hiện có.
Receipt trước/sau và snapshot catalog nằm trong thư mục backup của lượt này.

Nếu binding của hồ sơ đang gắn với revision cũ, chủ tài khoản xác nhận lại
ngành/khóa qua “Kiểm tra dữ liệu”; ứng dụng không bỏ qua yêu cầu đó.

## Kiểm chứng đã đạt

- **621 pytest passed, 80 DB cases deselected**, gồm các ca PDF acceptance với
  `--full-catalog-root docs/acceptance/hus_2022`. Một warning Starlette/httpx có
  sẵn; hai warning decode stdout subprocess trên Windows đã được kiểm tra lại
  ở đúng 2 ca với `PYTHONUTF8=1`: cả hai pass, không còn warning decode.
- Node model checks: biên của từng mức, chuyển mức, payload, quota, K67/K68/K69,
  năm tuyển sinh, đổi năm học, khóa thiếu/tương lai/hết hạn và HK3 sai.
- **5 Chrome suites pass**: intake/recommendation, saved semester plans,
  VNU-only, presentation và study desk. Bộ mới kiểm tra Tự chọn có/không có
  hướng bắt buộc, input trống, chat chỉ cuối 3/4 bước, keyboard slider,
  K68/K69 và đổi khóa, khóa thiếu, text 120 ký tự trên mobile, save/error/
  response-lost, logout race, VI/EN, sáng/tối, reduced motion và ba viewport.
- Contract với catalog runtime thật và transcript giả cho kết quả context
  ready, board ready, không preview metadata. Không đọc bảng điểm thật hoặc
  gọi model/provider để kiểm thử.
- Publisher dry-run, Ruff, JS syntax, diff checks và kiểm tra assets local đạt.
  `/health`, `/ready` và homepage 200; 22 assets HTML + module import khớp disk;
  endpoint cá nhân ẩn danh vẫn 401. Đã xem ảnh mốc K68 và tóm tắt cuối.

Server vẫn chạy tại <http://127.0.0.1:8000/#recommend>, listener PID 9328 là số
ghi nhận lúc kiểm tra, phải xác minh trước khi dừng. Không restart app để giữ
phiên đang có. Sau nghiệm thu, người dùng yêu cầu commit/push lên nhánh hiện tại
`feat/recommendation-conversation-ui` với khoảng 10 commit. Lượt publication dự
kiến đúng 10 commit từ `c823aa5`, bao gồm source/tests/docs/memory; trạng thái
push và commit cuối cần đối chiếu Git/GitHub. Dữ liệu runtime và các bản PDF,
video, cấu hình local không nằm trong nội dung Git của lượt publication này.
