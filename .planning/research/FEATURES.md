# Network Discovery/Inventory Tool Features Research

Research completed: 2026-01-15

## Table Stakes (Users Expect These)

Features that users consider baseline for any network discovery/inventory tool:

### Discovery Capabilities
- **Multi-source discovery**: Pull hosts from DHCP leases, VMs, network scans (HIGH confidence - [Comparitech](https://www.comparitech.com/net-admin/best-network-discovery-tools-and-software/), [Faddom](https://faddom.com/best-network-discovery-tools-top-10-tools-to-know-in-2025/))
- **Device identification**: MAC address, hostname, IP address extraction (HIGH confidence - standard in all tools reviewed)
- **Scheduled/on-demand scans**: Ability to run discovery manually or on schedule (HIGH confidence - [StableNet](https://www.infosim.net/stablenet/network-discovery/))

### Data Management
- **Structured inventory database**: Searchable, filterable device records (HIGH confidence - universal feature)
- **Deduplication**: Correlate same device across sources using MAC address (HIGH confidence - [NetBox Labs](https://netboxlabs.com/docs/discovery/))
- **Export capabilities**: CSV, API access to inventory data (MEDIUM confidence - [MikroTik forums](https://forum.mikrotik.com/viewtopic.php?t=29597))

### Integration
- **NetBox sync**: Push discovered devices to NetBox (HIGH confidence - primary use case, multiple plugins exist: [ntc-netbox-plugin-onboarding](https://github.com/networktocode/ntc-netbox-plugin-onboarding), [Slurp'it](https://slurpit.io/use-cases/new-netbox-slurpit-plugin-to-discover-onboard-your-network-in-no-time/))
- **API-first design**: REST API for automation integration (HIGH confidence - expected for automation tools)

### User Experience
- **Status tracking**: Know what's been discovered, synced, failed (HIGH confidence - [NetBox onboarding plugin](https://github.com/networktocode/ntc-netbox-plugin-onboarding) tracks task status)
- **Clear error reporting**: Why did discovery/sync fail? (MEDIUM confidence - common complaint when missing)

## Differentiators (Competitive Advantage)

Features that would set this tool apart for home/lab environments:

### Unique to This Project
- **MikroTik DHCP + Proxmox + scan correlation**: Most tools focus on enterprise protocols (SNMP, CDP/LLDP). Combining consumer-grade router DHCP with hypervisor APIs is underserved (MEDIUM confidence - gap identified in research)
- **Switch port MAC correlation**: Knowing which switch port a device is on via MAC table queries (HIGH confidence - [Cisco documentation](https://www.cisco.com/c/en/us/support/docs/ip/simple-network-management-protocol-snmp/44800-mactoport44800.html) shows this is valuable but often manual)
- **Unbound DNS automation**: Auto-generating DNS records from discovered hosts (MEDIUM confidence - limited tooling exists for this integration)

### Workflow Differentiators
- **Human-in-the-loop review**: Web UI for approving changes before push (HIGH confidence - [Slurp'it reconciliation](https://slurpit.io/use-cases/new-netbox-slurpit-plugin-to-discover-onboard-your-network-in-no-time/), [NetBox branching](https://netboxlabs.com/blog/diode-now-supports-branching-change-control-for-data-ingestion/))
- **Diff preview**: Show what will change in NetBox/DNS before applying (MEDIUM confidence - enterprise tools have this, smaller tools often lack it)
- **CLI + web hybrid**: CLI for power users/automation, web for review (MEDIUM confidence - most tools are one or the other)

### Home Lab Focused
- **Simple deployment**: Single binary/container, minimal dependencies (HIGH confidence - [Rack Root](https://medium.com/@a.j.longchamps/introducing-rack-root-the-home-lab-inventory-tracking-system-053e557c8250), [HomeBox](https://www.xda-developers.com/self-hosted-inventory-app/) emphasize simplicity)
- **No agent requirement**: Agentless discovery for home equipment (HIGH confidence - agents impractical for IoT/embedded devices)
- **Low resource usage**: Run on Raspberry Pi or small VM (LOW confidence - assumed preference, not explicitly researched)

## Anti-Features (Commonly Requested but Problematic)

Features to avoid or defer despite user requests:

### Complexity Traps
- **Automatic approval/sync**: Pushing changes without review leads to data quality issues (HIGH confidence - [NetBox Labs branching post](https://netboxlabs.com/blog/diode-now-supports-branching-change-control-for-data-ingestion/) emphasizes review)
- **Full network topology mapping**: Layer 2/3 topology visualization is a rabbit hole (MEDIUM confidence - scope creep risk, enterprise tools spend years on this)
- **Agent-based discovery**: Requires deployment to each device, impractical for home labs (HIGH confidence - [Comparitech](https://www.comparitech.com/net-admin/best-network-discovery-tools-and-software/) notes deployment burden)

### Security Risks
- **Storing credentials in config files**: Router/switch credentials need secure handling (HIGH confidence - [NIST IoT onboarding](https://www.nccoe.nist.gov/projects/trusted-iot-device-network-layer-onboarding-and-lifecycle-management))
- **Automated network changes**: Discovery should be read-only initially (MEDIUM confidence - reduces blast radius)

### Over-Engineering
- **AI/ML anomaly detection**: Overkill for home labs, adds complexity (LOW confidence - enterprise trend, not needed for MVP)
- **Multi-tenant support**: Home lab tool doesn't need isolation between users (LOW confidence - assumption)
- **Historical trending/analytics**: Nice-to-have, not core discovery function (MEDIUM confidence - scope discipline)

## Feature Dependencies

### Dependency Graph

```
MikroTik DHCP discovery
    └── requires: RouterOS API access
    └── enables: hostname extraction, lease tracking

Proxmox VM discovery
    └── requires: Proxmox API token
    └── enables: VM inventory, IP extraction via QEMU agent

Network scan discovery
    └── requires: nmap or similar
    └── enables: finding devices not in DHCP/VM sources

MAC table correlation
    └── requires: Switch SNMP/API access (optional)
    └── enables: physical port mapping

NetBox sync
    └── requires: NetBox API token
    └── depends on: device correlation/deduplication
    └── enables: DCIM/IPAM population

Unbound DNS update
    └── requires: write access to Unbound config dir
    └── depends on: confirmed/approved devices only
    └── enables: automatic DNS resolution
```

### Phased Approach
1. **Phase 1**: Discovery from sources (read-only, low risk)
2. **Phase 2**: Correlation and deduplication (internal processing)
3. **Phase 3**: Review UI (human approval)
4. **Phase 4**: NetBox push (external writes)
5. **Phase 5**: DNS update (external writes)

## MVP Definition (What's Needed for v1)

### Must Have (v1.0)
- [ ] MikroTik DHCP lease discovery via RouterOS API
- [ ] Proxmox VM discovery via API
- [ ] Basic network scan (nmap wrapper or native)
- [ ] MAC-based correlation across sources
- [ ] CLI for running discovery
- [ ] SQLite storage for discovered hosts
- [ ] Simple web UI to view discoveries
- [ ] Approve/reject workflow for individual hosts
- [ ] NetBox device creation for approved hosts
- [ ] Basic Unbound config generation

### Should Have (v1.x)
- [ ] Switch MAC table queries (SNMP)
- [ ] Scheduled discovery runs
- [ ] Bulk approve/reject in web UI
- [ ] Diff preview before NetBox push
- [ ] DNS conflict detection

### Could Have (v2.0+)
- [ ] Multiple NetBox site support
- [ ] Custom field mapping
- [ ] Webhook notifications
- [ ] Discovery profiles (different source configs)
- [ ] Historical change tracking

### Won't Have (Out of Scope)
- Full topology mapping
- Agent-based discovery
- Multi-tenant isolation
- Enterprise SNMP discovery (Cisco CDP/LLDP crawling)
- AI/ML features

## Sources

### Primary Sources (HIGH Confidence)
- [Comparitech - Best Network Discovery Tools](https://www.comparitech.com/net-admin/best-network-discovery-tools-and-software/)
- [Faddom - Best Network Discovery Tools 2025](https://faddom.com/best-network-discovery-tools-top-10-tools-to-know-in-2025/)
- [NetBox Labs - Discovery Documentation](https://netboxlabs.com/docs/discovery/)
- [NTC NetBox Onboarding Plugin](https://github.com/networktocode/ntc-netbox-plugin-onboarding)
- [Slurp'it NetBox Plugin](https://slurpit.io/use-cases/new-netbox-slurpit-plugin-to-discover-onboard-your-network-in-no-time/)
- [NetBox Proxbox Plugin](https://github.com/netdevopsbr/netbox-proxbox)
- [ProxSyncBox](https://github.com/WDutra22/ProxSyncBox)

### Secondary Sources (MEDIUM Confidence)
- [XDA - Mapping Home Lab Machines](https://www.xda-developers.com/i-mapped-every-machine-in-my-home-lab-with-this-free-tool/)
- [Rack Root - Home Lab Inventory](https://medium.com/@a.j.longchamps/introducing-rack-root-the-home-lab-inventory-tracking-system-053e557c8250)
- [MikroTik Forums - DHCP Export](https://forum.mikrotik.com/viewtopic.php?t=29597)
- [Cisco - SNMP MAC to Port](https://www.cisco.com/c/en/us/support/docs/ip/simple-network-management-protocol-snmp/44800-mactoport44800.html)
- [NetBox Labs - Diode Branching](https://netboxlabs.com/blog/diode-now-supports-branching-change-control-for-data-ingestion/)

### Tertiary Sources (LOW Confidence)
- [Resolve - Automation Anti-patterns](https://resolve.io/blog/top-automation-mistakes)
- [NIST - IoT Onboarding](https://www.nccoe.nist.gov/projects/trusted-iot-device-network-layer-onboarding-and-lifecycle-management)
- [Dev.to - Home Lab Monitoring Tools](https://dev.to/boniyeamincse/open-source-network-monitoring-tools-for-home-lab-3p23)

---

## Key Insights for This Project

1. **Gap in the market**: Most discovery tools target enterprise (SNMP, CDP/LLDP). The MikroTik + Proxmox + home lab focus is underserved.

2. **Review workflow is critical**: Enterprise tools (NetBox Diode, Slurp'it) emphasize staging/branching/review. Auto-sync leads to data quality problems.

3. **Simplicity wins for home labs**: Complex tools like NetBox Discovery require significant setup. A focused CLI + simple web UI is appropriate.

4. **MAC address is the correlation key**: Across DHCP leases, VM configs, and switch ports, MAC is the stable identifier.

5. **Start read-only**: Discovery should be safe. Writes to NetBox/DNS are opt-in after review.
