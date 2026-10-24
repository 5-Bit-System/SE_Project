# Thử kết nối cổng đào tạo VNU

> Cập nhật tích hợp 23/10/2026: API/profile và migration đã được thêm vào
> hệ thống local. Xem `docs/PORTAL_INTEGRATION_STATUS_2026_10_23.md` cho trạng
> thái nghiệm thu, thiết lập mới và giới hạn identity/completeness. Các mục
> bên dưới mô tả connector thử gốc. CLI chỉ in bảng điểm khi truyền rõ
> `--show-transcript`; không dùng tùy chọn đó với log chia sẻ.

Bản thử độc lập, chưa tích hợp API hoặc database. Không lưu tài khoản, cookie,
HTML hay bảng điểm ra file. Kết quả chỉ in ra terminal trong phiên thử.

## Cài và chạy từ thư mục gốc

```bash
conda activate SE_Project
python -m pip install playwright
python -m playwright install chromium
python -m tools.try_daotao
```

Trình duyệt chạy nền (headless), không mở cửa sổ. Nhập tài khoản trong terminal, mật khẩu được ẩn.
Công cụ gửi form đăng nhập một lần, đợi mục `#PortalModule_374` có title
`Xem điểm sinh viên`, rồi bấm để trang chạy handler `showApp` sẵn có.
Sau đó đợi ô `#divList3 td[title="Mã môn học"]` trong trang hoặc frame và đọc bảng
cha gần nhất. Không đọc các bảng bố cục bên ngoài.

Selector menu và cấu trúc bảng dựa trên HTML người dùng cung cấp.
Chưa kiểm chứng bằng phiên đăng nhập thật. Mỗi bước đợi tối đa 30 giây;
nếu đăng nhập thất bại hoặc trang thay đổi sẽ báo lỗi và đóng trình duyệt.
Chưa xử lý màn hình CAPTCHA/OTP, chọn bộ lọc hay phân trang tự động.

Kết quả là các hàng ô văn bản: giữ dòng học kỳ, mã học kỳ, môn, tín chỉ,
điểm hệ 10/chữ/hệ 4 và dòng tổng kết theo trang; không tính lại điểm.
Chưa ánh xạ thành mô hình môn học, chưa mở rộng rowspan/colspan.
Nếu bảng được tải theo từng phần, cần xác minh thêm dấu hiệu tải hoàn tất.

Có thể thay cách đọc bằng CSS selector khi cần chẩn đoán:

```bash
python -m tools.try_daotao --selector '#id-bang-diem'
```

ID trên chỉ là ví dụ. Chế độ này vẫn tự bấm menu, rồi đọc các bảng khớp
selector trong các trang/frame. Đầu ra terminal có thể có dữ liệu cá nhân;
không đưa dữ liệu thật vào Git hoặc log dùng chung.

## 1. Các file và trách nhiệm

```text
app/integrations/
├── __init__.py                 # Đánh dấu package integrations
└── daotao/
    ├── __init__.py             # Đánh dấu package daotao
    ├── client.py               # Điều khiển trình duyệt, đọc bảng HTML
    ├── parser.py               # Làm sạch khoảng trắng trong ô dữ liệu
    └── README.md               # Tài liệu này

tools/try_daotao.py             # Điểm bắt đầu để chạy thử toàn bộ luồng
tests/integrations/test_daotao_parser.py  # Kiểm tra bằng dữ liệu giả lập
```

Hai file `__init__.py` hiện chỉ có mô tả package, không đăng nhập hay lấy dữ liệu.
`client.py` làm việc với trang web; `parser.py` xử lý dữ liệu đã đọc về.
`tools/try_daotao.py` phối hợp hai phần và in kết quả cho người chạy.

## 2. Luồng chạy từ đầu đến cuối

```text
python -m tools.try_daotao
    │
    ├─ Đọc tùy chọn --selector (nếu có)
    ├─ Kiểm tra đã cài Playwright
    ├─ Nhập tên đăng nhập và mật khẩu trong terminal
    ├─ Mở Chromium chạy nền
    ├─ Tạo context tạm và DaotaoClient
    │
    ├─ client.login()
    │    ├─ Mở /dkmh/login.asp
    │    ├─ Điền tên đăng nhập, mật khẩu
    │    └─ Bấm nút đăng nhập, đợi DOM tải
    │
    ├─ client.open_transcript()
    │    ├─ Tìm mục Xem điểm sinh viên trong các trang/frame
    │    ├─ Bấm mục đó → JavaScript showApp của web chạy
    │    └─ Đợi ô có title="Mã môn học" xuất hiện
    │
    ├─ Không có --selector → client.read_transcript()
    │    ├─ Từ ô Mã môn học, tìm bảng cha gần nhất
    │    ├─ Đọc văn bản từng ô, theo thứ tự hàng/cột
    │    └─ parser.normalize_rows() làm sạch dữ liệu
    │
    ├─ Có --selector → client.read_tables(selector)
    │    └─ Đọc và làm sạch các bảng hiển thị khớp selector
    │
    ├─ In JSON trong terminal
    └─ Đóng Chromium, kết thúc phiên
```

