"""SQLAlchemy models for netbox-auto staging database.

Provides ORM models for tracking discovered hosts and discovery runs.
Uses SQLAlchemy 2.0 style with Mapped and mapped_column.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    type_annotation_map = {
        dict[str, Any]: JSON,
    }


class DiscoveryStatus(str, Enum):
    """Status of a discovery run."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class HostSource(str, Enum):
    """Source where a host was discovered."""

    DHCP = "dhcp"
    PROXMOX = "proxmox"
    SCAN = "scan"
    MANUAL = "manual"


class HostStatus(str, Enum):
    """Approval status of a discovered host."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUSHED = "pushed"


class HostType(str, Enum):
    """Classification of host type."""

    SERVER = "server"
    WORKSTATION = "workstation"
    IOT = "iot"
    NETWORK = "network"
    UNKNOWN = "unknown"


class DiscoveryRun(Base):
    """A single discovery run capturing hosts at a point in time."""

    __tablename__ = "discovery_run"

    id: Mapped[int] = mapped_column(primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=DiscoveryStatus.RUNNING.value)

    # Relationship to hosts discovered in this run
    hosts: Mapped[list["Host"]] = relationship("Host", back_populates="discovery_run")

    def __repr__(self) -> str:
        return f"<DiscoveryRun(id={self.id}, status={self.status}, started_at={self.started_at})>"


class Host(Base):
    """A discovered host to be reviewed and potentially pushed to NetBox."""

    __tablename__ = "host"

    id: Mapped[int] = mapped_column(primary_key=True)
    mac: Mapped[str] = mapped_column(String(17), unique=True, index=True)
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_addresses: Mapped[dict[str, Any]] = mapped_column(JSON, default=list)
    source: Mapped[str] = mapped_column(String(20), default=HostSource.MANUAL.value)
    switch_port: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=HostStatus.PENDING.value)
    host_type: Mapped[str] = mapped_column(String(20), default=HostType.UNKNOWN.value)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    discovery_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("discovery_run.id"), nullable=True
    )
    netbox_id: Mapped[int | None] = mapped_column(nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationship to discovery run
    discovery_run: Mapped["DiscoveryRun | None"] = relationship(
        "DiscoveryRun", back_populates="hosts"
    )

    # Add index on MAC for fast lookups
    __table_args__ = (Index("ix_host_mac_lookup", "mac"),)

    def __repr__(self) -> str:
        return (
            f"<Host(id={self.id}, mac={self.mac}, hostname={self.hostname}, status={self.status})>"
        )
