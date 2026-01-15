---
phase: 02-discovery
plan: 04
subsystem: collectors
tags: [mikrotik, switch, mac-table, librouteros]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: config system, models
provides:
  - SwitchCollector for MAC-to-port mapping
  - SwitchConfig model for switch credentials
affects: [05-correlation, orchestrator]

# Tech tracking
tech-stack:
  added: []
  patterns: [dual-path API query (bridge/switch host tables)]

key-files:
  created: [src/netbox_auto/collectors/switch.py]
  modified: [src/netbox_auto/config.py, src/netbox_auto/collectors/__init__.py]

key-decisions:
  - "SwitchCollector returns dict, not DiscoveredHost list - enrichment pattern"
  - "Try bridge host table first, fall back to switch host table"

patterns-established:
  - "Enrichment collectors return data for correlation, not host lists"

# Metrics
duration: 4min
completed: 2026-01-15
---

# Phase 2 Plan 4: MikroTik Switch MAC Table Collector Summary

**SwitchCollector queries MikroTik switches for MAC-to-port mappings to enable switch port correlation for discovered hosts.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-01-15T23:26:15Z
- **Completed:** 2026-01-15T23:31:03Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- SwitchCollector implementation for querying MikroTik switch MAC tables
- SwitchConfig model supporting multiple switches with friendly names
- Dual-path API query (bridge host table for CRS series, switch host table for older)
- Graceful error handling with logging for connection failures

## Task Commits

Each task was committed atomically:

1. **Task 1: Add switch configuration** - `71e7f7f` (included in 02-03 commit due to wave 1 parallel execution)
2. **Task 2: Implement switch MAC table collector** - `83ee3bb` (feat)

_Note: Task 1 changes were committed alongside 02-03's ScannerConfig since both modified config.py in wave 1 parallel execution._

## Files Created/Modified

- `src/netbox_auto/collectors/switch.py` - SwitchCollector implementation with MAC table queries
- `src/netbox_auto/config.py` - SwitchConfig model and switches list in Config (committed with 02-03)
- `src/netbox_auto/collectors/__init__.py` - Export SwitchCollector

## Decisions Made

- **Enrichment pattern vs Collector protocol:** SwitchCollector returns `dict[str, str]` (MAC -> switch_name:port) rather than implementing the Collector protocol. This is because switch data enriches existing hosts rather than discovering new ones.
- **Dual API path:** Try `/interface/bridge/host` first (CRS/hAP series), fall back to `/interface/ethernet/switch/host` (older switches) for compatibility.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Next Phase Readiness

- SwitchCollector ready for integration with discovery orchestrator
- MAC-to-port mappings can be used to enrich DiscoveredHost.switch_port field
- Ready for 02-05-PLAN.md (correlation orchestrator)

---
*Phase: 02-discovery*
*Completed: 2026-01-15*
