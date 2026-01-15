# Architecture Research: Network Discovery Tool

Research for CLI + web review pattern in network automation context.

## System Overview

```
+------------------+     +------------------+     +------------------+
|   DATA SOURCES   |     |   DISCOVERY      |     |   STAGING DB     |
|                  |     |   ENGINE         |     |                  |
| - MikroTik DHCP  |---->|                  |---->|   SQLite         |
| - Proxmox VMs    |     | - Collect        |     | - discovered_hosts
| - Network Scan   |     | - Normalize      |     | - mac_mappings   |
| - Switch MACs    |     | - Correlate      |     | - classifications|
+------------------+     +------------------+     +------------------+
                                                          |
                                                          v
+------------------+     +------------------+     +------------------+
|   OUTPUT         |<----|   PUSH           |<----|   WEB REVIEW     |
|   TARGETS        |     |   ENGINE         |     |                  |
|                  |     |                  |     | - View hosts     |
| - NetBox API     |     | - Only approved  |     | - Classify       |
| - Unbound DNS    |     | - Idempotent     |     | - Approve/Reject |
+------------------+     +------------------+     +------------------+

CLI Commands:
  discover   ->  Runs collectors, populates staging DB
  serve      ->  Starts web UI for review
  push       ->  Pushes approved hosts to targets
  sync       ->  Full pipeline: discover + serve (wait) + push
```

## Component Responsibilities

### 1. Collectors (Data Sources)

Each collector implements a common interface, returns normalized host records.

| Collector | Library | Data Retrieved |
|-----------|---------|----------------|
| MikroTik DHCP | `routeros-api` (socialwifi) | hostname, MAC, IP, lease time |
| Proxmox VMs | `proxmoxer` | VM name, MAC, IP, node |
| Network Scanner | `scapy` or `python-nmap` | IP, MAC, open ports |
| Switch MACs | SNMP via `pysnmp` or device API | port, MAC, VLAN |

**Confidence: HIGH** - Libraries verified on PyPI with recent releases (2024-2025).

### 2. Correlation Engine

Matches hosts across sources using MAC address as primary key.

```python
# Simplified correlation logic
def correlate(hosts: list[DiscoveredHost]) -> list[CorrelatedHost]:
    by_mac = defaultdict(list)
    for h in hosts:
        by_mac[h.mac].append(h)
    return [merge_records(records) for records in by_mac.values()]
```

**Confidence: MEDIUM** - Pattern derived from switch port mapping tool concepts. No specific library; custom implementation needed.

### 3. Staging Database

SQLite file for persistence between CLI runs. Schema supports review workflow.

```sql
CREATE TABLE discovered_hosts (
    id INTEGER PRIMARY KEY,
    mac TEXT UNIQUE NOT NULL,
    hostname TEXT,
    ip_addresses TEXT,  -- JSON array
    sources TEXT,       -- JSON array of source names
    switch_port TEXT,
    vlan INTEGER,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    status TEXT DEFAULT 'pending',  -- pending|approved|rejected|pushed
    classification TEXT,  -- server|workstation|iot|network|ignore
    notes TEXT
);
```

**Confidence: HIGH** - Standard SQLite pattern. Python's built-in `sqlite3` module sufficient.

### 4. Web Review UI

Minimal Flask or FastAPI app for host classification before push.

**Option A: Flask (Recommended for simplicity)**
- Server-side rendered HTML
- Jinja2 templates
- Single file possible for small scope
- No build step

**Option B: FastAPI + HTMX**
- Modern, async-capable
- Auto-generated API docs
- HTMX for dynamic updates without full SPA
- Slightly more setup

**Confidence: HIGH** - Both frameworks well-documented. Flask simpler for HTML-first UI.

### 5. Push Engines

#### NetBox
- Library: `pynetbox` (official, maintained)
- Pattern: Check-then-create with idempotent updates
- Objects: Device, Interface, IP Address

#### Unbound DNS
- Method: Generate zone file or use `unbound-control`
- Pattern: Template-based file generation + reload
- No direct Python API; use subprocess

**Confidence: HIGH** (NetBox), **MEDIUM** (Unbound - file-based approach)

## Recommended Project Structure

