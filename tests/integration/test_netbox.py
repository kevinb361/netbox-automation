"""Integration tests for NetBox client operations.

Tests NetBox client methods with mocked pynetbox API to verify
correct API calls without requiring a real NetBox instance.

Covers INTG-03 (device creation), INTG-04 (IP assignment), INTG-05 (cable creation).
"""

from unittest.mock import MagicMock, patch

from netbox_auto.netbox import NetBoxClient


class TestDeviceCreation:
    """Test device and VM creation API calls (INTG-03)."""

    def test_create_device_calls_api(self) -> None:
        """Verify create_device calls dcim.devices.create with correct params."""
        mock_device = MagicMock()
        mock_device.id = 42

        with patch("netbox_auto.netbox.pynetbox") as mock_pynetbox:
            mock_api = MagicMock()
            mock_pynetbox.api.return_value = mock_api
            mock_api.dcim.devices.create.return_value = mock_device

            client = NetBoxClient(url="http://netbox.local", token="test-token")
            client.create_device(
                name="test-device",
                device_type_id=1,
                device_role_id=2,
                site_id=3,
            )

            mock_api.dcim.devices.create.assert_called_once_with(
                name="test-device",
                device_type=1,
                role=2,
                site=3,
                status="active",
            )

    def test_create_device_returns_id(self) -> None:
        """Verify create_device returns dict with id from mock response."""
        mock_device = MagicMock()
        mock_device.id = 123

        with patch("netbox_auto.netbox.pynetbox") as mock_pynetbox:
            mock_api = MagicMock()
            mock_pynetbox.api.return_value = mock_api
            mock_api.dcim.devices.create.return_value = mock_device

            client = NetBoxClient(url="http://netbox.local", token="test-token")
            result = client.create_device(
                name="test-device",
                device_type_id=1,
                device_role_id=2,
                site_id=3,
            )

            assert result == {"id": 123}

    def test_create_vm_calls_api(self) -> None:
        """Verify create_vm calls virtualization.virtual_machines.create with correct params."""
        mock_vm = MagicMock()
        mock_vm.id = 55

        with patch("netbox_auto.netbox.pynetbox") as mock_pynetbox:
            mock_api = MagicMock()
            mock_pynetbox.api.return_value = mock_api
            mock_api.virtualization.virtual_machines.create.return_value = mock_vm

            client = NetBoxClient(url="http://netbox.local", token="test-token")
            result = client.create_vm(
                name="test-vm",
                cluster_id=10,
            )

            mock_api.virtualization.virtual_machines.create.assert_called_once_with(
                name="test-vm",
                cluster=10,
                status="active",
            )
            assert result == {"id": 55}


class TestIPAssignment:
    """Test IP address assignment operations (INTG-04)."""

    def test_assign_ip_creates_address(self) -> None:
        """Verify assign_ip calls ipam.ip_addresses.create with correct params."""
        mock_ip = MagicMock()
        mock_ip.id = 100

        with patch("netbox_auto.netbox.pynetbox") as mock_pynetbox:
            mock_api = MagicMock()
            mock_pynetbox.api.return_value = mock_api
            mock_api.ipam.ip_addresses.create.return_value = mock_ip

            client = NetBoxClient(url="http://netbox.local", token="test-token")
            result = client.assign_ip(
                ip_address="192.168.1.100/24",
                interface_id=5,
                interface_type="dcim.interface",
            )

            mock_api.ipam.ip_addresses.create.assert_called_once_with(
                address="192.168.1.100/24",
                assigned_object_type="dcim.interface",
                assigned_object_id=5,
            )
            assert result == {"id": 100}

    def test_assign_ip_adds_prefix(self) -> None:
        """Verify IP without /XX gets /32 added."""
        mock_ip = MagicMock()
        mock_ip.id = 101

        with patch("netbox_auto.netbox.pynetbox") as mock_pynetbox:
            mock_api = MagicMock()
            mock_pynetbox.api.return_value = mock_api
            mock_api.ipam.ip_addresses.create.return_value = mock_ip

            client = NetBoxClient(url="http://netbox.local", token="test-token")
            client.assign_ip(
                ip_address="10.0.0.50",  # No prefix
                interface_id=6,
            )

            # Should have /32 added
            mock_api.ipam.ip_addresses.create.assert_called_once_with(
                address="10.0.0.50/32",
                assigned_object_type="dcim.interface",
                assigned_object_id=6,
            )

    def test_get_or_create_interface_finds_existing(self) -> None:
        """Verify get_or_create_interface returns existing interface without creating."""
        mock_existing = MagicMock()
        mock_existing.id = 200

        with patch("netbox_auto.netbox.pynetbox") as mock_pynetbox:
            mock_api = MagicMock()
            mock_pynetbox.api.return_value = mock_api
            mock_api.dcim.interfaces.filter.return_value = [mock_existing]

            client = NetBoxClient(url="http://netbox.local", token="test-token")
            result = client.get_or_create_interface(
                device_id=10,
                name="eth0",
            )

            mock_api.dcim.interfaces.filter.assert_called_once_with(device_id=10, name="eth0")
            mock_api.dcim.interfaces.create.assert_not_called()
            assert result == {"id": 200}

    def test_get_or_create_interface_creates_new(self) -> None:
        """Verify get_or_create_interface creates new interface when none exists."""
        mock_new = MagicMock()
        mock_new.id = 201

        with patch("netbox_auto.netbox.pynetbox") as mock_pynetbox:
            mock_api = MagicMock()
            mock_pynetbox.api.return_value = mock_api
            mock_api.dcim.interfaces.filter.return_value = []  # No existing
            mock_api.dcim.interfaces.create.return_value = mock_new

            client = NetBoxClient(url="http://netbox.local", token="test-token")
            result = client.get_or_create_interface(
                device_id=10,
                name="eth1",
                interface_type="10gbase-t",
            )

            mock_api.dcim.interfaces.create.assert_called_once_with(
                device=10,
                name="eth1",
                type="10gbase-t",
            )
            assert result == {"id": 201}


