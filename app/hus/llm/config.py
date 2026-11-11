"""Explicit LLM settings, independent of recommendation and root .env loading."""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field

import httpx


@dataclass(frozen=True)
class HUSLLMSettings:
    enabled: bool = False
    base_url: str = 'https://generativelanguage.googleapis.com/v1beta/openai'
    model: str = 'gemini-3.5-flash-lite'
    api_key: str = field(default='', repr=False)

    def __post_init__(self) -> None:
        if type(self.enabled) is not bool:
            raise ValueError('HUS_LLM_ENABLED must be a boolean')
        if (not isinstance(self.base_url, str)
                or any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in self.base_url)
                or '?' in self.base_url or '#' in self.base_url):
            raise ValueError('HUS_LLM_BASE_URL must be an absolute HTTP(S) URL')
        try:
            url = httpx.URL(self.base_url)
            valid_url = (url.scheme in {'http', 'https'} and bool(url.host)
                         and not url.userinfo
                         and (url.port is None or 0 < url.port <= 65535))
        except httpx.InvalidURL:
            valid_url = False
        if not valid_url:
            raise ValueError('HUS_LLM_BASE_URL must be an absolute HTTP(S) URL without credentials, '
                             'query or fragment')
        if (not isinstance(self.model, str) or not self.model
                or any(c.isspace() or ord(c) < 32 for c in self.model)):
            raise ValueError('HUS_LLM_MODEL must be a nonempty model ID')
        if (not isinstance(self.api_key, str) or not self.api_key.isascii()
                or any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in self.api_key)
                or (self.enabled and not self.api_key)):
            raise ValueError('HUS_LLM_API_KEY must be a valid key when enabled')

    @classmethod
    def read_enabled(cls, environ: Mapping[str, str] | None = None) -> bool:
        """Read just the enable flag so disabled paths need no model/key configuration."""
        env = os.environ if environ is None else environ
        raw_enabled = env.get('HUS_LLM_ENABLED', 'false')
        if not isinstance(raw_enabled, str):
            raise ValueError('HUS_LLM_ENABLED must be true or false')
        value = raw_enabled.strip().lower()
        if value not in {'true', 'false', '1', '0', 'yes', 'no', 'on', 'off'}:
            raise ValueError('HUS_LLM_ENABLED must be true or false')
        return value in {'true', '1', 'yes', 'on'}

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> 'HUSLLMSettings':
        """Read only HUS_LLM_*; never load .env or reuse GEMINI_* settings."""
        env = os.environ if environ is None else environ
        return cls(enabled=cls.read_enabled(env),
                   base_url=env.get('HUS_LLM_BASE_URL', cls.base_url),
                   model=env.get('HUS_LLM_MODEL', cls.model),
                   api_key=env.get('HUS_LLM_API_KEY', ''))


def llm_rewrite_available() -> bool:
    """Safe UI capability only; its consent text promises direct HTTPS to Google."""
    try:
        if not HUSLLMSettings.read_enabled():
            return False
        settings = HUSLLMSettings.from_env()
        url = httpx.URL(settings.base_url)
        return (url.scheme == 'https' and url.host == 'generativelanguage.googleapis.com'
                and settings.api_key not in settings.model)
    except ValueError:
        return False
