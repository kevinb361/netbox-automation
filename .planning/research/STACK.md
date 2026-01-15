# Technology Stack Research

**Research Date:** 2026-01-15
**Target:** Python 3.11+ | Network automation / infrastructure discovery tool
**Purpose:** Discover hosts from MikroTik DHCP, Proxmox VMs, network scans; correlate with switch port MAC tables; push to NetBox; update Unbound DNS

---

## Summary Recommendations

| Category | Primary Choice | Version | Confidence |
|----------|----------------|---------|------------|
| MikroTik API | librouteros | 3.4.1 | HIGH |
| Proxmox API | proxmoxer | 2.2.0 | HIGH |
| NetBox API | pynetbox | 7.6.0 | HIGH |
| Network Scanning | scapy | 2.7.0 | HIGH |
| SSH Automation | asyncssh | 2.22.0 | HIGH |
| CLI Framework | typer | 0.21.1 | HIGH |
| Web UI | NiceGUI | 3.5.0 | MEDIUM |
| Terminal Output | rich | 14.2.0 | HIGH |

---

## 1. MikroTik RouterOS API

### Primary: librouteros

**Version:** 3.4.1 (Dec 2024)
**License:** GPL-2.0+
**Python:** 3.8 - 3.13
**Confidence:** HIGH (official docs, active maintenance, Ansible integration)

```bash
pip install librouteros
```

**Rationale:**
- Used by Ansible community.routeros collection (production-proven)
- Memory-efficient: yields items instead of returning tuples
- Path object for easy queries
- Explicit login_method parameter for RouterOS 6.43+ auth
- Actively maintained with December 2024 release

**Basic Usage:**
```python
from librouteros import connect

api = connect(
    host='192.168.88.1',
    username='admin',
    password='password',
    port=8728
)

# Get DHCP leases
dhcp = api.path('/ip/dhcp-server/lease')
for lease in dhcp:
    print(lease['mac-address'], lease.get('host-name', 'unknown'))
```