class TestCableCreation:
    """Test cable creation operations (INTG-05)."""

    def test_create_cable_calls_api(self) -> None:
        """Verify create_cable calls dcim.cables.create with correct terminations format."""
        mock_cable = MagicMock()
        mock_cable.id = 300

        with patch("netbox_auto.netbox.pynetbox") as mock_pynetbox:
            mock_api = MagicMock()
            mock_pynetbox.api.return_value = mock_api
            mock_api.dcim.cables.create.return_value = mock_cable

            client = NetBoxClient(url="http://netbox.local", token="test-token")
            client.create_cable(
                a_termination_type="dcim.interface",
                a_termination_id=10,
                b_termination_type="dcim.interface",
                b_termination_id=20,
            )

            mock_api.dcim.cables.create.assert_called_once_with(
                a_terminations=[{"object_type": "dcim.interface", "object_id": 10}],
                b_terminations=[{"object_type": "dcim.interface", "object_id": 20}],
            )

    def test_create_cable_returns_id(self) -> None:
        """Verify create_cable returns dict with cable ID."""
        mock_cable = MagicMock()
        mock_cable.id = 456

        with patch("netbox_auto.netbox.pynetbox") as mock_pynetbox:
            mock_api = MagicMock()
            mock_pynetbox.api.return_value = mock_api
            mock_api.dcim.cables.create.return_value = mock_cable

            client = NetBoxClient(url="http://netbox.local", token="test-token")
            result = client.create_cable(
                a_termination_type="dcim.interface",
                a_termination_id=15,
                b_termination_type="dcim.interface",
                b_termination_id=25,
            )

            assert result == {"id": 456}


class TestClientConnection:
    """Test lazy connection and caching behavior."""

    def test_lazy_connection(self) -> None:
        """Verify client doesn't connect until first API call."""
        with patch("netbox_auto.netbox.pynetbox") as mock_pynetbox:
            client = NetBoxClient(url="http://netbox.local", token="test-token")

            # No connection yet
            mock_pynetbox.api.assert_not_called()

            # Trigger connection via API call
            mock_api = MagicMock()
            mock_pynetbox.api.return_value = mock_api
            mock_api.dcim.devices.all.return_value = []
            client.get_devices()

            # Now connected
            mock_pynetbox.api.assert_called_once_with("http://netbox.local", token="test-token")

    def test_connection_caches_api(self) -> None:
        """Verify second call reuses existing connection."""
        with patch("netbox_auto.netbox.pynetbox") as mock_pynetbox:
            mock_api = MagicMock()
            mock_pynetbox.api.return_value = mock_api
            mock_api.dcim.devices.all.return_value = []
            mock_api.virtualization.virtual_machines.all.return_value = []

            client = NetBoxClient(url="http://netbox.local", token="test-token")

            # First call
            client.get_devices()
            assert mock_pynetbox.api.call_count == 1

            # Second call should reuse connection
            client.get_vms()
            assert mock_pynetbox.api.call_count == 1  # Still 1, not 2
