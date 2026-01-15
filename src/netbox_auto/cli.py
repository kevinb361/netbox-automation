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
def serve() -> None:
    """Start the web UI for reviewing discovered hosts.

    Launches a local web server where you can review, classify,
    and approve hosts before pushing to NetBox.
    """
    typer.echo("Not implemented yet")


@app.command()
def push() -> None:
    """Push approved hosts to NetBox and update DNS.

    Creates NetBox devices/VMs for approved hosts, creates cable
    records linking switches to devices, and updates Unbound DNS.
    """
    typer.echo("Not implemented yet")


@app.command()
def status() -> None:
    """Show discovery and push status summary.

    Displays counts of discovered hosts, pending approvals,
    and recent push activity.
    """
    typer.echo("Not implemented yet")


if __name__ == "__main__":
    app()
