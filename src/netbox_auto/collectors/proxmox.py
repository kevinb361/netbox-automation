"""Proxmox VM inventory collector.

Discovers virtual machines from Proxmox VE clusters via the Proxmox API.
Extracts MAC addresses from network interface configurations and IPs
from the QEMU guest agent when available.
"""

import logging
import re
from typing import Any

from proxmoxer import ProxmoxAPI

from netbox_auto.collectors.base import DiscoveredHost
from netbox_auto.config import ProxmoxConfig
from netbox_auto.models import HostSource

logger = logging.getLogger(__name__)

# Regex to extract MAC address from Proxmox net config
# Format: "virtio=AA:BB:CC:DD:EE:FF,bridge=vmbr0" or similar
MAC_PATTERN = re.compile(r"([0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5})")


class ProxmoxCollector:
    """Collector for Proxmox VM inventory.

    Connects to Proxmox VE API and discovers all VMs across all nodes.
    Extracts MAC addresses from VM network configurations and IP addresses
    from the QEMU guest agent when available.
    """

    def __init__(self, config: ProxmoxConfig) -> None:
        """Initialize the Proxmox collector.

        Args:
            config: Proxmox API connection configuration.
        """
        self._config = config

    @property
    def name(self) -> str:
        """Human-readable name for this collector."""
        return "Proxmox"

    def collect(self) -> list[DiscoveredHost]:
        """Collect VMs from Proxmox cluster.

        Returns:
            List of discovered hosts from all VMs with network interfaces.
            Empty list on connection/auth errors.
        """
        try:
            api = ProxmoxAPI(
                self._config.host,
                user=self._config.username,
                password=self._config.password,
                verify_ssl=self._config.verify_ssl,
            )
        except Exception as e:
            logger.error(f"Failed to connect to Proxmox at {self._config.host}: {e}")
            return []

        hosts: list[DiscoveredHost] = []

        try:
            for node in api.nodes.get():
                node_name = node["node"]
                logger.debug(f"Collecting VMs from node {node_name}")

                hosts.extend(self._collect_from_node(api, node_name))

        except Exception as e:
            logger.error(f"Error collecting from Proxmox: {e}")
            return []

        logger.info(f"Proxmox collector found {len(hosts)} VMs with network interfaces")
        return hosts

    def _collect_from_node(self, api: ProxmoxAPI, node_name: str) -> list[DiscoveredHost]:
        """Collect VMs from a single Proxmox node.

        Args:
            api: Connected ProxmoxAPI instance.
            node_name: Name of the node to collect from.

        Returns:
            List of discovered hosts from this node.
        """
        hosts: list[DiscoveredHost] = []

        try:
            vms = api.nodes(node_name).qemu.get()
        except Exception as e:
            logger.warning(f"Failed to get VMs from node {node_name}: {e}")
            return []

        for vm in vms:
            vmid = vm["vmid"]
            vm_name = vm.get("name", f"vm-{vmid}")

            try:
                config = api.nodes(node_name).qemu(vmid).config.get()
            except Exception as e:
                logger.warning(f"Failed to get config for VM {vmid} on {node_name}: {e}")
                continue

            # Extract MAC addresses from network interfaces (net0, net1, etc.)
            macs = self._extract_macs(config)
            if not macs:
                logger.debug(f"VM {vm_name} ({vmid}) has no network interfaces")
                continue

            # Try to get IP addresses from guest agent
            ip_addresses = self._get_agent_ips(api, node_name, vmid)

            # Create a DiscoveredHost for each MAC address
            for mac in macs:
                hosts.append(
                    DiscoveredHost(
                        mac=mac,
                        hostname=vm_name,
                        ip_addresses=ip_addresses,
                        source=HostSource.PROXMOX,
                        switch_port=None,
                    )
                )

        return hosts

    def _extract_macs(self, config: dict[str, Any]) -> list[str]:
        """Extract MAC addresses from VM network configuration.

        Args:
            config: VM configuration dictionary from Proxmox API.

        Returns:
            List of MAC addresses found in network interfaces.
        """
        macs: list[str] = []

        # Check net0 through net9 (typical range)
        for i in range(10):
            net_key = f"net{i}"
            if net_key not in config:
                continue

            net_value = config[net_key]
            # Format: "virtio=AA:BB:CC:DD:EE:FF,bridge=vmbr0"
            match = MAC_PATTERN.search(net_value)
            if match:
                macs.append(match.group(1))

        return macs

    def _get_agent_ips(self, api: ProxmoxAPI, node_name: str, vmid: int) -> list[str]:
        """Get IP addresses from QEMU guest agent.

        Args:
            api: Connected ProxmoxAPI instance.
            node_name: Name of the node.
            vmid: VM ID to query.

        Returns:
            List of IP addresses from guest agent, or empty list if unavailable.
        """
        try:
            result = api.nodes(node_name).qemu(vmid).agent.get("network-get-interfaces")
        except Exception:
            # Guest agent not available or VM not running
            return []

        ip_addresses: list[str] = []

        # Result is a list of interface dicts
        if not isinstance(result, dict) or "result" not in result:
            return []

        for iface in result.get("result", []):
            # Skip loopback
            if iface.get("name") == "lo":
                continue

            for ip_info in iface.get("ip-addresses", []):
                ip_addr = ip_info.get("ip-address")
                if ip_addr and not ip_addr.startswith("127."):
                    ip_addresses.append(ip_addr)

        return ip_addresses
