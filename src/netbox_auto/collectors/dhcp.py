"""MikroTik DHCP lease collector.

Collects DHCP lease information from MikroTik routers via the RouterOS API.
"""

import logging
from typing import TYPE_CHECKING

import librouteros
from librouteros.exceptions import LibRouterosError

from netbox_auto.collectors.base import DiscoveredHost
from netbox_auto.models import HostSource

if TYPE_CHECKING:
    from netbox_auto.config import MikroTikConfig

logger = logging.getLogger(__name__)


class DHCPCollector:
    """Collector for MikroTik DHCP server leases.

    Connects to a MikroTik router via the RouterOS API and retrieves
    all active DHCP leases.
    """

    def __init__(self, config: "MikroTikConfig") -> None:
        """Initialize the DHCP collector.

        Args:
            config: MikroTik connection configuration
        """
        self._config = config

    @property
    def name(self) -> str:
        """Human-readable name for this collector."""
        return "MikroTik DHCP"

    def collect(self) -> list[DiscoveredHost]:
        """Collect DHCP leases from MikroTik router.

        Returns:
            List of discovered hosts from DHCP leases.
            Returns empty list if connection fails or no active leases.
        """
        hosts: list[DiscoveredHost] = []

        try:
            api = librouteros.connect(
                host=self._config.host,
                username=self._config.username,
                password=self._config.password,
                port=self._config.port,
            )
        except LibRouterosError as e:
            logger.error(f"Failed to connect to MikroTik at {self._config.host}: {e}")
            return hosts
        except Exception as e:
            logger.error(f"Unexpected error connecting to MikroTik: {e}")
            return hosts

        try:
            leases = api.path("/ip/dhcp-server/lease")
            for lease in leases:
                mac = lease.get("mac-address")
                if not mac:
                    continue

                # Get IP from active-address (current) or address (static)
                ip = lease.get("active-address") or lease.get("address")
                if not ip:
                    # Skip leases without an IP (not active)
                    continue

                hostname = lease.get("host-name") or None

                host = DiscoveredHost(
                    mac=mac,
                    hostname=hostname,
                    ip_addresses=[ip],
                    source=HostSource.DHCP,
                    switch_port=None,
                )
                hosts.append(host)
                logger.debug(f"Discovered host: {mac} ({hostname or 'no hostname'}) -> {ip}")

        except LibRouterosError as e:
            logger.error(f"Failed to query DHCP leases: {e}")
        except Exception as e:
            logger.error(f"Unexpected error querying DHCP leases: {e}")
        finally:
            try:
                api.close()
            except Exception:
                pass  # Ignore close errors

        logger.info(f"Collected {len(hosts)} hosts from DHCP leases")
        return hosts
