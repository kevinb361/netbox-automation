"""Flask application factory for netbox-auto web interface.

Provides create_app() factory function following Flask best practices.
"""

from pathlib import Path

from flask import Blueprint, Flask, redirect, render_template, url_for

from netbox_auto.database import get_session
from netbox_auto.models import Host

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
        return render_template("hosts.html", hosts=hosts_list)
    finally:
        session.close()


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

    # Register blueprint
    app.register_blueprint(bp)

    return app
