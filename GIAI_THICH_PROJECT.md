# Hiểu dự án này — bản dễ đọc nhất

> Cách đọc tài liệu này: đọc từ trên xuống như đọc truyện, không cần nhảy mục. Gặp từ tiếng Anh nào lạ, cứ đọc tiếp — ngay sau đó sẽ có giải thích hoặc bạn tra ở **Phần 7: Từ điển**.

---

## Phần 1. Dự án này làm gì? (30 giây)

Đây là một **trang web giúp sinh viên biết kỳ tới nên đăng ký môn gì**.

Bạn làm 3 việc:

1. Chọn ngành của bạn.
2. Tick những môn bạn đã học qua.
3. Gõ một câu như: *"Kỳ này mình muốn học nhẹ, thích tìm hiểu về thị giác máy tính."*

Hệ thống trả về 3–5 môn gợi ý. Mỗi môn kèm **2 lý do**:

- Vì sao bạn **được phép** học môn này (đã qua môn tiên quyết nào, thuộc nhóm nào).
- Vì sao môn này **phù hợp** với điều bạn muốn.

Điểm đặc biệt: hệ thống **không bao giờ gợi ý môn bạn chưa đủ điều kiện**, dù bạn tha thiết muốn học nó đến đâu. Đây là điều quan trọng nhất của cả dự án.

---

## Phần 2. Hệ thống giống một nhà hàng

Hãy tưởng tượng dự án này là một nhà hàng. Mỗi file trong dự án là một người/vị trí trong nhà hàng đó. Hiểu ví von này là hiểu 80% dự án.

| Trong nhà hàng | Trong dự án | Việc nó làm |
|---|---|---|
| **Quầy tiếp khách + menu** | `app/static/` (trang web) | Nơi bạn nhìn thấy, bấm nút, gõ chat |
| **Nhân viên phục vụ** | `app/api/routes.py` | Nhận order từ khách, chuyển cho bếp, mang kết quả ra |
| **Tổ trưởng ca** | `app/services/` | Nhận việc từ phục vụ, chuyển cho đúng đầu bếp chuyên môn |
| **Sổ quy định + biểu mẫu** | `app/models.py`, `app/schemas/` | Quy định dữ liệu phải có hình dạng thế nào (mã môn không được rỗng, điểm 0–10…) |
| **Nhân viên kiểm tra điều kiện** | `app/rules.py` | Người nói: "Khách này chưa được dùng nguyên liệu X" — quan trọng nhất nhà hàng |
| **Đầu bếp chính** | `app/service.py` | Nấu món "danh sách môn gợi ý" |
| **Phụ bếp** | `app/recommendation/` (5 file) | Hiểu khách muốn gì, chấm điểm món, kiểm tra món hợp lệ, viết lời giới thiệu món |
| **Chuyên gia thuê ngoài** | AI (Gemini) | Giúp câu chữ tự nhiên hơn. Không được tự quyết định món nào được dọn ra |
| **Bếp trưởng kiêm chăm sóc khách** | `app/advisor.py` | Nút chat nổi: trả lời câu hỏi, từ chối câu hỏi ngoài phạm vi |
| **Thủ kho** | `app/catalog.py`, `app/infrastructure/` | Nơi lấy dữ liệu môn học |
| **Kho lạnh** | PostgreSQL (trong `app/db/`) | Nơi dữ liệu ở khi hệ thống chạy thật |
| **Sổ giấy gốc trong kho** | `data/` (file JSON) | Bản gốc giấy tờ, dùng để nhập lại vào kho lạnh |
| **Xe nhập hàng định kỳ** | `tools/` | Kiểm tra hàng và chở hàng từ sổ giấy vào kho lạnh |
| **Bảng nội quy** | `app/config.py` | Đọc cấu hình: dùng kho nào, có bật AI không |
| **Danh sách mã lỗi** | `app/errors.py` | "Hết hàng" (404), "kho không mở cửa" (503), "hàng lỗi" (500) |
| **Thanh tra vệ sinh** | `tests/` | Tự động kiểm tra mọi thứ còn đúng quy định không |

Ba câu thần chú của nhà hàng này:

1. **Đổi ngành = dọn sạch bàn**: đổi ngành là xóa hết môn đã tick và lịch sử chat, không trộn hai ngành.
2. **Kiểm tra điều kiện TRƯỚC, xếp hạng SAU**: chuyên gia thuê ngoài chỉ được nhìn thấy danh sách môn đã hợp lệ. Không có AI nào được mở khóa môn.
3. **Thiếu dữ liệu thì nói thiếu**: không đoán bừa. Không biết môn có mở lớp không thì ghi rõ "chưa xác minh".

---

## Phần 3. Ba tầng của hệ thống

Hệ thống có 3 tầng tách bạch, đi từ ngoài vào trong:

```
TẦNG 1 — KHÁCH NHÌN THẤY (frontend)
  app/static/index.html   ← trang web
  app/static/app.js       ← não của trang web (bấm nút gì, gọi API nào)
  app/static/styles.css   ← màu sắc, bố cục

TẦNG 2 — BẾP (backend, viết bằng Python + FastAPI)
  app/main.py             ← cửa vào của cả máy chủ
  app/api/routes.py       ← danh sách các "địa chỉ API"
  app/services/*          ← tổ trưởng ca (chuyển việc)
  app/rules.py, service.py, advisor.py, ... ← các đầu bếp
  app/recommendation/*    ← phụ bếp

TẦNG 3 — KHO (nơi giữ dữ liệu)
  PostgreSQL (kho lạnh)            hoặc
  data/curricula/*.json (sổ giấy)  ← tùy cấu hình chọn kho nào
```

### API là gì?

**API** là "địa chỉ để gọi đồ ăn". Trang web muốn xin dữ liệu thì gửi một yêu cầu (request) tới một địa chỉ API, ví dụ:

- `GET /programs` — xin danh sách 4 ngành.
- `POST /eligibility` — xin kiểm tra môn nào đủ điều kiện.
- `POST /recommendations` — xin gợi ý môn.
- `POST /advisor/chat` — gửi một câu chat.

**GET** giống như "hỏi xem có gì", **POST** giống như "đưa dữ liệu lên để xử lý".

