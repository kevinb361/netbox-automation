# Architecture — netbox-automation

<!--
_meta:
  updated_at: 2026-04-27T15:55:00Z
  version: 2
  scope: Architectural shape captured from CLAUDE.md, README.md, pyproject.toml, and the src/netbox_auto/ implementation as of v0.1.0.
-->

netbox-automation is a single-operator CLI tool that pulls host inventory from heterogeneous network sources, lets a human review and classify the result, then writes the approved subset into NetBox plus Unbound DNS. The whole loop is offline-friendly: the staging database is local SQLite, the review UI binds to localhost, and the push step is idempotent and dry-runnable.

## Pipeline

```
Collectors → Discovery → Staging DB → Web Review → Push → NetBox + DNS
(discover)               (SQLite)     (serve)            (push)
```

Each step is a separate CLI command (`netbox-auto discover|serve|push|status`). The staging DB is the contract between steps — both the web UI and the push command read from it.

## Modules

- **`cli.py`** — Typer app. Loads config and runs `init_db()` in the top-level callback before any subcommand fires. Console-script `netbox-auto` is registered in `pyproject.toml` to `netbox_auto.cli:app`.
- **`config.py`** — Pydantic v2 models (`MikroTikConfig`, `SwitchConfig`, `ProxmoxConfig`, `NetBoxConfig`, `UnboundConfig` containing a list of `UnboundHostConfig`, `ScannerConfig`) plus a top-level `Config`. YAML file loader is merged with environment overrides under prefix `NETBOX_AUTO_<SECTION>__<FIELD>` — secrets travel through env, not the YAML.
- **`database.py`** — SQLAlchemy 2 engine + `sessionmaker` against `netbox-auto.db`. `init_db()` is idempotent.
- **`models.py`** — SQLAlchemy 2 ORM with `Mapped`/`mapped_column`. Two tables: `discovery_run` (status, timestamps) and `host` (MAC unique-indexed; `ip_addresses` is JSON; `host_type` and `status` are persisted as the value of their respective enums). `host.mac` carries an extra `ix_host_mac_lookup` index.
- **`discovery.py`** — Orchestrator. `run_discovery()` creates a `DiscoveryRun`, runs the host collectors (DHCP, Proxmox, Scanner) and the Switch collector for MAC-to-port mappings, merges hosts by lowercased MAC, picks hostname by priority (DHCP > Proxmox > Scan), filters IPv6 unless `discovery.include_ipv6=true`, then upserts into `host`.
- **`reconcile.py`** — Bridges the staging DB and NetBox: `import_netbox_devices()` pulls existing devices/VMs into the staging DB; `reconcile_hosts()` classifies new vs matched vs stale.
- **`push.py`** — `push_approved_hosts(dry_run, skip_netbox, skip_dns)` iterates `Host.status == APPROVED`, creates the NetBox device/VM + cable records via `netbox.py`, updates DNS via `dns.py`, and marks each host `PUSHED`.
- **`netbox.py`** — pynetbox wrapper with **lazy connection** (no API call in `__init__`).
- **`dns.py`** — Generates Unbound `local-data:` records and pushes them via paramiko SSH, atomically replacing the configured `local.conf` path on each Unbound host.
- **`web/app.py`** — Flask app factory + `main` blueprint. Routes for the hosts table, status/type updates (single + bulk), and a reconciliation view + import action.
- **`collectors/`** — Each collector implements the `Collector` Protocol (name + `collect() -> list[DiscoveredHost]`) defined in `base.py`. `DiscoveredHost.__post_init__` normalizes MAC to lowercase colon format.

## Decisions

- **MAC is the primary key for correlation.** DHCP, Proxmox guest agents, ARP scans, and switch MAC tables all surface MAC addresses; merging on MAC is the only way to fuse them.
- **Source priority is fixed: DHCP > Proxmox > Scan.** DHCP is the most specific (named lease entries); Proxmox is structured but VM-name-based; ARP scan rarely yields hostnames at all. The same priority drives both `_pick_hostname` and `_pick_primary_source`.
- **Human-in-the-loop is mandatory.** The web UI exists because production NetBox should not be written from auto-discovery alone — every host transitions `pending → approved/rejected` before push, and bulk approval is a UI primitive, not a CLI flag.
- **Lazy NetBox connection.** The pynetbox client connects on first use, not at construction. This keeps `--help`, `status`, and `discover` runnable without NetBox reachability.
- **Secrets via environment variables.** YAML is for shape; env vars carry tokens and passwords. The `NETBOX_AUTO_<SECTION>__<FIELD>` convention is documented in CLAUDE.md and respected by pydantic-settings.
- **Idempotent push with dry-run and partial skip.** `--dry-run` previews changes without writing; `--skip-netbox` and `--skip-dns` allow partial pushes when one side is unavailable.
- **IPv6 opt-in.** `discovery.include_ipv6` defaults to false. Most homelab/SMB inventories care about v4 first; v6 surfaces a lot of link-local noise that would clutter NetBox.
- **Local SQLite staging.** No external state store. The DB is portable, recoverable, and survives across discovery sessions; the same file backs the review UI and the push step.
- **Strict typing posture.** MyPy `strict = true`, with `disable_error_code = ["import-untyped"]` to accommodate libraries (pynetbox, librouteros, proxmoxer, scapy, flask) that lack type stubs. Per-module `ignore_missing_imports` overrides are explicit in `pyproject.toml`.
- **Switch port mapping is best-effort.** `Host.switch_port` is optional and only filled when a switch collector finds a matching MAC. The merge step preserves an existing port over a missing one (`existing.switch_port = switch_port or existing.switch_port`).

## Out of Scope (per implementation choices)

- Continuous discovery / scheduling — `discover` is a one-shot command.
- Multi-tenant or multi-user review — single-operator tool, web UI binds to `127.0.0.1` by default.
- Direct NetBox webhook / push from collectors — the staging DB sits between every collector and NetBox.
- Authentication on the review UI — relies on local-only binding and trusted operator.
