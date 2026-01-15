"""CLI entry point for netbox-auto."""

import typer

from netbox_auto import __version__

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
    version: bool | None = typer.Option(
        None,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Network discovery and NetBox population tool.

    Discover hosts from MikroTik DHCP, Proxmox VMs, and network scans.
    Correlate with switch MAC tables and push to NetBox.
    """
    pass


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
