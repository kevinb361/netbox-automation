# Requirements: NetBox Automation

**Defined:** 2026-01-15
**Core Value:** Automated discovery and correlation of network hosts to their switch ports — eliminating manual data gathering and reducing NetBox population from hours to minutes.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Discovery

- [ ] **DISC-01**: Tool can pull DHCP leases from MikroTik router via API
- [ ] **DISC-02**: Tool can query Proxmox API for VM inventory (name, MAC, IP)
- [ ] **DISC-03**: Tool can scan network subnets to discover hosts with static IPs
- [ ] **DISC-04**: Tool can query MikroTik switch MAC tables to find host-to-port mappings
- [ ] **DISC-05**: Tool correlates hosts across sources using MAC address as primary key

### Data Management

- [ ] **DATA-01**: Discovered hosts are stored in SQLite staging database
- [ ] **DATA-02**: Duplicate hosts from different sources are merged by MAC
- [ ] **DATA-03**: Each host has status tracking (pending/approved/rejected/pushed)

### Review

- [ ] **REVW-01**: Web UI displays all discovered hosts in a table
- [ ] **REVW-02**: User can approve individual hosts for push
- [ ] **REVW-03**: User can reject individual hosts (mark as ignored)
- [ ] **REVW-04**: User can classify hosts (server/workstation/IoT/network)
- [ ] **REVW-05**: User can bulk approve/reject multiple hosts at once

### NetBox Reconciliation

- [ ] **NBRC-01**: Tool can list existing devices from NetBox
- [ ] **NBRC-02**: Tool compares discovered hosts with NetBox (highlights new)
- [ ] **NBRC-03**: Tool detects stale NetBox entries (not seen in discovery)
- [ ] **NBRC-04**: Tool can import NetBox devices into staging DB for reference

### Output

- [ ] **OUTP-01**: Tool creates NetBox devices/VMs for approved hosts with IP assignments
- [ ] **OUTP-02**: Tool creates cable records in NetBox (switch port to device)
- [ ] **OUTP-03**: Tool generates Unbound DNS config and pushes via SSH
- [ ] **OUTP-04**: Tool supports dry-run mode (preview changes without pushing)

### CLI

- [ ] **CLI-01**: `discover` command runs all collectors and populates staging DB
- [ ] **CLI-02**: `serve` command starts web UI server
- [ ] **CLI-03**: `push` command pushes approved hosts to NetBox and Unbound
- [ ] **CLI-04**: `status` command shows discovery/push status summary

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

| Feature | Reason |
|---------|--------|
| Docker container tracking | Too ephemeral, just track Docker hosts |
| Full cable path (patch panels, wall jacks) | Switch-to-device only for v1 |
| Multi-site support | Single site only |
| Real-time continuous discovery | On-demand runs only |
| Full topology mapping | Scope creep, enterprise feature |
| Agent-based discovery | Impractical for home lab |
| AI/ML anomaly detection | Overkill for home lab scale |

## Traceability

Which phases cover which requirements. Updated by create-roadmap.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DISC-01 | TBD | Pending |
| DISC-02 | TBD | Pending |
| DISC-03 | TBD | Pending |
| DISC-04 | TBD | Pending |
| DISC-05 | TBD | Pending |
| DATA-01 | TBD | Pending |
| DATA-02 | TBD | Pending |
| DATA-03 | TBD | Pending |
| REVW-01 | TBD | Pending |
| REVW-02 | TBD | Pending |
| REVW-03 | TBD | Pending |
| REVW-04 | TBD | Pending |
| REVW-05 | TBD | Pending |
| NBRC-01 | TBD | Pending |
| NBRC-02 | TBD | Pending |
| NBRC-03 | TBD | Pending |
| NBRC-04 | TBD | Pending |
| OUTP-01 | TBD | Pending |
| OUTP-02 | TBD | Pending |
| OUTP-03 | TBD | Pending |
| OUTP-04 | TBD | Pending |
| CLI-01 | TBD | Pending |
| CLI-02 | TBD | Pending |
| CLI-03 | TBD | Pending |
| CLI-04 | TBD | Pending |
| CONF-01 | TBD | Pending |
| CONF-02 | TBD | Pending |
| CONF-03 | TBD | Pending |

**Coverage:**
- v1 requirements: 28 total
- Mapped to phases: 0
- Unmapped: 28 ⚠️ (pending create-roadmap)

---
*Requirements defined: 2026-01-15*
*Last updated: 2026-01-15 after initial definition*
