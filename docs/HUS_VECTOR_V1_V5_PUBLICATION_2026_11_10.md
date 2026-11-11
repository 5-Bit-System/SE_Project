# Đóng gói và push V1–V5 — 10/11/2026

Người dùng yêu cầu push V1–V5 lên nhánh riêng `hus-embedding-chromadb`
với tổng cộng25commit kể từ `26acab1`. Yêu cầu này cho phép commit/push
phần WIP V4/V5 và xuất bản việc chia V3 thành5commit đã yêu cầu trước đó;
các ghi chú “chưa commit/push” trong receipt/báo cáo trước đó là trạng thái
lịch sử của lượt triển khai, không phải trạng thái đợt xuất bản này.

## Phân nhóm lịch sử

| Nhóm | Commit |
| --- | ---: |
| V1 gốc, giữ nguyên ID/tác giả | 4 |
| V2 gốc, giữ nguyên ID/tác giả | 5 |
| Tài liệu tiến độ chung đã có (`884838b`) | 1 |
| V3, chia theo encoder/index/CLI/artifact/nghiệm thu | 5 |
| V4, query/runtime/tích hợp/nghiệm thu/bàn giao | 5 |
| V5, hybrid/evaluator/dev-baseline/đối chứng/bàn giao | 5 |
| Tổng từ `26acab1` | 25 |

Không tạo commit rỗng, tác giả giả hoặc ngày commit giả. V3 giữ tác giả và
AuthorDate của commit gốc `1ad85e3`; committer của lượt chia là người đã
thực hiện thao tác. V1/V2, tài liệu chung và toàn bộ lịch sử trước đó giữ
nguyên ID. V4/V5 dùng tác giả Git hiện hành. Main/nhánh của đồng đội không
được cập nhật trong yêu cầu này; không merge/deploy hoặc tự tạo PR.

Remote được kiểm trước khi chuẩn bị ở
`1ad85e3205ca9ba377f7a757ce4145ab589574fe`. Việc chia commit V3 làm lịch sử
nhánh riêng không fast-forward. Push chỉ dùng refspec đúng nhánh và lease
gắn với HEAD đó; nếu remote đã đổi thì phải dừng và kiểm tra lại. Giữ bản
gốc/recovery và bằng chứng Git local trong ignored `backups/`.

## Bảo toàn nội dung và bằng chứng

Nội dung runtime/data/evaluator và các receipt V1–V5 giữ nguyên byte so với
kết quả triển khai đã kiểm; không chạy lại inference để thay số đo. Git
attributes mới giữ nguyên các file đã ghim checksum, kể cả sự khác nhau
LF/CRLF có chủ đích. Dependency versions, model/cache, corpus/gold/source,
Chroma binary và cấu hình process đang chạy không thay đổi.

V4 được chia từ snapshot đã lưu, rồi V5 áp lên đúng snapshot đó. Vì thế
các commit tích hợp V4 và V5 thể hiện đúng hành vi theo từng bước, không
đưa cấu hình hybrid V5 vào commit V4. Không sửa receipt lịch sử để nhận
commit mới là base đã được dùng trong phép đo cũ.

Trước commit/push, kiểm lại full offline suite bằng venv CI sẵn có, Ruff,
diff whitespace, replay480prediction, policy/identity/receipt pins, số commit,
parent/author metadata và final tree/raw-file hashes. Chỉ model weights,
binary Chroma, venv, cache và backup local được loại khỏi Git như trước;
manifest/inventory/code và evidence JSON của ba mode được đưa lên nhánh.

## Giới hạn sản phẩm

Mặc định vẫn lexical; hybrid chỉ bật tường minh. Đối chứng dev160câu/mode:
Recall@5 lexical55/56,vector55/56,hybrid56/56; MRR0,87649/0,88690/0,88155,
false-refusal5/6/5. Chưa có đầy đủ review ngữ nghĩa theo response mới, chưa
nghiệm thu A7/holdout độc lập, không có LLM/provider hoặc production activation.

Kết quả push thực tế và HEAD cuối cần xác nhận bằng `git ls-remote`; log
thao tác và sơ đồ25commit được lưu riêng dưới backups để không tạo vòng
tham chiếu hash của commit đang chứa tài liệu này.
