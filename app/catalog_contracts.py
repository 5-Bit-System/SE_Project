"""Stable HUS runtime identifiers and snapshot integrity helpers."""

from __future__ import annotations

import hashlib
import json

from app.models import Catalog

MAJOR_PROGRAM_IDS = {
    "7460101": "toan_hoc_7460101_2022",
    "7460117": "toan_tin_7460117_2022",
    "7460108": "khdl_7460108_2022",
    "7480113QTD": "khmtt_7480113qtd_2022",
}
PROGRAM_MAJOR_IDS = {value: key for key, value in MAJOR_PROGRAM_IDS.items()}
EXPECTED_PROGRAM_IDS = frozenset(PROGRAM_MAJOR_IDS)


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def catalog_payload(catalog: Catalog) -> dict:
    return catalog.model_dump(mode="json", exclude_none=False)


def catalog_revision(catalog: Catalog, source_digest: str) -> str:
    return digest({"catalog": catalog_payload(catalog), "source_digest": source_digest})
