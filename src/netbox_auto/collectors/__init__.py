"""Collectors package for netbox-auto discovery.

Provides collector implementations for various host discovery sources.
"""

from netbox_auto.collectors.base import Collector, DiscoveredHost

__all__ = ["Collector", "DiscoveredHost"]
