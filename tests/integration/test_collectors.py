"""Integration tests for network collectors.

Tests MikroTik DHCP and Proxmox collectors with mocked external APIs.
Verifies collector logic without requiring real network access.

Requirements covered:
- INTG-01: MikroTik DHCP collector integration tests
- INTG-02: Proxmox collector integration tests
"""

from unittest.mock import MagicMock, patch

import pytest
from librouteros.exceptions import LibRouterosError

from netbox_auto.collectors.dhcp import DHCPCollector
from netbox_auto.collectors.proxmox import ProxmoxCollector
from netbox_auto.config import MikroTikConfig, ProxmoxConfig
from netbox_auto.models import HostSource

# =============================================================================
# MikroTik DHCP Collector Tests (INTG-01)
# =============================================================================


@pytest.fixture
def mikrotik_config() -> MikroTikConfig:
    """Create test MikroTik configuration."""
    return MikroTikConfig(
        host="192.168.88.1",
        username="admin",
        password="testpassword",
        port=8728,
    )


class TestDHCPCollectorConnect:
    """Tests for DHCP collector connection handling."""

    def test_dhcp_collector_connects_to_router(self, mikrotik_config: MikroTikConfig) -> None:
        """Verify collector connects with correct config values."""
        mock_api = MagicMock()
        mock_api.path.return_value = []  # Empty leases

        with patch("netbox_auto.collectors.dhcp.librouteros.connect") as mock_connect:
            mock_connect.return_value = mock_api

            collector = DHCPCollector(mikrotik_config)
            collector.collect()

            mock_connect.assert_called_once_with(
                host="192.168.88.1",
                username="admin",
                password="testpassword",
                port=8728,
            )

    def test_dhcp_collector_handles_connection_error(self, mikrotik_config: MikroTikConfig) -> None:
        """Verify collector returns empty list on connection failure."""
        with patch("netbox_auto.collectors.dhcp.librouteros.connect") as mock_connect:
            mock_connect.side_effect = LibRouterosError("Connection refused")

            collector = DHCPCollector(mikrotik_config)
            hosts = collector.collect()

            assert hosts == []


class TestDHCPCollectorLeases:
    """Tests for DHCP lease processing."""

    def test_dhcp_collector_returns_hosts_from_leases(
        self, mikrotik_config: MikroTikConfig
    ) -> None:
        """Verify collector converts DHCP leases to DiscoveredHost objects."""
        mock_leases = [
            {
                "mac-address": "AA:BB:CC:DD:EE:01",
                "address": "192.168.1.10",
                "host-name": "workstation-1",
            },
            {
                "mac-address": "AA:BB:CC:DD:EE:02",
                "active-address": "192.168.1.11",
                "host-name": "server-1",
            },
        ]

        mock_api = MagicMock()
        mock_api.path.return_value = mock_leases

        with patch("netbox_auto.collectors.dhcp.librouteros.connect") as mock_connect:
            mock_connect.return_value = mock_api

            collector = DHCPCollector(mikrotik_config)
            hosts = collector.collect()

            assert len(hosts) == 2

            # Check first host (MACs are normalized to lowercase)
            assert hosts[0].mac == "aa:bb:cc:dd:ee:01"
            assert hosts[0].hostname == "workstation-1"
            assert hosts[0].ip_addresses == ["192.168.1.10"]
            assert hosts[0].source == HostSource.DHCP

            # Check second host
            assert hosts[1].mac == "aa:bb:cc:dd:ee:02"
            assert hosts[1].hostname == "server-1"
            assert hosts[1].ip_addresses == ["192.168.1.11"]
            assert hosts[1].source == HostSource.DHCP

    def test_dhcp_collector_skips_leases_without_mac(self, mikrotik_config: MikroTikConfig) -> None:
        """Verify collector skips leases missing MAC address field."""
        mock_leases = [
            {
                # No mac-address field
                "address": "192.168.1.10",
                "host-name": "orphan-lease",
            },
            {
                "mac-address": "AA:BB:CC:DD:EE:01",
                "address": "192.168.1.11",
                "host-name": "valid-lease",
            },
        ]

        mock_api = MagicMock()
        mock_api.path.return_value = mock_leases

        with patch("netbox_auto.collectors.dhcp.librouteros.connect") as mock_connect:
            mock_connect.return_value = mock_api

            collector = DHCPCollector(mikrotik_config)
            hosts = collector.collect()

            # Only the host with MAC should be included (normalized to lowercase)
            assert len(hosts) == 1
            assert hosts[0].mac == "aa:bb:cc:dd:ee:01"

    def test_dhcp_collector_uses_active_address_over_address(
        self, mikrotik_config: MikroTikConfig
    ) -> None:
        """Verify collector prefers active-address when both fields present."""
        mock_leases = [
            {
                "mac-address": "AA:BB:CC:DD:EE:01",
                "address": "192.168.1.10",  # Static/assigned address
                "active-address": "192.168.1.20",  # Current active address
                "host-name": "dynamic-host",
            },
        ]

        mock_api = MagicMock()
        mock_api.path.return_value = mock_leases

        with patch("netbox_auto.collectors.dhcp.librouteros.connect") as mock_connect:
            mock_connect.return_value = mock_api

            collector = DHCPCollector(mikrotik_config)
            hosts = collector.collect()

            assert len(hosts) == 1
            # active-address should be preferred
            assert hosts[0].ip_addresses == ["192.168.1.20"]


