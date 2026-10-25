"""Explicit, idempotent local bootstrap. Credentials are never written to Git/stdout."""

import argparse
import os
import secrets
import subprocess
import uuid
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import make_url

from app.auth.repository import engine
from app.auth.security import password_hash
from app.auth.settings import ROOT, settings

ACCOUNTS = [('admin@sohoctap.test', 'admin', 'Local administrator'),
            ('student@sohoctap.test', 'student', 'Local student')]


def seed(output):
    config = settings()
    url = make_url(str(engine().url.render_as_string(hide_password=False)))
    allowed_database = url.database == 'ai07' or (config.environment == 'test' and url.database.startswith('ai07_runtime_test_'))
    if config.environment not in {'local', 'test'} or url.host not in {'127.0.0.1', 'localhost'} or not allowed_database:
        raise RuntimeError('Development seed is restricted to local ai07')
    output = Path(output).resolve()
    backup_root = (ROOT / 'backups').resolve()
    if not output.is_relative_to(backup_root):
        raise RuntimeError('Private credential output must be inside ignored backups/')
    output.parent.mkdir(parents=True, exist_ok=True)
    created, values = [], []
    try:
        with engine().begin() as conn:
            conn.execute(text('SELECT pg_advisory_xact_lock(18107025)'))
            for email, role, name in ACCOUNTS:
                prior = conn.execute(text('SELECT * FROM accounts WHERE email_normalized=:email'), {'email': email}).mappings().one_or_none()
                if prior:
                    if not prior['seeded_for_dev'] or prior['role'] != role:
                        raise RuntimeError('Seed identity conflicts with an existing account')
                    continue
                account_id, password = str(uuid.uuid4()), secrets.token_urlsafe(24)
                conn.execute(text("""INSERT INTO accounts
                    (username,id,email,email_normalized,display_name,password_hash,role,
                     email_verified_at,seeded_for_dev,must_change_password)
                    VALUES(:username,:id,:email,:email,:name,:password,:role,now(),true,true)"""),
                             {'username': 'local:' + account_id, 'id': account_id, 'email': email,
                              'name': name, 'password': password_hash(password), 'role': role})
                created.append(email)
                values.append(f'{role}: {email}\nTemporary password: {password}\n')
            if values:
                with output.open('x', encoding='utf-8') as private:
                    if os.name == 'nt':
                        user = subprocess.check_output(['whoami'], text=True).strip()
                        subprocess.run(['icacls', str(output), '/inheritance:r', '/grant:r', user + ':F'],
                                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    else:
                        output.chmod(0o600)
                    private.write('LOCAL TEST ACCOUNTS ONLY. Change the temporary password after first login.\n\n'
                                  + '\n'.join(values))
    except Exception:
        # Do not overwrite a prior handoff or reset existing credentials.
        raise
    return len(created)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default=str(ROOT / 'backups' / 'system_auth_20261025' / 'accounts.private.txt'))
    args = parser.parse_args()
    count = seed(args.output)
    print(f'Local system account seed complete: {count} created; existing credentials preserved.')
    if count:
        print('Private credential file: ' + str(Path(args.output).resolve()))


if __name__ == '__main__':
    main()
