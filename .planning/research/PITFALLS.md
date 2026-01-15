# Network Automation Pitfalls Research

Research findings on common mistakes when integrating with MikroTik, Proxmox, NetBox, and related network automation tools.

---

## Critical Pitfalls

### 1. Privilege Separation on Proxmox API Tokens (HIGH)

**The Mistake**: Creating an API token with privilege separation enabled (the default) and expecting it to work like the parent user account.

**What Happens**: API calls return `data: null` or empty responses. Authentication succeeds but queries return nothing. Terraform reports "valid credentials but cannot retrieve user list."

**How to Avoid**:
- Uncheck "privilege separation" when creating tokens for automation
- OR explicitly grant ACL permissions to the token itself: `pveum acl modify /vms -token 'user@pve!token' -role PVEAuditor`

**Source**: [Proxmox Forum - API Token Config](https://forum.proxmox.com/threads/api-token-config.92465/), [Bare Metal Bridge](https://baremetalbridge.com/querying-proxmox-mvs-via-api-troubleshooting-and-success/) [HIGH confidence]

---

### 2. MikroTik RouterOS API Authentication Version Mismatch (HIGH)

**The Mistake**: Using the wrong authentication method for RouterOS version.

**What Happens**: Connection failures, authentication errors, or SSL/TLS handshake failures.

**How to Avoid**:
- For RouterOS 6.43+: Use `plaintext_login=True` option
- For SSL connections without certificates: Anonymous Diffie-Hellman cipher required
- For SSL with certificates: Standard TLS session
- Default ports: TCP:8728 (plain), TCP:8729 (SSL)

**Source**: [MikroTik API Documentation](https://help.mikrotik.com/docs/spaces/ROS/pages/47579160/API), [RouterOS-api PyPI](https://pypi.org/project/RouterOS-api/) [HIGH confidence]

---

### 3. NetBox Race Conditions on IP Address Allocation (HIGH)

**The Mistake**: Parallel API requests allocating "next available" IP addresses without locking.

**What Happens**: Both requests get the same IP, creating duplicates. VRF unique enforcement fails under concurrent load.

**How to Avoid**:
- Use NetBox v3.3.7+ which has advisory locks for IP allocation
- Serialize IP allocation requests in automation code
- Use database-level locking if using direct DB access

**Source**: [NetBox Issue #10282](https://github.com/netbox-community/netbox/issues/10282), [NetBox Issue #3475](https://github.com/netbox-community/netbox/issues/3475) [HIGH confidence]

---

### 4. Configuration Changes as Primary Outage Cause (HIGH)

**The Mistake**: Treating config changes as low-risk compared to code changes.

**What Happens**: AWS outage postmortems show ~50% of global outages are caused by configuration changes. Automation that writes configs without validation causes cascading failures.

**How to Avoid**:
- Treat config changes with same rigor as code deployments
- Implement pre-change validation
- Use dry-run/check modes before applying
- Maintain rollback capability

**Source**: [AWS Outage Postmortem](https://www.constellationr.com/blog-news/insights/aws-delivers-outage-post-mortem-when-automation-bites-back), [Dan Luu - Postmortem Lessons](https://danluu.com/postmortem-lessons/) [HIGH confidence]

---

### 5. QEMU Guest Agent Not Actually Running (MEDIUM)

**The Mistake**: Enabling guest agent in Proxmox VM config but not properly installing/starting it in the guest.

**What Happens**: IP addresses unavailable via API, graceful shutdown fails, backups may be inconsistent.

**How to Avoid**:
- Linux: Install, start, AND enable the service: `apt install qemu-guest-agent && systemctl enable --now qemu-guest-agent`
- Windows: Install VirtIO serial driver FIRST, then guest agent MSI
- Ubuntu quirk: After install, must STOP then START the VM (not just restart)
- Test communication: `qm agent <vmid> ping`

**Source**: [Proxmox Wiki - Qemu-guest-agent](https://pve.proxmox.com/wiki/Qemu-guest-agent), [Proxmox Forum](https://forum.proxmox.com/threads/no-qemu-guest-agent-configured-even-though-its-running.126126/) [HIGH confidence]

---

### 6. SSH Timeout Defaults Too Short for Automation (MEDIUM)

**The Mistake**: Using default 10-second SSH command timeouts.

**What Happens**: Scripts fail intermittently during high latency or heavy processing. Airflow/Ansible tasks timeout unexpectedly.

**How to Avoid**:
- Increase cmd_timeout to 60s minimum for automation tools
- Configure keepalive: `ServerAliveInterval 60` in ssh_config
- Set `ClientAliveInterval` and `ClientAliveCountMax` on servers
- Don't disable host key checking in production (MITM risk)

**Source**: [Medium - Airflow SSH Timeout](https://medium.com/@vaibhavnsingh/resolving-airflow-ssh-command-timeout-issue-a-solution-to-airflowexception-ssh-command-timed-7ca7fb957b79), [DevOps Knowledge Hub - Ansible SSH](https://devops.aibit.im/article/troubleshooting-ansible-ssh-connection-failures) [HIGH confidence]

---

### 7. Network Scanner Aggressive Timing Kills Devices (MEDIUM)

**The Mistake**: Using nmap -T4/-T5 or high --min-rate on production networks.

**What Happens**: Legacy network gear overwhelmed. UDP scans trigger rate limiting (Linux: 1 ICMP/second). Packets dropped upstream without notification.

**How to Avoid**:
- Use -T2 or -T3 timing templates
- Limit ports with -F or specific -p lists
- Set --scan-delay for UDP scans (1s for Solaris/Linux)
- Use --host-timeout to cap time per host
- ARP scans require CAP_NET_RAW or root

**Source**: [Nmap - Timing and Performance](https://nmap.org/book/man-performance.html), [Nmap - Scan Time Reduction](https://nmap.org/book/reduce-scantime.html) [HIGH confidence]

---

### 8. Hardcoded Credentials in Automation Scripts (HIGH)

**The Mistake**: Embedding API keys, passwords, or tokens directly in scripts.

**What Happens**: Credentials committed to Git. Found in 80,000+ exposed secrets across Kubernetes clusters in one study. Scripts become liability.

**How to Avoid**:
- Use secrets management (HashiCorp Vault, AWS Secrets Manager)
- Environment variables for runtime injection
- Ansible Vault for playbook secrets
- Rotate credentials regularly
- Implement credential expiration alerts

**Source**: [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html), [Palo Alto - Secrets Management Mistakes](https://www.paloaltonetworks.com/blog/prisma-cloud/5-secrets-management-mistakes/) [HIGH confidence]

---

## Technical Debt Patterns

### Pattern 1: Lab Scripts in Production

**Description**: "Scripts that worked perfectly in your small test lab produce unpredictable and often disastrous results in production."

**Symptoms**:
- Automation brittle to OS upgrades
- More time fixing scripts than manual work would take
- No error handling for network timeouts or device states

**Prevention**:
- Use EVE-NG/GNS3/Cisco Modeling Labs for realistic testing
- Build CI/CD: lint -> dry-run -> unit tests -> integration tests
- Test against same device types AND software versions as production

**Source**: [CloudMyLab - Network Automation Challenges](https://blog.cloudmylab.com/network-automation-challenges-mistakes-engineers), [ipSpace - Expert Beginners](https://blog.ipspace.net/2023/01/network-automation-expert-beginners/) [HIGH confidence]

---

### Pattern 2: Non-Idempotent Operations

**Description**: Scripts that produce different results depending on device state.

**Symptoms**:
- Running script twice creates duplicates
- Partial runs leave inconsistent state
- No safe way to re-run after failures

**Prevention**:
- Design all operations to be idempotent
- Check for existence before create
- Use upsert patterns where available
- pynetbox: check for threading issues causing duplicates

**Source**: [NetBox Ansible Issue #165](https://github.com/netbox-community/ansible_modules/issues/165), [CloudMyLab](https://blog.cloudmylab.com/network-automation-challenges-mistakes-engineers) [HIGH confidence]

---

### Pattern 3: Missing Rollback Capability

**Description**: Automation that can push changes but cannot undo them.

**Symptoms**:
- Manual CLI intervention required after failures
- No pre-change state capture
- Fear of running automation

**Prevention**:
- Capture state before changes
- Implement automated rollback on error detection
- Test rollback procedures regularly

**Source**: [ipSpace - Expert Beginners](https://blog.ipspace.net/2023/01/network-automation-expert-beginners/) [HIGH confidence]

---

### Pattern 4: Source of Truth Drift

**Description**: Network state diverges from documented state in NetBox.

**Symptoms**:
- Automation uses stale data
- Manual changes not captured
- Discovery tools find "unknown" devices

**Prevention**:
- Schedule reconciliation jobs (compare live vs documented)
- Use event-driven updates (SNMP traps, syslog)
- Implement GitOps for config changes
- Use NetBox Assurance for continuous validation

**Source**: [Cisco SSOT Whitepaper](https://www.cisco.com/c/en/us/solutions/collateral/executive-perspectives/technology-perspectives/ssot-nw-automation-wp.html), [NetBox Assurance](https://netboxlabs.com/docs/assurance/) [HIGH confidence]

---

## Integration Gotchas

### MikroTik RouterOS

| Issue | Impact | Solution | Confidence |
|-------|--------|----------|------------|
| Word order in API queries matters | Queries fail silently | Follow documented order | HIGH |
| Zero-length word terminates sentence | Commands not executed | Ensure proper termination | HIGH |
| Regex not supported in API | Queries with ~ fail | Use exact matching | HIGH |
| Non-UTF8 characters mangled | Hostnames corrupted | Specify encoding (latin-1 or windows-1250) | HIGH |
| DHCP lease null characters | API errors for some devices | Trim `\00` from values | MEDIUM |
| "Store leases on disk" causes delays | 30-second connection delays | Set to "never" | MEDIUM |
| Hardware offload can drop packets | Intermittent connectivity | Disable if seeing random drops | LOW |

**Sources**: [MikroTik API Docs](https://help.mikrotik.com/docs/spaces/ROS/pages/47579160/API), [GitHub - Homepage Discussions](https://github.com/gethomepage/homepage/discussions/3994) [Varies]

---

### Proxmox VE

| Issue | Impact | Solution | Confidence |
|-------|--------|----------|------------|
| Privilege separation default | Empty API responses | Disable or grant explicit ACLs | HIGH |
| Node-specific API calls | 404 errors after VM migration | Query /cluster/resources first | HIGH |
| Ticket vs token confusion | Auth failures | Use tokens for automation (tickets expire) | HIGH |
| SSL cert regeneration | TLS negotiation errors | Update certificates in automation | MEDIUM |
| Token secret in scripts | Security exposure | Use secrets management | HIGH |

**Sources**: [Proxmox Forum](https://forum.proxmox.com/threads/api-token-config.92465/), [Proxmox VE API Wiki](https://pve.proxmox.com/wiki/Proxmox_VE_API) [Varies]

---

### NetBox

| Issue | Impact | Solution | Confidence |
|-------|--------|----------|------------|
| Generic relations require two fields | Validation errors | Set both assigned_object_type and assigned_object_id | HIGH |
| pynetbox threading = duplicates | Missing or duplicate devices | Disable threading for critical syncs | HIGH |
| pynetbox save() on unchanged object | Server error (not catchable) | Check for changes before save | MEDIUM |
| Custom fields break in pynetbox 7.0+ | Complex custom_fields set to None | Pin version or workaround | MEDIUM |
| Large object_change table | Performance degradation | Periodic cleanup, use pagination | MEDIUM |
| Collections are generators | Second iteration empty | Convert to list if multiple passes needed | HIGH |

**Sources**: [pynetbox Issues](https://github.com/netbox-community/pynetbox/issues), [NetBox GitHub](https://github.com/netbox-community/netbox) [Varies]

---

### Network Scanning (nmap/arp-scan)

| Issue | Impact | Solution | Confidence |
|-------|--------|----------|------------|
| Root/CAP_NET_RAW required | Falls back to slow TCP connect scan | `setcap cap_net_raw+p` | HIGH |
| UDP rate limiting | Scans take hours | --scan-delay 1s for Linux/Solaris | HIGH |
| Aggressive timing | Network gear overwhelmed | Use -T2/-T3, not -T4/-T5 | HIGH |
| ARP scans local-only | Can't scan remote subnets | Use different method for remote | HIGH |
| Wake-on-LAN shows port up, no MAC | False positives | Verify with traffic generation | MEDIUM |

**Sources**: [Nmap Documentation](https://nmap.org/book/), [arp-scan man page](https://linux.die.net/man/1/arp-scan) [HIGH]

---

### MAC Address Table Correlation

| Issue | Impact | Solution | Confidence |
|-------|--------|----------|------------|
| Multiple MACs per switch port | Can't identify individual hosts | Track upstream switches separately | HIGH |
| Aging timer removes entries | Timing-dependent discovery | Run discovery when hosts active | MEDIUM |
| MAC flooding attacks | Table overflow, broadcast storm | Enable port security | MEDIUM |
| VLAN-specific SNMP queries | Missing MACs in other VLANs | Query per-VLAN: `community@vlan` | HIGH |

**Sources**: [Cisco SNMP MAC-to-Port](https://www.cisco.com/c/en/us/support/docs/ip/simple-network-management-protocol-snmp/44800-mactoport44800.html), [JumpCloud](https://jumpcloud.com/it-index/what-is-a-mac-address-table) [HIGH]

---

### Unbound DNS

| Issue | Impact | Solution | Confidence |
|-------|--------|----------|------------|
| Config filename collisions | Plugin conflicts | Use unique filenames | MEDIUM |
| DNSSEC + capitalization randomization | Resolution failures | Disable capitalization randomization | MEDIUM |
| OpenResolv conflict (Debian) | Unexpected behavior | Check /etc/resolv.conf management | MEDIUM |
| Cache flush on reload | Slow resolution after config change | Disable if using dynamic interfaces | LOW |
| Chroot breaks Python modules | Module failures | Set `chroot: ""` | HIGH |

**Sources**: [OPNsense Unbound Docs](https://docs.opnsense.org/manual/unbound.html), [Unbound Documentation](https://unbound.docs.nlnetlabs.nl/) [Varies]

---

## Security Mistakes

### 1. Excessive Automation Account Privileges (HIGH)

**Mistake**: Creating automation accounts with admin/root privileges "to make things work."

**Risk**: Compromised automation = full network compromise.

**Prevention**:
- Create read-only groups for discovery operations
- Separate write credentials with explicit scope
- Use API tokens with minimal permissions
- Restrict "Allowed From" to automation host IPs

---

### 2. HTTP API Without TLS (HIGH)

**Mistake**: Using unencrypted API connections, especially MikroTik www service.

**Risk**: Credentials readable via passive eavesdropping.

**Prevention**:
- Always use HTTPS/SSL ports
- Accept self-signed certs explicitly rather than disabling verification entirely
- MikroTik: Use api-ssl (8729) not api (8728) in production

---

### 3. Secrets in Version Control (HIGH)

**Mistake**: Committing .env files, credentials, API tokens to Git.

**Risk**: Public exposure of production credentials.

**Prevention**:
- .gitignore all credential files
- Use pre-commit hooks to detect secrets
- Rotate any accidentally committed credentials immediately
- Use GitHub secret scanning

---

### 4. Disabling Host Key Checking (MEDIUM)

**Mistake**: Setting `StrictHostKeyChecking=no` to avoid SSH prompts.

**Risk**: MITM attacks go undetected.

**Prevention**:
- Pre-populate known_hosts
- Use SSH certificate authority
- Accept key once and verify

---

### 5. Credential Expiration Blind Spots (MEDIUM)

**Mistake**: Non-human identity credentials with no expiration tracking.

**Risk**: Sudden automation failures, urgent security escalations.

**Prevention**:
- Track all credential expiration dates
- Implement automated rotation
- Use dynamic secrets where possible (HashiCorp Vault)

---

## "Looks Done But Isn't" Checklist

Use this checklist before declaring discovery/sync integration complete:

### Data Quality

- [ ] **Duplicate prevention**: Test concurrent requests for same resource
- [ ] **Idempotency**: Run full sync twice, verify no duplicates/changes
- [ ] **Empty states handled**: What happens when DHCP has no leases? VM has no IP?
- [ ] **Character encoding**: Test hostnames with special characters, spaces, unicode
- [ ] **Null/missing fields**: Handle None, empty strings, missing keys gracefully

### Integration Completeness

- [ ] **All VLANs discovered**: Not just default VLAN
- [ ] **VMs on all nodes**: Query cluster resources, not single node
- [ ] **Guest agent dependency**: Document which VMs need agent for full data
- [ ] **MAC table timing**: Discovery runs when devices are active
- [ ] **DHCP lease coverage**: Static and dynamic leases both captured

### Error Handling

- [ ] **Network timeouts**: Test with increased latency, dropped packets
- [ ] **API rate limiting**: Test with large datasets
- [ ] **Authentication expiration**: What happens when token expires mid-sync?
- [ ] **Partial failures**: Can resume after interruption?
- [ ] **Rollback capability**: Can undo changes if sync goes wrong?

### Security

- [ ] **Credentials not in code**: All secrets via env vars or vault
- [ ] **Minimal permissions**: Each integration uses least-privilege account
- [ ] **TLS everywhere**: No plain HTTP API calls
- [ ] **Audit logging**: Changes are traceable

### Operational Readiness

- [ ] **Drift detection**: Know when source of truth diverges from reality
- [ ] **Monitoring/alerting**: Know when sync fails
- [ ] **Documentation**: Runbook for common failure modes
- [ ] **Test environment**: Can test changes without touching production

---

## Source Summary

### High Confidence Sources (Verified, Multiple Corroborations)

- [MikroTik API Documentation](https://help.mikrotik.com/docs/spaces/ROS/pages/47579160/API)
- [Proxmox VE API Wiki](https://pve.proxmox.com/wiki/Proxmox_VE_API)
- [NetBox GitHub Issues](https://github.com/netbox-community/netbox/issues)
- [pynetbox GitHub Issues](https://github.com/netbox-community/pynetbox/issues)
- [Nmap Official Documentation](https://nmap.org/book/)
- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [AWS Outage Postmortems](https://www.infoq.com/news/2021/12/aws-outage-postmortem/)
- [Google SRE Book - Postmortem Culture](https://sre.google/sre-book/postmortem-culture/)

### Medium Confidence Sources (Community Forums, Single Reports)

- [Proxmox Support Forum threads](https://forum.proxmox.com/)
- [MikroTik Community Forum](https://forum.mikrotik.com/)
- [GitHub Discussions on network automation](https://github.com/netbox-community/netbox/discussions)
- [ipSpace.net Blog](https://blog.ipspace.net/)
- [CloudMyLab Blog](https://blog.cloudmylab.com/)

### Low Confidence Sources (Anecdotal, Unverified)

- Individual blog posts without corroboration
- Forum posts without follow-up confirmation
- Theoretical issues not demonstrated in practice

---

*Research compiled: 2026-01-15*
*Domain: Network automation / infrastructure discovery*
*Focus: MikroTik DHCP, Proxmox VMs, NetBox, Unbound DNS, MAC table correlation*
