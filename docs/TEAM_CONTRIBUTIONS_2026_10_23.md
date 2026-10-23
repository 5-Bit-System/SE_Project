# Team contribution history reconciliation — 2026-10-23

The user requested preserving teammates' original commits on `main`, with pull
requests documenting integration. Earlier selective imports preserved useful
code but did not make the original login/crawler commits ancestors of `main`.
The starting main commit is `0b4b2fc`.

## Database work already present

Both `origin/feat/database-setup-and-tests` and
`origin/feat/vinh-database-tests` are already ancestors of the starting main.
Their original commits and authors are retained; no additional merge or
replacement commits are required. Database work includes contributions under
`23172c43` and `huyvinh005`. Existing Git history is the evidence, even where
the earlier integration did not use a GitHub pull request.

## Login history

Reconcile `origin/feat/login` at `b3964ce`, which has 33 commits not reachable
from the starting main, authored under `23172c43` (including merge commits).
The connector was previously imported selectively from `b790d6a`, then extended
and fixed in the main application's portal integration.

This is an explicit **history-only merge using Git's `ours` merge strategy**:
the source branch is a merge parent, preserving its original commit IDs and
author metadata, while the current main implementation is retained. The only
tree changes in this PR are contribution documentation and project memory.
It does not claim that every source-branch change has been deployed or accepted.
In particular, later source-branch timestamp/merged-head migrations, repository
changes and associated documentation are not adopted by this reconciliation.
They require separate functional review if requested. Because the source tip
becomes an ancestor, Git will consider these historical changes merged; future
adoption must explicitly restore/reapply and review the desired changes.

## Crawler history

The fetched crawler tip is `3a45aae`, with 53 commits not reachable from the
starting main: 43 under `Thang`, and 10 under `Duong Van Tai`. This second
history-only `ours` merge retains the original crawler tip as a merge parent,
preserving all 53 original commits and authors. The current main tree is
retained apart from this documentation and memory. The crawler and RAG remain
inactive; no crawl, trial-data restoration or corpus publication occurs.
The earlier candidate snapshot commit `1f95c3e` and retained local sources are
historical evidence, not evidence of a production corpus or active serving.
Future functional integration requires explicit reapplication and review of
the desired crawler changes because Git will now consider this tip merged.

## Pull requests and validation

- Login: [PR #2](https://github.com/5-Bit-System/SE_Project/pull/2).
- Crawler: [PR #3](https://github.com/5-Bit-System/SE_Project/pull/3), from
  `integration/crawler-history-20261023` to `main`.
- PR #2 was merged as `c73d08f` after all six GitHub checks succeeded. GitHub
  PR records provide the authoritative merge and CI status for both PRs.
- Local offline regression: 398 passed, 39 deselected; one pre-existing
  Starlette/httpx warning. Whole-repository Ruff and `git diff --check` passed.
- Application, database, tests, tools, dependencies and CI files remain exactly
  as at `0b4b2fc`. PostgreSQL checks are delegated to GitHub CI's synthetic
  service databases; no local or production database is accessed.

## Attribution and scope

Original author identities are not rewritten, commits are not manufactured or
squashed, and existing main history is not rebased or force-pushed. GitHub
account attribution depends on the original author email being linked to the
member's account. Commit counts above describe reachable history, including
merge commits, not independently measured work or a grading guarantee.

No live VNU requests, real student-data inspection, environment changes,
database migrations or service restarts are part of this task.
