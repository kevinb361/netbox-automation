# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-16

### Added

- **Discovery**
  - MikroTik DHCP lease collector via RouterOS API
  - Proxmox VM collector via Proxmox API (with QEMU guest agent support)
  - Network scanner using ARP for static IP discovery
  - Switch MAC table collector for host-to-port correlation
  - MAC-based host correlation merging data across sources

- **Data Management**
  - SQLite staging database for discovered hosts
  - Host status tracking (pending/approved/rejected/pushed)
  - Host type classification (server/workstation/IoT/network)
  - Discovery run history with timestamps

- **Web UI**
  - Flask-based review interface
  - Host table with filtering and sorting
  - Approve/reject/classify individual hosts
  - Bulk actions for multiple hosts
  - NetBox reconciliation view (new/matched/stale)

- **NetBox Integration**
  - Device and VM creation with IP assignments
  - Cable record creation (switch port to device)
  - Import existing NetBox devices for comparison
  - Stale entry detection

- **DNS Updates**
  - Unbound DNS config generation
  - SSH-based push to multiple DNS servers
  - Automatic service reload after updates

- **CLI**
  - `discover` - Run all collectors
  - `serve` - Start web UI
  - `push` - Push to NetBox and DNS (with `--dry-run`)
  - `status` - Show discovery/push summary
  - YAML config with environment variable overrides

[1.0.0]: https://github.com/kevinb361/netbox-automation/releases/tag/v1.0
