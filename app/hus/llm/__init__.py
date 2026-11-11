"""Optional HUS Q&A LLM adapter; importing this package performs no I/O."""

from .client import HUSLLMClient, HUSLLMError
from .config import HUSLLMSettings

__all__ = ['HUSLLMClient', 'HUSLLMError', 'HUSLLMSettings']
