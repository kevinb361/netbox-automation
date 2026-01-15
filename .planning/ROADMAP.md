# Roadmap: NetBox Automation

## Overview

Build a network discovery tool that collects hosts from MikroTik/Proxmox/scans, correlates them by MAC to switch ports, and pushes to NetBox with DNS updates. Foundation → Discovery → Review UI → Push.

## Phases

- [ ] **Phase 1: Foundation** - Project structure, config, CLI, database
- [ ] **Phase 2: Discovery** - Collectors and MAC correlation
- [ ] **Phase 3: Review** - Web UI for host approval
- [ ] **Phase 4: Push** - NetBox and DNS output

## Phase Details

### Phase 1: Foundation

**Goal**: Project structure with working CLI shell and config loading
**Depends on**: Nothing (first phase)
**Requirements**: CONF-01, CONF-02, CONF-03, DATA-01
**Success Criteria** (what must be TRUE):

1. `netbox-auto --help` displays available commands
2. Config file is loaded and validated on startup
3. SQLite database is created on first run
4. Missing config results in helpful error message
   **Research**: Unlikely (standard Python project setup)
   **Plans**: TBD

Plans:

- [x] 01-01: Project Structure + CLI Shell
- [ ] 01-02: Configuration System
- [ ] 01-03: Database Foundation

### Phase 2: Discovery

**Goal**: Collect hosts from all sources and correlate by MAC
**Depends on**: Phase 1
**Requirements**: DISC-01, DISC-02, DISC-03, DISC-04, DISC-05, DATA-02, DATA-03, CLI-01
**Success Criteria** (what must be TRUE):

1. `netbox-auto discover` pulls DHCP leases from MikroTik
2. `netbox-auto discover` pulls VMs from Proxmox
3. `netbox-auto discover` scans subnets for static IPs
4. `netbox-auto discover` queries switch MAC tables
5. Hosts from different sources are merged by MAC in staging DB
   **Research**: Likely (external APIs, network scanning)
   **Research topics**: librouteros auth patterns, proxmoxer token privileges, scapy ARP scanning, MikroTik switch MAC table queries
   **Plans**: TBD

Plans:

- [ ] 02-01: TBD

### Phase 3: Review

**Goal**: Web UI to review, classify, and approve hosts
**Depends on**: Phase 2
**Requirements**: REVW-01, REVW-02, REVW-03, REVW-04, REVW-05, CLI-02, NBRC-01, NBRC-02, NBRC-03, NBRC-04
**Success Criteria** (what must be TRUE):

1. `netbox-auto serve` starts web UI accessible at localhost
2. User sees all discovered hosts in a table view
3. User can approve/reject individual hosts
4. User can classify hosts by type (server/workstation/IoT/network)
5. User can compare discovered hosts with NetBox inventory
   **Research**: Unlikely (Flask + Jinja2 standard patterns)
   **Plans**: TBD

Plans:

- [ ] 03-01: TBD

### Phase 4: Push

**Goal**: Push approved hosts to NetBox and update DNS
**Depends on**: Phase 3
**Requirements**: OUTP-01, OUTP-02, OUTP-03, OUTP-04, CLI-03, CLI-04
**Success Criteria** (what must be TRUE):

1. `netbox-auto push` creates NetBox devices/VMs for approved hosts
2. `netbox-auto push` creates cable records linking switches to devices
3. `netbox-auto push` updates Unbound DNS via SSH
4. `netbox-auto status` shows discovery/push status summary
5. Dry-run mode previews changes without pushing
   **Research**: Likely (external APIs)
   **Research topics**: pynetbox cable/interface API, asyncssh patterns, Unbound local-data config format
   **Plans**: TBD

Plans:

- [ ] 04-01: TBD

## Progress

| Phase         | Plans Complete | Status      | Completed |
| ------------- | -------------- | ----------- | --------- |
| 1. Foundation | 1/3            | In progress | -         |
| 2. Discovery  | 0/?            | Not started | -         |
| 3. Review     | 0/?            | Not started | -         |
| 4. Push       | 0/?            | Not started | -         |
