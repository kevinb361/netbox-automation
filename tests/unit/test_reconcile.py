"""Unit tests for reconciliation module.

Tests for host matching and categorization logic:
- UNIT-08: New hosts identification
- UNIT-09: Matched hosts identification
- UNIT-10: Stale hosts identification
"""

from netbox_auto.models import Host, HostSource, HostStatus
from netbox_auto.reconcile import (
    _match_host_to_netbox,
    _normalize_ip,
    reconcile_hosts,
)

# =============================================================================
# Helper function tests: _normalize_ip
# =============================================================================


def test_normalize_ip_strips_prefix():
    """Given IP with CIDR prefix, returns IP without prefix."""
    result = _normalize_ip("192.168.1.1/24")
    assert result == "192.168.1.1"


def test_normalize_ip_handles_none():
    """Given None, returns None."""
    result = _normalize_ip(None)
    assert result is None


def test_normalize_ip_handles_bare_ip():
    """Given IP without prefix, returns IP unchanged."""
    result = _normalize_ip("10.0.0.1")
    assert result == "10.0.0.1"


def test_normalize_ip_strips_long_prefix():
    """Given IP with /32 prefix, returns bare IP."""
    result = _normalize_ip("172.16.0.100/32")
    assert result == "172.16.0.100"


# =============================================================================
# UNIT-09: Matching tests - _match_host_to_netbox
# =============================================================================


def test_match_host_to_netbox_by_ip(in_memory_db):
    """Given host IP matches NetBox primary_ip, returns matching item."""
    session = in_memory_db
    host = Host(
        mac="aa:bb:cc:dd:ee:ff",
        ip_addresses=["192.168.1.100"],
        source=HostSource.DHCP.value,
        status=HostStatus.PENDING.value,
    )
    session.add(host)
    session.flush()

    netbox_item = {"id": 1, "name": "server1", "primary_ip": "192.168.1.100/24"}

    match = _match_host_to_netbox(host, [netbox_item])
    assert match == netbox_item


def test_match_host_to_netbox_no_match(in_memory_db):
    """Given host IP doesn't match any NetBox item, returns None."""
    session = in_memory_db
    host = Host(
        mac="aa:bb:cc:dd:ee:ff",
        ip_addresses=["192.168.1.100"],
        source=HostSource.DHCP.value,
        status=HostStatus.PENDING.value,
    )
    session.add(host)
    session.flush()

    netbox_item = {"id": 1, "name": "server1", "primary_ip": "10.0.0.1/24"}

    match = _match_host_to_netbox(host, [netbox_item])
    assert match is None


def test_match_host_handles_dict_ip_format(in_memory_db):
    """Given host with dict IP format (legacy), still matches correctly."""
    session = in_memory_db
    host = Host(
        mac="aa:bb:cc:dd:ee:ff",
        ip_addresses={"eth0": "192.168.1.100"},  # dict format
        source=HostSource.DHCP.value,
        status=HostStatus.PENDING.value,
    )
    session.add(host)
    session.flush()

    netbox_item = {"id": 1, "name": "server1", "primary_ip": "192.168.1.100/24"}

    match = _match_host_to_netbox(host, [netbox_item])
    assert match == netbox_item


def test_match_host_handles_multiple_ips(in_memory_db):
    """Given host with multiple IPs, matches if any IP matches."""
    session = in_memory_db
    host = Host(
        mac="aa:bb:cc:dd:ee:ff",
        ip_addresses=["10.0.0.50", "192.168.1.100", "172.16.0.1"],
        source=HostSource.DHCP.value,
        status=HostStatus.PENDING.value,
    )
    session.add(host)
    session.flush()

    netbox_item = {"id": 1, "name": "server1", "primary_ip": "192.168.1.100/24"}

    match = _match_host_to_netbox(host, [netbox_item])
    assert match == netbox_item


def test_match_host_returns_first_match(in_memory_db):
    """Given multiple matching NetBox items, returns first match."""
    session = in_memory_db
    host = Host(
        mac="aa:bb:cc:dd:ee:ff",
        ip_addresses=["192.168.1.100"],
        source=HostSource.DHCP.value,
        status=HostStatus.PENDING.value,
    )
    session.add(host)
    session.flush()

    netbox_items = [
        {"id": 1, "name": "server1", "primary_ip": "192.168.1.100/24"},
        {"id": 2, "name": "server2", "primary_ip": "192.168.1.100/32"},  # duplicate IP
    ]

    match = _match_host_to_netbox(host, netbox_items)
    assert match["id"] == 1  # Returns first match


