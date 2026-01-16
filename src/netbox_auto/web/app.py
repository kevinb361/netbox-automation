"""Flask application factory for netbox-auto web interface.

Provides create_app() factory function following Flask best practices.
"""

import logging
import os
import secrets
from pathlib import Path

from flask import Blueprint, Flask, flash, redirect, render_template, request, url_for

from netbox_auto.database import get_session
from netbox_auto.models import Host, HostStatus, HostType
from netbox_auto.reconcile import import_netbox_devices, reconcile_hosts

# Create blueprint for main routes
bp = Blueprint("main", __name__)


@bp.route("/")
def index() -> object:
    """Redirect root to hosts list."""
    return redirect(url_for("main.hosts"))


@bp.route("/hosts")
def hosts() -> str:
    """Display all discovered hosts in a table."""
    session = get_session()
    try:
        hosts_list = session.query(Host).order_by(Host.last_seen.desc()).all()
        return render_template(
            "hosts.html",
            hosts=hosts_list,
            host_types=[t.value for t in HostType],
        )
    finally:
        session.close()


@bp.route("/hosts/<int:host_id>/status", methods=["POST"])
def update_host_status(host_id: int) -> object:
    """Update a host's approval status."""
    session = get_session()
    try:
        host = session.query(Host).filter_by(id=host_id).first()
        if not host:
            flash("Host not found", "error")
            return redirect(url_for("main.hosts"))

        new_status = request.form.get("status")
        if new_status not in [s.value for s in HostStatus]:
            flash("Invalid status", "error")
            return redirect(url_for("main.hosts"))

        host.status = new_status
        session.commit()
        flash(f"Host {host.mac} status updated to {new_status}", "success")
    finally:
        session.close()

    return redirect(url_for("main.hosts"))


@bp.route("/hosts/<int:host_id>/type", methods=["POST"])
def update_host_type(host_id: int) -> object:
    """Update a host's type classification."""
    session = get_session()
    try:
        host = session.query(Host).filter_by(id=host_id).first()
        if not host:
            flash("Host not found", "error")
            return redirect(url_for("main.hosts"))

        new_type = request.form.get("host_type")
        if new_type not in [t.value for t in HostType]:
            flash("Invalid host type", "error")
            return redirect(url_for("main.hosts"))

        host.host_type = new_type
        session.commit()
        flash(f"Host {host.mac} type updated to {new_type}", "success")
    finally:
        session.close()

    return redirect(url_for("main.hosts"))


@bp.route("/hosts/bulk", methods=["POST"])
def bulk_update_hosts() -> object:
    """Bulk update status for multiple hosts."""
    session = get_session()
    try:
        action = request.form.get("action")
        host_ids = request.form.getlist("host_ids")

        if not action:
            flash("Please select an action", "error")
            return redirect(url_for("main.hosts"))

        if not host_ids:
            flash("Please select at least one host", "error")
            return redirect(url_for("main.hosts"))

        # Map action to status
        status_map = {
            "approve": HostStatus.APPROVED.value,
            "reject": HostStatus.REJECTED.value,
        }

        if action not in status_map:
            flash("Invalid action", "error")
            return redirect(url_for("main.hosts"))

        new_status = status_map[action]

        # Convert to integers and update
        host_id_ints = [int(hid) for hid in host_ids]
        updated = (
            session.query(Host)
            .filter(Host.id.in_(host_id_ints))
            .update({Host.status: new_status}, synchronize_session="fetch")
        )
        session.commit()
        flash(f"Updated {updated} hosts to {new_status}", "success")
    finally:
        session.close()

    return redirect(url_for("main.hosts"))


@bp.route("/reconcile")
def reconcile() -> str:
    """Display reconciliation comparison between discovered hosts and NetBox."""
    result = reconcile_hosts()
    return render_template(
        "reconcile.html",
        new_hosts=result.new_hosts,
        matched_hosts=result.matched_hosts,
        stale_netbox=result.stale_netbox,
    )


@bp.route("/reconcile/import", methods=["POST"])
def reconcile_import() -> object:
    """Import devices and VMs from NetBox into staging database."""
    try:
        count = import_netbox_devices()
        if count > 0:
            flash(f"Imported {count} devices from NetBox", "success")
        else:
            flash("No new devices to import from NetBox", "success")
    except Exception as e:
        flash(f"Error importing from NetBox: {e}", "error")

    return redirect(url_for("main.hosts"))


def create_app() -> Flask:
    """Create and configure the Flask application.

    Returns:
        Configured Flask application instance.
    """
    # Get the web package directory for templates/static
    web_dir = Path(__file__).parent

    app = Flask(
        __name__,
        template_folder=str(web_dir / "templates"),
        static_folder=str(web_dir / "static"),
    )

    # Secret key: use env var if set, otherwise generate random key
    # Random key means sessions invalidate on restart (acceptable for this use case)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)

    # Session cookie security settings
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    # Template auto-reload follows debug mode
    app.config["TEMPLATES_AUTO_RELOAD"] = app.debug

    # Configure request logging
    if not app.debug:
        # Production: log to werkzeug logger at INFO level
        logging.getLogger("werkzeug").setLevel(logging.INFO)

    # Register blueprint
    app.register_blueprint(bp)

    return app
