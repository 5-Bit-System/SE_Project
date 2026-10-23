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

## Crawler history pending

The fetched crawler tip is `3a45aae`, with 53 commits not reachable from the
starting main: 43 under `Thang`, and 10 under `Duong Van Tai`. Reconcile this
history separately with the same explicit history-only scope. The crawler and
RAG remain inactive; no crawl, trial-data restoration or corpus publication is
authorized by this history task.

## Attribution and scope

Original author identities are not rewritten, commits are not manufactured or
squashed, and existing main history is not rebased or force-pushed. GitHub
account attribution depends on the original author email being linked to the
member's account. Commit counts above describe reachable history, including
merge commits, not independently measured work or a grading guarantee.

No live VNU requests, real student-data inspection, environment changes,
database migrations or service restarts are part of this task.