# =============================================================================
# Proxmox Collector Tests (INTG-02)
# =============================================================================


@pytest.fixture
def proxmox_config() -> ProxmoxConfig:
    """Create test Proxmox configuration."""
    return ProxmoxConfig(
        host="pve.example.com",
        username="root@pam",
        password="testpassword",
        verify_ssl=False,
    )


class TestProxmoxCollectorConnect:
    """Tests for Proxmox collector connection handling."""

    def test_proxmox_collector_connects_to_api(self, proxmox_config: ProxmoxConfig) -> None:
        """Verify collector connects with correct config values."""
        mock_api = MagicMock()
        mock_api.nodes.get.return_value = []  # No nodes

        with patch(
            "netbox_auto.collectors.proxmox.ProxmoxAPI", return_value=mock_api
        ) as mock_class:
            collector = ProxmoxCollector(proxmox_config)
            collector.collect()

            mock_class.assert_called_once_with(
                "pve.example.com",
                user="root@pam",
                password="testpassword",
                verify_ssl=False,
            )


class TestProxmoxCollectorVMs:
    """Tests for Proxmox VM discovery."""

    def test_proxmox_collector_discovers_vms(self, proxmox_config: ProxmoxConfig) -> None:
        """Verify collector discovers VMs and extracts MAC addresses."""
        # Setup mock API
        mock_api = MagicMock()

        # Mock nodes list
        mock_api.nodes.get.return_value = [{"node": "pve1"}]

        # Mock VMs on node
        mock_api.nodes.return_value.qemu.get.return_value = [
            {"vmid": 100, "name": "web-server"},
            {"vmid": 101, "name": "db-server"},
        ]

        # Mock VM configs with network interfaces
        def mock_config_get(vmid):
            configs = {
                100: {"net0": "virtio=AA:BB:CC:DD:EE:01,bridge=vmbr0"},
                101: {"net0": "virtio=AA:BB:CC:DD:EE:02,bridge=vmbr0"},
            }
            mock_vm = MagicMock()
            mock_vm.config.get.return_value = configs[vmid]
            return mock_vm

        mock_api.nodes.return_value.qemu.side_effect = mock_config_get

        # Mock agent call (returns empty - no guest agent)
        def mock_agent_get(vmid):
            mock_vm = MagicMock()
            mock_vm.agent.get.side_effect = Exception("QEMU guest agent is not running")
            return mock_vm

        def qemu_handler(*args):
            if not args:
                # qemu.get() call - return VM list
                mock_qemu = MagicMock()
                mock_qemu.get.return_value = [
                    {"vmid": 100, "name": "web-server"},
                    {"vmid": 101, "name": "db-server"},
                ]
                return mock_qemu
            else:
                # qemu(vmid) call
                vmid = args[0]
                mock_vm = MagicMock()
                configs = {
                    100: {"net0": "virtio=AA:BB:CC:DD:EE:01,bridge=vmbr0"},
                    101: {"net0": "virtio=AA:BB:CC:DD:EE:02,bridge=vmbr0"},
                }
                mock_vm.config.get.return_value = configs[vmid]
                mock_vm.agent.get.side_effect = Exception("QEMU guest agent is not running")
                return mock_vm

        mock_node = MagicMock()
        mock_node.qemu = MagicMock(side_effect=qemu_handler)
        mock_node.qemu.get.return_value = [
            {"vmid": 100, "name": "web-server"},
            {"vmid": 101, "name": "db-server"},
        ]
        mock_api.nodes.return_value = mock_node

        with patch("netbox_auto.collectors.proxmox.ProxmoxAPI", return_value=mock_api):
            collector = ProxmoxCollector(proxmox_config)
            hosts = collector.collect()

            assert len(hosts) == 2

            # Check hosts (MACs normalized to lowercase, order may vary)
            macs = {h.mac for h in hosts}
            assert "aa:bb:cc:dd:ee:01" in macs
            assert "aa:bb:cc:dd:ee:02" in macs

            hostnames = {h.hostname for h in hosts}
            assert "web-server" in hostnames
            assert "db-server" in hostnames

            # All should be PROXMOX source
            for host in hosts:
                assert host.source == HostSource.PROXMOX

    def test_proxmox_collector_extracts_mac_from_net_config(
        self, proxmox_config: ProxmoxConfig
    ) -> None:
        """Verify MAC regex extraction from various net config formats."""
        # Test the MAC extraction directly via collector internals
        collector = ProxmoxCollector(proxmox_config)

        # Test various Proxmox net config formats
        test_cases = [
            (
                {"net0": "virtio=AA:BB:CC:DD:EE:FF,bridge=vmbr0"},
                ["AA:BB:CC:DD:EE:FF"],
            ),
            (
                {"net0": "e1000=11:22:33:44:55:66,bridge=vmbr1,firewall=1"},
                ["11:22:33:44:55:66"],
            ),
            (
                {
                    "net0": "virtio=AA:BB:CC:DD:EE:01,bridge=vmbr0",
                    "net1": "virtio=AA:BB:CC:DD:EE:02,bridge=vmbr1",
                },
                ["AA:BB:CC:DD:EE:01", "AA:BB:CC:DD:EE:02"],
            ),
            # No network interfaces
            ({"memory": 2048, "cores": 2}, []),
        ]

        for config, expected_macs in test_cases:
            macs = collector._extract_macs(config)
            assert macs == expected_macs, f"Failed for config: {config}"


