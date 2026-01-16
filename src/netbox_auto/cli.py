"""CLI entry point for netbox-auto."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from netbox_auto import __version__
from netbox_auto.config import ConfigError, get_config, load_config
from netbox_auto.database import init_db
from netbox_auto.discovery import run_discovery

console = Console()

app = typer.Typer(
    name="netbox-auto",
    help="Network discovery and NetBox population tool",
    add_completion=False,
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"netbox-auto version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            "-c",
            envvar="NETBOX_AUTO_CONFIG",
            help="Path to configuration file.",
        ),
    ] = Path("config.yaml"),
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-V",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = None,
) -> None:
    """Network discovery and NetBox population tool.

    Discover hosts from MikroTik DHCP, Proxmox VMs, and network scans.
    Correlate with switch MAC tables and push to NetBox.
    """
    # Store config path in context for commands to access if needed
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config

    # Load configuration on startup
    try:
        load_config(config)
    except ConfigError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from None

    # Initialize database (creates if not exists)
    db_path = init_db()
    typer.echo(f"Database initialized at {db_path}")


@app.command()
def discover() -> None:
    """Discover hosts from all configured sources.

    Pulls DHCP leases from MikroTik, VMs from Proxmox, scans subnets
    for static IPs, and correlates hosts with switch MAC tables.
    """
    config = get_config()

    console.print("\n[bold]Running discovery...[/bold]\n")

    # Show which collectors will run
    collectors_enabled: list[str] = []
    if config.mikrotik:
        collectors_enabled.append("MikroTik DHCP")
    if config.proxmox:
        collectors_enabled.append("Proxmox")
    if config.scanner and config.scanner.subnets:
        collectors_enabled.append("Network scan")
    if config.switches:
        collectors_enabled.append("Switch MAC tables")

    if not collectors_enabled:
        console.print("[yellow]No collectors configured. Check your config.yaml.[/yellow]")
        return

    console.print(f"Collectors: {', '.join(collectors_enabled)}\n")

    # Run discovery
    result = run_discovery()

    # Display results
    console.print()
    if result.errors:
        console.print("[bold yellow]Collection warnings:[/bold yellow]")
        for error in result.errors:
            console.print(f"  [yellow]! {error}[/yellow]")
        console.print()

    console.print("[bold green]Discovery complete:[/bold green]")
    console.print(f"  New hosts:     {result.new_hosts}")
    console.print(f"  Updated hosts: {result.updated_hosts}")
    console.print(f"  Total:         {result.total_hosts}")
    console.print()


@app.command()
def serve(
    host: Annotated[
        str,
        typer.Option(
            "--host",
            "-h",
            help="Host to bind server to.",
        ),
    ] = "127.0.0.1",
    port: Annotated[
        int,
        typer.Option(
            "--port",
            "-p",
            help="Port to bind server to.",
        ),
    ] = 5000,
    debug: Annotated[
        bool,
        typer.Option(
            "--debug",
            "-d",
            help="Run in debug mode with auto-reload.",
        ),
    ] = False,
) -> None:
    """Start the web UI for reviewing discovered hosts.

    Launches a local web server where you can review, classify,
    and approve hosts before pushing to NetBox.
    """
    from netbox_auto.web.app import create_app

    console.print("\n[bold]Starting web server...[/bold]\n")
    console.print(f"  URL: [link]http://{host}:{port}[/link]")
    console.print(f"  Debug: {'on' if debug else 'off'}")
    console.print("\n  Press [bold]Ctrl+C[/bold] to stop.\n")

    flask_app = create_app()
    flask_app.run(host=host, port=port, debug=debug)


@app.command()
def push(
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-n",
            help="Preview changes without pushing.",
        ),
    ] = False,
    skip_netbox: Annotated[
        bool,
        typer.Option(
            "--skip-netbox",
            help="Skip NetBox push.",
        ),
    ] = False,
    skip_dns: Annotated[
        bool,
        typer.Option(
            "--skip-dns",
            help="Skip DNS push.",
        ),
    ] = False,
) -> None:
    """Push approved hosts to NetBox and update DNS.

    Creates NetBox devices/VMs for approved hosts, creates cable
    records linking switches to devices, and updates Unbound DNS.
    """
    from sqlalchemy import func

    from netbox_auto.database import get_session
    from netbox_auto.models import Host, HostStatus
    from netbox_auto.push import push_approved_hosts

    # Show banner
    console.print()
    if dry_run:
        console.print("[bold yellow]DRY RUN[/bold yellow] - No changes will be made\n")

    # Show approved host count before starting
    session = get_session()
    approved_count = (
        session.query(func.count(Host.id))
        .filter(Host.status == HostStatus.APPROVED.value)
        .scalar()
        or 0
    )
    session.close()

    if approved_count == 0:
        console.print("[yellow]No approved hosts to push.[/yellow]")
        console.print("Use 'netbox-auto serve' to review and approve hosts first.\n")
        return

    console.print(f"[bold]Pushing {approved_count} approved hosts...[/bold]\n")

    # Show what will be skipped
    if skip_netbox:
        console.print("  [dim]Skipping NetBox push[/dim]")
    if skip_dns:
        console.print("  [dim]Skipping DNS push[/dim]")
    if skip_netbox or skip_dns:
        console.print()

    # Run push
    result = push_approved_hosts(
        dry_run=dry_run,
        skip_netbox=skip_netbox,
        skip_dns=skip_dns,
    )

    # Display results
    console.print("[bold green]Push complete:[/bold green]")
    console.print(f"  NetBox created: {result.netbox_created}")
    console.print(f"  Cables created: {result.cables_created}")
    if result.dns_updated:
        console.print(f"  DNS servers:    {len(result.dns_updated)}")
        for server in result.dns_updated:
            console.print(f"    - {server}")
    else:
        console.print("  DNS servers:    0")

    # Show errors if any
    if result.errors:
        console.print()
        console.print("[bold yellow]Errors:[/bold yellow]")
        for error in result.errors:
            console.print(f"  [yellow]! {error}[/yellow]")

    console.print()


@app.command()
def status() -> None:
    """Show discovery and push status summary.

    Displays counts of discovered hosts, pending approvals,
    and recent push activity.
    """
    from sqlalchemy import func

    from netbox_auto.database import get_session
    from netbox_auto.models import DiscoveryRun, DiscoveryStatus, Host, HostStatus, HostType

    session = get_session()

    # Count hosts by status
    status_counts = dict(
        session.query(Host.status, func.count(Host.id)).group_by(Host.status).all()
    )

    # Count hosts by type
    type_counts = dict(
        session.query(Host.host_type, func.count(Host.id)).group_by(Host.host_type).all()
    )

    total_hosts = session.query(func.count(Host.id)).scalar() or 0

    # Get recent discovery runs (last 5) with host counts
    recent_runs = (
        session.query(DiscoveryRun)
        .order_by(DiscoveryRun.started_at.desc())
        .limit(5)
        .all()
    )

    # Get host count for last run before closing session
    last_run_info = None
    if recent_runs:
        last_run = recent_runs[0]
        run_host_count = (
            session.query(func.count(Host.id))
            .filter(Host.discovery_run_id == last_run.id)
            .scalar()
            or 0
        )
        last_run_info = {
            "started_at": last_run.started_at,
            "status": last_run.status,
            "host_count": run_host_count,
        }

    session.close()

    # Handle empty database
    if total_hosts == 0 and not recent_runs:
        console.print(
            "\n[yellow]No hosts discovered yet. Run 'netbox-auto discover' first.[/yellow]\n"
        )
        return

    console.print()

    # Host Status section
    console.print("[bold]Host Status:[/bold]")
    for status_val in [HostStatus.PENDING, HostStatus.APPROVED, HostStatus.REJECTED, HostStatus.PUSHED]:
        count = status_counts.get(status_val.value, 0)
        label = status_val.value.capitalize()
        console.print(f"  {label:10} {count:>5}")
    console.print("  " + "─" * 16)
    console.print(f"  {'Total':10} {total_hosts:>5}")

    console.print()

    # Host Types section
    console.print("[bold]Host Types:[/bold]")
    for type_val in [HostType.SERVER, HostType.WORKSTATION, HostType.IOT, HostType.NETWORK, HostType.UNKNOWN]:
        count = type_counts.get(type_val.value, 0)
        label = type_val.value.capitalize()
        console.print(f"  {label:12} {count:>5}")

    console.print()

    # Recent Discovery section
    if last_run_info:
        console.print("[bold]Recent Discovery:[/bold]")

        # Format timestamp
        if last_run_info["started_at"]:
            run_time = last_run_info["started_at"].strftime("%Y-%m-%d %H:%M")
        else:
            run_time = "unknown"

        # Format status
        run_status = last_run_info["status"]
        if run_status == DiscoveryStatus.COMPLETED.value:
            status_display = "completed"
        elif run_status == DiscoveryStatus.RUNNING.value:
            status_display = "running"
        else:
            status_display = "failed"

        console.print(
            f"  Last run: {run_time} ({status_display}, {last_run_info['host_count']} hosts)"
        )

    console.print()


if __name__ == "__main__":
    app()
