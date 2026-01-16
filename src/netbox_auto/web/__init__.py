"""Web interface for netbox-auto.

Provides Flask application for reviewing and managing discovered hosts.
"""

from netbox_auto.web.app import create_app

__all__ = ["create_app"]
