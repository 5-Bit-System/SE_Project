"""Reproducible Admin browser checks against an explicit disposable database.

Migrate/publish only that test target, set HUS_TEST_DATABASE_URL and TEST_BASE_URL,
then run: python -m tools.verify_admin_console --reset-fixtures [suite ...].
The reset flag authorizes replacing test accounts/revisions/documents, never the
root .env application database. Logs/screenshots remain under ignored backups.
"""
import json
import os
import runpy
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import dotenv_values
from sqlalchemy.engine import make_url

from tests.support.postgres_targets import validate_hus_test_target

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

URL = os.environ.get('HUS_TEST_DATABASE_URL', '')
if not URL:
    raise SystemExit('Set HUS_TEST_DATABASE_URL to an explicitly disposable local ai07 database')
target = validate_hus_test_target(URL)
runtime_url = dotenv_values(ROOT / '.env').get('DATABASE_URL')
if runtime_url:
    runtime = make_url(runtime_url)
    if runtime.host in {'127.0.0.1', 'localhost'} and (target.port or 5432, target.database) == (runtime.port or 5432, runtime.database):
        raise SystemExit('Refusing to reset the configured application database')
BASE_URL = os.environ.get('TEST_BASE_URL', 'http://127.0.0.1:8031')
base = urlsplit(BASE_URL)
if base.hostname != '127.0.0.1' or base.scheme != 'http' or not base.port or base.port == 8000 or base.path:
    raise SystemExit('TEST_BASE_URL must be a separate loopback HTTP port, not the product port8000')
PORT = base.port
OUT = ROOT / 'backups/admin_console_verification' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
OUT.mkdir(parents=True, exist_ok=True)
ENV = os.environ.copy()
ENV.update(DATABASE_URL=URL, HUS_DATABASE_URL=URL, HUS_TEST_DATABASE_URL=URL,
    STORAGE_BACKEND='postgres', DATABASE_MODEL='hus', APP_ENV='test', EMAIL_BACKEND='fake',
    AUTH_TOKEN_PEPPER='synthetic-admin-browser-only-secret-at-least-32-characters',
    PUBLIC_BASE_URL=BASE_URL, AUTH_ALLOWED_ORIGINS=BASE_URL + ',http://127.0.0.1:8000',
    GEMINI_API_KEY='', RECOMMENDATION_LLM_ENABLED='false',
    PYTHONUTF8='1', PYTHONIOENCODING='utf-8', TEST_BASE_URL=BASE_URL)
os.environ.update(ENV)


def seed():
    from sqlalchemy import create_engine, text

    from app.audit.service import log_admin_action
    from app.auth.security import password_hash
    from app.crawler.document_review_service import create_document
    from app.curriculum.repository import (
        publish_revision,
        review_revision,
    )
    eng = create_engine(URL)
    assert eng.url.host == '127.0.0.1' and eng.url.database == 'ai07'
    with eng.begin() as conn:
        conn.execute(text('TRUNCATE accounts CASCADE'))
        conn.execute(text('TRUNCATE curriculum_revisions CASCADE'))
        conn.execute(text('TRUNCATE crawled_documents CASCADE'))
        conn.execute(text('DELETE FROM auth_rate_limits'))
        for name, role in [('admin', 'admin'), ('23001939', 'student')]:
            conn.execute(text('''INSERT INTO accounts
                (username,email,email_normalized,display_name,password_hash,role,email_verified_at,seeded_for_dev,must_change_password)
                VALUES (:name,:email,:email,:display,:password,:role,now(),true,false)'''),
                {'name': name, 'email': 'admin@sohoctap.local' if name == 'admin' else name + '@integration.test', 'display': 'Synthetic ' + name,
                 'password': password_hash('admin123'), 'role': role})
        from tests.support.admin_catalog import complete_draft
        for index in range(2):
            rev = complete_draft(conn, 'Synthetic browser ' + str(index))
            if index == 0:
                review_revision(conn, rev['revision_id'], None, 'approved', 'Synthetic fixture only')
                publish_revision(conn, rev['revision_id'], None, 'Synthetic fixture only')
        for index in range(105):
            create_document(conn, url=f'https://example.invalid/synthetic-{index}', title=f'Synthetic document {index}',
                            markdown_content=f'# Synthetic content {index}', major='toan_hoc', doc_type='curriculum', doc_id=f'integration_doc_{index:03}')
        log_admin_action(conn, actor_id=None, actor_email=None, action='integration:synthetic-fixture', target_type='catalog_revision', target_id='synthetic', summary='Synthetic fixture only')
    eng.dispose()


def run_one(name):
    path = ROOT / 'tests/frontend' / ('check_admin_' + name + '.py')
    runpy.run_path(str(path), run_name='__main__')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--server':
        import uvicorn
        uvicorn.run('app.main:app', host='127.0.0.1', port=PORT, log_level='warning')
    elif len(sys.argv) > 1 and sys.argv[1] == '--one':
        run_one(sys.argv[2])
    else:
        if '--reset-fixtures' not in sys.argv:
            raise SystemExit('Pass --reset-fixtures to authorize resetting this disposable test database')
        seed()
        suites = [arg for arg in sys.argv[1:] if arg != '--reset-fixtures'] or ['shell', 'overview', 'curriculum', 'workflow', 'rules', 'import', 'documents', 'users', 'health_metrics', 'synthetic_preview', 'announcements', 'audit', 'provenance', 'session_races']
        results = []
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        with (OUT / 'admin-server.log').open('w', encoding='utf-8') as log:
            server = subprocess.Popen([sys.executable, '-m', 'tools.verify_admin_console', '--server'], cwd=ROOT, env=ENV,
                                      stdout=log, stderr=subprocess.STDOUT, creationflags=creationflags)
            try:
                for attempt in range(40):
                    if server.poll() is not None:
                        raise RuntimeError('Temporary server exited')
                    try:
                        with urllib.request.urlopen(BASE_URL + '/health', timeout=1) as response:
                            assert response.status == 200
                        break
                    except OSError:
                        time.sleep(0.25)
                else:
                    raise RuntimeError('Temporary server did not become ready')
                from sqlalchemy import create_engine, text
                eng = create_engine(URL)
                for name in suites:
                    with eng.begin() as conn:
                        conn.execute(text('DELETE FROM auth_rate_limits'))
                    print('RUN admin-' + name, flush=True)
                    started = time.monotonic()
                    with (OUT / ('browser-' + name + '.log')).open('w', encoding='utf-8') as stream:
                        try:
                            completed = subprocess.run([sys.executable, '-m', 'tools.verify_admin_console', '--one', name], cwd=ROOT, env=ENV,
                                                       stdout=stream, stderr=subprocess.STDOUT, timeout=90)
                            code = completed.returncode
                        except subprocess.TimeoutExpired:
                            code = 124
                    results.append({'suite': name, 'exit_code': code, 'seconds': round(time.monotonic() - started, 1)})
                    print(json.dumps(results[-1]), flush=True)
                    (OUT / 'admin-browser-results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
                    if code:
                        print((OUT / ('browser-' + name + '.log')).read_text(encoding='utf-8')[-2000:], flush=True)
                eng.dispose()
            finally:
                server.terminate()
                try:
                    server.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait(timeout=10)
        raise SystemExit(any(item['exit_code'] for item in results))
