"""Independent v4 source/locator audit. This does not judge semantic entailment."""

import hashlib
import json
import re

from tools.hus_chatbot_source_audit import SourceAuditor
from tools.hus_rag_layer_metrics import canonical_field
from tools.verify_hus_e2e import EvidenceOracle, _read

RELEASE = 'hus-data-20261111-v4'
RELEASE_SHA = 'ed4c1ccb93da50829c6b6b960f22d1a077c433ed0a55c3a1e1bed832c1baf463'
PARENT_MANIFEST_SHA = '5a926e7587a41b0817838da14213809bce2675a763b2f9d84b2933ce6b00ad4f'
DERIVED = {'f3_records.jsonl', 'f3_chunks.jsonl', 'chunks.jsonl',
           'evaluation/questions.jsonl', 'quality_report.json'}


def checksum(raw):
    return hashlib.sha256(raw).hexdigest()


def rendered_parts(record, field):
    """Render source records independently of app.f3_detail/adapter/retrieval."""
    profile = record['profile']
    if field == 'objectives':
        return ['Mục tiêu tham khảo do AI đề xuất:\n' + '\n'.join('- ' + s for s in profile['objectives'])]
    assert field == 'content'
    result = ['Tổng quan tham khảo:\n' + profile['overview'] + '\nCác chủ đề tham khảo:\n'
              + '\n'.join('- ' + u['title'] for u in profile['units'])]
    result += [u['title'] + '\n' + u['explanation'] + '\nKhái niệm thành phần: '
               + '; '.join(u['concepts']) + '.\nVí dụ minh họa do AI biên soạn: ' + u['example']
               for u in profile['units']]
    return result


