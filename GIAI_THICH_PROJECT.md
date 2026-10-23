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

## 6. Mã giả cho từng file

Phần này đi từng file. Mỗi file có:

- **Vai trò**: một hai câu.
- **Mã giả**: các bước chính, viết bằng tiếng Việt.

Các file quá nhỏ hoặc chỉ để "nối dây" (`__init__.py`) được gộp lại ở cuối.

---

## 6A. Khởi động và cấu hình

### `app/main.py` — cửa khởi động

**Vai trò:** tạo ứng dụng FastAPI, gắn giao diện tĩnh, mở các cổng kiểm tra sức khỏe.

```text
tạo app FastAPI
gắn thư mục /static
gắn router API

khi app bắt đầu chạy:
  gọi check_storage_ready()

hàm check_storage_ready():
  nếu backend là postgres:
    mở repository tương ứng
    gọi ready()
  nếu backend là json:
    lấy danh sách catalog
    nếu không đủ 4 catalog:
      báo lỗi "Chưa có đủ bốn catalog"

GET /            → trả index.html
GET /favicon.ico → trả rỗng (204)
GET /health      → trả {"status": "ok"}
GET /ready       → kiểm tra storage rồi trả ok

nếu storage không kết nối được → HTTP 503
nếu dữ liệu storage sai      → HTTP 500
```

### `app/config.py` — đọc cấu hình

**Vai trò:** đọc file `.env` và biến môi trường, kiểm tra hợp lệ, trả về một object `Settings`.

```text
đọc file .env ở thư mục gốc (không ghi đè biến đã có)

backend = STORAGE_BACKEND, mặc định "postgres"
  chỉ nhận "postgres" hoặc "json"

model = DATABASE_MODEL, mặc định "hus"
  chỉ nhận "hus" hoặc "legacy"

nếu backend là postgres:
  DATABASE_URL phải là URL PostgreSQL hợp lệ và có tên database

đọc thêm:
  GEMINI_API_KEY
  GEMINI_BASE_URL
  GEMINI_MODEL, mặc định "gemini-3.8-flash"
  RECOMMENDATION_LLM_ENABLED, mặc định bật

lưu kết quả vào cache để không đọc lại nhiều lần
```

### `app/errors.py` — lỗi dùng chung

**Vai trò:** định nghĩa 3 loại lỗi để phân biệt "không tìm thấy", "không kết nối được", "dữ liệu sai".

```text
CatalogError       = lỗi không tìm thấy catalog (là con của ValueError)
StorageUnavailable = lỗi không kết nối được storage (RuntimeError)
StorageDataError   = lỗi dữ liệu lưu trữ không hợp lệ (RuntimeError)
```

---

## 6B. API và khuôn dữ liệu

### `app/api/routes.py` — danh sách API

**Vai trò:** nhận request từ trình duyệt, gọi nghiệp vụ, đổi lỗi thành mã HTTP đúng.

```text
hàm phụ _catalog_metadata(catalog):
  trả thông tin ngành + số môn

hàm phụ _raise_domain_error(lỗi):
  nếu là CatalogError → HTTP 404
  còn lại            → HTTP 422

GET /programs:
  trả metadata của tất cả catalog

GET /courses?program_id=...:
  load catalog rồi trả danh sách môn

GET /profiles?program_id=...:
  load danh sách profile demo
  kèm metadata catalog

GET /profiles/{profile_id}:
  load 1 profile
  kèm metadata catalog

GET /profiles/{profile_id}/transcript/summary:
  load profile → đổi thành transcript
  tính isolation, tín chỉ, tiến độ, GPA
  trả tổng hợp

POST /recommendations:
  load catalog
  lấy adapter LLM nếu có
  gọi recommend()
  kiểm tra lại response bằng model
  trả kết quả

POST /recommendations/what-if:
  load catalog
  tính eligibility một lần
  gọi recommend() với eligibility đó và what_if = true
  trả kết quả

POST /transcript/summary:
  nhận transcript từ client
  load catalog
  tính isolation, tín chỉ, tiến độ, GPA
  trả tổng hợp

POST /eligibility:
  load catalog
  gọi evaluate_eligibility()
  trả kết quả

POST /advisor/chat:
  load catalog
  gọi chat_advisor()
  trả kết quả
```

### `app/schemas/__init__.py` — nạp schema kiểu "lazy"

**Vai trò:** cho phép `from app.schemas import ProfileSummary` mà không tạo vòng lặp import.

```text
khi có người xin ProgramCatalogMetadata:
  mới import từ schemas.catalog

khi có người xin ProfileDetail / ProfileSummary / TranscriptSummary:
  mới import từ schemas.profile
```

### `app/schemas/catalog.py`

**Vai trò:** khuôn trả về thông tin ngành, có thêm số môn.

```text
ProgramCatalogMetadata = Program + course_count
```

### `app/schemas/eligibility.py`

**Vai trò:** gom các khuôn liên quan điều kiện học.

```text
xuất lại:
  BlockedCourse
  BlockedReason
  EligibilityRequest
  EligibilityResult
```

### `app/schemas/profile.py`

**Vai trò:** khuôn cho danh sách profile, chi tiết profile, và bản tóm tắt bảng điểm.

```text
ProfileSummary:
  thông tin nhẹ để hiển thị danh sách
  kèm metadata catalog

ProfileDetail:
  toàn bộ profile demo
  kèm metadata catalog

TranscriptSummary:
  mã ngành, tên ngành
  tín chỉ tích lũy
  tiến độ
  GPA hệ 10, GPA hệ 4
  môn đã đạt, môn chưa đạt
  kết quả kiểm tra isolation
  metadata catalog
```

### `app/schemas/recommendation.py`

**Vai trò:** gom khuôn cho request/response gợi ý.

```text
xuất lại:
  RecommendationRequest
  RecommendationResponse
  RecommendedCourse
  RankingWeights
  StructuredPreference
  WhatIfRequest
```

### `app/schemas/advisor.py`

**Vai trò:** khuôn cho chat.

```text
AdvisorMessage:
  role (user / assistant / system)
  content

AdvisorRequest:
  program_id
  message (tối đa 1000 ký tự)
  passed_course_codes
  history
  selected_track_id
  selected_graduation_path_id

AdvisorResponse:
  reply
  mode: gemini_llm | heuristic_fallback | guardrail_rejected
  is_guardrail_triggered
  guardrail_reason
  suggested_courses
```

### `app/schemas/metadata.py`

**Vai trò:** khuôn chặt cho metadata môn học (nguồn, bằng chứng, phiên bản).

```text
FieldEvidenceItem:
  nguồn, vị trí, cách nhập, trạng thái, ghi chú

Hours:
  số giờ lý thuyết / thực hành / tự học

CourseMetadata:
  kiểm tra các trường metadata
  bắt buộc có bằng chứng cho trường quan trọng

CourseEnvelope:
  gói tất cả môn + phiên bản schema + phiên bản từ vựng
  kiểm tra không trùng mã môn
```

---

## 6C. Mô hình dữ liệu và catalog

### `app/models.py` — khuôn dữ liệu gốc

**Vai trò:** định nghĩa các object mà toàn bộ hệ thống dùng chung.

```text
ChoiceGroup:
  một nhóm môn tự chọn + số tín chỉ cần

Track:
  một hướng chuyên ngành + các nhóm môn của nó

GraduationPath:
  một nhánh tốt nghiệp + môn + track được phép

Program:
  thông tin ngành
  tổng tín chỉ
  trạng thái catalog (draft_unverified / verified)
  nhóm tự chọn, track, nhánh tốt nghiệp
  nguồn tài liệu

Course:
  mã, tên, số tín chỉ, khối kiến thức
  tiên quyết: danh sách AND của các nhóm OR
  trạng thái tiên quyết
  nhóm tự chọn, nhánh tốt nghiệp
  metadata: chủ đề, hướng, độ khó, workload
  bằng chứng nguồn

Catalog:
  program + danh sách courses + phiên bản metadata

StructuredPreference:
  sở thích đã chuẩn hóa
  workload, difficulty, orientation
  chủ đề quan tâm, nghề nghiệp mong muốn
  số tín chỉ / số môn mong muốn
  loại môn, mức chấp nhận tiên quyết

RankingWeights:
  trọng số cho chủ đề, từ khóa, loại môn, hướng, độ khó, workload
  tổng trọng số phải lớn hơn 0

RecommendationRequest:
  ngành, môn đã học, mục tiêu
  ngân sách tín chỉ (mặc định 18)
  số môn tối đa (mặc định 5)
  track, nhánh tốt nghiệp
  preference và trọng số (có thể gửi sẵn)

WhatIfRequest:
  giống RecommendationRequest
  nhưng bắt buộc có ranking_weights

RecommendedCourse:
  mã, tên, tín chỉ
  lý do, thứ hạng, điểm
  lý do đủ điều kiện, lý do phù hợp
  trạng thái nguồn, trạng thái mở lớp

RecommendationResponse:
  danh sách gợi ý
  số môn đủ điều kiện
  cảnh báo
  preference đã dùng
  backend xếp hạng
  thống kê môn bị chặn
  trọng số đã dùng

BlockedReason:
  loại lý do + câu giải thích + tiên quyết còn thiếu

BlockedCourse:
  môn bị chặn + danh sách lý do

EligibilityResult:
  môn đủ điều kiện
  môn bị chặn
  môn đã học
  các con số tổng
  lý do đủ điều kiện

EligibilityRequest:
  ngành, môn đã học, ngân sách tín chỉ, track, nhánh
```