### Frontend "nói chuyện" với backend thế nào?

Trang web (app.js) dùng một hàm tên `fetch()` để gửi yêu cầu tới API, nhận kết quả dạng **JSON** (văn bản có cấu trúc) rồi vẽ lên màn hình. Frontend **không chứa logic kiểm tra điều kiện** — nó chỉ hiển thị và gửi yêu cầu.

⚠️ Quan trọng: **API key của AI chỉ nằm ở backend**. Trình duyệt của bạn không bao giờ thấy chìa khóa đó. Bạn cũng không bao giờ thấy nó trong file gửi lên GitHub.

---

## Phần 4. BỐN HÀNH TRÌNH — đọc kỹ phần này là hiểu cả dự án

Tôi kể 4 hành trình thật: một yêu cầu của bạn đi qua những file nào, gặp ai, rồi quay về màn hình thế nào.

### Hành trình 1: Chọn ngành và tick môn đã học

**Câu chuyện:** Bạn mở trang web, chọn ngành "Khoa học dữ liệu", tick môn "INT1006 Lập trình", rồi nhìn ô tín chỉ và GPA tự nhảy số.

**Từng bước, ai gọi ai:**

```
1. Bạn mở http://127.0.0.1:8000
   → app/main.py nhận, trả file index.html về
   → index.html kéo theo app.js và styles.css

2. app.js tự gọi GET /programs
   → app/main.py chuyển cho app/api/routes.py (hàm programs())
   → routes.py gọi app/services/catalog_service.py
   → catalog_service.py gọi app/catalog.py (hàm list_catalogs)
   → catalog.py hỏi: cấu hình đang dùng kho nào?
        Nếu kho lạnh (Postgres): gọi app/infrastructure/postgres_repository.py
        Nếu sổ giấy (JSON):    gọi app/infrastructure/json_catalog_repository.py
   → kết quả được gói lại, trả về cho app.js
   → app.js đổ danh sách ngành vào ô chọn (dropdown)

3. Bạn chọn ngành "Khoa học dữ liệu"
   → app.js gọi GET /courses?program_id=khdl_7460108_2022 (xin danh sách môn)
   → đi đúng con đường như trên (routes → service → catalog → kho)
   → app.js vẽ danh sách 65 môn thành các ô tick

4. Bạn tick "INT1006"
   → app.js lưu vào bộ nhớ tạm của trang web (không gửi lên server vội)
   → app.js gọi POST /transcript/summary, gửi lên {ngành + danh sách môn + điểm}

5. app/api/routes.py (hàm transcript_summary) nhận dữ liệu
   → gọi app/transcript.py để tạo "bảng điểm" (StudentTranscript)
       • transcript.py kiểm tra: mã môn phải viết hoa, điểm 0–10, kỳ 1–12
       • tự tính “đậu” nếu điểm >= 5
       • kiểm tra cô lập ngành: môn này có thuộc ngành đang chọn không?
   → gọi catalog.py để lấy đúng ngành đó
   → gọi transcript.py tính: tổng tín chỉ, GPA hệ 10, GPA hệ 4
   → app/main.py gói kết quả, trả về

6. app.js nhận kết quả, đổ số lên các ô KPI (số môn đậu, tín chỉ, GPA)
```

**Vì sao các file được tách như vậy?** Vì mỗi file có 1 việc riêng:

- `routes.py` chỉ lo "nhận order, trả hàng" — không chứa logic.
- `services/` chỉ là "tổ trưởng" đứng giữa, sau này đổi logic bên trong không cần sửa API.
- `transcript.py` lo mọi thứ về bảng điểm.
- `catalog.py` là "người gác cổng kho" — ai muốn lấy dữ liệu môn học đều phải đi qua nó.

### Hành trình 2: Gõ câu xin gợi ý môn — hành trình quan trọng nhất

**Câu chuyện:** Bạn gõ: *"Kỳ này muốn học nhẹ, thích thị giác máy tính"* và bấm "Gợi ý". Hệ thống phải nghĩ ra vài môn và giải thích vì sao.

Đây là hành trình dài nhất, đi qua 4 chặng:

```
CHẶNG 1 — KIỂM TRA ĐIỀU KIỆN (bắt buộc chạy trước, do app/rules.py làm)

   Bạn gửi: ngành + môn đã qua + câu mong muốn
   → routes.py gọi app/service.py (hàm recommend)
   → service.py gọi app/rules.py (hàm evaluate_eligibility)

   rules.py duyệt từng môn trong ngành và trả lời 2 câu hỏi cho mỗi môn:
       "Cho học": đã đậu tiên quyết chưa? đúng track chưa? còn chỗ trong nhóm tự chọn không?
       "Chặn": thiếu môn nào thì ghi rõ tên môn thiếu

   Kết quả: 2 danh sách — "môn ĐỦ ĐIỀU KIỆN" và "môn BỊ CHẶN (kèm lý do)"

   ⚠️ Từ đây, AI chỉ được NHÌN thấy danh sách "đủ điều kiện". Môn bị chặn vĩnh viễn
      không thể xuất hiện trong kết quả, bất kể AI nói gì.

CHẶNG 2 — HIỂU CÂU BẠN MUỐN GÌ (do app/recommendation/preference.py làm)

   → service.py gọi preference.py (hàm extract_structured_preference)
   → nó biến câu văn thành 1 "phiếu mong muốn" (StructuredPreference):
        học nhẹ     → workload = "light"
        thích thị giác máy tính → quan tâm chủ đề "computer_vision"
        các mục chưa nói → để trống, KHÔNG đoán

   Nếu có bật AI: AI cũng làm được việc này (app/recommendation/llm.py), nhưng nếu AI
   lỗi hoặc chưa cấu hình thì quay về cách "đếm từ khóa" ở trên.

CHẶNG 3 — XẾP HẠNG CÁC MÔN ĐỦ ĐIỀU KIỆN (do app/ranking.py hoặc AI làm)

   → ra lệnh cho "bếp chính" (service.py) gọi app/ranking.py (hàm KeywordRanker)
   → nó gọi app/recommendation/scoring.py chấm điểm từng môn từ 0 tới 1:
        môn có chủ đề "computer_vision" trong dữ liệu  → điểm cao
        môn chứa từ trong câu bạn gõ trong tên         → điểm cộng thêm
        môn có metadata "nhẹ" (nếu dữ liệu có)         → điểm cộng thêm
        môn thiếu dữ liệu độ nhẹ                       → KHÔNG cộng điểm (không đoán)
   → sắp xếp từ điểm cao xuống thấp (bằng điểm thì theo mã môn, để luôn ổn định)

   Nếu có AI: AI được thấy danh sách đủ điều kiện + phiếu mong muốn và trả về thứ tự.
   Nhưng AI trả thế nào cũng phải đi qua cửa kiểm tra ở chặng 4.

CHẶNG 4 — KIỂM TRA KẾT QUẢ, RỒI GIẢI THÍCH (validation + explanation)

   → service.py gọi app/recommendation/validation.py
        kiểm tra từng mã môn trong kết quả: có nằm trong danh sách đủ điều kiện không?
        mã lạ, mã trùng, mã đã học → loại hết, kèm cảnh báo
   → nếu kết quả bị loại sạch → tự dùng lại cách xếp hạng đếm từ khóa (fallback)
   → chọn môn vào danh sách cuối: đi từ điểm cao xuống, dừng khi
        hết chỗ tín chỉ (bạn đặt "tối đa 12 tín chỉ" thì không vượt)
        hoặc đủ số môn (bạn đặt "lấy 5 môn" thì dừng ở 5)

   Với mỗi môn được chọn, viết 2 lý do:
        "Đủ điều kiện: ..." ← lấy từ lý do của rules.py ở chặng 1
        "Phù hợp: ..."      ← do app/recommendation/explanation.py + scoring.py viết

   Luôn kèm cảnh báo: "Trạng thái mở lớp trong học kỳ chưa được xác minh"

   → kết quả quay về routes.py → về app.js → hiện thành các thẻ môn trên màn hình
```

