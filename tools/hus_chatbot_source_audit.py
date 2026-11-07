"""Independent post-response F2 contracts, reusing the old citation oracle."""

from __future__ import annotations

import json

from tools.evaluate_hus_diagnostic import audit_development_prediction
from tools.hus_rag_layer_metrics import canonical_field
from tools.validate_hus_holdout import rows


class SourceAuditor:
    def __init__(self):
        from tools.verify_hus_e2e import EvidenceOracle

        self.oracle = EvidenceOracle()
        root = self.oracle.root
        self.programs = rows(root / 'programs.jsonl')
        self.groups = rows(root / 'groups.jsonl')
        self.records = {r['record_id']: r for r in rows(root / 'f2_records.jsonl')}
        self.source = self.oracle.bundle
        self.binary_checks = {}

    @staticmethod
    def prerequisite_status(record):
        source = record['prerequisites']
        values = [r.get('prerequisite_source_text') for r in record['source_occurrences']]
        variants = {' '.join(v.split()) for v in values if v and v.strip()}
        if source['has_conflict'] or len(variants) > 1:
            return 'conflict'
        if not values or any(not v or not v.strip() for v in values):
            return 'unknown'
        if source['external_codes'] or set(source['parse_statuses']) - {'normalized', 'parsed'}:
            return 'unresolved'
        return 'present'

    def course_contract(self, answer, target, evidence):
        refs = [evidence[eid]['source_ref'] for eid in target['evidence_ids']]
        identities = {r['identity'] for r in refs if r['identity_field'] == 'record_id'}
        assert len(identities) == 1, 'F2 course target needs a single bound source record'
        record = self.records[next(iter(identities))]
        field = canonical_field(target['expected_field'])
        raw = record['source_occurrences']
        if field == 'prerequisites':
            value = [r['prerequisite_source_text'] for r in raw]
        elif field == 'credits':
            credits = [r['credits_in_source'] for r in raw]
            assert credits and all(v is not None for v in credits) and len(set(credits)) == 1
            value = credits[0]
        elif field == 'name':
            value = record['course_name']
        elif field == 'course_info':
            value = {'course_name': record['course_name'], 'credits': record['credits']}
        elif field == 'hours':
            metadata = next(m for m in self.source['course_metadata']
                            if m['program_id'] == record['program_id'] and m['code'] == record['course_code'])
            value = metadata['values']['hours']
        else:
            raise AssertionError('Unsupported F2 course field')
        return {'course_code': record['course_code'], 'field': field, 'value': value,
                'review_status': record['catalog_review']['status'],
                'prerequisite_status': self.prerequisite_status(record)}

    def program_contract(self, observation, target):
        answer, request = observation['response']['hus_answer'], observation['request']
        assert observation['http_status'] == 200 and answer['status'] == 'answered'
        assert answer['release_id'] == self.oracle.current['release_id']
        assert answer['release_sha256'] == self.oracle.current['release_sha256']
        assert answer['generated_reference_allowed'] == request.get('allow_generated_reference', False)
        assert answer['dataset'] == 'f2' and answer['major'] == request['major'] and answer['version'] == request['version']
        program = next(p for p in self.programs if p['major'] == request['major']
                       and p['scope']['curriculum_version'] == request['version'])
        scope, facts = program['scope'], answer['facts']
        assert facts['scope'] == scope and facts['program_id'] == program['program_id']
        assert request.get('program_variant') in {None, scope['program_variant']}
        field = target['expected_field']
        if field == 'program_credits':
            selected = [program]
            value = {'credits_required': program['credits_required']}
        else:
            selected = [g for g in self.groups if g['program_id'] == program['program_id']]
            if field == 'group_rules':
                selected = [g for g in selected if g['group_key'] == facts['value']['group_key']]
            assert selected
            values = [{k: row[k] for k in ('group_key', 'group_title', 'source_heading', 'group_note',
                                          'min_credits_if_selected', 'offered_credits')} for row in selected]
            value = values[0] if field == 'group_rules' else values
        assert facts['value'] == value and facts['field'] == field
        assert facts['review_status'] == program['catalog_review']['status']
        assert facts['catalog_review'] == program['catalog_review']
        assert len(answer['citations']) == len(selected)
        assert [c['citation_id'] for c in answer['citations']] == [str(i + 1) for i in range(len(selected))]
        for citation, record in zip(answer['citations'], selected, strict=True):
            source = record['citation']
            assert f"[{citation['citation_id']}]" in answer['reply']
            assert citation['dataset'] == 'f2' and citation['source_id'] == source['source_id']
            assert citation['metadata']['release_id'] == self.oracle.current['release_id']
            assert citation['metadata']['release_sha256'] == self.oracle.current['release_sha256']
            assert citation['locator'] == {'evidence_path': source['evidence_path'], 'json_pointer': source['json_pointer']}
            assert citation['source_url'] == citation['open_url'] == source['url']
            assert citation['metadata']['scope'] == scope
            assert citation['metadata']['source_sha256'] == source['source_sha256']
            assert citation['metadata']['source_git_blob'] == source['source_git_blob']
            assert citation['review_status'] == record['catalog_review']['status']
            assert citation['metadata']['catalog_review'] == record['catalog_review']
            assert citation['evidence_kind'] == 'web' and citation['pdf_page'] is None
            assert not citation['pdf_pages'] and citation['availability'] == 'unverified'
            assert citation['document_sha256'] is None and citation['content_origin'] == 'structured_source_draft'
            _, _, table, index = source['json_pointer'].split('/')
            raw = self.source['tables'][table][int(index)]
            quote = json.loads(citation['quote'])
            assert quote and all(raw[k] == v for k, v in quote.items()), 'Quote differs from canonical source'
            expected_quote = ({**value, 'note': program['source_note']} if field == 'program_credits' else
                              {k: record[k] for k in ('group_key', 'group_title', 'source_heading', 'group_note',
                                                     'min_credits_if_selected', 'offered_credits')})
            assert quote == expected_quote, 'Citation omits required source fields'
        return {'field': field, 'program_id': program['program_id'], 'scope': scope, 'value': value,
                'review_status': program['catalog_review']['status'], 'catalog_review': program['catalog_review']}

    def audit(self, observation, target, evidence, client):
        field = target['expected_field']
        try:
            response = observation.get('response') or {}
            assert response.get('mode') == 'hus_rag' and response.get('reply') == response['hus_answer']['reply']
            if target['category'] == 'f2' and field in {'program_credits', 'program_groups', 'group_rules'}:
                expected = self.program_contract(observation, target)
                return {'question_id': observation['question_id'], 'passed': True, 'error': None,
                        'source_f2_contract': expected}
            result = audit_development_prediction(observation, target, evidence, self.oracle, client, self.binary_checks)
            if target['category'] == 'f2' and observation.get('response', {}).get('hus_answer', {}).get('status') == 'answered':
                result['source_f2_contract'] = self.course_contract(observation['response']['hus_answer'], target, evidence)
            return result
        except (AssertionError, KeyError, ValueError, TypeError, StopIteration) as exc:
            return {'question_id': observation['question_id'], 'passed': False, 'error': f'{type(exc).__name__}: {exc}'}
