"""Integration tests for DNS push to Unbound servers.

Tests config generation and SSH push with mocked paramiko.
Covers INTG-06 requirement.
"""

from unittest.mock import MagicMock, patch

import pytest

from netbox_auto.dns import generate_unbound_config, push_dns_config
from netbox_auto.models import Host


@pytest.fixture
def host_factory(in_memory_db):
    """Factory for creating Host objects with persistence.

    Returns a callable that creates Host instances in the test database.
    """

    def _factory(
        mac: str = "aa:bb:cc:dd:ee:ff",
        hostname: str | None = None,
        ip_addresses: list[str] | None = None,
    ) -> Host:
        host = Host(
            mac=mac,
            hostname=hostname,
            ip_addresses=ip_addresses if ip_addresses is not None else [],
        )
        in_memory_db.add(host)
        in_memory_db.commit()
        return host

    return _factory


# =============================================================================
# Config Generation Tests
# =============================================================================


class TestGenerateUnboundConfig:
    """Tests for generate_unbound_config function."""

    def test_creates_local_data_with_fqdn_and_ip(self, host_factory):
        """Verify local-data line format with FQDN and IP."""
        host = host_factory(
            mac="aa:bb:cc:dd:ee:01",
            hostname="server1",
            ip_addresses=["192.168.1.10"],
        )

        config = generate_unbound_config([host], domain="lan")

        assert 'local-data: "server1.lan. A 192.168.1.10"' in config

    def test_adds_domain_suffix_to_hostname(self, host_factory):
        """Hostname without dot gets .lan appended."""
        host = host_factory(
            mac="aa:bb:cc:dd:ee:02",
            hostname="myhost",
            ip_addresses=["10.0.0.1"],
        )

        config = generate_unbound_config([host], domain="home")

        assert 'local-data: "myhost.home. A 10.0.0.1"' in config

    def test_preserves_fqdn_hostname(self, host_factory):
        """Hostname with dot (FQDN) kept as-is."""
        host = host_factory(
            mac="aa:bb:cc:dd:ee:03",
            hostname="server.example.com",
            ip_addresses=["172.16.0.5"],
        )

        config = generate_unbound_config([host])

        # Should NOT add another domain suffix
        assert 'local-data: "server.example.com. A 172.16.0.5"' in config
        assert "server.example.com.lan" not in config

    def test_skips_hosts_without_hostname(self, host_factory):
        """No hostname = skipped from config."""
        host_with_name = host_factory(
            mac="aa:bb:cc:dd:ee:04",
            hostname="named",
            ip_addresses=["192.168.1.1"],
        )
        host_without_name = host_factory(
            mac="aa:bb:cc:dd:ee:05",
            hostname=None,
            ip_addresses=["192.168.1.2"],
        )

        config = generate_unbound_config([host_with_name, host_without_name])

        assert "named.lan" in config
        assert "192.168.1.2" not in config

    def test_handles_multiple_ips(self, host_factory):
        """Multiple IPs = multiple local-data lines."""
        host = host_factory(
            mac="aa:bb:cc:dd:ee:06",
            hostname="multi-ip",
            ip_addresses=["192.168.1.10", "192.168.1.11", "10.0.0.50"],
        )

        config = generate_unbound_config([host])

        assert 'local-data: "multi-ip.lan. A 192.168.1.10"' in config
        assert 'local-data: "multi-ip.lan. A 192.168.1.11"' in config
        assert 'local-data: "multi-ip.lan. A 10.0.0.50"' in config


# =============================================================================
# SSH Push Tests (mocked paramiko)
# =============================================================================


