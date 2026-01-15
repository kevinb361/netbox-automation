"""Collectors package for netbox-auto discovery.

Provides collector implementations for various host discovery sources.
"""

from netbox_auto.collectors.base import Collector, DiscoveredHost
from netbox_auto.collectors.dhcp import DHCPCollector
from netbox_auto.collectors.proxmox import ProxmoxCollector
from netbox_auto.collectors.scanner import ScannerCollector

__all__ = ["Collector", "DiscoveredHost", "DHCPCollector", "ProxmoxCollector", "ScannerCollector"]
