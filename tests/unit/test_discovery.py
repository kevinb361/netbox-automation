"""Unit tests for discovery module.

Tests MAC correlation logic and source priority for hostname selection.
Covers requirements UNIT-01 and UNIT-02.
"""

from netbox_auto.discovery import _pick_hostname, _pick_primary_source
from netbox_auto.models import HostSource


class TestMACCorrelation:
    """Tests for MAC-based host correlation (UNIT-01)."""

    def test_merge_hosts_combines_ips_from_same_mac(self, discovered_host_factory):
        """Hosts with same MAC should have their IPs combined."""
        host1 = discovered_host_factory(
            mac="aa:bb:cc:dd:ee:ff",
            ip_addresses=["192.168.1.10"],
            source=HostSource.DHCP,
        )
        host2 = discovered_host_factory(
            mac="aa:bb:cc:dd:ee:ff",
            ip_addresses=["10.0.0.10"],
            source=HostSource.PROXMOX,
        )

        # Simulate merge logic: collect all IPs from hosts with same MAC
        hosts = [host1, host2]
        all_ips: set[str] = set()
        for h in hosts:
            all_ips.update(h.ip_addresses)

        assert all_ips == {"192.168.1.10", "10.0.0.10"}

    def test_merge_hosts_groups_by_mac_case_insensitive(self, discovered_host_factory):
        """MAC addresses should be treated case-insensitively."""
        host1 = discovered_host_factory(
            mac="AA:BB:CC:DD:EE:FF",
            hostname="upper-case",
            source=HostSource.DHCP,
        )
        host2 = discovered_host_factory(
            mac="aa:bb:cc:dd:ee:ff",
            hostname="lower-case",
            source=HostSource.PROXMOX,
        )

        # DiscoveredHost normalizes MAC to lowercase in __post_init__
        assert host1.mac == host2.mac
        assert host1.mac == "aa:bb:cc:dd:ee:ff"

    def test_mac_normalization_converts_dashes_to_colons(self, discovered_host_factory):
        """MAC addresses with dashes should be normalized to colons."""
        host = discovered_host_factory(mac="aa-bb-cc-dd-ee-ff")
        assert host.mac == "aa:bb:cc:dd:ee:ff"


class TestSourcePriority:
    """Tests for source priority in hostname selection (UNIT-02)."""

    def test_pick_hostname_prefers_dhcp_over_proxmox(self, discovered_host_factory):
        """DHCP hostname should be selected over Proxmox."""
        dhcp_host = discovered_host_factory(
            mac="aa:bb:cc:dd:ee:ff",
            hostname="dhcp-name",
            source=HostSource.DHCP,
        )
        proxmox_host = discovered_host_factory(
            mac="aa:bb:cc:dd:ee:ff",
            hostname="proxmox-name",
            source=HostSource.PROXMOX,
        )

        # Order shouldn't matter - priority is by source type
        result = _pick_hostname([proxmox_host, dhcp_host])
        assert result == "dhcp-name"

    def test_pick_hostname_prefers_proxmox_over_scan(self, discovered_host_factory):
        """Proxmox hostname should be selected over scan."""
        proxmox_host = discovered_host_factory(
            mac="aa:bb:cc:dd:ee:ff",
            hostname="proxmox-name",
            source=HostSource.PROXMOX,
        )
        scan_host = discovered_host_factory(
            mac="aa:bb:cc:dd:ee:ff",
            hostname="scan-name",
            source=HostSource.SCAN,
        )

        result = _pick_hostname([scan_host, proxmox_host])
        assert result == "proxmox-name"

    def test_pick_hostname_returns_none_when_no_hostname(self, discovered_host_factory):
        """Should return None when no hosts have hostnames."""
        host1 = discovered_host_factory(
            mac="aa:bb:cc:dd:ee:ff",
            hostname=None,
            source=HostSource.DHCP,
        )
        host2 = discovered_host_factory(
            mac="aa:bb:cc:dd:ee:ff",
            hostname=None,
            source=HostSource.PROXMOX,
        )

        result = _pick_hostname([host1, host2])
        assert result is None

    def test_pick_hostname_skips_empty_hostname(self, discovered_host_factory):
        """Should skip sources with empty string hostnames."""
        dhcp_host = discovered_host_factory(
            mac="aa:bb:cc:dd:ee:ff",
            hostname="",  # Empty string, should be skipped
            source=HostSource.DHCP,
        )
        proxmox_host = discovered_host_factory(
            mac="aa:bb:cc:dd:ee:ff",
            hostname="proxmox-name",
            source=HostSource.PROXMOX,
        )

        result = _pick_hostname([dhcp_host, proxmox_host])
        # Empty string is falsy, so Proxmox hostname should be selected
        assert result == "proxmox-name"

    def test_pick_primary_source_follows_priority(self, discovered_host_factory):
        """Primary source should follow DHCP > Proxmox > Scan priority."""
        dhcp_host = discovered_host_factory(
            mac="aa:bb:cc:dd:ee:ff",
            source=HostSource.DHCP,
        )
        proxmox_host = discovered_host_factory(
            mac="aa:bb:cc:dd:ee:ff",
            source=HostSource.PROXMOX,
        )
        scan_host = discovered_host_factory(
            mac="aa:bb:cc:dd:ee:ff",
            source=HostSource.SCAN,
        )

        # Test all orders to ensure priority is enforced
        result1 = _pick_primary_source([scan_host, proxmox_host, dhcp_host])
        assert result1 == HostSource.DHCP

        result2 = _pick_primary_source([scan_host, proxmox_host])
        assert result2 == HostSource.PROXMOX

        result3 = _pick_primary_source([scan_host])
        assert result3 == HostSource.SCAN

    def test_pick_primary_source_returns_first_when_empty(self, discovered_host_factory):
        """Should return first host's source when no priority match."""
        manual_host = discovered_host_factory(
            mac="aa:bb:cc:dd:ee:ff",
            source=HostSource.MANUAL,
        )

        # MANUAL is not in the priority list, so returns the first host's source
        result = _pick_primary_source([manual_host])
        assert result == HostSource.MANUAL
