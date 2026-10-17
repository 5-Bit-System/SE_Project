# Current implementation checklist

Updated 2026-10-17. This tracks the active HUS runtime. Prior milestone records are in [the archive](archive/2026-10-17-prior-checklists.md).

## Delivered

- [x] FastAPI and static browser UI use versioned catalogs from HUS PostgreSQL `ai07` when `DATABASE_MODEL=hus`.
- [x] Four draft catalogs publish through independent HUS migrations and a repeatable publisher.
- [x] Manual transcript, major scoped eligibility, progress, ranking, What-if and course advisor operate through the current API.
- [x] Legacy PostgreSQL schema and configuration remain available for rollback.
- [x] Offline test fixtures are synthetic and separate from catalog source data.

## Remaining product work

- [ ] Review official source material and complete `full_catalog_acceptance`; current HUS catalogs remain `draft_unverified`.
- [ ] Add student authentication and portal transcript synchronization if approved.
- [ ] Add HUS document Q&A/RAG and OCR if approved. The existing course advisor is a separate feature.
- [ ] Verify timetable, offerings and academic rules against official sources before claiming those capabilities.

See [HUS operations](../database/HUS_RUNTIME.md) and [system specification](SYSTEM_SPECIFICATION.md). Historical test counts are snapshots, not current acceptance results.
