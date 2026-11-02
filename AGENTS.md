# Repository Guidelines

The detailed project memory and contributor instructions are maintained in [`.agent/AGENTS.md`](.agent/AGENTS.md). Read that file before making changes, and consult the referenced documents only when the task requires them.

When the user asks to use `project-toolkit`, read its local `SKILL.md` if available and select the relevant skill while preserving the requested scope and mode. The toolkit is local-only and excluded from Git; a fresh clone does not include it.

## Pull requests and team attribution

All future changes to `main`, including documentation, must go through a feature
branch and a GitHub pull request. Merge with **Create a merge commit** so team
members' original commits and authors remain in `main` history. Do not squash,
rebase-merge, or replace teammates' contributions with copied code committed only
under the integrator's identity. Preserve genuine author metadata; do not invent
commits or authorship. See `.agent/AGENTS.md` for the full workflow and exceptions.