### `app/catalog.py` — cửa vào catalog

**Vai trò:** che giấu chuyện "catalog đang đọc từ JSON hay PostgreSQL". Nơi khác chỉ cần gọi 2 hàm này.

```text
load_catalog(program_id, root=None):
  nếu có root hoặc backend là json:
    đọc từ json_catalog_repository
  ngược lại:
    lấy repository postgres (hus hoặc legacy)
    gọi load_catalog()

list_catalogs(root=None):
  nếu có root hoặc backend là json:
    đọc từ json_catalog_repository
  ngược lại:
    lấy repository postgres
    gọi list_catalogs()
```

### `app/catalog_normalization.py` — chuẩn hóa nguồn

**Vai trò:** biến dữ liệu thô (envelope mới hoặc danh sách cũ) thành object `Catalog` thống nhất.

```text
nếu courses là object (envelope mới):
  kiểm tra phiên bản metadata và từ vựng
  kiểm tra program_id / revision khớp với curriculum
  tạo Catalog từ Program + danh sách Course
nếu courses là list (định dạng cũ):
  đổi vài trạng thái tiên quyết cho tương thích
  tạo Catalog
nếu kiểu khác:
  báo lỗi

gọi validate_catalog()
nếu có lỗi → đổi thành StorageDataError
```

### `app/catalog_validation.py` — kiểm tra catalog

**Vai trò:** "người kiểm hàng" trước khi catalog được dùng. Đây là nơi bắt dữ liệu sai.

```text
validate_curriculum_selections(program, mã môn):
  kiểm tra nhóm tự chọn không trùng
  kiểm tra track không trùng
  kiểm tra track chỉ trỏ tới nhóm có thật
  kiểm tra nhánh tốt nghiệp chỉ trỏ tới môn/track có thật

validate_catalog(catalog, vocabulary):
  kiểm tra là object Catalog
  nếu là metadata chặt:
    kiểm tra phiên bản 1.0
    kiểm tra có vocabulary khớp

  kiểm tra mã môn không trùng
  kiểm tra cấu trúc nhóm/track/nhánh

  với từng nhóm:
    nếu nhóm khai báo danh sách môn:
      danh sách đó phải khớp thành viên thật

  với từng môn:
    nhóm tự chọn phải tồn tại
    nhánh tốt nghiệp phải tồn tại
    mỗi nhóm OR không được rỗng, không trùng mã, không tự trỏ mình
    mã ngoài catalog phải được đánh dấu external đúng
    metadata phải hợp lệ
    chủ đề / nghề nghiệp phải nằm trong vocabulary

  kiểm tra vòng lặp tiên quyết bằng DFS
    nếu A cần B, B cần A → báo lỗi
```

### `app/catalog_contracts.py` — danh tính và hash

**Vai trò:** giữ danh sách 4 ngành cố định và tính hash để phát hiện catalog bị sửa.

```text
MAJOR_PROGRAM_IDS:
  "7460101"  → toan_hoc_7460101_2022
  "7460117"  → toan_tin_7460117_2022
  "7460108"  → khdl_7460108_2022
  "7480113QTD" → khmtt_7480113qtd_2022

canonical_json(value):
  đổi object thành JSON có thứ tự khóa cố định
  (để hash luôn giống nhau)

digest(value):
  hash SHA-256 của canonical_json

catalog_payload(catalog):
  đổi catalog thành dict JSON

catalog_revision(catalog, source_digest):
  hash của (nội dung catalog + hash nguồn)
```

### `app/infrastructure/repositories.py` — chọn repository

**Vai trò:** một công tắc nhỏ: dùng HUS hay legacy.

```text
postgres_repository():
  nếu DATABASE_MODEL = legacy:
    trả PostgresRepository
  ngược lại:
    trả HusRepository
```

### `app/infrastructure/hus_repository.py` — đọc HUS runtime

**Vai trò:** đọc catalog đã đóng gói trong `hus_catalog_revisions`.

```text
HEAD = "hus_20261017_02"   ← phiên bản migration mong đợi

connection():
  mở connection với isolation REPEATABLE READ
  nếu lỗi SQL → StorageUnavailable
  nếu dữ liệu sai → StorageDataError

_validated(row, identity):
  lấy payload JSON
  đổi thành Catalog
  kiểm tra program_id khớp
  kiểm tra curriculum_id khớp
  kiểm tra revision_id đúng bằng hash nội dung
  kiểm tra phiên bản metadata là 1.0
  gọi validate_catalog()
  trả catalog

_load_catalog(conn, program_id):
  tìm revision đang active của ngành
  join với bảng curricula
  nếu không có → CatalogError
  kiểm tra major_code khớp
  trả catalog đã validate

load_catalog(program_id):
  mở connection rồi gọi _load_catalog

list_catalogs():
  lấy tất cả program_id đang active
  load từng catalog

read_profiles():
  trả [] vì demo không đọc dữ liệu sinh viên thật

ready():
  kiểm tra version migration = HEAD
  kiểm tra đúng 4 catalog active
  load thử từng catalog
```

### `app/infrastructure/postgres_repository.py` — đọc legacy

**Vai trò:** đọc database cũ, nơi catalog được tách thành nhiều bảng quan hệ.

```text
connection():
  mở connection REPEATABLE READ
  đổi lỗi SQL thành StorageUnavailable

ready():
  chạy SELECT 1
  đếm catalog active
  phải đúng 4

_load_catalog(conn, program_id):
  tìm revision active
  đọc courses theo thứ tự
  đọc prerequisite_groups + prerequisite_options
    ghép lại thành danh sách AND của OR
  đọc choice_group_courses
    ghép lại thành nhóm tự chọn của từng môn
  lấy payload chương trình
  nếu có metadata contract:
    chuẩn hóa theo envelope mới
  nếu không:
    chuẩn hóa kiểu cũ
  kiểm tra program_id khớp revision
  validate_catalog()
  trả catalog

load_catalog / list_catalogs:
  giống HUS nhưng dùng bảng legacy

read_profiles():
  đọc demo_profiles + transcript_records
  trả list dict
```

### `app/infrastructure/json_catalog_repository.py` — đọc JSON

**Vai trò:** đọc catalog từ thư mục `data/curricula/`.

```text
list_catalogs(root):
  lấy tên các thư mục con
  load từng thư mục

load_catalog(program_id, root):
  đổi alias ngành thành ID đầy đủ
  kiểm tra thư mục có tồn tại
  đọc curriculum.json
  đọc courses.json
  đọc vocabulary.json nếu có
  gọi normalize_catalog()
  kiểm tra lựa chọn nhóm/track/nhánh
  kiểm tra program_id khớp tên thư mục
  kiểm tra mã môn không trùng
  kiểm tra nhóm tự chọn có thật
  trả catalog
```

### `app/db/session.py` — tạo engine SQLAlchemy

**Vai trò:** tạo "đường ống" kết nối PostgreSQL và giữ lại để tái sử dụng.

```text
engine_for_url(url):
  tạo engine
  bật pool_pre_ping (tự kiểm tra kết nối cũ)
  pool_size = 5, max_overflow = 5
  ẩn tham số trong log
  connect_timeout = 5 giây
  cache theo URL

get_engine():
  lấy DATABASE_URL từ Settings
  gọi engine_for_url()
```

### `app/db/schema.py` — bảng của legacy

**Vai trò:** định nghĩa các bảng quan hệ cho database cũ và cho seed.

```text
các bảng chính:
  programs
  catalog_revisions      ← mỗi lần seed là một revision
  courses
  course_sources
  choice_groups
  choice_group_courses
  prerequisite_groups
  prerequisite_options
  tracks
  track_choice_groups
  graduation_paths
  graduation_path_courses
  graduation_path_tracks
  demo_profiles
  transcript_records

quy tắc:
  khóa chính thường gồm revision_id + mã
  khóa ngoại ghép bảo đảm dữ liệu không lẫn giữa các revision
  mỗi ngành chỉ có tối đa 1 revision active (unique index có điều kiện)
  điểm phải từ 0 đến 10
  term phải từ 1 đến 12
  passed phải khớp với grade >= 5
```

---

## 6D. Nghiệp vụ học vụ

### `app/transcript.py` — bảng điểm

**Vai trò:** nhận bảng điểm, chuẩn hóa mã môn, tính GPA, kiểm tra môn ngoài ngành.