class V4EvidenceOracle(EvidenceOracle):
    def check_asset_binding(self):
        assert self.current['release_id'] == RELEASE and self.current['release_sha256'] == RELEASE_SHA
        manifest = _read(self.root / 'manifest.json')
        unsigned = {k: v for k, v in manifest.items() if k != 'release_sha256'}
        raw = (json.dumps(unsigned, sort_keys=True, ensure_ascii=False, indent=2) + '\n').encode()
        assert checksum(raw) == manifest['release_sha256'] == RELEASE_SHA
        assert set(manifest['files']) | {'manifest.json'} == {
            p.relative_to(self.root).as_posix() for p in self.root.rglob('*') if p.is_file()}
        for name, identity in manifest['files'].items():
            path = (self.root / name).resolve()
            assert path.is_relative_to(self.root.resolve())
            body = path.read_bytes()
            assert identity == {'bytes': len(body), 'sha256': checksum(body)}
        path = self.root / 'evidence/f3_v2/parent_manifest.json'
        assert checksum(path.read_bytes()) == PARENT_MANIFEST_SHA
        parent = _read(path)
        assert self.asset_registry['release_sha256'] == parent['release_sha256']
        # Prove inheritance for every unchanged parent payload, not just its declaration.
        for name, identity in parent['files'].items():
            if name not in DERIVED:
                body = (self.root / name).read_bytes()
                assert identity == {'bytes': len(body), 'sha256': checksum(body)}
        for sha, entry in self.asset_registry['assets'].items():
            path = (self.asset_root / entry['path']).resolve()
            assert path.is_relative_to(self.asset_root.resolve())
            body = path.read_bytes()
            assert checksum(body) == sha == entry['sha256'] and len(body) == entry['bytes']

    def check_f3_quote(self, citation, original):
        record = self.f3_records[original['record_id']]
        source = original['citation']
        field = original['field']
        parts = rendered_parts(record, field)
        position, spans = 0, {}
        for part in parts:
            spans[position, position + len(part)] = part
            position += len(part) + 2
        start, end = source['start_char'], source['end_char']
        assert citation['quote'] == spans[start, end]
        assert original['text'].endswith(citation['quote'])
        assert citation['locator'] == {
            'record_id': record['record_id'], 'field': field, 'evidence_path': 'f3_records.jsonl',
            'start_char': start, 'end_char': end, 'offset_scope': source['offset_scope'],
            'release_id': RELEASE,
        }
        assert source['offset_scope'] == 'rendered_field_text_excluding_repeated_context'
        assert record['scope'] == original['scope']
        assert citation['metadata']['academic_verified'] is False
        assert citation['metadata']['disclosure_required'] is True

    def check_targets(self, record, request, answer):
        family, gold = answer['dataset'], record['gold']
        evidence = record['gold_evidence']
        assert evidence and [e['evidence_id'] for e in evidence] == gold['evidence_ids']
        codes = set(re.findall(r'\b[A-Z]{3}\d{4}[A-Z]?\b', request['question']))
        if request.get('course_code'):
            codes.add(request['course_code'])
        if request.get('version') is not None:
            assert answer['version'] == request['version']
        if family in {'f1', 'f3'}:
            assert answer['facts'] == {}
        for target in evidence:
            ref = target['source_ref']
            if family == 'f1':
                assert ref['identity_field'] == 'chunk_id' and ref['json_pointer'] == '/source_quote'
                assert ref['path'] in {f'data/hus/rag/releases/{v}/f1_chunks.jsonl'
                                       for v in (RELEASE, 'hus-data-20261031-v3')}
                source = self.chunks['f1'][ref['identity']]
                assert target['value'] in source['source_quote']
                assert any(c['metadata']['chunk_id'] == ref['identity'] for c in answer['citations'])
            elif family == 'f2':
                assert ref['identity_field'] == 'record_id'
                assert ref['path'] in {f'data/hus/rag/releases/{v}/f2_records.jsonl'
                                       for v in (RELEASE, 'hus-data-20261031-v3')}
                codes.add(ref['identity'].rsplit(':', 1)[1])
                source = self.records[self.curricula[request['major'], answer['version']], answer['facts']['course_code']]
                assert source['record_id'] == ref['identity']
            else:
                assert ref['path'] == f'data/hus/rag/releases/{RELEASE}/f3_records.jsonl'
                assert ref['sha256'] == checksum((self.root / 'f3_records.jsonl').read_bytes())
                source = self.f3_records[ref['record_id']]
                assert ref['field'] == gold['expected_field']
                assert source['major'] == request['major'] and source['curriculum_version'] == answer['version']
                assert target['value'] in rendered_parts(source, ref['field'])
                assert any(c['quote'] == target['value'] and c['locator']['record_id'] == ref['record_id']
                           for c in answer['citations'])
                codes.add(source['course_code'])
        if family in {'f2', 'f3'}:
            assert len(codes) == 1
            actual = (answer['facts']['course_code'] if family == 'f2'
                      else answer['citations'][0]['metadata']['course_code'])
            assert codes == {actual}

    def audit(self, record):
        try:
            request = record.get('effective_request', record['request'])
            response, gold = record['baseline'], record['gold']
            assert set(response) == {'mode', 'reply', 'hus_answer'}
            if gold['category'] == 'basic_chat':
                assert response['mode'] == 'basic_chat' and response['hus_answer'] is None
            else:
                answer = response['hus_answer']
                assert response['mode'] == 'hus_rag' and response['reply'] == answer['reply']
                assert answer['status'] == gold['expected_status']
                assert answer['major'] == request['major']
                assert answer['release_id'] == RELEASE and answer['release_sha256'] == RELEASE_SHA
                if answer['status'] != 'answered':
                    assert not answer['citations'] and not answer['facts']
                else:
                    self.check_targets(record, request, answer)
                    code = answer.get('course_code')
                    if not code and answer['dataset'] == 'f2':
                        code = answer['facts']['course_code']
                    if not code and answer['dataset'] == 'f3':
                        code = answer['citations'][0]['metadata']['course_code']
                    self.check(answer, request['major'], dataset=gold['category'], code=code,
                               version=answer['version'])
                    field = canonical_field(gold['expected_field'])
                    if answer['dataset'] == 'f2':
                        source = self.records[self.curricula[request['major'], answer['version']], code]
                        rows = source['source_occurrences']
                        expected = ([r['prerequisite_source_text'] for r in rows] if field == 'prerequisites'
                                    else rows[0]['credits_in_source'])
                        if field == 'credits':
                            assert all(r['credits_in_source'] == expected for r in rows) and expected is not None
                        assert answer['facts']['field'] == field and answer['facts']['value'] == expected
                        assert type(answer['facts']['value']) is type(expected)
                        assert answer['facts']['prerequisite_status'] == SourceAuditor.prerequisite_status(source)
                    else:
                        for citation in answer['citations']:
                            chunk = self.chunks[answer['dataset']][citation['metadata']['chunk_id']]
                            assert chunk['field'] == field
                            assert (answer['dataset'] == 'f1' and answer['version'] is None
                                    or chunk['scope']['curriculum_version'] == answer['version'])
            return {'passed': True, 'kind': 'source_integrity_not_semantic_review'}
        except (AssertionError, KeyError, TypeError, ValueError, IndexError, StopIteration) as exc:
            return {'passed': False, 'error': type(exc).__name__}
