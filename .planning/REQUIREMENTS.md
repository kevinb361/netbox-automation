# Requirements: NetBox Automation

**Defined:** 2026-01-15
**Core Value:** Automated discovery and correlation of network hosts to their switch ports — eliminating manual data gathering and reducing NetBox population from hours to minutes.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Discovery

- [x] **DISC-01**: Tool can pull DHCP leases from MikroTik router via API
- [x] **DISC-02**: Tool can query Proxmox API for VM inventory (name, MAC, IP)
- [x] **DISC-03**: Tool can scan network subnets to discover hosts with static IPs
- [x] **DISC-04**: Tool can query MikroTik switch MAC tables to find host-to-port mappings
- [x] **DISC-05**: Tool correlates hosts across sources using MAC address as primary key

### Data Management

- [x] **DATA-01**: Discovered hosts are stored in SQLite staging database
- [x] **DATA-02**: Duplicate hosts from different sources are merged by MAC
- [x] **DATA-03**: Each host has status tracking (pending/approved/rejected/pushed)

### Review

- [x] **REVW-01**: Web UI displays all discovered hosts in a table
- [x] **REVW-02**: User can approve individual hosts for push
- [x] **REVW-03**: User can reject individual hosts (mark as ignored)
- [x] **REVW-04**: User can classify hosts (server/workstation/IoT/network)
- [x] **REVW-05**: User can bulk approve/reject multiple hosts at once

### NetBox Reconciliation

- [x] **NBRC-01**: Tool can list existing devices from NetBox
- [x] **NBRC-02**: Tool compares discovered hosts with NetBox (highlights new)
- [x] **NBRC-03**: Tool detects stale NetBox entries (not seen in discovery)
- [x] **NBRC-04**: Tool can import NetBox devices into staging DB for reference

### Output

- [x] **OUTP-01**: Tool creates NetBox devices/VMs for approved hosts with IP assignments
- [x] **OUTP-02**: Tool creates cable records in NetBox (switch port to device)
- [x] **OUTP-03**: Tool generates Unbound DNS config and pushes via SSH
- [x] **OUTP-04**: Tool supports dry-run mode (preview changes without pushing)

### CLI

- [x] **CLI-01**: `discover` command runs all collectors and populates staging DB
- [x] **CLI-02**: `serve` command starts web UI server
- [x] **CLI-03**: `push` command pushes approved hosts to NetBox and Unbound
- [x] **CLI-04**: `status` command shows discovery/push status summary

### Configuration

- [ ] **CONF-01**: Tool reads credentials and settings from YAML config file
- [ ] **CONF-02**: Secrets can be overridden via environment variables
- [ ] **CONF-03**: Example config file is included with the project

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Automation

- **AUTO-01**: Scheduled discovery runs (cron-like)
- **AUTO-02**: Webhook notifications on discovery/push events

### Data Export

- **EXPO-01**: Export discovered hosts to CSV
- **EXPO-02**: REST API for automation integration

### Enhanced Review

- **REVW-06**: Detailed diff preview before push
- **REVW-07**: DNS conflict detection before push

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature                                    | Reason                                 |
| ------------------------------------------ | -------------------------------------- |
| Docker container tracking                  | Too ephemeral, just track Docker hosts |
| Full cable path (patch panels, wall jacks) | Switch-to-device only for v1           |
| Multi-site support                         | Single site only                       |
| Real-time continuous discovery             | On-demand runs only                    |
| Full topology mapping                      | Scope creep, enterprise feature        |
| Agent-based discovery                      | Impractical for home lab               |
| AI/ML anomaly detection                    | Overkill for home lab scale            |

## Traceability

Which phases cover which requirements. Updated by create-roadmap.

| Requirement | Phase   | Status   |
| ----------- | ------- | -------- |
| CONF-01     | Phase 1 | Complete |
| CONF-02     | Phase 1 | Complete |
| CONF-03     | Phase 1 | Complete |
| DATA-01     | Phase 1 | Complete |
| DISC-01     | Phase 2 | Complete |
| DISC-02     | Phase 2 | Complete |
| DISC-03     | Phase 2 | Complete |
| DISC-04     | Phase 2 | Complete |
| DISC-05     | Phase 2 | Complete |
| DATA-02     | Phase 2 | Complete |
| DATA-03     | Phase 2 | Complete |
| CLI-01      | Phase 2 | Complete |
| REVW-01     | Phase 3 | Complete |
| REVW-02     | Phase 3 | Complete |
| REVW-03     | Phase 3 | Complete |
| REVW-04     | Phase 3 | Complete |
| REVW-05     | Phase 3 | Complete |
| CLI-02      | Phase 3 | Complete |
| NBRC-01     | Phase 3 | Complete |
| NBRC-02     | Phase 3 | Complete |
| NBRC-03     | Phase 3 | Complete |
| NBRC-04     | Phase 3 | Complete |
| OUTP-01     | Phase 4 | Complete |
| OUTP-02     | Phase 4 | Complete |
| OUTP-03     | Phase 4 | Complete |
| OUTP-04     | Phase 4 | Complete |
| CLI-03      | Phase 4 | Complete |
| CLI-04      | Phase 4 | Complete |

**Coverage:**

- v1 requirements: 28 total
- Mapped to phases: 28 ✓
- Unmapped: 0

---

_Requirements defined: 2026-01-15_
_Last updated: 2026-01-15 after initial definition_