```text
PROGRAM_ALIASES:
  khdl / khmtt / toan_hoc / toan_tin → ID đầy đủ

grade_to_gpa4(grade):
  >= 9.0 → 4.0
  >= 8.5 → 3.7
  >= 8.0 → 3.5
  >= 7.0 → 3.0
  >= 6.5 → 2.5
  >= 5.5 → 2.0
  >= 5.0 → 1.5
  >= 4.0 → 1.0
  còn lại → 0.0

resolve_program_id(identifier):
  đổi alias thành ID đầy đủ
  nếu không phải alias thì giữ nguyên

TranscriptRecord:
  mã môn (viết hoa, bỏ khoảng trắng)
  điểm 0..10 (có thể rỗng)
  term 1..12 (có thể rỗng)
  passed (mặc định true)
  nếu có điểm thì passed = điểm >= 5.0

StudentTranscript:
  program_id (chuẩn hóa)
  selected_track_id
  selected_graduation_path_id
  records
  không cho trùng mã môn (vì không hỗ trợ học lại)

  passed_course_codes  = các môn passed
  failed_course_codes  = các môn chưa passed
  all_course_codes     = tất cả môn
  grade_map            = mã môn → điểm

  validate_major_isolation(catalog):
    nếu program_id khác catalog:
      coi tất cả môn là môn ngoài ngành
    nếu khớp:
      tách môn hợp lệ và môn ngoài ngành

  calculate_earned_credits(catalog):
    cộng tín chỉ các môn passed
    bỏ qua môn không tính vào tổng

  calculate_gpa_10(catalog):
    trung bình có trọng số tín chỉ, thang 10

  calculate_gpa(catalog):
    đổi từng điểm sang hệ 4
    rồi trung bình có trọng số tín chỉ
```

### `app/profiles.py` — hồ sơ demo

**Vai trò:** đọc và kiểm tra hồ sơ mẫu. Đây là dữ liệu để demo, không phải sinh viên thật.

```text
PROFILES_PATH = data/synthetic/profiles.json

DemoProfile:
  profile_id, program_id, label
  current_term
  target_track
  career_goal
  preferences
  records

  to_transcript():
    đổi thành StudentTranscript

_read_profiles(path):
  nếu đang dùng postgres và không truyền path:
    đọc từ repository
  ngược lại đọc file JSON
  kiểm tra file tồn tại
  kiểm tra là danh sách
  kiểm tra từng profile hợp lệ
  kiểm tra profile_id không trùng

validate_profile(profile, catalog):
  load catalog nếu chưa có
  kiểm tra program_id khớp
  kiểm tra không có môn ngoài ngành
  kiểm tra không trùng môn
  kiểm tra mọi môn thuộc catalog
  kiểm tra mọi record có term
  kiểm tra term không vượt current_term
  kiểm tra target_track có thật
  kiểm tra tiên quyết:
    môn tiên quyết phải được học ở term nhỏ hơn

validate_demo_profiles():
  đọc tất cả profile
  validate từng cái
  yêu cầu đủ 4 ngành
  yêu cầu đúng 3 profile mỗi ngành
  yêu cầu tổng 12 profile

list_profiles(program_id):
  đọc tất cả
  lọc theo ngành nếu có
  validate từng cái

load_profile(profile_id):
  tìm theo ID
  nếu không có → ProfileError
  validate rồi trả về
```

### `app/progress.py` — tiến độ chương trình

**Vai trò:** tính "đã học được bao nhiêu tín chỉ" theo từng khối, nhóm, track, nhánh.

```text
counts_toward_total(catalog, course):
  trả false nếu môn nằm trong danh sách loại trừ
  trả false nếu counted_in_total = false
  ngược lại trả true

calculate_progress(catalog, passed_codes, track_id, path_id):
  kiểm tra mã môn hợp lệ
  kiểm tra track/nhánh hợp lệ
  lọc các môn passed có tính vào tổng

  hàm con item(id, tên, tập mã, tín chỉ yêu cầu):
    tính tín chỉ đã học trong tập mã
    tính tín chỉ còn thiếu

  tính tiến độ từng khối kiến thức
  tính tiến độ từng nhóm tự chọn
  nếu có track: tính tiến độ track
  nếu có nhánh: tính tiến độ nhánh
  tính tổng toàn chương trình

  thêm cảnh báo:
    tiến độ chỉ để tham khảo
    catalog chưa xác minh
    chưa chọn track / nhánh

  trả CurriculumProgress
```

### `app/rules.py` — máy gác cổng (quan trọng nhất)

**Vai trò:** quyết định môn nào được vào danh sách gợi ý. Đây là nơi duy nhất có quyền quyết định này.

```text
_prepare_selection_context(catalog, track_id, path_id):
  lấy danh sách track
  nếu track_id không tồn tại → lỗi invalid_track_id
  lấy danh sách nhánh tốt nghiệp
  nếu path_id không tồn tại → lỗi invalid_graduation_path_id
  nếu chọn cả hai mà track không thuộc nhánh:
    → lỗi incompatible_track_graduation_path
  trả về dữ liệu tra cứu

_validate_passed_codes(passed, known):
  nếu có mã không thuộc catalog
    → lỗi unknown_passed_course_codes
  trả về set mã đã học

_validate_max_credits(max_credits):
  nếu <= 0 → lỗi invalid_max_credits

evaluate_eligibility(catalog, passed, max_credits, track_id, path_id):
  kiểm tra max_credits
  tạo map nhóm, map môn
  kiểm tra mã môn đã học
  chuẩn bị track/nhánh

  tính tín chỉ đã dùng cho từng nhóm tự chọn

  với từng môn trong catalog:
    nếu đã học:
      đưa vào completed
      bỏ qua

    tạo danh sách lý do chặn

    nếu trạng thái tiên quyết là xung đột nguồn:
      chặn với lý do source_conflict
    nếu trạng thái là unknown:
      chặn với lý do prerequisite_unknown

    với từng nhóm AND của tiên quyết:
      nếu không có bất kỳ môn nào trong nhóm OR đã học:
        ghi nhận nhóm còn thiếu
    nếu có nhóm thiếu:
      chặn với lý do missing_prerequisites

    nếu có chọn track:
      nếu môn thuộc track khác và không thuộc track đã chọn:
        chặn với lý do track_mismatch

    nếu có chọn nhánh tốt nghiệp:
      nếu môn thuộc nhánh khác:
        chặn với lý do graduation_path_mismatch

    nếu môn thuộc nhóm tự chọn và mọi nhóm liên quan đã đủ tín chỉ:
      chặn với lý do choice_group_full

    nếu số tín chỉ của môn vượt ngân sách:
      chặn với lý do credits_exceeded

    nếu không có lý do nào:
      cho vào eligible
      ghi lý do đủ điều kiện

  trả EligibilityResult gồm:
    môn đủ điều kiện
    môn bị chặn
    môn đã học
    các tổng số

eligible_courses(...):
  hàm tương thích cũ
  chỉ trả danh sách môn đủ điều kiện
```

Ghi nhớ về tiên quyết:

```text
prerequisites = [ ["A"], ["B", "C"] ]
nghĩa là: phải có A, VÀ phải có (B hoặc C).
```

---

## 6E. Pipeline gợi ý

### `app/services/recommendation_service.py` — ghép các bước

**Vai trò:** nhạc trưởng của pipeline gợi ý. Gọi đúng thứ tự, xử lý fallback.

```text
recommend(catalog, request, ranker, preference_extractor, llm_ranker,
          eligibility, what_if):
  nếu program_id không khớp catalog → lỗi

  lấy tập mã môn của catalog
  nếu passed có mã lạ → lỗi

  nếu chưa có eligibility:
    gọi evaluate_eligibility()

  candidates = eligibility.eligible_courses
  by_code = map mã → môn
  weights = request.ranking_weights hoặc mặc định

  warnings = []

  preference = request.preference
  nếu chưa có:
    thử extractor (LLM hoặc deterministic)
    nếu lỗi:
      dùng extract_structured_preference()
      thêm cảnh báo

  nếu preference chưa có raw_goal và request có goal:
    gắn goal vào

  backend_name = "deterministic-keyword-v1"

  thử xếp hạng:
    nếu có ranker hoặc LLM ranker:
      dùng nó
    ngược lại:
      dùng KeywordRanker
    nếu lỗi:
      ranking = []
      thêm cảnh báo

  lọc ranking:
    chỉ giữ mã thuộc eligible
    bỏ mã trùng
    bỏ mã sai kiểu
    thêm cảnh báo nếu có mã bị loại

  nếu không còn mã hợp lệ:
    quay về deterministic

  luôn thêm phần còn lại của deterministic ranking
  (để danh sách không bị thiếu môn)

  duyệt từng mã:
    nếu cộng tín chỉ vượt max_credits: bỏ qua
    tính score
    tạo lý do từ eligibility + fit
    tạo RecommendedCourse
    tăng tổng tín chỉ
    dừng khi đủ limit

  đếm lý do bị chặn theo loại

  thêm cảnh báo:
    catalog chưa verified
    trạng thái mở lớp chưa xác minh

  trả RecommendationResponse
```

### `app/recommendation/preference.py` — hiểu mục tiêu