`context` là một phiên trình duyệt riêng, giữ cookie trong lúc chạy để các
thao tác sau đăng nhập dùng cùng phiên. `page` là tab; `frame` là tài liệu
trong tab, có thể là nội dung nhúng bằng iframe. Công cụ duyệt các frame vì
menu và bảng điểm có thể nằm ở các tài liệu khác nhau.

`login()` chỉ gửi form, chưa tự kết luận tài khoản đúng. Việc tìm được menu
ở bước tiếp theo là dấu hiệu để tiếp tục. Nếu không tìm thấy, công cụ báo lỗi
chung; hiện chưa phân biệt sai mật khẩu, lỗi mạng hay thay đổi giao diện.

## 3. Mã giả của tools/try_daotao.py

```text
HÀM main():
    đọc tham số dòng lệnh
    nếu chưa có Playwright:
        thông báo cách cài và kết thúc với mã 1

    nhập username
    nhập password ở chế độ ẩn
    nếu thiếu username hoặc password:
        thông báo và kết thúc với mã 1

    THỬ:
        mở Chromium chạy nền
        THỬ:
            tạo context tạm, không nhận tải file
            tạo client bằng context
            client.login(username, password)
            gán biến password thành chuỗi rỗng
            client.open_transcript()

            nếu có selector tùy chọn:
                kết quả = client.read_tables(selector)
            ngược lại:
                kết quả = client.read_transcript()

            in kết quả dưới dạng JSON
            trả mã 0 nếu kết quả không rỗng, ngược lại trả mã 1
        LUÔN LUÔN:
            đóng trình duyệt
    NẾU lỗi Playwright:
        in thông báo chung, không in log thao tác có thể chứa tài khoản
        trả mã 1
    NẾU người dùng ngắt hoặc kết thúc luồng nhập:
        thông báo đã dừng và trả mã 1
```

Mã `0` biểu thị chạy thành công với kết quả không rỗng; mã `1` biểu thị lỗi
hoặc kết quả rỗng. Gán `password = ""` chỉ thay giá trị biến trong chương trình,
không bảo đảm xóa mọi bản sao mật khẩu khỏi bộ nhớ.

## 4. Mã giả của client.py

### Khởi tạo và đăng nhập

```text
HÀM khởi_tạo(context):
    giữ context để dùng cùng phiên đăng nhập
    tạo một tab mới và giữ vào self.page

HÀM login(username, password):
    mở LOGIN_URL, đợi DOMContentLoaded
    điền username vào #txtLoginId
    điền password vào #txtPassword
    bấm input[type="submit"] bên trong #frmLogin
    đợi DOMContentLoaded
```

Không cần tự gán `chkSubmit`: bấm nút submit để trình duyệt chạy handler
`chkLogin()` của form như thao tác người dùng. `DOMContentLoaded` cho biết
DOM đã tải, không bảo đảm mọi yêu cầu tải dữ liệu nền đã hoàn tất.

### Chờ phần tử trong trang hoặc frame

```text
HÀM _wait_for_element(selector, timeout_ms):
    hạn_chót = thời_gian_đơn_điệu_hiện_tại + timeout_ms / 1000
    lặp khi chưa đến hạn_chót:
        với từng tab trong context:
            với từng frame trong tab:
                tìm các phần tử khớp selector
                nếu có phần tử đang hiển thị:
                    trả phần tử đó ngay
                nếu có lỗi do frame bị tháo hoặc tab đã đóng:
                    bỏ qua và tiếp tục tìm
                nếu là lỗi khác:
                    báo lỗi ra ngoài
        nghỉ 0,2 giây rồi tìm lại
    báo lỗi hết thời gian chờ
```

Dùng `monotonic()` để tính khoảng chờ mà không phụ thuộc việc đồng hồ hệ thống
được chỉnh giờ. Tiền tố `_` cho biết đây là hàm hỗ trợ nội bộ của client.
Mỗi lần gọi hàm này có thời hạn riêng, mặc định bên gọi truyền 30 giây;
đó không phải tổng thời gian tối đa của toàn bộ chương trình.

### Mở trang xem điểm

```text
HÀM open_transcript(timeout_ms = 30000):
    menu = đợi '#PortalModule_374[title="Xem điểm sinh viên"]'
    bấm menu
    đợi '#divList3 td[title="Mã môn học"]' xuất hiện
```

Theo HTML đã cung cấp, bấm menu sẽ gọi:

```javascript
showApp(this.id, 'ListPoint/listpoint.asp')
```

Client bấm đúng phần tử để trang tự xử lý điều hướng và phiên đăng nhập.
Không tự gọi hàm `showApp` hay đoán URL của frame.

