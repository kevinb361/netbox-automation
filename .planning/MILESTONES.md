# Project Milestones: NetBox Automation

## v1.0 MVP (Shipped: 2026-01-16)

**Delivered:** Network discovery tool that collects hosts from MikroTik DHCP, Proxmox VMs, and network scans, correlates them by MAC to switch ports, and pushes to NetBox with DNS updates.

**Phases completed:** 1-4 (17 plans total)

**Key accomplishments:**

- Python CLI with discover, serve, push, status commands
- Multi-source discovery (MikroTik DHCP, Proxmox, ARP scanning, switch MACs)
- MAC-based host correlation merging data across sources
- Flask web UI for host review, approval, and classification
- NetBox reconciliation comparing discovered vs existing inventory
- NetBox device/VM/cable creation and Unbound DNS push via SSH

**Stats:**

- 26 source files created
- 2,779 lines of Python
- 4 phases, 17 plans
- ~5 hours from start to ship

**Git range:** `73d21ad` → `8a99f3d`

**What's next:** v2 features (scheduled discovery, CSV export, REST API)

---