**Vai trò:** đổi câu tiếng Việt thành `StructuredPreference` bằng từ khóa. Không cần LLM.

```text
_fold(text):
  bỏ dấu tiếng Việt, đổi về chữ thường

_first_match(text, bảng_từ):
  trả giá trị của cụm từ đầu tiên xuất hiện

extract_structured_preference(goal):
  cắt goal tối đa 500 ký tự
  bỏ dấu

  tìm chủ đề quan tâm (AI, dữ liệu, mạng, ...)
  tìm workload (nhẹ / vừa / nặng)
  tìm difficulty (dễ / vừa / khó)
  tìm orientation (lý thuyết / thực hành / nghiên cứu)
  tìm nghề nghiệp mong muốn
  tìm số tín chỉ / số môn
  tìm loại môn (bắt buộc / tự chọn)
  tìm mức chấp nhận tiên quyết

  trả StructuredPreference
  (trường không tìm thấy thì để null)
```

### `app/recommendation/ranking.py` — xếp hạng

**Vai trò:** sắp môn theo điểm giảm dần. Chỉ trả mã môn.

```text
KeywordRanker.rank(candidates, goal, preference, weights):
  nếu chưa có preference:
    trích từ goal
  sắp xếp candidates theo:
    điểm giảm dần
    nếu bằng điểm thì mã tăng dần
  trả danh sách mã
```

### `app/recommendation/scoring.py` — chấm điểm

**Vai trò:** cho mỗi môn một điểm từ 0 đến 1 dựa trên metadata thật.

```text
score_course(course, preference, weights):
  lấy metadata của môn
  tạo vùng text để tìm từ khóa
  tính điểm từng phần:
    chủ đề khớp
    từ khóa khớp
    loại môn khớp
    hướng khớp
    độ khó khớp
    workload khớp
  chuẩn hóa theo tổng trọng số
  trả điểm 0..1
  (metadata thiếu thì không được cộng điểm)

fit_reason(course, preference, score):
  tạo câu giải thích ngắn
  chỉ dựa trên metadata có thật
```

### `app/recommendation/validation.py` — lọc output LLM

**Vai trò:** không cho LLM "bịa" mã môn.

```text
validate_ranking_output(output, allowed_codes):
  nếu output không phải list:
    trả rỗng + cảnh báo

  với từng phần tử:
    lấy code (hỗ trợ dict hoặc chuỗi)
    nếu không phải chuỗi hoặc không nằm trong allowed:
      đếm là invalid, bỏ
    nếu bị trùng:
      đếm là duplicate, bỏ
    ngược lại: giữ

  trả danh sách mã hợp lệ + cảnh báo
```

### `app/recommendation/explanation.py` — viết lý do

**Vai trò:** ghép lý do đủ điều kiện và lý do phù hợp thành một câu.

```text
build_grounded_explanation(course, preference, eligibility_reasons, score):
  fit = fit_reason(...)
  nếu có lý do đủ điều kiện:
    ghép lại
  nếu không:
    dùng câu mặc định
  reason = "Đủ điều kiện: ... Phù hợp: ..."
  trả (reason, fit)
```

### `app/recommendation/llm.py` — adapter LLM

**Vai trò:** bọc một nhà cung cấp LLM thành 2 thứ pipeline hiểu: bộ trích preference và bộ xếp hạng.

```text
LLMPreferenceExtractor.extract(goal):
  gọi provider
  validate kết quả bằng StructuredPreference

LLMRanker.rank(candidates, goal, preference, weights):
  tạo danh sách ứng viên gọn
  gọi provider
  trả kết quả thô
  (service sẽ validate mã)

_parse_json_response(text):
  bỏ code fence ```json
  parse JSON
  nếu lỗi → ValueError

_llm_text(prompt):
  gọi endpoint chat completions
  gửi model + prompt
  đọc choices[0].message.content
  nếu rỗng → lỗi

configured_adapters():
  nếu LLM bị tắt hoặc không có API key:
    trả (None, None)
  tạo provider cho preference
  tạo provider cho ranking
  trả 2 adapter
```

---

## 6F. Trợ lý ảo

### `app/services/advisor_service.py` — chat có kiểm soát

**Vai trò:** trả lời câu hỏi tự nhiên, nhưng vẫn bị khóa bởi eligibility.

```text
MAX_HISTORY_MESSAGES = 8
MAX_HISTORY_MESSAGE_CHARS = 500
MAX_FACTS_IN_PROMPT = 30
MAX_BLOCKED_IN_PROMPT = 15

_extract_session_preference(request):
  trích preference từ câu hiện tại
  trích thêm từ history
  trường nào câu hiện tại không có thì lấy từ history
  gộp chủ đề quan tâm (tối đa 20)
  trả preference

_build_recommendation_facts(catalog, eligibility, preference):
  với từng môn đủ điều kiện:
    tính score
    tạo lý do đủ điều kiện + lý do phù hợp
    tạo fact gồm mã, tên, tín chỉ, năm, điểm, lý do
  sắp xếp theo điểm giảm dần

_history_for_prompt(history):
  lấy 8 tin nhắn gần nhất
  cắt mỗi tin 500 ký tự
  định dạng thành văn bản

_extract_codes(text):
  tìm các mã dạng ABC1234
  bỏ trùng, giữ thứ tự

_validate_llm_suggestions(reply, eligible_codes):
  lấy mã trong câu trả lời
  lọc bằng validate_ranking_output

_has_unsafe_catalog_recommendation(reply, catalog_codes, eligible_codes):
  tìm môn không đủ điều kiện
  nếu cùng dòng có từ khuyến nghị ("nên", "gợi ý", "đăng ký", ...)
    → coi là không an toàn

_redact_unknown_course_codes(reply, catalog_codes):
  mã không có trong catalog
  → thay bằng "[mã ngoài catalog đã được loại bỏ]"

check_scope_guardrails(message):
  nếu câu hỏi chứa từ về thời khóa biểu / xếp lịch:
    trả (true, "schedule_request", câu từ chối)
  nếu chứa từ về giảng viên / dễ khó / xin điểm:
    trả (true, "instructor_evaluation", câu từ chối)
  ngược lại:
    trả (false, None, None)

heuristic_advisor(...):
  tạo eligibility giả từ dữ liệu đã có
  lấy facts
  chọn 4 môn đầu
  viết câu trả lời có:
    lời chào
    danh sách môn nên học
    2 môn bị chặn tiêu biểu
    lời khuyên
    ghi chú "Heuristic Advisor"
  trả (văn bản, danh sách mã)

build_advisor_prompt(...):
  tạo prompt gồm:
    vai trò cố vấn
    6 quy tắc (chỉ chọn môn eligible, không bịa, ...)
    ngành, số môn đã học
    danh sách môn đủ điều kiện
    preference JSON
    facts JSON
    một số môn bị chặn
    history
    câu hỏi
  trả prompt

call_gemini_api(prompt, api_key):
  đọc base_url và model
  nếu dùng cổng Beeknoee:
    đổi alias model
    gọi endpoint /chat/completions
    đọc choices[0].message.content
  nếu dùng Google trực tiếp:
    gọi generateContent
    ghép các part text
  trả văn bản

chat_advisor(catalog, request, api_key):
  kiểm tra program_id khớp catalog

  1. kiểm tra guardrail
     nếu bị chặn:
       trả mode = guardrail_rejected

  2. tính eligibility (max_credits = 40)
     lấy môn đủ điều kiện, môn bị chặn
     lấy tập mã catalog

  3. trích preference từ câu hỏi + history
     tạo facts

  4. nếu LLM đang bật và có key:
       build prompt
       gọi Gemini
       nếu câu trả lời khuyên môn không eligible:
         coi như lỗi → xuống fallback
       lọc mã hợp lệ
       che mã ngoài catalog
       trả mode = gemini_llm

  5. nếu không có key hoặc có lỗi:
       gọi heuristic_advisor()
       trả mode = heuristic_fallback
```

Ghi chú: advisor dùng `max_credits = 40` để không chặn oan môn chỉ vì ngân sách gợi ý. Nó vẫn chặn theo tiên quyết, track, nhánh và nhóm tự chọn.

---

## 6G. Giao diện web

### `app/static/index.html` — khung trang

**Vai trò:** bố cục nhìn thấy trên màn hình.

```text
phần đầu:
  tiêu đề
  chọn ngành
  chọn profile demo (nếu có)
  thông tin catalog

3 tab:
  Tab 1 "Bảng điểm":
    các ô KPI: số môn đạt, tín chỉ, GPA, số môn đủ điều kiện
    nút hồ sơ Năm 1 / Năm 2 / Năm 3
    nút xóa trắng
    ô tìm môn
    bộ lọc khối kiến thức
    danh sách môn để tick + nhập điểm

  Tab 2 "Điều kiện học":
    số môn đủ điều kiện / bị chặn / đã học
    danh sách môn đủ điều kiện
    danh sách môn bị chặn + lý do

  Tab 3 "Gợi ý":
    ô mục tiêu
    thanh chọn tín chỉ tối đa
    thanh chọn số môn tối đa
    3 thanh trọng số cho what-if
    nút chạy gợi ý
    nút chạy what-if
    vùng kết quả

