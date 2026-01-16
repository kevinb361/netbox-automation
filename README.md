# NetBox Automation

Network discovery tool that collects hosts from multiple sources, correlates them by MAC address to switch ports, and pushes to NetBox with DNS updates.

## Features

- **Multi-source discovery**: MikroTik DHCP leases, Proxmox VMs, ARP network scans, switch MAC tables
- **MAC-based correlation**: Merges host data across sources using MAC address as primary key
- **Web UI for review**: Approve, reject, and classify hosts before pushing
- **NetBox integration**: Creates devices, VMs, IP assignments, and cable records
- **DNS updates**: Pushes records to Unbound DNS servers via SSH

## Requirements

- Python 3.11+
- MikroTik router with API enabled
- NetBox instance with API access
- Optional: Proxmox server, Unbound DNS servers

## Installation

```bash
# Clone the repository
git clone git@gitea:kevin/netbox-automation.git
cd netbox-automation

# Create virtual environment and install
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Configuration

Copy the example config and fill in your credentials:

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml` with your settings:

```yaml
mikrotik:
  host: "192.168.1.1"
  username: "admin"
  password: ""  # Use env var instead

proxmox:
  host: "proxmox.local"
  username: "root@pam"
  password: ""

netbox:
  url: "https://netbox.local"
  token: ""

unbound:
  hosts:
    - host: "dns1.local"
      user: "root"
      config_path: "/etc/unbound/local.d/local.conf"
```

Secrets can be set via environment variables:

```bash
export NETBOX_AUTO_MIKROTIK__PASSWORD=secret
export NETBOX_AUTO_NETBOX__TOKEN=abc123
```

## Usage

### Discover hosts

```bash
netbox-auto discover
```

Runs all configured collectors (DHCP, Proxmox, network scan, switch MACs) and stores results in the local database.

### Review hosts

```bash
netbox-auto serve
```

Opens web UI at http://127.0.0.1:5000 to review, classify, and approve discovered hosts.

### Push to NetBox

```bash
# Preview changes
netbox-auto push --dry-run

# Push approved hosts
netbox-auto push
```

Creates NetBox devices/VMs, cable records, and updates DNS.

### Check status

```bash
netbox-auto status
```

Shows counts of discovered hosts by status and type.

## CLI Reference

```
netbox-auto --help              Show help
netbox-auto --version           Show version
netbox-auto -c FILE             Use alternate config file

netbox-auto discover            Run discovery from all sources
netbox-auto serve               Start web UI (default: localhost:5000)
netbox-auto serve -p 8080       Use alternate port
netbox-auto push                Push approved hosts to NetBox/DNS
netbox-auto push --dry-run      Preview without changes
netbox-auto push --skip-dns     Push to NetBox only
netbox-auto status              Show discovery/push summary
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all checks
make ci

# Individual commands
make format    # Black + Ruff
make lint      # Ruff
make type      # MyPy
make test      # Pytest
```

## License

MIT
