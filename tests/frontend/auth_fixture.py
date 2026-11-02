"""Synthetic verified application account for isolated source/UI checks."""


def session_payload(authenticated=True):
    if not authenticated:
        return {'authenticated': False}
    return {'authenticated': True, 'csrf_token': 'synthetic-browser-csrf', 'account': {
        'account_id': '00000000-0000-4000-8000-000000000001',
        'session_id': '00000000-0000-4000-8000-000000000002',
        'email': None, 'vnu_subject': 'synthetic-only', 'auth_method': 'vnu', 'display_name': 'Synthetic student',
        'role': 'student', 'must_change_password': False, 'expires_in': 7200, 'auth_version': 0}}


EMPTY_PROFILE = {'subject': None, 'profile': {}, 'snapshot': None, 'fetched_at': None, 'last_synced_at': None}