khung chat nổi:
  nút mở chat
  cửa sổ chat
  chọn track / nhánh tốt nghiệp
  vùng tin nhắn
  ô nhập + nút gửi
```

### `app/static/app.js` — não của giao diện

**Vai trò:** giữ trạng thái trong trình duyệt, gọi API, vẽ kết quả.

```text
state:
  ngành đang chọn
  danh sách môn của ngành
  bảng điểm (mã môn → điểm/đã đạt)
  track, nhánh tốt nghiệp
  lịch sử chat
  request id để bỏ qua response cũ

api(path, options):
  gọi fetch
  nếu lỗi:
    đọc detail
    ném lỗi
  trả JSON

initTabs():
  bấm tab nào thì hiện panel đó

loadPrograms():
  gọi GET /programs
  đổ vào ô chọn ngành
  tự chọn ngành đầu tiên

onProgramChanged():
  tăng request id
  xóa bảng điểm, kết quả, track, nhánh
  load môn của ngành mới
  load profile của ngành
  vẽ lại checklist
  gọi updateStudentState()

renderCourseChecklist():
  lọc theo ô tìm kiếm + khối kiến thức
  vẽ từng môn:
    checkbox
    mã + tên + tín chỉ
    ô nhập điểm
  khi tick:
    thêm vào bảng điểm
    gọi updateStudentState()
  khi nhập điểm:
    cập nhật điểm
    gọi updateStudentState()

updateStudentState():
  tạo payload transcript từ state
  gọi POST /transcript/summary
  gọi POST /eligibility
  cập nhật KPI
  vẽ tab điều kiện

renderRuleEngineTab(eligibility):
  vẽ danh sách môn đủ điều kiện
  vẽ danh sách môn bị chặn
  mỗi lý do có nhãn loại lý do

handleRecommendationSubmit():
  tạo payload:
    ngành, môn đã học, mục tiêu
    tín chỉ, số môn
    track, nhánh
  gọi POST /recommendations
  vẽ kết quả

handleWhatIf():
  tạo payload giống trên
  thêm ranking_weights từ 3 thanh trượt
  gọi POST /recommendations/what-if
  vẽ kết quả

renderRecommendationData(data):
  hiện tổng quan
  hiện cảnh báo
  mỗi môn là một card:
    hạng, mã, tên, tín chỉ
    điểm
    lý do đủ điều kiện
    lý do phù hợp
    trạng thái nguồn / mở lớp

initFloatingAdvisor():
  mở / đóng / phóng to chat
  Enter để gửi
  gắn sự kiện cho form

gửi chat:
  thêm tin nhắn user vào khung
  gọi POST /advisor/chat với history
  thêm tin nhắn assistant
  nếu guardrail bị chặn: đánh dấu khác màu
  hiện các nút gợi ý môn

nút hồ sơ mẫu:
  tick sẵn một số môn
  gọi updateStudentState()

nút xóa trắng:
  xóa toàn bộ bảng điểm
  gọi updateStudentState()
```

Điểm quan trọng: **bảng điểm không được gửi lên server để lưu**. Mỗi lần đổi ngành, `app.js` xóa state. Đây là thiết kế có chủ ý để tránh lưu dữ liệu cá nhân.

### `app/static/styles.css`

**Vai trò:** trang trí. Không chứa nghiệp vụ.

```text
định nghĩa màu, khoảng cách, tab, card, badge
định nghĩa giao diện chat nổi
định nghĩa responsive cho màn hình nhỏ
```

### `app/static/favicon.svg`

**Vai trò:** icon nhỏ trên tab trình duyệt. Chỉ là hình.

---

## 6H. Module database HUS

### `database/hus_db/config.py` — đọc cấu hình database

**Vai trò:** đọc `HUS_DATABASE_URL`, che mật khẩu khi in log.

```text
ENV_VAR = "HUS_DATABASE_URL"
DEFAULT_SSLMODE = "require"
LOCAL_ENV_FILE = database/.env.docker

is_postgres_url(url):
  kiểm tra scheme bắt đầu bằng "postgres"

redact_url(url):
  thay mật khẩu bằng "***"

with_ssl_required(url):
  nếu chưa có sslmode:
    thêm sslmode=require

load_config(env=None):
  nếu truyền env thì chỉ đọc env đó
  nếu không:
    đọc file .env.docker
    rồi để biến môi trường thật ghi đè
  nếu thiếu HUS_DATABASE_URL → lỗi rõ ràng
  nếu không phải URL postgres → lỗi
  trả HusDatabaseConfig
```

Lưu ý bảo mật: mật khẩu Neon **không bao giờ** được commit. Chỉ đặt trong biến môi trường hoặc `database/.env.docker` (đã bị gitignore).

### `database/hus_db/connection.py` — tạo kết nối

**Vai trò:** tạo engine cho công cụ database.

```text
DEFAULT_CONNECT_TIMEOUT = 15 giây

create_engine_for(config):
  lấy URL đã bật SSL
  tạo engine
  bật pool_pre_ping
  đặt connect_timeout
  trả engine

connect(config=None):
  nếu chưa có config:
    load_config()
  gọi create_engine_for()
```

### `database/hus_db/schema.py` — bảng runtime

**Vai trò:** định nghĩa bảng `hus_catalog_revisions` cho công cụ Python.

```text
hus_catalog_revisions:
  revision_id (khóa chính, hash 64 ký tự)
  curriculum_id
  program_id
  active
  source_digest
  payload (JSONB)
  created_at

index:
  mỗi program chỉ có 1 revision active
  mỗi curriculum chỉ có 1 revision active
```

Các bảng nguồn (`courses`, `curricula`, ...) không định nghĩa ở đây. Chúng đến từ file SQL.

### `database/hus_db/prerequisites.py` — đọc ký hiệu tiên quyết

**Vai trò:** đổi chuỗi kiểu `(A B)/C` thành cấu trúc AND/OR.

```text
quy ước nguồn:
  dấu "/" = HOẶC
  khoảng trắng = VÀ
  ngoặc để gom nhóm

expression_key(expression):
  chuẩn hóa để so sánh 2 biểu thức có giống nhau không
  (không quan tâm thứ tự)

parse_prerequisites(raw):
  nếu rỗng → trả []
  bỏ khoảng trắng thừa
  tách token: mã môn, ngoặc, dấu /
  nếu có ký tự lạ → lỗi

  đọc biểu thức đệ quy:
    atom = mã môn hoặc "( ... )"
    alternatives = atom, nối bằng "/"
    conjunction = alternatives, nối bằng khoảng trắng

  nhân phân phối để đưa về dạng AND của OR
  ví dụ: (A B)/C → (A hoặc C) VÀ (B hoặc C)

  giới hạn số tổ hợp để tránh bùng nổ
  trả danh sách nhóm OR
```

### `database/hus_db/catalog_builder.py` — đóng gói catalog

**Vai trò:** đọc bảng nguồn trong `hus_source.json`, kiểm tra chéo, tạo 4 `Catalog`.

Đây là file dài và quan trọng nhất của module database.

```text
PROGRAM_IDS:
  (mã ngành, năm, phiên bản) → program_id

EXCLUDED:
  các môn không tính vào tổng tín chỉ

build_catalogs(bundle):
  kiểm tra schema_version = 1
  kiểm tra đủ 8 bảng nguồn

  tạo map tra cứu:
    faculties theo mã
    majors theo mã
    curricula theo id
    courses theo mã
    memberships theo (curriculum_id, course_code)
    groups theo (curriculum_id, group_key)
    entries theo entry_id
    prerequisites theo (curriculum, course, group_no, ref)

  kiểm tra:
    đúng 4 curriculum và đúng bộ (ngành, năm, phiên bản)
    major trỏ tới faculty có thật
    curriculum trỏ tới major có thật
    mỗi membership trỏ tới curriculum + course + group có thật
    mỗi entry trỏ tới membership + group có thật
    tín chỉ trong entry khớp tín chỉ course
    không có entry trùng
    mỗi membership có ít nhất 1 entry
    prerequisite không tự trỏ mình
    group_no liên tục từ 1

  với từng môn:
    đọc các lần xuất hiện trong nguồn
    parse text tiên quyết
    nếu text nói "không có" mà lại có chữ → lỗi
    nếu parse ra mã không tồn tại → lỗi
    so sánh biểu thức quan hệ với biểu thức trong text
      nếu khác hoàn toàn → lỗi
    nếu có nhiều biến thể khác nhau:
      đánh dấu conflict
    nếu trạng thái lạ hoặc có text mà không parse được:
      đánh dấu unknown
    ngược lại: draft_unverified

  với từng curriculum:
    tạo choice_groups:
      ngoại ngữ B1
      nhóm II
      nhóm IV.2
      các nhóm V.2
    tạo tracks nếu ngành có
    tạo graduation paths từ V.3
    tạo blocks I..V
    tạo Program
      catalog_status = draft_unverified
      kèm nguồn, ghi chú, bảng nhóm gốc

    với từng môn trong ngành:
      tạo Course:
        mã, tên, tín chỉ
        khối, loại yêu cầu
        tiên quyết đã parse
        trạng thái tiên quyết
        nhóm tự chọn
        nhánh tốt nghiệp
        metadata + bằng chứng từng trường
        dữ liệu nguồn để truy vết

    tạo Catalog
    validate_catalog()
    thêm vào kết quả

  trả danh sách 4 Catalog
