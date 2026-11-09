"""Capture AI technical observations; all identity/validity decisions remain pending."""
import csv
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

from tools.audit_hus_source_review import ROOT, RELEASE, digest, read_rows, require, write_json, write_rows

OUT = ROOT / 'data/hus/review/p13_followup_v1'
OCR = ROOT / 'data/hus/review/p13_ocr_v1'
BASE = ROOT / 'data/hus/review/p13_source_audit_v1'
CS = '56d751cc897fe12626f05ebaa28842440e3b6402dede058bd280d6f3c1def2d0'
MI = '6e049389bc467f41ea6d48cffd66182c50bf52e77efdbb57868dbe6f14f33b7b'


def image_evidence(folder, sha, page):
    path = ROOT / f'backups/hus_source_review/p13/{folder}/{sha}-p{page:04d}.png'
    return {'source_sha256': sha, 'physical_page': page, 'image_path': path.relative_to(ROOT).as_posix(),
            'image_sha256': digest(path.read_bytes()), 'method': 'AI_assisted_visual_inspection',
            'human_reviewer': None, 'academic_verified': False}


def main():
    require(not OUT.exists(), 'followup exists; preserve the frozen pack')
    ocr = read_rows(OCR / 'ocr_pages.jsonl')
    require(len(ocr) == 72, 'finish the frozen OCR queue before preparing this pack')
    report = json.loads((OCR / 'report.json').read_bytes())
    require(report['ocr_pages'] == 72, 'OCR report incomplete')
    inputs = json.loads((OCR / 'run_inputs.json').read_bytes())['source_inputs_sha256']
    require(all(digest((ROOT / p).read_bytes()) == sha for p, sha in inputs.items()), 'source inputs changed')
    candidates = {r['candidate_id']: r for r in read_rows(RELEASE / 'source_syllabi.jsonl')}
    canonical = {(r['major'], r['course_code']): r for r in read_rows(RELEASE / 'f2_records.jsonl')}
    specs = [
        ('098df9e79c1391af:3:2502', 23, 'printed_code_missing_prefix', 'MAT2502',
         'Trang nguồn in 2502, không in MAT2502; tên Giải tích 2 và 4 tín chỉ gợi ý mapping, cần người duyệt xác nhận.'),
        ('098df9e79c1391af:12:MAT3550E', 74, 'orthographic_title_variant', 'MAT3550E',
         'Nguồn ghi NGUYÊN LÝ; canonical ghi Nguyên lí. Mã, tên tiếng Anh và 3 tín chỉ cùng khớp; đây là đề xuất xử lý khác cách viết.'),
        ('098df9e79c1391af:14:MAT1202', 86, 'matching_title_but_source_duplicate_retained', 'MAT1202',
         'LẬP TRÌNH HƯỚNG ĐỐI TƯỢNG, mã MAT1202, 3 tín chỉ khớp canonical; nguồn còn một đề cương khác dùng trùng mã nên giữ blocker duplicate.'),
        ('098df9e79c1391af:27:MAT1202', 162, 'printed_code_title_and_credit_conflict', None,
         'Nguồn thật in MAT1202 cho XÂY DỰNG HỆ THỐNG NHÚNG, 2 tín chỉ; cùng trang ghi MAT1202 là tiên quyết Lập trình hướng đối tượng. Không nối nội dung này vào MAT1202 canonical.'),
        ('bc0a1f59b7ab202c:54:MAT3561', 256, 'orthographic_title_variant_with_edition_blocker', 'MAT3561',
         'Nguồn ghi XỬ LÝ, canonical ghi Xử lí. Nguồn 2021 in tiên quyết MAT3508/MAT3509; canonical QD3567-2023 ghi MAT3533. Tên gần trùng không xác minh tương đương phiên bản hay tiên quyết.'),
    ]
    identities = []
    for cid, page, kind, code, note in specs:
        row = candidates[cid]
        record = canonical.get((row['source_major'], code)) if code else None
        require(code is None or record is not None, 'proposed identity not in canonical scope')
        identities.append({'candidate_id': cid, 'source_title': row['title_as_extracted'],
                           'source_code_as_printed': row['course_code_as_printed'],
                           'source_edition': row['source_publication_year'], 'source_major': row['source_major'],
                           'classification': kind, 'observation': note,
                           'proposed_canonical_record_id': record['record_id'] if record else None,
                           'canonical_title': record['course_name'] if record else None,
                           'canonical_scope': record['scope'] if record else None,
                           'canonical_prerequisite_variants': record['prerequisites']['raw_variants'] if record else None,
                           'evidence': image_evidence('visual_identity_v1', row['raw_sha256'], page),
                           'existing_release_identity_issues': row['identity_issues'],
                           'proposal_applied': False, 'decision_status': 'pending_human_identity_and_edition_review',
                           'academic_verified': False, 'default_retrieval_enabled': False,
                           'reviewer': None, 'reviewed_at': None})
        if cid == 'bc0a1f59b7ab202c:54:MAT3561':
            identities[-1]['canonical_pdf_visual_evidence'] = {
                **image_evidence('ocr_images_v1', '6c19e390ba61c1766e2826b055fe39b3987db25ef707263f60ce337347d87df8', 12),
                'row_as_printed': 54, 'observed_prerequisite': 'MAT3533',
                'observation': 'Đối chiếu trực quan ô tiên quyết của MAT3561 trong bản QD3567-2023; không dùng bản đề cương 2021 ghi khác để đè dữ kiện này.'}
    sparse_specs = [
        ('2bc81e20fa37d37234cdb50862bdcbd2c1ae0fb4b136a7612a56da34fb712920', 3, False, 'Chỉ quan sát thấy dòng Hà Nội, 2015.'),
        ('49974d4ff831180faf7125853d921f74dde88a4120cd967212e0eefa1cdb4ce6', 29, False, 'Chỉ quan sát thấy số trang 29.'),
        (CS, 172, False, 'Chỉ quan sát thấy footer số 5 và số trang 172.'),
        (MI, 281, True, 'Có đề mục XII. Map, Filter, Reduce và ba tiểu mục; không phải trang trắng. PyMuPDF capture đã giữ nội dung, PDFium chỉ trích số trang.'),
        ('e8a9524ff81bfec2038760970327650c005f31cbadb7be8ad2abe2f141c8978f', 15, False, 'Chỉ quan sát thấy số in 17 trên trang PDF vật lý 15; giữ physical page 15.'),
        ('ec3123312b52b36ac9e612344fca7ab7898532942d468a7fa5fc6901c5e46212', 18, False, 'Chỉ quan sát thấy số trang 18.'),
    ]
    sparse = [{**image_evidence('visual_sparse_v1', sha, page), 'body_content_observed': content,
               'observation': note, 'blank_verified': False, 'academic_review_upgraded': False}
              for sha, page, content, note in sparse_specs]
    placeholders = [
        {**image_evidence('visual_placeholders_v1', MI, 10),
         'candidate_id': 'bc0a1f59b7ab202c:1:PEC1008', 'field': 'objectives',
         'observation': 'Mục 6 chỉ có tiêu đề rồi chuyển thẳng sang mục 7 Chuẩn đầu ra. Giữ thiếu mục tiêu; không lấy chuẩn đầu ra thay cho mục tiêu.'},
        {**image_evidence('visual_placeholders_v1', MI, 41),
         'source_titles': ['TIẾNG ANH B1', 'GIÁO DỤC THỂ CHẤT', 'GIÁO DỤC QUỐC PHÒNG AN NINH'],
         'observation': 'Ba tiêu đề trên trang nguồn không có mã hay nội dung đề cương chi tiết; không tự tạo thêm ba hồ sơ học phần.'},
        {**image_evidence('visual_placeholders_v1', MI, 42),
         'observation': 'Trang tiếp theo bắt đầu đề cương TIN HỌC CƠ SỞ, in INM1000; không nối nội dung môn này vào ba tiêu đề trang 41.'},
    ]
    corpus = json.loads((ROOT / 'data/hus/corpus/source_manifest.json').read_bytes())
    missing = []
    source_hashes = {}
    alias_ids = {'554827330988bff8', 'a8f161744d0c9907', '7b0e9c679a8eb75a', 'a090bd625a439d9b'}
    for row in read_rows(BASE / 'missing_sources.jsonl'):
        path = ROOT / 'data/hus' / corpus['documents'][row['document_id']]['markdown_path']
        archive = path.read_text(encoding='utf-8')
        body = archive.split('---', 2)[-1]
        fold = ''.join(c for c in unicodedata.normalize('NFD', body[:2000]).casefold().replace('đ', 'd')
                       if not unicodedata.combining(c))
        fold = ' '.join(fold.split())
        if any(phrase in fold for phrase in ['trinh do thac si', 'dao tao tien si', 'trinh do tien si']):
            category, priority = 'postgraduate_archive_outside_current_undergraduate_scope', 'defer_outside_current_scope'
        elif row['document_id'] in alias_ids:
            category, priority = 'undergraduate_scan_possible_alias', 'verify_original_binary_binding'
        elif '/TUYENSINH/' in row['source_url'] or '/DATA/IMAGES/2026/' in row['source_url']:
            category, priority = 'admissions_separate_year_and_scope', 'separate_scope_and_effective_year_review'
        elif '/semianar/' in row['source_url']:
            category, priority = 'seminar_outside_F123', 'defer_outside_current_scope'
        else:
            category, priority = 'curriculum_outcome_matrix_or_map', 'recover_and_identify_program_edition'
        source_hashes[path.relative_to(ROOT).as_posix()] = digest(path.read_bytes())
        missing.append({**row, 'proposed_category': category, 'priority': priority,
                        'classification_basis': 'archived_markdown_body_and_URL_not_original_binary_review',
                        'archive_path': path.relative_to(ROOT).as_posix(), 'archive_sha256': digest(path.read_bytes()),
                        'raw_recovered_in_followup': False, 'scope_verified': False})
    bindings = {'554827330988bff8': 'bc070d7ae3713f77c36817d960b73dec53dcdeacda5e25e557c37a732abe09ab',
                'a8f161744d0c9907': 'bc070d7ae3713f77c36817d960b73dec53dcdeacda5e25e557c37a732abe09ab',
                '7b0e9c679a8eb75a': 'b4b0289701a6c1e2b7d288ea880970a2a9f49d680dc6c3986d9b840d93083ab2',
                'a090bd625a439d9b': '6c19e390ba61c1766e2826b055fe39b3987db25ef707263f60ce337347d87df8',
                'c1c50f5ba9094527': 'b4b0289701a6c1e2b7d288ea880970a2a9f49d680dc6c3986d9b840d93083ab2',
                'd988fffe2a509f23': '6c19e390ba61c1766e2826b055fe39b3987db25ef707263f60ce337347d87df8'}
    blockers = []
    for row in read_rows(BASE / 'historical_ocr_blockers.jsonl'):
        available = row['binary_available_in_this_audit']
        sha = bindings[row['document_id']]
        blockers.append({**row, 'related_binary_sha256': sha,
                         'related_binary_binding': 'existing_recovered_capture' if available else 'possible_alias_not_proven',
                         'related_binary_pages_ocr_executed': sum(r['source_sha256'] == sha for r in ocr),
                         'historical_document_ocr_executed': available,
                         'historical_bytes_proven': False, 'resolved_by_this_followup': False,
                         'review_status': 'OCR_executed_visual_table_review_pending' if available else 'original_binding_unresolved_related_OCR_only'})
    OUT.mkdir(parents=True)
    write_rows(OUT / 'identity_proposals.jsonl', identities)
    write_rows(OUT / 'sparse_page_observations.jsonl', sparse)
    write_rows(OUT / 'source_placeholder_observations.jsonl', placeholders)
    write_rows(OUT / 'missing_source_priorities.jsonl', missing)
    write_rows(OUT / 'historical_ocr_followup.jsonl', blockers)
    write_json(OUT / 'validity_search_notes.json', {
        'checked_on': '2026-11-02', 'method': 'connected_web_search_official_domains',
        'queries': [
            'site:hus.vnu.edu.vn "chương trình đào tạo" "Toán tin" 2025',
            'site:hus.vnu.edu.vn "chương trình đào tạo" "Khoa học máy tính" 2024 2025',
            'site:hus.vnu.edu.vn "chương trình đào tạo" "Khoa học dữ liệu" 2025',
            'site:mim.hus.vnu.edu.vn "3567" "3568"'],
        'selected_leads': [
            {'url': 'https://hus.vnu.edu.vn/tin-tuc-su-kien/khai-mac-chuong-trinh-danh-gia-ngoai-4-chuong-trinh-dao-tao-cua-truong-dai-hoc-khoa-hoc-tu-nhien-theo-tieu-chuan-aun-qa-142125',
             'page_date': '2025-07-08', 'scope': 'KHMTTT undergraduate accreditation event; not a curriculum amendment/edition applicability decision'},
            {'url': 'https://hus.vnu.edu.vn/tin-tuc-su-kien/be-mac-dot-khao-sat-chinh-thuc-kiem-dinh-chat-luong-05-chuong-trinh-dao-tao-trinh-do-dai-hoc-140828',
             'page_date': '2025-01-14', 'scope': 'Mathematics/Data Science undergraduate evaluation event; not a QD3565/QD3569 current-validity certificate'},
            {'url': 'https://hus.vnu.edu.vn/sites/default/files/huongdan/4.%20May%20tinh%20va%20khoa%20hoc%20thong%20tin.pdf',
             'document_decision_in_search_extract': '3552/QD-DHQGHN, 2015-09-28',
             'scope': 'Historical curriculum; search-index publication/crawl time must not replace declared document edition',
             'live_binary_hash_verified': False},
            {'url': 'https://tuyensinh.hus.vnu.edu.vn/dai-hoc/nganh-hoc/toan-toan-ung-dung-va-tin-hoc/toan-tin',
             'scope': 'Program introduction; does not prove QD3567 applicability to an individual cohort'}],
        'conclusion': 'Bounded search found relevant context but did not establish current curriculum/syllabus validity or absence of later amendments.',
        'search_is_exhaustive': False, 'current_validity_confirmed': 0, 'academic_review_upgraded': False})
    by_page = {(r['source_sha256'], r['pdf_page']): r for r in ocr}
    number_to_sha = {p['source_ref'].split('.', 1)[0]: p['sha256']
                     for p in json.loads((RELEASE / 'input_manifest.json').read_bytes())['pdfs']}
    code_diagnostics = []
    with (RELEASE / 'evidence/pdf_code_page_audit.csv').open(encoding='utf-8', newline='') as stream:
        for expected in csv.DictReader(stream):
            page = by_page[number_to_sha[expected['pdf_number']], int(expected['pdf_page'])]
            hits = [i for i, box in enumerate(page['boxes'])
                    if expected['course_code'] in {''.join(m) for m in re.findall(r'\b([A-Z]{3})\s*(\d{4})(E?)\b', box['text'].upper())}]
            code_diagnostics.append({**expected, 'source_sha256': page['source_sha256'],
                                     'matching_OCR_box_indexes': hits, 'code_token_seen_on_page': bool(hits),
                                     'row_alignment_verified': False, 'academic_verified': False,
                                     'limitation': 'Token may occur in prerequisites or other rows; page presence does not verify a curriculum cell or transcription accuracy.'})
    write_rows(OUT / 'code_token_diagnostic.jsonl', code_diagnostics)
    summary = {'identity_headers_visually_inspected': len(identities), 'proposed_identity_links_not_applied': 4,
               'printed_duplicate_conflict_retained': 1, 'sparse_pages_visually_inspected': 6,
               'source_placeholder_pages_visually_inspected': 3, 'distinct_visual_pages_inspected': 15,
               'sparse_pages_with_body_content': 1, 'missing_originals_remaining': len(missing),
               'missing_source_proposed_categories': dict(Counter(r['proposed_category'] for r in missing)),
               'historical_ocr_blockers': len(blockers), 'existing_recovered_documents_ocr_executed': 2,
               'historical_ocr_blockers_closed': 0, 'new_academic_reviews': 0,
               'new_field_quotes_for_review': 50, 'OCR_pages': len(ocr),
               'source_retry_attempts': 6, 'new_originals_recovered': 0,
               'expected_code_page_occurrences_diagnosed': len(code_diagnostics),
               'code_token_seen_on_page': sum(r['code_token_seen_on_page'] for r in code_diagnostics),
               'code_token_missing_from_OCR_page': sum(not r['code_token_seen_on_page'] for r in code_diagnostics),
               'code_token_diagnostic_is_not_row_accuracy': True,
               'current_validity_confirmed': 0, 'official_F3_enabled': False, 'runtime_modified': False,
               'P1_3_accepted': False, 'human_reviewer': None}
    write_json(OUT / 'report.json', summary)
    packet = ['# P1-3 — Gói tiếp tục chờ review', '',
              'Các quan sát dưới đây do AI hỗ trợ kiểm tra kỹ thuật. Reviewer học vụ và thời điểm duyệt vẫn null. '
              'Không áp dụng mapping, không bật candidate/official F3, không suy hiệu lực hiện tại từ năm trên bìa.', '',
              '## Mã/tên cần quyết định', '',
              '| Candidate | Quan sát | Quyết định |', '| --- | --- | --- |']
    packet += [f"| `{r['candidate_id']}` | {r['observation']} | Chờ người review |" for r in identities]
    packet += ['', '## 50 trích đoạn bổ sung', '',
               'Mở PDF ghim để kiểm tra bảng/ô và phiên bản; nguyên văn, offset và mọi trang có trong '
               '`../p13_syllabus_supplement_v1/field_supplements.jsonl`. Đường dẫn Git dưới đây mở binary đã kiểm hash, '
               'không xác nhận URL gốc đang hoạt động hoặc tài liệu còn hiệu lực.', '',
               '| Candidate | Trường | Trang PDF vật lý | PDF ghim |', '| --- | --- | --- | --- |']
    for r in read_rows(ROOT / 'data/hus/review/p13_syllabus_supplement_v1/field_supplements.jsonl'):
        sha = r['raw_sha256'];pages = r['span']['pdf_pages']
        url = f'https://raw.githubusercontent.com/5-Bit-System/SE_Project/a543cf8d1fac273db41a65a14fb7ae0a05b2d965/data/hus/recovery/20261031/files/{sha}.pdf#page={pages[0]}'
        packet.append(f"| `{r['candidate_id']}` | {r['field']} | {', '.join(map(str,pages))} | [Mở PDF]({url}) |")
    packet += ['', '## Các thiếu hụt giữ nguyên', '',
               '- PEC1008: mục 6 trên trang PDF10 có tiêu đề và không có phần thân; không lấy mục 7 thay thế.',
               '- Trang PDF41 đề cương Toán tin có ba tiêu đề Tiếng Anh B1/GDTC/GDQPAN, không có mã hay đề cương chi tiết; trang42 đã sang INM1000.',
               '- 37 raw chưa thu hồi: xem `missing_source_priorities.jsonl`; 24 sau đại học và 1 seminar được đề xuất hoãn theo phạm vi hiện tại.',
               '- 6 hồ sơ pending OCR lịch sử chưa được đóng: 2 binary đã OCR; 4 liên kết raw cũ vẫn chưa chứng minh dù có PDF liên quan để tham khảo.',
               '- Text OCR của 72 trang nằm ở `../p13_ocr_v1/ocr_pages.jsonl`; ảnh tại `image_path` trong backups. '
               'Điểm confidence của model không phải độ chính xác hay xác minh mọi ô bảng.', '',
               '## Cách người review ghi quyết định', '',
               'Với từng candidate/field: ghi accept/reject/defer, reviewer thật, ngày, scope ngành/edition/cohort, '
               'hash PDF, trang vật lý, quote hoặc ô bảng và lý do. Kiểm riêng hiệu lực/điều chỉnh sau văn bản. '
               'Giữ bản pack này làm snapshot; ghi quyết định vào bản review mới rồi mới chuẩn bị release và nghiệm thu citation.', '']
    (OUT / 'reviewer_packet.md').write_bytes('\n'.join(packet).encode('utf-8'))
    (OUT / 'generation_script.py').write_bytes(Path(__file__).read_bytes())
    write_json(OUT / 'manifest.json', {'schema_version': '1.0', 'source_inputs_sha256': source_hashes,
               'baseline_manifest_sha256': digest((BASE / 'manifest.json').read_bytes()),
               'ocr_manifest_sha256': digest((OCR / 'manifest.json').read_bytes()),
               'syllabus_supplement_manifest_sha256': digest((ROOT / 'data/hus/review/p13_syllabus_supplement_v1/manifest.json').read_bytes()),
               'source_retry_manifest_sha256': digest((ROOT / 'data/hus/review/p13_source_retry_v1/manifest.json').read_bytes()),
               'files_sha256': {p.name: digest(p.read_bytes()) for p in OUT.iterdir() if p.is_file()}})
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
