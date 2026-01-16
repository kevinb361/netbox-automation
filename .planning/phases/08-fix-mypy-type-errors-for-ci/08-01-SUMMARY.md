---
phase: 08-fix-mypy-type-errors-for-ci
plan: 01
subsystem: infra
tags: [mypy, types, type-stubs, paramiko]

# Dependency graph
requires:
  - phase: 07-ci-pipeline
    provides: GitHub Actions CI workflow requiring type checks
provides:
  - types-paramiko stub package
  - mypy configuration for untyped third-party libraries
  - import-untyped error suppression
affects: [08-02-code-type-fixes]

# Tech tracking
tech-stack:
  added: [types-paramiko]
  patterns: [disable_error_code for untyped libraries]

key-files:
  created: []
  modified: [pyproject.toml]

key-decisions:
  - "Used disable_error_code=[import-untyped] globally instead of per-module"
  - "Keep ignore_missing_imports per-module for proper import resolution"

patterns-established:
  - "Untyped third-party libraries handled via disable_error_code + ignore_missing_imports"

# Metrics
duration: 3min
completed: 2026-01-16
---

# Phase 8 Plan 1: Configure mypy for untyped libraries Summary

**Added types-paramiko stubs and configured mypy to disable import-untyped errors for pynetbox, librouteros, proxmoxer, scapy, and flask**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-16T07:22:28Z
- **Completed:** 2026-01-16T07:25:32Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- Installed types-paramiko stub package for paramiko type checking
- Configured mypy with disable_error_code=["import-untyped"] globally
- Added ignore_missing_imports overrides for pynetbox, librouteros, proxmoxer, scapy, flask
- Reduced mypy errors from 29 to 21 (all import-untyped errors resolved)

## Task Commits

Each task was committed atomically:

1. **Task 1: Install type stubs** - `399f285` (chore)
2. **Task 2: Configure mypy overrides for untyped libraries** - `0f67fad` (chore)

## Files Created/Modified

- `pyproject.toml` - Added types-paramiko to dev deps, added mypy disable_error_code and module overrides

## Decisions Made

1. **Used disable_error_code globally** - Cleaner than per-module overrides for import-untyped error
2. **Keep ignore_missing_imports per-module** - Maintains explicit list of untyped libraries for documentation

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- mypy import errors resolved, actual code type errors now visible
- Ready for 08-02-PLAN.md to fix remaining 21 code type errors
- All errors are in 6 files: dns.py, push.py, scanner.py, discovery.py, web/app.py, cli.py

---
*Phase: 08-fix-mypy-type-errors-for-ci*
*Completed: 2026-01-16*