```

Điểm cần nhớ: builder **không ghi database**. Nó chỉ kiểm tra và tạo object. Việc ghi là của `publish_catalogs.py`.

### `database/hus_db/introspect.py` — chụp nhanh schema

**Vai trò:** đọc cấu trúc database và in ra báo cáo.

```text
ColumnInfo / TableInfo / SchemaSnapshot:
  các object chứa thông tin schema

read_row_counts(engine, tên bảng):
  chạy một câu UNION ALL
  đếm tất cả bảng trong 1 lần
  nếu bảng chưa có thì bỏ qua

collect_schema(engine):
  đọc danh sách bảng
  đọc cột, kiểu, nullable, default
  đọc khóa chính, unique, foreign key, check, index
  đọc view
  đọc số dòng
  trả SchemaSnapshot

render_schema_text(snapshot):
  in dạng văn bản

render_schema_markdown(snapshot):
  in dạng bảng Markdown
```

### `database/hus_db/verify.py` — kiểm tra dữ liệu

**Vai trò:** chạy các bài kiểm tra để biết database có đúng không.

```text
CheckResult:
  tên bài kiểm tra
  đạt hay không
  mô tả

check_required_objects(snapshot):
  kiểm tra đủ bảng lõi
  kiểm tra đủ bảng official (nếu bật)
  kiểm tra đủ view

check_min_rows(counts):
  kiểm tra bảng có tối thiểu số dòng

check_no_prerequisite_cycles(engine):
  chạy SQL tìm chu trình tiên quyết
  phải bằng 0

check_curricula_have_courses(engine):
  mỗi ngành phải có ít nhất 1 môn

check_official_entries_covered(engine):
  mọi entry chính thức phải có trong curriculum_courses

run_checks(engine):
  gom tất cả bài kiểm tra
  trả danh sách kết quả

summarize(results):
  trả (số đạt, tổng số)
```

### `database/tools/migrate.py` — chạy migration HUS

**Vai trò:** cầu nối tới Alembic riêng của HUS.

```text
config():
  trỏ tới database/hus_alembic.ini
  trỏ script_location tới database/hus_alembic

main():
  nhận action: upgrade / current / heads
  upgrade → chạy lên head
  current → in phiên bản hiện tại
  heads → in các head
```

### `database/tools/apply_sql.py` — chạy file SQL

**Vai trò:** chạy DDL/import SQL một cách có kiểm soát.

```text
DANGEROUS_TOKENS = drop database, drop schema, alter database

scan_dangerous_statements(sql):
  bỏ qua comment
  bỏ qua chuỗi trong dấu nháy
  tìm các cụm nguy hiểm
  trả danh sách

apply_sql(engine, sql):
  gửi cả file SQL vào PostgreSQL
  để file tự BEGIN/COMMIT

main():
  nhận đường dẫn file + --dry-run + --allow-dangerous
  nếu dry-run: chỉ in kế hoạch
  nếu có lệnh nguy hiểm mà không cho phép: dừng
  nếu không: chạy
```

### `database/tools/inspect_schema.py` — in schema

**Vai trò:** CLI gọi `introspect.collect_schema()`.

```text
main():
  nhận --format text|markdown
  connect()
  collect_schema()
  in theo định dạng
```

### `database/tools/publish_catalogs.py` — publish catalog

**Vai trò:** đưa 4 catalog từ nguồn vào database, một transaction.

```text
NATURAL_KEYS:
  khóa tự nhiên của từng bảng nguồn

_upsert(conn, table, row, keys):
  INSERT ... ON CONFLICT
  nếu đã có thì UPDATE
  nếu không có gì để update thì DO NOTHING

_mapped_rows(rows, ids):
  đổi curriculum_id tạm sang id thật trong database

_assert_no_removed_relationships(...):
  so sánh quan hệ hiện có với nguồn mới
  nếu nguồn làm mất quan hệ cũ → báo lỗi
  (buộc người sửa phải xem tay)

publish_catalogs(engine, bundle):
  build_catalogs(bundle)  ← kiểm tra toàn bộ trước
  kiểm tra đúng 4 program
  validate từng catalog
  tính source_digest
  tính revision_id cho từng catalog

  mở transaction:
    khóa advisory để không publish chồng
    kiểm tra migration head đúng
    kiểm tra quan hệ cũ không bị mất
    upsert bảng nguồn
    ghi revision mới
    tắt active cũ
    bật active mới cho cả 4
    commit

activate_revision(engine, program_id, revision_id):
  đổi revision active của một ngành
  (dùng khi cần quay lại bản cũ)

main():
  đọc hus_source.json
  nhận --dry-run
  nếu dry-run: chỉ build + in kế hoạch
  nếu không: publish
```

### `database/tools/verify_data.py` — CLI kiểm tra

```text
main():
  đọc --no-official
  connect()
  run_checks()
  in PASS/FAIL từng bài
  in tổng số
  trả mã 0 nếu đạt hết, 1 nếu có lỗi
```

### `database/hus_alembic/env.py`

**Vai trò:** cấu hình Alembic cho HUS.

```text
run_migrations():
  lấy URL từ HUS_DATABASE_URL
  nối vào engine
  chạy migration trong transaction
```

### `database/hus_alembic/versions/20261017_01_baseline.py`

**Vai trò:** tạo hoặc "nhận" schema nguồn 13 bảng + 2 view.

```text
upgrade():
  kiểm tra các object đã tồn tại chưa
  nếu chưa có gì:
    chạy 00_ai07_schema.sql
    chạy phần DDL official
  nếu có một phần:
    từ chối adopt (tránh database nửa vời)
  nếu có đủ:
    tạo schema tạm
    dựng baseline chuẩn vào schema tạm
    so sánh từng cột/constraint/view với public
    nếu khác → báo lỗi
    nếu giống → coi như đã adopt

downgrade():
  không hỗ trợ (tránh mất dữ liệu)
```

### `database/hus_alembic/versions/20261017_02_runtime.py`

**Vai trò:** thêm các cột runtime và bảng snapshot.

```text
upgrade():
  thêm curricula.program_id
  thêm curricula.runtime_rules
  thêm curriculum_courses.applicable_credits
  thêm counted_in_total
  thêm runtime_metadata
  thêm prerequisite_state
  tạo bảng hus_catalog_revisions
  tạo unique index cho active
  thêm check hash 64 ký tự
  thêm check payload là object

downgrade():
  không hỗ trợ (sẽ mất snapshot)
```

Đây là revision `hus_20261017_02`, cũng là `HEAD` mà `HusRepository.ready()` mong đợi.

### `database/sql/00_ai07_schema.sql`

**Vai trò:** DDL gốc của database HUS.

```text
tạo 11 bảng:
  faculties, majors, curricula, courses
  curriculum_courses, course_prerequisites
  academic_terms, accounts, students
  course_attempts, student_preferences

tạo 2 view:
  v_students_profile
  v_student_transcript
```

### `database/sql/10_official_curricula_2023.sql`

**Vai trò:** tạo 2 bảng official và nạp 4 chương trình 2023.

```text
kiểm tra đang ở database ai07
kiểm tra schema gốc đã có
tạo official_curriculum_groups
tạo official_curriculum_entries
nạp dữ liệu 4 ngành
xóa dữ liệu demo cũ trong phạm vi cho phép
COMMIT
```

### `database/docker-compose.yml` và `database/.env.example`

**Vai trò:** dựng PostgreSQL HUS ở cổng 5433.

```text
container: se_hus_db
database:  ai07
port:      127.0.0.1:5433
volume:    se_hus_pgdata
mật khẩu:  đọc từ database/.env.docker
```

### `database/data/hus_source.json`

**Vai trò:** nguồn dữ liệu catalog.

```text
schema_version = 1
tables:
  faculties                    1 dòng
  majors                       4 dòng
  curricula                    4 dòng
  courses                    179 dòng
  curriculum_courses         290 dòng
  course_prerequisites       348 dòng
  official_curriculum_groups  41 dòng
  official_curriculum_entries 297 dòng
