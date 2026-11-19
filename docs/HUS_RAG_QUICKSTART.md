# Chạy chatbot HUS trên Windows

Dành cho **Windows 64-bit, Python 3.11**. Chạy từ thư mục gốc của source đã nhận,
không dùng đường dẫn hoặc máy của tác giả. Chatbot F1/F2/F3 dùng dữ liệu đi kèm;
không cần PostgreSQL, Docker, tài khoản VNU hay chatbot tư vấn chọn môn.

## 1. Cài dependency và kiểm RAG

Mở PowerShell tại thư mục có `requirements-rag.txt`:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-rag.txt -c requirements-lock.txt
.\.venv\Scripts\python.exe -X utf8 -m tools.run_hus_rag --check
.\.venv\Scripts\python.exe -X utf8 -m tools.run_hus_rag
```

Nếu máy không có lệnh `py`, dùng đường dẫn interpreter Python 3.11 của máy bạn
thay `py -3.11` ở lệnh đầu. Không cần activate venv hoặc đổi execution policy.

Mở **http://127.0.0.1:8011/**. Ctrl+C để dừng. Cổng bận thì chạy lại với
`--port 8012` rồi mở cổng8012. Server chỉ bind loopback, chưa phải server public.

Cách chạy này cố ý dùng **v4 / lexical / LLM tắt**, kể cả khi terminal có biến
LLM từ trước. Không đọc `.env`, không cần key và không gọi Google. F3 đọc hồ sơ
AI đã lưu; đó không phải sinh nội dung mới khi hỏi.

Lần cài dependency cần Internet hoặc bộ wheel phù hợp. Sau khi cài, RAG và file
PDF/DOCX local chạy offline; mở URL web nguồn vẫn cần mạng.

## 2. Bật Gemini thật trên backend — tùy chọn

Dừng server cũ bằng Ctrl+C. Nếu đã lưu **`HUS_LLM_API_KEY` trong `.env` ở gốc
dự án**, chỉ cần chạy:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m tools.run_hus_llm
```

Lệnh này tự đọc cấu hình `HUS_LLM_*` từ `.env`, bật LLM cho process đang chạy,
dùng lexical và mở server ở **http://127.0.0.1:8011/**; không hỏi nhập key.
Key đã có trong môi trường terminal được ưu tiên hơn file. Không đọc file mẫu
hoặc dùng `GEMINI_API_KEY` của chatbot tư vấn môn. Startup không gọi Google.
Nếu file backend ở chỗ khác, thêm `--env-file duong-dan-file`; cổng bận thì thêm
`--port 8012`. **Gemini tự động được dùng**, không cần tick diễn đạt.
Khi Google trả **429**, server chuyển sang RAG offline và ngừng gọi Gemini
trong process hiện tại. 429 có thể là giới hạn theo phút/ngày, không tự chứng
minh đã hết toàn bộ quota. Khi hạn mức được khôi phục, Ctrl+C rồi chạy lại
server để thử Gemini. Lỗi key/mạng/503 hoặc output bị chặn sẽ báo lỗi, không
thay bằng đáp án offline. Câu mơ hồ/thiếu bằng chứng vẫn được làm rõ trước model.

