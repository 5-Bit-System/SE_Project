# Giải thích dự án SE_Project (AI-07) — bản dễ hiểu

> Tài liệu này viết lại theo code hiện tại (ngày 20/10/2026), sau khi nhóm tái cấu trúc dự án.
> Mục tiêu: người đọc chưa rành tiếng Anh vẫn hiểu được hệ thống làm gì, các file liên kết ra sao, và mỗi file có nhiệm vụ gì.
>
> Cách đọc: đọc từ trên xuống. Gặp từ tiếng Anh trong ngoặc, cứ đọc phần giải thích tiếng Việt ngay cạnh. Không cần nhớ hết một lần.

**Mục lục**

- [0. Tóm tắt trong một câu](#0-tóm-tắt-trong-một-câu)
- [1. Câu chuyện: nhà máy nhỏ](#1-câu-chuyện-hãy-tưởng-tượng-đây-là-một-nhà-máy-nhỏ)
- [2. Làm được gì, không làm gì](#2-hệ-thống-làm-được-gì-và-không-làm-gì)
- [3. Bản đồ thư mục](#3-bản-đồ-thư-mục-nhìn-nhanh)
- [4. Bốn kho dữ liệu](#4-bốn-kho-dữ-liệu--đừng-nhầm-lẫn)
- [5. Các file liên kết với nhau](#5-các-file-liên-kết-với-nhau-như-thế-nào)
- [6. Mã giả cho từng file](#6-mã-giả-cho-từng-file)
- [7. Từ điển nhanh](#7-từ-điển-nhanh-chỉ-những-từ-hay-gặp)
- [8. Chạy dự án](#8-chạy-dự-án)
- [9. Sự thật hiện tại](#9-sự-thật-hiện-tại-để-không-bị-bất-ngờ)
- [10. Muốn sửa gì thì sửa ở đâu](#10-muốn-sửa-gì-thì-sửa-ở-đâu)
- [11. Đọc code trong 30 phút](#11-nếu-bạn-chỉ-có-30-phút-để-hiểu-code)
- [12. Hiểu nhầm dễ gặp](#12-những-hiểu-nhầm-rất-dễ-gặp)
- [13. Tóm tắt cuối](#13-tóm-tắt-cuối-cùng)


---

## 0. Tóm tắt trong một câu

Đây là một **website gợi ý môn học có giải thích**: sinh viên chọn ngành, nhập các môn đã học, hệ thống kiểm tra môn nào **đủ điều kiện**, rồi **xếp hạng** các môn phù hợp với mục tiêu và **viết lý do** vì sao nên học.

Nói cách khác:

```text
Catalog (danh mục môn của ngành)
        +
Bảng điểm (môn đã học)
        +
Mục tiêu (ví dụ: "muốn theo AI")
        ↓
   HỆ THỐNG
        ↓
Danh sách môn nên học + lý do + cảnh báo
```

---

## 1. Câu chuyện: hãy tưởng tượng đây là một nhà máy nhỏ

Nhà máy có 5 máy, xếp theo thứ tự:

```text
[Nguyên liệu]
 catalog + bảng điểm + mục tiêu
        │
        ▼
 (1) MÁY GÁC CỔNG  ──►  chỉ cho môn "đủ điều kiện" đi tiếp
        │                 (rules.py)
        ▼
 (2) MÁY PHIÊN DỊCH ──►  đổi câu nói thành "sở thích có cấu trúc"
        │                 (preference.py)
        ▼
 (3) MÁY XẾP HÀNG  ──►  chấm điểm và sắp thứ tự
        │                 (ranking.py + scoring.py)
        ▼
 (4) MÁY VIẾT NHÃN ──►  viết lý do "vì sao môn này phù hợp"
        │                 (explanation.py)
        ▼
 (5) NHÂN VIÊN TƯ VẤN ─► trả lời câu hỏi tự nhiên
                           (advisor_service.py)
```

Điều quan trọng nhất cần nhớ:

> **Máy gác cổng (eligibility) luôn chạy trước và luôn do code quyết định.**
> AI/LLM chỉ được **xếp hạng lại** hoặc **viết lời giải thích**, không được tự thêm môn không đủ điều kiện.

Vì sao phải như vậy? Vì LLM có thể "bịa" môn học. Nếu để LLM quyết định, sinh viên có thể nhận gợi ý sai. Nên hệ thống dùng một nguyên tắc:

```text
Code quyết định sự thật (đủ điều kiện hay không).
LLM chỉ được diễn đạt lại sự thật đó.
```

Đây gọi là **grounded** (có căn cứ): mọi câu trả lời phải bám vào dữ liệu thật.

---

## 2. Hệ thống làm được gì, và không làm gì

### Làm được

- Chọn 1 trong 4 ngành.
- Nhập môn đã học (chỉ cần mã môn, hoặc nhập điểm hệ 10).
- Tính tín chỉ tích lũy, GPA hệ 10, GPA hệ 4.
- Xem tiến độ theo khối kiến thức, nhóm tự chọn, track, nhánh tốt nghiệp.
- Kiểm tra môn nào đủ điều kiện, môn nào bị chặn và **vì sao** bị chặn.
- Gợi ý môn nên học, kèm điểm phù hợp và lý do.
- Chạy **what-if**: đổi trọng số xếp hạng để xem kết quả thay đổi thế nào, nhưng **không đổi** tập môn đủ điều kiện.
- Chat với trợ lý ảo. Trợ lý từ chối câu hỏi về thời khóa biểu và đánh giá giảng viên.

### Không làm được (hiện tại)

- Không đăng nhập, không đồng bộ cổng đào tạo thật.
- Không lưu bảng điểm lên server. Bảng điểm chỉ nằm trong trình duyệt của phiên đang mở.
- Không xác nhận môn có được mở trong học kỳ tới hay không. Trạng thái mở lớp luôn là `unknown` (chưa biết).
- Không xếp thời khóa biểu, không tránh trùng tiết.
- Không đánh giá giảng viên dễ/khó.
- Không đọc bảng điểm từ ảnh (OCR mới là kế hoạch, module 09).
- Không tự động chuyển sang JSON khi PostgreSQL lỗi. Phải chọn backend rõ ràng.

---

## 3. Bản đồ thư mục (nhìn nhanh)

```text
SE_Project/
├── app/                 ← Code chạy website (FastAPI + nghiệp vụ)
│   ├── main.py          ← Cửa khởi động
│   ├── config.py        ← Đọc cấu hình từ .env
│   ├── api/routes.py    ← Danh sách đường dẫn API
│   ├── models.py        ← Khuôn dữ liệu chính
│   ├── schemas/         ← Khuôn dữ liệu cho API
│   ├── recommendation/  ← Xếp hạng, chấm điểm, giải thích
│   ├── services/        ← Ghép các bước thành pipeline
│   ├── infrastructure/  ← Đọc catalog từ JSON/PostgreSQL
│   ├── db/              ← Bảng của database legacy
│   └── static/          ← Giao diện HTML/CSS/JS
│
├── database/            ← Database HUS (PostgreSQL ai07)
│   ├── hus_db/          ← Đọc/ghi/kiểm tra database HUS
│   ├── tools/           ← Lệnh migrate, publish, verify
│   ├── hus_alembic/     ← Lịch sử migration riêng của HUS
│   ├── sql/             ← DDL gốc 11 bảng + 2 view
│   └── data/hus_source.json ← Nguồn catalog HUS
│
├── tools/               ← Công cụ build catalog và seed legacy
├── data/                ← Mẫu metadata (không phải runtime)
├── tests/               ← Test chia theo chức năng
├── docs/                ← Đặc tả, ADR, báo cáo
├── modules/             ← Đặc tả chia module (01–09)
├── alembic/             ← Migration của database legacy (để rollback)
├── .agent/              ← Ghi nhớ dự án cho agent
├── README.md            ← Hướng dẫn chạy
└── GIAI_THICH_PROJECT.md ← Bạn đang đọc file này
```

Giải thích nhanh vài từ:

- **Catalog**: danh mục môn học của một ngành. Giống "thực đơn" của ngành đó.
- **Runtime**: phần đang chạy thật khi mở website.
- **Legacy**: phần cũ, giữ lại để quay về nếu cần (rollback).
- **Migration**: kịch bản thay đổi cấu trúc database.
- **Seed**: nạp dữ liệu ban đầu vào database.
- **Schema**: bản thiết kế các bảng/cột trong database.

---

## 4. Bốn kho dữ liệu — đừng nhầm lẫn

Dự án này rất dễ nhầm vì có nhiều nơi chứa dữ liệu. Nhớ 4 kho sau:

### Kho 1: `database/data/hus_source.json`

Đây là **nguồn** catalog HUS đã được nhập tay từ PDF.

- Chứa 4 ngành, 179 môn, 290 quan hệ ngành–môn, 348 quan hệ tiên quyết.
- Là file JSON nằm trong Git.
- **Không phải** database đang chạy. Nó giống "bản nháp nguồn".

### Kho 2: PostgreSQL `ai07` (container `se_hus_db`)

Đây là **database thật đang chạy**.

- Chứa bảng nguồn (`courses`, `curricula`, ...).
- Chứa bảng `hus_catalog_revisions`: mỗi dòng là một **catalog đã đóng gói** dưới dạng JSONB.
- Runtime đọc từ đây.

### Kho 3: `data/curricula/`

Đây chỉ là **một mẫu** của ngành Khoa học dữ liệu.

- Dùng để minh họa cấu trúc metadata.
- **Không đủ** 4 ngành, nên không dùng để chạy JSON backend thật.
- Nếu chọn `STORAGE_BACKEND=json`, ứng dụng sẽ báo lỗi vì thiếu catalog.

### Kho 4: `data/synthetic/profiles.json`

Đây là nơi code **mong đợi** hồ sơ demo.

- Hiện file này **không tồn tại** trong repo.
- Vì vậy API profile khi chạy HUS trả danh sách rỗng; khi chạy JSON sẽ báo lỗi thiếu file.
- Đây là hiện trạng, không phải lỗi bạn gây ra.

### Bảng so sánh cực ngắn

| Kho | Vai trò | Có dùng khi chạy HUS? |
|---|---|---|
| `database/data/hus_source.json` | Nguồn để publish | Chỉ khi publish |
| PostgreSQL `ai07` | Runtime chính | Có |
| `data/curricula/` | Mẫu metadata | Không |
| `data/synthetic/profiles.json` | Hồ sơ demo | Không (đang thiếu) |

---

## 5. Các file liên kết với nhau như thế nào

Phần này là "bản đồ ai gọi ai". Có 6 chuyến đi thường gặp.

### Chuyến 1: Mở trang web

```text
Trình duyệt
   │  GET /
   ▼
app/main.py
   │  trả file
   ▼
app/static/index.html
   │  nạp
   ▼
app/static/app.js  +  app/static/styles.css
```

Khi khởi động, `app/main.py` còn gọi `check_storage_ready()`:

```text
check_storage_ready()
   │
   ├─ nếu STORAGE_BACKEND = postgres
   │     └─ infrastructure/repositories.py
   │           └─ HusRepository.ready()  (hoặc PostgresRepository nếu legacy)
   │
   └─ nếu STORAGE_BACKEND = json
         └─ catalog.list_catalogs()
               └─ phải đủ 4 catalog, nếu không báo lỗi
```

### Chuyến 2: Xem danh sách ngành và môn

```text
app.js
  │  GET /programs
  ▼
app/api/routes.py :: programs()
  │
  ▼
app/catalog.py :: list_catalogs()
  │
  ├─ STORAGE_BACKEND=json
  │     └─ infrastructure/json_catalog_repository.py
  │           └─ catalog_normalization.py
  │                 └─ catalog_validation.py
  │
  └─ STORAGE_BACKEND=postgres
        └─ infrastructure/repositories.py
              ├─ DATABASE_MODEL=hus    → hus_repository.py
              └─ DATABASE_MODEL=legacy → postgres_repository.py
```

`GET /courses?program_id=...` đi gần như y hệt, nhưng chỉ lấy một catalog.

### Chuyến 3: Nhập bảng điểm → xem GPA và tiến độ

```text
app.js (giữ bảng điểm trong biến state)
  │  POST /transcript/summary
  ▼
app/api/routes.py :: transcript_summary()
  │
  ├─ app/catalog.py :: load_catalog()
  ├─ app/transcript.py :: StudentTranscript
  │     ├─ validate_major_isolation()
  │     ├─ calculate_earned_credits()
  │     ├─ calculate_gpa()
  │     └─ calculate_gpa_10()
  └─ app/progress.py :: calculate_progress()
        └─ app/rules.py ::_prepare_selection_context()
```

Điểm quan trọng: `validate_major_isolation()` kiểm tra bảng điểm có môn "lạ" ngoài ngành hay không. Nếu có, nó báo `foreign_courses`.

### Chuyến 4: Kiểm tra điều kiện

```text
app.js
  │  POST /eligibility
  ▼
app/api/routes.py :: check_eligibility()
  │
  ├─ app/catalog.py :: load_catalog()
  └─ app/rules.py :: evaluate_eligibility()
        │
        ├─ kiểm tra mã môn lạ
        ├─ kiểm tra track / nhánh tốt nghiệp
        ├─ xét tiên quyết
        ├─ xét nhóm tự chọn đã đủ tín chỉ chưa
        └─ xét ngân sách tín chỉ
```

Kết quả gồm 2 danh sách:

- `eligible_courses`: môn được phép học tiếp.
- `blocked_courses`: môn bị chặn, kèm lý do.

### Chuyến 5: Gợi ý môn học

Đây là chuyến quan trọng nhất.

```text
app.js
  │  POST /recommendations
  ▼
app/api/routes.py :: recommendations()
  │
  ├─ app/catalog.py :: load_catalog()
  ├─ app/recommendation/llm.py :: configured_adapters()
  │     └─ chỉ trả LLM nếu có API key và LLM đang bật
  │
  └─ app/services/recommendation_service.py :: recommend()
        │
        ├─ 1. kiểm tra program_id
        ├─ 2. kiểm tra mã môn lạ
        ├─ 3. app/rules.py :: evaluate_eligibility()   ← luôn chạy
        ├─ 4. app/recommendation/preference.py         ← hiểu mục tiêu
        ├─ 5. app/recommendation/ranking.py            ← xếp hạng
        ├─ 6. app/recommendation/validation.py         ← lọc mã bịa
        ├─ 7. app/recommendation/scoring.py            ← chấm điểm
        ├─ 8. app/recommendation/explanation.py        ← viết lý do
        └─ 9. trả RecommendationResponse
```

Nếu LLM lỗi ở bất kỳ bước nào, hệ thống **không sập**. Nó tự quay về xếp hạng từ khóa (deterministic).

### Chuyến 6: Hỏi trợ lý ảo

```text
app.js
  │  POST /advisor/chat
  ▼
app/api/routes.py :: advisor_chat_endpoint()
  │
  ├─ app/catalog.py :: load_catalog()
  └─ app/services/advisor_service.py :: chat_advisor()
        │
        ├─ 1. check_scope_guardrails()   ← chặn câu hỏi ngoài phạm vi
        ├─ 2. evaluate_eligibility()      ← luôn chạy
        ├─ 3. _extract_session_preference()
        ├─ 4. _build_recommendation_facts()
        ├─ 5. nếu có API key:
        │       ├─ build_advisor_prompt()
        │       ├─ call_gemini_api()
        │       ├─ _has_unsafe_catalog_recommendation()
        │       ├─ _validate_llm_suggestions()
        │       └─ _redact_unknown_course_codes()
        └─ 6. nếu không có key hoặc lỗi:
                └─ heuristic_advisor()
```

### Chuyến 7 (phụ): Nạp catalog từ nguồn vào database

Đây là chuyến của người quản trị, không phải của sinh viên.

```text
database/data/hus_source.json
        │
        ▼
database/hus_db/catalog_builder.py :: build_catalogs()
        │  (đọc bảng nguồn, kiểm tra, đóng gói thành 4 Catalog)
        ▼
database/hus_db/catalog_builder.py → app/catalog_validation.py
        │  (kiểm tra lần cuối)
        ▼
database/tools/publish_catalogs.py :: publish_catalogs()
        │  (một transaction: ghi bảng nguồn + ghi hus_catalog_revisions)
        ▼
PostgreSQL ai07
        │
        ▼
app/infrastructure/hus_repository.py (đọc revision đang active)
```

Điểm cần nhớ:

- Publishing là **một transaction**. Hoặc cả 4 catalog được cập nhật, hoặc không cái nào.
- Revision được đặt tên bằng **hash nội dung**. Nội dung không đổi thì dùng lại revision cũ.
- Runtime kiểm tra hash và `program_id` để phát hiện dữ liệu bị sửa tay.

---

