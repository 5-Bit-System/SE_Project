"""Errors shared across storage adapters and API boundaries."""


class CatalogError(ValueError):
    """The requested catalog does not exist."""


class StorageUnavailable(RuntimeError):
    """Storage cannot be reached; messages must not contain credentials."""


class StorageDataError(RuntimeError):
    """Stored server data is invalid or has not been initialized."""