prerequisite_pdf_review: thông tin đợt rà soát PDF
```

### Các file tài liệu trong `database/`

- `README.md`: cách chạy nhanh.
- `DESIGN.md`: giải thích thiết kế database, bối cảnh, ví dụ.
- `SCHEMA.md`: ảnh chụp schema thật (tự sinh, không sửa tay).
- `HUS_RUNTIME.md`: biến môi trường, migration, publish, rollback.
- `DOCKER_SCHEMA.md`: schema khi chạy Docker.
- `DOCKER_VERIFICATION.md`: cách kiểm tra Docker.
- `archive/2026-10-17-sql-neon-guide.md`: hướng dẫn cũ, chỉ để tham khảo.

---

## 6I. Công cụ ở thư mục gốc

### `tools/build_catalogs.py` — build catalog từ bản nhập tay

**Vai trò:** dùng cho bộ catalog mẫu trong `data/curricula/`. Không dùng cho HUS runtime.

```text
prerequisite_clauses(raw):
  đọc ký hiệu "/" = HOẶC, khoảng trắng = VÀ
  trả cấu trúc AND của OR

build_courses(program, source_rows):
  với từng dòng nguồn:
    tạo thông tin môn
    gắn khối, nhóm, tín chỉ
    parse tiên quyết
  trả danh sách môn

check_curriculum(program, rows, courses):
  kiểm tra số dòng, số môn
  kiểm tra mã môn trùng
  kiểm tra dòng nguồn khớp môn
  trả báo cáo

merge_source_fields(existing, generated):
  giữ các trường metadata đã có
  cập nhật các trường sinh từ nguồn
  trả envelope mới

main():
  nhận --check (mặc định) hoặc --write
  với từng thư mục ngành:
    đọc curriculum.json + source_rows.json
    build courses
    kiểm tra
    đọc courses.json hiện tại
    chuẩn hóa
    nếu --write: ghi lại
    nếu --check: so sánh, khác thì báo lỗi
  in báo cáo
```

### `tools/seed_database.py` — seed database legacy

**Vai trò:** nạp catalog mẫu + profile demo vào database cũ. Không dùng cho HUS.

```text
seed_database(engine, source_root, profiles_path):
  đọc profiles.json
  yêu cầu đúng 12 profile, không trùng
  với từng thư mục ngành:
    load catalog
    validate catalog
    đọc source_rows
    kiểm tra curriculum
    chọn 3 profile của ngành
    validate từng profile
    tạo bundle
  yêu cầu đủ 4 ngành
  mở transaction:
    khóa advisory
    với từng bundle:
      tính revision_id = hash nội dung
      thêm program nếu chưa có
      nếu revision chưa có: ghi toàn bộ dữ liệu
      tắt active cũ
      bật active mới
  trả thống kê
```

---

## 6J. Test, dữ liệu mẫu và tài liệu

### `tests/` — bộ kiểm thử

Test được chia theo chức năng, không phải theo file code.

```text
tests/conftest.py
  cấu hình chung, fixture dùng lại

tests/advisor/test_advisor.py
  guardrail, fallback, prompt, lọc mã môn

tests/catalogs/
  test_catalog_fixtures.py      kiểm tra catalog mẫu
  test_curriculum_data.py       kiểm tra dữ liệu chương trình
  test_hus_catalog_builder.py   kiểm tra builder HUS
  test_metadata_builder.py      kiểm tra sinh metadata
  test_metadata_compatibility.py
  test_metadata_contract.py
  test_metadata_validation.py
  test_seed_validation.py

tests/database/
  test_database.py              test database legacy
  test_hus_database.py          test cấu hình/verify/apply
  test_hus_migration_runtime.py migration HUS
  test_hus_persistence.py       ghi/đọc snapshot
  test_hus_postgres.py          test cần PostgreSQL thật
  test_hus_runtime.py           runtime HUS
  integrity/test_sql_checks.py  kiểm tra SQL
  source/                       kiểm tra nguồn 4 ngành

tests/eligibility/test_rules.py
  tiên quyết, track, nhánh, nhóm, ngân sách tín chỉ

tests/progress/test_progress.py
  tín chỉ, phần trăm, track, nhánh

tests/recommendations/test_recommendations.py
  xếp hạng, LLM giả, lọc mã, what-if

tests/storage/test_storage.py
  chọn backend, lỗi storage, JSON/Postgres

tests/transcript/test_transcript.py
  chuẩn hóa, GPA, isolation, trùng môn

tests/support/
  fixture và helper dùng chung
```

Chạy test mặc định:

```bash
python -m pytest -q -m "not postgres and not hus_postgres and not full_catalog_acceptance"
```

### `data/curricula/khdl_7460108_2022/`

**Vai trò:** một mẫu catalog ngành Khoa học dữ liệu.

```text
curriculum.json   thông tin ngành, nhóm, track, nhánh
courses.json      danh sách môn
source_rows.json  dòng gốc đã nhập tay
vocabulary.json   từ vựng chủ đề/nghề nghiệp
README.md         ghi chú
```

Đây **không phải** nguồn runtime HUS. Đừng nhầm với `database/data/hus_source.json`.

### `alembic/` — migration legacy

**Vai trò:** lịch sử migration của database cũ. Giữ lại để rollback.

```text
alembic/env.py                    cấu hình Alembic legacy
alembic/schema_v1.py              định nghĩa schema legacy
alembic/versions/20261014_01_initial.py  migration đầu tiên
```

Cảnh báo: **không chạy migration này lên database `ai07`**. Hai database có lịch sử riêng.

### `docs/` — tài liệu kỹ thuật

- `SYSTEM_SPECIFICATION.md`: đặc tả hệ thống theo pipeline.
- `DATABASE_DESIGN.md`: thiết kế database.
- `COURSE_METADATA_SPECIFICATION.md`: đặc tả metadata môn.
- `COURSE_SELECTION_REASONS.md`: khung lý do chọn môn.
- `CODEBASE_CHECKLIST.md`: checklist tình trạng code.
- `CONTRIBUTING.md`: quy tắc đóng góp.
- `adr/0001-hus-runtime-and-rollback.md`: quyết định dùng HUS làm runtime.
- `VINH_*`: báo cáo kiểm tra dữ liệu/PDF của thành viên.
- `archive/`: tài liệu cũ.

### `modules/` — đặc tả chia việc

9 module:

```text
01 catalog
02 transcript/profile
03 eligibility
04 preference/ranking/what-if
05 explanation/LLM validation
06 advisor chat
07 recommendation API
08 web UI
09 transcript OCR (mới là kế hoạch)
```

Đây là tài liệu phân công, **không phải bằng chứng module đã xong**.

### `.agent/` và `AGENTS.md`

**Vai trò:** ghi nhớ dự án cho người/agent làm việc tiếp.

```text
.agent/AGENTS.md       hướng dẫn chi tiết
.agent/KE_HOACH_DU_AN.md  kế hoạch dự án
.agent/archive/        ghi nhớ cũ
AGENTS.md (gốc)        nhắc đọc .agent/AGENTS.md + quy tắc commit
```

---

## 6K. Các file `__init__.py` và file nối dây

Các file này thường rỗng hoặc chỉ export. Không có logic nghiệp vụ.

```text
app/__init__.py
app/api/__init__.py
app/db/__init__.py
app/infrastructure/__init__.py
app/recommendation/__init__.py
app/services/__init__.py
database/__init__.py
database/hus_db/__init__.py
database/tools/__init__.py
tests/__init__.py
tests/support/__init__.py
```

Chúng tồn tại để Python coi thư mục là "package" (gói) và cho phép import.

---

## 7. Từ điển nhanh (chỉ những từ hay gặp)

| Từ | Nghĩa dễ hiểu |
|---|---|
| **API** | Cửa để phần mềm khác gọi vào. Ví dụ `/recommendations`. |
| **Backend** | Phần chạy trên server, xử lý logic. |
| **Frontend** | Phần nhìn thấy trong trình duyệt. |
| **Endpoint** | Một đường dẫn API cụ thể, ví dụ `/eligibility`. |
| **Request / Response** | Yêu cầu gửi đi / kết quả trả về. |
| **Catalog** | Danh mục môn học của một ngành. |
| **Curriculum** | Chương trình đào tạo (có thể hiểu gần giống catalog). |
| **Eligibility** | Điều kiện được học một môn. |
| **Prerequisite** | Môn tiên quyết (phải học trước). |
| **Track** | Hướng chuyên ngành (ví dụ hướng Công nghệ phần mềm). |
| **Graduation path** | Nhánh tốt nghiệp (ví dụ làm khóa luận hay học thêm môn). |
| **Choice group** | Nhóm môn tự chọn, phải đủ số tín chỉ. |
| **Credits** | Tín chỉ. |
| **GPA** | Điểm trung bình tích lũy. |
| **Transcript** | Bảng điểm. |
| **Ranking** | Xếp hạng. |
| **Score** | Điểm phù hợp (0 đến 1), không phải điểm học tập. |
| **Weight** | Trọng số, mức quan trọng của từng tiêu chí. |
| **What-if** | "Nếu thử đổi trọng số thì kết quả ra sao". |
| **Guardrail** | Hàng rào chặn câu hỏi ngoài phạm vi. |
| **Fallback** | Phương án dự phòng khi cách chính lỗi. |
| **Deterministic** | Chạy cùng đầu vào thì luôn ra cùng kết quả, không ngẫu nhiên. |
| **LLM** | Mô hình ngôn ngữ lớn (như Gemini). |
| **Grounded** | Có căn cứ trong dữ liệu, không bịa. |
| **Schema** | Khuôn dữ liệu hoặc thiết kế bảng. |
| **Migration** | Kịch bản thay đổi cấu trúc database. |
| **Seed** | Nạp dữ liệu ban đầu. |
| **Publish** | Công bố catalog mới vào database. |
| **Revision** | Một phiên bản catalog. |
| **Snapshot** | Ảnh chụp dữ liệu tại một thời điểm. |
| **Repository** | Lớp code chuyên đọc/ghi dữ liệu. |
| **Adapter** | Lớp bọc để nối hai thứ khác giao diện. |
| **Runtime** | Phần đang chạy thật. |
| **Legacy** | Phần cũ, giữ để rollback. |
| **Rollback** | Quay về phiên bản trước. |
| **Transaction** | Một nhóm thay đổi database: hoặc thành công hết, hoặc hủy hết. |
| **Hash** | Chuỗi "dấu vân tay" của nội dung, dùng để phát hiện thay đổi. |
| **Fixture** | Dữ liệu mẫu cố định dùng cho test. |
| **Mock / Fake** | Đối tượng giả để test, không gọi mạng thật. |
| **Marker** | Nhãn đánh dấu test (ví dụ test cần PostgreSQL). |

---

## 8. Chạy dự án

### 8.1. Chuẩn bị

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt -c requirements-lock.txt
```

