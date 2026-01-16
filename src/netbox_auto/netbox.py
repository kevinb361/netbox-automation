"""NetBox API client for device and VM listing.

Provides a client wrapper for the pynetbox library to fetch
existing devices and VMs from NetBox for comparison with discovered hosts.
"""

import logging
from typing import TYPE_CHECKING, Any

import pynetbox
from pynetbox.core.api import Api as NetBoxApi

if TYPE_CHECKING:
    from netbox_auto.config import NetBoxConfig

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
