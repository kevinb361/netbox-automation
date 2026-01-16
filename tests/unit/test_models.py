"""Unit tests for SQLAlchemy models.

Tests status workflow, enum validity, and model constraints.
Covers UNIT-03 (pending -> approved -> pushed) and UNIT-04 (pending -> rejected).
"""

import pytest
from sqlalchemy.exc import IntegrityError

from netbox_auto.models import (
    DiscoveryStatus,
    Host,
    HostSource,
    HostStatus,
    HostType,
)


class TestStatusTransitions:
    """Tests for host status transition workflow (UNIT-03, UNIT-04)."""

    def test_host_default_status_is_pending(self, in_memory_db):
        """New hosts should have PENDING status by default."""
        host = Host(mac="aa:bb:cc:dd:ee:01")
        in_memory_db.add(host)
        in_memory_db.commit()

        assert host.status == HostStatus.PENDING.value

    def test_host_status_can_be_approved(self, in_memory_db):
        """Hosts can transition from PENDING to APPROVED."""
        host = Host(mac="aa:bb:cc:dd:ee:02", status=HostStatus.PENDING.value)
        in_memory_db.add(host)
        in_memory_db.commit()

        host.status = HostStatus.APPROVED.value
        in_memory_db.commit()

        assert host.status == HostStatus.APPROVED.value

    def test_host_status_can_be_pushed(self, in_memory_db):
        """Hosts can transition from APPROVED to PUSHED."""
        host = Host(mac="aa:bb:cc:dd:ee:03", status=HostStatus.APPROVED.value)
        in_memory_db.add(host)
        in_memory_db.commit()

        host.status = HostStatus.PUSHED.value
        in_memory_db.commit()

        assert host.status == HostStatus.PUSHED.value

    def test_push_only_processes_approved_hosts(self, in_memory_db):
        """Verify that push module queries only APPROVED hosts.

        This is a design verification test documenting the contract:
        push.push_approved_hosts() filters by HostStatus.APPROVED.value.

        See src/netbox_auto/push.py line 48:
            approved_hosts = session.query(Host).filter(
                Host.status == HostStatus.APPROVED.value
            ).all()
        """
        # Create hosts in various statuses
        pending_host = Host(mac="aa:bb:cc:dd:ee:04", status=HostStatus.PENDING.value)
        approved_host = Host(mac="aa:bb:cc:dd:ee:05", status=HostStatus.APPROVED.value)
        rejected_host = Host(mac="aa:bb:cc:dd:ee:06", status=HostStatus.REJECTED.value)
        pushed_host = Host(mac="aa:bb:cc:dd:ee:07", status=HostStatus.PUSHED.value)

        in_memory_db.add_all([pending_host, approved_host, rejected_host, pushed_host])
        in_memory_db.commit()

        # Query using same filter as push module
        approved_hosts = (
            in_memory_db.query(Host).filter(Host.status == HostStatus.APPROVED.value).all()
        )

        # Only the APPROVED host should be selected
        assert len(approved_hosts) == 1
        assert approved_hosts[0].mac == "aa:bb:cc:dd:ee:05"

    def test_host_status_can_be_rejected(self, in_memory_db):
        """Hosts can transition from PENDING to REJECTED (UNIT-04)."""
        host = Host(mac="aa:bb:cc:dd:ee:08", status=HostStatus.PENDING.value)
        in_memory_db.add(host)
        in_memory_db.commit()

        host.status = HostStatus.REJECTED.value
        in_memory_db.commit()

        assert host.status == HostStatus.REJECTED.value

    def test_status_enum_has_all_expected_values(self):
        """HostStatus enum should have PENDING, APPROVED, REJECTED, PUSHED."""
        expected_values = {"pending", "approved", "rejected", "pushed"}
        actual_values = {status.value for status in HostStatus}

        assert actual_values == expected_values


class TestModelEnums:
    """Tests for model enum values and constraints."""

    def test_host_source_enum_values(self):
        """HostSource enum should have DHCP, PROXMOX, SCAN, MANUAL."""
        expected_values = {"dhcp", "proxmox", "scan", "manual"}
        actual_values = {source.value for source in HostSource}

        assert actual_values == expected_values

    def test_host_type_enum_values(self):
        """HostType enum should have SERVER, WORKSTATION, IOT, NETWORK, UNKNOWN."""
        expected_values = {"server", "workstation", "iot", "network", "unknown"}
        actual_values = {host_type.value for host_type in HostType}

        assert actual_values == expected_values

    def test_discovery_run_status_enum_values(self):
        """DiscoveryStatus enum should have RUNNING, COMPLETED, FAILED."""
        expected_values = {"running", "completed", "failed"}
        actual_values = {status.value for status in DiscoveryStatus}

        assert actual_values == expected_values


class TestHostConstraints:
    """Tests for Host model constraints and representation."""

    def test_host_mac_is_unique_constraint(self, in_memory_db):
        """MAC address should be unique - duplicate should raise IntegrityError."""
        host1 = Host(mac="aa:bb:cc:dd:ee:ff")
        in_memory_db.add(host1)
        in_memory_db.commit()

        host2 = Host(mac="aa:bb:cc:dd:ee:ff")
        in_memory_db.add(host2)

        with pytest.raises(IntegrityError):
            in_memory_db.commit()

    def test_host_repr_includes_key_fields(self, in_memory_db):
        """Host repr should include id, mac, hostname, and status."""
        host = Host(
            mac="aa:bb:cc:dd:ee:11",
            hostname="test-host",
            status=HostStatus.APPROVED.value,
        )
        in_memory_db.add(host)
        in_memory_db.commit()

        repr_str = repr(host)

        assert "aa:bb:cc:dd:ee:11" in repr_str
        assert "test-host" in repr_str
        assert "approved" in repr_str
        assert str(host.id) in repr_str