Nếu venv cũ báo thiếu `dotenv`, cập nhật dependency một lần:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-rag.txt -c requirements-lock.txt
```

### Cách nhập key tạm thời nếu chưa lưu trong file

Dùng cùng venv, dừng server ở bước1 trước. Bạn cần key Google của mình hoặc
backend dùng chung đã được nhóm cấu hình. **Không nhập key vào chat, JavaScript,
file mẫu hoặc commit Git.** Không sao chép key của người khác.

Lệnh dưới hỏi key bằng ô nhập ẩn trong PowerShell; chỉ đặt key trong môi trường
của terminal/backend hiện tại, không ghi key vào source hoặc lịch sử lệnh:

```powershell
$env:HUS_RAG_ROOT = Join-Path (Get-Location).Path "data\hus\rag"
$env:HUS_RETRIEVAL_MODE = "lexical"
$env:HUS_LLM_ENABLED = "true"
$env:HUS_LLM_AUTO = "true"
$env:HUS_LLM_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
$env:HUS_LLM_MODEL = "gemini-3.5-flash-lite"
$husGeminiSecret = Read-Host "Google API key (nhap an)" -AsSecureString
$env:HUS_LLM_API_KEY = [System.Net.NetworkCredential]::new("", $husGeminiSecret).Password
try {
    .\.venv\Scripts\python.exe -X utf8 -m uvicorn app.hus.demo:app --host 127.0.0.1 --port 8011
} finally {
    Remove-Item Env:HUS_LLM_API_KEY -ErrorAction SilentlyContinue
    $env:HUS_LLM_ENABLED = "false"
    Remove-Item Env:HUS_LLM_AUTO -ErrorAction SilentlyContinue
    Remove-Variable husGeminiSecret -ErrorAction SilentlyContinue
}
```

Dùng lệnh `uvicorn` ở trên cho profile Gemini; `tools.run_hus_rag` luôn ép LLM
tắt và không đọc key từ file. Bạn không cần sửa file mẫu; `python-dotenv` đã
có trong dependency RAG cho launcher Gemini mới. Chỉ dùng các biến `HUS_LLM_*` cho chatbot này;
`GEMINI_API_KEY` của phần tư vấn môn là cấu hình khác.

Profile này tự gọi Google khi câu hỏi có bằng chứng phù hợp. Quyền dùng F3
vẫn riêng. Startup không kiểm key bằng lời gọi provider; hãy xem trạng thái sau
khi hỏi. API profile cũ không đặt `HUS_LLM_AUTO=true` vẫn hỗ trợ opt-in thủ công.

Launcher Gemini cũng bật hiểu ý định khi luật chưa hiểu câu hỏi: gửi câu hỏi,
phạm vi và danh mục mã/tên môn công khai, nhận JSON được backend kiểm. Một câu
có thể cần tối đa hai call (hiểu ý định + diễn đạt); lỗi khác429 vẫn báo lỗi.
Có thể nhập “Ngành Toán học có bao nhiêu môn học?” hoặc “Liệt kê các môn trong
chương trình” sau khi chọn đúng ngành. Kết quả là danh mục theo phiên bản, **không
phải số môn mỗi sinh viên phải học**. Câu lọc bắt buộc/tự chọn/điều kiện chưa hỗ
trợ sẽ yêu cầu làm rõ. [Chi tiết và giới hạn](RAG_INTENT_F2_CATALOG_2026_11_14.md).

Mỗi lời gọi có thể tiêu quota/chi phí của project Google. Trong phiên làm việc
với trợ lý, mọi lượt test Google mới cần số call được thống nhất trước; lệnh
khởi động không cấp thêm ngân sách test. Không cần 9Router hoặc proxy local.

### Chạy hybrid BM25 + ChromaDB với v4

Máy local đã có môi trường `.venv-hybrid`, cache model trong
`.cache/hus/multilingual-e5-small` và index v4 riêng. Dừng server cũ, kiểm trước:

```powershell
./.venv-hybrid/Scripts/python.exe -X utf8 -m tools.run_hus_llm --retrieval hybrid --check
```

Check **không đọc key/không gọi Google**. Chỉ đạt khi `actual_mode=hybrid`, hai
nhánh có ứng viên và đúng index ID trong profile. Sau đó chạy Gemini tự động:

```powershell
./.venv-hybrid/Scripts/python.exe -X utf8 -m tools.run_hus_llm --retrieval hybrid
```

Lệnh này tự đọc key backend như mục2. F3 vẫn cần quyền tham khảo riêng. Muốn chỉ
thử hybrid offline, dùng `-m tools.run_hus_rag --retrieval hybrid` bằng cùng Python.
F1/F3 dùng BM25 + Chroma/RRF; F2 vẫn tra dữ kiện trực tiếp. Khởi động có thể chậm
do kiểm index/cache và nạp model CPU. Sau tối ưu fingerprint, lượt đối chiếu local
10 câu có search đạt median RAG **3,33giây** (1,95–3,96giây), so với6,59giây của
hàm cũ trên cùng runtime/snapshot; chưa gồm Gemini. Cold lượt mới56,48giây,
các lượt cũ65–156giây; không coi khác biệt cold là hiệu quả của bản sửa hay cam
kết trên máy khác. Chờ dòng **Hybrid ready** rồi mở trang. Nếu server đang chạy,
restart để nạp code mới. [Số đo và giới hạn](RAG_HYBRID_LATENCY_2026_11_15.md).

Profile `data/hus/vector_profiles/hybrid_v4_20261114.json` ghim contract/passages,
đường dẫn index và expected ID bên ngoài DB. Cờ `--retrieval hybrid` chọn profile
này; chỉ đổi biến môi trường trong `.env` không thay lựa chọn mặc định của launcher.
Có thể chỉ cache khác bằng `--model-cache duong-dan-cache`.

### Thử câu trả lời tập trung và chọn nguồn

Chế độ `focused` là lựa chọn kiểm thử mới, mặc định vẫn `legacy`. Kiểm offline
không cần key, có kiểm nguồn mơ hồ phải làm rõ:

```powershell
./.venv/Scripts/python.exe -X utf8 -m tools.run_hus_llm --answer-policy focused --check
```

Chạy RAG offline với cách chọn context mới:

```powershell
./.venv/Scripts/python.exe -X utf8 -m tools.run_hus_rag --answer-policy focused
```

Khi muốn thử Gemini bằng key backend đã lưu, dùng:

```powershell
./.venv-hybrid/Scripts/python.exe -X utf8 -m tools.run_hus_llm --retrieval hybrid --answer-policy focused
```

Nếu chưa chuẩn bị hybrid, dùng Python `.venv` và bỏ `--retrieval hybrid`. Khởi
chạy server chỉ nạp cấu hình; mỗi câu đủ bằng chứng gửi tới Google sẽ dùng quota
của key đã cấu hình. Các lượt kiểm của agent tiếp theo vẫn cần thống nhất budget.

Trong chế độ này, F1 có nhiều edition/hệ/nguồn sẽ hiện nút chọn nguồn; chọn nút
để gửi lại nguyên câu hỏi theo đúng nguồn đó. F3 vẫn cần quyền AI riêng. Một số
câu định nghĩa được chọn đủ đoạn giải thích liên quan trước khi diễn đạt, giữ
điều kiện/phủ định. Chưa hỗ trợ paraphrase tự do hoặc kiến thức ngoài nguồn.
Lỗi ngoài429 vẫn báo lỗi, không âm thầm trả offline.

Muốn quay lại hợp đồng cũ, restart server và bỏ `--answer-policy focused` hoặc
dùng `--answer-policy legacy`. Không cần sửa key/dữ liệu/index. Kiểm hybrid
`--retrieval hybrid --check` ở mục trên chỉ là preflight retrieval; kiểm QA
focused riêng bằng lệnh lexical `--answer-policy focused --check`.
[Phạm vi triển khai và kiểm chứng](RAG_FOCUSED_ANSWER_2026_11_15.md).

Để quay về lexical, dừng server và chạy lại không có cờ hybrid hoặc thêm
`--retrieval lexical`. Lỗi nhánh vector khi đang phục vụ có thể dùng lexical
cho **retrieval**, Gemini vẫn theo chính sách tự động/429; đây không phải chuyển
LLM sang offline. Preflight khởi động không coi fallback lexical là hybrid đạt.

**Với máy/source khác:** weights, `.venv-hybrid` và database Chroma binary là
artifact local, không nằm trong Git. Nhận đủ các artifact đã kiểm hoặc tự chuẩn
bị trước; không hứa clone source là có ngay hybrid. Cách cài môi trường:

```powershell
py -3.11 -m venv .venv-hybrid
./.venv-hybrid/Scripts/python.exe -m pip install --require-hashes -r requirements-rag-vector-lock.txt
```

Nếu thiếu model/index, dùng các công cụ hiện có với contract/passages v4:

```powershell
./.venv-hybrid/Scripts/python.exe -X utf8 -m tools.build_hus_vector_index --fetch-model --contract data/hus/vector_contracts/e5_small_v4_20261114 --model-cache .cache/hus/multilingual-e5-small
./.venv-hybrid/Scripts/python.exe -X utf8 -m tools.build_hus_vector_index --out data/hus/vector_indexes/e5_small_v4_local_r1 --contract data/hus/vector_contracts/e5_small_v4_20261114 --passages data/hus/vector_passages/e5_small_v4_20261114 --model-cache .cache/hus/multilingual-e5-small
```

`--fetch-model` là bước tải model có chủ đích, cần mạng; build dùng CPU và thư
mục output **chưa tồn tại**, không chép đè index cũ. Sau build mới, cập nhật hai
trường `index_path`/`expected_index_id` trong profile local theo đường dẫn/ID
build vừa trả về, rồi chạy lại `--check`. Không đoán/copy ID từ DB hoặc bỏ kiểm
pin khi build khác. Bộ local hiện tại được seed từ môi trường vector đã cài,
`pip check`/112 package khóa/9 file model đã kiểm; chưa thử cài PyPI sạch trên máy khác.

## 3. Thử giao diện

1. Chọn đúng ngành; phiên bản chương trình được hiển thị cạnh ngành.
2. Hỏi **“Giới thiệu ngành”** hoặc chọn câu trong menu.
3. Chọn KHDL, hỏi **“Số tín chỉ MAT3533?”**; câu trả lời phải giữ dữ kiện và nguồn.
4. Muốn F3, bật **“Cho phép kiến thức AI tham khảo”** rồi hỏi **“Nội dung MAT3533?”**.
5. Với `tools.run_hus_llm`, kiểm thông báo **Tự động dùng Gemini** rồi hỏi; không cần checkbox diễn đạt.

Ví dụ nhập tự nhiên: chọn **Khoa học dữ liệu**, bật quyền F3 rồi hỏi
**“Tôi muốn tìm hiểu về môn Thị giác máy tính”**. Chatbot tìm đúng hồ sơ
**MAT3562** trong ngành đang chọn; “Giới thiệu môn…” và “Tổng quan về môn…”
cũng được hiểu là yêu cầu nội dung tham khảo. Profile Gemini tự diễn đạt.
Sau khi cập nhật code, dừng server và chạy lại để nạp bản sửa.

Profile tự động ẩn checkbox diễn đạt và công khai việc gửi câu hỏi/bằng chứng
tới Google. Checkbox F3 vẫn cần bật để dùng kiến thức AI tham khảo. Chỉ câu hỏi/
bằng chứng cần thiết được gửi; tài khoản, bảng điểm và lịch sử chat không nằm trong luồng này.

| Trạng thái | Cách hiểu |
| --- | --- |
| **AI diễn đạt từ nguồn** | Hệ thống đã dùng đầu ra model qua kiểm tra. Vẫn cần đọc nguồn. |
| **AI diễn đạt** ở câu F3 | Đã dùng model để diễn đạt hồ sơ AI tham khảo; không hiển thị thẻ nguồn AI hoặc số dẫn chứng. |
| **Bản trích nguồn** | Trong profile tự động: đã gặp429 và dùng RAG offline; trong launcher offline: LLM tắt. |
| **kiến thức AI / Nội dung AI tham khảo** | Hồ sơ F3 do AI biên soạn, không phải đề cương chính thức; profile tự động dùng hồ sơ offline sau429. |
| **Cần làm rõ / chưa đủ thông tin** | Chọn lại ngành/môn/phiên bản hoặc hỏi rõ hơn; không tự gọi model để bịa nguồn. |

Đổi ngành sẽ bỏ câu hỏi/đáp án/nguồn cũ, tắt quyền F3 và bỏ phản hồi muộn của
ngành trước; chế độ Gemini tự động vẫn giữ. Enter gửi câu; Shift+Enter xuống dòng.

Thẻ PDF/DOCX mở file nguồn local khi có file/hash hợp lệ. Thẻ web mở URL nguồn,
không tự xác nhận hiệu lực hiện tại. F3 chỉ hiện thông báo AI tham khảo, không
lặp thẻ nguồn “kiến thức AI” hoặc số dẫn chứng. F1/F2 vẫn hiện nguồn tài liệu,
kể cả khi Gemini hỗ trợ diễn đạt.

## 4. Xử lý lỗi thường gặp

Phản hồi bị chặn có nhãn riêng: **Chưa hiểu yêu cầu**, **Chọn lại phạm vi**,
**Chưa hỗ trợ thao tác này**, **Chưa tìm thấy dữ liệu**, **Chưa đủ căn cứ trả lời**,
**Phản hồi AI bị chặn** hoặc **Lỗi dịch vụ AI**. Xem hướng xử lý trong phản hồi;
không phải mọi câu từ chối đều do BM25 hoặc Gemini. Sai ngành sẽ nêu rõ ngành
đang chọn và ngành được hỏi; chọn lại bằng ô ngành, hệ thống không âm thầm đổi.
Terminal của launcher Gemini ghi `hus_chat_block code=...`, không ghi câu hỏi,
key hoặc body lỗi thô. API502 có `detail.diagnostic` chứa mã lỗi an toàn.

| Hiện tượng | Kiểm tra |
| --- | --- |
| Checkbox diễn đạt bị khóa | Có đang chạy launcher LLM-off không? Nếu muốn Gemini, dùng profile mục2 và cấu hình đủ biến backend rồi tải lại trang. |
| Lỗi quyền AI (401/403) | Kiểm key/project/quyền trên tài khoản Google của bạn; không gửi key qua chat. Không suy một banner quota thành nguyên nhân lỗi quyền. |
| AI tạm thời chưa sẵn sàng (503)/mạng | Profile tự động báo lỗi (API502), không trả offline thay thế. Kiểm dịch vụ sau, không tự kết luận key hỏng. |
| AI chạm hạn mức (429) | Tự trả RAG offline đến khi restart; sau khi quota hồi phục hãy khởi động lại để dùng Gemini. |
| Phản hồi AI chưa đạt kiểm tra | Profile tự động báo lỗi, không hiển thị nội dung bị chặn hoặc trả offline thay thế. Không nới validator để ép dùng output. |
| Không tải được dữ liệu/nguồn | Kiểm source đã nhận đủ các file bên dưới và chạy lại `--check`. |
| Cài package hoặc import lỗi | Kiểm đúng Python3.11/venv; cài lại với cả `requirements-rag.txt` và constraint `requirements-lock.txt`. |

## 5. Source phải có và giới hạn của check

Source cần có `app/hus/`, schema/service HUS, static HUS, `tools/run_hus_rag.py`,
hai file requirements, `data/hus/rag/CURRENT.json` cùng release v4 được chọn,
registry và PDF/DOCX trong `data/hus/citation_assets/`. Không copy DB, tài khoản,
bảng điểm hoặc file secret. Source nhận đầy đủ có thể chạy; thay đổi còn local
chưa tự xuất hiện trên GitHub khi chưa commit/push theo quy trình nhóm.

`--check` kiểm release/hash, static,2.124 câu menu,20 ca API trên bốn ngành và file
nguồn được các ca đó trả về. Provider/kết nối ngoài bị chặn, không dùng key.
Nó không kiểm Gemini thật, không thay việc nhóm đọc nội dung và không chứng minh
mọi file/cách hỏi đều đã được kiểm.

`tools.run_hus_submission` là wrapper tương thích launcher RAG-offline. Không cần
ZIP trong `backups/` để chạy source. Phạm vi hỗ trợ hiện tại là Windows/Python3.11;
không có yêu cầu Linux/macOS hoặc triển khai public. Chưa chạy GitHub Actions
cho thay đổi local này.

Xem [tiến độ](RAG_PROGRESS_AND_NEXT_PLAN.md) và [bộ30 câu/nguồn để nhóm review](RAG_STUDENT_CONTENT_30_LIVE_2026_11_14.md).