```
netbox-automation/
├── pyproject.toml           # Project config, dependencies, CLI entry points
├── Makefile                  # Standard: format, lint, type, test, ci
├── CLAUDE.md                 # Project-specific guidance
├── README.md                 # Public documentation
│
├── src/
│   └── netbox_automation/
│       ├── __init__.py
│       ├── __main__.py       # python -m netbox_automation
│       ├── cli.py            # Click/Typer CLI definition
│       ├── config.py         # YAML config loading, validation
│       │
│       ├── collectors/       # Data source modules
│       │   ├── __init__.py
│       │   ├── base.py       # Abstract collector interface
│       │   ├── mikrotik.py   # MikroTik DHCP leases
│       │   ├── proxmox.py    # Proxmox VM inventory
│       │   ├── scanner.py    # Network scanner (nmap/scapy)
│       │   └── switch.py     # SNMP MAC table queries
│       │
│       ├── core/             # Shared business logic
│       │   ├── __init__.py
│       │   ├── models.py     # Pydantic models for hosts
│       │   ├── correlation.py # MAC-based correlation
│       │   └── database.py   # SQLite operations
│       │
│       ├── push/             # Output target modules
│       │   ├── __init__.py
│       │   ├── netbox.py     # pynetbox integration
│       │   └── unbound.py    # DNS zone generation
│       │
│       └── web/              # Review UI
│           ├── __init__.py
│           ├── app.py        # Flask/FastAPI app
│           ├── routes.py     # HTTP endpoints
│           └── templates/    # Jinja2 templates
│               ├── base.html
│               ├── hosts.html
│               └── host_detail.html
│
├── tests/
│   ├── conftest.py
│   ├── test_collectors/
│   ├── test_core/
│   └── test_push/
│
└── config.example.yaml       # Example configuration
```

**Confidence: HIGH** - Follows Python packaging standards (src layout, pyproject.toml).

## Data Flow Patterns

### Discovery Flow

```
1. CLI: `netbox-auto discover`
2. Load config.yaml (credentials, enabled collectors)
3. For each enabled collector:
   a. Connect to data source
   b. Fetch raw data
   c. Normalize to DiscoveredHost model
4. Correlate all hosts by MAC
5. Upsert into SQLite staging DB
6. Report: N new, M updated, X unchanged
```

### Review Flow

```
1. CLI: `netbox-auto serve` (starts on localhost:5000)
2. User opens browser
3. View pending hosts table (sortable, filterable)
4. For each host:
   - See merged data from all sources
   - Set classification (server, workstation, iot, etc.)
   - Approve or reject
5. Bulk actions available
6. Changes saved to SQLite immediately
```

### Push Flow

```
1. CLI: `netbox-auto push [--dry-run]`
2. Query SQLite for status='approved'
3. For each approved host:
   a. NetBox: Create/update device, interfaces, IPs
   b. Unbound: Add to pending DNS records
4. After NetBox success: Update status='pushed'
5. Generate Unbound zone file, trigger reload
6. Report: N pushed, M failed (with reasons)
```

## Integration Points

### Configuration File (config.yaml)

```yaml
# Example structure
collectors:
  mikrotik:
    enabled: true
    host: "router.local"
    username: "api-user"
    # password from env: MIKROTIK_PASSWORD

  proxmox:
    enabled: true
    host: "proxmox.local"
    user: "automation@pve"
    # token from env: PROXMOX_TOKEN

  scanner:
    enabled: false
    networks:
      - "192.168.1.0/24"

  switch:
    enabled: true
    devices:
      - host: "switch1.local"
        community: "public"

outputs:
  netbox:
    url: "https://netbox.local"
    # token from env: NETBOX_TOKEN
    site: "home-lab"
    default_role: "server"

  unbound:
    zone_file: "/etc/unbound/local.d/discovered.conf"
    reload_command: "sudo unbound-control reload"

database:
  path: "~/.local/share/netbox-automation/staging.db"

web:
  host: "127.0.0.1"
  port: 5000
```

**Confidence: HIGH** - Standard YAML config pattern. Secrets via environment variables.

### Key Libraries

