"""Hand-written academic evidence, independent of the production bundle builder."""

from app.hus.llm.contracts import HUSRewriteContext
from app.schemas.hus import HUSAnswer, HUSCitation, HUSQuestion

FIRST = 'Chương trình có 3 học phần; môn MAT3533 thuộc phiên bản 2023.'
SECOND = 'Sinh viên có thể học tiếp sau đại học tại Việt Nam.'


def context(dataset='f1'):
    request = HUSQuestion(question='Thông tin trong nguồn là gì?', major='data_science',
        dataset=dataset, version='2023', course_code='MAT3533' if dataset != 'f1' else None,
        allow_llm_rewrite=True, allow_generated_reference=dataset == 'f3')
    sources = []
    for i, quote in enumerate([FIRST, SECOND], 1):
        ai = dataset == 'f3'
        sources.append(HUSCitation(citation_id=str(i), dataset=dataset, label='Nguồn HUS',
            quote=quote, locator={'local_path': 'C:/Users/private/source.pdf'},
            review_status='generated_reference' if ai else 'include',
            content_origin='generated' if ai else 'source',
            metadata={'major': 'data_science', 'field': 'content' if ai else 'introduction',
                      'release_id': 'synthetic-release-v1', 'release_sha256': 'a' * 64,
                      'scope': {'major': 'data_science', 'curriculum_version': '2023',
                                'program_variant': 'standard'},
                      'account': 'PRIVATE_ACCOUNT', 'transcript': 'PRIVATE_TRANSCRIPT',
                      'history': 'PRIVATE_HISTORY', 'api_key': 'PRIVATE_KEY',
                      'package_path': 'C:/Users/private/package.json'},
            evidence_kind='ai' if ai else 'web', display_label='kiến thức AI' if ai else 'HUS',
            source_url=None if ai else 'https://hus.vnu.edu.vn/source',
            open_url=None if ai else 'https://hus.vnu.edu.vn/source', availability='unverified'))
    facts = ({'course_code': 'MAT3533', 'course_name': 'Học phần mẫu', 'field': 'credits',
              'value': 3, 'review_status': 'draft_unverified', 'prerequisite_status': 'unknown',
              'has_prerequisite_conflict': False, 'unresolved_prerequisites': [],
              'catalog_review': {'reviewer': 'PRIVATE_REVIEWER'},
              'account': 'PRIVATE_ACCOUNT', 'history': 'PRIVATE_HISTORY'} if dataset == 'f2' else {})
    answer = HUSAnswer(reply='Đáp án canonical và cảnh báo nguyên vẹn.', status='answered',
        dataset=dataset, major='data_science', version='2023', citations=sources, facts=facts,
        warnings=['Nguồn chưa xác minh hiệu lực hiện tại.'], release_id='synthetic-release-v1',
        release_sha256='a' * 64, generated_reference_allowed=dataset == 'f3')
    return HUSRewriteContext(question=request, answer=answer,
                             requested_model='gemini-3.5-flash-lite')


def text_output():
    return {'kind': 'rewrite', 'points': [
        {'text': FIRST, 'citation_id': '1', 'anchor_quote': FIRST},
        {'text': SECOND, 'citation_id': '2', 'anchor_quote': SECOND},
    ]}


def compact_text_output():
    """Hand-written current-protocol output; legacy points remain separately tested."""
    return {'kind': 'rewrite_v3', 'items': [{'id': 'b001', 'text': FIRST},
                                           {'id': 'b002', 'text': SECOND}]}


def facts_output():
    return {'kind': 'facts', 'style': 'explain_source', 'fact_keys': [
        'course_code', 'course_name', 'field', 'value', 'review_status',
        'prerequisite_status', 'has_prerequisite_conflict', 'unresolved_prerequisites'],
        'citation_ids': ['1', '2']}
