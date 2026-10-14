"""Các schema Pydantic của ứng dụng.

Imports are lazy to avoid a circular dependency chain:
  catalog_normalization → schemas.metadata → schemas/__init__ → schemas.profile
  → profiles → catalog → json_catalog_repository → catalog_normalization
"""


def __getattr__(name: str):
    if name == "ProgramCatalogMetadata":
        from app.schemas.catalog import ProgramCatalogMetadata

        return ProgramCatalogMetadata
    if name in ("ProfileDetail", "ProfileSummary", "TranscriptSummary"):
        from app.schemas import profile as _profile

        return getattr(_profile, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "ProfileDetail",
    "ProfileSummary",
    "ProgramCatalogMetadata",
    "TranscriptSummary",
]
