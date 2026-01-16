---
phase: 08-fix-mypy-type-errors-for-ci
plan: 02
subsystem: infra
tags: [mypy, types, type-annotations, flask, sqlalchemy, scapy]

# Dependency graph
requires:
  - phase: 08-01
    provides: mypy configuration for untyped third-party libraries
provides:
  - Zero mypy errors in all source files
  - Proper type annotations for push.py, discovery.py, scanner.py, web/app.py, cli.py
  - Fixed Host.ip_addresses model type from dict to list[str]
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: [Response return types for Flask routes, dict comprehension for SQLAlchemy Row conversion]

key-files:
  created: []
  modified: [src/netbox_auto/push.py, src/netbox_auto/discovery.py, src/netbox_auto/models.py, src/netbox_auto/collectors/scanner.py, src/netbox_auto/web/app.py, src/netbox_auto/cli.py]

key-decisions:
  - "Use NetBoxClient instead of function reference for type annotation"
  - "Rename collector variables to be type-specific to avoid variable type conflicts"
  - "Fix Host.ip_addresses type from dict[str, Any] to list[str] to match actual usage"
  - "Use type: ignore[attr-defined] for scapy dynamic imports"
  - "Use werkzeug.wrappers.Response for Flask route return types"
  - "Use dict comprehension instead of dict() for SQLAlchemy Row conversion"

patterns-established:
  - "Flask routes returning redirect should have -> Response return type"
  - "Use hasattr check before calling methods on union types"

# Metrics
duration: 5min
completed: 2026-01-16
---

# Phase 8 Plan 2: Fix source code type errors Summary

**Fixed all 21 mypy type errors across 6 source files by adding proper type annotations, fixing model types, and using appropriate type ignore comments for dynamic imports**

## Performance

- **Duration:** 5 min
- **Started:** 2026-01-16T07:28:00Z
- **Completed:** 2026-01-16T07:33:05Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- Reduced mypy errors from 21 to 0 across all source files
- Fixed push.py and discovery.py type annotations (Session, NetBoxClient, Config imports)
- Fixed Host.ip_addresses model type annotation from dict[str, Any] to list[str]
- Fixed scanner.py scapy imports with type: ignore and Any types
- Fixed web/app.py Flask route return types with Response
- Fixed cli.py dict comprehensions and strftime attribute access

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix push.py and discovery.py type errors** - `dc1193e` (fix)
2. **Task 2: Fix remaining module type errors** - `294b132` (fix)

## Files Created/Modified

- `src/netbox_auto/push.py` - Added Session and NetBoxClient imports, fixed parameter types
- `src/netbox_auto/discovery.py` - Added Session and Config imports, renamed collector variables
- `src/netbox_auto/models.py` - Fixed ip_addresses type from dict[str, Any] to list[str]
- `src/netbox_auto/collectors/scanner.py` - Added Any import, fixed scapy parameter types, added type: ignore
- `src/netbox_auto/web/app.py` - Added Response import, fixed route return types
- `src/netbox_auto/cli.py` - Fixed dict comprehensions and strftime attribute check

## Decisions Made

1. **Fix Host.ip_addresses type** - Changed from dict[str, Any] to list[str] since the field stores IP addresses as a list, not a dict
2. **Use type: ignore for scapy** - Scapy dynamic imports don't have proper type stubs, suppressed with targeted ignore
3. **Use Response for Flask redirects** - Flask redirect() returns werkzeug.wrappers.Response, not object
4. **Use hasattr for strftime** - Safer pattern than isinstance for checking datetime method availability

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed Host.ip_addresses type annotation**
- **Found during:** Task 1 (push.py and discovery.py type errors)
- **Issue:** Host.ip_addresses was typed as Mapped[dict[str, Any]] but code treats it as list[str]
- **Fix:** Changed to Mapped[list[str]] and added list[str]: JSON to type_annotation_map
- **Files modified:** src/netbox_auto/models.py
- **Verification:** mypy passes, tests pass
- **Committed in:** dc1193e

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Necessary fix discovered during type checking. The model type was incorrect.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All mypy errors resolved (0 errors in 18 source files)
- `make type` passes
- `make ci` passes (format + lint + type + test)
- CI pipeline type check step will now pass
- Phase 8 complete

---
*Phase: 08-fix-mypy-type-errors-for-ci*
*Completed: 2026-01-16*
