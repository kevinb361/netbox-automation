"""Collectors package for netbox-auto discovery.

Provides collector implementations for various host discovery sources.
"""

from netbox_auto.collectors.base import Collector, DiscoveredHost
from netbox_auto.collectors.dhcp import DHCPCollector

__all__ = ["Collector", "DiscoveredHost", "DHCPCollector"]
