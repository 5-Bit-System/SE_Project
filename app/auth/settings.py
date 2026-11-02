"""Explicit local/production auth and mail configuration; secrets never appear in repr."""

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, repr=False)
class AuthSettings:
    environment: str
    secret: str
    base_url: str
    allowed_origins: tuple[str, ...]
    mail_backend: str
    mail_host: str
    mail_port: int
    mail_user: str
    mail_password: str
    mail_security: str
    mail_from: str
    idle_seconds: int = 7200
    absolute_seconds: int = 43200
    verification_seconds: int = 1800


@lru_cache
def settings():
    env = {**dotenv_values(ROOT / '.env.auth'), **os.environ}
    environment = env.get('APP_ENV', 'local')
    if environment not in {'local', 'test', 'production'}:
        raise RuntimeError('APP_ENV must be local, test or production')
    secret = env.get('AUTH_TOKEN_PEPPER', '')
    if len(secret) < 32:
        raise RuntimeError('Auth configuration requires a server secret')
    base = env.get('PUBLIC_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')
    url = urlsplit(base)
    if url.scheme not in {'http', 'https'} or not url.hostname or url.username or url.query or url.fragment or url.path:
        raise RuntimeError('Invalid public application origin')
    backend = env.get('EMAIL_BACKEND', 'smtp')
    security = env.get('SMTP_SECURITY', 'none')
    if security not in {'none', 'starttls', 'tls'} or backend not in {'smtp', 'fake'}:
        raise RuntimeError('Invalid mail configuration')
    if environment == 'production' and (url.scheme != 'https' or security == 'none' or backend != 'smtp'):
        raise RuntimeError('Production requires HTTPS and secure SMTP')
    default_origins = base if environment == 'production' else base + ',http://localhost:8000'
    origins = tuple(item.strip() for item in env.get('AUTH_ALLOWED_ORIGINS', default_origins).split(','))
    for origin in origins:
        allowed = urlsplit(origin)
        if (allowed.scheme not in {'http', 'https'} or not allowed.netloc or allowed.username
                or allowed.path or allowed.query or allowed.fragment
                or (environment == 'production' and allowed.scheme != 'https')):
            raise RuntimeError('Invalid allowed application origin')
    return AuthSettings(environment, secret, base,
                        origins,
                        backend, env.get('SMTP_HOST', '127.0.0.1'), int(env.get('SMTP_PORT', '1025')),
                        env.get('SMTP_USERNAME', ''), env.get('SMTP_PASSWORD', ''), security,
                        env.get('MAIL_FROM', 'So hoc tap <noreply@sohoctap.test>'))
