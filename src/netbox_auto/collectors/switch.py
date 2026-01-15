"""MikroTik switch MAC table collector.

Queries MikroTik switches for MAC table entries to enable
switch port correlation for discovered hosts.
"""

import logging
from typing import TYPE_CHECKING

import librouteros
from librouteros.exceptions import LibRouterosError

if TYPE_CHECKING:
    from netbox_auto.config import SwitchConfig

logger = logging.getLogger(__name__)


class SwitchCollector:
    """Collector for MikroTik switch MAC table entries.

    Unlike other collectors that implement the Collector protocol and return
    DiscoveredHost lists, SwitchCollector returns a MAC-to-port mapping dict.
    This is used to enrich discovered hosts with switch port information.
    """

    def __init__(self, switches: list["SwitchConfig"]) -> None:
        """Initialize switch collector.

        Args:
            switches: List of MikroTik switch configurations to query.
        """
        self._switches = switches

    @property
    def name(self) -> str:
        """Human-readable name for this collector."""
        return "switch"

    def collect(self) -> dict[str, str]:
        """Collect MAC-to-port mappings from all configured switches.

        Returns:
            Dictionary mapping MAC addresses (lowercase, colon-separated)
            to switch port identifiers in format "switch_name:port_name".
        """
        mappings: dict[str, str] = {}

        for switch in self._switches:
            try:
                switch_mappings = self._collect_from_switch(switch)
                # Merge, newer switch data overwrites (in case of duplicates)
                mappings.update(switch_mappings)
                logger.info(
                    "Collected %d MAC entries from switch %s",
                    len(switch_mappings),
                    switch.name,
                )
            except LibRouterosError as e:
                logger.warning(
                    "Failed to connect to switch %s (%s): %s",
                    switch.name,
                    switch.host,
                    e,
                )
            except Exception as e:
                logger.error(
                    "Unexpected error collecting from switch %s: %s",
                    switch.name,
                    e,
                )

        return mappings

    def _collect_from_switch(self, switch: "SwitchConfig") -> dict[str, str]:
        """Collect MAC table entries from a single switch.

        Tries bridge host table first (CRS series), then falls back to
        switch host table (older switches).

        Args:
            switch: Switch configuration to connect to.

        Returns:
            Dictionary mapping MAC addresses to "switch_name:port_name".
        """
        api = librouteros.connect(
            host=switch.host,
            username=switch.username,
            password=switch.password,
            port=switch.port,
        )

        mappings: dict[str, str] = {}

        try:
            # Try bridge host table first (CRS series, hAP series, etc.)
            hosts = self._get_bridge_hosts(api)
            if not hosts:
                # Fall back to switch host table (older switches)
                hosts = self._get_switch_hosts(api)

            for entry in hosts:
                mac = entry.get("mac-address")
                port = entry.get("on-interface")

                if mac and port:
                    # Normalize MAC to lowercase with colons
                    normalized_mac = mac.lower().replace("-", ":")
                    mappings[normalized_mac] = f"{switch.name}:{port}"

        finally:
            api.close()

        return mappings

    def _get_bridge_hosts(self, api: librouteros.Api) -> list[dict[str, str]]:
        """Get hosts from bridge host table (CRS/hAP series).

        Args:
            api: Connected RouterOS API instance.

        Returns:
            List of host entries with mac-address and on-interface fields.
        """
        try:
            hosts_path = api.path("/interface/bridge/host")
            return list(hosts_path)
        except LibRouterosError:
            return []

    def _get_switch_hosts(self, api: librouteros.Api) -> list[dict[str, str]]:
        """Get hosts from switch host table (older switches).

        Args:
            api: Connected RouterOS API instance.

        Returns:
            List of host entries with mac-address and on-interface fields.
        """
        try:
            hosts_path = api.path("/interface/ethernet/switch/host")
            return list(hosts_path)
        except LibRouterosError:
            return []