**Vì sao thiết kế kiểu này?** Vì muốn đảm bảo: **không có môn nào thiếu tiên quyết lọt vào kết quả**. AI chỉ được làm 3 việc: hiểu câu bạn muốn gì, sắp xếp thứ tự các môn đã hợp lệ, viết lời giải thích. AI không bao giờ quyết định môn nào được học.

### Hành trình 3: Bấm nút chat hỏi

**Câu chuyện:** Bạn nhấn nút chat nổi và hỏi: *"Ngành KHDL có môn nào hay không?"* — hoặc hỏi: *"Lịch học thứ 7 có môn nào không?"*

```
1. app.js gọi POST /advisor/chat (gửi câu hỏi + môn đã học + lịch sử chat)

2. app/api/routes.py (hàm advisor_chat_endpoint) nhận
   → gọi app/advisor.py (hàm chat_advisor)

3. advisor.py TRƯỚC TIÊN kiểm tra phạm vi (gọi là "guardrail" — rào chắn):
        Hỏi về thời khóa biểu, xếp lịch, trùng tiết?  → từ chối lịch sự, hết chuyện
        Hỏi về giảng viên nào dễ tính?               → từ chối lịch sự, hết chuyện
        Hỏi bình thường về môn học                   → đi tiếp

4. advisor.py gọi app/rules.py để tự tính lại danh sách môn đủ điều kiện
   (không tin danh sách nào khác — luôn tự kiểm tra)

5. advisor.py gọi app/recommendation/preference.py để hiểu bạn muốn gì
   (ưu tiên câu bạn vừa gõ; thiếu gì thì lấy thêm từ lịch sử chat)

6. advisor.py chuẩn bị "phiếu dữ kiện": các môn đủ điều kiện + điểm + lý do

7. Nếu có cấu hình AI (Gemini):
        → advisor.py nhờ AI viết câu trả lời (chỉ được thấy môn đủ điều kiện)
        → khi AI trả lời xong, advisor.py kiểm tra:
             AI có đang khuyên học môn bị chặn không? → nếu có, coi như lỗi
             AI có bịa mã môn không? → che mã lạ đi, thay bằng "mã ngoài catalog"
        → trả về câu trả lời của AI

8. Nếu KHÔNG có AI, hoặc AI lỗi mạng:
        → advisor.py tự viết câu trả lời bằng "công thức có sẵn":
             "Chào bạn, dựa trên ngành ... bạn nên cân nhắc 4 môn này ..."
             kèm 2 môn bị chặn làm ví dụ và lời khuyên học môn cơ sở trước
        → trả về câu trả lời tự viết
```

Chú ý: dù là AI hay tự viết, **câu trả lời luôn bám dữ liệu thật**, không bịa.

### Hành trình 4: Dữ liệu vào kho — từ PDF đến lúc chạy được

**Câu chuyện:** Làm sao 290 môn học chui được vào hệ thống?

```
1. Người nhập liệu mở PDF khung chương trình của trường
   → chép tay từng dòng vào data/curricula/<tên-ngành>/source_rows.json
     (giữ nguyên mã, tên, tín chỉ, tiên quyết + ghi rõ số trang PDF)
   → KHÔNG dùng OCR, chép tay rồi đối chiếu — vì cần chính xác tuyệt đối

2. Xây thêm 2 file cho mỗi ngành:
   → curriculum.json: khung ngành (nhóm tự chọn, quota tín chỉ, track, nhánh tốt nghiệp)
   → courses.json: danh sách môn (mã, tên, tín chỉ, tiên quyết dạng AND/OR)

3. Chạy tools/build_catalogs.py --check (xe nhập hàng kiểm tra hàng)
   → nó kiểm tra: mã môn trùng không? mã tiên quyết có tồn tại không?
     tiên quyết có tạo vòng tròn không (A cần B, B cần A)? nhóm/track có hợp lệ không?

4. Chạy tools/seed_database.py (xe chở hàng vào kho lạnh)
   → nó kiểm tra lại toàn bộ + 12 hồ sơ sinh viên demo
   → băm nội dung thành 1 mã "revision" (phiên bản)
   → mở 1 giao dịch: nạp môn, tiên quyết, nhóm, hồ sơ vào PostgreSQL
   → nếu nội dung y hệt lần trước: bỏ qua (không tạo rác)
   → nếu nội dung thay đổi: tạo phiên bản mới, tắt phiên bản cũ

5. Lúc chạy thật, app/infrastructure/postgres_repository.py chỉ đọc
   phiên bản đang bật (active) → đó là dữ liệu hiện hành

6. Trước khi nạp lần đầu, phải chạy python -m alembic upgrade head
   → alembic tạo sẵn các bảng trong PostgreSQL (programs, catalog_revisions, courses...)
```

