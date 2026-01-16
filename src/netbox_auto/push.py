"""Push orchestration module for NetBox and DNS updates.

Orchestrates the push workflow from approved hosts to NetBox and DNS.
"""

import logging
from dataclasses import dataclass, field

from netbox_auto.database import get_session
from netbox_auto.dns import generate_unbound_config, push_dns_config
from netbox_auto.models import Host, HostSource, HostStatus
from netbox_auto.netbox import get_netbox_client

logger = logging.getLogger(__name__)


@dataclass
class PushResult:
    """Result of a push operation."""

    netbox_created: int = 0
    cables_created: int = 0
    dns_updated: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    dry_run: bool = False


def push_approved_hosts(
    dry_run: bool = False,
    skip_netbox: bool = False,
    skip_dns: bool = False,
) -> PushResult:
    """Push approved hosts to NetBox and DNS.

    Args:
        dry_run: If True, preview changes without pushing.
        skip_netbox: If True, skip NetBox push.
        skip_dns: If True, skip DNS push.

    Returns:
        PushResult with counts of created/updated resources.
    """
    result = PushResult(dry_run=dry_run)
    session = get_session()

    try:
        # Query approved hosts
        approved_hosts = session.query(Host).filter(Host.status == HostStatus.APPROVED.value).all()

        if not approved_hosts:
            logger.info("No approved hosts to push")
            return result

        logger.info(f"Found {len(approved_hosts)} approved hosts to push")

        # Push to NetBox if not skipped
        if not skip_netbox:
            netbox_client = get_netbox_client()

            for host in approved_hosts:
                try:
                    _push_host_to_netbox(host, netbox_client, result, dry_run, session)
                except Exception as e:
                    error_msg = f"Failed to push {host.hostname or host.mac}: {e}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)
                    # Continue with other hosts

        # Generate and push DNS config if not skipped
        if not skip_dns:
            # Get all pushed hosts (including newly pushed) for DNS
            pushed_hosts = session.query(Host).filter(Host.status == HostStatus.PUSHED.value).all()

            if pushed_hosts:
                config = generate_unbound_config(pushed_hosts)
                try:
                    updated = push_dns_config(config, dry_run=dry_run)
                    result.dns_updated = updated
                except Exception as e:
                    error_msg = f"DNS push failed: {e}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)

        session.commit()
        return result

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def _push_host_to_netbox(
    host: Host,
    netbox_client: "get_netbox_client",  # noqa: F821
    result: PushResult,
    dry_run: bool,
    session: "Session",  # noqa: F821
) -> None:
    """Push a single host to NetBox.

    Args:
        host: Host to push.
        netbox_client: NetBox client instance.
        result: PushResult to update.
        dry_run: If True, don't actually push.
        session: Database session for status updates.
    """
    hostname = host.hostname or f"host-{host.mac.replace(':', '')}"

    if dry_run:
        logger.info(f"[DRY RUN] Would create {_get_host_type(host)}: {hostname}")
        if host.switch_port:
            logger.info(f"[DRY RUN] Would create cable for switch port: {host.switch_port}")
            result.cables_created += 1
        result.netbox_created += 1
        return

    # Determine if VM or device based on source
    is_vm = host.source == HostSource.PROXMOX.value

    if is_vm:
        # Note: cluster_id would need to come from config in real implementation
        # For now, log that VM creation needs more config
        logger.warning(f"VM creation for {hostname} requires cluster_id configuration")
        result.errors.append(f"VM creation for {hostname} skipped - cluster_id not configured")
        return
    else:
        # Device creation needs device_type_id, role_id, site_id from config
        # For now, log that device creation needs more config
        logger.warning(
            f"Device creation for {hostname} requires device_type_id, role_id, site_id configuration"
        )
        result.errors.append(f"Device creation for {hostname} skipped - NetBox IDs not configured")
        return

    # Mark as pushed after successful creation
    host.status = HostStatus.PUSHED.value
    result.netbox_created += 1

    # Create cable if switch port is set
    if host.switch_port:
        # Note: Cable creation needs switch interface IDs from NetBox
        logger.info(f"Cable creation for {hostname} to {host.switch_port}")
        result.cables_created += 1


def _get_host_type(host: Host) -> str:
    """Get human-readable host type for logging.

    Args:
        host: Host to check.

    Returns:
        'VM' or 'device' string.
    """
    return "VM" if host.source == HostSource.PROXMOX.value else "device"
