"""Identity performance changes must retain every canonical field and mutation check."""
from dataclasses import asdict, replace

import pytest

from app.hus import vector_query
from app.hus.rag_loader import MAJOR_CODES, HUSRAGData
from app.hus.vector_contract import digest_json


@pytest.fixture(scope='module')
def data():
    return HUSRAGData.load_current()


def legacy_payload(data):
    return {'release': data.release_identity,
        'chunks': [asdict(c) for family in ('f1', 'f3') for major in sorted(MAJOR_CODES.values())
                   for c in data.chunks(family, major=major, allow_generated=True)]}


def test_fast_payload_is_byte_equivalent_to_complete_legacy_snapshot(data):
    payload = vector_query._canonical_payload(data)
    assert digest_json(payload) == digest_json(legacy_payload(data))
    assert vector_query._canonical_signature(data) == digest_json(payload)
    assert len(payload['chunks']) == sum(len(v) for v in data._chunks.values())


def test_payload_does_not_export_mutable_canonical_metadata(data):
    expected = vector_query._canonical_signature(data)
    payload = vector_query._canonical_payload(data)
    payload['chunks'][0]['metadata']['citation']['source_id'] = 'external-mutation'
    payload['chunks'][0]['text'] = 'external-text'
    assert vector_query._canonical_signature(data) == expected


@pytest.mark.parametrize('field', ['text', 'review', 'provenance'])
def test_nested_tampering_changes_full_signature(data, monkeypatch, field):
    expected = vector_query._canonical_signature(data)
    family = 'f1'
    chunks = data._chunks[family]
    original = chunks[0]
    import copy
    metadata = copy.deepcopy(original.metadata)
    if field == 'review':
        metadata['review_status'] = 'tampered'
    elif field == 'provenance':
        metadata['citation']['source_id'] = 'tampered'
    changed = replace(original, text=original.text + 'tampered' if field == 'text' else original.text,
                      metadata=metadata)
    monkeypatch.setitem(data._chunks, family, (changed, *chunks[1:]))
    payload = vector_query._canonical_payload(data)
    assert digest_json(payload) == digest_json(legacy_payload(data))
    assert vector_query._canonical_signature(data) != expected