Chi tiết hay: trong database, mỗi bảng khóa bằng cặp `(revision_id + mã môn)`. Nghĩa là môn của ngành A **không thể trỏ nhầm** sang môn của ngành B — cô lập ngành được khóa chặt ngay trong kho.

---

## Phần 5. Bản đồ file — ai gọi ai

Phần này liệt kê **tất cả file**, mỗi file trả lời 3 câu: *Nó là ai? Ai gọi nó? Nó gọi ai?*

### 5.1. Cửa vào + cấu hình

**`app/main.py`** — Lễ tân của cả nhà hàng.
- Việc làm: mở cửa (tạo app FastAPI), gắn trang web, gắn danh sách API, xử lý lỗi chung.
- Ai gọi nó: trình duyệt gọi thẳng (`/`, `/health`, `/ready`), hoặc nó tự chạy khi khởi động (kiểm tra kho đã sẵn sàng chưa).
- Nó gọi ai: `app/api/routes.py`, `app/config.py`, `app/errors.py`.
- `GET /` trả trang chủ. `GET /health` = "máy còn sống không?". `GET /ready` = "kho + dữ liệu sẵn sàng chưa?".
- Khi lỗi: mất kho → trả lỗi 503; dữ liệu sai → trả lỗi 500. Không tự ý đổi kho.

**`app/config.py`** — Bảng nội quy.
- Việc làm: đọc file `.env` ở **đúng một chỗ** cho cả dự án: dùng kho nào (postgres hay json), địa chỉ kho, chìa khóa AI, mô hình AI nào.
- Ai gọi nó: gần như mọi file cần cấu hình.
- Đặc biệt: mặc định dùng PostgreSQL; sai cấu hình là báo lỗi ngay lúc khởi động, không chạy nửa vời.

**`app/errors.py`** — Danh sách mã lỗi.
- 3 lỗi: `CatalogError` (xin ngành không có → 404), `StorageUnavailable` (kho đóng cửa → 503), `StorageDataError` (dữ liệu trong kho hỏng → 500).
- Ai gọi nó: `main.py`, `catalog.py`, `infrastructure/*`.
- Nó gọi ai: không ai (chỉ định nghĩa).

### 5.2. Giấy tờ + khuôn dữ liệu

**`app/models.py`** — Sổ quy định hình dạng dữ liệu.
- Việc làm: định nghĩa mọi "khuôn" dữ liệu dùng chung toàn hệ thống: `Program` (ngành), `Course` (môn), `Catalog` (ngành + môn), `StructuredPreference` (phiếu mong muốn), `RecommendationRequest/Response` (đơn xin gợi ý + kết quả), `EligibilityResult` (kết quả kiểm tra điều kiện), `BlockedCourse` (môn bị chặn + lý do)…
- Điểm cần biết: tiên quyết lưu dạng **danh sách lồng danh sách**. Danh sách ngoài = AND (phải thỏa tất cả). Trong 1 nhóm = OR (chỉ cần 1 môn). Ví dụ `[[A, B], [C]]` = "(A hoặc B) VÀ C".
- Ai gọi nó: gần như mọi file.
- Nó gọi ai: không (chỉ định nghĩa khuôn).

**`app/schemas/`** — Khuôn riêng cho từng loại API (6 file).
- `catalog.py`: khuôn trả về thông tin ngành + số môn.
- `eligibility.py`: khuôn cho API `/eligibility`.
- `recommendation.py`: khuôn đơn xin gợi ý và kết quả gợi ý (kể cả đơn "what-if").
- `profile.py`: khuôn cho hồ sơ sinh viên demo và bảng điểm tóm tắt.
- `advisor.py`: khuôn cho chat.
- `transcript.py`: khuôn bảng điểm người dùng nhập.
- Vì sao tách riêng khỏi `models.py`: để đổi cấu trúc API không làm hỏng logic nội bộ, và ngược lại.

**`app/recommendation/validation.py`, `app/recommendation/explanation.py`** — hai "cửa kiểm tra" nhỏ đã kể ở Hành trình 2 (lọc mã lạ, viết lý do).

### 5.3. Người gác cổng + thủ kho

**`app/catalog.py`** — Người gác cổng kho dữ liệu.
- Việc làm: 2 hàm `load_catalog(mã ngành)` và `list_catalogs()`. Nó tự xem cấu hình rồi định tuyến: cấu hình `json` → đọc sổ giấy; còn lại → đọc kho lạnh Postgres.
- Ai gọi nó: `routes.py` (qua `services`), `service.py`, `advisor.py`, `profiles.py`.
- Nó gọi ai: `infrastructure/json_catalog_repository.py` hoặc `infrastructure/postgres_repository.py`.

**`app/catalog_validation.py`** — Máy soi khung chương trình.
- Việc làm: kiểm tra ngành có hợp lệ không: nhóm tự chọn trùng nhau? track trỏ tới nhóm không tồn tại? nhánh tốt nghiệp chứa môn không có thật?
- Ai gọi nó: cuối mỗi lần đọc catalog (cả 2 kho đều gọi).
- Nó gọi ai: không.

**`app/infrastructure/json_catalog_repository.py`** — Thủ kho sổ giấy.
- Việc làm: đọc `data/curricula/<ngành>/curriculum.json` + `courses.json`, kiểm tra, trả về.
- Ai gọi nó: `catalog.py`.
- Dùng khi nào: làm việc offline, test, hoặc seed dữ liệu.

