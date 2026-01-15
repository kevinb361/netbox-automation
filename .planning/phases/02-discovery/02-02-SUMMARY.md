---
phase: 02-discovery
plan: 02
subsystem: collectors
tags: [proxmox, proxmoxer, vm-discovery, qemu-agent]

requires:
  - phase: 02-01
    provides: Collector protocol and DiscoveredHost dataclass
provides:
  - ProxmoxCollector for VM inventory discovery
  - MAC address extraction from Proxmox VM network configs
  - IP address retrieval from QEMU guest agent
affects: [02-05, discovery-orchestration]

tech-stack:
  added: [proxmoxer>=2.0, requests>=2.0]
  patterns: [collector-protocol]

key-files:
  created: [src/netbox_auto/collectors/proxmox.py]
  modified: [pyproject.toml, src/netbox_auto/collectors/__init__.py]

key-decisions:
  - "Use regex to extract MAC from Proxmox net config format"
  - "Query QEMU guest agent for IP addresses when available"
  - "Return empty list on connection/auth errors (graceful degradation)"

duration: 5 min
completed: 2026-01-15
---

# Phase 2 Plan 02: Proxmox Collector Summary

**ProxmoxCollector implementation using proxmoxer library with MAC extraction and QEMU agent IP retrieval**

## Performance

- **Duration:** 5 min
- **Started:** 2026-01-15T23:26:37Z
- **Completed:** 2026-01-15T23:31:38Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Implemented ProxmoxCollector following Collector protocol
- Extract MAC addresses from VM network interfaces (net0-net9)
- Query QEMU guest agent for IP addresses when available
- Added proxmoxer and requests dependencies

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement Proxmox collector** - `db49225` (feat)
2. **Task 2: Update collectors package exports** - `2c72116` (feat)

**Deviation fix:** `932f30c` (fix: add requests dependency for proxmoxer)

## Files Created/Modified

- `src/netbox_auto/collectors/proxmox.py` - ProxmoxCollector implementation
- `src/netbox_auto/collectors/__init__.py` - Added ProxmoxCollector to exports
- `pyproject.toml` - Added proxmoxer>=2.0 and requests>=2.0 dependencies

## Decisions Made

- **MAC extraction via regex**: Proxmox stores MAC in format "virtio=AA:BB:CC:DD:EE:FF,bridge=vmbr0", use regex to extract
- **QEMU agent for IPs**: Guest agent provides accurate IP addresses when available, gracefully skip if not
- **Graceful error handling**: Return empty list on connection/auth errors, log the error

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added requests dependency for proxmoxer**

- **Found during:** Task 2 verification
- **Issue:** proxmoxer requires requests module for HTTP backend but doesn't declare it as dependency
- **Fix:** Added requests>=2.0 to pyproject.toml dependencies
- **Files modified:** pyproject.toml
- **Verification:** ProxmoxCollector.collect() works without import errors
- **Commit:** 932f30c

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary for proxmoxer to function. No scope creep.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- ProxmoxCollector ready for integration with discovery orchestrator
- Requires Proxmox API credentials in config.yaml to function
- Ready for 02-03-PLAN.md (scanner collector)

---
*Phase: 02-discovery*
*Completed: 2026-01-15*