def test_match_host_with_no_ips(in_memory_db):
    """Given host with no IP addresses, returns None."""
    session = in_memory_db
    host = Host(
        mac="aa:bb:cc:dd:ee:ff",
        ip_addresses=[],
        source=HostSource.DHCP.value,
        status=HostStatus.PENDING.value,
    )
    session.add(host)
    session.flush()

    netbox_item = {"id": 1, "name": "server1", "primary_ip": "192.168.1.100/24"}

    match = _match_host_to_netbox(host, [netbox_item])
    assert match is None


# =============================================================================
# UNIT-08, UNIT-09, UNIT-10: Categorization tests - reconcile_hosts
# =============================================================================


def test_unmatched_host_is_new(in_memory_db, mocker):
    """UNIT-08: Host with IP not in NetBox appears in new_hosts."""
    session = in_memory_db
    host = Host(
        mac="aa:bb:cc:dd:ee:ff",
        hostname="new-server",
        ip_addresses=["192.168.1.100"],
        source=HostSource.DHCP.value,
        status=HostStatus.PENDING.value,
    )
    session.add(host)
    session.commit()

    # Mock NetBox returns empty inventory
    mocker.patch("netbox_auto.reconcile.get_netbox_devices", return_value=[])
    mocker.patch("netbox_auto.reconcile.get_netbox_vms", return_value=[])
    mocker.patch("netbox_auto.reconcile.get_session", return_value=session)

    result = reconcile_hosts()

    assert len(result.new_hosts) == 1
    assert result.new_hosts[0].mac == "aa:bb:cc:dd:ee:ff"
    assert len(result.matched_hosts) == 0
    assert len(result.stale_netbox) == 0


def test_host_with_deleted_netbox_id_is_new(in_memory_db, mocker):
    """UNIT-08: Host with netbox_id not in NetBox appears in new_hosts."""
    session = in_memory_db
    host = Host(
        mac="aa:bb:cc:dd:ee:ff",
        hostname="orphan-server",
        ip_addresses=["192.168.1.100"],
        source=HostSource.DHCP.value,
        status=HostStatus.PENDING.value,
        netbox_id=999,  # NetBox item was deleted
    )
    session.add(host)
    session.commit()

    # NetBox has different items (ID 999 doesn't exist)
    mocker.patch(
        "netbox_auto.reconcile.get_netbox_devices",
        return_value=[{"id": 1, "name": "other-server", "primary_ip": "10.0.0.1/24"}],
    )
    mocker.patch("netbox_auto.reconcile.get_netbox_vms", return_value=[])
    mocker.patch("netbox_auto.reconcile.get_session", return_value=session)

    result = reconcile_hosts()

    assert len(result.new_hosts) == 1
    assert result.new_hosts[0].netbox_id == 999
    assert len(result.matched_hosts) == 0


def test_host_matched_by_netbox_id(in_memory_db, mocker):
    """UNIT-09: Host with netbox_id matching NetBox item appears in matched_hosts."""
    session = in_memory_db
    host = Host(
        mac="aa:bb:cc:dd:ee:ff",
        hostname="known-server",
        ip_addresses=["192.168.1.100"],
        source=HostSource.DHCP.value,
        status=HostStatus.PENDING.value,
        netbox_id=123,
    )
    session.add(host)
    session.commit()

    netbox_device = {"id": 123, "name": "known-server", "primary_ip": "192.168.1.100/24"}
    mocker.patch(
        "netbox_auto.reconcile.get_netbox_devices",
        return_value=[netbox_device],
    )
    mocker.patch("netbox_auto.reconcile.get_netbox_vms", return_value=[])
    mocker.patch("netbox_auto.reconcile.get_session", return_value=session)

    result = reconcile_hosts()

    assert len(result.matched_hosts) == 1
    matched_host, matched_netbox = result.matched_hosts[0]
    assert matched_host.mac == "aa:bb:cc:dd:ee:ff"
    assert matched_netbox["id"] == 123
    assert len(result.new_hosts) == 0


