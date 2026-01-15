"""CLI entry point for netbox-auto."""

from pathlib import Path
from typing import Annotated

import typer

from netbox_auto import __version__
from netbox_auto.config import ConfigError, load_config

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
        raise typer.Exit(1)


@app.command()
def discover() -> None:
    """Discover hosts from all configured sources.

    Pulls DHCP leases from MikroTik, VMs from Proxmox, scans subnets
    for static IPs, and correlates hosts with switch MAC tables.
    """
    typer.echo("Not implemented yet")


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
