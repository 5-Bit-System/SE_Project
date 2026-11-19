"""Portable standalone RAG profile: lexical, LLM off, no private env-file or product DB."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import socket
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
RELEASE = 'hus-data-20261111-v4'
RELEASE_SHA = 'ed4c1ccb93da50829c6b6b960f22d1a077c433ed0a55c3a1e1bed832c1baf463'
PROGRAMS = {'data_science': ('MAT3533', 'QD3569-2023'),
            'mathematics': ('MAT3300', 'QD3565-2023'),
            'mathematics_informatics': ('MAT3539', 'QD3567-2023'),
            'computer_science': ('MAT3507', 'QD3568-2023')}


def configure():
    # Set before any app import. Never read a private config or provider key.
    os.environ['HUS_RAG_ROOT'] = str(ROOT / 'data/hus/rag')
    os.environ['HUS_RETRIEVAL_MODE'] = 'lexical'
    os.environ['HUS_LLM_ENABLED'] = 'false'
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'


def check(*, answer_policy='legacy') -> dict:
    if answer_policy not in {'legacy', 'focused'}:
        raise ValueError('Invalid answer policy')
    configure()
    os.environ['HUS_ANSWER_POLICY'] = answer_policy
    from fastapi.testclient import TestClient

    from app.hus.demo import app
    from app.hus.llm.client import HUSLLMClient
    from app.services.hus_service import get_hus_answerer

    def forbidden(*args, **kwargs):
        raise AssertionError('Submission check attempted external network/provider access')

    real_connect = socket.socket.connect

    def local_connect(sock, address):
        # Windows asyncio creates a loopback socket pair when starting TestClient.
        if isinstance(address, tuple) and address[0] in {'127.0.0.1', '::1'}:
            return real_connect(sock, address)
        return forbidden()

    get_hus_answerer.cache_clear()
    rows, assets, menus = [], set(), 0
    with (patch('socket.create_connection', forbidden), patch('socket.socket.connect', local_connect),
          patch.object(HUSLLMClient, '__init__', forbidden), TestClient(app) as client):
        config = client.get('/hus/config')
        assert config.status_code == 200
        metadata = config.json()
        assert metadata['release_id'] == RELEASE and metadata['release_sha256'] == RELEASE_SHA
        assert metadata['llm_rewrite_available'] is False and len(metadata['majors']) == 4
        for path in ('/', '/static/hus-rag-demo.css', '/static/hus-rag-demo.js', '/static/favicon.svg'):
            assert client.get(path).status_code == 200
        for major, (course, version) in PROGRAMS.items():
            menu = client.get('/hus/questions', params={'major': major, 'version': version})
            assert menu.status_code == 200
            # Count below uses the public menu contract, not source files.
            groups = menu.json()['groups']
            menus += sum(len(group['questions']) for group in groups)
            for question, consent, expected, dataset in (
                ('Giới thiệu ngành', False, 'answered', 'f1'),
                (f'Số tín chỉ {course}?', False, 'answered', 'f2'),
                (f'Nội dung {course}?', False, 'needs_clarification', 'f3'),
                (f'Nội dung {course}?', True, 'answered', 'f3'),
                (f'{course} thi cuối kỳ bao nhiêu phần trăm?', False, 'no_information', 'f3'),
            ):
                response = client.post('/hus/chat', json={'question': question, 'major': major,
                    'version': version, 'allow_generated_reference': consent, 'allow_llm_rewrite': True})
                assert response.status_code == 200
                value = response.json()
                assert set(value) == {'mode', 'reply', 'hus_answer'}
                answer = value['hus_answer']
                if answer_policy == 'focused' and dataset == 'f1' and answer.get('source_choices'):
                    expected = 'needs_clarification'
                    assert not answer['citations'] and len(answer['source_choices']) > 1
                assert answer['status'] == expected and answer['major'] == major and answer['dataset'] == dataset
                if expected == 'answered' and dataset == 'f2':
                    assert answer['facts']['course_code'] == course and answer['facts']['field'] == 'credits'
                    if major == 'data_science':
                        assert answer['facts']['value'] == 3
                if expected == 'answered':
                    assert answer['citations']
                    for citation in answer['citations']:
                        if answer['dataset'] == 'f3':
                            assert citation['display_label'] == 'kiến thức AI' and citation['open_url'] is None
                        url = citation.get('open_url')
                        if url and url.startswith('/hus/sources/'):
                            binary = client.get(url.split('#')[0])
                            assert binary.status_code == 200
                            assert hashlib.sha256(binary.content).hexdigest() == citation['document_sha256']
                            assets.add(citation['document_sha256'])
                rows.append({'major': major, 'question': question, 'status': expected})
        assert menus == 2124
    return {'schema_version': 'hus-submission-check-1.0', 'passed': True,
        'release_id': RELEASE, 'release_sha256': RELEASE_SHA,
        'profile': {'retrieval': 'lexical', 'llm_enabled': False, 'bind': '127.0.0.1',
                    'answer_policy': answer_policy},
        'environment': {'python': sys.version.split()[0], 'platform': platform.platform(),
            'packages': {name: importlib.metadata.version(name) for name in
                ('fastapi', 'starlette', 'uvicorn', 'pydantic', 'httpx', 'pdfplumber')}},
        'cases': rows, 'menu_items': menus, 'downloaded_source_hashes': sorted(assets),
        'new_provider_calls': 0, 'external_network_allowed': False,
        'limits': ['Local in-process API check, not browser/network/load or external-machine acceptance.',
                   'Does not test live Gemini, all source files or semantic answer quality; LLM stays off.']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Offline API/source/config check, then exit')
    parser.add_argument('--port', type=int, default=8011)
    parser.add_argument('--retrieval', choices=['lexical', 'hybrid'], default='lexical')
    parser.add_argument('--model-cache', type=Path)
    parser.add_argument('--answer-policy', choices=['legacy', 'focused'], default='legacy')
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error('--port must be between 1 and 65535')
    configure()
    os.environ['HUS_ANSWER_POLICY'] = args.answer_policy
    if args.retrieval == 'hybrid':
        from app.hus.retrieval_profile import check_hybrid

        if not args.check:
            print('Checking hybrid v4 index and loading the local embedding model...', flush=True)
        report = check_hybrid(model_cache=args.model_cache, root=ROOT)
        if args.check:
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return
        print('Hybrid ready (LLM off). Open http://127.0.0.1:' + str(args.port), flush=True)
    if args.check:
        report = check(answer_policy='focused') if args.answer_policy == 'focused' else check()
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        import uvicorn

        uvicorn.run('app.hus.demo:app', host='127.0.0.1', port=args.port, workers=1,
                    access_log=False, log_level='warning')


if __name__ == '__main__':
    main()