**Sources:**
- [librouteros PyPI](https://pypi.org/project/librouteros/)
- [librouteros GitHub](https://github.com/luqasz/librouteros)
- [Ansible community.routeros](https://docs.ansible.com/ansible/latest/collections/community/routeros/api_module.html)

### Alternative: RouterOS-api

**Version:** 0.21.0 (Mar 2025)
**License:** MIT
**Python:** 3.9 - 3.12
**Confidence:** HIGH

```bash
pip install RouterOS-api
```

**When to use instead:**
- MIT license preferred over GPL
- Simpler API for basic use cases
- SSL context flexibility needed

**Sources:**
- [RouterOS-api PyPI](https://pypi.org/project/RouterOS-api/)
- [RouterOS-api GitHub](https://github.com/socialwifi/RouterOS-api)

---

## 2. Proxmox VE API

### Primary: proxmoxer

**Version:** 2.2.0 (Dec 2024)
**License:** MIT
**Python:** 3.8 - 3.12
**Confidence:** HIGH (official wrapper, well-documented)

```bash
pip install proxmoxer
```

**Rationale:**
- Official Python wrapper for Proxmox API v2
- Supports PVE, PMG, and PBS
- Multiple backends: HTTPS, SSH (via pvesh)
- Dynamic attribute creation for API endpoints
- Well-documented with active maintenance

**Basic Usage:**
```python
from proxmoxer import ProxmoxAPI

proxmox = ProxmoxAPI(
    'proxmox.example.com',
    user='root@pam',
    password='secret',
    verify_ssl=False  # Remove for valid certs
)

# List all VMs across cluster
for node in proxmox.nodes.get():
    for vm in proxmox.nodes(node['node']).qemu.get():
        print(f"{vm['vmid']}: {vm['name']} ({vm['status']})")

# Get VM network config
vm_config = proxmox.nodes('pve1').qemu(100).config.get()
print(vm_config.get('net0'))
```

**Token Authentication (recommended):**
```python
proxmox = ProxmoxAPI(
    'proxmox.example.com',
    user='automation@pve',
    token_name='discovery',
    token_value='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
    verify_ssl=True
)
```

**Sources:**
- [proxmoxer PyPI](https://pypi.org/project/proxmoxer/)
- [proxmoxer GitHub](https://github.com/proxmoxer/proxmoxer)
- [proxmoxer Docs](https://proxmoxer.github.io/docs/latest/)

---

## 3. NetBox API

### Primary: pynetbox

**Version:** 7.6.0 (Jan 2026)
**License:** Apache 2.0
**Python:** 3.10 - 3.12
**NetBox:** 3.3+
**Confidence:** HIGH (official community library)

```bash
pip install pynetbox
```

**Rationale:**
- Official NetBox community library
- Threading support for parallel queries
- RecordSet generators for memory efficiency
- Strict filter validation option
- Comprehensive endpoint coverage

**Basic Usage:**
```python
import pynetbox

nb = pynetbox.api(
    'https://netbox.example.com',
    token='your-api-token',
    threading=True  # Enable parallel queries
)

# Create/update device
device = nb.dcim.devices.create(
    name='server01',
    device_type=1,
    role=1,
    site=1,
    status='active'
)

# Create interface with MAC
interface = nb.dcim.interfaces.create(
    device=device.id,
    name='eth0',
    type='1000base-t',
    mac_address='00:11:22:33:44:55'
)

# Assign IP address
ip = nb.ipam.ip_addresses.create(
    address='192.168.1.100/24',
    assigned_object_type='dcim.interface',
    assigned_object_id=interface.id
)
```

**Performance Tips:**
```python
# Threading for large datasets
nb = pynetbox.api(url, token=token, threading=True)

# Exclude config_context for speed
devices = nb.dcim.devices.filter(exclude='config_context')

# Strict filter validation
nb = pynetbox.api(url, token=token, strict_filters=True)
```

**Sources:**
- [pynetbox PyPI](https://pypi.org/project/pynetbox/)
- [pynetbox GitHub](https://github.com/netbox-community/pynetbox)
- [pynetbox Docs](https://netbox-community.github.io/pynetbox/)

---

## 4. Network Scanning

### Primary: scapy

**Version:** 2.7.0 (Dec 2025)
**License:** GPL-2.0
**Python:** 3.7+ (3.9+ recommended for Python 3.7/3.8 EOL)
**Confidence:** HIGH (industry standard)

```bash
pip install scapy
```

**Rationale:**
- Industry-standard packet manipulation library
- ARP scanning for host discovery
- Cross-platform (Linux, macOS, Windows)
- No external dependencies for basic scanning
- Extensive protocol support

**ARP Network Scan:**
```python
from scapy.all import ARP, Ether, srp

def arp_scan(network: str) -> list[dict]:
    """Scan network for hosts using ARP.

    Requires root/sudo privileges.
    """
    arp = ARP(pdst=network)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether / arp

    result = srp(packet, timeout=3, verbose=0)[0]

    hosts = []
    for sent, received in result:
        hosts.append({
            'ip': received.psrc,
            'mac': received.hwsrc
        })
    return hosts

# Usage (requires sudo)
hosts = arp_scan('192.168.1.0/24')
```

**Note:** Requires root/sudo for raw socket access.

**Sources:**
- [scapy PyPI](https://pypi.org/project/scapy/)
- [scapy GitHub](https://github.com/secdev/scapy)
- [scapy Docs](https://scapy.readthedocs.io/)

### Alternative: python-nmap

**Version:** 0.7.1
**Confidence:** MEDIUM (stable but less active)

```bash
pip install python-nmap
```

**When to use instead:**
- Need service detection beyond ARP
- Port scanning required
- OS fingerprinting needed
- nmap already installed on system

**Basic Usage:**
```python
import nmap

nm = nmap.PortScanner()
nm.scan(hosts='192.168.1.0/24', arguments='-sn')  # Ping scan

for host in nm.all_hosts():
    print(f"{host}: {nm[host].hostname()}")
```

**Sources:**
- [python-nmap PyPI](https://pypi.org/project/python-nmap/)

---

## 5. SSH Automation

### Primary: asyncssh

**Version:** 2.22.0 (2025)
**License:** EPL-2.0
**Python:** 3.8+
**Confidence:** HIGH (active development, async-native)

```bash
pip install asyncssh
```

**Rationale:**
- Native asyncio support
- Handles multiple connections efficiently
- Full SSHv2, SFTP, SCP support
- Proven in production (used by Suzieq)
- Active development through 2025

**Basic Usage (Unbound config update):**
```python
import asyncssh

async def update_unbound_config(host: str, config_content: str):
    """Update Unbound DNS configuration via SSH."""
    async with asyncssh.connect(host, username='admin') as conn:
        # Write config
        async with conn.start_sftp_client() as sftp:
            async with sftp.open('/etc/unbound/local.d/hosts.conf', 'w') as f:
                await f.write(config_content)

        # Reload Unbound
        result = await conn.run('sudo unbound-control reload', check=True)
        return result.exit_status == 0

# Multiple hosts in parallel
async def update_all_dns_servers(servers: list[str], config: str):
    tasks = [update_unbound_config(s, config) for s in servers]
    return await asyncio.gather(*tasks)
```

**Sources:**
- [asyncssh PyPI](https://pypi.org/project/asyncssh/)
- [asyncssh GitHub](https://github.com/ronf/asyncssh)
- [asyncssh Docs](https://asyncssh.readthedocs.io/)

### Alternative: Fabric

**Version:** 3.2.2 (Oct 2024)
**License:** BSD-2-Clause
**Confidence:** HIGH

```bash
pip install fabric
```

**When to use instead:**
- Synchronous code preferred
- Simple command execution
- Existing Fabric experience

**Sources:**
- [Fabric Docs](https://www.fabfile.org/)
- [paramiko Docs](https://www.paramiko.org/)

---

## 6. CLI Framework

### Primary: typer

**Version:** 0.21.1 (Jan 2026)
**License:** MIT
**Python:** 3.9+
**Confidence:** HIGH (modern, well-maintained, type-hint based)

```bash
pip install typer[all]  # Includes rich and shellingham
```

**Rationale:**
- Type hint-based (modern Python)
- Automatic help generation
- Shell completion for all shells
- Built on Click (battle-tested)
- Integrates with Rich for beautiful output
- Active development by FastAPI author

**Basic Usage:**
```python
import typer
from typing import Optional

app = typer.Typer(help="NetBox Automation Tool")

@app.command()
def discover(
    network: str = typer.Argument(..., help="Network CIDR to scan"),
    mikrotik: Optional[str] = typer.Option(None, help="MikroTik router IP"),
    proxmox: Optional[str] = typer.Option(None, help="Proxmox host"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Don't push to NetBox")
):
    """Discover hosts and push to NetBox."""
    typer.echo(f"Scanning {network}...")

@app.command()
def sync():
    """Sync discovered hosts to NetBox."""
    pass

if __name__ == "__main__":
    app()
```

**Sources:**
- [typer PyPI](https://pypi.org/project/typer/)
- [typer Docs](https://typer.tiangolo.com/)
- [typer GitHub](https://github.com/tiangolo/typer)

---

## 7. Web UI Framework

### Primary: NiceGUI

**Version:** 3.5.0
**License:** MIT
**Python:** 3.8+
**Confidence:** MEDIUM (newer, but well-designed for dashboards)

```bash
pip install nicegui
```

**Rationale:**
- Pure Python (no JS required)
- Built on FastAPI + Vue + Quasar
- WebSocket-based real-time updates
- Great for internal dashboards
- Tailwind CSS styling
- Low learning curve

**Basic Usage:**
```python
from nicegui import ui

@ui.page('/')
def index():
    ui.label('NetBox Automation Dashboard').classes('text-2xl')

    with ui.card():
        ui.label('Recent Discoveries')
        table = ui.table(
            columns=[
                {'name': 'ip', 'label': 'IP Address', 'field': 'ip'},
                {'name': 'mac', 'label': 'MAC Address', 'field': 'mac'},
                {'name': 'source', 'label': 'Source', 'field': 'source'},
            ],
            rows=[]
        )

    async def refresh():
        # Fetch data and update table
        pass

    ui.button('Refresh', on_click=refresh)

ui.run(port=8080)
```

**Sources:**
- [NiceGUI PyPI](https://pypi.org/project/nicegui/)
- [NiceGUI GitHub](https://github.com/zauberzeug/nicegui)
- [NiceGUI Docs](https://nicegui.io/)

### Alternative: Streamlit

**Version:** Latest 2025
**Confidence:** HIGH (mature, data-focused)

```bash
pip install streamlit
```

**When to use instead:**
- Data visualization heavy
- Rapid prototyping
- Jupyter-like workflow preferred

**Sources:**
- [Streamlit Docs](https://docs.streamlit.io/)

### Alternative: FastAPI + Jinja2

**Confidence:** HIGH

**When to use instead:**
- Need REST API alongside UI
- Custom frontend required
- Maximum flexibility needed

---

## 8. Terminal Output

### Primary: rich

**Version:** 14.2.0 (Oct 2025)
**License:** MIT
**Python:** 3.8+
**Confidence:** HIGH (industry standard, Typer integration)

```bash
pip install rich
```

**Rationale:**
- Beautiful terminal output
- Tables, progress bars, syntax highlighting
- Integrated with Typer
- Cross-platform
- Jupyter support

**Basic Usage:**
```python
from rich.console import Console
from rich.table import Table
from rich.progress import track

console = Console()

# Progress bar
for host in track(hosts, description="Scanning..."):
    process(host)

# Table output
table = Table(title="Discovered Hosts")
table.add_column("IP", style="cyan")
table.add_column("MAC", style="green")
table.add_column("Source", style="yellow")

for host in hosts:
    table.add_row(host['ip'], host['mac'], host['source'])

console.print(table)
```

**Sources:**
- [rich PyPI](https://pypi.org/project/rich/)
- [rich GitHub](https://github.com/Textualize/rich)
- [rich Docs](https://rich.readthedocs.io/)

---

## Installation Summary

### requirements.txt (Minimal)

```
# Core APIs
librouteros>=3.4.0
proxmoxer>=2.2.0
pynetbox>=7.5.0

# Network scanning
scapy>=2.7.0

# SSH automation
asyncssh>=2.21.0

# CLI
typer[all]>=0.21.0

# Terminal output (included with typer[all])
rich>=14.0.0
```

### requirements.txt (Full with Web UI)

```
# Core APIs
librouteros>=3.4.0
proxmoxer>=2.2.0
pynetbox>=7.5.0

# Network scanning
scapy>=2.7.0

# SSH automation
asyncssh>=2.21.0

# CLI
typer[all]>=0.21.0

# Web UI
nicegui>=3.5.0

# Terminal output
rich>=14.0.0
```

### Installation Commands

```bash
# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install with pip
pip install -r requirements.txt

# Or with uv (faster)
uv pip install -r requirements.txt
```

---

## Architecture Notes

### Async Considerations

- **pynetbox:** Uses threading, not asyncio. Wrap with `asyncio.to_thread()` if needed.
- **proxmoxer:** Synchronous. Use `asyncio.to_thread()` for async contexts.
- **librouteros:** Synchronous. Use `asyncio.to_thread()` for async contexts.
- **asyncssh:** Native asyncio - preferred for SSH operations.
- **scapy:** Synchronous. Run in thread pool for async integration.

### Async Integration Pattern

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)

async def get_mikrotik_leases(router_ip: str):
    """Wrap synchronous librouteros in async."""
    def _get_leases():
        api = connect(host=router_ip, ...)
        return list(api.path('/ip/dhcp-server/lease'))

    return await asyncio.get_event_loop().run_in_executor(
        executor, _get_leases
    )
```

### Error Handling

All libraries may raise connection/authentication errors. Implement retry logic:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
def connect_with_retry(host, **kwargs):
    return connect(host=host, **kwargs)
```

---

## Confidence Levels

| Level | Meaning |
|-------|---------|
| HIGH | Official docs, PyPI verified, active maintenance, production-proven |
| MEDIUM | Community consensus, recent updates, limited production data |
| LOW | Blog posts only, unverified, or outdated information |

---

## Research Sources

### Official Documentation
- [MikroTik API Docs](https://help.mikrotik.com/docs/spaces/ROS/pages/47579209/Python3+Example)
- [Proxmox VE API](https://pve.proxmox.com/wiki/Proxmox_VE_API)
- [NetBox API](https://netboxlabs.com/docs/)
- [Scapy Docs](https://scapy.readthedocs.io/)
- [AsyncSSH Docs](https://asyncssh.readthedocs.io/)
- [Typer Docs](https://typer.tiangolo.com/)
- [NiceGUI Docs](https://nicegui.io/)
- [Rich Docs](https://rich.readthedocs.io/)

### PyPI Package Pages
- [librouteros](https://pypi.org/project/librouteros/)
- [proxmoxer](https://pypi.org/project/proxmoxer/)
- [pynetbox](https://pypi.org/project/pynetbox/)
- [scapy](https://pypi.org/project/scapy/)
- [asyncssh](https://pypi.org/project/asyncssh/)
- [typer](https://pypi.org/project/typer/)
- [nicegui](https://pypi.org/project/nicegui/)
- [rich](https://pypi.org/project/rich/)

### GitHub Repositories
- [librouteros](https://github.com/luqasz/librouteros)
- [proxmoxer](https://github.com/proxmoxer/proxmoxer)
- [pynetbox](https://github.com/netbox-community/pynetbox)
- [scapy](https://github.com/secdev/scapy)
- [asyncssh](https://github.com/ronf/asyncssh)
- [typer](https://github.com/tiangolo/typer)
- [nicegui](https://github.com/zauberzeug/nicegui)
- [rich](https://github.com/Textualize/rich)
