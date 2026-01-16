"""NetBox API client for device and VM listing.

Provides a client wrapper for the pynetbox library to fetch
existing devices and VMs from NetBox for comparison with discovered hosts.
"""

import logging
from typing import TYPE_CHECKING, Any

import pynetbox
from pynetbox.core.api import Api as NetBoxApi

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class NetBoxClient:
    """Client for interacting with NetBox API.

    Provides methods to fetch devices and VMs from NetBox for comparison
    with discovered hosts. Uses lazy connection to defer API initialization
    until first use.
    """

    def __init__(self, url: str | None = None, token: str | None = None) -> None:
        """Initialize the NetBox client.

        Args:
            url: NetBox API URL. If not provided, will use config.
            token: NetBox API token. If not provided, will use config.
        """
        self._url = url
        self._token = token
        self._api: NetBoxApi | None = None

    def _connect(self) -> NetBoxApi:
        """Establish connection to NetBox API.

        Returns:
            Connected pynetbox API instance.

        Raises:
            ValueError: If URL or token not provided and not in config.
        """
        if self._api is not None:
            return self._api

        url = self._url
        token = self._token

        # Get from config if not provided
        if url is None or token is None:
            from netbox_auto.config import get_config

            config = get_config()
            if config.netbox is None:
                raise ValueError(
                    "NetBox configuration not found. "
                    "Add netbox section to config.yaml or provide url/token."
                )
            url = url or config.netbox.url
            token = token or config.netbox.token

        self._api = pynetbox.api(url, token=token)
        return self._api

    def get_devices(self) -> list[dict[str, Any]]:
        """Fetch all devices from NetBox.

        Returns:
            List of device dictionaries with fields:
            - id: NetBox device ID
            - name: Device name
            - primary_ip: Primary IP address (if assigned)
            - device_type: Device type model name
            - status: Device status (active, planned, etc.)

        Returns empty list if connection fails.
        """
        devices: list[dict[str, Any]] = []

        try:
            api = self._connect()
            for device in api.dcim.devices.all():
                primary_ip = None
                if device.primary_ip:
                    # Extract IP without prefix length
                    primary_ip = str(device.primary_ip).split("/")[0]

                devices.append(
                    {
                        "id": device.id,
                        "name": device.name,
                        "primary_ip": primary_ip,
                        "device_type": str(device.device_type) if device.device_type else None,
                        "status": str(device.status) if device.status else None,
                    }
                )
        except Exception as e:
            logger.warning(f"Failed to fetch devices from NetBox: {e}")
            return []

        logger.info(f"Fetched {len(devices)} devices from NetBox")
        return devices

    def get_vms(self) -> list[dict[str, Any]]:
        """Fetch all virtual machines from NetBox.

        Returns:
            List of VM dictionaries with fields:
            - id: NetBox VM ID
            - name: VM name
            - primary_ip: Primary IP address (if assigned)
            - status: VM status (active, offline, etc.)

        Returns empty list if connection fails.
        """
        vms: list[dict[str, Any]] = []

        try:
            api = self._connect()
            for vm in api.virtualization.virtual_machines.all():
                primary_ip = None
                if vm.primary_ip:
                    # Extract IP without prefix length
                    primary_ip = str(vm.primary_ip).split("/")[0]

                vms.append(
                    {
                        "id": vm.id,
                        "name": vm.name,
                        "primary_ip": primary_ip,
                        "status": str(vm.status) if vm.status else None,
                    }
                )
        except Exception as e:
            logger.warning(f"Failed to fetch VMs from NetBox: {e}")
            return []

        logger.info(f"Fetched {len(vms)} VMs from NetBox")
        return vms

    def create_device(
        self,
        name: str,
        device_type_id: int,
        device_role_id: int,
        site_id: int,
    ) -> dict[str, Any]:
        """Create a new device in NetBox.

        Args:
            name: Device name.
            device_type_id: ID of the device type.
            device_role_id: ID of the device role.
            site_id: ID of the site.

        Returns:
            Dictionary with 'id' of the created device.

        Raises:
            Exception: If device creation fails.
        """
        api = self._connect()
        device = api.dcim.devices.create(
            name=name,
            device_type=device_type_id,
            role=device_role_id,
            site=site_id,
            status="active",
        )
        logger.info(f"Created device '{name}' with ID {device.id}")
        return {"id": device.id}

    def create_vm(
        self,
        name: str,
        cluster_id: int,
    ) -> dict[str, Any]:
        """Create a new virtual machine in NetBox.

        Args:
            name: VM name.
            cluster_id: ID of the cluster to place the VM in.

        Returns:
            Dictionary with 'id' of the created VM.

        Raises:
            Exception: If VM creation fails.
        """
        api = self._connect()
        vm = api.virtualization.virtual_machines.create(
            name=name,
            cluster=cluster_id,
            status="active",
        )
        logger.info(f"Created VM '{name}' with ID {vm.id}")
        return {"id": vm.id}

    def assign_ip(
        self,
        ip_address: str,
        interface_id: int,
        interface_type: str = "dcim.interface",
    ) -> dict[str, Any]:
        """Assign an IP address to an interface.

        Args:
            ip_address: IP address with or without prefix (e.g., '192.168.1.1' or '192.168.1.1/24').
            interface_id: ID of the interface to assign the IP to.
            interface_type: Type of interface ('dcim.interface' for devices, 'virtualization.vminterface' for VMs).

        Returns:
            Dictionary with 'id' of the created IP address.

        Raises:
            Exception: If IP assignment fails.
        """
        api = self._connect()
        # Ensure IP has prefix length
        if "/" not in ip_address:
            ip_address = f"{ip_address}/32"

        ip = api.ipam.ip_addresses.create(
            address=ip_address,
            assigned_object_type=interface_type,
            assigned_object_id=interface_id,
        )
        logger.info(f"Assigned IP '{ip_address}' to interface {interface_id}")
        return {"id": ip.id}


def get_netbox_client() -> NetBoxClient:
    """Create a NetBox client from configuration.

    Returns:
        NetBoxClient instance configured from config file.

    Note:
        The client uses lazy connection, so actual connection
        errors will occur on first API call, not here.
    """
    return NetBoxClient()


def get_netbox_devices() -> list[dict[str, Any]]:
    """Convenience function to get devices from NetBox.

    Returns:
        List of device dictionaries from NetBox.
        Returns empty list if connection fails.
    """
    client = get_netbox_client()
    return client.get_devices()


def get_netbox_vms() -> list[dict[str, Any]]:
    """Convenience function to get VMs from NetBox.

    Returns:
        List of VM dictionaries from NetBox.
        Returns empty list if connection fails.
    """
    client = get_netbox_client()
    return client.get_vms()
