"""Reconciliation module for comparing discovered hosts with NetBox inventory.

Provides functions to compare discovered hosts with NetBox devices/VMs and
import NetBox devices into the staging database for tracking.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from netbox_auto.database import get_session
from netbox_auto.models import Host, HostSource, HostStatus
from netbox_auto.netbox import get_netbox_devices, get_netbox_vms

logger = logging.getLogger(__name__)


@dataclass
class ReconciliationResult:
    """Result of comparing discovered hosts with NetBox inventory.

    Attributes:
        new_hosts: Hosts discovered but not in NetBox
        matched_hosts: Hosts found in both discovery and NetBox
        stale_netbox: NetBox entries not found in discovery
    """

    new_hosts: list[Host] = field(default_factory=list)
    matched_hosts: list[tuple[Host, dict[str, Any]]] = field(default_factory=list)
    stale_netbox: list[dict[str, Any]] = field(default_factory=list)


def _normalize_ip(ip: str | None) -> str | None:
    """Normalize IP address by stripping prefix length.

    Args:
        ip: IP address potentially with prefix (e.g., "192.168.1.1/24")

    Returns:
        IP address without prefix, or None if input is None
    """
    if ip is None:
        return None
    return ip.split("/")[0]


def _get_netbox_inventory() -> list[dict[str, Any]]:
    """Fetch all devices and VMs from NetBox.

    Returns:
        Combined list of devices and VMs with a 'type' field added.
    """
    inventory: list[dict[str, Any]] = []

    # Get devices
    devices = get_netbox_devices()
    for device in devices:
        device["_type"] = "device"
        inventory.append(device)

    # Get VMs
    vms = get_netbox_vms()
    for vm in vms:
        vm["_type"] = "vm"
        inventory.append(vm)

    return inventory


def _match_host_to_netbox(host: Host, netbox_items: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Try to match a discovered host to a NetBox item.

    Matching is done by:
    1. IP address comparison (host IPs vs NetBox primary_ip)

    Args:
        host: Discovered host to match
        netbox_items: List of NetBox devices/VMs

    Returns:
        Matching NetBox item or None if no match found
    """
    # Get host IPs as a set for fast lookup
    host_ips: set[str] = set()
    if isinstance(host.ip_addresses, list):
        for ip in host.ip_addresses:
            normalized = _normalize_ip(ip)
            if normalized:
                host_ips.add(normalized)
    elif isinstance(host.ip_addresses, dict):
        # Handle dict format if stored that way
        for ip in host.ip_addresses.values():
            if isinstance(ip, str):
                normalized = _normalize_ip(ip)
                if normalized:
                    host_ips.add(normalized)

    # Try to match by IP
    for item in netbox_items:
        netbox_ip = _normalize_ip(item.get("primary_ip"))
        if netbox_ip and netbox_ip in host_ips:
            return item

    return None


def reconcile_hosts() -> ReconciliationResult:
    """Compare discovered hosts with NetBox inventory.

    Fetches all hosts from the staging database and compares them with
    devices and VMs from NetBox. Categorizes hosts as:
    - new_hosts: Discovered but not in NetBox
    - matched_hosts: Found in both (paired with NetBox data)
    - stale_netbox: In NetBox but not discovered

    Returns:
        ReconciliationResult with categorized hosts
    """
    result = ReconciliationResult()

    # Get discovered hosts from database
    session = get_session()
    try:
        discovered_hosts = session.query(Host).all()
    finally:
        session.close()

    # Get NetBox inventory
    netbox_items = _get_netbox_inventory()
    matched_netbox_ids: set[int] = set()

    # Compare each discovered host with NetBox
    for host in discovered_hosts:
        # Check if already linked to NetBox
        if host.netbox_id is not None:
            # Find the NetBox item by ID
            for item in netbox_items:
                if item["id"] == host.netbox_id:
                    result.matched_hosts.append((host, item))
                    matched_netbox_ids.add(item["id"])
                    break
            else:
                # NetBox item not found - may have been deleted
                result.new_hosts.append(host)
            continue

        # Try to match by IP
        match = _match_host_to_netbox(host, netbox_items)
        if match:
            result.matched_hosts.append((host, match))
            matched_netbox_ids.add(match["id"])
        else:
            result.new_hosts.append(host)

    # Find stale NetBox entries (not matched to any discovered host)
    for item in netbox_items:
        if item["id"] not in matched_netbox_ids:
            result.stale_netbox.append(item)

    logger.info(
        f"Reconciliation: {len(result.new_hosts)} new, "
        f"{len(result.matched_hosts)} matched, "
        f"{len(result.stale_netbox)} stale"
    )

    return result


def import_netbox_devices() -> int:
    """Import devices and VMs from NetBox into the staging database.

    Creates Host records for NetBox entries that don't already exist
    in the database (matched by netbox_id or IP address).

    Returns:
        Number of hosts imported
    """
    session = get_session()
    imported = 0

    try:
        # Get existing hosts for comparison
        existing_hosts = session.query(Host).all()
        existing_netbox_ids: set[int] = {h.netbox_id for h in existing_hosts if h.netbox_id}
        existing_ips: set[str] = set()

        for host in existing_hosts:
            if isinstance(host.ip_addresses, list):
                for ip in host.ip_addresses:
                    normalized = _normalize_ip(ip)
                    if normalized:
                        existing_ips.add(normalized)

        # Get NetBox inventory
        netbox_items = _get_netbox_inventory()

        for item in netbox_items:
            # Skip if already imported by netbox_id
            if item["id"] in existing_netbox_ids:
                logger.debug(f"Skipping {item['name']}: already imported (netbox_id)")
                continue

            # Skip if IP already exists
            item_ip = _normalize_ip(item.get("primary_ip"))
            if item_ip and item_ip in existing_ips:
                logger.debug(f"Skipping {item['name']}: IP {item_ip} already exists")
                continue

            # Create new host record
            # Generate a placeholder MAC for imported devices
            # Use format: 00:NB:XX:XX:XX:XX where X is from netbox ID
            netbox_id = item["id"]
            mac_suffix = f"{netbox_id:08x}"
            placeholder_mac = f"00:nb:{mac_suffix[0:2]}:{mac_suffix[2:4]}:{mac_suffix[4:6]}:{mac_suffix[6:8]}"

            # Check if this placeholder MAC already exists
            existing_mac = session.query(Host).filter_by(mac=placeholder_mac).first()
            if existing_mac:
                logger.debug(f"Skipping {item['name']}: placeholder MAC already exists")
                continue

            ip_list = [item_ip] if item_ip else []

            new_host = Host(
                mac=placeholder_mac,
                hostname=item["name"],
                ip_addresses=ip_list,
                source=HostSource.MANUAL.value,
                status=HostStatus.PENDING.value,
                netbox_id=item["id"],
                notes=f"Imported from NetBox ({item['_type']})",
            )

            session.add(new_host)
            imported += 1
            logger.info(f"Imported {item['name']} from NetBox")

        session.commit()

    except Exception as e:
        session.rollback()
        logger.error(f"Error importing NetBox devices: {e}")
        raise
    finally:
        session.close()

    logger.info(f"Imported {imported} hosts from NetBox")
    return imported
