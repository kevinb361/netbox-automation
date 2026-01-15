"""Discovery orchestration for netbox-auto.

Coordinates all collectors, merges hosts by MAC address, applies switch port
mappings, and persists results to the staging database.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone

from netbox_auto.collectors import (
    DHCPCollector,
    DiscoveredHost,
    ProxmoxCollector,
    ScannerCollector,
    SwitchCollector,
)
from netbox_auto.config import get_config
from netbox_auto.database import get_session
from netbox_auto.models import DiscoveryRun, DiscoveryStatus, Host, HostSource

logger = logging.getLogger(__name__)


@dataclass
class DiscoveryResult:
    """Results from a discovery run."""

    total_hosts: int
    new_hosts: int
    updated_hosts: int
    errors: list[str]


@dataclass
class CollectorResult:
    """Result from running a single collector."""

    name: str
    hosts: list[DiscoveredHost]
    error: str | None = None


def run_discovery() -> DiscoveryResult:
    """Run discovery from all configured sources and persist to database.

    Creates a DiscoveryRun record, runs all configured collectors, merges
    hosts by MAC address, applies switch port mappings, and persists
    results to the Host table.

    Returns:
        DiscoveryResult with counts and any errors encountered.
    """
    config = get_config()
    session = get_session()
    errors: list[str] = []

    # Create discovery run record
    discovery_run = DiscoveryRun(status=DiscoveryStatus.RUNNING.value)
    session.add(discovery_run)
    session.commit()

    all_hosts: list[DiscoveredHost] = []
    mac_to_port: dict[str, str] = {}

    # Run host collectors
    collector_results = _run_host_collectors(config)
    for result in collector_results:
        if result.error:
            errors.append(f"{result.name}: {result.error}")
        else:
            all_hosts.extend(result.hosts)

    # Run switch collector for MAC-to-port mappings
    if config.switches:
        try:
            switch_collector = SwitchCollector(config.switches)
            mac_to_port = switch_collector.collect()
            logger.info(f"Collected {len(mac_to_port)} MAC-to-port mappings from switches")
        except Exception as e:
            error_msg = f"Switch MAC collection failed: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

    # Merge hosts and persist
    try:
        new_count, updated_count = _merge_and_persist(
            session, all_hosts, mac_to_port, discovery_run
        )
    except Exception as e:
        error_msg = f"Failed to persist discovery results: {e}"
        logger.error(error_msg)
        errors.append(error_msg)
        new_count, updated_count = 0, 0

    # Update discovery run status
    if errors and not all_hosts:
        discovery_run.status = DiscoveryStatus.FAILED.value
    else:
        discovery_run.status = DiscoveryStatus.COMPLETED.value
    discovery_run.completed_at = datetime.now(timezone.utc)
    session.commit()
    session.close()

    return DiscoveryResult(
        total_hosts=new_count + updated_count,
        new_hosts=new_count,
        updated_hosts=updated_count,
        errors=errors,
    )


def _run_host_collectors(config) -> list[CollectorResult]:
    """Run all configured host collectors.

    Instantiates and runs collectors based on what's configured:
    - DHCPCollector if mikrotik config exists
    - ProxmoxCollector if proxmox config exists
    - ScannerCollector if scanner config exists with subnets

    Args:
        config: Application configuration.

    Returns:
        List of CollectorResult with hosts and any errors.
    """
    results: list[CollectorResult] = []

    # DHCP collector
    if config.mikrotik:
        try:
            collector = DHCPCollector(config.mikrotik)
            hosts = collector.collect()
            results.append(CollectorResult(name=collector.name, hosts=hosts))
            logger.info(f"{collector.name}: collected {len(hosts)} hosts")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"DHCP collector failed: {error_msg}")
            results.append(CollectorResult(name="MikroTik DHCP", hosts=[], error=error_msg))

    # Proxmox collector
    if config.proxmox:
        try:
            collector = ProxmoxCollector(config.proxmox)
            hosts = collector.collect()
            results.append(CollectorResult(name=collector.name, hosts=hosts))
            logger.info(f"{collector.name}: collected {len(hosts)} VMs")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Proxmox collector failed: {error_msg}")
            results.append(CollectorResult(name="Proxmox", hosts=[], error=error_msg))

    # Scanner collector
    if config.scanner and config.scanner.subnets:
        try:
            collector = ScannerCollector(config.scanner)
            hosts = collector.collect()
            results.append(CollectorResult(name=collector.name, hosts=hosts))
            logger.info(f"{collector.name}: collected {len(hosts)} hosts")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Scanner collector failed: {error_msg}")
            results.append(CollectorResult(name="network-scanner", hosts=[], error=error_msg))

    return results


def _merge_and_persist(
    session,
    all_hosts: list[DiscoveredHost],
    mac_to_port: dict[str, str],
    discovery_run: DiscoveryRun,
) -> tuple[int, int]:
    """Merge discovered hosts by MAC and persist to database.

    Groups hosts by MAC address, merges IP addresses from all sources,
    picks hostname by priority (dhcp > proxmox > scan), applies switch
    port mappings, and creates or updates Host records.

    Args:
        session: Database session.
        all_hosts: List of all discovered hosts from collectors.
        mac_to_port: Mapping of MAC addresses to switch ports.
        discovery_run: Current discovery run record.

    Returns:
        Tuple of (new_hosts_count, updated_hosts_count).
    """
    if not all_hosts:
        return 0, 0

    # Group hosts by MAC address
    hosts_by_mac: dict[str, list[DiscoveredHost]] = defaultdict(list)
    for host in all_hosts:
        hosts_by_mac[host.mac.lower()].append(host)

    new_count = 0
    updated_count = 0

    for mac, hosts in hosts_by_mac.items():
        # Merge IP addresses from all sources
        all_ips: set[str] = set()
        for h in hosts:
            all_ips.update(h.ip_addresses)

        # Pick hostname by source priority: dhcp > proxmox > scan
        hostname = _pick_hostname(hosts)

        # Get primary source (most authoritative)
        primary_source = _pick_primary_source(hosts)

        # Apply switch port mapping
        switch_port = mac_to_port.get(mac)

        # Check if host exists in DB
        existing = session.query(Host).filter(Host.mac == mac).first()

        if existing:
            # Update existing host
            existing.hostname = hostname or existing.hostname
            existing.ip_addresses = list(all_ips) if all_ips else existing.ip_addresses
            existing.switch_port = switch_port or existing.switch_port
            existing.discovery_run_id = discovery_run.id
            # last_seen is auto-updated via onupdate
            updated_count += 1
            logger.debug(f"Updated host: {mac} ({hostname or 'no hostname'})")
        else:
            # Create new host
            new_host = Host(
                mac=mac,
                hostname=hostname,
                ip_addresses=list(all_ips),
                source=primary_source.value,
                switch_port=switch_port,
                discovery_run_id=discovery_run.id,
            )
            session.add(new_host)
            new_count += 1
            logger.debug(f"New host: {mac} ({hostname or 'no hostname'})")

    session.commit()
    return new_count, updated_count


def _pick_hostname(hosts: list[DiscoveredHost]) -> str | None:
    """Pick the best hostname from multiple discovered host records.

    Priority order: DHCP > Proxmox > Scan (DHCP is most specific).

    Args:
        hosts: List of DiscoveredHost records for the same MAC.

    Returns:
        Best hostname found, or None if no hostname available.
    """
    priority = [HostSource.DHCP, HostSource.PROXMOX, HostSource.SCAN]

    for source in priority:
        for h in hosts:
            if h.source == source and h.hostname:
                return h.hostname

    return None


def _pick_primary_source(hosts: list[DiscoveredHost]) -> HostSource:
    """Pick the primary source for a host record.

    Priority order: DHCP > Proxmox > Scan.

    Args:
        hosts: List of DiscoveredHost records for the same MAC.

    Returns:
        Most authoritative source found.
    """
    priority = [HostSource.DHCP, HostSource.PROXMOX, HostSource.SCAN]

    for source in priority:
        for h in hosts:
            if h.source == source:
                return source

    # Default to first host's source
    return hosts[0].source if hosts else HostSource.MANUAL
