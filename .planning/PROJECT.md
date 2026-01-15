# NetBox Automation

## What This Is

A network discovery and inventory tool that maps hosts from multiple sources (MikroTik DHCP, network scans, Proxmox), correlates them with switch port data, and populates NetBox with devices, VMs, IPs, and cabling. Also updates Unbound DNS records.

## Core Value

Automated discovery and correlation of network hosts to their switch ports — eliminating manual data gathering and reducing NetBox population from hours to minutes.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Pull DHCP leases from MikroTik router via API
- [ ] Scan network subnets to discover hosts with static IPs
- [ ] Query Proxmox API for VM inventory
- [ ] Query MikroTik switch MAC tables to correlate hosts with switch ports
- [ ] Cross-reference discovered hosts with existing DNS records
- [ ] CLI tool to run discovery and output results
- [ ] Simple web UI to review/classify discovered hosts before pushing
- [ ] Push discovered hosts to NetBox as Devices or VMs with IP assignments
- [ ] Create cable records in NetBox (switch port to device)
- [ ] Update Unbound DNS config files via SSH on two VMs
- [ ] Config file for API credentials (gitignored) with env var override

### Out of Scope

- Docker container tracking — too ephemeral, just track Docker hosts
- Patch panel / wall jack / full cable path — switch-to-device only
- Multi-site support — single site only
- Real-time continuous discovery — on-demand runs only

## Context

**Environment:**
- MikroTik router + switches (RouterOS API enabled)
- Ruckus Unleashed APs
- 4 physical servers, 2 are Proxmox hosts
- Mix of VMs and Docker containers on Proxmox hosts
- Unbound DNS on two VMs
- NetBox exists but needs API setup

**NetBox current state:**
- Switches/router defined
- VLANs/subnets configured
- Interconnect ports documented
- Missing: access ports, hosts, cables

**Scale:**
- Small (<50 cables)
- Single site

## Constraints

- **Tech stack**: Python — matches existing workflow and tooling
- **NetBox API**: Must configure API access before tool can push data
- **DNS method**: Unbound requires direct file edit + reload (no dynamic API)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| CLI + web UI hybrid | Discovery is scriptable, review is better visual | — Pending |
| Ignore Docker containers | Ephemeral, share host IP, track hosts instead | — Pending |
| Switch-to-device cabling only | Simpler, full path can be added later | — Pending |
| Direct SSH for Unbound | Unbound has no dynamic record API | — Pending |

---
*Last updated: 2025-01-15 after initialization*
