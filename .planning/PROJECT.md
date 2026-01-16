# NetBox Automation

## What This Is

A network discovery and inventory tool that maps hosts from multiple sources (MikroTik DHCP, network scans, Proxmox), correlates them with switch port data, and populates NetBox with devices, VMs, IPs, and cabling. Also updates Unbound DNS records.

## Core Value

Automated discovery and correlation of network hosts to their switch ports — eliminating manual data gathering and reducing NetBox population from hours to minutes.

## Requirements

### Validated

- Pull DHCP leases from MikroTik router via API — v1.0
- Scan network subnets to discover hosts with static IPs — v1.0
- Query Proxmox API for VM inventory — v1.0
- Query MikroTik switch MAC tables to correlate hosts with switch ports — v1.0
- Cross-reference discovered hosts with existing DNS records — v1.0
- CLI tool to run discovery and output results — v1.0
- Simple web UI to review/classify discovered hosts before pushing — v1.0
- Push discovered hosts to NetBox as Devices or VMs with IP assignments — v1.0
- Create cable records in NetBox (switch port to device) — v1.0
- Update Unbound DNS config files via SSH on two VMs — v1.0
- Config file for API credentials (gitignored) with env var override — v1.0

### Active

(None — planning next milestone)

### Out of Scope

- Docker container tracking — too ephemeral, just track Docker hosts
- Patch panel / wall jack / full cable path — switch-to-device only
- Multi-site support — single site only
- Real-time continuous discovery — on-demand runs only

## Context

**Current State (v1.0 shipped):**
- 2,779 lines Python across 26 source files
- Tech stack: Python 3.11+, Typer CLI, Flask, SQLAlchemy, pynetbox, paramiko
- Four CLI commands: discover, serve, push, status
- All v1 requirements implemented and validated

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
| CLI + web UI hybrid | Discovery is scriptable, review is better visual | Good |
| Ignore Docker containers | Ephemeral, share host IP, track hosts instead | Good |
| Switch-to-device cabling only | Simpler, full path can be added later | Good |
| Direct SSH for Unbound | Unbound has no dynamic record API | Good |
| Typer CLI with rich output | Modern Python CLI, good UX | Good |
| src/ layout for package | Cleaner imports, standard practice | Good |
| MAC address as correlation key | Unique identifier across all sources | Good |
| Protocol over ABC for collectors | Duck-typing, simpler interface | Good |
| Hostname priority: DHCP > Proxmox > scan | Most specific source wins | Good |
| Continue on collector failure | Partial data better than no data | Good |
| paramiko for SSH | Simpler than asyncssh for sync operations | Good |
| Dry-run mode for push | Safe preview of changes | Good |

---
*Last updated: 2026-01-16 after v1.0 milestone*
