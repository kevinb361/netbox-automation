# Phase 2: Discovery Verification

**Phase Goal:** Collect hosts from all sources and correlate by MAC
**Verified:** 2026-01-15
**Status:** PASSED

## Success Criteria Verification

### Criterion 1: `netbox-auto discover` pulls DHCP leases from MikroTik

**Status:** PASSED

**Evidence:**
- CLI command exists: `src/netbox_auto/cli.py` lines 74-117 define `discover` command
- DHCPCollector implementation: `src/netbox_auto/collectors/dhcp.py`
  - Uses `librouteros` library (line 9): `import librouteros`
  - Queries `/ip/dhcp-server/lease` endpoint (line 65)
  - Extracts MAC, IP (active-address or address), hostname (lines 67-78)
  - Returns `DiscoveredHost` objects with `source=HostSource.DHCP`
- Dependency declared in `pyproject.toml` line 22: `"librouteros>=3.2"`
- CLI help confirms: "Pulls DHCP leases from MikroTik"

### Criterion 2: `netbox-auto discover` pulls VMs from Proxmox

**Status:** PASSED

**Evidence:**
- ProxmoxCollector implementation: `src/netbox_auto/collectors/proxmox.py`
  - Uses `proxmoxer` library (line 12): `from proxmoxer import ProxmoxAPI`
  - Iterates all nodes and VMs via `api.nodes.get()` and `api.nodes(node).qemu.get()`
  - Extracts MACs from network config using regex (line 22, lines 131-154)
  - Gets IPs from QEMU guest agent when available (lines 156-188)
  - Returns `DiscoveredHost` objects with `source=HostSource.PROXMOX`
- Dependency declared in `pyproject.toml` line 23: `"proxmoxer>=2.0"`
- Orchestrator calls ProxmoxCollector: `discovery.py` lines 142-152

### Criterion 3: `netbox-auto discover` scans subnets for static IPs

**Status:** PASSED

**Evidence:**
- ScannerCollector implementation: `src/netbox_auto/collectors/scanner.py`
  - Uses `scapy` library (line 54): `from scapy.all import ARP, Ether, srp`
  - Sends ARP broadcast packets to configured subnets (lines 96-100)
  - Extracts MAC (`received.hwsrc`) and IP (`received.psrc`) from responses (lines 106-107)
  - Returns `DiscoveredHost` objects with `source=HostSource.SCAN`
- Dependency declared in `pyproject.toml` line 26: `"scapy>=2.5"`
- Config supports subnet list: `config.py` lines 73-79 `ScannerConfig`
- Orchestrator calls ScannerCollector: `discovery.py` lines 154-164

### Criterion 4: `netbox-auto discover` queries switch MAC tables

**Status:** PASSED

**Evidence:**
- SwitchCollector implementation: `src/netbox_auto/collectors/switch.py`
  - Uses `librouteros` library (line 9): `import librouteros`
  - Queries `/interface/bridge/host` for CRS/hAP series (lines 117-130)
  - Falls back to `/interface/ethernet/switch/host` for older switches (lines 132-145)
  - Returns dict mapping MAC to "switch_name:port_name" (lines 40-73)
- Config supports multiple switches: `config.py` lines 28-35 `SwitchConfig`
- Orchestrator integrates switch data: `discovery.py` lines 76-84

### Criterion 5: Hosts from different sources are merged by MAC in staging DB

**Status:** PASSED

**Evidence:**
- Merge logic in `discovery.py` function `_merge_and_persist()` (lines 169-243):
  - Groups hosts by MAC address (lines 193-196)
  - Merges IP addresses from all sources (lines 203-205)
  - Picks hostname by priority: DHCP > Proxmox > Scan (lines 208, 246-264)
  - Applies switch port mapping from MAC lookup (line 214)
  - Creates or updates Host records in database (lines 217-240)
- Host table has unique constraint on MAC: `models.py` line 83
- Database schema verified:
  - `host` table with `mac VARCHAR(17) UNIQUE`
  - `ip_addresses JSON` for multiple IPs
  - `switch_port VARCHAR(100)` for correlation
  - `source VARCHAR(20)` for tracking origin

## Code Quality Checks

| Check | Result |
|-------|--------|
| All collectors use correct libraries | librouteros, proxmoxer, scapy |
| Error handling present | All collectors catch exceptions, log, return empty lists |
| MAC normalization consistent | `DiscoveredHost.__post_init__` normalizes MAC format |
| Database persistence working | Schema verified via SQLAlchemy inspect |

## Requirement Coverage

| Requirement | Status |
|-------------|--------|
| DISC-01: MikroTik DHCP leases | Complete |
| DISC-02: Proxmox VM inventory | Complete |
| DISC-03: Network subnet scanning | Complete |
| DISC-04: Switch MAC table query | Complete |
| DISC-05: MAC-based host correlation | Complete |
| DATA-02: Duplicate merge by MAC | Complete |
| DATA-03: Host status tracking | Complete (Host.status field) |
| CLI-01: discover command | Complete |

## Files Verified

- `/home/kevin/projects/netbox-automation/src/netbox_auto/cli.py`
- `/home/kevin/projects/netbox-automation/src/netbox_auto/discovery.py`
- `/home/kevin/projects/netbox-automation/src/netbox_auto/collectors/__init__.py`
- `/home/kevin/projects/netbox-automation/src/netbox_auto/collectors/base.py`
- `/home/kevin/projects/netbox-automation/src/netbox_auto/collectors/dhcp.py`
- `/home/kevin/projects/netbox-automation/src/netbox_auto/collectors/proxmox.py`
- `/home/kevin/projects/netbox-automation/src/netbox_auto/collectors/scanner.py`
- `/home/kevin/projects/netbox-automation/src/netbox_auto/collectors/switch.py`
- `/home/kevin/projects/netbox-automation/src/netbox_auto/models.py`
- `/home/kevin/projects/netbox-automation/src/netbox_auto/database.py`
- `/home/kevin/projects/netbox-automation/pyproject.toml`

## Summary

Phase 2 is **PASSED**. All five success criteria are met:

1. DHCPCollector uses librouteros to query MikroTik DHCP leases
2. ProxmoxCollector uses proxmoxer to discover VMs with MACs and IPs
3. ScannerCollector uses scapy for ARP-based subnet scanning
4. SwitchCollector queries MikroTik bridge/switch MAC tables
5. Discovery orchestration merges hosts by MAC with hostname priority and switch port correlation

The `netbox-auto discover` command is functional and persists correlated hosts to the SQLite staging database.

---
*Verified: 2026-01-15*
*Verifier: Claude Code*