**`app/infrastructure/postgres_repository.py`** — Thủ kho kho lạnh.
- Việc làm: đọc PostgreSQL: tìm phiên bản catalog đang bật → lấy môn → ráp lại tiên quyết + nhóm tự chọn → trả về. Còn có hàm đọc 12 hồ sơ demo và hàm `ready()` kiểm tra kho.
- Ai gọi nó: `catalog.py`, `profiles.py`, `main.py` (lúc khởi động).
- Nó gọi ai: `app/db/session.py` (mở kết nối), `app/db/schema.py` (biết tên bảng), `catalog_validation.py`.

**`app/db/session.py`** — Người giữ chùm chìa khóa kho.
- Việc làm: tạo kết nối tới PostgreSQL, có "hồ bơi" 5 kết nối dùng lại (pool), tự kiểm tra kết nối còn tốt không trước khi dùng.
- Ai gọi nó: `postgres_repository.py`, `tools/seed_database.py`.

**`app/db/schema.py`** — Bản thiết kế các bảng trong kho lạnh.
- Việc làm: định nghĩa 7 bảng: `programs` (ngành) → `catalog_revisions` (phiên bản) → `courses` (môn), `prerequisite_groups/options` (tiên quyết AND/OR), `choice_group_courses` (môn thuộc nhóm nào), `demo_profiles` + `transcript_records` (12 hồ sơ).
- Ai gọi nó: `postgres_repository.py`, `tools/seed_database.py`, `alembic`.
- Chi tiết: khóa kép `(revision_id + mã môn)` khóa chặt cô lập ngành.

### 5.4. Các đầu bếp (logic chính)

**`app/transcript.py`** — Nhân viên hồ sơ bảng điểm.
- Việc làm:
  - `TranscriptRecord`: 1 dòng điểm — mã môn tự viết hoa, điểm 0–10, kỳ 1–12; có điểm thì tự biết đậu/rớt (>= 5 là đậu).
  - `StudentTranscript`: cả bảng điểm — biết môn nào đậu/rớt, tính tổng tín chỉ, GPA hệ 10, GPA hệ 4, và "kiểm tra cô lập ngành" (môn có thuộc ngành đang chọn không).
  - Bảng quy đổi điểm hệ 10 sang hệ 4, và từ điển tên ngắn ngành ("khdl" = "khdl_7460108_2022").
- Ai gọi nó: `routes.py`, `profiles.py`, `catalog.py` (dùng tên ngắn), `service.py`, `advisor.py`.
- Nó gọi ai: `models.py`.

**`app/profiles.py`** — Quản lý 12 hồ sơ sinh viên giả lập.
- Việc làm: đọc 12 hồ sơ demo (3 hồ sơ mỗi ngành, 4 ngành), kiểm tra kỹ: không trùng môn, môn nào cũng có kỳ học, môn học sau phải đúng thứ tự tiên quyết (tiên quyết phải học kỳ trước, không thể cùng kỳ), hướng theo hợp lệ.
- Ai gọi nó: `routes.py`, `tools/seed_database.py`.
- Nó gọi ai: `transcript.py`, `catalog.py`, và kho (Postgres hoặc file `data/synthetic/profiles.json`).

**`app/rules.py`** — Nhân viên kiểm tra điều kiện. **File quan trọng nhất dự án.**
- Việc làm: với từng môn, trả lời "được học" hay "bị chặn + lý do". Kiểm tra theo thứ tự:
  1. Môn có xung đột nguồn tài liệu? → chặn.
  2. Thiếu tiên quyết? → chặn, ghi rõ thiếu môn nào.
  3. Môn thuộc track khác với track đã chọn? → chặn.
  4. Môn thuộc nhánh tốt nghiệp khác? → chặn.
  5. Nhóm tự chọn đã đủ chỉ tiêu? → chặn.
  6. Môn nặng hơn cả tổng ngân sách tín chỉ? → chặn.
  7. Không dính gì? → cho vào danh sách đủ điều kiện.
- Ai gọi nó: `service.py`, `advisor.py`, `routes.py`, `tools` (gián tiếp).
- Nó gọi ai: `models.py`.

**`app/service.py`** — Đầu bếp chính (hàm `recommend`). Điều phối cả Hành trình 2: kiểm tra → xin preference → xếp hạng → validate → chọn môn theo tín chỉ → viết lý do → đóng gói kết quả + cảnh báo.
- Ai gọi nó: `routes.py` (qua `services/recommendation_service.py`), `advisor.py` (dùng chung cách viết lý do).
- Nó gọi ai: `rules.py`, `recommendation/preference.py`, `recommendation/scoring.py`, `recommendation/validation.py`, `recommendation/explanation.py`, `ranking.py`, `models.py`, `transcript.py`.

**`app/ranking.py`** — Người sắp xếp đơn giản.
- Việc làm: `KeywordRanker` — chấm điểm mọi môn bằng `scoring.py` rồi xếp từ cao xuống thấp. Bằng điểm thì xếp theo mã môn (để kết quả luôn giống nhau ở mọi lần chạy).
- Ai gọi nó: `service.py`.
- Nó gọi ai: `recommendation/scoring.py`.

**`app/advisor.py`** — Bếp trưởng kiêm chăm sóc khách (nút chat nổi).
- Việc làm: (1) rào chắn — từ chối câu hỏi ngoài phạm vi; (2) tự kiểm tra điều kiện lại; (3) hiểu bạn muốn gì (ưu tiên câu mới, bổ sung từ lịch sử chat); (4) nhờ AI viết câu trả lời, kèm kiểm tra an toàn; (5) nếu AI lỗi/không có → tự viết câu trả lời bằng công thức sẵn.
- Có 2 danh sách từ khóa: "thời khóa biểu, xếp lịch, trùng tiết…" và "giảng viên, thầy nào, cho điểm cao…". Thấy là từ chối lịch sự.
- Ai gọi nó: `routes.py` (qua `services/advisor_service.py`).
- Nó gọi ai: `rules.py`, `recommendation/preference.py`, `recommendation/scoring.py`, `recommendation/explanation.py`, `recommendation/validation.py`, `config.py`.

**`app/recommendation/preference.py`** — Người hiểu câu chat (bản không cần AI).
- Việc làm: biến câu văn thành phiếu mong muốn: "nhẹ"→workload light; "khó"→difficulty advanced; "thực hành"→orientation practice; "thị giác máy tính"→chủ đề computer_vision; "6 tín chỉ"→target 6; "3 môn"→target 3…
- Ai gọi nó: `service.py`, `advisor.py`, `ranking.py` (khi cần).
- Nó gọi ai: `models.py`.

