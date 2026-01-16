"""End-to-end tests for CLI commands.

Tests CLI workflows using CliRunner with mocked dependencies.
Covers requirements E2E-01, E2E-02, E2E-03, E2E-04.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from netbox_auto.cli import app
from netbox_auto.discovery import DiscoveryResult
from netbox_auto.models import (
    Base,
    DiscoveryRun,
    DiscoveryStatus,
    Host,
    HostStatus,
    HostType,
)


@pytest.fixture
def runner():
    """Create a CLI runner for invoking commands."""
    return CliRunner()


@pytest.fixture
def temp_config(tmp_path):
    """Create a minimal temporary config file."""
    config_content = """
database:
  path: "{db_path}"
discovery:
  include_ipv6: false
mikrotik:
  host: 192.168.1.1
  username: admin
  password: test
"""
    config_file = tmp_path / "config.yaml"
    db_path = tmp_path / "test.db"
    config_file.write_text(config_content.format(db_path=db_path))
    return config_file


@pytest.fixture
def reset_config():
    """Reset global config state before and after each test."""
    import netbox_auto.config as config_module
    import netbox_auto.database as db_module

    # Save original state
    original_config = config_module._config
    original_engine = db_module._engine
    original_session_factory = db_module._session_factory

    # Reset before test
    config_module._config = None
    db_module._engine = None
    db_module._session_factory = None

    yield

    # Restore after test
    config_module._config = original_config
    db_module._engine = original_engine
    db_module._session_factory = original_session_factory


class TestDiscoverCommand:
    """Tests for 'discover' command (E2E-01)."""

    def test_discover_populates_db(self, runner, temp_config, reset_config):
        """discover command populates staging DB with fixture data."""
        mock_result = DiscoveryResult(
            total_hosts=5,
            new_hosts=3,
            updated_hosts=2,
            errors=[],
        )

        with patch("netbox_auto.cli.run_discovery", return_value=mock_result):
            result = runner.invoke(app, ["--config", str(temp_config), "discover"])

        assert result.exit_code == 0
        assert "Discovery complete" in result.output

    def test_discover_shows_collector_names(self, runner, temp_config, reset_config):
        """discover shows which collectors are enabled from config."""
        mock_result = DiscoveryResult(
            total_hosts=2,
            new_hosts=2,
            updated_hosts=0,
            errors=[],
        )

        with patch("netbox_auto.cli.run_discovery", return_value=mock_result):
            result = runner.invoke(app, ["--config", str(temp_config), "discover"])

        assert result.exit_code == 0
        # Config has mikrotik configured
        assert "MikroTik DHCP" in result.output

    def test_discover_shows_host_counts(self, runner, temp_config, reset_config):
        """discover output includes new, updated, and total host counts."""
        mock_result = DiscoveryResult(
            total_hosts=10,
            new_hosts=6,
            updated_hosts=4,
            errors=[],
        )

        with patch("netbox_auto.cli.run_discovery", return_value=mock_result):
            result = runner.invoke(app, ["--config", str(temp_config), "discover"])

        assert result.exit_code == 0
        assert "New hosts:" in result.output
        assert "6" in result.output
        assert "Updated hosts:" in result.output
        assert "4" in result.output
        assert "Total:" in result.output
        assert "10" in result.output


class TestStatusCommand:
    """Tests for 'status' command (E2E-02)."""

    def test_status_shows_counts_by_status(self, runner, temp_config, reset_config):
        """status command shows counts by host status (Pending/Approved/Pushed)."""
        # Set up test database with hosts
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from netbox_auto.config import load_config

        load_config(temp_config)

        from netbox_auto.config import get_config

        config = get_config()
        engine = create_engine(f"sqlite:///{config.database.path}")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        # Create a discovery run
        run = DiscoveryRun(status=DiscoveryStatus.COMPLETED.value)
        session.add(run)
        session.commit()

        # Add hosts with different statuses
        hosts = [
            Host(mac="aa:bb:cc:dd:ee:01", status=HostStatus.PENDING.value, discovery_run_id=run.id),
            Host(mac="aa:bb:cc:dd:ee:02", status=HostStatus.PENDING.value, discovery_run_id=run.id),
            Host(
                mac="aa:bb:cc:dd:ee:03", status=HostStatus.APPROVED.value, discovery_run_id=run.id
            ),
            Host(mac="aa:bb:cc:dd:ee:04", status=HostStatus.PUSHED.value, discovery_run_id=run.id),
        ]
        session.add_all(hosts)
        session.commit()
        session.close()

        result = runner.invoke(app, ["--config", str(temp_config), "status"])

        assert result.exit_code == 0
        assert "Pending" in result.output
        assert "Approved" in result.output
        assert "Pushed" in result.output
        # Total should be 4
        assert "4" in result.output

    def test_status_shows_counts_by_type(self, runner, temp_config, reset_config):
        """status command shows counts by host type (Server/Workstation/Unknown)."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from netbox_auto.config import load_config

        load_config(temp_config)

        from netbox_auto.config import get_config

        config = get_config()
        engine = create_engine(f"sqlite:///{config.database.path}")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        # Create a discovery run
        run = DiscoveryRun(status=DiscoveryStatus.COMPLETED.value)
        session.add(run)
        session.commit()

        # Add hosts with different types
        hosts = [
            Host(mac="aa:bb:cc:dd:ee:01", host_type=HostType.SERVER.value, discovery_run_id=run.id),
            Host(
                mac="aa:bb:cc:dd:ee:02",
                host_type=HostType.WORKSTATION.value,
                discovery_run_id=run.id,
            ),
            Host(
                mac="aa:bb:cc:dd:ee:03", host_type=HostType.UNKNOWN.value, discovery_run_id=run.id
            ),
        ]
        session.add_all(hosts)
        session.commit()
        session.close()

        result = runner.invoke(app, ["--config", str(temp_config), "status"])

        assert result.exit_code == 0
        assert "Server" in result.output
        assert "Workstation" in result.output
        assert "Unknown" in result.output

    def test_status_shows_recent_discovery(self, runner, temp_config, reset_config):
        """status command shows 'Last run:' with timestamp."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from netbox_auto.config import load_config

        load_config(temp_config)

        from netbox_auto.config import get_config

        config = get_config()
        engine = create_engine(f"sqlite:///{config.database.path}")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        # Create a discovery run with specific timestamp
        run = DiscoveryRun(
            status=DiscoveryStatus.COMPLETED.value,
            started_at=datetime(2026, 1, 15, 10, 30, 0, tzinfo=UTC),
        )
        session.add(run)
        session.commit()

        # Add a host
        host = Host(mac="aa:bb:cc:dd:ee:01", discovery_run_id=run.id)
        session.add(host)
        session.commit()
        session.close()

        result = runner.invoke(app, ["--config", str(temp_config), "status"])

        assert result.exit_code == 0
        assert "Last run:" in result.output
        assert "completed" in result.output

    def test_status_empty_database(self, runner, temp_config, reset_config):
        """status with empty database shows 'No hosts discovered yet'."""
        from sqlalchemy import create_engine

        from netbox_auto.config import load_config

        load_config(temp_config)

        from netbox_auto.config import get_config

        config = get_config()
        engine = create_engine(f"sqlite:///{config.database.path}")
        Base.metadata.create_all(engine)

        result = runner.invoke(app, ["--config", str(temp_config), "status"])

        assert result.exit_code == 0
        assert "No hosts discovered yet" in result.output


class TestPushCommand:
    """Tests for 'push --dry-run' command (E2E-03)."""

    def test_push_dry_run_shows_preview(self, runner, temp_config, reset_config):
        """push --dry-run shows preview with [DRY RUN] without making changes."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from netbox_auto.config import load_config
        from netbox_auto.push import PushResult

        load_config(temp_config)

        from netbox_auto.config import get_config

        config = get_config()
        engine = create_engine(f"sqlite:///{config.database.path}")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        # Create a discovery run
        run = DiscoveryRun(status=DiscoveryStatus.COMPLETED.value)
        session.add(run)
        session.commit()

        # Add an approved host
        host = Host(
            mac="aa:bb:cc:dd:ee:01",
            hostname="test-server",
            status=HostStatus.APPROVED.value,
            discovery_run_id=run.id,
        )
        session.add(host)
        session.commit()
        session.close()

        # Mock push_approved_hosts to avoid real network calls
        mock_result = PushResult(
            netbox_created=1,
            cables_created=0,
            dns_updated=[],
            errors=[],
            dry_run=True,
        )

        with patch("netbox_auto.push.push_approved_hosts", return_value=mock_result):
            result = runner.invoke(app, ["--config", str(temp_config), "push", "--dry-run"])

        assert result.exit_code == 0
        assert "DRY RUN" in result.output

    def test_push_dry_run_no_approved(self, runner, temp_config, reset_config):
        """push --dry-run with no approved hosts shows appropriate message."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from netbox_auto.config import load_config

        load_config(temp_config)

        from netbox_auto.config import get_config

        config = get_config()
        engine = create_engine(f"sqlite:///{config.database.path}")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        # Create a discovery run
        run = DiscoveryRun(status=DiscoveryStatus.COMPLETED.value)
        session.add(run)
        session.commit()

        # Add only pending hosts (none approved)
        host = Host(
            mac="aa:bb:cc:dd:ee:01",
            hostname="test-server",
            status=HostStatus.PENDING.value,
            discovery_run_id=run.id,
        )
        session.add(host)
        session.commit()
        session.close()

        result = runner.invoke(app, ["--config", str(temp_config), "push", "--dry-run"])

        assert result.exit_code == 0
        assert "No approved hosts to push" in result.output


class TestServeCommand:
    """Tests for 'serve' command (E2E-04)."""

    def test_serve_creates_flask_app(self, runner, temp_config, reset_config):
        """serve command creates Flask app and calls app.run()."""
        # Mock the Flask app to avoid actually starting a server
        mock_app = MagicMock()

        with (patch("netbox_auto.web.app.create_app", return_value=mock_app) as mock_create,):
            # invoke() will run the command; since we mock app.run,
            # it won't block
            result = runner.invoke(app, ["--config", str(temp_config), "serve"])

        # Verify create_app was called
        mock_create.assert_called_once()
        # Verify app.run was called with default params
        mock_app.run.assert_called_once()
        call_kwargs = mock_app.run.call_args.kwargs
        assert call_kwargs.get("host") == "127.0.0.1"
        assert call_kwargs.get("port") == 5000
        assert call_kwargs.get("debug") is False
        assert result.exit_code == 0
