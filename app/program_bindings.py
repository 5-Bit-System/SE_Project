"""Account-specific, explicit curriculum confirmation against source enrollment."""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone

from app.academic_catalogs import TALENT_PROGRAM_ID, list_academic_catalogs
from app.academic_policies import POLICY_VERSION
from app.catalog_contracts import digest
from app.curriculum_reference import current_cohort


class ProgramBindingError(ValueError):
    pass


def catalog_fingerprint(catalog) -> str:
    # Preserve the staged context's existing content-addressed revision contract.
    import hashlib
    import json

    return hashlib.sha256(json.dumps(catalog.model_dump(mode="json"), sort_keys=True,
                                    ensure_ascii=False).encode()).hexdigest()


def source_scope(profile: dict) -> str:
    return digest({key: profile.get(key) for key in ("program", "cohort")})


def _fold(value) -> str:
    value = unicodedata.normalize("NFD", str(value or "").casefold())
    value = "".join(char for char in value if unicodedata.category(char) != "Mn")
    return " ".join(value.replace("đ", "d").replace("&", " va ").split())


def source_program_candidates(profile: dict) -> list[str]:
    # Suggestions only. A match never writes a binding without explicit owner confirmation.
    aliases = {
        "toan hoc": ["toan_hoc_7460101_2022", TALENT_PROGRAM_ID],
        "toan hoc chuong trinh chuan": ["toan_hoc_7460101_2022"],
        "toan hoc tai nang": [TALENT_PROGRAM_ID],
        "toan hoc chuong trinh tai nang": [TALENT_PROGRAM_ID],
        "toan tin": ["toan_tin_7460117_2022"],
        "khoa hoc du lieu": ["khdl_7460108_2022"],
        "khoa hoc may tinh va thong tin": ["khmtt_7480113qtd_2022"],
    }
    return aliases.get(_fold(profile.get("program")), [])


def source_program(profile: dict) -> str | None:
    candidates = source_program_candidates(profile)
    return candidates[0] if len(candidates) == 1 else None


def source_cohort(profile: dict) -> int | None:
    value = str(profile.get("cohort") or "").strip()
    match = re.fullmatch(r"[Kk]?\s*(\d{2})", value)
    if match:
        number = int(match[1])
    elif re.fullmatch(r"20\d{2}", value):
        number = 67 + int(value) - 2022
    else:
        return None
    return number if 67 <= number <= current_cohort() else None


def binding_current(profile: dict) -> bool:
    binding = profile.get("academic_binding")
    return isinstance(binding, dict) and (
        binding.get("confirmation_method") != "owner_confirmed_source_enrollment"
        or binding.get("source_scope") == source_scope(profile))


def options(saved: dict) -> dict:
    profile = saved.get("profile") or {}
    snapshot = saved.get("snapshot") or {}
    programs = [{"program_id": catalog.program.program_id, "name": catalog.program.name,
                 "catalog_revision": catalog_fingerprint(catalog),
                 "catalog_status": catalog.program.catalog_status}
                for catalog in list_academic_catalogs()]
    return {"programs": programs, "cohorts": list(range(67, current_cohort() + 1)),
            "suggested_program_id": source_program(profile),
            "program_candidates": source_program_candidates(profile),
            "suggested_cohort": source_cohort(profile),
            "source_program": profile.get("program"), "source_cohort": profile.get("cohort"),
            "source_scope": source_scope(profile), "snapshot_digest": snapshot.get("digest"),
            "policy_version": POLICY_VERSION,
            "policy_source": "/academic-policy/vnu-3626-2022",
            "binding": profile.get("academic_binding") if binding_current(profile) else None}


def confirm(saved: dict, *, program_id: str, cohort: int, expected_catalog_revision: str,
            expected_snapshot_digest: str, expected_source_scope: str) -> dict:
    profile = saved.get("profile") or {}
    snapshot = saved.get("snapshot") or {}
    if not snapshot or snapshot.get("digest") != expected_snapshot_digest:
        raise ProgramBindingError("context_changed")
    if source_scope(profile) != expected_source_scope:
        raise ProgramBindingError("context_changed")
    candidates, source_year = source_program_candidates(profile), source_cohort(profile)
    if not candidates or source_year is None:
        raise ProgramBindingError("source_enrollment_unresolved")
    if program_id not in candidates or source_year != cohort:
        raise ProgramBindingError("academic_program_source_mismatch")
    catalog = next((catalog for catalog in list_academic_catalogs()
                    if catalog.program.program_id == program_id), None)
    if catalog is None:
        raise ProgramBindingError("academic_program_not_supported")
    revision = catalog_fingerprint(catalog)
    if revision != expected_catalog_revision:
        raise ProgramBindingError("context_changed")
    return {"program_id": program_id, "cohort": cohort, "catalog_revision": revision,
            "verified": True, "policy_version": POLICY_VERSION,
            "confirmation_method": "owner_confirmed_source_enrollment",
            "source_scope": expected_source_scope,
            "confirmed_at": datetime.now(timezone.utc).isoformat(),
            "evidence_ref": f"owner-confirmation:{expected_source_scope}:K{cohort}"}
