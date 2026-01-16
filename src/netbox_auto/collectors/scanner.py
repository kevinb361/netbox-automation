"""Network ARP scanner collector for netbox-auto discovery.

Provides ARP-based network scanning to discover hosts with static IP addresses
that may not appear in DHCP leases.

Note: ARP scanning requires elevated privileges (root/admin) on most systems.
"""

import logging

from netbox_auto.collectors.base import DiscoveredHost
from netbox_auto.config import ScannerConfig
from netbox_auto.models import HostSource

logger = logging.getLogger(__name__)


class ScannerCollector:
    """Collector that discovers hosts via ARP scanning.

    Scans configured subnets using ARP requests and collects responding
    hosts' MAC and IP addresses. Useful for finding hosts with static
    IPs that don't appear in DHCP leases.

    Note: Requires elevated privileges (root/admin) to send raw packets.
    """

    def __init__(self, config: ScannerConfig) -> None:
        """Initialize scanner with configuration.

        Args:
            config: Scanner configuration with subnets to scan and timeout.
        """
        self._config = config

    @property
    def name(self) -> str:
        """Human-readable name for this collector."""
        return "network-scanner"

    def collect(self) -> list[DiscoveredHost]:
        """Scan configured subnets and return discovered hosts.

        Uses ARP requests to discover hosts on each configured subnet.
        Hosts are returned with their MAC and IP addresses, with
        source=scan.

        Returns:
            List of discovered hosts. Empty list if scanning fails
            (e.g., insufficient permissions) or no hosts respond.
        """
        try:
            # Import scapy lazily to avoid import errors if not installed
            from scapy.all import ARP, Ether, srp
        except ImportError:
            logger.error("scapy not installed - cannot perform network scanning")
            return []

        discovered: list[DiscoveredHost] = []

        for subnet in self._config.subnets:
            logger.info(f"Scanning subnet: {subnet}")
            try:
                hosts = self._scan_subnet(subnet, ARP, Ether, srp)
                logger.info(f"Found {len(hosts)} hosts in {subnet}")
                discovered.extend(hosts)
            except PermissionError:
                logger.warning(
                    f"Insufficient permissions to scan {subnet}. "
                    "ARP scanning requires root/admin privileges."
                )
            except Exception as e:
                logger.error(f"Error scanning subnet {subnet}: {e}")

        return discovered

    def _scan_subnet(
        self,
        subnet: str,
        ARP: type,  # noqa: N803 - scapy naming convention
        Ether: type,  # noqa: N803 - scapy naming convention
        srp: type,  # noqa: N803 - scapy naming convention
    ) -> list[DiscoveredHost]:
        """Scan a single subnet using ARP.

        Args:
            subnet: CIDR notation subnet to scan (e.g., "192.168.1.0/24")
            ARP: scapy ARP class (passed for testability)
            Ether: scapy Ether class (passed for testability)
            srp: scapy srp function (passed for testability)

        Returns:
            List of discovered hosts in the subnet.
        """
        # Build ARP packet: broadcast Ethernet frame with ARP request
        packet = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=subnet)

        # Send packets and collect responses
        # verbose=0 suppresses scapy's default output
        answered, _ = srp(packet, timeout=self._config.timeout, verbose=0)

        hosts: list[DiscoveredHost] = []
        for _sent, received in answered:
            # received.psrc is the IP address
            # received.hwsrc is the MAC address
            ip_address = received.psrc
            mac_address = received.hwsrc

            host = DiscoveredHost(
                mac=mac_address,
                hostname=None,  # ARP doesn't provide hostname
                ip_addresses=[ip_address],
                source=HostSource.SCAN,
                switch_port=None,
            )
            hosts.append(host)

        return hosts
