# Academic board and UI local integration

This integration merges the three original commits through
`0d6ca10ae60e48cb2d321536df5cbae03026eae6` into local base
`5d7a4df27d855ca4606c75932dd39bcff176062e`, preserving their original authors
and ancestry. It does not publish a branch or change the runtime database.

## Result

- Course-board defaults remain downstream of the prerequisite rule engine.
  Unresolved outcomes cannot become completed or unlock another course.
  No-prerequisite/excluded defaults can enter an advisory plan when the board
  allows planning; missing collection/binding/policy, outside mappings and
  unresolved program selections still prevent planning and saving.
- Current persistent semester plans and session-scoped drafts remain intact.
  A paused board preserves an edited draft while disabling selection and save.
- The source branch's typography, local licensed fonts, themes, navigation,
  ambient background and study-book motion are retained. Motion starts after
  application-session restoration, fits the active page heading and animates
  the current personal semester-plan list.
- Source-sync success feedback requires a completed job and a complete
  saved/unchanged collection. Existing retained-source warnings, epoch guards,
  current-account ownership checks, CSRF and reauthentication remain in place.
- Retired public curriculum lookup, unsupported talented catalog and old student
  authentication flows are not restored. The imported original frontend reports
  describe their source-branch snapshots; this report describes adaptation to
  the current local system.

## Verification in the isolated academic checkout

- 88 focused offline tests passed: board/defaults, personal plan validation/API,
  academic API, binding, CSRF and ownership checks. Seven added regressions cover
  saving defaults without unlocking downstream prerequisites and rejecting both
  empty and populated plans across all global planning gates.
- Four fully intercepted synthetic Chrome scripts passed: `check_course_status`,
  `check_presentation`, `check_motion` and `check_study_desk`. They cover current
  VNU app authentication fixtures, Vietnamese/English, light/dark, 1440/1024/390,
  contrast, keyboard focus, draft preservation, plan effects, source job feedback,
  reduced motion, fallback without the enhancement script and full motion cycles.
- Whole-checkout Ruff, changed JavaScript syntax and Git whitespace checks passed.
- Evidence is ignored under `backups/frontend_polish_20261028/after/`,
  `backups/frontend_motion_20261029/`, `backups/study_desk_motion_20261029/` and
  `backups/local_runtime/course-status/` within this isolated checkout.
  Video capture is optional via `UI_RECORD_VIDEO=1` and requires Playwright ffmpeg;
  this run used screenshots and measured animation samples, without video.

Full combined offline/PostgreSQL/browser verification belongs to the coordinator
after merging Dashboard changes and restoring the pre-existing local overlay.
No real VNU account, personal grades or external email was accessed.
Catalogs remain `draft_unverified`; this integration does not activate RAG.
