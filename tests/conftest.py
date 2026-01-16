"""Shared pytest fixtures for netbox-auto tests.

Provides factory functions and database fixtures used across test modules.
"""

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from netbox_auto.collectors.base import DiscoveredHost
from netbox_auto.models import Base, HostSource


@pytest.fixture
def discovered_host_factory():
    """Factory function for creating DiscoveredHost instances.

    Returns a callable that creates DiscoveredHost with sensible defaults.
    Useful for tests needing multiple hosts with varying attributes.

    Example:
        def test_merge(discovered_host_factory):
            host1 = discovered_host_factory(mac="aa:bb:cc:dd:ee:ff")
            host2 = discovered_host_factory(mac="aa:bb:cc:dd:ee:ff", source=HostSource.PROXMOX)
    """

    def _factory(
        mac: str = "aa:bb:cc:dd:ee:ff",
        hostname: str | None = None,
        ip_addresses: list[str] | None = None,
        source: HostSource = HostSource.DHCP,
        switch_port: str | None = None,
    ) -> DiscoveredHost:
        return DiscoveredHost(
            mac=mac,
            hostname=hostname,
            ip_addresses=ip_addresses if ip_addresses is not None else [],
            source=source,
            switch_port=switch_port,
        )

    return _factory


@pytest.fixture(scope="session")
def in_memory_engine():
    """Session-scoped in-memory SQLite engine.

    Creates a single engine used across all tests in the session.
    Tables are created once at session start.
    """
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def in_memory_db(in_memory_engine) -> Iterator[Session]:
    """Function-scoped database session for in-memory SQLite.

    Each test gets a fresh transaction that is rolled back after the test.
    This ensures test isolation while reusing the same in-memory database.

    Example:
        def test_host_creation(in_memory_db):
            host = Host(mac="aa:bb:cc:dd:ee:ff")
            in_memory_db.add(host)
            in_memory_db.commit()
            assert in_memory_db.query(Host).count() == 1
    """
    connection = in_memory_engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection)
    session = session_factory()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
