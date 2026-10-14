# SE_Project

Codebase của Explainable Course Recommender (AI-07): FastAPI, giao diện static, PostgreSQL và Alembic. Đây là dự án đang phát triển.

## Trạng thái dữ liệu hiện tại

`data/` chỉ giữ **mẫu Khoa học dữ liệu 2022 gồm 65 học phần**, theo hợp đồng metadata mới, để bàn giao cho người xây dựng dữ liệu. Xem [hướng dẫn mẫu](data/curricula/khdl_7460108_2022/README.md) và [đặc tả metadata](docs/COURSE_METADATA_SPECIFICATION.md).

Loader, validator, builder và seed đã hỗ trợ envelope metadata 1.0. Các catalog khác và profile sản phẩm đã được gỡ theo yêu cầu; mẫu vẫn chưa đối soát PDF. Một bản clone mới chưa đủ dữ liệu để chạy demo bốn ngành hoặc seed database sản phẩm từ đầu. Không dùng fixtures kiểm thử làm dữ liệu học vụ.

Database local đã seed trước đây được giữ nguyên; adapter vẫn đọc được định dạng legacy. JSON loader đọc được mẫu một ngành, nhưng readiness sản phẩm vẫn yêu cầu đủ bốn catalog. Seed kiểm tra đủ bốn catalog và 12 profile hợp lệ trước khi ghi database.

Builder `--check` kiểm tra mẫu mà không ghi file. `--write` giữ metadata tư vấn và evidence, từ chối thay đổi mã môn, tiên quyết hoặc trường đã review cần thẩm định lại. Việc cập nhật nguồn thực tế cần review dữ liệu và revision riêng; không chạy seed lên database đang dùng chỉ để thử mẫu.

## Cài môi trường

Yêu cầu Python 3.11+:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt -c requirements-lock.txt
```

Copy `.env.example` thành `.env` nếu chưa có, điền cấu hình và giữ bí mật server-side. Không ghi đè `.env` đang dùng. Skill/toolkit, môi trường ảo, cache và backup là tài nguyên local, không được push.

## Vận hành với database đã có dữ liệu

```powershell
docker compose up -d db
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

Mở `http://127.0.0.1:8000`, API docs ở `/docs`. `/health` kiểm tra tiến trình; `/ready` kiểm tra storage và catalog. PostgreSQL là backend mặc định, không tự fallback sang JSON. Không chạy `docker compose down -v` nếu muốn giữ database.

## Kiểm tra và giới hạn

```powershell
python -m ruff check app tests tools alembic
python -m pytest -q
python -X utf8 tools/build_catalogs.py --check
```

Test nghiệp vụ dùng fixtures giả lập nhỏ tại `tests/fixtures/`: bốn ngành, 14 môn/ngành và 12 profile, không phải bản khôi phục các catalog đã xóa. Mẫu thật 65 môn được kiểm tra riêng. Test PostgreSQL chỉ chạy khi đặt `TEST_DATABASE_URL`, tạo/drop schema `se_test_*` riêng; không dùng database sản phẩm để chạy thử.

Các kiểm thử kiểm kê đầy đủ nguồn bốn ngành có marker `full_catalog_acceptance`. Mặc định chúng được bỏ qua vì chưa có nguồn đầy đủ; chạy rõ ràng bằng `python -m pytest -m full_catalog_acceptance --full-catalog-root <thu-muc-nguon>`. Nguồn được yêu cầu nhưng thiếu/sai sẽ làm kiểm tra thất bại. CI tách offline và PostgreSQL trên fixtures; chưa xác minh CI remote. Xem [checklist và kết quả kiểm tra](docs/CODEBASE_CHECKLIST.md).

## Tài liệu

- [Đặc tả hệ thống](docs/SYSTEM_SPECIFICATION.md)
- [Thiết kế database](docs/DATABASE_DESIGN.md)
- [Metadata môn học](docs/COURSE_METADATA_SPECIFICATION.md)
- [Phân trách nhiệm module](modules/README.md)
- `KE_HOACH_DU_AN.md` và `SE_Project.pdf`: tài liệu kế hoạch/bối cảnh lịch sử.

Các tài liệu hệ thống/database mô tả kiến trúc hướng tới bốn chương trình; trạng thái dữ liệu thực tế hiện tại được ghi ở README này và README trong `data/`. Không dùng checklist lịch sử để khẳng định toàn bộ tính năng đã hoàn tất.
