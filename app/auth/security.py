"""Password and purpose-separated random-token primitives."""

import hashlib
import hmac
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from email_validator import EmailNotValidError, validate_email

from app.auth.settings import settings

hasher = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)
DUMMY = hasher.hash(secrets.token_urlsafe(32))


class AuthFailure(Exception):
    def __init__(self, code, status=400):
        self.code, self.status = code, status
        super().__init__(code)


def email_address(value):
    if not isinstance(value, str) or len(value) > 254:
        raise AuthFailure('invalid_email')
    try:
        parsed = validate_email(value.strip(), check_deliverability=False,
                                test_environment=settings().environment in {'test', 'local'})
        return parsed.normalized, parsed.normalized.lower()
    except EmailNotValidError:
        raise AuthFailure('invalid_email') from None


def password_hash(value):
    if not isinstance(value, str) or not 6 <= len(value) <= 128:
        raise AuthFailure('weak_password')
    if value.lower() in {'passwordpassword', '123456789012345', 'qwertyuiopasdfgh'}:
        raise AuthFailure('weak_password')
    return hasher.hash(value)


def password_matches(encoded, value):
    try:
        return hasher.verify(encoded or DUMMY, value)
    except (VerificationError, InvalidHashError, TypeError):
        return False


def digest(value, purpose='session'):
    return hmac.new(settings().secret.encode(), (purpose + ':' + value).encode(), hashlib.sha256).hexdigest()


def token():
    return secrets.token_urlsafe(32)


def csrf(value):
    return digest(value, 'csrf')
