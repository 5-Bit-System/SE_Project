"""Opt-in real browser proof in a disposable PostgreSQL database.

Uses synthetic identities and an isolated database. Never contacts VNU or sends mail.
Run: .venv/Scripts/python.exe -m tests.frontend.check_system_auth
"""
import os
import secrets
import socket
import threading
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import uvicorn
from playwright.sync_api import sync_playwright

from app.config import get_settings


def main():
    target = get_settings().database_url
    if not target:
        raise RuntimeError('A local PostgreSQL target is required')
    evidence = Path('backups/system_auth_20261025/browser_' + uuid.uuid4().hex[:10])
    evidence.mkdir(parents=True)
    with socket.socket() as available:
        available.bind(('127.0.0.1', 0))
        port = available.getsockname()[1]
    base = f'http://127.0.0.1:{port}'
    environment = {'HUS_TEST_DATABASE_URL': target, 'APP_ENV': 'test', 'STORAGE_BACKEND': 'json',
                   'AUTH_TOKEN_PEPPER': secrets.token_urlsafe(48), 'PUBLIC_BASE_URL': base,
                   'AUTH_ALLOWED_ORIGINS': base, 'EMAIL_BACKEND': 'fake', 'SMTP_HOST': '127.0.0.1',
                   'SMTP_PORT': '1025', 'SMTP_SECURITY': 'none'}
    with patch.dict(os.environ, environment):
        from app.auth import repository
        from app.auth.settings import settings
        from app.integrations.daotao import runtime, store
        from app.integrations.daotao.snapshot import snapshot
        from app.main import app
        from database.tools import seed_system_accounts as seeder
        from tests.database.test_hus_migration_runtime import runtime_engine
        from tests.support.catalog_fixtures import create_catalog_fixture
        catalogs, _ = create_catalog_fixture(evidence / 'synthetic')
        get_settings.cache_clear()
        settings.cache_clear()
        source_failure = [False]

        async def collect(value):
            subject = value.get('subject', value.get('username'))
            if source_failure[0]:
                return {'authenticated': True, 'subject': subject, 'snapshot': None,
                        'warning': 'source_unavailable', 'cookies': []}
            return {'authenticated': True, 'subject': subject, 'snapshot': snapshot([['1', 'TEST001', 'Synthetic only', '3', '8', 'B', '3']]),
                    'profile': {'name': 'Synthetic student', 'program': None, 'cohort': None},
                    'cookies': [{'name': 'synthetic', 'value': 'private-synthetic-browser-cookie',
                                 'domain': 'daotao.vnu.edu.vn', 'path': '/dkmh/', 'expires': -1}]}

        with contextmanager(runtime_engine.__wrapped__)() as engine, \
                patch.object(repository, 'engine', lambda: engine), patch.object(store, 'engine', lambda: engine), \
                patch.object(seeder, 'engine', lambda: engine), patch('app.catalog.DATA_ROOT', catalogs), \
                patch.object(runtime, 'collect', collect):
            handoff = evidence / 'accounts.private.txt'
            assert seeder.seed(handoff) == 2
            assert seeder.seed(handoff) == 0
            temporary = handoff.read_text(encoding='utf-8').split('Temporary password: ')[1].splitlines()[0]
            server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=port, access_log=False, log_level='warning'))
            thread = threading.Thread(target=server.run, daemon=True)
            thread.start()
            try:
                for _ in range(100):
                    if server.started:
                        break
                    time.sleep(.05)
                assert server.started
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch(channel='chrome', headless=True)
                    try:
                        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
                        errors, personal = [], []
                        page.on('pageerror', lambda error: errors.append(str(error)))
                        page.on('request', lambda request: personal.append(request.url) if '/me/profile' in request.url else None)
                        page.route('**/*', lambda route: route.continue_() if route.request.url.startswith(base) else route.abort())
                        page.goto(base)
                        page.locator('#auth-student-form').wait_for(state='visible')
                        assert page.locator('.main-content').is_hidden() and not personal
                        assert page.locator('#auth-register-form').count()==0
                        assert page.locator('#auth-register-tab').count()==0
                        password='Syn6!x'
                        submissions=[]
                        page.on('request',lambda request: submissions.append(request.url) if request.method=='POST' else None)

                        def student_login():
                            page.locator('#auth-student-tab').click()
                            page.locator('#auth-vnu-username').fill('synthetic-browser-vnu')
                            page.locator('#auth-vnu-password').fill('synthetic-vnu-password')
                            page.locator('#auth-student-form button[type=submit]').click()

                        def admin_login(secret):
                            page.locator('#auth-login-tab').click()
                            page.locator('#auth-login-email').fill('admin@sohoctap.test')
                            page.locator('#auth-login-password').fill(secret)
                            page.locator('#auth-login-form button[type=submit]').click()

                        student_login()
                        page.wait_for_function("document.body.dataset.authState === 'workspace'")
                        assert sum(url.endswith('/auth/vnu') for url in submissions)==1
                        assert not any(url.endswith('/me/portal-connection') or url.endswith('/auth/login') for url in submissions)
                        assert page.locator('#system-password').is_hidden()
                        assert page.locator('#system-admin-open').is_hidden()
                        assert page.request.get(base+'/admin/users').status==403
                        page.locator('#tab-btn-profile').click()
                        page.locator('#portal-profile').wait_for(state='visible')
                        assert page.locator('#portal-login').is_hidden()
                        assert page.locator('#auth-vnu-password').input_value()==''
                        page.locator('#portal-sync').click()
                        page.wait_for_function("!document.getElementById('portal-sync').disabled")
                        assert page.locator('#portal-reauth').is_hidden()
                        page.reload()
                        page.wait_for_function("document.body.dataset.authState === 'workspace'")
                        page.locator('#tab-btn-profile').click()
                        page.locator('#portal-profile').wait_for(state='visible')
                        assert 'synthetic-browser-vnu' in page.locator('#system-account-name').inner_text()
                        page.locator('#system-logout').click()
                        page.locator('#auth-student-form').wait_for(state='visible')
                        assert page.locator('#portal-identity').inner_text()==''
                        source_failure[0] = True
                        student_login()
                        page.locator('#portal-profile').wait_for(state='visible')
                        page.wait_for_function("document.getElementById('portal-status').textContent.includes('ch\\u01b0a t\\u1ea3i')")
                        assert page.locator('#portal-status').is_visible()
                        assert page.locator('#portal-login').is_hidden()
                        source_failure[0] = False
                        page.locator('#system-logout').click()
                        page.locator('#auth-student-form').wait_for(state='visible')
                        admin_login(temporary)
                        page.locator('#auth-password-form').wait_for(state='visible')
                        assert page.locator('#system-admin-open').is_hidden()
                        for key,value in [('current-password',temporary),('new-password',password),('new-confirm',password)]:
                            page.locator('#auth-'+key).fill(value)
                        page.locator('#auth-password-form button[type=submit]').click()
                        page.locator('#system-admin-open').wait_for(state='visible')
                        page.locator('#system-admin-open').click()
                        page.locator('#admin-users tbody tr').first.wait_for(state='visible')
                        assert page.locator('#admin-users tbody tr').count()==3
                        assert 'password_hash' not in page.locator('#admin-users').inner_text()
                        page.set_viewport_size({'width':390,'height':844})
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                        page.screenshot(path=str(evidence/'admin-mobile.png'),full_page=True)
                        page.on('dialog',lambda dialog:dialog.accept())
                        row=page.locator('#admin-users tbody tr').filter(has_text='synthetic-browser-vnu')
                        row.locator('button').click()
                        page.wait_for_function("document.querySelector('#admin-users tbody').textContent.includes('kh\u00f3a')")
                        page.locator('#system-logout').click()
                        page.locator('#auth-student-form').wait_for(state='visible')
                        student_login()
                        page.wait_for_function("document.getElementById('auth-notice').classList.contains('is-error')")
                        assert page.locator('.main-content').is_hidden()
                        assert page.locator('#auth-vnu-password').input_value()==''
                        for language in ['en','vi']:
                            page.locator(f'[data-language-choice="{language}"]').click()
                            assert page.locator('#auth-student-tab').inner_text()==('VNU student' if language=='en' else 'Sinh vi\u00ean VNU')
                        page.locator('[data-theme-choice="dark"]').click()
                        page.screenshot(path=str(evidence/'auth-mobile.png'),full_page=True)
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                        page.locator('[data-theme-choice="light"]').click()
                        page.set_viewport_size({'width':1440,'height':1000})
                        page.screenshot(path=str(evidence/'auth-desktop.png'),full_page=True)
                        assert not errors
                    finally:
                        browser.close()
            finally:
                server.should_exit = True
                thread.join(timeout=15)
                if thread.is_alive():
                    raise RuntimeError('Synthetic browser server did not stop')
    get_settings.cache_clear()
    print('Browser passed: one VNU sign-in, no email registration/second connection, session reload, admin login/password/disable, sync, logout cleanup, VI/EN and mobile.')
    print('Synthetic screenshot: ' + str(evidence / 'auth-mobile.png'))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        import traceback
        location = traceback.extract_tb(error.__traceback__)[-1]
        # Do not echo tokens, verification URLs, credentials or browser traces.
        print('Browser proof failed at stage: ' + type(error).__name__)
        frames = [frame for frame in traceback.extract_tb(error.__traceback__) if frame.filename == __file__]
        print('Test line: ' + str(frames[-1].lineno if frames else location.lineno))
        raise SystemExit(1) from None
