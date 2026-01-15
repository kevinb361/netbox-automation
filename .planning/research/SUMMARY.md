# Project Research Summary

**Project:** NetBox Automation
**Domain:** Network discovery / infrastructure inventory tool
**Researched:** 2026-01-15
**Confidence:** HIGH

## Executive Summary

This is a well-understood problem domain with mature Python libraries for all integrations. The recommended stack (librouteros, proxmoxer, pynetbox, scapy, asyncssh) is battle-tested and actively maintained. The architecture pattern—CLI discovery → SQLite staging → web review → push—is common in network automation tools.

The key risk is **data quality issues from automatic sync**. Enterprise tools (NetBox Diode, Slurp'it) have moved toward staging/branching/review workflows specifically because auto-sync creates duplicates and stale data. Starting with human-in-the-loop review is the right approach.

The MikroTik + Proxmox + home lab focus is **underserved**—most tools target enterprise protocols (SNMP, CDP/LLDP). This is a differentiator.

## Key Findings

### Recommended Stack

All libraries are HIGH confidence with active maintenance (2024-2025 releases).

**Core technologies:**
- **librouteros 3.4.1**: MikroTik API — used by Ansible, memory-efficient, GPL-2.0
- **proxmoxer 2.2.0**: Proxmox API — official wrapper, token auth supported
- **pynetbox 7.6.0**: NetBox API — threading support, official community library
- **scapy 2.7.0**: Network scanning — industry standard ARP scanning
- **asyncssh 2.22.0**: SSH automation — native asyncio for parallel Unbound updates
- **typer + rich**: CLI framework — type-hint based, beautiful output
- **Flask + Jinja2**: Web UI — simple, no JS build step

See: `.planning/research/STACK.md`

### Expected Features

**Must have (table stakes):**
- Multi-source discovery (DHCP, VMs, scans)
- MAC-based correlation and deduplication
- CLI for discovery, web for review
- NetBox sync capability
- Status tracking (pending/approved/pushed)

**Should have (differentiators):**
- Switch port MAC correlation
- Unbound DNS automation
- Diff preview before push

**Defer (v2+):**
- Scheduled discovery runs
- Multi-site support
- Historical change tracking

See: `.planning/research/FEATURES.md`

### Architecture Approach

CLI + SQLite staging + web review pattern. Separate commands for each phase:
- `discover`: Run collectors, populate staging DB
- `serve`: Start web UI for review
- `push`: Push approved hosts to targets

**Major components:**
1. **Collectors**: MikroTik, Proxmox, scanner, switch MAC — each returns normalized HostRecord
2. **Correlation engine**: MAC-based matching across sources
3. **Staging DB**: SQLite with status tracking
4. **Web UI**: Flask + Jinja2 for approve/reject workflow
5. **Push engines**: NetBox (pynetbox), Unbound (SSH file edit)

See: `.planning/research/ARCHITECTURE.md`

### Critical Pitfalls

1. **Proxmox API token privilege separation** — default breaks automation, must disable or grant explicit ACLs
2. **MikroTik auth version mismatch** — use `plaintext_login=True` for RouterOS 6.43+
3. **NetBox race conditions** — serialize IP allocation, use v3.3.7+
4. **pynetbox threading duplicates** — disable threading for critical syncs
5. **Network scanner aggressive timing** — use -T2/-T3, not -T4/-T5

See: `.planning/research/PITFALLS.md`

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Project Foundation
**Rationale:** Establish project structure, config handling, CLI skeleton before any integration work
**Delivers:** Working CLI shell, config loading, SQLite database setup
**Addresses:** Project structure patterns from ARCHITECTURE.md
**Avoids:** "Lab scripts in production" anti-pattern

### Phase 2: Discovery Collectors
**Rationale:** Read-only operations first, lowest risk
**Delivers:** MikroTik DHCP, Proxmox VM, network scan collectors
**Uses:** librouteros, proxmoxer, scapy
**Avoids:** Proxmox token privilege separation pitfall, MikroTik auth issues

### Phase 3: Correlation Engine
**Rationale:** Core value proposition — MAC-based host correlation
**Delivers:** Unified host records from multiple sources, deduplication
**Implements:** MAC address as primary correlation key pattern
**Avoids:** Data quality issues from unprocessed raw data

### Phase 4: Web Review UI
**Rationale:** Human-in-the-loop before any external writes
**Delivers:** Flask app for reviewing/classifying/approving hosts
**Addresses:** "Review workflow is critical" insight from features research
**Avoids:** Auto-sync data quality problems

### Phase 5: NetBox Push
**Rationale:** External writes only after review workflow complete
**Delivers:** Device/VM/IP/cable creation in NetBox
**Uses:** pynetbox with idempotent patterns
**Avoids:** Race conditions, threading duplicates, non-idempotent operations

### Phase Ordering Rationale

- **Foundation first**: Can't test collectors without CLI/config
- **Discovery before correlation**: Need raw data to correlate
- **Review before push**: Data quality requires human approval
- **NetBox before DNS**: NetBox is primary target, DNS is enhancement

### Research Flags

Phases with well-documented patterns (skip research-phase):
- **Phase 1**: Standard Python project setup
- **Phase 3**: MAC correlation is straightforward
- **Phase 4**: Flask review UI is simple

Phases that may need clarification during planning:
- **Phase 2**: MikroTik switch MAC table queries (SNMP vs API?)
- **Phase 5**: NetBox object model for cables/interfaces

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All libraries verified on PyPI, actively maintained |
| Features | HIGH | Patterns from enterprise tools (Slurp'it, NetBox Diode) |
| Architecture | HIGH | Standard CLI + SQLite + Flask pattern |
| Pitfalls | HIGH | From official docs and community post-mortems |

**Overall confidence:** HIGH

### Gaps to Address

- **MikroTik switch SNMP OIDs**: Specific MikroTik SNMP queries for MAC tables need verification during Phase 2 planning
- **NetBox cable modeling**: Exact pynetbox API for cable creation needs Phase 5 research
- **Unbound config format**: Exact local-data syntax for Unbound needs verification

## Sources

### Primary (HIGH confidence)
- librouteros, proxmoxer, pynetbox, scapy PyPI pages — version info
- MikroTik API, Proxmox API, NetBox API official docs — integration patterns
- Nmap documentation — scanning best practices

### Secondary (MEDIUM confidence)
- Community forums (Proxmox, MikroTik) — pitfall identification
- NetBox GitHub issues — pynetbox gotchas

### Tertiary (LOW confidence)
- Blog posts — feature inspiration, not verified

---
*Research completed: 2026-01-15*
*Ready for roadmap: yes*