def test_host_matched_by_ip(in_memory_db, mocker):
    """UNIT-09: Host without netbox_id but matching IP appears in matched_hosts."""
    session = in_memory_db
    host = Host(
        mac="aa:bb:cc:dd:ee:ff",
        hostname="discovered-server",
        ip_addresses=["192.168.1.100"],
        source=HostSource.DHCP.value,
        status=HostStatus.PENDING.value,
        netbox_id=None,  # Not linked yet
    )
    session.add(host)
    session.commit()

    netbox_device = {"id": 456, "name": "existing-server", "primary_ip": "192.168.1.100/24"}
    mocker.patch(
        "netbox_auto.reconcile.get_netbox_devices",
        return_value=[netbox_device],
    )
    mocker.patch("netbox_auto.reconcile.get_netbox_vms", return_value=[])
    mocker.patch("netbox_auto.reconcile.get_session", return_value=session)

    result = reconcile_hosts()

    assert len(result.matched_hosts) == 1
    matched_host, matched_netbox = result.matched_hosts[0]
    assert matched_host.mac == "aa:bb:cc:dd:ee:ff"
    assert matched_netbox["id"] == 456
    assert len(result.new_hosts) == 0


def test_netbox_item_not_in_discovery_is_stale(in_memory_db, mocker):
    """UNIT-10: NetBox item with IP not matching any discovered host is stale."""
    session = in_memory_db
    # Add a discovered host with different IP
    host = Host(
        mac="aa:bb:cc:dd:ee:ff",
        hostname="local-server",
        ip_addresses=["192.168.1.100"],
        source=HostSource.DHCP.value,
        status=HostStatus.PENDING.value,
    )
    session.add(host)
    session.commit()

    # NetBox has item with different IP
    stale_device = {"id": 789, "name": "stale-server", "primary_ip": "10.0.0.50/24"}
    mocker.patch(
        "netbox_auto.reconcile.get_netbox_devices",
        return_value=[stale_device],
    )
    mocker.patch("netbox_auto.reconcile.get_netbox_vms", return_value=[])
    mocker.patch("netbox_auto.reconcile.get_session", return_value=session)

    result = reconcile_hosts()

    assert len(result.stale_netbox) == 1
    assert result.stale_netbox[0]["id"] == 789
    assert result.stale_netbox[0]["name"] == "stale-server"


def test_all_categorization_mutual_exclusive(in_memory_db, mocker):
    """Hosts appear in exactly one category (new, matched, or stale)."""
    session = in_memory_db

    # Create hosts for different scenarios
    new_host = Host(
        mac="11:22:33:44:55:66",
        hostname="new-server",
        ip_addresses=["192.168.1.10"],
        source=HostSource.DHCP.value,
        status=HostStatus.PENDING.value,
    )
    matched_host = Host(
        mac="aa:bb:cc:dd:ee:ff",
        hostname="matched-server",
        ip_addresses=["192.168.1.100"],
        source=HostSource.DHCP.value,
        status=HostStatus.PENDING.value,
    )
    session.add_all([new_host, matched_host])
    session.commit()

    # NetBox: one matching device, one stale device
    netbox_devices = [
        {"id": 1, "name": "matched-device", "primary_ip": "192.168.1.100/24"},
        {"id": 2, "name": "stale-device", "primary_ip": "10.0.0.1/24"},
    ]
    mocker.patch("netbox_auto.reconcile.get_netbox_devices", return_value=netbox_devices)
    mocker.patch("netbox_auto.reconcile.get_netbox_vms", return_value=[])
    mocker.patch("netbox_auto.reconcile.get_session", return_value=session)

    result = reconcile_hosts()

    # Verify categorization
    assert len(result.new_hosts) == 1
    assert len(result.matched_hosts) == 1
    assert len(result.stale_netbox) == 1

    # Verify mutual exclusivity
    new_macs = {h.mac for h in result.new_hosts}
    matched_macs = {h.mac for h, _ in result.matched_hosts}
    stale_ids = {item["id"] for item in result.stale_netbox}

    # New host MAC should only appear in new_hosts
    assert "11:22:33:44:55:66" in new_macs
    assert "11:22:33:44:55:66" not in matched_macs

    # Matched host MAC should only appear in matched_hosts
    assert "aa:bb:cc:dd:ee:ff" in matched_macs
    assert "aa:bb:cc:dd:ee:ff" not in new_macs

    # Stale NetBox device should only appear in stale_netbox
    assert 2 in stale_ids
    assert 1 not in stale_ids  # Matched device should not be stale