class TestPushDnsConfig:
    """Tests for push_dns_config function with mocked SSH."""

    @pytest.fixture
    def mock_unbound_config(self):
        """Create mock config with Unbound hosts."""
        from netbox_auto.config import Config, UnboundConfig, UnboundHostConfig

        return Config(
            unbound=UnboundConfig(
                hosts=[
                    UnboundHostConfig(
                        host="dns1.example.com",
                        user="admin",
                        config_path="/etc/unbound/local.d/local.conf",
                    )
                ]
            )
        )

    def test_connects_via_ssh(self, mock_unbound_config):
        """Mock SSHClient.connect, verify called with host/user."""
        with (
            patch("netbox_auto.dns.get_config", return_value=mock_unbound_config),
            patch("netbox_auto.dns.paramiko.SSHClient") as mock_ssh_class,
        ):
            mock_client = MagicMock()
            mock_ssh_class.return_value = mock_client
            mock_sftp = MagicMock()
            mock_client.open_sftp.return_value = mock_sftp
            mock_file = MagicMock()
            mock_sftp.file.return_value.__enter__ = MagicMock(return_value=mock_file)
            mock_sftp.file.return_value.__exit__ = MagicMock(return_value=False)
            mock_stdout = MagicMock()
            mock_stdout.channel.recv_exit_status.return_value = 0
            mock_client.exec_command.return_value = (MagicMock(), mock_stdout, MagicMock())

            push_dns_config("# test config")

            mock_client.connect.assert_called_once_with(
                hostname="dns1.example.com", username="admin"
            )

    def test_writes_config_via_sftp(self, mock_unbound_config):
        """Mock open_sftp().file(), verify config written."""
        test_config = "# test config\nlocal-data: test"

        with (
            patch("netbox_auto.dns.get_config", return_value=mock_unbound_config),
            patch("netbox_auto.dns.paramiko.SSHClient") as mock_ssh_class,
        ):
            mock_client = MagicMock()
            mock_ssh_class.return_value = mock_client
            mock_sftp = MagicMock()
            mock_client.open_sftp.return_value = mock_sftp
            mock_file = MagicMock()
            mock_sftp.file.return_value.__enter__ = MagicMock(return_value=mock_file)
            mock_sftp.file.return_value.__exit__ = MagicMock(return_value=False)
            mock_stdout = MagicMock()
            mock_stdout.channel.recv_exit_status.return_value = 0
            mock_client.exec_command.return_value = (MagicMock(), mock_stdout, MagicMock())

            push_dns_config(test_config)

            mock_sftp.file.assert_called_once_with("/etc/unbound/local.d/local.conf", "w")
            mock_file.write.assert_called_once_with(test_config)

    def test_reloads_unbound(self, mock_unbound_config):
        """Mock exec_command, verify 'sudo unbound-control reload' called."""
        with (
            patch("netbox_auto.dns.get_config", return_value=mock_unbound_config),
            patch("netbox_auto.dns.paramiko.SSHClient") as mock_ssh_class,
        ):
            mock_client = MagicMock()
            mock_ssh_class.return_value = mock_client
            mock_sftp = MagicMock()
            mock_client.open_sftp.return_value = mock_sftp
            mock_file = MagicMock()
            mock_sftp.file.return_value.__enter__ = MagicMock(return_value=mock_file)
            mock_sftp.file.return_value.__exit__ = MagicMock(return_value=False)
            mock_stdout = MagicMock()
            mock_stdout.channel.recv_exit_status.return_value = 0
            mock_client.exec_command.return_value = (MagicMock(), mock_stdout, MagicMock())

            push_dns_config("# config")

            mock_client.exec_command.assert_called_once_with("sudo unbound-control reload")

    def test_returns_updated_hosts(self, mock_unbound_config):
        """Verify list of successfully updated hostnames returned."""
        with (
            patch("netbox_auto.dns.get_config", return_value=mock_unbound_config),
            patch("netbox_auto.dns.paramiko.SSHClient") as mock_ssh_class,
        ):
            mock_client = MagicMock()
            mock_ssh_class.return_value = mock_client
            mock_sftp = MagicMock()
            mock_client.open_sftp.return_value = mock_sftp
            mock_file = MagicMock()
            mock_sftp.file.return_value.__enter__ = MagicMock(return_value=mock_file)
            mock_sftp.file.return_value.__exit__ = MagicMock(return_value=False)
            mock_stdout = MagicMock()
            mock_stdout.channel.recv_exit_status.return_value = 0
            mock_client.exec_command.return_value = (MagicMock(), mock_stdout, MagicMock())

            result = push_dns_config("# config")

            assert result == ["dns1.example.com"]

    def test_dry_run_skips_connection(self, mock_unbound_config):
        """dry_run=True, verify SSHClient.connect NOT called."""
        with (
            patch("netbox_auto.dns.get_config", return_value=mock_unbound_config),
            patch("netbox_auto.dns.paramiko.SSHClient") as mock_ssh_class,
        ):
            mock_client = MagicMock()
            mock_ssh_class.return_value = mock_client

            result = push_dns_config("# config", dry_run=True)

            # Should NOT call connect in dry run mode
            mock_client.connect.assert_not_called()
            # Should still return the hosts that would have been updated
            assert result == ["dns1.example.com"]