Tạo file cấu hình:

```bash
cp .env.example .env
cp database/.env.example database/.env.docker
```

Sau đó sửa mật khẩu trong `database/.env.docker`, và đặt `DATABASE_URL` trong `.env` trỏ tới database `ai07`.

### 8.2. Dựng database HUS

```bash
docker compose --env-file database/.env.docker -f database/docker-compose.yml up -d --wait
python -m database.tools.migrate upgrade
python -m database.tools.publish_catalogs --dry-run
python -m database.tools.publish_catalogs
python -m database.tools.verify_data
```

### 8.3. Chạy web

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Mở:

- `http://127.0.0.1:8000/` — giao diện
- `http://127.0.0.1:8000/docs` — danh sách API
- `http://127.0.0.1:8000/health` — kiểm tra tiến trình
- `http://127.0.0.1:8000/ready` — kiểm tra database + catalog

### 8.4. Chạy hoàn toàn offline (không gọi AI)

Trong `.env`:

```text
RECOMMENDATION_LLM_ENABLED=false
```

Hệ thống vẫn chạy đầy đủ, chỉ dùng xếp hạng từ khóa và câu trả lời mẫu.

### 8.5. Chạy test

```bash
python -m pytest -q -m "not postgres and not hus_postgres and not full_catalog_acceptance"
python -m ruff check .
python -X utf8 tools/build_catalogs.py --check
```

---

## 9. Sự thật hiện tại (để không bị bất ngờ)

- Có **4 ngành**: Toán học, Toán tin, Khoa học máy tính và thông tin, Khoa học dữ liệu.
- Nguồn HUS có **179 môn**, **290 quan hệ ngành–môn**, **348 quan hệ tiên quyết**.
- Cả 4 catalog đang ở trạng thái `draft_unverified` (chưa xác minh đầy đủ). Vì vậy kết quả chỉ để tham khảo.
- Môn có tiên quyết chưa rõ sẽ **bị chặn**, không được đoán.
- `MAT3325` có xung đột nguồn. `MAT3423` chưa xác định vì thiếu định nghĩa `MAT3402`.
- Bảng `accounts`, `students`, `course_attempts` đang trống. Không có dữ liệu sinh viên thật.
- API profile trả rỗng khi chạy HUS.
- `data/synthetic/profiles.json` đang thiếu.
- `data/curricula/` chỉ có 1 mẫu, nên JSON backend không chạy đủ 4 ngành.
- Trạng thái mở lớp luôn là `unknown`.
- LLM là tùy chọn. Không có key vẫn chạy bình thường.

---

## 10. Muốn sửa gì thì sửa ở đâu

| Bạn muốn đổi... | Sửa file |
|---|---|
| Quy tắc môn nào đủ điều kiện | `app/rules.py` |
| Cách tính điểm phù hợp | `app/recommendation/scoring.py` |
| Trọng số mặc định | `app/models.py` (class `RankingWeights`) |
| Cách hiểu câu mục tiêu | `app/recommendation/preference.py` |
| Câu trả lời mẫu của chat | `app/services/advisor_service.py` (`heuristic_advisor`) |
| Từ khóa bị chặn trong chat | `app/services/advisor_service.py` (`SCHEDULE_KEYWORDS`, `INSTRUCTOR_KEYWORDS`) |
| Danh sách API | `app/api/routes.py` |
| Khuôn request/response | `app/models.py` và `app/schemas/` |
| Giao diện | `app/static/index.html`, `app.js`, `styles.css` |
| Cấu hình chung | `app/config.py` và `.env` |
| Nguồn catalog HUS | `database/data/hus_source.json` rồi publish lại |
| Cấu trúc database HUS | thêm revision mới trong `database/hus_alembic/versions/` |
| Cấu trúc database legacy | thêm revision trong `alembic/versions/` |
| Cách đọc catalog | `app/infrastructure/` |
| Cách publish catalog | `database/tools/publish_catalogs.py` |
| Cách kiểm tra database | `database/hus_db/verify.py` |
| Dữ liệu test | `tests/support/` |

---

## 11. Nếu bạn chỉ có 30 phút để hiểu code

Đọc theo đúng thứ tự này:

```text
1. app/models.py
   → biết dữ liệu trông như thế nào

2. app/rules.py
   → biết "đủ điều kiện" nghĩa là gì (phần quan trọng nhất)

3. app/services/recommendation_service.py
   → biết các bước được ghép ra sao

4. app/api/routes.py
   → biết trình duyệt gọi vào đâu

5. app/main.py
   → biết app khởi động thế nào

6. app/services/advisor_service.py
   → biết chat hoạt động ra sao

7. app/catalog.py + app/infrastructure/
   → biết dữ liệu được đọc từ đâu

8. database/hus_db/catalog_builder.py
   → biết catalog được tạo từ nguồn thế nào
```

Nếu chỉ nhớ một điều, hãy nhớ:

> **Eligibility do code quyết định. LLM chỉ xếp hạng và viết lời giải thích.**

---

## 12. Những hiểu nhầm rất dễ gặp

### "Có hai thư mục alembic, chắc là một cái thừa"

Không. Chúng phục vụ hai database khác nhau:

```text
alembic/               → database legacy (course_recommender)
database/hus_alembic/  → database HUS (ai07)
```

Không chạy lẫn migration của cái này lên database của cái kia.

### "Seed database là nạp catalog HUS"

Không. `tools/seed_database.py` dành cho database **legacy**. Catalog HUS dùng `database/tools/publish_catalogs.py`.

### "Đổi what-if sẽ đổi danh sách môn đủ điều kiện"

Không. What-if chỉ đổi **cách xếp hạng**. Tập môn đủ điều kiện được tính một lần và giữ nguyên. Đây là chủ ý để so sánh công bằng.

### "Không có API key thì web không chạy"

Không. Hệ thống tự dùng fallback. Chỉ là câu trả lời chat sẽ theo mẫu, không tự nhiên bằng LLM.

### "API profile trả rỗng là do lỗi"

Không hẳn. HUS runtime cố ý không đọc hồ sơ sinh viên thật. Repo cũng chưa có `data/synthetic/profiles.json`. Đây là giới hạn dữ liệu, không phải lỗi code.

### "Catalog đã import thành công nghĩa là đã chính xác"

Không. Import thành công chỉ nghĩa là dữ liệu đúng **cấu trúc**. Nội dung vẫn là `draft_unverified`, cần con người đối chiếu PDF và quy định chính thức.

---

## 13. Tóm tắt cuối cùng

```text
Người dùng
   │
   ▼
Giao diện (app/static)
   │  gọi API
   ▼
FastAPI (app/main.py + app/api/routes.py)
   │
   ├─► Catalog (app/catalog.py → infrastructure/)
   ├─► Bảng điểm (app/transcript.py, app/profiles.py)
   ├─► Tiến độ (app/progress.py)
   ├─► Điều kiện (app/rules.py)          ← luôn chạy trước
   ├─► Gợi ý (app/services/recommendation_service.py)
   │      └─ preference → ranking → scoring → explanation
   └─► Chat (app/services/advisor_service.py)
          └─ guardrail → eligibility → LLM (tùy chọn) → fallback

Dữ liệu đến từ:
   database/data/hus_source.json
        │ publish
        ▼
   PostgreSQL ai07 (hus_catalog_revisions)
        │ đọc
        ▼
   app/infrastructure/hus_repository.py
```

Nếu bạn đọc đến đây, bạn đã nắm được toàn bộ dự án ở mức đủ để tìm file và hiểu luồng chạy. Muốn đi sâu phần nào, mở đúng file trong bảng ở mục 10.