### Đọc đúng bảng điểm

```text
HÀM read_transcript(timeout_ms = 30000):
    ô_mã_môn = đợi '#divList3 td[title="Mã môn học"]'
    bảng = bảng tổ tiên gần nhất của ô_mã_môn
    với từng hàng thuộc trực tiếp bảng:
        đọc innerText của từng ô thành một danh sách chuỗi
    trả normalize_rows(các_hàng)
```

XPath `ancestor::table[1]` chọn bảng tổ tiên gần nhất. Vì vậy, nếu trang có
nhiều bảng lồng nhau để bố trí giao diện, chương trình lấy bảng chứa ô mã môn.
Điều kiện `row.closest('table') === table` loại hàng thuộc bảng con lồng bên
trong; nội dung chữ trong ô vẫn lấy bằng `innerText`.

Kết quả có kiểu `list[list[str]]`. Ví dụ hoàn toàn giả lập:

```json
[
  ["HỌC KỲ 1 - 2099-2100. MÃ HỌC KỲ 991", ""],
  ["1", "TEST001", "Môn giả lập", "3", "8.0", "B+", "3.5", ""],
  ["Tổng tín chỉ: 3"]
]
```

Các hàng có thể có số ô khác nhau do `colspan`. Ô chứa nút ảnh Chi tiết có thể
trở thành chuỗi rỗng. Điểm và tín chỉ vẫn là chuỗi; chưa chuyển sang số hoặc
xác định môn đã đạt. Client chỉ đọc bảng đầu tiên tìm được, chưa gom nhiều
bảng điểm riêng biệt hay duyệt qua nhiều trang kết quả.

### Đọc bảng tùy chọn để chẩn đoán

```text
HÀM read_tables(selector = "table"):
    kết_quả = []
    với từng tab và frame:
        với từng bảng khớp selector:
            nếu bảng không hiển thị: bỏ qua
            đọc các hàng trực tiếp của bảng và văn bản từng ô
            làm sạch bằng normalize_rows()
            nếu còn hàng:
                thêm {page_index, frame_index, table_index, rows} vào kết_quả
    trả kết_quả
```

Khác với `read_transcript()`, hàm này trả danh sách đối tượng có chỉ số vị trí
và dữ liệu của từng bảng. Nó không tự chờ bảng tùy chọn xuất hiện. Tham số
selector nên trỏ đến phần tử `table`, vì phần đọc sử dụng thuộc tính `table.rows`.

## 5. Mã giả của parser.py

```text
HÀM normalize_rows(rows):
    với từng hàng:
        với từng ô:
            tách chuỗi theo khoảng trắng, xuống dòng hoặc khoảng trắng HTML
            ghép các phần lại bằng một dấu cách
    loại hàng mà tất cả ô đều rỗng
    trả các hàng còn lại
```

Ví dụ: `"  Mã\n môn  "` thành `"Mã môn"`. Ô rỗng trong hàng có dữ liệu vẫn
được giữ để tránh dịch vị trí cột. Hàm không đổi `"8,5"` thành `8.5`, không
suy ra GPA và không gộp các lần học cùng mã môn.

## 6. Kiểm tra và giới hạn hiện tại

`tests/integrations/test_daotao_parser.py` dùng dữ liệu giả lập để kiểm tra:

- Làm sạch khoảng trắng, giữ nguyên chuỗi điểm và ô trống.
- `read_transcript()` chọn bảng tổ tiên gần nhất và giữ hàng học kỳ/tổng kết
  bằng đối tượng giả, không kết nối cổng đào tạo.

Các kiểm tra này không chứng minh đăng nhập hay điều hướng trên trang thật
đã thành công. Cần chạy thử bằng phiên tài khoản thật để xác minh selector,
frame và dấu hiệu bảng đã tải đầy đủ trước khi viết bước đồng bộ database.

### Phân biệt bảng tiêu đề và bảng dữ liệu

Trang có bảng `#ListHeader` trong `#divList2` chỉ chứa tiêu đề cột và bảng
trong `#divList3` chứa học kỳ, môn và tổng kết. Cả hai đều có ô mang
`title="Mã môn học"`. Vì vậy phải giới hạn tìm kiếm trong `#divList3`,
tránh chọn nhầm bảng tiêu đề.

## Chạy nền khi đăng nhập

Worker đăng nhập của web và CLI `tools.try_daotao` dùng `headless=True`,
không bật cửa sổ trình duyệt. Worker vẫn dùng Google Chrome (`channel="chrome"`);
CLI dùng Chromium do Playwright quản lý. Khởi động lại backend sau khi cập nhật
để áp dụng. Cách xác thực và đọc bảng không thay đổi. Chưa kiểm chứng lại phiên
VNU thật ở chế độ này; CAPTCHA/OTP vẫn chưa có luồng tương tác riêng.