| Purpose | Library | Version | Confidence |
|---------|---------|---------|------------|
| CLI | `click` or `typer` | latest | HIGH |
| Config | `pyyaml` + `pydantic` | latest | HIGH |
| MikroTik | `RouterOS-api` | >=0.17 | HIGH |
| Proxmox | `proxmoxer` | >=2.0 | HIGH |
| NetBox | `pynetbox` | >=7.0 | HIGH |
| Web UI | `flask` | >=3.0 | HIGH |
| Database | `sqlite3` (stdlib) | - | HIGH |
| Models | `pydantic` | >=2.0 | HIGH |
| Network scan | `python-nmap` | latest | MEDIUM |
| SNMP | `pysnmp` | latest | MEDIUM |

## Design Decisions

### Why SQLite for Staging?

1. Zero dependencies (Python stdlib)
2. File-based = easy backup/reset
3. Single-user access pattern fits CLI tool
4. SQL queries for filtering in web UI
5. ACID transactions for data integrity

**Confidence: HIGH**

### Why Flask over FastAPI?

For this use case (simple HTML review UI):
- Flask is simpler, less boilerplate
- Server-rendered HTML = no JS build step
- FastAPI advantages (async, auto-docs) not needed
- Flask's Jinja2 templates are sufficient

If API-first approach wanted later, FastAPI would be better.

**Confidence: MEDIUM** - Subjective; either works.

### Why Separate CLI Commands vs. Single Pipeline?

1. `discover` can run frequently (cron)
2. `serve` runs on-demand when reviewing
3. `push` can be manual or automated
4. Separation allows:
   - Review before any push
   - Re-run discovery without losing classifications
   - Dry-run push for validation

**Confidence: HIGH** - Common pattern in automation tools.

### MAC Address as Primary Correlation Key

- Most reliable cross-source identifier
- DHCP, VMs, and switch tables all report MAC
- IP addresses change; MACs are stable
- Handles multi-homed hosts (multiple IPs, same MAC)

Limitation: Virtual MACs, MAC spoofing, or shared MACs (VRRP) need special handling.

**Confidence: HIGH**

## Sources

### Network Discovery Tools
- [Natlas - Network Discovery and Auto-Diagramming](https://github.com/MJL85/natlas)
- [Secure Cartography - SSH-based discovery](https://github.com/scottpeterman/secure_cartography)
- [ndcrawl - CDP/LLDP Crawler](https://github.com/yantisj/ndcrawl)
- [Netwalk - Python network discovery library](https://developer.cisco.com/codeexchange/github/repo/nttitaly/netwalk/)

### Python Project Structure
- [Real Python - Python Application Layouts](https://realpython.com/python-application-layouts/)
- [Hitchhiker's Guide - Structuring Your Project](https://docs.python-guide.org/writing/structure/)
- [Cosmic Python - Template Project Structure](https://www.cosmicpython.com/book/appendix_project_structure.html)
- [Python Packaging Guide - CLI Tools](https://packaging.python.org/en/latest/guides/creating-command-line-tools/)

### API Libraries
- [pynetbox - NetBox Python client](https://github.com/netbox-community/pynetbox)
- [proxmoxer - Proxmox API wrapper](https://github.com/proxmoxer/proxmoxer)
- [RouterOS-api - MikroTik API client](https://github.com/socialwifi/RouterOS-api)

### Web Frameworks
- [Flask Documentation](https://flask.palletsprojects.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [JetBrains - Django vs Flask vs FastAPI](https://blog.jetbrains.com/pycharm/2025/02/django-flask-fastapi/)

### Data Pipeline Patterns
- [Start Data Engineering - Code Patterns](https://www.startdataengineering.com/post/code-patterns/)
- [Dagster - Pipeline Architecture Patterns](https://dagster.io/guides/data-pipeline/data-pipeline-architecture-5-design-patterns-with-examples)
- [Pybites - Pipeline Pattern in Python](https://pybit.es/articles/a-practical-example-of-the-pipeline-pattern-in-python/)

### Switch Port Mapping
- [SolarWinds - Switch Port Mapper](https://www.solarwinds.com/engineers-toolset/use-cases/switch-port-mapper)
- [SwitchMiner - Open source port mapper](https://switchminer.sourceforge.net/)

### DNS Integration
- [Unbound Documentation](https://unbound.docs.nlnetlabs.nl/)
- [Extending Unbound with Python](https://jpmens.net/2011/08/09/extending-unbound-with-python-module/)

---

*Research completed: 2026-01-15*
*Target: Python 3.11+, small-scale network automation tool*