**`app/recommendation/scoring.py`** — Người chấm điểm món.
- Việc làm: cho mỗi môn 1 điểm từ 0 đến 1, dựa trên: chủ đề có trùng không, từ khóa trong câu có xuất hiện không, loại môn/định hướng/độ nhẹ có đúng không. Điểm được nhân theo "trọng số" (ví dụ chủ đề 0.6, từ khóa 0.25…).
- Nguyên tắc vàng: **thiếu dữ liệu = 0 điểm, không đoán bừa**.
- Còn có `fit_reason()` viết 1 câu lý do phù hợp.
- Ai gọi nó: `ranking.py`, `service.py`, `advisor.py`.

**`app/recommendation/llm.py`** — Cầu nối với AI bên ngoài.
- Việc làm: nếu cấu hình cho phép và có chìa khóa AI → tạo 2 "adapter" (bộ chuyển đổi): 1 cái nhờ AI hiểu câu (trả về phiếu mong muốn), 1 cái nhờ AI xếp hạng (trả về thứ tự mã môn). Nó còn biết đọc câu trả lời của AI kể cả khi AI viết lộn xộn (gỡ ```json, cắt đoạn JSON).
- Nếu không có chìa khóa → trả về "không có gì" (None), cả hệ thống dùng cách đếm từ khóa.
- Ai gọi nó: `service.py`, `routes.py` (hàm `configured_adapters`).

### 5.5. Cửa API + lớp đệm

**`app/api/routes.py`** — Nhân viên phục vụ. Danh sách địa chỉ API:

| Địa chỉ | Việc nó làm |
|---|---|
| `GET /programs` | Trả danh sách 4 ngành |
| `GET /courses?program_id=...` | Trả danh sách môn của 1 ngành |
| `GET /profiles` | Trả 12 hồ sơ demo |
| `GET /profiles/{id}` | Trả chi tiết 1 hồ sơ |
| `GET /profiles/{id}/transcript/summary` | Trả tóm tắt bảng điểm của hồ sơ đó |
| `POST /transcript/summary` | Nhận bảng điểm bạn nhập → trả tín chỉ, GPA, kiểm tra cô lập ngành |
| `POST /eligibility` | Nhận ngành + môn đã qua → trả 2 danh sách đủ điều kiện / bị chặn |
| `POST /recommendations` | Nhận ngành + môn đã qua + câu mong muốn → trả môn gợi ý |
| `POST /recommendations/what-if` | Như trên nhưng đổi trọng số, không đổi điều kiện |
| `POST /advisor/chat` | Nhận câu chat → trả câu trả lời |

- Ai gọi nó: `app/main.py` (gắn vào), trình duyệt (gọi thẳng).
- Nó gọi ai: `app/services/*`.
- Khi lỗi: xin ngành không có → 404; dữ liệu gửi sai (mã môn ngoài ngành, track lạ, ngân sách sai) → 422 kèm mã lỗi đọc được bằng máy, ví dụ `unknown_passed_course_codes`.

**`app/services/*`** — Tổ trưởng ca (6 file, mỗi file vài dòng).
- `catalog_service.py`, `transcript_service.py`, `eligibility_service.py`, `recommendation_service.py`, `profile_service.py`, `advisor_service.py`.
- Việc làm: chỉ "chuyển tiếp" — nhận yêu cầu rồi gọi đúng hàm ở file chính. Ví dụ `recommendation_service.py` chỉ có 1 dòng: lấy hàm `recommend` từ `service.py`.
- Vì sao tồn tại: để `routes.py` chỉ nói chuyện với "tổ trưởng", còn ai làm việc thì tùy. Sau này đổi nội bộ, API không đổi.

### 5.6. Trang web (frontend)

**`app/static/index.html`** — Bộ mặt trang web: 3 tab (Hồ sơ / Điều kiện / Gợi ý), ô chọn ngành, danh sách tick môn, form gợi ý, nút chat nổi.

**`app/static/app.js`** — Não của trang web (~1000 dòng). Việc làm:
- Giữ "trạng thái" hiện tại: ngành nào, môn nào đã tick, chat tới đâu…
- Gọi API bằng `fetch`, nhận JSON, vẽ lên màn hình.
- 3 tab: Tab Hồ sơ (tick môn → gọi transcript → hiện KPI), Tab Điều kiện (gọi eligibility → 2 cột đủ/bị chặn), Tab Gợi ý (gửi câu + tín chỉ → hiện thẻ môn; nút what-if gửi trọng số mới).
- Nút chat: gửi câu + lịch sử (tối đa 8 tin) → hiện bong bóng chat.
- Đặc biệt: **đổi ngành là tự xóa sạch môn đã tick + lịch sử chat** (cô lập ngành phía người dùng).

**`app/static/styles.css`, `favicon.svg`** — Trang trí + biểu tượng, không có logic.

### 5.7. Công cụ nhập hàng + lịch sử kho

**`tools/build_catalogs.py`** — Xe kiểm tra hàng.
- Việc làm: đọc các dòng nguồn, kiểm tra catalog có sạch không (mã trùng? tiên quyết vòng tròn? nhóm/track lệch?), có thể ghi lại file catalog.
- Lệnh: `--check` (chỉ kiểm tra), `--check --report` (kiểm tra + in chi tiết), `--write` (ghi lại — hiện cấm chạy trên mẫu bàn giao).
- Ai gọi nó: bạn (thủ công), `tools/seed_database.py` (gọi lại để kiểm tra chung).

**`tools/seed_database.py`** — Xe chở hàng vào kho lạnh.
- Việc làm: kiểm tra 4 ngành + 12 hồ sơ → băm nội dung thành mã phiên bản → nạp vào PostgreSQL trong 1 giao dịch (được tất cả hoặc không gì cả). Chạy lại mà dữ liệu y hệt: không tạo bản mới.
- Ai gọi nó: bạn chạy tay: `python -m tools.seed_database`.

**`alembic/`** — Sổ lịch sử xây dựng kho lạnh.
- `versions/20261014_01_initial.py`: bản thiết kế xây dựng lần đầu (tạo các bảng).
- `env.py`: cấu hình Alembic (biết dùng kết nối nào, so với schema hiện tại).
- Lệnh: `python -m alembic upgrade head` (xây/nâng cấp kho), `python -m alembic check` (kiểm tra kho có lệch thiết kế không).

**`docker-compose.yml`** — Nút bật kho lạnh.
- Chỉ chạy 1 thứ: PostgreSQL 16 (tên `se_recommender_db`). Dữ liệu giữ trong volume `se_recommender_pgdata` (không mất khi tắt máy). Cổng mở ở `127.0.0.1:5432`.
- Lệnh: `docker compose up -d db`.

**`pyproject.toml`, `requirements*.txt`, `.env.example`** — Nội quy công cụ: danh sách thư viện cần cài, cách chạy test, mẫu cấu hình (không chứa bí mật thật).

### 5.8. Dữ liệu

**`data/curricula/khdl_7460108_2022/`** — Bộ mẫu Data Science 2022 (65 môn):
- `curriculum.json` — khung ngành (nhóm, quota, track, nhánh tốt nghiệp).
- `courses.json` — 65 môn.
- `source_rows.json` — bản chép từng dòng từ PDF gốc.
- `vocabulary.json` — từ điển chủ đề (computer_vision, machine_learning…).
- `README.md` — hướng dẫn cách xây dữ liệu ngành mới (8 bước).
- Trạng thái: mẫu này dùng "envelope mới" (cấu trúc file kiểu mới) nên **các loader/seed hiện tại chưa đọc được** — việc tích hợp là nhiệm vụ riêng. Các ngành khác đã gỡ khỏi repo theo yêu cầu.

Các file `data/synthetic/profiles.json` (12 hồ sơ) và `data/curricula` đủ 4 ngành đã từng có, nhưng hiện đã gỡ. Database local đã seed từ trước vẫn giữ để chạy demo.

### 5.9. Thanh tra + tài liệu

**`tests/`** — 8 file thanh tra. Điểm đáng chú ý: `conftest.py` ép mọi test chạy offline (chặn mọi kết nối mạng thật; ai lỡ gọi mạng là test fail). Các test khác:
- `test_transcript.py`: chuẩn hóa mã, điểm, GPA, cô lập ngành.
- `test_rules.py`: tiên quyết AND/OR, track, nhóm, ngân sách.
- `test_recommendations.py`: hiểu câu, chấm điểm, lọc mã lạ, fallback.
- `test_advisor.py`: rào chắn chat, fallback, che mã ngoài catalog.
- `test_storage.py`, `test_database.py`, `test_curriculum_data.py`: kiểm tra kho + dữ liệu.

Lệnh chạy: `python -m pytest -q`.

**`docs/`** — Tài liệu chính thức:
- `SYSTEM_SPECIFICATION.md`: đặc tả pipeline chuẩn (đọc khi cần chi tiết gốc).
- `DATABASE_DESIGN.md`: thiết kế database.
- `COURSE_METADATA_SPECIFICATION.md`: hợp đồng metadata môn học.
- `CODEBASE_CHECKLIST.md`: checklist tiến độ hạ tầng.

**`modules/`** — 9 file đặc tả chia việc (01 catalog → 09 OCR bảng điểm). Đây là kế hoạch phân công, không phải mã chạy. Module 09 (nhập bảng điểm từ ảnh OCR) mới là kế hoạch, chưa có code.

**`KE_HOACH_DU_AN.md`, `SE_Project.pdf`** — Kế hoạch/bối cảnh lịch sử, để tham khảo.

**`README.md`** (gốc), **`AGENTS.md` + `.agent/AGENTS.md`** — Trạng thái dự án + luật cộng tác khi sửa code (commit kèm `Co-authored-by`, không commit bí mật, giữ Postgres mặc định…).

---

## Phần 6. Một túi câu hỏi nhanh

**Hỏi: Tôi đổi ngành giữa chừng thì sao?**
Đáp: `app.js` xóa môn đã tick + lịch sử chat ngay trên trình duyệt. Nếu bạn cố gửi mã môn ngành cũ lên, backend cũng từ chối vì mã không thuộc ngành đang chọn. Database cũng khóa bằng cặp `(revision_id + mã môn)`.

**Hỏi: AI (Gemini) có quyền gì?**
Đáp: 3 việc đúng theo thứ tự: (1) hiểu câu bạn muốn gì, (2) sắp xếp các môn đã đủ điều kiện, (3) viết lời giải thích. AI **không có quyền** mở khóa môn, không quyết định đủ/không đủ điều kiện.

**Hỏi: Nếu AI lỗi hoặc không có chìa khóa AI?**
Đáp: hệ thống tự chuyển sang cách "đếm từ khóa" (`preference.py` + `ranking.py`). Mọi thứ vẫn chạy, chỉ là câu chữ tự viết thay vì AI viết.

**Hỏi: Vì sao môn "Thị giác máy tính" của tôi bị chặn?**
Đáp: vì bạn chưa qua môn tiên quyết của nó (ví dụ "Học máy"). Nhìn vào `app/rules.py` → lý do bị chặn ghi rõ tên môn thiếu.

**Hỏi: Kết quả gợi ý có phải môn chắc chắn mở lớp kỳ này không?**
Đáp: Không. Hệ thống chỉ nói "môn này đủ điều kiện theo dữ liệu chương trình hiện có và phù hợp tương đối với mong muốn đã nhập." Trạng thái mở lớp luôn là "chưa xác minh".

**Hỏi: Tôi cần PDF và OCR để tạo khung chương trình à?**
Đáp: Cần PDF gốc để đối chiếu. Không cần OCR — người nhập chép tay vào `source_rows.json` rồi đối chiếu lại. OCR trong dự án là việc khác: nhập *bảng điểm của sinh viên* từ ảnh (module 09, mới là kế hoạch).

**Hỏi: Tại sao `services/` toàn file vài dòng vô nghĩa?**
Đáp: chúng là lớp đệm có chủ đích. `routes.py` chỉ gọi `services`, nên khi logic bên trong thay đổi thì API không phải sửa. Tuy nhỏ nhưng giữ cho 2 tầng độc lập nhau.

---

## Phần 7. Từ điển từ tiếng Anh hay gặp

Đọc theo thứ tự bạn gặp trong tài liệu. Nghĩa được viết kiểu đời thường:

| Từ | Nghĩa đời thường |
|---|---|
| **Catalog** | "Danh mục chương trình đào tạo": toàn bộ môn của 1 ngành |
| **Transcript** | "Bảng điểm": danh sách môn đã học + điểm |
| **Profile** | "Hồ sơ demo": 1 sinh viên giả lập |
| **Eligibility** | "Điều kiện được học" |
| **Eligible course** | Môn đủ điều kiện |
| **Blocked course** | Môn bị chặn (kèm lý do) |
| **Prerequisite** | "Môn tiên quyết": môn phải học trước. Ví dụ phải qua "Toán rời rạc" mới học "Thuật toán" |
| **AND / OR** | Kiểu điều kiện: AND = phải thỏa hết; OR = chỉ cần 1 |
| **Track** | "Hướng chuyên sâu" trong ngành |
| **Graduation path** | "Nhánh tốt nghiệp" |
| **Choice group** | "Nhóm tự chọn" + số tín chỉ cần học trong nhóm đó |
| **Credits (TC)** | "Tín chỉ" |
| **GPA** | Điểm trung bình tích lũy (thang 10 hoặc thang 4) |
| **Preference** | "Phiếu mong muốn" của bạn (học nhẹ, thích chủ đề gì…) |
| **Ranking** | "Xếp hạng" môn từ hợp nhất đến ít hợp nhất |
| **Score** | Điểm phù hợp từ 0 tới 1 |
| **Fallback** | "Phương án dự phòng" khi thứ chính lỗi |
| **Deterministic** | "Không ngẫu nhiên": cùng đầu vào luôn ra cùng kết quả |
| **Validation / Validate** | "Kiểm tra hợp lệ" |
| **Explanation** | "Lời giải thích" |
| **Grounded** | "Bám dữ liệu thật", không bịa |
| **LLM** | "Mô hình AI ngôn ngữ" (ở đây là Gemini) |
| **API key** | "Chìa khóa" để gọi AI — chỉ nằm ở backend |
| **Advisor** | "Cố vấn": nút chat nổi |
| **Guardrail** | "Rào chắn": từ chối câu hỏi ngoài phạm vi |
| **Heuristic** | "Cách tự viết sẵn" không cần AI |
| **What-if** | "Thử giả định": đổi mong muốn xem kết quả khác thế nào, không sửa hồ sơ thật |
| **Backend / Frontend** | "Bếp" (máy chủ Python) / "quầy khách" (trang web) |
| **Endpoint** | "Địa chỉ API" (ví dụ `POST /recommendations`) |
| **Request / Response** | Yêu cầu gửi lên / Kết quả trả về |
| **Schema / Model** | "Khuôn dữ liệu" — quy định dữ liệu có trường gì, kiểu gì |
| **Repository** | "Thủ kho" — lớp đọc/ghi dữ liệu |
| **PostgreSQL** | "Kho lạnh" — hệ quản trị cơ sở dữ liệu |
| **JSON** | "Sổ giấy có cấu trúc" — văn bản mà máy đọc được |
| **Migration** | "Xây/nâng cấp kho" theo phiên bản (Alembic) |
| **Docker Compose** | "Nút bật kho lạnh" bằng 1 lệnh |
| **Major isolation** | "Cô lập ngành": không trộn môn ngành này với ngành khác |
| **Foreign code** | "Mã môn lạ": không thuộc ngành đang chọn |
| **Offering status** | "Trạng thái mở lớp" — dự án luôn để "unknown" (chưa xác minh) |
| **Source status** | "Trạng thái nguồn": đã xác minh / còn nháp / xung đột |
| **Endpoint / Route** | Địa chỉ API (2 từ hay dùng thay nhau) |
| **Fixture** | "Dữ liệu mẫu cố định" dùng cho test |
| **Revision** | "Phiên bản" catalog (mỗi lần dữ liệu đổi thì tạo phiên bản mới) |
| **Idempotent** | "Chạy lại vô hại": chạy 2 lần không tạo rác |

---

## Phần 8. Chạy thử trong 6 lệnh

```bash
python -m venv .venv                                    # tạo môi trường riêng
python -m pip install -r requirements-dev.txt -c requirements-lock.txt
cp .env.example .env                                    # điền DATABASE_URL, GEMINI_API_KEY
docker compose up -d db                                 # bật kho lạnh
python -m alembic upgrade head                          # xây bảng trong kho
python -m uvicorn app.main:app --reload                 # bật máy chủ
```

Mở `http://127.0.0.1:8000` để dùng trang web, `http://127.0.0.1:8000/docs` để xem tài liệu API.

Kiểm tra sức khỏe: `/health` (máy còn sống?), `/ready` (kho sẵn sàng chưa?).

Chạy thanh tra: `python -m pytest -q` và `python -m ruff check app tests tools alembic`.

---

## Phần 9. Tình trạng hiện tại (quan trọng khi bạn sờ vào code)

- `data/` hiện chỉ còn **mẫu Data Science 2022 (65 môn)** theo cấu trúc mới. Mẫu này **chưa nối được** với loader/seed hiện tại (việc tích hợp còn nợ).
- Database local đã seed từ trước (4 ngành, 290 môn, 12 hồ sơ demo) vẫn giữ nguyên để chạy demo/seed lại không cần.
- Vì thiếu dữ liệu cũ, test mặc định chạy ra **22 đạt / 21 hỏng / 11 bỏ qua**. 21 test hỏng là do dữ liệu thay đổi, không phải do logic mới hỏng.
- 11 test PostgreSQL chỉ chạy khi bạn tự đặt biến `TEST_DATABASE_URL` (chúng tạo/xóa schema tạm riêng, không đụng dữ liệu thật).
- Việc còn nợ (xem `docs/CODEBASE_CHECKLIST.md`): tích hợp mẫu metadata mới, khôi phục 4 ngành, tách frontend, và phần chatbot hỏi đáp HUS (crawler + tìm kiếm tài liệu).
