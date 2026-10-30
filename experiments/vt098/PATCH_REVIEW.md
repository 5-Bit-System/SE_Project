# Review before accepting the VT-098 corrective patch

This is the coding agent's source-backed self-review, not a claim that the
student or another human independently approved it. Read this diff personally
before requesting team review. Nothing has been merged into main.

The actual diff is preserved in `evidence/patch.diff` relative to red commit
`a20c996f65b017b4dc1a2e3d9b692a25fec42f94`. Only `harness.py` changes behavior:
27 added lines, 8 removed lines. The reviewed test file is identical in red/green.

| Diff decision | Why accepted in the harness | Evidence / limit |
|---|---|---|
| Digest key; fingerprint normalized body | Object order/defaults do not create a new intent; changed body with same key is rejected | Real schema loader and canonicalization/conflict tests; cryptographic collision freedom is not proved |
| Lookup receipt inside `BEGIN IMMEDIATE` | Two connections cannot both observe absence and insert duplicate business data | Pairwise subcases run through separate SQLite connections; not PostgreSQL row locks |
| Composite scope includes account and operation | The same key for B cannot replay A's response | Account-isolation pairwise cases; account authentication is outside this harness |
| Replay before current basis/quota check | A committed receipt is a historical result, not a new write; retry at quota 100 must still work | Current-basis and quota tests; no new academic claims |
| Insert plan, business audit and receipt before commit | Errors after each write roll everything back; lost return value after commit replays durable receipt | Fault-injection tests, independent SQL counts; no OS kill or remote-service transaction |
| Keep receipt when plan is deleted | Retry cannot resurrect the deleted resource | Direct SQL deletion fixture; DELETE API behavior remains untested |

Rejected simplifications: a process cache, title/body-only deduplication, returning
201 without matching the original response, and mocking away database writes.
The initial two weak AI test methods are visible at `9b18b7d`; their reviewed
replacements are visible at `a20c996`, before the corrective code exists.

Before the patch commit: inspect the diff, confirm all 18 unchanged reviewed test
methods pass, verify red/green test hashes match, and run Ruff on this experiment.
No mutation, coverage or 150-task test belongs to requirement 3; these are pending.
