-- AI07 / NEON / DATABASE ai07 / public schema
-- OFFICIAL 2023 HUS CURRICULA: 3565,3567,3568,3569 (applicable from 2022 admission onwards).
-- Generated from the four user-provided PDF scans; no synthetic grades are loaded.
-- DESTRUCTIVE WITHIN DEMO SCOPE: deletes demo students 99000001-99000008, demo curricula and their demo points.
-- Before executing: create a Neon branch or backup. Connect to database ai07 (NOT neondb).
-- DOES NOT DROP database ai07, entire schema public, or user-created records outside demo scope.
--
-- Repository note: run `sql/00_ai07_schema.sql` first — it creates the 11 base tables
-- and the 2 read-only views this file depends on. This file creates the 2 official_*
-- tables and imports the four official 2023 HUS curricula. See database/README.md
-- for the exact run order and the expected post-import row counts.
BEGIN;
SET LOCAL client_min_messages TO NOTICE;
DO $$
BEGIN
  IF current_database() <> 'ai07' THEN
    RAISE EXCEPTION 'Expected database ai07; connected to %', current_database();
  END IF;
  IF to_regclass('public.courses') IS NULL OR to_regclass('public.students') IS NULL
     OR to_regclass('public.curricula') IS NULL OR to_regclass('public.curriculum_courses') IS NULL THEN
    RAISE EXCEPTION 'The original 11-table AI07 schema is missing. Apply 01_ai07_tables_and_data_fixed.sql first.';
  END IF;
END $$;

-- Required additional tables: distinguish duplicated entries from curriculum_courses PRIMARY KEY,
-- track elective-group credit limits and preserve exact prerequisite text and printed PDF page.
CREATE TABLE IF NOT EXISTS public.official_curriculum_groups (
  curriculum_id BIGINT NOT NULL REFERENCES public.curricula(curriculum_id) ON DELETE CASCADE,
  group_key TEXT NOT NULL,
  group_title TEXT NOT NULL,
  min_credits_if_selected SMALLINT,
  offered_credits SMALLINT,
  source_heading TEXT,
  group_note TEXT,
  PRIMARY KEY (curriculum_id,group_key)
);
CREATE TABLE IF NOT EXISTS public.official_curriculum_entries (
  entry_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  curriculum_id BIGINT NOT NULL,
  group_key TEXT NOT NULL,
  source_row_number SMALLINT,
  course_code TEXT NOT NULL REFERENCES public.courses(course_code),
  credits_in_source SMALLINT NOT NULL,
  prerequisite_source_text TEXT,
  prerequisite_parse_status TEXT NOT NULL CHECK (prerequisite_parse_status IN
     ('none','normalized','complex_expression','unlisted_prerequisite','needs_review')),
  pdf_document TEXT NOT NULL,
  pdf_page SMALLINT NOT NULL,
  FOREIGN KEY (curriculum_id,group_key) REFERENCES
     public.official_curriculum_groups(curriculum_id,group_key) ON DELETE CASCADE,
  UNIQUE (curriculum_id,group_key,course_code)
);
CREATE INDEX IF NOT EXISTS ix_official_entries_course ON public.official_curriculum_entries(course_code);

-- Remove only synthetic records supplied by our initial demo seed; do not touch any other students.
DELETE FROM public.students
 WHERE student_code IN ('99000001','99000002','99000003','99000004','99000005','99000006','99000007','99000008')
   AND full_name LIKE 'Sinh viên mẫu%';
DELETE FROM public.accounts
 WHERE username IN ('99000001','99000002','99000003','99000004','99000005','99000006','99000007','99000008')
   AND role='student'
   AND NOT EXISTS (SELECT 1 FROM public.students s WHERE s.student_code=public.accounts.username);

-- Old demo curricula: remove only our version (restrict for safety if actual student was bound to one).
DELETE FROM public.curricula
 WHERE curriculum_version='DEMO-2023' AND major_code IN ('7460101','7460117','7460108','7480113QTD');

INSERT INTO public.faculties(faculty_code,faculty_name) VALUES
 ('MIM','Khoa Toán - Cơ - Tin học') ON CONFLICT (faculty_code)
 DO UPDATE SET faculty_name=EXCLUDED.faculty_name;
INSERT INTO public.majors(major_code,faculty_code,major_name,admission_code) VALUES
 ('7460101','MIM','Toán học','QHT01'),
 ('7460117','MIM','Toán tin','QHT02'),
 ('7460108','MIM','Khoa học dữ liệu','QHT93'),
 ('7480113QTD','MIM','Khoa học máy tính và thông tin','QHT98')
 ON CONFLICT (major_code) DO UPDATE
 SET faculty_code=EXCLUDED.faculty_code,major_name=EXCLUDED.major_name;

INSERT INTO public.curricula (major_code,curriculum_version,cohort_year,credits_required,official_source_url,note) VALUES
 ('7460101','QD3565-2023',2022,135,NULL,'Quyết định 3565/QĐ-ĐHKHTN ngày 18/10/2023; áp dụng từ khóa tuyển sinh 2022. Nguồn: file PDF do người dùng cung cấp: 101. Toán học-chuẩn final QD 3565 Scan.pdf'),
 ('7460117','QD3567-2023',2022,132,NULL,'Quyết định 3567/QĐ-ĐHKHTN ngày 18/10/2023; áp dụng từ khóa tuyển sinh 2022. Nguồn: file PDF do người dùng cung cấp: 103. Toán tin-chuẩn final QD 3567 Scan.pdf'),
 ('7480113QTD','QD3568-2023',2022,129,NULL,'Quyết định 3568/QĐ-ĐHKHTN ngày 18/10/2023; áp dụng từ khóa tuyển sinh 2022. Nguồn: file PDF do người dùng cung cấp: 104.-KHMTTT-chuẩn final QD 3568 Scan final.pdf'),
 ('7460108','QD3569-2023',2022,127,NULL,'Quyết định 3569/QĐ-ĐHKHTN ngày 18/10/2023; áp dụng từ khóa tuyển sinh 2022. Nguồn: file PDF do người dùng cung cấp: 105.-Khoa-học-dữ-liệu-chuẩn final QĐ 3569 Scan.pdf')
ON CONFLICT (major_code,curriculum_version,cohort_year) DO UPDATE
SET credits_required=EXCLUDED.credits_required, note=EXCLUDED.note;

CREATE TEMP TABLE _new_curricula ON COMMIT DROP AS
SELECT curriculum_id,major_code FROM public.curricula
 WHERE (major_code,curriculum_version,cohort_year) IN
 (
  ('7460101','QD3565-2023',2022),
  ('7460117','QD3567-2023',2022),
  ('7480113QTD','QD3568-2023',2022),
  ('7460108','QD3569-2023',2022)
 );
-- Clear old official catalog links if this migration is re-run.
DELETE FROM public.official_curriculum_groups g USING _new_curricula nc WHERE g.curriculum_id=nc.curriculum_id;
DELETE FROM public.curriculum_courses cc USING _new_curricula nc WHERE cc.curriculum_id=nc.curriculum_id;

