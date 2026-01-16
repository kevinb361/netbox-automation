# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Network discovery tool that collects hosts from multiple sources (MikroTik DHCP, Proxmox VMs, ARP scans, switch MAC tables), correlates them by MAC address, provides a web UI for review/approval, and pushes approved hosts to NetBox with DNS updates to Unbound servers.

## Commands

```bash
# Development
make ci              # format + lint + type + test (run before commits)
make format          # black + ruff --fix
make lint            # ruff check
make type            # mypy src/
make test            # pytest

# CLI
netbox-auto discover           # Run all collectors, store to staging DB
netbox-auto serve              # Web UI at localhost:5000
netbox-auto push               # Push approved hosts to NetBox/DNS
netbox-auto push --dry-run     # Preview changes
netbox-auto status             # Show host counts by status/type
```

## Architecture

### Data Flow
```
Collectors → Discovery → Staging DB → Web Review → Push → NetBox + DNS
(discover)               (SQLite)     (serve)           (push)
```

### Module Structure

- **cli.py**: Typer CLI entry point with commands: discover, serve, push, status
- **discovery.py**: Orchestrates collectors, merges hosts by MAC, persists to DB
- **reconcile.py**: Compares staging DB with NetBox inventory (new/matched/stale)
- **push.py**: Pushes approved hosts to NetBox and DNS
- **netbox.py**: pynetbox wrapper (lazy connection, device/VM CRUD, cables)
- **dns.py**: Generates Unbound config, pushes via SSH/paramiko
- **config.py**: Pydantic settings from YAML + env var overrides (NETBOX_AUTO_SECTION__FIELD)
- **database.py**: SQLAlchemy engine/session factory, SQLite storage
- **models.py**: SQLAlchemy 2.0 ORM (Host, DiscoveryRun) with status enums

### Collectors (`collectors/`)

All implement `Collector` Protocol from `base.py`:
- **base.py**: `Collector` Protocol + `DiscoveredHost` dataclass (MAC as key)
- **dhcp.py**: MikroTik DHCP leases via librouteros
- **proxmox.py**: Proxmox VMs via proxmoxer
- **scanner.py**: ARP scans via scapy (requires root)
- **switch.py**: MikroTik switch MAC tables → MAC-to-port mapping

### Key Patterns

- **MAC-based correlation**: Hosts merged by MAC address across sources
- **Source priority**: DHCP > Proxmox > Scan (for hostname selection)
- **Status workflow**: pending → approved/rejected → pushed
- **Lazy connections**: NetBox client connects on first use, not init
- **Env var secrets**: `NETBOX_AUTO_MIKROTIK__PASSWORD`, `NETBOX_AUTO_NETBOX__TOKEN`

## Configuration

Copy `config.example.yaml` to `config.yaml`. Secrets via env vars preferred.

## Testing

```bash
pytest tests/                    # all tests
pytest tests/test_models.py      # single file
pytest -k test_host              # pattern match
```

Test directory mirrors src/ structure. Currently minimal test coverage.
