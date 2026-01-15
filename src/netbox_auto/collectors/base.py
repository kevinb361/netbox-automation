"""Base collector protocol for netbox-auto discovery.

Provides the Collector Protocol and DiscoveredHost dataclass that all
collectors must implement.
"""

from dataclasses import dataclass, field
from typing import Protocol

from netbox_auto.models import HostSource


@dataclass
class DiscoveredHost:
    """A host discovered by a collector.

    Attributes:
        mac: MAC address in lowercase colon format (aa:bb:cc:dd:ee:ff)
        hostname: Optional hostname from discovery source
        ip_addresses: List of IP addresses associated with this host
        source: Discovery source (dhcp, proxmox, scan, manual)
        switch_port: Optional switch port identifier (e.g., "switch01:ether5")
    """

    mac: str
    hostname: str | None = None
    ip_addresses: list[str] = field(default_factory=list)
    source: HostSource = HostSource.MANUAL
    switch_port: str | None = None

    def __post_init__(self) -> None:
        """Normalize MAC address to lowercase with colons."""
        self.mac = self.mac.lower().replace("-", ":")


class Collector(Protocol):
    """Protocol that all collectors must implement.

    Collectors are responsible for gathering host information from a single
    source (DHCP, Proxmox, network scan, etc.). The orchestrator handles
    persistence and correlation.
    """

    @property
    def name(self) -> str:
        """Human-readable name for this collector."""
        ...

    def collect(self) -> list[DiscoveredHost]:
        """Collect hosts from this source.

        Returns:
            List of discovered hosts. Empty list if collection fails
            or no hosts are found.
        """
        ...