-- Actual course list from the four PDF curriculum tables. Difficulty/tags from demo are removed.
INSERT INTO public.courses(course_code,course_name,credits,difficulty_level,topics,description,is_active) VALUES
 ('CME1000','Giáo dục quốc phòng - an ninh',8,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('FLF1107','Tiếng Anh B1',5,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('FLF1207','Tiếng Nga B1',5,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('FLF1307','Tiếng Pháp B1',5,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('FLF1407','Tiếng Trung Quốc B1',5,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('FLF1507','Tiếng Đức B1',5,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('FLF1607','Tiếng Nhật Bản B1',5,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('FLF1707','Tiếng Hàn Quốc B1',5,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('HIS1001','Lịch sử Đảng Cộng sản Việt Nam',2,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('HIS1056','Cơ sở văn hóa Việt Nam',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('HUS1011','Tin học cơ sở',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('HUS1012','Kỹ năng bổ trợ',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('HUS1021','Khoa học Trái Đất và sự sống',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('HUS1022','Nhập môn Internet kết nối vạn vật',2,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('HUS1023','Nhập môn phân tích dữ liệu',2,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('HUS1024','Nhập môn Robotic',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT1076','Cơ học lý thuyết',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT1201','Phương pháp nghiên cứu khoa học',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT1202','Lập trình hướng đối tượng',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT1203','Phân tích và thiết kế hệ thống thông tin',4,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT1204','Phương pháp nghiên cứu khoa học',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT1205E','Tiếng Anh chuyên ngành khoa học máy tính',2,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT1206E','Nhập môn Trí tuệ nhân tạo',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT1207','Công nghệ phần mềm',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT1208','Xây dựng hệ thống nhúng',2,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT1209','Tự động hóa',2,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT2034','Giải tích số',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT2300','Đại số tuyến tính 1',4,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT2301','Đại số tuyến tính 2',4,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT2302','Giải tích 1',5,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT2303','Giải tích 2',5,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT2304','Giải tích 3',4,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT2306','Phương trình đạo hàm riêng 1',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT2307','Giải tích số 1',4,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT2308','Xác suất 1',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT2310','Hình học giải tích',2,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT2311','Thống kê ứng dụng',4,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT2314','Phương trình vi phân',4,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT2315','Phương pháp nghiên cứu khoa học',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT2316','Lập trình C/C++',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT2318','Lập trình Python',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT2319','Lập trình Julia',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT2323','Xác suất - Thống kê',4,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT2400','Đại số tuyến tính',5,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT2403','Phương trình vi phân',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT2404','Giải tích số',4,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT2405','Xác suất',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT2406','Thống kê ứng dụng',4,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT2407','Tối ưu hóa',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT2501','Giải tích 1',4,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT2502','Giải tích 2',4,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT2503','Giải tích 3',2,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT2505','Lập trình cơ bản',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3148','Tính toán song song',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3300','Đại số đại cương',4,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3301','Giải tích hàm',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3302','Toán rời rạc',4,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3304','Thực hành tính toán',2,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3305','Tôpô đại cương',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3306','Cơ sở hình học vi phân',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3307','Lý thuyết độ đo và tích phân',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3310','Cơ sở tôpô đại số',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3311','Lý thuyết nhóm và biểu diễn nhóm',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3313','Lý thuyết số',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3317','Phương trình đạo hàm riêng 2',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3318','Giải tích trên đa tạp',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3321','Quá trình ngẫu nhiên',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3322','Xác suất 2',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3323','Tối ưu rời rạc',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3324','Tổ hợp',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3325','Lịch sử toán học',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3326','Xêmina Toán lý thuyết',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3327','Điều khiển tối ưu',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3329','Giải tích số 2',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3333','Các mô hình toán ứng dụng 1',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3334','Các mô hình toán ứng dụng 2',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3335','Đại số máy tính',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3337','Xêmina Toán ứng dụng',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3339','Đại số tuyến tính 3',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3344','Giải tích phức',4,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3345','Lý thuyết ổn định của phương trình vi phân',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3347','Lý thuyết Galois',4,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3359','Thực tập chuyên ngành',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3360','Tối ưu hóa nâng cao',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3361','Cơ học lý thuyết nâng cao',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3362','Một số vấn đề chọn lọc trong Cơ học',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3365','Phương trình đạo hàm riêng',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3366','Hệ máy tính',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3367','Đại số ứng dụng',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3368','Thuật toán ngẫu nhiên',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3369','Giải tích số nâng cao',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3370','Thống kê Bayes',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3371','Xây dựng phần mềm',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3373E','Nhập môn an toàn máy tính',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3374','Thực tập thực tế phát triển phần mềm',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3377','Một số vấn đề chọn lọc về Trí tuệ nhân tạo',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3378','Quản trị dữ liệu lớn',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3379','Phân tích hồi quy và ứng dụng',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3381','Thực tập thực tế về Khoa học dữ liệu',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3382','Lập trình cho Khoa học dữ liệu',2,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3383','Trực quan hóa thông tin',2,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3385','Cơ sở dữ liệu Web và hệ thống thông tin',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3386','Phương pháp tính toán trong thống kê và khoa học dữ liệu',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3387','Kĩ thuật lấy mẫu khảo sát',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3388','Phân tích chuỗi thời gian',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3389','Quy hoạch thực nghiệm',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3390','Nhập môn Tin sinh học',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3391','Hệ thống thông tin địa lí',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3392','Ứng dụng dữ liệu lớn trong quản lí rủi ro tai biến thiên nhiên',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3393','Khai thác dữ liệu trong Hóa học',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3394','Mô hình toán sinh thái',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3395','Lí thuyết trò chơi',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3396','Sức bền vật liệu',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3397','Một số vấn đề ứng dụng của khoa học dữ liệu',4,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3398','Một số chủ đề trong mô hình hóa và phân tích dữ liệu',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3399','Xử lí ngôn ngữ tự nhiên và học sâu',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3401','Phép tính biến phân',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3406','Lý thuyết dao động',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3407','Lý thuyết đàn hồi',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3408','Cơ học chất lỏng',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3409','Giải tích hàm ứng dụng',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3411','Phương pháp phần tử hữu hạn',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3412','Lý thuyết dẻo',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3413','Cơ học giải tích',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3415','Cơ học vật liệu composite',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3418','Phương pháp số trong cơ học',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3422','Lý thuyết bản và vỏ mỏng',4,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3423','Cơ học môi trường liên tục',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3452','Phân tích thống kê nhiều chiều',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3453','Phương pháp chọn mẫu dữ liệu',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3456','Logic ứng dụng',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3500','Toán rời rạc',4,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3504','Thiết kế và đánh giá thuật toán',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3505','Kiến trúc máy tính',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3506','Mạng máy tính',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3507','Cơ sở dữ liệu',4,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3508','Nhập môn trí tuệ nhân tạo',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3509','Ngôn ngữ hình thức và ôtômat',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3514','Cấu trúc dữ liệu và thuật toán',4,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3519','Ngôn ngữ lập trình thứ hai',2,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3525','Thực hành tính toán',2,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3531','Tính toán phân tán',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3533','Học máy',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3534','Khai phá dữ liệu',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3535','Tìm kiếm thông tin',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3538','Các hệ thống tri thức',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3539','Mật mã và an toàn dữ liệu',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3541E','Nguyên lí các ngôn ngữ lập trình',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3542','Phát triển ứng dụng web',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3545','Lý thuyết tính toán',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3550E','Nguyên lí hệ điều hành',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3552E','Thiết kế và đánh giá thuật toán',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3554E','Ngôn ngữ hình thức và ôtômat',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3557','Môi trường lập trình Linux',2,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3558','Lập trình mobile',2,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3560','Phát triển phần mềm trò chơi',2,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3561','Xử lí ngôn ngữ tự nhiên và ứng dụng',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3561E','Xử lí ngôn ngữ tự nhiên và ứng dụng',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3562','Thị giác máy tính',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3562E','Thị giác máy tính',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3563','Một số vấn đề chọn lọc về thị giác máy tính',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT3565','Nhập môn khai phá các tập dữ liệu lớn',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT4070','Khóa luận tốt nghiệp',7,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT4071','Một số vấn đề chọn lọc trong Toán học',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT4072','Một số vấn đề chọn lọc trong tính toán khoa học',4,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT4080','Khóa luận tốt nghiệp',7,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT4082','Khóa luận tốt nghiệp',7,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('MAT4083','Khóa luận tốt nghiệp',7,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('PEC1008','Kinh tế chính trị Mác - Lênin',2,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('PES1000','Giáo dục thể chất',4,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('PHI1002','Chủ nghĩa xã hội khoa học',2,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('PHI1006','Triết học Mác - Lênin',3,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('POL1001','Tư tưởng Hồ Chí Minh',2,2,ARRAY[]::TEXT[],NULL,TRUE),
 ('THL1057','Nhà nước và pháp luật đại cương',2,2,ARRAY[]::TEXT[],NULL,TRUE)
ON CONFLICT(course_code) DO UPDATE
SET course_name=EXCLUDED.course_name, credits=EXCLUDED.credits,
    difficulty_level=2, topics=ARRAY[]::TEXT[], description=NULL, is_active=TRUE;

-- Use a normalized flat temp source preserving each printed occurrence (including duplicates across tracks).
CREATE TEMP TABLE _official_rows (
 major_code TEXT, group_key TEXT, source_row_number SMALLINT,
 course_code TEXT, course_name TEXT, credits_in_source SMALLINT,
 pdf_page SMALLINT, prerequisite_source_text TEXT,
 prerequisite_parse_status TEXT, course_type TEXT
) ON COMMIT DROP;
INSERT INTO _official_rows VALUES
 ('7460101','I',1,'PHI1006','Triết học Mác - Lênin',3,8,NULL,'none','required'),
 ('7460101','I',2,'PEC1008','Kinh tế chính trị Mác - Lênin',2,8,'PHI1006','normalized','required'),
 ('7460101','I',3,'PHI1002','Chủ nghĩa xã hội khoa học',2,8,'PHI1006','normalized','required'),
 ('7460101','I',4,'HIS1001','Lịch sử Đảng Cộng sản Việt Nam',2,8,NULL,'none','required'),
 ('7460101','I',5,'POL1001','Tư tưởng Hồ Chí Minh',2,8,NULL,'none','required'),
 ('7460101','I',6,'THL1057','Nhà nước và pháp luật đại cương',2,8,NULL,'none','required'),
 ('7460101','I',7,'HUS1011','Tin học cơ sở',3,8,NULL,'none','required'),
 ('7460101','I',8,'FLF1107','Tiếng Anh B1',5,8,NULL,'none','elective'),
 ('7460101','I',8,'FLF1207','Tiếng Nga B1',5,8,NULL,'none','elective'),
 ('7460101','I',8,'FLF1307','Tiếng Pháp B1',5,8,NULL,'none','elective'),
 ('7460101','I',8,'FLF1407','Tiếng Trung Quốc B1',5,8,NULL,'none','elective'),
 ('7460101','I',8,'FLF1507','Tiếng Đức B1',5,8,NULL,'none','elective'),
 ('7460101','I',8,'FLF1607','Tiếng Nhật Bản B1',5,8,NULL,'none','elective'),
 ('7460101','I',8,'FLF1707','Tiếng Hàn Quốc B1',5,8,NULL,'none','elective'),
 ('7460101','I',9,'CME1000','Giáo dục quốc phòng - an ninh',8,9,NULL,'none','required'),
 ('7460101','I',10,'PES1000','Giáo dục thể chất',4,9,NULL,'none','required'),
 ('7460101','I',11,'HUS1012','Kỹ năng bổ trợ',3,9,NULL,'none','required'),
 ('7460101','II',12,'HUS1021','Khoa học Trái Đất và sự sống',3,9,NULL,'none','elective'),
 ('7460101','II',13,'HUS1022','Nhập môn Internet kết nối vạn vật',2,9,NULL,'none','elective'),
 ('7460101','II',14,'HUS1023','Nhập môn phân tích dữ liệu',2,9,NULL,'none','elective'),
 ('7460101','II',15,'HUS1024','Nhập môn Robotic',3,9,NULL,'none','elective'),
 ('7460101','II',16,'HIS1056','Cơ sở văn hóa Việt Nam',3,9,NULL,'none','elective'),
 ('7460101','III',17,'MAT1076','Cơ học lý thuyết',3,9,'MAT2302','normalized','required'),
 ('7460101','IV.1',18,'MAT2300','Đại số tuyến tính 1',4,9,NULL,'none','required'),
 ('7460101','IV.1',19,'MAT2301','Đại số tuyến tính 2',4,9,'MAT2300','normalized','required'),
 ('7460101','IV.1',20,'MAT2302','Giải tích 1',5,9,NULL,'none','required'),
 ('7460101','IV.1',21,'MAT2303','Giải tích 2',5,9,'MAT2302','normalized','required'),
 ('7460101','IV.1',22,'MAT2304','Giải tích 3',4,9,'MAT2303','normalized','required'),
 ('7460101','IV.1',23,'MAT2314','Phương trình vi phân',4,9,'MAT2301/
MAT2321
MAT2303','unlisted_prerequisite','required'),
 ('7460101','IV.1',24,'MAT2306','Phương trình đạo hàm riêng 1',3,10,'MAT2304
MAT2314','normalized','required'),
 ('7460101','IV.1',25,'MAT2307','Giải tích số 1',4,10,'MAT2314
MAT2316/
MAT2505/
MAT2318/
MAT2319','normalized','required'),
 ('7460101','IV.1',26,'MAT2308','Xác suất 1',3,10,'MAT2300/
MAT2320
MAT2302','unlisted_prerequisite','required'),
 ('7460101','IV.1',27,'MAT2407','Tối ưu hóa',3,10,'MAT2301/
MAT2321/
MAT2400
MAT2303/
MAT2502','unlisted_prerequisite','required'),
 ('7460101','IV.1',28,'MAT2310','Hình học giải tích',2,10,'MAT2301/
MAT2321','unlisted_prerequisite','required'),
 ('7460101','IV.1',29,'MAT2311','Thống kê ứng dụng',4,10,'MAT2308','normalized','required'),
 ('7460101','IV.1',30,'MAT2315','Phương pháp nghiên cứu khoa học',3,10,NULL,'none','required'),
 ('7460101','IV.2',31,'MAT2316','Lập trình C/C++',3,10,'HUS1011','normalized','elective'),
 ('7460101','IV.2',32,'MAT2505','Lập trình cơ bản',3,10,'HUS1011','normalized','elective'),
 ('7460101','IV.2',33,'MAT2318','Lập trình Python',3,10,'HUS1011','normalized','elective'),
 ('7460101','IV.2',34,'MAT2319','Lập trình Julia',3,10,'HUS1011','normalized','elective'),
 ('7460101','V.1',35,'MAT3300','Đại số đại cương',4,10,'MAT2301/
MAT2321','unlisted_prerequisite','required'),
 ('7460101','V.1',36,'MAT3301','Giải tích hàm',3,10,'MAT2301
MAT2304','normalized','required'),
 ('7460101','V.1',37,'MAT3302','Toán rời rạc',4,10,NULL,'none','required'),
 ('7460101','V.1',38,'MAT3344','Giải tích phức',4,11,'MAT2301/
MAT2321
MAT2304/
MAT2322','unlisted_prerequisite','required'),
 ('7460101','V.1',39,'MAT3304','Thực hành tính toán',2,11,'MAT2307','normalized','required'),
 ('7460101','V.1',40,'MAT3305','Tôpô đại cương',3,11,'MAT2302','normalized','required'),
 ('7460101','V.1',41,'MAT3306','Cơ sở hình học vi phân',3,11,'MAT2300/
MAT2320
MAT3305','unlisted_prerequisite','required'),
 ('7460101','V.1',42,'MAT3307','Lý thuyết độ đo và tích phân',3,11,'MAT2304/
MAT2322','unlisted_prerequisite','required'),
 ('7460101','V.1',43,'MAT3347','Lý thuyết Galois',4,11,'MAT3300','normalized','required'),
 ('7460101','V.1',44,'MAT3359','Thực tập chuyên ngành',3,11,'(MAT1202
MAT3507)/
MAT3304','complex_expression','required'),
 ('7460101','V.2.1',45,'MAT3339','Đại số tuyến tính 3',3,11,'MAT2301/
MAT2321','unlisted_prerequisite','elective'),
 ('7460101','V.2.1',46,'MAT3310','Cơ sở tôpô đại số',3,11,'MAT3300
MAT3305','normalized','elective'),
 ('7460101','V.2.1',47,'MAT3311','Lý thuyết nhóm và biểu diễn nhóm',3,11,'MAT3300','normalized','elective'),
 ('7460101','V.2.1',48,'MAT3313','Lý thuyết số',3,11,'MAT2301/
MAT2321
MAT2304/
MAT2322','unlisted_prerequisite','elective'),
 ('7460101','V.2.1',49,'MAT3317','Phương trình đạo hàm riêng 2',3,11,'MAT3301/
MAT3340
MAT3307','unlisted_prerequisite','elective'),
 ('7460101','V.2.1',50,'MAT3318','Giải tích trên đa tạp',3,11,'MAT3339
MAT3305','normalized','elective'),
 ('7460101','V.2.1',51,'MAT3345','Lý thuyết ổn định của phương trình vi phân',3,11,'MAT2314','normalized','elective'),
 ('7460101','V.2.1',52,'MAT3321','Quá trình ngẫu nhiên',3,12,'MAT2311','normalized','elective'),
 ('7460101','V.2.1',53,'MAT3322','Xác suất 2',3,12,'MAT2308
MAT3307','normalized','elective'),
 ('7460101','V.2.1',54,'MAT3323','Tối ưu rời rạc',3,12,'MAT2407
MAT3302/
MAT3500','normalized','elective'),
 ('7460101','V.2.1',55,'MAT3324','Tổ hợp',3,12,'MAT3302','normalized','elective'),
 ('7460101','V.2.1',56,'MAT3325','Lịch sử toán học',3,12,'MAT2314
MAT2304','normalized','elective'),
 ('7460101','V.2.1',57,'MAT3326','Xêmina Toán lý thuyết',3,12,'MAT2308','normalized','elective'),
 ('7460101','V.2.2',58,'MAT3327','Điều khiển tối ưu',3,12,'MAT2306/
MAT2313/
MAT3365
MAT2311/
MAT2406','unlisted_prerequisite','elective'),
 ('7460101','V.2.2',59,'MAT3370','Thống kê Bayes',3,12,'MAT2308/
MAT2405','normalized','elective'),
 ('7460101','V.2.2',60,'MAT3329','Giải tích số 2',3,12,'MAT2307','normalized','elective'),
 ('7460101','V.2.2',61,'MAT3360','Tối ưu hóa nâng cao',3,12,'MAT2407','normalized','elective'),
 ('7460101','V.2.2',62,'MAT3323','Tối ưu rời rạc',3,12,'MAT2407
MAT3302/
MAT3500','normalized','elective'),
 ('7460101','V.2.2',63,'MAT3322','Xác suất 2',3,12,'MAT2308
MAT3307','normalized','elective'),
 ('7460101','V.2.2',64,'MAT3452','Phân tích thống kê nhiều chiều',3,12,'MAT2311/
MAT2406/
MAT2323','normalized','elective'),
 ('7460101','V.2.2',65,'MAT3321','Quá trình ngẫu nhiên',3,12,'MAT2311','normalized','elective'),
 ('7460101','V.2.2',66,'MAT3333','Các mô hình toán ứng dụng 1',3,12,'MAT2304
MAT2308/
MAT2405','normalized','elective'),
 ('7460101','V.2.2',67,'MAT3334','Các mô hình toán ứng dụng 2',3,13,'MAT2314
MAT2311/
MAT2406','normalized','elective'),
 ('7460101','V.2.2',68,'MAT3335','Đại số máy tính',3,13,'MAT2316/
MAT2505/
MAT2318/
MAT2319
MAT2301','normalized','elective'),
 ('7460101','V.2.2',69,'MAT3539','Mật mã và an toàn dữ liệu',3,13,'MAT2301/
MAT2400
MAT2316/
MAT2505/
MAT2318/
MAT2319','normalized','elective'),
 ('7460101','V.2.2',70,'MAT3324','Tổ hợp',3,13,'MAT3302','normalized','elective'),
 ('7460101','V.2.2',71,'MAT3345','Lý thuyết ổn định của phương trình vi phân',3,13,'MAT2314','normalized','elective'),
 ('7460101','V.2.2',72,'MAT3325','Lịch sử toán học',3,13,'MAT2304/
MAT2322
MAT2314','unlisted_prerequisite','elective'),
 ('7460101','V.2.2',73,'MAT3337','Xêmina Toán ứng dụng',3,13,'MAT2301
MAT2304','normalized','elective'),
 ('7460101','V.2.3',74,'MAT3401','Phép tính biến phân',3,13,'MAT2304
MAT2314','normalized','elective'),
 ('7460101','V.2.3',75,'MAT3361','Cơ học lý thuyết nâng cao',3,13,'MAT2304
MAT1076','normalized','elective'),
 ('7460101','V.2.3',76,'MAT3423','Cơ học môi trường liên tục',3,13,'MAT2314
MAT3402','unlisted_prerequisite','elective'),
 ('7460101','V.2.3',77,'MAT3396','Sức bền vật liệu',3,13,'MAT2314
MAT1076','normalized','elective'),
 ('7460101','V.2.3',78,'MAT3406','Lý thuyết dao động',3,13,'MAT2306
MAT3361','normalized','elective'),
 ('7460101','V.2.3',79,'MAT3407','Lý thuyết đàn hồi',3,13,'MAT2306
MAT3423','normalized','elective'),
 ('7460101','V.2.3',80,'MAT3408','Cơ học chất lỏng',3,13,'MAT2306
MAT3423','normalized','elective'),
 ('7460101','V.2.3',81,'MAT3411','Phương pháp phần tử hữu hạn',3,14,'MAT3396','normalized','elective'),
 ('7460101','V.2.3',82,'MAT3412','Lý thuyết dẻo',3,14,'MAT3407','normalized','elective'),
 ('7460101','V.2.3',83,'MAT3413','Cơ học giải tích',3,14,'MAT3361','normalized','elective'),
 ('7460101','V.2.3',84,'MAT3415','Cơ học vật liệu composite',3,14,'MAT3423','normalized','elective'),
 ('7460101','V.2.3',85,'MAT3418','Phương pháp số trong cơ học',3,14,'MAT2307
MAT2316/
MAT2505/
MAT2318/
MAT2319','normalized','elective'),
 ('7460101','V.3.1',NULL,'MAT4070','Khóa luận tốt nghiệp',7,14,NULL,'none','thesis'),
 ('7460101','V.3.2',86,'MAT4071','Một số vấn đề chọn lọc trong Toán học',3,14,NULL,'none','elective'),
 ('7460101','V.3.2',87,'MAT4072','Một số vấn đề chọn lọc trong tính toán khoa học',4,14,'MAT2307/
MAT2404
MAT2407','normalized','elective'),
 ('7460101','V.3.3',88,'MAT3362','Một số vấn đề chọn lọc trong Cơ học',3,14,'MAT3407','normalized','elective'),
 ('7460101','V.3.3',89,'MAT3422','Lý thuyết bản và vỏ mỏng',4,14,'MAT3407','normalized','elective'),
 ('7460117','I',1,'PHI1006','Triết học Mác - Lênin',3,8,NULL,'none','required'),
 ('7460117','I',2,'PEC1008','Kinh tế chính trị Mác - Lênin',2,8,'PHI1006','normalized','required'),
 ('7460117','I',3,'PHI1002','Chủ nghĩa xã hội khoa học',2,8,'PHI1006','normalized','required'),
 ('7460117','I',4,'HIS1001','Lịch sử Đảng Cộng sản Việt Nam',2,8,NULL,'none','required'),
 ('7460117','I',5,'POL1001','Tư tưởng Hồ Chí Minh',2,8,NULL,'none','required'),
 ('7460117','I',6,'THL1057','Nhà nước và pháp luật đại cương',2,8,NULL,'none','required'),
 ('7460117','I',7,'HUS1011','Tin học cơ sở',3,8,NULL,'none','required'),
 ('7460117','I',8,'FLF1107','Tiếng Anh B1',5,8,NULL,'none','elective'),
 ('7460117','I',8,'FLF1207','Tiếng Nga B1',5,8,NULL,'none','elective'),
 ('7460117','I',8,'FLF1307','Tiếng Pháp B1',5,8,NULL,'none','elective'),
 ('7460117','I',8,'FLF1407','Tiếng Trung Quốc B1',5,8,NULL,'none','elective'),
 ('7460117','I',8,'FLF1507','Tiếng Đức B1',5,8,NULL,'none','elective'),
 ('7460117','I',8,'FLF1607','Tiếng Nhật Bản B1',5,8,NULL,'none','elective'),
 ('7460117','I',8,'FLF1707','Tiếng Hàn Quốc B1',5,8,NULL,'none','elective'),
 ('7460117','I',9,'CME1000','Giáo dục quốc phòng - an ninh',8,9,NULL,'none','required'),
 ('7460117','I',10,'PES1000','Giáo dục thể chất',4,9,NULL,'none','required'),
 ('7460117','I',11,'HUS1012','Kỹ năng bổ trợ',3,9,NULL,'none','required'),
 ('7460117','II',12,'HUS1021','Khoa học Trái Đất và sự sống',3,9,NULL,'none','elective'),
 ('7460117','II',13,'HUS1022','Nhập môn Internet kết nối vạn vật',2,9,NULL,'none','elective'),
 ('7460117','II',14,'HUS1023','Nhập môn phân tích dữ liệu',2,9,NULL,'none','elective'),
 ('7460117','II',15,'HUS1024','Nhập môn Robotic',3,9,NULL,'none','elective'),
 ('7460117','II',16,'HIS1056','Cơ sở văn hóa Việt Nam',3,9,NULL,'none','elective'),
 ('7460117','III',17,'MAT2505','Lập trình cơ bản',3,9,'HUS1011','normalized','required'),
 ('7460117','IV',18,'MAT2300','Đại số tuyến tính 1',4,9,NULL,'none','required'),
 ('7460117','IV',19,'MAT2301','Đại số tuyến tính 2',4,9,'MAT2300','normalized','required'),
 ('7460117','IV',20,'MAT2302','Giải tích 1',5,9,NULL,'none','required'),
 ('7460117','IV',21,'MAT2303','Giải tích 2',5,9,'MAT2302','normalized','required'),
 ('7460117','IV',22,'MAT2304','Giải tích 3',4,9,'MAT2303','normalized','required'),
 ('7460117','IV',23,'MAT2314','Phương trình vi phân',4,9,'MAT2301/
MAT2321
MAT2303','unlisted_prerequisite','required'),
 ('7460117','IV',24,'MAT3409','Giải tích hàm ứng dụng',3,9,'MAT2301
MAT2304','normalized','required'),
 ('7460117','IV',25,'MAT2404','Giải tích số',4,10,'MAT2314
MAT2505','normalized','required'),
 ('7460117','IV',26,'MAT2405','Xác suất',3,10,'MAT2303
MAT2301','normalized','required'),
 ('7460117','IV',27,'MAT2406','Thống kê ứng dụng',4,10,'MAT2405','normalized','required'),
 ('7460117','IV',28,'MAT2407','Tối ưu hóa',3,10,'MAT2301/
MAT2321/
MAT2400
MAT2303/
MAT2502','unlisted_prerequisite','required'),
 ('7460117','IV',29,'MAT1201','Phương pháp nghiên cứu khoa học',3,10,NULL,'none','required'),
 ('7460117','V.1',30,'MAT3500','Toán rời rạc',4,10,NULL,'none','required'),
 ('7460117','V.1',31,'MAT3365','Phương trình đạo hàm riêng',3,10,'MAT2304','normalized','required'),
 ('7460117','V.1',32,'MAT1202','Lập trình hướng đối tượng',3,10,'MAT2505','normalized','required'),
 ('7460117','V.1',33,'MAT3366','Hệ máy tính',3,10,'MAT2505','normalized','required'),
 ('7460117','V.1',34,'MAT3514','Cấu trúc dữ liệu và thuật toán',4,10,'MAT2505','normalized','required'),
 ('7460117','V.1',35,'MAT3504','Thiết kế và đánh giá thuật toán',3,10,'MAT3514','normalized','required'),
 ('7460117','V.1',36,'MAT3507','Cơ sở dữ liệu',4,10,'MAT2505','normalized','required'),
 ('7460117','V.1',37,'MAT3452','Phân tích thống kê nhiều chiều',3,10,'MAT2311/
MAT2406/
MAT2323','normalized','required'),
 ('7460117','V.1',38,'MAT3525','Thực hành tính toán',2,10,'MAT2404','normalized','required'),
 ('7460117','V.1',39,'MAT3359','Thực tập chuyên ngành',3,10,'(MAT3507
MAT1202)/
MAT3304','complex_expression','required'),
 ('7460117','V.1',40,'MAT3533','Học máy',3,10,'MAT2406/
MAT2323','normalized','required'),
 ('7460117','V.2.1',41,'MAT3367','Đại số ứng dụng',3,11,NULL,'none','elective'),
 ('7460117','V.2.1',42,'MAT3545','Lý thuyết tính toán',3,11,'MAT3500
MAT3504','normalized','elective'),
 ('7460117','V.2.1',43,'MAT3539','Mật mã và an toàn dữ liệu',3,11,'MAT2301/
MAT2400
MAT2316/
MAT2505/
MAT2318/
MAT2319','normalized','elective'),
 ('7460117','V.2.1',44,'MAT3323','Tối ưu rời rạc',3,11,'MAT2407
MAT3302/
MAT3500','normalized','elective'),
 ('7460117','V.2.1',45,'MAT3509','Ngôn ngữ hình thức và ôtômat',3,11,'MAT2505
MAT3500','normalized','elective'),
 ('7460117','V.2.1',46,'MAT3456','Logic ứng dụng',3,11,'MAT2505
MAT3500','normalized','elective'),
 ('7460117','V.2.1',47,'MAT3531','Tính toán phân tán',3,11,'MAT3366
MAT1202','normalized','elective'),
 ('7460117','V.2.1',48,'MAT3508','Nhập môn trí tuệ nhân tạo',3,11,'MAT3507
MAT1202','normalized','elective'),
 ('7460117','V.2.1',49,'MAT3335','Đại số máy tính',3,11,'MAT2316/
MAT2505/
MAT2318/
MAT2319
MAT2301','normalized','elective'),
 ('7460117','V.2.1',50,'MAT3368','Thuật toán ngẫu nhiên',3,11,'MAT2405','normalized','elective'),
 ('7460117','V.2.2',51,'MAT3327','Điều khiển tối ưu',3,12,'MAT2306/
MAT2313/
MAT3365
MAT2311/
MAT2406','unlisted_prerequisite','elective'),
 ('7460117','V.2.2',52,'MAT3565','Nhập môn khai phá các tập dữ liệu lớn',3,12,'MAT1202
MAT2405','normalized','elective'),
 ('7460117','V.2.2',53,'MAT3148','Tính toán song song',3,12,'MAT3514','normalized','elective'),
 ('7460117','V.2.2',54,'MAT3561','Xử lí ngôn ngữ tự nhiên và ứng dụng',3,12,'MAT3533','normalized','elective'),
 ('7460117','V.2.2',55,'MAT3562','Thị giác máy tính',3,12,'MAT3533
MAT2301','normalized','elective'),
 ('7460117','V.2.2',56,'MAT3333','Các mô hình toán ứng dụng 1',3,12,'MAT2304
MAT2308/
MAT2405','normalized','elective'),
 ('7460117','V.2.2',57,'MAT3334','Các mô hình toán ứng dụng 2',3,12,'MAT2314
MAT2311/
MAT2406','normalized','elective'),
 ('7460117','V.2.2',58,'MAT3323','Tối ưu rời rạc',3,12,'MAT2407
MAT3302/
MAT3500','normalized','elective'),
 ('7460117','V.2.2',59,'MAT3369','Giải tích số nâng cao',3,12,'MAT2404','normalized','elective'),
 ('7460117','V.2.2',60,'MAT3370','Thống kê Bayes',3,12,'MAT2308/
MAT2405','normalized','elective'),
 ('7460117','V.3.1',61,'MAT4082','Khóa luận tốt nghiệp',7,12,NULL,'none','thesis'),
 ('7460117','V.3.2',62,'MAT4072','Một số vấn đề chọn lọc trong tính toán khoa học',4,12,'MAT2307/
MAT2404
MAT2407','normalized','elective'),
 ('7460117','V.3.2',63,'MAT3371','Xây dựng phần mềm',3,12,'MAT1202','normalized','elective'),
 ('7480113QTD','I',1,'PHI1006','Triết học Mác - Lênin',3,9,NULL,'none','required'),
 ('7480113QTD','I',2,'PEC1008','Kinh tế chính trị Mác - Lênin',2,9,'PHI1006','normalized','required'),
 ('7480113QTD','I',3,'PHI1002','Chủ nghĩa xã hội khoa học',2,9,'PHI1006','normalized','required'),
 ('7480113QTD','I',4,'HIS1001','Lịch sử Đảng Cộng sản Việt Nam',2,9,NULL,'none','required'),
 ('7480113QTD','I',5,'POL1001','Tư tưởng Hồ Chí Minh',2,9,NULL,'none','required'),
 ('7480113QTD','I',6,'THL1057','Nhà nước và pháp luật đại cương',2,9,NULL,'none','required'),
 ('7480113QTD','I',7,'HUS1011','Tin học cơ sở',3,9,NULL,'none','required'),
 ('7480113QTD','I',8,'FLF1107','Tiếng Anh B1',5,9,NULL,'none','elective'),
 ('7480113QTD','I',8,'FLF1207','Tiếng Nga B1',5,9,NULL,'none','elective'),
 ('7480113QTD','I',8,'FLF1307','Tiếng Pháp B1',5,9,NULL,'none','elective'),
 ('7480113QTD','I',8,'FLF1407','Tiếng Trung Quốc B1',5,9,NULL,'none','elective'),
 ('7480113QTD','I',8,'FLF1507','Tiếng Đức B1',5,9,NULL,'none','elective'),
 ('7480113QTD','I',8,'FLF1607','Tiếng Nhật Bản B1',5,9,NULL,'none','elective'),
 ('7480113QTD','I',8,'FLF1707','Tiếng Hàn Quốc B1',5,9,NULL,'none','elective'),
 ('7480113QTD','I',9,'CME1000','Giáo dục quốc phòng - an ninh',8,9,NULL,'none','required'),
 ('7480113QTD','I',10,'PES1000','Giáo dục thể chất',4,9,NULL,'none','required'),
 ('7480113QTD','I',11,'HUS1012','Kỹ năng bổ trợ',3,9,NULL,'none','required'),
 ('7480113QTD','II',12,'HUS1021','Khoa học Trái Đất và sự sống',3,10,NULL,'none','elective'),
 ('7480113QTD','II',13,'HUS1022','Nhập môn Internet kết nối vạn vật',2,10,NULL,'none','elective'),
 ('7480113QTD','II',14,'HUS1023','Nhập môn phân tích dữ liệu',2,10,NULL,'none','elective'),
 ('7480113QTD','II',15,'HUS1024','Nhập môn Robotic',3,10,NULL,'none','elective'),
 ('7480113QTD','II',16,'HIS1056','Cơ sở văn hóa Việt Nam',3,10,NULL,'none','elective'),
 ('7480113QTD','III',17,'MAT2505','Lập trình cơ bản',3,10,'HUS1011','normalized','required'),
 ('7480113QTD','IV',18,'MAT2400','Đại số tuyến tính',5,10,NULL,'none','required'),
 ('7480113QTD','IV',19,'MAT2501','Giải tích 1',4,10,NULL,'none','required'),
 ('7480113QTD','IV',20,'MAT2502','Giải tích 2',4,10,'MAT2501','normalized','required'),
 ('7480113QTD','IV',21,'MAT2503','Giải tích 3',2,10,'MAT2502','normalized','required'),
 ('7480113QTD','IV',22,'MAT2403','Phương trình vi phân',3,10,'MAT2400
MAT2501','normalized','required'),
 ('7480113QTD','IV',23,'MAT2323','Xác suất - Thống kê',4,10,'MAT2502','normalized','required'),
 ('7480113QTD','IV',24,'MAT2407','Tối ưu hóa',3,10,'MAT2301/
MAT2321/
MAT2400
MAT2303/
MAT2502','unlisted_prerequisite','required'),
 ('7480113QTD','IV',25,'MAT1204','Phương pháp nghiên cứu khoa học',3,10,'MAT3507
MAT3514','normalized','required'),
 ('7480113QTD','V.1',26,'MAT1205E','Tiếng Anh chuyên ngành khoa học máy tính',2,10,'FLF1107','normalized','required'),
 ('7480113QTD','V.1',27,'MAT3500','Toán rời rạc',4,11,NULL,'none','required'),
 ('7480113QTD','V.1',28,'MAT3557','Môi trường lập trình Linux',2,11,NULL,'none','required'),
 ('7480113QTD','V.1',29,'MAT3550E','Nguyên lí hệ điều hành',3,11,'MAT2505','normalized','required'),
 ('7480113QTD','V.1',30,'MAT3507','Cơ sở dữ liệu',4,11,'MAT2505','normalized','required'),
 ('7480113QTD','V.1',31,'MAT1202','Lập trình hướng đối tượng',3,11,'MAT2505','normalized','required'),
 ('7480113QTD','V.1',32,'MAT3514','Cấu trúc dữ liệu và thuật toán',4,11,'MAT2505','normalized','required'),
 ('7480113QTD','V.1',33,'MAT3552E','Thiết kế và đánh giá thuật toán',3,11,'MAT3514','normalized','required'),
 ('7480113QTD','V.1',34,'MAT3505','Kiến trúc máy tính',3,11,'MAT2505
MAT3557','normalized','required'),
 ('7480113QTD','V.1',35,'MAT3373E','Nhập môn an toàn máy tính',3,11,'MAT2505','normalized','required'),
 ('7480113QTD','V.1',36,'MAT3506','Mạng máy tính',3,11,'MAT2505','normalized','required'),
 ('7480113QTD','V.1',37,'MAT1206E','Nhập môn Trí tuệ nhân tạo',3,11,'MAT3507
MAT1202','normalized','required'),
 ('7480113QTD','V.1',38,'MAT3374','Thực tập thực tế phát triển phần mềm',3,11,'MAT1202
MAT3507','normalized','required'),
 ('7480113QTD','V.1',39,'MAT1207','Công nghệ phần mềm',3,11,'MAT3374','normalized','required'),
 ('7480113QTD','V.1',40,'MAT3541E','Nguyên lí các ngôn ngữ lập trình',3,11,'MAT1202','normalized','required'),
 ('7480113QTD','V.1',41,'MAT3533','Học máy',3,11,'MAT2406/
MAT2323','normalized','required'),
 ('7480113QTD','V.2.1',42,'MAT3519','Ngôn ngữ lập trình thứ hai',2,11,'MAT2505','normalized','elective'),
 ('7480113QTD','V.2.1',43,'MAT3558','Lập trình mobile',2,11,'MAT2505','normalized','elective'),
 ('7480113QTD','V.2.1',44,'MAT1208','Xây dựng hệ thống nhúng',2,12,'MAT1202
MAT3505','normalized','elective'),
 ('7480113QTD','V.2.1',45,'MAT3560','Phát triển phần mềm trò chơi',2,12,'MAT2505','normalized','elective'),
 ('7480113QTD','V.2.2',46,'MAT3148','Tính toán song song',3,12,'MAT3514','normalized','elective'),
 ('7480113QTD','V.2.2',47,'MAT3554E','Ngôn ngữ hình thức và ôtômat',3,12,'MAT2505
MAT3500','normalized','elective'),
 ('7480113QTD','V.2.2',48,'MAT3562E','Thị giác máy tính',3,12,'MAT3533
MAT2400','normalized','elective'),
 ('7480113QTD','V.2.2',49,'MAT3561E','Xử lí ngôn ngữ tự nhiên và ứng dụng',3,12,'MAT3533','normalized','elective'),
 ('7480113QTD','V.2.2',50,'MAT3563','Một số vấn đề chọn lọc về thị giác máy tính',3,12,'MAT3562E','normalized','elective'),
 ('7480113QTD','V.2.2',51,'MAT3534','Khai phá dữ liệu',3,12,'MAT3507
MAT2323','normalized','elective'),
 ('7480113QTD','V.2.2',52,'MAT3542','Phát triển ứng dụng web',3,12,'MAT1202
MAT3507','normalized','elective'),
 ('7480113QTD','V.2.2',53,'MAT3539','Mật mã và an toàn dữ liệu',3,12,'MAT2301/
MAT2400
MAT2316/
MAT2505/
MAT2318/
MAT2319','normalized','elective'),
 ('7480113QTD','V.2.2',54,'MAT3452','Phân tích thống kê nhiều chiều',3,12,'MAT2311/
MAT2406/
MAT2323','normalized','elective'),
 ('7480113QTD','V.2.2',55,'MAT3453','Phương pháp chọn mẫu dữ liệu',3,12,'MAT2323','normalized','elective'),
 ('7480113QTD','V.2.2',56,'MAT2034','Giải tích số',3,12,'MAT2502
MAT2403','normalized','elective'),
 ('7480113QTD','V.2.2',57,'MAT3538','Các hệ thống tri thức',3,12,'MAT1206E
MAT3514','normalized','elective'),
 ('7480113QTD','V.2.2',58,'MAT3535','Tìm kiếm thông tin',3,12,'MAT3514
MAT2323','normalized','elective'),
 ('7480113QTD','V.3.1',59,'MAT4080','Khóa luận tốt nghiệp',7,13,NULL,'none','thesis'),
 ('7480113QTD','V.3.2',60,'MAT1203','Phân tích và thiết kế hệ thống thông tin',4,13,'MAT3374
MAT3552E
MAT1207','normalized','elective'),
 ('7480113QTD','V.3.2',61,'MAT3377','Một số vấn đề chọn lọc về Trí tuệ nhân tạo',3,13,'MAT1206E','normalized','elective'),
 ('7460108','I',1,'PHI1006','Triết học Mác - Lênin',3,9,NULL,'none','required'),
 ('7460108','I',2,'PEC1008','Kinh tế chính trị Mác - Lênin',2,9,'PHI1006','normalized','required'),
 ('7460108','I',3,'PHI1002','Chủ nghĩa xã hội khoa học',2,9,'PHI1006','normalized','required'),
 ('7460108','I',4,'HIS1001','Lịch sử Đảng Cộng sản Việt Nam',2,9,NULL,'none','required'),
 ('7460108','I',5,'POL1001','Tư tưởng Hồ Chí Minh',2,9,NULL,'none','required'),
 ('7460108','I',6,'THL1057','Nhà nước và pháp luật đại cương',2,9,NULL,'none','required'),
 ('7460108','I',7,'HUS1011','Tin học cơ sở',3,9,NULL,'none','required'),
 ('7460108','I',8,'FLF1107','Tiếng Anh B1',5,9,NULL,'none','elective'),
 ('7460108','I',8,'FLF1207','Tiếng Nga B1',5,9,NULL,'none','elective'),
 ('7460108','I',8,'FLF1307','Tiếng Pháp B1',5,9,NULL,'none','elective'),
 ('7460108','I',8,'FLF1407','Tiếng Trung Quốc B1',5,9,NULL,'none','elective'),
 ('7460108','I',8,'FLF1507','Tiếng Đức B1',5,9,NULL,'none','elective'),
 ('7460108','I',8,'FLF1607','Tiếng Nhật Bản B1',5,9,NULL,'none','elective'),
 ('7460108','I',8,'FLF1707','Tiếng Hàn Quốc B1',5,9,NULL,'none','elective'),
 ('7460108','I',9,'CME1000','Giáo dục quốc phòng - an ninh',8,9,NULL,'none','required'),
 ('7460108','I',10,'PES1000','Giáo dục thể chất',4,9,NULL,'none','required'),
 ('7460108','I',11,'HUS1012','Kỹ năng bổ trợ',3,9,NULL,'none','required'),
 ('7460108','II',12,'HUS1021','Khoa học Trái Đất và sự sống',3,10,NULL,'none','elective'),
 ('7460108','II',13,'HUS1022','Nhập môn Internet kết nối vạn vật',2,10,NULL,'none','elective'),
 ('7460108','II',14,'HUS1023','Nhập môn phân tích dữ liệu',2,10,NULL,'none','elective'),
 ('7460108','II',15,'HUS1024','Nhập môn Robotic',3,10,NULL,'none','elective'),
 ('7460108','II',16,'HIS1056','Cơ sở văn hóa Việt Nam',3,10,NULL,'none','elective'),
 ('7460108','III',17,'MAT2505','Lập trình cơ bản',3,10,'HUS1011','normalized','required'),
 ('7460108','IV',18,'MAT2400','Đại số tuyến tính',5,10,NULL,'none','required'),
 ('7460108','IV',19,'MAT2501','Giải tích 1',4,10,NULL,'none','required'),
 ('7460108','IV',20,'MAT2502','Giải tích 2',4,10,'MAT2501','normalized','required'),
 ('7460108','IV',21,'MAT2503','Giải tích 3',2,10,'MAT2502','normalized','required'),
 ('7460108','IV',22,'MAT2403','Phương trình vi phân',3,10,'MAT2400
MAT2501','normalized','required'),
 ('7460108','IV',23,'MAT2323','Xác suất - Thống kê',4,10,'MAT2502','normalized','required'),
 ('7460108','IV',24,'MAT2407','Tối ưu hóa',3,10,'MAT2301/
MAT2321/
MAT2400
MAT2303/
MAT2502','unlisted_prerequisite','required'),
 ('7460108','IV',25,'MAT1204','Phương pháp nghiên cứu khoa học',3,10,'MAT3507
MAT3514','normalized','required'),
 ('7460108','V.1',26,'MAT2034','Giải tích số',3,11,'MAT2502
MAT2403','normalized','required'),
 ('7460108','V.1',27,'MAT3500','Toán rời rạc',4,11,NULL,'none','required'),
 ('7460108','V.1',28,'MAT3557','Môi trường lập trình Linux',2,11,NULL,'none','required'),
 ('7460108','V.1',29,'MAT1202','Lập trình hướng đối tượng',3,11,'MAT2505','normalized','required'),
 ('7460108','V.1',30,'MAT3514','Cấu trúc dữ liệu và thuật toán',4,11,'MAT2505','normalized','required'),
 ('7460108','V.1',31,'MAT3507','Cơ sở dữ liệu',4,11,'MAT2505','normalized','required'),
 ('7460108','V.1',32,'MAT3378','Quản trị dữ liệu lớn',3,11,'MAT3507
MAT1202','normalized','required'),
 ('7460108','V.1',33,'MAT3148','Tính toán song song',3,11,'MAT3514','normalized','required'),
 ('7460108','V.1',34,'MAT3379','Phân tích hồi quy và ứng dụng',3,11,'MAT2323
MAT2400
MAT2505','normalized','required'),
 ('7460108','V.1',35,'MAT3533','Học máy',3,11,'MAT2406/
MAT2323','normalized','required'),
 ('7460108','V.1',36,'MAT3381','Thực tập thực tế về Khoa học dữ liệu',3,11,'MAT1202
MAT3507
MAT3378','normalized','required'),
 ('7460108','V.2.1',37,'MAT3382','Lập trình cho Khoa học dữ liệu',2,11,'MAT3514','normalized','elective'),
 ('7460108','V.2.1',38,'MAT3383','Trực quan hóa thông tin',2,11,NULL,'none','elective'),
 ('7460108','V.2.1',39,'MAT1209','Tự động hóa',2,11,'MAT3533','normalized','elective'),
 ('7460108','V.2.2',40,'MAT3385','Cơ sở dữ liệu Web và hệ thống thông tin',3,11,'MAT1202
MAT3507','normalized','elective'),
 ('7460108','V.2.2',41,'MAT3504','Thiết kế và đánh giá thuật toán',3,11,'MAT3514','normalized','elective'),
 ('7460108','V.2.2',42,'MAT3508','Nhập môn trí tuệ nhân tạo',3,11,'MAT3507
MAT1202','normalized','elective'),
 ('7460108','V.2.3',43,'MAT3534','Khai phá dữ liệu',3,12,'MAT3507
MAT2323','normalized','elective'),
 ('7460108','V.2.3',44,'MAT3386','Phương pháp tính toán trong thống kê và khoa học dữ liệu',3,12,'MAT2323','normalized','elective'),
 ('7460108','V.2.3',45,'MAT3387','Kĩ thuật lấy mẫu khảo sát',3,12,'MAT2323','normalized','elective'),
 ('7460108','V.2.3',46,'MAT3388','Phân tích chuỗi thời gian',3,12,'MAT2323','normalized','elective'),
 ('7460108','V.2.3',47,'MAT3389','Quy hoạch thực nghiệm',3,12,'MAT2323','normalized','elective'),
 ('7460108','V.2.4',48,'MAT3390','Nhập môn Tin sinh học',3,12,'MAT2505
MAT3514','normalized','elective'),
 ('7460108','V.2.4',49,'MAT3391','Hệ thống thông tin địa lí',3,12,'MAT3507','normalized','elective'),
 ('7460108','V.2.4',50,'MAT3392','Ứng dụng dữ liệu lớn trong quản lí rủi ro tai biến thiên nhiên',3,12,'MAT3507
MAT2323','normalized','elective'),
 ('7460108','V.2.4',51,'MAT3393','Khai thác dữ liệu trong Hóa học',3,12,'MAT3533','normalized','elective'),
 ('7460108','V.2.4',52,'MAT3394','Mô hình toán sinh thái',3,12,'MAT2403','normalized','elective'),
 ('7460108','V.2.4',53,'MAT3562','Thị giác máy tính',3,12,'MAT2301/
MAT2400
MAT3533','normalized','elective'),
 ('7460108','V.2.4',54,'MAT3395','Lí thuyết trò chơi',3,12,'MAT2323','normalized','elective'),
 ('7460108','V.2.4',55,'MAT3535','Tìm kiếm thông tin',3,12,'MAT3514
MAT2323','normalized','elective'),
 ('7460108','V.2.4',56,'MAT3399','Xử lí ngôn ngữ tự nhiên và học sâu',3,12,'MAT3533','normalized','elective'),
 ('7460108','V.3.1',57,'MAT4083','Khóa luận tốt nghiệp',7,13,NULL,'none','thesis'),
 ('7460108','V.3.2',58,'MAT3397','Một số vấn đề ứng dụng của khoa học dữ liệu',4,13,'MAT3533','normalized','elective'),
 ('7460108','V.3.2',59,'MAT3398','Một số chủ đề trong mô hình hóa và phân tích dữ liệu',3,13,'MAT3533','normalized','elective')
;
-- Elective credit limits must be respected by the recommender; NOT all listed electives are required.
CREATE TEMP TABLE _group_def (major_code TEXT,group_key TEXT,group_title TEXT,
 min_credits SMALLINT,offered_credits SMALLINT,source_heading TEXT,group_note TEXT)
 ON COMMIT DROP;
INSERT INTO _group_def VALUES
 ('7460101','I','Kiến thức chung; ngoại ngữ B1 chọn 1/7, GDTC và GDQP-AN không tính vào tổng tín chỉ',21,NULL,'I','Kiến thức chung; ngoại ngữ B1 chọn 1/7, GDTC và GDQP-AN không tính vào tổng tín chỉ; CME1000, PES1000, HUS1012 không tính vào tổng tín chỉ chương trình; ngoại ngữ chọn một mã FLF.'),
 ('7460101','II','Kiến thức theo lĩnh vực',5,13,'II','Kiến thức theo lĩnh vực'),
 ('7460101','III','Kiến thức theo khối ngành',3,3,'III','Kiến thức theo khối ngành'),
 ('7460101','IV.1','Kiến thức nhóm ngành bắt buộc',48,48,'IV.1','Kiến thức nhóm ngành bắt buộc'),
 ('7460101','IV.2','Nhóm ngành tự chọn; chọn 1 trong 4 học phần lập trình',3,12,'IV.2','Nhóm ngành tự chọn; chọn 1 trong 4 học phần lập trình'),
 ('7460101','V.1','Kiến thức ngành bắt buộc',33,33,'V.1','Kiến thức ngành bắt buộc'),
 ('7460101','V.2.1','Định hướng Toán lý thuyết',15,39,'V.2.1','Định hướng Toán lý thuyết; Chọn MỘT trong ba định hướng V.2.1/V.2.2/V.2.3, không phải cả ba.'),
 ('7460101','V.2.2','Định hướng Toán ứng dụng',15,48,'V.2.2','Định hướng Toán ứng dụng; Chọn MỘT trong ba định hướng V.2.1/V.2.2/V.2.3, không phải cả ba.'),
 ('7460101','V.2.3','Định hướng Cơ học',15,36,'V.2.3','Định hướng Cơ học; Chọn MỘT trong ba định hướng V.2.1/V.2.2/V.2.3, không phải cả ba.'),
 ('7460101','V.3.1','Khóa luận tốt nghiệp',7,7,'V.3.1','Khóa luận tốt nghiệp; Chỉ chọn một phương án hoàn thành khóa luận/thay thế phù hợp.'),
 ('7460101','V.3.2','Hai học phần thay thế khóa luận định hướng Toán',7,7,'V.3.2','Hai học phần thay thế khóa luận định hướng Toán; Chỉ chọn một phương án hoàn thành khóa luận/thay thế phù hợp.'),
 ('7460101','V.3.3','Hai học phần thay thế khóa luận định hướng Cơ học',7,7,'V.3.3','Hai học phần thay thế khóa luận định hướng Cơ học; Chỉ chọn một phương án hoàn thành khóa luận/thay thế phù hợp.'),
 ('7460117','I','Kiến thức chung; ngoại ngữ B1 chọn 1/7, GDTC và GDQP-AN không tính vào tổng tín chỉ',21,NULL,'I','Kiến thức chung; ngoại ngữ B1 chọn 1/7, GDTC và GDQP-AN không tính vào tổng tín chỉ; CME1000, PES1000, HUS1012 không tính vào tổng tín chỉ chương trình; ngoại ngữ chọn một mã FLF.'),
 ('7460117','II','Kiến thức theo lĩnh vực',5,13,'II','Kiến thức theo lĩnh vực'),
 ('7460117','III','Kiến thức theo khối ngành',3,3,'III','Kiến thức theo khối ngành'),
 ('7460117','IV','Kiến thức theo nhóm ngành bắt buộc',46,46,'IV','Kiến thức theo nhóm ngành bắt buộc'),
 ('7460117','V.1','Kiến thức ngành bắt buộc',35,35,'V.1','Kiến thức ngành bắt buộc'),
 ('7460117','V.2.1','Học phần tự chọn định hướng Tin học',15,30,'V.2.1','Học phần tự chọn định hướng Tin học; Chọn MỘT trong hai định hướng V.2.1/V.2.2; tổng khối V.2 chỉ 15 tín chỉ.'),
 ('7460117','V.2.2','Học phần tự chọn chuyên sâu và bổ trợ định hướng Tin học',15,30,'V.2.2','Học phần tự chọn chuyên sâu và bổ trợ định hướng Tin học; Chọn MỘT trong hai định hướng V.2.1/V.2.2; tổng khối V.2 chỉ 15 tín chỉ.'),
 ('7460117','V.3.1','Khóa luận tốt nghiệp',7,7,'V.3.1','Khóa luận tốt nghiệp; Chỉ chọn một phương án hoàn thành khóa luận/thay thế phù hợp.'),
 ('7460117','V.3.2','Hai học phần thay thế khóa luận',7,7,'V.3.2','Hai học phần thay thế khóa luận; Chỉ chọn một phương án hoàn thành khóa luận/thay thế phù hợp.'),
 ('7480113QTD','I','Kiến thức chung; ngoại ngữ B1 chọn 1/7, GDTC và GDQP-AN không tính vào tổng tín chỉ',21,NULL,'I','Kiến thức chung; ngoại ngữ B1 chọn 1/7, GDTC và GDQP-AN không tính vào tổng tín chỉ; CME1000, PES1000, HUS1012 không tính vào tổng tín chỉ chương trình; ngoại ngữ chọn một mã FLF.'),
 ('7480113QTD','II','Kiến thức theo lĩnh vực',5,13,'II','Kiến thức theo lĩnh vực'),
 ('7480113QTD','III','Kiến thức theo khối ngành',3,3,'III','Kiến thức theo khối ngành'),
 ('7480113QTD','IV','Kiến thức theo nhóm ngành bắt buộc',28,28,'IV','Kiến thức theo nhóm ngành bắt buộc'),
 ('7480113QTD','V.1','Kiến thức ngành bắt buộc',49,49,'V.1','Kiến thức ngành bắt buộc'),
 ('7480113QTD','V.2.1','Tự chọn về kĩ năng phần mềm',4,8,'V.2.1','Tự chọn về kĩ năng phần mềm'),
 ('7480113QTD','V.2.2','Tự chọn về trí tuệ nhân tạo và phát triển phần mềm',12,39,'V.2.2','Tự chọn về trí tuệ nhân tạo và phát triển phần mềm'),
 ('7480113QTD','V.3.1','Khóa luận tốt nghiệp',7,7,'V.3.1','Khóa luận tốt nghiệp; Chỉ chọn một phương án hoàn thành khóa luận/thay thế phù hợp.'),
 ('7480113QTD','V.3.2','Các học phần thay thế khóa luận',7,7,'V.3.2','Các học phần thay thế khóa luận; Chỉ chọn một phương án hoàn thành khóa luận/thay thế phù hợp.'),
 ('7460108','I','Kiến thức chung; ngoại ngữ B1 chọn 1/7, GDTC và GDQP-AN không tính vào tổng tín chỉ',21,NULL,'I','Kiến thức chung; ngoại ngữ B1 chọn 1/7, GDTC và GDQP-AN không tính vào tổng tín chỉ; CME1000, PES1000, HUS1012 không tính vào tổng tín chỉ chương trình; ngoại ngữ chọn một mã FLF.'),
 ('7460108','II','Kiến thức theo lĩnh vực',5,13,'II','Kiến thức theo lĩnh vực'),
 ('7460108','III','Kiến thức theo khối ngành',3,3,'III','Kiến thức theo khối ngành'),
 ('7460108','IV','Kiến thức theo nhóm ngành bắt buộc',28,28,'IV','Kiến thức theo nhóm ngành bắt buộc'),
 ('7460108','V.1','Kiến thức ngành bắt buộc',35,35,'V.1','Kiến thức ngành bắt buộc'),
 ('7460108','V.2.1','Tự chọn về kĩ năng phần mềm',4,6,'V.2.1','Tự chọn về kĩ năng phần mềm'),
 ('7460108','V.2.2','Tự chọn về Khoa học máy tính',6,9,'V.2.2','Tự chọn về Khoa học máy tính'),
 ('7460108','V.2.3','Tự chọn về Thống kê và Khai phá dữ liệu',9,15,'V.2.3','Tự chọn về Thống kê và Khai phá dữ liệu'),
 ('7460108','V.2.4','Tự chọn về ứng dụng Khoa học dữ liệu',9,27,'V.2.3','Tự chọn về ứng dụng Khoa học dữ liệu; Trong bản scan, tiêu đề này được in lặp V.2.3. Dùng V.2.4 làm mã nội bộ để không đụng tên.'),
 ('7460108','V.3.1','Khóa luận tốt nghiệp',7,7,'V.3.1','Khóa luận tốt nghiệp; Chỉ chọn một phương án hoàn thành khóa luận/thay thế phù hợp.'),
 ('7460108','V.3.2','Các học phần thay thế khóa luận',7,7,'V.3.2','Các học phần thay thế khóa luận; Chỉ chọn một phương án hoàn thành khóa luận/thay thế phù hợp.');
INSERT INTO public.official_curriculum_groups
 (curriculum_id,group_key,group_title,min_credits_if_selected,offered_credits,source_heading,group_note)
 SELECT nc.curriculum_id,g.group_key,g.group_title,g.min_credits,g.offered_credits,g.source_heading,g.group_note
 FROM _group_def g JOIN _new_curricula nc USING(major_code);

-- One course can appear in multiple elective tracks. Preserve EVERY official occurrence in
-- official_curriculum_entries; de-duplicate only for legacy curriculum_courses PK.
INSERT INTO public.curriculum_courses(curriculum_id,course_code,course_type,course_group)
SELECT DISTINCT ON (nc.curriculum_id,r.course_code) nc.curriculum_id,r.course_code,r.course_type,r.group_key
FROM _official_rows r JOIN _new_curricula nc USING(major_code)
ORDER BY nc.curriculum_id,r.course_code,r.group_key;

INSERT INTO public.official_curriculum_entries
 (curriculum_id,group_key,source_row_number,course_code,credits_in_source,
  prerequisite_source_text,prerequisite_parse_status,pdf_document,pdf_page)
SELECT nc.curriculum_id,r.group_key,r.source_row_number,r.course_code,r.credits_in_source,
       r.prerequisite_source_text,r.prerequisite_parse_status,
       CASE nc.major_code

        WHEN '7460101' THEN '101. Toán học-chuẩn final QD 3565 Scan.pdf'
        WHEN '7460117' THEN '103. Toán tin-chuẩn final QD 3567 Scan.pdf'
        WHEN '7480113QTD' THEN '104.-KHMTTT-chuẩn final QD 3568 Scan final.pdf'
        WHEN '7460108' THEN '105.-Khoa-học-dữ-liệu-chuẩn final QĐ 3569 Scan.pdf'
       END,r.pdf_page
FROM _official_rows r JOIN _new_curricula nc USING(major_code);

-- Only prerequisites with an unambiguous expression AND known catalog course codes
-- are normalized. Full raw cells (including unlisted prerequisite codes) are retained above.
INSERT INTO public.course_prerequisites(curriculum_id,course_code,group_no,prerequisite_course_code)
SELECT nc.curriculum_id,p.course_code,p.group_no,p.prerequisite_code
FROM (VALUES
  ('7460101','MAT1076',1,'MAT2302'),
  ('7460101','MAT2301',1,'MAT2300'),
  ('7460101','MAT2303',1,'MAT2302'),
  ('7460101','MAT2304',1,'MAT2303'),
  ('7460101','MAT2306',1,'MAT2304'),
  ('7460101','MAT2306',2,'MAT2314'),
  ('7460101','MAT2307',1,'MAT2314'),
  ('7460101','MAT2307',2,'MAT2316'),
  ('7460101','MAT2307',2,'MAT2318'),
  ('7460101','MAT2307',2,'MAT2319'),
  ('7460101','MAT2307',2,'MAT2505'),
  ('7460101','MAT2311',1,'MAT2308'),
  ('7460101','MAT2316',1,'HUS1011'),
  ('7460101','MAT2318',1,'HUS1011'),
  ('7460101','MAT2319',1,'HUS1011'),
  ('7460101','MAT2505',1,'HUS1011'),
  ('7460101','MAT3301',1,'MAT2301'),
  ('7460101','MAT3301',2,'MAT2304'),
  ('7460101','MAT3304',1,'MAT2307'),
  ('7460101','MAT3305',1,'MAT2302'),
  ('7460101','MAT3310',1,'MAT3300'),
  ('7460101','MAT3310',2,'MAT3305'),
  ('7460101','MAT3311',1,'MAT3300'),
  ('7460101','MAT3318',1,'MAT3339'),
  ('7460101','MAT3318',2,'MAT3305'),
  ('7460101','MAT3321',1,'MAT2311'),
  ('7460101','MAT3322',1,'MAT2308'),
  ('7460101','MAT3322',2,'MAT3307'),
  ('7460101','MAT3323',1,'MAT2407'),
  ('7460101','MAT3323',2,'MAT3302'),
  ('7460101','MAT3323',2,'MAT3500'),
  ('7460101','MAT3324',1,'MAT3302'),
  ('7460101','MAT3325',1,'MAT2314'),
  ('7460101','MAT3325',2,'MAT2304'),
  ('7460101','MAT3326',1,'MAT2308'),
  ('7460101','MAT3329',1,'MAT2307'),
  ('7460101','MAT3333',1,'MAT2304'),
  ('7460101','MAT3333',2,'MAT2308'),
  ('7460101','MAT3333',2,'MAT2405'),
  ('7460101','MAT3334',1,'MAT2314'),
  ('7460101','MAT3334',2,'MAT2311'),
  ('7460101','MAT3334',2,'MAT2406'),
  ('7460101','MAT3335',1,'MAT2316'),
  ('7460101','MAT3335',1,'MAT2318'),
  ('7460101','MAT3335',1,'MAT2319'),
  ('7460101','MAT3335',1,'MAT2505'),
  ('7460101','MAT3335',2,'MAT2301'),
  ('7460101','MAT3337',1,'MAT2301'),
  ('7460101','MAT3337',2,'MAT2304'),
  ('7460101','MAT3345',1,'MAT2314'),
  ('7460101','MAT3347',1,'MAT3300'),
  ('7460101','MAT3360',1,'MAT2407'),
  ('7460101','MAT3361',1,'MAT2304'),
  ('7460101','MAT3361',2,'MAT1076'),
  ('7460101','MAT3362',1,'MAT3407'),
  ('7460101','MAT3370',1,'MAT2308'),
  ('7460101','MAT3370',1,'MAT2405'),
  ('7460101','MAT3396',1,'MAT2314'),
  ('7460101','MAT3396',2,'MAT1076'),
  ('7460101','MAT3401',1,'MAT2304'),
  ('7460101','MAT3401',2,'MAT2314'),
  ('7460101','MAT3406',1,'MAT2306'),
  ('7460101','MAT3406',2,'MAT3361'),
  ('7460101','MAT3407',1,'MAT2306'),
  ('7460101','MAT3407',2,'MAT3423'),
  ('7460101','MAT3408',1,'MAT2306'),
  ('7460101','MAT3408',2,'MAT3423'),
  ('7460101','MAT3411',1,'MAT3396'),
  ('7460101','MAT3412',1,'MAT3407'),
  ('7460101','MAT3413',1,'MAT3361'),
  ('7460101','MAT3415',1,'MAT3423'),
  ('7460101','MAT3418',1,'MAT2307'),
  ('7460101','MAT3418',2,'MAT2316'),
  ('7460101','MAT3418',2,'MAT2318'),
  ('7460101','MAT3418',2,'MAT2319'),
  ('7460101','MAT3418',2,'MAT2505'),
  ('7460101','MAT3422',1,'MAT3407'),
  ('7460101','MAT3452',1,'MAT2311'),
  ('7460101','MAT3452',1,'MAT2323'),
  ('7460101','MAT3452',1,'MAT2406'),
  ('7460101','MAT3539',1,'MAT2301'),
  ('7460101','MAT3539',1,'MAT2400'),
  ('7460101','MAT3539',2,'MAT2316'),
  ('7460101','MAT3539',2,'MAT2318'),
  ('7460101','MAT3539',2,'MAT2319'),
  ('7460101','MAT3539',2,'MAT2505'),
  ('7460101','MAT4072',1,'MAT2307'),
  ('7460101','MAT4072',1,'MAT2404'),
  ('7460101','MAT4072',2,'MAT2407'),
  ('7460101','PEC1008',1,'PHI1006'),
  ('7460101','PHI1002',1,'PHI1006'),
  ('7460108','MAT1202',1,'MAT2505'),
  ('7460108','MAT1204',1,'MAT3507'),
  ('7460108','MAT1204',2,'MAT3514'),
  ('7460108','MAT1209',1,'MAT3533'),
  ('7460108','MAT2034',1,'MAT2502'),
  ('7460108','MAT2034',2,'MAT2403'),
  ('7460108','MAT2323',1,'MAT2502'),
  ('7460108','MAT2403',1,'MAT2400'),
  ('7460108','MAT2403',2,'MAT2501'),
  ('7460108','MAT2502',1,'MAT2501'),
  ('7460108','MAT2503',1,'MAT2502'),
  ('7460108','MAT2505',1,'HUS1011'),
  ('7460108','MAT3148',1,'MAT3514'),
  ('7460108','MAT3378',1,'MAT3507'),
  ('7460108','MAT3378',2,'MAT1202'),
  ('7460108','MAT3379',1,'MAT2323'),
  ('7460108','MAT3379',2,'MAT2400'),
  ('7460108','MAT3379',3,'MAT2505'),
  ('7460108','MAT3381',1,'MAT1202'),
  ('7460108','MAT3381',2,'MAT3507'),
  ('7460108','MAT3381',3,'MAT3378'),
  ('7460108','MAT3382',1,'MAT3514'),
  ('7460108','MAT3385',1,'MAT1202'),
  ('7460108','MAT3385',2,'MAT3507'),
  ('7460108','MAT3386',1,'MAT2323'),
  ('7460108','MAT3387',1,'MAT2323'),
  ('7460108','MAT3388',1,'MAT2323'),
  ('7460108','MAT3389',1,'MAT2323'),
  ('7460108','MAT3390',1,'MAT2505'),
  ('7460108','MAT3390',2,'MAT3514'),
  ('7460108','MAT3391',1,'MAT3507'),
  ('7460108','MAT3392',1,'MAT3507'),
  ('7460108','MAT3392',2,'MAT2323'),
  ('7460108','MAT3393',1,'MAT3533'),
  ('7460108','MAT3394',1,'MAT2403'),
  ('7460108','MAT3395',1,'MAT2323'),
  ('7460108','MAT3397',1,'MAT3533'),
  ('7460108','MAT3398',1,'MAT3533'),
  ('7460108','MAT3399',1,'MAT3533'),
  ('7460108','MAT3504',1,'MAT3514'),
  ('7460108','MAT3507',1,'MAT2505'),
  ('7460108','MAT3508',1,'MAT3507'),
  ('7460108','MAT3508',2,'MAT1202'),
  ('7460108','MAT3514',1,'MAT2505'),
  ('7460108','MAT3533',1,'MAT2323'),
  ('7460108','MAT3533',1,'MAT2406'),
  ('7460108','MAT3534',1,'MAT3507'),
  ('7460108','MAT3534',2,'MAT2323'),
  ('7460108','MAT3535',1,'MAT3514'),
  ('7460108','MAT3535',2,'MAT2323'),
  ('7460108','MAT3562',1,'MAT2301'),
  ('7460108','MAT3562',1,'MAT2400'),
  ('7460108','MAT3562',2,'MAT3533'),
  ('7460108','PEC1008',1,'PHI1006'),
  ('7460108','PHI1002',1,'PHI1006'),
  ('7460117','MAT1202',1,'MAT2505'),
  ('7460117','MAT2301',1,'MAT2300'),
  ('7460117','MAT2303',1,'MAT2302'),
  ('7460117','MAT2304',1,'MAT2303'),
  ('7460117','MAT2404',1,'MAT2314'),
  ('7460117','MAT2404',2,'MAT2505'),
  ('7460117','MAT2405',1,'MAT2303'),
  ('7460117','MAT2405',2,'MAT2301'),
  ('7460117','MAT2406',1,'MAT2405'),
  ('7460117','MAT2505',1,'HUS1011'),
  ('7460117','MAT3148',1,'MAT3514'),
  ('7460117','MAT3323',1,'MAT2407'),
  ('7460117','MAT3323',2,'MAT3302'),
  ('7460117','MAT3323',2,'MAT3500'),
  ('7460117','MAT3333',1,'MAT2304'),
  ('7460117','MAT3333',2,'MAT2308'),
  ('7460117','MAT3333',2,'MAT2405'),
  ('7460117','MAT3334',1,'MAT2314'),
  ('7460117','MAT3334',2,'MAT2311'),
  ('7460117','MAT3334',2,'MAT2406'),
  ('7460117','MAT3335',1,'MAT2316'),
  ('7460117','MAT3335',1,'MAT2318'),
  ('7460117','MAT3335',1,'MAT2319'),
  ('7460117','MAT3335',1,'MAT2505'),
  ('7460117','MAT3335',2,'MAT2301'),
  ('7460117','MAT3365',1,'MAT2304'),
  ('7460117','MAT3366',1,'MAT2505'),
  ('7460117','MAT3368',1,'MAT2405'),
  ('7460117','MAT3369',1,'MAT2404'),
  ('7460117','MAT3370',1,'MAT2308'),
  ('7460117','MAT3370',1,'MAT2405'),
  ('7460117','MAT3371',1,'MAT1202'),
  ('7460117','MAT3409',1,'MAT2301'),
  ('7460117','MAT3409',2,'MAT2304'),
  ('7460117','MAT3452',1,'MAT2311'),
  ('7460117','MAT3452',1,'MAT2323'),
  ('7460117','MAT3452',1,'MAT2406'),
  ('7460117','MAT3456',1,'MAT2505'),
  ('7460117','MAT3456',2,'MAT3500'),
  ('7460117','MAT3504',1,'MAT3514'),
  ('7460117','MAT3507',1,'MAT2505'),
  ('7460117','MAT3508',1,'MAT3507'),
  ('7460117','MAT3508',2,'MAT1202'),
  ('7460117','MAT3509',1,'MAT2505'),
  ('7460117','MAT3509',2,'MAT3500'),
  ('7460117','MAT3514',1,'MAT2505'),
  ('7460117','MAT3525',1,'MAT2404'),
  ('7460117','MAT3531',1,'MAT3366'),
  ('7460117','MAT3531',2,'MAT1202'),
  ('7460117','MAT3533',1,'MAT2323'),
  ('7460117','MAT3533',1,'MAT2406'),
  ('7460117','MAT3539',1,'MAT2301'),
  ('7460117','MAT3539',1,'MAT2400'),
  ('7460117','MAT3539',2,'MAT2316'),
  ('7460117','MAT3539',2,'MAT2318'),
  ('7460117','MAT3539',2,'MAT2319'),
  ('7460117','MAT3539',2,'MAT2505'),
  ('7460117','MAT3545',1,'MAT3500'),
  ('7460117','MAT3545',2,'MAT3504'),
  ('7460117','MAT3561',1,'MAT3533'),
  ('7460117','MAT3562',1,'MAT3533'),
  ('7460117','MAT3562',2,'MAT2301'),
  ('7460117','MAT3565',1,'MAT1202'),
  ('7460117','MAT3565',2,'MAT2405'),
  ('7460117','MAT4072',1,'MAT2307'),
  ('7460117','MAT4072',1,'MAT2404'),
  ('7460117','MAT4072',2,'MAT2407'),
  ('7460117','PEC1008',1,'PHI1006'),
  ('7460117','PHI1002',1,'PHI1006'),
  ('7480113QTD','MAT1202',1,'MAT2505'),
  ('7480113QTD','MAT1203',1,'MAT3374'),
  ('7480113QTD','MAT1203',2,'MAT3552E'),
  ('7480113QTD','MAT1203',3,'MAT1207'),
  ('7480113QTD','MAT1204',1,'MAT3507'),
  ('7480113QTD','MAT1204',2,'MAT3514'),
  ('7480113QTD','MAT1205E',1,'FLF1107'),
  ('7480113QTD','MAT1206E',1,'MAT3507'),
  ('7480113QTD','MAT1206E',2,'MAT1202'),
  ('7480113QTD','MAT1207',1,'MAT3374'),
  ('7480113QTD','MAT1208',1,'MAT1202'),
  ('7480113QTD','MAT1208',2,'MAT3505'),
  ('7480113QTD','MAT2034',1,'MAT2502'),
  ('7480113QTD','MAT2034',2,'MAT2403'),
  ('7480113QTD','MAT2323',1,'MAT2502'),
  ('7480113QTD','MAT2403',1,'MAT2400'),
  ('7480113QTD','MAT2403',2,'MAT2501'),
  ('7480113QTD','MAT2502',1,'MAT2501'),
  ('7480113QTD','MAT2503',1,'MAT2502'),
  ('7480113QTD','MAT2505',1,'HUS1011'),
  ('7480113QTD','MAT3148',1,'MAT3514'),
  ('7480113QTD','MAT3373E',1,'MAT2505'),
  ('7480113QTD','MAT3374',1,'MAT1202'),
  ('7480113QTD','MAT3374',2,'MAT3507'),
  ('7480113QTD','MAT3377',1,'MAT1206E'),
  ('7480113QTD','MAT3452',1,'MAT2311'),
  ('7480113QTD','MAT3452',1,'MAT2323'),
  ('7480113QTD','MAT3452',1,'MAT2406'),
  ('7480113QTD','MAT3453',1,'MAT2323'),
  ('7480113QTD','MAT3505',1,'MAT2505'),
  ('7480113QTD','MAT3505',2,'MAT3557'),
  ('7480113QTD','MAT3506',1,'MAT2505'),
  ('7480113QTD','MAT3507',1,'MAT2505'),
  ('7480113QTD','MAT3514',1,'MAT2505'),
  ('7480113QTD','MAT3519',1,'MAT2505'),
  ('7480113QTD','MAT3533',1,'MAT2323'),
  ('7480113QTD','MAT3533',1,'MAT2406'),
  ('7480113QTD','MAT3534',1,'MAT3507'),
  ('7480113QTD','MAT3534',2,'MAT2323'),
  ('7480113QTD','MAT3535',1,'MAT3514'),
  ('7480113QTD','MAT3535',2,'MAT2323'),
  ('7480113QTD','MAT3538',1,'MAT1206E'),
  ('7480113QTD','MAT3538',2,'MAT3514'),
  ('7480113QTD','MAT3539',1,'MAT2301'),
  ('7480113QTD','MAT3539',1,'MAT2400'),
  ('7480113QTD','MAT3539',2,'MAT2316'),
  ('7480113QTD','MAT3539',2,'MAT2318'),
  ('7480113QTD','MAT3539',2,'MAT2319'),
  ('7480113QTD','MAT3539',2,'MAT2505'),
  ('7480113QTD','MAT3541E',1,'MAT1202'),
  ('7480113QTD','MAT3542',1,'MAT1202'),
  ('7480113QTD','MAT3542',2,'MAT3507'),
  ('7480113QTD','MAT3550E',1,'MAT2505'),
  ('7480113QTD','MAT3552E',1,'MAT3514'),
  ('7480113QTD','MAT3554E',1,'MAT2505'),
  ('7480113QTD','MAT3554E',2,'MAT3500'),
  ('7480113QTD','MAT3558',1,'MAT2505'),
  ('7480113QTD','MAT3560',1,'MAT2505'),
  ('7480113QTD','MAT3561E',1,'MAT3533'),
  ('7480113QTD','MAT3562E',1,'MAT3533'),
  ('7480113QTD','MAT3562E',2,'MAT2400'),
  ('7480113QTD','MAT3563',1,'MAT3562E'),
  ('7480113QTD','PEC1008',1,'PHI1006'),
  ('7480113QTD','PHI1002',1,'PHI1006')
 ) AS p(major_code,course_code,group_no,prerequisite_code)
JOIN _new_curricula nc USING(major_code)
ON CONFLICT DO NOTHING;

-- Clean only orphaned course codes from our old demo list; no other user-defined courses are deleted.

-- Hard fail if the four official curricula or their expected source rows were not loaded.
DO $$
DECLARE n_cur INTEGER; n_entries INTEGER;
BEGIN
 SELECT COUNT(*) INTO n_cur FROM public.curricula WHERE curriculum_version IN
  ('QD3565-2023','QD3567-2023','QD3568-2023','QD3569-2023') AND cohort_year=2022;
 SELECT COUNT(*) INTO n_entries FROM public.official_curriculum_entries e
 JOIN public.curricula c ON c.curriculum_id=e.curriculum_id
 WHERE c.curriculum_version IN ('QD3565-2023','QD3567-2023','QD3568-2023','QD3569-2023') AND c.cohort_year=2022;
 IF n_cur <> 4 OR n_entries <> 297 THEN
   RAISE EXCEPTION 'Unexpected official import: % curricula / % entries (expect 4 / 297)',n_cur,n_entries;
 END IF;
END $$;
COMMIT;

-- Verification queries (run after successful COMMIT):
SELECT m.major_code,m.major_name,c.curriculum_version,c.credits_required,
       COUNT(DISTINCT cc.course_code) AS unique_courses,COUNT(DISTINCT e.entry_id) AS pdf_entries
FROM public.curricula c JOIN public.majors m ON m.major_code=c.major_code
LEFT JOIN public.curriculum_courses cc ON cc.curriculum_id=c.curriculum_id
LEFT JOIN public.official_curriculum_entries e ON e.curriculum_id=c.curriculum_id
WHERE c.curriculum_version LIKE 'QD35%-2023'
GROUP BY m.major_code,m.major_name,c.curriculum_version,c.credits_required
ORDER BY m.major_code;
-- Outstanding cases (original prerequisite cell preserved, not fabricated):
SELECT c.major_code,e.course_code,e.prerequisite_source_text,e.prerequisite_parse_status,
       e.pdf_document,e.pdf_page
FROM public.official_curriculum_entries e JOIN public.curricula c USING(curriculum_id)
WHERE e.prerequisite_parse_status IN('unlisted_prerequisite','complex_expression','needs_review')
ORDER BY c.major_code,e.pdf_page,e.course_code;