class TestProxmoxCollectorGuestAgent:
    """Tests for Proxmox guest agent IP extraction."""

    def test_proxmox_collector_gets_ips_from_guest_agent(
        self, proxmox_config: ProxmoxConfig
    ) -> None:
        """Verify collector extracts IPs from guest agent response."""
        mock_api = MagicMock()
        mock_api.nodes.get.return_value = [{"node": "pve1"}]

        # Setup VM with guest agent returning IPs
        mock_node = MagicMock()
        mock_vm = MagicMock()
        mock_vm.config.get.return_value = {"net0": "virtio=AA:BB:CC:DD:EE:01,bridge=vmbr0"}

        # Guest agent response with network interfaces
        mock_vm.agent.get.return_value = {
            "result": [
                {
                    "name": "lo",
                    "ip-addresses": [{"ip-address": "127.0.0.1"}],
                },
                {
                    "name": "eth0",
                    "ip-addresses": [
                        {"ip-address": "192.168.1.100"},
                        {"ip-address": "fe80::1"},  # IPv6 link-local
                    ],
                },
            ]
        }

        def qemu_handler(*args):
            if not args:
                mock_qemu = MagicMock()
                mock_qemu.get.return_value = [{"vmid": 100, "name": "test-vm"}]
                return mock_qemu
            else:
                return mock_vm

        mock_node.qemu = MagicMock(side_effect=qemu_handler)
        mock_node.qemu.get.return_value = [{"vmid": 100, "name": "test-vm"}]
        mock_api.nodes.return_value = mock_node

        with patch("netbox_auto.collectors.proxmox.ProxmoxAPI", return_value=mock_api):
            collector = ProxmoxCollector(proxmox_config)
            hosts = collector.collect()

            assert len(hosts) == 1
            # Should have IPs from guest agent (excluding loopback)
            assert "192.168.1.100" in hosts[0].ip_addresses
            assert "fe80::1" in hosts[0].ip_addresses
            # Loopback should be excluded
            assert "127.0.0.1" not in hosts[0].ip_addresses

    def test_proxmox_collector_handles_missing_guest_agent(
        self, proxmox_config: ProxmoxConfig
    ) -> None:
        """Verify collector returns empty IP list when guest agent unavailable."""
        mock_api = MagicMock()
        mock_api.nodes.get.return_value = [{"node": "pve1"}]

        mock_node = MagicMock()
        mock_vm = MagicMock()
        mock_vm.config.get.return_value = {"net0": "virtio=AA:BB:CC:DD:EE:01,bridge=vmbr0"}
        # Guest agent call raises exception (VM not running or no agent)
        mock_vm.agent.get.side_effect = Exception("QEMU guest agent is not running")

        def qemu_handler(*args):
            if not args:
                mock_qemu = MagicMock()
                mock_qemu.get.return_value = [{"vmid": 100, "name": "test-vm"}]
                return mock_qemu
            else:
                return mock_vm

        mock_node.qemu = MagicMock(side_effect=qemu_handler)
        mock_node.qemu.get.return_value = [{"vmid": 100, "name": "test-vm"}]
        mock_api.nodes.return_value = mock_node

        with patch("netbox_auto.collectors.proxmox.ProxmoxAPI", return_value=mock_api):
            collector = ProxmoxCollector(proxmox_config)
            hosts = collector.collect()

            assert len(hosts) == 1
            # Should have MAC (normalized to lowercase) but empty IP list (guest agent unavailable)
            assert hosts[0].mac == "aa:bb:cc:dd:ee:01"
            assert hosts[0].ip_addresses == []
